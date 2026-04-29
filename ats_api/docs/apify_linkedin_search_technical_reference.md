# Apify LinkedIn Search — Technical Reference

## Overview

LinkedIn candidate search using the **HarvestAPI LinkedIn Profile Search** actor (`harvestapi~linkedin-profile-search`) via the Apify platform. Performs keyword-based LinkedIn people search, returns structured profile data, and integrates with the sourcing pipeline to create `SourcedProfile` records.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                       Entry Points                                │
│                                                                   │
│  SourcingsController#create       TalentSearchesController#create │
│  (sources: ["linkedin"])          (sources: ["linkedin"])         │
│           │                                │                      │
│           ▼                                ▼                      │
│  JobEnqueuerService              handle_linkedin_search           │
│           │                                │                      │
│           ▼                                ▼                      │
│              Apify::LinkedinSearchJob                             │
│                        │                                          │
│                        ▼                                          │
│          LinkedinSearchExecutorService                            │
│                        │                                          │
│                        ▼                                          │
│             LinkedinSearchService                                 │
│                   │         │                                     │
│                   ▼         ▼                                     │
│              HttpClient   Query                                   │
│                   │         │                                     │
│                   ▼         ▼                                     │
│          Apify API (harvestapi~linkedin-profile-search)           │
│                        │                                          │
│                        ▼                                          │
│                   ResultSet                                       │
│                  (Profile[])                                      │
│                        │                                          │
│                        ▼                                          │
│        SourcedProfile + SourcedProfileSourcing                    │
│                        │                                          │
│                        ▼                                          │
│          SourcingChannel (WebSocket broadcast)                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## File Inventory

| File | Role |
|---|---|
| `app/services/apify/linkedin_search_service.rb` | Core service — starts Apify run, polls, fetches results |
| `app/services/apify/linkedin_search/query.rb` | Validates criteria, builds `to_actor_input` payload |
| `app/services/apify/linkedin_search/query_builder.rb` | Fluent builder API for constructing queries |
| `app/services/apify/linkedin_search/profile.rb` | Profile wrapper with Location, Experience, Education, Certification, Project, Volunteering, Publication |
| `app/services/apify/linkedin_search/result_set.rb` | Enumerable collection of profiles |
| `app/services/apify/linkedin_search/cost_calculator.rb` | Estimated cost calculation |
| `app/services/apify/linkedin_search/http_client.rb` | Faraday HTTP client for Apify API |
| `app/services/apify/linkedin_search_executor_service.rb` | Pipeline integration — creates SourcedProfile records |
| `app/jobs/apify/linkedin_search_job.rb` | Sidekiq job — async execution with tenant switching |
| `app/services/sourcings/job_enqueuer_service.rb` | Dispatches search to correct job per source |

---

## Apify Actor

**Actor:** `harvestapi~linkedin-profile-search`
**API Base:** `https://api.apify.com/v2`
**Auth:** Bearer token via `APIFY_KEY` environment variable

### Profile Scraper Modes

| Mode | Key | Cost/Profile | Data Returned |
|---|---|---|---|
| Short | `:short` | $0.00 | Name, headline, location, current position |
| Full | `:full` | $0.004 | + About, experience, education, skills, languages, certifications, projects, volunteering |
| Full + Email | `:full_with_email` | $0.01 | + Email address lookup |

### Rate Limits

- **429 Too Many Requests**: Apify returns rate limit errors when too many concurrent runs
- The service raises `LinkedinSearchService::RateLimitError` with `retry_after` timestamp
- Recommended: max 3 concurrent runs per API key

### Cost Model

```
total = (take_pages × $0.10) + (profiles_found × cost_per_profile_by_mode)
```

Each page returns up to 25 profiles. Example: 2 pages × Full+Email = $0.20 + (50 × $0.01) = $0.70

---

## INPUT: All Actor Parameters

### Basic Search Filters

