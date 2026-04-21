---
name: feature-audit
description: "Auditoria completa de features, ajustes e correções na Plataforma LIA, alinhada ao WeDO Talent Guide v3.3. Use OBRIGATORIAMENTE antes de marcar qualquer tarefa como concluída, após implementar features novas, fazer ajustes, ou quando o usuário pedir revisão/auditoria. Cobre 14 dimensões — integração, dados, UI/Design System v4.2.1, backend, tipos, fluxo do usuário, consistência, documentação, arquitetura de agentes, qualidade LLM, serviços IA, governança IA, segurança e performance. Para verificações mais profundas de governança, compliance e DEI, consultar as 4 skills complementares: wedo-governance, screening-compliance, dei-fairness e lgpd-data-protection."
---

  # Feature Audit — Checklist Universal de Auditoria (14 Dimensões)

  Esta skill é uma auditoria obrigatória de **14 dimensões** que deve ser executada antes de marcar qualquer feature, ajuste ou correção como concluído. Ela garante que nada fique desconectado, parcialmente implementado, invisível ao usuário, ou em violação ao Design System / arquitetura de IA.

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
| Quando Usar | `references/01-quando-usar.md` |
| Filosofia | `references/02-filosofia.md` |
| Skills Complementares | `references/03-skills-complementares.md` |
| Mapa das 14 Dimensões | `references/04-mapa-das-14-dimensoes.md` |
| As 14 Dimensões da Auditoria | `references/05-as-14-dimensoes-da-auditoria.md` |
| Formato de Relatório | `references/06-formato-de-relatorio.md` |
| Quando NÃO Pular Dimensões | `references/08-quando-nao-pular-dimensoes.md` |
| Atalho para Auditorias Rápidas (Ajustes Menores) | `references/09-atalho-para-auditorias-rapidas-ajustes-menores.md` |
| Arquivos-Chave da Plataforma para Referência | `references/10-arquivos-chave-da-plataforma-para-referencia.md` |
| Uso em Outros Ambientes | `references/11-uso-em-outros-ambientes.md` |
| Boy Scout Rule (addendum v2 — orchestrator-aware) | `references/12-boy-scout-rule-addendum-v2-orchestrator-aware.md` |
| Cross-references com a cascata (orchestrator) | `references/13-cross-references-com-a-cascata-orchestrator.md` |

