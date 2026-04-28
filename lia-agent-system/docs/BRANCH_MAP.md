# Branch Map — lia-agent-system (Replit)

> **Mapa de navegação canônico do repositório.** Atualizado: 2026-04-27.
> Branch de trabalho ativa: `feat/orch-migration-sprint-I`
> Cobertura: ~600 commits organizados em 18 milestones e 19 seções temáticas.

---

## Índice rápido por tema

| # | Tema | Tag de milestone |
|---|---|---|
| §1 | Teams Integration (Wave 1–9) | `milestone/teams-integration-complete` |
| §2 | Harness / Orchestrator Migration | `milestone/harness-orchestrator-v1` |
| §3 | LIA Maturity Program (FIX 1-28) | `milestone/lia-maturity-track1` |
| §4 | Rail Features (PR-A → PR-O) | `milestone/rail-features-sprint1` |
| §5 | Tasks #712–#886 | — |
| §6 | Chat Unificado — Saneamento Fase 1 | `milestone/chat-saneamento-fase1-p0` |
| §7 | WorkflowRail UX Redesign (UX-1 a UX-7) | `milestone/workflow-rail-ux7` |
| §8 | Domínios Production-Ready + Glossário | `milestone/domains-production-ready`, `milestone/glossary-canonical-281` |
| §9 | DEFAULT_DOMAIN + Tenant Isolation | — |
| §10 | Teams — Validação Inicial (pré-Wave 1) | `milestone/teams-task706-validation` |
| §11 | Candidate Portal (Spec + Research) | `milestone/candidate-portal-rails-spec` |
| §12 | DEVELOPER_HANDOFF — PARTES A–L | — |
| §13 | PARTE D — Foundation Stack (D0-D5) | `milestone/parte-d-complete` |
| §14 | LLM Factory + BYOK + Quality Tier Guard | `milestone/byok-llm-factory-adr-018` |
| §15 | WSI — Métrica + Compliance + Transparência | `milestone/wsi-scale-0-10-atomic-flip`, `milestone/wsi-eu-ai-act-compliance`, `milestone/wsi-phase2-remediation` |
| §16 | LIA Persona Diagnostic + Identity Override | `milestone/lia-persona-diagnostic` |
| §17 | Eval Framework — Iterative Hardening | — |
| §18 | Senioridade + Job Migration | — |
| §19 | Chat Unificado — Hardening de Ações | — |

---

## Como usar este documento com IA (Claude Code, Cursor, agentes)

Este documento foi escrito para ser **consumível por LLM** além de humanos. Para que sua IA aproveite ao máximo:

### 1. Inclua-o no contexto da sessão
- **Claude Code:** mencione `@docs/BRANCH_MAP.md` na primeira mensagem da sessão.
- **Cursor:** adicione como `@Doc` permanente do workspace, ou inclua no `.cursorrules`.
- **Claude API direta:** prefixe o system prompt com o conteúdo deste arquivo.

### 2. Padrão de prompt recomendado

```
Quero trabalhar em <tema>. Antes de qualquer mudança:
1. Leia BRANCH_MAP.md e identifique a seção relevante (1-19).
2. Liste os milestones e docs canônicos cruzados.
3. Rode os comandos `git log --grep` listados para ver o histórico.
4. Só então proponha a mudança.
```

### 3. Cross-references obrigatórias por tema

Quando trabalhar em um tema da seção 1-19, **sempre** cruze este BRANCH_MAP com os docs canônicos abaixo:

| Tema | Doc canônico raiz | Doc específico |
|---|---|---|
| Geral / qualquer mudança | [`CLAUDE.md`](../../CLAUDE.md) | — |
| Arquitetura | [`ARCHITECTURE.md`](../../ARCHITECTURE.md), [`ARCHITECTURE_TARGET.md`](../../ARCHITECTURE_TARGET.md) | [`docs/architecture/AI_AGENT_AUDIT_REPORT.md`](architecture/AI_AGENT_AUDIT_REPORT.md) |
| Handoff principal | [`DEVELOPER_HANDOFF.md`](../../DEVELOPER_HANDOFF.md) | (PARTES A–L, ver §12) |
| Teams | — | [`docs/DOC_HANDOFF_TEAMS.md`](DOC_HANDOFF_TEAMS.md), [`docs/CONTRATO_RAILS_TEAMS.md`](CONTRATO_RAILS_TEAMS.md), [`docs/TEAMS_ENDPOINTS_AND_DIAGRAM.md`](TEAMS_ENDPOINTS_AND_DIAGRAM.md) |
| LIA Maturity | — | [`docs/HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md`](HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md), [`docs/LIA_MATURITY_ROADMAP.md`](LIA_MATURITY_ROADMAP.md), [`docs/LIA_MATURITY_LEAP_RESUMO.md`](LIA_MATURITY_LEAP_RESUMO.md) |
| LLM Factory / BYOK | [`LLM_FACTORY_HANDOFF_v2.md`](../../LLM_FACTORY_HANDOFF_v2.md) | ADR-018 |
| Hardening / Segurança | [`HARDENING_PLAN.md`](../../HARDENING_PLAN.md) | [`docs/PRODUCTION_READINESS_GAPS.md`](PRODUCTION_READINESS_GAPS.md), [`docs/PRODUCTION_READINESS_REPORT.md`](PRODUCTION_READINESS_REPORT.md) |
| Multi-tenancy / RLS | — | [`docs/RLS_CONTRACT.md`](RLS_CONTRACT.md), [`docs/CANONICAL_SOURCES_SPEC.md`](CANONICAL_SOURCES_SPEC.md) |
| Compliance EU AI Act | — | [`docs/FRIA_EU_AI_ACT.md`](FRIA_EU_AI_ACT.md), [`docs/FAIRNESS_GUARD_COVERAGE.md`](FAIRNESS_GUARD_COVERAGE.md) |
| Conceitos de IA | — | [`docs/CONCEITOS_IA_WEDOTALENT.md`](CONCEITOS_IA_WEDOTALENT.md), [`docs/MAPA_CAMADA_INTELIGENCIA.md`](MAPA_CAMADA_INTELIGENCIA.md) |
| Histórico de tasks | — | [`docs/HISTORICO_TASKS_IMPLEMENTADAS.md`](HISTORICO_TASKS_IMPLEMENTADAS.md) |
| Runbooks operacionais | — | [`docs/RUNBOOK_INCIDENT_PLAYBOOKS.md`](RUNBOOK_INCIDENT_PLAYBOOKS.md), [`docs/RUNBOOK_DEGRADATION.md`](RUNBOOK_DEGRADATION.md), [`docs/RUNBOOK_BACKUP_RECOVERY.md`](RUNBOOK_BACKUP_RECOVERY.md) |
| Rails contract | — | [`docs/RAILS_GAPS.md`](RAILS_GAPS.md), [`docs/AUDIT_FORK_VS_RAILS_2026-04-05.md`](AUDIT_FORK_VS_RAILS_2026-04-05.md) |
| API | [`API_REFERENCE.md`](../../API_REFERENCE.md), [`API_EXAMPLES.md`](../../API_EXAMPLES.md) | [`docs/API_REFERENCE.md`](API_REFERENCE.md) |

