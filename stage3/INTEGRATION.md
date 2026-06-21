# Stage 3 — Integration Instructions

Adds hybrid retrieval. GPU only in step 31 — your CUDA setup handles it.

## 1. Add files to `stage3/`

- `stage3/__init__.py`
- `stage3/30_candidate_text.py`
- `stage3/31_encode_candidates.py`
- `stage3/32_hybrid_score.py`
- `stage3/README.md`

## 2. Add to `common/config.py` (at end)

```python
# Stage 3 outputs
CANDIDATE_TEXT_JSONL = ARTIFACTS / "candidate_texts.jsonl"
CANDIDATE_EMBEDDINGS_NPY = ARTIFACTS / "candidate_embeddings.npy"
CANDIDATE_EMB_IDS_JSON = ARTIFACTS / "candidate_embeddings_ids.json"
BM25_SCORES_NPY = ARTIFACTS / "bm25_scores.npy"
HYBRID_REPORT_JSON = ARTIFACTS / "stage3_hybrid_report.json"
```

## 3. Install the one new dependency

```bash
pip install rank_bm25
```

## 4. Run in order

```bash
python stage3/30_candidate_text.py
python stage3/31_encode_candidates.py
python stage3/32_hybrid_score.py
```

**Timing on your RTX 4050 (6GB):** step 31 encodes 100K passages — expect a few minutes on
GPU. The first run may pause briefly loading the cached model. If you ever see Hugging Face
connection-reset spam, it's harmless (offline mode is set; it uses the cache), but it should
be quiet now because the script sets `HF_HUB_OFFLINE=1`.

**VRAM note:** if step 31 throws a CUDA out-of-memory error on the 6GB card, lower the batch:
```bash
python stage3/31_encode_candidates.py --batch-size 32
```

## 5. Verify

```bash
python -c "import pandas as pd; df=pd.read_parquet('artifacts/features_100k.parquet'); print('hybrid_score' in df.columns, '| mean:', round(df['hybrid_score'].mean(),4)); print(df.sort_values('hybrid_score',ascending=False).head(5).index.tolist())"
```

You want `hybrid_score` present and a sensible top-5. Also check
`artifacts/stage3_hybrid_report.json` — the `dense_bm25_corr` should be **low** (~0.2-0.5);
low correlation means dense and BM25 capture different signal, which is the whole point of
combining them. If it's near 1.0, something's wrong (they'd be redundant).

## 6. Commit

```bash
git add stage3/ common/config.py artifacts/stage3_hybrid_report.json
git commit -m "Stage 3: hybrid retrieval (recency-weighted text, bge encode, BM25, hybrid_score)"
```

(`candidate_embeddings.npy`, `bm25_scores.npy`, `features_100k.parquet` are gitignored —
large and regenerable.)

## What to send me after the run

The contents of `artifacts/stage3_hybrid_report.json`. I want to confirm two things before
Stage 4: that the dense/BM25 correlation is healthy (low), and that the top-10 by hybrid score
are sensible candidates with real coverage — not the keyword-stuffers. If a known-stuffer
archetype is sitting in the hybrid top-10, that's fine (the disqualifiers correct it later),
but I want to see it so we know the corrections are doing their job in Stage 5.

When this runs and you've committed, tell me — Stage 4 is the honeypot audit (the 10 keyword
+ 4 arithmetic signals, recall-hardened and precision-guarded, with the ≤8% rate target that
keeps you clear of the 10% disqualification line).
