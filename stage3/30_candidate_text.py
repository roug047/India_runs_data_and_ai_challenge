"""
stage3/30_candidate_text.py
Synthesize one retrieval text per candidate, recency-weighted to survive truncation.

WHY RECENCY-FIRST: bge-large truncates at ~512 tokens (~2000 chars). ~32% of candidate
career texts exceed that. If we list roles oldest-first, truncation would chop the most
recent (most relevant) role. So we put the CURRENT role first and repeat it, ensuring the
candidate's latest and most relevant work always lands inside the encoder's window.

This text is also the corpus for BM25 (Stage 3.32). Same text, two retrieval views.

No GPU. Streams the pool. Output is small (text only).

Run:  python stage3/30_candidate_text.py
      python stage3/30_candidate_text.py --sample
Output: artifacts/candidate_texts.jsonl  ({"candidate_id":..., "text":...} per line)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402


def synthesize(c: dict) -> str:
    prof = c["profile"]
    hist = sorted(c.get("career_history", []),
                  key=lambda r: r.get("start_date", ""), reverse=True)

    parts: list[str] = []
    # 1. current/most-recent role FIRST and doubled (recency weight, truncation-safe)
    if hist:
        cur = hist[0]
        cur_blob = f"{cur.get('title','')} at {cur.get('company','')}: {cur.get('description','')}"
        parts.append(cur_blob)
        parts.append(cur_blob)   # repeat → survives truncation, weights recent work

    # 2. headline + summary (candidate's own framing)
    parts.append(prof.get("headline", ""))
    parts.append(prof.get("summary", ""))

    # 3. remaining roles, newest-to-oldest
    for r in hist[1:]:
        parts.append(f"{r.get('title','')} at {r.get('company','')}: {r.get('description','')}")

    # 4. skills last (lowest priority — most gameable, least likely to survive truncation,
    #    which is INTENTIONAL: we don't want skill keywords dominating the semantic vector)
    skills = ", ".join(s.get("name", "") for s in c.get("skills", []))
    if skills:
        parts.append("Skills: " + skills)

    return " ".join(p for p in parts if p).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args()
    config.ensure_artifacts()

    src = config.SAMPLE_CANDIDATES if args.sample else config.CANDIDATES_JSONL
    if not Path(src).exists():
        print(f"WARNING: {src} missing; using sample.")
        src = config.SAMPLE_CANDIDATES

    out = config.CANDIDATE_TEXT_JSONL if not args.sample else \
        config.CANDIDATE_TEXT_JSONL.with_name("candidate_texts_sample.jsonl")

    n = 0
    lengths = []
    with open(out, "w", encoding="utf-8") as f:
        for c in iter_candidates(Path(src)):
            text = synthesize(c)
            lengths.append(len(text))
            f.write(json.dumps({"candidate_id": c["candidate_id"], "text": text}) + "\n")
            n += 1
            if n % 20000 == 0:
                print(f"  ...{n}")

    import statistics as st
    print(f"wrote {n} candidate texts -> {out}")
    print(f"text length chars: mean={int(st.mean(lengths))} max={max(lengths)} "
          f"over2000={sum(1 for l in lengths if l > 2000)}")
    print("STAGE 3.30 (candidate text): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
