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
| `WEBHOOK_OWNERSHIP_MISMATCH` | `app/shared/security/webhook_ownership.py::verify_webhook_owner` | An external webhook (Teams / OpenMic / Merge / Twilio / WhatsApp / Mailgun) carries a `company_id` (header, payload, or `linked_account.end_user_origin_id`) that does NOT match the tenant that owns the signing secret. Either a misconfigured integration or a cross-tenant forgery attempt. (Task #1129e) |
| `CELERY_MISSING_TENANT` | `app/jobs/tenant_aware_task.py::TenantAwareTask.before_start` | A Celery task was enqueued without `company_id` in `kwargs` (or with a reserved literal like `"default"`/`"none"`). In strict-mode this raises before the worker runs any SQL. Severity-2 during the retrocompat window, promoted to severity-1 after. (Task #1129d) |
| `CACHE_TENANT_NAMESPACE_VIOLATION` | `app/orchestrator/semantic_cache.py` + `app/shared/{cache_strategy,memory_resolver,...}.py` | A Redis `SET`/`SETEX`/`GET` was issued with a key that does NOT include the `company_id` namespace. Means two tenants can share a cached response (router decision, semantic cache, rate-limit bucket). (Task #1129c) |

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

## 4c. `WEBHOOK_OWNERSHIP_MISMATCH` (Task #1129e)

Triage (≤ 5 min):

1. Identify the provider from the fingerprint tag (`provider=teams|openmic|merge|twilio|whatsapp|mailgun`).
2. Pull the audit row:
   ```sql
   SELECT created_at, criteria_used
   FROM audit_logs
   WHERE decision_type = 'webhook_ownership_verified'
     AND criteria_used->>'outcome' = 'mismatch'
     AND created_at > now() - interval '30 minutes'
   ORDER BY created_at DESC;
   ```
3. **Same provider + same tenant pair in a tight loop:** a customer
   rotated webhook secrets without updating LIA. Coordinate with CS to
   re-import the per-tenant secret in `/configuracoes/integracoes`.
4. **Many tenants firing at once:** rotate the *global* fallback secret
   (`{PROVIDER}_WEBHOOK_SECRET`) — it has likely leaked.
5. Do NOT disable `verify_webhook_owner` to silence — the whole point
   of #1129e is that cross-tenant forgery is auditable.

## 4d. `CELERY_MISSING_TENANT` (Task #1129d)

Triage (≤ 5 min):

1. Pull the Sentry event — it includes `task_name` and the offending
   call site stack.
2. **Single task, single caller:** an `apply_async` lost `company_id`
   in a refactor. Patch the caller; redeploy.
3. **Many tasks from `scheduler`/`beat`:** a periodic task's signature
   wasn't migrated. Check `app/jobs/scheduled_reports.py`.
4. During the retrocompat window (sev-2), the task **was rejected
   before enqueue**; no data was touched. After window flip (sev-1),
   alert + investigate normally.
5. Do NOT flip `LIA_CELERY_TENANT_STRICT=false` — same anti-pattern as
   `LIA_AGENT_TENANT_STRICT=false`. Use a targeted patch.

## 4e. `CACHE_TENANT_NAMESPACE_VIOLATION` (Task #1129c)

Triage (≤ 5 min):

1. Sentry event includes the `module` label (which file emitted the
   key without a namespace).
2. **Quick mitigation:** flush the offending key prefix in Redis:
   ```bash
   redis-cli --scan --pattern '<prefix>:*' | xargs -L 100 redis-cli DEL
   ```
   (this discards any potentially poisoned entries.)
3. Patch the call site to use
   `app.shared.cache.tenant_namespaced_key(company_id, ...)` or to
   include `company_id` directly in the key literal.
4. Re-run sentinela (b) locally:
   `pytest tests/integration/security/test_multi_tenant_ownership_inventory_t_1129.py::test_no_redis_key_without_tenant_namespace`.
5. If the spike persists after the patch deploys, check
   `lia_redis_tenant_namespace_violation_total` in Grafana panel
   "Multi-tenant Ownership" — the counter resets on rebuild, so
   non-zero means new emissions, not historic.

## 5. Long-term remediation

- The Prometheus counter `lia_tenant_demo_fallback_total` should have
  an alert rule: `sum(rate(...)) > 0` for 5 min in prod = page on-call.
- The integration test
  `tests/integration/test_tenant_demo_fallback_t4.py` is the canonical
  no-regression suite. CI must run it on every PR touching
  `app/api/v1/company.py`.
