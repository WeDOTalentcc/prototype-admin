# 00b — Inventário Documental WeDO/ — Auditoria 2026-05-10

> **⚠ INVENTÁRIO PRESCRITIVO — NÃO-EXECUTADO no clone GitHub canonical.**
>
> A pasta `WeDO/` vive dentro do clone do repositório GitHub canonical `WeDOTalentcc/wedotalent02202026.git`. **Modificações nesse clone violam REGRA ZERO** (CLAUDE.md global): tudo do GitHub é canonical e intocável; alterações lá são responsabilidade exclusiva do Anderson/time canonical.
>
> Este documento é portanto um **registro/recomendação** do que **deveria ser feito** na higiene documental — não a descrição de ações executadas no canonical. Quando Anderson/time decidir aplicar, este inventário serve como playbook pronto.
>
> **Princípio aplicado:** código é fonte de verdade. Docs aqui foram triados para reduzir ruído documental — mas **nenhum TODO de doc desta lista pode entrar no roadmap (Fase 4) sem revalidação via grep/sensor no código**.

---

## Status real desta auditoria documental

| Local | O que existe | Status |
|---|---|---|
| Replit `lia-agent-system/.audit/2026-05-10/` | `00-CAPACIDADES_LIVE.md` + `00b-INVENTARIO_DOCUMENTAL.md` (este doc) | ✅ Comitado (commits `48cdd3bd9` + `0148ba10c`, sem push) |
| Local `~/Documents/wedotalent_audit_2026-05-10/` | Cópia dos artefatos da auditoria | ✅ Pasta segura fora do clone canonical |
| GitHub canonical `WeDOTalentcc/wedotalent02202026/WeDO/` | **INTOCADO** | 🔒 REGRA ZERO — não modificamos clones canonical |

---

## Sumário das ações RECOMENDADAS (não-executadas no canonical)

> Quando Anderson/time canonical optar por aplicar a higiene, esta é a especificação:

| Ação recomendada | Quantidade | Local destino sugerido |
|---|---|---|
| 🗄 **Arquivar** (status histórico + duplicado) | **11** | `WeDO/_archive/2026-05-10/{analises,planos}/` |
| ✅ **Adicionar header CANONICAL VIVO** | **9** | In-place em `WeDO/{analises,planos}/` (apenas adição de bloco no topo) |
| 🔵 **Manter sem alteração** (referência permanente) | **7** | `WeDO/analises/` |
| ⏳ **Pendente** (arquivar após Fase 4 produzir substituto) | **10** | Aguardar `04-ROADMAP_PRIORIZADO.md` |
| 📄 **Criar README.md** | 1 | `WeDO/README.md` (índice canonical) — modelo em `~/Documents/wedotalent_audit_2026-05-10/WeDO_README.md` |

**Total processado (catalogado):** 37 docs (28 em `analises/` + 9 em `planos/`).

---

## Tabela completa: 37 docs × decisão

### 🗄 ARQUIVADOS AGORA (11) — `_archive/2026-05-10/`

