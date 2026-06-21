# Stage 3 — Hybrid Retrieval

Adds the semantic backbone: encodes every candidate with bge-large, scores BM25 over the JD
query, and writes a combined `hybrid_score` into `features_100k.parquet`. This is what catches
the "quiet shipper" — a candidate who built a recsys but never writes the buzzword "RAG".

GPU used in step 31 (your CUDA setup pays off here). Steps 30 and 32 are CPU.

## Files

| File | Does | GPU? |
|------|------|------|
| `30_candidate_text.py` | Synthesizes one retrieval text per candidate, **current role first and doubled** so it survives bge's 512-token truncation | no |
| `31_encode_candidates.py` | Encodes all texts with bge-large, **no query prefix** (passages are asymmetric), saves N×1024 matrix | **yes** |
| `32_hybrid_score.py` | BM25 over JD query + dense similarity → `hybrid_score`, written back into the feature table | no |

## Run (in order)

```bash
python stage3/30_candidate_text.py            # ~1 min, writes candidate_texts.jsonl
python stage3/31_encode_candidates.py         # GPU: few min on RTX 4050; CPU: ~1-2 hr
python stage3/32_hybrid_score.py              # ~1-2 min, updates features parquet
```

Dependencies: `pip install rank_bm25` (the others you already have).

## Scoring

```
hybrid_score = 0.60 * dense_norm + 0.40 * bm25_norm
dense        = 0.6 * cos(candidate, JD) + 0.4 * cos(candidate, ideal_summary)
```

- **Dense** catches semantic fit (built-a-recsys without keywords).
- **BM25** catches exact rare tech (Milvus, NDCG, LambdaMART) dense vectors smooth over.
- The **ideal-summary** term sharpens toward the "strong fit" profile, not just JD keywords.

## Why hybrid_score is an INPUT, not the ranking

Validated on the sample: BM25 alone ranks the real fit (Recommendation Systems Engineer at
Swiggy) #1 — but also ranks the keyword-stuffer CAND_0000001 at #3, because its text contains
JD lexical terms. That's expected and fine: `hybrid_score` is one feature. Stage 2's
disqualifier penalty (0.15 on that candidate) and coverage features, combined in Stage 5,
pull the stuffer back down. No single signal is trusted alone.

## Truncation handling

~32% of candidate texts exceed bge's ~512-token window. Step 30 puts the current role first
and repeats it, so the most recent and relevant work always lands inside the window. Skills go
last (lowest priority) — intentional, so gameable skill keywords don't dominate the vector.

## Consistency guard

Step 31 reads `embedding_meta.json` (from Stage 1) to use the SAME model and asserts the
passage prefix is empty. This keeps the query/passage asymmetry correct end to end.

## Consumed downstream

- `hybrid_score`, `dense_score`, `bm25_score` columns → Stage 4 (honeypot uses them),
  Stage 5 (composite), Stage 6 (ranker feature).
- `candidate_embeddings.npy` → Stage 7 `rank.py` recomputes hybrid at inference.
