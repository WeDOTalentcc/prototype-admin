# DATA_MODELS.md — Modelos de Dados da Plataforma LIA

> **Versão**: 2.0  
> **Última atualização**: 2026-03-26  
> **Fonte**: Código-fonte dos repositórios `ats_api` (Rails 7.1), `lia-agent-system` (FastAPI/SQLAlchemy) e `recruiter_agent_v5` (Python)  
> **Proprietário**: WeDOTalent Engineering

---

## 1. Visão Geral

A Plataforma LIA opera com **duas bases de dados PostgreSQL** em sistemas distintos, conectadas via API interna e RabbitMQ:

| Sistema | Framework | Banco | Propósito |
|---------|-----------|-------|-----------|
| `ats_api` | Rails 7.1 | PostgreSQL | ATS core — vagas, candidatos, aplicações, processos seletivos, autenticação JWT, permissões RBAC |
| `lia-agent-system` | FastAPI + SQLAlchemy (async) | PostgreSQL | IA — agentes ReAct, triagem WSI, opiniões LIA, calibração, comunicação, compliance LGPD, multi-channel |

### 1.1 Convenções globais

| Convenção | `ats_api` (Rails) | `lia-agent-system` (Python) |
|-----------|-------------------|----------------------------|
| **IDs** | Integer autoincrement | UUID v4 (`uuid.uuid4()`) |
| **Timestamps** | `created_at`, `updated_at` (Rails auto) | `datetime.utcnow()` default em Python |
| **Multi-tenancy** | `account_id` (FK integer) | `company_id` (String(255), default `"demo_company"`) — obrigatório em toda query |
| **Soft delete** | `is_deleted: boolean DEFAULT false` | `is_active: boolean` ou `status` enum |
| **JSON columns** | PostgreSQL `jsonb` | PostgreSQL `JSONB` via SQLAlchemy `JSON` type |
| **Naming** | snake_case (Rails convention) | snake_case (Python convention) |
| **ORM** | ActiveRecord | SQLAlchemy 2.0 (async) |
| **Migrations** | Rails migrations `[7.1]` | Alembic |

### 1.2 Padrão de datas

Todas as datas em ISO 8601 UTC: `2026-03-15T10:00:00Z`

---

## 2. Sistema `ats_api` (Rails 7.1)

### 2.1 Diagrama de Entidades

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

### 2.2 Tabela: `accounts`

> **Migration**: `db/migrate/20250630161949_create_accounts.rb`  
> **Multi-tenancy**: Padrão Apartment-like — cada account é um tenant

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `name` | string | YES | — | — |
| `tenant` | string | YES | — | index |
| `staging_tenant` | string | YES | — | index |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações**: `has_many :users`, `has_many :jobs`, `has_many :candidates`, `has_many :applies`, `has_many :selective_processes`

### 2.3 Tabela: `users`

> **Migration**: `db/migrate/20250630164633_create_users.rb` + `add_account_to_users.rb`  
> **Factory**: `spec/factories/users.rb`

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `email` | string | YES | — | index (unique) |
| `password_digest` | string | YES | — | — |
| `account_id` | bigint | YES | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Autenticação**: `has_secure_password` (bcrypt) → JWT: `JWT.encode({ user_id: user.id }, Rails.application.secret_key_base)`  
**Associações**: `belongs_to :account`, `has_many :jobs`, `has_many :user_roles` → `has_many :roles, through: :user_roles`  
**Métodos**: `can?(permission_name)` — verifica permissão por role ou direta; `effective_permissions` — todas as permissões  
**Segurança**: `password_digest` nunca exposto em serializers

### 2.4 Tabela: `jobs`

> **Migration**: `db/migrate/20250630171206_create_jobs.rb` + add_fields  
> **Serializer**: `app/serializer/job_serializer.rb` (`JSONAPI::Serializer`)  
> **Factory**: `spec/factories/jobs.rb`

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

**Serializer attributes (JSONAPI)**:

```ruby
attributes(
  :id, :title, :description, :user_id, :account_id,
  :created_at, :updated_at, :provider, :provider_job_id,
  :company_id, :published_date, :application_deadline,
  :is_remote, :city, :state, :country, :job_url,
  :career_page_id, :career_page_name, :career_page_url,
  :career_page_logo, :friendly_badge, :disabilities, :workplace_type
)
```

**Índice único composto**: `[provider, provider_job_id]` — impede duplicação de vagas importadas  
**Callbacks**: `after_create :create_default_selective_processes` — cria 5 etapas padrão  
**Elasticsearch**: `Job.reindex` obrigatório após create/update para full-text search

### 2.5 Tabela: `candidates`

> **Factory**: `spec/factories/candidates.rb` (45+ campos)

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
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Validações**: `name` presence; `email` presence + uniqueness; `cpf` uniqueness (allow_blank)

### 2.6 Tabela: `evaluations`

