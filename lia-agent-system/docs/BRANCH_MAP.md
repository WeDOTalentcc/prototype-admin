# Branch Map — lia-agent-system (Replit)

> Guia de navegação para o time. Atualizado: 2026-04-27.
> Branch de trabalho ativa: `feat/orch-migration-sprint-I`

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
