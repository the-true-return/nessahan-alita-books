# Regras de tradução (pt-BR → en-US)

Estas regras valem para todos os livros. Em caso de conflito, a ordem de
prioridade é: (1) fidelidade ao sentido, (2) voz do autor, (3) naturalidade
em inglês, (4) convenções tipográficas.

## 1. Princípios

- Origem: português brasileiro (pt-BR). Destino: inglês americano (en-US),
  com ortografia americana (*behavior*, *center*, *defense*).
- Tradução natural, fluente e idiomática, adequada para publicação. Busque
  equivalência semântica, não correspondência palavra por palavra.
- Preserve rigorosamente sentido, ideias, argumentos, tom, intenção e estilo.
- **Não** resuma, simplifique, adapte livremente, omita, suavize, intensifique
  nem invente conteúdo. Cada frase do original deve ter correspondente na tradução.
- Preserve a estrutura dos parágrafos: um segmento de origem = um segmento traduzido.
- Não acrescente explicações ao texto. Nota explicativa indispensável vai em
  `<!-- TN: ... -->` para revisão humana.
- Ambiguidade real (mais de uma leitura plausível): escolha a leitura mais
  provável **e** registre `<!-- QUERY: ... -->` com as alternativas. Nunca
  invente uma interpretação para resolver a dúvida em silêncio.

## 2. Voz e estilo do autor

O autor escreve ensaios filosóficos e polêmicos sobre relações amorosas,
psicologia e esoterismo (Gurdjieff, Samael Aun Weor, Eliphas Lévi,
Schopenhauer), num registro que mistura o filosófico e o coloquial, com humor,
ironia e desabafo.

- Mantenha o registro de cada trecho: frases solenes continuam solenes;
  coloquialismos, ironias e diminutivos pejorativos (*espertinhas*,
  *joguinhos*, *inferninhos*) ganham equivalente coloquial em inglês, não uma
  versão neutra.
- Não neutralize nem atenue posições do autor, mesmo polêmicas ou ofensivas:
  a tradução reproduz o que ele diz, sem endosso nem correção.
- Linguagem de gênero: preserve o masculino genérico (*o homem* → *man*, *a man*)
  e as oposições do autor (*Mulher* com maiúscula vs. *fêmea* → *Woman* vs.
  *female*). Não troque por formas neutras.
- Repetições deliberadas e vocabulário técnico do autor (*elemento passivo*,
  *egos*, *magnetismo*) devem ser mantidos; não varie sinônimos por elegância.
- Frases longas com muitas orações podem ser reorganizadas para soar naturais
  em inglês, desde que nada seja perdido. Dividir uma frase em duas é aceitável
  quando necessário; juntar parágrafos, nunca.
- Ênfases do original (maiúsculas como *NÃO SE APLICAM*, itálico, negrito)
  são preservadas nas palavras inglesas equivalentes.

## 3. Nomes, títulos, citações e referências

- Nomes próprios de pessoas: manter (*Nessahan Alita*, *Eliphas Lévi*).
  Figuras com grafia inglesa consagrada usam essa grafia (*Cristo* → *Christ*,
  *Buda* → *Buddha*).
- Erros de grafia de nomes no original (ex.: *Ganhdi*, *Budha*): usar a grafia
  correta e registrar `QUERY`.
- **Nada fica em português.** Títulos de obras, referências bibliográficas,
  rótulos e notas são todos traduzidos. Exceções são apenas nomes próprios
  (pessoas, cidades, editoras: *São Paulo*, *Madras*) e termos que já estão em
  outra língua no original (*conjunctio*, *perish of soul*).
- Títulos de obras: usar o título inglês consagrado quando existir; senão,
  traduzir o título. Registrar `QUERY` com o título original e as alternativas.
- Referências bibliográficas: traduzir título e rótulos (*trad.* → *trans.*,
  *5ª edição* → *5th edition*), preservando autor, ano, cidade, editora e páginas.
  Citações no formato *Lévi (1855/2001)* ficam como estão.
- Citações de terceiros traduzidas pelo autor para o português: traduzir a
  partir do português do autor. Se a obra tiver tradução inglesa clássica em
  domínio público, registre `QUERY` indicando-a; não insira traduções protegidas
  por direitos autorais.
- Distinga sempre o texto do autor de citações, cartas de leitores, epígrafes
  e notas editoriais: a formatação (itálico, aspas, recuo) e o tipo do segmento
  são mantidos.