| # | Doc | Pasta original | Categoria | Razão de archive | Cross-ref destino |
|---|---|---|---|---|---|
| 1 | `PENDENTES_IA.md` | `planos/` | STATUS HISTÓRICO | Data 21/12/2024. 88% TODOs já fechados em Sprints A-K + Sprint B (verificado via git log no Replit) | `00-CAPACIDADES_LIVE.md` Seção 2 |
| 2 | `ANALISE-GAPS-COMPLETA.md` | `analises/` | STATUS HISTÓRICO | Data 20/12/2025. Gaps pré-Sprint Pre-flight, todos endereçados | `00-CAPACIDADES_LIVE.md` Seção 2 |
| 3 | `AUDITORIA-FUNCIONALIDADES.md` | `analises/` | STATUS HISTÓRICO | Data 03/03/2026. Snapshot anterior aos commits Sprint 9 + Q2 + Sprint B | Sensor `check_no_select_in_services` (0 violations) |
| 4 | `QA_REPORT_SPRINT_2026-02-28.md` | `analises/` | STATUS HISTÓRICO | Sprint 28/02/2026. Refeito a cada sprint, snapshot puro | — |
| 5 | `QA_VACANCY_SYSTEM_REVIEW.md` | `analises/` | STATUS HISTÓRICO | Data 20/01/2026. Vacancy system passou por 3 ondas de canonical-truth desde então | `mapa_inteligencia_lia_completo.md` |
| 6 | `QA_WIZARD_REVIEW_JAN2026.md` | `analises/` | STATUS HISTÓRICO | Janeiro 2026. Wizard refatorado em Sprint 2 Phase 2 (PromptComposer) | Commit `c9baec92e` |
| 7 | `RELATORIO_TRANSFORMACAO_IA_LIA.md` | `analises/` | STATUS HISTÓRICO | Janeiro 2026. Snapshot de transformação, parcialmente obsoleto | `00-CAPACIDADES_LIVE.md` Seção 2 |
| 8 | `feature-impact-remove-block3-eligibility.md` | `analises/` | STATUS HISTÓRICO | Decisão pontual já tomada e implementada | — |
| 9 | `feature-impact-vacancy-lifecycle.md` | `analises/` | STATUS HISTÓRICO | Análise feature em progresso; substituto será roadmap Fase 4 | Phase 2.5 commits |
| 10 | `analise-reuniao-alinhamento-06fev2026.md` | `analises/` | STATUS HISTÓRICO | Snapshot reunião 06/02/2026. Múltiplas decisões já implementadas | — |
| 11 | `analise-comparativa-v5-vs-lia.md` | `analises/` | DUPLICADO | Mesmo escopo de `ANALISE_COMPARATIVA_V5_vs_LIA.md` (versão UPPERCASE, 2172 linhas, 19/03/2026, mais recente) | `analises/ANALISE_COMPARATIVA_V5_vs_LIA.md` |

**Header de obsolescência RECOMENDADO em cada um (modelo):**
```markdown
> **🗄 ARQUIVADO em 2026-05-10.** Doc movido de `WeDO/analises/` ou `WeDO/planos/` para `WeDO/_archive/2026-05-10/`.
> **Status:** snapshot histórico — válido até a data de "última atualização" no próprio doc. **Não usar como evidência viva** sem cross-check via grep/sensor no código (...)
> **Para estado atual da plataforma, ver:** `WeDO/auditoria_2026-05-10/00-CAPACIDADES_LIVE.md`
> Preservado para rastreabilidade histórica.
```

---

### ✅ HEADER CANONICAL VIVO RECOMENDADO (9) — in-place

| # | Doc | Pasta | Tema | Próxima validação |
|---|---|---|---|---|
| 1 | `mapeamento_capacidades_prompts_lia.md` | `analises/` | 4 contextos de prompt × tools × v5 comparison | Fase 4 (será atualizado) |
| 2 | `ANALISE_COMPARATIVA_V5_vs_LIA.md` | `analises/` | Comparativo arquitetura LIA vs v5 (19/03/2026) | Fase 4 |
| 3 | `diagnostico_arquitetura_codigo_lia_vs_v5.md` | `analises/` | Diagnóstico profundo de implementação | Fase 4 |
| 4 | `relatorio_capacidades_prompts_lia.md` | `analises/` | Capacidades expandido (6.609 linhas) | Fase 4 |
| 5 | `Paralelo_LIA_vs_V5_Arquitetura_IA.md` | `analises/` | Paralelo arquitetura agentes | Fase 4 |
| 6 | `RELATORIO_AUDITORIA_LIA.md` | `analises/` | Síntese executiva auditoria (15/03/2026) | Fase 4 |
| 7 | `mapa_inteligencia_lia_completo.md` | `analises/` | Mapa arquitetura agentes | Fase 4 |
| 8 | `AUDITORIA_TECNICA_EXECUCAO.md` | `analises/` | Plano execução das recomendações (28/02/2026) | Fase 4 |
| 9 | `PLANO_IMPLEMENTACAO_STATUS.md` | `planos/` | Registro de fases concluídas | Fase 4 (entradas adicionadas) |

