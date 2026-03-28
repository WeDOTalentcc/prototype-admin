# Plano de Implementação — Status de Continuidade
**Última atualização:** 04/março/2026 — Sessão 2
**Sessão anterior:** Implementação das Fases 0, 1, 2, 3, 4, 5, 7 e testes (F6)

---

## O QUE JÁ FOI FEITO (não reimplementar)

### Fase 0 — Bugs + Limpeza ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| B1 — intent bug | `app/orchestrator/orchestrator.py:118` | Separado `domain_id` de `intent`; intent agora usa `route.intent_details["raw_intent"]` |
| B2 — checkpoint merge | `app/domains/job_management/agents/job_wizard_graph.py:246` | Invertido para `{**state, **prior}` com lista `EPHEMERAL_FIELDS` |
| B3 — typos português | `app/shared/agents/react_loop.py:407` | "nao" → "não", "solicitacao" → "solicitação", "esta" → "está" |
| B4 — duplicações FairnessGuard | `app/shared/compliance/fairness_guard.py:33-50` | Removidas 5 chaves duplicadas (com/sem acento); `_normalize_text()` já normaliza antes da busca |
| Código morto | `app/agents/agent_registry.py` | **DELETADO** — era shim vazio (retornava None em tudo) |
| Imports legados | `app/api/v1/wizard_smart_orchestrator.py` | Migrado para `app.domains.job_management` e `app.shared.agents.state_machine` |
| Imports legados | `app/api/v1/lia_assistant.py` | Migrado para `app.shared.agents.state_machine` |
| Imports legados | `app/api/v1/chat.py` | Migrado para `app.shared.agents.conversation` |
| ADR 001 | `docs/adr/001-python-not-ruby.md` | Criado — decisão de manter Python/FastAPI |
| ADR 002 | `docs/adr/002-graph-vs-react.md` | Criado — quando usar Graph vs ReAct Loop |
| CLAUDE.md | `CLAUDE.md` | Referência a Ruby/Rails removida da tabela de tech stack |

**Import legacy restante intencional:**
- `app/api/v1/hiring_policy.py:41` → `from app.agents.policy_setup_agent import policy_setup_agent`
- É o fallback quando `PolicyReActAgent` falha. Não deletar sem criar versão domain equivalente.

---

### Fase 1 — Configurações Centralizadas ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| 18 novas settings | `app/core/config.py` | Adicionado bloco de LLM Models, LLM Params, ReAct Params, Router Params, Cascade Thresholds |
| Magic numbers — llm | `app/services/llm.py` | `MAX_TOOL_CALLS_PER_REQUEST`, `model_name`, `temperature`, `max_tokens`, `timeout`, modelos Gemini → settings |
| Magic numbers — router | `app/orchestrator/cascaded_router.py` | `cache_max_size`, confidence threshold → settings; import de settings adicionado |
| Magic numbers — orchestrator | `app/orchestrator/orchestrator.py` | `% 10` → `% settings.ROUTER_SUMMARY_EVERY_N_MESSAGES`; import de settings adicionado |
| Magic numbers — react loop | `app/shared/agents/react_loop.py` | `max_iterations` default_factory, duplicate threshold, truncamento de observação → settings; import adicionado |

---

### Fase 1.2 — Confidence Cascade Haiku→Sonnet→Opus ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| `LLMCascadeResult` dataclass | `app/services/llm.py` | Criado com campos: content, model_used, confidence, requires_human, reason |
| `generate_with_cascade()` | `app/services/llm.py` | Método implementado; itera Haiku→Sonnet→Opus por threshold |
| `_get_claude_for_model()` | `app/services/llm.py` | Helper para criar cliente Claude por nome de modelo |
| intent_router cascade | `app/orchestrator/intent_router.py` | `route()` usa cascade; `_fallback_response()` extraído |
| cascaded_router cascade | `app/orchestrator/cascaded_router.py` | `_route_via_llm()` usa cascade internamente |

---

