# Stage 5 — Composite Scoring + Anchor Calibration

The payoff stage. Combines every Stage 2-4 signal into one final score, tunes the weights
against your golden set, and produces **Submission #1 — your leaderboard safety net.**

## The scoring model

```
final_score = relevance * disqualifier_penalty * honeypot_score
              * availability_multiplier * notice_factor

relevance = weighted blend of:
  weighted_hard_req_coverage, production_evidence_score, hybrid_score,
  weighted_soft_req_coverage, yoe_fit, location_score, shipped_relevant_system
```

The **multipliers sit outside the blend** so a single fatal flag collapses the score no
matter how strong the positives look. This is what ejects the honeypot that fooled retrieval
(CAND_0093547: high hybrid 0.89 × honeypot 0.12 → crushed, out of the top 100).

## Files

| File | Does |
|------|------|
| `composite.py` | The scoring function (used by both calibrator and rank.py — single source of truth) |
| `51_calibrate.py` | Tunes weights against the golden set: hard gate + Spearman maximization |
| `52_submission_one.py` | Builds the valid 100-row ranked CSV with fact-grounded reasoning |

## Run

```bash
python stage5/51_calibrate.py        # tune weights on your 60-candidate anchor
python stage5/52_submission_one.py   # produce submission_one.csv
```

## The calibration (why the golden set mattered)

`51_calibrate.py` does two things against your hand labels:

1. **Hard gate:** no candidate you labeled 0 may outscore any candidate you labeled 3. If
   this fails, the weights are wrong — the search keeps going until it passes.
2. **Spearman maximization:** bounded random search around sensible default weights, picking
   the set with the best rank-correlation to your labels that also passes the gate.

The search is deliberately modest (±60% around defaults) because the anchor is only ~60
points — we want weights that generalize, not ones overfit to 60 labels.

The report shows where your label-3 anchors land in the FULL 100K ranking (should be near the
top) and where your label-0 anchors land (should be deep down). That's the real-world check
that the composite ranks the way you judged.

## Submission #1 format (submission_spec compliant)

`candidate_id,rank,score,reasoning` — exactly 100 rows, ranks 1-100 unique, scores
monotonically non-increasing in (0,1], all ids exist in the pool. Scores are rank-based
(guaranteed unique + decreasing). Reasoning cites only literal profile facts (title, company,
YOE, a real achievement sentence, recruiter response rate) — never an invented skill, because
Stage-4 manual review penalizes reasoning mentioning skills not in the profile.

## Why this is a "safety net"

Stage 6 builds a heavier LightGBM ranker. If that overfits or underperforms on the anchor,
Submission #1 (a transparent, fully-explainable composite tuned to your human labels) is a
solid fallback you can submit with confidence. You always have a defensible submission.

## Consumed downstream

- `composite_weights.json` → Stage 7 rank.py (same scoring at inference)
- `submission_one.csv` → your first leaderboard submission
