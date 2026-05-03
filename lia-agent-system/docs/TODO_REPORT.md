# TODO Report — Non-Conforming TODOs

Generated: 2026-05-02
Scope: `app/` directory, `*.py` files
Non-conforming = TODOs without `(owner, ISSUE-XXX, YYYY-MM-DD)` format

## Standard Format Required

```python
# TODO(owner, ISSUE-XXX, YYYY-MM-DD): description
```

---

## Open TODOs

### P1 — Critical (blocked integration / missing service call)

| # | File | Line | TODO Text | Suggested Owner |
|---|------|------|-----------|-----------------|
| 1 | `app/api/v1/admin_platform.py` | 91 | call clients_crud.create_client + workos provisioning | backend-infra |
| 2 | `app/api/v1/admin_platform.py` | 129 | call actual client creation service | backend-infra |
| 3 | `app/api/v1/admin_platform.py` | 134 | call workos_provisioning_service.provision_workos_organization | backend-infra |
| 4 | `app/api/v1/admin_platform.py` | 138 | call email_service.send_welcome_email | backend-infra |
| 5 | `app/api/v1/admin_platform.py` | 143 | call hubspot_service.update_onboarding_status | backend-infra |
| 6 | `app/api/v1/admin_platform.py` | 168 | query ClientAccount + setup sections from DB | backend-infra |

**Context:** All 6 TODOs in `admin_platform.py` relate to the Admin Tenant Gap — admin creates
client in FastAPI/WorkOS/HubSpot but does NOT create accounts in Rails, so multi-tenancy breaks
at client login. These should be tracked as a single issue `admin-tenant-provisioning`.

Suggested conforming format:
```python
# TODO(backend-infra, ISSUE-admin-tenant, 2026-05-02): call clients_crud.create_client + workos provisioning
```

### P2 — Important (data pipeline gap / LIA training gap)

| # | File | Line | TODO Text | Suggested Owner |
|---|------|------|-----------|-----------------|
| 7 | `app/api/v1/teams.py` | 949 | persist to feedback table for LIA training | ai-training |
| 8 | `app/services/onboarding_consumer.py` | 123 | Poll Rails for new invited users | integrations |
| 9 | `app/services/fewshot_evolution_service.py` | 266 | extract from YAML for true novelty check | ai-training |

Suggested conforming formats:
```python
# TODO(ai-training, ISSUE-lia-feedback, 2026-05-02): persist to feedback table for LIA training
# TODO(integrations, ISSUE-rails-sync, 2026-05-02): Poll Rails for new invited users
# TODO(ai-training, ISSUE-fewshot-novelty, 2026-05-02): extract from YAML for true novelty check
```

---

## Summary

| Severity | Count | Risk |
|----------|-------|------|
| P1 | 6 | Broken admin-to-tenant provisioning (client cannot log in after admin creates account) |
| P2 | 3 | Missing LIA training signal + Rails sync gaps |
| **Total** | **9** | |

## Remediation

1. **P1 (admin_platform.py L91-168):** Track as `ISSUE-admin-tenant-provisioning`. Assign to `backend-infra`. Block Q2 release.
2. **P2 item 7 (teams.py L949):** Feedback signal lost — LIA cannot learn from team reactions.
3. **P2 item 8 (onboarding_consumer.py L123):** Rails invited-user sync incomplete.
4. **P2 item 9 (fewshot_evolution_service.py L266):** Novelty check always returns False — risk of duplicate few-shots.
