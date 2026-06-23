import json
from pathlib import Path
import sys; sys.path.insert(0, ".")
from common.io import iter_candidates

CID = sys.argv[1]  # e.g. CAND_0012345
for c in iter_candidates(Path("candidates.jsonl")):
    if c["candidate_id"] == CID:
        p = c["profile"]
        print(f"\n{'='*70}\n{CID}  |  {p['anonymized_name']}")
        print(f"{p['current_title']} @ {p['current_company']} ({p['current_company_size']})")
        print(f"YOE {p['years_of_experience']} | {p['location']}, {p['country']}")
        print(f"\nSUMMARY: {p['summary']}")
        print(f"\n--- CAREER ---")
        for r in c["career_history"]:
            print(f"\n[{r['title']} @ {r['company']}] {r['start_date']}→{r['end_date']} ({r['duration_months']}mo)")
            print(f"  {r['description']}")
        print(f"\n--- SKILLS ---")
        for s in c["skills"]:
            print(f"  {s['name']} ({s['proficiency']}, {s.get('duration_months','?')}mo, {s['endorsements']} end.)")
        sig = c["redrob_signals"]
        print(f"\n--- SIGNALS ---")
        print(f"  assessments: {sig['skill_assessment_scores']}")
        print(f"  github={sig['github_activity_score']} notice={sig['notice_period_days']}d "
              f"relocate={sig['willing_to_relocate']} open_to_work={sig['open_to_work_flag']}")
        print(f"  saved_by_recruiters_30d={sig['saved_by_recruiters_30d']} "
              f"recruiter_response_rate={sig['recruiter_response_rate']}")
        break