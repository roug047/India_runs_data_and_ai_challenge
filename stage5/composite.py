"""
stage5/composite.py
The composite scoring engine. Combines all Stage 2-4 signals into one final score.

final_score = relevance * disqualifier_penalty * honeypot_score * availability_multiplier

where `relevance` is a weighted blend of the positive signals. The weights are tuned in
51_calibrate.py against the golden set; this module just defines the scoring function so
both the calibrator and rank.py use the EXACT same logic.

The multipliers (disqualifier, honeypot, availability) are applied OUTSIDE the weighted
blend so a single fatal flag (honeypot, hard disqualifier) collapses the score regardless
of how strong the positive signals look. This is what ejects the honeypot that fooled
retrieval (e.g. CAND_0093547: high hybrid, honeypot_score 0.12 -> crushed).
"""
from __future__ import annotations

# Default weights for the positive-relevance blend. Sum need not be 1 (normalized in use).
# These are STARTING points; 51_calibrate.py searches around them against the anchor.
DEFAULT_WEIGHTS = {
    "weighted_hard_req_coverage": 0.30,   # JD hard requirements (career-weighted)
    "production_evidence_score":  0.22,   # JD #1 priority: shipped to real users
    "hybrid_score":               0.18,   # semantic + lexical retrieval fit
    "weighted_soft_req_coverage": 0.10,   # nice-to-haves
    "yoe_fit":                    0.08,    # 5-9 band
    "location_score":             0.07,    # India / preferred / relocate
    "shipped_relevant_system":    0.05,    # built retrieval/ranking specifically
}


def compute_relevance(row: dict, weights: dict) -> float:
    """Weighted blend of positive signals, normalized by total weight."""
    total_w = sum(weights.values()) or 1.0
    s = 0.0
    for feat, w in weights.items():
        v = row.get(feat, 0.0)
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = 0.0
        s += w * v
    return s / total_w


def compute_final_score(row: dict, weights: dict) -> float:
    """
    relevance * disqualifier_penalty * honeypot_score * availability_multiplier
    Each multiplier defaults to 1.0 if absent. notice_score folds a mild logistics nudge.
    """
    relevance = compute_relevance(row, weights)

    dq = float(row.get("disqualifier_penalty", 1.0) or 1.0)
    hp = float(row.get("honeypot_score", 1.0) or 1.0)
    avail = float(row.get("availability_multiplier", 1.0) or 1.0)
    notice = float(row.get("notice_score", 1.0) or 1.0)

    # notice applied gently (0.85-1.0 band) so it nudges but never dominates
    notice_factor = 0.85 + 0.15 * notice

    return relevance * dq * hp * avail * notice_factor


def score_dataframe(df, weights):
    """Vectorized scoring over a pandas DataFrame. Returns a Series of final scores."""
    import numpy as np
    total_w = sum(weights.values()) or 1.0
    relevance = np.zeros(len(df), dtype="float64")
    for feat, w in weights.items():
        if feat in df.columns:
            relevance += w * df[feat].fillna(0.0).astype("float64").values
    relevance /= total_w

    def col(name, default=1.0):
        return df[name].fillna(default).astype("float64").values if name in df.columns \
            else np.full(len(df), default)

    dq = col("disqualifier_penalty")
    hp = col("honeypot_score")
    avail = col("availability_multiplier")
    notice = col("notice_score")
    notice_factor = 0.85 + 0.15 * notice
    return relevance * dq * hp * avail * notice_factor