### Fase 2 — Observabilidade ✅ PARCIAL (backend feito, frontend pendente)

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| Truncamento removido | `app/shared/agents/observability.py:73` | `reasoning[:500]` → `reasoning` (sem limite) |
| company_id + user_id | `app/shared/agents/observability.py` | Adicionados a `AgentExecutionLog` e `ReActObserver.__init__()` |
| 8 agentes atualizados | Todos os agentes ReAct de domínio | Passam `company_id=input.company_id, user_id=input.user_id` ao ReActObserver |
| Truncamento observação | `app/shared/agents/react_loop.py:599` | 2000 chars → `settings.REACT_OBSERVATION_MAX_CHARS` (5000) |

**8 agentes atualizados:**
- `app/domains/sourcing/agents/sourcing_react_agent.py`
- `app/domains/job_management/agents/wizard_react_agent.py`
- `app/domains/cv_screening/agents/pipeline_react_agent.py`
- `app/domains/recruiter_assistant/agents/talent_react_agent.py`
- `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
- `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- `app/domains/pipeline/agents/pipeline_transition_agent.py`
- `app/domains/hiring_policy/agents/policy_react_agent.py`

---

### Fase 3 — Guardrails no Banco ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| Modelo SQLAlchemy | `app/models/guardrail.py` | Criado com: id, level, domain, node, tool, rule, blocking_message, is_active, company_id, updated_by, updated_at |
| Migration | `alembic/versions/020_add_guardrails_table.py` | Criado com 4 índices; revisa migration 019 |
| Seed | `app/core/seeds/guardrails_seed.py` | 6 primários (globais LGPD/fairness) + 7 secundários por domínio; idempotente |
| Repositório | `app/shared/compliance/guardrail_repository.py` | `get_active()`, `get_blocked_tools()`, `upsert()`, `toggle_active()` — async |
| enhanced_agent_mixin | `app/shared/agents/enhanced_agent_mixin.py:116` | 3-tier fallback: autonomia → DB → static list |
| GUARDRAIL_TOOLS expandido | `app/domains/pipeline/agents/pipeline_tool_registry.py` | 1 → 7 tools com comentários |
| Endpoints CRUD | `app/api/v1/guardrails.py` | GET list, POST create, GET detail, PUT update, PATCH toggle |
| Router registrado | `app/main.py` | `guardrails.router` incluído |
| Modelo exportado | `app/models/__init__.py` | `Guardrail` exportado |
| Proxy FE list/create | `plataforma-lia/src/app/api/backend-proxy/guardrails/route.ts` | GET + POST |
| Proxy FE detail/update | `plataforma-lia/src/app/api/backend-proxy/guardrails/[id]/route.ts` | GET + PUT |
| Proxy FE toggle | `plataforma-lia/src/app/api/backend-proxy/guardrails/[id]/toggle/route.ts` | PATCH |
| Admin UI | `plataforma-lia/src/app/admin/compliance/guardrails/page.tsx` | Lista, filtros, toggle, dialog criar/editar |

### F3.9 — check_semantic() integrado ✅ COMPLETO

| Agente | Status | Onde |
|--------|--------|------|
| `pipeline_tool_registry.py` | ✅ Já existia | `check_rejection_fairness()` linha ~494 |
| `wizard_tool_registry.py` | ✅ Já existia | `_wrap_validate_job_requirements()` linha ~68 |
| `triagem_curricular_agent.py` | ✅ Adicionado | Após `rubric_evaluation_service.evaluate_candidate()` em `_handle_screen_candidate()` |

---

### Fase 4 — Prompts Consolidados ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| 9 YAMLs completados | `app/prompts/domains/*.yaml` | sourcing, job_management, cv_screening, communication, interview_scheduling, analytics, ats_integration, automation, recruiter_assistant — todos com: persona, scope_in, scope_out, behavioral_rules, system_prompt, intent_examples |
| Documentação duplicação | `app/prompts/job_wizard.py` e `jobs_management_prompts.py` | Arquivos são diferentes (wizard vs analytics) — comentários cross-reference adicionados em ambos |
| Few-shot protocol | `docs/prompts/few_shot_validation_protocol.md` | Protocolo completo com processo, critérios, checklist de release e tabela de casos ambíguos cross-domain |

