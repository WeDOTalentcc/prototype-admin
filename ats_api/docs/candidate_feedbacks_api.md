# Candidate Feedbacks — Like e Dislike de Candidatos

## Visao Geral

A feature de feedback permite que usuarios avaliem candidatos com **like** ou **dislike** em diferentes contextos: funil (apply), sourcing, perfil sourcado, ou candidato avulso.

O sistema e um **upsert inteligente** — nao e necessario verificar se ja existe um feedback antes de enviar. O backend trata os tres casos:

| Situacao                              | Comportamento                              | `action` retornado |
|---------------------------------------|--------------------------------------------|--------------------|
| Nenhum feedback existe                | Cria novo                                  | `created`          |
| Feedback existe com mesmo tipo        | Remove (soft delete / toggle off)          | `removed`          |
| Feedback existe com tipo diferente    | Atualiza para o novo tipo                  | `updated`          |

---

## Contextos suportados

Ao menos um destes campos e obrigatorio por requisicao:

| Campo                        | Contexto                                       |
|------------------------------|------------------------------------------------|
| `apply_id`                   | Candidato no funil de uma vaga                 |
| `sourced_profile_sourcing_id`| Perfil retornado em um sourcing                |
| `sourcing_id` + `candidate_id` | Candidato dentro de um sourcing especifico   |
| `candidate_id`               | Candidato avulso (sem contexto de vaga)        |

> Quando `apply_id` e informado, `candidate_id` e `job_id` sao preenchidos automaticamente pelo backend.
> Quando `sourced_profile_sourcing_id` e informado, `sourcing_id` e `candidate_id` sao preenchidos automaticamente.

---

## Endpoints

### `GET /v1/users/candidate_feedbacks`

Lista feedbacks com suporte a filtros e busca.

**Query params comuns (padrao do sistema de search):**

| Param   | Exemplo                                               | Descricao                        |
|---------|-------------------------------------------------------|----------------------------------|
| `where` | `{"apply_id":123}`                                    | Filtros exatos                   |
| `where` | `{"candidate_id":456,"feedback_type":"like"}`         | Multiplos filtros                |
| `where` | `{"job_id":789,"is_deleted":false}`                   | Por vaga                         |
| `q`     | `"joao"`                                              | Busca textual (nome, query, etc) |
| `page`  | `{"number":1,"size":20}`                              | Paginacao                        |

`account_id` e `is_deleted: false` sao injetados automaticamente — nao e necessario enviar.

**Resposta (200):**

```json
{
  "data": [
    {
      "id": "1",
      "type": "candidate_feedback",
      "attributes": {
        "id": 1,
        "sourcing_id": null,
        "apply_id": 42,
        "candidate_id": 7,
        "user_id": 3,
        "account_id": 1,
        "job_id": 10,
        "sourced_profile_sourcing_id": null,
        "reference_type": null,
        "reference_id": null,
        "reason": "Perfil muito fora do esperado",
        "feedback_type": "dislike",
        "is_like": false,
        "is_dislike": true,
        "context": "apply",
        "search_query_snapshot": {},
        "candidate_score_snapshot": { "cv_match": 42.0 },
        "query_summary": null,
        "candidate_score": null,
        "is_deleted": false,
        "created_at": "2026-03-06T10:00:00.000Z",
        "updated_at": "2026-03-06T10:00:00.000Z"
      }
    }
  ],
  "meta": { "total": 1 }
}
```

---

### `POST /v1/users/candidate_feedbacks`

Cria, atualiza ou remove um feedback (upsert). **Este e o endpoint principal — use-o para like e dislike.**

**Body:**

```json
{
  "feedback_type": "like",
  "apply_id": 42,
  "reason": "Excelente experiencia",
  "job_id": 10
}
```

```json
{
  "feedback_type": "dislike",
  "sourced_profile_sourcing_id": 88,
  "reason": "Nivel de senioridade abaixo do esperado"
}
```

```json
{
  "feedback_type": "like",
  "sourcing_id": 15,
  "candidate_id": 7
}
```

**Campos aceitos:**

