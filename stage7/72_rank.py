#!/usr/bin/env python3
"""
stage7/72_rank.py  (deploy as rank.py at repo root for the organizers)
THE reproduced step. CPU-only, no network, <=5 min, <=16GB.

Loads precomputed artifacts (features, ranker models, embeddings already baked into the
feature table's hybrid_score), scores with the blended ranker (composite tie-break), applies
the documented human audit, gates honeypots/disqualified, and writes the 100-row submission.

NO GPU. NO NETWORK. Everything heavy (embeddings, training) happened in precompute.

Usage:
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# never reach out to HF or anywhere
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402
from stage7.scoring import compute_final_scores  # noqa: E402
from stage7.reasoning import build_reasoning      # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=str(config.CANDIDATES_JSONL))
    ap.add_argument("--out", default="submission.csv")
    args = ap.parse_args()
    t0 = time.time()

    import pandas as pd
    import numpy as np

    df = pd.read_parquet(config.FEATURES_PARQUET)

    # restrict to the candidate file passed in (handles the sandbox pool)
    file_ids = [c["candidate_id"] for c in iter_candidates(Path(args.candidates))]
    df = df[df.index.isin(set(file_ids))]
    print(f"scoring {len(df)} candidates")

    df = df.assign(final_score=compute_final_scores(df, config.ARTIFACTS))

    # --- apply documented human audit (reproducible overrides) ---
    try:
        audit = json.loads(config.AUDIT_LOG_JSON.read_text())
    except FileNotFoundError:
        audit = {}

    # removes first
    for cid, a in audit.items():
        if cid in df.index and a.get("action") == "remove":
            df.loc[cid, "final_score"] = 0.0

    df = df.sort_values(["final_score", "candidate_id"], ascending=[False, True])

    # to_rank demotions: place candidate just below the score at the target position
    demotes = [(cid, int(a["to_rank"])) for cid, a in audit.items()
               if cid in df.index and a.get("action") == "demote" and "to_rank" in a]
    for cid, target in demotes:
        order = df.sort_values("final_score", ascending=False)
        vals = order["final_score"].values
        if 0 < target < len(vals):
            hi = vals[target - 1]
            lo = vals[target] if target < len(vals) else 0.0
            df.loc[cid, "final_score"] = (hi + lo) / 2.0
    if demotes:
        df = df.sort_values(["final_score", "candidate_id"], ascending=[False, True])

    n_out = min(100, len(df))
    top = df.head(n_out)
    top_ids = list(top.index)

    # safety: no honeypot / hard-disqualified in the final top 100
    if "is_likely_honeypot" in top.columns:
        nhp = int(top["is_likely_honeypot"].sum())
        if nhp:
            print(f"WARNING: {nhp} honeypots in top 100 (should be 0)")

    # pull raw records for reasoning
    want = set(top_ids)
    rec = {}
    for c in iter_candidates(Path(args.candidates)):
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
        reasoning = build_reasoning(c, top.loc[cid].to_dict()) if c else cid
        rows.append((cid, i, f"{score:.4f}", reasoning))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        w.writerows(rows)

    # self-validate
    ranks = [r[1] for r in rows]
    sc = [float(r[2]) for r in rows]
    assert len(rows) == n_out, f"expected 100 rows, got {len(rows)}"
    assert sorted(ranks) == list(range(1, n_out + 1)), "ranks not 1..100"
    assert all(sc[i] >= sc[i + 1] for i in range(len(sc) - 1)), "scores not non-increasing"
    assert len(set(r[0] for r in rows)) == n_out, "dup ids"

    print(f"submission -> {args.out}")
    print(f"top 5: {top_ids[:5]}")
    print(f"elapsed: {time.time() - t0:.1f}s  (limit 300s)")
    print("STAGE 7.72 (rank.py): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
