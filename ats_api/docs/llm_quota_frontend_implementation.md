# LLM Quota - Frontend Implementation Guide

## Overview

This document describes how to integrate the LLM Quota system into the admin frontend. The backend is fully implemented with all endpoints ready to consume.

---

## 1. API Endpoints

### 1.1 User-facing (own account)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/users/llm_quotas/current` | Get quota + usage + summary for current account |
| `PATCH` | `/v1/users/llm_quotas/update_current` | Update own quota settings (admin only) |

### 1.2 Admin (manage all accounts)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/users/admin/llm_quotas` | List all account quotas |
| `GET` | `/v1/users/admin/llm_quotas/:id` | Show specific quota |
| `PUT` | `/v1/users/admin/llm_quotas/:id` | Update quota (plan, limits, enabled) |
| `POST` | `/v1/users/admin/llm_quotas/:id/grant_extra` | Grant extra budget |
| `POST` | `/v1/users/admin/llm_quotas/:id/reset_usage` | Reset usage counters |

### 1.3 LLM Usage analytics (already integrated)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/users/llm_usages/stats` | Period stats (today, week, month, 30d) |
| `GET` | `/v1/users/llm_usages/by_model` | Cost breakdown by model |
| `GET` | `/v1/users/llm_usages/by_operation` | Cost breakdown by operation |
| `GET` | `/v1/users/llm_usages/by_service` | Cost breakdown by service |
| `GET` | `/v1/users/llm_usages/daily_trend?days=30` | Daily cost/requests trend |
| `GET` | `/v1/users/llm_usages/recent?limit=50` | Recent usage records |
| `GET` | `/v1/users/llm_usages/top_consumers` | Top users by cost |

---

## 2. API Response Schemas

### 2.1 `GET /v1/users/llm_quotas/current`

```json
{
  "success": true,
  "data": {
    "quota": {
      "id": 1,
      "plan": "starter",
      "monthly_cost_limit_usd": 5.0,
      "monthly_request_limit": 5000,
      "burst_rpm": 20,
      "extra_budget_usd": 0.0,
      "extra_budget_expires_at": null,
      "effective_monthly_limit": 5.0,
      "enabled": true,
      "notify_at_percentage": 80,
      "hard_limit": false
    },
    "usage": {
      "period": "2026-02",
      "total_cost_usd": 0.281086,
      "total_requests": 257,
      "total_tokens": 45230,
      "cost_by_model": {
        "gemini-2.0-flash": 0.15,
        "gemini-embedding-001": 0.13
      },
      "cost_by_operation": {
        "chat": 0.15,
        "embedding": 0.13
      },
      "last_synced_at": "2026-02-27T14:30:00Z"
    },
    "summary": {
      "usage_percentage": 5.62,
      "cost_remaining_usd": 4.718914,
      "requests_remaining": 4743,
      "resets_at": "2026-03-01T00:00:00Z",
      "over_limit": false
    }
  }
}
```

