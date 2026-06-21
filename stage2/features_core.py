"""
stage2/features_core.py
Pure feature-extraction functions. No IO, no side effects — each takes a candidate dict
(and shared config/taxonomy) and returns a flat dict of numeric features.

DESIGN PRINCIPLE (the JD's central instruction):
  "A Tier 5 candidate may not use the words 'RAG' or 'Pinecone' ... but if their career
   history shows they built a recommendation system at a product company, they're a fit.
   A candidate who has all the AI keywords listed as skills but whose title is 'Marketing
   Manager' is not a fit, no matter how perfect their skill list looks."

So requirement coverage is computed from BOTH career-description text and the skills list,
but career evidence is weighted ~2x skill-claim evidence, and skill claims are DISCOUNTED
when on-platform assessment scores contradict them. This is the mechanism that makes the
keyword trap backfire.

All recency uses the frozen reference date from Stage 0 (common.config.get_reference_date()).
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def career_text(c: dict) -> str:
    """All free text describing what the candidate has DONE (weighted toward recency
    by the caller, which doubles the current role)."""
    parts = [c["profile"].get("summary", ""), c["profile"].get("headline", "")]
    for r in c.get("career_history", []):
        parts.append(r.get("description", ""))
        parts.append(r.get("title", ""))
    return " ".join(parts).lower()


def recent_career_text(c: dict) -> str:
    """Text from current + most-recent role only — used to check 'still doing it lately'."""
    hist = sorted(c.get("career_history", []),
                  key=lambda r: r.get("start_date", ""), reverse=True)
    parts = []
    for r in hist[:2]:
        parts.append(r.get("description", ""))
        parts.append(r.get("title", ""))
    return " ".join(parts).lower()


def skills_text(c: dict) -> str:
    return " ".join(s.get("name", "").lower() for s in c.get("skills", []))


def _count_group_hits(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if t in text)


def _parse_date(s: str | None):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Skill-claim credibility: discount skills the assessment scores contradict
# ---------------------------------------------------------------------------
def skill_credibility(c: dict) -> dict:
    """
    Returns a multiplier in [0.4, 1.0] applied to skill-list evidence.
    If the candidate claims skills but their on-platform assessment scores on those skills
    are low (<50), we trust the skill list LESS. Candidates with no assessments are neutral
    (1.0) — we don't penalize absence, only contradiction. (Only ~20% have assessments.)
    """
    assess = c["redrob_signals"].get("skill_assessment_scores", {})
    if not assess:
        return {"skill_credibility": 1.0, "n_assessed": 0, "mean_assessment": -1.0}
    scores = list(assess.values())
    mean = sum(scores) / len(scores)
    # Map mean assessment (0-100) to a credibility multiplier.
    # >=70 -> 1.0 ; 50 -> ~0.7 ; <=30 -> 0.4
    if mean >= 70:
        cred = 1.0
    elif mean >= 50:
        cred = 0.7 + (mean - 50) / 20 * 0.3
    else:
        cred = 0.4 + max(0.0, (mean - 30)) / 20 * 0.3
    return {"skill_credibility": round(cred, 3),
            "n_assessed": len(scores),
            "mean_assessment": round(mean, 1)}


# ---------------------------------------------------------------------------
# Requirement coverage (the core anti-keyword-trap feature)
# ---------------------------------------------------------------------------
def requirement_coverage(c: dict, jd_config: dict, groups: dict) -> dict:
    """
    For each hard/soft requirement, a coverage score in [0,1] blending:
       career-evidence (weight 0.65) + credibility-adjusted skill-claim (weight 0.35)
    Career evidence dominates so 'built it' beats 'listed it'.
    """
    ctext = career_text(c)
    stext = skills_text(c)
    cred = skill_credibility(c)["skill_credibility"]

    out = {}
    weighted_hard, hard_strength_sum = 0.0, 0.0
    for name, strength in jd_config["hard_requirements"].items():
        terms = groups.get(name, [])
        if not terms:
            continue
        career_hits = _count_group_hits(ctext, terms)
        skill_hits = _count_group_hits(stext, terms)
        # saturating: 1 hit gets you most of the way, more adds a little
        career_sig = 1 - 0.5 ** career_hits if career_hits else 0.0
        skill_sig = (1 - 0.5 ** skill_hits if skill_hits else 0.0) * cred
        cov = 0.65 * career_sig + 0.35 * skill_sig
        out[f"cov_{name}"] = round(cov, 3)
        weighted_hard += cov * strength
        hard_strength_sum += strength
    out["weighted_hard_req_coverage"] = round(
        weighted_hard / hard_strength_sum if hard_strength_sum else 0.0, 3)

    weighted_soft, soft_strength_sum = 0.0, 0.0
    for name, strength in jd_config["soft_requirements"].items():
        terms = groups.get(name, [])
        if not terms:
            continue
        career_hits = _count_group_hits(ctext, terms)
        skill_hits = _count_group_hits(stext, terms)
        career_sig = 1 - 0.5 ** career_hits if career_hits else 0.0
        skill_sig = (1 - 0.5 ** skill_hits if skill_hits else 0.0) * cred
        cov = 0.65 * career_sig + 0.35 * skill_sig
        out[f"cov_{name}"] = round(cov, 3)
        weighted_soft += cov * strength
        soft_strength_sum += strength
    out["weighted_soft_req_coverage"] = round(
        weighted_soft / soft_strength_sum if soft_strength_sum else 0.0, 3)

    # raw keyword counts (anchor-helper + honeypot inputs)
    hard_terms = {t for n in jd_config["hard_requirements"] for t in groups.get(n, [])}
    out["hard_req_keyword_count"] = _count_group_hits(stext, list(hard_terms))
    out["hard_req_career_count"] = _count_group_hits(ctext, list(hard_terms))
    # the SIGNATURE OF THE TRAP: many skill keywords, little career evidence
    out["keyword_evidence_gap"] = round(
        max(0.0, (out["hard_req_keyword_count"] / 4.0)
            - (out["hard_req_career_count"] / 4.0)), 3)
    return out


# ---------------------------------------------------------------------------
# Production / shipping evidence (JD's #1 priority)
# ---------------------------------------------------------------------------
def production_evidence(c: dict, groups: dict) -> dict:
    ctext = career_text(c)
    prod_terms = groups.get("production_evidence", [])
    hits = _count_group_hits(ctext, prod_terms)
    # also reward retrieval/ranking evidence appearing NEAR production language
    retr = groups.get("embeddings_retrieval", []) + groups.get("vector_search_infra", [])
    retr_hits = _count_group_hits(ctext, retr)
    score = (1 - 0.6 ** hits) if hits else 0.0
    shipped_relevant = 1.0 if (hits and retr_hits) else 0.0
    return {
        "production_evidence_score": round(score, 3),
        "production_hit_count": hits,
        "shipped_relevant_system": shipped_relevant,
    }


# ---------------------------------------------------------------------------
# Career trajectory: product vs services, recency-weighted
# ---------------------------------------------------------------------------
def career_trajectory(c: dict, jd_config: dict) -> dict:
    hist = c.get("career_history", [])
    firms = jd_config.get("consulting_firms", [])
    total_months = sum(r.get("duration_months", 0) for r in hist) or 1

    services_months = 0
    recent_services_months = 0   # last 2 roles weighted 2x
    hist_sorted = sorted(hist, key=lambda r: r.get("start_date", ""), reverse=True)
    for i, r in enumerate(hist_sorted):
        comp = r.get("company", "").lower()
        is_serv = any(f in comp for f in firms) or r.get("industry", "").lower() == "it services"
        m = r.get("duration_months", 0)
        if is_serv:
            services_months += m
            if i < 2:
                recent_services_months += m
    services_ratio = services_months / total_months
    # recency-weighted: recent services hurts more (JD: "currently at one of these but
    # prior product experience is fine")
    recency_weighted_services = min(1.0, (services_months + recent_services_months) /
                                    (total_months + sum(r.get("duration_months", 0)
                                     for r in hist_sorted[:2])))
    return {
        "services_ratio": round(services_ratio, 3),
        "consulting_penalty": round(recency_weighted_services, 3),
        "pure_consulting_career": float(services_ratio >= 0.95),
        "total_career_months": total_months,
        "n_roles": len(hist),
    }


# ---------------------------------------------------------------------------
# Experience fit (5-9 band, soft)
# ---------------------------------------------------------------------------
def experience_fit(c: dict, jd_config: dict) -> dict:
    yoe = c["profile"].get("years_of_experience", 0.0)
    lo, hi = jd_config["min_yoe"], jd_config["max_yoe"]
    ilo, ihi = jd_config.get("yoe_ideal_low", 6), jd_config.get("yoe_ideal_high", 8)
    if ilo <= yoe <= ihi:
        fit = 1.0
    elif lo <= yoe <= hi:
        fit = 0.85
    elif (lo - 1) <= yoe <= (hi + 1):
        fit = 0.6
    elif (lo - 2) <= yoe <= (hi + 3):
        fit = 0.35
    else:
        fit = 0.1
    return {"years_of_experience": yoe, "yoe_fit": round(fit, 3)}


# ---------------------------------------------------------------------------
# Title signal (engineering vs not) — anchor-helper + trap detector
# ---------------------------------------------------------------------------
ENG_TOKENS = ["engineer", "developer", "scientist", "architect", "ml", "ai ",
              "applied scien", "data scien", "research engineer", "sde", "swe"]
NONTECH_TOKENS = ["manager", "marketing", "sales", "hr ", "human resource", "recruiter",
                  "operations", "consultant", "analyst", "coordinator", "executive",
                  "administrator", "designer", "writer", "specialist"]


def title_signal(c: dict) -> dict:
    title = c["profile"].get("current_title", "").lower()
    is_eng = any(t in title for t in ENG_TOKENS)
    is_nontech = any(t in title for t in NONTECH_TOKENS) and not is_eng
    return {
        "is_engineering_title": float(is_eng),
        "is_nontechnical_title": float(is_nontech),
    }


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------
def education_features(c: dict) -> dict:
    edu = c.get("education", [])
    tiers = {"tier_1": 4, "tier_2": 3, "tier_3": 2, "tier_4": 1, "unknown": 1}
    best = max((tiers.get(e.get("tier", "unknown"), 1) for e in edu), default=1)
    fields = " ".join(e.get("field_of_study", "").lower() for e in edu)
    tech_field = float(any(k in fields for k in
                      ["computer", "software", "data", "machine learning", "artificial",
                       "electrical", "electronics", "information", "mathematics", "statistics"]))
    return {"edu_tier_best": best, "edu_tech_field": tech_field}


# ---------------------------------------------------------------------------
# Behavioral availability (JD EXPLICITLY asks to down-weight inactive/unresponsive)
# ---------------------------------------------------------------------------
def behavioral_features(c: dict, ref: date) -> dict:
    sig = c["redrob_signals"]
    last_active = _parse_date(sig.get("last_active_date"))
    days_inactive = (ref - last_active).days if last_active else 365
    # availability multiplier: fresh+responsive ~1.0 ; stale+unresponsive ~0.5
    inactivity_factor = max(0.0, 1 - days_inactive / 180)        # 0 at 6 months
    response = sig.get("recruiter_response_rate", 0.0)
    open_flag = 1.0 if sig.get("open_to_work_flag") else 0.0
    saved = min(1.0, sig.get("saved_by_recruiters_30d", 0) / 10.0)
    availability = (0.40 * inactivity_factor + 0.30 * response +
                    0.20 * open_flag + 0.10 * saved)
    # JD: "perfect-on-paper but hasn't logged in 6 months + 5% response = not available"
    availability_multiplier = 0.5 + 0.5 * availability     # never zero out entirely
    return {
        "days_inactive": days_inactive,
        "recruiter_response_rate": round(response, 3),
        "open_to_work": open_flag,
        "availability_score": round(availability, 3),
        "availability_multiplier": round(availability_multiplier, 3),
    }


# ---------------------------------------------------------------------------
# Logistics (location, notice, relocation)
# ---------------------------------------------------------------------------
def logistics_features(c: dict, jd_config: dict) -> dict:
    prof = c["profile"]
    sig = c["redrob_signals"]
    loc = (prof.get("location", "") + " " + prof.get("country", "")).lower()
    in_india = "india" in prof.get("country", "").lower()
    in_pref = any(x in loc for x in jd_config.get("preferred_locs", []))
    relocate = bool(sig.get("willing_to_relocate"))

    if in_pref:
        location_score = 1.0
    elif in_india:
        location_score = 0.7 if relocate else 0.55
    elif relocate:
        location_score = 0.4
    else:
        location_score = 0.05      # outside India + won't relocate => near-zero (JD hard line)

    notice = sig.get("notice_period_days", 90)
    if notice <= 30:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.7
    elif notice <= 90:
        notice_score = 0.5
    else:
        notice_score = 0.3
    return {
        "in_india": float(in_india),
        "in_preferred_loc": float(in_pref),
        "willing_to_relocate": float(relocate),
        "location_score": round(location_score, 3),
        "notice_period_days": notice,
        "notice_score": round(notice_score, 3),
    }
