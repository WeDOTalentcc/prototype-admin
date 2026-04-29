# MIGRATION REGRESSION BASELINE
## Contratos observáveis a preservar durante a migração V1 → V2

> **Template inicial**. Este documento será **preenchido durante o Sprint I** com dados reais coletados do staging atual. Ele é o **contrato** que a migração deve preservar — qualquer Sprint posterior deve ser comparado contra essas linhas de base.

**Versão**: 1.0 (template)  
**Criado**: 2026-04-26  
**Será preenchido em**: Sprint I (Tarefa B + E)  
**Referenciado por**: `ORCHESTRATOR_MIGRATION_MASTER_PLAN.md` + cada `SPRINT_*.md`

---

## 1. PROPÓSITO

Este documento captura o **comportamento atual de produção** do sistema antes de qualquer migração. Serve como referência para:

1. **Detectar regressão** — qualquer Sprint posterior deve comparar suas métricas contra estas baselines
2. **Validar contratos observáveis** — logs específicos, comportamentos previsíveis que clientes/integrações dependem
3. **Definir limiares de auto-rollback** — se latência piorar X%, rollback automático

**Princípio**: o que não está medido aqui, não está sendo protegido. Adicionar quando descobrir comportamentos não-óbvios.

---

## 2. BASELINE METRICS — Conservative Defaults (2026-04-26)

> **Decisão de produto (Paulo)**: prosseguir com baseline conservador SEM coleta
> de dados de produção. Os valores abaixo são **defaults defensivos** baseados
> em SLOs típicos de chat-bots LLM enterprise. **Auto-rollback dispara em
> qualquer violação** — favoreço falsos positivos a deixar regressão passar.
>
> **Quando substituir por dados reais**: assim que houver acesso ao Sentry/
> Datadog/Honeycomb, atualizar esta seção com `latency-p95-real-2026-XX-XX`
> commits dedicados.

### 2.1 — Latência absoluta máxima (auto-rollback se ultrapassar)

| Flow | Endpoint | p50 max | p95 max | p99 max |
|------|----------|---------|---------|---------|
| Chat REST | `POST /chat/message` | 1500 ms | 5000 ms | 10000 ms |
| Chat WS | `WS /chat/ws` | 1500 ms | 5000 ms | 10000 ms |
| Chat SSE | `SSE /chat/stream` | 1500 ms | 5000 ms | 10000 ms |
| Orchestrated Job Chat | `POST /jobs/chat` | 2000 ms | 6000 ms | 12000 ms |
| Orchestrated Talent Chat | `POST /talent/chat` | 2000 ms | 6000 ms | 12000 ms |
| Orchestrated Jobs Mgmt | `POST /jobs/manage/command` | 2000 ms | 6000 ms | 12000 ms |
| Wizard Job Graph | `POST /job-wizard/graph-orchestrate` | 3000 ms | 8000 ms | 15000 ms |
| Legacy Orchestrator | `POST /api/orchestrator/process` | 2000 ms | 6000 ms | 12000 ms |

**Justificativa dos valores**:
- p95 5-8s = SLO típico de chat com LLM (Claude Sonnet média 2-4s, com tools 4-8s)
- Wizard mais permissivo (cria vagas — operação mais pesada)
- Esses valores são **teto absoluto**, não baseline relativo. Se V2 ficar mais lento
  que isso → rollback. Não comparamos vs "antes" porque não temos baseline real.

### 2.2 — Error rate absoluto máximo

| Flow | Error rate max |
|------|----------------|
| Chat REST | 2% (1 erro em 50 requests) |
| Chat WS | 2% |
| Chat SSE | 2% |
| Orchestrated Job Chat | 1.5% |
| Orchestrated Talent Chat | 1.5% |
| Orchestrated Jobs Mgmt | 1.5% |
| Wizard Job Graph | 3% (operação complexa, tolerância maior) |

**Justificativa**: SLO típico de SaaS é 99% uptime (1% error). Valores acima são
**teto pessimista** considerando que LLM upstream pode falhar. Se V2 piorar isso
→ rollback.

### 2.3 — Throughput mínimo absoluto (regressão se cair abaixo)

Sem dados reais, é difícil estabelecer threshold absoluto. Estratégia:

> **Coletar baseline durante Sprint III.E primeiro estágio (5%)**: rodar 24h em
> staging com flags ON, capturar RPS médio, definir baseline relativo (-10% =
> regressão). Os primeiros 5% do canary servem como auto-baseline.

Procedimento documentado em `SPRINT_III_E_CANARY_PLAN.md` Estágio 1.

### 2.4 — Token usage por tenant (top 10)

Sem acesso ao LLM cost center, impossível fixar threshold absoluto.

