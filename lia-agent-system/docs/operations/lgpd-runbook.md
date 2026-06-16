# LGPD Operations Runbook — WeDOTalent LIA

**Status**: Active
**Last update**: 2026-05-06 (Q2 Canonical Refactor Sprint 4B)
**Owner**: Compliance / Engineering joint

This runbook covers operational procedures for LGPD compliance of the
LIA backend. It is the **single source of truth** for compliance
incident response, audit pulls, and routine validation.

---

## 1. Compliance invariants (must never break)

| Invariant | Where enforced | How verified |
|---|---|---|
| Multi-tenancy isolation | App: `tool_handler` ContextVar (Sprint 1B). DB: RLS migration 068 + 118 (Sprint 4A) | Sensors `check_no_tenant_in_tool_schemas`, `check_no_cid_empty_escape`, `check_table_has_rls_policy` + integration tests `tests/integration/test_rls_candidates.py` |
| Protected attributes registry loaded | `is_registry_loaded()` + FairnessGuard `__init__(strict=True)` in production (Sprint 4B.1) | `tests/unit/compliance/test_fairness_guard_failfast.py` (6/6) + startup raise on missing YAML |
| No PII in logs | `app/shared/compliance/pii_masking.py` + `Sentry before_send` | `scripts/check_no_pii_in_logs.py` (pre-commit blocking) |
| Article 11 (sensitive data filter) | `lgpd_field_registry.py:19` (ATS outbound) + `fairness_guard.py:895` (learning validator) | Unit tests + manual audit |
| Article 20 (human review) | `handlers_lifecycle.py:1088-1098` + `_shared.py:632` | `reviewer_id` required in rejection flows |
| 4/5 rule + chi-squared | `bias_audit_service.py:220-308` | `bias_audit_snapshots` table populated on demand |
| LGPD retention policy | `jobs/tasks/compliance.py:run_lgpd_cleanup_task` daily 02h BRT | Celery beat `lgpd-cleanup-daily` |

---

## 2. Daily / weekly checks

### Daily (automated, no human action needed)

- **02h BRT**: `lgpd-cleanup-daily` Celery beat fires `run_lgpd_cleanup_task`. Verify in Sentry/logs no failures.
- **03h UTC**: RAGAS evaluation (model drift) `ragas-evaluate-daily`.
- **06h BRT**: Daily briefings.

### Weekly (manual until Sprint 5)

- **Monday 09h BRT**: pull `bias_audit_snapshots` to confirm zero `has_alerts=true` rows for the past 7 days. If any: open ticket → see §4.
- **Monday 10h BRT**: review Sentry breadcrumbs filtered by `compliance.protected_attributes.*` — should be empty in steady state.

### Monthly

- **1st of month**: audit retention policy compliance (`apply_audit_lifecycle_policy` task).

---

## 3. Pre-deploy checks (every PR)

Pre-commit hooks (auto, blocking):
- `no-pii-in-logs` — no PII leakage in log calls
- `no-tenant-in-tool-schemas --block` — no `company_id` in tool JSON schemas
- `no-cid-empty-escape` — no `:cid='' OR ...` SQL escape pattern
- `no-devmode-in-prod-env` — no `LIA_DEV_MODE=1` in prod env files
- `tenant-db-required` — every `app/domains/` endpoint uses `get_tenant_db`
- `no-sql-in-controllers` — no SQL in API controllers (ADR-001)
- `response-model-required` — all endpoints have `response_model`

Pre-commit hooks (auto, warn-only — visibility only):
- `mypy-warn-only`
- `company-id-in-routes-warn`
- `no-direct-contextvar-set-warn`
- `table-has-rls-policy` — RLS coverage gaps surfaced (currently 180 — Sprint 5)

CI (manual or pipeline):
- All pre-commit checks
- `check_llm_factory_enforcement`
- `check_tenant_db`
- `check_tool_output_schemas`
- `check_tool_governance`
- Full pytest unit + integration

---

## 4. Compliance incident response

### Symptom: empty PROTECTED_ATTRIBUTE_IDS at runtime

This is the LGPD compliance gap that ran in production from Mar 2026 to
2026-05-06 (commit `ca6f004cf` fixed the loader path bug).

**Detection**:
- Sentry breadcrumb category `compliance.protected_attributes.yaml_not_found`
- FairnessGuard fails to initialize (`RuntimeError`) in production (Sprint 4B.1 strict mode)
- Test `test_fairness_guard_succeeds_when_registry_loaded` fails

**Diagnosis**:
```bash
ssh replit-wedo-0405
cd /home/runner/workspace/lia-agent-system
python3 -c "
from app.shared.compliance.protected_attributes import _CONFIG_PATH, is_registry_loaded
print('path:', _CONFIG_PATH)
print('loaded:', is_registry_loaded())
"
```

Expected: path ends with `/app/config/protected_attributes.yaml`, loaded=True.

