# Tradução automática (agente agendado)

Um agente local traduz um livro inteiro sozinho, em várias sessões, e continua
de onde parou quando o limite de uso é liberado.

## Como funciona

- O **Agendador de Tarefas do Windows** roda `run-translation.ps1` **a cada hora**
  (tarefa `NessahanAlita-Translation`).
- Cada execução inicia sessões do Claude Code em modo automático (`claude -p`)
  com as instruções de `translate-book.md`. Cada sessão traduz cerca de 12 mil
  palavras em lotes, roda o QA a cada lote e registra o progresso. As sessões
  são **encadeadas sem pausa** enquanto houver progresso; o script só espera o
  horário seguinte quando uma sessão falha (limite de uso) ou não avança.
- O progresso fica nos próprios arquivos (`translations/`, `review/`), então
  a próxima execução continua do primeiro trecho pendente.
- Se o limite de uso estiver esgotado, a execução falha logo, sem efeito, e a
  da hora seguinte tenta de novo. O limite é liberado periodicamente.
- Uma trava (`state/<slug>.lock`) impede duas execuções ao mesmo tempo.
- No fim: glossário em inglês, PDF, verificação, publicação em `books/`,
  arquivo `state/<slug>.done`, e a tarefa agendada se remove sozinha.
- Permissões da sessão automática: ler e editar arquivos do projeto e rodar
  apenas `pymupdf-venv/Scripts/python.exe` e comandos de leitura (`cat`, `ls`, `grep`...).

## Acompanhar

- Progresso legível: `automation/state/<slug>-progress.md` (uma entrada por execução).
- Progresso por capítulo: `pymupdf-venv\Scripts\python.exe tools\status.py <slug>`
- Saída completa de cada execução: `automation/logs/`.

## Comandos

```powershell
# rodar uma execução agora (sem esperar o agendador)
powershell -ExecutionPolicy Bypass -File automation\run-translation.ps1

# pausar / retomar / remover o agendamento
Disable-ScheduledTask -TaskName NessahanAlita-Translation
Enable-ScheduledTask  -TaskName NessahanAlita-Translation
Unregister-ScheduledTask -TaskName NessahanAlita-Translation -Confirm:$false

# outro livro: passe -Slug (e registre outra tarefa, ou troque o padrão no script)
powershell -ExecutionPolicy Bypass -File automation\run-translation.ps1 -Slug guerra-da-paixao-2005
```

Requisitos: o computador ligado e o usuário logado (a tarefa usa o login do
Claude Code deste usuário).