> **Estratégia alternativa**: monitorar via OTLP span attribute `tokens_used` por
> request. Se média de tokens por request crescer > 20% em qualquer tenant
> durante canary → manual review (não rollback automático).

Implementação requer adicionar `span.set_attribute("tokens_used", N)` em
`fallback_react_service.py` e `plan_orchestration_service.py`. **Postponed para
Sprint III.E pré-trabalho** (não bloqueia merge da branch atual).

---

## 3. CONTRATOS OBSERVÁVEIS DO V1 (preencher no Sprint I)

Durante a migração, os seguintes comportamentos do V1 **devem ser preservados**:

### 3.1 — Logs específicos emitidos

| Log message (V1) | Quando emitido | Manter pós-migração? |
|------------------|----------------|----------------------|
| `[Orchestrator] context_type override: X → Y` | Quando hardcoded mapping é aplicado (ex: company_settings → settings) | ✅ Sim — análise de produto depende |
| `[Orchestrator] Technical response detected, falling back to LIA-A04` | Quando heurística detecta resposta muito técnica | ✅ Sim — debug em produção |
| `[LIA-A04] _handle_directly bound N tools` | Quando fallback ReAct binding completa | ✅ Sim — observabilidade |
| `[LIA-A04] _handle_directly LLM requested N tool(s)` | Quando LLM pede tool durante fallback | ✅ Sim — observabilidade |
| `[cv_screening rubric] match found / no match` | Quando rubric tool é executada | ✅ Sim — debug de matching |

**Para Sprint II/III**: cada log acima deve ser emitido pelo destino canônico (ex: `[FallbackReActService]` em vez de `[LIA-A04]`), com mesma frequência e contexto.

### 3.2 — Comportamentos não-óbvios (capturados em Sprint I-C, 50 characterization tests verdes)

| # | Comportamento | Onde está em V1 | Test que captura | Por que importante |
|---|---------------|-----------------|------------------|---------------------|
| 1 | "cancelar" / "cancela" / "cancel" → early return com `cancelled=True`, sem tocar router/policy/LLM | `process_request` linhas 117-119 (CancellationHandler.is_cancellation_request) | `test_v1_process_request.py::TestProcessRequestCancellation` | UX previsível — usuário sempre consegue cancelar |
| 2 | "recomeçar" / "restart" → limpa state via `state_manager.clear_state()`, retorna `restarted=True` | `process_request` linhas 120-123 | mesmo arquivo | UX de reset de conversa |
| 3 | `context_type=company_settings` força domain=company_settings (bypass router) | `process_request` linhas 130-145 | `TestProcessRequestContextOverride::test_company_settings_*` | Hardcoded mapping crítico para configuração |
| 4 | `context_type=hiring_policy` força domain=hiring_policy (bypass router) | mesma seção | `test_hiring_policy_context_overrides_routing` | Idem, para política de contratação |
| 5 | Policy denied retorna `success=False` com mensagem "Não foi possível processar: {reason}" | `process_request` linhas 158-161 | `TestProcessRequestPolicyDenied` | Feedback claro ao usuário sobre policy |
| 6 | Domain `autonomous` (Tier 6) retorna direto da `route.intent_details.response` sem chamar domain workflow | `process_request` linhas 240-263 | `TestProcessRequestAutonomousIntercept` | Performance — evita loop em cross-domain |
| 7 | `_handle_directly` para `intent="cv_screening"` ou heurística CV match → tenta `_handle_cv_screening_with_rubric` PRIMEIRO | `_handle_directly` linhas 432-436 | `test_v1_internal_methods.py::TestHandleDirectly` | LIA-A04 — caminho preferencial para CV matching |
| 8 | `is_tool_allowed` usa `prompt_context: str` (NÃO `scope`) — retornará `False` para tool desconhecida | `is_tool_allowed` linha 605 | `TestIsToolAllowed::test_unknown_tool_*` | API não-óbvia (vs main_orchestrator que pode usar `scope`) |
| 9 | `get_available_tools` aceita `agent_type: str | None` — retorna `list[dict]` (NÃO dict) | `get_available_tools` linha 598 | `TestGetAvailableTools::test_no_agent_type_returns_list` | Tipo de retorno consistente |
| 10 | `execute_plan(conversation_id, plan_dict)` → constrói `ExecutionPlan` interno e chama `_plan_executor.execute()` (não `execute_from_dict`) | linhas 608-640 | `TestExecutePlan::test_returns_dict_with_required_keys` | API interna do plan_executor |
| 11 | `process_analytics_request` se `command in COMMAND_TEMPLATES` → `execute_command()`, senão → `analyze_natural_query()` | linhas 652-668 | `TestProcessAnalyticsRequest::test_command_in_templates_*` | Routing analytics templated vs natural |
| 12 | `process_analytics_request` em exception → retorna `{success: False, error: str(e)}` (graceful degradation) | linha 668-670 | `TestProcessAnalyticsRequest::test_handles_exception_gracefully` | Resiliência |
| 13 | `invalidate_cache_for_entity("job", id)` → delega para `invalidate_for_job(id)` (entity-specific path) | linhas 105-110 | `TestInvalidateCacheForEntity::test_job_routes_*` | Granularidade de invalidação |
| 14 | `invalidate_cache_for_entity("unknown", id)` → fallback para `invalidate_by_pattern(f"*unknown*id*")` | linha 112 | `test_unknown_entity_uses_pattern_invalidation` | Generic fallback |
| 15 | `process_request_with_memory` em exception → faz `db.rollback()` antes de retornar dict de erro | linhas 372-376 | `TestProcessRequestWithMemory::test_handles_exception_gracefully` | Transação atomic |
| 16 | `process_request_with_memory` propaga `company_id` do `context` para `enhanced` context (P0 LGPD) | linhas 343-347 | `test_propagates_company_id` | Multi-tenant isolation |

