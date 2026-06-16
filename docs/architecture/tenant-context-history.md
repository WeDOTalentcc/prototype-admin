# Tenant Context History — Tasks T-A → T-F

> **Origem:** este arquivo extrai do `replit.md` o histórico denso das tasks **T-A**, **T-B (#970)**, **T-C (#969)**, **T-D (#971)**, **T-E (#972)** e **T-F** que endereçaram o bug recorrente *"LIA pergunta `company_id` no chat"*. O `replit.md` mantém apenas o resumo executivo de uma linha por task — o detalhamento técnico vive aqui.
>
> **Quando atualizar:** sempre que houver alteração em `TenantAwareAgentMixin`, `TenantContextService`, `CompanyId`, migration de `companies`, helper `resolve_tenant_snippet_for_non_react`, golden dataset `eval/golden/tenant_context.jsonl` ou nos sentinelas em `tests/integration/agents/test_tenant_*`.
>
> **Documentos relacionados:**
> - Runbook on-call: [`docs/runbooks/missing_tenant_context.md`](../runbooks/missing_tenant_context.md)
> - Arquitetura geral: [`docs/architecture/ARCHITECTURE.md`](./ARCHITECTURE.md)
> - Catálogo de agentes/tools: [`docs/architecture/LIA_TOOLS_CATALOG.md`](./LIA_TOOLS_CATALOG.md)

---

## T-A — Fundação: `CompanyId` value object + canary monitoring

Estabelece o **value object canônico `CompanyId`** (`app/shared/value_objects/company_id.py`) com `CompanyId.parse()` aceitando UUID v4 OU slug `^[a-z][a-z0-9_-]{2,63}$` e bloqueando os literais reservados `default | none | null | undefined | system | anonymous`.

Introduz o helper `is_tenant_strict_mode()` que retorna `True` em `production`/`staging` por padrão e respeita o override `LIA_AGENT_TENANT_STRICT={true|false}`.

Canary monitoring entra em produção via:
- Endpoint `/api/v1/health/compliance/bypass-status` expondo `tenant_aware_agent.{strict_mode, metrics}`.
- Counter Prometheus `lia_agent_tenant_context_resolved_total{agent,outcome=hit|miss|fail_open|fail_closed}`.
- `app/main.py` lifespan loga **CRITICAL** + `sentry_sdk.capture_message(level=error)` quando `LIA_AGENT_TENANT_STRICT=false` em prod/staging (agregado com as 4 flags de bypass R-007). Sentry event key estável: `LIA_AGENT_TENANT_STRICT_BYPASS` (fingerprint + tag).

---

## T-B (Task #970, MERGED) — Wizard como piloto

`WizardReActAgent` herda de `TenantAwareAgentMixin` (MRO: `mixin → LangGraphReActBase → EnhancedAgentMixin`) com `tenant_strict_override = True` — wizard **NUNCA** degrada para `"sua empresa"/"geral"` mesmo se `LIA_AGENT_TENANT_STRICT=false` em dev.

`_get_runtime_domain_instructions` chama `self._compose_runtime_prompt(...)` (helper canônico do mixin que auto-injeta `tenant_context_snippet` lido de `input.context`) em vez de `PromptComposer.for_domain_runtime` direto — fechando o gap onde o snippet propagado por SSE/WS handlers se perdia no runtime prompt.

`WizardSessionService._build_state` valida `company_id` via `CompanyId.parse`:
- **strict-mode:** levanta `InvalidCompanyIdError` para entradas inválidas (`""`, `"default"`, `"none"`).
- **legacy-mode:** degrada com warning para `workspace_id=0`/`company_id=""`.

Substitui o hotfix `fix-wizard-company-context.md` (origem do bug "LIA pergunta company_id no chat do wizard"). Testes: `tests/integration/wizard/test_wizard_tenant_context_e2e.py`.

---

## T-C (Task #969) — Multi-tenant Companies Schema

A tabela `companies` é a **raiz multi-tenant**. Schema enriquecido pela migration `127_enrich_companies_schema` com `sector`, `industry_segment`, `plan`, `timezone`, `headcount_range` e `lia_persona_override` — esses campos alimentam `TenantContextService.get_context()` e o prompt da LIA.

**Demo Company canônica** é a UUID `00000000-0000-4000-a000-000000000001` (slug `demo_company` foi removido como duplicidade); seed idempotente em `scripts/seeds/demo_company.py` (UPSERT com `sector=Tecnologia`, `plan=enterprise`, `timezone=America/Sao_Paulo`, persona WeDo Talent). `app.core.database.ensure_default_company` delega ao seed canônico (não faz mais DDL inline nem cria slug).

O modelo SQLAlchemy `lia_models.company.Company` é a única forma autorizada de ler a tabela — antes não existia, fazendo `TenantContextService` cair silenciosamente em `"sua empresa"/"geral"`.

CHECK constraint `ck_companies_id_format_canonical` espelha `CompanyId.parse()` (T-A): aceita UUID v4 OU slug `^[a-z][a-z0-9_-]{2,63}$`, e bloqueia os literais reservados — DB e value object **falham pelo mesmo motivo**.

Re-runner idempotente: `python -m scripts.migrate_demo_company_consolidation` (exit 0 sucesso, 1 conflito FK, 2 falha técnica). Rollback: `scripts/rollback_demo_company_consolidation.sql`.

---

## T-D (Task #971, MERGED) — Roll-out para os 16 ReActAgents

Após o piloto T-B (wizard), os outros 15 ReActAgents foram migrados para herdar `TenantAwareAgentMixin` (MRO: `mixin → LangGraphReActBase → EnhancedAgentMixin`):

`analytics`, `ats_integration`, `automation`, `autonomous`, `candidate_self_service`, `communication`, `company_settings`, `cv_screening` (pipeline), `hiring_policy` (policy), `jobs_mgmt`, `kanban`, `talent_funnel`, `sourcing`, `talent_pool`, `pipeline_transition`.

**Total canônico:** **16 agentes** (wizard incluso). Inventário e MRO testados em `tests/integration/agents/test_tenant_aware_rollout_t_d.py` (sentinel `test_canonical_inventory_count_16_agents` quebra se um 17º ReActAgent for adicionado sem seguir o padrão).

### Padrão mecânico aplicado
1. import `TenantAwareAgentMixin`;
2. `class XReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)`;
3. `_get_runtime_domain_instructions` chama `self._compose_runtime_prompt(input, agent_type=..., domain_specific=..., ...)` em vez de `PromptComposer.for_domain_runtime` direto.

**Helper canônico ampliado:** `TenantAwareAgentMixin._compose_runtime_prompt` agora aceita `agent_type` opcional para preservar chaves YAML quando `agent_type != domain_name` (`cv_screening_pipeline` vs `pipeline`, `jobs_mgmt` vs `jobs_management`).

### Casos especiais
1. `CandidateSelfServiceAgent` mantém override de `_get_system_prompt` (Audit N — evitar persona recruiter); o snippet flui via `_get_system_prompt` (não via runtime instructions).
2. `TalentPoolReActAgent` ganhou `_get_runtime_domain_instructions` novo (antes só tinha `DOMAIN_INSTRUCTIONS = TALENT_POOL_DOMAIN_SPECIFIC` estático — ponto cego histórico do contexto de tenant).
3. `PipelineTransitionAgent` (cv_screening L3) também usa `_get_system_prompt` (chama `get_pipeline_system_prompt(from_stage, to_stage, ...)` com assinatura customizada); o snippet é prefixado ao base.
4. `interview_scheduling` e `offer` **NÃO** são ReActAgents (são graphs/nodes — confirmado por `grep -rln 'LangGraphReActBase' app/domains/`; fora do escopo T-D).
5. `agent_studio/custom_agent_runtime.py` é fora de escopo (custom agents arquitetura separada, conforme spec).

`tenant_strict_override` é deixado em `None` nos 15 (controle via env `LIA_AGENT_TENANT_STRICT`); só wizard tem `True` hard-coded.

---

## T-E (Task #972) — Evals + Bug-Repro

Suite de **não-regressão canônica** contra o bug "LIA pergunta company_id no chat" (caiu 2× — anti-padrão *"fix sem teste de regressão = bug volta"*).

Entrega 3 contratos × 16 agentes = **50 testes** em `tests/integration/agents/test_tenant_context_no_regression.py`:

1. **POSITIVO** — quando snippet presente, prompt renderizado contém marcadores do tenant (nome empresa, setor, plano).
2. **ANTI-PADRÃO** — regex `(?ix)(qual.*empresa|qual.*id.*empresa|preciso.*empresa|me\s+informe.*empresa|informe.*company_id|em\s+qual\s+empresa\s+você\s+trabalha)` **NUNCA** aparece em prompt renderizado de nenhum agente (defesa contra futuro PR adicionar instrução do tipo *"se não souber a empresa, pergunte"*).
3. **FAIL-CLOSED** — em `LIA_AGENT_TENANT_STRICT=true`, agente sem tenant resolvível levanta `MissingTenantContextError` com `tenant_source="system_prompt_hook"` (request rejeitada antes da chamada LLM, LIA nunca tem oportunidade de perguntar empresa).

### Sentinelas adicionais
- (a) wizard strict-override hardcoded `True` mesmo com env OFF em dev;
- (b) snippet **não contém PII de pessoa natural** (CPF/email/phone) — whitelist canônica do FairnessGuard depende dessa invariante (LGPD Art. 5 V);
- (c) inventário 16 agentes (espelha sentinel T-D).

### Golden dataset + gate canônico
- `eval/golden/tenant_context.jsonl` — 18 cenários, 1+ por agente — com `expected_snippet_markers`/`anti_patterns`/`success_criteria` (5 critérios 0-1) e `fail_threshold_avg=0.85`.
- Gate: `python -m eval.eval_runner --gate eval/golden/tenant_context.jsonl` (threshold 0.85, 2 runs consecutivos, exige cobertura ≥80% do inventário 16 agentes).
- Histórico: `eval/.gate_history.json` escrito automaticamente após cada run.

### Out-of-scope (sem alteração nesta task)
Novo eval framework (existe `eval/eval_runner.py` + `eval/eval_judge.py`), Sentry/Prometheus setup, FairnessGuard core, custom agents `agent_studio`. Caminho CSS dos agentes (`CandidateSelfServiceAgent`, `PipelineTransitionAgent`) cobertos só nos contratos 1+2 (override próprio de `_get_system_prompt` que prefixa snippet; strict-mode sync via mixin não se aplica — fail-closed acontece via `_process_langgraph` async).

---

## T-F (MERGED) — Non-ReAct Tenant Snippet Helper

Defesa canônica contra a **3ª recorrência** do bug "LIA pergunta company_id no chat" — auditoria identificou **5 causas raiz** que escapavam do contrato T-D/T-E (que só cobre os 16 ReActAgents).

### R1 — UUID-safe PII masking
`app/shared/pii_masking.py` — novo `_UUID_V4_PATTERN` + Layer-0 guard-token reversível (`\x00UUIDn\x00`) protege UUIDs canônicos (Demo Company `00000000-0000-4000-a000-000000000001`) **antes** dos PII patterns. Sem isso, `PHONE_BR_PATTERN` mastigava UUIDs em `[TELEFONE REMOVIDO]-[TELEFONE REMOVIDO]-...`, fazendo `TenantContextService.get_context()` lançar e degradar para `"sua empresa"/"geral"`.

### R2+R3 — Helper canônico para callsites NON-ReAct
Novo helper canônico módulo-level `resolve_tenant_snippet_for_non_react(ctx, agent_name, company_id_raw)` em `app/shared/agents/tenant_aware_agent.py` — equivalente sync das hooks do `TenantAwareAgentMixin`:
- Mesma telemetria Prometheus `lia_agent_tenant_context_resolved_total{agent,outcome}`.
- Mesma decisão fail-open/fail-closed via `is_tenant_strict_mode()`.
- Mesma `MissingTenantContextError`.

Aplicado em:
- `app/orchestrator/services/fallback_react_service.py:174` — label `agent="fallback_react"` (caminho de fallback do CascadedRouter quando nenhum ReActAgent atende a intent).
- `app/orchestrator/orchestrator.py:416` — label `agent="orchestrator_v1"` (Orchestrator V1 deprecated mas ainda exposto via `/api/orchestrator_routes.py`).

Antes: ambos liam `ctx.get("tenant_context_snippet", "")` direto, sem telemetria nem fail-closed → snippet vazio em strict-mode e LIA voltava a perguntar empresa.

### R4 — Idempotência do main_orchestrator
`app/orchestrator/main_orchestrator.py:336-369` agora é **idempotente** (não sobrescreve snippet já injetado por SSE/WS handler) E adiciona fallback `TenantContextService.build_authenticated_snippet(company_id)` quando `get_context` lança — paridade com `agent_chat_sse.py:331-353` (que já tinha esse fallback).

### R5 — Sentinelas
`tests/integration/agents/test_non_react_tenant_helper_t_f.py` (8 testes) — sentinela canônica com **5 invariantes**:
- POSITIVO (snippet upstream chega ao prompt);
- MISS (TenantContext sync renderiza + cacheia);
- FAIL-CLOSED (strict raises com `tenant_source="non_react_helper"`);
- FAIL-OPEN (dev mode retorna `""` + métrica);
- ANTI-PADRÃO (lê source de `fallback_react_service.py` e `orchestrator.py` exigindo o helper — quebra build se devops re-introduzir o anti-padrão).

`tests/unit/test_pii_masking_uuid_safe.py` (63 testes) cobre R1 com paramétricos para Demo UUID, UUIDs aleatórios, UUIDs em texto livre, UUIDs misturados com PII real (telefone/email/CPF) — confirma que UUIDs sobrevivem e PII real continua redigida.

### Out-of-scope
Novo golden dataset (`eval/golden/tenant_context.jsonl` da T-E continua canônica), Sentry/Prometheus setup (já em produção via T-A).

**NB:** `11912345678` (11 dígitos puros sem separador) é capturado pelo `CPF_PATTERN` — comportamento pré-existente, não regressão T-F.

---

## T-1129 — Multi-tenant Ownership Completo (Tasks #1129a..f + #1149 sealing)

Sucessor natural do tronco T-A→T-F. Enquanto T-A..F endereçaram o caminho
**agente/LLM** (snippet de tenant no prompt), T-1129 fechou o contrato de
**ownership do dado em TODAS as camadas onde o JWT já chegava mas o
`company_id` ainda não era gate explícito**: API REST, cache Redis, jobs
Celery, webhooks externos, queries Elasticsearch, audit-bypass admin.

### As 7 sub-tasks

| # | Sub-task | Entrega | Sentinela |
|---|---|---|---|
| #1129a | Sensor RLS coverage (warn) | `lia-agent-system/scripts/check_table_has_rls_policy.py` + `.rls_allowlist.txt` | `tests/scripts/test_rls_coverage_sensor.py` |
| #1129b | `_require_company_id` gate canônico + sweep ≥90 endpoints | `app/shared/security/require_company_id.py` + counter `lia_endpoint_require_company_id_total` | sentinela (a) abaixo |
| #1129c | Cache Redis tenant-namespaced | `app/orchestrator/semantic_cache.py` refator + `tenant_namespaced_key(...)` + per-tenant rate-limit | sentinela (b) abaixo |
| #1129d | Celery `TenantAwareTask` base | `app/jobs/tenant_aware_task.py` + sweep `app/jobs/tasks/*` + counter `lia_celery_task_tenant_outcome_total` | sentinela (d) abaixo |
| #1129e | Webhook ownership validators | `app/shared/security/webhook_ownership.py::verify_webhook_owner` per-tenant HMAC (Teams/OpenMic/Merge/Twilio/WhatsApp/Mailgun) + `lia_webhook_ownership_outcome_total` | `tests/security/test_webhook_ownership_crossvalidation.py` |
| #1129f | ES `with_tenant_filter` wrapper + sweep 10 serviços | `app/shared/search/tenant_aware_es_query.py::with_tenant_filter` + `lia_es_search_tenant_filter_outcome_total` | sentinela (c) abaixo |
| **#1149** | **Sealing** — eval gate + Playwright + sentinela inventário + promoção RLS sensor | abaixo | abaixo |

### Decisões D1-D8 (consolidadas)

1. **D1 escopo:** "ownership multi-camada" (interpretação justificada em
   `.local/tasks/T-1129-multi-tenant-ownership-plan.md §1.2`).
2. **D2 cache cold-start:** PM autorizou ~5 min p95 router cache miss em
   deploy de #1129c.
3. **D3 webhook secrets:** PM/CS aceitaram dual-validate (global OR
   per-tenant) com deprecação do secret global em 90 d.
4. **D4 SSH staging:** SRE confirmou RLS ativo nas 103 tabelas via
   `\dp <table>` em janela de manutenção (pré-#1129b).
5. **D5 88 tabelas UUID:** **fora de escopo** desta iniciativa; sucessora
   #1129b-uuid trata do refit de tipo + RLS.
6. **D6 `agent_studio/custom_agent_runtime.py`:** fora de escopo per
   histórico T-D (custom agents têm arquitetura própria).
7. **D7 budget eval:** cap $5/PR para `multi_tenant_ownership.jsonl`
   (reusa `eval/eval_judge.py`).
8. **D8 Playwright canon:** suíte mora em
   `plataforma-lia/e2e/tests/multi-tenant/` (espelha `wizard/`).

### Entregas de #1149 (sealing)

- **Eval gate** — `lia-agent-system/eval/golden/multi_tenant_ownership.jsonl`
  (15 cenários = 5 famílias × 3: cache_poison, celery_missing_tenant,
  webhook_forge, es_search_no_filter, endpoint_no_gate). Gate:
  `python -m eval.eval_runner --gate eval/golden/multi_tenant_ownership.jsonl`
  (threshold 0.85, 2 runs consecutivos, histórico em
  `eval/.gate_history.json`).
- **Playwright e2e** —
  `plataforma-lia/e2e/tests/multi-tenant/15-multi-tenant-ownership.spec.ts`
  (4 cenários red-team: B1 vaga A invisível pra B, B2 webhook Teams
  cross-tenant 403, B3 cache Redis isolado, B4 busca ES cross-tenant 0
  hits). Wrapper canônico:
  `plataforma-lia/scripts/run-pw-cenario-1129.sh`.
- **Sentinela AST de inventário** (5 asserções) —
  `lia-agent-system/tests/integration/security/test_multi_tenant_ownership_inventory_t_1129.py`:
  (a) `test_no_endpoint_missing_require_company_id_gate` —
  `tests/.allowlist_public_endpoints.txt` lista as exceções legítimas
  (health, auth, webhooks com `verify_webhook_owner`);
  (b) `test_no_redis_key_without_tenant_namespace`;
  (c) `test_no_es_search_without_tenant_filter`;
  (d) `test_no_celery_task_without_tenant_aware_base`;
  (e) `test_no_legacy_cross_tenant_session_usage`.
- **Sensor RLS promovido para `--block`** em `.github/workflows/adr-001-sensors.yml`
  (Sensor 4) — PR novo com tabela `company_id` sem migration RLS quebra
  build.
- **Métricas Prometheus + Grafana** — painel
  `lia-agent-system/observability/grafana/multi_tenant_ownership.json`
  agrega 6 counters: `lia_endpoint_require_company_id_total`,
  `lia_redis_tenant_namespace_violation_total`,
  `lia_celery_task_tenant_outcome_total`,
  `lia_webhook_ownership_outcome_total`,
  `lia_es_search_tenant_filter_outcome_total`,
  `lia_cross_tenant_session_bypass_total`. 3 alertas Sentry novos:
  `WEBHOOK_OWNERSHIP_MISMATCH` (sev-1), `CELERY_MISSING_TENANT` (sev-2 em
  janela retrocompatível, sev-1 depois), `CACHE_TENANT_NAMESPACE_VIOLATION`
  (sev-1) — runbook em
  [`docs/runbooks/missing_tenant_context.md`](../runbooks/missing_tenant_context.md).

### Como adicionar uma 6ª camada de ownership

1. Implementar gate canônico em `app/shared/security/` ou
   `app/shared/<layer>/`.
2. Adicionar counter Prometheus `lia_<layer>_tenant_outcome_total`.
3. Estender `tests/integration/security/test_multi_tenant_ownership_inventory_t_1129.py`
   com 1 sentinela AST nova.
4. Adicionar 3 cenários no `multi_tenant_ownership.jsonl` (family nova).
5. Adicionar fingerprint Sentry no runbook.
6. Promover sensor para `--block` apenas após code-review final
   (`architect(responsibility="evaluate_task", includeGitDiff:true)`).

---

## Mapa rápido — onde mexer no quê

| Sintoma / mudança | Arquivo |
|---|---|
| Adicionar 17º ReActAgent | atualizar inventário em `tests/integration/agents/test_tenant_aware_rollout_t_d.py` + herdar `TenantAwareAgentMixin` |
| Mudar regex anti-padrão | `tests/integration/agents/test_tenant_context_no_regression.py` |
| Novo cenário golden | `eval/golden/tenant_context.jsonl` |
| Novo callsite NON-ReAct | usar `resolve_tenant_snippet_for_non_react(...)` (NÃO ler `ctx["tenant_context_snippet"]` direto) |
| Mudar formato de `company_id` | `app/shared/value_objects/company_id.py` + migration ajustando `ck_companies_id_format_canonical` |
| Bypass emergencial | `LIA_AGENT_TENANT_STRICT=false` (ver runbook on-call) |
