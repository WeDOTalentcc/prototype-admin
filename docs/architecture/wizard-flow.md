# Fluxo do Wizard de Criação de Vagas

> Mapa canônico do wizard de criação de vagas da Plataforma LIA, com nós
> reais do `JobCreationGraph` (LangGraph), gates HITL, integração com
> `TenantAwareAgentMixin`, classificador conversacional LLM e bugs
> históricos. **Source of truth atualizado em 2026-05-15** após auditoria
> profunda + canonical-fix do `IntakeExtractor`.

> ⚠ Este documento substitui versões anteriores que descreviam dois
> wizards convivendo (`JobWizardGraph` legacy + `WizardReActAgent`) e um
> grafo fictício de 6 nós (`intent_classifier → field_extractor → tool_router
> → tool_executor → response_generator → stage_transition`). Nenhuma dessas
> peças corresponde ao código real. **`JobWizardGraph` está deprecated**
> (Task #1084 / D8 da auditoria 2026-05-14). O fluxo ativo hoje é
> exclusivamente o `JobCreationGraph` linear de 11 nós descrito abaixo.

---

## 1. Visão geral

| Conceito | Implementação canônica |
|---|---|
| Entry point HTTP | `POST /api/v1/chat` (REST) **ou** `WS /api/v1/ws/chat/{session_id}` (WebSocket) |
| Pin de sessão wizard | `wizard_session_pin` Tier 0.5 do `CascadedRouter` (force `active_domain="wizard"` se há checkpoint aberto) |
| Orquestrador | `app/orchestrator/main_orchestrator.py` (Phase 1.4 — wizard_session_pin único) |
| Serviço de sessão | `app/domains/job_creation/services/wizard_session_service.py::WizardSessionService` |
| Grafo principal | `app/domains/job_creation/graph.py::create_job_creation_graph` (11 nós lineares) |
| Agente ReAct (T-D piloto) | `app/domains/job_management/agents/wizard_react_agent.py::WizardReActAgent` (`tenant_strict_override=True`) |
| Persistência de estado | `lia_agents_core.checkpointer.get_checkpointer` (PostgresSaver → MemorySaver fallback dev) |
| Gates HITL canônicos | `app/domains/job_creation/services/wizard_gate_service.py::WizardGateService` (Task #1084) |
| Classificador conversacional HITL | `wizard_gate_classifier` (Task #1085, ON em dev/test, OFF em prod até GA — feature flag `LIA_WIZARD_LLM_GATES`) |
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
WizardSessionService.process_message(session_id, message, ...)
   │ 1. derive_thread_id(company_id, session_id) → "wiz-{token8}-{session_id}"
   │ 2. _build_state(...)  →  CompanyId.parse  →  fail-closed em strict
   │ 3. ManagerPreferencesService.apply_to_state()  ←  LL-2 (NÃO em intake_node)
   ▼
JobCreationGraph.compile(checkpointer).ainvoke(state, config={"thread_id":...})
   │
   ▼
intake → jd_enrichment → bigfive → salary → competency → wsi_questions
       → eligibility → review → publish → calibration → handoff → END
```

---

## 2. Os 11 nós do `JobCreationGraph`

Source: `lia-agent-system/app/domains/job_creation/graph.py` (4600 linhas).
Linhas exatas conferidas em 2026-05-15.

| # | Nó | Linha | Função | HITL | Compliance |
|---|---|---|---|---|---|
| 1 | `intake_node` | 444 | Parse de `user_query` via `IntakeExtractor` (LLM Claude → regex fallback). Emite `parsed_title/seniority/department/location/model` + `pipeline_template` determinístico (`_suggest_pipeline_template`). | — | — |
| 2 | `jd_enrichment_node` | 561 | Enriquecimento da JD via LLM. **L1** `FairnessGuard.check(raw_input)`; **L2** `strip_pii_for_llm_prompt`; **L3** `FairnessGuard.check(enriched_text)`. Fallback determinístico `_fallback_enrichment` por timeout (`LIA_JD_ENRICHMENT_TIMEOUT_S`). Inclui o **input-thin guard** (Task #1096 — ver §4.1). | **#1** | FG L1+L2+L3 + audit EU AI Act |
| 3 | `bigfive_node` | ≈700 | Big Five mapeado da JD. FG pre + PII strip. Timeout `LIA_BIGFIVE_TIMEOUT_S`. | — | FG pre + PII |
| 4 | `salary_node` | ≈830 | Faixa salarial via mercado. Re-pergunta de empresa **NÃO** acontece (regressão B4 protegida pelo pin). Timeout `LIA_SALARY_TIMEOUT_S`. | — | — |
| 5 | `competency_node` | ≈940 | Competências (rota condicional para `wsi_questions` ou pula). | — | — |
| 6 | `wsi_questions_node` | ≈1050 | Geração das 6 perguntas WSI. FG pre (L4 question guard) + PII strip. Timeout `LIA_WSI_QUESTIONS_TIMEOUT_S`. | **#2** | FG L4 + PII |
| 7 | `eligibility_node` | ≈1230 | Critérios não invasivos por LGPD. | — | — |
| 8 | `review_node` | ≈1330 | Consolida pacote para revisão antes do publish. | **#3** | — |
| 9 | `publish_node` | ≈1410 | Cria a vaga via `JobCreationAPIClient` (Rails). Idempotente. | **#4** | Audit EU AI Act |
| 10 | `calibration_node` | ≈1640 | Calibração pós-publish (weights por tenant). | — | — |
| 11 | `handoff_node` | ≈1750 | Encerra sessão, libera checkpoint. | — | — |

### 2.1 Edges (`create_job_creation_graph`, ≈L1900)

```
START → intake → jd_enrichment
              ↳ route_after_jd: bigfive | intake | END
bigfive → salary → competency
              ↳ route_after_competency: wsi_questions | eligibility
wsi_questions
              ↳ route_after_questions: eligibility
eligibility → review
              ↳ route_after_review: publish | review
publish
              ↳ route_after_publish: calibration | END
calibration
              ↳ route_after_calibration: handoff | END
handoff → END
```

Entry point: `intake`. Checkpointer: `get_checkpointer()` (Postgres → Memory fallback em dev).

---

## 3. Gates HITL e classificador conversacional

Os 4 pontos HITL (`#1 jd_enrichment`, `#2 wsi_questions`, `#3 review`, `#4 publish`) foram unificados sob **um único entry point canônico**:

```
WizardGateService.resume_gate(thread_id, pending_id, decision, ...)
                                                       ↑
                                                       │
   ┌───────────────────────────────────────────────────┴─┐
   │                                                     │
WS  agent_chat_ws.py (resume_domain=="wizard")    REST  /api/v1/wizard/hitl/*
```

- **Task #1084 (D8 fix):** `WizardGateService` com idempotência CAS Redis (`wizard:gate:resolved:{gate_id}`, TTL 24h). Chamar `resume_gate` 2× com mesmo `gate_id` retorna `cached=True` na 2ª, 1× engine, **1** audit row. Timeout NÃO cacheia (permite retry).
- **Task #1085 (T2):** `wizard_gate_classifier` LLM-based substitui o classifier brittle keyword-based em `jd_enrichment`. Usa Claude Haiku (`temp=0`, allowlist `approve | reject_with_feedback | provide_new_content | ask_question | off_topic`), Pydantic-validated. Mutação determinística — `intent` ∈ allowlist mapeia para fields fixos do state. **`conversational_reply` do LLM nunca é usado como controle de fluxo.** FG L1 roda antes do classifier. Audit row por gate. Feature flag: `LIA_WIZARD_LLM_GATES` (ON dev/test, OFF prod até GA).
- **Sentinela:** `tests/integration/agents/test_wizard_gate_engine_t2.py`. Eval gate: `eval/golden/wizard_conversational_hitl.jsonl` (5 cenários). E2E: `plataforma-lia/e2e/tests/wizard/11-conversational-hitl.spec.ts`.

### 3.1 Fallback determinístico

`WizardSessionService._generate_fallback_reply` chama Claude Haiku quando o estado fica inconsistente — **sem** dict canned (Task #1089 / T3 removeu `_STAGE_DEFAULTS`). Falhas geram audit `decision_type=wizard_fallback_invoked` + Prometheus counter via `WizardFallbackTracker`. Sentinela arquitetural: `tests/integration/agents/test_wizard_no_canned_fallback_t3.py` (veta a reintrodução de literais canned).

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

**Sintoma observado pelo usuário:** ao escrever no chat:
1. "vamos abrir uma vaga"
2. "onde esta o painel a direita?"
3. "desenvolvedor python senior"
4. "o que voce precisa?"

A LIA respondeu **o mesmo template canned** nas 4 mensagens:
> "Para começar a criação da vaga, preciso de mais contexto. Você pode (a) colar a descrição da vaga (JD) aqui no chat, (b) anexar um arquivo no painel à direita, ou (c) começar respondendo no painel — me diga título do cargo, senioridade e principais responsabilidades."

**Diagnóstico — DOIS bugs encadeados:**

#### Bug A — `IntakeExtractor` quebrado em duplo

`lia-agent-system/app/domains/job_creation/services/intake_extractor.py`

1. **Sub-bug A1 (import path errado + função inexistente):** `_get_llm` importava `from app.shared.services.tenant_llm_context import get_llm_for_current_tenant`. Path **errado** (correto: `app.shared.tenant_llm_context`, sem `.services`) **e** função **inexistente** (renomeada para `get_claude_model_for_tenant` em refactor passado). O `try/except` engolia o `ModuleNotFoundError` como warning e caía sempre no regex fallback.
2. **Sub-bug A2 (schema drift):** `graph.py:488-494::intake_node` lia `extraction.parsed_title`, `.parsed_seniority`, `.confidence`, `.source` direto. O `IntakeExtractor.extract()` retorna um `JobIntakePayload` (canônico em `intake_extractor.py:97`) cuja interface real é `.title.value`, `.title.source`, `.overall_confidence`. `AttributeError` engolido pelo `try/except` fail-open. **`parsed_title` nunca era setado no state**, mesmo para inputs triviais como "Desenvolvedor Python Senior".

**Fix canônico (canonical-fix Phase 4 — sem wrapper, na fonte):**
- `intake_extractor.py:362-414` — restaura a intenção original: tenta `get_claude_model_for_tenant()` (tenant-specific Claude), cai para `ChatAnthropic` global se tenant não tem custom key, regex só como último recurso.
- `graph.py:488-518` — lê corretamente do `JobIntakePayload` via helper `_val(field_name)` que retorna `field.value` ou `None`. `intake_source` lê `extraction.title.source` (`"llm"` / `"regex"` / `"user_text"` / etc.).

#### Bug B — `input-thin guard` dependente de Bug A

`lia-agent-system/app/domains/job_creation/graph.py:616-672` (Task #1096 — guarda introduzida para evitar enriquecer "lixo" com LLM).

A guarda dispara quando **TODAS** estas são `True`:
```
not jd_enriched ∧ not right_panel_form ∧ not attached_file_text
∧ not parsed_title ∧ raw_input_len < 100
```

Como Bug A garantia `parsed_title=None` para sempre, a guarda disparava em **toda** turn curta, **inclusive** quando o input era um título de cargo válido (`"desenvolvedor python senior"` = 27 chars, sem regex match `vaga|posição|cargo`).

**Fix canônico:** já consertado no Bug A — com o `IntakeExtractor` voltando a chamar o LLM, `parsed_title` é extraído corretamente para inputs colloquial e a guarda só dispara para inputs que **realmente** são intent-puro sem material aproveitável (ex: "vamos abrir uma vaga" sozinho).

### 5.2 Limitações conhecidas e dívidas remanescentes

| Item | Severidade | Origem | Plano |
|---|---|---|---|
| **Guard estática vs intent classifier** | ~~Médio~~ **RESOLVIDO** | Task #1096 → Task #1098 → Task #1123 | **#1098 resolveu:** `IntakeIntentClassifier` (Haiku) roda no primeiro turno do `intake_node`. **#1123 estendeu para `jd_enrichment_node`:** classifier roda ANTES do guard estático, em qualquer comprimento de mensagem (`_classifier_eligible` removeu dependência de `raw_len<100`). Guard estático é now **last-resort** (`_guard_eligible`: dispara só quando classifier devolve `None` ou conf<0.7 E `raw_len<100`). Cobertura: `test_jd_enrichment_classifier_first.py` (6 cenários) + `wizard_conversational_resilience.jsonl` (11 cenários). |
| **Template menciona "painel à direita" inexistente** | Médio | Task #1096 | A `data.message` da guarda assume painel renderizado; se o FE não monta o painel, recrutador fica perdido (caso real do print de 2026-05-15). Solução: tornar a mensagem condicional ao `right_panel_form` schema disponível, ou mover a sugestão para botões/chips que o FE renderiza. |
| **D6 — `_suggest_pipeline_template` retorna lista completa** | Baixa | Auditoria 2026-05-14 | Frontend pode mostrar opções A-E mesmo quando o sugerido é "intern" — validar UX. |
| **D2 — domain split confuso** | Baixa | Auditoria 2026-05-14 | Graph vive em `app/domains/job_creation/`, agente em `app/domains/job_management/`. Funciona; é dívida de naming. |

---

## 6. Verificação T-A → T-F

| Task | Aplicação | Status |
|---|---|---|
| **T-A** | `WizardSessionService._build_state` valida `company_id` via `CompanyId.parse`. `_heal_legacy_demo_company_id` reconcilia legacy demo IDs. | ✅ |
| **T-B (#970)** | `WizardReActAgent` é o piloto canônico do `TenantAwareAgentMixin` com `tenant_strict_override=True` (linha 71). | ✅ |
| **T-C (#969)** | Snippet `tenant_context_snippet` consumido pelo wizard contém `sector/industry_segment/plan/timezone/headcount_range/lia_persona_override`. CHECK `ck_companies_id_format_canonical` espelha `CompanyId.parse`. | ✅ |
| **T-D (#971)** | Wizard incluso no inventário de 16 ReActAgents canônicos. | ✅ |
| **T-E (#972)** | `wizard_no_tenant_leak.jsonl` (12 cenários B1/B2/B3/B4 — Task #1052). Threshold 0.85. Espelha T-E. | ✅ |
| **T-F** | `WizardSessionService.process_message` propaga `tenant_context_snippet` (idempotente, R4 da T-F). | ✅ |

---

## 7. Eval gates e sentinelas

### 7.1 Eval gates online (live, contra backend up)

| Gate | Cenários | Threshold | Comando |
|---|---|---|---|
| `eval/golden/wizard_no_tenant_leak.jsonl` (Task #1052) | 12 (B1×3 single + B2/B3/B4×3 multi) | 0.85 | `python -m eval.eval_runner --transport ws --dataset eval/golden/wizard_no_tenant_leak.jsonl && python -m eval.eval_runner --gate eval/golden/wizard_no_tenant_leak.jsonl` |
| `eval/golden/wizard_pipeline_template.jsonl` (Task #1058) | 7 (4 ramos + retomada + fallback) | 0.85 | mesma sintaxe com este dataset |
| `eval/golden/wizard_conversational_hitl.jsonl` (Task #1085) | 5 (HITL conversacional) | 0.85 | mesma sintaxe |
| `eval/golden/wizard_conversational_resilience.jsonl` (Task #1123) | 11 (meta-questions, off-topic, ask_clarification — jd/competency/wsi/review) | 0.85 | mesma sintaxe |

CI: `.github/workflows/wizard-eval-gates.yml` (Task #1063 + #1064 + #1123) sobe Postgres + Redis + lia-backend, semeia Demo Company + demo user, e roda `--transport ws` (WS-aware desde Task #1064 / D7). **Fail-CLOSED** em `push`; required-check no `main`. Input default: `gates=leak,template,hitl,resilience`.

### 7.2 Sentinelas offline (pytest, sem backend)

- `test_wizard_session_continuity_t1080.py` — pin handler-level + thread_id puro
- `test_tenant_aware_rollout_t_d.py` — inventário 16 ReActAgents
- `test_wizard_pipeline_template_emission_t1055.py` — emissão `pipeline_template`
- `test_wizard_step_audit_t1061.py` — audit por step (D3 fix)
- `test_wizard_node_timeouts_t1062.py` — timeouts por env (D4 fix)
- `test_wizard_hitl_unified_contract.py` — `WizardGateService` (D8 fix)
- `test_wizard_gate_engine_t2.py` — classifier LLM Task #1085
- `test_wizard_no_canned_fallback_t3.py` — anti-canned fallback Task #1089
- `test_no_hardcoded_haiku_model_t1123.py` — proíbe literal Haiku fora de `app/shared/llm_models.py` (canonical Haiku/Sonnet module)
- `test_jd_enrichment_classifier_first.py` — 6 cenários garantindo que `jd_enrichment_node` é classifier-first (independente de `raw_len`)
- `test_wizard_meta_question_resilience.py` — gates HITL respondem meta/off-topic via Sonnet helper; fail-OPEN para classifier reply

### 7.3 E2E Playwright (`plataforma-lia/e2e/tests/wizard/`)

- `01-vaga-tecnica.spec.ts` (cenário A) — Backend Pleno técnico
- `03-vaga-executiva.spec.ts` (cenário B) — Diretor de Marketing
- `08-hitl-correcao.spec.ts` (cenário C) — correção HITL
- `09-edge-cases.spec.ts` (cenário D) — fallback timeout + cancel mid-wizard
- `10-session-continuity.spec.ts` — reload mid-wizard + anti-pergunta de empresa
- `11-conversational-hitl.spec.ts` — Task #1085 conversational HITL
- `15-conversational-resilience.spec.ts` — Task #1123 meta-questions (curta + longa ≥100 chars) + off-topic redirect

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
  "requires_approval": <bool — true em HITL>
}
```

Componentes principais:
- `WizardPipelineTemplateCard.tsx` — consome `data.suggestions_data.pipeline_template` (`data-testid="wizard-template-card"`).
- `useWizardChatCards.ts` — orquestra cards.
- `useSettingsConversational.ts` — bridge chat ↔ settings (Task T6 #993).

---

## 11. Filosofia conversacional (Task #1123)

A LIA é **conversacional por design** — o wizard NÃO é um formulário
com validação de campos, é uma sessão de trabalho com o recrutador. As
três invariantes que estruturam essa filosofia:

1. **Classifier-first em TODA boundary de entrada.** Tanto o `intake_node`
   (Task #1098) quanto o `jd_enrichment_node` (Task #1123) chamam o
   `IntakeIntentClassifier` (Haiku) **antes** de qualquer guard estático
   ou de qualquer LLM caro (Layer 2 enrichment). Os 4 gates HITL
   (jd_gate, competency_gate, wsi_questions_gate, review_gate) chamam o
   `WizardGateClassifier` (Haiku, Task #1085). Guard estático
   (`_guard_eligible`) é **last-resort** — só dispara quando o
   classifier devolveu `None` ou conf<0.7 E mensagem é curta (<100 chars).
   **O classifier NÃO é gateado por `raw_len`** — pergunta meta longa
   também passa por ele (bug raiz Task #1123).

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
   `test_no_hardcoded_haiku_model_t1123.py` veta o literal fora do
   módulo canônico.

### Anti-patterns que esta filosofia previne

- LIA pergunta `company_id` / nome / setor / plano em texto livre
  (regressão B1 — coberta por `wizard_no_tenant_leak.jsonl` + Task #1123
  cenários).
- LIA enriquece uma pergunta meta longa como se fosse JD (bug raiz
  Task #1123 — coberto por `test_jd_enrichment_classifier_first.py`
  cenário 2).
- LIA repete a mesma resposta canned ("preciso de aprovação", "deseja
  aprovar?") quando recrutador acabou de pedir outra coisa (cobertura:
  `wizard_conversational_hitl.jsonl` + `wizard_conversational_resilience.jsonl`).
- LIA trava em loop quando recrutador insiste na mesma pergunta (cobertura:
  `WCR-09-loop-detection-meta-repeated` — `last_turns` permite ao
  Sonnet helper oferecer ângulo diferente).

---

## 9. Operação

### 9.1 Feature flags relevantes

| Flag | Default | Efeito |
|---|---|---|
| `LIA_AGENT_TENANT_STRICT` | `true` em prod/staging, `false` em dev | Quando `false`, mixin opera em fail-OPEN. **Wizard ignora** essa flag (`tenant_strict_override=True` hardcoded). |
| `LIA_WIZARD_LLM_GATES` | ON dev/test, OFF prod/staging | Liga o classifier LLM em `jd_enrichment` HITL #1 (Task #1085). |
| `LIA_WIZARD_FALLBACK_LLM_DISABLED` | OFF | Desliga LLM cheap em `_generate_fallback_reply` (testes offline). |
| `LIA_JD_ENRICHMENT_TIMEOUT_S` | 12s (0.001 em pw-cenario-D) | Timeout do enriquecimento JD. |
| `LIA_BIGFIVE_TIMEOUT_S` | 10s | Timeout do bigfive. |
| `LIA_WSI_QUESTIONS_TIMEOUT_S` | 20s | Timeout WSI. |
| `LIA_SALARY_TIMEOUT_S` | 10s | Timeout salary. |
| `LIA_DISABLE_COMPANY_AUDIT` | OFF | Emergency rollback de audit (Task #1004). |
| `LIA_WIZARD_INTAKE_CLASSIFIER_ENABLED` | ON | Liga o `IntakeIntentClassifier` (Task #1098) — usado em `intake_node` e `jd_enrichment_node` (Task #1123). |
| `LIA_WIZARD_META_HELPER_MODEL` | `CANONICAL_SONNET_MODEL` | Override do modelo do `wizard_meta_question_helper` (Task #1123). |
| `LIA_WIZARD_META_HELPER_TIMEOUT_S` | 6s | Timeout sync do Sonnet helper meta. Falha → fail-OPEN para classifier reply. |

**Modelos LLM canônicos** (Task #1123): NUNCA hardcode literal de modelo
fora de `lia-agent-system/app/shared/llm_models.py`. Importe
`CANONICAL_HAIKU_MODEL` / `CANONICAL_SONNET_MODEL`. Sentinela:
`test_no_hardcoded_haiku_model_t1123.py` (CI fail).

### 9.2 Runbooks

- `docs/runbooks/missing_tenant_context.md` — on-call para o bug "LIA pergunta company_id".
- `docs/architecture/tenant-context-history.md` — histórico T-A → T-F.

### 9.3 Onde olhar quando o wizard falha

1. **Logs `lia-backend`:** procurar `[JobCreation:intake]`, `[JobCreation:jd_enrichment]`, `[IntakeExtractor]`, `[WizardSession]`.
2. **Sintomas comuns:**
   - `[JobCreation:jd_enrichment] input-thin guard fired` repetido com `has_title=False` → suspeitar de Bug A regression (intake não setando `parsed_title`).
   - `[IntakeExtractor] tenant LLM ... unavailable` → checar import path em `_get_llm` e exports de `app.shared.tenant_llm_context`.
   - `[JobCreation:intake] F3-1 extraction failed (fail-open): 'X' object has no attribute 'Y'` → schema drift entre `IntakeExtractor` e `intake_node` consumer (Bug A2 pattern).
3. **Reproduzir offline:** rodar uma das sentinelas pytest listadas em §7.2 antes de tocar em código.

---

## 10. Histórico recente do documento

- **2026-05-15 (Task #1123)** — wizard conversational resilience. (1) Canonical Haiku/Sonnet module + sentinela. (2) `jd_enrichment_node` classifier-first (guard estático vira last-resort). (3) `wizard_meta_question_helper` (Sonnet sync, fail-OPEN) plugado em ask_question/off_topic/ask_clarification dos 4 gates HITL. (4) `last_turns` plumbed em ambos classifiers + 4 YAMLs. (5) Eval gate `wizard_conversational_resilience.jsonl` (11 cenários, threshold 0.85) wired em `.github/workflows/wizard-eval-gates.yml`. (6) E2E `15-conversational-resilience.spec.ts` (3 cenários: meta curta, meta longa ≥100 chars, off-topic). Nova §11 "Filosofia conversacional".
- **2026-05-15** — reescrita completa após auditoria + canonical-fix do Bug A (intake import + schema drift). Removida narrativa fictícia dos 6 nós (`intent_classifier`/`field_extractor`/etc.) que nunca existiram. Removida menção ao `JobWizardGraph` legacy (deprecated desde Task #1084). Adicionada §5 "Bugs históricos" com diagnóstico do template-repetido-4× e §9.3 "Onde olhar quando o wizard falha".
- **2026-05-14** — auditoria profunda em `docs/audits/wizard-job-creation-2026-05.md` (Task #1058) — base desta reescrita.
- **Anterior** — versões descrevendo dois wizards convivendo (`JobWizardGraph` + `WizardReActAgent`). Obsoleto.
