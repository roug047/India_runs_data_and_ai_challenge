"""
stage0/05_merge_golden.py
Rebuild golden_set.json from BOTH the original anchor worksheet and the disagreement worksheet.

Use this instead of 03_build_golden_set.py once you've labeled the disagreement candidates.
It reads both CSVs, validates labels, and writes the combined, frozen golden set.

Run:  python stage0/05_merge_golden.py
"""
from __future__ import annotations
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402

VALID = {0, 1, 2, 3}


def read_labels(path: Path) -> dict:
    labels = {}
    if not path.exists():
        return labels
    with open(path, newline="", encoding="utf-8") as f:
        for ln, row in enumerate(csv.DictReader(f), start=2):
            cid = (row.get("candidate_id") or "").strip()
            raw = (row.get("label") or "").strip()
            if not cid or raw == "":
                continue
            try:
                v = int(float(raw))
            except ValueError:
                print(f"  bad label at {path.name} line {ln}: {cid} -> '{raw}'")
                continue
            if v in VALID:
                labels[cid] = v
    return labels


def main() -> int:
    config.ensure_artifacts()
    a = read_labels(config.ANCHOR_WORKSHEET_CSV)
    d = read_labels(config.ARTIFACTS / "disagreement_worksheet.csv")

    merged = dict(a)
    overlaps = set(a) & set(d)
    merged.update(d)   # disagreement labels win on conflict (you looked at them more recently)

    dist = dict(sorted(Counter(merged.values()).items()))
    print(f"original anchor labeled: {len(a)}")
    print(f"disagreement labeled:    {len(d)}")
    print(f"overlap (disagreement wins): {len(overlaps)}")
    print(f"combined golden set: {len(merged)}  distribution: {dist}")

    if dist.get(3, 0) < 5 or dist.get(0, 0) < 5 or len(dist) < 3:
        print("WARNING: anchor still thin at an extreme — but writing anyway.")

    config.GOLDEN_SET_JSON.write_text(json.dumps(merged, indent=2, sort_keys=True))
    print(f"FROZEN -> {config.GOLDEN_SET_JSON}")
    print("Next: re-run stage5/51_calibrate.py to re-tune on the bigger anchor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
