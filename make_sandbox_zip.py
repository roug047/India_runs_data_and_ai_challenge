"""
make_sandbox_zip.py
Builds repo.zip for the Colab sandbox with CORRECT forward-slash paths that work on Linux.
PowerShell's Compress-Archive writes Windows backslash paths that break on Colab — this avoids that.

Run from the repo root:  python make_sandbox_zip.py
Produces: repo.zip  (only what rank.py needs; no big .npy / candidate_texts / models)
"""
import os
import zipfile

# Exactly what the ranking step needs (verified by the import trace).
INCLUDE_FILES = [
    "rank.py",
    "requirements.txt",
    "sample_candidates.json",
]
INCLUDE_DIRS = [
    "common",
    "stage5",
    "stage7",
]
# Allow-list of artifacts rank.py reads (nothing else from artifacts/).
INCLUDE_ARTIFACTS = [
    "features_100k.parquet",
    "ranker_rule.txt",
    "ranker_llm.txt",
    "blend.json",
    "lgb_features.json",
    "composite_weights.json",
    "engine_choice.json",
    "audit_log.json",
]

SKIP_EXT = {".npy", ".pyc"}
SKIP_DIR_NAMES = {"__pycache__"}


def add_file(zf, src, arc):
    # arc uses forward slashes always
    arc = arc.replace("\\", "/")
    zf.write(src, arc)


def main():
    out = "repo.zip"
    if os.path.exists(out):
        os.remove(out)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        # top-level files
        for f in INCLUDE_FILES:
            if os.path.isfile(f):
                add_file(zf, f, f)
            else:
                print("WARN missing file:", f)

        # code directories (recursive, skipping pycache and compiled files)
        for d in INCLUDE_DIRS:
            for root, dirs, files in os.walk(d):
                dirs[:] = [x for x in dirs if x not in SKIP_DIR_NAMES]
                for fn in files:
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in SKIP_EXT:
                        continue
                    full = os.path.join(root, fn)
                    add_file(zf, full, full)

        # allow-listed artifacts only
        for name in INCLUDE_ARTIFACTS:
            src = os.path.join("artifacts", name)
            if os.path.isfile(src):
                add_file(zf, src, "artifacts/" + name)
            else:
                print("WARN missing artifact:", src)

    size_mb = os.path.getsize(out) / (1024 * 1024)
    print(f"\nwrote {out}  ({size_mb:.1f} MB)")
    # list contents for verification
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    print(f"{len(names)} entries. sample paths:")
    for n in names[:12]:
        print("  ", n)
    # sanity: confirm forward slashes and key files present
    assert any(n == "rank.py" for n in names), "rank.py missing!"
    assert any(n == "artifacts/features_100k.parquet" for n in names), "parquet missing!"
    assert all("\\" not in n for n in names), "backslash in a path — would break on Linux!"
    print("\nOK: forward-slash paths, rank.py + parquet present.")


if __name__ == "__main__":
    main()
