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
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1.
- **WSI Screening**: A 6-block (0-5) AI-powered methodology for comprehensive candidate evaluation.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and factual accuracy.
- **Job Creation Flow**: Supports both conversational ("Criar com a LIA") and manual entry ("Criar manualmente").
- **Kanban Candidate Movement System**: Features AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` and `PendingActionState` with LLM-powered smart parameter extraction.
- **Unified Tool Calling System**: Allows LIA to execute real actions with tenant scoping and persistent conversation memory.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **LangGraph Agent System**: All agents use LangGraph natively.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI screening with text and bidirectional audio support (TTS/STT).
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` with `RedisBroker` (default), `RabbitMQBroker`, and `PubSubBroker` for messaging.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API. Twilio serves as PSTN fallback.
- **Microsoft Teams Notifications**: TeamsBot provides adaptive cards for various notifications.
- **Apify Candidate Enrichment**: Enriches candidate profiles via LinkedIn and email discovery.
- **Gate 2 Re-Discovery Embedding**: Automatically generates Gemini embeddings for rejected candidates for future vector-similarity matching.
- **A/B Testing Email Templates**: Manages A/B testing for email templates with variant assignment, metric recording, and analysis.
- **Template Learning Integration**: Recommends best-performing templates based on open rates.
- **LLM Job Classification Filter**: Post-vector-search filter using Gemini Flash LLM to validate candidate-job compatibility.
- **FairnessGuard L3 Sector-Dependent**: Uses sector-specific rules for Layer 3 (LLM semantic) bias analysis.
- **Weekly Digest — Proactive Insights**: Aggregates data into a consolidated weekly report delivered via Teams, Chat, and Bell notifications.
- **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
- **FairnessGuard in Agent Outputs**: Integrated `FairnessGuard.check()` and `check_implicit_bias()` across various agent outputs to prevent bias.
- **LGPD Log Retention**: Implemented scheduled deletion for `ai_consumption` logs after 365 days.
- **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions.
- **Proactive Predictive Briefing**: LIA proactively presents a briefing with pipeline stats, candidate alerts, and ML predictions.
- **Split-Screen Dinâmico**: Dynamic contextual panel that opens to the right of the LIA float chat for context-specific visualizations (calibration, candidate_review, profile, job_creation, scheduling).
- **Super Prompt Flutuante (LiaSuperPrompt)**: Expanding the mini chat opens a ~95% viewport overlay with tabs, dynamic contextual suggestions, and controls.
- **HTTP Chat Fallback**: When WebSocket is unavailable, floating LIA chat falls back to HTTP.
- **ReAct JSON Strip**: Defense-in-depth against raw ReAct JSON leaking to users, extracting only the `response` field.
- **WSI Pipeline Unification**: Reads screening questions exclusively from `job_screening_questions` DB table, with fallbacks and standardized nomenclature.
- **Design Token Migration**: Full codebase migration from hardcoded Tailwind color classes to semantic Design System LIA v4.2.1 tokens.
- **Security Audit & Hardening**: Removed hardcoded credentials, migrated authentication to httpOnly cookies with JWT and WorkOS SSO, added API security measures, enforced `request.state.user_id` for critical endpoints, and implemented robust email provider chaining.
- **Profile Analysis BARS+WSI**: Enriched `AnalysisService` with unified BARS rubric evaluation + WSI Big Five trait inference from CV text.
- **Zustand State Management**: Introduced zustand for centralized state management, covering auth, kanban, and candidate data.
- **Performance Improvements**: Implemented lazy loading for modals and error boundaries for major pages.
- **Sentry Error Monitoring**: Activated Sentry integration for both backend and frontend.
- **WSI Threshold Alignment**: Unified all WSI approval/decision thresholds across the codebase.
- **Refinamento UX**: Mode Labels above prompt input, Switch Task modal (Cmd+K), Background Agents status panel, and inline completion notifications for background tasks.
- **Unified LIA Chat System**: Replaced fragmented chat systems with a single `LiaChatContext` for shared message store, persistent `conversation_id`, and a single backend communication channel.
- **Multi-Tenancy `company_id` Isolation**: Added `client_account_id` FK to `CompanyProfile` model, created tenant resolution endpoint, built centralized `useCompanyId` React hook, and replaced hardcoded `company_id`.
- **Reports & Predictions Real Data**: Frontend reports/predictions pages now fetch real data from backend endpoints.
- **Event Handlers + Post-Screening Automation**: Stage automation engine with registered handlers for automatic post-screening transitions and notifications.
- **ATS Integration Frontend-Backend Wiring**: Full ATS integration with Gupy, Pandapé, and Merge.dev. Includes security measures like SSRF allowlist and HMAC-SHA256 webhook signatures.
- **Mailgun Webhooks**: `POST /api/v1/webhooks/mailgun` endpoint with HMAC-SHA256 signature validation. Updates `CommunicationLog` status.
- **Credits Infrastructure**: `CreditAccount` and `CreditTransaction` models with `CreditService` for managing credit balance and transactions.
- **Interview Flow with Company Stages**: Added `recruitment_stage_id` FK to Interview model, allowing scheduling based on company-configured stages.
- **Chat Empty State Redesign**: Redesigned chat empty state with a centered Brain icon, LIA greeting, suggestion grid, and improved input area.
- **WSI Detailed Report (wsi-detailed-report.tsx)**: Full 3-tab detailed WSI report component (Respostas/Parecer/Ranking) integrated into `components/wsi/`. Opens from WSIScorecard's "Ver Relatório Completo" button. Shows competency responses with STAR analysis, Bloom/Dreyfus levels, gap analysis, executive summary, strengths/gaps, recommendation, and candidate feedback.
- **Weekly Digest Notifications**: 3 components in `components/notifications/` for delivering weekly recruitment summaries: `WeeklyDigestNotification` (bell dropdown), `WeeklyDigestChatMessage` (proactive chat message), `WeeklyDigestTeamsCard` (MS Teams adaptive card). All use shared `WeeklyDigestData` type.