### 2.2 `GET /v1/users/admin/llm_quotas` (index)

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "account_id": 1,
      "account_name": "Acme Corp",
      "plan": "starter",
      "monthly_cost_limit_usd": 5.0,
      "monthly_request_limit": 5000,
      "burst_rpm": 20,
      "extra_budget_usd": 0.0,
      "extra_budget_expires_at": null,
      "effective_monthly_limit": 5.0,
      "enabled": true,
      "hard_limit": false,
      "notify_at_percentage": 80,
      "current_usage": {
        "period": "2026-02",
        "total_cost_usd": 0.281086,
        "total_requests": 257,
        "total_tokens": 45230,
        "usage_percentage": 5.62,
        "cost_remaining": 4.718914
      },
      "metadata": {},
      "created_at": "2026-02-27T12:00:00Z",
      "updated_at": "2026-02-27T14:30:00Z"
    }
  ]
}
```

### 2.3 `PUT /v1/users/admin/llm_quotas/:id`

**Request body:**
```json
{
  "llm_quota": {
    "plan": "pro",
    "monthly_cost_limit_usd": 25.0,
    "monthly_request_limit": 25000,
    "burst_rpm": 50,
    "enabled": true,
    "notify_at_percentage": 80,
    "hard_limit": true
  }
}
```

**Response:** Same schema as show (single quota with usage).

### 2.4 `POST /v1/users/admin/llm_quotas/:id/grant_extra`

**Request body:**
```json
{
  "extra_budget_usd": 10.0,
  "expires_at": "2026-03-31T23:59:59Z",
  "reason": "Customer requested extra capacity for hiring sprint"
}
```

**Response:**
```json
{
  "success": true,
  "data": { "..." },
  "message": "Extra budget of $10.0 granted successfully"
}
```

### 2.5 `POST /v1/users/admin/llm_quotas/:id/reset_usage`

**Response:**
```json
{
  "success": true,
  "message": "Usage reset for period 2026-02"
}
```

---

## 3. Available Plans

| Plan | Monthly Cost Limit | Monthly Requests | Burst RPM |
|------|-------------------|-----------------|-----------|
| `starter` | $5.00 | 5,000 | 20 |
| `pro` | $25.00 | 25,000 | 50 |
| `enterprise` | $100.00 | 100,000 | 100 |
| `custom` | Configurable | Configurable | Configurable |

---

## 4. Frontend Implementation

### 4.1 New Composable: `useLlmQuotas.ts`

Create `composables/useLlmQuotas.ts` following the same pattern as `useSearchCredits.ts`.

```typescript
interface LlmQuota {
  id: number
  account_id: number
  account_name: string
  plan: 'starter' | 'pro' | 'enterprise' | 'custom'
  monthly_cost_limit_usd: number
  monthly_request_limit: number
  burst_rpm: number
  extra_budget_usd: number
  extra_budget_expires_at: string | null
  effective_monthly_limit: number
  enabled: boolean
  hard_limit: boolean
  notify_at_percentage: number
  current_usage: {
    period: string
    total_cost_usd: number
    total_requests: number
    total_tokens: number
    usage_percentage: number
    cost_remaining: number
  }
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

interface QuotaSummary {
  usage_percentage: number
  cost_remaining_usd: number
  requests_remaining: number
  resets_at: string
  over_limit: boolean
}
```

**Methods the composable should expose:**

| Method | API Call | Use Case |
|--------|---------|----------|
| `fetchAll(filters?)` | `GET /admin/llm_quotas?plan=X&enabled=X` | List view |
| `fetchOne(id)` | `GET /admin/llm_quotas/:id` | Detail/edit |
| `updateQuota(id, data)` | `PUT /admin/llm_quotas/:id` | Edit form |
| `grantExtra(id, { amount, expires_at, reason })` | `POST /admin/llm_quotas/:id/grant_extra` | Extra budget modal |
| `resetUsage(id)` | `POST /admin/llm_quotas/:id/reset_usage` | Reset button |
| `fetchCurrent()` | `GET /users/llm_quotas/current` | User's own quota view |

### 4.2 New Tab in Account Form

Add a 3rd tab **"Consumo IA"** in `features/admin/accounts/form.vue`, following the exact pattern of the existing "Créditos" tab:

```vue
<!-- Add to v-tabs -->
<v-tab value="llm">
  <v-icon icon="mdi-brain" class="mr-2" size="small" />
  Consumo IA
</v-tab>

<!-- Add to v-tabs-window -->
<v-tabs-window-item value="llm">
  <AccountLlmQuota v-if="props.record?.id" :accountId="props.record.id" />
</v-tabs-window-item>
```

### 4.3 New Component: `features/admin/accounts/llm_quota.vue`

This component receives `accountId` as prop and displays 3 sections:

#### Section A — Balance Cards

4 `StatCard` components (reuse from `features/admin/ai_costs/`):

| Card | Value | Color |
|------|-------|-------|
| Monthly Limit | `$${effective_monthly_limit}` | blue |
| Used | `$${total_cost_usd}` | orange/red based on percentage |
| Remaining | `$${cost_remaining}` | green |
| Requests | `${total_requests} / ${monthly_request_limit}` | purple |

Add a `v-progress-linear` bar below the cards showing `usage_percentage` with color thresholds:
- 0-60%: green
- 60-80%: yellow
- 80-100%: red

Display `resets_at` as "Renova em X dias".

#### Section B — Quota Settings

Editable form fields (only for super admin):

| Field | Component | Notes |
|-------|-----------|-------|
| Plan | `v-select` | Options: starter, pro, enterprise, custom |
| Monthly Cost Limit | `FormInput` (number) | Disabled unless plan=custom |
| Monthly Request Limit | `FormInput` (number) | Disabled unless plan=custom |
| Burst RPM | `FormInput` (number) | Disabled unless plan=custom |
| Enabled | `v-switch` | Toggle account access |
| Hard Limit | `v-switch` | When ON, blocks calls over limit |
| Notify At | `v-slider` (1-100) | Percentage to trigger alert |

When changing **Plan** (non-custom), auto-fill the limit fields from the plan defaults table. When plan is **custom**, enable all fields for manual input.

**Save button** calls `PUT /v1/users/admin/llm_quotas/:id`.

#### Section C — Actions

| Action | Component | API Call |
|--------|-----------|---------|
| Grant Extra Budget | Button → Opens dialog | `POST .../grant_extra` |
| Reset Usage | Button (with confirmation) | `POST .../reset_usage` |

**Grant Extra Dialog fields:**
- Amount (USD): `FormInput` number, required
- Expires at: Date picker, optional
- Reason: `FormInput` text, optional

#### Section D — Usage Breakdown (optional, reuse existing)

Reuse `useLlmUsages` composable filtered by `accountId`:
- Mini chart with `daily_trend` (last 7 days)
- Breakdown by model/operation (small tables or chips)

---

## 5. Component Hierarchy

```
features/admin/accounts/form.vue
├── Tab "Informações" → existing info form
├── Tab "Créditos"    → features/admin/accounts/credits.vue (existing)
└── Tab "Consumo IA"  → features/admin/accounts/llm_quota.vue (NEW)
    ├── Balance Cards (StatCard × 4)
    ├── Usage Progress Bar (v-progress-linear)
    ├── Quota Settings Form
    │   ├── Plan Select
    │   ├── Limit Fields (auto/manual based on plan)
    │   ├── Enabled Switch
    │   ├── Hard Limit Switch
    │   └── Notify Slider
    ├── Actions
    │   ├── Grant Extra Budget (dialog)
    │   └── Reset Usage (confirm dialog)
    └── Usage Breakdown (optional, reuses useLlmUsages)
```

---

## 6. Plan Selector Behavior

When the user selects a plan from the dropdown:

```typescript
const PLAN_DEFAULTS: Record<string, { cost: number; requests: number; rpm: number }> = {
  starter:    { cost: 5.00,   requests: 5000,   rpm: 20  },
  pro:        { cost: 25.00,  requests: 25000,  rpm: 50  },
  enterprise: { cost: 100.00, requests: 100000, rpm: 100 },
}

function onPlanChange(plan: string) {
  if (plan === 'custom') {
    isCustom.value = true
    return
  }
  isCustom.value = false
  const defaults = PLAN_DEFAULTS[plan]
  form.monthly_cost_limit_usd = defaults.cost
  form.monthly_request_limit = defaults.requests
  form.burst_rpm = defaults.rpm
}
```

---

## 7. Color/Status Logic

```typescript
function usageColor(percentage: number): string {
  if (percentage >= 90) return 'error'
  if (percentage >= 80) return 'warning'
  if (percentage >= 60) return 'orange'
  return 'success'
}

function statusChip(quota: LlmQuota): { text: string; color: string } {
  if (!quota.enabled) return { text: 'Disabled', color: 'grey' }
  if (quota.current_usage.usage_percentage >= 100) return { text: 'Over Limit', color: 'error' }
  if (quota.current_usage.usage_percentage >= 80) return { text: 'High Usage', color: 'warning' }
  return { text: 'Active', color: 'success' }
}
```

---

## 8. Optional: Quota Column in Accounts Table

Add a visual column to the accounts listing table showing quota status at a glance:

```
| Account Name | Plan    | Usage      | Status    |
|-------------|---------|------------|-----------|
| Acme Corp   | starter | 5.6% ($0.28) | ● Active |
| Beta Inc    | pro     | 82% ($20.50) | ● High   |
| Gamma Ltd   | starter | disabled     | ● Off    |
```

This requires the accounts `search_url` backend to include `llm_quota` data in the listing, OR a separate call to `GET /admin/llm_quotas` to merge client-side.

---

## 9. Test Script (Manual QA)

### Pre-requisites
- Backend running (`docker compose up`)
- At least 1 account with LLM usage data
- Admin user logged in on the frontend

### Test 1 — View Quota Tab
1. Go to **Admin → Accounts**
2. Click on any account row (opens form in expansion panel)
3. Click tab **"Consumo IA"**
4. **Expected:** 4 balance cards render with real data, progress bar shows percentage, settings form shows plan/limits

### Test 2 — Check Initial Data Consistency
1. On the "Consumo IA" tab, note the values displayed
2. Open a terminal and run:
   ```bash
   docker compose exec web bin/rails runner '
     account = Account.first
     quota = LlmQuota.find_by(account_id: account.id)
     usage = LlmQuotaUsage.current_for(account.id)
     puts "Plan: #{quota.plan}"
     puts "Limit: $#{quota.effective_monthly_limit}"
     puts "Used: $#{usage.total_cost_usd.round(6)}"
     puts "Requests: #{usage.total_requests}"
     puts "Usage%: #{quota.usage_percentage}%"
   '
   ```
3. **Expected:** Values on screen match the terminal output exactly

### Test 3 — Change Plan
1. In the "Consumo IA" tab, change plan from `starter` to `pro`
2. **Expected:** Limit fields auto-fill to $25.00 / 25,000 requests / 50 RPM
3. Click **Save**
4. **Expected:** Success toast, cards update to show new limit, usage percentage recalculates

**Verify backend:**
```bash
docker compose exec web bin/rails runner '
  quota = LlmQuota.find_by(account_id: Account.first.id)
  puts "Plan: #{quota.plan}, Limit: $#{quota.monthly_cost_limit_usd}"
'
```

### Test 4 — Custom Plan
1. Select plan **"custom"**
2. **Expected:** All limit fields become editable
3. Set: Cost=$50, Requests=10000, RPM=30
4. Save
5. **Expected:** Values persisted, cards reflect custom limits

### Test 5 — Grant Extra Budget
1. Click **"Grant Extra Budget"** button
2. Fill: Amount=$10.00, Reason="Testing extra budget"
3. Click confirm
4. **Expected:**
   - Success toast: "Extra budget of $10.0 granted successfully"
   - "Monthly Limit" card updates from $50 → $60 (effective = base + extra)
   - Usage percentage recalculates

**Verify backend:**
```bash
docker compose exec web bin/rails runner '
  quota = LlmQuota.find_by(account_id: Account.first.id)
  puts "Extra: $#{quota.extra_budget_usd}"
  puts "Effective: $#{quota.effective_monthly_limit}"
  puts "Metadata: #{quota.metadata}"
'
```

### Test 6 — Toggle Hard Limit
1. Turn ON the **"Hard Limit"** switch
2. Save
3. **Expected:** When usage exceeds the limit, AI features will be blocked for this account
4. Turn OFF
5. Save
6. **Expected:** Account can exceed limit (soft limit = only notification)

### Test 7 — Disable Account
1. Turn OFF the **"Enabled"** switch
2. Save
3. **Expected:** Status chip changes to "Disabled" / grey
4. Try to use any AI feature from that account's perspective (search, enrichment, etc.)
5. **Expected:** AI calls are blocked with error "account_disabled"
6. Turn ON again, Save
7. **Expected:** AI features work again

### Test 8 — Reset Usage
1. Note current usage values (cost, requests)
2. Click **"Reset Usage"** button
3. Confirm in the dialog
4. **Expected:**
   - Success toast: "Usage reset for period 2026-02"
   - All usage cards go to $0.00 / 0 requests
   - Progress bar goes to 0%

**Verify backend:**
```bash
docker compose exec web bin/rails runner '
  usage = LlmQuotaUsage.current_for(Account.first.id)
  puts "Cost: #{usage.total_cost_usd}, Requests: #{usage.total_requests}"
'
```

**Re-sync to restore:**
```bash
docker compose exec web bin/rails runner 'Llm::QuotaUsageSyncJob.new.perform'
```

### Test 9 — Notify At Percentage
1. Set **"Notify At"** slider to 50%
2. Save
3. **Expected:** When usage crosses 50%, system should trigger notification (check logs or Sidekiq dashboard)

### Test 10 — Data Refresh After LLM Call
1. Note the current usage values
2. In a separate tab, perform an AI action (e.g., search with AI, candidate enrichment)
3. Return to the "Consumo IA" tab
4. Refresh or re-open the tab
5. **Expected:** Usage values increased (cost_usd and total_requests went up)

### Test 11 — Multiple Accounts (Admin Overview)
1. If admin listing shows a "Usage" column, verify each row shows correct status
2. Open 2-3 different accounts and check their quota tabs
3. **Expected:** Each account has independent quota/usage data

### Test 12 — End-to-End Blocking Flow
1. Set account plan to `custom`, cost limit to `$0.001`, hard_limit=ON
2. Save
3. Open a different browser tab logged as a user of that account
4. Try to use AI search
5. **Expected:** Error message indicating quota exceeded
6. Back on admin, click **"Grant Extra Budget"** → $5.00
7. Try AI search again from user tab
8. **Expected:** Search works now

### Test 13 — Full Backend Validation Script
Run the automated test script to validate all backend logic:

```bash
docker compose exec web bin/rails runner '
  load Rails.root.join("scripts/test_llm_quota_system.rb").to_s
  LlmQuotaTest.run
'
```

**Expected:** 7/7 tests pass, state is restored.

---

## 10. Error Handling

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

| HTTP Status | Meaning | Frontend Action |
|-------------|---------|-----------------|
| 200 | Success | Update UI |
| 403 | Not admin | Show "Access Denied" toast |
| 404 | Quota not found | Show "Not found" + auto-provision |
| 422 | Validation failed | Show field-level errors |
| 500 | Server error | Show generic error toast |

---

## 11. Files to Create/Modify

| Action | File | Description |
|--------|------|-------------|
| **CREATE** | `composables/useLlmQuotas.ts` | Composable for all quota API calls |
| **CREATE** | `features/admin/accounts/llm_quota.vue` | Main quota management component |
| **MODIFY** | `features/admin/accounts/form.vue` | Add "Consumo IA" tab |
| **OPTIONAL** | `features/admin/accounts/grant_extra_dialog.vue` | Dialog for granting extra budget |

No new pages or routes needed — everything lives inside the existing accounts form expansion panel.
