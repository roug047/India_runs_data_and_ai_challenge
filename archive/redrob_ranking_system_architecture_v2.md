# Redrob AI — Intelligent Candidate Ranking System
## Redesigned Architecture v2.0 (15-Day Build Plan)

---

## Overview

**Mission:** Given a job description (JD), rank the 100 best-fit candidates from a 100K pool — the way a *senior technical recruiter with ML intuition* would, not a keyword search engine.

**Core constraints:**
- Ranking step: ≤5 min wall-clock, ≤16 GB RAM, CPU only, no network
- Pre-computation (embeddings, features, pseudo-labels) can run offline with no limits
- Output: `candidate_id, rank, score, reasoning` CSV with exactly 100 rows
- Metric: `0.50 × NDCG@10 + 0.30 × NDCG@50 + 0.15 × MAP + 0.05 × P@10`
- Honeypot disqualification: >10% in top 100 = auto-disqualified

**Core design philosophy: Recruiter Emulation, not Search Engine**

A recruiter would: verify the candidate is real and reachable → hard-disqualify obvious mismatches → evaluate career trajectory over skill checklists → weight recent production work over theoretical exposure → write honest, specific notes. Our system mirrors this exact flow.

**Why the previous architecture needed a redesign:**
1. LambdaMART training strategy was circular (pseudo-labels from Stage 4 scores trained to predict Stage 4 scores)
2. Honeypot detection had a broken temporal formula and no multiplicative penalty accumulation
3. Behavioral weights didn't reflect what "hireable" actually means in a recruiting context
4. Reasoning generation was LLM-open-ended, inviting hallucination that Stage 4 penalizes
5. `offer_acceptance_rate = -1` was treated as 0 (penalizing new users who've never had offers)
6. `skill_assessment_scores` was averaged into a single number, discarding the most verifiable signal
7. `preferred_work_mode` from redrob_signals was never used
8. No fallback plan if BGE-large encoding takes too long
9. `compute_range_overlap` for salary was left undefined (`...`)
10. Timeline was backloaded — LambdaMART, reasoning, validation all crammed into final 5 days

---

## System Architecture: 7 Stages

```
Stage 0: Pre-flight & Environment Setup          (Day 1)
Stage 1: JD Intelligence Layer                   (Days 1–2)
Stage 2: Candidate Feature Engineering           (Days 3–6)
Stage 3: Semantic Embedding Index                (Days 4–7, runs in parallel)
Stage 4: Honeypot Detection                      (Day 7)
Stage 5: Multi-Signal Scoring Engine             (Days 8–9)
Stage 6: LambdaMART Re-Ranker                    (Days 10–12)
Stage 7: Reasoning Generation + Output           (Days 12–14)
```

---

## Stage 0: Pre-flight & Environment Setup
**Day 1 | Goal: Validate environment, data, tools before building**

This stage prevents the classic hackathon mistake of discovering environment problems on Day 10.

### 0.1 — Environment Validation

```bash
# Python version + memory check
python3 -c "import sys; print(sys.version)"
python3 -c "import psutil; print(f'RAM: {psutil.virtual_memory().total / 1e9:.1f} GB')"

# Required packages
pip install sentence-transformers lightgbm scikit-learn pandas numpy pyarrow tqdm
pip install anthropic  # offline pseudo-labeling only

# Model download (do this NOW while you build other things)
python3 -c "
from sentence_transformers import SentenceTransformer
model_fast = SentenceTransformer('BAAI/bge-base-en-v1.5')      # 768-dim, ~500MB, 2x faster
model_best = SentenceTransformer('BAAI/bge-large-en-v1.5')     # 1024-dim, ~1.3GB, better
print('Models downloaded.')
"
```

### 0.2 — Data Integrity Check

```python
import gzip, json
from collections import Counter
from datetime import date

candidates = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in f:
        if line.strip():
            candidates.append(json.loads(line))

assert len(candidates) == 100_000, f"Expected 100K, got {len(candidates)}"

# Check ID uniqueness
ids = [c["candidate_id"] for c in candidates]
assert len(set(ids)) == 100_000, "Duplicate IDs found!"

# Check required fields exist
required = ["candidate_id", "profile", "career_history", "education", "skills", "redrob_signals"]
for c in candidates[:100]:
    for field in required:
        assert field in c, f"Missing {field} in {c['candidate_id']}"

print(f"✅ Data check passed: {len(candidates)} candidates, all IDs unique, required fields present")

# Quick distribution stats (important for calibrating features)
yoe = [c["profile"]["years_of_experience"] for c in candidates]
countries = Counter(c["profile"]["country"] for c in candidates)
work_modes = Counter(c["redrob_signals"]["preferred_work_mode"] for c in candidates)
print(f"Years of experience: min={min(yoe):.1f}, median={sorted(yoe)[50000]:.1f}, max={max(yoe):.1f}")
print(f"Top countries: {countries.most_common(5)}")
print(f"Work modes: {dict(work_modes)}")
```

### 0.3 — Embedding Speed Benchmark

```python
import time
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-base-en-v1.5")
sample_texts = ["sample candidate text " * 50] * 128  # representative length
start = time.time()
_ = model.encode(sample_texts, batch_size=64)
elapsed = time.time() - start

rate = 128 / elapsed
est_hours = 100_000 / rate / 3600
print(f"Encoding rate: {rate:.0f} candidates/sec")
print(f"Estimated time for 100K (bge-base): {est_hours:.1f} hours")

# Decision rule:
# bge-base  < 1.5 hours → use bge-large for better quality
# bge-base  1.5–3 hours → use bge-base as primary
# bge-base  > 3 hours  → use all-MiniLM-L6-v2 (20× faster) as primary, bge-base as reranker on top-5K
```

**Decision checkpoint:** Choose your embedding model NOW based on the benchmark. Write it down. Don't change mid-build.

---

## Stage 1: JD Intelligence Layer
**Days 1–2 | Goal: Extract structured meaning from the JD, not a keyword list**

### 1.1 — LLM-Powered JD Parsing (offline, one-time)

Parse the JD into a structured schema using Claude/GPT-4. This runs once offline — not during the ranking step.

```python
import anthropic, json

JD_TEXT = open("job_description.md").read()

client = anthropic.Anthropic()

parse_prompt = f"""
Parse the following job description into the exact JSON schema below.
Be thorough — include implied signals, not just explicit text.
For example, "shipped to real users" implies production_deployment_required = true.
Respond with ONLY valid JSON, no explanation, no markdown fences.

JD:
{JD_TEXT}

Schema to fill:
{{
  "role_title": "...",
  "experience_range": {{"min": 0, "max": 0}},
  "hard_requirements": [
    // Each is a skill group name (will be matched against SKILL_GROUPS below)
    // Must: vector_search_infra, embedding_models, ranking_evaluation, python_production
  ],
  "soft_requirements": [
    // Nice-to-have skill group names
    // e.g.: llm_finetuning, learning_to_rank, hr_tech_experience, distributed_systems
  ],
  "disqualifier_patterns": [
    // Each is a string key matching our disqualifier check functions
    // e.g.: "pure_consulting_career", "no_production_deployment", "cv_speech_robotics_only",
    //        "langchain_only_under_12mo", "no_code_in_18mo", "closed_source_only_5yr"
  ],
  "preferred_locations": ["Pune", "Noida", "Hyderabad", "Mumbai", "Delhi NCR"],
  "acceptable_countries": ["India"],
  "notice_period_ideal_days": 30,
  "notice_period_max_days": 90,
  "salary_band_inr_lpa": {{"min": 30, "max": 70}},
  "preferred_work_modes": ["hybrid", "flexible", "onsite"],
  "culture_flags": ["startup_ready", "ships_fast", "no_title_chasing", "writes_async"],
  "production_deployment_required": true,
  "ideal_profile_summary": "..."
}}
"""

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2000,
    messages=[{"role": "user", "content": parse_prompt}]
)

raw = response.content[0].text.strip()
jd_parsed = json.loads(raw)
json.dump(jd_parsed, open("jd_parsed.json", "w"), indent=2)
print("✅ JD parsed and saved.")
```

**Manual verification (mandatory):** After parsing, read `jd_parsed.json` against the raw JD. Verify:
- All 4 hard requirements appear (vector search, embeddings, ranking eval, Python production)
- All 6 disqualifier patterns appear
- Location and salary are correct
- `production_deployment_required = true` (the JD is explicit about this)

### 1.2 — Skill Taxonomy (expanded and corrected)

```python
SKILL_GROUPS = {
    # Hard requirement groups
    "vector_search_infra": [
        "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
        "elasticsearch", "pgvector", "chromadb", "annoy", "vespa", "typesense",
        "vector database", "ann", "approximate nearest neighbor", "hnsw"
    ],
    "embedding_models": [
        "sentence-transformers", "sentence transformers", "bge", "e5", "openai embeddings",
        "ada-002", "instructor", "gte", "clip", "cohere embed", "text embeddings",
        "dense retrieval", "bi-encoder", "dual encoder", "semantic search"
    ],
    "ranking_evaluation": [
        "ndcg", "mrr", "map", "mean average precision", "a/b testing", "a/b test",
        "learning to rank", "ltr", "lambdamart", "xgboost ranker", "listwise",
        "pairwise", "offline evaluation", "online evaluation", "ranking metrics",
        "information retrieval", "recall@k", "precision@k", "hit rate"
    ],
    "python_production": [
        "python", "fastapi", "flask", "django", "production python", "pydantic",
        "asyncio", "celery", "gunicorn", "uvicorn"
    ],

    # Soft requirement groups
    "llm_finetuning": [
        "lora", "qlora", "peft", "rlhf", "sft", "instruction tuning",
        "fine-tuning", "finetuning", "dpo", "full fine-tune", "adapter",
        "parameter efficient", "alpaca", "llama", "mistral fine-tune"
    ],
    "learning_to_rank": [
        "lambdamart", "xgboost rank", "lightgbm rank", "ranknet", "listnet",
        "learning to rank", "l2r", "gradient boosted trees rank"
    ],
    "hr_tech_experience": [
        "recruiting", "talent acquisition", "ats", "applicant tracking", "hr tech",
        "hrtech", "talent intelligence", "candidate matching", "job matching",
        "resume parsing", "talent platform"
    ],
    "distributed_systems": [
        "kafka", "spark", "flink", "ray", "distributed", "kubernetes", "k8s",
        "microservices", "grpc", "message queue", "celery", "redis", "rabbitmq"
    ],
    "hybrid_retrieval": [
        "bm25", "tfidf", "tf-idf", "hybrid search", "hybrid retrieval",
        "sparse retrieval", "dense-sparse fusion", "rrf", "reciprocal rank fusion",
        "rag", "retrieval augmented", "reranking", "cross-encoder"
    ],

    # Negative/disqualifier groups
    "consulting_firms": [
        "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
        "capgemini", "mphasis", "tech mahindra", "hexaware", "ltimindtree",
        "mindtree", "hcl technologies", "hcltech", "l&t infotech", "persistent systems",
        "mastech", "niit technologies"
    ],
    "cv_speech_robotics": [
        "computer vision", "image classification", "object detection", "yolo", "opencv",
        "speech recognition", "asr", "tts", "text to speech", "robotics", "ros",
        "point cloud", "lidar", "slam", "autonomous driving", "ocr only"
    ]
}

# Flatten to lookup
SKILL_TO_GROUP = {}
for group, terms in SKILL_GROUPS.items():
    for term in terms:
        SKILL_TO_GROUP[term.lower()] = group
```

### 1.3 — JD Embedding (offline, one-time)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-large-en-v1.5")  # or your chosen model from Stage 0.3

# BGE requires a query prefix for retrieval tasks
JD_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Embed the full JD narrative + ideal candidate description
jd_full_text = open("job_description.md").read()
ideal_candidate_text = jd_parsed["ideal_profile_summary"]

jd_embedding = model.encode(
    JD_QUERY_PREFIX + jd_full_text,
    normalize_embeddings=True
)
ideal_embedding = model.encode(
    JD_QUERY_PREFIX + ideal_candidate_text,
    normalize_embeddings=True
)

np.save("jd_embedding.npy", jd_embedding)
np.save("ideal_embedding.npy", ideal_embedding)
print(f"✅ JD embeddings saved. Shape: {jd_embedding.shape}")
```

---

## Stage 2: Candidate Feature Engineering
**Days 3–6 | Goal: Convert every candidate into a deterministic, normalized feature vector**

All feature extraction runs offline and is stored as a Parquet file. The online ranking step loads pre-computed features — no recomputation during the 5-minute window.

### 2.1 — Feature Engineering Master Runner

```python
import pandas as pd
import numpy as np
import json, gzip
from datetime import date
from tqdm import tqdm

REFERENCE_DATE = date(2026, 6, 6)  # fix this to the dataset's reference date

def extract_all_features(candidate, jd_parsed):
    features = {}
    features.update(career_features(candidate))
    features.update(skills_features(candidate, jd_parsed))
    features.update(education_features(candidate))
    features.update(logistics_features(candidate, jd_parsed))
    features.update(behavioral_features(candidate["redrob_signals"]))
    features.update(honeypot_features(candidate))
    features["candidate_id"] = candidate["candidate_id"]
    return features

# Run on all 100K
all_features = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in tqdm(f, total=100_000):
        if line.strip():
            c = json.loads(line)
            all_features.append(extract_all_features(c, jd_parsed))

df = pd.DataFrame(all_features)
df.to_parquet("features_100k.parquet", index=False)
print(f"✅ Features saved: {df.shape[0]} rows × {df.shape[1]} cols")
```

### 2.2 — Career Features

```python
CONSULTING_FIRMS_SET = set(SKILL_GROUPS["consulting_firms"])

COMPANY_SIZE_SCORE = {
    "1-10": 0.4,       # Very small startup — high risk, good signal if product
    "11-50": 0.7,      # Startup — product company likely
    "51-200": 0.85,
    "201-500": 0.9,
    "501-1000": 0.85,
    "1001-5000": 0.75,
    "5001-10000": 0.6,
    "10001+": 0.4      # Large companies — often consulting at this size
}

TITLE_SENIORITY = {
    "intern": 0, "trainee": 0, "junior": 1, "associate": 2, "engineer": 3,
    "analyst": 2, "developer": 3, "senior": 4, "lead": 5, "staff": 5,
    "principal": 6, "architect": 6, "manager": 4, "director": 7, "vp": 8, "head": 7
}

PRODUCTION_ML_KEYWORDS = [
    "deployed", "production", "served", "serving", "real users", "at scale",
    "inference", "latency", "throughput", "a/b test", "shipped", "rollout",
    "monitoring", "drift", "retraining", "mlops", "feature store", "model registry"
]

RETRIEVAL_IR_KEYWORDS = [
    "retrieval", "ranking", "search", "embedding", "vector", "faiss", "milvus",
    "bm25", "ndcg", "mrr", "recall@", "precision@", "rerank", "rag",
    "recommendation", "similarity", "nearest neighbor", "dense", "sparse"
]

def is_consulting(company_name):
    name_lower = company_name.lower()
    return any(firm in name_lower for firm in CONSULTING_FIRMS_SET)

def compute_seniority_score(title):
    title_lower = title.lower()
    for keyword, score in sorted(TITLE_SENIORITY.items(), key=lambda x: -x[1]):
        if keyword in title_lower:
            return score
    return 2  # default: junior-ish

def career_features(candidate):
    history = candidate["career_history"]
    profile = candidate["profile"]
    yoe = profile["years_of_experience"]

    total_months = sum(r["duration_months"] for r in history)

    # --- Consulting ratio ---
    consulting_months = sum(
        r["duration_months"] for r in history if is_consulting(r["company"])
    )
    consulting_ratio = consulting_months / max(total_months, 1)

    # --- Product company experience ---
    product_months = total_months - consulting_months
    years_in_product = product_months / 12

    # --- Deployment & retrieval signals from descriptions ---
    all_descriptions = " ".join(r["description"].lower() for r in history)
    prod_ml_hits = sum(1 for kw in PRODUCTION_ML_KEYWORDS if kw in all_descriptions)
    retrieval_ir_hits = sum(1 for kw in RETRIEVAL_IR_KEYWORDS if kw in all_descriptions)

    # Normalize by number of roles to avoid penalizing people with fewer roles
    n_roles = max(len(history), 1)
    deployment_score = min(prod_ml_hits / (n_roles * 3), 1.0)     # up to 3 keywords per role
    retrieval_score = min(retrieval_ir_hits / (n_roles * 3), 1.0)

    # --- Seniority trend ---
    sorted_history = sorted(history, key=lambda r: r["start_date"])
    seniority_scores = [compute_seniority_score(r["title"]) for r in sorted_history]
    if len(seniority_scores) >= 2:
        seniority_trend = (seniority_scores[-1] - seniority_scores[0]) / max(len(seniority_scores), 1)
        seniority_trend = max(-1, min(1, seniority_trend / 3))  # normalize to [-1, 1]
    else:
        seniority_trend = 0.0

    # --- Job hopping: short stints < 18 months, in last 8 years ---
    cutoff = "2018-06-01"
    recent_roles = [r for r in history if r["start_date"] >= cutoff and not r["is_current"]]
    short_stints = sum(1 for r in recent_roles if r["duration_months"] < 18)
    job_hop_penalty = min(short_stints / 3, 1.0)  # 3+ short stints = full penalty

    # --- Company size signal (current role, product companies score higher) ---
    current_size_score = COMPANY_SIZE_SCORE.get(profile["current_company_size"], 0.5)
    # Consulting companies at large size are a stronger negative
    if is_consulting(profile["current_company"]):
        current_size_score *= 0.4

    # --- Title chaser flag: multiple lateral title moves without seniority growth ---
    # If someone has >3 companies but current seniority <= starting seniority → flag
    title_chaser = (
        len(history) >= 4
        and seniority_scores[-1] <= seniority_scores[0]
        and short_stints >= 2
    )

    return {
        "consulting_ratio": consulting_ratio,
        "years_in_product": min(years_in_product / 8, 1.0),  # normalize at 8 years
        "deployment_score": deployment_score,
        "retrieval_ir_score": retrieval_ir_score,
        "seniority_trend": (seniority_trend + 1) / 2,  # shift to [0, 1]
        "job_hop_penalty": job_hop_penalty,
        "title_chaser_flag": float(title_chaser),
        "current_size_score": current_size_score,
        "n_roles": n_roles,
    }
```

### 2.3 — Skills Features (with verified assessment integration)

This is where the previous architecture lost the most value. Assessment scores are the only *verified* signal in the dataset — they deserve to anchor the skills scoring.

```python
def hard_req_coverage(candidate, jd_parsed):
    """
    For each hard requirement group in the JD, determine if the candidate
    demonstrates it via: (a) verified assessment, (b) advanced/expert skill, or
    (c) keyword in career descriptions.
    Returns a dict of group -> coverage_score [0, 1].
    """
    skills_lower = {s["name"].lower(): s for s in candidate["skills"]}
    descriptions = " ".join(r["description"].lower() for r in candidate["career_history"])
    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})

    # Normalize assessment keys to lowercase
    assessments_lower = {k.lower(): v for k, v in assessments.items()}

    coverage = {}
    for req_group in jd_parsed["hard_requirements"]:
        group_terms = SKILL_GROUPS.get(req_group, [])
        score = 0.0

        for term in group_terms:
            # Check assessment (highest credibility — verified, can't be faked)
            for akey, aval in assessments_lower.items():
                if term in akey or akey in term:
                    if aval >= 70:
                        score = max(score, 1.0)    # verified expert
                    elif aval >= 50:
                        score = max(score, 0.8)    # verified competent
                    elif aval >= 30:
                        score = max(score, 0.5)    # verified beginner
                    else:
                        score = max(score, 0.2)    # took test, failed — still real

            # Check self-reported skills (medium credibility)
            if term in skills_lower:
                s = skills_lower[term]
                prof_map = {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.75, "expert": 0.9}
                duration_bonus = min(s.get("duration_months", 0) / 36, 0.1)
                endorsement_bonus = min(s.get("endorsements", 0) / 50, 0.05)
                skill_score = prof_map[s["proficiency"]] + duration_bonus + endorsement_bonus

                # Self-reported "expert" without assessment = credibility discount
                if s["proficiency"] == "expert" and not any(
                    term in akey or akey in term for akey in assessments_lower
                ):
                    skill_score *= 0.75  # unverified expert claim

                score = max(score, skill_score)

            # Check career descriptions (lower credibility, implicit signal)
            if term in descriptions:
                score = max(score, 0.4)  # mentioned in work context

        coverage[f"hard_req_{req_group}"] = min(score, 1.0)

    return coverage