### 4. Fluxos de trabalho prontos

| Pergunta da IA / dev | Resposta com este map |
|---|---|
| "Onde está o código de Teams?" | §1 (Teams Integration) + grep `(teams)` + `git checkout milestone/teams-integration-complete` |
| "O que é PARTE D?" | §13 + `DEVELOPER_HANDOFF.md` PARTE D + `git show milestone/parte-d-complete` |
| "Como o BYOK funciona?" | §14 + `LLM_FACTORY_HANDOFF_v2.md` + ADR-018 + tag `milestone/byok-llm-factory-adr-018` |
| "Por que escala WSI 0-10?" | §15 + Task #497 PR1/PR2/PR3 + ADR-017 |
| "Eval framework está quebrado, o que tentar?" | §17 — 30 commits `fix(eval):` documentam padrões já corrigidos |
| "Persona da LIA inconsistente?" | §16 + Task #527 (120 sondas automatizadas) |

### 5. Convenções de commit que este map aproveita

- `feat(<dominio>):` — feature em domínio específico (teams, lia, wsi, harness…)
- `fix(<dominio>):` — bug fix
- `docs(handoff): PARTE X` — adição cumulativa ao DEVELOPER_HANDOFF.md
- `Task #NNN` — task numerada do backlog
- `FIX N` — correção numerada do programa LIA Maturity
- `Wave N.M` — entrega Teams (W1.1, W2.3, W9.2…)
- `feat(orch-migration): Sprint N` — sprint de migração do orquestrador

Use `git log --grep="<padrão>"` para isolar qualquer um deles.

---

## Branches ativas

| Branch | Status | Propósito |
|---|---|---|
| `feat/orch-migration-sprint-I` | **ATIVA** — base de todo trabalho recente | Acumulação principal. Contém Teams, Harness, LIA Maturity, Rail, Tasks |
| `feat/pr-a-rail-a-metadata` | Pronta para PR | Rail A — metadata, Tier 0.0, Pydantic schema, `rail_a_hint_override` |
| `feat/pr-b-offer-review` | Pronta para PR | Offer Review Modal + 3 triggers + proxy routes + Zustand store |
| `feat/pr-d-ui-action-unified` | Pronta para PR | UIAction Pydantic mirror + 14 testes (espelho BE/FE) |
| `feat/admin-tenant-rails-account-sync` | Integrada em sprint-I | Admin cria ClientAccount no Rails no momento da criação do cliente |
| `fix/kanban-e2e-bugs` | Integrada em sprint-I | Restore daily-briefing-card + disc-assessment-modal |
| `backup/pre-pr-a-extract` | Backup | Snapshot antes de extrair PR-A para branch separado. Não usar. |
| `replit-sync-2026-04-17` | Histórico | Snapshot do estado em 2026-04-17. Apenas referência. |
| `main` | Desatualizada | Última sync com GitHub. Tudo novo está em `feat/orch-migration-sprint-I`. |

---

## Milestones (git tags)

Use `git show <tag>` para ver o commit de cada marco.

### Janela recente (commits à frente de `main`)

| Tag | Commit | O que marca |
|---|---|---|
| `milestone/teams-integration-complete` | `8656f5e9c` | Teams Wave 1-9 + docs handoff completos |
| `milestone/harness-orchestrator-v1` | `94a629c1d` | Orchestrator migration + canary kit entregues |
| `milestone/lia-maturity-track1` | `42d5dbb7b` | LIA Maturity Program Track 1 (FIX 1-28) completo |
| `milestone/rail-features-sprint1` | `710adfcef` | Rail features PR-A→PR-O Sprint 1 base |
| `teams/wave1-start` | `f7f972882` | Primeiro commit Teams (P0-1 multi-tenancy) |

### Janela anterior (já em `main` — Tasks #574–#712)

| Tag | Commit | O que marca |
|---|---|---|
| `milestone/teams-task706-validation` | `4a7191d99` | Task #706 — primeira validação prod do Teams (pré Wave 1) |
| `milestone/glossary-canonical-281` | `6e9287f50` | ADR-019 + glossário canônico 281 actions / 94 tools / 18 domínios |
| `milestone/domains-production-ready` | `f05db64d8` | Task #691 — padronização de domínios em evolução para production-ready |
| `milestone/chat-saneamento-fase1-p0` | `421cfdb99` | Task #580 — saneamento P0 da cadeia de execução do chat unificado |
| `milestone/funil-unificado-fase2` | `f3ddab57b` | Task #592 — especificação Fase 2 do funil unificado |
| `milestone/workflow-rail-ux7` | `c07d3d5dc` | UX-7 — WorkflowRail compact single-line bar com hover popovers |
| `milestone/candidate-portal-rails-spec` | `1b0ca9629` | Spec completa do Candidate Portal (Rails + Replit) |

### Janela 3 (Tasks #494–#570 — fundações WSI + BYOK + Persona)

| Tag | Commit | O que marca |
|---|---|---|
| `milestone/parte-d-complete` | `8314d3517` | PARTE D entregue (D0-D5: Apify gateway, LIA tools, PreConditionChecker, Manifest, onboarding) |
| `milestone/byok-llm-factory-adr-018` | `aa6d38cd1` | LLM Factory + BYOK compliance + Quality Tier Guard + audit trail (ADR-018) |
| `milestone/wsi-scale-0-10-atomic-flip` | `689b90885` | Task #497 PR2 — flip atômico WSI escala 0-5 → 0-10 (engine + DB + Pydantic) |
| `milestone/wsi-eu-ai-act-compliance` | `6ac807839` | Task #511 — Compliance EU AI Act WSI (audit trail + response_hash + endpoint) |
| `milestone/lia-persona-diagnostic` | `e4e06c10d` | Task #527 — Diagnóstico de persona da LIA automatizado (120 sondas) |
| `milestone/wsi-phase2-remediation` | `1513a89ef` | Phase 2 WSI/Screening remediation — G1 + G2 entregues |
| `milestone/canonical-fix-skill` | `0a4170019` | Task #495 — Skill `canonical-fix` criada (corrigir na origem, sem workaround) |