| Ruby Parameter | Actor Key | Type | Default | Description |
|---|---|---|---|---|
| `search_query` | `searchQuery` | String | nil | Free-text LinkedIn search keywords |
| `current_job_titles` | `currentJobTitles` | Array\<String> | [] | Filter by current job titles |
| `past_job_titles` | `pastJobTitles` | Array\<String> | [] | Filter by previous job titles |
| `locations` | `locations` | Array\<String> | [] | Geographic filter (city, state, country) |
| `current_companies` | `currentCompanies` | Array\<String> | [] | LinkedIn company URLs |
| `past_companies` | `pastCompanies` | Array\<String> | [] | LinkedIn company URLs |
| `schools` | `schools` | Array\<String> | [] | LinkedIn school URLs |
| `industries` | `industries` | Array\<String> | [] | LinkedIn industry IDs |
| `years_of_experience` | `yearsOfExperience` | Array\<String> | [] | Ranges: "1-2", "3-5", "6-10", "11+" |
| `years_at_current_company` | `yearsAtCurrentCompany` | Array\<String> | [] | Ranges: "less-than-1", "1-2", "3-5", "6-10", "11+" |

### Advanced Filters

| Ruby Parameter | Actor Key | Type | Default | Description |
|---|---|---|---|---|
| `seniority_levels` | `seniorityLevelIds` | Array\<Integer> | [] | Seniority level IDs (see table below) |
| `functions` | `functionIds` | Array\<Integer> | [] | Job function IDs (see table below) |
| `company_headcount` | `companyHeadcount` | Array\<String> | [] | Company size codes (see table below) |
| `profile_languages` | `profileLanguages` | Array\<String> | [] | LinkedIn profile language codes (e.g. "en", "pt") |
| `first_names` | `firstNames` | Array\<String> | [] | Filter by first name |
| `last_names` | `lastNames` | Array\<String> | [] | Filter by last name |
| `recently_changed_jobs` | `recentlyChangedJobs` | Boolean | nil | Only profiles that recently changed jobs |
| `company_headquarter_locations` | `companyHeadquarterLocations` | Array\<String> | [] | Filter by company HQ location |

### Exclusion Filters

| Ruby Parameter | Actor Key | Type | Description |
|---|---|---|---|
| `exclude_locations` | `excludeLocations` | Array\<String> | Exclude profiles in these locations |
| `exclude_current_companies` | `excludeCurrentCompanies` | Array\<String> | Exclude current company URLs |
| `exclude_past_companies` | `excludePastCompanies` | Array\<String> | Exclude past company URLs |
| `exclude_schools` | `excludeSchools` | Array\<String> | Exclude school URLs |
| `exclude_current_job_titles` | `excludeCurrentJobTitles` | Array\<String> | Exclude current titles |
| `exclude_past_job_titles` | `excludePastJobTitles` | Array\<String> | Exclude past titles |
| `exclude_industry_ids` | `excludeIndustryIds` | Array\<String> | Exclude industry IDs |
| `exclude_seniority_levels` | `excludeSeniorityLevelIds` | Array\<Integer> | Exclude seniority IDs |
| `exclude_function_ids` | `excludeFunctionIds` | Array\<Integer> | Exclude function IDs |
| `exclude_company_headquarter_locations` | `excludeCompanyHeadquarterLocations` | Array\<String> | Exclude HQ locations |

### Pagination & Control

| Ruby Parameter | Actor Key | Type | Default | Description |
|---|---|---|---|---|
| `mode` | `profileScraperMode` | Symbol | `:short` | `:short`, `:full`, `:full_with_email` |
| `start_page` | `startPage` | Integer | 1 | First page to scrape |
| `take_pages` | `takePages` | Integer | 1 | Number of pages (max 100) |
| `max_items` | `maxItems` | Integer | 0 | Max profiles (0 = unlimited) |

### Auto Query Segmentation

Automatically splits large searches into smaller queries for better coverage when LinkedIn truncates results at 100 pages.

| Ruby Parameter | Actor Key | Type | Description |
|---|---|---|---|
| `auto_query_segmentation` | `autoQuerySegmentation` | Boolean | Enable automatic segmentation |
| `auto_query_segmentation_levels` | `autoQuerySegmentationLevels` | Integer | Segmentation depth (1-3, default: auto) |
| `auto_query_segmentation_target_countries` | `autoQuerySegmentationTargetCountries` | Array\<String> | Countries to segment by |

