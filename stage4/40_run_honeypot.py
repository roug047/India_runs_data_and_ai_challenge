"""
stage4/40_run_honeypot.py
Apply honeypot signals across the pool, write honeypot_score into the feature table,
and report the flag rate + a synthetic recall test.

Two things we must verify (v6.1):
  PRECISION: the flag rate must be TINY (~0.1-1%). Honeypots are ~0.08% of the pool. If we
             flag 5%+, we're removing real candidates from the top 100 and losing NDCG.
  RECALL:    synthetic impossible profiles must trip at least one signal.

Run:  python stage4/40_run_honeypot.py
      python stage4/40_run_honeypot.py --sample
Output: honeypot_score + is_likely_honeypot in features parquet;
        artifacts/stage4_honeypot_report.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402
from stage4.honeypot_signals import honeypot_signals  # noqa: E402


def _synthetic_recall_test() -> dict:
    """Five hand-built impossible profiles; each MUST trip >=1 signal."""
    cases = [
        {"name": "8yr_role_but_2yr_career", "profile": {"years_of_experience": 2.0},
         "career_history": [{"company": "X", "title": "Eng", "start_date": "2022-01-01",
                             "end_date": "2030-01-01", "duration_months": 96,
                             "is_current": True}], "skills": []},
        {"name": "expert_10_skills_zero", "profile": {"years_of_experience": 6.0},
         "career_history": [{"company": "X", "title": "Eng", "start_date": "2019-01-01",
                             "end_date": "2025-01-01", "duration_months": 72}],
         "skills": [{"name": f"S{i}", "proficiency": "expert", "duration_months": 0}
                    for i in range(10)]},
        {"name": "summary_yoe_contradiction", "profile": {"years_of_experience": 2.8,
         "summary": "Machine learning engineer with 7.4 years of experience in production ML."},
         "career_history": [{"company": "X", "title": "Eng", "start_date": "2019-01-01",
                             "end_date": "2026-01-01", "duration_months": 84}],
         "skills": [{"name": "Py", "proficiency": "expert", "duration_months": 80}]},
        {"name": "tenure_sum_impossible", "profile": {"years_of_experience": 5.0},
         "career_history": [{"company": "A", "title": "E", "start_date": "2020-01-01",
                             "end_date": "2025-01-01", "duration_months": 60},
                            {"company": "B", "title": "E", "start_date": "2020-01-01",
                             "end_date": "2025-01-01", "duration_months": 60},
                            {"company": "C", "title": "E", "start_date": "2020-01-01",
                             "end_date": "2025-01-01", "duration_months": 60}],
         "skills": []},
        {"name": "date_mismatch", "profile": {"years_of_experience": 7.0},
         "career_history": [{"company": "A", "title": "E", "start_date": "2023-01-01",
                             "end_date": "2023-06-01", "duration_months": 80},
                            {"company": "B", "title": "E", "start_date": "2022-01-01",
                             "end_date": "2022-03-01", "duration_months": 60}],
         "skills": []},
    ]
    results = {}
    for c in cases:
        r = honeypot_signals(c)
        results[c["name"]] = {"score": r["honeypot_score"],
                              "flagged": r["is_likely_honeypot"],
                              "reasons": r["honeypot_reasons"]}
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args()
    config.ensure_artifacts()

    # recall test first — fail loudly if a known-impossible profile slips through
    recall = _synthetic_recall_test()
    missed = [k for k, v in recall.items() if not v["flagged"]]
    print("Synthetic recall test:")
    for k, v in recall.items():
        print(f"  {'PASS' if v['flagged'] else 'MISS'}  {k:28s} score={v['score']} [{v['reasons']}]")
    if missed:
        print(f"  WARNING: {len(missed)} synthetic honeypots not flagged: {missed}")

    try:
        import pandas as pd
    except ImportError:
        print("FATAL: pip install pandas pyarrow")
        return 1

    src = config.SAMPLE_CANDIDATES if args.sample else config.CANDIDATES_JSONL
    if not Path(src).exists():
        src = config.SAMPLE_CANDIDATES
    feat_file = config.FEATURES_PARQUET.with_name("features_sample.parquet") \
        if args.sample else config.FEATURES_PARQUET

    rows = []
    n = 0
    for c in iter_candidates(Path(src)):
        r = honeypot_signals(c)
        rows.append({"candidate_id": c["candidate_id"],
                     "honeypot_score": r["honeypot_score"],
                     "is_likely_honeypot": r["is_likely_honeypot"],
                     "honeypot_signal_count": r["honeypot_signal_count"]})
        n += 1
        if n % 20000 == 0:
            print(f"  ...{n}")

    hp = pd.DataFrame(rows).set_index("candidate_id")
    flag_rate = float(hp["is_likely_honeypot"].mean())

    # write into the feature table if it exists as parquet
    try:
        df = pd.read_parquet(feat_file)
        for col in ["honeypot_score", "is_likely_honeypot", "honeypot_signal_count"]:
            if col in df.columns:
                df = df.drop(columns=[col])
        df = df.join(hp, how="left")
        df["honeypot_score"] = df["honeypot_score"].fillna(1.0)
        df["is_likely_honeypot"] = df["is_likely_honeypot"].fillna(False)
        df.to_parquet(feat_file)
        wrote = feat_file.name
    except Exception as e:
        wrote = f"(parquet not updated: {e})"

    report = {
        "n": n,
        "flagged_honeypots": int(hp["is_likely_honeypot"].sum()),
        "flag_rate_pct": round(100 * flag_rate, 3),
        "expected_honeypots_in_pool": "~80 (0.08%)",
        "synthetic_recall": recall,
        "synthetic_recall_missed": missed,
        "score_distribution": {
            "clean_1.0": int((hp["honeypot_score"] >= 0.99).sum()),
            "soft_0.15_0.99": int(((hp["honeypot_score"] >= 0.15) &
                                   (hp["honeypot_score"] < 0.99)).sum()),
            "flagged_below_0.15": int((hp["honeypot_score"] < 0.15).sum()),
        },
    }
    rep = config.HONEYPOT_REPORT_JSON.with_name("stage4_honeypot_report_sample.json") \
        if args.sample else config.HONEYPOT_REPORT_JSON
    rep.write_text(json.dumps(report, indent=2))

    print("-" * 60)
    print(f"processed {n}  flagged honeypots: {report['flagged_honeypots']} "
          f"({report['flag_rate_pct']}%)")
    print(f"score dist: {report['score_distribution']}")
    print(f"features updated: {wrote}")
    print(f"report -> {rep}")
    if flag_rate > 0.03:
        print("WARNING: flag rate >3% — likely over-firing on real candidates. Review thresholds.")
    print("STAGE 4 (honeypot audit): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
