# Unattended translation run

You are running unattended (no human is watching, nobody can answer questions).
Each run continues where the previous one stopped. Work carefully, then stop
cleanly so the next run can resume.

Book for this job: **{{SLUG}}** ("{{TITLE_PT}}" → "{{TITLE_EN}}").

## Before anything

1. Read `CLAUDE.md`, `translation-rules.md` and `automation/state/{{SLUG}}-progress.md`
   (the log of previous runs; create it if missing).
2. Run `pymupdf-venv/Scripts/python.exe tools/status.py {{SLUG}}` to see where things stand.

## Hard rules

- Never run `tools/segment.py` (it would renumber the segments).
- Never modify `portuguese-original-pdf/`, `extracted/`, `extracted-fixed/`, `work/`,
  `config/`, or another book's translations.
- Nothing may stay in Portuguese. Do not exempt text from QA; translate it.
- Never ask questions: record doubts as `<!-- QUERY: ... -->` in the segment.
- Follow `translation-rules.md` and the glossary exactly (approved terms are
  mandatory; proposed terms are the default). Keep the author's voice and tone,
  including when the content is polemical: translate faithfully, without softening,
  endorsing or commenting.
- Distinguish the author's text from readers' letters and interview questions
  (those segments are in a different font in the original; just translate them).
- Read `known_issues` in `config/books/{{SLUG}}.json` and the warnings in
  `work/{{SLUG}}/structure-report.md` before starting; when you reach a segment
  they mention (e.g. a footnote matched to a reference pages away), check it
  and add a QUERY if something does not fit.
- Segments of type `table_row` hold table cells separated by ` ¦ `: translate
  each cell and keep exactly the same number of `¦` (a row starting with `¦`
  continues the previous row).
- Do not run git: the runner commits and pushes when the book is finished.
- Other books already finished are listed in `automation/state/*.done`. Reuse
  their glossary decisions for consistency across the author's work.

## Work loop (translation phase)

Repeat until you have translated about **12,000 source words in this run**, then stop:

1. `pymupdf-venv/Scripts/python.exe tools/status.py {{SLUG}} --next NN --words 1200`
   for the first chapter that is not fully translated (in order 00, 01, 02, ...).
2. Translate the batch and append it to `translations/{{SLUG}}/NN.en.md`
   (create the file with the header `<!-- book: {{SLUG}} | chapter: NN | en-US -->`
   if needed). Copy every marker line exactly. Use curly quotes and apostrophes.
3. `pymupdf-venv/Scripts/python.exe tools/qa.py {{SLUG}} NN` and fix every error
   before the next batch. Review warnings; fix real problems.
4. When a chapter is complete, read the end of the previous chapter's
   translation for continuity before starting the next one, and add recurring
   new terms to `glossary/glossary.json` as `"status": "proposed"`.

Before stopping, append a short entry to `automation/state/{{SLUG}}-progress.md`:
date/time, chapters and segments done this run, open queries count, anything a
human should look at.

## Final phase (only when every chapter shows `translated` and QA `pass`/`warn`)

1. `pymupdf-venv/Scripts/python.exe tools/qa.py {{SLUG}} --all` (must have no errors).
2. Glossary appendix: `pymupdf-venv/Scripts/python.exe tools/build_pdf.py {{SLUG}}`.
   If it fails because concepts lack English notes, add `display_en`,
   `display_pt` and `note_en` for them in `glossary/glossary.json` (style of the
   existing notes) and build again.
3. `pymupdf-venv/Scripts/python.exe tools/check_pdf.py {{SLUG}}`. Fix real
   problems (in translations first; touch `tools/` only if unavoidable, and then
   rebuild and re-check every already finished book, i.e. `magnetismo-relacoes-sociais-2008`,
   `como-lidar-com-mulheres-2008` and each slug with a `.done` file, so they
   all still pass). Look at a few previews in `output/{{SLUG}}/preview/`
   (title page, a page with footnotes, any table, the glossary) and compare
   one body page with the original PDF for fidelity.
4. When the check passes (it publishes the PDF to `books/`), write
   `automation/state/{{SLUG}}.done` with a summary: pages, segments, open
   queries, glossary terms added, and the path of the PDF in `books/`.
   Also update the "Estado atual" section of `CLAUDE.md` with one line saying the
   book is translated and awaiting human review.
