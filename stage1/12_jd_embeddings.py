"""
stage1/12_jd_embeddings.py
Encode the JD and the ideal-candidate summary into bge-large vectors.

CRITICAL (v6.1 retrieval-correctness): bge-large is ASYMMETRIC. The QUERY side gets the
instruction prefix; the PASSAGE side (candidates, in Stage 3) gets NO prefix. The JD and
the ideal summary are QUERIES, so they get the prefix here. Stage 3 must encode candidates
WITHOUT it. Getting this backwards silently degrades every similarity score.

GPU is fine here (precompute). Model: BAAI/bge-large-en-v1.5 (1024-dim, normalized).

Run:  python stage1/12_jd_embeddings.py
      python stage1/12_jd_embeddings.py --model BAAI/bge-base-en-v1.5   # smaller/faster
Output: artifacts/jd_embedding.npy, artifacts/ideal_embedding.npy
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402

# The bge query-side instruction. MUST match what Stage 3 uses for the query side,
# and MUST NOT be prepended to candidate passages.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="BAAI/bge-large-en-v1.5")
    ap.add_argument("--device", default=None, help="cuda / cpu / mps (auto if unset)")
    args = ap.parse_args()
    config.ensure_artifacts()

    if not config.JD_CONFIG_JSON.exists():
        print("FATAL: run stage1/10_parse_jd.py first (need jd_config.json).")
        return 1
    cfg = json.loads(config.JD_CONFIG_JSON.read_text())

    # JD query text = the extracted JD plus the ideal summary's intent. We embed two things:
    #   1. the full JD text (broad signal)
    #   2. the ideal_profile_summary (sharp, what a 'strong fit' looks like)
    jd_text = config.JD_TEXT_CACHE.read_text(encoding="utf-8") \
        if config.JD_TEXT_CACHE.exists() else cfg.get("ideal_profile_summary", "")
    ideal_text = cfg["ideal_profile_summary"]

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("FATAL: sentence-transformers not installed.")
        print("  pip install sentence-transformers")
        print("  (Stage 1.10 and 1.11 don't need it; only this embedding step does.)")
        return 1

    import numpy as np

    device = args.device
    if device is None:
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
    print(f"Encoding with {args.model} on {device}")

    model = SentenceTransformer(args.model, device=device)

    jd_vec = model.encode(BGE_QUERY_PREFIX + jd_text, normalize_embeddings=True)
    ideal_vec = model.encode(BGE_QUERY_PREFIX + ideal_text, normalize_embeddings=True)

    np.save(config.JD_EMBEDDING_NPY, jd_vec.astype("float32"))
    np.save(config.IDEAL_EMBEDDING_NPY, ideal_vec.astype("float32"))

    # Record the model + prefix so Stage 3 uses the SAME ones (consistency guard).
    (config.ARTIFACTS / "embedding_meta.json").write_text(json.dumps({
        "model": args.model,
        "dim": int(jd_vec.shape[0]),
        "query_prefix": BGE_QUERY_PREFIX,
        "passage_prefix": "",   # candidates get NO prefix in Stage 3
        "normalized": True,
    }, indent=2))

    print(f"jd_embedding    -> {config.JD_EMBEDDING_NPY}  dim={jd_vec.shape[0]}")
    print(f"ideal_embedding -> {config.IDEAL_EMBEDDING_NPY}  dim={ideal_vec.shape[0]}")
    print("NOTE: Stage 3 must encode candidates WITHOUT the query prefix (asymmetric bge).")
    print("STAGE 1.12 (jd embeddings): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
