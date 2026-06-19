# Redrob AI — Intelligent Candidate Ranking System
## Architecture v4.0 — Competition-Final: Win Edition

---

## What Changed from v3 and Why

Every change in v4 is driven by a specific gap identified across the three LLM reviewers (Claude v3, ChatGPT, DeepSeek), the organizer bundle, or the submission spec. Nothing was changed for complexity's sake — each addition has a concrete reason. Changes are marked **[v4]**.

### Critical bug fixes from v3:
1. **`title_chaser_flag` was inverted** — it fired on stagnant careers, not actual title-chasers. **[v4: fixed direction]**
2. **Disqualifier penalty was applied two inconsistent ways** — Stage 5 capped at 0.12 absolute; `rank.py` multiplied by 0.12. **[v4: unified into per-type penalty dict]**
3. **`saved_by_recruiters_30d` and `search_appearance_30d` excluded from Stage 5 composite** — the signals doc explicitly calls these predictive, and the Day-9 safety-net submission never used them. **[v4: both enter behavioral composite and are standalone LambdaMART features]**
4. **Bare `"search"` in `RETRIEVAL_IR_KEYWORDS`** — false-positives on "led the search for a vendor." **[v4: removed; replaced with multi-word anchored terms]**
5. **`rank.py` ignored `--candidates` flag** — loaded parquet unconditionally. **[v4: validates candidate IDs from flag against parquet index]**
6. **Experience modifier had hard discontinuities** — 4.9yr → 0.90, 5.0yr → 1.00. **[v4: replaced with smooth sigmoid]**
7. **Pseudo-label sampling only covered quartiles** — edge cases near disqualifier boundary underrepresented. **[v4: stratified by composite + disqualifier flag]**
8. **Ensemble weights were fixed at 0.40/0.30/0.30** — arbitrary. **[v4: weights optimized by scipy.optimize against CV composite metric]**

### New features added:
9. **`production_evidence_score`** — all three LLM reviewers and the JD itself emphasize "shipped to real users, latency, SLA, monitoring." New dedicated feature. **[v4]**
10. **`startup_fit_score`** — JD explicitly values "startup mindset, ambiguity, ownership, ships fast." New signal. **[v4]**
11. **`recruiter_intent_score`** — DeepSeek and Claude both flagged that `search_appearance_30d` and `profile_views_received_30d` are unused despite the signals doc calling them predictive. **[v4]**
12. **`role_transition_score`** — DeepSeek's suggestion: career trajectory toward AI/ML matters. **[v4]**
13. **Requirement strength weights for LambdaMART** — ChatGPT's suggestion: hard reqs have varying importance (vector_search_infra=1.0, python_production=0.8, etc.). **[v4]**
14. **Per-disqualifier soft penalties** — DeepSeek correctly noted a hard cap of 0.12 collapses nuance. **[v4: per-type caps]**
15. **BM25 query uses natural JD text** — DeepSeek flagged that keyword-list BM25 queries are unnatural. **[v4: uses key technical paragraph verbatim]**
16. **Reasoning fallback is substantive** — DeepSeek flagged the generic fallback. **[v4: fallback now pulls actual feature values]**
17. **Validator checks score range and reasoning sentence count** — DeepSeek's spec compliance additions. **[v4]**
18. **Low-confidence JD field fallbacks** — DeepSeek's suggestion: automated fallback, not just print. **[v4]**

### What we deliberately did NOT change:
- Three-model LambdaMART ensemble remains. ChatGPT said reduce to one; Claude said keep ensemble for hedge. We keep it, but add empirical weight optimization so if one model degrades, weights self-adjust.
- BM25 + semantic hybrid remains — all three reviewers agreed it's the right architecture for IR-keyword-dense JDs.
- Honeypot detection at 10 signals remains — ChatGPT gave it 10/10 and DeepSeek gave it 9/10.
- All API calls remain in precompute — confirmed correct by all three reviewers.

---

## System Architecture: 7 Stages

```
Stage 0: Pre-flight & Environment Setup           (Day 1)
Stage 1: JD Intelligence Layer                    (Days 1–2)
Stage 2: Candidate Feature Engineering            (Days 3–6)
Stage 3: Hybrid Retrieval Index                   (Days 4–7, parallel)
Stage 4: Honeypot Audit                           (Day 7)
Stage 5: Multi-Signal Scoring Engine              (Days 8–9)
Stage 6: LambdaMART Ensemble Re-Ranker            (Days 10–12)
Stage 7: Reasoning Generation + Output            (Days 12–14)
Day 13: Sandbox deployment (mandatory per spec §10.5)
Day 15: Buffer / Submission #3 if meaningful improvement
```

---

## Stage 0: Pre-flight & Environment Setup
**Day 1 | Validate everything before building anything.**

### 0.1 — Environment Validation

```python
import sys, psutil, subprocess
print(f"Python: {sys.version}")
ram_gb = psutil.virtual_memory().total / 1e9
print(f"RAM: {ram_gb:.1f} GB")
assert ram_gb >= 14, f"Only {ram_gb:.1f}GB RAM — need 14GB minimum for safety margin"

packages = [
    "sentence-transformers", "lightgbm", "scikit-learn", "pandas",
    "numpy", "pyarrow", "tqdm", "rank_bm25", "anthropic", "scipy"
]
subprocess.run(["pip", "install"] + packages, check=True)
```

### 0.2 — Data Integrity + Distribution Analysis

```python
import gzip, json
from collections import Counter
from datetime import date

REFERENCE_DATE = date(2026, 6, 6)  # pin to dataset reference date

candidates = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in f:
        if line.strip():
            candidates.append(json.loads(line))

assert len(candidates) == 100_000, f"Expected 100K, got {len(candidates)}"
ids = [c["candidate_id"] for c in candidates]
assert len(set(ids)) == 100_000, "Duplicate IDs found!"

yoe = [c["profile"]["years_of_experience"] for c in candidates]
countries = Counter(c["profile"]["country"] for c in candidates)
work_modes = Counter(c["redrob_signals"]["preferred_work_mode"] for c in candidates)
open_to_work = sum(1 for c in candidates if c["redrob_signals"]["open_to_work_flag"])
has_assessments = sum(1 for c in candidates if c["redrob_signals"]["skill_assessment_scores"])
has_github = sum(1 for c in candidates if c["redrob_signals"]["github_activity_score"] != -1)
saved_30d_vals = [c["redrob_signals"]["saved_by_recruiters_30d"] for c in candidates]
search_app_vals = [c["redrob_signals"]["search_appearance_30d"] for c in candidates]

print(f"YOE: min={min(yoe):.1f}, median={sorted(yoe)[50000]:.1f}, max={max(yoe):.1f}")
print(f"Countries top-5: {countries.most_common(5)}")
print(f"Work modes: {dict(work_modes)}")
print(f"Open to work: {open_to_work / 1000:.1f}%")
print(f"Have assessments: {has_assessments / 1000:.1f}%")
print(f"Have GitHub: {has_github / 1000:.1f}%")
# v4: check distribution of underused signals
print(f"saved_by_recruiters_30d: p50={sorted(saved_30d_vals)[50000]}, p90={sorted(saved_30d_vals)[90000]}")
print(f"search_appearance_30d: p50={sorted(search_app_vals)[50000]}, p90={sorted(search_app_vals)[90000]}")

text_lens = [sum(len(r["description"]) for r in c["career_history"]) for c in candidates]
print(f"Career desc length: p10={sorted(text_lens)[10000]}, p50={sorted(text_lens)[50000]}, p90={sorted(text_lens)[90000]}")
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
# Decision: ETA < 1.5h → use bge-large | 1.5–3h → use bge-base | >3h → MiniLM
```

---

## Stage 1: JD Intelligence Layer
**Days 1–2 | Extract structured meaning including implied signals.**

### 1.1 — LLM-Powered JD Parsing with Confidence Scores + Requirement Strengths

**[v4]** Two new additions: (a) per-field automated fallback values for low-confidence fields (DeepSeek), (b) `requirement_strength` per hard/soft requirement (ChatGPT) so LambdaMART can learn which reqs matter more.

