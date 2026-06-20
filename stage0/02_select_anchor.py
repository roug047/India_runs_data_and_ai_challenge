"""
stage0/02_select_anchor.py
Select the 60 golden-set candidates to hand-label — Day 1, from RAW signals only.

WHY A DAY-1 PROXY SELECTOR:
The v6 select_anchor_candidates() needs hybrid_score / honeypot_score / disqualifier
flags, which only exist after Stages 2-4. But the whole point of v6.1 is to label on
Day 1 so the anchor is ready before tuning. So this script reproduces the SAME five
information-rich buckets using cheap heuristics computable from raw JSON alone:

  bucket A "neutral strong" : JD-keyword hits in career text + product-company + 5-9yr
  bucket B "mid-band"       : YOE in [5,9], not obviously strong/weak
  bucket C "keyword trap"   : many AI skill names BUT non-engineering current title
  bucket D "honeypot suspect": cheap arithmetic impossibility (durations vs YOE/dates)
  bucket E "disqualifier"   : IT-services lifer / outside-India-no-relocate / too junior-senior

These are NEUTRAL proxies (no composite_score involved) so the anchor stays a true
held-out validator (v6.1 anti-circularity fix). After Stage 3 you MAY re-run the full
selector to swap in hybrid_score for bucket A — but you do NOT need to; the Day-1 anchor
is valid on its own. Freeze whichever you label first.

Output:
  artifacts/anchor_candidates.json    -> {"ids":[...60], "buckets":{id:bucket}}
  artifacts/golden_set_worksheet.csv  -> human-readable; you fill the 'label' column

Run:  python stage0/02_select_anchor.py
      python stage0/02_select_anchor.py --sample
"""
from __future__ import annotations
import argparse
import csv
import json
import random
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import load_candidates  # noqa: E402

# --- cheap keyword banks (subset of Stage-1 taxonomy; enough for proxy bucketing) ---
JD_HARD_KW = [
    "retrieval", "ranking", "embedding", "vector", "semantic search", "faiss",
    "milvus", "pinecone", "qdrant", "weaviate", "elasticsearch", "opensearch",
    "ndcg", "mrr", "learning to rank", "lambdamart", "recommendation", "recsys",
    "bm25", "hybrid search", "reranking", "cross-encoder", "bi-encoder",
    "sentence-transformers", "information retrieval",
]
AI_SKILL_NAMES = [
    "nlp", "fine-tuning llms", "lora", "qlora", "peft", "embeddings", "milvus",
    "faiss", "pinecone", "weaviate", "qdrant", "rag", "langchain", "llamaindex",
    "transformers", "bert", "gpt", "vector", "ranking", "recommendation",
]
ENG_TITLE_TOKENS = ["engineer", "developer", "scientist", "architect", "ml ", "ai ",
                    "research", "applied scientist", "data scien"]
SERVICES_FIRMS = ["tcs", "tata consultancy", "infosys", "wipro", "accenture",
                  "cognizant", "capgemini", "mphasis", "tech mahindra", "hexaware",
                  "ltimindtree", "mindtree", "hcl", "l&t infotech", "persistent"]
PRODUCT_COS = ["google", "amazon", "microsoft", "meta", "apple", "netflix",
               "flipkart", "swiggy", "zomato", "phonepe", "razorpay", "meesho",
               "zepto", "cred", "groww", "zerodha", "uber", "linkedin", "nvidia"]
PREFERRED_LOCS = ["pune", "noida", "hyderabad", "mumbai", "delhi", "ncr",
                  "gurgaon", "gurugram", "bengaluru", "bangalore"]


def _career_text(c) -> str:
    parts = [c["profile"].get("summary", ""), c["profile"].get("headline", "")]
    for r in c.get("career_history", []):
        parts.append(r.get("description", ""))
        parts.append(r.get("title", ""))
    return " ".join(parts).lower()


def _hard_kw_hits(c) -> int:
    t = _career_text(c)
    return sum(1 for kw in JD_HARD_KW if kw in t)


def _ai_skill_count(c) -> int:
    names = " ".join(s.get("name", "").lower() for s in c.get("skills", []))
    return sum(1 for kw in AI_SKILL_NAMES if kw in names)


def _is_eng_title(c) -> bool:
    t = c["profile"].get("current_title", "").lower()
    return any(tok in t for tok in ENG_TITLE_TOKENS)


def _is_services_lifer(c) -> bool:
    hist = c.get("career_history", [])
    if not hist:
        return False
    months = sum(r.get("duration_months", 0) for r in hist)
    serv = sum(r.get("duration_months", 0) for r in hist
               if any(f in r.get("company", "").lower() for f in SERVICES_FIRMS))
    return months > 0 and serv / months >= 0.6


def _at_product(c) -> bool:
    comp = c["profile"].get("current_company", "").lower()
    return any(p in comp for p in PRODUCT_COS)


def _cheap_honeypot_suspect(c) -> bool:
    """Raw arithmetic impossibilities — no keyword dependence (mirrors Stage-4 signals)."""
    yoe = c["profile"].get("years_of_experience", 0)
    hist = c.get("career_history", [])
    total_months = sum(r.get("duration_months", 0) for r in hist)
    # A: durations grossly exceed plausible career length
    if total_months > (yoe + 3) * 12 * 1.5:
        return True
    # B: a skill claimed longer than the whole career + 2yr grace
    for s in c.get("skills", []):
        if s.get("duration_months", 0) > (yoe * 12) + 24:
            return True
    # C: >=2 roles whose duration disagrees with their own dates by >12 months
    mism = 0
    for r in hist:
        if r.get("end_date") and r.get("start_date"):
            try:
                s = datetime.strptime(r["start_date"], "%Y-%m-%d")
                e = datetime.strptime(r["end_date"], "%Y-%m-%d")
                if abs((e - s).days / 30.0 - r.get("duration_months", 0)) > 12:
                    mism += 1
            except Exception:
                pass
    return mism >= 2


