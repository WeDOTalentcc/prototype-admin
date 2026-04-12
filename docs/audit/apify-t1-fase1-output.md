# T1 Fase 1 — Diagnostico Apify Integration

**Data**: 2026-04-12
**Objetivo**: Mapeamento completo do estado atual para integracao Apify

---

## 1.1 MAPEAMENTO DO APIFY SERVICE

### A. Actors configurados

| Actor | Variavel | Uso |
|-------|----------|-----|
| `voyager/linkedin-company-profile-scraper` | `LINKEDIN_ACTOR_ID` | `scrape_linkedin_company` |
| `dev_fusion/Linkedin-Profile-Scraper` | `LINKEDIN_PERSON_ACTOR_ID` | `_scrape_linkedin_person` |
| `anchor/linkedin-person-scraper` | `LINKEDIN_LEGACY_ACTOR_ID` | Fallback se dev_fusion falhar |
| `curious_coder/email-finder` | `EMAIL_FINDER_ACTOR_ID` | `_discover_email` |
| `bebity/glassdoor-scraper` | `GLASSDOOR_ACTOR_ID` | `scrape_glassdoor_company` |
| `hMvNSpz3JnHgl5jkh` (hardcoded) | — | `scrape_salary_data` (Google Jobs) |
| `misceres/indeed-scraper` (hardcoded) | — | `scrape_salary_data` (Indeed) |

### B. Metodos

| Metodo | Assinatura | O que faz |
|--------|-----------|-----------|
| `run_apify_actor` | `async (actor_id, input_data) -> dict` | Core runner — inicia actor, poll cada 5s, max 300s |
| `scrape_linkedin_company` | `async (linkedin_url) -> dict` | Scrape dados empresa (missao, cultura, valores) |
| `scrape_glassdoor_company` | `async (company_name) -> dict` | Scrape Glassdoor (ratings, pros/cons) |
| `enrich_candidate_profile` | `async (linkedin_url, name, email) -> dict` | Orquestra person scraping + email discovery |
| `scrape_salary_data` | `async (job_title, location) -> list` | Scrape salarios Google Jobs + Indeed |
| `_scrape_linkedin_person` | `async (linkedin_url) -> dict` | Scrape perfil pessoa (skills, exp, edu) |
| `_discover_email` | `async (name, linkedin_url) -> list[str]` | Descoberta de emails |

### C. Output do enrich_candidate_profile

Retorna dict com:
- `first_name`, `last_name`, `headline`, `summary`, `location`, `industry`, `connections`
- `experience`: lista de `{title, company, duration, location}`
- `skills`: lista de strings
- `education`: lista de `{school, degree, field}`
- `certifications`: lista de strings
- `source`: "linkedin"
- `emails`: lista de emails descobertos

### D. Autenticacao

- `APIFY_API_KEY` lido de `os.environ` (linha 17)
- Tambem em `IntegrationSettings` no `config.py` (linha 311)
- Passado como query param `token={api_key}` nas URLs da API
- Validado no inicio de `run_apify_actor` — se vazio, retorna `{}`

### E. Tratamento de erro

- **Error handling**: try/except com `httpx.HTTPStatusError` e `Exception` generica
- **Fail-soft**: retorna `{}` ou `[]` em caso de falha (nao levanta excecao)
- **Rate limiting**: NENHUM client-side. Depende dos limites do Apify
- **Retry**: NENHUM retry automatico no `run_apify_actor`
- **Circuit breaker**: NENHUM no `apify_service.py` (implementado no `contact_enrichment_service.py` via `APIFY_CIRCUIT`)
- **Timeout**: 120s HTTP, 30s connect. Poll maximo 300s (5 min)

### F. ENV vars Apify

| Variavel | Local | Default |
|----------|-------|---------|
| `APIFY_API_KEY` | `os.environ` + `config.py` | `""` / `None` |
| `APIFY_COST_PER_ENRICHMENT_USD` | `config.py` + `apify_service.py` | `0.01` |
| `APIFY_ENRICHMENT_TIMEOUT_SECONDS` | `config.py` + `apify_service.py` | `30` |
| `APIFY_MAX_CONCURRENT_ENRICHMENTS` | `config.py` + `apify_service.py` | `5` |
| `APIFY_LEGACY_ACTOR` | `config.py` + `apify_service.py` | `anchor/linkedin-person-scraper` |
| `USE_APIFY_MCP` | Usado em `CompanyScraperService` | — |

---

## 1.2 MAPEAMENTO DO MODELO CANDIDATE

### Candidate — Campos completos

