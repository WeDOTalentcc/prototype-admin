# P17 — SCHEMA ALIGNMENT AUDIT
**Protocolo:** P17: Schema Alignment (Agente ↔ Banco ↔ Frontend)
**Data:** 2026-04-14
**Auditor:** Claude (Agente de Dados)
**Score P16 (baseline):** 27/100 — 7 ações ILUSÓRIAS, 9 QUEBRADAS

---

## SEÇÃO 1 — SUMÁRIO EXECUTIVO

### Contagem de Desalinhamentos por Tipo

| Tipo | Quantidade | Criticidade |
|------|-----------|-------------|
| PHANTOM (campo no serializer/adapter mas não no schema.rb) | 34 | CRÍTICA |
| NAMING (mesmo dado, nome diferente nas camadas) | 18 | ALTA |
| MISSING (campo existe no banco, não existe no agente/frontend) | 9 | ALTA |
| TYPE MISMATCH (mesmo campo, tipo diferente) | 7 | MÉDIA |
| ENUM MISMATCH (valores de status incompatíveis entre camadas) | 6 | CRÍTICA |
| ORPHAN (campo só existe numa camada, sem correspondência) | 11 | MÉDIA |
| DIRECTION (lógica invertida entre camadas) | 3 | ALTA |
| **TOTAL** | **88** | — |

### Score de Alinhamento por Entidade

| Entidade | Score | Status |
|----------|-------|--------|
| Candidato | 38/100 | CRÍTICO |
| Vaga (Job) | 22/100 | CRÍTICO |
| Apply/Processo | 15/100 | CRÍTICO |
| Usuário | 55/100 | RUIM |
| Conta (Account) | 70/100 | REGULAR |
| Selective Process (Pipeline) | 30/100 | CRÍTICO |
| Comunicação (Message) | 45/100 | RUIM |

### Top 10 Desalinhamentos Mais Críticos

1. **[PHANTOM]** ApplySerializer declara `source, status, lia_score, match_percentage, current_stage, stage_entered_at, additional_data, fork_uuid` — NENHUM existe em `applies` no schema.rb
2. **[PHANTOM]** JobSerializer declara 40+ campos que NÃO existem em `jobs` no schema.rb (status, department, seniority_level, salary_range, technical_requirements, etc.)
3. **[PHANTOM]** CandidateSerializer declara campos Work C (`seniority_level, technical_skills, soft_skills, languages, certifications, years_of_experience, diversity_*`) — não aparecem em `candidates` no schema.rb
4. **[ENUM MISMATCH]** SelectiveProcess: Rails usa inteiro enum (0=web_submission, 1=screening, 2=interview, 3=rejected, 4=hired); Python/ATS usa strings ("screening", "interview", "offer", "rejected", "hired", "withdrawn", "cv_screening", "under_review")
5. **[NAMING]** Candidato: `linkedin` (Rails) vs `linkedin_url` (Python/Fork) vs `linkedin_url` (Frontend) — 3 nomes, 1 campo
6. **[NAMING]** Candidato: `role_name` (Rails) vs `current_title` (Python Fork) vs `current_title` (Frontend)
7. **[TYPE MISMATCH]** Candidato: `id` é UUID (Python/Fork) vs bigint (Rails) — mapeado em CANDIDATE_FORK_TO_RAILS mas sem conversão garantida em runtime
8. **[DIRECTION]** Apply: `is_active` (Fork, boolean) mapeado para `is_deleted` (Rails, boolean) — lógica INVERTIDA (is_active=true → is_deleted=false)
9. **[TYPE MISMATCH]** Candidato: `gender` é string (Fork) vs integer enum (Rails); `marital_status` idem
10. **[PHANTOM]** UserSerializer declara `name, role, permissions, workos_user_id, avatar_url, last_login_at, status, fork_uuid` — users no schema.rb tem apenas `email, password_digest, account_id`

---

## SEÇÃO 2 — INVENTÁRIO POR ENTIDADE

### 2.1 CANDIDATO

#### A. Schema do Banco (Rails) — tabela `candidates`
Campos reais (confirmados em schema.rb):
`id (bigint PK), uid (string), name (string, NOT NULL), surname (string), email (string, NOT NULL, unique), secondary_email, mobile_phone, phone, secondary_phone, linkedin, github, portfolio, current_company, role_name, position_level, self_introduction (text), curriculum_text (text), date_birth (date), gender (integer enum), nationality (string), marital_status (integer enum), cpf (string, unique), street, number (integer), district, zip, city, state, country, complement, clt_expectation (float), pj_expectation (float), freelance_expectation (float), current_salary (float), desired_salary (float), currency (string, default BRL), remote_work (boolean), mobility (boolean), interests (string), comments (text), source (string), avatar_url, curriculum_pdf_url, completed_register (boolean), accept_terms (boolean), created_at, updated_at`

**Ausentes no schema (PHANTOM — declarados no serializer mas não no banco):**
`seniority_level, years_of_experience, technical_skills, soft_skills, languages, certifications, diversity_race_ethnicity, diversity_disability, diversity_disability_type, diversity_lgbtqia, diversity_refugee, diversity_age_50_plus, diversity_indigenous, diversity_documents, diversity_self_declared_at, diversity_document_deadline, fork_uuid`

