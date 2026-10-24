"""Rebuild the logical structure of a book from extracted/<book>/pages/*.json.

The extractor stores PyMuPDF blocks, which in these PDFs are often single
lines or even single words (justified lines are split word by word). This
script regroups spans by baseline into lines, classifies each line
(heading, body, footnote, page number, watermark) and joins lines into
paragraphs using indentation, vertical gaps and line widths. It then splits
the book into chapters and writes, under work/<slug>/:

  book.json                 chapter index + detected layout metrics
  chapters/NN.json          source segments (pt-BR) with a style summary
  chapters/NN.layout.json   per-segment line geometry, for the PDF rebuild
  chapters/NN.pt.md         marker-delimited source text for translation
  structure-report.md       what was detected, dropped and flagged

Usage:
  python tools/segment.py <slug>
"""

import argparse
import collections
import re
import statistics
import sys

from common import (
    WORK_DIR, PipelineError, fail, load_book_config, load_json, marker,
    strip_markup, text_hash, write_json_atomic, write_text_atomic,
)

DEFAULT_CHAPTER_RE = (
    r"^(\d{1,2}\s*\.\s*\S|Introdução|Conclus(ão|ões)|Anexos?\b|"
    r"Referências?|Sobre o autor|Aforismos)"
)


# ---------------------------------------------------------------- lines

def build_lines(page: dict, page_no: int) -> list[dict]:
    """Group the page's spans into visual lines.

    Larger spans are placed first so that small raised spans (footnote
    markers) attach to the line whose vertical range contains them."""
    spans = []
    for block_index, block in enumerate(page["blocks"]):
        if block["type"] != "text":
            continue
        for span in block["spans"]:
            if span["text"].strip():
                spans.append(dict(span, block=block_index))
    spans.sort(key=lambda s: -s["size"])

    lines = []
    for span in spans:
        cy = (span["bbox"][1] + span["bbox"][3]) / 2
        for line in lines:
            if line["y0"] - 0.5 <= cy <= line["y1"] + 0.5:
                line["spans"].append(span)
                break
        else:
            lines.append({"y0": span["bbox"][1], "y1": span["bbox"][3], "spans": [span]})

    result = [finish_line(line["spans"], page_no) for line in lines]
    result.sort(key=lambda ln: (ln["y0"], ln["x0"]))
    return result


def finish_line(spans: list[dict], page_no: int) -> dict:
    spans.sort(key=lambda s: s["bbox"][0])
    main = max(spans, key=lambda s: len(s["text"].strip()))
    size, baseline = main["size"], main["origin"][1]
    chars = sum(len(s["text"].strip()) for s in spans) or 1

    runs = []          # (text, italic, bold, kind) with kind in text|ref|space
    prev = None
    max_gap = 0.0
    for span in spans:
        text = span["text"]
        raised = span["size"] < 0.85 * size and span["origin"][1] < baseline - 1.0
        if prev is not None:
            gap = span["bbox"][0] - prev["bbox"][2]
            max_gap = max(max_gap, gap)
            if (gap > 0.2 * size and not raised
                    and not prev["text"][-1:].isspace() and not text[:1].isspace()):
                runs.append((" ", False, False, "space"))
        if raised and re.fullmatch(r"\s*\d{1,3}\s*", text):
            runs.append((f"[^{text.strip()}]", False, False, "ref"))
            if text[-1:].isspace():
                runs.append((" ", False, False, "space"))
        else:
            runs.append((text, bool(span["flags"] & 2), bool(span["flags"] & 16), "text"))
        prev = span

    plain = re.sub(r"\s+", " ", "".join(r[0] for r in runs)).strip()
    bold = sum(len(s["text"].strip()) for s in spans if s["flags"] & 16) / chars
    italic = sum(len(s["text"].strip()) for s in spans if s["flags"] & 2) / chars
    return {
        "page": page_no,
        "x0": min(s["bbox"][0] for s in spans),
        "y0": min(s["bbox"][1] for s in spans),
        "x1": max(s["bbox"][2] for s in spans),
        "y1": max(s["bbox"][3] for s in spans),
        "size": round(size, 1),
        "font": main["font"],
        "color": main["color"],
        "flags": main["flags"],
        "bold": bold,
        "italic": italic,
        "runs": runs,
        "plain": plain,
        "max_gap": max_gap,
        "blocks": sorted({s["block"] for s in spans}),
        "nchars": chars,
    }


