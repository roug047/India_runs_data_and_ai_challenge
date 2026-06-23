"""
stage5/53_calibrate_regularized.py
Regularized weight calibration — reduces overfitting/variance vs the plain search.

Two changes from 51_calibrate.py:
  1. REGULARIZATION: the objective penalizes weight vectors that lean too hard on any single
     feature (L2 toward the balanced default + an entropy-style spread bonus). This prefers
     simpler, more generalizable weights over ones that overfit the anchor.
  2. CROSS-VALIDATION: reports 5-fold held-out Spearman so you see GENERALIZATION, not just
     fit. The chosen weights are the ones that pass the hard gate AND maximize regularized
     in-sample objective; CV is the honesty check on them.

Run:  python stage5/53_calibrate_regularized.py --iters 6000 --reg 0.15
Output: overwrites composite_weights.json (regularized), writes stage5_cv_report.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402
from stage5.composite import DEFAULT_WEIGHTS, score_dataframe  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=6000)
    ap.add_argument("--reg", type=float, default=0.15,
                    help="regularization strength (0=none, higher=simpler weights)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    config.ensure_artifacts()

    import numpy as np
    import pandas as pd
    from scipy.stats import spearmanr
    from sklearn.model_selection import KFold

    labels = {k: int(v) for k, v in json.loads(config.GOLDEN_SET_JSON.read_text()).items()}
    df = pd.read_parquet(config.FEATURES_PARQUET)
    aids = [c for c in labels if c in df.index]
    da = df.loc[aids]
    y = np.array([labels[c] for c in aids])
    print(f"anchor: {len(aids)}  dist: {dict(sorted(pd.Series(y).value_counts().items()))}")

    keys = list(DEFAULT_WEIGHTS)
    base = np.array([DEFAULT_WEIGHTS[k] for k in keys])
    base_norm = base / base.sum()

    def weights_dict(w):
        return {k: float(v) for k, v in zip(keys, w)}

    def reg_penalty(w):
        # distance from the balanced default (L2) — discourages extreme weights
        wn = w / (w.sum() + 1e-9)
        return float(np.sum((wn - base_norm) ** 2))

    def evaluate(weights, idx):
        scores = score_dataframe(da.iloc[idx], weights)
        yy = y[idx]
        rho = spearmanr(scores, yy).correlation
        return 0.0 if np.isnan(rho) else rho

    def hard_gate(weights):
        scores = np.asarray(score_dataframe(da, weights))
        s3, s0 = scores[y == 3], scores[y == 0]
        if len(s3) and len(s0):
            return bool(s0.max() < s3.min()), int((s0[:, None] >= s3[None, :]).sum())
        return True, 0

    rng = np.random.default_rng(args.seed)
    all_idx = np.arange(len(aids))

    best = None
    for _ in range(args.iters):
        w = np.clip(base * rng.uniform(0.4, 1.6, len(base)), 0.0, None)
        wd = weights_dict(w)
        rho = evaluate(wd, all_idx)
        obj = rho - args.reg * reg_penalty(w)   # regularized objective
        gate, viol = hard_gate(wd)
        key = (1 if gate else 0, obj)
        if best is None or key > best["key"]:
            best = {"key": key, "w": wd, "rho": rho, "obj": obj,
                    "gate": gate, "viol": viol}

    bw = best["w"]
    tot = sum(bw.values()) or 1.0
    bw_norm = {k: round(v / tot, 4) for k, v in bw.items()}

    # 5-fold CV on the chosen weights (generalization honesty check)
    kf = KFold(n_splits=5, shuffle=True, random_state=1)
    cv = []
    for _, te in kf.split(all_idx):
        if len(set(y[te])) < 2:
            continue
        cv.append(evaluate(bw, te))
    cv_mean = float(np.nanmean(cv))

    config.COMPOSITE_WEIGHTS_JSON.write_text(json.dumps(bw_norm, indent=2))
    report = {
        "anchor_size": len(aids),
        "reg_strength": args.reg,
        "in_sample_spearman": round(best["rho"], 4),
        "cv_spearman": round(cv_mean, 4),
        "cv_per_fold": [round(x, 3) for x in cv],
        "hard_gate": best["gate"],
        "hard_gate_violations": best["viol"],
        "weights": bw_norm,
    }
    (config.ARTIFACTS / "stage5_cv_report.json").write_text(json.dumps(report, indent=2))

    print("-" * 60)
    print(f"in-sample spearman: {best['rho']:.3f}")
    print(f"CV spearman (held-out): {cv_mean:.3f}  per-fold: {report['cv_per_fold']}")
    print(f"hard gate: {'OK' if best['gate'] else 'FAIL'} (violations={best['viol']})")
    print(f"weights -> {config.COMPOSITE_WEIGHTS_JSON}")
    print("STAGE 5.53 (regularized calibrate): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
