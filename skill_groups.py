"""
Step 1.2 — Skill Taxonomy Expansion  (merged: Claude + ChatGPT best-of-both)
Stage 1: JD Intelligence Layer

Maps raw skill mentions in candidate text to canonical skill groups.
A candidate with "FAISS" gets vector_search credit even without "Pinecone".
A candidate at "Wipro" their entire career gets consulting_firm_flag = True.

Group structure
───────────────
  HARD REQUIREMENT GROUPS  (4)  — directly map to jd_parsed hard_requirements
    vector_search, embedding_models, retrieval_infra, ranking_eval

  SOFT REQUIREMENT GROUPS  (7)  — map to soft_requirements + inferred signals
    learning_to_rank, llm_finetune, llm_prod, nlp_foundations,
    distributed_systems, ml_ops_infra, python_stack

  DOMAIN SIGNAL GROUPS     (2)  — positive soft signals from JD
    hrtech, marketplace

  DISQUALIFIER / FLAG GROUPS (4) — negative signals; bury or penalise
    consulting_firms, research_only_signals,
    cv_speech_robotics, tutorial_framework_signals

Usage:
    from skill_groups import SKILL_GROUPS, get_skill_groups,
                             get_hard_req_coverage, get_consulting_ratio,
                             is_consulting_firm_only
"""

# ─────────────────────────────────────────────────────────────────────────────
# Taxonomy
# ─────────────────────────────────────────────────────────────────────────────

