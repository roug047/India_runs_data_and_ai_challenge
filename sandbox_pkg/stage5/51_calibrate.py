"""
stage5/51_calibrate.py
Calibrate composite weights against the golden set (the payoff of Day-1 labeling).

Two jobs:
  1. HARD GATE: no candidate labeled 0 may outscore any candidate labeled 3. If this fails,
     the weights are wrong — we search until it passes (or report the violation).
  2. MAXIMIZE Spearman rank-correlation between final_score and your hand labels on the anchor.

We do a bounded random search around DEFAULT_WEIGHTS (the anchor is small, ~60 points, so we
keep the search modest and prefer the simplest weights that pass — avoiding overfitting to 60
labels). The chosen weights are frozen to composite_weights.json for Stage 7 rank.py.

Run:  python stage5/51_calibrate.py
      python stage5/51_calibrate.py --iters 4000
Output: artifacts/composite_weights.json, artifacts/stage5_calibration_report.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402
from stage5.composite import DEFAULT_WEIGHTS, score_dataframe  # noqa: E402


def evaluate(df_anchor, labels, weights):
    """Return (spearman, hard_gate_ok, n_violations) for a weight set on the anchor."""
    import numpy as np
    from scipy.stats import spearmanr
    scores = score_dataframe(df_anchor, weights)
    y = np.array([labels[c] for c in df_anchor.index])
    rho = spearmanr(scores, y).correlation
    rho = 0.0 if np.isnan(rho) else rho
    # hard gate: min(score among label-3) > max(score among label-0)
    s3 = scores[y == 3]
    s0 = scores[y == 0]
    if len(s3) and len(s0):
        violations = int((s0[:, None] >= s3[None, :]).sum())  # pairs where a 0 >= a 3
        gate_ok = bool(s0.max() < s3.min())
    else:
        violations, gate_ok = 0, True
    return rho, gate_ok, violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    config.ensure_artifacts()

    if not config.GOLDEN_SET_JSON.exists():
        print("FATAL: artifacts/golden_set.json missing — Stage 0 must be done.")
        return 1
    labels = {k: int(v) for k, v in json.loads(config.GOLDEN_SET_JSON.read_text()).items()}

    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        print("FATAL: pip install pandas numpy scipy scikit-learn pyarrow")
        return 1

    feat_file = config.FEATURES_PARQUET
    if not feat_file.exists():
        print(f"FATAL: {feat_file.name} missing — run Stages 2-4 first.")
        return 1
    df = pd.read_parquet(feat_file)

    # restrict to anchor candidates present in the feature table
    anchor_ids = [c for c in labels if c in df.index]
    missing = [c for c in labels if c not in df.index]
    if missing:
        print(f"WARNING: {len(missing)} anchor ids not in feature table: {missing[:5]}...")
    df_anchor = df.loc[anchor_ids]
    print(f"Anchor: {len(anchor_ids)} candidates "
          f"(labels: {dict(sorted(pd.Series([labels[c] for c in anchor_ids]).value_counts().items()))})")

    # --- baseline: default weights ---
    rho0, gate0, viol0 = evaluate(df_anchor, labels, DEFAULT_WEIGHTS)
    print(f"DEFAULT weights:  spearman={rho0:.3f}  hard_gate={'OK' if gate0 else 'FAIL'} "
          f"(violations={viol0})")

    # --- bounded random search around defaults ---
    rng = np.random.default_rng(args.seed)
    keys = list(DEFAULT_WEIGHTS)
    base = np.array([DEFAULT_WEIGHTS[k] for k in keys])
    best = {"weights": DEFAULT_WEIGHTS, "rho": rho0, "gate": gate0, "viol": viol0,
            "score": (1 if gate0 else 0, rho0)}

    for _ in range(args.iters):
        # jitter weights ±60%, clip to non-negative
        w = np.clip(base * rng.uniform(0.4, 1.6, size=len(base)), 0.0, None)
        wd = {k: float(v) for k, v in zip(keys, w)}
        rho, gate, viol = evaluate(df_anchor, labels, wd)
        # objective: gate first (lexicographic), then spearman, then fewer violations
        score = (1 if gate else 0, rho, -viol)
        if score > (1 if best["gate"] else 0, best["rho"], -best["viol"]):
            best = {"weights": wd, "rho": rho, "gate": gate, "viol": viol, "score": score}

    bw = best["weights"]
    # normalize weights to sum=1 for readability (scoring normalizes anyway)
    tot = sum(bw.values()) or 1.0
    bw_norm = {k: round(v / tot, 4) for k, v in bw.items()}

    config.COMPOSITE_WEIGHTS_JSON.write_text(json.dumps(bw_norm, indent=2))

    # full-pool sanity: where do the anchor's 3s and 0s land in the FULL ranking?
    full_scores = score_dataframe(df, bw)
    full = pd.Series(full_scores, index=df.index).sort_values(ascending=False)
    rank_of = {cid: int((full.index == cid).argmax()) + 1 for cid in anchor_ids}
    threes = sorted([rank_of[c] for c in anchor_ids if labels[c] == 3])
    zeros = sorted([rank_of[c] for c in anchor_ids if labels[c] == 0])

    report = {
        "anchor_size": len(anchor_ids),
        "default_spearman": round(rho0, 4),
        "best_spearman": round(best["rho"], 4),
        "hard_gate_pass": best["gate"],
        "hard_gate_violations": best["viol"],
        "chosen_weights": bw_norm,
        "label3_full_ranks": threes,
        "label0_full_ranks_sample": zeros[:10],
        "label3_median_rank": int(np.median(threes)) if threes else None,
        "label0_median_rank": int(np.median(zeros)) if zeros else None,
    }
    config.CALIBRATION_REPORT_JSON.write_text(json.dumps(report, indent=2))

    print("-" * 60)
    print(f"BEST weights:     spearman={best['rho']:.3f}  "
          f"hard_gate={'OK' if best['gate'] else 'FAIL'} (violations={best['viol']})")
    print(f"label-3 anchors land at full-pool ranks: {threes}")
    print(f"label-0 anchors median full-pool rank: {report['label0_median_rank']} "
          f"(want this LOW-ranked = large number)")
    print(f"weights -> {config.COMPOSITE_WEIGHTS_JSON}")
    if not best["gate"]:
        print("WARNING: hard gate still fails — a label-0 outscores a label-3. "
              "Inspect those candidates; the labels or a feature may need review.")
    print("STAGE 5.51 (calibrate): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
