# Progress log: textos-complementares-2008 (Textos Complementares → Supplementary Texts)

## Run 1 — 2026-10-24 ~08:45

- Started from scratch. Config `known_issues`: many short bold body-size subheadings (chapter "1. Aprofundamentos" has ~40 of them; all segmented as headings and translated as such). Structure report: completeness OK, no warnings.
- Translated chapters 00–19 completely (front matter, Introduction, book chapters 1–18; 340 segments, ~12,600 source words).
- QA: chapters 00–19 all PASS, 0 errors, 0 warnings.
- Open items: 16 QUERY, 0 TN.
- Glossary: added as "proposed" `tríade sinistra` → "Dark Triad" (concept, with appendix fields), `níveis de aproximação` → "levels of approach" (concept, with appendix fields), `infernização` → "torment(s)" (expression).
- Decisions to keep consistent in later chapters:
  - Chapter titles in the TOC (00-0027..0031) must match the headings: 19. "On enchantment", 20. "On the revolt against reality", 21. "Passionate love and lust", 22. "Reinforcing the pillars of the theory", "Contraindications".
  - "Johnasson" → "Jonason" (QUERY in 08-0004; ch. 22 segments 23-0009/23-0010 also say "Johnasson"/"Peter Johnasson": correct to "Jonason" and refer to the query). "tríade sinistra" → "Dark Triad".
  - "Reflexões Masculinas" (23-0010) → "Masculine Reflections on Woman and Love" (full title, glossary).
  - "espertinha(s)" → "sly one(s)"; "joguinhos" → "little games"; "encurralamento" → "cornering"; "fujona" → "runaway"; "cafajestes" → "cads"; "desapaixonar" → "free from passion"; "blindagem" → "armor"; "impressionismo" → "impressionism"; "comportamento ambíguo" → "ambiguous behavior"; "guerra da paixão" → "war of passion".
- For a human:
  - 06-0009: footnote glosses the English term "battered man syndrome" in Portuguese; rendered as an English gloss ("That is, the 'syndrome of the mistreated man.'").
  - 02-0102: pun "desgraçados" (deprived of Grace) rendered "dis-graced wretches".
  - 02-0081: "O Imbecil Coletivo" has no established English title.
- Next run: start at chapter 20 (`status.py textos-complementares-2008 --next 20`), then 21–23 (~2,800 words), then the final phase.

## Run 2 — 2026-10-24 ~08:47

- Translated chapters 20–23 (book chapters 19–22 + "Contraindications"; 47 segments, ~2,800 source words). Book complete: 373 segments.
- QA `--all`: every chapter PASS, 0 errors, 0 warnings. Open items: 21 QUERY, 0 TN.
- Glossary: added as "proposed" `luxúria / luxurioso` → "lust / lustful" and `passionalismo` → "passionalism" (both `expression`). Re-ran QA on the other finished books: no new warnings.
- Final phase: `build_pdf.py` OK (glossary appendix: 18 terms); `check_pdf.py` PASS (59 pages, 0 errors, 0 warnings); published to `books/Nessahan Alita - Supplementary Texts (2008 Edition).pdf`. Checked previews of title page, contents, footnote page (p. 54) and glossary (p. 58); contents compared with the original.
- For a human:
  - 22-0005: "Eric From" corrected to "Erich Fromm".
  - 22-0013: Rabolú's "Morte em Marcha" rendered "Death in Motion" (no confirmed English title); "V.M." kept.
  - 21-0004: idiom "esmurra facas" (dar murro em ponta de faca) kept as an image: "beats his fists against knife points".
  - 20-0003: "molecas" → "brats".
  - 23-0009/23-0010: "Johnasson" → "Jonason"; short title "Reflexões Masculinas" → full English title.
