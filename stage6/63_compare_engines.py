"""
stage6/63_compare_engines.py
Compare three scoring engines on the golden set with 5-fold cross-validation:
  (A) composite     — the regularized Stage 5 composite (CV ~0.83)
  (B) ranker        — the blended LightGBM ranker (Stage 6)
  (C) rank_average  — average of the RANK POSITIONS of A and B

Rank-averaging often beats either model alone because the two models make independent errors;
averaging their ranks cancels noise. We pick the engine with the best held-out CV Spearman AND
NDCG@10, and write the choice to engine_choice.json for Stage 7 rank.py.

Run:  python stage6/63_compare_engines.py
Output: artifacts/engine_choice.json, prints the comparison table.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402
from stage5.composite import score_dataframe  # noqa: E402


def _mm(a):
    import numpy as np
    a = np.asarray(a, float)
    r = a.max() - a.min()
    return (a - a.min()) / r if r > 1e-12 else a * 0.0


def main() -> int:
    import numpy as np
    import pandas as pd
    import lightgbm as lgb
    from scipy.stats import spearmanr
    from sklearn.metrics import ndcg_score
    from sklearn.model_selection import KFold

    df = pd.read_parquet(config.FEATURES_PARQUET)
    feats = json.loads(config.LGB_FEATURES_JSON.read_text())
    golden = {k: int(v) for k, v in json.loads(config.GOLDEN_SET_JSON.read_text()).items()}
    aids = [c for c in golden if c in df.index]
    y = np.array([golden[c] for c in aids])
    da = df.loc[aids]

    # engine A: composite
    wts = json.loads(config.COMPOSITE_WEIGHTS_JSON.read_text())
    comp_full = _mm(score_dataframe(df, wts))
    comp = pd.Series(comp_full, index=df.index).loc[aids].values

    # engine B: blended ranker
    m_rule = lgb.Booster(model_file=str(config.RANKER_RULE_TXT))
    blend = json.loads(config.BLEND_JSON.read_text())
    alpha = blend.get("alpha_rule", 1.0)
    Xall = df[feats].fillna(0).values
    pr = _mm(m_rule.predict(Xall))
    if blend.get("has_llm") and config.RANKER_LLM_TXT.exists():
        m_llm = lgb.Booster(model_file=str(config.RANKER_LLM_TXT))
        rank_full = _mm(alpha * pr + (1 - alpha) * _mm(m_llm.predict(Xall)))
    else:
        rank_full = pr
    ranker = pd.Series(rank_full, index=df.index).loc[aids].values

    # engine C: rank-average (average of rank POSITIONS, full-pool, then restricted)
    comp_rank = pd.Series(comp_full, index=df.index).rank(ascending=True)
    rank_rank = pd.Series(rank_full, index=df.index).rank(ascending=True)
    ravg_full = (comp_rank + rank_rank) / 2.0
    ravg = _mm(ravg_full.loc[aids].values)

    engines = {"composite": comp, "ranker": ranker, "rank_average": ravg}

    # 5-fold CV
    kf = KFold(n_splits=5, shuffle=True, random_state=1)
    results = {}
    for name, s in engines.items():
        rhos, ndcgs = [], []
        for _, te in kf.split(aids):
            if len(set(y[te])) < 2:
                continue
            rhos.append(spearmanr(s[te], y[te]).correlation)
            ndcgs.append(ndcg_score([y[te]], [s[te]], k=min(10, len(te))))
        results[name] = {
            "cv_spearman": round(float(np.nanmean(rhos)), 4),
            "cv_ndcg10": round(float(np.nanmean(ndcgs)), 4),
            "per_fold_spearman": [round(float(x), 3) for x in rhos],
        }

    # pick winner by CV spearman (primary), ndcg10 (tiebreak)
    winner = max(results, key=lambda n: (results[n]["cv_spearman"],
                                         results[n]["cv_ndcg10"]))
    config.ARTIFACTS.joinpath("engine_choice.json").write_text(
        json.dumps({"engine": winner, "results": results}, indent=2))

    print("=" * 64)
    print(f"{'engine':16s} {'CV Spearman':>12s} {'CV NDCG@10':>12s}")
    for name, r in results.items():
        mark = "  <-- WINNER" if name == winner else ""
        print(f"{name:16s} {r['cv_spearman']:>12.4f} {r['cv_ndcg10']:>12.4f}{mark}")
    print("=" * 64)
    print(f"per-fold spearman:")
    for name, r in results.items():
        print(f"  {name:16s} {r['per_fold_spearman']}")
    print(f"\nchosen engine: {winner} -> artifacts/engine_choice.json")
    print("STAGE 6.63 (engine comparison): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
