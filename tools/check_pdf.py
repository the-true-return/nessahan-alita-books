"""Quality checks for a generated PDF (output/<slug>/<slug>-en.pdf).

Checks:
  - completeness: every translated segment appears in the PDF, in order
    (body text and footnotes are checked against separate text streams);
  - footnotes: each note is on the same page as its reference;
  - fonts: all embedded;
  - layout: no text outside the margins, no overlapping lines, no empty
    pages, no heading stranded at the bottom of a page;
  - previews: PNG of every page in output/<slug>/preview/ for visual review.

Writes output/<slug>/pdf-check.md. Exit code 1 if there are errors. If there
are none, publishes the PDF to books/ as
"Nessahan Alita - <English title> (<edition> Edition).pdf".

Usage:
  python tools/check_pdf.py <slug>
"""

import argparse
import os
import re
import shutil
import sys

import pymupdf

from common import (
    ROOT, TRANSLATIONS_DIR, WORK_DIR, PipelineError, chapter_ids, fail,
    load_book_config, load_json, parse_marked_md, strip_markup, write_text_atomic,
)

OUTPUT_DIR = ROOT / "output"
BOOKS_DIR = ROOT / "books"


def norm(text: str) -> str:
    """Letters and digits only: immune to hyphenation, spacing and quotes."""
    return re.sub(r"[^0-9a-z]", "", text.lower())


def published_name(cfg: dict) -> str:
    """Final file name, in the same pattern as the Portuguese originals."""
    return f"Nessahan Alita - {cfg['title_en']} ({cfg['edition']} Edition).pdf"


def publish(cfg: dict, pdf_path):
    """Copy a PDF that passed every check to books/ (final PDFs only)."""
    BOOKS_DIR.mkdir(exist_ok=True)
    target = BOOKS_DIR / published_name(cfg)
    tmp = target.with_name(target.name + ".tmp")
    shutil.copyfile(pdf_path, tmp)
    os.replace(tmp, target)
    return target


