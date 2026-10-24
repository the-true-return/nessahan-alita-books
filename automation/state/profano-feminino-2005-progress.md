# Progress log: profano-feminino-2005 (O Profano Feminino → The Profane Feminine, 2005 edition)

## Run 1 — 2026-10-24

- Started from scratch (translations dir only had `progress.json`). Read config `known_issues` (edition superseded by 2008; pdfFactory watermark, already dropped) and structure report (completeness OK, no warnings).
- Note: CLAUDE.md says not to translate this edition without a user decision; it is listed in `automation/queue.txt`, which was taken as that decision.
- Method: most 2005 paragraphs are identical to the 2008 edition (already translated, `profano-feminino-2008`). Segments whose Portuguese text is identical reuse the 2008 English verbatim (including its QUERYs); differing segments were translated individually against a word diff of 2005 vs 2008. Typical 2005 differences: extra "sempre" (always), "loucura" (→ "madness", where 2008 has "obsessão/confusão"), "humanóide(s)" (→ "humanoid(s)", glossary), "garotas" (→ "girls"), plus a few 2005-only sentences and footnotes (e.g. 02-0010, n=2 "gate-crashers").
- Translated chapters 00–10 completely (274 segments, ~14,000 source words): front matter, Introduction, chapters 1–9.
- QA: all eleven chapters PASS, 0 errors, 0 warnings.
- Open items: 25 QUERY, 0 TN.
- Glossary: no new terms (all terms already covered by entries used for the 2008 edition).
- For a human:
  - 00-0012: author’s notice forbids any alteration of the book’s "language or title" (this edition does not explicitly say "translate").
  - 00-0033: chapter 11 TOC title differs from its heading (same as 2008).
  - 03-0009: text cites "this month (July 2006)" in a book dated 2005 ("second edition"); kept as written. "74% … the remaining 24%" kept.
- Next run: start at chapter 11 (`status.py profano-feminino-2005 --next 11`); chapters 11–16 remain (~6,600 source words; chapter 15 "14. Esclarecimentos adicionais", 99 segments, likely has more 2005-only text). Then the final phase.

## Run 2 — 2026-10-24

- Translated chapters 11–16 (144 segments, ~6,600 source words), same method as run 1 (2008 English reused for identical segments; 44 differing segments translated individually, incl. the 2005-only "Clarification about homophobia" section, 15-0059..0076, footnotes 29–32).
- QA --all: 17 chapters PASS, 0 errors, 0 warnings. Open items: 26 QUERY, 0 TN (1 new: 15-0079 "Warren Farrel" → Farrell).
- Final phase: build_pdf OK (glossary appendix 19 terms, no notes missing); check_pdf first flagged p. 5 nearly empty (Introduction signature spilling over), fixed by tightening wording in 01-0006/01-0007; re-check PASS, 71 pages, 0 warnings. Previews checked (title page, footnote page, glossary) and a body page compared with the original.
- Published `books/Nessahan Alita - The Profane Feminine (2005 Edition).pdf`; wrote `profano-feminino-2005.done`; CLAUDE.md updated.
- Glossary: no new terms.
