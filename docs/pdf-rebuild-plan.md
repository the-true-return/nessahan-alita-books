# Plano: reconstrução dos PDFs em inglês

**Status (2026-10-24):** implementado em `tools/build_pdf.py` e
`tools/check_pdf.py` e validado com *Magnetism in Social Relations* (52 páginas
contra 54 do original; verificação sem erros nem avisos). Decisões tomadas:

- Motor: Typst (pacote Python `typst`, offline, reprodutível).
- Fonte: Liberation Serif (OFL), com métricas idênticas às da Times New Roman do original.
- Espaçamento entre letras de 1 pt, entrelinha de 20,7 pt e espaço entre
  parágrafos de 32,7 pt (de base a base), medidos no original e guardados na
  seção `pdf` da config do livro.
- Abertura (capítulo 00) com as posições verticais do original; demais
  capítulos em página nova, como no original.
- Numeração das notas definida explicitamente (há livros que reiniciam por capítulo).
- Trechos só com pontuação (artefatos do original) não são impressos.
- Hifenização em inglês ligada no corpo; desligada em títulos e textos centralizados.

Pendências para os próximos livros: sublinhado do título no bloco de citação
(o sublinhado é um desenho vetorial, que não foi extraído); tabela de Textos
Complementares II; estilo próprio para as cartas de Como lidar com mulheres.

O plano original segue abaixo, como referência.

## Princípio: refluxo fiel ao estilo, não página a página

O inglês ocupa em geral de 5% a 15% menos espaço que o português, e de modo
desigual. Sobrepor texto inglês às coordenadas originais causaria vazios,
cortes e sobreposições. A recomendação é **recompor** o livro (refluxo),
reproduzindo fielmente o *estilo* de cada elemento: tamanho e formato da
página, margens, fontes, tamanhos, recuos, alinhamento, espaçamentos, notas
no pé da mesma página da chamada e títulos de capítulo na mesma posição
relativa. A paginação resultante será outra, e o sumário e as referências
cruzadas serão regenerados.

## Fontes de dados

| Dado | Origem |
|---|---|
| Texto em inglês, por segmento | `translations/<slug>/NN.en.md` |
| Tipo e estilo do segmento (fonte, tamanho, negrito/itálico, alinhamento, recuo) | `work/<slug>/chapters/NN.json` → `style` |
| Geometria das linhas originais (página, bbox, fonte, cor, blocos) | `work/<slug>/chapters/NN.layout.json` |
| Tamanho da página, margens, entrelinha, recuo | `work/<slug>/book.json` → `metrics` + `extracted/.../metadata.json` |
| Linha separadora das notas e bordas de tabela | ler do PDF original com `page.get_drawings()` (não estão em `extracted/`) |
| Imagens | nenhum livro tem imagens; `extracted/<livro>/images/` está vazio |

## Pipeline proposto

1. **`tools/build_style.py <slug>`**: deriva uma folha de estilos do livro a
   partir das métricas e dos estilos dos segmentos: estilo do corpo, título de
   capítulo, subtítulo, nota, citação, front matter, margens e entrelinha.
   Gera `output/<slug>/style.json`, revisável por um humano.
2. **`tools/build_pdf.py <slug>`**: monta o documento a partir dos segmentos
   traduzidos e da folha de estilos e gera `output/<slug>/<slug>-en.pdf`.
   Motor recomendado: **Typst** (um único executável, local e reprodutível, com
   notas de rodapé nativas, controle fino de tipografia e PDF/A). Alternativas:
   WeasyPrint (HTML/CSS, notas com `float: footnote`) ou `pymupdf.Story`
   (já instalado, mas sem notas de rodapé nativas).
   - `<i>`/`<b>` → ênfase do motor; `[^N]` + segmento `footnote n=N` → nota de rodapé nativa.
   - Capítulos começam em página nova quando começavam assim no original
     (posição `y` do título ≈ topo da área de texto em `layout.json`).
   - Sumário gerado a partir dos `heading`.
   - Front matter (capa, dados de citação, advertência) em modelo próprio,
     posicionado a partir das coordenadas originais da página 1-3.
3. **`tools/check_pdf.py <slug>`**: controle de qualidade do PDF gerado:
   - todo segmento traduzido aparece no PDF (extração do texto e busca de cada
     segmento normalizado);
   - nenhum texto fora da área útil (bbox dos spans contra as margens);
   - nenhuma sobreposição entre blocos de texto;
   - nenhuma página vazia ou quase vazia, exceto as intencionais;
   - viúvas e órfãs, e títulos sozinhos no pé da página;
   - toda nota na mesma página da chamada (ou com continuação marcada);
   - fontes todas incorporadas (`page.get_fonts()`), sem substituição;
   - relatório com miniaturas das páginas com problemas (`page.get_pixmap()`).

## Ajustes tipográficos

- Manter fonte, tamanho e entrelinha do original como ponto de partida.
- Corpo justificado com hifenização em inglês ligada (os originais não
  hifenizam, mas em inglês justificado sem hifenização aparecem "rios" de espaço).
- Controle de viúvas e órfãs (mínimo de 2 linhas).
- Títulos presos ao parágrafo seguinte.
- Se o volume de páginas variar demais, ajuste de entrelinha em ±0,5 pt no
  livro inteiro, nunca por página.

## Fontes tipográficas e licenças

Fontes usadas nos originais e situação local:

| Original | Embutida no PDF? | Instalada nesta máquina | Licença | Substituta livre recomendada |
|---|---|---|---|---|
| Times New Roman | parcial (subconjunto em Magnetismo) | sim | Monotype, distribuída com o Windows: uso e incorporação em PDF permitidos, sem redistribuição do arquivo da fonte | TeX Gyre Termes ou Liberation Serif (OFL, métricas compatíveis) |
| Bookman Old Style | subconjunto em alguns livros | **não** | Monotype, distribuída com o MS Office | TeX Gyre Bonum (GUST, livre) |
| Georgia | não | sim | Microsoft | Gelasio (OFL, métricas compatíveis) |
| Arial / Helvetica | não | sim | Monotype / Linotype | Liberation Sans ou TeX Gyre Heros |
| Symbol | não | sim | — | só se for usada (marcadores) |

Os subconjuntos embutidos nos PDFs **não** devem ser extraídos e reutilizados
(estão incompletos e a licença não permite). Recomendação: usar as substitutas
livres para a edição publicada, o que dá uma licença clara, reprodutibilidade
em qualquer máquina e incorporação sem restrições. Antes de publicar,
confirmar a licença das fontes escolhidas e registrá-la em `output/<slug>/FONTS.md`.

## Elementos que não serão copiados

- Marca d'água do pdfFactory.
- Números de página originais (regenerados).
- Metadados originais incorretos (o título, o autor "Ninguém" etc. serão
  definidos a partir de `config/books/<slug>.json`).
- Criptografia RC4 dos originais.

## Casos especiais pendentes

- Tabela de Textos Complementares II (pp. 9-10): definir a estrutura à mão,
  como segmentos `table_cell` com linha e coluna, antes da tradução desse trecho.
- Cartas de leitores em Como lidar com mulheres (Helvetica-Oblique): estilo
  próprio, para manter a distinção entre o texto do autor e o de terceiros.
