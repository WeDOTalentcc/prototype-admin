# scripts/

Maintenance and guard scripts wired into pre-commit and CI. Each script is
self-contained, exits non-zero on violation, and is safe to run locally.

## Architectural guards

| Script                                  | Hook id                    | Rule          | Notes                                                            |
| --------------------------------------- | -------------------------- | ------------- | ---------------------------------------------------------------- |
| `check_no_sql_in_controllers.py`        | `no-sql-in-controllers`    | ADR-001 (G1)  | No raw SQL/ORM calls inside `app/api/*` route handlers.          |
| `check_response_models.py`              | `response-model-required`  | ADR-005 (G2)  | Every endpoint declares `response_model`.                        |
| `check_no_pii_in_logs.py`               | `no-pii-in-logs`           | ADR-006 (G4)  | Block PII (`email`, `cpf`, `name`, …) in log calls.              |
| `check_forbidden_imports.py`            | `no-forbidden-imports`     | ADR-012 (G5)  | Ban `libs.models.lia_models.*` and `libs.messaging.lia_messaging.*` imports. |
| `check_init_completeness.py`            | `init-completeness`        | ADR-002 (G6)  | All model files exported in `lia_models/__init__.py`.            |

## Audit guards (Task #326 — §9 recommendations S7.1 / S7.2 / S7.3)

| Script                                    | Hook id                      | Rule  | Description |
| ----------------------------------------- | ---------------------------- | ----- | ----------- |
| `check_shim_sla.py`                       | `shim-sla`                   | S7.1  | Fails if any shim/proxy file has 0 importers AND is ≥ 90 days old (eligible for deletion). |
| `check_no_legacy_tool_decorator.py`       | `no-legacy-tool-decorator`   | S7.3  | Blocks `from langchain_core.tools import tool` inside `app/domains/*/tools/`. Use `@tool_handler` instead. |

> S7.2 (anti-revival of `GlobalToolRegistry`) was retired by Task #350 along
> with `app/shared/global_tool_registry.py` itself.

### Running locally

```bash
# All guards via pre-commit
pre-commit run --all-files

# Individual scripts
python3 scripts/check_shim_sla.py                       # human-readable
python3 scripts/check_shim_sla.py --json                # machine-readable
python3 scripts/check_no_legacy_tool_decorator.py
python3 -m pytest tests/unit/test_global_tool_registry_empty.py
```

### Allow lists / SLA tuning

- `check_no_legacy_tool_decorator.py` carries a small `ALLOW_LIST` of files
  that pre-date the rule. Do **not** extend it; remove entries as files
  migrate to `@tool_handler`.
- `check_shim_sla.py` accepts `--max-age-days` for ad-hoc tuning. The
  default (90 days) is the contractual SLA documented in `ARCHITECTURE.md`.

## Other utilities

The scripts not listed above (`seed_*.py`, `audit_prompts.py`, etc.) are
one-off operational tools rather than guards. They are not wired into CI.


## Pydantic Conventions canonical (2026-05-20 pós-audit E2E)

| Script                                  | Hook id                       | Regras       | Notes                                                |
| --------------------------------------- | ----------------------------- | ------------ | ---------------------------------------------------- |
| `check_pydantic_conventions.py`         | `pydantic-conventions-warn`   | R1+R2+R3+R4  | CLAUDE.md "Pydantic Conventions canonical (registrado 2026-05-20)". |

**Regras:**
- **R1** — Request body schemas DEVEM ter `extra='forbid'` ou herdar de `WeDoBaseModel` (canonical em `app/shared/types.py`). Origem: F1.O2 audit.
- **R2** — Nenhum BaseModel com sufixo `Create|Update|Request|Payload|Input` pode ter field `company_id`. Multi-tenancy canonical — vem do JWT via `Depends(require_company_id)`. Origem: F4.O1+F5.O1.
- **R3** — Nenhum `: UUID = Path(..., pattern=...)` combo. Pydantic 2.10+ não aceita. Use `JobIdParam` alias canonical. Origem: F2.B1 (24 endpoints quebrados).
- **R4** — Nenhum handler com `x_company_id: ... = Header(...)` nem assignment `company_id = x_company_id ...`. Use `Depends(get_verified_company_id)` canonical. Origem: SMOKE-#2 LGPD (28 sites cross-tenant manipulation).

### Como rodar locally

```bash
# Via Makefile (recomendado):
make check-pydantic       # AST checker R1+R2+R3+R4 (~1s)
make smoke                # contract smoke test 1798 endpoints (~34s)
make check-all            # ambos em sequência (~35s)

# Manual:
python3 scripts/check_pydantic_conventions.py app/
python3 -m pytest tests/contract/test_endpoint_smoke.py
```

### Como interpretar violations

