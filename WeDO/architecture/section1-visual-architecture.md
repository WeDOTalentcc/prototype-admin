#### 1. Visão Geral da Arquitetura

> **Mapa mental para o desenvolvedor.** Esta seção fornece a visão panorâmica que todo dev precisa antes de mergulhar nos cards individuais. Entenda as camadas, onde cada arquivo vive, como os grafos LangGraph se conectam e — mais importante — quais arquivos do protótipo podem ser portados diretamente para produção.
>
> **Leia esta seção primeiro** e depois consulte os cards Jira (Seções 2+) para detalhes de implementação de cada componente.

##### 1.1 Diagrama de Arquitetura — Camadas do Sistema

O protótipo LIA Agent System é organizado em **5 camadas** hierárquicas. Cada camada depende apenas das camadas abaixo dela:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CAMADA 1 — ENTRY POINTS                                                │
│  FastAPI (app/main.py, 377L) → /api/v1/* routes + /orchestrator/*       │
│  WebSocket (real-time chat) │ Background Workers (automações)           │
│  ~144 endpoints REST │ WorkOS JWT auth                                  │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CAMADA 2 — ORQUESTRAÇÃO E ROTEAMENTO                                   │
│  CascadedRouter (Memory → Fast → LLM)                                   │
│  ├── MemoryRouter: resolve referências conversacionais (cache O(1))     │
│  ├── FastRouter: keyword patterns, ~80% dos casos (254L, regex)         │
│  └── LLMRouter: classificação semântica (fallback, IntentRouter 384L)   │
│                                                                         │
│  Orchestrator (356L) → DomainRegistry (118L) → identifica domínio       │
│  PolicyEngine (147L) → validação de permissões e tenant scoping         │
│  PlanDetector (234L) → detecta multi-step plans                         │
│  PlanExecutor (231L) → executa planos com consolidação de respostas     │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CAMADA 3 — DOMÍNIOS (DDD)                                              │
│  Cada domínio segue: DomainPrompt ABC (171L) → DomainWorkflow (463L)    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │ Job         │ │ CV          │ │ Sourcing    │ │Communication│      │
│  │ Management  │ │ Screening   │ │             │ │             │      │
│  │ (198+37L)   │ │ (188+33L)   │ │ (122+38L)   │ │ (175+125L)  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │ Interview   │ │ ATS         │ │ Automation  │ │ Analytics   │      │
│  │ Scheduling  │ │ Integration │ │             │ │             │      │
│  │ (208+149L)  │ │ (207+127L)  │ │ (214+125L)  │ │ (202+149L)  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │
│  ┌─────────────┐                                                       │
│  │ Recruiter   │                                                       │
│  │ Assistant   │  → 9 domínios total (cada um: domain.py + actions.py) │
│  │ (218+145L)  │                                                       │
│  └─────────────┘                                                       │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CAMADA 4 — AGENTES ESPECIALIZADOS (13 agentes)                        │
│  Ag.0  Orchestrator (Pipeline Chat)               → AGT-000            │
│  Ag.1  JobIntakeAgent (4132L)                     → AGT-005            │
│  Ag.2  SourcingAgent (1881L)                      → AGT-006            │
│  Ag.3  TriagemCurricular (1384L)                  → AGT-002            │
│  Ag.4  EntrevistadorWSI (1117L)                   → AGT-007            │
│  Ag.5  AvaliadorWSI (1596L)                       → AGT-001            │
│  Ag.6  SchedulingAgent (1512L)                    → AGT-003            │
│  Ag.7  AnalistaFeedback (2068L)                   → AGT-008            │
│  Ag.8  IntegradorATS (704L)                       → AGT-009            │
│  Ag.9  TaskPlanner (821L)                         → AGT-010            │
│  Ag.10 CommunicationAgent (390L)                  → AGT-011            │
│  Ag.11 RecruiterAssistant (2551L)                 → AGT-012            │
│  Ag.12 AnalyticsAgent (465L)                      → (dentro Analytics) │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CAMADA 5 — SERVIÇOS E INFRAESTRUTURA                                   │
│  Shared Services: LLM Factory (439L), Embedding, WSI, ConversationMemory│
│  Compliance: FairnessGuard (195L), FactChecker (251L), LGPD            │
│  Resilience: CircuitBreaker (364L), CacheManager, StatsManager         │
│  Intelligence: SmartExtractor (213L), SemanticSearch                   │
│  Learning: LearningLoop (1073L), TemplateLearning (401L)               │
│  Robustness: InputValidation, ErrorHandling, DefensivePrompts (2585L)  │
│  Providers: Gemini, Claude, OpenAI, Mailgun, WhatsApp, Merge           │
│  ~177 service files │ ~369k linhas Python total                        │
└─────────────────────────────────────────────────────────────────────────┘
```

##### 1.2 Árvore de Diretórios Anotada

```
lia-agent-system/
├── app/
│   ├── main.py                             # FastAPI entry point (377L)
│   ├── agents/                             # Backward-compatible agents layer
│   │   ├── specialized/                    # 13 agentes (stubs → delegam para domains/)
│   │   │   ├── avaliador_wsi_agent.py      # Ag.5 → AGT-001 (WSI scoring)
│   │   │   ├── triagem_curricular_agent.py # Ag.3 → AGT-002
│   │   │   ├── scheduling_agent.py         # Ag.6 → AGT-003
│   │   │   ├── job_intake_agent.py         # Ag.1 → AGT-005
│   │   │   ├── sourcing_agent.py           # Ag.2 → AGT-006
│   │   │   ├── entrevistador_agent.py      # Ag.4 → AGT-007
│   │   │   ├── analista_feedback_agent.py  # Ag.7 → AGT-008
│   │   │   ├── integrador_ats_agent.py     # Ag.8 → AGT-009
│   │   │   ├── task_planner_agent.py       # Ag.9 → AGT-010
│   │   │   ├── communication_agent.py      # Ag.10 → AGT-011
│   │   │   ├── recruiter_assistant_agent.py # Ag.11 → AGT-012
│   │   │   ├── analytics_agent.py          # Analytics domain agent
│   │   │   └── screening_agent.py          # CV screening agent
│   │   ├── robustness/                     # Input validation, error handling → PREP-013
│   │   └── prompts/                        # Prompt registry + few-shot examples
│   │       └── examples/                   # Orchestrator, job planner, sourcing, pipeline
│   ├── domains/                            # ★ CORE DDD — Código canônico
│   │   ├── base.py                         # DomainPrompt ABC (171L) → PREP-002/INF-001
│   │   ├── registry.py                     # DomainRegistry + auto-discovery (118L) → PREP-004
│   │   ├── workflow.py                     # DomainWorkflow LangGraph (463L) → PREP-003/INF-002
│   │   ├── job_management/                 # Domínio: criação de vagas → AGT-005
│   │   │   ├── domain.py (198L), actions.py (37L)
│   │   │   ├── agents/
│   │   │   │   ├── job_intake_agent.py (4132L)         # Wizard principal
│   │   │   │   ├── job_drafting_agent.py (1420L)       # JD generation
│   │   │   │   ├── job_vacancy_nodes.py (1543L)        # ConversationGraph nodes
│   │   │   │   ├── job_lifecycle_agent.py (1071L)      # Ciclo de vida
│   │   │   │   ├── job_rubric_agent.py (566L)          # Rubrica de avaliação
│   │   │   │   ├── job_wizard_graph.py (401L)          # Wizard graph
│   │   │   │   ├── job_insights_agent.py (320L)        # Insights
│   │   │   │   └── job_benefits_comp_agent.py (155L)   # Benefits & compensation
│   │   │   ├── services/ (jd_generator, wizard, templates, enrichment...)
│   │   │   └── tools/ (job_tools, job_wizard_tools, query_tools)
│   │   ├── cv_screening/                   # Domínio: triagem + WSI → AGT-001/002/007
│   │   │   ├── domain.py (188L), actions.py (33L)
│   │   │   ├── agents/
│   │   │   │   ├── avaliador_wsi_agent.py (1596L)      # WSI scoring principal
│   │   │   │   ├── triagem_curricular_agent.py (1384L) # Triagem CV
│   │   │   │   └── screening_agent.py (443L)           # Screening
│   │   │   ├── services/ (wsi_scorer, cv_parser, question_generator...)
│   │   │   └── prompts/
│   │   ├── sourcing/                       # Domínio: busca de candidatos → AGT-006
│   │   │   ├── domain.py (122L), actions.py (38L)
│   │   │   ├── agents/
│   │   │   │   ├── sourcing_agent.py (1881L)           # Busca principal
│   │   │   │   └── engagement_nodes.py (1354L)         # Sourcing engagement flow
│   │   │   ├── services/ (5888L total)
│   │   │   │   ├── sourcing_pipeline.py (1117L)        # Pipeline principal
│   │   │   │   ├── pearch_service.py (1042L)           # Pearch AI integration
│   │   │   │   ├── candidate_search_route_service.py (1032L) # Search routing
│   │   │   │   ├── search_analytics.py (597L)          # Analytics de busca
│   │   │   │   ├── vacancy_search.py (511L)            # Busca por vaga
│   │   │   │   ├── apify_mcp_client.py (473L)          # Apify integration
│   │   │   │   ├── evaluation_criteria.py (465L)       # Critérios de avaliação
│   │   │   │   ├── apify_service.py (276L)             # Apify service
│   │   │   │   ├── pre_wrf_filter.py (104L)            # Pre-WRF filter
│   │   │   │   ├── es_analyzer.py (99L)                # Elasticsearch analyzer
│   │   │   │   ├── pgv_analyzer.py (90L)               # PGVector analyzer
│   │   │   │   └── wrf_service.py (81L)                # WRF ranking
│   │   │   └── tools/
│   │   ├── communication/                  # Domínio: email + WhatsApp → AGT-011
│   │   │   ├── domain.py (175L), actions.py (125L)
│   │   │   ├── agents/communication_agent.py (390L)
│   │   │   ├── services/ (email, whatsapp, notification, dispatcher)
│   │   │   └── tools/
│   │   ├── interview_scheduling/           # Domínio: agendamento → AGT-003
│   │   │   ├── domain.py (208L), actions.py (149L)
│   │   │   ├── agents/
│   │   │   │   ├── scheduling_agent.py (1512L)         # Agendamento principal
│   │   │   │   ├── entrevistador_agent.py (1117L)      # Entrevista WSI
│   │   │   │   └── interview_scheduling_nodes.py (418L) # Graph nodes
│   │   │   └── services/ (scheduling, calendar, ms_graph)
│   │   ├── ats_integration/                # Domínio: ATS sync → AGT-009
│   │   │   ├── domain.py (207L), actions.py (127L)
│   │   │   ├── agents/integrador_ats_agent.py (704L)
│   │   │   └── services/ (merge, gupy, pandape, ats_sync)
│   │   ├── automation/                     # Domínio: background jobs → AUT-001~008
│   │   │   ├── domain.py (214L), actions.py (125L)
│   │   │   ├── agents/task_planner_agent.py (821L)
│   │   │   └── services/ (automation_engine, scheduler, stage_automation, triggers)
│   │   ├── analytics/                      # Domínio: relatórios + KPIs
│   │   │   ├── domain.py (202L), actions.py (149L)
│   │   │   ├── agents/
│   │   │   │   ├── analista_feedback_agent.py (2068L)  # Feedback analysis
│   │   │   │   └── analytics_agent.py (465L)           # KPIs e reports
│   │   │   └── services/ (report, insights, predictive, monitoring)
│   │   └── recruiter_assistant/            # Domínio: assistente contextual → AGT-012
│   │       ├── domain.py (218L), actions.py (145L)
│   │       ├── agents/recruiter_assistant_agent.py (2551L)
│   │       └── services/ (conversation_memory, kanban, pipeline)
│   ├── orchestrator/                       # ★ Orchestration layer
│   │   ├── cascaded_router.py              # 3-tier routing (187L) → INF-003/PREP-005
│   │   ├── fast_router.py                  # Keyword-based routing (254L) → INF-004
│   │   ├── intent_router.py               # LLM-based intent routing (384L)
│   │   ├── orchestrator.py                # Main orchestrator (356L) → AGT-000
│   │   ├── policy_engine.py               # Permission + tenant validation (147L)
│   │   ├── state_manager.py               # State persistence (306L)
│   │   └── task_planner.py                # Task planning orchestration (235L)
│   ├── shared/                             # ★ Cross-domain infrastructure
│   │   ├── agents/
│   │   │   ├── conversation.py             # ConversationGraph LangGraph (1657L)
│   │   │   ├── nodes.py                    # JobWizardGraph nodes (1292L)
│   │   │   └── state_machine.py            # WizardStage/WizardIntent enums (467L)
│   │   ├── compliance/                     # FairnessGuard (195L), FactChecker (251L) → INF-006/007
│   │   ├── execution/                      # ExecutionPlan (149L), PlanDetector (234L), PlanExecutor (231L)
│   │   ├── governance/                     # FeatureFlags (315L), AgentMonitoring (580L) → INF-012/013
│   │   ├── intelligence/                   # SmartExtractor (213L), Embeddings, SemanticSearch → INF-009
│   │   ├── learning/                       # LearningLoop (1073L), TemplateLearning (401L) → LRN-001/002
│   │   ├── memory/                         # ConversationState (146L), ReferenceResolver (315L) → INF-008
│   │   ├── providers/                      # LLM Factory: Gemini (109L), Claude (96L), OpenAI (74L) → SRV-001
│   │   ├── repositories/                   # Base repo + candidate/company/job repos
│   │   ├── resilience/                     # CircuitBreaker (364L), CacheManager, StatsManager → INF-010
│   │   ├── robustness/                     # Error handling (269L), input validation (288L) → PREP-013
│   │   └── tools/                          # Export tools
│   ├── services/                           # Legacy services (backward-compatible, ~177 files)
│   │   ├── wsi_*.py                        # WSI pipeline (7 files) → SRV-002/003/004
│   │   ├── whatsapp_*.py                   # WhatsApp providers (5 files) → SRV-012
│   │   ├── email_*.py                      # Email providers (2 files) → SRV-011
│   │   ├── sourcing_pipeline_service.py    # Legacy sourcing (1102L) → SRV-009
│   │   ├── token_tracking_service.py       # Token usage tracking (622L) → INF-011
│   │   ├── embedding_service.py            # Embedding + semantic → SRV-008
│   │   └── ...
│   ├── api/v1/                             # ~144 REST endpoints
│   ├── auth/                               # WorkOS JWT auth
│   ├── config/                             # Settings, environment
│   ├── constants/                          # Business constants
│   ├── core/                               # Database, middleware
│   ├── data/templates/                     # Job templates
│   ├── models/                             # SQLAlchemy models
│   ├── schemas/                            # Pydantic schemas
│   ├── tools/                              # Tool registry (145L) + executor (335L) → PREP-008
│   ├── prompts/                            # Domain YAML prompts + shared prompts
│   │   ├── domains/                        # 9 YAML files (1 per domínio)
│   │   └── shared/                         # lia_persona.yaml (218L), defensive.yaml (163L), agent_prompts.yaml (1686L)
│   ├── templates/                          # Communication templates
│   └── utils/                              # Helpers, formatters
├── alembic/                                # Database migrations
├── training/                               # Fine-tuning data + RAG knowledge
│   ├── data_generation/                    # Synthetic data for training
│   └── rag_knowledge/                      # RAG knowledge base (WSI methodology)
├── tests/                                  # Test suites
└── docs/                                   # Architecture + methodology docs
```

##### 1.3 Grafos LangGraph — Fluxos Visuais

###### 1.3.1 ConversationGraph (1657L — `app/shared/agents/conversation.py`)

O grafo principal da LIA. Recebe mensagem do usuário, classifica intenção via LLM, extrai entidades, e roteia para o subgrafo correto:

```
                    ┌─────────────────┐
                    │     START       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ classify_intent  │ ← LLM classifica intenção
                    │ (Claude)         │   create_job | search_candidates |
                    └────────┬────────┘   schedule_interview | chitchat...
                             │
                    ┌────────▼────────┐
                    │ extract_entities │ ← NER: extrai cargo, skills,
                    │ (Claude)         │   localização, senioridade...
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────────────────────┐
              │              │                              │
    ┌─────────▼──────┐ ┌────▼───────────┐        ┌────────▼─────────────┐
    │ ask_           │ │ execute_       │        │ create_job_vacancy   │
    │ clarification  │ │ candidate_     │        │ (Job Wizard subgraph)│
    │ (falta info)   │ │ search         │        │                      │
    └───────┬────────┘ └────────┬───────┘        └────────┬─────────────┘
            │                   │                          │
            │           ┌──────▼───────┐       ┌──────────▼──────────┐
            │           │execute_global│       │ job_state_loader    │
            │           │_search       │       │      ↓              │
            │           │ (Pearch AI)  │       │ job_router ←───────┐│
            │           └──────┬───────┘       │      ↓ (stages)   ││
            │                  │               │ onboarding         ││
            │                  │               │ basics_collector   ││
            │                  │               │ remuneration       ││
            │                  │               │ org_structure      ││
            │                  │               │ technical_matrix   ││
            │                  │               │ sourcing_strategy  ││
            │                  │               │ wsi_competencies   ││
            │                  │               │ interview_flow     ││
            │                  │               │ governance         ││
            │                  │               │ comm_templates     ││
            │                  │               │ screening          ││
            │                  │               │ jd_generator       ││
            │                  │               │ publication────────┘│
            │                  │               └────────────────────┘
            │                  │
            └──────────┬───────┘
                       │
              ┌────────▼────────┐
              │ generate_       │ ← Formata resposta final
              │ response        │   (Markdown + emojis + sugestões)
              └────────┬────────┘
                       │
                    ┌──▼──┐
                    │ END │
                    └─────┘
```

**Subgrafo: schedule_interview** (simplificado)
```
interview_state_loader → interview_router → interview_details_collector
    → interview_validator → interview_scheduler_executor → interview_response_planner
```

**Subgrafo: sourcing_engagement** (simplificado)
```
sourcing_state_initializer → local_search_node → calibration_node
    → volume_assessment_node → global_expansion_node → contact_approval_node
    → email_outreach_node → async_screening_node → candidate_feedback_node
    → recruiter_report_node → recruiter_decision_node
    → auto_scheduling_node / rejection_feedback_node / placement_node
```

###### 1.3.2 JobWizardGraph (1292L — `app/shared/agents/nodes.py`)

O wizard de criação de vagas. 6 nós LLM-powered que operam em loop até completar todas as etapas:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  JobWizardGraph — 6 Nós LLM-powered (Smart Orchestrator)                │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ intent_      │───▶│ field_       │───▶│ tool_        │               │
│  │ classifier   │    │ extractor    │    │ router       │               │
│  │ (Gemini)     │    │ (Gemini)     │    │              │               │
│  └──────────────┘    └──────────────┘    └───────┬──────┘               │
│                                                   │                      │
│                                           ┌───────▼──────┐              │
│                                           │ tool_        │              │
│                                           │ executor     │              │
│                                           │ (registry)   │              │
│                                           └───────┬──────┘              │
│                                                   │                      │
│  ┌──────────────┐    ┌──────────────┐    ┌───────▼──────┐              │
│  │ stage_       │◀───│ response_    │◀───│              │              │
│  │ transition   │    │ generator    │    │              │              │
│  │              │    │ (stage-      │    │              │              │
│  │              │    │  specific    │    │              │              │
│  │              │    │  prompts)    │    │              │              │
│  └──────┬───────┘    └──────────────┘    └──────────────┘              │
│         │                                                               │
│         ▼ (loop: should_continue?)                                      │
│  WizardStage: INITIAL → TITLE_DEPARTMENT → JOB_SUMMARY → SALARY       │
│               → COMPETENCIES → SCREENING → REVIEW → COMPLETE           │
│                                                                         │
│  State: JobWizardState (467L) — TypedDict com:                          │
│  ├── messages, current_stage, job_draft, confidence_scores              │
│  ├── reasoning_steps, tool_calls, tool_results                          │
│  └── session_id, company_id, should_continue, awaiting_confirmation     │
└──────────────────────────────────────────────────────────────────────────┘
```

###### 1.3.3 DomainWorkflow (463L — `app/domains/workflow.py`)

Pipeline genérico que qualquer domínio usa. 3 nós principais + pre/post checks:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DomainWorkflow — Pipeline genérico para qualquer domínio               │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │ _pre_check   │──▶│ _resolve_    │──▶│ _analyze_    │                │
│  │ (Fairness    │   │  references  │   │  intent      │                │
│  │  Guard)      │   │ (Reference   │   │ (SmartExtract│                │
│  └──────────────┘   │  Resolver)   │   │ + Domain     │                │
│                     └──────────────┘   │  .process_   │                │
│                                        │   intent())  │                │
│                                        └───────┬──────┘                │
│                                                │                        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────▼───────┐               │
│  │ _post_check  │◀──│ _format      │◀──│ _execute     │               │
│  │ (Fact        │   │ (suggestions │   │ (Domain      │               │
│  │  Checker)    │   │  + metadata) │   │  .execute_   │               │
│  └──────────────┘   └──────────────┘   │   action())  │               │
│                                        └──────────────┘                │
│                                                                         │
│  Cada domínio implementa DomainPrompt ABC (171L):                       │
│  ├── get_system_prompt()      # Prompt do agente                       │
│  ├── get_allowed_actions()    # Lista de ações disponíveis             │
│  ├── process_intent()         # LLM classifica intenção                │
│  ├── execute_action()         # Executa ação → DomainResponse          │
│  ├── validate_context()       # Valida contexto necessário             │
│  ├── get_suggestions()        # Sugestões proativas                    │
│  └── get_action_by_id()       # Busca ação por ID                      │
│                                                                         │
│  WorkflowStep enum: PRE_CHECK → RESOLVE_REFERENCES → SMART_EXTRACT    │
│                     → ANALYZE_INTENT → EXECUTE → FORMAT → POST_CHECK   │
│                     → COMPLETE | ERROR                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

##### 1.4 Lista de Arquivos Aproveitáveis — Inventário por Card Jira

> **Legenda:** ✅ Portável direto (adaptar imports/ORM) · 🔧 Adaptar (lógica aproveitável, requer reestruturação) · ❌ Rebuild from specs

###### Infraestrutura Core

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/domains/base.py` | 171 | PREP-002 / INF-001 | ✅ Direto | ABC → Ruby concern ou Python ABC. Dataclasses portáveis |
| `app/domains/workflow.py` | 463 | PREP-003 / INF-002 | ✅ Direto | LangGraph pipeline portável. 3 nós + pre/post checks |
| `app/domains/registry.py` | 118 | PREP-004 | ✅ Direto | Singleton pattern + auto-discovery decorator |
| `app/orchestrator/cascaded_router.py` | 187 | INF-003 / PREP-005 | ✅ Direto | 3-tier routing: memory → fast → LLM |
| `app/orchestrator/fast_router.py` | 254 | INF-004 | ✅ Direto | Regex patterns. Resolve ~80% dos casos |
| `app/orchestrator/intent_router.py` | 384 | INF-004 | ✅ Direto | LLM-based intent classification |
| `app/orchestrator/orchestrator.py` | 356 | AGT-000 | 🔧 Adaptar | Grafo complexo com cache + plans + domains |
| `app/orchestrator/policy_engine.py` | 147 | AGT-000 | ✅ Direto | Permission + tenant validation |
| `app/orchestrator/state_manager.py` | 306 | AGT-000 | 🔧 Adaptar | State persistence (trocar in-memory → Redis/DB) |
| `app/orchestrator/task_planner.py` | 235 | AGT-010 | ✅ Direto | Task planning orchestration |
| `app/shared/memory/conversation_state.py` | 146 | INF-008 | ✅ Direto | Conversation state tracking |
| `app/shared/memory/reference_resolver.py` | 315 | INF-008 | ✅ Direto | Pronoun/reference resolution |
| `app/shared/compliance/fairness_guard.py` | 195 | INF-006 | ✅ Direto | Bias detection, 100% determinístico |
| `app/shared/compliance/fact_checker.py` | 251 | INF-007 | ✅ Direto | Response verification |
| `app/shared/intelligence/smart_extractor.py` | 213 | INF-009 | ✅ Direto | Entity extraction with caching |
| `app/shared/governance/feature_flag_service.py` | 315 | INF-012 | ✅ Direto | Feature flag management |
| `app/shared/governance/agent_monitoring_service.py` | 580 | INF-013 | ✅ Direto | Agent health monitoring |
| `app/shared/resilience/circuit_breaker.py` | 364 | INF-010 | ✅ Direto | Circuit breaker pattern |
| `app/services/token_tracking_service.py` | 622 | INF-011 | ✅ Direto | Token usage tracking + billing |
| `app/shared/execution/execution_plan.py` | 149 | AGT-000 | ✅ Direto | Multi-step plan dataclass |
| `app/shared/execution/plan_detector.py` | 234 | AGT-000 | ✅ Direto | Multi-step plan detection |
| `app/shared/execution/plan_executor.py` | 231 | AGT-000 | ✅ Direto | Plan execution + consolidation |

**Subtotal Infraestrutura:** 22 arquivos · 5,831L · 20 ✅ + 2 🔧

###### Grafos LangGraph

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/shared/agents/conversation.py` | 1657 | AGT-000 / AGT-004 | 🔧 Adaptar | Grafo conversacional complexo. Extrair lógica dos nós |
| `app/shared/agents/nodes.py` | 1292 | AGT-005 (wizard) | 🔧 Adaptar | 6 nós LLM-powered. Prompts 100% portáveis |
| `app/shared/agents/state_machine.py` | 467 | AGT-005 | ✅ Direto | Enums, TypedDict, schemas. 100% portável |

**Subtotal Grafos:** 3 arquivos · 3,416L · 1 ✅ + 2 🔧

###### Domínios (domain.py + actions.py)

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/domains/job_management/domain.py` | 198 | AGT-005 | ✅ Direto | DomainPrompt impl para vagas |
| `app/domains/job_management/actions.py` | 37 | AGT-005 | ✅ Direto | DomainAction definitions |
| `app/domains/cv_screening/domain.py` | 188 | AGT-001/002 | ✅ Direto | DomainPrompt impl para triagem |
| `app/domains/cv_screening/actions.py` | 33 | AGT-001/002 | ✅ Direto | DomainAction definitions |
| `app/domains/sourcing/domain.py` | 122 | AGT-006 | ✅ Direto | DomainPrompt impl para sourcing |
| `app/domains/sourcing/actions.py` | 38 | AGT-006 | ✅ Direto | DomainAction definitions |
| `app/domains/communication/domain.py` | 175 | AGT-011 | ✅ Direto | DomainPrompt impl para comunicação |
| `app/domains/communication/actions.py` | 125 | AGT-011 | ✅ Direto | DomainAction definitions |
| `app/domains/interview_scheduling/domain.py` | 208 | AGT-003 | ✅ Direto | DomainPrompt impl para agendamento |
| `app/domains/interview_scheduling/actions.py` | 149 | AGT-003 | ✅ Direto | DomainAction definitions |
| `app/domains/ats_integration/domain.py` | 207 | AGT-009 | ✅ Direto | DomainPrompt impl para ATS |
| `app/domains/ats_integration/actions.py` | 127 | AGT-009 | ✅ Direto | DomainAction definitions |
| `app/domains/automation/domain.py` | 214 | AUT-001~008 | ✅ Direto | DomainPrompt impl para automação |
| `app/domains/automation/actions.py` | 125 | AUT-001~008 | ✅ Direto | DomainAction definitions |
| `app/domains/analytics/domain.py` | 202 | Analytics | ✅ Direto | DomainPrompt impl para analytics |
| `app/domains/analytics/actions.py` | 149 | Analytics | ✅ Direto | DomainAction definitions |
| `app/domains/recruiter_assistant/domain.py` | 218 | AGT-012 | ✅ Direto | DomainPrompt impl para assistente |
| `app/domains/recruiter_assistant/actions.py` | 145 | AGT-012 | ✅ Direto | DomainAction definitions |

**Subtotal Domínios:** 18 arquivos · 2,660L · 18 ✅

###### Agentes Especializados (domains/*/agents/)

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/domains/job_management/agents/job_intake_agent.py` | 4132 | AGT-005 | 🔧 Adaptar | Wizard principal. Prompts portáveis, grafo adaptar |
| `app/domains/job_management/agents/job_drafting_agent.py` | 1420 | AGT-005 | 🔧 Adaptar | JD generation. Prompts + templates portáveis |
| `app/domains/job_management/agents/job_vacancy_nodes.py` | 1543 | AGT-005 | 🔧 Adaptar | ConversationGraph job nodes |
| `app/domains/job_management/agents/job_lifecycle_agent.py` | 1071 | AGT-005 | 🔧 Adaptar | Job lifecycle management |
| `app/domains/job_management/agents/job_rubric_agent.py` | 566 | AGT-005 | ✅ Direto | Rubrica de avaliação, lógica pura |
| `app/domains/job_management/agents/job_wizard_graph.py` | 401 | AGT-005 | 🔧 Adaptar | LangGraph wizard graph |
| `app/domains/job_management/agents/job_insights_agent.py` | 320 | AGT-005 | ✅ Direto | Job insights analytics |
| `app/domains/job_management/agents/job_benefits_comp_agent.py` | 155 | AGT-005 | ✅ Direto | Benefits & compensation |
| `app/domains/cv_screening/agents/avaliador_wsi_agent.py` | 1596 | AGT-001 | 🔧 Adaptar | WSI scoring principal. Algoritmo portável |
| `app/domains/cv_screening/agents/triagem_curricular_agent.py` | 1384 | AGT-002 | 🔧 Adaptar | Triagem CV. Prompts portáveis |
| `app/domains/cv_screening/agents/screening_agent.py` | 443 | AGT-002 | ✅ Direto | CV screening |
| `app/domains/sourcing/agents/sourcing_agent.py` | 1881 | AGT-006 | 🔧 Adaptar | Busca principal. Pipeline portável |
| `app/domains/sourcing/agents/engagement_nodes.py` | 1354 | AGT-006 | 🔧 Adaptar | Sourcing engagement flow |
| `app/domains/communication/agents/communication_agent.py` | 390 | AGT-011 | ✅ Direto | Email + WhatsApp agent |
| `app/domains/interview_scheduling/agents/scheduling_agent.py` | 1512 | AGT-003 | 🔧 Adaptar | Calendar + MS Graph integration |
| `app/domains/interview_scheduling/agents/entrevistador_agent.py` | 1117 | AGT-007 | 🔧 Adaptar | Entrevista WSI. Prompts portáveis |
| `app/domains/interview_scheduling/agents/interview_scheduling_nodes.py` | 418 | AGT-003 | ✅ Direto | Interview graph nodes |
| `app/domains/ats_integration/agents/integrador_ats_agent.py` | 704 | AGT-009 | 🔧 Adaptar | ATS sync (Merge, Gupy, Pandapé) |
| `app/domains/automation/agents/task_planner_agent.py` | 821 | AGT-010 | 🔧 Adaptar | Task automation planner |
| `app/domains/analytics/agents/analista_feedback_agent.py` | 2068 | AGT-008 | 🔧 Adaptar | Feedback analysis |
| `app/domains/analytics/agents/analytics_agent.py` | 465 | Analytics | ✅ Direto | KPIs e reports |
| `app/domains/recruiter_assistant/agents/recruiter_assistant_agent.py` | 2551 | AGT-012 | 🔧 Adaptar | Assistente contextual |

**Subtotal Agentes:** 22 arquivos · 26,312L · 8 ✅ + 14 🔧

###### Serviços WSI

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/services/wsi_deterministic_scorer.py` | stub | SRV-004 | ✅ Direto | 100% determinístico, scoring WSI |
| `app/services/wsi_question_generator.py` | stub | SRV-003 | ✅ Direto | Geração de perguntas WSI |
| `app/services/wsi_screening_pipeline.py` | stub | SRV-002 | ✅ Direto | Pipeline de triagem WSI |
| `app/services/wsi_service.py` | stub | SRV-002 | ✅ Direto | WSI service principal |
| `app/services/wsi_question_adjuster.py` | stub | SRV-003 | ✅ Direto | Ajuste de perguntas WSI |
| `app/services/wsi_question_service.py` | stub | SRV-003 | ✅ Direto | Question management |
| `app/services/wsi_voice_orchestrator.py` | stub | SRV-005 | ✅ Direto | Voice interview orchestration |