```python
import anthropic, json

JD_TEXT = open("job_description.md").read()
client = anthropic.Anthropic()

parse_prompt = f"""
Parse the following job description into the exact JSON schema below.
Include implicit signals — "shipped to real users" implies production_deployment_required=true.
For each field, also provide a confidence (0.0-1.0) and the exact JD text that supports it.
For hard_requirements and soft_requirements, ALSO provide a strength weight (0.0-1.0) indicating
how critical this requirement is to the role based on JD language.
Respond with ONLY valid JSON, no markdown fences, no explanation.

JD:
{JD_TEXT}

Schema:
{{
  "role_title": {{"value": "...", "confidence": 0.99, "evidence": "..."}},
  "experience_range": {{"value": {{"min": 5, "max": 9}}, "confidence": 0.99, "evidence": "5-9 years"}},
  "hard_requirements": {{
    "value": [
      {{"name": "vector_search_infra", "strength": 1.0}},
      {{"name": "embedding_models", "strength": 0.95}},
      {{"name": "ranking_evaluation", "strength": 0.90}},
      {{"name": "python_production", "strength": 0.85}}
    ],
    "confidence": 0.97,
    "evidence": "Things you absolutely need..."
  }},
  "soft_requirements": {{
    "value": [
      {{"name": "llm_finetuning", "strength": 0.70}},
      {{"name": "learning_to_rank", "strength": 0.75}},
      {{"name": "hr_tech_experience", "strength": 0.50}},
      {{"name": "distributed_systems", "strength": 0.60}},
      {{"name": "hybrid_retrieval", "strength": 0.80}}
    ],
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
  "acceptable_countries": {{"value": ["India"], "confidence": 0.95, "evidence": "Outside India: case-by-case"}},
  "notice_period_ideal_days": {{"value": 30, "confidence": 0.99, "evidence": "..."}},
  "notice_period_max_days": {{"value": 90, "confidence": 0.85, "evidence": "30+ day notice candidates still in scope"}},
  "salary_band_inr_lpa": {{"value": null, "confidence": 0.0, "evidence": "not mentioned in JD — leave null"}},
  "preferred_work_modes": {{"value": ["hybrid", "flexible", "onsite"], "confidence": 0.90, "evidence": "..."}},
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

# [v4] Automated fallback values for low-confidence fields
FALLBACK_VALUES = {
    "experience_range": {"min": 3, "max": 12},
    "preferred_locations": ["Pune", "Noida", "Hyderabad", "Mumbai", "Delhi NCR", "Bangalore"],
    "acceptable_countries": ["India"],
    "notice_period_ideal_days": 30,
    "notice_period_max_days": 90,
    "preferred_work_modes": ["hybrid", "remote", "onsite", "flexible"],
}
for field, fallback in FALLBACK_VALUES.items():
    if field in jd_parsed_with_confidence:
        conf = jd_parsed_with_confidence[field].get("confidence", 1.0)
        if conf < 0.7:
            print(f"⚠ Auto-applying fallback for low-confidence field: {field} (conf={conf:.2f})")
            jd_parsed_with_confidence[field]["value"] = fallback

jd_parsed = {k: v["value"] for k, v in jd_parsed_with_confidence.items()}

# [v4] Build requirement-strength lookup for feature weighting
HARD_REQ_STRENGTHS = {
    r["name"]: r["strength"]
    for r in jd_parsed.get("hard_requirements", [])
    if isinstance(r, dict)
}
SOFT_REQ_STRENGTHS = {
    r["name"]: r["strength"]
    for r in jd_parsed.get("soft_requirements", [])
    if isinstance(r, dict)
}
# Flatten to name lists for backward compatibility
jd_parsed["hard_requirements"] = list(HARD_REQ_STRENGTHS.keys())
jd_parsed["soft_requirements"] = list(SOFT_REQ_STRENGTHS.keys())

json.dump(jd_parsed, open("artifacts/jd_parsed.json", "w"), indent=2)
json.dump(jd_parsed_with_confidence, open("artifacts/jd_parsed_confidence.json", "w"), indent=2)
json.dump({"hard": HARD_REQ_STRENGTHS, "soft": SOFT_REQ_STRENGTHS},
          open("artifacts/req_strengths.json", "w"), indent=2)
print("✅ JD parsed with confidence scores and requirement strengths.")

low_conf = {k: v for k, v in jd_parsed_with_confidence.items() if v.get("confidence", 1.0) < 0.7}
if low_conf:
    print(f"⚠ Low-confidence fields (fallbacks applied): {list(low_conf.keys())}")
```

### 1.2 — Skill Taxonomy

```python
SKILL_GROUPS = {
    # Hard requirement groups
    "vector_search_infra": [
        "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
        "elasticsearch", "pgvector", "chromadb", "annoy", "vespa", "typesense",
        "vector database", "ann", "approximate nearest neighbor", "hnsw", "haystack",
        "vector store", "vector index"
    ],
    "embedding_models": [
        "sentence-transformers", "sentence transformers", "bge", "e5", "openai embeddings",
        "ada-002", "instructor", "gte", "clip", "cohere embed", "text embeddings",
        "dense retrieval", "bi-encoder", "dual encoder", "semantic search", "embeddings",
        "embedding model", "representation learning"
    ],
    "ranking_evaluation": [
        "ndcg", "mrr", "map", "mean average precision", "a/b testing", "a/b test",
        "learning to rank", "ltr", "lambdamart", "xgboost ranker", "listwise",
        "pairwise", "offline evaluation", "online evaluation", "ranking metrics",
        "information retrieval", "recall@k", "precision@k", "hit rate", "ranknet",
        "evaluation framework", "ranking pipeline"
    ],
    "python_production": [
        "python", "fastapi", "flask", "django", "pydantic", "asyncio", "celery",
        "gunicorn", "uvicorn", "pytest", "mypy", "production python",
        "rest api", "grpc", "microservice"
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

### 1.3 — JD Embeddings (offline, one-time)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-large-en-v1.5")
JD_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

jd_full_text = open("job_description.md").read()
ideal_candidate_text = jd_parsed["ideal_profile_summary"]

jd_embedding = model.encode(JD_QUERY_PREFIX + jd_full_text, normalize_embeddings=True)
ideal_embedding = model.encode(JD_QUERY_PREFIX + ideal_candidate_text, normalize_embeddings=True)

np.save("artifacts/jd_embedding.npy", jd_embedding)
np.save("artifacts/ideal_embedding.npy", ideal_embedding)
print(f"✅ JD embeddings saved: {jd_embedding.shape}")
```

---

## Stage 2: Candidate Feature Engineering
**Days 3–6 | All features extracted, validated, persisted.**

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
    features.update(behavioral_features(candidate["redrob_signals"]))  # includes new v4 signals
    features.update(honeypot_features(candidate))

    # Persist raw profile fields needed at inference
    features["candidate_id"]          = candidate["candidate_id"]
    features["years_of_experience"]   = candidate["profile"]["years_of_experience"]
    features["current_title"]         = candidate["profile"]["current_title"]
    features["current_company"]       = candidate["profile"]["current_company"]
    features["current_company_size"]  = candidate["profile"]["current_company_size"]
    features["location"]              = candidate["profile"]["location"]
    features["country"]               = candidate["profile"]["country"]

    # Disqualifiers computed here (not lazily in rank.py)
    disq_hit, disq_reasons, disq_penalty = compute_disqualifier_flags(features, candidate)
    features["disqualifier_hit"]      = disq_hit
    features["disqualifier_reasons"]  = disq_reasons
    features["disqualifier_penalty"]  = disq_penalty  # [v4] per-type soft penalty, not binary cap

    return features

all_features = []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in tqdm(f, total=100_000):
        if line.strip():
            c = json.loads(line)
            all_features.append(extract_all_features(c, jd_parsed))

df = pd.DataFrame(all_features)
df.to_parquet("artifacts/features_100k.parquet", index=False)
print(f"✅ Features: {df.shape[0]} rows × {df.shape[1]} cols")

required_cols = [
    "candidate_id", "years_of_experience", "current_title", "current_company",
    "consulting_ratio", "years_in_product", "deployment_score", "retrieval_ir_score",
    "production_evidence_score", "startup_fit_score", "recruiter_intent_score",  # [v4]
    "honeypot_score", "is_likely_honeypot",
    "disqualifier_hit", "disqualifier_reasons", "disqualifier_penalty",  # [v4]
    "behavioral_score", "location_score", "avg_hard_req_coverage",
    "saved_30d", "search_appearance_30d_feat",  # [v4]
]
for col in required_cols:
    assert col in df.columns, f"MISSING COLUMN: {col}"
print("✅ All required columns present.")
```

### 2.2 — Career Features

**[v4] Bug fix: `title_chaser_flag` direction corrected.** The JD defines a title-chaser as someone who hops companies frequently to collect promotions (seniority *climbing* via job changes, not staying). v3 incorrectly flagged stagnant careers.

```python
CONSULTING_FIRMS_SET = set(SKILL_GROUPS["consulting_firms"])
LARGE_PRODUCT_COMPANIES = {
    "google", "amazon", "microsoft", "meta", "apple", "netflix", "flipkart",
    "paytm", "swiggy", "zomato", "ola", "nykaa", "phonepe", "razorpay",
    "meesho", "zepto", "cred", "groww", "zerodha"
}

# [v4] Production evidence keywords — separate from deployment_score
# These specifically capture "shipped to real users, latency, SLA, monitoring"
PRODUCTION_EVIDENCE_KEYWORDS = [
    "served", "latency", "throughput", "sla", "monitoring", "a/b test",
    "production incidents", "deployment pipeline", "millions of users",
    "real users", "at scale", "rollout", "canary", "load test",
    "p99", "p95", "uptime", "reliability", "on-call"
]

PRODUCTION_ML_KEYWORDS = [
    "shipped", "production", "deployed", "serving", "inference", "api endpoint",
    "real users", "at scale", "latency", "throughput", "monitoring", "a/b test",
    "retrieval", "ranking", "embedding", "vector"
]

# [v4] FIXED: bare "search" removed — only multi-word anchored IR terms
RETRIEVAL_IR_KEYWORDS = [
    "information retrieval", "vector retrieval", "hybrid retrieval", "dense retrieval",
    "sparse retrieval", "semantic retrieval", "candidate retrieval",
    "ranking pipeline", "ranking model", "ranking system",
    "recommendation system", "recommendation engine",
    "ndcg", "mrr", "map@", "recall@", "precision@",
    "faiss", "milvus", "elasticsearch", "opensearch", "vector db", "vector database",
    "hybrid search", "bm25", "reranking", "cross-encoder", "learning to rank",
    "lambdamart", "ranknet"
]

# [v4] Startup fit keywords
STARTUP_KEYWORDS = [
    "founded", "startup", "seed", "series a", "series b", "early stage",
    "end-to-end", "0 to 1", "zero to one", "wore many hats", "full ownership",
    "cross-functional", "shipped fast", "shipped quickly", "moved fast",
    "ambiguity", "self-directed", "no playbook", "greenfield", "solo"
]

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
        return 0.75
    if "startup" in industry.lower() or "saas" in industry.lower():
        return min(base + 0.1, 1.0)
    return base

def is_consulting_company(company_name):
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
    return 3

def role_transition_score(history):
    """
    [v4 new] Score whether career trajectory trends toward AI/ML.
    Positive = moved toward ML; negative = moved away.
    """
    ML_ROLE_KEYWORDS = {
        "ml engineer": 3, "ai engineer": 3, "machine learning engineer": 3,
        "research engineer": 2, "data scientist": 2, "nlp engineer": 3,
        "search engineer": 3, "ranking engineer": 3,
        "data engineer": 1, "software engineer": 1, "backend engineer": 1,
        "analytics engineer": 1, "full stack": 0, "frontend": -1,
        "marketing": -2, "sales": -2, "hr": -2, "operations": -1
    }
    sorted_roles = sorted(history, key=lambda r: r["start_date"])
    role_scores = []
    for r in sorted_roles:
        title = r["title"].lower()
        score = 0
        for keyword, val in ML_ROLE_KEYWORDS.items():
            if keyword in title:
                score = val
                break
        role_scores.append(score)
    if len(role_scores) < 2:
        return 0.5  # neutral
    delta = role_scores[-1] - role_scores[0]
    return max(0.0, min(1.0, (delta + 4) / 8))  # normalize -4..+4 → 0..1

