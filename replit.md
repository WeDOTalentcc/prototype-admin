# Recent Changes

- **Task #429 — Job Readiness Hub (MVP)**: Pipeline visual de 7 estágios para preparar vagas importadas do ATS antes da triagem.
  - Backend: novas colunas em `job_vacancies` (migration 086), `JobReadinessService` com classificador puro + HITL approval, REST API em `/api/v1/job-readiness/*`.
  - Frontend: cliente `readiness-api.ts`, página Hub em `/[locale]/jobs/readiness` (alias PT `/vagas/prontidao`) com kanban + drawer + ações em lote, banner CTA + botão "Prontidão" na página de Vagas.
  - Tests: 16 unit tests do classifier + integration test de isolamento multi-tenant.

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

# Regras de Desenvolvimento (OBRIGATÓRIAS)

Estas regras valem para toda sessão de trabalho — humana ou IA — antes de qualquer edição. Violar qualquer uma delas é motivo para reverter o trabalho.

1. **Identifique o arquivo canônico antes de editar.** Antes de qualquer fix ou feature, mapeie a fonte da verdade (qual arquivo/rota/hook/serviço é o dono daquela responsabilidade). Se houver mais de um candidato, pare e consolide primeiro.
   - ❌ Não fazer: editar o primeiro arquivo que apareceu no grep e seguir adiante.
   - ✅ Fazer: rodar busca, listar todos os candidatos, escolher o canônico, marcar os demais para deleção.

2. **Corrija na origem, nunca no consumidor.** Se o bug está num serviço/endpoint/hook usado por N telas, conserte lá — não em cada chamada.
   - ❌ Não fazer: adicionar um `if (!data) return []` na tela X para esconder que o endpoint Y devolve `null`.
   - ✅ Fazer: ajustar o endpoint Y para devolver `[]` (ou tipar/validar a resposta no serviço compartilhado).

3. **Proibido workaround.** Sem `try/except` mascarando erro, sem fallback silencioso, sem cópia de lógica para "ganhar tempo", sem flag improvisada para desviar do bug.
   - ❌ Não fazer: `try: real_call() except: return mock_data` para o build não quebrar.
   - ✅ Fazer: deixar o erro explodir explicitamente, logar com contexto e corrigir a causa raiz.

4. **Arquitetura canônica e unificada.** Uma responsabilidade = um arquivo. Um endpoint = uma rota. Um domínio = um hook/serviço. Sem duplicatas, sem "v2" convivendo com "v1" sem plano de remoção.
   - ❌ Não fazer: manter `useCandidates.ts` e `useCandidatesNew.ts` ativos ao mesmo tempo.
   - ✅ Fazer: migrar consumidores para o canônico e deletar o legado na mesma task.

5. **Clean code enterprise.** Nomes claros, funções pequenas (<50 linhas), sem dead code, contratos tipados (Pydantic no backend, types no frontend), separação real de concerns frontend/backend/IA. Sem `any` gratuito, sem `print()`, sem segredo hardcoded.
   - ❌ Não fazer: função de 300 linhas que faz fetch, transforma, valida, persiste e renderiza.
   - ✅ Fazer: dividir em funções nomeadas por intenção, cada uma testável isoladamente.

6. **Antes de marcar concluído.** Rode a auditoria de 14 dimensões (skill `feature-audit`) e, quando o trabalho envolveu correção de código existente, rode também a checagem da skill `canonical-fix`. Se qualquer dimensão ficar ⚠️ ou ❌, conserte antes de fechar a task.
   - ❌ Não fazer: marcar `completed` porque "compilou e a tela abriu".
   - ✅ Fazer: passar pelas 14 dimensões, anexar o resultado, só então fechar.

**Skills relacionadas:**
- `feature-audit` — auditoria obrigatória de 14 dimensões antes de marcar qualquer task como concluída.
- `lia-planning` — metodologia de planning unificada (GSD + spec-driven + brainstorming) para qualquer trabalho significativo.
- `canonical-fix` — protocolo para identificar arquivo canônico e corrigir na origem, sem workaround (a ser criada em task dependente).
- `vue-migration-prep` — garante que o código novo já nasce preparado para a futura migração Vue/Nuxt.
- `design-standardize` — padronização visual React+Tailwind conforme Design System LIA v4.2.1.

