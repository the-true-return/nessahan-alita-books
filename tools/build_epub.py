"""Build the English EPUB of a book (EPUB 3, reflowable).

Same sources as the PDF (tools/build_pdf.py): the translated segments
(translations/<slug>/NN.en.md), the source segment styles
(work/<slug>/chapters/NN.json) and the glossary appendix. Unlike the PDF, the
text reflows: the original page geometry is not reproduced, only the
structure (headings, paragraph indents, centered and indented blocks,
italics, tables) and the footnotes, which become pop-up notes at the end of
each chapter file, with links back to the reference.

No fonts are embedded: the reader's own fonts are used. The cover is an image
generated with Typst (fonts from fonts/), skipped if Typst or PyMuPDF are not
installed.

Output: output/<slug>/<slug>-en.epub. tools/check_epub.py verifies it and,
if every check passes, publishes it to epubs/.

Usage:
  python tools/build_epub.py <slug> [--draft]
  python tools/build_epub.py --all [--draft]
"""

import argparse
import datetime
import html
import re
import subprocess
import sys
import uuid
import zipfile

from build_pdf import GLOSSARY_INTRO, TOKEN_RE, glossary_entries
from common import (
    CONFIG_DIR, ROOT, TRANSLATIONS_DIR, WORK_DIR, PipelineError, chapter_ids, fail,
    load_book_config, load_json, parse_marked_md, strip_markup,
)
from qa import check_chapter, load_glossary

OUTPUT_DIR = ROOT / "output"
AUTHOR = "Nessahan Alita"
LANG = "en-US"

CSS = """\
body { margin: 0 4%; line-height: 1.45; font-family: serif; }
p { margin: 0 0 0.6em 0; text-indent: 0; text-align: justify;
    hyphens: auto; -webkit-hyphens: auto; -epub-hyphens: auto; adobe-hyphenate: auto; }
p.indent { text-indent: 1.6em; }
p.center { text-align: center; text-indent: 0; hyphens: none; -webkit-hyphens: none; }
p.block { margin-left: 2em; }
p.hang { margin-left: 2em; text-indent: -1.2em; }
p.italic { font-style: italic; }
p.bold { font-weight: bold; }
p.sans, td.sans { font-family: sans-serif; }
p.small { font-size: 0.9em; }
h1 { font-size: 1.35em; font-weight: bold; text-align: center; margin: 2em 0 1.2em 0;
     line-height: 1.3; hyphens: none; -webkit-hyphens: none; page-break-after: avoid; }
h2 { font-size: 1.05em; font-weight: bold; margin: 1.6em 0 0.8em 0; line-height: 1.3;
     hyphens: none; -webkit-hyphens: none; page-break-after: avoid; }
.left h1, .left h2 { text-align: left; }
.center h2 { text-align: center; }
.front h1, .front h2 { text-align: center; }
.front p { text-align: center; text-indent: 0; }
.front p.justify { text-align: justify; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
td { border: 1px solid; padding: 0.3em 0.4em; vertical-align: top; text-align: left; font-size: 0.9em; }
a.noteref { text-decoration: none; }
sup { font-size: 0.7em; line-height: 0; vertical-align: super; }
section.notes { margin-top: 2em; font-size: 0.88em; }
section.notes hr { width: 30%; margin: 0 auto 1em 0; border: 0; border-top: 1px solid; }
section.notes p { text-indent: 0; }
p.gloss { margin-left: 1.5em; text-indent: -1.5em; }
p.gloss-intro { font-style: italic; }
div.cover { text-align: center; margin: 0; padding: 0; }
div.cover img { max-width: 100%; max-height: 100%; }
"""

XHTML_HEAD = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}" lang="{lang}">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="{css}"/>
</head>
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def attr(text: str) -> str:
    return html.escape(text, quote=True)


def xhtml(title: str, body: str, body_class: str = "", css: str = "../css/book.css") -> str:
    cls = f' class="{body_class}"' if body_class else ""
    return (XHTML_HEAD.format(lang=LANG, title=esc(title), css=css)
            + f"<body{cls}>\n{body}\n</body>\n</html>\n")