### Deduplication (MongoDB)

| Ruby Parameter | Actor Key | Type | Description |
|---|---|---|---|
| `deduplication_mode` | `profileDeduplicationMode` | String | "none", "disabled", "duplicates_only", "unique_only" |
| `mongodb_connection_string` | `mongoDbConnectionString` | String | MongoDB URI for cross-run dedup |
| `post_filter_query` | `postFilteringMongoDbQuery` | String | MongoDB query to filter results |
| `post_filter_aggregation` | `postFilteringMongoDbAggregation` | String | MongoDB aggregation pipeline |

---

## Reference Tables

### Seniority Level IDs (`seniorityLevelIds`)

| ID | Level | Ruby Constant |
|---|---|---|
| 100 | Unpaid | `Query::SENIORITY_LEVELS[:unpaid]` |
| 110 | Training | `Query::SENIORITY_LEVELS[:training]` |
| 120 | Entry | `Query::SENIORITY_LEVELS[:entry]` |
| 130 | Senior | `Query::SENIORITY_LEVELS[:senior]` |
| 200 | Manager | `Query::SENIORITY_LEVELS[:manager]` |
| 210 | Director | `Query::SENIORITY_LEVELS[:director]` |
| 220 | VP | `Query::SENIORITY_LEVELS[:vp]` |
| 300 | CXO | `Query::SENIORITY_LEVELS[:cxo]` |
| 310 | Partner | `Query::SENIORITY_LEVELS[:partner]` |
| 320 | Owner | `Query::SENIORITY_LEVELS[:owner]` |

### Job Function IDs (`functionIds`)

| ID | Function | ID | Function |
|---|---|---|---|
| 1 | Accounting | 14 | Legal |
| 2 | Administrative | 15 | Marketing |
| 3 | Arts & Design | 16 | Media & Communication |
| 4 | Business Development | 17 | Military & Protective Services |
| 5 | Community & Social Services | 18 | Operations |
| 6 | Consulting | 19 | Product Management |
| 7 | Education | 20 | Program & Project Management |
| 8 | Engineering | 21 | Purchasing |
| 9 | Entrepreneurship | 22 | Quality Assurance |
| 10 | Finance | 23 | Real Estate |
| 11 | Healthcare Services | 24 | Research |
| 12 | Human Resources | 25 | Sales |
| 13 | Information Technology | 26 | Support |

### Company Headcount Codes (`companyHeadcount`)

| Code | Range | Ruby Constant |
|---|---|---|
| A | Self-employed | `Query::COMPANY_HEADCOUNT[:self_employed]` |
| B | 1-10 | `Query::COMPANY_HEADCOUNT[:tiny]` |
| C | 11-50 | `Query::COMPANY_HEADCOUNT[:small]` |
| D | 51-200 | `Query::COMPANY_HEADCOUNT[:medium_small]` |
| E | 201-500 | `Query::COMPANY_HEADCOUNT[:medium]` |
| F | 501-1000 | `Query::COMPANY_HEADCOUNT[:medium_large]` |
| G | 1001-5000 | `Query::COMPANY_HEADCOUNT[:large]` |
| H | 5001-10000 | `Query::COMPANY_HEADCOUNT[:very_large]` |
| I | 10001+ | `Query::COMPANY_HEADCOUNT[:enterprise]` |

---

## OUTPUT: All Profile Fields

### Profile (`Apify::LinkedinSearchService::Profile`)

