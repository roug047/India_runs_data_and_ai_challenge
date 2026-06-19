# Redrob AI — Intelligent Candidate Ranking System
## Architecture v3.0 — Competition-Final (15-Day Build Plan)

---

## What Changed From v2 and Why

This v3 fixes every concrete gap identified by both reviewers, adds the improvements both agreed on, and resolves the ambiguities the organizers' docs expose. Changes are marked inline. The underlying philosophy (recruiter emulation, not keyword search) is unchanged and correct.

**Bugs fixed from v2:**
1. Honeypot rate of final top-100 was never checked before upload → **added explicit assertion in validator**
2. `rank.py` referenced `years_of_experience`, `current_title`, `disqualifier_hit` that weren't persisted in parquet → **all raw fields now explicitly saved in Stage 2**
3. Per-role max-pooling score (Stage 3.4) was computed and never used → **wired into feature matrix and LambdaMART**
4. Location disqualifier was stricter than the JD: NRI + willing_to_relocate was blocked → **added relocate-aware branch**
5. `langchain_only_under_12mo` and `no_code_in_18mo` disqualifiers were parsed but never checked → **fully implemented in Stage 5.2**
6. LambdaMART CV only validated NDCG@10, not the full composite metric → **CV now computes all four metric components**
7. Sandbox / demo link requirement (spec Section 10.5) was missing from the roadmap → **added Day 13 sandbox task**
8. Company size bias: `10001+` firms include Google, Amazon, etc. → **size × industry interaction now used**

**Improvements added from both reviewers:**
- BM25 + semantic hybrid retrieval for top-10K candidate selection
- Three-model LambdaMART ensemble (recruiter labels / hard-req labels / semantic labels)
- Contradiction-based honeypot detection (four new signal categories)
- JD extraction confidence scores per field
- Consulting ratio × product ratio instead of consulting ratio alone
- Pairwise training samples alongside listwise for LambdaMART

---

## System Architecture: 7 Stages

```
Stage 0: Pre-flight & Environment Setup           (Day 1)
Stage 1: JD Intelligence Layer                    (Days 1–2)
Stage 2: Candidate Feature Engineering            (Days 3–6)
Stage 3: Hybrid Retrieval Index                   (Days 4–7, parallel)
Stage 4: Honeypot Detection                       (Day 7)
Stage 5: Multi-Signal Scoring Engine              (Days 8–9)
Stage 6: LambdaMART Ensemble Re-Ranker            (Days 10–12)
Stage 7: Reasoning Generation + Output            (Days 12–14)
Day 13: Sandbox deployment (mandatory per spec)
Day 15: Buffer
```

---

## Stage 0: Pre-flight & Environment Setup
**Day 1 | Goal: Validate environment and data before building anything**

### 0.1 — Environment Validation

```bash
python3 -c "import sys; print(sys.version)"
python3 -c "import psutil; print(f'RAM: {psutil.virtual_memory().total / 1e9:.1f} GB')"

pip install sentence-transformers lightgbm scikit-learn pandas numpy pyarrow tqdm rank_bm25 anthropic
```

### 0.2 — Data Integrity + Distribution Analysis

```python
import gzip, json
from collections import Counter
from datetime import date

REFERENCE_DATE = date(2026, 6, 6)  # fix to dataset reference date

candidates = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in f:
        if line.strip():
            candidates.append(json.loads(line))

assert len(candidates) == 100_000, f"Expected 100K, got {len(candidates)}"
ids = [c["candidate_id"] for c in candidates]
assert len(set(ids)) == 100_000, "Duplicate IDs found!"

# ADDED v3: null-rate and distribution analysis — sparse features overfit LambdaMART
yoe = [c["profile"]["years_of_experience"] for c in candidates]
countries = Counter(c["profile"]["country"] for c in candidates)
work_modes = Counter(c["redrob_signals"]["preferred_work_mode"] for c in candidates)
open_to_work = sum(1 for c in candidates if c["redrob_signals"]["open_to_work_flag"])
has_assessments = sum(1 for c in candidates if c["redrob_signals"]["skill_assessment_scores"])
has_github = sum(1 for c in candidates if c["redrob_signals"]["github_activity_score"] != -1)

print(f"YOE: min={min(yoe):.1f}, median={sorted(yoe)[50000]:.1f}, max={max(yoe):.1f}")
print(f"Countries top-5: {countries.most_common(5)}")
print(f"Work modes: {dict(work_modes)}")
print(f"Open to work: {open_to_work / 1000:.1f}%")
print(f"Have assessments: {has_assessments / 1000:.1f}%")
print(f"Have GitHub: {has_github / 1000:.1f}%")

# Skill text length distribution (proxy for profile completeness)
text_lens = [
    sum(len(r["description"]) for r in c["career_history"])
    for c in candidates
]
print(f"Career desc length: p10={sorted(text_lens)[10000]}, median={sorted(text_lens)[50000]}, p90={sorted(text_lens)[90000]}")
```

### 0.3 — Embedding Speed Benchmark

```python
import time
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")
sample_texts = ["sample candidate text " * 50] * 128
start = time.time()
_ = model.encode(sample_texts, batch_size=64)
elapsed = time.time() - start

rate = 128 / elapsed
est_hours = 100_000 / rate / 3600
print(f"bge-base rate: {rate:.0f} candidates/sec → 100K ETA: {est_hours:.1f}h")
# Decision: bge-base < 1.5h → use bge-large | 1.5-3h → use bge-base | >3h → MiniLM
```

---

## Stage 1: JD Intelligence Layer
**Days 1–2 | Goal: Extract structured meaning including implied signals, with confidence scores**

### 1.1 — LLM-Powered JD Parsing (offline, one-time) with Confidence Scores

**v3 change:** Each extracted field now includes a confidence score and evidence string. This prevents silent hallucination from propagating downstream.

```python
import anthropic, json

JD_TEXT = open("job_description.md").read()
client = anthropic.Anthropic()

parse_prompt = f"""
Parse the following job description into the exact JSON schema below.
Include implicit signals — "shipped to real users" implies production_deployment_required=true.
For each field, also provide a confidence (0.0-1.0) and the exact JD text that supports it.
Respond with ONLY valid JSON, no markdown fences, no explanation.

JD:
{JD_TEXT}

Schema:
{{
  "role_title": {{"value": "...", "confidence": 0.99, "evidence": "..."}},
  "experience_range": {{"value": {{"min": 5, "max": 9}}, "confidence": 0.99, "evidence": "5-9 years"}},
  "hard_requirements": {{
    "value": ["vector_search_infra", "embedding_models", "ranking_evaluation", "python_production"],
    "confidence": 0.97,
    "evidence": "Things you absolutely need..."
  }},
  "soft_requirements": {{
    "value": ["llm_finetuning", "learning_to_rank", "hr_tech_experience", "distributed_systems", "hybrid_retrieval"],
    "confidence": 0.90,
    "evidence": "Things we'd like you to have..."
  }},
  "disqualifier_patterns": {{
    "value": [
      "pure_consulting_career",
      "no_production_deployment",
      "langchain_only_under_12mo",
      "no_code_in_18mo",
      "cv_speech_robotics_only",
      "closed_source_only_5yr"
    ],
    "confidence": 0.99,
    "evidence": "Things we explicitly do NOT want..."
  }},
  "preferred_locations": {{"value": ["Pune", "Noida", "Hyderabad", "Mumbai", "Delhi NCR"], "confidence": 0.99, "evidence": "..."}},
  "acceptable_countries": {{"value": ["India"], "confidence": 0.95, "evidence": "Outside India: case-by-case, we don't sponsor visas"}},
  "notice_period_ideal_days": {{"value": 30, "confidence": 0.99, "evidence": "..."}},
  "notice_period_max_days": {{"value": 90, "confidence": 0.85, "evidence": "30+ day notice candidates still in scope but bar gets higher"}},
  "salary_band_inr_lpa": {{"value": null, "confidence": 0.0, "evidence": "not mentioned in JD — leave null"}},
  "preferred_work_modes": {{"value": ["hybrid", "flexible", "onsite"], "confidence": 0.90, "evidence": "Hybrid — flexible cadence"}},
  "culture_flags": {{"value": ["startup_ready", "ships_fast", "no_title_chasing", "writes_async"], "confidence": 0.95, "evidence": "..."}},
  "production_deployment_required": {{"value": true, "confidence": 0.99, "evidence": "pure research → will not move forward"}},
  "ideal_profile_summary": {{"value": "...", "confidence": 0.95, "evidence": "How to read between the lines"}}
}}
"""

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=3000,
    messages=[{"role": "user", "content": parse_prompt}]
)

raw = response.content[0].text.strip()
jd_parsed_with_confidence = json.loads(raw)

# Strip to values-only dict for pipeline use; keep full version for audit
jd_parsed = {k: v["value"] for k, v in jd_parsed_with_confidence.items()}
json.dump(jd_parsed, open("jd_parsed.json", "w"), indent=2)
json.dump(jd_parsed_with_confidence, open("jd_parsed_confidence.json", "w"), indent=2)
print("✅ JD parsed with confidence scores.")

# Manual check: any field with confidence < 0.7 needs human review
low_conf = {k: v for k, v in jd_parsed_with_confidence.items() if v.get("confidence", 1.0) < 0.7}
if low_conf:
    print(f"⚠ Low-confidence fields (REVIEW MANUALLY): {list(low_conf.keys())}")
# Note: salary_band_inr_lpa is correctly null — the JD doesn't state salary figures.
# Do NOT guess or hallucinate a range. salary_score will use 0.5 neutral for all candidates.
```

### 1.2 — Skill Taxonomy

