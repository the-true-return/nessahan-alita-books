"""Quality checks for a generated EPUB (output/<slug>/<slug>-en.epub).

Checks:
  - container: "mimetype" first and uncompressed, META-INF/container.xml;
  - XML: every XHTML/OPF/NCX file is well-formed;
  - package: every manifest item exists and every file is in the manifest;
    spine, nav and NCX links resolve (file and #fragment);
  - footnotes: every note reference has its note, every note links back,
    no duplicate ids;
  - completeness: every translated segment appears in its chapter file, in
    order (body text and notes are checked separately), and the word counts
    match;
  - residue: no leftover comments, footnote markers, escaped tags or
    Portuguese text (except the Portuguese terms of the glossary, marked
    lang="pt-BR");
  - EPUBCheck (W3C validator), if Java and epubcheck.jar are available
    (pip install epubcheck);
  - previews: PNG of the opening pages, the first page with notes and the
    glossary, in output/<slug>/epub-preview/, for visual review.

Writes output/<slug>/epub-check.md. Exit code 1 if there are errors. If there
are none, publishes the EPUB to epubs/ as
"Nessahan Alita - <English title> (<edition> Edition).epub".

Usage:
  python tools/check_epub.py <slug>
  python tools/check_epub.py --all
"""

import argparse
import os
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from common import (
    CONFIG_DIR, ROOT, TRANSLATIONS_DIR, WORK_DIR, PipelineError, chapter_ids, fail,
    load_book_config, load_json, parse_marked_md, strip_markup, write_text_atomic,
)
from qa import looks_portuguese

OUTPUT_DIR = ROOT / "output"
EPUBS_DIR = ROOT / "epubs"
NS = {"x": "http://www.w3.org/1999/xhtml", "opf": "http://www.idpf.org/2007/opf",
      "ncx": "http://www.daisy.org/z3986/2005/ncx/",
      "c": "urn:oasis:names:tc:opendocument:xmlns:container"}
EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
RESIDUE_RE = re.compile(r"<!--|-->|\[\^|&lt;/?[ib]&gt;|</?[ib]>|¦|\bQUERY\b|\bTN:|\bKEEP:|\*\*\w|\w\*\*")


def norm(text: str) -> str:
    """Letters and digits only: immune to spacing and markup differences."""
    return re.sub(r"[^0-9a-z]", "", text.lower())


def words(text: str) -> int:
    return len(re.findall(r"[0-9A-Za-zÀ-ÿ’']+", text))


def published_name(cfg: dict) -> str:
    return f"Nessahan Alita - {cfg['title_en']} ({cfg['edition']} Edition).epub"


def element_text(el, skip_pt=False) -> str:
    """Text of an element. skip_pt leaves out lang="pt-BR" spans and italics
    (foreign words such as Latin "esse" are italicized). Table cells are
    and line breaks count as a space."""
    if skip_pt and (el.get("lang") == "pt-BR" or el.get(XML_LANG) == "pt-BR"
                    or el.tag == f"{{{NS['x']}}}i"):
        return el.tail or ""
    parts = [el.text or ""]
    for child in el:
        parts.append(element_text(child, skip_pt))
    if el.tag in (f"{{{NS['x']}}}td", f"{{{NS['x']}}}br"):
        parts.append(" ")
    parts.append(el.tail or "")
    return "".join(parts)


