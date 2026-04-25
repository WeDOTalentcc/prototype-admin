# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system designed to optimize hiring processes. It leverages a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology to provide comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to revolutionize recruitment by offering advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics, ensuring an efficient, compliant, and intelligent solution that improves hiring quality and reduces time-to-hire. The platform covers the entire hiring cycle from attracting to hiring and analysis, with a focus on intelligent automation and detailed reporting.

# User Preferences
- Idioma: Português
- Design/Layout: Sempre perguntar antes de fazer mudanças em design ou layouts - o usuário quer avaliar propostas antes da implementação
- Separação Backend/Frontend: Manter estruturas de back e front completamente separadas (API REST/GraphQL no backend, SPA no frontend)
- Componentização: Priorizar componentes reutilizáveis e modulares, evitar código monolítico
- Preparação para Migração: Estruturar código pensando em possível conversão para Vue.js + Nuxt (frontend) e Ruby on Rails (backend)
- Border Radius: Seguir DS v4.2.1 — rounded-md (8px) padrão universal para botões/inputs/cards/modais, rounded-xl (16px) para interfaces imersivas (chat, login), rounded-full (pill) para badges/skills/avatars.
- Chat é a interface principal - O recrutador interage com a LIA através de conversa natural, NÃO através de botões
- LIA pergunta, recrutador responde - Quando uma etapa está completa, a LIA PERGUNTA se quer avançar. O recrutador RESPONDE no chat (ex: "sim", "vamos", "pode avançar")
- Painéis são suporte visual - Os painéis laterais mostram informações e permitem edição, mas a navegação e decisões são feitas via chat
- Sem botões como interface principal - Botões são apenas atalhos opcionais, NUNCA a forma principal de interação
- Transições via confirmação textual - O recrutador confirma avanço de etapa escrevendo no chat, não clicando em botões
- A LIA deve entender variações naturais de confirmação em português