def assessment_credibility_score(candidate):
    """
    Detect self-inflation: expert claims without matching assessments, or
    expert claims with contradicting low assessment scores.
    Returns penalty factor [0, 1] where 1 = credible, 0 = highly inflated.
    """
    skills = candidate["skills"]
    assessments = {k.lower(): v for k, v in
                   candidate["redrob_signals"].get("skill_assessment_scores", {}).items()}

    inflation_hits = 0
    checks = 0

    for skill in skills:
        name_lower = skill["name"].lower()
        if skill["proficiency"] in ["expert", "advanced"]:
            checks += 1
            # Find matching assessment
            matched_score = None
            for akey, aval in assessments.items():
                if name_lower in akey or akey in name_lower:
                    matched_score = aval
                    break

            if matched_score is not None:
                if skill["proficiency"] == "expert" and matched_score < 40:
                    inflation_hits += 2   # strong contradiction
                elif skill["proficiency"] == "advanced" and matched_score < 25:
                    inflation_hits += 1

    if checks == 0:
        return 0.8  # no expert/advanced claims → neutral
    inflation_rate = inflation_hits / (checks * 2)
    return max(0.1, 1.0 - inflation_rate)


def skills_features(candidate, jd_parsed):
    coverage = hard_req_coverage(candidate, jd_parsed)

    # Average hard requirement coverage
    hard_scores = [v for v in coverage.values()]
    avg_hard_coverage = sum(hard_scores) / max(len(hard_scores), 1)

    # Minimum hard coverage (weakest link — recruiter would notice missing critical skill)
    min_hard_coverage = min(hard_scores) if hard_scores else 0.0

    # Soft requirement coverage
    skills_text = " ".join(
        s["name"].lower() for s in candidate["skills"]
    ) + " " + " ".join(
        r["description"].lower() for r in candidate["career_history"]
    )
    soft_hits = sum(
        1 for group in jd_parsed["soft_requirements"]
        if any(term in skills_text for term in SKILL_GROUPS.get(group, []))
    )
    soft_coverage = soft_hits / max(len(jd_parsed["soft_requirements"]), 1)

    # Skill assessment score for JD-relevant skills only
    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})
    jd_relevant_assessments = []
    all_jd_terms = set()
    for group in jd_parsed["hard_requirements"] + jd_parsed["soft_requirements"]:
        all_jd_terms.update(SKILL_GROUPS.get(group, []))

    for akey, aval in assessments.items():
        if any(term in akey.lower() or akey.lower() in term for term in all_jd_terms):
            jd_relevant_assessments.append(aval)

    avg_relevant_assessment = (
        sum(jd_relevant_assessments) / len(jd_relevant_assessments)
        if jd_relevant_assessments else -1  # -1 = no relevant assessments taken
    )
    has_relevant_assessments = float(len(jd_relevant_assessments) > 0)

    # CV/Speech/Robotics domain mismatch
    skills_descriptions = " ".join(
        s["name"].lower() for s in candidate["skills"]
    ) + " " + " ".join(r["description"].lower() for r in candidate["career_history"])
    cv_speech_hits = sum(
        1 for term in SKILL_GROUPS["cv_speech_robotics"]
        if term in skills_descriptions
    )
    ir_ml_hits = sum(
        1 for group in ["vector_search_infra", "embedding_models", "ranking_evaluation", "hybrid_retrieval"]
        for term in SKILL_GROUPS[group]
        if term in skills_descriptions
    )
    domain_mismatch = (
        cv_speech_hits > 3 and ir_ml_hits < 2
    )

    return {
        **coverage,                                      # individual hard req scores
        "avg_hard_req_coverage": avg_hard_coverage,
        "min_hard_req_coverage": min_hard_coverage,      # KEY: weakest-link signal
        "soft_req_coverage": soft_coverage,
        "avg_relevant_assessment": max(avg_relevant_assessment, 0) / 100,  # normalize
        "has_relevant_assessments": has_relevant_assessments,
        "assessment_credibility": assessment_credibility_score(candidate),
        "domain_mismatch_flag": float(domain_mismatch),
    }
