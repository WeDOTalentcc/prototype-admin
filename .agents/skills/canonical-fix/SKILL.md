---
name: canonical-fix
description: "Identifica o arquivo canonico (fonte da verdade) antes de qualquer fix, refactor ou edicao com risco de duplicata. Use OBRIGATORIAMENTE quando: (a) for corrigir um bug, (b) for editar codigo onde podem existir duplicatas (rotas paralelas, hooks clonados .ts/.tsx, services com nomes similares), (c) for refatorar, (d) o usuario pedir 'corrige na raiz', 'sem gambiarra', 'sem workaround', 'corrige na origem', 'arruma direito'. Garante que o fix seja aplicado na fonte (nao no consumidor), sem fallback silencioso, sem try/except mascarando, sem flag improvisada e sem copy-paste de logica."
---

  # Canonical-Fix — Corrigir na Origem, Sem Workaround

  Procedimento obrigatorio antes de editar codigo para corrigir um bug ou refatorar. Garante que voce identifique o **arquivo canonico** (fonte da verdade), entenda quem o consome, e aplique o fix no lugar certo — nunca no consumidor, nunca atras de um fallback, nunca com copy-paste.

  > Esta skill segue o padrao **progressive-disclosure** (ver `.agents/skills/progressive-disclosure/SKILL.md`). O SKILL.md serve para triagem rapida; o conteudo tecnico foi distribuido em `references/` por dimensao/passo/parte.

  ## Quando ativar

  Veja a `description` no frontmatter para os gatilhos completos. Em geral: ative quando o trabalho atual cair num dos topicos da tabela "Mapa de references" abaixo.

  ## Quando NAO ativar

  - Quando o trabalho ja foi coberto por outra skill mais especifica.
  - Quando o escopo for trivial (typo, copy de UI sem logica, edicao isolada que nao ativa nenhum topico).

  ## Como usar

  1. **Triagem** — leia este SKILL.md. Identifique quais topicos da tabela abaixo se aplicam ao trabalho.
  2. **Diagnostico** — abra apenas as references relevantes (1-3 normalmente bastam).
  3. **Execucao** — siga o procedimento descrito nas references abertas.
  4. **Output em camadas** — entregue TL;DR -> resumo -> detalhe sob demanda (ver `progressive-disclosure`).

  ## Mapa de references

  | Topico | Arquivo |
|--------|---------|
| Quando usar | `references/01-quando-usar.md` |
| Quando NAO usar | `references/02-quando-nao-usar.md` |
| Filosofia | `references/03-filosofia.md` |
| Checklist em 5 fases | `references/04-checklist-em-5-fases.md` |
| Anti-padroes catalogados | `references/05-anti-padroes-catalogados.md` |
| Comandos prontos | `references/06-comandos-prontos.md` |
| Integracao com outras skills | `references/07-integracao-com-outras-skills.md` |
| Saida esperada | `references/08-saida-esperada.md` |
| Addendum v2 — duplicatas de rotas paralelas e link com o orchestrator | `references/09-addendum-v2-duplicatas-de-rotas-paralelas-e-link-com-o-orche.md` |


  ## Output esperado

  Ao terminar, responda na ordem:

  1. **TL;DR** — 1-3 linhas com o veredicto/resultado.
  2. **Resumo estruturado** — bullets ou mini-tabela cobrindo os topicos efetivamente aplicados.
  3. **Detalhe por topico** — abrir apenas se houver bloqueio ou pedido explicito.
  4. **Anexos** — comandos rodados, logs, diffs, sempre rotulados ao final.

  Se voce abriu uma reference e nao aplicou nada dela, declare explicitamente "topico X verificado, sem acao necessaria".
  