Avaliações de candidatos criadas por recrutadores ou pelo agente IA.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `candidate_id` | bigint | NOT NULL | — | FK → candidates |
| `job_id` | bigint | YES | — | FK → jobs |
| `evaluator_id` | bigint | YES | — | FK → users |
| `score` | integer | YES | — | — |
| `comments` | text | YES | — | — |
| `evaluation_type` | string | YES | — | — |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Associações**: `belongs_to :candidate`, `belongs_to :job`, `belongs_to :user (evaluator)`  
**Endpoints**: CRUD completo via `/v1/users/evaluations`  
**Tool YAML**: `evaluations_search.yml`, `evaluations_create.yml`, `evaluations_update.yml`, `evaluations_delete.yml`

### 2.7 Tabela: `questions`

Perguntas de avaliação associadas a vagas ou processos seletivos.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `content` | text | YES | — | — |
| `question_type` | string | YES | — | — |
| `job_id` | bigint | YES | — | FK → jobs |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Endpoints**: CRUD via `/v1/users/questions`  
**Tool YAML**: `questions_search.yml`, `questions_create.yml`, `questions_update.yml`, `questions_delete.yml`

### 2.8 Tabela: `sourced_profiles`

Perfis de candidatos captados via sourcing ativo (Pearch AI, LinkedIn, etc.)  
antes de serem convertidos em `candidates`.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `name` | string | YES | — | — |
| `email` | string | YES | — | index |
| `linkedin` | string | YES | — | index |
| `headline` | string | YES | — | — |
| `current_company` | string | YES | — | — |
| `location` | string | YES | — | — |
| `source` | string | YES | — | — |
| `raw_data` | jsonb | YES | `{}` | — |
| `converted` | boolean | YES | `false` | — |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Endpoints**: `/v1/users/sourced_profile_sourcings` (search, create), `/v1/users/sourced_profiles/import` (batch import), `/v1/users/sourced_profiles/convert` (convert to candidates)

### 2.9 Tabela: `sourced_profile_sourcings`

Relação entre buscas de sourcing e perfis encontrados.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `sourced_profile_id` | bigint | NOT NULL | — | FK → sourced_profiles |
| `job_id` | bigint | YES | — | FK → jobs |
| `search_query` | text | YES | — | — |
| `match_score` | float | YES | — | — |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |

### 2.10 Tabela: `lists`

Listas customizadas de candidatos criadas por recrutadores (talent pools, shortlists).

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `name` | string | NOT NULL | — | — |
| `description` | text | YES | — | — |
| `list_type` | string | YES | — | — |
| `user_id` | bigint | NOT NULL | — | FK → users |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Endpoints**: `/v1/users/lists` (search)  
**Tool YAML**: `lists_search.yml`

### 2.11 Tabela: `list_relationships`

Associação many-to-many entre listas e candidatos.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `list_id` | bigint | NOT NULL | — | FK → lists |
| `candidate_id` | bigint | NOT NULL | — | FK → candidates |
| `created_at` | datetime | NOT NULL | — | — |

**Endpoints**: `/v1/users/list_relationships` (create)  
**Tool YAML**: `list_relationships_create.yml`

### 2.12 Tabela: `talent_pool`

Pool de talentos para busca passiva.

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `candidate_id` | bigint | NOT NULL | — | FK → candidates |
| `tags` | jsonb | YES | `[]` | — |
| `notes` | text | YES | — | — |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |

**Endpoints**: `/v1/users/talent_pool` (search)  
**Tool YAML**: `talent_pool_search.yml`

### 2.13 Tabela: `organizational_structure`

Estrutura organizacional (times, hierarquia).

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `data` | jsonb | YES | `{}` | — |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |

**JSON structure**: `{ "directManager": "...", "teamSize": 5, "teamComposition": [...] }`  
**Endpoints**: `/v1/users/organizational_structure` (create)  
**Tool YAML**: `organizational_structure_create.yml`

### 2.14 Tabela: `applies`

> **Migration**: `db/migrate/20250714142059_create_applies.rb`  
> **Serializer**: `app/serializer/apply_serializer.rb`

| Campo | Tipo | Null | Default | Índice |
|-------|------|------|---------|--------|
| `id` | bigint | NOT NULL | auto | PK |
| `candidate_id` | bigint | NOT NULL | — | FK → candidates |
| `job_id` | bigint | NOT NULL | — | FK → jobs |
| `selective_process_id` | bigint | NOT NULL | — | FK → selective_processes |
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `is_deleted` | boolean | NOT NULL | `false` | — |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Soft delete**: `apply.update(is_deleted: true)` — nunca `.destroy`  
**Callbacks**: `before_update :log_selective_process_change` — cria `ApplyStatus` ao mudar de etapa

### 2.7 Tabela: `selective_processes`

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
| `account_id` | bigint | NOT NULL | — | FK → accounts |
| `created_at` | datetime | NOT NULL | — | — |
| `updated_at` | datetime | NOT NULL | — | — |

**Enum `status`**:

| Valor | Nome | Descrição |
|-------|------|-----------|
| 0 | `web_submission` | Inscrição Web |
| 1 | `screening` | Triagem |
| 2 | `interview` | Entrevista |
| 3 | `rejected` | Rejeitados |
| 4 | `hired` | Contratados |

