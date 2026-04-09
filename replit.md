# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system designed to optimize hiring processes. It uses a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology for comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to provide an intelligent, conversational, and data-driven platform with advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics. The project's vision is to revolutionize recruitment by offering a compliant, efficient, and intelligent solution that enhances hiring quality and reduces time-to-hire.

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
The platform's frontend uses Next.js, React, and TypeScript with Radix UI, shadcn/ui, and Tailwind CSS. The backend is built with FastAPI (Python) and PostgreSQL. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation.
- **Intelligent Conversational Interface (LIA)**: Primary interaction model is chat-based for job creation and candidate screening, featuring intent classification, multi-step reasoning, and session persistence.
- **AI Stage Automation**: Employs a state machine for managing recruitment stages with smart transition automation.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1. Dynamic split-screen panels and a floating Super Prompt enhance user interaction.
- **WSI Screening**: A 6-block (0-5) AI-powered methodology for comprehensive candidate evaluation, including a detailed report with STAR analysis, Bloom/Dreyfus levels, gap analysis, and recommendations.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and factual accuracy. FairnessGuard L3 uses sector-specific rules for LLM semantic bias analysis. LGPD requires scheduled deletion for `ai_consumption` logs after 365 days.
- **Job Creation Flow**: Supports both conversational ("Criar com a LIA") and manual entry ("Criar manualmente").
- **Kanban Candidate Movement System**: Features AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` and `PendingActionState` with LLM-powered smart parameter extraction. Unified tool calling system allows LIA to execute real actions with tenant scoping and persistent conversation memory.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring. Includes a post-vector-search filter using Gemini Flash LLM for candidate-job compatibility.
- **LangGraph Agent System**: All agents use LangGraph natively.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI screening with text and bidirectional audio support (TTS/STT).
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` with `RedisBroker` (default), `RabbitMQBroker`, and `PubSubBroker` for messaging.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API. Twilio serves as PSTN fallback.
- **Microsoft Teams Notifications**: TeamsBot provides adaptive cards for various notifications, including weekly digests.
- **Apify Candidate Enrichment**: Enriches candidate profiles via LinkedIn and email discovery.
- **Gate 2 Re-Discovery Embedding**: Automatically generates Gemini embeddings for rejected candidates for future vector-similarity matching.
- **A/B Testing Email Templates**: Manages A/B testing for email templates with variant assignment, metric recording, and analysis, and integrates template learning for recommendations.
- **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
- **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions.
- **Proactive Predictive Briefing**: LIA proactively presents a briefing with pipeline stats, candidate alerts, and ML predictions.
- **Security Audit & Hardening**: Authentication uses httpOnly cookies with JWT and WorkOS SSO. API security measures include enforced `request.state.user_id` for critical endpoints and robust email provider chaining. ATS integration includes SSRF allowlist and HMAC-SHA256 webhook signatures.
- **Profile Analysis BARS+WSI**: Enriched `AnalysisService` with unified BARS rubric evaluation + WSI Big Five trait inference from CV text.
- **Zustand State Management**: Introduced zustand for centralized state management, covering auth, kanban, and candidate data.
- **Performance Improvements**: Implemented lazy loading for modals and error boundaries for major pages.
- **Sentry Error Monitoring**: Activated Sentry integration for both backend and frontend.
- **Unified LIA Chat System**: Replaced fragmented chat systems with a single `LiaChatContext` for shared message store, persistent `conversation_id`, and a single backend communication channel. HTTP Chat Fallback for WebSocket unavailability.
- **Multi-Tenancy `company_id` Isolation**: Implemented `client_account_id` FK in `CompanyProfile`, tenant resolution endpoint, `useCompanyId` React hook, and `useCurrentCompany` hook. User management uses `tenantId`.
- **Reports & Predictions Real Data**: Frontend reports/predictions pages now fetch real data from backend endpoints.
- **ATS Integration**: Full ATS integration with Gupy, Pandapé, and Merge.dev.
- **Credits Infrastructure**: `CreditAccount` and `CreditTransaction` models with `CreditService` for managing credit balance and transactions.
- **Interview Flow with Company Stages**: Added `recruitment_stage_id` FK to Interview model, allowing scheduling based on company-configured stages.
- **Rails→FastAPI Frontend Migration (Task #91)**: All 94 frontend proxy route files migrated from `backendTarget: "rails"` to `"fastapi"`. Zero Rails references remain. New endpoint `GET /api/v1/email-templates/categories/list` created (returns 14 distinct categories). FastAPI is now the sole backend for all frontend routes. Rails (`ats-api-copia`) remains available as opt-in bridge for legacy data (Decision C).
- **Choose Your AI — LLM Config Integration (Task #94)**: Full end-to-end integration of per-tenant LLM provider configuration. Tenants can configure their own API keys for Gemini, Claude, and OpenAI via Settings → Integrations → AI Models. Keys are encrypted at-rest with Fernet. Backend uses `llm_config_router` at `/api/v1/admin/llm-config` with merge semantics to preserve existing keys when updating. ProviderContainer supports tenant-specific API keys with fallback to system keys. Persistent audit trail via SOXAuditLog. Frontend IntegrationDetailDrawer has Test Connection + Save buttons with real-time feedback and password toggle. Proxy routes: `/api/backend-proxy/llm-config` (GET+PUT), `/test` (POST), `/providers` (GET).

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
- SendGrid
- Mailgun
- Resend (email fallback)
- PostgreSQL
- Redis
- Elasticsearch
- Sentry (error monitoring)
- OpenAI (Whisper, TTS — PSTN fallback only)
- Twilio (Voice — PSTN fallback only)
- Deepgram (STT/transcrição de voz)
- Celery