# API_CONTRACTS.md — Contratos de API da Plataforma LIA

> **Versão**: 2.0  
> **Última atualização**: 2026-03-26  
> **Fonte**: `ats_api/config/routes.rb`, `lia-agent-system/app/main.py` (362+ endpoints), `recruiter_agent_v5/src/api.py`  
> **Proprietário**: WeDOTalent Engineering

---

## 1. Visão Geral da Arquitetura de APIs

```
┌─────────────────────────────────────────────────────────────────────┐
│  plataforma-lia (Next.js, port 5000)                                │
│                                                                      │
│  ┌──────────────────────┐     ┌──────────────────────────────┐     │
│  │  lia-api.ts (client)  │────>│  /api/lia/[...path]/route.ts │     │
│  └──────────────────────┘     │  (proxy → localhost:8000)    │     │
│                                └──────────────┬───────────────┘     │
└───────────────────────────────────────────────┼─────────────────────┘
                                                 │ HTTP (internal)
┌───────────────────────────────────────────────┼─────────────────────┐
│  lia-agent-system (FastAPI, port 8000)         │                     │
│  362+ REST endpoints + WebSocket               │                     │
│  7 ReAct agents (LangGraph)                    │                     │
│  WorkOS SSO authentication                     │                     │
└───────────────────────────────────────────────┼─────────────────────┘
                                                 │ HTTP + RabbitMQ
┌───────────────────────────────────────────────┼─────────────────────┐
│  ats_api (Rails 7.1, port 3000)                │                     │
│  CRUD REST (JSONAPI) + ActionCable             │                     │
│  JWT authentication                            │                     │
└────────────────────────────────────────────────────────────────────┘
                                                 │
┌────────────────────────────────────────────────▼────────────────────┐
│  recruiter_agent_v5 (Python, worker)                                │
│  Chat/Stream API + RabbitMQ consumer                                │
│  Google Gemini + domain orchestration                               │
└────────────────────────────────────────────────────────────────────┘
```

### 1.1 Serviços e portas

| Serviço | Framework | Porta | Propósito |
|---------|-----------|-------|-----------|
| `plataforma-lia` | Next.js 14 | 5000 | Frontend + API proxy |
| `lia-agent-system` | FastAPI 0.115+ | 8000 | Backend principal — IA, pipeline, compliance |
| `ats_api` | Rails 7.1 | 3000 | ATS core — CRUD, Elasticsearch, ActionCable |
| `recruiter_agent_v5` | FastAPI | — | Worker agent — Gemini, domain orchestration |

### 1.2 Convenções globais

| Convenção | Valor |
|-----------|-------|
| **Formato de data** | ISO 8601 UTC: `2026-03-15T10:00:00Z` |
| **IDs** | UUID v4 (`lia-agent-system`) ou Integer (`ats_api`) |
| **Paginação** | `?page=1&page_size=20` (Python) ou `?page=1&per_page=20` (Rails) |
| **Multi-tenant** | `company_id` (UUID) via user auth ou header `X-Company-ID` |
| **Content-Type** | `application/json` |
| **Charset** | UTF-8 |
| **Request ID** | Header `X-Request-ID` (auto-gerado pelo middleware) |

---

## 2. Autenticação

### 2.1 `ats_api` — JWT

```http
POST /v1/sessions
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret"
}

Response 200:
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": { "id": 1, "email": "user@example.com", "account_id": 1 }
}
```

```http
GET /v1/me
Authorization: Bearer <jwt_token>

Response 200:
{
  "user": { "id": 1, "email": "...", "account_id": 1, ... }
}
```

```http
POST /v1/logout
Authorization: Bearer <jwt_token>

Response 200: {}
```

Todas as rotas em `/v1/users/*` requerem `Authorization: Bearer <token>`.

### 2.2 `lia-agent-system` — JWT (email/password) + WorkOS SSO (separado)

Fonte: `app/api/v1/auth.py` (login JWT) + `app/api/v1/workos.py` (SSO)

**Login padrão** (email/password → JWT):

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "secret"
}

Response 200 (TokenResponse):
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**WorkOS SSO** (rotas separadas em `app/api/v1/workos.py`):

| Rota | Prefixo | Proteção |
|------|---------|----------|
| `router` | `/workos` | `verify_internal_auth` |
| `scim_router` | `/workos` | `verify_scim_webhook` |
| `auth_router` | `/auth/workos` | `verify_internal_auth` |
| `webhook_router` | `/workos/webhooks` | (webhook signature) |

WorkOS SSO é para integração empresarial — NÃO é o login padrão.

**Dependency injection**:

| Dependency | Efeito |
|-----------|--------|
| `get_current_user` | Valida Bearer token — 401 se ausente/inválido |
| `get_current_active_user` | + verifica `is_active=True` |
| `get_current_user_or_demo` | Aceita token ou cria user demo (dev only) |
| `get_user_company_id` | Extrai `company_id` do user autenticado |

### 2.3 `recruiter_agent_v5` — JWT via `ats_api`

```python
# ATSAPIClient obtém JWT do ats_api
POST /v1/sessions { email, password } → { token: "..." }
# Usado em todas as chamadas subsequentes
Authorization: Bearer <jwt_from_ats_api>
```

---