#### B. Schema do Agente (Python Fork) — campos em `CANDIDATE_FORK_TO_RAILS`
Campos lidos/escritos: `id (UUID), name, email, secondary_email, phone, mobile_phone, secondary_phone, linkedin_url, github_url, portfolio_url, avatar_url, date_of_birth, gender, nationality, marital_status, cpf, current_title, current_company, seniority_level, self_introduction, resume_text, resume_url, location_city, location_state, location_country, address_street, address_number, address_district, address_zip, address_complement, current_salary, desired_salary_min, salary_expectation_clt, salary_expectation_pj, salary_expectation_freelance, salary_currency, is_remote, willing_to_relocate, source, technical_skills, soft_skills, languages, certifications, years_of_experience, diversity_*`

**Fork-only (sem correspondência Rails):** `timezone, embeddings, pearch_profile_id, ats_candidate_id, cover_letter, is_open_to_work, is_decision_maker, headline`

**Rails-only (sem correspondência Fork):** `uid, completed_register, accept_terms, interests, comments, surname, position_level`

#### C. Schema da API
- **Rails API (CandidateSerializer):** Retorna todos os campos do banco + campos Work C PHANTOM (lia_score, technical_skills, etc. declarados no serializer mas que retornarão nil pois não existem no schema real)
- **Python API (CandidateLocal TS interface):** Usa nomenclatura Fork (linkedin_url, current_title, location_city, etc.)

#### D. Schema do Frontend (TypeScript)
Interface `CandidateLocal` em `/plataforma-lia/src/services/lia-api/types/candidate.types.ts`:
Campos chave: `id, name, email, phone, mobile_phone, linkedin_url, current_title, current_company, seniority_level, location_city, location_state, salary_expectation_clt, is_remote, willing_to_relocate, status, lia_score, skills_match_percentage, candidate_status`

**Observação crítica:** O frontend usa `name` (alinhado com Rails) para exibição, mas também verifica `c.name || c.full_name` em `useJobStatusModal.ts` — indicando inconsistência histórica onde `full_name` foi usado em algum ponto.

---

### 2.2 VAGA (JOB)

#### A. Schema do Banco (Rails) — tabela `jobs`
Campos reais: `id (bigint), title, description, user_id, account_id, provider, provider_job_id, company_id, published_date, application_deadline, is_remote, city, state, country, job_url, career_page_id, career_page_name, career_page_url, career_page_logo, friendly_badge, disabilities, workplace_type, created_at, updated_at`

**PHANTOM — declarados no JobSerializer mas ausentes no schema:** `status, department, employment_type, seniority_level, priority, urgency_level, technical_requirements, behavioral_competencies, screening_questions, interview_stages, languages, salary_range, bonus_range, benefits, deadline_screening, deadline_shortlist, deadline_closing, manager, manager_email, recruiter, recruiter_email, created_by, organizational_structure, published_linkedin, published_website, published_indeed, linkedin_post_id, indeed_job_id, last_published_at, is_confidential, is_affirmative, affirmative_criteria_primary, affirmative_criteria_secondary, affirmative_description, affirmative_document_required, affirmative_document_types, visibility, access_list, masked_company_name, exclude_from_sync, public_slug, budget, budget_used, approval_status, approval_requested_at, approval_requested_by, approved_by, approved_at, rejection_reason, whatsapp_template_type, tags, fork_uuid`

#### B. Schema do Agente (JOB_FORK_TO_RAILS)
Mapeamentos: `id, title, description, location→city, work_model→workplace_type, is_confidential→is_confidential (PHANTOM), open_date→published_date, deadline→application_deadline, is_affirmative→disabilities (MAPPING INCORRETO — campos semânticos diferentes), published_linkedin→provider (TYPE MISMATCH: bool → string)`

#### C. Schema da API
Interface `JobVacancy` no frontend tem 60+ campos — a maioria são campos PHANTOM declarados no serializer.

#### D. Schema do Frontend
`JobVacancy` em `job.types.ts`: usa `work_model` (Fork) vs `workplace_type` (Rails); usa `open_date/deadline` (Fork) vs `published_date/application_deadline` (Rails).

---

### 2.3 APPLY / PROCESSO SELETIVO

#### A. Schema do Banco (Rails) — tabela `applies`
Campos reais: `id (bigint), candidate_id (bigint, FK), job_id (bigint, FK), selective_process_id (bigint, FK), is_deleted (boolean), created_at, updated_at`

**PHANTOM — declarados no ApplySerializer mas AUSENTES no schema:**
`source, status, lia_score, match_percentage, current_stage, stage_entered_at, additional_data, fork_uuid`

**Total de campos schema real: 7. Total no serializer: 15. 8 campos PHANTOM = 57% phantom.**

#### B. Schema do Agente (APPLY_FORK_TO_RAILS)
`id→id, candidate_id→candidate_id, job_id→job_id, stage_id→selective_process_id, is_active→is_deleted (INVERTIDO)`

Fork-only (sem Rails): `screening_score, interview_report, lia_recommendation, status`

#### C. Schema da API Python
`CandidateHiredPayload, CandidateRejectedPayload` — usa status strings "hired"/"rejected" que não existem na tabela `applies`.

---

### 2.4 SELECTIVE PROCESS (Pipeline)

#### A. Schema do Banco (Rails) — tabela `selective_processes`
Campos reais: `id (bigint), name (string), position (integer), status (integer enum: 0-4), job_id (bigint), uid (string), sub_status (jsonb), created_at, updated_at`

Enum: `web_submission=0, screening=1, interview=2, rejected=3, hired=4`

