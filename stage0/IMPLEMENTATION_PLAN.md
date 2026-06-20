# Redrob V6 — Implementation Plan & Repository Blueprint

This is the build map for Architecture V6. **Stage 0 is implemented and tested** (see
`stage0/` and `common/`); everything below is the contract each later stage must satisfy.
No architecture changes — this is implementation planning only.

---

## What I verified against your real data (not assumptions)

Running the Stage 0 code on your actual `sample_candidates.json` surfaced three facts that
shaped the implementation:

1. **`sample_candidates.json` is a JSON array; `candidates.jsonl` is line-delimited.** The
   shared loader (`common/io.py`) auto-detects both, so every stage reads either transparently.
2. **The hardcoded reference date was wrong.** Derived value is **2026-05-25** (max
   `last_active_date`), 12 days before the old `2026-06-06` guess. Now frozen to
   `artifacts/reference_date.json` and read everywhere via `common.config.get_reference_date()`.
3. **Both pasted sample candidates are textbook traps**, and the proxy selector flags them
   (services/relocation disqualifier; out-of-band YOE). The golden-set worksheet pre-computes
   the hints a human needs to label fast.

---

## Repository structure (production-grade)

```
INDIA_RUNS_DATA_AND_AI_CHALLENGE/
├── common/                      # NEW — shared, imported by every stage
│   ├── __init__.py
│   ├── config.py                # all paths + frozen reference date + SEED
│   └── io.py                    # JSONL/JSON-array auto-detecting loader
│
├── stage0/                      # DONE — pre-flight + golden set
│   ├── 00_env_check.py
│   ├── 01_data_audit.py
│   ├── 02_select_anchor.py
│   ├── 03_build_golden_set.py
│   └── README.md
│
├── stage1/                      # JD intelligence (local LLM + deterministic fallback)
│   ├── 10_parse_jd.py           # -> artifacts/jd_config.json
│   ├── 11_skill_taxonomy.py     # -> artifacts/skill_groups.json (importable module too)
│   └── 12_jd_embeddings.py      # -> artifacts/jd_embedding.npy, ideal_embedding.npy
│
├── stage2/                      # candidate feature engineering
│   ├── 20_features_core.py      # career/skills/edu/logistics/behavioral  (lib of pure fns)
│   ├── 21_disqualifiers.py      # incl. 2 new flags (pure_research, closed_source)
│   ├── 22_anchor_helpers.py     # hard_req_keyword_count, is_engineering_title
│   └── 23_build_feature_table.py# -> artifacts/features_100k.parquet  (the master runner)
│
├── stage3/                      # hybrid retrieval index
│   ├── 30_candidate_text.py     # synthesize_candidate_text (current role doubled)
│   ├── 31_encode_candidates.py  # bge-large on GPU -> candidate_embeddings.npy (+ ids.json)
│   ├── 32_build_bm25.py         # -> bm25_scores.npy
│   └── 33_hybrid_score.py       # writes hybrid_score back into features parquet
│
├── stage4/                      # honeypot audit (recall-hardened + precision-guarded)
│   ├── 40_honeypot_signals.py   # 10 keyword + 4 arithmetic signals (lib)
│   ├── 41_run_honeypot.py       # -> honeypot_score column; precision sweep report
│   └── 42_honeypot_tests.py     # synthetic recall test + 100K precision flag-rate
│
├── stage5/                      # composite scoring + ANCHOR CALIBRATION
│   ├── 50_composite.py          # compute_relevance_score / compute_final_score (lib)
│   ├── 51_calibrate.py          # hard gate + Spearman ρ vs golden_set.json
│   └── 52_submission_one.py     # SAFETY-NET submission from composite alone
│
├── stage6/                      # 2-model ranker + anchor-tuned blend
│   ├── 60_label_rule.py         # deterministic rule labels
│   ├── 61_label_local_llm.py    # Qwen GGUF labels (GPU) — NO API
│   ├── 62_train_rankers.py      # 2x LightGBM lambdarank -> ranker_rule.txt, ranker_llm.txt
│   ├── 63_pick_alpha.py         # choose blend α to max NDCG@10 on anchor -> blend.json
│   └── 64_shap_prune.py         # optional: drop dead features -> lgb_features.json
│
├── stage7/                      # final ranking + human audit + output
│   ├── 70_generate_top40.py     # model top-40 for you to read
│   ├── 71_audit_log.py          # helper to write artifacts/audit_log.json (remove/demote)
│   ├── 72_reasoning.py          # literal-fact reasoning -> reasoning_cache.json
│   ├── rank.py                  # ★ CPU-ONLY, NO-NET, ≤5min — the reproduced step
│   └── validate_submission.py   # 100 rows, unique ranks/ids, monotone scores, honeypot ≤8%
│
├── sandbox/
│   └── redrob_demo.ipynb        # Colab: pull artifacts, run rank.py on ≤100 sample
│
├── artifacts/                   # shared outputs (see .gitignore for what's committed)
├── archive/                     # old v1–v5 stuff
├── .gitignore                   # NEW
├── requirements.txt             # NEW (split: precompute vs rank)
├── README.md                    # documents GPU-precompute vs CPU-rank split
└── submission_metadata.yaml
```

**Key conventions that make this maintainable:**
- Every stage imports `common.config` for paths and `get_reference_date()` — no stage hardcodes
  a path or a date.
- Each stage has *library* modules (pure functions, importable + unit-testable) separated from
  *runner* scripts (the numbered entry points that read/write artifacts).
