# Admin Integration Contract — Billing & Plan API

> **Version:** 1.0.0 — 2026-06-18
> **Status:** Production-ready (Replit canonical, branch `feat/benefits-prv-canonical`)
> **Audience:** `admin2.wedotalent.cc` backend — machine-to-machine calls only

---

## Overview

This document describes the service-to-service API used by the external admin panel (`admin2.wedotalent.cc`) to read and manage company billing plans and usage.

**Canonical flow:**

```
admin2.wedotalent.cc  →  INTERNAL_API_TOKEN  →  /api/v1/admin-api/*  →  DB (Subscription + CompanyPlanConfig)
                                                                                   ↓
                                                          client frontend reads via GET /billing/my-plan-summary
```

**Principle:** The admin panel is the **sole decision-maker** for plan assignment and discounts. The client frontend is read-only — it never writes billing data.

---

## Authentication

All endpoints require a `Bearer` token matching the `INTERNAL_API_TOKEN` environment variable.

```
Authorization: Bearer <INTERNAL_API_TOKEN>
```

| Condition | HTTP Status |
|-----------|-------------|
| No `Authorization` header | `401 Unauthorized` |
| Wrong token | `401 Unauthorized` |
| `INTERNAL_API_TOKEN` env var missing | `503 Service Unavailable` |

**Security rules:**
- `INTERNAL_API_TOKEN` is never hardcoded — always from env var
- No JWT, no user context — purely machine-to-machine
- Never send this token to client-facing endpoints

---

## Base URL

```
https://<replit-dev-host>/api/v1/admin-api
```

All paths below are relative to this base.

---

## Endpoints

### 1. GET `/subscription/{company_id}`

Returns the active plan, features, quotas and per-company overrides.

**Response 200:**
```json
{
  "plan_name": "Pro",
  "plan_code": "pro",
  "status": "active",
  "seats_contracted": 20,
  "features_enabled": ["bulk_actions", "export_full", "byok", "api_access"],
  "llm": {
    "embedding_monthly_cap": 200000000,
    "general_monthly_cap": 10000000,
    "byok_active": false,
    "byok_provider": null
  },
  "pearch": {
    "monthly_included_credits": 1500,
    "credits_rollover": false
  },
  "apify": {
    "monthly_included_credits": 1500,
    "credits_rollover": false
  },
  "agent_quotas": {
    "custom_agents": 10,
    "sourcing_agents": 5,
    "digital_twins": 0,
    "campaigns": 5
  },
  "overrides": {}
}
```

**Error codes:**
| Status | Reason |
|--------|--------|
| `401` | Auth failure |
| `404` | Company not found OR no active subscription |
| `503` | `INTERNAL_API_TOKEN` not configured |

---

### 2. GET `/usage/{company_id}?month=YYYY-MM`

Returns token and credit consumption for the billing period.

**Query params:**
- `month` (optional): `YYYY-MM` format. Defaults to current month.

**Response 200:**
```json
{
  "period": {
    "start": "2026-06-01T00:00:00+00:00",
    "end": "2026-07-01T00:00:00+00:00"
  },
  "embedding_tokens_used": 12500000,
  "llm_general_tokens_used": 450000,
  "pearch_credits_used": 87,
  "apify_credits_used": 23,
  "agent_executions_used": 0,
  "actions_used": {
    "cv_analysis": 15,
    "wsi_screening": 8
  }
}
```

**Error codes:**
| Status | Reason |
|--------|--------|
| `401` | Auth failure |
| `404` | Company not found |
| `422` | Invalid `month` format |

---

### 3. POST `/usage/{company_id}/record`

Records external consumption into the credit system (metering from admin or external services).

**Request body:**
```json
{
  "meter_type": "pearch",
  "amount": 10,
  "action_type": null
}
```

**`meter_type` values:** `embedding` | `llm_general` | `pearch` | `apify` | `action` | `agent_execution`

> When `meter_type=action`, `action_type` is required.

**Response 200:**
```json
{"ok": true, "recorded": 10, "meter_type": "pearch"}
```

**Error codes:**
| Status | Reason |
|--------|--------|
| `400` | `action_type` missing when `meter_type=action` |
| `401` | Auth failure |
| `404` | Company not found |
| `422` | Invalid `meter_type` or `amount <= 0` |
| `500` | Credit service error |

**Idempotency:** This endpoint is **not idempotent**. Caller must deduplicate before calling.

---

### 4. PUT `/subscription/{company_id}/plan`