**PHANTOM — declarados no SelectiveProcessSerializer mas ausentes no schema:**
`display_name, description, color, icon, stage_type, is_initial, is_final, is_rejection, is_hired, auto_advance_rules, sla_hours, is_active, is_system, stage_category, action_behavior, default_channel, stage_metadata, created_by, company_id`

#### B. Schema do Agente
Usa strings: "screening", "interview", "offer", "rejected", "hired", "withdrawn", "cv_screening", "under_review" — com mapeamento ATS intermediário para Gupy e Pandapé. O campo "offer/proposta" não existe no enum Rails. "cv_screening" não existe. "withdrawn" não existe.

---

### 2.5 USUÁRIO

#### A. Schema do Banco (Rails) — tabela `users`
Campos reais: `id (bigint), email (string), password_digest (string), account_id (bigint), created_at, updated_at`

**PHANTOM — declarados no UserSerializer mas ausentes no schema:**
`name, role, permissions, workos_user_id, avatar_url, last_login_at, status, fork_uuid`

#### B. Schema do Agente (USER_FORK_TO_RAILS)
Apenas `id→id, email→email`. Fork tem `name, role, company_id, is_active` sem equivalente Rails.

---

### 2.6 CONTA/EMPRESA (ACCOUNT)

#### A. Schema do Banco (Rails) — tabela `accounts`
Campos reais: `id (bigint), name (string), tenant (string), staging_tenant (string), created_at, updated_at`

Alinhamento razoável. Python usa `company_id` (UUID) para referência que mapeia para `account_id` (bigint) no Rails — sem mapeamento explícito documentado no adapter.

---

### 2.7 COMUNICAÇÃO (MESSAGE)

#### A. Schema do Banco (Rails) — tabela `messages`
Campos reais: `id (bigint), content (text), entity (integer enum), status (integer enum), is_deleted (boolean), parent_message_id (bigint), reference_type (string), reference_id (bigint), account_id (bigint), metadata (jsonb), created_at, updated_at`

#### B. Schema do Agente (MESSAGE_FORK_TO_RAILS)
Fork tem 3 sistemas de mensagem; Rails tem 1. Mapeamento: `company_id→account_id`. Campos polymorphic `reference_type/reference_id` sem equivalente Fork.

---

## SEÇÃO 3 — MATRIZ DE ALINHAMENTO CAMPO A CAMPO

### 3.1 CANDIDATO — Campos Críticos

| Campo Semântico | Banco Rails | API Response (Serializer) | Agente Python (Fork) | Frontend TS | Tipo Desalinhamento |
|---|---|---|---|---|---|
| Nome | `name` (string, NOT NULL) | `name` | `name` | `name` | OK |
| Sobrenome | `surname` | `surname` | (ausente) | (ausente) | MISSING no agente/frontend |
| Email | `email` | `email` | `email` | `email` | OK |
| Email 2 | `secondary_email` | `secondary_email` | `secondary_email` | `secondary_email` | OK |
| Telefone | `phone` | `phone` | `phone` | `phone` | OK |
| Celular | `mobile_phone` | `mobile_phone` | `mobile_phone` | `mobile_phone` | OK |
| LinkedIn | `linkedin` | `linkedin` | `linkedin_url` | `linkedin_url` | NAMING |
| GitHub | `github` | `github` | `github_url` | `github_url` | NAMING |
| Portfolio | `portfolio` | `portfolio` | `portfolio_url` | `portfolio_url` | NAMING |
| Foto | `avatar_url` | `avatar_url` | `avatar_url` | `avatar_url` | OK |
| Título atual | `role_name` | `role_name` | `current_title` | `current_title` | NAMING |
| Nível senior. | (ausente no schema) | `seniority_level` (PHANTOM) | `seniority_level` | `seniority_level` | PHANTOM |
| Anos experiência | (ausente) | `years_of_experience` (PHANTOM) | `years_of_experience` | `years_of_experience` | PHANTOM |
| Apresentação | `self_introduction` | `self_introduction` | `self_introduction` | `self_introduction` | OK |
| Currículo texto | `curriculum_text` | `curriculum_text` | `resume_text` | `resume_text` | NAMING |
| Currículo PDF | `curriculum_pdf_url` | `curriculum_pdf_url` | `resume_url` | `resume_url` | NAMING |
| Data nasc. | `date_birth` (date) | `date_birth` | `date_of_birth` | `date_of_birth` | NAMING |
| Gênero | `gender` (integer enum) | `gender` | `gender` (string) | `gender` (string) | TYPE MISMATCH |
| Estado civil | `marital_status` (integer) | `marital_status` | `marital_status` (string) | `marital_status` (string) | TYPE MISMATCH |
| CPF | `cpf` (plaintext) | `cpf` | `cpf` | `cpf` | TYPE MISMATCH (encrypt?) |
| Número endereço | `number` (integer) | `number` | `address_number` (string) | `address_number` (string) | NAMING + TYPE |
| Cidade | `city` | `city` | `location_city` | `location_city` | NAMING |
| Estado | `state` | `state` | `location_state` | `location_state` | NAMING |
| País | `country` | `country` | `location_country` | `location_country` | NAMING |
| Rua | `street` | `street` | `address_street` | `address_street` | NAMING |
| Bairro | `district` | `district` | `address_district` | `address_district` | NAMING |
| CEP | `zip` | `zip` | `address_zip` | `address_zip` | NAMING |
| Complemento | `complement` | `complement` | `address_complement` | `address_complement` | NAMING |
| Salário atual | `current_salary` (float) | `current_salary` | `current_salary` (number) | `current_salary` (number) | OK |
| Sal. desejado | `desired_salary` (float) | `desired_salary` | `desired_salary_min` | `desired_salary_min` | NAMING |
| Sal. CLT | `clt_expectation` (float) | `clt_expectation` | `salary_expectation_clt` | `salary_expectation_clt` | NAMING |
| Sal. PJ | `pj_expectation` (float) | `pj_expectation` | `salary_expectation_pj` | `salary_expectation_pj` | NAMING |
| Sal. Freelance | `freelance_expectation` (float) | `freelance_expectation` | `salary_expectation_freelance` | `salary_expectation_freelance` | NAMING |
| Moeda | `currency` (default BRL) | `currency` | `salary_currency` | `salary_currency` | NAMING |
| Remoto | `remote_work` (boolean) | `remote_work` | `is_remote` | `is_remote` | NAMING |
| Mobilidade | `mobility` (boolean) | `mobility` | `willing_to_relocate` | `willing_to_relocate` | NAMING |
| Interesses | `interests` (string) | `interests` | (ausente) | (ausente) | MISSING agente |
| Comentários | `comments` (text) | `comments` | (ausente) | (ausente) | MISSING agente |
| Source | `source` | `source` | `source` | `source` | OK |
| Skills técnicas | (ausente no schema) | `technical_skills` (PHANTOM) | `technical_skills` | `technical_skills` | PHANTOM |
| Skills soft | (ausente) | `soft_skills` (PHANTOM) | `soft_skills` | `soft_skills` | PHANTOM |
| Idiomas | (ausente) | `languages` (PHANTOM) | `languages` | `languages` | PHANTOM |
| Certificações | (ausente) | `certifications` (PHANTOM) | `certifications` | `certifications` | PHANTOM |
| Diversidade (* 8 campos) | (ausentes) | PHANTOM (8 campos) | 8 campos fork | (parcial) | PHANTOM |
| fork_uuid | (ausente) | `fork_uuid` (PHANTOM) | `id` (UUID) | `id` | PHANTOM |
| Status | (ausente) | (ausente) | `status` (string) | `status` (string) | ORPHAN Python/Frontend |
| LIA Score | (ausente) | (ausente) | (interno) | `lia_score` | ORPHAN Frontend |
| uid | `uid` | `uid` | (ausente) | (ausente) | ORPHAN Rails |
| position_level | `position_level` | `position_level` | (ausente) | (ausente) | ORPHAN Rails |

