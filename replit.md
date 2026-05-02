# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system. It uses a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology to provide comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to optimize hiring processes through advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics. The platform covers the entire hiring cycle from attracting to hiring and analysis, focusing on intelligent automation and detailed reporting to improve hiring quality and reduce time-to-hire.

# User Preferences
- Idioma: Português
- Design/Layout: Sempre perguntar antes de fazer mudanças em design ou layouts - o usuário quer avaliar propostas antes da implementação
- Separação Backend/Frontend: Manter estruturas de back e front completamente separadas (API REST/GraphQL no backend, SPA no frontend)
- Componentização: Priorizar componentes reutilizáveis e modulares, evitar código monolítico
- Preparação para Migração: Estruturar código pensando em possível conversão para Vue.js + Nuxt (frontend) e Ruby on Rails (backend)
- Border Radius: Seguir DS v4.2.2 — rounded-md (8px) padrão universal para botões/inputs/cards/modais, rounded-xl (16px) para interfaces imersivas (chat, login), rounded-full (pill) para badges/skills/avatars.
- Chat é a interface principal - O recrutador interage com a LIA através de conversa natural, NÃO através de botões
- LIA pergunta, recrutador responde - Quando uma etapa está completa, a LIA PERGUNTA se quer avançar. O recrutador RESPONDE no chat (ex: "sim", "vamos", "pode avançar")
- Painéis são suporte visual - Os painéis laterais mostram informações e permitem edição, mas a navegação e decisões são feitas via chat
- Sem botões como interface principal - Botões são apenas atalhos opcionais, NUNCA a forma principal de interação
- Transições via confirmação textual - O recrutador confirma avanço de etapa escrevendo no chat, não clicando em botões
- A LIA deve entender variações naturais de confirmação em português

# System Architecture
The platform uses Next.js, React, and TypeScript for the frontend, styled with Radix UI, shadcn/ui, and Tailwind CSS. The backend is built with FastAPI (Python) and PostgreSQL. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation. It supports a custom agent marketplace and uses a CascadedRouter with severity-based delegation.
- **Intelligent Conversational Interface (LIA)**: The primary interaction is chat-based, supporting multi-step reasoning, intent classification, and session persistence through a unified chat system (WebSocket/SSE). It utilizes a "5-Chat + 2-Channel Architecture" for various recruitment stages.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, and dynamic split-screen panels, aligned with Design System v4.2.2.
- **WSI Screening**: A 6-block AI-powered methodology for comprehensive candidate evaluation, generating detailed reports and supporting public candidate-facing chat with text and bidirectional audio.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection and a `BiasAuditService`.
- **Job Creation & Candidate Management**: Supports conversational and manual job creation with a Kanban candidate movement system featuring AI-powered sub-status prediction and WSI score integration. A Job Readiness Hub provides a 7-stage visual pipeline. The canonical job creation wizard ensures Human-in-the-Loop (HITL) approval for critical steps.
- **Pipeline / Recruitment Stages**: Four distinct endpoints manage company-wide pipeline configurations, job-specific stages, transition validations, and a catalog of pipeline templates.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` with LLM-powered parameter extraction.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` for messaging with `RedisBroker`, `RabbitMQBroker`, and `PubSubBroker` implementations.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API with Twilio as PSTN fallback.
- **Security & Production Readiness**: Includes robust authentication with httpOnly cookies, JWT, WorkOS SSO, API security, unified health endpoints, structured logging, global exception handlers, and Row Level Security (RLS) in PostgreSQL.
- **Talent Intelligence Domain**: Implements competitive capabilities such as a Skills Ontology Engine, Internal Mobility matching, Workforce Planning, Interview Intelligence, and Passive Candidate Nurture.
- **Interview Intelligence Infrastructure**: Manages the full interview lifecycle with Microsoft Calendar integration, Gemini-based audio/video transcription, and 5 services for WSI methodology, bias detection, comparative analysis, strategic opinion, and feedback generation.
- **External API Consumption Tracking**: Unified ledger for tracking external API costs per tenant with budget alerts.
- **ATS Integration**: Full integration with Gupy, Pandapé, and Merge.dev.
- **Monetizable Modules Infrastructure**: Provides a framework for managing and gating features as modules with different tiers and statuses.
- **LLM Configuration**: Allows per-tenant configuration of LLM providers (Gemini, Claude, OpenAI).
- **Recursive RAG Chunking**: Implements a `RecursiveTextSplitter` strategy for hierarchical document chunking.
- **CrewAI-Style Delegation on AgentBus**: A formal multi-agent delegation system built on AgentBus for task orchestration.
- **Database Migrations**: Uses Alembic for schema management, automated via `scripts/post-merge.sh`. Schema head: `5880556c6d91` (LGPD Art.18 — `legal_basis_id`/`consent_version_id` em candidates + tabelas `lgpd_legal_bases`/`lgpd_consent_versions` com seed dos 4 fundamentos do Art.7). Anti-padrão conhecido: `Base.metadata.create_all()` em `app/core/database.py:1234` cria tabelas no startup antes do Alembic — pode causar schema drift parcial. Workflow `lia-backend` chama uvicorn direto (não `start.sh`), portanto não roda `alembic upgrade head` no boot — depende exclusivamente do post-merge.
- **Tenant Minimum Config Spec**: Defines the minimum viable configuration for any LIA tenant, covering critical settings and onboarding hints.
- **JD Upload**: Supports asynchronous Job Description uploads with progress tracking and validation, orchestrating the wizard intake process.
- **Settings Menu Architecture**: `settings-page-enhanced.tsx` is the single entry point for the settings menu, featuring 9 canonical hubs, dynamic deep-linking, and mandatory conventions for new hubs.

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