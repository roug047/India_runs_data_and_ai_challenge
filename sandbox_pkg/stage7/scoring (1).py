"""
stage7/scoring.py
Final scoring logic, shared by 70_generate_top40.py and rank.py so they are IDENTICAL.

Engine: blended LightGBM ranker (Stage 6) is primary; composite (Stage 5) breaks ties.
Both are combined into one orderable score, then the hard multipliers (honeypot,
disqualifier) gate the result so no impossible/disqualified candidate survives to the top.

final = ranker_blend_norm  +  1e-4 * composite_norm        (composite as fine tie-break)
        then * honeypot_score * disqualifier_penalty       (hard gates)

The tie-break weight (1e-4) is tiny: composite only matters when the ranker is ~exactly
tied, which is common in this dataset because career texts are templated (many identical
profiles). Without a tie-break, ties resolve arbitrarily; the composite gives a principled order.
"""
from __future__ import annotations
import json


def _minmax(a):
    import numpy as np
    a = np.asarray(a, dtype="float64")
    r = a.max() - a.min()
    return (a - a.min()) / r if r > 1e-12 else a * 0.0


def compute_final_scores(df, artifacts_dir):
    """
    Return a pandas Series of final scores indexed like df.
    Honors engine_choice.json (composite / ranker / rank_average). Falls back to
    ranker-primary-composite-tiebreak if no choice file is present.
    Requires: lgb_features.json, ranker_rule.txt, ranker_llm.txt, blend.json,
              composite_weights.json.
    """
    import numpy as np
    import pandas as pd
    import lightgbm as lgb
    from pathlib import Path
    from stage5.composite import score_dataframe, DEFAULT_WEIGHTS

    adir = Path(artifacts_dir)
    feats = json.loads((adir / "lgb_features.json").read_text())

    # --- train/inference skew guard (v6.1) ---
    missing = [f for f in feats if f not in df.columns]
    if missing:
        raise RuntimeError(f"rank.py: {len(missing)} ranker features missing from table: "
                           f"{missing[:8]} — feature pipeline mismatch.")
    X = df[feats].fillna(0.0).values

    blend = json.loads((adir / "blend.json").read_text())
    alpha = float(blend.get("alpha_rule", 1.0))

    m_rule = lgb.Booster(model_file=str(adir / "ranker_rule.txt"))
    p_rule = _minmax(m_rule.predict(X))
    if blend.get("has_llm") and (adir / "ranker_llm.txt").exists():
        m_llm = lgb.Booster(model_file=str(adir / "ranker_llm.txt"))
        p_llm = _minmax(m_llm.predict(X))
        ranker = alpha * p_rule + (1 - alpha) * p_llm
    else:
        ranker = p_rule
    ranker = _minmax(ranker)

    weights = json.loads((adir / "composite_weights.json").read_text()) \
        if (adir / "composite_weights.json").exists() else DEFAULT_WEIGHTS
    composite = _minmax(score_dataframe(df, weights))

    # which engine?
    choice = "ranker_primary"
    cpath = adir / "engine_choice.json"
    if cpath.exists():
        choice = json.loads(cpath.read_text()).get("engine", "ranker_primary")

    if choice == "composite":
        base = composite + 1e-4 * ranker
    elif choice == "rank_average":
        cr = pd.Series(composite, index=df.index).rank(ascending=True)
        rr = pd.Series(ranker, index=df.index).rank(ascending=True)
        base = _minmax(((cr + rr) / 2.0).values)
    elif choice == "ranker":
        base = ranker + 1e-4 * composite
    else:  # ranker_primary default
        base = ranker + 1e-4 * composite

    # hard gates: honeypot + disqualifier multipliers
    hp = df["honeypot_score"].fillna(1.0).astype("float64").values \
        if "honeypot_score" in df.columns else np.ones(len(df))
    dq = df["disqualifier_penalty"].fillna(1.0).astype("float64").values \
        if "disqualifier_penalty" in df.columns else np.ones(len(df))

    final = np.asarray(base) * hp * dq
    return pd.Series(final, index=df.index)
