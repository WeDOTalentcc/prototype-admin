# API Lists & List Relationships — Referência Completa

> Todas as rotas autenticadas requerem header `Authorization: Bearer <JWT_TOKEN>`

---

## Sumário

- [1. CRUD de Lists](#1-crud-de-lists)
- [2. List Relationships — CRUD](#2-list-relationships--crud)
- [3. List Relationships — Listagem por Tipo](#3-list-relationships--listagem-por-tipo)
- [4. List Relationships — Operações em Lote](#4-list-relationships--operações-em-lote)
- [5. List Relationships — Ordenação](#5-list-relationships--ordenação)
- [6. Adicionar Candidatos de uma Lista a uma Vaga](#6-adicionar-candidatos-de-uma-lista-a-uma-vaga)
- [7. Guia Prático — Fluxo Completo](#7-guia-prático--fluxo-completo)

---

## 1. CRUD de Lists

### `GET /v1/users/lists` — Listar Listas

Retorna as listas do tenant do usuário autenticado. Usa Searchkick com filtros e paginação.

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `search` | string | Busca full-text pelo nome da lista (default: `"*"`) |
| `page` | integer | Página (default: 1) |
| `per_page` | integer | Itens por página (max: 30) |
| `where[is_public]` | boolean | Filtrar listas públicas/privadas |
| `where[user_id]` | integer | Filtrar por criador |
| `order[field]` | string | Campo para ordenação |
| `order[direction]` | string | `asc` ou `desc` |

> O filtro `account_id` e `is_deleted: false` é aplicado automaticamente.

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "10",
      "type": "list",
      "attributes": {
        "id": 10,
        "name": "Candidatos Backend Senior",
        "is_public": true,
        "user_id": 1,
        "account_id": 1,
        "candidates_count": 25,
        "jobs_count": 0,
        "applies_count": 0,
        "selective_processes_count": 0,
        "color": "#3498db",
        "description": "Lista de candidatos selecionados para vagas backend senior",
        "created_at": "2026-01-10T08:00:00.000Z",
        "updated_at": "2026-03-01T14:30:00.000Z",
        "user_name": "Maria Recrutadora",
        "user_email": "maria@empresa.com"
      }
    }
  ],
  "meta": {
    "total": 8
  }
}
```

---

### `GET /v1/users/lists/:id` — Detalhe da Lista

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da lista |

**Response (200 — JSON:API):** Mesmo formato de um item da listagem.

**Response (404):**

```json
{
  "error": "List not found"
}
```

---

### `POST /v1/users/lists` — Criar Lista

**Body:**

```json
{
  "list": {
    "name": "Candidatos Backend Senior",
    "is_public": true,
    "color": "#3498db",
    "description": "Lista de candidatos selecionados para vagas backend senior"
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | string | Sim | Nome da lista |
| `is_public` | boolean | Não | Se a lista é visível para todos do tenant (default: false) |
| `color` | string | Não | Cor da lista em hex (ex: `"#3498db"`) |
| `description` | string | Não | Descrição da lista |

> Os campos `user_id` e `account_id` são preenchidos automaticamente com o usuário autenticado.

**Response (201 — JSON:API):**

```json
{
  "data": {
    "id": "10",
    "type": "list",
    "attributes": {
      "id": 10,
      "name": "Candidatos Backend Senior",
      "is_public": true,
      "user_id": 1,
      "account_id": 1,
      "candidates_count": 0,
      "jobs_count": 0,
      "applies_count": 0,
      "selective_processes_count": 0,
      "color": "#3498db",
      "description": "Lista de candidatos selecionados para vagas backend senior",
      "created_at": "2026-03-18T10:00:00.000Z",
      "updated_at": "2026-03-18T10:00:00.000Z",
      "user_name": "Maria Recrutadora",
      "user_email": "maria@empresa.com"
    }
  }
}
```

**Response (422):**

```json
{
  "errors": { "name": ["can't be blank"] }
}
```

---

### `PUT /v1/users/lists/:id` — Atualizar Lista

**Body:**

```json
{
  "list": {
    "name": "Candidatos Backend Senior - Atualizado",
    "color": "#e74c3c"
  }
}
```

Campos permitidos: `name`, `is_public`, `color`, `description`.

**Response (200 — JSON:API):** Lista atualizada serializada.

---

### `DELETE /v1/users/lists/:id` — Deletar Lista (soft-delete)

Marca `is_deleted: true`. Não remove fisicamente.

**Response (200 — JSON:API):** Lista com `is_deleted: true`.

---

## 2. List Relationships — CRUD

Lista de relacionamentos entre uma lista e entidades (Candidate, Job, Apply, SourcedProfileSourcing, etc.).

### `GET /v1/users/lists/:id/relationships/:relationship_id` — Detalhe do Relacionamento

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da lista |
| `relationship_id` | integer | Sim | ID do relacionamento |

**Response (200 — JSON:API):**

```json
{
  "data": {
    "id": "50",
    "type": "list_relationship",
    "attributes": {
      "id": 50,
      "list_id": 10,
      "reference_type": "Candidate",
      "reference_id": 456,
      "position": 1,
      "general_comments": "Perfil excelente para vaga de backend",
      "score": 85.5,
      "account_id": 1,
      "created_at": "2026-03-18T10:00:00.000Z",
      "updated_at": "2026-03-18T10:00:00.000Z",
      "list_name": "Candidatos Backend Senior",
      "name": "João Silva",
      "email": "joao@email.com",
      "city": "São Paulo",
      "role_name": "Desenvolvedor Backend"
    }
  }
}
```

> Os atributos da entidade referenciada (Candidate, Job, etc.) são mesclados automaticamente na resposta pelo serializer. Os campos extras dependem do `reference_type`.

---

### `POST /v1/users/lists/:id/relationships` — Adicionar Item à Lista

Cria um relacionamento entre a lista e uma entidade.

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da lista |

**Body:**

```json
{
  "list_relationship": {
    "reference_type": "Candidate",
    "reference_id": 456,
    "general_comments": "Perfil excelente para vaga de backend",
    "score": 85.5
  }
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `reference_type` | string | Sim | Tipo da entidade: `"Candidate"`, `"Job"`, `"Apply"`, `"SourcedProfileSourcing"`, `"SelectiveProcess"` |
| `reference_id` | integer | Sim | ID da entidade referenciada |
| `general_comments` | string | Não | Comentários livres sobre o item na lista |
| `score` | float | Não | Score/nota atribuído ao item |
| `position` | integer | Não | Posição na lista (preenchido automaticamente se omitido) |

> `list_id` e `account_id` são preenchidos automaticamente. A `position` é calculada como última posição + 1.

**Response (201 — JSON:API):**

```json
{
  "data": {
    "id": "50",
    "type": "list_relationship",
    "attributes": {
      "id": 50,
      "list_id": 10,
      "reference_type": "Candidate",
      "reference_id": 456,
      "position": 1,
      "general_comments": "Perfil excelente para vaga de backend",
      "score": 85.5,
      "account_id": 1,
      "created_at": "2026-03-18T10:00:00.000Z",
      "updated_at": "2026-03-18T10:00:00.000Z",
      "list_name": "Candidatos Backend Senior",
      "name": "João Silva",
      "email": "joao@email.com"
    }
  }
}
```

**Response (422 — Duplicata):**

```json
{
  "errors": { "base": ["This relationship already exists in the list"] }
}
```

---

### `PUT /v1/users/lists/:id/relationships/:relationship_id` — Atualizar Relacionamento

**Body:**

```json
{
  "list_relationship": {
    "general_comments": "Comentário atualizado",
    "score": 90.0,
    "position": 3
  }
}
```

Campos atualizáveis: `reference_type`, `reference_id`, `general_comments`, `score`, `position`.

> `list_id` e `account_id` não podem ser alterados.

**Response (200 — JSON:API):** Relacionamento atualizado.

---

### `DELETE /v1/users/lists/:id/relationships/:relationship_id` — Remover Item da Lista

Soft-delete (`is_deleted: true`). Atualiza os contadores da lista automaticamente.

**Response (200):**

```json
{
  "data": {
    "message": "List relationship removed successfully"
  }
}
```

---

## 3. List Relationships — Listagem por Tipo

### `GET /v1/users/lists/:id/relationships/:reference_type` — Listar Itens via Redirect

Redireciona para o endpoint de busca da entidade (`/v1/users/candidates`, `/v1/users/jobs`, etc.) com filtro `list_ids` aplicado.

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da lista |
| `reference_type` | string | Sim | Tipo da entidade: `Candidate`, `Job`, `Apply`, etc. |

**Query Params:**

| Param | Tipo | Descrição |
|---|---|---|
| `search` | string | Busca full-text |
| `page` | integer | Página |
| `where` | JSON | Filtros adicionais |
| `order` | JSON | Ordenação |
| `filter` | JSON | Filtros alternativos |

**Comportamento:** Faz um redirect interno para `/v1/users/{reference_type_plural}?where[list_ids]={list_id}&extra_params=list_relationships(...)`. O resultado é a listagem padrão da entidade com os dados de list_relationship embutidos.

**Response (200 — JSON:API):** Formato da entidade referenciada (ex: CandidateSerializer se `reference_type=Candidate`).

---

### `GET /v1/users/lists/:id/relationships_by_reference/:reference_type` — Listar via ListRelationship

Retorna os ListRelationships diretamente (sem redirect), filtrados por tipo de referência.

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da lista |
| `reference_type` | string | Sim | Tipo da entidade |

**Query Params:** Mesmos do Searchkick padrão (`search`, `page`, `per_page`, `where`, `order`).

**Response (200 — JSON:API):**

```json
{
  "data": [
    {
      "id": "50",
      "type": "list_relationship",
      "attributes": {
        "id": 50,
        "list_id": 10,
        "reference_type": "Candidate",
        "reference_id": 456,
        "position": 1,
        "general_comments": "Perfil excelente",
        "score": 85.5,
        "account_id": 1,
        "created_at": "2026-03-18T10:00:00.000Z",
        "updated_at": "2026-03-18T10:00:00.000Z",
        "list_name": "Candidatos Backend Senior",
        "name": "João Silva",
        "email": "joao@email.com",
        "city": "São Paulo",
        "role_name": "Desenvolvedor Backend"
      }
    }
  ],
  "meta": {
    "total": 25
  }
}
```

---

## 4. List Relationships — Operações em Lote

### `POST /v1/users/lists/:id/relationships/collection` — Adicionar em Lote

Adiciona múltiplos itens à lista de forma assíncrona (background job).

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da lista |

#### Formato 1: Via lista explícita de referências

```json
{
  "list_collection": {
    "collections": [
      { "reference_type": "Candidate", "reference_id": 100, "general_comments": "Bom perfil" },
      { "reference_type": "Candidate", "reference_id": 101 },
      { "reference_type": "Candidate", "reference_id": 102, "general_comments": "Destaque técnico" }
    ]
  }
}
```

| Campo (`collections[]`) | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `reference_type` | string | Sim | `"Candidate"`, `"Job"`, `"Apply"`, `"SourcedProfileSourcing"` |
| `reference_id` | integer | Sim | ID da entidade |
| `general_comments` | string | Não | Comentário por item |

#### Formato 2: Via `select_all_params` (busca)

Seleciona itens via busca Searchkick e adiciona todos à lista.

```json
{
  "list_collection": {
    "select_all_params": {
      "reference_type": "Candidate",
      "search": "*",
      "where": { "city": "São Paulo", "is_deleted": false },
      "page": 1,
      "per_page": 30
    }
  }
}
```

| Campo (`select_all_params`) | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `reference_type` | string | Sim | Tipo da entidade a buscar |
| `search` | string | Não | Termo de busca |
| `where` | object | Não | Filtros Searchkick |

> **Conversão automática:** Se `reference_type` for `"Apply"`, o sistema converte para `"Candidate"` usando o `candidate_id` do apply. Se for `"SourcedProfileSourcing"`, converte para `"Candidate"` criando/buscando o candidato correspondente.

**Response (200):**

```json
{
  "data": {
    "status": "processing"
  }
}
```

---

### `DELETE /v1/users/lists/:id/relationships/delete_collection` — Remover em Lote

Remove múltiplos itens da lista de forma assíncrona.

#### Formato 1: Via lista explícita

```json
{
  "list_collection": {
    "collections": [
      { "reference_type": "Candidate", "reference_id": 100 },
      { "reference_type": "Candidate", "reference_id": 101 }
    ]
  }
}
```

#### Formato 2: Via `select_all_params`

```json
{
  "list_collection": {
    "select_all_params": {
      "reference_type": "Candidate",
      "where": { "city": "Rio de Janeiro" }
    }
  }
}
```

**Response (200):**

```json
{
  "data": {
    "status": "processing"
  }
}
```

---

## 5. List Relationships — Ordenação

### `POST /v1/users/lists/:id/relationships/sort` — Reordenar Itens

Atualiza a posição dos itens na lista.

**Body:**

```json
{
  "list_relationships": [
    { "id": 50, "position": 0 },
    { "id": 51, "position": 1 },
    { "id": 52, "position": 2 }
  ]
}
```

**Response (200):**

```json
{
  "data": {
    "message": "List relationships sorted successfully"
  }
}
```

---

## 6. Adicionar Candidatos de uma Lista a uma Vaga

### `POST /v1/users/jobs/:id/add_candidates_from_list` — Criar Applies a partir de Lista

Pega todos os candidatos de uma lista e cria applies (candidaturas) para a vaga especificada. Executa em background.

**Path Params:**

| Param | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | integer | Sim | ID da vaga (job) |

**Body:**

```json
{
  "list_id": 10,
  "selective_process_id": 25
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `list_id` | integer | Sim | ID da lista de candidatos |
| `selective_process_id` | integer | Sim | ID da etapa do processo seletivo onde os candidatos entrarão |

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

**Response (400):**

```json
{
  "error": "list_id is required"
}
```

```json
{
  "error": "selective_process_id is required"
}
```

**Response (404):**

```json
{
  "error": "List not found"
}
```

---

## 7. Guia Prático — Fluxo Completo

Passo a passo de como criar uma lista, adicionar candidatos e enviar para uma vaga.

### Passo 1: Criar a lista

```
POST /v1/users/lists

{
  "list": {
    "name": "Shortlist Backend Senior - Q1 2026",
    "is_public": true,
    "color": "#2196F3",
    "description": "Candidatos pré-selecionados para vagas de backend senior"
  }
}
```

**Resposta:** `id: 10` (guardar para usar nos próximos passos)

---

### Passo 2: Adicionar candidatos individualmente

```
POST /v1/users/lists/10/relationships

{
  "list_relationship": {
    "reference_type": "Candidate",
    "reference_id": 456,
    "general_comments": "10 anos de experiência com Ruby",
    "score": 92.0
  }
}
```

---

### Passo 3: Adicionar candidatos em lote (lista explícita)

```
POST /v1/users/lists/10/relationships/collection

{
  "list_collection": {
    "collections": [
      { "reference_type": "Candidate", "reference_id": 100, "general_comments": "Destaque técnico" },
      { "reference_type": "Candidate", "reference_id": 101 },
      { "reference_type": "Candidate", "reference_id": 102 },
      { "reference_type": "Candidate", "reference_id": 103 }
    ]
  }
}
```

---

### Passo 4: Adicionar candidatos em lote via busca

```
POST /v1/users/lists/10/relationships/collection

{
  "list_collection": {
    "select_all_params": {
      "reference_type": "Candidate",
      "search": "ruby rails",
      "where": {
        "city": "São Paulo",
        "is_deleted": false
      }
    }
  }
}
```

---

### Passo 5: Ver os candidatos da lista

```
GET /v1/users/lists/10/relationships/Candidate?page=1&per_page=30
```

Ou para ver como ListRelationship (com score e comments):

```
GET /v1/users/lists/10/relationships_by_reference/Candidate?page=1&per_page=30
```

---

### Passo 6: Enviar candidatos da lista para uma vaga

```
POST /v1/users/jobs/789/add_candidates_from_list

{
  "list_id": 10,
  "selective_process_id": 25
}
```

Isso cria automaticamente um Apply para cada candidato da lista na vaga 789, na etapa 25 (ex: "Triagem").

---

### Passo 7 (opcional): Reordenar candidatos na lista

```
POST /v1/users/lists/10/relationships/sort

{
  "list_relationships": [
    { "id": 50, "position": 0 },
    { "id": 52, "position": 1 },
    { "id": 51, "position": 2 }
  ]
}
```

---

### Passo 8 (opcional): Remover candidatos da lista

Individualmente:

```
DELETE /v1/users/lists/10/relationships/50
```

Em lote:

```
DELETE /v1/users/lists/10/relationships/delete_collection

{
  "list_collection": {
    "collections": [
      { "reference_type": "Candidate", "reference_id": 101 },
      { "reference_type": "Candidate", "reference_id": 102 }
    ]
  }
}
```

---

## Referência de `reference_type`

| Valor | Descrição | Conversão automática |
|---|---|---|
| `Candidate` | Candidato direto | — |
| `Job` | Vaga | — |
| `Apply` | Candidatura | Converte para `Candidate` via `apply.candidate_id` |
| `SourcedProfileSourcing` | Perfil de sourcing | Converte para `Candidate` (cria candidato se não existir) |
| `SelectiveProcess` | Etapa do processo seletivo | — |

---

## Contadores da Lista

Ao criar, atualizar ou remover relacionamentos, os contadores da lista são recalculados automaticamente:

| Campo | Descrição |
|---|---|
| `candidates_count` | Total de Candidates + SourcedProfileSourcings ativos |
| `jobs_count` | Total de Jobs ativos |
| `applies_count` | Total de Applies ativos |
| `selective_processes_count` | Total de SelectiveProcesses ativos |

---

## Validações

- **Duplicata:** Não é possível adicionar o mesmo item duas vezes na mesma lista (`reference_type` + `reference_id` + `list_id` únicos entre ativos).
- **Campos obrigatórios:** `reference_type`, `reference_id`, `list_id`, `account_id` (últimos dois preenchidos automaticamente).
- **Autorização (Pundit):** Apenas usuários do mesmo tenant podem acessar/modificar listas e relacionamentos.