## 3. Endpoints REST — `ats_api` (Rails)

Base URL: `https://<ats-api-host>/v1`

### 3.1 Jobs

| Método | Path | Ação |
|--------|------|------|
| GET | `/users/jobs` | Listar vagas (com busca Elasticsearch) |
| GET | `/users/jobs/:id` | Detalhes de uma vaga |
| POST | `/users/jobs` | Criar vaga |
| PUT | `/users/jobs/:id` | Atualizar vaga (owner only) |
| DELETE | `/users/jobs/:id` | Deletar vaga (owner only) |

**Request body (create/update)**:
```json
{
  "job": {
    "title": "Dev Rails (required)",
    "description": "Descrição (required)",
    "user_id": 1,
    "account_id": 1
  }
}
```

**Serializer**: `JobSerializer` (JSONAPI::Serializer) — 22 attributes

### 3.2 Candidates

| Método | Path | Ação |
|--------|------|------|
| GET | `/users/candidates` | Listar candidatos |
| GET | `/users/candidates/:id` | Detalhes |
| POST | `/users/candidates` | Criar candidato |
| PUT | `/users/candidates/:id` | Atualizar |
| DELETE | `/users/candidates/:id` | Deletar |

**Request body (create/update)**: 45+ campos em `{ "candidate": { ... } }`

### 3.3 Applies (Candidaturas)

| Método | Path | Ação |
|--------|------|------|
| GET | `/users/applies` | Listar (filtro `is_deleted: false`) |
| GET | `/users/applies/:id` | Detalhes |
| POST | `/users/applies` | Criar candidatura |
| PUT | `/users/applies/:id` | Atualizar (mover de etapa) |
| DELETE | `/users/applies/:id` | Soft delete (`is_deleted: true`) |

**Request body**:
```json
{
  "apply": {
    "candidate_id": 1,
    "job_id": 1,
    "selective_process_id": 1,
    "account_id": 1
  }
}
```

### 3.4 Selective Processes

| Método | Path | Ação |
|--------|------|------|
| GET | `/users/selective_processes` | Listar etapas |
| GET | `/users/selective_processes/:id` | Detalhes |
| POST | `/users/selective_processes` | Criar etapa |
| PUT | `/users/selective_processes/:id` | Atualizar |
| DELETE | `/users/selective_processes/:id` | Deletar |

### 3.5 Messages

| Método | Path | Ação |
|--------|------|------|
| GET | `/users/messages` | Listar mensagens |
| POST | `/users/messages` | Criar mensagem |

### 3.6 Users (Search)

| Método | Path | Ação |
|--------|------|------|
| GET | `/users/search` | Buscar usuários |
| GET | `/users/search/:id` | Detalhes |
| POST | `/users/create` | Criar |
| PUT | `/users/edit/:id` | Editar |
| DELETE | `/users/delete/:id` | Deletar |

### 3.7 Busca e Filtros (`perform_search`)

```http
GET /users/candidates?q=Maria&where[city]=SP&page=1&per_page=20
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `q` | string | Full-text search (Elasticsearch) |
| `where[campo]` | any | Filtro exato |
| `page` | integer | Página (default 1) |
| `per_page` | integer | Itens/página (default 20) |
| `order[campo]` | asc/desc | Ordenação |

**Response shape (JSONAPI)**:
```json
{
  "data": [
    { "id": 1, "title": "Dev Rails", "user_id": 5, "..." : "..." }
  ],
  "meta": {
    "total": 42,
    "aggregators": {}
  }
}
```

---

## 4. Endpoints REST — `lia-agent-system` (FastAPI)

Base URL: `https://<host>/api/v1`  
**Total**: 362+ endpoints REST + WebSocket  
**Documentação interativa**: `/docs` (Swagger UI), `/docs/redoc` (ReDoc), `/openapi.json`

### 4.1 OpenAPI Tags (categorias)

| Tag | Descrição | Módulo(s) principal(is) |
|-----|-----------|------------------------|
| `agents` | Agentes ReAct de recrutamento | `agent_chat_ws`, `orchestrated_*` |
| `candidates` | Gestão de candidatos, busca RAG híbrida | `candidates.py`, `candidate_search.py` |
| `jobs` | Vagas, wizard, importação JD | `job_vacancies.py`, `jd_import.py` |
| `rag-search` | Busca semântica BM25 + pgvector | `rag_search.py` |
| `hitl` | Human-in-the-Loop | `hitl.py` |
| `guardrails` | Guardrails de agentes | `guardrails.py` |
| `pipeline` | Pipeline, stages, kanban | `pipeline.py`, `recruitment_stages.py` |
| `sourcing` | Busca ativa, boolean strings | `sourcing.py` |
| `cv-screening` | Triagem WSI, scores | `triagem.py`, `wsi.py` |
| `compliance` | LGPD, bias audit, fairness | `bias_audit.py`, `lgpd_compliance.py` |
| `analytics` | KPIs, funil, previsões ML | `reports.py`, `ml_predictions.py` |
| `communication` | Email, WhatsApp, Teams | `communication.py`, `whatsapp.py` |
| `scheduling` | Entrevistas, calendário | `scheduling.py`, `calendar.py` |
| `auth` | WorkOS SSO, permissões | `workos.py`, `auth.py` |
| `admin` | Administração, circuit breakers | `admin.py`, `admin_circuit_breakers.py` |
| `health` | Health check, observabilidade | `system_health.py`, `health_langgraph.py` |
| `toon` | TOON cards — perfil visual | `toon.py` |
| `drift` | Model drift detection | `drift.py` |
| `bias-audit` | Four-Fifths Rule | `bias_audit.py` |
| `wsi` | Entrevista estruturada WhatsApp/voz | `wsi.py`, `wsi_async.py` |
| `policy-engine` | Motor de políticas por setor | `policy_engine.py` |
| `short-lists` | Short lists por vaga | `short_lists.py` |