def inline(text: str, footnotes: dict, used: list) -> str:
    """Segment markup (<i>, <b>, [^n], newlines) to XHTML."""
    out = []
    for tok in TOKEN_RE.split(text):
        if not tok:
            continue
        if tok in ("<i>", "</i>", "<b>", "</b>"):
            out.append(tok)
        elif tok == "\n":
            out.append("<br/>")
        elif tok.startswith("[^"):
            n = int(tok[2:-1])
            if n not in footnotes:
                raise PipelineError(f"footnote [^{n}] has no translated footnote text")
            if n in used:
                raise PipelineError(f"footnote [^{n}] referenced twice in one chapter")
            used.append(n)
            out.append(f'<a class="noteref" epub:type="noteref" role="doc-noteref" '
                       f'id="ref{n}" href="#fn{n}"><sup>{n}</sup></a>')
        else:
            out.append(esc(tok.replace("¦", "")))
    return "".join(out)


def para_classes(style: dict, body_size: float) -> list[str]:
    """CSS classes from the source paragraph style (same rules as the PDF)."""
    cls = []
    if style["align"] == "center":
        cls.append("center")
    else:
        first = max(style["first_line_indent"], 0)
        left = max(style["left"], 0)
        if left > 5:
            if first > left + 5:            # indented paragraph with a left margin (letters)
                cls += ["indent", "block"] if left > 25 else ["indent"]
            elif left > first + 5:          # hanging layout (numbered and bulleted lists)
                cls.append("hang")
            elif style.get("lines", 2) == 1 and first <= 40:
                cls.append("indent")        # one-line paragraph: only its first-line indent shows
            else:
                cls.append("block")         # whole paragraph indented
        elif first > 5:
            cls.append("indent")
    if style.get("italic"):
        cls.append("italic")
    if style.get("bold"):
        cls.append("bold")
    font = style.get("font", "").lower()
    if "helvetica" in font or "arial" in font:
        cls.append("sans")
    if style.get("size", body_size) < body_size - 1:
        cls.append("small")
    return cls


def p(body: str, cls: list[str]) -> str:
    c = f' class="{" ".join(cls)}"' if cls else ""
    return f"<p{c}>{body}</p>"


def table_html(rows: list[tuple], footnotes: dict, used: list) -> str:
    """Rows whose first cell is empty continue the previous row (as in the PDF)."""
    groups = []
    for seg, text in rows:
        cells = [c.strip() for c in text.split("¦")]
        if cells[0] or not groups:
            groups.append([[c] if c else [] for c in cells])
        else:
            for k, c in enumerate(cells[1:], 1):
                if c:
                    groups[-1][k].append(c)
    font = rows[0][0]["style"].get("font", "").lower()
    td = '<td class="sans">' if "helvetica" in font or "arial" in font else "<td>"
    out = ["<table>"]
    for group in groups:
        cells = "".join(td + "<br/>".join(inline(x, footnotes, used) for x in parts) + "</td>"
                        for parts in group)
        out.append(f"<tr>{cells}</tr>")
    out.append("</table>")
    return "\n".join(out)


def chapter_html(chapter: str, segments: list, en: dict, body_size: float,
                 title_en: str = "") -> tuple[str, str, int]:
    """XHTML body of one chapter, its title for the table of contents, and the
    number of segments rendered. Mirrors build_pdf.chapter_body's rules."""
    footnotes = {s["fn"]: en[s["id"]] for s in segments if s["type"] == "footnote"}
    used: list = []
    out, title, rendered = [], None, 0
    run_in = ""
    table: list = []
    front = chapter == "00"

    def flush_table():
        if table:
            out.append(table_html(table, footnotes, used))
            table.clear()

    for i, seg in enumerate(segments):
        if seg["type"] == "footnote":
            continue
        text = en[seg["id"]]
        if not front and seg["type"] == "heading" and i > 0 and seg["style"]["size"] < body_size - 0.5:
            # Bold sentence misdetected as a heading: joined to the next paragraph.
            run_in = (f"<b>{text}</b>" if seg["style"].get("bold") else text) + " "
            rendered += 1
            continue
        if run_in and seg["type"] != "heading":
            text, run_in = run_in + text, ""
        if re.fullmatch(r"\s*[.,;:]\s*", strip_markup(text)):
            rendered += 1  # stray punctuation in the original (dropped in the PDF too)
            continue
        rendered += 1
        if seg["type"] == "table_row":
            table.append((seg, text))
            continue
        flush_table()
        if front and seg["type"] == "heading":
            # Title page: the book title is the h1; the other headings (series,
            # subtitle, notices) keep their relative size from the original.
            ratio = min(max(seg["style"]["size"] / body_size, 1.0), 2.0)
            size = f' style="font-size: {ratio:.2f}em"' if ratio > 1.05 else ""
            if strip_markup(text).strip().lower() == title_en.lower():
                out.append(f'<h1 class="title" id="s{seg["id"]}"{size}>'
                           f'{inline(text, footnotes, used)}</h1>')
            else:
                out.append(f'<p class="center bold" id="s{seg["id"]}"{size}>'
                           f'{inline(text, footnotes, used)}</p>')
        elif seg["type"] == "heading":
            level = 1 if i == 0 else 2
            if title is None and not front:
                title = strip_markup(text).replace("\n", " ")
            out.append(f'<h{level} id="s{seg["id"]}">{inline(text, footnotes, used)}</h{level}>')
        else:
            cls = para_classes(seg["style"], body_size)
            if front and seg["style"]["align"] != "center" and len(strip_markup(text)) > 200:
                cls.append("justify")
            out.append(p(inline(text, footnotes, used), cls))
    flush_table()
    if run_in:
        raise PipelineError(f"chapter {chapter}: run-in heading at the end of the chapter")

    unused = set(footnotes) - set(used)
    if unused:
        raise PipelineError(f"chapter {chapter}: footnotes never referenced: {sorted(unused)}")
    if used:
        out.append('<section class="notes" epub:type="endnotes" role="doc-endnotes">\n<hr/>')
        for n in used:  # in reading order
            out.append(f'<aside epub:type="footnote" role="doc-footnote" id="fn{n}">'
                       f'<p><a href="#ref{n}" role="doc-backlink">{n}.</a> '
                       f'{inline(footnotes[n], {}, [])}</p></aside>')
        out.append("</section>")
    return "\n".join(out), title or "Title Page", rendered


