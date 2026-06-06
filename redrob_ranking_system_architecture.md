# Redrob AI — Intelligent Candidate Ranking System
## Full Architecture Breakdown (15-Day Build Plan)

---

## Overview

**Mission:** Given a job description (JD), rank 100 best-fit candidates from a 100K pool — the way a *senior technical recruiter with ML intuition* would, not the way a keyword search engine would.

**Core constraints from the spec:**
- Ranking step must run in ≤5 min on a 16 GB CPU-only machine (no GPU, no hosted LLM APIs during ranking)
- Pre-computation (embeddings, indexes) can be done offline upfront
- Output: `candidate_id, rank, score, reasoning` CSV with exactly 100 rows
- Metric: `0.50 × NDCG@10 + 0.30 × NDCG@50 + 0.15 × MAP + 0.05 × P@10`
- Honeypot detection: profiles with impossible/inconsistent data must be caught and buried

**Key insight from the JD:** The job description explicitly warns against keyword matching. The system must:
1. Understand *what the JD means* (e.g., "product-company AI engineer" → career trajectory signal, not just skill keywords)
2. Use behavioral signals as a multiplier (an inactive candidate is not a real candidate)
3. Detect and penalize honeypots (impossible profiles, pure keyword stuffers)

---

## System Architecture: 6 Stages

```
Stage 1: JD Intelligence Layer         (Days 1–2)
Stage 2: Candidate Feature Engineering (Days 3–5)
Stage 3: Semantic Embedding Index      (Days 4–6)
Stage 4: Multi-Signal Scoring Engine   (Days 6–9)
Stage 5: Behavioral Multiplier + Honeypot Filter (Days 9–11)
Stage 6: LambdaMART Re-Ranker + Output (Days 11–15)
```

---

## Stage 1: JD Intelligence Layer
**Days 1–2 | Goal: Extract structured meaning from the JD, not keywords**

### What to do

The JD is not a keyword list. It contains:
- Explicit requirements ("must have"), soft preferences ("nice to have"), disqualifiers ("explicitly do NOT want")
- Implied signals ("product company experience" > consulting background)
- Logistical constraints (location, notice period, salary band)
- Cultural/behavioral signals (startup-ready, ships fast, writes well)

**Step 1.1 — Offline LLM-Powered JD Parsing (pre-computation, allowed)**

Use Claude/GPT-4 *once* offline to parse the JD into a structured JSON schema:

```json
{
  "role_title": "Senior AI Engineer",
  "experience_range": {"min": 5, "max": 9},
  "hard_requirements": [
    "production embeddings-based retrieval systems",
    "vector databases or hybrid search (Pinecone/Weaviate/Qdrant/Milvus/FAISS)",
    "strong Python",
    "evaluation frameworks for ranking (NDCG/MRR/MAP)"
  ],
  "soft_requirements": [
    "LLM fine-tuning (LoRA/QLoRA/PEFT)",
    "learning-to-rank (XGBoost/neural)",
    "HR-tech/marketplace experience",
    "distributed systems / large-scale inference"
  ],
  "disqualifiers": [
    "pure research background without production deployment",
    "AI experience = only LangChain tutorials <12 months",
    "tech lead who hasn't coded in 18 months",
    "only consulting firms (TCS/Infosys/Wipro/Accenture/Cognizant/Capgemini) career",
    "CV/speech/robotics without NLP/IR exposure",
    "closed-source only without external validation"
  ],
  "preferred_location": ["Pune", "Noida", "Hyderabad", "Mumbai", "Delhi NCR"],
  "preferred_notice_days": {"ideal": 30, "acceptable": 90, "max": 180},
  "ideal_profile_narrative": "6-8 years, 4-5 applied ML at product companies, shipped search/ranking/rec system to real users at scale",
  "salary_band_inr_lpa": {"min": 30, "max": 70},
  "culture_signals": ["startup_ready", "ships_fast", "writes_well", "no_title_chasing"],
  "must_be_active": true
}
```

**Step 1.2 — Skill Taxonomy Expansion**