Changes the company's active subscription plan. Invalidates token budget and quota caches. Logs the change in `credit_transactions`.

**Request body:**
```json
{"plan_code": "pro"}
```

**Valid `plan_code` values:** `trial` | `starter` | `pro` | `enterprise`

**Response 200:**
```json
{
  "ok": true,
  "company_id": "uuid",
  "old_plan": "starter",
  "new_plan": "pro"
}
```

**Error codes:**
| Status | Reason |
|--------|--------|
| `400` | Unknown `plan_code` |
| `401` | Auth failure |
| `404` | Company not found OR no active subscription |
| `422` | Extra fields in body (schema rejects them) |

---

### 5. PATCH `/subscription/{company_id}/discount`

Sets a per-company **ALFA discount** on the active subscription.

- `desconto_pct=0` removes any existing discount.
- `desconto_validade=null` means no expiry date.
- The discount appears in `GET /billing/my-plan-summary` under `data.desconto` when `pct > 0`.
- This is a **WeDOTalent-exclusive feature** — clients cannot set or see the raw value.

**Request body:**
```json
{
  "desconto_pct": 15.0,
  "desconto_validade": "2026-12-31T23:59:59"
}
```

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `desconto_pct` | `float` | `0 ≤ x ≤ 100` | `0` removes discount |
| `desconto_validade` | `string \| null` | ISO 8601 datetime | `null` = no expiry |

**Response 200:**
```json
{
  "success": true,
  "company_id": "uuid",
  "desconto_pct": 15.0,
  "desconto_validade": "2026-12-31T23:59:59"
}
```

**Error codes:**
| Status | Reason |
|--------|--------|
| `401` | Auth failure |
| `404` | Active subscription not found |
| `422` | `desconto_pct` out of `[0, 100]` OR invalid `desconto_validade` format |

**How the discount surfaces to the client:**

`GET /billing/my-plan-summary` returns `desconto` only when `pct > 0`:
```json
{
  "plan_code": "pro",
  "desconto": {
    "pct": 15.0,
    "validade": "2026-12-31T23:59:59"
  }
}
```
The `PlanoTab` renders a teal badge with the discount percentage and expiry date.

---

## Plan Tiers Reference

| Code | Name | Seats | LLM/month | Pearch credits | Apify credits |
|------|------|-------|-----------|----------------|---------------|
| `trial` | Trial | 2 | 500k | 200 | 200 |
| `starter` | Starter | 5 | 2M | 500 | 500 |
| `pro` | Pro | 20 | 10M | 1,500 | 1,500 |
| `enterprise` | Enterprise | 100+ | 40M | 4,000 | 4,000 |

Source of truth: `company_plan_configs` DB table (migration 292). Do not hardcode these values.

---

## Subscription Status States

| Status | Meaning |
|--------|---------|
| `active` | Fully operational |
| `trialing` | 30-day trial (transitions to `suspended` on expiry, never `cancelled`) |
| `past_due` | Payment overdue — limited functionality |
| `suspended` | Access suspended — data retained for 30 days |
| `cancelled` | After 30 days suspended without payment — 90 days data export window |

---

## Contract Tests

All endpoints are covered by static file-based contract tests:

```bash
cd lia-agent-system
python -m pytest tests/contract/test_admin_plan_api.py -v
```

Tests cover:
- Auth: 401 without token, 401 with wrong token, 503 with missing env var
- 404 for unknown company
- Schema validation: extra fields → 422
- No hardcoded tokens in source
- PATCH /discount: 422 for pct > 100, pct < 0, unknown company → 404
- OpenAPI schema: PATCH /discount present with 401/404 documented

---

## Changing Plans — Recommended Workflow

```bash
# 1. Verify current subscription
curl -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  https://<host>/api/v1/admin-api/subscription/<company_id>

# 2. Change plan
curl -X PUT -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_code": "pro"}' \
  https://<host>/api/v1/admin-api/subscription/<company_id>/plan

# 3. (Optional) Apply ALFA discount
curl -X PATCH -H "Authorization: Bearer $INTERNAL_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"desconto_pct": 20.0, "desconto_validade": "2026-12-31T23:59:59"}' \
  https://<host>/api/v1/admin-api/subscription/<company_id>/discount
```

---

## Out of Scope (Next Iteration)

- Webhooks (Stripe events → subscription state changes)
- Self-service upgrade/downgrade from client portal
- Automated dunning (past_due → suspended transition)
- FeatureFlag central table (dynamic flag overrides per company)
- Metering ingestion for Studio (R$0.0015/1K tokens)
