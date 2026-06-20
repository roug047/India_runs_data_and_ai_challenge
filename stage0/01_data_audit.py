"""
stage0/01_data_audit.py
Data integrity + empirically-derived reference date + distribution report + naive baseline.

KEY FIX (v6.1 #1): REFERENCE_DATE is NOT hardcoded. It is derived as the max
last_active_date across the pool (the latest moment the data could have been
snapshotted) and frozen to artifacts/reference_date.json. Every later stage reads
it via common.config.get_reference_date(), so all recency features agree.

Run:  python stage0/01_data_audit.py
      python stage0/01_data_audit.py --sample      # dry-run on the 50-row sample
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config              # noqa: E402
from common.io import iter_candidates  # noqa: E402


def derive_reference_date(last_active_dates: list[str]) -> date:
    """
    Empirical reference 'now' = the latest last_active_date in the pool.
    Rationale: the dataset is a snapshot; no activity can post-date the snapshot,
    so the max observed activity date is the tightest lower bound on 'now' and the
    correct zero-point for recency features. Hardcoding a guess (the old 2026-06-06)
    biased every recency feature — the sample already contained 2026-05-25.
    """
    valid = [d for d in last_active_dates if d]
    return max(date.fromisoformat(d) for d in valid)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true",
                    help="Run on sample_candidates.json instead of the 100K pool.")
    args = ap.parse_args()

    config.ensure_artifacts()
    src = config.SAMPLE_CANDIDATES if args.sample else config.CANDIDATES_JSONL
    if not Path(src).exists():
        if Path(config.SAMPLE_CANDIDATES).exists():
            print(f"WARNING: {src} missing; falling back to sample for a dry run.")
            src = config.SAMPLE_CANDIDATES
            args.sample = True
        else:
            print(f"FATAL: no candidate data found at {src}")
            return 1

    print(f"Reading candidates from: {src}")

    # Single streaming pass — memory-safe for the 400MB file.
    n = 0
    ids = set()
    dup_ids = 0
    yoe_vals: list[float] = []
    countries: Counter = Counter()
    company_sizes: Counter = Counter()
    open_to_work = 0
    willing_relocate = 0
    last_active: list[str] = []
    signup: list[str] = []
    career_end_dates: list[str] = []
    n_with_skill_duration = 0
    n_total_skills = 0
    notice_vals: list[int] = []
    github_linked = 0
    offer_history = 0
    missing_required = 0

    REQUIRED_TOP = {"candidate_id", "profile", "career_history",
                    "education", "skills", "redrob_signals"}

    for c in iter_candidates(Path(src)):
        n += 1
        if not REQUIRED_TOP.issubset(c.keys()):
            missing_required += 1
            continue
        cid = c["candidate_id"]
        if cid in ids:
            dup_ids += 1
        ids.add(cid)

        prof = c["profile"]
        yoe_vals.append(prof.get("years_of_experience", 0.0))
        countries[prof.get("country", "?")] += 1
        company_sizes[prof.get("current_company_size", "?")] += 1

        sig = c["redrob_signals"]
        open_to_work += int(bool(sig.get("open_to_work_flag")))
        willing_relocate += int(bool(sig.get("willing_to_relocate")))
        if sig.get("last_active_date"):
            last_active.append(sig["last_active_date"])
        if sig.get("signup_date"):
            signup.append(sig["signup_date"])
        notice_vals.append(sig.get("notice_period_days", 0))
        if sig.get("github_activity_score", -1) != -1:
            github_linked += 1
        if sig.get("offer_acceptance_rate", -1) != -1:
            offer_history += 1

        for r in c.get("career_history", []):
            if r.get("end_date"):
                career_end_dates.append(r["end_date"])
        for s in c.get("skills", []):
            n_total_skills += 1
            if "duration_months" in s:
                n_with_skill_duration += 1

    # ---- Integrity assertions (soft for sample, hard for full pool) ----
    print("=" * 60)
    print(f"Total records:        {n}")
    print(f"Unique candidate_ids: {len(ids)}")
    print(f"Duplicate ids:        {dup_ids}")
    print(f"Missing required key: {missing_required}")
    if not args.sample:
        assert n == 100_000, f"Expected 100000 candidates, got {n}"
        assert dup_ids == 0, f"{dup_ids} duplicate candidate_ids!"
        assert missing_required == 0, f"{missing_required} records missing required keys!"

    # ---- Reference date (THE FIX) ----
    ref = derive_reference_date(last_active)
    config.REFERENCE_DATE_JSON.write_text(json.dumps({
        "reference_date": ref.isoformat(),
        "method": "max(last_active_date) across pool",
        "source": "sample" if args.sample else "full_pool",
        "max_last_active": max(last_active) if last_active else None,
        "max_career_end_date": max(career_end_dates) if career_end_dates else None,
    }, indent=2))
    print("-" * 60)
    print(f"REFERENCE_DATE (derived): {ref.isoformat()}   <-- frozen to artifacts/")
    print(f"  max last_active_date:   {max(last_active) if last_active else None}")
    print(f"  max career end_date:    {max(career_end_dates) if career_end_dates else None}")

    # ---- Distribution report ----
    yoe_sorted = sorted(yoe_vals)
    def pct(p): return yoe_sorted[min(len(yoe_sorted) - 1, int(p * len(yoe_sorted)))]
    report = {
        "n": n,
        "unique_ids": len(ids),
        "reference_date": ref.isoformat(),
        "yoe": {
            "min": round(min(yoe_vals), 1), "p25": round(pct(0.25), 1),
            "median": round(pct(0.50), 1), "p75": round(pct(0.75), 1),
            "max": round(max(yoe_vals), 1),
            "in_5_9_band_pct": round(100 * sum(1 for y in yoe_vals if 5 <= y <= 9) / n, 1),
        },
        "countries_top": countries.most_common(8),
        "india_pct": round(100 * countries.get("India", 0) / n, 1),
        "company_size_top": company_sizes.most_common(),
        "open_to_work_pct": round(100 * open_to_work / n, 1),
        "willing_to_relocate_pct": round(100 * willing_relocate / n, 1),
        "github_linked_pct": round(100 * github_linked / n, 1),
        "has_offer_history_pct": round(100 * offer_history / n, 1),
        "skills_with_duration_pct": round(100 * n_with_skill_duration / max(n_total_skills, 1), 1),
        "notice_days": {
            "p25": sorted(notice_vals)[len(notice_vals)//4],
            "median": sorted(notice_vals)[len(notice_vals)//2],
            "p75": sorted(notice_vals)[3*len(notice_vals)//4],
        },
    }
    config.DATA_REPORT_JSON.write_text(json.dumps(report, indent=2))
    print("-" * 60)
    print(f"YOE: median={report['yoe']['median']}  "
          f"5-9 band={report['yoe']['in_5_9_band_pct']}%")
    print(f"India={report['india_pct']}%  open_to_work={report['open_to_work_pct']}%  "
          f"willing_relocate={report['willing_to_relocate_pct']}%")
    print(f"countries: {report['countries_top'][:5]}")
    print(f"report -> {config.DATA_REPORT_JSON}")

    # ---- Naive baseline (defensibility anchor) ----
    # Reload ids+yoe cheaply for the baseline (small list of tuples already in memory).
    naive_pairs = sorted(
        ((cid, abs(y - 7.0)) for cid, y in zip(  # note: ids set unordered; rebuild below
            [c["candidate_id"] for c in iter_candidates(Path(src))],
            [c["profile"]["years_of_experience"] for c in iter_candidates(Path(src))],
        )),
        key=lambda t: t[1]
    )
    naive_top100 = [cid for cid, _ in naive_pairs[:100]]
    config.NAIVE_BASELINE_JSON.write_text(json.dumps(naive_top100, indent=2))
    print(f"naive baseline (YOE≈7) top100 -> {config.NAIVE_BASELINE_JSON}")

    print("=" * 60)
    print("STAGE 0 data audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