| Method | Return Type | Source Field | Mode Required |
|---|---|---|---|
| `id` | String | `id` | Short |
| `public_identifier` | String | `publicIdentifier` | Short |
| `linkedin_url` | String | `linkedinUrl` | Short |
| `object_urn` | String | `objectUrn` | Short |
| `first_name` | String | `firstName` | Short |
| `last_name` | String | `lastName` | Short |
| `full_name` | String | computed | Short |
| `headline` | String | `headline` | Short |
| `about` | String | `about` | Full |
| `photo_url` | String | `photo` | Short |
| `profile_picture` | Hash | `profilePicture` (with sizes) | Short |
| `profile_picture_url(size:)` | String | Selects from profilePicture sizes | Short |
| `cover_picture` | Hash | `coverPicture` | Full |
| `email` | String | `email` | Full+Email |
| `has_email?` | Boolean | computed | Full+Email |
| `open_to_work?` | Boolean | `openToWork` | Short |
| `hiring?` | Boolean | `hiring` | Short |
| `premium?` | Boolean | `premium` | Short |
| `influencer?` | Boolean | `influencer` | Short |
| `verified?` | Boolean | `verified` | Short |
| `memorialized?` | Boolean | `memorialized` | Short |
| `connections_count` | Integer | `connectionsCount` | Short |
| `follower_count` | Integer | `followerCount` | Short |
| `registered_at` | String | `registeredAt` | Full |
| `top_skills_text` | String | `topSkills` (comma-separated) | Short |
| `current_company` | String | `currentPosition[0].companyName` | Short |
| `current_position` | Experience | First experience | Full |
| `current_positions` | [Experience] | `currentPosition` array | Short |
| `top_education` | Education | `profileTopEducation` | Short |
| `years_of_experience` | Integer | computed from earliest start_date | Full |
| `page_number` | Integer | `_meta.pagination.pageNumber` | Short |

### Collections (Full mode)

| Method | Return Type | Source Field |
|---|---|---|
| `experience` | [Experience] | `experience[]` |
| `education` | [Education] | `education[]` |
| `skills` | [String] | `skills[].name` |
| `languages` | [String] | `languages[].name` |
| `certifications` | [Certification] | `certifications[]` |
| `projects` | [Project] | `projects[]` |
| `volunteering` | [Volunteering] | `volunteering[]` |
| `publications` | [Publication] | `publications[]` |
| `courses` | Array\<Hash> | `courses[]` (raw) |
| `patents` | Array\<Hash> | `patents[]` (raw) |
| `honors_and_awards` | Array\<Hash> | `honorsAndAwards[]` (raw) |
| `causes` | Array\<String> | `causes[]` (raw) |
| `received_recommendations` | Array\<Hash> | `receivedRecommendations[]` (raw) |
| `featured` | Array\<Hash> | `featured[]` (raw) |
| `more_profiles` | Array\<Hash> | `moreProfiles[]` (raw) |

### Location

| Method | Return Type | Source Field |
|---|---|---|
| `text` | String | `location.linkedinText` |
| `country_code` | String | `location.countryCode` |
| `country` | String | `location.parsed.country` |
| `state` | String | `location.parsed.state` |
| `city` | String | `location.parsed.city` |
| `to_s` | String | same as `text` |

### Experience

| Method | Return Type | Source Field |
|---|---|---|
| `title` | String | `position` |
| `company` | String | `companyName` |
| `company_url` | String | `companyLinkedinUrl` |
| `company_id` | Integer | `companyId` |
| `company_universal_name` | String | `companyUniversalName` |
| `company_logo_url` | String | `companyLogo.url` or `companyLogo` |
| `location` | String | `location` |
| `employment_type` | String | `employmentType` (e.g. "Full-time", "Contract") |
| `workplace_type` | String | `workplaceType` (e.g. "Remote", "On-site", "Hybrid") |
| `duration` | String | `duration` |
| `description` | String | `description` |
| `current?` | Boolean | `endDate.text == "Present"` |
| `start_date` | Hash | `startDate` ({year:, month:, text:}) |
| `end_date` | Hash | `endDate` ({year:, month:, text:}) |
| `skills` | [String] | `skills[].name` |
| `experience_group_id` | String | `experienceGroupId` |

### Education

| Method | Return Type | Source Field |
|---|---|---|
| `school` | String | `schoolName` |
| `school_linkedin_url` | String | `schoolLinkedinUrl` |
| `school_id` | Integer | `schoolId` |
| `school_logo_url` | String | `schoolLogo.url` or `schoolLogo` |
| `degree` | String | `degree` |
| `field` | String | `fieldOfStudy` |
| `description` | String | `description` |
| `start_date` | Hash | `startDate` |
| `end_date` | Hash | `endDate` |
| `period` | String | `period` |
| `skills` | [String] | `skills[].name` |

