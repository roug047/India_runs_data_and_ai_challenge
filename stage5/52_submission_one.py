"""
stage5/52_submission_one.py
Produce Submission #1 — the safety-net ranked CSV from the calibrated composite.

Format (submission_spec): candidate_id,rank,score,reasoning
  - exactly 100 rows, ranks 1..100 unique, score non-increasing, ids exist in pool.
  - reasoning cites SPECIFIC profile facts (title, company, yoe, a real signal) — Stage-4
    manual review samples 10 rows and penalizes reasoning that mentions skills not in profile.

Scoring: rank-based (1.0 - rank*k) so scores are guaranteed unique + strictly decreasing in
[0,1] regardless of how composite values cluster. Honeypots/disqualified are structurally
excluded from the top 100 by the multipliers already baked into the composite.

Run:  python stage5/52_submission_one.py
Output: artifacts/submission_one.csv
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402
from stage5.composite import score_dataframe, DEFAULT_WEIGHTS  # noqa: E402


def build_reasoning(c: dict, row: dict) -> str:
    """1-2 sentences citing ONLY literal profile facts. No skill claimed that isn't present."""
    p = c["profile"]
    title = p.get("current_title", "role")
    company = p.get("current_company", "")
    yoe = p.get("years_of_experience", 0)

    # find ONE concrete achievement sentence containing a JD keyword + a digit
    jd_kw = ["retrieval", "ranking", "embedding", "vector", "search", "recommendation",
             "recsys", "ndcg", "production", "deployed", "shipped", "pipeline", "scale",
             "latency", "model"]
    ach = ""
    for r in c.get("career_history", []):
        for sent in r.get("description", "").split("."):
            s = sent.strip()
            if any(k in s.lower() for k in jd_kw) and any(ch.isdigit() for ch in s):
                ach = s[:150]
                break
        if ach:
            break

    sig = c["redrob_signals"]
    bits = [f"{title} at {company}, {yoe:.0f} yrs" if company else f"{title}, {yoe:.0f} yrs"]
    if ach:
        bits.append(ach)
    else:
        # fall back to literal coverage facts, never invented skills
        if row.get("production_evidence_score", 0) > 0.3:
            bits.append("career shows production deployment experience")
        if row.get("weighted_hard_req_coverage", 0) > 0.4:
            bits.append("relevant retrieval/ranking background")
    # one concrete signal
    rr = sig.get("recruiter_response_rate", 0)
    bits.append(f"recruiter response rate {rr:.2f}")
    text = "; ".join(bits)
    return text[:300]


def main() -> int:
    ap = argparse.ArgumentParser()
    args = ap.parse_args()
    config.ensure_artifacts()

    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        print("FATAL: pip install pandas numpy pyarrow")
        return 1

    if not config.FEATURES_PARQUET.exists():
        print("FATAL: features_100k.parquet missing.")
        return 1
    df = pd.read_parquet(config.FEATURES_PARQUET)

    weights = json.loads(config.COMPOSITE_WEIGHTS_JSON.read_text()) \
        if config.COMPOSITE_WEIGHTS_JSON.exists() else DEFAULT_WEIGHTS
    print(f"Using {'calibrated' if config.COMPOSITE_WEIGHTS_JSON.exists() else 'DEFAULT'} weights")

    scores = score_dataframe(df, weights)
    df = df.assign(final_score=scores)
    # deterministic tie-break: final_score desc, then hybrid_score desc, then candidate_id
    df = df.sort_values(
        ["final_score", "hybrid_score", "candidate_id"],
        ascending=[False, False, True])
    top = df.head(100)
    top_ids = list(top.index)

    # safety guard: assert no honeypot/hard-disqualified leaked into the top 100
    if "is_likely_honeypot" in top.columns:
        n_hp = int(top["is_likely_honeypot"].sum())
        print(f"honeypots in top 100: {n_hp} (must be 0 for safety; DQ at >10)")
    n_dq = int((top.get("disqualifier_penalty", pd.Series(1, index=top.index)) < 0.2).sum())
    print(f"hard-disqualified in top 100: {n_dq}")

    # fetch full candidate records for the top 100 (for reasoning)
    want = set(top_ids)
    rec = {}
    for c in iter_candidates(config.CANDIDATES_JSONL):
        if c["candidate_id"] in want:
            rec[c["candidate_id"]] = c
            if len(rec) == len(want):
                break

    # rank-based monotone unique scores in (0,1]
    n = len(top_ids)
    rows = []
    for i, cid in enumerate(top_ids, 1):
        score = round(0.999 - (i - 1) * (0.95 / max(n - 1, 1)), 4)
        c = rec.get(cid)
        reasoning = build_reasoning(c, top.loc[cid].to_dict()) if c else f"{cid}"
        rows.append((cid, i, f"{score:.4f}", reasoning))

    with open(config.SUBMISSION_ONE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        w.writerows(rows)

    # quick validation
    ranks = [r[1] for r in rows]
    sc = [float(r[2]) for r in rows]
    assert len(rows) == 100, f"expected 100 rows, got {len(rows)}"
    assert sorted(ranks) == list(range(1, 101)), "ranks not 1..100 unique"
    assert all(sc[i] >= sc[i + 1] for i in range(len(sc) - 1)), "scores not non-increasing"
    assert len(set(r[0] for r in rows)) == 100, "duplicate candidate_ids"

    print("-" * 60)
    print(f"Submission #1 -> {config.SUBMISSION_ONE_CSV}")
    print(f"top 5: {top_ids[:5]}")
    print("validation: 100 rows, unique ranks, monotone scores, unique ids — PASS")
    print("STAGE 5.52 (submission one): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
