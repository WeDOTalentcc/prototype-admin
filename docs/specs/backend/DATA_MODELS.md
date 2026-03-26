# Data Models — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: `ats_api/db/schema.rb` (Rails 7.1) + models `app/models/*.rb`
> **SPEC-DRIVEN DEVELOPMENT** — entidades, campos, relacionamentos e validações.

---

## 1. Visão Geral do Banco

| Item | Valor |
|------|-------|
| **SGBD** | PostgreSQL |
| **Multi-tenant** | Sim — via `accounts` (Apartment gem pattern) |
| **ORM** | ActiveRecord (Rails 7.1) |
| **Schema version** | `2025_07_14_142059` |
| **Extensions** | `plpgsql` |

---

## 2. Diagrama de Entidades (ER)

```
┌──────────┐      ┌──────────┐      ┌──────────────┐
│ accounts │──1:N─│  users   │──1:N─│    jobs       │
│          │      │          │      │              │
└──────────┘      └────┬─────┘      └──────┬───────┘
                       │                    │
                       │              ┌─────┴──────────┐
                       │              │                 │
                  ┌────┴─────┐  ┌────▼────────┐  ┌────▼────────────┐
                  │user_roles│  │selective_   │  │   applies       │
                  │          │  │processes    │  │                 │
                  └────┬─────┘  └─────────────┘  └───┬─────────────┘
                       │                              │
                  ┌────▼─────┐               ┌───────▼──────┐
                  │  roles   │               │  candidates  │
                  └────┬─────┘               └──────────────┘
                       │
                  ┌────▼─────────┐
                  │role_permissions│
                  └────┬─────────┘
                       │
                  ┌────▼──────┐
                  │permissions│
                  └───────────┘

                  ┌──────────┐
                  │ messages │  (polimórfico via reference_type/reference_id)
                  └──────────┘

                  ┌──────────────┐
                  │ apply_status │  (log de mudanças de etapa)
                  └──────────────┘
```

---

## 3. Entidades Detalhadas

### 3.1 accounts

Representa um tenant (empresa cliente).

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `name` | string | YES | — | — |
| `tenant` | string | YES | — | index |
| `staging_tenant` | string | YES | — | index |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações:** `has_many :users`

### 3.2 users

Usuários (recrutadores) do sistema.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `email` | string | YES | — | index |
| `password_digest` | string | YES | — | — |
| `account_id` | bigint | YES | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações:**
- `belongs_to :account` (optional)
- `has_many :jobs`
- `has_many :user_roles` → `has_many :roles, through: :user_roles`
- `has_many :user_permissions` → `has_many :direct_permissions`

**Validações:** `email` presence, uniqueness (case insensitive)

**Auth:** `has_secure_password` (bcrypt)

**Métodos:**
- `can?(permission_name)` — verifica permissão por role ou direta
- `effective_permissions` — todas as permissões (role + diretas)

### 3.3 jobs

Vagas de emprego.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `title` | string | YES | — | — |
| `description` | text | YES | — | — |
| `user_id` | bigint | NOT NULL | — | FK → users |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `provider` | string | NOT NULL | `""` | index (composto) |
| `provider_job_id` | string | NOT NULL | `""` | index (composto, unique) |
| `company_id` | bigint | YES | — | — |
| `published_date` | datetime | YES | — | — |
| `application_deadline` | datetime | YES | — | — |
| `is_remote` | boolean | YES | — | — |
| `city` | string | YES | — | — |
| `state` | string | YES | — | — |
| `country` | string | YES | — | — |
| `job_url` | string | YES | — | — |
| `career_page_id` | bigint | YES | — | — |
| `career_page_name` | string | YES | — | — |
| `career_page_url` | string | YES | — | — |
| `career_page_logo` | string | YES | — | — |
| `friendly_badge` | boolean | YES | — | — |
| `disabilities` | boolean | YES | — | — |
| `workplace_type` | string | YES | — | — |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações:**
- `belongs_to :user`
- `belongs_to :account` (optional)
- `has_many :selective_processes` (dependent: destroy)

