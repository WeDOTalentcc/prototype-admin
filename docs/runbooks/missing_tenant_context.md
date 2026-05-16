# Runbook — Missing Tenant Context / Demo Fallback Drift

**Audience:** on-call SRE
**Severity:** SEV-2 (data integrity / tenant isolation)
**Time-to-diagnosis target:** ≤ 5 min

This runbook covers two related Sentry alerts that indicate the
platform is degrading silently into the **Demo Company** instead of
serving the caller's real tenant.

| Sentry fingerprint | Fired by | What it means |
|---|---|---|
| `LIA_AGENT_TENANT_STRICT_BYPASS` | `app/main.py` lifespan | `LIA_AGENT_TENANT_STRICT=false` was set in prod. ReAct agents can degrade to "sua empresa"/"geral". (T-A) |
| `TENANT_DEMO_FALLBACK_PROD` | `app/shared/security/tenant_demo_fallback.py` | A real-tenant request hit the legacy Demo Company fallback in `GET /company/profile` or `POST /company/onboarding`. (T4 #991) |
| `CROSS_TENANT_BYPASS_SPIKE` | `app/shared/admin/cross_tenant_session.py` | Rate of legitimate cross-tenant RLS bypasses (`lia_cross_tenant_session_bypass_total`) exceeds `baseline + 3σ`. Either a runaway admin batch job or — worse — a compromised superadmin account hitting many tenants in succession. (Task #1148) |

## 1. Confirm the alert

```bash
curl -s https://api.lia.wedotalent.com/api/v1/health/compliance/bypass-status | jq
```

Look at:

- `flags.LIA_AGENT_TENANT_STRICT` — must be `true` in prod.
- `tenant_aware_agent.metrics` — `fail_open` should stay `0`.
- `tenant_demo_fallback.total_count` — must stay `0` in prod. Per-process; for the authoritative aggregate, query Prometheus:

```promql
sum(rate(lia_tenant_demo_fallback_total[5m])) by (endpoint, reason)
```

## 2. Top-3 root causes (T4 #991)

1. **Real-tenant user has no `CompanyProfile` row.** Symptom: `reason="missing_profile_for_real_tenant"`. Fix: complete onboarding via `/configuracoes/minha-empresa`, or have admin run the seed for that tenant.
2. **Profile lookup keyed on the wrong column.** A recent migration renamed `client_account_id` or dropped an index. Symptom: `endpoint="get_company_profile"` spikes for many tenants at once. Check the latest Alembic migration in `lia-agent-system/migrations/versions/`.
3. **Auth context lost across a proxy hop.** `current_user.company_id` arrives as `None`. Symptom: `reason="no_auth_context_dev_fallback"` in prod. Check WorkOS/JWT middleware logs for issuance failures.

## 3. Mitigation (≤ 5 min)

- **Stop the bleeding.** If the spike is coming from one tenant, ask Customer Success to pause the affected workspace from the admin console.
- **Do NOT** flip `LIA_AGENT_TENANT_STRICT=false` to "make it go away" — that masks the leak and re-opens the bug class T4 was built to close.

## 4. Emergency rollback

The fix is fully behind the helper module. To revert in extremis:

```bash
git revert <T4 commit sha>
```

There is no env-flag rollback by design — silent Demo fallback is a
tenant-isolation breach (LGPD Art. 5 V) and must not be re-enabled
without code review.

## 4b. `CROSS_TENANT_BYPASS_SPIKE` — specific triage

This alert fires when the rate of legitimate cross-tenant bypasses opened via
`app.shared.admin.cross_tenant_session` exceeds `baseline + 3σ` over a
rolling 15-min window:

```promql
sum(rate(lia_cross_tenant_session_bypass_total[5m])) by (reason)
  > (
      avg_over_time(
        sum(rate(lia_cross_tenant_session_bypass_total[5m])) by (reason)[7d:5m]
      )
      + 3 * stddev_over_time(
        sum(rate(lia_cross_tenant_session_bypass_total[5m])) by (reason)[7d:5m]
      )
  )
```

Triage (≤ 5 min):

1. Pull the matching audit rows — each bypass writes a `start` + `end` pair
   into `audit_logs` with `decision_type='cross_tenant_bypass'`,
   `agent_name='cross_tenant_session'`, the actor in `session_id`, and the
   `reason` inside `criteria_used`:
   ```sql
   SELECT created_at, session_id AS actor, criteria_used
   FROM audit_logs
   WHERE decision_type = 'cross_tenant_bypass'
     AND created_at > now() - interval '30 minutes'
   ORDER BY created_at DESC;
   ```
2. **Same actor + same reason in a tight loop:** likely a runaway scheduled
   report. Pause the job in the admin console; do NOT rotate creds yet.
3. **Same actor + many different reasons / cross-tenant fanout:** treat as
   account-takeover. Revoke the actor's superadmin session, rotate their
   credential, and page Security.
4. **Many different actors firing at once:** check for a recent deploy that
   wrapped a non-admin endpoint with `Depends(require_superadmin)` by mistake
   — `git log --since=24h -- lia-agent-system/app/api/` is usually enough.

Do **NOT** roll back the helper to silence the alert — bypass is *supposed* to
be auditable. The whole point of Task #1148 is that we now know who did it.

## 5. Long-term remediation

- The Prometheus counter `lia_tenant_demo_fallback_total` should have
  an alert rule: `sum(rate(...)) > 0` for 5 min in prod = page on-call.
- The integration test
  `tests/integration/test_tenant_demo_fallback_t4.py` is the canonical
  no-regression suite. CI must run it on every PR touching
  `app/api/v1/company.py`.
