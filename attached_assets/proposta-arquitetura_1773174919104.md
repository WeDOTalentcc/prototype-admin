# Arquitetura Completa — Plataforma de RH com Agentes de IA

## Sumario

1. [Visao Geral](#1-visao-geral)
2. [Estrutura do Monorepo](#2-estrutura-do-monorepo)
3. [Camada de Comunicacao](#3-camada-de-comunicacao)
4. [Orquestrador de Agentes](#4-orquestrador-de-agentes)
5. [Padrao para Dominios de Fluxo Previsivel (LangGraph)](#5-padrao-para-dominios-de-fluxo-previsivel-langgraph)
6. [Padrao para Dominios de Fluxo Imprevisivel (LangGraph ReAct)](#6-padrao-para-dominios-de-fluxo-imprevisivel-langgraph-react)
7. [Auditabilidade](#7-auditabilidade)
8. [Bancos de Dados](#8-bancos-de-dados)
9. [Autenticacao e Autorizacao](#9-autenticacao-e-autorizacao)
10. [Configuracao e Variaveis de Ambiente](#10-configuracao-e-variaveis-de-ambiente)
11. [Contextos de Agentes](#11-contextos-de-agentes)
12. [Observability e Monitoramento](#12-observability-e-monitoramento)
13. [Sugestoes e Apontamentos](#13-sugestoes-e-apontamentos)

---

## 1. Visao Geral

### Principios

- **Monorepo Python com UV** como gerenciador de pacotes e workspaces.
- **3 APIs de dominio** (Vagas, Funil de Talentos, Onboarding), cada uma como pacote independente.
- **Libs compartilhadas** centralizadas para modelos, servicos de banco, utilitarios, auditoria e contextos de agentes.
- **LangGraph como engine unica** para todos os agentes (Graph determinista e ReAct autonomo).
- **Comunicacao hibrida**: REST sincrono (<=2-3s) + WebSocket assincrono (via RabbitMQ) para operacoes com LLM/batch.
- **Celery + RabbitMQ** para distribuicao de tasks pesadas com prioridades por dominio.
- **Auditabilidade como cidadao de primeira classe** em todos os agentes.

### Diagrama de Alto Nivel

```
+-----------------------------------------------------------------+
|                          FRONTEND                                |
|                                                                  |
|   REST (CRUD, leitura, <=2-3s)    WebSocket (LLM, batch, async) |
+----------+----------------------------------+--------------------+
           |                                  |
           v                                  v
+---------------------+           +----------------------+
|   FastAPI Gateway    |           |   WebSocket Gateway   |
|   (sync endpoints)  |           |   (async endpoints)   |
+----------+----------+           +----------+-----------+
           |                                  |
           |                                  v
           |                      +----------------------+
           |                      |     RabbitMQ          |
           |                      |   (orquestracao)      |
           |                      +----------+-----------+
           |                                  |
           v                                  v
+-----------------------------------------------------------------+
|                     APIS DE DOMINIO                              |
|                                                                  |
|  +-------------+   +------------------+   +-----------------+    |
|  |  API Vagas   |   | API Funil        |   | API Onboarding  |   |
|  |             |   | de Talentos      |   |                 |    |
|  | - CRUDs     |   | - CRUDs          |   | - CRUDs         |   |
|  | - LangGraph |   | - LangGraph      |   | - LangGraph     |   |
|  |   Graphs    |   |   Graphs         |   |   Graphs        |   |
|  | - LangGraph |   | - LangGraph      |   | - LangGraph     |   |
|  |   ReAct     |   |   ReAct          |   |   ReAct         |   |
|  +-------------+   +------------------+   +-----------------+    |
|                                                                  |
+--------------------------+---------------------------------------+
                           |
+--------------------------v---------------------------------------+
|                     LIBS COMPARTILHADAS                          |
|                                                                  |
|  +----------+ +----------+ +----------+ +----------+             |
|  | models   | | services | |  utils   | |  audit   |             |
|  | (DB)     | | (repos)  | |          | |          |             |
|  +----------+ +----------+ +----------+ +----------+             |
|  +----------+ +----------+ +----------+ +----------+             |
|  | contexts | |  auth    | |  config  | | agents   |             |
|  | (prompts)| |          | |  (envs)  | | (core)   |             |
|  +----------+ +----------+ +----------+ +----------+             |
|                                                                  |
+--------------------------+---------------------------------------+
                           |
+--------------------------v---------------------------------------+
|                     INFRAESTRUTURA                               |
|                                                                  |
|  +--------------+  +--------------+  +--------------------+      |
|  | PostgreSQL   |  | Elasticsearch|  |  S3 / GCS          |      |
|  | + pgvector   |  |              |  |  (audit logs)      |      |
|  +--------------+  +--------------+  +--------------------+      |
|                                                                  |
|  +--------------+  +--------------+  +--------------------+      |
|  |  RabbitMQ    |  |  Redis       |  |  Doppler / GCP     |      |
|  |  + Celery    |  |  (cache +    |  |  Secret Manager    |      |
|  |              |  |   results)   |  |                    |      |
|  +--------------+  +--------------+  +--------------------+      |
|                                                                  |
+-----------------------------------------------------------------+
```

---

## 2. Estrutura do Monorepo

```
rh-platform/
+-- pyproject.toml                    # Workspace root (UV)
+-- uv.lock
|
+-- apps/
|   +-- api-vagas/
|   |   +-- pyproject.toml            # Dependencias especificas
|   |   +-- src/
|   |   |   +-- __init__.py
|   |   |   +-- main.py               # FastAPI app
|   |   |   +-- routes/
|   |   |   |   +-- rest/             # Endpoints sincronos (CRUD)
|   |   |   |   |   +-- jobs.py
|   |   |   |   |   +-- drafts.py
|   |   |   |   |   +-- templates.py
|   |   |   |   +-- ws/               # Endpoints WebSocket
|   |   |   |       +-- wizard_chat.py
|   |   |   |       +-- job_enrichment.py
|   |   |   +-- agents/
|   |   |   |   +-- graphs/           # LangGraph - fluxos previsiveis
|   |   |   |   |   +-- wizard_graph.py
|   |   |   |   |   +-- nodes/
|   |   |   |   |   |   +-- intent_classifier.py
|   |   |   |   |   |   +-- field_extractor.py
|   |   |   |   |   |   +-- tool_router.py
|   |   |   |   |   |   +-- tool_executor.py
|   |   |   |   |   |   +-- response_generator.py
|   |   |   |   |   |   +-- stage_transition.py
|   |   |   |   |   +-- edges.py      # Condicoes de transicao
|   |   |   |   |   +-- state.py      # TypedDict do estado
|   |   |   |   +-- react/            # LangGraph - fluxos livres
|   |   |   |   |   +-- job_assistant.py
|   |   |   |   |   +-- tools/
|   |   |   |   |       +-- salary_benchmark.py
|   |   |   |   |       +-- job_suggestions.py
|   |   |   |   |       +-- jd_enrichment.py
|   |   |   +-- workers/
|   |   |   |   +-- job_worker.py     # Consumer RabbitMQ
|   |   |   +-- tasks/
|   |   |       +-- job_tasks.py      # Celery tasks
|   |   +-- tests/
|   |
|   +-- api-funil/
|   |   +-- pyproject.toml
|   |   +-- src/
|   |   |   +-- main.py
|   |   |   +-- routes/
|   |   |   |   +-- rest/
|   |   |   |   |   +-- candidates.py
|   |   |   |   |   +-- pipeline.py
|   |   |   |   |   +-- screening.py
|   |   |   |   |   +-- interviews.py
|   |   |   |   +-- ws/
|   |   |   |       +-- talent_chat.py
|   |   |   |       +-- screening_batch.py
|   |   |   |       +-- kanban_chat.py
|   |   |   +-- agents/
|   |   |   |   +-- graphs/
|   |   |   |   |   +-- screening_graph.py
|   |   |   |   |   +-- interview_graph.py
|   |   |   |   |   +-- evaluation_graph.py
|   |   |   |   |   +-- nodes/
|   |   |   |   |   +-- state.py
|   |   |   |   +-- react/
|   |   |   |   |   +-- sourcing_agent.py
|   |   |   |   |   +-- kanban_agent.py
|   |   |   |   |   +-- analytics_agent.py
|   |   |   |   |   +-- tools/
|   |   |   |   |       +-- candidate_search.py
|   |   |   |   |       +-- pipeline_stats.py
|   |   |   |   |       +-- cv_analysis.py
|   |   |   |   |       +-- wsi_evaluation.py
|   |   |   +-- workers/
|   |   |   |   +-- funil_worker.py
|   |   |   |   +-- evaluation_dispatcher.py
|   |   |   +-- tasks/
|   |   |       +-- sourcing_tasks.py
|   |   |       +-- evaluation_tasks.py
|   |   +-- tests/
|   |
|   +-- api-onboarding/
|       +-- pyproject.toml
|       +-- src/
|       |   +-- main.py
|       |   +-- routes/
|       |   |   +-- rest/
|       |   |   |   +-- company.py
|       |   |   |   +-- benefits.py
|       |   |   |   +-- culture.py
|       |   |   |   +-- pipeline_templates.py
|       |   |   +-- ws/
|       |   |       +-- onboarding_chat.py
|       |   +-- agents/
|       |   |   +-- graphs/
|       |   |   |   +-- company_setup_graph.py
|       |   |   |   +-- nodes/
|       |   |   |   +-- state.py
|       |   |   +-- react/
|       |   |       +-- onboarding_assistant.py
|       |   |       +-- tools/
|       |   +-- workers/
|       |   |   +-- onboarding_worker.py
|       |   +-- tasks/
|       |       +-- onboarding_tasks.py
|       +-- tests/
|
+-- libs/
|   +-- models/                       # Modelos de dados (SQLAlchemy)
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- base.py               # Base declarativa
|   |       +-- vagas/
|   |       |   +-- job.py
|   |       |   +-- draft.py
|   |       |   +-- template.py
|   |       +-- funil/
|   |       |   +-- candidate.py
|   |       |   +-- application.py
|   |       |   +-- pipeline_stage.py
|   |       |   +-- screening.py
|   |       +-- onboarding/
|   |           +-- company.py
|   |           +-- benefit.py
|   |           +-- culture.py
|   |
|   +-- services/                     # Repositorios de acesso a dados
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- database.py           # Engine, session factory, migrations
|   |       +-- elasticsearch.py      # Client ES configurado
|   |       +-- vagas/
|   |       |   +-- job_repository.py
|   |       |   +-- draft_repository.py
|   |       |   +-- template_repository.py
|   |       +-- funil/
|   |       |   +-- candidate_repository.py
|   |       |   +-- application_repository.py
|   |       |   +-- screening_repository.py
|   |       +-- onboarding/
|   |           +-- company_repository.py
|   |           +-- benefit_repository.py
|   |
|   +-- utils/                        # Utilitarios genericos
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- dates.py
|   |       +-- text.py
|   |       +-- hashing.py
|   |       +-- pii_masking.py        # LGPD: mascarar CPF, email, tel
|   |       +-- validators.py
|   |
|   +-- audit/                        # Auditabilidade centralizada
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- graph_audit.py        # Auditoria para LangGraph (callback)
|   |       +-- audit_callback.py     # LangGraph callback handler
|   |       +-- audit_writer.py       # Persistencia (S3 + PG metadata)
|   |       +-- audit_models.py       # Dataclasses dos registros
|   |       +-- reconstruction.py     # Reconstrucao de timeline
|   |
|   +-- contexts/                     # Prompts e contextos dos agentes
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- vagas/
|   |       |   +-- wizard_stages.py       # Definicao de estagios
|   |       |   +-- wizard_prompts.py      # System prompts por estagio
|   |       |   +-- wizard_tools.py        # Ferramentas por estagio
|   |       +-- funil/
|   |       |   +-- screening_stages.py
|   |       |   +-- screening_prompts.py
|   |       |   +-- kanban_prompts.py
|   |       |   +-- sourcing_prompts.py
|   |       |   +-- sourcing_tools.py
|   |       +-- onboarding/
|   |       |   +-- setup_stages.py
|   |       |   +-- setup_prompts.py
|   |       +-- orchestrator/
|   |           +-- router_prompts.py      # Prompt do IntentRouter
|   |           +-- router_examples.py     # Few-shot + exemplos de fronteira
|   |           +-- domain_registry.py     # Registro de dominios
|   |
|   +-- auth/                         # Autenticacao e autorizacao
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- provider.py           # Interface abstrata
|   |       +-- workos_provider.py    # Implementacao WorkOS
|   |       +-- auth0_provider.py     # Implementacao Auth0 (alternativa)
|   |       +-- middleware.py         # FastAPI middleware
|   |       +-- dependencies.py       # FastAPI Depends()
|   |       +-- permissions.py        # RBAC / politicas
|   |
|   +-- config/                       # Configuracao centralizada
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- settings.py           # Carregamento das envs
|   |       +-- env_definitions.py    # Definicao documentada de cada env var
|   |       +-- providers/
|   |           +-- doppler.py        # Provider Doppler
|   |           +-- gcp_secrets.py    # Provider GCP Secret Manager
|   |
|   +-- orchestrator/                 # Orquestrador central de agentes
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- intent_router.py      # Roteador com escada de custo
|   |       +-- memory_resolver.py    # Tier 0: resolucao de referencias
|   |       +-- fast_router.py        # Tier 1: cache hash
|   |       +-- regex_router.py       # Tier 2: regex com scoring
|   |       +-- llm_router.py         # Tier 3: LLM com cascata
|   |       +-- semantic_cache.py     # Cache semantico com embeddings
|   |       +-- domain_registry.py    # Registro de agentes por dominio
|   |
|   +-- agents-core/                  # Engine LangGraph compartilhada
|   |   +-- pyproject.toml
|   |   +-- src/
|   |       +-- __init__.py
|   |       +-- graph/
|   |       |   +-- base_graph.py          # Classe base para graphs LangGraph
|   |       |   +-- base_node.py           # Interface de no
|   |       |   +-- edge_conditions.py     # Condicoes de transicao reutilizaveis
|   |       |   +-- checkpointer.py        # PostgresSaver wrapper (persistencia)
|   |       |   +-- state_schemas.py       # TypedDicts base para estados
|   |       +-- react/
|   |       |   +-- base_react_agent.py    # Classe base para ReAct com LangGraph
|   |       |   +-- tool_node.py           # ToolNode com timeout e isolamento
|   |       |   +-- confidence.py          # Calculo de confianca pos-execucao
|   |       +-- callbacks/
|   |       |   +-- audit_callback.py      # LangGraph callback para auditoria
|   |       |   +-- streaming_callback.py  # Callback para streaming via WS
|   |       +-- base_agent.py              # Interface base
|   |       +-- llm_client.py              # Client LLM unificado (Anthropic)
|   |
|   +-- messaging/                    # RabbitMQ + WebSocket + Celery
|       +-- pyproject.toml
|       +-- src/
|           +-- __init__.py
|           +-- rabbitmq.py           # Producer/Consumer
|           +-- celery_app.py         # Celery app compartilhado
|           +-- celery_config.py      # Filas, prioridades, routing
|           +-- dispatchers.py        # Dispatcher base (RabbitMQ -> Celery)
|           +-- websocket_manager.py  # Gerenciamento de conexoes WS
|           +-- message_schemas.py    # Schemas das mensagens
|
+-- infra/
|   +-- docker-compose.yml            # Dev local
|   +-- docker-compose.prod.yml
|   +-- docker-compose.workers.yml    # Workers Celery por dominio
|   +-- dockerfiles/
|   |   +-- Dockerfile.api-vagas
|   |   +-- Dockerfile.api-funil
|   |   +-- Dockerfile.api-onboarding
|   |   +-- Dockerfile.worker
|   +-- k8s/                          # Se usar Kubernetes
|       +-- deployments/
|       +-- services/
|
+-- migrations/                       # Alembic (compartilhado)
|   +-- alembic.ini
|   +-- env.py
|   +-- versions/
|
+-- scripts/
    +-- seed.py                       # Dados iniciais
    +-- migrate.py                    # Wrapper de migracao
    +-- health_check.py
```

---

## 3. Camada de Comunicacao

### 3.1. REST API Sincrona

Para operacoes que resolvem em ate 2-3 segundos (corte maximo em 5s):

- CRUD de vagas, candidatos, estagios, templates.
- Leituras de configuracao (beneficios, cultura, pipeline stages).
- Autocomplete e buscas rapidas.
- Validacoes de formulario.
- Dashboard data (metricas pre-calculadas).
- Autenticacao e autorizacao.

Cada API de dominio expoe seus endpoints REST independentemente.

### 3.2. Canal Assincrono (WebSocket + RabbitMQ + Celery)

Para operacoes que envolvem LLM, batch, ou processamento > 3s:

```
Frontend (WebSocket) --> API Gateway --> RabbitMQ --> Dispatcher
                                                        |
                                                        v
                                                   Celery Worker
                                                   (Agente/LLM)
                                                        |
                                                        v
                                              RabbitMQ (resposta)
                                                        |
                                                        v
                                              WebSocket Gateway
                                                        |
                                                        v
                                                    Frontend
```

**Fluxo detalhado:**

1. Frontend abre conexao WebSocket com o gateway.
2. Usuario envia mensagem no chat.
3. Gateway publica na fila RabbitMQ com `session_id`, `user_id`, `company_id`.
4. Dispatcher consome da fila e despacha para Celery task com prioridade por dominio.
5. Celery worker executa o agente LangGraph (Graph ou ReAct).
6. Worker publica resposta em fila de retorno (ou exchange direcionado por `session_id`).
7. Gateway recebe e envia via WebSocket para o frontend.

**Padrao Dispatcher -> Celery (do codigo atual, mantido):**

O dispatcher e um consumer pika leve que apenas faz parse do JSON e chama `.delay()` na Celery task correspondente. Isso separa a responsabilidade de consumir a fila (rapido, nao bloqueia) do processamento pesado (Celery com concurrency, retries, prioridades).

```python
# Dispatcher: consumer pika rapido
class DomainDispatcher:
    def _callback(self, ch, method, properties, body):
        message = json.loads(body)
        # Despacha para Celery task com prioridade
        process_domain_query.apply_async(
            args=[message],
            queue=DOMAIN_QUEUES[message["domain"]].name,
            priority=message.get("priority", 5),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
```

**Filas Celery com prioridade:**

```python
DOMAIN_QUEUES = {
    "sourcing":    QueueConfig(name="sourcing_high",    priority=8),
    "evaluation":  QueueConfig(name="evaluation_normal", priority=5),
    "vagas":       QueueConfig(name="vagas_normal",      priority=5),
    "onboarding":  QueueConfig(name="onboarding_low",    priority=3),
    "default":     QueueConfig(name="default",           priority=5),
}
```

**Casos de uso:**

- Chat conversacional com agentes (wizard de vagas, assistente, kanban).
- Triagem em batch (screening de N CVs).
- Geracao de relatorios complexos.
- Enriquecimento de descricao de vaga com LLM.
- Comparacao de candidatos.
- Avaliacao de respostas de candidatos (evaluation).

---

## 4. Orquestrador de Agentes

### 4.1. Escada de Custo para Roteamento

Toda mensagem conversacional que chega via fila passa pelo orquestrador, que tenta resolver do mais barato ao mais caro:

```
Mensagem do usuario
    |
    v
[Tier 0] Resolucao de Referencias (memoria conversacional)
    |   "me fale dele" -> resolve pronome para ultimo candidato
    |   "o segundo da lista" -> resolve posicao
    |   "desses, filtre por senior" -> mantem filtros ativos
    |   Custo: ~0 (lookup em memoria)
    |   Cobertura estimada: 15-25% das mensagens
    |
    | Nao resolveu
    v
[Tier 1] Cache Hash
    |   Hash da mensagem normalizada -> busca no Redis
    |   Se hit exato: retorna dominio cacheado
    |   Custo: ~0 (lookup Redis)
    |   Cobertura estimada: 5-10% (mensagens repetidas)
    |
    | Cache miss
    v
[Tier 2] Regex com Scoring
    |   Patterns por dominio com keywords (1pt) e regex (2pts)
    |   Negative patterns eliminam dominios
    |   Score >= 2: aceita roteamento
    |   Custo: ~0 (regex em memoria)
    |   Cobertura estimada: 30-40%
    |
    | Score < 2 ou empate
    v
[Tier 3] LLM com Cascata de Confianca
    |
    |   Prompt few-shot com:
    |     - Exemplos claros por dominio
    |     - Exemplos de fronteira (ambiguos)
    |     - Instrucao para retornar JSON com confidence
    |
    +-> Haiku (mais barato, ~$0.001-0.003)
    |     confidence >= 0.80 -> aceita, cacheia resultado
    |     confidence < 0.80 |
    |
    +-> Sonnet (~$0.01)
    |     confidence >= 0.80 -> aceita, cacheia resultado
    |     confidence < 0.80 |
    |
    +-> Fallback: solicita clarificacao ao usuario
          "Nao entendi exatamente o que precisa.
           Voce quer: [opcao A] ou [opcao B]?"
```

### 4.2. Cache Semantico (otimizacao do Tier 3)

Antes de chamar a LLM no Tier 3, verifica se existe uma mensagem semanticamente similar ja classificada:

```
Mensagem -> Embedding (modelo leve) -> Busca vetorial no cache
  -> Similaridade > 0.95: usa dominio cacheado (custo ~zero)
  -> Similaridade <= 0.95: segue para LLM, classifica, cacheia
```

Isso reduz chamadas LLM em 40-60% apos semanas de uso.

### 4.3. Formato do Prompt Few-Shot (Tier 3)

```
Dominios disponiveis:
- vagas: criacao, edicao, publicacao de vagas
- funil_screening: triagem e avaliacao de candidatos
- funil_sourcing: busca e atracao de candidatos
- funil_pipeline: gestao do kanban/pipeline
- funil_analytics: metricas, relatorios, KPIs
- onboarding: cadastro e configuracao da empresa

EXEMPLOS CLAROS:
"Criar vaga de dev backend senior" -> vagas (0.95)
"Buscar candidatos com Python" -> funil_sourcing (0.93)
"Como esta o funil da vaga de PM?" -> funil_analytics (0.90)

EXEMPLOS DE FRONTEIRA:
"Quero ver os candidatos da vaga de PM"
-> funil_pipeline (0.88) -- visualizacao de lista, NAO criacao de vaga

"Muda os requisitos da vaga de PM pra incluir ingles"
-> vagas (0.92) -- edicao da vaga, NAO gestao de candidatos

"Quantas vagas a gente tem abertas?"
-> funil_analytics (0.85) -- metrica, NAO criacao de vaga

"Fecha a vaga de designer, ja contratamos"
-> vagas (0.90) -- encerramento de vaga, NAO onboarding
```

---

## 5. Padrao para Dominios de Fluxo Previsivel (LangGraph)

### 5.1. Quando usar

- Wizard de criacao de vagas (estagios definidos).
- Fluxo de triagem/screening (etapas sequenciais).
- Onboarding de empresa (setup passo a passo).
- Fluxos de aprovacao.
- Pipeline multi-agent linear (intent -> plan -> execute -> validate -> format).
- Qualquer processo com estagios conhecidos e transicoes claras.

### 5.2. Estrutura com LangGraph StateGraph

Usa `langgraph.graph.StateGraph` com `TypedDict` para estado tipado, conditional edges para decisoes, e checkpointer para persistencia:

```python
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver


class WizardState(TypedDict):
    """Estado tipado do wizard. LangGraph garante type safety."""
    session_id: str
    user_id: str
    company_id: str
    current_stage: str
    messages: list
    extracted_fields: dict
    draft: dict
    tools_used: list
    error: Optional[str]
    needs_human_review: bool


def create_wizard_graph(checkpointer=None) -> StateGraph:
    """
    Cria grafo LangGraph para wizard de vagas.
    Cada no e uma funcao pura que recebe e retorna estado.
    """
    graph = StateGraph(WizardState)

    # Nos (funcoes que processam estado)
    graph.add_node("intent_classifier", classify_intent)
    graph.add_node("field_extractor", extract_fields)
    graph.add_node("tool_router", route_to_tools)
    graph.add_node("tool_executor", execute_tools)
    graph.add_node("response_generator", generate_response)
    graph.add_node("stage_transition", check_stage_transition)

    # Entry point
    graph.set_entry_point("intent_classifier")

    # Edges condicionais
    graph.add_conditional_edges(
        "intent_classifier",
        should_extract_or_respond,
        {
            "extract": "field_extractor",
            "respond": "response_generator",
            "error": END,
        }
    )

    graph.add_edge("field_extractor", "tool_router")

    graph.add_conditional_edges(
        "tool_router",
        needs_tools,
        {
            "yes": "tool_executor",
            "no": "response_generator",
        }
    )

    graph.add_edge("tool_executor", "response_generator")

    graph.add_conditional_edges(
        "response_generator",
        should_transition_stage,
        {
            "transition": "stage_transition",
            "stay": END,
        }
    )

    graph.add_edge("stage_transition", END)

    # Compilar com checkpointer para persistencia
    return graph.compile(checkpointer=checkpointer)
```

### 5.3. Definicao de Estagios por Dominio

Cada dominio define seus estagios em arquivos separados (identico a proposta original):

```python
# contexts/vagas/wizard_stages.py

WIZARD_STAGES = {
    "basic_info": {
        "required_fields": ["title", "seniority", "work_model"],
        "optional_fields": ["department", "location"],
        "next_stage": "requirements",
        "tools": ["get_job_suggestions", "get_company_config"],
        "transition_criteria": "Titulo, senioridade e modelo preenchidos",
    },
    "requirements": {
        "required_fields": ["requirements"],
        "optional_fields": ["skills", "nice_to_have"],
        "next_stage": "compensation",
        "tools": ["get_job_suggestions", "search_similar_jobs"],
        "transition_criteria": "Requisitos minimos definidos",
    },
    # ...
}
```

### 5.4. Checkpoints com PostgresSaver

LangGraph oferece checkpointer nativo para PostgreSQL. Isso substitui a implementacao manual de checkpoints:

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Cria checkpointer conectado ao PostgreSQL
checkpointer = PostgresSaver.from_conn_string(settings.DATABASE_URL)

# Grafo com persistencia automatica
graph = create_wizard_graph(checkpointer=checkpointer)

# Invocacao com thread_id para recovery
config = {"configurable": {"thread_id": f"wizard-{session_id}"}}
result = graph.invoke(state, config=config)

# Se o usuario fechar o browser e voltar:
# LangGraph restaura automaticamente o ultimo estado salvo
result = graph.invoke(new_input, config=config)
```

### 5.5. Streaming por No

LangGraph suporta streaming nativo via `.stream()`:

```python
async for event in graph.astream(state, config=config):
    # event contem: node_name, state_update
    # Enviar via WebSocket para o frontend
    await ws.send_json({
        "type": "node_complete",
        "node": event.get("node"),
        "data": extract_relevant(event),
    })
```

### 5.6. Vantagens sobre implementacao propria

- **Checkpoints**: `PostgresSaver` ja implementado e testado, sem codigo custom.
- **Streaming**: `.astream()` nativo, sem precisar implementar event emitter.
- **Visualizacao**: LangGraph Studio permite visualizar e debugar o grafo.
- **Human-in-the-loop**: `interrupt_before`/`interrupt_after` nativos para pausar em nos especificos.
- **Subgraphs**: grafos podem conter sub-grafos, permitindo composicao hierarquica.

---

## 6. Padrao para Dominios de Fluxo Imprevisivel (LangGraph ReAct)

### 6.1. Quando usar

- Assistente do recrutador (consultas livres).
- Analytics sob demanda ("como esta o funil?").
- Kanban/pipeline analysis.
- Sourcing e busca exploratoria.
- Comparacao de candidatos.
- Qualquer interacao onde a sequencia de acoes depende do contexto.

### 6.2. LangGraph prebuilt ReAct Agent

LangGraph oferece `create_react_agent` que implementa o loop ReAct completo:

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic


def create_sourcing_agent(checkpointer=None):
    """
    Agente ReAct para sourcing usando LangGraph prebuilt.
    Define apenas: model, tools, system prompt. O loop e do framework.
    """
    llm = ChatAnthropic(
        model=settings.LLM_AGENT_MODEL,
        temperature=0.3,
    )

    tools = [
        search_candidates,
        get_candidate_details,
        compare_candidates,
        get_pipeline_stats,
        apply_filters,
        get_sourcing_recommendations,
    ]

    system_prompt = load_prompt("funil/sourcing_prompts.py")

    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_prompt,
        checkpointer=checkpointer,
    )

    return agent
```

### 6.3. Agente ReAct Custom com LangGraph (quando precisar de mais controle)

Para casos que precisam de logica customizada (confianca, resposta forcada, max iteracoes):

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode


class ReActState(TypedDict):
    messages: list
    tools_used: list[str]
    iteration: int
    max_iterations: int
    confidence: float
    final_answer: Optional[str]


def create_custom_react_graph(llm, tools, max_iterations=8):
    """
    ReAct customizado com LangGraph para controle total.
    Mantem as vantagens do framework (checkpoints, streaming, callbacks)
    mas adiciona logica propria (confianca, resposta forcada, limites).
    """
    graph = StateGraph(ReActState)
    tool_node = ToolNode(tools)

    graph.add_node("reason", reason_node)        # LLM decide acao
    graph.add_node("act", tool_node)              # Executa tool
    graph.add_node("force_answer", force_answer)  # Resposta forcada

    graph.set_entry_point("reason")

    graph.add_conditional_edges(
        "reason",
        decide_next_step,
        {
            "use_tool": "act",
            "final_answer": END,
            "force": "force_answer",   # Max iteracoes atingido
        }
    )

    graph.add_edge("act", "reason")  # Observe -> Reason loop
    graph.add_edge("force_answer", END)

    return graph.compile()


def decide_next_step(state: ReActState) -> Literal["use_tool", "final_answer", "force"]:
    """Condicao de transicao: tool, resposta, ou forcada."""
    if state["iteration"] >= state["max_iterations"]:
        return "force"

    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "use_tool"

    return "final_answer"
```

### 6.4. Contrato para Agentes de Dominio

Qualquer agente ReAct segue o mesmo padrao — define prompt, tools e contexto:

```python
class KanbanAgent:
    """
    O agente de dominio e fino.
    Ele define prompt, tools e contexto.
    O grafo LangGraph faz o resto (loop, checkpoints, auditoria, streaming).
    """
    def __init__(self):
        self.graph = create_custom_react_graph(
            llm=get_llm(settings.LLM_AGENT_MODEL),
            tools=self._get_tools(),
            max_iterations=8,
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        config = {
            "configurable": {"thread_id": input.session_id},
            "callbacks": [AuditCallback(input.user_id, input.company_id)],
        }

        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=input.message)]},
            config=config,
        )

        return AgentOutput(
            message=result["final_answer"],
            confidence=result.get("confidence", 0.0),
            tools_used=result.get("tools_used", []),
        )
```

### 6.5. Isolamento de Ferramentas

O `ToolNode` do LangGraph ja executa tools com captura de excecao. Para adicionar timeout:

```python
from langgraph.prebuilt import ToolNode
import asyncio

class TimedToolNode(ToolNode):
    """ToolNode com timeout por execucao de tool."""

    def __init__(self, tools, timeout_seconds=15):
        super().__init__(tools)
        self.timeout = timeout_seconds

    async def _arun_tool(self, tool_call, config):
        try:
            return await asyncio.wait_for(
                super()._arun_tool(tool_call, config),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            return f"Tool {tool_call['name']} timeout after {self.timeout}s"
```

### 6.6. Resposta Forcada

Se o loop esgota as iteracoes sem resposta final, o no `force_answer` faz uma ultima chamada ao modelo removendo as ferramentas e pedindo a melhor resposta possivel com as informacoes coletadas. Nunca retorna erro ao usuario por esgotamento de iteracoes.

### 6.7. Confianca Calculada

A confianca nao e um numero fixo. E derivada da execucao: taxa de sucesso das ferramentas, se resolveu antes de esgotar iteracoes, se deu resposta final explicita.

---

## 7. Auditabilidade

### 7.1. Principio

Toda execucao de agente — Graph ou ReAct — deve produzir um registro imutavel completo que permita reconstruir exatamente o que aconteceu e por que. Esse log e essencial para compliance (LGPD, regulamentacoes de IA), debug, e melhoria continua.

### 7.2. Separacao de Armazenamento

```
+-------------------------+     +---------------------------+
|   PostgreSQL (leve)     |     |   S3 / GCS (pesado)       |
|                         |     |                           |
|  - execution_id         |     |  - Prompt completo        |
|  - session_id           |---->|  - Resposta bruta LLM     |
|  - company_id           | ref |  - Tool inputs/outputs    |
|  - user_id              |     |  - State snapshots        |
|  - domain               |     |  - Decisoes humanas       |
|  - timestamp            |     |  - Raciocinio completo    |
|  - duration_ms          |     |                           |
|  - nodes_visited        |     |  Particionado por:        |
|  - tools_used           |     |  audit/{domain}/{date}/   |
|  - success              |     |  {company_id}/{exec}.jsonl|
|  - confidence           |     |                           |
|  - error (se houver)    |     |                           |
+-------------------------+     +---------------------------+
```

- **Consulta rapida** (metricas, dashboard, investigacao inicial) -> PostgreSQL.
- **Investigacao profunda** (reconstruir raciocinio, compliance) -> S3 via execution_id.

### 7.3. Auditoria via LangGraph Callbacks

Em vez de implementar auditoria manualmente em cada no, usa-se o sistema de callbacks do LangGraph. Um unico `AuditCallback` captura tudo automaticamente:

```python
from langchain_core.callbacks import BaseCallbackHandler
from uuid import uuid4
from datetime import datetime, timezone


class AuditCallback(BaseCallbackHandler):
    """
    Callback LangGraph que captura automaticamente:
    - Inicio/fim de cada no
    - Chamadas LLM (prompt, resposta, tokens, latencia)
    - Chamadas de tools (input, output, duracao)
    - Transicoes entre nos

    Nenhum no precisa saber que esta sendo auditado.
    """

    def __init__(self, user_id: str, company_id: str, session_id: str):
        self.execution_id = str(uuid4())
        self.user_id = user_id
        self.company_id = company_id
        self.session_id = session_id
        self.entries = []
        self.start_time = None

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.start_time = datetime.now(timezone.utc)

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._current_llm_start = datetime.now(timezone.utc)

    def on_llm_end(self, response, **kwargs):
        latency = (datetime.now(timezone.utc) - self._current_llm_start).total_seconds() * 1000
        self.entries.append({
            "type": "llm_call",
            "timestamp": self._current_llm_start.isoformat(),
            "model": response.llm_output.get("model_name") if response.llm_output else None,
            "prompt": kwargs.get("prompts"),
            "response": response.generations[0][0].text if response.generations else None,
            "tokens": response.llm_output.get("token_usage") if response.llm_output else None,
            "latency_ms": latency,
        })

    def on_tool_start(self, serialized, input_str, **kwargs):
        self._current_tool_start = datetime.now(timezone.utc)
        self._current_tool_name = serialized.get("name", "unknown")

    def on_tool_end(self, output, **kwargs):
        latency = (datetime.now(timezone.utc) - self._current_tool_start).total_seconds() * 1000
        self.entries.append({
            "type": "tool_call",
            "timestamp": self._current_tool_start.isoformat(),
            "tool": self._current_tool_name,
            "input": kwargs.get("input_str"),
            "output": str(output),
            "latency_ms": latency,
        })

    def on_chain_end(self, outputs, **kwargs):
        """Ao final, persiste tudo."""
        total_duration = (datetime.now(timezone.utc) - self.start_time).total_seconds() * 1000

        # Metadata leve -> PostgreSQL
        save_execution_metadata(
            execution_id=self.execution_id,
            session_id=self.session_id,
            user_id=self.user_id,
            company_id=self.company_id,
            duration_ms=total_duration,
            nodes_visited=[e for e in self.entries if e["type"] == "node"],
            tools_used=[e["tool"] for e in self.entries if e["type"] == "tool_call"],
            success=True,
        )

        # Log completo -> S3
        save_full_audit_log(
            execution_id=self.execution_id,
            domain=kwargs.get("domain", "unknown"),
            company_id=self.company_id,
            entries=self.entries,
        )
```

**Uso em qualquer agente:**

```python
# O agente NAO sabe que esta sendo auditado
config = {
    "callbacks": [AuditCallback(user_id, company_id, session_id)],
    "configurable": {"thread_id": session_id},
}
result = graph.invoke(state, config=config)
```

### 7.4. Reconstrucao de Timeline

Endpoint interno para investigacao:

```
GET /api/v1/audit/executions/{execution_id}/timeline

Retorna:
{
  "execution_id": "...",
  "domain": "kanban",
  "user": "recrutador@empresa.com",
  "company": "Empresa X",
  "timestamp": "2026-03-06T14:30:00Z",
  "duration_ms": 4500,
  "confidence": 0.85,
  "steps": [
    {
      "step": 1,
      "type": "llm_call",
      "reasoning": "Usuario quer ver metricas do pipeline...",
      "decision": "use_tool",
      "tool": "get_pipeline_summary",
      "tool_input": {"job_id": "123"},
      "tool_output": {"stages": [...], "total": 45},
      "duration_ms": 1200
    },
    {
      "step": 2,
      "type": "llm_call",
      "reasoning": "Tenho os dados, vou formatar...",
      "decision": "final_answer",
      "duration_ms": 800
    }
  ]
}
```

---

## 8. Bancos de Dados

### 8.1. PostgreSQL (Transacional + Vetorial + Checkpoints)

**Uso principal:** dados transacionais (vagas, candidatos, empresas, pipeline stages, configuracoes).

**pgvector:** busca vetorial para:

- Embeddings de vagas (match candidato <-> vaga).
- Cache semantico do orquestrador.
- Busca semantica de candidatos por skills.

**LangGraph checkpoints:** tabelas gerenciadas pelo `PostgresSaver` para persistencia de estado dos grafos.

**Schema sugerido:**

```
public/                    # Dados transacionais
  jobs, candidates, companies, applications,
  pipeline_stages, screening_results, ...

audit_metadata/            # Indice leve de auditoria
  agent_executions (execution_id, session_id, company_id,
                    domain, timestamp, duration_ms, success, ...)

vectors/                   # pgvector
  job_embeddings, candidate_embeddings, semantic_cache

langgraph/                 # Checkpoints LangGraph (PostgresSaver)
  checkpoints, checkpoint_writes
```

### 8.2. Elasticsearch

**Uso:** busca full-text em documentos de candidatos:

- CVs parseados.
- Transcricoes de entrevistas.
- Notas de recrutadores.
- Busca booleana avancada (sourcing).

**Nao usar para:** dados transacionais ou metricas. PostgreSQL e mais adequado.

### 8.3. S3 / GCS (Object Storage)

**Uso:** logs completos de auditoria (append-only, imutavel).

**Estrutura:**

```
audit/
  vagas/
    2026/03/06/
      {company_id}/
        {execution_id}.jsonl
  funil/
    2026/03/06/
      ...
```

### 8.4. Redis

**Uso:** cache operacional + Celery result backend:

- Cache hash do orquestrador (Tier 1).
- Cache semantico (Tier 3, se nao usar pgvector).
- Rate limiting.
- Session data do WebSocket.
- Celery result backend e broker auxiliar.

---

## 9. Autenticacao e Autorizacao

### 9.1. Provider

Recomendacao: **WorkOS** se o foco e B2B com SSO/SCIM. **Auth0** se precisa de fluxos B2C variados.

Para esta plataforma (B2B, empresas de RH), WorkOS e a escolha mais direta.

### 9.2. Estrutura

```python
# libs/auth/provider.py -- Interface abstrata

class AuthProvider(ABC):
    async def verify_token(self, token: str) -> AuthUser
    async def get_organization(self, org_id: str) -> Organization
    async def list_users(self, org_id: str) -> List[AuthUser]


# libs/auth/workos_provider.py -- Implementacao

class WorkOSProvider(AuthProvider):
    async def verify_token(self, token: str) -> AuthUser:
        # Valida JWT via WorkOS
        ...


# libs/auth/middleware.py -- FastAPI middleware

class AuthMiddleware:
    async def __call__(self, request, call_next):
        token = extract_bearer(request)
        user = await self.provider.verify_token(token)
        request.state.user = user
        request.state.company_id = user.organization_id
        return await call_next(request)
```

### 9.3. Multi-tenancy

Toda query ao banco inclui `company_id` como filtro. O `company_id` vem do token JWT (via WorkOS organization). Nenhum endpoint retorna dados de outra empresa.

---

## 10. Configuracao e Variaveis de Ambiente

### 10.1. Provider Externo

Variaveis vem de **Doppler** ou **GCP Secret Manager**, nunca de `.env` em producao.

### 10.2. Carregamento Padronizado

```python
# libs/config/env_definitions.py

from pydantic_settings import BaseSettings
from typing import Optional


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str
    ELASTICSEARCH_URL: str
    DB_POOL_SIZE: int = 20
    DB_CONNECT_TIMEOUT: int = 10


class LLMSettings(BaseSettings):
    ANTHROPIC_API_KEY: str
    LLM_ROUTER_MODEL: str = "claude-haiku-4-5-20251001"
    LLM_AGENT_MODEL: str = "claude-sonnet-4-5-20250929"
    LLM_ROUTER_TEMPERATURE: float = 0.1
    LLM_AGENT_TEMPERATURE: float = 0.3


class MessagingSettings(BaseSettings):
    RABBITMQ_URL: str
    RABBITMQ_EXCHANGE: str = "rh_platform"
    RABBITMQ_PREFETCH: int = 1
    CELERY_BROKER_URL: str = ""  # Default: same as RABBITMQ_URL
    CELERY_RESULT_BACKEND: str = ""  # Default: Redis


class AuthSettings(BaseSettings):
    WORKOS_CLIENT_ID: str
    WORKOS_API_KEY: str
    WORKOS_WEBHOOK_SECRET: Optional[str] = None


class AuditSettings(BaseSettings):
    AUDIT_STORAGE_BUCKET: str
    AUDIT_STORAGE_PREFIX: str = "audit"
    AUDIT_STORAGE_REGION: str = "us-east-1"


class CacheSettings(BaseSettings):
    REDIS_URL: str
    ROUTER_CACHE_TTL: int = 3600
    SEMANTIC_CACHE_TTL: int = 86400


class AppSettings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000
    SENTRY_DSN: Optional[str] = None


class Settings(
    DatabaseSettings,
    LLMSettings,
    MessagingSettings,
    AuthSettings,
    AuditSettings,
    CacheSettings,
    AppSettings,
):
    class Config:
        env_file = ".env"  # Apenas para dev local
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
```

### 10.3. Uso no Codigo

```python
from libs.config import settings

db_url = settings.DATABASE_URL       # Ja carregado e tipado
model = settings.LLM_ROUTER_MODEL   # Com valor padrao se nao setado
```

---

## 11. Contextos de Agentes

### 11.1. Estrutura

Cada dominio tem seus arquivos de contexto separados em `libs/contexts/`:

```
contexts/
+-- vagas/
|   +-- wizard_stages.py       # Definicao dos estagios do wizard
|   +-- wizard_prompts.py      # System prompts por estagio
|   +-- wizard_tools.py        # Ferramentas disponiveis por estagio
+-- funil/
|   +-- screening_stages.py    # Estagios do fluxo de triagem
|   +-- screening_prompts.py   # Prompts de triagem
|   +-- kanban_prompts.py      # Prompt do agente kanban
|   +-- sourcing_prompts.py    # Prompt do agente de sourcing
|   +-- sourcing_tools.py      # Ferramentas de sourcing
+-- onboarding/
|   +-- setup_stages.py        # Estagios do setup da empresa
|   +-- setup_prompts.py       # Prompts de onboarding
+-- orchestrator/
    +-- router_prompts.py      # Prompt do roteador
    +-- router_examples.py     # Few-shot + exemplos de fronteira
    +-- domain_registry.py     # Mapa dominio -> agente
```

### 11.2. Prompts como Codigo

Prompts sao versionados no repositorio, nao em banco. Isso permite code review, historico de mudancas, e rollback. Se precisar de A/B testing de prompts, usar feature flags, nao banco.

---

## 12. Observability e Monitoramento

### 12.1. Stack Recomendada

- **Sentry**: error tracking e alertas em producao.
- **Prometheus + Grafana**: metricas operacionais (latencia, throughput, filas).
- **LangSmith**: tracing de execucoes LangGraph (complementar ao audit proprio).
- **Celery Flower**: monitoramento de workers e tasks.
- **Logs estruturados (JSON)**: para correlacao via `request_id` e `execution_id`.
- **PII Masking**: filtro global nos logs para LGPD (CPF, email, telefone, nomes).

### 12.2. Metricas Chave

```
# Orquestrador
router_tier_hit{tier="0|1|2|3"}           # Qual tier resolveu
router_confidence{model="haiku|sonnet"}   # Distribuicao de confianca
router_latency_ms{tier="0|1|2|3"}         # Latencia por tier

# Agentes
agent_execution_duration_ms{domain, type} # Graph vs ReAct
agent_iterations{domain}                  # Quantas iteracoes ReAct
agent_tool_calls{domain, tool}            # Ferramentas mais usadas
agent_tool_failures{domain, tool}         # Taxa de falha por tool
agent_confidence{domain}                  # Confianca das respostas

# Celery
celery_task_duration_ms{queue, task}      # Duracao por task
celery_queue_depth{queue}                 # Tasks pendentes por fila
celery_task_retries{queue, task}          # Retries por task

# Infraestrutura
rabbitmq_queue_depth{queue}               # Mensagens pendentes
rabbitmq_consumer_lag_ms{queue}           # Lag do worker
ws_active_connections                     # WebSockets ativos
llm_tokens_consumed{model, domain}        # Consumo de tokens
llm_cost_usd{model, domain}              # Custo estimado
```

---

## 13. Sugestoes e Apontamentos

### 13.1. APIs Separadas por Dominio — Isolamento de Carga

A estrutura propoe 3 APIs separadas (vagas, funil, onboarding) com deploys independentes. A principal razao nao e organizacional — e **isolamento de carga**.

**Por que separar:**

- **Evaluation** processa respostas de candidatos via LLM — CPU/memoria intensivo, com picos imprevisiveis quando uma empresa lanca processo seletivo grande (centenas de candidatos respondendo ao mesmo tempo).
- **Sourcing** faz multiplas chamadas a APIs externas + LLM — latencia alta, pode segurar conexoes por 10-30s.
- **CRUD de vagas/onboarding** e leve e rapido — resposta esperada em <200ms.

Com tudo num unico deploy, um pico de evaluations pode estourar memoria/CPU e degradar o CRUD que deveria ser instantaneo. Com deploys separados, escala-se evaluation horizontalmente (mais replicas) sem afetar o resto.

**O codigo atual ja reconhece isso parcialmente**: os Celery workers sao separados por dominio (`sourcing_high`, `evaluation_normal`). Mas a camada HTTP (Flask) e unica — se o endpoint REST de evaluation receber rajada, degrada tudo.

**Recomendacao**: APIs separadas desde o inicio. O monorepo com UV permite compartilhar libs sem acoplar o deploy. O custo operacional de N deploys e baixo com containers — e muito menor que o custo de um incidente onde sourcing derruba CRUD.

**Estrategia de deploy:**

```
api-vagas        -> 1-2 replicas (carga leve, previsivel)
api-funil        -> 2-4 replicas (carga media, picos por processo seletivo)
api-onboarding   -> 1 replica (carga minima)
workers-sourcing -> 2-4 replicas Celery (auto-scale por queue depth)
workers-eval     -> 2-6 replicas Celery (auto-scale por queue depth)
```

### 13.2. Worker por Dominio vs Worker Generico

O padrao atual do codigo (dispatchers + Celery workers por fila) ja resolve isso bem. Manter mixed workers para absorver picos e workers dedicados para dominios com SLA mais apertado (sourcing, evaluation). Escalar horizontalmente adicionando replicas no docker-compose ou k8s.

### 13.3. Versionamento de Prompts

Se os prompts mudam com frequencia e impactam comportamento dos agentes, considerar manter um changelog de prompts junto com metricas de performance (confianca, acuracia, tempo) para cada versao. Isso ajuda a identificar regressoes quando um prompt e alterado.

### 13.4. Custo de Auditoria

Os logs completos (com prompts e respostas sem truncar) podem crescer rapido. Definir politica de retencao desde o inicio: logs completos por 90 dias em storage quente (S3 standard), depois move para storage frio (S3 Glacier/GCS Nearline). Metadata no PostgreSQL pode ter retencao maior (1 ano+) porque e leve.

### 13.5. Testes dos Agentes

Agentes sao dificeis de testar porque dependem de LLM. Criar fixtures com respostas LLM gravadas (snapshot testing) para os fluxos mais criticos. O audit trail ajuda aqui: gravar execucoes reais e usar como test cases de regressao. LangSmith permite replay de traces, o que facilita debug.

### 13.6. Rate Limiting por Empresa

Cada empresa (tenant) deve ter um budget de tokens/chamadas LLM. O orquestrador deve verificar o budget antes de rotear para o Tier 3. Isso evita que um tenant com uso abusivo impacte o custo da plataforma.

### 13.7. Fallback sem LLM

Para operacoes criticas (publicar vaga, mover candidato), garantir que existe um caminho de execucao que funciona mesmo se todas as LLMs estiverem fora do ar. O CRUD via REST nao depende de LLM. Os agentes podem falhar graciosamente sugerindo que o usuario use a interface manual.

### 13.8. Migracao Gradual

Se a plataforma ja existe (como sugere o codigo analisado), a migracao para essa arquitetura deve ser incremental:

1. **Fase 1**: Adicionar auditabilidade (AuditCallback) nos grafos LangGraph existentes.
2. **Fase 2**: Implementar escada de custo no roteador.
3. **Fase 3**: Adicionar agentes ReAct para sourcing (maior ganho de capacidade).
4. **Fase 4**: Migrar Flask -> FastAPI com WebSocket.
5. **Fase 5**: Separar APIs por dominio quando volume justificar.

Nao reescrever tudo de uma vez.

### 13.9. Elasticsearch — Considerar Alternativas

Para busca de documentos de candidatos, avaliar se **pgvector + full-text search do PostgreSQL** (ts_vector) nao e suficiente antes de adicionar Elasticsearch como dependencia. PostgreSQL 16+ tem FTS robusto e pgvector resolve busca semantica. Elasticsearch adiciona complexidade operacional significativa. So vale se o volume de documentos e a complexidade das queries justificarem.

### 13.10. Comunicacao entre APIs

Se as 3 APIs forem deployadas separadamente, elas precisam se comunicar. Evitar chamadas HTTP sincronas entre elas (acoplamento). Preferir comunicacao via RabbitMQ (eventos) ou shared database (ja que o PostgreSQL e centralizado). Exemplo: quando uma vaga e publicada (API Vagas), emitir evento na fila que a API Funil consome para preparar o pipeline.

### 13.11. LangGraph Studio para Debug

LangGraph Studio permite visualizar a execucao dos grafos em tempo real, incluindo estado em cada no, decisoes de transicao e tool calls. Usar em desenvolvimento e staging para validar comportamento dos agentes antes de ir para producao.