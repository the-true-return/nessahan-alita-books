# Nessahan Alita: tradução pt-BR → en-US

Tradução dos livros de Nessahan Alita do português brasileiro para o inglês
americano, preservando conteúdo, voz do autor e estrutura, com vistas à
reconstrução futura dos PDFs.

Antes de traduzir qualquer coisa, leia `translation-rules.md` e o glossário
`glossary/glossary.json`.

## Estado atual

- Fase: **piloto**. O livro piloto é *O Magnetismo nas Relações Sociais*
  (`magnetismo-relacoes-sociais-2008`, capítulos `00` a `16`, ~12 mil palavras),
  traduzido inteiro antes de qualquer outro livro. **Tradução concluída em
  2026-10-23; aguardando revisão humana** (`review/magnetismo-relacoes-sociais-2008/book-qa.md`).
- Não traduza outros livros sem pedido explícito.
- Sempre cite os livros pelo título completo (`title_pt` da config), nunca abreviado.
- `profano-feminino-2005` foi superado pela edição de 2008; não traduzir sem decisão do usuário.
- `como-lidar-com-mulheres-2008` tem um problema de extração **bloqueante**
  (veja `known_issues` na config). Não segmentar nem traduzir antes de corrigir.

## Diretórios

| Diretório | Conteúdo | Quem escreve |
|---|---|---|
| `portuguese-original-pdf/` | PDFs originais | **somente leitura** |
| `extracted/` | Extração bruta do PyMuPDF (`extract_pdfs.py`) | **somente leitura** |
| `config/books/<slug>.json` | Configuração e problemas conhecidos por livro | humano / Claude, com cuidado |
| `work/<slug>/` | Texto-fonte normalizado em segmentos + layout (gerado) | `tools/segment.py` |
| `glossary/glossary.json` | Glossário compartilhado entre todos os livros | Claude propõe, humano aprova |
| `translations/<slug>/NN.en.md` | Traduções, um arquivo por capítulo | Claude (tradução) |
| `review/<slug>/` | Relatórios de QA, revisão bilíngue, dúvidas | `tools/qa.py` |
| `output/<slug>/` | PDFs gerados (futuro) | ferramenta de rebuild (futuro) |
| `docs/` | Análise da extração e plano de reconstrução dos PDFs | — |

Nunca modifique `portuguese-original-pdf/` nem `extracted/`. `work/` é
regenerável, mas depois que a tradução de um livro começar, não rode
`segment.py` de novo sem necessidade: os IDs dos segmentos são sequenciais e
uma segmentação diferente os desloca (o QA acusa isso por hash).

## Ambiente e comandos

As ferramentas usam só a biblioteca padrão (Python 3.10+). O venv existente
também serve (PyMuPDF e Typst são usados na geração e verificação dos PDFs):

```powershell
$py = "pymupdf-venv\Scripts\python.exe"
& $py tools\segment.py <slug>             # segmenta um livro -> work/<slug>/ + structure-report.md
& $py tools\status.py <slug>              # progresso por capítulo
& $py tools\status.py <slug> --next NN    # próximo lote de segmentos do capítulo NN (~1200 palavras)
& $py tools\qa.py <slug> NN               # QA do capítulo -> review/<slug>/NN.qa.md e NN.bilingual.md
& $py tools\qa.py <slug> --all           # + review/<slug>/book-qa.md
```

Slugs: veja `config/books/`.

## Formato dos arquivos de tradução

`work/<slug>/chapters/NN.pt.md` e `translations/<slug>/NN.en.md` têm o mesmo
formato: cada segmento começa com uma linha marcadora, seguida do texto.

```
<!-- seg 09-0003 paragraph h=19b962ac -->
Text of the segment, in English...

<!-- seg 09-0004 footnote n=2 h=8bfb81ab -->
Footnote text...
```

- Copie a linha marcadora **exatamente** da fonte (o hash `h=` identifica a
  versão do texto-fonte traduzida).
- Um bloco por segmento, na mesma ordem. Nunca junte, divida, omita ou reordene segmentos.
- Tipos: `heading`, `paragraph`, `footnote` (com `n=` = número da nota).
- Marcação inline a preservar: `<i>…</i>`, `<b>…</b>` e chamadas de nota `[^N]`.
- Dúvidas e notas ficam em comentários dentro do bloco do segmento, nunca no texto:
  - `<!-- QUERY: ambiguidade, opção escolhida, alternativas -->`
  - `<!-- TN: nota do tradutor proposta, para revisão humana -->`
  - `<!-- KEEP: palavra1, palavra2 -->` libera no QA palavras estrangeiras com
    acento que não são portuguesas. **Nenhum texto pode ficar em português.**
