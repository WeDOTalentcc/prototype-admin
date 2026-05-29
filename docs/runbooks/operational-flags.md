# Operational Flags & Environment Reference

**Última atualização:** 2026-05-16 (extraído de `replit.md` para reduzir bloat do README canônico)
**Escopo:** flags de compliance/emergency, Redis encryption, ambiente E2E (Playwright + dev-up.sh).

---

## 1. Redis Encryption (`REDIS_ENCRYPTION_KEY`) — obrigatório em prod

Plataforma usa Fernet (cryptography lib) para encriptar PII em Redis: sessões, candidate_list_store, fairness cache, voice transcripts. **`REDIS_ENCRYPTION_KEY`** deve estar setado em `production` e `staging`.

- Default `app.shared.security.redis_crypto.RedisCrypto` é fail-OPEN (plaintext) se key ausente — para gradual rollout em dev.
- Em prod: `app/main.py:lifespan` levanta `RuntimeError` no boot se key vazia (R-001 do plano de remediação, finding F-049).

Gerar key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Setar via Doppler (preferido) ou env var direto. Validação cobre `production`, `prod` e `staging`; `development` mantém posture fail-OPEN com warning.

---

## 2. Compliance Bypass Flags (R-007 — emergency only)

| Flag | Efeito |
|---|---|
| `LIA_ALLOW_NON_COMPLIANT_DOMAINS=1` | Bypassa ComplianceDomainPrompt (FairnessGuard + PII + PromptInjection + FactCheck) em domains |
| `LIA_ALLOW_NON_COMPLIANT_AGENTS=1` | Bypassa LangGraphReActBase compliance em agents (PII/Fairness/Audit em agent layer) |
| `LIA_DISABLE_C3B=1` | **KILL SWITCH** da camada C3b inteira (PII strip + FairnessGuard L3 + FactCheck + Audit) — passthrough total |
| `LIA_ALLOW_REGISTRY_DRIFT=1` | Permite class_path inválido em agents_registry (R-004 emergency rollback only) |
| `LIA_AGENT_TENANT_STRICT=false` | **(inversa)** Default: `true` em prod/staging, `false` em dev. Quando `false` em prod, `TenantAwareAgentMixin` opera em fail-OPEN — agentes voltam a degradar silenciosamente. Origem do bug "LIA pergunta company_id no chat". Em prod, deixar `true` (ou ausente). |
| `LIA_WIZARD_LLM_GATES=true` | **(T2 / Task #1085 + GA Task #1130)** Liga o gate LLM-based nos **4 gates HITL** do wizard (`jd_enrichment`, `competency`, `wsi_questions`, `review`) — substitui o classifier brittle keyword-based de `domain.py::_route_by_stage` por classificador Pydantic-validado (Claude Haiku, temp=0). Allowlists POR GATE em `wizard_gate_classifier.py::STAGE_ALLOWLISTS`: `jd_enrichment` (T2: 5 intents), `competency` (T4 #1086: 4 intents), `wsi_questions` (T5 #1087: 6 intents), `review` (T6 #1088: 4 intents — `publish_now` exige **dual-confirmation SOX** via `pending_publish_confirmation` + TTL 300s, gera 2 audit rows correlatas via `trace_id` com `confirmation_method=chat` e depois `=dual`). **Default pós-GA Task #1130: ON em TODOS os ambientes** (dev/staging/prod). Override `LIA_WIZARD_LLM_GATES=0` reservado para rollback emergencial. Tombstone dos `route_after_*` keyword-based em `domain.py` agendado para 2026-09-01. Timeout: `LIA_WIZARD_GATE_CLASSIFIER_TIMEOUT_S` (default 5s). Modelo: `LIA_WIZARD_GATE_CLASSIFIER_MODEL` (default vem de `app.shared.llm_models.CANONICAL_HAIKU_MODEL`). Resolve bug "wizard repete `preciso aprovação` 4× ignorando `manda bala`/`tá liberado`/`fica bom`" nas 4 etapas. Sentinelas: `tests/integration/agents/test_wizard_gate_engine_t2.py` (jd), `test_wizard_gate_competency_t4.py`, `test_wizard_gate_wsi_questions_t5.py`, `test_wizard_gate_review_t6.py`. Eval gates: `eval/golden/wizard_conversational_hitl.jsonl` (20 cenários), `wizard_gate_competency.jsonl` (5), `wizard_gate_wsi_questions.jsonl` (5), `wizard_gate_review.jsonl` (7, threshold 0.85). E2E: `plataforma-lia/e2e/tests/wizard/11-conversational-hitl.spec.ts`. Mutação de state é **determinística** (mapeia `intent` ∈ allowlist → fields fixos); `conversational_reply` do LLM nunca é executado nem usado como controle de fluxo. FairnessGuard L1 roda ANTES do classifier em todos os gates. Audit row por gate (`decision_type=wizard_step_completed`, `agent_name=wizard_<stage>_classifier`). |
| `LIA_WIZARD_FALLBACK_LLM_DISABLED=1` | **(T3 / Task #1089)** Desliga a chamada LLM cheap (Haiku) em `_generate_fallback_reply` (`wizard_session_service.py`) — útil em testes offline / cenários sem rede. Quando ON, o fallback do wizard devolve direto a mensagem hard-prefixada `[ATENÇÃO: estado inconsistente — contate suporte] …` em vez de tentar o LLM. Default: OFF. Modelo: `LIA_WIZARD_FALLBACK_MODEL` (default `claude-3-5-haiku-20241022`). Timeout: `LIA_WIZARD_FALLBACK_TIMEOUT_S` (default 3s). O dict canned `_STAGE_DEFAULTS` foi REMOVIDO em favor deste path fail-loud (log error + Sentry + audit `decision_type=wizard_fallback_invoked` + Prometheus counter via `WizardFallbackTracker`). Sentinela arquitetural: `tests/integration/agents/test_wizard_no_canned_fallback_t3.py` veta a reintrodução do dict ou de qualquer literal canned ("preciso da sua aprovação", "Captei a vaga", "Vaga em criação", "Vaga criada com sucesso"). |
| `LIA_WIZARD_SUPERVISOR_CLASSIFIER=true` | **(T1.1 / Task #1127)** Liga o **supervisor pre-graph** do wizard de criação de vaga (`WizardSupervisorClassifier` — Haiku, Pydantic+allowlist, sync). Classifica cada turno em 6 intents canônicos (`create_new \| resume_draft \| edit_published \| meta_question \| exit_wizard \| continue_current`) ANTES do `JobCreationGraph` ser invocado. Short-circuit determinístico para `meta_question` (resposta via `wizard_meta_question_helper`) e `exit_wizard` (mensagem educada); demais intents caem no fluxo legacy. Default: ON em dev/test, OFF em prod/staging até GA. Fail-OPEN em qualquer erro (caller cai em `continue_current` ⇒ fluxo legacy intacto). Mutação de state pelo supervisor: ZERO. Modelo: `LIA_WIZARD_SUPERVISOR_MODEL` (default `CANONICAL_HAIKU_MODEL`). Timeout: `LIA_WIZARD_SUPERVISOR_TIMEOUT_S` (default 5s). Telemetria: Prometheus `lia_wizard_supervisor_intent_total{intent,stage}` + audit `decision_type=wizard_supervisor_routed` (SOX 7y). Sentinela: `tests/integration/agents/test_wizard_supervisor_t1127.py`. Eval gate: `eval/golden/wizard_supervisor_routing.jsonl` (10 cenários, threshold 0.85). Dashboard Grafana: `ops/grafana/lia-wizard-dashboard.json`; runbook: `docs/runbooks/wizard-observability.md`. Ver `docs/architecture/wizard-flow.md` §12. |
| `LIA_DISABLE_COMPANY_AUDIT=1` | **(PR4 / Task #1004)** Desliga o wrapper `audit_company_change` em todas as save tools de `company_settings` (`save_company_field`, `save_company_section`, `import_workforce_plan`, `save_hiring_policy`, `import_benefits_from_data`, `check_company_completeness`). Default: OFF (fail-CLOSED **outbox de duas fases**: emite intent `decision="initiated"` em `__aenter__` — falha aqui aborta o bloco antes de qualquer mutação; emite outcome `completed`/`failed`/`blocked_fairness`/`exception`/`read` em `__aexit__` com `before`/`after`/`target_id` capturados via setters; falha no outcome levanta `RuntimeError` para o caller). Cada save canônico produz **2 audit rows** correlatas via `trace_id` (decision_type=`company_settings_change`, retenção SOX 7 anos). Quando ON, viola Inegociável #6 (auditabilidade SOX/ISO 27001 / EU AI Act) e os saves passam a ser invisíveis ao trail de audit corporativo. Usar APENAS em rollback emergencial se o storage de `audit_logs` estiver bloqueando saves. |

**Em produção:** apenas para rollback emergencial. Quando ON:
- `app/main.py` lifespan loga **CRITICAL** no startup com lista agregada das flags ativas;
- Sentry `capture_message` (level=error) em prod;
- Endpoint `/api/v1/health/compliance/bypass-status` exposes em runtime (canary deve alertar quando `warning_count > 0`).

**Default:** tudo OFF. Ver `.env.example` seção *"COMPLIANCE / EMERGENCY FLAGS"*. Origem: R-007 do plano de remediação, finding F-053.

---

## 3. Ambiente E2E (Task #1079)

A suíte Playwright (`pw-cenario-A → D`) reusa o `dev-server` já em pé — nenhum cenário spawna seu próprio webServer.

| Variável | Default | Efeito |
|---|---|---|
| `PW_REUSE_SERVER` | `1` (reusa) | Quando `0`, força `playwright.config.ts` a iniciar `npm run dev` próprio em :5000. Em Replit, com `dev-server` rodando como workflow, deixar default — caso contrário causa `EADDRINUSE :5000`. |

**Bootstrap único** (devs locais e CI): `./scripts/dev-up.sh` sobe Redis + `lia-backend` (FastAPI :8001) + `dev-server` (Next.js :5000) em ordem com healthcheck entre cada etapa. Idempotente: pula serviços já saudáveis. Use `--no-fe` quando o workflow `dev-server` do Replit já gerencia o frontend.

**Wrappers de cenário** em `plataforma-lia/scripts/run-pw-cenario-{a,b,c,reset}.sh` invocam o canônico `run-pw-cenario.sh <label> <spec>`, que: (1) espera o frontend responder em 120s antes de chamar `pnpm playwright test`; (2) faz warmup de `/pt` e `/pt/chat` para evitar cold-compile do Next/Turbopack; (3) exporta `PW_REUSE_SERVER=1`. Os workflows `pw-cenario-A/B/C` apontam para esses wrappers; `pw-cenario-D` mantém seu próprio bootstrap inline (precisa subir o backend com `LIA_JD_ENRICHMENT_TIMEOUT_S=0.001`). O wrapper `run-pw-cenario-reset.sh` (Task #1134, label `pw-cenario-reset`) roda o sentinela `15-nova-conversa-reset.spec.ts` da Task #1128 — sem workflow nativo enquanto o bug do counter de workflow-limit não for destravado; invocar via `bash plataforma-lia/scripts/run-pw-cenario-reset.sh`.

**Warmup em duas etapas (Task #1173) — por que `page.goto('/pt')` deixava de estourar 90s.** Em container Replit frio, os cenários (`pw-cenario-B/C/D`) falhavam na primeira navegação com timeout de 90s + "Failed to fetch" / 502, mesmo com o curl de warmup tendo passado em <1s logo antes. **Root cause:** o curl só busca o HTML, o que força o `next dev --turbopack` a compilar a *rota do servidor* — mas NÃO os dezenas de chunks JS client-side que o Chromium headless pede em seguida (dynamic imports do `UnifiedChat`, locale routing). Na primeira navegação real do teste, esses chunks ainda estão compilando e o dev-server responde 502, derrubando o `goto`. **Fix:** o `run-pw-cenario.sh` agora roda 2 etapas de warmup — (1) curl (compila a rota), (2) **`node scripts/pw-warmup.mjs`** dirige um Chromium headless real (mesmos args da `playwright.config.ts`) por `/pt` e `/pt/chat`, esperando o textbox do chat aparecer, o que força a compilação de TODOS os chunks lazy e deixa o cache do Turbopack quente. Best-effort (sai 0 mesmo em falha parcial). Como rede de segurança adicional, `goToChatHome` (`e2e/tests/wizard/01-helpers.ts`) reenvia o `page.goto('/pt')` até 3× (60s cada) — um 502 transitório no primeiro contato recompila e a tentativa seguinte pega os bundles quentes, falhando só por motivo real de produto. Para rodar o warmup browser isolado: `cd plataforma-lia && node scripts/pw-warmup.mjs [baseUrl]`.

**Bootstrap do `lia-backend`** (canônico em `scripts/dev-up.sh`): aguarda `fuser 8001/tcp` esvaziar (até 10s) antes de bindar, eliminando a race com `fuser -k` que causava `EADDRINUSE :8001` em restarts rápidos.

> **Aviso operacional (Task #1079):** os workflows do Replit `lia-backend`, `pw-cenario-A/B/C` ainda contêm os comandos *antigos* (race-prone). A reconfiguração programática via `configureWorkflow` está bloqueada pelo bug do contador de workflow-limit (os 4 `mockup-sandbox: Component Preview Server` managed-by-artifact contam dobrado, levando o counter a `11/10`). Como mitigação: os comandos **canônicos** estão em `scripts/dev-up.sh` e `plataforma-lia/scripts/run-pw-cenario-{a,b,c}.sh`; rode-os via `bash` que o comportamento é o desejado. Quando a plataforma corrigir o counter (ou um operador remover manualmente um mockup-sandbox no painel), o próximo agente pode `configureWorkflow` cada um dos quatro nomes para apontar para o respectivo wrapper. Workflow `pw-cenario-A` foi removido durante a tentativa de re-add e não pôde ser restaurado pelo mesmo bug — invocar via `bash plataforma-lia/scripts/run-pw-cenario-a.sh`.

**Wave 16-20 (Task #1131)** — 5 specs novos cobrindo intents do `WizardSupervisorClassifier`. Rodar via:

```bash
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-16 e2e/tests/wizard/16-vaga-nova-do-zero.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-17 e2e/tests/wizard/17-retomada-draft.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-18 e2e/tests/wizard/18-edicao-publicada.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-19 e2e/tests/wizard/19-meta-question-global.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-20 e2e/tests/wizard/20-exit-wizard-clean.spec.ts
```

## Task #1161 — Checkpointer async (LangGraph)

> Detalhamento completo em [`task-1161-three-bugs.md`](./task-1161-three-bugs.md) §Bug B (root cause REAL).

A factory `lia_agents_core.checkpointer.get_checkpointer()` agora aplica um
guard `_supports_async(saver)`: se o saver retornado herda `aget_tuple` do
stub abstrato `BaseCheckpointSaver` (caso da classe sync `PostgresSaver`),
em DEV cai para `MemorySaver`/`InMemorySaver` (suporta async); em
`APP_ENV in {"production","staging"}` levanta `RuntimeError` exigindo
migração para `AsyncPostgresSaver`.

**Por quê.** O wizard `aresume_with_message` faz
`await self._graph.ainvoke(Command(resume=...))`. O `AsyncPregelLoop.__aenter__`
chama `await checkpointer.aget_tuple(...)`. Sem o guard, o stub abstrato
disparava `NotImplementedError` silenciado pelo `_emit_silent_fallback`
do `wizard_session_service` — o usuário via apenas a mensagem genérica
de fallback. Sentinela: `tests/integration/agents/test_checkpointer_async_support_t_1161.py`.

