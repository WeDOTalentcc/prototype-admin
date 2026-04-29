# Insights Agent — API Endpoints

Endpoints REST consumidos pelos agentes Python de IA. Todos requerem autenticação via JWT Bearer token no header `Authorization`.

**Base URL:** `/v1/users`

---

## 1. GET /v1/users/applies/stats

Métricas agregadas de candidaturas para o agente de insights.

### Parâmetros de Entrada (Query String)

| Param | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `start_date` | `string` (YYYY-MM-DD) | Não | 30 dias atrás | Início do período |
| `end_date` | `string` (YYYY-MM-DD) | Não | Data atual | Fim do período |
| `job_id` | `integer` | Não | — | Filtrar por vaga específica |
| `user_id` | `integer` | Não | — | Filtrar por recrutador responsável |

### Exemplo de Requisição

```
GET /v1/users/applies/stats?start_date=2026-02-01&end_date=2026-03-01&job_id=42
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "by_status": {
    "web_submission": 120,
    "screening": 45,
    "interview": 18,
    "hired": 3,
    "rejected": 54
  },
  "by_source": [
    { "source": "portal", "count": 80, "percentage": 66.7 },
    { "source": "linkedin", "count": 30, "percentage": 25.0 },
    { "source": "referral", "count": 10, "percentage": 8.3 }
  ],
  "by_period": [
    { "date": "2026-02-01", "count": 5 },
    { "date": "2026-02-02", "count": 8 }
  ],
  "conversion_rates": {
    "submission_to_screening": 0.375,
    "screening_to_interview": 0.4,
    "interview_to_hired": 0.167,
    "overall": 0.025
  },
  "totals": {
    "total": 120,
    "active": 63,
    "rejected": 54,
    "hired": 3,
    "new_in_period": 120,
    "avg_score": 72.5
  },
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-03-01"
  }
}
```

**Cache:** 10 minutos. Chave: `applies_stats:{account_id}:{job_id}:{user_id}:{start_date}:{end_date}`

---

## 2. GET /v1/users/applies/aging

Candidaturas paradas sem movimentação há X dias. Retorna formato **JSON:API**.

### Parâmetros de Entrada (Query String)

| Param | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `days` | `integer` | Não | `3` | Dias mínimos sem atividade |
| `status` | `string` | Não | — | Filtrar por status do estágio (ex: `screening`) |
| `job_id` | `integer` | Não | — | Filtrar por vaga |
| `page` | `integer` | Não | `1` | Página |
| `per_page` | `integer` | Não | `20` | Itens por página (máx 30) |

### Exemplo de Requisição

```
GET /v1/users/applies/aging?days=5&job_id=42&page=1&per_page=10
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "data": [
    {
      "id": "101",
      "type": "aging_apply",
      "attributes": {
        "candidate_name": "Maria Silva",
        "candidate_email": "maria@email.com",
        "job_title": "Desenvolvedor Backend",
        "stage_name": "Triagem",
        "stage_status": 1,
        "days_in_stage": 7,
        "cv_match": 85.5,
        "total_score": 72.0,
        "last_activity_at": "2026-02-28T14:30:00Z",
        "recruiter_id": 5,
        "severity": "critical"
      }
    }
  ],
  "meta": {
    "total": 35,
    "page": 1,
    "per_page": 10,
    "severity_counts": {
      "critical": 10,
      "warning": 15,
      "attention": 10
    },
    "by_stage": {
      "screening": 20,
      "interview": 15
    }
  }
}
```

### Thresholds de Severidade

| Severidade | Dias sem atividade |
|---|---|
| `critical` | >= 5 dias |
| `warning` | 3–4 dias |
| `attention` | 2 dias |

Exclui automaticamente candidaturas com status `rejected` ou `hired`.

---

## 3. GET /v1/users/applies/:id/timeline

Histórico completo de uma candidatura: mudanças de etapa, avaliações, entrevistas, disparos.

### Parâmetros de Entrada (Path)

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `integer` | Sim | ID da candidatura (Apply) |

### Exemplo de Requisição

