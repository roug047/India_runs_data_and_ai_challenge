SKILL_GROUPS = {

    # =========================
    # Retrieval / Search
    # =========================
    "vector_search": [
        "pinecone", "weaviate", "qdrant", "milvus",
        "faiss", "opensearch", "elasticsearch",
        "pgvector", "chromadb", "annoy",
        "vespa", "solr", "lucene"
    ],

    "retrieval_systems": [
        "dense retrieval",
        "sparse retrieval",
        "hybrid retrieval",
        "semantic search",
        "candidate retrieval",
        "document retrieval",
        "retrieval pipeline",
        "information retrieval",
        "search relevance",
        "vector retrieval",
        "nearest neighbor search",
        "approximate nearest neighbor",
        "ann search"
    ],

    "embedding_models": [
        "sentence-transformers",
        "openai embeddings",
        "bge",
        "e5",
        "gte",
        "instructor",
        "ada",
        "text-embedding",
        "clip",
        "simcse",
        "contriever"
    ],

    # =========================
    # Ranking / Recommendation
    # =========================
    "ranking_systems": [
        "ranking",
        "reranking",
        "learning to rank",
        "search ranking",
        "candidate ranking",
        "recommendation engine",
        "recommendation system",
        "personalization",
        "relevance ranking",
        "search relevance"
    ],

    "ranking_eval": [
        "ndcg",
        "mrr",
        "map",
        "precision@k",
        "recall@k",
        "hit rate",
        "auc",
        "offline evaluation",
        "online evaluation",
        "a/b testing",
        "interleaving",
        "ranking metrics"
    ],

    "learning_to_rank": [
        "xgboost ranker",
        "lightgbm ranker",
        "lambdamart",
        "ranknet",
        "listwise",
        "pairwise",
        "pointwise",
        "ltr"
    ],

    # =========================
    # LLM Engineering
    # =========================
    "llm_finetune": [
        "lora",
        "qlora",
        "peft",
        "sft",
        "instruction tuning",
        "rlhf",
        "dpo",
        "ppo",
        "alpaca",
        "flan",
        "finetuning"
    ],

    "llm_prod": [
        "rag",
        "agentic workflows",
        "tool calling",
        "prompt engineering",
        "llm serving",
        "vllm",
        "tgi",
        "langgraph",
        "guardrails",
        "evaluation harness"
    ],

    # =========================
    # Product Search Infra
    # =========================
    "product_infra": [
        "bm25",
        "hybrid retrieval",
        "reranking",
        "cross encoder",
        "bi encoder",
        "candidate generation",
        "retrieval augmented generation",
        "dense retrieval",
        "semantic ranking",
        "query understanding"
    ],

    # =========================
    # NLP Foundations
    # =========================
    "nlp": [
        "nlp",
        "information retrieval",
        "text classification",
        "entity extraction",
        "named entity recognition",
        "semantic similarity",
        "question answering",
        "topic modeling",
        "text ranking"
    ],

    # =========================
    # Distributed / Scale
    # =========================
    "distributed_systems": [
        "spark",
        "ray",
        "distributed inference",
        "distributed training",
        "kubernetes",
        "airflow",
        "streaming",
        "large scale systems",
        "scalable ml",
        "high throughput"
    ],

    # =========================
    # MLOps
    # =========================
    "mlops": [
        "mlflow",
        "kubeflow",
        "model serving",
        "feature store",
        "monitoring",
        "drift detection",
        "model deployment",
        "model evaluation",
        "production ml"
    ],

    # =========================
    # Languages
    # =========================
    "python": [
        "python",
        "pytorch",
        "numpy",
        "pandas",
        "scikit-learn",
        "fastapi",
        "django"
    ],

    # =========================
    # Domain Signals
    # =========================
    "hrtech": [
        "recruitment",
        "talent intelligence",
        "candidate matching",
        "ats",
        "hiring platform",
        "job matching",
        "recruiter workflow"
    ],

    "marketplace": [
        "marketplace",
        "two-sided platform",
        "recommendation engine",
        "matching engine",
        "supply demand matching"
    ],

    # =========================
    # Negative Signals
    # =========================
    "consulting_firms": [
        "tcs",
        "infosys",
        "wipro",
        "accenture",
        "cognizant",
        "capgemini",
        "mphasis",
        "tech mahindra",
        "hcl",
        "lti",
        "ltimindtree",
        "birlasoft"
    ],

    "research_only": [
        "research scientist",
        "research fellow",
        "phd researcher",
        "postdoctoral researcher",
        "academic research"
    ],

    "cv_specialization": [
        "object detection",
        "image segmentation",
        "computer vision",
        "slam",
        "robotics",
        "speech recognition"
    ]
}