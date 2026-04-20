# MIGRATION-LOG — Canonical Tools Unification (ADR-016)

Rastreamento incremental da migração descrita em `/Users/paulomoraes/.claude/plans/floofy-doodling-widget.md`.

## Formato

Cada entrada = uma sessão executora. Números do `scripts/audit_tool_routing.py` servem de baseline medido.

---

## Sessão A — 2026-04-20 (Paulo + Claude)

**Escopo pretendido**: Nível 1 — fechar 12 ACTIONABLE_INTENTS órfãos.

**Achado central**: Nível 1 já estava implementado em sessão anterior. A auditoria confirmou que todos os 12 action_ids listados no plano têm handler real em `app/orchestrator/action_handlers/*.py`, cobertos por 23 testes verdes em `tests/unit/test_action_executor_unit.py`.

### Baseline medido (pós-auditoria)

Rodado: `python3 scripts/audit_tool_routing.py`

| CHECK | Plano estimou | Real medido | Status |
|---|---|---|---|
| 1 — ACTIONABLE_INTENTS coverage | 12 missing | **1 missing** (`respond_identity`) | ⚠️ WARN (respond_identity vive em `_simulate_execution`, aceitável) |
| 2 — No duplicate routing | — | **46 unique, 0 dupes** | ✅ PASS |
| 3 — V2 ToolDefinitions fora do registry | ~206 | **220** across 19 files | ⚠️ Target após Nível 3: 0 |
| 4 — V1 REST handler paths broken | 44 | **40/94** | ❌ FAIL — target após Nível 2: 0 |

### Distribuição CHECK 3 (para priorizar Nível 3)

```
 41  autonomous/agents/autonomous_tool_registry.py
 35  pipeline/agents/pipeline_tool_registry.py
 22  recruiter_assistant/agents/kanban_tool_registry.py
 18  sourcing/agents/sourcing_tool_registry.py
 15  recruiter_assistant/agents/jobs_mgmt_tool_registry.py
 13  recruiter_assistant/agents/talent_tool_registry.py
 13  hiring_policy/agents/policy_tool_registry.py
 12  job_management/agents/wizard_tool_registry.py
  7  company_settings/agents/company_tool_registry.py
  6  analytics/agents/analytics_tool_registry.py
  6  automation/agents/automation_tool_registry.py
  5  sourcing/agents/nurture_sequence_tool_registry.py
  5  communication/agents/communication_tool_registry.py
  5  ats_integration/agents/ats_integration_tool_registry.py
  4  sourcing/agents/github_tool_registry.py
  4  sourcing/agents/referral_tool_registry.py
  3  sourcing/agents/diversity_tool_registry.py
  3  sourcing/agents/passive_pipeline_tool_registry.py
  3  sourcing/agents/stackoverflow_tool_registry.py
```

### Distribuição CHECK 4 (V1 REST handlers quebrados)

40 handlers broken em 5 domains:
- `interview_scheduling/tools/__init__.py` — 10 broken (scheduling_service + voice_service paths)
- `ats_integration/tools/__init__.py` — 10 broken (ats_sync_service paths)
- `automation/tools/__init__.py` — ~10 broken (task_service + automation_service)
- `communication/tools/__init__.py`, `cv_screening/tools/__init__.py` — resto

Pattern comum: paths tipo `app.domains.X.services.Y.Y_service.method` (service instance duplicada no path). V1 legacy que deve ser **deletado** no Nível 2 em vez de consertado.

### Entregas desta sessão

1. ✅ `scripts/audit_tool_routing.py` criado (4 checks). Executável, retorna exit 0 em PASS e 1 em FAIL.
2. ✅ Baseline numérico validado e documentado aqui.
3. ✅ Nível 1 confirmado **completo** (sem código novo necessário).
4. ✅ Spawn task criada: "Fix map_intent_to_actionable regression" (42 testes quebrados, regressão não relacionada).

### NÃO commitado nesta sessão (Paulo commita manualmente via Replit IDE)