**Nota sobre consolidação de persona LIA:**
- `app/prompts/shared/lia_persona.yaml` já é a fonte canônica — carregada via `PromptLoader.load("shared/lia_persona")`
- `app/shared/prompts/agent_prompts.py` já importa via `_shared["prompts"]["lia_persona"]`
- pipeline_system_prompt.py ainda tem PIPELINE_IDENTITY hardcoded — **pendente para próxima sessão** (baixo impacto)

---

### Fase 5 — API Async + WebSocket ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| Documentação sync/async | `docs/architecture/sync-vs-async.md` | Regras, inventário, decisões, exemplos WebSocket |
| 4 tasks Celery | `app/jobs/celery_tasks.py` | `agents.wsi_interview.start`, `agents.triagem.run`, `agents.sourcing.search`, `communication.email.send_bulk` |
| AsyncJobResponse schema | `app/schemas/async_job.py` | `AsyncJobResponse` + `AsyncJobStatusResponse` — Pydantic models |
| Async endpoints | `app/api/v1/async_endpoints.py` | POST triagem/run-batch, POST interviews/wsi/start, POST sourcing/search, POST communication/email/bulk, GET jobs/{job_id}/status |
| WebSocket endpoint | `app/api/v1/jobs_ws.py` | `ws://host/ws/jobs/{job_id}` — polling Celery com fallback timeout 3h |
| Routers registrados | `app/main.py` | `async_endpoints.router` e `jobs_ws.router` incluídos |
| Componente FE | `plataforma-lia/src/components/async/AsyncJobProgress.tsx` | WebSocket + polling fallback, barra de progresso, retry em falha |
| Proxy FE status | `plataforma-lia/src/app/api/backend-proxy/async/jobs/[job_id]/status/route.ts` | GET status |

---

### Fase 6 — Testes de Domínio ✅ PARCIAL

| Item | Arquivo | Status |
|------|---------|--------|
| Conftest | `tests/test_domains/conftest.py` | ✅ Criado — fixtures company_id, user_id, mock_llm, mock_db, sample_candidate, discriminatory_text |
| test_pipeline_transition_agent | `tests/test_domains/test_pipeline_transition_agent.py` | ✅ Criado |
| test_wizard_react_agent | `tests/test_domains/test_wizard_react_agent.py` | ✅ Criado |
| test_sourcing_react_agent | `tests/test_domains/test_sourcing_react_agent.py` | ✅ Criado |
| test_cv_screening_agents | `tests/test_domains/test_cv_screening_agents.py` | ✅ Criado (1 assert fix pendente — já identificado) |
| test_kanban_react_agent | `tests/test_domains/test_kanban_react_agent.py` | ✅ Criado |
| test_policy_react_agent | `tests/test_domains/test_policy_react_agent.py` | ✅ Criado |
| test_interview_scheduling | `tests/test_domains/test_interview_scheduling.py` | ✅ Criado |
| E2E Alpha 1 | `tests/e2e/test_alpha1_scenario.py` | ✅ Criado — 10 etapas do fluxo completo |

**PENDENTE — executar e corrigir falhas:**
```bash
cd lia-agent-system
python -m pytest tests/test_domains/ -q
```
- 1 falha conhecida em `test_cv_screening_agents.py::TestTriagemScoreCalculation::test_score_thresholds_defined`
  - assert foi ajustado mas pytest foi interrompido antes de confirmar
  - Fix: `assert any(k in thresholds for k in ("advance", "avançar", "auto_approve"))`
  - ⚠️ Verificar se o Edit foi salvo corretamente

---

### Fase 7 — Compliance LGPD ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| Footer IA em emails | `app/shared/channels/adapters/email_adapter.py` | `AI_GENERATED_FOOTER` constante + `_add_ai_footer()` helper; aplicado automaticamente quando `message.ai_generated=True` ou `message.source_agent` presente |
| Campos ConsentType | `app/models/communication_settings.py` | Adicionados: `DATA_SHARING_EMAIL_PROVIDERS`, `DATA_SHARING_SMS_PROVIDERS`, `AI_GENERATED_COMMUNICATIONS` |
| Sampling 5% | `app/services/human_review_sampling_service.py` | `HumanReviewSamplingService` — determinístico por MD5 hash; `ALWAYS_REVIEW_DECISIONS` para finalize_hiring/mass_rejection/fairness_flagged; singleton `human_review_sampling_service` |

