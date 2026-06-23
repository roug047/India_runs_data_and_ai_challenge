# Stage 7 — Final Integration (the finale)

Complete, updated for the rank_average engine. Produces `rank.py` (the reproduced step),
the top-30 audit, diversified reasoning, and Submission #2.

## 1. Add these to `stage7/`

- `stage7/__init__.py`
- `stage7/scoring.py`        (reads engine_choice.json → uses rank_average)
- `stage7/reasoning.py`      (diversified per-candidate reasoning)
- `stage7/70_generate_top40.py`
- `stage7/71_make_audit_template.py`
- `stage7/72_rank.py`        (deploy as rank.py at repo root)
- `stage7/validate_submission.py`

## 2. Add to `common/config.py` (at end) — SKIP if already present

```python
# Stage 7 outputs
AUDIT_LOG_JSON = ARTIFACTS / "audit_log.json"
REASONING_CACHE_JSON = ARTIFACTS / "reasoning_cache.json"
TOP40_REVIEW_CSV = ARTIFACTS / "top40_review.csv"
SUBMISSION_TWO_CSV = ARTIFACTS / "submission_two.csv"
```

## 3. Generate the top 40 for your audit

```bash
python stage7/70_generate_top40.py
```

Writes `artifacts/top40_review.csv` using the **rank_average** engine (CV 0.851).

## 4. THE TOP-30 AUDIT (your highest-leverage hour)

Open `top40_review.csv`. Read the top 30 against the JD's ideal-candidate description.
55% of your score is NDCG@10 — fixing even one wrong candidate in your top 10 matters more
than any model tuning. Watch for:
- keyword-stuffers (impressive skills, weak/ops career) that slipped through
- honeypots (summary YOE doesn't match career)
- wrong-domain candidates
- anyone whose `honeypot_score` or `disqualifier_penalty` is below 1.0

For anyone who doesn't belong:

```bash
python stage7/71_make_audit_template.py   # creates empty audit_log.json
```

Edit `artifacts/audit_log.json`:
```json
{
  "CAND_0012345": {"action": "remove", "reason": "keyword-stuffer: ops career, AI skills only"},
  "CAND_0067890": {"action": "demote", "to_rank": 35, "reason": "6mo inactive, low response"}
}
```
If the top 30 all look good, leave it `{}` — that means the engine nailed it.

## 5. Produce Submission #2

```bash
python stage7/72_rank.py --out artifacts/submission_two.csv
python stage7/validate_submission.py artifacts/submission_two.csv
```

Must print `VALID`. Check the reasoning is diversified:
```bash
python -c "import pandas as pd; s=pd.read_csv('artifacts/submission_two.csv'); print('distinct reasoning:', s.reasoning.nunique(), '/ 100'); print(s.head(12).to_string())"
```
`distinct reasoning` should be ~100 (not repeated like Submission #1 was).

## 6. Deploy rank.py for reproduction

```bash
copy stage7\72_rank.py rank.py
python rank.py --candidates candidates.jsonl --out submission.csv
python stage7/validate_submission.py submission.csv
```

rank.py is CPU-only, no network, self-validating, has the train/inference skew guard, and
applies the audit log deterministically. It reads precomputed artifacts (features parquet,
ranker models, blend, weights, engine_choice, audit_log) — all produced by Stages 1-6.

## 7. Commit

```bash
git add stage7/ rank.py common/config.py artifacts/audit_log.json artifacts/submission_two.csv
git commit -m "Stage 7: rank.py (rank_average engine), top-30 audit, diversified reasoning, Submission #2"
```

## What the reasoning looks like now (the diversified fix)

Each candidate's reasoning is composed from THEIR specific facts — company, the hard
requirement they best cover, a real listed skill, location, notice, response rate — so two
candidates sharing a templated career sentence still get different reasoning. Only literal
profile facts are cited; never an invented skill.

## What to send me

1. Your top 30 from `top40_review.csv` (or the whole CSV) — we'll review them together and
   I'll help you spot anything that doesn't belong before you finalize the audit.
2. After Submission #2: the `72_rank.py` elapsed time and the distinct-reasoning count.

This is the finale. Once Submission #2 validates and you've audited the top 30, you have a
complete, defensible, hackathon-ready system — rank_average engine at CV 0.851, every trap
(honeypot, stuffer, availability) handled, fully reproducible on CPU.
