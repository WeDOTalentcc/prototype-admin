# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system that optimizes hiring processes using a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology. It provides comprehensive candidate assessment (technical, behavioral, cultural fit) through an intelligent, conversational, and data-driven platform. LIA aims to revolutionize recruitment with advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics, ensuring a compliant, efficient, and intelligent solution that enhances hiring quality and reduces time-to-hire.

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
The platform utilizes Next.js, React, and TypeScript for the frontend, styled with Radix UI, shadcn/ui, and Tailwind CSS. The backend is built with FastAPI (Python) and PostgreSQL. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation.
- **Intelligent Conversational Interface (LIA)**: Primary interaction is chat-based for job creation and candidate screening, featuring intent classification, multi-step reasoning, and session persistence.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1. Dynamic split-screen panels and a floating Super Prompt enhance user interaction.
- **WSI Screening**: A 6-block (0-5) AI-powered methodology for comprehensive candidate evaluation, including a detailed report with STAR analysis, Bloom/Dreyfus levels, gap analysis, and recommendations.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and factual accuracy.
- **Job Creation Flow**: Supports both conversational ("Criar com a LIA") and manual entry ("Criar manualmente").
- **Kanban Candidate Movement System**: Features AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` and `PendingActionState` with LLM-powered smart parameter extraction.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring, including a post-vector-search filter using Gemini Flash LLM.
- **LangGraph Agent System**: All agents use LangGraph natively.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI screening with text and bidirectional audio support (TTS/STT).
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` with `RedisBroker` (default), `RabbitMQBroker`, and `PubSubBroker` for messaging.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API with Twilio as PSTN fallback.
- **Microsoft Teams Notifications**: TeamsBot provides adaptive cards for various notifications.
- **Apify Candidate Enrichment**: Enriches candidate profiles via LinkedIn and email discovery.
- **Gate 2 Re-Discovery Embedding**: Automatically generates Gemini embeddings for rejected candidates for future vector-similarity matching.
- **A/B Testing Email Templates**: Manages A/B testing for email templates with variant assignment, metric recording, and analysis.
- **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
- **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions.
- **Proactive Predictive Briefing**: LIA proactively presents a briefing with pipeline stats, candidate alerts, and ML predictions.
- **Security Audit & Hardening**: Authentication uses httpOnly cookies with JWT and WorkOS SSO. API security measures include enforced `request.state.user_id` for critical endpoints and robust email provider chaining. ATS integration includes SSRF allowlist and HMAC-SHA256 webhook signatures.
- **Profile Analysis BARS+WSI**: Enriched `AnalysisService` with unified BARS rubric evaluation + WSI Big Five trait inference from CV text.
- **Zustand State Management**: Introduced zustand for centralized state management, covering auth, kanban, and candidate data.
- **Performance Improvements**: Implemented lazy loading for modals and error boundaries for major pages.
- **Unified LIA Chat System**: Replaced fragmented chat systems with a single `LiaChatContext` for shared message store, persistent `conversation_id`, and a single backend communication channel, with HTTP Chat Fallback for WebSocket unavailability.
- **Hooks Organization**: 120 hooks organized into 9 domain folders under `src/hooks/`: `ai/`, `candidates/`, `chat/`, `company/`, `jobs/`, `recruitment/`, `search/`, `shared/`, `ui/`. Each domain has a barrel `index.ts`. Pre-existing `prompt/` and `settings/` subdirectories remain. Import pattern: `@/hooks/domain/hookName`.
- **OpenAPI TypeScript Types**: Auto-generated from backend OpenAPI spec via `npm run generate:api-types` → `src/types/api.generated.ts`.
- **Multi-Tenancy `company_id` Isolation**: Implemented `client_account_id` FK in `CompanyProfile`, tenant resolution endpoint, `useCompanyId` React hook, and `useCurrentCompany` hook. User management uses `tenantId`.
- **Reports & Predictions Real Data**: Frontend reports/predictions pages now fetch real data from backend endpoints.
- **ATS Integration**: Full ATS integration with Gupy, Pandapé, and Merge.dev.
- **Credits Infrastructure**: `CreditAccount` and `CreditTransaction` models with `CreditService` for managing credit balance and transactions.
- **Interview Flow with Company Stages**: Added `recruitment_stage_id` FK to Interview model, allowing scheduling based on company-configured stages.
- **Rails→FastAPI Frontend Migration**: All frontend proxy route files migrated from Rails to FastAPI, making FastAPI the sole backend for all frontend routes.
- **Choose Your AI — LLM Config Integration**: Full end-to-end integration of per-tenant LLM provider configuration, allowing tenants to configure their own API keys for Gemini, Claude, and OpenAI via Settings.
- **NEXT_PUBLIC_* Env Var Cleanup**: Eliminated direct use of `NEXT_PUBLIC_BACKEND_URL` or `NEXT_PUBLIC_API_URL` in frontend, with all client-side API calls now going through `/api/backend-proxy/*` routes exclusively.
- **Pipeline Stage Maps**: Centralized icon/color mapping for pipeline stages in `plataforma-lia/src/lib/pipeline-stage-maps.ts` with dynamic fallback by action_behavior/stage_category and hash-based pool for custom stages. Includes status translation map (PT-BR). Internal/legacy stages grouped under "Outros" in pipeline overview proxy.
- **Pipeline Pulse**: Real-time pipeline stage counts displayed as badges below Workflow Reels nodes.
- **Voice Abstraction in LLM Factory**: Created `VoiceStreamProviderABC` abstraction with `NATIVE_MULTIMODAL` and `COMPOSITE_PIPELINE` strategies, supporting `GeminiLiveVoiceProvider`, `OpenAIRealtimeVoiceProvider`, and `CompositeVoiceProvider`.
- **TipTap Rich Text Editor Integration**: Replaced raw HTML textareas with TipTap WYSIWYG editor for email templates and job description editing, including a custom `TemplateVariable` TipTap extension.
- **SSE Fallback for Chat Streaming**: Added Server-Sent Events (SSE) as automatic fallback transport when WebSocket is unavailable (corporate proxies, firewalls). New `POST /api/v1/chat/{session_id}/stream` SSE endpoint. Frontend `useChatTransport` hook abstracts WS/SSE with automatic failover. Debug-only transport mode indicator (WS/SSE) in chat header. Shared `chat_event_serializer.py` ensures identical event format across both transports. `Last-Event-ID` header support for SSE reconnection.
- **CrewAI-Style Delegation on AgentBus**: Formal multi-agent delegation system built on top of AgentBus without importing CrewAI/AutoGen. Introduces `AgentCrew` (with declarative roles: leader/researcher/executor/reviewer), `CrewPlan` (DAG-based task sequencing with dependencies), `CrewContext` (shared Redis state with TTL and local cache fallback), and `CrewPlanExecutor` (orchestrates DAG execution with per-task timeouts, retries, and context mappings). AgentBus extended with request-reply pattern (correlation_id + dedicated reply channels). `CrewAuditService` logs every crew step to the audit trail. Feature flag `CREW_DELEGATION_ENABLED` gates the functionality (default: true). Fire-and-forget remains the default; crew-mode is opt-in. Files: `app/shared/agents/crew_*.py`, `agent_bus.py`.
- **TopBar Elimination & Sidebar User Panel**: Moved avatar dropdown (profile, password change, logout), notification bell, and HITL pending badge from the top bar to the sidebar footer. TopBar component eliminated from dashboard layout, freeing vertical space for chat. Notification panel redesigned with temporal grouping (Agora/Hoje/Ontem/Esta Semana), category filter icons, inline quick actions, polished empty state, and collision-aware portal positioning. Toast notifications via sonner for new notification arrivals with bell shake animation. Key files: `sidebar.tsx` (footer), `notification-system.tsx` (redesigned), `dashboard-app.tsx` (TopBar removed).
- **Agent Studio & Custom Agent Marketplace (Fase 4)**: Full custom agent system with CRUD, runtime sandbox (ReAct loop with tenant isolation via contextvars), marketplace (publish/review/install/uninstall), billing per execution, and CrewPlan integration. Models: `CustomAgent`, `AgentMarketplaceListing`, `AgentInstallation`. API: 3 routers (custom-agents, agent-marketplace, admin/agent-marketplace). Frontend: `CustomAgentsTab` and `MarketplaceTab` integrated into Agent Studio page. Key files: `lia-agent-system/libs/models/lia_models/custom_agent.py`, `app/api/v1/custom_agents.py`, `app/services/agent_marketplace_service.py`, `app/domains/agent_studio/custom_agent_runtime.py`, `plataforma-lia/src/components/pages-agent-studio/CustomAgentsTab.tsx`, `plataforma-lia/src/components/pages-agent-studio/MarketplaceTab.tsx`.
- **Agent Studio Stubs Activation + Metering/Billing (Fase 5)**: All Agent Studio stubs activated with real logic. Digital Twin domain connected to TwinInferenceService (RAG few-shot via pgvector) and TwinKnowledgeIndexer (audio transcription + decision extraction). Agent Studio `calibrate_agent` dispatches real SourcingAgentOrchestrator calibration, `get_agent_status` returns real metrics, `run_multi_strategy` executes 4 parallel search strategies. Recruitment Campaign domain persists campaigns with configurable stages and `advance_campaign` progresses through stages with auto-actions. **Metering separation**: `AiConsumption.agent_category` field distinguishes "core" vs "studio" usage. `AiConsumption.studio_agent_id` tracks per-agent consumption. **AgentQuota model**: Per-plan agent limits (Starter=1, Pro=5, Business=20, Enterprise=unlimited) with enforcement on creation. **StudioMeteringService**: Centralized service for recording studio usage, checking quotas, and providing consumption breakdown by agent type. **Studio consumption endpoint**: `get_studio_consumption` action returns breakdown by type (sourcing/custom/twin/campaign) with tokens, executions, and cost. New models: `AgentQuota`, `RecruitmentCampaign`. New service: `StudioMeteringService`. Key files: `lia-agent-system/libs/models/lia_models/agent_quota.py`, `lia-agent-system/libs/models/lia_models/recruitment_campaign.py`, `lia-agent-system/app/services/studio_metering_service.py`.
- **Talent Intelligence Domain**: New domain (`app/domains/talent_intelligence/`) implementing competitive capabilities: Skills Ontology Engine (graph-based taxonomy with 111 skills, 8 domains, 840 edges, adjacency traversal, gap analysis), Internal Mobility (match internal candidates via ontology-aware skill matching), Workforce Planning (forecast hiring needs from turnover/pipeline/growth data), Interview Intelligence (transcript analysis with sentiment, competency mapping, bias detection), and Passive Candidate Nurture (automated engagement sequences with templates). 10 new tools registered in `tool_registry_metadata.yaml` and `tool_permissions.yaml`.

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