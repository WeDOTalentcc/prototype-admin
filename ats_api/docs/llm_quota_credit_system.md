# LLM Quota & Credit System

## Overview

The LLM Quota system controls how much each account can spend on LLM (Gemini) calls per month. Instead of counting raw requests, the system tracks **cost in USD** as the primary metric — because an embedding call (~$0.0001) costs vastly less than a chat completion (~$0.01+).

Every account gets a **plan** (starter, pro, enterprise) that defines monthly cost limits, request limits, and burst rate limits. The system is enforced inline in `GeminiClient` before every LLM call.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GeminiClient                           │
│                                                             │
│  1. enforce_rate_limit!(tracking)                           │
│     └─► Llm::RateLimiter.check!                            │
│         ├─ Burst RPM check (Redis sorted set)              │
│         ├─ Monthly cost check (LlmQuotaUsage)              │
│         └─ Monthly requests check (LlmQuotaUsage)          │
│                                                             │
│  2. Execute LLM call (Gemini API)                          │
│                                                             │
│  3. record_quota_usage!(account_id, cost, tokens, tracking)│
│     └─► Llm::RateLimiter.record_usage!                     │
│         ├─ Increment burst counter (Redis)                  │
│         ├─ Increment LlmQuotaUsage (PostgreSQL)            │
│         └─ Check notification threshold                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Tables (public schema)

### `llm_quotas`

One row per account. Defines the account's spending limits.

| Column                    | Type         | Description                                                 |
|---------------------------|--------------|-------------------------------------------------------------|
| `account_id`              | bigint (FK)  | Unique per account                                          |
| `plan`                    | string       | `starter`, `pro`, or `enterprise`                           |
| `monthly_cost_limit_usd`  | decimal(10,4)| Base monthly cost cap in USD                                |
| `monthly_request_limit`   | integer      | Max requests per month (nil = unlimited)                    |
| `burst_rpm`               | integer      | Max requests per minute (sliding window)                    |
| `extra_budget_usd`        | decimal(10,4)| Temporary extra budget added by admin                       |
| `extra_budget_expires_at` | datetime     | When the extra budget expires                               |
| `enabled`                 | boolean      | If false, all LLM calls are blocked                         |
| `notify_at_percentage`    | integer      | Log warning when usage reaches this % (default: 80)         |
| `hard_limit`              | boolean      | If true, blocks calls when over limit. If false, just warns.|
| `metadata`                | jsonb        | Stores notification state, extra budget history             |

### `llm_quota_usages`

One row per account per month. Tracks accumulated usage.

| Column              | Type         | Description                                    |
|---------------------|--------------|------------------------------------------------|
| `account_id`        | bigint (FK)  | The account                                    |
| `period`            | string       | Format `YYYY-MM` (e.g., `2025-06`)            |
| `total_cost_usd`    | decimal(12,8)| Accumulated cost this month                    |
| `total_requests`    | integer      | Number of successful LLM calls                 |
| `total_tokens`      | bigint       | Tokens consumed this month                     |
| `cost_by_model`     | jsonb        | Cost breakdown by model name                   |
| `cost_by_operation` | jsonb        | Cost breakdown by operation type                |
| `last_synced_at`    | datetime     | Last time the hourly sync job reconciled data  |

Unique index on `[account_id, period]`. Each month automatically starts a new period — no "reset" action needed.

---

## Plans

Defined in `Llm::QuotaPlan`:

| Plan         | Monthly Cost Limit | Monthly Requests | Burst RPM |
|--------------|-------------------:|------------------:|----------:|
| `starter`    |             $5.00  |             5,000 |        20 |
| `pro`        |            $25.00  |            25,000 |        50 |
| `enterprise` |           $100.00  |           100,000 |       100 |

New accounts are automatically assigned the `starter` plan via an `after_create_commit` callback on `Account`.

---

## Rate Limiting Flow

When `GeminiClient.chat` or `GeminiClient.embeddings` is called:

1. **Before the call** — `enforce_rate_limit!` runs inside `Apartment::Tenant.switch("public")`:
   - Finds or auto-provisions the account's `LlmQuota` (defaults to starter)
   - Checks if quota is **enabled** (if not → blocked)
   - Checks **burst RPM** via Redis sorted set with 60s sliding window
   - Checks **monthly cost** against `effective_monthly_limit` (base + active extra budget)
   - Checks **monthly requests** against `monthly_request_limit`
   - If any check fails and `hard_limit` is true → raises `Llm::RateLimitExceeded`
   - If `hard_limit` is false → logs warning but allows the call

