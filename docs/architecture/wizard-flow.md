# Fluxo do Wizard de Criação de Vagas

> Mapa canônico do wizard de criação de vagas da Plataforma LIA, com nós
> reais do `JobCreationGraph` (LangGraph), gates HITL com `interrupt()`,
> integração com `TenantAwareAgentMixin`, classifiers conversacionais
> LLM (intake / gates / supervisor pre-graph) e bugs históricos.
> **Source of truth atualizado em 2026-05-18** após Task #1161 (3 bugs
> bloqueantes E2E) + auditoria exaustiva do código vs. doc.

> ⚠ Este documento substitui versões anteriores que descreviam dois
> wizards convivendo (`JobWizardGraph` legacy + `WizardReActAgent`) e um
> grafo fictício de 6 nós (`intent_classifier → field_extractor → tool_router
> → tool_executor → response_generator → stage_transition`). Nenhuma dessas
> peças corresponde ao código real. **`JobWizardGraph` está deprecated**
> (Task #1084 / D8 da auditoria 2026-05-14). O fluxo ativo hoje é
> exclusivamente o `JobCreationGraph` em `app/domains/job_creation/graph.py`
> (4867 linhas) com **15 nós** = 11 funcionais + 4 gate nodes HITL.

---

## 1. Visão geral

| Conceito | Implementação canônica |
|---|---|
| Entry point HTTP | `POST /api/v1/chat` (REST) **ou** `WS /api/v1/ws/chat/{session_id}` (WebSocket) |
| Pin de sessão wizard | Handler-level (Task #1080) em `agent_chat_ws.py`/`agent_chat_sse.py` ANTES do `CascadedRouter` |
| Orquestrador | `app/orchestrator/main_orchestrator.py` (Phase 1.4 — wizard_session_pin único) |
| Serviço de sessão | `app/domains/job_creation/services/wizard_session_service.py::WizardSessionService` |
| Supervisor pre-graph | `services/wizard_supervisor_classifier.py` (Task #1127, OFF em prod/staging por default — ver §10) |
| Grafo principal | `app/domains/job_creation/graph.py::JobCreationGraph` (Singleton, L4748) — 15 nós |
| Gate service unificado | `services/wizard_gate_service.py::WizardGateService` (Task #1084) |
| Classifier por gate HITL | `services/wizard_gate_classifier.py::WizardGateClassifier` (Task #1085, **default ON** pós-GA #1130) |
| Intake intent classifier | `services/intake_intent_classifier.py::IntakeIntentClassifier` (Task #1098) |
| Agente ReAct (T-D piloto) | `app/domains/job_management/agents/wizard_react_agent.py::WizardReActAgent` (L71: `tenant_strict_override=True`) |
| Persistência de estado | `lia_agents_core.checkpointer.get_checkpointer` — Postgres async em prod / `MemorySaver` em dev (Task #1161 Bug B — ver §3.2) |
| Bridge FE | `plataforma-lia/src/components/unified-chat/wizard/*` consumindo `ws_stage_payload.data.*` |

### 1.1 Como uma turn chega ao grafo

```
Browser (chat input)
   │
   ▼
WS /api/v1/ws/chat/{session_id}  ──►  agent_chat_ws.py
   │                                       │ (pin handler-level Task #1080)
   │                                       │ if active_domain∈{auto,recruiter_assistant,""}
   │                                       │   AND is_wizard_session_active(company_id, session_id):
   │                                       │     active_domain = "wizard"
   ▼
WizardSessionService.process_message(session_id, message, ...)   ← L792
   │ 1. _run_supervisor(...)  → short-circuit em meta_question/exit_wizard (Task #1127)
   │ 2. derive_thread_id(company_id, session_id) → "wiz-{token8}-{session_id}"  ← L294
   │ 3. _build_state(...) → CompanyId.parse → fail-closed em strict (L432)
   │ 4. ManagerPreferencesService.apply_to_state()  ←  LL-2 (NÃO em intake_node)
   ▼
JobCreationGraph.invoke / aresume_with_message(thread_id, message)  ← L4765 / L4839
   │  (compile(checkpointer) acontece uma vez no Singleton)
   ▼
intake → jd_enrichment → jd_gate (HITL #1) → bigfive → salary
       → competency → competency_gate (HITL #2) → wsi_questions
       → wsi_questions_gate (HITL #3) → eligibility → review
       → review_gate (HITL #4) → publish → calibration → handoff → END
```

---

## 2. Os 15 nós do `JobCreationGraph`

Source: `lia-agent-system/app/domains/job_creation/graph.py` (4867 linhas).
Line numbers conferidas em 2026-05-18.

### 2.1 Nós funcionais (11)

| # | Nó | Linha | Função | Compliance |
|---|---|---|---|---|
| 1 | `intake_node` | L498 | Parse de `user_query` via `IntakeExtractor` (LLM Claude → regex fallback). Emite `parsed_title/seniority/department/location/model` + `pipeline_template` determinístico (`_suggest_pipeline_template`). Classifier-first via `IntakeIntentClassifier` (Task #1098). | — |
| 2 | `jd_enrichment_node` | L636 | Enriquecimento da JD via LLM. **L1** `FairnessGuard.check(raw_input)`; **L2** `strip_pii_for_llm_prompt`; **L3** `FairnessGuard.check(enriched_text)`. Fallback determinístico `_fallback_enrichment` por timeout (`LIA_JD_ENRICHMENT_TIMEOUT_S=12s`). Inclui o **input-thin guard** classifier-first (Task #1096 → #1098 → #1123 — ver §5.1). | FG L1+L2+L3 + audit EU AI Act |
| 3 | `bigfive_node` | L1166 | Big Five mapeado da JD. FG pre + PII strip. Timeout `LIA_BIGFIVE_TIMEOUT_S=10s`. | FG pre + PII |
| 4 | `salary_node` | L1434 | Faixa salarial via mercado. Re-pergunta de empresa **NÃO** acontece (regressão B4 protegida pelo pin). Timeout `LIA_SALARY_TIMEOUT_S=10s`. | — |
| 5 | `competency_node` | L1607 | Competências (rota condicional para `wsi_questions` ou pula). | — |
| 6 | `wsi_questions_node` | L1717 | Geração das 6 perguntas WSI. FG pre (L4 question guard) + PII strip. Timeout `LIA_WSI_QUESTIONS_TIMEOUT_S=20s`. | FG L4 + PII |
| 7 | `eligibility_node` | L2076 | Critérios não invasivos por LGPD. | — |
| 8 | `review_node` | L2122 | Consolida pacote para revisão antes do publish. | — |
| 9 | `publish_node` | L2190 | Cria a vaga via `JobCreationAPIClient` (Rails). Idempotente. | Audit EU AI Act |
| 10 | `calibration_node` | L2438 | Calibração pós-publish (weights por tenant). | — |
| 11 | `handoff_node` | L2552 | Encerra sessão, libera checkpoint. | — |

### 2.2 Gate nodes HITL (4) — `interrupt()` canônico

Os 4 gates HITL são **nós distintos** no grafo (não branches dentro do nó funcional). Cada um chama `langgraph.types.interrupt()` para pausar e devolve controle via `JobCreationGraph.aresume_with_message`.

Cada gate tem allowlist **stage-specific** definida em `services/wizard_gate_classifier.py::STAGE_ALLOWLISTS` (L43-L80):

| # | Gate node | Linha | `interrupt()` | Allowlist real do stage |
|---|---|---|---|---|
| #1 | `jd_gate_node` | L2643 | L2716 | `approve / reject_with_feedback / provide_new_content / ask_question / off_topic` |
| #2 | `competency_gate_node` | L2999 | L3039 | `select_compact / select_full / ask_question / undecided` (T4 / Task #1086 — escolha modo de triagem) |
| #3 | `wsi_questions_gate_node` | L3356 | L3418 | `approve_all / regenerate_all / edit_specific_question / add_question / remove_question / ask_question` (T5 / Task #1087) |
| #4 | `review_gate_node` | L3842 | L3910 | `publish_now / request_changes / ask_clarification / configure_destinations` (T6 / Task #1088 — `publish_now` exige dupla confirmação chat + TTL 5min) |

Cada gate roda o `WizardGateClassifier` (Haiku, allowlist + Pydantic + temp=0) quando `LIA_WIZARD_LLM_GATES` está ON (default desde Task #1130 — ver §11.1). Mutação determinística — o `intent` da allowlist mapeia para fields fixos do state. `conversational_reply` do LLM NUNCA é usado como controle de fluxo. Audit row por gate via `WizardGateService._emit_gate_audit` (L366, `decision_type="wizard_step_completed"`).

### 2.3 Edges (`create_job_creation_graph`, L4596-L4736)

```
START → intake (entry_point, L4596)
intake → jd_enrichment (L4599)

# Caminho ON (use_llm_gates=True, default pós-#1130):
jd_enrichment      → jd_gate            (L4605)
jd_gate            → route_after_gate              (L3285): bigfive | intake (provide_new_content) | END (ask_question/off_topic/fairness)
competency         → competency_gate    (L4635)
competency_gate    → route_after_competency_gate   (L3269): wsi_questions (mode∈{compact,full}) | END (ask_question/undecided/fairness)
wsi_questions      → wsi_questions_gate (L4660)
wsi_questions_gate → route_after_wsi_questions_gate (L3723): eligibility | END
review             → review_gate        (L4691)
review_gate        → route_after_review_gate       (L4364): publish (dual-confirm + ready) | jd_enrichment/salary/wsi_questions/eligibility (request_changes target_section) | END (ask_clarification/configure_destinations/1ª publish_now/fairness)

# Caminho OFF (use_llm_gates=False, rollback emergencial — TBR 2026-09-01):
jd_enrichment → route_after_jd (L3315 / wiring L4616): bigfive | intake | END
competency    → route_after_competency (L3347 / L4645): wsi_questions | END
wsi_questions → route_after_questions (L3742 / L4671): eligibility | END
review        → route_after_review (L3759 / L4706): publish | review | END

# Comum aos dois caminhos:
bigfive → salary (L4627) → competency (L4628)
eligibility → review (L4682)
publish     → route_after_publish (L4716): calibration | END
calibration → route_after_calibration (L4726): handoff | END
handoff → END (L4736)
```

Entry point: `intake`. Checkpointer: `get_checkpointer()` (ver §3.2).

> **Sobre as duas vias `_gate` vs `route_after_*`:** o keyword-based `route_after_*` em `domain.py` está em **deprecation window** (TBR 2026-09-01 conforme comentário em `graph.py:114-122`). Pós-GA #1130 a flag `LIA_WIZARD_LLM_GATES` é ON por default em todos os ambientes e o caminho dos `_gate` é o único caminho real em produção. Os `add_conditional_edges` keyword-based só rodam se a flag for OFF (rollback emergencial).

---

## 3. Gates HITL, gate service, checkpointer e bootstrap LLM

### 3.0 Entry point unificado dos gates

```
WizardGateService.resume_gate(thread_id, pending_id, decision, ...)   ← L466
                                                       ↑
                                                       │
   ┌───────────────────────────────────────────────────┴─┐
   │                                                     │
WS  agent_chat_ws.py (resume_domain=="wizard")    REST  /api/v1/wizard/hitl/*
```

- **Task #1084 (D8 fix):** `WizardGateService` com idempotência CAS Redis (`wizard:gate:resolved:{gate_id}`, TTL 24h). Chamar `resume_gate` 2× com mesmo `gate_id` retorna `cached=True` na 2ª, 1× engine, **1** audit row. Timeout NÃO cacheia (permite retry).
- **Task #1085 (T2):** `WizardGateClassifier` LLM-based substitui o classifier brittle keyword-based em `jd_enrichment`. Usa Claude Haiku (`temp=0`, allowlist enforced post-hoc), Pydantic-validated. FG L1 roda antes do classifier. Audit row por gate via `_emit_gate_audit` (L366).
- **Task #1118 (resume via interrupt):** `_resume_engine` (L414) delega para `JobCreationGraph.aresume_with_message` (L4839, que usa `Command(resume=...)`). Eval gate `wizard_resume_via_interrupt.jsonl` exige zero repetição de pergunta + EXATAMENTE 4 audit rows `wizard_gate_service/resume_gate` em uma única `conversation_id`.
  - **Gatilho obrigatório de CI:** em PRs que toquem os 4 gate_nodes ou `WizardGateService._resume_engine`, rodar `bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1118 e2e/tests/wizard/14-resume-via-interrupt.spec.ts` (asserta zero repetição de pergunta + EXATAMENTE 4 audit rows `wizard_gate_service/resume_gate` em uma única `conversation_id`) **e** o eval gate `wizard_resume_via_interrupt.jsonl`.
- **Sentinelas:** `tests/integration/agents/test_wizard_gate_engine_t2.py` (classifier), `test_wizard_hitl_unified_contract.py` (gate service), `test_wizard_session_continuity_t1080.py` (resume). E2E: `11-conversational-hitl.spec.ts`, `14-resume-via-interrupt.spec.ts`.

### 3.1 Fallback determinístico

`WizardSessionService._generate_fallback_reply` chama Claude Haiku quando o estado fica inconsistente — **sem** dict canned (Task #1089 / T3 removeu `_STAGE_DEFAULTS`). Falhas geram audit `decision_type=wizard_fallback_invoked` (L197) + Prometheus counter via `WizardFallbackTracker`. Sentinela arquitetural: `tests/integration/agents/test_wizard_no_canned_fallback_t3.py`.

### 3.2 Checkpointer (Task #1161 Bug B — root cause real do `NotImplementedError`)

`libs/agents-core/lia_agents_core/checkpointer.py::get_checkpointer()` é a única forma canônica de obter o saver do LangGraph para o wizard.

| Ambiente | Comportamento |
|---|---|
| `APP_ENV ∈ {production, staging}` | `PostgresSaver` obrigatório; **`RuntimeError`** se indisponível OU se o saver não sobrescreve `aget_tuple` (Bug B). Exige migração para `AsyncPostgresSaver`. |
| `APP_ENV` qualquer outro (dev/test) | `PostgresSaver` preferido; fallback `MemorySaver` (= `InMemorySaver`, suporta async) com WARNING. |

**Root cause descoberto (addendum Bug B):** o traceback completo (habilitado pela fix B em §5.3) revelou que `PostgresSaver` sync herda `aget_tuple` do stub abstrato `BaseCheckpointSaver` → `await self._graph.ainvoke(Command(resume=...))` em `aresume_with_message` disparava `NotImplementedError` no `AsyncPregelLoop.__aenter__`, silenciado pelo `_emit_silent_fallback`. O sintoma visível era o wizard repetir a mesma pergunta gate após resume.

**Fix canônico:** helper `_supports_async(saver)` (L56) detecta se `aget_tuple` foi sobrescrito em algum lugar da MRO além da `BaseCheckpointSaver`. Em dev cai para `MemorySaver`; em prod-like levanta `RuntimeError` curto e específico exigindo `AsyncPostgresSaver`.

**Sentinela offline:** `tests/integration/agents/test_checkpointer_async_support_t_1161.py` (3 testes: AST helper exists, AST guard chamado, runtime saver suporta `aget_tuple`).

### 3.3 Anthropic base_url (Task #1161 Bug A)

`app/shared/llm_bootstrap.py::_inject_anthropic_env` (L112) patch global de `anthropic.Anthropic.__init__` / `AsyncAnthropic.__init__`.

**Bug histórico:** o helper só injetava `base_url` quando o caller NÃO passava `api_key`. Callsites tipo `ChatAnthropic(api_key=tenant_key)` (LangChain wrapper) construíam `Anthropic(api_key=...)` com o key explícito, então o proxy local `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` era silenciosamente ignorado — todas as chamadas iam para `api.anthropic.com` direto (401 em dev/staging que dependem do modelfarm).

**Fix canônico (L121-L135):** `api_key` continua gated em ausência do caller, mas `base_url` injeta **incondicionalmente** sempre que o env var está configurado. Em prod o env é unset → no-op. Em dev/staging aponta para o modelfarm proxy → todo client Anthropic roteia através dele.

**Sentinela offline:** `tests/integration/llm/test_anthropic_base_url_injection_t_1161.py` inclui AST guard `test_inject_helper_uses_unconditional_base_url`.

**Addendum Task #1164 (Bug D — root cause real do "IA degradada").** A fix de Bug A não cobria callsites do `ChatAnthropic` porque `langchain_anthropic.ChatAnthropic._client_params` (L1617 em `chat_models.py`) SEMPRE faz `"base_url": self.anthropic_api_url`, com o default vindo de `from_env(["ANTHROPIC_API_URL","ANTHROPIC_BASE_URL"], default="https://api.anthropic.com")`. Em dev/staging nenhum desses env vars está setado → kwargs chega no patch com `base_url="https://api.anthropic.com"` já populado → o guard `"base_url" not in kwargs` pulava a injeção → `create_tracked_llm`/`get_claude_model_for_tenant`/`IntakeExtractor._get_llm` saíam batendo direto na API pública com a wrapper key do modelfarm (401). Os classifiers (supervisor/gates/intake/meta_helper) escapavam porque criam `anthropic.Anthropic(...)` direto sem `base_url`. **Fix Task #1164:** novo helper `_is_default_anthropic_base_url(value)` enumera os defaults upstream (`https://api.anthropic.com` com/sem trailing slash) e o guard ficou `if current is None or _is_default_anthropic_base_url(current): kwargs["base_url"] = base_url`. Override explícito do caller com URL não-default continua respeitado. **Sentinelas:** `tests/integration/llm/test_anthropic_base_url_injection_t_1164.py` (5 testes — reprodução do kwargs do LangChain wrapper, variante trailing slash, preservação de override não-default, coverage runtime do helper, AST guard exigindo chamada de `_is_default_anthropic_base_url`).

---

## 4. Continuidade de sessão e pin (Task #1080)

`thread_id` é derivado por uma **única função pura**:

```python
app.shared.sessions.derive_thread_id(company_id, session_id) -> "wiz-{token8}-{session_id}"
```

- Sem honor de `msg["thread_id"]` custom.
- Sem Redis marker (`lia:wizard:active:*` foi extinto).
- Sem heurística `_candidate_thread_ids`.
- Sem Tier 0.5 hardcoded no `CascadedRouter`.

"Esta sessão é wizard?" é detectado por `app.shared.sessions.is_wizard_session_active(company_id, session_id)`, que lê o checkpoint LangGraph e retorna True iff existe estado E `current_stage != "completed"` (fail-open em outage).

O **pin** vive nos handlers de transport (`agent_chat_ws.py` e `agent_chat_sse.py`) **antes** da chamada ao `CascadedRouter`. Quando o FE não enviou `domain` explícito (`active_domain ∈ {"auto","recruiter_assistant",""}`) e a sessão tem checkpoint aberto, força `active_domain="wizard"` e pula o roteamento normal. O `main_orchestrator` (REST) opera com a mesma checagem via `WizardSessionService.is_session_active`.

**Sentinelas:** `tests/integration/agents/test_wizard_session_continuity_t1080.py` (S1 pureza, S2 anti-honor msg.thread_id, S3 fail-open, S4 AST router-clean, S5 wrappers delegam, S6 handlers donos do pin). E2E: `plataforma-lia/e2e/tests/wizard/10-session-continuity.spec.ts`.

---

## 5. Bugs históricos e correções canônicas

### 5.1 Bug do "template repetido 4×" (corrigido 2026-05-15)

**Sintoma observado:** ao escrever no chat "vamos abrir uma vaga" / "onde está o painel à direita?" / "desenvolvedor python senior" / "o que você precisa?", a LIA respondia o mesmo template canned 4×.

**Diagnóstico — DOIS bugs encadeados:**

#### Bug A — `IntakeExtractor` quebrado em duplo

1. **Sub-bug A1 (import path errado + função inexistente):** `_get_llm` importava `from app.shared.services.tenant_llm_context import get_llm_for_current_tenant`. Path **errado** (correto: `app.shared.tenant_llm_context`, sem `.services`) **e** função **inexistente** (renomeada para `get_claude_model_for_tenant` em refactor passado). O `try/except` engolia o `ModuleNotFoundError` como warning e caía sempre no regex fallback.
2. **Sub-bug A2 (schema drift):** `graph.py::intake_node` lia `extraction.parsed_title`, `.parsed_seniority` direto. O `IntakeExtractor.extract()` retorna um `JobIntakePayload` cuja interface real é `.title.value`, `.title.source`, `.overall_confidence`. `AttributeError` engolido pelo `try/except` fail-open. **`parsed_title` nunca era setado no state**.

**Fix canônico (canonical-fix Phase 4 — na fonte):**
- `intake_extractor.py:362-414` — restaura a intenção original: tenta `get_claude_model_for_tenant()`, cai para `ChatAnthropic` global, regex só como último recurso.
- `graph.py::intake_node` lê corretamente do `JobIntakePayload` via helper `_val(field_name)`. `intake_source` lê `extraction.title.source`.

#### Bug B — `input-thin guard` dependente de Bug A

`jd_enrichment_node` (Task #1096) disparava guard quando `not parsed_title ∧ raw_input_len < 100`. Como Bug A garantia `parsed_title=None` sempre, a guarda disparava em **toda** turn curta — inclusive títulos válidos como `"desenvolvedor python senior"`. **Fix:** consertado via Bug A (intake voltou a setar `parsed_title`).

### 5.2 Resolução classifier-first (Tasks #1098 + #1123)

- **Task #1098 + Task #1123:** `IntakeIntentClassifier` (Haiku, sync, Pydantic-validado) roda em `jd_enrichment_node` (`graph.py:727-751`), NÃO em `intake_node`. O `intake_node` continua sendo só o parse do `IntakeExtractor`; o classifier de intent vive no nó seguinte, gateado por `_classifier_eligible` (sem dependência de `raw_len`) e roda ANTES do guard estático em qualquer comprimento de mensagem.
- Refina em 4 buckets canônicos: `provides_jd_intent | meta_question | intent_only | off_topic`. Fail-OPEN — qualquer falha (flag OFF, sem API key, timeout, schema inválido, off-allowlist) devolve `None` e cai no guard estático (`_guard_eligible`, last-resort: só dispara quando classifier devolveu `None` ou conf<0.7 E `raw_len<100`).
- `conversational_reply` do LLM NUNCA é usado como controle de fluxo — só como texto exibido. Mutação de state é determinística por intent.
- Sentinelas: `test_jd_enrichment_classifier_first.py` (6 cenários) + eval `wizard_conversational_resilience.jsonl` (11 cenários).

### 5.3 Task #1161 — 3 bugs E2E bloqueantes (MERGED 2026-05-18)

Três regressões resolvidas com sentinelas offline AST-validadas. **O traceback completo habilitado pela própria fix B foi o que revelou o root cause real do Bug B (addendum em §3.2).**

| Bug | Sintoma | Fix canônico | Sentinela |
|---|---|---|---|
| **A** — Anthropic 401 com `ChatAnthropic+api_key=` | Modelfarm bypassed; LLM calls 401 em dev/staging | `_inject_anthropic_env` injeta `base_url` SEMPRE (fora do gate api_key) — ver §3.3 | `test_anthropic_base_url_injection_t_1161.py` (AST guard `test_inject_helper_uses_unconditional_base_url`) |
| **B** — `NotImplementedError` silenciado em `aresume_with_message` | Wizard repetia pergunta após resume; silencioso | (1) `WizardSessionService.process_message` chama `logger.exception(...)` + `sentry_sdk.capture_exception(...)` ANTES de `_emit_silent_fallback(...)` (L872-884). (2) Root cause: `PostgresSaver` sync herda `aget_tuple` do stub abstrato → fix em `lia_agents_core/checkpointer.py::_supports_async` — ver §3.2 | `test_wizard_resume_traceback_t_1161.py` (AST exige ordem dos statements) + `test_checkpointer_async_support_t_1161.py` (3 testes) |
| **C** — `/company/culture-*` 500 vazando `str(e)` | `ResponseValidationError` 500 + information disclosure | (1) `CompanyCultureProfileBase` ganhou `field_validator(mode="before")` em 7 campos `list[str]` via helper `_normalize_list_of_strings` (coerce dict→str via code/name/label/value, drop None/empty). (2) 19 catches em 2 arquivos substituíram `detail=str(e)` por `detail="internal error"` | `test_culture_no_internal_leak_t_1161.py` (AST HTTP + coverage real do validator) |

**Runbook completo:** [`docs/runbooks/task-1161-three-bugs.md`](../runbooks/task-1161-three-bugs.md).

### 5.4 Limitações conhecidas e dívidas remanescentes

| Item | Severidade | Origem | Plano |
|---|---|---|---|
| **D6 — `_suggest_pipeline_template` retorna lista completa** | Baixa | Auditoria 2026-05-14 | Frontend pode mostrar opções A-E mesmo quando o sugerido é "intern" — validar UX. |
| **D2 — domain split confuso** | Baixa | Auditoria 2026-05-14 | Graph vive em `app/domains/job_creation/`, agente em `app/domains/job_management/`. Funciona; é dívida de naming. |
| **TBR 2026-09-01 — keyword-based `route_after_*` em `domain.py`** | Baixa | Task #1130 GA | Remover após 30 dias de baseline sem regressão (comentário em `graph.py:114-122`). |

---

## 6. Verificação T-A → T-F

| Task | Aplicação | Status |
|---|---|---|
| **T-A** | `WizardSessionService._build_state` valida `company_id` via `CompanyId.parse`. `_heal_legacy_demo_company_id` reconcilia legacy demo IDs. | ✅ |
| **T-B (#970)** | `WizardReActAgent` é o piloto canônico do `TenantAwareAgentMixin` com `tenant_strict_override=True` (L71). | ✅ |
| **T-C (#969)** | Snippet `tenant_context_snippet` consumido pelo wizard contém `sector/industry_segment/plan/timezone/headcount_range/lia_persona_override`. CHECK `ck_companies_id_format_canonical` espelha `CompanyId.parse`. | ✅ |
| **T-D (#971)** | Wizard incluso no inventário de 16 ReActAgents canônicos. Sentinela `test_tenant_aware_rollout_t_d.py`. | ✅ |
| **T-E (#972)** | `wizard_no_tenant_leak.jsonl` (12 cenários B1/B2/B3/B4 — Task #1052). Threshold 0.85. | ✅ |
| **T-F** | `WizardSessionService.process_message` e `WizardSupervisorClassifier` usam `resolve_tenant_snippet_for_non_react(ctx, *, agent_name=..., company_id_raw=...)` — assinatura canônica T-F. | ✅ |

---

## 7. Eval gates e sentinelas

### 7.1 Eval gates online (live, contra backend up)

| Gate | Cenários | Threshold | Task |
|---|---|---|---|
| `eval/golden/wizard_no_tenant_leak.jsonl` | 12 (B1×3 single + B2/B3/B4×3 multi) | 0.85 | #1052 |
| `eval/golden/wizard_pipeline_template.jsonl` | 7 (4 ramos + retomada + fallback) | 0.85 | #1058 |
| `eval/golden/wizard_conversational_hitl.jsonl` | 5 (HITL conversacional) | 0.85 | #1085 |
| `eval/golden/wizard_conversational_resilience.jsonl` | 11 (meta-questions, off-topic, ask_clarification — jd/competency/wsi/review) | 0.85 | #1123 |
| `eval/golden/wizard_supervisor_routing.jsonl` | 10 cenários × 6 intents | 0.85 | #1127 |
| `eval/golden/wizard_resume_via_interrupt.jsonl` | resume com `Command(resume=...)` — zero repetição + 4 audit rows | 0.85 | #1118 |

Comando padrão: `python -m eval.eval_runner --transport ws --dataset <path> && python -m eval.eval_runner --gate <path>`.

CI: `.github/workflows/wizard-eval-gates.yml` (Task #1063 + #1064 + #1123) sobe Postgres + Redis + lia-backend, semeia Demo Company + demo user, e roda `--transport ws` (WS-aware desde Task #1064 / D7). **Fail-CLOSED** em `push`; required-check no `main`.

### 7.2 Sentinelas offline (pytest, sem backend)

| Sentinela | Cobertura |
|---|---|
| `test_wizard_session_continuity_t1080.py` | pin handler-level + thread_id puro (S1-S6) |
| `test_tenant_aware_rollout_t_d.py` | inventário 16 ReActAgents (Task #971) |
| `test_wizard_pipeline_template_emission_t1055.py` | emissão `pipeline_template` |
| `test_wizard_step_audit_t1061.py` | audit por step (D3 fix) |
| `test_wizard_node_timeouts_t1062.py` | timeouts por env (D4 fix) |
| `test_wizard_hitl_unified_contract.py` | `WizardGateService` (D8 fix) |
| `test_wizard_gate_engine_t2.py` | classifier LLM Task #1085 |
| `test_wizard_no_canned_fallback_t3.py` | anti-canned fallback Task #1089 |
| `test_intake_node_schema_contract.py` | schema entre `IntakeExtractor` e `intake_node` (anti-Bug A2 regression) |
| `test_wizard_node_message_invariant.py` | `data.message` obrigatória em todo payload (Task #1099) |
| `test_no_hardcoded_haiku_model_t1123.py` | proíbe literal Haiku fora de `app/shared/llm_models.py` |
| `test_jd_enrichment_classifier_first.py` | 6 cenários classifier-first em jd_enrichment |
| `test_wizard_meta_question_resilience.py` | gates HITL respondem meta/off-topic via Sonnet helper |
| `test_wizard_supervisor_t1127.py` | supervisor pre-graph + allowlist enforcement + carve-out FG |
| **`test_anthropic_base_url_injection_t_1161.py`** | Task #1161 Bug A — AST guard `_inject_anthropic_env` injeta base_url SEMPRE |
| **`test_wizard_resume_traceback_t_1161.py`** | Task #1161 Bug B — AST exige `logger.exception+sentry` antes de `_emit_silent_fallback` |
| **`test_checkpointer_async_support_t_1161.py`** | Task #1161 Bug B — 3 testes (AST helper exists, AST guard chamado, runtime saver suporta `aget_tuple`) |

### 7.3 E2E Playwright (`plataforma-lia/e2e/tests/wizard/`)

| Spec | Cobertura |
|---|---|
| `01-helpers.ts` | helpers compartilhados |
| `02-vaga-tecnica.spec.ts` (cenário A) | Backend Pleno técnico |
| `03-vaga-executiva.spec.ts` (cenário B) | Diretor de Marketing |
| `04-vaga-operacional.spec.ts` | operacional |
| `05-vaga-estagio.spec.ts` | estágio |
| `06-validators-erro.spec.ts` | validators |
| `07-pos-publicacao.spec.ts` | pós-publish |
| `08-hitl-correcao.spec.ts` (cenário C) | correção HITL |
| `09-edge-cases.spec.ts` (cenário D) | fallback timeout + cancel mid-wizard |
| `10-session-continuity.spec.ts` | reload mid-wizard + anti-pergunta de empresa |
| `11-conversational-hitl.spec.ts` | Task #1085 conversational HITL |
| `12-panel-chat-resync.spec.ts` | resync painel ↔ chat |
| `13-hitl-dupla-aprovacao.spec.ts` | idempotência dupla aprovação |
| `14-resume-via-interrupt.spec.ts` | **Task #1118** — resume canônico via `Command(resume=...)`, zero repetição + 4 audit rows |
| `15-conversational-resilience.spec.ts` | Task #1123 meta-questions (curta + longa ≥100 chars) + off-topic redirect |
| `15-nova-conversa-reset.spec.ts` | reset de conversa |
| `16-vaga-nova-do-zero.spec.ts` | Task #1131 — supervisor intent `create_new` |
| `17-retomada-draft.spec.ts` | Task #1131 — supervisor intent `resume_draft` |
| `18-edicao-publicada.spec.ts` | Task #1131 — supervisor intent `edit_published` (defensiva) |
| `19-meta-question-global.spec.ts` | Task #1131 — supervisor intent `meta_question` short-circuit (3 perguntas) |
| `20-exit-wizard-clean.spec.ts` | Task #1131 — supervisor intent `exit_wizard` preserva draft |
| `step1-info-basica.spec.ts` ... `step7-revisao.spec.ts` | specs legacy step-a-step |
| `complete-flow.spec.ts` | fluxo completo de ponta a ponta |
| `wizard-a11y.spec.ts` | acessibilidade |
| `wizard-prv-benefits.spec.ts` | benefícios PRV |

---

## 8. Bridge frontend (`plataforma-lia/src/components/unified-chat/wizard/`)

Cada nó emite um `ws_stage_payload` no formato:

```json
{
  "type": "wizard_stage",
  "stage": "<node_name>",
  "data": {
    "message": "<obrigatório, Task #1099>",
    "...": "campos específicos do nó"
  },
  "completeness": <0-1 do calculate_completeness>,
  "requires_approval": <bool — true em gate_node>
}
```

Componentes principais:
- `WizardPipelineTemplateCard.tsx` — consome `data.suggestions_data.pipeline_template` (`data-testid="wizard-template-card"`).
- `useWizardChatCards.ts` — orquestra cards.
- `useSettingsConversational.ts` — bridge chat ↔ settings (Task T6 #993).

---

## 9. Filosofia conversacional (Task #1123)

A LIA é **conversacional por design** — o wizard NÃO é um formulário
com validação de campos, é uma sessão de trabalho com o recrutador. As
três invariantes que estruturam essa filosofia:

1. **Classifier-first em TODA boundary de entrada.** Tanto o `intake_node`
   (Task #1098) quanto o `jd_enrichment_node` (Task #1123) chamam o
   `IntakeIntentClassifier` (Haiku) **antes** de qualquer guard estático
   ou de qualquer LLM caro. Os 4 gates HITL (`jd_gate`, `competency_gate`,
   `wsi_questions_gate`, `review_gate`) chamam o `WizardGateClassifier`
   (Haiku, Task #1085). Guard estático (`_guard_eligible`) é **last-resort**
   — só dispara quando o classifier devolveu `None` ou conf<0.7 E mensagem
   é curta (<100 chars). **O classifier NÃO é gateado por `raw_len`** —
   pergunta meta longa também passa por ele (bug raiz Task #1123).

2. **Resposta tenant-aware + history-aware em paths "meta".** Para
   `ask_question` / `off_topic` / `ask_clarification`, o gate tenta
   primeiro o `wizard_meta_question_helper` (Sonnet, sync, fail-OPEN),
   que recebe `tenant_context_snippet` + `last_turns` (últimas 3) +
   `stage_description` e devolve resposta rica em 2-4 frases terminada
   em pergunta de continuidade. Falhou? Cai no `output.conversational_reply`
   do classifier. Falhou de novo? Cai no canned do gate. **Em nenhum
   path o state de aprovação muta** — helper é só geração de texto.

3. **Modelos LLM centralizados.** `CANONICAL_HAIKU_MODEL` e
   `CANONICAL_SONNET_MODEL` vivem em `app/shared/llm_models.py`. Literal
   antigo (`claude-3-5-haiku-20241022`) retorna `UNSUPPORTED_MODEL` no
   modelfarm proxy local — qualquer reintrodução faz classifiers
   fail-OPEN silenciosamente. Sentinela CI:
   `test_no_hardcoded_haiku_model_t1123.py`.

### Anti-patterns que esta filosofia previne

- LIA pergunta `company_id` / nome / setor / plano em texto livre
  (regressão B1 — coberta por `wizard_no_tenant_leak.jsonl`).
- LIA enriquece uma pergunta meta longa como se fosse JD (bug raiz
  Task #1123 — coberto por `test_jd_enrichment_classifier_first.py`).
- LIA repete a mesma resposta canned ("preciso de aprovação", "deseja
  aprovar?") quando recrutador acabou de pedir outra coisa.
- LIA trava em loop quando recrutador insiste na mesma pergunta
  (`last_turns` permite ao Sonnet helper oferecer ângulo diferente).

---

## 10. Wizard Supervisor pre-graph (Task #1127)

A partir de Task #1127 todo turno do wizard passa por um **supervisor pre-graph** antes de tocar o `JobCreationGraph`. O supervisor é um classifier LLM (`WizardSupervisorClassifier`, `services/wizard_supervisor_classifier.py`) que decide a INTENÇÃO GLOBAL do recrutador em 6 categorias canônicas (allowlist enforced).

| Intent | Comportamento do caller |
|---|---|
| `meta_question` | **Short-circuit** — `WizardSessionService._run_supervisor` responde via `wizard_meta_question_helper` (Sonnet) e devolve payload `wizard_meta_reply` SEM tocar o graph. Funciona mesmo mid-HITL. |
| `exit_wizard` | **Short-circuit** — emite mensagem educada de despedida (payload `wizard_exit`). NÃO descarta o draft. |
| `continue_current` | DEFAULT. Cai no fluxo legacy (graph). Sem mudança de contrato. |
| `create_new` / `resume_draft` / `edit_published` | Slice T1.1 mantém em `continue_current`-like (passa para o graph). Handlers dedicados nas Tasks #1128+. |

**Contrato de segurança:**
- Pydantic schema + allowlist post-hoc (defense-in-depth). Sentinela `test_wizard_supervisor_t1127.py` veta drift da allowlist.
- Fail-OPEN: qualquer falha devolve `None` → caller cai 100% no fluxo legacy.
- Mutação de state pelo supervisor: ZERO. Apenas roteia.
- `tenant_context_snippet` via `resolve_tenant_snippet_for_non_react(ctx, *, agent_name="wizard_supervisor", company_id_raw=...)`.

**Carve-out de FairnessGuard:** o supervisor pre-graph é um **router de intent**, não um produtor de resposta de produto — por isso **não roda FairnessGuard L1 antes do classifier**. Decisão DELIBERADA documentada na sentinela `test_supervisor_fallback_message_is_not_canned_product_literal`.

**Observabilidade:**
- Prometheus counter `lia_wizard_supervisor_intent_total{intent,stage}` por turno.
- Audit row `decision_type=wizard_supervisor_routed` (SOX 7y) com `intent`, `confidence`, `stage`, `thread_id` em `reasoning` (`wizard_session_service.py:769`).
- Eval gate `wizard_supervisor_routing.jsonl` (10 cenários × 6 intents, threshold 0.85).
- Dashboard Grafana: `ops/grafana/lia-wizard-dashboard.json` (8 painéis, UID `lia-wizard-observability`).
- Runbook: `docs/runbooks/wizard-observability.md`.

---

## 11. Operação

### 11.1 Feature flags relevantes

| Flag | Default | Efeito |
|---|---|---|
| `LIA_AGENT_TENANT_STRICT` | `true` em prod/staging, `false` em dev | Quando `false`, mixin opera em fail-OPEN. **Wizard ignora** essa flag (`tenant_strict_override=True` hardcoded). |
| `LIA_WIZARD_LLM_GATES` | **ON em TODOS os ambientes** (pós-Task #1130 GA) | Liga o classifier LLM nos 4 gates HITL (Task #1085). OFF é rollback emergencial — keyword-based `route_after_*` em `domain.py` é o caminho de fallback (TBR 2026-09-01). |
| `LIA_WIZARD_INTAKE_LLM_CLASSIFIER` | ON em dev, OFF em prod (env-based) | Liga o `IntakeIntentClassifier` (Task #1098) em `intake_node` e `jd_enrichment_node` (Task #1123). |
| `LIA_WIZARD_SUPERVISOR_CLASSIFIER` | ON em dev/test, OFF em prod/staging | Liga o supervisor pre-graph (Task #1127). |
| `LIA_WIZARD_SUPERVISOR_MODEL` | `CANONICAL_HAIKU_MODEL` | Override do modelo do supervisor. |
| `LIA_WIZARD_SUPERVISOR_TIMEOUT_S` | 5s | Timeout sync do supervisor. |
| `LIA_WIZARD_FALLBACK_LLM_DISABLED` | OFF | Desliga LLM cheap em `_generate_fallback_reply` (testes offline). |
| `LIA_WIZARD_META_HELPER_MODEL` | `CANONICAL_SONNET_MODEL` | Override do modelo do `wizard_meta_question_helper` (Task #1123). |
| `LIA_WIZARD_META_HELPER_TIMEOUT_S` | 6s | Timeout sync do Sonnet helper meta. Falha → fail-OPEN para classifier reply. |
| `LIA_JD_ENRICHMENT_TIMEOUT_S` | 12s (0.001 em pw-cenario-D) | Timeout do enriquecimento JD. |
| `LIA_BIGFIVE_TIMEOUT_S` | 10s | Timeout do bigfive. |
| `LIA_WSI_QUESTIONS_TIMEOUT_S` | 20s | Timeout WSI. |
| `LIA_SALARY_TIMEOUT_S` | 10s | Timeout salary. |
| `LIA_DISABLE_COMPANY_AUDIT` | OFF | Emergency rollback de audit (Task #1004). |
| `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` | unset em prod, modelfarm proxy em dev/staging | Task #1161 Bug A — injetado SEMPRE no Anthropic client quando set (§3.3). |

**Modelos LLM canônicos** (Task #1123): NUNCA hardcode literal de modelo
fora de `lia-agent-system/app/shared/llm_models.py`. Importe
`CANONICAL_HAIKU_MODEL` / `CANONICAL_SONNET_MODEL`. Sentinela CI:
`test_no_hardcoded_haiku_model_t1123.py`.

### 11.2 Audit logs `wizard_*`

| `decision_type` | Origem | Quando |
|---|---|---|
| `wizard_step_completed` | `WizardGateService._emit_gate_audit` (L393) | A cada `resume_gate` resolvido (4× por wizard completo). |
| `wizard_fallback_invoked` | `WizardSessionService` (L197) | `_generate_fallback_reply` foi chamado (estado inconsistente). |
| `wizard_supervisor_routed` | `WizardSessionService._run_supervisor` (L769) | Toda turn quando supervisor está ON — `reasoning` carrega `intent`/`confidence`/`stage`/`thread_id`. |

Padrão geral: `actor/action/decision` — ex. `wizard_gate_service/resume_gate:wizard/approved`.

### 11.3 Runbooks

- [`docs/runbooks/task-1161-three-bugs.md`](../runbooks/task-1161-three-bugs.md) — Task #1161 (3 bugs E2E + addendum Bug B root cause).
- [`docs/runbooks/missing_tenant_context.md`](../runbooks/missing_tenant_context.md) — on-call para o bug "LIA pergunta company_id".
- [`docs/runbooks/wizard-observability.md`](../runbooks/wizard-observability.md) — dashboard + 4 alertas (gate latency p95>2s, gate error rate>5%, silent fallback spike, supervisor fallback>5%).
- [`docs/runbooks/operational-flags.md`](../runbooks/operational-flags.md) — todas as flags e bypass switches.
- [`docs/architecture/tenant-context-history.md`](./tenant-context-history.md) — histórico T-A → T-F.

### 11.4 Onde olhar quando o wizard falha

1. **Logs `lia-backend`:** procurar `[JobCreation:intake]`, `[JobCreation:jd_enrichment]`, `[IntakeExtractor]`, `[WizardSession]`, `[Checkpointer]`.
2. **Sintomas comuns:**
   - `[JobCreation:jd_enrichment] input-thin guard fired` repetido com `has_title=False` → suspeitar de Bug A regression (intake não setando `parsed_title`).
   - `[IntakeExtractor] tenant LLM ... unavailable` → checar import path em `_get_llm` e exports de `app.shared.tenant_llm_context`.
   - `[JobCreation:intake] F3-1 extraction failed (fail-open): 'X' object has no attribute 'Y'` → schema drift entre `IntakeExtractor` e `intake_node` consumer (Bug A2 pattern).
   - `[Checkpointer] ... nao implementa aget_tuple` → Task #1161 Bug B regression em prod (precisa `AsyncPostgresSaver`).
   - Wizard repete pergunta de gate após resume → checar se traceback de `aresume_with_message` aparece em `lia-backend-stdout.log` (Task #1161 fix B garante que aparece, NÃO é silenciado).
   - Anthropic 401 em dev/staging → checar se `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` está set E se `_inject_anthropic_env` está sendo chamado (sentinela `test_anthropic_base_url_injection_t_1161.py`).
3. **Reproduzir offline:** rodar uma das sentinelas pytest listadas em §7.2 antes de tocar em código.

---

## 12. Histórico recente do documento

- **2026-05-18 (Task #1161 MERGED + auditoria exaustiva)** — (1) Contagem de nós corrigida: **15** (11 funcionais + 4 gate nodes HITL como nós distintos), não 11. Line numbers reais conferidos no `graph.py` 4867L. (2) Nova §2.2 "Gate nodes HITL" com `interrupt()` location de cada um. (3) Edges §2.3 reescritos para refletir as duas vias (`_gate` ON pós-#1130 vs keyword-based `route_after_*` em deprecation TBR 2026-09-01). (4) Nova §3.2 "Checkpointer" com addendum Bug B root cause (`PostgresSaver` sync herda `aget_tuple` do stub abstrato → `NotImplementedError` silenciado). (5) Nova §3.3 "Anthropic base_url" (Bug A fix). (6) Nova §5.3 com tabela dos 3 bugs do #1161 + sentinelas. (7) `LIA_WIZARD_LLM_GATES` default corrigido para **ON em todos os ambientes** (pós-#1130). (8) Flag `LIA_WIZARD_INTAKE_CLASSIFIER_ENABLED` renomeada para o nome real `LIA_WIZARD_INTAKE_LLM_CLASSIFIER`. (9) Supervisor (§10) reordenado para depois da Filosofia (§9) — numeração consertada (estava §8→§11→§9→§10→§12). (10) §7.2 ganhou 3 sentinelas T_1161 (`test_anthropic_base_url_injection`, `test_wizard_resume_traceback`, `test_checkpointer_async_support`) + 2 esquecidas (`test_intake_node_schema_contract`, `test_wizard_node_message_invariant`). (11) §7.3 ampliado para listar TODAS as 25+ specs E2E reais (antes listava 7), incluindo `14-resume-via-interrupt`, `16/17/18/19/20` da Task #1131. (12) §11.2 nova com tabela de audit decisions reais. (13) §11.4 "onde olhar" ganhou sintomas Bug B / Bug A.
- **2026-05-15 (Task #1123)** — wizard conversational resilience. Canonical Haiku/Sonnet module + sentinela; `jd_enrichment_node` classifier-first; `wizard_meta_question_helper` (Sonnet sync, fail-OPEN); `last_turns` plumbed; eval gate `wizard_conversational_resilience.jsonl` (11 cenários); E2E `15-conversational-resilience.spec.ts`.
- **2026-05-15** — reescrita completa após auditoria + canonical-fix do Bug A (intake import + schema drift). Removida narrativa fictícia dos 6 nós. Removida menção ao `JobWizardGraph` legacy. Adicionada §5 "Bugs históricos".
- **2026-05-14** — auditoria profunda em `docs/audits/wizard-job-creation-2026-05.md` (Task #1058) — base desta reescrita.
- **Anterior** — versões descrevendo dois wizards convivendo (`JobWizardGraph` + `WizardReActAgent`). Obsoleto.