```

### 2.4 — Education Features

```python
TIER_SCORE = {"tier_1": 1.0, "tier_2": 0.78, "tier_3": 0.56, "tier_4": 0.35, "unknown": 0.45}

CS_ADJACENT_FIELDS = [
    "computer science", "information technology", "electrical engineering",
    "electronics", "mathematics", "statistics", "data science",
    "artificial intelligence", "machine learning", "software engineering",
    "computational", "informatics"
]

def education_features(candidate):
    edu = candidate["education"]
    if not edu:
        return {"edu_tier_score": 0.35, "is_cs_adjacent": 0.0, "has_postgrad": 0.0}

    best = max(edu, key=lambda e: TIER_SCORE.get(e.get("tier", "unknown"), 0.45))
    tier_score = TIER_SCORE.get(best.get("tier", "unknown"), 0.45)

    field = best.get("field_of_study", "").lower()
    is_cs = float(any(f in field for f in CS_ADJACENT_FIELDS))

    # Postgraduate degree bonus
    degree = best.get("degree", "").lower()
    has_postgrad = float(any(d in degree for d in ["m.tech", "m.e.", "mtech", "m.s.", "ms ", "mba", "phd", "ph.d", "master"]))

    # Recency: did they graduate into the right era?
    end_year = best.get("end_year", 2000)
    edu_recency = max(0, min(1, (end_year - 2000) / 20))  # 2020+ grad = 1.0

    return {
        "edu_tier_score": tier_score,
        "is_cs_adjacent": is_cs,
        "has_postgrad": has_postgrad,
        "edu_recency": edu_recency,
    }
```

### 2.5 — Logistics Features (with work mode fix)

```python
PREFERRED_LOCS = {"pune", "noida", "hyderabad", "mumbai", "delhi", "ncr", "gurgaon", "gurugram", "bengaluru"}

def salary_fit(candidate_range, jd_range):
    """Correct overlap formula. Partial credit for near-misses."""
    cmin, cmax = candidate_range["min"], candidate_range["max"]
    jmin, jmax = jd_range["min"], jd_range["max"]

    overlap_low = max(cmin, jmin)
    overlap_high = min(cmax, jmax)

    if overlap_high >= overlap_low:
        # There is overlap
        overlap = overlap_high - overlap_low
        jd_width = max(jmax - jmin, 1)
        return min(overlap / jd_width, 1.0)
    else:
        # No overlap — partial credit if close
        gap = overlap_low - overlap_high
        jd_width = max(jmax - jmin, 1)
        return max(0.0, 1.0 - gap / jd_width)


