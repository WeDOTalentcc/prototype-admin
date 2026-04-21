---
name: lia-planning
description: "Metodologia de planning unificada para Plataforma LIA — combina GSD workflow (4 modos), spec-driven development (4 fases) e brainstorming estruturado. Use ao iniciar qualquer trabalho significativo, planejar sprints, diagnosticar bugs, especificar features ou quando o usuario pedir para seguir a metodologia. Triggers: gsd, metodologia, workflow, novo sprint, planejar feature, bug fix, especificar, brainstorming, como vamos trabalhar."
---

  # LIA Planning — Metodologia Unificada

  Combina 3 abordagens: GSD workflow (modos operacionais), spec-driven development (fases de profundidade) e brainstorming estruturado (exploracao de ideias).

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
| Principio Central: Auto-Sizing | `references/01-principio-central-auto-sizing.md` |
| Arquivos de Estado | `references/02-arquivos-de-estado.md` |
| Modo 1: Bug Fix | `references/03-modo-1-bug-fix.md` |
| Modo 2: Feature | `references/04-modo-2-feature.md` |
| Modo 3: Refactor | `references/05-modo-3-refactor.md` |
| Modo 4: Sprint | `references/06-modo-4-sprint.md` |
| Spec-Driven: 4 Fases Adaptativas | `references/07-spec-driven-4-fases-adaptativas.md` |
| Regras Inegociaveis do Projeto | `references/08-regras-inegociaveis-do-projeto.md` |
| Erros Pre-Existentes a Ignorar | `references/09-erros-pre-existentes-a-ignorar.md` |
| Quality Gates | `references/10-quality-gates.md` |
| Template de Session Plan | `references/11-template-de-session-plan.md` |
| Comandos Rapidos | `references/12-comandos-rapidos.md` |


  ## Output esperado

  Ao terminar, responda na ordem:

  1. **TL;DR** — 1-3 linhas com o veredicto/resultado.
  2. **Resumo estruturado** — bullets ou mini-tabela cobrindo os topicos efetivamente aplicados.
  3. **Detalhe por topico** — abrir apenas se houver bloqueio ou pedido explicito.
  4. **Anexos** — comandos rodados, logs, diffs, sempre rotulados ao final.

  Se voce abriu uma reference e nao aplicou nada dela, declare explicitamente "topico X verificado, sem acao necessaria".
  