def epubcheck(path) -> tuple[str, list[str]]:
    try:
        import epubcheck as ec
        jar = os.path.join(os.path.dirname(ec.__file__), "epubcheck.jar")
    except ImportError:
        return "not run (pip install epubcheck)", []
    java = shutil.which("java")
    if not java:
        return "not run (Java not found)", []
    proc = subprocess.run([java, "-jar", jar, str(path)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    lines = (proc.stdout + proc.stderr).splitlines()
    problems = [ln for ln in lines if re.match(r"(FATAL|ERROR|WARNING)", ln)]
    summary = next((ln for ln in lines if ln.startswith("Messages:")), "no summary")
    return summary, problems


def previews(slug: str, path) -> list[str]:
    """Render a few pages with MuPDF's EPUB layout (approximates a reader)."""
    try:
        import pymupdf
    except ImportError:
        return []
    out_dir = OUTPUT_DIR / slug / "epub-preview"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    doc = pymupdf.open(str(path))
    doc.layout(width=420, height=640, fontsize=11)
    wanted = {0: "cover", 1: "title-page", 2: "title-page-2"}
    for i in range(doc.page_count):
        text = doc[i].get_text()
        # Notes page: the rule above the notes, and backlinks to earlier pages.
        if "first-notes" not in wanted.values() and i > 3 and doc[i].get_drawings() \
                and any(0 <= (ln.get("page") or i) < i for ln in doc[i].get_links()):
            wanted[i] = "first-notes"
        if text.lstrip().startswith("Glossary") and "glossary" not in wanted.values():
            wanted[i] = "glossary"
    wanted.setdefault(min(5, doc.page_count - 1), "chapter-page")
    names = []
    for i, label in sorted(wanted.items()):
        if i >= doc.page_count:
            continue
        name = f"p{i + 1:03d}-{label}.png"
        doc[i].get_pixmap(dpi=110).save(str(out_dir / name))
        names.append(name)
    return names


def check(slug: str) -> bool:
    cfg = load_book_config(slug)
    path = OUTPUT_DIR / slug / f"{slug}-en.epub"
    if not path.exists():
        raise PipelineError(f"EPUB not found: {path} (run tools/build_epub.py {slug})")
    errors, warnings, info = [], [], []
    zf = zipfile.ZipFile(path)
    names = zf.namelist()

    # Container
    first = zf.infolist()[0]
    if first.filename != "mimetype" or first.compress_type != zipfile.ZIP_STORED \
            or zf.read("mimetype") != b"application/epub+zip":
        errors.append("'mimetype' must be the first entry, uncompressed, 'application/epub+zip'")

    # XML well-formedness
    trees = {}
    for name in names:
        if name.endswith((".xhtml", ".opf", ".ncx", ".xml")):
            try:
                trees[name] = ET.fromstring(zf.read(name))
            except ET.ParseError as exc:
                errors.append(f"{name}: not well-formed XML: {exc}")
    if errors:
        return report(slug, cfg, path, errors, warnings, info, [], "not run", [])

    opf_path = trees["META-INF/container.xml"].find(".//c:rootfile", NS).get("full-path")
    base = posixpath.dirname(opf_path)
    opf = trees[opf_path]

    def resolve(href, rel_to):
        return posixpath.normpath(posixpath.join(posixpath.dirname(rel_to), unquote(href)))

    # Metadata
    md = opf.find("opf:metadata", NS)
    for tag in ("identifier", "title", "language", "creator"):
        if md.find(f"{{http://purl.org/dc/elements/1.1/}}{tag}") is None:
            errors.append(f"OPF metadata: missing dc:{tag}")
    if md.find("opf:meta[@property='dcterms:modified']", NS) is None:
        errors.append("OPF metadata: missing dcterms:modified")

    # Manifest <-> files
    items = {i.get("id"): i for i in opf.find("opf:manifest", NS)}
    manifest_files = set()
    for item in items.values():
        target = resolve(item.get("href"), opf_path)
        manifest_files.add(target)
        if target not in names:
            errors.append(f"manifest item missing from the archive: {target}")
    for name in names:
        if name not in manifest_files and name not in ("mimetype", "META-INF/container.xml", opf_path):
            errors.append(f"file not in the manifest: {name}")
    spine = [items[r.get("idref")] for r in opf.find("opf:spine", NS) if r.get("idref") in items]
    if len(spine) != len(opf.find("opf:spine", NS)):
        errors.append("spine references an unknown manifest id")

    # Ids per document, and link resolution
    ids = {name: {el.get("id") for el in tree.iter() if el.get("id")}
           for name, tree in trees.items() if name.endswith(".xhtml")}
    for name, tree in trees.items():
        if not name.endswith(".xhtml"):
            continue
        all_ids = [el.get("id") for el in tree.iter() if el.get("id")]
        dup = {i for i in all_ids if all_ids.count(i) > 1}
        if dup:
            errors.append(f"{name}: duplicate ids {sorted(dup)}")
        for a in tree.iter(f"{{{NS['x']}}}a"):
            href = a.get("href", "")
            if href.startswith(("http:", "https:", "mailto:")):
                continue
            file_part, _, frag = href.partition("#")
            target = resolve(file_part, name) if file_part else name
            if target not in names:
                errors.append(f"{name}: broken link {href}")
            elif frag and frag not in ids.get(target, set()):
                errors.append(f"{name}: link to a missing anchor {href}")
    ncx = next((t for n, t in trees.items() if n.endswith(".ncx")), None)
    if ncx is not None:
        ncx_name = next(n for n in trees if n.endswith(".ncx"))
        for c in ncx.iter(f"{{{NS['ncx']}}}content"):
            if resolve(c.get("src").partition("#")[0], ncx_name) not in names:
                errors.append(f"toc.ncx: broken link {c.get('src')}")
    nav = next((resolve(i.get("href"), opf_path) for i in items.values()
                if "nav" in (i.get("properties") or "").split()), None)
    if nav is None:
        errors.append("no navigation document (properties=\"nav\")")
    else:
        toc_links = [a.get("href") for a in trees[nav].iter(f"{{{NS['x']}}}a")]
        info.append(f"table of contents: {len(toc_links)} entries")

    # Chapters: footnotes, completeness, residue
    total_src_words = total_epub_words = 0
    chapter_files = {posixpath.basename(resolve(i.get("href"), opf_path)): resolve(i.get("href"), opf_path)
                     for i in spine}
    for chapter in chapter_ids(slug):
        name = chapter_files.get(f"ch{chapter}.xhtml")
        if not name:
            errors.append(f"chapter {chapter}: no ch{chapter}.xhtml in the spine")
            continue
        tree = trees[name]
        body = tree.find("x:body", NS)
        notes = body.find("x:section[@class='notes']", NS)
        note_texts = {}
        if notes is not None:
            body.remove(notes)
            for aside in notes.iter(f"{{{NS['x']}}}aside"):
                if aside.get(EPUB_TYPE) != "footnote":
                    errors.append(f"{name}: note {aside.get('id')} lacks epub:type=footnote")
                back = aside.find(".//x:a[@role='doc-backlink']", NS)
                if back is None:
                    errors.append(f"{name}: note {aside.get('id')} has no backlink")
                note_texts[aside.get("id")] = norm(re.sub(r"^\s*\d+\.\s*", "", element_text(aside)))
        refs = [a for a in body.iter(f"{{{NS['x']}}}a") if a.get(EPUB_TYPE) == "noteref"]
        for a in refs:
            if a.get("href", "#")[1:] not in note_texts:
                errors.append(f"{name}: note reference {a.get('href')} without a note")
        if len(refs) != len(note_texts):
            errors.append(f"{name}: {len(refs)} note references but {len(note_texts)} notes")

        body_text = element_text(body)
        stream = norm(body_text)
        en = parse_marked_md(TRANSLATIONS_DIR / slug / f"{chapter}.en.md")
        src_ids = [s["id"] for s in load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")["segments"]]
        if [s["id"] for s in en] != src_ids:
            errors.append(f"chapter {chapter}: translation segments differ from the source")
        pos, missing = 0, []
        fn_expected = {}
        for seg in en:
            text = norm(strip_markup(seg["text"]))
            if seg["type"] == "footnote":
                fn_expected[f"fn{seg['fn']}"] = text
                continue
            found = stream.find(text, pos)
            if found < 0:
                missing.append(seg["id"])
            else:
                pos = found + len(text)
        if missing:
            errors.append(f"chapter {chapter}: segments missing or out of order: {missing[:10]}")
        for fid, text in fn_expected.items():
            if note_texts.get(fid) != text:
                errors.append(f"chapter {chapter}: note {fid} text differs from the translation")
        src_words = sum(words(strip_markup(s["text"])) for s in en)
        epub_words = words(body_text) + sum(
            words(element_text(a)) for a in (notes.iter(f"{{{NS['x']}}}aside") if notes is not None else []))
        # Note numbers appear twice in the EPUB (reference and note label) and
        # once in the translation markup.
        epub_words -= len(note_texts)
        total_src_words += src_words
        total_epub_words += epub_words
        if src_words != epub_words:
            warnings.append(f"chapter {chapter}: {src_words} words in the translation, {epub_words} in the EPUB")

    # Residue and Portuguese, in every content document
    keep = set()
    for chapter in chapter_ids(slug):
        for seg in parse_marked_md(TRANSLATIONS_DIR / slug / f"{chapter}.en.md"):
            for k in seg["keep"]:
                keep |= {w.strip().lower() for w in k.split(",")}
    for name, tree in trees.items():
        if not name.endswith(".xhtml"):
            continue
        raw = zf.read(name).decode("utf-8")
        body_raw = raw[raw.find("<body"):]
        for m in RESIDUE_RE.finditer(re.sub(r"<(/?[ib])>", "", body_raw)):
            errors.append(f"{name}: leftover markup {m.group(0)!r}")
        for el in tree.iter():
            if el.tag not in (f"{{{NS['x']}}}p", f"{{{NS['x']}}}h1", f"{{{NS['x']}}}h2", f"{{{NS['x']}}}td"):
                continue
            text = element_text(el, skip_pt=True)
            check_text = " ".join(w for w in text.split() if w.strip(".,;:()“”\"").lower() not in keep)
            if looks_portuguese(check_text):
                warnings.append(f"{name}: looks Portuguese: {text[:120]!r}")

    info.append(f"words: {total_src_words} in the translation, {total_epub_words} in the EPUB")
    summary, problems = epubcheck(path)
    if problems:
        errors += [f"EPUBCheck: {p}" for p in problems]
    pngs = previews(slug, path)
    return report(slug, cfg, path, errors, warnings, info, pngs, summary, problems)


def report(slug, cfg, path, errors, warnings, info, pngs, summary, problems) -> bool:
    lines = [f"# EPUB check: {cfg['title_en']}", "",
             f"- File: `{path.relative_to(ROOT).as_posix()}` ({path.stat().st_size // 1024} KB)",
             f"- EPUBCheck: {summary}",
             *[f"- {x}" for x in info],
             f"- Errors: {len(errors)}", f"- Warnings: {len(warnings)}", ""]
    if errors:
        lines += ["## Errors", ""] + [f"- {e}" for e in errors] + [""]
    if warnings:
        lines += ["## Warnings", ""] + [f"- {w}" for w in warnings] + [""]
    if pngs:
        lines += ["## Previews (output/%s/epub-preview/)" % slug, ""] + [f"- {n}" for n in pngs] + [""]
    ok = not errors
    if ok:
        EPUBS_DIR.mkdir(exist_ok=True)
        target = EPUBS_DIR / published_name(cfg)
        tmp = target.with_name(target.name + ".tmp")
        shutil.copyfile(path, tmp)
        os.replace(tmp, target)
        lines += [f"Published: `epubs/{target.name}`", ""]
    write_text_atomic(OUTPUT_DIR / slug / "epub-check.md", "\n".join(lines))
    print(f"{slug}: {len(errors)} errors, {len(warnings)} warnings; EPUBCheck: {summary}")
    for e in errors[:20]:
        print(f"  ERROR {e}")
    for w in warnings[:20]:
        print(f"  WARN  {w}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug", nargs="?")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.slug and not args.all:
        parser.error("give a slug or --all")
    slugs = sorted(p.stem for p in CONFIG_DIR.glob("*.json")) if args.all else [args.slug]
    try:
        results = [check(s) for s in slugs]
    except PipelineError as exc:
        fail(str(exc))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