def logistics_features(candidate, jd_parsed):
    signals = candidate["redrob_signals"]
    profile = candidate["profile"]

    # Location
    loc_lower = profile["location"].lower()
    country_lower = profile["country"].lower()
    in_preferred = any(city in loc_lower for city in PREFERRED_LOCS)

    if in_preferred:
        location_score = 1.0
    elif country_lower == "india" and signals["willing_to_relocate"]:
        location_score = 0.65
    elif country_lower == "india":
        location_score = 0.35  # right country, wrong city, won't relocate
    else:
        location_score = 0.05  # outside India

    # Notice period
    notice = signals["notice_period_days"]
    if notice <= 15:
        notice_score = 1.0
    elif notice <= 30:
        notice_score = 0.95
    elif notice <= 60:
        notice_score = 0.7
    elif notice <= 90:
        notice_score = 0.45
    else:
        notice_score = 0.15  # >90 days is a real problem for this role

    # Salary fit (using correct formula now)
    jd_sal = jd_parsed["salary_band_inr_lpa"]
    sal_range = signals["expected_salary_range_inr_lpa"]
    salary_score = salary_fit(sal_range, jd_sal)

    # Work mode compatibility (NEW — was missing from v1)
    preferred_mode = signals["preferred_work_mode"]
    jd_modes = set(jd_parsed["preferred_work_modes"])   # ["hybrid", "flexible", "onsite"]
    if preferred_mode in jd_modes or preferred_mode == "flexible":
        work_mode_score = 1.0
    elif preferred_mode == "onsite" and "hybrid" in jd_modes:
        work_mode_score = 0.8   # onsite candidate for hybrid role — compatible
    elif preferred_mode == "remote":
        # Remote candidate for hybrid role — depends on willingness to relocate
        work_mode_score = 0.3 if not signals["willing_to_relocate"] else 0.5
    else:
        work_mode_score = 0.6

    return {
        "location_score": location_score,
        "notice_score": notice_score,
        "salary_score": salary_score,
        "work_mode_score": work_mode_score,
        "willing_to_relocate": float(signals["willing_to_relocate"]),
    }
```

### 2.6 — Behavioral Features (reweighted and with -1 handling)

**Key fix from v1:** `offer_acceptance_rate = -1` means no offer history (new user), not "rejected all offers." Treat it as neutral (0.5), not 0.

```python
def behavioral_features(signals):
    # --- Recency ---
    last_active = date.fromisoformat(signals["last_active_date"])
    days_inactive = (REFERENCE_DATE - last_active).days
    recency = max(0.0, 1.0 - days_inactive / 120)   # 4 months inactive = 0; was 6 months in v1

    # --- Hiring intent (most important signal for recruiter) ---
    open_to_work = float(signals["open_to_work_flag"])

    # --- Responsiveness ---
    response_rate = signals["recruiter_response_rate"]   # 0-1
    avg_response_hrs = signals["avg_response_time_hours"]
    response_time_score = max(0.0, 1.0 - avg_response_hrs / 72)   # 72h = 0; was 168h in v1

    # Composite responsiveness
    responsiveness = 0.65 * response_rate + 0.35 * response_time_score

    # --- Application activity ---
    apps_30d = min(signals["applications_submitted_30d"] / 8, 1.0)   # 8+ apps/month = max
    saved_30d = min(signals["saved_by_recruiters_30d"] / 10, 1.0)     # proxy for market interest

    # --- Track record ---
    interview_completion = signals["interview_completion_rate"]
    offer_acceptance_raw = signals["offer_acceptance_rate"]
    # FIX: -1 = no offer history (new user), not "rejected all offers"
    offer_acceptance = 0.5 if offer_acceptance_raw == -1 else offer_acceptance_raw

    track_record = 0.5 * interview_completion + 0.5 * offer_acceptance

    # --- Platform credibility ---
    credibility = (
        0.40 * float(signals["verified_email"]) +
        0.30 * float(signals["verified_phone"]) +
        0.20 * (signals["profile_completeness_score"] / 100) +
        0.10 * float(signals["linkedin_connected"])
    )

    # --- GitHub activity (NEW — was not used in v1) ---
    github_raw = signals["github_activity_score"]
    # -1 = no GitHub linked; 0-100 = activity score
    if github_raw == -1:
        github_score = 0.4     # neutral: no GitHub is common for product engineers
    elif github_raw >= 70:
        github_score = 1.0     # strong external signal
    elif github_raw >= 40:
        github_score = 0.7
    elif github_raw >= 15:
        github_score = 0.5
    else:
        github_score = 0.3     # linked GitHub but nearly inactive

    # --- Composite behavioral score (reweighted from v1) ---
    # Priority order for hiring: open_to_work → responsiveness → recency → track_record
    behavioral = (
        0.25 * open_to_work +          # was 8% in v1 (buried inside intent). Now primary.
        0.22 * responsiveness +         # recruiter contact success
        0.18 * recency +                # are they actively looking?
        0.15 * track_record +           # will they close?
        0.10 * credibility +            # is the profile real?
        0.05 * apps_30d +
        0.05 * github_score
    )

    return {
        "behavioral_score": behavioral,
        "open_to_work": open_to_work,
        "recency": recency,
        "responsiveness": responsiveness,
        "track_record": track_record,
        "credibility": credibility,
        "github_score": github_score,
        "apps_30d": apps_30d,
        "saved_30d": saved_30d,
    }
```

### 2.7 — Honeypot Detection (rebuilt from scratch)

**Key fix from v1:** v1's formula was broken (single-flag instant zero, wrong temporal logic). This uses multiplicative penalty accumulation and 6 distinct signal types, each independently motivated.

```python
from datetime import date, datetime

def parse_year(date_str):
    """Safely extract year from a date string."""
    try:
        return int(date_str[:4])
    except:
        return None

def honeypot_features(candidate):
    """
    Returns honeypot_score [0, 1]:
      1.0 = clean profile
      0.0 = certainly a honeypot (impossible profile)
    Penalties multiply — multiple moderate flags compound.
    """
    profile = candidate["profile"]
    history = candidate["career_history"]
    skills = candidate["skills"]
    edu = candidate["education"]
    yoe = profile["years_of_experience"]

    penalty = 1.0   # start clean, multiply down

    # --- Signal 1: Temporal impossibility (role start predates graduation) ---
    if edu:
        latest_grad_year = max((e.get("end_year", 0) for e in edu), default=0)
        for role in history:
            if not role.get("is_current", False):
                role_start_year = parse_year(role.get("start_date", "2000"))
                if role_start_year and latest_grad_year and \
                   role_start_year < latest_grad_year - 1:
                    # Working full-time a year before graduation → suspicious
                    penalty *= 0.1   # very strong signal

    # --- Signal 2: Duration exceeds possible career span ---
    # Sum of all role durations cannot exceed years_of_experience by more than 24 months
    # (small overlap is fine: someone can have done consulting + part-time)
    total_duration_months = sum(r["duration_months"] for r in history)
    max_possible_months = yoe * 12 + 24
    if total_duration_months > max_possible_months:
        excess = total_duration_months - max_possible_months
        penalty *= max(0.05, 1.0 - excess / (yoe * 12))   # proportional penalty

    # --- Signal 3: Expert proficiency with zero months used ---
    zero_duration_experts = [
        s for s in skills
        if s["proficiency"] == "expert" and s.get("duration_months", 0) == 0
    ]
    if len(zero_duration_experts) >= 2:
        penalty *= 0.2   # expert in something you've never used
    elif len(zero_duration_experts) == 1:
        penalty *= 0.6

    # --- Signal 4: Assessment contradicts expert self-report ---
    assessments_lower = {
        k.lower(): v for k, v in
        candidate["redrob_signals"].get("skill_assessment_scores", {}).items()
    }
    expert_assessment_contradictions = 0
    for skill in skills:
        if skill["proficiency"] == "expert":
            name_lower = skill["name"].lower()
            for akey, aval in assessments_lower.items():
                if name_lower in akey or akey in name_lower:
                    if aval < 35:
                        expert_assessment_contradictions += 1

    if expert_assessment_contradictions >= 2:
        penalty *= 0.15
    elif expert_assessment_contradictions == 1:
        penalty *= 0.45

    # --- Signal 5: Too many expert skills for experience level ---
    # A 3-year engineer claiming expert in 5+ skills is implausible
    expert_count = sum(1 for s in skills if s["proficiency"] == "expert")
    if yoe < 4 and expert_count >= 5:
        penalty *= 0.25
    elif yoe < 6 and expert_count >= 8:
        penalty *= 0.40
    elif yoe < 8 and expert_count >= 12:
        penalty *= 0.55

    # --- Signal 6: Overlapping concurrent full-time roles ---
    # Sort non-current roles by start date; check for >3 month overlaps
    past_roles = sorted(
        [r for r in history if not r.get("is_current", False) and r.get("end_date")],
        key=lambda r: r["start_date"]
    )
    for i in range(len(past_roles) - 1):
        r1 = past_roles[i]
        r2 = past_roles[i + 1]
        # r2 starts before r1 ends
        if r2["start_date"] < r1["end_date"]:
            overlap_start = r2["start_date"]
            overlap_end = min(r1["end_date"], r2.get("end_date") or r1["end_date"])
            # Rough overlap in months
            try:
                start = datetime.strptime(overlap_start, "%Y-%m-%d")
                end = datetime.strptime(overlap_end, "%Y-%m-%d")
                overlap_months = max(0, (end - start).days / 30)
                if overlap_months > 3:
                    penalty *= 0.3   # two concurrent full-time jobs for >3 months
            except:
                pass

    return {
        "honeypot_score": penalty,
        "is_likely_honeypot": float(penalty < 0.15),
    }
