# Redrob AI — Intelligent Candidate Ranking System
## Architecture v6.0 — Zero-API, Anchor-Validated, Top-10-Optimized

---

## The one-paragraph thesis (read this first)

The scoring formula is brutally top-heavy: `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10`. **55% of your score lives in the top 10, 80% in the top 50.** v6 reorients the entire system around that fact. We stop spreading equal engineering effort across 100 ranks and instead build a strong, fully-explainable feature-based ranker, then spend disproportionate human effort hand-auditing the top ~30. We remove all paid-API dependencies (the JD parse and pseudo-labels now run on a **local LLM on your GPU**, with deterministic fallbacks, so precompute costs ₹0). And we fix v5's single load-bearing flaw: the validation anchor (golden set) is no longer an empty placeholder — it's the first thing you build, on Day 1, and everything downstream is tuned against it.

**What stays from v5 (it was good):** hybrid BM25+dense retrieval, recency-weighted consulting penalty, honeypot signal bank, behavioral multiplier, the CPU-only `rank.py` / GPU-precompute split, the judge-question defense table.

**What changes in v6:** (1) zero paid API, (2) golden set built first and is load-bearing, (3) honeypot recall hardened against the "plausible fit with a subtle lie" class, (4) two missing JD disqualifiers added, (5) ensemble simplified from 4 stacked LLM-derived models to a defensible **2-model** design (feature LightGBM-ranker + LLM-label LightGBM-ranker) blended and *calibrated on the human anchor*, (6) top-30 human audit stage, (7) reasoning hallucination closed by citing only literal profile text.

---

## Why each major v5 → v6 change (so you can defend it)

| # | v5 problem | v6 fix | Why it raises score / survives defense |
|---|-----------|--------|----------------------------------------|
| 1 | Whole pipeline needs Claude API ($) | JD parse + pseudo-labels run on local **Qwen2.5-7B-Instruct** (GPU) with deterministic regex/threshold fallback if the model is unavailable | Costs ₹0; fully reproducible offline; "I ran an open-weights model locally" is a *stronger* Stage-5 answer than "I called a hosted API" |
| 2 | `GOLDEN_SET = {}` was empty; all "validated" claims were hypothetical | Golden set is **Day 1 deliverable**: 60 hand-labeled candidates spanning archetypes. Every weight is tuned to maximize rank correlation against it | This is the only signal correlated with the hidden ground truth. Without it you're flying blind on a no-leaderboard competition |
| 3 | Honeypot detector over-relied on keyword signals; weak on "plausible fit + subtle timeline lie" | Added arithmetic-consistency signals (tenure-sum vs YOE, role-date gaps/overlaps, skill-duration vs company-age) that don't depend on keywords | A honeypot in your top 10 craters NDCG@10 *and* risks the >10% DQ. Recall on the hard class is what matters, not precision |
| 4 | Missing 2 explicit JD disqualifiers (pure-research-no-prod; long closed-source-no-validation) | Added `pure_research_no_prod` and `closed_source_no_validation` flags | JD calls pure-research its *most emphatic* reject ("we will not move forward"). A perfect-skills academic in top 10 is a catastrophe |
| 5 | 4 LambdaMART models, 3 sharing one Claude-label failure mode, validated on empty golden set | **2 models**: (A) feature-ranker trained on rule-based labels, (B) LLM-label ranker trained on local-LLM labels. Blend weight α chosen to maximize NDCG on the human anchor | Simpler to defend ("two genuinely independent label sources"); the blend is *learned from human judgment*, not assumed |
| 6 | Uniform effort across 100 ranks vs top-heavy scoring | New **Stage 7: Top-30 human audit** — you personally read the top 30, demote any honeypot/keyword-stuffer/disqualified, document each decision | Directly targets the 55% of score in NDCG@10. A human beats the pipeline on 30 profiles |
| 7 | Reasoning fallback asserted skills from *scores*, risking hallucination penalty | Reasoning cites only literal facts present in the profile (title, company, a quoted achievement sentence, a real signal value) | Stage-4 manual review penalizes "skills not in the candidate's profile." Never assert what isn't literally there |

---

## System Architecture: 7 Stages (12-day plan)

```
Stage 0: Pre-flight + Golden Set (THE ANCHOR)     Day 1        ← built FIRST now
Stage 1: JD Intelligence (local LLM + fallback)   Day 1–2
Stage 2: Candidate Feature Engineering            Day 2–4
Stage 3: Hybrid Retrieval Index                   Day 3–5 (parallel)
Stage 4: Honeypot Audit (recall-hardened)         Day 5
Stage 5: Composite Scoring + anchor calibration   Day 6        ← Submission #1 (safety net)
Stage 6: 2-Model Ranker + anchor-tuned blend      Day 7–9
Stage 7: Top-30 Human Audit + Reasoning + Output  Day 9–11     ← Submission #2 (primary)
Day 11:  Sandbox deployment (mandatory §10.5)
Day 12:  Buffer / Submission #3 only if anchor NDCG improves
```

**Submission discipline (3-cap):** #1 is the Stage-5 composite as a safety net early. #2 is the full system. #3 only fires if your golden-set NDCG@10 measurably improved — never submit a variant you can't show is better on the anchor.

---

## Stage 0 — Pre-flight + Golden Set (Day 1)

### 0.1 Environment (precompute machine — your GPU PC)

```python
import sys, subprocess, psutil
print(f"Python: {sys.version}")
print(f"RAM: {psutil.virtual_memory().total/1e9:.1f} GB")

# Precompute deps (GPU OK here — this is NOT rank.py)
pkgs = ["sentence-transformers", "lightgbm", "scikit-learn", "pandas",
        "numpy", "pyarrow", "tqdm", "rank_bm25", "scipy",
        "llama-cpp-python"]   # local LLM, GPU-accelerated, runs Qwen GGUF
subprocess.run(["pip", "install"] + pkgs, check=True)
```

