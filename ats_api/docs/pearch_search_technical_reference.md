# Pearch Global Search — Technical Reference

## Overview

Pearch is a global talent search API providing access to ~500M+ candidate profiles worldwide. The WeDO Talent ATS integrates Pearch as the engine for "global sourcing" — finding candidates beyond the internal Elasticsearch/pgvector database.

**API Endpoint:** `https://api.pearch.ai/v2/search`
**Auth:** Bearer token via `PEARCH_API_KEY` env var
**HTTP Client:** `Net::HTTP` with 180s timeout
**Billing:** Credit-based — each search deducts credits from `Account.pearch_credits`

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│ FRONTEND (Vue/Nuxt)                                                     │
│  POST /v1/users/talent_searches { query, sources:["global"], async:true }│
│  POST /v1/users/sourcings/search_profiles { archetype_id, profile }     │
│  POST /v1/users/sourcings/:id/load_more                                 │
│  GET  /v1/users/talent_searches/credits                                 │
│  GET  /v1/users/talent_searches/transactions                            │
│  GET  /v1/users/talent_searches/search_profiles                         │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TalentSearchesController / SourcingsController                          │
│  → parse_sources → check_credits → create Sourcing(status: processing)  │
│  → SYNC: executes search inline and returns results                     │
│  → ASYNC (async=true): enqueues TalentSearchJob, returns 202 Accepted   │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
┌─────────────────────┐  ┌─────────────────────────────────┐
│ Sidekiq              │  │ Inline (sync mode)               │
│ TalentSearchJob      │  │ TalentSearchExecutorService.call │
│ queue: sourcing_search│  └──────────────┬──────────────────┘
│ retry: 2             │                  │
└──────────┬───────────┘                  │
           │                              │
           ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TalentSearchExecutorService                                             │
│  1. QueryParserService.call(query)  → LLM (Gemini) translates PT→EN    │
│     + extracts structured filters                                       │
│  2. SearchProfilesBuilder.build(params) → builds API options            │
│  3. merge_account_config!(options) → applies per-account defaults       │
│  4. merge_custom_filters!(options, parsed) → merges LLM filters         │
│  5. SearchService.search(query, **options) → HTTP call to Pearch        │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Pearch::SearchService                                                    │
│  1. validate_credits!(options) → checks Account.pearch_credits           │
│  2. build_params(query, options) → constructs API payload                │
│  3. make_request(params) → NET::HTTP POST to api.pearch.ai/v2/search    │
│  4. parse_response(response)                                             │
│  5. log_search_and_consume_credits(result, params):                      │
│     a. Creates PearchSearchLog                                           │
│     b. Consumes credits via CreditsService                               │
│     c. Creates PearchCreditTransaction                                   │
│     d. Updates Sourcing record                                           │
│     e. Enqueues ProcessSourcingJob                                       │
│     f. Broadcasts via SourcingChannel                                    │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ ProcessSourcingJob (queue: sourcing_search, retry: 3)                    │
│  1. Caches full search_results in Redis (30min TTL)                      │
│  2. Processes first 15 profiles (PAGE_SIZE):                             │
│     a. ProfileMatchingService → dedup by email/phone/cpf/linkedin        │
│     b. Creates SourcedProfile records                                    │
│     c. Broadcasts profile_processed per profile                          │
│  3. Broadcasts profiles_processing_completed                             │
│  4. Pagination via load_more reads from Redis cache                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `app/services/pearch/search_service.rb` | HTTP client — builds request, calls API, logs, consumes credits |
| `app/services/pearch/credits_service.rb` | Credit management — add, consume, balance, history, statistics |
| `app/services/pearch/talent_search_executor_service.rb` | Orchestrator — parses query (LLM), builds options, delegates to SearchService |
| `app/services/pearch/query_parser_service.rb` | LLM-based PT→EN query translator via Gemini |
| `app/services/pearch/search_profiles_builder.rb` | Converts internal filter params to Pearch API format |
| `app/services/pearch/search_profiles.rb` | Pre-configured search profile definitions (fast/balanced/premium) |
| `app/services/pearch/contact_enrichment_service.rb` | Email/phone enrichment for individual SourcedProfiles |
| `app/services/search_archetypes/to_pearch_params_service.rb` | Converts SearchArchetype records to Pearch params |
| `app/jobs/pearch/talent_search_job.rb` | Sidekiq job (queue: sourcing_search) — async search execution |
| `app/jobs/process_sourcing_job.rb` | Processes Pearch results → creates SourcedProfile records |
| `app/controllers/v1/users/talent_searches_controller.rb` | API endpoints for search, credits, profiles, transactions |
| `app/models/pearch_search_log.rb` | Audit trail for every Pearch search |
| `app/models/pearch_credit_transaction.rb` | Audit trail for credit changes |