**Default**: 5 etapas criadas automaticamente via callback `after_create` em Job

### 2.8 Tabela: `messages`

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

**Constantes**: `STATUS_NOT_ANSWERED = 0`, `STATUS_ANSWERED = 1`; `ROLE_SYSTEM = 0`, `ROLE_USER = 1`  
**Callbacks**: `after_create_commit :publish_message_event` — publica via ActionCable

### 2.9 Tabelas de Permissões RBAC

#### `roles`

| Campo | Tipo | Constraint |
|-------|------|-----------|
| `id` | bigint PK | |
| `name` | string | NOT NULL, unique |
| `description` | text | |

#### `permissions`

| Campo | Tipo | Constraint |
|-------|------|-----------|
| `id` | bigint PK | |
| `name` | string | NOT NULL, unique |
| `description` | text | |

#### `role_permissions` (join)

| Campo | Tipo | Constraint |
|-------|------|-----------|
| `role_id` | FK → roles | unique `[role_id, permission_id]` |
| `permission_id` | FK → permissions | |

#### `user_roles` (join)

| Campo | Tipo | Constraint |
|-------|------|-----------|
| `user_id` | FK → users | unique `[user_id, role_id]` |
| `role_id` | FK → roles | |

#### `user_permissions` (join — permissões diretas)

| Campo | Tipo | Constraint |
|-------|------|-----------|
| `user_id` | FK → users | unique `[user_id, permission_id]` |
| `permission_id` | FK → permissions | |

### 2.10 Concerns Compartilhados (Rails)

| Concern | Incluído em | Função |
|---------|-------------|--------|
| `Searchable` | Job, Candidate, Apply, User, Message, SelectiveProcess | Full-text search via Elasticsearch/Searchkick |
| `AccountScopable` | Todos os models com `account_id` | Escopo automático por tenant |

### 2.11 Índices

| Tabela | Índice | Campos | Unique |
|--------|--------|--------|--------|
| accounts | `index_accounts_on_tenant` | tenant | No |
| accounts | `index_accounts_on_staging_tenant` | staging_tenant | No |
| applies | `index_applies_on_candidate_id` | candidate_id | No |
| applies | `index_applies_on_job_id` | job_id | No |
| applies | `index_applies_on_selective_process_id` | selective_process_id | No |
| candidates | `index_candidates_on_email` | email | No |
| candidates | `index_candidates_on_linkedin` | linkedin | No |
| candidates | `index_candidates_on_uid` | uid | No |
| jobs | `index_jobs_on_account_id` | account_id | No |
| jobs | `index_jobs_on_provider_and_job_id` | [provider, provider_job_id] | **Yes** |
| jobs | `index_jobs_on_user_id` | user_id | No |
| messages | `index_messages_on_account_id` | account_id | No |
| messages | `index_messages_on_parent_message_id` | parent_message_id | No |
| messages | `index_messages_on_reference` | [reference_type, reference_id] | No |

### 2.12 Foreign Keys

| Tabela | Campo | Referência |
|--------|-------|-----------|
| applies | candidate_id | candidates(id) |
| applies | job_id | jobs(id) |
| applies | selective_process_id | selective_processes(id) |
| applies | account_id | accounts(id) |
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

## 3. Sistema `lia-agent-system` (FastAPI + SQLAlchemy)

### 3.1 Diagrama de Relacionamentos

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   companies     │────<│  job_vacancies   │>────│ vacancy_        │
│ (company_       │     │   (60+ campos)   │     │ candidates      │
│  profiles)      │     └──────┬───────────┘     └────────┬────────┘
└─────────────────┘            │                          │
                        ┌──────┴──────┐                   │
                        │             │                   │
               ┌────────▼────────┐    │          ┌────────▼────────┐
               │ interview_      │    │          │   candidates    │
               │ stages          │    │          │   (55+ campos)  │
               └─────────────────┘    │          └────────┬────────┘
                                      │                   │
                              ┌───────▼───────┐   ┌──────┴───────┐
                              │ recruitment_  │   │              │
                              │ stages        │   │  ┌───────────▼──────────┐
                              └───────────────┘   │  │ candidate_           │
                                                  │  │ experiences          │
                              ┌───────────────────┘  └────────────────────┘
                              │
                     ┌────────▼────────┐     ┌─────────────────────┐
                     │ voice_screening │────>│ voice_screening_    │
                     │ _calls          │     │ analyses            │
                     └────────┬────────┘     └─────────────────────┘
                              │
                     ┌────────▼────────┐     ┌─────────────────────┐
                     │  lia_opinions   │     │ calibration_        │
                     └─────────────────┘     │ sessions/feedback   │
                                             └─────────────────────┘