def career_features(candidate):
    history = candidate["career_history"]
    profile = candidate["profile"]
    total_months = sum(r["duration_months"] for r in history)
    if total_months == 0:
        return {k: 0.0 for k in [
            "consulting_ratio", "product_ratio", "consulting_penalty",
            "years_in_product", "deployment_score", "retrieval_ir_score",
            "production_evidence_score", "startup_fit_score",
            "seniority_trend", "job_hop_penalty", "title_chaser_flag",
            "current_size_score", "n_roles", "role_transition_score"
        ]}

    consulting_months = sum(r["duration_months"] for r in history if is_consulting_company(r["company"]))
    product_months = total_months - consulting_months
    consulting_ratio = consulting_months / max(total_months, 1)
    product_ratio = product_months / max(total_months, 1)
    consulting_penalty = consulting_ratio * (1 - product_ratio)
    years_in_product = product_months / 12

    all_descriptions = " ".join(r["description"].lower() for r in history)

    prod_ml_hits = sum(1 for kw in PRODUCTION_ML_KEYWORDS if kw in all_descriptions)
    retrieval_ir_hits = sum(1 for kw in RETRIEVAL_IR_KEYWORDS if kw in all_descriptions)
    n_roles = max(len(history), 1)
    deployment_score = min(prod_ml_hits / (n_roles * 3), 1.0)
    retrieval_ir_score = min(retrieval_ir_hits / (n_roles * 2), 1.0)

    # [v4] Dedicated production evidence score
    prod_evidence_hits = sum(1 for kw in PRODUCTION_EVIDENCE_KEYWORDS if kw in all_descriptions)
    production_evidence_score = min(prod_evidence_hits / 5, 1.0)

    # [v4] Startup fit score
    startup_hits = sum(1 for kw in STARTUP_KEYWORDS if kw in all_descriptions)
    startup_role_hits = sum(
        1 for r in history
        if r.get("company_size", "") in ["1-10", "11-50", "51-200"]
        and not is_consulting_company(r["company"])
    )
    startup_fit_score = min((startup_hits / 4 + startup_role_hits / 3) / 2, 1.0)

    sorted_history = sorted(history, key=lambda r: r["start_date"])
    seniority_scores_list = [compute_seniority_score(r["title"]) for r in sorted_history]

    if len(seniority_scores_list) >= 2:
        seniority_trend = (seniority_scores_list[-1] - seniority_scores_list[0]) / max(len(seniority_scores_list), 1)
        seniority_trend = max(-1, min(1, seniority_trend / 3))
    else:
        seniority_trend = 0.0

    cutoff = "2018-06-01"
    recent_roles = [r for r in history if r["start_date"] >= cutoff and not r["is_current"]]
    short_stints = sum(1 for r in recent_roles if r["duration_months"] < 18)
    job_hop_penalty = min(short_stints / 3, 1.0)

    # [v4] FIXED title_chaser_flag direction:
    # A title-chaser hops companies rapidly AND seniority CLIMBS (collecting promotions via moves).
    # Stagnant career (seniority not climbing) is NOT a title-chaser.
    seniority_is_climbing_fast = (
        len(seniority_scores_list) >= 3
        and seniority_scores_list[-1] > seniority_scores_list[0]  # climbing, not stagnant
        and short_stints >= 2   # via frequent short moves
    )
    title_chaser_flag = float(seniority_is_climbing_fast)

    current_role = next((r for r in history if r.get("is_current")), history[0])
    current_size_score = get_company_size_score(
        profile["current_company"],
        profile["current_company_size"],
        profile.get("current_industry", "")
    )

    return {
        "consulting_ratio": consulting_ratio,
        "product_ratio": product_ratio,
        "consulting_penalty": consulting_penalty,
        "years_in_product": min(years_in_product / 8, 1.0),
        "deployment_score": deployment_score,
        "retrieval_ir_score": retrieval_ir_score,
        "production_evidence_score": production_evidence_score,   # [v4]
        "startup_fit_score": startup_fit_score,                   # [v4]
        "seniority_trend": (seniority_trend + 1) / 2,
        "job_hop_penalty": job_hop_penalty,
        "title_chaser_flag": title_chaser_flag,                   # [v4 fixed direction]
        "current_size_score": current_size_score,
        "n_roles": n_roles,
        "role_transition_score": role_transition_score(history),  # [v4]
    }
```

### 2.3 — Skills Features (with Assessment Credibility and Requirement Strengths)

```python
req_strengths = json.load(open("artifacts/req_strengths.json"))
HARD_REQ_STRENGTHS = req_strengths["hard"]
SOFT_REQ_STRENGTHS = req_strengths["soft"]

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
            for akey, aval in assessments_lower.items():
                if term in akey or akey in term:
                    if aval >= 70:   score = max(score, 1.0)
                    elif aval >= 50: score = max(score, 0.8)
                    elif aval >= 30: score = max(score, 0.5)
                    else:            score = max(score, 0.2)
            if term in skills_lower:
                s = skills_lower[term]
                prof_map = {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.75, "expert": 0.9}
                duration_bonus = min(s.get("duration_months", 0) / 36, 0.1)
                skill_score = prof_map[s["proficiency"]] + duration_bonus
                if s["proficiency"] == "expert" and not any(
                    term in akey or akey in term for akey in assessments_lower
                ):
                    skill_score *= 0.75
                score = max(score, skill_score)
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
            matched_score = next(
                (v for k, v in assessments.items()
                 if skill["name"].lower() in k or k in skill["name"].lower()), None
            )
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

    # [v4] Strength-weighted hard req score (not just average)
    req_names = jd_parsed["hard_requirements"]
    strength_weighted_sum = sum(
        coverage.get(f"hard_req_{req}", 0) * HARD_REQ_STRENGTHS.get(req, 1.0)
        for req in req_names
    )
    total_strength = sum(HARD_REQ_STRENGTHS.get(req, 1.0) for req in req_names) or 1
    weighted_hard_coverage = strength_weighted_sum / total_strength

    avg_hard_coverage = sum(hard_scores) / max(len(hard_scores), 1)
    min_hard_coverage = min(hard_scores) if hard_scores else 0.0

    skills_text = " ".join(s["name"].lower() for s in candidate["skills"]) + " " + \
                  " ".join(r["description"].lower() for r in candidate["career_history"])

    soft_hits = sum(
        SOFT_REQ_STRENGTHS.get(group, 0.5)  # [v4] weighted, not binary
        for group in jd_parsed["soft_requirements"]
        if any(term in skills_text for term in SKILL_GROUPS.get(group, []))
    )
    soft_coverage = soft_hits / max(sum(SOFT_REQ_STRENGTHS.values()), 1)

    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})
    all_jd_terms = set()
    for group in jd_parsed["hard_requirements"] + jd_parsed["soft_requirements"]:
        all_jd_terms.update(SKILL_GROUPS.get(group, []))
    jd_relevant_assessments = [v for k, v in assessments.items()
                                if any(term in k.lower() or k.lower() in term
                                       for term in all_jd_terms)]
    avg_relevant_assessment = (sum(jd_relevant_assessments) / len(jd_relevant_assessments)
                               if jd_relevant_assessments else -1)

    cv_speech_hits = sum(1 for term in SKILL_GROUPS["cv_speech_robotics"] if term in skills_text)
    ir_ml_hits = sum(1 for group in ["vector_search_infra", "embedding_models",
                                      "ranking_evaluation", "hybrid_retrieval"]
                     for term in SKILL_GROUPS[group] if term in skills_text)
    domain_mismatch = float(cv_speech_hits > 3 and ir_ml_hits < 2)

    langchain_hits = sum(1 for term in SKILL_GROUPS["langchain_llm_wrapper_only"]
                         if term in skills_text)
    has_pre_llm_ml = ir_ml_hits >= 2 or avg_relevant_assessment > 50

    return {
        **coverage,
        "avg_hard_req_coverage": avg_hard_coverage,
        "weighted_hard_req_coverage": weighted_hard_coverage,   # [v4]
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
        return {"edu_tier_score": 0.35, "is_cs_adjacent": 0.0,
                "has_postgrad": 0.0, "edu_recency": 0.5}
    best = max(edu, key=lambda e: TIER_SCORE.get(e.get("tier", "unknown"), 0.45))
    tier_score = TIER_SCORE.get(best.get("tier", "unknown"), 0.45)
    field = best.get("field_of_study", "").lower()
    is_cs = float(any(f in field for f in CS_ADJACENT_FIELDS))
    degree = best.get("degree", "").lower()
    has_postgrad = float(any(d in degree for d in
                             ["m.tech", "mtech", "m.s.", "ms", "mba", "phd", "ph.d", "master"]))
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

```python
PREFERRED_LOCS = {"pune", "noida", "hyderabad", "mumbai", "delhi", "ncr",
                  "gurgaon", "gurugram", "bengaluru", "bangalore"}

def salary_fit(candidate_range, jd_range):
    if jd_range is None:
        return 0.5
    cmin, cmax = candidate_range["min"], candidate_range["max"]
    jmin, jmax = jd_range["min"], jd_range["max"]
    overlap_low, overlap_high = max(cmin, jmin), min(cmax, jmax)
    if overlap_high >= overlap_low:
        return min((overlap_high - overlap_low) / max(jmax - jmin, 1), 1.0)
    gap = overlap_low - overlap_high
    return max(0.0, 1.0 - gap / max(jmax - jmin, 1))

def notice_score(days):
    """[v4] More granular notice scoring per DeepSeek suggestion"""
    if days <= 15:   return 1.0
    elif days <= 30: return 0.95
    elif days <= 45: return 0.85   # [v4] was 0.95
    elif days <= 60: return 0.65   # [v4] was 0.7
    elif days <= 90: return 0.40   # [v4] was 0.45
    else:            return 0.15

def logistics_features(candidate, jd_parsed):
    signals = candidate["redrob_signals"]
    profile = candidate["profile"]
    loc_lower = profile["location"].lower()
    country_lower = profile["country"].lower()
    in_preferred = any(city in loc_lower for city in PREFERRED_LOCS)

    if in_preferred:                                             location_score = 1.0
    elif country_lower == "india" and signals["willing_to_relocate"]: location_score = 0.65
    elif country_lower == "india":                               location_score = 0.35
    elif signals["willing_to_relocate"]:                         location_score = 0.30
    else:                                                        location_score = 0.05

    n_score = notice_score(signals["notice_period_days"])

    jd_sal = jd_parsed.get("salary_band_inr_lpa")
    sal_range = signals["expected_salary_range_inr_lpa"]
    s_score = salary_fit(sal_range, jd_sal)

    preferred_mode = signals["preferred_work_mode"]
    jd_modes = set(jd_parsed["preferred_work_modes"])
    if preferred_mode in jd_modes or preferred_mode == "flexible":  work_mode_score = 1.0
    elif preferred_mode == "onsite" and "hybrid" in jd_modes:       work_mode_score = 0.8
    elif preferred_mode == "remote":
        work_mode_score = 0.3 if not signals["willing_to_relocate"] else 0.5
    else:                                                            work_mode_score = 0.6

    return {
        "location_score": location_score,
        "notice_score": n_score,
        "salary_score": s_score,
        "work_mode_score": work_mode_score,
        "willing_to_relocate": float(signals["willing_to_relocate"]),
        "notice_period_days": signals["notice_period_days"],
    }
```

### 2.6 — Behavioral Features

**[v4]** `search_appearance_30d` and `saved_by_recruiters_30d` now both enter the composite AND are exported as standalone features for LambdaMART. `recruiter_intent_score` is the dedicated signal combining what organizers explicitly flagged.

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

    # [v4] search_appearance now used (was computed but excluded from composite in v3)
    search_app_30d = min(signals["search_appearance_30d"] / 200, 1.0)

    # [v4] profile_views signals doc: recruiters viewing = interest signal
    profile_views_30d = min(signals["profile_views_received_30d"] / 50, 1.0)

    # [v4] Dedicated recruiter intent score — combines all recruiter-action signals
    recruiter_intent_score = (
        0.35 * saved_30d +           # saved = strongest recruiter intent
        0.30 * search_app_30d +      # appearing in search = passive discoverable
        0.20 * profile_views_30d +   # viewed = recruiter interest
        0.15 * response_rate         # responsive = hirable
    )

    interview_completion = signals["interview_completion_rate"]
    offer_acceptance_raw = signals["offer_acceptance_rate"]
    offer_acceptance = 0.5 if offer_acceptance_raw == -1 else offer_acceptance_raw
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
        0.22 * open_to_work +
        0.20 * responsiveness +
        0.15 * recency +
        0.15 * recruiter_intent_score +   # [v4] was absent from composite
        0.10 * track_record +
        0.08 * credibility +
        0.06 * apps_30d +
        0.04 * github_score
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
        "search_appearance_30d_feat": search_app_30d,  # [v4] renamed to avoid parquet col clash
        "profile_views_30d_feat": profile_views_30d,   # [v4]
        "recruiter_intent_score": recruiter_intent_score,  # [v4]
    }
