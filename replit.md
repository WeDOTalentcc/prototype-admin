# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system designed to optimize hiring processes. It leverages a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology to provide comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to revolutionize recruitment by offering advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics, ensuring an efficient, compliant, and intelligent solution that improves hiring quality and reduces time-to-hire.

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
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation and supports a custom agent marketplace with metering and billing.
- **Intelligent Conversational Interface (LIA)**: The primary interaction is chat-based, supporting multi-step reasoning, intent classification, and session persistence. It includes a unified chat system with WebSocket and SSE fallback.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1. Dynamic split-screen panels and a floating Super Prompt enhance user interaction.
- **WSI Screening**: A 6-block AI-powered methodology for comprehensive candidate evaluation, generating detailed reports with STAR analysis, Bloom/Dreyfus levels, gap analysis, and recommendations. Includes a public candidate-facing chat page for WSI screening with text and bidirectional audio support.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection. Includes a `BiasAuditService` to calculate adverse impact.
- **Job Creation & Candidate Management**: Supports conversational and manual job creation, with a Kanban candidate movement system featuring AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` with LLM-powered smart parameter extraction.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` for messaging with `RedisBroker`, `RabbitMQBroker`, and `PubSubBroker` implementations.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API with Twilio as PSTN fallback.
- **Security & Production Readiness**: Includes robust authentication with httpOnly cookies, JWT, and WorkOS SSO, API security measures, unified health endpoint, structured logging, and global exception handlers. Per-request cost tracking with budget alerts.
- **Talent Intelligence Domain**: Implements competitive capabilities such as a Skills Ontology Engine, Internal Mobility matching, Workforce Planning, Interview Intelligence (transcript analysis + Gemini transcription service), and Passive Candidate Nurture. These are part of monetizable modules with module-aware tool gating.
- **Interview Intelligence Infrastructure**: Full interview lifecycle with Microsoft Calendar integration, dedicated transcript/transcript_language/transcript_source columns on Interview model, Gemini-based audio/video transcription service (`app/domains/interview_intelligence/services/transcription_service.py`), background transcription via PATCH `/interviews/{id}/recording`, POST `/interviews/{id}/transcribe`, GET `/interviews/{id}/transcript`. Teams transcription also populates the dedicated columns. Migration 067 adds the new columns.
- **Interview Intelligence Pro (Premium Module)**: 5 services in `app/domains/interview_intelligence/services/`: (1) InterviewWSIService — WSI methodology on transcripts (Bloom/Dreyfus/CBI/Big Five), (2) BiasDetectorService — dual-layer bias detection (regex + LLM), (3) ComparativeAnalysisService — candidate ranking vs vacancy peers, (4) StrategicOpinionService — LLM hiring recommendation with evidence, (5) FeedbackGeneratorService — structured candidate feedback. 5 tools: `analyze_interview_recording` (full suite), `detect_interview_bias`, `generate_interview_opinion`, `generate_candidate_feedback`, `compare_interview_performance`. All gated by `interview_intelligence` module.
- **ATS Integration**: Full integration with Gupy, Pandapé, and Merge.dev.
- **Monetizable Modules Infrastructure**: Provides a framework for managing and gating features as modules with different tiers and statuses (beta, trial, active, expired). Audited in Task #163 — 14-dimension analysis + WeDO governance + LGPD compliance passed. 15 tools mapped to 5 modules (7 PREMIUM_GATED, 8 TASTING). Fail-closed on error. PII masking at LLMService level covers all module tool calls. Tenant isolation via `_enforce_tenant()` on all endpoints. See `docs/audit/AUDIT_MODULES_GOVERNANCE_T163.md`.
- **LLM Configuration**: Allows per-tenant configuration of LLM providers (Gemini, Claude, OpenAI) via settings.
- **Recursive RAG Chunking**: Implements a `RecursiveTextSplitter` strategy for hierarchical document chunking.
- **CrewAI-Style Delegation on AgentBus**: A formal multi-agent delegation system built on AgentBus with `AgentCrew`, `CrewPlan`, and `CrewPlanExecutor` for task orchestration.
- **UI/UX Enhancements**: TopBar eliminated, sidebar now includes user panel and redesigned notification system. TipTap Rich Text Editor integrated for email templates and job descriptions.

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