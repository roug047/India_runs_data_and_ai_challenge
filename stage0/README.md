# Stage 0 — Pre-flight + Golden Set

**Architecture V6 · Day 1.** This stage produces the project's load-bearing artifact: the
hand-labeled **golden set** that every later stage validates against. It also derives the
**reference date** empirically (not hardcoded) and records a naive baseline for defensibility.

> GPU is fine here. Stage 0 is precompute. Only `rank.py` (Stage 7) is CPU-only / no-network / ≤5 min.

## Scripts (run in order)

| Script | What it does | Output |
|--------|--------------|--------|
| `00_env_check.py` | Verifies Python, core libs, and input files exist | console PASS/FAIL |
| `01_data_audit.py` | Integrity checks; **derives REFERENCE_DATE = max(last_active_date)**; distribution report; naive YOE≈7 baseline | `artifacts/reference_date.json`, `artifacts/stage0_data_report.json`, `artifacts/naive_baseline_top100.json` |
| `02_select_anchor.py` | Picks 60 information-rich candidates to label, using **raw-signal proxies only** (no tuned score → no circularity). Emits a human worksheet | `artifacts/anchor_candidates.json`, `artifacts/golden_set_worksheet.csv` |
| `03_build_golden_set.py` | Converts your filled worksheet into the frozen, validated golden set | `artifacts/golden_set.json` |

## Day-1 workflow

```bash
# 1. environment + data sanity
python stage0/00_env_check.py
python stage0/01_data_audit.py            # add --sample to dry-run on the 50-row file

# 2. choose the 60 to label
python stage0/02_select_anchor.py         # add --sample for a dry run

# 3. OPEN artifacts/golden_set_worksheet.csv
#    Read each profile. Fill the 'label' column with 0/1/2/3 using the rubric below.
#    (The worksheet pre-computes hints: yoe, hard_kw_hits, ai_skill_count, eng_title, github.)

# 4. freeze the anchor (validates size + label balance)
python stage0/03_build_golden_set.py
```

## Labeling rubric (read JD "how to read between the lines" first)

```
3 STRONG : 5–9yr, mostly product (not services); career text shows a SHIPPED
           retrieval/ranking/recsys/search system to real users; India or will
           relocate; notice ≤ 90d; reachable. Keywords NOT required if the story is there.
2 MODERATE: right trajectory, missing 1–2 hard reqs, OR strong skills + partial
           consulting, OR adjacent (data-eng / NLP) pivoting in.
1 WEAK   : some relevant skills but career mostly unrelated; too junior/senior; thin production.
0 NOT FIT: pure consulting career; CV/speech/robotics-only w/o NLP/IR; pure-research-no-prod;
           outside India + won't relocate; honeypot; non-tech title w/ stuffed AI skills.
```

The two sample candidates are textbook 0s: `CAND_0000001` (services-adjacent backend eng,
stuffed AI skills, assessment scores 38–53, GitHub 9.2, Canada + won't relocate) and
`CAND_0000002` (Operations Manager, 12.5yr, internally contradictory history).

## Why these choices (defense notes)

- **Reference date is derived, not guessed.** The sample already contained `2026-05-25`,
  past the old hardcoded `2026-06-06`. Every recency feature now keys off the true snapshot.
- **Anchor selection uses neutral proxies only** (keyword hits, YOE band, arithmetic
  impossibility, services ratio) — never a score we later tune. This keeps the golden set a
  true held-out validator (v6.1 anti-circularity fix).
- **You label ~50–60, not thousands.** On a no-leaderboard competition the human anchor is
  the only signal correlated with the hidden ground truth.

## Outputs consumed downstream

- `artifacts/reference_date.json` → every stage (recency features) via `common.config.get_reference_date()`
- `artifacts/golden_set.json` → Stage 5 composite calibration, Stage 6 blend-α selection
- `artifacts/naive_baseline_top100.json` → final report (v6 vs naive NDCG@10)
