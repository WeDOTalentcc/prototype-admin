# API: Candidate Match by Text (Vector Similarity)

Endpoint que recebe um texto livre (currículo, job description, ou qualquer descrição de perfil) e retorna candidatos do banco que possuem maior similaridade semântica via pgvector embeddings.

---

## Endpoint

```
POST /v1/users/candidates/match_by_text
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## Request Body

| Campo | Tipo | Obrigatório | Default | Descrição |
|---|---|---|---|---|
| `text` | string | **Sim** | — | Texto livre para match (currículo, job description, perfil ideal, etc.). Mínimo 10 caracteres. |
| `top_k` | integer | Não | 500 | Número máximo de candidatos a considerar no ranking vetorial (1-2000). |
| `page` | integer | Não | 1 | Página atual para paginação. |
| `per_page` | integer | Não | 20 | Itens por página (1-100). |
| `min_score` | float | Não | 0.0 | Score mínimo de similaridade (0.0-1.0). |
| `max_score` | float | Não | 1.0 | Score máximo de similaridade (0.0-1.0). |
| `filters` | object | Não | `{}` | Filtros adicionais aplicados via Elasticsearch (mesmos filtros do `candidates#index`). |
| `includes` | string | Não | — | Campos adicionais separados por vírgula. Valores: `"applies"`. |

### Exemplos de Request

#### Match por Job Description

```json
{
  "text": "Buscamos um desenvolvedor Ruby on Rails sênior com experiência em PostgreSQL, Elasticsearch e microsserviços. Conhecimento em Docker, CI/CD e testes automatizados é essencial. Experiência com sistemas de pagamento é diferencial.",
  "per_page": 10,
  "min_score": 0.3
}
```

#### Match por Currículo

```json
{
  "text": "João Silva | Senior Ruby Developer | São Paulo, SP\n\nExperiência:\n- PagSeguro (2019-2024): Desenvolvimento de APIs REST em Ruby on Rails, otimização de queries PostgreSQL, microsserviços com Sidekiq e Redis.\n- CI&T (2017-2019): Full-stack Rails + React, TDD com RSpec.\n\nSkills: Ruby on Rails, PostgreSQL, Redis, Docker, Kubernetes, TDD, RSpec, Elasticsearch\n\nFormação: Ciência da Computação - USP",
  "top_k": 200,
  "per_page": 20,
  "min_score": 0.2
}
```

#### Match com Filtros

```json
{
  "text": "Engenheiro de dados com Python, Spark, Airflow e experiência em cloud AWS",
  "per_page": 15,
  "min_score": 0.25,
  "filters": {
    "city": "São Paulo",
    "remote_work": true
  }
}
```

---

## Response (JSON:API)

A resposta segue o mesmo padrão do `candidates#index`, formato JSON:API com `data` + `meta`. Cada candidato inclui um campo `score` representando a similaridade vetorial (0.0 a 1.0).

### Sucesso (200 OK)

```json
{
  "data": [
    {
      "id": "1234",
      "type": "candidate_match",
      "attributes": {
        "id": 1234,
        "uid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "João Silva",
        "email": "joao@email.com",
        "mobile_phone": "(11) 99999-0000",
        "linkedin": "https://linkedin.com/in/joaosilva",
        "github": "https://github.com/joaosilva",
        "portfolio": null,
        "current_company": "PagSeguro",
        "role_name": "Senior Ruby Developer",
        "position_level": "senior",
        "self_introduction": "Desenvolvedor Ruby on Rails com 7 anos de experiência...",
        "curriculum_text": "Texto completo do currículo...",
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "remote_work": true,
        "mobility": false,
        "interests": "Backend, API Design, Distributed Systems",
        "source": "linkedin",
        "score": 0.847,
        "avatar_url": "https://...",
        "curriculum_pdf_url": "https://...",
        "url": "/user/candidates/1234",
        "pin": false,
        "confidential": false,
        "favorite": true,
        "gender_name": "Masculino",
        "marital_status_name": null,
        "clt_expectation": 18000.0,
        "pj_expectation": 22000.0,
        "freelance_expectation": null,
        "current_salary": 16000.0,
        "desired_salary": 20000.0,
        "currency": "BRL",
        "completed_register": true,
        "created_at": "2024-03-15T10:30:00.000Z",
        "updated_at": "2025-12-01T14:22:00.000Z"
      }
    },
    {
      "id": "5678",
      "type": "candidate_match",
      "attributes": {
        "name": "Maria Oliveira",
        "role_name": "Full Stack Developer",
        "score": 0.723,
        "...": "..."
      }
    }
  ],
  "meta": {
    "total": 85,
    "page": 1,
    "per_page": 10,
    "total_pages": 9,
    "min_score": 0.3,
    "max_score": 1.0,
    "aggregators": {}
  }
}
```

### Com `includes=applies`

```json
{
  "text": "Ruby on Rails Senior Developer",
  "includes": "applies",
  "per_page": 5
}
```

Resposta inclui o campo `applies` em cada candidato:

```json
{
  "data": [
    {
      "id": "1234",
      "type": "candidate_match",
      "attributes": {
        "name": "João Silva",
        "score": 0.847,
        "applies": [
          {
            "id": 456,
            "job_id": 789,
            "job_title": "Desenvolvedor Ruby Senior",
            "selective_process_id": 12,
            "is_deleted": false,
            "created_at": "2025-06-10T08:00:00.000Z",
            "updated_at": "2025-06-15T14:30:00.000Z"
          }
        ],
        "...": "..."
      }
    }
  ]
}
```

---

## Respostas de Erro

### Texto ausente (400)

```json
{
  "errors": ["text is required"]
}
```

### Texto curto demais (422)

```json
{
  "errors": ["Text too short (minimum 10 characters)"]
}
```