### Certification

| Method | Return Type | Source Field |
|---|---|---|
| `name` | String | `name` |
| `authority` | String | `authority` |
| `url` | String | `url` |
| `start_date` | Hash | `startDate` |
| `end_date` | Hash | `endDate` |
| `to_h` | Hash | Serialized hash |

### Project

| Method | Return Type | Source Field |
|---|---|---|
| `title` | String | `title` |
| `description` | String | `description` |
| `url` | String | `url` |
| `start_date` | Hash | `startDate` |
| `end_date` | Hash | `endDate` |
| `members` | Array | `members[]` |
| `to_h` | Hash | Serialized hash |

### Volunteering

| Method | Return Type | Source Field |
|---|---|---|
| `role` | String | `role` |
| `organization` | String | `organization` or `companyName` |
| `cause` | String | `cause` |
| `description` | String | `description` |
| `start_date` | Hash | `startDate` |
| `end_date` | Hash | `endDate` |
| `to_h` | Hash | Serialized hash |

### Publication

| Method | Return Type | Source Field |
|---|---|---|
| `title` | String | `title` or `name` |
| `publisher` | String | `publisher` |
| `url` | String | `url` |
| `date` | Hash | `date` or `publishedDate` |
| `description` | String | `description` |
| `to_h` | Hash | Serialized hash |

---

## Pipeline: Profile → SourcedProfile Mapping

### Direct Column Mappings

| Profile Method | SourcedProfile Column | Notes |
|---|---|---|
| `full_name` | `name` | |
| `first_name` | `first_name` | |
| `last_name` | `last_name` | |
| `headline` | `title` | |
| `current_company` | `current_company` | |
| `current_position.title` | `current_title` | |
| `email` | `email`, `emails[]` | |
| `linkedin_url` | `linkedin_url` | |
| `public_identifier` | `external_id`, `linkedin_slug` | |
| `location.city` | `city` | |
| `location.state` | `state` | |
| `location.country` | `country` | |
| `location.to_s` | `location` | |
| `years_of_experience` | `total_experience_years` | |
| `skills` | `skills_data` | jsonb array |
| `languages` | `languages_data` | jsonb array |
| `photo_url` | `picture_url` | |
| `about` | `summary` | |
| `follower_count` | `followers_count` | |
| `connections_count` | `connections_count` | |
| `certifications` | `certifications_data` | jsonb, via `to_h` |
| `honors_and_awards` | `awards_data` | jsonb, raw |

### Enriched Data Mappings

| Profile Method | SourcedProfile Column | Format |
|---|---|---|
| `experience[]` | `experiences_data` | Array of hashes with: title, company, company_url, company_id, company_universal_name, location, employment_type, workplace_type, duration, description, current, start_date, end_date, skills |
| `education[]` | `educations_data` | Array of hashes with: school, school_linkedin_url, school_id, degree, field, description, start_date, end_date, period, skills |

### profile_data (jsonb catch-all)

Stored in `SourcedProfile.profile_data` as a single JSON object:

```json
{
  "open_to_work": true,
  "hiring": false,
  "premium": true,
  "influencer": false,
  "verified": true,
  "registered_at": "2015-01-15",
  "top_skills_text": "Ruby, Rails, PostgreSQL",
  "object_urn": "urn:li:member:123456",
  "profile_picture": { "sizes": { "100x100": "url", "200x200": "url", "400x400": "url", "800x800": "url" } },
  "cover_picture": { "url": "...", "sizes": { ... } },
  "projects": [{ "title": "...", "description": "..." }],
  "volunteering": [{ "role": "...", "organization": "..." }],
  "publications": [{ "title": "...", "publisher": "..." }],
  "courses": [{ "name": "...", "number": "..." }],
  "patents": [{ "title": "...", "description": "..." }],
  "causes": ["Education", "Environment"],
  "received_recommendations": [{ "recommender": "...", "text": "..." }],
  "more_profiles": [{ "publicIdentifier": "...", "linkedinUrl": "..." }]
}
```

---

## How to Consume: Input Examples