```python
SKILL_GROUPS = {
    # Hard requirement groups
    "vector_search_infra": [
        "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
        "elasticsearch", "pgvector", "chromadb", "annoy", "vespa", "typesense",
        "vector database", "ann", "approximate nearest neighbor", "hnsw", "haystack"
    ],
    "embedding_models": [
        "sentence-transformers", "sentence transformers", "bge", "e5", "openai embeddings",
        "ada-002", "instructor", "gte", "clip", "cohere embed", "text embeddings",
        "dense retrieval", "bi-encoder", "dual encoder", "semantic search", "embeddings"
    ],
    "ranking_evaluation": [
        "ndcg", "mrr", "map", "mean average precision", "a/b testing", "a/b test",
        "learning to rank", "ltr", "lambdamart", "xgboost ranker", "listwise",
        "pairwise", "offline evaluation", "online evaluation", "ranking metrics",
        "information retrieval", "recall@k", "precision@k", "hit rate", "ranknet"
    ],
    "python_production": [
        "python", "fastapi", "flask", "django", "pydantic", "asyncio", "celery",
        "gunicorn", "uvicorn", "pytest", "mypy", "production python"
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
        "mindtree", "hcl technologies", "hcltech", "l&t infotech", "persistent systems"
    ],
    "cv_speech_robotics": [
        "computer vision", "image classification", "object detection", "yolo", "opencv",
        "speech recognition", "asr", "tts", "text to speech", "robotics", "ros",
        "point cloud", "lidar", "slam", "autonomous driving"
    ],
    "langchain_llm_wrapper_only": [
        "langchain", "llamaindex", "llama-index", "haystack pipeline", "openai api",
        "anthropic api", "gpt-4", "chatgpt", "prompt engineering"
    ]
}

SKILL_TO_GROUP = {}
for group, terms in SKILL_GROUPS.items():
    for term in terms:
        SKILL_TO_GROUP[term.lower()] = group
```

### 1.3 — JD Embedding (offline, one-time)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-large-en-v1.5")
JD_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

jd_full_text = open("job_description.md").read()
ideal_candidate_text = jd_parsed["ideal_profile_summary"]

jd_embedding = model.encode(JD_QUERY_PREFIX + jd_full_text, normalize_embeddings=True)
ideal_embedding = model.encode(JD_QUERY_PREFIX + ideal_candidate_text, normalize_embeddings=True)

np.save("jd_embedding.npy", jd_embedding)
np.save("ideal_embedding.npy", ideal_embedding)
print(f"✅ JD embeddings: {jd_embedding.shape}")
```

---

## Stage 2: Candidate Feature Engineering
**Days 3–6 | Goal: All features extracted, persisted, and validated**

**v3 critical fix:** The parquet file now explicitly saves every column that `rank.py` and Stage 5/6 reference, including raw profile fields. No more KeyError at submission time.

### 2.1 — Feature Engineering Master Runner

```python
import pandas as pd
import numpy as np
import json, gzip
from datetime import date
from tqdm import tqdm

REFERENCE_DATE = date(2026, 6, 6)

def extract_all_features(candidate, jd_parsed):
    features = {}
    features.update(career_features(candidate))
    features.update(skills_features(candidate, jd_parsed))
    features.update(education_features(candidate))
    features.update(logistics_features(candidate, jd_parsed))
    features.update(behavioral_features(candidate["redrob_signals"]))
    features.update(honeypot_features(candidate))

    # FIXED v3: Explicitly persist raw profile fields needed by rank.py and Stage 5
    features["candidate_id"] = candidate["candidate_id"]
    features["years_of_experience"] = candidate["profile"]["years_of_experience"]
    features["current_title"] = candidate["profile"]["current_title"]
    features["current_company"] = candidate["profile"]["current_company"]
    features["current_company_size"] = candidate["profile"]["current_company_size"]
    features["location"] = candidate["profile"]["location"]
    features["country"] = candidate["profile"]["country"]

    return features

all_features = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in tqdm(f, total=100_000):
        if line.strip():
            c = json.loads(line)
            all_features.append(extract_all_features(c, jd_parsed))

df = pd.DataFrame(all_features)
df.to_parquet("features_100k.parquet", index=False)
print(f"✅ Features: {df.shape[0]} rows × {df.shape[1]} cols")

# Sanity check: required columns all present
required_cols = [
    "candidate_id", "years_of_experience", "current_title", "current_company",
    "consulting_ratio", "years_in_product", "deployment_score", "retrieval_ir_score",
    "honeypot_score", "is_likely_honeypot", "disqualifier_hit", "disqualifier_reasons",
    "behavioral_score", "location_score", "avg_hard_req_coverage"
]
for col in required_cols:
    assert col in df.columns, f"MISSING COLUMN: {col}"
print("✅ All required columns present in parquet.")
```

### 2.2 — Career Features

**v3 change:** Consulting penalty now uses `consulting_ratio × (1 - product_ratio)` — a candidate with 4 years consulting + 4 years product is not penalized the same as one with 8 years pure consulting. Company size now uses `size × industry` interaction.

```python
CONSULTING_FIRMS_SET = set(SKILL_GROUPS["consulting_firms"])

# FIXED v3: Company size now uses industry context
# Large tech product companies (Google, Amazon, etc.) are NOT consulting
LARGE_PRODUCT_COMPANIES = {
    "google", "amazon", "microsoft", "meta", "apple", "netflix", "flipkart",
    "paytm", "swiggy", "zomato", "ola", "nykaa", "phonepe", "razorpay",
    "meesho", "zepto", "cred", "groww", "zerodha"
}

def get_company_size_score(company_name, size_band, industry):
    company_lower = company_name.lower()
    is_consulting = any(firm in company_lower for firm in CONSULTING_FIRMS_SET)
    is_known_product = any(prod in company_lower for prod in LARGE_PRODUCT_COMPANIES)

    base = {
        "1-10": 0.45, "11-50": 0.72, "51-200": 0.85,
        "201-500": 0.90, "501-1000": 0.85, "1001-5000": 0.78,
        "5001-10000": 0.65, "10001+": 0.50
    }.get(size_band, 0.5)

    if is_consulting:
        return base * 0.4
    if is_known_product and size_band == "10001+":
        return 0.75  # large product company — not the negative we assumed
    if "startup" in industry.lower() or "saas" in industry.lower():
        return min(base + 0.1, 1.0)
    return base


PRODUCTION_ML_KEYWORDS = [
    "shipped", "production", "deployed", "serving", "inference", "api endpoint",
    "real users", "at scale", "latency", "throughput", "monitoring", "a/b test",
    "retrieval", "ranking", "search", "recommendation", "embedding", "vector"
]
RETRIEVAL_IR_KEYWORDS = [
    "retrieval", "ranking", "search", "recommendation", "ndcg", "mrr", "map",
    "faiss", "milvus", "elasticsearch", "opensearch", "vector db", "hybrid search",
    "bm25", "dense retrieval", "sparse retrieval", "reranking", "learning to rank"
]

def is_consulting(company_name):
    cl = company_name.lower()
    return any(firm in cl for firm in CONSULTING_FIRMS_SET)

def compute_seniority_score(title):
    title_lower = title.lower()
    for keyword, score in [
        ("vp", 8), ("director", 7), ("principal", 6), ("staff", 5), ("lead", 5),
        ("senior", 4), ("sr.", 4), ("engineer", 3), ("developer", 3), ("analyst", 2),
        ("associate", 2), ("junior", 1), ("jr.", 1), ("intern", 0), ("trainee", 0)
    ]:
        if keyword in title_lower:
            return score
    return 3  # default = mid-level

def career_features(candidate):
    history = candidate["career_history"]
    profile = candidate["profile"]

    total_months = sum(r["duration_months"] for r in history)
    if total_months == 0:
        return {k: 0.0 for k in [
            "consulting_ratio", "product_ratio", "consulting_penalty",
            "years_in_product", "deployment_score", "retrieval_ir_score",
            "seniority_trend", "job_hop_penalty", "title_chaser_flag",
            "current_size_score", "n_roles"
        ]}

    # Consulting vs product breakdown
    consulting_months = sum(r["duration_months"] for r in history if is_consulting(r["company"]))
    product_months = total_months - consulting_months
    consulting_ratio = consulting_months / max(total_months, 1)
    product_ratio = product_months / max(total_months, 1)

    # FIXED v3: penalty is consulting_ratio × (1 - product_ratio)
    # Pure consulting career: 1.0 × 1.0 = 1.0 (full penalty)
    # Mixed (4yr consulting + 4yr product): 0.5 × 0.5 = 0.25 (minimal penalty)
    consulting_penalty = consulting_ratio * (1 - product_ratio)

    years_in_product = product_months / 12

    # Deployment and retrieval signals from descriptions
    all_descriptions = " ".join(r["description"].lower() for r in history)
    prod_ml_hits = sum(1 for kw in PRODUCTION_ML_KEYWORDS if kw in all_descriptions)
    retrieval_ir_hits = sum(1 for kw in RETRIEVAL_IR_KEYWORDS if kw in all_descriptions)

    n_roles = max(len(history), 1)
    deployment_score = min(prod_ml_hits / (n_roles * 3), 1.0)
    retrieval_ir_score = min(retrieval_ir_hits / (n_roles * 3), 1.0)

    # Seniority trend
    sorted_history = sorted(history, key=lambda r: r["start_date"])
    seniority_scores = [compute_seniority_score(r["title"]) for r in sorted_history]
    if len(seniority_scores) >= 2:
        seniority_trend = (seniority_scores[-1] - seniority_scores[0]) / max(len(seniority_scores), 1)
        seniority_trend = max(-1, min(1, seniority_trend / 3))
    else:
        seniority_trend = 0.0

    # Job hopping
    cutoff = "2018-06-01"
    recent_roles = [r for r in history if r["start_date"] >= cutoff and not r["is_current"]]
    short_stints = sum(1 for r in recent_roles if r["duration_months"] < 18)
    job_hop_penalty = min(short_stints / 3, 1.0)

    # Company size (with industry context fix)
    current_role = next((r for r in history if r.get("is_current")), history[0])
    current_size_score = get_company_size_score(
        profile["current_company"],
        profile["current_company_size"],
        profile.get("current_industry", "")
    )

    # Title chaser
    title_chaser = (
        len(history) >= 4
        and seniority_scores[-1] <= seniority_scores[0]
        and short_stints >= 2
    )

    return {
        "consulting_ratio": consulting_ratio,
        "product_ratio": product_ratio,
        "consulting_penalty": consulting_penalty,
        "years_in_product": min(years_in_product / 8, 1.0),
        "deployment_score": deployment_score,
        "retrieval_ir_score": retrieval_ir_score,
        "seniority_trend": (seniority_trend + 1) / 2,
        "job_hop_penalty": job_hop_penalty,
        "title_chaser_flag": float(title_chaser),
        "current_size_score": current_size_score,
        "n_roles": n_roles,
    }