Don't just match "Pinecone" in skills. Build a skill synonym/hierarchy map:

```python
SKILL_GROUPS = {
    "vector_search": ["pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch", 
                      "elasticsearch", "pgvector", "chromadb", "annoy"],
    "embedding_models": ["sentence-transformers", "bge", "e5", "openai embeddings", 
                         "ada", "instructor", "gte", "clip"],
    "ranking_eval": ["ndcg", "mrr", "map", "a/b testing", "online eval", "learning to rank", 
                     "xgboost ranker", "listwise", "pairwise"],
    "llm_finetune": ["lora", "qlora", "peft", "rlhf", "sft", "instruction tuning", 
                     "flan", "alpaca", "dpo"],
    "product_infra": ["rag", "hybrid retrieval", "bm25", "reranking", "dense retrieval"],
    "consulting_firms": ["tcs", "infosys", "wipro", "accenture", "cognizant", 
                         "capgemini", "mphasis", "tech mahindra"]
}
```

This means a candidate with "FAISS" in their career history description gets `vector_search` credit even if "Pinecone" isn't in their skills list.

**Step 1.3 — JD Embedding (offline, once)**

Generate a high-quality embedding of the full JD narrative + the "ideal candidate" paragraph using a powerful sentence-transformer (e.g., `BAAI/bge-large-en-v1.5` or `intfloat/e5-large-v2`). Store this for Stage 3.

### Correctness Check

- Manually verify the parsed JSON against the raw JD. Do all 4 hard requirements appear? Are all 6 disqualifier types captured?
- Run the skill expansion on 10 known-good and 10 known-bad candidates manually; verify groupings make sense.
- Unit test: assert that "FAISS" → `vector_search = True`, "Wipro only career" → `consulting_firm_flag = True`.

---

## Stage 2: Candidate Feature Engineering
**Days 3–5 | Goal: Convert every candidate profile into a structured, normalized feature vector**

### What to do

For each of the 100K candidates, compute a deterministic feature vector. This runs *offline* and is stored on disk. The online ranking step simply loads precomputed features and scores them.

**2.1 — Career Quality Features**

```python
def career_features(candidate):
    history = candidate["career_history"]
    
    # Product company vs consulting ratio
    consulting_months = sum(
        r["duration_months"] for r in history 
        if any(f in r["company"].lower() for f in CONSULTING_FIRMS)
    )
    total_months = sum(r["duration_months"] for r in history)
    consulting_ratio = consulting_months / max(total_months, 1)
    
    # Title progression signal (are they climbing or stagnant?)
    titles = [r["title"].lower() for r in sorted(history, key=lambda x: x["start_date"])]
    seniority_trend = compute_seniority_trend(titles)  # +1=growing, 0=flat, -1=declining
    
    # Job hopping signal: number of jobs <18 months in last 8 years
    short_stints = sum(1 for r in history if r["duration_months"] < 18)
    
    # Production AI deployment signal: scan descriptions for deployment keywords
    deploy_keywords = ["shipped", "deployed", "production", "real users", "at scale", 
                       "serving", "inference", "latency", "throughput", "A/B"]
    deployment_score = sum(
        1 for r in history 
        for kw in deploy_keywords 
        if kw in r["description"].lower()
    ) / len(history)
    
    return {
        "consulting_ratio": consulting_ratio,
        "seniority_trend": seniority_trend,
        "short_stint_count": short_stints,
        "deployment_score": deployment_score,
        "years_in_product_companies": (total_months - consulting_months) / 12,
        "current_company_size_score": SIZE_MAP[candidate["profile"]["current_company_size"]]
    }
```

**2.2 — Skills Match Features**

