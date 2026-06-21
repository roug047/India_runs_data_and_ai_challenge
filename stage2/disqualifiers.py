"""
stage2/disqualifiers.py
Compute the 7 JD disqualifier flags, each traceable to a JD sentence, with the JD's
explicit RESCUE conditions (so we don't over-fire on legitimately-pivoted candidates).

Returns a dict of 0/1 flags plus a single multiplicative `disqualifier_penalty` in (0,1].
Stage 5 applies the penalty; Stage 2 just computes it.

Penalty philosophy: hard rejects ("we will not move forward") cut deep; soft rejects
("we will probably not move forward") cut moderately. We take the MIN penalty across fired
flags (most severe wins) rather than multiplying them, to avoid double/triple-stacking that
would bury a candidate for a single underlying issue.
"""
from __future__ import annotations
from datetime import date

from stage2.features_core import (
    career_text, recent_career_text, skills_text, _count_group_hits, _parse_date,
)

# Severity of each flag = the multiplier applied if it fires (lower = harsher).
PENALTY = {
    "pure_research_no_prod":        0.10,   # JD: "we will not move forward" (most emphatic)
    "pure_consulting_career":       0.12,   # "entire career" at services firms
    "cv_speech_robotics_only":      0.15,   # "re-learning fundamentals here"
    "langchain_only_under_12mo":    0.25,   # "we will probably not move forward, unless..."
    "no_code_18mo":                 0.30,   # "we will probably not move forward"
    "closed_source_no_validation":  0.35,   # "we need to see how you think"
    "title_chaser":                 0.55,   # soft-negative, penalize not reject
}


def compute_disqualifiers(c: dict, jd_config: dict, groups: dict, feats: dict,
                          ref: date) -> dict:
    flags: dict[str, float] = {}
    ctext = career_text(c)
    rtext = recent_career_text(c)
    stext = skills_text(c)
    hist = c.get("career_history", [])

    # 1. pure_research_no_prod — research/academic-style career AND no production deployment.
    #    Title list matches how THIS dataset names research roles (AI Research Engineer,
    #    Data Scientist, Applied Scientist). The production + thin-evidence gates discriminate:
    #    anyone who shipped to production or has real hard-req career evidence does NOT fire,
    #    regardless of title.
    research_title_tokens = ["research", "researcher", "scientist", "postdoc",
                             "post-doctoral", "research fellow", "phd", "applied scien"]
    all_titles = " ".join(r.get("title", "").lower() for r in hist)
    research_titles = sum(1 for tok in research_title_tokens if tok in all_titles)
    research_text = _count_group_hits(ctext, groups["pure_research"])
    no_prod = feats.get("production_evidence_score", 0) < 0.12
    thin_evidence = feats.get("hard_req_career_count", 0) < 1
    flags["pure_research_no_prod"] = float(
        (research_titles >= 1 or research_text >= 2) and no_prod and thin_evidence)

    # 2. pure_consulting_career — already computed in trajectory; mirror it.
    flags["pure_consulting_career"] = feats.get("pure_consulting_career", 0.0)

    # 3. cv_speech_robotics_only — CV/speech/robotics primary AND little NLP/IR (RESCUE).
    cv_hits = _count_group_hits(ctext, groups["cv_speech_robotics"]) + \
        _count_group_hits(stext, groups["cv_speech_robotics"])
    nlp_hits = _count_group_hits(ctext, groups["nlp_ir"]) + \
        _count_group_hits(stext, groups["nlp_ir"])
    flags["cv_speech_robotics_only"] = float(cv_hits >= 3 and nlp_hits < 2)

    # 4. langchain_only_under_12mo — LangChain-framework AI as the ONLY AI signal, with no
    #    substantial pre-LLM ML production. The "<12mo" refers to AI EXPERIENCE being shallow,
    #    NOT total career length. Fires when LangChain is present but there's no deeper ML/IR
    #    production depth (framework demos only).
    lc_hits = _count_group_hits(ctext, groups["langchain_framework"]) + \
        _count_group_hits(stext, groups["langchain_framework"])
    pre_llm_ml = feats.get("hard_req_career_count", 0) >= 2 or \
        feats.get("production_evidence_score", 0) >= 0.4
    flags["langchain_only_under_12mo"] = float(lc_hits >= 1 and not pre_llm_ml)

    # 5. no_code_18mo — recent roles are management/architecture, no production code lately.
    mgmt_recent = _count_group_hits(rtext, groups["management_only"])
    codes_recently = _count_group_hits(rtext, groups["python_production"]) >= 1 or \
        _count_group_hits(rtext, groups["embeddings_retrieval"]) >= 1
    flags["no_code_18mo"] = float(mgmt_recent >= 1 and not codes_recently
                                  and c["profile"].get("years_of_experience", 0) >= 8)

    # 6. closed_source_no_validation — 5+ yr services/closed AND no external validation.
    services_months = feats.get("total_career_months", 0) * feats.get("services_ratio", 0)
    long_closed = services_months >= 60
    has_external = (_count_group_hits(ctext, groups["open_source"]) +
                    _count_group_hits(stext, groups["open_source"])) >= 1 or \
        c["redrob_signals"].get("github_activity_score", -1) >= 30
    flags["closed_source_no_validation"] = float(long_closed and not has_external)

    # 7. title_chaser — short average tenure with title-climbing pattern.
    if len(hist) >= 3:
        durations = [r.get("duration_months", 0) for r in hist if not r.get("is_current")]
        avg_tenure = sum(durations) / len(durations) if durations else 99
        flags["title_chaser"] = float(avg_tenure < 18)
    else:
        flags["title_chaser"] = 0.0

    # --- aggregate: most-severe penalty wins (MIN), default no penalty (1.0) ---
    fired = [PENALTY[name] for name, v in flags.items() if v >= 1.0]
    penalty = min(fired) if fired else 1.0
    flags["disqualifier_hit"] = bool(fired)
    flags["disqualifier_penalty"] = round(penalty, 3)
    flags["n_disqualifiers_fired"] = len(fired)
    return flags