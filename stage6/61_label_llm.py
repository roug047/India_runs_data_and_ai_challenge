"""
stage6/61_label_llm.py
Label the SAME training candidates with a local Qwen2.5-3B GGUF (label source B).

Zero API. Runs on your GPU via llama-cpp-python. Independent of the rule labeler so the two
rankers make different mistakes. Reads the candidate's raw profile (not features) so the LLM
judges the actual text — catching nuance the rule scorer misses, and vice versa.

6GB-VRAM friendly: 3B-q4 needs ~2.5GB. If the model file or llama-cpp is missing, this exits
gracefully and Stage 6 proceeds with rule labels only (the blend just weights LLM at 0).

Download once (precompute):
  huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf \
    --local-dir models

Run:  python stage6/61_label_llm.py
Output: artifacts/train_labels_llm.json  {candidate_id: 0|1|2|3}
"""
from __future__ import annotations
import os, ctypes
# Make torch's bundled CUDA DLLs findable by llama-cpp's llama.dll
try:
    import torch, pathlib
    torch_lib = pathlib.Path(torch.__file__).parent / "lib"
    os.add_dll_directory(str(torch_lib))
    # also add CUDA bin if present
    for p in os.environ.get("PATH", "").split(";"):
        if "cuda" in p.lower() and os.path.isdir(p):
            os.add_dll_directory(p)
except Exception as e:
    print(f"(dll path setup skipped: {e})")


import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402

MODEL_PATH = config.REPO_ROOT / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"

RUBRIC = (
    "You are screening candidates for a Senior AI Engineer role. The role needs someone who "
    "has SHIPPED production retrieval/ranking/recommendation/search systems to real users, "
    "with embeddings, vector search, and ranking evaluation (NDCG/MRR). 5-9 years experience. "
    "Based in India or willing to relocate. Tilt toward shippers over researchers. "
    "Keyword lists do NOT matter; what they actually BUILT matters. Rate fit 0-3:\n"
    "3=strong fit (shipped relevant systems, right experience)\n"
    "2=moderate (adjacent or missing 1-2 things)\n"
    "1=weak (some relevance, mostly off)\n"
    "0=not fit (wrong domain, pure consulting, non-technical, or impossible profile)\n"
)


def profile_blurb(c: dict) -> str:
    p = c["profile"]
    lines = [f"Title: {p.get('current_title','')} at {p.get('current_company','')}",
             f"YOE: {p.get('years_of_experience','')}  Location: {p.get('location','')}, {p.get('country','')}",
             f"Summary: {p.get('summary','')[:350]}"]
    for r in c.get("career_history", [])[:3]:
        lines.append(f"Role: {r.get('title','')} - {r.get('description','')[:200]}")
    skills = ", ".join(s.get("name", "") for s in c.get("skills", [])[:12])
    lines.append(f"Skills: {skills}")
    sig = c["redrob_signals"]
    lines.append(f"Notice: {sig.get('notice_period_days','')}d  "
                 f"OpenToWork: {sig.get('open_to_work_flag','')}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device-layers", type=int, default=-1,
                    help="n_gpu_layers (-1=all on GPU; lower if VRAM tight)")
    args = ap.parse_args()
    config.ensure_artifacts()

    if not config.TRAIN_LABELS_RULE_JSON.exists():
        print("FATAL: run stage6/60_label_rule.py first (defines the training set).")
        return 1
    target_ids = set(json.loads(config.TRAIN_LABELS_RULE_JSON.read_text()).keys())
    print(f"labeling {len(target_ids)} candidates with local Qwen2.5-3B")

    if not MODEL_PATH.exists():
        print(f"⚠ model not found at {MODEL_PATH}")
        print("  Stage 6 will proceed with RULE LABELS ONLY (blend weights LLM at 0).")
        print("  To enable: download the GGUF (see script header).")
        return 0
    try:
        from llama_cpp import Llama
    except Exception as e:
        print(f"⚠ llama-cpp unavailable ({type(e).__name__}) — proceeding with rule labels only.")
        return 0
        print("⚠ llama-cpp-python not installed — proceeding with rule labels only.")
        print("  pip install llama-cpp-python")
        return 0

    llm = Llama(model_path=str(MODEL_PATH), n_ctx=2048,
                n_gpu_layers=args.device_layers, verbose=False)

    # collect the target candidates' raw records
    records = {}
    for c in iter_candidates(config.CANDIDATES_JSONL):
        if c["candidate_id"] in target_ids:
            records[c["candidate_id"]] = c
            if len(records) == len(target_ids):
                break

    labels = {}
    done = 0
    for cid, c in records.items():
        prompt = (f"{RUBRIC}\nCANDIDATE:\n{profile_blurb(c)}\n\n"
                  "Answer with ONLY one digit (0, 1, 2, or 3):")
        try:
            out = llm(prompt, max_tokens=3, temperature=0.0)["choices"][0]["text"].strip()
            digit = next((ch for ch in out if ch in "0123"), None)
            labels[cid] = int(digit) if digit else 1
        except Exception:
            labels[cid] = 1   # neutral on failure
        done += 1
        if done % 250 == 0:
            print(f"  ...{done}/{len(records)}")

    config.TRAIN_LABELS_LLM_JSON.write_text(json.dumps(labels))
    from collections import Counter
    print(f"LLM-labeled {len(labels)}  distribution: {dict(sorted(Counter(labels.values()).items()))}")
    print(f"-> {config.TRAIN_LABELS_LLM_JSON}")
    print("STAGE 6.61 (llm labels): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