```python
def skills_features(candidate, jd_parsed):
    skills_lower = {s["name"].lower(): s for s in candidate["skills"]}
    
    # Hard requirement coverage (0-4)
    hard_hits = 0
    for req_group in jd_parsed["hard_requirements_groups"]:  # e.g., ["vector_search"]
        if any(skill in SKILL_GROUPS[req_group] for skill in skills_lower):
            hard_hits += 1
    
    # Skill depth: weighted by proficiency and endorsements
    def skill_weight(skill):
        prof_map = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.85, "expert": 1.0}
        endorsement_bonus = min(skill["endorsements"] / 50, 0.15)
        duration_bonus = min(skill.get("duration_months", 0) / 48, 0.15)
        return prof_map[skill["proficiency"]] + endorsement_bonus + duration_bonus
    
    # Assessment score alignment (when available)
    assessment_scores = candidate["redrob_signals"].get("skill_assessment_scores", {})
    avg_assessment = (
        sum(assessment_scores.values()) / len(assessment_scores) 
        if assessment_scores else 50  # neutral if no assessments
    )
    
    return {
        "hard_req_coverage": hard_hits / 4,
        "avg_skill_depth": sum(skill_weight(s) for s in candidate["skills"]) / max(len(candidate["skills"]), 1),
        "soft_req_coverage": ...,  # similar to hard_hits
        "disqualifier_flags": compute_disqualifiers(candidate, jd_parsed),
        "avg_assessment_score": avg_assessment / 100
    }
```

**2.3 — Education Features**

```python
TIER_SCORE = {"tier_1": 1.0, "tier_2": 0.8, "tier_3": 0.6, "tier_4": 0.4, "unknown": 0.5}

def education_features(candidate):
    edu = candidate["education"]
    if not edu: return {"edu_tier": 0.4, "is_cs_adjacent": False}
    
    best = max(edu, key=lambda e: TIER_SCORE.get(e.get("tier", "unknown"), 0.5))
    cs_fields = ["computer science", "information technology", "electrical engineering", 
                 "mathematics", "statistics", "data science", "ai", "machine learning"]
    is_cs = any(f in best["field_of_study"].lower() for f in cs_fields)
    
    return {
        "edu_tier_score": TIER_SCORE.get(best.get("tier", "unknown"), 0.5),
        "is_cs_adjacent": is_cs
    }
```

**2.4 — Logistics Fit Features**

```python
def logistics_features(candidate, jd_parsed):
    loc = candidate["profile"]["location"].lower()
    country = candidate["profile"]["country"].lower()
    preferred_locs = [l.lower() for l in jd_parsed["preferred_location"]]
    
    location_score = 1.0 if any(pl in loc for pl in preferred_locs) else (
        0.6 if country == "india" and candidate["redrob_signals"]["willing_to_relocate"] else 0.2
    )
    
    notice = candidate["redrob_signals"]["notice_period_days"]
    notice_score = 1.0 if notice <= 30 else (0.7 if notice <= 60 else (0.4 if notice <= 90 else 0.1))
    
    salary = candidate["redrob_signals"]["expected_salary_range_inr_lpa"]
    jd_sal = jd_parsed["salary_band_inr_lpa"]
    salary_overlap = compute_range_overlap(salary, jd_sal)
    
    return {
        "location_score": location_score,
        "notice_score": notice_score,
        "salary_fit": salary_overlap
    }
```

### Correctness Check

- For each feature, assert the full range is used (not all candidates scoring in 0.4–0.6)
- Check that CAND_0000002 (Operations Manager at Wipro) scores `consulting_ratio ≈ 1.0` and `hard_req_coverage = 0`
- Check that a candidate with FAISS + RAG + NDCG + Python gets `hard_req_coverage = 1.0`
- Spot-check 20 candidates manually, compute features by hand, diff with code output — zero tolerance for off-by-one errors on categorical mappings

---

## Stage 3: Semantic Embedding Index
**Days 4–6 | Goal: Semantic similarity beyond keywords using dense retrieval**

### What to do

Keywords miss context. A candidate who "built a hybrid BM25 + dense retrieval system for a marketplace" is a perfect fit even if they never wrote the word "RAG" in their profile.

**3.1 — Candidate Text Synthesis**

For each candidate, synthesize a rich text blob combining all narrative fields:

```python
def synthesize_candidate_text(c):
    parts = [
        c["profile"]["headline"],
        c["profile"]["summary"],
        *[r["description"] for r in c["career_history"]],
        " ".join(f"{s['name']} ({s['proficiency']})" for s in c["skills"]),
        *[f"{e['degree']} in {e['field_of_study']} from {e['institution']}" 
          for e in c["education"]],
        *[cert["name"] for cert in c.get("certifications", [])]
    ]
    return " ".join(parts)
```

**3.2 — Embedding Model Choice**

Use `BAAI/bge-large-en-v1.5` (best retrieval model as of 2024, MTEB Retrieval top performer). This model is ~1.3 GB, runs on CPU, and produces 1024-dim embeddings.

- Batch all 100K candidates through the model offline (will take ~2-4 hours on CPU, but this is pre-computation)
- Store embeddings as a `numpy` memmap or `numpy.save` (.npy) for fast loading

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-large-en-v1.5")
texts = [synthesize_candidate_text(c) for c in candidates]
embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
np.save("candidate_embeddings.npy", embeddings)
```

**3.3 — JD Query Embedding**

Embed the JD with the same model (using BGE's query prefix: `"Represent this sentence for searching relevant passages: "`). Compute cosine similarity against all 100K candidates → `semantic_similarity_score` per candidate.

**3.4 — Career History Per-Role Embeddings (optional, high value)**

Embed each *career role description* individually and max-pool across roles. This captures candidates who had one stellar relevant role even if other roles are unrelated.

```python
def max_pool_career_similarity(candidate, jd_embedding, model):
    role_texts = [r["description"] for r in candidate["career_history"]]
    role_embeddings = model.encode(role_texts, normalize_embeddings=True)
    sims = role_embeddings @ jd_embedding
    return float(np.max(sims))  # best role match
```

### Correctness Check

- Run cosine similarity between the JD embedding and 5 manually-identified "clearly good" candidates vs 5 "clearly bad" ones; good candidates should all score > 0.55, bad ones < 0.35
- Sanity check: verify the embedding for "FAISS for vector search" and "Pinecone for ANN retrieval" are cosine-similar (≥ 0.7)
- Timing benchmark: loading the .npy and doing 100K dot products must complete in < 5 seconds

---

## Stage 4: Multi-Signal Scoring Engine
**Days 6–9 | Goal: Combine all feature signals into a single composite relevance score**

### What to do

This is the core scoring function. It should *not* be a simple weighted sum — weighted sums are gameable. Instead, use a scoring strategy that mirrors how a good recruiter actually thinks:

**4.1 — Disqualifier Gates (hard filters applied first)**

Before scoring, apply binary disqualifiers. Any candidate that hits one of these is capped at a maximum score of 0.15 (still ranked but at the bottom):

```python
DISQUALIFIERS = [
    lambda c, f: f["consulting_ratio"] > 0.95,  # entire career at consulting firms
    lambda c, f: f["hard_req_coverage"] < 0.25,  # hits 0 of 4 hard requirements
    lambda c, f: c["profile"]["years_of_experience"] < 3,  # too junior
    lambda c, f: f["is_pure_research"],  # no production deployment evidence
    lambda c, f: f["location_score"] < 0.2 and not c["redrob_signals"]["willing_to_relocate"],
]

def apply_disqualifiers(candidate, features):
    return any(d(candidate, features) for d in DISQUALIFIERS)
