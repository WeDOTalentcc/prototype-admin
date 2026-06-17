# Background Agent — Python Integration Prompt

## Contexto

O backend Rails do ATS publica mensagens no RabbitMQ quando um Background Agent precisa executar um ciclo de busca. O projeto Python (recruiter_agent) precisa consumir essas mensagens, autenticar-se no Rails via token efêmero (OTT), executar buscas nos providers (Pearch, LinkedIn/Apify, Local) e reportar resultados de volta ao Rails via HTTP.

---

## 1. Fluxo Completo de Comunicação

```
Rails (Sidekiq CronJob)
  │
  ├── BackgroundAgents::PublishToAgentService
  │     ├── Cria AgentCycle + Sourcing
  │     ├── Gera OTT (one-time token, TTL 600s)
  │     └── Publica no RabbitMQ
  │
  ▼
RabbitMQ
  exchange: "background_agents"
  routing_key: "background_agents.search"
  queue: (Python deve criar/bind)
  │
  ▼
Python Agent (Consumer)
  │
  ├── 1. Recebe mensagem
  ├── 2. Troca OTT por service token (POST /v1/agent_tokens/exchange)
  ├── 3. Usa service token em todas as requests subsequentes
  ├── 4. Executa buscas nos providers
  └── 5. Reporta resultados de volta ao Rails
        ├── POST  deliver_cycle
        ├── PATCH update_status
        ├── PATCH update_preferences
        └── POST  log_search_iteration
```

---

## 2. Payload da Mensagem RabbitMQ

O Rails publica essa estrutura JSON:

```json
{
  "operation": "execute_intelligent_search",
  "background_agent_id": 123,
  "cycle_id": 456,
  "sourcing_id": 789,
  "account_id": 1,
  "user_id": 42,
  "auth": {
    "one_time_token": "<jwt_ott>",
    "exchange_url": "http://localhost:3000/v1/agent_tokens/exchange",
    "api_base_url": "http://localhost:3000"
  },
  "context": {
    "agent": {
      "id": 123,
      "name": "Backend Senior",
      "criteria_text": "Senior Ruby developer with Rails experience...",
      "criteria_structured": { "skills": ["ruby", "rails"], "seniority": "senior" },
      "calibration_state": "calibrated",
      "mode": "review",
      "sources": ["local", "linkedin", "global"],
      "min_score_threshold": 70,
      "extracted_preferences": {
        "preferred_skills": ["ruby", "rails", "postgresql"],
        "preferred_titles": ["senior software engineer"],
        "avoid_patterns": ["no remote experience"]
      },
      "diversity_queries": [],
      "remaining_today": 8,
      "total_delivered": 45,
      "total_approved": 30,
      "total_rejected": 15,
      "approval_rate": 66.7
    },
    "job": {
      "id": 10,
      "title": "Senior Backend Developer",
      "description": "We are looking for...",
      "city": "São Paulo",
      "state": "SP",
      "country": "Brazil",
      "seniority": 3,
      "skills": ["Ruby", "Rails", "PostgreSQL"],
      "has_embedding": true
    },
    "feedback_history": {
      "recent": [
        {
          "action": "approved",
          "reason": null,
          "score": 85,
          "profile_name": "João Silva",
          "profile_title": "Senior Ruby Developer"
        },
        {
          "action": "rejected",
          "reason": "no_remote_experience",
          "score": 60,
          "profile_name": "Maria Santos",
          "profile_title": "Junior Developer"
        }
      ],
      "summary": {
        "total_approved": 30,
        "total_rejected": 15,
        "approval_rate": 66.7
      }
    },
    "search_history": [
      {
        "iteration_number": 1,
        "query_used": "senior ruby developer",
        "results_count": 25,
        "selected_count": 8,
        "strategy": "initial"
      }
    ],
    "search_config": {}
  }
}
```

---

## 3. Autenticação — OTT → Service Token

### Passo 1: Trocar OTT por Service Token

**IMPORTANTE:** O OTT só pode ser usado UMA VEZ. Após o exchange, ele é invalidado.

```
POST {api_base_url}/v1/agent_tokens/exchange
Content-Type: application/json

{
  "one_time_token": "<jwt_ott>"
}
```