SKILL_GROUPS: dict[str, list[str]] = {

    # =========================================================================
    # HARD REQUIREMENT GROUPS
    # =========================================================================

    # JD: "vector databases or hybrid search infrastructure"
    "vector_search": [
        # Purpose-built vector DBs
        "pinecone", "weaviate", "qdrant", "milvus", "zilliz",
        "chromadb", "marqo", "vald",
        # General search engines with vector support
        "opensearch", "elasticsearch", "solr", "lucene",
        # Library-level ANN
        "faiss", "annoy", "hnswlib", "nmslib", "scann", "voyager",
        # Postgres extension
        "pgvector",
        # Redis vector
        "redis vector", "redis-vector", "redisearch",
        # Others
        "typesense", "vespa",
    ],

    # JD: "embeddings-based retrieval systems"
    "embedding_models": [
        # Sentence-transformer family
        "sentence-transformers", "sentence_transformers", "sbert", "all-minilm",
        # BGE / E5 / GTE family
        "bge", "baai/bge", "e5", "intfloat/e5", "gte", "multilingual-e5",
        # OpenAI
        "openai embeddings", "text-embedding-ada", "text-embedding-3",
        "text-embedding", "ada",
        # Other hosted / open
        "instructor", "instructor-xl",
        "cohere embed", "cohere embeddings",
        "nomic-embed", "jina embeddings",
        "clip", "simcse", "contriever",
        # Architecture terms (encoder pattern)
        "bi-encoder", "bi encoder", "cross-encoder", "cross encoder",
        # Sparse / late-interaction
        "colbert", "splade",
    ],

    # JD: "production embeddings-based retrieval … BM25 + dense, hybrid"
    "retrieval_infra": [
        # RAG / hybrid paradigms
        "rag", "retrieval augmented generation", "retrieval-augmented",
        "hybrid retrieval", "hybrid search",
        "candidate retrieval", "document retrieval", "retrieval pipeline",
        "vector retrieval",
        # Sparse retrieval
        "bm25", "tf-idf", "tfidf", "sparse retrieval", "sparse vectors",
        # Reranking
        "reranking", "re-ranking", "re ranking", "semantic ranking",
        # Two-tower / DPR
        "two-tower", "two tower", "dual encoder",
        "dense passage retrieval", "dpr",
        "dense retrieval",
        # ANN / search infra terms
        "inverted index", "approximate nearest neighbor", "ann",
        "nearest neighbor search", "ann search",
        # Higher-level search concepts
        "semantic search", "neural search",
        "information retrieval", "search relevance",
        "query understanding", "candidate generation",
    ],

    # JD: "evaluation frameworks for ranking — NDCG, MRR, MAP, A/B testing"
    "ranking_eval": [
        # Core metrics
        "ndcg", "mrr", "map",
        "mean average precision", "mean reciprocal rank",
        "normalized discounted cumulative gain",
        "precision@k", "recall@k", "hit rate", "auc",
        # Offline / online eval
        "offline evaluation", "offline eval", "offline-to-online",
        "online evaluation", "online eval",
        "a/b testing", "a/b test", "ab testing",
        "interleaving",
        # LTR terms that belong to eval context too
        "learning to rank", "learning-to-rank", "ltr",
        "ranking metrics",
        # Generic but relevant
        "recall", "precision",
    ],

    # =========================================================================
    # SOFT REQUIREMENT GROUPS
    # =========================================================================

    # JD: "learning-to-rank (XGBoost/neural)"
    "learning_to_rank": [
        "xgboost ranker", "xgboost rank",
        "lightgbm ranker", "lightgbm rank", "lgbm ranker",
        "lambdamart", "lambda mart", "lambdarank",
        "ranknet", "rankboost", "ranklib",
        "catboost ranking",
        "listwise", "pairwise", "pointwise",
        "listwise ranking", "pairwise ranking",
        "listnet", "listmle", "approxndcg",
        "neural ranking", "neural ranker",
        "ltr",
    ],

    # JD: "LLM fine-tuning (LoRA/QLoRA/PEFT)"
    "llm_finetune": [
        "lora", "qlora", "peft",
        "rlhf", "dpo", "ppo", "orpo", "rpo",
        "sft", "supervised fine-tuning", "supervised finetuning",
        "instruction tuning",
        "fine-tuning", "finetuning", "fine tuning", "full fine-tune",
        "adapter tuning", "prompt tuning", "prefix tuning",
        "continued pretraining",
        "flan", "alpaca",
    ],

    # LLM production / serving (soft signal; also used to detect
    # "LLM experience = only wrappers" when combined with tutorial signals)
    "llm_prod": [
        "rag",  # duplicated intentionally — also a retrieval_infra term
        "agentic workflows", "tool calling",
        "prompt engineering",
        "llm serving", "llm inference",
        "vllm", "text generation inference", "tgi", "ollama",
        "langgraph", "langchain", "llamaindex", "llama index",
        "guardrails", "evaluation harness",
        "huggingface", "hugging face", "transformers",
        "haystack", "semantic kernel", "autogen", "dspy",
    ],

    # NLP foundations — signals depth pre-LLM
    "nlp_foundations": [
        "nlp", "natural language processing",
        "text classification", "entity extraction",
        "named entity recognition", "ner",
        "semantic similarity",
        "question answering",
        "topic modeling",
        "text ranking",
        "information extraction",
        "coreference resolution", "dependency parsing",
        "word2vec", "glove", "fasttext",
    ],

    # JD: "distributed systems / large-scale inference"
    "distributed_systems": [
        # Batch processing
        "spark", "apache spark", "pyspark",
        "flink", "apache flink",
        "dask",
        # Streaming
        "kafka", "apache kafka", "streaming",
        # Orchestration / scheduling
        "airflow", "celery",
        # Distributed ML training
        "distributed training", "distributed inference",
        "horovod", "deepspeed",
        "multi-gpu", "multi gpu",
        "data parallelism", "model parallelism",
        # Scale descriptors
        "large scale systems", "scalable ml", "high throughput",
        # Infra
        "ray", "kubernetes", "redis",
    ],

    # MLOps / serving
    "ml_ops_infra": [
        "mlflow", "wandb", "weights & biases", "weights and biases",
        "kubeflow", "metaflow",
        "ray serve", "triton", "torchserve",
        "bentoml", "seldon", "kserve",
        "model serving", "model deployment", "production ml",
        "feature store", "feast", "tecton",
        "monitoring", "drift detection", "model evaluation",
        "docker", "kubernetes", "k8s",
    ],

    # Python / core ML stack (hard requirement in JD; tracked separately
    # so feature engineering can weight code quality signals)
    "python_stack": [
        "python",
        "pytorch", "tensorflow", "jax",
        "numpy", "pandas", "scikit-learn", "sklearn",
        "fastapi", "flask", "django",
    ],

    # =========================================================================
    # DOMAIN SIGNAL GROUPS  (positive soft signals)
    # =========================================================================

    # JD: "HR-tech/marketplace experience" (nice to have)
    "hrtech": [
        "recruitment", "recruiting", "talent intelligence",
        "candidate matching", "ats", "applicant tracking",
        "hiring platform", "job matching",
        "recruiter workflow", "talent acquisition",
        "hr tech", "hrtech",
    ],

    "marketplace": [
        "marketplace", "two-sided platform",
        "recommendation engine", "recommendation system",
        "matching engine", "supply demand matching",
        "personalization",
        "e-commerce", "ecommerce",
    ],

    # =========================================================================
    # DISQUALIFIER / FLAG GROUPS  (negative signals — penalise or bury)
    # =========================================================================

    # JD: "only consulting firms … in their entire career"
    "consulting_firms": [
        # Named in JD explicitly
        "tcs", "tata consultancy", "tata consultancy services",
        "infosys", "wipro", "accenture",
        "cognizant", "capgemini",
        # Named in JD implicitly (common Indian IT services)
        "mphasis", "tech mahindra", "techmahindra",
        "hcl", "hcl technologies", "hcltech",
        "lti", "ltimindtree", "lti mindtree", "l&t infotech",
        "hexaware", "birlasoft",
        "mindtree",          # pre-LTIMindtree merger
        "niit technologies", "mastech", "virtusa",
    ],

    # JD: "pure research environments without any production deployment"
    "research_only_signals": [
        "research scientist", "research fellow", "research engineer",
        "phd researcher", "postdoctoral researcher",
        "postdoc", "post-doc", "postdoctoral",
        "academic research", "academic lab", "university lab", "research lab",
        # Conference names alone are NOT disqualifiers; used in combination
        "arxiv", "neurips", "icml", "iclr", "acl", "emnlp",
        # Well-known pure-research orgs
        "deepmind", "google brain", "openai research", "fair", "msr",
    ],

    # JD: "CV/speech/robotics without NLP/IR exposure"
    "cv_speech_robotics": [
        # Computer vision
        "computer vision", "opencv",
        "image segmentation", "object detection",
        "yolo", "resnet", "vgg", "efficientnet",
        "action recognition", "pose estimation",
        # Speech
        "speech recognition", "asr",
        "text to speech", "tts", "whisper",
        # Robotics
        "robotics", "ros", "robot operating system",
        "slam", "lidar", "point cloud",
    ],

    # JD: "AI experience = only LangChain tutorials <12 months"
    "tutorial_framework_signals": [
        "langchain tutorial", "openai tutorial", "chatgpt tutorial",
        "prompt engineering course",
        "udemy", "coursera certificate",
        "kaggle beginner", "kaggle novice",
        "build with chatgpt", "gpt wrapper",
        "evaluation harness",   # often appears only in tutorial-grade work
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

# The 4 groups that map directly to JD hard requirements
HARD_REQ_GROUPS = ["vector_search", "embedding_models", "retrieval_infra", "ranking_eval"]


def get_skill_groups(text: str) -> dict[str, bool]:
    """
    Given any free text (headline, summary, job description, skills list),
    return {group_name: True/False} for every group in SKILL_GROUPS.

    Example:
        get_skill_groups("Built FAISS index, evaluated with NDCG")
        → {"vector_search": True, "ranking_eval": True, ...}
    """
    text_lower = text.lower()
    return {
        group: any(term in text_lower for term in terms)
        for group, terms in SKILL_GROUPS.items()
    }


def get_hard_req_coverage(text: str) -> dict:
    """
    Returns coverage score for the 4 JD hard requirements.
    Score = hits / 4  (0.0 – 1.0).
    """
    hits = get_skill_groups(text)
    covered = [g for g in HARD_REQ_GROUPS if hits.get(g)]
    return {
        "hard_req_coverage": len(covered) / len(HARD_REQ_GROUPS),
        "covered_groups": covered,
        "missing_groups": [g for g in HARD_REQ_GROUPS if g not in covered],
    }


def is_consulting_firm_only(career_history: list[dict]) -> bool:
    """
    Returns True if every role in career_history is at a consulting firm.
    career_history: list of {"company": str, ...}
    """
    if not career_history:
        return False
    terms = SKILL_GROUPS["consulting_firms"]
    return all(
        any(t in role.get("company", "").lower() for t in terms)
        for role in career_history
    )


def get_consulting_ratio(career_history: list[dict]) -> float:
    """
    Returns fraction of total career months spent at consulting firms.
    career_history: list of {"company": str, "duration_months": int}
    """
    if not career_history:
        return 0.0
    terms = SKILL_GROUPS["consulting_firms"]
    consulting_months = sum(
        r.get("duration_months", 0) for r in career_history
        if any(t in r.get("company", "").lower() for t in terms)
    )
    total_months = sum(r.get("duration_months", 0) for r in career_history)
    return consulting_months / max(total_months, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests  (python skill_groups.py  to verify)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    PASS = "\033[92m✓\033[0m"
    FAIL = "\033[91m✗\033[0m"
    errors = 0

    def check(label: str, condition: bool) -> None:
        global errors
        symbol = PASS if condition else FAIL
        print(f"  {symbol}  {label}")
        if not condition:
            errors += 1

    # ── Hard requirement groups ───────────────────────────────────────────────
    print("\n── Hard requirement group lookups ─────────────────────────────────")

    g = get_skill_groups("Built FAISS-based index for similarity search")
    check("FAISS → vector_search",                  g["vector_search"])
    check("FAISS (no embedding terms) → embedding_models = False", not g["embedding_models"])

    g = get_skill_groups("Used Pinecone with OpenAI embeddings and pgvector")
    check("Pinecone → vector_search",               g["vector_search"])
    check("OpenAI embeddings → embedding_models",   g["embedding_models"])
    check("pgvector → vector_search",               g["vector_search"])

    g = get_skill_groups("Solr and Lucene for full-text search at scale")
    check("Solr → vector_search",                   g["vector_search"])
    check("Lucene → vector_search",                 g["vector_search"])

    g = get_skill_groups("Evaluated ranking with NDCG, MRR; ran A/B tests; used interleaving")
    check("NDCG + MRR → ranking_eval",              g["ranking_eval"])
    check("A/B tests → ranking_eval",               g["ranking_eval"])
    check("interleaving → ranking_eval",            g["ranking_eval"])

    g = get_skill_groups("Built RAG pipeline with BM25 sparse + dense hybrid retrieval")
    check("RAG + BM25 → retrieval_infra",           g["retrieval_infra"])

    g = get_skill_groups("Used ColBERT and SimCSE for retrieval")
    check("ColBERT → embedding_models",             g["embedding_models"])
    check("SimCSE → embedding_models",              g["embedding_models"])

    # ── Soft requirement groups ───────────────────────────────────────────────
    print("\n── Soft requirement group lookups ─────────────────────────────────")

    g = get_skill_groups("Fine-tuned LLM using LoRA, QLoRA, and DPO")
    check("LoRA + QLoRA + DPO → llm_finetune",     g["llm_finetune"])

    g = get_skill_groups("PPO-based RLHF alignment training")
    check("PPO + RLHF → llm_finetune",             g["llm_finetune"])

    g = get_skill_groups("LambdaMART and LightGBM ranker for search")
    check("LambdaMART → learning_to_rank",         g["learning_to_rank"])
    check("LightGBM ranker → learning_to_rank",    g["learning_to_rank"])

    g = get_skill_groups("NLP pipeline: NER, text classification, semantic similarity")
    check("NLP + NER → nlp_foundations",           g["nlp_foundations"])

    g = get_skill_groups("Python, PyTorch, FastAPI, NumPy")
    check("Python + PyTorch → python_stack",       g["python_stack"])

    # ── Domain signal groups ──────────────────────────────────────────────────
    print("\n── Domain signal group lookups ─────────────────────────────────────")

    g = get_skill_groups("Worked on ATS integration and candidate matching for hiring platform")
    check("ATS + candidate matching → hrtech",     g["hrtech"])

    g = get_skill_groups("Two-sided marketplace with matching engine and personalization")
    check("Marketplace + matching engine → marketplace", g["marketplace"])

    # ── Consulting firm detection ─────────────────────────────────────────────
    print("\n── Consulting firm detection ───────────────────────────────────────")

    history_consulting = [
        {"company": "Wipro", "duration_months": 36},
        {"company": "Infosys", "duration_months": 24},
    ]
    check("Wipro + Infosys only → consulting_firm_only = True",
          is_consulting_firm_only(history_consulting))

    history_mixed = [
        {"company": "Wipro", "duration_months": 24},
        {"company": "Swiggy", "duration_months": 36},
    ]
    check("Wipro then Swiggy → consulting_firm_only = False",
          not is_consulting_firm_only(history_mixed))

    check("Wipro+Infosys consulting_ratio ≈ 1.0",
          abs(get_consulting_ratio(history_consulting) - 1.0) < 0.01)

    check("Wipro+Swiggy consulting_ratio ≈ 0.40",
          abs(get_consulting_ratio(history_mixed) - 0.40) < 0.01)

    g = get_skill_groups("Birlasoft and HCL consulting projects")
    check("Birlasoft → consulting_firms",          g["consulting_firms"])
    check("HCL → consulting_firms",               g["consulting_firms"])

    # ── Hard requirement coverage ─────────────────────────────────────────────
    print("\n── Hard requirement coverage ───────────────────────────────────────")

    perfect = "Built FAISS vector index, used BGE embeddings, evaluated with NDCG, implemented hybrid BM25+dense RAG"
    result = get_hard_req_coverage(perfect)
    check("All 4 hard reqs → coverage = 1.0", result["hard_req_coverage"] == 1.0)
    check("No missing groups",                 result["missing_groups"] == [])

    weak = "Python developer with Django and REST APIs"
    result = get_hard_req_coverage(weak)
    check("No ML terms → coverage = 0.0",     result["hard_req_coverage"] == 0.0)

    # ── Disqualifier groups ───────────────────────────────────────────────────
    print("\n── Disqualifier group lookups ──────────────────────────────────────")

    g = get_skill_groups("Computer vision expert, YOLO object detection, OpenCV")
    check("YOLO + OpenCV → cv_speech_robotics",    g["cv_speech_robotics"])

    g = get_skill_groups("ASR pipeline, speech recognition, Whisper fine-tuning")
    check("ASR + Whisper → cv_speech_robotics",    g["cv_speech_robotics"])

    g = get_skill_groups("LangChain tutorial, built GPT wrapper, Udemy certificate")
    check("LangChain tutorial → tutorial_framework_signals",
          g["tutorial_framework_signals"])

    g = get_skill_groups("Research scientist at DeepMind, published at NeurIPS")
    check("Research scientist + DeepMind → research_only_signals",
          g["research_only_signals"])

    # ── Negative checks ───────────────────────────────────────────────────────
    print("\n── Negative checks (should NOT fire) ──────────────────────────────")

    g = get_skill_groups("5 years NLP, built search ranking at Flipkart")
    check("Flipkart → consulting_firms = False",   not g["consulting_firms"])

    g = get_skill_groups("Built recommendation system using matrix factorisation")
    check("Matrix factorisation → vector_search = False", not g["vector_search"])

    g = get_skill_groups("Trained BERT for text classification at Zomato")
    check("BERT text classification → cv_speech_robotics = False",
          not g["cv_speech_robotics"])

    # ── Summary ───────────────────────────────────────────────────────────────
    total = 36
    passed = total - errors
    print(f"\n{'─'*55}")
    if errors == 0:
        print(f"  \033[92mAll {total} tests passed.\033[0m")
    else:
        print(f"  \033[91m{errors}/{total} test(s) failed.\033[0m")
        sys.exit(1)
