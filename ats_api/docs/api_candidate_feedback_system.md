# API: Sistema de Like/Dislike (Candidate Feedback)

Documentação completa do sistema de feedback (like/dislike) para candidatos e sourced profiles no WeDO Talent ATS.

---

## Visão Geral

O sistema possui **dois mecanismos de feedback** que operam de forma integrada:

| Sistema | Quem usa | Ações | Modelo |
|---|---|---|---|
| **CandidateFeedback** | Recrutador (frontend) | `like` / `dislike` | `CandidateFeedback` |
| **AgentFeedback** | Background Agent (IA) | `approved` / `rejected` | `AgentFeedback` |

Os dois sistemas são **sincronizados bidirecionalmente**:
- Quando o recrutador dá like/dislike em um perfil de background agent → cria `AgentFeedback` correspondente
- Quando o background agent aprova/rejeita → cria `CandidateFeedback` correspondente

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│ RECRUTADOR (Frontend)                                       │
│                                                             │
│  Like/Dislike em:                                           │
│   - Candidato direto                                        │
│   - Candidato em Sourcing                                   │
│   - SourcedProfileSourcing (resultado de busca)             │
│   - Apply (candidatura)                                     │
└────────────────────────┬────────────────────────────────────┘
                         │ POST /candidate_feedbacks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ CandidateFeedbacks::UpsertService                           │
│                                                             │
│  1. Valida contexto (sourcing, apply, candidate, SPS)       │
│  2. Busca feedback existente do mesmo user + contexto       │
│  3. Se existe com mesmo tipo → REMOVE (toggle off)          │
│  4. Se existe com tipo diferente → ATUALIZA (toggle)        │
│  5. Se não existe → CRIA novo                               │
│  6. Salva snapshots (query + score do momento)              │
│  7. Sincroniza com AgentFeedback se SPS é de agent          │
└────────────────────────┬────────────────────────────────────┘
                         │ se SPS é de background_agent
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ BackgroundAgents::ProcessFeedbackService                     │
│                                                             │
│  1. Cria AgentFeedback (approved/rejected)                  │
│  2. Atualiza contadores (total_approved, total_rejected)    │
│  3. Verifica calibração (≥5 feedbacks → calibrated)         │
│  4. Enfileira ExtractPreferencesJob se calibrado            │
│  5. Atualiza last_interaction_at                            │
│  6. Marca ciclo como reviewed se todos avaliados            │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. CandidateFeedback — Like/Dislike de Candidatos

### Endpoint: Criar ou Alternar Feedback

