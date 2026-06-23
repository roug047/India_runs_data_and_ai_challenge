# Stage 6 — Integration Instructions

Two-model ranker + anchor-tuned blend. GPU only in step 61 (the local LLM labeling).

## 1. Add files to `stage6/`

- `stage6/__init__.py`
- `stage6/60_label_rule.py`
- `stage6/61_label_llm.py`
- `stage6/62_train_blend.py`
- `stage6/README.md`

## 2. Add to `common/config.py` (at end)

```python
# Stage 6 outputs
TRAIN_LABELS_RULE_JSON = ARTIFACTS / "train_labels_rule.json"
TRAIN_LABELS_LLM_JSON = ARTIFACTS / "train_labels_llm.json"
RANKER_RULE_TXT = ARTIFACTS / "ranker_rule.txt"
RANKER_LLM_TXT = ARTIFACTS / "ranker_llm.txt"
BLEND_JSON = ARTIFACTS / "blend.json"
LGB_FEATURES_JSON = ARTIFACTS / "lgb_features.json"
STAGE6_REPORT_JSON = ARTIFACTS / "stage6_report.json"
```

## 3. Install dependencies

```bash
pip install lightgbm
pip install llama-cpp-python      # for the local LLM labeler (GPU build)
```

For `llama-cpp-python` with GPU on Windows, the prebuilt CUDA wheel is easiest:
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```
If that fights you, the CPU build also works (labeling 4000 on CPU is slower but fine as
precompute). Or skip the LLM entirely — see step 5.

## 4. Download the 3B model (fits your 6GB card)

```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir models
```

This puts the GGUF at `models/qwen2.5-3b-instruct-q4_k_m.gguf` (~2GB download).

## 5. Run

```bash
python stage6/60_label_rule.py --n 4000      # instant; deterministic labels
python stage6/61_label_llm.py                # GPU, ~30-60 min for 4000 on 3B
python stage6/62_train_blend.py              # trains both rankers, picks alpha
```

**If you decide to skip the LLM** (or it OOMs / won't install): just don't run `61`. Step
`62` detects the missing LLM labels and trains rule-only with `alpha=1.0`. Fully valid.

**VRAM note (6GB):** if `61` throws a CUDA OOM, lower GPU layers:
```bash
python stage6/61_label_llm.py --device-layers 20
```
That keeps some layers on CPU. Slower but fits.

## 6. Check the result

After `62`, look at `artifacts/stage6_report.json`:
- `alpha_rule` — the blend weight. ~0.5 means both sources contribute; ~1.0 means the LLM
  added nothing useful on the anchor (rule model carried it).
- `anchor_ndcg10` — NDCG@10 of the blended ranker on your golden set.
- `anchor_spearman_ranker` — compare this to your Stage 5 composite's 0.73. **If the ranker's
  spearman is HIGHER, the ML ranker beats the composite.** If lower, the composite was better
  and Stage 7 should lean on it.

## 7. Commit

```bash
git add stage6/ common/config.py artifacts/blend.json artifacts/lgb_features.json artifacts/stage6_report.json artifacts/train_labels_rule.json
git commit -m "Stage 6: two-model ranker, anchor-tuned blend"
```

(`ranker_*.txt`, `train_labels_llm.json`, the GGUF model are large/gitignored.)

## What to send me

`artifacts/stage6_report.json`. The key comparison: **ranker spearman vs your composite's
0.73.** This tells us whether Stage 7 should rank by the ML blend, the composite, or a
combination. We decide that with the number in hand — the anchor tells us which is actually
better, so we never ship a worse ranker than Submission #1.

Then Stage 7 is the finale: `rank.py` (CPU-only, ≤5 min, the reproduced step), the top-30
human audit, the diversified reasoning (fixing the templated-text issue), the validator, and
Submission #2 — the primary.
