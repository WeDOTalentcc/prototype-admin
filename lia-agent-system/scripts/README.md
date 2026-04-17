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
| _(pytest)_ `tests/unit/test_global_tool_registry_empty.py` | n/a                          | S7.2  | Anti-revival of Task #308: `GlobalToolRegistry._registry` MUST be empty after app boot. |
| `check_no_legacy_tool_decorator.py`       | `no-legacy-tool-decorator`   | S7.3  | Blocks `from langchain_core.tools import tool` inside `app/domains/*/tools/`. Use `@tool_handler` instead. |

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