```

---

## Stage 3: Semantic Embedding Index
**Days 4–7 (parallel to Stage 2) | Goal: Capture semantic fit beyond keyword matching**

### 3.1 — Candidate Text Synthesis

```python
def synthesize_candidate_text(c):
    """
    Synthesize a rich text blob from all narrative fields.
    Order matters: put most-relevant fields first (embedding models weight earlier text).
    """
    parts = []

    # Career descriptions first — most signal for a technical role
    for role in sorted(c["career_history"], key=lambda r: r["start_date"], reverse=True):
        # Weight recent roles by adding them twice
        parts.append(f"{role['title']} at {role['company']} ({role['industry']}): {role['description']}")

    # Profile headline and summary
    parts.append(c["profile"]["headline"])
    parts.append(c["profile"]["summary"])

    # Skills with proficiency context
    skill_strs = []
    for s in c["skills"]:
        assessments = c["redrob_signals"].get("skill_assessment_scores", {})
        akey = next((k for k in assessments if s["name"].lower() in k.lower()), None)
        if akey:
            skill_strs.append(f"{s['name']} ({s['proficiency']}, assessment: {assessments[akey]:.0f}/100)")
        else:
            skill_strs.append(f"{s['name']} ({s['proficiency']})")
    parts.append("Skills: " + ", ".join(skill_strs))

    # Education
    for e in c["education"]:
        parts.append(f"{e['degree']} in {e['field_of_study']} from {e['institution']}")

    # Certifications
    for cert in c.get("certifications", []):
        parts.append(f"Certified: {cert['name']} ({cert['issuer']}, {cert['year']})")

    return " | ".join(parts)
```

### 3.2 — Batch Encoding with Fallback

```python
import numpy as np
from sentence_transformers import SentenceTransformer
import gzip, json
from tqdm import tqdm
import time

def batch_encode_candidates(model_name, output_path, batch_size=64):
    model = SentenceTransformer(model_name)
    texts = []
    ids = []

    with gzip.open("candidates.jsonl.gz", "rt") as f:
        for line in tqdm(f, total=100_000, desc="Synthesizing texts"):
            if line.strip():
                c = json.loads(line)
                texts.append(synthesize_candidate_text(c))
                ids.append(c["candidate_id"])

    print(f"Encoding {len(texts)} candidates with {model_name}...")
    start = time.time()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True
    )
    elapsed = time.time() - start
    print(f"Done in {elapsed/3600:.2f} hours. Shape: {embeddings.shape}")

    np.save(output_path, embeddings)
    # Save ID order so we can join back to features
    with open(output_path.replace(".npy", "_ids.json"), "w") as f:
        json.dump(ids, f)

    return embeddings, ids

# FALLBACK DECISION (from Stage 0.3 benchmark):
# If bge-large < 3hrs on your machine → use it
# If bge-large would take 3-5hrs → use bge-base
# If bge-base would take > 3hrs → use all-MiniLM-L6-v2 AND keep bge-base for top-5K reranking
try:
    batch_encode_candidates("BAAI/bge-large-en-v1.5", "candidate_embeddings_large.npy")
except MemoryError:
    print("⚠ OOM on bge-large, falling back to bge-base")
    batch_encode_candidates("BAAI/bge-base-en-v1.5", "candidate_embeddings_base.npy")
```

### 3.3 — Semantic Similarity Computation

```python
def compute_semantic_scores(embedding_path, jd_embedding_path, ideal_embedding_path):
    embeddings = np.load(embedding_path, mmap_mode="r")   # memory-map = doesn't load all to RAM
    jd_emb = np.load(jd_embedding_path)
    ideal_emb = np.load(ideal_embedding_path)

    # Full JD cosine similarity (embeddings are normalized → dot product = cosine)
    jd_sims = embeddings @ jd_emb           # shape: (100K,)
    ideal_sims = embeddings @ ideal_emb     # shape: (100K,)

    # Blend: 60% full JD, 40% ideal profile
    semantic_scores = 0.6 * jd_sims + 0.4 * ideal_sims

    np.save("semantic_scores.npy", semantic_scores)
    print(f"Semantic scores: min={semantic_scores.min():.3f}, max={semantic_scores.max():.3f}, "
          f"mean={semantic_scores.mean():.3f}")
    return semantic_scores
```

### 3.4 — Per-Role Semantic Score (Max Pooling)

```python
def compute_per_role_scores(jd_embedding, model):
    """
    For each candidate, embed each career role separately and take the max.
    This captures candidates with one stellar relevant role surrounded by unrelated work.
    Runs on top-5K candidates by initial composite score (not all 100K, for speed).
    """
    per_role_scores = {}
    # Load top 5K candidate IDs from intermediate composite scores
    top5k_ids = set(json.load(open("top5k_ids.json")))

    with gzip.open("candidates.jsonl.gz", "rt") as f:
        for line in tqdm(f, total=100_000, desc="Per-role scoring"):
            if not line.strip(): continue
            c = json.loads(line)
            if c["candidate_id"] not in top5k_ids: continue

            role_texts = [r["description"] for r in c["career_history"]]
            if not role_texts:
                per_role_scores[c["candidate_id"]] = 0.0
                continue

            role_embeddings = model.encode(role_texts, normalize_embeddings=True)
            sims = role_embeddings @ jd_embedding
            per_role_scores[c["candidate_id"]] = float(np.max(sims))

    return per_role_scores
```

---

## Stage 4: Honeypot Audit
**Day 7 | Goal: Zero honeypots in top 100 before scoring**

This is now a standalone stage because a honeypot rate >10% means instant disqualification regardless of NDCG.

```python
def audit_honeypots(features_df, threshold=0.15):
    """
    Review all candidates with honeypot_score < threshold.
    Print a sample for manual verification.
    """
    suspects = features_df[features_df["honeypot_score"] < threshold].copy()
    suspects = suspects.sort_values("honeypot_score")

    print(f"Honeypot suspects (score < {threshold}): {len(suspects)}")
    print(f"Expected ~80 from spec. We found {len(suspects)}.")

    # Manual spot-check: print top 10 most suspicious
    for _, row in suspects.head(10).iterrows():
        print(f"\n  {row['candidate_id']}: honeypot_score={row['honeypot_score']:.3f}")

    return suspects["candidate_id"].tolist()

# After running: verify by hand that 5-10 of the most suspicious candidates
# are truly impossible profiles. This is your Stage 4 review prep.
```

**Manual verification checklist:**
- [ ] At least 5 honeypot suspects reviewed by hand against their full JSON
- [ ] Zero honeypots appear in your top-200 candidates (check after initial ranking)
- [ ] If a clearly-good candidate has `honeypot_score < 0.5`, investigate why — may be a detection bug

---

## Stage 5: Multi-Signal Scoring Engine
**Days 8–9 | Goal: Produce an accurate initial composite ranking**

### 5.1 — Experience Band Modifier

```python
def experience_modifier(yoe):
    """
    Soft penalty for experience outside 5-9 year target.
    JD is explicit: 5-9 is a range, not a hard cutoff.
    """
    if 5 <= yoe <= 9:   return 1.00
    if 4 <= yoe < 5:    return 0.90   # slightly junior — borderline
    if 9 < yoe <= 11:   return 0.96   # slightly senior — still fine
    if 3 <= yoe < 4:    return 0.72   # too junior
    if 11 < yoe <= 14:  return 0.88   # over-experienced — probably wants different scope
    if yoe > 14:        return 0.78   # significantly over-experienced
    return 0.50
```

### 5.2 — Hard Disqualifier Gates

Any candidate hitting a disqualifier is capped at 0.12 (ranked but buried). Not zeroed — zero creates exact ties at the bottom which can cause submission validation issues.

```python
def compute_disqualifier_flags(features, candidate):
    signals = candidate["redrob_signals"]
    flags = []

    # 1. Entire career at consulting firms
    if features["consulting_ratio"] > 0.90:
        flags.append("pure_consulting")

    # 2. Zero meaningful hard requirement coverage
    if features["min_hard_req_coverage"] < 0.15:
        flags.append("zero_hard_reqs")

    # 3. Too junior for the role
    if candidate["profile"]["years_of_experience"] < 3:
        flags.append("too_junior")

    # 4. No evidence of production deployment
    if features["deployment_score"] < 0.1 and features["retrieval_ir_score"] < 0.1:
        flags.append("no_production_ml")

    # 5. CV/speech/robotics domain with no IR/NLP overlap
    if features["domain_mismatch_flag"] == 1.0:
        flags.append("wrong_domain")

    # 6. Definitely a honeypot
    if features["is_likely_honeypot"] == 1.0:
        flags.append("honeypot")

    # 7. Outside India, won't relocate (hard logistics block)
    if features["location_score"] < 0.1:
        flags.append("unreachable_location")

    return flags