# -------------------------------------------------------------- metrics

def mode(values, default=None):
    counts = collections.Counter(values)
    return counts.most_common(1)[0][0] if counts else default


def book_metrics(pages_lines: list[list[dict]]) -> dict:
    size_chars = collections.Counter()
    for lines in pages_lines:
        for ln in lines:
            size_chars[ln["size"]] += ln["nchars"]
    body_size = size_chars.most_common(1)[0][0]

    body = [ln for lines in pages_lines for ln in lines
            if abs(ln["size"] - body_size) < 0.3 and ln["bold"] < 0.5]
    left = mode(round(ln["x0"]) for ln in body)
    right = mode(round(ln["x1"]) for ln in body if ln["x1"] > left + 200)
    indent = mode((round(ln["x0"]) for ln in body if left + 8 < ln["x0"] < left + 60), None)

    gaps = []
    for lines in pages_lines:
        b = [ln for ln in lines if abs(ln["size"] - body_size) < 0.3]
        for a, c in zip(b, b[1:]):
            gap = c["y0"] - a["y1"]
            if 0 < gap < 3 * body_size:
                gaps.append(gap)
    line_gap = statistics.median(gaps) if gaps else body_size * 0.5
    return {
        "body_size": body_size,
        "left": left,
        "right": right,
        "indent": indent,
        "line_gap": round(line_gap, 2),
        "para_gap": round(max(line_gap * 1.6, line_gap + 4), 2),
    }


# -------------------------------------------------------- classification

def starts_with_ref(ln: dict) -> bool:
    first = next((r for r in ln["runs"] if r[0].strip()), None)
    return first is not None and first[3] == "ref"


def classify(lines: list[dict], page: dict, metrics: dict, drop_res, prev_page_notes: bool) -> bool:
    """Set ln["kind"] on every line. Returns True if the page has footnotes.

    The footnote zone is the run of small-font lines below the last
    normal-size line, starting at a line that begins with a raised number
    (or, at the top of the zone, continuing a note from the previous page).
    Small text that does not start that way (a table of contents, an
    epigraph) stays body text."""
    height = page["height"]
    body_size = metrics["body_size"]
    for ln in lines:
        if any(r.search(ln["plain"]) for r in drop_res):
            ln["kind"] = "drop"
        elif re.fullmatch(r"\d{1,4}|[ivxlcdm]{1,6}", ln["plain"], re.I) and ln["y0"] > 0.85 * height:
            ln["kind"] = "page_number"
        else:
            ln["kind"] = None

    normal = [ln for ln in lines if ln["kind"] is None and ln["size"] > body_size - 1]
    last_normal = max((ln["y1"] for ln in normal), default=0)
    candidates = [ln for ln in lines if ln["kind"] is None and ln["size"] <= body_size - 1
                  and ln["y0"] > 0.5 * height and ln["y0"] >= last_normal]
    in_zone = False
    for i, ln in enumerate(candidates):
        if starts_with_ref(ln) or (i == 0 and prev_page_notes and ln["y0"] > 0.7 * height):
            in_zone = True
        if in_zone:
            ln["kind"] = "footnote"

    for ln in lines:
        if ln["kind"]:
            continue
        if (ln["bold"] >= 0.8 or ln["size"] >= body_size + 1.5) and len(ln["plain"]) <= 200:
            ln["kind"] = "heading"
        else:
            ln["kind"] = "body"
    return in_zone


# ------------------------------------------------------------ segments

