# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system designed to optimize hiring processes. It utilizes a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology for comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to provide an intelligent, conversational, and data-driven platform with advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics. The project's vision is to revolutionize recruitment by offering a compliant, efficient, and intelligent solution that enhances hiring quality and reduces time-to-hire.

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
- **Intelligent Conversational Interface (LIA)**: The primary interaction model is chat-based for job creation and candidate screening, featuring intent classification, multi-step reasoning, and session persistence.
- **AI Stage Automation**: Employs a state machine for managing recruitment stages with smart transition automation.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1.
- **WSI Screening**: A 6-block (0-5) AI-powered methodology for comprehensive candidate evaluation.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and factual accuracy.
- **Job Creation Flow**: Supports both conversational ("Criar com a LIA") and manual entry ("Criar manualmente").
- **Kanban Candidate Movement System**: Features AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` and `PendingActionState` with LLM-powered smart parameter extraction.
- **Unified Learning System**: A central hub for learning operations, dynamic company catalogs, and an integrated learning loop.
- **Autonomous Agents System**: Manages background jobs and proactive LIA-initiated suggestions.
- **Unified Tool Calling System**: Allows LIA to execute real actions with tenant scoping and persistent conversation memory.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **ReAct Agent System**: Implements autonomous agents using ReAct loops across 7 distinct domains.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **WSI Saturation Intelligence**: Manages and displays candidate pipeline saturation for organic and sourcing pools.
- **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI screening with text and bidirectional audio support (TTS/STT). Features on-demand TTS per LIA message (speaker button), voice auto-play toggle in InputBar (localStorage-persisted), single "Iniciar Conversa" button (no separate voice mode entry). Phone call screening channel via OpenMic.ai — "Receber Ligação" button conditionally shown when recruiter enables phone channel in screening config; PhoneConfirmModal collects BR phone number and triggers automated call with 2-min cooldown rate limit.
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Voice Analysis Integration**: Uses Deepgram STT + OpenAI TTS for voice mode in triagem.
- **Microsoft Teams Notifications**: TeamsBot provides adaptive cards for various notifications.
- **Apify Candidate Enrichment**: Enriches candidate profiles via LinkedIn and email discovery.
- **Gate 2 Re-Discovery Embedding**: Automatically generates Gemini embeddings for rejected candidates for future vector-similarity matching.
- **A/B Testing Email Templates**: Manages A/B testing for email templates with variant assignment, metric recording, and analysis.
- **Template Learning Integration**: Recommends best-performing templates based on open rates.
- **WRF Dynamic K Quality-Adaptive**: Enhances WRF with adaptive K computation based on match score distribution.
- **LLM Job Classification Filter**: Post-vector-search filter using Gemini Flash LLM to validate candidate-job compatibility.
- **FairnessGuard L3 Sector-Dependent**: Uses sector-specific rules for Layer 3 (LLM semantic) bias analysis.
- **Vue/Vuetify Standardization Skill**: A 10-step workflow for standardizing Vue 3 + Vuetify 3 + Nuxt 3 components against DS v4.2.1.
- **Weekly Digest — Proactive Insights**: Aggregates data into a consolidated weekly report delivered via Teams, Chat, and Bell notifications.
- **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
- **FairnessGuard in Agent Outputs**: Integrated `FairnessGuard.check()` and `check_implicit_bias()` across various agent outputs to prevent bias.
- **LGPD Log Retention**: Implemented scheduled deletion for `ai_consumption` logs after 365 days.
- **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions.
- **Proactive Predictive Briefing**: LIA proactively presents a briefing with pipeline stats, candidate alerts, and ML predictions.
- **Polling Optimization**: Frontend polling intervals reduced to prevent 429 cascading.
- **SearchPresetsModal Unification (T004)**: Unifies multiple preset modals into a single generic `SearchPresetsModal<T>` component.
- **Super Prompt Flutuante (LiaSuperPrompt)**: Expanding the mini chat opens a ~95% viewport overlay with tabs, dynamic contextual suggestions, and controls.
- **HTTP Chat Fallback**: When WebSocket is unavailable, floating LIA chat falls back to HTTP.
- **ReAct JSON Strip (`_strip_react_json`)**: Defense-in-depth against raw ReAct JSON leaking to users, extracting only the `response` field.
- **WSI Pipeline Unification (Fonte Única de Verdade)**: Reads screening questions exclusively from `job_screening_questions` DB table, with fallbacks and standardized nomenclature.
- **WSI Competency Minimums**: Minimum technical skills raised to 9 and behavioral competencies to 5, with pipeline adjustments and frontend warnings.
- **Design Token Migration (Tasks #95–#98 Complete)**: Full codebase migration from hardcoded Tailwind color classes to semantic Design System LIA v4.2.1 tokens.
- **Admin Audit & Streamlining (Task #100)**: Reduced accessible admin pages from 61 to 30 (51% reduction) by removing redundant or premature features and consolidating sections.
- **Security Audit Tasks #105-107**: Removed hardcoded credentials, migrated authentication to httpOnly cookies with JWT and WorkOS SSO, and added API security measures including Zod validation, file/body size limits, HSTS, and X-XSS-Protection headers.
- **Zustand State Management (Task #116)**: Introduced zustand for centralized state management. Created `src/stores/auth-store.ts` (auth state), `src/stores/kanban-store.ts` (kanban view/candidates), `src/stores/candidates-store.ts` (search/candidates). Auth context now delegates to zustand store. Kanban and candidates hooks consume from stores for shared state (viewMode, selectedCandidates, candidatesData, etc.).
- **@ts-ignore Elimination (Quality Audit)**: Removed ALL 665 @ts-ignore comments from the entire frontend codebase (0 remaining). Fix patterns: String(value) for unknown→string, as Type assertions, optional chaining, proper callback typing, missing .map() index params, and variant prop casts.
- **God Components Split (Quality Audit)**: Split 45+ largest components into hooks + sub-components. Zero files >800L (was ~55). Top results: LiaChatPanel (1075→112L), useKanbanPageCore (990→452L), useExpandedChatModalCore (1001→65L), RecruitersTab (925→254L), DepartmentsTab (859→290L), onboarding-page (830→106L), tasks-page (821→131L), etc.
- **Performance: React.lazy + Error Boundaries**: Created ErrorBoundarySection and SuspenseFallback reusable components. Added lazy loading for 17+ modals. Wrapped 8 major pages with Error Boundaries. Settings tabs use next/dynamic.
- **localStorage → Zustand Migration (93%)**: 16 Zustand stores total (auth, kanban, candidates, onboarding, ui-preferences, job-ui, navigation, job-filters, talent-funnel, wizard, template, triagem, recent-items, table-features, chat-state). Migrated 259 of 278 localStorage usages to centralized stores (19 remaining: session-cleanup, auth-service, SearchPresetsModal prop interface).

# External Dependencies
- Anthropic (Claude API)
- WorkOS
- OpenMic.ai
- Google Gemini
- Pearch AI
- Deepgram
- Microsoft Graph
- Gupy ATS
- Pandapé ATS
- Merge
- HubSpot
- Stripe
- Apify
- SendGrid
- Mailgun
- PostgreSQL
- Redis
- Elasticsearch