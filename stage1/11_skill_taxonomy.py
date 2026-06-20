"""
stage1/11_skill_taxonomy.py
Skill taxonomy — maps each JD requirement/disqualifier to a bank of surface terms.

These groups are how Stage 2 turns free-text career descriptions and skill lists into
requirement-coverage features. Group NAMES match the keys in jd_config's hard/soft
requirements and disqualifiers so the two line up exactly.

IMPORTANT (the trap): skill-name presence is gameable. Stage 2 uses these terms against
CAREER DESCRIPTION text (what they built) with more weight than against the SKILLS list
(what they claim). The taxonomy just supplies vocabulary; the weighting lives in Stage 2.

Run:  python stage1/11_skill_taxonomy.py
Output: artifacts/skill_groups.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402


SKILL_GROUPS: dict[str, list[str]] = {
    # ---- HARD REQUIREMENTS ----
    "embeddings_retrieval": [
        "embedding", "embeddings", "sentence-transformers", "sentence transformers",
        "bge", "e5", "openai embeddings", "semantic search", "dense retrieval",
        "bi-encoder", "biencoder", "vector embedding", "text embedding", "retrieval",
        "embedding drift", "index refresh", "retrieval quality", "rag",
        "retrieval augmented", "nearest neighbor", "ann", "knn search",
    ],
    "vector_search_infra": [
        "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
        "faiss", "vector database", "vector db", "vector store", "hybrid search",
        "approximate nearest neighbor", "hnsw", "ivf", "scann", "vespa",
    ],
    "ranking_evaluation": [
        "ndcg", "mrr", "map", "mean average precision", "mean reciprocal rank",
        "precision@k", "recall@k", "a/b test", "ab test", "ab testing", "offline evaluation",
        "online evaluation", "offline-to-online", "ranking metric", "evaluation framework",
        "relevance evaluation", "ranking evaluation", "experimentation", "holdout",
    ],
    "python_production": [
        "python", "pytest", "type hints", "production code", "code review", "ci/cd",
        "software engineering", "clean code", "fastapi", "production python",
    ],

    # ---- SOFT REQUIREMENTS ----
    "llm_finetuning": [
        "fine-tuning", "fine tuning", "finetuning", "lora", "qlora", "peft",
        "instruction tuning", "sft", "rlhf", "dpo", "adapter", "parameter efficient",
    ],
    "learning_to_rank": [
        "learning to rank", "learning-to-rank", "ltr", "lambdamart", "lambdarank",
        "ranknet", "xgboost ranker", "gradient boosted", "gbdt ranking",
        "pairwise ranking", "listwise", "rank svm",
    ],
    "hr_tech_experience": [
        "hr-tech", "hr tech", "hrtech", "recruiting", "recruitment", "talent",
        "applicant tracking", "ats", "candidate matching", "job matching",
        "marketplace", "two-sided marketplace", "hiring platform",
    ],
    "distributed_systems": [
        "distributed systems", "distributed", "kafka", "spark", "ray", "kubernetes",
        "horizontal scaling", "sharding", "large-scale inference", "inference optimization",
        "low latency", "high throughput", "model serving", "triton", "vllm",
    ],
    "open_source": [
        "open source", "open-source", "github", "maintainer", "contributor",
        "pull request", "oss", "published paper", "arxiv", "neurips", "icml", "acl",
        "emnlp", "sigir", "kdd", "conference talk", "kaggle", "tech blog",
    ],
    "hybrid_retrieval": [
        "hybrid retrieval", "hybrid search", "bm25", "lexical search", "sparse retrieval",
        "dense + sparse", "reranking", "re-ranking", "cross-encoder", "cross encoder",
        "reciprocal rank fusion", "rrf", "colbert",
    ],

    # ---- DISQUALIFIER / NEGATIVE GROUPS ----
    "pure_research": [
        "research scientist", "researcher", "postdoc", "post-doctoral", "research fellow",
        "research assistant", "phd candidate", "phd student", "research intern",
        "academic", "thesis", "dissertation", "research lab", "research only",
    ],
    "production_evidence": [
        "production", "deployed", "in production", "shipped", "launched", "rolled out",
        "live system", "real users", "serving", "at scale", "millions of", "daily active",
        "throughput", "latency", "sla", "uptime", "online system", "went live",
    ],
    "langchain_framework": [
        "langchain", "llama-index", "llamaindex", "llama index", "autogen", "crewai",
        "haystack", "semantic kernel", "flowise", "langgraph",
    ],
    "cv_speech_robotics": [
        "computer vision", "image classification", "object detection", "segmentation",
        "opencv", "yolo", "speech recognition", "asr", "tts", "text-to-speech",
        "speech-to-text", "robotics", "ros", "slam", "lidar", "point cloud",
        "gan", "gans", "image generation", "diffusion model", "video analytics",
    ],
    "nlp_ir": [   # used to CHECK whether a CV/speech person ALSO has NLP/IR (rescues them)
        "nlp", "natural language", "information retrieval", "text classification",
        "named entity", "ner", "question answering", "search", "ranking", "retrieval",
        "language model", "transformer", "bert", "text mining",
    ],
    "management_only": [   # for the "no code in 18 months / architecture-tech-lead" flag
        "engineering manager", "tech lead", "technical lead", "team lead", "architect",
        "head of engineering", "vp engineering", "director of engineering", "people manager",
    ],
    "title_chase": [   # informational; Stage 2 measures tenure, not keywords, for this
        "senior", "staff", "principal", "lead",
    ],
}

# Cross-reference: which jd_config keys each group serves (sanity documentation).
GROUP_ROLE = {
    "embeddings_retrieval": "hard_req", "vector_search_infra": "hard_req",
    "ranking_evaluation": "hard_req", "python_production": "hard_req",
    "llm_finetuning": "soft_req", "learning_to_rank": "soft_req",
    "hr_tech_experience": "soft_req", "distributed_systems": "soft_req",
    "open_source": "soft_req", "hybrid_retrieval": "soft_req",
    "pure_research": "disqualifier", "production_evidence": "evidence",
    "langchain_framework": "disqualifier", "cv_speech_robotics": "disqualifier",
    "nlp_ir": "rescue_check", "management_only": "disqualifier",
    "title_chase": "informational",
}


def main() -> int:
    config.ensure_artifacts()
    # term -> group reverse index (lowercased) for fast Stage 2 lookups.
    term_to_group = {}
    for group, terms in SKILL_GROUPS.items():
        for t in terms:
            term_to_group[t.lower()] = group

    payload = {
        "skill_groups": SKILL_GROUPS,
        "group_role": GROUP_ROLE,
        "term_to_group": term_to_group,
        "_note": "Group names match jd_config hard/soft/disqualifier keys. "
                 "Stage 2 weights career-description matches above skill-list matches.",
    }
    config.SKILL_GROUPS_JSON.write_text(json.dumps(payload, indent=2))

    n_terms = sum(len(v) for v in SKILL_GROUPS.values())
    print(f"skill groups: {len(SKILL_GROUPS)}  total terms: {n_terms}")
    for g, terms in SKILL_GROUPS.items():
        print(f"  {GROUP_ROLE[g]:13s} {g:22s} ({len(terms)} terms)")
    print(f"skill_groups -> {config.SKILL_GROUPS_JSON}")
    print("STAGE 1.11 (skill taxonomy): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