def join_runs(segment_lines: list[dict], soft_hyphenation: bool) -> list[tuple]:
    runs = []
    for i, ln in enumerate(segment_lines):
        if i:
            prev = segment_lines[i - 1]["plain"]
            hyphen_break = prev.endswith("-") and len(prev) > 1 and prev[-2].isalpha()
            if hyphen_break and soft_hyphenation:
                runs[-1] = (runs[-1][0].rstrip().rstrip("-"),) + runs[-1][1:]
            elif not hyphen_break:
                runs.append((" ", False, False, "space"))
            else:
                runs[-1] = (runs[-1][0].rstrip(),) + runs[-1][1:]
        runs.extend(ln["runs"])
    return runs


def render(runs: list[tuple], suppress_italic: bool, suppress_bold: bool) -> str:
    out, open_i, open_b = [], False, False
    for text, italic, bold, kind in runs:
        if kind == "text" and text.strip():
            want_i = italic and not suppress_italic
            want_b = bold and not suppress_bold
            if (want_i, want_b) != (open_i, open_b):
                if open_i:
                    out.append("</i>")
                if open_b:
                    out.append("</b>")
                if want_b:
                    out.append("<b>")
                if want_i:
                    out.append("<i>")
                open_i, open_b = want_i, want_b
        out.append(text)
    if open_i:
        out.append("</i>")
    if open_b:
        out.append("</b>")
    text = "".join(out)
    for tag in ("i", "b"):
        text = re.sub(rf"</{tag}>(\s*)<{tag}>", r"\1", text)
        text = re.sub(rf"(\s+)</{tag}>", rf"</{tag}>\1", text)
        text = re.sub(rf"<{tag}>(\s+)", rf"\1<{tag}>", text)
    return re.sub(r"\s+", " ", text).strip()


def make_segment(kind: str, seg_lines: list[dict], metrics: dict, cfg: dict, fn=None) -> dict:
    runs = join_runs(seg_lines, cfg.get("soft_hyphenation", False))
    chars = sum(len(r[0].strip()) for r in runs if r[3] == "text") or 1
    italic = sum(len(r[0].strip()) for r in runs if r[3] == "text" and r[1]) / chars
    bold = sum(len(r[0].strip()) for r in runs if r[3] == "text" and r[2]) / chars
    all_italic, all_bold = italic >= 0.9, bold >= 0.9
    text = render(runs, all_italic, all_bold)
    if fn is not None:
        text = re.sub(r"^\[\^\d+\]\s*", "", text)

    first = seg_lines[0]
    left, right = metrics["left"], metrics["right"]
    mid = (first["x0"] + first["x1"]) / 2
    centered = (first["x0"] > left + 15 and abs(mid - (left + right) / 2) < 15
                and all(ln["x1"] < right - 10 for ln in seg_lines))
    sizes = collections.Counter()
    for ln in seg_lines:
        sizes[ln["size"]] += ln["nchars"]

    segment = {
        "type": kind,
        "text": text,
        "pages": sorted({ln["page"] for ln in seg_lines}),
        "style": {
            "font": first["font"],
            "size": sizes.most_common(1)[0][0],
            "bold": all_bold,
            "italic": all_italic,
            "align": "center" if centered else "justify",
            "first_line_indent": round(first["x0"] - left, 1) if not centered else 0,
            "left": round(min(ln["x0"] for ln in seg_lines[1:] or seg_lines) - left, 1),
            "color": first["color"],
        },
        "warnings": [],
        "_lines": seg_lines,
    }
    if fn is not None:
        segment["fn"] = fn
    if any(ln["max_gap"] > 4 * ln["size"] for ln in seg_lines):
        segment["warnings"].append("wide gap inside a line: possible table or columns")
    return segment


def is_full_width(ln: dict, metrics: dict) -> bool:
    return ln["x1"] >= metrics["right"] - 12