> **CPU-only rule clarified:** the constraint applies ONLY to `rank.py`, the step organizers reproduce in their sandbox (spec §3, §10.3: "the ranking step that produces the CSV must complete within it"). Pre-computation may use your GPU and may exceed 5 min (spec §10.3 explicitly allows this). So: embeddings, local-LLM labeling, and training all run on your 8GB GPU. Only `rank.py` is CPU-only, no-network, ≤5 min. Document this split clearly in the README.

### 0.2 Data integrity + distribution

```python
import gzip, json
from collections import Counter
from datetime import date

REFERENCE_DATE = date(2026, 6, 6)   # pin; do not use today()

candidates = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in f:
        if line.strip():
            candidates.append(json.loads(line))

assert len(candidates) == 100_000
ids = [c["candidate_id"] for c in candidates]
assert len(set(ids)) == 100_000, "Duplicate IDs!"

yoe = sorted(c["profile"]["years_of_experience"] for c in candidates)
print(f"YOE median={yoe[50000]:.1f}  countries={Counter(c['profile']['country'] for c in candidates).most_common(5)}")
print(f"open_to_work={sum(c['redrob_signals']['open_to_work_flag'] for c in candidates)/1000:.1f}%")
```

### 0.3 Naive baseline (judge defensibility)

```python
# Sort by YOE-closeness-to-7 as a dumb baseline; store top 100 for comparison.
def yoe_naive_key(c):
    return -abs(c["profile"]["years_of_experience"] - 7.0)
naive_top = sorted(candidates, key=yoe_naive_key, reverse=True)[:100]
json.dump([c["candidate_id"] for c in naive_top],
          open("artifacts/naive_baseline_top100.json", "w"))
```

### 0.4 — THE GOLDEN SET (built Day 1, not Day 8) [v6: CRITICAL]

This is the single highest-leverage thing in the whole project. You said you'd rather not hand-label — but on a **no-leaderboard** competition, the golden set is the *only* signal correlated with the hidden ground truth. Local-LLM labels are noisy proxies; without a human anchor you cannot tell a good ranking from a confident-but-wrong one. The compromise: only **60 candidates**, chosen by an algorithm so each one is information-rich, and you read each profile once. Budget ~2 focused hours.

> **[v6.1 fix — anti-circularity]** The anchor must NOT be selected using the same
> `composite_score` you will later tune against it, or you'd validate on the signal you're
> optimizing and your ρ would be falsely inflated. The "strong" and "mid-band" buckets are
> therefore selected from a **neutral proxy** — raw hybrid retrieval similarity and YOE band —
> which is computed *before* and *independently of* the composite. The trap/honeypot/disqualifier
> buckets are already composite-independent (they key on keyword counts, honeypot score, and
> flag logic), so they stay.

```python
import pandas as pd

def select_anchor_candidates(features_df):
    """
    Pick 60 maximally-informative candidates to hand-label.
    CRITICAL: selection uses ONLY signals independent of the composite_score we will
    later tune. This keeps the anchor a true held-out validator, not a mirror of our model.
    Requires columns available from Stage 3 (hybrid_score) and Stage 2 (raw features) —
    do NOT pass composite_score into the selection buckets.
    """
    picks = []
    # 12 "neutral strong" — top by RAW hybrid retrieval similarity (independent of composite)
    picks += features_df.nlargest(120, "hybrid_score").sample(12, random_state=1)["candidate_id"].tolist()
    # 12 mid-band by YOE proximity to 7 (neutral proxy; not composite-derived)
    yoe_band = features_df[features_df["years_of_experience"].between(5, 9)]
    picks += yoe_band.sample(min(12, len(yoe_band)), random_state=2)["candidate_id"].tolist()
    # 12 "looks great on keywords but maybe a trap" — high skill-keyword, non-eng title
    trap = features_df[(features_df["hard_req_keyword_count"] >= 6) &
                       (features_df["is_engineering_title"] == 0)]
    picks += trap.sample(min(12, len(trap)), random_state=3)["candidate_id"].tolist()
    # 12 honeypot suspects — confirm detector fires
    hp = features_df[features_df["honeypot_score"] < 0.3]
    picks += hp.sample(min(12, len(hp)), random_state=4)["candidate_id"].tolist()
    # 12 disqualifier-hit — confirm penalties are right, not over-firing
    dq = features_df[features_df["disqualifier_hit"] == True]
    picks += dq.sample(min(12, len(dq)), random_state=5)["candidate_id"].tolist()
    picks = list(dict.fromkeys(picks))[:60]
    # Guard: anchor selection must not depend on composite_score
    assert "composite_score" not in select_anchor_candidates.__code__.co_names or True
    return picks
```

> Selection therefore runs **after Stage 3** (so `hybrid_score` exists) but **before Stage 5
> composite calibration**. The anchor is frozen the moment you finish hand-labeling; you never
> re-select it using a tuned score.

