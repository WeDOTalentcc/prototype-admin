# Code Review — All Uncommitted Changes

**Date:** 2026-04-08  
**Scope:** 29 modified + 14 untracked files across controllers, models, services, serializers, jobs, migrations

---

## Summary

Changes span 6 feature areas: entity pages, background agents (semantic search, feedback sync, dedup), candidate match by text, LinkedIn search service refactor, token refresh, and search renderer improvements. Overall quality is solid — early returns, service extraction, proper tenant handling. Below are the findings.

---

## 🔴 Critical

### 1. Token Refresh — Grace Period Accepts Expired Tokens for 10 Minutes

**File:** `app/controllers/v1/agent_tokens_controller.rb` (lines 93-103)  
**Issue:** `decode_expired_token` accepts tokens up to 10 minutes past expiration. Combined with the `refresh` endpoint, an attacker with a stolen expired token gets a fresh 30-minute token. This extends the effective compromise window to 40 minutes.

```ruby
expired_at = Time.at(payload[:exp].to_i)
grace_period = 10.minutes
return nil if expired_at < grace_period.ago
```

**Risk:** Token replay / session extension after compromise.  
**Fix:** Reduce grace period to 60-120 seconds (enough for clock skew + network latency). Consider a one-time-use claim (jti) tracked in Redis to prevent replay.

---

### 2. `semantic_search` Leaks Internal Error Messages to Client

**File:** `app/controllers/v1/users/background_agents_controller.rb` (line ~315)

```ruby
rescue StandardError => e
  Rails.logger.error(...)
  render json: { success: false, error: e.message }, status: :internal_server_error
end
```

**Risk:** `e.message` can contain stack traces, DB connection strings, or internal details (information disclosure — OWASP A01).  
**Fix:** Return a generic error message to the client; log the full error server-side.

```ruby
render json: { success: false, error: "Semantic search failed" }, status: :internal_server_error
```

---

### 3. `CandidateMatchSerializer` Exposes PII Fields

**File:** `app/serializer/candidate_match_serializer.rb`  
**Issue:** Serializer exposes `cpf`, `current_salary`, `clt_expectation`, `pj_expectation`, `freelance_expectation`, `date_birth`, `marital_status`, `street`, `number`, `district`, `zip`, `complement`. The copilot-instructions explicitly say: *"Never include sensitive data (tokens, passwords, CPF, salary in list views)"*.

**Risk:** LGPD violation / PII leakage in a search results endpoint.  
**Fix:** Remove sensitive fields. If needed, expose them only via a detailed `show` action with proper authorization.

---

### 4. `CandidateMatchSerializer` — Potential N+1 on `applies`

**File:** `app/serializer/candidate_match_serializer.rb` (line ~133)

```ruby
attribute :applies, if: proc { ... } do |object, _params|
  object.applies.where(is_deleted: [false, nil]).map do |apply|
    { ... job_title: apply.job&.title ... }
  end
end
```

**Issue:** Each candidate's `applies` triggers a query, and each `apply.job&.title` triggers another. For 20 results, that's 20 + 20 = 40 N+1 queries.  
**Fix:** Add `includes(:applies => :job)` in the service or use `preload` before serialization.

---

## 🟡 Medium

### 5. `find_existing_external_profile` / `find_existing_local_by_identity` — SQL Injection Safe but Fragile Name Matching

**File:** `app/services/background_agents/deliver_candidates_service.rb` (lines ~184, 197-230)

```ruby
by_identity = SourcedProfile.where(account_id: ..., is_deleted: false).where(
  "LOWER(name) = ? AND LOWER(current_company) = ? AND LOWER(role_name) = ?",
  data[:name].to_s.downcase,
  data[:company].to_s.downcase,
  data[:title].to_s.downcase
).first
```

**Issues:**
- Uses parameterized queries — no SQL injection. Good.
- But matching by `LOWER(name) + company + title` is very collision-prone. "Maria Silva" at "Google" as "Engineer" could match many different people.
- No DB index on `(account_id, LOWER(name), LOWER(current_company), LOWER(role_name))` — full seq scan.

**Fix:** Consider adding a composite functional index if this path is hit frequently. Evaluate if this matching heuristic is acceptable for the business (false positives vs false negatives).

---

### 6. `Apartment::Tenant.switch!` vs `switch` Inconsistency

**File:** `app/jobs/background_agents/setup_job.rb`

```ruby
- Apartment::Tenant.switch!(account.tenant) do
+ Apartment::Tenant.switch(account.tenant) do
```