```

**4.2 — Component Score Computation**

```
S_semantic    = cosine_similarity(jd_embedding, candidate_embedding)          [0, 1]
S_career      = f(consulting_ratio, seniority_trend, deployment_score, ...)   [0, 1]
S_skills      = f(hard_req_coverage, skill_depth, assessments, ...)           [0, 1]
S_logistics   = f(location, notice_period, salary_overlap)                    [0, 1]
S_education   = f(edu_tier, cs_field)                                          [0, 1]
```

**4.3 — Composite Relevance Score**

Weights informed by the JD emphasis (hard requirements > location > education):

```python
def compute_relevance_score(features, semantic_score):
    # Semantic similarity: captures narrative intent beyond keywords
    s_semantic = semantic_score                                          # 0.25 weight
    
    # Career trajectory: the JD cares deeply about "product company, shipped to users"
    s_career = (
        0.4 * (1 - features["consulting_ratio"]) +
        0.3 * features["deployment_score"] +
        0.2 * max(0, features["years_in_product_companies"] / 8) +
        0.1 * (features["seniority_trend"] + 1) / 2
    )                                                                    # 0.30 weight
    
    # Skills: hard reqs are make-or-break
    s_skills = (
        0.6 * features["hard_req_coverage"] +                           # hard reqs dominate
        0.25 * features["soft_req_coverage"] +
        0.15 * features["avg_skill_depth"]
    )                                                                    # 0.25 weight
    
    # Logistics: location + notice + salary
    s_logistics = (
        0.5 * features["location_score"] +
        0.3 * features["notice_score"] +
        0.2 * features["salary_fit"]
    )                                                                    # 0.10 weight
    
    # Education: minor factor
    s_edu = (
        0.7 * features["edu_tier_score"] +
        0.3 * float(features["is_cs_adjacent"])
    )                                                                    # 0.10 weight
    
    composite = (
        0.25 * s_semantic +
        0.30 * s_career +
        0.25 * s_skills +
        0.10 * s_logistics +
        0.10 * s_edu
    )
    return composite
```

**4.4 — Experience Band Penalty**

The JD says 5-9 years with nuance. Apply a soft penalty:

```python
def experience_modifier(years):
    if 5 <= years <= 9: return 1.0
    if 4 <= years < 5:  return 0.9   # slightly junior
    if 9 < years <= 12: return 0.95  # slight over-experience
    if 3 <= years < 4:  return 0.7   # too junior
    if years > 12:      return 0.85  # likely wants different role
    return 0.5
```

### Correctness Check

- Build a "golden set" of 20 candidates (10 clearly good, 10 clearly bad) by manually reading their full profiles with the JD in mind. Score them through the system. All 10 "good" should outscore all 10 "bad."
- Plot the distribution of composite scores across all 100K — should be a right-skewed distribution, not a uniform one
- Verify that CAND_0000001 (Backend Engineer, mostly data engineering, some ML, Toronto) scores notably lower than a hypothetical candidate with "shipped FAISS-based ranker at product company in Noida"
- Check that salary/location features have meaningful variance (if 90% of candidates score 0.5 on location, the feature is miscalibrated)

---

## Stage 5: Behavioral Multiplier + Honeypot Filter
**Days 9–11 | Goal: Adjust relevance by real-world availability & weed out fake profiles**

This stage is what separates a search engine from a recruiter.

### What to do

**5.1 — Behavioral Availability Score**

```python
from datetime import date

REFERENCE_DATE = date(2026, 6, 6)  # today

def behavioral_score(signals):
    s = signals
    
    # Recency: days since last active
    last_active = date.fromisoformat(s["last_active_date"])
    days_inactive = (REFERENCE_DATE - last_active).days
    recency = max(0, 1 - days_inactive / 180)  # 0 at 6 months inactive, 1 if active today
    
    # Responsiveness
    response_rate = s["recruiter_response_rate"]   # 0-1
    response_time = max(0, 1 - s["avg_response_time_hours"] / 168)  # 1 week = worst
    responsiveness = 0.6 * response_rate + 0.4 * response_time
    
    # Hiring intent signals
    intent = (
        0.4 * float(s["open_to_work_flag"]) +
        0.3 * min(s["applications_submitted_30d"] / 5, 1.0) +
        0.3 * min(s["saved_by_recruiters_30d"] / 10, 1.0)
    )
    
    # Engagement quality
    engagement = (
        0.5 * s["interview_completion_rate"] +
        0.5 * max(0, s["offer_acceptance_rate"])  # -1 = no history → 0
    )
    
    # Platform credibility
    credibility = (
        0.4 * float(s["verified_email"]) +
        0.3 * float(s["verified_phone"]) +
        0.2 * (s["profile_completeness_score"] / 100) +
        0.1 * float(s["linkedin_connected"])
    )
    
    behavioral = (
        0.30 * recency +
        0.25 * responsiveness +
        0.20 * intent +
        0.15 * engagement +
        0.10 * credibility
    )
    return behavioral