```

### 5.3 — Composite Relevance Score

```python
def compute_relevance_score(features, semantic_score):
    """
    Weighted composite of all signal groups.
    Weights are deliberately NOT equal — they reflect JD priority.
    """

    # Component: Career trajectory
    # The JD cares more about career trajectory than skills lists
    s_career = (
        0.35 * (1.0 - features["consulting_ratio"]) +
        0.30 * features["deployment_score"] +
        0.20 * features["retrieval_ir_score"] +
        0.10 * features["years_in_product"] +
        0.05 * features["seniority_trend"]
        - 0.10 * features["job_hop_penalty"]
        - 0.08 * features["title_chaser_flag"]
    )
    s_career = max(0.0, min(1.0, s_career))

    # Component: Skills match (with assessment credibility)
    s_skills = (
        0.50 * features["avg_hard_req_coverage"] +
        0.15 * features["min_hard_req_coverage"] +  # weakest-link penalty
        0.15 * features["soft_req_coverage"] +
        0.10 * features["has_relevant_assessments"] * features["avg_relevant_assessment"] +
        0.10 * features["assessment_credibility"]
        - 0.10 * features["domain_mismatch_flag"]
    )
    s_skills = max(0.0, min(1.0, s_skills))

    # Component: Semantic similarity (narrative intent, context beyond keywords)
    s_semantic = float(semantic_score)

    # Component: Education
    s_edu = (
        0.60 * features["edu_tier_score"] +
        0.25 * features["is_cs_adjacent"] +
        0.15 * features["has_postgrad"]
    )

    # Component: Logistics
    s_logistics = (
        0.40 * features["location_score"] +
        0.25 * features["notice_score"] +
        0.20 * features["salary_score"] +
        0.15 * features["work_mode_score"]
    )

    # Final weighted composite
    composite = (
        0.30 * s_career +       # career trajectory — most important per JD
        0.28 * s_skills +       # skills match with credibility discount
        0.22 * s_semantic +     # semantic narrative fit
        0.12 * s_logistics +    # logistics — important but not a tiebreaker
        0.08 * s_edu            # education — signal but not gating
    )

    return composite, {
        "s_career": s_career, "s_skills": s_skills, "s_semantic": s_semantic,
        "s_edu": s_edu, "s_logistics": s_logistics
    }


def compute_final_score(relevance, behavioral_score, honeypot_score, disqualifier_flags, yoe):
    """
    Pipeline:
    1. Apply disqualifier cap
    2. Apply experience modifier
    3. Apply behavioral multiplier
    4. Apply honeypot penalty
    """
    if disqualifier_flags:
        relevance = min(relevance, 0.12)

    # Experience modifier on relevance only (not behavioral)
    relevance *= experience_modifier(yoe)

    # Behavioral multiplier [0.35, 1.0]
    # Even a totally inactive candidate isn't zeroed — they might still be recruitable
    behavioral_multiplier = 0.35 + 0.65 * behavioral_score
    score = relevance * behavioral_multiplier

    # Honeypot penalty (multiplicative)
    score *= honeypot_score

    return max(score, 0.001)   # avoid exact zeros → submission validator issues
```

### 5.4 — Golden Set Validation

Before proceeding to LambdaMART, validate that your scoring makes sense on a manually curated set.

```python
"""
Build your golden set by hand:
  - Read 15 candidate profiles fully alongside the JD
  - Classify each as: strong_fit (2), moderate_fit (1), not_fit (0)
  - Target: ~5 of each

Strong fit profile characteristics:
  - 5-9 years at product companies
  - Some career history with retrieval/ranking/search work
  - Located in India, willing to relocate
  - Active on platform
  - Notice ≤ 60 days

Not fit profile characteristics:
  - Entire career at TCS/Infosys/Wipro
  - ML experience = only NLP/speech/vision without retrieval
  - Located outside India, won't relocate
  - Very junior (<3 years)
  - Honeypot flags
"""

GOLDEN_SET = {
    # Fill these in after manual review of sample_candidates.json
    "CAND_XXXXXXX": 2,   # strong fit
    # ...
}

def validate_golden_set(scores_dict, golden_set):
    strong_scores = [scores_dict[cid] for cid, label in golden_set.items() if label == 2]
    moderate_scores = [scores_dict[cid] for cid, label in golden_set.items() if label == 1]
    not_fit_scores = [scores_dict[cid] for cid, label in golden_set.items() if label == 0]

    print(f"Strong fit scores:  {[f'{s:.3f}' for s in sorted(strong_scores, reverse=True)]}")
    print(f"Moderate scores:    {[f'{s:.3f}' for s in sorted(moderate_scores, reverse=True)]}")
    print(f"Not fit scores:     {[f'{s:.3f}' for s in sorted(not_fit_scores, reverse=True)]}")

    # Hard assertion: every strong fit must outscore every not-fit
    assert min(strong_scores) > max(not_fit_scores), \
        "FAIL: some not-fit candidate outscores a strong-fit candidate"
    print("✅ Golden set validation passed")
```

---

## Stage 6: LambdaMART Re-Ranker
**Days 10–12 | Goal: Learn non-linear signal combinations directly optimizing NDCG**

### 6.1 — Why LambdaMART (and when to drop it)

LambdaMART can discover that `consulting_ratio > 0.8 AND deployment_score < 0.2` is multiplicatively disqualifying, not just additively bad. It optimizes directly for NDCG@10 (50% of your score).

**Decision rule:** Train LambdaMART on Day 11. If its NDCG@10 on your holdout set is ≥ 0.05 better than the Stage 5 weighted sum → use it. If not → ship the weighted sum. Do not use LambdaMART that doesn't improve on your existing ranker.

### 6.2 — Pseudo-Label Generation (offline, 2,500 candidates)

This fixes the critical v1 flaw: we're now labeling 2,500 candidates (5× v1) and labeling from the JD, not from our own scores.

```python
import anthropic, json, time
from tqdm import tqdm

client = anthropic.Anthropic()

JD_SUMMARY = """
Role: Senior AI Engineer at Redrob AI (Series A product company, Pune/Noida India)

STRONG FIT (label 3): 
- 5-9 years at product companies (NOT consulting-only)
- Production experience with vector databases OR embedding-based retrieval OR hybrid search
- Evidence of shipping ML systems to real users at scale
- Located in India or willing to relocate; notice ≤ 90 days

MODERATE FIT (label 2):
- Adjacent skills (data engineering, NLP, some retrieval work) but missing 1-2 hard reqs
- Right career trajectory but consulting background (partial)

WEAK FIT (label 1):
- Has some relevant skills but career is mostly unrelated (consulting, CV/speech)
- Too junior (<4 years) or too senior (>14 years)

NOT A FIT (label 0):
- Entire career at consulting firms with no product-company experience
- Wrong domain (pure CV/speech/robotics with no NLP/IR)
- Outside India, won't relocate
- Honeypot (impossible profile)
- Marketing/HR/non-technical role despite AI keywords
"""