---

## API Endpoints

### `POST /v1/users/talent_searches`

Main search endpoint. Supports sync and async modes.

**Request:**
```json
{
  "query": "desenvolvedor ruby senior são paulo",
  "sources": ["global"],
  "async": true,
  "limit": 30,
  "type": "fast",
  "reveal_emails": true,
  "reveal_phones": false,
  "custom_filters": {
    "locations": ["São Paulo, Brazil"],
    "titles": ["Software Engineer", "Backend Developer"]
  }
}
```

**Sync Response (200):**
```json
{
  "success": true,
  "data": {
    "search_results": [...],
    "uuid": "abc-123",
    "thread_id": "thread-456",
    "duration": 12.5,
    "total_estimate": 500,
    "credits_used": 45,
    "sourcing_id": 789,
    "query_metadata": {
      "original_query": "desenvolvedor ruby senior são paulo",
      "parsed_query": "Senior Ruby Developer",
      "custom_filters_applied": { "locations": ["São Paulo"] },
      "confidence": 0.95
    }
  }
}
```

**Async Response (202):**
```json
{
  "sourcing_id": 789,
  "uid": "abc-123-def",
  "status": "processing",
  "message": "Search enqueued. Subscribe to sourcing_789 channel for updates."
}
```

### `GET /v1/users/talent_searches/credits`

Returns credit statistics for the account.

**Query params:** `start_date`, `end_date` (optional)

**Response:**
```json
{
  "current_balance": 500,
  "total_consumed": 1200,
  "credits_added": 2000,
  "credits_consumed": 1500,
  "search_stats": {
    "total_searches": 45,
    "successful": 42,
    "failed": 3,
    "total_credits_used": 1200,
    "total_results_returned": 1050,
    "average_duration": 8.5
  }
}
```

### `GET /v1/users/talent_searches/search_profiles`

Returns available search profile presets.

### `GET /v1/users/talent_searches/transactions`

Returns credit transaction history.

### `POST /v1/users/sourcings/:id/load_more`

Loads next page of results from Redis cache. Each page has 15 profiles (PAGE_SIZE).

---

## Search Profiles (Presets)

| Profile | Type | Insights | Scoring | Freshness | Default Limit | Cost/Result |
|---------|------|----------|---------|-----------|---------------|-------------|
| **fast** | fast | No | No | No | 10 | 1 credit |
| **balanced** (recommended) | fast | Yes | Yes | No | 30 | 3 credits |
| **premium** | pro | Yes | No | No | 10 | 7 credits |

---

## Credit Cost Calculation

```
base_cost = limit × (type == "fast" ? 1 : 5)

Add-ons (per result):
  + insights         → +1
  + profile_scoring   → +1
  + high_freshness    → +2
  + reveal_emails     → +2
  + reveal_phones     → +14
  + require_emails    → +1
  + require_phones    → +1
  + require_phones_or_emails → +1
```

**Examples:**
- 10 results, fast, no extras = 10 credits
- 30 results, fast, insights+scoring = 30 + 30 + 30 = 90 credits
- 30 results, fast, insights+scoring+emails = 90 + 60 = 150 credits
- 30 results, fast, emails+phones = 30 + 60 + 420 = 510 credits

---

## Query Parsing (LLM)

`Pearch::QueryParserService` uses Gemini to:

1. Translate Portuguese → English
2. Extract structured filters (locations, titles, companies, etc.)
3. Return confidence score

**Example:**
- Input: `"desenvolvedor ruby senior são paulo fintech"`
- Output: `{ query: "Senior Ruby Developer", custom_filters: { locations: ["São Paulo, Brazil"], keywords: ["fintech"] }, confidence: 0.92 }`

Tracked as `operation: "pearch.query_parsing"` in `LlmUsage`.

---

## Custom Filters (Pearch API)

