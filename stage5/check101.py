import pandas as pd, sys; sys.path.insert(0,".")
from common.io import iter_candidates
from common import config
sub = pd.read_csv("artifacts/submission_two.csv")
ids = set(sub.candidate_id)
rows=[(int(sub[sub.candidate_id==c['candidate_id']]['rank'].iloc[0]), c['profile'].get('country'), c['redrob_signals'].get('willing_to_relocate')) for c in iter_candidates(config.CANDIDATES_JSONL) if c['candidate_id'] in ids and c['profile'].get('country','').lower()!='india']
for r in sorted(rows): print(f'rank {r[0]:3d} {r[1]} relocate={r[2]}')
print(f'{len(rows)} overseas in top 100')