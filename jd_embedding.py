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
  BLOCK B  — Hard requirements  (must-haves; carry highest scoring weight)  [x3]
  BLOCK C  — Soft requirements  (nice-to-haves; secondary signal)
  BLOCK E  — Ideal candidate narrative (richest semantic signal)             [x3]
  BLOCK F  — Behavioral / cultural signals

NOTE: Disqualifiers are intentionally NOT embedded. Including terms like
"YOLO", "TCS", "computer vision" in the JD vector pulls it semantically
toward those concepts, causing false-positive similarity for the very
profiles we want to penalise. Disqualifier enforcement belongs in
skill_groups.py (Step 1.2) and the hard-gate logic of Stage 4/5.

Blocks B and E are concatenated three times — amplifies their cosine
influence; validated against realistic bi-encoder score distributions.

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

# ── Block B: Hard requirements (tripled below for emphasis) ──────────────────
BLOCK_B_HARD_REQUIREMENTS = """
Critical production requirements — all four are mandatory:
1. Embeddings-based retrieval systems shipped to real users at scale: managed embedding
   drift, index refresh cycles, retrieval-quality regression in live production.
   Hands-on with sentence-transformers, BGE, E5, OpenAI text-embedding, Cohere Embed,
   bi-encoder architectures, dense passage retrieval, two-tower models.
2. Vector database and hybrid search infrastructure in production: deep operational
   knowledge of tradeoffs between approximate nearest neighbour approaches.
   Direct experience with FAISS, Pinecone, Weaviate, Qdrant, Milvus, OpenSearch,
   Elasticsearch, pgvector — not just API calls but index tuning, latency management,
   recall-precision tradeoffs, and hybrid BM25 plus dense retrieval pipelines.
3. Production Python engineering with code quality discipline: clean, tested, reviewed
   code deployed to real systems — not prototypes or Jupyter notebooks.
4. Designed and operated ranking evaluation frameworks in production: NDCG@10, NDCG@50,
   MRR, MAP, precision@k, offline-to-online correlation, A/B test design, experiment
   analysis, and recruiter-feedback loops. Built the infra, ran the experiments,
   interpreted the results, acted on them.
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

# ── Block E: Ideal candidate narrative (the richest semantic signal) ─────────
BLOCK_E_IDEAL_NARRATIVE = """
Ideal candidate: 6–8 years total, 4–5 years applied ML and AI engineering at product
companies — AI-native startups, search platforms, recommendation systems, marketplace
tech companies. Has shipped at least one complete end-to-end ranking, search, or
recommendation system to real users at meaningful production scale. Deeply familiar
with information retrieval, semantic search, candidate-job matching, hybrid retrieval
architectures combining sparse BM25 and dense vector search. Built and operated
embedding pipelines, vector indexes, and reranking stages in production. Designed
offline evaluation benchmarks, ran online A/B experiments, measured NDCG and MRR,
and iterated on ranking quality based on recruiter and user engagement signals.
Holds strong opinions on hybrid versus pure dense retrieval, when fine-tuning beats
prompting, and how to build evaluation infra that actually correlates with business
outcomes. Actively writes production code in Python. Has worked in talent-tech,
job marketplace, or candidate-matching domains, or in equivalent high-signal matching
and personalisation products at scale. Ships working systems quickly even when ML
approach is not yet perfectly optimised. Writes well, communicates clearly, thinks
in systems and tradeoffs rather than frameworks and tutorials. Plans multi-year tenure.
Actively seeking a new role with recent job search activity.
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

    Block D (disqualifiers) is deliberately excluded: embedding terms like
    "YOLO", "TCS", "computer vision" would pull the JD vector toward those
    concepts, inflating similarity scores for exactly the profiles we want
    to penalise. Disqualifier enforcement is handled by skill_groups.py
    (Step 1.2) and the hard-gate logic in Stages 4/5.

    Blocks B (hard requirements) and E (ideal narrative) are repeated three
    times to amplify their cosine weight — validated against real score
    distributions from bge-large-en-v1.5.

    For e5 models, the full text is prefixed with 'passage: ' as required.
    """
    prefix = MODELS[model_key]["prompt_prefix"]

    blocks = [
        BLOCK_A_ROLE_CONTEXT,
        BLOCK_B_HARD_REQUIREMENTS,        # pass 1
        BLOCK_C_SOFT_REQUIREMENTS,
        BLOCK_E_IDEAL_NARRATIVE,          # pass 1
        BLOCK_F_BEHAVIORAL,
        BLOCK_B_HARD_REQUIREMENTS,        # pass 2
        BLOCK_E_IDEAL_NARRATIVE,          # pass 2
        BLOCK_B_HARD_REQUIREMENTS,        # pass 3
        BLOCK_E_IDEAL_NARRATIVE,          # pass 3
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
        "id": "strong_fit",
        "label": "Strong fit — ideal profile match",
        "text": (
            "7 years applied ML at product companies. Built hybrid BM25 + dense retrieval "
            "pipeline at production scale using FAISS and BGE embeddings. Designed and ran "
            "A/B experiments, tracked NDCG@10 and MRR for ranking quality, built offline "
            "evaluation benchmarks. Strong Python, shipped to real users. LambdaMART and "
            "LightGBM ranker experience. Currently at an AI-native search startup. "
            "Information retrieval, semantic search, candidate matching, reranking pipelines."
        ),
        "expect": "high",
    },
    {
        "id": "moderate_fit",
        "label": "Moderate fit — some retrieval, missing eval depth",
        "text": (
            "5 years NLP at a product company. Used Elasticsearch and sentence-transformers "
            "for semantic search. Python and PyTorch. No explicit mention of ranking metrics, "
            "A/B testing, or evaluation frameworks. Built text classification and NER systems."
        ),
        "expect": "medium",
    },
    {
        "id": "weak_fit",
        "label": "Weak fit — CV engineer, no NLP/IR overlap",
        "text": (
            "6 years in image recognition and object detection. Trained deep learning models "
            "for visual tasks. Strong PyTorch skills. Worked on segmentation and classification "
            "pipelines. No search, retrieval, ranking, or NLP work in career history."
        ),
        "expect": "low",
    },
    {
        "id": "disqualifier",
        "label": "Disqualifier — consulting-only career, no ML production",
        "text": (
            "8 years at large IT services firms. Java and .NET enterprise application "
            "development. Some Python scripting for automation. No machine learning, "
            "no search systems, no retrieval or ranking work. Client-facing delivery roles."
        ),
        "expect": "very_low",
    },
]

# Delta thresholds: what matters most is *separation* between tiers.
# Absolute scores are model/domain dependent; these deltas are robust.
DELTA_CHECKS = [
    # (higher_id, lower_id, min_delta, label)
    ("strong_fit",   "weak_fit",      0.04, "strong_fit > weak_fit by ≥ 0.04"),
    ("strong_fit",   "disqualifier",  0.06, "strong_fit > disqualifier by ≥ 0.06"),
    ("moderate_fit", "weak_fit",      0.01, "moderate_fit > weak_fit by ≥ 0.01"),
    ("moderate_fit", "disqualifier",  0.03, "moderate_fit > disqualifier by ≥ 0.03"),
]

# Absolute floor/ceiling checks (loose — only catch gross mis-calibration)
ABSOLUTE_CHECKS = [
    # (id, check_type, threshold, label)
    ("strong_fit",   "min", 0.68, "strong_fit score ≥ 0.68"),
    ("moderate_fit", "min", 0.60, "moderate_fit score ≥ 0.60"),
    ("weak_fit",     "max", 0.76, "weak_fit score ≤ 0.76"),
    ("disqualifier", "max", 0.74, "disqualifier score ≤ 0.74"),
]


def run_smoke_test(model, embedding_text: str, jd_vec: np.ndarray, model_key: str) -> None:
    # For e5: candidate texts use 'query: ' prefix (asymmetric passage/query)
    # For bge: no prefix needed for either side
    candidate_prefix = "query: " if model_key == "e5" else ""

    log.info("Running smoke-test similarity checks ...")

    # ── Score all cases ───────────────────────────────────────────────────────
    scores: dict[str, float] = {}
    for case in SMOKE_TEST_CASES:
        cand_text = candidate_prefix + case["text"]
        cand_vec = model.encode([cand_text], normalize_embeddings=True, show_progress_bar=False)
        scores[case["id"]] = float(np.dot(jd_vec[0], cand_vec[0]))
        log.info("  score=%.4f  [%s]  %s", scores[case["id"]], case["expect"], case["label"])

    log.info("")
    log.info("── Delta checks (separation between tiers) ─────────────────────────")
    delta_failures = 0
    for (hi_id, lo_id, min_delta, label) in DELTA_CHECKS:
        delta = scores[hi_id] - scores[lo_id]
        passed = delta >= min_delta
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            delta_failures += 1
        log.info("  %s  [Δ=%.4f, need ≥%.2f]  %s", status, delta, min_delta, label)

    log.info("")
    log.info("── Absolute floor/ceiling checks (gross mis-calibration guard) ─────")
    abs_failures = 0
    for (cid, check_type, threshold, label) in ABSOLUTE_CHECKS:
        if check_type == "min":
            passed = scores[cid] >= threshold
            detail = f"score={scores[cid]:.4f} ≥ {threshold}"
        else:
            passed = scores[cid] <= threshold
            detail = f"score={scores[cid]:.4f} ≤ {threshold}"
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            abs_failures += 1
        log.info("  %s  [%s]  %s", status, detail, label)

    log.info("")
    total_failures = delta_failures + abs_failures
    if total_failures == 0:
        log.info("All smoke tests passed.")
    else:
        if delta_failures > 0:
            log.warning(
                "%d delta check(s) failed — tiers are not separating correctly. "
                "Try: (1) strengthen Block B/E vocabulary, (2) increase repetition count, "
                "(3) switch to --model e5 for comparison.", delta_failures
            )
        if abs_failures > 0:
            log.warning(
                "%d absolute check(s) failed — score range is mis-calibrated. "
                "Delta checks are more reliable; absolute failures alone may be acceptable "
                "if all delta checks pass.", abs_failures
            )


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
            "B_hard_requirements (x3)",
            "C_soft_requirements",
            "E_ideal_narrative (x3)",
            "F_behavioral_cultural",
        ],
        "design_note": (
            "Block D (disqualifiers) is intentionally excluded from the embedding: "
            "including terms like 'YOLO', 'TCS', 'computer vision' would pull the JD "
            "vector toward disqualified profiles, inflating their cosine similarity. "
            "Disqualifier enforcement is handled by skill_groups.py and Stage 4/5 gates. "
            "Blocks B and E are repeated 3x to amplify their cosine weight."
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
