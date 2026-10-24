"""Re-extract one PDF into extracted-fixed/<book>/ with corrected text flags.

Same output format as extract_pdfs.py (pages/page-NNNN.json, metadata.json,
document.md), but uses TEXT_INHIBIT_SPACES so that letter-spaced text (e.g.
the Helvetica-Oblique letters in "Como lidar com mulheres") is not split into
fragments like "co n q u ist ad a". The original extracted/ directory is
never modified; point the book's config "extracted_dir" at the new folder.

Usage:
  python tools/extract_book.py "<PDF file name in portuguese-original-pdf/>"
"""

import json
import sys
from pathlib import Path

import pymupdf

from common import ROOT, fail, write_text_atomic

INPUT_DIR = ROOT / "portuguese-original-pdf"
OUTPUT_DIR = ROOT / "extracted-fixed"
FLAGS = pymupdf.TEXTFLAGS_DICT | pymupdf.TEXT_INHIBIT_SPACES


def extract(pdf_path: Path) -> Path:
    book_dir = OUTPUT_DIR / pdf_path.stem
    pages_dir = book_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    metadata = {"source_file": pdf_path.name, "extraction_flags": "TEXTFLAGS_DICT|TEXT_INHIBIT_SPACES",
                "page_count": 0, "metadata": {}, "toc": [], "fonts": [], "pages": []}
    markdown = []
    with pymupdf.open(pdf_path) as doc:
        metadata["page_count"] = len(doc)
        metadata["metadata"] = doc.metadata or {}
        metadata["toc"] = doc.get_toc()
        for page in doc:
            number = page.number + 1
            blocks = []
            md = [f"<!-- Original PDF page: {number} -->", f"# Page {number}", ""]
            for block in page.get_text("dict", flags=FLAGS, sort=True)["blocks"]:
                if block.get("type") != 0:
                    continue
                spans, lines = [], []
                for line in block.get("lines", []):
                    text = "".join(s.get("text", "") for s in line.get("spans", []))
                    if text:
                        lines.append(text)
                    for s in line.get("spans", []):
                        if s.get("text", "").strip():
                            spans.append({k: s.get(k) for k in
                                          ("text", "font", "size", "flags", "color", "bbox", "origin")})
                text = "\n".join(lines).strip()
                if text:
                    blocks.append({"type": "text", "bbox": block.get("bbox"), "text": text, "spans": spans})
                    md += [text, ""]
            page_json = {"page_number": number, "width": page.rect.width, "height": page.rect.height,
                         "rotation": page.rotation, "blocks": blocks}
            (pages_dir / f"page-{number:04d}.json").write_text(
                json.dumps(page_json, ensure_ascii=False, indent=2), encoding="utf-8")
            metadata["pages"].append({"page_number": number, "width": page.rect.width,
                                      "height": page.rect.height, "rotation": page.rotation,
                                      "block_count": len(blocks)})
            markdown.append("\n".join(md))
    write_text_atomic(book_dir / "document.md", "\n\n".join(markdown))
    write_text_atomic(book_dir / "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    return book_dir


def main() -> None:
    if len(sys.argv) != 2:
        fail(__doc__)
    pdf = INPUT_DIR / sys.argv[1]
    if not pdf.exists():
        fail(f"PDF not found: {pdf}")
    print(f"Extracted to {extract(pdf).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
