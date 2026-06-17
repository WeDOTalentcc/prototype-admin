# ADR-WT-2027 — BYOK (Bring-Your-Own-Key) Strategy: Track-Only When Tenant Pays Direct

**Status**: Accepted
**Data**: 2026-05-22
**Severity**: P0 — Credibility break (UI promised unmetered, backend silently blocked)
**Sprint**: Sprint Voice Gate (Q1 partial)
**Supersedes**: open question "BYOK strategy" in PLAN_WEBSOCKET_VOICE_GATE.md (Q1)
**Related**: ADR-LGPD-001 (anonymized aggregates), CLAUDE.md "REGRA 4 fail-loud em config invalido"

---

## Contexto

Auditoria Wave 4 (2026-05-22) revelou **Bug B3** em
`app/shared/services/ai_credit_gate.py:check_credit_budget`:

> A funcao bloqueava todos os tenants quando
> `current_usage >= monthly_limit`, **inclusive tenants que pagam o
> provider direto (BYOK)**. UI permitia configurar API key propria em
> Configuracoes -> LLM, prometendo billing direto + nao-metrado. Backend
> ignorava: lia o `tenant_llm_configs.providers.{provider}.api_key`
> apenas para ROTEAR a chamada, mas o gate de credito olhava SO o
> `ai_credits_balance.monthly_limit` do plano WeDoTalent.

### Impacto

- **Credibility break**: cliente BYOK paga 2x (direto + WeDoTalent) ou
  apanha 429 sem warning quando cota WeDoTalent acaba.
- **LGPD Art. 37 nao afetado**: WeDoTalent ainda precisa rastrear
  consumption (audit trail), mesmo em modo BYOK. Esta ADR preserva.
- **REGRA 4 violation**: gate falhava silenciosamente (sem log de
  "blocked because no BYOK detected") -- usuario nao tinha visibilidade
  do bug. ADR adiciona `byok_track_only_total` Grafana counter.

PLUS: descoberto bug latente -- a importacao
`from app.models.observability import AiCreditsBalance` em
`ai_credit_gate.py:103` **falhava silenciosamente** (classe vive em
`app.models.ai_consumption`, nao em `observability`). Toda chamada caia
no `fail_safe ALLOW` -- o gate era um no-op silencioso ha tempos. Fix
incluido nesta mudanca.

### Severidade

**P0** porque:
- Cobranca dupla involuntaria a tenants BYOK (financeiro -> credibility).
- Gate de credito todo era no-op silencioso ate hoje (governance gap).

---

## Decisao

**Opcao C: Track-only mode quando BYOK ativo, com soft cap opcional
tenant-managed.**

Avaliados:

| Opcao | Descricao | Decisao |
|-------|-----------|---------|
| A | Gate bloqueia BYOK tambem (defense vs free-tier abuse) | Rejeitada -- viola contrato BYOK + cobra 2x |
| B | BYOK = totalmente unmetered, sem track | Rejeitada -- LGPD Art. 37 exige audit + sem visibilidade Grafana |
| **C** | **BYOK = track-only, alarm opcional (soft cap), nunca bloqueia** | **Aceita** |

Anderson approval recommendation: Opcao C balanceia
- (a) Cliente BYOK paga so o provider, conforme prometido na UI.
- (b) WeDoTalent ainda rastreia consumption pra LGPD + audit + Grafana
  visibility (`byok_track_only_total`).
- (c) Tenant pode opt-in a alarm Grafana via `byok_soft_cap`
  (`byok_soft_cap_breached_total` emite sem bloquear).

## Implementacao canonical

### 1. Detection helper `app.shared.services.byok_detector.is_byok_active`

```python
async def is_byok_active(
    db: AsyncSession,
    company_id: str,
    *,
    service: str | None = None,
    provider: str | None = None,
) -> tuple[bool, str | None]:
    """Returns (byok_active, provider_resolved)."""
```

Per-provider: ter chave Anthropic NAO conta como BYOK OpenAI. Service
identifier (`"voice_realtime"`, `"anthropic_sdk"`, etc.) infere provider
via `_SERVICE_TO_PROVIDER` quando `provider` param e None.

Fail-safe: detection error -> `(False, provider)` (assume WeDo-paid,
gate enforces). NUNCA fail-open pra BYOK (que vazaria dinheiro).

### 2. Schema: `ai_credits_balance` ganha 2 colunas

```sql
ALTER TABLE ai_credits_balance
    ADD COLUMN byok_soft_cap INTEGER NULL,                  -- tenant-managed
    ADD COLUMN byok_active BOOLEAN NOT NULL DEFAULT FALSE;  -- denormalized
```

