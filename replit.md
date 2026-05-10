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
- **Job Creation & Candidate Management**: Supports conversational and manual job creation with a Kanban candidate movement system featuring AI-powered sub-status prediction and WSI score integration. A Job Readiness Hub provides a 7-stage visual pipeline. The canonical job creation wizard ensures Human-in-the-Loop (HITL) approval for critical steps. The SSE handler (`agent_chat_sse.py`) injects tenant context via `TenantContextService` and includes a wizard canonical path mirroring the WS handler. `create_tracked_llm` in `llm_factory.py` provides LangChain Chat models for graph nodes. UUID `company_id` tenants use `workspace_id=0` with `company_id` string fallback in `review_node`.
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
- **Database Migrations**: Uses Alembic for schema management, automated via `scripts/post-merge.sh`.
- **Tenant Minimum Config Spec**: Defines the minimum viable configuration for any LIA tenant, covering critical settings and onboarding hints.
- **JD Upload**: Supports asynchronous Job Description uploads with progress tracking and validation, orchestrating the wizard intake process.
- **Funil de Talentos (canônico 719L)**: `src/components/pages/candidates-page.tsx` é a ÚNICA implementação válida — orquestrada por `useCandidatesPageCore` + `CandidatesPageHeader` + `CandidatesPageModals` + `CandidateSearchResultsView` + `CandidateSearchBar`, com 6 abas (Busca/Favoritos/Listas/Bancos de Talentos/Buscas Salvas/Histórico) e busca multi-modo (Linguagem Natural/Boolean/JD/Filtros/LinkedIn/Arquétipos) sobre 3 fontes (local/híbrida/Pearch). **NÃO criar `FunilDeTalentosClient.tsx` ou alternativas** — já caiu 2× (a2282c541 + 1119d216d via cherry-pick com `--theirs`); detalhes no header do arquivo. A rota `(dashboard)/funil-de-talentos/page.tsx` deve renderizar `<CandidatesPage />` direto (nunca `redirect()`); `dashboard-app.tsx::PAGE_ROUTES` deve conter `"Funil de Talentos": "/funil-de-talentos"`; `sidebar.tsx` item Funil deve ter `navigateOnClick: true`. Em cherry-picks de bundles externos, NUNCA `--theirs` em massa nesses arquivos.
- **Settings Menu Architecture**: `settings-page-enhanced.tsx` is the single entry point for the settings menu, featuring 9 canonical hubs, dynamic deep-linking, and mandatory conventions for new hubs. The route `/[locale]/(dashboard)/configuracoes/page.tsx` uses a thin `SettingsRouteClient` wrapper (`"use client"`) — same pattern as `chat/ChatRouteClient.tsx` — to isolate the heavy client component from the Server Component shell. **CRITICAL**: do NOT add `loading.tsx` at the parent `configuracoes/` level — only at sub-route levels (e.g. `configuracoes/ai-credits/loading.tsx`). A parent+child nested `loading.tsx` inside the `(dashboard)` route group triggers a Turbopack 16.2.4 compile deadlock that hangs the route forever (see comment block in `configuracoes/layout.tsx`).

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


## Redis Encryption (REDIS_ENCRYPTION_KEY) — obrigatório em prod

Plataforma usa Fernet (cryptography lib) para encriptar PII em Redis: sessões,
candidate_list_store, fairness cache, voice transcripts.

**REDIS_ENCRYPTION_KEY** deve estar setado em `production` e `staging`.

- Default `app.shared.security.redis_crypto.RedisCrypto` é fail-OPEN (plaintext)
  se key ausente — para gradual rollout em dev.
- Em prod: `app/main.py:lifespan` levanta `RuntimeError` no boot se key vazia
  (R-001 do plano de remediação, finding F-049).

Gerar key:

```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Setar via Doppler (preferido) ou env var direto. Validação cobre `production`,
`prod` e `staging`; `development` mantém posture fail-OPEN com warning.

## Compliance Bypass Flags (R-007 — emergency only)

Plataforma tem 4 env flags que bypassam camadas de compliance:

| Flag | Efeito |
|---|---|
| `LIA_ALLOW_NON_COMPLIANT_DOMAINS=1` | Bypassa ComplianceDomainPrompt (FairnessGuard + PII + PromptInjection + FactCheck) em domains |
| `LIA_ALLOW_NON_COMPLIANT_AGENTS=1` | Bypassa LangGraphReActBase compliance em agents (PII/Fairness/Audit em agent layer) |
| `LIA_DISABLE_C3B=1` | **KILL SWITCH** da camada C3b inteira (PII strip + FairnessGuard L3 + FactCheck + Audit) — passthrough total |
| `LIA_ALLOW_REGISTRY_DRIFT=1` | Permite class_path inválido em agents_registry (R-004 emergency rollback only) |
| `LIA_AGENT_TENANT_STRICT=false` | **(inversa)** Default: `true` em prod/staging, `false` em dev. Quando `false` em prod, `TenantAwareAgentMixin` opera em fail-OPEN — agentes voltam a degradar silenciosamente para `"sua empresa"/"geral"` quando tenant não resolvível. Origem do bug "LIA pergunta company_id no chat do wizard". Em prod, deixar `true` (ou ausente) para preservar fail-CLOSED canônico (T-A) |

**Em produção:** apenas para rollback emergencial. Quando ON:
- `app/main.py` lifespan loga **CRITICAL** no startup com lista agregada das flags ativas
- Sentry `capture_message` (level=error) em prod/prod-only
- Endpoint `/api/v1/health/compliance/bypass-status` exposes em runtime (canary monitoring deve alertar quando `warning_count > 0`)

**Default**: tudo OFF. Ver `.env.example` seção "COMPLIANCE / EMERGENCY FLAGS".

Origem: R-007 do plano de remediação, finding F-053.