```

### 2.7 — Honeypot Features (10 signals)

```python
from datetime import datetime

def honeypot_features(candidate):
    profile = candidate["profile"]
    history = candidate["career_history"]
    skills = candidate["skills"]
    signals = candidate["redrob_signals"]
    yoe = profile["years_of_experience"]
    penalty = 1.0
    honeypot_signal_log = []  # [v4] track which signals fired for reasoning

    # Signal 1: Experience > company age
    current_role = next((r for r in history if r.get("is_current")), None)
    if current_role:
        try:
            company_start = datetime.strptime(current_role["start_date"], "%Y-%m-%d")
            if yoe > (REFERENCE_DATE.year - company_start.year + 5):
                penalty *= 0.15
                honeypot_signal_log.append("exp_exceeds_company_age")
        except: pass

    # Signal 2: Tenure impossibly long relative to YOE
    if current_role and current_role["duration_months"] > yoe * 12 * 0.9:
        penalty *= 0.2
        honeypot_signal_log.append("tenure_exceeds_yoe")

    # Signal 3: Zero-duration expert skills
    zero_duration_experts = [s for s in skills
                              if s["proficiency"] == "expert"
                              and s.get("duration_months", None) == 0]
    if len(zero_duration_experts) >= 2:
        penalty *= 0.2
        honeypot_signal_log.append("zero_duration_experts")
    elif len(zero_duration_experts) == 1:
        penalty *= 0.6

    # Signal 4: Assessment contradicts expert self-report
    assessments_lower = {k.lower(): v for k, v in signals.get("skill_assessment_scores", {}).items()}
    contradictions = sum(
        1 for s in skills
        if s["proficiency"] == "expert"
        for akey, aval in assessments_lower.items()
        if (s["name"].lower() in akey or akey in s["name"].lower()) and aval < 35
    )
    if contradictions >= 2:
        penalty *= 0.15
        honeypot_signal_log.append("assessment_contradictions")
    elif contradictions == 1:
        penalty *= 0.45

    # Signal 5: Too many expert skills for experience level
    expert_count = sum(1 for s in skills if s["proficiency"] == "expert")
    if yoe < 4 and expert_count >= 5:
        penalty *= 0.25
        honeypot_signal_log.append("expert_count_vs_yoe")
    elif yoe < 6 and expert_count >= 8:
        penalty *= 0.40
    elif yoe < 8 and expert_count >= 12:
        penalty *= 0.55

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
                    honeypot_signal_log.append("overlapping_roles")
            except: pass

    # Signal 7: Non-technical role with deep AI skill claims
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
        penalty *= 0.1
        honeypot_signal_log.append("title_skill_contradiction")

    # Signal 8: Education timeline impossibility
    edu = candidate.get("education", [])
    for e in edu:
        start, end = e.get("start_year", 1990), e.get("end_year", 2000)
        if end < start:
            penalty *= 0.3
            honeypot_signal_log.append("edu_impossible_timeline")
        other_degrees = [x for x in edu if x != e]
        for other in other_degrees:
            if "ph" in e.get("degree", "").lower() and "b." in other.get("degree", "").lower():
                if e.get("end_year", 9999) < other.get("start_year", 9999):
                    penalty *= 0.2
                    honeypot_signal_log.append("phd_before_bachelor")

    # Signal 9: Non-ML career but claims multiple expert AI tools
    all_career_text = " ".join(r["description"].lower() for r in history)
    career_has_ml = any(kw in all_career_text for kw in [
        "machine learning", "deep learning", "neural", "model", "embedding",
        "retrieval", "ranking", "inference", "training", "dataset"
    ])
    career_roles_non_ml = all(
        any(nr in r["title"].lower() for nr in [
            "accountant", "marketing", "sales", "hr", "graphic", "content", "operations"
        ]) for r in history
    ) if history else False
    highly_specialized_ai_skills = sum(
        1 for s in skills
        if s["proficiency"] in ["advanced", "expert"]
        and any(t in s["name"].lower() for t in ["milvus", "qdrant", "lora", "qlora", "peft", "faiss"])
    )
    if career_roles_non_ml and not career_has_ml and highly_specialized_ai_skills >= 2:
        penalty *= 0.15
        honeypot_signal_log.append("career_skill_mismatch")

    # Signal 10: LangChain expert with no LangChain assessment passed
    for s in skills:
        if "langchain" in s["name"].lower() and s["proficiency"] == "expert":
            lc_assessed = any("langchain" in k for k in assessments_lower)
            if lc_assessed and next(
                (v for k, v in assessments_lower.items() if "langchain" in k), 100
            ) < 30:
                penalty *= 0.5
                honeypot_signal_log.append("langchain_expert_fail")

    honeypot_score = max(penalty, 0.001)
    return {
        "honeypot_score": honeypot_score,
        "is_likely_honeypot": float(honeypot_score < 0.15),
        "honeypot_signal_log": "|".join(honeypot_signal_log) if honeypot_signal_log else "",
    }
```

### 2.8 — Disqualifier Flags (per-type soft penalties)

**[v4]** Replaces the universal 0.12 hard cap with per-disqualifier penalty multipliers. Some are near-zero (honeypot, zero hard reqs), others are softer (consulting background). This resolves the "collapses nuance" problem DeepSeek identified.

```python
# [v4] Per-type disqualifier caps — not all disqualifiers are equally fatal
DISQUALIFIER_PENALTIES = {
    "pure_consulting":         0.25,   # Not impossible — some consulting then product is ok
    "zero_hard_reqs":          0.10,   # Very hard to rank if core skills absent
    "too_junior":              0.35,   # Junior but could be strong
    "no_production_ml":        0.20,   # Strong signal but not guaranteed
    "wrong_domain":            0.25,   # CV/speech without any IR — very low fit
    "honeypot":                0.05,   # Near-zero by design
    "unreachable_location":    0.20,   # Hard barrier but not absolute
    "langchain_only_under_12mo": 0.15, # JD's most explicit disqualifier
    "no_code_in_18mo":         0.20,   # Managers who stopped shipping
}

def compute_disqualifier_flags(features, raw_candidate):
    signals = raw_candidate["redrob_signals"]
    profile = raw_candidate["profile"]
    flags = []

    if features["consulting_penalty"] > 0.85:
        flags.append("pure_consulting")
    if features["min_hard_req_coverage"] < 0.15:
        flags.append("zero_hard_reqs")
    if features["years_of_experience"] < 3:
        flags.append("too_junior")
    if features["deployment_score"] < 0.1 and features["retrieval_ir_score"] < 0.1:
        flags.append("no_production_ml")
    if features["domain_mismatch_flag"] == 1.0:
        flags.append("wrong_domain")
    if features["is_likely_honeypot"] == 1.0:
        flags.append("honeypot")
    if features["location_score"] < 0.1:
        flags.append("unreachable_location")
    if features["langchain_only_flag"] == 1.0:
        flags.append("langchain_only_under_12mo")

    code_keywords = ["implemented", "built", "wrote", "shipped", "deployed", "coded",
                     "developed", "python", "api", "sql", "bash", "script", "pull request",
                     "commit", "git"]
    recent_history = [r for r in raw_candidate["career_history"]
                      if r.get("start_date", "2000-01-01") >= "2024-01-01"]
    recent_descriptions = " ".join(r["description"].lower() for r in recent_history)
    title_lower = features.get("current_title", "").lower()
    is_arch_role = any(t in title_lower for t in
                       ["architect", "principal", "tech lead", "vp", "director"])
    has_recent_code = any(kw in recent_descriptions for kw in code_keywords)
    if is_arch_role and not has_recent_code and len(recent_history) > 0:
        flags.append("no_code_in_18mo")

    # [v4] Compute the minimum (most punishing) per-type penalty across all flags
    # If multiple disqualifiers fire, take the lowest penalty cap (strictest)
    if not flags:
        disq_penalty = 1.0
    else:
        disq_penalty = min(DISQUALIFIER_PENALTIES.get(f, 0.15) for f in flags)

    return bool(flags), "|".join(flags), disq_penalty