2. **After the call** — `record_quota_usage!` increments:
   - Redis burst counter (sorted set with TTL)
   - `LlmQuotaUsage` row via atomic SQL `UPDATE SET total_cost_usd = total_cost_usd + ?`
   - Checks if notification threshold was crossed

### Bypass Flag

Internal system jobs (embeddings, enrichment) can bypass rate limiting:

```ruby
GeminiClient.new.embeddings(
  input: texts,
  tracking: { bypass_rate_limit: true, operation: "system_embedding" }
)
```

---

## Extra Budget

Admins can grant temporary extra spending budget to an account:

```ruby
quota.grant_extra_budget!(
  amount: 10.00,
  expires_at: 30.days.from_now,
  reason: "Customer onboarding"
)
```

The effective monthly limit becomes `monthly_cost_limit_usd + active_extra_budget`. Extra budgets can have an expiration date and are automatically cleaned up by `Llm::ExpireExtraBudgetJob`.

---

## Scheduled Jobs

Configured in `config/schedule.yml` via `sidekiq-cron`:

| Job                           | Schedule        | Purpose                                          |
|-------------------------------|-----------------|--------------------------------------------------|
| `Llm::QuotaUsageSyncJob`     | Every hour      | Reconciles `LlmQuotaUsage` from `llm_usages`    |
| `Llm::MonthlyQuotaSetupJob`  | 1st of month    | Pre-creates usage records for the new period     |
| `Llm::ExpireExtraBudgetJob`  | Daily at 00:10  | Zeros out expired extra budgets                  |

---

## API Endpoints

### User Endpoints

**GET** `/v1/users/llm_quotas/current`

Returns the calling user's account quota, current usage, and summary.

Response:
```json
{
  "success": true,
  "data": {
    "quota": {
      "plan": "starter",
      "monthly_cost_limit_usd": 5.0,
      "effective_monthly_limit": 5.0,
      "enabled": true,
      "hard_limit": false
    },
    "usage": {
      "period": "2025-06",
      "total_cost_usd": 1.234567,
      "total_requests": 342,
      "total_tokens": 128000
    },
    "summary": {
      "usage_percentage": 24.69,
      "cost_remaining_usd": 3.765433,
      "requests_remaining": 4658,
      "resets_at": "2025-07-01T00:00:00Z",
      "over_limit": false
    }
  }
}
```

**PATCH** `/v1/users/llm_quotas/update_current` (admin only)

Update `notify_at_percentage` and `hard_limit` for own account.

```json
{ "llm_quota": { "notify_at_percentage": 90, "hard_limit": true } }
```

### Admin Endpoints

All require admin authentication.

| Method | Path                                    | Action                        |
|--------|-----------------------------------------|-------------------------------|
| GET    | `/v1/users/admin/llm_quotas`            | List all quotas (filterable)  |
| GET    | `/v1/users/admin/llm_quotas/:id`        | Show specific quota + usage   |
| PATCH  | `/v1/users/admin/llm_quotas/:id`        | Update plan/limits/enabled    |
| POST   | `/v1/users/admin/llm_quotas/:id/grant_extra`  | Grant extra budget     |
| POST   | `/v1/users/admin/llm_quotas/:id/reset_usage`  | Reset current month    |

**Grant Extra Budget:**
```json
{
  "extra_budget_usd": 10.00,
  "expires_at": "2025-07-15T00:00:00Z",
  "reason": "Customer demo period"
}
```