```
GET /v1/users/applies/101/timeline
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "apply_id": 101,
  "candidate_name": "Maria Silva",
  "job_title": "Desenvolvedor Backend",
  "current_stage": "Entrevista Técnica",
  "created_at": "2026-01-15T10:30:00Z",
  "timeline": [
    {
      "timestamp": "2026-01-15T10:30:00Z",
      "type": "apply_created",
      "description": "Candidatura recebida via portal",
      "actor": "system"
    },
    {
      "timestamp": "2026-01-16T09:00:00Z",
      "type": "stage_change",
      "to": "Triagem",
      "stage_status": 1,
      "actor": "João Recrutador"
    },
    {
      "timestamp": "2026-01-18T14:00:00Z",
      "type": "evaluation_sent",
      "evaluation": "Fit Cultural",
      "actor": "João Recrutador"
    },
    {
      "timestamp": "2026-01-20T11:30:00Z",
      "type": "evaluation_completed",
      "evaluation": "Fit Cultural",
      "score": 85.0,
      "classification": "A"
    },
    {
      "timestamp": "2026-01-22T15:00:00Z",
      "type": "interview_scheduled",
      "title": "Entrevista Técnica",
      "provider": "google_meet",
      "sub_status": "scheduled",
      "interviewer": "Ana Tech Lead"
    },
    {
      "timestamp": "2026-01-25T10:00:00Z",
      "type": "dispatch_sent",
      "channel": "email",
      "subject": "Próximas etapas",
      "status": "delivered"
    }
  ],
  "summary": {
    "days_in_pipeline": 52,
    "stages_visited": 3,
    "evaluations_completed": 1,
    "interviews_scheduled": 1
  }
}
```

### Tipos de Eventos no Timeline

| type | Descrição |
|---|---|
| `apply_created` | Candidatura criada |
| `stage_change` | Mudança de etapa no pipeline |
| `evaluation_sent` | Avaliação enviada ao candidato |
| `evaluation_completed` | Avaliação respondida/completada |
| `interview_scheduled` | Entrevista agendada |
| `dispatch_sent` | Email/WhatsApp enviado |

---

## 4. GET /v1/users/meetings/stats

Métricas de reuniões/entrevistas.

### Parâmetros de Entrada (Query String)

| Param | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `start_date` | `string` (YYYY-MM-DD) | Não | 30 dias atrás | Início do período |
| `end_date` | `string` (YYYY-MM-DD) | Não | Data atual | Fim do período |
| `job_id` | `integer` | Não | — | Filtrar por vaga |
| `organizer_id` | `integer` | Não | — | Filtrar por organizador |

### Exemplo de Requisição

```
GET /v1/users/meetings/stats?start_date=2026-02-01&end_date=2026-03-01
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "totals": {
    "total": 45,
    "completed": 30,
    "scheduled": 8,
    "cancelled": 3,
    "no_show": 4
  },
  "by_sub_status": {
    "completed": 30,
    "scheduled": 8,
    "no_show": 4,
    "rescheduled": 3
  },
  "by_provider": {
    "google_meet": 25,
    "teams": 15,
    "in_person": 5
  },
  "by_period": [
    {
      "week": "2026-02-03",
      "total": 12,
      "completed": 8,
      "no_show": 1,
      "cancelled": 0
    },
    {
      "week": "2026-02-10",
      "total": 10,
      "completed": 7,
      "no_show": 2,
      "cancelled": 0
    }
  ],
  "no_show_rate": 0.089,
  "cancellation_rate": 0.063,
  "avg_per_week": 11.25,
  "upcoming_24h": 3,
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-03-01"
  }
}
```

**Cache:** 15 minutos.

---

## 5. GET /v1/users/dashboard/briefing

Endpoint unificado para briefing diário. Retorna tudo que o agente precisa em uma única chamada.

### Parâmetros de Entrada (Query String)

| Param | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `since` | `integer` | Não | `24` | Horas para lookback |
| `timezone` | `string` | Não | `America/Sao_Paulo` | Timezone para agenda do dia |

### Exemplo de Requisição

```
GET /v1/users/dashboard/briefing?since=48&timezone=America/Sao_Paulo
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "generated_at": "2026-03-08T10:30:00-03:00",
  "user_name": "João Recrutador",
  "summary": {
    "new_applies": 15,
    "pipeline_movements": 28,
    "interviews_today": 3,
    "evaluations_completed": 5,
    "pending_alerts": 2,
    "active_jobs": 12
  },
  "alerts": {
    "summary": { "total_alerts": 2, "critical": 1, "warning": 1 },
    "alerts": []
  },
  "new_applies": [
    {
      "apply_id": 201,
      "candidate_name": "Ana Costa",
      "job_title": "Frontend Developer",
      "cv_match": 92.5,
      "source": "linkedin",
      "created_at": "2026-03-07T16:30:00Z"
    }
  ],
  "todays_agenda": [
    {
      "time": "09:00",
      "end_time": "09:45",
      "candidate_name": "Carlos Souza",
      "job_title": "Backend Developer",
      "type": "interview",
      "provider": "google_meet",
      "sub_status": "scheduled"
    }
  ],
  "completed_evaluations": [
    {
      "candidate_name": "Maria Silva",
      "evaluation_name": "Fit Cultural WSI",
      "job_title": "UX Designer",
      "score": 88.0,
      "wsi_classification": "A",
      "wsi_summary": "Forte alinhamento cultural...",
      "completed_at": "2026-03-07T20:15:00Z"
    }
  ],
  "aging_applies": [
    {
      "candidate_name": "Pedro Lima",
      "job_title": "DevOps Engineer",
      "current_stage": "Triagem",
      "days_in_stage": 6,
      "severity": "critical"
    }
  ],
  "recent_movements": [
    {
      "candidate_name": "Julia Santos",
      "job_title": "Product Manager",
      "to_stage": "Entrevista Final",
      "moved_by": "Ana Recrutadora",
      "moved_at": "2026-03-07T18:00:00Z"
    }
  ],
  "no_shows": [
    {
      "candidate_name": "Rafael Oliveira",
      "job_title": "Data Analyst",
      "scheduled_at": "2026-03-07T14:00:00Z"
    }
  ]
}
```

