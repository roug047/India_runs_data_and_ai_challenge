"""
stage7/71_make_audit_template.py
Create an empty audit_log.json (if absent) so you can fill in overrides.

The audit log is your documented, reproducible human-in-the-loop override. rank.py reads it.
It is NOT manual CSV editing (which the spec forbids) — it's a version-controlled decision
table applied deterministically.

Schema:
  {
    "CAND_0012345": {"action": "remove", "reason": "honeypot: 11yr at 3yr-old company"},
    "CAND_0067890": {"action": "demote", "to_rank": 35, "reason": "CV-only, weak NLP/IR"}
  }

Run:  python stage7/71_make_audit_template.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402


def main() -> int:
    config.ensure_artifacts()
    if config.AUDIT_LOG_JSON.exists():
        existing = json.loads(config.AUDIT_LOG_JSON.read_text())
        print(f"audit_log.json already exists with {len(existing)} entries. Leaving it.")
        return 0
    config.AUDIT_LOG_JSON.write_text(json.dumps({}, indent=2))
    print(f"created empty {config.AUDIT_LOG_JSON}")
    print("Edit it to add remove/demote decisions from your top-40 review, e.g.:")
    print(json.dumps({
        "CAND_0000000": {"action": "remove", "reason": "example: honeypot"},
        "CAND_0000001": {"action": "demote", "to_rank": 35, "reason": "example: weak fit"},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
