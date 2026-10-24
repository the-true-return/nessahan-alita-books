# Progress: Como lidar com mulheres → How to Deal with Women

Book prepared on 2026-10-24 (interactive session):
- Letter-spacing extraction bug fixed (tools/extract_book.py → extracted-fixed/).
- Segmented: 36 chapters, 1,531 segments, ~73,500 words, completeness 100%.
- PDF layout parameters measured and stored in config (A4, Times 11.7 pt, letters in Helvetica → Liberation Sans).
- Draft PDF build tested successfully.

## Runs

### Run 1 — 2026-10-23, ~23:20 onward
- Translated chapters 00–06 in full (front matter, Introduction, chapters 1–5): 382 segments, ~13,000 source words. All seven chapters QA **PASS**, 0 errors, 0 warnings.
- Open queries: 17 (00: 6, 02: 2, 03: 4, 06: 5); 1 TN (01-0021, the pre-concept/prejudice wordplay).
- Glossary: added as `proposed` `artimanha(s)` → wile(s), `horrorização` → horrification (concept, with appendix note), `vadia(s)` → tramp(s), `domínio (vs. dominação)` → dominance/mastery (concept, this book only, with appendix note).
- Things a human should look at:
  - **00-0014**: the author's notice explicitly forbids translating the book. Translated faithfully, but someone should confirm the English edition is authorized.
  - 02-0009/0010: "vadia(s)" rendered "tramp(s)" (the author's footnote relies on the "idle person" sense).
  - 03-0014: the film cited as "Conselheiro Amoroso (TENNANT, 2001)" is *Hitch* (2005); kept the year as in the original.
  - 03-0007: "Karen Salmanshon" corrected to Salmansohn; check against the bibliography in chapter 34.
  - 06-0065: "domínio" vs. "dominação": "dominance" in most places, "mastery" vs. "domination" in note 25. Decide whether to unify.
  - Quotations (Nietzsche, Ecclesiastes, Lévi) are translated from the author's Portuguese; each QUERY names the public-domain English version.
- Next run: start with chapter 07 ("6. As torturas psicológicas").
- Tooling note: long bash heredocs fail in this environment ("Parser aborted"); create files with Write and append with Edit.

### Run 2 — 2026-10-23, ~23:50 onward
- Translated chapters 07–12 in full (chapters 6–11 of the book: psychological tortures through "why they observe us"): 239 segments, ~12,600 source words. QA: 07 **WARN** (only "duplicate translation" for 07-0015/07-0020, two identical dictionary footnotes, correct as is); 08–12 **PASS**, 0 errors.
- Open queries this run: 12 (07: 2, 08: 1, 09: 2, 10: 4, 11: 3); 1 TN (08-0014, Nelson Rodrigues). Book total: 29 queries, 2 TNs.
- Glossary: added as `proposed` `trouxa(s)` → sucker(s); `desapaixonamento / desapaixonado` → freedom from passion / free of passion (concept, with appendix note); `alternância` → alternation (concept, with appendix note). Re-ran QA on 00–12 afterwards: no new warnings.
- Things a human should look at:
  - 07-0007: Goleman (*Emotional Intelligence*) quoted from the Portuguese edition; the English original is copyrighted, so the quotation is a back-translation from the author's Portuguese. 07-0009: Alberoni likewise.
  - 10-0011 (Machiavelli), 10-0021–0023 (Nietzsche, *Zarathustra*), 09-0040 (Proverbs 9:13), 11-0005 / 11-0039 (Lévi): translated from the author's Portuguese; QUERY names the public-domain English versions. "grifo meu" (emphasis mine) appears in 10-0023 and 11-0039, but the emphasis is not marked in the extracted text — check the PDF.
  - 11-0042: "Misterium Conjunctionis" corrected to *Mysterium Coniunctionis*.
  - 10-0006: "a fine pair of horns" for "colocar chifres" (cuckolding idiom); 10-0061: "letting him stew" for "cozinhar".
  - "domínio" kept as "dominance" throughout 07–12 (still pending the dominance/mastery decision from run 1).
- Next run: start with chapter 13 ("12. Como lidar com mulheres que fogem").
- Tooling note: shell loops with `$var` are blocked by the permission sandbox; run QA commands one per chapter, chained with `;`.

### Run 3: 2026-10-23 ~23:55 to 2026-10-24 ~00:30
- Translated chapters 13–19 in full (chapters 12–18 of the book: women who run away through "why it is important for us to be decisive men"): 187 segments, ~11,700 source words. QA: 13–15 and 17–19 **PASS**; 16 **WARN** (only length ratios for 16-0041/16-0053, explained below). 0 errors.
- Open queries this run: 12 (13: 1, 14: 1, 15: 1, 16: 7, 17: 2). Book total: 41 queries, 2 TNs.
- Glossary: added `fujona(s)` → runaway(s) as `proposed` (expression, this book only). Re-ran QA on 13–19 afterwards: no change.
- Things a human should look at:
  - **16-0041 / 16-0053 (segmentation error)**: the source segment for footnote 5 (16-0041) contains the opening of the Schopenhauer block quotation ("Os enganos que os desejos eróticos..."), which in the PDF (p. 114) begins the quotation after "A paixão é uma armadilha enganosa:". The translation moves that sentence to the start of 16-0053, where it belongs. Check the rebuilt PDF page.
  - 16-0051: "Platão, em Fédron": translated as *Phaedo*; it might be the *Phaedrus*.
  - 14-0013: "V.M. Samael Aun Weor" kept as "V.M." (Venerable Master).
  - 15-0008: another long note on "domínio" vs. "dominação" (dominance vs. domination; "domínio de si mesmo" → "mastery of oneself"). The dominance/mastery decision from run 1 is still pending.
  - 17-0014: "grifo meu" again, with no emphasis marked in the extracted text (same as 10-0023, 11-0039).
  - Nietzsche (13-0036, 16-0032–0036, 17-0014), Schopenhauer (16-0010, 16-0053), and Lévi (16-0011, 17-0016) are translated from the author's Portuguese; each QUERY names the public-domain English version.
  - 16-0017: Bible references kept as "II Samuel", "I Kings" (Roman numerals, as in the source).
- Next run: start with chapter 20 ("19. Como destroçar os joguinhos emocionais", 95 segments).
- Tooling note: short heredocs work in Bash, but long ones (or ones with certain characters) fail with "unexpected EOF"; use Write/Edit for large blocks.

### Run 4: 2026-10-24 ~00:00 to ~00:15
- Translated chapters 20–25 in full (book chapters 19–24: "How to Shatter Their Little Emotional Games" through "Observing Them Realistically"): 222 segments, ~14,700 source words. QA: 20–22, 24, 25 **PASS**; 23 **WARN** (only "duplicate translation" for the four identical Michaelis/Aurélio dictionary footnotes, correct as is). 0 errors.
- Open queries this run: 9 (20: 3, 22: 3, 23: 2, 24: 1); 1 TN (24-0008). Book total: 50 queries, 3 TNs.
- Glossary: added as `proposed` `inferno(s) mental(is)` → mental hell(s) and `inveja do pênis` → penis envy (both expressions, this book only). Re-ran QA on 09, 10, 17, 20–25 afterwards: no new warnings.
- Things a human should look at:
  - **23-0017**: the author writes "Segundo ela" about Caligaris (Contardo Calligaris was a man). Rendered "According to Caligaris" to avoid the wrong pronoun; spelling "Caligaris" kept as in the original. Check against the bibliography.
  - 24-0008 (TN): Brazilian folklore beings (saci, caipora, curupira, iara) kept as names; may need a translator's note in the English edition.
  - 20-0079: Matthew 5:41 quoted with "league" and "enemy" as in the author's Portuguese; QUERY gives the KJV text.
  - 22-0004–0006 (Schopenhauer, "On Women"), 23-0009/0010/0029 (Schopenhauer, 2004 anthology), 20-0074 (Schopenhauer), 20-0076 and 22-0013 (Lévi), 24-0003 (Harrison and Weiner, copyrighted, back-translated): translated from the author's Portuguese; QUERYs name the public-domain English versions where they exist.
  - 22-0007: "phalus erectus" corrected to "phallus erectus".
  - 24-0016 / 24-0017: "infernizações emocionais" rendered "emotional hell-raising" (as in ch. 11); earlier chapters (06, 13) vary. Not added to the glossary for that reason.
- Next run: start with chapter 26 ("25. Aprisionando-as a nós pelos sentimentos", 36 segments).
- Tooling note: Bash `for` loops with `$c` are blocked ("simple_expansion"); chain the QA commands with `;`.

### Run 5: 2026-10-24 ~00:15 to ~00:21
- Translated chapters 26–31 in full (book chapters 25–29 and Appendix 1, the interview): 213 segments, ~11,700 source words. QA: 26, 27, 29, 30, 31 **PASS**; 28 **WARN** (only the number check for "década de 90" → "1990s", explained in a QUERY). 0 errors.
- Open queries this run: 18 (26: 2, 27: 2, 28: 6, 29: 2, 31: 6); 1 TN (28-0034, Brazilian "motel"). Book total: 68 queries, 4 TNs.
- Glossary: added as `proposed` concepts (this book only, with appendix notes) `indefinição` → indefiniteness (35 occurrences; ch. 07 uses "vagueness", accepted in `match_en`) and `prostituição inconsciente` → unconscious prostitution. Re-ran QA on 07, 10, 13, 19, 20, 23, 26, 28, 31: no new warnings.
- Things a human should look at:
  - 31-0002: interview questions marked "P -" in the original rendered "Q:". Interviewer's questions vs. author's answers otherwise kept as separate segments.
  - 31-0043/0044: "fêmea fatal" rendered "fatal female" (approved term "female"); "femme fatale" is the alternative. Note: the QA's glossary check fails when a footnote call is glued to the term ("female[^9]" → "female9"); worked around by placing the call after a comma.
  - 31-0050: "vagabundas" → "sluts", kept distinct from "vadias" → "tramps".
  - 27-0005 / 28-0064: "mendigos encantados" wordplay rendered "Beggar Charmings".
  - Films cited by Brazilian titles: 27-0002 "Um Príncipe em Minha Vida" → *The Prince & Me*; 29-0011 "A Batalha de Riddick" → *The Chronicles of Riddick* (Riddick's line in 29-0010 is back-translated; check the English dialogue).
  - 28-0047: Nelson Rodrigues's play "Bonitinha, mas Ordinária" → "Pretty but Wicked" (no established English title).
  - Spelling corrections: 27-0006 Salmansohn; 28-0048 "kuhikuru" → Kuikuro; 31-0082 "Farrel" → Farrell (bibliography confirms).
  - Copyrighted works back-translated from the author's Portuguese: Johnson's *She* (28-0007), Ram Dass (28-0023), Calligaris (28-0050–0053); Schopenhauer (26-0016) with a QUERY naming Haldane and Kemp.
- Next run: start with chapter 32 ("Anexo 2. Correspondências", 161 segments; check the 5 footnotes matched to references a few pages away).

### Run 6: 2026-10-24 ~00:22 to ~00:35 (translation finished + final phase)
- Translated chapters 32–35 in full (Appendix 2: Correspondence, Conclusions, Bibliography, About the author): 288 segments, ~9,700 source words. QA for all four: **PASS**, 0 errors. Full-book QA (`--all`): 0 errors; WARN only in 07, 16, 23, 28 (already explained in earlier runs).
- The 5 footnotes the structure report flagged in the letters (22, 23, 26, 27, 28) were each checked: every one fits its reference. Noted in QUERYs (26, 27, 28) or visible from the text (22, 23).
- Open queries this run: 39 (32: 15, 34: 24). Book total: 107 queries, 4 TNs.
- Glossary: added as `proposed` concepts (all books, with appendix notes) `kundalini`, `Homem Autêntico` → Authentic Man, `humanóide` → humanoid.
- Final phase: PDF built (207 pages, glossary appendix with 29 terms); `check_pdf.py` **PASS**; published to `books/Nessahan Alita - How to Deal with Women (2008 Edition).pdf`. Previews checked: title page, the letters page with footnotes (p. 174), the run-in sentence (p. 191), the Glossary (p. 205).
- **Tool changes (please review):**
  - `tools/qa.py`: URLs (".com", ".br"…) and the city name "São Paulo" no longer count as Portuguese residue (the bibliography repeats "São Paulo" for city and publisher, which tripped the stopword check); the "identical to the source" error now applies only when the source looks Portuguese (English book titles such as *Manliness* are legitimately identical). No KEEP was added for Portuguese text. The one KEEP (`das`, 34-0097) is for the German original title.
  - `tools/check_pdf.py`: (1) the footnote search cursor never advanced, so identical short notes ("Spiritually.", dictionary notes) all matched the first one (p. 42) and produced 18 false "reference/note on different pages" errors; (2) small body text (letters, quotations at 9.7 pt) and notes (8.8 pt) are now searched in separate streams, because a small paragraph crossing a page break was split by that page's notes (8 false "not found" errors).
  - `tools/build_pdf.py`: a heading segment smaller than the body text is treated as a bold sentence misdetected as a heading and run into the next paragraph (only 32-0148, the author's bold sentence ending in "sex.[^33]", which had rendered as a centered heading).
  - After these changes, *Magnetism in Social Relations* was rebuilt and re-checked: **PASS**, 56 pages (was 55). Its Glossary appendix now also includes "alternation" and "freedom from passion" (`"*"` concepts added in runs 1–2 that occur in that book), so the PDF in `books/` was republished with 30 terms. Confirm this is wanted.
- Things a human should look at:
  - 32-0021, 0048, 0064, 0088, 0125, 0136 and note 26: e-mail dates converted from day/month to month/day ("10/8/2004" → "8/10/2004"). The alternative is to keep the timestamps verbatim.
  - 32-0023 ff.: the author's ironic "a senhorita" / "a senhora" rendered "young lady" / "madam".
  - 32-0031: "kundartiguador" kept (Samael Aun Weor's term; some English editions use "Kundabuffer").
  - 32-0084: "animals do not speak Portuguese" kept literally (the joke depends on it).
  - 23-0017 (fixed this run): the bibliography shows the author is **Eliana** Calligaris, so "Segundo ela" is now "According to her" (run 4 had assumed Contardo Calligaris).
  - 34 (bibliography): titles of the Brazilian editions translated into English, using the established English title where one exists; each QUERY gives the original/English title. Name spellings corrected (Crhistina, Johan, Oliveria, Gehard, Theodosios, Salmanshon, Shanon, "David" Goleman → Daniel). Spanish-language editions (Freud/Breuer, Jung, Nietzsche) also got English titles.
  - **00-0014** (from run 1): the author's notice forbids translating the book. Someone must confirm the English edition is authorized before it is distributed.