| Campo                        | Tipo    | Obrigatorio              | Descricao                             |
|------------------------------|---------|--------------------------|---------------------------------------|
| `feedback_type`              | string  | sim                      | `"like"` ou `"dislike"`               |
| `apply_id`                   | integer | contexto (ver acima)     | ID do apply no funil                  |
| `sourced_profile_sourcing_id`| integer | contexto (ver acima)     | ID do sourced profile sourcing        |
| `sourcing_id`                | integer | contexto (ver acima)     | ID do sourcing                        |
| `candidate_id`               | integer | contexto (ver acima)     | ID do candidato                       |
| `job_id`                     | integer | nao                      | ID da vaga (preenchido auto via apply)|
| `reason`                     | string  | nao                      | Justificativa textual                 |
| `reference_type`             | string  | nao                      | Tipo de referencia polimorfica        |
| `reference_id`               | integer | nao                      | ID da referencia polimorfica          |

**Resposta — criado (201):**

```json
{
  "data": {
    "id": "1",
    "type": "candidate_feedback",
    "attributes": { "feedback_type": "like", "is_like": true, "is_dislike": false, "context": "apply", ... }
  },
  "meta": {
    "action": "created",
    "message": "Feedback created successfully"
  }
}
```

**Resposta — atualizado (200):**

```json
{
  "meta": { "action": "updated", "message": "Feedback updated successfully" }
}
```

**Resposta — removido / toggle off (200):**

```json
{
  "meta": { "action": "removed", "message": "Feedback removed successfully" }
}
```

**Erros (422):**

```json
{
  "errors": ["At least one context must be present"]
}
```

```json
{
  "errors": ["Invalid feedback type"]
}
```

---

### `DELETE /v1/users/candidate_feedbacks/:id`

Remove um feedback especifico por ID.

**Resposta (200):**

```json
{
  "data": { ... },
  "meta": { "message": "Feedback removed successfully" }
}
```

**Erro (404):** feedback nao encontrado ou nao pertence a conta.

---

### `DELETE /v1/users/candidate_feedbacks/` (collection)

Remove feedback buscando pelos filtros `where`. Util quando nao se tem o `id` mas se tem os dados de contexto.

**Query params:**

```
DELETE /v1/users/candidate_feedbacks/?where={"apply_id":42}
```

---

## Campo `context` na resposta

O serializer resolve automaticamente qual contexto esta ativo, em ordem de prioridade:

```
apply_id > sourced_profile_sourcing_id > sourcing_id > candidate_id
```

Valores possiveis: `"apply"`, `"sourced_profile_sourcing"`, `"sourcing"`, `"candidate"`, `"unknown"`.

---

## Logica de unicidade

O feedback e unico por `(user_id, candidate_id, sourcing_id, apply_id, sourced_profile_sourcing_id)` considerando apenas registros com `is_deleted: false`.

Ou seja: **um usuario pode ter um like e um dislike para o mesmo candidato em contextos diferentes** (ex: um no funil e outro em um sourcing).

---

## Sugestoes para Vue/Nuxt

> **Importante:** analise os componentes e composables existentes antes de criar qualquer coisa nova. DRY, SOLID e reutilizacao sao prioridade.

### 1. Logica de estado do botao

O `action` retornado pela API e suficiente para saber o que aconteceu sem precisar re-buscar o recurso:

```js
async function submitFeedback(type, context) {
  const { data, meta } = await useApi('/v1/users/candidate_feedbacks', {
    method: 'POST',
    body: { feedback_type: type, ...context }
  })

  if (meta.action === 'removed') {
    currentFeedback.value = null
  } else {
    currentFeedback.value = data.attributes.feedback_type
  }
}
```

### 2. Estado visual dos botoes

Use `is_like` e `is_dislike` que ja vem prontos na resposta para definir qual botao esta ativo. Ao chamar o POST com o mesmo tipo do atual, `action === 'removed'` indica que deve desativar os dois botoes.

### 3. Buscar feedback existente ao carregar

Ao renderizar um card de candidato no funil, consulte o feedback existente para inicializar o estado dos botoes:

```
GET /v1/users/candidate_feedbacks?where={"apply_id":42}
```

### 4. Contexto no funil (kanban / apply)

Ao dar like/dislike em um candidato no funil, envie `apply_id`. O backend preenche `candidate_id` e `job_id` automaticamente.

### 5. Contexto no sourcing

Ao dar like/dislike em um perfil no resultado de sourcing, envie `sourced_profile_sourcing_id`. O backend preenche `sourcing_id` e `candidate_id` automaticamente.
