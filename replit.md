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
-   **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation.
-   **Intelligent Conversational Interface (LIA)**: The primary interaction model is chat-based for job creation and candidate screening, featuring intent classification, multi-step reasoning, and session persistence.
-   **AI Stage Automation**: Employs a state machine for managing recruitment stages with smart transition automation.
-   **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1.
-   **WSI Screening**: A 6-block (0-5) AI-powered methodology for comprehensive candidate evaluation, covering approach, presentation, company fit (including eligibility), technical skills, behavioral/cultural fit, and closing.
-   **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and factual accuracy, including logging, data retention, and PII masking.
-   **Job Creation Flow**: Supports both conversational ("Criar com a LIA") and manual entry ("Criar manualmente") with an `ExpandedChatModal` for the conversational wizard and `JobEditTab` for manual editing.
-   **Kanban Candidate Movement System**: Features AI-powered sub-status prediction and WSI score integration.
-   **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
-   **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` and `PendingActionState` with LLM-powered smart parameter extraction.
-   **Unified Learning System**: A central hub for learning operations, dynamic company catalogs, and an integrated learning loop.
-   **Autonomous Agents System**: Manages background jobs and proactive LIA-initiated suggestions.
-   **Unified Tool Calling System**: Allows LIA to execute real actions with tenant scoping and persistent conversation memory.
-   **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
-   **ReAct Agent System**: Implements autonomous agents using ReAct loops across 7 distinct domains.
-   **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
-   **WSI Saturation Intelligence**: Backend API and frontend components to manage and display candidate pipeline saturation for organic and sourcing pools.
-   **PUB-001 Public Triagem Chat Page**: Public candidate-facing chat web page for WSI screening with text and bidirectional audio support (TTS/STT).
-   **Multi-Channel Communication Dispatcher**: `dispatch_message()` sends to ALL available channels (email + WhatsApp) by default.
-   **Celery Scheduler & Automations (Task #70)**: Background automations via Celery Beat — `followup.process_pending` (7-day email follow-up for WSI invites), `wsi.check_abandoned` (48h/96h timeout reminders), `feedback.auto_send` (auto-send approved rejection feedback via email/WhatsApp), `feedback.process_pending_sends` (safety net batch), SendGrid Event Webhook (`POST /email-tracking/webhook`), and Template Learning stub service (`template_learning_service`) with open-rate recommendation.
-   **Voice Analysis Integration (Task #71)**: Deepgram STT + OpenAI TTS for triagem voice mode. Domain services: `cv_screening/services/deepgram_service.py` (DeepgramTriagemService) and `cv_screening/services/voice_service.py` (TriagemVoiceService). API endpoints: `POST /triagem/{token}/audio` (audio transcription), `POST /triagem/{token}/tts` (speech synthesis), `GET /triagem/{token}/voice-status` (availability check). Delegates to shared `VoiceService` with triagem-specific defaults (pt-BR, nova-2).
-   **Microsoft Teams Notifications (Task #71)**: TeamsBot with lazy initialization (no crash when credentials absent). Event dispatchers: `notify_triagem_completed()`, `notify_scheduling_confirmed()`, `notify_candidate_timeout()`. Each generates dedicated Adaptive Cards with facts/actions. Notification types also available via `send_notification()` with type string.
-   **Apify Candidate Enrichment (Task #71)**: `ApifyService.enrich_candidate_profile()` enriches candidates via LinkedIn person scraper (`anchor/linkedin-profile-scraper`) and email discovery (`curious_coder/email-finder`). Sourcing tool `enrich_candidate_profile` registered for `talent-search` and `profile-analysis` stages.
-   **Gate 2 Re-Discovery Embedding (Task #71)**: `reject_candidate()` automatically generates a Gemini 768-dim embedding via `JobEmbeddingService` for rejected candidates. Embedding stored with `outcome_status=rejected_gate2` for future vector-similarity matching against new vacancies.
-   **A/B Testing Email Templates (Task #72)**: Seeded 3 A/B test experiments at startup (screening invite, follow-up reminder, rejection feedback) with control + treatment variants (50/50 split). `ABTestingService` in `shared/learning/ab_testing_service.py` handles variant assignment (hash-based), metric recording, and statistical significance analysis (z-score, p-value, 95% CI). API: `GET/POST /api/v1/ab-tests`, `POST /{test_name}/record`, `GET /{test_name}/results`. Email dispatch in `communication_service.send_templated_message()` now looks up A/B variant for the candidate.
-   **Template Learning Integration (Task #72)**: `TemplateLearningService.recommend_template()` wired into `send_templated_message()`. Queries `message_queue` + `email_tracking_events` to find the best-performing template per company (by open rate). Records sends automatically via `template_learning_service.record_send()` on successful dispatch. Falls back gracefully to situation-based template lookup when no learning data is available.
-   **WRF Dynamic K Quality-Adaptive (Task #72)**: `WRFDynamicKService` enhanced with `compute_adaptive_k()` that analyzes match score distribution. High top-score cluster → reduces K by 30% (precision). Low top-score → increases K by 40% (recall). Tight score spread → reduces K by 10. Controlled by `WRF_ADAPTIVE_K` env var (default: true). Bounds: K ∈ [10, 100]. Domain `wrf_service.py` consolidated as re-export from canonical `services/wrf_dynamic_k_service.py`.
-   **LLM Job Classification Filter (Task #72)**: `LLMJobClassificationService` in `sourcing/services/llm_job_classification_service.py`. Post-vector-search filter that validates candidate-job compatibility using Gemini Flash LLM. Removes fundamentally incompatible candidates (e.g., Java dev matched against neurosurgeon). Heuristic fallback with `INCOMPATIBLE_AREAS` area detection when LLM is unavailable. Wired into `rag_pipeline_service.py` after WRF re-ranking.
-   **FairnessGuard L3 Sector-Dependent (Task #72)**: `FairnessGuard.check_with_sector()` method uses `ALPHA1_SECTOR_RULES` from `policy_engine_service.py` to determine if Layer 3 (LLM semantic) analysis is enabled per sector. Sectors with L3 enabled: tech, financeiro, saude, rpo. Sectors without L3: varejo, logistica. Sector-specific context injected into LLM prompt (e.g., tech → "atenção a vieses de gênero em cargos técnicos, etarismo").
-   **Weekly Digest — Proactive Insights (Task #78)**: `WeeklyDigestService` aggregates PredictiveAnalytics, FairnessGuard, ABTesting, and LearningLoop data into a consolidated weekly report. Delivered every Monday at 08h BRT via Teams (Adaptive Card), Chat (proactive markdown), and Bell notification. `DigestFormatter` uses Strategy pattern: `TeamsDigestFormatter`, `ChatDigestFormatter`, `BellDigestFormatter`. Celery beat schedule `digest-weekly` (Monday 11h UTC). API: `GET/POST /api/v1/digest/weekly/preview|send|send-all`, `GET/PUT /api/v1/digest/weekly/preferences`. Frontend opt-out toggle in Settings > Comunicação & Alertas > Alertas tab ("Resumo Semanal" card). Opt-out stored in `user.notification_preferences.weekly_report_enabled`.
-   **Production Readiness**: Includes a unified health endpoint, `RequestIdMiddleware` for distributed tracing, structured JSON logging, global exception handlers, auth protection, and rate limiting middleware.
-   **FairnessGuard in Agent Outputs**: Integrated `FairnessGuard.check()` and `check_implicit_bias()` across various agent outputs to prevent bias and ensure fairness.
-   **LGPD Log Retention (L6)**: Implemented scheduled deletion for `ai_consumption` logs after 365 days.
-   **BiasAuditService + API**: Calculates adverse impact using the Four-Fifths Rule across demographic dimensions for specific jobs, with API endpoints for reporting.
-   **Proactive Predictive Briefing**: When entering a job, LIA proactively presents a briefing with pipeline stats, candidate alerts, and ML predictions (time-to-fill, salary range) instead of a separate MLInsightsCard widget. All AI interaction flows through LIA chat.
-   **Polling Optimization**: Frontend polling intervals reduced to prevent 429 cascading — ai-suggestions 60s, notifications 60s, setup-progress 120s.
-   **Super Prompt Flutuante (LiaSuperPrompt)**: Expanding the mini chat opens a ~95% viewport overlay instead of redirecting to `/chat`. Features tabs (Conversa/Centro de Controle), dynamic contextual suggestions (reads from `localStorage` key `lia-recruiter-context` with fallback to static suggestions), inline vs redirect action logic, and minimize/close controls. State managed via `LiaFloatContext` with `isExpanded`/`expand()`/`collapse()`/`closeAll()`. Component: `LiaSuperPrompt.tsx`, hook: `useDynamicSuggestions.ts`.
-   **HTTP Chat Fallback**: When WebSocket is unavailable (e.g., Replit proxy), floating LIA chat falls back to HTTP via `POST /chat/message` endpoint. Backend: `agent_chat_ws.py` (same auth, budget, token tracking as WS). Frontend: `use-float-streaming.ts` detects `isConnected=false` and calls `/api/backend-proxy/chat/message`. Next.js proxy at `src/app/api/backend-proxy/chat/message/route.ts` forwards with auth headers.
-   **ReAct JSON Strip (`_strip_react_json`)**: Defense-in-depth against raw ReAct JSON leaking to users. Applied at 2 layers: (1) API layer in `agent_chat_ws.py` — WS handler, HTTP fallback, and HITL resume paths; (2) Agent layer in `langgraph_react_base.py` `_extract_text_content()`. Detects `{"thought":..., "response":...}` format (plain or fenced in ```json blocks), extracts only the `response` field. Falls back to safe message when `response` is empty.
-   **WSI Pipeline Unification (Fonte Única de Verdade)**: `wsi_interview_graph.py` `load_context()` reads screening questions exclusively from `job_screening_questions` DB table (saved by recruiter in Configurações da Vaga > Perguntas de Triagem). Falls back to `WSIScreeningPipeline` with WARNING log if no saved questions exist. Question source is logged (`saved_db` / `fallback_pipeline` / `hardcoded_fallback`). Modes: compact=7 questions, full=12 questions (seniority-adaptive distributions). Duplicate generation path removed from `JDEvaluationPanel` — `onGenerateQuestions` now redirects to the "perguntas" section. Nomenclature standardized: `compact_plus` → `full` across `wsi_service.py` and `wsi_screening_pipeline.py`.
-   **WSI Competency Minimums (Task #43)**: Minimum technical skills raised to 9 (from 3) in enrichment service and quality gates; minimum behavioral competencies raised to 5 (from 3). Pipeline handles insufficient skills by requesting more questions per available skill. Behavioral block uses Big Five traits as fallback when no behavioral competencies provided. Frontend shows amber warning in ScreeningConfigManager when skills are below recommended minimums, and disables Full mode when < 5 technical skills. Wizard system prompt updated to guide recruiter toward collecting at least 9 technical skills with decomposition suggestions. Document WSI_METHODOLOGY_COMPLETE_v2.md updated with new minimums, decomposition rules, and F1.C→F2 flow explanation.

# Skills de Desenvolvimento
16 skills organizadas por fase de trabalho. Ver guia completo em `.agents/skills/SKILLS_INDEX.md`.
- **Antes de codificar:** lia-planning (unifica GSD + spec-driven + brainstorming), feature-impact
- **Design/UI:** frontend-design, design-standardize, design-patterns (inclui composition patterns)
- **Implementacao:** lia-testing (unifica TDD + piramide + evals IA), vue-migration-prep
- **Validacao:** feature-audit, browser-use
- **Compliance:** lia-compliance (unifica governanca + screening + DEI + LGPD)
- **Utilitarias:** humanizer, pdf, pptx, agent-tools, find-skills, skill-creator

# Architecture Diagrams
- `docs/diagrams/architecture-transversal-unified.html` — Unified transversal architecture diagram (HTML). Shows v5 vs LIA side-by-side with transversal compliance bands crossing all 8 domains, coverage matrix (24 dim × 8 domains), 23 compliance concerns (C01-C23), Hub 13 components, dual pipelines, 3 architectural groups. Published at `/diagram-transversal.html`.
- `docs/diagrams/recruiter-agent-v5-architecture.excalidraw` — Combined Excalidraw (1022 elements). v5 transversal layout (717 elements: hub, groups, coverage matrix, concerns, pipelines) + LIA side (305 elements). Open at excalidraw.com.
- `docs/diagrams/recruiter-agent-v5-architecture-detailed.html` — v5 detailed HTML (10 layers). Published at `/diagram-v5-detailed.html`.
- `docs/diagrams/lia-ai-architecture-detailed.html` — LIA detailed HTML (10 layers). Published at `/diagram-lia-detailed.html`.
- `docs/diagrams/lia-ai-architecture.excalidraw` — Original LIA-only architecture diagram.

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
-   Apify
-   SendGrid
-   Mailgun
-   PostgreSQL
-   Redis
-   Elasticsearch