def is_indented(ln: dict, prev: dict, metrics: dict) -> bool:
    indent = metrics["indent"]
    if indent is None or abs(ln["x0"] - indent) > 4:
        return False
    # A block of lines that all start at the indent (a quotation) is not a
    # new paragraph on every line.
    return not (abs(prev["x0"] - ln["x0"]) <= 2 and is_full_width(prev, metrics))


def build_segments(pages_lines, metrics, cfg):
    body_segments = []        # headings and paragraphs, reading order
    footnotes = []            # with "_page" of their first line
    current = None            # (kind, [lines])

    def close():
        nonlocal current
        if current:
            body_segments.append(make_segment(current[0], current[1], metrics, cfg))
        current = None

    for lines in pages_lines:
        page_note = None
        for ln in lines:
            kind = ln["kind"]
            if kind in ("drop", "page_number"):
                continue
            if kind == "footnote":
                ref = ln["runs"][0] if ln["runs"] else None
                if ref and ref[3] == "ref":
                    page_note = {"fn": int(ref[0][2:-1]), "lines": [ln], "page": ln["page"]}
                    footnotes.append(page_note)
                elif page_note is not None:
                    page_note["lines"].append(ln)
                elif footnotes:
                    # Footnote continued from the previous page.
                    page_note = footnotes[-1]
                    page_note["lines"].append(ln)
                else:
                    page_note = {"fn": None, "lines": [ln], "page": ln["page"]}
                    footnotes.append(page_note)
                continue

            if kind == "heading":
                if (current and current[0] == "heading"
                        and current[1][-1]["page"] == ln["page"]
                        and abs(current[1][-1]["size"] - ln["size"]) < 0.5
                        and ln["y0"] - current[1][-1]["y1"] < metrics["para_gap"]):
                    current[1].append(ln)
                else:
                    close()
                    current = ("heading", [ln])
                continue

            new = True
            if current and current[0] == "paragraph":
                prev = current[1][-1]
                # A short previous line ends the paragraph only if it also ends
                # a sentence: the originals contain manual line breaks in
                # mid-sentence ("... existentes. A" / "dificuldade está ...").
                continues = (re.search(r"[.!?:;…”\"»)]\s*$", prev["plain"]) is None
                             and ln["plain"][:1].islower())
                short_end = not is_full_width(prev, metrics) and not continues
                if abs(prev["size"] - ln["size"]) > 0.8:
                    new = True
                elif continues and ln["y0"] - prev["y1"] <= metrics["para_gap"] or (
                        continues and prev["page"] != ln["page"]):
                    # Mid-sentence break wins over indentation (hanging
                    # indents in numbered lists).
                    new = False
                elif is_indented(ln, prev, metrics):
                    new = True
                elif prev["page"] != ln["page"]:
                    new = short_end
                else:
                    new = ln["y0"] - prev["y1"] > metrics["para_gap"] or short_end
            if new:
                close()
                current = ("paragraph", [ln])
            else:
                current[1].append(ln)
    close()

    notes = []
    for note in footnotes:
        seg = make_segment("footnote", note["lines"], metrics, cfg, fn=note["fn"])
        seg["_page"] = note["page"]
        notes.append(seg)
    return body_segments, notes


# ------------------------------------------------------------- chapters

def split_chapters(body_segments, cfg):
    explicit = cfg.get("chapter_starts")
    pattern = re.compile(cfg.get("chapter_heading_regex", DEFAULT_CHAPTER_RE))

    def starts_chapter(seg):
        if seg["type"] != "heading":
            return False
        plain = strip_markup(seg["text"])
        if explicit is not None:
            return any(seg["pages"][0] == c["page"] and plain.startswith(c["starts_with"])
                       for c in explicit)
        return bool(pattern.match(plain))

    chapters = [{"title": "(front matter)", "segments": []}]
    for seg in body_segments:
        if starts_chapter(seg):
            chapters.append({"title": strip_markup(seg["text"]), "segments": []})
        chapters[-1]["segments"].append(seg)
    if not chapters[0]["segments"]:
        chapters.pop(0)
    for i, ch in enumerate(chapters):
        ch["id"] = f"{i:02d}"
    return chapters