```

### 2.3 — Skills Features (with Assessment Credibility)

```python
def hard_req_coverage(candidate, jd_parsed):
    skills_lower = {s["name"].lower(): s for s in candidate["skills"]}
    descriptions = " ".join(r["description"].lower() for r in candidate["career_history"])
    assessments_lower = {k.lower(): v for k, v in
                         candidate["redrob_signals"].get("skill_assessment_scores", {}).items()}

    coverage = {}
    for req_group in jd_parsed["hard_requirements"]:
        group_terms = SKILL_GROUPS.get(req_group, [])
        score = 0.0
        for term in group_terms:
            # Assessment (verified — highest weight)
            for akey, aval in assessments_lower.items():
                if term in akey or akey in term:
                    if aval >= 70:   score = max(score, 1.0)
                    elif aval >= 50: score = max(score, 0.8)
                    elif aval >= 30: score = max(score, 0.5)
                    else:            score = max(score, 0.2)

            # Self-reported skill
            if term in skills_lower:
                s = skills_lower[term]
                prof_map = {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.75, "expert": 0.9}
                duration_bonus = min(s.get("duration_months", 0) / 36, 0.1)
                skill_score = prof_map[s["proficiency"]] + duration_bonus
                # Unverified expert claim → credibility discount
                if s["proficiency"] == "expert" and not any(
                    term in akey or akey in term for akey in assessments_lower
                ):
                    skill_score *= 0.75
                score = max(score, skill_score)

            # Career description mention (lowest credibility)
            if term in descriptions:
                score = max(score, 0.4)

        coverage[f"hard_req_{req_group}"] = min(score, 1.0)
    return coverage


def assessment_credibility_score(candidate):
    skills = candidate["skills"]
    assessments = {k.lower(): v for k, v in
                   candidate["redrob_signals"].get("skill_assessment_scores", {}).items()}
    inflation_hits, checks = 0, 0
    for skill in skills:
        if skill["proficiency"] in ["expert", "advanced"]:
            checks += 1
            matched_score = next((v for k, v in assessments.items()
                                  if skill["name"].lower() in k or k in skill["name"].lower()), None)
            if matched_score is not None:
                if skill["proficiency"] == "expert" and matched_score < 40:
                    inflation_hits += 2
                elif skill["proficiency"] == "advanced" and matched_score < 25:
                    inflation_hits += 1
    if checks == 0:
        return 0.8
    return max(0.1, 1.0 - inflation_hits / (checks * 2))