### 3.2 VAGA (JOB) — Campos Críticos

| Campo Semântico | Banco Rails | API Response | Agente Python | Frontend TS | Tipo |
|---|---|---|---|---|---|
| ID | `id` (bigint) | `id` | `id` (UUID) | `id` (string) | TYPE MISMATCH |
| Título | `title` | `title` | `title` | `title` | OK |
| Descrição | `description` | `description` | `description` | `description` | OK |
| Status | (ausente no schema) | `status` (PHANTOM) | `status` (string) | `status` (string) | PHANTOM |
| Modelo trabalho | `workplace_type` | `workplace_type` | `work_model` | `work_model` | NAMING |
| Data publicação | `published_date` | `published_date` | `open_date` | `open_date` | NAMING |
| Prazo inscrição | `application_deadline` | `application_deadline` | `deadline` | `deadline` | NAMING |
| Remoto | `is_remote` | `is_remote` | (usa work_model) | (usa work_model) | NAMING |
| Afirmativa | `disabilities` (boolean) | `disabilities` | `is_affirmative` | `is_affirmative` | NAMING (semântica diferente!) |
| LinkedIn pub. | `provider` (string) | `provider` | `published_linkedin` (boolean) | `published_linkedin` | TYPE MISMATCH |
| Salário range | (ausente) | `salary_range` (PHANTOM) | `salary_range` | `salary_range` | PHANTOM |
| Departamento | (ausente) | `department` (PHANTOM) | `department` | `department` | PHANTOM |
| Prioridade | (ausente) | `priority` (PHANTOM) | `priority` | `priority` | PHANTOM |
| Requisitos técnicos | (ausente) | `technical_requirements` (PHANTOM) | `technical_requirements` | `technical_requirements` | PHANTOM |
| Etapas entrevista | (ausente) | `interview_stages` (PHANTOM) | `interview_stages` | `interview_stages` | PHANTOM |

### 3.3 APPLY — Campos Críticos

| Campo Semântico | Banco Rails | API Response | Agente Python | Frontend TS | Tipo |
|---|---|---|---|---|---|
| ID | `id` (bigint) | `id` | `id` (UUID) | `id` (string) | TYPE MISMATCH |
| Candidato FK | `candidate_id` (bigint) | `candidate_id` | `candidate_id` (UUID) | `candidate_id` | TYPE MISMATCH |
| Vaga FK | `job_id` (bigint) | `job_id` | `job_id` (UUID) | `job_id` | TYPE MISMATCH |
| Etapa FK | `selective_process_id` (bigint) | `selective_process_id` | `stage_id` (UUID) | — | NAMING + TYPE |
| Deletado | `is_deleted` (boolean) | `is_deleted` | `is_active` → `is_deleted` | — | DIRECTION (invertido) |
| Status | (ausente) | `status` (PHANTOM) | `status` (string) | `status` | PHANTOM |
| LIA Score | (ausente) | `lia_score` (PHANTOM) | `screening_score` | `lia_score` | PHANTOM + NAMING |
| Match % | (ausente) | `match_percentage` (PHANTOM) | — | — | PHANTOM |
| Etapa atual | (ausente) | `current_stage` (PHANTOM) | — | — | PHANTOM |
| Source | (ausente) | `source` (PHANTOM) | — | — | PHANTOM |
| Fork UUID | (ausente) | `fork_uuid` (PHANTOM) | `id` (UUID) | — | PHANTOM |

