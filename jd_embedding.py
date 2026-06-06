"""
Step 1.3 — JD Embedding  (offline, run once)
Stage 1: JD Intelligence Layer

Generates a high-quality embedding of the JD's semantic core and saves it to
`jd_embedding.npy` for use in Stage 3 (cosine similarity against candidate
embeddings).

Model priority:
  1. BAAI/bge-large-en-v1.5   (primary — highest BEIR scores for retrieval tasks)
  2. intfloat/e5-large-v2      (fallback — equally strong on MTEB)

Both are ~1.3 GB; download once, cached in ~/.cache/huggingface by default.

What is embedded
────────────────
  BLOCK A  — Role-level context (who Redrob is looking for, and why)
  BLOCK B  — Hard requirements  (must-haves; carry highest scoring weight)
  BLOCK C  — Soft requirements  (nice-to-haves; secondary signal)
  BLOCK D  — Disqualifiers      (explicit exclusions the model should "know about")
  BLOCK E  — Ideal candidate narrative (richest semantic signal; repeated for emphasis)
  BLOCK F  — Behavioral / cultural signals

Blocks B and E are concatenated twice — a simple, proven technique to increase
their cosine influence without needing weighted-average pooling here.

Output
──────
  jd_embedding.npy     — float32 array, shape (1, D) where D = 1024 for bge-large
                          / e5-large; ready to np.load() in Stage 3.
  jd_embedding_meta.json — provenance record (model, input_tokens, timestamp, etc.)

Usage
─────
  python jd_embedding.py                        # uses primary model
  python jd_embedding.py --model e5             # forces e5-large-v2
  python jd_embedding.py --out ./stage1/        # custom output directory
  python jd_embedding.py --smoke-test           # also runs similarity sanity checks
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("step1.3")

# ─────────────────────────────────────────────────────────────────────────────
# Model registry
# ─────────────────────────────────────────────────────────────────────────────

MODELS = {
    "bge": {
        "hf_id": "BAAI/bge-large-en-v1.5",
        "prompt_prefix": "",          # BGE uses no query prefix for documents
        "dim": 1024,
        "notes": "Primary choice — top BEIR benchmark; optimised for retrieval",
    },
    "e5": {
        "hf_id": "intfloat/e5-large-v2",
        "prompt_prefix": "passage: ",  # e5 requires passage: / query: prefixes
        "dim": 1024,
        "notes": "Fallback — comparable MTEB score; different vocabulary bias",
    },
}

DEFAULT_MODEL = "bge"

# ─────────────────────────────────────────────────────────────────────────────
# JD text blocks  (derived from jd_parsed.json + raw JD)
# ─────────────────────────────────────────────────────────────────────────────

# ── Block A: Role context ────────────────────────────────────────────────────
BLOCK_A_ROLE_CONTEXT = """
Senior AI Engineer — Founding Team at Redrob AI (Series A).
Own the intelligence layer of Redrob's product: ranking, retrieval, and matching
systems that determine what recruiters see when searching for candidates and what
candidates see when searching for roles. Core focus areas: candidate-JD matching
at scale, ranking and retrieval systems, search relevance, evaluation
infrastructure (offline and online), and recruiter experience optimisation.
Full-time role, 5–9 years experience, preferred locations Noida or Pune.
""".strip()

# ── Block B: Hard requirements (doubled below for emphasis) ──────────────────
BLOCK_B_HARD_REQUIREMENTS = """
Critical hard requirements — must have all four in production:
1. Embeddings-based retrieval systems: must have deployed to real users and managed
   embedding drift, index refresh, and retrieval-quality regression in production.
   Examples: sentence-transformers, OpenAI embeddings, BGE, E5, Cohere Embed.
2. Vector databases and hybrid search infrastructure: operational production experience,
   understanding of tradeoffs, not just API familiarity.
   Examples: Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS, pgvector.
3. Strong Python with code quality discipline — writes production code, not demos.
4. Ranking evaluation frameworks — must have designed and run evaluation frameworks:
   NDCG, MRR, MAP, offline-to-online correlation, A/B test design and interpretation.
""".strip()

# ── Block C: Soft requirements ───────────────────────────────────────────────
BLOCK_C_SOFT_REQUIREMENTS = """
Nice-to-have soft requirements:
- LLM fine-tuning: LoRA, QLoRA, PEFT, DPO, SFT.
- Learning-to-rank models: LambdaMART, XGBoost ranker, neural ranking, pairwise and
  listwise ranking approaches.
- Domain experience in HR-tech, recruiting technology, marketplace products, or
  search and recommendation platforms.
- Distributed systems and large-scale inference optimisation.
- External technical validation: open-source contributions, published papers,
  conference talks, or technical blog posts demonstrating systems depth.
""".strip()

# ── Block D: Disqualifiers ───────────────────────────────────────────────────
BLOCK_D_DISQUALIFIERS = """
Hard disqualifiers — must NOT match these profiles:
- Pure research background without any production deployment to real users.
- AI experience that is primarily recent (under 12 months) LangChain or OpenAI
  wrapper projects, unless substantial pre-LLM applied ML production history exists.