---

## Navegação por tema em `feat/orch-migration-sprint-I`

Para listar commits de um tema específico:

```bash
# Teams (Wave 1–9 + docs + testes)
git log --oneline --grep="teams" feat/orch-migration-sprint-I

# Harness / Orchestrator migration
git log --oneline --grep="orch-migration\|harness" feat/orch-migration-sprint-I

# LIA Maturity Program (FIX 1-35 + Ondas)
git log --oneline --grep="lia.*FIX\|Onda" feat/orch-migration-sprint-I

# Rail features (PR-A, PR-B, PR-C…)
git log --oneline --grep="rail\|pr-[a-z]" feat/orch-migration-sprint-I

# Security / Privacy / LGPD
git log --oneline --grep="security\|privacy\|lgpd\|pii" feat/orch-migration-sprint-I

# Multi-tenancy fixes
git log --oneline --grep="multi-tenancy\|multi-tenant\|company_id" feat/orch-migration-sprint-I

# Tasks numeradas (#xxx)
git log --oneline --grep="Task #8" feat/orch-migration-sprint-I
```

---

## Mapa de temas por commit range

### 1. Teams Integration (Wave 1–9)
- **Commits:** `f7f972882` → `8656f5e9c`
- **Tag de início:** `teams/wave1-start`
- **Tag de fim:** `milestone/teams-integration-complete`
- **Documentação:** `docs/DOC_HANDOFF_TEAMS.md`, `docs/CONTRATO_RAILS_TEAMS.md`, `docs/TEAMS_ENDPOINTS_AND_DIAGRAM.md`
- **Testes:** `tests/integration/test_teams_*.py`, `tests/smoke/test_teams_e2e_smoke.py`
- **Grep:** `git log --grep="teams"`

**O que foi implementado:**
- Multi-tenancy (company_id server-side, nunca do payload)
- Bot Framework webhook + JWT validation
- Adaptive Cards (resposta rica)
- Tab Pipeline + Tab Dashboard (SSO OBO)
- Proactive notifications (new candidate, screening complete, daily digest 08h)
- Group/channel broadcast (W9.1)
- Multimedia: PDF→CV, imagem→Gemini Vision, áudio/vídeo→STT, documentos (W9.2+W9.3)
- PromptInjectionGuard (W7.2) + PII strip antes do LLM (W7.1)
- LGPD consent gate em /webhook approve (W7.3)
- Calendário Microsoft Graph (agendamento de entrevistas)

---

### 2. Harness / Orchestrator Migration
- **Commits:** `f4989d53b` → `94a629c1d`
- **Tag:** `milestone/harness-orchestrator-v1`
- **Grep:** `git log --grep="orch-migration\|harness"`

**O que foi implementado:**
- PlanOrchestrationService (Sprint II)
- FallbackReActService (LIA-A04)
- RubricDispatchService (CV match BARS)
- AnalyticsDispatchService
- OTLP tracing + canary rollout kit
- ADR-019 canonical span constants
- 50 characterization tests (Sprint I-C)
- G6+G7 hooks block-only

---

### 3. LIA Maturity Program (Track 1)
- **Commits:** `82009b0c8` → `42d5dbb7b`
- **Tag:** `milestone/lia-maturity-track1`
- **Grep:** `git log --grep="feat(lia)\|fix(lia)\|FIX [0-9]"`
- **Documentação canônica:**
  - [`docs/HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md`](HANDOFF_LIA_MATURITY_PROGRAM_COMPLETE.md) — 740 linhas, 33 referências aos FIX, 81 commit hashes citados
  - [`docs/LIA_MATURITY_ROADMAP.md`](LIA_MATURITY_ROADMAP.md) — 289 linhas, source of truth do programa, 19 referências aos FIX
  - [`docs/LIA_MATURITY_LEAP_RESUMO.md`](LIA_MATURITY_LEAP_RESUMO.md) — 319 linhas, resumo explicativo para o time

**O que foi implementado:**
- FIX 1–28: grounded capability catalog, DomainActions, FairnessGuard, HITL, briefing, memory, proactive hints, cost tracker, persona consistency, error recovery
- Ondas 2.x–5.x: episodic memory, citation, workflow_context, history compaction
- Eval golden set + CI workflow

**Nota:** os 3 docs acima foram apagados acidentalmente pelo commit `f7627f1bf "Saved progress at the end of the loop"` (auto-commit do Replit Agent) e recuperados via `git cat-file` em `014ea00a8`.

---

### 4. Rail Features (PR-A → PR-O)
- **Tag base:** `milestone/rail-features-sprint1`
- **Branches separados:** `feat/pr-a-rail-a-metadata`, `feat/pr-b-offer-review`, `feat/pr-d-ui-action-unified`
- **Grep:** `git log --grep="rail\|feat(pr-"`

| Sub-feature | Branch / Commit | Status |
|---|---|---|
| PR-A Rail A metadata + Tier 0.0 | `feat/pr-a-rail-a-metadata` | Branch separado — pronto para PR |
| PR-B Offer Review Modal | `feat/pr-b-offer-review` | Branch separado — pronto para PR |
| PR-C Register Hire | `ec7d4a817` | Em `sprint-I` |
| PR-D UIAction unified | `feat/pr-d-ui-action-unified` | Branch separado — pronto para PR |
| PR-J Capability Map + Entity Resolver | `43802d069` | Em `sprint-I` |
| PR-K/L/M/N/O | vários commits | Em `sprint-I` |

---

### 5. Tasks #712–#886 (Features de produto)
- **Grep:** `git log --grep="Task #"`
- Sem branch separado — todos em `feat/orch-migration-sprint-I`
- Temas cobertos: onboarding proativo, wizard vagas, benefícios, WSI/Bloom terms, triagem, funil de candidatos, multi-tenancy

---

## Janela anterior — Tasks #574–#712 (já em `main`)

### 6. Chat Unificado — Saneamento Fase 1 + Funil Unificado
- **Tag base:** `milestone/chat-saneamento-fase1-p0`
- **Tasks principais:** #580, #582, #583, #584, #591, #592
- **Grep:** `git log --grep="chat unificado\|Saneamento\|Funil unificado"`