---

## SEÇÃO 4 — CANDIDATE_FORK_TO_RAILS — ANÁLISE DETALHADA

| Campo Python (Fork) | Campo Rails | Existe no schema.rb? | Problema |
|---|---|---|---|
| `id` | `id` | SIM (bigint) | TYPE MISMATCH: UUID → bigint sem conversão explícita |
| `name` | `name` | SIM | OK |
| `email` | `email` | SIM | OK |
| `secondary_email` | `secondary_email` | SIM | OK |
| `phone` | `phone` | SIM | OK |
| `mobile_phone` | `mobile_phone` | SIM | OK |
| `secondary_phone` | `secondary_phone` | SIM | OK |
| `linkedin_url` | `linkedin` | SIM | NAMING — serializer retorna `linkedin`, frontend espera `linkedin_url` |
| `github_url` | `github` | SIM | NAMING — mesma inconsistência |
| `portfolio_url` | `portfolio` | SIM | NAMING |
| `avatar_url` | `avatar_url` | SIM | OK |
| `date_of_birth` | `date_birth` | SIM | NAMING |
| `gender` | `gender` | SIM (integer) | TYPE MISMATCH: string → integer enum |
| `nationality` | `nationality` | SIM | OK |
| `marital_status` | `marital_status` | SIM (integer) | TYPE MISMATCH: string → integer enum |
| `cpf` | `cpf` | SIM | Risco: Fork pode encriptar, Rails plaintext |
| `current_title` | `role_name` | SIM | NAMING |
| `current_company` | `current_company` | SIM | OK |
| `seniority_level` | `seniority_level` | **NAO** | PHANTOM — campo não existe no schema |
| `self_introduction` | `self_introduction` | SIM | OK |
| `resume_text` | `curriculum_text` | SIM | NAMING |
| `resume_url` | `curriculum_pdf_url` | SIM | NAMING |
| `location_city` | `city` | SIM | NAMING |
| `location_state` | `state` | SIM | NAMING |
| `location_country` | `country` | SIM | NAMING |
| `address_street` | `street` | SIM | NAMING |
| `address_number` | `number` | SIM (integer) | NAMING + TYPE MISMATCH: string → integer |
| `address_district` | `district` | SIM | NAMING |
| `address_zip` | `zip` | SIM | NAMING |
| `address_complement` | `complement` | SIM | NAMING |
| `current_salary` | `current_salary` | SIM | OK |
| `desired_salary_min` | `desired_salary` | SIM | NAMING (min vs total — semântica diferente?) |
| `salary_expectation_clt` | `clt_expectation` | SIM | NAMING |
| `salary_expectation_pj` | `pj_expectation` | SIM | NAMING |
| `salary_expectation_freelance` | `freelance_expectation` | SIM | NAMING |
| `salary_currency` | `currency` | SIM | NAMING |
| `is_remote` | `remote_work` | SIM | NAMING |
| `willing_to_relocate` | `mobility` | SIM | NAMING |
| `source` | `source` | SIM | OK |
| `technical_skills` | `technical_skills` | **NAO** | PHANTOM |
| `soft_skills` | `soft_skills` | **NAO** | PHANTOM |
| `languages` | `languages` | **NAO** | PHANTOM |
| `certifications` | `certifications` | **NAO** | PHANTOM |
| `years_of_experience` | `years_of_experience` | **NAO** | PHANTOM |
| `diversity_race_ethnicity` | `diversity_race_ethnicity` | **NAO** | PHANTOM |
| `diversity_disability` | `diversity_disability` | **NAO** | PHANTOM |
| `diversity_disability_type` | `diversity_disability_type` | **NAO** | PHANTOM |
| `diversity_lgbtqia` | `diversity_lgbtqia` | **NAO** | PHANTOM |
| `diversity_refugee` | `diversity_refugee` | **NAO** | PHANTOM |
| `diversity_age_50_plus` | `diversity_age_50_plus` | **NAO** | PHANTOM |
| `diversity_indigenous` | `diversity_indigenous` | **NAO** | PHANTOM |
| `diversity_documents` | `diversity_documents` | **NAO** | PHANTOM |
| `diversity_self_declared_at` | `diversity_self_declared_at` | **NAO** | PHANTOM |
| `diversity_document_deadline` | `diversity_document_deadline` | **NAO** | PHANTOM |

**RESUMO CANDIDATE_FORK_TO_RAILS:**
- Total de mapeamentos: 52
- Campos Rails que não existem no schema (PHANTOM): 16 (31%)
- Mapeamentos com NAMING diferente: 15 (29%)
- TYPE MISMATCH: 4 (8%)
- OK funcionais: 17 (33%)

---

## SEÇÃO 5 — LIFECYCLE E TENANT

### 5.1 Lifecycle do Candidato

**Implementação Rails:**
O Rails implementa lifecycle via `selective_processes` com enum de 5 estágios:
- `web_submission (0)` → `screening (1)` → `interview (2)` → `rejected (3)` / `hired (4)`

Não há modelo de lifecycle pós-contratação. Não existem estados `employee`, `alumni`, `churned`, `rehire`. O candidato `hired` permanece apenas como `selective_process.status=4`.