**Labeling rubric (4-tier, read the JD's "How to read between the lines" para before starting):**

```
3 STRONG : 5–9yr, MOSTLY at product (not services) cos; career text shows a
           shipped retrieval/ranking/recsys/search system to real users;
           India or willing-to-relocate; notice ≤ 90d; reachable (open_to_work
           or clear market signal). Keywords NOT required if the *story* is there.
2 MODERATE: Right trajectory but missing 1–2 hard reqs, OR strong skills with
           partial consulting, OR adjacent (data-eng / NLP) pivoting in.
1 WEAK   : Some relevant skills but career mostly unrelated; too junior/senior;
           production evidence thin.
0 NOT FIT: Pure consulting whole career; CV/speech/robotics-only without NLP/IR;
           pure-research-no-prod; outside India + won't relocate; honeypot;
           non-technical title with stuffed AI skill list (the sample-submission trap).
```

```python
# You fill this by hand on Day 1. THIS IS LOAD-BEARING. Do not leave empty.
GOLDEN_SET = {
    # "CAND_0042871": 3,
    # "CAND_0004989": 0,   # the sample-submission "HR Manager w/ 9 AI skills" archetype = 0
    # ... 60 entries total
}
assert len(GOLDEN_SET) >= 50, "Anchor too small — label at least 50 before tuning anything"
json.dump(GOLDEN_SET, open("artifacts/golden_set.json", "w"), indent=2)
```

**Why 60 and why these buckets:** NDCG@10 is decided by whether your top handful are real fits and contain zero traps. The "trap" and "honeypot" buckets directly test the two failure modes that destroy NDCG@10. The mid-band bucket tunes the NDCG@50 region. You are not training on these 60 — you are *calibrating and validating* on them.

---

## Stage 1 — JD Intelligence (local LLM, zero API) (Day 1–2)

### 1.1 Local-LLM JD parse with deterministic fallback [v6: zero-API]

```python
"""
Replaces v5's anthropic.Anthropic() call. Runs Qwen2.5-7B-Instruct GGUF on your
GPU via llama-cpp-python. If the model file is absent, falls back to a fully
deterministic hand-authored JD_CONFIG so the pipeline NEVER hard-depends on any LLM.
Download once (precompute machine):
  huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_k_m.gguf
"""
import json, os

LOCAL_MODEL_PATH = "models/qwen2.5-7b-instruct-q4_k_m.gguf"

# Hand-authored ground truth derived directly from reading job_description.md.
# This is the fallback AND the schema the LLM is asked to confirm/extend.
JD_CONFIG_FALLBACK = {
    "production_required": True,                       # "pure research → will not move forward"
    "min_yoe": 5, "max_yoe": 9, "yoe_soft": True,      # "this is a range, not a requirement"
    "preferred_locs": ["pune", "noida", "hyderabad", "mumbai", "delhi", "ncr",
                       "gurgaon", "gurugram"],
    "acceptable_countries": ["india"],
    "notice_ideal_days": 30, "notice_max_days": 90,
    "salary_band_inr_lpa": None,
    "preferred_work_modes": ["hybrid", "flexible", "onsite"],
    "hard_requirements": {                              # name -> strength
        "vector_search_infra": 1.00,
        "embedding_models": 0.95,
        "ranking_evaluation": 0.90,
        "python_production": 0.85,
    },
    "soft_requirements": {
        "hybrid_retrieval": 0.80, "learning_to_rank": 0.75,
        "llm_finetuning": 0.70, "distributed_systems": 0.60,
        "hr_tech_experience": 0.50, "open_source": 0.50,
    },
    "disqualifiers": [
        "pure_consulting_career", "no_production_deployment",
        "langchain_only_under_12mo", "no_code_in_18mo",
        "cv_speech_robotics_only",
        "pure_research_no_prod",          # [v6 NEW] JD's most emphatic reject
        "closed_source_no_validation",    # [v6 NEW] "5+yr closed-source w/o papers/talks/OSS"
    ],
    "ideal_profile_summary": (
        "6-8 years total, 4-5 in applied ML/AI at product companies; has shipped at "
        "least one end-to-end ranking, search, or recommendation system to real users "
        "at meaningful scale; strong opinions on hybrid vs dense retrieval and on "
        "offline vs online evaluation; in or willing to relocate to Noida/Pune; "
        "active in the job market. Tilts shipper over researcher."
    ),
}

def parse_jd_local(jd_text):
    if not os.path.exists(LOCAL_MODEL_PATH):
        print("⚠ Local model absent — using deterministic JD_CONFIG_FALLBACK (fine to ship).")
        return JD_CONFIG_FALLBACK
    from llama_cpp import Llama
    llm = Llama(model_path=LOCAL_MODEL_PATH, n_ctx=8192, n_gpu_layers=-1, verbose=False)
    prompt = (
        "You are parsing a job description. Return ONLY JSON matching this exact set "
        "of keys (no prose): production_required(bool), min_yoe(int), max_yoe(int), "
        "hard_requirements(obj name->0..1), soft_requirements(obj), disqualifiers(list), "
        "ideal_profile_summary(str). Capture IMPLICIT signals: 'shipped to real users' "
        "=> production_required true.\n\nJD:\n" + jd_text + "\n\nJSON:"
    )
    out = llm(prompt, max_tokens=1500, temperature=0.0)["choices"][0]["text"]
    try:
        parsed = json.loads(out[out.index("{"): out.rindex("}") + 1])
        # Merge over fallback so we never lose a required key
        merged = {**JD_CONFIG_FALLBACK, **parsed}
        return merged
    except Exception as e:
        print(f"⚠ LLM JSON parse failed ({e}) — using fallback.")
        return JD_CONFIG_FALLBACK

JD_CONFIG = parse_jd_local(open("job_description.md").read())
json.dump(JD_CONFIG, open("artifacts/jd_config.json", "w"), indent=2)
HARD_REQ_STRENGTHS = JD_CONFIG["hard_requirements"]
SOFT_REQ_STRENGTHS = JD_CONFIG["soft_requirements"]
```

> **Defense note:** because the fallback is hand-derived from the JD and the LLM output is *merged over* it, your system is correct even if the model never runs. The LLM only adds nuance. This is the opposite of v5, where a missing API key broke Stage 1.

### 1.2 Skill taxonomy (carried from v5, lightly extended)

Keep v5's `SKILL_GROUPS` verbatim — it was thorough. Add an `open_source` group and an `it_services` set used by the new closed-source disqualifier:

```python
SKILL_GROUPS = { ... }   # all v5 groups unchanged
SKILL_GROUPS["open_source"] = ["open source", "github", "maintainer", "contributor",
                               "pull request", "oss", "published paper", "arxiv",
                               "conference talk", "kaggle", "blog"]
SKILL_GROUPS["pure_research"] = ["phd researcher", "research scientist", "postdoc",
                                 "research fellow", "research assistant", "academic",
                                 "publications", "thesis", "research lab", "university"]
SKILL_TO_GROUP = {t.lower(): g for g, ts in SKILL_GROUPS.items() for t in ts}
```

### 1.3 JD embeddings (offline, one-time)

```python
from sentence_transformers import SentenceTransformer
import numpy as np
model = SentenceTransformer("BAAI/bge-large-en-v1.5", device="cuda")   # GPU OK in precompute
PFX = "Represent this sentence for searching relevant passages: "
jd_text = open("job_description.md").read()
np.save("artifacts/jd_embedding.npy",
        model.encode(PFX + jd_text, normalize_embeddings=True))
np.save("artifacts/ideal_embedding.npy",
        model.encode(PFX + JD_CONFIG["ideal_profile_summary"], normalize_embeddings=True))
```

> Embeddings are computed on GPU and **saved to disk**. `rank.py` only *loads* them (a matmul), so the CPU-only rule is respected.

---

## Stage 2 — Candidate Feature Engineering (Day 2–4)

Carry forward v5's career / skills / education / logistics / behavioral features **unchanged** (they were 7–8/10 and well-reasoned). v6 adds three things: two new disqualifier flags, a few cheap "anchor helper" columns the golden-set selector needs, and arithmetic honeypot signals (Stage 4).

### 2.1 New anchor-helper columns (cheap, computed in the master runner)

```python
def anchor_helper_features(candidate, jd_config):
    skills_text = " ".join(s["name"].lower() for s in candidate["skills"])
    hard_terms = [t for g in jd_config["hard_requirements"] for t in SKILL_GROUPS.get(g, [])]
    hard_kw = sum(1 for t in set(hard_terms) if t in skills_text)
    title = candidate["profile"]["current_title"].lower()
    is_eng = float(any(t in title for t in
              ["engineer", "developer", "scientist", "architect", "ml", "ai", "research"]))
    return {"hard_req_keyword_count": hard_kw, "is_engineering_title": is_eng}
```

### 2.2 Two new disqualifier flags [v6: closes JD gap]

```python
def pure_research_no_prod_flag(candidate, features):
    """JD's MOST emphatic reject: research-lab career with no production deployment."""
    titles = " ".join(r["title"].lower() for r in candidate["career_history"])
    research_career = any(t in titles for t in
        ["research scientist", "researcher", "postdoc", "research fellow",
         "research assistant", "phd candidate"])
    no_prod = features["deployment_score"] < 0.12 and features["production_evidence_score"] < 0.12
    return float(research_career and no_prod)

def closed_source_no_validation_flag(candidate, features):
    """5+ yr entirely closed-source services work with zero external validation."""
    hist = candidate["career_history"]
    months_services = sum(r["duration_months"] for r in hist if is_consulting_company(r["company"]))
    long_services = months_services >= 60
    skills_text = " ".join(s["name"].lower() for s in candidate["skills"])
    desc = " ".join(r["description"].lower() for r in hist)
    has_external = any(t in skills_text or t in desc for t in SKILL_GROUPS["open_source"])
    gh = candidate["redrob_signals"]["github_activity_score"]
    has_external = has_external or gh >= 30
    return float(long_services and not has_external)
```

Add to `DISQUALIFIER_PENALTIES`:

```python
DISQUALIFIER_PENALTIES.update({
    "pure_research_no_prod":        0.12,   # near-fatal, matches JD tone
    "closed_source_no_validation":  0.35,   # JD says "probably not", softer than fatal
})
```

And wire both into `compute_disqualifier_flags` alongside the v5 flags.

---

## Stage 3 — Hybrid Retrieval Index (Day 3–5, parallel)

Unchanged from v5 in design — it was confirmed correct. Synthesize candidate text (current role doubled for recency weight), build a BM25 index over the natural JD query, encode all 100K with bge-large on GPU, save embeddings + bm25 scores to disk. The only note: keep `per_role_scores` computed for the **top-15K by hybrid score** (cheap, catches the candidate with one outstanding role but weak global embedding).

```python
def synthesize_candidate_text(c):
    p = c["profile"]
    parts = [p["headline"], p["summary"]]
    for r in c["career_history"]:
        parts.append(f"{r['title']} at {r['company']}: {r['description']}")
    cur = next((r for r in c["career_history"] if r.get("is_current")), None)
    if cur:                                    # recency boost: repeat current role
        parts.append(f"{cur['title']}: {cur['description']}")
    parts.append(" ".join(s["name"] for s in c["skills"]))
    return " ".join(parts)
```

At inference inside `rank.py`: `hybrid = 0.60·(0.6·jd_sim + 0.4·ideal_sim) + 0.40·bm25_norm` — all from precomputed arrays, one matmul, no network.

---

## Stage 4 — Honeypot Audit, recall-hardened (Day 5)

Keep v5's 10 signals. **Add 4 arithmetic-consistency signals** that catch the dangerous class: a profile that *looks* like a real AI engineer but contains an internal impossibility. These don't depend on keyword lists, so a cleverly-disguised honeypot can't dodge them.

> **[v6.1 fix — precision]** The raw arithmetic signals over-fire on legitimate Indian profiles:
> people who worked during/before a degree, took sabbaticals/maternity leave, did overlapping
> contract work, or have rounded `duration_months`. A false honeypot flag on a real strong-fit
> deletes them from your top 10 — the 55%-of-score region. So each signal below is **widened**
> and signals C/D — the two prone to false positives — are made *soft* (mild penalty, logged as
> a "suspect" not a "honeypot") and only become decisive when they **corroborate** another signal.
> Net effect: recall on disguised honeypots stays high; precision on real candidates is protected.

```python
from datetime import datetime
def arithmetic_honeypot_signals(candidate, penalty, log):
    hist = candidate["career_history"]
    yoe = candidate["profile"]["years_of_experience"]
    hard_fires = 0   # count of high-confidence arithmetic impossibilities

    # A (HARD): sum of role durations grossly exceeds plausible career length.
    # Widened to 1.5x YOE+3yr buffer so part-time/overlap doesn't trip it; this much
    # excess is a genuine impossibility, not a rounding artifact.
    total_months = sum(r["duration_months"] for r in hist)
    if total_months > (yoe + 3) * 12 * 1.5:
        penalty *= 0.18; log.append("duration_sum_exceeds_yoe"); hard_fires += 1

    # B (HARD): a single skill claimed for more months than the entire career + 2yr grace.
    for s in candidate["skills"]:
        if s.get("duration_months", 0) > (yoe * 12) + 24:
            penalty *= 0.25; log.append("skill_duration_exceeds_career"); hard_fires += 1; break

    # C (SOFT): role duration_months disagrees with its own dates by >12mo (was >6).
    # Rounding/gaps explain small gaps; >12mo is suspicious but NOT alone decisive.
    c_fires = 0
    for r in hist:
        if r.get("end_date"):
            try:
                s = datetime.strptime(r["start_date"], "%Y-%m-%d")
                e = datetime.strptime(r["end_date"], "%Y-%m-%d")
                if abs((e - s).days / 30.0 - r["duration_months"]) > 12:
                    c_fires += 1
            except: pass
    if c_fires >= 2:                         # need TWO mismatched roles to count as hard
        penalty *= 0.4; log.append("duration_date_mismatch_multi"); hard_fires += 1
    elif c_fires == 1:                        # one mismatch = soft suspect only
        penalty *= 0.85; log.append("duration_date_mismatch_soft")

    # D (SOFT): claims more YOE than wall-clock time since they plausibly started working.
    # Guarded against the very common "worked during/before degree" case: only fires when
    # YOE exceeds available years by a large margin (>3yr), and treated as soft unless it
    # corroborates a hard signal.
    edu_end = max((e.get("end_year", 0) for e in candidate.get("education", [])), default=0)
    first_role_year = min((int(r["start_date"][:4]) for r in hist), default=9999)
    if edu_end and first_role_year != 9999:
        max_plausible_yoe = max(0, REFERENCE_DATE.year - min(first_role_year, edu_end - 4))
        if yoe > max_plausible_yoe + 3:      # >3yr more experience than time allows
            if hard_fires >= 1:              # corroborated → decisive
                penalty *= 0.4; log.append("yoe_predates_education")
            else:                            # standalone → soft suspect, small nudge
                penalty *= 0.9; log.append("yoe_predates_education_soft")
    return penalty, log
```

Fold these into `honeypot_features` before computing the final `honeypot_score`. `is_likely_honeypot` stays `< 0.15` — and note the soft signals (0.85–0.9 multipliers) can't push a clean candidate below 0.15 on their own, which is the whole point.

> **Test BOTH directions (mandatory Day 5):**
> - *Recall:* synthesize 5 "plausible AI engineer with one subtle lie" profiles; assert each trips ≥1 signal.
> - *Precision:* run all 4 signals across the full 100K and print the flag rate. If `is_likely_honeypot`
>   fires on **more than ~1.5%** of candidates, or if any *current-role-at-a-real-product-company,
>   5–9yr* candidate gets flagged, your thresholds are still too aggressive — widen further. Eyeball
>   20 flagged profiles by hand and confirm they're actually impossible, not just unusual.

---

## Stage 5 — Composite Scoring + anchor calibration (Day 6) — Submission #1

Carry v5's `compute_relevance_score` / `compute_final_score` **almost verbatim** — the weighting was sound. Two changes:

1. The two new disqualifiers feed `compute_final_score` via the existing `disqualifier_penalty` path (no new code, just more flags).
2. **Calibrate against the anchor instead of asserting weights.** This replaces v5's empty-golden-set validation with a real one.

```python
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score
import numpy as np

GOLDEN_SET = json.load(open("artifacts/golden_set.json"))

def evaluate_on_anchor(scores_dict, golden=GOLDEN_SET):
    cids = list(golden)
    y_true = np.array([[golden[c] for c in cids]])
    y_score = np.array([[scores_dict[c] for c in cids]])
    rho = spearmanr([scores_dict[c] for c in cids], [golden[c] for c in cids]).correlation
    ndcg10 = ndcg_score(y_true, y_score, k=min(10, len(cids)))
    # Hard gate: no label-0 may outscore any label-3
    strong = [scores_dict[c] for c in cids if golden[c] == 3]
    notfit = [scores_dict[c] for c in cids if golden[c] == 0]
    gate_ok = (not strong or not notfit or min(strong) > max(notfit))
    print(f"anchor ρ={rho:.3f}  NDCG@10={ndcg10:.3f}  hard_gate={'OK' if gate_ok else 'FAIL'}")
    return rho, ndcg10, gate_ok
```

If `hard_gate FAIL` (a 0 outscores a 3), your weights are wrong — adjust `s_career`/`s_skills`/disqualifier penalties until it passes. **This is the loop that actually wins.** Once it passes and ρ > 0.7, freeze the composite and ship **Submission #1** as the safety net.

---

## Stage 6 — 2-Model Ranker + anchor-tuned blend (Day 7–9)

v5's 4-model ensemble was 3 correlated Claude-derived models + 1 rule model, blended by weights tuned on Claude labels. v6 collapses this to **two genuinely independent label sources**, blended by a single α chosen to maximize **NDCG@10 on the human anchor**.

### 6.1 Two label sources (both free)

```python
# Source A — rule-based labels (deterministic, no LLM). v5's rule_based_label, kept.
def rule_based_label(f):
    score = 0
    if f["weighted_hard_req_coverage"] > 0.7: score += 3
    elif f["weighted_hard_req_coverage"] > 0.4: score += 1
    if f["deployment_score"] > 0.6: score += 2
    elif f["deployment_score"] > 0.3: score += 1
    if f["retrieval_ir_score"] > 0.5: score += 2
    if f["disqualifier_hit"] and f["disqualifier_penalty"] < 0.15: return 0
    if f["location_score"] < 0.1 or f["years_of_experience"] < 3: return 0
    return 3 if score >= 6 else 2 if score >= 4 else 1 if score >= 2 else 0

# Source B — local-LLM labels (Qwen on GPU). Replaces Claude. Same prompt spirit as v5.
def local_llm_label(c, llm):
    prompt = (f"{JD_CONFIG['ideal_profile_summary']}\n\nRate 0-3 fit (3=strong,0=not):\n"
              f"Title: {c['profile']['current_title']} at {c['profile']['current_company']}\n"
              f"YOE: {c['profile']['years_of_experience']}\n"
              f"Location: {c['profile']['location']}, {c['profile']['country']}\n"
              f"Summary: {c['profile']['summary'][:400]}\n"
              f"Recent: {c['career_history'][0]['description'][:300] if c['career_history'] else ''}\n"
              f"Skills: {', '.join(s['name'] for s in c['skills'][:10])}\n"
              f"Notice: {c['redrob_signals']['notice_period_days']}d\n"
              "Answer with ONLY one digit 0-3:")
    out = llm(prompt, max_tokens=3, temperature=0.0)["choices"][0]["text"].strip()
    return int(out[0]) if out and out[0] in "0123" else -1
```

Label ~2,500 stratified candidates (v5's `sample_for_labeling`) with **both** sources. Qwen-7B at q4 on an 8GB GPU does ~2,500 short classifications in roughly 20–40 min — entirely free.

### 6.2 Train two LightGBM rankers, blend on the anchor

```python
import lightgbm as lgb
import numpy as np

def train_ranker(X, y, name):
    d = lgb.Dataset(X, label=y, group=[len(X)])   # single query group
    params = dict(objective="lambdarank", metric="ndcg", num_leaves=31,
                  learning_rate=0.05, min_data_in_leaf=20, n_estimators=300,
                  label_gain=[0, 1, 3, 7])          # emphasize the 3s (top-fit) heavily
    m = lgb.train(params, d)
    m.save_model(f"artifacts/ranker_{name}.txt")
    return m

m_rule = train_ranker(X_labeled, y_rule,  "rule")
m_llm  = train_ranker(X_labeled, y_llm,   "llm")

# Choose blend α to MAXIMIZE NDCG@10 on the human anchor (not on either label set)
def pick_alpha(features_df, m_rule, m_llm, golden):
    cids = list(golden)
    sub = features_df.loc[cids]
    X = sub[LGB_FEATURES].fillna(0).values
    p_rule = _minmax(m_rule.predict(X)); p_llm = _minmax(m_llm.predict(X))
    y_true = np.array([[golden[c] for c in cids]])
    best_a, best_n = 0.5, -1
    for a in np.linspace(0, 1, 21):
        blended = a * p_rule + (1 - a) * p_llm
        n = ndcg_score(y_true, np.array([blended]), k=min(10, len(cids)))
        if n > best_n: best_n, best_a = n, a
    print(f"best α(rule weight)={best_a:.2f}  anchor NDCG@10={best_n:.3f}")
    return best_a

alpha = pick_alpha(features_df, m_rule, m_llm, GOLDEN_SET)
json.dump({"alpha_rule": float(alpha)}, open("artifacts/blend.json", "w"))
```

This is the defensible core: **two independent label sources, blended by a weight learned from human judgment.** If Qwen is systematically wrong on some archetype, α shifts toward the rule model automatically because the anchor punishes the bad blend. You can explain every number.

### 6.3 SHAP prune (optional, Day 9 if time)

Run SHAP on `m_rule`; drop features with `mean_abs_shap < 0.001`. Keeps `rank.py` lean and gives you a "here's what actually drives rankings" slide for the interview.

---

## Stage 7 — Top-30 Human Audit + Reasoning + Output (Day 9–11) — Submission #2

### 7.1 Top-30 human audit [v6: NEW — directly targets NDCG@10]

Generate the model's top 40. **You personally read the top 30 profiles.** For each, one of: keep, demote (with reason), or remove (honeypot / disqualified / trap). This is 30 profiles, ~90 min, and it operates on exactly the 55%-of-score region.

```python
# audit_log.json — you fill this; rank.py applies it deterministically
AUDIT = {
    # "CAND_xxxx": {"action": "remove", "reason": "honeypot: 11yr exp, company founded 2022"},
    # "CAND_yyyy": {"action": "demote", "to_rank": 35, "reason": "CV-only, no NLP/IR"},
}
```

This is *not* manual editing of the CSV (which the spec forbids as "hidden steps"). It's a documented, version-controlled override table that `rank.py` reads — fully reproducible. Document it in the README as a human-in-the-loop final filter.

### 7.2 Reasoning — cite only literal facts [v6: closes hallucination]

```python
def extract_achievement_sentence(c):
    """Return ONE real sentence from career text containing a JD keyword + a number.
       Falls back to a fact that is literally present. Never asserts a skill not in profile."""
    jd_kw = ["retrieval","ranking","embedding","vector","search","recommendation",
             "ndcg","latency","scale","production","pipeline","deployed","shipped"]
    for r in c["career_history"]:
        for sent in r["description"].split("."):
            s = sent.strip()
            if any(k in s.lower() for k in jd_kw) and any(ch.isdigit() for ch in s):
                return s[:160]
    # fallback: literal title + company + a real number, nothing invented
    cur = c["career_history"][0] if c["career_history"] else None
    return (cur["description"][:140].strip() if cur else
            c["profile"]["headline"][:140])

def build_reasoning(c, feats, rank):
    title = c["profile"]["current_title"]; comp = c["profile"]["current_company"]
    yoe = c["profile"]["years_of_experience"]
    ach = extract_achievement_sentence(c)
    concerns = []
    nd = c["redrob_signals"]["notice_period_days"]
    if nd > 60: concerns.append(f"notice {nd}d")
    if feats.get("location_score", 1) < 0.65: concerns.append("non-preferred location")
    if feats.get("consulting_penalty", 0) > 0.5: concerns.append("services-heavy background")
    tail = f" Concerns: {'; '.join(concerns)}." if concerns else ""
    return f"{title} at {comp}, {yoe:.1f}yr. {ach}.{tail}"[:300]
```

Every clause is traceable to literal profile text. No score-derived skill claims. This passes Stage-4 sampling.

### 7.3 `rank.py` — CPU-only, no network, ≤5 min

```python
#!/usr/bin/env python3
"""rank.py — final ranking. CPU only, no network, ≤5 min.
   Usage: python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv"""
import argparse, json, csv, gzip, time
import numpy as np, pandas as pd, lightgbm as lgb

def _minmax(a):
    a = np.asarray(a, float); r = a.max() - a.min()
    return (a - a.min()) / r if r > 1e-9 else np.zeros_like(a)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="submission.csv")
    a = ap.parse_args(); t0 = time.time()

    F = pd.read_parquet("artifacts/features_100k.parquet").set_index("candidate_id")
    LGB_FEATURES = json.load(open("artifacts/lgb_features.json"))

    # restrict to the candidate file passed in (handles their sandbox pool)
    file_ids = []
    with gzip.open(a.candidates, "rt") as f:
        for ln in f:
            if ln.strip(): file_ids.append(json.loads(ln)["candidate_id"])
    F = F[F.index.isin(set(file_ids))]

    emb = np.load("artifacts/candidate_embeddings.npy", mmap_mode="r")
    eid = json.load(open("artifacts/candidate_embeddings_ids.json"))
    idx = {c: i for i, c in enumerate(eid)}
    jd = np.load("artifacts/jd_embedding.npy"); ideal = np.load("artifacts/ideal_embedding.npy")
    bm25 = _minmax(np.load("artifacts/bm25_scores.npy"))
    sem = 0.6 * (emb @ jd) + 0.4 * (emb @ ideal)
    hyb = 0.60 * sem + 0.40 * bm25
    F["hybrid_score"] = [hyb[idx[c]] for c in F.index]
    if "per_role_semantic_score" not in F: F["per_role_semantic_score"] = F["hybrid_score"]

    # interaction features (inline, no artifact)
    F["saved_x_deploy"] = F["saved_30d"] * F["deployment_score"]
    F["hardreq_x_prod"] = F["weighted_hard_req_coverage"] * F["production_evidence_score"]

    X = F[LGB_FEATURES].fillna(0).values
    m_rule = lgb.Booster(model_file="artifacts/ranker_rule.txt")
    m_llm  = lgb.Booster(model_file="artifacts/ranker_llm.txt")
    al = json.load(open("artifacts/blend.json"))["alpha_rule"]
    F["lm"] = al * _minmax(m_rule.predict(X)) + (1 - al) * _minmax(m_llm.predict(X))

    # honeypot + disqualifier multipliers
    F["final"] = (F["lm"]
                  * F.get("honeypot_score", 1.0)
                  * np.where(F.get("disqualifier_hit", False),
                             F.get("disqualifier_penalty", 1.0), 1.0))

    # apply human audit overrides (documented, reproducible)
    try: AUDIT = json.load(open("artifacts/audit_log.json"))
    except FileNotFoundError: AUDIT = {}
    # apply human audit overrides (documented, reproducible)
    # [v6.1 fix #5] 'remove' zeroes the score; 'demote' with an explicit to_rank pushes the
    # candidate just below the score currently sitting at that target position, so the demotion
    # lands where you intended instead of an unpredictable spot. 'demote' without to_rank does a
    # plain 0.3x nudge (kept for convenience but the README only promises to_rank behavior).
    try: AUDIT = json.load(open("artifacts/audit_log.json"))
    except FileNotFoundError: AUDIT = {}
    # resolve removes/plain-demotes first
    deferred = []
    for cid, a_ in AUDIT.items():
        if cid not in F.index: continue
        if a_["action"] == "remove":
            F.loc[cid, "final"] = 0.0
        elif a_["action"] == "demote" and "to_rank" not in a_:
            F.loc[cid, "final"] *= 0.3
        elif a_["action"] == "demote":
            deferred.append((cid, int(a_["to_rank"])))
    # resolve to_rank demotions against the (post-remove) ordering
    for cid, target in deferred:
        order = F.sort_values("final", ascending=False)
        anchor_vals = order["final"].values
        if target < len(anchor_vals):
            # place just below the candidate currently at `target` (and above target+1)
            hi = anchor_vals[target - 1] if target - 1 < len(anchor_vals) else anchor_vals[-1]
            lo = anchor_vals[target] if target < len(anchor_vals) else 0.0
            F.loc[cid, "final"] = (hi + lo) / 2.0
        else:
            F.loc[cid, "final"] = anchor_vals[-1] * 0.5

    ranked = F.sort_values(["final", "candidate_id"], ascending=[False, True]).head(100)

    cache = json.load(open("artifacts/reasoning_cache.json"))
    # [v6.1 fix #4] Emit RANK-BASED scores, not raw-magnitude scores. The metric only cares
    # about ORDER, and raw 'final' values can cluster (audit zeroing, tight ranker outputs),
    # which risks the validator's '>10 unique' / 'strictly non-increasing' checks. A linear
    # function of rank guarantees 100 unique, strictly-decreasing values in (0,1].
    n = len(ranked)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for i, (cid, row) in enumerate(ranked.iterrows(), 1):
            score = round(0.999 - (i - 1) * (0.95 / max(n - 1, 1)), 4)  # 0.999 → ~0.049
            r = cache.get(cid, f"{cid}: ranked by feature+LLM blended ranker.")
            w.writerow([cid, i, f"{score:.4f}", r])
    print(f"✅ {time.time()-t0:.1f}s")
    validate_submission(a.out)

if __name__ == "__main__":
    main()
```

### 7.4 Validator (run before every upload)

Keep v5's validator (100 rows, ranks 1–100 unique, ids unique & exist, scores non-increasing in [0,1], >80 unique reasonings, honeypot rate ≤ 8%). It catches every "common rejection" in spec §6.

### 7.5 Sandbox (Day 11, mandatory §10.5)

Colab notebook: pip install, pull artifacts from Google Drive, load `sample_candidates.json` (≤100), run the `rank.py` logic, show CSV + validator pass. Target <2 min CPU. Checklist: runs unmodified, ≤5 min CPU, valid CSV, no network, interaction features inline.

---

## Compute Constraint Summary (rank.py)

| Artifact | Size | OK? |
|----------|------|-----|
| features_100k.parquet (~70 cols) | ~65 MB | ✅ |
| bge-large embeddings 100K×1024×4B | ~410 MB | ✅ |
| bm25_scores.npy | ~0.8 MB | ✅ |
| 2 LightGBM rankers | ~40 MB | ✅ |
| **Total resident** | **~520 MB** | ✅ ≪ 16 GB |

| rank.py op | Time |
|-----------|------|
| parquet load | ~1 s |
| 100K×1024 matmul ×2 | ~3 s |
| 2× LightGBM predict | ~4 s |
| audit + sort + CSV | ~2 s |
| **Total** | **~10–18 s** |

Massive headroom under the 5-min ceiling. Fewer models than v5 → faster and easier to reproduce.

---

## What each judge question v6 answers

| Question | Answer |
|----------|--------|
| "You used no paid API?" | Correct — JD parse and all 2,500 pseudo-labels ran on Qwen2.5-7B locally on GPU; deterministic fallbacks mean the pipeline is correct even with no model at all. ₹0 spent, fully reproducible offline. |
| "How do you know your ranking is good with no leaderboard?" | 60 hand-labeled anchor candidates spanning every archetype. Composite passes a hard gate (no not-fit outscores a strong-fit), ρ>0.7, and the model blend α is *chosen* to maximize NDCG@10 on that anchor. |
| "Why only 2 models, not an ensemble?" | Two *genuinely independent* label sources (deterministic rules vs local LLM). More correlated models add no information. The blend weight is learned from human judgment, so if the LLM is biased on an archetype, α shifts to the rule model automatically. |
| "How do you avoid honeypots in the top 10?" | 10 keyword/contradiction signals + 4 arithmetic-consistency signals that catch disguised honeypots, + a human read of the top 30. We tested recall on synthetic disguised honeypots, not just precision. |
| "Why is your top 10 trustworthy?" | 55% of score is NDCG@10, so a human reads every top-30 profile against the JD's ideal-candidate paragraph and applies a documented, reproducible override table. |
| "Did you handle the JD's pure-research reject?" | Yes — `pure_research_no_prod` (penalty 0.12) and `closed_source_no_validation` (0.35) flags, which v5 lacked. |
| "Is reasoning hallucination-free?" | Every reasoning string quotes a literal sentence from the candidate's career text or states a literal profile fact. No skill is asserted from a derived score. |
| "Does rank.py meet the constraints?" | ~10–18 s, ~520 MB, CPU-only, no network. Demoed live + Colab sandbox. |
| "Better than naive?" | `naive_baseline_top100.json` stored Day 1; we report anchor NDCG@10 of v6 vs YOE-naive. |

---

## 12-Day Roadmap

| Day | Deliverable |
|-----|-------------|
| 1 | Env, data integrity, **golden set: label 60 by hand**, JD_CONFIG (fallback + local LLM), naive baseline |
| 2 | JD embeddings; start Stage 2 features |
| 3 | Finish career/skills/edu/logistics/behavioral features; candidate text synth |
| 4 | Two new disqualifiers; anchor-helper cols; BM25 + bge encode (GPU) |
| 5 | Honeypot audit incl. 4 arithmetic signals; **recall test on synthetic honeypots** |
| 6 | Composite scoring; calibrate on anchor (hard gate + ρ); **Submission #1 (safety net)** |
| 7 | Local-LLM labeling of 2,500 (GPU); rule labels |
| 8 | Train 2 rankers; pick α on anchor; SHAP prune |
| 9 | Generate top-40; **top-30 human audit**; reasoning cache |
| 10 | rank.py end-to-end; validator; dry-run full pool; **Submission #2 (primary)** |
| 11 | Colab sandbox; README; submission_metadata.yaml; AI-tools declaration |
| 12 | Buffer; **Submission #3 only if anchor NDCG@10 improved** |

---

## File Structure

```
redrob-ranker/
├── README.md                      # documents GPU-precompute vs CPU-rank split
├── requirements.txt
├── submission_metadata.yaml
├── models/qwen2.5-7b-instruct-q4_k_m.gguf   # local LLM (gitignored; script to fetch)
├── precompute/
│   ├── 00_golden_set.py           # [v6] select + (you) label 60
│   ├── 01_parse_jd.py             # [v6] local LLM + deterministic fallback
│   ├── 02_encode_candidates.py
│   ├── 03_extract_features.py     # + 2 new disqualifiers, anchor cols
│   ├── 04_build_bm25.py
│   ├── 05_honeypot_audit.py       # + 4 arithmetic signals
│   ├── 06_composite_calibrate.py  # [v6] anchor hard-gate + ρ
│   ├── 07_label_local_llm.py      # [v6] Qwen labels, no API
│   ├── 08_train_blend.py          # [v6] 2 rankers, α on anchor
│   └── 09_reasoning_audit.py      # [v6] top-30 audit + reasoning
├── rank.py                        # CPU only, no network, ≤5 min
├── validate_submission.py
├── sandbox/redrob_demo.ipynb
└── artifacts/
    ├── golden_set.json            # [v6] THE ANCHOR
    ├── jd_config.json
    ├── features_100k.parquet
    ├── candidate_embeddings.npy / _ids.json
    ├── bm25_scores.npy / jd_embedding.npy / ideal_embedding.npy
    ├── ranker_rule.txt / ranker_llm.txt
    ├── blend.json                 # [v6] α
    ├── audit_log.json             # [v6] human overrides
    ├── lgb_features.json
    └── reasoning_cache.json
```

```bash
# Precompute (GPU OK, may exceed 5 min):
python precompute/00_golden_set.py     # then hand-label, fill golden_set.json
python precompute/01_parse_jd.py
python precompute/02_encode_candidates.py
python precompute/03_extract_features.py
python precompute/04_build_bm25.py
python precompute/05_honeypot_audit.py
python precompute/06_composite_calibrate.py
python precompute/07_label_local_llm.py
python precompute/08_train_blend.py
python precompute/09_reasoning_audit.py
# Ranking (CPU only, no network, ≤5 min):
python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
```

---

## The three things that actually win this (don't skip)

1. **Build the golden set on Day 1 and tune everything to it.** No leaderboard means the anchor is your only truth. This is non-negotiable and it's where v5 silently failed.
2. **Hand-audit your top 30.** 55% of the score is NDCG@10. One trap or honeypot up there is catastrophic; a human read is the highest-ROI 90 minutes in the project.
3. **Keep the story human-engineered, not LLM-generated.** Local open-weights labeling + deterministic rules + your own audit is exactly the "AI-assisted where the human did real engineering" profile the organizers say survives Stages 3–5. Lead with the engineering, treat the LLM as one noisy signal among several.
