# Stage 1 — Integration Instructions

Three new scripts go in `stage1/`, plus two small edits to files in `common/`. Everything
matches your existing layout (`common/` at repo root, `from common import config`, artifacts
at repo root). Do these in order.

## 1. Add the new files to `stage1/`

Copy these into your repo's `stage1/` folder:
- `stage1/10_parse_jd.py`
- `stage1/11_skill_taxonomy.py`
- `stage1/12_jd_embeddings.py`
- `stage1/README.md`

## 2. Edit `common/config.py` — add two blocks

**(a)** Find the line that defines `JD_MD` and add the docx path right after it:

```python
JD_DOCX = REPO_ROOT / "job_description.docx"   # organizers' original — source of truth
```

**(b)** Find the line that defines `GOLDEN_SET_JSON` (end of your Stage 0 outputs) and add
this block right after it:

```python
# Stage 1 outputs
JD_CONFIG_JSON = ARTIFACTS / "jd_config.json"
SKILL_GROUPS_JSON = ARTIFACTS / "skill_groups.json"
JD_EMBEDDING_NPY = ARTIFACTS / "jd_embedding.npy"
IDEAL_EMBEDDING_NPY = ARTIFACTS / "ideal_embedding.npy"
JD_TEXT_CACHE = ARTIFACTS / "jd_text.txt"
```

## 3. Edit `common/io.py` — add the docx reader

Append the `read_docx_text` function (it's in the `common/io.py` provided in this delivery —
just copy that one function to the end of your `common/io.py`). It uses only the standard
library, no new dependencies.

## 4. Run it

```bash
python stage1/10_parse_jd.py          # deterministic, no model — should PASS
python stage1/11_skill_taxonomy.py    # should PASS
```

Both run with zero ML dependencies. Then the embedding step (needs your GPU env):

```bash
pip install sentence-transformers      # if not already installed
python stage1/12_jd_embeddings.py      # downloads bge-large once, encodes on GPU
```

If `sentence-transformers` isn't installed yet, you can defer `12` — Stage 2 doesn't need
the embeddings; only Stage 3 (hybrid retrieval) does. So `10` and `11` unblock Stage 2 now.

## 5. Verify and commit

```bash
python -c "import json; c=json.load(open('artifacts/jd_config.json')); print('disqualifiers:', len(c['disqualifiers']), '| hard reqs:', list(c['hard_requirements']))"

git add stage1/ common/config.py common/io.py artifacts/jd_config.json artifacts/skill_groups.json
git commit -m "Stage 1: JD intelligence (deterministic parse, taxonomy, embeddings)"
```

## What you should see

- `jd_config.json`: 4 hard requirements, 6 soft, 7 disqualifiers, YOE 5–9 (ideal 6–8),
  consulting-firm list, and the ideal-candidate summary.
- `skill_groups.json`: 17 keyword groups, ~240 terms, names matching the jd_config keys.

When `10` and `11` pass and are committed, tell me and I'll build Stage 2 (candidate feature
engineering) — the master feature table, the two new disqualifier flags, and the
career-text-over-skill-list weighting that makes the keyword trap backfire.