```

---

## Stage 3: Hybrid Retrieval Index
**Days 4–7 (parallel to Stage 2)**

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

### 3.2 — BM25 Index

**[v4]** BM25 query now uses the verbatim technical paragraph from the JD, not an artificial keyword list. DeepSeek correctly pointed out that BM25 works best with natural language queries.

```python
from rank_bm25 import BM25Okapi
import json, gzip, pickle, numpy as np

corpus, ids = [], []
with gzip.open("candidates.jsonl.gz", "rt") as f:
    for line in f:
        if line.strip():
            c = json.loads(line)
            corpus.append(synthesize_candidate_text(c).lower().split())
            ids.append(c["candidate_id"])

bm25 = BM25Okapi(corpus)
with open("artifacts/bm25_index.pkl", "wb") as f:
    pickle.dump((bm25, ids), f)

# [v4] FIXED: use natural JD technical paragraphs, not artificial keyword list
# This is the verbatim "Things you absolutely need" section of the JD
JD_BM25_QUERY = """
You have built vector search infrastructure — FAISS, Milvus, Pinecone, Weaviate, Qdrant,
OpenSearch, or equivalent — and shipped embedding-based retrieval to real users.
You know how to evaluate ranking quality with NDCG, MAP, MRR, and build hybrid search
combining BM25 with dense retrieval. You write production Python, have worked with
sentence-transformers, and understand LambdaMART or similar learning-to-rank approaches.
""".lower().split()

bm25_scores = bm25.get_scores(JD_BM25_QUERY)
np.save("artifacts/bm25_scores.npy", bm25_scores)
print(f"BM25 scores: max={bm25_scores.max():.3f}, mean={bm25_scores.mean():.3f}")
```

### 3.3 — Semantic Encoding (batch-efficient)

**[v4]** Role descriptions batch-encoded together for efficiency (DeepSeek's performance suggestion).

```python
def batch_encode_candidates(model_name, output_path, batch_size=64):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    texts, ids = [], []
    with gzip.open("candidates.jsonl.gz", "rt") as f:
        for line in tqdm(f, total=100_000, desc="Encoding"):
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
    embeddings, ids = batch_encode_candidates("BAAI/bge-large-en-v1.5",
                                              "artifacts/candidate_embeddings.npy")
except MemoryError:
    embeddings, ids = batch_encode_candidates("BAAI/bge-base-en-v1.5",
                                              "artifacts/candidate_embeddings.npy")
```

### 3.4 — Hybrid Score Computation

```python
def compute_hybrid_scores(embedding_path, jd_emb, ideal_emb, bm25_scores_path):
    embeddings = np.load(embedding_path, mmap_mode="r")
    jd_emb_loaded = np.load(jd_emb)
    ideal_emb_loaded = np.load(ideal_emb)
    bm25_raw = np.load(bm25_scores_path)

    semantic = 0.6 * (embeddings @ jd_emb_loaded) + 0.4 * (embeddings @ ideal_emb_loaded)
    bm25_max = bm25_raw.max()
    bm25_norm = bm25_raw / bm25_max if bm25_max > 0 else bm25_raw
    hybrid = 0.60 * semantic + 0.40 * bm25_norm   # BM25 elevated for IR-keyword-dense JD

    np.save("artifacts/semantic_scores.npy", semantic)
    np.save("artifacts/hybrid_scores.npy", hybrid)
    return hybrid

hybrid = compute_hybrid_scores(
    "artifacts/candidate_embeddings.npy", "artifacts/jd_embedding.npy",
    "artifacts/ideal_embedding.npy", "artifacts/bm25_scores.npy"
)
```

### 3.5 — Per-Role Semantic Score + Merge

```python
def compute_per_role_scores(embedding_ids, jd_embedding_path, top10k_ids, model_name):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    jd_emb = np.load(jd_embedding_path)
    top10k_set = set(top10k_ids)

    # [v4] Batch-encode all role descriptions for top10k together (efficient)
    all_texts = []
    all_ids = []
    role_index = []  # (candidate_id, role_idx)

    with gzip.open("candidates.jsonl.gz", "rt") as f:
        for line in tqdm(f, total=100_000):
            if not line.strip(): continue
            c = json.loads(line)
            if c["candidate_id"] not in top10k_set: continue
            for i, role in enumerate(c["career_history"]):
                all_texts.append(role["description"])
                all_ids.append(c["candidate_id"])

    all_role_embeddings = model.encode(all_texts, batch_size=64, normalize_embeddings=True,
                                       show_progress_bar=True)

    from collections import defaultdict
    per_role_scores = defaultdict(list)
    for i, (cid, emb) in enumerate(zip(all_ids, all_role_embeddings)):
        per_role_scores[cid].append(float(emb @ jd_emb))

    per_role_max = {cid: max(scores) for cid, scores in per_role_scores.items()}
    json.dump(per_role_max, open("artifacts/per_role_scores.json", "w"))
    return per_role_max

embedding_ids = json.load(open("artifacts/candidate_embeddings_ids.json"))
id_to_hybrid = {cid: float(hybrid[i]) for i, cid in enumerate(embedding_ids)}
top10k_ids = sorted(id_to_hybrid, key=id_to_hybrid.get, reverse=True)[:10000]
json.dump(top10k_ids, open("artifacts/top10k_ids.json", "w"))

per_role_scores = compute_per_role_scores(
    embedding_ids, "artifacts/jd_embedding.npy", top10k_ids, "BAAI/bge-base-en-v1.5"
)

features_df = pd.read_parquet("artifacts/features_100k.parquet")
features_df["per_role_semantic_score"] = features_df["candidate_id"].map(
    lambda cid: per_role_scores.get(cid, id_to_hybrid.get(cid, 0.0))
)
features_df["hybrid_score"] = features_df["candidate_id"].map(id_to_hybrid)
semantic_id_map = {cid: float(np.load("artifacts/semantic_scores.npy")[i])
                   for i, cid in enumerate(embedding_ids)}
features_df["semantic_score"] = features_df["candidate_id"].map(semantic_id_map)
features_df.to_parquet("artifacts/features_100k.parquet", index=False)
print("✅ Retrieval scores merged.")
```

---

## Stage 4: Honeypot Audit
**Day 7 | Zero honeypots in top 100 — no exceptions.**

```python
def audit_honeypots(features_df, threshold=0.15):
    suspects = features_df[features_df["honeypot_score"] < threshold].copy()
    suspects = suspects.sort_values("honeypot_score")
    print(f"Honeypot suspects (score < {threshold}): {len(suspects)} (spec says ~80)")
    for _, row in suspects.head(15).iterrows():
        print(f"  {row['candidate_id']}: score={row['honeypot_score']:.3f} "
              f"signals={row.get('honeypot_signal_log', '?')} "
              f"title={row.get('current_title', '?')} yoe={row.get('years_of_experience', '?'):.1f}")
    return suspects["candidate_id"].tolist()
```

**Manual verification checklist (mandatory — don't skip):**
- [ ] Top 15 most suspicious candidates reviewed against full JSON profile
- [ ] Impossible timelines, assessment contradictions, role mismatches confirmed
- [ ] Zero honeypot suspects appear in top-200 after first scoring pass
- [ ] `honeypot_signal_log` checked for false-positives (signals 7–10 most at risk)

---

## Stage 5: Multi-Signal Scoring Engine
**Days 8–9 | Initial composite ranking — the Day-9 safety-net submission.**

### 5.1 — Experience Modifier

**[v4]** Replaced hard discontinuities with smooth sigmoid. A candidate at 4.9yr no longer gets a 10% penalty vs 5.0yr.

```python
import math

def experience_modifier(yoe):
    """[v4] Smooth function — peaks at 7yr (JD says 5-9yr, center is 7yr)"""
    optimal = 7.0
    # Gaussian-like falloff centered at optimal
    if yoe < optimal:
        return max(0.50, 1.0 - 0.15 * max(0, optimal - yoe) / optimal)
    else:
        return max(0.72, 1.0 - 0.07 * max(0, yoe - optimal) / optimal)
```

### 5.2 — Composite Relevance Score

**[v4]** Three additions: `production_evidence_score`, `startup_fit_score`, and `recruiter_intent_score` enter the composite. `weighted_hard_req_coverage` replaces simple average.

```python
def compute_relevance_score(features, semantic_score, hybrid_score, per_role_score):
    # Career trajectory (30%)
    s_career = (
        0.28 * (1.0 - features["consulting_penalty"]) +
        0.25 * features["deployment_score"] +
        0.15 * features["production_evidence_score"] +   # [v4]
        0.12 * features["retrieval_ir_score"] +
        0.08 * features["startup_fit_score"] +           # [v4]
        0.07 * features["years_in_product"] +
        0.05 * features["seniority_trend"]
        - 0.08 * features["job_hop_penalty"]
        - 0.06 * features["title_chaser_flag"]
    )
    s_career = max(0.0, min(1.0, s_career))

    # Skills (28%) — use strength-weighted hard req coverage
    s_skills = (
        0.40 * features["weighted_hard_req_coverage"] +   # [v4]
        0.15 * features["min_hard_req_coverage"] +
        0.15 * features["soft_req_coverage"] +
        0.10 * features["has_relevant_assessments"] * features["avg_relevant_assessment"] +
        0.10 * features["assessment_credibility"] +
        0.10 * features["role_transition_score"]           # [v4]
        - 0.10 * features["domain_mismatch_flag"]
    )
    s_skills = max(0.0, min(1.0, s_skills))

    # Semantic (22%) — blend global + per-role max-pooling
    s_semantic = 0.6 * float(hybrid_score) + 0.4 * float(per_role_score)

    # Education (8%)
    s_edu = (
        0.60 * features["edu_tier_score"] +
        0.25 * features["is_cs_adjacent"] +
        0.15 * features["has_postgrad"]
    )

    # Logistics (12%)
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


