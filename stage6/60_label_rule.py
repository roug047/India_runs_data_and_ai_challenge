"""
stage6/60_label_rule.py
Label a stratified training sample with a DETERMINISTIC rule-based scorer (0-3).

This is label source A — fully deterministic, free, instant, defensible. It encodes the
JD's priorities directly from features (no LLM). It is intentionally INDEPENDENT of the
local-LLM labeler (source B) so the two rankers in Stage 6 make different errors, and the
anchor-tuned blend can play them off each other.

Stratified sampling: we don't label random candidates. We oversample the interesting middle
and the top (where ranking precision matters) and include enough clear-negatives for contrast.

Run:  python stage6/60_label_rule.py --n 4000
Output: artifacts/train_labels_rule.json  {candidate_id: 0|1|2|3}
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402


def rule_label(row: dict) -> int:
    """Deterministic 0-3 fit label from features. Mirrors the JD's stated priorities."""
    # hard exclusions first
    if row.get("disqualifier_penalty", 1.0) < 0.2:
        return 0
    if row.get("is_likely_honeypot", False):
        return 0
    if row.get("location_score", 1.0) < 0.1:        # outside India + won't relocate
        return 0
    if row.get("years_of_experience", 0) < 2:
        return 0

    score = 0.0
    # production + retrieval/ranking evidence (JD #1)
    score += 3.0 * row.get("production_evidence_score", 0)
    score += 2.5 * row.get("weighted_hard_req_coverage", 0)
    score += 1.0 * row.get("hybrid_score", 0)
    score += 1.0 * row.get("weighted_soft_req_coverage", 0)
    score += 0.8 * row.get("yoe_fit", 0)
    score += 0.5 * row.get("shipped_relevant_system", 0)
    score += 0.5 * row.get("location_score", 0)
    # apply soft multipliers
    score *= row.get("disqualifier_penalty", 1.0)
    score *= row.get("availability_multiplier", 1.0)

    # thresholds tuned so the distribution spans all four labels
    if score >= 4.2:
        return 3
    if score >= 2.8:
        return 2
    if score >= 1.4:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    config.ensure_artifacts()

    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        print("FATAL: pip install pandas numpy pyarrow")
        return 1

    df = pd.read_parquet(config.FEATURES_PARQUET)
    rng = np.random.default_rng(args.seed)

    # stratified sample: 40% from top-5000 by hybrid (where precision matters),
    # 35% from the middle band, 25% random (clear negatives + coverage).
    by_hybrid = df.sort_values("hybrid_score", ascending=False)
    n_top = int(args.n * 0.40)
    n_mid = int(args.n * 0.35)
    n_rand = args.n - n_top - n_mid

    top_pool = by_hybrid.head(5000).index.to_numpy()
    mid_pool = by_hybrid.iloc[5000:40000].index.to_numpy()
    rand_pool = df.index.to_numpy()

    pick = set()
    for pool, k in [(top_pool, n_top), (mid_pool, n_mid), (rand_pool, n_rand)]:
        k = min(k, len(pool))
        pick.update(rng.choice(pool, size=k, replace=False).tolist())
    pick = list(pick)

    labels = {}
    for cid in pick:
        labels[cid] = rule_label(df.loc[cid].to_dict())

    config.TRAIN_LABELS_RULE_JSON.write_text(json.dumps(labels))
    from collections import Counter
    dist = dict(sorted(Counter(labels.values()).items()))
    print(f"rule-labeled {len(labels)} candidates  distribution: {dist}")
    print(f"-> {config.TRAIN_LABELS_RULE_JSON}")
    print("STAGE 6.60 (rule labels): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
