"""
stage7/70_generate_top40.py
Generate the top-40 candidates by the final scoring engine, as a human-readable review CSV.

You READ these 40 (especially the top 30 — 55% of score is NDCG@10) and decide for each:
keep / demote / remove. Record decisions in audit_log.json (use 71_make_audit_template.py
to scaffold it). rank.py applies the audit deterministically.

Run:  python stage7/70_generate_top40.py
Output: artifacts/top40_review.csv
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402
from stage7.scoring import compute_final_scores  # noqa: E402


def main() -> int:
    try:
        import pandas as pd
    except ImportError:
        print("FATAL: pip install pandas pyarrow lightgbm scikit-learn scipy")
        return 1

    df = pd.read_parquet(config.FEATURES_PARQUET)
    scores = compute_final_scores(df, config.ARTIFACTS)
    df = df.assign(final_score=scores).sort_values(
        ["final_score", "candidate_id"], ascending=[False, True])
    top = df.head(40)
    ids = list(top.index)

    # pull raw records for the readable review
    want = set(ids)
    rec = {}
    for c in iter_candidates(config.CANDIDATES_JSONL):
        if c["candidate_id"] in want:
            rec[c["candidate_id"]] = c
            if len(rec) == len(want):
                break

    fields = ["audit_rank", "candidate_id", "final_score", "title", "company", "yoe",
              "location", "country", "notice", "hard_req_cov", "production",
              "honeypot_score", "disqualifier_penalty", "summary"]
    with open(config.TOP40_REVIEW_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, cid in enumerate(ids, 1):
            c = rec.get(cid, {})
            p = c.get("profile", {})
            row = top.loc[cid]
            w.writerow({
                "audit_rank": i, "candidate_id": cid,
                "final_score": round(float(row["final_score"]), 4),
                "title": p.get("current_title", ""), "company": p.get("current_company", ""),
                "yoe": p.get("years_of_experience", ""),
                "location": p.get("location", ""), "country": p.get("country", ""),
                "notice": c.get("redrob_signals", {}).get("notice_period_days", ""),
                "hard_req_cov": round(float(row.get("weighted_hard_req_coverage", 0)), 3),
                "production": round(float(row.get("production_evidence_score", 0)), 3),
                "honeypot_score": round(float(row.get("honeypot_score", 1)), 3),
                "disqualifier_penalty": round(float(row.get("disqualifier_penalty", 1)), 3),
                "summary": p.get("summary", "")[:200],
            })

    print(f"top-40 review -> {config.TOP40_REVIEW_CSV}")
    print("READ the top 30. For any that don't belong, add an entry to audit_log.json:")
    print('  {"CAND_xxx": {"action":"remove","reason":"..."}}  or')
    print('  {"CAND_xxx": {"action":"demote","to_rank":35,"reason":"..."}}')
    print("Then run stage7/72_rank.py")
    print("STAGE 7.70 (top-40): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
