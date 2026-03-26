# AI Architecture — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` (GitHub WeDOTalent) + `lia-agent-system` (Replit)
> **SPEC-DRIVEN DEVELOPMENT** — este documento é fonte da verdade para a arquitetura de IA.

---

## 1. Visão Geral da Arquitetura

O sistema de IA da WeDOTalent opera em duas camadas complementares:

| Camada | Repositório | Stack | Papel |
|--------|-------------|-------|-------|
| **Agente Multi-Domínio** | `recruiter_agent_v5` | Python + LangGraph + Gemini + Celery + RabbitMQ | Processa queries do recrutador via linguagem natural, executando ações no ATS |
| **Serviços LIA** | `lia-agent-system` | Python + FastAPI + LangGraph | Triagem WSI, sourcing, voz, análises — serviços isolados consumidos pelo frontend |

### 1.1 Diagrama de Fluxo Geral

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  ats_front   │────▶│  ats_api (Rails)  │────▶│  PostgreSQL  │
│  (Nuxt 3)    │     │  REST API + JWT   │     │  Multi-tenant│
└──────┬───────┘     └────────┬──────────┘     └──────────────┘
       │                      │
       │  WebSocket/HTTP      │  RabbitMQ / HTTP
       │                      │
       ▼                      ▼
┌──────────────┐     ┌──────────────────────────────┐
│  LIA Chat    │     │  recruiter_agent_v5          │
│  (Prompt UI) │────▶│  ┌─────────────────────────┐ │
│              │     │  │ WorkflowOrchestrator     │ │
└──────────────┘     │  │  (LangGraph StateGraph)  │ │
                     │  │                           │ │
                     │  │  intent_analyzer          │ │
                     │  │  → api_planner            │ │
                     │  │  → api_executor           │ │
                     │  │  → plan_validator         │ │
                     │  │  → data_processor         │ │
                     │  │  → answer_formatter       │ │
                     │  └─────────────────────────┘ │
                     │                               │
                     │  Domain Dispatchers:           │
                     │  ┌──────────────────────────┐ │
                     │  │ applies │ jobs │ insights │ │
                     │  │ messaging │ autonomous   │ │
                     │  │ evaluation │ sourcing     │ │
                     │  └──────────────────────────┘ │
                     └──────────────────────────────┘
```

---

## 2. Workflow Pipeline (LangGraph)

O pipeline principal é um `StateGraph` definido em `src/workflow/graph.py`. Todos os agentes operam sobre um estado compartilhado (`QueryState`).

### 2.1 Nós do Grafo

| Nó | Agente | Responsabilidade | Arquivo |
|----|--------|-----------------|---------|
| `intent_analyzer` | `IntentAnalyzerAgent` | Analisa a query, identifica entidades, ação principal, filtros, campos necessários | `src/agents/intent_analyzer.py` |
| `api_planner` | `APIPlannerAgent` | Cria plano de execução com steps sequenciais, cada um mapeando para uma API | `src/agents/api_planner.py` |
| `api_executor` | `APIExecutorAgent` | Executa chamadas REST ao ATS API seguindo o plano | `src/agents/api_executor.py` |
| `plan_validator` | `PlanValidatorAgent` | Valida resultados — pode solicitar re-planejamento se dados insuficientes | `src/agents/plan_validator.py` |
| `data_processor` | `DataProcessorAgent` | Processa e formata dados brutos das APIs | `src/agents/data_processor.py` |
| `answer_formatter` | `AnswerFormatterAgent` | Formata resposta final usando taxonomia de 11 tipos | `src/agents/answer_formatter.py` |

### 2.2 Fluxo de Execução

```
START
  │
  ▼
[intent_analyzer] ──── error? ──── END
  │ continue
  ▼
[api_planner] ──── error? ──── END
  │ continue
  ▼
[api_executor] ──── needs_confirmation? ──── END (aguarda confirmação do usuário)
  │ continue         │ error? ──── END
  ▼
