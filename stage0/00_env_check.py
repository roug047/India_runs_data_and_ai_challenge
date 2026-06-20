"""
stage0/00_env_check.py
Verify the precompute environment and required inputs before anything runs.

GPU is FINE here — Stage 0 is precompute. Only rank.py (Stage 7) is CPU-only/no-net/<=5min.
Run:  python stage0/00_env_check.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import config  # noqa: E402


def main() -> int:
    print("=" * 60)
    print("STAGE 0 — ENVIRONMENT CHECK")
    print("=" * 60)
    print(f"Python: {sys.version.split()[0]}")

    # RAM (psutil optional — don't hard-fail if missing)
    try:
        import psutil
        gb = psutil.virtual_memory().total / 1e9
        print(f"RAM: {gb:.1f} GB", "OK" if gb >= 14 else "WARNING: <14GB")
    except ImportError:
        print("RAM: psutil not installed (optional)")

    # Core libs the pipeline needs (import-check only; install separately).
    needed = ["numpy", "pandas", "sklearn", "scipy"]
    optional = ["pyarrow", "lightgbm", "sentence_transformers", "rank_bm25", "llama_cpp", "tqdm"]
    missing_core = []
    for m in needed:
        try:
            __import__(m)
            print(f"  [core] {m}: ok")
        except ImportError:
            missing_core.append(m)
            print(f"  [core] {m}: MISSING")
    for m in optional:
        try:
            __import__(m)
            print(f"  [opt ] {m}: ok")
        except ImportError:
            print(f"  [opt ] {m}: not installed (needed later, not for Stage 0)")

    # Required input files.
    print("-" * 60)
    inputs = {
        "candidates.jsonl": config.CANDIDATES_JSONL,
        "sample_candidates.json": config.SAMPLE_CANDIDATES,
        "candidate_schema.json": config.CANDIDATE_SCHEMA,
        "job_description.md": config.JD_MD,
    }
    missing_inputs = []
    for name, p in inputs.items():
        ok = Path(p).exists()
        size = (Path(p).stat().st_size / 1e6) if ok else 0
        print(f"  {name}: {'ok' if ok else 'MISSING'} ({size:.1f} MB)" if ok else f"  {name}: MISSING")
        if not ok and name != "candidates.jsonl":
            # candidates.jsonl may be intentionally absent on a dev box; warn only.
            missing_inputs.append(name)
    if not Path(config.CANDIDATES_JSONL).exists():
        print("  NOTE: candidates.jsonl absent — Stage 0 will fall back to the sample for a dry run.")

    config.ensure_artifacts()
    print(f"  artifacts dir: {config.ARTIFACTS} (ready)")

    print("=" * 60)
    if missing_core:
        print(f"FAIL: install core libs: pip install {' '.join(missing_core)}")
        return 1
    if missing_inputs:
        print(f"FAIL: missing required inputs: {missing_inputs}")
        return 1
    print("PASS: environment ready for Stage 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
