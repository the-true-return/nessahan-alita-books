# Progress log: profano-feminino-2008 (O Profano Feminino → The Profane Feminine)

## Run 1 — 2026-10-24 ~03:40

- Started from scratch. Read config `known_issues` (bold body-size subheadings in "Esclarecimentos adicionais", ch. 18) and structure report (completeness OK, no warnings).
- Translated chapters 00–09 completely (232 segments, ~11,400 source words): front matter, Introduction, chapters 1–8.
- QA: all ten chapters PASS, 0 errors, 0 warnings.
- Open items: 27 QUERY, 0 TN.
- Glossary: added as "proposed" `duplicidade de sentimentos` → "duplicity of feelings" (concept, with appendix fields) and `pilantragem` → "crookedness / crooked trick" (expression).
- Decisions to keep consistent in later chapters:
  - "fêmeas fatais" → "fatal females" (approved glossary "female"), 03-0006, 03-0012.
  - "Além do homem" → "Beyond-Man" (02-0015, QUERY; Masculine Reflections used "Overman").
  - "escracho" → "dressing-down"; "ficar" → "hooking up"; "banana" → "wimp"; "otário" → "chump".
  - Chapter titles in the TOC (00-0025..0043) must match the chapter headings when translated: 9. "Shattering the little emotional hells", 10. "The strategy of attacking masculinity", 12. "When they leave", 13. "Why they reject sex without love", 14. "Love in its various forms", 15. "Dismantling ambiguity", 16. "Preserving the thin thread and moving forward", 17. "Additional clarifications", "Conclusions". Chapter 11's heading differs from the TOC in the original ("The weakening of suspicions" vs. TOC "How they undermine distrust"; QUERY in 00-0036).
- For a human:
  - 00-0014: the author's notice explicitly forbids translating the book; needs a decision before distribution (as with the other volumes).
  - 03-0009: "74% … the remaining 24%" kept as in the original.
  - 09-0031: "Slayne … Path Mills" corrected to Sláine / Pat Mills (QUERY); the quoted lines are back-translated from the Portuguese.
- Next run: start at chapter 10 (`status.py profano-feminino-2008 --next 10`).

## Run 2 — 2026-10-24 ~03:46

- Translated chapters 10–17 completely (book chapters 9–16; 111 segments) and chapter 18 ("17. Additional clarifications") segments 18-0001 to 18-0102 (102 of 150). ~12,400 source words.
- QA: chapters 00–17 PASS (0 errors, 0 warnings); 18 in progress, 0 errors, 0 warnings.
- Open items: 35 QUERY in total (8 new this run), 1 TN (10-0034, "inferno astral" → "astral hell").
- Glossary: added as "proposed" `amor consciente` → "conscious love" and `Sagrado Feminino / Profano Feminino` → "Sacred Feminine / Profane Feminine" (both concepts, with appendix fields).
- Decisions to keep consistent:
  - "joguinhos infernizantes" → "hellish little games" (as in The War of Passion); "atitudes-espelho" → "mirror actions"; "blindagem (psíquica)" → "(psychic) armor"; "machista" → "chauvinist"; "sedutólogos" → "seductologists"; "infra-sexuais" → "infra-sexuals"; "(rs)" → "(ha ha)" (QUERY 17-0007).
  - Lalande quotations: the author's own translation from the French; rendered from his Portuguese, "tradução minha" → "my translation". Encyclopedias: "NEW BARSA ENCYCLOPEDIA", "GREAT LAROUSSE CULTURAL ENCYCLOPEDIA"; keep the same in the bibliography (chapter 20).
  - Samael titles: "Treatise of Revolutionary Psychology", "The Perfect Matrimony"; "Dialética da Razão Objetiva" → "Dialectic of Objective Reason" (QUERY 15-0002, no established English title found).
- For a human: 15-0009 (Fromm's categories as the author lists them, not matching the English original's headings); 10-0011 (Schopenhauer line, source not identified).
- Next run: continue chapter 18 at 18-0103 (`status.py profano-feminino-2008 --next 18`), then 19–21, then the final phase.

## Run 3 — 2026-10-24

- Translated chapter 18 segments 18-0103 to 18-0150 (48) and chapters 19–21 (Conclusions, Bibliographical references, About the author; 34 segments). ~3,500 source words. Translation complete: 517/517 segments.
- QA `--all`: all 22 chapters PASS, 0 errors, 0 warnings. Totals: 42 QUERY, 1 TN (7 new queries this run: Lachelier and Spinoza title spellings, 19-0005 adjective string, bibliography entries 20-0002/0004/0006/0007).
- Glossary: added `centro emocional` → "emotional center(s)" (proposed concept, with appendix fields).
- Final phase: build_pdf OK (23 glossary terms in the appendix); check_pdf PASS, 88 pages, published to `books/Nessahan Alita - The Profane Feminine (2008 Edition).pdf`. Previews checked (title page, footnote page 79, bibliography p. 84, glossary p. 86); page 79 matches original p. 81 closely.
- Book finished: `automation/state/profano-feminino-2008.done` written, CLAUDE.md updated.