The `SearchProfilesBuilder` converts internal params to Pearch custom_filters:

| Internal Param | Pearch Filter | Notes |
|----------------|---------------|-------|
| `current_job_titles` | `filters[:titles]` | Array of job title strings |
| `companies` | `filters[:companies]` | Current company names |
| `excluded_companies` | `filters[:excluded_companies]` | Blacklisted companies |
| `company_sectors` | `filters[:industries]` | Industry IDs |
| `universities` | `filters[:universities]` | School names |
| `study_areas` | `filters[:keywords]` | Added to keywords |
| `academic_degree` | `filters[:degrees]` | bachelor/master/postdoc/doctor |
| `skills` | `filters[:keywords]` | Added to keywords |
| `languages` | `filters[:languages]` | Language names |
| `has_email` | `filter_out_no_emails: true` | Require email |
| `has_phone` | `filter_out_no_phones: true` | Require phone |
| `reveal_emails` | `reveal_emails: true` | Include emails in results |
| `reveal_phones` | `reveal_phones: true` | Include phones in results |

**Default location:** If no location is specified, "Brasil" is automatically added.

---

## INPUT: Complete Parameter Reference

### Top-Level API Parameters

These are passed directly to `Pearch::SearchService.search(query:, **options)`:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | String | required | Free-text search query (in English — auto-translated by LLM) |
| `type` | String | "fast" | Search type: "fast" (1 credit/result) or "pro" (5 credits/result) |
| `limit` | Integer | 30 | Max results (clamped 30-150) |
| `offset` | Integer | 0 | Result offset for pagination |
| `insights` | Boolean | false | Include profile insights (+1 credit/result) |
| `profile_scoring` | Boolean | false | Include relevance score (+1 credit/result) |
| `high_freshness` | Boolean | false | Prioritize recent data (+2 credits/result) |
| `strict_filters` | Boolean | false | Enforce strict filter matching |
| `reveal_emails` | Boolean | false | Reveal email addresses (+2 credits/result) |
| `reveal_phones` | Boolean | false | Reveal phone numbers (+14 credits/result) |
| `filter_out_no_emails` | Boolean | false | Only return profiles with emails (+1 credit/result) |
| `filter_out_no_phones` | Boolean | false | Only return profiles with phones (+1 credit/result) |
| `filter_out_no_phones_or_emails` | Boolean | false | Require phone or email (+1 credit/result) |
| `thread_id` | String | nil | Reuse thread for pagination (no extra cost) |
| `docid_blacklist` | Array\<String> | nil | Exclude specific docids from results |
| `docid_whitelist` | Array\<String> | nil | Only return specific docids |

### custom_filters Object

Passed inside options as `custom_filters: { ... }`:

| Filter Key | Type | Description |
|---|---|---|
| `locations` | Array\<String> | Geographic locations (e.g. ["São Paulo, Brazil"]) |
| `titles` | Array\<String> | Job title filter (e.g. ["Software Engineer", "Backend Developer"]) |
| `companies` | Array\<String> | Current company names |
| `excluded_companies` | Array\<String> | Companies to exclude |
| `industries` | Array\<String> | Industry/sector names |
| `universities` | Array\<String> | University/school names |
| `degrees` | Array\<String> | Academic degree: "bachelor", "master", "postdoc", "doctor" |
| `keywords` | Array\<String> | Additional keywords (skills, study areas merged here) |
| `languages` | Array\<String> | Spoken languages |

### Search Profiles (Presets)

| Preset | `type` | `insights` | `scoring` | `freshness` | Default Limit | Cost/Result |
|--------|--------|------------|-----------|-------------|---------------|-------------|
| `fast` | fast | false | false | false | 10 | 1 credit |
| `balanced` | fast | false | false | false | 30 | 1 credit |
| `premium` | pro | true | false | false | 10 | 7 credits |

### Credit Cost Formula

```
base_cost = limit × (type == "fast" ? 1 : 5)

Add-ons (per result):
  + insights           → +1
  + profile_scoring     → +1
  + high_freshness      → +2
  + reveal_emails       → +2
  + reveal_phones       → +14
  + require_emails      → +1
  + require_phones      → +1
  + require_phones_or_emails → +1
```

