# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system. It uses a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology to provide comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to optimize hiring processes through advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics. The platform covers the entire hiring cycle from attracting to hiring and analysis, focusing on intelligent automation and detailed reporting to improve hiring quality and reduce time-to-hire.

# User Preferences
- Idioma: Português
- Design/Layout: Sempre perguntar antes de fazer mudanças em design ou layouts - o usuário quer avaliar propostas antes da implementação
- Separação Backend/Frontend: Manter estruturas de back e front completamente separadas (API REST/GraphQL no backend, SPA no frontend)
- Componentização: Priorizar componentes reutilizáveis e modulares, evitar código monolítico
- Preparação para Migração: Estruturar código pensando em possível conversão para Vue.js + Nuxt (frontend) e Ruby on Rails (backend)
- Border Radius (fonte-da-verdade = código): cards/modais = `rounded-xl` (12px); botões/inputs/selects = `rounded-md`; chips/badges/pílulas = `rounded-full`. Interfaces imersivas (chat expandido, login) podem usar `rounded-2xl`. NUNCA sobrescrever o raio em `<Button>`. Paleta SEMPRE via tokens `status-*`/`wedo-*`/`lia-*` — cores cruas do Tailwind (`amber-50`, `emerald-600`, `purple-100`, `blue-50`, `red-200`…) são proibidas quando há token equivalente. Detalhe completo na seção **Design System — Fundação**.
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
- **Roteamento context-aware (T-1165)** — `useNavigationIntent` decide se `lia:navigation-hint` dispara (supressão chat-first vs `mode="ask"` com confirmação textual PT-BR via `classifyNavConfirmation`); `useWizardFlow` emite o hint nas transições de `SPLIT_STAGE`. **Detalhamento, callers, sentinelas e E2E:** [`docs/architecture/ARCHITECTURE.md`](./docs/architecture/ARCHITECTURE.md) §6.6.

## Contratos críticos (não desviar sem atualizar testes canônicos)