[plan_validator] ──── replan? ──── [api_planner] (loop)
  │ continue         │ abort? ──── [answer_formatter]
  ▼
[data_processor] ──── error? ──── END
  │ continue
  ▼
[answer_formatter] ──── END
```

### 2.3 Estado Compartilhado (`QueryState`)

Definido em `src/models/state.py`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `question` | `str` | Query original do usuário |
| `intent` | `dict` | Intent parsed: entities, action, filters, fields |
| `api_plan` | `list[dict]` | Steps de execução planejados |
| `api_results` | `dict` | Resultados das chamadas API |
| `processed_data` | `dict` | Dados processados e formatados |
| `final_answer` | `str` | Resposta final em linguagem natural |
| `error` | `str` | Erro se houver |
| `user_confirmation` | `dict` | Confirmação do usuário para ações destrutivas |

### 2.4 Taxonomia de Respostas (11 tipos)

O `AnswerFormatterAgent` usa uma taxonomia fixa:

| Tipo | Quando Usar |
|------|-------------|
| `ACTION_SUCCESS` | Ação executada com sucesso (create/update/delete) |
| `ACTION_FAILED` | Ação falhou |
| `COUNT` | Contagem ("quantos candidatos?") |
| `AGGREGATION` | Médias, somas, distribuições |
| `COMPARISON` | Comparação entre entidades |
| `NOT_FOUND` | 0 resultados |
| `ENTITY_DETAIL` | 1 resultado detalhado |
| `ENTITY_LIST` | 2-15 resultados em lista |
| `DISAMBIGUATION` | Múltiplos resultados quando 1 era esperado |
| `ERROR` | Erro formatado para o usuário |
| `CONVERSATIONAL` | Resposta conversacional |

---

## 3. Sistema Multi-Domínio

O sistema opera com domínios especializados que processam queries dentro de seu escopo. Cada domínio herda de `DomainPrompt` (base abstrata).

### 3.1 Registro de Domínios

Domínios são registrados via decorator `@register_domain` em `src/domains/registry.py`.

### 3.2 Classe Base (`DomainPrompt`)

Definida em `src/domains/base.py`:

```
DomainPrompt (ABC)
├── domain_id: str          — identificador único
├── domain_name: str        — nome legível
├── description: str        — descrição para o router
├── get_allowed_actions()   — lista de ações disponíveis
├── get_system_prompt()     — system prompt para o LLM
├── process_intent()        — classifica intent dentro do domínio
├── execute_action()        — executa a ação identificada
└── format_response()       — formata resposta do domínio
```

### 3.3 Estruturas de Dados Compartilhadas

| Classe | Descrição |
|--------|-----------|
| `DomainAction` | Define uma ação: id, nome, descrição, tipo (QUERY/AGGREGATE/ANALYZE/ACTION), exemplos |
| `DomainContext` | Contexto da sessão: domain_id, dados atuais, metadata, IDs selecionados, auth_token, api_calls_history |
| `DomainResponse` | Resposta: success, message, data, suggestions, needs_confirmation, needs_clarification |
| `APICallRecord` | Registro de chamada API: endpoint, method, params, duration_ms, status_code |
| `ActionType` | Enum: QUERY, AGGREGATE, ANALYZE, ACTION |

---

## 4. Comunicação e Integração

### 4.1 Comunicação com ATS API

Cada domínio tem seu próprio `api_client.py` que faz chamadas REST ao `ats_api` (Rails):

```
Domínio → api_client.py → HTTP REST → ats_api (Rails) → PostgreSQL
```

Autenticação: JWT token passado via `DomainContext.auth_token`.

### 4.2 Comunicação com Frontend

Dois mecanismos:

| Mecanismo | Uso | Implementação |
|-----------|-----|--------------|
| **RabbitMQ** | Assíncrono — queries longas, batch operations | `BaseDispatcher` + Celery workers |
| **REST API** | Síncrono — queries simples, streaming | `src/api.py` (FastAPI) |

### 4.3 Message Router

O `MessageRouter` (`src/services/message_router.py`) recebe mensagens do frontend e roteia para o domínio correto baseado no contexto:

1. Extrai domínio do metadata da mensagem
2. Identifica se é query nova ou continuação de conversa
3. Despacha para o `DomainPrompt` correspondente
4. Retorna resposta via callback ao Rails

### 4.4 Callbacks para Rails

O `send_to_rails_callback` envia respostas de volta ao Rails via HTTP POST, que propaga via ActionCable/WebSocket ao frontend.

---

## 5. Serviços Transversais

### 5.1 Circuit Breaker

Implementado em `src/services/circuit_breaker.py`:

| Config | Valor Default |
|--------|--------------|
| Failure threshold | 3 falhas |
| Cooldown | 30 segundos |
| Retry delay | 1 segundo |

Comportamento: após 3 falhas consecutivas, o circuito "abre" e rejeita chamadas por 30s. Após o cooldown, permite uma tentativa (half-open).

### 5.2 LLM Factory

`src/utils/llm_factory.py` — factory centralizada para criar instâncias de LLM com tracking:

```python
create_tracked_llm(
    temperature=0.0,          # 0.0 para determinismo
    service_name="...",       # para tracking (ex: "AppliesDomain")
    operation="chat|intent",  # tipo de operação
    model_override=None,      # override do modelo (default: settings.gemini.model)
    max_output_tokens=None,   # limite de tokens
)
```

### 5.3 RAG Service

`src/services/rag_service.py` — Retrieval-Augmented Generation para documentação de APIs. Usado pelo `IntentAnalyzerAgent` e `APIPlannerAgent` para consultar docs de ferramentas disponíveis.

### 5.4 Memory Service

`src/services/memory_service.py` — Persistência de conversas em PostgreSQL. Opcional — sistema funciona 100% via REST APIs mesmo sem memória.

### 5.5 Thinking Message Service

`src/services/thinking_message.py` — Envia status de "pensamento" ao frontend durante processamento:

| Status | Descrição |
|--------|-----------|
| `planning` | Analisando a query |
| `executing` | Executando chamadas API |
| `processing` | Processando dados |
| `formatting` | Formatando resposta |

---

## 6. Evaluation Graph (Sub-sistema)

O domínio `evaluation` tem seu próprio LangGraph independente para avaliação de candidatos em entrevistas.

### 6.1 Fluxo do Evaluation Graph

```
[classify_input] ─── answer? ─── [evaluate] ─── [decide_flow] ─── [craft_message] ─── END
       │                                              │
       └── not answer? ──────────── [decide_flow] ────┘
