# Stage 4 — Integration Instructions

Honeypot detection. Pure CPU, fast. Precision-first.

## 1. Add files to `stage4/`

- `stage4/__init__.py`
- `stage4/honeypot_signals.py`
- `stage4/40_run_honeypot.py`
- `stage4/README.md`

## 2. Add to `common/config.py` (at end)

```python
# Stage 4 outputs
HONEYPOT_REPORT_JSON = ARTIFACTS / "stage4_honeypot_report.json"
```

## 3. Run

```bash
python stage4/40_run_honeypot.py --sample    # confirms recall + precision on sample
python stage4/40_run_honeypot.py             # full 100K
```

The full run prints a synthetic recall test (5 impossible profiles, all should say PASS),
then processes the pool and writes `honeypot_score` + `is_likely_honeypot` into the feature
table.

## 4. The number that matters

After the full run, look at `flag_rate_pct` in `artifacts/stage4_honeypot_report.json`.

- **Expected: well under 1%** (there are ~80 honeypots = 0.08% of the pool).
- If it's **0%**: possibly too strict — but on the sample 0% was correct (honeypots are rare).
  Send me the report; if the full pool flags 0, we may loosen slightly so the planted ~80 are
  caught.
- If it's **above ~3%**: too loose, catching real candidates. The script warns you. Send me
  the report and we tighten.

The sweet spot is flagging roughly a few dozen to ~100 candidates out of 100K — close to the
~80 the organizers planted.

## 5. Verify

```bash
python -c "import pandas as pd; df=pd.read_parquet('artifacts/features_100k.parquet'); print('honeypot cols:', [c for c in df.columns if 'honeypot' in c]); print('flagged:', int(df['is_likely_honeypot'].sum()), 'of', len(df))"
```

## 6. Commit

```bash
git add stage4/ common/config.py artifacts/stage4_honeypot_report.json
git commit -m "Stage 4: honeypot audit (7 impossibility signals, precision-first, recall-tested)"
```

## What to send me after the run

`artifacts/stage4_honeypot_report.json` — specifically the `flag_rate_pct` and
`flagged_honeypots` count. This is the one stage where the full-pool number genuinely matters
for calibration: the sample is too small to contain planted honeypots, so the 100K run is the
real test of whether we're catching ~80 without over-firing. Once I see it lands in the
right range, Stage 5 is the composite scoring + anchor calibration — where your golden set
finally does its job, and you get Submission #1 (the safety net).