- `scripts/audit_tool_routing.py` (7428 bytes, novo)
- `docs/architecture/MIGRATION-LOG-TOOLS-UNIFIED.md` (este arquivo)

### Handoff para Sessão B

**Escopo**: Nível 2, metade 1 — deletar V1 REST layer em 4 domains menores.

**Ordem recomendada** (do menos acoplado pro mais):
1. `interview_scheduling` (10 handlers broken, já tem ToolDefs V2 em `agents/*.py`)
2. `ats_integration` (10 broken, isolado — pouco consumer externo)
3. `automation` (~6 broken, touch no task_service)
4. `communication` (5 broken, touch em email/whatsapp providers — mais cuidado)

**Comando inicial da Sessão B**:
```
Ler plano em /Users/paulomoraes/.claude/plans/floofy-doodling-widget.md (Nível 2)
e MIGRATION-LOG em docs/architecture/MIGRATION-LOG-TOOLS-UNIFIED.md (Sessão A).
Branch: feat/tools-migration-level-2-delete-v1-rest

Executar Nível 2 — metade 1: interview_scheduling, ats_integration, automation, communication.
Para cada domain:
  1. Migrar tools do `{DOMAIN}_TOOLS` dict pra registro canônico via
     `tool_registry.register(ToolDefinition(...))` em `register_<dom>_rest_tools()`.
  2. Adicionar chamada em `app/tools/__init__.py::initialize_tools()`.
  3. Redirecionar `action_executor._execute_action` → `tool_executor.execute()` quando aplicável.
  4. Deletar `app/domains/<dom>/tools/__init__.py` (dict V1).
  5. Rodar `python3 scripts/audit_tool_routing.py` — CHECK 4 deve cair.
  6. Rodar `pytest tests/unit/test_action_executor_unit.py` — 23/23 verde.
  7. Commit atômico por domain (CLAUDE.md + production-quality + canonical).

Objetivo: CHECK 4 vai de 40 → ~10-15 nesta sessão. Nível 2 metade 2 na Sessão C.
```

### Gaps no plano original (corrigir antes de Sessão B)

- Plano assumia `scripts/audit_tool_routing.py` existia — não existia, agora foi criado.
- Plano estimava 12 orphan intents — real é 1 (não-bloqueante).
- Plano estimava CHECK 4 = 44 broken — real é 40 (marginal).
- Plano não mencionava regressão `map_intent_to_actionable` — task separada spawnada.

---

## Sessão B — [pendente]

(A ser preenchido quando executada.)

---

## Handoff Atualizado — Sequência Aprovada 2026-04-20

Paulo aprovou execução em ordem **C → A → B** com CLAUDE.md aplicado em cada commit:

### Sessão B (próxima) — Escopo: 3 tarefas P0/P1 em sequência

#### 📋 Tarefa C — `map_intent_to_actionable` regression (P1, ~1-2h)
**Objetivo**: destravar 42 testes verdes em `tests/unit/test_intent_to_actionable.py`
**Raiz**: `map_intent_to_actionable` foi removido de `app/api/v1/chat.py` em refactor anterior sem migrar os testes.
**Plano**:
1. `git log --all --oneline -p -- app/api/v1/chat.py | grep -B2 -A5 "map_intent_to_actionable"` — achar implementação antiga
2. Se lógica migrou para `app/orchestrator/action_executor/` → atualizar imports nos testes (preferência: estabilidade de testes)
3. Se lógica foi apagada → re-exportar função wrapper em `app/api/v1/chat.py` apontando pro novo local
4. `pytest tests/unit/test_intent_to_actionable.py -q` → 42+ passed
5. Commit atômico (CLAUDE.md: boy scout P2 fixes no mesmo arquivo)