```

### 6.2 Nós do Evaluation Graph

| Nó | Função |
|----|--------|
| `classify_input` | Classifica input do candidato: answer, question, off_topic, unclear, not_interested |
| `evaluate` | Avalia resposta com rubrica: relevância (30%), profundidade (30%), clareza (20%), exemplos (20%) |
| `decide_flow` | Decide próximo passo: continuar, fazer follow-up, encerrar |
| `craft_message` | Gera mensagem para o candidato com persona configurável |

### 6.3 Estado do Interview (`InterviewState`)

| Campo | Tipo |
|-------|------|
| `account_id` | int |
| `evaluation_candidate_id` | int |
| `job_description` | str |
| `question_text` | str |
| `expected_response` | str |
| `candidate_answer` | str |
| `classification` | InputClassification |
| `evaluation` | RubricEvaluation |
| `flow_decision` | FlowDecision |
| `final_message` | CandidateMessage |
| `final_score` | float |
| `is_satisfactory` | bool |

### 6.4 Segurança

`src/domains/evaluation/security.py` — Proteção contra prompt injection nas respostas dos candidatos:
- Sanitização de input
- Detecção de padrões de injeção
- Criação de contexto seguro (safe context)

---

## 7. Autonomous Agent (ReAct)

O domínio `autonomous` implementa um agente ReAct universal com acesso a ~73 ferramentas que cobrem toda a API do ATS.

### 7.1 Arquitetura

```
UniversalReActAgent
├── Tools (~73 ferramentas)
│   ├── applies.py     — busca, pipeline, scoring, bulk
│   ├── candidates.py  — CRUD, busca, perfis
│   ├── jobs.py        — CRUD, publicação, templates
│   ├── evaluations.py — avaliações, rubricas
│   ├── sourcing.py    — sourcing externo
│   ├── scheduling.py  — agendamentos
│   ├── organization.py — departamentos, estrutura
│   ├── macros.py      — playbooks compostos
│   └── file_system.py — export, relatórios
├── Playbooks (YAML)
│   ├── diagnostico_vaga.yaml
│   ├── panorama_vagas.yaml
│   ├── sourcing_completo.yaml
│   ├── triagem_vaga.yaml
│   └── weekly_review.yaml
└── Context Builder
    └── Resolve referências UI (viewing_entities)
