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
- **LIA Toolbar Brain Button**: All toolbar LIA prompt inputs (candidates, jobs, kanban) have been replaced with a compact Brain icon button (`LIAToolbarBrainButton`) that opens the expanded LIA chat. The shared component lives at `src/components/ui/lia-toolbar-brain-button.tsx`.
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
- **WSI Saturation Intelligence**: Backend API and frontend components to manage and display candidate pipeline saturation for organic and sourcing pools.
- **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI screening with text and bidirectional audio support (TTS/STT).
- **Multi-Channel Communication Dispatcher**: `dispatch_message()` sends to ALL available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Voice Analysis Integration**: Deepgram STT + OpenAI TTS for triagem voice mode.
- **Microsoft Teams Notifications**: TeamsBot with adaptive cards for various notifications.
- **Apify Candidate Enrichment**: Enriches candidate profiles via LinkedIn and email discovery.
- **Gate 2 Re-Discovery Embedding**: Automatically generates Gemini embeddings for rejected candidates for future vector-similarity matching.
- **A/B Testing Email Templates**: Manages A/B testing for email templates with variant assignment, metric recording, and analysis.
- **Template Learning Integration**: Recommends best-performing templates based on open rates.
- **WRF Dynamic K Quality-Adaptive**: Enhances WRF with adaptive K computation based on match score distribution.
- **LLM Job Classification Filter**: Post-vector-search filter using Gemini Flash LLM to validate candidate-job compatibility.
- **FairnessGuard L3 Sector-Dependent**: Uses sector-specific rules for Layer 3 (LLM semantic) bias analysis.
- **Vue/Vuetify Standardization Skill**: `.agents/skills/vue-vuetify-standardize/SKILL.md` — 10-step workflow for standardizing Vue 3 + Vuetify 3 + Nuxt 3 components against DS v4.2.1. Covers token setup, hex tokenization, residual color cleanup, monolith split, React-Vue bridge, design audit, code review, 14-dimension audit, multi-agent workflow, and final validation. Adapts 5 existing skills (design-standardize, vue-migration-prep, frontend-design, feature-audit, design-patterns) for the Vue/Vuetify ecosystem.
- **Weekly Digest — Proactive Insights**: Aggregates data into a consolidated weekly report delivered via Teams, Chat, and Bell notifications.
- **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
- **FairnessGuard in Agent Outputs**: Integrated `FairnessGuard.check()` and `check_implicit_bias()` across various agent outputs to prevent bias.
- **LGPD Log Retention**: Implemented scheduled deletion for `ai_consumption` logs after 365 days.
- **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions.
- **Proactive Predictive Briefing**: LIA proactively presents a briefing with pipeline stats, candidate alerts, and ML predictions instead of a separate widget.
- **Polling Optimization**: Frontend polling intervals reduced to prevent 429 cascading.
- **SearchPresetsModal Unification (T004)**: 3 modal components (CompanyPresetsModal, LocationPresetsModal, UniversityPresetsModal) unified into a single generic `SearchPresetsModal<T>` component at `plataforma-lia/src/components/search/SearchPresetsModal.tsx`. Original files retained as thin wrappers preserving exact consumer APIs and preset data. Config-driven via `SearchPresetsModalConfig<T>` supporting custom tabs, localStorage, inline/footer save forms, and preview renderers.
- **Super Prompt Flutuante (LiaSuperPrompt)**: Expanding the mini chat opens a ~95% viewport overlay with tabs, dynamic contextual suggestions, and controls.
- **HTTP Chat Fallback**: When WebSocket is unavailable, floating LIA chat falls back to HTTP.
- **ReAct JSON Strip (`_strip_react_json`)**: Defense-in-depth against raw ReAct JSON leaking to users, extracting only the `response` field.
- **WSI Pipeline Unification (Fonte Única de Verdade)**: Reads screening questions exclusively from `job_screening_questions` DB table, with fallbacks and standardized nomenclature.
- **WSI Competency Minimums**: Minimum technical skills raised to 9 and behavioral competencies to 5, with pipeline adjustments and frontend warnings.
- **Design Token Migration (Tasks #95–#98 Complete)**: Full codebase migration from hardcoded Tailwind color classes (gray-*, slate-*, zinc-*, neutral-*) to semantic Design System LIA v4.2.1 tokens (CSS variables). Audit results — zero violations across all forbidden patterns: bg-gray/slate/zinc/neutral-*, text-gray/slate/zinc/neutral-*, border-gray/slate/zinc/neutral-*, bg-white, var(--gray-*), dark:lia-* malformed, hover:lia-* malformed, bare lia-text-NNN. Only intentional documentation comments retain gray-NNN references. Dev server starts and serves pages successfully (HTTP 200); pre-existing TypeScript issues in unrelated files (e.g., ai-credits dynamic import, candidate profile types) are outside migration scope.
- **Admin Audit & Streamlining (Task #100)**: Audited all 61 admin pages across 7 macro-areas. Decision: 30 MANTER, 22 REMOVER, 9 SIMPLIFICAR — reduced admin from 61 to 30 accessible pages (51% reduction). Key changes: removed Gestão de Riscos (5 pages), Trust Center from nav (3 pages), Monitoramento hub/dashboard (2 pages), Health Check, redundant Auditoria & Logs in Configurações, and advanced/premature client features (Workforce, Big Five, Automações, Testes Técnicos, Observabilidade). Added Guardrails IA and Consumo IA tab to client detail. Compliance reduced from 21 to 8 nav items. Decision doc: `plataforma-lia/docs/admin-audit-decision.md`. API contracts: `plataforma-lia/docs/admin-api-contracts.md`.
- **Infinite Loading Fix (R01)**: Removed `src/app/loading.tsx` which created an automatic Suspense boundary causing SSR streaming hydration failures on pages using `DashboardApp`. Also removed explicit `<Suspense>` from `src/app/page.tsx`. Fixed `tasks/page.tsx` `initialPage` from "Configurações" to "Painel de Controle". All 4 affected pages (`/`, `/configuracoes`, `/tasks`, `/funil`) now render correctly.
- **Chat handleSmartSearchCancel Fix (R02)**: Added missing `handleSmartSearchCancel` function in `src/components/pages/chat-page/useChatPageHandlers.tsx`.
- **CSP Avatar Images Fix (R03)**: Updated `next.config.js` CSP `img-src` to allow `i.pravatar.cc` and `randomuser.me`.
- **Security Audit Tasks #105-107**: (1) Removed hardcoded credentials, XSS, fake avatar URLs across 14+ files. (2) Auth migrated from localStorage to httpOnly cookies with JWT middleware and WorkOS SSO support. (3) API security: added Zod validation to 53 write routes (POST/PUT/PATCH/DELETE) using `validateBody`, `validateParams`, `validateQuery`, `validateFormData` helpers in `src/lib/api/validate.ts`; created domain schemas in `src/lib/schemas/proxy.schema.ts`; added file size limits (10-25MB) to FormData upload routes; added body size limits (2-5MB) to catch-all proxy routes; added HSTS (2yr preload) and X-XSS-Protection headers to `next.config.js`. Result: 0 unvalidated write routes (was 53), 314/427 total routes validated, all 7 security headers active.
- **Task #109 — @ts-ignore Cleanup**: Removed ~95 `@ts-ignore` across 7 files with proper type fixes. Created `DashboardCandidate` interface, `JobReportData` interface, typed `toolResults` casts, `SmartSearchInput` ComponentType cast.
- **Task #110 — Design System + Accessibility + Dead Code**: Verified `text-micro` on Badge is correct (DS v4.2.1 token = 0.625rem, intentional override of Badge base `text-xs`). Removed 7 `@ts-ignore` from `chart-components.tsx`, `success-prediction.tsx`, `KanbanJobHeader.tsx`. Deleted dead code: `chart-components.tsx` (0 imports), `success-prediction.tsx` (0 imports), empty `ml-analytics/` dir. Added `aria-label` to 3 icon-only buttons (stage-transition-actions-modal, PortalFieldRenderer 2x). Verified all `<img>` and `<Image>` tags already have alt text. Error boundary + error.tsx + not-found.tsx already exist at root level. 0 TypeScript errors.
- **WeDOTalent Diagnostic Guide**: Comprehensive comparison between React spec and Vue production code at `.agents/outputs/guia-completo-correcoes-wedotalent.md` (6 parts: screenshots, visual comparison, 8 bug fixes, 6 feature gaps, 7 backend fixes, sprint priorities).

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

# Audit & Comparison Documents
- `plataforma-lia/docs/audit-candidate-preview-qa.md` — Restructured QA audit (7 Parts): Part 1 Executive Summary, Part 2 Visual Bugs + Code Fixes (D01-D50), Part 3 Feature Gaps (G01-G16 + V01-V07), Part 4 Backend/API Bugs (B01-B10), Part 5 AI + Database (IA01-IA06, DB01-DB06), Part 6 Unified Sprint Priority Table (FIX-01 to FIX-31 + FIX-R01-R03), Part 7 Technical Reference. Includes Jira card template and Epic grouping.
- `.agents/outputs/guia-completo-correcoes-wedotalent.md` — Consolidated correction guide (6 parts + appendix R01-R03)