"""Measure the typography of an original PDF and write the "pdf" section of
config/books/<slug>.json (used by build_pdf.py).

Measures: body font and size, letter tracking, baseline-to-baseline line and
paragraph pitch, footnote size/pitch, footnote rule length, page-number size
and alignment. Maps the original fonts to free equivalents in fonts/.

Usage:
  python tools/measure_layout.py <slug>            print the measurements
  python tools/measure_layout.py <slug> --write    also store them in the config
"""

import argparse
import collections
import json
import re
import statistics
import sys

import pymupdf

from common import CONFIG_DIR, ROOT, PipelineError, fail, load_book_config

# Original font family (substring) -> free font available in fonts/
FREE_FONTS = {
    "TimesNewRoman": "Liberation Serif",
    "Times": "Liberation Serif",
    "BookmanOldStyle": "TeX Gyre Bonum",
    "Bookman": "TeX Gyre Bonum",
    "Georgia": "Gelasio",
    "Helvetica": "Liberation Sans",
    "Arial": "Liberation Sans",
    "Tahoma": "Liberation Sans",
}
FONT_FILES = {
    "Liberation Serif": ROOT / "fonts/liberation/LiberationSerif-Regular.ttf",
    "Liberation Sans": ROOT / "fonts/liberation/LiberationSans-Regular.ttf",
    "TeX Gyre Bonum": ROOT / "fonts/texgyre/texgyrebonum-regular.otf",
    "Gelasio": ROOT / "fonts/gelasio/Gelasio-Regular.ttf",
}
FLAGS = pymupdf.TEXTFLAGS_DICT | pymupdf.TEXT_INHIBIT_SPACES


def free_font(name: str) -> str:
    for family, free in FREE_FONTS.items():
        if family.lower() in name.lower().replace(" ", ""):
            return free
    return "Liberation Serif"


def mode(values, default=None):
    c = collections.Counter(values)
    return c.most_common(1)[0][0] if c else default


def measure(slug: str) -> dict:
    cfg = load_book_config(slug)
    drop = [re.compile(x) for x in cfg.get("drop_line_patterns", [])]   # watermarks
    doc = pymupdf.open(ROOT / cfg["source_pdf"])
    lines = []   # (page, size, font, x0, y0, x1, baseline, text, nspans, flags)
    rules = collections.Counter()
    for page in doc:
        if page.number < 2:          # skip title pages
            continue
        for block in page.get_text("dict", flags=FLAGS)["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                main = max(spans, key=lambda s: len(s["text"].strip()))
                text = "".join(s["text"] for s in spans).rstrip()
                if any(r.search(text) for r in drop):
                    continue
                lines.append((page.number, round(main["size"], 1), main["font"], line["bbox"][0],
                              line["bbox"][1], line["bbox"][2], main["origin"][1], text, len(spans),
                              main["flags"]))
        for d in page.get_drawings():
            r = d["rect"]
            if r.height < 2 and 50 < r.width < 300 and r.y0 > page.rect.height * 0.4:
                rules[round(r.width)] += 1

    weights = collections.Counter()
    for ln in lines:
        weights[ln[1]] += len(ln[7])
    body_size = weights.most_common(1)[0][0]
    body = [ln for ln in lines if ln[1] == body_size and not ln[9] & 16]
    body_font = mode(ln[2] for ln in body)

    # baseline pitches between consecutive body lines on the same page
    pitches = collections.Counter()
    for a, b in zip(body, body[1:]):
        if a[0] == b[0] and 0 < b[6] - a[6] < 4 * body_size:
            pitches[round(b[6] - a[6], 1)] += 1
    line_pitch = pitches.most_common(1)[0][0]
    para = [p for p in pitches if p > line_pitch * 1.3]
    para_pitch = max(para, key=lambda p: pitches[p]) if para else round(line_pitch * 1.6, 1)

    # letter tracking from short (unjustified) single-span body lines
    right = mode(round(ln[5]) for ln in body if ln[5] > doc[0].rect.width * 0.6)
    # Natural widths come from the free font that will actually be used, so the
    # measured extra spacing is what build_pdf.py must add.
    font = pymupdf.Font(fontfile=str(FONT_FILES[free_font(body_font)]))
    tracking = []
    for ln in body:
        if ln[8] == 1 and ln[5] < right - 40 and len(ln[7]) > 25:
            natural = font.text_length(ln[7], fontsize=ln[1])
            tracking.append((ln[5] - ln[3] - natural) / (len(ln[7]) - 1))
    track = round(min(max(statistics.median(tracking), 0), 2) * 2) / 2 if tracking else 0.0

    # footnotes: smaller lines low on the page
    small = [ln for ln in lines if ln[1] < body_size - 1 and ln[4] > doc[0].rect.height * 0.55
             and not ln[7].strip().isdigit()]
    fn_size = mode(ln[1] for ln in small if len(ln[7]) > 20) or round(body_size * 0.8, 1)
    fn_lines = [ln for ln in small if ln[1] == fn_size]
    fn_pitch = mode(round(b[6] - a[6], 1) for a, b in zip(fn_lines, fn_lines[1:])
                    if a[0] == b[0] and 0 < b[6] - a[6] < 2 * fn_size) or round(fn_size * 1.15, 1)

    # page numbers
    height, width = doc[0].rect.height, doc[0].rect.width
    nums = [ln for ln in lines if ln[7].strip().isdigit() and ln[4] > height * 0.85]
    pn_size = mode(ln[1] for ln in nums) or 10
    centers = [abs((ln[3] + ln[5]) / 2 - width / 2) for ln in nums]
    align = "center" if centers and statistics.median(centers) < 20 else "right"

    fonts = {ln[2] for ln in lines}
    font_map = {}
    for f in sorted(fonts):
        free = free_font(f)
        key = next((fam for fam in FREE_FONTS if fam.lower() in f.lower().replace(" ", "")), None)
        if key and free != free_font(body_font):
            font_map[key] = free
    return {
        "font": free_font(body_font),
        "font_dir": "fonts",
        "font_map": font_map,
        "tracking_pt": track,
        "line_pitch_pt": line_pitch,
        "paragraph_pitch_pt": para_pitch,
        "footnote_size_pt": fn_size,
        "footnote_pitch_pt": fn_pitch,
        "page_number_size_pt": pn_size,
        "page_number_align": align,
        "footnote_rule_pt": mode(rules.elements()) or 144,
        "notes": f"Measured by tools/measure_layout.py from {cfg['source_pdf']} "
                 f"(body {body_font} {body_size} pt).",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        pdf = measure(args.slug)
        print(json.dumps(pdf, ensure_ascii=False, indent=2))
        if args.write:
            path = CONFIG_DIR / f"{args.slug}.json"
            cfg = json.loads(path.read_text(encoding="utf-8"))
            cfg["pdf"] = pdf
            path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Written to {path.relative_to(ROOT)}")
    except PipelineError as exc:
        fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