def compute_final_score(relevance, behavioral_score, honeypot_score,
                        disqualifier_hit, disqualifier_penalty, yoe):
    # [v4] Per-type disqualifier penalty (soft cap, not universal 0.12)
    if disqualifier_hit:
        relevance = min(relevance, disqualifier_penalty)

    # [v4] Smooth experience modifier
    relevance *= experience_modifier(yoe)

    # Behavioral multiplier — keeps disengaged candidates lower even if skill-match is high
    behavioral_multiplier = 0.35 + 0.65 * behavioral_score

    # Recruiter intent bonus — explicit signal that recruiters already notice this person
    recruiter_intent_boost = 1.0 + 0.08 * behavioral_score  # small bonus, not dominant

    score = relevance * behavioral_multiplier * honeypot_score * recruiter_intent_boost
    return max(score, 0.001)
```

### 5.3 — Golden Set Validation

```python
"""
Read 15+ candidates manually. Classify each 0/1/2.
Strong fit (2): 5-9yr product company, retrieval/search/embedding work, India + open to work
Not fit (0): pure consulting, wrong domain, outside India + won't relocate, honeypot, <3yr exp
"""
GOLDEN_SET = {
    # Fill in after manual review on Day 8
    "CAND_XXXXXXX": 2,
}

def validate_golden_set(scores_dict, golden_set):
    strong  = [scores_dict[cid] for cid, label in golden_set.items() if label == 2]
    not_fit = [scores_dict[cid] for cid, label in golden_set.items() if label == 0]
    assert min(strong) > max(not_fit), "FAIL: some not-fit outscores a strong-fit!"
    print("✅ Golden set validation passed.")
```

---

## Stage 6: LambdaMART Ensemble Re-Ranker
**Days 10–12 | Learn non-linear signal combinations, NDCG-optimized.**

### 6.1 — Feature Matrix

**[v4]** New features added: `production_evidence_score`, `startup_fit_score`, `recruiter_intent_score`, `role_transition_score`, `weighted_hard_req_coverage`, `search_appearance_30d_feat`, `profile_views_30d_feat`, `disqualifier_penalty`.

```python
LAMBDAMART_FEATURES = [
    # Semantic
    "semantic_score", "hybrid_score", "per_role_semantic_score",
    # Career
    "consulting_ratio", "consulting_penalty", "product_ratio",
    "years_in_product", "deployment_score", "retrieval_ir_score",
    "production_evidence_score",         # [v4]
    "startup_fit_score",                 # [v4]
    "role_transition_score",             # [v4]
    "seniority_trend", "job_hop_penalty", "title_chaser_flag",
    "current_size_score", "n_roles",
    # Skills
    "avg_hard_req_coverage",
    "weighted_hard_req_coverage",        # [v4]
    "min_hard_req_coverage", "soft_req_coverage",
    "avg_relevant_assessment", "has_relevant_assessments", "assessment_credibility",
    "domain_mismatch_flag", "langchain_only_flag",
    # Individual hard req coverage scores
    "hard_req_vector_search_infra", "hard_req_embedding_models",
    "hard_req_ranking_evaluation", "hard_req_python_production",
    # Logistics
    "location_score", "notice_score", "salary_score", "work_mode_score",
    "willing_to_relocate", "notice_period_days",
    # Education
    "edu_tier_score", "is_cs_adjacent", "has_postgrad",
    # Behavioral
    "behavioral_score", "open_to_work", "recency", "responsiveness",
    "track_record", "github_score", "apps_30d",
    "saved_30d",
    "search_appearance_30d_feat",        # [v4]
    "profile_views_30d_feat",            # [v4]
    "recruiter_intent_score",            # [v4]
    # Honeypot
    "honeypot_score",
    # Experience + disqualifiers
    "years_of_experience",
    "disqualifier_penalty",              # [v4] soft per-type value, not binary
]
```

### 6.2 — Pseudo-Label Strategy

**[v4]** Stratified sampling now covers: top quartile, bottom quartile, disqualifier-hit candidates, and edge cases near the 5yr and 9yr experience boundaries.

```python
import anthropic, json, time
from tqdm import tqdm

client = anthropic.Anthropic()

JD_SUMMARY = """
Role: Senior AI Engineer at Redrob AI (Series A, Pune/Noida India)
STRONG FIT (label 3): 5-9yr at product companies; production vector DB / embedding retrieval / hybrid search; ships code; India or willing to relocate; notice ≤ 90 days
MODERATE FIT (label 2): Adjacent skills (data eng, NLP, some retrieval) but missing 1-2 hard reqs; or right skills but partial consulting background
WEAK FIT (label 1): Some relevant skills but career mostly unrelated; or too junior/senior
NOT A FIT (label 0): Pure consulting; wrong domain (CV/speech only); outside India + won't relocate; honeypot; non-technical with AI keywords
"""

