# Stage 6 — Two-Model Ranker + Anchor-Tuned Blend

Trains LightGBM rankers on two INDEPENDENT label sources and blends them by a weight chosen
to maximize NDCG@10 on your golden set. The blend can only help: if one label source is
biased, the anchor-tuned alpha shifts toward the other.

## Why two independent label sources

A single LLM-labeled ranker inherits the LLM's biases. The v6 design uses two genuinely
independent sources so the rankers make different errors:
- **Rule labels** (source A): deterministic, from features, encodes the JD's priorities.
- **LLM labels** (source B): local Qwen2.5-3B reads the raw profile text, catches nuance.

The blend weight `alpha` (rule weight) is chosen to maximize NDCG@10 on your hand labels —
so the combination is tuned to human judgment, not assumed.

## Files

| File | Does | GPU? |
|------|------|------|
| `60_label_rule.py` | Stratified 4000-candidate sample, deterministic 0-3 labels | no |
| `61_label_llm.py` | Same candidates labeled by local Qwen2.5-3B (6GB-friendly) | yes |
| `62_train_blend.py` | Trains 2 LightGBM rankers, picks alpha on the anchor | no |

## Setup (one-time)

```bash
pip install lightgbm llama-cpp-python
# download the 3B GGUF (fits 6GB VRAM at q4 ~2.5GB):
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir models
```

## Run

```bash
python stage6/60_label_rule.py --n 4000     # instant
python stage6/61_label_llm.py               # GPU, ~30-60 min on 3B for 4000
python stage6/62_train_blend.py             # trains + blends, fast
```

## Graceful degradation

If the Qwen model or llama-cpp is missing, `61` exits cleanly and `62` trains rule-only with
`alpha=1.0`. The system still produces a valid, defensible ranker — the LLM is upside, not a
dependency.

## Validated

- Rule labeler: the two known traps → 0, the genuine fit (CAND_0000031) → 3, distribution
  spans all four labels.
- Blend: alpha-selection correctly maximizes anchor NDCG@10 (rule-only vs llm-only vs blend
  compared; best alpha chosen).

## Important: no train/inference skew

`62` writes `lgb_features.json` — the exact feature columns and order. Stage 7 `rank.py` reads
this same list, so the ranker sees identical inputs at inference. This is the classic ML bug
the v6.1 audit flagged; we close it with the shared feature list + an assertion in rank.py.

## Consumed downstream

- `ranker_rule.txt`, `ranker_llm.txt`, `blend.json`, `lgb_features.json` → Stage 7 rank.py.