Migration: `alembic/versions/175_byok_soft_cap.py`
(`revision="175_byok_soft_cap"`, `down_revision="174_briefing_frequency_canonical"`).

`byok_active` e denormalizado pra evitar re-ler `tenant_llm_configs` em
cada LLM call. Source of truth permanece em `tenant_llm_configs.providers.*.api_key`;
o flag e refrescado por `refresh_byok_active_flag` no write path.

### 3. Gate refactor `check_credit_budget`

Novos kwargs: `provider`, `byok_active` (override testing).

Comportamento canonical:

```
if byok_active:
    -> emit byok_track_only_total counter (Grafana)
    -> if projected >= byok_soft_cap (when configured):
           emit byok_soft_cap_breached_total counter + WARN log
    -> return {"byok": True, "remaining": None, ...}  # NEVER raises

else:  # WeDo-paid
    -> if projected >= monthly_limit:
           emit ai_credit_exhausted_total + raise AICreditExhausted  # UNCHANGED
```

### 4. Write-path wiring `refresh_byok_active_flag`

Novo helper em `app.shared.tenant_llm_context`:

```python
async def refresh_byok_active_flag(db, company_id: str, providers_dict: dict) -> bool
```

Invocado em `app/api/v1/llm_config.py:update_llm_config` apos
`repo.upsert`, antes do audit log. Logica:

- `any(_has_real_key(p) for p in providers_dict.values())` define o
  flag novo.
- "Real key" = string nao vazia, sem `"..."` (mascarado pelo GET endpoint).
- `_remove: True` sentinel ignorado.
- Fail-safe: erro no flush nao reverte o config update (gate ainda tem
  live detect via `byok_detector`).

### 5. Sensores

- `scripts/check_credit_gate_respects_byok.py` (BLOCKING) -- AST scan
  garante que `check_credit_budget` (a) referencia `is_byok_active`,
  (b) aceita kwarg `byok_active`, (c) tem path retornando
  `{"byok": True}`, (d) emite `byok_track_only_total` counter.
- `tests/contract/test_byok_gate_skip.py` (13 tests) -- detector + gate
  + write-path refresh. Pure-unit (AsyncSession mockado), zero IO.

### 6. Metricas Grafana

| Counter | Labels | Significado |
|---------|--------|-------------|
| `byok_track_only_total` | `service`, `provider` | Cada chamada de gate em modo BYOK |
| `byok_soft_cap_breached_total` | `company_id_hash`, `service`, `provider` | Tenant excedeu seu proprio soft cap (alarm only) |
| `ai_credit_exhausted_total` | `company_id_hash`, `service` | (existente) bloqueio WeDo-paid |

Comparing `byok_track_only_total / ai_credit_gate_calls_total` da a
fracao do trafico que e BYOK -- KPI de adocao.

## Open items

1. **UI BYOK soft cap setter** -- novo endpoint `PUT /api/v1/ai-credits/byok-soft-cap`
   + tab em `AICreditsPage` so visivel quando `byok_active=true`.
   Status: **TODO** (audit doc: `~/Documents/wedotalent_audit_2026-05-22/byok-soft-cap-ui.md`
   a criar).
2. **Backfill `byok_active` para tenants existentes** -- Sprint follow-up
   pode rodar `UPDATE ai_credits_balance SET byok_active = ...` baseado em
   leitura batch de `tenant_llm_configs`. Hoje o flag fica False ate o
   tenant salvar config de novo (acceptable -- gate cai no live detect via
   `byok_detector` enquanto isso).
3. **`recruiter_agent_v5` integration** -- v5 tem proprio sistema de
   `tenant_policies` (Rails-side) com namespace separado. Quando frontend
   migrar pra chamar v5, este gate cobre apenas o caminho `lia-agent-system`.
   Cross-stack BYOK strategy fica fora do escopo desta ADR.

## Skills aplicadas

- canonical-fix (BYOK detection helper canonical)
- harness-engineering (sensors + Grafana counters)
- production-quality:canonical-standards (Pydantic R1, ADR-001, idempotent migration)
- TDD (13 contract tests verde antes de commit)
- REGRA 4 fail-loud (gate antes era no-op silencioso por import bug)
- REGRA ZERO (zero git push, edicao so via Replit `feat/benefits-prv-canonical`)

## Referencias

- CLAUDE.md `lia_field_toggles canonical pattern` (2026-05-21) -- mesmo
  principio: toggle visivel UI deve ter consumer real, senao = ghost
  setting.
- CLAUDE.md `Pydantic Conventions REGRA 5` -- exception handler global
  evita stack trace leak quando gate raises.
- ADR-LGPD-001 -- audit trail preservado mesmo em modo BYOK (Art. 37).
