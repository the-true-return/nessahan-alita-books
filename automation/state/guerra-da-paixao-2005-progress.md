# Progress: A Guerra da Paixão (guerra-da-paixao-2005)

### Run 1: 2026-10-24 (chapters 00–11)
- Translated chapters 00–11 in full: 246 segments, ~13,100 source words (slightly over the 12,000-word target so that chapter 11 could be finished). QA for every chapter: **PASS** with 0 errors, except 08 (**WARN**, 1 warning: 08-0002 has a length ratio of 0.74 because it is a list of nouns; checked, nothing is missing).
- Remaining: chapters 12–18 (125 segments, ~9,700 words), then the final phase (QA `--all`, PDF build/check, `.done`).
- Open queries: 14 QUERY, 0 TN (see `review/guerra-da-paixao-2005/NN.qa.md`).
- Glossary (all `proposed`): added `megera(s)` → shrew(s) (`"*"`) and `ilogicidade(s)` → illogicality (this book, with appendix notes); added this slug to `books` of `indefinição` and `continuidade (do interesse masculino)`.
- Conventions set in this run (keep them for chapters 12–18): "espertinha(s)" → "sly one(s)"/"sly woman"; "encurralantes/encurraladoras" → "cornering"; "castigo/castiguinho" → "punishment"/"little punishment"; "devolver as consequências" → "hand back the consequences"; "especular" → "mirror-like"; "desapaixonado" → "free of passion"; "bonzinho(s)" → "nice guy(s)"; "machista" → "male chauvinist"; "joguinhos infernais" → "hellish little games".
- Things a human should look at:
  - **00-0012**: the author’s notice forbids any alteration of the book’s "language or title"; confirm that the English edition is authorized (as for the other volumes).
  - 00-0003: subtitle "The Wiles and Cunning Tricks of Women in Love".
  - 06-0003 / 06-0005: authors cited without titles, "Cláudia Pacheco" and "Elane Calligaris" (the second is uncertain: maybe Contardo Calligaris); names kept as they are.
  - 10-0007: "Karen Salmanshon" → Salmansohn and "Ammy Shuterland" → Amy Sutherland (second identification to confirm).
  - 11-0028: "diga-lhe para nunca mais dizer a verdade" translated literally; it may be a slip in the original.
  - 08-0007: "pentalfa invertida" → "inverted pentagram".

### Run 2: 2026-10-24 ~03:30 (chapters 12–18 + final phase)
- Translated chapters 12–18 in full: 125 segments, ~9,700 source words. QA `--all`: 0 errors; every chapter PASS except 08 (WARN, known and checked).
- Headings of chapters 12–15 use sentence case, the same as the table of contents (00-0032…00-0037) and chapters 01–11.
- New QUERY items this run (6): 12-0016 ("a perde" = loses the war), 13-0015 ("canções psicológicas" → "psychological songs"), 13-0026 ("impressionismo" → "the wish to impress"; the proposed glossary term "impressionism" is limited to Masculine Reflections on Woman and Love), 15-0010 ("Eliane Calligaris", spelled "Elane" in 06-0005; probably Eliana Calligaris), 15-0013 (original says "location B" where the logic requires "location A"; translated "A"), 16-0002 ("insinuação" kept as "insinuation", as in the table of contents). Total open: 20 QUERY, 0 TN.
- Glossary: added `egoísmo sentimental` → "sentimental selfishness" (proposed, `"*"`, with appendix notes; already used that way in the other books). The appendix now also lists it in How to Deal with Women (207 → 208 pages) and Masculine Reflections on Woman and Love.
- Tool change: `tools/build_pdf.py` raises the page number (footer descent capped at `bottom − 30 − 1.3 × size`) because this book’s 12 pt page numbers fell 1.4 pt below the area check_pdf accepts. The result is unchanged for page numbers ≤10.1 pt. Magnetism in Social Relations, How to Deal with Women and Masculine Reflections on Woman and Love were rebuilt, re-checked (PASS) and republished.
- PDF: 98 pages (original 103), check PASS, 0 warnings → `books/Nessahan Alita - The War of Passion (2005 Edition).pdf`. Previews checked: title page, p. 57 (notes 36–37, compared with original p. 61), glossary p. 96. Note: chapter headings are left-aligned and not underlined, while the original centers and underlines them (same as in the other books built so far).