def pseudo_label_candidate(c):
    prompt = f"""
{JD_SUMMARY}

Candidate profile:
- Title: {c['profile']['current_title']} at {c['profile']['current_company']}
- Years of experience: {c['profile']['years_of_experience']}
- Location: {c['profile']['location']}, {c['profile']['country']}
- Summary: {c['profile']['summary'][:500]}
- Recent role: {c['career_history'][0]['description'][:400] if c['career_history'] else 'N/A'}
- Key skills: {', '.join(s['name'] for s in c['skills'][:10])}
- Notice: {c['redrob_signals']['notice_period_days']} days
- Open to work: {c['redrob_signals']['open_to_work_flag']}
- Willing to relocate: {c['redrob_signals']['willing_to_relocate']}

Respond with ONLY a single integer: 0, 1, 2, or 3.
"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}]
        )
        label_str = response.content[0].text.strip()
        return int(label_str[0])  # take first char in case of trailing space
    except:
        return -1   # failed → skip in training

# Sample 2500 candidates: stratify by our Stage 5 composite score quartiles
# so we get good label coverage across the full range
def sample_for_labeling(features_df, n=2500):
    df = features_df.copy()
    # Roughly equal samples from each composite score quartile
    df["quartile"] = pd.qcut(df["composite_score"], 4, labels=[0, 1, 2, 3])
    sampled = df.groupby("quartile").sample(n // 4, random_state=42)
    return sampled["candidate_id"].tolist()
```

### 6.3 — Feature Matrix and Training

```python
import lightgbm as lgb
from sklearn.model_selection import KFold
import numpy as np

LAMBDAMART_FEATURES = [
    # Semantic
    "semantic_score",
    # Career
    "consulting_ratio", "years_in_product", "deployment_score",
    "retrieval_ir_score", "seniority_trend", "job_hop_penalty", "title_chaser_flag",
    # Skills
    "avg_hard_req_coverage", "min_hard_req_coverage", "soft_req_coverage",
    "avg_relevant_assessment", "has_relevant_assessments", "assessment_credibility",
    "domain_mismatch_flag",
    # Individual hard req coverage scores (from skills_features)
    "hard_req_vector_search_infra", "hard_req_embedding_models",
    "hard_req_ranking_evaluation", "hard_req_python_production",
    # Logistics
    "location_score", "notice_score", "salary_score", "work_mode_score",
    # Education
    "edu_tier_score", "is_cs_adjacent", "has_postgrad",
    # Behavioral
    "behavioral_score", "open_to_work", "recency", "responsiveness",
    "track_record", "github_score",
    # Honeypot
    "honeypot_score",
    # Raw
    "experience_modifier_val",
]

def train_lambdamart(X_train, y_train, X_val, y_val):
    # Single query group (all candidates compete for same JD)
    train_group = [len(X_train)]
    val_group = [len(X_val)]

    train_data = lgb.Dataset(X_train, label=y_train, group=train_group,
                              feature_name=LAMBDAMART_FEATURES)
    val_data = lgb.Dataset(X_val, label=y_val, group=val_group,
                            feature_name=LAMBDAMART_FEATURES, reference=train_data)

    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [10, 50],
        "learning_rate": 0.03,
        "num_leaves": 63,
        "min_data_in_leaf": 5,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "lambda_l2": 0.1,
        "verbose": 50,
        "label_gain": [0, 1, 3, 7],  # gains for labels 0,1,2,3 (emphasizes label 3)
    }

    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)]
    )

    return model


def cross_validate_lambdamart(labeled_df, full_feature_df):
    # Merge features for labeled candidates
    labeled_features = full_feature_df[
        full_feature_df["candidate_id"].isin(labeled_df["candidate_id"])
    ].merge(labeled_df, on="candidate_id")

    X = labeled_features[LAMBDAMART_FEATURES].values
    y = labeled_features["label"].values

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    fold_ndcgs = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        model = train_lambdamart(X[train_idx], y[train_idx], X[val_idx], y[val_idx])
        val_pred = model.predict(X[val_idx])
        # Compute NDCG@10 on this fold
        from sklearn.metrics import ndcg_score
        ndcg = ndcg_score([y[val_idx]], [val_pred], k=10)
        fold_ndcgs.append(ndcg)
        print(f"  Fold {fold+1}: NDCG@10 = {ndcg:.4f}")

    print(f"\nMean CV NDCG@10: {np.mean(fold_ndcgs):.4f} ± {np.std(fold_ndcgs):.4f}")
    return np.mean(fold_ndcgs)


# Decision: if CV NDCG@10 > (baseline weighted-sum NDCG@10 + 0.03) → train final model
# Otherwise: skip LambdaMART, use Stage 5 composite as final score
```

---

## Stage 7: Reasoning Generation + Final Output
**Days 12–14 | Goal: Stage 4-proof reasoning and correct CSV format**

### 7.1 — Anchored Reasoning Generation (hallucination-proof)

The v1 reasoning prompt was open-ended. This version **constructs the reasoning from structured profile facts** before passing to the LLM, making hallucination structurally impossible.

```python
def build_reasoning_context(candidate, features, rank, score):
    """
    Build a structured fact card. The LLM can only write what's in this card.
    This prevents hallucination by design.
    """
    signals = candidate["redrob_signals"]
    profile = candidate["profile"]

    # Only list skills with advanced/expert proficiency or verified by assessment
    assessments = signals.get("skill_assessment_scores", {})
    verified_skills = []
    claimed_skills = []
    for s in candidate["skills"]:
        akey = next((k for k in assessments if s["name"].lower() in k.lower()), None)
        if akey:
            verified_skills.append(f"{s['name']} (assessment: {assessments[akey]:.0f}/100)")
        elif s["proficiency"] in ["advanced", "expert"]:
            claimed_skills.append(f"{s['name']} ({s['proficiency']}, self-reported)")

    # Recent role (most relevant to recruiter)
    recent_role = candidate["career_history"][0] if candidate["career_history"] else None
    role_str = (
        f"{recent_role['title']} at {recent_role['company']} "
        f"({recent_role['duration_months']} months, {recent_role['industry']})"
        if recent_role else "N/A"
    )

    # Concerns — be explicit so LLM can mention them
    concerns = []
    if signals["notice_period_days"] > 60:
        concerns.append(f"long notice period ({signals['notice_period_days']} days)")
    if features["location_score"] < 0.65:
        concerns.append(f"not in preferred location ({profile['location']}, relocate: {signals['willing_to_relocate']})")
    if features["consulting_ratio"] > 0.5:
        concerns.append(f"significant consulting background ({features['consulting_ratio']:.0%})")
    if features["recency"] < 0.5:
        concerns.append(f"low platform activity")
    if features["avg_hard_req_coverage"] < 0.6:
        concerns.append("missing some hard requirements")

    return {
        "rank": rank,
        "years": profile["years_of_experience"],
        "current_role": role_str,
        "location": f"{profile['location']}, {profile['country']}",
        "verified_skills": verified_skills[:5],      # top 5
        "claimed_skills": claimed_skills[:5],
        "notice_days": signals["notice_period_days"],
        "open_to_work": signals["open_to_work_flag"],
        "salary_range": f"{signals['expected_salary_range_inr_lpa']['min']}-{signals['expected_salary_range_inr_lpa']['max']} LPA",
        "concerns": concerns,
        "score": score,
    }


def generate_reasoning(candidate, features, rank, score, client):
    ctx = build_reasoning_context(candidate, features, rank, score)

    prompt = f"""
You are writing a recruiter shortlist note. Write exactly 1-2 sentences.

RULES:
- Reference ONLY the facts below. Do not mention any skill, employer, or experience not in this list.
- Be specific: mention actual role names, skill names, numbers.
- Acknowledge concerns if any exist.
- Tone should match rank: rank 1-10 = strong endorsement; rank 50-100 = honest but modest.
- Do not use generic phrases like "strong candidate" or "perfect fit."

FACTS:
- Rank: {ctx['rank']} of 100
- Score: {ctx['score']:.3f}
- Years of experience: {ctx['years']}
- Current: {ctx['current_role']}
- Location: {ctx['location']}
- Verified skills (by platform assessment): {', '.join(ctx['verified_skills']) or 'none'}
- Claimed skills (self-reported advanced/expert): {', '.join(ctx['claimed_skills']) or 'none'}
- Notice period: {ctx['notice_days']} days
- Open to work: {ctx['open_to_work']}
- Salary expectation: {ctx['salary_range']}
- Concerns: {'; '.join(ctx['concerns']) if ctx['concerns'] else 'none noted'}

Write the 1-2 sentence recruiter note now:
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def generate_all_reasoning(top100_candidates, features_dict, scores_dict):
    """Generate reasoning for top 100 + 50 backup candidates (in case of last-minute reranking)."""
    client = anthropic.Anthropic()
    reasoning_cache = {}

    for rank, c in enumerate(tqdm(top100_candidates[:150], desc="Generating reasoning"), start=1):
        cid = c["candidate_id"]
        features = features_dict[cid]
        score = scores_dict[cid]
        reasoning_cache[cid] = generate_reasoning(c, features, rank, score, client)
        time.sleep(0.3)   # rate limit

    json.dump(reasoning_cache, open("reasoning_cache.json", "w"), indent=2)
    print(f"✅ Reasoning generated for {len(reasoning_cache)} candidates")
    return reasoning_cache
```

### 7.2 — Final Ranker (rank.py)

This is the script that must run in ≤5 minutes with no network.

```python
#!/usr/bin/env python3
"""
rank.py — Final ranking script for Redrob Hackathon submission.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runtime target: < 2 minutes (well within 5-minute limit).
Dependencies: numpy, pandas, lightgbm, scikit-learn (no network calls)
"""
import argparse, json, csv, time
import numpy as np
import pandas as pd
import lightgbm as lgb

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="submission.csv")
    args = parser.parse_args()

    t0 = time.time()

    # 1. Load precomputed embeddings + candidate ID order
    print("[1/6] Loading precomputed embeddings...")
    embeddings = np.load("candidate_embeddings.npy", mmap_mode="r")     # memory-mapped
    embedding_ids = json.load(open("candidate_embeddings_ids.json"))
    id_to_idx = {cid: i for i, cid in enumerate(embedding_ids)}

    # 2. Load precomputed feature matrix
    print("[2/6] Loading feature matrix...")
    features_df = pd.read_parquet("features_100k.parquet")
    features_df = features_df.set_index("candidate_id")

    # 3. Compute JD semantic similarity (the only online computation)
    print("[3/6] Computing semantic similarities...")
    jd_emb = np.load("jd_embedding.npy")
    ideal_emb = np.load("ideal_embedding.npy")
    jd_sims = embeddings @ jd_emb
    ideal_sims = embeddings @ ideal_emb
    semantic_scores = 0.6 * jd_sims + 0.4 * ideal_sims

    # Map back to candidate IDs
    features_df["semantic_score"] = [
        semantic_scores[id_to_idx[cid]] for cid in features_df.index
    ]
    features_df["experience_modifier_val"] = features_df["years_of_experience"].apply(experience_modifier)

    # 4. Load LambdaMART model and score
    print("[4/6] Scoring with LambdaMART...")
    model = lgb.Booster(model_file="ranker.lgb")
    X = features_df[LAMBDAMART_FEATURES].values
    raw_scores = model.predict(X)
    features_df["final_score"] = raw_scores

    # Apply honeypot penalty and disqualifier cap AFTER LambdaMART
    # (LambdaMART was trained on clean candidates; honeypots need hard suppression)
    features_df["final_score"] = features_df.apply(
        lambda row: row["final_score"] * row["honeypot_score"] * (
            0.12 if row["disqualifier_hit"] else 1.0
        ), axis=1
    )

    # 5. Sort and select top 100
    print("[5/6] Selecting top 100...")
    ranked = features_df.sort_values(
        ["final_score", "candidate_id"],  # secondary sort = deterministic tie-breaking
        ascending=[False, True]
    ).head(100)

    # 6. Load reasoning and write CSV
    print("[6/6] Writing submission CSV...")
    reasoning_cache = json.load(open("reasoning_cache.json"))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (cid, row) in enumerate(ranked.iterrows(), start=1):
            reasoning = reasoning_cache.get(cid, f"{row.get('current_title', 'Candidate')} with {row.get('years_of_experience', '?')} years of experience.")
            writer.writerow([cid, rank, f"{row['final_score']:.4f}", reasoning])

    elapsed = time.time() - t0
    print(f"✅ Submission written to {args.out} in {elapsed:.1f}s")

    # Self-validation
    validate_submission(args.out)