**Header RECOMENDADO in-place no topo (modelo):**
```markdown
> **✅ CANONICAL VIVO.** Última validação: 2026-05-10 (Fase 0 da auditoria profunda).
> Doc consultado e cruzado contra código real no Replit branch `feat/benefits-prv-canonical`.
> **Visão consolidada e atualizada:** `WeDO/auditoria_2026-05-10/00-CAPACIDADES_LIVE.md`
> **Princípio de uso:** doc é referência, **código é fonte de verdade**.
```

---

### 🔵 MANTIDOS SEM ALTERAÇÃO (7) — referência permanente

Frameworks atemporais. Sem header de obsolescência ou canonical (são corretos por construção).

| # | Doc | Pasta | Razão de manter |
|---|---|---|---|
| 1 | `PLAYBOOK_AUDITORIA_PROFUNDA.md` | `analises/` | Framework 14-dim + 12-dim + 13-Crenças (3171 linhas) — atemporal |
| 2 | `ANALISE_COMPETITIVA_2026.md` | `analises/` | Benchmark mercado IA recrutamento — atualização independente |
| 3 | `ANALISE_ESTRATEGICA_CAMADA_INTELIGENCIA.md` | `analises/` | Estratégia camada inteligência (vs 8 concorrentes) |
| 4 | `AUDITORIA_GUIA_MIGRACAO.md` | `analises/` | Guia migração v5 → Compliance v2.2 |
| 5 | `COMPETITIVE_ANALYSIS_AI_RECRUITING_AGENTS.md` | `analises/` | Análise competitiva — metodologia atemporal |
| 6 | `NLP_CLUSTERING_STRATEGIC_ANALYSIS.md` | `analises/` | Recomendação estratégica NLP |
| 7 | `analise-viabilidade-saas-stack.md` | `analises/` | Análise viabilidade SaaS stack — independent |

---

### ⏳ PENDENTES (10) — arquivar APÓS Fase 4 produzir substituto

Os 10 docs de plano que serão substituídos pelo `04-ROADMAP_PRIORIZADO.md`. Por enquanto vivem (Fase 4 ainda não rodou). Quando Fase 4 entregar, estes serão movidos com header de obsolescência.

| # | Doc | Pasta | Substituto previsto |
|---|---|---|---|
| 1 | `PLANO_SPRINTS_Y1_Y5.md` | `planos/` | `04-ROADMAP_PRIORIZADO.md` |
| 2 | `PLANO_IMPLEMENTACAO_GAPS_IA.md` | `analises/` | `04-ROADMAP_PRIORIZADO.md` |
| 3 | `PLANO_IMPLEMENTACAO_INTELIGENCIA.md` | `analises/` | `04-ROADMAP_PRIORIZADO.md` |
| 4 | `GUIA_TESTES_ONDA1.md` | `analises/` | Será incorporado ao roadmap (test strategy) |
| 5 | `MVP_DEVELOPMENT_SPEC.md` | `planos/` | `04-ROADMAP_PRIORIZADO.md` (consolidar) |
| 6 | `PLANO_ACAO_AGENTES_IA.md` | `planos/` | `04-ROADMAP_PRIORIZADO.md` |
| 7 | `PLANO_AJUSTE_PROTOTIPO.md` | `planos/` | `04-ROADMAP_PRIORIZADO.md` |
| 8 | `PLANO_REVISAO_JOB_WIZARD_V2.md` | `planos/` | Feature-específico — incorporar ou deprecar |
| 9 | `mvp-alpha-scenarios.md` | `planos/` | Cenários refinados em `02-SMOKE_TESTS_RESULTS.md` (Fase 2) |
| 10 | `plano_implementacao_wizard.md` | `planos/` | Feature-específico — incorporar ou deprecar |

---

## Antes / Depois

### Estado atual em GitHub canonical (INTOCADO)
```
WeDOTalentcc/wedotalent02202026/WeDO/
├── analises/          (28 .md, mistura de canonical + obsoleto + duplicado)
├── planos/            (9 .md, mistura)
└── (sem README.md)
```

