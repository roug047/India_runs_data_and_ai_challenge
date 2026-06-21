# Stage 2 — Integration Instructions

Pure pandas, no GPU. Adds the master feature table. Matches your layout exactly.

## 1. Add files to `stage2/`

Copy into your repo's `stage2/` folder:
- `stage2/__init__.py`  (makes it an importable package — REQUIRED)
- `stage2/features_core.py`
- `stage2/disqualifiers.py`
- `stage2/20_build_features.py`
- `stage2/README.md`

## 2. Add three lines to `common/config.py`

At the very end of the file:

```python
# Stage 2 outputs
FEATURES_PARQUET = ARTIFACTS / "features_100k.parquet"
FEATURE_LIST_JSON = ARTIFACTS / "feature_list.json"
FEATURE_REPORT_JSON = ARTIFACTS / "stage2_feature_report.json"
```

## 3. Run

```bash
# dry run first (50 rows, ~1 second) — sanity check before the full pool
python stage2/20_build_features.py --sample

# full 100K — pure CPU, a few minutes
python stage2/20_build_features.py
```

Expected on the full run: ~52 columns, a disqualifier hit-rate report, and a breakdown of
which disqualifiers fired how often. Watch that no single disqualifier fires on a huge
fraction of the pool (that would mean a rescue condition is too weak).

## 4. Sanity-check the trap backfire

```bash
python -c "import pandas as pd; df=pd.read_parquet('artifacts/features_100k.parquet'); print('cols:', len(df.columns)); print('DQ rate:', round(df['disqualifier_hit'].mean(),3)); print('mean hard-req coverage:', round(df['weighted_hard_req_coverage'].mean(),3))"
```

## 5. Commit

```bash
git add stage2/ common/config.py artifacts/feature_list.json artifacts/stage2_feature_report.json
git commit -m "Stage 2: candidate feature engineering (career-weighted coverage, disqualifiers, behavioral)"
```

(`features_100k.parquet` is gitignored — large and regenerable. That's intended.)

## What to look at in the report

`artifacts/stage2_feature_report.json` gives you the disqualifier breakdown across the full
100K. On the full pool you should see `pure_research_no_prod`, `langchain_only_under_12mo`,
and `closed_source_no_validation` actually firing (they were 0 on the tiny sample because
those archetypes were rare in 50 rows). If any of them is still 0 across 100K, tell me — a
threshold may need tuning for the real distribution.

## Important note on the disqualifier hit-rate

If the overall `disqualifier_hit` rate comes back very high (say >40%), that's worth a look —
it may mean a rescue condition is too strict and is catching legitimate candidates. The
sample showed 0.32, which is reasonable for a trap-heavy dataset, but the full pool is the
real test. Send me the report JSON after the full run and I'll confirm the thresholds are
calibrated before we build Stage 3.

When the full run passes and you've committed, tell me — Stage 3 is hybrid retrieval (the
GPU candidate encode + BM25 + writing `hybrid_score` back into this table).