def skills_features(candidate, jd_parsed):
    coverage = hard_req_coverage(candidate, jd_parsed)
    hard_scores = list(coverage.values())
    avg_hard_coverage = sum(hard_scores) / max(len(hard_scores), 1)
    min_hard_coverage = min(hard_scores) if hard_scores else 0.0

    skills_text = " ".join(s["name"].lower() for s in candidate["skills"]) + " " + \
                  " ".join(r["description"].lower() for r in candidate["career_history"])
    soft_hits = sum(1 for group in jd_parsed["soft_requirements"]
                    if any(term in skills_text for term in SKILL_GROUPS.get(group, [])))
    soft_coverage = soft_hits / max(len(jd_parsed["soft_requirements"]), 1)

    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})
    all_jd_terms = set()
    for group in jd_parsed["hard_requirements"] + jd_parsed["soft_requirements"]:
        all_jd_terms.update(SKILL_GROUPS.get(group, []))
    jd_relevant_assessments = [v for k, v in assessments.items()
                                if any(term in k.lower() or k.lower() in term
                                       for term in all_jd_terms)]
    avg_relevant_assessment = (sum(jd_relevant_assessments) / len(jd_relevant_assessments)
                                if jd_relevant_assessments else -1)

    # Domain mismatch: heavy CV/speech/robotics without IR/NLP overlap
    cv_speech_hits = sum(1 for term in SKILL_GROUPS["cv_speech_robotics"] if term in skills_text)
    ir_ml_hits = sum(1 for group in ["vector_search_infra", "embedding_models",
                                      "ranking_evaluation", "hybrid_retrieval"]
                     for term in SKILL_GROUPS[group] if term in skills_text)
    domain_mismatch = float(cv_speech_hits > 3 and ir_ml_hits < 2)

    # LangChain-only detection (maps to disqualifier)
    langchain_hits = sum(1 for term in SKILL_GROUPS["langchain_llm_wrapper_only"]
                         if term in skills_text)
    has_pre_llm_ml = ir_ml_hits >= 2 or avg_relevant_assessment > 50

    return {
        **coverage,
        "avg_hard_req_coverage": avg_hard_coverage,
        "min_hard_req_coverage": min_hard_coverage,
        "soft_req_coverage": soft_coverage,
        "avg_relevant_assessment": max(avg_relevant_assessment, 0) / 100,
        "has_relevant_assessments": float(len(jd_relevant_assessments) > 0),
        "assessment_credibility": assessment_credibility_score(candidate),
        "domain_mismatch_flag": domain_mismatch,
        "langchain_only_flag": float(langchain_hits >= 2 and not has_pre_llm_ml),
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
        return {"edu_tier_score": 0.35, "is_cs_adjacent": 0.0, "has_postgrad": 0.0, "edu_recency": 0.5}
    best = max(edu, key=lambda e: TIER_SCORE.get(e.get("tier", "unknown"), 0.45))
    tier_score = TIER_SCORE.get(best.get("tier", "unknown"), 0.45)
    field = best.get("field_of_study", "").lower()
    is_cs = float(any(f in field for f in CS_ADJACENT_FIELDS))
    degree = best.get("degree", "").lower()
    has_postgrad = float(any(d in degree for d in ["m.tech", "mtech", "m.s.", "ms", "mba", "phd", "ph.d", "master"]))
    end_year = best.get("end_year", 2000)
    edu_recency = max(0, min(1, (end_year - 2000) / 20))
    return {
        "edu_tier_score": tier_score,
        "is_cs_adjacent": is_cs,
        "has_postgrad": has_postgrad,
        "edu_recency": edu_recency,
    }
```

### 2.5 — Logistics Features

**v3 fix:** Non-India candidates who are willing to relocate are no longer hard-blocked. The JD says "case-by-case" for outside India, not automatic reject.

```python
PREFERRED_LOCS = {"pune", "noida", "hyderabad", "mumbai", "delhi", "ncr",
                  "gurgaon", "gurugram", "bengaluru", "bangalore"}

def salary_fit(candidate_range, jd_range):
    """Correct overlap formula. Returns 0.5 (neutral) if jd_range is None."""
    if jd_range is None:
        return 0.5  # JD doesn't state salary — don't penalize anyone
    cmin, cmax = candidate_range["min"], candidate_range["max"]
    jmin, jmax = jd_range["min"], jd_range["max"]
    overlap_low, overlap_high = max(cmin, jmin), min(cmax, jmax)
    if overlap_high >= overlap_low:
        return min((overlap_high - overlap_low) / max(jmax - jmin, 1), 1.0)
    gap = overlap_low - overlap_high
    return max(0.0, 1.0 - gap / max(jmax - jmin, 1))

def logistics_features(candidate, jd_parsed):
    signals = candidate["redrob_signals"]
    profile = candidate["profile"]
    loc_lower = profile["location"].lower()
    country_lower = profile["country"].lower()
    in_preferred = any(city in loc_lower for city in PREFERRED_LOCS)

    if in_preferred:
        location_score = 1.0
    elif country_lower == "india" and signals["willing_to_relocate"]:
        location_score = 0.65
    elif country_lower == "india":
        location_score = 0.35
    elif signals["willing_to_relocate"]:
        # FIXED v3: JD says "outside India: case-by-case" — willing NRIs get a fair score
        location_score = 0.30
    else:
        location_score = 0.05  # outside India, won't relocate → real barrier

    notice = signals["notice_period_days"]
    if notice <= 15:   notice_score = 1.0
    elif notice <= 30: notice_score = 0.95
    elif notice <= 60: notice_score = 0.7
    elif notice <= 90: notice_score = 0.45
    else:              notice_score = 0.15

    jd_sal = jd_parsed.get("salary_band_inr_lpa")  # may be null
    sal_range = signals["expected_salary_range_inr_lpa"]
    salary_score = salary_fit(sal_range, jd_sal)

    preferred_mode = signals["preferred_work_mode"]
    jd_modes = set(jd_parsed["preferred_work_modes"])
    if preferred_mode in jd_modes or preferred_mode == "flexible":
        work_mode_score = 1.0
    elif preferred_mode == "onsite" and "hybrid" in jd_modes:
        work_mode_score = 0.8
    elif preferred_mode == "remote":
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

### 2.6 — Behavioral Features

```python
def behavioral_features(signals):
    last_active = date.fromisoformat(signals["last_active_date"])
    days_inactive = (REFERENCE_DATE - last_active).days
    recency = max(0.0, 1.0 - days_inactive / 120)
    open_to_work = float(signals["open_to_work_flag"])

    response_rate = signals["recruiter_response_rate"]
    avg_response_hrs = signals["avg_response_time_hours"]
    response_time_score = max(0.0, 1.0 - avg_response_hrs / 72)
    responsiveness = 0.65 * response_rate + 0.35 * response_time_score

    apps_30d = min(signals["applications_submitted_30d"] / 8, 1.0)
    saved_30d = min(signals["saved_by_recruiters_30d"] / 10, 1.0)

    interview_completion = signals["interview_completion_rate"]
    offer_acceptance_raw = signals["offer_acceptance_rate"]
    offer_acceptance = 0.5 if offer_acceptance_raw == -1 else offer_acceptance_raw  # -1 = no history
    track_record = 0.5 * interview_completion + 0.5 * offer_acceptance

    credibility = (
        0.40 * float(signals["verified_email"]) +
        0.30 * float(signals["verified_phone"]) +
        0.20 * (signals["profile_completeness_score"] / 100) +
        0.10 * float(signals["linkedin_connected"])
    )

    github_raw = signals["github_activity_score"]
    if github_raw == -1:   github_score = 0.4
    elif github_raw >= 70: github_score = 1.0
    elif github_raw >= 40: github_score = 0.7
    elif github_raw >= 15: github_score = 0.5
    else:                  github_score = 0.3

    behavioral = (
        0.25 * open_to_work +
        0.22 * responsiveness +
        0.18 * recency +
        0.12 * track_record +
        0.10 * credibility +
        0.08 * apps_30d +
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

### 2.7 — Honeypot Detection (expanded with contradiction signals)

**v3 change:** Added four new signal categories from reviewer 2: role mismatch, timeline inconsistencies, skill-career mismatch, and assessment contradiction — on top of the existing six v2 signals.

```python
from datetime import datetime

def honeypot_features(candidate):
    profile = candidate["profile"]
    history = candidate["career_history"]
    skills = candidate["skills"]
    signals = candidate["redrob_signals"]
    yoe = profile["years_of_experience"]
    penalty = 1.0

    # === Original 6 signals ===

    # Signal 1: Experience > company age
    current_role = next((r for r in history if r.get("is_current")), None)
    if current_role:
        try:
            company_start = datetime.strptime(current_role["start_date"], "%Y-%m-%d")
            if yoe > (REFERENCE_DATE.year - company_start.year + 5):
                penalty *= 0.15
        except:
            pass

    # Signal 2: Recent employer, impossibly long tenure
    if current_role and current_role["duration_months"] > yoe * 12 * 0.9:
        penalty *= 0.2

    # Signal 3: Zero-duration expert skills
    zero_duration_experts = [s for s in skills
                              if s["proficiency"] == "expert" and s.get("duration_months", 0) == 0]
    if len(zero_duration_experts) >= 2:   penalty *= 0.2
    elif len(zero_duration_experts) == 1: penalty *= 0.6

    # Signal 4: Assessment contradicts expert self-report
    assessments_lower = {k.lower(): v for k, v in signals.get("skill_assessment_scores", {}).items()}
    contradictions = sum(
        1 for s in skills
        if s["proficiency"] == "expert"
        for akey, aval in assessments_lower.items()
        if (s["name"].lower() in akey or akey in s["name"].lower()) and aval < 35
    )
    if contradictions >= 2:   penalty *= 0.15
    elif contradictions == 1: penalty *= 0.45

    # Signal 5: Too many expert skills for experience level
    expert_count = sum(1 for s in skills if s["proficiency"] == "expert")
    if yoe < 4 and expert_count >= 5:    penalty *= 0.25
    elif yoe < 6 and expert_count >= 8:  penalty *= 0.40
    elif yoe < 8 and expert_count >= 12: penalty *= 0.55

    # Signal 6: Overlapping concurrent full-time roles
    past_roles = sorted([r for r in history if not r.get("is_current") and r.get("end_date")],
                        key=lambda r: r["start_date"])
    for i in range(len(past_roles) - 1):
        r1, r2 = past_roles[i], past_roles[i + 1]
        if r2["start_date"] < r1["end_date"]:
            try:
                s = datetime.strptime(r2["start_date"], "%Y-%m-%d")
                e = datetime.strptime(min(r1["end_date"], r2.get("end_date") or r1["end_date"]), "%Y-%m-%d")
                if max(0, (e - s).days / 30) > 3:
                    penalty *= 0.3
            except:
                pass

    # === 4 new signals (v3) ===

    # Signal 7: Title-skill contradiction (Category A — role mismatch)
    # Marketing Manager / HR Manager / Graphic Designer claiming deep AI skills
    non_technical_titles = [
        "marketing", "hr", "human resource", "graphic designer", "content writer",
        "sales", "operations manager", "accountant", "finance", "customer support"
    ]
    current_title_lower = profile["current_title"].lower()
    is_non_technical = any(t in current_title_lower for t in non_technical_titles)
    has_advanced_ai_skills = sum(
        1 for s in skills
        if s["proficiency"] in ["advanced", "expert"]
        and any(term in s["name"].lower() for term in
                ["milvus", "faiss", "lora", "rag", "vector", "embedding", "ndcg", "lambdamart"])
    )
    if is_non_technical and has_advanced_ai_skills >= 2:
        penalty *= 0.1  # Accountant claiming expert RAG + Milvus = clear honeypot

    # Signal 8: Education timeline impossibility (Category B)
    edu = candidate.get("education", [])
    for e in edu:
        start, end = e.get("start_year", 1990), e.get("end_year", 2000)
        # PhD before Bachelor's check
        other_degrees = [x for x in edu if x != e]
        for other in other_degrees:
            if "ph" in e.get("degree", "").lower() and "b." in other.get("degree", "").lower():
                if e.get("end_year", 9999) < other.get("start_year", 9999):
                    penalty *= 0.2  # PhD finished before Bachelor's started
        # Impossible duration
        if end < start:
            penalty *= 0.3

    # Signal 9: Skill-career mismatch (Category C)
    # Career entirely unrelated to AI but claims expert in multiple AI tools
    all_career_text = " ".join(r["description"].lower() for r in history)
    career_has_ml = any(kw in all_career_text for kw in [
        "machine learning", "deep learning", "neural", "model", "embedding",
        "retrieval", "ranking", "inference", "training", "dataset"
    ])
    career_roles_non_ml = all(
        any(nr in r["title"].lower() for nr in [
            "accountant", "marketing", "sales", "hr", "graphic", "content", "operations"
        ]) for r in history
    )
    highly_specialized_ai_skills = sum(
        1 for s in skills
        if s["proficiency"] in ["advanced", "expert"]
        and any(t in s["name"].lower() for t in ["milvus", "qdrant", "lora", "qlora", "peft", "faiss"])
    )
    if career_roles_non_ml and not career_has_ml and highly_specialized_ai_skills >= 2:
        penalty *= 0.15

    # Signal 10: LangChain expert but never passed LangChain assessment (Category D)
    # (minor signal — LangChain itself is weak, but contradiction is a honeypot tell)
    for s in skills:
        if "langchain" in s["name"].lower() and s["proficiency"] == "expert":
            for akey, aval in assessments_lower.items():
                if "langchain" in akey and aval < 20:
                    penalty *= 0.5

    return {
        "honeypot_score": penalty,
        "is_likely_honeypot": float(penalty < 0.15),
    }
```

### 2.8 — Disqualifier Flags (now computed in Stage 2)

**v3 critical fix:** `compute_disqualifier_flags()` now runs in Stage 2 and is persisted in the parquet, so `rank.py` can reference `disqualifier_hit` without a KeyError.

```python
def compute_disqualifier_flags(features, raw_candidate):
    """Runs during feature extraction. Returns (bool, list_of_reasons)."""
    signals = raw_candidate["redrob_signals"]
    profile = raw_candidate["profile"]
    flags = []

    # 1. Pure consulting career (v2 — updated to use consulting_penalty instead)
    if features["consulting_penalty"] > 0.85:
        flags.append("pure_consulting")

    # 2. Zero hard requirement coverage
    if features["min_hard_req_coverage"] < 0.15:
        flags.append("zero_hard_reqs")

    # 3. Too junior
    if features["years_of_experience"] < 3:
        flags.append("too_junior")

    # 4. No production ML evidence
    if features["deployment_score"] < 0.1 and features["retrieval_ir_score"] < 0.1:
        flags.append("no_production_ml")

    # 5. Wrong domain
    if features["domain_mismatch_flag"] == 1.0:
        flags.append("wrong_domain")

    # 6. Honeypot
    if features["is_likely_honeypot"] == 1.0:
        flags.append("honeypot")

    # 7. Outside India, won't relocate (FIXED v3: willing NRI gets 0.30 — not disqualified)
    if features["location_score"] < 0.1:
        flags.append("unreachable_location")

    # FIXED v3: These two disqualifiers were parsed but never implemented in v2
    # 8. LangChain-only under 12 months (without pre-LLM ML background)
    if features["langchain_only_flag"] == 1.0:
        flags.append("langchain_only_under_12mo")

    # 9. No code in 18 months (architect/tech-lead who stopped shipping)
    # Detect: current title is Lead/Principal/Architect AND recent descriptions have no code keywords
    code_keywords = ["implemented", "built", "wrote", "shipped", "deployed", "coded", "developed",
                     "python", "api", "sql", "bash", "script", "pull request", "commit", "git"]
    recent_history = [r for r in raw_candidate["career_history"]
                      if r.get("start_date", "2000-01-01") >= "2024-01-01"]
    recent_descriptions = " ".join(r["description"].lower() for r in recent_history)
    title_lower = features.get("current_title", "").lower()
    is_architecture_role = any(t in title_lower for t in ["architect", "principal", "tech lead", "vp", "director"])
    has_recent_code = any(kw in recent_descriptions for kw in code_keywords)
    if is_architecture_role and not has_recent_code and len(recent_history) > 0:
        flags.append("no_code_in_18mo")

    return bool(flags), "|".join(flags)


# Integrate into extract_all_features:
# After computing all sub-features, compute disqualifiers and add to features dict
def extract_all_features(candidate, jd_parsed):
    features = {}
    features.update(career_features(candidate))
    features.update(skills_features(candidate, jd_parsed))
    features.update(education_features(candidate))
    features.update(logistics_features(candidate, jd_parsed))
    features.update(behavioral_features(candidate["redrob_signals"]))
    features.update(honeypot_features(candidate))

    # Add raw profile fields
    features["candidate_id"] = candidate["candidate_id"]
    features["years_of_experience"] = candidate["profile"]["years_of_experience"]
    features["current_title"] = candidate["profile"]["current_title"]
    features["current_company"] = candidate["profile"]["current_company"]
    features["current_company_size"] = candidate["profile"]["current_company_size"]
    features["location"] = candidate["profile"]["location"]
    features["country"] = candidate["profile"]["country"]

    # Compute and persist disqualifiers NOW (not lazily in rank.py)
    disq_hit, disq_reasons = compute_disqualifier_flags(features, candidate)
    features["disqualifier_hit"] = disq_hit
    features["disqualifier_reasons"] = disq_reasons

    return features
```

---

## Stage 3: Hybrid Retrieval Index
**Days 4–7 (parallel to Stage 2)**

**v3 major change:** Pure semantic retrieval missed exact IR/ranking terminology. Now using BM25 + semantic hybrid, then per-role max-pooling on the top-10K for fine-grained scoring.

### 3.1 — Candidate Text Synthesis

```python
def synthesize_candidate_text(c):
    parts = []
    for role in sorted(c["career_history"], key=lambda r: r["start_date"], reverse=True):
        parts.append(f"{role['title']} at {role['company']} ({role['industry']}): {role['description']}")
    parts.append(c["profile"]["headline"])
    parts.append(c["profile"]["summary"])
    skill_strs = []
    assessments = c["redrob_signals"].get("skill_assessment_scores", {})
    for s in c["skills"]:
        akey = next((k for k in assessments if s["name"].lower() in k.lower()), None)
        if akey:
            skill_strs.append(f"{s['name']} ({s['proficiency']}, assessed: {assessments[akey]:.0f}/100)")
        else:
            skill_strs.append(f"{s['name']} ({s['proficiency']})")
    parts.append("Skills: " + ", ".join(skill_strs))
    for e in c["education"]:
        parts.append(f"{e['degree']} in {e['field_of_study']} from {e['institution']}")
    for cert in c.get("certifications", []):
        parts.append(f"Certified: {cert['name']} ({cert['issuer']}, {cert['year']})")
    return " | ".join(parts)
```

### 3.2 — BM25 Index (NEW in v3)

BM25 excels at exact IR terminology: NDCG, MAP, LambdaMART, FAISS, Milvus. These are low-frequency, high-precision terms that embeddings can miss.

```python
from rank_bm25 import BM25Okapi
import json, gzip, pickle

# Build BM25 corpus
print("Building BM25 index...")
corpus = []
ids = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in f:
        if line.strip():
            c = json.loads(line)
            text = synthesize_candidate_text(c)
            corpus.append(text.lower().split())
            ids.append(c["candidate_id"])

bm25 = BM25Okapi(corpus)
with open("bm25_index.pkl", "wb") as f:
    pickle.dump((bm25, ids), f)
print("✅ BM25 index built.")

# JD query for BM25: use key IR terms from the JD
JD_BM25_QUERY = """
vector search embedding retrieval ranking NDCG MAP MRR LambdaMART FAISS Milvus Pinecone
Weaviate Qdrant OpenSearch Elasticsearch sentence-transformers BGE hybrid search BM25
production deployed real users evaluation framework A/B testing python fastapi
""".lower().split()

bm25_scores = bm25.get_scores(JD_BM25_QUERY)  # shape: (100K,)
# Save indexed scores
import numpy as np
np.save("bm25_scores.npy", bm25_scores)
print(f"BM25 scores: max={bm25_scores.max():.3f}, mean={bm25_scores.mean():.3f}")
```

### 3.3 — Semantic Encoding (with fallback)

```python
def batch_encode_candidates(model_name, output_path, batch_size=64):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    texts, ids = [], []
    with gzip.open("candidates.jsonl.gz", "rt") as f:
        for line in tqdm(f, total=100_000, desc="Synthesizing"):
            if line.strip():
                c = json.loads(line)
                texts.append(synthesize_candidate_text(c))
                ids.append(c["candidate_id"])
    embeddings = model.encode(texts, batch_size=batch_size,
                              normalize_embeddings=True, show_progress_bar=True)
    np.save(output_path, embeddings)
    with open(output_path.replace(".npy", "_ids.json"), "w") as f:
        json.dump(ids, f)
    return embeddings, ids

try:
    embeddings, ids = batch_encode_candidates("BAAI/bge-large-en-v1.5", "candidate_embeddings.npy")
except MemoryError:
    embeddings, ids = batch_encode_candidates("BAAI/bge-base-en-v1.5", "candidate_embeddings.npy")
```

### 3.4 — Hybrid Score Computation

```python
def compute_hybrid_scores(embedding_path, jd_emb, ideal_emb, bm25_scores_path):
    embeddings = np.load(embedding_path, mmap_mode="r")
    jd_emb_loaded = np.load(jd_emb)
    ideal_emb_loaded = np.load(ideal_emb)
    bm25_raw = np.load(bm25_scores_path)

    # Semantic: 60% JD + 40% ideal profile
    semantic = 0.6 * (embeddings @ jd_emb_loaded) + 0.4 * (embeddings @ ideal_emb_loaded)

    # Normalize BM25 to [0, 1]
    bm25_max = bm25_raw.max()
    bm25_norm = bm25_raw / bm25_max if bm25_max > 0 else bm25_raw

    # Hybrid: 60% semantic + 40% BM25
    # BM25 weight is elevated here because the JD is IR-keyword-dense
    hybrid = 0.60 * semantic + 0.40 * bm25_norm

    np.save("semantic_scores.npy", semantic)
    np.save("hybrid_scores.npy", hybrid)
    print(f"Hybrid scores: min={hybrid.min():.3f}, max={hybrid.max():.3f}, mean={hybrid.mean():.3f}")
    return hybrid

hybrid = compute_hybrid_scores(
    "candidate_embeddings.npy", "jd_embedding.npy", "ideal_embedding.npy", "bm25_scores.npy"
)
```

### 3.5 — Per-Role Semantic Score (FIXED: now wired into features)

**v3 fix:** This was dead code in v2. Now computed for top-10K and merged into the feature matrix.

```python
def compute_per_role_scores(embedding_ids, jd_embedding_path, top10k_ids, model_name):
    """
    For top-10K candidates: embed each career role, take the max.
    Captures candidates with one stellar relevant role buried under unrelated work.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    jd_emb = np.load(jd_embedding_path)
    top10k_set = set(top10k_ids)
    per_role_scores = {}

    with gzip.open("candidates.jsonl.gz", "rt") as f:
        for line in tqdm(f, total=100_000, desc="Per-role scoring"):
            if not line.strip(): continue
            c = json.loads(line)
            if c["candidate_id"] not in top10k_set: continue
            role_texts = [r["description"] for r in c["career_history"]]
            if not role_texts:
                per_role_scores[c["candidate_id"]] = 0.0
                continue
            role_embeddings = model.encode(role_texts, normalize_embeddings=True)
            sims = role_embeddings @ jd_emb
            per_role_scores[c["candidate_id"]] = float(np.max(sims))

    json.dump(per_role_scores, open("per_role_scores.json", "w"))
    return per_role_scores

# After computing hybrid scores, get top-10K IDs
embedding_ids = json.load(open("candidate_embeddings_ids.json"))
id_to_hybrid = {cid: float(hybrid[i]) for i, cid in enumerate(embedding_ids)}
top10k_ids = sorted(id_to_hybrid, key=id_to_hybrid.get, reverse=True)[:10000]
json.dump(top10k_ids, open("top10k_ids.json", "w"))

per_role_scores = compute_per_role_scores(
    embedding_ids, "jd_embedding.npy", top10k_ids, "BAAI/bge-base-en-v1.5"
)

# Merge per_role_scores into features parquet
features_df = pd.read_parquet("features_100k.parquet")
features_df["per_role_semantic_score"] = features_df["candidate_id"].map(
    lambda cid: per_role_scores.get(cid, id_to_hybrid.get(cid, 0.0))
    # fallback to global hybrid score for candidates outside top-10K
)
# Also merge hybrid and semantic scores
features_df["hybrid_score"] = features_df["candidate_id"].map(id_to_hybrid)
semantic_id_map = {cid: float(np.load("semantic_scores.npy")[i])
                   for i, cid in enumerate(embedding_ids)}
features_df["semantic_score"] = features_df["candidate_id"].map(semantic_id_map)

features_df.to_parquet("features_100k.parquet", index=False)
print("✅ Semantic, hybrid, and per-role scores merged into features parquet.")
```

---

## Stage 4: Honeypot Audit
**Day 7 | Goal: Zero honeypots in top 100 — no exceptions**

### 4.1 — Audit Report

```python
def audit_honeypots(features_df, threshold=0.15):
    suspects = features_df[features_df["honeypot_score"] < threshold].copy()
    suspects = suspects.sort_values("honeypot_score")
    print(f"Honeypot suspects (score < {threshold}): {len(suspects)} (spec says ~80)")
    for _, row in suspects.head(15).iterrows():
        print(f"  {row['candidate_id']}: honeypot={row['honeypot_score']:.3f} "
              f"title={row.get('current_title', '?')} yoe={row.get('years_of_experience', '?')}")
    return suspects["candidate_id"].tolist()
```

**Manual verification checklist (mandatory):**
- [ ] 10 most suspicious candidates reviewed against full JSON profile
- [ ] All clearly-synthetic profiles identified (impossible timelines, expert contradictions, role mismatches)
- [ ] Zero honeypot suspects appear in your top-200 after first ranking pass

---

## Stage 5: Multi-Signal Scoring Engine
**Days 8–9 | Goal: Accurate initial composite ranking**

### 5.1 — Experience Band Modifier

```python
def experience_modifier(yoe):
    if 5 <= yoe <= 9:    return 1.00
    if 4 <= yoe < 5:     return 0.90
    if 9 < yoe <= 11:    return 0.96
    if 3 <= yoe < 4:     return 0.72
    if 11 < yoe <= 14:   return 0.88
    if yoe > 14:         return 0.78
    return 0.50
```

### 5.2 — Composite Relevance Score

Weights mirror the JD's explicit philosophy: career trajectory > skills > semantic > logistics > education.

```python
def compute_relevance_score(features, semantic_score, hybrid_score, per_role_score):
    # Career trajectory
    s_career = (
        0.30 * (1.0 - features["consulting_penalty"]) +  # FIXED: uses penalty not ratio
        0.30 * features["deployment_score"] +
        0.20 * features["retrieval_ir_score"] +
        0.10 * features["years_in_product"] +
        0.05 * features["seniority_trend"]
        - 0.10 * features["job_hop_penalty"]
        - 0.08 * features["title_chaser_flag"]
    )
    s_career = max(0.0, min(1.0, s_career))

    # Skills (with credibility discount)
    s_skills = (
        0.50 * features["avg_hard_req_coverage"] +
        0.15 * features["min_hard_req_coverage"] +
        0.15 * features["soft_req_coverage"] +
        0.10 * features["has_relevant_assessments"] * features["avg_relevant_assessment"] +
        0.10 * features["assessment_credibility"]
        - 0.10 * features["domain_mismatch_flag"]
    )
    s_skills = max(0.0, min(1.0, s_skills))

    # Semantic: blend of global + per-role max-pooling (FIXED: per-role now used)
    s_semantic = 0.6 * float(hybrid_score) + 0.4 * float(per_role_score)

    # Education
    s_edu = (
        0.60 * features["edu_tier_score"] +
        0.25 * features["is_cs_adjacent"] +
        0.15 * features["has_postgrad"]
    )

    # Logistics
    s_logistics = (
        0.40 * features["location_score"] +
        0.25 * features["notice_score"] +
        0.20 * features["salary_score"] +
        0.15 * features["work_mode_score"]
    )

    composite = (
        0.30 * s_career +
        0.28 * s_skills +
        0.22 * s_semantic +
        0.12 * s_logistics +
        0.08 * s_edu
    )

    return composite, {
        "s_career": s_career, "s_skills": s_skills, "s_semantic": s_semantic,
        "s_edu": s_edu, "s_logistics": s_logistics
    }


def compute_final_score(relevance, behavioral_score, honeypot_score, disqualifier_hit, yoe):
    if disqualifier_hit:
        relevance = min(relevance, 0.12)
    relevance *= experience_modifier(yoe)
    behavioral_multiplier = 0.35 + 0.65 * behavioral_score
    score = relevance * behavioral_multiplier * honeypot_score
    return max(score, 0.001)
```

### 5.3 — Golden Set Validation (build before proceeding to LambdaMART)

```python
"""
Read 15 candidate profiles manually vs the JD. Classify 0/1/2.
Strong fit (2): 5-9yr product company, retrieval/search work, India or willing to relocate
Not fit (0): pure consulting, wrong domain, outside India + won't relocate, honeypot, very junior
"""
GOLDEN_SET = {
    # FILL IN after manual review
    "CAND_XXXXXXX": 2,
}

def validate_golden_set(scores_dict, golden_set):
    strong = [scores_dict[cid] for cid, label in golden_set.items() if label == 2]
    not_fit = [scores_dict[cid] for cid, label in golden_set.items() if label == 0]
    assert min(strong) > max(not_fit), "FAIL: some not-fit outscores a strong-fit!"
    print("✅ Golden set validation passed")
```

---

## Stage 6: LambdaMART Ensemble Re-Ranker
**Days 10–12 | Goal: Learn non-linear signal combinations, NDCG-optimized**

**v3 major change:** Three LambdaMART models trained on different label signals, then ensembled. This hedges against pseudo-label quality issues — the biggest weakness of any single-model approach.

### 6.1 — Feature Matrix

**v3 fix:** `per_role_semantic_score` is now included (it was dead code in v2).

```python
LAMBDAMART_FEATURES = [
    # Semantic (v3: both global hybrid and per-role)
    "semantic_score", "hybrid_score", "per_role_semantic_score",
    # Career
    "consulting_ratio", "consulting_penalty", "product_ratio",
    "years_in_product", "deployment_score", "retrieval_ir_score",
    "seniority_trend", "job_hop_penalty", "title_chaser_flag", "current_size_score",
    # Skills
    "avg_hard_req_coverage", "min_hard_req_coverage", "soft_req_coverage",
    "avg_relevant_assessment", "has_relevant_assessments", "assessment_credibility",
    "domain_mismatch_flag", "langchain_only_flag",
    # Individual hard req coverage scores
    "hard_req_vector_search_infra", "hard_req_embedding_models",
    "hard_req_ranking_evaluation", "hard_req_python_production",
    # Logistics
    "location_score", "notice_score", "salary_score", "work_mode_score",
    # Education
    "edu_tier_score", "is_cs_adjacent", "has_postgrad",
    # Behavioral
    "behavioral_score", "open_to_work", "recency", "responsiveness",
    "track_record", "github_score", "apps_30d", "saved_30d",
    # Honeypot
    "honeypot_score",
    # Experience
    "years_of_experience",
]
```

### 6.2 — Three-Label Strategy for Pseudo-Labels

```python
import anthropic, json, time
from tqdm import tqdm

client = anthropic.Anthropic()

JD_SUMMARY = """
Role: Senior AI Engineer at Redrob AI (Series A, Pune/Noida India)
STRONG FIT (label 3): 5-9yr at product companies; production vector DB / embedding retrieval / hybrid search; ships code; India or willing to relocate; notice ≤ 90 days
MODERATE FIT (label 2): Adjacent skills (data eng, NLP, some retrieval) but missing 1-2 hard reqs; or right skills but partial consulting background
WEAK FIT (label 1): Some relevant skills but career mostly unrelated (consulting, CV/speech); or too junior/senior
NOT A FIT (label 0): Pure consulting; wrong domain (CV/speech only); outside India + won't relocate; honeypot; non-technical role with AI keywords
"""

def pseudo_label_candidate(c, label_strategy="recruiter"):
    """
    label_strategy:
      "recruiter"  → holistic recruiter judgment (Model A)
      "hard_reqs"  → hard requirement coverage only (Model B)
      "semantic"   → semantic fit only (Model C, just use composite semantic score → no API needed)
    """
    if label_strategy == "recruiter":
        prompt = f"""
{JD_SUMMARY}
Candidate:
- Title: {c['profile']['current_title']} at {c['profile']['current_company']}
- YOE: {c['profile']['years_of_experience']}
- Location: {c['profile']['location']}, {c['profile']['country']}
- Summary: {c['profile']['summary'][:500]}
- Recent role: {c['career_history'][0]['description'][:400] if c['career_history'] else 'N/A'}
- Key skills: {', '.join(s['name'] for s in c['skills'][:10])}
- Notice: {c['redrob_signals']['notice_period_days']} days
- Open: {c['redrob_signals']['open_to_work_flag']}
- Relocate: {c['redrob_signals']['willing_to_relocate']}
Respond ONLY with integer 0, 1, 2, or 3."""

    elif label_strategy == "hard_reqs":
        hard_req_skills = ["vector database", "embeddings", "NDCG", "ranking", "python production",
                           "FAISS", "Milvus", "Pinecone", "retrieval", "hybrid search", "LambdaMART"]
        skills_text = ", ".join(s["name"] for s in c["skills"])
        descriptions = " ".join(r["description"][:300] for r in c["career_history"][:2])
        prompt = f"""
Rate 0-3 how well this candidate covers these hard requirements: {hard_req_skills}
Skills: {skills_text}
Experience: {descriptions}
3 = covers most, 2 = covers some, 1 = barely, 0 = none
Respond ONLY with integer 0, 1, 2, or 3."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}]
        )
        return int(response.content[0].text.strip()[0])
    except:
        return -1