### 4.2 Chat e Conversação

Fonte: `app/api/v1/chat.py` + `app/schemas/chat.py`

**Request**: `MessageCreate` (Pydantic)

```http
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Preciso de desenvolvedores Python sênior em São Paulo",
  "conversation_id": "uuid (optional — se null, cria nova)"
}
```

**Response 200**: `ChatResponse` (Pydantic)

```json
{
  "message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "Encontrei 15 candidatos que atendem ao perfil...",
    "message_metadata": {
      "intent": "search_candidates",
      "entities": {"skills": ["Python"], "location": "São Paulo"},
      "confidence": 0.95,
      "action_executed": false
    },
    "created_at": "2026-03-26T10:00:00Z"
  },
  "conversation": {
    "id": "uuid",
    "status": "active",
    "created_at": "2026-03-26T10:00:00Z",
    "updated_at": "2026-03-26T10:00:00Z"
  }
}
```

**Fluxo interno**: `send_message()` → `_invoke_orchestrator()` → `handle_action_flow()` → `_build_response_from_action()`  
**user_id**: extraído do JWT via `get_current_user_or_demo`  
**company_id**: `current_user.company_id` ou fallback `"demo_company"`

**Intents reconhecidos** (`INTENT_TO_ACTIONABLE`):

| Intent (EN) | Ação (PT) | Descrição |
|-------------|-----------|-----------|
| `move_candidate` | `mover_candidato` | Mover no pipeline |
| `update_candidate_status` | `atualizar_status_candidato` | Atualizar status |
| `reject_candidate` | `reprovar_candidato` | Reprovar |
| `approve_candidate` | `aprovar_candidato` | Aprovar |
| `send_email` | `enviar_email` | Enviar email |
| `schedule_interview` | `agendar_entrevista` | Agendar entrevista |
| `trigger_screening` | `disparar_triagem` | Disparar triagem |
| `analyze_profile` | `analisar_perfil` | Analisar perfil |
| `pause_job` | `pausar_vaga` | Pausar vaga |
| `close_job` | `fechar_vaga` | Fechar vaga |
| `duplicate_job` | `duplicar_vaga` | Duplicar vaga |
| `reopen_job` | `reabrir_vaga` | Reabrir vaga |

**Intents que não geram ação** (`SKIP_ACTION_INTENTS`): `create_job`, `greeting`, `general_question`, `search_candidates`, `unknown`

### 4.3 Chat Streaming (SSE)

Fonte: `app/api/v1/chat.py` linhas 1125-1240

**Request**: `MessageCreate` (mesmo schema do REST)

```http
POST /api/v1/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Analise o perfil do candidato João",
  "conversation_id": "uuid (optional)"
}
```

**Response**: `text/event-stream` (SSE via `StreamingResponse`)

Fonte: `app/api/v1/chat.py` `_sse_event_generator()` linha 1161

```
data: {"token": "Anali"}
data: {"token": "sando"}
data: {"token": " o perfil..."}
data: [DONE]
```

Cada chunk é emitido como JSON envelope `{"token": "<text>"}` via `json.dumps()`.  
Erros: `{"error": "<message>"}`.  
Fim do stream: `data: [DONE]\n\n` (texto literal, não JSON).  
**Implementação**: `anthropic.AsyncAnthropic` SDK, `client.messages.stream()` com `claude-sonnet-4-6`, `max_tokens=2048`.  
System prompt: `_LIA_STREAM_SYSTEM_PROMPT` (linha 1128).  
Após stream completo, persiste `Message` no DB com `role="ai"`, `message_metadata={"stream": True}`.

### 4.4 Job Vacancies (4677 linhas)

```http
GET /api/v1/job-vacancies
Authorization: Bearer <token>

Query params:
  ?page=1&page_size=20
  &status=active
  &company_id=uuid
  &search=python developer

Response 200:
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

```http
POST /api/v1/job-vacancies
Authorization: Bearer <token>