- `rank.py` imports its `validate_submission` explicitly (closes the v6.1 `NameError` risk).

---

## Build order & dependency graph

```
stage0 ──────────────┐ (reference_date, golden_set, naive_baseline)
                     │
stage1 ──┐           │  jd_config, jd/ideal embeddings, skill taxonomy
         │           │
stage2 ◄─┘◄──────────┘  needs jd_config (req strengths) + reference_date
   │  features_100k.parquet (no hybrid_score yet)
   ▼
stage3                  needs candidate text + jd embeddings → writes hybrid_score
   │  parquet now has hybrid_score
   ▼
stage4                  needs parquet → writes honeypot_score
   │
   ▼
stage0/02 (RE-RUN optional)  full select_anchor now that hybrid/honeypot exist
   │   (only if you want to swap proxy buckets for real ones; Day-1 anchor already valid)
   ▼
stage5 ◄── golden_set   composite + calibrate (hard gate + ρ) → SUBMISSION #1
   │
   ▼
stage6 ◄── golden_set   2 label sets → 2 rankers → α on anchor
   │
   ▼
stage7 ◄── everything   top-40 → human audit → reasoning → rank.py → SUBMISSION #2
```

**Critical dependencies (the ones that bite if violated):**
- `reference_date.json` must exist before Stage 2 (recency features). Stage 0 guarantees it.
- `jd_config.json` must exist before Stage 2 (requirement strengths feed coverage features).
- `hybrid_score` (Stage 3) must be in the parquet before Stage 4's selector and Stage 5.
- `golden_set.json` must be frozen before Stage 5/6 calibration — and never re-selected from a
  tuned score afterward (anti-circularity).
- Train-time feature list (`lgb_features.json`) must be a subset of `rank.py`'s parquet columns
  — assert this in `rank.py` (closes the train/inference skew risk).

---

## Recommended sequencing over your remaining days

| Day | Stage work | Milestone |
|-----|-----------|-----------|
| 1 | **Stage 0 (done) + start labeling**; Stage 1 parse/taxonomy | reference_date frozen; begin golden set |
| 2 | Finish golden set; Stage 1 embeddings; start Stage 2 | `golden_set.json` frozen (≥50) |
| 3 | Stage 2 features; Stage 3 candidate text | feature table building |
| 4 | Stage 2 disqualifiers; Stage 3 encode + bm25 (GPU) | `features_100k.parquet` + `hybrid_score` |
| 5 | Stage 4 honeypot + **both-direction tests** | honeypot_score; precision ≤1.5% confirmed |
| 6 | Stage 5 composite + calibrate | **Submission #1 (safety net)** |
| 7 | Stage 6 labels (rule + Qwen on GPU) | 2,500 labeled (start early; can take hours) |
| 8 | Stage 6 train 2 rankers + pick α | blend.json |
| 9 | Stage 7 top-40 + **human audit top-30** | audit_log.json |
| 10 | Stage 7 reasoning + rank.py + validator; full dry run | **Submission #2 (primary)** |
| 11 | Colab sandbox; README; metadata; AI-tools declaration | sandbox proven ≤5min CPU |
| 12 | Buffer; **Submission #3 only if anchor NDCG@10 improved** | — |

---

## Stage-by-stage file contracts (what each must produce)

**stage1** → `jd_config.json` (hard/soft req strengths, disqualifier list incl. 2 new, ideal
summary), `skill_groups.json`, `jd_embedding.npy`, `ideal_embedding.npy`. Local Qwen with a
hand-authored deterministic fallback merged underneath — correct even if the model never runs.

**stage2** → `features_100k.parquet` keyed by `candidate_id`, ~70 columns, all recency features
using the frozen reference date. Includes the two new disqualifier flags and the anchor-helper
columns Stage 0 already depends on. Library functions are pure and unit-tested on the 2 samples.

**stage3** → `candidate_embeddings.npy` (+ `candidate_embeddings_ids.json`), `bm25_scores.npy`,
and `hybrid_score` written back into the parquet. **Encode candidates WITHOUT the bge query
prefix** (only the JD gets the prefix) — asymmetric, as the model expects.

**stage4** → `honeypot_score` column + a precision-sweep report. Ship only if flag rate ≤ ~1.5%
and no clean 5–9yr product-company candidate is flagged.

**stage5** → calibrated composite; `evaluate_on_anchor` must pass the hard gate (no label-0
outscores a label-3) and report ρ. Emits the safety-net submission CSV.

**stage6** → `ranker_rule.txt`, `ranker_llm.txt`, `blend.json` (α chosen on the anchor),
`lgb_features.json`. Single query group is correct here (one JD = one query).

**stage7** → `reasoning_cache.json` (literal facts only), `audit_log.json` (your overrides),
`submission.csv` via `rank.py` (rank-based monotone unique scores), validator green.

---

## Immediate next actions

1. Drop `common/` and `stage0/` into your repo, add `.gitignore`, commit.
2. `python stage0/00_env_check.py` then `python stage0/01_data_audit.py` on the **full**
   `candidates.jsonl` to freeze the real reference date and distribution.
3. `python stage0/02_select_anchor.py`, open `artifacts/golden_set_worksheet.csv`, and start
   labeling. This is the long pole — begin today.
4. `python stage0/03_build_golden_set.py` once you've labeled ≥50.

When the golden set is frozen, say the word and I'll build Stage 1.
