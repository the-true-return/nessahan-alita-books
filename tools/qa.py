"""Quality checks for translated chapters.

Compares work/<slug>/chapters/NN.json (source) with
translations/<slug>/NN.en.md (translation) and writes, under review/<slug>/:

  NN.qa.md          human-readable report
  NN.qa.json        machine-readable result (used by status.py)
  NN.bilingual.md   source and translation side by side, for human review

Usage:
  python tools/qa.py <slug> <NN> [<NN> ...]
  python tools/qa.py <slug> --all        (every chapter that has a translation)

Exit code 1 if any chapter has errors.
"""

import argparse
import collections
import datetime
import re
import sys

from common import (
    GLOSSARY_FILE, REVIEW_DIR, TRANSLATIONS_DIR, WORK_DIR, PipelineError, fail,
    load_json, parse_marked_md, strip_markup, write_json_atomic, write_text_atomic,
)

PT_STOPWORDS = {
    "que", "não", "uma", "para", "com", "dos", "das", "pelo", "pela", "pelos",
    "pelas", "mas", "também", "então", "isso", "isto", "este", "esta", "esse",
    "essa", "seus", "suas", "muito", "quando", "porque", "ele", "ela", "eles",
    "elas", "nós", "você", "mulher", "homem", "mulheres", "homens", "são",
    "está", "entre", "sobre", "sem", "mais", "como", "nos", "nas", "aos",
}
PT_DIACRITIC_WORD = re.compile(r"\b[a-zà-ÿ]*[ãõçâêôáíóúà][a-zà-ÿ]*\b")
# Not Portuguese residue: URLs ("epoca.com.br") and the city name São Paulo,
# which bibliographies repeat (city and publisher names are kept).
NOT_RESIDUE_RE = re.compile(r"\S+\.(?:com|br|org|net)\S*|\bSão Paulo\b", re.IGNORECASE)


def looks_portuguese(text: str) -> bool:
    words = re.findall(r"[a-zà-ÿ]+", NOT_RESIDUE_RE.sub(" ", text).lower())
    return any(w in PT_STOPWORDS for w in words) or bool(PT_DIACRITIC_WORD.search(text))
REF_RE = re.compile(r"\[\^(\d+)\]")
NUMBER_RE = re.compile(r"\d+")


def load_glossary(slug: str) -> list[dict]:
    if not GLOSSARY_FILE.exists():
        return []
    entries = load_json(GLOSSARY_FILE)["entries"]
    return [e for e in entries
            if e.get("status") in ("approved", "do_not_translate")
            and ("*" in e.get("books", ["*"]) or slug in e.get("books", []))]


def forms_regex(forms: list[str]) -> re.Pattern:
    alts = "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
    return re.compile(rf"(?<![\w-])(?:{alts})(?![\w-])", re.I)


def numbers(text: str) -> collections.Counter:
    """Digit sequences in the text, ignoring footnote references."""
    return collections.Counter(NUMBER_RE.findall(REF_RE.sub("", text)))


def tags_balanced(text: str) -> bool:
    stack = []
    for closing, tag in re.findall(r"<(/?)([ib])>", text):
        if not closing:
            stack.append(tag)
        elif not stack or stack.pop() != tag:
            return False
    return not stack