**O que foi implementado:**
- Saneamento P0 da cadeia de execução do chat unificado (Task #580)
- Phase 2 chat sanitization para 5 domínios P1 (Task #582)
- Zero actions sem tool nem handler no chat unificado (Task #583)
- Auto-discovery de `AGENT_TYPE_TO_DOMAIN` (Task #584)
- Funil unificado Fase 1 educativa (Task #592) + spec Fase 2 (`f3ddab57b`)
- Stub→real handlers em todo o chat (Task #602)

---

### 7. WorkflowRail UX Redesign (Sprints UX-1 a UX-7)
- **Tag final:** `milestone/workflow-rail-ux7`
- **Spec técnica:** `a39b48d5f docs(ux): UX_REDESIGN_COMPETITIVO_SPEC.md`
- **Grep:** `git log --grep="WorkflowRail\|workflow-rail\|UX-[0-9]"`

**O que foi implementado:**
- 5 iterações de design da WorkflowRail (compact, scrollable, popovers, theme toggle)
- Coexistência WorkflowRail × Chat sem poluição (Task #617)
- Tracking de next-step clicks e panel toggles (Task #589)
- Thinking pulse dentro do popover (Task #655)

---

### 8. Domínios Production-Ready + Glossário Canônico
- **Tags:** `milestone/domains-production-ready`, `milestone/glossary-canonical-281`
- **Tasks:** #687, #690, #691, #692
- **Grep:** `git log --grep="glossário\|production-ready\|execute_action\|ADR-019"`

**O que foi implementado:**
- ADR-019 + glossário central: **281 actions / 94 tools / 18 domínios** (`6e9287f50`)
- `execute_action` coverage para todos os 11 domínios (Task #687)
- Padronização de domínios em evolução (Task #691)
- Glossário Central + sync automático + CI guard (Task #692)
- Enriquecimento de descrições de actions e tools (Task #690)

---

### 9. DEFAULT_DOMAIN + Tenant Isolation
- **Tasks:** #670, #672, #673
- **Grep:** `git log --grep="DEFAULT_DOMAIN\|tenant-isolation\|tenant_id"`

**O que foi implementado:**
- DEFAULT_DOMAIN routing warning + chat-capabilities CI gate (Task #672)
- Consolidate tenant-isolation residual — fecha #329, #335, #336, #359, #361 (Task #673)
- Proteção de 8 dirs estratégicos + recategorização (Task #670)
- WSI tenant id forwarding (Task #334)

---

### 10. Teams — Validação Inicial (pré-Wave 1)
- **Tag:** `milestone/teams-task706-validation`
- **Task:** #706
- **Grep:** `git log --grep="Teams\|microsoft"`

**O que foi implementado:**
- Configuração e validação inicial do LIA Microsoft Teams app para produção (`4a7191d99`)
- Base que mais tarde foi expandida nas Waves 1-9

---

### 11. Candidate Portal (Spec + Research)
- **Tag:** `milestone/candidate-portal-rails-spec`
- **Tasks:** #574, #576
- **Grep:** `git log --grep="candidate.*portal\|chat candidato"`
- **Documentação:** `docs/CANDIDATE_PORTAL_RAILS_SPEC.md`

**O que foi implementado:**
- Auditoria técnica do chat candidato pós-aplicação (Task #574)
- Proposta de construção do chat candidato pós-aplicação (Task #576)
- Spec Rails + Replit completa (`1b0ca9629`)
- Market research — chat candidato pós-aplicação

---

### 12. DEVELOPER_HANDOFF — PARTES A–I
- **Documentação:** `DEVELOPER_HANDOFF.md`
- **Grep:** `git log --grep="docs(handoff): PARTE"`

**Estrutura cumulativa do handoff principal:**
- PARTE A–E: `fc76b0a88 — guia completo PARTES A-E`
- PARTE F: `3722e7b38 — conversational UX + P2/P3 hardening`
- PARTE G: `04ff86a65 — LIA Eval 62→70/73, 15 fixes`
- PARTE H: `6aa9492fb — chat ReAct, stub→real, scheduling, WSI tenant, WorkflowRail UX, IDOR`
- PARTE I: `df34f5707 — BETA badge polish, hide chat/rail on auth routes, e2e fixes`
- PARTE J: `97ac557f1 — A Jornada Completa (narrativa)`
- PARTE K: `49464a0c6 — FIX 14-17 conversation continuity layer`
- PARTE L: `ba28c86ff — runtime-inert gaps pattern`

---

## Janela 3 — Tasks #494–#570 (fundações WSI + BYOK + Persona)

### 13. PARTE D — Foundation Stack (D0-D5)
- **Tag:** `milestone/parte-d-complete`
- **Grep:** `git log --grep="parte-d\|feat(.*): D[0-9]"`

**O que foi implementado:**
- D0 — Apify gateway com enforced tracking + budget check per tenant (`a2b2310fb`)
- D1 — LIA tools enrichment + company settings tools (`eee514587`)
- D2 — PreConditionChecker + 5 new proactive checks (`08a912340`)
- D4 — Platform Manifest: single source of truth para pages, methodology, capabilities (`f4106776c`)
- D5 — Guided onboarding flow no `company_settings` agent (`3464e6021`)
- Close 4 PARTE D gaps — full tracking + canonical schema + manifest wiring + proactive UI (`8314d3517`)

---

### 14. LLM Factory + BYOK + Quality Tier Guard
- **Tag:** `milestone/byok-llm-factory-adr-018`
- **ADR:** `f4462e2ab — ADR-018 LLM Factory / BYOK contract`
- **Grep:** `git log --grep="byok\|llm-factory\|BYOK"`

**O que foi implementado:**
- LLM Factory canonical com BYOK compliance (`aa6d38cd1`)
- Quality Tier Guard (impede downgrade de modelo via BYOK do tenant)
- Audit trail per LLM call (response_hash + session_id)
- Frontend UI BYOK (seções 9+10)
- Auditoria E2E + correção de 4 bugs P0 de audit trail e BYOK bypass
- BUG-07 — WSI analyze-response BYOK + Quality Tier Guard
- Mapa completo de **54 consumidores LLM** auditados (`5d34569ef`)

---

### 15. WSI — Métrica + Compliance EU AI Act + Transparência
- **Tags:** `milestone/wsi-scale-0-10-atomic-flip`, `milestone/wsi-eu-ai-act-compliance`, `milestone/wsi-phase2-remediation`
- **ADR:** `51a09caec — ADR-017 (Phase 1 audit + selos rev. 5)`
- **Grep:** `git log --grep="wsi\|WSI\|Bloom\|Dreyfus"`

**O que foi implementado:**
- Phase 1 remediação WSI (ADR-017) — selos rev. 5
- Phase 2 remediação — G1 + G2 entregues; G3 promovido a tasks
- Task #495 — skill `canonical-fix` criada (princípio: corrigir na origem)
- Task #496 — extrair `transcript_extractor` do orchestrator
- Task #497 — flip atômico escala WSI 0-5 → 0-10 (PR1: extract constants, PR2: atomic flip, PR3: frontend)
- Task #498 — split tech/behav 100% determinístico via category explícita
- Task #510 — Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates)
- Task #511 — Compliance EU AI Act WSI (audit_trail + response_hash + endpoint)
- Task #512 — frontend escala 0-10
- Task #523 — refactor 23 consumidores WSI /5 → /10 (audit rev. 14)
- Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03)
- Task #529 — UI Modal Triagem: banner degraded + breakdown granular
- Task #530 — Kanban: indicador visual de modo degradado no score WSI
- Task #534 — Backfill `transparency_extras` para legacy WSI response analyses
- Task #535 — Tests UI wsi-modal LGPD/EU AI Act
- Task #538 — "Apenas modo degradado" toggle no job kanban
- Task #541 — WSICompactPipeline LLM call regression tests

---

### 16. LIA Persona Diagnostic + Identity Override
- **Tag:** `milestone/lia-persona-diagnostic`
- **Grep:** `git log --grep="persona\|identity\|diagnóstico"`

**O que foi implementado:**
- Diagnóstico manual de persona da LIA (roteiro + harness Playwright) — `5a7205e44`
- Task #527 — automate LIA persona diagnostic (120 sondas)
- LIA identity override — prevent Gemini from leaking model identity (`881aef9d0`)
- Phase 1 intercept para identity questions — LIA never calls Gemini for "quem é você" (`44e381ce5`)
- Persona Diagnostic cross-check probes really hit the intended specialised agent
- Fix 23 falhas críticas do diagnóstico de persona (`32cd180b4`)

---

### 17. Eval Framework — Iterative Hardening
- **Grep:** `git log --grep="fix(eval):"`

**O que foi implementado (em ondas iterativas, ~30 commits `fix(eval):`):**
- UnboundLocalError no executor + short job_id em query_tools
- UUID/varchar JOIN mismatch no candidate/sourcing pipeline
- CM-001/CM-003 — remove all wrong CAST uuid on varchar
- CO-002 — offer letter generation instruction no communication domain
- KB-005/006 — UUID guard + WZ-002/003 keywords + MT-002 job_title extraction
- Salary benchmark em analytics + offer ID rule + negation cancel pattern
- Portuguese-aware criteria matching para WZ-002/003 agile/data/location checks
- list_jobs routing + duplica keyword
- name resolution + implicit job context + wizard tenant scope
- Task #563 — agentic eval framework + canonical-fix consolidation

---

### 18. Senioridade + Job Migration
- **Tasks:** #531, #539, #559, #560, #562
- **Grep:** `git log --grep="seniority\|senioridade\|level"`

**O que foi implementado:**
- Task #531 — Migração `job.level` → `seniority` (write-both + leitura unificada)
- Task #539 — Remove legacy `level` field do Job type
- Task #559 — Show "Senioridade não informada" instead of guessing "Pleno"
- Task #560 — cobertura E2E de edição de senioridade
- Task #562 — Padronizar e enriquecer card do Kanban de Vagas

---

### 19. Chat Unificado — Hardening + Auditoria de Ações
- **Tasks:** #569, #570
- **Grep:** `git log --grep="hardening\|aprendizado\|Task #569\|Task #570"`

**O que foi implementado:**
- Task #569 — Auditoria das ações de mensagem do chat unificado e loop de aprendizado
- Task #570 — Hardening P0/P1 das ações do chat unificado
- Fix mensagens copy/thumbs

---

## Padrão para novos trabalhos (a partir de agora)

Para facilitar o handoff do time, **todo novo tema/feature deve ter branch próprio**:

```
feat/<tema>-<descricao-curta>
fix/<tema>-<descricao-curta>
```

Exemplos seguindo o padrão correto já adotado:
- `feat/pr-a-rail-a-metadata` ✅
- `feat/pr-b-offer-review` ✅
- `feat/teams-integration` (retroativo — teria sido o ideal)

**Não acumular temas diferentes em um branch de sprint.**

---

## Como criar um branch a partir de um milestone

```bash
# Criar branch de hotfix a partir do milestone Teams completo
git checkout -b fix/teams-<descricao> milestone/teams-integration-complete

# Ver o que mudou em Teams desde o milestone
git diff milestone/teams-integration-complete HEAD -- app/api/v1/teams.py
```

---

## Apêndice A — Templates de prompt para IA

Cole estes prompts diretamente no Claude Code, Cursor ou qualquer agente para acelerar onboarding.

### Template 1 — Onboarding em tema desconhecido

```
Estou começando a trabalhar em <tema>. Preciso entender:

1. Lê docs/BRANCH_MAP.md e identifica em qual seção §1-19 cai esse tema.
2. Lista as tags milestone correspondentes.
3. Lista os docs canônicos cruzados (DEVELOPER_HANDOFF, ADR, MATURITY, etc.)
4. Roda `git log --grep` para os 20 commits mais relevantes.
5. Para cada commit relevante, mostra o subject e o autor.
6. Resume em até 10 bullets o que entender do tema antes de eu propor mudança.

NÃO escreve código ainda. Só me devolve esse mapa.
```

### Template 2 — Investigar bug em tema mapeado

```
Bug observado: <descrição>

Antes de propor fix:
1. Identifica em docs/BRANCH_MAP.md qual seção §1-19 cobre esse tema.
2. Lê o último milestone do tema com `git show <tag>`.
3. Procura nos últimos 50 commits do tema (grep do BRANCH_MAP) por
   regressões similares ou commits que tocaram o arquivo afetado.
4. Cita 2-3 commits que parecem relacionados.
5. Propõe hipótese de causa-raiz baseada nessa cronologia.
6. SÓ depois propõe fix — alinhado a `canonical-fix` skill (corrigir na origem).
```

### Template 3 — Estender feature de tema existente

```
Quero adicionar <feature> ao tema <tema>.

1. Confirma em docs/BRANCH_MAP.md a seção e milestones do tema.
2. Verifica se há branch de feature ativo (ex: `feat/pr-X-<...>`).
   Se sim, criar a partir dele. Se não, criar branch novo seguindo
   o padrão `feat/<tema>-<descricao-curta>`.
3. Lê o doc canônico do tema (Teams → DOC_HANDOFF_TEAMS, BYOK → ADR-018, etc.)
   antes de qualquer linha de código.
4. Aplica skills production-quality + harness-engineering + canonical-fix.
5. Commit atomic ao final, mensagem `feat(<tema>): <descricao>`.
6. NÃO faz git push.
```

### Template 4 — Hotfix de produção urgente

```
Hotfix urgente: <descrição do incidente>

1. Identifica o tema em docs/BRANCH_MAP.md.
2. Cria branch a partir do último milestone estável do tema:
   `git checkout -b fix/hotfix-<...>  milestone/<tag>`
3. Aplica fix mínimo (não refatora).
4. Atualiza o RUNBOOK relevante em docs/RUNBOOK_*.md se for incidente recorrente.
5. Commit: `fix(<tema>): hotfix <descricao>` + nota no DEVELOPER_HANDOFF.md
   na PARTE atual.
6. NÃO faz push.
```

---

## Apêndice B — Manutenção deste documento

Quando este BRANCH_MAP fica desatualizado, ele perde valor rápido. Manter assim:

1. **A cada PR mergeado em `feat/orch-migration-sprint-I`:** se for um tema novo (não cabe em §1-19), adicionar nova seção numerada.
2. **A cada milestone significativo:** criar tag `milestone/<descricao>` e adicionar à tabela de Milestones.
3. **A cada novo doc canônico em `docs/`:** adicionar linha à tabela "Cross-references obrigatórias por tema" (seção "Como usar").
4. **A cada nova convenção de commit prefix:** adicionar à seção "Convenções de commit".

Atualizações a este arquivo devem usar commit message:
```
docs(nav): BRANCH_MAP — <descrição da atualização>
```

Para verificar quem atualizou por último:
```bash
git log --oneline -- docs/BRANCH_MAP.md
```

---

## Apêndice C — Estatísticas

- **Branches ativas:** 9 (1 ativa, 3 prontas para PR, 3 integradas, 2 históricas)
- **Milestones:** 18 tags `milestone/*`
- **Seções temáticas:** 19 (§1–§19)
- **Commits cobertos:** ~600 commits (3 janelas de ~200)
- **Docs canônicos cruzados:** 24 (root + docs/ + docs/architecture/)
- **Última atualização:** 2026-04-27


---

## Ondas 18-21 — Wizard Canonical Plugs (2026-04-28)

**Branch:** `feat/orch-migration-sprint-I` (sprint corrente)
**Harness:** sensor (computacional) — feedback_learning + canonical priority

### Mudanças aplicadas

| Arquivo | Mudança |
|---------|---------|
| `app/shared/chat_event_serializer.py` | Param `wizard_step_response` adicionado a `serialize_message()` |
| `app/shared/wizard_suggestion_priority.py` | **NOVO** — `WizardSuggestion` dataclass + `pick_canonical()` |
| `wizard_step_service/stage_description.py` | `apply_learning` plugado (F.1) |
| `wizard_step_service/stage_basic_info.py` | `apply_learning` plugado (F.2) |
| `wizard_step_service/stage_wsi.py` | `apply_learning` plugado (F.3) |
| `wizard_step_service/stage_review.py` | `apply_learning` plugado (F.4) |
| `wizard_step_service/stage_salary.py` | `pick_canonical()` wired — history + market priority (S.1) |
| `wizard_step_service/service.py` | `db` + `company_id` passados para os 4 handlers |
| `tests/unit/test_company_job_history_service.py` | **NOVO** — 7 cenários |
| `tests/unit/test_recruitment_template_service.py` | **NOVO** — 11 cenários |

### Nota de compatibilidade
`wizard_react_agent.py` foi intencionalmente deletado no Task #850 (canonical consolidation).
As mudanças C.2/P.1/C.4 do Mac (`followup/wizard-canonical-plugs`) são incompatíveis com
a arquitetura atual do Replit — omitidas propositalmente.

---

## Onda 22 — Wave 5 Sensors: Offer FE Invariants (2026-04-28)

**Branch:** `feat/orch-migration-sprint-I`
**Commit:** `4e6374302`
**Harness:** SENSOR (computacional) — pathlib-only, 10 guards, zero imports de runtime

### Arquivos entregues

| Arquivo | Mudança | Guard |
|---------|---------|-------|
| `plataforma-lia/src/components/offer-review-modal/OfferHITLBanner.tsx` | **NOVO** — banner HITL com `role="alert"` no estado de erro | Guard 8 (WCAG 2.1 AA) |
| `plataforma-lia/src/components/offer-review-modal/OfferReviewModal.tsx` | HITL two-step `idle→confirming→success/error` + `user_confirmation` | Guards 2, 3 |
| `plataforma-lia/src/components/offer-review-modal/OfferDataForm.tsx` | `aria-invalid={salaryOverBudget}` no campo salário | Guard 7 |
| `plataforma-lia/src/stores/offer-draft-store.ts` | `reset()/initialState` + `devtools` middleware + `setDraft/setOpen` | Guards 6, 10 |
| `plataforma-lia/src/hooks/offers/useOfferReviewFlow.ts` | `start()` chama `offersApi.createDraft`, `setDraft(draft)`, `setOpen(true)` | Guard 5 |
| `lia-agent-system/tests/unit/test_wave5_offer_fe_invariants.py` | **NOVO** — 10 sensors computacionais | Guards 1–10 |

### Resultado dos sensors
```
10/10 PASSED (feat/orch-migration-sprint-I, Replit)
Rodar com: pytest lia-agent-system/tests/unit/test_wave5_offer_fe_invariants.py --no-cov -v
```

### Guards implementados
1. `OfferReviewModal.tsx` ≤ 250 linhas — 193 linhas ✅
2. `user_confirmation: true` presente no modal (HITL nunca bypassado) ✅
3. Send só dispara após `confirmState="confirming"` ✅
4. `offersApi` usa `/api/backend-proxy` (nunca FastAPI direta) ✅
5. `useOfferReviewFlow.start()` chama `offersApi.createDraft`, `setDraft`, `setOpen` ✅
6. `useOfferDraftStore` tem `reset()` + `initialState` ✅
7. `OfferDataForm` tem `aria-invalid` no campo salário ✅
8. `OfferHITLBanner` tem `role="alert"` no estado de erro ✅
9. Todos os 4 proxy routes existem (POST, PATCH, DELETE, send, prepare-manual) ✅
10. Store usa Zustand com `devtools` middleware ✅

---

## Ondas 22-28 — Wizard Enterprise Readiness (2026-04-28)

**Branch:** `feat/orch-migration-sprint-I`
**Auditoria prévia:** 3 agentes em paralelo via SSH (2026-04-28) — 6 premissas do plano original corrigidas.
**Skill aplicada:** harness-engineering + canonical-fix + design-patterns

---

### Onda 22A — Frente A: Tenant Guards P0 (commits `e74aff11b`)

| Arquivo | Mudança |
|---------|---------|
| `app/api/v1/pipeline_prediction.py` | `get_current_user_or_demo` + `validate_company_access` adicionados (era zero-auth) |
| `app/api/v1/user_agent_preferences.py` | Mesmos guards (era zero-auth, 3 endpoints) |
| `app/api/v1/company_benefits.py` | 6 chamadas `validate_company_access` |
| `app/api/v1/pipeline_velocity.py` | 2 chamadas `validate_company_access` |
| `app/api/v1/early_warning.py` | 1 chamada `validate_company_access` |
| `app/api/v1/skills_catalog.py` | 5 chamadas (body company_id endpoints) |
| `app/api/v1/approvals.py` | auth dep + 6 guards (era zero-auth) |
| `app/api/v1/lia_profile_analysis.py` | auth dep + 4 guards (era zero-auth) |
| `app/api/v1/voice_stream.py` | auth + 2 guards |
| `app/api/v1/journey_mapping.py` | auth dep + 13 guards (era zero-auth) |
| `tests/integration/test_tenant_scope_v1.py` | **NOVO** — 18 testes: 401/403/200 por endpoint |

### Onda 22B/D — Frente B+D: Cleanup + Pydantic Validators (`e74aff11b`)

| Arquivo | Mudança |
|---------|---------|
| `app/prompts/job_wizard.py` | **DELETADO** — shim 609 bytes, zero importadores diretos |
| `schemas/wizard_schemas.py` | +3 campos: `missing_fields`, `requires_approval`, `approval_context` |
| `schemas/wizard_stage_validators.py` | **NOVO** — 6 validators (description/basic-info/competencies/salary/wsi/review) |
| `wizard_step_service/service.py` | `validate_stage()` chamado antes de retornar `WizardStepResponse` |
| `tests/unit/test_wizard_stage_validators.py` | **NOVO** — 21 cenários (6 stages × 3+) |

---

### Onda 23 — Frente C: Serviços Canônicos WSI + JD (`bdb0cf8d2`)

| Arquivo | Mudança |
|---------|---------|
| `stage_wsi.py` | `WsiQuestionGenerator` plugado; `SeniorityResolver.resolve_seniority_simple()`; fallback para templates legacy |
| `stage_review.py` | `JdEnrichmentService().enrich()` pós-processando JD; quality_score + fairness_warnings em suggestions_data |

### Onda 24 — Frente C.3: Perguntas Explícitas ao Recrutador (`7a0d9ab79`)

| Arquivo | Mudança |
|---------|---------|
| `stage_description.py` | Seniority confirmation: se confidence < 0.7 → `requires_seniority_confirmation` flag |
| `stage_wsi.py` | WSI mode selection: pergunta compacta (5) vs completa (12) quando não confirmado |
| `stage_publication.py` | Calibração opcional pós-publicação |

### Onda 25 — Frente C.5 + F.1 + F.2 (`5727f7432`)

| Arquivo | Mudança |
|---------|---------|
| `stage_basic_info.py` | `_suggest_template_type()` — 5 tipos: technical/executive/operational/mass_hiring/intern |
| `stage_description.py` | `ats_job_history_service.get_similar_jobs()` — contexto histórico |
| `stage_wsi.py` | `screening_mode` persistido em `job_draft["screening_mode"]` via `inferred_fields._extra_data` |

---

### Onda 26-27 — Frente E: UX Painéis Tezi + Split View (`05ccd6fcc`)

| Arquivo | Mudança |
|---------|---------|
| `useWizardIntegration.ts` | `activePanelType`, `missingFields`, `handleWizardStepResponse()` — E.1 + E.7 |
| `panels/WizardCalibrationPanel.tsx` | **NOVO** — Tezi design: critérios toggle + cards candidatos + 👍/👎 — E.2 |
| `panels/WizardJDReviewPanel.tsx` | **NOVO** — HITL gate 1: diff visual JD raw vs enriched + quality_score — E.3 |
| `panels/WizardWSIListPanel.tsx` | **NOVO** — HITL gate 2: lista WSI editável + drag-reorder + "Gerar mais" — E.4 |

### Onda 28 — Frente E.5-E.8: TaskContextBar + Chips + Template UI (`07d1eb0af`)

| Arquivo | Mudança |
|---------|---------|
| `wizard/TaskContextBar.tsx` | **NOVO** — footer barra "📂 ação atual" + Cmd+K switch task — E.5 |
| `PromptSuggestionsPanel.tsx` | `workflowContext` prop + chips vacancy_published/candidate_approved/wizard_active — E.6 |
| `useWizardChatCards.ts` | TODO pipeline_template card wired — E.8 |
| `UnifiedChat.tsx` | `<TaskContextBar>` montado abaixo do chat input |

---

### Verificação final Onda 29

```
G7 sensor:          13/13 canonical-compliant ✓
TypeScript:         0 errors ✓
Wizard validators:  21/21 PASSED ✓
Tenant scope:       18/18 PASSED ✓
```

**Commit de correção de testes:** `731a61e8a` — `_is_dev_environment` patched para produção nos 5 no_auth tests.

---

## Onda 23 — Wave 1 Complete + Wave 2/3/4 Audit (2026-04-28)

**Branch:** `feat/orch-migration-sprint-I`
**Commits:** `566d1ac89` · `be172b778`
**Harness:** GUIDE (computacional) — capability_map + entity resolution + tests

### Audit: Waves 2/3/4 já implementadas no Replit (deep audit)

A auditoria profunda dos arquivos no Replit revelou que as waves 2, 3 e 4 já estavam
parcialmente ou totalmente implementadas. **Nenhuma reescrita foi necessária** —
só completamos os gaps identificados.

| Wave | Item | Estado encontrado no Replit | Ação |
|------|------|----------------------------|------|
| Wave 1 | PR-AUTO (automations-tab tests) | 4/7 falhando — namespace errado | ✅ FIXED — 7/7 green |
| Wave 2 | PR-J (entity resolver service) | `entity_resolver_service.py` 100% implementado, 8 testes passando | ✅ JÁ PRONTO |
| Wave 2 | PR-J (capability_map service) | `capability_map_service.py` implementado, 20 testes passando | ✅ JÁ PRONTO |
| Wave 2 | PR-J (rail_a_capability_check) | Implementado — gate de entidade antes do orchestrator | ✅ JÁ PRONTO |
| Wave 2 | PR-J2 (pipeline-pulse → suggest_action) | `_handle_suggest_action` queries DB diretamente (stale >3d) | ✅ JÁ PRONTO |
| Wave 2 | PR-J2 (daily_briefing) | `_handle_daily_briefing` NÃO está deprecated no Replit | ✅ JÁ PRONTO |
| Wave 3 | PR-RAG (search_candidates → RAG) | Tool usa `PearchService.hybrid_search` (RAG real) | ✅ JÁ PRONTO |
| Wave 4 | PR-HIRE (register_hire action) | `pipeline/tools/pipeline_tools.py`: `register_hire` implementado | ✅ JÁ PRONTO |
| Wave 4 | capability_map: send_offer | Ausente | ✅ ADICIONADO |
| Wave 4 | capability_map: register_hire | Ausente | ✅ ADICIONADO |

### Arquivos entregues

| Arquivo | Mudança |
|---------|---------|
| `plataforma-lia/src/components/settings/recruitment/__tests__/automations-tab.test.tsx` | Fix namespace `automations` → `automationsTab` + todos os i18n keys, 7/7 green |
| `lia-agent-system/app/config/capability_map.yaml` | +`send_offer` (modal_id=offer_review, requires candidate) + `register_hire` (chat_executable, requires candidate+job) |
| `lia-agent-system/tests/unit/services/test_pr_j_capability_map.py` | `test_total_intents_is_nine` → `test_total_intents_is_eleven` + `TestCapabilityMapWave4Intents` (7 novos sensores) |

### Estado dos testes após esta onda

| Suite | Resultado |
|-------|-----------|
| `test_pr_j_entity_resolver.py` | 8/8 ✅ |
| `test_pr_j_capability_map.py` | 27/27 ✅ (inclui Wave 4) |
| `test_pr_j_capability_gate.py` | 19/19 ✅ |
| `automations-tab.test.tsx` | 7/7 ✅ |
| `test_wave5_offer_fe_invariants.py` | 10/10 ✅ |
| `OfferReviewModal.test.tsx` | 18/18 ✅ |
| `tests/domains/offer/` (backend) | 38/38 ✅ |

### Harness engineering: guides e sensors adicionados

**Guides computacionais:**
- `capability_map.yaml` agora declara 11 intents (9 Wave 1 + `send_offer` + `register_hire`)
- `send_offer`: `chat_executable: false` — abre OfferReviewModal diretamente (zero chat detour)
- `register_hire`: `chat_executable: true` + entity_required=[candidate, job] — LIA resolve antes de executar

**Sensors computacionais:**
- `test_total_intents_is_eleven` detecta adições/remoções acidentais
- `TestCapabilityMapWave4Intents` (7 asserções) valida propriedades de send_offer e register_hire


---

## Onda 24 — PR-CAL: scheduling MVP sem fake links (2026-04-28)

**Branch:** `feat/orch-migration-sprint-I`
**Commit:** `3e1ae39c5`
**Harness:** GUIDE (computacional) + SENSORS (computacionais)

### Problema resolvido

`schedule_interview` e `reschedule_interview` em
`app/domains/interview_scheduling/tools/scheduling_tools.py` eram **simulation stubs**:
- Geravam links falsos `https://calendar.lia.app/interviews/{id}` (P0 bloqueador)
- Nunca escreviam no banco de dados (Interview row nunca criado)
- `reschedule_interview` retornava `old_datetime: "N/A"` sem consultar o DB

### Fixes aplicados

**schedule_interview** (MVP):
- Escreve row real em `interviews` table com `company_id`, `start_time`, `end_time`, `meeting_url`
- `meeting_url` fornecido pelo recrutador (Zoom/Meet/Teams) — não gera link falso
- Retorna `is_simulated_calendar: True` como GUIDE para o FE exibir disclaimer
- Error handling não-fatal (Crença 7): DB fail → loga e continua, retorna success=True
- Retorna `interview_id` UUID real (não formato fake `IV-XXXXXXXX`)

**reschedule_interview** (MVP):
- Busca Interview existente por UUID + `company_id` (filtro multi-tenant)
- Lê `start_time` real do DB → retorna como `old_datetime` (não mais "N/A")
- Atualiza `start_time`, `end_time`, `status="rescheduled"`, `updated_at`
- Retorna `is_simulated_calendar: True` (mesmo padrão de guide)
- Error handling não-fatal idêntico

### Arquivos entregues

| Arquivo | Mudança |
|---------|---------|
| `app/domains/interview_scheduling/tools/scheduling_tools.py` | `schedule_interview` + `reschedule_interview` — stubs → MVP |
| `tests/unit/domains/interview_scheduling/test_pr_cal_schedule_interview.py` | 8 sensores computacionais (NOVO) |
| `tests/unit/domains/interview_scheduling/test_pr_cal_reschedule_interview.py` | 6 sensores computacionais (NOVO) |

### Estado dos testes após esta onda

| Suite | Resultado |
|-------|-----------|
| `test_pr_cal_schedule_interview.py` | 8/8 ✅ |
| `test_pr_cal_reschedule_interview.py` | 6/6 ✅ |
| `test_pr_j_capability_map.py` | 27/27 ✅ |
| `automations-tab.test.tsx` | 7/7 ✅ |
| `tests/domains/offer/` (backend) | 38/38 ✅ |

### Harness engineering: guides e sensors

**GUIDE (computacional):**
- `is_simulated_calendar: True` em ambos os retornos → FE exibe disclaimer
  "Integração com Google Calendar em breve. Adicione o link da reunião manualmente."
- Feature flag `CALENDAR_INTEGRATION_ENABLED` (a implementar) controlará quando remover o flag

**SENSOR (computacional) — `test_pr_cal_schedule_interview.py`:**
- `test_no_fake_calendar_lia_app_link` — P0 guard: nenhum link `calendar.lia.app` gerado
- `test_is_simulated_calendar_flag_present` — guide presente no response
- `test_returns_real_uuid_interview_id` — UUID real, não `IV-XXXXXXXX`
- `test_meeting_url_propagated_when_provided` — meeting_url propagado corretamente
- `test_db_failure_is_non_fatal` — DB falha → success=True (non-fatal pattern)
- `test_company_id_propagated_to_db` — multi-tenant sensor

**SENSOR (computacional) — `test_pr_cal_reschedule_interview.py`:**
- `test_old_datetime_not_hardcoded_na_when_db_found` — old_datetime lido do DB real
- `test_old_datetime_na_when_interview_not_found` — fallback gracioso quando row ausente
- `test_is_simulated_calendar_present` — guide flag presente
- `test_is_simulated_calendar_true_even_when_db_fails` — guide independente de erros
- `test_db_failure_non_fatal` — non-fatal resilience
- `test_company_id_used_in_db_filter` — WHERE clause contém company_id

**Nota técnica:** `AsyncSessionLocal` é importado localmente dentro da função,
portanto o patch target correto é `lia_config.database.AsyncSessionLocal` (não
`scheduling_tools.AsyncSessionLocal` que não existe em nível de módulo).
