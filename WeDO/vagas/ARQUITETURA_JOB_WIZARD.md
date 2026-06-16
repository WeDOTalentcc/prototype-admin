# 🏗️ Arquitetura Completa do Job Creation Wizard

> **Plataforma LIA** - Learning Intelligence Assistant  
> Documento de Arquitetura Técnica v1.0  
> Data: Fevereiro 2026

---

## 📋 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Fluxo End-to-End de Mensagem](#3-fluxo-end-to-end-de-mensagem)
4. [Componentes Detalhados](#4-componentes-detalhados)
5. [Grafo de Agentes (JobWizardGraph)](#5-grafo-de-agentes-jobwizardgraph)
6. [Stages do Wizard](#6-stages-do-wizard)
7. [Fluxo de Dados](#7-fluxo-de-dados)
8. [Persistência no Banco de Dados](#8-persistência-no-banco-de-dados)
9. [Mapa de Conexões](#9-mapa-de-conexões)
10. [Status de Integração](#10-status-de-integração)

---

## 1. Visão Geral do Sistema

O Job Creation Wizard é um sistema conversacional alimentado por IA que permite a criação de vagas de emprego através de diálogo natural com a LIA (Learning Intelligence Assistant).

### Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                         PLATAFORMA LIA                                  │
│                                                                         │
│   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐      │
│   │               │      │               │      │               │      │
│   │   FRONTEND    │ ───► │   PROXY API   │ ───► │    BACKEND    │      │
│   │   Next.js     │      │   Next.js     │      │    FastAPI    │      │
│   │   :5000       │ ◄─── │   :5000       │ ◄─── │    :8000      │      │
│   │               │      │               │      │               │      │
│   └───────────────┘      └───────────────┘      └───────────────┘      │
│                                                        │               │
│                                                        │               │
│                                                        ▼               │
│                                               ┌───────────────┐        │
│                                               │               │        │
│                                               │  JobWizard    │        │
│                                               │    Graph      │        │
│                                               │  (6 Nodes)    │        │
│                                               │               │        │
│                                               └───────┬───────┘        │
│                                                       │                │
│                                          ┌────────────┼────────────┐   │
│                                          │            │            │   │
│                                          ▼            ▼            ▼   │
│                                   ┌──────────┐ ┌──────────┐ ┌─────────┐│
│                                   │  Gemini  │ │  60      │ │Postgres ││
│                                   │  2.5     │ │  Tools   │ │   DB    ││
│                                   │  Flash   │ │          │ │         ││
│                                   └──────────┘ └──────────┘ └─────────┘│
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stack Tecnológica

### Frontend
| Tecnologia | Versão | Função |
|------------|--------|--------|
| Next.js | 15.5.6 | Framework React |
| React | 18.x | UI Library |
| TypeScript | 5.x | Type Safety |
| Tailwind CSS | 3.x | Styling |
| shadcn/ui | - | Component Library |

### Backend
| Tecnologia | Versão | Função |
|------------|--------|--------|
| FastAPI | 0.100+ | Web Framework |
| Python | 3.11 | Runtime |
| SQLAlchemy | 2.x | ORM |
| Pydantic | 2.x | Validation |
| LangGraph-style | Custom | Agent Orchestration |

### AI/LLM
| Tecnologia | Modelo | Função |
|------------|--------|--------|
| Google Gemini | 2.5 Flash | Intent, Extraction, Response |
| Anthropic Claude | Sonnet | Backup/Complex Tasks |

### Database
| Tecnologia | Provider | Função |
|------------|----------|--------|
| PostgreSQL | Neon/Replit | Persistence |
| pgvector | Extension | Embeddings |

---

## 3. Fluxo End-to-End de Mensagem

### Diagrama Sequencial

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│RECRUTADOR│    │ FRONTEND │    │  PROXY   │    │ BACKEND  │    │   LLM    │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │               │
     │ 1. "Preciso   │               │               │               │
     │    de um dev  │               │               │               │
     │    Python"    │               │               │               │
     │──────────────►│               │               │               │
     │               │               │               │               │
     │               │ 2. orchestrate│               │               │
     │               │    WizardMsg()│               │               │
     │               │──────────────►│               │               │
     │               │               │               │               │
     │               │               │ 3. POST       │               │
     │               │               │ /smart-orch   │               │
     │               │               │──────────────►│               │
     │               │               │               │               │
     │               │               │               │ 4. Intent     │
     │               │               │               │    Classify   │
     │               │               │               │──────────────►│
     │               │               │               │               │
     │               │               │               │◄──────────────│
     │               │               │               │ "start_from   │
     │               │               │               │  _scratch"    │
     │               │               │               │  (0.90)       │
     │               │               │               │               │
     │               │               │               │ 5. Generate   │
     │               │               │               │    Response   │
     │               │               │               │──────────────►│
     │               │               │               │               │
     │               │               │               │◄──────────────│
     │               │               │               │ "Ótimo! Vamos │
     │               │               │               │  criar..."    │
     │               │               │               │               │
     │               │               │◄──────────────│               │
     │               │               │ 6. Response   │               │
     │               │               │    JSON       │               │
     │               │               │               │               │
     │               │◄──────────────│               │               │
     │               │ 7. Process    │               │               │
     │               │    Response   │               │               │
     │               │               │               │               │
     │◄──────────────│               │               │               │
     │ 8. LIA msg    │               │               │               │
     │    displayed  │               │               │               │
     │               │               │               │               │
```

### Descrição das Etapas

| Etapa | Origem | Destino | Ação |
|-------|--------|---------|------|
| 1 | Recrutador | Frontend | Digita mensagem no chat |
| 2 | Frontend | lia-api.ts | Chama `orchestrateWizardMessage()` |
| 3 | Proxy | Backend | POST `/api/v1/wizard/smart-orchestrate` |
| 4 | Backend | Gemini | Intent classification |
| 5 | Backend | Gemini | Response generation |
| 6 | Backend | Proxy | Retorna `SmartOrchestrateResponse` |
| 7 | Proxy | Frontend | `processOrchestratorResponse()` |
| 8 | Frontend | Recrutador | Exibe mensagem da LIA |

---

## 4. Componentes Detalhados

### 4.1 Frontend

```
plataforma-lia/
├── src/
│   ├── components/
│   │   └── expanded-chat-modal.tsx    ◄── Chat principal (7000+ linhas)
│   │
│   ├── services/
│   │   └── lia-api.ts                 ◄── Cliente API (4600+ linhas)
│   │       └── orchestrateWizardMessage()  (linha 3989)
│   │
│   ├── app/api/backend-proxy/
│   │   └── wizard/smart-orchestrate/
│   │       └── route.ts               ◄── Proxy Next.js → FastAPI
│   │
│   └── components/expanded-chat/config/
│       └── wizard-config.ts           ◄── Stage mappings
```

### 4.2 Backend

```
lia-agent-system/
├── app/
│   ├── api/v1/
│   │   └── wizard_smart_orchestrator.py   ◄── Endpoint principal
│   │
│   ├── agents/
│   │   ├── job_wizard_graph.py            ◄── Grafo LangGraph-style
│   │   ├── nodes.py                       ◄── 6 nós do grafo (1274 linhas)
│   │   └── state_machine.py               ◄── Tipos e estados
│   │
│   ├── services/
│   │   ├── llm.py                         ◄── Integração Gemini/Claude
│   │   └── job_vacancy_service.py         ◄── Persistência DB
│   │
│   └── tools/
│       ├── registry.py                    ◄── 60 tools registradas
│       └── executor.py                    ◄── Executor de tools
```

---

## 5. Grafo de Agentes (JobWizardGraph)

### Estrutura do Grafo

```
                              ┌─────────────────────┐
                              │       START         │
                              └──────────┬──────────┘
                                         │
                                         ▼
                    ┌────────────────────────────────────────┐
                    │         INTENT_CLASSIFIER              │
                    │                                        │
                    │  • Analisa mensagem do usuário         │
                    │  • Classifica intenção                 │
                    │  • Retorna: WizardIntent + confidence  │
                    │                                        │
                    │  🤖 LLM Call: Gemini 2.5 Flash         │
                    │  ⏱️  Duração: ~2 segundos              │
                    └────────────────┬───────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ START_FROM_     │    │ PROVIDE_INFO    │    │ CONFIRM/SKIP/   │
    │ SCRATCH /       │    │ MODIFY          │    │ GO_BACK         │
    │ USE_EXISTING    │    │                 │    │                 │
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                      │                      │
             │                      ▼                      │
             │        ┌────────────────────────────┐       │
             │        │     FIELD_EXTRACTOR        │       │
             │        │                            │       │
             │        │  • Extrai campos da msg    │       │
             │        │  • Atualiza job_draft      │       │
             │        │  • Calcula confidence      │       │
             │        │                            │       │
             │        │  🤖 LLM Call: Gemini       │       │
             │        │  ⏱️  Duração: ~1.5s        │       │
             │        └─────────────┬──────────────┘       │
             │                      │                      │
             │                      ▼                      │
             │        ┌────────────────────────────┐       │
             │        │       TOOL_ROUTER          │       │
             │        │                            │       │
             │        │  • Decide tools a chamar   │       │
             │        │  • Baseado em stage/intent │       │
             │        │                            │       │
             │        │  ❌ Sem LLM (lógica)       │       │
             │        │  ⏱️  Duração: <10ms        │       │
             │        └─────────────┬──────────────┘       │
             │                      │                      │
             │              ┌───────┴───────┐              │
             │              │ tools_to_call │              │
             │              │     > 0?      │              │
             │              └───────┬───────┘              │
             │                      │                      │
             │            ┌─────────┴─────────┐            │
             │            │                   │            │
             │            ▼                   │            │
             │  ┌─────────────────────┐       │            │
             │  │   TOOL_EXECUTOR     │       │            │
             │  │                     │       │            │
             │  │  • Executa tools    │       │            │
             │  │  • Benchmark salário│       │            │
             │  │  • Skills catalog   │       │            │
             │  │  • Company config   │       │            │
             │  │                     │       │            │
             │  │  ❌ Sem LLM         │       │            │
             │  │  ⏱️  ~500ms        │       │            │
             │  └──────────┬──────────┘       │            │
             │             │                  │            │
             │             └────────┬─────────┘            │
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────────────┐
                    │        RESPONSE_GENERATOR              │
                    │                                        │
                    │  • Gera resposta natural da LIA        │
                    │  • Inclui resumo de campos detectados  │
                    │  • Pergunta de confirmação             │
                    │  • Usa prompt especializado por stage  │
                    │                                        │
                    │  🤖 LLM Call: Gemini 2.5 Flash         │
                    │  ⏱️  Duração: ~2 segundos              │
                    └────────────────┬───────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────────────┐
                    │         STAGE_TRANSITION               │
                    │                                        │
                    │  • Avalia se pode avançar              │
                    │  • CONFIRMATION GATE para stages       │
                    │    críticos (salary, competencies...)  │
                    │  • Bloqueia até receber CONFIRM        │
                    │                                        │
                    │  ❌ Sem LLM (lógica)                   │
                    │  ⏱️  Duração: <10ms                    │
                    └────────────────┬───────────────────────┘
                                     │
                              ┌──────┴──────┐
                              │ stage ==    │
                              │ "complete"? │
                              └──────┬──────┘
                                     │
                      ┌──────────────┴──────────────┐
                      │                             │
                      ▼                             ▼
            ┌─────────────────┐           ┌─────────────────┐
            │  PERSIST TO DB  │           │      END        │
            │                 │           │                 │
            │  job_vacancy_   │           │  Return         │
            │  service.       │           │  Response       │
            │  create_from_   │           │                 │
            │  wizard_draft() │           │                 │
            └────────┬────────┘           └─────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   PostgreSQL    │
            │                 │
            │  job_vacancies  │
            │     table       │
            └─────────────────┘
```

### Tabela de Nós

| Nó | Função | LLM? | Duração |
|----|--------|------|---------|
| `intent_classifier` | Classifica intenção do usuário | ✅ Gemini | ~2s |
| `field_extractor` | Extrai campos da mensagem | ✅ Gemini | ~1.5s |
| `tool_router` | Decide quais tools chamar | ❌ Lógica | <10ms |
| `tool_executor` | Executa tools (benchmark, skills) | ❌ Services | ~500ms |
| `response_generator` | Gera resposta natural da LIA | ✅ Gemini | ~2s |
| `stage_transition` | Avalia transição + confirmation gate | ❌ Lógica | <10ms |

### Intents Suportados

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WIZARD INTENTS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INICIAIS (escolha de jornada):                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ START_FROM_SCRATCH  │ Criar vaga do zero                        │    │
│  │ USE_EXISTING        │ Duplicar/adaptar vaga existente           │    │
│  │ USE_TEMPLATE        │ Usar template do catálogo                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  PADRÃO:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ PROVIDE_INFO   │ Fornecendo informações (cargo, salário, etc.)  │    │
│  │ ASK_QUESTION   │ Fazendo uma pergunta                           │    │
│  │ CONFIRM        │ Confirmando/aceitando algo                     │    │
│  │ REJECT         │ Rejeitando/recusando algo                      │    │
│  │ MODIFY         │ Querendo modificar algo já informado           │    │
│  │ SKIP           │ Pulando etapa atual                            │    │
│  │ GO_BACK        │ Voltando à etapa anterior                      │    │
│  │ HELP           │ Pedindo ajuda                                  │    │
│  │ UNKNOWN        │ Não foi possível determinar                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Stages do Wizard

### Mapeamento Frontend ↔ Backend

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     STAGE MAPPING                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   BACKEND STAGE          FRONTEND STAGE         REQUER CONFIRMAÇÃO?     │
│   ─────────────          ──────────────         ────────────────────    │
│                                                                         │
│   initial            ──► input-evaluation           ✅ SIM              │
│   title_department   ──► input-evaluation           ✅ SIM              │
│   job_summary        ──► job-summary                ✅ SIM              │
│   salary             ──► salary                     ✅ SIM              │
│   competencies       ──► competencies               ✅ SIM              │
│   screening          ──► wsi-questions              ✅ SIM              │
│   review             ──► review-publish             ✅ SIM              │
│   search_calibration ──► search-calibration         ❌ NÃO              │
│   complete           ──► complete                   ❌ NÃO              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Jornada Ideal

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        JORNADA DE CRIAÇÃO DE VAGA                        │
└──────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────┐
     │                  │
  1  │ INPUT-EVALUATION │  Cargo, departamento, gestor, responsabilidades
     │                  │
     └────────┬─────────┘
              │
              │ ✅ Confirmação do usuário
              ▼
     ┌──────────────────┐
     │                  │
  2  │     SALARY       │  Faixa salarial + benchmark de mercado
     │                  │
     └────────┬─────────┘
              │
              │ ✅ Confirmação do usuário
              ▼
     ┌──────────────────┐
     │                  │
  3  │  COMPETENCIES    │  Skills técnicas e comportamentais
     │                  │
     └────────┬─────────┘
              │
              │ ✅ Confirmação do usuário
              ▼
     ┌──────────────────┐
     │                  │
  4  │  WSI-QUESTIONS   │  Perguntas de triagem (screening)
     │                  │
     └────────┬─────────┘
              │
              │ ✅ Confirmação do usuário
              ▼
     ┌──────────────────┐
     │                  │
  5  │ REVIEW-PUBLISH   │  Revisão final e publicação
     │                  │
     └────────┬─────────┘
              │
              │ ✅ Confirmação do usuário
              ▼
     ┌──────────────────┐
     │                  │
  6  │    COMPLETE      │  Vaga criada no banco de dados!
     │                  │     🎉
     └──────────────────┘
```

---

## 7. Fluxo de Dados

### Request (Frontend → Backend)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SmartOrchestrateRequest                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  {                                                                      │
│    "message": "Preciso de um desenvolvedor Python senior",              │
│                                                                         │
│    "current_stage": "input-evaluation",                                 │
│                      ▲                                                  │
│                      │ Frontend format                                  │
│                                                                         │
│    "collected_data": {                                                  │
│      "job_title": "Dev Backend",                                        │
│      "department": "Tecnologia",                                        │
│      "salary_min": 15000                                                │
│    },                                                                   │
│                                                                         │
│    "conversation_history": [                                            │
│      { "role": "user", "content": "Oi LIA" },                           │
│      { "role": "assistant", "content": "Olá! Como posso ajudar?" }      │
│    ],                                                                   │
│                                                                         │
│    "conversation_id": "uuid-session-123",                               │
│    "company_id": "company-abc",                                         │
│    "user_id": "user@example.com"                                        │
│  }                                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### State (Interno do Grafo)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       JobWizardState                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  {                                                                      │
│    "messages": [                                                        │
│      { "role": "user", "content": "..." },                              │
│      { "role": "assistant", "content": "..." }                          │
│    ],                                                                   │
│                                                                         │
│    "current_stage": "title_department",  ◄── Backend format             │
│                                                                         │
│    "job_draft": {                        ◄── Acumula todos os campos    │
│      "title": "Desenvolvedor Python",                                   │
│      "department": "Tecnologia",                                        │
│      "seniority": "Senior",                                             │
│      "salary_min": 15000,                                               │
│      "salary_max": 20000                                                │
│    },                                                                   │
│                                                                         │
│    "confidence_scores": {                                               │
│      "title": 0.95,                                                     │
│      "department": 0.85,                                                │
│      "salary_min": 0.90                                                 │
│    },                                                                   │
│                                                                         │
│    "intent": "provide_info",                                            │
│    "extracted_fields": { "job_title": "desenvolvedor Python" },         │
│                                                                         │
│    "tool_calls": [                                                      │
│      { "name": "search_salary_benchmark", "params": {...} }             │
│    ],                                                                   │
│    "tool_results": [                                                    │
│      { "name": "search_salary_benchmark", "result": {...} }             │
│    ],                                                                   │
│                                                                         │
│    "response_text": "Ótimo! Registrei...",                              │
│    "awaiting_confirmation": true,                                       │
│    "auto_transition": false,                                            │
│    "should_continue": false                                             │
│  }                                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Response (Backend → Frontend)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SmartOrchestrateResponse                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  {                                                                      │
│    "success": true,                                                     │
│                                                                         │
│    "lia_message": "Ótimo! Vamos criar sua vaga do zero. Entendi que     │
│                    você precisa de um 'desenvolvedor Python'.\n\n       │
│                    📋 **Informações da Vaga:**\n                        │
│                    Registrei o cargo como **Desenvolvedor Python**.\n   │
│                    \n✨ Posso avançar para remuneração?",               │
│                                                                         │
│    "detected_criteria": {                                               │
│      "job_title": "desenvolvedor Python"                                │
│    },                                                                   │
│                                                                         │
│    "next_stage": null,           ◄── null = não avançou                 │
│    "auto_transition": false,     ◄── não transicionar automaticamente   │
│    "awaiting_confirmation": true,◄── bloqueado esperando confirmação    │
│                                                                         │
│    "tool_results": [],                                                  │
│                                                                         │
│    "confidence": 0.90,                                                  │
│    "intent": "start_from_scratch",                                      │
│                                                                         │
│    "reasoning_steps": [                                                 │
│      "[intent_classifier] Classified: start_from_scratch (0.90)",       │
│      "[response_generator] Generated response (2.1s)",                  │
│      "[stage_transition] Blocked - awaiting confirmation"               │
│    ],                                                                   │
│                                                                         │
│    "error": null,                                                       │
│    "job_vacancy_id": null,       ◄── Preenchido quando stage=complete   │
│    "job_published": false                                               │
│  }                                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Persistência no Banco de Dados

### Fluxo de Criação de Vaga

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE PERSISTÊNCIA                                 │
└──────────────────────────────────────────────────────────────────────────┘


  STAGE_TRANSITION detecta:
  current_stage == "complete"
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  wizard_smart_orchestrator.py (linha 327-341)                           │
│                                                                         │
│  if current_backend_stage == WizardStage.COMPLETE.value:                │
│      merged_draft = {**request.collected_data, **detected_criteria}     │
│                                                                         │
│      job_vacancy_id = await finalize_job_vacancy_from_wizard(           │
│          job_draft=merged_draft,                                        │
│          session_id=session_id,                                         │
│          company_id=company_id,                                         │
│          user_id=user_id,                                               │
│      )                                                                  │
│                                                                         │
│      if job_vacancy_id:                                                 │
│          job_published = True                                           │
│          logger.info("🎉 Job vacancy created!")                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  finalize_job_vacancy_from_wizard() (linha 174-233)                     │
│                                                                         │
│  PASSO 1: IDEMPOTENCY CHECK                                             │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  existing = await db.execute(                                           │
│      select(JobVacancy).where(                                          │
│          JobVacancy.conversation_id == conv_uuid                        │
│      )                                                                  │
│  )                                                                      │
│                                                                         │
│  if existing_job:                                                       │
│      logger.info("⚠️ Job already exists!")                              │
│      return str(existing_job.id)  ◄── Retorna ID existente              │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  PASSO 2: CREATE                                                        │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  job_vacancy = await job_vacancy_service.create_from_wizard_draft(      │
│      draft=job_draft,                                                   │
│      conversation_id=session_id,                                        │
│      created_by=user_id,                                                │
│      company_id=company_id,                                             │
│      db=db,                                                             │
│  )                                                                      │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  PASSO 3: COMMIT                                                        │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  await db.commit()                                                      │
│  await db.refresh(job_vacancy)                                          │
│  return str(job_vacancy.id)                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  job_vacancy_service.create_from_wizard_draft() (linha 603+)            │
│                                                                         │
│  FIELD NORMALIZATION:                                                   │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  • title = draft.get("title") or draft.get("job_title")                 │
│  • technical_requirements = _normalize_skills_to_objects(raw_skills)    │
│  • salary_range = _normalize_salary_range(salary)                       │
│  • screening_questions = _normalize_questions(questions)                │
│                                                                         │
│  CREATE JobVacancy ORM object                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          PostgreSQL                                     │
│                                                                         │
│  INSERT INTO job_vacancies (                                            │
│      id,                                                                │
│      title,                                                             │
│      department,                                                        │
│      seniority,                                                         │
│      location,                                                          │
│      salary_range,              ◄── JSONB                               │
│      technical_requirements,    ◄── JSONB                               │
│      behavioral_competencies,   ◄── JSONB                               │
│      screening_questions,       ◄── JSONB                               │
│      created_by,                                                        │
│      company_id,                                                        │
│      conversation_id,           ◄── Para idempotency check              │
│      status,                    ◄── "draft"                             │
│      created_at,                                                        │
│      updated_at                                                         │
│  ) RETURNING id;                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Mapa de Conexões

### Diagrama Completo de Conexões

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                           MAPA DE CONEXÕES COMPLETO                                  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘


  ┌──────────────────┐
  │    RECRUTADOR    │
  │                  │
  │  "Preciso de um  │
  │   dev Python"    │
  │                  │
  └────────┬─────────┘
           │
           │ (1) Input no chat
           │
           ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│   FRONTEND  │  plataforma-lia/                                                     │
│   ──────────┴──────────────────────────────────────────────────────────────────    │
│                                                                                    │
│   expanded-chat-modal.tsx                                                          │
│       │                                                                            │
│       │ (2) Linha 7055: chama função                                               │
│       ▼                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │  orchestrateWizardMessage({                                                 │  │
│   │    message: "Preciso de um dev Python",                                     │  │
│   │    current_stage: "input-evaluation",                                       │  │
│   │    collected_data: {...},                                                   │  │
│   │    conversation_history: [...],                                             │  │
│   │    company_id: "...",                                                       │  │
│   │    user_id: "..."                                                           │  │
│   │  })                                                                         │  │
│   └──────────────────────────────────────────────────────────┬──────────────────┘  │
│                                                              │                     │
│   lia-api.ts                                                 │                     │
│       │                                                      │                     │
│       │ (3) Linha 3997                                       │                     │
│       ▼                                                      │                     │
│   ┌─────────────────────────────────────────────────────┐    │                     │
│   │  fetch('/api/backend-proxy/wizard/smart-orchestrate/')   │                     │
│   └──────────────────────────────────────────────────────────┘                     │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
           │
           │ (4) HTTP POST
           │
           ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│   PROXY  │  plataforma-lia/src/app/api/backend-proxy/wizard/smart-orchestrate/    │
│   ───────┴─────────────────────────────────────────────────────────────────────    │
│                                                                                    │
│   route.ts                                                                         │
│       │                                                                            │
│       │ (5) Linha 15: Repassa para backend                                         │
│       ▼                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │  fetch('http://127.0.0.1:8000/api/v1/wizard/smart-orchestrate', {...})      │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
           │
           │ (6) HTTP POST
           │
           ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│   BACKEND  │  lia-agent-system/                                                    │
│   ─────────┴───────────────────────────────────────────────────────────────────    │
│                                                                                    │
│   wizard_smart_orchestrator.py                                                     │
│       │                                                                            │
│       │ (7) Linha 266: Mapeia stage                                                │
│       │     backend_stage = map_frontend_to_backend_stage()                        │
│       │                                                                            │
│       │ (8) Linha 273-294: Cria estado inicial                                     │
│       │     initial_state = JobWizardState(...)                                    │
│       │                                                                            │
│       │ (9) Linha 298: Executa grafo                                               │
│       ▼                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │  final_state = await job_wizard_graph.invoke(initial_state)                 │  │
│   └──────────────────────────────────────────────────────────┬──────────────────┘  │
│                                                              │                     │
└──────────────────────────────────────────────────────────────┼─────────────────────┘
                                                               │
                                                               │ (10)
                                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│   GRAPH  │  job_wizard_graph.py + nodes.py                                         │
│   ───────┴─────────────────────────────────────────────────────────────────────    │
│                                                                                    │
│   ┌────────────────────┐                                                           │
│   │ intent_classifier  │──────────────────────────────────────────────────────┐    │
│   │                    │                                                      │    │
│   │  Classifica        │                                                      │    │
│   │  intenção          │                                                      ▼    │
│   └────────────────────┘                                             ┌────────────┐│
│            │                                                         │  GEMINI    ││
│            │ (11)                                                    │  2.5 Flash ││
│            ▼                                                         │            ││
│   ┌────────────────────┐                                             │ (LLM Call) ││
│   │ response_generator │─────────────────────────────────────────────►            ││
│   │                    │                                             └────────────┘│
│   │  Gera resposta     │                                                           │
│   │  natural           │                                                           │
│   └────────────────────┘                                                           │
│            │                                                                       │
│            │ (12)                                                                  │
│            ▼                                                                       │
│   ┌────────────────────┐                                                           │
│   │ stage_transition   │                                                           │
│   │                    │                                                           │
│   │  CONFIRMATION GATE │                                                           │
│   │  ──────────────────│                                                           │
│   │  Bloqueia stages   │                                                           │
│   │  críticos até      │                                                           │
│   │  CONFIRM intent    │                                                           │
│   └────────────────────┘                                                           │
│            │                                                                       │
│            │ (13) Se stage == "complete"                                           │
│            ▼                                                                       │
│   ┌────────────────────┐         ┌─────────────────────┐                           │
│   │ finalize_job_      │────────►│  job_vacancy_       │                           │
│   │ vacancy_from_      │         │  service.           │                           │
│   │ wizard()           │         │  create_from_       │                           │
│   │                    │         │  wizard_draft()     │                           │
│   └────────────────────┘         └──────────┬──────────┘                           │
│                                             │                                      │
└─────────────────────────────────────────────┼──────────────────────────────────────┘
                                              │
                                              │ (14) INSERT
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│   DATABASE  │  PostgreSQL (Neon/Replit)                                            │
│   ──────────┴──────────────────────────────────────────────────────────────────    │
│                                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                         job_vacancies                                       │  │
│   ├─────────────────────────────────────────────────────────────────────────────┤  │
│   │  id                  │ UUID        │ PK                                     │  │
│   │  title               │ VARCHAR     │ "Desenvolvedor Python"                 │  │
│   │  department          │ VARCHAR     │ "Tecnologia"                           │  │
│   │  seniority           │ VARCHAR     │ "Senior"                               │  │
│   │  salary_range        │ JSONB       │ {"min": 15000, "max": 20000}           │  │
│   │  technical_reqs      │ JSONB       │ [{"name": "Python", "level": 4}]       │  │
│   │  screening_questions │ JSONB       │ [{"question": "...", "type": "text"}]  │  │
│   │  company_id          │ UUID        │ FK → companies                         │  │
│   │  conversation_id     │ UUID        │ Para idempotency                       │  │
│   │  created_by          │ VARCHAR     │ user@example.com                       │  │
│   │  status              │ VARCHAR     │ "draft"                                │  │
│   │  created_at          │ TIMESTAMP   │                                        │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
           │
           │ (15) Response volta pelo caminho inverso
           ▼
     ┌──────────────────┐
     │    RECRUTADOR    │
     │                  │
     │  Vê mensagem da  │
     │  LIA no chat     │
     │                  │
     └──────────────────┘
```

---

## 10. Status de Integração

### ✅ Todos os Componentes Funcionando

| Componente | Status | Evidência |
|------------|--------|-----------|
| **LLM (Gemini 2.5 Flash)** | ✅ OK | `HTTP/1.1 200 OK` em todas as chamadas |
| **Intent Classifier** | ✅ OK | 90% confiança em classificação |
| **Field Extractor** | ✅ OK | Detecta campos como `job_title`, `salary` |
| **Response Generator** | ✅ OK | Gera respostas naturais em português |
| **Confirmation Gate** | ✅ OK | Bloqueia stages críticos corretamente |
| **Stage Transitions** | ✅ OK | CONFIRM intent avança `title_department` → `job_summary` |
| **Tool Executor** | ✅ OK | Executa `search_salary_benchmark`, `get_company_config` com sucesso |
| **Persistência DB** | ✅ OK | Vagas criadas no PostgreSQL com ID único |
| **Idempotency Check** | ✅ OK | Mesmo ID retornado em tentativa duplicada |
| **Frontend → Backend Proxy** | ✅ OK | Proxy Next.js funciona corretamente |
| **60+ Tools Registered** | ✅ OK | Benchmark, skills catalog, company config |

### Métricas de Performance

| Métrica | Valor |
|---------|-------|
| Tempo médio de resposta | ~3.8 segundos |
| Tempo de execução de tools | ~8.3 segundos |
| Nós executados por mensagem | 3-6 (depende do stage) |
| Confiança média de intent | 0.90-1.00 |
| Tools registradas | 60+ |

---

## 11. Resultados dos Testes

### Teste 1: Stage Transitions

**Cenário:** Usuário confirma informações no stage `title_department`

```
Input:  "Sim, confirmo. Pode avançar."
Stage:  title_department
```

**Resultado:**
```
Intent detected: confirm
Final stage: job_summary
Awaiting confirmation: False
```

**Status:** ✅ PASSED - Stage avançou corretamente após confirmação

---

### Teste 2: Tool Executor

**Cenário:** Usuário fornece salário no stage `salary`

```
Input:  "O salário será entre 15000 e 20000 reais"
Stage:  salary
```

**Resultado:**
```
[tool_router] Routed 2 tool(s): ['search_salary_benchmark', 'get_company_config']
[tool_executor] Executed 2 tools, 2 successful (8292.7ms)

Tool results:
  ✅ search_salary_benchmark: OK
  ✅ get_company_config: OK
```

**Status:** ✅ PASSED - Tools executadas com sucesso

---

### Teste 3: Persistência no Banco

**Cenário:** Criar vaga de emprego quando wizard atinge stage `complete`

```python
{
    "title": "Engenheiro de Dados Pleno - TESTE FINAL",
    "department": "Data Engineering",
    "seniority": "Pleno",
    "technical_skills": ["Python", "Spark", "AWS", "SQL"]
}
```

**Resultado:**
```sql
SELECT id, title FROM job_vacancies WHERE title LIKE '%TESTE%';
-- 1f7ed796-b8b4-4579-b489-73230da0b4eb | Engenheiro de Dados Pleno - TESTE FINAL
```

**Status:** ✅ PASSED - Vaga criada com UUID único

---

### Teste 4: Idempotency Check

**Cenário:** Tentar criar a mesma vaga duas vezes com o mesmo `session_id`

**Resultado:**
```
>>> Attempt 1: Create job
Job ID 1: 1f7ed796-b8b4-4579-b489-73230da0b4eb

>>> Attempt 2: Try to create duplicate
Job ID 2: 1f7ed796-b8b4-4579-b489-73230da0b4eb

✅ SUCCESS: Same ID returned for duplicate attempt
```

**Status:** ✅ PASSED - Idempotency funcionando

---

## 12. Correções Aplicadas

| Problema | Solução | Arquivo |
|----------|---------|---------|
| FK Constraint em `conversation_id` | Verifica se conversation existe antes de usar como FK | `wizard_smart_orchestrator.py` |
| UUID Validation | Valida formato antes de converter | `wizard_smart_orchestrator.py` |
| Idempotency com NULL FK | Busca por `additional_data->>'wizard_session_id'` | `wizard_smart_orchestrator.py` |
| Tools não registradas | Chama `initialize_tools()` na inicialização do graph | `job_wizard_graph.py` |

---

## 13. Comandos para Testes

```bash
cd lia-agent-system

# Teste de Persistência
python3 -c "
import asyncio
from uuid import uuid4
from app.api.v1.wizard_smart_orchestrator import finalize_job_vacancy_from_wizard

async def test():
    return await finalize_job_vacancy_from_wizard(
        job_draft={'title': 'Test Job', 'department': 'IT'},
        session_id=str(uuid4()),
        company_id='a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        user_id='test@example.com'
    )

print(asyncio.run(test()))
"

# Verificar no banco
psql -c \"SELECT id, title FROM job_vacancies ORDER BY created_at DESC LIMIT 5;\"
```

---

## 14. Sistema de Orquestração Inteligente de Dados

A partir da versão 1.3, o Job Wizard conta com um sistema de orquestração inteligente que consolida dados de múltiplas fontes com priorização baseada em confiança.

### 14.1 Arquitetura de 3 Camadas de Cache

```
┌─────────────────────────────────────────────────────────────────┐
│                   TOKEN ECONOMY ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   LAYER 1    │    │   LAYER 2    │    │   LAYER 3    │       │
│  │   Session    │ →  │    Redis     │ →  │  PostgreSQL  │       │
│  │   (1 hour)   │    │  (7 days)    │    │  (30 days)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│   In-memory          Short TTL           Long TTL               │
│   Per conversation   Volatile data       Stable patterns        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Componentes:**
- `CacheManagerService`: Orquestra as 3 camadas de cache
- `SessionCache`: Cache em memória por sessão de conversa
- `RedisCache`: Cache L1 para dados voláteis (fallback gracioso se indisponível)
- `PostgresCache`: Cache L2 para dados estáveis e padrões

### 14.2 Priorização de Fontes de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA SOURCE PRIORITY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRIORITY 1: Learning Patterns ───────── VERY_HIGH (95%)        │
│              (Preferências históricas da empresa)                │
│                          │                                       │
│  PRIORITY 2: Company Config ─────────── HIGH (85%)              │
│              (Políticas explícitas de RH)                        │
│                          │                                       │
│  PRIORITY 3: Job Insights ───────────── HIGH (85%)              │
│              (Dados internos da LIA)                             │
│                          │                                       │
│  PRIORITY 4: ATS History ────────────── MEDIUM (70%)            │
│              (Histórico de ATSs conectados)                      │
│                          │                                       │
│  PRIORITY 5: Market Benchmark ───────── LOW_MEDIUM (55%)        │
│              (Dados externos de mercado)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Componentes:**
- `IntelligentDataOrchestrator`: Consolida todas as fontes com pontuação de confiança
- `ATSJobHistoryService`: Busca JDs históricas de Gupy, Pandapé, StackOne, Merge

### 14.3 Sistema de Learning Loop Silencioso

```
┌─────────────────────────────────────────────────────────────────┐
│                   SILENT LEARNING LOOP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CAPTURE                 ANALYZE                  APPLY         │
│   ────────                ───────                  ─────         │
│   ┌─────────┐            ┌─────────┐            ┌─────────┐     │
│   │Feedback │ ────────►  │Learning │ ────────►  │Improved │     │
│   │Events   │            │Patterns │            │Suggest. │     │
│   └─────────┘            └─────────┘            └─────────┘     │
│        │                      │                      │           │
│        ▼                      ▼                      ▼           │
│   Silently records      Detects patterns       Uses patterns    │
│   accepted/modified/    from accumulated       for better       │
│   rejected values       feedback data          suggestions      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Componentes:**
- `LearningLoopService`: Captura feedback silencioso e gera padrões
- `FeedbackEvent`: Modelo de banco para eventos de feedback
- `LearningPattern`: Modelo de banco para padrões aprendidos

### 14.4 Novas Tools Registradas

| Tool | Descrição | Schema |
|------|-----------|--------|
| `get_intelligent_salary` | Busca salário de múltiplas fontes com priorização | GET_INTELLIGENT_SALARY_SCHEMA |
| `get_intelligent_skills` | Busca skills de múltiplas fontes consolidadas | GET_INTELLIGENT_SKILLS_SCHEMA |
| `capture_wizard_feedback` | Captura feedback silencioso para learning loop | CAPTURE_WIZARD_FEEDBACK_SCHEMA |

### 14.5 Modelos de Banco de Dados

```sql
-- Cache L2 (PostgreSQL)
CREATE TABLE cache_entries (
    id UUID PRIMARY KEY,
    cache_key VARCHAR(512) UNIQUE,
    namespace VARCHAR(100),
    company_id VARCHAR(255),
    value JSONB,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0
);

-- Eventos de Feedback (silenciosos)
CREATE TABLE feedback_events (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255),
    field_name VARCHAR(100),
    suggested_value JSONB,
    final_value JSONB,
    outcome VARCHAR(20),  -- accepted, modified, rejected
    processed_for_learning BOOLEAN DEFAULT FALSE
);

-- Padrões Aprendidos
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255),
    pattern_type VARCHAR(100),
    pattern_key VARCHAR(512),
    pattern_value JSONB,
    sample_size INTEGER,
    acceptance_rate FLOAT,
    confidence_score FLOAT
);
```

---

## Changelog

| Data | Versão | Alterações |
|------|--------|------------|
| 2026-02-04 | 1.3 | Sistema de Orquestração Inteligente (3-layer cache, learning loop, ATS history) |
| 2026-02-04 | 1.2 | Correção do Tool Executor (initialize_tools), documentos unificados |
| 2026-02-04 | 1.1 | Testes executados, correções de FK/idempotency |
| 2026-02-04 | 1.0 | Documento inicial |

---

*Documento atualizado em 2026-02-04. Todos os testes passaram com sucesso.*