def check_chapter(slug: str, chapter: str, glossary: list[dict]) -> dict:
    source = load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")
    en_path = TRANSLATIONS_DIR / slug / f"{chapter}.en.md"
    errors, warnings = [], []
    if not en_path.exists():
        raise PipelineError(f"No translation file: {en_path}")

    src_segments = source["segments"]
    src_by_id = {s["id"]: s for s in src_segments}
    en_segments = parse_marked_md(en_path)

    # --- structure: ids, order, duplicates, stale hashes
    seen = collections.Counter(s["id"] for s in en_segments)
    for seg_id, count in seen.items():
        if count > 1:
            errors.append(f"{seg_id}: appears {count} times in the translation")
        if seg_id not in src_by_id:
            errors.append(f"{seg_id}: not in the source (extra segment)")
    en_by_id = {s["id"]: s for s in en_segments}
    # Segments after the last translated one are "pending" (batch not done
    # yet); a gap before it means something was skipped.
    src_ids = [s["id"] for s in src_segments]
    last = max((src_ids.index(s["id"]) for s in en_segments if s["id"] in src_by_id), default=-1)
    missing = [i for i in src_ids[:last + 1] if i not in en_by_id]
    pending = src_ids[last + 1:]
    for seg_id in missing:
        errors.append(f"{seg_id}: missing from the translation (skipped)")
    order = [s["id"] for s in en_segments if s["id"] in src_by_id]
    expected = [s["id"] for s in src_segments if s["id"] in en_by_id]
    if order != expected:
        errors.append("segments are out of order")

    translated_texts = collections.defaultdict(list)
    queries, notes = [], []
    for en in en_segments:
        src = src_by_id.get(en["id"])
        if src is None:
            continue
        sid = en["id"]
        queries += [(sid, q) for q in en["queries"]]
        notes += [(sid, n) for n in en["notes"]]
        if en["hash"] != src["hash"]:
            errors.append(f"{sid}: source changed since translation (hash {en['hash']} "
                          f"!= {src['hash']}); re-check this segment")
        if en["type"] != src["type"] or en["fn"] != src.get("fn"):
            errors.append(f"{sid}: marker type/footnote number differs from the source")
        pt_text, en_text = src["text"], en["text"]
        if not en_text:
            errors.append(f"{sid}: empty translation")
            continue
        pt_plain, en_plain = strip_markup(pt_text), strip_markup(en_text)
        # A source already in English (e.g. an English book title) may stay identical.
        if en_plain == pt_plain and len(pt_plain.split()) > 3 and looks_portuguese(pt_plain):
            errors.append(f"{sid}: identical to the source (untranslated?)")
        translated_texts[en_plain].append(sid)

        # Footnote references must survive exactly.
        if collections.Counter(REF_RE.findall(pt_text)) != collections.Counter(REF_RE.findall(en_text)):
            errors.append(f"{sid}: footnote references differ: source {REF_RE.findall(pt_text)} "
                          f"vs translation {REF_RE.findall(en_text)}")
        if not tags_balanced(en_text):
            errors.append(f"{sid}: unbalanced <i>/<b> tags")
        for tag in ("i", "b"):
            if pt_text.count(f"<{tag}>") != en_text.count(f"<{tag}>"):
                warnings.append(f"{sid}: <{tag}> count differs (source {pt_text.count(f'<{tag}>')}, "
                                f"translation {en_text.count(f'<{tag}>')})")

        if '"' in en_plain or "'" in en_plain:
            warnings.append(f"{sid}: straight quotes or apostrophes; use curly “ ” ‘ ’")
        if numbers(pt_text) != numbers(en_text):
            warnings.append(f"{sid}: numbers differ: source {sorted(numbers(pt_text).elements())} "
                            f"vs translation {sorted(numbers(en_text).elements())}")

        if len(pt_plain) >= 100:
            ratio = len(en_plain) / len(pt_plain)
            if not 0.75 <= ratio <= 1.35:
                warnings.append(f"{sid}: length ratio {ratio:.2f} (check for omissions or additions)")

        # Nothing may stay in Portuguese: residue is an error. KEEP lists
        # foreign (non-Portuguese) words with accents that are allowed.
        allowed = {w.strip().lower() for k in en["keep"] for w in k.split(",")}
        words = re.findall(r"[a-zà-ÿ]+", NOT_RESIDUE_RE.sub(" ", en_plain).lower())
        pt_hits = [w for w in words if w in PT_STOPWORDS and w not in allowed]
        diacritic = [w for w in PT_DIACRITIC_WORD.findall(en_plain) if w.lower() not in allowed]
        if len(pt_hits) >= 2 or diacritic:
            errors.append(f"{sid}: Portuguese left in the translation: "
                          f"{sorted(set(pt_hits + diacritic))}")

        for entry in glossary:
            if forms_regex(entry["match_pt"]).search(pt_plain) and \
                    not forms_regex(entry["match_en"]).search(en_plain):
                warnings.append(f"{sid}: glossary: '{entry['term_pt']}' should be rendered as "
                                f"'{entry['term_en']}'")

    for text, ids in translated_texts.items():
        if len(ids) > 1 and len({strip_markup(src_by_id[i]['text']) for i in ids}) > 1:
            warnings.append(f"duplicate translation for different source segments: {', '.join(ids)}")

    done = sum(1 for s in en_segments if s["id"] in src_by_id and s["text"])
    return {
        "book": slug,
        "chapter": chapter,
        "title": source["title"],
        "checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "segments_total": len(src_segments),
        "segments_translated": done,
        "complete": done == len(src_segments),
        "pending_from": pending[0] if pending else None,
        "status": "fail" if errors else ("in_progress" if pending else ("warn" if warnings else "pass")),
        "errors": errors,
        "warnings": warnings,
        "queries": [{"segment": s, "text": q} for s, q in queries],
        "translator_notes": [{"segment": s, "text": n} for s, n in notes],
        "_source": src_segments,
        "_en": en_by_id,
    }


