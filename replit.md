# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system that optimizes hiring processes. It uses a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology to assess candidates' technical, behavioral, and cultural fit. LIA aims to provide an intelligent, conversational, and data-driven platform with advanced AI capabilities, psychometrics, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics. The project's ambition is to revolutionize recruitment by offering a comprehensive, compliant, and efficient solution that enhances hiring quality and reduces time-to-hire.

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
The platform's frontend is built with Next.js, React, and TypeScript, leveraging Radix UI, shadcn/ui, and Tailwind CSS for UI components. The backend is implemented using FastAPI (Python) and PostgreSQL for data persistence. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
-   **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology.
-   **Intelligent Conversational Interface (LIA)**: The primary interaction model is "Chat as primary interface" for job creation and candidate screening, featuring intent classification, multi-step reasoning, and session persistence.
-   **AI Stage Automation**: Employs a state machine for managing recruitment stages with "Smart Transition Automation".
-   **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1.
-   **WSI Screening**: A 7-block AI-powered methodology for comprehensive candidate evaluation.
-   **Semantic Search**: AI-powered search functionality, enhanced with Redis caching.
-   **Intelligent Interview Notes System**: Integrates WSI for dual rating and AI-generated questions.
-   **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and factual accuracy, including logging, data retention, and PII masking.
-   **Job Creation Flow (MVP)**: Two-option entry point via `CreateJobModal` — "Criar com a LIA" (conversational wizard via `ExpandedChatModal`) or "Criar manualmente" (quick form → `POST /job-vacancies` with status "Rascunho"). Manual creation redirects to `JobEditTab` in creation mode (`isCreationMode=true`) with amber banner, all sections editable, and "Publicar Vaga" button. Publishing calls `generatePublicLink` + status update to "Ativa", shows success dialog with copyable public link. The "Link de Candidatura" section in info-geral shows the public URL when published. Key files: `create-job-modal.tsx`, `JobEditTab.tsx`, `job-kanban-page.tsx`.
-   **Job Creation Wizard (LIA)**: A streamlined, conversational process with structured field typology, confidence policies, skill catalog integration, and an intelligence layer.
-   **Kanban Candidate Movement System**: Features AI-powered sub-status prediction and WSI score integration.
-   **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
-   **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` and `PendingActionState` with LLM-powered smart parameter extraction.
-   **Unified Learning System**: A central hub for learning operations, dynamic company catalogs, and an integrated learning loop.
-   **Feature Flags System**: Provides granular control over platform functionality for A/B testing.
-   **Autonomous Agents System**: Manages background jobs and proactive LIA-initiated suggestions.
-   **Multi-modal Analysis System**: Supports analysis of video, image, and documents using advanced AI models.
-   **Unified Tool Calling System**: Allows LIA to execute real actions with tenant scoping.
-   **Persistent Conversation Memory**: Maintains context across sessions through LLM-generated summaries.
-   **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
-   **ReAct Agent System**: Implements autonomous agents using ReAct loops across 7 distinct domains.
-   **WeDO Talent Guide v3.3 Integration**: Incorporates governance skills defining production readiness, screening methodology, DEI principles, and compliance frameworks.
-   **Long-Term Memory System**: Utilizes `LongTermMemoryService` with PostgreSQL-backed cross-session memory persistence.
-   **Agent Explainability System**: `ExecutionLogStore` persists full reasoning chains for auditing agent decisions.
-   **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
-   **WSI Saturation Intelligence**: Backend API and frontend components to manage and display candidate pipeline saturation. Separate pools for organic (web/whatsapp) and sourcing (sourcing/ats) with independent thresholds. Settings UI in Configurações → Pipeline → Triagem card. `GET/PUT /api/v1/settings/saturation` for company-level defaults. `saturation-status` endpoint returns pool-separated counts. Unlock pipeline updates both pool thresholds. Origin badges on kanban cards (Web/WhatsApp/Busca/ATS + Aguardando). SaturationBadge shows "org | src" pools with dynamic values.
-   **Pipeline Layer 2 (AI/LLM)**: Full AI integration for pipeline transitions, including batch rejection.
-   **Multi-Channel Communication**: Uses a `ChannelAdapter` abstract interface and `ChannelRouter` for intelligent message routing.
-   **Async Task Processing at Scale**: Employs PostgreSQL-backed models and services for robust background task management, integrated with Celery.
-   **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
-   **FairnessGuard in Agent Outputs**: Integrated `FairnessGuard.check()` and `check_implicit_bias()` across various agent outputs to prevent bias and ensure fairness.
-   **LGPD Log Retention (L6)**: Implemented scheduled deletion for `ai_consumption` logs after 365 days.
-   **Google Calendar Integration**: Provides `GoogleCalendarClient` for event management, availability checks, and scheduling.
-   **Red Teaming**: Formalized red teaming tests for bias elicitation, prompt injection, jailbreak, score manipulation, data exfiltration, and privilege escalation.
-   **Compliance Diagnostic (Deep)**: Comprehensive 136-gap analysis across 4 dimensions (IA/Agents, LGPD, Audit, Fairness/DEI). Covers LGPD, EU AI Act, PL 2338/2023, NYC LL144, BCB-498, SOX, SOC-2, ISO 42001 compliance. 4-phase remediation roadmap. Benchmark vs Eightfold, Gupy, HireVue, Paradox, Greenhouse, Findem. Output: `docs/DIAGNOSTICO_COMPLIANCE_IA_COMPLETO.md` (documento único consolidado com ~1880 linhas).
-   **Token Tracking**: Implemented tracking of token usage for cost analysis and resource management.
-   **Orchestrator LLM Fallback for Technical Responses**: Added `_is_technical_response()` detection and automatic LLM fallback in `orchestrator.py` to rewrite technical responses into natural conversational output.
-   **LiaChatPanel REST API**: Chat panel uses `POST /api/backend-proxy/chat` (REST) instead of WebSocket for reliable communication.
-   **AUD Jira Cards (Auditoria Agente Python)**: 7 cards (WT-1506 to WT-1512) + Epic WT-1505 created for the dev team to implement audit/compliance fixes in the Python agent (V5). Cards are agent-ready with full LIA code references, snippets, and implementation steps. Diagnostic doc: `docs/diagnostico-auditoria-agente-python.md`.
-   **Roadmap MVP Alpha 1 — Cards Unificados v5.1**: Documento `docs/roadmap-mvp-alpha1-cards-unificados.md`. v5.0 adiciona 15 seções globais de referência IA. v5.1 adiciona §11 — É35 Arquitetura de IA (AGT): 21 cards completos em YAML enriquecido cobrindo agentes Python (LangGraph/LangChain), orquestrador, serviços IA, infra compartilhada, automações Celery, HITL e frontend. Épico Jira WT-1558, cards WT-1559→WT-1579. Stack: Claude Sonnet + OpenAI/Gemini fallback, PostgresSaver, Redis, PGVector, Celery Beat. Total: 65 cards · 413 SPs (44 funcionalidade + 21 arquitetura IA, 8 épicos).
-   **Four-Fifths Rule + Golden Dataset**: Established a baseline for bias auditing using a golden dataset and the Four-Fifths Rule to detect adverse impact.
-   **Model Drift Detection Service**: Monitors and alerts on score, approval, cost, and latency drift in AI models.
-   **Anti-sycophancy / Sector Benchmark Service**: Injects sector-specific benchmarks into prompts to prevent AI sycophancy.
-   **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions for specific jobs, with API endpoints for reporting.
-   **ShareSearchModal Redesign**: Two-column layout with 3-way channel toggle, recipients, template selector, editable subject, message textarea, and real-time preview.
-   **"Ambos" (Both) Channel — All Modals**: 7 modals across the platform now support `channel: 'both'` for simultaneous email + WhatsApp delivery.
-   **Kanban Screening Approve/Reject Fix**: Updated flows for approving and rejecting candidates in the Triagem (screening) column to use `UniversalTransitionModal` with LIA chat suggestions for scheduling or rejection reasons.
-   **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI triagem. Route: `/triagem/[token]`. Standalone layout (no app navigation). Full end-to-end flow: invite dispatch → candidate opens link → chat with LIA (text + audio) → confirmation → completion → post-automation (email, recruiter notification, pipeline auto-move). Backend: `TriagemSession` + `TriagemMessage` SQLAlchemy models, `triagem_session_service.py` with 7-block WSI flow, 6 REST endpoints. Frontend: `use-triagem-chat.ts` hook (Vue migration prep), 10 DS v4.2.1 components, snake_case→camelCase mapping, XSS-safe markdown rendering. Bidirectional voice support: TTS (OpenAI tts-1) auto-plays LIA responses in voice mode, STT (Deepgram/Whisper) for candidate audio input. AudioPlayer component for playback with speaking animation. Voice UI controls: "Iniciar Conversa por Voz" button, mute/unmute toggle, "Finalizar Conversa" button. Voice mode state propagated correctly through all message requests. Key files: `plataforma-lia/src/app/triagem/[token]/page.tsx`, `plataforma-lia/src/hooks/use-triagem-chat.ts`, `plataforma-lia/src/components/triagem/`, `plataforma-lia/src/components/ui/audio-player.tsx`, `lia-agent-system/app/api/v1/triagem.py`, `lia-agent-system/app/services/triagem_session_service.py`, `lia-agent-system/libs/models/lia_models/triagem.py`.
-   **SAT-005 Queue Auto-Promotion**: When a candidate is rejected (via `handle_candidate_rejected` or `handle_stage_changed`), `process_screening_queue(max_promote=1)` is automatically called to promote the next queued candidate from `awaiting_screening`. Key file: `lia-agent-system/app/domains/automation/services/automation_handlers.py`.
-   **SAT-006 Override Approve Button**: Recruiters can manually approve candidates from the saturation queue directly on Kanban cards. Component: `OverrideApproveButton` with inline confirmation (Sim/Não). Hook: `use-override-approve.ts`. Proxy: `POST /api/backend-proxy/candidates/[id]/screening-decision`. Backend: `POST /api/v1/candidates/{id}/screening-decision` with `decision: "approved"`. DS v4.2.1 compliant (bg-gray-900, rounded-md, dark mode). Key files: `plataforma-lia/src/components/kanban/components/OverrideApproveButton.tsx`, `plataforma-lia/src/hooks/use-override-approve.ts`, `plataforma-lia/src/components/pages/job-kanban-page.tsx`.
-   **Multi-Channel Communication Dispatcher**: `dispatch_message()` sends to ALL available channels (email + WhatsApp) by default (`multi_channel=True`); single-channel mode still available. Key file: `lia-agent-system/app/domains/communication/services/communication_dispatcher.py`.
-   **Web Application Form**: Public vacancy page (`/vagas/[slug]`) includes "Candidatar-se Online" form with fields: Nome, Email, Telefone, CV upload, LGPD consent. Backend: `POST /api/v1/public-vacancies/p/{slug}/apply`. Key files: `plataforma-lia/src/app/vagas/[slug]/page.tsx`.

# External Dependencies
-   Anthropic (Claude API)
-   WorkOS
-   OpenMic.ai
-   Google Gemini
-   Pearch AI
-   Deepgram
-   Microsoft Graph
-   Gupy ATS
-   Pandapé ATS
-   Merge
-   HubSpot
-   Stripe
-   Mailgun
-   PostgreSQL
-   Redis
-   Elasticsearch