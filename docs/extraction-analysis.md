# Análise da extração (2026-10-23)

Fonte: `extracted/<livro>/` gerado por `extract_pdfs.py` (PyMuPDF 2.0 /
MuPDF 1.28.5, `get_text("dict", sort=True)`).

## Visão geral dos livros

| Slug | Págs. | Formato | Corpo | Capítulos detectados | Observações |
|---|---|---|---|---|---|
| guerra-da-paixao-2005 | 103 | Carta | TNR 13.9 | 19 | marca d'água pdfFactory |
| como-lidar-com-mulheres-2008 | 249 | A4 | Times 11.7 | 36 | **espaçamento quebrado em ~645 blocos** |
| magnetismo-relacoes-sociais-2008 | 54 | Carta | TNR 12 | 17 | limpo, **piloto** |
| profano-feminino-2008 | 88 | A4 | TNR 12 | 22 | — |
| reflexoes-masculinas-2008 | 67 | Carta | Bookman 13.9 | 12 | marca d'água pdfFactory, muitos subtítulos |
| textos-complementares-2008 | 79 | A4 | Bookman 11.7 | 24 | muitos subtítulos curtos |
| textos-complementares-ii-2009 | 46 | A4 | TNR 12 | 23 | **tabela na p. 9** |

Para todos os livros, a segmentação reproduz 100% dos caracteres das linhas
mantidas (verificado em `work/<slug>/structure-report.md`).

## Como os elementos aparecem nos dados

| Elemento | Representação | Detecção |
|---|---|---|
| Parágrafo | Uma linha por bloco (às vezes um bloco por parágrafo, em Textos Compl. II) | 1ª linha recuada (~36 pt) e/ou espaço vertical maior; última linha curta |
| Título de capítulo | Bloco em negrito, às vezes maior, frequentemente "N. Título"; às vezes em 2 linhas | negrito ≥ 80% ou tamanho ≥ corpo + 1,5; regex de capítulo |
| Subtítulo | Negrito no tamanho do corpo | mesmo critério; não casa com a regex de capítulo |
| Chamada de nota | Span sobrescrito (flag 1, ~8 pt) colado à palavra | span menor e elevado em relação à linha de base |
| Texto da nota | Fonte menor (~10 pt) no pé da página, começando por número elevado de ~6,5 pt | zona abaixo do último texto do corpo, iniciando com número elevado |
| Nota que continua | A chamada e o texto podem estar em páginas diferentes (ex.: Magnetismo, nota 5: chamada na p. 43, texto na p. 44) | busca da chamada na mesma página ou em até 2 páginas antes |
| Itálico / negrito inline | Spans com flags 2 / 16 | convertidos em `<i>` / `<b>` |
| Citações / epígrafes | Itálico entre aspas, ou fonte menor e recuada | itálico preservado; recuo registrado no estilo |
| Número de página | Linha só com dígitos no rodapé | removido (regenerado na reconstrução) |
| Sumário ("Índice") | Linhas comuns, às vezes azuis (cor 255 = links do Word) | tratado como texto da seção inicial |
| Imagens | **Nenhuma** em nenhum livro | — |
| Linhas e bordas vetoriais | Separador de notas, bordas de tabela | **não extraídas**; ler do PDF na reconstrução |

## Problemas encontrados

1. **Linhas justificadas fragmentadas.** Em linhas muito espaçadas, o
   PyMuPDF quebrou palavra por palavra (`"O \nprimeiro \npasso"` no
   `document.md`). Resolvido na segmentação: os spans são reagrupados por linha de base.
2. **`document.md` não serve como texto-fonte.** Ele tem uma linha por bloco,
   quebras no meio dos parágrafos, números de página e marca d'água misturados ao texto.
3. **Espaços espúrios dentro das palavras (bloqueante para Como lidar com
   mulheres).** ~52 mil caracteres em Helvetica-Oblique (cartas e anexos, pp. ~204-249)
   saíram como `co n q u ist ad a`. Reextraindo com
   `flags=pymupdf.TEXTFLAGS_TEXT | pymupdf.TEXT_INHIBIT_SPACES`, o texto sai
   correto. Nos outros 7 livros essa flag não muda nenhuma palavra.
   Corrigir antes de trabalhar nesse livro (nova extração em diretório
   separado, sem sobrescrever `extracted/`).
4. **Marca d'água do pdfFactory** ("PDF created with pdfFactory trial version")
   em todas as páginas de Guerra da Paixão e Reflexões Masculinas. Removida via `drop_line_patterns`.
5. **Tabela de duas colunas** (Textos Complementares II, pp. 9-10): o
   extrator fundiu células de colunas diferentes no mesmo bloco. A segmentação
   sinaliza com um aviso; essa tabela exigirá marcação manual.
6. **`metadata.json` → `fonts`** guarda só o último tamanho e as últimas flags
   vistos de cada fonte; não use como inventário tipográfico. Os tamanhos
   reais estão nos spans de `pages/*.json`.
7. **Metadados dos PDFs não são confiáveis**: o título de Guerra da Paixão é "Reflexões Masculinas" (modelo do pdfFactory); os
   de 2008 são "Microsoft Word - ...". Use `config/books/*.json`.
8. **Sem sumário embutido (outline)** em nenhum PDF, e os links internos são
   só das notas de rodapé. Os capítulos vêm da detecção dos títulos.
9. **Hifenização**: não há hifenização automática; todo hífen em fim de
   linha é real (*chamá-los*, *auto-*). A junção de linhas mantém o hífen.
10. **Ordem de leitura**: correta em todos os livros (coluna única).
    `sort=True` não causou inversões.
11. **Numeração das notas**: contínua no livro (Magnetismo) ou reiniciada a
    cada capítulo (Como lidar). As notas são associadas por capítulo e por página.
12. **Duas edições de O Profano Feminino**: a de 2008 amplia a de 2005. A
    edição de 2005 foi removida do projeto em 2026-10-24 (duplicada).

## Capítulos: automático ou manual?

Detecção automática, com confirmação humana. Os títulos de capítulo são
identificáveis por estilo (negrito/tamanho) e pelo padrão `N. Título`,
`Introdução`, `Conclusões` etc. Em Magnetismo, Guerra da Paixão, Profano
Feminino, Textos Complementares I/II e Como lidar com mulheres, a lista
detectada corresponde aos títulos numerados do texto. Casos que exigem conferência:

- Reflexões Masculinas: o título do cap. 4 está no tamanho dos subtítulos
  (a regex resolve) e há títulos quebrados em duas linhas (juntados
  automaticamente). **O original tem dois capítulos "5."** (pp. 40 e 46), e o
  capítulo "6. Algumas artimanhas femininas infernizantes" não consta do
  Índice. É erro do original: preservar e registrar `QUERY`.
- Como lidar com mulheres: os anexos têm o problema de extração descrito acima.
- Front matter (capa, advertência, sumário) fica no capítulo `00`.

Quando necessário, a config aceita uma lista explícita:
`"chapter_starts": [{"page": 28, "starts_with": "8. O caráter"}, ...]`.