### Estado RECOMENDADO (se Anderson/time aplicar a higiene)
```
WeDO/
├── README.md                              [NEW — índice canonical]
├── auditoria_2026-05-10/                  [NEW — Fase 0/0.5 outputs]
│   ├── 00-CAPACIDADES_LIVE.md             [Fase 0]
│   └── 00b-INVENTARIO_DOCUMENTAL.md       [Fase 0.5 — este doc]
├── analises/                              (18 .md vivos: 8 canonical com header + 7 referência + 3 substituível)
├── planos/                                (8 .md vivos: 1 canonical com header + 7 substituível)
└── _archive/
    └── 2026-05-10/
        ├── analises/   (10 .md arquivados)
        └── planos/     (1 .md arquivado: PENDENTES_IA.md)
```

### Estado real LOCAL hoje
```
/Users/paulomoraes/Documents/wedotalent_audit_2026-05-10/  ← FORA do clone canonical
├── WeDO_README.md                         [modelo do README sugerido]
└── auditoria_2026-05-10/
    ├── 00-CAPACIDADES_LIVE.md             [Fase 0]
    └── 00b-INVENTARIO_DOCUMENTAL.md       [Fase 0.5 — este doc, agora prescritivo]

/Users/paulomoraes/Documents/Python/wedotalent02202026/  ← clone GitHub canonical
└── WeDO/  ← INTOCADO, working tree limpo após git restore
```

### Estado real REPLIT hoje
```
lia-agent-system/.audit/2026-05-10/   ← branch feat/benefits-prv-canonical
├── 00-CAPACIDADES_LIVE.md             [commit 48cdd3bd9]
└── 00b-INVENTARIO_DOCUMENTAL.md       [commit 0148ba10c]
```

**Métricas (se aplicado no canonical):**
- Docs vivos sem ruído: 26 (era 37) → redução de 30%
- Cada canonical vivo tem header explícito sobre status
- Zero deleções — 100% rastreabilidade preservada
- README.md serve de entry point único

---

## Princípios aplicados

1. **Código é fonte de verdade** — nenhum doc arquivado pode contribuir TODO ao roadmap sem revalidação via grep/sensor.
2. **Arquivar > deletar** — preservação histórica vale mais que limpeza visual.
3. **Headers explícitos** — cada doc agora declara seu status (canonical vivo, arquivado, ou referência permanente). Nenhum estado ambíguo.
4. **Cross-references** — toda referência de doc a doc usa link relativo, permitindo navegação.
5. **Versionamento por data** — pasta `_archive/2026-05-10/` permite futuras auditorias sem misturar com este momento.

---

## Sensores e métricas (recomendação — se aplicado no canonical)

| Métrica | Valor pretendido | Status atual no canonical |
|---|---|---|
| Docs em `analises/` antes / depois | 28 / 18 | 28 (intocado) |
| Docs em `planos/` antes / depois | 9 / 8 | 9 (intocado) |
| Docs com header canonical | 9 | 0 (intocado) |
| Docs com header arquivado | 11 | 0 (intocado) |
| Deleções | 0 | 0 ✅ |
| README.md em `WeDO/` | Sim | Não (modelo gerado em `~/Documents/wedotalent_audit_2026-05-10/WeDO_README.md`) |

## Próximos passos para Anderson/time canonical

Se o time canonical optar por aplicar:

1. Criar branch dedicada (ex: `chore/wedo-doc-hygiene-2026-05-10`) — não em main/develop
2. Seguir tabela acima de archive (11 docs) e canonical headers (9 docs)
3. Copiar `~/Documents/wedotalent_audit_2026-05-10/WeDO_README.md` → `WeDO/README.md`
4. PR para review do time
5. Sem urgência — não bloqueia roadmap. É housekeeping puro.

---

**Fim do 00b-INVENTARIO_DOCUMENTAL.md.**

Próximo: aprovação Paulo → Fase 1 (auditoria estrutural com 4 Explore agents paralelos × 14 dimensões).