```

**5.2 — Apply Behavioral Multiplier**

The behavioral score is a *multiplier* on the relevance score, not an additive factor. This prevents a perfectly relevant but inactive candidate from beating a slightly-less-relevant but actively-looking candidate:

```python
def final_score(relevance_score, behavioral_score):
    # Behavioral acts as a multiplier: range [0.3, 1.0]
    # Even a totally inactive candidate isn't zeroed out (may still be recruitable)
    behavioral_multiplier = 0.3 + 0.7 * behavioral_score
    return relevance_score * behavioral_multiplier
```

**5.3 — Honeypot Detection**

The spec explicitly warns about ~80 honeypots with impossible profiles. These are caught by consistency checks:

```python
def honeypot_score(candidate):
    """Returns a penalty factor: 1.0 = clean, 0.0 = definitely honeypot"""
    penalties = []
    
    # Check 1: Work duration at a company that was founded later
    # (We don't have founding dates, so we use a heuristic: if duration > experience_years * 12 + 6)
    for role in candidate["career_history"]:
        if role["duration_months"] > candidate["profile"]["years_of_experience"] * 12 + 6:
            penalties.append(0.0)
    
    # Check 2: Expert proficiency in many skills with 0 months used
    zero_duration_experts = sum(
        1 for s in candidate["skills"]
        if s["proficiency"] == "expert" and s.get("duration_months", 0) == 0
    )
    if zero_duration_experts >= 3:
        penalties.append(0.0)
    
    # Check 3: Skills that are conceptually impossible together at expert level
    # (e.g., "expert" in 10+ skills is implausible for someone with 3 years total experience)
    if candidate["profile"]["years_of_experience"] < 4:
        expert_count = sum(1 for s in candidate["skills"] if s["proficiency"] == "expert")
        if expert_count >= 5:
            penalties.append(0.1)
    
    # Check 4: Assessment score vs self-reported proficiency massive mismatch
    for skill in candidate["skills"]:
        assessment_score = candidate["redrob_signals"]["skill_assessment_scores"].get(skill["name"])
        if assessment_score is not None:
            if skill["proficiency"] == "expert" and assessment_score < 30:
                penalties.append(0.1)
    
    # Check 5: Career history dates that overlap significantly
    # (two full-time roles at the same time for >6 months → suspicious)
    # [implementation: sort by start_date, check for overlapping non-current roles]
    
    return min(penalties) if penalties else 1.0  # worst penalty wins

def apply_honeypot_penalty(final_score, honeypot_factor):
    if honeypot_factor == 0.0:
        return 0.05  # effectively buried, not zeroed (avoid exact ties)
    return final_score * honeypot_factor