# Deployment Configuration
- **Frontend Dockerfile**: `plataforma-lia/Dockerfile` — multi-stage build using `output: 'standalone'` (Node.js 22 Alpine)
- **next.config.js**: `output: 'standalone'`, rewrites use `BACKEND_URL` env var (defaults to `http://127.0.0.1:8001`)
- **Backend**: FastAPI on port 8001, started via uvicorn (`lia-agent-system/app/main.py`)
- **Environment variables**: See `plataforma-lia/.env.example` and `lia-agent-system/.env.example` for full list

# E2E Testing Status
- 20 Playwright test files in `plataforma-lia/e2e/tests/` (auth, chat, kanban, wizard, search)
- Playwright config at `plataforma-lia/playwright.config.ts`
- Chromium system libraries installed via Nix; config uses system Chromium automatically
- Auth fixture bypasses WorkOS by setting cookies directly (dev mode middleware skips JWT verification)
- Proven results: auth 6/6, kanban 6/7, wizard 12/13 — chat tests too heavy for Replit timeout
- Pendência: rodar suíte completa com WorkOS real em CI (GitHub Actions)

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

# Auth Flow (Dev Mode)
- **Auto-login**: Middleware calls `getDevToken()` which logs in via backend `/api/v1/auth/login` with demo credentials, caches the JWT token, and injects `Authorization: Bearer <token>` header into every non-public request
- **Cookies**: `lia_access_token` (httpOnly), `lia_refresh_token` (httpOnly), `lia_auth_method` (non-httpOnly, readable by JS)
- **Server-side user injection**: `layout.tsx` (async server component) calls `getServerUser()` which reads the `Authorization` header (set by middleware), fetches user data from backend `/api/v1/auth/me`, decodes JWT for `company_id`, and injects the result as `window.__INITIAL_USER__` via a `<script>` tag in the HTML
- **initAuth flow**: Reads `window.__INITIAL_USER__` first (instant, no fetch needed), falls back to `getMeDirect()` client-side fetch, then to JWT cookie-based auth
- **OnboardingController**: Shows spinner while `authIsLoading` OR `(authIsAuthenticated && !userData)`, prevents flash of "Acesso Restrito"
- **Important**: In dev mode with 5700+ modules, initial page load takes ~30-60s due to on-demand compilation; subsequent loads are fast

# Platform Audit (2026-04-07)
- **Full audit report**: `.local/audit/platform-audit-report.md`
- **Results**: 87% FUNCIONAL, 7% PARCIAL, 3% STUB, 3% AUSENTE
- **Backend**: 228 routers, 69 tools, all endpoints return 401 (auth enforced)
- **Frontend**: 30 pages, ~120 proxy routes, 15 Zustand stores
- **Top blockers for production**: WhatsApp Meta credentials, Pearch API key
- **Code gaps**: A/B testing UI, credit purchase system, Weekly Digest cron, i18n