```

### 7.2 Resolução de Contexto UI

O agente autônomo resolve referências implícitas na seguinte prioridade:
1. `viewing_entities` — entidades na tela do usuário (mais confiável)
2. Contexto da sessão (IDs ativos)
3. URL atual (`current_path`)
4. Perguntar ao usuário (último recurso)

---

## 8. Fairness Guard

Implementado em `src/domains/jobs/fairness.py`:

### 8.1 Filtros Bloqueados

```
gender, genero, sexo, age, idade, birth_date, data_nascimento,
race, raca, raça, ethnicity, etnia, marital, estado_civil,
religion, religiao, religião
```

### 8.2 Filtros Condicionais

| Filtro | Condição |
|--------|----------|
| PCD/disability | Só permitido se `job.disabilities == true` |

### 8.3 Disclaimers Obrigatórios

- **Matching**: aviso que o matching é baseado em fit técnico, requer revisão humana
- **Bulk actions**: aviso que ações em lote afetam múltiplos candidatos

---

## 9. Deploy Topology

| Componente | Deploy | Porta |
|-----------|--------|-------|
| ats_api (Rails) | Cloud (GCP) | 8080 |
| ats_front (Nuxt) | Cloud | 3000 |
| recruiter_agent_v5 | Cloud (GCP) + Workers | 8000 |
| lia-agent-system | Replit | 8000 |
| RabbitMQ | CloudAMQP | 5672 |
| PostgreSQL | Cloud | 5432/5433 |
| LangSmith | SaaS | — |

---

## 10. Contratos de Integração

### 10.1 recruiter_agent_v5 → ats_api

| Tipo | Protocolo | Auth |
|------|-----------|------|
| REST API | HTTP/HTTPS | JWT Bearer Token |

O `ATSAPIClient` (`src/services/api_client.py`) faz login com username/password, recebe JWT, e usa em todas as chamadas subsequentes.

### 10.2 ats_front → recruiter_agent_v5

| Tipo | Protocolo | Mecanismo |
|------|-----------|-----------|
| Chat message | RabbitMQ | Queue por sessão/domínio |
| Streaming | WebSocket via Rails ActionCable | Push de status e respostas parciais |

### 10.3 recruiter_agent_v5 → LLM

| Provider | Modelo Default | Biblioteca |
|----------|---------------|-----------|
| Google Gemini | `gemini-2.5-flash` | `langchain-google-genai` |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Workflow Graph | `recruiter_agent_v5/src/workflow/graph.py` |
| Settings | `recruiter_agent_v5/src/config/settings.py` |
| Base Domain | `recruiter_agent_v5/src/domains/base.py` |
| LLM Factory | `recruiter_agent_v5/src/utils/llm_factory.py` |
| Circuit Breaker | `recruiter_agent_v5/src/services/circuit_breaker.py` |
| Evaluation Graph | `recruiter_agent_v5/src/domains/evaluation/graph.py` |
| Autonomous Agent | `recruiter_agent_v5/src/domains/autonomous/agent.py` |
| Fairness Guard | `recruiter_agent_v5/src/domains/jobs/fairness.py` |