**Examples:**
- 10 results, fast, no extras = 10 credits
- 30 results, fast, insights+scoring = 30 + 30 + 30 = 90 credits
- 30 results, fast, emails+phones = 30 + 60 + 420 = 510 credits

---

## How to Consume: Input Examples

### Basic Search (sync)

```ruby
result = Pearch::SearchService.new(account, user).search(
  query: "Senior Ruby Developer",
  type: "fast",
  limit: 30,
  reveal_emails: true,
  custom_filters: {
    locations: ["São Paulo, Brazil"],
    titles: ["Software Engineer", "Backend Developer"]
  }
)
```

### Via TalentSearchExecutorService (recommended)

```ruby
executor = Pearch::TalentSearchExecutorService.new(
  user: user,
  sourcing: sourcing,
  params: {
    query: "desenvolvedor ruby senior são paulo",
    search_profile: "balanced",
    show_emails: true,
    current_job_titles: ["Software Engineer"],
    companies: ["iFood", "Nubank"],
    excluded_companies: ["Competitor Corp"],
    skills: ["Ruby", "Rails", "PostgreSQL"],
    languages: ["Portuguese", "English"],
    academic_degree: ["bachelor", "master"],
    universities: ["USP", "Unicamp"],
    has_email: true,
    limit: 30
  }
)

result = executor.call
```

### Via SearchProfilesBuilder (manual control)

```ruby
builder = Pearch::SearchProfilesBuilder.new(
  search_profile: "balanced",
  current_job_titles: ["Data Engineer"],
  companies: ["Google", "Meta"],
  company_sectors: ["Technology"],
  skills: ["Python", "Spark", "AWS"],
  languages: ["English"],
  show_emails: true,
  show_phone_numbers: false,
  has_email: true,
  limit: 50
)

options = builder.build
result = Pearch::SearchService.new(account, user).search(query: "Data Engineer", **options)
```

### Async via Sidekiq Job

```ruby
sourcing = account.sourcings.create!(
  user: user,
  uid: SecureRandom.uuid,
  provider: "pearch",
  query: "Backend Developer",
  status: "processing",
  searched_at: Time.current
)

Pearch::TalentSearchJob.perform_async(
  account.id, user.id, sourcing.id,
  {
    query: "Backend Developer",
    search_profile: "balanced",
    show_emails: true,
    limit: 30,
    custom_filters: { locations: ["Brazil"], titles: ["Backend Developer"] }
  }.to_json
)
```

### Pagination with thread_id

```ruby
first_result = Pearch::SearchService.new(account, user).search(
  query: "Ruby Developer",
  type: "fast",
  limit: 30,
  offset: 0
)

thread_id = first_result[:thread_id]

second_page = Pearch::SearchService.new(account, user).search(
  query: "Ruby Developer",
  type: "fast",
  limit: 30,
  offset: 30,
  thread_id: thread_id
)
```

### Using Search Archetypes

```ruby
archetype = SearchArchetype.find(id)

params = SearchArchetypes::ToPearchParamsService.call(
  archetype: archetype,
  profile: "balanced",
  additional_options: { reveal_emails: true }
)

result = Pearch::SearchService.new(account, user).search(**params)
```

### Contact Enrichment

```ruby
Pearch::ContactEnrichmentService.new(
  sourced_profile: profile,
  account: account,
  user: user
).enrich!
```

---

## OUTPUT: API Response Structure

### Top-Level Response

```ruby
result = Pearch::SearchService.new(account, user).search(query: "...", **options)

result[:search_results]               # Array — profile results
result[:uuid]                         # String — search UUID
result[:thread_id]                    # String — reusable for pagination
result[:total_estimate]               # Integer — estimated total matches
result[:total_estimate_is_lower_bound] # Boolean
result[:credits_remaining]            # Integer — credits left after search
result[:duration]                     # Float — seconds
result[:status]                       # String — "success" or error
result[:sourcing_id]                  # Integer — if sourcing record attached
```

### Profile Result Object (inside search_results)

Each element in `search_results` is a hash representing a candidate. Key fields:

```ruby
result = search_result_item

result[:docid]                        # String — unique document ID
result[:score]                        # Float — relevance score (if profile_scoring enabled)

profile = result[:profile]            # Hash — candidate data

profile[:name]                        # "João Silva"
profile[:first_name]                  # "João"
profile[:middle_name]                 # "Carlos"
profile[:last_name]                   # "Silva"
profile[:title]                       # "Senior Software Engineer"
profile[:role_name]                   # "Software Engineer"
profile[:summary]                     # About/bio text
profile[:picture_url]                 # Profile picture URL
profile[:estimated_age]               # Integer or nil
profile[:location]                    # "São Paulo, SP, Brazil"
profile[:city]                        # "São Paulo"
profile[:state]                       # "SP"
profile[:country]                     # "Brazil"
profile[:linkedin_url]                # "https://linkedin.com/in/joao-silva"
profile[:linkedin_slug]               # "joao-silva"
profile[:cpf]                         # CPF (LGPD sensitive!)
profile[:date_birth]                  # Date of birth
profile[:remote_work]                 # String: "yes"/"no"/"hybrid"
profile[:mobility]                    # Boolean
profile[:position_level]              # "senior"/"manager"/etc
profile[:total_experience_years]      # Integer
profile[:is_decision_maker]           # Boolean
profile[:is_top_universities]         # Boolean
profile[:followers_count]             # Integer
profile[:connections_count]           # Integer

# Contact (requires reveal_emails/reveal_phones)
profile[:business_emails]             # ["joao@company.com"]
profile[:personal_emails]             # ["joao@gmail.com"]
profile[:phone_numbers]               # ["+55119999999"]

# Structured data
profile[:skills]                      # ["Ruby", "Rails", "PostgreSQL"]
profile[:languages]                   # ["Portuguese", "English"]
profile[:expertise]                   # ["Backend Development", "API Design"]
profile[:experiences]                 # Array — see below
profile[:educations]                  # Array — see below
profile[:certifications]              # Array — [{name: "AWS", ...}]
profile[:awards]                      # Array — [{name: "...", ...}]
```

### Experience Object (inside profile[:experiences])

```ruby
experience = profile[:experiences].first

experience[:company_info][:name]      # "Google"
experience[:company_info][:industry]  # "Technology"
experience[:company_roles]            # Array of roles at this company
experience[:company_roles].first[:title]               # "Software Engineer"
experience[:company_roles].first[:is_current_experience] # true/false
experience[:company_roles].first[:start_date]          # "2020-01"
experience[:company_roles].first[:end_date]            # "Present"
experience[:company_roles].first[:description]         # "Building APIs..."
```

### Education Object (inside profile[:educations])

```ruby
education = profile[:educations].first

education[:school_name]               # "USP"
education[:degree]                    # "Bachelor's"
education[:field_of_study]            # "Computer Science"
education[:start_date]                # "2012"
education[:end_date]                  # "2016"
```

---

## How to Consume: Output Examples

### Reading Raw API Response

```ruby
result = Pearch::SearchService.new(account, user).search(
  query: "Ruby Developer São Paulo",
  type: "fast",
  limit: 10,
  reveal_emails: true
)

puts "Found ~#{result[:total_estimate]} candidates"
puts "Thread: #{result[:thread_id]}"
puts "Duration: #{result[:duration]}s"
puts "Credits remaining: #{result[:credits_remaining]}"

result[:search_results].each do |item|
  profile = item[:profile]

  puts "#{profile[:name]} — #{profile[:title]}"
  puts "  Company: #{profile[:experiences]&.first&.dig(:company_info, :name)}"
  puts "  Location: #{profile[:city]}, #{profile[:state]}, #{profile[:country]}"
  puts "  Experience: #{profile[:total_experience_years]} years"
  puts "  LinkedIn: #{profile[:linkedin_url]}"
  puts "  Skills: #{profile[:skills]&.join(', ')}"
  puts "  Languages: #{profile[:languages]&.join(', ')}"
  puts "  Decision maker: #{profile[:is_decision_maker]}"

  emails = Array(profile[:business_emails]) + Array(profile[:personal_emails])
  puts "  Emails: #{emails.join(', ')}" if emails.any?

  phones = Array(profile[:phone_numbers])
  puts "  Phones: #{phones.join(', ')}" if phones.any?
end
```

### Reading Processed SourcedProfile

After `ProcessSourcingJob` runs, data is stored in `SourcedProfile`:

```ruby
sp = SourcedProfile.find(id)

# Basic fields
sp.name                    # "João Silva"
sp.first_name              # "João"
sp.last_name               # "Silva"
sp.title                   # "Senior Software Engineer"
sp.current_company         # "Google"
sp.current_title           # "Software Engineer"
sp.role_name               # "Software Engineer"
sp.position_level          # "senior"

# Contact
sp.email                   # "joao@company.com"
sp.emails                  # ["joao@company.com", "joao@gmail.com"]
sp.phone                   # "+55119999999"
sp.phones                  # ["+55119999999"]
sp.has_emails              # true
sp.has_phone_numbers       # true

# Location
sp.location                # "São Paulo, SP, Brazil"
sp.city                    # "São Paulo"
sp.state                   # "SP"
sp.country                 # "Brazil"
sp.remote_work             # "yes"
sp.mobility                # true

# Professional
sp.total_experience_years  # 8
sp.is_decision_maker       # false
sp.is_top_universities     # true
sp.followers_count         # 1200
sp.connections_count       # 500

# Structured data (jsonb)
sp.skills_data             # ["Ruby", "Rails", "PostgreSQL"]
sp.languages_data          # ["Portuguese", "English"]
sp.expertise               # ["Backend Development"]
sp.certifications_data     # [{"name" => "AWS Solutions Architect"}]
sp.awards_data             # [{"name" => "Best Paper 2023"}]

# Experience (jsonb array)
sp.experiences_data.each do |exp|
  company = exp.dig("company_info", "name")
  roles = exp["company_roles"] || []
  roles.each do |role|
    puts "#{role['title']} at #{company} (#{role['start_date']} - #{role['end_date']})"
  end
end

# Education (jsonb array)
sp.educations_data.each do |edu|
  puts "#{edu['degree']} #{edu['field_of_study']} at #{edu['school_name']}"
end

# Full raw profile (jsonb)
sp.profile_data            # Complete Pearch profile hash (all fields)

# Identifiers
sp.provider                # "pearch" (or "hybrid" if merged with local)
sp.external_id             # Pearch docid
sp.linkedin_url            # "https://linkedin.com/in/..."
sp.linkedin_slug           # "joao-silva"
```

---

## Data Flow: Pearch Result → SourcedProfile

| Pearch Field | SourcedProfile Column | Notes |
|---|---|---|
| `result[:docid]` | `external_id` | Unique Pearch document ID |
| `profile[:name]` | `name` | |
| `profile[:first_name]` | `first_name` | |
| `profile[:middle_name]` | `middle_name` | |
| `profile[:last_name]` | `last_name` | |
| `profile[:title]` | `title` | |
| `profile[:role_name]` | `role_name` | Falls back to title |
| `profile[:summary]` | `summary` | |
| `profile[:picture_url]` | `picture_url` | |
| `profile[:estimated_age]` | `estimated_age` | |
| `profile[:location]` | `location` | |
| `profile[:city]` | `city` | |
| `profile[:state]` | `state` | |
| `profile[:country]` | `country` | |
| `profile[:linkedin_url]` | `linkedin_url` | |
| `profile[:linkedin_slug]` | `linkedin_slug` | |
| `profile[:cpf]` | `cpf` | LGPD sensitive |
| `profile[:date_birth]` | `date_birth` | |
| `profile[:remote_work]` | `remote_work` | |
| `profile[:mobility]` | `mobility` | |
| `profile[:position_level]` | `position_level` | |
| `profile[:total_experience_years]` | `total_experience_years` | |
| `profile[:is_decision_maker]` | `is_decision_maker` | |
| `profile[:is_top_universities]` | `is_top_universities` | |
| `profile[:followers_count]` | `followers_count` | |
| `profile[:connections_count]` | `connections_count` | |
| `business_emails + personal_emails` | `email`, `emails` | Merged, deduped |
| `profile[:phone_numbers]` | `phone`, `phones` | Deduped |
| `profile[:skills]` | `skills_data` | jsonb array |
| `profile[:languages]` | `languages_data` | jsonb array |
| `profile[:expertise]` | `expertise` | jsonb array |
| `profile[:experiences]` | `experiences_data` | jsonb array of hashes |
| `profile[:educations]` | `educations_data` | jsonb array of hashes |
| `profile[:certifications]` | `certifications_data` | jsonb array |
| `profile[:awards]` | `awards_data` | jsonb array |
| `profile` (entire hash) | `profile_data` | Full raw data (jsonb) |