def sample_for_labeling(features_df, n=2500):
    df = features_df.copy()
    df["quartile"] = pd.qcut(df["composite_score"], 4, labels=[0, 1, 2, 3])
    return df.groupby("quartile").sample(n // 4, random_state=42)["candidate_id"].tolist()
```

### 6.3 — Three-Model Training and Ensemble

```python
import lightgbm as lgb
from sklearn.model_selection import KFold
import numpy as np

def train_lambdamart(X_train, y_train, X_val, y_val, model_name="lambdamart"):
    train_data = lgb.Dataset(X_train, label=y_train, group=[len(X_train)],
                             feature_name=LAMBDAMART_FEATURES)
    val_data = lgb.Dataset(X_val, label=y_val, group=[len(X_val)],
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
        "verbose": -1,
        "label_gain": [0, 1, 3, 7],
    }
    model = lgb.train(params, train_data, num_boost_round=500,
                      valid_sets=[val_data],
                      callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)])
    model.save_model(f"ranker_{model_name}.lgb")
    return model


# FIXED v3: CV computes full composite metric, not just NDCG@10
def compute_composite_metric(y_true, y_pred):
    """Compute 0.50×NDCG@10 + 0.30×NDCG@50 + 0.15×MAP + 0.05×P@10"""
    from sklearn.metrics import ndcg_score, average_precision_score
    ndcg10 = ndcg_score([y_true], [y_pred], k=10)
    ndcg50 = ndcg_score([y_true], [y_pred], k=50)
    # MAP approximation
    ranked_idx = np.argsort(y_pred)[::-1]
    relevant = (y_true[ranked_idx] >= 2).astype(float)
    cum_relevant = np.cumsum(relevant)
    ranks = np.arange(1, len(relevant) + 1)
    map_score = float(np.sum(relevant * cum_relevant / ranks) / max(relevant.sum(), 1))
    # P@10
    p10 = float(relevant[:10].sum() / 10)
    return 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * map_score + 0.05 * p10, {
        "ndcg10": ndcg10, "ndcg50": ndcg50, "map": map_score, "p10": p10
    }