- Bloco "Dados para citação" da primeira página: traduzir por inteiro,
  com o título inglês do livro.

## 4. Números, datas e tipografia

- Números, anos, numeração de capítulos (*8.*) e de listas: preservar.
- Datas: formato americano. *Em 29 de dezembro de 2002.* → *On December 29, 2002.*
- Ordinais: *1ª* → *1st*, *2º* → *2nd*.
- Aspas: usar aspas curvas duplas “ ” (e ‘ ’ dentro de aspas), com vírgula e
  ponto dentro das aspas, como é a convenção americana.
- Travessões: o autor usa hífen com espaços como travessão (*palavra - palavra*);
  em inglês use travessão (em dash) sem espaços: *word—word*. Listas de
  palavras-chave separadas por " - " mantêm o separador.
- Hifenização antiga do português (*auto-determinação*, *anti-*) não se
  transfere: use a forma inglesa padrão (*self-determination*).
- Erros de digitação e concordância evidentes no original (*sobra a perfídia*
  → *sobre*; *Os principais paixões*) são traduzidos pelo sentido evidente,
  sem `QUERY`. Se houver qualquer dúvida sobre o sentido, registre `QUERY`.

## 5. Marcação e estrutura (obrigatório)

- Copie cada linha marcadora `<!-- seg ... -->` exatamente como na fonte.
- Mantenha `<i>…</i>` e `<b>…</b>` em volta das palavras inglesas equivalentes.
  O número de tags deve ser o mesmo, salvo justificativa em `QUERY`.
- Mantenha cada chamada de nota `[^N]` exatamente uma vez, na posição
  equivalente da frase (mesma palavra ou sinal de pontuação de referência).
- Segmentos `footnote` são o texto da nota, sem o número (o número está em `n=`).
- Títulos (`heading`) são traduzidos; a numeração é mantida.
- Não use Markdown (`*`, `_`, `#`) no texto traduzido; só a marcação acima.

## 6. Dúvidas e notas

```
<!-- QUERY: "cadeia" pode ser "chain" (Lévi) ou "network". Usei "chain" (glossário). -->
<!-- TN: "Egrégora": conceito ocultista; talvez mereça nota para o leitor inglês. -->
```

- Uma `QUERY` por dúvida, curta: o problema, a opção usada e as alternativas.
- `<!-- KEEP: palavra1, palavra2 -->` só para liberar no QA palavras que não são
  portuguesas mas têm acento (ex.: *façade*). Nunca para deixar texto em português.
- `TN` só quando o leitor de língua inglesa realmente perderia algo
  (trocadilho intraduzível, referência cultural brasileira).
- Os relatórios de QA juntam todas as `QUERY` e `TN` em `review/<slug>/NN.qa.md`.

## 7. Glossário

Arquivo único, `glossary/glossary.json`, compartilhado entre os livros.
Cada entrada:

```json
{
  "term_pt": "egrégora",
  "match_pt": ["egrégora", "egrégoras"],
  "term_en": "egregore(s)",
  "match_en": ["egregore", "egregores"],
  "category": "concept | proper_name | title | expression | style",
  "status": "approved | proposed | do_not_translate",
  "books": ["*"],
  "notes": "contexto, alternativas descartadas, fonte"
}
```

- `match_pt` / `match_en`: formas (flexões) usadas pelo QA para verificar a
  consistência; a comparação ignora maiúsculas e respeita limites de palavra.
- `books`: `["*"]` para todos os livros, ou a lista de slugs.
- Conceitos (`concept`, `style`) também levam os campos do apêndice do livro em
  inglês: `display_en`, `display_pt` (o termo original, sem anotações) e
  `note_en` (uma ou duas frases em inglês, sem opinião do tradutor, explicando o
  sentido do termo na obra do autor). Esse apêndice "Glossary" vai no fim de todo
  livro traduzido.
- Termos novos recorrentes (aparecem 2+ vezes ou são conceitos do autor) devem
  ser adicionados como `proposed` ao fim do capítulo.

## 8. Checklist antes de entregar um lote

- [ ] Todos os segmentos do lote presentes, com o marcador idêntico ao da fonte.
- [ ] Nenhuma frase omitida ou acrescentada; nada de resumo.
- [ ] `[^N]`, `<i>`, `<b>`, números e datas preservados.
- [ ] Termos do glossário respeitados.
- [ ] Nenhum resto de português.
- [ ] Dúvidas registradas como `QUERY`, e não resolvidas por invenção.
- [ ] `qa.py` sem erros.