def write_reports(result: dict) -> None:
    slug, chapter = result["book"], result["chapter"]
    out = REVIEW_DIR / slug
    md = [f"# QA report: {slug} / chapter {chapter}", "",
          f"**{result['title']}**  ", f"Checked: {result['checked_at']}  ",
          f"Status: **{result['status'].upper()}**  ",
          f"Translated: {result['segments_translated']}/{result['segments_total']} segments  ",
          f"Next pending segment: {result['pending_from'] or 'none'}", ""]
    for label, key in (("Errors (must fix)", "errors"), ("Warnings (review)", "warnings")):
        md += [f"## {label}", ""] + ([f"- {x}" for x in result[key]] or ["- none"]) + [""]
    md += ["## Open questions for human review", ""]
    md += [f"- **{q['segment']}**: {q['text']}" for q in result["queries"]] or ["- none"]
    md += ["", "## Proposed translator's notes (not in the text)", ""]
    md += [f"- **{n['segment']}**: {n['text']}" for n in result["translator_notes"]] or ["- none"]
    write_text_atomic(out / f"{chapter}.qa.md", "\n".join(md) + "\n")

    public = {k: v for k, v in result.items() if not k.startswith("_")}
    write_json_atomic(out / f"{chapter}.qa.json", public)

    bi = [f"# Bilingual review: {slug} / chapter {chapter}", "", f"**{result['title']}**", ""]
    for src in result["_source"]:
        en = result["_en"].get(src["id"])
        label = src["type"] + (f" {src['fn']}" if src.get("fn") else "")
        bi += [f"### {src['id']} · {label}", "", "> " + src["text"], "",
               en["text"] if en and en["text"] else "_(not translated)_", ""]
        if en:
            bi += [f"- **QUERY:** {q}" for q in en["queries"]]
            bi += [f"- **TN:** {n}" for n in en["notes"]]
            if en["queries"] or en["notes"]:
                bi.append("")
    write_text_atomic(out / f"{chapter}.bilingual.md", "\n".join(bi) + "\n")


def write_book_report(slug: str, results: list[dict]) -> None:
    """One page for the human reviewer: status per chapter and every open
    question / proposed note in the book."""
    md = [f"# Book QA summary: {slug}", "",
          "| ch | title | status | translated | errors | warnings | queries |",
          "|---|---|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['chapter']} | {r['title']} | {r['status']} | "
                  f"{r['segments_translated']}/{r['segments_total']} | {len(r['errors'])} | "
                  f"{len(r['warnings'])} | {len(r['queries'])} |")
    md += ["", "## Open questions", ""]
    for r in results:
        md += [f"- **{q['segment']}**: {q['text']}" for q in r["queries"]]
    md += ["", "## Proposed translator's notes", ""]
    notes = [f"- **{n['segment']}**: {n['text']}" for r in results for n in r["translator_notes"]]
    md += notes or ["- none"]
    write_text_atomic(REVIEW_DIR / slug / "book-qa.md", "\n".join(md) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug")
    parser.add_argument("chapters", nargs="*")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    try:
        if args.all:
            chapters = sorted(p.name.split(".")[0] for p in (TRANSLATIONS_DIR / args.slug).glob("*.en.md"))
        else:
            chapters = args.chapters
        if not chapters:
            raise PipelineError("No chapters given (pass chapter ids or --all).")
        glossary = load_glossary(args.slug)
        failed = False
        results = []
        for chapter in chapters:
            result = check_chapter(args.slug, chapter, glossary)
            write_reports(result)
            results.append(result)
            failed |= result["status"] == "fail"
            print(f"{chapter}: {result['status'].upper()} - "
                  f"{result['segments_translated']}/{result['segments_total']} translated, "
                  f"{len(result['errors'])} errors, {len(result['warnings'])} warnings, "
                  f"{len(result['queries'])} queries -> review/{args.slug}/{chapter}.qa.md")
        if args.all:
            write_book_report(args.slug, results)
            print(f"Book summary -> review/{args.slug}/book-qa.md")
        sys.exit(1 if failed else 0)
    except PipelineError as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()