Baseline 2026-05-20 (pós-audit E2E + Sprint 0 refinement):

| Regra | Baseline | Sprint pra fix | Prioridade |
| ----- | -------- | -------------- | ---------- |
| R1    | 694      | Sprint 4 (migration gradual + codemod)  | Médio (legacy débito) |
| R2    | 139      | Sprint 4 (gradual)            | Médio |
| R3    | **0** ✅ | Mantém em 0 (sensor blocking) | Alto (regressão crítica) |
| R4    | 29       | Sprint 1 (hybrid via `tenant_guard.get_verified_company_id`) | **Alto (LGPD cross-tenant)** |

### Priorização pra fixar

1. **R3 (0)** — manter em 0. CI promove a blocking automático. Regression = build red.
2. **R4 (29)** — Sprint 1 prioritário (multi-tenancy LGPD risk). Refactor canonical batch via `tenant_guard.get_verified_company_id`.
3. **R2 (139)** — Sprint 4 gradual. Cada PR que toca handler com `company_id` no payload deve corrigir.
4. **R1 (694)** — Sprint 4 gradual + codemod automation. Boy Scout rule: cada PR que toca schema legacy, migra pra `WeDoBaseModel`.

### Adicionar SKIP

Se uma classe LEGITIMAMENTE precisa de `extra='allow'` (e.g., webhook externo com schema drift), adicione ao `SKIP_R1` set em `scripts/check_pydantic_conventions.py` com motivo + ticket.

Pra R4: `SKIP_R4_FILES` e `SKIP_R4_FUNCTIONS` (canonical defense em `tenant_guard.py`).

### Contract Smoke Test

| Script                                  | Hook id                       | Notes                                                |
| --------------------------------------- | ----------------------------- | ---------------------------------------------------- |
| `tests/contract/test_endpoint_smoke.py` | `smoke-test-warn` (futuro CI) | Hits cada endpoint da OpenAPI com sample payload, asserta NÃO retorna HTTP 500. Detecta NameError, schema mismatch, stack leak. |

Baseline 2026-05-20: **1789/1798 passed (99.5%)**, 9 falhas catalogadas em backlog.

```bash
make smoke  # requires uvicorn rodando em localhost:8001
```

Adicionar endpoints conhecidos como falsos positivos: editar `SKIP_ENDPOINTS` em `tests/contract/test_endpoint_smoke.py` com motivo + ticket.


## Operational scripts

### `bootstrap_admin_user.py` — admin de login por e-mail/senha

Cria (ou atualiza, idempotente) um usuário **admin com senha** na tabela de
autenticação `users` (a mesma que `POST /api/v1/auth/login` consulta — NÃO
`client_users`). Use quando a plataforma roda em modo e-mail/senha (WorkOS SSO
desligado) e não há usuário válido para login.

O usuário criado tem `role=admin`, `is_active=true`, `company_id` da empresa
canônica e `password_hash` gerado pelo utilitário canônico (`app/auth/security.py`).
Re-rodar com a mesma `ADMIN_BOOTSTRAP_EMAIL` atualiza a senha do mesmo usuário.

**Secrets / variáveis de ambiente** (nunca hardcoded):

| Variável                     | Obrigatória | Default                                  |
| ---------------------------- | ----------- | ---------------------------------------- |
| `ADMIN_BOOTSTRAP_EMAIL`      | sim         | —                                        |
| `ADMIN_BOOTSTRAP_PASSWORD`   | sim         | — (mín. 8 caracteres)                    |
| `ADMIN_BOOTSTRAP_NAME`       | não         | `Platform Admin`                         |
| `ADMIN_BOOTSTRAP_COMPANY_ID` | não         | `00000000-0000-4000-a000-000000000001` (Demo Company) |

**Rodar em dev** (usa a `DATABASE_URL` configurada):

```bash
cd lia-agent-system
export ADMIN_BOOTSTRAP_EMAIL="owner@example.com"
export ADMIN_BOOTSTRAP_PASSWORD="uma-senha-forte"
python -m scripts.bootstrap_admin_user
```

**Rodar contra produção (one-off):** aponte `DATABASE_URL` para o banco de
produção apenas nesta invocação. Defina os secrets de e-mail/senha do admin no
painel de Secrets do deployment (ou exporte-os no shell de produção) — eles
nunca devem ir para o código.

```bash
DATABASE_URL="<prod-database-url>" \
ADMIN_BOOTSTRAP_EMAIL="owner@example.com" \
ADMIN_BOOTSTRAP_PASSWORD="uma-senha-forte" \
python -m scripts.bootstrap_admin_user
```

Depois de rodar, faça login no site publicado pelo formulário normal de
e-mail/senha com essas credenciais — você chega no dashboard.