**Subtotal WSI:** 7 arquivos (stubs delegando para domains/) · 7 ✅

###### Serviços de Comunicação

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/services/whatsapp_factory.py` | stub | SRV-012 / INT-AI-007 | ✅ Direto | Provider factory |
| `app/services/whatsapp_meta_service.py` | stub | SRV-012 / INT-AI-007 | 🔧 Adaptar | Meta Business API |
| `app/services/whatsapp_provider.py` | stub | SRV-012 / INT-AI-007 | ✅ Direto | Provider interface |
| `app/services/whatsapp_service.py` | stub | SRV-012 / INT-AI-007 | ✅ Direto | Service principal |
| `app/services/whatsapp_twilio_service.py` | stub | SRV-012 / INT-AI-007 | 🔧 Adaptar | Twilio integration |
| `app/services/email_providers.py` | stub | SRV-011 / INT-AI-003 | ✅ Direto | Email provider factory |
| `app/services/email_service.py` | stub | SRV-011 / INT-AI-003 | ✅ Direto | Email service principal |

**Subtotal Comunicação:** 7 arquivos · 5 ✅ + 2 🔧

###### Sourcing Services

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/domains/sourcing/services/sourcing_pipeline.py` | 1117 | SRV-009 | ✅ Direto | Pipeline de sourcing principal |
| `app/domains/sourcing/services/pearch_service.py` | 1042 | SRV-009 | 🔧 Adaptar | Pearch AI integration (API externa) |
| `app/domains/sourcing/services/candidate_search_route_service.py` | 1032 | SRV-009 | 🔧 Adaptar | Search routing |
| `app/domains/sourcing/services/search_analytics.py` | 597 | SRV-009 | ✅ Direto | Search analytics |
| `app/domains/sourcing/services/vacancy_search.py` | 511 | SRV-009 | ✅ Direto | Vacancy search |
| `app/domains/sourcing/services/apify_mcp_client.py` | 473 | SRV-009 | 🔧 Adaptar | Apify MCP client |
| `app/domains/sourcing/services/evaluation_criteria.py` | 465 | SRV-009 | ✅ Direto | Evaluation criteria |
| `app/domains/sourcing/services/apify_service.py` | 276 | SRV-009 | 🔧 Adaptar | Apify service |
| `app/domains/sourcing/services/pre_wrf_filter.py` | 104 | SRV-009 | ✅ Direto | Pre-WRF filter |
| `app/domains/sourcing/services/es_analyzer.py` | 99 | SRV-009 | ✅ Direto | Elasticsearch analyzer |
| `app/domains/sourcing/services/pgv_analyzer.py` | 90 | SRV-009 | ✅ Direto | PGVector analyzer |
| `app/domains/sourcing/services/wrf_service.py` | 81 | SRV-009 | ✅ Direto | WRF ranking algorithm |
| `app/services/sourcing_pipeline_service.py` | 1102 | SRV-009 | 🔧 Adaptar | Legacy sourcing (delega para domain) |