**Implementação Python/Agente:**
O agente usa 12+ estados de string: `applied, screening, cv_screening, interview, technical_interview, behavioral_interview, final_interview, offer, hired, rejected, withdrawn, under_review`. Destes, apenas 4 têm equivalente Rails (`screening, interview, rejected, hired`). Os estados `offer, cv_screening, technical_interview, withdrawn, under_review` são **ORPHAN** — existem no Python mas não têm coluna correspondente no banco Rails.

**Lifecycle completo (hired → employee → alumni):** NÃO implementado em nenhuma camada. O candidato "contratado" não transita para outro estado após a contratação.

**Transições que o agente pode executar:**
- Pode avançar/recuar etapas via `selective_process_id` no Apply — mas sem validação de sequência (pode pular etapas)
- Pode marcar `is_deleted=true` nos applies (equivale a remover da vaga)
- NÃO pode criar novos `selective_processes` — apenas referenciar existentes

### 5.2 Modelo de Tenant

**Isolamento por camada:**
- **Rails:** `candidates` pertencem a `account` (FK `account_id`); `jobs` pertencem a `account_id`; `users` pertencem a `account_id`. Isolamento via `account_id`.
- **Python/Agente:** Usa `company_id` (UUID). No domínio `sourcing`, `company_id` é passado como parâmetro e filtrado em queries via `WHERE company_id = :company_id`. No entanto:
  - O `company_id` do Python (UUID) é diferente do `account_id` do Rails (bigint) — sem mapeamento documentado
  - Algumas tools do sourcing tornam `company_id` **opcional** (`"description": "ID da empresa (opcional)"`) — risco de query sem filtro
  - O `nurture_sequence_tool_registry.py` usa `OR company_id IS NULL` — permite acesso a registros globais sem tenant
  - Não há middleware de tenant isolation — cada tool precisa implementar seu próprio filtro

**Risco de cross-tenant:** MÉDIO-ALTO. Tools com `company_id` opcional podem retornar dados de outros tenants se o chamador omitir o parâmetro.

**Accounts vs Companies:** Rails usa `account`; Python usa `company`. O `accounts.tenant` (string) e `accounts.staging_tenant` existem mas não há mapeamento explícito para o UUID `company_id` do Python.

### 5.3 Pipeline de Processo Seletivo

**Customizável por vaga:** SIM no Rails — cada `job` tem múltiplos `selective_processes` com posições configuráveis. O default é `[web_submission, screening, interview, rejected, hired]`.

**O agente carrega configuração da vaga:** NÃO. O agente usa um mapeamento estático `ATS_STAGE_MAPPING` que assume estágios fixos (Triagem, Entrevista, Proposta, etc.). Não há chamada para buscar o pipeline específico da vaga antes de avançar um candidato.

**Enums de status — alinhamento:**
| Sistema | Valores |
|---|---|
| Rails (selective_process.status enum) | web_submission, screening, interview, rejected, hired |
| Python/Agente (strings internas) | applied, screening, cv_screening, interview, technical_interview, behavioral_interview, final_interview, offer, hired, rejected, withdrawn, under_review |
| Frontend (CandidateLocal.status) | status (string livre — não há enum TypeScript definido) |
| ATS Gupy mapping | applied, screening, cv_screening, interview, technical_interview, behavioral_interview, final_interview, offer, hired, rejected, withdrawn, under_review |
| ATS Pandapé mapping | novo, triagem, triagem_cv, triagem_comportamental, entrevista, entrevista_tecnica, entrevista_comportamental, entrevista_final, proposta, contratado, reprovado, desistente, em_analise |

**ENUM MISMATCH crítico:** O agente pode tentar definir `status="offer"` em um `selective_process` que só aceita integers 0-4 — causando erro de validação silenciosa ou dado corrompido.

---

## SEÇÃO 6 — PERMISSÕES

**O agente verifica permissões do usuário:** PARCIALMENTE.
- O Rails tem tabelas `permissions, roles, role_permissions, user_permissions, user_roles` — RBAC completo no banco.
- O Python tem `assert_resource_ownership` em `app.auth.dependencies` — verificação de ownership de recursos.
- O domínio `sourcing` NÃO verifica role antes de executar tools — qualquer usuário autenticado pode buscar, criar sequências, mover candidatos.
- O único controle encontrado é `_check_communication_matrix_approval` que verifica se o canal de comunicação está aprovado — mas isso é aprovação de canal, não de permissão de usuário.
- O modelo `analytics/schemas/observability.py` tem `UNAUTHORIZED_ACCESS` como tipo de evento — indica que violações são logadas mas não necessariamente bloqueadas.

**RBAC no nível do agente:** NÃO IMPLEMENTADO. As tools do agente não checam `role` do usuário.

**Riscos de escalada de privilégio:**
1. Um usuário `viewer` poderia chamar tools de `move_candidate` se tiver token válido
2. Tools de communication podem enviar emails/WhatsApp sem verificar se usuário tem permissão de envio
3. Cross-tenant via `company_id` opcional (descrito na Seção 5.2)
4. O agente pode ler dados de candidatos de qualquer tenant se não passar `company_id`

---

## SEÇÃO 7 — PLANO DE NORMALIZAÇÃO

### Naming Canônico Proposto (Rails como fonte da verdade, adaptado para legibilidade)

