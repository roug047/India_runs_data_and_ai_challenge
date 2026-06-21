import json
import sys; sys.path.insert(0, ".")
from common import config
from common.io import iter_candidates
want = {"CAND_0018499", "CAND_0081846", "CAND_0086022"}
for c in iter_candidates(config.CANDIDATES_JSONL):
    if c["candidate_id"] in want:
        print(c["candidate_id"], "::", c["profile"]["current_company"])
        for r in c["career_history"]:
            if "50M" in r["description"] or "RAG" in r["description"]:
                print("   ", r["description"][:130])
        if len(want) == 1: break
        want.discard(c["candidate_id"])