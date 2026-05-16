# Runbook — `MissingTenantContextError` em produção

> **Audiência:** on-call backend / SRE.
> **Origem:** Task #972 (T-E) — observabilidade do `TenantAwareAgentMixin`.
> **Bug histórico:** "LIA pergunta company_id no chat" — caiu 2 vezes.
>   T-A/T-B/T-D corrigiram a mecânica; T-E entrega esta runbook + bug-repro.

## Sintomas

Um ou mais dos seguintes:

- Sentry: aumento súbito de `MissingTenantContextError` (level=`error`).
- Prometheus: `lia_agent_tenant_context_resolved_total{outcome="fail_closed"}` cresce.
- Endpoint de canary `/api/v1/health/compliance/bypass-status` retorna
  `tenant_aware_agent.metrics.<agent>.fail_closed > 0`.
- Alerta Prometheus `LIATenantContextFailClosedRate` (severity=critical) ou
  `LIATenantContextFailOpen` (severity=warning) — definidos em
  `deploy/observability/tenant_context_canary.rules.yaml` (Task #977).
  Snapshot por-processo opcional: `/api/v1/health/tenant-context-canary`.
- Logs estruturados: `agent_tenant_context_missing` (level=ERROR) com
  `tenant_source` em `("agent_input", "system_prompt_hook")`.
- Usuários reportam HTTP 500 ou erro genérico no chat / wizard / kanban.

## Diagnóstico rápido (≤ 5 min)

1. **Confirme a flag estrita:**

   ```bash
   curl -s https://api.<env>/api/v1/health/compliance/bypass-status \
     | jq '.tenant_aware_agent'
   ```

   Se `strict_mode=false` em prod → ver seção "Rollback emergencial".

2. **Identifique o agente afetado:** o `extra.agent` do log
   `agent_tenant_context_missing` aponta o domain (`wizard`, `analytics`, …).

3. **Verifique o caller:**

   - SSE handler (`agent_chat_sse.py`) e WS handler (`websocket_chat.py`)
     devem injetar `tenant_context_snippet` em `input.context` via
     `TenantContextService` antes de chamar o agente.
   - Se ambos handlers estão rodando o código atual, possivelmente o
     `TenantContextService.get_context` está falhando em ler a empresa
     no DB → checar `companies` table + `ensure_default_company`.

4. **Confirme empresa válida no DB:**

   ```sql
   SELECT id, name, sector, plan
   FROM companies
   WHERE id = '<company_id_raw do log>';
   ```

   Esperado: 1 linha. Se 0 → seed `python -m scripts.seeds.demo_company`
   ou similar para esta empresa.

## Causas conhecidas (top-3)

| # | Causa raiz | Sinal | Ação |
|---|---|---|---|
| 1 | Empresa nova criada sem `sector`/`plan` (snippet vazio) | `to_prompt_snippet()` retorna `""` | Backfill via `UPDATE companies SET sector=…, plan=… WHERE id=…` |
| 2 | JWT com `company_id` literal reservado (`"default"`, `"none"`) | Log: `agent_tenant_context_invalid_company_id`, `reason=reserved_literal` | Cliente está reusando token mock — invalidar sessão e exigir re-login |
| 3 | `TenantContextService.get_context` lança exception silenciosa | Log: `agent_tenant_context_resolve_failed` | Investigar trace; provável esquema da tabela `companies` divergente do `lia_models.company.Company` |

## Mitigação imediata

### Caso 1 — Empresa identificada e fix DB possível (preferido)

1. Aplique o backfill no banco.
2. Próxima request da empresa resolve via cache + DB → métricas voltam ao
   normal sem deploy.
3. Não precisa rollback de código.

### Caso 2 — JWT comprometido / cliente errado

1. Invalide sessões da empresa via WorkOS / token revoke.
2. Comunicar o cliente que precisa relogar.

### Caso 3 — Bug em `TenantContextService` ou ramo de código

1. Capture trace completa do Sentry.
2. Compare com a última deploy (`git log` entre tags).
3. Se confirmado bug pós-deploy → rollback do release ou hotfix.

## Rollback emergencial — `LIA_AGENT_TENANT_STRICT=false`

⚠️ **Última opção.** Desliga o fail-CLOSED. Agentes voltam a degradar
silenciosamente para `"sua empresa"/"geral"` — origem do bug histórico.

**Quando usar:** somente se a falha é generalizada (todos os tenants),
você não consegue identificar a causa em ≤ 30 min, e **manter a LIA
respondendo "sua empresa" é menos pior que estar 100% indisponível.**

```bash
# 1. Confirme com on-call sênior + product (registre no incident channel).
# 2. Set via Doppler/secret manager:
doppler secrets set LIA_AGENT_TENANT_STRICT=false --project lia --config prd
# 3. Restart graceful do FastAPI.
# 4. Endpoint /api/v1/health/compliance/bypass-status passa a expor
#    a flag em active_bypasses[]. Sentry envia capture_message
#    "COMPLIANCE BYPASS ATIVA em produção" (já configurado em
#    app/main.py lifespan).
# 5. Abra ticket P0 pra remover a flag em ≤ 24h.
```

**Reverter rollback:** `doppler secrets delete LIA_AGENT_TENANT_STRICT`
+ restart. Endpoint `bypass-status` volta a `warning_count=0`.

## Pós-incidente

- Verifique se o cenário que causou o incidente está coberto pela suíte
  `tests/integration/agents/test_tenant_context_no_regression.py`. Se
  não estiver, **adicione um caso novo** — fix sem teste de regressão =
  bug volta (anti-padrão T-E).
- Adicione 1 turno ao `eval/golden/tenant_context.jsonl` representando
  o cenário do incidente (mesmo agente, prompt similar) para o canary
  pegar regressões futuras.
- Atualize esta runbook se descobriu uma nova causa raiz.

## Métricas relevantes

- `lia_agent_tenant_context_resolved_total{agent, outcome}` — Counter Prom.
  - `outcome=hit` — snippet veio do `input.context` (rota feliz).
  - `outcome=miss` — resolveu via DB no agente (caller esqueceu de injetar).
  - `outcome=fail_open` — sem tenant + dev mode (warning).
  - `outcome=fail_closed` — sem tenant + strict mode → exception.
- Alerta canary recomendado:
  `sum(rate(...{outcome="fail_closed"}[5m])) / sum(rate(...{outcome=~"hit|miss"}[5m])) > 0.001`
  (>0,1% de fail_closed em 24h indica regressão).

## Audit schema mapping — `cross_tenant_session` (Task #1148)

A spec do ADR-030 v2 §4 descreve audit rows com colunas conceituais
`event_type / actor / reason / started_at / ended_at`. A tabela real
`audit_logs` neste repo não tem essas colunas — o canonical helper mapeia
da seguinte forma (duas rows por bypass: uma de `start`, uma de `end`):

| Conceito spec | Coluna real em `audit_logs` |
|---|---|
| `event_type='cross_tenant_bypass'` | `decision_type='cross_tenant_bypass'` |
| `actor` (user id) | `session_id` |
| `reason` | `criteria_used` (JSON `{"reason": "<reason>", "phase": "start\|end"}`) |
| `started_at` | row `action='start'` + `created_at` |
| `ended_at` | row `action='end'` + `created_at` |
| `duration_seconds` | row `action='end'` + `score` |

Consumidores de observabilidade (dashboards, alertas, exports SOX/EU-AI-Act)
devem consultar por `decision_type='cross_tenant_bypass'` e correlacionar
as duas rows via `session_id` (mesmo actor) + `created_at` próximos.

## Referências

- `app/shared/agents/tenant_aware_agent.py` — implementação canônica.
- `app/api/v1/system_health.py` — endpoint `/health/compliance/bypass-status`.
- `tests/integration/agents/test_tenant_context_no_regression.py` — bug-repro.
- `tests/integration/agents/test_tenant_aware_rollout_t_d.py` — inventário.
- `replit.md` seções "Wizard como piloto T-B" + "TenantAwareAgent Roll-out".
- Tasks históricas: #970 (T-B), #971 (T-D), #972 (T-E).