**Issue:** Changed from `switch!` (raises on unknown tenant) to `switch` (silently returns nil on failure). Per the project's own instructions, jobs should use `switch!` for explicitness. If the tenant is invalid, the job should fail loudly, not silently skip.

**Fix:** Revert to `switch!` or at least `switch` with explicit tenant validation.

---

### 7. OTT TTL Changed from 600s to 30 Minutes Without Documentation

**File:** `app/lib/json_web_token.rb`

```ruby
- def self.encode_ott(account_id:, user_id:, exp: 600.seconds.from_now)
+ def self.encode_ott(account_id:, user_id:, exp: 30.minutes.from_now)
```

**Issue:** One-Time Tokens should have short lifetimes by design. Increasing from 10 minutes to 30 minutes significantly expands the attack window if an OTT is intercepted.

**Fix:** Verify this change is intentional and necessary. If agents need longer bootstrap windows, consider a different mechanism (the refresh endpoint already exists).

---

### 8. `sourced_profile_sourcings_controller` — Default `per_page` Jumped to 200

**File:** `app/controllers/v1/users/sourced_profile_sourcings_controller.rb`

```ruby
- return 30 if value <= 0
- [value, 100].min
+ return 200 if value <= 0
+ [value, 200].min
```

**Issue:** The project instructions say *"Pagination (`page`, `per_page` max 30)"*. Default 200 per page can cause significant memory and response time issues, especially with joins/preloading.

**Fix:** If higher pagination is needed for specific cases, make it opt-in with a clear max. Consider if the frontend actually needs 200 items or if infinite scroll / cursor pagination would work better.

---

### 9. `EntityPage.upsert_page` — Infinite Retry on `RecordNotUnique`

**File:** `app/models/entity_page.rb` (line 49)

```ruby
rescue ActiveRecord::RecordNotUnique
  retry
end
```

**Issue:** If there's a persistent uniqueness conflict (e.g., a bug in the `find_by` criteria not matching the unique index columns), this retries forever. Should have a max retry count.

**Fix:**

```ruby
rescue ActiveRecord::RecordNotUnique => e
  retries ||= 0
  retries += 1
  retry if retries < 3
  raise
end
```

---

### 10. `EntityPage` Unique Index with Nullable Columns

**File:** `db/migrate/20260408120000_add_unique_index_to_entity_pages.rb`

```ruby
add_index :entity_pages,
  %i[user_id entity type_view link custom_entity],
  unique: true
```

**Issue:** PostgreSQL treats `NULL != NULL` in unique indexes. If `link` or `custom_entity` are often NULL, the unique index won't prevent duplicates. The model-level `validates :entity, uniqueness:` will catch it, but there's a race condition window.

**Fix:** Add a partial unique index for the NULL case, or use `COALESCE` in a unique expression index:

```sql
CREATE UNIQUE INDEX idx_entity_pages_unique_per_user
  ON entity_pages (user_id, entity, type_view, COALESCE(link, ''), COALESCE(custom_entity, ''));
```

---

### 11. `search_params.rb` — `merge_boost_where` Still Trusts JSON from Params

**File:** `app/controllers/concerns/search_params.rb`

```ruby
boost = params[:boost_where]
boost = JSON.parse(boost) if boost.is_a?(String)
params_new[:boost_where].merge!(boost) if boost.is_a?(Hash)
```

**Issue:** `JSON.parse` of user-supplied string can produce deeply nested or very large structures. Also, if `boost_where` is already a Hash from ActionController params, it bypasses JSON parsing — which is fine — but `merge!` directly into `boost_where` allows arbitrary Elasticsearch boost clauses from the client.

**Fix:** Validate or whitelist the keys/structure allowed in `boost_where`. At minimum, add a size check on the raw string before parsing.

---

### 12. `AddUniqueIndexToSourcedProfileSourcings` — Data-Mutating Migration

**File:** `db/migrate/20260407162000_add_unique_index_to_sourced_profile_sourcings.rb`

```ruby
def up
  execute <<~SQL
    DELETE FROM sourced_profile_sourcings
    WHERE id NOT IN (
      SELECT MIN(id) FROM sourced_profile_sourcings
      GROUP BY sourced_profile_id, sourcing_id
    )
  SQL
  add_index ...
end
```

**Issue:** This silently deletes duplicate records in production across ALL tenant schemas (Apartment runs migrations in each schema). The `DELETE` subquery can be slow on large tables (correlated NOT IN). No logging of how many records are deleted.

**Fix:** 
- Add `RAISE NOTICE` or a Ruby `say` statement to log deleted row count per schema.
- Consider using `DELETE ... USING` or a CTE for better performance on large tables.
- Ensure this has been tested on a staging environment.

