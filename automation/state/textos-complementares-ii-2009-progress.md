# Progress log: textos-complementares-ii-2009 (Textos Complementares II → Supplementary Texts II)

## Run 1 — 2026-10-24

- Started from scratch. Structure report: completeness OK, no warnings. Config `known_issues`: the Wile/Solution table (pp. 9–10) is already segmented as clean `table_row` segments (06-0003 to 06-0041; rows starting with `¦` continue the previous wile); translated cell by cell, separator count preserved. "Aforismos" (ch. 22) has ~45 short subheadings.
- Translated chapters 00–21 completely (front matter, Introduction, book chapters 1–20; 323 segments, ~12,450 source words).
- QA: chapters 00–21 all PASS, 0 errors, 0 warnings. Open items: 16 QUERY, 0 TN.
- Glossary: added as "proposed" (books limited to this slug): `magia sexual` → "sexual magic" (concept, with appendix fields), `ginásio psicológico` → "psychological gymnasium" (concept, with appendix fields), `trapaça(s)` → "swindle(s)" (expression).
- Decisions to keep consistent in chapter 22 (Aforismos):
  - TOC entries in 00 must match headings; the last TOC entry 00-0029 "On translations and printings" must match the heading "Sobre traduções e impressões" (p. 46, inside ch. 22).
  - "artimanha" → "wile"; "desarticular" → "dismantle"; "encurralamento/encurralante" → "cornering"; "espertinha(s)" → "sly one(s)"; "joguinhos" → "little games"; "trapaça" → "swindle"; "cafajeste" → "cad"; "vadia" → "tramp"; "apaixonamento simulado" → "feigned infatuation" (as in table 06-0027); "ultimatum" → "ultimatum"; "desejo da continuidade" → "desire for continuity"; "guerra da paixão" → "war of passion"; "paixão/paixões" → "passion(s)" (approved; QA warns otherwise); "blindagem" → "armor"; "infernização" → "torment"; "(rs)" → "(ha ha)".
- For a human:
  - 02-0002 "pegada" → "firm grip"; 03-0004 "agüentar o tranco" → "take the pounding"; 07-0009 "miguxo" → "bestie".
  - 04-0010 repeats 04-0003 verbatim in the original; translated identically.
  - 00-0027 TOC "20 Indo além" lacks the period; added.
  - 16 title "galanteios" → "compliments" (TOC 00-0022 matched).
- Next run: chapter 22 "Aforismos" (`status.py textos-complementares-ii-2009 --next 22 --words 1200`, 114 segments, ~2,800 words), then the final phase (QA --all, build_pdf, check_pdf, .done, CLAUDE.md).

## Run 2 — 2026-10-24

- Translated chapter 22 "Aforismos" completely (114 segments, ~2,800 source words) in two batches; heading 22-0111 matches TOC 00-0029.
- QA --all: all 23 chapters PASS, 0 errors, 0 warnings. Open items: 21 QUERY (5 new in ch. 22), 0 TN.
- Glossary: added `entrega unilateral` → "one-sided surrender" (proposed, this slug).
- Final phase: build_pdf OK (Glossary appendix, 17 terms); check_pdf PASS (46 pages, original 46; 0 errors, 0 warnings). Looked at previews of the title page, the Wile/Solution table with footnotes (p. 9), an Aphorisms page (p. 40, compared with original p. 40) and the glossary (p. 46). Published to `books/Nessahan Alita - Supplementary Texts II (2009 Edition).pdf`. Wrote `.done` and updated CLAUDE.md.
- For a human (ch. 22): 22-0019 "nos tomarem por aí" → "take us for a ride"; 22-0033 "revolta" → "resentment" (kept apart from "rebeldia" → "rebelliousness"); 22-0097 heading → "The irritation of doubt" (Peirce); 22-0102 "relatos e perguntas" → "accounts and questionnaires"; 22-0110 "desencarnação" → "discarnation". Note 22-0113: the author permits translating parts (chapters or passages) of the current versions, provided errors are not attributed to him; a full-book translation goes beyond that literal permission.