```
POST /v1/users/candidate_feedbacks
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

#### Comportamento de Toggle

O sistema funciona como **toggle inteligente**:

| Estado atual | Ação enviada | Resultado |
|---|---|---|
| Sem feedback | `like` | Cria feedback `like` |
| Sem feedback | `dislike` | Cria feedback `dislike` |
| Já tem `like` | `like` | **Remove** feedback (toggle off) |
| Já tem `like` | `dislike` | **Atualiza** para `dislike` |
| Já tem `dislike` | `dislike` | **Remove** feedback (toggle off) |
| Já tem `dislike` | `like` | **Atualiza** para `like` |

#### Contextos Suportados

O feedback pode ser dado em **4 contextos diferentes**, de acordo com os campos enviados:

| Contexto | Campo obrigatório | Descrição |
|---|---|---|
| **Candidato direto** | `candidate_id` | Like/dislike no perfil do candidato (sem vínculo a vaga) |
| **Sourcing** | `sourcing_id` + `candidate_id` | Like/dislike em resultado de busca |
| **SourcedProfileSourcing** | `sourced_profile_sourcing_id` | Like/dislike em perfil entregue por background agent ou busca similar |
| **Apply** | `apply_id` | Like/dislike em candidatura a uma vaga |

**Regra:** Pelo menos um contexto deve estar presente.

---

### Request: Like em Candidato Direto

```json
{
  "candidate_id": 1234,
  "feedback_type": "like"
}
```

### Request: Dislike em SourcedProfileSourcing (com motivo)

```json
{
  "sourced_profile_sourcing_id": 456,
  "feedback_type": "dislike",
  "reason": "Sem experiência em cloud"
}
```

### Request: Like em Candidato de Sourcing

```json
{
  "sourcing_id": 789,
  "candidate_id": 1234,
  "feedback_type": "like",
  "job_id": 100
}
```

### Request: Like em Apply (candidatura)

```json
{
  "apply_id": 555,
  "feedback_type": "like"
}
```

### Request: Feedback com referência polimórfica

```json
{
  "candidate_id": 1234,
  "feedback_type": "dislike",
  "reason": "Overqualified",
  "reference_type": "Job",
  "reference_id": 100
}
```

### Campos do Request

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `feedback_type` | string | **Sim** | `"like"` ou `"dislike"` |
| `candidate_id` | integer | Condicional | ID do candidato |
| `sourcing_id` | integer | Condicional | ID do sourcing |
| `sourced_profile_sourcing_id` | integer | Condicional | ID do sourced_profile_sourcing |
| `apply_id` | integer | Condicional | ID da aplicação |
| `job_id` | integer | Não | ID da vaga (preenchido automaticamente se apply_id presente) |
| `reason` | string | Não | Motivo do feedback (texto livre) |
| `reference_type` | string | Não | Tipo polimórfico de referência (ex: `"Job"`, `"Sourcing"`) |
| `reference_id` | integer | Não | ID da referência polimórfica |

---

### Response: Feedback Criado (201 Created)

```json
{
  "data": {
    "id": "789",
    "type": "candidate_feedback",
    "attributes": {
      "id": 789,
      "sourcing_id": null,
      "apply_id": null,
      "candidate_id": 1234,
      "user_id": 10,
      "account_id": 1,
      "job_id": null,
      "sourced_profile_sourcing_id": 456,
      "reference_type": null,
      "reference_id": null,
      "reason": "Sem experiência em cloud",
      "feedback_type": "dislike",
      "search_query_snapshot": {
        "query": "Ruby Senior Developer",
        "provider": "background_agent",
        "searched_at": "2026-04-01T10:00:00Z",
        "results_count": 15
      },
      "candidate_score_snapshot": {
        "sourcing_score": 73,
        "search_source": "background_agent",
        "search_score": 82
      },
      "is_deleted": false,
      "is_like": false,
      "is_dislike": true,
      "context": "sourced_profile_sourcing",
      "query_summary": {
        "query": "Ruby Senior Developer",
        "searched_at": "2026-04-01T10:00:00Z"
      },
      "candidate_score": 73,
      "created_at": "2026-04-06T15:30:00Z",
      "updated_at": "2026-04-06T15:30:00Z"
    },
    "relationships": {
      "sourcing": { "data": null },
      "apply": { "data": null },
      "candidate": { "data": { "id": "1234", "type": "candidate" } },
      "user": { "data": { "id": "10", "type": "user" } },
      "job": { "data": null },
      "sourced_profile_sourcing": { "data": { "id": "456", "type": "sourced_profile_sourcing" } }
    }
  },
  "meta": {
    "action": "created",
    "message": "Feedback created successfully"
  }
}
```

### Response: Feedback Atualizado (toggle like → dislike) (200 OK)

```json
{
  "data": {
    "id": "789",
    "type": "candidate_feedback",
    "attributes": {
      "feedback_type": "like",
      "is_like": true,
      "is_dislike": false,
      "...": "..."
    }
  },
  "meta": {
    "action": "updated",
    "message": "Feedback updated successfully"
  }
}
```

### Response: Feedback Removido (toggle off — mesmo tipo) (200 OK)

```json
{
  "data": {
    "id": "789",
    "type": "candidate_feedback",
    "attributes": {
      "is_deleted": true,
      "feedback_type": "like",
      "...": "..."
    }
  },
  "meta": {
    "action": "removed",
    "message": "Feedback removed successfully"
  }
}
```

---

### Endpoint: Listar Feedbacks

```
GET /v1/users/candidate_feedbacks
Authorization: Bearer <jwt_token>
```

Usa o padrão `perform_search` (Searchkick) — suporta filtros, paginação e aggregations.

#### Query Params

| Param | Tipo | Descrição |
|---|---|---|
| `where` | JSON | Filtros estruturados |
| `search` | string | Busca full-text |
| `page` | integer | Página (default: 1) |
| `per_page` | integer | Itens por página (max: 30) |
| `order` | JSON | Ordenação |

#### Exemplos de Filtros (`where`)

```
# Feedbacks de um sourcing específico
GET /v1/users/candidate_feedbacks?where={"sourcing_id":789}

# Apenas likes
GET /v1/users/candidate_feedbacks?where={"feedback_type":"like"}

# Feedbacks de um candidato específico
GET /v1/users/candidate_feedbacks?where={"candidate_id":1234}

# Feedbacks de um sourced_profile_sourcing
GET /v1/users/candidate_feedbacks?where={"sourced_profile_sourcing_id":456}