**Subtotal Sourcing:** 13 arquivos · 6,989L · 8 ✅ + 5 🔧

###### Providers (LLM Factory)

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/shared/providers/llm_provider.py` | 110 | SRV-001 | ✅ Direto | Base provider ABC |
| `app/shared/providers/llm_factory.py` | 50 | SRV-001 | ✅ Direto | Multi-provider factory |
| `app/shared/providers/llm_claude.py` | 96 | SRV-001 | ✅ Direto | Claude (Anthropic) provider |
| `app/shared/providers/llm_gemini.py` | 109 | SRV-001 | ✅ Direto | Gemini (Google) provider |
| `app/shared/providers/llm_openai.py` | 74 | SRV-001 | ✅ Direto | OpenAI provider |

**Subtotal Providers:** 5 arquivos · 439L · 5 ✅

###### Learning & Intelligence

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/shared/learning/learning_loop_service.py` | 1073 | LRN-001 | ✅ Direto | Feedback loop de aprendizado |
| `app/shared/learning/template_learning_service.py` | 401 | LRN-002 | ✅ Direto | Template learning |

**Subtotal Learning:** 2 arquivos · 1,474L · 2 ✅

###### Robustness

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/shared/robustness/context_management.py` | 298 | PREP-013 | ✅ Direto | Context management |
| `app/shared/robustness/error_handling.py` | 269 | PREP-013 | ✅ Direto | Error handling patterns |
| `app/shared/robustness/input_validation.py` | 288 | PREP-013 | ✅ Direto | Input validation rules |
| `app/shared/robustness/intent_schemas.py` | 485 | PREP-013 | ✅ Direto | Intent validation schemas |
| `app/shared/robustness/response_filter.py` | 364 | PREP-013 | ✅ Direto | Response filtering |
| `app/shared/robustness/enhanced_base.py` | 300 | PREP-013 | ✅ Direto | Enhanced base agent |
| `app/shared/robustness/enhanced_registry.py` | 320 | PREP-013 | ✅ Direto | Enhanced registry |
| `app/shared/robustness/defensive_prompts.py` | 108 | PREP-013 | ✅ Direto | Defensive prompt patterns |

**Subtotal Robustness:** 8 arquivos · 2,432L · 8 ✅

###### Tools

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/tools/registry.py` | 145 | PREP-008 | ✅ Direto | Tool registry + discovery |
| `app/tools/executor.py` | 335 | PREP-008 | ✅ Direto | Tool execution engine |