```

### Correctness Check

- Test behavioral_score on extreme profiles: candidate with `last_active = 2025-01-01`, `response_rate = 0.05`, `open_to_work = False` should score < 0.2
- Test honeypot detection on 5 manually-constructed impossible profiles; all should score ≤ 0.1 on honeypot_score
- Verify that honeypots in the sample candidates (if any) are caught by at least one rule
- The spec says ≤10% honeypots in top 100 is the threshold; aim for 0% in top 100. Run honeypot_score on top 200 candidates, manually verify all score > 0.9

---

## Stage 6: LambdaMART Re-Ranker + Final Output
**Days 11–15 | Goal: Learn the optimal combination of all signals using a learning-to-rank model, then generate high-quality reasoning**

### What to do

**6.1 — Why LambdaMART?**

We have ~15-20 features per candidate. A hand-tuned weighted sum (Stage 4) is good but can't discover non-linear interactions. LambdaMART (Gradient Boosted Trees for ranking) can:
- Learn that "consulting_ratio > 0.8 AND hard_req_coverage < 0.5" is not just additive but multiplicative
- Optimize directly for NDCG@10 (the competition's highest-weighted metric)
- Run in milliseconds on CPU for 100K candidates at inference time

**6.2 — Training Data Strategy**

We don't have labeled training data for this specific JD. Use a two-step approach:

*Option A: LLM-Generated Pseudo-Labels (offline, pre-computation)*

Use Claude/GPT-4 offline to pseudo-label a sample of 500-1000 candidates as (relevant, partially_relevant, not_relevant) based on the JD. This takes ~2 hours and ~$5 in API costs. Use these as training labels.

```python
# Offline only — not during ranking step
prompt = f"""
JD: {jd_text}

Candidate profile:
{json.dumps(candidate, indent=2)}

Rate this candidate's fit for the JD on a 4-point scale:
3 = Strong fit — would definitely shortlist
2 = Moderate fit — worth a look
1 = Weak fit — one or two relevant signals only
0 = Not a fit — disqualified by JD criteria

Respond with only the number.
"""
```

*Option B: Heuristic Labels from Stage 4 Scores*

If Option A is impractical, use Stage 4 composite scores to create "soft labels" and train LambdaMART to refine the ordering.

**6.3 — Feature Matrix**

Assemble all features for LambdaMART input:

```python
FEATURE_NAMES = [
    "semantic_similarity",          # Stage 3
    "max_pool_career_similarity",   # Stage 3
    "consulting_ratio",             # Stage 2
    "deployment_score",             # Stage 2
    "years_in_product_companies",   # Stage 2
    "seniority_trend",              # Stage 2
    "hard_req_coverage",            # Stage 2
    "soft_req_coverage",            # Stage 2
    "avg_skill_depth",              # Stage 2
    "avg_assessment_score",         # Stage 2
    "edu_tier_score",               # Stage 2
    "is_cs_adjacent",               # Stage 2
    "location_score",               # Stage 2
    "notice_score",                 # Stage 2
    "salary_fit",                   # Stage 2
    "experience_modifier",          # Stage 4
    "behavioral_score",             # Stage 5
    "honeypot_factor",              # Stage 5
    "experience_years_raw",         # raw
    "github_activity_score",        # behavioral
    "disqualifier_hit",             # binary
]
```

**6.4 — Training and Inference**

```python
import lightgbm as lgb

# Training (offline)
train_data = lgb.Dataset(X_train, label=y_train, group=group_sizes)
params = {
    "objective": "lambdarank",
    "metric": "ndcg",
    "ndcg_eval_at": [10, 50],
    "learning_rate": 0.05,
    "num_leaves": 31,
    "n_estimators": 300
}
model = lgb.train(params, train_data, num_boost_round=300)
model.save_model("ranker.lgb")

# Inference (online, runs in seconds on CPU)
model = lgb.Booster(model_file="ranker.lgb")
scores = model.predict(X_all_candidates)  # 100K rows in < 10 seconds
```

**6.5 — Tie-Breaking**

Per spec, if two candidates have identical scores, break by `candidate_id` ascending (deterministic, spec-compliant).

**6.6 — Reasoning Generation (offline pre-computation)**

The spec rewards specific, honest reasoning. Generate reasoning strings *offline* using the LLM, caching results for all top-200 candidates:

```python
reasoning_prompt = f"""
Write a 1-2 sentence recruiter note for this candidate as a fit for the JD.
Be specific (mention actual skills, companies, signals from their profile).
Be honest (note any concerns like notice period or location).
Do NOT invent skills they don't have.

JD summary: {jd_summary}
Candidate: {candidate_text}
Score: {score:.3f}
"""
```

Example output: `"4.5 years applied ML at product companies, shipped hybrid BM25+dense retrieval at DataCo; strong NDCG/MRR eval background. Located in Pune, 30-day notice. Slight concern: no vector DB production experience listed, though retrieval work implies exposure."`

**6.7 — Final Output Pipeline**

```
rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Runtime breakdown (must complete in < 5 min):
- Load precomputed embeddings (.npy): ~5s
- Load precomputed features (.parquet): ~3s
- Compute JD embedding (once): ~2s
- Compute cosine similarities (matmul, CPU): ~8s
- Load features + score with LambdaMART: ~10s
- Sort and select top 100: <1s
- Load precomputed reasoning strings: <1s
- Write CSV: <1s
- **Total: ~30 seconds**

