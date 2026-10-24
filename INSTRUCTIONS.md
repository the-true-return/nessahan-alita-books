# Instruções do projeto

Como o projeto funciona: estrutura de diretórios, requisitos e comandos do
pipeline de tradução e geração dos PDFs. A apresentação dos livros está no
[README](README.md); as regras para o Claude Code estão em `CLAUDE.md`.

## Estrutura

```
portuguese-original-pdf/   PDFs originais (somente leitura)
extracted/                 extração bruta do PyMuPDF (somente leitura; extract_pdfs.py)
config/books/              configuração e problemas conhecidos de cada livro
work/<slug>/               texto-fonte normalizado em capítulos e segmentos + layout (gerado)
glossary/glossary.json     glossário pt-BR -> en-US compartilhado
translations/<slug>/       traduções en-US (NN.en.md)
review/<slug>/             relatórios de QA, revisão bilíngue, dúvidas
output/<slug>/             PDFs de trabalho, verificação e prévias
books/                     PDFs finais verificados, com título em inglês
tools/                     scripts do pipeline
docs/                      análise da extração e plano de reconstrução dos PDFs
```

## Requisitos

- Python 3.10+ (as ferramentas de `tools/` usam só a biblioteca padrão).
- PyMuPDF (`pymupdf-venv/`), para a extração e a verificação dos PDFs.
- Typst (`pymupdf-venv\Scripts\pip install typst`), para gerar os PDFs.
- Fontes livres em `fonts/` (Liberation Serif, OFL).

## Comandos

```powershell
$py = "pymupdf-venv\Scripts\python.exe"
& $py tools\segment.py magnetismo-relacoes-sociais-2008       # estrutura -> work/ + structure-report.md
& $py tools\status.py  magnetismo-relacoes-sociais-2008       # progresso
& $py tools\status.py  magnetismo-relacoes-sociais-2008 --next 09   # próximo lote a traduzir
& $py tools\qa.py      magnetismo-relacoes-sociais-2008 --all # QA -> review/
& $py tools\build_pdf.py magnetismo-relacoes-sociais-2008      # PDF -> output/
& $py tools\check_pdf.py magnetismo-relacoes-sociais-2008      # verificação do PDF
```

Fluxo completo e regras: `CLAUDE.md` e `translation-rules.md`.
