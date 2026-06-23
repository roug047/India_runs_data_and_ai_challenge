# Redrob AI — Intelligent Candidate Ranking System

Ranks the **top 100 candidates** for a *Senior AI Engineer* role out of a **100,000-candidate**
pool, for the India Runs Data & AI Challenge.

**Headline facts**

| | |
|---|---|
| Ranking quality (held-out cross-validation) | **Spearman 0.85** |
| Honeypots (traps) in our top 100 | **0** (disqualification threshold is >10%) |
| Ranking step runtime | **~8 seconds** (limit: 5 minutes) |
| Compute for ranking | **CPU-only, no network, < 16 GB RAM** |
| Paid API cost | **$0** (all models run locally) |
| Reproducibility | **Verified in a clean virtual environment** |

---

## Table of contents

1. [The 30-second summary](#1-the-30-second-summary)
2. [How to reproduce the submission](#2-how-to-reproduce-the-submission)
3. [Repository layout](#3-repository-layout)
4. [How the system works (the 7 stages)](#4-how-the-system-works-the-7-stages)
5. [Key engineering decisions](#5-key-engineering-decisions-the-defense)
6. [The precompute vs. reproduce split](#6-the-precompute-vs-reproduce-split)
7. [Regenerating everything from scratch](#7-regenerating-everything-from-scratch-optional)
8. [Sandbox / demo](#8-sandbox--demo)
9. [Validation results](#9-validation-results)

---

## 1. The 30-second summary

The core idea: **rank by what a candidate has actually built, not by the keywords they list.**

Most ranking systems embed a profile and a job description and measure similarity. That is easy
to fool — a candidate who pastes every AI buzzword into their skills section scores highly even
if their real career is in warehouse operations. This dataset is full of exactly those traps
(keyword stuffers and ~80 "honeypot" profiles with subtly impossible histories).

Our system instead weighs **career evidence** (what the role descriptions say the person did)
above **skill claims** (what they list), discounts claims that on-platform assessment scores
contradict, and runs a precision-first detector for impossible profiles. Final scores come from
a **rank-average of two independent rankers** — a transparent feature composite and a learned
LightGBM model — chosen by cross-validation on a hand-labeled anchor set.

Everything runs locally. The expensive parts (embeddings, model training, label generation)
are precomputed once; the **ranking step that produces the submission is CPU-only and finishes
in about 8 seconds.**

---

## 2. How to reproduce the submission

The submission CSV is produced by a single command:

```bash
python rank.py --candidates candidates.jsonl --out submission.csv
```

This is the **scored step**. It is CPU-only, makes no network calls, and completes in well
under the 5-minute limit. It reads pre-computed artifacts (committed to this repo) and the
candidate file, and writes a 100-row ranked CSV.

### Clean-environment reproduction (recommended verification)

To confirm it runs with only the declared dependencies — exactly what a sandboxed reviewer
does — use a fresh virtual environment:

```bash
# 1. create an isolated, empty environment
python -m venv testenv

# 2. activate it
#    Windows:  testenv\Scripts\activate
#    macOS/Linux:  source testenv/bin/activate

# 3. install ONLY the runtime dependencies
pip install -r requirements.txt

# 4. run the ranking step
python rank.py --candidates candidates.jsonl --out submission.csv

# 5. validate the output against the spec
python stage7/validate_submission.py submission.csv
```

Expected output: `VALID`, ~8 seconds elapsed, 100 rows, 0 honeypots in the top 100.

The candidate file may be the plain `candidates.jsonl` or the gzipped `candidates.jsonl.gz` —
`rank.py` handles both automatically.

---

## 3. Repository layout

```
.
├── rank.py                     # THE SCORED STEP — produces the submission CSV (CPU, ~8s)
├── requirements.txt            # runtime dependencies for rank.py
├── submission_metadata.yaml    # team / submission metadata (mirrors portal fields)
├── sandbox_demo.ipynb          # hosted-sandbox demo notebook (Colab)
│
├── common/                     # shared config + IO (gzip-aware candidate reader)
│
├── stage0/  …  stage7/         # the pipeline, one folder per stage (see Section 4)
│
└── artifacts/                  # pre-computed outputs the pipeline produces
    ├── features_100k.parquet       # per-candidate feature table (rank.py reads this)
    ├── ranker_rule.txt             # LightGBM model (rule-labeled)
    ├── ranker_llm.txt              # LightGBM model (LLM-labeled)
    ├── blend.json                  # blend weight between the two rankers
    ├── composite_weights.json      # calibrated feature-composite weights
    ├── engine_choice.json          # which engine won cross-validation (rank_average)
    ├── lgb_features.json           # feature order for the LightGBM models
    ├── audit_log.json              # documented human top-30 audit (remove/demote)
    ├── golden_set.json             # 95-candidate hand-labeled anchor (validation)
    └── … (JD config, skill taxonomy, stage reports)
```

Each stage folder contains its own `README.md` and `INTEGRATION.md` describing that stage in
detail. Large regenerable files (raw embeddings `*.npy`, the local LLM in `models/`) are
git-ignored — they are not needed by `rank.py` (the dense retrieval signal is already baked
into `features_100k.parquet`).

---

## 4. How the system works (the 7 stages)

The pipeline is built in seven stages. Stages 0–6 are **precompute**; Stage 7 is the
**ranking step** plus auditing and reasoning.

### Stage 0 — Golden set (the ruler)
Before building anything, we hand-labeled an anchor of candidates (relevance tiers 0–3),
growing it to **95 candidates** as the project progressed. This anchor is the load-bearing
validator: every later design choice is checked against it. The dataset's reference "today"
date is derived empirically from the data (the latest activity date), not hardcoded.

### Stage 1 — JD intelligence
Parse the job description deterministically into **hard requirements** (e.g. embeddings/
retrieval, vector search, ranking evaluation, production Python), **soft requirements**, and
**disqualifiers**. Build a 17-group skill taxonomy and encode the JD with the `bge-large`
embedding model (query-prefixed, asymmetric).

### Stage 2 — Feature engineering (the heart)
Compute ~53 features per candidate. The central formula:

```
requirement coverage = 0.65 · career-evidence  +  0.35 · (skill-claim · credibility)
```

- **Career evidence** = how strongly the candidate's *role descriptions* show they did the
  work. This dominates.
- **Skill claims** are weighted less and **discounted** when on-platform assessment scores
  contradict them (claiming "expert" with a low assessment lowers credibility).
- **Production evidence** only counts when ML/technical context appears in the *role
  descriptions* — not the self-authored summary. This is what stops a keyword-stuffer whose
  career is logistics ("production" = warehouse output) from getting ML-production credit.

This design is what makes the dataset's keyword traps backfire instead of winning.

### Stage 3 — Hybrid retrieval
Encode each candidate's career text (recency-weighted: the current role is placed first and
counted double so it survives the 512-token limit) with `bge-large`, and combine dense
similarity with BM25:

```
hybrid score = 0.60 · dense  +  0.40 · BM25
```

Dense similarity finds the "quiet shipper" who built a recommender without using buzzwords;
BM25 catches exact rare tech terms. The two signals are complementary (correlation ≈ 0.54).

### Stage 4 — Honeypot detection
The dataset hides ~80 **honeypots**: profiles with subtly impossible histories (e.g. a summary
claiming 7 years while the experience field says 3; "expert" in 10 skills each used 0 months).
Ranking these in your top 10 is a strong signal your system isn't reading profiles — and a
honeypot rate above 10% in the top 100 is an automatic disqualification.

Our detector is **precision-first**: it flags about 0.06% of the pool. The strongest signal is
a contradiction between the experience a candidate *claims in their summary* and their actual
experience field — a tell that caught honeypots which initially fooled even careful human
labeling. **Result: 0 honeypots in the final top 100.**

### Stage 5 — Composite + calibration
All signals combine multiplicatively so that a single fatal flag collapses the score:

```
final = relevance × disqualifier_penalty × honeypot_score × availability × notice_factor
```

The feature weights are tuned against the anchor under two constraints: a **hard gate** (no
candidate we judged unfit may outrank one we judged a strong fit) and **L2 regularization**
(to prevent overfitting the small anchor). Held-out cross-validated Spearman: **0.83**.

### Stage 6 — Learned ranker
Two **LightGBM lambdarank** models are trained on independent label sources — deterministic
rule-based labels and labels from a **local quantized Qwen-2.5-3B** model (no API) — then
blended. Training the ranker on a learned objective complements the hand-tuned composite.

### Stage 7 — Ranking, audit, and reasoning
`rank.py` is the scored step. It also:
- **Selects the engine** by cross-validation (see Section 5).
- Applies a **documented human audit** (`audit_log.json`) — top-30 overrides are reproducible
  data, not manual CSV edits.
- Generates **reasoning** for each candidate: a literal quoted achievement from their history
  plus an explicit, feature-grounded assessment and logistics — never invented facts.

---

## 5. Key engineering decisions (the defense)

These are the choices that distinguish a carefully-engineered system from a lucky one.

**1. We shipped the model that generalizes, not the one with the best in-sample score.**
We compared three engines under 5-fold cross-validation on the anchor:

| Engine | Held-out Spearman | NDCG@10 |
|---|---|---|
| Feature composite | 0.834 | 0.956 |
| LightGBM ranker | 0.710 | 0.856 |
| **Rank-average (chosen)** | **0.851** | **0.965** |

The learned ranker alone *looked* competitive on a smaller anchor but proved to be overfitting
once the anchor grew. Rank-averaging the two engines cancelled their independent errors and beat
both. We selected it on held-out evidence, recorded in `engine_choice.json`.

**2. A "hard gate" turned label disagreements into a bug-finding tool.**
Enforcing "no unfit candidate may outrank a strong fit" on the anchor repeatedly surfaced —
each time through a single failing candidate — real, pool-wide bugs: an over-aggressive
title-tenure penalty, a taxonomy blind spot (recommendation systems weren't being counted as
ranking experience), honeypot false-positives that were burying thousands of real candidates,
and the keyword-stuffer production-credit hole. Each fix improved the whole ranking.

**3. The honeypot detector beat human labeling — by design.**
During labeling we initially marked several honeypots as strong fits; their summaries read
convincingly. The experience-contradiction signal caught them. The lesson is encoded in the
system: judge internal consistency, not surface impressiveness.

**4. Availability and location reflect placeability, not just talent.**
The JD asks to down-weight inactive/unresponsive candidates and to prioritize India-based or
willing-to-relocate ones (no visa sponsorship). So a brilliant but long-inactive engineer is a
weaker *placement*; an overseas candidate who has committed to relocating competes on merit,
while one who won't relocate is deprioritized. These are explicit, JD-grounded rules — and in
the final ranking, willing-to-relocate overseas candidates appear on merit while non-relocators
do not.

**5. Reasoning is honest synthesis, never invention.**
Because the synthetic dataset reuses career text across candidates, we do **not** fabricate
distinguishing details (the spec penalizes hallucination). Each reasoning string quotes a
*literal* sentence from the candidate's own history, adds an explicit feature-grounded
assessment ("covers JD requirements: …"), and states logistics. Only facts present in the
profile are cited.

---

## 6. The precompute vs. reproduce split

The challenge rules apply the compute limits (5 min, CPU, no network) **only to the ranking
step** — precompute may use GPU, network, and unlimited time. We respect that split cleanly:

| Phase | What it does | Compute | When it runs |
|---|---|---|---|
| **Precompute** (Stages 1–6) | embeddings, BM25, features, honeypot scores, model training, LLM labels | GPU OK, network OK, slow OK | once, offline |
| **Reproduce** (`rank.py`) | load features + models, score, rank, write CSV | **CPU-only, no network, ~8s** | every submission |

The artifacts `rank.py` needs are committed to the repo, so a fresh clone can run the ranking
step immediately without re-running precompute. The dense-retrieval signal is already baked into
`features_100k.parquet`, so the raw embeddings (large) are not required at ranking time.

---

## 7. Regenerating everything from scratch (optional)

Only needed to rebuild the precomputed artifacts (requires a GPU for embeddings and the local
LLM). The ranking step does **not** require this.

```bash
# Stage 1 — JD intelligence + embeddings
python stage1/10_parse_jd.py
python stage1/11_skill_taxonomy.py
python stage1/12_jd_embeddings.py

# Stage 2 — features
python stage2/20_build_features.py

# Stage 3 — hybrid retrieval (GPU encode)
python stage3/30_candidate_text.py
python stage3/31_encode_candidates.py
python stage3/32_hybrid_score.py

# Stage 4 — honeypot scoring
python stage4/40_run_honeypot.py

# Stage 5 — composite calibration
python stage5/53_calibrate_regularized.py --reg 0.10

# Stage 6 — learned rankers (local LLM labeling)
python stage6/60_label_rule.py --n 4000
python stage6/61_label_llm.py
python stage6/62_train_blend.py
python stage6/63_compare_engines.py     # selects the engine via cross-validation

# Stage 7 — produce the submission
python rank.py --candidates candidates.jsonl --out submission.csv
```

Dependencies for precompute (beyond `requirements.txt`): `sentence-transformers`,
`transformers`, `torch`, `rank-bm25`, and `llama-cpp-python` for the local LLM. The embedding
model is `bge-large`; the labeling model is a quantized Qwen-2.5-3B GGUF.

---

## 8. Sandbox / demo

`sandbox_demo.ipynb` is a Google Colab notebook that clones the repo, installs the CPU
dependencies, builds a 100-candidate sample, runs `rank.py`, and shows the ranked output —
end-to-end in under 5 minutes on a free CPU runtime. It satisfies the hackathon's hosted-sandbox
requirement (small-sample reproducibility). Open it in Colab, set the repo URL in the first
cell, and run all cells.

---

## 9. Validation results

| Check | Result |
|---|---|
| Held-out CV Spearman (rank-average engine) | **0.85** |
| Composite engine (CV) | 0.83 |
| Hard gate (no unfit over strong-fit on anchor) | **clean — 0 violations** |
| Honeypots in top 100 | **0** (DQ at >10%) |
| `rank.py` runtime | **~8 s** (limit 300 s) |
| `rank.py` compute | CPU-only, no network, < 16 GB RAM |
| Clean-venv reproduction | **VALID** |
| Submission format | 100 rows, unique ranks, monotone scores, 100 distinct reasonings |
| Paid API cost | **$0** |

---

*Built with AI assistance (declared honestly per the hackathon rules). All architecture,
debugging, validation, and engineering judgment — the feature design, the honeypot signals, the
cross-validation-driven engine selection, the bug fixes surfaced by the hard gate — represent
real engineering work, reproducible from this repository.*