**Cache:** 5 minutos. Máximo 10 itens por seção.

---

## 6. GET /v1/users/candidates/stats

Métricas agregadas de candidatos.

### Parâmetros de Entrada (Query String)

| Param | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `start_date` | `string` (YYYY-MM-DD) | Não | 30 dias atrás | Início do período |
| `end_date` | `string` (YYYY-MM-DD) | Não | Data atual | Fim do período |
| `source` | `string` | Não | — | Filtrar por fonte (ex: `portal`, `linkedin`) |

### Exemplo de Requisição

```
GET /v1/users/candidates/stats?start_date=2026-02-01&source=linkedin
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "totals": {
    "total": 1500,
    "new_in_period": 120,
    "with_applies": 950,
    "without_applies": 550
  },
  "by_source": [
    { "source": "portal", "count": 600, "percentage": 40.0 },
    { "source": "linkedin", "count": 450, "percentage": 30.0 },
    { "source": "referral", "count": 250, "percentage": 16.7 },
    { "source": "unknown", "count": 200, "percentage": 13.3 }
  ],
  "new_per_day": [
    { "date": "2026-02-01", "count": 4 },
    { "date": "2026-02-02", "count": 6 }
  ],
  "by_location": [
    { "city": "São Paulo", "state": "SP", "count": 350 },
    { "city": "Rio de Janeiro", "state": "RJ", "count": 180 }
  ],
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-03-08"
  }
}
```

**Cache:** 30 minutos.

---

## 7. GET /v1/users/candidates/:id/communications

Timeline de comunicações com um candidato específico.

### Parâmetros de Entrada (Path)

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `integer` | Sim | ID do candidato |

### Exemplo de Requisição

```
GET /v1/users/candidates/55/communications
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "candidate_id": 55,
  "candidate_name": "Maria Silva",
  "communications": [
    {
      "type": "dispatch",
      "channel": "email",
      "subject": "Convite para entrevista",
      "status": "delivered",
      "direction": "outbound",
      "sent_at": "2026-03-05T10:00:00Z",
      "opened_at": "2026-03-05T10:15:00Z",
      "date": "2026-03-05T10:00:00Z"
    },
    {
      "type": "evaluation_sent",
      "evaluation_name": "Fit Cultural WSI",
      "status": "completed",
      "direction": "outbound",
      "sent_at": "2026-03-01T14:00:00Z",
      "completed_at": "2026-03-02T09:30:00Z",
      "date": "2026-03-01T14:00:00Z"
    },
    {
      "type": "interview",
      "title": "Entrevista Técnica",
      "provider": "google_meet",
      "status": "completed",
      "scheduled_at": "2026-02-28T15:00:00Z",
      "date": "2026-02-28T15:00:00Z"
    },
    {
      "type": "pipeline_change",
      "to_stage": "Entrevista Final",
      "changed_by": "João Recrutador",
      "changed_at": "2026-02-27T11:00:00Z",
      "date": "2026-02-27T11:00:00Z"
    }
  ],
  "summary": {
    "total_communications": 4,
    "last_outbound_at": "2026-03-05T10:00:00Z",
    "last_inbound_at": "2026-03-02T09:30:00Z",
    "days_since_last_contact": 3
  }
}
```

### Tipos de Comunicação

| type | direction | Descrição |
|---|---|---|
| `dispatch` | `outbound` | Email ou WhatsApp enviado |
| `evaluation_sent` | `outbound` | Avaliação enviada |
| `interview` | — | Entrevista agendada/realizada |
| `pipeline_change` | — | Mudança de etapa no pipeline |

---

## 8. GET /v1/users/dispatches

Lista de disparos (emails/WhatsApp) com filtros. Retorna formato **JSON:API**.

### Parâmetros de Entrada (Query String)