# System Architecture
The platform uses Next.js, React, and TypeScript for the frontend, styled with Radix UI, shadcn/ui, and Tailwind CSS. The backend is built with FastAPI (Python) and PostgreSQL. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation and supports a custom agent marketplace with metering and billing.
- **Intelligent Conversational Interface (LIA)**: The primary interaction is chat-based, supporting multi-step reasoning, intent classification, and session persistence. It includes a unified chat system with WebSocket and SSE fallback.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1. Dynamic split-screen panels and a floating Super Prompt enhance user interaction.
- **WSI Screening**: A 6-block AI-powered methodology for comprehensive candidate evaluation, generating detailed reports with STAR analysis, Bloom/Dreyfus levels, gap analysis, and recommendations. Includes a public candidate-facing chat page for WSI screening with text and bidirectional audio support.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection. Includes a `BiasAuditService` to calculate adverse impact.
- **Job Creation & Candidate Management**: Supports conversational and manual job creation, with a Kanban candidate movement system featuring AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams. Settings pages use the `settings_config` context type via UnifiedChat lateral — no embedded chat. Chat transport: WebSocket first (via `/api/auth/ws-token` JWT), SSE fallback, REST fallback (`POST /api/backend-proxy/chat` → backend `/api/v1/chat`). Backend response format: `{ ok, data: { message: { content }, conversation: { id } } }`. Domain-specific contexts (`company_settings`, `hiring_policy`) skip Phase 1 (ActionExecutor) and Phase 1.5 (Agentic Loop) to route directly to their dedicated agent via context_type_override in Orchestrator.
- **Minha Empresa (Conversational Cards)**: The "Minha Empresa" page in Settings uses collapsible cards (Dados Basicos, Cultura, Tech Stack, Beneficios, Departamentos, Politicas) that update in real-time when the company_settings agent responds via the UnifiedChat lateral. Context auto-switches to `settings_config` on mount.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` with LLM-powered smart parameter extraction.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` for messaging with `RedisBroker`, `RabbitMQBroker`, and `PubSubBroker` implementations.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API with Twilio as PSTN fallback.
- **Security & Production Readiness**: Includes robust authentication with httpOnly cookies, JWT, and WorkOS SSO, API security measures, unified health endpoint, structured logging, and global exception handlers. Per-request cost tracking with budget alerts. RLS (Row Level Security) enforced at PostgreSQL level on 107 VARCHAR company_id tables via migration 068. Deny-by-default policies with `lia_app` non-superuser role. See `docs/RLS_CONTRACT.md` for Rails integration guide.
- **Talent Intelligence Domain**: Implements competitive capabilities such as a Skills Ontology Engine, Internal Mobility matching, Workforce Planning, Interview Intelligence (transcript analysis + Gemini transcription service), and Passive Candidate Nurture. These are part of monetizable modules with module-aware tool gating.
- **Interview Intelligence Infrastructure**: Full interview lifecycle with Microsoft Calendar integration, dedicated transcript/transcript_language/transcript_source columns on Interview model, Gemini-based audio/video transcription service (`app/domains/interview_intelligence/services/transcription_service.py`), background transcription via PATCH `/interviews/{id}/recording`, POST `/interviews/{id}/transcribe`, GET `/interviews/{id}/transcript`. Teams transcription also populates the dedicated columns. Migration 067 adds the new columns.
- **Interview Intelligence Pro (Premium Module)**: 5 services in `app/domains/interview_intelligence/services/`: (1) InterviewWSIService — WSI methodology on transcripts (Bloom/Dreyfus/CBI/Big Five), (2) BiasDetectorService — dual-layer bias detection (regex + LLM), (3) ComparativeAnalysisService — candidate ranking vs vacancy peers, (4) StrategicOpinionService — LLM hiring recommendation with evidence, (5) FeedbackGeneratorService — structured candidate feedback. 5 tools: `analyze_interview_recording` (full suite), `detect_interview_bias`, `generate_interview_opinion`, `generate_candidate_feedback`, `compare_interview_performance`. All gated by `interview_intelligence` module.
- **External API Consumption Tracking (Apify/Pearch)**: Unified ledger for tracking external API costs per tenant. `ExternalApiConsumption` model records every Apify/Pearch call with company_id, cost_usd, cost_brl, exchange_rate, provider, operation, success status. Endpoints: GET `/api/v1/consumption/report` (period report), GET `/api/v1/consumption/invoice-data` (invoice generation data), GET `/api/v1/consumption/budget-status` (Apify budget tracking). Budget alerts via ActivityService when monthly Apify spend exceeds threshold. Env vars: `APIFY_USD_TO_BRL_RATE` (default 5.50), `APIFY_MONTHLY_BUDGET_USD` (default 100.00). `CreditTransactionType` extended with `APIFY_ENRICHMENT` and `PEARCH_SEARCH`. TokenTrackingService extended with `record_apify_usage()` for ai_consumption integration. Migration 075.
- **ATS Integration**: Full integration with Gupy, Pandapé, and Merge.dev.
- **Monetizable Modules Infrastructure**: Provides a framework for managing and gating features as modules with different tiers and statuses (beta, trial, active, expired). Audited in Task #163 — 14-dimension analysis + WeDO governance + LGPD compliance passed. 15 tools mapped to 5 modules (7 PREMIUM_GATED, 8 TASTING). Fail-closed on error. PII masking at LLMService level covers all module tool calls. Tenant isolation via `_enforce_tenant()` on all endpoints. See `docs/audit/AUDIT_MODULES_GOVERNANCE_T163.md`.
- **LLM Configuration**: Allows per-tenant configuration of LLM providers (Gemini, Claude, OpenAI) via settings.
- **Recursive RAG Chunking**: Implements a `RecursiveTextSplitter` strategy for hierarchical document chunking.
- **CrewAI-Style Delegation on AgentBus**: A formal multi-agent delegation system built on AgentBus with `AgentCrew`, `CrewPlan`, and `CrewPlanExecutor` for task orchestration.
- **UI/UX Enhancements**: TopBar eliminated, sidebar now includes user panel and redesigned notification system. TipTap Rich Text Editor integrated for email templates and job descriptions.

