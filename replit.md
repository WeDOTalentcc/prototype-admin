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
- **Roteamento context-aware (T-1165)** — `useNavigationIntent` (`plataforma-lia/src/hooks/shared/use-navigation-intent.ts`) é o único caller que decide se `lia:navigation-hint` deve ser disparado, via helper puro `resolveNavigationIntentMode(raw, pathname)`: (a) já em `/chat` + alvo em `CHAT_FIRST_TARGET_PAGES` (atualmente só `"Vagas"`) → `page=null` (supressão, fluxo segue no chat); (b) outra rota → `mode="ask"`. `UnifiedChat.tsx` forwarda `result.mode` no `detail` do CustomEvent; `DashboardApp` ramifica em `detail.mode === "ask"`, posta uma mensagem da LIA no chat propondo a transição, e classifica a resposta livre PT-BR do recrutador via `classifyNavConfirmation` (positivos "sim/vamos/pode/bora/claro/ok/manda/fechou/...", negativos "não/agora não/depois/deixa pra lá/cancela/...", com negativos tendo precedência sobre tokens positivos como "pode" em "pode esperar"). Só `yes` dispara `router.push`; `no` posta ack ("Combinado — seguimos por aqui."); ambíguo deixa a proposta pendente até a próxima mensagem. `useWizardFlow` emite o mesmo hint `{page:"Vagas", mode:"ask", hint:"wizard:<stage>"}` quando `currentStage` transita para uma `SPLIT_STAGE` (review/publish/calibration/handoff/done/scheduling); transições dentro do mesmo stage não re-emitem (guard via `useRef`). Callers legacy (`useProactiveActionRouter`, `TourController`, `DonePanel`, `BibliotecaLiaRouteClient`, `NavigationHintCard`) que não setam `mode` continuam no caminho `navigate` direto. Sentinelas: `src/hooks/__tests__/use-navigation-intent.context.test.ts` (5 cenários do helper puro) + `src/components/__tests__/classify-nav-confirmation.test.ts` (positivos/negativos/ambíguos exaustivo) + E2E `e2e/tests/wizard/20-roteamento-split-view-coerente.spec.ts` (3 cenários: A=intent em /chat não empurra; B=ask + "pode ir" → push; B'=ask + "agora não" → ack).

## Contratos críticos (não desviar sem atualizar testes canônicos)

- **Funil de Talentos (canônico 719L)** — `src/components/pages/candidates-page.tsx` é a ÚNICA implementação válida (orquestrada por `useCandidatesPageCore` + `CandidatesPageHeader` + `CandidatesPageModals` + `CandidateSearchResultsView` + `CandidateSearchBar`, com 6 abas e busca multi-modo sobre 3 fontes). **NÃO criar `FunilDeTalentosClient.tsx` ou alternativas** — caiu 2× (a2282c541 + 1119d216d via cherry-pick `--theirs`). A rota `(dashboard)/funil-de-talentos/page.tsx` deve renderizar `<CandidatesPage />` direto; `dashboard-app.tsx::PAGE_ROUTES` deve conter `"Funil de Talentos": "/funil-de-talentos"`; `sidebar.tsx` item Funil deve ter `navigateOnClick: true`. Em cherry-picks de bundles externos, NUNCA `--theirs` em massa nesses arquivos.
- **Settings Menu** — `settings-page-enhanced.tsx` é o entry point único (9 hubs canônicos, deep-linking dinâmico). A rota `/[locale]/(dashboard)/configuracoes/page.tsx` usa um wrapper fino `SettingsRouteClient` (`"use client"`) — mesmo padrão de `chat/ChatRouteClient.tsx`. **CRÍTICO:** NÃO adicionar `loading.tsx` no nível pai `configuracoes/` — só em sub-rotas (ex.: `configuracoes/ai-credits/loading.tsx`). Parent+child nested `loading.tsx` no route group `(dashboard)` causa Turbopack 16.2.4 compile deadlock.
- **Settings ↔ chat lateral (T6 #993)** — `useSettingsConversational` (`plataforma-lia/src/hooks/settings/use-settings-conversational.ts`) injeta tags estruturadas `[ACTION:prefill_section][target_section:<key>]` no prompt do chat. `triggerPrefillSection` envia com `autoSend: true` por padrão (alinha com `analyzeWebsite`). O agente `CompanySettingsReActAgent` (`lia-agent-system/app/domains/company_settings/...`) reconhece essas tags via bloco `structured_action_tags` no YAML (`app/prompts/domains/company_settings.yaml`) e respeita `tenant_context_snippet` (regra #8 de `behavioral_rules`) — NUNCA pergunta nome/setor/plano/headcount já resolvidos do JWT. Após HITL, persiste via `save_company_field` / `save_company_section` / `import_benefits_from_data` / `import_workforce_plan` (todas com FairnessGuard). Sentinela offline em `lia-agent-system/tests/integration/agents/test_company_settings_no_regression.py`. Eval gate: `python -m eval.eval_runner --gate eval/golden/company_settings_prefill.jsonl` (18 cenários = 6 seções × 3 contratos positivo/anti-padrão/fairness, threshold 0.85 espelhando T-E).
- **Wizard de criação de vaga** — fluxo lineares (11 nós) + 4 HITLs com `interrupt()` canônico, classifier LLM por gate (Task #1085, flag `LIA_WIZARD_LLM_GATES`), continuidade de sessão via `derive_thread_id` puro + pin handler-level (Task #1080), eval gate online `wizard_no_tenant_leak.jsonl` (Task #1052) e intent classifier no primeiro turno (Task #1098). **Detalhamento técnico, contratos, sentinelas, eval gates, CI commands e runbook em [`docs/architecture/wizard-flow.md`](./docs/architecture/wizard-flow.md).** `WizardReActAgent` herda de `TenantAwareAgentMixin` com `tenant_strict_override = True` (NUNCA degrada para `"sua empresa"/"geral"`); ver também [`docs/architecture/tenant-context-history.md`](./docs/architecture/tenant-context-history.md) §T-B. Sentinelas offline: `tests/integration/agents/test_wizard_session_continuity_t1080.py`, `test_intake_node_schema_contract.py`, `test_wizard_node_message_invariant.py`. E2E: `e2e/tests/wizard/10-session-continuity.spec.ts`, `14-resume-via-interrupt.spec.ts`. Em PRs que toquem os 4 gate_nodes ou `WizardGateService._resume_engine`, rodar `bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1118 e2e/tests/wizard/14-resume-via-interrupt.spec.ts` (asserta zero repetição de pergunta + EXATAMENTE 4 audit rows `wizard_gate_service/resume_gate` em uma única `conversation_id`) e o eval gate `wizard_resume_via_interrupt.jsonl` (Task #1118).
- **16 ReActAgents canônicos** — inventário sentinela em `tests/integration/agents/test_tenant_aware_rollout_t_d.py`. Adicionar um 17º quebra o build se não seguir o padrão T-D.
- **NON-ReAct callsites** — `resolve_tenant_snippet_for_non_react(...)` é a única forma canônica de injetar snippet de tenant fora dos 16 ReActAgents. NÃO ler `ctx["tenant_context_snippet"]` direto. Sentinela em `tests/integration/agents/test_non_react_tenant_helper_t_f.py`.
- **Bootstrap cobertura Anthropic (Task #1164 — Bug D, addendum #1161)** — `_inject_anthropic_env` em `lia-agent-system/app/shared/llm_bootstrap.py` DEVE sobrescrever o `base_url` quando `kwargs["base_url"]` é o default upstream (`https://api.anthropic.com` com/sem trailing slash), via helper `_is_default_anthropic_base_url`. Sem isso, `langchain_anthropic.ChatAnthropic._client_params` (linha 1617 em `chat_models.py`) auto-popula kwargs com o default e o cliente bate direto em `api.anthropic.com` (401 com a wrapper key em dev/staging) — root cause real do "IA degradada (qualidade estimada: 20%)" disparando em 100% dos turnos do wizard de criação de vaga. Cobre `create_tracked_llm`/`get_claude_model_for_tenant`/`IntakeExtractor._get_llm` e qualquer novo callsite que use `ChatAnthropic`. Sentinelas: `tests/integration/llm/test_anthropic_base_url_injection_t_1164.py` (5 testes: 2 reproduzem kwargs do LangChain wrapper, 1 garante respeito a override não-default, 1 coverage runtime do helper, 1 AST guard exigindo chamada do helper no `_inject_anthropic_env`). Runbook completo: [`docs/runbooks/task-1161-three-bugs.md`](./docs/runbooks/task-1161-three-bugs.md) §"Bug A — Addendum Task #1164".
- **Wizard E2E — 3 bugs bloqueantes (Task #1161)** — três regressões resolvidas com sentinelas offline AST-validadas. **Bug B addendum (root cause real):** o traceback completo (habilitado pela própria fix B) revelou que `PostgresSaver` sync herda `aget_tuple` do stub abstrato `BaseCheckpointSaver` — `await self._graph.ainvoke(Command(resume=...))` em `aresume_with_message` disparava `NotImplementedError` no `AsyncPregelLoop.__aenter__`, silenciado pelo `_emit_silent_fallback`. Fix em `libs/agents-core/lia_agents_core/checkpointer.py` adiciona helper `_supports_async()` e fallback dev para `MemorySaver`/`InMemorySaver` (suporta async); em prod-like levanta `RuntimeError` exigindo migração para `AsyncPostgresSaver`. Sentinela: `tests/integration/agents/test_checkpointer_async_support_t_1161.py` (3 testes: AST helper exists, AST guard chamado, runtime saver suporta `aget_tuple`). Fixes detalhados originais: (A) `lia-agent-system/app/shared/llm_bootstrap.py` helper `_inject_anthropic_env` injeta `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` SEMPRE (fora do gate `api_key`), evitando 401 quando `ChatAnthropic` passa `api_key=` explícita — sentinela `tests/integration/llm/test_anthropic_base_url_injection_t_1161.py` inclui AST guard `test_inject_helper_uses_unconditional_base_url`; (B) catch de `aresume_with_message` em `WizardSessionService.process_message` agora chama `logger.exception(...)` + `sentry_sdk.capture_exception(...)` ANTES de `_emit_silent_fallback(...)` — sentinela `tests/integration/agents/test_wizard_resume_traceback_t_1161.py` exige ordem dos statements via AST; (C) endpoints `/api/v1/company/culture-*` (2 arquivos, 19 catches) substituíram `detail=str(e)` por `detail="internal error"` (information disclosure) E o `CompanyCultureProfileBase` ganhou `field_validator(mode="before")` em 7 campos `list[str]` via helper `_normalize_list_of_strings` (coerce dict→str via code/name/label/value, drop None/empty) que era a causa REAL do `ResponseValidationError` 500 — sentinela `tests/integration/security/test_culture_no_internal_leak_t_1161.py` cobre AST (HTTP) + coverage real do validator. Runbook completo: [`docs/runbooks/task-1161-three-bugs.md`](./docs/runbooks/task-1161-three-bugs.md).
- **Audit obrigatório nos 3 domínios Interview + Offer (T-1157)** — todo `async def` público em `app/domains/{interview_scheduling,interview_intelligence,offer}/services/*.py` que faz mutação (`db.commit`, `_repo.create/update/delete`, `db.add`) DEVE chamar `AuditService.log_decision[_in_session]` (SOX 7-year para offer; LGPD Art.46 para transcription). Sentinelas AST: `tests/integration/security/test_audit_required_interview_offer_t_1157.py` (audit obrigatório) e `test_ownership_xvalidation_interview_offer_t_1157.py` (rotas mutating em `interviews.py`/`interview_notes.py`/`interview_analysis.py`/`scheduling.py`/`offers.py`/`calendar.py` repassam `company_id=` para a camada inferior). Padrão ratchet: débito legado em `tests/.baseline_audit_missing_interview_offer.txt` (7) e `.baseline_ownership_xvalidation_interview_offer.txt` (26); regressão NOVA quebra a build, remoção de entrada é encorajada. **`self_scheduling_public.py`** — apenas POST `/link` exige `Depends(require_company_id)` (e sobrescreve `body.company_id` com o claim do JWT contra spoofing); GET `/link/{token}` e POST `/link/{token}/confirm` são legitimamente públicos (token opaco single-use). **CRÍTICO:** o middleware (`app/middleware/auth_enforcement.py`) usa `PUBLIC_REGEX_PATHS` com regex EXPLÍCITA para os 2 paths (token 16-128 chars `[A-Za-z0-9_-]`) — NÃO use prefixo amplo `/api/v1/scheduling/link/` em `PUBLIC_PREFIXES` (sub-rotas futuras ficariam auth-bypassed; sentinela `test_middleware_no_longer_uses_broad_scheduling_prefix` impede regressão). Property tests hermeticos em `tests/integration/security/test_self_scheduling_public_properties_t_1157.py` cobrem 9 propriedades (404 sem token, 410 em replay/TTL/used, GET não vaza PII/internals, POST recrutador sobrescreve `body.company_id`, regex matcher rejeita sub-rotas). Runbook: [`docs/runbooks/audit-interview-offer.md`](./docs/runbooks/audit-interview-offer.md).

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