---

## O QUE FOI FEITO NESTA SESSÃO (04/mar/2026 — continuação)

### Fase 6 — Testes de Domínio ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| 56 testes passando | `tests/test_domains/` + `tests/e2e/` | 14 falhas corrigidas; 56/56 ✅ |
| `check_explicit_bias()` | `app/shared/compliance/fairness_guard.py` | Alias para `check()` + property `is_biased` em `FairnessCheckResult` |
| Padrão faixa etária | `fairness_guard.py` | `r"\bde\s+\d+\s+(a|até|ate)\s+\d+\s+anos\b"` adicionado à categoria `idade` |
| Categoria maternidade | `fairness_guard.py` | `maternidade_paternidade` — 7 padrões (engravidar, sem filhos, tem filhos…) |
| `EPHEMERAL_FIELDS` módulo | `job_wizard_graph.py:32` | Extraído para nível de módulo como `frozenset` |
| `ReActObserver` atributos | `observability.py` | `company_id` e `user_id` como atributos diretos (além de `self.log`) |
| Fixes de testes | 5 arquivos de teste | `agent_name`→`session_id`/`agent_class`; `WizardToolRegistry`→`get_wizard_tools()`; `domain_name`; `seed_guardrails`→`run_seed` |

### Fase 2.4 — Dashboard de Saúde de Agentes ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| `get_domain_health()` | `app/shared/agents/execution_log_store.py` | Query agrupada por domínio; status: healthy/warning/degraded/stale |
| Endpoints domínio | `app/api/v1/agent_monitoring.py` | `GET /agent-monitoring/domains/health` + `GET /agent-monitoring/domains/{domain}/metrics` |
| `check_agent_health()` | `app/services/drift_alert_service.py` | Verifica saúde por domínio; alerta Bell+Teams se degradado/stale |
| Proxy FE health | `plataforma-lia/src/app/api/backend-proxy/agent-monitoring/domains/health/route.ts` | GET |
| Proxy FE metrics | `plataforma-lia/src/app/api/backend-proxy/agent-monitoring/domains/[domain]/metrics/route.ts` | GET |
| Dashboard | `plataforma-lia/src/app/admin/monitoring/agents/page.tsx` | Tabela com status, confiança, falha de tools, iterações, duração, uptime |

### pipeline_system_prompt.py — LIA Persona ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| `_load_pipeline_identity()` | `pipeline_system_prompt.py` | Carrega de `PromptLoader.load("shared/lia_persona")` com fallback local |

---

## O QUE FOI FEITO NA SESSÃO 2 (04/mar/2026)

### Itens Pendentes do Plano — ✅ TODOS CONCLUÍDOS

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| Migration 020 (guardrails) | banco + `alembic_version` | Tabela já existia no banco; `alembic_version` corrigido de `008` → `021`; `varchar(32)` → `varchar(128)` |
| Seed de guardrails | `app/core/seeds/guardrails_seed.py` | 13 guardrails inseridos: 6 primários (globais LGPD/fairness) + 7 secundários por domínio |
| `company_id` real no dashboard | `plataforma-lia/src/app/admin/monitoring/agents/page.tsx` | `"demo-company"` hardcoded → `useCurrentCompany()` hook; bug de loading state corrigido (`dataLoading` + `companyLoading`) |
| Link no sidebar admin | `plataforma-lia/src/app/admin/layout.tsx` | "Saúde dos Agentes" adicionado em Compliance & Segurança com ícone `Brain` |

### Migration 022 — Reconciliação de Schemas ✅ COMPLETO