### Basic Search

```ruby
Apify::LinkedinSearchService.builder
  .with_query("Ruby on Rails developer")
  .with_titles("Software Engineer", "Backend Developer")
  .in_locations("São Paulo, Brazil")
  .mode(:full_with_email)
  .pages(2)
  .execute
```

### Advanced Filters

```ruby
Apify::LinkedinSearchService.builder
  .with_query("Engineering Manager")
  .in_locations("Brazil")
  .with_seniority_levels(200, 210)       # Manager, Director
  .with_functions(8, 13)                  # Engineering, IT
  .with_company_headcount("F", "G", "H") # 501-10000 employees
  .with_profile_languages("pt", "en")
  .recently_changed_jobs
  .mode(:full_with_email)
  .pages(3)
  .execute
```

### Using Constants

```ruby
Query = Apify::LinkedinSearchService::Query

Apify::LinkedinSearchService.builder
  .with_seniority_levels(
    Query::SENIORITY_LEVELS[:senior],
    Query::SENIORITY_LEVELS[:manager]
  )
  .with_company_headcount(
    Query::COMPANY_HEADCOUNT[:large],
    Query::COMPANY_HEADCOUNT[:enterprise]
  )
  .execute
```

### Exclusion Filters

```ruby
Apify::LinkedinSearchService.builder
  .with_query("Software Engineer")
  .in_locations("Brazil")
  .exclude_locations("Rio de Janeiro, Brazil")
  .exclude_current_companies("https://linkedin.com/company/competitor")
  .exclude_current_titles("Intern", "Junior")
  .exclude_industries("47")  # Mining
  .mode(:full)
  .pages(5)
  .execute
```

### Name-Based Search

```ruby
Apify::LinkedinSearchService.builder
  .with_first_names("João", "Maria")
  .with_last_names("Silva", "Santos")
  .in_locations("São Paulo, Brazil")
  .mode(:short)
  .pages(1)
  .execute
```

### Auto Query Segmentation

```ruby
Apify::LinkedinSearchService.builder
  .with_query("Data Scientist")
  .in_locations("Brazil")
  .with_auto_segmentation(levels: 2, target_countries: ["BR", "PT"])
  .mode(:full_with_email)
  .pages(10)
  .execute
```

### Deduplication with MongoDB

```ruby
Apify::LinkedinSearchService.builder
  .with_query("Product Manager")
  .in_locations("São Paulo")
  .with_deduplication("unique_only", mongodb_url: ENV["MONGODB_URL"])
  .mode(:full)
  .pages(20)
  .execute
```

### Post-Filtering

```ruby
Apify::LinkedinSearchService.builder
  .with_query("Developer")
  .in_locations("Brazil")
  .with_post_filter(
    query: '{"connectionsCount": {"$gte": 500}}',
    aggregation: '[{"$match": {"openToWork": true}}]'
  )
  .mode(:full)
  .pages(5)
  .execute
```

### Direct Query (without builder)

```ruby
query = Apify::LinkedinSearchService::Query.new(
  search_query: "Ruby developer",
  locations: ["São Paulo, Brazil"],
  seniority_levels: [130, 200],
  functions: [8, 13],
  company_headcount: ["E", "F", "G"],
  exclude_current_companies: ["https://linkedin.com/company/competitor"],
  recently_changed_jobs: true,
  mode: :full_with_email,
  take_pages: 3
)

query.valid?         # => true
query.to_actor_input # => Hash with camelCase keys
query.estimated_cost # => { total: 1.05, ... }
```

---

## How to Consume: Output Examples

### Iterating Results