def check(slug: str) -> bool:
    cfg = load_book_config(slug)
    metrics = load_json(WORK_DIR / slug / "book.json")["metrics"]
    pdf_path = OUTPUT_DIR / slug / f"{slug}-en.pdf"
    if not pdf_path.exists():
        raise PipelineError(f"PDF not found: {pdf_path}. Run tools/build_pdf.py {slug}")
    doc = pymupdf.open(pdf_path)
    errors, warnings = [], []
    body_size = metrics["body_size"]
    fn_size = cfg["pdf"]["footnote_size_pt"]

    # ---- text streams per page, classified by line (a line's main size
    # decides: superscript note numbers stay with the line they belong to)
    pages = []
    for page in doc:
        h = page.rect.height
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [sp for sp in line["spans"] if sp["text"].strip()]
                if not spans:
                    continue
                text = "".join(sp["text"] for sp in spans)
                main = max(spans, key=lambda sp: len(sp["text"].strip()))
                is_footer = line["bbox"][1] > h - 60 and re.fullmatch(r"\s*\d+\s*", text)
                lines.append({"text": text, "size": main["size"], "flags": main["flags"],
                              "bbox": line["bbox"], "footer": bool(is_footer), "spans": spans})
        content = [ln for ln in lines if not ln["footer"]]
        pages.append({"page": page, "lines": content,
                      "spans": [sp for ln in content for sp in ln["spans"]]})

    def stream(pred):
        text, owners = [], []
        for i, p in enumerate(pages):
            for ln in p["lines"]:
                if pred(ln):
                    t = norm(ln["text"])
                    text.append(t)
                    owners.extend([i] * len(t))
        return "".join(text), owners

    big, big_pages = stream(lambda ln: ln["size"] >= body_size - 0.5)
    # Notes and small body text (quotations, letters) are kept apart: a small
    # paragraph that crosses a page break would otherwise be split by the notes.
    notes, notes_pages = stream(lambda ln: ln["size"] <= fn_size + 0.3)
    small, small_pages = stream(lambda ln: fn_size + 0.3 < ln["size"] < body_size - 0.5)
    everything, _ = stream(lambda ln: True)

    # ---- completeness, in order
    pos_big = 0
    small_streams = {"notes": [notes, notes_pages, 0], "small": [small, small_pages, 0]}
    seg_count = 0
    note_pages = {}
    for chapter in chapter_ids(slug):
        src = {s["id"]: s for s in load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")["segments"]}
        en = parse_marked_md(TRANSLATIONS_DIR / slug / f"{chapter}.en.md")
        for seg in en:
            style = src[seg["id"]]["style"]
            # Typst renders note references with the font's superscript
            # glyphs, which extract as ordinary digits: keep them in the body.
            target = norm(strip_markup(seg["text"]))
            if not target:
                continue  # punctuation-only artifacts are skipped by build_pdf.py
            seg_count += 1
            if chapter == "00":
                if target not in everything:
                    errors.append(f"{seg['id']}: text not found in the PDF")
                continue
            if seg["type"] == "footnote" or style["size"] < body_size - 0.5:
                order = ["notes", "small"] if seg["type"] == "footnote" else ["small", "notes"]
                found = -1
                for name in order:  # in order first, then anywhere in either stream
                    text, owners, pos = small_streams[name]
                    found = text.find(target, pos)
                    if found < 0:
                        found = text.find(target)
                    if found >= 0:
                        small_streams[name][2] = found + len(target)
                        break
                if found < 0:
                    errors.append(f"{seg['id']}: footnote text not found in the PDF")
                    continue
                if seg["type"] == "footnote":
                    note_pages[(chapter, seg["fn"])] = owners[found]
            else:
                found = big.find(target, pos_big)
                if found < 0:
                    where = "anywhere" if big.find(target) < 0 else "in order (out of sequence)"
                    errors.append(f"{seg['id']}: text not found {where} in the PDF")
                    continue
                pos_big = found + len(target)
                for n in re.findall(r"\[\^(\d+)\]", seg["text"]):
                    note_pages.setdefault((chapter, int(n), "ref"), big_pages[found + len(target) - 1])

    for key, page_idx in note_pages.items():
        if len(key) == 3:
            note_page = note_pages.get((key[0], key[1]))
            if note_page is not None and abs(note_page - page_idx) > 1:
                errors.append(f"footnote {key[1]} (chapter {key[0]}): reference on p. {page_idx + 1}, "
                              f"note on p. {note_page + 1}")

    # ---- fonts
    for page in doc:
        for f in page.get_fonts():
            if f[1] == "n/a":
                errors.append(f"p. {page.number + 1}: font not embedded: {f[3]}")
    # ---- layout
    left, right = metrics["left"], metrics["right"]
    for i, p in enumerate(pages):
        page = p["page"]
        if not p["spans"]:
            errors.append(f"p. {i + 1}: empty page")
            continue
        # Glyph boxes, not span boxes: spans include trailing tracking/space.
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for sp in line["spans"]:
                    for ch in sp["chars"]:
                        if ch["c"].isspace():
                            continue
                        x0, y0, x1, y1 = ch["bbox"]
                        if x0 < left - 3 or x1 > right + 3 or y0 < 40 or y1 > page.rect.height - 30:
                            errors.append(f"p. {i + 1}: text outside the margins near "
                                          f"'{''.join(c['c'] for c in sp['chars'])[:40]}'")
                            break
        lines = sorted({(round(sp["bbox"][1], 1), round(sp["bbox"][3], 1)) for sp in p["spans"]
                        if sp["size"] >= body_size - 0.5})
        for (a0, a1), (b0, b1) in zip(lines, lines[1:]):
            if b0 < a1 - 4 and b0 - a0 > 3:
                warnings.append(f"p. {i + 1}: lines may overlap near y={b0}")
                break
        body = [sp for sp in p["spans"] if sp["size"] >= body_size - 0.5]
        if body:
            last = max(body, key=lambda sp: sp["bbox"][3])
            if last["flags"] & 16 and i + 1 < len(pages) and last["bbox"][1] > page.rect.height * 0.75:
                warnings.append(f"p. {i + 1}: heading stranded at the bottom: '{last['text'][:40]}'")
        if len(norm("".join(sp["text"] for sp in p["spans"]))) < 20 and i > 1:
            warnings.append(f"p. {i + 1}: nearly empty page")

    # ---- previews
    prev_dir = OUTPUT_DIR / slug / "preview"
    prev_dir.mkdir(parents=True, exist_ok=True)
    for old in prev_dir.glob("*.png"):
        old.unlink()
    for page in doc:
        page.get_pixmap(dpi=50).save(prev_dir / f"page-{page.number + 1:03d}.png")

    md = [f"# PDF check: {slug}", "", f"File: `{pdf_path.relative_to(ROOT)}`  ",
          f"Pages: {len(doc)} (original: {load_json(cfg['_extracted_path'] / 'metadata.json')['page_count']})  ",
          f"Segments checked: {seg_count}  ",
          f"Status: **{'FAIL' if errors else 'PASS'}**", "",
          "## Errors", ""] + ([f"- {e}" for e in errors] or ["- none"]) + [
          "", "## Warnings", ""] + ([f"- {w}" for w in warnings] or ["- none"]) + [
          "", f"Previews: `output/{slug}/preview/`"]
    write_text_atomic(OUTPUT_DIR / slug / "pdf-check.md", "\n".join(md) + "\n")
    print(f"{slug}: {'FAIL' if errors else 'PASS'} - {len(doc)} pages, {seg_count} segments, "
          f"{len(errors)} errors, {len(warnings)} warnings -> output/{slug}/pdf-check.md")
    if not errors:
        doc.close()
        print(f"Published: {publish(cfg, pdf_path).relative_to(ROOT)}")
    return not errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug")
    args = parser.parse_args()
    try:
        sys.exit(0 if check(args.slug) else 1)
    except PipelineError as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()