### Deduplication

`SourcedProfiles::ProfileMatchingService` checks in order:
1. `email` (case-insensitive)
2. `phone`
3. `cpf`
4. `linkedin_url`
5. `external_id` (docid)

If duplicate found: existing profile is updated with non-blank new fields, provider changes to "hybrid" if was "local".

---

## Contact Enrichment

`Pearch::ContactEnrichmentService` enriches a single `SourcedProfile` with missing emails/phones by doing a targeted Pearch search using the profile's `external_id` (docid_whitelist):

```ruby
Pearch::ContactEnrichmentService.new(
  sourced_profile: profile,
  account: account,
  user: user
).enrich!
```

Credit cost: 1 base + 2 (emails) + 14 (phones) = up to 17 credits per enrichment.

---

## WebSocket Events

**Channel:** `SourcingChannel` — stream: `"{user_id}_sourcing_{sourcing_id}"`

| Event | When |
|-------|------|
| `sourcing_started` | Search initiated |
| `global_search_submitted` | HTTP request sent to Pearch |
| `global_search_processing` | Processing results |
| `sourcing_profiles_found` | Results received from Pearch |
| `profile_processed` | Single SourcedProfile created (progress) |
| `profiles_processing_completed` | First page of 15 profiles done |
| `sourcing_completed` | Search fully completed |
| `sourcing_failed` | Search error |

**Channel:** `SearchCreditsChannel` — stream: `"search_credits_account_{account_id}"`

| Event | When |
|-------|------|
| `credit_update` | Any credit balance change (consumption, purchase, refund) |

---

## Redis Caching (Pagination)

Results are cached in Redis for pagination (30min TTL):

```
Key: "sourcing_pool:{sourcing_id}:global"
Value: {
  search_results: [...all Pearch results...],
  total: 150,
  page_size: 15,
  created_at: "...",
  expires_at: "..."
}

Key: "sourcing_pool_page:{sourcing_id}"
Value: current_page_number (integer)
```

`load_more` reads from this cache and processes the next page of 15 profiles.

---

## Account Configuration

Per-account Pearch defaults stored in `Account.sourcing_config`:

```ruby
account.pearch_config
# => { "limit" => 10, "type" => "fast" }

account.update!(sourcing_config: {
  pearch: { limit: 20, type: "pro" }
})
```

---

## Search Archetypes

`SearchArchetype` records define reusable search templates. Converted to Pearch params via `SearchArchetypes::ToPearchParamsService`:

```ruby
SearchArchetypes::ToPearchParamsService.call(
  archetype: archetype,
  profile: "balanced",
  additional_options: { reveal_emails: true }
)
# => { query: "Senior Ruby Developer", custom_filters: {...}, search_profile: "balanced", limit: 30 }
```

Maps internal seniority levels to Pearch title keywords:
- intern → Intern, Trainee
- junior → Junior, Associate
- mid → Mid-Level, Analyst
- senior → Senior, Lead, Sr, Sr.
- lead → Lead, Team Lead, Tech Lead
- manager → Manager, Head
- director → Director, VP
- c_level → C-Level, CTO, CEO, CFO

---

## Audit Trail

### PearchSearchLog

Every Pearch API call is logged with:
- query, uuid, thread_id
- search_parameters (jsonb)
- results_count, total_estimate
- credits_used, credits_remaining_after
- duration_seconds, status, error_message

**Scopes:** `successful`, `failed`, `by_account`, `by_user`, `by_date_range`

### PearchCreditTransaction

Every credit change is recorded:
- transaction_type: purchase, refund, bonus, adjustment, consumption
- amount (negative for consumption)
- balance_before, balance_after
- reason, reference_id, reference_type

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PEARCH_API_KEY` | Bearer token for Pearch API v2 |
| `GEMINI_CHAT_MODEL` | LLM model for QueryParserService (default: gemini-2.5-flash) |

---

## Error Handling

| HTTP Status | Error |
|-------------|-------|
| 400 | Invalid parameters (ArgumentError) |
| 401 | Invalid API key |
| 402 | Insufficient credits (InsufficientCreditsError) |
| 429 | Rate limit exceeded |
| 500+ | Generic API error |

All errors are logged to `Rails.logger` and search status is set to `"failed"` on the Sourcing record.