if __name__ == "__main__":
    main()
```

### 7.3 — Built-in Submission Validator

```python
def validate_submission(filepath):
    """Runs every check from the spec before you upload."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 100, f"❌ Expected 100 rows, got {len(rows)}"

    ranks = [int(r["rank"]) for r in rows]
    assert sorted(ranks) == list(range(1, 101)), "❌ Ranks must be 1-100 exactly once each"

    ids = [r["candidate_id"] for r in rows]
    assert len(set(ids)) == 100, "❌ Duplicate candidate_ids"

    scores = [float(r["score"]) for r in rows]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1] - 1e-6, \
            f"❌ Scores not non-increasing at rank {i+1} → {i+2}: {scores[i]:.4f} > {scores[i+1]:.4f}"

    assert len(set(scores)) > 10, "❌ Suspiciously few unique scores — model may not be differentiating"

    # Check for candidate IDs that look like valid format
    for cid in ids:
        assert cid.startswith("CAND_") and len(cid) == 12, f"❌ Invalid candidate_id format: {cid}"

    # Check reasoning quality (basic)
    reasonings = [r["reasoning"] for r in rows]
    assert all(len(r) > 20 for r in reasonings), "❌ Some reasoning strings are too short"
    assert len(set(reasonings)) > 50, "❌ Too many duplicate reasoning strings — templating detected"

    print(f"✅ Submission validation passed: 100 rows, ranks 1-100, non-increasing scores, unique IDs")
```

---

## 15-Day Implementation Roadmap (Revised)

| Day | Task | Output | Checkpoint |
|-----|------|--------|------------|
| 1 | Stage 0: environment setup, data check, embedding benchmark. Start Stage 1: JD parsing | `jd_parsed.json`, model downloaded | Decision: which embedding model to use |
| 2 | Stage 1 complete: skill taxonomy, JD embedding. Start candidate text synthesis | `jd_embedding.npy`, `skill_groups.py` | Manual check: JD parsed correctly |
| 3 | Stage 2: career + education features | `feature_engineering.py` tested | Unit tests pass for CAND_0000001 |
| 4 | Stage 2: skills features + assessment integration. Start encoding (runs overnight) | Skills feature code done, encoding starts | Encoding ETA confirmed |
| 5 | Stage 2: logistics + behavioral features (with all v1 fixes). Full feature pipeline | `extract_all_features()` complete | Run on sample 1K, spot-check 20 manually |
| 6 | Run full feature extraction on 100K candidates | `features_100k.parquet` | Assert shape: 100K × ~45 features |
| 7 | Stage 3: encoding done (if not overnight). Compute semantic scores. Stage 4: honeypot audit | `semantic_scores.npy`, `honeypot_audit.txt` | Manual verify 10 honeypot suspects |
| 8 | Stage 5: composite scoring + golden set validation | `composite_scores.npy` | Golden set: all strong-fit > all not-fit |
| 9 | **Submit submission #1** (Stage 5 composite, no LambdaMART). Generate preliminary reasoning | `submission_v1.csv` submitted | Validator passes, reasoning reviewed |
| 10 | Stage 6: pseudo-label 2,500 candidates with LLM | `pseudo_labels.csv` | Label distribution: ~10% 3s, 25% 2s, 35% 1s, 30% 0s |
| 11 | Stage 6: train LambdaMART, 5-fold CV. Compare vs Stage 5 baseline | `ranker.lgb` | CV NDCG@10 > baseline + 0.03? |
| 12 | If LambdaMART wins: generate final scores. Stage 7: reasoning generation (anchored) | `reasoning_cache.json` | 150 reasoning strings, spot-check 20 |
| 13 | Build `rank.py` end-to-end. Timing benchmark (<5 min). Edge case testing | `rank.py` | Runtime: target <2 min, hard limit 5 min |
| 14 | **Submit submission #2** (with LambdaMART if it improved, else refined Stage 5). Full review | `submission_v2.csv` submitted | Validator passes |
| 15 | Buffer: fix any issues from review. **Submit submission #3** if improvements found | Final submission | 3rd and final submission |

**Submission strategy:** Submit by Day 9 (Stage 5 composite). This protects you if something breaks in Days 10-14. Submissions #2 and #3 are improvements, not your only hope.

---

## Anti-Patterns Addressed

| Anti-Pattern (v1 flaw) | Fix in v2 |
|---|---|
| LambdaMART trained on its own predictions | Labels generated by LLM from JD context; CV validates improvement over baseline |
| Honeypot formula could misfire on legitimate candidates | Multiplicative penalty accumulation; 6 independent signals; manual audit gate |
| `offer_acceptance_rate = -1` treated as zero | Explicitly handled as 0.5 (neutral/unknown) |
| Behavioral weights didn't prioritize `open_to_work` | `open_to_work` is now 25% of behavioral score (was ~8% in v1) |
| Assessment scores averaged into single number | Per-requirement assessment matching; credibility penalty for contradicted expert claims |
| `preferred_work_mode` signal unused | Added as `work_mode_score` in logistics features |
| `compute_range_overlap` undefined | Implemented correctly with partial-credit for near-misses |
| Reasoning prompt was open-ended | Structured fact card passed to LLM; can only reference profile facts |
| No fallback if BGE-large is too slow | Speed benchmark on Day 1; documented fallback chain to bge-base → MiniLM |
| Timeline backloaded | First submission on Day 9; LambdaMART is an improvement layer, not a dependency |

---

## File Structure for Submission Repo

```
redrob-ranker/
├── README.md                        # Setup + single command to reproduce
├── requirements.txt                 # Pinned versions
├── submission_metadata.yaml         # Mirror of portal metadata
│
├── precompute/
│   ├── 01_parse_jd.py               # Stage 1: JD parsing + skill taxonomy
│   ├── 02_encode_candidates.py      # Stage 3: batch embedding (runs offline)
│   ├── 03_extract_features.py       # Stage 2: all feature extraction
│   ├── 04_compute_semantics.py      # Stage 3: cosine similarity computation
│   ├── 05_honeypot_audit.py         # Stage 4: honeypot detection report
│   ├── 06_generate_pseudolabels.py  # Stage 6: LLM pseudo-labeling (needs API key)
│   ├── 07_train_lambdamart.py       # Stage 6: LambdaMART training
│   └── 08_generate_reasoning.py     # Stage 7: anchored reasoning generation
│
├── rank.py                          # RANKING STEP: runs in < 5 min, no network
├── validate_submission.py           # Spec-compliant validator
│
├── artifacts/                       # Pre-computed (committed to repo or documented to regenerate)
│   ├── jd_parsed.json
│   ├── jd_embedding.npy
│   ├── ideal_embedding.npy
│   ├── features_100k.parquet
│   ├── candidate_embeddings.npy
│   ├── candidate_embeddings_ids.json
│   ├── ranker.lgb
│   └── reasoning_cache.json
│
└── tests/
    ├── test_features.py             # Unit tests for feature extraction
    ├── test_honeypot.py             # Honeypot detection unit tests
    └── test_golden_set.py           # Golden set validation
```

**One-command reproduction (for README):**
```bash
# Pre-computation (run once, ~3-6 hours total):
python precompute/01_parse_jd.py
python precompute/02_encode_candidates.py   # longest step
python precompute/03_extract_features.py
python precompute/04_compute_semantics.py
python precompute/05_honeypot_audit.py
python precompute/06_generate_pseudolabels.py  # requires ANTHROPIC_API_KEY
python precompute/07_train_lambdamart.py
python precompute/08_generate_reasoning.py     # requires ANTHROPIC_API_KEY

# Ranking step (< 5 minutes, CPU only, no network):
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```