def cross_validate_and_train(labeled_df, full_feature_df, label_col="recruiter_label"):
    labeled_features = full_feature_df[
        full_feature_df["candidate_id"].isin(labeled_df["candidate_id"])
    ].merge(labeled_df[["candidate_id", label_col]], on="candidate_id")

    X = labeled_features[LAMBDAMART_FEATURES].values
    y = labeled_features[label_col].values

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    fold_composites = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        model = train_lambdamart(X[train_idx], y[train_idx], X[val_idx], y[val_idx])
        val_pred = model.predict(X[val_idx])
        composite, breakdown = compute_composite_metric(y[val_idx], val_pred)
        fold_composites.append(composite)
        print(f"  Fold {fold+1}: composite={composite:.4f} "
              f"(NDCG@10={breakdown['ndcg10']:.4f}, NDCG@50={breakdown['ndcg50']:.4f}, "
              f"MAP={breakdown['map']:.4f}, P@10={breakdown['p10']:.4f})")

    mean_composite = np.mean(fold_composites)
    print(f"\nMean CV composite: {mean_composite:.4f} ± {np.std(fold_composites):.4f}")
    return mean_composite


def build_ensemble(features_df, model_paths, weights=(0.40, 0.30, 0.30)):
    """
    Ensemble of three LambdaMART models:
    - Model A (recruiter_label): 40% — holistic recruiter judgment
    - Model B (hard_req_label): 30% — hard requirement coverage
    - Model C (semantic_label): 30% — semantic score quantized to 0-3 (no API needed)
    """
    X = features_df[LAMBDAMART_FEATURES].values
    ensemble_scores = np.zeros(len(features_df))
    for model_path, weight in zip(model_paths, weights):
        model = lgb.Booster(model_file=model_path)
        preds = model.predict(X)
        # Normalize to [0, 1]
        preds = (preds - preds.min()) / max(preds.max() - preds.min(), 1e-8)
        ensemble_scores += weight * preds
    return ensemble_scores