```ruby
result_set = Apify::LinkedinSearchService.builder
  .with_query("Ruby developer")
  .in_locations("São Paulo")
  .mode(:full_with_email)
  .pages(2)
  .execute

puts "Total found: #{result_set.total_count}"
puts "Pages scraped: #{result_set.pages_scraped}"
puts "Has more: #{result_set.has_more?}"
puts "Run ID: #{result_set.run_id}"
puts "Rate limited: #{result_set.rate_limited?}"

result_set.each do |profile|
  # Basic info
  puts "#{profile.full_name} (#{profile.public_identifier})"
  puts "  LinkedIn: #{profile.linkedin_url}"
  puts "  Headline: #{profile.headline}"
  puts "  About: #{profile.about}"

  # Status flags
  puts "  Open to work: #{profile.open_to_work?}"
  puts "  Hiring: #{profile.hiring?}"
  puts "  Premium: #{profile.premium?}"
  puts "  Verified: #{profile.verified?}"

  # Network metrics
  puts "  Connections: #{profile.connections_count}"
  puts "  Followers: #{profile.follower_count}"
  puts "  Registered: #{profile.registered_at}"

  # Contact
  puts "  Email: #{profile.email}" if profile.has_email?

  # Location
  loc = profile.location
  puts "  Location: #{loc.city}, #{loc.state}, #{loc.country} (#{loc.country_code})"

  # Profile picture (multiple sizes)
  puts "  Photo: #{profile.profile_picture_url(size: '400x400')}"

  # Experience
  profile.experience.each do |exp|
    puts "  #{exp.title} at #{exp.company}"
    puts "    Type: #{exp.employment_type} / #{exp.workplace_type}"
    puts "    Location: #{exp.location}"
    puts "    Duration: #{exp.duration}"
    puts "    Skills: #{exp.skills.join(', ')}" if exp.skills.any?
    puts "    Current: #{exp.current?}"
  end

  # Education
  profile.education.each do |edu|
    puts "  #{edu.degree} in #{edu.field} at #{edu.school}"
    puts "    Period: #{edu.period}"
    puts "    Skills: #{edu.skills.join(', ')}" if edu.skills.any?
  end

  # Certifications
  profile.certifications.each do |cert|
    puts "  Cert: #{cert.name} by #{cert.authority}"
  end

  # Projects
  profile.projects.each do |proj|
    puts "  Project: #{proj.title} — #{proj.url}"
  end

  # Volunteering
  profile.volunteering.each do |vol|
    puts "  Volunteer: #{vol.role} at #{vol.organization} (#{vol.cause})"
  end

  # Publications
  profile.publications.each do |pub|
    puts "  Publication: #{pub.title} in #{pub.publisher}"
  end

  # Other
  puts "  Skills: #{profile.skills.join(', ')}"
  puts "  Top Skills: #{profile.top_skills_text}"
  puts "  Languages: #{profile.languages.join(', ')}"
  puts "  Courses: #{profile.courses.size}"
  puts "  Patents: #{profile.patents.size}"
  puts "  Awards: #{profile.honors_and_awards.size}"
  puts "  Causes: #{profile.causes.join(', ')}"
  puts "  Recommendations: #{profile.received_recommendations.size}"

  # Raw data access
  puts "  Raw: #{profile.raw_data.keys.join(', ')}"
end
```

### Via Sourcing Pipeline

```ruby
sourcing = account.sourcings.create!(
  user: user,
  uid: SecureRandom.uuid,
  provider: "linkedin",
  query: "Backend Developer",
  status: "processing",
  searched_at: Time.current
)

params = {
  query: "Backend Developer",
  locations: ["Brazil"],
  mode: "full_with_email",
  take_pages: 3,
  seniority_levels: [130, 200],
  functions: [8],
  exclude_current_companies: ["https://linkedin.com/company/competitor"]
}

Apify::LinkedinSearchJob.perform_async(
  account.id, user.id, sourcing.id, params.to_json
)
```

### Reading SourcedProfile After Pipeline