def _is_disqualifier_suspect(c) -> bool:
    prof = c["profile"]
    sig = c["redrob_signals"]
    yoe = prof.get("years_of_experience", 0)
    loc = (prof.get("location", "") + " " + prof.get("country", "")).lower()
    in_india = "india" in prof.get("country", "").lower()
    in_pref = any(x in loc for x in PREFERRED_LOCS)
    outside_no_relocate = (not in_india) and (not sig.get("willing_to_relocate", False))
    too_far_yoe = yoe < 3 or yoe > 11   # JD band is 5-9; >11 or <3 is clearly out-of-range
    return _is_services_lifer(c) or outside_no_relocate or too_far_yoe or \
        (not _is_eng_title(c) and _ai_skill_count(c) >= 5)


def _row(c) -> dict:
    prof = c["profile"]
    sig = c["redrob_signals"]
    return {
        "candidate_id": c["candidate_id"],
        "name": prof.get("anonymized_name", ""),
        "title": prof.get("current_title", ""),
        "company": prof.get("current_company", ""),
        "size": prof.get("current_company_size", ""),
        "yoe": prof.get("years_of_experience", ""),
        "location": prof.get("location", ""),
        "country": prof.get("country", ""),
        "notice_days": sig.get("notice_period_days", ""),
        "relocate": sig.get("willing_to_relocate", ""),
        "open_to_work": sig.get("open_to_work_flag", ""),
        "hard_kw_hits": _hard_kw_hits(c),
        "ai_skill_count": _ai_skill_count(c),
        "eng_title": int(_is_eng_title(c)),
        "github": sig.get("github_activity_score", ""),
        "headline": prof.get("headline", "")[:80],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--per-bucket", type=int, default=12)
    args = ap.parse_args()

    config.ensure_artifacts()
    src = config.SAMPLE_CANDIDATES if args.sample else config.CANDIDATES_JSONL
    if not Path(src).exists():
        print(f"WARNING: {src} missing; using sample.")
        src = config.SAMPLE_CANDIDATES
    cands = load_candidates(Path(src))
    print(f"Loaded {len(cands)} candidates from {Path(src).name}")

    rng = random.Random(config.SEED)

    # Bucket membership (a candidate may qualify for several; we assign greedily C>D>E>A>B
    # so the rarer/more-informative buckets win the candidate).
    strong, midband, trap, honey, disq = [], [], [], [], []
    for c in cands:
        if (not _is_eng_title(c)) and _ai_skill_count(c) >= 5:
            trap.append(c)
        elif _cheap_honeypot_suspect(c):
            honey.append(c)
        elif _is_disqualifier_suspect(c):
            disq.append(c)
        elif _hard_kw_hits(c) >= 3 and _at_product(c) and \
                5 <= c["profile"].get("years_of_experience", 0) <= 9:
            strong.append(c)
        elif 5 <= c["profile"].get("years_of_experience", 0) <= 9:
            midband.append(c)

    k = args.per_bucket

    def take(pool, kk):
        rng.shuffle(pool)
        return pool[:min(kk, len(pool))]

    chosen, bucket_of = [], {}
    for name, pool in [("strong", strong), ("midband", midband), ("trap", trap),
                       ("honeypot", honey), ("disqualifier", disq)]:
        picks = take(pool, k)
        for c in picks:
            if c["candidate_id"] not in bucket_of:
                bucket_of[c["candidate_id"]] = name
                chosen.append(c)

    # If buckets were thin (small sample), backfill from mid-band / all to reach target.
    target = min(60, len(cands))
    if len(chosen) < target:
        seen = set(bucket_of)
        pool = [c for c in cands if c["candidate_id"] not in seen]
        rng.shuffle(pool)
        for c in pool[: target - len(chosen)]:
            bucket_of[c["candidate_id"]] = "backfill"
            chosen.append(c)

    ids = [c["candidate_id"] for c in chosen][:target]
    bucket_of = {i: bucket_of[i] for i in ids}

    config.ANCHOR_CANDIDATES_JSON.write_text(json.dumps(
        {"ids": ids, "buckets": bucket_of,
         "source": "sample" if args.sample else "full_pool"}, indent=2))

    # Human worksheet — you fill 'label' (0/1/2/3) and optional 'note'.
    fields = ["label", "bucket", "candidate_id", "name", "title", "company", "size",
              "yoe", "location", "country", "notice_days", "relocate", "open_to_work",
              "hard_kw_hits", "ai_skill_count", "eng_title", "github", "note", "headline"]
    by_id = {c["candidate_id"]: c for c in chosen}
    with open(config.ANCHOR_WORKSHEET_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        # order by bucket so similar cases sit together while labeling
        for cid in sorted(ids, key=lambda i: bucket_of[i]):
            r = _row(by_id[cid])
            r["label"] = ""      # YOU fill: 0/1/2/3
            r["bucket"] = bucket_of[cid]
            r["note"] = ""
            w.writerow(r)

    counts = {b: sum(1 for v in bucket_of.values() if v == b) for b in set(bucket_of.values())}
    print(f"Selected {len(ids)} anchor candidates.")
    print(f"Bucket counts: {counts}")
    print(f"  ids       -> {config.ANCHOR_CANDIDATES_JSON}")
    print(f"  worksheet -> {config.ANCHOR_WORKSHEET_CSV}")
    print("\nNEXT: open the worksheet, read each profile, fill the 'label' column (0-3),")
    print("then run:  python stage0/03_build_golden_set.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
