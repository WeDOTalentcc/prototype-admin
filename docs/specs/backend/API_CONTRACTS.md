# API Contracts — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: `ats_api/config/routes.rb` + controllers + `recruiter_agent_v5/documentation/*.yml`
> **SPEC-DRIVEN DEVELOPMENT** — contratos REST entre todos os serviços.

---

## 1. Visão Geral das Integrações

```
ats_front (Nuxt 3)
    │
    ├── REST ──▶ ats_api (Rails) ──▶ PostgreSQL
    │
    ├── WebSocket (ActionCable) ◀── ats_api (push)
    │
    └── RabbitMQ ──▶ recruiter_agent_v5 (Python)
                         │
                         ├── REST ──▶ ats_api (via JWT)
                         │
                         └── HTTP ──▶ Google Gemini API
```

---

## 2. Autenticação

### 2.1 Login (JWT)

```
POST /v1/sessions
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret"
}

Response 200:
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": { ... }
}
```

### 2.2 Sessão Atual

```
GET /v1/me
Authorization: Bearer <token>

Response 200:
{
  "user": { "id": 1, "email": "...", "account_id": 1, ... }
}
```

### 2.3 Logout

```
POST /v1/logout
Authorization: Bearer <token>
```

Todas as rotas em `/v1/users/*` requerem `Authorization: Bearer <token>`.

---

## 3. Endpoints REST — ats_api

Base URL: `https://<ats-api-host>/v1`

### 3.1 Jobs

| Método | Path | Controller | Ação |
|--------|------|------------|------|
| GET | `/users/jobs` | `JobsController#index` | Listar vagas (com busca/filtros) |
| GET | `/users/jobs/:id` | `JobsController#show` | Detalhes de uma vaga |
| POST | `/users/jobs` | `JobsController#create` | Criar vaga |
| PUT | `/users/jobs/:id` | `JobsController#update` | Atualizar vaga (owner only) |
| DELETE | `/users/jobs/:id` | `JobsController#destroy` | Deletar vaga (owner only) |

**Parâmetros de criação/atualização:**
```json
{
  "job": {
    "title": "string (required)",
    "description": "string (required)",
    "user_id": "integer",
    "account_id": "integer"
  }
}
```

**Serializer:** `JobSerializer`

### 3.2 Candidates

| Método | Path | Controller | Ação |
|--------|------|------------|------|
| GET | `/users/candidates` | `CandidatesController#index` | Listar candidatos |
| GET | `/users/candidates/:id` | `CandidatesController#show` | Detalhes |
| POST | `/users/candidates` | `CandidatesController#create` | Criar candidato |
| PUT | `/users/candidates/:id` | `CandidatesController#update` | Atualizar |
| DELETE | `/users/candidates/:id` | `CandidatesController#destroy` | Deletar |

**Parâmetros:**
```json
{
  "candidate": {
    "name": "string (required)",
    "email": "string (required, unique)",
    "surname": "string",
    "mobile_phone": "string",
    "cpf": "string (unique)",
    "linkedin": "string",
    "github": "string",
    "portfolio": "string",
    "current_company": "string",
    "role_name": "string",
    "position_level": "string",
    "self_introduction": "text",
    "curriculum_text": "text",
    "date_birth": "date",
    "gender": "integer",
    "nationality": "string",
    "city": "string",
    "state": "string",
    "country": "string",
    "clt_expectation": "float",
    "pj_expectation": "float",
    "current_salary": "float",
    "desired_salary": "float",
    "currency": "string (default: BRL)",
    "remote_work": "boolean",
    "source": "string",
    "avatar_url": "string",
    "curriculum_pdf_url": "string",
    "account_id": "integer"
  }
}
```

### 3.3 Applies (Candidaturas)

| Método | Path | Controller | Ação |
|--------|------|------------|------|
| GET | `/users/applies` | `AppliesController#index` | Listar (filtro `is_deleted: false`) |
| GET | `/users/applies/:id` | `AppliesController#show` | Detalhes |
| POST | `/users/applies` | `AppliesController#create` | Criar candidatura |
| PUT | `/users/applies/:id` | `AppliesController#update` | Atualizar (mover de etapa) |
| DELETE | `/users/applies/:id` | `AppliesController#destroy` | Soft delete (`is_deleted: true`) |

