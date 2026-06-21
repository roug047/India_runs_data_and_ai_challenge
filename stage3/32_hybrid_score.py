"""
stage3/32_hybrid_score.py
Compute BM25 over the JD query, combine with dense similarity into hybrid_score,
and write hybrid_score + components back into features_100k.parquet.

WHY HYBRID: dense embeddings catch the "quiet shipper" who built a recsys but never writes
'RAG'. BM25 catches exact rare terms (Milvus, NDCG, LambdaMART) that dense vectors smooth
over. Neither alone is enough; the JD wants both the semantic fit AND the specific-tech signal.

Score = 0.60 * dense + 0.40 * bm25_normalized
  dense = 0.6 * sim(candidate, JD) + 0.4 * sim(candidate, ideal_summary)
The ideal-summary term sharpens toward the "strong fit" profile, not just JD keywords.

No GPU. Reads the dense embeddings from Stage 3.31.

Run:  python stage3/32_hybrid_score.py
      python stage3/32_hybrid_score.py --sample
Output: updates features parquet with hybrid_score, dense_score, bm25_score;
        artifacts/bm25_scores.npy; artifacts/stage3_hybrid_report.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402

_TOKEN = re.compile(r"[a-z0-9@+#./-]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _minmax(a):
    import numpy as np
    a = np.asarray(a, dtype="float64")
    rng = a.max() - a.min()
    return (a - a.min()) / rng if rng > 1e-12 else np.zeros_like(a)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--w-dense", type=float, default=0.60)
    ap.add_argument("--w-bm25", type=float, default=0.40)
    args = ap.parse_args()
    config.ensure_artifacts()

    try:
        import numpy as np
        import pandas as pd
        from rank_bm25 import BM25Okapi
    except ImportError:
        print("FATAL: pip install numpy pandas rank_bm25 pyarrow")
        return 1

    sfx = "_sample" if args.sample else ""
    text_file = config.CANDIDATE_TEXT_JSONL.with_name(f"candidate_texts{sfx}.jsonl") \
        if args.sample else config.CANDIDATE_TEXT_JSONL
    emb_file = config.CANDIDATE_EMBEDDINGS_NPY.with_name(f"candidate_embeddings{sfx}.npy") \
        if args.sample else config.CANDIDATE_EMBEDDINGS_NPY
    ids_file = config.CANDIDATE_EMB_IDS_JSON.with_name(f"candidate_embeddings_ids{sfx}.json") \
        if args.sample else config.CANDIDATE_EMB_IDS_JSON
    feat_file = config.FEATURES_PARQUET.with_name("features_sample.parquet") \
        if args.sample else config.FEATURES_PARQUET

    for need in (text_file, emb_file, ids_file):
        if not Path(need).exists():
            print(f"FATAL: {need.name} missing — run stage3 30 & 31 first.")
            return 1

    # --- load candidate texts (BM25 corpus) in the SAME order as embeddings ---
    ids = json.loads(Path(ids_file).read_text())
    text_by_id = {}
    with open(text_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                o = json.loads(line)
                text_by_id[o["candidate_id"]] = o["text"]
    corpus = [tokenize(text_by_id[i]) for i in ids]

    # --- BM25 over the JD query (+ ideal summary terms) ---
    jd_text = config.JD_TEXT_CACHE.read_text(encoding="utf-8") \
        if config.JD_TEXT_CACHE.exists() else ""
    jd_cfg = json.loads(config.JD_CONFIG_JSON.read_text())
    query = tokenize(jd_text + " " + jd_cfg.get("ideal_profile_summary", ""))
    bm25 = BM25Okapi(corpus)
    bm25_raw = bm25.get_scores(query)
    bm25_norm = _minmax(bm25_raw)
    np.save(config.BM25_SCORES_NPY.with_name(f"bm25_scores{sfx}.npy")
            if args.sample else config.BM25_SCORES_NPY, bm25_raw.astype("float32"))

    # --- dense similarity (cosine = dot, vectors are normalized) ---
    emb = np.load(emb_file)                       # N x 1024
    jd_vec = np.load(config.JD_EMBEDDING_NPY)     # 1024
    ideal_vec = np.load(config.IDEAL_EMBEDDING_NPY)
    sim_jd = emb @ jd_vec
    sim_ideal = emb @ ideal_vec
    dense = 0.6 * sim_jd + 0.4 * sim_ideal
    dense_norm = _minmax(dense)

    hybrid = args.w_dense * dense_norm + args.w_bm25 * bm25_norm

    # --- write back into features parquet ---
    df = pd.read_parquet(feat_file)
    score_df = pd.DataFrame({
        "candidate_id": ids,
        "dense_score": dense_norm.astype("float32"),
        "dense_sim_jd": sim_jd.astype("float32"),
        "dense_sim_ideal": sim_ideal.astype("float32"),
        "bm25_score": bm25_norm.astype("float32"),
        "hybrid_score": hybrid.astype("float32"),
    }).set_index("candidate_id")

    df = df.join(score_df, how="left")
    # any candidate missing an embedding (shouldn't happen) → hybrid falls back to dense=0
    df[["dense_score", "bm25_score", "hybrid_score"]] = \
        df[["dense_score", "bm25_score", "hybrid_score"]].fillna(0.0)
    df.to_parquet(feat_file)

    # --- report: do the planted strong fits rise? ---
    top = df.sort_values("hybrid_score", ascending=False).head(10)
    report = {
        "n": int(len(df)),
        "hybrid_mean": round(float(df["hybrid_score"].mean()), 4),
        "dense_bm25_corr": round(float(np.corrcoef(dense_norm, bm25_norm)[0, 1]), 3),
        "top10_ids": top.index.tolist(),
        "top10_hard_req_coverage": [round(float(x), 3)
                                    for x in top["weighted_hard_req_coverage"]],
    }
    rep_file = config.HYBRID_REPORT_JSON.with_name(f"stage3_hybrid_report{sfx}.json") \
        if args.sample else config.HYBRID_REPORT_JSON
    rep_file.write_text(json.dumps(report, indent=2))

    print(f"hybrid written into {feat_file.name}")
    print(f"dense/bm25 correlation: {report['dense_bm25_corr']} "
          f"(low = they capture different signal, good)")
    print(f"top-10 by hybrid: {report['top10_ids'][:5]}...")
    print(f"top-10 hard-req coverage: {report['top10_hard_req_coverage']}")
    print("STAGE 3.32 (hybrid score): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
