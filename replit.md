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

> **Documentação completa:** o índice canônico vive em [`docs/INDEX.md`](./docs/INDEX.md). O source of truth técnico (~1300 linhas, atualizado a cada PR estrutural) é [`docs/architecture/ARCHITECTURE.md`](./docs/architecture/ARCHITECTURE.md). Este `replit.md` mantém apenas o resumo executivo e os contratos críticos que mudam com pouca frequência.

**Stack:** Next.js + React + TypeScript no frontend (Radix UI / shadcn/ui / Tailwind), FastAPI (Python) + PostgreSQL no backend. Agentes LangGraph com Claude Sonnet como LLM primário. Redis para cache/queue, Celery para jobs assíncronos, Elasticsearch para busca, Sentry para erros.

**Pilares arquiteturais:**

- **Multi-Agent AI System** — 16 ReActAgents canônicos orquestrados por CascadedRouter com delegação por severidade. Marketplace de custom agents via `agent_studio`.
- **Conversational Interface (LIA)** — chat é a interface primária (WebSocket/SSE), com intent classification, persistência de sessão e arquitetura "5-Chat + 2-Channel". O wizard de criação de vaga é HITL com aprovação humana em steps críticos.
- **WSI Screening** — metodologia de 6 blocos para avaliação de candidato; gera relatório detalhado e suporta chat público (texto + áudio bidirecional).
- **Compliance 3-Pillar** — LGPD + SOX + EU AI Act, com FairnessGuard, FactChecker e `BiasAuditService`.
- **Tenant Context (T-A → T-F)** — `TenantAwareAgentMixin` + `CompanyId` value object + canary monitoring blindam o sistema contra a recorrência do bug *"LIA pergunta `company_id` no chat"*. **Detalhamento técnico:** [`docs/architecture/tenant-context-history.md`](./docs/architecture/tenant-context-history.md). Runbook on-call: [`docs/runbooks/missing_tenant_context.md`](./docs/runbooks/missing_tenant_context.md).
- **Pipeline / Recruitment Stages** — 4 endpoints para configurações company-wide, stages por vaga, validação de transições e templates de pipeline. Job Readiness Hub renderiza pipeline visual de 7 stages.
- **Closed-Loop Action Execution** — `ActionExecutorService` com extração LLM de parâmetros executa ações cross-chat.
- **Talent Funnel Search** — Elasticsearch + PG Vector + WRF com classificação de vaga via LLM e scoring de candidato.
- **Progressive Automation** — `CompanyHiringPolicy` com confidence-based decision engine controla nível de automação por tenant.
- **Broker Abstraction** — `BrokerInterface` com implementações Redis / RabbitMQ / Pub/Sub.
- **Voice Analysis** — VoIP browser via Gemini Live Audio API; Twilio como PSTN fallback (com OpenAI Whisper/TTS no fallback).
- **Security & Production Readiness** — httpOnly cookies, JWT, WorkOS SSO, RLS no PostgreSQL, structured logging, global exception handlers, unified health endpoints.
- **Talent Intelligence Domain** — Skills Ontology Engine, Internal Mobility, Workforce Planning, Interview Intelligence, Passive Candidate Nurture.
- **Interview Intelligence** — full lifecycle com Microsoft Calendar, Gemini transcription áudio/vídeo, e 5 serviços (WSI, bias detection, comparativa, opinião estratégica, geração de feedback).
- **External API Cost Tracking** — ledger unificado por tenant com alertas de budget.
- **ATS Integration** — Gupy, Pandapé, Merge.dev.
- **Monetizable Modules** — framework de gating de features por tier/status.
- **LLM Configuration** — per-tenant (Gemini, Claude, OpenAI).
- **Recursive RAG Chunking** — `RecursiveTextSplitter` com chunking hierárquico.
- **CrewAI-Style Delegation on AgentBus** — multi-agent delegation formal sobre AgentBus.
- **Database Migrations** — Alembic, automatizado via `scripts/post-merge.sh`.
- **Tenant Minimum Config Spec** — config mínimo viável para qualquer tenant LIA.
- **Multi-tenant Companies Schema** — tabela `companies` é a raiz multi-tenant (UUID v4 ou slug). Demo Company canônica: UUID `00000000-0000-4000-a000-000000000001`. Detalhes em [`docs/architecture/tenant-context-history.md`](./docs/architecture/tenant-context-history.md) §T-C.
- **JD Upload** — upload assíncrono de Job Description com progress tracking; orquestra wizard intake.

## Contratos críticos (não desviar sem atualizar testes canônicos)