| Campo | Tipo | Nullable | Relevante Apify? |
|-------|------|----------|-----------------|
| `id` | UUID | No | No |
| `name` | String(255) | No | Sim (verificacao) |
| `email` | String(255) | Yes | **Sim** (descoberta) |
| `secondary_email` | String(255) | Yes | **Sim** |
| `phone` | String(50) | Yes | **Sim** |
| `mobile_phone` | String(50) | Yes | **Sim** |
| `secondary_phone` | String(50) | Yes | **Sim** |
| `linkedin_url` | String(500) | Yes | **Sim** (fonte primaria) |
| `github_url` | String(500) | Yes | Sim |
| `portfolio_url` | String(500) | Yes | Sim |
| `avatar_url` | String(500) | Yes | **Sim** |
| `current_title` | String(255) | Yes | **Sim** |
| `current_company` | String(255) | Yes | **Sim** |
| `seniority_level` | String(50) | Yes | **Sim** (derivado) |
| `years_of_experience` | Integer | Yes | **Sim** (calculado) |
| `self_introduction` | Text | Yes | **Sim** (bio/summary) |
| `technical_skills` | ARRAY(String) | Yes | **Sim** |
| `soft_skills` | ARRAY(String) | Yes | Sim |
| `languages` | JSON | Yes | Sim |
| `certifications` | ARRAY(String) | Yes | Sim |
| `location_city` | String(100) | Yes | **Sim** |
| `location_state` | String(100) | Yes | **Sim** |
| `location_country` | String(100) | Yes | **Sim** |
| `headline` | String(500) | Yes | **Sim** |
| `linkedin_followers` | Integer | Yes | Sim |
| `linkedin_connections` | Integer | Yes | Sim |
| `best_personal_email` | String(255) | Yes | **Sim** |
| `best_business_email` | String(255) | Yes | **Sim** |
| `personal_emails` | JSON | Yes | **Sim** |
| `business_emails` | JSON | Yes | **Sim** |
| `estimated_age` | Integer | Yes | Sim |
| `work_history` | JSON | Yes | Sim |
| `is_open_to_work` | Boolean | Yes | Sim |

### CandidateExperience

| Campo | Tipo | Nullable | Relevante Apify? |
|-------|------|----------|-----------------|
| `id` | UUID | No | No |
| `candidate_id` | UUID | No | No |
| `company_name` | String(255) | No | **Sim** |
| `company_linkedin_url` | String(500) | Yes | **Sim** |
| `company_domain` | String(255) | Yes | Sim |
| `title` | String(255) | Yes | **Sim** |
| `start_date` | String(50) | Yes | **Sim** |
| `end_date` | String(50) | Yes | **Sim** |
| `duration_years` | Float | Yes | **Sim** (calculado) |
| `is_current` | Boolean | Yes | **Sim** |
| `description` | Text | Yes | Sim |
| `location` | String(255) | Yes | Sim |
| `industries` | ARRAY(String) | Yes | Sim |
| `company_size` | String(50) | Yes | Sim |
| `technologies` | ARRAY(String) | Yes | Sim |

### CandidateEducation

| Campo | Tipo | Nullable | Relevante Apify? |
|-------|------|----------|-----------------|
| `id` | UUID | No | No |
| `candidate_id` | UUID | No | No |
| `institution` | String(255) | No | **Sim** |
| `degree` | String(100) | Yes | **Sim** |
| `field_of_study` | String(255) | Yes | **Sim** |
| `start_date` | String(50) | Yes | Sim |
| `end_date` | String(50) | Yes | Sim |
| `is_completed` | Boolean | Yes | Sim |

---

## 1.3 MAPEAMENTO DO CIRCUIT BREAKER

### PEARCH_CIRCUIT (referencia)

```python
PEARCH_CIRCUIT = CircuitBreaker(
    "pearch",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)
```

### APIFY_CIRCUIT (ja registrado)

```python
APIFY_CIRCUIT = CircuitBreaker(
    "apify",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=120.0,
    )
)
```

**Onde usado**: `contact_enrichment_service.py` — check `is_open`, `record_success()`, `record_failure()`

---

## 1.4 MAPEAMENTO DO RAILS ADAPTER

### CANDIDATE_FORK_TO_RAILS — campos relevantes Apify

| Fork | Rails | Apify preenche? |
|------|-------|----------------|
| `email` | `email` | **Sim** |
| `secondary_email` | `secondary_email` | **Sim** |
| `phone` | `phone` | **Sim** |
| `mobile_phone` | `mobile_phone` | **Sim** |
| `linkedin_url` | `linkedin` | **Sim** |
| `avatar_url` | `avatar_url` | **Sim** |
| `current_title` | `role_name` | **Sim** |
| `current_company` | `current_company` | **Sim** |
| `seniority_level` | `seniority_level` | **Sim** |
| `location_city` | `city` | **Sim** |
| `location_state` | `state` | **Sim** |
| `location_country` | `country` | **Sim** |
| `technical_skills` | `technical_skills` | **Sim** |
| `years_of_experience` | `years_of_experience` | **Sim** |

