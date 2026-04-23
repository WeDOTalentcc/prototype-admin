# API Jobs — Referência Completa de Rotas

> Todas as rotas autenticadas requerem header `Authorization: Bearer <JWT_TOKEN>`

---

## Sumário

- [1. CRUD de Jobs](#1-crud-de-jobs)
- [2. Ações de Status/Publicação](#2-ações-de-statuspublicação)
- [3. Cópia e Duplicação](#3-cópia-e-duplicação)
- [4. Ações em Lote (Collection)](#4-ações-em-lote-collection)
- [5. Kanban / Pipeline](#5-kanban--pipeline)
- [6. Applies (Candidaturas) — Ações em Lote](#6-applies-candidaturas--ações-em-lote)
- [7. Analytics e Stats](#7-analytics-e-stats)
- [8. AI / Sugestões / Matching](#8-ai--sugestões--matching)
- [9. Auto Source (Sourcing Automático)](#9-auto-source-sourcing-automático)
- [10. Estrutura Organizacional](#10-estrutura-organizacional)
- [11. Activity Logs](#11-activity-logs)
- [12. Evaluations (Avaliações da Vaga)](#12-evaluations-avaliações-da-vaga)
- [13. Selective Processes (Etapas)](#13-selective-processes-etapas)
- [14. Job Journeys (Jornadas)](#14-job-journeys-jornadas)
- [15. Job Field Templates](#15-job-field-templates)
- [16. Job Statuses](#16-job-statuses)
- [17. Job Users (Times da Vaga)](#17-job-users-times-da-vaga)
- [18. Apply Statuses](#18-apply-statuses)
- [19. Enums / Lookups](#19-enums--lookups)
- [20. Rotas Públicas (Sem Auth)](#20-rotas-públicas-sem-auth)

---

## 1. CRUD de Jobs

### `GET /v1/users/jobs` — Listar Jobs (Search)

Usa Searchkick com filtros, paginação, ordenação e agregações.

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `search` | string | Termo de busca full-text (default: `"*"`) |
| `page` | integer | Página (default: 1) |
| `per_page` | integer | Itens por página (max: 30) |
| `where[is_active]` | boolean | Filtrar por ativas |
| `where[is_archived]` | boolean | Filtrar por arquivadas |
| `where[is_deleted]` | boolean | Filtrar deletadas (default: false) |
| `where[user_id]` | integer | Filtrar por recrutador |
| `where[job_status_id]` | integer | Filtrar por status |
| `where[city]` | string | Filtrar por cidade |
| `where[seniority]` | integer | Filtrar por senioridade |
| `where[employment_type]` | integer | Filtrar por tipo de contrato |
| `where[workplace_type]` | integer | Filtrar por modelo de trabalho |
| `where[priority]` | integer | Filtrar por prioridade |
| `where[department_id]` | integer | Filtrar por departamento |
| `order[field]` | string | Campo para ordenação |
| `order[direction]` | string | `asc` ou `desc` |
| `compact` | string | Campos separados por vírgula (modo compacto) |
| `id` | integer | Buscar job específico por ID |

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "123",
      "type": "job",
      "attributes": {
        "id": 123,
        "uid": "abc-def-ghi",
        "slug": "desenvolvedor-fullstack",
        "title": "Desenvolvedor Fullstack",
        "description": "<p>Descrição da vaga...</p>",
        "is_published": true,
        "is_active": true,
        "is_archived": false,
        "is_urgent": false,
        "user_id": 1,
        "account_id": 1,
        "job_status_id": 2,
        "company_id": 5,
        "published_date": "2026-01-15T10:00:00.000Z",
        "application_deadline": "2026-03-15T23:59:59.000Z",
        "screening_deadline": null,
        "shortlist_deadline": null,
        "closing_deadline": null,
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "workplace_type": 2,
        "workplace_type_text": "Híbrido",
        "employment_type": 0,
        "employment_type_text": "CLT",
        "seniority": 2,
        "seniority_text": "Sênior",
        "priority": 1,
        "priority_text": "Alta",
        "urgency_level": 3,
        "urgency_level_text": "Média",
        "salary_from": 8000.0,
        "salary_to": 15000.0,
        "salary_currency": "BRL",
        "salary_period": "Mensal",
        "salary_contract_type": "CLT",
        "commission_from": null,
        "commission_to": null,
        "commission_currency": null,
        "commission_period": null,
        "bonus_from": null,
        "bonus_to": null,
        "bonus_currency": null,
        "bonus_period": null,
        "friendly_badge": null,
        "disabilities": false,
        "is_remote": false,
        "external_id": null,
        "provider": null,
        "provider_job_id": null,
        "job_url": null,
        "sector": "Tecnologia",
        "segment": null,
        "target_audience": null,
        "confidential_type": 1,
        "confidential_type_text": "Pública",
        "confidential_company_name": null,
        "is_screening_active": true,
        "minimum_screening_score": 70,
        "screening_timeout": 48,
        "screening_max_attempts": 3,
        "screening_approve_limit": null,
        "interview_minimum_score": null,
        "has_automatic_interview": false,
        "interview_calendar_type": null,
        "interview_hours_range": null,
        "interview_duration": null,
        "use_whatsapp_channel": true,
        "use_webchat_channel": false,
        "use_voice_channel": false,
        "use_call_channel": false,
        "notification_channels": ["email", "whatsapp"],
        "responsibilities": ["Desenvolver features", "Code review"],
        "has_linkedin_post": false,
        "has_website_post": true,
        "has_indeed_post": false,
        "reason_for_pause": null,
        "web_saturation_amount": 100,
        "sourcing_saturation_amount": 50,
        "saturation_amount_increase": null,
        "saturation_release_hours": null,
        "allowed_screenings_limit_date": null,
        "main_pcd_category": null,
        "main_pcd_category_text": "Não informado",
        "secondary_pcd_category": null,
        "secondary_pcd_category_text": "Não informado",
        "pcd_description": null,
        "pcd_files_description": null,
        "required_pcd_files": null,
        "department_id": 3,
        "department_name": "Engenharia",
        "hiring_manager_id": 7,
        "hiring_manager_name": "Maria Silva",
        "hiring_manager_email": "maria@empresa.com",
        "user_name": "João Recruiter",
        "user_email": "joao@empresa.com",
        "user_whatsapp": "11999999999",
        "job_status": "Em andamento",
        "job_status_color": "#4CAF50",
        "applies_count": 42,
        "applies_by_status_count": {
          "approved": 5,
          "rejected": 10,
          "pending": 27
        },
        "in_process": 27,
        "selection_process_summary": [
          { "id": 1, "name": "Triagem", "count": 20 },
          { "id": 2, "name": "Entrevista", "count": 7 }
        ],
        "company": { "id": 5, "name": "Tech Corp" },
        "organizational_structure": {
          "department": { "name": "Engenharia" },
          "hiring_manager": { "name": "Maria Silva" },
          "team": null,
          "reports_to": null
        },
        "missing_fields": ["description"],
        "completeness_percentage": 85,
        "is_ready_for_publication": true,
        "is_confidential": false,
        "pin": false,
        "confidential": false,
        "url": "/user/jobs/123",
        "share_url": "https://app.wedo.com/vagas/desenvolvedor-fullstack/tech-corp",
        "created_at": "2026-01-10T08:00:00.000Z",
        "updated_at": "2026-03-01T14:30:00.000Z"
      }
    }
  ],
  "meta": {
    "total_count": 150,
    "page": 1,
    "per_page": 20
  }
}
```

---

### `GET /v1/users/jobs/:id` — Detalhe do Job

**Response (200):** Mesmo formato JSON:API do item acima (objeto único em `data`).

---

### `POST /v1/users/jobs` — Criar Job

**Body (JSON):**

```json
{
  "job": {
    "title": "Desenvolvedor Backend",
    "description": "<p>Descrição detalhada da vaga</p>",
    "user_id": 1,
    "job_status_id": 1,
    "company_id": 5,
    "department": "Engenharia",
    "department_id": 3,
    "city": "São Paulo",
    "state": "SP",
    "workplace_type": 2,
    "employment_type": 0,
    "seniority": 2,
    "priority": 1,
    "urgency_level": 3,
    "is_remote": false,
    "is_urgent": false,
    "is_active": true,
    "is_screening_active": true,
    "published_date": "2026-01-15",
    "application_deadline": "2026-03-15",
    "screening_deadline": "2026-02-28",
    "shortlist_deadline": null,
    "closing_deadline": "2026-04-01",
    "salary_from": 8000,
    "salary_to": 15000,
    "salary_currency": "BRL",
    "salary_period": "monthly",
    "salary_contract_type": "clt",
    "commission_from": null,
    "commission_to": null,
    "bonus_from": null,
    "bonus_to": null,
    "sector": "Tecnologia",
    "confidential_type": 1,
    "confidential_company_name": null,
    "hiring_manager_id": 7,
    "friendly_badge": null,
    "disabilities": false,
    "minimum_screening_score": 70,
    "screening_timeout": 48,
    "screening_max_attempts": 3,
    "screening_approve_limit": null,
    "has_automatic_interview": false,
    "use_whatsapp_channel": true,
    "use_webchat_channel": false,
    "use_voice_channel": false,
    "use_call_channel": false,
    "web_saturation_amount": 100,
    "sourcing_saturation_amount": 50,
    "notification_channels": ["email"],
    "responsibilities": ["Desenvolver APIs", "Code review", "Mentorar juniors"],
    "main_pcd_category": null,
    "secondary_pcd_category": null,
    "skills": [
      { "name": "Ruby on Rails", "priority": 1 },
      { "name": "PostgreSQL", "priority": 2 }
    ],
    "benefits": [
      { "name": "Vale Refeição", "value": "800" },
      { "name": "Plano de Saúde" }
    ],
    "selective_processes_attributes": [
      { "name": "Triagem", "position": 0, "external_id": "triagem-1", "color": "#4CAF50" },
      { "name": "Entrevista RH", "position": 1, "external_id": "entrevista-rh-1", "color": "#2196F3" }
    ]
  }
}
```

**Response (201):** Job serializado em JSON:API (inclui `selective_processes`).

---

### `PUT/PATCH /v1/users/jobs/:id` — Atualizar Job

**Body:** Mesmos campos do create (parcial — só enviar campos que quer atualizar). Aceita também:

```json
{
  "job": {
    "title": "Novo Título",
    "pin": true,
    "confidential": true,
    "languages": [
      { "name": "Inglês", "level": "Avançado" },
      { "name": "Espanhol", "level": "Intermediário" }
    ]
  }
}
```

**Response (200):** Job serializado em JSON:API.

---

### `DELETE /v1/users/jobs/:id` — Deletar Job

**Response (200):** Job serializado (soft-delete via `is_deleted: true`).

---

## 2. Ações de Status/Publicação

### `POST /v1/users/jobs/:id/change_status` — Mudar Status

**Body:**

```json
{
  "job_status_id": 3,
  "reason": "Motivo da mudança (opcional)"
}
```

**Response (200):** Job serializado.

**Response (422):**

```json
{
  "errors": ["Transição não permitida"],
  "allowed_transitions": [2, 4, 5]
}
```

---

### `POST /v1/users/jobs/:id/publish` — Publicar Vaga

**Body:** Nenhum.

**Response (200):** Job serializado com `is_published: true`.

**Response (422):**

```json
{
  "errors": ["Vaga não está pronta para publicação"],
  "missing_fields": ["description", "city"]
}
```

---

### `POST /v1/users/jobs/:id/unpublish` — Despublicar Vaga

**Body:** Nenhum.

**Response (200):** Job serializado com `is_published: false`.

---

## 3. Cópia e Duplicação

### `POST /v1/users/jobs/:id/copy` — Copiar Vaga

**Body:**

```json
{
  "job": {
    "user_id": 2,
    "entities": ["selective_processes", "skills", "benefits"]
  }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `user_id` | integer | ID do recrutador dono da cópia (opcional, default: current_user) |
| `entities` | array[string] | Entidades para copiar junto: `selective_processes`, `skills`, `benefits` |

**Response (200):** Job copiado serializado.

---

### `POST /v1/users/jobs/:id/copy_job_by_amount` — Copiar Vaga N vezes

**Body:**

```json
{
  "amount": 5,
  "job": {
    "user_id": 2,
    "entities": ["selective_processes"]
  }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `amount` | integer | Quantidade de cópias (1-99) |

**Response (200):**

```json
{
  "data": {
    "attributes": {
      "message": "Job duplication in progress",
      "amount": 5,
      "job_id": 123
    }
  }
}
```

> Se `amount == 1`, executa síncrono. Se > 1, executa em background (Sidekiq).

---

### `POST /v1/users/jobs/:id/duplicate_selective_processes` — Duplicar Etapas de Outra Vaga

**Body:**

```json
{
  "source_job_id": 456,
  "replace": true
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `source_job_id` | integer | ID da vaga de origem |
| `replace` | boolean | Se `true`, substitui etapas existentes; se `false`, adiciona |

**Response (200):** Job serializado com `selective_processes` incluídos.

---

## 4. Ações em Lote (Collection)

Todas usam `select_all_params` que é o mesmo objeto de filtros do search (para selecionar quais jobs aplicar).

### `POST /v1/users/jobs/archive` — Arquivar em Lote

**Body:**

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "is_active": true, "user_id": 1 }
  },
  "is_archived": true
}
```

**Response (200):**

```json
{
  "data": {
    "attributes": {
      "status": "processing",
      "message": "As vagas estão sendo arquivadas"
    }
  }
}
```

---

### `POST /v1/users/jobs/unarchive` — Desarquivar em Lote

**Body:**

```json
{
  "select_all_params": {
    "search": "*",
    "where": { "is_archived": true }
  }
}
```

**Response (200):** Mesmo formato `{ status: "processing", message: "..." }`.

---

### `POST /v1/users/jobs/activate` — Ativar em Lote

**Body:**

```json
{
  "select_all_params": {
    "where": { "is_active": false }
  },
  "reason": "Retomando após pausa"
}
```

---

### `POST /v1/users/jobs/pause` — Pausar em Lote

**Body:**

```json
{
  "select_all_params": {
    "where": { "is_active": true }
  },
  "reason": "Pausa temporária para reestruturação"
}
```

---

### `POST /v1/users/jobs/bulk_update` — Atualizar Campos em Lote

**Body:**

```json
{
  "job_ids": [1, 2, 3, 4, 5],
  "fields": {
    "priority": 1,
    "urgency_level": 4,
    "job_status_id": 3
  }
}
```

> Se `job_ids.size > 100`, executa via Sidekiq.

**Response (200):**

```json
{
  "success": true,
  "data": {
    "updated_count": 5,
    "failed_count": 0,
    "errors": []
  }
}
```

---

### `POST /v1/users/jobs/:id/add_candidates_from_list` — Adicionar Candidatos de uma Lista

**Body:**

```json
{
  "list_id": 10,
  "selective_process_id": 25
}
```

**Response (200):**

```json
{
  "data": {
    "attributes": {
      "message": "Processamento iniciado. Os candidatos da lista serão adicionados à vaga."
    }
  }
}
```

---

## 5. Kanban / Pipeline

### `GET /v1/users/jobs/:job_id/kanban` — Visualizar Kanban

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `term` | string | Busca por nome/email do candidato |
| `page` | integer | Página (paginação dentro de cada coluna) |
| `selective_process_id` | integer | Filtrar coluna específica |
| `where[source]` | string | `sourcing` ou `web_response` |
| `where[screening_score][gte]` | float | Score mínimo de screening |

**Response (200):**

```json
{
  "data": {
    "job_id": 123,
    "job_title": "Desenvolvedor Fullstack",
    "columns": [
      {
        "selective_process_id": 1,
        "selective_process_title": "Triagem",
        "approved_process_id": 2,
        "rejected_process_id": null,
        "action_behavior": null,
        "sub_status_options": ["Em análise", "Aguardando retorno"],
        "sourcing_applies_count": 5,
        "web_response_applies_count": 15,
        "applies": {
          "records": [
            {
              "id": 100,
              "candidate_id": 50,
              "candidate_name": "Ana Souza",
              "candidate_email": "ana@email.com",
              "source": "web_response",
              "selective_process_id": 1,
              "screening_score": 85.5,
              "created_at": "2026-02-01T10:00:00Z",
              "evaluation_candidate_summaries": [
                { "evaluation_id": 1, "score": 78, "status": "answered" }
              ]
            }
          ],
          "total_count": 20
        }
      },
      {
        "selective_process_id": 2,
        "selective_process_title": "Entrevista Técnica",
        "applies": {
          "records": [],
          "total_count": 0
        }
      }
    ]
  }
}
```

---

## 6. Applies (Candidaturas) — Ações em Lote

### `POST /v1/users/jobs/:id/applies/approve_collection` — Aprovar Candidaturas em Lote

**Body:**

```json
{
  "select_all_params": {
    "where": {
      "selective_process_id": 1,
      "job_id": 123
    }
  }
}
```

**Response (200):**

```json
{
  "data": {
    "attributes": {
      "status": "processing",
      "message": "As candidaturas estão sendo aprovadas em background",
      "job_id": 123
    }
  }
}
```

---

### `POST /v1/users/jobs/:id/applies/reject_collection` — Rejeitar Candidaturas em Lote

**Body:** Mesmo formato do `approve_collection`.

---

### `POST /v1/users/jobs/:id/applies/send_reject_feedback` — Enviar Feedback de Rejeição

Dois modos: IA (generate=true) ou template manual.

#### Modo IA (gera feedback via LLM):

**Body:**

```json
{
  "generate": true,
  "reference_ids": [100, 101, 102],
  "select_all_params": null
}
```

#### Modo Template:

**Body:**

```json
{
  "generate": false,
  "reference_ids": [100, 101, 102],
  "subject": "Retorno sobre sua candidatura",
  "description": "Agradecemos seu interesse...",
  "name": "Feedback padrão"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `generate` | boolean | `true` = gera via IA; `false` = usa template |
| `reference_ids` | array[int] | IDs dos applies (max: 50) |
| `select_all_params` | object | Alternativa ao reference_ids (modo IA) |
| `subject` | string | Assunto do email (obrigatório no modo template) |
| `description` | string | Conteúdo do feedback (obrigatório no modo template) |

**Response (200):**

```json
{
  "data": {
    "attributes": {
      "status": "processing",
      "message": "Os feedbacks estão sendo gerados em background",
      "job_id": 123
    }
  }
}
```

---

## 7. Analytics e Stats

### `GET /v1/users/jobs/:id/analytics` — Analytics de uma Vaga

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `force_refresh` | boolean | Forçar recálculo do cache |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "total_applies": 42,
    "applies_by_source": { "web_response": 30, "sourcing": 12 },
    "applies_by_stage": [
      { "stage": "Triagem", "count": 20 },
      { "stage": "Entrevista", "count": 15 }
    ],
    "conversion_rates": { "triagem_to_entrevista": 0.75 },
    "avg_time_in_stage_days": { "Triagem": 3.2, "Entrevista": 5.1 },
    "screening_stats": { "avg_score": 72.5, "completion_rate": 0.85 },
    "timeline": [
      { "date": "2026-01-15", "applies_count": 5 }
    ]
  }
}
```

---

### `POST /v1/users/jobs/bulk_analytics` — Analytics em Lote

**Body:**

```json
{
  "job_ids": [1, 2, 3],
  "where": { "is_active": true },
  "force_refresh": false,
  "limit": 50
}
```

**Response (200):**

```json
{
  "success": true,
  "jobs": [
    { "job_id": 1, "analytics": { "..." : "..." } },
    { "job_id": 2, "analytics": { "..." : "..." } }
  ],
  "meta": { "total": 3, "processed": 3 }
}
```

---

### `GET /v1/users/jobs/stats` — Estatísticas Gerais

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `start_date` | string | Data início (ISO 8601) |
| `end_date` | string | Data fim (ISO 8601) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "total_jobs": 150,
    "active_jobs": 80,
    "paused_jobs": 20,
    "archived_jobs": 50,
    "total_applies": 3200,
    "avg_applies_per_job": 21.3
  }
}
```

---

### `GET /v1/users/jobs/alerts` — Alertas de Vagas

**Response (200):**

```json
{
  "success": true,
  "data": [
    {
      "job_id": 123,
      "job_title": "Dev Backend",
      "alert_type": "deadline_approaching",
      "message": "Prazo de candidatura expira em 3 dias"
    }
  ]
}
```

---

### `GET /v1/users/jobs/pipeline_health` — Saúde do Pipeline

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `job_ids` | string | IDs separados por vírgula: `1,2,3` |
| `include_inactive` | boolean | Incluir vagas inativas |
| `aging_threshold_days` | integer | Dias limite para considerar "stale" |
| `limit` | integer | Limite de vagas |

**Response (200):**

```json
{
  "success": true,
  "jobs": [
    {
      "job_id": 123,
      "title": "Dev Backend",
      "health_score": 0.75,
      "bottlenecks": ["Triagem"],
      "stale_applies_count": 5,
      "avg_days_open": 30
    }
  ]
}
```

---

## 8. AI / Sugestões / Matching

### `POST /v1/users/jobs/:job_id/suggestion` — Sugestão de Descrição via IA

**Body:**

```json
{
  "type": "description"
}
```

**Response (200):**

```json
{
  "suggestion": "Estamos procurando um profissional experiente..."
}
```

---

### `POST /v1/users/jobs/:id/suggestion/questions` — Gerar Perguntas de Avaliação via IA (WSI)

**Body:**

```json
{
  "type": "wsi_compact",
  "evaluation_id": 10,
  "query": "perguntas técnicas sobre Ruby on Rails"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `type` | string | `wsi_compact`, `wsi_compact_plus` ou `query` |
| `evaluation_id` | integer | (Opcional) Se informado, cria as perguntas na avaliação |
| `query` | string | (Para type=query) Descrição livre do que gerar |

**Response (200) — sem evaluation_id:**

```json
{
  "questions": [
    {
      "title": "Descreva uma situação em que...",
      "competence_type": "técnica",
      "response_type": "text",
      "category": "situacional",
      "framework_weights": { "bloom": 0.3, "dreyfus": 0.4, "big_five": 0.2, "cbi": 0.1 },
      "validation_type_weight": { "text": 1.0 }
    }
  ]
}
```

**Response (200) — com evaluation_id:**

```json
{
  "questions": [ "..." ],
  "created_questions": [
    { "id": 1, "title": "Descreva uma situação em que..." }
  ]
}
```

---

### `POST /v1/users/jobs/generate_query_from_job` — Gerar Query de Busca a Partir de Vagas Recentes

**Body:** Nenhum.

**Response (200):**

```json
[
  {
    "job_id": 123,
    "job_title": "Dev Backend",
    "query": "Ruby Rails PostgreSQL API senior"
  }
]
```

---

### `GET /v1/users/jobs/:id/matching_candidates` — Candidatos Matching (Vector Search)

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `top_k` | integer | Candidatos no pool de busca (1-2000, default: 500) |
| `page` | integer | Página |
| `per_page` | integer | Itens por página (1-100, default: 20) |
| `min_score` | float | Score mínimo (0.0-1.0) |
| `max_score` | float | Score máximo (0.0-1.0) |
| `filters[city]` | string | Filtrar por cidade |
| `filters[skills]` | string | Filtrar por skills |
| `include` | string | Campos extras: `skills,languages` |

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "50",
      "type": "job_candidate_match",
      "attributes": {
        "candidate_id": 50,
        "name": "Ana Souza",
        "email": "ana@email.com",
        "city": "São Paulo",
        "score": 0.87,
        "skills": ["Ruby", "Rails", "PostgreSQL"]
      }
    }
  ],
  "meta": {
    "total_count": 250,
    "page": 1,
    "per_page": 20,
    "total_pages": 13
  }
}
```

---

### `GET /v1/users/jobs/matches/candidates` — Matching com Modo Compacto

**Query Params:** Mesmos do `matching_candidates` + `compact` (campos CSV).

| Param | Tipo | Descrição |
|---|---|---|
| `job_id` | integer | ID do job (via rota) |
| `compact` | string | Campos a retornar: `id,name,score` |

**Response com compact (200):**

```json
{
  "data": [
    { "id": 50, "name": "Ana Souza", "score": 0.87 }
  ],
  "meta": { "total_count": 250 }
}
```

---

### `GET /v1/users/jobs/:id/context_for_ai` — Contexto da Vaga para IA

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `tier` | integer | 1 = básico, 2 = completo com analytics |

**Response Tier 1 (200):**

```json
{
  "success": true,
  "data": {
    "job": {
      "id": 123,
      "title": "Desenvolvedor Backend",
      "description": "...",
      "city": "São Paulo",
      "state": "SP",
      "seniority_text": "Sênior",
      "employment_type_text": "CLT",
      "skills": ["Ruby", "Rails"],
      "benefits": ["VR", "Plano de Saúde"],
      "responsibilities": ["Desenvolver APIs"],
      "salary_from": 8000,
      "salary_to": 15000,
      "completeness_percentage": 85,
      "is_ready_for_publication": true,
      "missing_fields": [],
      "cached_applies_count": 42
    },
    "pipeline_summary": [
      { "id": 1, "name": "Triagem", "count": 20 }
    ]
  }
}
```

**Response Tier 2 (200):** Tier 1 + `analytics` + `recent_activity`.

---

### `POST /v1/users/jobs/boolean_search` — Gerar Busca Booleana via IA

**Body:**

```json
{
  "job_id": 123
}
```

> Publica mensagem via WebSocket com busca booleana gerada com base nas skills da vaga.

---

## 9. Auto Source (Sourcing Automático)

### `POST /v1/users/jobs/:id/auto_source` — Iniciar Auto Source

**Body:**

```json
{
  "limit": 30,
  "min_score": 70,
  "sources": ["local", "global"],
  "reset": false
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `limit` | integer | Candidatos a buscar (1-100, default: 30) |
| `min_score` | float | Score mínimo (0-100, default: 70) |
| `sources` | array | `["local"]`, `["global"]` ou `["local", "global"]` |
| `reset` | boolean | Resetar state anterior |

**Response (202):**

```json
{
  "success": true,
  "sourcing_id": 456,
  "uid": "abc-123",
  "status": "started",
  "job_id": 123,
  "min_score_threshold": 70.0,
  "target_count": 30,
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "processed": 0,
    "total": 30
  },
  "subscription": {
    "channel": "SourcingChannel",
    "stream": "1_sourcing_456",
    "events": [
      "auto_source_started",
      "profile_analyzed",
      "auto_source_batch_completed",
      "auto_source_finished"
    ]
  },
  "message": "Auto Source started. Subscribe to channel for real-time updates."
}
```

---

## 10. Estrutura Organizacional

### `GET /v1/users/jobs/:job_id/organizational_structure` — Ver Estrutura

**Response (200):**

```json
{
  "structure": {
    "department": { "name": "Engenharia", "parent": null },
    "hiring_manager": { "name": "Maria", "title": "VP Engenharia", "email": "maria@company.com" },
    "team": {
      "name": "Backend Team",
      "size": 8,
      "description": "Time de backend",
      "composition": [
        { "role": "Senior Dev", "count": 3, "description": null },
        { "role": "Pleno Dev", "count": 5, "description": null }
      ]
    },
    "reports_to": { "position": "Tech Lead", "name": "Carlos" }
  },
  "complete": false,
  "completion_percentage": 75,
  "suggestions": ["Adicione reports_to"],
  "warnings": [],
  "job_id": "123"
}
```

---

### `POST /v1/users/jobs/:job_id/organizational_structure` — Criar Estrutura

### `PATCH /v1/users/jobs/:job_id/organizational_structure` — Atualizar Estrutura

**Body:**

```json
{
  "organizational_data": {
    "department": { "name": "Engenharia", "parent": "Tecnologia" },
    "hiring_manager": { "name": "Maria", "title": "VP", "email": "maria@co.com" },
    "team": {
      "name": "Backend",
      "size": 8,
      "description": "Team desc",
      "composition": [
        { "role": "Senior Dev", "count": 3 }
      ]
    },
    "reports_to": { "position": "CTO", "name": "João" }
  }
}
```

**Response (201/200):**

```json
{
  "structure": { "..." : "..." },
  "complete": true,
  "completion_percentage": 100,
  "suggestions": [],
  "warnings": [],
  "success": true,
  "changes": ["department_updated", "team_created"],
  "errors": [],
  "job_id": 123
}
```

---

## 11. Activity Logs

### `GET /v1/users/jobs/:job_id/activity_log` — Logs de Atividade

**Query Params:** Mesmos do Searchkick (search, where, order, page, per_page).

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "500",
      "type": "activity_log",
      "attributes": {
        "action": "update",
        "reference_type": "Job",
        "reference_id": 123,
        "user_id": 1,
        "user_name": "João",
        "changes": { "title": ["Título antigo", "Título novo"] },
        "created_at": "2026-03-01T14:00:00Z"
      }
    }
  ]
}
```

---

## 12. Evaluations (Avaliações da Vaga)

### `GET /v1/users/jobs/:job_id/evaluations` — Listar Avaliações da Vaga

**Query Params:** Searchkick padrão.

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "10",
      "type": "evaluation",
      "attributes": {
        "name": "Avaliação Técnica",
        "job_id": 123,
        "status": "active",
        "questions_count": 15,
        "created_at": "2026-01-20T10:00:00Z"
      }
    }
  ]
}
```

---

### `POST /v1/users/evaluations/:evaluation_id/:job_id/generate_report` — Gerar Relatório de Avaliação

**Body:** Nenhum.

**Response (200):** Relatório gerado da avaliação.

---

## 13. Selective Processes (Etapas)

### `GET /v1/users/selective_processes` — Listar Etapas

**Query Params:** Searchkick padrão + `where[job_id]`.

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "1",
      "type": "selective_process",
      "attributes": {
        "name": "Triagem",
        "position": 0,
        "status": "active",
        "job_id": 123,
        "external_id": "triagem-1",
        "color": "#4CAF50",
        "sub_status": ["Em análise", "Aguardando"],
        "approved_process_id": 2,
        "rejected_process_id": null
      }
    }
  ]
}
```

---

### `GET /v1/users/selective_processes/:id` — Detalhe

### `POST /v1/users/selective_processes` — Criar Etapa

**Body:**

```json
{
  "selective_process": {
    "name": "Entrevista Final",
    "position": 3,
    "job_id": 123,
    "status": "active",
    "external_id": "entrevista-final",
    "color": "#FF9800",
    "sub_status": ["Agendada", "Realizada"],
    "approved_process_id": null,
    "rejected_process_id": null
  }
}
```

### `PUT /v1/users/selective_processes/:id` — Atualizar

### `DELETE /v1/users/selective_processes/:id` — Deletar (soft-delete)

### `POST /v1/users/selective_processes/order` — Reordenar Etapas

**Body:**

```json
{
  "selective_processes": [
    { "id": 1, "position": 0 },
    { "id": 2, "position": 1 },
    { "id": 3, "position": 2 }
  ]
}
```

---

## 14. Job Journeys (Jornadas)

### `GET /v1/users/job_journeys` — Listar

**Query Params:** Searchkick padrão + `where[job_id]`.

### `GET /v1/users/job_journeys/:id` — Detalhe

### `POST /v1/users/job_journeys` — Criar

**Body:**

```json
{
  "job_journey": {
    "name": "Revisão Técnica",
    "description": "Etapa de revisão de código",
    "position": 2,
    "active": true,
    "required": true,
    "job_id": null
  }
}
```

### `PUT /v1/users/job_journeys/:id` — Atualizar

### `DELETE /v1/users/job_journeys/:id` — Deletar

### `PUT /v1/users/job_journeys/update_positions` — Reordenar

**Body:**

```json
{
  "job_journeys": [
    { "id": 1, "position": 0 },
    { "id": 2, "position": 1 }
  ]
}
```

---

## 15. Job Field Templates

### `GET /v1/users/job_field_templates` — Listar Templates

### `GET /v1/users/job_field_templates/:id` — Detalhe

### `POST /v1/users/job_field_templates` — Criar Template

**Body:**

```json
{
  "job_field_template": {
    "name": "Template Padrão Tech",
    "is_default": true,
    "fields": [
      {
        "label": "Título da Vaga",
        "category": "basic",
        "priority": 1,
        "field_name": "title",
        "is_required": true,
        "job_journey_position": 0
      },
      {
        "label": "Descrição",
        "category": "basic",
        "priority": 2,
        "field_name": "description",
        "is_required": true,
        "job_journey_position": 0
      }
    ]
  }
}
```

### `PUT /v1/users/job_field_templates/:id` — Atualizar

### `DELETE /v1/users/job_field_templates/:id` — Deletar

### `GET /v1/users/job_field_templates/default_fields` — Campos Padrão do Sistema

**Response (200):**

```json
{
  "data": {
    "type": "default_fields",
    "attributes": {
      "fields": [
        { "field_name": "title", "label": "Título", "category": "basic", "is_required": true },
        { "field_name": "description", "label": "Descrição", "category": "basic" }
      ]
    }
  }
}
```

> Também existe a versão admin: `GET /v1/users/admin/job_field_templates/*` (mesmos endpoints).

---

## 16. Job Statuses

### `GET /v1/users/job_statuses` — Listar

### `GET /v1/users/job_statuses/:id` — Detalhe

### `POST /v1/users/job_statuses` — Criar

**Body:**

```json
{
  "job_status": {
    "name": "Em andamento",
    "color": "#4CAF50"
  }
}
```

### `PUT /v1/users/job_statuses/:id` — Atualizar

### `DELETE /v1/users/job_statuses/:id` — Deletar

---

## 17. Job Users (Times da Vaga)

### `GET /v1/users/job_users` — Listar

### `GET /v1/users/job_users/:id` — Detalhe

### `POST /v1/users/job_users` — Criar (vincular usuário à vaga)

**Body:**

```json
{
  "job_user": {
    "user_id": 5,
    "job_id": 123,
    "person_function": "recruiter",
    "split": 50
  }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `user_id` | integer | ID do usuário |
| `job_id` | integer | ID da vaga |
| `person_function` | string | Papel: recruiter, hiring_manager, etc |
| `split` | integer | Percentual de split/comissão |

### `PUT /v1/users/job_users/:id` — Atualizar

### `DELETE /v1/users/job_users/:id` — Deletar

---

## 18. Apply Statuses

### `GET /v1/users/apply_statuses` — Listar

### `GET /v1/users/apply_statuses/:id` — Detalhe

### `POST /v1/users/apply_statuses` — Criar

**Body:**

```json
{
  "apply_status": {
    "apply_id": 100,
    "selective_process_id": 1,
    "status_name": "Em análise",
    "user_id": 1
  }
}
```

### `PUT /v1/users/apply_statuses/:id` — Atualizar

### `DELETE /v1/users/apply_statuses/:id` — Deletar (soft-delete)

---

## 19. Enums / Lookups

Endpoints que retornam listas fixas de opções. Nenhum body necessário.

### `GET /v1/users/jobs/priorities`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Não informado", "id": null } },
    { "id": "1", "attributes": { "name": "Alta", "id": 1 } },
    { "id": "2", "attributes": { "name": "Média", "id": 2 } },
    { "id": "3", "attributes": { "name": "Baixa", "id": 3 } }
  ]
}
```

### `GET /v1/users/jobs/urgency_levels`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Não informado", "id": null } },
    { "id": "1", "attributes": { "name": "Baixa", "id": 1 } },
    { "id": "2", "attributes": { "name": "Moderada", "id": 2 } },
    { "id": "3", "attributes": { "name": "Média", "id": 3 } },
    { "id": "4", "attributes": { "name": "Alta", "id": 4 } },
    { "id": "5", "attributes": { "name": "Crítica", "id": 5 } }
  ]
}
```

### `GET /v1/users/jobs/workplace_types`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Não informado", "id": null } },
    { "id": "1", "attributes": { "name": "Remoto", "id": 1 } },
    { "id": "2", "attributes": { "name": "Híbrido", "id": 2 } },
    { "id": "3", "attributes": { "name": "Presencial", "id": 3 } }
  ]
}
```

### `GET /v1/users/jobs/employment_types`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "CLT", "id": 0 } },
    { "id": "1", "attributes": { "name": "PJ", "id": 1 } },
    { "id": "2", "attributes": { "name": "Estágio", "id": 2 } },
    { "id": "3", "attributes": { "name": "Temporário", "id": 3 } },
    { "id": "4", "attributes": { "name": "Freelancer", "id": 4 } },
    { "id": "5", "attributes": { "name": "Aprendiz", "id": 5 } }
  ]
}
```

### `GET /v1/users/jobs/seniorities`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Júnior", "id": 0 } },
    { "id": "1", "attributes": { "name": "Pleno", "id": 1 } },
    { "id": "2", "attributes": { "name": "Sênior", "id": 2 } },
    { "id": "3", "attributes": { "name": "Especialista", "id": 3 } },
    { "id": "4", "attributes": { "name": "Estágio", "id": 4 } },
    { "id": "5", "attributes": { "name": "Lead", "id": 5 } },
    { "id": "6", "attributes": { "name": "Gerente", "id": 6 } },
    { "id": "7", "attributes": { "name": "Diretor", "id": 7 } }
  ]
}
```

### `GET /v1/users/jobs/pcd_categories`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Não informado", "id": null } },
    { "id": "1", "attributes": { "name": "Gênero", "id": 1 } },
    { "id": "2", "attributes": { "name": "Raça/Etnia", "id": 2 } },
    { "id": "3", "attributes": { "name": "PCD", "id": 3 } },
    { "id": "4", "attributes": { "name": "LGBTQIA+", "id": 4 } },
    { "id": "5", "attributes": { "name": "50+", "id": 5 } },
    { "id": "6", "attributes": { "name": "Refugiado", "id": 6 } },
    { "id": "7", "attributes": { "name": "Indígena", "id": 7 } },
    { "id": "8", "attributes": { "name": "Outro", "id": 8 } }
  ]
}
```

### `GET /v1/users/jobs/confidential_types`

```json
{
  "data": [
    { "id": "0", "attributes": { "name": "Não informado", "id": null } },
    { "id": "1", "attributes": { "name": "Pública", "id": 1 } },
    { "id": "2", "attributes": { "name": "Interna", "id": 2 } },
    { "id": "3", "attributes": { "name": "Confidencial", "id": 3 } }
  ]
}
```

---

## 20. Rotas Públicas (Sem Auth)

### `GET /v1/vagas/:slug/:account_slug` — Ver Vaga Pública

Sem autenticação. Retorna apenas vagas publicadas.

**Response (200 — JSON:API):**

```json
{
  "data": {
    "id": "123",
    "type": "public_job",
    "attributes": {
      "title": "Desenvolvedor Fullstack",
      "description": "<p>Descrição...</p>",
      "city": "São Paulo",
      "state": "SP",
      "country": "Brasil",
      "department_name": "Engenharia",
      "employment_type_text": "CLT",
      "seniority_text": "Sênior",
      "workplace_type_text": "Híbrido",
      "disabilities": false,
      "confidential_company_name": null,
      "responsibilities": ["Desenvolver features"],
      "sector": "Tecnologia",
      "skills": ["Ruby", "Rails", "PostgreSQL"],
      "languages_data": [
        { "name": "Inglês", "level": "Avançado" }
      ],
      "behavioral_skills": ["Proatividade", "Trabalho em equipe"],
      "benefits": [
        { "name": "Vale Refeição", "value": "800" },
        { "name": "Plano de Saúde", "value": null }
      ]
    }
  }
}
```

---

### `POST /v1/vagas/:slug/:account_slug/applications` — Candidatura Pública

Sem autenticação. Aceita `multipart/form-data` (para upload de currículo).

**Body (form-data):**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | string | Sim | Nome do candidato |
| `email` | string | Sim | Email do candidato |
| `mobile_phone` | string | Não | Telefone |
| `curriculum` | file | Não* | Arquivo do currículo (PDF, DOC) |
| `curriculum_text` | string | Não* | Texto do currículo |
| `accept_terms` | boolean | Sim | Aceite dos termos |

> *Pelo menos um: `curriculum` (file) ou `curriculum_text`.

**Alternativa (JSON):**

```json
{
  "application": {
    "name": "Ana Souza",
    "email": "ana@email.com",
    "mobile_phone": "11999999999",
    "curriculum_text": "Experiência profissional...",
    "accept_terms": true
  }
}
```

**Response (201 — JSON:API):**

```json
{
  "data": {
    "id": "500",
    "type": "public_apply",
    "attributes": {
      "candidate_name": "Ana Souza",
      "job_title": "Desenvolvedor Fullstack",
      "status": "pending",
      "created_at": "2026-03-18T10:00:00Z"
    }
  }
}
```

**Response (409 — Conflito):**

```json
{
  "errors": ["Candidato já se candidatou a esta vaga"]
}
```

---

## Exportação

### `GET /v1/users/jobs/:id/export` — Exportar Vaga

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `format` | string | `csv` (default) |

**Response:** Download direto do arquivo (CSV).

---

### `GET /v1/users/jobs/data_for_description` — Dados para Geração de Descrição

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `job_id` | integer | ID do job |

**Response (200):** Job serializado com `includes: [remunerations, benefits, skills, languages]`.