```

**Decision rule:** If ensemble composite > (Stage 5 baseline + 0.03) → use ensemble. Otherwise → ship Stage 5 composite scores.

---

## Stage 7: Reasoning Generation + Final Output
**Days 12–14 | Sandbox: Day 13**

### 7.1 — Anchored Reasoning Generation

```python
def build_reasoning_context(candidate, features, rank, score):
    signals = candidate["redrob_signals"]
    profile = candidate["profile"]

    assessments = signals.get("skill_assessment_scores", {})
    verified_skills = []
    claimed_skills = []
    for s in candidate["skills"]:
        akey = next((k for k in assessments if s["name"].lower() in k.lower()), None)
        if akey:
            verified_skills.append(f"{s['name']} (assessed {assessments[akey]:.0f}/100)")
        elif s["proficiency"] in ["advanced", "expert"]:
            claimed_skills.append(f"{s['name']} ({s['proficiency']}, self-reported)")

    recent_role = candidate["career_history"][0] if candidate["career_history"] else None
    role_str = (f"{recent_role['title']} at {recent_role['company']} "
                f"({recent_role['duration_months']}mo, {recent_role['industry']})"
                if recent_role else "N/A")

    concerns = []
    if signals["notice_period_days"] > 60:
        concerns.append(f"long notice ({signals['notice_period_days']} days)")
    if features.get("location_score", 1.0) < 0.65:
        concerns.append(f"not in preferred location ({profile['location']}, relocate: {signals['willing_to_relocate']})")
    if features.get("consulting_penalty", 0) > 0.5:
        concerns.append(f"significant consulting background")
    if features.get("recency", 1.0) < 0.5:
        concerns.append("low platform activity")
    if features.get("avg_hard_req_coverage", 1.0) < 0.6:
        concerns.append("missing some hard requirements")

    return {
        "rank": rank, "score": score,
        "years": profile["years_of_experience"],
        "current_role": role_str,
        "location": f"{profile['location']}, {profile['country']}",
        "verified_skills": verified_skills[:5],
        "claimed_skills": claimed_skills[:5],
        "notice_days": signals["notice_period_days"],
        "open_to_work": signals["open_to_work_flag"],
        "salary_range": f"{signals['expected_salary_range_inr_lpa']['min']}-{signals['expected_salary_range_inr_lpa']['max']} LPA",
        "concerns": concerns,
    }