# System Architecture
The platform uses Next.js, React, and TypeScript for the frontend, styled with Radix UI, shadcn/ui, and Tailwind CSS. The backend is built with FastAPI (Python) and PostgreSQL. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation and supports a custom agent marketplace with metering and billing. This system uses a CascadedRouter with 8 tiers and 19 canonical domains, managing 27 agents and tool permissions per tenant. **Severity-based delegation** (`_decide_agent_type_from_hints` em `app/orchestrator/main_orchestrator.py`): hints proativos do `PreConditionChecker` só desviam o turno para `company_settings` quando severity é `warning`/`critical` — hints `info` (benefits/culture/policy ausentes) ficam apenas como sugestão anexada ao prompt e a intenção primária do usuário (ex.: criar vaga) é executada normalmente.
- **Intelligent Conversational Interface (LIA)**: The primary interaction is chat-based, supporting multi-step reasoning, intent classification, and session persistence. It includes a unified chat system with WebSocket and SSE fallback. It supports a "5-Chat + 2-Channel Architecture" (Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy chats, integrated with WhatsApp and MS Teams).
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1. It features dynamic split-screen panels and a floating Super Prompt, with a redesigned sidebar and integrated TipTap Rich Text Editor.
- **WSI Screening**: A 6-block AI-powered methodology for comprehensive candidate evaluation, generating detailed reports with STAR analysis, Bloom/Dreyfus levels, gap analysis, and recommendations. Includes a public candidate-facing chat page for WSI screening with text and bidirectional audio support. WSI scoring has been scaled from 0-5 to 0-10 with corresponding adjustments to calculations and thresholds.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection. Includes a `BiasAuditService` to calculate adverse impact. Various compliance shields (FairnessGuard 3L, PII Masking 4L, FactChecker, BiasAudit Four-Fifths, AuditTrail SOX, Policy Engine, PromptInjectionGuard, C3B Layer, Scoring Safeguards) are integrated.
- **Job Creation & Candidate Management**: Supports conversational and manual job creation, with a Kanban candidate movement system featuring AI-powered sub-status prediction and WSI score integration. A Job Readiness Hub provides a 7-stage visual pipeline for preparing imported ATS vacancies.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` with LLM-powered smart parameter extraction.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` for messaging with `RedisBroker`, `RabbitMQBroker`, and `PubSubBroker` implementations.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API with Twilio as PSTN fallback.
- **Security & Production Readiness**: Includes robust authentication with httpOnly cookies, JWT, and WorkOS SSO, API security measures, unified health endpoint, structured logging, and global exception handlers. RLS (Row Level Security) is enforced at the PostgreSQL level.
- **Talent Intelligence Domain**: Implements competitive capabilities such as a Skills Ontology Engine, Internal Mobility matching, Workforce Planning, Interview Intelligence, and Passive Candidate Nurture.
- **Interview Intelligence Infrastructure**: Full interview lifecycle with Microsoft Calendar integration, Gemini-based audio/video transcription, and 5 services for WSI methodology, bias detection, comparative analysis, strategic opinion, and feedback generation.
- **External API Consumption Tracking**: Unified ledger for tracking external API costs per tenant from services like Apify and Pearch, with budget alerts.
- **ATS Integration**: Full integration with Gupy, Pandapé, and Merge.dev.
- **Monetizable Modules Infrastructure**: Provides a framework for managing and gating features as modules with different tiers and statuses (beta, trial, active, expired).
- **LLM Configuration**: Allows per-tenant configuration of LLM providers (Gemini, Claude, OpenAI).
- **Recursive RAG Chunking**: Implements a `RecursiveTextSplitter` strategy for hierarchical document chunking.
- **CrewAI-Style Delegation on AgentBus**: A formal multi-agent delegation system built on AgentBus with `AgentCrew`, `CrewPlan`, and `CrewPlanExecutor` for task orchestration.
- **Database Migrations**: Uses Alembic, with versions managed in `lia-agent-system/alembic/versions/`. Migrations are automated with `scripts/post-merge.sh` and ensure schema consistency.
- **Demo Tenant Seed Estendido (Task #813)**: `app/shared/services/seed_service.py` expõe `seed_demo_company_settings(db)`, função idempotente (skip-if-exists) e restrita ao tenant demo (`DEMO_COMPANY_UUID`) que popula 8 tabelas críticas — `company_benefits` (25 BR padrão), `company_culture_profiles`, `company_hiring_policies`, `company_compliance_controls` (5 controles × 3 frameworks), `company_responsibilities`, `company_skills_catalog` + `behavioral_competencies_catalog`, `company_retention_policies`, `company_screening_questions`. Garante a row canônica em `company_profiles` (id = DEMO_COMPANY_UUID) para satisfazer FK de culture profile. Após esse seed, os hints `benefits_catalog_empty`, `culture_profile_missing` e `hiring_policy_missing` do `PreConditionChecker` passam a retornar False para o tenant demo. Plugado dentro de `seed_demo_data` no entry point `/api/v1/admin/seed-data/demo`.
- **Auditoria Canônica do Chat Runtime (Task #817)**: `docs/audit/chat-runtime-audit.md` é o relatório (PT-BR) que mapeia 3 sintomas runtime do chat e suas correções canônicas. (1) **WS-token canônico**: `src/hooks/chat/useChatSocket.ts` é o ÚNICO consumidor produtivo de `/api/auth/ws-token` (já com retry 3× backoff 1500ms). Removidos 2 hooks de código morto (`src/hooks/use-float-streaming.ts` + `src/hooks/ai/use-float-streaming.ts`, ~675 linhas, 0 consumidores) + teste órfão. (2) **Pipeline-pulse defesa em profundidade**: consumer `chat-workflow-reels.tsx` agora valida `Array.isArray(data?.stages)` antes de iterar; proxy `src/app/api/backend-proxy/pipeline-pulse/route.ts` valida shape com `isValidPulsePayload` e retorna 502 explícito se backend devolver payload divergente em 200 OK. (3) **Intent classifier — falso positivo desmontado**: existem 2 classificadores legítimos (`IntentType` 5 valores para wizard / `EnhancedIntentType` 10 valores para chat geral) + 2 shims intencionais em `app/shared/services/` re-exportando o canônico em `app/domains/ai/services/` + 2 conceitos não-relacionados que apenas compartilham "intent" no nome. A constante `_COMPANY_SETTINGS_INTENTS` alegada NÃO existe (grep zerado). Testes regressivos: `tests/unit/test_intent_classifier_no_company_settings.py` (5 cenários) + `chat-workflow-reels-pulse.test.ts` (9 cenários) + `pipeline-pulse/route.test.ts` (7 cenários). 3 ADRs registrados.
- **Tenant Minimum Config Spec (Task #816)**: `docs/governance/tenant-minimum-config.md` é o contrato canônico (PT-BR) que define o "mínimo viável" de configuração para qualquer tenant LIA. Mapeia as 8 hints do `PreConditionChecker` → tabela alvo → query SQL → severity → cobertura pela #813; documenta que apenas `missing_company_id` (warning) bloqueia rota hoje, as 5 demais hints onboarding são `info` e só ruído. Define defaults canônicos por tabela (com marcador `[FAIR]` para os que exigem `FairnessGuard.check()` pré-persistência), matriz de seeding AUTO/ONBOARDING/MANUAL, cross-reference com WeDO Talent Guide v3.3 e skill lia-compliance, e enumera 7 próximas tarefas habilitadas (generalizar `seed_demo_company_settings` para qualquer tenant, wizard de onboarding, endpoint `/admin/tenants/{id}/bootstrap-defaults`, fechar gaps `incomplete_company_profile`/`company_website_missing` no demo, etc.). Spec-only: nenhuma mudança de código nesta task.

# External Dependencies
- Anthropic (Claude API)
- WorkOS
- Google Gemini (API, Live Audio API)
- Pearch AI
- Microsoft Graph
- Gupy ATS
- Pandapé ATS
- Merge (ATS connector)
- HubSpot
- Stripe
- Apify
- Mailgun (primary email)
- Resend (email fallback)
- PostgreSQL
- Redis
- Elasticsearch
- Sentry (error monitoring)
- OpenAI (Whisper, TTS — PSTN fallback only)
- Twilio (Voice — PSTN fallback only)
- Deepgram (STT/transcrição de voz)
- Celery