| Param | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `channel_type` | `string` | Não | — | `email` ou `whatsapp` |
| `status` | `string` | Não | — | `pending`, `sent`, `failed`, etc. |
| `candidate_id` | `integer` | Não | — | Filtrar por candidato destinatário |
| `job_id` | `integer` | Não | — | Filtrar por vaga referência |
| `page` | `integer` | Não | `1` | Página |
| `per_page` | `integer` | Não | `30` | Itens por página (máx 30) |

### Exemplo de Requisição

```
GET /v1/users/dispatches?channel_type=email&candidate_id=55&page=1&per_page=10
Authorization: Bearer <token>
```

### Resposta (200 OK)

```json
{
  "data": [
    {
      "id": "301",
      "type": "dispatch",
      "attributes": {
        "channel_type": "email",
        "status": "sent",
        "name": "Convite para entrevista",
        "subject": "Convite para entrevista técnica",
        "scheduled_for": null,
        "created_at": "2026-03-05T10:00:00Z",
        "recipient_count": 5,
        "opened_count": 3,
        "delivered_count": 5,
        "failed_count": 0,
        "recipients": [
          {
            "id": 55,
            "name": "Maria Silva",
            "email": "maria@email.com",
            "status": "delivered",
            "sent_at": "2026-03-05T10:01:00Z",
            "opened_at": "2026-03-05T10:15:00Z"
          }
        ]
      }
    }
  ],
  "meta": {
    "total": 25,
    "page": 1,
    "per_page": 10
  }
}
```

---

## 9. GET /v1/users/dispatches/:id

Detalhes de um disparo específico.

### Parâmetros de Entrada (Path)

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `integer` | Sim | ID do dispatch |

### Resposta (200 OK)

Mesmo formato de um item individual do array `data` do endpoint de listagem (JSON:API).

---

## 10. POST /v1/users/email_templates/render_for_candidate

Renderiza um template substituindo variáveis com dados reais de candidato/vaga.

### Parâmetros de Entrada (Body JSON)

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `template_id` | `integer` | Sim | ID do template |
| `candidate_id` | `integer` | Sim | ID do candidato |
| `job_id` | `integer` | Não | ID da vaga (para resolver tags de vaga) |
| `apply_id` | `integer` | Não | ID da candidatura |
| `extra_variables` | `object` | Não | Variáveis extras `{ "chave": "valor" }` |

### Exemplo de Requisição

```
POST /v1/users/email_templates/render_for_candidate
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": 10,
  "candidate_id": 55,
  "job_id": 42,
  "extra_variables": {
    "data_entrevista": "10/03/2026",
    "horario": "14:00"
  }
}
```

### Resposta (200 OK)

```json
{
  "subject": "Convite para entrevista - Desenvolvedor Backend",
  "body": "<p>Olá Maria Silva, você foi convidada para uma entrevista para a vaga Desenvolvedor Backend no dia 10/03/2026 às 14:00.</p>",
  "body_text": "Olá Maria Silva, você foi convidada para uma entrevista para a vaga Desenvolvedor Backend no dia 10/03/2026 às 14:00.",
  "variables_used": ["candidato_nome", "vaga", "data_entrevista", "horario"],
  "variables_missing": []
}
```

### Respostas de Erro

| Status | Caso |
|---|---|
| `404` | `template_id`, `candidate_id` ou `job_id` não encontrado |
| `401` | Token JWT ausente ou inválido |

Se houver variáveis não resolvidas, elas aparecem no campo `variables_missing` como `["{{variavel_x}}"]`.

---

## Autenticação

Todos os endpoints requerem header:

```
Authorization: Bearer <jwt_token>
```

Respostas de erro de autenticação:

```json
// 401 Unauthorized
{ "error": "Unauthorized" }
```

---

## Indexação (Performance)

Migration de índices criada para otimizar consultas:

| Índice | Tabela | Colunas |
|---|---|---|
| `idx_applies_created_at_not_deleted` | `applies` | `created_at WHERE is_deleted = false` |
| `idx_apply_statuses_apply_id_created_at` | `apply_statuses` | `apply_id, created_at` |
| `idx_apply_statuses_created_at_desc` | `apply_statuses` | `created_at DESC` |
| `idx_calendar_events_start_time_type_active` | `calendar_events` | `start_time, event_type WHERE is_deleted = false AND is_cancelled = false` |
| `idx_dispatch_messages_recipient` | `dispatch_messages` | `recipient_type, recipient_id` |
| `idx_evaluation_candidates_candidate_job` | `evaluation_candidates` | `candidate_id, job_id` |
| `idx_meetings_start_time_not_deleted` | `meetings` | `start_time WHERE is_deleted = false` |