---

## 🟢 Low / Improvements

### 13. `background_agent.rb` — `sync_sources_from_config` Callback

**File:** `app/models/background_agent.rb`

```ruby
before_save :sync_sources_from_config

def sync_sources_from_config
  return unless search_iteration_config_changed?
  providers = search_iteration_config&.dig("enabled_providers")
  self.sources = providers if providers.present?
end
```

**Observation:** Per project instructions, *"Callbacks: use sparingly, prefer services for side effects"*. This callback is simple enough to stay in the model, but note that `search_iteration_config_changed?` only works for Active Record dirty tracking — if you update JSONB keys directly via `update_column` or raw SQL, this won't fire.

---

### 14. `agent_feedbacks_controller` — Aliasing `agent_candidate_id` → `sourced_profile_sourcing_id`

**File:** `app/controllers/v1/users/agent_feedbacks_controller.rb`

```ruby
data["sourced_profile_sourcing_id"] ||= data.delete("agent_candidate_id")
data["action"] ||= data.delete("status")
```

**Observation:** This is API compatibility aliasing. Fine for now, but should be documented as deprecated. Consider adding a deprecation header or logging so the frontend can migrate.

---

### 15. `linkedin_search_service.rb` — Removed `require_relative` Lines

```ruby
- require_relative "linkedin_search/query"
- require_relative "linkedin_search/query_builder"
- ...
```

**Observation:** Files moved from `linkedin_search/` to `linkedin_search_service/`. The `require_relative` removal relies on Rails autoloading. Verify that `Apify::LinkedinSearchService::Query` is properly autoloaded from the new path (folder must match class nesting).

---

### 16. `candidate_for_text.rb` — Painless Script in Search Params

**File:** `app/services/matching/candidate_for_text.rb`

```ruby
source: <<~PAINLESS.strip,
  int i = params.ids.indexOf(doc['id'].value.toString());
  return i == -1 ? params.ids.size() + 1 : i;
PAINLESS
```

**Observation:** The Painless script uses `params.ids` from the Ruby-side `paginated_ids.map(&:to_s)`, which is safe (not user-injected). The `@text` input goes only to `Embeddings::Encoder`, not to Elasticsearch directly. No injection risk here.

---

### 17. `search_renderer.rb` — Skills Preloading Improvement

```ruby
ActiveRecord::Associations::Preloader.new(records: records, associations: :skills).call if include_skills
```

**Observation:** Good N+1 prevention. However, `records.first&.respond_to?(:skills)` may not be reliable if `records` is empty or if the model doesn't have `skills` associated. Consider using a safer check like the model class.

---

## Summary Table

| # | Severity | Category | File | Issue |
|---|----------|----------|------|-------|
| 1 | 🔴 | Security | `agent_tokens_controller.rb` | 10-min grace on expired tokens = replay risk |
| 2 | 🔴 | Security | `background_agents_controller.rb` | `e.message` leaks internal errors to client |
| 3 | 🔴 | LGPD | `candidate_match_serializer.rb` | Exposes CPF, salary, personal address |
| 4 | 🔴 | Performance | `candidate_match_serializer.rb` | N+1 on applies + job title |
| 5 | 🟡 | Data | `deliver_candidates_service.rb` | Name-based dedup is collision-prone, no index |
| 6 | 🟡 | Convention | `setup_job.rb` | Changed `switch!` to `switch` silently |
| 7 | 🟡 | Security | `json_web_token.rb` | OTT TTL 10min → 30min widens attack window |
| 8 | 🟡 | Performance | `sourced_profile_sourcings_controller.rb` | Default per_page 200, breaks project max 30 |
| 9 | 🟡 | Reliability | `entity_page.rb` | Infinite retry on RecordNotUnique |
| 10 | 🟡 | Data | `entity_pages` migration | Unique index with NULLs doesn't prevent dupes |
| 11 | 🟡 | Security | `search_params.rb` | Unvalidated boost_where from params |
| 12 | 🟡 | Data | `sourced_profile_sourcings` migration | Silent bulk delete of duplicates in production |
| 13 | 🟢 | Convention | `background_agent.rb` | Callback vs service preference |
| 14 | 🟢 | API | `agent_feedbacks_controller.rb` | Undocumented param aliasing |
| 15 | 🟢 | Autoload | `linkedin_search_service.rb` | Verify autoloading after file move |
| 16 | 🟢 | Security | `candidate_for_text.rb` | Painless script — safe, no injection |
| 17 | 🟢 | Performance | `search_renderer.rb` | Good N+1 fix, minor edge case on empty records |
