"""
stage0/03_build_golden_set.py
Convert the hand-filled worksheet into the frozen artifacts/golden_set.json.

This is the LOAD-BEARING artifact (v6.1). Everything downstream (composite calibration
in Stage 5, blend-alpha in Stage 6) validates against it. This script enforces that the
anchor is large enough and label-balanced enough to be a useful validator.

Run AFTER you fill the 'label' column in golden_set_worksheet.csv:
  python stage0/03_build_golden_set.py
  python stage0/03_build_golden_set.py --min 50   # override minimum size
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402

VALID_LABELS = {0, 1, 2, 3}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=50, help="Minimum labeled candidates required.")
    ap.add_argument("--allow-partial", action="store_true",
                    help="Write whatever is labeled even if below --min (NOT for final run).")
    args = ap.parse_args()

    if not config.ANCHOR_WORKSHEET_CSV.exists():
        print(f"FATAL: {config.ANCHOR_WORKSHEET_CSV} not found. Run 02_select_anchor.py first.")
        return 1

    golden: dict[str, int] = {}
    skipped_blank = 0
    bad_rows = []
    with open(config.ANCHOR_WORKSHEET_CSV, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            cid = (row.get("candidate_id") or "").strip()
            raw = (row.get("label") or "").strip()
            if not cid:
                continue
            if raw == "":
                skipped_blank += 1
                continue
            try:
                lbl = int(float(raw))
            except ValueError:
                bad_rows.append((i, cid, raw))
                continue
            if lbl not in VALID_LABELS:
                bad_rows.append((i, cid, raw))
                continue
            golden[cid] = lbl

    if bad_rows:
        print("FATAL: invalid labels (must be 0/1/2/3):")
        for ln, cid, raw in bad_rows[:20]:
            print(f"  line {ln}: {cid} -> '{raw}'")
        return 1

    n = len(golden)
    dist = Counter(golden.values())
    print(f"Labeled: {n}   (blank rows skipped: {skipped_blank})")
    print(f"Label distribution: " + ", ".join(f"{k}:{dist.get(k,0)}" for k in [3, 2, 1, 0]))

    # ---- Quality gates: the anchor must be able to discriminate ----
    problems = []
    if n < args.min and not args.allow_partial:
        problems.append(f"only {n} labeled; need >= {args.min} (or pass --allow-partial for a dry run)")
    if dist.get(3, 0) < 5:
        problems.append(f"only {dist.get(3,0)} STRONG(3) labels; need >=5 to anchor the top")
    if dist.get(0, 0) < 5:
        problems.append(f"only {dist.get(0,0)} NOT-FIT(0) labels; need >=5 to anchor the bottom")
    if len(dist) < 3:
        problems.append("labels span <3 distinct values; anchor can't calibrate a gradient")

    if problems and not args.allow_partial:
        print("FAIL — anchor not yet usable:")
        for p in problems:
            print(f"  - {p}")
        print("Keep labeling, then re-run.")
        return 1

    config.GOLDEN_SET_JSON.write_text(json.dumps(golden, indent=2, sort_keys=True))
    print("-" * 60)
    print(f"FROZEN golden set -> {config.GOLDEN_SET_JSON}  ({n} candidates)")
    if problems:
        print("WARNING (partial mode): " + "; ".join(problems))
    print("This is the validator for Stage 5 (composite) and Stage 6 (blend alpha).")
    print("Do NOT re-select the anchor using any tuned score after this point.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