### Correctness Check

- Validate CSV format against spec before every submission: exactly 100 rows, ranks 1-100, non-increasing scores, all IDs valid
- Run the format validator script from the bundle
- Feature importance from LambdaMART: `hard_req_coverage`, `consulting_ratio`, and `semantic_similarity` should be top-3 features. If `notice_period` is #1, something is wrong
- Hold out 20 pseudo-labeled candidates from training; NDCG@10 on this holdout should be ≥ 0.75
- Manual review: read the top 10 candidates' full profiles. Every one should make intuitive sense. If a Marketing Manager appears in top 10, there is a bug

---

## 15-Day Implementation Roadmap

| Day | Task | Output |
|-----|------|--------|
| 1 | Parse JD with LLM; build skill taxonomy | `jd_parsed.json`, `skill_groups.py` |
| 2 | JD embedding; test semantic similarity on sample | `jd_embedding.npy` |
| 3 | Career + education feature extractors | `feature_engineering.py` (tested) |
| 4 | Skills + logistics feature extractors | Feature pipeline complete |
| 5 | Run full feature extraction on 100K candidates | `features_100k.parquet` |
| 6 | BGE model setup; batch encode all candidates | `candidate_embeddings.npy` (started) |
| 7 | Finish embeddings; compute cosine sims | `semantic_scores.npy` |
| 8 | Stage 4: composite scoring; validate golden set | `composite_scores.npy` |
| 9 | Stage 5: behavioral multiplier + honeypot filter | Updated `final_scores.npy` |
| 10 | Offline LLM pseudo-labeling of 800 candidates | `pseudo_labels.csv` |
| 11 | Train LambdaMART ranker; validate feature importance | `ranker.lgb` |
| 12 | Generate reasoning strings for top-200 candidates | `reasoning_cache.json` |
| 13 | Build `rank.py` end-to-end; benchmark runtime | `rank.py` (<5 min confirmed) |
| 14 | Full validation; format check; honeypot audit | Submission-ready CSV |
| 15 | Buffer: fix issues, polish reasoning, final submit | `team_xxx.csv` submitted |

---

## Anti-Patterns to Avoid (From the JD and Spec)

| Anti-Pattern | Why It Fails | Our Mitigation |
|---|---|---|
| Pure keyword matching | JD explicitly calls this a trap; keyword-stuffed profiles win | Semantic embeddings + career trajectory features dominate |
| Consulting firm candidates rise | JD explicitly disqualifies consulting-only careers | `consulting_ratio` feature + hard disqualifier gate |
| Honeypots rank high | Spec disqualifies submissions with >10% honeypots in top 100 | Consistency checks in Stage 5 |
| Inactive candidates rank high | Perfect-on-paper but unreachable | Behavioral multiplier in Stage 5 |
| All scores identical | Auto-rejected by validator | LambdaMART produces continuous scores; assert variance > 0.1 |
| Hallucinated reasoning | Penalized at Stage 4 review | Reasoning generated from candidate's own text, not invented |
| Job hoppers score high | JD warns against title-chasers | `short_stint_count` feature penalizes frequent switches |

---

## Key Design Philosophy

**Recruiter Emulation, Not Search Engine**

The system is structured to ask: *Would a senior recruiter shortlist this person?*

A recruiter would:
1. First check if the candidate is real and reachable (behavioral filter)
2. Immediately disqualify obvious mismatches (disqualifier gate)
3. Evaluate career trajectory, not just a skills checklist
4. Weight recent, relevant production work more than old or theoretical experience
5. Notice red flags: consulting-only career, no deployment evidence, 6 months inactive
6. Write specific, honest notes about each candidate

Our system mirrors this flow exactly: gate → career → skills+semantic → logistics → behavioral multiplier → re-rank → reason.
