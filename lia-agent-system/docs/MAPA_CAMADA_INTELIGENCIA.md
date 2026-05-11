# Mapa da Camada de Inteligencia — Plataforma LIA

  > Guia completo de onboarding tecnico para desenvolvedores.
  > Permite entender toda a camada de IA, seus componentes, padroes de codigo
  > e saber exatamente onde e como fazer qualquer alteracao.

  ---

  ## Indice

  1. [Stack Tecnologica Completa](#1-stack-tecnologica-completa)
  2. [Arquitetura da Camada de Inteligencia](#2-arquitetura-da-camada-de-inteligencia)
     - IA vs Deterministico — mapa de decisoes
     - Diagrama Geral de Execucao (3 mecanismos)
  3. [Pontos de Contato da LIA](#3-pontos-de-contato-da-lia) (7 pontos)
  4. [Orquestrador](#4-orquestrador)
     - ConversationGraph (47 nos, 4 subgrafos)
     - Sistema de Actions (Closed-Loop), ACTIONABLE_INTENTS, Multi-turno, Confirmation Patterns
  5. [Todos os Dominios](#5-todos-os-dominios) (10 dominios)
     - Fluxos ponta-a-ponta: Perguntas WSI, Feedback Personalizado (§5.4), Triagem WhatsApp (§5.6), Agendamento (§5.7)
  6. [Catalogo Completo de Agentes](#6-catalogo-completo-de-agentes) (26 agentes)
  7. [Agentes ReAct em Detalhe](#7-agentes-react-em-detalhe) (7 agentes, 89 tools)
     - ReActLoop (ciclo iterativo), Grafo JobWizardGraph (6 nos)
  8. [Infraestrutura Compartilhada](#8-infraestrutura-compartilhada) (~118 arquivos)
     - Compliance 3 Pilares, Auth/Multi-tenancy, EnhancedBaseAgent, Token Tracking, A/B Testing
  9. [Catalogo de Servicos](#9-catalogo-de-servicos) (140 catalogados, ~330 arquivos)
  10. [Padroes de Codigo](#10-padroes-de-codigo) (9 padroes)
      - Logging, Prompt Registry, Error Handling
  11. [Guia Pratico "Onde Mexer"](#11-guia-pratico-onde-mexer) (16 cenarios)
      - Human-in-the-Loop, Mapa de Risco por Acao, Limites Operacionais
  12. [Conceitos de IA — Documento Educacional e Conceitual](#12-conceitos-de-ia--documento-educacional-e-conceitual) (10 temas)
      - Fundamentos ReAct, Orquestracao, Busca Inteligente, WSI, Memoria, Async, Compliance, Automacao, Decisoes de Design
      - Analise de Migracao Legacy→ReAct, Alinhamento WeDO REAL
  13. [Glossario](#13-glossario) (48 termos)

  ---
## 1. Stack Tecnologica Completa

### Diagrama de Conexao

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (atual)                                 │
│   Next.js 15 + React 19 + TypeScript + Radix UI + Tailwind CSS      │
│   [Futuro: Vue.js + Vuetify + Nuxt — pos-conversao]                 │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ REST API / WebSocket
                            v
┌──────────────────────────────────────────────────────────────────────┐
│                     BACKEND (atual)                                   │
│   FastAPI + Uvicorn (ASGI) + Python + Pydantic + SQLAlchemy + Alembic│
│   [Futuro: Ruby on Rails — pos-conversao]                            │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              v             v             v
┌──────────────────┐ ┌───────────┐ ┌──────────────┐
│   ORQUESTRADOR   │ │  CELERY   │ │  RABBITMQ    │
│ CascadedRouter → │ │  (filas   │ │  (message    │
│ FastRouter →     │ │  async)   │ │   broker)    │
│ IntentRouter     │ │           │ │              │
└────────┬─────────┘ └───────────┘ └──────────────┘
         │
         v
┌──────────────────────────────────────────────────────────────────────┐
│                  AGENTES REACT + LEGACY                              │
│   WizardAgent, KanbanAgent, TalentAgent, JobsMgmt, Policy, ...      │
│   ReActLoop: Thought → Action → Observe → Decide                    │
│                                                                      │
│   Frameworks IA: LangChain (orquestracao LLM) + LangGraph (grafos)  │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                     ┌──────┼──────┐
                     v      v      v
              ┌────────┐┌──────┐┌────────┐
              │ Claude ││Gemini││ OpenAI │
              │(Anthro)││(GCP) ││ (GPT)  │
              └────────┘└──────┘└────────┘
                            │
                     ┌──────┼──────┐
                     v      v      v
              ┌────────┐┌──────┐┌────────┐
              │Postgre ││Redis ││PGVector│
              │  SQL   ││      ││        │
              └────────┘└──────┘└────────┘
```

### Backend (Python)

| Categoria | Tecnologia | Para que serve |
|---|---|---|
| Framework Web | FastAPI | API REST assincrona de alta performance |
| Servidor ASGI | Uvicorn | Servidor de producao para FastAPI |
| Tempo Real | WebSockets | Comunicacao bidirecional para chat em tempo real |
| ORM | SQLAlchemy 2.0 | Mapeamento objeto-relacional com suporte async |
| Banco Async | AsyncPG | Driver PostgreSQL assincrono de alta performance |
| Migrations | Alembic | Versionamento e migracao de schema do banco |
| Busca Vetorial | PGVector | Busca por similaridade semantica no PostgreSQL |
| Framework IA | LangChain | Orquestracao de LLMs, chains e prompts |
| Grafos IA | LangGraph | Grafos de estado para fluxos multi-step (Wizard) |
| Observabilidade IA | LangSmith | Tracing e debugging de chamadas LLM |
| LLM Principal | langchain-anthropic | Integra Claude (Anthropic) como LLM |
| LLM Alternativo | langchain-openai | Integra GPT (OpenAI) como LLM |
| LLM Alternativo | langchain-google-vertexai | Integra Gemini (Google) como LLM |
| Filas | Celery | Processamento assincrono de tarefas em background |
| Cache/Broker | Redis | Cache de sessoes, broker do Celery, rate limiting |
| Mensageria | aio-pika (RabbitMQ) | Message broker AMQP para filas distribuidas |
| Agendamento | APScheduler | Agendamento de tarefas recorrentes |
| Auth Microsoft | MSAL | Autenticacao OAuth2 com Azure AD |
| API Microsoft | MS Graph SDK | Integracao com Teams, Calendar, OneDrive |
| Bot Microsoft | BotBuilder | Bot framework para Microsoft Teams |
| WhatsApp/SMS | Twilio | Envio de mensagens WhatsApp e SMS |
| Email | Mailgun | Envio de emails transacionais |
| Auth SSO | WorkOS | Autenticacao SSO empresarial |
| Auth JWT | python-jose | Geracao e validacao de tokens JWT |
| Senhas | passlib (bcrypt) | Hash seguro de senhas |
| PDF Parsing | PyPDF2 | Extracao de texto de curriculos em PDF |
| Word Parsing | python-docx | Extracao de texto de curriculos em DOCX |
| Excel Parsing | openpyxl | Leitura de planilhas (importacao em massa) |
| HTTP Client | httpx | Cliente HTTP assincrono para APIs externas |
| HTTP Client | aiohttp | Cliente HTTP alternativo (webhooks, integraces) |
| Criptografia | cryptography | Criptografia de chaves ATS e dados sensiveis |
| Validacao | Pydantic 2.10 | Validacao de schemas, DTOs e configuracao |

### Frontend (TypeScript/React)

| Categoria | Tecnologia | Para que serve |
|---|---|---|
| Framework | Next.js 15 | Framework React com SSR e API routes |
| UI Library | React 19 | Biblioteca de componentes reativos |
| Linguagem | TypeScript | Tipagem estatica para JavaScript |
| Componentes Base | Radix UI | Primitivos acessiveis e sem estilo |
| Design System | shadcn/ui | Componentes pre-estilizados sobre Radix |
| Estilizacao | Tailwind CSS | Utility-first CSS framework |
| Graficos | Chart.js + react-chartjs-2 | Graficos interativos (pipeline, metricas) |
| Graficos | Recharts | Graficos declarativos React (dashboards) |
| Animacoes | Framer Motion | Animacoes fluidas e transicoes |
| Icones | Lucide React | Biblioteca de icones consistente |
| PDF Export | jsPDF | Geracao de relatorios PDF no frontend |
| Screenshot | html2canvas | Captura de componentes como imagem |
| SVG Render | canvg | Renderizacao de SVG para canvas |
| Temas | next-themes | Dark mode e temas dinamicos |

### Migracao Futura Planejada

| De | Para | Status |
|---|---|---|
| Next.js + React | Vue.js + Vuetify + Nuxt | Planejado |
| FastAPI + Python | Ruby on Rails | Planejado |

> O codigo atual esta sendo estruturado para facilitar essa migracao futura.
> Padroes como separacao de concerns, prop patterns e naming conventions
> sao seguidos pensando na conversibilidade.

### Integracoes Externas

| Servico | Para que | Tipo |
|---|---|---|
| Anthropic (Claude) | LLM principal para agentes ReAct | IA |
| Google Vertex AI (Gemini) | LLM alternativo, default do LLMFactory | IA |
| OpenAI (GPT) | LLM alternativo para tarefas especificas | IA |
| Twilio | Envio de WhatsApp e SMS para candidatos | Comunicacao |
| Mailgun | Envio de emails transacionais | Comunicacao |
| Microsoft Graph | Integracao com Teams, calendario, reunioes | Comunicacao |
| Deepgram | Transcricao de voz em tempo real | IA/Audio |
| OpenMic.ai | Voice screening de candidatos | IA/Audio |
| Apify | Web scraping de perfis profissionais | Sourcing |
| Pearch AI | Busca inteligente de candidatos | Sourcing |
| WorkOS | Autenticacao SSO empresarial | Auth |
| HubSpot | CRM e gestao de clientes | CRM |
| Stripe | Pagamentos e assinaturas | Billing |
| Gupy ATS | Integracao com ATS Gupy | ATS |
| Pandape ATS | Integracao com ATS Pandape | ATS |
| Merge | Integracao unificada com multiplos ATS | ATS |
| LangSmith | Observabilidade e tracing de LLMs e agentes | IA/Observabilidade |
| Elasticsearch | Busca full-text + BM25 para Talent Funnel Search | Busca |
| Iugu | Billing e pagamentos SaaS | Billing |
| Vindi | Billing e pagamentos SaaS alternativo | Billing |
| GCP | Infraestrutura cloud, Vertex AI | Infra/IA |
| Notion | Gestao de conhecimento e documentacao | Produtividade |
| Jira | Gestao de projetos e tracking | Produtividade |
| ProfitWell | Metricas de receita e churn SaaS | Billing/Analytics |
| Warden AI | Monitoramento de seguranca de IA | IA/Seguranca |
| PrivacyTools | Ferramentas de privacidade e compliance | Privacy/LGPD |
| Drata/Vanta | Automacao de compliance SOC2/ISO | Compliance |

---

## 2. Arquitetura da Camada de Inteligencia

### Organograma Completo da Plataforma

```
                        ┌─────────────────────────────────────┐
                        │         ORQUESTRADOR                │
                        │  Cache → FastRouter → IntentRouter  │
                        │     (9 dominios roteados)           │
                        └──────────────────┬──────────────────┘
                                           │
        ┌──────────┬──────────┬────────────┼────────────┬──────────┬──────────┐
        │          │          │            │            │          │          │
        v          v          v            v            v          v          v
   ┌─────────┐┌─────────┐┌─────────┐┌──────────┐┌──────────┐┌────────┐┌────────┐
   │ WIZARD  ││ KANBAN  ││ TALENT  ││JOBS MGMT ││ POLICY   ││SOURCING││PIPELINE│
   │ ReAct   ││ ReAct   ││ ReAct   ││ ReAct    ││ ReAct    ││ ReAct  ││ ReAct  │
   │ 9 tools ││14 tools ││12 tools ││13 tools  ││13 tools  ││14 tools││14 tools│
   │ 29 svcs ││10 svcs  ││10 svcs  ││10 svcs   ││ 0 svcs   ││12 svcs ││20 svcs │
   └─────────┘└─────────┘└─────────┘└──────────┘└──────────┘└────────┘└────────┘
   job_mgmt    recruiter   recruiter  recruiter   hiring_     sourcing  cv_
               _assistant  _assistant _assistant   policy               screening

        ┌──────────┬──────────┐
        │          │          │
        v          v          v
   ┌──────────┐┌─────────┐┌──────────┐
   │COMMUNIC. ││INTERVIEW││ANALYTICS │    ┌──────────┐┌──────────┐
   │ Legacy   ││ Legacy  ││ Legacy   │    │ATS INTEG.││AUTOMATION│
   │26 svcs   ││ 4 svcs  ││10 svcs   │    │ Legacy   ││ Legacy   │
   │email,wpp ││calendar ││reports   │    │ 8 svcs   ││17 svcs   │
   │teams,sms ││deepgram ││predict.  │    │gupy,merge││scheduler │
   └──────────┘└─────────┘└──────────┘    └──────────┘└──────────┘
   communication interview  analytics      ats_integ.  automation

        ┌─────────────────────────────────────────────────────────────────────┐
        │              INFRAESTRUTURA COMPARTILHADA (shared/)                │
        │                                                                     │
        │  ReActLoop     FairnessGuard    LLMFactory      WorkingMemory      │
        │  (ciclo IA)    (compliance)     (3 providers)   (sessao)           │
        │                                                                     │
        │  LongTermMemory  CircuitBreaker  PIIMasking     FeatureFlags       │
        │  (cross-session) (resiliencia)   (LGPD)         (governanca)       │
        │                                                                     │
        │  MultiChannel    TaskManager     PromptRegistry  Repositories      │
        │  (5 adapters)    (async+DLQ)     (examples)      (CRUD)            │
        │                                                                     │
        │  LangChain       LangGraph       Celery          RabbitMQ          │
        │  (orquestr. LLM) (grafos estado) (filas async)   (msg broker)      │
        └─────────────────────────────────┬───────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    v                     v                     v
             ┌────────────┐      ┌──────────────┐      ┌────────────┐
             │   Claude   │      │   Gemini     │      │   OpenAI   │
             │ (Anthropic)│      │ (Vertex AI)  │      │  (GPT-4)   │
             └────────────┘      └──────────────┘      └────────────┘
                    │                     │                     │
                    v                     v                     v
             ┌────────────┐      ┌──────────────┐      ┌────────────┐
             │ PostgreSQL │      │    Redis     │      │  PGVector  │
             │  (dados)   │      │(cache/filas) │      │ (vetores)  │
             └────────────┘      └──────────────┘      └────────────┘
```

**Numeros totais**: 7 agentes ReAct + 1 LangGraph + 18 Legacy = 26 agentes | 140 servicos catalogados (~330 arquivos de servico) | 89 tools | 89 modelos de dados

### Diagrama Geral de Execucao (3 mecanismos)

A plataforma usa 3 mecanismos de execucao distintos. Toda mensagem entra pelo ConversationGraph;
os outros dois sao acionados conforme o tipo de tarefa.

```
Mensagem do usuario
    │
    v
ConversationGraph (47 nos, LangGraph StateGraph)  ← shared/agents/conversation.py
    │
    ├── classify_intent → extract_entities → decide_next_action
    │       │
    │       ├── execute_candidate_search → generate_response → END
    │       ├── execute_global_search → generate_response → END
    │       ├── ask_clarification → END
    │       ├── create_job_vacancy → [Job Wizard Subgrafo — 15 nos]
    │       ├── schedule_interview → [Interview Subgrafo — 6 nos]
    │       ├── sourcing_flow → [Sourcing Subgrafo — 14 nos]
    │       └── generate_response → END
    │
    ├── Job Wizard Subgrafo (15 nos):
    │     job_state_loader → job_router → [13 collectors] → validator → JD generator → publication
    │
    ├── Interview Subgrafo (6 nos):
    │     interview_state_loader → router → details_collector → validator → scheduler → response
    │
    └── Sourcing Subgrafo (14 nos):
          sourcing_initializer → local_search → calibration → volume → global → contact → outreach → ...

Separadamente (nao dentro do ConversationGraph):

JobWizardGraph (6 nos)          ← job_management/agents/job_wizard_graph.py
  intent_classifier → field_extractor → tool_router → tool_executor → response_generator → stage_transition
  (grafo customizado com conditional edges, alternativo ao subgrafo LangGraph)

ReActLoop (7 agentes)           ← shared/agents/react_loop.py
  ┌─ REASON ─┐   ┌── ACT ──┐   ┌─ OBSERVE ─┐   ┌─ DECIDE ─┐
  │ LLM gera │──▶│ Executa │──▶│ Resultado │──▶│ Continua │──┐
  │ reasoning│   │ tool    │   │ da tool   │   │ ou para  │  │
  └──────────┘   └─────────┘   └───────────┘   └──────────┘  │
       ▲                                              │ loop  │
       └──────────────────────────────────────────────┘       ▼ final_answer
```

**3 Mecanismos de Execucao — Comparativo**

| Aspecto | ConversationGraph | JobWizardGraph | ReActLoop |
|---|---|---|---|
| **Tipo** | LangGraph StateGraph (47 nos) | Grafo customizado (6 nos) | Loop autonomo iterativo |
| **Quando usar** | Toda interacao conversacional | Wizard de criacao de vaga (alternativo) | Agentes que raciocinam livremente |
| **Estado** | ConversationState (TypedDict) | JobWizardState (TypedDict) | ReActState (Pydantic) |
| **Subgrafos** | 4 (core, job wizard, interview, sourcing) | Nenhum (grafo plano) | Nenhum (ciclo unico) |
| **Quem usa** | Ponto de entrada unico do chat | WizardAgent (modo grafo) | Wizard, Kanban, Talent, JobsMgmt, Policy, Sourcing, Pipeline |
| **Arquivo** | `shared/agents/conversation.py` | `job_management/agents/job_wizard_graph.py` | `shared/agents/react_loop.py` |

### Arvore Completa de `app/`

```
app/
├── api/                          ← Endpoints REST (rotas FastAPI)
│   ├── v1/                       ← Versao 1 da API (~160 endpoints)
│   ├── public/                   ← Endpoints publicos (portal candidato)
│   └── orchestrator_routes.py    ← Rota principal do chat
│
├── orchestrator/                 ← Camada 1: Roteamento inteligente
│   ├── orchestrator.py           ← Ponto de entrada — recebe mensagem, retorna resposta
│   ├── cascaded_router.py        ← Router em 3 camadas (cache/regex/LLM)
│   ├── fast_router.py            ← Tier 2: classificacao por regex/keywords
│   ├── intent_router.py          ← Tier 3: classificacao por LLM
│   ├── action_executor.py        ← Execucao de acoes com confirmacao
│   ├── pending_action.py         ← Estado de acoes pendentes (multi-turn)
│   ├── state_manager.py          ← Persistencia de estado de sessao
│   ├── policy_engine.py          ← Politicas de empresa aplicadas ao fluxo
│   └── task_planner.py           ← Planejamento de tarefas compostas
│
├── domains/                      ← Camada 2: Dominios de negocio
│   ├── job_management/           ← Criacao e gestao de vagas
│   ├── recruiter_assistant/      ← Assistentes (Kanban, Talent, Jobs Mgmt)
│   ├── hiring_policy/            ← Politicas de contratacao
│   ├── cv_screening/             ← Triagem e avaliacao WSI
│   ├── sourcing/                 ← Busca ativa de candidatos
│   ├── communication/            ← Email, WhatsApp, Teams
│   ├── interview_scheduling/     ← Agendamento de entrevistas
│   ├── analytics/                ← Relatorios e metricas
│   ├── ats_integration/          ← Integracao com ATS externos
│   └── automation/               ← Automacoes e tarefas programadas
│
├── shared/                       ← Camada 3: Infraestrutura compartilhada
│   ├── agents/                   ← BaseAgent, ReActLoop, WorkingMemory
│   ├── compliance/               ← FairnessGuard, AuditService
│   ├── intelligence/             ← Embeddings, busca semantica
│   ├── learning/                 ← A/B testing, learning loop
│   ├── memory/                   ← Estado de conversacao
│   ├── providers/                ← LLMFactory (Claude/Gemini/OpenAI)
│   ├── channels/                 ← MultiChannel (email/whatsapp/sms/teams)
│   ├── execution/                ← Planos de acao
│   ├── resilience/               ← Circuit breaker, cache
│   ├── robustness/               ← Error handling, validacao
│   ├── prompts/                  ← Registry de prompts e examples
│   ├── governance/               ← Feature flags, monitoring
│   ├── repositories/             ← Acesso a dados (CRUD)
│   ├── async_processing/         ← Task manager, scheduler, DLQ
│   └── tools/                    ← Tools compartilhadas (export, insight)
│
├── models/                       ← Modelos SQLAlchemy (89 modelos de dados)
├── services/                     ← Servicos globais (llm, skill_catalog)
└── main.py                      ← Entrypoint FastAPI
```

### As 4 Camadas

| Camada | O que controla | Exemplo | Onde fica |
|---|---|---|---|
| **Orquestracao** | Roteamento de mensagens para o agente certo | Classifica "quero criar uma vaga" → WizardAgent | `app/orchestrator/` |
| **Agentes** | Raciocinio autonomo + execucao de acoes | WizardAgent raciocina, chama tools, responde | `app/domains/*/agents/` |
| **Servicos** | Logica de negocio e integracao com dados | WSI scoring, CV parsing, email dispatch | `app/domains/*/services/` |
| **Infra Compartilhada** | Componentes reutilizaveis entre dominios | FairnessGuard, LLMFactory, ReActLoop | `app/shared/` |

### Fluxo de Requisicao (mensagem ate resposta)

```
1. Usuario envia mensagem no chat
   ↓
2. Frontend (Next.js) → POST /api/v1/orchestrator/chat
   ↓
3. Orchestrator.process_message()
   ↓
4. CascadedRouter classifica a intencao:
   [Tier 1] Cache em memoria (O(1) lookup)
   [Tier 2] FastRouter (regex, ~80% das queries)
   [Tier 3] IntentRouter (LLM, queries ambiguas)
   ↓
5. Roteia para o agente certo (ex: WizardReActAgent)
   ↓
6. Agente executa ciclo ReAct:
   THOUGHT: "O usuario quer criar uma vaga de dev Python senior"
   ACTION:  call_tool("validate_job_fields", {title: "Dev Python", ...})
   OBSERVE: {valid: true, suggestions: [...]}
   DECIDE:  Tenho info suficiente → responder
   ↓
7. AgentOutput retornado ao Orchestrator
   ↓
8. Orchestrator enriquece resposta (acoes, navegacao, metadata)
   ↓
9. Frontend renderiza resposta + painel lateral
```

### LangGraph vs ReActLoop

| Aspecto | LangGraph (JobWizardGraph) | ReActLoop Customizado |
|---|---|---|
| **Tipo de fluxo** | Grafo de estado com nos fixos | Loop autonomo sem fluxo pre-definido |
| **Quando usar** | Processos com etapas sequenciais claras | Agentes que precisam raciocinar livremente |
| **Estado** | StateGraph com TypedDict | WorkingMemory + ReActState |
| **Exemplo** | Wizard de criacao de vaga (6 etapas) | Kanban, Talent, Jobs Management |
| **Onde fica** | `job_management/agents/job_wizard_graph.py` | `shared/agents/react_loop.py` |

### Conexao com LLMs

```
ReActConfig(model_provider="claude")
        ↓
    ReActLoop
        ↓
    LLMProviderFactory.get_provider("claude")
        ↓
    ┌─────────────┐
    │ LLMClaude   │ → Anthropic API (Claude Sonnet)
    │ LLMGemini   │ → Google Vertex AI (Gemini Pro)
    │ LLMOpenAI   │ → OpenAI API (GPT-4)
    └─────────────┘
```

Cada agente pode usar um provider diferente via `ReActConfig.model_provider`.
O default e `"claude"`. Configuravel por dominio sem mudar codigo — basta
alterar o parametro no construtor do agente.

### O que e IA vs Deterministico

Nem tudo na plataforma depende de LLM. Este mapa mostra o que e decidido
por IA, o que e hibrido e o que e 100% codigo deterministico:

```
DECISOES 100% IA (LLM):
├─ Intent classification (o que o recrutador quer)
├─ Geracao de Job Description
├─ Analise de CV e extracao de dados
├─ WSI scoring qualitativo (blocos comportamentais)
├─ Geracao de perguntas de triagem
├─ Sugestoes de competencias e skills
├─ Analise de fit cultural
├─ Geracao de comunicacoes personalizadas
├─ Analise multimodal (video, imagem, voz)
└─ Predicao de sub-status de pipeline

DECISOES HIBRIDAS (IA + Regras):
├─ Roteamento de dominio: Cache → Regex → LLM (cascata)
├─ WSI scoring quantitativo: LLM extrai + Algoritmo pontua
├─ Busca de candidatos: WRF (pesos deterministicos) + embeddings
├─ Personalizacao: Estatisticas historicas + LLM ajusta
├─ Automacao de pipeline: Triggers deterministicos + LLM prediz
└─ Cache semantico: Cosine similarity (math) + LLM (fallback)

DECISOES 100% DETERMINISTICAS:
├─ Autenticacao e autorizacao (JWT + RBAC)
├─ FairnessGuard camada 1 (regex pattern matching)
├─ FactChecker (validacao numerica com ranges fixos)
├─ Rate limiting e PolicyEngine (contadores + limites)
├─ Retencao LGPD (dias fixos por tipo)
├─ Pipeline state machine (transicoes validas hardcoded)
├─ Multi-tenancy isolation (company_id filter)
├─ Token tracking e billing (contagem exata)
└─ Feature flags (boolean per tenant)
```

**Regra pratica**: Se uma decisao e critica (rejeitar candidato, enviar email),
ela DEVE ter componente deterministico (codigo Python na tool), nao depender
apenas do LLM. Ver "Niveis de Garantia" na Secao 11.

### Duas Geracoes de Agentes — Legacy vs ReAct

A plataforma opera com duas geracoes de agentes coexistindo, controladas
por feature flag (`USE_REACT_AGENTS`):

```
┌──────────────────────────────────────────────────────────────────┐
│          LEGACY vs REACT — COMPARAÇÃO                            │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐           │
│  │  LEGACY (18 agents) │      │  REACT (7 agents)   │           │
│  │                     │      │                     │           │
│  │  DomainPrompt       │      │  ReActLoop          │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  process_intent()   │      │  Thought→Action→Obs │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  Action mapeada     │      │  Tool escolhida     │           │
│  │  (código decide)    │      │  (IA decide)        │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  Tool executada     │      │  Tool executada     │           │
│  │                     │      │                     │           │
│  │  PRÓ: Previsível    │      │  PRÓ: Flexível      │           │
│  │  CON: Rígido        │      │  PRÓ: Autônomo      │           │
│  │  CON: Escalabilidade│      │  PRÓ: Explainability│           │
│  └─────────────────────┘      └─────────────────────┘           │
│                                                                  │
│  Feature Flag: USE_REACT_AGENTS                                  │
│  ├── true (default) → Orchestrator usa ReactAgentRegistry        │
│  └── false → Orchestrator usa DomainPrompt.process_intent()      │
│                                                                  │
│  Fallback automático:                                            │
│  Se ReAct falha com exceção → tenta agente legacy                │
│  Se domínio não tem ReAct → usa legacy automaticamente           │
└──────────────────────────────────────────────────────────────────┘
```

> **Para detalhes completos**: analise da migracao Legacy→ReAct, status por
> dominio, consumo de tokens, projecao de consolidacao (de 26 para ~12 agentes)
> e alinhamento com o WeDO REAL, ver **§12.2.5** mais adiante neste documento.

---

## 3. Pontos de Contato da LIA

A LIA atua em 7 pontos de contato distintos, cada um com agentes, canais e propositos diferentes.
Este mapa mostra ONDE a inteligencia artificial atua no produto.

### Mapa Visual

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              PLATAFORMA WEB (Next.js)                                    │
│                                                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ 1. JOB CHAT  │ │ 2. TALENT    │ │ 3. JOBS MGMT │ │ 4. PIPELINE  │ │ 5. POLICY    │   │
│  │  (Wizard)    │ │    CHAT      │ │    CHAT      │ │    CHAT      │ │    CHAT      │   │
│  │              │ │              │ │              │ │   (Kanban)   │ │  (Politicas) │   │
│  │ Recrutador   │ │ Recrutador   │ │ Recrutador   │ │ Recrutador   │ │ Recrutador   │   │
│  │ cria vagas   │ │ busca perfis │ │ gerencia     │ │ move candid. │ │ configura    │   │
│  │              │ │              │ │ vagas        │ │              │ │ politicas    │   │
│  │ WizardReAct  │ │ TalentReAct  │ │ JobsMgmtReAct│ │ KanbanReAct  │ │ PolicyReAct  │   │
│  │ 9 tools      │ │ 12 tools     │ │ 13 tools     │ │ 14 tools     │ │ 13 tools     │   │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘   │
│         │                │                │                │                │            │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │                │
          └────────────────┴────────┬───────┴────────────────┴────────────────┘
                                    │
                                    v
                        ┌───────────────────────┐
                        │     ORQUESTRADOR      │
                        │  + ReActLoop + LLMs   │
                        └───────────┬───────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                                   │
                  v                                   v
        ┌─────────────────┐                 ┌─────────────────┐
        │  6. WHATSAPP    │                 │  7. MS TEAMS    │
        │  COM CANDIDATO  │                 │  COM RECRUTADOR │
        │                 │                 │                 │
        │ Canal: Twilio   │                 │ Canal: BotBuild.│
        │                 │                 │                 │
        │ LIA faz triagem │                 │ LIA envia       │
        │ WSI, coleta     │                 │ alertas, permite│
        │ respostas,      │                 │ gerenciar fluxo │
        │ screening       │                 │ direto no Teams │
        │                 │                 │                 │
        │ WSI + Screening │                 │ Teams Bot +     │
        │ Agent + LLM     │                 │ MS Graph + LLM  │
        └─────────────────┘                 └─────────────────┘
```

### Detalhamento dos 7 Pontos de Contato

| # | Ponto de Contato | Canal | Quem Interage | Agente Principal | O que Acontece |
|---|---|---|---|---|---|
| 1 | **Job Chat (Wizard)** | Plataforma Web | Recrutador | WizardReActAgent (9 tools) | Recrutador cria vaga por conversa natural. LIA extrai dados, enriquece JD com IA, sugere salarios com benchmarks, valida compliance via FairnessGuard, gera perguntas WSI. 6 estagios: input → JD → salary → skills → WSI → review |
| 2 | **Talent Chat** | Plataforma Web | Recrutador | TalentReActAgent (12 tools) | Recrutador busca candidatos, compara perfis, analisa skills, cria shortlists. LIA usa PGVector + Elasticsearch para busca semantica, ranking por WRF, e valida fairness nos criterios de busca |
| 3 | **Jobs Management Chat** | Plataforma Web | Recrutador | JobsMgmtReActAgent (13 tools) | Recrutador gerencia portfolio de vagas: pausa, reabre, fecha, analisa SLA, compara vagas, identifica gargalos. LIA usa benchmarks de recrutamento (Robert Half, ABRH) para contra-argumentar |
| 4 | **Pipeline/Kanban Chat** | Plataforma Web | Recrutador | KanbanReActAgent (14 tools) | Recrutador gerencia pipeline: move candidatos entre estagios, identifica bottlenecks, envia comunicacao em lote, inicia screening batch. LIA valida fairness em rejeicoes e sugere movimentacoes |
| 5 | **Policy Chat (Politicas)** | Plataforma Web | Recrutador | PolicyReActAgent (13 tools) | Recrutador configura politicas de contratacao da empresa: limites salariais, niveis de automacao, criterios de compliance, benchmarks por industria. LIA consulta dados ABRH/GPTW/Gupy/Robert Half, valida via FairnessGuard, detecta anomalias e gera relatorios de efetividade. 3 estagios: onboarding → review → consulting |
| 6 | **WhatsApp com Candidato** | WhatsApp (Twilio) | Candidato | ScreeningAgent + WSI | LIA faz triagem do candidato via WhatsApp: envia perguntas WSI, coleta respostas, aplica scoring deterministico, gera feedback personalizado. Usa Twilio para envio/recebimento e LLM para interpretacao de respostas |
| 7 | **Teams com Recrutador** | Microsoft Teams (BotBuilder) | Recrutador | Teams Bot + LLM | LIA interage com recrutador diretamente no MS Teams: envia alertas proativos (candidato parado, vaga expirando), permite consultas rapidas, gerencia fluxo sem sair do Teams. Usa MS Graph + BotBuilder |

### Stack por Ponto de Contato

| Ponto | Frontend | Backend | Agente | LLM | Integracao Externa |
|---|---|---|---|---|---|
| Job Chat | Next.js (web) | FastAPI + Orchestrator | WizardReActAgent | Claude | FairnessGuard, Benchmarks |
| Talent Chat | Next.js (web) | FastAPI + Orchestrator | TalentReActAgent | Claude | PGVector, Elasticsearch |
| Jobs Mgmt Chat | Next.js (web) | FastAPI + Orchestrator | JobsMgmtReActAgent | Claude | SQL, Benchmarks |
| Pipeline Chat | Next.js (web) | FastAPI + Orchestrator | KanbanReActAgent | Claude | FairnessGuard, SQL |
| Policy Chat | Next.js (web) | FastAPI + Orchestrator | PolicyReActAgent | Claude | FairnessGuard, Industry Benchmarks (ABRH, GPTW, Gupy, Robert Half) |
| WhatsApp | Twilio (WhatsApp) | FastAPI + Webhooks | ScreeningAgent + WSI | Claude | Twilio, Deepgram |
| Teams | MS Teams (Bot) | FastAPI + BotBuilder | Teams Bot | Claude | MS Graph, MSAL |

---

## 4. Orquestrador

### Arvore de Arquivos

```
app/orchestrator/
├── orchestrator.py          ← Ponto de entrada principal
│                               Recebe mensagem → processa → retorna resposta
├── cascaded_router.py       ← Router em 3 camadas (cache/regex/LLM)
├── fast_router.py           ← Tier 2: classificacao por regex e keywords
│                               Resolve ~80% das queries sem LLM
├── intent_router.py         ← Tier 3: classificacao por LLM (Claude)
│                               Para queries ambiguas ou novas
├── action_executor.py       ← Executa acoes com confirmacao do usuario
│                               Closed-loop: propoe → confirma → executa
├── pending_action.py        ← Estado de acoes pendentes (multi-turn)
│                               Persiste entre mensagens
├── state_manager.py         ← Persistencia de estado de sessao
│                               Salva/recupera contexto de conversacao
├── policy_engine.py         ← Aplica politicas da empresa ao fluxo
│                               CompanyHiringPolicy → regras de automacao
└── task_planner.py          ← Planejamento de tarefas compostas
                                Decomposicao de tarefas complexas
```

### Roteamento em 3 Camadas

```
Mensagem do usuario
     │
     v
[Tier 1] Cache em memoria
     │ Hash da mensagem → lookup O(1)
     │ HIT → resposta imediata (sem custo LLM)
     │ MISS ↓
     v
[Tier 2] FastRouter (regex/keywords)
     │ Padroes regex por dominio
     │ ~80% das queries resolvidas aqui
     │ Alta confianca → roteia direto
     │ Baixa confianca ↓
     v
[Tier 3] IntentRouter (LLM/Claude)
     │ Classifica em 1 de 9+ dominios
     │ Usa exemplos few-shot para acuracia
     │ Custo: 1 chamada LLM (~0.01 USD)
     v
Agente do dominio identificado
```

### Tabela de Roteamento

| Dominio | Agente | Exemplos de Frases |
|---|---|---|
| wizard | WizardReActAgent | "quero criar uma vaga", "nova posicao de dev" |
| kanban | KanbanReActAgent | "como esta o pipeline?", "mova candidatos", "gargalos" |
| talent | TalentReActAgent | "buscar candidatos", "comparar perfis", "ranking" |
| jobs_mgmt | JobsMgmtReActAgent | "minhas vagas", "pausar vaga", "SLA das vagas" |
| policy | PolicyReActAgent | "configurar politicas", "regras de contratacao" |
| sourcing | SourcingReActAgent | "busca ativa", "outreach", "encontrar candidatos" |
| pipeline | PipelineReActAgent | "triagem de CVs", "screening", "mover candidato" |
| scheduling | SchedulingAgent | "agendar entrevista", "calendario" |
| communication | CommunicationAgent | "enviar email", "mensagem whatsapp" |

### Sistema de Actions (Closed-Loop)

Quando um agente decide executar uma acao, o Orquestrador usa o sistema
de Actions para garantir que acoes irreversiveis passem por confirmacao:

```
Agente decide acao
     │
     v
ActionExecutorService.propose_action()
     │
     ├─ requires_confirmation = false → Executa direto
     │
     └─ requires_confirmation = true
          │
          v
     PendingActionState (salvo em sessao)
          │
          v
     LIA pergunta: "Confirma X?"
          │
          v
     Recrutador responde no chat ("sim", "pode", "confirmo")
          │
          v
     ActionExecutorService.execute_pending()
          │
          v
     Resultado retornado ao agente
```

**PendingActionState**: Persiste entre mensagens (multi-turn). Se o recrutador
muda de assunto, a acao pendente e descartada automaticamente.

> Para o catalogo completo de 205 actions por dominio, ver auditoria §6.

### ACTIONABLE_INTENTS (Ciclo Fechado)

O `ActionExecutorService` define quais intents resultam em execucao real:

| Intent | Parametros Obrigatorios | Risco | Confirmacao |
|---|---|---|---|
| `mover_candidato` | candidate_id, target_stage | Medio | Sim |
| `enviar_email` | candidate_id, subject, body | Alto | Sim |
| `agendar_entrevista` | candidate_id, datetime, interviewer | Medio | Sim |
| `disparar_triagem` | candidate_ids | Baixo | Nao |
| `analisar_perfil` | candidate_id | Baixo | Nao |
| `aprovar_candidato` | candidate_id | Medio | Sim |

### Fluxo Multi-turno (Clarificacao)

Quando faltam parametros, o sistema entra em clarificacao multi-turno:

```
Usuario envia mensagem
     │
     v
PendingActionState existe?
     │
     ├─ SIM → extract_param_from_message()
     │         │
     │         ├─ Param extraido → atualiza collected_params
     │         │    │
     │         │    ├─ Completo? → requires_confirmation?
     │         │    │                 ├─ SIM → "Confirma X?"
     │         │    │                 └─ NAO → executa direto
     │         │    │
     │         │    └─ Incompleto? → next_question()
     │         │
     │         └─ Nao extraiu → repete pergunta
     │
     └─ NAO → Orchestrator.process_request()
               │
               └─ Intent acionavel? → try_execute()
                    │
                    ├─ status="executed" → resultado real
                    ├─ status="needs_params" → salva PendingActionState
                    ├─ status="needs_confirmation" → aguarda resposta
                    └─ status="not_actionable" → resposta normal
```

### Confirmation/Rejection Patterns

O sistema detecta confirmacao e rejeicao com 30+ padroes PT/EN:

- **Confirmacao**: "sim", "pode", "confirmo", "ok", "manda", "envia", "faz isso", "perfeito", "isso mesmo", "avanca", "prossiga", "yes", "go", "confirm", ...
- **Rejeicao**: "nao", "cancela", "espera", "mudei de ideia", "esquece", "no", "cancel", "stop", ...

### Fallback para Modais

Quando a execucao automatica falha (ex: erro de DB, parametro invalido),
o sistema oferece o modal tradicional como fallback — o recrutador nao fica
bloqueado. Isso garante resiliencia sem perder a experiencia conversacional.

> Para detalhes completos do ciclo fechado, ver `PLANO_CICLO_FECHADO_LIA.md`.

### ConversationGraph — Grafo Completo (47 nos)

O `ConversationGraph` e o grafo principal LangGraph (`StateGraph`) que processa
todas as mensagens do chat. Arquivo: `shared/agents/conversation.py`, funcao `create_conversation_graph()`.

```
ENTRY → classify_intent → extract_entities → decide_next_action
                                                    │
                    ┌───────────┬───────────┬───────┼───────┬────────────┬──────────┐
                    v           v           v       v       v            v          v
             execute_search  execute_  create_job  schedule  generate_  ask_      END
             (local DB)      global    _vacancy    _interview response  clarif.
                    │         (Pearch)      │           │       │          │
                    v           │           v           v       v          v
             generate_response ─┘    [Job Wizard]  [Interview] END       END
                    │                  Subgrafo      Subgrafo
                    v
                   END
```

**Roteamento condicional** (`decide_next_action` — 7 destinos):

| Condicao | Destino | Quando |
|---|---|---|
| `intent == "confirm_global_search"` | `execute_global` | Usuario confirmou busca paga |
| `intent == "chitchat"` | `generate_response` | Conversa casual |
| `confidence < 0.6` | `ask_question` | Intent ambiguo |
| `intent == "search_candidates"` | `execute_search` | Busca de candidatos |
| `intent == "create_job_vacancy"` | `create_job_vacancy` | Criacao de vaga |
| `intent == "schedule_interview"` | `schedule_interview` | Agendamento |
| fallback | `generate_response` | Demais intents |

**4 Subgrafos integrados**:

| Subgrafo | Nos | Entry Node | Fluxo |
|---|---|---|---|
| **Core** | ~6 | classify_intent | classify → extract → decide → search/response/clarification → END |
| **Job Wizard** | ~18 | job_state_loader | loader → router → [13 collectors] → validator → frame_gen → response_planner → response |
| **Interview** | ~6 | interview_state_loader | loader → router → details_collector → validator → scheduler → response_planner → response |
| **Sourcing** | ~16 | sourcing_state_initializer | initializer → local_search → calibration → volume → global → contact → outreach → screening → feedback → report → decision → scheduling/rejection → placement → mass_feedback → response |

**Job Wizard — 13 collectors** (loop via `job_router` + `decide_job_creation_next`):

```
job_state_loader → job_router ──┐
       ▲                        │ decide_job_creation_next()
       │                        v
       │  ┌─ onboarding_node ──────────────────────┐
       │  ├─ basics_collector                      │
       │  ├─ remuneration_collector                │
       │  ├─ org_structure_collector               │
       │  ├─ technical_matrix_collector            │
       │  ├─ sourcing_strategy_collector           │
       │  ├─ wsi_competencies_collector            │
       │  ├─ interview_flow_collector              │
       │  ├─ governance_collector                  │
       │  ├─ communication_templates_collector     │
       │  ├─ job_description_generator             │
       │  ├─ screening_collector                   │
       │  └─ publication_node ─→ sourcing ou validator
       │                                           │
       └───────────────── loop ◄───────────────────┘
                          │
                validator → frame_generator → response_planner → generate_response → END
```

**Interview Scheduling — 6 nos**:

```
interview_state_loader → interview_router → interview_details_collector
    → interview_validator ─┬─ ready → interview_scheduler_executor → interview_response_planner
                           └─ not ready → interview_response_planner
                                                    → generate_response → END
```

**Sourcing & Engagement — 16 nos** (Steps 14-27):

```
sourcing_state_initializer → local_search → calibration → [espera feedback]
  → process_calibration_feedback → volume_assessment → global_expansion → [espera aprovacao]
  → contact_approval → email_outreach → [espera respostas]
  → async_screening → candidate_feedback → recruiter_report → [espera decisao]
  → recruiter_decision ─┬─ aprovar → auto_scheduling
                        └─ rejeitar → rejection_feedback
  → placement → mass_feedback → generate_response → END
```

**Protecao contra loops**: `collection_attempts >= 3` redireciona para `response_planner` (pergunta ao usuario).

---

## 5. Todos os Dominios

### 5.1 job_management — Criacao e Gestao de Vagas

Dominio responsavel por todo o ciclo de vida de vagas: criacao via wizard,
enriquecimento de JD com IA, templates, insights e publicacao.

```
app/domains/job_management/
├── agents/
│   ├── wizard_react_agent.py         ← Agente ReAct do wizard de criacao
│   ├── wizard_system_prompt.py       ← Prompt do wizard
│   ├── wizard_tool_registry.py       ← 9 tools do wizard
│   ├── wizard_stage_context.py       ← Contexto por estagio do wizard
│   ├── job_wizard_graph.py           ← Grafo LangGraph do wizard (6 nos)
│   ├── job_vacancy_nodes.py          ← Nos do grafo de vagas
│   ├── stage_context.py              ← Definicoes dos 6 estagios
│   ├── job_drafting_agent.py         ← Agente de rascunho de JD
│   ├── job_intake_agent.py           ← Agente de intake
│   ├── job_lifecycle_agent.py        ← Agente de ciclo de vida
│   ├── job_insights_agent.py         ← Agente de insights
│   ├── job_benefits_comp_agent.py    ← Agente de beneficios/compensacao
│   └── job_rubric_agent.py           ← Agente de rubricas de avaliacao
├── services/
│   ├── wizard_orchestrator_service.py ← Orquestrador do wizard
│   ├── wizard_data_priority_service.py ← Prioridade de dados no wizard
│   ├── wizard_analytics_service.py   ← Analytics do wizard
│   ├── jd_generation_service.py      ← Geracao de JD com IA
│   ├── jd_enrichment_service.py      ← Enriquecimento de JD com IA
│   ├── jd_import_service.py          ← Importacao de JD existente
│   ├── jd_template_service.py        ← Templates de JD
│   ├── jd_template_cache_service.py  ← Cache de templates
│   ├── job_vacancy_service.py        ← CRUD de vagas
│   ├── job_vacancy_route_service.py  ← Roteamento de vagas
│   ├── job_context_service.py        ← Contexto da vaga para agentes
│   ├── job_embedding_service.py      ← Embeddings de vagas (PGVector)
│   ├── job_qualification_service.py  ← Qualificacao de vagas
│   ├── job_template_service.py       ← Gestao de templates
│   ├── job_clone_service.py          ← Clonagem de vagas
│   ├── job_board_service.py          ← Publicacao em job boards
│   ├── job_alert_service.py          ← Alertas de vagas
│   ├── job_audit_service.py          ← Auditoria de vagas
│   ├── job_status_webhook_service.py ← Webhooks de status
│   ├── job_analytics_prompt_service.py ← Prompts analiticos
│   ├── job_insights_service.py       ← Insights de vagas
│   ├── job_report_service.py         ← Relatorios de vagas
│   ├── job_pattern_service.py        ← Padroes de vagas
│   ├── seniority_jd_analyzer.py      ← Analise de senioridade na JD
│   ├── template_importer_service.py  ← Importacao de templates
│   ├── template_learning_service.py  ← Learning de templates
│   ├── template_seeder.py            ← Seed de templates iniciais
│   ├── vacancy_search_service.py     ← Busca de vagas
│   ├── outcome_tracker.py            ← Rastreamento de resultados
│   └── recruitment_email_templates.py ← Templates de email
├── tools/
│   ├── job_wizard_tools.py           ← Funcoes base do wizard
│   ├── job_tools.py                  ← Funcoes gerais de vagas
│   └── query_tools.py               ← Funcoes de query SQL
└── models/, schemas/                 ← Modelos e schemas Pydantic
```

**Conexoes**: Usa FairnessGuard (validacao de requisitos), LLMFactory (geracao de JD), PGVector (embeddings de vagas), WSI (geracao de perguntas)

### 5.2 recruiter_assistant — Assistentes do Recrutador

Dominio que abriga os 3 agentes ReAct de assistencia direta ao recrutador:
Kanban (pipeline), Talent (candidatos) e Jobs Management (portfolio de vagas).

```
app/domains/recruiter_assistant/
├── agents/
│   ├── kanban_react_agent.py         ← Agente ReAct do Kanban (pipeline)
│   ├── kanban_system_prompt.py       ← Prompt do Kanban
│   ├── kanban_tool_registry.py       ← 14 tools do Kanban
│   ├── kanban_stage_context.py       ← Contexto por estagio do Kanban
│   ├── talent_react_agent.py         ← Agente ReAct de Talent (candidatos)
│   ├── talent_system_prompt.py       ← Prompt do Talent
│   ├── talent_tool_registry.py       ← 12 tools do Talent
│   ├── talent_stage_context.py       ← Contexto por estagio do Talent
│   ├── jobs_mgmt_react_agent.py      ← Agente ReAct de Jobs Management
│   ├── jobs_mgmt_system_prompt.py    ← Prompt do Jobs Management
│   ├── jobs_mgmt_tool_registry.py    ← 13 tools do Jobs Management
│   ├── jobs_mgmt_stage_context.py    ← Contexto por estagio do Jobs Mgmt
│   └── recruiter_assistant_agent.py  ← Agente legacy (fallback)
├── services/
│   ├── kanban_assistant_service.py   ← Servico do Kanban
│   ├── talent_assistant_service.py   ← Servico do Talent
│   ├── jobs_management_assistant_service.py ← Servico do Jobs Mgmt
│   ├── pipeline_service.py           ← Servico do pipeline de candidatos
│   ├── pipeline_stage_service.py     ← Servico de estagios do pipeline
│   ├── conversation_manager.py       ← Gerenciador de conversacao
│   ├── conversation_memory.py        ← Memoria de conversacao
│   ├── memory_service.py             ← Servico de memoria
│   ├── wizard_action_executor.py     ← Executor de acoes do wizard
│   └── wizard_analytics_service.py   ← Analytics do wizard
├── tools/
│   └── pipeline_tools.py            ← Tools do pipeline
└── models/, schemas/
```

**Conexoes**: Usa FairnessGuard (fairness em rejeicoes e buscas), SQL direto (benchmarks de pipeline e recrutamento), WorkingMemory (contexto de sessao)

### 5.3 hiring_policy — Politicas de Contratacao

Dominio dedicado a configuracao de politicas de contratacao por empresa.
O PolicyReActAgent substitui o antigo fluxo de 19 perguntas fixas por um
agente consultivo que se adapta ao contexto da empresa.

```
app/domains/hiring_policy/
├── agents/
│   ├── policy_react_agent.py         ← Agente ReAct de politicas
│   ├── policy_system_prompt.py       ← Prompt consultivo
│   ├── policy_tool_registry.py       ← 13 tools (mais FairnessGuard integrado)
│   └── policy_stage_context.py       ← 3 estagios: onboarding/review/consulting
└── models/, schemas/
```

**Conexoes**: FairnessGuard integrado diretamente nas validacoes, benchmarks de 8 setores com fontes (ABRH, GPTW, Gupy, Robert Half), `CompanyHiringPolicy` no banco

### 5.4 cv_screening — Triagem e Avaliacao WSI

Dominio responsavel pela triagem de curriculos usando a metodologia WSI
(WeDoTalent Skill Index) com 7 blocos de avaliacao.

```
app/domains/cv_screening/
├── agents/
│   ├── pipeline_react_agent.py       ← Agente ReAct do pipeline
│   ├── pipeline_system_prompt.py     ← Prompt do pipeline
│   ├── pipeline_tool_registry.py     ← 14 tools do pipeline
│   ├── pipeline_stage_context.py     ← Contexto por estagio
│   ├── screening_agent.py            ← Agente de screening (legacy)
│   ├── avaliador_wsi_agent.py        ← Avaliador WSI (legacy)
│   └── triagem_curricular_agent.py   ← Triagem curricular (legacy)
├── services/
│   ├── wsi_service.py                ← Servico principal WSI
│   ├── wsi_screening_pipeline.py     ← Pipeline de screening WSI
│   ├── wsi_question_service.py       ← Gestao de perguntas WSI
│   ├── wsi_question_generator.py     ← Geracao de perguntas por IA
│   ├── wsi_question_adjuster.py      ← Ajuste de perguntas
│   ├── wsi_deterministic_scorer.py   ← Scoring deterministico
│   ├── wsi_voice_orchestrator.py     ← Orquestrador de voz WSI
│   ├── cv_parser.py                  ← Parser de CV (PDF/DOCX)
│   ├── cv_scoring_service.py         ← Scoring de CV
│   ├── screening_question_set_service.py ← Set de perguntas de screening
│   ├── evaluation_criteria_service.py ← Criterios de avaliacao
│   ├── eligibility_verification_service.py ← Verificacao de eligibilidade
│   ├── pre_qualification_service.py  ← Pre-qualificacao
│   ├── rubric_evaluation_service.py  ← Avaliacao por rubrica
│   ├── calibration_profiles.py       ← Perfis de calibracao
│   ├── seniority_context_calibrator.py ← Calibracao por senioridade
│   ├── seniority_resolver.py         ← Resolucao de senioridade
│   ├── seniority_utils.py            ← Utilidades de senioridade
│   ├── score_normalization_service.py ← Normalizacao de scores
│   └── personalized_feedback_service.py ← Feedback personalizado
├── tools/
│   └── candidate_tools.py           ← Tools de candidatos
└── models/, schemas/
```

**Conexoes**: PGVector (busca semantica de candidatos), FairnessGuard (validacao de criterios), LLM (geracao e ajuste de perguntas), Deepgram (transcricao de voz)

#### Fluxo: Criacao de Perguntas de Triagem WSI

Pipeline completo orquestrado por `WSIScreeningPipeline.build_pipeline()`:

```
Request (skills, seniority, job_title)
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Resolve Seniority                                        │
│    seniority_resolver.py → Dreyfus stage + Bloom levels     │
│    Ex: "senior" → Dreyfus 4 (Proficiente), Bloom [4,5]     │
├─────────────────────────────────────────────────────────────┤
│ 2. Calibracao Contextual                                    │
│    seniority_context_calibrator.py                          │
│    Ajusta nivel com base em: titulo, departamento,          │
│    industria, pais, faixa salarial, porte da empresa        │
├─────────────────────────────────────────────────────────────┤
│ 3. Geracao por Bloco (compact=8 / full=12 perguntas)        │
│                                                             │
│    Bloco 2: Perguntas padrao da empresa (do banco de dados) │
│    Bloco 3: Elegibilidade WSI (eligibility_verification)    │
│    Bloco 4: Tecnico — Bloom/Dreyfus (wsi_question_service)  │
│    Bloco 5: Comportamental — Big Five/CBI                   │
│             (wsi_question_generator)                        │
├─────────────────────────────────────────────────────────────┤
│ 4. Deduplicacao (SequenceMatcher, threshold 0.65)           │
│    Remove perguntas similares entre blocos                  │
├─────────────────────────────────────────────────────────────┤
│ 5. Perguntas Afirmativas (quando aplicavel)                 │
│    PCD, racial, genero, idade, LGBTQIA+                    │
│    Tom acolhedor, nao-eliminatoria                         │
├─────────────────────────────────────────────────────────────┤
│ 6. Ajuste por IA (wsi_question_adjuster.py)                 │
│    LLM refina perguntas com limite de iteracoes por bloco   │
│    Avalia adequacao ao nivel de senioridade                  │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
UnifiedScreeningQuestion[] com metadata (bloco, Bloom level, Dreyfus stage, Big Five trait)
```

**Arquivos-chave**: `wsi_screening_pipeline.py` (orquestrador), `wsi_question_generator.py` (Big Five/CBI), `wsi_question_service.py` (Bloom/Dreyfus tecnico), `wsi_question_adjuster.py` (refinamento IA), `seniority_context_calibrator.py` (calibracao)

**Compliance**: FairnessGuard valida perguntas afirmativas | Deduplicacao impede repeticao | Calibracao contextual evita perguntas fora do nivel | Ajuste com limite de iteracoes previne loops

#### Fluxo: Feedback Personalizado para Candidatos

Pipeline de feedback de rejeicao via `PersonalizedFeedbackService`:

```
Recrutador solicita feedback (via chat ou acao de pipeline)
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Coleta de Contexto                                       │
│    CandidateContext: nome, skills, experiencia, senioridade  │
│    JobContext: titulo, requisitos, competencias              │
│    WSIEvaluationContext: score (0-5), classificacao          │
│      (excelente/alto/medio/regular/baixo),                  │
│      pontos fortes, areas de desenvolvimento                │
├─────────────────────────────────────────────────────────────┤
│ 2. Geracao por IA (Claude)                                  │
│    _build_personalization_prompt() → LLM                    │
│    Tom configuravel: warm | professional | encouraging      │
│    Inclui: sugestoes de desenvolvimento acionaveis,         │
│    referencia a pontos especificos da avaliacao WSI          │
├─────────────────────────────────────────────────────────────┤
│ 3. Parse da Resposta                                        │
│    _parse_ai_response() → feedback_data estruturado         │
├─────────────────────────────────────────────────────────────┤
│ 4. Preview para Recrutador (Human-in-the-Loop)              │
│    get_feedback_preview() → recrutador aprova/edita/rejeita │
│    Status: draft → pending_approval → approved/edited       │
├─────────────────────────────────────────────────────────────┤
│ 5. Envio Multicanal                                         │
│    FeedbackChannel: email | whatsapp | both                 │
│    Email: _compose_html_body() (HTML + texto plano)         │
│    WhatsApp: _generate_whatsapp_version() (versao condensada│
│              gerada por IA, via WhatsAppService/Twilio)      │
├─────────────────────────────────────────────────────────────┤
│ 6. Tracking e Analytics                                     │
│    Status final: sent | failed                              │
│    PersonalizedFeedbackRecord (PostgreSQL) — persistencia   │
│    Metricas de efetividade do feedback                       │
└─────────────────────────────────────────────────────────────┘
```

**Feedback em lote**: `mass_feedback_node` no Sourcing subgrafo (Secao 4, ConversationGraph) — dispara feedback para multiplos candidatos rejeitados simultaneamente

**Arquivos-chave**: `personalized_feedback_service.py` (orquestrador), `communication_dispatcher.py` (dispatch multicanal), `whatsapp_service.py` (envio WhatsApp), `email_templates_data.py` (templates)

**Compliance**: Human-in-the-Loop obrigatorio (recrutador aprova antes de enviar) | FairnessGuard valida feedback de rejeicao para bias | PII masking em logs | Persistencia para auditoria (PersonalizedFeedbackRecord)

### 5.5 sourcing — Busca Ativa de Candidatos

Dominio de sourcing ativo: busca em bases internas e externas, scoring,
outreach e engajamento de candidatos.

```
app/domains/sourcing/
├── agents/
│   ├── sourcing_react_agent.py       ← Agente ReAct de sourcing
│   ├── sourcing_system_prompt.py     ← Prompt de sourcing
│   ├── sourcing_tool_registry.py     ← 14 tools de sourcing
│   ├── sourcing_stage_context.py     ← Contexto por estagio
│   ├── sourcing_agent.py             ← Agente legacy de sourcing
│   └── engagement_nodes.py           ← Nos de engajamento
├── services/
│   ├── sourcing_pipeline.py          ← Pipeline de sourcing
│   ├── candidate_search_route_service.py ← Roteamento de busca
│   ├── wrf_service.py                ← WRF (Weighted Ranking Function)
│   ├── pre_wrf_filter.py             ← Filtro pre-WRF
│   ├── es_analyzer.py                ← Analise Elasticsearch
│   ├── pgv_analyzer.py               ← Analise PGVector
│   ├── evaluation_criteria.py        ← Criterios de avaliacao
│   ├── search_analytics.py           ← Analytics de busca
│   ├── vacancy_search.py             ← Busca de vagas para sourcing
│   ├── pearch_service.py             ← Integracao Pearch AI
│   ├── apify_service.py              ← Integracao Apify
│   └── apify_mcp_client.py           ← Cliente MCP Apify
├── tools/
│   └── query_tools.py               ← Tools de query
└── prompts.py, tools.py
```

**Conexoes**: Pearch AI (busca externa), Apify (web scraping), Elasticsearch (busca full-text), PGVector (busca semantica), WRF (ranking)

### 5.6 communication — Comunicacao Multi-Canal

Dominio de comunicacao com candidatos e equipe via email, WhatsApp, SMS e Teams.

```
app/domains/communication/
├── agents/
│   └── communication_agent.py        ← Agente de comunicacao (legacy)
├── services/
│   ├── communication_service.py      ← Servico principal de comunicacao
│   ├── communication_dispatcher.py   ← Dispatcher de mensagens
│   ├── communication_history_service.py ← Historico de comunicacoes
│   ├── email_service.py              ← Servico de email
│   ├── email_providers.py            ← Abstracoes de provedores de email
│   ├── email_providers/
│   │   ├── base.py                   ← Interface base de email
│   │   ├── resend_provider.py        ← Provider Resend
│   │   └── mailgun_provider.py      ← Provider Mailgun
│   ├── email_templates_data.py       ← Dados de templates de email
│   ├── whatsapp_service.py           ← Servico WhatsApp
│   ├── whatsapp_provider.py          ← Provider WhatsApp
│   ├── whatsapp_factory.py           ← Factory de WhatsApp
│   ├── whatsapp_twilio_service.py    ← WhatsApp via Twilio
│   ├── whatsapp_meta_service.py      ← WhatsApp via Meta API
│   ├── teams_service.py              ← Servico Microsoft Teams
│   ├── teams_auth.py                 ← Autenticacao Teams
│   ├── teams_bot.py                  ← Bot do Teams
│   ├── teams_simple.py               ← Integracao Teams simplificada
│   ├── teams_recording_service.py    ← Gravacao de reunioes Teams
│   ├── data_request_service.py       ← Requisicoes de dados (LGPD)
│   ├── data_request_whatsapp_service.py ← Requisicoes via WhatsApp
│   ├── transition_dispatch_service.py ← Dispatch em transicoes de pipeline
│   ├── webhook_service.py            ← Servico de webhooks
│   ├── infer_behavior_service.py     ← Inferencia de comportamento
│   ├── interpret_context_llm_service.py ← Interpretacao de contexto por LLM
│   └── return_event_service.py       ← Servico de eventos de retorno
├── tools/
│   └── communication_tools.py       ← Tools de comunicacao
└── models/, schemas/
```

**Conexoes**: Twilio (WhatsApp/SMS), Mailgun (email), Microsoft Graph (Teams), LLM (inferencia de contexto)

#### Fluxo: Triagem de Candidatos via WhatsApp

Pipeline de triagem conversacional via WhatsApp usando perguntas WSI:

```
Recrutador dispara triagem (via chat LIA ou batch)
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Selecao de Perguntas                                     │
│    WSIScreeningPipeline gera set de perguntas (Blocos 2-5)  │
│    Ver fluxo completo em §5.4 "Criacao de Perguntas WSI"    │
├─────────────────────────────────────────────────────────────┤
│ 2. Consentimento LGPD                                       │
│    WhatsApp: mensagem de opt-in antes de iniciar triagem    │
│    Candidato deve aceitar para prosseguir                    │
├─────────────────────────────────────────────────────────────┤
│ 3. Envio Sequencial de Perguntas                            │
│    WhatsAppService.send_message() ou send_interactive()     │
│    Provider: TwilioWhatsAppService (producao)               │
│    Modo dev: _send_development() (simula envio)             │
├─────────────────────────────────────────────────────────────┤
│ 4. Recepcao de Respostas                                    │
│    Twilio webhook → parse_webhook_message()                 │
│    Suporta: texto, audio (transcricao Deepgram), documento  │
├─────────────────────────────────────────────────────────────┤
│ 5. Interpretacao por LLM                                    │
│    interpret_context_llm_service.py                         │
│    Extrai dados estruturados da resposta livre              │
│    Avalia qualidade e completude da resposta                │
├─────────────────────────────────────────────────────────────┤
│ 6. Scoring Deterministico                                   │
│    wsi_deterministic_scorer.py                              │
│    Pontuacao por bloco WSI com pesos configurados            │
├─────────────────────────────────────────────────────────────┤
│ 7. Proxima Pergunta ou Finalizacao                          │
│    Loop ate esgotar perguntas do set                         │
│    Opt-out: candidato pode sair a qualquer momento           │
├─────────────────────────────────────────────────────────────┤
│ 8. Resultado Final                                          │
│    Score agregado + classificacao WSI                        │
│    (excelente/alto/medio/regular/baixo)                     │
│    Disponivel no pipeline do recrutador                      │
└─────────────────────────────────────────────────────────────┘
```

**Status do adapter**: WhatsAppService funcional com Twilio (`send_message`, `send_template`, `send_interactive`). Dois providers: `TwilioWhatsAppService` (producao) e `WhatsAppMetaService` (Meta Cloud API). Modo development com simulacao de envio disponivel.

**Arquivos-chave**: `whatsapp_service.py` (servico principal), `whatsapp_twilio_service.py` (provider Twilio), `whatsapp_meta_service.py` (provider Meta), `whatsapp_factory.py` (factory de providers), `interpret_context_llm_service.py` (interpretacao IA), `wsi_deterministic_scorer.py` (scoring)

**Compliance**: Consentimento LGPD obrigatorio antes do envio | PII masking nas respostas armazenadas | Opt-out a qualquer momento | Webhook signature validation (`verify_webhook_signature`)

### 5.7 interview_scheduling — Agendamento de Entrevistas

Dominio de agendamento de entrevistas com integracao de calendario e transcricao.

```
app/domains/interview_scheduling/
├── agents/
│   ├── scheduling_agent.py           ← Agente de agendamento (legacy)
│   ├── entrevistador_agent.py        ← Agente entrevistador (legacy)
│   └── interview_scheduling_nodes.py ← Nos de agendamento
├── services/
│   ├── scheduling_service.py         ← Servico de agendamento
│   ├── calendar_service.py           ← Integracao de calendario
│   ├── deepgram_service.py           ← Transcricao Deepgram
│   └── interview_transcript_analysis_service.py ← Analise de transcricoes
├── models/
│   ├── interview.py                  ← Modelo de entrevista
│   └── self_scheduling.py            ← Modelo de auto-agendamento
└── schemas/
    ├── calendar.py                   ← Schema de calendario
    └── interview_scheduling_state.py ← Estado do agendamento
```

**Conexoes**: Microsoft Graph (calendario), Deepgram (transcricao), LLM (analise de entrevista)

#### Fluxo: Agendamento de Entrevistas

Pipeline completo desde a solicitacao ate o envio de convite:

```
Recrutador: "agendar entrevista com Joao para sexta as 14h"
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Roteamento via ConversationGraph                         │
│    Intent: agendar_entrevista (risco medio)                 │
│    → Interview subgrafo (6 nos)                             │
├─────────────────────────────────────────────────────────────┤
│ 2. Coleta de Dados (interview_details_collector)            │
│    candidate_id, data/hora, entrevistador(es),              │
│    tipo (presencial/online/hibrido), duracao, local/link    │
│    LLM extrai parametros da mensagem natural                │
├─────────────────────────────────────────────────────────────┤
│ 3. Validacao (interview_validator)                          │
│    Verifica: candidato existe, horario disponivel,           │
│    entrevistador tem agenda livre                            │
│    calendar_service.py consulta disponibilidade              │
├─────────────────────────────────────────────────────────────┤
│ 4. Confirmacao do Recrutador (Human-in-the-Loop)            │
│    LIA apresenta resumo da entrevista para confirmacao       │
│    Recrutador confirma via chat (§4 Confirmation Patterns)   │
├─────────────────────────────────────────────────────────────┤
│ 5. Criacao da Entrevista                                    │
│    SchedulingService.create_interview_with_teams()           │
│    → Microsoft Graph: cria evento no calendario + link Teams │
│    Fallback: create_fallback_interview_with_ics()            │
│    → Gera arquivo .ics quando MS Graph indisponivel          │
├─────────────────────────────────────────────────────────────┤
│ 6. Envio de Convite                                         │
│    send_interview_invite() → email ao candidato              │
│    send_interview_confirmation() → confirmacao ao recrutador │
│    Canais: email (principal) + WhatsApp (opcional)           │
├─────────────────────────────────────────────────────────────┤
│ 7. Self-Scheduling (alternativo)                            │
│    Modelo self_scheduling.py                                │
│    Candidato recebe link para escolher horario               │
│    Disponibilidades pre-aprovadas pelo recrutador            │
└─────────────────────────────────────────────────────────────┘
```

**Arquivos-chave**: `scheduling_service.py` (orquestrador, 15+ metodos), `calendar_service.py` (integracao calendario), `deepgram_service.py` (transcricao pos-entrevista), `interview_transcript_analysis_service.py` (analise IA)

**Modelos de dados**: `interview.py` (entrevista principal), `self_scheduling.py` (auto-agendamento), `interview_scheduling_state.py` (estado do fluxo)

**Compliance**: Confirmacao obrigatoria antes de agendar (risco medio) | Notificacao ao candidato em todos os cenarios | Fallback .ics garante funcionamento sem MS Graph | Registro em audit log

### 5.8 analytics — Relatorios e Metricas

Dominio de analytics, relatorios e metricas preditivas.

```
app/domains/analytics/
├── agents/
│   ├── analytics_agent.py            ← Agente de analytics (legacy)
│   └── analista_feedback_agent.py    ← Agente de feedback (legacy)
├── services/
│   ├── report_service.py             ← Servico de relatorios
│   ├── candidate_report_service.py   ← Relatorios de candidatos
│   ├── job_report_service.py         ← Relatorios de vagas
│   ├── job_insights_service.py       ← Insights de vagas
│   ├── job_analytics_prompt_service.py ← Prompts analiticos
│   ├── predictive_analytics_service.py ← Analytics preditivo
│   ├── search_analytics_service.py   ← Analytics de busca
│   ├── wizard_analytics_service.py   ← Analytics do wizard
│   ├── agent_monitoring_service.py   ← Monitoramento de agentes
│   └── wsi_observability.py          ← Observabilidade WSI
├── tools/
│   ├── analytics_query_tools.py      ← Tools de query analitica
│   └── query_tools.py               ← Tools de query SQL
├── models/
│   ├── health_check.py               ← Modelo de health check
│   ├── lia_profile_analysis.py       ← Modelo de perfil LIA
│   ├── observability.py              ← Modelo de observabilidade
│   └── saas_metrics.py               ← Modelo de metricas SaaS
└── schemas/
```

**Conexoes**: SQL (queries analiticas diretas), Prometheus (metricas), LLM (analytics preditivo)

### 5.9 ats_integration — Integracao com ATS

Dominio de integracao com sistemas ATS externos (Applicant Tracking Systems).

```
app/domains/ats_integration/
├── agents/
│   └── integrador_ats_agent.py       ← Agente integrador (legacy)
├── services/
│   ├── ats_sync_service.py           ← Sincronizacao com ATS
│   ├── gupy_service.py               ← Servico Gupy
│   ├── pandape_service.py            ← Servico Pandape
│   ├── merge_ats_service.py          ← Servico Merge
│   └── ats_clients/
│       ├── base.py                   ← Interface base de ATS
│       ├── gupy.py                   ← Cliente Gupy
│       ├── pandape.py                ← Cliente Pandape
│       └── merge.py                  ← Cliente Merge.dev
└── models/
```

**Conexoes**: APIs externas (Gupy, Pandape, Merge.dev), cryptography (chaves de API criptografadas)

### 5.10 automation — Automacoes e Tarefas Programadas

Dominio de automacoes do pipeline, alertas proativos e tarefas em background.

```
app/domains/automation/
├── agents/
│   └── task_planner_agent.py         ← Agente de planejamento (legacy)
├── services/
│   ├── automation_service.py         ← Servico principal de automacao
│   ├── automation_handlers.py        ← Handlers de automacao
│   ├── automation_scheduler.py       ← Scheduler de automacoes
│   ├── automation_trigger_service.py ← Servico de triggers
│   ├── autonomous_agent_service.py   ← Servico de agentes autonomos
│   ├── stage_automation_engine.py    ← Engine de automacao de estagios
│   ├── stage_transition_automation.py ← Automacao de transicoes
│   ├── pipeline_monitor.py           ← Monitor de pipeline
│   ├── proactive_service.py          ← Servico proativo
│   ├── proactive_alert_service.py    ← Alertas proativos
│   ├── candidate_context_aggregator.py ← Agregador de contexto
│   ├── prediction_action_bridge.py   ← Ponte predicao-acao
│   ├── event_action_connector.py     ← Conector evento-acao
│   ├── pattern_applier.py            ← Aplicador de padroes
│   ├── learning_automation.py        ← Aprendizado de automacoes
│   ├── planned_task_service.py       ← Servico de tarefas planejadas
│   ├── task_service.py               ← Servico de tarefas
│   └── webhook_adapters.py           ← Adaptadores de webhook
├── models/
│   ├── automation.py                 ← Modelo de automacao
│   ├── recruitment_stages.py         ← Modelo de estagios
│   ├── planned_task.py               ← Modelo de tarefa planejada
│   └── task.py                       ← Modelo de tarefa
└── tools/
```

**Conexoes**: Celery (processamento em background), APScheduler (agendamento), Redis (broker), todos os outros dominios (triggers de automacao)

### Arquivos Base de Dominios

Alem dos 10 dominios, existem 3 arquivos base que definem a infraestrutura comum:

| Arquivo | Para que serve |
|---|---|
| `domains/base.py` | Classe base dos dominios — interface comum herdada por todos |
| `domains/workflow.py` | Fluxo base de dominio — ciclo de vida padrao (init → process → respond) |
| `domains/registry.py` | Registro de dominios — lookup dinamico por nome para o roteador |

---

## 6. Catalogo Completo de Agentes

### Visao Geral

| # | Agente | Dominio | Tipo | Tools | O que faz |
|---|---|---|---|---|---|
| 1 | WizardReActAgent | job_management | ReAct | 9 | Guia criacao de vagas com enriquecimento IA |
| 2 | KanbanReActAgent | recruiter_assistant | ReAct | 14 | Gestao de pipeline de candidatos |
| 3 | TalentReActAgent | recruiter_assistant | ReAct | 12 | Busca e analise de candidatos |
| 4 | JobsMgmtReActAgent | recruiter_assistant | ReAct | 13 | Gestao de portfolio de vagas |
| 5 | PolicyReActAgent | hiring_policy | ReAct | 13 | Config de politicas de contratacao |
| 6 | SourcingReActAgent | sourcing | ReAct | 14 | Busca ativa e outreach de candidatos |
| 7 | PipelineReActAgent | cv_screening | ReAct | 14 | Triagem e movimentacao no pipeline |
| 8 | JobWizardGraph | job_management | LangGraph | - | Grafo de estado do wizard (6 nos) |
| 9 | JobDraftingAgent | job_management | Legacy | - | Rascunho de descricao de vaga |
| 10 | JobIntakeAgent | job_management | Legacy | - | Intake de requisitos de vaga |
| 11 | JobLifecycleAgent | job_management | Legacy | - | Ciclo de vida da vaga |
| 12 | JobInsightsAgent | job_management | Legacy | - | Insights sobre vagas |
| 13 | JobBenefitsCompAgent | job_management | Legacy | - | Beneficios e compensacao |
| 14 | JobRubricAgent | job_management | Legacy | - | Rubricas de avaliacao |
| 15 | RecruiterAssistantAgent | recruiter_assistant | Legacy | - | Assistente geral (fallback) |
| 16 | ScreeningAgent | cv_screening | Legacy | - | Screening de candidatos |
| 17 | AvaliadorWSIAgent | cv_screening | Legacy | - | Avaliacao WSI |
| 18 | TriagemCurricularAgent | cv_screening | Legacy | - | Triagem curricular |
| 19 | SourcingAgent | sourcing | Legacy | - | Sourcing (fallback) |
| 20 | CommunicationAgent | communication | Legacy | - | Comunicacao multi-canal |
| 21 | SchedulingAgent | interview_scheduling | Legacy | - | Agendamento de entrevistas |
| 22 | EntrevistadorAgent | interview_scheduling | Legacy | - | Conducao de entrevistas |
| 23 | AnalyticsAgent | analytics | Legacy | - | Relatorios e analytics |
| 24 | AnalistaFeedbackAgent | analytics | Legacy | - | Analise de feedback |
| 25 | IntegradorATSAgent | ats_integration | Legacy | - | Integracao com ATS |
| 26 | TaskPlannerAgent | automation | Legacy | - | Planejamento de tarefas |

### Tipos de Agente

- **ReAct (7)**: Agentes autonomos que raciocinam, decidem e executam acoes via tools. Seguem o padrao de 4 arquivos. Usam `ReActLoop` com `ReActConfig`.
- **LangGraph (1)**: Grafo de estado com nos fixos e transicoes definidas. Usado para o wizard que tem 6 etapas sequenciais.
- **Legacy (18)**: Agentes com pipeline fixo. Recebem input, processam e retornam output sem raciocinio autonomo. Feature flag `USE_REACT_AGENTS` controla routing entre ReAct e Legacy com fallback automatico.

---

## 7. Agentes ReAct em Detalhe

### ReActLoop — Ciclo Iterativo (shared/agents/react_loop.py)

```
┌─ REASON ─┐    ┌── ACT ──┐    ┌─ OBSERVE ─┐    ┌─ DECIDE ─┐
│ LLM gera │───▶│ Executa │───▶│ Resultado │───▶│ Continua │──┐
│ reasoning│    │ tool    │    │ da tool   │    │ ou para  │  │
└──────────┘    └─────────┘    └───────────┘    └──────────┘  │
     ▲                                                │ loop  │
     └────────────────────────────────────────────────┘       │
                                                         ▼ final_answer
```

**ReActConfig (parametros principais)**:

| Parametro | Default | Descricao |
|---|---|---|
| `max_iterations` | 5 | Maximo de ciclos reason-act-observe antes de forcar resposta |
| `domain` | (obrigatorio) | Dominio do agente (wizard, pipeline, talent, etc.) |
| `guardrails` | [] | Acoes que exigem confirmacao do usuario antes de executar |
| `model_provider` | "claude" | Provider LLM: "claude", "gemini" ou "openai" |
| `model_name` | "claude-sonnet-4-20250514" | Modelo especifico para referencia/logging |
| `temperature` | 0.3 | Temperatura de geracao do LLM |
| `system_prompt` | (obrigatorio) | Prompt que define personalidade e instrucoes do agente |

Usado por todos os 7 agentes ReAct (Wizard, Kanban, Talent, JobsMgmt, Policy, Sourcing, Pipeline), cada um com seu proprio `ReActConfig`.

### Tabela de Arquivo por Tipo

| Tipo de Arquivo | O que controla | Nivel de Garantia | Quando mexer |
|---|---|---|---|
| `*_system_prompt.py` | Tom, personalidade, regras gerais | Soft (LLM pode ignorar) | Mudar comportamento conversacional |
| `*_tool_registry.py` | Acoes concretas com codigo Python | Hard (codigo executado) | Adicionar/modificar capacidades |
| `*_react_agent.py` | Orquestracao do ciclo ReAct | Hard (fluxo controlado) | Mudar como o agente processa |
| `*_stage_context.py` | Contexto injetado por estagio | Medio (orienta o LLM) | Mudar campos/instrucoes por estagio |

### 7.1 WizardReActAgent (9 tools)

```
app/domains/job_management/agents/
├── wizard_react_agent.py         ← Classe do agente
├── wizard_system_prompt.py       ← Prompt (191 linhas)
├── wizard_tool_registry.py       ← 9 tools (471 linhas)
└── wizard_stage_context.py       ← 6 estagios
```

| Tool | Tipo | O que faz |
|---|---|---|
| `validate_job_requirements` | Compliance | Valida texto contra FairnessGuard (regex + semantico LLM) |
| `get_salary_benchmarks` | Leitura | Retorna benchmark salarial por cargo/senioridade com fontes |
| `search_salary_benchmark` | Leitura | Busca benchmark salarial por query livre |
| `validate_job_fields` | Leitura | Valida campos da vaga (titulo, departamento, etc) |
| `get_job_suggestions` | Leitura | Sugere melhorias para a vaga via IA |
| `save_job_draft` | Acao | Salva rascunho da vaga no banco |
| `get_company_config` | Leitura | Retorna config da empresa (porte, setor, politicas) |
| `generate_enriched_jd` | Acao | Gera descricao enriquecida via LLM |
| `check_job_draft_health` | Proativa | Avalia saude do rascunho antes de publicar |

**STAGE_TOOLS**:
- `input-evaluation`: validate_job_requirements, validate_job_fields, get_company_config, check_job_draft_health
- `jd-enrichment`: generate_enriched_jd, get_job_suggestions, validate_job_requirements
- `salary`: get_salary_benchmarks, search_salary_benchmark
- `competencies`: get_job_suggestions, validate_job_requirements
- `wsi-questions`: validate_job_requirements
- `review-publish`: save_job_draft, check_job_draft_health, validate_job_fields

**Grafo LangGraph do Wizard (JobWizardGraph)**

O Wizard tambem usa uma maquina de estados com interface similar a LangGraph
(arquivo: `job_management/agents/job_wizard_graph.py`).

```
              ┌──────────────────┐
              │  intent_         │  Classifica: START_FROM_SCRATCH, PROVIDE_INFO,
              │  classifier      │  MODIFY, SKIP, GO_BACK, CONFIRM, HELP...
              └────────┬─────────┘
                       │
         ┌─────────────┼──────────────────────┐
         v             v                      v
  ┌────────────┐ ┌───────────┐         ┌────────────┐
  │START_FROM_ │ │PROVIDE_   │         │SKIP /      │
  │SCRATCH /   │ │INFO /     │         │GO_BACK /   │
  │TEMPLATE    │ │MODIFY     │         │CONFIRM     │
  └──────┬─────┘ └─────┬─────┘         └──────┬─────┘
         │             v                      v
         │      ┌────────────┐         ┌────────────┐
         │      │ field_     │         │ stage_     │
         │      │ extractor  │         │ transition │
         │      └──────┬─────┘         └──────┬─────┘
         │             v                      │
         │      ┌────────────┐                │
         │      │ tool_router│                │
         │      └──────┬─────┘                │
         │        ┌────┴────┐                 │
         │        v         v                 │
         │  tool_executor  response_          │
         │        │        generator          │
         │        v            │              │
         │  response_gen.      │              │
         │        │            │              │
         └────────┴────────────┴──────────────┘
                       │
                       v
                stage_transition → END ou loop
```

| Node | Funcao |
|---|---|
| `intent_classifier` | Classifica o que o recrutador quer (10 intents via `WizardIntent` enum) |
| `field_extractor` | Extrai campos estruturados da mensagem via LLM |
| `tool_router` | Decide se precisa chamar tools ou responder direto |
| `tool_executor` | Executa a tool selecionada (das 9 tools do registry) |
| `response_generator` | Gera resposta formatada com base nos resultados |
| `stage_transition` | Avanca/retrocede estagio se os campos estao completos |

**Conditional Edges (roteamento em runtime)**:

```
intent_classifier:
  ├─ [prio 3] intent ∈ {START_FROM_SCRATCH, USE_EXISTING, USE_TEMPLATE} → response_generator
  ├─ [prio 2] intent ∈ {HELP, ASK_QUESTION}                            → response_generator
  ├─ [prio 1] intent ∈ {PROVIDE_INFO, MODIFY}                          → field_extractor
  ├─ [prio 1] intent ∈ {SKIP, GO_BACK, CONFIRM}                        → stage_transition
  └─ [prio 0] fallback                                                  → field_extractor

tool_router:
  ├─ [prio 1] len(tool_calls) > 0  → tool_executor
  └─ [prio 0] sem tool_calls       → response_generator

stage_transition:
  ├─ [prio 1] !should_continue     → END
  └─ [prio 0] should_continue      → intent_classifier (loop)
```

**Protecao contra loops**: `MAX_ITERATIONS = 10` (hardcoded).

> Para detalhes completos do LangGraph (ConversationGraph com 47 nos e 4 subgrafos), ver Secao 4.

### 7.2 KanbanReActAgent (14 tools)

```
app/domains/recruiter_assistant/agents/
├── kanban_react_agent.py         ← Classe do agente
├── kanban_system_prompt.py       ← Prompt
├── kanban_tool_registry.py       ← 14 tools
└── kanban_stage_context.py       ← Estagios do pipeline
```

| Tool | Tipo | O que faz |
|---|---|---|
| `get_pipeline_benchmarks` | Leitura | Benchmarks de pipeline com fontes (Gupy, LinkedIn) |
| `get_pipeline_summary` | Leitura | Resumo do pipeline (candidatos por estagio) |
| `get_stage_metrics` | Leitura | Metricas detalhadas de um estagio |
| `list_stage_candidates` | Leitura | Lista candidatos de um estagio |
| `analyze_stage` | Leitura | Analise profunda de um estagio |
| `identify_bottlenecks` | Leitura | Identifica gargalos no pipeline |
| `get_candidate_aging` | Leitura | Tempo de permanencia por candidato |
| `compare_stages` | Leitura | Compara metricas entre estagios |
| `suggest_movements` | Leitura | Sugere movimentacoes de candidatos |
| `batch_move_candidates` | Acao | Move multiplos candidatos entre estagios |
| `send_batch_communication` | Acao | Envia comunicacao em lote |
| `start_screening_batch` | Acao | Inicia triagem em lote |
| `generate_pipeline_report` | Acao | Gera relatorio do pipeline |
| `check_rejection_fairness` | Compliance | Verifica fairness em rejeicoes via FairnessGuard |

### 7.3 TalentReActAgent (12 tools)

```
app/domains/recruiter_assistant/agents/
├── talent_react_agent.py         ← Classe do agente
├── talent_system_prompt.py       ← Prompt
├── talent_tool_registry.py       ← 12 tools
└── talent_stage_context.py       ← Estagios
```

| Tool | Tipo | O que faz |
|---|---|---|
| `search_candidates` | Leitura | Busca candidatos por criterios |
| `list_candidates` | Leitura | Lista candidatos com filtros |
| `view_candidate_profile` | Leitura | Perfil completo de um candidato |
| `compare_candidates` | Leitura | Compara candidatos lado a lado |
| `rank_candidates` | Leitura | Ranking de candidatos por score |
| `analyze_skills` | Leitura | Analise de skills de candidatos |
| `recommend_actions` | Leitura | Recomenda acoes para candidatos |
| `create_shortlist` | Acao | Cria shortlist de candidatos |
| `export_report` | Acao | Exporta relatorio de candidatos |
| `check_search_fairness` | Compliance | Verifica fairness nos criterios de busca |
| `get_talent_pool_benchmarks` | Leitura | Benchmarks do pool de talentos |
| `check_pool_health` | Proativa | Avalia saude do pool de candidatos |

### 7.4 JobsMgmtReActAgent (13 tools)

```
app/domains/recruiter_assistant/agents/
├── jobs_mgmt_react_agent.py      ← Classe do agente
├── jobs_mgmt_system_prompt.py    ← Prompt
├── jobs_mgmt_tool_registry.py    ← 13 tools
└── jobs_mgmt_stage_context.py    ← Estagios
```

| Tool | Tipo | O que faz |
|---|---|---|
| `validate_job_action_fairness` | Compliance | Valida fairness antes de acoes em vagas |
| `get_recruitment_benchmarks` | Leitura | Benchmarks de recrutamento com fontes |
| `list_jobs` | Leitura | Lista vagas com filtros |
| `view_job_details` | Leitura | Detalhes de uma vaga |
| `get_portfolio_metrics` | Leitura | Metricas do portfolio de vagas |
| `compare_jobs` | Leitura | Compara vagas lado a lado |
| `check_sla` | Leitura | Verifica SLA de vagas |
| `analyze_bottlenecks` | Leitura | Analisa gargalos de vagas |
| `pause_job` | Acao | Pausa uma vaga |
| `reopen_job` | Acao | Reabre uma vaga |
| `close_job` | Acao | Fecha uma vaga |
| `update_priority` | Acao | Atualiza prioridade de uma vaga |
| `generate_report` | Acao | Gera relatorio de vagas |

### 7.5 PolicyReActAgent (13 tools)

```
app/domains/hiring_policy/agents/
├── policy_react_agent.py         ← Classe do agente
├── policy_system_prompt.py       ← Prompt
├── policy_tool_registry.py       ← 13 tools
└── policy_stage_context.py       ← 3 estagios
```

| Tool | Tipo | O que faz |
|---|---|---|
| `get_current_policy` | Leitura | Retorna politica atual da empresa |
| `save_policy_field` | Acao | Salva campo individual da politica |
| `save_policy_block` | Acao | Salva bloco completo de politica |
| `get_policy_summary` | Leitura | Resumo da politica |
| `validate_policy_compliance` | Compliance | Valida compliance da politica (FairnessGuard) |
| `get_company_context` | Leitura | Contexto da empresa (porte, setor) |
| `get_industry_benchmarks` | Leitura | Benchmarks do setor (8 setores, fontes ABRH/GPTW) |
| `get_platform_benchmarks` | Leitura | Benchmarks da plataforma |
| `explain_policy_impact` | Leitura | Explica impacto de uma politica |
| `get_setup_progress` | Leitura | Progresso do setup de politicas |
| `apply_industry_defaults` | Acao | Aplica defaults do setor |
| `detect_policy_impact_anomalies` | Proativa | Detecta anomalias no impacto de politicas |
| `get_policy_effectiveness_report` | Leitura | Relatorio de efetividade |

**Estagios**: onboarding → review → consulting

### 7.6 SourcingReActAgent (14 tools)

```
app/domains/sourcing/agents/
├── sourcing_react_agent.py       ← Classe do agente
├── sourcing_system_prompt.py     ← Prompt
├── sourcing_tool_registry.py     ← 14 tools
└── sourcing_stage_context.py     ← Estagios
```

| Tool | Tipo | O que faz |
|---|---|---|
| `set_search_criteria` | Acao | Define criterios de busca |
| `suggest_skills` | Leitura | Sugere skills complementares |
| `search_candidates` | Leitura | Busca candidatos em bases |
| `filter_results` | Leitura | Filtra resultados de busca |
| `view_candidate` | Leitura | Perfil detalhado de candidato |
| `analyze_profile` | Leitura | Analise profunda de perfil |
| `compare_candidates` | Leitura | Compara candidatos |
| `score_candidate` | Leitura | Scoring de candidato |
| `add_to_shortlist` | Acao | Adiciona a shortlist |
| `remove_from_shortlist` | Acao | Remove da shortlist |
| `rank_candidates` | Leitura | Ranking de candidatos |
| `send_outreach` | Acao | Envia mensagem de outreach |
| `generate_message` | Leitura | Gera mensagem personalizada |
| `track_response` | Acao | Rastreia resposta de candidato |

**Estagios**: criteria → search → evaluate → engage

### 7.7 PipelineReActAgent (14 tools)

```
app/domains/cv_screening/agents/
├── pipeline_react_agent.py       ← Classe do agente
├── pipeline_system_prompt.py     ← Prompt
├── pipeline_tool_registry.py     ← 14 tools
└── pipeline_stage_context.py     ← Estagios
```

| Tool | Tipo | O que faz |
|---|---|---|
| `view_candidate_profile` | Leitura | Perfil completo do candidato |
| `move_candidate` | Acao | Move candidato entre estagios |
| `analyze_cv` | Leitura | Analisa curriculo com IA |
| `run_wsi_screening` | Acao | Executa screening WSI |
| `schedule_interview` | Acao | Agenda entrevista |
| `send_communication` | Acao | Envia comunicacao ao candidato |
| `add_notes` | Acao | Adiciona notas ao candidato |
| `batch_move` | Acao | Move candidatos em lote |
| `add_to_shortlist` | Acao | Adiciona a shortlist |
| `view_screening_results` | Leitura | Resultados do screening |
| `view_interview_notes` | Leitura | Notas da entrevista |
| `generate_offer` | Acao | Gera proposta |
| `finalize_hiring` | Acao | Finaliza contratacao |
| `update_status` | Acao | Atualiza status do candidato |

**Estagios**: screening → evaluation → interview → offer → hiring

---

## 8. Infraestrutura Compartilhada (~118 arquivos)

### Arvore Completa de `shared/`

```
app/shared/
├── agents/                           ← Core dos agentes
│   ├── agent_interface.py            ← BaseAgent, AgentInput, AgentOutput
│   ├── react_loop.py                 ← ReActLoop, ReActConfig, ToolDefinition
│   ├── working_memory.py             ← WorkingMemoryService (sessao)
│   ├── long_term_memory.py           ← LongTermMemoryService (cross-session)
│   ├── memory_integration.py         ← Ponte WorkingMemory ↔ LongTermMemory
│   ├── react_agent_registry.py       ← ReactAgentRegistry (singleton)
│   ├── agent_scaffold.py             ← AgentScaffold.generate() (4 arquivos)
│   ├── execution_log_store.py        ← Persiste reasoning chains
│   ├── observability.py              ← ReActObserver (telemetria)
│   ├── proactive_worker.py           ← Worker para sugestoes proativas
│   ├── enhanced_agent_mixin.py       ← Mixin com capacidades extras
│   ├── conversation.py               ← Gestao de conversacao
│   ├── nodes.py                      ← Nos genericos de grafo
│   ├── state_machine.py              ← Maquina de estados
│   ├── learning_extractor.py         ← Extracao de aprendizados
│   ├── autonomy_engine.py            ← Engine de autonomia
│   └── sourcing_engagement_nodes.py  ← Nos de engajamento sourcing
│
├── compliance/                       ← Conformidade e etica
│   ├── fairness_guard.py             ← FairnessGuard: check() + check_semantic()
│   ├── audit_service.py              ← Auditoria de acoes
│   └── fact_checker.py               ← Verificacao de fatos
│
├── intelligence/                     ← Capacidades de IA
│   ├── embedding_service.py          ← Geracao de embeddings
│   ├── semantic_search_service.py    ← Busca semantica
│   ├── smart_extractor.py            ← Extracao inteligente de dados
│   └── param_patterns.py             ← Padroes de parametros
│
├── learning/                         ← Aprendizado continuo
│   ├── learning_loop_service.py      ← Loop de aprendizado
│   ├── ab_testing_service.py         ← A/B testing
│   ├── finetuning_export.py          ← Exportacao para fine-tuning
│   └── template_learning_service.py  ← Aprendizado de templates
│
├── memory/                           ← Memoria de conversacao
│   ├── conversation_state.py         ← Estado da conversacao
│   └── reference_resolver.py         ← Resolucao de referencias
│
├── providers/                        ← Provedores de servicos externos
│   ├── llm_factory.py                ← LLMProviderFactory (factory principal)
│   ├── llm_provider.py               ← Interface base de LLM
│   ├── llm_client.py                 ← Cliente LLM generico
│   ├── llm_claude.py                 ← Provider Claude (Anthropic)
│   ├── llm_openai.py                 ← Provider OpenAI
│   ├── llm_gemini.py                 ← Provider Gemini (Google)
│   ├── voice_provider.py             ← Provider de voz (Deepgram/OpenMic)
│   └── ats_factory.py                ← Factory de clientes ATS
│
├── channels/                         ← Comunicacao multi-canal
│   ├── multi_channel_service.py      ← Servico unificado
│   ├── channel_router.py             ← Roteamento inteligente
│   ├── channel_adapter.py            ← Interface base
│   └── adapters/
│       ├── email_adapter.py          ← Adapter de email
│       ├── whatsapp_adapter.py       ← Adapter WhatsApp
│       ├── sms_adapter.py            ← Adapter SMS
│       ├── teams_adapter.py          ← Adapter Teams
│       └── in_app_adapter.py         ← Adapter in-app
│
├── execution/                        ← Planos de acao
│   ├── action_planner.py             ← Planejador de acoes
│   ├── plan_executor.py              ← Executor de planos
│   ├── plan_detector.py              ← Detector de planos
│   ├── plan_templates.py             ← Templates de planos
│   └── execution_plan.py             ← Modelo de plano
│
├── resilience/                       ← Resiliencia e cache
│   ├── circuit_breaker.py            ← Circuit breaker para falhas
│   ├── cache_manager_service.py      ← Gerenciador de cache
│   └── stats_manager.py              ← Gerenciador de estatisticas
│
├── robustness/                       ← Robustez e validacao
│   ├── error_handling.py             ← Tratamento de erros
│   ├── input_validation.py           ← Validacao de inputs
│   ├── response_filter.py            ← Filtro de respostas
│   ├── defensive_prompts.py          ← Prompts defensivos
│   ├── enhanced_base.py              ← Base melhorada
│   ├── enhanced_registry.py          ← Registry melhorado
│   ├── context_management.py         ← Gestao de contexto
│   └── intent_schemas.py             ← Schemas de intencao
│
├── prompts/                          ← Prompts e exemplos
│   ├── prompt_registry.py            ← Registry de prompts
│   ├── agent_prompts.py              ← Prompts de agentes
│   └── examples/
│       ├── job_planner_examples.py   ← Exemplos job planner
│       ├── orchestrator_examples.py  ← Exemplos orquestrador
│       ├── pipeline_examples.py      ← Exemplos pipeline
│       └── sourcing_examples.py      ← Exemplos sourcing
│
├── governance/                       ← Governanca
│   ├── feature_flag_service.py       ← Feature flags
│   └── agent_monitoring_service.py   ← Monitoramento de agentes
│
├── repositories/                     ← Acesso a dados
│   ├── base.py                       ← Repository base
│   ├── sqlalchemy_base.py            ← Base SQLAlchemy
│   ├── candidate_repository.py       ← CRUD de candidatos
│   ├── company_repository.py         ← CRUD de empresas
│   ├── job_repository.py             ← CRUD de vagas
│   └── notification_repository.py    ← CRUD de notificacoes
│
├── async_processing/                 ← Processamento assincrono
│   ├── enhanced_task_manager.py      ← Task manager com persistencia
│   ├── task_manager.py               ← Task manager base
│   ├── task_persistence.py           ← Persistencia de tasks no DB
│   ├── task_scheduler.py             ← Scheduler com cron parser
│   └── task_queue.py                 ← Fila de tasks com DLQ
│
├── tools/                            ← Tools compartilhadas
│   ├── export_tools.py               ← Exportacao (PDF, Excel)
│   ├── insight_tools.py              ← Insights e analytics
│   ├── predictive_tools.py           ← Predicoes (dropout, tempo)
│   └── proactive_tools.py            ← Alertas proativos
│
├── ab_testing.py                     ← A/B testing (modulo raiz)
├── cache_strategy.py                 ← Estrategia de cache
├── delegation_fallback.py            ← Fallback de delegacao
├── domain_action_registry.py         ← Registry de acoes por dominio
├── encryption.py                     ← Criptografia (AES/RSA)
├── param_validation.py               ← Validacao de parametros
├── pii_masking.py                    ← Mascaramento de PII (LGPD)
├── policy_helper.py                  ← Helper de politicas
├── policy_middleware.py              ← Middleware de politicas
├── policy_sync_service.py            ← Sincronizacao de politicas
├── prompt_injection.py               ← Guard contra prompt injection
├── structured_logging.py             ← Logging JSON estruturado
├── tracing.py                        ← Tracing distribuido (request_id)
└── mixins/
    └── serializable.py               ← Mixin de serializacao
```

### Diagrama de Conexoes

```
FairnessGuard ──→ WizardAgent, KanbanAgent, TalentAgent, JobsMgmtAgent, PolicyAgent
                  (check regex + check_semantic LLM + check_implicit_bias)

ReActLoop ──────→ Todos os 7 agentes ReAct
                  (ciclo autonomo de raciocinio)

LLMFactory ─────→ ReActLoop, agentes legacy, servicos de geracao
                  (Claude, Gemini, OpenAI)

WorkingMemory ──→ Todos os agentes ReAct (memoria de sessao)
LongTermMemory ─→ Todos os agentes ReAct (memoria cross-session)

CircuitBreaker ─→ LLMFactory, servicos externos
                  (protecao contra falhas em cascata)

PIIMasking ─────→ Logs, respostas, exports
                  (mascaramento de dados pessoais - LGPD)
```

### Destaques Criticos

**FairnessGuard** (`compliance/fairness_guard.py`):
- `check(text)`: Validacao por regex (termos proibidos, padroes discriminatorios)
- `check_implicit_bias(text)`: Deteccao de vies implicito por padroes
- `check_semantic(text)`: Analise semantica via LLM para vies sutil
- Usado por 5 agentes ReAct como guardrail obrigatorio

**ReActLoop** (`agents/react_loop.py`):
- Core do sistema de agentes autonomos
- Configuravel via `ReActConfig` (max_iterations, tools, provider, guardrails)
- Suporta observer para telemetria (`ReActObserver`)
- 705 linhas de codigo

**LLMProviderFactory** (`providers/llm_factory.py`):
- Factory pattern para 3 providers (Claude, Gemini, OpenAI)
- Selecionavel via string: `"claude"`, `"gemini"`, `"openai"`
- Default: `"claude"` (configuravel por agente)

**Compliance — 3 Pilares** (`compliance/`):

```
┌─────────────────────────────────────────────────────┐
│              CAMADA DE COMPLIANCE                    │
├──────────────┬──────────────┬────────────────────────┤
│    LGPD      │    SOX       │     EU AI Act          │
│ (Dados Pess.)│ (Auditoria)  │ (IA Responsavel)       │
├──────────────┴──────────────┴────────────────────────┤
│            COMPONENTES DE ENFORCEMENT                │
│                                                      │
│  FairnessGuard     FactChecker       AuditService    │
│  (anti-bias        (validacao        (log de todas   │
│   3 camadas)       numerica com      as decisoes     │
│                    ranges fixos)     de IA)          │
│                                                      │
│  PolicyEngine      LGPD API          Tool Registry   │
│  (regras de        (consent mgmt,    (RBAC de tools  │
│   negocio)         portal titular)   por role)       │
└──────────────────────────────────────────────────────┘
```

Todo dev que cria tools ou agentes DEVE garantir que:
- Texto do usuario passa por `FairnessGuard.check()` antes de processar
- Dados numericos (salario, scores) sao validados pelo `FactChecker`
- Acoes sao registradas no `AuditService` para rastreabilidade

> Para detalhes completos de compliance, ver auditoria §11.

**Auth e Multi-tenancy**:
- Autenticacao: JWT nativo (30min access / 7d refresh) + WorkOS (SSO empresarial)
- 3 roles RBAC: `admin` (acesso total), `recruiter` (own company), `viewer` (somente leitura)
- **Regra critica**: toda query ao banco DEVE filtrar por `company_id`. Nunca retornar dados cross-tenant
- Arquivos: `app/auth/dependencies.py` (guards), `app/auth/models.py` (User model)

> Para detalhes completos de auth e seguranca, ver auditoria §17.

**EnhancedBaseAgent** (`robustness/enhanced_base.py`):
- Camada de robustez entre `BaseAgent` e agentes especificos
- `sanitize_text()`: remove XSS, SQL injection, caracteres perigosos
- `@handle_agent_errors`: decorator que captura erros e retorna mensagem amigavel
- `CancellationHandler`: detecta se processamento foi cancelado
- `detect_language()`: identifica idioma (pt-BR default)
- Defensive prompts: `get_clarification_message()`, `get_out_of_scope_response()`
- Hierarquia: `BaseAgent` → `EnhancedBaseAgent` → `[AgentesEspecificos]`

**Token Tracking e AI Consumption**:
- Toda chamada LLM registra automaticamente em `AiConsumption` (tabela):
  - `company_id`, `user_id`, `agent_type`, `model`, `input_tokens`, `output_tokens`, `cost_cents`
- `AiCreditsBalance`: limites mensais por empresa (`monthly_limit`, `current_usage`, `overage_allowed`)
- API: `GET /api/v1/ai-consumption/summary` — resumo de consumo do periodo
- O dev NAO precisa registrar manualmente — o tracking e automatico via LLMFactory

**A/B Testing** (`shared/ab_testing.py` + `shared/learning/ab_testing_service.py`):
- Experimentacao de prompts, modelos e fluxos por tenant
- `shared/ab_testing.py`: modulo raiz com definicao de experimentos e variantes
- `shared/learning/ab_testing_service.py`: servico com logica de atribuicao, tracking de metricas e selecao de vencedor
- Permite testar diferentes versoes de prompts ou providers (ex: Claude vs Gemini) com split controlado por empresa

---

## 9. Catalogo de Servicos

### job_management (31 servicos)

| Servico | O que faz |
|---|---|
| wizard_orchestrator_service | Orquestra fluxo do wizard |
| wizard_data_priority_service | Prioridade de dados no wizard |
| wizard_analytics_service | Analytics do wizard |
| jd_generator_service | Geracao de JD com IA |
| jd_enrichment_service | Enriquecimento de JD |
| jd_import_service | Importacao de JD existente |
| jd_template_service | Templates de JD |
| jd_template_cache_service | Cache de templates |
| job_vacancy_service | CRUD de vagas |
| job_vacancy_route_service | Roteamento de vagas |
| job_context_service | Contexto da vaga para agentes |
| job_embedding_service | Embeddings de vagas (PGVector) |
| job_qualification_service | Qualificacao de vagas |
| job_template_service | Gestao de templates |
| job_clone_service | Clonagem de vagas |
| job_board_service | Publicacao em job boards |
| job_alert_service | Alertas de vagas |
| job_audit_service | Auditoria de vagas |
| job_status_webhook_service | Webhooks de status |
| job_analytics_prompt_service | Prompts analiticos |
| job_insights_service | Insights de vagas |
| job_report_service | Relatorios de vagas |
| job_pattern_service | Padroes de vagas |
| seniority_jd_analyzer | Analise de senioridade na JD |
| template_importer_service | Importacao de templates |
| template_learning_service | Learning de templates |
| template_seeder | Seed de templates iniciais |
| vacancy_search_service | Busca de vagas |
| outcome_tracker | Rastreamento de resultados |
| ats_job_history_service | Historico de vagas do ATS |
| recruitment_email_templates | Templates de email de recrutamento |

### recruiter_assistant (10 servicos)

| Servico | O que faz |
|---|---|
| kanban_assistant_service | Servico de assistencia Kanban |
| talent_assistant_service | Servico de assistencia Talent |
| jobs_management_assistant_service | Servico de assistencia Jobs Mgmt |
| pipeline_service | Servico do pipeline de candidatos |
| pipeline_stage_service | Servico de estagios do pipeline |
| conversation_manager | Gerenciador de conversacao |
| conversation_memory | Memoria de conversacao |
| memory_service | Servico de memoria |
| wizard_action_executor | Executor de acoes do wizard |
| wizard_analytics_service | Analytics do wizard |

### cv_screening (20 servicos)

| Servico | O que faz |
|---|---|
| wsi_service | Servico principal WSI |
| wsi_screening_pipeline | Pipeline de screening WSI |
| wsi_question_service | Gestao de perguntas WSI |
| wsi_question_generator | Geracao de perguntas por IA |
| wsi_question_adjuster | Ajuste de perguntas |
| wsi_deterministic_scorer | Scoring deterministico |
| wsi_voice_orchestrator | Orquestrador de voz WSI |
| cv_parser | Parser de CV (PDF/DOCX) |
| cv_scoring_service | Scoring de CV |
| screening_question_set_service | Set de perguntas de screening |
| evaluation_criteria_service | Criterios de avaliacao |
| eligibility_verification_service | Verificacao de eligibilidade |
| pre_qualification_service | Pre-qualificacao |
| rubric_evaluation_service | Avaliacao por rubrica |
| calibration_profiles | Perfis de calibracao |
| seniority_context_calibrator | Calibracao por senioridade |
| seniority_resolver | Resolucao de senioridade |
| seniority_utils | Utilidades de senioridade |
| score_normalization_service | Normalizacao de scores |
| personalized_feedback_service | Feedback personalizado |

### sourcing (12 servicos)

| Servico | O que faz |
|---|---|
| sourcing_pipeline | Pipeline de sourcing |
| candidate_search_route_service | Roteamento de busca |
| wrf_service | WRF (Weighted Ranking Function) |
| pre_wrf_filter | Filtro pre-WRF |
| es_analyzer | Analise Elasticsearch |
| pgv_analyzer | Analise PGVector |
| evaluation_criteria | Criterios de avaliacao |
| search_analytics | Analytics de busca |
| vacancy_search | Busca de vagas para sourcing |
| pearch_service | Integracao Pearch AI |
| apify_service | Integracao Apify |
| apify_mcp_client | Cliente MCP Apify |

### communication (26 servicos)

| Servico | O que faz |
|---|---|
| communication_service | Servico principal de comunicacao |
| communication_dispatcher | Dispatcher de mensagens |
| communication_history_service | Historico de comunicacoes |
| email_service | Servico de email |
| email_providers | Abstracoes de provedores |
| email_providers/base | Interface base de email |
| email_providers/resend_provider | Provider Resend |
| email_providers/mailgun_provider | Provider Mailgun |
| email_templates_data | Dados de templates de email |
| whatsapp_service | Servico WhatsApp |
| whatsapp_provider | Provider WhatsApp |
| whatsapp_factory | Factory de WhatsApp |
| whatsapp_twilio_service | WhatsApp via Twilio |
| whatsapp_meta_service | WhatsApp via Meta API |
| teams_service | Servico Microsoft Teams |
| teams_auth | Autenticacao Teams |
| teams_bot | Bot do Teams |
| teams_simple | Integracao Teams simplificada |
| teams_recording_service | Gravacao de reunioes |
| data_request_service | Requisicoes de dados (LGPD) |
| data_request_whatsapp_service | Requisicoes via WhatsApp |
| transition_dispatch_service | Dispatch em transicoes |
| webhook_service | Servico de webhooks |
| infer_behavior_service | Inferencia de comportamento |
| interpret_context_llm_service | Interpretacao por LLM |
| return_event_service | Eventos de retorno |

### interview_scheduling (4 servicos)

| Servico | O que faz |
|---|---|
| scheduling_service | Servico de agendamento |
| calendar_service | Integracao de calendario |
| deepgram_service | Transcricao Deepgram |
| interview_transcript_analysis_service | Analise de transcricoes |

### analytics (10 servicos)

| Servico | O que faz |
|---|---|
| report_service | Servico de relatorios |
| candidate_report_service | Relatorios de candidatos |
| job_report_service | Relatorios de vagas |
| job_insights_service | Insights de vagas |
| job_analytics_prompt_service | Prompts analiticos |
| predictive_analytics_service | Analytics preditivo |
| search_analytics_service | Analytics de busca |
| wizard_analytics_service | Analytics do wizard |
| agent_monitoring_service | Monitoramento de agentes |
| wsi_observability | Observabilidade WSI |

### ats_integration (9 servicos)

| Servico | O que faz |
|---|---|
| ats_sync_service | Sincronizacao com ATS |
| gupy_service | Servico Gupy |
| pandape_service | Servico Pandape |
| merge_ats_service | Servico Merge |
| ats_clients/base | Interface base de ATS |
| ats_clients/gupy | Cliente Gupy |
| ats_clients/pandape | Cliente Pandape |
| ats_clients/merge | Cliente Merge.dev |

### automation (18 servicos)

| Servico | O que faz |
|---|---|
| automation_service | Servico principal de automacao |
| automation_handlers | Handlers de automacao |
| automation_scheduler | Scheduler de automacoes |
| automation_trigger_service | Servico de triggers |
| autonomous_agent_service | Servico de agentes autonomos |
| stage_automation_engine | Engine de automacao de estagios |
| stage_transition_automation | Automacao de transicoes |
| pipeline_monitor | Monitor de pipeline |
| proactive_service | Servico proativo |
| proactive_alert_service | Alertas proativos |
| candidate_context_aggregator | Agregador de contexto |
| prediction_action_bridge | Ponte predicao-acao |
| event_action_connector | Conector evento-acao |
| pattern_applier | Aplicador de padroes |
| learning_automation | Aprendizado de automacoes |
| planned_task_service | Servico de tarefas planejadas |
| task_service | Servico de tarefas |
| webhook_adapters | Adaptadores de webhook |

**Total: 140 servicos catalogados** (incluindo sub-servicos e providers; o total de arquivos de servico no repositorio e ~330)

---

## 10. Padroes de Codigo

### 10.1 Padrao de System Prompt

Todo agente ReAct tem um system prompt com estas secoes obrigatorias:

```
=== IDENTIDADE ===         → Nome, personalidade, tom, idioma
=== FILOSOFIA CENTRAL ===  → Chat como interface principal
=== INSTRUCOES REACT ===   → Como raciocinar (Thought/Action/Observe)
=== ESTAGIOS ===           → Estagios do dominio com campos de cada um
=== COMPLIANCE E ETICA === → LGPD, FairnessGuard, regras de validacao
=== EXEMPLOS ===           → Few-shot: entrada do usuario → raciocinio → resposta
=== CONTRA-ARGUMENTACAO == → Quando e como discordar do recrutador com dados
=== CALIBRACAO ===         → Adaptar ao porte da empresa (startup/PME/corporacao)
=== CONFIRMACOES ===       → Palavras de confirmacao/negacao em PT-BR
=== REGRAS CRITICAS ===    → Lista de NUNCA/SEMPRE
```

**Exemplo real** (trecho do `wizard_system_prompt.py`):

```python
=== COMPLIANCE E ETICA ===
- SEMPRE use validate_job_requirements para validar requisitos e descricoes
- A plataforma segue LGPD: nunca solicite dados pessoais sensiveis
- Use FairnessGuard PROATIVAMENTE: valide cada campo textual antes de salvar
- Quando FairnessGuard bloquear, explique de forma educacional, sem julgamento

=== EXEMPLOS DE INTERACAO ===
Recrutador: "Preciso de um dev Python senior pra equipe de dados, remoto"
LIA (thought): "Extraio: titulo=Dev Python, senioridade=Senior, depto=Dados, modelo=Remoto"
LIA (respond): "Perfeito! Ja registrei: **Dev Python Senior** para **Dados**, **remoto**."

Recrutador: "Coloca salario de 3 mil"
LIA (thought): "R$ 3.000 para Senior e abaixo do mercado. Vou usar benchmarks."
LIA (call_tool): get_salary_benchmarks(job_title="Dev Python", seniority="Senior")
LIA (respond): "O benchmark e R$ 12.000-22.000 (Robert Half 2024). Quer ajustar?"

=== CONTRA-ARGUMENTACAO ===
- Salario abaixo: cite benchmark + fonte + impacto na atracao
- Requisitos irrealistas: cite padrao de mercado + sugira ajuste
- NUNCA concorde silenciosamente com requisitos que prejudicam a vaga
```

### 10.2 Padrao de Tool Registry

Cada agente ReAct tem um `*_tool_registry.py` com esta estrutura:

```python
from app.shared.agents.react_loop import ToolDefinition
from app.shared.compliance.fairness_guard import FairnessGuard

_fairness_guard = FairnessGuard()

async def _wrap_minha_tool(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper async que o ReActLoop chama."""
    try:
        resultado = await logica_de_negocio(kwargs)
        return {"status": "success", "data": resultado}
    except Exception as e:
        logger.error(f"[tool] erro: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

TOOL_DEFINITIONS: List[ToolDefinition] = [
    ToolDefinition(
        name="minha_tool",
        description="Faz X para o dominio Y. Use quando Z.",
        parameters={
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Descricao"},
            },
            "required": ["param1"],
        },
        function=_wrap_minha_tool,
    ),
]

STAGE_TOOLS: Dict[str, List[str]] = {
    "estagio_1": ["minha_tool", "outra_tool"],
    "estagio_2": ["tool_avancada"],
}

GUARDRAIL_TOOLS: List[str] = ["validate_fairness"]

def get_tools() -> List[ToolDefinition]:
    return list(TOOL_DEFINITIONS)

def get_stage_tools(stage: str) -> List[ToolDefinition]:
    names = STAGE_TOOLS.get(stage, [t.name for t in TOOL_DEFINITIONS])
    return [t for t in TOOL_DEFINITIONS if t.name in names]
```

**O que o LLM ve**: `name` + `description` + `parameters` (JSON Schema).
O LLM decide quando usar cada tool com base na `description`.

**O que o codigo executa**: `function` (funcao Python async).

### 10.3 Padrao de ReAct Agent

Todo agente ReAct segue o padrao de 4 arquivos:

```
dominio/agents/
├── {dominio}_react_agent.py      ← Classe do agente (herda BaseAgent)
├── {dominio}_system_prompt.py    ← Prompt com personalidade e regras
├── {dominio}_tool_registry.py    ← Tools disponiveis + STAGE_TOOLS
└── {dominio}_stage_context.py    ← Contexto dinamico por estagio
```

**Exemplo real** (trecho do `wizard_react_agent.py`):

```python
class WizardReActAgent(EnhancedAgentMixin, BaseAgent):
    def __init__(self) -> None:
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_wizard_tools()]
        self._setup_enhanced(domain="wizard")

    @property
    def domain_name(self) -> str:
        return "wizard"

    async def process(self, input: AgentInput) -> AgentOutput:
        config = ReActConfig(
            max_iterations=5,
            # Audit-final 2026-05-10: signature atual usa kwargs:
            #   build_system_prompt(stage_context=..., memory_summary=...)
            # Ver app/domains/job_management/agents/wizard_react_agent.py:93
            system_prompt=build_system_prompt(
                stage_context=ctx.get("stage_context", ""),
                memory_summary=ctx.get("memory", ""),
            ),
            available_tools=get_stage_tools(current_stage),
            domain="wizard",
            model_provider="claude",
            temperature=0.3,
            guardrails=["save_job_draft"],
        )
        loop = ReActLoop(config)
        result = await loop.run(messages, observer=observer)
        return AgentOutput(response=result.response, ...)
```

### 10.4 Padrao de ToolDefinition

```python
class ToolDefinition(BaseModel):
    name: str          # Identificador unico (ex: "get_salary_benchmarks")
    description: str   # O que a tool faz — o LLM le isso para decidir
    parameters: Dict   # JSON Schema dos parametros esperados
    function: Callable # Funcao async Python que executa a logica
```

**Fluxo**:
1. LLM recebe lista de tools no prompt (name + description + parameters)
2. LLM decide: `action="call_tool", tool_name="get_salary_benchmarks"`
3. ReActLoop localiza a ToolDefinition pelo `name`
4. ReActLoop chama `tool.function(**tool_args)`
5. Resultado volta ao LLM como "observation"
6. LLM decide se precisa chamar outra tool ou responder

### 10.5 Padrao de Servico FastAPI

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

class JobCreateRequest(BaseModel):
    title: str
    department: str

@router.post("/")
async def create_job(
    request: JobCreateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    service = JobService(db)
    return await service.create(request, current_user.company_id)
```

### 10.6 Anti-Patterns (O que NUNCA fazer)

| Anti-Pattern | Por que e ruim | Faca isso ao inves |
|---|---|---|
| Hardcodar dados por cliente no codigo | Quebra multi-tenant, impede escalar | Use `CompanyHiringPolicy` no banco de dados |
| Ignorar FairnessGuard em tools de texto | Permite vies discriminatorio | Chame `_fairness_guard.check()` + `check_semantic()` |
| Tools sem error handling (try/except) | Erros nao tratados crasham o ReActLoop | Envolva toda tool em try/except com logging |
| Mudar tools sem atualizar STAGE_TOOLS | Tool existe mas agente nao consegue usar | Sempre atualize STAGE_TOOLS junto |
| Logica de negocio no system prompt | Prompt e "soft" — LLM pode ignorar | Use tools com codigo Python para garantia "hard" |
| Criar tool sem description clara | LLM nao sabe quando/como usar a tool | Escreva: "Faz X. Use quando Y. Retorna Z." |
| Retornar erro tecnico ao usuario | Experiencia ruim, expoe internals | Retorne mensagem amigavel no catch |

### 10.7 Padrao de Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Job created: {job_id}")
logger.warning(f"SECURITY: Request without X-Company-ID from {ip}")
logger.error(f"Failed to process screening: {str(e)}")
```

**Regras**:
- Formato: Structured JSON automatico em producao (`JSONFormatter` em `shared/structured_logging.py`)
- `request_id`: Injetado automaticamente pelo `RequestIdMiddleware` (header `X-Request-ID`)
- Prefixo `SECURITY:` para eventos de seguranca (login falho, acesso negado, tentativa de injection)
- **NUNCA** logar dados pessoais (CPF, email, telefone) sem `PIIMasker`:

```python
from app.shared.pii_masking import PIIMasker

masker = PIIMasker()
safe_text = masker.mask(texto_com_pii)
logger.info(f"Processed: {safe_text}")
```

### 10.8 Prompt Registry e Defensive Prompts

Prompts podem ser definidos de duas formas:

| Metodo | Onde fica | Quando usar |
|---|---|---|
| YAML (registry) | `app/prompts/domains/*.yaml` | Prompts versionados e reutilizaveis |
| Inline (Python) | `*_system_prompt.py` | Prompts especificos de agentes ReAct |

**PromptRegistry** (`shared/prompts/prompt_registry.py`):
- Carrega prompts YAML por dominio com fallback inline
- Suporta variaveis de template (Jinja2-like)
- Versionamento via git (cada mudanca e rastreavel)

**Defensive Prompts** (`shared/robustness/defensive_prompts.py`):
- `get_clarification_message()`: Quando intent e ambiguo, pede esclarecimento
- `get_out_of_scope_response()`: Quando request esta fora do dominio do agente
- `get_defensive_prompt_section()`: Adiciona guardrails ao prompt do agente
- Anti-hallucination: "So afirme dados que voce pode verificar"
- Anti-bias: "Nunca use criterios discriminatorios"
- Scope containment: "Nao execute acoes fora do seu dominio"

### 10.9 Hierarquia de Error Handling

| Camada | Tratamento | Exemplo |
|---|---|---|
| **Agent** | `EnhancedBaseAgent` com try/catch, fallback, retry | Falha de LLM → resposta de fallback |
| **Domain** | Cada action retorna `ActionResult` com `success`/`error` | Erro em busca → mensagem educativa |
| **Orchestrator** | CascadedRouter fallback (cache → regex → LLM) | Falha LLM → regex matching |
| **API** | `HTTPException` com status codes apropriados | 401, 403, 404, 422, 500 |
| **Compliance** | `IncidentReport` com severidade e remediacao | Bias detectado → alerta |

**Regra**: Erros NUNCA devem vazar tracebacks ao usuario. Cada camada captura
e traduz o erro para a camada superior. O usuario sempre recebe mensagem amigavel.

---

## 11. Guia Pratico "Onde Mexer"

### Tabela de Cenarios

| # | Preciso de... | Mexo em... | Arquivo(s) |
|---|---|---|---|
| 1 | Nova legislacao/compliance | shared/compliance/ | `fairness_guard.py` (regras), `audit_service.py` (log) |
| 2 | Mudar triagem de candidatos | cv_screening/services/ | `wsi_service.py`, `evaluation_criteria_service.py` |
| 3 | Adicionar tool a um agente | domains/*/agents/ | `*_tool_registry.py` (funcao + registro + STAGE_TOOLS) |
| 4 | Mudar tom/formato de resposta | domains/*/agents/ | `*_system_prompt.py` |
| 5 | Criar novo agente/dominio | shared/agents/ | `agent_scaffold.py` → gera 4 arquivos |
| 6 | Mudar roteamento de intencoes | orchestrator/ | `fast_router.py` (regex), `intent_router.py` (LLM) |
| 7 | Ajustar memoria/personalizacao | shared/agents/ | `working_memory.py`, `long_term_memory.py` |
| 8 | Adicionar validacao de vies | shared/compliance/ | `fairness_guard.py` (novos padroes) |
| 9 | Mudar regra do pipeline | cv_screening/agents/ | `pipeline_tool_registry.py`, `pipeline_system_prompt.py` |
| 10 | Adicionar canal de comunicacao | shared/channels/adapters/ | Criar novo adapter + registrar no `channel_router.py` |
| 11 | Trocar provedor de LLM | shared/providers/ | `llm_factory.py` + criar novo `llm_*.py` |
| 12 | Adicionar benchmarks | domains/*/agents/ | `*_tool_registry.py` (dados + fontes na tool) |
| 13 | Config por empresa (multi-tenant) | Banco de dados | `CompanyHiringPolicy` (nunca hardcodar no codigo) |
| 14 | Mascarar dados pessoais (LGPD) | shared/ | `pii_masking.py` (novos padroes PII) |
| 15 | Mudar pesos/blocos do WSI | cv_screening/services/ | `wsi_service.py`, `wsi_deterministic_scorer.py` |
| 16 | Adicionar feature flag | shared/governance/ | `feature_flag_service.py` |

### Niveis de Garantia

| Nivel | Onde fica | Como funciona | Confiabilidade | Exemplo |
|---|---|---|---|---|
| **Soft** | System Prompt | Instrucao textual ao LLM | Baixa (LLM pode ignorar) | "Responda em portugues" |
| **Medio** | Stage Context | Contexto injetado por estagio | Media (orienta o LLM) | "Estagio atual: salary" |
| **Hard** | Tool Code (Python) | Codigo executado, nao depende do LLM | Alta (garantido) | `FairnessGuard.check()` |

**Regra**: Para qualquer regra critica de negocio, use nivel **Hard** (codigo na tool).
Prompts sao para orientar, nao para garantir.

### Cenario 1: Adicionar nova legislacao (ex: nova norma LGPD)

```
Passo 1: shared/compliance/fairness_guard.py
   → Adicionar novos padroes regex em BLOCKED_PATTERNS
   → Adicionar novas categorias se necessario

Passo 2: shared/compliance/fairness_guard.py (metodo check_semantic)
   → Atualizar instrucoes do LLM para incluir a nova norma

Passo 3: domains/*/agents/*_system_prompt.py
   → Adicionar referencia a nova norma na secao === COMPLIANCE E ETICA ===

Passo 4: Testar
   → Enviar texto que viola a nova norma
   → Verificar que FairnessGuard bloqueia (check + check_semantic)
   → Verificar que agente explica educacionalmente
```

### Cenario 2: Adicionar nova tool a um agente existente

```
Passo 1: domains/*/agents/*_tool_registry.py
   → Criar funcao async wrapper: async def _wrap_nova_tool(**kwargs)
   → Com try/except e logging

Passo 2: Mesmo arquivo
   → Adicionar ToolDefinition em TOOL_DEFINITIONS
   → Com name, description clara, parameters JSON Schema, function

Passo 3: Mesmo arquivo
   → Adicionar nome da tool nos estagios corretos em STAGE_TOOLS

Passo 4: domains/*/agents/*_system_prompt.py (opcional)
   → Adicionar instrucao de quando usar a nova tool

Passo 5: Testar
   → Enviar mensagem que deveria triggar a nova tool
   → Verificar no log que o agente chamou a tool corretamente
```

### Cenario 3: Criar novo dominio do zero

```
Passo 1: Usar AgentScaffold
   from app.shared.agents.agent_scaffold import AgentScaffold
   AgentScaffold.generate(domain="novo_dominio")
   → Cria 4 arquivos: *_react_agent.py, *_system_prompt.py,
     *_tool_registry.py, *_stage_context.py

Passo 2: Implementar tools
   → Criar funcoes wrapper no tool_registry
   → Definir TOOL_DEFINITIONS e STAGE_TOOLS

Passo 3: Escrever system prompt
   → Seguir padrao: IDENTIDADE, REGRAS, TOOLS, COMPLIANCE, EXEMPLOS

Passo 4: Registrar no ReactAgentRegistry
   → shared/agents/react_agent_registry.py

Passo 5: Adicionar roteamento
   → orchestrator/fast_router.py (padroes regex)
   → orchestrator/intent_router.py (exemplos LLM)

Passo 6: Testar end-to-end
   → Enviar mensagem que deveria rotear para o novo dominio
   → Verificar roteamento → agente → tools → resposta
```

### Anti-Patterns (NUNCA faca isso)

| Anti-Pattern | Consequencia | Alternativa |
|---|---|---|
| Hardcodar regras por empresa | Impossivel escalar para N clientes | Use `CompanyHiringPolicy` no banco |
| Colocar dados sensiveis em logs | Violacao LGPD | Use `PIIMasking` antes de logar |
| Criar tool sem `try/except` | Erro nao tratado crasha o ReActLoop | Sempre envolva em try/except |
| Mudar tool sem atualizar `STAGE_TOOLS` | Tool existe mas agente nao consegue usar | Atualize STAGE_TOOLS junto |
| Logica critica so no prompt | LLM pode ignorar a regra | Implemente em codigo (tool ou guard) |
| Chamar LLM sem circuit breaker | Falha do provider derruba o sistema | Use `CircuitBreaker` para chamadas externas |
| Ignorar FairnessGuard em texto do usuario | Vies discriminatorio passa sem deteccao | Sempre valide texto com `check()` |
| Retornar traceback ao usuario | UX ruim, expoe internals | Retorne mensagem amigavel no catch |

### Human-in-the-Loop — Tabela de Confirmacoes

Toda acao que causa efeito externo (envia, publica, rejeita, agenda) requer
confirmacao do recrutador via `requires_confirmation`. Acoes informativas sao automaticas.

| Acao | Confirmacao? | Motivo |
|---|---|---|
| Envio de email em massa | SIM | Comunicacao irreversivel |
| Rejeicao de candidato | SIM | Decisao final negativa |
| Publicacao de vaga | SIM | Exposicao publica |
| Movimentacao de pipeline | SIM | Mudanca de etapa |
| Agendamento de entrevista | SIM | Compromisso com candidato |
| Envio via WhatsApp | SIM | Comunicacao direta |
| Geracao de JD | NAO | Preview antes de publicar |
| Scoring WSI | NAO | Informativo, nao acao |
| Sugestoes de skills | NAO | Sugestao editavel |
| Busca de candidatos | NAO | Apenas listagem |

#### Mapa de Risco por Acao (Ciclo Fechado)

| Acao | Risco | Confirmacao | Dominio |
|---|---|---|---|
| analisar_perfil | Baixo | Nao | cv_screening |
| disparar_triagem | Baixo | Nao | cv_screening |
| mover_candidato | Medio | Sim | pipeline |
| aprovar_candidato | Medio | Sim | pipeline |
| agendar_entrevista | Medio | Sim | interview_scheduling |
| enviar_email | Alto | Sim | communication |
| reprovar_candidato | Alto | Sim | pipeline |

> Ref.: `PLANO_CICLO_FECHADO_LIA.md` Secao 3.1 para detalhes de cada nivel de risco.

**Ao criar uma nova tool**: se ela causa efeito externo, adicione-a como
`GUARDRAIL_TOOL` no tool registry e defina `requires_confirmation = true`
no `ActionExecutorService`.

### Limites Operacionais — Referencia Rapida

| Recurso | Limite | Onde fica |
|---|---|---|
| LLM timeout (Claude/OpenAI) | 120 segundos | `shared/providers/llm_*.py` |
| LLM timeout (Gemini) | Default do SDK | `shared/providers/llm_gemini.py` |
| Max tool calls por request | 3 | `MAX_TOOL_CALLS_PER_REQUEST` |
| Max iteracoes ReActLoop | 5 (default, configuravel) | `ReActConfig.max_iterations` |
| Rate limit por minuto | 200 requests/min por tenant | Rate limiter middleware |
| Rate limit por hora | 2.000 requests/hr por tenant | Rate limiter middleware |
| Cache hot (Tier 1) | TTL 5 minutos | `shared/resilience/cache_manager_service.py` |
| Cache warm (Tier 2) | TTL 1 hora | idem |
| Cache cold (Tier 3) | TTL 24 horas | idem |
| DB pool size | Configuravel via `DATABASE_POOL_SIZE` | `app/core/config.py` |
| DB pool recycle | 3600 segundos | Pool settings |
| Pearch searches/dia | 10 por tenant | `PolicyEngine` |
| Voice screenings/dia | 20 por tenant | `PolicyEngine` |
| Max tokens/request | 50.000 | `PolicyEngine` |
| Max concurrent requests | 5 por tenant | `PolicyEngine` |

**Ao criar uma nova tool**: se ela chama LLM ou API externa, verifique se
esta dentro dos limites. Use `CircuitBreaker` para chamadas externas.


## 12. Conceitos de IA — Documento Educacional e Conceitual

> Material didático completo sobre todos os conceitos de IA implementados na plataforma.
> Serve como guia de referência para entender a arquitetura, decisões de design e trade-offs.
> Originado do documento CONCEITOS_IA_WEDOTALENT.md, integrado ao mapa técnico.

---

### 12.1 Introdução e Visão Geral

#### 12.1.1 O que é a LIA?

A **LIA** (Learning Intelligence Assistant) é a camada de inteligência artificial da plataforma WedoTalent. Ela não é um chatbot — é um **sistema de agentes especializados** que auxilia recrutadores em todo o ciclo de contratação: desde a criação de vagas até a contratação final.

**Analogia:** Pense na LIA como uma equipe de especialistas invisíveis. Quando o recrutador pede algo, a LIA decide qual especialista é mais adequado, encaminha a tarefa, e o especialista usa suas ferramentas para entregar o resultado. Tudo isso acontece em segundos, de forma transparente.

#### 12.1.2 Números da Plataforma

```
┌──────────────────────────────────────────────────────────────┐
│                  LIA EM NÚMEROS                              │
│                                                              │
│   11 Domínios de conhecimento                                │
│    7 Agentes ReAct (arquitetura moderna)                     │
│   18 Agentes Legacy (em migração)                            │
│    1 Agente LangGraph (orquestração de workflow)             │
│   89 Ferramentas ReAct (tools autônomas)                     │
│  109 Ferramentas Legacy                                      │
│  140+ Serviços de negócio                                    │
│    3 Provedores LLM (Claude, Gemini, OpenAI)                 │
│    3 Camadas de cache                                        │
│    3 Camadas de proteção contra viés (FairnessGuard)         │
│    4 Frameworks psicométricos integrados (WSI)               │
│    7 Frameworks de compliance monitorados                    │
│   86 Modelos de dados (entidades no banco)                   │
│  768 Dimensões vetoriais (embeddings semânticos)             │
└──────────────────────────────────────────────────────────────┘
```

#### 12.1.3 Arquitetura em Camadas — Visão de 10.000 Pés

A LIA é organizada em camadas que se comunicam de cima para baixo:

```
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 1: INTERFACE                                            │
│  Chat (recrutador) │ WhatsApp (candidato) │ Teams/Email (gestor)│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 2: ORQUESTRAÇÃO                                         │
│  CascadedRouter → StateManager → PolicyEngine → TaskPlanner     │
│  "Quem deve atender?" "Qual o contexto?" "É permitido?" "Como?"│
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
│  CAMADA 3A:     │ │  CAMADA 3B:   │ │  CAMADA 3C:      │
│  AGENTES REACT  │ │  AGENTE       │ │  AGENTES LEGACY  │
│  (7 agentes,    │ │  LANGGRAPH    │ │  (18 agentes,    │
│   89 tools)     │ │  (Job Wizard) │ │   109 tools)     │
│  Autônomos      │ │  Workflow     │ │  Em migração     │
└────────┬────────┘ └───────┬───────┘ └────────┬─────────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 4: SERVIÇOS ESPECIALIZADOS                              │
│  WSI Scoring │ Busca Semântica │ Análise Multimodal │ Analytics │
│  CV Parser   │ WRF Ranking     │ Voz (Deepgram)     │ Predição  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 5: INFRAESTRUTURA TRANSVERSAL                           │
│  Compliance    │ Cache        │ Memória       │ Observabilidade │
│  FairnessGuard │ 3 camadas    │ Working+LT    │ Audit Logs      │
│  FactChecker   │ Redis+PG     │ Embeddings    │ Telemetria      │
│  LGPD/EU AI   │ Semântico    │ Cross-session │ Health Checks   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 6: DADOS E INTEGRAÇÕES                                  │
│  PostgreSQL  │ pgvector    │ Redis      │ Elasticsearch         │
│  (ACID)      │ (768 dims)  │ (cache)    │ (full-text + BM25)    │
│  RabbitMQ    │ S3/Storage  │ ATS APIs   │ LLM APIs              │
│  (filas)     │ (arquivos)  │ (Gupy/etc) │ (Claude/Gemini/OpenAI)│
└─────────────────────────────────────────────────────────────────┘
```

#### 12.1.4 Os 11 Domínios de Conhecimento

Cada domínio é uma área de especialização da LIA. Pense neles como "departamentos" de uma empresa:

```
┌────────────────────────────────────────────────────────────────────┐
│                    11 DOMÍNIOS DA LIA                              │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 1. SOURCING │ │ 2. JOB      │ │ 3. CV       │ │ 4. COMMUNI- │ │
│  │             │ │ MANAGEMENT  │ │ SCREENING   │ │ CATION      │ │
│  │ Busca e     │ │ Criação e   │ │ Triagem     │ │ Email,      │ │
│  │ captação de │ │ gestão de   │ │ WSI, scoring│ │ WhatsApp,   │ │
│  │ candidatos  │ │ vagas       │ │ e avaliação │ │ Teams, SMS  │ │
│  │ 30 actions  │ │ 29 actions  │ │ 25 actions  │ │ 20 actions  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 5. INTER-   │ │ 6. ANALY-   │ │ 7. ATS      │ │ 8. AUTOMA-  │ │
│  │ VIEW &      │ │ TICS        │ │ INTEGRATION │ │ TION        │ │
│  │ SCHEDULING  │ │             │ │             │ │             │ │
│  │ Agendamento,│ │ KPIs,       │ │ Sync com    │ │ Regras,     │ │
│  │ voz, WSI    │ │ previsões,  │ │ Gupy,       │ │ alertas,    │ │
│  │ interview   │ │ dashboards  │ │ Pandapé,etc │ │ agentes     │ │
│  │ 20 actions  │ │ 18 actions  │ │ 18 actions  │ │ 20 actions  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │
│  │ 9. RECRUI-  │ │ 10.PIPELINE │ │ 11.HIRING   │                 │
│  │ TER ASSIST. │ │ TRANSITION  │ │ POLICY      │                 │
│  │             │ │             │ │             │                 │
│  │ Assistente  │ │ Movimentação│ │ Políticas   │                 │
│  │ pessoal do  │ │ de candidat.│ │ de contrata-│                 │
│  │ recrutador  │ │ no pipeline │ │ ção via IA  │                 │
│  │ 20 actions  │ │ 5 actions   │ │ ReAct agent │                 │
│  └─────────────┘ └─────────────┘ └─────────────┘                 │
└────────────────────────────────────────────────────────────────────┘
```

**Princípio de design:** Cada domínio é **autossuficiente** — possui seus próprios agentes, ações e ferramentas. O orquestrador apenas decide para qual domínio encaminhar a mensagem. Isso permite que novos domínios sejam adicionados sem alterar os existentes.

---

### 12.2 Fundamentos: Como os Agentes Pensam

#### 12.2.1 O Padrão ReAct — Thought → Action → Observation

O ReAct (Reasoning + Acting) é o padrão central de raciocínio dos agentes modernos da LIA. Ele resolve um problema fundamental da IA: **como um modelo de linguagem pode executar ações no mundo real de forma controlada?**

**A ideia central:** Em vez de pedir ao LLM uma resposta direta, o ReAct faz o LLM **pensar em voz alta**, decidir qual ferramenta usar, observar o resultado, e repetir até ter informação suficiente para responder.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REACT LOOP — CICLO DE RACIOCÍNIO                 │
│                    (máximo 5 iterações por segurança)                │
│                                                                     │
│                        Mensagem do Recrutador                       │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 1. REASON (Raciocinar)                                     │     │
│  │                                                            │     │
│  │  O LLM recebe:                                            │     │
│  │  • System prompt (personalidade + regras do domínio)       │     │
│  │  • Lista de tools disponíveis (nome + descrição + params)  │     │
│  │  • Contexto da conversa (histórico + estado)               │     │
│  │  • Observações anteriores (resultados de tools)            │     │
│  │  • Memórias de longo prazo (cross-session learnings)       │     │
│  │                                                            │     │
│  │  Produz JSON: { thought, action, tool_name, tool_args }   │     │
│  └──────────────────────────┬─────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 2. PARSE & DECIDE (Analisar e Decidir)                     │     │
│  │                                                            │     │
│  │  action == "respond"            → Gera resposta final ──────── FIM
│  │  action == "ask_clarification"  → Pede mais info ───────────── FIM
│  │  action == "call_tool"          → Continua para ACT ──┐  │     │
│  └───────────────────────────────────────────────────────│──┘     │
│                                                          │         │
│                                                          ▼         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 3. ACT (Executar)                                          │     │
│  │                                                            │     │
│  │  Verificações de segurança:                                │     │
│  │  ✓ Tool existe no registry?                                │     │
│  │  ✓ Já falhou com esses mesmos argumentos?                  │     │
│  │  ✓ É uma chamada duplicada? (≥2 repetições → break)       │     │
│  │  ✓ Tool está em guardrails? → Pede confirmação ao humano  │     │
│  │                                                            │     │
│  │  Se tudo OK: executa tool_function(**tool_args)            │     │
│  └──────────────────────────┬─────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 4. OBSERVE (Observar)                                      │     │
│  │                                                            │     │
│  │  Interpreta o resultado da ferramenta                      │     │
│  │  Adiciona observação ao estado do loop                     │     │
│  └──────────────────────────┬─────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 5. SHOULD RESPOND? (Já posso responder?)                   │     │
│  │                                                            │     │
│  │  Heurística: tool sucedeu? dados suficientes?              │     │
│  │  SIM → Gera resposta final ──────────────────────────────── FIM  │
│  │  NÃO → Volta para REASON (próxima iteração) ─────────── LOOP   │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                     │
│  PROTEÇÕES CONTRA LOOPS INFINITOS:                                  │
│  • Máximo 5 iterações → resposta de fallback                       │
│  • Detecção de chamadas duplicadas (≥2 repetições → para)          │
│  • Tracking de falhas (não repete tool com mesmos params)           │
│  • Guardrail tools → requerem confirmação do recrutador             │
│  • Error handling → resposta de fallback segura                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Exemplo concreto:** O recrutador pergunta "Qual o salário de mercado para Dev Python Sênior em SP?"

```
Iteração 1:
  THOUGHT: "Preciso buscar dados salariais reais para Python Sênior em SP"
  ACTION:  call_tool → get_salary_benchmarks(role="Python Developer", 
                         seniority="Senior", location="São Paulo")
  OBSERVE: "Resultado: R$ 12.000 — R$ 22.000 (mediana R$ 16.500)"

  SHOULD RESPOND? SIM — tenho dados suficientes.

  RESPONSE: "O salário de mercado para Dev Python Sênior em São Paulo
             está entre R$ 12.000 e R$ 22.000, com mediana de R$ 16.500
             (fonte: benchmarks internos + Robert Half/Gupy 2024)."
```

**Por que ReAct e não chamada direta?** Porque o agente escolhe sozinho quais ferramentas usar e em qual ordem. Ele pode precisar de 1, 2 ou 5 ferramentas dependendo da complexidade da pergunta. Essa flexibilidade é impossível com código hardcoded.

#### 12.2.2 Os Três Provedores LLM — Por Que Três?

A LIA não depende de um único modelo de linguagem. Ela usa três provedores, cada um escolhido para o que faz melhor:

```
┌──────────────────────────────────────────────────────────────┐
│               ESTRATÉGIA MULTI-LLM                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │ CLAUDE (Anthropic) — "O Pensador"                  │      │
│  │                                                    │      │
│  │ Modelo: claude-sonnet-4-20250514                   │      │
│  │ Temperatura: 0.3 (respostas mais consistentes)     │      │
│  │                                                    │      │
│  │ Usado para:                                        │      │
│  │ • Raciocínio complexo (ReAct loop, análise de CV)  │      │
│  │ • Geração de Job Descriptions                      │      │
│  │ • Classificação de intent (camada 3 do router)     │      │
│  │ • Análise de imagens (Claude Vision)               │      │
│  │ • Avaliação WSI (blocos comportamentais)            │      │
│  │                                                    │      │
│  │ Por quê: Melhor raciocínio estruturado e seguimento│      │
│  │ de instruções complexas. Output JSON mais confiável│      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │ GEMINI (Google) — "O Rápido"                       │      │
│  │                                                    │      │
│  │ Usado para:                                        │      │
│  │ • Expansão semântica de termos de busca             │      │
│  │   "Python" → [FastAPI, Django, Flask, PyTorch...]   │      │
│  │ • Análise de vídeo de entrevista                    │      │
│  │ • Tarefas de baixa latência (<300ms target)         │      │
│  │                                                    │      │
│  │ Por quê: Menor latência para expansão semântica.   │      │
│  │ Bom custo-benefício para tarefas rápidas.          │      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │ OPENAI — "O Versátil"                              │      │
│  │                                                    │      │
│  │ Usado para:                                        │      │
│  │ • Embeddings (text-embedding-004, 768 dimensões)   │      │
│  │ • Text-to-Speech (tts-1, tts-1-hd)                 │      │
│  │ • Speech-to-Text fallback (Whisper)                 │      │
│  │ • Tarefas auxiliares e fallback geral               │      │
│  │                                                    │      │
│  │ Por quê: Melhor ecossistema de embeddings e voz.   │      │
│  │ API madura e estável para produção.                │      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  PRINCÍPIO: "Best tool for the job"                          │
│  O LLMFactory seleciona o provedor ideal por tarefa.         │
│  Se um provedor falha, há fallback automático.               │
└──────────────────────────────────────────────────────────────┘
```

#### 12.2.3 Tools — As Mãos dos Agentes

Os LLMs pensam, mas não podem agir sozinhos. As **tools** (ferramentas) são funções que o agente pode chamar para buscar dados, executar ações ou interagir com sistemas externos.

```
┌──────────────────────────────────────────────────────────────────┐
│               TOOL DEFINITION — ANATOMIA DE UMA FERRAMENTA       │
│                                                                  │
│  Cada tool é definida por:                                       │
│                                                                  │
│  ToolDefinition {                                                │
│    name: "get_salary_benchmarks"                                 │
│    description: "Busca benchmarks salariais reais por cargo..."  │
│    parameters: JSON Schema (quais argumentos aceita)             │
│    function: referência para a função Python que executa         │
│  }                                                               │
│                                                                  │
│  O agente NÃO sabe o código da ferramenta.                       │
│  Ele só vê nome + descrição + parâmetros.                        │
│  É a DESCRIÇÃO que permite ao agente escolher a ferramenta certa.│
└──────────────────────────────────────────────────────────────────┘
```

**89 ferramentas ReAct** distribuídas em **7 registries** especializados:

```
┌──────────────────────────────────────────────────────────────────┐
│          7 REGISTRIES DE FERRAMENTAS REACT                       │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Wizard Registry  │  │ Kanban Registry  │                     │
│  │ (9 tools)        │  │ (14 tools)       │                     │
│  │                  │  │                  │                     │
│  │ validate_job_req │  │ get_benchmarks   │                     │
│  │ get_salary_bench │  │ pipeline_summary │                     │
│  │ validate_fields  │  │ identify_bottle. │                     │
│  │ get_suggestions  │  │ suggest_movements│                     │
│  │ save_job_draft   │  │ batch_move       │                     │
│  │ generate_jd      │  │ check_fairness   │                     │
│  │ ...              │  │ ...              │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Talent Registry  │  │ Jobs Mgmt Reg.   │                     │
│  │ (12 tools)       │  │ (13 tools)       │                     │
│  │                  │  │                  │                     │
│  │ search_candidates│  │ list_jobs        │                     │
│  │ compare_candidat.│  │ check_sla        │                     │
│  │ rank_candidates  │  │ analyze_bottlen. │                     │
│  │ check_fairness   │  │ pause/reopen/    │                     │
│  │ pool_health      │  │ close_job        │                     │
│  │ ...              │  │ ...              │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Policy Registry  │  │ Sourcing Reg.    │  │ Screening Reg. │ │
│  │ (13 tools)       │  │ (14 tools)       │  │ (14 tools)     │ │
│  │                  │  │                  │  │                │ │
│  │ get/save_policy  │  │ set_criteria     │  │ parse_cv       │ │
│  │ validate_complia.│  │ execute_search   │  │ calculate_wsi  │ │
│  │ industry_bench.  │  │ validate_fair.   │  │ generate_ques. │ │
│  │ explain_impact   │  │ analyze_results  │  │ evaluate_resp. │ │
│  │ ...              │  │ ...              │  │ ...            │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  DIFERENÇA FUNDAMENTAL:                                          │
│  Legacy tools: código decide qual tool chamar (hardcoded)        │
│  ReAct tools:  IA decide qual tool chamar (por descrição)        │
│  → Desacoplamento total, flexibilidade máxima                    │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.2.4 Enhanced Base Agent — A Camada de Robustez

Todos os agentes herdam de uma base comum que fornece proteções automáticas. Pense nela como um "sistema imunológico" dos agentes:

```
┌──────────────────────────────────────────────────────────────────┐
│          ENHANCED BASE AGENT — 6 PROTEÇÕES AUTOMÁTICAS           │
│                                                                  │
│  BaseAgent → EnhancedBaseAgent → [Agente Específico]             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. ROTEAMENTO INTELIGENTE (can_handle)                     │  │
│  │    Cada agente define IntentSchemas que descrevem           │  │
│  │    quais intenções ele sabe atender, com entidades          │  │
│  │    obrigatórias e opcionais. O router consulta todos        │  │
│  │    os agentes e escolhe o com maior confiança.              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 2. ERROR HANDLING AUTOMÁTICO                               │  │
│  │    @handle_agent_errors transforma erros técnicos em       │  │
│  │    mensagens amigáveis para o recrutador.                  │  │
│  │    Exemplo: "ConnectionError" → "Não consegui acessar      │  │
│  │    o serviço agora. Tente novamente em instantes."          │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 3. VALIDAÇÃO E SANITIZAÇÃO DE INPUT                        │  │
│  │    sanitize_text() remove tentativas de XSS, SQL injection │  │
│  │    detect_language() identifica idioma (pt-BR padrão)      │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 4. DETECÇÃO DE CANCELAMENTO                                │  │
│  │    Se o contexto de processamento é cancelado (ex:         │  │
│  │    recrutador fecha a página), o agente para de forma      │  │
│  │    segura em vez de continuar gastando recursos.            │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 5. PROMPTS DEFENSIVOS                                      │  │
│  │    Mensagens pré-formatadas para intents ambíguos           │  │
│  │    ("Não entendi exatamente. Você quer X ou Y?")            │  │
│  │    e requests fora do escopo do domínio.                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 6. TELEMETRIA AUTOMÁTICA                                   │  │
│  │    Métricas coletadas por request:                          │  │
│  │    • total_requests, successful, failed                     │  │
│  │    • avg_response_time_ms                                   │  │
│  │    • cancellations                                          │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.2.5 ReAct vs Legacy — Duas Gerações de Agentes

A plataforma está em migração da arquitetura legacy para ReAct. Ambas coexistem, controladas por feature flag:

```
┌──────────────────────────────────────────────────────────────────┐
│          LEGACY vs REACT — COMPARAÇÃO                            │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐           │
│  │  LEGACY (18 agents) │      │  REACT (7 agents)   │           │
│  │                     │      │                     │           │
│  │  DomainPrompt       │      │  ReActLoop          │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  process_intent()   │      │  Thought→Action→Obs │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  Action mapeada     │      │  Tool escolhida     │           │
│  │  (código decide)    │      │  (IA decide)        │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  Tool executada     │      │  Tool executada     │           │
│  │                     │      │                     │           │
│  │  PRÓ: Previsível    │      │  PRÓ: Flexível      │           │
│  │  CON: Rígido        │      │  PRÓ: Autônomo      │           │
│  │  CON: Escalabilidade│      │  PRÓ: Explainability│           │
│  └─────────────────────┘      └─────────────────────┘           │
│                                                                  │
│  Feature Flag: USE_REACT_AGENTS                                  │
│  ├── true (default) → Orchestrator usa ReactAgentRegistry        │
│  └── false → Orchestrator usa DomainPrompt.process_intent()      │
│                                                                  │
│  Fallback automático:                                            │
│  Se ReAct falha com exceção → tenta agente legacy                │
│  Se domínio não tem ReAct → usa legacy automaticamente           │
└──────────────────────────────────────────────────────────────────┘
```

##### 12.2.5.1 Análise da Migração Legacy → ReAct — Status, Impacto e Direção

> **Contexto**: A plataforma WedoTalent nasceu com a arquitetura legacy (18 agentes) e está sendo
> progressivamente migrada para ReAct (7 agentes já migrados). A migração foi **iniciada mas ainda
> não concluída**. As duas gerações coexistem porque é mais seguro migrar domínio por domínio do que
> reescrever tudo de uma vez. Esta seção documenta o estado atual da migração, o impacto em consumo
> de tokens, a projeção de consolidação ao concluir a migração, e uma análise de alinhamento entre
> o WeDO REAL (Recruiter Agent V5) construído pelo time de desenvolvimento e a direção arquitetural
> da WedoTalent.

###### O que ainda é Legacy — Mapa Completo

Os 18 agentes legacy que ainda existem na plataforma, distribuídos em 7 áreas:

| # | Agente Legacy | Área (Domínio) | O que faz |
|---|---|---|---|
| 1 | JobDraftingAgent | Gestão de Vagas | Rascunho de descrição de vaga |
| 2 | JobIntakeAgent | Gestão de Vagas | Intake de requisitos de vaga |
| 3 | JobLifecycleAgent | Gestão de Vagas | Ciclo de vida da vaga |
| 4 | JobInsightsAgent | Gestão de Vagas | Insights sobre vagas |
| 5 | JobBenefitsCompAgent | Gestão de Vagas | Benefícios e compensação |
| 6 | JobRubricAgent | Gestão de Vagas | Rubricas de avaliação |
| 7 | RecruiterAssistantAgent | Assistente do Recrutador | Assistente geral (fallback) |
| 8 | ScreeningAgent | Triagem de CVs | Screening de candidatos |
| 9 | AvaliadorWSIAgent | Triagem de CVs | Avaliação WSI |
| 10 | TriagemCurricularAgent | Triagem de CVs | Triagem curricular |
| 11 | SourcingAgent | Sourcing | Sourcing (fallback) |
| 12 | CommunicationAgent | Comunicação | Comunicação multi-canal |
| 13 | SchedulingAgent | Entrevistas | Agendamento de entrevistas |
| 14 | EntrevistadorAgent | Entrevistas | Condução de entrevistas |
| 15 | AnalyticsAgent | Analytics | Relatórios e analytics |
| 16 | AnalistaFeedbackAgent | Analytics | Análise de feedback |
| 17 | IntegradorATSAgent | Integração ATS | Integração com ATS externos |
| 18 | TaskPlannerAgent | Automação | Planejamento de tarefas |

###### Status da Migração por Domínio

```
┌──────────────────────────────────────────────────────────────┐
│         MIGRAÇÃO POR DOMÍNIO — STATUS ATUAL                  │
│                                                              │
│  DOMÍNIO              │ ReAct        │ Legacy     │ Status   │
│  ─────────────────────┼──────────────┼────────────┼──────────│
│  Gestão de Vagas      │ WizardReAct  │ 6 agentes  │ PARCIAL  │
│                       │ (9 tools)    │            │          │
│  Assistente Recrutador│ KanbanReAct  │ 1 agente   │ PARCIAL  │
│                       │ TalentReAct  │ (fallback) │          │
│                       │ JobsMgmtReAct│            │          │
│  Triagem de CVs       │ PipelineReAct│ 3 agentes  │ PARCIAL  │
│                       │ (14 tools)   │            │          │
│  Sourcing             │ SourcingReAct│ 1 agente   │ PARCIAL  │
│                       │ (14 tools)   │ (fallback) │          │
│  Políticas Contratação│ PolicyReAct  │ NENHUM     │ ✅ 100%  │
│                       │ (13 tools)   │            │          │
│  Comunicação          │ —            │ 1 agente   │ ❌ 0%    │
│  Entrevistas          │ —            │ 2 agentes  │ ❌ 0%    │
│  Analytics            │ —            │ 2 agentes  │ ❌ 0%    │
│  Integração ATS       │ —            │ 1 agente   │ ❌ 0%    │
│  Automação            │ —            │ 1 agente   │ ❌ 0%    │
└──────────────────────────────────────────────────────────────┘
```

**Resumo**: Apenas 1 domínio (Políticas de Contratação) está 100% migrado. 4 domínios têm ReAct
mas mantêm legacy como fallback. 5 domínios ainda são 100% legacy.

###### Diferença de Consumo de Tokens — Legacy vs ReAct

O ReAct tende a consumir mais tokens por interação individual, mas resolve problemas mais
complexos em menos interações. O impacto real no custo depende do cenário:

```
LEGACY (1 chamada LLM por interação):
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │ ──→ │  1x LLM  │ ──→ │ Resposta │
│  do user │     │  call    │     │  final   │
└──────────┘     └──────────┘     └──────────┘
Tokens: ~1.000-3.000 por interação (1 chamada)

ReAct (até 5 chamadas LLM por interação):
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │ ──→ │ Thought  │ ──→ │  Action  │ ──→ │ Observe  │ ──╮
│  do user │     │ (LLM #1) │     │ (Tool)   │     │ (result) │   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘   │
                                                                   │
     ╭─────────────────────────────────────────────────────────────╯
     │  Loop repete até 5x (max_iterations = 5)
     ▼
┌──────────┐
│ Resposta │
│  final   │
└──────────┘
Tokens: ~3.000-15.000 por interação (1-5 chamadas)
```

| Aspecto | Legacy | ReAct |
|---------|--------|-------|
| Chamadas LLM por interação | 1 (fixa) | 1 a 5 (dinâmica) |
| Tokens por chamada | ~1.000-3.000 | ~1.000-3.000 cada |
| Total por interação | ~1.000-3.000 | ~3.000-15.000 |
| Custo estimado | ~$0.01 | ~$0.01-0.05 |
| **Mas...** | Pode precisar de 3-4 interações para resolver | Frequentemente resolve em 1 interação |

**O ponto-chave: custo por RESULTADO, não por chamada.**

- **Legacy**: O usuário pergunta algo complexo → agente dá resposta parcial → usuário precisa
  reformular → outra resposta parcial → 3-4 trocas para resolver. Total: 4 x $0.01 = **$0.04**
- **ReAct**: O usuário pergunta algo complexo → agente raciocina, usa 3 tools, dá resposta
  completa. Total: 1 x $0.04 = **$0.04**

O custo total tende a ser similar, mas a experiência do usuário é muito melhor com ReAct porque
resolve em uma interação só. A plataforma rastreia tudo isso na tabela `AiConsumption` — cada
chamada LLM registra `input_tokens`, `output_tokens`, `cost_cents`, `agent_type` e `model`, com
limite mensal de 100.000 tokens por empresa (configurável).

###### Projeção de Consolidação — De 26 Agentes (Hoje) para ~12 ReAct (Futuro)

A recomendação é migrar tudo para ReAct. Hoje a plataforma tem **26 agentes no total** (7 ReAct +
1 LangGraph + 18 Legacy). Após a migração completa, a projeção é de **~12 agentes ReAct** — uma
redução de ~14 agentes. A mágica é que **um agente ReAct substitui vários agentes legacy**, porque
ele é flexível o suficiente para cobrir múltiplas funções dentro do mesmo domínio:

```
EXEMPLO REAL — DOMÍNIO "GESTÃO DE VAGAS":

ANTES (Legacy):                    DEPOIS (ReAct):
├── JobDraftingAgent               ├── WizardReActAgent (9 tools)
├── JobIntakeAgent                 │   └── 1 agente faz TUDO que
├── JobLifecycleAgent              │       os 6 faziam, porque
├── JobInsightsAgent               │       escolhe a tool certa
├── JobBenefitsCompAgent           │       conforme o contexto
├── JobRubricAgent                 │
│                                  │
│   6 agentes                      │   1 agente
│   6 arquivos de lógica           │   4 arquivos (padrão fixo)
│   Código duplicado entre eles    │   Zero duplicação
```

| Domínio | Hoje (total de agentes) | Futuro (só ReAct) | Redução |
|---------|:---:|:---:|:---:|
| Gestão de Vagas | 7 (1 ReAct + 6 Legacy) | 1 (WizardReAct) ✅ já existe | -6 |
| Assistente Recrutador | 4 (3 ReAct + 1 Legacy) | 3 (Kanban + Talent + JobsMgmt) ✅ já existe | -1 |
| Triagem de CVs | 4 (1 ReAct + 3 Legacy) | 1 (PipelineReAct) ✅ já existe | -3 |
| Sourcing | 2 (1 ReAct + 1 Legacy) | 1 (SourcingReAct) ✅ já existe | -1 |
| Políticas | 1 (1 ReAct) | 1 (PolicyReAct) ✅ já existe | 0 |
| Gestão de Vagas (LangGraph) | 1 (JobWizardGraph) | absorvido pelo WizardReAct | -1 |
| Comunicação | 1 Legacy | 1 ReAct (futuro) | 0 |
| Entrevistas | 2 Legacy | 1 ReAct (futuro) | -1 |
| Analytics | 2 Legacy | 1 ReAct (futuro) | -1 |
| Integração ATS | 1 Legacy | 1 ReAct (futuro) | 0 |
| Automação | 1 Legacy | 1 ReAct (futuro) | 0 |
| **TOTAL** | **26 agentes** | **~12 ReAct** | **~14 a menos** |

*\*O domínio "Assistente do Recrutador" tinha 1 agente legacy genérico que fazia tudo de forma
limitada. A versão ReAct dividiu em 3 agentes especializados (Kanban, Talent, JobsMgmt) que fazem
tudo bem — mas mesmo assim o total líquido da plataforma diminui de 26 para ~12.*

**O que enxuga de verdade não é só o número de agentes — é a complexidade total:**

- **Menos código**: Cada agente ReAct segue o padrão de 4 arquivos. Hoje os 18 legacy têm
  estruturas diferentes entre si.
- **Zero duplicação**: Serviços compartilhados (FairnessGuard, busca, cache) são acessados via
  tools, não replicados em cada agente.
- **Um único motor**: Todos os agentes ReAct usam o mesmo `ReActLoop`. Manutenção centralizada —
  melhora um, melhora todos.
- **Menos rotas de decisão**: O Orchestrator precisa saber rotear para 26 agentes hoje. Com
  migração completa, seriam ~12, todos via `ReactAgentRegistry`.

> **Analogia**: Hoje é como ter 26 funcionários, cada um com um manual de instruções diferente.
> Depois da migração, seriam ~12 funcionários, todos treinados pelo mesmo método, com acesso às
> mesmas ferramentas, mas cada um especialista na sua área.

###### Análise de Alinhamento — WeDO REAL (Recruiter Agent V5) vs WedoTalent

> **Contexto**: O time de desenvolvimento construiu o WeDO REAL (Recruiter Agent V5)
> baseado na documentação arquitetural da WedoTalent. Esta análise avalia o grau de alinhamento
> entre o que foi construído no WeDO REAL e a direção arquitetural da WedoTalent.

**Diagnóstico: O WeDO REAL é 100% Legacy.**

O Recruiter Agent V5 foi construído inteiramente na arquitetura legacy — não possui nenhum
componente ReAct. O WeDO REAL reproduziu fielmente a geração antiga da WedoTalent:

```
WeDO REAL (Recruiter Agent V5)        WEDOTALENT
─────────────────────────────         ──────────────────────────
DomainPrompt (ABC)                    DomainPrompt (ABC) ← LEGACY
  → process_intent()                    → process_intent() ← LEGACY
  → execute_action()                    → execute_action() ← LEGACY
DomainRegistry                        DomainRegistry ← LEGACY
DomainWorkflow (LangGraph 3 nós)      DomainWorkflow ← LEGACY
  intent → execute → format             (mesma estrutura)
DomainOrchestrator                    Orchestrator ← tem AMBOS
RouterAgent (keywords+regex+LLM)      CascadedRouter ← SIMILAR
MultiAgentOrchestrator                NÃO EXISTE na WeDoTalent
6 agentes especializados              18 agentes legacy equivalentes

❌ NÃO TEM: ReActLoop                ✅ TEM: ReActLoop
❌ NÃO TEM: Thought→Action→Observe   ✅ TEM: ciclo completo
❌ NÃO TEM: ToolDefinition/Registry   ✅ TEM: 89 tools tipadas
❌ NÃO TEM: Feature Flag             ✅ TEM: USE_REACT_AGENTS
```

**O que ESTÁ alinhado** (o WeDO REAL reproduz bem o legado):

| Conceito | WeDO REAL | WedoTalent (Legacy) | Veredicto |
|----------|---------|---------------------|-----------|
| DomainPrompt ABC | Implementado | Idêntico | ✅ Alinhado |
| process_intent() → LLM classifica | Gemini | Claude/Gemini | ✅ Alinhado |
| execute_action() → ação mapeada | Implementado | Idêntico | ✅ Alinhado |
| DomainRegistry + decorator | @register_domain | Mesmo padrão | ✅ Alinhado |
| DomainWorkflow (3 nós LangGraph) | intent→execute→format | Mesmo fluxo | ✅ Alinhado |
| ConversationMemory | Implementado | Equivalente | ✅ Alinhado |
| FairnessGuard | Implementado | Mais completo na WT | ⚠️ Parcial |
| Fast Routing (regex/keywords) | RouterAgent 3 cascatas | CascadedRouter 3 tiers | ✅ Similar |
| Cache/StatsManager | Implementado | Mais sofisticado na WT | ⚠️ Parcial |

**O que NÃO está alinhado** (o WeDO REAL não tem):

| Conceito da WedoTalent | Status no WeDO REAL | Impacto |
|-------------------------|-------------------|---------|
| **ReActLoop** (motor central) | ❌ Ausente | ALTO — é o futuro da plataforma |
| **89 ReAct Tools tipadas** | ❌ Ausente | ALTO — escalabilidade |
| **4-file pattern** (agent/prompt/tools/context) | ❌ Ausente | ALTO — padrão de organização |
| **Feature Flag** USE_REACT_AGENTS | ❌ Ausente | MÉDIO — controle de migração |
| **Fallback automático** ReAct→Legacy | ❌ Ausente | MÉDIO — resiliência |
| **Multi-provider LLM** (Claude+Gemini+GPT) | ❌ Só Gemini | MÉDIO — diversificação |
| **WSI (4 frameworks psicométricos)** | ❌ Ausente | MÉDIO — diferencial do produto |
| **PolicyEngine** (políticas por empresa) | ❌ Ausente | MÉDIO — compliance |
| **Token Tracking/Billing** | ❌ Ausente | BAIXO — operacional |

**O que o WeDO REAL tem que a WedoTalent NÃO tem:**

| Conceito do WeDO REAL | Existe na WT? | Observação |
|---------------------|---------------|------------|
| **MultiAgentOrchestrator** (6 sub-agentes) | ❌ Não | Abordagem diferente — na WT cada domínio é 1 agente com N tools |
| **ExecutionPlan** (8 planos multi-etapa) | ❌ Não | Na WT o ReActLoop decide sozinho a sequência |
| **FactChecker** (verifica claims da IA) | ❌ Não | Conceito interessante ausente na WT |
| **Pipeline Global** (6 nós sem domínio) | ❌ Não | Na WT tudo passa por domínio |

```
┌──────────────────────────────────────────────────────────────┐
│                  DIAGNÓSTICO DE ALINHAMENTO                   │
│                                                              │
│  O WeDO REAL reproduziu fielmente a GERAÇÃO ANTIGA (legacy)  │
│  da WedoTalent. Porém, a WedoTalent já está migrando         │
│  para a GERAÇÃO NOVA (ReAct).                                │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │WeDO REAL│    │ WT hoje │    │ WT futuro│                  │
│  │ 100%    │    │ ~60%    │    │ 100%     │                  │
│  │ Legacy  │    │ ReAct   │    │ ReAct    │                  │
│  └─────────┘    └─────────┘    └─────────┘                  │
│       ↑              ↑              ↑                        │
│   WeDO REAL      WedoTalent     Para onde                    │
│    está AQUI      está AQUI      estamos indo                │
│                                                              │
│  RECOMENDAÇÃO: O WeDO REAL precisa incorporar o padrão       │
│  ReAct para estar alinhado com a direção da WedoTalent.      │
│  Caso contrário, estará construindo sobre uma base que       │
│  será descontinuada.                                         │
└──────────────────────────────────────────────────────────────┘
```

###### Plano de Alinhamento do WeDO REAL — Orientação Inicial

- **Fase 1 — Fundação (criar o motor ReAct)**: Implementar o `ReActLoop` (ciclo
  Thought→Action→Observation), a `ReActConfig` (max_iterations=5, temperature=0.3, guardrails,
  provider), o `BaseAgent` interface e o `ReactAgentRegistry` (singleton).
- **Fase 2 — Padrão de 4 arquivos**: Cada agente ReAct segue a estrutura
  `{nome}_react_agent.py` + `{nome}_system_prompt.py` + `{nome}_tool_registry.py` +
  `{nome}_stage_context.py`.
- **Fase 3 — Migrar Sourcing como piloto**: Converter os 6 sub-agentes (Search, Analytics,
  Detail, Comparison, Report, Action) em tools de um único `SourcingReActAgent`. O ReActLoop
  decide sozinho qual tool usar — eliminando RouterAgent, MultiAgentOrchestrator e ExecutionPlan.
- **Fase 4 — Feature Flag + Fallback**: Implementar `USE_REACT_AGENTS`, manter legacy funcionando
  em paralelo com fallback automático e logs de monitoramento.
- **Fase 5 — Multi-provider LLM**: Implementar `LLMFactory` que abstrai o provider (hoje só
  Gemini, futuro: Claude + GPT-4).

> **Prioridade sugerida**: (1) ReActLoop + ReActConfig → sem isso, nada mais funciona. (2) Migrar
> Sourcing como piloto → maior domínio, maior impacto. (3) Feature Flag → segurança na transição.
> (4) Multi-provider → pode vir depois.
>
> **O ponto mais importante**: No WeDO REAL hoje, o **código decide** o que fazer (if/else, handlers
> mapeados). No ReAct, a **IA decide** o que fazer (raciocina e escolhe tools). Essa é a mudança
> fundamental.

#### 12.2.6 Observabilidade — Rastreando Cada Decisão

Cada execução do loop ReAct é registrada com telemetria completa:

```
┌──────────────────────────────────────────────────────────────────┐
│          REACT OBSERVER — TELEMETRIA DE EXECUÇÃO                 │
│                                                                  │
│  Para cada request do recrutador, é criado um registro:          │
│                                                                  │
│  AgentExecutionLog {                                             │
│    session_id          → Sessão do recrutador                    │
│    domain              → Qual domínio atendeu                    │
│    agent_class         → Qual agente específico                  │
│    total_duration_ms   → Tempo total de processamento            │
│    total_iterations    → Quantas vezes o loop rodou              │
│    tools_called        → Lista de ferramentas usadas             │
│    tools_succeeded     → Quantas sucederam                       │
│    tools_failed        → Quantas falharam                        │
│    final_confidence    → Confiança na resposta (0.0-1.0)         │
│    model_provider      → Qual LLM foi usado                     │
│    reasoning_chain     → Cadeia completa de raciocínio           │
│    stage_before/after  → Se houve transição de estágio           │
│  }                                                               │
│                                                                  │
│  Cada ITERAÇÃO dentro do loop também é registrada:               │
│                                                                  │
│  IterationLog {                                                  │
│    iteration, timestamp, phase, duration_ms                      │
│    tool_name, tool_args, tool_success                             │
│    reasoning   → "O que o agente pensou"                         │
│    observation → "O que o agente viu como resultado"              │
│    decision    → "respond" | "continue" | "error"                │
│  }                                                               │
│                                                                  │
│  → Permite auditoria completa: por que o agente fez X?           │
│  → Reprodutibilidade: mesma entrada → mesma cadeia               │
│  → Debugging: onde exatamente o agente errou?                    │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.3 Orquestração: Quem Decide o Quê

#### 12.3.1 CascadedRouter — Roteamento em 3 Camadas

Quando o recrutador envia uma mensagem, a primeira decisão é: **qual domínio deve atender?** O CascadedRouter resolve isso com uma estratégia em cascata — começa rápido e barato, e só escala para IA quando necessário:

```
┌──────────────────────────────────────────────────────────────────┐
│          CASCADED ROUTER — 3 CAMADAS DE ROTEAMENTO               │
│                                                                  │
│  Mensagem: "Qual o salário de mercado para dev Python?"          │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  CAMADA 1: MEMORY CACHE                              │       │
│  │                                                      │       │
│  │  Verifica cache de sessão/memória.                    │       │
│  │  "Esse usuário já perguntou sobre salários nesta      │       │
│  │   sessão? Se sim, manda para job_management."         │       │
│  │                                                      │       │
│  │  Latência: < 1ms  │  Custo: $0  │  Acurácia: Alta    │       │
│  └──────────┬───────────────────────────────────────────┘       │
│             │ MISS (primeira vez)                                │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  CAMADA 2: FAST ROUTER (Regex/Keywords)              │       │
│  │                                                      │       │
│  │  Cada domínio contribui um _KEYWORD_ACTION_MAP:      │       │
│  │  "salário"  → job_management    (conf: 0.72)         │       │
│  │  "cv"       → cv_screening      (conf: 0.64)         │       │
│  │  "agendar"  → interview_sched.  (conf: 0.74)         │       │
│  │                                                      │       │
│  │  Confiança = min(0.95, 0.6 + len(keyword) × 0.02)   │       │
│  │                                                      │       │
│  │  Latência: < 5ms  │  Custo: $0  │  Acurácia: Média   │       │
│  └──────────┬───────────────────────────────────────────┘       │
│             │ confidence < threshold                             │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  CAMADA 3: INTENT ROUTER (LLM)                       │       │
│  │                                                      │       │
│  │  Claude classifica intent + domínio em formato JSON:  │       │
│  │  { domain: "job_management", confidence: 0.92 }      │       │
│  │                                                      │       │
│  │  Usado apenas quando regex não tem confiança.         │       │
│  │  Representa ~15-20% dos requests.                     │       │
│  │                                                      │       │
│  │  Latência: 500-2000ms  │  Custo: ~$0.01              │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  RESULTADO: RouteResult { domain_id, confidence }                │
│                                                                  │
│  NOTA: O "intent" no orquestrador É o domain_id.                │
│  A classificação granular (qual ação dentro do domínio)          │
│  é feita pelo próprio domínio em process_intent().               │
└──────────────────────────────────────────────────────────────────┘
```

**Por que 3 camadas?**
- **Economia:** ~80% dos requests são resolvidos nas camadas 1+2 (custo $0)
- **Velocidade:** Latência média cai de ~1.5s (se fosse tudo LLM) para ~10ms
- **Resiliência:** Se o LLM estiver indisponível, as camadas 1+2 continuam funcionando

#### 12.3.2 Orquestrador Central — O Hub de Coordenação

O Orchestrator é o componente central que coordena todos os outros. Ele é o "controlador de tráfego aéreo" da LIA:

```
┌──────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR — FLUXO COMPLETO                  │
│                                                                  │
│  Mensagem do Recrutador                                          │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │ 1. Cascaded  │  "Para qual domínio vai?"                      │
│  │    Router    │  → domain_id + confidence                      │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 2. State     │  "Qual o contexto atual?"                      │
│  │    Manager   │  → histórico, vaga ativa, candidato ativo,     │
│  │              │    etapa do wizard                              │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 3. Policy    │  "O recrutador PODE fazer isso?"               │
│  │    Engine    │  → RBAC, rate limits, regras de negócio        │
│  │              │  → max 10 buscas Pearch/dia                    │
│  │              │  → max 50.000 tokens/request                   │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 4. Task      │  "É uma tarefa simples ou complexa?"           │
│  │    Planner   │  Simples → direto para o domínio               │
│  │              │  Complexa → decompõe em sub-tarefas:           │
│  │              │  "Busque Python SR e compare com pipeline"     │
│  │              │  → Task 0: sourcing.search(Python, Senior)     │
│  │              │  → Task 1: assistant.compare(task_0.results)   │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 5. Plan      │  Executa as tarefas:                           │
│  │    Executor  │  • Resultado da task N → contexto da task N+1  │
│  │              │  • Execução paralela quando possível            │
│  │              │  • Retry com backoff exponencial em falha       │
│  └──────────────┘                                                │
│                                                                  │
│  RESULTADO: Resposta formatada para o recrutador                 │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.3.3 ConversationGraph — Conversas como Grafo de Estados

Para fluxos que precisam de uma sequência definida de passos (como criação de vaga), a LIA usa um **grafo de conversação** baseado em LangGraph:

```
┌──────────────────────────────────────────────────────────────────┐
│          CONVERSATION GRAPH — FLUXO DE ESTADOS                   │
│                                                                  │
│  Conceito: A conversa é modelada como um grafo onde cada         │
│  NÓ é um estado e cada ARESTA é uma transição possível.          │
│                                                                  │
│  GraphSession {                                                  │
│    session_id    → Identifica a sessão                           │
│    graph_type    → Tipo do grafo ("job_wizard", "screening"...)  │
│    current_node  → Estado atual no grafo                         │
│    state_data    → Dados acumulados (JSON)                       │
│  }                                                               │
│                                                                  │
│  Exemplo: Job Wizard Graph                                       │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │  INPUT   │────▸│ JD           │────▸│ SALARY       │         │
│  │ EVALUAT. │     │ ENRICHMENT   │     │ BENCHMARK    │         │
│  │          │     │              │     │              │         │
│  │ Coleta   │     │ Gera JD com  │     │ Busca faixa  │         │
│  │ requisit.│     │ IA + enrique.│     │ salarial     │         │
│  └──────────┘     └──────────────┘     └──────┬───────┘         │
│                                               │                  │
│                                               ▼                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │ REVIEW   │◂────│ WSI          │◂────│ COMPETEN-    │         │
│  │ PUBLISH  │     │ QUESTIONS    │     │ CIES         │         │
│  │          │     │              │     │              │         │
│  │ Revisão  │     │ Gera perguntas│     │ Mapeia       │         │
│  │ final +  │     │ de triagem   │     │ competências │         │
│  │ publicar │     │ baseadas na JD│     │ e skills     │         │
│  └──────────┘     └──────────────┘     └──────────────┘         │
│                                                                  │
│  Cada nó pode:                                                   │
│  • Avançar para o próximo (dados suficientes)                    │
│  • Voltar para o anterior (recrutador quer editar)               │
│  • Permanecer (pedindo mais informações)                         │
│  • A cada nó, um agente ReAct específico é ativado               │
│                                                                  │
│  O estado persiste: se o recrutador sai e volta no dia           │
│  seguinte, a vaga continua exatamente onde parou.                │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.3.4 Anti-Sycophancy — A IA que Discorda

Um dos guardrails mais importantes é o sistema **anti-sycophancy** (anti-bajulação). A LIA não concorda cegamente com o recrutador:

```
┌─────────────────────────────────────────────────────────────────┐
│      ANTI-SYCOPHANCY — CONTRA-ARGUMENTAÇÃO BASEADA EM DADOS     │
│                                                                 │
│  CENÁRIO                          │ COMPORTAMENTO DA LIA        │
│  ─────────────────────────────────┼────────────────────────────  │
│  Salário muito abaixo do mercado  │ Apresenta benchmark +       │
│                                   │ contra-argumenta com dados  │
│                                   │                             │
│  "10 anos de experiência para     │ Aponta incompatibilidade +  │
│   cargo junior"                   │ sugere ajuste               │
│                                   │                             │
│  Skills conflitantes              │ "Java + .NET no mesmo       │
│  (Java + .NET juntos)             │ projeto é incomum" +        │
│                                   │ sugere stack coerente       │
│                                   │                             │
│  Rejeição sem critério objetivo   │ Mostra score do candidato + │
│                                   │ pede critérios técnicos     │
│                                   │                             │
│  Mover candidatos sem avaliação   │ Recomenda triagem WSI antes │
│                                   │                             │
│  ─────────────────────────────────┼────────────────────────────  │
│  REGRA: "NUNCA concorde silenciosamente com requisitos que      │
│  prejudicam a vaga / comprometam a qualidade do processo."      │
│                                                                 │
│  Se recrutador insiste após ver os dados:                       │
│  → Executa, mas documenta: "Configurado conforme solicitado.    │
│  Registro que o benchmark sugere [X]."                          │
│                                                                 │
│  Calibração por porte da empresa:                               │
│  STARTUP (<50 func.):   Requisitos flexíveis, equity OK         │
│  PME (50-500):          Equilíbrio requisitos/realidade          │
│  CORPORAÇÃO (>500):     Requisitos detalhados, compliance       │
└─────────────────────────────────────────────────────────────────┘
```

---

### 12.4 Busca Inteligente: Encontrando o Candidato Certo

#### 12.4.1 O Pipeline de Busca — 6 Etapas

Buscar candidatos na WedoTalent não é uma query SQL simples. É um pipeline de 6 etapas que combina busca textual, busca vetorial, filtragem e ranking:

```
┌──────────────────────────────────────────────────────────────────┐
│          TALENT FUNNEL SEARCH PIPELINE — 6 ETAPAS                │
│                                                                  │
│  Recrutador digita: "Python sênior em São Paulo"                 │
│       │                                                          │
│       ▼                                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 1: Expansão Semântica (Gemini)          │              │
│  │                                               │              │
│  │ "Python" → [FastAPI, Django, Flask, PyTorch,  │              │
│  │             Pandas, NumPy, Celery, SQLAlchemy] │              │
│  │                                               │              │
│  │ Amplia a busca para incluir tecnologias       │              │
│  │ relacionadas que o recrutador não digitou      │              │
│  │ Target: P95 < 300ms │ Cache: 5-10 min (Redis) │              │
│  └───────────────────┬───────────────────────────┘              │
│                      │                                           │
│         ┌────────────┴────────────┐                              │
│         │                         │                              │
│         ▼                         ▼                              │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │ ETAPA 2A:    │          │ ETAPA 2B:    │                     │
│  │ Elasticsearch│          │ PG Vector    │                     │
│  │              │          │              │                     │
│  │ Full-text    │          │ Cosine       │                     │
│  │ search +     │          │ similarity   │                     │
│  │ BM25 scoring │          │ on embeddings│                     │
│  │              │          │ (768 dims)   │                     │
│  │ Encontra por │          │ Encontra por │                     │
│  │ palavras     │          │ significado  │                     │
│  │ exatas       │          │ semântico    │                     │
│  └──────┬───────┘          └──────┬───────┘                     │
│         │                         │                              │
│         └────────────┬────────────┘                              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 3: Pre-WRF Filter                       │              │
│  │                                               │              │
│  │ Filtragem determinística rápida:               │              │
│  │ • Senioridade compatível                       │              │
│  │ • Localização no raio de busca                 │              │
│  │ • Anos de experiência mínima                   │              │
│  │                                               │              │
│  │ Remove candidatos claramente inadequados       │              │
│  │ ANTES do ranking caro                          │              │
│  └───────────────────┬───────────────────────────┘              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 4: WRF (Weighted Ranking Framework)      │              │
│  │                                               │              │
│  │ Score = w1 × skills_match                      │              │
│  │       + w2 × experience_match                  │              │
│  │       + w3 × semantic_similarity               │              │
│  │       + w4 × location_match                    │              │
│  │       + w5 × seniority_match                   │              │
│  │                                               │              │
│  │ Pesos (w1-w5) são determinísticos e            │              │
│  │ ajustáveis por tipo de vaga                    │              │
│  └───────────────────┬───────────────────────────┘              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 5: PGV Gap Analyzer                      │              │
│  │                                               │              │
│  │ Analisa gaps semânticos: quais skills o        │              │
│  │ candidato NÃO tem comparado com o requerido?   │              │
│  │                                               │              │
│  │ Candidato tem Python + Django, mas não FastAPI  │              │
│  │ → Gap de FastAPI informado no resultado        │              │
│  └───────────────────┬───────────────────────────┘              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 6: ES Score Drop Analyzer                │              │
│  │                                               │              │
│  │ Detecta quedas abruptas de score entre         │              │
│  │ candidatos consecutivos. Determina o           │              │
│  │ "corte natural" de relevância.                 │              │
│  │                                               │              │
│  │ Candidatos 1-15: score 85-92 (cluster A)       │              │
│  │ Candidatos 16-18: score 71-73 (QUEDA)          │              │
│  │ → Sugere corte nos 15 primeiros                │              │
│  └───────────────────────────────────────────────┘              │
│                                                                  │
│  Resultado: Lista rankeada + gaps + corte sugerido               │
│  + feedback loop para otimização estatística                     │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.4.2 Por Que Duas Engines de Busca?

```
┌──────────────────────────────────────────────────────────────────┐
│  ELASTICSEARCH vs PG VECTOR — COMPLEMENTARES, NÃO CONCORRENTES  │
│                                                                  │
│  Elasticsearch (BM25):                                           │
│  ✓ "Python Developer" encontra "Desenvolvedora Python"          │
│  ✓ Busca por termos exatos, booleanos, proximidade              │
│  ✗ Não entende que "Machine Learning" ≈ "Deep Learning"         │
│                                                                  │
│  PG Vector (Cosine Similarity):                                  │
│  ✓ "Machine Learning" encontra "Deep Learning Engineer"         │
│  ✓ Entende significado semântico das palavras                    │
│  ✗ Pode retornar resultados semanticamente similares             │
│    mas não exatamente relevantes                                 │
│                                                                  │
│  JUNTOS: Cobertura máxima                                        │
│  • Elasticsearch garante que termos exatos são encontrados       │
│  • PG Vector garante que termos semanticamente próximos          │
│    também são encontrados                                        │
│  • WRF combina os scores de ambos em ranking unificado           │
│                                                                  │
│  Embeddings: text-embedding-004 (768 dimensões)                  │
│  Indexação: IVFFlat (>10k registros) ou HNSW                     │
│  Operador: <=> (cosine distance) │ Threshold: 0.7 (busca)       │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.5 Triagem WSI: A Metodologia Proprietária de Avaliação

#### 12.5.1 O que é o WSI?

O **WSI (WeDoTalent Skill Index)** é a metodologia proprietária de avaliação de candidatos. Ele combina múltiplos frameworks psicométricos estabelecidos em um score composto de **7 blocos**, produzindo uma avaliação holística e não apenas técnica.

#### 12.5.2 Os 7 Blocos do WSI

```
┌──────────────────────────────────────────────────────────────────┐
│                   WSI SCORE (0-100)                               │
│          WeDoTalent Skill Index — 7 Blocos                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ BLOCO 1: Competências Técnicas                    ████████│  │
│  │   Hard skills, certificações, domínio do stack            │  │
│  │   Avaliado por: extração de CV + perguntas técnicas       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 2: Competências Comportamentais             ███████ │  │
│  │   Soft skills + mapeamento Big Five (OCEAN)               │  │
│  │   Avaliado por: perguntas comportamentais CBI             │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 3: Experiência Profissional                 ████████│  │
│  │   Histórico, senioridade, progressão de carreira          │  │
│  │   Avaliado por: parsing de CV + Modelo Dreyfus            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 4: Fit Cultural                             ██████  │  │
│  │   Alinhamento com valores e cultura da empresa            │  │
│  │   Avaliado por: perguntas contextuais + CompanyCulture    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 5: Potencial de Crescimento                 █████████│  │
│  │   Learning agility, adaptabilidade, curiosidade           │  │
│  │   Avaliado por: Taxonomia de Bloom + perguntas situac.    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 6: Formação Acadêmica                       ████    │  │
│  │   Educação formal, cursos, certificações, idiomas         │  │
│  │   Avaliado por: extração de CV                            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 7: Alinhamento com a Vaga                   ████████│  │
│  │   Match específico: requisitos da JD vs perfil            │  │
│  │   Avaliado por: comparação estruturada JD ↔ CV           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SCORE GLOBAL = Média ponderada dos 7 blocos                     │
│  (pesos configuráveis por empresa via CompanyHiringPolicy)       │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.5.3 Os 4 Frameworks Psicométricos Integrados

O WSI não inventa frameworks próprios. Ele integra 4 frameworks acadêmicos reconhecidos:

```
┌──────────────────────────────────────────────────────────────────┐
│          4 FRAMEWORKS PSICOMÉTRICOS DO WSI                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 1. TAXONOMIA DE BLOOM                                │        │
│  │    "Quão PROFUNDO é o conhecimento?"                  │        │
│  │                                                      │        │
│  │    Nível 6: Criar      ████████████████████ (Expert) │        │
│  │    Nível 5: Avaliar    ██████████████████            │        │
│  │    Nível 4: Analisar   ████████████████              │        │
│  │    Nível 3: Aplicar    ██████████████                │        │
│  │    Nível 2: Entender   ████████████                  │        │
│  │    Nível 1: Lembrar    ████████        (Iniciante)   │        │
│  │                                                      │        │
│  │    Uso: Classifica profundidade cognitiva das         │        │
│  │    respostas do candidato na triagem                   │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 2. MODELO DE DREYFUS                                 │        │
│  │    "Qual o NÍVEL DE PROFICIÊNCIA prática?"            │        │
│  │                                                      │        │
│  │    Novice → Adv. Beginner → Competent → Proficient   │        │
│  │                                          → Expert     │        │
│  │                                                      │        │
│  │    Uso: Classifica nível de expertise do candidato    │        │
│  │    baseado em experiência demonstrada                 │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 3. BIG FIVE (OCEAN)                                  │        │
│  │    "Qual o PERFIL COMPORTAMENTAL?"                    │        │
│  │                                                      │        │
│  │    O = Openness (Abertura)                            │        │
│  │    C = Conscientiousness (Conscienciosidade)          │        │
│  │    E = Extraversion (Extroversão)                     │        │
│  │    A = Agreeableness (Amabilidade)                    │        │
│  │    N = Neuroticism (Neuroticismo)                     │        │
│  │                                                      │        │
│  │    Uso: Mapeia traços de personalidade do candidato   │        │
│  │    para avaliar fit cultural e comportamental         │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 4. CBI (Competency-Based Interview)                  │        │
│  │    "As respostas têm EVIDÊNCIAS CONCRETAS?"           │        │
│  │                                                      │        │
│  │    Framework STAR:                                     │        │
│  │    S = Situation (contexto)                            │        │
│  │    T = Task (tarefa específica)                        │        │
│  │    A = Action (ação tomada)                            │        │
│  │    R = Result (resultado obtido)                       │        │
│  │                                                      │        │
│  │    Uso: Valida se o candidato apresenta evidências    │        │
│  │    comportamentais concretas, não apenas opiniões      │        │
│  └─────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.5.4 Pipeline Completo de Triagem

```
┌──────────────────────────────────────────────────────────────────┐
│          PIPELINE DE TRIAGEM WSI — 7 ETAPAS                      │
│                                                                  │
│  ┌──────────┐                                                    │
│  │ 1. PARSE │  CV (PDF/Docx) → Extração estruturada             │
│  │    CV     │  Nome, email, skills, experiência, formação       │
│  │          │  + Layout score (Claude Vision: 1-10)              │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 2. SCORE │  Avaliação automática contra requisitos da vaga    │
│  │    AUTO   │  "Candidato tem 70% das skills obrigatórias"      │
│  │          │  Scoring quantitativo (determinístico + LLM)       │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 3. GERAR │  3 camadas de perguntas:                           │
│  │ PERGUNTAS│  1. Derived: geradas pelo LLM a partir da JD      │
│  │    WSI   │  2. Company Bank: banco de perguntas da empresa    │
│  │          │  3. Custom: criadas pelo recrutador                │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 4. ENTRE-│  Candidato responde as perguntas                   │
│  │ VISTA WSI│  Opções: texto, áudio (Deepgram transcreve),       │
│  │          │  ou vídeo (Gemini analisa body language)            │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 5. CALCU-│  Avaliação das respostas usando 4 frameworks:      │
│  │ LAR WSI  │  Bloom + Dreyfus + Big Five + CBI                  │
│  │          │  → Score final por bloco (0-100)                   │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 6. RANK  │  Normalização de scores entre candidatos           │
│  │          │  Score Normalization Service unifica escalas        │
│  │          │  (WSI, entrevista, CV, testes) → comparação justa  │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 7. CORTE │  Seleção do top 25% (corte dinâmico)              │
│  │ DINÂMICO │  Baseado em distribuição estatística real           │
│  │          │  + ES Score Drop (queda abrupta de relevância)     │
│  └──────────┘                                                    │
│                                                                  │
│  SAÍDA: Parecer completo com WSI Scorecard + Evidências          │
│  + Pontos fortes/atenção + Recomendação + Senioridade calibrada  │
│  + Compliance (FairnessGuard ✓ │ FactChecker ✓ │ LGPD ✓)       │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.5.5 Análise Multimodal — Além do Texto

A triagem WSI não se limita a texto. A LIA pode analisar múltiplos formatos:

```
┌──────────────────────────────────────────────────────────────────┐
│          ANÁLISE MULTIMODAL — 3 PROVEDORES                       │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ CLAUDE VISION (Anthropic)                       │             │
│  │ • CV visual → layout score (1-10), organização  │             │
│  │ • Foto profissional → professionalism score     │             │
│  │ • Documento → extração estruturada              │             │
│  │ Formatos: jpg, png, gif, webp                   │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ GEMINI (Google)                                 │             │
│  │ • Vídeo de entrevista → body language,          │             │
│  │   eye contact, confiança (score 1-10)           │             │
│  │ • Apresentação técnica → effectiveness score    │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ VOZ (Deepgram Nova-2 + OpenAI Whisper fallback) │             │
│  │ • Transcrição de áudio (pt-BR)                  │             │
│  │ • WSI Voice Orchestrator: candidato responde     │             │
│  │   perguntas WSI por áudio → transcrição → score │             │
│  │ • TTS: LIA fala as perguntas (OpenAI TTS)       │             │
│  │ Formatos: mp3, wav, webm, m4a, ogg, flac        │             │
│  └────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.6 Memória e Aprendizado: Uma IA que Lembra e Evolui

#### 12.6.1 Arquitetura de Memória em 3 Níveis

A LIA possui um sistema de memória sofisticado que opera em três horizontes temporais:

```
┌──────────────────────────────────────────────────────────────────┐
│          SISTEMA DE MEMÓRIA — 3 HORIZONTES                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 1: Working Memory (Memória de Trabalho)              │  │
│  │ Horizonte: Sessão atual (minutos/horas)                    │  │
│  │                                                            │  │
│  │ O que armazena:                                            │  │
│  │ • Histórico de mensagens da conversa atual                 │  │
│  │ • Contexto acumulado (vaga ativa, candidato ativo)         │  │
│  │ • Estado do wizard (etapa atual, dados preenchidos)        │  │
│  │                                                            │  │
│  │ Como funciona:                                             │  │
│  │ Cada mensagem é adicionada ao estado do StateManager.      │  │
│  │ O agente sempre vê as últimas N mensagens como contexto.   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 2: Conversation Memory (Memória Conversacional)      │  │
│  │ Horizonte: Cross-sessão (dias/semanas)                     │  │
│  │                                                            │  │
│  │ O que armazena:                                            │  │
│  │ • Embeddings das conversas anteriores (Vector 768)         │  │
│  │ • Busca por similaridade semântica                         │  │
│  │                                                            │  │
│  │ Tabela: conversation_memories                              │  │
│  │ • embedding: Vector(768)                                   │  │
│  │ • content: texto da conversa                               │  │
│  │ • session_id: de qual sessão veio                          │  │
│  │                                                            │  │
│  │ Exemplo: "Na semana passada discutimos que a vaga de       │  │
│  │ Python Senior precisa de experiência com FastAPI."          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 3: Long-Term Memory (Memória de Longo Prazo)         │  │
│  │ Horizonte: Permanente (meses/anos)                         │  │
│  │                                                            │  │
│  │ O que armazena:                                            │  │
│  │ • Padrões aprendidos ("pattern")                           │  │
│  │ • Preferências da empresa ("preference")                   │  │
│  │ • Aprendizados ("learning")                                │  │
│  │ • Resultados de contratações ("outcome")                   │  │
│  │                                                            │  │
│  │ Tabela: agent_long_term_memory                             │  │
│  │ • company_id: escopo por empresa (multi-tenant)            │  │
│  │ • domain: qual agente criou                                │  │
│  │ • memory_key: ex: "salary_range_dev_senior"                │  │
│  │ • memory_value: JSON com dados                             │  │
│  │ • usage_count: popularidade (quantas vezes usada)          │  │
│  │ • relevance_score: 0.0-1.0 (com decay temporal)           │  │
│  │                                                            │  │
│  │ Ranking: score = relevance × (usage_count + 1)             │  │
│  │ → Memórias mais usadas e mais relevantes aparecem primeiro │  │
│  │ → Relevância decai com o tempo (decay_factor = 0.95)       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INTEGRAÇÃO: MemoryIntegration combina os 3 níveis              │
│  get_enriched_context() → "=== Session Memory ===" +            │
│                            "=== Cross-Session Learnings ==="     │
│  → Injetado no prompt do agente como extra_context              │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.6.2 Cache Inteligente de 3 Camadas

Para evitar chamadas repetidas (e caras) ao LLM, a LIA usa cache em 3 camadas:

```
┌──────────────────────────────────────────────────────────────────┐
│          CACHE MANAGER — 3 CAMADAS                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 1: Session Cache (In-Memory)      HOT              │  │
│  │ TTL: 1 hora │ Max: 1.000 entries │ Latência: <1ms         │  │
│  │ Escopo: Por conversa/sessão                                │  │
│  │ Uso: Respostas recentes, estado de workflow                │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ miss                               │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 2: Redis Cache                    WARM              │  │
│  │ TTL: 1-30 dias (por namespace) │ Latência: ~1-5ms          │  │
│  │ Escopo: Global (compartilhado entre sessões)               │  │
│  │                                                            │  │
│  │ Namespaces:                                                │  │
│  │ • SALARY_BENCHMARK:    7 dias   (dados salariais)          │  │
│  │ • SKILLS_SUGGESTIONS:  30 dias  (expansão semântica)       │  │
│  │ • LLM_RESPONSE:        7 dias   (respostas cacheadas)      │  │
│  │ • EMBEDDINGS:          30 dias  (vetores gerados)          │  │
│  │ • COMPANY_CONFIG:      7 dias   (config da empresa)        │  │
│  │ • LEARNING_PATTERNS:   30 dias  (padrões aprendidos)       │  │
│  │                                                            │  │
│  │ Features: similarity matching (threshold 0.75-0.90),       │  │
│  │ graceful degradation para in-memory se Redis cai,          │  │
│  │ multi-tenant via company_id scoping                        │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ miss                               │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 3: PostgreSQL Cache               COLD              │  │
│  │ TTL: 30+ dias │ Latência: ~5-20ms                          │  │
│  │ Tabela: intelligent_cache                                  │  │
│  │ Uso: Configurações de empresa, padrões aprendidos,         │  │
│  │      embeddings, dados estáveis                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  AI Cache Service (camada especializada para conteúdo IA):       │
│  • jd_generation:      24h, threshold 0.85                       │
│  • wsi_questions:      48h, threshold 0.90                       │
│  • skills_extraction:  72h, threshold 0.80                       │
│  • salary_analysis:    12h, threshold 0.75                       │
│  • competency_mapping: 48h, threshold 0.85                       │
│                                                                  │
│  → Cache semântico: não precisa ser a MESMA query,               │
│    basta ser SIMILAR o suficiente (cosine similarity)             │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.6.3 Learning Loop — Aprendizado Contínuo

A LIA aprende com os resultados das contratações para melhorar ao longo do tempo:

```
┌──────────────────────────────────────────────────────────────────┐
│          LEARNING LOOP — CICLO DE APRENDIZADO                    │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │ AÇÃO     │────▸│ RESULTADO    │────▸│ FEEDBACK     │         │
│  │          │     │              │     │              │         │
│  │ LIA faz  │     │ Candidato    │     │ Recrutador   │         │
│  │ triagem  │     │ contratado   │     │ avalia:      │         │
│  │ e dá     │     │ ou rejeitado │     │ útil/inútil  │         │
│  │ score 85 │     │              │     │ preciso/imp. │         │
│  └──────────┘     └──────────────┘     └──────┬───────┘         │
│                                               │                  │
│                                               ▼                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ APRENDIZADO                                                │  │
│  │                                                            │  │
│  │ 1. LearningPattern registra padrão:                        │  │
│  │    "Para vagas Python Senior em SP, candidatos com         │  │
│  │     FastAPI+Docker tiveram 80% de sucesso"                 │  │
│  │                                                            │  │
│  │ 2. InteractionFeedback grava avaliação:                    │  │
│  │    rating=4/5, "recomendação foi precisa"                  │  │
│  │                                                            │  │
│  │ 3. FeedbackEvent registra evento:                          │  │
│  │    "recrutador aceitou sugestão de skills"                 │  │
│  │                                                            │  │
│  │ 4. LongTermMemory persiste como "outcome":                 │  │
│  │    key="hiring_success_python_sr_sp",                      │  │
│  │    value={success_rate: 0.80, sample_size: 15}             │  │
│  └────────────────────────────────┬───────────────────────────┘  │
│                                   │                              │
│                                   ▼                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ APLICAÇÃO                                                  │  │
│  │                                                            │  │
│  │ Na próxima triagem similar, a memória é injetada:          │  │
│  │ "=== Cross-Session Learnings ===                           │  │
│  │  Known Patterns: Para Python Senior em SP, priorize        │  │
│  │  candidatos com FastAPI+Docker (80% success rate, n=15)"   │  │
│  │                                                            │  │
│  │ → O agente usa esse contexto para calibrar sua avaliação   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.7 Processamento Assíncrono: Trabalhando em Escala

#### 12.7.1 Por Que Processamento Assíncrono?

Algumas operações são pesadas demais para executar em tempo real. Quando o recrutador pede "triar 200 candidatos", a LIA não pode fazê-lo esperar 30 minutos. A solução: **processamento em background**.

```
┌──────────────────────────────────────────────────────────────────┐
│          PROCESSAMENTO ASSÍNCRONO — ARQUITETURA                  │
│                                                                  │
│  Recrutador: "Faça a triagem dos 200 candidatos da vaga X"       │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────┐                                        │
│  │ Resposta Imediata    │  "Iniciei a triagem de 200 candidatos. │
│  │ (< 2 segundos)       │   Vou notificá-lo quando terminar."   │
│  └──────────┬───────────┘                                        │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────┐               │
│  │ RabbitMQ (Fila de Mensagens)                  │               │
│  │                                              │               │
│  │ 4 filas especializadas:                       │               │
│  │ ├── cv_screening:  bulk_screen, batch_eval    │               │
│  │ ├── communication: mass_email, mass_whatsapp  │               │
│  │ ├── ats_sync:      bulk_sync, full_import     │               │
│  │ └── reports:       full_report, export_data   │               │
│  └──────────────┬───────────────────────────────┘               │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────────────┐               │
│  │ Celery Workers (Pool de Processamento)        │               │
│  │                                              │               │
│  │ Worker 1: bulk_screening_task                 │               │
│  │   → WSI pipeline para cada candidato          │               │
│  │   → Usa Claude para scoring                   │               │
│  │                                              │               │
│  │ Worker 2: mass_communication_task             │               │
│  │   → Envia emails/WhatsApp em lote             │               │
│  │   → Rate limiting por provider                │               │
│  │                                              │               │
│  │ Worker 3: ats_sync_task                       │               │
│  │   → Sincroniza com Gupy/Pandapé               │               │
│  │   → Idempotency e retry automático            │               │
│  │                                              │               │
│  │ Worker 4: scheduled_reports_task              │               │
│  │   → Daily briefings, weekly reports           │               │
│  └──────────────────────────────────────────────┘               │
│                                                                  │
│  Configuração de domínios elegíveis para async:                  │
│  max_concurrent_per_domain = 3                                   │
│  max_queue_size = 100                                            │
│                                                                  │
│  9 domínios × ações elegíveis:                                   │
│  sourcing: bulk_search, mass_outreach, import_candidates         │
│  cv_screening: bulk_screen, batch_evaluate, full_pipeline        │
│  communication: mass_email, mass_whatsapp, bulk_notification     │
│  analytics: generate_full_report, export_dataset, predictive     │
│  ...e mais 5 domínios                                            │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.7.2 EnhancedTaskManager — Resiliência de Tarefas

O sistema nativo de tarefas (não Celery) provê funcionalidades adicionais:

```
┌──────────────────────────────────────────────────────────────────┐
│          ENHANCED TASK MANAGER — RESILIÊNCIA                     │
│                                                                  │
│  TaskQueue        → Fila de tarefas com prioridade               │
│       │                                                          │
│       ▼                                                          │
│  TaskScheduler    → Agendamento (cron + interval)                │
│       │                                                          │
│       ▼                                                          │
│  TaskPersistence  → Salva estado no banco (sobrevive restart)    │
│       │                                                          │
│       ▼                                                          │
│  EnhancedTask     → Retry com backoff exponencial                │
│  Manager          → Dead Letter Queue (DLQ) para falhas          │
│                   → Monitoring com health checks                 │
│                   → MAX_TOOL_CALLS_PER_REQUEST: 3                │
│                                                                  │
│  Se uma task falha 3x:                                           │
│  → Move para DLQ (Dead Letter Queue)                             │
│  → Pode ser reprocessada manualmente                             │
│  → Alerta de monitoramento é gerado                              │
│                                                                  │
│  Proteção anti-loop: máximo 3 chamadas de tool por request       │
│  → Evita que um bug gere centenas de chamadas LLM               │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.7.3 Comunicação Multi-Canal

A LIA se comunica por 5 canais, todos gerenciados por uma abstração unificada:

```
┌──────────────────────────────────────────────────────────────────┐
│          MULTI-CHANNEL SERVICE — 5 CANAIS                        │
│                                                                  │
│  MultiChannelService                                             │
│       │                                                          │
│       ├── ChannelRouter (decide o melhor canal)                  │
│       │                                                          │
│       ├── EmailAdapter       → Mailgun / SMTP                  │
│       ├── WhatsAppAdapter    → Twilio / Meta API                │
│       ├── SMSAdapter         → Twilio                           │
│       ├── TeamsAdapter       → Microsoft Graph                  │
│       └── InAppAdapter       → Notificações internas            │
│                                                                  │
│  Cada adapter:                                                   │
│  • Template engine com variáveis dinâmicas                       │
│  • Rate limiting por provider                                    │
│  • Retry automático em falha                                     │
│  • Tracking de entrega e abertura                                │
│  • LGPD: registro de consentimento e opt-out                     │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.8 Compliance e Ética: IA Responsável por Design

#### 12.8.1 FairnessGuard — 3 Camadas Contra Viés

O **FairnessGuard** é o sistema de proteção contra viés discriminatório. Ele opera em 3 camadas progressivas, de rápida a profunda:

```
┌──────────────────────────────────────────────────────────────────┐
│          FAIRNESS GUARD — 3 CAMADAS ANTI-VIÉS                    │
│                                                                  │
│  Texto a verificar: "Preciso de um candidato jovem e dinâmico"   │
│       │                                                          │
│       ▼                                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 1: Regex/Keyword Matching                           │  │
│  │ Latência: < 1ms │ Custo: $0                                │  │
│  │                                                            │  │
│  │ Detecta termos explicitamente discriminatórios:             │  │
│  │ "jovem" → ALERTA (discriminação por idade)                 │  │
│  │ "bonita" → ALERTA (aparência física)                       │  │
│  │ "casado" → ALERTA (estado civil)                           │  │
│  │ "cristão" → ALERTA (religião)                              │  │
│  │                                                            │  │
│  │ Se detecta → Para imediatamente com alerta                 │  │
│  │ Se não detecta → Passa para Camada 2                       │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ passou                             │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 2: Detecção de Viés Implícito                       │  │
│  │ Latência: < 5ms │ Custo: $0                                │  │
│  │                                                            │  │
│  │ Detecta padrões que sugerem viés sem termos explícitos:     │  │
│  │ "boa aparência" → Viés de aparência                        │  │
│  │ "formação em universidade de ponta" → Viés socioeconômico  │  │
│  │ "sem filhos" → Discriminação familiar                      │  │
│  │                                                            │  │
│  │ Se detecta → Alerta com sugestão de reformulação           │  │
│  │ Se não detecta → Passa para Camada 3 (quando ativada)      │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ passou                             │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 3: Análise Semântica LLM (Deep Check)               │  │
│  │ Latência: 500-2000ms │ Custo: ~$0.01                       │  │
│  │                                                            │  │
│  │ LLM analisa o CONTEXTO COMPLETO para viés sutil:           │  │
│  │ "Buscamos alguém com energia para acompanhar nosso         │  │
│  │  ritmo acelerado" → Pode indicar discriminação por idade   │  │
│  │                                                            │  │
│  │ Usado em: validação de políticas de contratação,           │  │
│  │ análise profunda de JDs, revisão de critérios de rejeição  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INTEGRAÇÃO nos agentes ReAct:                                   │
│  • Wizard: validate_job_requirements usa FairnessGuard 3-tier    │
│  • Kanban: check_rejection_fairness ANTES de qualquer rejeição   │
│  • Talent: check_search_fairness valida critérios de busca       │
│  • JobsMgmt: validate_job_action_fairness em ações de gestão     │
│  • Policy: validate_policy_compliance com deep check semântico   │
│                                                                  │
│  REGRA no system prompt do Kanban:                               │
│  "SEMPRE use check_rejection_fairness ANTES de registrar         │
│   qualquer rejeição"                                             │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.8.2 FactChecker — Validação de Veracidade

O **FactChecker** é um middleware pós-processamento que valida se a resposta da IA contém afirmações factualmente corretas:

```
┌──────────────────────────────────────────────────────────────────┐
│          FACT CHECKER — 4 VALIDADORES                            │
│                                                                  │
│  Resposta do LLM                                                 │
│       │                                                          │
│       ▼                                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. _check_salary_claims()                                  │  │
│  │    Regex: R$\s*([\d.,]+)                                   │  │
│  │    Range válido: R$ 1.500 — R$ 200.000                     │  │
│  │    Se há dados reais → compara desvio %                    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 2. _check_candidate_counts()                               │  │
│  │    Regex: (\d+)\s*candidatos?                              │  │
│  │    Limite: max 50.000                                      │  │
│  │    Se há dado real → compara com context["total_candidat."]│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 3. _check_percentage_claims()                              │  │
│  │    Regex: (\d+(?:[.,]\d+)?)\s*%                            │  │
│  │    Range: 0% — 100%                                        │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 4. _check_date_claims()                                    │  │
│  │    Regex: (\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})        │  │
│  │    Validação de formato e razoabilidade                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│       │                                                          │
│       ▼                                                          │
│  FactCheckResult {                                               │
│    total_claims         → Quantas afirmações detectadas          │
│    verified_claims      → Quantas verificadas contra dados reais │
│    accurate_claims      → Quantas estão corretas                 │
│    inaccurate_claims    → Quantas estão ERRADAS                  │
│    overall_accuracy     → accurate / verified                    │
│  }                                                               │
│                                                                  │
│  Se inaccurate_claims > 0 → WARNING no log                      │
│  Metadata adicionada à resposta para transparência               │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.8.3 AuditService — Explicabilidade Completa

Toda decisão de IA é registrada para auditoria (LGPD Art. 20, EU AI Act Art. 14):

```
┌──────────────────────────────────────────────────────────────────┐
│          AUDIT SERVICE — RASTREABILIDADE COMPLETA                 │
│                                                                  │
│  Cada decisão registra:                                          │
│  • decision_type:     SCORE_CANDIDATE, REJECT, MOVE_STAGE...    │
│  • agent_id:          Qual agente decidiu                        │
│  • input_data:        Dados de entrada (contexto)                │
│  • output_data:       Resultado da decisão                       │
│  • criteria_evaluated: Critérios avaliados (prova de não-bias)   │
│  • criteria_ignored:  Critérios deliberadamente ignorados        │
│  • justification:     Justificativa textual                      │
│  • llm_model:         Modelo LLM usado                           │
│  • prompt_hash:       Hash do prompt (reprodutibilidade)         │
│                                                                  │
│  Retenção por tipo (LGPD):                                       │
│  • Decisões de scoring:   730 dias (2 anos)                      │
│  • Rejeições:             1.095 dias (3 anos)                    │
│  • Contratações:          1.825 dias (5 anos)                    │
│                                                                  │
│  → Permite responder: "Por que a IA rejeitou o candidato X?"     │
│  → Com cadeia completa: raciocínio + dados + critérios           │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.8.4 Human-in-the-Loop — Quando a IA Pede Permissão

Nem tudo é automático. Ações com impacto externo requerem confirmação:

```
┌──────────────────────────────────────────────────────────────────┐
│          HUMAN-IN-THE-LOOP — O QUE PRECISA DE APROVAÇÃO          │
│                                                                  │
│  REQUER CONFIRMAÇÃO (efeito externo):                            │
│  ✓ Envio de email em massa        → Comunicação irreversível     │
│  ✓ Rejeição de candidato          → Decisão final negativa       │
│  ✓ Publicação de vaga             → Exposição pública            │
│  ✓ Movimentação no pipeline       → Mudança de etapa             │
│  ✓ Agendamento de entrevista      → Compromisso com candidato    │
│  ✓ Envio via WhatsApp             → Comunicação direta           │
│                                                                  │
│  AUTOMÁTICO (informativo, sem efeito externo):                   │
│  ✗ Geração de Job Description     → Preview antes de publicar    │
│  ✗ Scoring WSI                    → Informativo                  │
│  ✗ Sugestões de skills            → Sugestão editável            │
│  ✗ Busca de candidatos            → Apenas listagem              │
│                                                                  │
│  PRINCÍPIO: "Toda ação que causa efeito externo                  │
│  (envia, publica, rejeita, agenda) requer confirmação.           │
│  Ações informativas são automáticas."                            │
│                                                                  │
│  Implementação: guardrails no ReActConfig                        │
│  → Tool marcada como guardrail → agente pede confirmação         │
│  → Recrutador confirma → agente executa                          │
│  → Recrutador rejeita → agente para                              │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.8.5 LGPD — Proteção de Dados Pessoais

```
┌──────────────────────────────────────────────────────────────────┐
│          LGPD — IMPLEMENTAÇÃO TÉCNICA                            │
│                                                                  │
│  PII Masking (mascaramento de dados pessoais):                   │
│  • Dados sensíveis mascarados em logs e traces                   │
│  • Pretensão salarial NUNCA sincronizada com ATS                │
│                                                                  │
│  Consentimento (Art. 8):                                         │
│  • ConsentRecord: registro de consentimento com base legal       │
│  • ConsentVersion: versionamento de termos                       │
│  • ConsentEvent: grant / revoke / renew                          │
│                                                                  │
│  Direitos do Titular (Art. 18):                                  │
│  • DataSubjectRequest: requisições de acesso/exclusão/correção   │
│  • DataAccessLog: log de todo acesso a dados pessoais            │
│                                                                  │
│  Agentes ReAct (system prompts):                                 │
│  • Wizard: "Nunca solicite dados pessoais sensíveis              │
│    (raça, religião, orientação sexual, estado civil)"            │
│  • Kanban: "Proteja dados pessoais dos candidatos em             │
│    todas as comunicações"                                        │
│                                                                  │
│  7 frameworks de compliance monitorados:                         │
│  SOX, SOC2, ISO27001, LGPD, BCB498, EU AI Act, NYC LL144        │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.9 Automação e Predição: De Reativa a Proativa

#### 12.9.1 Stage Automation Engine — 16 Triggers

O motor de automação observa eventos no pipeline e dispara ações automaticamente (ou sugere ao recrutador):

```
┌──────────────────────────────────────────────────────────────────┐
│          STAGE AUTOMATION — 16 TRIGGERS                          │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ EVENTOS DE TRIGGER:                                        │   │
│  │                                                           │   │
│  │ Triagem:                        Pipeline:                  │   │
│  │ • SCREENING_COMPLETED           • STAGE_CHANGED            │   │
│  │ • CANDIDATE_APPLIED             • CANDIDATE_INACTIVE       │   │
│  │ • CANDIDATES_SOURCED            • NO_RESPONSE_48H          │   │
│  │                                                           │   │
│  │ Entrevista:                     Ofertas:                   │   │
│  │ • INTERVIEW_SCHEDULED           • OFFER_SENT               │   │
│  │ • INTERVIEW_COMPLETED           • CANDIDATE_HIRED          │   │
│  │ • CANDIDATE_NO_SHOW             • CANDIDATE_REJECTED       │   │
│  │                                                           │   │
│  │ Outros:                                                    │   │
│  │ • ATS_SYNC                      • FEEDBACK_RECEIVED        │   │
│  │ • JOB_PUBLISHED                 • DEADLINE_APPROACHING     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  FLUXO DE PROCESSAMENTO:                                         │
│                                                                  │
│  Evento → Validação Multi-Tenant → Avaliar Regras da Empresa     │
│                                         │                        │
│                          ┌──────────────┴──────────────┐        │
│                          ▼                             ▼        │
│                    auto_execute?                  Criar Sugestão │
│                    (nível autonomia)              para Aprovação  │
│                          │                             │        │
│                          ▼                             ▼        │
│                    Executar handler              Recrutador      │
│                    automaticamente               aprova/rejeita  │
│                          │                             │        │
│                          └──────────────┬──────────────┘        │
│                                         ▼                        │
│                                    Audit Log                     │
│                                                                  │
│  Condições avaliáveis por regra:                                 │
│  • min_wsi_score    → Score WSI mínimo                           │
│  • stages           → Etapa específica do pipeline               │
│  • min_confidence   → Confiança mínima da IA                     │
│  • source_types     → Tipo de fonte (interno, Pearch)            │
│  • min_cv_score     → Score mínimo de CV                         │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.9.2 Alertas Proativos — 5 Categorias

A LIA monitora continuamente e gera alertas inteligentes:

```
┌──────────────────────────────────────────────────────────────────┐
│          ALERTAS PROATIVOS — 5 CATEGORIAS                        │
│                                                                  │
│  ┌────────────────────────────────────┐                         │
│  │ 1. PIPELINE (saúde do funil)       │                         │
│  │ • Conversão < 5% → WARNING         │                         │
│  │ • 5+ candidatos parados 10+ dias   │                         │
│  │ • Oferta sem resposta há 72h       │ → URGENT                │
│  │ • Pipeline com < 3 candidatos      │ → URGENT                │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 2. PRODUTIVIDADE (recrutador)      │                         │
│  │ • 5+ tarefas atrasadas            │ → URGENT                │
│  │ • Sem atividade há 2h             │ → INFO                  │
│  │ • < 50% da meta às 16h            │ → WARNING               │
│  │ • Scorecards pendentes            │                         │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 3. COMUNICAÇÃO (saúde de comms)    │                         │
│  │ • Taxa de entrega de email baixa   │                         │
│  │ • Candidatos sem resposta          │                         │
│  │ • Taxa alta de opt-out             │                         │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 4. PREDITIVO (insights IA)         │                         │
│  │ • Dropout risk alto                │                         │
│  │ • Time-to-fill em risco de SLA     │                         │
│  │ • Candidato ideal detectado!       │                         │
│  │ • Padrão de rejeição detectado     │                         │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 5. SISTEMA (saúde técnica)         │                         │
│  │ • Falha na sincronização ATS       │                         │
│  │ • Agente IA com health baixo       │                         │
│  │ • Créditos de IA acabando          │                         │
│  │ • Erro em decisão de IA            │                         │
│  └────────────────────────────────────┘                         │
│                                                                  │
│  Cada alerta tem:                                                │
│  • threshold configurável                                        │
│  • severity: INFO | WARNING | URGENT                             │
│  • cooldown_hours: evita repetição excessiva                     │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.9.3 OutcomePredictor — Predições Acionáveis

O sistema preditivo calcula probabilidades para ajudar decisões:

```
┌──────────────────────────────────────────────────────────────────┐
│          OUTCOME PREDICTOR — 4 TIPOS DE PREDIÇÃO                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. predict_hiring_probability()                            │  │
│  │    "Qual a chance deste candidato ser contratado?"          │  │
│  │    Fatores: WSI score, fit cultural, senioridade match,     │  │
│  │    disponibilidade, pretensão salarial vs range             │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 2. predict_dropout_risk()                                  │  │
│  │    "Qual o risco de desistência?"                           │  │
│  │    Fatores e pesos:                                        │  │
│  │    • dropout_base:             0.15                         │  │
│  │    • time_in_pipeline:         0.25 (mais tempo → risco)   │  │
│  │    • communication_frequency:  0.20 (menos comms → risco)  │  │
│  │    • response_time:            0.10 (mais lento → risco)   │  │
│  │                                                            │  │
│  │    Classificação: LOW <30% │ MEDIUM 30-60% │               │  │
│  │                    HIGH 60-80% │ CRITICAL >80%              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 3. predict_time_to_fill()                                  │  │
│  │    "Quanto tempo até preencher esta vaga?"                  │  │
│  │    Baseado em histórico da empresa + benchmarks do setor    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 4. predict_offer_acceptance()                              │  │
│  │    "O candidato vai aceitar a oferta?"                      │  │
│  │    Baseado em pretensão salarial, fit, engajamento          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Onde são aplicados:                                             │
│  • Pipeline Kanban → Badges de risco por candidato               │
│  • Alertas Proativos → dropout_risk gera alertas automáticos     │
│  • Dashboard → Métricas preditivas no painel de analytics        │
│  • Decisões de IA → Agentes priorizam ações por probabilidade    │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.9.4 CompanyHiringPolicy — 5 Níveis de Autonomia

Cada empresa configura quanto de autonomia a LIA tem, desde "assistente passivo" até "piloto automático":

```
┌──────────────────────────────────────────────────────────────────┐
│       COMPANY HIRING POLICY — 5 NÍVEIS DE AUTONOMIA              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 1: ASSISTENTE (Padrão Inicial)                       │  │
│  │ • LIA só age quando perguntada                             │  │
│  │ • Toda decisão requer confirmação                          │  │
│  │ • Não monitora proativamente                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 2: RECOMENDADOR                                      │  │
│  │ • LIA sugere ações proativamente                           │  │
│  │ • Recrutador decide se executa                             │  │
│  │ • Alertas e notificações automáticas                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 3: SEMI-AUTÔNOMO                                     │  │
│  │ • Ações de baixo risco automáticas                         │  │
│  │ • Ações de médio/alto risco requerem aprovação             │  │
│  │ • Ex: triagem automática, mas rejeição requer confirmação  │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 4: AUTÔNOMO                                          │  │
│  │ • Maioria das ações automatizadas                          │  │
│  │ • Apenas decisões críticas requerem humano                 │  │
│  │ • Relatórios automáticos de tudo que foi feito             │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 5: PILOTO AUTOMÁTICO                                 │  │
│  │ • LIA gerencia o pipeline completo                         │  │
│  │ • Humano supervisiona e intervém quando quer               │  │
│  │ • Todas as ações documentadas e auditáveis                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Configuração: PolicyReActAgent (13 tools) guia o setup          │
│  → Onboarding de 19 perguntas adaptativas por setor              │
│  → Benchmarks por indústria (8 setores: tech, finance, retail,   │
│    healthcare, legal, education, manufacturing, services)        │
│  → Fontes: ABRH/GPTW (dados do mercado brasileiro)              │
│  → Calibrado por porte: Startup / PME / Corporação              │
└──────────────────────────────────────────────────────────────────┘
```

---

### 12.10 Por Que Escolhemos Esta Arquitetura

#### 12.10.1 Decisões de Design e Seus Trade-offs

```
┌──────────────────────────────────────────────────────────────────┐
│          DECISÕES ARQUITETURAIS — TRADE-OFFS                     │
│                                                                  │
│  DECISÃO 1: Domain-Driven em vez de Agent-First                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Domínios como fronteira, agentes subordinados  │  │
│  │ ALTERNATIVA: Agentes como entidade principal                │  │
│  │ POR QUÊ: Domínios são estáveis (sourcing sempre existe);  │  │
│  │ agentes mudam (legacy → ReAct → futuro). Domínios como     │  │
│  │ contratos de interface facilitam migração incremental.      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 2: Multi-LLM em vez de Single Provider                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Claude + Gemini + OpenAI, cada um para o       │  │
│  │ que faz melhor                                             │  │
│  │ ALTERNATIVA: Usar apenas um provedor para tudo              │  │
│  │ POR QUÊ: Reduz vendor lock-in, aproveita forças de cada   │  │
│  │ modelo, resilência se um ficar indisponível.                │  │
│  │ TRADE-OFF: Mais complexidade na abstração (LLMFactory)     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 3: CascadedRouter (3 camadas) em vez de LLM direto     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Cache → Regex → LLM (cascata progressiva)     │  │
│  │ ALTERNATIVA: Chamar LLM para toda classificação             │  │
│  │ POR QUÊ: ~80% dos requests resolvidos sem LLM ($0, <5ms). │  │
│  │ Economia massiva em tokens + latência.                      │  │
│  │ TRADE-OFF: Regex pode classificar errado; mitigado pela    │  │
│  │ camada 3 (LLM) como fallback.                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 4: ReAct Loop com max 5 iterações                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Limite rígido de 5 iterações + proteções       │  │
│  │ ALTERNATIVA: Loop livre até o agente decidir parar          │  │
│  │ POR QUÊ: LLMs podem entrar em loops, gerando custo         │  │
│  │ infinito. 5 iterações cobrem 99% dos casos de uso.         │  │
│  │ TRADE-OFF: Perguntas muito complexas podem ser truncadas;  │  │
│  │ mitigado por TaskPlanner (decompõe em sub-tarefas).        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 5: Duas engines de busca (Elasticsearch + pgvector)     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Full-text (BM25) + Vetorial (cosine) + WRF    │  │
│  │ ALTERNATIVA: Apenas Elasticsearch ou apenas vetorial        │  │
│  │ POR QUÊ: Texto garante match exato; vetorial garante       │  │
│  │ match semântico. Juntos, cobertura máxima.                  │  │
│  │ TRADE-OFF: Dois sistemas para manter e sincronizar;        │  │
│  │ mitigado pelo WRF que unifica os scores.                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 6: FairnessGuard em 3 camadas                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Regex → Implícito → LLM (cascata progressiva) │  │
│  │ ALTERNATIVA: Apenas LLM para todo viés                      │  │
│  │ POR QUÊ: Regex é determinístico (sem false negatives para  │  │
│  │ termos óbvios), rápido ($0), e pega a maioria dos casos.   │  │
│  │ LLM só é ativado para análise profunda.                     │  │
│  │ TRADE-OFF: Regex pode ter falsos positivos; mitigado        │  │
│  │ pela camada 2 que refina antes de escalar.                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 7: Coexistência Legacy + ReAct com feature flag        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Migração gradual com fallback automático       │  │
│  │ ALTERNATIVA: Big bang — migrar tudo de uma vez              │  │
│  │ POR QUÊ: Risco zero. Se ReAct falha, legacy assume.       │  │
│  │ Permite migrar domínio por domínio, validando cada um.     │  │
│  │ TRADE-OFF: Duas arquiteturas para manter durante           │  │
│  │ migração; custos de manutenção temporariamente maiores.     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.10.2 O Que É IA vs O Que É Determinístico

Uma decisão crucial é saber onde usar IA e onde usar código determinístico:

```
┌──────────────────────────────────────────────────────────────────┐
│          IA vs DETERMINÍSTICO — MAPA COMPLETO                    │
│                                                                  │
│  100% IA (LLM):                                                  │
│  ├─ Classificação de intent (o que o recrutador quer)            │
│  ├─ Geração de Job Description                                   │
│  ├─ Análise de CV e extração de dados                            │
│  ├─ WSI scoring qualitativo (blocos comportamentais)             │
│  ├─ Geração de perguntas de triagem                              │
│  ├─ Sugestões de competências e skills                           │
│  ├─ Análise de fit cultural                                       │
│  ├─ Geração de comunicações personalizadas                       │
│  ├─ Análise multimodal (vídeo, imagem, voz)                     │
│  └─ Predição de sub-status de pipeline                           │
│                                                                  │
│  HÍBRIDO (IA + Regras):                                          │
│  ├─ Roteamento: Cache → Regex → LLM (cascata)                  │
│  ├─ WSI quantitativo: LLM extrai → Algoritmo pontua             │
│  ├─ Busca: WRF (pesos determinísticos) + embeddings (IA)        │
│  ├─ Personalização: Estatísticas históricas + LLM ajusta        │
│  ├─ Automação: Triggers determinísticos + LLM prediz             │
│  └─ Cache semântico: Cosine similarity (math) + LLM (fallback)  │
│                                                                  │
│  100% DETERMINÍSTICO:                                            │
│  ├─ Autenticação e autorização (JWT + RBAC)                     │
│  ├─ FairnessGuard camada 1 (regex pattern matching)              │
│  ├─ FactChecker (validação numérica com ranges fixos)            │
│  ├─ Rate limiting e PolicyEngine (contadores + limites)          │
│  ├─ Retenção LGPD (dias fixos por tipo)                          │
│  ├─ Pipeline state machine (transições válidas hardcoded)        │
│  ├─ Multi-tenancy isolation (company_id filter)                  │
│  ├─ Token tracking e billing (contagem exata)                    │
│  └─ Feature flags (boolean per tenant)                           │
│                                                                  │
│  PRINCÍPIO: "IA onde precisa de inteligência;                    │
│  código onde precisa de garantia."                                │
│  Decisões de segurança e compliance são SEMPRE determinísticas.  │
└──────────────────────────────────────────────────────────────────┘
```

#### 12.10.3 Resumo: Os Princípios da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│         10 PRINCÍPIOS DA ARQUITETURA DE IA DA WEDOTALENT         │
│                                                                  │
│  1. DOMAIN-FIRST: Domínios definem fronteiras, agentes servem    │
│                                                                  │
│  2. BEST TOOL FOR THE JOB: Cada LLM usado para sua força        │
│                                                                  │
│  3. CASCATA ECONÔMICA: Sempre tente o mais barato primeiro       │
│     (cache → regex → LLM)                                       │
│                                                                  │
│  4. HUMAN-IN-THE-LOOP: IA sugere, humano decide em ações        │
│     com impacto externo                                          │
│                                                                  │
│  5. EXPLICABILIDADE: Toda decisão de IA é auditável              │
│     (raciocínio + dados + critérios registrados)                 │
│                                                                  │
│  6. FAIRNESS BY DESIGN: Anti-viés integrado em toda ação         │
│     (3 camadas + anti-sycophancy)                                │
│                                                                  │
│  7. MEMÓRIA EVOLUTIVA: IA aprende com resultados e               │
│     personaliza por empresa                                      │
│                                                                  │
│  8. MIGRAÇÃO SEGURA: Feature flags + fallback automático         │
│     (legacy → ReAct sem risco)                                   │
│                                                                  │
│  9. MULTI-TENANT ISOLATION: Dados e aprendizados isolados        │
│     por empresa (company_id em tudo)                             │
│                                                                  │
│  10. IA ONDE PRECISA, CÓDIGO ONDE GARANTE:                       │
│      Segurança e compliance são sempre determinísticos            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 13. Glossario

| Termo | Definicao |
|---|---|
| **ReAct** | Reason-Act-Observe-Decide. Padrao de agente autonomo que raciocina antes de agir. |
| **ReActLoop** | Implementacao do ciclo ReAct em `shared/agents/react_loop.py`. Core dos agentes autonomos. |
| **ReActConfig** | Configuracao do ReActLoop: max_iterations, tools, provider, guardrails, temperature. |
| **ToolDefinition** | Schema de uma tool: name, description, parameters (JSON Schema), function (Python async). |
| **WorkingMemory** | Memoria de sessao — dados acumulados durante uma conversa. Resetada entre sessoes. |
| **LongTermMemory** | Memoria cross-session — padroes, preferencias e aprendizados persistidos no banco. |
| **FairnessGuard** | Sistema de deteccao de vies com 3 camadas: regex, implicito, semantico (LLM). |
| **WSI** | WeDoTalent Skill Index. Metodologia de avaliacao com 7 blocos. |
| **LangGraph** | Framework para grafos de estado. Usado no JobWizardGraph para fluxos sequenciais. |
| **LangChain** | Framework de orquestracao de LLMs. Base para prompts, chains e integracao. |
| **CascadedRouter** | Router em 3 camadas (cache → regex → LLM) para classificar intencao do usuario. |
| **FastRouter** | Tier 2 do CascadedRouter. Classifica ~80% das queries por regex sem custo LLM. |
| **IntentRouter** | Tier 3 do CascadedRouter. Usa LLM para queries ambiguas. |
| **BaseAgent** | Interface abstrata que todo agente implementa (process, domain_name, available_tools). |
| **AgentInput** | Entrada padronizada: message, context, metadata. |
| **AgentOutput** | Saida padronizada: response, actions, state_updates, navigation. |
| **STAGE_TOOLS** | Dicionario que mapeia estagio → lista de tools disponiveis naquele estagio. |
| **GUARDRAIL_TOOLS** | Tools que requerem confirmacao do usuario antes de executar (ex: save, delete). |
| **CircuitBreaker** | Padrao de resiliencia que interrompe chamadas a servicos que estao falhando. |
| **PII Masking** | Mascaramento de dados pessoais identificaveis para compliance LGPD. |
| **CompanyHiringPolicy** | Modelo no banco que armazena politicas de contratacao por empresa (multi-tenant). |
| **Feature Flag** | Chave liga/desliga para funcionalidades. Ex: `USE_REACT_AGENTS` controla routing. |
| **Prompt Injection** | Ataque onde usuario tenta manipular o LLM via input. Guard em `shared/prompt_injection.py`. |
| **WRF** | Weighted Ranking Function. Algoritmo de ranking ponderado para sourcing. |
| **DLQ** | Dead Letter Queue. Fila para tasks que falharam permanentemente. |
| **Observer** | ReActObserver que registra cada iteracao do ciclo ReAct para telemetria/debug. |
| **AgentScaffold** | Gerador de boilerplate que cria os 4 arquivos padrao de um agente ReAct. |
| **ActionExecutor** | Servico que executa acoes propostas por agentes, com confirmacao quando necessario. |
| **PendingActionState** | Estado de uma acao pendente de confirmacao do recrutador. Persiste entre mensagens. |
| **EnhancedBaseAgent** | Camada de robustez entre BaseAgent e agentes especificos. Sanitizacao, error handling, defensive prompts. |
| **AiConsumption** | Tabela que registra automaticamente tokens, custo e modelo de cada chamada LLM por tenant. |
| **AiCreditsBalance** | Modelo que controla limites mensais de tokens por empresa (monthly_limit, current_usage). |
| **FactChecker** | Validador deterministico de dados numericos (salario, scores) contra ranges fixos. |
| **AuditService** | Servico que registra todas as decisoes de IA para rastreabilidade e compliance. |
| **RBAC** | Role-Based Access Control. 3 roles: admin (acesso total), recruiter (own company), viewer (somente leitura). |
| **Human-in-the-Loop** | Principio: toda acao com efeito externo requer confirmacao do recrutador antes de executar. |
| **PromptInjectionGuard** | Guard que detecta 6 categorias de prompt injection em PT/EN com sanitizacao. |
| **ACTIONABLE_INTENTS** | Dicionario que mapeia intents executaveis (mover_candidato, enviar_email, etc.) a seus dominios, parametros e nivel de risco. |
| **Clarificacao Multi-turno** | Padrao onde a LIA pergunta parametros faltantes antes de executar, acumulando em PendingActionState. |
| **A/B Testing** | Sistema de experimentacao que compara variantes de prompts, modelos ou fluxos por tenant com atribuicao deterministica. |
| **ConversationGraph** | Grafo LangGraph principal da plataforma (47 nos, 4 subgrafos). Ponto de entrada de toda conversa. `shared/agents/conversation.py`. |
| **JobWizardGraph** | Grafo customizado (6 nos) para o wizard de criacao de vagas. Interface similar a LangGraph com conditional edges. |
| **WSIScreeningPipeline** | Orquestrador de perguntas de triagem WSI. Gera set unificado com 4 blocos (empresa, elegibilidade, tecnico, comportamental). `cv_screening/services/wsi_screening_pipeline.py`. |
| **PersonalizedFeedbackService** | Servico de feedback personalizado por IA (Claude). Gera, apresenta preview, e envia feedback multicanal com tracking. `cv_screening/services/personalized_feedback_service.py`. |
| **Big Five** | Modelo de personalidade com 5 dimensoes (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism). Usado no Bloco 5 de perguntas WSI. |
| **Bloom/Dreyfus** | Taxonomia de Bloom (6 niveis cognitivos) + Modelo Dreyfus (5 estagios de skill). Calibra perguntas tecnicas por senioridade. |
| **SchedulingService** | Servico de agendamento de entrevistas com integracao MS Graph, fallback .ics, e envio de convites multicanal. `interview_scheduling/services/scheduling_service.py`. |
| **SeniorityContextCalibrator** | Calibra nivel de senioridade com contexto (titulo, industria, pais, salario) para ajustar dificuldade de perguntas WSI. |

---

> **Ultima atualizacao**: 24/02/2026
> **Linhas**: ~2650+
> **Secoes**: 12 (reorganizadas: Orquestrador agora e Secao 4)
> **Termos no glossario**: 48
> **Integracoes externas**: 27
> **Modelos de dados**: 89
> **Arquivos shared**: ~118
> **Fluxos ponta-a-ponta documentados**: 4 (Perguntas WSI, Triagem WhatsApp, Agendamento, Feedback)
> **Grafos documentados**: ConversationGraph (47 nos), JobWizardGraph (6 nos), ReActLoop (ciclo)
> **Documento complementar**: `ai-architecture-audit.md` (auditoria completa, ~7500 linhas)
> **Documento complementar**: `PLANO_CICLO_FECHADO_LIA.md` (ciclo fechado, 682 linhas)
> **Mantido por**: Equipe de Engenharia LIA
