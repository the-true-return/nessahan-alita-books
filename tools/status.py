"""Translation progress per chapter, and the next batch to translate.

Progress is derived from the files themselves (source segments, the .en.md
translation and the last QA result), so it is always accurate after an
interruption; nothing has to be updated by hand.

Usage:
  python tools/status.py <slug>                 progress table (+ translations/<slug>/progress.json)
  python tools/status.py <slug> --next <NN>     print the next batch of source segments
                                                not yet translated in chapter NN
  python tools/status.py <slug> --next <NN> --words 1200
"""

import argparse
import sys

from common import (
    REVIEW_DIR, TRANSLATIONS_DIR, WORK_DIR, PipelineError, chapter_ids, fail,
    load_json, marker, parse_marked_md, strip_markup, write_json_atomic,
)


def chapter_status(slug: str, chapter: str) -> dict:
    source = load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")
    en_path = TRANSLATIONS_DIR / slug / f"{chapter}.en.md"
    qa_path = REVIEW_DIR / slug / f"{chapter}.qa.json"
    by_id = {s["id"]: s for s in source["segments"]}
    translated = stale = 0
    if en_path.exists():
        for seg in parse_marked_md(en_path):
            src = by_id.get(seg["id"])
            if src and seg["text"]:
                translated += 1
                stale += seg["hash"] != src["hash"]
    qa = "-"
    if qa_path.exists():
        qa = load_json(qa_path)["status"]
        if en_path.exists() and en_path.stat().st_mtime > qa_path.stat().st_mtime:
            qa += " (outdated: re-run qa.py)"
    total = len(source["segments"])
    if not translated:
        state = "not started"
    elif translated < total:
        state = "in progress"
    else:
        state = "translated"
    return {"chapter": chapter, "title": source["title"], "segments": total,
            "translated": translated, "stale": stale, "state": state, "qa": qa}


def print_table(slug: str) -> None:
    rows = [chapter_status(slug, c) for c in chapter_ids(slug)]
    print(f"{'ch':<3} {'state':<12} {'done':>9}  {'qa':<28} title")
    for r in rows:
        done = f"{r['translated']}/{r['segments']}"
        flag = f" [{r['stale']} stale]" if r["stale"] else ""
        print(f"{r['chapter']:<3} {r['state']:<12} {done:>9}  {r['qa']:<28} {r['title'][:60]}{flag}")
    write_json_atomic(TRANSLATIONS_DIR / slug / "progress.json", {"book": slug, "chapters": rows})


def print_next(slug: str, chapter: str, max_words: int) -> None:
    source = load_json(WORK_DIR / slug / "chapters" / f"{chapter}.json")
    en_path = TRANSLATIONS_DIR / slug / f"{chapter}.en.md"
    done = set()
    if en_path.exists():
        done = {s["id"] for s in parse_marked_md(en_path) if s["text"]}
    batch, words = [], 0
    for seg in source["segments"]:
        if seg["id"] in done:
            continue
        n = len(strip_markup(seg["text"]).split())
        if batch and words + n > max_words:
            break
        batch.append(seg)
        words += n
    if not batch:
        print(f"Chapter {chapter} is fully translated. Run: python tools/qa.py {slug} {chapter}")
        return
    print(f"<!-- next batch: {slug} / {chapter} | {len(batch)} segments, {words} words | "
          f"append to translations/{slug}/{chapter}.en.md -->\n")
    for seg in batch:
        print(marker(seg))
        print(seg["text"])
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("slug")
    parser.add_argument("--next", metavar="NN", help="chapter id")
    parser.add_argument("--words", type=int, default=1200, help="batch size in source words")
    args = parser.parse_args()
    try:
        if args.next:
            print_next(args.slug, args.next, args.words)
        else:
            print_table(args.slug)
    except PipelineError as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()
