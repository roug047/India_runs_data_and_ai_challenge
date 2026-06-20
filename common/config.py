"""
common/config.py
Single source of truth for paths and the (empirically-derived) reference date.

Architecture V6 — shared across all stages. Importing this from any stage script
guarantees every stage reads/writes the same artifact locations and uses the SAME
reference date (derived once in Stage 0, then frozen to artifacts/reference_date.json).

NOTHING here computes features or rankings. Paths + constants only.
"""
from __future__ import annotations
import json
import os
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-root resolution: this file lives at <repo>/common/config.py
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
print("REPO_ROOT =", REPO_ROOT)

# Input data (provided by organizers) — live at repo root in your layout
CANDIDATES_JSONL = REPO_ROOT / "candidates.jsonl"          # 100K, line-delimited
SAMPLE_CANDIDATES = REPO_ROOT / "sample_candidates.json"   # 50, JSON array
CANDIDATE_SCHEMA = REPO_ROOT / "candidate_schema.json"
JD_MD = REPO_ROOT / "job_description.md"
JD_DOCX = REPO_ROOT / "job_description.docx" 
SAMPLE_SUBMISSION = REPO_ROOT / "sample_submission.csv"

# Output artifacts (shared, git-ignored except the small human-owned ones)
ARTIFACTS = REPO_ROOT / "artifacts"

# Stage 0 outputs
REFERENCE_DATE_JSON = ARTIFACTS / "reference_date.json"
DATA_REPORT_JSON = ARTIFACTS / "stage0_data_report.json"
NAIVE_BASELINE_JSON = ARTIFACTS / "naive_baseline_top100.json"
ANCHOR_CANDIDATES_JSON = ARTIFACTS / "anchor_candidates.json"        # the 60 IDs to label
ANCHOR_WORKSHEET_CSV = ARTIFACTS / "golden_set_worksheet.csv"        # human fills this
GOLDEN_SET_JSON = ARTIFACTS / "golden_set.json"                      # final labels (human-owned)

# Stage 1 outputs
JD_CONFIG_JSON = ARTIFACTS / "jd_config.json"
SKILL_GROUPS_JSON = ARTIFACTS / "skill_groups.json"
JD_EMBEDDING_NPY = ARTIFACTS / "jd_embedding.npy"
IDEAL_EMBEDDING_NPY = ARTIFACTS / "ideal_embedding.npy"
JD_TEXT_CACHE = ARTIFACTS / "jd_text.txt"

# Fallback reference date ONLY used if Stage 0 hasn't been run yet.
# Real value is derived empirically in stage0 and written to REFERENCE_DATE_JSON.
_FALLBACK_REFERENCE_DATE = date(2026, 6, 6)


def get_reference_date() -> date:
    """
    Return the frozen, empirically-derived reference date.
    Stage 0 writes artifacts/reference_date.json; every later stage reads it here
    so recency-weighted features are consistent everywhere.
    """
    if REFERENCE_DATE_JSON.exists():
        d = json.loads(REFERENCE_DATE_JSON.read_text())["reference_date"]
        return date.fromisoformat(d)
    return _FALLBACK_REFERENCE_DATE


def ensure_artifacts() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)


# Random seed used wherever sampling happens, for reproducibility.
SEED = 42
