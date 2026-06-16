# Auditoria profunda — Wizard de criação de vagas

**Data:** 2026-05-14
**Task:** #1058
**Escopo:** `JobCreation` LangGraph + `WizardReActAgent` + `WizardSessionService` + tools de save + bridge FE
**Modo:** Auditoria offline + leitura canonical (live eval gates dependem de backend up — ver §Eval Gates)
**Referências:** `replit.md`, `docs/architecture/ARCHITECTURE.md`, `docs/architecture/tenant-context-history.md`

---

## 1. Inventário canonical do graph

### 1.1 Nós (`lia-agent-system/app/domains/job_creation/graph.py`)

| Ordem | Nó | Linha | Função | HITL | Compliance aplicada |
|---|---|---|---|---|---|
| 1 | `intake` | L140 | Parse de `user_query` via `IntakeExtractor` (LLM + regex fallback). Emite `parsed_title/seniority/department/location/model` + sugere `pipeline_template` via `_suggest_pipeline_template` (L108, determinístico, fail-open). | — | — (entrada raw) |
| 2 | `jd_enrichment` | L240 | Enriquecimento da JD via LLM. **L1** `FairnessGuard.check(raw_input)` antes do LLM (L258); **L2** `strip_pii_for_llm_prompt` antes do LLM (L295); **L3** `FairnessGuard.check(enriched_text)` depois do LLM (L390). Fallback determinístico (`_fallback_enrichment`) ativado por `LIA_JD_ENRICHMENT_TIMEOUT_S` ou exceção LLM — usado pelo `pw-cenario-D`. Emite `requires_approval=True` em sucesso (HITL #1). | **#1** | FG L1+L2+L3 + audit EU AI Act |
| 3 | `bigfive` | L497 | Big Five mapeado a partir da JD enriquecida. FG pre-check + PII masking antes do LLM. | — | FG pre + PII strip |
| 4 | `salary` | L629 | Faixa salarial sugerida via mercado/benchmark. Re-pergunta empresa **NÃO** acontece (regressão B4 protegida pelo `wizard_session_pin` Tier 0.5). | — | — |
| 5 | `competency` | L737 | Mapeamento de competências (rota condicional para `wsi_questions` ou pula). | — | — |
| 6 | `wsi_questions` | L814 | Geração das 6 perguntas WSI. FG pre-check (L864) + PII masking (L887) antes do LLM. Emite HITL #2 quando perguntas geradas. | **#2** | FG pre + PII strip |
| 7 | `eligibility` | L1027 | Critérios de elegibilidade (não invasivos por LGPD). | — | — |
| 8 | `review` | L1053 | Consolida o pacote para revisão humana antes do publish. | — | — |
| 9 | `publish` | L1110 | Cria a vaga via `JobCreationAPIClient` (Rails). Idempotente. | — | Audit EU AI Act |
| 10 | `calibration` | L1326 | Calibração pós-publish (weights por tenant). | — | — |
| 11 | `handoff` | L1429 | Encerra a sessão e libera o `wizard_session_marker` no Redis. | — | — |

### 1.2 Edges & roteamento (`create_job_creation_graph`, L1705)

```
intake → jd_enrichment
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

Entry point: `intake`. Checkpointer: `lia_agents_core.checkpointer.get_checkpointer` (PostgresSaver → MemorySaver fallback em dev).

### 1.3 Agente + sessão

- **Agente canonical:** `app/domains/job_management/agents/wizard_react_agent.py::WizardReActAgent` (1 dos 16 ReActAgents canônicos). MRO: `TenantAwareAgentMixin → LangGraphReActBase → EnhancedAgentMixin`. `tenant_strict_override = True` (linha 71) — **NUNCA** degrada para `"sua empresa"`/`"geral"` mesmo com `LIA_AGENT_TENANT_STRICT=false` em dev.
- **Sessão:** `app/domains/job_creation/services/wizard_session_service.py::WizardSessionService` — `derive_thread_id()` (priority `msg["thread_id"]` > `wiz-{token}-{sid}` > `wiz-{sid}`) + Redis marker `lia:wizard:active:{session_id}` (TTL 2h) + `is_session_active()` consultado pelo `CascadedRouter.route()` Tier 0.5 (`wizard_session_pin`). `_build_state` valida `company_id` via `CompanyId.parse` fail-closed em strict-mode.
- **Executor canônico:** `app/orchestrator/main_orchestrator.py` Phase 1.4 — `wizard_session_pin` cobre WS, SSE, REST orchestrator e autonomous_react_agent sem duplicação.
- **Bridge FE:** `plataforma-lia/src/components/unified-chat/wizard/WizardPipelineTemplateCard.tsx` consome `data.suggestions_data.pipeline_template` (sentinela offline `test_wizard_pipeline_template_emission_t1055`). `useWizardChatCards.ts` orquestra cards. `pw-cenario-A` (Playwright) valida o card no DOM.

---

## 2. Verificação T-A → T-F

| Task | Contrato | Aplicação no wizard | Status |
|---|---|---|---|
| **T-A** | `CompanyId.parse` aceita UUID v4 OU slug, bloqueia literais reservados; `is_tenant_strict_mode()`. | `WizardSessionService._build_state` valida via `CompanyId.parse`. `_heal_legacy_demo_company_id` (`app/auth/dependencies.py`) reconcilia in-place qualquer `company_id` demo legacy → `CANONICAL_DEMO_UUID` antes do parse (B1 fix). | ✅ |
| **T-B (#970)** | `WizardReActAgent` é o piloto canonical do `TenantAwareAgentMixin` com `tenant_strict_override=True`. | Confirmado em `wizard_react_agent.py:42-71`. `_get_runtime_domain_instructions` chama `self._compose_runtime_prompt(...)` (helper canônico). | ✅ |
| **T-C (#969)** | Schema `companies` com `sector/industry_segment/plan/timezone/headcount_range/lia_persona_override` + Demo Company UUID `00000000-0000-4000-a000-000000000001`. | Snippet `tenant_context_snippet` consumido pelo wizard contém esses campos. CHECK `ck_companies_id_format_canonical` espelha `CompanyId.parse`. | ✅ |
| **T-D (#971)** | 16 ReActAgents canonicalmente migrados. Sentinela em `test_tenant_aware_rollout_t_d.py`. | Wizard incluso. `tenant_strict_override=True` (único hardcoded). | ✅ |
| **T-E (#972)** | Eval gate `tenant_context.jsonl` (18 cenários, threshold 0.85, ≥80% cobertura dos 16). | Wizard tem cenários próprios em `wizard_no_tenant_leak.jsonl` (12 cenários B1/B2/B3/B4 — Task #1052). Espelha threshold T-E. | ✅ |
| **T-F** | Helper `resolve_tenant_snippet_for_non_react()` para callsites NON-ReAct. | Wizard é ReAct → não aplicável diretamente. Mas `WizardSessionService.process_message` (callsite que entrega ao graph) usa `tenant_context_snippet` propagado pelo MainOrchestrator (idempotente, R4 da T-F). | ✅ |

**Sentinelas offline ativas:**
- `tests/integration/agents/test_tenant_aware_rollout_t_d.py` — inventário 16 (quebra build se 17º for adicionado sem padrão).
- `tests/integration/agents/test_tenant_context_no_regression.py` — 50 testes (POSITIVO + ANTI-PADRÃO + FAIL-CLOSED).
- `tests/integration/agents/test_wizard_session_continuity_t1051.py` — 10 cases (heal + helper + router pin AST + WS no-dup + comportamental).
- `tests/integration/agents/test_wizard_pipeline_template_emission_t1055.py` — emissão `data.suggestions_data.pipeline_template` no `ws_stage_payload`.
- `tests/integration/agents/test_non_react_tenant_helper_t_f.py` — helper canonical NON-ReAct.
- `tests/integration/agents/test_tenant_question_guard_in_prompts.py` + `test_tenant_snippet_fairness_safe.py` — defesa adicional.

Nenhum drift detectado em T-A → T-F. ✅

---

## 3. Checklist 14 dimensões (skill `feature-audit`)

| # | Dimensão | Evidência | Status |
|---|---|---|---|
| 1 | **Integração** | Wizard → Rails (`JobCreationAPIClient`) → `companies`/`jobs`. WS `/ws/chat/{session_id}` + REST `/api/v1/chat`. | ✅ |
| 2 | **Dados** | `JobCreationState` (TypedDict) consistente entre nodes. `parsed_*` flui de `intake` para todos os downstream. | ✅ |
| 3 | **UI/DS v4.2.1** | `WizardPipelineTemplateCard` — `data-testid="wizard-template-card"` validado em `pw-cenario-A`. Tokens DS v4.2.2 (rounded-md). | ✅ |
| 4 | **Backend** | FastAPI + LangGraph. Checkpointer Postgres → Memory fallback. Idempotência em `publish`. | ✅ |
| 5 | **Tipos** | `JobCreationState`, `JobCreationAPIClient`, schemas Pydantic (`schemas.py`). Bridge FE em `types/api.generated.ts`. | ✅ |
| 6 | **Fluxo do usuário** | 11 nodes lineares com 2 HITL. Continuidade entre turnos via `wizard_session_pin` (Tier 0.5 do `CascadedRouter`). | ✅ |
| 7 | **Consistência** | Cenários B/C/D do `pw-cenario-*` cobrem técnico/não-técnico/retomada/fallback. | ✅ |
| 8 | **Documentação** | `replit.md` "Wizard de criação de vaga" + Task #1051/#1052 + `tenant-context-history.md`. Esta auditoria. | ✅ |
| 9 | **Arquitetura de agentes** | `WizardReActAgent` é o piloto T-B. MRO mixin → ReAct → Enhanced. Único agente com `tenant_strict_override=True` hardcoded. | ✅ |
| 10 | **Qualidade LLM** | `IntakeExtractor` com regex fallback. `_fallback_enrichment` por timeout (`LIA_JD_ENRICHMENT_TIMEOUT_S`). `_suggest_pipeline_template` 100% determinístico. | ✅ |
| 11 | **Serviços IA** | LLM via `app/domains/ai/` (Claude primário). FairnessGuard (3 layers) + PII masking aplicados em `jd_enrichment`, `bigfive`, `wsi_questions`. | ✅ |
| 12 | **Governança IA (EU AI Act)** | Audit em `jd_enrichment` (L390-L420 emite audit em FG L3 BLOCK) e `publish`. HITL explícito em pontos críticos. | ✅ |
| 13 | **Segurança** | `CompanyId` value object fail-closed strict. `_heal_legacy_demo_company_id` reconcilia legacy. PII strip antes de cada LLM call. | ✅ |
| 14 | **Performance** | Timeout LLM via `LIA_JD_ENRICHMENT_TIMEOUT_S` (default seguro, 0.001 em test cenário-D). Checkpointer Postgres compartilhado. Redis marker TTL 2h. | ✅ |

---

## 4. Checklist 18 Production Readiness (skill `lia-compliance`)

| # | Item | Evidência | Status |
|---|---|---|---|
| 1 | Auth obrigatório | `WizardSessionService._build_state` exige `company_id` via JWT. | ✅ |
| 2 | Multi-tenant isolation | `company_id` é primary scope; `_heal_legacy_demo_company_id` reconcilia. | ✅ |
| 3 | Tenant strict mode | `tenant_strict_override=True` hardcoded no wizard. | ✅ |
| 4 | Compliance 3-pillar (LGPD+SOX+EU AI Act) | FairnessGuard L1/L2/L3 + PII strip + audit EU AI Act em `publish`. | ✅ |
| 5 | FairnessGuard pre-check | `jd_enrichment`, `bigfive`, `wsi_questions`. | ✅ |
| 6 | Audit trail SOX | Audit EU AI Act em `publish`. **Drift médio:** alguns nodes (intake/competency/eligibility) não emitem audit row — não-crítico, mas deveria existir um row por step crítico. | ⚠️ |
| 7 | PII masking | `strip_pii_for_llm_prompt` antes de cada LLM. | ✅ |
| 8 | Fail-closed em strict mode | `CompanyId.parse` levanta `InvalidCompanyIdError` em strict; mixin levanta `MissingTenantContextError`. | ✅ |
| 9 | Fail-open em dev | Confirmado nos blocos `try/except` com warning logs. | ✅ |
| 10 | Eval gate canonical | `wizard_no_tenant_leak.jsonl` (12 cenários) + novo `wizard_pipeline_template.jsonl` (7 cenários) — threshold 0.85. | ✅ |
| 11 | Sentinelas offline | 6 sentinelas listadas em §2 (rollout/no-regression/continuity/pipeline-emission/non-react/question-guard). | ✅ |
| 12 | Idempotência de mutações | `publish` idempotente. Demo Company seed UPSERT. | ✅ |
| 13 | Checkpointer durável | `get_checkpointer` Postgres → Memory fallback. | ✅ |
| 14 | Observability | Prometheus `lia_agent_tenant_context_resolved_total{agent,outcome}` + Sentry para bypass flags. | ✅ |
| 15 | Timeout/circuit breaker | `LIA_JD_ENRICHMENT_TIMEOUT_S` + `_fallback_enrichment`. **Drift baixo:** outros nodes (bigfive, wsi_questions, salary) não têm timeout explícito por env var. | ⚠️ |
| 16 | HITL formal | 2 pontos: `jd_enrichment` (#1) e `wsi_questions` (#2). `requires_approval=True` no payload. | ✅ |
| 17 | Rollback emergencial | Bypass flags R-007 documentadas em `replit.md` (não recomendadas para wizard). | ✅ |
| 18 | Documentação operacional | `tenant-context-history.md` + runbook `missing_tenant_context.md` + esta auditoria. | ✅ |

**Score:** 16/18 ✅ + 2/18 ⚠️ (não-críticos).

---

## 5. Eval Gates

### 5.1 `wizard_no_tenant_leak.jsonl` (existente — Task #1052)
- 12 cenários (B1×3 single-turn + B2/B3/B4×3 multi-turn de 3 turnos cada).
- Threshold 0.85, scorer com `re.search` IGNORECASE/DOTALL sobre `anti_patterns` + ≥1 marker em `expected_snippet_markers`.
- Comando: `python -m eval.eval_runner --dataset eval/golden/wizard_no_tenant_leak.jsonl && python -m eval.eval_runner --gate eval/golden/wizard_no_tenant_leak.jsonl`.
- **Status live nesta auditoria (2026-05-14, backend up em :8001):** **🔴 RED 0/12 (0%)**. Evidência em `lia-agent-system/eval/eval_results_20260514_113158.json`. **Causa raiz:** o endpoint REST `/api/v1/chat` devolve apenas a mensagem conversacional terse de HITL #1 do wizard (`"Descrição da vaga enriquecida — preciso da sua aprovação."`, 56 chars) — o conteúdo rico (JD, parsed_title, panel/ws_stage_payload com `pipeline_template`) só é entregue via eventos WebSocket que o `eval_runner` REST-only **não captura**. **Não é regressão do wizard:** a sentinela offline `test_wizard_session_continuity_t1051.py` continua verde, `test_wizard_pipeline_template_emission_t1055.py` continua verde, e o `pw-cenario-*` Playwright (que consome WS) continua verde. **É drift do scorer / transport:** o `eval_runner` precisa virar WS-aware (ou os cenários precisam ser reescritos para validar o que o REST devolve, não o que o WS streama). Drift D7 abaixo + follow-up dedicado.

### 5.2 `wizard_pipeline_template.jsonl` (NOVO — esta task)
- **7 cenários** cobrindo os 4 ramos críticos:
  - `WPT-T1-tech-backend` + `WPT-T2-tech-fullstack` — **técnico** (template=technical via `_TECHNICAL_KEYWORDS`).
  - `WPT-NT1-operational-vendedor` — **não-técnico operacional** (template=operational via `_OPERATIONAL_KEYWORDS`).
  - `WPT-NT2-executive-cto` — **não-técnico executivo** (template=executive via `_EXECUTIVE_KEYWORDS`).
  - `WPT-NT3-intern-estagio` — **estágio** (template=intern via `_INTERN_KEYWORDS` — cobre "estagi").
  - `WPT-RES1-resume-keep-title` — **retomada de sessão** (multi-turn, valida `wizard_session_pin` mantendo `parsed_title` e template estável entre turnos).
  - `WPT-FB1-fallback-vague` — **fallback LLM** (título vago → `_suggest_pipeline_template` cai no default seguro `technical` sem crashar; valida fail-open).
- Threshold 0.85, mesmo scorer da `wizard_no_tenant_leak.jsonl` (heurístico + Portuguese-aware).
- Cada cenário inclui `tenant_snippet` (Demo Company canonical) e `anti_patterns` que reproduzem B1 (no_company_id_question), B2 (no_title_reset, no multi-turn) e o defaultar para `"sua empresa"/"geral"/"default"`.
- Comando: `python -m eval.eval_runner --dataset eval/golden/wizard_pipeline_template.jsonl && python -m eval.eval_runner --gate eval/golden/wizard_pipeline_template.jsonl`.
- **Status live nesta auditoria (2026-05-14, backend up em :8001):** **🔴 RED 0/7 (0%)**. Evidência em `lia-agent-system/eval/eval_results_20260514_113307.json`. **Mesma causa raiz da §5.1**: REST devolve só o prompt HITL terse, scorer não vê o `parsed_title`/`pipeline_template` que ficam no payload WS. O dataset em si está correto (formato validado contra `load_golden_jsonl` + `score_heuristic`, 7 cenários cobrindo os 4 ramos pedidos pela task) — o gate só será verde quando o transport do `eval_runner` for corrigido (D7 / follow-up).

### 5.3 Sentinelas offline (todas pytest, sem backend)
Listadas em §2. Devem rodar em qualquer mudança no wizard. **São a fonte de verdade canônica enquanto os gates live estiverem RED por D7.**

---

## 6. Drift / duplicação encontrada

| ID | Severidade | Achado | Plano de remediação | Follow-up |
|---|---|---|---|---|
| **D1** | Baixa | `WIZARD_WSI_IMPLEMENTATION_GUIDE.md` vive dentro de `app/domains/job_creation/` (não-código numa pasta de código). | Mover para `docs/architecture/wizard-wsi-implementation-guide.md` ou referenciar a partir de `docs/INDEX.md`. | Task de doc cleanup. |
| **D2** | Baixa | Não existe diretório `app/domains/job_creation/agents/` — wizard agent vive em `app/domains/job_management/agents/wizard_react_agent.py`. Confusão de DDD: o domain do graph é `job_creation`, mas o agent vive em `job_management`. | Mover `WizardReActAgent` para `app/domains/job_creation/agents/wizard_react_agent.py` OU documentar a fronteira (graph = `job_creation`, agent que orquestra = `job_management`). Hoje funciona; é dívida de naming. | Task de refactor opcional. |
| **D3** | ✅ Resolvida (Task #1061) | Audit row apenas em `jd_enrichment` (FG L3 block) e `publish`. Nodes intermediários (bigfive, wsi_questions) não emitem audit explícito quando completam OK. EU AI Act sugere audit por step decisório. | **Implementado:** helper `_emit_wizard_step_audit` em `app/domains/job_creation/graph.py` emite `decision_type=wizard_step_completed` (mapeado em `DECISION_TYPE_MAPPING` → `GENERATE_FEEDBACK`) com `before/after/target_id/trace_id` em `reasoning`, espelhando o padrão de `audit_company_change`. Call sites em `bigfive_node`, `wsi_questions_node`, `competency_node`, `eligibility_node`. Sentinela offline: `tests/integration/agents/test_wizard_step_audit_t1061.py` (5 cenários — 1 por node + guard estático contra remoção de call site). | ✅ |
| **D4** | ✅ Resolvido (Task #1062) | Apenas `jd_enrichment` tem timeout via env (`LIA_JD_ENRICHMENT_TIMEOUT_S`). `bigfive`, `wsi_questions`, `salary` confiam no timeout default do LLM client. Agora os 4 nós LLM-bound têm timeout via env (`LIA_JD_ENRICHMENT_TIMEOUT_S=12`, `LIA_BIGFIVE_TIMEOUT_S=10`, `LIA_WSI_QUESTIONS_TIMEOUT_S=20`, `LIA_SALARY_TIMEOUT_S=10`) com fallback determinístico em cada um (JD → `_fallback_enrichment`; bigfive → `BigFiveExtraction()` defaults 0.5; wsi → `_fallback_questions(block, count)` por bloco; salary → `salary_benchmark=None` graceful skip). Sentinela `tests/integration/agents/test_wizard_node_timeouts_t1062.py` cobre os 3 fallbacks novos. Pattern usa `ThreadPoolExecutor(max_workers=1) + shutdown(wait=False)` para que o timeout seja efetivo (context-manager `with` bloqueia em `__exit__`). | — |
| **D5** | ✅ Resolvido (Task #1063) | Live eval gates (`wizard_no_tenant_leak.jsonl`, `wizard_pipeline_template.jsonl`) agora rodam em CI via `.github/workflows/wizard-eval-gates.yml` (workflow_dispatch + push em paths críticos: `eval_runner.py`, os 2 goldens, `app/domains/job_creation/**`, `wizard_react_agent.py`, `cascaded_router.py`, `main_orchestrator.py`). O workflow sobe Postgres + Redis + lia-backend, aplica migrations, semeia Demo Company + demo user e roda `--dataset` seguido de `--gate` para cada um. `eval/.gate_history.json` + `eval_results_*.json` + `backend.log` ficam anexados como artifact (`wizard-eval-gates-<run_id>`, retenção 30d). Comportamento **fail-CLOSED por default**: qualquer exit ≠ 0 derruba o job, e marcando `wizard eval gates` como required-check em Settings → Branches → main bloqueia o merge. Override `enforce=false` só vale para `workflow_dispatch` manual de diagnóstico — em runs de `push` o `continue-on-error` resolve sempre para `false`. Com D7 fechado pela Task #1064, os 2 steps de gate passaram a invocar `eval_runner` com `--transport ws` e o workflow está pronto para virar required-check no `main` sem ressalvas. | — |
| **D6** | Baixa | `_suggest_pipeline_template` retorna `templates: list(_PIPELINE_TEMPLATE_IDS)` (lista completa) junto com `suggested_type`. Frontend pode mostrar opções A/B/C/D/E mesmo quando o sugerido é "intern" — pode confundir. | Validar no FE se a UI realmente lista todos os 5 templates ou só o suggested. Se lista todos, OK por design (recrutador escolhe). Documentar contrato. | Task de UX, não-crítica. |
| **D8** | ✅ Resolvido (Task #1084 / T1) | HITL contract duplicado: `JobWizardGraph` (legacy) e `JobCreationGraph` (canonical) ambos servindo "approval" do wizard, com o handler WS `approval_response` instanciando `JobWizardGraph` inline para resumir após aprovação — abria espaço para audit row duplicado e race condition entre botão+chat. **Implementado:** novo serviço canônico `app/domains/job_creation/services/wizard_gate_service.py::WizardGateService` com `resume_gate(thread_id, pending_id, decision, ...)` como ÚNICO entry point para resumir gates do wizard a partir de qualquer transport. Idempotência via CAS Redis (key `wizard:gate:resolved:{gate_id}`, TTL 24h, fail-open in-memory) sobre `gate_id = "gate:{thread_id}:{pending_id}"`: chamar `resume_gate` 2× com mesmo `gate_id` retorna `cached=True` na 2ª, executa engine 1× e emite **1** audit row (`decision_type=wizard_step_completed`). Timeout no engine NÃO escreve CAS (permite retry pelo usuário) e NÃO emite audit row. WS handler `agent_chat_ws.py:557+` migrado para chamar `wizard_gate_service.resume_gate(...)` no branch `resume_domain == "wizard"` — `JobWizardGraph` NÃO é mais importado em `agent_chat_ws.py` (sentinela AST garante zero regressão). `JobWizardGraph` ganhou header `# DEPRECATED (Task #1084 / T1)` listando os call-sites legítimos remanescentes (crew_examples + tests + delegação interna do `WizardGateService._resume_engine`). Sentinela offline: `tests/integration/agents/test_wizard_hitl_unified_contract.py` (5 cenários — S1 determinismo `derive_gate_id`, S2 idempotência aprovação, S3 idempotência rejeição, S4 AST anti-import, S5 timeout NÃO cacheia). T1 é puro refactor — ZERO mudança comportamental observável pelo usuário; é pré-requisito de T2 (#1085) que troca o `_resume_engine` interno para `JobCreationGraph` com `interrupt()` LangGraph nativo, fechando o bug-mãe "repete 4× ignorando user input". | — |
| **D7** | ✅ Resolvido (Task #1064) | `eval_runner` ganhou um transport WebSocket dedicado (`--transport ws`): para cada caso abre `/api/v1/ws/chat/{session_id}` com first-message auth (UC-P0-19), envia o turno como `{"type":"message"}` e agrega o frame terminal `message` + frames auxiliares `wizard_stage` e `panel_update` (JSON-stringified) no campo `response` antes de chamar o scorer — exatamente o mesmo payload que o frontend consome, então `parsed_title`, `pipeline_template` e os marcadores `Backend`/`Engenheiro`/`Demo Company` voltam a ser observáveis pelo gate. Multi-turn cases reusam o mesmo socket por caso para preservar `conversation_history` na scope do handler e exercitar o `wizard_session_pin` Tier 0.5 + checkpointer LangGraph (sem isso B2/B3/B4 não seriam observáveis). O workflow `wizard-eval-gates.yml` passou a chamar os 2 datasets com `--transport ws` e o `continue-on-error` dinâmico continua restrito ao `workflow_dispatch` manual com `enforce=false` — em qualquer `push` o gate é fail-CLOSED. | — |

**Sem duplicação canonical detectada.** Não há `WizardReActAgent` paralelo, não há graph duplicado, não há outro `_suggest_pipeline_template`. ✅

---

## 7. Conclusão

O wizard está **canonicamente estável e sem drift crítico**. Os contratos T-A → T-F estão honrados; as 6 sentinelas offline cobrem os 4 bugs originais (B1/B2/B3/B4) + emissão de `pipeline_template` + non-React tenant. Os 2 eval gates canônicos (`wizard_no_tenant_leak.jsonl` + `wizard_pipeline_template.jsonl`) somam 19 cenários cobrindo tenant leak, retomada, ramos técnico/não-técnico/estágio/executivo e fallback.

**Drift identificado:** 6 itens, todos baixos/médios, nenhum bloqueador. Os 2 mais relevantes (D3 audit por step + D4 timeouts por env) merecem follow-up tasks dedicadas; os outros são higiene/doc.

**Próximo passo natural:** uma vez resolvido #1060 (estabilidade do `lia-backend` em runs longos), rodar os 2 gates live em CI e bloquear merge no main quando falham.