**Conclusao**: Todos os campos que o Apify preenche JA estao no mapping Rails. Nenhum gap identificado.

**Sync trigger**: Via `ATSSyncService.trigger_sync()` — chamado por agentes/tools ou eventos (STATUS_CHANGE, CANDIDATE_CREATED). O `RailsAdapter` publica via webhook para `/v1/events`.

---

## 1.5 MAPEAMENTO DO CONTACT PERSISTENCE

### Fluxo do reveal_contact

1. Endpoint `POST /search/reveal-contact/`
2. **Passo 1 (Apify)**: Se `linkedin_slug` disponivel, tenta `ContactEnrichmentService` primeiro ($0.01). Se sucesso + contato encontrado, retorna com `credits_used=0`
3. **Passo 2 (Pearch fallback)**: Se Apify falha ou sem LinkedIn, usa Pearch FAST. Email: 2 creditos. Phone: 14 creditos
4. Persiste via `persist_revealed_contact` no `contact_persistence.py`

### Campos persistidos

- `pearch_profile_id`, `name`, `first_name`, `last_name`
- `email`, `phone`, `linkedin_url`, `avatar_url`
- `current_title`, `current_company`
- `source` = `"pearch"` (quando via Pearch)
- `additional_data.imported_via` = `"reveal_contact"`
- `additional_data.has_revealed_email/phone`

### Source do contato

- DB `source` field: `"pearch"` ou `"apify"`
- `additional_data.imported_via`: `"reveal_contact"`
- API response `message`: indica fonte (ex: "Email revelado via Apify ($0.01)")

---

## 1.6 OUTPUT DO DEV_FUSION ACTOR

### Mapeamento dev_fusion/Linkedin-Profile-Scraper -> Candidate

| Campo Apify | Campo Candidate | Transformacao |
|------------|----------------|---------------|
| `firstName` + `lastName` | `name` | Concatenar |
| `headline` | `headline`, `current_title` | Direto |
| `summary` | `self_introduction` | Direto |
| `profileUrl` / `url` | `linkedin_url` | Direto |
| `profilePicture` / `img` | `avatar_url` | Direto |
| `location` | `location_city/state/country` | Parse por virgula |
| `connectionCount` | `linkedin_connections` | Int cast |
| `followersCount` | `linkedin_followers` | Int cast |
| `email` / `emailAddress` | `email` | Primeiro email |
| `emails[]` | `personal_emails` | Lista completa |
| `phone` / `phoneNumber` | `phone` | Primeiro telefone |
| `experience[].companyName` | `CandidateExperience.company_name` | Direto |
| `experience[].title` | `CandidateExperience.title` | Direto |
| `experience[].timePeriod.startDate` | `CandidateExperience.start_date` | YYYY-MM format |
| `experience[].timePeriod.endDate` | `CandidateExperience.end_date` | YYYY-MM ou is_current |
| `experience[].locationName` | `CandidateExperience.location` | Direto |
| `education[].schoolName` | `CandidateEducation.institution` | Direto |
| `education[].degreeName` | `CandidateEducation.degree` | Direto |
| `education[].fieldOfStudy` | `CandidateEducation.field_of_study` | Direto |
| `skills[].name` | `technical_skills` | Lista de strings |
| `certifications[].name` | `certifications` | Lista de strings |
| `languages[].name` | `languages` | Lista de strings |
| Mais antiga `experience.startDate` | `years_of_experience` | `now.year - earliest_year` |
| `headline` (keywords) | `seniority_level` | Inferencia por keywords |

---

## GAPS IDENTIFICADOS

1. ~~`apify_mapper.py` nao existia~~ -> **CRIADO** nesta fase
2. ~~ENV vars `APIFY_COST_PER_ENRICHMENT_USD`, etc nao existiam~~ -> **ADICIONADOS**
3. ~~Health check endpoint nao existia~~ -> **CRIADO** em `/api/v1/integrations/apify/health`
4. ~~Actor legacy nao configurado~~ -> **ADICIONADO** `LINKEDIN_LEGACY_ACTOR_ID`
5. Rails Adapter: **SEM GAPS** — todos os campos Apify ja estao no mapping

## ENV VARS

| Variavel | Existente? | Default |
|----------|-----------|---------|
| `APIFY_API_KEY` | Sim | `None` |
| `APIFY_COST_PER_ENRICHMENT_USD` | **Novo** | `0.01` |
| `APIFY_ENRICHMENT_TIMEOUT_SECONDS` | **Novo** | `30` |
| `APIFY_MAX_CONCURRENT_ENRICHMENTS` | **Novo** | `5` |
| `APIFY_LEGACY_ACTOR` | **Novo** | `anchor/linkedin-person-scraper` |
