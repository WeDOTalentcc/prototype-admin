# RLS Multi-Tenant Contract

## Overview

Row Level Security (RLS) is enforced at the PostgreSQL level for tenant isolation.
Any client connecting to the database (Python/FastAPI, Ruby on Rails, etc.) gets
automatic data isolation when following this contract.

## How It Works

1. **Function**: `app_current_company_id()` returns the current session's company_id as TEXT
2. **Policies**: Every protected table has 4 policies (SELECT, INSERT, UPDATE, DELETE)
   that enforce `company_id = app_current_company_id()`
3. **Deny-by-default**: If no company_id is set in the session, zero rows are visible
4. **Role**: The `lia_app` role (non-superuser) ensures RLS cannot be bypassed

## Client Integration Contract

Every database client MUST do two things per request:

```sql
-- 1. Drop to non-superuser role (RLS only applies to non-superusers)
SET ROLE lia_app;

-- 2. Set the tenant context for this session
SELECT set_config('app.company_id', '<company_id>', true);
```

The third parameter `true` means the setting is local to the current transaction.

After the request completes:

```sql
RESET ROLE;
```

## Python/FastAPI Implementation

Already implemented in `libs/config/lia_config/database.py`:

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            # Always RESET ROLE first — pooled connections may retain
            # SET ROLE lia_app from a previous authenticated request.
            await session.execute(sa.text("RESET ROLE"))

            _cid = _get_current_company_id()  # from ContextVar
            if _cid:
                await session.execute(sa.text("SET ROLE lia_app"))
                await session.execute(
                    sa.text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": _cid},
                )
            # No company_id → unauthenticated route (login, register, etc.)
            # Uses postgres superuser which bypasses RLS — safe because
            # AuthEnforcementMiddleware controls which routes are public.
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.execute(sa.text("RESET ROLE"))
            await session.close()
```

**Connection pool safety**: The `RESET ROLE` at the top of `get_db()` is critical.
Without it, a pooled connection that previously ran `SET ROLE lia_app` would still
be in that role when reused by an unauthenticated request (e.g., login), causing
RLS deny-by-default to block the query and return "Invalid email or password".

## Rails Integration (ats-api)

Add to `config/initializers/rls.rb` or equivalent:

```ruby
# config/initializers/rls.rb
ActiveSupport.on_load(:active_record) do
  ActiveRecord::ConnectionAdapters::PostgreSQLAdapter.set_callback :checkout, :after do
    # lia_app role is created by migration 068
    execute("SET ROLE lia_app")
  end

  ActiveRecord::ConnectionAdapters::PostgreSQLAdapter.set_callback :checkin, :before do
    execute("RESET ROLE")
  end
end
```

And in ApplicationController:

```ruby
class ApplicationController < ActionController::API
  before_action :set_tenant_context

  private

  def set_tenant_context
    company_id = current_user&.company_id
    if company_id.present?
      ActiveRecord::Base.connection.execute(
        ActiveRecord::Base.sanitize_sql_array([
          "SELECT set_config('app.company_id', ?, true)", company_id.to_s
        ])
      )
    end
  end
end
```

## Protected Tables

### VARCHAR company_id (107 tables) - RLS ACTIVE

All tables with `company_id VARCHAR` have RLS enabled and enforced.
Key tables: `job_vacancies`, `vacancy_candidates`, `audit_logs`, `users`,
`candidate_stage_history`, `communication_history`, `lia_opinions`,
`interviews`, `company_modules`, `credit_accounts`.

### UUID company_id (88 tables) - RLS NOT YET ACTIVE

Tables with `company_id UUID` are not yet protected by RLS.
These tables use a different type and need alignment before policies can be applied.

### Tables WITHOUT company_id - NOT PROTECTED

Critical tables that lack `company_id` entirely:
- `candidates` (314 rows) - linked via `vacancy_candidates`
- `conversations` (278 rows) - no tenant column
- `messages` - no tenant column
- `wsi_sessions` - no tenant column
- `notifications` - no tenant column
- `pipeline_stages` - no tenant column

These tables need `company_id` columns added before RLS can protect them.

## GCP Cloud Run Deployment Notes

- Cloud SQL creates non-superuser roles by default — RLS works automatically
- The `lia_app` role should be created in Cloud SQL via the migration
- Ensure the application connects with a non-superuser database user
- The `postgres` superuser bypasses all RLS (use only for migrations/admin)

## company_id Format

- Type: `VARCHAR(255)` (TEXT comparison in policies)
- Current dev value: `'demo_company'`
- Production: Use any string identifier (UUID strings work in VARCHAR)
- The function casts to TEXT, so both VARCHAR and UUID-as-string work

## Rollback

If RLS causes issues, run:

```sql
-- Revert via Alembic
alembic downgrade 067
```

Or manually:

```sql
-- For a specific table
DROP POLICY IF EXISTS <table>_tenant_select ON <table>;
DROP POLICY IF EXISTS <table>_tenant_insert ON <table>;
DROP POLICY IF EXISTS <table>_tenant_update ON <table>;
DROP POLICY IF EXISTS <table>_tenant_delete ON <table>;
ALTER TABLE <table> DISABLE ROW LEVEL SECURITY;
```

## Migration History

- `040_add_rls_multi_tenant.py` - Original attempt (never executed, had IS NULL OR bug)
- `068_rls_deny_by_default.py` - Current implementation (deny-by-default, TEXT-based)