**Fix**:
- If path wrong: regression on `app/shared/compliance/protected_attributes.py:24-27`. Verify single canonical `_CONFIG_PATH` assignment.
- If file missing: restore `app/config/protected_attributes.yaml` from git or backup. Schema documented in ADR-031 v2.
- If parse error: `python3 -c "import yaml; print(yaml.safe_load(open('app/config/protected_attributes.yaml')))"` to surface error.

### Symptom: cross-tenant data leak alert

**Detection**:
- `bias_audit_snapshots` shows `has_alerts=true`
- User reports seeing other tenants' data
- Sentry: queries returning rows with `company_id` differing from session

**Diagnosis** (per ADR-030 v2):
```sql
-- Check RLS state of suspect table
SELECT rowsecurity FROM pg_tables WHERE tablename = '<table>';

-- Check policies
SELECT * FROM pg_policies WHERE tablename = '<table>';

-- Check active session var
SELECT current_setting('app.company_id', true);

-- Confirm session role is lia_app (not postgres superuser)
SELECT current_user, session_user;
```

**Fix path**:
1. If `rowsecurity = false` → table missing RLS migration. Create migration following `118_rls_candidates.py` pattern.
2. If session running as `postgres` (not `lia_app`) → check `app/core/database.py:get_tenant_db` is being used (not raw `AsyncSessionLocal()`). RLS bypass is intentional only via `cross_tenant_session` (Sprint 5 — currently no implementation, no admin paths require).
3. If `app.company_id` empty → middleware not setting context. Check `app/middleware/auth_enforcement.py:_set_company_id_from_jwt` is called.

### Symptom: LGPD subject access request (DSR Art. 18)

User exercises right to access / portability / deletion / correction.

**Procedure**:
1. Verify identity (out of scope here — see Legal team).
2. Access:
   ```bash
   # Pull all candidate data for given user_id / candidate_id
   psql "$DATABASE_URL" -c "SET app.company_id = '<company_id>'; \
     SELECT row_to_json(c) FROM candidates c WHERE id = '<candidate_id>';"
   ```
3. Erasure:
   - Run `lgpd_cleanup_service.run_cleanup` with `dry_run=False` for the candidate's data.
   - For learning patterns: also recompute `bigfive_department_profiles` to remove subject's contribution.
4. Document in `audit_logs` with `event_type=lgpd_subject_request`, reason, requestor.

### Symptom: data incident (Art. 48)

ANPD breach notification within 72h.

**Procedure** documented in `docs/operations/data-incident-response.md` (separate doc — not in scope of this runbook).

---

## 5. Verifying compliance state

### Quick health check (paste in any dev session)

```bash
ssh replit-wedo-0405
cd /home/runner/workspace/lia-agent-system

# 1. Sensors green
python3 scripts/check_no_tenant_in_tool_schemas.py --block && echo "✓ no tenant in schemas"
python3 scripts/check_no_cid_empty_escape.py && echo "✓ no SQL escape pattern"
python3 scripts/check_no_devmode_in_prod_env.py && echo "✓ no devmode in prod"

# 2. Compliance loader healthy
python3 -c "
from app.shared.compliance.protected_attributes import is_registry_loaded, PROTECTED_ATTRIBUTE_IDS
assert is_registry_loaded(), 'YAML not loaded'
assert len(PROTECTED_ATTRIBUTE_IDS) >= 7, f'only {len(PROTECTED_ATTRIBUTE_IDS)} attrs'
print(f'✓ {len(PROTECTED_ATTRIBUTE_IDS)} protected attributes loaded')
"

# 3. RLS state of critical tables
psql "$DATABASE_URL" -c "
  SELECT tablename, rowsecurity FROM pg_tables
  WHERE tablename IN ('candidates', 'job_vacancies', 'audit_logs', 'interviews')
  ORDER BY tablename;
" | grep -E '^\s+\S+\s+\| t$' | wc -l
# Expected: 4

# 4. RLS coverage sensor (informational)
python3 scripts/check_table_has_rls_policy.py 2>&1 | head -3
```

---

## 6. References

- ADR-031 v2 — Protected Attributes Loader Path + Compliance Observability
- ADR-030 v2 — Postgres RLS Baseline + Coverage Gaps
- ADR-029 — ToolDefinition Unification + RuntimeContext Wrapper
- ADR-001 — Repository Pattern (Caminho C policy)
- ADR-006 — No PII in logs
- LGPD Art. 5º (definitions)
- LGPD Art. 11 (sensitive data)
- LGPD Art. 16 (retention)
- LGPD Art. 18 (subject rights)
- LGPD Art. 20 (automated decisions / human review)
- LGPD Art. 48 (incident notification)
- Lei 9.029/95 (anti-discrimination in hiring)
- EEOC 4/5 Rule (Title VII)

---

## 7. Change log

| Date | Change |
|---|---|
| 2026-05-06 | Initial version (Sprint 4B.3). Covers Sprint 1+4 canonical state. |