- **Funil de Talentos (canônico 719L)** — `src/components/pages/candidates-page.tsx` é a ÚNICA implementação válida (orquestrada por `useCandidatesPageCore` + `CandidatesPageHeader` + `CandidatesPageModals` + `CandidateSearchResultsView` + `CandidateSearchBar`, com 6 abas e busca multi-modo sobre 3 fontes). **NÃO criar `FunilDeTalentosClient.tsx` ou alternativas** — caiu 2× (a2282c541 + 1119d216d via cherry-pick `--theirs`). A rota `(dashboard)/funil-de-talentos/page.tsx` deve renderizar `<CandidatesPage />` direto; `dashboard-app.tsx::PAGE_ROUTES` deve conter `"Funil de Talentos": "/funil-de-talentos"`; `sidebar.tsx` item Funil deve ter `navigateOnClick: true`. Em cherry-picks de bundles externos, NUNCA `--theirs` em massa nesses arquivos.
- **Settings Menu** — `settings-page-enhanced.tsx` é o entry point único (9 hubs canônicos, deep-linking dinâmico). A rota `/[locale]/(dashboard)/configuracoes/page.tsx` usa um wrapper fino `SettingsRouteClient` (`"use client"`) — mesmo padrão de `chat/ChatRouteClient.tsx`. **CRÍTICO:** NÃO adicionar `loading.tsx` no nível pai `configuracoes/` — só em sub-rotas (ex.: `configuracoes/ai-credits/loading.tsx`). Parent+child nested `loading.tsx` no route group `(dashboard)` causa Turbopack 16.2.4 compile deadlock.
- **Wizard de criação de vaga** — `WizardReActAgent` herda de `TenantAwareAgentMixin` com `tenant_strict_override = True` (NUNCA degrada para `"sua empresa"/"geral"`, mesmo com `LIA_AGENT_TENANT_STRICT=false` em dev). Detalhes em [`docs/architecture/tenant-context-history.md`](./docs/architecture/tenant-context-history.md) §T-B.
- **16 ReActAgents canônicos** — inventário sentinela em `tests/integration/agents/test_tenant_aware_rollout_t_d.py`. Adicionar um 17º quebra o build se não seguir o padrão T-D.
- **NON-ReAct callsites** — `resolve_tenant_snippet_for_non_react(...)` é a única forma canônica de injetar snippet de tenant fora dos 16 ReActAgents. NÃO ler `ctx["tenant_context_snippet"]` direto. Sentinela em `tests/integration/agents/test_non_react_tenant_helper_t_f.py`.

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
- Mailgun (primary email) / Resend (fallback)
- PostgreSQL
- Redis
- Elasticsearch
- Sentry (error monitoring)
- OpenAI (Whisper, TTS — PSTN fallback only)
- Twilio (Voice — PSTN fallback only)
- Deepgram (STT/transcrição de voz)
- Celery

# Operational Notes

## Redis Encryption (REDIS_ENCRYPTION_KEY) — obrigatório em prod

Plataforma usa Fernet (cryptography lib) para encriptar PII em Redis: sessões, candidate_list_store, fairness cache, voice transcripts. **REDIS_ENCRYPTION_KEY** deve estar setado em `production` e `staging`.

- Default `app.shared.security.redis_crypto.RedisCrypto` é fail-OPEN (plaintext) se key ausente — para gradual rollout em dev.
- Em prod: `app/main.py:lifespan` levanta `RuntimeError` no boot se key vazia (R-001 do plano de remediação, finding F-049).

Gerar key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Setar via Doppler (preferido) ou env var direto. Validação cobre `production`, `prod` e `staging`; `development` mantém posture fail-OPEN com warning.

## Compliance Bypass Flags (R-007 — emergency only)

| Flag | Efeito |
|---|---|
| `LIA_ALLOW_NON_COMPLIANT_DOMAINS=1` | Bypassa ComplianceDomainPrompt (FairnessGuard + PII + PromptInjection + FactCheck) em domains |
| `LIA_ALLOW_NON_COMPLIANT_AGENTS=1` | Bypassa LangGraphReActBase compliance em agents (PII/Fairness/Audit em agent layer) |
| `LIA_DISABLE_C3B=1` | **KILL SWITCH** da camada C3b inteira (PII strip + FairnessGuard L3 + FactCheck + Audit) — passthrough total |
| `LIA_ALLOW_REGISTRY_DRIFT=1` | Permite class_path inválido em agents_registry (R-004 emergency rollback only) |
| `LIA_AGENT_TENANT_STRICT=false` | **(inversa)** Default: `true` em prod/staging, `false` em dev. Quando `false` em prod, `TenantAwareAgentMixin` opera em fail-OPEN — agentes voltam a degradar silenciosamente. Origem do bug "LIA pergunta company_id no chat". Em prod, deixar `true` (ou ausente). |

**Em produção:** apenas para rollback emergencial. Quando ON:
- `app/main.py` lifespan loga **CRITICAL** no startup com lista agregada das flags ativas;
- Sentry `capture_message` (level=error) em prod;
- Endpoint `/api/v1/health/compliance/bypass-status` exposes em runtime (canary deve alertar quando `warning_count > 0`).

**Default:** tudo OFF. Ver `.env.example` seção *"COMPLIANCE / EMERGENCY FLAGS"*. Origem: R-007 do plano de remediação, finding F-053.