def generate_reasoning(candidate, features, rank, score, client):
    ctx = build_reasoning_context(candidate, features, rank, score)
    prompt = f"""
Write a recruiter shortlist note in exactly 1-2 sentences.

RULES:
- Reference ONLY the facts below. No skills, employers, or experience not listed here.
- Be specific: use actual role names, skill names, numbers.
- Mention concerns if they exist.
- Rank 1-10: strong endorsement | Rank 50-100: honest and measured.
- NO generic phrases like "strong candidate" or "perfect fit."

FACTS:
- Rank: {ctx['rank']} of 100 | Score: {ctx['score']:.3f}
- YOE: {ctx['years']} | Current: {ctx['current_role']}
- Location: {ctx['location']}
- Verified skills: {', '.join(ctx['verified_skills']) or 'none'}
- Claimed (self-reported advanced/expert): {', '.join(ctx['claimed_skills']) or 'none'}
- Notice: {ctx['notice_days']} days | Open to work: {ctx['open_to_work']}
- Salary expectation: {ctx['salary_range']}
- Concerns: {'; '.join(ctx['concerns']) if ctx['concerns'] else 'none'}

Write the recruiter note now:
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()
```

### 7.2 — Final rank.py

```python
#!/usr/bin/env python3
"""
rank.py — Final ranking step. Must run in ≤5 min, CPU only, no network.
Usage: python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
"""
import argparse, json, csv, time
import numpy as np
import pandas as pd
import lightgbm as lgb

LAMBDAMART_FEATURES = [ ... ]  # same list as Stage 6

def experience_modifier(yoe): ...  # same as Stage 5
def compute_final_score(...): ...  # same as Stage 5

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="submission.csv")
    args = parser.parse_args()
    t0 = time.time()

    print("[1/6] Loading precomputed features...")
    features_df = pd.read_parquet("artifacts/features_100k.parquet")
    features_df = features_df.set_index("candidate_id")

    print("[2/6] Loading embeddings...")
    embeddings = np.load("artifacts/candidate_embeddings.npy", mmap_mode="r")
    embedding_ids = json.load(open("artifacts/candidate_embeddings_ids.json"))
    id_to_idx = {cid: i for i, cid in enumerate(embedding_ids)}

    print("[3/6] Computing semantic and hybrid scores...")
    jd_emb = np.load("artifacts/jd_embedding.npy")
    ideal_emb = np.load("artifacts/ideal_embedding.npy")
    bm25_scores = np.load("artifacts/bm25_scores.npy")
    bm25_norm = bm25_scores / max(bm25_scores.max(), 1)

    jd_sims = embeddings @ jd_emb
    ideal_sims = embeddings @ ideal_emb
    semantic = 0.6 * jd_sims + 0.4 * ideal_sims
    hybrid = 0.60 * semantic + 0.40 * bm25_norm

    features_df["semantic_score"] = [semantic[id_to_idx[cid]] for cid in features_df.index]
    features_df["hybrid_score"] = [hybrid[id_to_idx[cid]] for cid in features_df.index]

    # per_role_semantic_score already in parquet (precomputed)
    # Fallback for candidates not in top-10K during precompute
    if "per_role_semantic_score" not in features_df.columns:
        features_df["per_role_semantic_score"] = features_df["hybrid_score"]

    print("[4/6] Scoring with LambdaMART ensemble...")
    X = features_df[LAMBDAMART_FEATURES].fillna(0).values
    ensemble_scores = np.zeros(len(features_df))
    model_weights = [("ranker_recruiter.lgb", 0.40),
                     ("ranker_hard_reqs.lgb", 0.30),
                     ("ranker_semantic.lgb", 0.30)]
    for model_path, weight in model_weights:
        try:
            m = lgb.Booster(model_file=f"artifacts/{model_path}")
            preds = m.predict(X)
            preds = (preds - preds.min()) / max(preds.max() - preds.min(), 1e-8)
            ensemble_scores += weight * preds
        except FileNotFoundError:
            print(f"  ⚠ {model_path} not found — skipping (using 0 contribution)")

    features_df["lm_score"] = ensemble_scores

    # Apply honeypot penalty and disqualifier cap
    features_df["final_score"] = features_df.apply(
        lambda row: row["lm_score"]
            * row.get("honeypot_score", 1.0)
            * (0.12 if row.get("disqualifier_hit", False) else 1.0),
        axis=1
    )

    print("[5/6] Selecting top 100...")
    ranked = features_df.sort_values(
        ["final_score", "candidate_id"], ascending=[False, True]
    ).head(100)

    print("[6/6] Writing submission CSV...")
    reasoning_cache = json.load(open("artifacts/reasoning_cache.json"))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank_num, (cid, row) in enumerate(ranked.iterrows(), start=1):
            reasoning = reasoning_cache.get(
                cid,
                f"{row.get('current_title', 'Candidate')} with {row.get('years_of_experience', '?'):.1f} years of experience."
            )
            writer.writerow([cid, rank_num, f"{row['final_score']:.4f}", reasoning])

    elapsed = time.time() - t0
    print(f"✅ Done in {elapsed:.1f}s")
    validate_submission(args.out, features_df)

if __name__ == "__main__":
    main()
```

### 7.3 — Submission Validator (FIXED: honeypot rate check added)

```python
def validate_submission(filepath, features_df):
    """All spec checks PLUS the one check that actually prevents disqualification."""
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
            f"❌ Scores not non-increasing at rank {i+1}→{i+2}"

    assert len(set(scores)) > 10, "❌ Too few unique scores — model isn't differentiating"

    reasonings = [r["reasoning"] for r in rows]
    assert all(len(r) > 20 for r in reasonings), "❌ Some reasoning strings too short"
    assert len(set(reasonings)) > 50, "❌ Too many duplicate reasoning strings"

    # CRITICAL FIX v3: Check honeypot rate BEFORE upload
    # This is the check that prevents automatic disqualification
    if features_df is not None:
        submitted_ids = set(ids)
        submitted_features = features_df[features_df.index.isin(submitted_ids)]
        honeypot_count = submitted_features["is_likely_honeypot"].sum()
        honeypot_rate = honeypot_count / 100.0
        print(f"  Honeypot rate in top 100: {honeypot_count:.0f}/100 ({honeypot_rate:.1%})")
        assert honeypot_rate <= 0.08, \
            f"❌ CRITICAL: {honeypot_count} honeypots in top 100 ({honeypot_rate:.1%}) — exceeds 10% threshold! FIX BEFORE UPLOADING."
        if honeypot_rate > 0.05:
            print(f"  ⚠ WARNING: {honeypot_count} honeypots detected. Threshold is 10% — you're cutting it close.")

    print(f"✅ Submission valid: 100 rows, ranks 1-100, scores non-increasing, {honeypot_rate:.0%} honeypot rate")
```

### 7.4 — Sandbox Deployment (Day 13 — mandatory per spec Section 10.5)

The spec is explicit: submissions without a sandbox link are flagged at Stage 1. Half a day, not optional.

```python
# Option A: Google Colab (simplest — link to notebook that runs end-to-end)
# Create: redrob_ranker_demo.ipynb
# - Cell 1: pip install deps, download artifacts
# - Cell 2: Load sample_candidates.json (provided in bundle, ≤100 candidates)
# - Cell 3: Run rank.py equivalent on the sample
# - Cell 4: Display ranked output and validate

# Option B: Streamlit Cloud (slightly nicer UX)
# app.py:
import streamlit as st
st.title("Redrob Ranker Demo")
uploaded = st.file_uploader("Upload candidates.jsonl (≤100 candidates)", type=["jsonl", "gz"])
if uploaded and st.button("Rank"):
    # run pipeline on uploaded file
    # show ranked table
    pass

# Note: sandbox only needs to handle ≤100 candidates (not 100K)
# Pre-load artifacts in the sandbox image
# Target: < 2 min runtime on CPU for 100 candidates
```

---

## 15-Day Implementation Roadmap

| Day | Task | Output | Checkpoint |
|-----|------|--------|------------|
| 1 | Stage 0: env setup, data check, benchmark. Stage 1: JD parsing with confidence | `jd_parsed.json`, `jd_parsed_confidence.json`, model downloaded | Manual check: low-confidence fields reviewed |
| 2 | Stage 1 complete: skill taxonomy, JD embedding. Review confidence audit | `jd_embedding.npy`, `skill_groups.py` | All JD fields confidence > 0.7 |
| 3 | Stage 2: career + education + disqualifier features | `feature_engineering.py` unit-tested | Unit tests pass on CAND_0000001 |
| 4 | Stage 2: skills + assessment features. Start encoding overnight | Skills code done, encoding starts | Encoding ETA confirmed |
| 5 | Stage 2: logistics + behavioral features. Full pipeline. Stage 3: BM25 index | `extract_all_features()` complete, `bm25_index.pkl` | BM25 scores non-zero for IR terms |
| 6 | Run full feature extraction on 100K | `features_100k.parquet` | Assert shape: 100K × ~55 cols. All required cols present. |
| 7 | Stage 3: encoding done. Compute hybrid scores. Merge per-role scores. Stage 4: honeypot audit | `hybrid_scores.npy`, `per_role_scores.json`, `honeypot_audit.txt` | Manual verify 10 honeypot suspects |
| 8 | Stage 5: composite scoring + golden set validation | `composite_scores.npy` | Golden set: all strong-fit > all not-fit |
| **9** | **Submit submission #1** (Stage 5 composite, no LambdaMART). Generate preliminary reasoning | `submission_v1.csv` submitted | Validator passes including honeypot rate check |
| 10 | Stage 6: pseudo-label 2,500 candidates (recruiter + hard-req strategies) | `pseudo_labels_recruiter.csv`, `pseudo_labels_hard_reqs.csv` | Label dist: ~10% 3s, 25% 2s, 35% 1s, 30% 0s |
| 11 | Train all 3 LambdaMART models. 5-fold CV with full composite metric. Build ensemble | `ranker_*.lgb` | CV composite > Stage 5 + 0.03? |
| 12 | Stage 7: reasoning for top-150 candidates | `reasoning_cache.json` | Spot-check 20: no hallucinations |
| 13 | Build `rank.py` end-to-end. Timing benchmark. **Build sandbox** (Colab or Streamlit) | `rank.py`, sandbox link | Runtime < 2min; sandbox runs on sample_candidates.json |
| **14** | **Submit submission #2** (ensemble + reasoning). Full validator including honeypot check | `submission_v2.csv` submitted | Validator passes |
| 15 | Buffer. Fix any issues. Submit #3 if meaningful improvement found | Final submission | |

**Submission strategy:** #1 on Day 9 is your safety net. #2 and #3 are improvements. Never ship without running the full validator including the honeypot rate assertion.

---

## What Each Fix Solves

| Gap | Where Fixed | Why It Matters |
|-----|-------------|----------------|
| Honeypot rate never checked pre-upload | Stage 7.3 validator | >10% = auto-disqualification, no appeal |
| `disqualifier_hit` not persisted in parquet → KeyError | Stage 2.8 + 2.1 | rank.py would crash at submission time |
| `years_of_experience`, `current_title` missing from parquet | Stage 2.1 | Same crash, same reason |
| Per-role max-pooling was dead code | Stage 3.5 + features merge | Wasted compute; now a real signal |
| NRI + willing_to_relocate was hard-blocked | Stage 2.5 | JD says case-by-case, not auto-reject |
| `langchain_only_under_12mo` never implemented | Stage 2.3 + 2.8 | JD's most explicit disqualifier was ignored |
| `no_code_in_18mo` never implemented | Stage 2.8 | Same — parsed but not checked |
| LambdaMART CV only validated NDCG@10 | Stage 6.3 | Could win NDCG@10 while hurting NDCG@50+MAP |
| Salary null hallucination risk | Stage 1.1 + 2.5 | JD has no salary → return null, not guessed range |
| Sandbox missing from roadmap | Day 13 | Stage 1 flag if missing — cheap to add, costly to miss |
| Consulting ratio penalized mixed careers | Stage 2.2 | Correct candidate (4yr consulting + 4yr product) buried |
| Company size bias penalized Google/Amazon | Stage 2.2 | False negative on strong candidates |
| Single LambdaMART → pseudo-label quality risk | Stage 6.3 | Three-model ensemble hedges against label bias |
| BM25 missing → IR terms missed by embeddings | Stage 3.2-3.4 | NDCG/LambdaMART/Milvus are low-freq, high-precision |
| No JD confidence scores | Stage 1.1 | Silent hallucination propagates through whole pipeline |

---

## File Structure

```
redrob-ranker/
├── README.md
├── requirements.txt
├── submission_metadata.yaml
│
├── precompute/
│   ├── 01_parse_jd.py
│   ├── 02_encode_candidates.py
│   ├── 03_extract_features.py           # includes disqualifier computation
│   ├── 04_build_bm25_index.py           # NEW in v3
│   ├── 05_compute_hybrid_scores.py      # NEW in v3
│   ├── 06_compute_per_role_scores.py    # WIRED in v3
│   ├── 07_honeypot_audit.py
│   ├── 08_generate_pseudolabels.py
│   ├── 09_train_lambdamart_ensemble.py  # 3 models in v3
│   └── 10_generate_reasoning.py
│
├── rank.py                               # ≤5 min, CPU only, no network
├── validate_submission.py                # includes honeypot rate check
├── sandbox/                              # Day 13 deliverable
│   └── redrob_demo.ipynb                 # or app.py for Streamlit
│
├── artifacts/
│   ├── jd_parsed.json
│   ├── jd_parsed_confidence.json        # NEW in v3
│   ├── jd_embedding.npy
│   ├── ideal_embedding.npy
│   ├── features_100k.parquet            # now includes per_role_score, hybrid_score, disqualifier_hit
│   ├── candidate_embeddings.npy
│   ├── candidate_embeddings_ids.json
│   ├── bm25_scores.npy                  # NEW in v3
│   ├── per_role_scores.json             # WIRED in v3
│   ├── ranker_recruiter.lgb             # NEW in v3
│   ├── ranker_hard_reqs.lgb             # NEW in v3
│   ├── ranker_semantic.lgb              # NEW in v3
│   └── reasoning_cache.json
│
└── tests/
    ├── test_features.py
    ├── test_honeypot.py
    ├── test_golden_set.py
    └── test_disqualifiers.py            # NEW: tests all 9 disqualifier checks
```

```bash
# Pre-computation (once, ~4-8 hours total):
python precompute/01_parse_jd.py
python precompute/02_encode_candidates.py
python precompute/03_extract_features.py
python precompute/04_build_bm25_index.py
python precompute/05_compute_hybrid_scores.py
python precompute/06_compute_per_role_scores.py
python precompute/07_honeypot_audit.py
python precompute/08_generate_pseudolabels.py
python precompute/09_train_lambdamart_ensemble.py
python precompute/10_generate_reasoning.py

# Ranking step (≤5 min, CPU only, no network):
python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
```