```

**Nota sobre importações**: Todos os arquivos em `app/models/*.py` são shims que re-exportam
os modelos reais via `from lia_models.<module> import *`. Os modelos definidos de facto estão em
`lia-agent-system/libs/models/lia_models/`. Os paths abaixo referem o shim para consistência de import,
mas as definições de campos vêm da lib interna.

### 3.2 Tabela: `job_vacancies` (60+ campos)

> **Model**: `lia-agent-system/app/models/job_vacancy.py` → `libs/models/lia_models/job_vacancy.py`

#### Identidade e controle

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | `uuid.uuid4()` |
| `company_id` | String(255) | Sim | Tenant — empresa dona da vaga (default: `"demo_company"`) |
| `status` | String(50) | Não | default `"Rascunho"` — valores em PT: `Ativa`, `Rascunho`, `Pausada`, `Concluída`, etc. (free string, sem enum constraint) |
| `stage` | String(50) | Não | default `"Planejamento"` — `Planejamento`, `Aprovação`, `Publicada`, etc. |
| `priority` | String(20) | Não | default `"média"` — `alta`, `média`, `baixa` |
| `urgency_level` | Integer | Não | default `3` (1-5) |
| `created_by` | String(255) | Não | Usuário que criou via LIA |

#### Descrição do cargo

Fonte: `libs/models/lia_models/job_vacancy.py` linhas 27-34

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `title` | String(255) | Sim | Título da vaga |
| `description` | Text | Não | Descrição completa |
| `department` | String(100) | Não | Departamento |
| `seniority_level` | String(50) | Não | `Júnior`, `Pleno`, `Sênior`, `Especialista` |
| `employment_type` | String(50) | Não | `CLT`, `PJ`, `Temporary` |
| `work_model` | String(50) | Não | `presencial`, `híbrido`, `remoto` |
| `location` | String(255) | Não | Localização (campo único, não normalizado) |

#### Requisitos

Fonte: `libs/models/lia_models/job_vacancy.py` linhas 36-48

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `requirements` | ARRAY(String) | Não | Requisitos básicos (legacy) |
| `technical_requirements` | JSON | Não | `[{"category": "Linguagens", "technology": "Python", "level": "Avançado", "required": true}]` |
| `behavioral_competencies` | JSON | Não | `[{"competency": "Liderança", "weight": "Essencial"}]` |
| `languages` | JSON | Não | `[{"language": "Inglês", "level": "Intermediário", "required": true}]` |

#### Financeiro

Fonte: `libs/models/lia_models/job_vacancy.py` linhas 49-57

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `salary` | String(100) | Não | Formato legacy (string) |
| `salary_range` | JSON | Não | `{"min": 12000, "max": 18000, "currency": "BRL"}` |
| `bonus_range` | JSON | Não | `{"min": 5000, "max": 8000, "currency": "BRL"}` |
| `benefits` | ARRAY(String) | Não | `["VR", "VT", "Plano de Saúde"]` |

#### Pipeline e IA

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `interview_stages` | JSON | Não | Estágios customizados do pipeline |
| `total_candidates` | Integer | Não | Contador de candidatos |
| `sourcing_status` | String(50) | Não | Status de sourcing ativo |
| `screening_criteria` | JSON | Não | Critérios de triagem automática |
| `evaluation_rubric` | JSON | Não | Rubrica BARS de avaliação |
| `ideal_profile` | JSON | Não | Perfil ideal gerado pela LIA |
| `scoring_weights` | JSON | Não | Pesos de scoring WSI |
| `affirmative_criteria` | JSON | Não | Critérios afirmativos (DEI) |
| `hiring_policy_id` | UUID (FK) | Não | Política de contratação |

#### Publicação

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `published_at` | DateTime | Não | Data de publicação |
| `deadline` | DateTime | Não | Prazo para candidaturas |
| `external_url` | String | Não | URL em job board externo |
| `career_page_published` | Boolean | Não | Publicado na career page |
| `job_boards` | JSON | Não | Boards onde foi publicado |

### 3.3 Tabela: `candidates` (55+ campos)

> **Model**: `lia-agent-system/app/models/candidate.py` → `libs/models/lia_models/candidate.py`

#### Identidade

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | |
| `company_id` | String(255) | Sim | Tenant |
| `external_id` | String | Não | ID no ATS Rails (`ats_api`) |
| `source` | String(100) | Não | `pearch`, `linkedin`, `manual`, `career_page`, `referral` |
| `source_detail` | String(255) | Não | Detalhe da origem |

#### Dados pessoais (PII — protegidos por LGPD)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `name` | String(255) | Sim | Nome completo — mascarado em logs (`install_global_pii_masking`) |
| `email` | String(255) | Não | Email — mascarado em logs |
| `phone` | String(50) | Não | Telefone — mascarado em logs |
| `cpf` | String(14) | Não | CPF — mascarado em logs |
| `linkedin_url` | String | Não | URL do LinkedIn |
| `photo_url` | String | Não | URL da foto |
| `location_city` | String(100) | Não | |
| `location_state` | String(100) | Não | |
| `location_country` | String(100) | Não | |
| `date_of_birth` | Date | Não | |
| `gender` | String(20) | Não | Anonimizado em avaliações LLM (`anonymize_for_llm`) |
| `ethnicity` | String(50) | Não | Uso exclusivo para métricas DEI — nunca exposto ao LLM |
| `disability` | String(100) | Não | PcD — critério afirmativo |

#### Dados profissionais

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `headline` | String(500) | Não | "Senior Python Engineer @ Company" |
| `current_title` | String(255) | Não | Cargo atual |
| `current_company` | String(255) | Não | Empresa atual |
| `years_experience` | Integer | Não | Anos de experiência |
| `education_level` | String(100) | Não | Escolaridade |
| `skills` | JSON | Não | `["Python", "FastAPI", "PostgreSQL"]` |
| `languages` | JSON | Não | Idiomas com proficiência |
| `salary_expectation` | Float | Não | Pretensão salarial |
| `salary_currency` | String(10) | Não | |
| `availability` | String(50) | Não | Disponibilidade para início |
| `resume_url` | String | Não | URL do CV |
| `resume_text` | Text | Não | CV extraído (texto plano) |
| `summary` | Text | Não | Resumo gerado pela LIA |

#### IA e busca

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `lia_score` | Float | Não | Score geral LIA (0-100) |
| `match_score` | Float | Não | Score de match com vaga |
| `archetype` | String(100) | Não | Arquétipo identificado |
| `tags` | JSON | Não | Tags automáticas |
| _nota_ | — | — | pgvector é usado para busca semântica via `CandidateSearch`, não diretamente na tabela `candidates` |

**Anonimização para LLM**: Antes de enviar candidatos ao LLM, `anonymize_for_llm()` substitui campos PII:

```python
anonymize_for_llm(candidates)
# → [{"candidate_code": "C001", "skills": [...], "score": 85}]
# Remove: name, email, cpf, gender, ethnicity
```

### 3.4 Tabela: `vacancy_candidates` (Tabela de junção)

> **Model**: `libs/models/lia_models/candidate.py` (class `VacancyCandidate`, linha 356)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | `uuid.uuid4()` |
| `vacancy_id` | UUID | Sim | `index=True` |
| `candidate_id` | UUID | Sim | `index=True` |
| `company_id` | String(255) | Sim | default `"demo_company"`, `index=True` |
| `source` | String(50) | Sim | default `"local"` |
| `origin` | String(50) | Não | default `"web"`, `index=True` |
| `lia_score` | Float | Não | Score LIA |
| `match_percentage` | Float | Não | Percentual de match |
| `status` | String(50) | Não | default `"sourced"`, `index=True` |
| `stage` | String(50) | Não | default `"initial"`, `index=True` |
| `added_by` | String(255) | Não | |
| `notes` | Text | Não | |
| `additional_data` | JSON | Não | default `{}` |
| `rejected_by_human` | Boolean | Não | LGPD art. 20 — Human Review Gate (L3) |
| `human_reviewer_id` | String(255) | Não | |
| `scheduled_deletion_at` | DateTime | Não | LGPD retention policy, `index=True` |
| `stage_entered_at` | DateTime | Não | Quando entrou no estágio atual, `index=True` |
| `created_at` | DateTime | Auto | `default=datetime.utcnow`, `index=True` |
| `updated_at` | DateTime | Auto | `default=datetime.utcnow, onupdate=datetime.utcnow` |

**Unique constraint**: `uq_vacancy_candidate (vacancy_id, candidate_id)`

#### Progressão de estágios (`STAGE_PROGRESSION_ORDER`)

Definido em `lia-agent-system/app/api/v1/candidates.py`:

| Rank | Estágio | Aliases aceitos |
|------|---------|-----------------|
| 0 | Sourcing | `sourcing`, `funil`, `funnel`, `sourced`, `novo`, `new` |
| 1 | Triagem | `triagem`, `screening`, `cv aprovado`, `cv review`, `pre-triagem` |
| 2 | Entrevista RH | `entrevista rh`, `interview_hr`, `entrevista inicial` |
| 3 | Entrevista Técnica | `entrevista técnica`, `technical interview`, `technical` |
| 4 | Entrevista Final | `entrevista final`, `final interview`, `entrevista gestor`, `manager interview` |
| 5 | Proposta | `proposta`, `offer`, `oferta`, `proposta enviada` |
| 6 | Aceito | `aceito`, `accepted`, `contratado`, `hired`, `admitido`, `contratação` |
| -1 | Rejeição | `reprovado`, `rejected`, `descartado`, `discarded`, `dropout`, `cancelado`, `arquivado` |
| -2 | Desconhecido | Qualquer stage não mapeado — transição tratada como neutral |

**Lógica de feedback automático** (`determine_feedback_action`):

```python
stage_to = "rejected" → return "reject"
rank_to > rank_from   → return "advance"
rank_to < rank_from   → return "reject"
else                   → return "neutral"
```

### 3.5 Tabela: `recruitment_stages`

> **Model**: `lia-agent-system/app/models/recruitment_stages.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | |
| `vacancy_id` | UUID (FK) | Sim | |
| `company_id` | String(255) | Sim | Tenant |
| `name` | String(100) | Sim | Nome do estágio |
| `stage_type` | String(50) | Sim | `sourcing`, `screening`, `interview`, `offer`, `hired` |
| `order_index` | Integer | Sim | Posição no pipeline |
| `is_active` | Boolean | Sim | |
| `automation_rules` | JSON | Não | Regras de automação por estágio |
| `screening_questions` | JSON | Não | Perguntas de triagem do estágio |
| `created_at` | DateTime | Auto | |
| `updated_at` | DateTime | Auto | |

**Sub-model: `CandidateStageHistory`** — audit trail de todas as transições:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID (PK) | |
| `vacancy_candidate_id` | UUID (FK) | |
| `from_stage` | String(100) | Estágio de origem |
| `to_stage` | String(100) | Estágio de destino |
| `changed_by` | UUID | User ID ou `"lia"` (automático) |
| `reason` | Text | Motivo da transição |
| `created_at` | DateTime | Quando a transição ocorreu |

### 3.6 Tabela: `voice_screening_calls`

> **Model**: `lia-agent-system/app/models/voice_screening.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | |
| `candidate_id` | UUID (FK) | Sim | |
| `job_vacancy_id` | UUID (FK) | Não | |
| `company_id` | String(255) | Sim | Tenant |
| `call_provider` | String(50) | Sim | `openmic`, `twilio`, `vapi` |
| `provider_call_id` | String(255) | Não | ID no provedor |
| `status` | String(50) | Sim | `scheduled`, `in_progress`, `completed`, `failed`, `no_answer` |
| `scheduled_at` | DateTime | Não | |
| `started_at` | DateTime | Não | |
| `ended_at` | DateTime | Não | |
| `duration_seconds` | Integer | Não | |
| `recording_url` | String | Não | |
| `transcript` | Text | Não | Transcrição completa |
| `language` | String(10) | Não | `pt-BR`, `en-US` |
| `questions_asked` | JSON | Não | |
| `candidate_answers` | JSON | Não | |

### 3.7 Tabela: `voice_screening_analyses`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | |
| `screening_call_id` | UUID (FK) | Sim | `→ voice_screening_calls.id` |
| `analysis_model` | String(100) | Não | `claude-sonnet-4-20250514`, `gemini-2.5-flash` |
| `tech_skills_mentioned` | JSON | Não | Skills que o candidato mencionou |
| `tech_skills_matched` | JSON | Não | Skills que batem com a vaga |
| `tech_skills_missing` | JSON | Não | Skills da vaga não mencionadas |
| `tech_score` | Integer | Não | Score técnico (0-100) |
| `comm_clarity` | String(20) | Não | `baixa`, `média`, `alta` |
| `comm_confidence` | String(20) | Não | |
| `comm_score` | Integer | Não | Score comunicação (0-100) |
| `fit_motivation` | Text | Não | Análise de motivação |
| `fit_red_flags` | JSON | Não | Red flags |
| `fit_green_flags` | JSON | Não | Green flags |
| `fit_score` | Integer | Não | Score fit cultural (0-100) |

### 3.8 Tabela: `lia_opinions` (Pareceres da IA)

> **Model**: `lia-agent-system/app/models/lia_opinion.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | |
| `candidate_id` | UUID (FK) | Sim | |
| `job_vacancy_id` | UUID (FK) | Não | Se WSI, referência à vaga |
| `opinion_type` | String(50) | Sim | `general`, `wsi` |
| `source` | String(50) | Sim | `cv_analysis`, `voice_screening`, `interview`, `composite` |
| `score` | Float | Não | Score geral (0-100) |
| `wsi_score` | Float | Não | Score WSI (0-100) |
| `recommendation` | String(50) | Não | `approved`, `pending_review`, `not_approved` |
| `summary` | Text | Não | Resumo do parecer |
| `archetype` | String(100) | Não | "Executor Pragmático", "Inovador Técnico", etc. |
| `score_breakdown` | JSON | Não | `{"technical": 85, "communication": 70, "cultural_fit": 90}` |
| `technical_analysis` | JSON | Não | Análise técnica detalhada |
| `behavioral_analysis` | JSON | Não | Análise comportamental |
| `cultural_fit` | JSON | Não | |
| `strengths` | JSON | Não | Pontos fortes |
| `concerns` | JSON | Não | Preocupações |
| `gaps` | JSON | Não | Gaps identificados |
| `matched_skills` | JSON | Não | Skills que batem |
| `missing_skills` | JSON | Não | Skills faltantes |
| `next_steps` | Text | Não | Próximos passos sugeridos |
| `recruiter_notes` | Text | Não | Notas do recrutador (HITL) |
| `recruiter_override` | String(50) | Não | Override: `approved`, `rejected` |
| `recruiter_override_reason` | Text | Não | Motivo do override |
| `is_current` | Boolean | Sim | Versão atual do parecer |
| `version` | Integer | Sim | Versionamento (1, 2, 3...) |

**Versionamento**: Ao gerar novo parecer, `is_current=False` no anterior, `version += 1` no novo.

### 3.9 Tabela: `calibration_feedback`

> **Model**: `lia-agent-system/app/models/calibration.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | String (PK) | Sim | |
| `vacancy_id` | String | Não | |
| `search_session_id` | String | Não | |
| `candidate_id` | String | Sim | |
| `user_id` | String | Sim | |
| `feedback` | String | Sim | `like`, `dislike`, `neutral` |
| `reason` | String | Não | Motivo |
| `candidate_snapshot` | JSON | Não | Snapshot do candidato no momento |
| `created_at` | DateTime | Auto | |

### 3.10 Tabela: `calibration_sessions`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | String (PK) | Sim | |
| `vacancy_id` | String | Não | |
| `user_id` | String | Sim | |
| `search_criteria` | JSON | Não | Critérios de busca originais |
| `status` | String | Sim | `awaiting_feedback`, `learning`, `confirmed`, `completed` |
| `total_shown` | Integer | Sim | Candidatos mostrados |
| `likes_count` | Integer | Sim | Total de likes |
| `dislikes_count` | Integer | Sim | Total de dislikes |
| `learned_criteria` | JSON | Não | Critérios aprendidos pela IA |
| `min_feedbacks_required` | Integer | Sim | Mínimo de feedbacks (default: 5) |
| `sourcing_blocked` | Boolean | Sim | Sourcing bloqueado até calibrar |
| `confirmation_message` | Text | Não | |

### 3.11 Tabela: `data_request_templates`

> **Model**: `lia-agent-system/app/models/data_request.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID (PK) | Sim | |
| `company_id` | String(255) | Sim | |
| `name` | String(255) | Sim | Nome do template |
| `description` | Text | Não | |
| `trigger_stage` | String(100) | Não | Estágio que dispara o template |
| `trigger_type` | Enum | Sim | `manual`, `automatic`, `stage_entry`, `stage_exit` |
| `is_blocking` | Boolean | Não | Bloqueia avanço no pipeline |
| `expiration_days` | Integer | Sim | Dias para expirar (default: 7) |
| `fields` | JSON | Não | Schema dos campos |
| `is_active` | Boolean | Sim | |
| `is_default` | Boolean | Não | |

**Tipos de campos para `fields`**:

| Tipo | Descrição | Validação |
|------|-----------|-----------|
| `text` | Texto simples | — |
| `cpf` | CPF | Módulo 11 |
| `cnpj` | CNPJ | Módulo 11 |
| `email` | Email | RFC 5322 |
| `phone` | Telefone | Formato BR |
| `date` | Data | ISO 8601 |
| `number` | Número | Min/Max |
| `currency` | Valor monetário | 2 decimais |
| `file` | Upload de arquivo | Extensão + tamanho |
| `photo` | Upload de foto | JPEG/PNG |
| `address` | Endereço completo | CEP lookup |
| `select` | Seleção única | Lista de opções |
| `multi_select` | Seleção múltipla | Lista de opções |
| `textarea` | Texto longo | — |

---

## 4. Tabelas de Comunicação

| Tabela | Descrição | Campos-chave |
|--------|-----------|--------------|
| `communication_history` | Histórico de todas as comunicações | `candidate_id`, `channel`, `direction`, `content`, `status` |
| `email_templates` | Templates de email da empresa | `company_id`, `name`, `subject`, `body`, `variables` |
| `recruitment_email_templates` | Templates de email de recrutamento | `company_id`, `stage`, `template_type`, `content` |
| `whatsapp_conversations` | Conversas WhatsApp | `candidate_id`, `phone`, `messages`, `status` |
| `message_queue` | Fila de mensagens assíncronas | `channel`, `recipient`, `payload`, `status`, `retry_count` |
| `pending_approvals` | Comunicações pendentes de aprovação HITL | `candidate_id`, `channel`, `content`, `approved_by` |
| `candidate_opt_outs` | Opt-outs de comunicação | `candidate_id`, `channel`, `opted_out_at` |
| `candidate_quarantine` | Candidatos em quarentena de comunicação | `candidate_id`, `reason`, `until` |

---

## 5. Tabelas de Configuração e Admin

| Tabela | Descrição | Campos-chave |
|--------|-----------|--------------|
| `companies` / `company_profiles` | Dados das empresas | `id`, `name`, `industry`, `size`, `settings` |
| `company_benefits` | Benefícios padrão | `company_id`, `name`, `category`, `description` |
| `company_culture` | Cultura organizacional | `company_id`, `values`, `mission`, `work_style` |
| `screening_questions` | Perguntas de triagem padrão | `company_id`, `question`, `type`, `required` |
| `pipeline_templates` | Templates de pipeline | `company_id`, `name`, `stages`, `is_default` |
| `global_policies` | Políticas globais | `company_id`, `policy_type`, `rules`, `is_active` |
| `rubrics` | Rubricas BARS de avaliação | `company_id`, `vacancy_id`, `criteria`, `levels` |
| `admin_settings` | Configurações gerais | `company_id`, `key`, `value`, `category` |
| `guardrails` | Guardrails de agentes IA | `company_id`, `agent_domain`, `rules`, `is_active` |

---

## 6. Tabelas de Compliance e Auditoria

| Tabela | Descrição | Framework |
|--------|-----------|-----------|
| `audit_logs` | Log de ações auditáveis | SOX / ISO 27001 |
| `lgpd_consents` | Consentimentos LGPD | LGPD |
| `data_subject_requests` | Solicitações DSAR | LGPD art. 18 |
| `bias_audit_reports` | Relatórios Four-Fifths Rule | EU AI Act |
| `fairness_reports` | Métricas de equidade por pipeline | DEI |
| `risk_register` | Registro de riscos IA | EU AI Act high-risk |

---

## 7. Autenticação e Multi-tenancy

### 7.1 `ats_api` — JWT direto

```ruby
# Login: POST /v1/sessions
token = JWT.encode({ user_id: user.id }, Rails.application.secret_key_base)
# Validação: before_action → decode JWT → Current.user = user
```

### 7.2 `lia-agent-system` — WorkOS SSO

```python
class User(Base):
    id: UUID
    workos_user_id: str
    email: str
    name: str
    role: UserRole           # admin, recruiter, viewer, hiring_manager
    company_id: String(255)  # Tenant obrigatório (default: "demo_company")
    is_active: bool
    last_login: datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"
    HIRING_MANAGER = "hiring_manager"
```

**Dependencies de autenticação**:

| Dependency | Uso |
|-----------|-----|
| `get_current_user` | Requer token válido — 401 se ausente |
| `get_current_active_user` | + `is_active=True` |
| `get_current_user_or_demo` | Aceita token ou cria user demo (dev) |
| `get_user_company_id` | Extrai `company_id` do user |

### 7.3 Regras de isolamento multi-tenant

| Regra | Enforcement |
|-------|-------------|
| Nunca retornar dados de outro tenant | Filtro `company_id` / `account_id` em toda query |
| Cross-tenant queries proibidas | Sem exceção |
| PII isolados por tenant | Candidatos pertencem ao tenant que os criou |
| Audit trail por tenant | Logs incluem `company_id` |

---

## 8. Busca e Indexação

| Tecnologia | Sistema | Uso |
|------------|---------|-----|
| **Elasticsearch** | `ats_api` | Full-text search em Job, Candidate (Searchkick) |
| **pgvector** | `lia-agent-system` | Busca semântica — `Vector(1536)`, cosine distance `<=>` |
| **BM25 + pgvector** | `lia-agent-system` | Hybrid search — full-text + semântico combinados |
| **Pearch AI** | `lia-agent-system` | API externa — 190M+ perfis, 2-tier (local free → global paid) |
| **Embedding cache** | `lia-agent-system` | Warm-up no startup, `embedding_cache_service` |

---

## 9. Migrations

### 9.1 Rails (`ats_api`)

| Regra | Correto | Errado |
|-------|---------|--------|
| Versão | `ActiveRecord::Migration[7.1]` | Sem versão |
| FKs | `null: false, foreign_key: true` | Sem null constraint |
| Soft delete | `t.boolean :is_deleted, default: false, null: false` | `DROP` de dados |
| Nomenclatura | `YYYYMMDDHHMMSS_verbo_substantivo.rb` | Nomes genéricos |
| Atomicidade | Uma responsabilidade por migration | Misturar operações |

### 9.2 Python (`lia-agent-system`)

| Regra | Correto | Errado |
|-------|---------|--------|
| PKs | `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4` | Integer |
| Campos obrigatórios | `nullable=False` | Sem constraint |
| Índices | `index=True` em campos de busca (`company_id`, `status`, `email`) | Sem índice |
| Timestamps | `default=datetime.utcnow` | `datetime.utcnow()` em Python |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Schema Rails | `ats_api/db/schema.rb` |
| Job model (Rails) | `ats_api/app/models/job.rb` |
| Candidate model (Rails) | `ats_api/app/models/candidate.rb` |
| Apply model (Rails) | `ats_api/app/models/apply.rb` |
| User model (Rails) | `ats_api/app/models/user.rb` |
| Job Vacancy model (Python) | `lia-agent-system/app/models/job_vacancy.py` |
| Candidate model (Python) | `lia-agent-system/app/models/candidate.py` |
| LIA Opinion model (Python) | `lia-agent-system/app/models/lia_opinion.py` |
| Calibration model (Python) | `lia-agent-system/app/models/calibration.py` |
| Voice Screening model (Python) | `lia-agent-system/app/models/voice_screening.py` |
| Data Request model (Python) | `lia-agent-system/app/models/data_request.py` |
| Auth models (Python) | `lia-agent-system/app/auth/models.py` |
| DATABASE_FIELDS_REFERENCE | `docs/architecture/core/DATABASE_FIELDS_REFERENCE.md` |
| BACKEND_STANDARDS | `docs/specs/standards/BACKEND_STANDARDS.md` |
