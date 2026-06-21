"""
stage4/honeypot_signals.py
Detect 'subtly impossible' honeypot profiles.

The organizers (README §7) name the exact patterns:
  - "8 years of experience at a company founded 3 years ago"
  - "'expert' proficiency in 10 skills with 0 years used"
There are ~80 honeypots in 100K (~0.08%), forced to relevance tier 0 in ground truth.
Ranking them in the top 100 at >10% rate DISQUALIFIES the submission. We target a TINY
flag rate (honeypots are rare) and bias hard toward PRECISION: a false honeypot flag on a
real candidate removes them from the top 100, costing NDCG. So each signal fires only on
GROSS impossibility, never mild overruns.

Calibration finding (from real data): "skill duration slightly exceeds career" fires on
~14% of candidates INCLUDING genuine strong fits — so it is NOT used as a standalone signal.
Only gross, self-contradictory impossibilities count.

Returns honeypot_score in (0,1]: 1.0 = clean, low = likely honeypot. Multiplicative.
is_likely_honeypot = honeypot_score < 0.15.
"""
from __future__ import annotations
from datetime import datetime


def _months(s: str | None, e: str | None):
    if not s or not e:
        return None
    try:
        a = datetime.strptime(s, "%Y-%m-%d")
        b = datetime.strptime(e, "%Y-%m-%d")
        return (b - a).days / 30.0
    except (ValueError, TypeError):
        return None


def honeypot_signals(c: dict) -> dict:
    """Return {honeypot_score, is_likely_honeypot, honeypot_reasons:[...]}"""
    prof = c["profile"]
    yoe = prof.get("years_of_experience", 0.0)
    hist = c.get("career_history", [])
    skills = c.get("skills", [])
    penalty = 1.0
    reasons: list[str] = []

    # --- SIGNAL 1: tenure-at-a-single-company exceeds plausible company age ---
    # Proxy for "8yr at a company founded 3yr ago": a single role's duration is impossibly
    # long relative to the candidate's total career, OR exceeds ~25 years.
    for r in hist:
        dm = r.get("duration_months", 0)
        if dm > 300:                       # >25 years in one role — impossible here
            penalty *= 0.08
            reasons.append("single_role_over_25yr")
            break
        # a role longer than the person's entire stated experience + 2yr slack — decisive
        if dm > (yoe + 2) * 12 and yoe > 0:
            penalty *= 0.12
            reasons.append("role_exceeds_total_yoe")
            break

    # --- SIGNAL 2: sum of role tenures grossly exceeds career length ---
    total_months = sum(r.get("duration_months", 0) for r in hist)
    if yoe > 0 and total_months > (yoe + 3) * 12 * 1.5:   # gross overlap — decisive
        penalty *= 0.12
        reasons.append("tenure_sum_grossly_exceeds_yoe")

    # --- SIGNAL 3: many advanced/expert skills with 0 months used ---
    # README: "'expert' in 10 skills with 0 years used". Require a GROSS count to avoid
    # flagging the one-off "listed a skill, no duration" case.
    adv_expert_zero = sum(1 for s in skills
                          if s.get("proficiency") in ("expert", "advanced")
                          and s.get("duration_months", 0) == 0)
    if adv_expert_zero >= 4:
        penalty *= 0.12
        reasons.append(f"adv_expert_zero_duration={adv_expert_zero}")
    elif adv_expert_zero == 3:
        penalty *= 0.6                     # soft: suspicious but not decisive
        reasons.append("adv_expert_zero_duration=3")

    # --- SIGNAL 4: a single skill claimed for grossly more time than the whole career ---
    for s in skills:
        if s.get("duration_months", 0) > (yoe * 12) + 36:   # >3yr beyond entire career
            penalty *= 0.12
            reasons.append("skill_duration_grossly_exceeds_career")
            break

    # --- SIGNAL 5: role duration disagrees with its own start/end dates (multi-role) ---
    mismatches = 0
    for r in hist:
        real = _months(r.get("start_date"), r.get("end_date"))
        if real is not None and abs(real - r.get("duration_months", 0)) > 12:
            mismatches += 1
    if mismatches >= 2:                     # need TWO to be decisive (one can be rounding)
        penalty *= 0.25
        reasons.append(f"date_duration_mismatch={mismatches}")

    # --- SIGNAL 6: YOE wildly exceeds time since first job started ---
    starts = [r.get("start_date") for r in hist if r.get("start_date")]
    if starts:
        try:
            first = min(datetime.strptime(s, "%Y-%m-%d") for s in starts)
            # crude 'now' from the latest end/start in the profile; avoid importing ref here
            latest = max(
                [datetime.strptime(r["end_date"], "%Y-%m-%d")
                 for r in hist if r.get("end_date")] +
                [datetime.strptime(s, "%Y-%m-%d") for s in starts])
            span_years = (latest - first).days / 365.0
            if yoe > span_years + 4:        # claims 4+ more years than career span allows
                penalty *= 0.30
                reasons.append("yoe_exceeds_career_span")
        except (ValueError, TypeError):
            pass

    # --- SIGNAL 7: all-zero-duration skills with a large skill list (stuffed + impossible)
    n_skills = len(skills)
    zero_dur = sum(1 for s in skills if s.get("duration_months", 0) == 0)
    if n_skills >= 8 and zero_dur == n_skills:
        penalty *= 0.15
        reasons.append("all_skills_zero_duration")

    penalty = max(penalty, 0.01)
    return {
        "honeypot_score": round(penalty, 4),
        "is_likely_honeypot": bool(penalty < 0.15),
        "honeypot_reasons": ";".join(reasons) if reasons else "",
        "honeypot_signal_count": len(reasons),
    }
