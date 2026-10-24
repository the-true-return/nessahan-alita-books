# Tradução automática (agente agendado)

Um agente local traduz os livros da fila (`queue.txt`) sozinho, um por vez, em
várias sessões, e continua de onde parou quando o limite de uso é liberado. Ao
terminar cada livro (PDF final em `books/`), faz **commit e push** automaticamente.

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
- Uma trava (`state/runner.lock`) impede duas execuções ao mesmo tempo.
- No fim de cada livro: glossário em inglês, PDF, verificação, publicação em
  `books/`, arquivo `state/<slug>.done`, `git commit` + `git push`, e o próximo
  livro da fila começa. Com a fila vazia, a tarefa agendada se remove sozinha.
- Push que falhar (rede) é repetido no início de cada execução seguinte.
- Permissões da sessão automática: ler e editar arquivos do projeto e rodar
  apenas `pymupdf-venv/Scripts/python.exe` e comandos de leitura (`cat`, `ls`, `grep`...).

## Acompanhar

- Progresso legível: `automation/state/<slug>-progress.md` (uma entrada por sessão).
- Livros concluídos: `automation/state/<slug>.done`.
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

# mudar a ordem ou acrescentar livros: edite automation\queue.txt
```

Requisitos: o computador ligado e o usuário logado (a tarefa usa o login do
Claude Code deste usuário).
