# API Applies — Referência Completa

Documentação detalhada de todos os endpoints relacionados a **Applies** (candidaturas) do ATS WeDO Talent.

**Base URL:** `/v1/users`
**Autenticação:** JWT Bearer Token (header `Authorization: Bearer <token>`)
**Formato:** JSON:API (exceto endpoints de stats/analytics que retornam JSON puro)

---

## Índice

1. [Applies CRUD](#1-applies-crud)
   - [GET /applies — Listar Applies](#11-get-applies--listar-applies)
   - [GET /applies/:id — Detalhe de Apply](#12-get-appliesid--detalhe-de-apply)
   - [POST /applies — Criar Apply](#13-post-applies--criar-apply)
   - [PUT /applies/:id — Atualizar Apply](#14-put-appliesid--atualizar-apply)
   - [DELETE /applies/:id — Deletar Apply (soft-delete)](#15-delete-appliesid--deletar-apply-soft-delete)
2. [Applies Collection (Bulk)](#2-applies-collection-bulk)
   - [POST /applies/create_collection — Criar em lote](#21-post-appliescreate_collection--criar-em-lote)
   - [PUT /applies/update_collection — Atualizar em lote](#22-put-appliesupdate_collection--atualizar-em-lote)
   - [DELETE /applies/delete_collection — Deletar em lote](#23-delete-appliesdelete_collection--deletar-em-lote)
3. [Applies Timeline](#3-applies-timeline)
   - [GET /applies/:id/timeline — Timeline do Apply](#31-get-appliesidtimeline--timeline-do-apply)
4. [Applies Stats e Analytics](#4-applies-stats-e-analytics)
   - [GET /applies/stats — Estatísticas](#41-get-appliesstats--estatísticas)
   - [GET /applies/aging — Candidaturas Paradas](#42-get-appliesaging--candidaturas-paradas)
5. [Kanban (Job Applies)](#5-kanban-job-applies)
   - [GET /jobs/:job_id/kanban — Kanban do Job](#51-get-jobsjob_idkanban--kanban-do-job)
6. [Job Applies Actions](#6-job-applies-actions)
   - [POST /jobs/:id/applies/approve_collection — Aprovar em lote](#61-post-jobsidappliesapprove_collection--aprovar-em-lote)
   - [POST /jobs/:id/applies/reject_collection — Rejeitar em lote](#62-post-jobsidappliesreject_collection--rejeitar-em-lote)
   - [POST /jobs/:id/applies/send_reject_feedback — Enviar feedback de rejeição](#63-post-jobsidappliessend_reject_feedback--enviar-feedback-de-rejeição)
7. [Apply Statuses CRUD](#7-apply-statuses-crud)
   - [GET /apply_statuses — Listar](#71-get-apply_statuses--listar)
   - [GET /apply_statuses/:id — Detalhe](#72-get-apply_statusesid--detalhe)
   - [POST /apply_statuses — Criar](#73-post-apply_statuses--criar)
   - [PUT /apply_statuses/:id — Atualizar](#74-put-apply_statusesid--atualizar)
   - [DELETE /apply_statuses/:id — Deletar (soft-delete)](#75-delete-apply_statusesid--deletar-soft-delete)

---

## 1. Applies CRUD

### 1.1 GET /applies — Listar Applies

Retorna lista paginada de applies com busca full-text via Searchkick.

**URL:** `GET /v1/users/applies`

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `term` | string | Não | Termo de busca full-text (nome, email, cargo, etc.). Default: `"*"` (todos) |
| `search` | string | Não | Alternativa ao `term` para busca |
| `page` | integer | Não | Página atual (default: 1) |
| `per_page` | integer | Não | Itens por página (default: 30, max: 30) |
| `where` | JSON string/object | Não | Filtros estruturados (ver tabela abaixo) |
| `order` | JSON string/object | Não | Ordenação. Default: `{ "created_at": "desc" }` |
| `filter` | JSON string/object | Não | Filtros alternativos (mesma estrutura que `where`) |
| `compact` | string (CSV) | Não | Campos a retornar em modo compacto (ex: `"id,name,email"`) |
| `boost_where` | JSON string | Não | Campos para boost na busca |

#### Filtros disponíveis (`where`)

| Campo | Tipo | Exemplo |
|---|---|---|
| `job_id` | integer | `{ "job_id": 123 }` |
| `candidate_id` | integer | `{ "candidate_id": 456 }` |
| `selective_process_id` | integer | `{ "selective_process_id": 10 }` |
| `selective_process_status` | string | `{ "selective_process_status": "interview" }` |
| `evaluation_candidate_status` | string | `"pending"`, `"sent"`, `"answered"` |
| `source` | string | `"web_response"`, `"sourcing"`, `"manual"` |
| `is_deleted` | boolean | `false` (default aplicado automaticamente) |
| `city` | string | `{ "city": "São Paulo" }` |
| `state` | string | `{ "state": "SP" }` |
| `remote_work` | string | Filtro por tipo de trabalho remoto |
| `cv_match` | range object | `{ "cv_match": { "gte": 50 } }` |
| `total_score` | range object | `{ "total_score": { "gte": 70 } }` |
| `created_at` | range object | `{ "created_at": { "gte": "2024-01-01", "lte": "2024-12-31" } }` |
| `candidate_feedback` | string | Tipo de feedback do candidato |
| `pin_user_ids` | integer | ID do usuário para filtrar pinados |

#### Ordenação (`order`)

| Campo | Direção |
|---|---|
| `created_at` | `asc` / `desc` |
| `updated_at` | `asc` / `desc` |
| `name` | `asc` / `desc` |
| `cv_match` | `asc` / `desc` |
| `total_score` | `asc` / `desc` |
| `_score` | `desc` (relevância da busca) |

#### Response (200 OK) — JSON:API

```json
{
  "data": [
    {
      "id": "123",
      "type": "apply",
      "attributes": {
        "id": 123,
        "candidate_id": 456,
        "job_id": 789,
        "selective_process_id": 10,
        "selective_process_name": "Triagem",
        "selective_process_status": "screening",
        "evaluation_candidate_status": "pending",
        "name": "João Silva",
        "email": "joao@email.com",
        "phone": "11999999999",
        "secondary_phone": null,
        "linkedin": "https://linkedin.com/in/joaosilva",
        "github": "https://github.com/joaosilva",
        "avatar_url": "https://storage.example.com/avatar.jpg",
        "curriculum_pdf_url": "https://storage.example.com/cv.pdf",
        "portfolio": "https://joaosilva.dev",
        "current_company": "Empresa Atual",
        "role_name": "Desenvolvedor Full Stack",
        "position_level": "senior",
        "self_introduction": "Texto de apresentação...",
        "curriculum_text": "Texto do currículo extraído...",
        "date_birth": "1990-05-15",
        "gender": "Masculino",
        "nationality": "Brasileiro",
        "marital_status": "Solteiro",
        "cpf": "123.456.789-00",
        "street": "Rua Exemplo",
        "number": "100",
        "district": "Centro",
        "zip": "01001-000",
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "complement": "Apto 101",
        "clt_expectation": 12000.0,
        "pj_expectation": 15000.0,
        "freelance_expectation": null,
        "current_salary": 10000.0,
        "desired_salary": 14000.0,
        "currency": "BRL",
        "remote_work": "hybrid",
        "mobility": "Sim",
        "interests": "Backend, DevOps",
        "comments": "Observações do candidato",
        "source": "web_response",
        "completed_register": true,
        "accept_terms": true,
        "is_deleted": false,
        "evaluation_candidate_scores": {
          "teste_tecnico_1": 85.0,
          "entrevista_cultural_2": 70.0
        },
        "evaluation_candidate_summaries": {
          "teste_tecnico_1": "Candidato demonstrou boa performance...",
          "entrevista_cultural_2": "Alinhamento com valores da empresa..."
        },
        "cv_match": 78.5,
        "total_score": 72.3,
        "alerts": [
          { "type": "approve", "timestamp": "2024-06-01T10:30:00Z" }
        ],
        "color": "#3498db",
        "is_candidate_favorite": false,
        "created_at": "2024-06-01T10:00:00.000Z",
        "updated_at": "2024-06-05T14:30:00.000Z",
        "external_id": "EXT-001",
        "sub_status": "aguardando_retorno",
        "is_screening_sent": false,
        "meetings": [
          {
            "id": 1,
            "reference_type": "Apply",
            "reference_id": 123,
            "role": "candidate",
            "meeting_id": 50,
            "calendar_event_id": 25,
            "join_url": "https://meet.example.com/abc",
            "provider_text": "Google Meet"
          }
        ],
        "url": "/user/jobs/789/applies/123",
        "pin": false,
        "confidential": false,
        "candidate_feedback": "positive"
      }
    }
  ],
  "meta": {
    "total": 150,
    "where": { "job_id": 789, "is_deleted": false }
  }
}
```

#### Response compacto (com `compact=id,name,email`)

```json
{
  "data": [
    { "id": 123, "name": "João Silva", "email": "joao@email.com" }
  ],
  "meta": { "total": 150 }
}
```

---

### 1.2 GET /applies/:id — Detalhe de Apply

**URL:** `GET /v1/users/applies/:id`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID do apply |

#### Response (200 OK) — JSON:API

Mesma estrutura de um item da listagem (seção 1.1), porém dentro de `data` (objeto único, não array).

```json
{
  "data": {
    "id": "123",
    "type": "apply",
    "attributes": {
      "id": 123,
      "candidate_id": 456,
      "job_id": 789,
      "selective_process_id": 10,
      "selective_process_name": "Triagem",
      "selective_process_status": "screening",
      "...": "... todos os campos da listagem ..."
    }
  }
}
```

#### Response (404 Not Found)

```json
{
  "error": "Apply not found"
}
```

---

### 1.3 POST /applies — Criar Apply

Cria um novo apply (candidatura). Se o candidato já tiver um apply ativo para a mesma vaga, retorna o existente. Se existir um apply deletado, reativa.

**URL:** `POST /v1/users/applies`

#### Request Body

```json
{
  "apply": {
    "candidate_id": 456,
    "job_id": 789,
    "selective_process_id": 10,
    "selective_process_status": "screening",
    "source": "manual",
    "account_id": 1
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `candidate_id` | integer | Sim* | ID do candidato |
| `job_id` | integer | Sim* | ID da vaga |
| `selective_process_id` | integer | Não | ID do processo seletivo (etapa) |
| `selective_process_status` | string | Não | Status do processo seletivo. Auto-preenchido se `selective_process_id` fornecido |
| `source` | string | Não | Origem da candidatura (ex: `"manual"`, `"web_response"`, `"sourcing"`) |
| `account_id` | integer | Não | ID da conta. Default: conta do usuário autenticado |
| `external_candidate_id` | string | Não | ID externo do candidato (alternativa ao `candidate_id`) |
| `external_job_id` | string | Não | ID externo da vaga (alternativa ao `job_id`) |
| `external_id` | string | Não | ID externo do apply |
| `sub_status` | string | Não | Sub-status da candidatura |
| `reason_for_reject` | string | Não | Motivo da rejeição |
| `reason_code` | string | Não | Código do motivo de rejeição |
| `reason_category` | string | Não | Categoria do motivo de rejeição |
| `internal_comment` | string | Não | Comentário interno |
| `is_screening_sent` | boolean | Não | Se a triagem foi enviada |

> *`candidate_id` e `job_id` são obrigatórios. Podem ser substituídos por `external_candidate_id` e `external_job_id` respectivamente.

#### Response (201 Created) — JSON:API

```json
{
  "data": {
    "id": "123",
    "type": "apply",
    "attributes": {
      "id": 123,
      "candidate_id": 456,
      "job_id": 789,
      "selective_process_id": 10,
      "selective_process_name": "Triagem",
      "selective_process_status": "screening",
      "source": "manual",
      "...": "... todos os campos ..."
    }
  }
}
```

#### Response (422 Unprocessable Entity)

```json
{
  "errors": ["candidate_id e job_id são obrigatórios"]
}
```

---

### 1.4 PUT /applies/:id — Atualizar Apply

**URL:** `PUT /v1/users/applies/:id`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID do apply |

#### Request Body

```json
{
  "apply": {
    "selective_process_id": 15,
    "selective_process_status": "interview",
    "sub_status": "aguardando_retorno",
    "pin": true,
    "confidential": false,
    "reason_for_reject": null,
    "internal_comment": "Candidato aprovado para entrevista"
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `selective_process_id` | integer | Não | Nova etapa do processo seletivo |
| `selective_process_status` | string | Não | Novo status. Auto-preenchido se `selective_process_id` fornecido |
| `sub_status` | string | Não | Sub-status da candidatura |
| `pin` | boolean | Não | Fixar/desfixar apply para o usuário atual |
| `confidential` | boolean | Não | Marcar/desmarcar como confidencial para o usuário |
| `reason_for_reject` | string | Não | Motivo da rejeição |
| `reason_code` | string | Não | Código do motivo de rejeição |
| `reason_category` | string | Não | Categoria do motivo de rejeição |
| `internal_comment` | string | Não | Comentário interno |
| `is_screening_sent` | boolean | Não | Se a triagem foi enviada |
| `is_deleted` | boolean | Não | Soft-delete flag |

#### Response (200 OK) — JSON:API

Mesma estrutura do show (seção 1.2).

#### Response (422 Unprocessable Entity)

```json
{
  "errors": { "field": ["mensagem de erro"] }
}
```

---

### 1.5 DELETE /applies/:id — Deletar Apply (soft-delete)

Marca o apply como deletado (`is_deleted: true`). Não remove fisicamente o registro.

**URL:** `DELETE /v1/users/applies/:id`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID do apply |

#### Response (200 OK) — JSON:API

Retorna o apply com `is_deleted: true`.

---

## 2. Applies Collection (Bulk)

### 2.1 POST /applies/create_collection — Criar em lote

Cria múltiplos applies de forma assíncrona (background job).

**URL:** `POST /v1/users/applies/create_collection`

#### Formato 1: Via `select_all_params` (busca)

Usa parâmetros de busca para selecionar candidatos.

```json
{
  "select_all_params": {
    "term": "*",
    "where": { "job_id": 789 },
    "page": 1,
    "per_page": 30
  },
  "apply": {
    "job_id": 100,
    "selective_process_id": 10,
    "selective_process_status": "screening"
  }
}
```

#### Formato 2: Via `collections` (lista explícita)

```json
{
  "collections": [
    { "candidate_id": 1 },
    { "candidate_id": 2 },
    { "reference_type": "SourcedProfile", "reference_id": 50 },
    { "reference_type": "SourcedProfileSourcing", "reference_id": 100 },
    { "reference_type": "Apply", "reference_id": 200 }
  ],
  "apply": {
    "job_id": 100,
    "selective_process_id": 10,
    "selective_process_status": "screening"
  }
}
```

#### Formato 3: Via `apply_collection` (combinado)

```json
{
  "apply_collection": {
    "job_id": 100,
    "selective_process_id": 10,
    "selective_process_status": "screening",
    "collections": [
      { "candidate_id": 1, "job_id": 100, "selective_process_id": 10 },
      { "candidate_id": 2, "job_id": 100, "selective_process_id": 10 }
    ]
  }
}
```

| Campo (`collections[]`) | Tipo | Descrição |
|---|---|---|
| `candidate_id` | integer | ID direto do candidato |
| `reference_type` | string | Tipo da referência: `"Candidate"`, `"SourcedProfile"`, `"SourcedProfileSourcing"`, `"Apply"` |
| `reference_id` | integer | ID da referência (resolve para candidate automaticamente) |

#### Response (200 OK)

```json
{
  "data": {
    "status": "processing",
    "message": "5 aplicações estão sendo processadas em background"
  }
}
```

---

### 2.2 PUT /applies/update_collection — Atualizar em lote

Atualiza múltiplos applies de forma assíncrona via `select_all_params`.

**URL:** `PUT /v1/users/applies/update_collection`

#### Request Body

```json
{
  "select_all_params": {
    "term": "*",
    "where": { "job_id": 789, "selective_process_status": "screening" }
  },
  "apply": {
    "selective_process_id": 15,
    "selective_process_status": "interview"
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `select_all_params` | object | Sim | Parâmetros de busca para seleção |
| `apply` | object | Sim | Campos a serem atualizados |

#### Response (200 OK)

```json
{
  "data": {
    "message": "As aplicações estão sendo atualizadas"
  }
}
```

---

### 2.3 DELETE /applies/delete_collection — Deletar em lote

Soft-delete em múltiplos applies de forma assíncrona.

**URL:** `DELETE /v1/users/applies/delete_collection`

#### Request Body

```json
{
  "select_all_params": {
    "term": "*",
    "where": { "job_id": 789, "selective_process_status": "rejected" }
  }
}
```

#### Response (200 OK)

```json
{
  "data": {
    "message": "As aplicações estão sendo deletadas"
  }
}
```

---

## 3. Applies Timeline

### 3.1 GET /applies/:id/timeline — Timeline do Apply

Retorna todo o histórico de eventos de uma candidatura.

**URL:** `GET /v1/users/applies/:id/timeline`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID do apply |

#### Response (200 OK) — JSON puro

```json
{
  "apply_id": 123,
  "candidate_name": "João Silva",
  "job_title": "Desenvolvedor Full Stack Senior",
  "current_stage": "Entrevista Técnica",
  "created_at": "2024-06-01T10:00:00.000Z",
  "timeline": [
    {
      "timestamp": "2024-06-01T10:00:00.000Z",
      "type": "apply_created",
      "description": "Candidatura recebida via web_response",
      "actor": "system"
    },
    {
      "timestamp": "2024-06-02T09:00:00.000Z",
      "type": "stage_change",
      "to": "Triagem",
      "stage_status": 0,
      "actor": "Maria Recrutadora"
    },
    {
      "timestamp": "2024-06-03T14:00:00.000Z",
      "type": "evaluation_sent",
      "evaluation": "Teste Técnico Python",
      "actor": "Maria Recrutadora"
    },
    {
      "timestamp": "2024-06-04T16:30:00.000Z",
      "type": "evaluation_completed",
      "evaluation": "Teste Técnico Python",
      "score": 8.5,
      "classification": "A"
    },
    {
      "timestamp": "2024-06-05T10:00:00.000Z",
      "type": "stage_change",
      "to": "Entrevista Técnica",
      "stage_status": 1,
      "actor": "Carlos Gestor"
    },
    {
      "timestamp": "2024-06-08T14:00:00.000Z",
      "type": "interview_scheduled",
      "title": "Entrevista Técnica - João Silva",
      "provider": "google_meet",
      "sub_status": "scheduled",
      "interviewer": "Carlos Gestor"
    },
    {
      "timestamp": "2024-06-03T11:00:00.000Z",
      "type": "dispatch_sent",
      "channel": "email",
      "subject": "Confirmação de candidatura",
      "status": "delivered"
    }
  ],
  "summary": {
    "days_in_pipeline": 7,
    "stages_visited": 3,
    "evaluations_completed": 1,
    "interviews_scheduled": 1
  }
}
```

#### Tipos de eventos na timeline

| Tipo | Descrição | Campos extras |
|---|---|---|
| `apply_created` | Candidatura criada | `description`, `actor` |
| `stage_change` | Mudança de etapa | `to`, `stage_status`, `actor` |
| `evaluation_sent` | Avaliação enviada | `evaluation`, `actor` |
| `evaluation_completed` | Avaliação respondida | `evaluation`, `score`, `classification` |
| `interview_scheduled` | Entrevista agendada | `title`, `provider`, `sub_status`, `interviewer` |
| `dispatch_sent` | Mensagem enviada | `channel`, `subject`, `status` |

#### Response (404 Not Found)

```json
{
  "error": "Apply not found"
}
```

---

## 4. Applies Stats e Analytics

### 4.1 GET /applies/stats — Estatísticas

Retorna estatísticas agregadas de applies com cache de 10 minutos.

**URL:** `GET /v1/users/applies/stats`

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `start_date` | date (YYYY-MM-DD) | Não | Data início (default: 30 dias atrás) |
| `end_date` | date (YYYY-MM-DD) | Não | Data fim (default: hoje) |
| `job_id` | integer | Não | Filtrar por vaga específica |
| `user_id` | integer | Não | Filtrar por recrutador responsável |

#### Response (200 OK) — JSON puro

```json
{
  "by_status": {
    "web_submission": 120,
    "screening": 85,
    "interview": 30,
    "hired": 5,
    "rejected": 45
  },
  "by_source": [
    { "source": "web_response", "count": 100, "percentage": 50.0 },
    { "source": "sourcing", "count": 60, "percentage": 30.0 },
    { "source": "manual", "count": 25, "percentage": 12.5 },
    { "source": "unknown", "count": 15, "percentage": 7.5 }
  ],
  "by_period": [
    { "date": "2024-06-01", "count": 12 },
    { "date": "2024-06-02", "count": 8 },
    { "date": "2024-06-03", "count": 15 }
  ],
  "conversion_rates": {
    "submission_to_screening": 0.708,
    "screening_to_interview": 0.353,
    "interview_to_hired": 0.167,
    "overall": 0.042
  },
  "totals": {
    "total": 200,
    "active": 150,
    "rejected": 45,
    "hired": 5,
    "new_in_period": 200,
    "avg_score": 65.3
  },
  "period": {
    "start_date": "2024-05-01",
    "end_date": "2024-06-01"
  }
}
```

---

### 4.2 GET /applies/aging — Candidaturas Paradas

Retorna applies que estão parados em uma etapa há mais tempo do que o esperado.

**URL:** `GET /v1/users/applies/aging`

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `days` | integer | Não | Dias mínimos parado (default: 3) |
| `status` | string | Não | Filtrar por status do processo seletivo |
| `job_id` | integer | Não | Filtrar por vaga específica |
| `page` | integer | Não | Página (default: 1) |
| `per_page` | integer | Não | Itens por página (default: 30, max: 30) |

#### Limiares de severidade

| Severidade | Dias na etapa |
|---|---|
| `attention` | 2–2 dias |
| `warning` | 3–4 dias |
| `critical` | 5+ dias |

#### Response (200 OK) — JSON:API

```json
{
  "data": [
    {
      "id": "123",
      "type": "aging_apply",
      "attributes": {
        "apply_id": 123,
        "candidate_name": "João Silva",
        "candidate_email": "joao@email.com",
        "job_id": 789,
        "job_title": "Desenvolvedor Full Stack",
        "current_stage": "Triagem",
        "current_stage_status": "screening",
        "days_in_stage": 7,
        "last_activity_at": "2024-05-25T14:30:00.000Z",
        "severity": "critical",
        "cv_match": 78.5,
        "total_score": 72.3
      }
    }
  ],
  "meta": {
    "total": 45,
    "page": 1,
    "per_page": 30,
    "by_severity": {
      "critical": 15,
      "warning": 18,
      "attention": 12
    },
    "by_stage": {
      "screening": 20,
      "interview": 15,
      "web_submission": 10
    }
  }
}
```

---

## 5. Kanban (Job Applies)

### 5.1 GET /jobs/:job_id/kanban — Kanban do Job

Retorna a visão Kanban com as colunas (etapas do processo seletivo) e os applies em cada coluna.

**URL:** `GET /v1/users/jobs/:job_id/kanban`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `job_id` | integer | Sim | ID da vaga |

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `term` | string | Não | Busca full-text nos applies (default: `"*"`) |
| `page` | integer | Não | Página dos applies dentro de cada coluna (default: 1) |
| `selective_process_id` | integer | Não | Filtrar por uma coluna específica |
| `where` | JSON string/object | Não | Filtros adicionais aplicados aos applies |

#### Response (200 OK) — JSON puro

```json
{
  "data": {
    "job_id": 789,
    "job_title": "Desenvolvedor Full Stack Senior",
    "columns": [
      {
        "selective_process_id": 10,
        "selective_process_title": "Triagem",
        "approved_process_id": 11,
        "rejected_process_id": 99,
        "action_behavior": "move",
        "sub_status_options": ["aguardando_retorno", "em_analise"],
        "sourcing_applies_count": 5,
        "web_response_applies_count": 12,
        "applies": {
          "records": [
            {
              "id": 123,
              "candidate_id": 456,
              "job_id": 789,
              "selective_process_id": 10,
              "selective_process_status": "screening",
              "cv_match": 85.2,
              "total_score": 78.5,
              "is_deleted": false,
              "created_at": "2024-06-01T10:00:00.000Z",
              "updated_at": "2024-06-05T14:30:00.000Z",
              "pin_user_ids": [1, 2],
              "confidential_user_ids": [],
              "alerts": [],
              "sub_status": null,
              "is_screening_sent": false,
              "source": "web_response",
              "evaluation_candidate_status": "pending",
              "evaluation_candidate_summaries": {
                "teste_tecnico_1": "Demonstrou domínio em..."
              }
            }
          ],
          "total_count": 17
        }
      },
      {
        "selective_process_id": 11,
        "selective_process_title": "Entrevista Técnica",
        "approved_process_id": 12,
        "rejected_process_id": 99,
        "action_behavior": "move",
        "sub_status_options": [],
        "sourcing_applies_count": 2,
        "web_response_applies_count": 8,
        "applies": {
          "records": [],
          "total_count": 10
        }
      }
    ]
  }
}
```

> **Nota:** Cada coluna retorna no máximo 10 applies por página (`PER_PAGE_KANBAN = 10`). Use o parâmetro `page` para paginação.

---

## 6. Job Applies Actions

### 6.1 POST /jobs/:id/applies/approve_collection — Aprovar em lote

Aprova múltiplas candidaturas de forma assíncrona, movendo para a próxima etapa.

**URL:** `POST /v1/users/jobs/:id/applies/approve_collection`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da vaga |

#### Request Body

```json
{
  "select_all_params": {
    "term": "*",
    "where": {
      "job_id": 789,
      "selective_process_id": 10,
      "is_deleted": false
    }
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `select_all_params` | object | Sim | Parâmetros de busca para selecionar applies a aprovar |

#### Response (200 OK)

```json
{
  "data": {
    "status": "processing",
    "message": "As candidaturas estão sendo aprovadas em background",
    "job_id": 789
  }
}
```

#### Response (400 Bad Request)

```json
{
  "error": "select_all_params é obrigatório"
}
```

---

### 6.2 POST /jobs/:id/applies/reject_collection — Rejeitar em lote

Rejeita múltiplas candidaturas de forma assíncrona.

**URL:** `POST /v1/users/jobs/:id/applies/reject_collection`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da vaga |

#### Request Body

```json
{
  "select_all_params": {
    "term": "*",
    "where": {
      "job_id": 789,
      "selective_process_id": 10,
      "is_deleted": false
    }
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `select_all_params` | object | Sim | Parâmetros de busca para selecionar applies a rejeitar |

#### Response (200 OK)

```json
{
  "data": {
    "status": "processing",
    "message": "As candidaturas estão sendo rejeitadas em background",
    "job_id": 789
  }
}
```

---

### 6.3 POST /jobs/:id/applies/send_reject_feedback — Enviar feedback de rejeição

Envia feedback de rejeição para candidatos. Dois modos: **geração automática via IA** ou **template manual**.

**URL:** `POST /v1/users/jobs/:id/applies/send_reject_feedback`

#### Path Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da vaga |

---

#### Modo 1: Geração automática via IA (`generate=true`)

```json
{
  "generate": true,
  "reference_ids": [123, 456, 789]
}
```

**Ou via select_all_params:**

```json
{
  "generate": true,
  "select_all_params": {
    "term": "*",
    "where": { "job_id": 789, "selective_process_status": "rejected" }
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `generate` | boolean | Sim | `true` para geração via IA |
| `reference_ids` | array[integer] | Condicional* | IDs dos applies (max 50) |
| `select_all_params` | object | Condicional* | Parâmetros de busca |

> *Obrigatório informar `reference_ids` ou `select_all_params`.

---

#### Modo 2: Template manual (`generate=false`)

```json
{
  "generate": false,
  "reference_ids": [123, 456],
  "subject": "Sobre sua candidatura para Desenvolvedor Full Stack",
  "description": "<p>Agradecemos pelo seu interesse...</p>",
  "name": "Feedback Rejeição Padrão"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `generate` | boolean | Sim | `false` para template manual |
| `reference_ids` | array[integer] | Sim | IDs dos applies (max 50) |
| `subject` | string | Sim | Assunto do e-mail de feedback |
| `description` | string | Sim | Corpo do e-mail (aceita HTML) |
| `name` | string | Não | Nome do template (default: `"Feedback de rejeição"`) |

#### Response (200 OK)

```json
{
  "data": {
    "status": "processing",
    "message": "Os feedbacks estão sendo gerados em background",
    "job_id": 789
  }
}
```

#### Response (400 Bad Request)

```json
{
  "error": "reference_ids ou select_all_params é obrigatório"
}
```

```json
{
  "error": "Limite máximo de 50 candidatos por vez"
}
```

```json
{
  "error": "subject é obrigatório quando generate é false"
}
```

---

## 7. Apply Statuses CRUD

Gerencia o histórico de mudanças de status de um apply (log de movimentação entre etapas).

### 7.1 GET /apply_statuses — Listar

**URL:** `GET /v1/users/apply_statuses`

#### Query Parameters

Mesmos parâmetros de busca padrão do sistema Searchkick.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `term` / `search` | string | Não | Busca full-text |
| `page` | integer | Não | Página (default: 1) |
| `per_page` | integer | Não | Itens por página (default: 30, max: 30) |
| `where` | JSON string/object | Não | Filtros (`apply_id`, `selective_process_id`, `user_id`, `is_deleted`) |
| `order` | JSON string/object | Não | Ordenação |

#### Response (200 OK) — JSON:API

```json
{
  "data": [
    {
      "id": "1",
      "type": "apply_status",
      "attributes": {
        "id": 1,
        "apply_id": 123,
        "selective_process_id": 10,
        "is_deleted": false,
        "account_id": 1,
        "user_id": 5,
        "status_name": "Triagem",
        "selective_process_name": "Triagem",
        "user_name": "Maria Recrutadora",
        "created_at": "2024-06-01T10:00:00.000Z",
        "updated_at": "2024-06-01T10:00:00.000Z"
      }
    }
  ],
  "meta": {
    "total": 15
  }
}
```

---

### 7.2 GET /apply_statuses/:id — Detalhe

**URL:** `GET /v1/users/apply_statuses/:id`

#### Response (200 OK) — JSON:API

Mesma estrutura de um item da listagem.

---

### 7.3 POST /apply_statuses — Criar

**URL:** `POST /v1/users/apply_statuses`

#### Request Body

```json
{
  "apply_status": {
    "apply_id": 123,
    "selective_process_id": 15,
    "status_name": "Entrevista Técnica",
    "user_id": 5,
    "account_id": 1
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `apply_id` | integer | Sim | ID do apply |
| `selective_process_id` | integer | Sim | ID do processo seletivo |
| `status_name` | string | Sim | Nome do status/etapa |
| `user_id` | integer | Não | ID do usuário que fez a ação |
| `account_id` | integer | Não | ID da conta |
| `is_deleted` | boolean | Não | Flag de soft-delete |

#### Response (201 Created) — JSON:API

```json
{
  "data": {
    "id": "50",
    "type": "apply_status",
    "attributes": {
      "id": 50,
      "apply_id": 123,
      "selective_process_id": 15,
      "is_deleted": false,
      "account_id": 1,
      "user_id": 5,
      "status_name": "Entrevista Técnica",
      "selective_process_name": "Entrevista Técnica",
      "user_name": "Maria Recrutadora",
      "created_at": "2024-06-05T10:00:00.000Z",
      "updated_at": "2024-06-05T10:00:00.000Z"
    }
  }
}
```

---

### 7.4 PUT /apply_statuses/:id — Atualizar

**URL:** `PUT /v1/users/apply_statuses/:id`

#### Request Body

```json
{
  "apply_status": {
    "status_name": "Novo nome da etapa",
    "selective_process_id": 20
  }
}
```

Campos permitidos: mesmos do create.

#### Response (200 OK) — JSON:API

Mesma estrutura do detalhe.

---

### 7.5 DELETE /apply_statuses/:id — Deletar (soft-delete)

**URL:** `DELETE /v1/users/apply_statuses/:id`

Marca como `is_deleted: true`.

#### Response (200 OK) — JSON:API

Retorna o apply_status com `is_deleted: true`.

---

## Enums e Constantes

### evaluation_candidate_status

| Valor | Código | Label |
|---|---|---|
| `pending` | 0 | Não enviado |
| `sent` | 1 | Enviado |
| `answered` | 2 | Respondido |

### Agregações disponíveis (index)

A busca no index de applies suporta as seguintes agregações:

| Agregação | Campo |
|---|---|
| `selective_process_status` | `selective_process_status` (limite: 10) |
| `candidate_feedback` | `candidate_feedback` (limite: 3) |

---

## Notas Gerais

- **Soft-delete:** Applies nunca são removidos fisicamente. O campo `is_deleted` é marcado como `true`.
- **Filtro automático:** O `is_deleted: false` é aplicado automaticamente no index quando não informado.
- **Pin/Confidential:** Arrays de `user_ids` no apply. O campo `pin` e `confidential` na resposta são calculados para o usuário autenticado.
- **cv_match:** Score de match entre CV do candidato e a vaga (0-100), calculado via embeddings pgvector.
- **total_score:** Média ponderada de `cv_match` + scores de avaliações.
- **Campos delegados do candidato:** A maioria dos campos pessoais (nome, email, telefone, endereço, etc.) vem do model `Candidate` vinculado ao apply.
- **Operações em lote:** São sempre assíncronas (Sidekiq jobs). A resposta é imediata com status `"processing"`.
- **Cache:** O endpoint `/stats` tem cache de 10 minutos por combinação de parâmetros.
- **ATS Sync:** Ao criar/atualizar/deletar um apply, uma sincronização com ATS externo pode ser disparada automaticamente.