# Feedbacks de uma vaga específica
GET /v1/users/candidate_feedbacks?where={"job_id":100}

# Feedbacks do usuário atual
GET /v1/users/candidate_feedbacks?where={"user_id":10}
```

#### Response (Lista)

```json
{
  "data": [
    {
      "id": "789",
      "type": "candidate_feedback",
      "attributes": {
        "id": 789,
        "feedback_type": "like",
        "candidate_id": 1234,
        "sourcing_id": 789,
        "is_like": true,
        "is_dislike": false,
        "context": "sourcing",
        "reason": null,
        "candidate_score": 82,
        "created_at": "2026-04-06T15:30:00Z",
        "...": "..."
      }
    },
    {
      "id": "790",
      "type": "candidate_feedback",
      "attributes": {
        "id": 790,
        "feedback_type": "dislike",
        "candidate_id": 5678,
        "sourced_profile_sourcing_id": 456,
        "is_like": false,
        "is_dislike": true,
        "context": "sourced_profile_sourcing",
        "reason": "Sem experiência em cloud",
        "candidate_score": 45,
        "created_at": "2026-04-06T15:35:00Z",
        "...": "..."
      }
    }
  ],
  "meta": {
    "total": 25
  }
}
```

---

### Endpoint: Remover Feedback

```
DELETE /v1/users/candidate_feedbacks/:id
Authorization: Bearer <jwt_token>
```

Soft-delete (`is_deleted: true`). Também aceita `DELETE /v1/users/candidate_feedbacks` com `where` params.

#### Response (200 OK)

```json
{
  "data": {
    "id": "789",
    "type": "candidate_feedback",
    "attributes": {
      "is_deleted": true,
      "...": "..."
    }
  },
  "meta": {
    "message": "Feedback removed successfully"
  }
}
```

---

## 2. AgentFeedback — Feedback em Background Agent

Usado para aprovar/rejeitar candidatos entregues pelo Background Agent. O feedback alimenta o ciclo de calibração e aprendizado do agente.

### Endpoint: Feedback Individual

```
POST /v1/users/background_agents/:background_agent_id/feedbacks
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

#### Request

```json
{
  "feedback": {
    "sourced_profile_sourcing_id": 456,
    "action": "approved",
    "reason": "Perfil excelente, experiência relevante"
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `sourced_profile_sourcing_id` | integer | **Sim** | ID do sourced_profile_sourcing a avaliar |
| `action` | string | **Sim** | `"approved"` ou `"rejected"` |
| `agent_cycle_id` | integer | Não | ID do ciclo (usa ciclo atual se omitido) |
| `reason` | string | Não | Motivo da aprovação/rejeição |

**Aliases aceitos:** `agent_candidate_id` → `sourced_profile_sourcing_id`, `status` → `action`

#### Response (201 Created)

```json
{
  "processed": 1,
  "calibration_state": "learning",
  "mode": "manual"
}
```

---

### Endpoint: Feedback em Lote (Bulk)

```
POST /v1/users/background_agents/:background_agent_id/feedbacks/bulk
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

#### Request

```json
{
  "feedbacks": [
    {
      "sourced_profile_sourcing_id": 456,
      "action": "approved",
      "reason": "Match excelente"
    },
    {
      "sourced_profile_sourcing_id": 457,
      "action": "rejected",
      "reason": "Sem experiência necessária"
    },
    {
      "sourced_profile_sourcing_id": 458,
      "action": "approved"
    }
  ]
}
```

**Limite:** Máximo 100 feedbacks por request.

#### Response (201 Created)

```json
{
  "processed": 3,
  "calibration_state": "calibrated",
  "mode": "manual"
}
```

---

### Calibração do Agente

O feedback alimenta um ciclo de calibração:

| Estado | Condição | Comportamento |
|---|---|---|
| `pending` | 0 feedbacks | Agente usa apenas critérios da vaga |
| `learning` | 1-4 feedbacks | Agente começa a registrar padrões |
| `calibrated` | ≥5 feedbacks | Dispara `ExtractPreferencesJob` — agente aprende preferências |

#### Preferências Extraídas (após calibração)

```json
{
  "preferred_skills": ["Ruby on Rails", "PostgreSQL", "Docker"],
  "preferred_titles": ["Senior Developer", "Tech Lead"],
  "preferred_companies": ["PagSeguro", "Nubank"],
  "preferred_locations": ["São Paulo, SP, Brasil"],
  "experience_range": { "min": 5, "max": 10 },
  "avoid_patterns": ["Sem experiência em cloud", "Junior demais"],
  "sample_size": { "approved": 8, "rejected": 4 },
  "extracted_at": "2026-04-06T15:30:00Z"
}
```