def attach_footnotes(chapters, notes, warnings):
    refs = []   # (page, fn, chapter, segment index)
    for ch in chapters:
        for i, seg in enumerate(ch["segments"]):
            for n in re.findall(r"\[\^(\d+)\]", seg["text"]):
                refs.append((seg["pages"], int(n), ch, seg))

    inserts = collections.defaultdict(list)   # id(seg) -> notes after it
    used = set()
    for note in notes:
        page, n = note["_page"], note.get("fn")
        target = None
        for back in (0, 1, 2):
            for k, (pages, rn, ch, seg) in enumerate(refs):
                if rn == n and (page - back) in pages and k not in used:
                    target = (k, ch, seg)
                    break
            if target:
                break
        if target:
            used.add(target[0])
            inserts[id(target[2])].append(note)
            note["_chapter"] = target[1]["id"]
        else:
            warnings.append(f"footnote {n} on page {page}: no matching reference found")
            ch = next((c for c in reversed(chapters)
                       if any(s["pages"][0] <= page for s in c["segments"])), chapters[-1])
            ch["segments"].append(note)
    for k, (pages, rn, ch, seg) in enumerate(refs):
        if k not in used:
            warnings.append(f"reference [^{rn}] on page {pages[0]} (chapter {ch['id']}): "
                            "no footnote text found")

    for ch in chapters:
        ordered = []
        for seg in ch["segments"]:
            ordered.append(seg)
            ordered.extend(inserts.get(id(seg), []))
        ch["segments"] = ordered


# ---------------------------------------------------------------- output

def layout_record(seg):
    return {
        "type": seg["type"],
        "lines": [{
            "page": ln["page"],
            "bbox": [round(ln["x0"], 1), round(ln["y0"], 1), round(ln["x1"], 1), round(ln["y1"], 1)],
            "font": ln["font"],
            "size": ln["size"],
            "flags": ln["flags"],
            "color": ln["color"],
            "blocks": ln["blocks"],
        } for ln in seg["_lines"]],
    }