**Subtotal Tools:** 2 arquivos · 480L · 2 ✅

###### Prompts (100% portáveis — texto puro)

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/prompts/domains/sourcing.yaml` | 7 | AGT-006 | ✅ Direto | System prompt sourcing |
| `app/prompts/domains/job_management.yaml` | 7 | AGT-005 | ✅ Direto | System prompt job mgmt |
| `app/prompts/domains/cv_screening.yaml` | 7 | AGT-001/002 | ✅ Direto | System prompt CV screening |
| `app/prompts/domains/communication.yaml` | 7 | AGT-011 | ✅ Direto | System prompt comunicação |
| `app/prompts/domains/interview_scheduling.yaml` | 7 | AGT-003/007 | ✅ Direto | System prompt entrevistas |
| `app/prompts/domains/analytics.yaml` | 7 | Analytics | ✅ Direto | System prompt analytics |
| `app/prompts/domains/ats_integration.yaml` | 7 | AGT-009 | ✅ Direto | System prompt ATS |
| `app/prompts/domains/automation.yaml` | 7 | AUT-001~008 | ✅ Direto | System prompt automação |
| `app/prompts/domains/recruiter_assistant.yaml` | 7 | AGT-012 | ✅ Direto | System prompt assistente |
| `app/prompts/shared/lia_persona.yaml` | 218 | PREP-001 | ✅ Direto | Persona base da LIA |
| `app/prompts/shared/defensive.yaml` | 163 | PREP-013 | ✅ Direto | Regras de segurança e ética |
| `app/prompts/shared/agent_prompts.yaml` | 1686 | PREP-001 | ✅ Direto | Prompts expandidos completos |
| `app/shared/prompts/prompt_registry.py` | 496 | PREP-001 | ✅ Direto | Prompt registry |
| `app/shared/prompts/agent_prompts.py` | 74 | PREP-001 | ✅ Direto | Agent prompt helpers |
| `app/prompts/kanban_assistant_prompts.py` | 777 | AGT-012 | ✅ Direto | Kanban assistant prompts |
| `app/prompts/templates.py` | 245 | PREP-001 | ✅ Direto | Prompt templates |
| `app/prompts/examples.py` | 387 | PREP-001 | ✅ Direto | Few-shot examples |
| `app/prompts/cot.py` | 305 | PREP-001 | ✅ Direto | Chain-of-thought prompts |
| `app/prompts/job_wizard.py` | 411 | AGT-005 | ✅ Direto | Job wizard prompts |

**Subtotal Prompts:** 19 arquivos · 4,824L · 19 ✅

###### Outros Serviços de Infraestrutura

| Arquivo do Protótipo | Linhas | Card Jira | Aproveitamento | Produção (equivalente) |
|----------------------|:------:|-----------|:--------------:|------------------------|
| `app/services/token_tracking_service.py` | 622 | INF-011 | ✅ Direto | Token usage + cost tracking |
| `app/main.py` | 377 | PREP-001 | ❌ Rebuild | FastAPI entry point — adaptar para prod |

**Subtotal Outros:** 2 arquivos · 999L · 1 ✅ + 1 ❌

---

###### Resumo do Inventário

| Categoria | Arquivos | Linhas | ✅ Direto | 🔧 Adaptar | ❌ Rebuild |
|-----------|:--------:|:------:|:---------:|:----------:|:----------:|
| Infraestrutura Core | 22 | 5,831 | 20 | 2 | 0 |
| Grafos LangGraph | 3 | 3,416 | 1 | 2 | 0 |
| Domínios (domain+actions) | 18 | 2,660 | 18 | 0 | 0 |
| Agentes Especializados | 22 | 26,312 | 8 | 14 | 0 |
| Serviços WSI | 7 | ~7 (stubs) | 7 | 0 | 0 |
| Comunicação | 7 | ~7 (stubs) | 5 | 2 | 0 |
| Sourcing Services | 13 | 6,989 | 8 | 5 | 0 |
| Providers (LLM) | 5 | 439 | 5 | 0 | 0 |
| Learning | 2 | 1,474 | 2 | 0 | 0 |
| Robustness | 8 | 2,432 | 8 | 0 | 0 |
| Tools | 2 | 480 | 2 | 0 | 0 |
| Prompts | 19 | 4,824 | 19 | 0 | 0 |
| Outros | 2 | 999 | 1 | 0 | 1 |
| **TOTAL** | **130** | **~56k** | **104 (80%)** | **25 (19%)** | **1 (1%)** |

> **Nota:** O protótipo completo tem ~936 arquivos Python totalizando ~369k linhas. A tabela acima cobre os **130 arquivos arquiteturalmente relevantes** (~56k linhas) que mapeiam diretamente para cards Jira. Os demais ~806 arquivos são models, schemas, migrations, utils, configs e endpoints REST que serão reimplementados na stack de produção seguindo os mesmos contratos.
>
> **Conclusão de portabilidade:**
> - **80% dos arquivos-chave** (104 de 130) podem ser portados diretamente com adaptação mínima de imports e ORM
> - **19%** (25 arquivos) requerem reestruturação mas têm lógica de negócio e prompts aproveitáveis
> - **Apenas 1%** (1 arquivo — entry point FastAPI) precisa ser reconstruído from scratch
> - **Prompts são 100% portáveis** — texto puro, independente de linguagem ou framework
