"""
stage2/20_build_features.py
Master runner: stream all candidates, compute every feature, write features parquet.

GPU not used. Pure pandas/Python. Streams the 100K file so memory stays low.

Run:  python stage2/20_build_features.py
      python stage2/20_build_features.py --sample      # dry-run on the 50-row sample
Output: artifacts/features_100k.parquet, artifacts/feature_list.json,
        artifacts/stage2_feature_report.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402
from stage2 import features_core as fc  # noqa: E402
from stage2.disqualifiers import compute_disqualifiers  # noqa: E402


def build_one(c: dict, jd_config: dict, groups: dict, ref) -> dict:
    row: dict = {"candidate_id": c["candidate_id"]}

    # order matters: some features consume earlier ones
    row.update(fc.experience_fit(c, jd_config))
    row.update(fc.title_signal(c))
    row.update(fc.education_features(c))
    row.update(fc.career_trajectory(c, jd_config))
    row.update(fc.production_evidence(c, groups))
    row.update(fc.requirement_coverage(c, jd_config, groups))
    row.update(fc.skill_credibility(c))
    row.update(fc.behavioral_features(c, ref))
    row.update(fc.logistics_features(c, jd_config))

    # disqualifiers need several of the above already in `row`
    row.update(compute_disqualifiers(c, jd_config, groups, row, ref))
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args()
    config.ensure_artifacts()

    # dependencies from earlier stages
    for need in (config.JD_CONFIG_JSON, config.SKILL_GROUPS_JSON):
        if not need.exists():
            print(f"FATAL: missing {need.name} — run Stage 1 first.")
            return 1
    jd_config = json.loads(config.JD_CONFIG_JSON.read_text())
    groups = json.loads(config.SKILL_GROUPS_JSON.read_text())["skill_groups"]
    ref = config.get_reference_date()
    print(f"reference_date = {ref}  (frozen from Stage 0)")

    src = config.SAMPLE_CANDIDATES if args.sample else config.CANDIDATES_JSONL
    if not Path(src).exists():
        print(f"WARNING: {src} missing; using sample.")
        src = config.SAMPLE_CANDIDATES

    try:
        import pandas as pd
    except ImportError:
        print("FATAL: pandas required.  pip install pandas pyarrow")
        return 1

    rows = []
    n = 0
    for c in iter_candidates(Path(src)):
        rows.append(build_one(c, jd_config, groups, ref))
        n += 1
        if n % 10000 == 0:
            print(f"  ...{n} processed")
    print(f"processed {n} candidates")

    df = pd.DataFrame(rows).set_index("candidate_id")
    # ensure deterministic column order
    df = df.reindex(sorted(df.columns), axis=1)

    if not args.sample:
        try:
            df.to_parquet(config.FEATURES_PARQUET)
            out = config.FEATURES_PARQUET
        except Exception as e:
            print(f"parquet failed ({e}); writing CSV fallback.")
            out = config.FEATURES_PARQUET.with_suffix(".csv")
            df.to_csv(out)
    else:
        out = config.FEATURES_PARQUET.with_name("features_sample.parquet")
        try:
            df.to_parquet(out)
        except Exception:
            out = out.with_suffix(".csv")
            df.to_csv(out)

    feature_list = [col for col in df.columns if df[col].dtype.kind in "biufc"]
    config.FEATURE_LIST_JSON.write_text(json.dumps(feature_list, indent=2))

    # quick report
    report = {
        "n": int(n),
        "n_features": len(df.columns),
        "numeric_features": len(feature_list),
        "disqualifier_hit_rate": round(float(df["disqualifier_hit"].mean()), 3),
        "means": {col: round(float(df[col].mean()), 3)
                  for col in ["weighted_hard_req_coverage", "production_evidence_score",
                              "yoe_fit", "location_score", "availability_score",
                              "keyword_evidence_gap"] if col in df.columns},
        "disqualifier_breakdown": {
            k: int(df[k].sum()) for k in
            ["pure_research_no_prod", "pure_consulting_career", "cv_speech_robotics_only",
             "langchain_only_under_12mo", "no_code_18mo", "closed_source_no_validation",
             "title_chaser"] if k in df.columns},
    }
    config.FEATURE_REPORT_JSON.write_text(json.dumps(report, indent=2))

    print("-" * 60)
    print(f"features -> {out}")
    print(f"rows={n}  columns={len(df.columns)}  numeric={len(feature_list)}")
    print(f"disqualifier hit rate: {report['disqualifier_hit_rate']}")
    print(f"DQ breakdown: {report['disqualifier_breakdown']}")
    print(f"key means: {report['means']}")
    print("STAGE 2 (build features): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
