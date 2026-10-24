"""Shared helpers: paths, config loading, atomic writes, segment markers."""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

# Windows consoles default to a legacy code page; the books are full of accents.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config" / "books"
GLOSSARY_FILE = ROOT / "glossary" / "glossary.json"
WORK_DIR = ROOT / "work"
TRANSLATIONS_DIR = ROOT / "translations"
REVIEW_DIR = ROOT / "review"

# Marker line that opens every segment in *.pt.md / *.en.md files:
#   <!-- seg 09-0002 paragraph h=1a2b3c4d -->
MARKER_RE = re.compile(
    r"^<!-- seg (?P<id>\d{2}-\d{4}) (?P<type>[a-z_]+)"
    r"(?: n=(?P<n>\d+))? h=(?P<hash>[0-9a-f]{8}) -->\s*$"
)
QUERY_RE = re.compile(r"<!--\s*QUERY:\s*(.*?)\s*-->", re.S)
TN_RE = re.compile(r"<!--\s*TN:\s*(.*?)\s*-->", re.S)
# Intentionally untranslated text (e.g. a bibliographic reference to the original).
KEEP_RE = re.compile(r"<!--\s*KEEP:\s*(.*?)\s*-->", re.S)


class PipelineError(Exception):
    """Expected failure with a message meant for the user."""


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PipelineError(f"File not found: {path}")
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Invalid JSON in {path}: {exc}")


def write_text_atomic(path: Path, text: str) -> None:
    """Write via a temp file + rename so an interruption never leaves a
    half-written file behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def write_json_atomic(path: Path, data) -> None:
    write_text_atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_book_config(slug: str) -> dict:
    path = CONFIG_DIR / f"{slug}.json"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in CONFIG_DIR.glob("*.json")))
        raise PipelineError(f"No config for book '{slug}'. Available: {available}")
    cfg = load_json(path)
    cfg["slug"] = slug
    extracted = ROOT / cfg["extracted_dir"]
    if not (extracted / "pages").is_dir():
        raise PipelineError(f"Extracted pages not found: {extracted / 'pages'}")
    cfg["_extracted_path"] = extracted
    return cfg


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def marker(seg: dict) -> str:
    n = f" n={seg['fn']}" if seg.get("fn") is not None else ""
    return f"<!-- seg {seg['id']} {seg['type']}{n} h={seg['hash']} -->"


def parse_marked_md(path: Path) -> list[dict]:
    """Parse a *.pt.md / *.en.md file into segments, in file order.

    Text before the first marker (file header) is ignored. QUERY and TN
    comments are pulled out of the segment text into separate lists."""
    segments = []
    current = None
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = MARKER_RE.match(line)
        if m:
            current = {
                "id": m["id"],
                "type": m["type"],
                "fn": int(m["n"]) if m["n"] else None,
                "hash": m["hash"],
                "line": line_no,
                "raw": [],
            }
            segments.append(current)
        elif current is not None:
            current["raw"].append(line)
    for seg in segments:
        raw = "\n".join(seg.pop("raw"))
        seg["queries"] = [q.strip() for q in QUERY_RE.findall(raw)]
        seg["notes"] = [t.strip() for t in TN_RE.findall(raw)]
        seg["keep"] = [k.strip() for k in KEEP_RE.findall(raw)]
        raw = KEEP_RE.sub("", TN_RE.sub("", QUERY_RE.sub("", raw)))
        seg["text"] = raw.strip()
    return segments


def chapter_ids(slug: str) -> list[str]:
    index = WORK_DIR / slug / "book.json"
    if not index.exists():
        raise PipelineError(f"Book not segmented yet. Run: python tools/segment.py {slug}")
    return [c["id"] for c in load_json(index)["chapters"]]


def strip_markup(text: str) -> str:
    """Plain text: drop <i>/<b> tags, turn [^n] refs into n."""
    text = re.sub(r"</?[ib]>", "", text)
    return re.sub(r"\[\^(\d+)\]", r"\1", text)