---

## 3. Feedback no SourcedProfileSourcing

O `SourcedProfileSourcingSerializer` expõe os feedbacks diretamente em cada resultado de sourcing:

```json
{
  "data": {
    "id": "456",
    "type": "sourced_profile_sourcing",
    "attributes": {
      "score": 73,
      "search_source": "background_agent",
      "candidate_feedback": "like",
      "likes": [
        {
          "id": 789,
          "user_id": 10,
          "created_at": "2026-04-06T15:30:00Z"
        }
      ],
      "dislikes": [],
      "...": "..."
    }
  }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `candidate_feedback` | string \| null | Tipo de feedback ativo do usuário (`"like"`, `"dislike"`, ou `null`) |
| `likes` | array | Lista de likes ativos com `id`, `user_id`, `created_at` |
| `dislikes` | array | Lista de dislikes ativos com `id`, `user_id`, `reason`, `created_at` |

---

## 4. Refinamento por Feedback (Sourcings)

Endpoint que usa likes/dislikes para refinar buscas de candidatos similares.

### Endpoint

```
POST /v1/users/sourcings/:sourcing_id/refinements
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Request

```json
{
  "liked_candidate_ids": [1234, 5678],
  "disliked_feedbacks": [
    {
      "candidate_id": 9012,
      "reason": "Sem experiência necessária em cloud"
    },
    {
      "candidate_id": 9013,
      "reason": "Senioridade abaixo do esperado"
    }
  ],
  "sources": ["local"],
  "limit": 20
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `liked_candidate_ids` | array[integer] | Não | IDs dos candidatos aprovados |
| `disliked_feedbacks` | array[object] | Não | Candidatos rejeitados com motivo |
| `disliked_feedbacks[].candidate_id` | integer | Sim | ID do candidato rejeitado |
| `disliked_feedbacks[].reason` | string | Não | Motivo da rejeição |
| `sources` | array[string] | Não | Fontes de busca (`["local"]` default) |
| `limit` | integer | Não | Máximo de resultados (1-50, default: 20) |

### Fluxo Interno

1. Salva feedbacks como `CandidateFeedback` (likes e dislikes)
2. Analisa padrões de feedback via `FeedbackAnalyzerService` (LLM)
3. Extrai perfil desejado, padrões de rejeição e padrões positivos
4. Refina embeddings usando feedback para buscar candidatos mais alinhados
5. Retorna novos candidatos ranqueados

### Response (200 OK)

```json
{
  "candidates": [
    {
      "id": 2345,
      "name": "Ana Costa",
      "score": 0.89,
      "...": "dados do candidato"
    }
  ],
  "feedback_analysis": {
    "desired_profile": "Senior backend developer with cloud experience and fintech background",
    "rejection_patterns": ["Lack of cloud experience", "Junior level"],
    "positive_patterns": ["Strong Ruby/Rails", "Fintech experience", "Senior level"],
    "explanation": "Recruiter prefers senior profiles with cloud + fintech combination"
  },
  "meta": {
    "total": 15,
    "sources_used": ["local"]
  }
}
```

---

## 5. Sincronização entre Sistemas

### Recrutador → Agente (CandidateFeedback → AgentFeedback)

Quando o recrutador dá like/dislike em um `SourcedProfileSourcing` que veio de um background agent:

```
CandidateFeedbacks::UpsertService
  │
  ├── Verifica se SPS.search_source == "background_agent"
  ├── Encontra o AgentCycle correspondente
  ├── Chama BackgroundAgents::ProcessFeedbackService
  │     └── Cria AgentFeedback com:
  │           action = like → "approved"
  │           action = dislike → "rejected"
  │
  └── Atualiza contadores e calibração do agente
```

### Agente → Recrutador (AgentFeedback → CandidateFeedback)

Quando o ProcessFeedbackService cria um AgentFeedback:

```
BackgroundAgents::ProcessFeedbackService
  │
  └── sync_candidate_feedback
        └── CandidateFeedbacks::UpsertService.call(
              sourced_profile_sourcing_id: sps.id,
              feedback_type: approved → "like" / rejected → "dislike",
              skip_agent_sync: true  ← evita loop infinito
            )