**Resposta (200 OK):**
```json
{
  "access_token": "<service_jwt>",
  "token_type": "Bearer",
  "expires_in": 300,
  "user_id": 42
}
```

**Erros possíveis:**
- `401` — Token inválido, expirado, ou já usado
- `409` — Token já consumido (replay attack)

### Passo 2: Usar Service Token em todas as requests

```
Authorization: Bearer <service_jwt>
```

O service token tem TTL de 5 minutos. Se o ciclo demorar mais, o Python deve fazer o exchange no início e trabalhar rápido. Se precisar de mais tempo, considere pedir um novo OTT (não suportado atualmente — o ciclo deve completar em 5 min).

---

## 4. Endpoints Rails — Todos em `/v1/users/background_agents`

**ATENÇÃO:** Todas as rotas do agent estão dentro do namespace `/v1/users/`. O service token é aceito pelo mesmo `authorize_request` que autentica usuários. Actions específicas do agent são protegidas por `require_service_token` (retorna 403 se chamadas com token de usuário comum).

### 4.1 GET /v1/users/background_agents/runnable

Lista agents prontos para execução. Usado pelo scheduler/orquestrador (não pelo consumer individual).

**Headers:** `Authorization: Bearer <service_token>`

**Resposta (200):**
```json
[
  {
    "id": 123,
    "job_id": 10,
    "user_id": 42,
    "account_id": 1,
    "name": "Backend Senior",
    "criteria_text": "...",
    "criteria_structured": {},
    "calibration_state": "calibrated",
    "mode": "review",
    "sources": ["local", "linkedin"],
    "min_score_threshold": 70,
    "remaining_today": 8,
    "search_iteration_config": {},
    "extracted_preferences": {}
  }
]
```

### 4.2 GET /v1/users/background_agents/:id/search_context

Retorna contexto completo para executar busca (agent, job, feedbacks, histórico).

**Headers:** `Authorization: Bearer <service_token>`

**Resposta (200):** Mesma estrutura do campo `context` da mensagem RabbitMQ.

### 4.3 POST /v1/users/background_agents/:id/deliver_cycle

Finaliza um ciclo de busca com resultados.

**Headers:** `Authorization: Bearer <service_token>`

**Body:**
```json
{
  "cycle_id": 456,
  "candidates_count": 8,
  "total_found": 25,
  "metadata": {
    "duration_seconds": 45,
    "providers_used": ["local", "linkedin"],
    "queries_executed": 3
  }
}
```

**Resposta (200):**
```json
{
  "success": true,
  "cycle_id": 456
}
```

### 4.4 PATCH /v1/users/background_agents/:id/update_status

Atualiza status do agent.

**Headers:** `Authorization: Bearer <service_token>`

**Body:**
```json
{
  "status": "active"
}
```

**Valores permitidos:** `active`, `paused`, `stopped`

**Resposta (200):**
```json
{
  "success": true
}
```

### 4.5 PATCH /v1/users/background_agents/:id/update_preferences

Persiste preferências extraídas pela IA (skills preferidas, padrões a evitar, etc).

**Headers:** `Authorization: Bearer <service_token>`

**Body:**
```json
{
  "preferences": {
    "preferred_skills": ["ruby", "rails", "postgresql"],
    "preferred_titles": ["senior software engineer", "staff engineer"],
    "preferred_companies": ["FAANG", "startups"],
    "preferred_locations": ["São Paulo", "Remote"],
    "experience_range": { "min": 5, "max": 15 },
    "avoid_patterns": ["no remote experience", "junior level"]
  }
}
```

**Resposta (200):**
```json
{
  "success": true
}
```

### 4.6 POST /v1/users/background_agents/:id/log_search_iteration

Registra uma iteração de busca no histórico.

**Headers:** `Authorization: Bearer <service_token>`

**Body:**
```json
{
  "iteration_number": 2,
  "query_used": "senior ruby developer são paulo",
  "results_count": 30,
  "selected_count": 12,
  "strategy": "refined_from_feedback"
}
```