def pseudo_label_candidate(c, label_strategy="recruiter"):
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
    """[v4] Richer stratification: quartiles + disqualifier-hit + experience boundaries"""
    df = features_df.copy()
    df["quartile"] = pd.qcut(df["composite_score"], 4, labels=[0, 1, 2, 3])
    base = df.groupby("quartile").sample(n // 6, random_state=42)

    # Extra samples near key decision boundaries
    disq_sample = df[df["disqualifier_hit"] == True].sample(
        min(n // 8, len(df[df["disqualifier_hit"] == True])), random_state=42
    )
    exp_boundary = df[df["years_of_experience"].between(4, 5) | df["years_of_experience"].between(9, 11)]
    exp_sample = exp_boundary.sample(min(n // 8, len(exp_boundary)), random_state=42)

    combined = pd.concat([base, disq_sample, exp_sample]).drop_duplicates("candidate_id")
    return combined.sample(min(n, len(combined)), random_state=42)["candidate_id"].tolist()
```

### 6.3 — Three-Model Training with Optimized Ensemble Weights

**[v4]** Ensemble weights are no longer fixed at 0.40/0.30/0.30. They are optimized via `scipy.optimize.minimize` on the cross-validation composite metric (DeepSeek's suggestion).

```python
import lightgbm as lgb
from sklearn.model_selection import KFold
from scipy.optimize import minimize
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
    model.save_model(f"artifacts/ranker_{model_name}.lgb")
    return model


def compute_composite_metric(y_true, y_pred):
    """0.50×NDCG@10 + 0.30×NDCG@50 + 0.15×MAP + 0.05×P@10"""
    from sklearn.metrics import ndcg_score
    ndcg10 = ndcg_score([y_true], [y_pred], k=10)
    ndcg50 = ndcg_score([y_true], [y_pred], k=50)
    ranked_idx = np.argsort(y_pred)[::-1]
    relevant = (y_true[ranked_idx] >= 2).astype(float)
    cum_relevant = np.cumsum(relevant)
    ranks = np.arange(1, len(relevant) + 1)
    map_score = float(np.sum(relevant * cum_relevant / ranks) / max(relevant.sum(), 1))
    p10 = float(relevant[:10].sum() / 10)
    composite = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * map_score + 0.05 * p10
    return composite, {"ndcg10": ndcg10, "ndcg50": ndcg50, "map": map_score, "p10": p10}


def optimize_ensemble_weights(X_val, y_val, models):
    """[v4] Empirically optimize ensemble weights instead of guessing."""
    model_preds = [m.predict(X_val) for m in models]

    def objective(w):
        w_norm = np.array(w) / (np.sum(np.abs(w)) + 1e-8)
        ensemble = sum(w_norm[i] * model_preds[i] for i in range(len(models)))
        return -compute_composite_metric(y_val, ensemble)[0]

    result = minimize(objective, [1/3, 1/3, 1/3],
                      bounds=[(0.0, 1.0)] * len(models),
                      method="L-BFGS-B")
    optimized = np.array(result.x)
    optimized = optimized / optimized.sum()
    print(f"Optimized weights: {[f'{w:.3f}' for w in optimized]}")
    return optimized


def cross_validate_and_train(labeled_df, full_feature_df, label_col="recruiter_label"):
    labeled_features = full_feature_df[
        full_feature_df["candidate_id"].isin(labeled_df["candidate_id"])
    ].merge(labeled_df[["candidate_id", label_col]], on="candidate_id")

    X = labeled_features[LAMBDAMART_FEATURES].fillna(0).values
    y = labeled_features[label_col].values

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    fold_composites = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        model = train_lambdamart(X[train_idx], y[train_idx], X[val_idx], y[val_idx],
                                  model_name=f"fold{fold}_{label_col}")
        val_pred = model.predict(X[val_idx])
        composite, breakdown = compute_composite_metric(y[val_idx], val_pred)
        fold_composites.append(composite)
        print(f"  Fold {fold+1}: composite={composite:.4f} "
              f"(NDCG@10={breakdown['ndcg10']:.4f}, NDCG@50={breakdown['ndcg50']:.4f}, "
              f"MAP={breakdown['map']:.4f}, P@10={breakdown['p10']:.4f})")

    print(f"\nMean CV composite: {np.mean(fold_composites):.4f} ± {np.std(fold_composites):.4f}")
    return np.mean(fold_composites)


def build_ensemble_with_optimized_weights(features_df, labeled_df):
    """[v4] Load all three models + optimize weights empirically."""
    X = features_df[LAMBDAMART_FEATURES].fillna(0).values

    model_paths = ["ranker_recruiter.lgb", "ranker_hard_reqs.lgb", "ranker_semantic.lgb"]
    models = [lgb.Booster(model_file=f"artifacts/{p}") for p in model_paths]

    # Use a held-out labeled sample for weight optimization
    labeled_features = features_df[
        features_df["candidate_id"].isin(labeled_df["candidate_id"])
    ].merge(labeled_df[["candidate_id", "recruiter_label"]], on="candidate_id")
    X_labeled = labeled_features[LAMBDAMART_FEATURES].fillna(0).values
    y_labeled = labeled_features["recruiter_label"].values

    # [v4] Empirically optimized weights
    weights = optimize_ensemble_weights(X_labeled, y_labeled, models)
    json.dump(weights.tolist(), open("artifacts/ensemble_weights.json", "w"))

    ensemble_scores = np.zeros(len(features_df))
    for model, weight in zip(models, weights):
        preds = model.predict(X)
        preds = (preds - preds.min()) / max(preds.max() - preds.min(), 1e-8)
        ensemble_scores += weight * preds

    return ensemble_scores
```

**Decision rule:** If ensemble composite > (Stage 5 baseline + 0.03) → use ensemble. Otherwise ship Stage 5 composite.

---

## Stage 7: Reasoning Generation + Final Output
**Days 12–14 | Sandbox: Day 13**

### 7.1 — Reasoning Context Builder

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
        concerns.append(f"not in preferred location ({profile['location']}, "
                        f"relocate: {signals['willing_to_relocate']})")
    if features.get("consulting_penalty", 0) > 0.5:
        concerns.append("significant consulting background")
    if features.get("recency", 1.0) < 0.5:
        concerns.append("low platform activity")
    if features.get("avg_hard_req_coverage", 1.0) < 0.6:
        concerns.append("missing some hard requirements")
    if features.get("production_evidence_score", 1.0) < 0.2:
        concerns.append("limited production deployment evidence")

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
        "recruiter_intent_score": features.get("recruiter_intent_score", 0),
        "production_evidence_score": features.get("production_evidence_score", 0),
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
- Production evidence strength: {'high' if ctx['production_evidence_score'] > 0.6 else 'moderate' if ctx['production_evidence_score'] > 0.3 else 'low'}
- Recruiter interest score: {ctx['recruiter_intent_score']:.2f}
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

**[v4]** `--candidates` flag now validates candidate IDs against parquet index (integrity check). Disqualifier penalty uses per-type soft value. Reasoning fallback uses actual features, not generic string.

```python
#!/usr/bin/env python3
"""
rank.py — Final ranking step. Must run in ≤5 min, CPU only, no network.
Usage: python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
"""
import argparse, json, csv, time, gzip
import numpy as np
import pandas as pd
import lightgbm as lgb

LAMBDAMART_FEATURES = [...]  # same list as Stage 6

def experience_modifier(yoe): ...   # same as Stage 5
def compute_final_score(...): ...   # same as Stage 5

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="submission.csv")
    args = parser.parse_args()
    t0 = time.time()

    print("[1/7] Loading precomputed features...")
    features_df = pd.read_parquet("artifacts/features_100k.parquet")
    features_df = features_df.set_index("candidate_id")

    # [v4 FIX] Actually validate --candidates against parquet
    print("[2/7] Validating candidate IDs from --candidates flag...")
    candidate_ids_from_file = []
    with gzip.open(args.candidates, "rt") as f:
        for line in f:
            if line.strip():
                candidate_ids_from_file.append(json.loads(line)["candidate_id"])
    candidate_ids_set = set(candidate_ids_from_file)
    parquet_ids_set = set(features_df.index)
    if candidate_ids_set != parquet_ids_set:
        missing = candidate_ids_set - parquet_ids_set
        extra = parquet_ids_set - candidate_ids_set
        print(f"  ⚠ ID mismatch: {len(missing)} in candidates not in parquet, "
              f"{len(extra)} in parquet not in candidates")
        # Restrict to intersection
        features_df = features_df[features_df.index.isin(candidate_ids_set)]
    else:
        print(f"  ✅ {len(candidate_ids_from_file)} candidate IDs validated.")

    print("[3/7] Loading embeddings and computing scores...")
    embeddings = np.load("artifacts/candidate_embeddings.npy", mmap_mode="r")
    embedding_ids = json.load(open("artifacts/candidate_embeddings_ids.json"))
    id_to_idx = {cid: i for i, cid in enumerate(embedding_ids)}

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
    if "per_role_semantic_score" not in features_df.columns:
        features_df["per_role_semantic_score"] = features_df["hybrid_score"]

    print("[4/7] Scoring with LambdaMART ensemble (optimized weights)...")
    X = features_df[LAMBDAMART_FEATURES].fillna(0).values

    # Load empirically optimized weights
    try:
        weights = json.load(open("artifacts/ensemble_weights.json"))
    except FileNotFoundError:
        weights = [0.40, 0.30, 0.30]  # fallback

    ensemble_scores = np.zeros(len(features_df))
    model_paths = ["ranker_recruiter.lgb", "ranker_hard_reqs.lgb", "ranker_semantic.lgb"]
    for model_path, weight in zip(model_paths, weights):
        try:
            m = lgb.Booster(model_file=f"artifacts/{model_path}")
            preds = m.predict(X)
            preds = (preds - preds.min()) / max(preds.max() - preds.min(), 1e-8)
            ensemble_scores += weight * preds
        except FileNotFoundError:
            print(f"  ⚠ {model_path} not found — skipping")
    features_df["lm_score"] = ensemble_scores

    print("[5/7] Applying per-type disqualifier penalties and honeypot scores...")
    # [v4] Per-type soft penalty (column already in parquet)
    features_df["final_score"] = features_df.apply(
        lambda row: (
            row["lm_score"]
            * row.get("honeypot_score", 1.0)
            * (row.get("disqualifier_penalty", 1.0) if row.get("disqualifier_hit", False) else 1.0)
        ),
        axis=1
    )

    print("[6/7] Selecting top 100...")
    ranked = features_df.sort_values(
        ["final_score", "candidate_id"], ascending=[False, True]
    ).head(100)

    print("[7/7] Writing submission CSV...")
    reasoning_cache = json.load(open("artifacts/reasoning_cache.json"))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank_num, (cid, row) in enumerate(ranked.iterrows(), start=1):
            # [v4] FIX: substantive fallback reasoning using actual features
            if cid in reasoning_cache:
                reasoning = reasoning_cache[cid]
            else:
                # Fallback with real data, not generic string
                title = row.get("current_title", "Engineer")
                yoe = row.get("years_of_experience", "?")
                concerns = []
                if row.get("notice_period_days", 0) > 60:
                    concerns.append(f"notice {int(row.get('notice_period_days', 0))} days")
                if row.get("location_score", 1.0) < 0.65:
                    concerns.append("non-preferred location")
                concern_str = f" Note: {'; '.join(concerns)}." if concerns else ""
                reasoning = (
                    f"{title} with {yoe:.1f}yr experience and "
                    f"retrieval/embedding score {row.get('retrieval_ir_score', 0):.2f}.{concern_str}"
                )
            writer.writerow([cid, rank_num, f"{row['final_score']:.4f}", reasoning])

    elapsed = time.time() - t0
    print(f"✅ Done in {elapsed:.1f}s")
    validate_submission(args.out, features_df)

if __name__ == "__main__":
    main()
```

### 7.3 — Submission Validator

**[v4]** Now validates score range and reasoning sentence count (DeepSeek's spec compliance additions).

```python
def validate_submission(filepath, features_df):
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
        assert scores[i] >= scores[i+1] - 1e-6, f"❌ Scores not non-increasing at rank {i+1}→{i+2}"
    assert len(set(scores)) > 10, "❌ Too few unique scores — model not differentiating"

    # [v4] Score range check
    for r in rows:
        s = float(r["score"])
        assert 0.0 <= s <= 1.0, f"❌ Score out of range [0,1]: {s}"

    # [v4] Reasoning sanity check
    reasonings = [r["reasoning"] for r in rows]
    assert all(len(r) > 20 for r in reasonings), "❌ Some reasoning strings too short"
    assert len(set(reasonings)) > 50, "❌ Too many duplicate reasoning strings"
    for r in rows:
        text = r["reasoning"]
        sentence_count = text.count(".") + text.count("!") + text.count("?")
        if sentence_count > 4:
            print(f"  ⚠ Rank {r['rank']}: reasoning may be too long ({sentence_count} sentences)")

    # CRITICAL: Check honeypot rate BEFORE upload
    if features_df is not None:
        submitted_ids = set(ids)
        submitted_features = features_df[features_df.index.isin(submitted_ids)]
        honeypot_count = int(submitted_features["is_likely_honeypot"].sum())
        honeypot_rate = honeypot_count / 100.0
        print(f"  Honeypot rate in top 100: {honeypot_count}/100 ({honeypot_rate:.1%})")
        assert honeypot_rate <= 0.08, \
            f"❌ CRITICAL: {honeypot_count} honeypots in top 100 ({honeypot_rate:.1%}) — DISQUALIFICATION RISK!"
        if honeypot_rate > 0.05:
            print(f"  ⚠ WARNING: {honeypot_count} honeypots — threshold is 10%, cutting it close.")

    print(f"✅ Submission valid: 100 rows, ranks 1-100, scores in [0,1], "
          f"unique reasonings, honeypot rate {honeypot_count}/100")
```

### 7.4 — Sandbox Deployment (Day 13 — mandatory per spec §10.5)

```python
# Option A: Google Colab (simplest — link to notebook that runs end-to-end)
# Create: redrob_ranker_demo.ipynb
# - Cell 1: pip install deps, download artifacts from Google Drive
# - Cell 2: Load sample_candidates.json (≤100 candidates, from bundle)
# - Cell 3: Run rank.py equivalent on the sample
# - Cell 4: Display ranked output and validate
# Target: < 2 min runtime on CPU for 100 candidates

# Option B: Streamlit Cloud (slightly nicer UX)
# app.py:
import streamlit as st
st.title("Redrob Ranker Demo")
uploaded = st.file_uploader("Upload candidates.jsonl (≤100 candidates)", type=["jsonl", "gz"])
if uploaded and st.button("Rank"):
    # run pipeline on uploaded file
    # show ranked table
    pass

# Checklist before sharing sandbox link:
# [ ] Runs on sample_candidates.json from the bundle without modification
# [ ] Completes within 5 minutes on CPU
# [ ] Produces valid CSV (pass validate_submission)
# [ ] No network calls during ranking
```

---

## 15-Day Implementation Roadmap

| Day | Task | Output | Checkpoint |
|-----|------|--------|------------|
| 1 | Stage 0: env setup, data audit, benchmark. Stage 1: JD parse with confidence + req strengths | `jd_parsed.json`, `req_strengths.json`, model selected | All JD fields confidence > 0.7 or fallback applied |
| 2 | Stage 1 complete: skill taxonomy, JD embedding. Review confidence audit | `jd_embedding.npy`, `skill_groups.py` | Low-conf fields fallback-corrected |
| 3 | Stage 2: career + education + disqualifier features. Fix `title_chaser_flag` | `feature_engineering.py` unit-tested | Unit tests pass including v4 fixed features |
| 4 | Stage 2: skills + assessment features + `production_evidence_score` + `startup_fit_score`. Start encoding overnight | Skills code done, encoding starts | Encoding ETA confirmed |
| 5 | Stage 2: logistics + behavioral features (incl `recruiter_intent_score`). Full pipeline. Stage 3: BM25 index (natural query) | `extract_all_features()` complete, `bm25_index.pkl` | BM25 scores non-zero for IR terms |
| 6 | Run full feature extraction on 100K | `features_100k.parquet` | Assert shape: 100K × ~65 cols. All v4 required cols present. |
| 7 | Stage 3: encoding done. Compute hybrid scores. Merge per-role scores (batch). Stage 4: honeypot audit | `hybrid_scores.npy`, `per_role_scores.json`, `honeypot_audit.txt` | Manual verify 15 honeypot suspects |
| 8 | Stage 5: composite scoring + golden set validation | `composite_scores.npy` | Golden set: all strong-fit > all not-fit |
| **9** | **Submit #1** (Stage 5 composite, no LambdaMART). Generate preliminary reasoning | `submission_v1.csv` submitted | Validator passes incl honeypot rate + score range + reasoning checks |
| 10 | Stage 6: pseudo-label 2,500 candidates with richer stratification | `pseudo_labels_recruiter.csv`, `pseudo_labels_hard_reqs.csv` | Label dist: ~10% 3s, 25% 2s, 35% 1s, 30% 0s |
| 11 | Train all 3 LambdaMART models. 5-fold CV. **Optimize ensemble weights with scipy.** | `ranker_*.lgb`, `ensemble_weights.json` | CV composite > Stage 5 + 0.03? |
| 12 | Stage 7: reasoning for top-150 candidates | `reasoning_cache.json` | Spot-check 20: no hallucinations |
| 13 | Build `rank.py` end-to-end (with v4 fixes). Timing benchmark. **Build sandbox** | `rank.py`, sandbox link live | Runtime < 2min; sandbox runs on sample_candidates.json |
| **14** | **Submit #2** (ensemble + reasoning + all v4 fixes). Full validator | `submission_v2.csv` submitted | Validator passes |
| 15 | Buffer. If meaningful improvement identified, submit #3 | Final submission | |

**Submission strategy:** #1 on Day 9 is your safety net. Never ship without the full validator. Honeypot check is load-bearing.

---

## Complete Fix Summary

| v3 Bug | v4 Fix | Stage |
|--------|--------|-------|
| `title_chaser_flag` inverted — fired on stagnant careers | Fires when seniority climbs fast via short moves | 2.2 |
| Disqualifier penalty: 0.12 cap in Stage 5, multiply in rank.py | Unified per-type penalty dict; Stage 5 and rank.py use same value | 2.8 + 7.2 |
| `saved_by_recruiters_30d` and `search_appearance_30d` unused in composite | Both enter behavioral composite and LambdaMART feature list | 2.6 |
| Bare `"search"` in IR keywords → false positives | Replaced with anchored multi-word IR terms only | 2.2 |
| `rank.py --candidates` flag ignored | Validates IDs against parquet index, restricts to intersection | 7.2 |
| Experience modifier had hard discontinuities | Smooth sigmoid centered at 7yr (midpoint of 5-9yr JD range) | 5.1 |
| Pseudo-label sampling: quartiles only | Enriched with disqualifier-hit + experience boundary samples | 6.2 |
| Ensemble weights fixed at 0.40/0.30/0.30 | scipy.optimize minimizes on CV composite metric | 6.3 |
| BM25 query was artificial keyword list | Natural language technical paragraph from JD | 3.2 |
| Per-role encoding was serial (slow) | Batch-encoded together in one model.encode() call | 3.5 |
| Reasoning fallback was generic string | Fallback uses actual title, YOE, retrieval score, concerns | 7.2 |
| Validator missing score range and sentence count checks | Both added | 7.3 |
| Low-confidence JD fields: only printed | Automated fallback values applied | 1.1 |

| v3 Missing Feature | v4 Addition | Stage |
|--------------------|-------------|-------|
| No `production_evidence_score` | Separate feature: "served", "latency", "SLA", "monitoring" keywords | 2.2 |
| No `startup_fit_score` | Company size ≤200 + ownership/ambiguity language | 2.2 |
| No `recruiter_intent_score` | Dedicated composite of saved, search appearances, profile views | 2.6 |
| No `role_transition_score` | Career trajectory toward ML/AI scoring | 2.2 |
| No requirement strength weights | Per-req strength from JD parse → weighted hard req coverage | 1.1 + 2.3 |
| No `honeypot_signal_log` | Track which signals fired for debugging and reasoning | 2.7 |

---

## File Structure

```
redrob-ranker/
├── README.md
├── requirements.txt
├── submission_metadata.yaml
│
├── precompute/
│   ├── 01_parse_jd.py                   # Stage 1 — includes req strengths + fallbacks [v4]
│   ├── 02_encode_candidates.py          # Stage 3 — batch-efficient per-role encoding [v4]
│   ├── 03_extract_features.py           # Stage 2 — all v4 features incl production_evidence etc.
│   ├── 04_build_bm25_index.py           # Stage 3 — natural JD query [v4]
│   ├── 05_compute_hybrid_scores.py      # Stage 3
│   ├── 06_compute_per_role_scores.py    # Stage 3 — batch-efficient [v4]
│   ├── 07_honeypot_audit.py             # Stage 4 — with signal log [v4]
│   ├── 08_generate_pseudolabels.py      # Stage 6 — richer stratification [v4]
│   ├── 09_train_lambdamart_ensemble.py  # Stage 6 — optimized weights [v4]
│   └── 10_generate_reasoning.py        # Stage 7
│
├── rank.py                              # ≤5 min, CPU only, no network, --candidates validated [v4]
├── validate_submission.py               # score range + sentence count checks [v4]
├── sandbox/
│   └── redrob_demo.ipynb               # Day 13 deliverable
│
├── artifacts/
│   ├── jd_parsed.json
│   ├── jd_parsed_confidence.json
│   ├── req_strengths.json               # [v4] hard/soft req strength weights
│   ├── jd_embedding.npy
│   ├── ideal_embedding.npy
│   ├── features_100k.parquet            # ~65 cols including all v4 features
│   ├── candidate_embeddings.npy
│   ├── candidate_embeddings_ids.json
│   ├── bm25_scores.npy
│   ├── per_role_scores.json
│   ├── semantic_scores.npy
│   ├── hybrid_scores.npy
│   ├── ranker_recruiter.lgb
│   ├── ranker_hard_reqs.lgb
│   ├── ranker_semantic.lgb
│   ├── ensemble_weights.json            # [v4] scipy-optimized weights
│   └── reasoning_cache.json
│
└── tests/
    ├── test_features.py
    ├── test_honeypot.py
    ├── test_golden_set.py
    ├── test_disqualifiers.py
    └── test_title_chaser.py             # [v4] unit test for corrected flag
```

```bash
# Pre-computation (once, ~4-8 hours total):
python precompute/01_parse_jd.py
python precompute/02_encode_candidates.py    # triggers per-role batch encoding too
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

---

## Compute Constraint Summary

| Component | Memory | Notes |
|-----------|--------|-------|
| features_100k.parquet (~65 cols) | ~60MB | Fine |
| bge-large embeddings (100K × 1024 × 4B) | ~410MB | Fine |
| bm25_scores.npy | ~0.8MB | Fine |
| 3 LambdaMART models | ~15MB each | Fine |
| **Total** | **~550MB** | Well under 16GB |

| rank.py operation | Time estimate |
|-------------------|---------------|
| Parquet load | ~1s |
| Embedding matrix multiply (100K × 1024) | ~2s |
| 3× LambdaMART predict (100K rows) | ~5s |
| Sort + CSV write | ~1s |
| ID validation pass | ~3s |
| **Total** | **~12–20s** |

**Realistically well under 1 minute. Massive headroom under 5-minute ceiling.**

---

## What Each Judge Question This Architecture Answers

| Likely Stage 5 question | Architecture answer |
|-------------------------|---------------------|
| "Why hybrid BM25 + semantic?" | IR-keyword-dense JD (NDCG, LambdaMART, Milvus) — embeddings underweight exact rare terms; BM25 catches them |
| "How do you handle honeypots?" | 10 signals across 4 categories (timeline, assessment contradiction, role mismatch, career mismatch); empirically validated against the spec's ~80 honeypot count |
| "Why three LambdaMART models?" | Label diversity hedge — Model A (holistic recruiter), B (hard reqs only), C (semantic quantized); ensemble weights empirically optimized, not guessed |
| "What's your biggest uncertainty?" | Pseudo-label quality — labels are Claude-generated, not human. We partially hedge with prompt diversity and optimized ensemble weights, but honest: if Claude has a systematic bias on this JD, both A and B inherit it |
| "How do you avoid hallucinating reasoning?" | Reasoning prompt references ONLY facts pre-built into `reasoning_context`. No skill names or employers not present in the actual profile can enter the output |
| "Does your code actually run in 5 minutes?" | rank.py is ~12-20 seconds. Can demo live. |
| "What changed between your submissions?" | v1 (Day 9) = Stage 5 composite (safety net). v2 (Day 14) = LambdaMART ensemble + all v4 fixes. Diff is clear and defensible |
```