{
  "title": "Senior Python Engineer",
  "description": "...",
  "department": "Engineering",
  "seniority_level": "senior",
  "employment_type": "clt",
  "work_model": "hybrid",
  "location_city": "São Paulo",
  "location_state": "SP",
  "salary_min": 15000,
  "salary_max": 25000,
  "salary_currency": "BRL",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "experience_years": 5
}
```

```http
GET /api/v1/job-vacancies/{vacancy_id}
PUT /api/v1/job-vacancies/{vacancy_id}
DELETE /api/v1/job-vacancies/{vacancy_id}
```

**Sub-endpoints de vaga** (verificados em `app/api/v1/job_vacancies.py`):

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/job-vacancies/finalize` | Finalizar criação (linha 310) |
| GET | `/job-vacancies/search` | Buscar vagas (linha 391) |
| POST | `/job-vacancies/{job_id}/publish` | Publicar vaga (linha 511) |
| POST | `/job-vacancies/{job_id}/confirm-global-search` | Confirmar busca global (linha 594) |
| GET | `/job-vacancies/{job_id}/sourcing-status` | Status de sourcing (linha 638) |
| GET | `/job-vacancies/{job_vacancy_id}/metrics` | Métricas da vaga (linha 719) |
| GET | `/job-vacancies/{job_id}/analytics` | Analytics (linha 933) |
| GET | `/job-vacancies/{job_id}/history` | Histórico (linha 1226) |
| GET | `/job-vacancies/archetypes` | Arquétipos (linha 1324) |
| GET | `/job-vacancies/stats/overview` | Estatísticas (linha 1570) |
| PATCH | `/job-vacancies/{job_vacancy_id}/status` | Mudar status (linha 2281) |
| POST | `/job-vacancies/{job_id}/duplicate` | Duplicar (linha 2736) |
| POST | `/{vacancy_id}/close` | Fechar vaga (linha 4366) |
| GET | `/jobs/{job_id}/report` | Relatório (linha 4558) |
| POST | `/job-vacancies/bulk/pause` | Bulk pausar (linha 3906) |
| POST | `/job-vacancies/bulk/resume` | Bulk retomar (linha 4005) |
| POST | `/job-vacancies/bulk/archive` | Bulk arquivar (linha 4091) |

**Vagas públicas** (sem autenticação):

```http
GET /api/v1/public-vacancies
GET /api/v1/public-vacancies/{vacancy_id}
```

### 4.5 Candidates (2128 linhas)

**Busca 2-tier**: Local (PostgreSQL, gratuito) → Global (Pearch AI 190M+, pago)

```http
GET /api/v1/candidates/search
Authorization: Bearer <token>

Query params:
  ?query=python developer senior
  &location=São Paulo
  &skills=Python,FastAPI
  &experience_min=3
  &page=1&page_size=20

Response 200:
{
  "candidates": [...],
  "total": 150,
  "search_type": "local",
  "search_time_seconds": 0.45
}
```

```http
POST /api/v1/candidates/pearch-search
Authorization: Bearer <token>

{
  "query": "Senior Python engineer in São Paulo",
  "limit": 10
}

Response 200:
{
  "query": "Senior Python engineer in São Paulo",
  "total_results": 10,
  "candidates": [
    {
      "id": null,
      "name": "...",
      "headline": "Senior Python Engineer @ Company",
      "current_title": "Senior Python Engineer",
      "current_company": "Company X",
      "location": "São Paulo, Brazil",
      "contact": {
        "email": "...",
        "linkedin_url": "..."
      },
      "skills": ["Python", "Django", "AWS"],
      "summary": "...",
      "match_score": 0.92
    }
  ],
  "search_time_seconds": 2.3
}
```

**Stage transitions**:

```http
PATCH /api/v1/candidates/{candidate_id}/stage
Authorization: Bearer <token>

{
  "vacancy_id": "uuid",
  "from_stage": "triagem",
  "to_stage": "entrevista rh",
  "reason": "CV aprovado"
}
```

### 4.6 Recruitment Stages

```http
GET /api/v1/recruitment-stages/stages
POST /api/v1/recruitment-stages/stages
PUT /api/v1/recruitment-stages/stages/{stage_id}
DELETE /api/v1/recruitment-stages/stages/{stage_id}
PUT /api/v1/recruitment-stages/stages/{stage_id}/config
POST /api/v1/recruitment-stages/stages/reorder
POST /api/v1/recruitment-stages/transition
POST /api/v1/recruitment-stages/initialize
GET /api/v1/recruitment-stages/jobs/{job_id}/pipeline
PUT /api/v1/recruitment-stages/jobs/{job_id}/pipeline
```

### 4.7 Sourcing Pipeline

```http
POST /api/v1/sourcing/start
Authorization: Bearer <token>

{
  "vacancy_id": "uuid",
  "search_criteria": {...},
  "auto_calibrate": true
}
```

### 4.8 WSI — Entrevista Estruturada

```http
POST /api/v1/wsi/generate-questions
Authorization: Bearer <token>

{
  "candidate_id": "uuid",
  "vacancy_id": "uuid",
  "channel": "whatsapp"
}

Response 200:
{
  "session_id": "uuid",
  "questions": [...],
  "estimated_duration_minutes": 15
}
```

```http
POST /api/v1/wsi/analyze-response
{
  "session_id": "uuid",
  "answers": [...]
}

Response 200:
{
  "score": 78.5,
  "recommendation": "approved",
  "analysis": {
    "technical": { "score": 85, "details": "..." },
    "communication": { "score": 70, "details": "..." },
    "cultural_fit": { "score": 80, "details": "..." }
  }
}
```

### 4.9 Calibration

```http
POST /api/v1/calibration/feedback
{
  "vacancy_id": "uuid",
  "candidate_id": "uuid",
  "feedback": "like",
  "reason": "Strong Python background"
}
```