**Resposta (200):**
```json
{
  "success": true,
  "history_size": 5
}
```

---

## 5. Endpoints de Busca — Criação de Sourcings

Para executar buscas, o Python agent usa o endpoint de `talent_searches` ou `sourcings`, que também ficam sob `/v1/users/`.

### 5.1 POST /v1/users/talent_searches

Cria uma busca. Suporta 3 fontes: `local`, `global` (Pearch), `linkedin` (Apify).

**Headers:** `Authorization: Bearer <service_token>`

**Body — Busca Local:**
```json
{
  "talent_search": {
    "query": "senior ruby developer",
    "source": "local",
    "job_id": 10
  }
}
```

**Body — Busca Global (Pearch):**
```json
{
  "talent_search": {
    "query": "senior ruby developer",
    "source": "global",
    "job_id": 10,
    "locations": ["São Paulo, Brazil"],
    "skills": ["Ruby", "Rails"],
    "titles": ["Senior Software Engineer"],
    "years_of_experience_min": 5,
    "years_of_experience_max": 15
  }
}
```

**Body — Busca LinkedIn (Apify):**
```json
{
  "talent_search": {
    "query": "senior ruby developer",
    "source": "linkedin",
    "job_id": 10,
    "locations": ["São Paulo"],
    "keywords": "Ruby Rails PostgreSQL",
    "current_companies": ["Company A", "Company B"],
    "past_companies": ["Company C"],
    "schools": ["USP", "Unicamp"],
    "industries": ["Software Development"],
    "seniority_levels": ["Senior", "Manager"],
    "functions": ["Engineering"],
    "company_headcount": ["51-200", "201-500"],
    "profile_languages": ["Portuguese", "English"],
    "exclude_locations": ["Rio de Janeiro"],
    "exclude_current_companies": ["Competitor X"],
    "exclude_past_companies": [],
    "exclude_schools": [],
    "exclude_current_job_titles": ["Intern"],
    "exclude_past_job_titles": [],
    "exclude_industry_ids": [],
    "exclude_seniority_levels": [],
    "exclude_function_ids": [],
    "exclude_company_headquarter_locations": [],
    "recently_changed_jobs": false
  }
}
```

**Respostas:**
- **Local (síncrono):** `200` com resultados imediatos
- **Global (síncrono Pearch):** `200` com resultados
- **LinkedIn (assíncrono):** `202 Accepted` com `sourcing_id` para polling

### 5.2 GET /v1/users/sourcings/:id

Polling do status de uma busca assíncrona (LinkedIn).

**Headers:** `Authorization: Bearer <service_token>`

**Resposta (200):** JSON:API format
```json
{
  "data": {
    "id": "789",
    "type": "sourcing",
    "attributes": {
      "status": "completed",
      "results_count": 25,
      "credits_used": 25,
      "query": "senior ruby developer",
      "provider": "linkedin"
    }
  }
}
```

**Status possíveis:** `processing`, `completed`, `failed`

### 5.3 GET /v1/users/sourced_profile_sourcings?filter[sourcing_id]=789

Lista perfis encontrados por uma busca.

**Headers:** `Authorization: Bearer <service_token>`

**Query Params:**
- `filter[sourcing_id]=789` — filtra por sourcing
- `page=1&per_page=30` — paginação (máx 30)

**Resposta:** JSON:API format com dados completos dos perfis (nome, título, empresa, LinkedIn, skills, score, etc.)

---

## 6. RabbitMQ — Configuração do Consumer Python

### Exchange e Queue

```python
EXCHANGE_NAME = "background_agents"
EXCHANGE_TYPE = "direct"
QUEUE_NAME = "background_agents.search"     # Criar esta queue
ROUTING_KEY = "background_agents.search"
DURABLE = True
```

O Python deve:
1. Declarar a queue `background_agents.search` (durable)
2. Fazer bind ao exchange `background_agents` com routing key `background_agents.search`
3. Consumir com ack manual (processar → ack, falhar → nack/reject)

### Exemplo de Consumer Base