**Update Plan:**
```json
{
  "llm_quota": {
    "plan": "pro",
    "monthly_cost_limit_usd": 25.00,
    "monthly_request_limit": 25000,
    "burst_rpm": 50
  }
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `app/models/llm_quota.rb` | Quota model with plan, limits, extra budget logic |
| `app/models/llm_quota_usage.rb` | Monthly usage tracking with atomic increments |
| `app/services/llm/rate_limiter.rb` | Core rate limiting engine (checks + recording) |
| `app/services/llm/quota_plan.rb` | Plan definitions (starter/pro/enterprise) |
| `app/services/gemini_client.rb` | Integration point — enforces limits before calls |
| `app/jobs/llm/quota_usage_sync_job.rb` | Hourly reconciliation from `llm_usages` |
| `app/jobs/llm/monthly_quota_setup_job.rb` | Monthly pre-creation of usage records |
| `app/jobs/llm/expire_extra_budget_job.rb` | Daily cleanup of expired extra budgets |
| `app/controllers/v1/users/llm_quotas_controller.rb` | User-facing API |
| `app/controllers/v1/users/admin/llm_quotas_controller.rb` | Admin API |

---

## How to Test

### Run the Specs

```bash
docker compose exec web bundle exec rspec spec/models/llm_quota_spec.rb
docker compose exec web bundle exec rspec spec/models/llm_quota_usage_spec.rb
docker compose exec web bundle exec rspec spec/services/llm/rate_limiter_spec.rb
docker compose exec web bundle exec rspec spec/jobs/llm/
```

Run all quota-related specs at once:

```bash
docker compose exec web bundle exec rspec spec/models/llm_quota_spec.rb spec/models/llm_quota_usage_spec.rb spec/services/llm/rate_limiter_spec.rb spec/jobs/llm/
```

### Manual Testing via Rails Console

```ruby
# 1. Check an account's quota
account = Account.first
quota = account.llm_quota
quota.plan                    # => "starter"
quota.monthly_cost_limit_usd  # => 5.00
quota.usage_percentage        # => 12.5
quota.cost_remaining          # => 4.375

# 2. Check current usage
usage = LlmQuotaUsage.current_for(account.id)
usage.total_cost_usd   # => 0.625
usage.total_requests   # => 87
usage.period           # => "2025-06"

# 3. Test rate limiting
limiter = Llm::RateLimiter.new(account_id: account.id)
result = limiter.check
result.allowed?   # => true
result.usage      # => { limit_usd: 5.0, used_usd: 0.625, ... }

# 4. Upgrade an account to pro
quota.apply_plan!("pro")
quota.monthly_cost_limit_usd  # => 25.00

# 5. Grant extra budget
quota.grant_extra_budget!(amount: 10, expires_at: 30.days.from_now, reason: "test")
quota.effective_monthly_limit  # => 35.00

# 6. Simulate exceeding the limit
usage.update!(total_cost_usd: 30.0)
quota.update!(hard_limit: true)
limiter = Llm::RateLimiter.new(account_id: account.id)
limiter.check!  # => raises Llm::RateLimitExceeded

# 7. Run sync job manually
Llm::QuotaUsageSyncJob.new.perform
```

### Manual Testing via API (curl)

```bash
TOKEN="your-auth-token"

# Check current quota
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/v1/users/llm_quotas/current | jq

# (Admin) List all quotas
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/v1/users/admin/llm_quotas | jq

# (Admin) Grant extra budget
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"extra_budget_usd": 10, "reason": "testing"}' \
  http://localhost:3000/v1/users/admin/llm_quotas/1/grant_extra | jq

# (Admin) Reset usage
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/v1/users/admin/llm_quotas/1/reset_usage | jq
```

### Testing the Burst Limiter (Redis)

```ruby
account = Account.first
limiter = Llm::RateLimiter.new(account_id: account.id)

# Fire requests rapidly
25.times { limiter.record_usage!(cost: 0.001, tokens: 100) }

result = limiter.check
result.allowed?  # => false (starter plan has 20 RPM)
result.reason    # => "burst_rpm_exceeded"

# Wait 60 seconds, then try again
sleep 61
limiter.check.allowed?  # => true
```

---

## How Monthly Renewal Works

There is no explicit "reset" operation. Each month is identified by a `period` string (`YYYY-MM`). When `LlmQuotaUsage.current_for(account_id)` is called and no record exists for the current month, a new zeroed-out row is created via `find_or_create_by`. This means usage automatically resets at the start of each month without any manual intervention.

The `Llm::MonthlyQuotaSetupJob` (runs on the 1st of each month) pre-creates these records to avoid race conditions during the first minutes of the new month.

---

## Soft vs Hard Limits

- **Soft limit** (`hard_limit: false`, default): When the account exceeds its monthly cost limit, the system logs a warning but **allows the call to proceed**. This prevents disruption to end users while giving operators visibility.

- **Hard limit** (`hard_limit: true`): When exceeded, the system raises `Llm::RateLimitExceeded` and the LLM call is **blocked**. The exception includes `limit_type` and `details` so the caller can show a meaningful error to the user.

Admins can toggle this per account via the API or console.
