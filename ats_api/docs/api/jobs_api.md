# API de Jobs - Documentação Completa

## Table of Contents

1. [Autenticação](#autenticação)
2. [Jobs (CRUD)](#1-jobs-crud)
3. [Operações em Lote](#2-operações-em-lote)
4. [Cópia de Jobs](#3-cópia-de-jobs)
5. [Enums e Referências](#4-enums-e-referências)
6. [Kanban](#5-kanban)
7. [Candidaturas (Applies) no Job](#6-candidaturas-applies-no-job)
8. [Sugestões com IA](#7-sugestões-com-ia)
9. [Estrutura Organizacional](#8-estrutura-organizacional)
10. [Match de Candidatos](#9-match-de-candidatos)
11. [Busca Booleana e Dados para Descrição](#10-busca-booleana-e-dados-para-descrição)
12. [Job Statuses](#11-job-statuses)
13. [Job Journeys](#12-job-journeys)
14. [Job Users (Equipe da Vaga)](#13-job-users-equipe-da-vaga)
15. [Job Field Templates](#14-job-field-templates)
16. [Opinião: Endpoints Faltantes](#opinião-endpoints-faltantes)

---

## Autenticação

Todas as requisições requerem autenticação via token Bearer:

```
Authorization: Bearer <jwt_token>
```

---

## 1. Jobs (CRUD)

Base URL: `/v1/users/jobs`

### 1.1 Listar Jobs

```
GET /v1/users/jobs
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | - | Termo de busca full-text |
| `page` | integer | 1 | Número da página |
| `per_page` | integer | 30 | Itens por página |
| `compact` | string | - | Campos a retornar (CSV). Ex: `id,title,city` |
| `pin` | boolean | - | Filtrar jobs fixados pelo usuário |
| `confidential` | boolean | - | Filtrar jobs confidenciais |
| `where[is_deleted]` | boolean | `false` | Filtrar deletados |
| `where[is_active]` | boolean | - | Filtrar por status ativo/inativo |
| `where[is_archived]` | boolean | - | Filtrar arquivados |
| `where[job_status_id]` | integer | - | Filtrar por status da vaga |
| `where[company_id]` | integer | - | Filtrar por empresa |
| `where[user_id]` | integer | - | Filtrar por recrutador |
| `where[priority]` | integer | - | Filtrar por prioridade |
| `where[urgency_level]` | integer | - | Filtrar por urgência |
| `where[seniority]` | integer | - | Filtrar por senioridade |
| `where[workplace_type]` | integer | - | Filtrar por regime de trabalho |
| `where[department_id]` | integer | - | Filtrar por departamento |
| `where[hiring_manager_id]` | integer | - | Filtrar por hiring manager |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "1",
      "type": "job",
      "attributes": {
        "id": 1,
        "title": "Desenvolvedor Ruby Senior",
        "description": "<p>Descrição da vaga...</p>",
        "user_id": 10,
        "account_id": 1,
        "job_status_id": 1,
        "company_id": 5,
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "is_remote": false,
        "workplace_type": 2,
        "workplace_type_text": "Híbrido",
        "employment_type": 0,
        "employment_type_text": "CLT",
        "seniority": 2,
        "seniority_text": "Sênior",
        "salary_from": 12000.0,
        "salary_to": 18000.0,
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
        "applies_count": 42,
        "is_active": true,
        "is_archived": false,
        "is_urgent": false,
        "pin": false,
        "confidential": false,
        "priority": 1,
        "priority_text": "Alta",
        "urgency_level": 3,
        "urgency_level_text": "Média",
        "published_date": "2026-02-15T10:00:00.000Z",
        "application_deadline": "2026-03-15T23:59:59.000Z",
        "screening_deadline": "2026-03-01",
        "shortlist_deadline": "2026-03-10",
        "closing_deadline": "2026-03-20",
        "reason_for_pause": null,
        "confidential_type": 1,
        "confidential_type_text": "Pública",
        "confidential_company_name": null,
        "job_status": "Ativa",
        "job_status_color": "#4CAF50",
        "company": {
          "id": 5,
          "name": "TechCorp"
        },
        "user_name": "João Recrutador",
        "user_email": "joao@empresa.com",
        "user_whatsapp": "+5511999999999",
        "department_id": 3,
        "department_name": "Engenharia",
        "hiring_manager_id": 7,
        "hiring_manager_name": "Maria Gerente",
        "hiring_manager_email": "maria@empresa.com",
        "missing_fields": ["benefits_data", "behavioral_competencies"],
        "completeness_percentage": 85.0,
        "is_ready_for_publication": true,
        "organizational_structure": {
          "department_id": 3,
          "department": "Engenharia",
          "team_id": null,
          "team": null,
          "team_composition": {},
          "reports_to": null,
          "hiring_manager": "Maria Gerente",
          "team_size": 0
        },
        "selection_process_summary": {},
        "main_pcd_category": null,
        "main_pcd_category_text": "Não informado",
        "secondary_pcd_category": null,
        "secondary_pcd_category_text": "Não informado",
        "responsibilities": ["Desenvolver APIs REST", "Code review"],
        "url": "/user/jobs/1",
        "created_at": "2026-02-10T08:00:00.000Z",
        "updated_at": "2026-02-28T14:30:00.000Z"
      }
    }
  ],
  "meta": {
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_count": 142,
      "per_page": 30
    }
  }
}
```

---

### 1.2 Obter Job

```
GET /v1/users/jobs/:id
```

**Response:** `200 OK` — Retorna o mesmo formato de atributos da listagem, porém em objeto singular (`data` ao invés de array).

---

### 1.3 Criar Job

```
POST /v1/users/jobs
```

**Request Body:**
```json
{
  "job": {
    "title": "Desenvolvedor Ruby Senior",
    "description": "<p>Buscamos um desenvolvedor Ruby...</p>",
    "company_id": 5,
    "job_status_id": 1,
    "city": "São Paulo",
    "state": "SP",
    "is_remote": false,
    "workplace_type": 2,
    "employment_type": 0,
    "seniority": 2,
    "priority": 1,
    "urgency_level": 3,
    "published_date": "2026-03-01T10:00:00.000Z",
    "application_deadline": "2026-04-01T23:59:59.000Z",
    "screening_deadline": "2026-03-15",
    "shortlist_deadline": "2026-03-25",
    "closing_deadline": "2026-04-01",
    "hiring_manager_id": 7,
    "department_id": 3,
    "confidential_type": 1,
    "salary_from": 12000,
    "salary_to": 18000,
    "salary_currency": "BRL",
    "salary_period": "monthly",
    "salary_contract_type": "CLT",
    "commission_from": null,
    "commission_to": null,
    "bonus_from": null,
    "bonus_to": null,
    "responsibilities": ["Desenvolver APIs REST", "Code review", "Mentoria"],
    "is_screening_active": true,
    "minimum_screening_score": 7.0,
    "screening_timeout": 48,
    "screening_max_attempts": 3,
    "screening_approve_limit": 10,
    "has_automatic_interview": false,
    "use_whatsapp_channel": true,
    "use_webchat_channel": false,
    "use_call_channel": false,
    "has_linkedin_post": true,
    "has_website_post": true,
    "has_indeed_post": false,
    "benefits": [1, 2, 3],
    "skills": [
      {"id": 1, "level": "advanced"},
      {"id": 2, "level": "intermediate"}
    ],
    "selective_processes_attributes": [
      {
        "name": "Funil",
        "status": "web_submission",
        "position": 0,
        "color": "#a8ced5",
        "external_id": "sp-funil-001"
      },
      {
        "name": "Triagem",
        "status": "screening",
        "position": 1,
        "color": "#d5bfa8",
        "external_id": "sp-triagem-001"
      }
    ]
  }
}
```

**Campos Permitidos:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `title` | string | sim* | Título da vaga |
| `description` | text | sim* | Descrição (HTML) |
| `company_id` | integer | não | Empresa associada |
| `job_status_id` | integer | não | Status da vaga |
| `city` | string | não | Cidade |
| `state` | string | não | Estado |
| `is_remote` | boolean | não | Trabalho remoto |
| `workplace_type` | integer | não | 1=Remoto, 2=Híbrido, 3=Presencial |
| `employment_type` | integer | não | 0=CLT, 1=PJ, 2=Estágio, 3=Temporário, 4=Freelancer, 5=Aprendiz |
| `seniority` | integer | não | 0=Júnior, 1=Pleno, 2=Sênior, 3=Especialista, 4=Estágio, 5=Lead, 6=Gerente, 7=Diretor |
| `priority` | integer | não | 1=Alta, 2=Média, 3=Baixa |
| `urgency_level` | integer | não | 1=Baixa, 2=Moderada, 3=Média, 4=Alta, 5=Crítica |
| `published_date` | datetime | não | Data de publicação |
| `application_deadline` | datetime | não | Prazo para candidatura |
| `screening_deadline` | date | não | Prazo de triagem |
| `shortlist_deadline` | date | não | Prazo de shortlist |
| `closing_deadline` | date | não | Prazo de encerramento |
| `salary_from` | decimal | não | Salário mínimo |
| `salary_to` | decimal | não | Salário máximo |
| `salary_currency` | string | não | Moeda do salário (ex: BRL, USD) |
| `salary_period` | string | não | Período (monthly, yearly, etc) |
| `salary_contract_type` | string | não | Tipo de contrato |
| `commission_from` | decimal | não | Comissão mínima |
| `commission_to` | decimal | não | Comissão máxima |
| `commission_currency` | string | não | Moeda da comissão |
| `commission_period` | string | não | Período da comissão |
| `bonus_from` | decimal | não | Bônus mínimo |
| `bonus_to` | decimal | não | Bônus máximo |
| `bonus_currency` | string | não | Moeda do bônus |
| `bonus_period` | string | não | Período do bônus |
| `hiring_manager_id` | integer | não | ID do hiring manager |
| `department_id` | integer | não | ID do departamento |
| `department` | string | não | Nome do departamento (cria/sync automaticamente) |
| `confidential_type` | integer | não | 1=Pública, 2=Interna, 3=Confidencial |
| `confidential_company_name` | string | não | Nome da empresa (se confidencial) |
| `responsibilities` | array[string] | não | Lista de responsabilidades |
| `is_active` | boolean | não | Vaga ativa |
| `is_urgent` | boolean | não | Vaga urgente |
| `is_screening_active` | boolean | não | Screening ativo |
| `minimum_screening_score` | float | não | Score mínimo de screening |
| `screening_timeout` | integer | não | Timeout de screening (horas) |
| `screening_max_attempts` | integer | não | Máximo de tentativas |
| `screening_approve_limit` | integer | não | Limite de aprovações automáticas |
| `interview_minimum_score` | float | não | Score mínimo de entrevista |
| `has_automatic_interview` | boolean | não | Entrevista automática |
| `interview_calendar_type` | integer | não | Tipo de calendário |
| `interview_hours_range` | string | não | Faixa de horários |
| `interview_duration` | integer | não | Duração da entrevista (minutos) |
| `use_whatsapp_channel` | boolean | não | Canal WhatsApp |
| `use_webchat_channel` | boolean | não | Canal Webchat |
| `use_call_channel` | boolean | não | Canal Ligação |
| `has_linkedin_post` | boolean | não | Publicar no LinkedIn |
| `has_website_post` | boolean | não | Publicar no site |
| `has_indeed_post` | boolean | não | Publicar no Indeed |
| `friendly_badge` | boolean | não | Badge amigável |
| `disabilities` | boolean | não | Vaga para PCD |
| `main_pcd_category` | integer | não | Categoria PCD principal |
| `secondary_pcd_category` | integer | não | Categoria PCD secundária |
| `pcd_description` | string | não | Descrição PCD |
| `required_pcd_files` | boolean | não | Arquivos PCD obrigatórios |
| `pcd_files_description` | string | não | Descrição dos arquivos PCD |
| `sector` | string | não | Setor |
| `segment` | string | não | Segmento |
| `target_audience` | string | não | Público-alvo |
| `external_id` | string | não | ID externo (único por account) |
| `provider` | string | não | Provedor externo |
| `provider_job_id` | string | não | ID no provedor |
| `job_url` | string | não | URL externa da vaga |
| `pin` | boolean | não | Fixar para o usuário |
| `confidential` | boolean | não | Marcar como confidencial para o usuário |
| `benefits` | array | não | IDs de benefícios |
| `skills` | array[object] | não | Skills com nível |
| `languages` | array/null | não | Idiomas (null para limpar) |
| `selective_processes_attributes` | array[object] | não | Etapas do processo seletivo |

\* Pelo menos `title` ou `description` deve estar presente.

**Response:** `201 Created` — Retorna o job criado com `selective_processes` inclusos.

**Response (erro):** `422 Unprocessable Entity`
```json
{
  "errors": ["Title ou Description deve ser preenchido"]
}
```

---

### 1.4 Atualizar Job

```
PUT /v1/users/jobs/:id
```

Apenas o dono do job (`user_id == current_user.id`) pode atualizar.

**Request Body:** Mesmo formato do create, apenas com os campos a serem alterados.

**Response:** `200 OK`

**Response (sem permissão):** `403 Forbidden`
```json
{
  "error": "Não autorizado a realizar esta ação neste job"
}
```

---

### 1.5 Deletar Job

```
DELETE /v1/users/jobs/:id
```

Apenas o dono do job pode deletar. Realiza soft delete (`is_deleted: true`).

**Response:** `200 OK`

---

## 2. Operações em Lote

### 2.1 Arquivar Jobs

```
POST /v1/users/jobs/archive
```

**Request Body:**
```json
{
  "select_all_params": {
    "where": {
      "job_status_id": 9
    },
    "select_all": true
  },
  "is_archived": true
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "status": "processing",
    "message": "As vagas estão sendo arquivadas"
  }
}
```

### 2.2 Desarquivar Jobs

```
POST /v1/users/jobs/unarchive
```

**Request Body:**
```json
{
  "select_all_params": {
    "where": {
      "is_archived": true
    },
    "select_all": true
  }
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "status": "processing",
    "message": "As vagas estão sendo desarquivadas"
  }
}
```

### 2.3 Ativar Jobs

```
POST /v1/users/jobs/activate
```

**Request Body:**
```json
{
  "select_all_params": {
    "where": {
      "is_active": false
    },
    "select_all": true
  }
}
```

### 2.4 Pausar Jobs

```
POST /v1/users/jobs/pause
```

**Request Body:**
```json
{
  "select_all_params": {
    "where": {
      "is_active": true
    },
    "select_all": true
  },
  "reason": "Processo de contratação temporariamente suspenso"
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `select_all_params` | object | **Obrigatório**. Filtros de seleção |
| `select_all_params.where` | object | Filtros para selecionar os jobs |
| `select_all_params.select_all` | boolean | Selecionar todos que atendem ao filtro |
| `reason` ou `reason_for_pause` | string | Motivo da pausa (apenas para pause) |
| `is_archived` | boolean | Status de arquivamento (apenas para archive) |

---

## 3. Cópia de Jobs

### 3.1 Copiar Job (Único)

```
POST /v1/users/jobs/:id/copy
```

**Request Body:**
```json
{
  "job": {
    "user_id": 10,
    "entities": ["selective_processes", "skills", "benefits", "languages", "behavioral_skills"]
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job.user_id` | integer | current_user.id | Recrutador da cópia |
| `job.entities` | array[string] | `[]` | Entidades a copiar |

**Entidades disponíveis:** `selective_processes`, `skills`, `benefits`, `languages`, `behavioral_skills`, `remunerations`

**Response:** `200 OK` — Retorna o job copiado.

### 3.2 Copiar Job por Quantidade (Assíncrono)

```
POST /v1/users/jobs/:id/copy_job_by_amount
```

**Request Body:**
```json
{
  "amount": 5,
  "job": {
    "entities": ["selective_processes", "skills"]
  }
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `amount` | integer | **Obrigatório**. Quantidade de cópias (1-99) |
| `job.entities` | array[string] | Entidades a copiar |

**Response:** `200 OK`
```json
{
  "data": {
    "message": "Job duplication in progress",
    "amount": 5,
    "job_id": 1
  }
}
```

> Se `amount == 1` executa sincronamente; caso contrário executa em background.

---

## 4. Enums e Referências

### 4.1 Prioridades

```
GET /v1/users/jobs/priorities
```

**Response:** `200 OK`
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

### 4.2 Níveis de Urgência

```
GET /v1/users/jobs/urgency_levels
```

**Response:** `200 OK`
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

### 4.3 Tipos de Regime de Trabalho

```
GET /v1/users/jobs/workplace_types
```

**Valores:** Não informado (null), Remoto (1), Híbrido (2), Presencial (3)

### 4.4 Tipos de Contratação

```
GET /v1/users/jobs/employment_types
```

**Valores:** CLT (0), PJ (1), Estágio (2), Temporário (3), Freelancer (4), Aprendiz (5)

### 4.5 Senioridades

```
GET /v1/users/jobs/seniorities
```

**Valores:** Júnior (0), Pleno (1), Sênior (2), Especialista (3), Estágio (4), Lead (5), Gerente (6), Diretor (7)

### 4.6 Categorias PCD

```
GET /v1/users/jobs/pcd_categories
```

**Valores:** Não informado (null), Gênero (1), Raça/Etnia (2), PCD (3), LGBTQIA+ (4), 50+ (5), Refugiado (6), Indígena (7), Outro (8)

### 4.7 Tipos de Confidencialidade

```
GET /v1/users/jobs/confidential_types
```

**Valores:** Não informado (null), Pública (1), Interna (2), Confidencial (3)

---

## 5. Kanban

### 5.1 Obter Kanban do Job

```
GET /v1/users/jobs/:job_id/kanban
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `selective_process_id` | integer | Filtrar por etapa específica |
| `term` | string | Busca textual nos candidatos |
| `page` | integer | Paginação por coluna |
| `where[...]` | object | Filtros adicionais sobre applies |

**Response:** `200 OK`
```json
{
  "data": {
    "job_id": 1,
    "job_title": "Desenvolvedor Ruby Senior",
    "columns": [
      {
        "selective_process_id": 10,
        "selective_process_title": "Funil",
        "approved_process_id": null,
        "rejected_process_id": null,
        "action_behavior": null,
        "sub_status_options": [],
        "applies": [
          {
            "id": 100,
            "candidate_id": 50,
            "candidate_name": "Ana Silva",
            "selective_process_id": 10
          }
        ]
      },
      {
        "selective_process_id": 11,
        "selective_process_title": "Triagem",
        "applies": []
      }
    ]
  }
}
```

---

## 6. Candidaturas (Applies) no Job

### 6.1 Aprovar Candidaturas em Lote

```
POST /v1/users/jobs/:id/applies/approve_collection
```

**Request Body:**
```json
{
  "select_all_params": {
    "where": {
      "selective_process_id": 10
    },
    "select_all": true
  }
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "status": "processing",
    "message": "As candidaturas estão sendo aprovadas em background",
    "job_id": 1
  }
}
```

### 6.2 Rejeitar Candidaturas em Lote

```
POST /v1/users/jobs/:id/applies/reject_collection
```

**Request Body:** Mesmo formato do approve_collection, com campo opcional adicional:

| Parameter | Type | Description |
|-----------|------|-------------|
| `reason_for_reject` | string | **Opcional**. Motivo da rejeição aplicado a todas as candidaturas rejeitadas |

Exemplo com motivo:
```json
{
  "select_all_params": {
    "where": { "selective_process_id": 10 },
    "select_all": true,
    "reason_for_reject": "Perfil não compatível com a vaga"
  }
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "status": "processing",
    "message": "As candidaturas estão sendo rejeitadas em background",
    "job_id": 1
  }
}
```

### 6.3 Adicionar Candidatos de uma Lista

```
POST /v1/users/jobs/:id/add_candidates_from_list
```

**Request Body:**
```json
{
  "list_id": 15,
  "selective_process_id": 10
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `list_id` | integer | **Obrigatório**. ID da lista de candidatos |
| `selective_process_id` | integer | **Obrigatório**. Etapa de destino |

**Response:** `200 OK`
```json
{
  "data": {
    "message": "Processamento iniciado. Os candidatos da lista serão adicionados à vaga."
  }
}
```

---

## 7. Sugestões com IA

### 7.1 Gerar Sugestão para Job

```
POST /v1/users/jobs/:job_id/suggestion
```

**Request Body:**
```json
{
  "suggestion": {
    "type": "description",
    "job": {
      "title": "Desenvolvedor Ruby Senior",
      "description": "Descrição parcial...",
      "skills": ["Ruby", "Rails"],
      "responsibilities": ["Desenvolver APIs"],
      "seniority_level": "Sênior"
    }
  }
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggestion.type` | string | **Obrigatório**. Tipo: `title`, `description`, `skills`, `behavioral_skills`, `questions` |
| `suggestion.job` | object | Dados do job (opcional se job_id na URL) |

**Tipos de Sugestão:**

| Tipo | Resultado |
|------|-----------|
| `title` | 3 sugestões de título |
| `description` | Descrição completa com 5 skills + 2 behavioral skills |
| `skills` | 5 skills técnicas |
| `behavioral_skills` | 2 competências comportamentais (Big Five) |
| `questions` | 5 perguntas de entrevista |

**Response:** `200 OK`
```json
{
  "suggestion": {
    "titles": ["Engenheiro de Software Ruby Senior", "..."]
  }
}
```

### 7.2 Gerar Perguntas de Avaliação (WSI)

```
POST /v1/users/jobs/:id/suggestion/questions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | **Obrigatório**. `wsi_compact`, `wsi_compact_plus` ou `query` |
| `evaluation_id` | integer | ID da avaliação (opcional — se presente, cria as questions) |
| `query` | string | Query customizada (apenas para tipo `query`) |

**Modelos WSI:**

| Modelo | Perguntas | Duração | Precisão |
|--------|-----------|---------|----------|
| `wsi_compact` | 6-8 | 5-7 min | ~90% |
| `wsi_compact_plus` | 8-10 | 6:30-9 min | ~95% |
| `query` | 1 | 40s-1:30 min | ~90% |

**Response (sem evaluation_id):** `200 OK`
```json
{
  "questions": {
    "questions": [
      {
        "title": "Descreva uma situação em que...",
        "description": "Contexto da pergunta",
        "competence_type": "technical",
        "response_type": "contextual",
        "bloom_level": "analysis",
        "dreyfus_target": 4,
        "ocean_trait": null,
        "framework": "cbi",
        "framework_weights": {
          "bloom": 0.25,
          "dreyfus": 0.35,
          "big_five": 0.1,
          "cbi_star": 0.3
        },
        "validation_type_weight": 0.60,
        "time": 1.5,
        "category": "avaliacao"
      }
    ]
  }
}
```

**Response (com evaluation_id):** `200 OK`
```json
{
  "questions": { "..." },
  "created_questions": [
    { "id": 1, "title": "Descreva uma situação em que..." }
  ]
}
```

### 7.3 Gerar Query a partir dos Últimos Jobs

```
POST /v1/users/jobs/generate_query_from_job
```

Gera queries de busca baseadas nos últimos 3 jobs criados pelo account.

**Response:** `200 OK`
```json
[
  {
    "job_id": 1,
    "query": "Ruby Senior São Paulo"
  },
  {
    "job_id": 2,
    "query": "Python Pleno Remoto"
  }
]
```

---

## 8. Estrutura Organizacional

### 8.1 Obter Estrutura

```
GET /v1/users/jobs/:job_id/organizational_structure
```

**Response:** `200 OK`
```json
{
  "structure": {
    "department_id": 3,
    "department": "Engenharia",
    "team_id": null,
    "team": null,
    "team_composition": {},
    "reports_to": "CTO",
    "hiring_manager": "Maria Gerente",
    "team_size": 8
  },
  "complete": false,
  "suggestions": ["Adicionar composição do time", "Definir reports_to"],
  "warnings": [],
  "completion_percentage": 60.0,
  "job_id": "1"
}
```

### 8.2 Criar/Atualizar Estrutura

```
POST /v1/users/jobs/:job_id/organizational_structure
PATCH /v1/users/jobs/:job_id/organizational_structure
```

**Request Body:**
```json
{
  "organizational_data": {
    "department": {
      "name": "Engenharia",
      "parent": "Tecnologia"
    },
    "hiring_manager": {
      "name": "Maria Gerente",
      "title": "Engineering Manager",
      "email": "maria@empresa.com"
    },
    "team": {
      "name": "Backend Team",
      "size": 8,
      "description": "Equipe responsável por APIs e microserviços",
      "composition": [
        { "role": "Senior Developer", "count": 3, "description": "Devs seniores" },
        { "role": "Pleno Developer", "count": 4, "description": "Devs plenos" }
      ]
    },
    "reports_to": {
      "position": "CTO",
      "name": "Carlos Diretor"
    },
    "team_composition": [
      { "role": "Senior Developer", "count": 3, "description": "Devs seniores" }
    ]
  }
}
```

**Response:** `201 Created` / `200 OK`
```json
{
  "structure": { "..." },
  "complete": true,
  "suggestions": [],
  "warnings": [],
  "completion_percentage": 100.0,
  "success": true,
  "changes": ["department_updated", "hiring_manager_created"],
  "errors": [],
  "job_id": 1
}
```

---

## 9. Match de Candidatos

### 9.1 Buscar Candidatos por Similaridade

```
GET /v1/users/jobs/matches/candidates?job_id=:job_id
```

Utiliza embeddings vetoriais para encontrar candidatos similares à vaga.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `job_id` | integer | - | **Obrigatório**. ID do job |
| `top_k` | integer | 500 | Número de candidatos a buscar (máx 2000) |
| `page` | integer | 1 | Página |
| `per_page` | integer | 30 | Itens por página (máx 100) |
| `min_score` | float | 0.0 | Score mínimo (0.0 a 1.0) |
| `max_score` | float | 1.0 | Score máximo (0.0 a 1.0) |
| `filters` | object | `{}` | Filtros adicionais de busca |
| `include` | string | - | Includes (CSV) |
| `compact` | string | - | Campos específicos (CSV) |

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "50",
      "type": "job_candidate_match",
      "attributes": {
        "candidate_id": 50,
        "name": "Ana Silva",
        "score": 0.92
      }
    }
  ],
  "meta": {
    "total_count": 150,
    "page": 1,
    "per_page": 30,
    "total_pages": 5
  }
}
```

---

## 10. Busca Booleana e Dados para Descrição

### 10.1 Gerar Busca Booleana

```
POST /v1/users/jobs/boolean_search
```

Gera uma busca booleana para encontrar candidatos no LinkedIn via Google, baseada nas skills do job.

**Request Body:**
```json
{
  "job_id": 1
}
```

**Response:** Processado de forma assíncrona via WebSocket/mensagens.

### 10.2 Dados para Descrição

```
GET /v1/users/jobs/data_for_description?job_id=:job_id
```

Retorna o job com dados expandidos: remunerações, benefícios, skills e idiomas.

**Response:** `200 OK` — Job serializado com includes: `remunerations`, `benefits`, `skills`, `languages`.

---

## 11. Job Statuses

Base URL: `/v1/users/job_statuses`

### 11.1 Listar Statuses

```
GET /v1/users/job_statuses
```

**Statuses Padrão:**

| Status | Descrição |
|--------|-----------|
| Ativa | Vaga em andamento |
| Aprovada | Vaga aprovada |
| Aguardando aprovação | Pendente de aprovação |
| Reaberta | Vaga reaberta |
| Paralisada | Vaga temporariamente pausada |
| Interna | Vaga interna |
| Fechada (preenchida) | Vaga preenchida |
| Fechada (expirada) | Vaga expirada |
| Cancelada | Vaga cancelada |
| Rascunho | Vaga em rascunho |
| Arquivada | Vaga arquivada |
| Concluída | Processo concluído |

### 11.2 Obter Status

```
GET /v1/users/job_statuses/:id
```

### 11.3 Criar Status

```
POST /v1/users/job_statuses
```

**Request Body:**
```json
{
  "job_status": {
    "name": "Em Revisão",
    "color": "#FF9800"
  }
}
```

> Requer permissão de admin/super_admin.

### 11.4 Atualizar Status

```
PUT /v1/users/job_statuses/:id
```

### 11.5 Deletar Status

```
DELETE /v1/users/job_statuses/:id
```

---

## 12. Job Journeys

Base URL: `/v1/users/job_journeys`

Representam as etapas do fluxo de criação/gestão de uma vaga.

### 12.1 Listar Journeys

```
GET /v1/users/job_journeys
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `where[job_id]` | integer | Filtrar por job (null = template do account) |

**Journeys Padrão (15 etapas):**

| Posição | Nome | Obrigatório |
|---------|------|-------------|
| 1 | Informações Básicas | Sim |
| 2 | Remuneração e Benefícios | Não |
| 3 | Estrutura Organizacional | Sim |
| 4 | Requisitos Técnicos | Sim |
| 5 | Competências Comportamentais | Não |
| 6 | Estratégia de Busca (Sourcing) | Sim |
| 7 | Idiomas e Senioridade | Não |
| 8 | Localização e Regime | Sim |
| 9 | Etapas de Entrevistas | Sim |
| 10 | Perguntas de Screening | Sim |
| 11 | Cronograma | Não |
| 12 | Governança do Processo | Sim |
| 13 | Templates de Comunicação | Não |
| 14 | Job Description Completa | Sim |
| 15 | Publicação | Sim |

### 12.2 Obter Journey

```
GET /v1/users/job_journeys/:id
```

### 12.3 Criar Journey

```
POST /v1/users/job_journeys
```

**Request Body:**
```json
{
  "job_journey": {
    "name": "Revisão Técnica",
    "description": "Etapa de revisão técnica da vaga",
    "position": 5,
    "active": true,
    "required": false,
    "job_id": 1
  }
}
```

### 12.4 Atualizar Journey

```
PUT /v1/users/job_journeys/:id
```

### 12.5 Reordenar Journeys

```
PUT /v1/users/job_journeys/update_positions
```

**Request Body:**
```json
{
  "job_journeys": [
    { "id": 1, "position": 0 },
    { "id": 2, "position": 1 },
    { "id": 3, "position": 2 }
  ]
}
```

### 12.6 Deletar Journey

```
DELETE /v1/users/job_journeys/:id
```

---

## 13. Job Users (Equipe da Vaga)

Base URL: `/v1/users/job_users`

Gerencia os membros da equipe associados a uma vaga.

### 13.1 Listar Membros

```
GET /v1/users/job_users
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `where[job_id]` | integer | Filtrar por vaga |
| `where[user_id]` | integer | Filtrar por usuário |
| `compact` | string | Campos (CSV) |

### 13.2 Obter Membro

```
GET /v1/users/job_users/:id
```

### 13.3 Atribuir Membro

```
POST /v1/users/job_users
```

**Request Body:**
```json
{
  "job_user": {
    "user_id": 10,
    "job_id": 1,
    "person_function": "Entrevistador",
    "split": 50
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `user_id` | integer | Sim | ID do usuário |
| `job_id` | integer | Sim | ID do job |
| `person_function` | string | Não | Função na vaga |
| `split` | integer | Não | Percentual de split (0-100) |

### 13.4 Atualizar Membro

```
PUT /v1/users/job_users/:id
```

### 13.5 Remover Membro

```
DELETE /v1/users/job_users/:id
```

---

## 14. Job Field Templates

Base URL: `/v1/users/job_field_templates`

Templates que definem quais campos são obrigatórios na criação de vagas.

### 14.1 Listar Templates

```
GET /v1/users/job_field_templates
```

### 14.2 Obter Template

```
GET /v1/users/job_field_templates/:id
```

### 14.3 Criar Template

```
POST /v1/users/job_field_templates
```

**Request Body:**
```json
{
  "job_field_template": {
    "name": "Template Padrão",
    "is_default": true,
    "fields": [
      {
        "field_name": "title",
        "label": "Título da Vaga",
        "is_required": true,
        "category": "basic",
        "priority": 1,
        "job_journey_position": 1
      },
      {
        "field_name": "salary_from",
        "label": "Faixa Salarial (De)",
        "is_required": false,
        "category": "compensation",
        "priority": 2,
        "job_journey_position": 2
      }
    ]
  }
}
```

### 14.4 Atualizar Template

```
PUT /v1/users/job_field_templates/:id
```

### 14.5 Deletar Template

```
DELETE /v1/users/job_field_templates/:id
```

### 14.6 Obter Campos Padrão

```
GET /v1/users/job_field_templates/default_fields
```

**Response:** `200 OK`
```json
{
  "data": {
    "type": "default_fields",
    "attributes": {
      "fields": [
        { "field_name": "title", "label": "Título da Vaga", "is_required": true },
        { "field_name": "seniority", "label": "Senioridade", "is_required": true },
        { "field_name": "salary_from", "label": "Faixa Salarial (De)", "is_required": false }
      ]
    }
  }
}
```

---

## Opinião: Endpoints Faltantes

Analisando a API como um todo, seguem sugestões de endpoints que poderiam agregar valor:

### Faltantes com Prioridade Alta

1. **`GET /v1/users/jobs/:id/analytics`** — Dashboard com métricas da vaga: tempo médio por etapa, taxa de conversão por stage, funil de candidatos, tempo desde publicação. Hoje essas métricas não são expostas via API.

2. **`GET /v1/users/jobs/:id/activity_log`** — Histórico de alterações da vaga. O model já possui `HasActivityLog`, mas não há endpoint para consultar o log de atividades de um job específico.

3. **`POST /v1/users/jobs/:id/change_status`** — Endpoint dedicado para mudar o status com validação de transições (ex: impedir de ir direto de "Rascunho" para "Fechada"). Hoje a mudança de status é feita via `PUT update` sem validação de fluxo.

4. **`POST /v1/users/jobs/:id/publish`** / **`POST /v1/users/jobs/:id/unpublish`** — Ações explícitas de publicação/despublicação. Já existe `is_ready_for_publication` no serializer, mas não há endpoint que execute a publicação com validações.

### Faltantes com Prioridade Média

5. **`GET /v1/users/jobs/:id/candidates`** — Listar candidatos de um job de forma simplificada (sem a complexidade do kanban). Hoje para listar candidatos é necessário usar o kanban ou a API de applies com filtro.

6. **`POST /v1/users/jobs/:id/duplicate_selective_processes`** — Copiar as etapas de outro job. Hoje só é possível copiar etapas durante a cópia do job inteiro.

7. **`GET /v1/users/jobs/:id/evaluations`** — Listar avaliações do job. As evaluations existem no model mas não têm endpoint aninhado ao job.

8. **`POST /v1/users/jobs/bulk_update`** — Atualização em lote de campos (ex: mudar hiring_manager de várias vagas). Hoje só existem operações em lote para archive/unarchive/activate/pause.

### Faltantes com Prioridade Baixa

9. **`GET /v1/users/jobs/:id/export`** — Exportar dados do job em CSV/PDF. Útil para relatórios e compartilhamento com stakeholders.

10. **`POST /v1/users/jobs/:id/share`** — Compartilhar vaga via link/email com usuários externos ou internos (não recrutadores).

11. **`GET /v1/users/jobs/stats`** — Estatísticas globais: total por status, vagas abertas vs fechadas no período, tempo médio de fechamento, etc.