def glossary_html(entries: list) -> str:
    out = ['<h1 id="glossary">Glossary</h1>',
           f'<p class="gloss-intro">{esc(GLOSSARY_INTRO)}</p>']
    for e in entries:
        out.append(f'<p class="gloss"><b>{esc(e["display_en"])}</b> '
                   f'(<i lang="pt-BR" xml:lang="pt-BR">{esc(e["display_pt"])}</i>) — '
                   f'{esc(e["note_en"])}</p>')
    return "\n".join(out)


def modified_time(slug: str) -> str:
    """Last commit touching the book's sources: rebuilding unchanged sources
    gives an identical file."""
    paths = [f"translations/{slug}", f"config/books/{slug}.json", "glossary/glossary.json"]
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", *paths], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        ts = datetime.datetime.fromtimestamp(int(out), datetime.timezone.utc)
    except (OSError, subprocess.CalledProcessError, ValueError):
        ts = datetime.datetime.now(datetime.timezone.utc)
    return ts.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def cover_jpeg(cfg: dict) -> bytes | None:
    """Typographic cover (1600x2560 px) made with Typst, rasterized with PyMuPDF."""
    try:
        import pymupdf
        import typst
    except ImportError:
        print("WARNING: Typst or PyMuPDF not installed: EPUB built without a cover image")
        return None

    def lit(t):  # a Typst string inserted as plain text (no smart quotes, no markup)
        return '#"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"'
    series = ""
    if cfg.get("series_en"):
        roman = ["I", "II", "III", "IV", "V", "VI"][cfg["series_index"] - 1]
        series = (f'#text(size: 13pt, tracking: 1.5pt, fill: rgb("#c9b37e"))'
                  f'[#upper({lit(cfg["series_en"])[1:]}) · VOLUME {roman}]\n#v(28pt)\n')
    subtitle = ""
    if cfg.get("subtitle_en"):
        subtitle = (f'#v(26pt)\n#text(size: 15pt, style: "italic", fill: rgb("#e8e2d4"))'
                    f'[{lit(cfg["subtitle_en"])}]\n')
    src = f"""#set page(width: 400pt, height: 640pt, margin: 40pt, fill: rgb("#1d2433"))
#set text(font: "Gelasio", fill: rgb("#f3efe6"), lang: "en", hyphenate: false)
#set par(justify: false, leading: 0.55em)
#align(center)[
#v(90pt)
{series}#line(length: 60pt, stroke: 0.8pt + rgb("#c9b37e"))
#v(30pt)
#text(size: 34pt, weight: "bold")[{lit(cfg["title_en"])}]
{subtitle}#v(30pt)
#line(length: 60pt, stroke: 0.8pt + rgb("#c9b37e"))
#v(1fr)
#text(size: 20pt, tracking: 3pt)[NESSAHAN ALITA]
#v(14pt)
#text(size: 11pt, tracking: 1.5pt, fill: rgb("#c9b37e"))[ENGLISH EDITION]
#v(30pt)
]
"""
    build = OUTPUT_DIR / cfg["slug"] / "build"
    build.mkdir(parents=True, exist_ok=True)
    typ = build / "cover.typ"
    typ.write_text(src, encoding="utf-8")
    pdf = typst.compile(str(typ), font_paths=[str(ROOT / "fonts" / "gelasio")],
                        ignore_system_fonts=True)
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(4, 4))  # 400x640 pt -> 1600x2560 px
    return pix.tobytes("jpeg", jpg_quality=88)