- Cabeçalho do arquivo (antes do primeiro marcador):
  `<!-- book: <slug> | chapter: NN | en-US -->`

## Fluxo de tradução (por capítulo, em lotes)

1. **Preparar o livro** (uma vez): `segment.py <slug>`. Leia
   `work/<slug>/structure-report.md` e confirme que a completude está `OK`,
   que a lista de capítulos bate com o sumário do livro e que os avisos foram
   entendidos. Se a detecção de capítulos falhar, use `chapter_starts` na config.
2. **Lote**: `status.py <slug> --next NN` imprime os próximos segmentos não
   traduzidos. Antes de traduzir, procure no glossário os termos do lote
   (`match_pt`) e releia o fim do trecho já traduzido para manter a continuidade.
3. **Traduzir** o lote seguindo `translation-rules.md` e **anexar** os blocos
   ao fim de `translations/<slug>/NN.en.md` (criar com o cabeçalho, se não existir).
4. **QA do lote**: `qa.py <slug> NN`. Corrija todos os erros antes do próximo
   lote. Avisos: revise um a um; mantenha a tradução se ela estiver correta
   (ex.: um número escrito por extenso) e, se for o caso, explique com `QUERY`.
5. **Fim do capítulo**: rode o QA de novo, leia `review/<slug>/NN.bilingual.md`
   inteiro (voz, consistência, notas) e proponha no glossário os termos novos
   e recorrentes (`status: "proposed"`). Informe ao usuário um resumo: status
   do QA, dúvidas abertas e termos propostos.

## Retomada após interrupção

O progresso é derivado dos próprios arquivos; não há estado a atualizar à mão.

1. `status.py <slug>` mostra o estado de cada capítulo.
2. Confira se o último bloco de `NN.en.md` está completo (se a escrita foi
   interrompida, ele pode estar truncado; o QA acusa razão de tamanho baixa).
   Se estiver incompleto, apague esse bloco.
3. `status.py <slug> --next NN` continua exatamente do primeiro segmento pendente.

As ferramentas gravam arquivos de forma atômica (arquivo temporário +
renomeação), então uma interrupção não deixa relatórios corrompidos.

## Glossário

- `approved` e `do_not_translate`: obrigatórios; o QA verifica.
- `proposed`: use como padrão, mas registre `QUERY` se o contexto pedir outra
  coisa. Só o usuário promove para `approved`.
- Claude pode **acrescentar** entradas `proposed`; não altera nem remove
  entradas `approved` sem pedido do usuário.
- Formato das entradas: `translation-rules.md`, seção "Glossário".

## Reconstrução dos PDFs

Implementada e validada com *Magnetism in Social Relations*
(`output/magnetismo-relacoes-sociais-2008/`). Detalhes em `docs/pdf-rebuild-plan.md`.

```powershell
& $py tools\build_pdf.py <slug>    # output/<slug>/<slug>-en.pdf (exige QA sem erros; --draft ignora)
& $py tools\check_pdf.py <slug>    # output/<slug>/pdf-check.md + preview/*.png
```

- Para um livro novo, a config precisa de `title_en` e de uma seção `pdf`
  (fonte, espaçamento entre letras, entrelinha), medida no PDF original;
  veja `config/books/magnetismo-relacoes-sociais-2008.json`.
- Depois de gerar o PDF, olhe as prévias das páginas de abertura, de páginas
  com notas e de listas, e não só o relatório.
- Fontes: só fontes livres em `fonts/`, com a licença registrada em `output/<slug>/FONTS.md`.
- **Todo livro termina com o apêndice "Glossary"**, um acréscimo da edição
  inglesa: os conceitos do glossário (`category` concept/style) que aparecem
  no livro, com termo em inglês, original em português e nota em inglês. O
  `build_pdf.py` **falha** se um conceito usado no livro não tiver
  `display_en`, `display_pt` e `note_en` no `glossary.json`; escreva essas
  notas ao terminar a tradução de cada livro.
- **PDF final em `books/`**: quando o `check_pdf.py` passa, ele copia o PDF para
  `books/Nessahan Alita - <title_en> (<edition> Edition).pdf`. Só PDFs
  verificados vão para `books/`; `output/` guarda os de trabalho. A config de
  cada livro precisa de `title_en` e `edition`.
