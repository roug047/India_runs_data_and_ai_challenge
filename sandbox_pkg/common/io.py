"""
common/io.py
Candidate loading utilities shared by every stage.

Handles the two on-disk formats present in this challenge:
  - candidates.jsonl       -> one JSON object per line (the real 100K pool)
  - sample_candidates.json -> a single JSON array (the 50-row sample)

Auto-detects by first non-whitespace char. Also supports .gz transparently so
you can store the big file compressed if you like.
"""
from __future__ import annotations
import gzip
import json
from pathlib import Path
from typing import Iterator, List, Dict, Any


def _open_maybe_gzip(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def iter_candidates(path: Path) -> Iterator[Dict[str, Any]]:
    """
    Stream candidates one at a time. Memory-friendly for the 100K file.
    Auto-detects JSON-array vs JSONL.
    """
    with _open_maybe_gzip(path) as f:
        # Peek first meaningful char to decide format.
        pos = f.tell()
        first = ""
        while True:
            ch = f.read(1)
            if not ch:
                break
            if not ch.isspace():
                first = ch
                break
        f.seek(pos)

        if first == "[":
            # JSON array — must read whole thing (sample file is tiny, this is fine).
            data = json.load(f)
            for obj in data:
                yield obj
        else:
            # JSONL
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def load_candidates(path: Path) -> List[Dict[str, Any]]:
    """Load all candidates into a list."""
    return list(iter_candidates(path))

def read_docx_text(path: Path) -> str:
    """
    Extract plain text from a .docx using only the standard library (zipfile + regex).
    No python-docx dependency. Paragraph breaks are preserved; runs are concatenated.
    Used to parse the organizers' job_description.docx (the source of truth).
    """
    import re
    import zipfile
 
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    # Paragraph close -> newline so structure survives.
    xml = re.sub(r"</w:p>", "\n", xml)
    # Tab elements -> spaces.
    xml = re.sub(r"<w:tab[^>]*/>", " ", xml)
    # Strip all remaining tags.
    text = re.sub(r"<[^>]+>", "", xml)
    # Unescape the few XML entities Word emits.
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&apos;", "'")]:
        text = text.replace(a, b)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text