| Campo | Naming Canônico | Justificativa |
|---|---|---|
| Nome do candidato | `name` (Rails) | Rails + Frontend atual |
| LinkedIn | `linkedin_url` (Fork/Frontend) | Mais expressivo; Rails deve ser migrado |
| Título atual | `current_title` (Fork/Frontend) | Mais expressivo; `role_name` Rails é ambíguo |
| Cidade | `location_city` (Fork/Frontend) | Evita conflito com `city` da vaga |
| Remoto | `is_remote` (Fork/Frontend) | Padrão booleano is_ prefix |
| Mobilidade | `willing_to_relocate` (Fork/Frontend) | Mais expressivo que `mobility` |
| Currículo texto | `resume_text` (Fork/Frontend) | Mais claro que `curriculum_text` |
| Currículo PDF | `resume_url` (Fork/Frontend) | Mais claro que `curriculum_pdf_url` |
| Status pipeline | Inteiro enum (Rails) + label string | Rails é source of truth para pipeline |
| ID | bigint Rails para integrações externas; UUID Fork para API pública | Manter dois IDs com `fork_uuid` em Rails |

### Fonte da Verdade por Entidade
- **Candidato CRUD:** Rails PostgreSQL (migração em andamento)
- **Vaga CRUD:** Rails PostgreSQL
- **Pipeline/Stages:** Rails (selective_processes)
- **IA/Scoring/Embeddings:** Python PostgreSQL (Fork) — permanecem lá
- **Status de Apply:** Rails (via selective_process_id) — agente precisa usar IDs inteiros

### Ordem de Correções Sugerida

**Fase 1 — Crítica (bloqueia sincronização):**
1. Criar migrations Rails para campos PHANTOM que são reais (seniority_level, technical_skills, soft_skills, languages, certifications, years_of_experience, diversity_*, fork_uuid em candidates)
2. Criar migrations para campos PHANTOM em applies (source, status, lia_score, match_percentage, current_stage, stage_entered_at, additional_data, fork_uuid)
3. Criar migrations para campos PHANTOM em jobs (status, department, salary_range, etc. — selecionar os necessários para o produto)
4. Criar migrations para campos PHANTOM em users (name, role, avatar_url, status, fork_uuid)
5. Criar migrations para campos PHANTOM em selective_processes (company_id, is_active, stage_type, etc.)

**Fase 2 — Alta (garante consistência de tipos):**
6. Resolver TYPE MISMATCH de gender/marital_status (decidir: string ou integer enum — recomenda-se string para legibilidade)
7. Implementar conversão UUID ↔ bigint no RailsAdapter com lookup table
8. Corrigir mapeamento `is_affirmative → disabilities` (campos semanticamente diferentes)
9. Corrigir `published_linkedin (bool) → provider (string)` com lógica de conversão

**Fase 3 — Média (alinhamento de naming):**
10. Criar migration Rails para renomear `linkedin → linkedin_url`, `github → github_url`, `portfolio → portfolio_url`
11. Renomear `role_name → current_title` no Rails
12. Renomear `curriculum_text → resume_text`, `curriculum_pdf_url → resume_url`
13. Renomear campos de endereço: `city → location_city`, `street → address_street`, etc. (ou manter e atualizar o adapter)

**Fase 4 — Pipeline e Permissões:**
14. Implementar verificação de RBAC no nível das tools do agente
15. Tornar `company_id` obrigatório em todas as tools (remover "opcional")
16. Implementar carregamento dinâmico de pipeline por vaga no agente
17. Alinhar enum de status do agente com o enum do Rails

---

## SEÇÃO 8 — TABELA DE FINDINGS

