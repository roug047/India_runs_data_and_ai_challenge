# Stage 1 — JD Intelligence (zero-API, deterministic)

Turns the Senior AI Engineer JD into structured artifacts the whole pipeline keys off.
No paid API, no required model — the JD config is hand-authored from the organizers'
`job_description.docx` and is correct on its own. An optional local-LLM refinement exists
but is **off by default**.

## Scripts (run in order)

| Script | Does | Output |
|--------|------|--------|
| `10_parse_jd.py` | Reads `job_description.docx` (source of truth), writes the deterministic JD config: hard/soft requirement strengths, 7 disqualifiers, YOE band, consulting-firm list, ideal-candidate summary | `artifacts/jd_config.json`, `artifacts/jd_text.txt` |
| `11_skill_taxonomy.py` | 17 keyword groups whose names match the jd_config requirement/disqualifier keys; supplies the vocabulary Stage 2 matches against career text | `artifacts/skill_groups.json` |
| `12_jd_embeddings.py` | Encodes the JD + ideal summary with bge-large, **using the query prefix** (candidates in Stage 3 get NO prefix) | `artifacts/jd_embedding.npy`, `artifacts/ideal_embedding.npy`, `artifacts/embedding_meta.json` |

## Run

```bash
python stage1/10_parse_jd.py                 # deterministic (default)
python stage1/11_skill_taxonomy.py
python stage1/12_jd_embeddings.py            # needs sentence-transformers; GPU fine
# optional, later: python stage1/10_parse_jd.py --use-llm
```

## Why these choices (defense notes)

- **Source of truth is the organizers' .docx**, parsed with a stdlib-only reader — your
  hand-made `.md` could drift; we never depend on it.
- **Deterministic config** means Stage 1 is reproducible and survives a Stage-5 defense
  ("show me your JD parse" → a hand-authored config traceable to JD sentences, not a
  black-box LLM call).
- **Every requirement strength and disqualifier cites a JD sentence** (see comments in
  `10_parse_jd.py`). The 7 disqualifiers are exactly the JD's explicit rejects plus the
  title-chaser soft-negative.
- **bge asymmetry is handled**: JD/ideal are queries (prefixed); candidates are passages
  (no prefix, Stage 3). `embedding_meta.json` records both so Stage 3 stays consistent.

## Validated on the two sample traps

Against `CAND_0000001` (keyword-stuffer) the taxonomy shows the decisive gap: 5 CV/speech
hits and 1 vector hit in the **skills list**, but **zero** hard-requirement or production
hits in the **career descriptions**. Stage 2 weights career-text over skill-list, so this
candidate sinks — exactly the trap the JD describes.

## Consumed downstream

- `jd_config.json` → Stage 2 (requirement coverage, disqualifier flags), Stage 5 (weights)
- `skill_groups.json` → Stage 2 (feature extraction vocabulary)
- `jd_embedding.npy`, `ideal_embedding.npy` → Stage 3 (hybrid semantic score)
- `embedding_meta.json` → Stage 3 (same model + prefix convention)