```http
GET /api/v1/calibration/session/{session_id}

Response 200:
{
  "status": "learning",
  "total_shown": 12,
  "likes_count": 7,
  "dislikes_count": 5,
  "learned_criteria": {...},
  "sourcing_blocked": true
}
```

### 4.10 LIA Opinions

```http
GET /api/v1/opinions/{candidate_id}
POST /api/v1/opinions/generate
Authorization: Bearer <token>

{
  "candidate_id": "uuid",
  "vacancy_id": "uuid",
  "opinion_type": "wsi"
}

Response 200:
{
  "id": "uuid",
  "score": 82.5,
  "wsi_score": 78.0,
  "recommendation": "approved",
  "archetype": "Executor Pragmático",
  "summary": "Candidato demonstra forte competência técnica...",
  "score_breakdown": {
    "technical": 85,
    "communication": 70,
    "cultural_fit": 90
  },
  "strengths": ["Python avançado", "Liderança técnica"],
  "concerns": ["Pouca experiência com cloud"],
  "next_steps": "Agendar entrevista técnica"
}
```

### 4.11 HITL — Human-in-the-Loop

```http
GET /api/v1/hitl/pending
Authorization: Bearer <token>

Response 200:
{
  "pending_actions": [
    {
      "id": "uuid",
      "action_type": "mover_candidato",
      "description": "Mover João para Entrevista RH",
      "entities": {...},
      "created_at": "2026-03-15T10:00:00Z"
    }
  ]
}
```

```http
POST /api/v1/hitl/{action_id}/approve
POST /api/v1/hitl/{action_id}/reject
{
  "reason": "Candidato não atende requisitos mínimos"
}
```

### 4.12 Guardrails

```http
GET /api/v1/guardrails
POST /api/v1/guardrails
PUT /api/v1/guardrails/{id}
DELETE /api/v1/guardrails/{id}
POST /api/v1/guardrails/seed-defaults
```

### 4.13 Compliance — LGPD

```http
GET /api/v1/lgpd/consents/{candidate_id}
POST /api/v1/lgpd/consents
DELETE /api/v1/lgpd/consents/{consent_id}
```

```http
POST /api/v1/data-subject-requests
{
  "candidate_email": "joao@example.com",
  "request_type": "access",
  "description": "Solicito acesso aos meus dados"
}
```

**DSR types**: `access`, `rectification`, `erasure`, `portability`, `restriction`, `objection`

### 4.14 Bias Audit

```http
GET /api/v1/bias-audit/{vacancy_id}

Response 200:
{
  "vacancy_id": "uuid",
  "four_fifths_rule": {
    "gender": { "ratio": 0.85, "passed": true },
    "ethnicity": { "ratio": 0.72, "passed": false }
  },
  "recommendations": [...]
}
```

### 4.15 Communication

```http
POST /api/v1/communication/send
{
  "candidate_id": "uuid",
  "channel": "email",
  "template_id": "uuid",
  "variables": { "name": "João", "position": "Dev Python" }
}
```

**Channels suportados**: `email`, `whatsapp`, `sms`, `teams`

### 4.16 Scheduling

```http
POST /api/v1/scheduling/create
{
  "candidate_id": "uuid",
  "vacancy_id": "uuid",
  "type": "technical_interview",
  "proposed_times": [
    "2026-04-01T14:00:00Z",
    "2026-04-02T10:00:00Z"
  ],
  "interviewer_ids": ["uuid1", "uuid2"]
}
```

### 4.17 Admin — Monitoramento

```http
GET /api/v1/admin/circuit-breakers
POST /api/v1/admin/circuit-breakers/{name}/reset
GET /api/v1/admin/agents/status
GET /api/v1/admin/dlq
POST /api/v1/admin/dlq/{id}/retry
GET /api/v1/admin/token-budget
```

### 4.18 Health Check

```http
GET /health
→ 307 Redirect to /api/v1/health

GET /api/v1/health

Response 200:
{
  "status": "healthy",
  "app": "lia-agent-system",
  "version": "3.0.0",
  "environment": "development",
  "database": "connected",
  "services": {
    "pearch": "configured",
    "openmic": "configured",
    "workos": "configured",
    "sentry": "configured",
    "langsmith": "configured"
  }
}
```

```http
GET /metrics
→ Prometheus metrics (text/plain; openmetrics)
```

### 4.19 Observabilidade

```http
GET /api/v1/observability/traces
GET /api/v1/observability/metrics
GET /api/v1/model-drift/status
GET /api/v1/agent-explainability/{decision_id}
```

---

## 5. WebSocket

### 5.1 `ats_api` — ActionCable

```
WebSocket URL: wss://<ats-api-host>/cable

Channels:
  - MessageChannel → Push de mensagens em tempo real
  - CreditChannel  → Atualização de créditos de sourcing
```

### 5.2 `lia-agent-system` — FastAPI WebSocket

```
WebSocket URL: wss://<host>/ws/agent-chat

Message format (client → server):
{
  "type": "message",
  "content": "Preciso de desenvolvedores Python",
  "user_id": "uuid",
  "conversation_id": "uuid"
}

Message format (server → client):
{
  "type": "response",
  "content": "Encontrei 15 candidatos...",
  "metadata": {...}
}

{
  "type": "thinking",
  "content": "Analisando requisitos da vaga..."
}

{
  "type": "action_required",
  "action": {
    "type": "mover_candidato",
    "description": "Mover João para Entrevista RH",
    "requires_confirmation": true
  }
}
```