```

### Remoção (Toggle Off)

Quando o recrutador remove um feedback (clica novamente no mesmo botão):

```
CandidateFeedbacks::UpsertService
  │
  ├── Detecta: mesmo tipo de feedback já existe
  ├── soft_delete! (is_deleted: true)
  └── remove_agent_feedback → AgentFeedback.destroy_all para aquele SPS
```

---

## 6. Campos do CandidateFeedback (Schema)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | integer | ID do feedback |
| `sourcing_id` | integer | Sourcing onde o candidato foi encontrado |
| `apply_id` | integer | Apply (candidatura) onde o feedback foi dado |
| `candidate_id` | integer | ID do candidato |
| `sourced_profile_sourcing_id` | integer | SPS de background agent/busca similar |
| `user_id` | integer | Usuário que deu o feedback |
| `account_id` | integer | Account (tenant) |
| `job_id` | integer | Vaga relacionada |
| `reference_type` | string | Tipo polimórfico de referência |
| `reference_id` | integer | ID da referência polimórfica |
| `feedback_type` | string | `"like"` ou `"dislike"` |
| `reason` | text | Motivo do feedback (texto livre) |
| `search_query_snapshot` | jsonb | Snapshot da query de busca no momento do feedback |
| `candidate_score_snapshot` | jsonb | Snapshot do score do candidato no momento do feedback |
| `is_deleted` | boolean | Soft delete |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Última atualização |

---

## 7. Campos do AgentFeedback (Schema)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | integer | ID do feedback |
| `background_agent_id` | integer | ID do background agent |
| `agent_cycle_id` | integer | ID do ciclo do agente |
| `sourced_profile_sourcing_id` | integer | ID do SPS avaliado |
| `action` | string | `"approved"` ou `"rejected"` |
| `reason` | text | Motivo |
| `created_at` | datetime | Criação |
| `updated_at` | datetime | Última atualização |

**Constraint:** Único por `(background_agent_id, sourced_profile_sourcing_id)` — um agente só pode dar um feedback por perfil.

---

## 8. Respostas de Erro

### Contexto ausente (422)

```json
{
  "errors": ["At least one context must be present"]
}
```

### Tipo de feedback inválido (422)

```json
{
  "errors": ["Invalid feedback type"]
}
```

### Candidato não encontrado (422)

```json
{
  "errors": ["Candidate not found"]
}
```

### SourcedProfileSourcing não encontrado (422)

```json
{
  "errors": ["SourcedProfileSourcing not found"]
}
```

### Background Agent não encontrado (404)

```json
{
  "errors": ["BackgroundAgent não encontrado"]
}
```

### Limite de bulk excedido (422)

```json
{
  "errors": ["Maximum 100 feedbacks per request"]
}
```

---

## 9. Guia de Implementação Frontend

### Estado Visual do Like/Dislike

```javascript
// Estado do botão baseado na resposta
const feedbackState = {
  none: { likeActive: false, dislikeActive: false },
  like: { likeActive: true, dislikeActive: false },
  dislike: { likeActive: false, dislikeActive: true }
}

// Determinar estado a partir do SPS (sourced_profile_sourcing)
function getFeedbackState(sps) {
  if (sps.attributes.candidate_feedback === 'like') return feedbackState.like
  if (sps.attributes.candidate_feedback === 'dislike') return feedbackState.dislike
  return feedbackState.none
}
```

### Dar Like/Dislike

```javascript
async function toggleFeedback(context, feedbackType) {
  const payload = {
    feedback_type: feedbackType, // "like" ou "dislike"
    ...context // { candidate_id } ou { sourced_profile_sourcing_id } ou { apply_id }
  }

  const response = await api.post('/v1/users/candidate_feedbacks', payload)

  const { action } = response.data.meta
  // action pode ser: "created", "updated", "removed"

  if (action === 'removed') {
    // Feedback foi removido (toggle off) — desativar botão
  } else if (action === 'created' || action === 'updated') {
    // Feedback ativo — ativar botão correspondente
    const type = response.data.data.attributes.feedback_type
    // Atualizar UI: ativar botão 'type', desativar o outro
  }
}

// Exemplos de uso:
toggleFeedback({ candidate_id: 1234 }, 'like')
toggleFeedback({ sourced_profile_sourcing_id: 456 }, 'dislike')
toggleFeedback({ apply_id: 555 }, 'like')