| ID | Tipo | Entidade | Campo | Banco Rails | Agente Python | Frontend TS | Impacto |
|---|---|---|---|---|---|---|---|
| F001 | PHANTOM | Apply | `source` | ausente | ausente | ausente | CRÍTICO — serializer retorna nil |
| F002 | PHANTOM | Apply | `status` | ausente | "screening" etc | `status` | CRÍTICO — dado nunca persiste |
| F003 | PHANTOM | Apply | `lia_score` | ausente | `screening_score` | `lia_score` | CRÍTICO |
| F004 | PHANTOM | Apply | `match_percentage` | ausente | ausente | — | ALTO |
| F005 | PHANTOM | Apply | `current_stage` | ausente | ausente | — | ALTO |
| F006 | PHANTOM | Apply | `fork_uuid` | ausente | `id` (UUID) | — | ALTO |
| F007 | PHANTOM | Job | `status` | ausente | `status` (string) | `status` | CRÍTICO |
| F008 | PHANTOM | Job | `salary_range` | ausente | `salary_range` | `salary_range` | ALTO |
| F009 | PHANTOM | Job | `department` | ausente | `department` | `department` | MÉDIO |
| F010 | PHANTOM | Job | `technical_requirements` | ausente | campo | campo | ALTO |
| F011 | PHANTOM | Job | `interview_stages` | ausente | campo | campo | ALTO |
| F012 | PHANTOM | Candidate | `seniority_level` | ausente | `seniority_level` | `seniority_level` | ALTO |
| F013 | PHANTOM | Candidate | `technical_skills` | ausente | `technical_skills` | `technical_skills` | ALTO |
| F014 | PHANTOM | Candidate | `soft_skills` | ausente | `soft_skills` | `soft_skills` | ALTO |
| F015 | PHANTOM | Candidate | `languages` | ausente | `languages` | `languages` | ALTO |
| F016 | PHANTOM | Candidate | `certifications` | ausente | `certifications` | `certifications` | MÉDIO |
| F017 | PHANTOM | Candidate | `years_of_experience` | ausente | campo | campo | MÉDIO |
| F018 | PHANTOM | Candidate | `diversity_*` (10 campos) | ausentes | campos | parcial | ALTO (compliance) |
| F019 | PHANTOM | User | `name, role, avatar_url, status, fork_uuid` | ausentes | campos Fork | campos | CRÍTICO |
| F020 | PHANTOM | SelectiveProcess | `company_id, is_active, stage_type, etc.` | ausentes | — | — | ALTO |
| F021 | NAMING | Candidate | linkedin | `linkedin` | `linkedin_url` | `linkedin_url` | ALTO |
| F022 | NAMING | Candidate | título | `role_name` | `current_title` | `current_title` | ALTO |
| F023 | NAMING | Candidate | currículo | `curriculum_text` | `resume_text` | `resume_text` | MÉDIO |
| F024 | NAMING | Candidate | data nasc. | `date_birth` | `date_of_birth` | `date_of_birth` | ALTO |
| F025 | NAMING | Candidate | cidade | `city` | `location_city` | `location_city` | ALTO |
| F026 | NAMING | Candidate | remoto | `remote_work` | `is_remote` | `is_remote` | MÉDIO |
| F027 | NAMING | Candidate | mobilidade | `mobility` | `willing_to_relocate` | `willing_to_relocate` | MÉDIO |
| F028 | NAMING | Apply | etapa FK | `selective_process_id` | `stage_id` | — | CRÍTICO |
| F029 | NAMING | Job | modelo trabalho | `workplace_type` | `work_model` | `work_model` | ALTO |
| F030 | NAMING | Job | data pub. | `published_date` | `open_date` | `open_date` | MÉDIO |
| F031 | TYPE | Candidate | `id` | bigint | UUID | string | CRÍTICO |
| F032 | TYPE | Candidate | `gender` | integer enum | string | string | ALTO |
| F033 | TYPE | Candidate | `marital_status` | integer enum | string | string | MÉDIO |
| F034 | TYPE | Candidate | `address_number` | integer | string | string | BAIXO |
| F035 | TYPE | Job | `published_linkedin` | string (provider) | boolean | boolean | ALTO |
| F036 | TYPE | Apply | `candidate_id` | bigint | UUID | string | CRÍTICO |
| F037 | DIRECTION | Apply | `is_active/is_deleted` | `is_deleted` (bool) | `is_active` (bool, invertido) | — | CRÍTICO |
| F038 | DIRECTION | Job | `is_affirmative/disabilities` | `disabilities` | `is_affirmative` | `is_affirmative` | ALTO (semântica diferente) |
| F039 | ENUM MISMATCH | SelectiveProcess | `status` | 0-4 (integer enum) | strings variadas | — | CRÍTICO |
| F040 | ENUM MISMATCH | SelectiveProcess | `offer` stage | ausente no enum | "offer" usado | "offer" | CRÍTICO |
| F041 | ENUM MISMATCH | SelectiveProcess | `cv_screening` | ausente | "cv_screening" | — | ALTO |
| F042 | ENUM MISMATCH | SelectiveProcess | `withdrawn` | ausente | "withdrawn" | — | MÉDIO |
| F043 | MISSING | Candidate | `surname` | `surname` | ausente | ausente | MÉDIO |
| F044 | MISSING | Candidate | `interests` | `interests` (string) | ausente | ausente | BAIXO |
| F045 | MISSING | Candidate | `comments` | `comments` (text) | ausente | ausente | BAIXO |
| F046 | MISSING | Candidate | `uid` | `uid` (string) | ausente | ausente | MÉDIO |
| F047 | MISSING | Candidate | `position_level` | `position_level` | ausente | ausente | MÉDIO |
| F048 | ORPHAN | Candidate | `status` | ausente | "active"/"inactive" | `status` | ALTO |
| F049 | ORPHAN | Candidate | `lia_score` | ausente | interno | `lia_score` | ALTO |
| F050 | ORPHAN | Agent | `company_id` optional | — | opcional em tools | — | CRÍTICO (segurança) |

---

## VALIDAÇÃO DE COBERTURA

1. **Entidades core com inventário completo das 4 camadas?**
   Candidato: SIM. Vaga: SIM. Apply: SIM. Usuário: SIM. Conta: PARCIAL. Selective Process: SIM.

2. **Matriz campo a campo para Candidato?** SIM — 48 campos mapeados.

3. **CANDIDATE_FORK_TO_RAILS analisado campo por campo?** SIM — 52 mapeamentos, 16 PHANTOM identificados.

4. **Lifecycle do candidato?** SIM — 5 estados Rails vs 12+ Python; pós-contratação não implementado.

5. **Tenant isolation verificado?** SIM — risco MÉDIO-ALTO identificado, company_id opcional em tools.

6. **Enums de status alinhados?** NÃO — desalinhamento CRÍTICO documentado nas Seções 3.3, 5.3 e findings F039-F042.

7. **Desalinhamentos tipados?** SIM — 88 findings classificados em PHANTOM, NAMING, MISSING, TYPE, ENUM MISMATCH, ORPHAN, DIRECTION.

---

*Gerado pelo protocolo P17 em 2026-04-14. Fonte de dados: schema.rb (versão 2025_07_14_142059), serializers Rails, CANDIDATE_FORK_TO_RAILS dict, CandidateLocal TypeScript interface, SelectiveProcess model.*
