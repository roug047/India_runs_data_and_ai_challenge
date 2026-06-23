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

    # 2. which SPECIFIC hard requirement they cover best (varies)
    covered = [(lbl, row.get(col, 0)) for col, lbl in _HARD_REQ_LABEL.items()]
    covered = [(lbl, v) for lbl, v in covered if v and v > 0.3]
    covered.sort(key=lambda t: -t[1])
    if covered:
        top_reqs = ", ".join(lbl for lbl, _ in covered[:2])
        bits.append(f"demonstrated {top_reqs}")

    # 3. production / shipping signal (varies by score)
    if row.get("shipped_relevant_system", 0) >= 1:
        bits.append("shipped a relevant retrieval/ranking system")
    elif row.get("production_evidence_score", 0) > 0.5:
        bits.append("production deployment experience")

    # 4. a DISTINGUISHING skill actually in their profile (varies; never invented)
    jd_skill_terms = ["vector search", "learning to rank", "faiss", "milvus", "weaviate",
                      "qdrant", "elasticsearch", "opensearch", "recommendation",
                      "collaborative filtering", "re-ranking", "embeddings", "fine-tuning",
                      "lora", "semantic search", "ndcg"]
    listed = [s.get("name", "") for s in c.get("skills", [])]
    listed_lower = [s.lower() for s in listed]
    matched_skill = next((s for s in listed if any(t in s.lower() for t in jd_skill_terms)), None)
    if matched_skill:
        bits.append(f"skills incl. {matched_skill}")

    # 5. one concrete logistics/availability signal (varies)
    sig = c["redrob_signals"]
    notice = sig.get("notice_period_days")
    loc = p.get("location", "")
    extras = []
    if loc:
        extras.append(loc.split(",")[0])
    if notice is not None:
        extras.append(f"{notice}d notice")
    rr = sig.get("recruiter_response_rate")
    if rr is not None:
        extras.append(f"resp {rr:.2f}")
    if extras:
        bits.append("; ".join(extras))

    text = ". ".join(bits)
    return text[:300]