def nav_html(cfg: dict, toc: list, first_body: str) -> str:
    items = "\n".join(f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in toc)
    landmarks = [('text/ch00.xhtml', "titlepage", "Title Page"),
                 (first_body, "bodymatter", "Start of Content"),
                 ("text/glossary.xhtml", "glossary", "Glossary")]
    marks = "\n".join(f'<li><a epub:type="{t}" href="{h}">{esc(lbl)}</a></li>'
                      for h, t, lbl in landmarks if h)
    body = (f'<nav epub:type="toc" role="doc-toc" id="toc">\n<h1>Contents</h1>\n<ol>\n{items}\n</ol>\n</nav>\n'
            f'<nav epub:type="landmarks" hidden="hidden">\n<h2>Landmarks</h2>\n<ol>\n{marks}\n</ol>\n</nav>')
    return xhtml(cfg["title_en"], body, css="css/book.css")


def ncx(cfg: dict, uid: str, toc: list) -> str:
    points = "\n".join(
        f'<navPoint id="np{k}" playOrder="{k}"><navLabel><text>{esc(label)}</text></navLabel>'
        f'<content src="{href}"/></navPoint>' for k, (href, label) in enumerate(toc, 1))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="{LANG}">
<head><meta name="dtb:uid" content="{uid}"/><meta name="dtb:depth" content="1"/>
<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>
<docTitle><text>{esc(cfg["title_en"])}</text></docTitle>
<docAuthor><text>{AUTHOR}</text></docAuthor>
<navMap>
{points}
</navMap>
</ncx>
"""


def opf(cfg: dict, uid: str, modified: str, files: list, has_cover: bool) -> str:
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="css" href="css/book.css" media-type="text/css"/>']
    if has_cover:
        manifest.append('<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" '
                        'properties="cover-image"/>')
        manifest.append('<item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml"/>')
    spine = ['<itemref idref="cover" linear="yes"/>'] if has_cover else []
    for item_id, href in files:
        manifest.append(f'<item id="{item_id}" href="{href}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{item_id}"/>')
    meta = [f'<dc:identifier id="uid">{uid}</dc:identifier>',
            f'<dc:title id="title">{esc(cfg["title_en"])}</dc:title>',
            '<meta refines="#title" property="title-type">main</meta>']
    if cfg.get("subtitle_en"):
        meta += [f'<dc:title id="subtitle">{esc(cfg["subtitle_en"])}</dc:title>',
                 '<meta refines="#subtitle" property="title-type">subtitle</meta>']
    meta += [f'<dc:creator id="author">{AUTHOR}</dc:creator>',
             '<meta refines="#author" property="role" scheme="marc:relators">aut</meta>',
             '<meta refines="#author" property="file-as">Alita, Nessahan</meta>',
             f"<dc:language>{LANG}</dc:language>",
             f'<dc:date>{cfg["edition"]}</dc:date>',
             f'<meta property="dcterms:modified">{modified}</meta>']
    if cfg.get("series_en"):
        meta += [f'<meta property="belongs-to-collection" id="series">{esc(cfg["series_en"])}</meta>',
                 '<meta refines="#series" property="collection-type">series</meta>',
                 f'<meta refines="#series" property="group-position">{cfg["series_index"]}</meta>',
                 f'<meta name="calibre:series" content="{attr(cfg["series_en"])}"/>',
                 f'<meta name="calibre:series_index" content="{cfg["series_index"]}"/>']
    if has_cover:
        meta.append('<meta name="cover" content="cover-image"/>')
    nl = "\n"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="{LANG}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
{nl.join(meta)}
</metadata>
<manifest>
{nl.join(manifest)}
</manifest>
<spine toc="ncx">
{nl.join(spine)}
</spine>
</package>
"""