**Validações:** `title` presence, `description` presence

**Callbacks:** `after_create :create_default_selective_processes` — cria 5 etapas padrão

**Índice único:** `[provider, provider_job_id]` — previne duplicação de vagas importadas

### 3.4 candidates

Candidatos.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `uid` | string | YES | — | index |
| `name` | string | YES | — | — |
| `surname` | string | YES | — | — |
| `email` | string | YES | `""` | index |
| `secondary_email` | string | YES | — | — |
| `mobile_phone` | string | YES | — | — |
| `phone` | string | YES | — | — |
| `secondary_phone` | string | YES | — | — |
| `linkedin` | string | YES | — | index |
| `github` | string | YES | — | — |
| `portfolio` | string | YES | — | — |
| `current_company` | string | YES | — | — |
| `role_name` | string | YES | — | — |
| `position_level` | string | YES | — | — |
| `self_introduction` | text | YES | — | — |
| `curriculum_text` | text | YES | — | — |
| `date_birth` | date | YES | — | — |
| `gender` | integer | YES | — | — |
| `nationality` | string | YES | — | — |
| `marital_status` | integer | YES | — | — |
| `cpf` | string | YES | — | — |
| `street` | string | YES | — | — |
| `number` | integer | YES | — | — |
| `district` | string | YES | — | — |
| `zip` | string | YES | — | — |
| `city` | string | YES | — | — |
| `state` | string | YES | — | — |
| `country` | string | YES | — | — |
| `complement` | string | YES | — | — |
| `clt_expectation` | float | YES | `0.0` | — |
| `pj_expectation` | float | YES | `0.0` | — |
| `freelance_expectation` | float | YES | `0.0` | — |
| `current_salary` | float | YES | `0.0` | — |
| `desired_salary` | float | YES | — | — |
| `currency` | string | YES | `"BRL"` | — |
| `remote_work` | boolean | YES | — | — |
| `mobility` | boolean | YES | `true` | — |
| `interests` | string | YES | — | — |
| `comments` | text | YES | — | — |
| `source` | string | YES | — | — |
| `avatar_url` | string | YES | — | — |
| `curriculum_pdf_url` | string | YES | — | — |
| `completed_register` | boolean | YES | `false` | — |
| `accept_terms` | boolean | YES | `false` | — |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações:** `belongs_to :account`

**Validações:**
- `name` presence
- `email` presence, uniqueness
- `cpf` uniqueness (allow_blank)

### 3.5 applies

Candidaturas (vínculo candidato ↔ vaga ↔ etapa).

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `candidate_id` | bigint | NOT NULL | — | FK → candidates |
| `job_id` | bigint | NOT NULL | — | FK → jobs |
| `selective_process_id` | bigint | NOT NULL | — | FK → selective_processes |
| `is_deleted` | boolean | NOT NULL | `false` | — |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações:**
- `belongs_to :candidate`
- `belongs_to :job`
- `belongs_to :selective_process`

**Callbacks:** `before_update :log_selective_process_change` — cria `ApplyStatus` ao mudar de etapa

**Soft delete:** campo `is_deleted` (não remove do banco)

### 3.6 selective_processes

Etapas do pipeline (funil de seleção).

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `name` | string | YES | — | — |
| `position` | integer | YES | — | — |
| `status` | integer | YES | — | — |
| `job_id` | bigint | YES | — | FK → jobs |
| `uid` | string | YES | — | index |
| `sub_status` | jsonb | YES | `[]` | — |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações:** `belongs_to :job`, `belongs_to :account`

**Enum `status`:**

| Valor | Nome | Posição |
|-------|------|---------|
| 0 | `web_submission` | Inscrição Web |
| 1 | `screening` | Triagem |
| 2 | `interview` | Entrevista |
| 3 | `rejected` | Rejeitados |
| 4 | `hired` | Contratados |

**Default process:** 5 etapas criadas automaticamente ao criar uma vaga.

### 3.7 messages