```ruby
sourced_profile = SourcedProfile.find(id)

# Direct columns
sourced_profile.name
sourced_profile.connections_count
sourced_profile.followers_count
sourced_profile.certifications_data  # => [{ name: "...", authority: "..." }]
sourced_profile.awards_data          # => [{ "name" => "...", ... }]

# Enriched experiences
sourced_profile.experiences_data.each do |exp|
  puts "#{exp['title']} at #{exp['company']}"
  puts "  Type: #{exp['employment_type']} / #{exp['workplace_type']}"
  puts "  Skills: #{exp['skills']&.join(', ')}"
end

# Enriched education
sourced_profile.educations_data.each do |edu|
  puts "#{edu['degree']} at #{edu['school']}"
  puts "  Period: #{edu['period']}"
  puts "  Skills: #{edu['skills']&.join(', ')}"
end

# Extra data in profile_data (jsonb)
data = sourced_profile.profile_data || {}
puts "Open to work: #{data['open_to_work']}"
puts "Premium: #{data['premium']}"
puts "Verified: #{data['verified']}"
puts "Projects: #{data['projects']&.size}"
puts "Volunteering: #{data['volunteering']&.size}"
puts "Publications: #{data['publications']&.size}"
puts "Causes: #{data['causes']&.join(', ')}"
```

---

## Sidekiq Job

### `Apify::LinkedinSearchJob`

| Setting | Value |
|---|---|
| Queue | `sourcing_search` |
| Retry | 2 |
| Priority | 6 (same as Pearch) |

**Arguments:** `(account_id, user_id, sourcing_id, params_json)`

**Lifecycle:**
1. Finds Account + User, switches tenant
2. Updates Sourcing status to `"processing"`
3. Broadcasts `sourcing_started` via SourcingChannel
4. Calls `LinkedinSearchExecutorService`
5. Broadcasts `sourcing_completed` or `sourcing_failed`

---

## HTTP Client & Polling

- **Library:** Faraday with JSON middleware
- **Base URL:** `https://api.apify.com/v2`
- **Auth:** Query parameter `token` from `ENV["APIFY_KEY"]`
- **Polling:** Every 5s, max 120 attempts (10min timeout)
- **Terminal statuses:** SUCCEEDED, FAILED, TIMED-OUT, ABORTED

---

## Error Handling

| Exception | Cause | Handling |
|---|---|---|
| `RateLimitError` | Apify rate limit hit | Returns retry_after timestamp |
| `TimeoutError` | 10-minute poll timeout | Sourcing marked as failed |
| `RunFailedError` | Actor run failed | Sourcing marked as failed |
| `AbortedError` | Actor run aborted | Sourcing marked as failed |
| `ApiError` | HTTP-level errors | Sourcing marked as failed |

---

## API Endpoints

### Via SourcingsController

```
POST /api/v1/users/sourcings
```

```json
{
  "query": "Ruby on Rails developer",
  "sources": ["linkedin"],
  "where": {
    "current_job_titles": ["Software Engineer"],
    "locations": ["São Paulo, Brazil"],
    "seniority_levels": [130, 200],
    "functions": [8],
    "company_headcount": ["E", "F", "G"],
    "exclude_current_companies": ["https://linkedin.com/company/competitor"],
    "recently_changed_jobs": true
  },
  "linkedin_mode": "full_with_email",
  "take_pages": 2,
  "max_items": 50
}
```

### WebSocket Events

Subscribe to `SourcingChannel` with `sourcing_id`:

```javascript
{ type: "sourcing_started", sourcing: { ... } }
{ type: "sourcing_completed", sourcing: { ... }, success: true }
{ type: "sourcing_failed", sourcing: { ... }, success: false, error: "message" }
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `APIFY_KEY` | Yes | Apify API token |

---

## Comparison: Pearch vs LinkedIn Search

| Feature | Pearch | LinkedIn (Apify) |
|---|---|---|
| Data Source | Multiple web sources | LinkedIn only |
| Speed | 5-30 seconds | 30s-10min (Apify polling) |
| Cost Model | Credits (per result + add-ons) | USD (per page + per profile) |
| Email Access | Add-on (+2 credits/result) | Mode: full_with_email ($0.01/profile) |
| Phone Access | Add-on (+14 credits/result) | Not available |
| Dedup | By external_id | By email + LinkedIn URL + public_identifier |
| Query Parser | LLM (Gemini) auto-translates PT→EN | Manual filter specification |
| Sync Mode | Supported | Always async (background job) |
| Advanced Filters | AI-parsed custom_filters | Structured: seniority, functions, headcount, exclusions, segmentation |
| Results/Page | Configurable (10-150) | Fixed 25/page |
| Provider Tag | `"pearch"` | `"linkedin"` |