// Com motivo (dislike):
async function dislikeWithReason(spsId, reason) {
  await api.post('/v1/users/candidate_feedbacks', {
    sourced_profile_sourcing_id: spsId,
    feedback_type: 'dislike',
    reason: reason
  })
}
```

### Listar Feedbacks

```javascript
// Feedbacks de um sourcing
const feedbacks = await api.get('/v1/users/candidate_feedbacks', {
  params: { where: JSON.stringify({ sourcing_id: 789 }) }
})

// Apenas likes de uma vaga
const likes = await api.get('/v1/users/candidate_feedbacks', {
  params: { where: JSON.stringify({ job_id: 100, feedback_type: 'like' }) }
})

// Feedbacks de um candidato específico
const candidateFeedbacks = await api.get('/v1/users/candidate_feedbacks', {
  params: { where: JSON.stringify({ candidate_id: 1234 }) }
})
```

### Remover Feedback

```javascript
// Por ID
await api.delete(`/v1/users/candidate_feedbacks/${feedbackId}`)

// Por contexto (DELETE na collection)
await api.delete('/v1/users/candidate_feedbacks', {
  params: { where: JSON.stringify({ sourced_profile_sourcing_id: 456 }) }
})
```

### Feedback em Background Agent (Bulk)

```javascript
async function submitAgentFeedbacks(agentId, feedbacks) {
  const response = await api.post(
    `/v1/users/background_agents/${agentId}/feedbacks/bulk`,
    {
      feedbacks: feedbacks.map(f => ({
        sourced_profile_sourcing_id: f.spsId,
        action: f.approved ? 'approved' : 'rejected',
        reason: f.reason || null
      }))
    }
  )

  // response.data = { processed: 5, calibration_state: "calibrated", mode: "manual" }
  return response.data
}
```

### Refinamento de Busca com Feedback

```javascript
async function refineSearch(sourcingId, likedIds, dislikedFeedbacks) {
  const response = await api.post(
    `/v1/users/sourcings/${sourcingId}/refinements`,
    {
      liked_candidate_ids: likedIds,
      disliked_feedbacks: dislikedFeedbacks.map(d => ({
        candidate_id: d.candidateId,
        reason: d.reason
      })),
      sources: ['local'],
      limit: 20
    }
  )

  // response.data.candidates = novos candidatos refinados
  // response.data.feedback_analysis = análise LLM dos padrões
  return response.data
}
```

---

## 10. Resumo de Rotas

| Método | Rota | Ação | Descrição |
|---|---|---|---|
| `POST` | `/v1/users/candidate_feedbacks` | create | Criar/alternar like/dislike |
| `GET` | `/v1/users/candidate_feedbacks` | index | Listar feedbacks (com filtros) |
| `DELETE` | `/v1/users/candidate_feedbacks/:id` | destroy | Remover feedback por ID |
| `DELETE` | `/v1/users/candidate_feedbacks` | destroy | Remover feedback por contexto |
| `POST` | `/v1/users/background_agents/:id/feedbacks` | create | Feedback individual do agente |
| `POST` | `/v1/users/background_agents/:id/feedbacks/bulk` | bulk | Feedback em lote do agente |
| `POST` | `/v1/users/sourcings/:id/refinements` | create | Refinar busca com likes/dislikes |

---

## 11. Atributos Computados no Serializer

### `context` (CandidateFeedbackSerializer)

Calculado pela prioridade do contexto:

| Prioridade | Campo presente | Valor retornado |
|---|---|---|
| 1 | `apply_id` | `"apply"` |
| 2 | `sourced_profile_sourcing_id` | `"sourced_profile_sourcing"` |
| 3 | `sourcing_id` | `"sourcing"` |
| 4 | `candidate_id` | `"candidate"` |

### `is_like` / `is_dislike`

Booleanos derivados de `feedback_type`:

```json
{
  "feedback_type": "like",
  "is_like": true,
  "is_dislike": false
}
```

### `candidate_score`

Score do candidato no momento do feedback (snapshot):

```json
{
  "candidate_score": 73,
  "query_summary": {
    "query": "Ruby Senior Developer",
    "searched_at": "2026-04-01T10:00:00Z"
  }
}
```

### `search_query_snapshot` / `candidate_score_snapshot`

Snapshots completos salvos no momento do feedback para auditoria:

```json
{
  "search_query_snapshot": {
    "query": "Ruby Senior Developer",
    "provider": "background_agent",
    "parameters": {},
    "searched_at": "2026-04-01T10:00:00Z",
    "results_count": 15
  },
  "candidate_score_snapshot": {
    "sourcing_score": 73,
    "search_source": "background_agent",
    "search_score": 82,
    "cv_match": 0.85,
    "total_score": 78
  }
}
```