```
WebSocket URL: wss://<host>/ws/jobs/{vacancy_id}
→ Real-time updates para uma vaga específica (candidatos, stage changes)
```

---

## 6. Contrato `recruiter_agent_v5` → `ats_api`

O agente Python acessa o Rails API via `ATSAPIClient` (`src/services/api_client.py`).

### 6.1 Tools documentadas em YAML

Cada tool do agente tem um arquivo YAML em `documentation/`:

| Resource | Endpoints | YAML files |
|----------|-----------|------------|
| candidates | GET, POST, PUT, DELETE `/users/candidates` | `candidates_search/create/show/update/delete.yml` |
| jobs | GET, POST, PUT, DELETE `/users/jobs` | `jobs_search/create/show/update/delete.yml` |
| applies | GET, POST, PUT, DELETE `/users/applies` | `applies_search/create/update/delete.yml` |
| selective_processes | GET, POST, PUT, DELETE `/users/selective_processes` | `selective_processes_search/create/update/delete.yml` |
| evaluations | GET, POST, PUT, DELETE `/users/evaluations` | `evaluations_search/create/update/delete.yml` |
| questions | GET, POST, PUT, DELETE `/users/questions` | `questions_search/create/update/delete.yml` |
| users | GET, POST, PUT, DELETE `/users/search\|create\|edit\|delete` | `users_search/create/update/delete.yml` |
| sourced_profiles | GET, POST `/users/sourced_profile_sourcings` | `sourced_profile_sourcings_search/create.yml` |
| sourced_profiles | POST `/users/sourced_profiles/import\|convert` | `sourced_profiles_import/convert_to_candidates.yml` |
| lists | GET `/users/lists` | `lists_search.yml` |
| list_relationships | POST `/users/list_relationships` | `list_relationships_create.yml` |
| talent_pool | GET `/users/talent_pool` | `talent_pool_search.yml` |
| org_structure | POST `/users/organizational_structure` | `organizational_structure_create.yml` |

### 6.2 Chat/Stream API

```http
POST /chat
Content-Type: application/json

{
  "message": "Quero ver vagas abertas",
  "session_id": "uuid",
  "domain": "jobs",
  "hub_mode": true,
  "context_data": {}
}

Response 200:
{
  "response": "Você tem 3 vagas abertas...",
  "session_id": "uuid",
  "domain": "jobs",
  "actions_taken": [...]
}
```

```http
POST /chat/stream
→ Server-Sent Events (SSE)
```

---

## 7. Contrato RabbitMQ (`recruiter_agent_v5` ↔ `lia-agent-system`)

### 7.1 Queues

| Queue | Consumer | Função |
|-------|----------|--------|
| `recruiter_agent` | `celery_worker.py` | Queries de domínio |
| `evaluation` | `evaluation_worker.py` | Avaliação de candidatos |
| `lia_platform_events` | `rabbitmq_consumer` | Eventos inter-API assíncronos |

### 7.2 Formato da mensagem

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
    "viewing_entities": {}
  },
  "metadata": {
    "source": "chat|voice|webhook",
    "timestamp": "2026-03-26T10:00:00Z"
  }
}
```

### 7.3 Callback de resposta

```http
POST /v1/agent_responses
Authorization: Bearer <agent_token>

{
  "session_id": "uuid",
  "message": "resposta em português",
  "metadata": {
    "action_type": "search|create|update|delete",
    "execution_time_ms": 1500,
    "api_calls": 3,
    "suggestions": ["Sugestão 1", "Sugestão 2"]
  }
}
```

---

## 8. Contrato `recruiter_agent_v5` ↔ LLMs

### 8.1 Arquitetura de chamadas LLM

```
recruiter_agent_v5
    │
    ├── create_tracked_llm()  ←── OBRIGATÓRIO (nunca ChatGoogleGenerativeAI() direto)
    │       │
    │       ├── GeminiConfig
    │       │   ├── model: "gemini-1.5-flash-latest" (default)
    │       │   ├── temperature: 0.0
    │       │   └── api_key: GOOGLE_API_KEY
    │       │
    │       └── LangSmith tracing (automático)
    │
    └── DomainResponse  ←── ÚNICO tipo de retorno (nunca dict raw)
```

### 8.2 Configuração LLM (`GeminiConfig`)

Fonte: `recruiter_agent_v5/src/config/gemini_config.py`

```python
@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str = "gemini-1.5-flash-latest"
    temperature: float = 0.0
```

**Model selection por complexidade**:

| Tier | Model | Uso |
|------|-------|-----|
| `model_fast` | `gemini-2.5-flash` | Classificação de intent, extração de entidades |
| `model_default` | `gemini-2.5-flash` | Chat conversacional, busca, CRUD |
| `model_heavy` | `gemini-2.5-pro` | Análise complexa, scoring WSI, parecer detalhado |

### 8.3 Request para LLM (via `create_tracked_llm`)

```python
llm = create_tracked_llm(
    temperature=0.0,
    service_name="AppliesDomain",
    operation="chat",
)