Mensagens do chat (polimórfico).

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `content` | text | YES | — | — |
| `entity` | integer | NOT NULL | `0` | — |
| `is_deleted` | boolean | YES | `false` | — |
| `status` | integer | NOT NULL | `0` | — |
| `parent_message_id` | bigint | YES | — | index |
| `reference_type` | string | NOT NULL | — | index (composto) |
| `reference_id` | bigint | NOT NULL | — | index (composto) |
| `account_id` | bigint | YES | — | FK → accounts |
| `metadata` | jsonb | YES | `{}` | — |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Constantes:**
- `STATUS_NOT_ANSWERED = 0`, `STATUS_ANSWERED = 1`
- `ROLE_SYSTEM = 0`, `ROLE_USER = 1`

**Callbacks:** `after_create_commit :publish_message_event` — publica evento via `MessageService::EventPublisher` (ActionCable)

### 3.8 Tabelas de Permissões

#### roles

| Campo | Tipo |
|-------|------|
| `id` | bigint PK |
| `name` | string NOT NULL, unique |
| `description` | text |

#### permissions

| Campo | Tipo |
|-------|------|
| `id` | bigint PK |
| `name` | string NOT NULL, unique |
| `description` | text |

#### role_permissions

| Campo | Tipo |
|-------|------|
| `role_id` | FK → roles |
| `permission_id` | FK → permissions |
| Unique: `[role_id, permission_id]` |

#### user_roles

| Campo | Tipo |
|-------|------|
| `user_id` | FK → users |
| `role_id` | FK → roles |
| Unique: `[user_id, role_id]` |

#### user_permissions

| Campo | Tipo |
|-------|------|
| `user_id` | FK → users |
| `permission_id` | FK → permissions |
| Unique: `[user_id, permission_id]` |

---

## 4. Concerns Compartilhados

### 4.1 Searchable

Incluído em: Job, Candidate, Apply, User, Message, SelectiveProcess

Implementa busca via Elasticsearch/Searchkick (configurável).

### 4.2 AccountScopable

Escopo automático por `account_id` para multi-tenancy.

---

## 5. Foreign Keys

| Tabela | Campo | Referência |
|--------|-------|-----------|
| applies | candidate_id | candidates(id) |
| applies | job_id | jobs(id) |
| applies | selective_process_id | selective_processes(id) |
| messages | account_id | accounts(id) |
| role_permissions | role_id | roles(id) |
| role_permissions | permission_id | permissions(id) |
| selective_processes | job_id | jobs(id) |
| user_permissions | user_id | users(id) |
| user_permissions | permission_id | permissions(id) |
| user_roles | user_id | users(id) |
| user_roles | role_id | roles(id) |
| users | account_id | accounts(id) |

---

## 6. Índices

| Tabela | Índice | Campos | Unique |
|--------|--------|--------|--------|
| accounts | index_accounts_on_tenant | tenant | No |
| accounts | index_accounts_on_staging_tenant | staging_tenant | No |
| applies | index_applies_on_candidate_id | candidate_id | No |
| applies | index_applies_on_job_id | job_id | No |
| applies | index_applies_on_selective_process_id | selective_process_id | No |
| candidates | index_candidates_on_email | email | No |
| candidates | index_candidates_on_linkedin | linkedin | No |
| candidates | index_candidates_on_uid | uid | No |
| jobs | index_jobs_on_account_id | account_id | No |
| jobs | index_jobs_on_provider_and_job_id | [provider, provider_job_id] | **Yes** |
| jobs | index_jobs_on_user_id | user_id | No |
| messages | index_messages_on_account_id | account_id | No |
| messages | index_messages_on_parent_message_id | parent_message_id | No |
| messages | index_messages_on_reference | [reference_type, reference_id] | No |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Schema | `ats_api/db/schema.rb` |
| Job model | `ats_api/app/models/job.rb` |
| Candidate model | `ats_api/app/models/candidate.rb` |
| Apply model | `ats_api/app/models/apply.rb` |
| User model | `ats_api/app/models/user.rb` |
| SelectiveProcess model | `ats_api/app/models/selective_process.rb` |
| Message model | `ats_api/app/models/message.rb` |
| Account model | `ats_api/app/models/account.rb` |
