# Task #293 — Evidências de validação (ciclo auth + relogin Funil)

## 1. Backend — não-regressão em produção

Testes automatizados em `lia-agent-system/tests/unit/test_auth_enforcement_dev_fallback.py`
(executados com `APP_ENV=production` + `LIA_DEV_MODE=""`):

```
test_production_without_bearer_returns_401                PASSED
test_production_rejects_dev_api_key_header_when_dev_mode_off  PASSED
test_dev_mode_injects_canonical_demo_uuid                 PASSED
test_dev_mode_without_dev_key_header_rejects              PASSED
========================= 4 passed in 1.25s =========================
```

Probes curl contra a instância em execução (dev-server local, LIA_DEV_MODE off):

| # | Request | Esperado | Observado |
|---|---------|----------|-----------|
| 1 | `GET /api/v1/candidates` sem Bearer | 401 `Authentication required` | **HTTP 401** `{"detail":"Authentication required"}` |
| 2 | `GET /api/v1/candidates` com `X-Dev-Api-Key` inválido | 401 | **HTTP 401** `{"detail":"Authentication required"}` |
| 3 | `GET /api/v1/candidates` com `Authorization: Bearer bogus.invalid.token` | 401 `Invalid or expired token` | **HTTP 401** `{"detail":"Invalid or expired token"}` |

Conclusão: comportamento de produção preservado. Nenhum bypass via header.

## 2. Backend — dev fallback injeta UUID canônico

Caso coberto por `test_dev_mode_injects_canonical_demo_uuid`: middleware com
`LIA_DEV_MODE=true` + `X-Dev-Api-Key` correta injeta `DEMO_COMPANY_UUID`
(não a string legada) em `request.state.company_id`, `token_payload.company_id`
e no `ContextVar` `_current_company_id`. O teste assert explicitamente que o
valor não é a string legada `demo_company`.

## 3. Frontend — classificação de erro no hook

`plataforma-lia/src/hooks/__tests__/use-candidates-list.test.ts` (14 testes):

```
HTTP 401 → errorKind="unauthorized"    PASSED
HTTP 403 → errorKind="forbidden"       PASSED
HTTP 500 → errorKind="server"          PASSED
HTTP 503 → errorKind="server"          PASSED
Network error (no status) → errorKind="network"  PASSED
```

## 4. Frontend — contrato i18n do Funil

`plataforma-lia/src/__tests__/i18n-pipeline-auth.test.ts` (3 testes) garante
que as chaves `pipeline.auth.{reloginTitle, reloginCta, unauthorizedMessage,
forbiddenMessage, serverErrorMessage, networkErrorMessage}` existem em ambos
os bundles (`pt-BR.json`, `en.json`) e que não há drift entre locales.

## 5. Frontend — UX de relogin

`FunilDeTalentosClient.tsx` renderiza:

- **401/403**: elemento com `role="alert"`, `data-testid="funil-relogin-state"`,
  substitui a tabela. Texto derivado de `t('auth.<kind>Message')`. CTA usa
  `useLocale()` para montar `/<locale>/login?next=<pathname+search>`.
- **500/5xx/network**: banner inline com `data-testid="funil-error-state"`,
  botão "Tentar novamente" que chama `refresh()` do hook.

A tabela permanece oculta durante estado de relogin (evita mostrar dados stale).