response = llm.invoke(prompt)
```

**Payload enviado ao Google Gemini** (via LangChain `ChatGoogleGenerativeAI`):

```json
{
  "model": "gemini-2.5-flash",
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "<system_prompt>\n\n<user_query>" }]
    }
  ],
  "generationConfig": {
    "temperature": 0.0,
    "maxOutputTokens": 8192,
    "topP": 0.95
  },
  "safetySettings": [
    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" }
  ]
}
```

### 8.4 Response do LLM

```json
{
  "candidates": [
    {
      "content": {
        "parts": [{ "text": "resposta gerada" }],
        "role": "model"
      },
      "finishReason": "STOP",
      "safetyRatings": [...]
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 1500,
    "candidatesTokenCount": 500,
    "totalTokenCount": 2000
  }
}
```

### 8.5 `DomainResponse` — contrato de retorno

Todas as actions de domínio retornam `DomainResponse` (nunca `dict` raw):

```python
class DomainResponse:
    success: bool
    message: str                          # Mensagem em português brasileiro
    data: Optional[Any] = None            # Dados estruturados
    metadata: Optional[Dict] = None       # Metadados (total, job_id, etc.)
    suggestions: Optional[List[str]] = None  # Sugestões de próximos passos
    needs_clarification: bool = False     # Pedir mais informação ao usuário
```

### 8.6 Fallback e retry

| Cenário | Tratamento |
|---------|-----------|
| LLM timeout (>30s) | Retry 1x com backoff exponencial |
| Rate limit (429) | Retry com jitter, máx 3 tentativas |
| Response vazio | `DomainResponse(success=False, message="Erro ao processar")` |
| Safety block | `DomainResponse(success=False, message="Não consigo processar esta solicitação")` |
| API key inválido | Startup warning — endpoints retornam 503 |

### 8.7 `lia-agent-system` — LLM Multi-Provider

Fonte: `lia-agent-system/app/services/llm.py` (class `LLMService`)

```
LLMService
    │
    ├── Primary: Claude Sonnet 4 (Anthropic)
    ├── Fallback 1: OpenAI GPT-4o
    ├── Fallback 2: Google Gemini 2.5 Flash
    │
    └── CircuitBreaker por provider
        ├── threshold: 5 falhas consecutivas
        ├── timeout: 60 segundos
        └── half-open: testa 1 request após timeout
```

**Multi-provider config** (via `app/core/config.py`):

| Setting | Descrição |
|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Sonnet 4 — provider primário |
| `OPENAI_API_KEY` | GPT-4o — fallback |
| `GOOGLE_API_KEY` | Gemini 2.5 — fallback |
| `LLM_TIMEOUT` | Timeout por request (default: 30s) |
| `LLM_MAX_RETRIES` | Máximo de retries (default: 2) |

### 8.8 Token budget e rate limiting

| Controle | Valor | Escopo |
|----------|-------|--------|
| Token budget por empresa | Configurável via admin | Per `company_id` per month |
| Rate limit (all endpoints) | 600 req/min per user, 3000/min per company | Via `rate_limiter.py` |
| Max tokens por request | 8192 (output) | Per request |
| Tracking | LangSmith traces | Per request — `configure_langsmith()` |

### 8.9 PII stripping antes do LLM

```python
strip_pii_for_llm_prompt(text)
anonymize_for_llm(candidates)
```

Campos removidos antes de enviar ao LLM: `name`, `email`, `cpf`, `phone`, `gender`, `ethnicity`  
Feature flag: `LLM_PROMPT_PII_STRIPPING_ENABLED`

---

## 9. Frontend Proxy (`plataforma-lia`)

O frontend Next.js proxia requests para o backend via duas estratégias:

**1. Rotas explícitas** (`src/app/api/backend-proxy/**/route.ts`):

Cada feature tem sua própria route handler (100+ arquivos):
- `/api/backend-proxy/chat/message/route.ts`
- `/api/backend-proxy/approvals/[id]/approve/route.ts`
- `/api/backend-proxy/candidates/compare/route.ts`
- `/api/backend-proxy/auth/[...slug]/route.ts`
- etc.

**2. Catch-all fallback** (`src/app/api/lia/[...path]/route.ts`):

```
Frontend → /api/lia/api/v1/<path> → Proxy → http://localhost:8000/api/v1/<path>
```

**Métodos permitidos**: GET, POST, PUT, DELETE, PATCH  
**Erro handling**: erros do backend retornam `{ error: data.detail || data }` com status original.  
Erros de conexão: `{ error: "Failed to connect to LIA backend" }` com 500.  
NÃO sanitiza headers/stack traces — expõe `data.detail` do backend (linha 66).  
**Razão**: Replit expõe apenas porta 5000 publicamente; porta 8000 é interna

**Client service**: `src/services/lia-api.ts` (base: `/api/backend-proxy`)

```typescript
import { liaApi } from '@/services/lia-api'

await liaApi.sendMessage({ content: "...", conversation_id: "..." })
await liaApi.searchCandidates({ query: "...", limit: 10 })
await liaApi.healthCheck()
await liaApi.getConversations(userId)
await liaApi.getConversationHistory(conversationId)
await liaApi.searchCandidatesByJobDescription(jd)
await liaApi.checkPearchHealth()
```

---

## 9. Error Handling

### 9.1 `ats_api` — Rails

| Code | Significado | Quando |
|------|-------------|--------|
| 200 | OK | Sucesso |
| 201 | Created | Recurso criado |
| 204 | No Content | Deletado com sucesso |
| 401 | Unauthorized | Token inválido/expirado |
| 403 | Forbidden | Sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 422 | Unprocessable Entity | Validação falhou |
| 500 | Internal Server Error | Erro do servidor |

**Formato de erro Rails**:
```json
{
  "error": "Mensagem de erro",
  "details": {}
}
```

### 9.2 `lia-agent-system` — FastAPI

| Code | Significado | Quando |
|------|-------------|--------|
| 200 | OK | Sucesso |
| 201 | Created | Recurso criado |
| 400 | Bad Request | Payload inválido (Pydantic validation) |
| 401 | Unauthorized | Token ausente ou inválido |
| 403 | Forbidden | Sem permissão para o recurso |
| 404 | Not Found | Recurso não encontrado |
| 422 | Validation Error | Pydantic field validation failed |
| 429 | Too Many Requests | Rate limit excedido (`RateLimitMiddleware`) |
| 500 | Internal Server Error | Erro do servidor — capturado pelo Sentry |

**Formato de erro FastAPI**:
```json
{
  "error": true,
  "status_code": 404,
  "message": "Vacancy not found",
  "request_id": "abc-123-def"
}
```

**Exception handlers globais** (definidos em `main.py`):

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "request_id": request.state.request_id,
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "request_id": request.state.request_id,
        }
    )
```

---

## 10. Middleware Stack (`lia-agent-system`)

Ordem de execução (outermost → innermost):

| Ordem | Middleware | Função |
|-------|-----------|--------|
| 1 | `StructuredLoggingMiddleware` | Logs estruturados com status code final |
| 2 | `RequestIdMiddleware` | Gera `X-Request-ID` para tracing |
| 3 | `RateLimitMiddleware` | Rate limiting por IP/user |
| 4 | `CORSMiddleware` | CORS headers — `allow_origins: settings.CORS_ORIGINS` |

---

## 11. Startup e Serviços Inicializados

No `lifespan` do FastAPI (em `main.py`), os seguintes serviços são inicializados na ordem:

| Serviço | Validação | Fallback se falhar |
|---------|-----------|-------------------|
| Microsoft Teams Bot | `MICROSOFT_APP_ID` + `MICROSOFT_APP_PASSWORD` | Warning — Teams offline |
| Microsoft Graph API | `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` + `AZURE_TENANT_ID` | Warning — Calendar offline |
| Pearch AI | `PEARCH_API_KEY` | Warning — Search offline |
| OpenMic.ai | `OPENMIC_API_KEY` | Warning — Voice offline |
| Database | `init_db()` | **Fatal** — startup fails |
| Domain Registry | `DomainRegistry().list_domains()` | Info |
| Embedding Cache | `embedding_cache.warm_up(db)` | Warning |
| Multi-Agent Orchestrator | `initialize_orchestrator(llm_service)` | Warning — chat offline |
| Automation Scheduler | `automation_scheduler.start()` | Warning — automations offline |
| Stage Automation Engine | `register_all_handlers()` | Warning — triggers offline |
| Tool Registry | `initialize_tools()` | Warning — function calling offline |
| PolicyEngine Rules | `PolicyEngineService().load_default_rules()` | Warning (non-blocking) |
| ReAct Agent Registry | `register_react_agents()` | Warning — agents offline |
| RabbitMQ Consumer | `rabbitmq_consumer.start()` | Info — async messaging offline |
| Platform Event Handlers | `register_platform_handlers()` | Warning |

---

## 12. Rate Limiting

Fonte: `app/middleware/rate_limiter.py` (Redis sliding window)

| Tier | Limite | Escopo |
|------|--------|--------|
| Per user (minuto) | 600 req/min | Per `user_id` |
| Per empresa (minuto) | 3000 req/min | Per `company_id` |
| Per empresa (hora) | 60000 req/hora | Per `company_id` |

Fallback: in-memory rate limiting quando Redis indisponível.  
Headers: `X-RateLimit-Limit` (600), `X-RateLimit-Remaining`, `X-RateLimit-Reset`.  
Retry: `Retry-After: 300` (5 min) para limites horários, `Retry-After: 60` para minuto.

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Routes (Rails) | `ats_api/config/routes.rb` |
| Main app (Python) | `lia-agent-system/app/main.py` |
| Chat API | `lia-agent-system/app/api/v1/chat.py` |
| Job Vacancies API | `lia-agent-system/app/api/v1/job_vacancies.py` |
| Candidates API | `lia-agent-system/app/api/v1/candidates.py` |
| WorkOS Auth | `lia-agent-system/app/api/v1/workos.py` |
| Tool Documentation | `recruiter_agent_v5/documentation/*.yml` |
| Frontend API Client | `plataforma-lia/src/services/lia-api.ts` |
| Frontend Proxy | `plataforma-lia/src/app/api/lia/[...path]/route.ts` |
| Integration Doc | `docs/integracao/FRONTEND_BACKEND_INTEGRATION.md` |
| BACKEND_STANDARDS | `docs/specs/standards/BACKEND_STANDARDS.md` |