- Candidate who has not written production code in the last 18 months; architecture-
  only or tech-lead-only roles without hands-on coding are disqualified.
Strong negative signals:
- Entire career at consulting or services firms (TCS, Infosys, Wipro, Accenture,
  Cognizant, Capgemini, Mphasis, Tech Mahindra) with no product-company experience.
- Primary expertise in computer vision, speech recognition, or robotics without
  significant NLP or information retrieval exposure.
- Five or more years exclusively on closed-source systems with no external validation.
- Title-chasing job-hopping pattern with average tenure under 1.5 years.
- Framework-enthusiast profile with no systems thinking evidence.
""".strip()

# ── Block E: Ideal candidate narrative (the richest semantic signal) ─────────
BLOCK_E_IDEAL_NARRATIVE = """
Ideal candidate profile:
6–8 years total experience, 4–5 years in applied ML and AI at product companies
(not pure services or consulting). Has shipped at least one end-to-end ranking,
search, or recommendation system to real users at meaningful scale. Holds
defensible opinions on hybrid versus dense retrieval, offline versus online
evaluation, and when to fine-tune versus prompt — all backed by systems they
actually built. Preferred backgrounds: AI-native startups, search and recommendation
platforms, marketplace companies, product-first tech companies. Strong shipper
mindset over researcher mindset. Willing to ship a working ranker in one week even
if the ML approach is not yet optimal. Engages with recruiter workflows and
evaluation frameworks rather than just writing code. Bias for action under
ambiguity. Writes well; async-first team. Plans a 3-plus-year tenure. No title
chasing. Actively seeking roles with recent platform activity.
""".strip()

# ── Block F: Behavioral and cultural signals ─────────────────────────────────
BLOCK_F_BEHAVIORAL = """
Cultural fit signals required: startup-ready, ships fast over perfects,
writes clearly, disagrees openly and decides quickly, no title chasing,
systems thinker not framework collector, product-aware, plans long tenure,
strong bias for action. Async-first team that writes a lot.
""".strip()

# ─────────────────────────────────────────────────────────────────────────────
# Compose the final embedding input text
# ─────────────────────────────────────────────────────────────────────────────

def build_jd_embedding_text(model_key: str) -> str:
    """
    Assemble the JD text to embed.

    Hard requirements (Block B) and the ideal narrative (Block E) are
    included twice to give them extra cosine influence. This is a simple
    and effective alternative to weighted-average pooling of separate embeddings,
    and avoids introducing another hyperparameter into Stage 3.

    For e5 models, every block is prefixed with 'passage: ' as required.
    """
    prefix = MODELS[model_key]["prompt_prefix"]

    blocks = [
        BLOCK_A_ROLE_CONTEXT,
        BLOCK_B_HARD_REQUIREMENTS,        # first pass
        BLOCK_C_SOFT_REQUIREMENTS,
        BLOCK_D_DISQUALIFIERS,
        BLOCK_E_IDEAL_NARRATIVE,          # first pass
        BLOCK_F_BEHAVIORAL,
        # --- second pass for high-weight blocks ---
        BLOCK_B_HARD_REQUIREMENTS,        # repeated
        BLOCK_E_IDEAL_NARRATIVE,          # repeated
    ]

    combined = "\n\n".join(blocks)

    if prefix:
        return prefix + combined
    return combined


# ─────────────────────────────────────────────────────────────────────────────
# Smoke-test texts  (used with --smoke-test flag)
# ─────────────────────────────────────────────────────────────────────────────

SMOKE_TEST_CASES = [
    {
        "label": "Strong fit — should score high (≥ 0.75)",
        "text": (
            "7 years in applied ML at product companies. Built hybrid BM25 + dense retrieval "
            "system at scale using FAISS and BGE embeddings. Ran A/B tests and tracked NDCG "
            "and MRR for ranking quality. Strong Python, shipped to production with real users. "
            "Experience with LambdaMART and LightGBM ranker. Currently at an AI-native startup."
        ),
        "expect": "high",
        "threshold": 0.70,
    },
    {
        "label": "Moderate fit — should score medium (0.45 – 0.75)",
        "text": (
            "5 years NLP experience. Used Elasticsearch and sentence-transformers for search. "
            "Some Python and PyTorch. No explicit mention of ranking metrics or A/B testing. "
            "Product company background."
        ),
        "expect": "medium",
        "threshold": 0.45,
    },
    {
        "label": "Weak fit — should score low (≤ 0.55)",
        "text": (
            "Computer vision engineer with 6 years experience. Object detection using YOLO "
            "and ResNet. OpenCV, PyTorch. No NLP or retrieval work mentioned."
        ),
        "expect": "low",
        "threshold_max": 0.60,
    },
    {
        "label": "Disqualifier — consulting only, should score very low",
        "text": (
            "7 years at TCS and Infosys. Java developer, worked on enterprise applications. "
            "Some Python scripting. No ML production experience."
        ),
        "expect": "very_low",
        "threshold_max": 0.50,
    },
]


def run_smoke_test(model, embedding_text: str, jd_vec: np.ndarray, model_key: str) -> None:
    prefix = MODELS[model_key]["prompt_prefix"]
    # For e5: candidate text uses 'query: ' prefix, not 'passage: '
    # For bge: no prefix needed
    candidate_prefix = "query: " if model_key == "e5" else ""

    log.info("Running smoke-test similarity checks ...")
    all_passed = True

    for case in SMOKE_TEST_CASES:
        cand_text = candidate_prefix + case["text"]
        cand_vec = model.encode([cand_text], normalize_embeddings=True)
        score = float(np.dot(jd_vec[0], cand_vec[0]))

        if case["expect"] == "high":
            passed = score >= case["threshold"]
            status = "✓ PASS" if passed else "✗ FAIL"
            detail = f"score={score:.4f} ≥ {case['threshold']}"
        elif case["expect"] == "medium":
            passed = score >= case["threshold"]
            status = "✓ PASS" if passed else "✗ FAIL"
            detail = f"score={score:.4f} ≥ {case['threshold']}"
        else:  # low / very_low
            passed = score <= case["threshold_max"]
            status = "✓ PASS" if passed else "✗ FAIL"
            detail = f"score={score:.4f} ≤ {case['threshold_max']}"

        if not passed:
            all_passed = False

        log.info("  %s  [%s]  %s", status, detail, case["label"])

    if all_passed:
        log.info("All smoke tests passed.")
    else:
        log.warning("Some smoke tests failed — check model choice or text construction.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step 1.3 — Generate JD embedding (offline, run once)"
    )
    parser.add_argument(
        "--model",
        choices=list(MODELS.keys()),
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--out",
        default=".",
        help="Output directory for jd_embedding.npy and jd_embedding_meta.json",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run cosine similarity sanity checks after embedding",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device for model inference: 'cpu' or 'cuda' (default: cpu)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    npy_path  = out_dir / "jd_embedding.npy"
    meta_path = out_dir / "jd_embedding_meta.json"

    model_cfg = MODELS[args.model]
    log.info("Model   : %s  (%s)", args.model, model_cfg["hf_id"])
    log.info("Notes   : %s", model_cfg["notes"])
    log.info("Device  : %s", args.device)

    # ── 1. Build embedding text ───────────────────────────────────────────────
    jd_text = build_jd_embedding_text(args.model)
    token_approx = len(jd_text.split())
    log.info("JD text : ~%d tokens (word-count approximation)", token_approx)

    # ── 2. Load model ─────────────────────────────────────────────────────────
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        log.error(
            "sentence-transformers is not installed.\n"
            "Run:  pip install sentence-transformers\n"
            "      (add --break-system-packages if using system Python)"
        )
        sys.exit(1)

    log.info("Loading model from HuggingFace (cached after first download) ...")
    t0 = time.perf_counter()
    model = SentenceTransformer(model_cfg["hf_id"], device=args.device)
    log.info("Model loaded in %.1fs", time.perf_counter() - t0)

    # ── 3. Encode ─────────────────────────────────────────────────────────────
    log.info("Encoding JD text ...")
    t0 = time.perf_counter()
    embedding = model.encode(
        [jd_text],
        normalize_embeddings=True,   # L2-normalise so cosine sim = dot product
        show_progress_bar=False,
        batch_size=1,
    )
    elapsed = time.perf_counter() - t0
    log.info("Encoded in %.2fs  |  shape=%s  dtype=%s", elapsed, embedding.shape, embedding.dtype)

    assert embedding.shape == (1, model_cfg["dim"]), (
        f"Expected shape (1, {model_cfg['dim']}), got {embedding.shape}"
    )
    assert abs(np.linalg.norm(embedding[0]) - 1.0) < 1e-5, "Embedding is not unit-normalised"

    # ── 4. Save .npy ─────────────────────────────────────────────────────────
    np.save(str(npy_path), embedding.astype(np.float32))
    log.info("Saved  : %s", npy_path.resolve())

    # ── 5. Save metadata ──────────────────────────────────────────────────────
    meta = {
        "step": "1.3",
        "stage": "JD Intelligence Layer",
        "model_key": args.model,
        "model_hf_id": model_cfg["hf_id"],
        "embedding_dim": model_cfg["dim"],
        "shape": list(embedding.shape),
        "dtype": "float32",
        "normalised": True,
        "device": args.device,
        "approx_input_tokens": token_approx,
        "blocks_included": [
            "A_role_context",
            "B_hard_requirements (x2)",
            "C_soft_requirements",
            "D_disqualifiers",
            "E_ideal_narrative (x2)",
            "F_behavioral_cultural",
        ],
        "design_note": (
            "Hard requirements (Block B) and ideal narrative (Block E) are included "
            "twice in the input text to amplify their cosine influence without "
            "requiring weighted-average pooling in Stage 3."
        ),
        "output_file": str(npy_path.resolve()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "encode_seconds": round(elapsed, 3),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    log.info("Metadata: %s", meta_path.resolve())

    # ── 6. Smoke test ─────────────────────────────────────────────────────────
    if args.smoke_test:
        run_smoke_test(model, jd_text, embedding, args.model)

    log.info("Step 1.3 complete.  jd_embedding.npy ready for Stage 3.")


if __name__ == "__main__":
    main()
