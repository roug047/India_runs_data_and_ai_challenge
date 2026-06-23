"""
stage6/62_train_blend.py
Train two LightGBM rankers (rule labels, LLM labels), pick blend alpha on the golden set.

If LLM labels are absent (no local model), trains rule-only and sets alpha=1.0 — the system
degrades gracefully to a single defensible ranker.

Blend: final_lgb = alpha * rank_rule + (1-alpha) * rank_llm, with alpha chosen to MAXIMIZE
NDCG@10 on the human anchor. So if the LLM labels are biased on some archetype, alpha shifts
toward the rule model automatically — the blend can only help.

The trained rankers' predictions become a feature for Stage 7. We also save lgb_features.json
(the exact feature columns + order) so rank.py uses identical inputs (no train/infer skew).

Run:  python stage6/62_train_blend.py
Output: ranker_rule.txt, ranker_llm.txt (if LLM labels), blend.json, lgb_features.json,
        stage6_report.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402

# Feature columns the rankers train on. Exclude raw multipliers we apply separately and
# exclude leakage-prone or non-numeric columns. Stage 7 reads this list back.
EXCLUDE = {"candidate_id", "final_score", "disqualifier_hit", "is_likely_honeypot"}


def _minmax(a):
    import numpy as np
    a = np.asarray(a, float)
    r = a.max() - a.min()
    return (a - a.min()) / r if r > 1e-12 else np.zeros_like(a)


def main() -> int:
    ap = argparse.ArgumentParser()
    args = ap.parse_args()
    config.ensure_artifacts()

    try:
        import numpy as np
        import pandas as pd
        import lightgbm as lgb
        from sklearn.metrics import ndcg_score
        from scipy.stats import spearmanr
    except ImportError:
        print("FATAL: pip install lightgbm scikit-learn pandas numpy pyarrow")
        return 1

    df = pd.read_parquet(config.FEATURES_PARQUET)
    feat_cols = [c for c in df.columns
                 if c not in EXCLUDE and df[c].dtype.kind in "biufc"]
    config.LGB_FEATURES_JSON.write_text(json.dumps(feat_cols, indent=2))
    print(f"{len(feat_cols)} ranker features")

    rule_labels = {k: int(v) for k, v in
                   json.loads(config.TRAIN_LABELS_RULE_JSON.read_text()).items()}
    has_llm = config.TRAIN_LABELS_LLM_JSON.exists()
    llm_labels = ({k: int(v) for k, v in
                   json.loads(config.TRAIN_LABELS_LLM_JSON.read_text()).items()}
                  if has_llm else {})

    def train(labels, name):
        ids = [c for c in labels if c in df.index]
        X = df.loc[ids, feat_cols].fillna(0.0).values
        y = np.array([labels[c] for c in ids])
        dset = lgb.Dataset(X, label=y, group=[len(X)])
        params = dict(objective="lambdarank", metric="ndcg",
                      num_leaves=31, learning_rate=0.05, min_data_in_leaf=20,
                      n_estimators=300, label_gain=[0, 1, 3, 7], verbose=-1)
        model = lgb.train(params, dset)
        out = config.RANKER_RULE_TXT if name == "rule" else config.RANKER_LLM_TXT
        model.save_model(str(out))
        print(f"  trained ranker_{name} on {len(ids)} labels -> {out.name}")
        return model

    m_rule = train(rule_labels, "rule")
    m_llm = train(llm_labels, "llm") if has_llm and len(llm_labels) >= 50 else None

    # --- choose alpha on the golden set ---
    golden = {k: int(v) for k, v in json.loads(config.GOLDEN_SET_JSON.read_text()).items()}
    aids = [c for c in golden if c in df.index]
    Xa = df.loc[aids, feat_cols].fillna(0.0).values
    y_true = np.array([[golden[c] for c in aids]])

    p_rule = _minmax(m_rule.predict(Xa))
    if m_llm is not None:
         p_llm = _minmax(m_llm.predict(Xa))
         y_flat_anchor = np.array([golden[c] for c in aids])
         best_a, best_obj, ndcg_at_alpha = 1.0, -1.0, 0.0
         for a in np.linspace(0, 1, 21):
             blended = a * p_rule + (1 - a) * p_llm
             n = ndcg_score(y_true, np.array([blended]), k=min(10, len(aids)))
             rho = spearmanr(blended, y_flat_anchor).correlation
             rho = 0.0 if np.isnan(rho) else rho
             # combined objective: NDCG@10 is flat/tie-prone on a small anchor, so we add
             # Spearman (full-anchor rank agreement) to break ties toward robust blends.
             obj = 0.5 * n + 0.5 * rho
             if obj > best_obj:
                 best_obj, best_a, ndcg_at_alpha = obj, float(a), n
         alpha = best_a
    else:
        alpha = 1.0
        ndcg_at_alpha = ndcg_score(y_true, np.array([p_rule]), k=min(10, len(aids)))
        print("  (LLM labels absent — rule-only, alpha=1.0)")

    config.BLEND_JSON.write_text(json.dumps(
        {"alpha_rule": alpha, "has_llm": m_llm is not None}, indent=2))

    # compare blended ranker vs composite on the anchor (is the ranker actually better?)
    y_flat = np.array([golden[c] for c in aids])
    blended_full = (alpha * p_rule + (1 - alpha) * _minmax(m_llm.predict(Xa))) \
        if m_llm is not None else p_rule
    rho_ranker = spearmanr(blended_full, y_flat).correlation

    report = {
        "n_features": len(feat_cols),
        "rule_label_dist": dict(sorted(__import__("collections").Counter(
            rule_labels.values()).items())),
        "llm_labels": len(llm_labels),
        "alpha_rule": alpha,
        "anchor_ndcg10": round(float(ndcg_at_alpha), 4),
        "anchor_spearman_ranker": round(float(rho_ranker), 4),
    }
    config.STAGE6_REPORT_JSON.write_text(json.dumps(report, indent=2))

    print("-" * 60)
    print(f"alpha (rule weight): {alpha:.2f}  ({'blended' if m_llm else 'rule-only'})")
    print(f"anchor NDCG@10: {report['anchor_ndcg10']}  "
          f"ranker spearman: {report['anchor_spearman_ranker']}")
    print(f"blend -> {config.BLEND_JSON}")
    print("STAGE 6.62 (train+blend): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
