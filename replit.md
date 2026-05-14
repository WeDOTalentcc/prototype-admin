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
- **Settings ↔ chat lateral (T6 #993)** — `useSettingsConversational` (`plataforma-lia/src/hooks/settings/use-settings-conversational.ts`) injeta tags estruturadas `[ACTION:prefill_section][target_section:<key>]` no prompt do chat. `triggerPrefillSection` envia com `autoSend: true` por padrão (alinha com `analyzeWebsite`). O agente `CompanySettingsReActAgent` (`lia-agent-system/app/domains/company_settings/...`) reconhece essas tags via bloco `structured_action_tags` no YAML (`app/prompts/domains/company_settings.yaml`) e respeita `tenant_context_snippet` (regra #8 de `behavioral_rules`) — NUNCA pergunta nome/setor/plano/headcount já resolvidos do JWT. Após HITL, persiste via `save_company_field` / `save_company_section` / `import_benefits_from_data` / `import_workforce_plan` (todas com FairnessGuard). Sentinela offline em `lia-agent-system/tests/integration/agents/test_company_settings_no_regression.py`. Eval gate: `python -m eval.eval_runner --gate eval/golden/company_settings_prefill.jsonl` (18 cenários = 6 seções × 3 contratos positivo/anti-padrão/fairness, threshold 0.85 espelhando T-E).
- **Wizard de criação de vaga** — `WizardReActAgent` herda de `TenantAwareAgentMixin` com `tenant_strict_override = True` (NUNCA degrada para `"sua empresa"/"geral"`, mesmo com `LIA_AGENT_TENANT_STRICT=false` em dev). Detalhes em [`docs/architecture/tenant-context-history.md`](./docs/architecture/tenant-context-history.md) §T-B. **Continuidade de sessão (Task #1051):** `CascadedRouter.route()` Tier 0.5 — `wizard_session_pin` — invoca `WizardSessionService.is_session_active(session_id, company_id)` AFTER `rail_a_hint` override (FE explícito ainda vence) e BEFORE Tier 0; quando há checkpoint LangGraph aberto (stage ≠ `completed`), curto-circuita com `RouteResult(domain_id="wizard", source="wizard_session_pin", confidence=1.0)`. Pin colocado na CAMADA CANÔNICA do router (não em cada handler) cobre TODOS os transports — WS, SSE, REST orchestrator, autonomous_react_agent — sem duplicação. `is_session_active` consulta marker Redis (`lia:wizard:active:{session_id}`, TTL 2h) PRIMEIRO — cobre `msg["thread_id"]` custom (priority 1 do `derive_thread_id`) — e fallback heurístico (`wiz-{token}-{sid}` + `wiz-{sid}`) depois. `process_message` mantém o marker (set em open, delete em completed). Sem isso, o turno 2 do wizard ("Demo Company, 5 anos…") era reclassificado pelo router → bypass do `WizardSessionService.process_message` → checkpointer não restaurado → estado perdido (B2 esquece título / B3 sem histórico / B4 salary tool re-pergunta empresa). Sentinela: `tests/integration/agents/test_wizard_session_continuity_t1051.py` (10 cases — S1 heal, S2 helper + 3 estratégias, S3 router pin AST + WS no-dup, S4 comportamental). **Eval gate online (Task #1052):** `eval/golden/wizard_no_tenant_leak.jsonl` reproduz, em conversação ao vivo contra o backend, os 4 bugs originais — B1 (NÃO pergunta `company_id` em texto livre), B2 (mantém o título da vaga entre turnos), B3 (NÃO afirma ter perdido o histórico), B4 (a salary tool NÃO re-pergunta empresa/setor) — em 12 cenários: 3 single-turn (B1) + 9 multi-turn de 3 turnos (B2/B3/B4 × 3 vagas: Engenheiro Backend, Analista Financeiro, Coordenador de Marketing). Cada caso multi-turn replay é executado sobre uma ÚNICA `conversation_id` (capturada da primeira resposta e devolvida nos turnos seguintes), forçando o checkpointer LangGraph + o `wizard_session_pin` Tier 0.5 a participarem do gate — sem isso, B2/B3/B4 não seriam observáveis. Em CI, rodar primeiro a execução ao vivo e depois o gate (espelha T-E e CSP, threshold 0.85): `python -m eval.eval_runner --dataset eval/golden/wizard_no_tenant_leak.jsonl && python -m eval.eval_runner --gate eval/golden/wizard_no_tenant_leak.jsonl`. O scorer aplica `re.search` (IGNORECASE/DOTALL) sobre os `anti_patterns` regex e exige pelo menos um `expected_snippet_markers` (ex.: "Demo Company", "Backend") na resposta final como evidência de que o `tenant_context_snippet` foi honrado. Requer `LIA_TEST_TOKEN` válido + backend rodando — runner usa o JWT auto-gerado de `eval_runner.py:_make_eval_token`. Helper paralelo `_heal_legacy_demo_company_id` em `app/auth/dependencies.py` reconcilia in-place QUALQUER `company_id` demo não-canônico (legacy `"demo_company"` ou outras strings inválidas) para `CANONICAL_DEMO_UUID` antes de `CompanyId.parse` consumir (B1 fix; comportamento amplo é intencional — qualquer estado inválido em user demo é hygiene).
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
| `LIA_DISABLE_COMPANY_AUDIT=1` | **(PR4 / Task #1004)** Desliga o wrapper `audit_company_change` em todas as save tools de `company_settings` (`save_company_field`, `save_company_section`, `import_workforce_plan`, `save_hiring_policy`, `import_benefits_from_data`, `check_company_completeness`). Default: OFF (fail-CLOSED **outbox de duas fases**: emite intent `decision="initiated"` em `__aenter__` — falha aqui aborta o bloco antes de qualquer mutação; emite outcome `completed`/`failed`/`blocked_fairness`/`exception`/`read` em `__aexit__` com `before`/`after`/`target_id` capturados via setters; falha no outcome levanta `RuntimeError` para o caller). Cada save canônico produz **2 audit rows** correlatas via `trace_id` (decision_type=`company_settings_change`, retenção SOX 7 anos). Quando ON, viola Inegociável #6 (auditabilidade SOX/ISO 27001 / EU AI Act) e os saves passam a ser invisíveis ao trail de audit corporativo. Usar APENAS em rollback emergencial se o storage de `audit_logs` estiver bloqueando saves. |

**Em produção:** apenas para rollback emergencial. Quando ON:
- `app/main.py` lifespan loga **CRITICAL** no startup com lista agregada das flags ativas;
- Sentry `capture_message` (level=error) em prod;
- Endpoint `/api/v1/health/compliance/bypass-status` exposes em runtime (canary deve alertar quando `warning_count > 0`).

**Default:** tudo OFF. Ver `.env.example` seção *"COMPLIANCE / EMERGENCY FLAGS"*. Origem: R-007 do plano de remediação, finding F-053.

## Ambiente E2E (Task #1079)

A suíte Playwright (`pw-cenario-A → D`) reusa o `dev-server` já em pé — nenhum cenário spawna seu próprio webServer.

| Variável | Default | Efeito |
|---|---|---|
| `PW_REUSE_SERVER` | `1` (reusa) | Quando `0`, força `playwright.config.ts` a iniciar `npm run dev` próprio em :5000. Em Replit, com `dev-server` rodando como workflow, deixar default — caso contrário causa `EADDRINUSE :5000`. |

**Bootstrap único** (devs locais e CI): `./scripts/dev-up.sh` sobe Redis + `lia-backend` (FastAPI :8001) + `dev-server` (Next.js :5000) em ordem com healthcheck entre cada etapa. Idempotente: pula serviços já saudáveis. Use `--no-fe` quando o workflow `dev-server` do Replit já gerencia o frontend.

**Wrappers de cenário** em `plataforma-lia/scripts/run-pw-cenario-{a,b,c}.sh` invocam o canônico `run-pw-cenario.sh <label> <spec>`, que: (1) espera o frontend responder em 120s antes de chamar `pnpm playwright test`; (2) faz warmup de `/pt` e `/pt/chat` para evitar cold-compile do Next/Turbopack; (3) exporta `PW_REUSE_SERVER=1`. Os workflows `pw-cenario-A/B/C` apontam para esses wrappers; `pw-cenario-D` mantém seu próprio bootstrap inline (precisa subir o backend com `LIA_JD_ENRICHMENT_TIMEOUT_S=0.001`).

**Bootstrap do `lia-backend`** (canônico em `scripts/dev-up.sh`): aguarda `fuser 8001/tcp` esvaziar (até 10s) antes de bindar, eliminando a race com `fuser -k` que causava `EADDRINUSE :8001` em restarts rápidos.

> **Aviso operacional (Task #1079):** os workflows do Replit `lia-backend`, `pw-cenario-A/B/C` ainda contêm os comandos *antigos* (race-prone). A reconfiguração programática via `configureWorkflow` está bloqueada pelo bug do contador de workflow-limit (os 4 `mockup-sandbox: Component Preview Server` managed-by-artifact contam dobrado, levando o counter a `11/10`). Como mitigação: os comandos **canônicos** estão em `scripts/dev-up.sh` e `plataforma-lia/scripts/run-pw-cenario-{a,b,c}.sh`; rode-os via `bash` que o comportamento é o desejado. Quando a plataforma corrigir o counter (ou um operador remover manualmente um mockup-sandbox no painel), o próximo agente pode `configureWorkflow` cada um dos quatro nomes para apontar para o respectivo wrapper. Workflow `pw-cenario-A` foi removido durante a tentativa de re-add e não pôde ser restaurado pelo mesmo bug — invocar via `bash plataforma-lia/scripts/run-pw-cenario-a.sh`.