#### 🔴 Tarefa A — Admin Tenant Gap (P0, ~4h)
**Objetivo**: ao criar cliente via Admin, criar também `account` no Rails para multi-tenancy funcionar
**Raiz**: fluxo atual cria em FastAPI/WorkOS/HubSpot mas não propaga pro Rails → login do cliente quebra
**Plano**:
1. Localizar serviço que cria cliente (provavelmente `app/domains/admin/services/client_creation_service.py` ou similar)
2. Identificar endpoint Rails para criar account (`POST /api/v1/accounts` no ats-api-copia)
3. Adicionar chamada `RailsClient.create_account(company_id, workos_org_id, name, ...)` no fluxo de criação
4. Tratamento de erro: se Rails falhar, rollback FastAPI+WorkOS+HubSpot (idempotência via outbox pattern recomendada)
5. Teste E2E: criar cliente → login com usuário do novo client → acessar dashboard
6. **CLAUDE.md enforcement**:
   - Multi-tenancy: `company_id` do JWT, nunca do payload
   - LGPD: sem dados sensíveis em logs
   - Sem secrets hardcoded (usar env vars `RAILS_API_URL` + `RAILS_API_KEY`)

#### 🟡 Tarefa B — Tool Migration Nível 2 metade 1 (P0, ~1 sessão)
**Objetivo**: CHECK 4 de `audit_tool_routing.py` cai de 40 → ~10-15
**Escopo**: 4 domains menos acoplados: interview_scheduling, ats_integration, automation, communication
**Plano**: ver seção "Sessão B" acima (já detalhada)
**Gate**: depois de cada domain rodar `python3 scripts/audit_tool_routing.py` + `pytest tests/unit/test_action_executor_unit.py` (23/23 green)

### CLAUDE.md não-negociáveis aplicados em TODOS os commits

1. **Multi-tenancy**: `company_id` sempre do JWT, nunca do payload
2. **LGPD**: zero dados sensíveis em logs/prompts (raça, religião, gênero, etnia, estado civil, saúde)
3. **Fairness**: rankings/scorings com instrução explícita de fairness
4. **No hardcoded secrets**: env vars via `os.environ`
5. **Design tokens**: zero cores/spacings hardcoded em frontend
6. **Boy Scout**: P2s do arquivo no mesmo commit
7. **Output review format**: P0 🔴 / P1 🟡 / P2 🟢

### Skills a rodar após cada tarefa (conforme CLAUDE.md)

```bash
python3 scripts/audit_tool_routing.py          # CI gate canônico
python3 scripts/check_no_pii_in_logs.py        # LGPD
python3 scripts/check_no_sql_in_controllers.py # ADR-001
python3 scripts/validate_stubs.py
pytest tests/unit/test_action_executor_unit.py # Regression gate (23 testes)
```

### Branches propostas (1 por tarefa, rollback independente)

```
fix/map-intent-to-actionable-regression        (tarefa C, ~1 commit)
feat/admin-tenant-rails-account-sync           (tarefa A, ~2-3 commits)
feat/tools-migration-level-2-delete-v1-rest    (tarefa B, ~4 commits, 1 por domain)
```

### Prompt inicial da Sessão B

```
Ler MIGRATION-LOG em docs/architecture/MIGRATION-LOG-TOOLS-UNIFIED.md
(seção "Handoff Atualizado — Sequência Aprovada 2026-04-20").

Executar C → A → B nesta ordem, aplicando CLAUDE.md em cada commit:
  C) Fix map_intent_to_actionable regression (~1-2h)
  A) Admin Tenant Gap — Rails account sync (~4h)
  B) Tool Migration Nível 2 metade 1 (4 domains)

SSH: ssh -i ~/.ssh/replit -p 22 82791557-0b63-4f8d-baed-bba54c6e1fdf@82791557-0b63-4f8d-baed-bba54c6e1fdf-00-32kinhguzv9ak.picard.replit.dev
Código: ~/workspace/lia-agent-system/
Paulo commita manualmente via Replit IDE (nunca git push direto).

Após cada tarefa: rodar skills do CLAUDE.md (audit_tool_routing + check_no_pii_in_logs + validate_stubs + pytest).
Reportar progresso em MIGRATION-LOG-TOOLS-UNIFIED.md no final de cada tarefa.
```
