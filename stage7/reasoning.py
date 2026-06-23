"""
stage7/reasoning.py
Generate diversified, fact-grounded reasoning for a candidate.

Problem (found in Stage 5): the dataset reuses career-description sentences across candidates,
so naive "first achievement sentence" extraction repeats verbatim. Fix: compose reasoning
from MULTIPLE distinguishing facts that vary per candidate — company, the SPECIFIC hard
requirement they match, their distinguishing skill, a concrete signal — so two candidates
with the same templated sentence still get different reasoning.

Hard rule: cite ONLY literal facts present in the profile/features. Never assert a skill the
candidate doesn't list (Stage-4 manual review penalizes invented skills).
"""
from __future__ import annotations

_HARD_REQ_LABEL = {
    "cov_embeddings_retrieval": "embeddings/retrieval",
    "cov_vector_search_infra": "vector search infrastructure",
    "cov_ranking_evaluation": "ranking evaluation (NDCG/MRR)",
    "cov_python_production": "production Python",
}


def build_reasoning(c: dict, row: dict) -> str:
    p = c["profile"]
    title = p.get("current_title", "").strip()
    company = p.get("current_company", "").strip()
    yoe = p.get("years_of_experience", 0)

    bits = []
    # 1. who they are (varies by candidate)
    head = f"{title} at {company}" if company else title
    bits.append(f"{head} ({yoe:.0f}y)")

    # 2. a LITERAL achievement sentence from their career history — quoted, not inferred.
    #    Prefer a sentence containing a JD-relevant term AND a number (concrete impact).
    jd_terms = ["retrieval", "ranking", "rank", "embedding", "vector", "search",
                "recommendation", "recsys", "ndcg", "mrr", "production", "deployed",
                "shipped", "latency", "throughput", "qps", "model", "pipeline"]
    best_sentence = ""
    fallback_sentence = ""
    for r in c.get("career_history", []):
        for raw in r.get("description", "").replace("\n", " ").split("."):
            s = raw.strip()
            if len(s) < 20:
                continue
            low = s.lower()
            has_term = any(t in low for t in jd_terms)
            has_num = any(ch.isdigit() for ch in s)
            if has_term and has_num and not best_sentence:
                best_sentence = s
            elif has_term and not fallback_sentence:
                fallback_sentence = s
        if best_sentence:
            break
    quote = best_sentence or fallback_sentence
    if quote:
        bits.append(quote[:160])

    # 3. which SPECIFIC hard requirement they cover best (varies, from features)
    covered = [(lbl, row.get(col, 0)) for col, lbl in _HARD_REQ_LABEL.items()]
    covered = [(lbl, v) for lbl, v in covered if v and v > 0.3]
    covered.sort(key=lambda t: -t[1])
    if covered:
        bits.append("strong on " + ", ".join(lbl for lbl, _ in covered[:2]))

    # 4. one concrete logistics/availability fact (varies)
    sig = c["redrob_signals"]
    loc = p.get("location", "")
    extras = []
    if loc:
        extras.append(loc.split(",")[0])
    notice = sig.get("notice_period_days")
    if notice is not None:
        extras.append(f"{notice}d notice")
    if extras:
        bits.append("; ".join(extras))

    text = ". ".join(bits)
    return text[:320]
