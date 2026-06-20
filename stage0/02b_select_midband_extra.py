import sys, csv, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root, like 03 does

from common import config
from common.io import load_candidates

def main():
    rng = random.Random(7)
    print("loading candidates from:", config.CANDIDATES_JSONL)
    cands = load_candidates(config.CANDIDATES_JSONL)
    print("loaded", len(cands), "candidates")

    ENG = ["engineer","developer","scientist","architect","ml","ai","applied scien","data scien"]
    already = set()
    if config.ANCHOR_CANDIDATES_JSON.exists():
        already = set(json.load(open(config.ANCHOR_CANDIDATES_JSON))["ids"])
    print("already in anchor:", len(already))

    pool = []
    for c in cands:
        p = c["profile"]
        if c["candidate_id"] in already: continue
        if not (5 <= p.get("years_of_experience", 0) <= 9): continue
        if not any(t in p.get("current_title","").lower() for t in ENG): continue
        if "india" not in p.get("country","").lower(): continue
        pool.append(c)
    print("candidates matching midband filter:", len(pool))

    rng.shuffle(pool)
    extra = pool[:15]
    if not extra:
        print("NOTHING matched — check that CANDIDATES_JSONL points to the full 100K file")
        return

    with open(config.ANCHOR_WORKSHEET_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for c in extra:
            p = c["profile"]; s = c["redrob_signals"]
            w.writerow(["", "midband_extra", c["candidate_id"], p.get("anonymized_name",""),
                        p.get("current_title",""), p.get("current_company",""),
                        p.get("current_company_size",""), p.get("years_of_experience",""),
                        p.get("location",""), p.get("country",""),
                        s.get("notice_period_days",""), s.get("willing_to_relocate",""),
                        s.get("open_to_work_flag",""), "", "", 1,
                        s.get("github_activity_score",""), "", p.get("headline","")[:80]])
    print(f"appended {len(extra)} midband candidates to {config.ANCHOR_WORKSHEET_CSV}")
    print("label them in the worksheet, then re-run stage0/03_build_golden_set.py")

if __name__ == "__main__":
    main()