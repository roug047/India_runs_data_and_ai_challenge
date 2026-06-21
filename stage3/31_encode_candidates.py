"""
stage3/31_encode_candidates.py
Encode all candidate texts with bge-large on GPU. The heaviest compute step in the project.

CRITICAL (asymmetric bge): candidates are PASSAGES and get NO query prefix. The JD/ideal
(Stage 1) were QUERIES and got the prefix. We read embedding_meta.json to use the SAME model
and confirm the passage prefix is empty. Getting this wrong silently degrades all similarities.

Sets HF_HUB_OFFLINE=1 so the run doesn't stall on Hugging Face metadata pings (the model is
already cached from Stage 1). GPU strongly recommended — on the RTX 4050 (6GB) this is a few
minutes; on CPU it's ~1-2 hours.

Run:  python stage3/31_encode_candidates.py
      python stage3/31_encode_candidates.py --sample --device cpu
Output: artifacts/candidate_embeddings.npy  (float32, N x 1024, L2-normalized),
        artifacts/candidate_embeddings_ids.json  (row order)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

# Skip HF metadata round-trips — model is cached from Stage 1.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--device", default=None, help="cuda / cpu (auto if unset)")
    ap.add_argument("--batch-size", type=int, default=64)
    args = ap.parse_args()
    config.ensure_artifacts()

    text_file = config.CANDIDATE_TEXT_JSONL if not args.sample else \
        config.CANDIDATE_TEXT_JSONL.with_name("candidate_texts_sample.jsonl")
    if not text_file.exists():
        print(f"FATAL: {text_file.name} missing — run stage3/30_candidate_text.py first.")
        return 1

    # model + passage prefix from Stage 1 (consistency guard)
    meta_path = config.ARTIFACTS / "embedding_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        model_name = meta["model"]
        passage_prefix = meta.get("passage_prefix", "")   # MUST be "" for bge passages
    else:
        model_name = "BAAI/bge-large-en-v1.5"
        passage_prefix = ""
        print("WARNING: embedding_meta.json missing; using bge-large defaults.")
    assert passage_prefix == "", "bge passages must have NO prefix (asymmetric)."

    ids, texts = [], []
    with open(text_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                ids.append(obj["candidate_id"])
                texts.append(obj["text"])
    print(f"loaded {len(texts)} candidate texts")

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        print("FATAL: pip install sentence-transformers numpy")
        return 1

    device = args.device
    if device is None:
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
    print(f"Encoding {len(texts)} passages with {model_name} on {device} "
          f"(batch={args.batch_size})")

    model = SentenceTransformer(model_name, device=device)
    # passages get NO prefix; normalize for cosine via dot product later
    emb = model.encode(
        texts,
        batch_size=args.batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype("float32")

    out_emb = config.CANDIDATE_EMBEDDINGS_NPY if not args.sample else \
        config.CANDIDATE_EMBEDDINGS_NPY.with_name("candidate_embeddings_sample.npy")
    out_ids = config.CANDIDATE_EMB_IDS_JSON if not args.sample else \
        config.CANDIDATE_EMB_IDS_JSON.with_name("candidate_embeddings_ids_sample.json")
    np.save(out_emb, emb)
    out_ids.write_text(json.dumps(ids))

    print(f"embeddings -> {out_emb}  shape={emb.shape}")
    print(f"ids        -> {out_ids}")
    print("STAGE 3.31 (encode candidates): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