def nonspace_chars(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def segment_book(slug: str) -> None:
    cfg = load_book_config(slug)
    drop_res = [re.compile(p) for p in cfg.get("drop_line_patterns", [])]
    page_files = sorted((cfg["_extracted_path"] / "pages").glob("page-*.json"))
    pages = [load_json(f) for f in page_files]
    if not pages:
        raise PipelineError(f"No page files in {cfg['_extracted_path'] / 'pages'}")

    pages_lines = [build_lines(p, p["page_number"]) for p in pages]
    metrics = book_metrics(pages_lines)
    metrics.update({k: v for k, v in cfg.get("metrics_override", {}).items()})
    dropped = collections.Counter()
    kept_chars = 0
    has_notes = False
    for page, lines in zip(pages, pages_lines):
        has_notes = classify(lines, page, metrics, drop_res, has_notes)
        for ln in lines:
            if ln["kind"] in ("drop", "page_number"):
                dropped[ln["kind"]] += 1
            else:
                kept_chars += nonspace_chars(strip_markup(ln["plain"]))

    warnings = []
    body_segments, notes = build_segments(pages_lines, metrics, cfg)
    chapters = split_chapters(body_segments, cfg)
    attach_footnotes(chapters, notes, warnings)

    out_dir = WORK_DIR / slug
    chap_dir = out_dir / "chapters"
    chap_dir.mkdir(parents=True, exist_ok=True)
    for stale in chap_dir.glob("*"):
        stale.unlink()

    index, seg_chars = [], 0
    for ch in chapters:
        for i, seg in enumerate(ch["segments"], 1):
            seg["id"] = f"{ch['id']}-{i:04d}"
            seg["hash"] = text_hash(seg["text"])
            # Footnote numbers live in "fn", not in the text.
            seg_chars += nonspace_chars(strip_markup(seg["text"])) + len(str(seg.get("fn") or ""))
            for w in seg["warnings"]:
                warnings.append(f"{seg['id']} (p. {seg['pages'][0]}): {w}")

        public = [{k: v for k, v in s.items() if not k.startswith("_")} for s in ch["segments"]]
        pages_span = [min(p for s in public for p in s["pages"]), max(p for s in public for p in s["pages"])]
        words = sum(len(strip_markup(s["text"]).split()) for s in public)
        write_json_atomic(chap_dir / f"{ch['id']}.json", {
            "book": slug, "chapter": ch["id"], "title": ch["title"],
            "pages": pages_span, "segments": public,
        })
        write_json_atomic(chap_dir / f"{ch['id']}.layout.json",
                          {s["id"]: layout_record(s) for s in ch["segments"]})
        md = [f"<!-- book: {slug} | chapter: {ch['id']} | pages: {pages_span[0]}-{pages_span[1]} -->",
              f"<!-- title: {ch['title']} -->", ""]
        for s in public:
            md += [marker(s), s["text"], ""]
        write_text_atomic(chap_dir / f"{ch['id']}.pt.md", "\n".join(md))
        index.append({
            "id": ch["id"], "title": ch["title"], "pages": pages_span,
            "segments": len(public), "words": words,
            "footnotes": sum(1 for s in public if s["type"] == "footnote"),
        })

    write_json_atomic(out_dir / "book.json", {
        "book": slug, "title": cfg.get("title_pt"), "metrics": metrics,
        "chapters": index, "dropped_lines": dict(dropped),
        "completeness": {"source_chars": kept_chars, "segment_chars": seg_chars},
        "warnings": warnings,
    })
    write_report(out_dir / "structure-report.md", slug, cfg, metrics, chapters, index,
                 dropped, kept_chars, seg_chars, warnings)

    status = "OK" if kept_chars == seg_chars else "MISMATCH"
    print(f"{slug}: {len(index)} chapters, {sum(c['segments'] for c in index)} segments, "
          f"completeness {status} ({seg_chars}/{kept_chars} chars), {len(warnings)} warnings")
    print(f"Report: {out_dir / 'structure-report.md'}")


def write_report(path, slug, cfg, metrics, chapters, index, dropped, kept, segc, warnings):
    md = [f"# Structure report: {slug}", "",
          f"Source: `{cfg['extracted_dir']}`", "",
          "## Layout metrics (auto-detected)", "",
          *[f"- {k}: {v}" for k, v in metrics.items()], "",
          "## Completeness", "",
          f"- Non-space characters in kept lines: {kept}",
          f"- Non-space characters in segments: {segc}",
          f"- Result: {'OK' if kept == segc else 'MISMATCH, investigate before translating'}",
          f"- Dropped lines: {dict(dropped) or 'none'}", "",
          "## Chapters", "",
          "| id | title | pages | segments | words | footnotes |",
          "|---|---|---|---|---|---|"]
    for c in index:
        md.append(f"| {c['id']} | {c['title']} | {c['pages'][0]}-{c['pages'][1]} | "
                  f"{c['segments']} | {c['words']} | {c['footnotes']} |")
    md += ["", "## Headings (check chapter vs. sub-heading)", ""]
    for ch in chapters:
        for s in ch["segments"]:
            if s["type"] == "heading":
                md.append(f"- [{ch['id']}] p. {s['pages'][0]}, {s['style']['size']} pt: "
                          f"{strip_markup(s['text'])}")
    md += ["", "## Warnings", ""] + ([f"- {w}" for w in warnings] or ["- none"])
    write_text_atomic(path, "\n".join(md) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug", help="book slug, as in config/books/<slug>.json")
    args = parser.parse_args()
    try:
        segment_book(args.slug)
    except PipelineError as exc:
        fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