- **Funil de Talentos (canônico 719L)** — `src/components/pages/candidates-page.tsx` é a ÚNICA implementação válida (orquestrada por `useCandidatesPageCore` + `CandidatesPageHeader` + `CandidatesPageModals` + `CandidateSearchResultsView` + `CandidateSearchBar`, com 6 abas e busca multi-modo sobre 3 fontes). **NÃO criar `FunilDeTalentosClient.tsx` ou alternativas** — caiu 2× (a2282c541 + 1119d216d via cherry-pick `--theirs`). A rota `(dashboard)/funil-de-talentos/page.tsx` deve renderizar `<CandidatesPage />` direto; `dashboard-app.tsx::PAGE_ROUTES` deve conter `"Funil de Talentos": "/funil-de-talentos"`; `sidebar.tsx` item Funil deve ter `navigateOnClick: true`. Em cherry-picks de bundles externos, NUNCA `--theirs` em massa nesses arquivos.
- **Settings Menu** — `settings-page-enhanced.tsx` é o entry point único (9 hubs canônicos, deep-linking dinâmico). A rota `/[locale]/(dashboard)/configuracoes/page.tsx` usa um wrapper fino `SettingsRouteClient` (`"use client"`) — mesmo padrão de `chat/ChatRouteClient.tsx`. **CRÍTICO:** NÃO adicionar `loading.tsx` no nível pai `configuracoes/` — só em sub-rotas (ex.: `configuracoes/ai-credits/loading.tsx`). Parent+child nested `loading.tsx` no route group `(dashboard)` causa Turbopack 16.2.4 compile deadlock.
- **Settings ↔ chat lateral (T6 #993)** — `useSettingsConversational` (`plataforma-lia/src/hooks/settings/use-settings-conversational.ts`) injeta tags estruturadas `[ACTION:prefill_section][target_section:<key>]` no prompt do chat. `triggerPrefillSection` envia com `autoSend: true` por padrão (alinha com `analyzeWebsite`). O agente `CompanySettingsReActAgent` (`lia-agent-system/app/domains/company_settings/...`) reconhece essas tags via bloco `structured_action_tags` no YAML (`app/prompts/domains/company_settings.yaml`) e respeita `tenant_context_snippet` (regra #8 de `behavioral_rules`) — NUNCA pergunta nome/setor/plano/headcount já resolvidos do JWT. Após HITL, persiste via `save_company_field` / `save_company_section` / `import_benefits_from_data` / `import_workforce_plan` (todas com FairnessGuard). Sentinela offline em `lia-agent-system/tests/integration/agents/test_company_settings_no_regression.py`. Eval gate: `python -m eval.eval_runner --gate eval/golden/company_settings_prefill.jsonl` (18 cenários = 6 seções × 3 contratos positivo/anti-padrão/fairness, threshold 0.85 espelhando T-E).
- **Wizard de criação de vaga** — fluxo linear (15 nós: 11 funcionais + 4 gates HITL com `interrupt()` canônico), classifier LLM por gate (flag `LIA_WIZARD_LLM_GATES`), continuidade de sessão via `derive_thread_id` puro + pin handler-level. `WizardReActAgent` herda de `TenantAwareAgentMixin` com `tenant_strict_override = True` (NUNCA degrada para `"sua empresa"/"geral"`; ver [`docs/architecture/tenant-context-history.md`](./docs/architecture/tenant-context-history.md) §T-B). **Contratos completos, nós, gates, sentinelas, eval gates, CI commands e runbook (incl. o gatilho E2E `run-pw-cenario` ao tocar gate_nodes/`_resume_engine`):** [`docs/architecture/wizard-flow.md`](./docs/architecture/wizard-flow.md).
- **16 ReActAgents canônicos** — inventário sentinela em `tests/integration/agents/test_tenant_aware_rollout_t_d.py`. Adicionar um 17º quebra o build se não seguir o padrão T-D.
- **NON-ReAct callsites** — `resolve_tenant_snippet_for_non_react(...)` é a única forma canônica de injetar snippet de tenant fora dos 16 ReActAgents. NÃO ler `ctx["tenant_context_snippet"]` direto. Sentinela em `tests/integration/agents/test_non_react_tenant_helper_t_f.py`.
- **Bootstrap cobertura Anthropic (Bug D / base_url injection)** — `_inject_anthropic_env` (`lia-agent-system/app/shared/llm_bootstrap.py`) DEVE sobrescrever `base_url` quando o caller (ou o wrapper `langchain_anthropic.ChatAnthropic`) já passou o default upstream `https://api.anthropic.com` — senão o cliente bate direto na Anthropic (401 com a wrapper key em dev/staging), root cause real do "IA degradada (qualidade ~20%)" em 100% dos turnos do wizard. **Helper `_is_default_anthropic_base_url`, callsites cobertos, 5 sentinelas e runbook:** [`docs/runbooks/task-1161-three-bugs.md`](./docs/runbooks/task-1161-three-bugs.md) §"Bug A — Addendum Task #1164".
- **Wizard E2E — 3 bugs bloqueantes (Bug A base_url · Bug B checkpointer async · Bug C culture leak/validator)** — três regressões resolvidas com sentinelas offline AST-validadas. Pontos inegociáveis: (A) `_inject_anthropic_env` injeta `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` fora do gate `api_key`; (B) o catch de `aresume_with_message` loga/captura exceção ANTES de qualquer silent fallback (o `NotImplementedError` do `PostgresSaver` sync era engolido), com fallback async-capable só em dev; (C) endpoints `/api/v1/company/culture-*` nunca vazam `str(e)` e o `CompanyCultureProfileBase` normaliza os campos `list[str]` via `field_validator(mode="before")`. **Fixes detalhados, sentinelas e runbook:** [`docs/runbooks/task-1161-three-bugs.md`](./docs/runbooks/task-1161-three-bugs.md).
- **Audit obrigatório nos 3 domínios Interview + Offer (T-1157)** — todo `async def` público mutativo em `app/domains/{interview_scheduling,interview_intelligence,offer}/services/*.py` DEVE chamar `AuditService.log_decision[_in_session]` (SOX 7-year para offer; LGPD Art.46 para transcription), e as rotas mutating devem repassar `company_id=` para a camada inferior. Padrão ratchet via baselines (regressão NOVA quebra a build). **CRÍTICO `self_scheduling_public.py`:** o middleware usa `PUBLIC_REGEX_PATHS` com regex EXPLÍCITA para os 2 paths públicos por token — NUNCA prefixo amplo `/api/v1/scheduling/link/` em `PUBLIC_PREFIXES` (auth-bypass de sub-rotas futuras). **Sentinelas AST, property tests, baselines e runbook:** [`docs/runbooks/audit-interview-offer.md`](./docs/runbooks/audit-interview-offer.md).

# Design System — Fundação

> **Fonte-da-verdade = código.** Onde doc e código divergirem, o código (componentes em `plataforma-lia/src/components/ui/`, tokens em `tailwind.config.ts` + `design-tokens.css`/`design-tokens.ts`) vence. A skill `design-standardize` e este resumo descrevem o MESMO padrão.

## Raio (border-radius)

| Elemento | Classe |
|---|---|
| Cards, modais, dialogs | `rounded-xl` (12px) |
| Botões, inputs, selects, textareas, dropdowns | `rounded-md` |
| Chips, badges, pílulas, avatars | `rounded-full` |
| Interfaces imersivas (chat expandido, login) | `rounded-2xl` |

**Inegociável:** NUNCA sobrescrever o raio em `<Button>` (variantes `sm`/`lg` já resolvem `rounded-md`). `rounded-sm`/`rounded-lg` em botões/inputs são proibidos.

## Paleta — SEMPRE tokens, NUNCA cores cruas do Tailwind

Cores cruas do Tailwind (`amber-50`, `emerald-600`, `purple-100`, `blue-50`, `red-200`, `green-700`…) são **proibidas** quando há token equivalente. Usar:

- **Status semântico:** `status-success` (#16A34A), `status-error` (#DC2626), `status-warning` (#D97706) + variantes `*-bg`/`*-border` (CSS vars). Opacidade via `/10`, `/20` (ex.: `bg-status-success/10`).
- **Acento IA/LIA (exclusivo):** `wedo-cyan` (#60BED1), `wedo-cyan-dark` (#4DA8BB). Cyan NUNCA em botões — só em ícones/badges/acento de IA.
- **Paleta `wedo-*` (acento 10%):** `wedo-green` (#5DA47A), `wedo-green-light` (#A8D5B7), `wedo-green-pastel` (#A8D5B7), `wedo-green-bright` (#60D186), `wedo-orange` (#D19960), `wedo-purple` (#9860D1), `wedo-magenta` (#D160AB), `wedo-amber` (#F59E0B) + `wedo-amber-light`, `wedo-coral` (#E87575). Todas suportam opacity modifiers.
- **Superfícies/texto/borda:** tokens `lia-*` (`lia-bg-*`, `lia-text-*`, `lia-border-*`) — dark mode automático via CSS vars. Aliases legados (`lia-surface`/`lia-border`/`lia-primary`/`lia-muted`) existem só por compat; preferir o canonical.

## Componentes canônicos (qual usar)

| Necessidade | Componente | Raio/Tokens |
|---|---|---|
| Campo de formulário (label + controle + hint + erro) | `FormField` (`ui/form-field.tsx`) envolvendo `Input`/`Textarea`/`Select` | controle `rounded-md`; injeta `htmlFor`/`id`/`aria-*` |
| Pílula de status | `StatusPill` (`ui/status-pill.tsx`) | `rounded-full` + `status-*`; use `withDot`/`icon` (daltonismo) |
| Chip/badge genérico | `Chip` (`ui/chip.tsx`) / `Badge` (`ui/badge.tsx`) | `rounded-full` |
| Bloco de alerta/aviso | `Callout` (`ui/callout.tsx`) | `rounded-md` + `status-*`/`wedo-cyan`; ícone semântico |
| KPI/número de dashboard | `Metric` (`ui/metric.tsx`) ou `textStyles.kpi*`/`textStyles.metric*` | `font-data` (Inter) + `tabular-nums` |
| Checkbox/radio | `Checkbox` (`ui/checkbox.tsx`) / `radio-group` | tokens `lia-*` |

**KPIs numéricos:** padrão ÚNICO = fonte de dados **Inter** (`font-data`) + `tabular-nums`. Nunca usar `font-sans` (Open Sans) em números. Consumir via `<Metric />` ou `textStyles.metric*`/`textStyles.kpi*`.

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

> **Referência canônica completa:** [`docs/runbooks/operational-flags.md`](./docs/runbooks/operational-flags.md) — Redis encryption (`REDIS_ENCRYPTION_KEY`), tabela completa de Compliance Bypass Flags com efeito por flag, ambiente E2E Playwright (`PW_REUSE_SERVER`, `scripts/dev-up.sh`, wrappers `run-pw-cenario-*.sh`), e o aviso operacional do bug do workflow-limit counter.

O resumo abaixo lista apenas as flags ativas com efeito de produção; consulte o runbook acima para semântica detalhada, sentinelas, eval gates e procedimento de rollback.

## Compliance Bypass Flags (R-007 — emergency only) — índice rápido

| Flag | Default | Quando usar |
|---|---|---|
| `LIA_ALLOW_NON_COMPLIANT_DOMAINS` | OFF | Rollback ComplianceDomainPrompt |
| `LIA_ALLOW_NON_COMPLIANT_AGENTS` | OFF | Rollback compliance em agent layer |
| `LIA_DISABLE_C3B` | OFF | **KILL SWITCH** camada C3b inteira |
| `LIA_ALLOW_REGISTRY_DRIFT` | OFF | Rollback emergencial agents_registry |
| `LIA_AGENT_TENANT_STRICT` | **ON** em prod | Mantenha ON; OFF reabre bug "LIA pergunta company_id" |
| `LIA_WIZARD_LLM_GATES` | **ON** (pós-GA #1130) | Liga classifier LLM nos 4 gates HITL |
| `LIA_WIZARD_FALLBACK_LLM_DISABLED` | OFF | Testes offline; canned reply hard-prefixada |
| `LIA_WIZARD_SUPERVISOR_CLASSIFIER` | ON dev / OFF prod | Supervisor pre-graph 6-intents (#1127) |
| `LIA_DISABLE_COMPANY_AUDIT` | OFF | Rollback se audit_logs travar saves (viola SOX) |

**Em produção, qualquer flag ON dispara:** log CRITICAL no lifespan, `capture_message` no Sentry, exposure em `/api/v1/health/compliance/bypass-status` (canary alerta quando `warning_count > 0`). **Semântica detalhada, sentinelas, eval gates, runbook E2E (`PW_REUSE_SERVER`, `dev-up.sh`, wrappers `run-pw-cenario-*`) e Wave 16-20 Playwright:** [`docs/runbooks/operational-flags.md`](./docs/runbooks/operational-flags.md).

## Plan & Execute Activation (`LIA_V2_USE_PLAN_SERVICE` — Task #1211)

Flag de rollout (não-compliance, default OFF) que liga o path **Plan & Execute** (Phase 1.3 do `MainOrchestrator`) para requests multi-step. **INVIOLÁVEL: criação de vaga é SEMPRE e SÓ o wizard canônico — Plan & Execute NUNCA cria vaga.** O `plan_detector` tem guard de import-time (`_assert_no_creation_steps` + `JOB_CREATION_ACTION_IDS`) que falha alto se um pattern reintroduzir step de criação; o bootstrap do wizard usa `detect_job_creation` (`app/orchestrator/routing/job_creation_disambiguator.py`) para capturar frases compostas (`"criar a vaga e publicar"`). Continuidade pós-wizard é conversacional: a LIA OFERECE a etapa restante no chat ao atingir stage terminal e só a executa (publish/sync via `ats_integration.sync_job`, vinculado ao `job_id` criado) mediante confirmação natural PT-BR (`classify_confirmation`); continuação não conectada retorna sinal explícito, NUNCA fake success. `PlanExecutor` agora recebe `DomainRegistry()`+`DomainWorkflow()` reais (eliminou o fake success do registry vazio). **Detalhamento, sentinelas, canary W3-023 e rollback:** [`docs/runbooks/operational-flags.md`](./docs/runbooks/operational-flags.md) §2b.