**Parâmetros:**
```json
{
  "apply": {
    "candidate_id": "integer (required)",
    "job_id": "integer (required)",
    "selective_process_id": "integer (required)",
    "is_deleted": "boolean",
    "account_id": "integer"
  }
}
```

### 3.4 Selective Processes (Etapas)

| Método | Path | Controller | Ação |
|--------|------|------------|------|
| GET | `/users/selective_processes` | `SelectiveProcessesController#index` | Listar etapas |
| GET | `/users/selective_processes/:id` | `SelectiveProcessesController#show` | Detalhes |
| POST | `/users/selective_processes` | `SelectiveProcessesController#create` | Criar etapa |
| PUT | `/users/selective_processes/:id` | `SelectiveProcessesController#update` | Atualizar |
| DELETE | `/users/selective_processes/:id` | `SelectiveProcessesController#destroy` | Deletar |

### 3.5 Messages

| Método | Path | Controller | Ação |
|--------|------|------------|------|
| GET | `/users/messages` | `MessagesController#index` | Listar mensagens |
| POST | `/users/messages` | `MessagesController#create` | Criar mensagem |

### 3.6 Users (Search)

| Método | Path | Controller | Ação |
|--------|------|------------|------|
| GET | `/users/search` | `UsersController#index` | Buscar usuários |
| GET | `/users/search/:id` | `UsersController#show` | Detalhes do usuário |
| POST | `/users/create` | `UsersController#create` | Criar usuário |
| PUT | `/users/edit/:id` | `UsersController#update` | Editar |
| DELETE | `/users/delete/:id` | `UsersController#destroy` | Deletar |

---

## 4. Busca e Filtros (perform_search)

O `ApplicationController` fornece `perform_search` via concern `SearchRenderer`:

```
GET /users/candidates?q=Maria&where[city]=SP&page=1&per_page=20
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `q` | string | Texto livre para full-text search |
| `where[campo]` | any | Filtro exato por campo |
| `page` | integer | Página (default 1) |
| `per_page` | integer | Itens por página (default 20) |
| `order[campo]` | asc/desc | Ordenação |

**Response shape:**
```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8
  }
}
```

---

## 5. WebSocket (ActionCable)

| Canal | Path | Uso |
|-------|------|-----|
| MessageChannel | `/cable` | Push de mensagens do chat em tempo real |
| CreditChannel | `/cable` | Atualização de créditos de sourcing |

Montado via: `mount ActionCable.server => "/cable"`

---

## 6. Contrato recruiter_agent_v5 → ats_api

O agente Python acessa o Rails API via `ATSAPIClient` (`src/services/api_client.py`).

### 6.1 Autenticação

```python
# Login e obtenção de JWT
POST /v1/sessions { email, password }
→ { token: "..." }
```

### 6.2 Ferramentas Documentadas (YAML)

Cada tool do agente tem um arquivo YAML em `documentation/`:

| Arquivo | Endpoint | Método |
|---------|----------|--------|
| `candidates_search.yml` | `/users/candidates` | GET |
| `candidates_create.yml` | `/users/candidates` | POST |
| `candidates_show.yml` | `/users/candidates/:id` | GET |
| `candidates_update.yml` | `/users/candidates/:id` | PUT |
| `candidates_delete.yml` | `/users/candidates/:id` | DELETE |
| `jobs_search.yml` | `/users/jobs` | GET |
| `jobs_create.yml` | `/users/jobs` | POST |
| `jobs_show.yml` | `/users/jobs/:id` | GET |
| `jobs_update.yml` | `/users/jobs/:id` | PUT |
| `jobs_delete.yml` | `/users/jobs/:id` | DELETE |
| `applies_search.yml` | `/users/applies` | GET |
| `applies_create.yml` | `/users/applies` | POST |
| `applies_update.yml` | `/users/applies/:id` | PUT |
| `applies_delete.yml` | `/users/applies/:id` | DELETE |
| `selective_processes_search.yml` | `/users/selective_processes` | GET |
| `selective_processes_create.yml` | `/users/selective_processes` | POST |
| `selective_processes_update.yml` | `/users/selective_processes/:id` | PUT |
| `selective_processes_delete.yml` | `/users/selective_processes/:id` | DELETE |
| `evaluations_search.yml` | `/users/evaluations` | GET |
| `evaluations_create.yml` | `/users/evaluations` | POST |
| `evaluations_update.yml` | `/users/evaluations/:id` | PUT |
| `evaluations_delete.yml` | `/users/evaluations/:id` | DELETE |
| `questions_search.yml` | `/users/questions` | GET |
| `questions_create.yml` | `/users/questions` | POST |
| `questions_update.yml` | `/users/questions/:id` | PUT |
| `questions_delete.yml` | `/users/questions/:id` | DELETE |
| `users_search.yml` | `/users/search` | GET |
| `users_create.yml` | `/users/create` | POST |
| `users_update.yml` | `/users/edit/:id` | PUT |
| `users_delete.yml` | `/users/delete/:id` | DELETE |
| `sourced_profile_sourcings_search.yml` | `/users/sourced_profile_sourcings` | GET |
| `sourced_profile_sourcings_create.yml` | `/users/sourced_profile_sourcings` | POST |
| `sourced_profiles_import.yml` | `/users/sourced_profiles/import` | POST |
| `sourced_profiles_convert_to_candidates.yml` | `/users/sourced_profiles/convert` | POST |
| `lists_search.yml` | `/users/lists` | GET |
| `list_relationships_create.yml` | `/users/list_relationships` | POST |
| `talent_pool_search.yml` | `/users/talent_pool` | GET |
| `organizational_structure_create.yml` | `/users/organizational_structure` | POST |

---

## 7. Contrato recruiter_agent_v5 ↔ RabbitMQ

### 7.1 Queues

| Queue | Consumer | Função |
|-------|----------|--------|
| `recruiter_agent` | `celery_worker.py` | Queries de domínio |
| `evaluation` | `evaluation_worker.py` | Avaliação de candidatos |

### 7.2 Formato da Mensagem (RabbitMQ)

```json
{
  "session_id": "uuid",
  "domain": "applies|jobs|insights|messaging|autonomous",
  "query": "texto da query do recrutador",
  "context": {
    "job_id": 123,
    "user_id": 1,
    "account_id": 1,
    "auth_token": "jwt...",
    "viewing_entities": { ... }
  },
  "metadata": {
    "source": "chat|voice",
    "timestamp": "2026-03-26T10:00:00Z"
  }
}
```

### 7.3 Callback de Resposta

O agente envia resposta de volta ao Rails via HTTP POST:

```
POST /v1/agent_responses
Authorization: Bearer <agent_token>

{
  "session_id": "uuid",
  "message": "resposta em português",
  "metadata": {
    "action_type": "search|create|update|...",
    "execution_time_ms": 1500,
    "api_calls": 3,
    "suggestions": ["Sugestão 1", "Sugestão 2"]
  }
}
```

---

## 8. Error Handling

### 8.1 HTTP Status Codes (Rails)

| Code | Significado | Quando |
|------|------------|--------|
| 200 | OK | Sucesso |
| 201 | Created | Recurso criado |
| 204 | No Content | Deletado com sucesso |
| 401 | Unauthorized | Token inválido/expirado |
| 403 | Forbidden | Sem permissão (ex: editar job de outro user) |
| 404 | Not Found | Recurso não encontrado |
| 422 | Unprocessable Entity | Validação falhou |
| 500 | Internal Server Error | Erro do servidor |

### 8.2 Formato de Erro

```json
{
  "error": "Mensagem de erro",
  "details": { ... }
}
```

---

## 9. Health Check

```
GET /up
Response 200 — aplicação saudável
Response 500 — aplicação com erro
```

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Routes | `ats_api/config/routes.rb` |
| Jobs Controller | `ats_api/app/controllers/v1/users/jobs_controller.rb` |
| Applies Controller | `ats_api/app/controllers/v1/users/applies_controller.rb` |
| Candidates Controller | `ats_api/app/controllers/v1/users/candidates_controller.rb` |
| Application Controller | `ats_api/app/controllers/application_controller.rb` |
| Tool Documentation | `recruiter_agent_v5/documentation/*.yml` |
| API Client (Python) | `recruiter_agent_v5/src/services/api_client.py` |
