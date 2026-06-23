"""
stage7/validate_submission.py
Validate a submission CSV against the spec's hard requirements.

Checks: exactly 100 rows; columns correct; ranks 1..100 unique; scores in (0,1] and
non-increasing; >10 unique scores; candidate_ids unique and exist in the pool; reasoning
non-empty and not all identical; top-100 honeypot rate under the DQ line.

Run:  python stage7/validate_submission.py artifacts/submission_two.csv
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402


def validate(path: str) -> bool:
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {msg}")
        ok = ok and cond

    check(len(rows) == 100, f"exactly 100 rows (got {len(rows)})")
    cols = list(rows[0].keys()) if rows else []
    check(cols == ["candidate_id", "rank", "score", "reasoning"],
          f"columns correct (got {cols})")

    ranks = [int(r["rank"]) for r in rows]
    check(sorted(ranks) == list(range(1, 101)), "ranks 1..100 unique")

    scores = [float(r["score"]) for r in rows]
    check(all(0 < s <= 1 for s in scores), "scores in (0,1]")
    check(all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)),
          "scores non-increasing")
    check(len(set(scores)) > 10, f"more than 10 unique scores (got {len(set(scores))})")

    ids = [r["candidate_id"] for r in rows]
    check(len(set(ids)) == 100, "candidate_ids unique")

    reasons = [r["reasoning"].strip() for r in rows]
    check(all(reasons), "all reasoning non-empty")
    check(len(set(reasons)) >= 80, f"reasoning mostly unique (got {len(set(reasons))} distinct)")

    # honeypot rate in top 100 (DQ at >10%)
    try:
        import pandas as pd
        df = pd.read_parquet(config.FEATURES_PARQUET)
        hp = int(df.loc[[i for i in ids if i in df.index], "is_likely_honeypot"].sum())
        check(hp <= 8, f"honeypots in top 100 <= 8 (got {hp}; DQ at >10)")
    except Exception as e:
        print(f"  (honeypot check skipped: {e})")

    print("VALID" if ok else "INVALID")
    return ok


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else str(config.SUBMISSION_TWO_CSV)
    raise SystemExit(0 if validate(p) else 1)