### Falha na geração do embedding (422)

```json
{
  "errors": ["Failed to generate embedding"]
}
```

### Token inválido/ausente (401)

```json
{
  "errors": ["Token inválido ou expirado"]
}
```

---

## Campo `score`

O `score` representa a **similaridade de cosseno** entre o embedding do texto enviado e o embedding do candidato armazenado no banco.

| Faixa | Interpretação |
|---|---|
| 0.80 - 1.00 | Muito alta similaridade — match forte |
| 0.60 - 0.79 | Alta similaridade — candidato relevante |
| 0.40 - 0.59 | Média similaridade — possível match parcial |
| 0.20 - 0.39 | Baixa similaridade — pouca aderência |
| 0.00 - 0.19 | Sem similaridade significativa |

**Fórmula:** `score = 1 - cosine_distance(embedding_texto, embedding_candidato)`

Os candidatos são retornados **ordenados por score decrescente** (mais similar primeiro).

---

## Como Funciona Internamente

```
POST /candidates/match_by_text { text: "..." }
    │
    ▼
CandidateMatchesController#search
    │ Valida text presente
    │
    ▼
Matching::CandidateForText.new(text:, account_id:, ...).call
    │
    ├── 1. Gera embedding do texto via Embeddings::Encoder
    │      (Gemini gemini-embedding-001, 768 dimensões)
    │
    ├── 2. Busca nearest neighbors via pgvector
    │      Embedding.for_candidates.nearest_neighbors(:embedding, vec, distance: "cosine")
    │
    ├── 3. Filtra por account_id e is_deleted: false
    │
    ├── 4. Aplica min_score / max_score
    │
    ├── 5. Pagina os resultados
    │
    ├── 6. Busca via Elasticsearch (Searchkick) com IDs paginados
    │      mantendo a ordenação por score vetorial
    │
    └── 7. Retorna records + meta
             │
             ▼
    CandidateMatchSerializer (JSON:API)
    Resposta com data[] + meta{}
```

---

## Parâmetros de Filtro (`filters`)

Os filtros são aplicados via Elasticsearch sobre os candidatos já ranqueados por similaridade vetorial. Suportam os mesmos campos do `candidates#index`:

| Filtro | Tipo | Exemplo |
|---|---|---|
| `city` | string | `"São Paulo"` |
| `state` | string | `"SP"` |
| `country` | string | `"Brasil"` |
| `remote_work` | boolean | `true` |
| `position_level` | string | `"senior"` |
| `source` | string | `"linkedin"` |
| `role_name` | string | `"Developer"` |
| `is_deleted` | boolean | `false` (default) |

---

## Diferenças em Relação ao `candidates#index`

| Aspecto | `candidates#index` | `candidates/match_by_text` |
|---|---|---|
| **Motor de busca** | Elasticsearch (full-text + filtros) | pgvector (similaridade vetorial) + Elasticsearch |
| **Input** | `search` (keywords), `where` (filtros) | `text` (texto livre) |
| **Ordenação** | Por relevância ES ou campo especificado | Por `score` (similaridade de cosseno) |
| **Campo extra** | — | `score` (0.0-1.0) |
| **Tipo no JSON:API** | `candidate` | `candidate_match` |
| **Use case** | Busca por keywords/filtros estruturados | Match semântico por descrição de perfil, currículo ou JD |

---

## Diferenças em Relação ao `jobs/:id/matching_candidates`

| Aspecto | `matching_candidates` | `match_by_text` |
|---|---|---|
| **Input** | `job_id` (usa título + descrição da vaga) | `text` (texto livre) |
| **Vínculo** | Precisa de uma vaga existente | Independente de vaga |
| **Embedding** | Gera do texto da vaga no momento | Gera do texto enviado no momento |
| **Use case** | "Quais candidatos combinam com esta vaga?" | "Quais candidatos combinam com este texto?" |

---

## Dicas de Uso para o Frontend

### Busca por Job Description

Ideal para quando o recrutador cola uma descrição de vaga externa (de outro site, email, etc.) e quer encontrar candidatos internos que combinam.

### Busca por Currículo

Ideal para "encontrar candidatos similares". O recrutador cola o currículo de um candidato referência e o sistema encontra perfis similares no banco.

### Busca por Perfil Ideal

O recrutador descreve em texto livre o perfil ideal: "Preciso de alguém com 5 anos de Python, experiência em machine learning, preferencialmente com background em fintech".

### Ajuste de `min_score`

Valores recomendados de `min_score` por cenário:

| Cenário | `min_score` sugerido |
|---|---|
| Busca ampla (exploratória) | `0.1` - `0.2` |
| Busca qualificada | `0.3` - `0.4` |
| Match preciso | `0.5` - `0.6` |
| Apenas muito similares | `0.7+` |

### Paginação

```javascript
// Primeira página
const res = await api.post('/v1/users/candidates/match_by_text', {
  text: jobDescription,
  page: 1,
  per_page: 20,
  min_score: 0.3
})

const { total, total_pages, page } = res.data.meta

// Próxima página
const nextPage = await api.post('/v1/users/candidates/match_by_text', {
  text: jobDescription,
  page: page + 1,
  per_page: 20,
  min_score: 0.3
})
```

---

## Limitações

- Apenas candidatos com embedding gerado são retornados. Candidatos sem embedding (recém-criados, sem currículo) não aparecem.
- O embedding é gerado em tempo real para o texto enviado — requests com textos muito longos (>8000 chars) terão o texto truncado.
- O `top_k` máximo é 2000 — para bases muito grandes, candidatos além desse limite não são considerados.
- O endpoint faz uma chamada ao Gemini API para gerar o embedding do texto — latência típica de 200-500ms.
