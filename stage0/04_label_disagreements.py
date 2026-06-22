"""
stage0/04_label_disagreements.py
Expand the golden set with the HIGHEST-INFORMATION candidates: the ones where the composite
and the LightGBM ranker disagree most in the top of the ranking.

Why these: a label on a candidate both models already agree on tells you nothing new. A label
where they disagree resolves WHICH model is right — exactly where it matters. ~35 targeted
labels here are worth more than 200 random ones.

Outputs a worksheet in the SAME format as the golden-set worksheet so you label it the same
way and fold it into golden_set.json.

Run:  python stage0/04_label_disagreements.py --n 35
Then: fill the 'label' column, run stage0/03_build_golden_set.py (it reads BOTH worksheets).
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402


def _mm(a):
    import numpy as np
    a = np.asarray(a, float)
    r = a.max() - a.min()
    return (a - a.min()) / r if r > 1e-12 else a * 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=35)
    ap.add_argument("--pool-top", type=int, default=300,
                    help="consider disagreements within the top-N of each model")
    args = ap.parse_args()
    config.ensure_artifacts()

    import numpy as np
    import pandas as pd
    import lightgbm as lgb
    from stage5.composite import score_dataframe

    df = pd.read_parquet(config.FEATURES_PARQUET)
    feats = json.loads(config.LGB_FEATURES_JSON.read_text())

    # composite ranking
    wts = json.loads(config.COMPOSITE_WEIGHTS_JSON.read_text())
    comp = _mm(score_dataframe(df, wts))
    comp_rank = pd.Series(comp, index=df.index).rank(ascending=False)

    # ranker ranking
    m_rule = lgb.Booster(model_file=str(config.RANKER_RULE_TXT))
    blend = json.loads(config.BLEND_JSON.read_text())
    alpha = blend.get("alpha_rule", 1.0)
    X = df[feats].fillna(0).values
    pr = _mm(m_rule.predict(X))
    if blend.get("has_llm") and config.RANKER_LLM_TXT.exists():
        m_llm = lgb.Booster(model_file=str(config.RANKER_LLM_TXT))
        rank_score = _mm(alpha * pr + (1 - alpha) * _mm(m_llm.predict(X)))
    else:
        rank_score = pr
    rank_rank = pd.Series(rank_score, index=df.index).rank(ascending=False)

    # candidates in the top pool of EITHER model
    in_pool = (comp_rank <= args.pool_top) | (rank_rank <= args.pool_top)
    pool = df.index[in_pool.values]

    # disagreement = absolute rank difference, biggest first
    disagree = (comp_rank - rank_rank).abs()
    cand = disagree.loc[pool].sort_values(ascending=False)

    # exclude ones already in the golden set
    golden = set(json.loads(config.GOLDEN_SET_JSON.read_text())) \
        if config.GOLDEN_SET_JSON.exists() else set()
    picks = [c for c in cand.index if c not in golden][:args.n]

    # pull profiles for the worksheet
    want = set(picks)
    rec = {}
    for c in iter_candidates(config.CANDIDATES_JSONL):
        if c["candidate_id"] in want:
            rec[c["candidate_id"]] = c
            if len(rec) == len(want):
                break

    out = config.ARTIFACTS / "disagreement_worksheet.csv"
    fields = ["label", "bucket", "candidate_id", "name", "title", "company", "size", "yoe",
              "location", "country", "notice_days", "relocate", "open_to_work",
              "comp_rank", "ranker_rank", "rank_gap", "summary"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for cid in picks:
            c = rec.get(cid, {})
            p = c.get("profile", {})
            w.writerow({
                "label": "", "bucket": "disagreement", "candidate_id": cid,
                "name": p.get("anonymized_name", ""), "title": p.get("current_title", ""),
                "company": p.get("current_company", ""), "size": p.get("current_company_size", ""),
                "yoe": p.get("years_of_experience", ""), "location": p.get("location", ""),
                "country": p.get("country", ""),
                "notice_days": c.get("redrob_signals", {}).get("notice_period_days", ""),
                "relocate": c.get("redrob_signals", {}).get("willing_to_relocate", ""),
                "open_to_work": c.get("redrob_signals", {}).get("open_to_work_flag", ""),
                "comp_rank": int(comp_rank[cid]), "ranker_rank": int(rank_rank[cid]),
                "rank_gap": int(disagree[cid]), "summary": p.get("summary", "")[:200],
            })

    print(f"wrote {len(picks)} disagreement candidates -> {out}")
    print("These are where composite and ranker disagree most — highest-information labels.")
    print("Fill the 'label' column (0-3), then re-run stage0/03_build_golden_set.py.")
    print("(03 must be updated to also read this worksheet — see integration notes.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