```python
import pika
import json

class BackgroundAgentConsumer:
    def __init__(self, rabbitmq_url: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        self._setup_queue()

    def _setup_queue(self):
        self.channel.exchange_declare(
            exchange="background_agents",
            exchange_type="direct",
            durable=True
        )
        self.channel.queue_declare(
            queue="background_agents.search",
            durable=True
        )
        self.channel.queue_bind(
            queue="background_agents.search",
            exchange="background_agents",
            routing_key="background_agents.search"
        )

    def start_consuming(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue="background_agents.search",
            on_message_callback=self._handle_message
        )
        self.channel.start_consuming()

    def _handle_message(self, channel, method, properties, body):
        try:
            payload = json.loads(body)
            self._process_search(payload)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False
            )

    def _process_search(self, payload: dict):
        # 1. Extrair auth
        auth = payload["auth"]
        api_base_url = auth["api_base_url"]

        # 2. Trocar OTT por service token
        client = RailsApiClient(api_base_url)
        client.exchange_token(auth["one_time_token"])

        # 3. Executar ciclo de busca
        agent_id = payload["background_agent_id"]
        cycle_id = payload["cycle_id"]
        context = payload["context"]

        # 4. Buscar nos providers configurados
        sources = context["agent"]["sources"]
        # ... executar buscas ...

        # 5. Reportar resultados
        client.deliver_cycle(agent_id, cycle_id, results)
```

---

## 7. Rails API Client — Classe Base para Python

```python
import httpx

class RailsApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def exchange_token(self, ott: str) -> dict:
        """Troca OTT por service token. Deve ser chamado PRIMEIRO."""
        response = httpx.post(
            f"{self.base_url}/v1/agent_tokens/exchange",
            json={"one_time_token": ott},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # === Background Agent Endpoints ===

    def get_search_context(self, agent_id: int) -> dict:
        r = httpx.get(
            f"{self.base_url}/v1/users/background_agents/{agent_id}/search_context",
            headers=self._headers,
            timeout=15
        )
        r.raise_for_status()
        return r.json()

    def deliver_cycle(self, agent_id: int, cycle_id: int,
                      candidates_count: int, total_found: int,
                      metadata: dict = None) -> dict:
        r = httpx.post(
            f"{self.base_url}/v1/users/background_agents/{agent_id}/deliver_cycle",
            headers=self._headers,
            json={
                "cycle_id": cycle_id,
                "candidates_count": candidates_count,
                "total_found": total_found,
                "metadata": metadata or {}
            },
            timeout=15
        )
        r.raise_for_status()
        return r.json()

    def update_status(self, agent_id: int, status: str) -> dict:
        r = httpx.patch(
            f"{self.base_url}/v1/users/background_agents/{agent_id}/update_status",
            headers=self._headers,
            json={"status": status},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def update_preferences(self, agent_id: int, preferences: dict) -> dict:
        r = httpx.patch(
            f"{self.base_url}/v1/users/background_agents/{agent_id}/update_preferences",
            headers=self._headers,
            json={"preferences": preferences},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def log_search_iteration(self, agent_id: int, iteration: dict) -> dict:
        r = httpx.post(
            f"{self.base_url}/v1/users/background_agents/{agent_id}/log_search_iteration",
            headers=self._headers,
            json=iteration,
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    # === Search Endpoints ===

    def create_talent_search(self, search_params: dict) -> dict:
        r = httpx.post(
            f"{self.base_url}/v1/users/talent_searches",
            headers=self._headers,
            json={"talent_search": search_params},
            timeout=30
        )
        r.raise_for_status()
        return r.json()

    def get_sourcing(self, sourcing_id: int) -> dict:
        r = httpx.get(
            f"{self.base_url}/v1/users/sourcings/{sourcing_id}",
            headers=self._headers,
            timeout=15
        )
        r.raise_for_status()
        return r.json()

    def get_sourced_profiles(self, sourcing_id: int,
                              page: int = 1, per_page: int = 30) -> dict:
        r = httpx.get(
            f"{self.base_url}/v1/users/sourced_profile_sourcings",
            headers=self._headers,
            params={
                "filter[sourcing_id]": sourcing_id,
                "page": page,
                "per_page": per_page
            },
            timeout=15
        )
        r.raise_for_status()
        return r.json()
```