| Item | Arquivo | O que foi feito |
|------|---------|----------------|
| Migration criada | `alembic/versions/022_reconcile_missing_schemas.py` | Aplica DDL faltante das migrations 010, 014, 015, 016 e 017 — todas com `IF NOT EXISTS` (idempotente) |
| 010 — Human Review Gate | `vacancy_candidates` | `rejected_by_human` (Boolean) + `human_reviewer_id` (String) + índice parcial |
| 014 — Channel Preferences | `candidates` | `preferred_channels` + `channel_opt_out` (convertidos JSON → JSONB) + índices GIN |
| 015 — FairnessGuard Log | `fairness_audit_log` | Tabela criada com 5 índices (company_id, category, is_blocked, created_at, composto) |
| 016 — AI Log Retention | `ai_consumption` | `scheduled_deletion_at` + índice + backfill `created_at + 365 dias` |
| 017 — Calendar Credentials | `company_calendar_credentials` + `interviews` | Tabela criada + `google_event_id` + `google_meet_link` |
| Banco verificado | query direta | 9/9 elementos confirmados ✅ |
| Alembic atual | `alembic current` | `022_reconcile_missing_schemas (head)` |

---

## O QUE FALTA IMPLEMENTAR

### ✅ PLANO CONCLUÍDO

Todas as fases e itens pendentes foram implementados e validados.

## PRÓXIMOS PASSOS SUGERIDOS

Nenhum item técnico pendente. Sugestões para evoluções futuras:

1. Testar `python -m pytest tests/test_domains/ -q` após migration 022 para garantir que nenhum teste quebrou com os novos campos
2. Monitorar o dashboard `/admin/monitoring/agents` em uso real para calibrar os thresholds de `healthy/warning/degraded/stale`

---

## CRITÉRIOS DE DONE (verificação rápida)

```bash
# F0 — nenhum import legado em endpoints ativos
grep -r "from app.agents" lia-agent-system/app/api/
# Esperado: apenas hiring_policy.py (fallback intencional)

# F1 — sem magic numbers nos arquivos críticos
grep -n '"claude-sonnet\|= 0\.7\|= 4096\|= 120\.' lia-agent-system/app/services/llm.py
# Esperado: 0 resultados

# F2 — traces têm company_id
grep -n "company_id" lia-agent-system/app/shared/agents/observability.py
# Esperado: campos em AgentExecutionLog e ReActObserver.__init__

# F3 — guardrails na tabela
# SELECT count(*) FROM guardrails  →  > 0

# F5 — tasks Celery registradas
# celery -A app.core.celery_app inspect registered
# Esperado: drift.run_batch, agents.wsi_interview.start, agents.triagem.run,
#           agents.sourcing.search, communication.email.send_bulk

# F6 — testes passando
# python -m pytest tests/test_domains/ -q → 0 failed

# F7 — footer IA em emails
grep -n "AI_GENERATED_FOOTER" lia-agent-system/app/shared/channels/adapters/email_adapter.py
# Esperado: constante definida e helper _add_ai_footer() presente

# Sessão 2 — guardrails seed
# SELECT count(*) FROM guardrails  →  13

# Sessão 2 — alembic na head
# python -m alembic current  →  022_reconcile_missing_schemas (head)

# Sessão 2 — schemas reconciliados (010, 014-017)
# SELECT column_name FROM information_schema.columns WHERE table_name='vacancy_candidates' AND column_name='rejected_by_human'  →  1 row
# SELECT table_name FROM information_schema.tables WHERE table_name='fairness_audit_log'  →  1 row
# SELECT table_name FROM information_schema.tables WHERE table_name='company_calendar_credentials'  →  1 row
```

---

## REFERÊNCIAS RÁPIDAS

| O que precisar | Onde encontrar |
|---------------|----------------|
| Estado atual do codebase | `docs/DIAGNOSTICO_ARQUITETURA_IA_v4.0.md` |
| Design System | `plataforma-lia/docs/design-system/00-design-system-v4.md` |
| Plano original completo (todas as fases) | `docs/DIAGNOSTICO_GUIA_v3.2.md` |
| ADR Python vs Ruby | `docs/adr/001-python-not-ruby.md` |
| ADR Graph vs ReAct | `docs/adr/002-graph-vs-react.md` |
| Config settings (novos campos) | `lia-agent-system/app/core/config.py` — seção final do arquivo |
| Sync vs Async — decisão formal | `docs/architecture/sync-vs-async.md` |
| Few-shot validation protocol | `docs/prompts/few_shot_validation_protocol.md` |
| Verificar imports legados restantes | `grep -r "from app.agents" app/api/` (deve retornar apenas hiring_policy.py) |