CONTAINER = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles>
<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
</rootfiles>
</container>
"""


def build(slug: str, draft: bool) -> None:
    cfg = load_book_config(slug)
    for key in ("title_en", "edition"):
        if key not in cfg:
            raise PipelineError(f"config/books/{slug}.json needs '{key}'")
    body_size = load_json(WORK_DIR / slug / "book.json")["metrics"]["body_size"]
    glossary = load_glossary(slug)
    # Chapter headings follow the original's predominant alignment (as in the PDF).
    aligns = []
    for chapter in chapter_ids(slug)[1:]:
        first = load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")["segments"][0]
        if first["type"] == "heading":
            aligns.append(first["style"]["align"])
    heading_class = "center" if aligns.count("center") >= len(aligns) / 2 else "left"

    files, toc, docs, book_text = [], [], {}, []
    for chapter in chapter_ids(slug):
        result = check_chapter(slug, chapter, glossary)
        if not result["complete"] or result["errors"]:
            msg = (f"chapter {chapter}: {result['segments_translated']}/{result['segments_total']} "
                   f"translated, {len(result['errors'])} QA errors")
            if not draft:
                raise PipelineError(msg + " (fix, or use --draft)")
            print(f"WARNING: {msg}")
        source = load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")["segments"]
        layout = load_json(WORK_DIR / slug / "chapters" / f"{chapter}.layout.json")
        for s in source:
            s["style"]["lines"] = len(layout[s["id"]]["lines"])
        en_path = TRANSLATIONS_DIR / slug / f"{chapter}.en.md"
        en = {e["id"]: e["text"] for e in parse_marked_md(en_path)} if en_path.exists() else {}
        en = {s["id"]: en.get(s["id"]) or s["text"] for s in source}
        book_text += [strip_markup(s["text"]) for s in source]
        body, title, _ = chapter_html(chapter, source, en, body_size, cfg["title_en"])
        href = f"text/ch{chapter}.xhtml"
        docs[href] = xhtml(title, body, "front" if chapter == "00" else heading_class)
        files.append((f"ch{chapter}", href))
        toc.append((href, title))

    entries = glossary_entries(slug, " ".join(book_text))
    docs["text/glossary.xhtml"] = xhtml("Glossary", glossary_html(entries), heading_class)
    files.append(("glossary", "text/glossary.xhtml"))
    toc.append(("text/glossary.xhtml", "Glossary"))

    uid = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"nessahan-alita-books/{slug}/en"))
    modified = modified_time(slug)
    cover = cover_jpeg(cfg)
    if cover:
        docs["text/cover.xhtml"] = xhtml(
            cfg["title_en"], f'<div class="cover"><img src="../images/cover.jpg" '
            f'alt="{attr(cfg["title_en"])}, by {AUTHOR}"/></div>')

    out = OUTPUT_DIR / slug / f"{slug}-en.epub"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    stamp = tuple(int(x) for x in re.findall(r"\d+", modified)[:6])

    def put(zf, name, data, compress=True):
        info = zipfile.ZipInfo(name, date_time=stamp)
        info.compress_type = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
        zf.writestr(info, data)

    with zipfile.ZipFile(tmp, "w") as zf:
        put(zf, "mimetype", "application/epub+zip", compress=False)  # first, uncompressed
        put(zf, "META-INF/container.xml", CONTAINER)
        put(zf, "OEBPS/content.opf", opf(cfg, uid, modified, files, bool(cover)))
        put(zf, "OEBPS/nav.xhtml", nav_html(cfg, toc, files[1][1] if len(files) > 2 else ""))
        put(zf, "OEBPS/toc.ncx", ncx(cfg, uid, toc))
        put(zf, "OEBPS/css/book.css", CSS)
        if cover:
            put(zf, "OEBPS/images/cover.jpg", cover, compress=False)
        for href, doc in docs.items():
            put(zf, f"OEBPS/{href}", doc)
    tmp.replace(out)
    print(f"glossary appendix: {len(entries)} terms")
    print(f"EPUB: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug", nargs="?")
    parser.add_argument("--all", action="store_true", help="every book in config/books/")
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    if not args.slug and not args.all:
        parser.error("give a slug or --all")
    slugs = sorted(p.stem for p in CONFIG_DIR.glob("*.json")) if args.all else [args.slug]
    try:
        for slug in slugs:
            print(f"== {slug}")
            build(slug, args.draft)
    except PipelineError as exc:
        fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