### 3.3 — Multi-tenant isolation (P0 LGPD)

| Verificação | Status atual | Mantido na migração? |
|-------------|--------------|---------------------|
| Cache não vaza entre `company_id` distintos | ✅ Validado em test_orchestrator_consolidation.py | ✅ Sim |
| `process_request` falha se `company_id` ausente do contexto | ✅ Validado | ✅ Sim |
| Tools com `require_company=True` rejeitam chamadas sem context | ✅ Validado | ✅ Sim |
| Audit log inclui `company_id` em 100% dos eventos | _TBD_ — verificar em Sprint I | ✅ Sim |

---

## 4. CRITÉRIOS DE REGRESSÃO

### 4.1 — Auto-rollback (Sprint III canary)

Critérios que disparam **rollback automático** sem aprovação humana:

- Error rate ≥ baseline + 1% por 5 min consecutivos
- Latência p95 ≥ baseline + 20% por 10 min consecutivos
- Audit log drop rate ≥ 0.1%
- Multi-tenant isolation violation detected (verificado por property test em produção)

### 4.2 — Manual review

Critérios que pausam o canary e exigem investigação manual:

- Error rate ≥ baseline + 0.5%
- Latência p95 ≥ baseline + 10%
- Token usage / tenant ≥ baseline + 5% (sinal de loop ou prompt mais longo)
- Spans com atributos faltantes (`tenant.company_id` ausente)

### 4.3 — Manual cancel migração

Critérios que abortam a migração e revertem para status quo:

- Comportamento crítico do V1 não pode ser preservado em V2 (ex: descobrir feature não documentada)
- Compliance LGPD em risco (regressão em audit log ou multi-tenancy)
- Stakeholder externo bloqueia (cliente reporta breakage)

---

## 5. CHECKLIST DE PREENCHIMENTO (Sprint I)

```
[ ] Tarefa B — Coletar baselines de produção/staging:
    [ ] Latência p50/p95/p99 por flow (seção 2.1)
    [ ] Error rate por flow (seção 2.2)
    [ ] Throughput por flow (seção 2.3)
    [ ] Token usage top 10 tenants (seção 2.4)

[ ] Tarefa A — Inventariar comportamentos do V1:
    [ ] Logs específicos (seção 3.1)
    [ ] Comportamentos não-óbvios (seção 3.2)
    [ ] Multi-tenant verifications (seção 3.3)

[ ] Tarefa E — Revisão final:
    [ ] Backend lead reviewed
    [ ] Paulo reviewed
    [ ] Mergeado em develop
```

---

## 6. HISTÓRICO DE MUDANÇAS

| Data | Mudança | Autor |
|------|---------|-------|
| 2026-04-26 | Template inicial criado | Claude (auditoria orchestrator) |
| 2026-04-26 | Seção 3.2 preenchida com 16 contratos observáveis capturados via 50 characterization tests | Sprint I-E |
| 2026-04-26 | Span constants canônicas linkadas (`app/orchestrator/_observability.py`) | Sprint I-D |
| _TBD_ | Métricas de produção da Seção 2 preenchidas (Sprint I-B) | Pendente acesso staging |

---

## 7. REFERÊNCIAS

- `ORCHESTRATOR_MIGRATION_MASTER_PLAN.md` — Plano mestre da migração
- `ORCHESTRATOR_MIGRATION_SPRINT_I.md` — Sprint I onde este doc é preenchido
- `AUDITORIA_CANONICA_2026_Q2.md` — Auditoria canônica geral
- ADR-019 (a criar no Sprint I) — Decisão arquitetural de consolidação