# Database Migrations
- **Tool**: Alembic. Versions live in `lia-agent-system/alembic/versions/` (NOT `lia-agent-system/app/db/migrations/`).
- **Apply**: `cd lia-agent-system && python -m alembic upgrade head`. Idempotent — re-runs are no-ops when already at head.
- **Automated**: `scripts/post-merge.sh` runs `alembic upgrade head` after every merge so model changes never leave the running DB out of sync (regression guard for the 2026-04-17 outage where Task #346's migration 082 `add_candidate_company_id` shipped but never ran → all `/candidates` and `/search/candidates` endpoints returned 500 with `UndefinedColumnError: column candidates.company_id does not exist`).
- **Demo tenant**: Canonical UUID is `00000000-0000-4000-a000-000000000001`. Migration 080 retired the legacy string id `'demo_company'` from every string-typed `company_id`/`tenant_id` column and inserted the canonical row into `companies`.

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

# i18n (Internationalization)
- **Library**: next-intl
- **Default locale**: pt (Portuguese), maps to messages/pt-BR.json
- **Supported locales**: pt, en
- **Locale prefix**: always (all routes prefixed with /pt/ or /en/)
- **Root / redirects**: 307 to /pt/
- **Config files**: src/i18n/config.ts, src/i18n/request.ts, src/i18n/routing.ts
- **Message files**: messages/pt-BR.json, messages/en.json
- **Route structure**: src/app/[locale]/ contains all page routes; src/app/api/ stays outside [locale]
- **Localized pathnames**: Not yet implemented. All routes use same path under both locales (e.g., /pt/vagas, /en/vagas). Localized URL rewrites (vagas↔jobs, funil↔pipeline) deferred to future tasks when route structure is consolidated
- **Middleware**: src/middleware.ts chains next-intl locale routing with existing JWT/WorkOS auth
- **Sidebar**: Uses useTranslations('sidebar') — section labels, item labels, user menu, recent items all translated
- **next.config.js**: Uses createNextIntlPlugin wrapping withBundleAnalyzer
- **Locale detection**: Disabled (`localeDetection: false` in routing.ts) — forces Portuguese regardless of browser language
- **Translation status**: All namespaces fully translated (sidebar, chat, jobs, candidates, screening, kanban, agents, settings). ~785 keys translated from English to Portuguese. Remaining ~195 untranslated keys are brand/proper names (WhatsApp, LinkedIn, Score WSI, etc.) intentionally identical in both languages