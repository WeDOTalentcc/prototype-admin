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

| Tag | Commit | O que marca |
|---|---|---|
| `milestone/teams-integration-complete` | `8656f5e9c` | Teams Wave 1-9 + docs handoff completos |
| `milestone/harness-orchestrator-v1` | `94a629c1d` | Orchestrator migration + canary kit entregues |
| `milestone/lia-maturity-track1` | `42d5dbb7b` | LIA Maturity Program Track 1 (FIX 1-28) completo |
| `milestone/rail-features-sprint1` | `710adfcef` | Rail features PR-A→PR-O Sprint 1 base |
| `teams/wave1-start` | `f7f972882` | Primeiro commit Teams (P0-1 multi-tenancy) |

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

**O que foi implementado:**
- FIX 1–28: grounded capability catalog, DomainActions, FairnessGuard, HITL, briefing, memory, proactive hints, cost tracker, persona consistency, error recovery
- Ondas 2.x–5.x: episodic memory, citation, workflow_context, history compaction
- Eval golden set + CI workflow

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
