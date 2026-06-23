# Stage 5 — Integration Instructions

The payoff stage: composite scoring, golden-set calibration, and **Submission #1**.

## 1. Add files to `stage5/`

- `stage5/__init__.py`
- `stage5/composite.py`
- `stage5/51_calibrate.py`
- `stage5/52_submission_one.py`
- `stage5/README.md`

## 2. Add to `common/config.py` (at end)

```python
# Stage 5 outputs
COMPOSITE_WEIGHTS_JSON = ARTIFACTS / "composite_weights.json"
CALIBRATION_REPORT_JSON = ARTIFACTS / "stage5_calibration_report.json"
SUBMISSION_ONE_CSV = ARTIFACTS / "submission_one.csv"
```

## 3. Run calibration

```bash
python stage5/51_calibrate.py
```

Watch the output:
- **`hard_gate=OK`** — no label-0 outscores a label-3. This is the must-pass.
- **`best_spearman`** — rank-correlation to your labels. Higher is better; anything above
  ~0.5 on a 60-point anchor is solid, above 0.7 is strong.
- **`label-3 anchors land at full-pool ranks: [...]`** — your hand-picked strong fits should
  land near the top of the full 100K ranking. If a candidate you labeled 3 is sitting at rank
  40,000, something's off — tell me.

### If the hard gate FAILS

It means a candidate you labeled 0 scores higher than one you labeled 3. Two possible causes:
1. A label is wrong (you may have mislabeled one) — the report names the ranks; check those candidates.
2. A feature is misbehaving for that candidate.

Send me `artifacts/stage5_calibration_report.json` and I'll help diagnose. Don't force-submit
with a failing gate.

## 4. Produce Submission #1

```bash
python stage5/52_submission_one.py
```

This writes `artifacts/submission_one.csv` and prints:
- honeypots in top 100 (must be 0 — if not, tell me)
- hard-disqualified in top 100 (should be 0)
- validation: 100 rows, unique ranks, monotone scores

## 5. Inspect the submission

```bash
python -c "import pandas as pd; s=pd.read_csv('artifacts/submission_one.csv'); print(s.head(10).to_string()); print('...'); print('rows:', len(s), '| score range:', s.score.min(), '-', s.score.max())"
```

Read the top 10 reasoning strings. They should cite real facts (title, company, years, an
achievement). If any reads oddly or mentions something not in the profile, flag it.

## 6. Commit

```bash
git add stage5/ common/config.py artifacts/composite_weights.json artifacts/stage5_calibration_report.json artifacts/submission_one.csv
git commit -m "Stage 5: composite scoring, anchor calibration, Submission #1"
```

## What to send me

Two things:
1. `artifacts/stage5_calibration_report.json` — I want to confirm the hard gate passed and
   your label-3 anchors rank near the top.
2. The top-10 of `submission_one.csv` — to eyeball that the people at the top are real fits
   and the reasoning is fact-grounded.

This is the first submission you can actually put on the leaderboard. Once it looks good,
Stage 6 builds the LightGBM ranker (your GPU labels the training data with a local model, no
API) and blends it with this composite — tuned, again, on your golden set. But Submission #1
is your safety net: a transparent, defensible ranking you can submit today.