---

## 8. Fluxo Completo do Ciclo de Busca (Python)

```
_process_search(payload):
│
├── 1. exchange_token(payload.auth.one_time_token)
│      → agora tem service_token (5 min TTL)
│
├── 2. Ler context do payload (já vem na mensagem)
│      agent = payload.context.agent
│      job = payload.context.job
│      sources = agent.sources  # ["local", "linkedin", "global"]
│
├── 3. Para cada source:
│      ├── "local" → create_talent_search(source="local", query=...)
│      │              → resposta síncrona com resultados
│      │
│      ├── "global" → create_talent_search(source="global", query=..., locations=...)
│      │              → resposta síncrona (Pearch)
│      │
│      └── "linkedin" → create_talent_search(source="linkedin", query=..., filters=...)
│                       → 202 Accepted, sourcing_id
│                       → poll get_sourcing(sourcing_id) até status != "processing"
│                       → get_sourced_profiles(sourcing_id)
│
├── 4. Agregar resultados de todos os sources
│
├── 5. Aplicar scoring/ranking com LLM
│
├── 6. log_search_iteration(agent_id, {
│        iteration_number, query_used,
│        results_count, selected_count, strategy
│      })
│
├── 7. Se calibration_state == "calibrated" e tem extracted_preferences:
│      → update_preferences(agent_id, novas_preferencias)
│
└── 8. deliver_cycle(agent_id, cycle_id,
         candidates_count, total_found, metadata)
```

---

## 9. Respostas JSON:API vs Flat JSON

**ATENÇÃO:** Os endpoints de background_agents (runnable, search_context, deliver_cycle, etc.) retornam **flat JSON** simples.

Os endpoints de sourcings e sourced_profile_sourcings retornam **JSON:API format**:

```json
{
  "data": {
    "id": "789",
    "type": "sourcing",
    "attributes": {
      "status": "completed",
      ...
    }
  }
}
```

O Python precisa parsear respostas JSON:API corretamente:
- `response["data"]["attributes"]["status"]` para acessar campos
- `response["data"]["id"]` para IDs
- Arrays: `response["data"]` é lista de objetos

---

## 10. Variáveis de Ambiente do Python

```env
# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# Não precisa de API_BASE_URL fixo — vem na mensagem RabbitMQ (auth.api_base_url)

# LLM (para scoring/ranking)
GEMINI_API_KEY=...

# Logging
LOG_LEVEL=INFO
```

---

## 11. Tratamento de Erros

### Token expirado durante o ciclo
O service token tem TTL de 5 minutos. Se o ciclo demorar mais:
- O Python receberá `401 Unauthorized`
- Não há como renovar (OTT é single-use)
- O ciclo deve ser marcado como falho
- O próximo CronJob gerará novo OTT

### Sourcing assíncrono (LinkedIn) — Timeout
- Poll máximo: 120 segundos
- Intervalo: 3-5 segundos entre polls
- Se timeout: continuar com resultados parciais ou falhar gracefully

### RabbitMQ — Mensagem não processada
- `basic_nack(requeue=False)` — não reprocessar (OTT já foi consumido ou expirou)
- Logar erro e seguir em frente
- O CronJob enviará nova mensagem no próximo ciclo

---

## 12. Resumo de Mudanças Recentes no Rails

1. **Namespace unificado:** Todas as rotas estão em `/v1/users/background_agents/`. Não existe mais `/v1/services/`.

2. **OTT na mensagem RabbitMQ:** O `PublishToAgentService` agora inclui bloco `auth` com `one_time_token`, `exchange_url` e `api_base_url`.

3. **Guard de service token:** As actions do agent (`runnable`, `search_context`, `deliver_cycle`, `update_preferences`, `update_status`, `log_search_iteration`) exigem `role: "service"` no JWT. Usuários comuns recebem 403.

4. **Filtros avançados LinkedIn:** O `JobEnqueuerService` agora passa 30+ parâmetros de filtro para Apify (seniority_levels, functions, company_headcount, exclude_*, etc).

5. **TalentSearches com rota:** O controller agora tem rota registrada em `/v1/users/talent_searches`.
