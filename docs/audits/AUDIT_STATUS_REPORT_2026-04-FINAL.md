# AUDIT STATUS REPORT — 2026-04 FINAL (Tarefa #347)

> **Escopo.** Auditoria de re-verificação 1:1 contra `attached_assets/CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN_1776388079132.md` (1.469 linhas; 6 sub-auditorias; 78 findings explícitos + Stage 6 observability).
> **Reconciliação.** Estado atual do código vs. snapshot de 2026-04-16 (`docs/audits/AUDIT_STATUS_REPORT_2026-04.md`, Tarefa #302).
> **Convenção de status (estrita, conforme spec da Tarefa #347).** Cada finding recebe **exatamente um** dos 5 valores:
> - `RESOLVIDO` — remediado e verificável no código de hoje.
> - `PARCIAL` — remediação parcial: parte das evidências canônicas presentes, parte ausentes.
> - `PENDENTE` — sem mudança vs. snapshot do plan.
> - `INCORRETO` — o código foi implementado mas faz a coisa errada / incompleta (a remediação existe mas a implementação tem bug ou cobre apenas parte do contrato esperado).
> - `OBSOLETO` — a remediação proposta no plan **não é mais necessária**. Cobre dois sub-casos: (a) falso-positivo do plan (o problema descrito nunca existiu no código); (b) o problema deixou de existir por rota independente (refactor, deleção, etc.) e a ação proposta não se aplica mais.
>
> **Resultado da auditoria desta dimensão.** Não foram identificados findings `INCORRETO` (não há remediação implementada com bug funcional). Os 5 falsos-positivos do plan são classificados como `OBSOLETO`.
> **Garantia.** Nenhum arquivo de código foi modificado nesta tarefa. Toda evidência é grep/path:line do estado atual.
> **Identificadores.** Mantemos os IDs estáveis adotados em #302: `C1-C9` (9), `T1-T3` (3), `D1-D3` (3), `A1-A4` (4), `R1-R7` (7), `W1-W21` (21), `O1-O17` (17), `I1-I32` (32) — total **96 marcadores ⊇ 78 findings nominais** (alguns findings nominais agregam vários sub-itens; outros — como o bloco `I*` de imports — desdobram um único finding em 32 sub-marcadores). Ver §4.

---

## 0. Errata vs. Tarefa #347 (reconciliação 2026-04-17)

> **Por quê.** A versão original deste documento (gerada na Tarefa #347) descreveu vários findings como `PENDENTE` que, no estado atual do código, já estão `RESOLVIDO`. Apresentou também contagens internamente inconsistentes (W7) e classificou Stage 6 (Observability) como 0% quando o trabalho canônico de movimentação dos 11 módulos para `app/shared/observability/` já está concluído (Tarefa #343). Esta errata reconcilia o documento contra o snapshot fresco do código. **Nenhum arquivo de código foi modificado** — apenas este relatório.
>
> **Reconciliação.** 2026-04-17 (re-grep completo). Commit SHA: `dcb90de764270124f7345387e47b8d57123e65b9`.

**Reclassificações em relação à Tarefa #347:**

| ID | Antes (#347) | Agora (reconciliado) | Evidência canônica fresca |
|---|---|---|---|
| **R1** — `api/v1/finetuning_export.py` IDOR | PENDENTE / CRÍTICO / Top 10 #1 | **RESOLVIDO** | `finetuning_export.py` agora importa `get_current_user` e `audit_service`; ambos os endpoints chamam `Depends(get_current_user)` + `audit_service.log_decision` nos paths de sucesso e falha. |
| **C1** — `cv_scoring_service.py` | PENDENTE | **RESOLVIDO** | `from app.shared.compliance.scoring_safeguards import FairnessBlockedError, hash_payload, log_scoring_decision, run_fairness_check` + 5 hits totais (`grep -c FairnessGuard\|fairness_guard\|audit_service\|scoring_safeguards`). |
| **C2** — `lia_score_service.py` | PENDENTE | **RESOLVIDO** | mesmo import canônico; 11 hits. |
| **C3** — `pre_qualification_service.py` | PENDENTE | **RESOLVIDO** | mesmo import canônico; 6 hits. |
| **C4** — `eligibility_verification_service.py` | PENDENTE | **RESOLVIDO** | mesmo import canônico; 6 hits. |
| **C5** — `evaluation_criteria_service.py` | PENDENTE | **RESOLVIDO** | mesmo import canônico; 6 hits. Linhas 16-21, 369-490: `run_fairness_check` → `log_scoring_decision` (fail-closed). |
| **T3** — `shared/global_tool_registry.py` | PENDENTE | **RESOLVIDO via deleção** | Arquivo não existe mais. Canary fitness `TestF12GlobalToolRegistryDeadCanary` impede ressurreição sem callers (F12 / task #352). |
| **Stage 6 — Observability (P16-P20)** | 0% / 15 PENDENTE | **PARCIAL → RESOLVIDO no código** | `app/shared/observability/__init__.py` = 512 bytes; **11 módulos canônicos presentes** (`tracing.py`, `structured_logging.py`, `callbacks.py`, `agent_monitoring_service.py`, `agent_health_alert_service.py`, `model_drift_service.py`, `drift_alert_service.py`, `token_tracking_service.py`, `token_budget_service.py`, `wsi_observability.py`, `langsmith.py`) + 41 importadores usando o caminho canônico `from app.shared.observability`. Os 11 paths legados foram **removidos sem shim** (verificados MISSING; CI gate em `scripts/check_forbidden_imports.py`). Resíduo doc-only: `ARCHITECTURE.md` §9.4, `CANONICAL_SOURCES_SPEC.md`, `CLAUDE.md` ainda precisam refletir o move (PARCIAL apenas para o eixo "documentação"; código está RESOLVIDO). |
| **A3** — `interview_graph.py` FairnessGuard | PARCIAL (f=0) | **RESOLVIDO** (f≥1) | `interview_graph.py:341-471` — `_apply_fairness_guard_to_response` usa `check_fairness` (FG L2) sobre `response_data["message"]` com política BLOCK + REGENERATE + audit `decision="blocked"`. 11 hits totais para `FairnessGuard\|fairness_guard`. |
| **W7 — `require_company=False`** | "23 ocorrências" em §1.1/§2/§7.3 e "18" em §1.2 #7 / F8 — **inconsistente** | **18 decoradores em 7 arquivos** (figura única usada em todo o documento) | `grep -rn "@tool_handler.*require_company=False" app --include="*.py" \| wc -l` = **18**. Distribuição: `pipeline_tool_registry.py` ×5, `kanban_tool_registry.py` ×3, `policy_tool_registry.py` ×3, `autonomous_tool_registry.py` ×3, `skills_ontology_tools.py` ×2, `market_intelligence_tools.py` ×1, `sourcing_tool_registry.py` ×1. |

**Correções de inventário (`app/shared/`):**

| Métrica | Tarefa #347 dizia | Verificado em 2026-04-17 |
|---|---|---|
| Total `.py` | 297 | **299** |
| Subpastas | 28 | **29** |
| Top-level `.py` | 23 | **20** |
| Importadores de `app.shared.observability` | (não medido) | **41** |
| Bytes de `shared/observability/__init__.py` | 53 | **512** |

**Top 10 do que ainda importa após reconciliação:** caem fora R1 (#1), C1-C5 (#2), Stage 6 código (#3 — resta apenas refresh doc), A3 (#5 — já marcada RESOLVIDO no §4), T3 (#4 deletado). Permanecem: A1 herança Base, sub-agents (escopo de critério), **T1/W8/W10 (re-classificados como CANÔNICO ATIVO em 2026-04-20 — ver §7.4 errata; migração para `@tool_handler` rescopada para 18 caller files + executor + orchestrator + scope_config + llm_factory, não 2 arquivos / 30 calls)**, R5/R6 (DOC), 146 shims sem SLA. Top 10 reformulado em §1.2.

---

## 0.1 Atualização 2026-04-19 (sessão TA/TB/TC/TD)

> **Por quê.** Fechamento dos pendentes consolidados da auditoria pré-produção (F4/F5/F8/F10/F11/F12, durabilidade #544 + cobertura #545, reconciliação documental). Esta entrada **não modifica** as classificações da §0 — apenas registra as evidências canônicas frescas geradas nas sessões TA/TB/TC/TD e o commit de referência.
>
> **Reconciliação.** 2026-04-19. Commit SHA de referência: `82024c5864738d65e76fa58644f0cc4e8e8d30dd` (HEAD da sessão TD).

| ID / Eixo | Selo | Evidência canônica fresca (2026-04-19) |
|---|---|---|
| **F4 — FairnessGuard no `interview_graph`** | ✅ RESOLVIDO confirmado | `lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py` — 25+ hits de `FairnessGuard` (política BLOCK + REGENERATE + `audit_service.log_decision`); teste `lia-agent-system/tests/integration/test_interview_graph_fairness.py` cobre o gate. |
| **F8 — `require_company=False`** | ✅ RESOLVIDO + DOC consolidada | 18 decoradores justificados + 1 nova exceção sub-classe (total **19**) catalogadas em `docs/policies/require_company_exemptions.md`; teste-guard `lia-agent-system/tests/test_global_tool_registry_smoke.py` impede regressão silenciosa. |
| **F10 — Shims `RAILS-DEPRECATED`** | ✅ RESOLVIDO + SLA documentado | 14 shims com SLA por tipo (data alvo de remoção + responsável) em `docs/policies/shim_sla.md`. |
| **F11 — `@tool` LangChain em `domains/`** | ✅ RESOLVIDO + guard ativo | 0 ocorrências; `lia-agent-system/tests/integration/test_no_langchain_tool_decorator_guard.py` falha CI se reaparecer. |
| **F12 — `global_tool_registry`** | ✅ RESOLVIDO via deleção | Confirmado: arquivo ausente; canary fitness mantido. |
| **F5 — Sub-agents + top-level ReAct** | ✅ RESOLVIDO | Fechado em tasks #369/#371 (já refletido na §0 original). |
| **#544 — Durabilidade do AI consumption (outbox)** | ⚠️ RESOLVIDO (single-instance) — follow-up multi-instance | `lia-agent-system/alembic/versions/095_create_ai_consumption_outbox.py` cria tabela outbox; teste `lia-agent-system/tests/test_ai_consumption_outbox.py` (4 casos) cobre enqueue + drain idempotente; helper de callback unificado em `app/shared/observability/usage_tracking_callback.py` (review-fix 2026-04-19: removido `asyncio.shield` espúrio que mascarava `TypeError` no `create_task` — regressão coberta por `test_outbox_callback_nao_usa_shield_em_create_task`). **Follow-up v2 hardening**: o drain do worker (`ai_consumption_outbox_worker.py`) faz `SELECT ... ORDER BY created_at LIMIT N` sem `FOR UPDATE SKIP LOCKED` — seguro hoje (Replit single-instance) mas **não é multi-instance safe**: drainers concorrentes processariam o mesmo lote. Antes de escalar horizontalmente, adicionar `FOR UPDATE SKIP LOCKED` ao SELECT e atualizar o teste `test_enqueue_and_drain_outbox` com cenário de 2 workers concorrentes. |
| **#545 — Cobertura do tracking de IA** | ✅ RESOLVIDO | `safe_invoke(on_usage=...)` propagado nos sinks estratégicos da Camada 2 do WSI + helpers reusáveis (commits `0b9ee1434`, `965cbb82f`, `b098b04e1`, `f795649dd`, `6f85980fe`, `3de3ce2ba`); cobertura registrada no Apêndice A do `.local/audit/wsi-screening-e2e-report.md` rev. 3. |
| **WSI E2E rev. 3 (17 achados)** | 11 ✅ + 5 ⚠️ + 1 ❌ | Reauditoria exaustiva publicada em `.local/audit/wsi-screening-e2e-report.md` (rev. 3). Único ❌: P0-4 (persistência por-questão no `wsi_voice_orchestrator`). Decisão sobre follow-up cabe ao usuário — esta auditoria não propõe tasks. |

**Garantia.** Nenhum arquivo de código foi alterado por esta atualização do relatório. Toda evidência veio de grep/path:line do commit alvo ou de artefatos criados nas sessões TA/TB/TC (migrations, testes-guard, policies).

---

## 1. Sumário Executivo

### 1.1 O quanto andou desde 2026-04-16

| Eixo | Snapshot 2026-04-16 | Snapshot 2026-04-17 | Delta |
|---|---|---|---|
| Findings RESOLVIDO | 14 | **66** | **+52** |
| Findings PARCIAL | 9 | 4 | -5 |
| Findings PENDENTE | 41 | 5 | -36 |
| Findings OBSOLETO (inclui falsos-positivos do plan) | 14 | 21 | +7 (mais auditados) |
| Findings INCORRETO (implementados com bug) | 0 | 0 | sem mudança |
| `from app.shared.services.audit_service` (shim antigo) | 8 imports | **0 imports** | -8 ✅ |
| `from langchain_core.tools import tool` em `domains/` (T2) | 5 arquivos | **0 arquivos** | -5 ✅ |
| `require_company=False` (W7) | 89 decoradores | **18** decoradores (todas justificadas com `# … kept: …` e documentadas em `docs/policies/require_company_exemptions.md` — F8) | -71 ✅ |
| `pii_filter` (C8) em `domains/job_creation/domain.py` | 1 import quebrado | **0** | -1 ✅ |
| Stage 6 — `shared/observability/` | __init__.py vazio | **__init__.py 512 bytes; 11 módulos canônicos movidos; 11 paths legados deletados; 41 importadores usando path canônico** (Tarefa #343) | ✅ |
| Inventário `shared/` (.py) | 308 (doc) → 308 (verificado) | **299** | -9 |
| Inventário `shared/` (subdirs) | 28 (doc) → 28 | **29** | +1 |
| Inventário `shared/` (top-level .py) | 28 (doc) | **20** | -8 |
| Sweep audit shim (W4, W5, W20, C9, I1-I5) | PENDENTE | **RESOLVIDO** | ✅ |
| Migração 5 @tool legados (T2) | PENDENTE | **RESOLVIDO** | ✅ |
| `applications`/`bulk_actions`/`stage_transition` (R2-R4) | PENDENTE | **RESOLVIDO** | ✅ |
| `sourcing_pipeline` + `candidate_feedback` (C6-C7) | PARCIAL | **RESOLVIDO** | ✅ |
| `JobCreationGraph` (A1) — 5% → ? | PENDENTE | **PARCIAL** (FairnessGuard pre+post + PII mask + AuditCallback) | ✅ |
| `PolicySetupAgent` (A2) — 25% → ? | PENDENTE | **PARCIAL** (Base + FG + PII + tenant + SPB + audit) | ✅ |
| `WSIInterviewGraph` (A4) — 55% → ? | PENDENTE | **PARCIAL** (FG L2 + Audit + PII + tenant) | ✅ |
| `InterviewGraph` (A3) — 50% → ? | PENDENTE | **RESOLVIDO** (Audit + PII + tenant + **FairnessGuard L2** sobre msg ao candidato — F4 / task #352) | ✅ |
| Bias detectors (D1) — 3 implementações | PENDENTE | **RESOLVIDO** (3 delegam a `FairnessGuard`) | ✅ |
| Duplicatas (D2, D3, W11-W15) | PENDENTE | **RESOLVIDO** (uma cópia em cada caso) | ✅ |
| 5 stubs `lia_*` + `company_benefits_api` (O13-O17) | PARCIAL | **RESOLVIDO** (arquivos removidos) | ✅ |
| `agent_chat_ws` sem prefix `/api/v1` (W17) | PENDENTE | **RESOLVIDO** (`prefix="/api/v1"` em routes.py:495) | ✅ |
| `bias_audit_service` em local errado (W6) | PENDENTE | **RESOLVIDO** (canonical em `shared/compliance/`, shim em `shared/services/`) | ✅ |
| `R7` — chat SSE sem `pre_compliance/post_compliance` | PENDENTE | **RESOLVIDO** (`agent_chat_sse.py:234, 403`) | ✅ |
| Scoring services C1-C5 | PENDENTE | **RESOLVIDO** (todos os 5 importam `scoring_safeguards` → `run_fairness_check` + `log_scoring_decision`; fail-closed quando FG indisponível) | ✅ |
| `R1` — `finetuning_export.py` IDOR | PENDENTE | **RESOLVIDO** (`Depends(get_current_user)` + `audit_service.log_decision` em ambos endpoints) | ✅ |
| `T3` GlobalToolRegistry — dead | PENDENTE | **RESOLVIDO via deleção** (`app/shared/global_tool_registry.py` removido; canary fitness `TestF12GlobalToolRegistryDeadCanary` impede ressurreição sem callers — F12 / task #352) | ✅ |
| `app/tools/registry.py` (T1/W8/W10) | PENDENTE | **CANÔNICO ATIVO** (re-classificado 2026-04-20 — não é registry paralelo; é o registry canônico wired por `initialize_tools()` com 18 caller files; loader e YAML têm consumidores ativos em `scope_config.py` + `llm_factory.py`. Ver §7.4 errata) | — |
| Sub-agents 14-29 — herança simbólica `↑` | PENDENTE (recompute) | **RESOLVIDO** (recompute task #369: política F5 aplicada; herança verificável `↑✓` de f/a/t via `LangGraphReActBase` em `libs/agents-core/lia_agents_core/langgraph_react_base.py:150-152, 251, 349`) | ✅ |
| Top-level `*ReActAgent` 1-13 — herança implícita não anotada | PENDENTE (recompute) | **RESOLVIDO** (recompute task #371: mesma política F5 estendida aos top-level que extends `LangGraphReActBase` direto; AuditCallback (col 2) e Tenant (col 5) — e FG (col 3) nas linhas 8/9/11 — passam a `↑✓`) | ✅ |

> **Reconciliação task #369 (sub-agents).** O recompute da matriz §4 foi executado conforme F5 (definida em task #352). **Nota de contagem:** o enunciado original da tarefa #369 referenciava "14 sub-agent rows" (número herdado de §1.2 item #8 pré-recompute, que datava do CODE_AUDIT inicial); o inventário atual da matriz §4 abrange **16 linhas** de sub-agent (linhas 14-29 — Kanban×3, Pipeline×3, Sourcing×10), portanto as 16 linhas foram processadas. Para cada uma verificou-se: (i) extends-relationship com o `*ReActAgent` pai (Python class inheritance — composição estrutural equivalente, e na prática mais forte, que `cls(...)` em grafo) — confirmada em todos os 16 arquivos via `class XxxAgent(YyyReActAgent)`; (ii) cadeia `*ReActAgent → LangGraphReActBase` injeta `FairnessGuard.check()` (linha 251), `AuditCallback` (linhas 150-152) e `tenant_llm_context.get_current_llm_tenant()` (linha 349) em runtime para todas as subclasses. As 16 linhas migram de `↑` para `↑✓` em FairnessGuard, AuditCallback e Tenant Context. Score sobe de 14%/29% para **43% uniforme**. Os critérios Base (b), PII (p), SPB (s) e Reg permanecem `—` no arquivo do sub-agent — F5 proíbe inheritance-pass nesses 4 critérios. Não houve mudança de código de produção: este é um rebuild de scorecard.

> **Reconciliação task #371 (top-level `*ReActAgent`).** Segundo passe do recompute F5, agora aplicado às 12 linhas top-level no escopo: `#1-#11` + `#13` (excluído `#12 CustomAgentRuntime` — runtime, não `*ReActAgent` e fora do critério F5/#371). As 12 classes extends `LangGraphReActBase` **diretamente** (verificado individualmente nos arquivos listados na matriz §4 col. "Arquivo" — `class WizardReActAgent(LangGraphReActBase, EnhancedAgentMixin)` em `wizard_react_agent.py:40`, `PipelineTransitionAgent` em `pipeline_transition_agent.py:33`, `SourcingReActAgent` em `sourcing_react_agent.py:84`, `TalentReActAgent` em `talent_react_agent.py:41`, `JobsManagementReActAgent` em `jobs_mgmt_react_agent.py:41`, `KanbanReActAgent` em `kanban_react_agent.py:41`, `PolicyReActAgent` em `policy_react_agent.py:41`, `AutomationReActAgent` em `automation_react_agent.py:30`, `AnalyticsReActAgent` em `analytics_react_agent.py:32`, `CommunicationReActAgent` em `communication_react_agent.py:34`, `ATSIntegrationReActAgent` em `ats_integration_react_agent.py:34`, `AutonomousReActAgent` em `autonomous_react_agent.py:65`). Como o per-file grep da matriz original só conta imports no próprio arquivo, AuditCallback e tenant_llm_context apareciam como `—` mesmo sendo injetados em runtime pela base. Migram para `↑✓`: **(2) Audit** e **(5) Tenant** em todas as 11 linhas no escopo (#1-#11); **(3) FG** adicional em #8/#9/#11, que não importavam FG localmente. Linhas 1-7 e 10 passam de 57% → **71%**; linhas 8/9/11 de 43% → **71%**; linha 13 (AutonomousReActAgent) ganha `↑✓` em Tenant mas score permanece **86%** (FG/Audit já contados como ✓ direto). Linha 12 fora do escopo. Não houve mudança de código de produção: este é um rebuild de scorecard.

### 1.2 Top 10 do que ainda importa (reformulado em 2026-04-17)

> Itens resolvidos no código (R1, C1-C5, T3, A3, Stage 6) foram removidos do Top 10. A lista abaixo reflete apenas o que efetivamente continua em aberto.

| # | Item | Severidade | Esforço estimado |
|---:|---|---|---|
| 1 | **T1 (rescopado) + W8/W10 (re-classificados como ATIVOS)** — `app/tools/registry.py` (169L) é o `tool_registry` **canônico** wired em `app/tools/__init__.py` via `initialize_tools()`; consumido por `app/tools/executor.py`, `app/orchestrator/orchestrator.py` (linha 37), `app/orchestrator/agentic_loop.py` e `app/domains/ai/services/tool_executor_service.py`, com **18 arquivos de caller** (`grep -rln "from app.tools.registry" app/ → 18`) que registram tools em ~14 módulos de domínio (sourcing, job_management, cv_screening, communication, analytics, automation, recruiter_assistant, talent_intelligence, company_settings, shared/tools). `tool_permissions.yaml` (245L) + `tool_permissions_loader.py` (288L) **não são dead code**: o loader é importado por `app/tools/scope_config.py` (que alimenta o orquestrador e o `tool_executor_service` via mapeamento `scope → [tool_names]` + `restricted_tools` HITL) e por `app/shared/providers/llm_factory.py:461` para selecionar `llm_provider` / `llm_fallback_order` por tenant. Se uma migração para `@tool_handler` ainda for desejada, ela deve ser planejada para os ~14 módulos de caller + executor + orquestrador (não para "2 arquivos / 30 calls" como a versão anterior afirmava), e a remoção do loader/yaml exige primeiro migrar `scope_config.py` + `llm_factory._load_from_permissions` para outra fonte. Ver ADR-016 para o caminho de migração planejado. | MÉDIO | L–XL (migração arquitetural ampla, não cleanup pontual) |
| 2 | **A1** — `JobCreationGraph` agora tem FG/PII/Audit, mas **não herda `LangGraphReActBase`** (b=0); por design é um `StateGraph`, não ReAct — pode ser tratado como `n/a` ou aceito como divergência permanente. | MÉDIO | M (ou doc-decisão) |
| 3 | **Stage 6 — refresh de documentação** — código e CI gate prontos (Tarefa #343); resta atualizar `ARCHITECTURE.md` §9.4, `CANONICAL_SOURCES_SPEC.md` e `CLAUDE.md` para refletir o novo path canônico `app.shared.observability.*`. | BAIXO | XS (doc-only) |
| 4 | Sub-agents ReAct (kanban_*, pipeline_*, sourcing_*, etc.) e top-level `*ReActAgent`: política F5 (task #352) já recomputada em duas passagens — sub-agents 14-29 (task #369) e top-level 1-13 (task #371). Gaps abertos por design (não compliance gaps): PII/SPB/Reg em sub-agents, e PII/SPB nas top-level — F5 não permite inheritance-pass nesses critérios. | INFORMATIVO | (concluído) |
| 5 | **R5/R6/W21** — rotas alegadas como duplicadas que não existem; precisam ser oficialmente fechadas como `OBSOLETO` no CHANGELOG do plan original. | DOC | XS |
| 6 | **146 shims backward-compat** restantes (10 `RAILS-DEPRECATED` já com `@deprecated since=2026-04-17` via F10). Removíveis em batch quando `integrations_hub` cobrir 100%. | BAIXO | L |
| 7 | **W7 (resíduo)** — 18 `@tool_handler(..., require_company=False)` restantes (vs. 89 originais). Documentadas em `docs/policies/require_company_exemptions.md` + CI gate em `scripts/check_require_company_exemptions.py` (F8 / task #352). | BAIXO | (concluído; manutenção apenas) |

### 1.3 Veredicto consolidado

A implementação fez **progresso quase completo nos 30 dias entre os dois snapshots**: Stage 1 (hotfixes) **fechado** (R1 RESOLVIDO em 2026-04-17), Stage 2 (compliance gates) **fechado** (R2-R7, C1-C9), Stage 3 (tools) **~85%** (T2, T3, W7 RESOLVIDO; W8/W10 + T1 abertos), Stage 4 (agentes) **avançado** (A2/A3/A4 RESOLVIDO ou PARCIAL≥57%; A1 PARCIAL com decisão arquitetural pendente), Stage 5 (cleanup) **~95%** (resta apenas SLA de 146 shims), Stage 6 (observability) **fechado no código** (Tarefa #343); resíduo é apenas refresh de 3 documentos.

---

## 2. Inventário Compartilhado — Delta vs. Plan

| Métrica | Plan diz | Verificado em 2026-04-16 (#302) | Verificado agora (#347) | Delta |
|---|---|---|---|---|
| Total `.py` em `app/shared/` | 307 | 308 | **299** | **-9** |
| Subpastas em `shared/` | 28 | 28 | **29** | **+1** (nova: `observability/`) |
| Arquivos top-level em `shared/` | 28 | 28 | **20** | **-8** |
| `from app.shared.services.audit_service` (W20+I1-I5) | 7 imports | 8 imports | **0** | **✅** |
| `from langchain_core.tools import tool` em `domains/` (T2) | 5 arquivos | 5 | **0** | **✅** |
| `@tool_handler(..., require_company=False)` (W7) | 89 | 89 | **18** | **-71** |
| Importadores de `app.shared.observability` (Stage 6) | n/a | n/a | **41** | (canônico ativo) |

**Interpretação.** A redução de 9 .py em `shared/` + 8 top-level + 1 nova subpasta (`observability/`) reflete (a) consolidação real de duplicatas (W11-W15, `bias_audit_service`), e (b) o move dos 11 módulos de observability para a nova subpasta canônica. Não há indício de remoção destrutiva — todos os módulos canônicos referenciados pelo doc continuam acessíveis no novo path `app.shared.observability.*`.

---

## 3. Tabela Canônica dos 78 Findings (96 marcadores)

> **Como ler.** Para cada finding mantemos: ID estável (igual a #302), descrição original do plan, status agora, evidência fresca (path:line), e nota de delta vs. 2026-04-16.

### 3.1 Críticos de Segurança / Compliance (R1-R7, C1-C9)

| ID | Descrição (do plan) | Status #302 | **Status #347** | Evidência fresca | Delta |
|---|---|---|---|---|---|
| **R1** | `api/v1/finetuning_export.py`: 2 endpoints sem auth, IDOR via `{company_id}` no path | PENDENTE | **RESOLVIDO** | `finetuning_export.py` importa `get_current_user` + `audit_service`; ambos endpoints com `Depends(get_current_user)` + `audit_service.log_decision` em sucesso e falha (verificado por grep). | ✅ |
| **R2** | `api/v1/applications.py`: aplicação pública sem auth/FairnessGuard/audit | PENDENTE | **RESOLVIDO** | `applications.py:21` (`get_current_user`), `:67-68` (audit/FG imports), `:225-275` (FG check + audit_service.log_decision pre/blocked), `:345` (audit final) | ✅ |
| **R3** | `api/v1/bulk_actions.py`: ações em lote sem fairness/audit | PENDENTE | **RESOLVIDO** | `bulk_actions.py:16` (`get_current_user`), `:22-30` (FG+audit imports + helper `_check_fairness_or_422`), `:37-94` (FG check + audit_service.log_decision), 6 endpoints com `Depends(get_current_user)` | ✅ |
| **R4** | `api/v1/stage_transition_automation.py`: transições automáticas sem fairness | PENDENTE | **RESOLVIDO** | `stage_transition_automation.py:21-28` (FG+audit), `:61` (audit log), `:504-551` (FG block on generated body) | ✅ |
| **R5** | `routes.py` — `llm_config_router` registrado 2× | INCORRETO | **OBSOLETO** (falso-positivo do plan) | `routes.py:260` (1 import) e `:426` (1 include único). 1 registro só. | confirmado |
| **R6** | `routes.py` — `webhooks.router` registrado 2× | INCORRETO | **OBSOLETO** (falso-positivo do plan) | `routes.py:529` único include. `:532-534` são 3 webhooks distintos (external/merge/mailgun). | confirmado |
| **R7** | Chat SSE sem `pre_compliance`/`post_compliance` (vs. WS/REST que têm) | PENDENTE | **RESOLVIDO** | `agent_chat_sse.py:45-46` (imports), `:234` (`pre_compliance`), `:403` (`post_compliance`). Paridade C3B com `chat.py` (`:222`, `:268`) e `agent_chat_ws.py` (`:661`, `:951`) | ✅ |
| **C1** | `cv_scoring_service.py` — produz score sem FG nem `audit_service` | PENDENTE | **RESOLVIDO** | `cv_scoring_service.py` importa `from app.shared.compliance.scoring_safeguards import FairnessBlockedError, hash_payload, log_scoring_decision, run_fairness_check`. 5 hits totais no arquivo. | ✅ |
| **C2** | `lia_score_service.py` — idem | PENDENTE | **RESOLVIDO** | mesmo import canônico de `scoring_safeguards`; 11 hits totais. | ✅ |
| **C3** | `pre_qualification_service.py` — idem | PENDENTE | **RESOLVIDO** | mesmo import canônico; 6 hits totais. | ✅ |
| **C4** | `eligibility_verification_service.py` — idem | PENDENTE | **RESOLVIDO** | mesmo import canônico; 6 hits totais. | ✅ |
| **C5** | `evaluation_criteria_service.py` — idem | PENDENTE | **RESOLVIDO** | `evaluation_criteria_service.py:16-21, 369-490` — `run_fairness_check` (fail-closed via `FairnessBlockedError`) + `log_scoring_decision` com `criteria_used=["fairness_guard"]`. 6 hits totais. | ✅ |
| **C6** | `sourcing_pipeline_service.py` sem FG nas filter criteria | PARCIAL | **RESOLVIDO** | `sourcing_pipeline_service.py:478-499` (FG `check`), `:517-577` (audit_service.log_decision), `:664-677` (segundo gate FG) | ✅ |
| **C7** | `candidate_feedback_service.py` sem FG no texto pós-gerado | PARCIAL | **RESOLVIDO** | `candidate_feedback_service.py:227, :445-520` (FG `check` no feedback gerado, regenera ou bloqueia) | ✅ |
| **C8** | `domains/job_creation/domain.py` importa `app.services.pii_filter` (módulo inexistente) | PENDENTE | **RESOLVIDO** | `domain.py` — `grep "pii_filter" → 0`. Substituído pelo path canônico `app.shared.pii_masking` | ✅ |
| **C9** | `domains/automation/services/stage_automation_engine.py` usa `app.shared.services.audit_service` (shim) | PENDENTE | **RESOLVIDO** | `stage_automation_engine.py:444` — `from app.shared.compliance.audit_service import audit_service` | ✅ |

### 3.2 Tools System (T1-T3)

| ID | Descrição | Status #302 | **Status #347** | Evidência | Delta |
|---|---|---|---|---|---|
| **T1** | ~~`app/tools/registry.py` — registry paralelo a `tool_handler`~~ **(re-classificado 2026-04-20)** `app/tools/registry.py` — registry **canônico** wired por `initialize_tools()`; não é paralelo ao `@tool_handler` (que é decorator de checagem por-função, não registry enumerável) | PENDENTE | **CANÔNICO ATIVO** (não-PENDENTE de remoção sem migração arquitetural ampla) | `app/tools/registry.py` (169 L) é instanciado em `app/tools/__init__.py:18` e populado por `initialize_tools()`; **18 caller files** registram tools (`grep -rln "from app.tools.registry" app/ → 18`); consumido por `app/tools/executor.py`, `app/orchestrator/orchestrator.py:37`, `app/orchestrator/agentic_loop.py`, `app/domains/ai/services/tool_executor_service.py:13`, `app/domains/job_management/agents/job_wizard_graph.py:34`. Ver §7.4 errata. | re-classificação (sem mudança de código) |
| **T2** | 5 arquivos `@tool` legados em `domains/*/tools/` | PENDENTE | **RESOLVIDO** | `grep "from langchain_core.tools import tool" lia-agent-system/app/domains → 0 matches`. Os 5 alvos confirmados migrados: `pipeline_tools.py:9` (`tool_handler`), `ats_tools.py:11`, `scheduling_tools.py:11`, `automation_tools.py:11`, `policy_tools.py:11` — todos com `@tool_handler(domain=…, require_company=True)` | ✅ |
| **T3** | `shared/global_tool_registry.py` — sem callers em produção | PENDENTE | **RESOLVIDO via deleção** | `app/shared/global_tool_registry.py` removido (verificado `[ -f ... ] → MISSING`). Canary fitness `TestF12GlobalToolRegistryDeadCanary` (F12 / task #352) impede recriação sem callers. | ✅ |

### 3.3 Duplicatas (D1-D3, W11-W15)

| ID | Descrição | Status #302 | **Status #347** | Evidência | Delta |
|---|---|---|---|---|---|
| **D1** | 3 bias detectors (`interview_intelligence/services/bias_detector_service.py`, `talent_intelligence/tools/interview_intelligence_tools.py`, `job_creation/services/jd_enrichment.py`) | PENDENTE | **RESOLVIDO** | Os 3 agora delegam ao FairnessGuard SSOT: `bias_detector_service.py:26-33` (`from app.shared.compliance.fairness_guard import FairnessGuard`), `interview_intelligence_tools.py:14-20` ("delegated… task #321"), `jd_enrichment.py:32-46` (thin wrapper sobre `FairnessGuard.apply_inclusive_language`) | ✅ |
| **D2** | `job_report_service.py` duplicado em `analytics/` e `job_management/` | PENDENTE | **RESOLVIDO** | apenas `domains/analytics/services/job_report_service.py` existe; `domains/job_management/services/job_report_service.py` removido | ✅ |
| **D3** | `pipeline_tool_registry.py` duplicado em `pipeline/agents/` e `cv_screening/agents/` | PENDENTE | **RESOLVIDO** | apenas `domains/pipeline/agents/pipeline_tool_registry.py` (99 458 bytes); `cv_screening/agents/pipeline_tool_registry.py` removido | ✅ |
| **W11** | `user_repository.py` em `auth/` e `company/` | PENDENTE | **RESOLVIDO** | apenas `domains/auth/repositories/user_repository.py` | ✅ |
| **W12** | `kanban_assistant_service.py` em `recruiter_assistant/` e `pipeline/` | PENDENTE | **RESOLVIDO** | apenas `domains/recruiter_assistant/services/kanban_assistant_service.py` | ✅ |
| **W13** | `seniority_resolver.py` em `cv_screening/` e `job_creation/` | PENDENTE | **RESOLVIDO** | apenas `domains/cv_screening/services/seniority_resolver.py` | ✅ |
| **W14** | `wizard_analytics_service.py` duplicado | PENDENTE | **RESOLVIDO** | inventariado: uma cópia | ✅ |
| **W15** | `job_insights_service.py` duplicado | PENDENTE | **RESOLVIDO** | apenas `domains/analytics/services/job_insights_service.py` | ✅ |

### 3.4 Agentes (A1-A4)

> **Critérios verificáveis no arquivo:** `b` = `LangGraphReActBase`; `a` = `AuditCallback/audit_callback`; `f` = `FairnessGuard/fairness_guard`; `p` = `pii_masking/mask_pii/strip_pii`; `t` = `tenant_llm_context/get_provider_for_tenant`; `s` = `SystemPromptBuilder`. Contagens são `grep -c` no arquivo.

| ID | Agente | Score doc | #302 | **#347 (re-grep)** | Status | Delta |
|---|---|---|---|---|---|---|
| **A1** | `domains/job_creation/graph.py` (JobCreationGraph) | 5% | 0% (b=0,a=0,f=0,p=0,t=0,s=0) | **b=0, a=2 (`AuditCallback`@1188-1197), f=20+ (gates pre/post em jd_enrichment+bigfive+wsi), p=4 (`mask_pii_for_llm`@36,169,294,532), t=0, s=0** | **PARCIAL** (~57% verificável) | ✅ |
| **A2** | `domains/policy/agents/agent.py` (PolicySetupAgent) | 25% | 0% | **b=5 (LangGraphReActBase@35,74), a=0, f=14 (FG checks), p=3 (strip_pii_for_llm_prompt), t=6 (tenant_llm_context), s=5 (SystemPromptBuilder@304)** | **PARCIAL** (~71%) — falta `AuditCallback` (mas `audit_service.log_decision` é chamado em `:251-278`) | ✅ |
| **A3** | `domains/interview_scheduling/agents/interview_graph.py` | 50% | 29% | **b=0, a=9, f=11 (FG L2 BLOCK + REGENERATE em `_apply_fairness_guard_to_response`@341-471), p=2 (strip_pii_for_llm_prompt@245), t=2 (tenant_llm_context@183-199)** | **RESOLVIDO** (~57%; F4 / task #352 fechou o gap de FairnessGuard) | ✅ |
| **A4** | `domains/cv_screening/agents/wsi_interview_graph.py` | 55% | 43% | **b=0, a=10 (audit_service.log_decision@652,755), f=5 (FG L2 check@577-594), p=2 (strip_pii_for_llm_prompt@571), t=4 (tenant_llm_context@42-56)** | **PARCIAL** (~71%) | ✅ |

### 3.5 Warnings (W1-W21) — exceto W11-W15 (acima)

| ID | Descrição | Status #302 | **Status #347** | Evidência | Delta |
|---|---|---|---|---|---|
| **W1** | Chat SSE sem `pre_compliance` | (= R7) | **RESOLVIDO** | `agent_chat_sse.py:234,403` | ✅ |
| **W2** | Chat REST sem FairnessGuard L3 (HR) | PARCIAL | **RESOLVIDO** | `chat.py:608-616, :898` (FG explícita) + C3B layer @ 222/268 | ✅ |
| **W3** | Inconsistência de FG em chat WS | PARCIAL | **RESOLVIDO** | `agent_chat_ws.py:52, :661, :951` — paridade total | ✅ |
| **W4** | `domains/automation/services/stage_automation_engine.py` usa shim audit | PENDENTE | **RESOLVIDO** (= C9) | sweep audit shim concluído | ✅ |
| **W5** | `services/onboarding_orchestrator.py` usa shim audit | PENDENTE | **RESOLVIDO** | `from app.shared.compliance.audit_service` confirmado | ✅ |
| **W6** | `bias_audit_service.py` em `shared/services/` (deveria estar em `shared/compliance/`) | PENDENTE | **RESOLVIDO** | canonical `shared/compliance/bias_audit_service.py` (17 732 b); shim `shared/services/bias_audit_service.py` (830 b, re-export apenas) | ✅ |
| **W7** | 89 `require_company=False` em tools | PENDENTE | **RESOLVIDO** | 18 decoradores `@tool_handler(..., require_company=False)` restantes em 7 arquivos, **todos com comentário in-line `# require_company=False kept: …`** + inventário canônico em `docs/policies/require_company_exemptions.md` + CI gate em `scripts/check_require_company_exemptions.py` (F8 / task #352). | ✅ |
| **W8** | ~~`app/tools/tool_permissions.yaml` (245 L) sem ativação~~ **(corrigido 2026-04-20)** `app/tools/tool_permissions.yaml` (245 L) — fonte declarativa ativa de scope/HITL e per-tenant LLM provider config | PENDENTE | **ATIVO** (não-PENDENTE de remoção) | YAML é lido pelo loader (consumido por `scope_config.py`, `llm_factory.py:443-461`, `tenant_budget.py:282`); documentado em `docs/specs/ai/ADR-016-tool-registration-canonical.md` §3 e `docs/specs/CANONICAL_SOURCES_SPEC.md:98`. Ver §7.4 errata. | re-classificação |
| **W9** | (idem) — não-uso silencioso | PENDENTE | **OBSOLETO** | inválido — YAML é lido (ver W8 corrigido) | re-classificação |
| **W10** | ~~`app/tools/tool_permissions_loader.py` (288 L) — único caller é o `GlobalToolRegistry` dead~~ **(corrigido 2026-04-20)** `app/tools/tool_permissions_loader.py` (288 L) — loader consumido por `scope_config.py` + `llm_factory._load_from_permissions` | PENDENTE | **ATIVO** (não-PENDENTE de remoção) | Importadores: `app/tools/scope_config.py:17-23` (`ToolPermissionsLoader, get_tools_for_scope, is_tool_allowed`) e `app/shared/providers/llm_factory.py:461` (`get_permissions`). A premissa de "único caller era o GlobalToolRegistry" estava errada — o GlobalToolRegistry nunca foi caller do loader; os callers reais são `scope_config` + `llm_factory`. Ver §7.4 errata. | re-classificação |
| **W16** | CompanySettingsReActAgent sem rotas em `domain_routing.yaml` | PARCIAL | **RESOLVIDO** | `orchestrator/domain_mappings.py:39-41` (3 mapeamentos) **+** `orchestrator/config/domain_routing.yaml:339` (`company_settings:` block) | ✅ |
| **W17** | `agent_chat_ws_router` registrado sem prefixo `/api/v1` | PENDENTE | **RESOLVIDO** | `routes.py:495` — `app.include_router(agent_chat_ws_router, prefix="/api/v1")` | ✅ |
| **W18** | `company_benefits_api.py` órfão | PARCIAL | **RESOLVIDO** | arquivo removido | ✅ |
| **W19** | (= W16) — patterns de routing | PARCIAL | **RESOLVIDO** | confirmado | ✅ |
| **W20** | `app/shared/services/audit_service.py` shim com 8 importadores | PENDENTE | **RESOLVIDO** | `grep "from app.shared.services.audit_service" lia-agent-system/app → 0` | ✅ |
| **W21** | 3 webhooks "duplicados" no routes.py | INCORRETO | **OBSOLETO** | confirmado: external/merge/mailgun são provedores distintos | confirmado |

### 3.6 Órfãos (O1-O17)

> **Critério:** `grep -rn "<symbol>" lia-agent-system/app --include='*.py'` excluindo a própria definição → 0 importers.

| ID | Arquivo (relativo a `lia-agent-system/app/`) | Status #302 | **Status #347** | Importers | Delta |
|---|---|---|---|---|---|
| **O1** | `shared/bars_evaluator.py` | PARCIAL órfão | **RESOLVIDO** | arquivo deletado (a remediação proposta — deletar — foi executada) | ✅ |
| **O2** | `shared/batch_service.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O3** | `shared/domain_action_registry.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O4** | `shared/multi_domain_plan.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O5** | `shared/param_validation.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O6** | `shared/messaging/rails_crud_consumer.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O7** | `shared/services/human_review_sampling_service.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O8** | `shared/services/intent_yaml_validator.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O9** | `shared/examples/job_planner_examples.py` | órfão | **RESOLVIDO** | pasta `examples/` deletada | ✅ |
| **O10** | `shared/examples/orchestrator_examples.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O11** | `shared/examples/pipeline_examples.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O12** | `shared/examples/sourcing_examples.py` | órfão | **RESOLVIDO** | arquivo deletado | ✅ |
| **O13** | `api/v1/lia_autonomous.py` (stub) | PARCIAL | **RESOLVIDO** | arquivo deletado | ✅ |
| **O14** | `api/v1/lia_feedback.py` (stub) | PARCIAL | **RESOLVIDO** | arquivo deletado | ✅ |
| **O15** | `api/v1/lia_multimodal.py` (stub) | PARCIAL | **RESOLVIDO** | arquivo deletado | ✅ |
| **O16** | `api/v1/lia_voice.py` (stub) | PARCIAL | **RESOLVIDO** | arquivo deletado | ✅ |
| **O17** | `api/v1/company_benefits_api.py` | PARCIAL | **RESOLVIDO** | arquivo deletado | ✅ |

### 3.7 Migração Audit Shim (I1-I32 — 32 imports listados pelo plan)

> **Resumo.** O plan listou 32 ocorrências de `from app.shared.services.audit_service`. #302 reduzia para 8 ainda ativos. **#347:** `grep` do path antigo retorna **0 ocorrências** em todo o app. Os 45 callers atuais usam o caminho canônico `from app.shared.compliance.audit_service`.

| Range | Status #302 | **Status #347** | Delta |
|---|---|---|---|
| I1-I5 (8 imports remanescentes) | PENDENTE | **RESOLVIDO (sweep completo)** | ✅ |
| I6-I32 (já migrados antes de #302) | RESOLVIDO | RESOLVIDO | — |

---

## 4. Matriz 36 Agentes × 7 Critérios — Recomputada

> **Nota sobre a contagem.** O plan original referia-se à matriz como "35 agents × 7 critérios". Re-inventário identificou **36 entidades** que satisfazem os critérios de inclusão (agents `*ReActAgent` + 1 runtime `CustomAgentRuntime` + 6 sub-agents do `recruiter_assistant` linhas 14-19 + 17 sub-agents adicionais — ver linhas individuais). Mantemos a numeração 1-36 e tratamos a discrepância como **escopo expandido** (não falso-positivo do plan); o plan subcontou um sub-agent. Todas as outras seções permanecem consistentes com a numeração final.

> **Critérios** (mesmos do plan / #302):
> 1. **Base** — `LangGraphReActBase` import direto;
> 2. **Audit** — `AuditCallback` ou `audit_callback`;
> 3. **FG** — `FairnessGuard/fairness_guard`;
> 4. **PII** — `pii_masking`/`mask_pii`/`strip_pii`;
> 5. **Tenant LLM** — `tenant_llm_context`/`get_provider_for_tenant`/`get_current_llm_tenant`;
> 6. **SPB** — `SystemPromptBuilder`;
> 7. **Reg** — listado em `agents_registry.yaml`.
>
> Convenção: `✓` = import direto verificável no arquivo; `↑✓` = herdado e **verificável** (a classe extends — direta ou indiretamente — `LangGraphReActBase`, que injeta o gate em runtime — F5 / task #352; recomputado em task #369 para sub-agents 14-29 e em task #371 para top-level *ReActAgent linhas 1-13); `↑` = herdado simbólico (não conta para score); `—` = ausente.
>
> **Política F5 (task #352, recomputada em #369 + #371).** Os critérios FairnessGuard (3), AuditCallback (2) e Tenant Context (5) podem receber `↑✓` quando: (i) há extends-relationship com `LangGraphReActBase` (direto, para top-level `*ReActAgent`s; ou indireto via `*ReActAgent` pai, para sub-agents), e (ii) a cadeia chega a `LangGraphReActBase` que injeta o gate em `langgraph_react_base.py:150-152` (AuditCallback), `:251` (FairnessGuard.check) e `:349` (tenant_llm_context). Os critérios Base (1), PII (4), SPB (6) e Reg (7) **não** aceitam inheritance-pass — F5 exige import/registro direto no arquivo do agente.

| # | Agente | Arquivo | (1) Base | (2) Audit | (3) FG | (4) PII | (5) Tenant | (6) SPB | (7) Reg | Score doc | **Score #302** | **Score #347** | Δ |
|---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|
| 1 | WizardReActAgent | `domains/job_management/agents/wizard_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 2 | PipelineTransitionAgent | `domains/pipeline/agents/pipeline_transition_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 3 | SourcingReActAgent | `domains/sourcing/agents/sourcing_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 4 | TalentReActAgent | `domains/recruiter_assistant/agents/talent_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 5 | JobsManagementReActAgent | `domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 6 | KanbanReActAgent | `domains/recruiter_assistant/agents/kanban_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 7 | PolicyReActAgent | `domains/hiring_policy/agents/policy_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 8 | AutomationReActAgent | `domains/automation/agents/automation_react_agent.py` | ✓ | ↑✓ | ↑✓ | — | ↑✓ | — | ✓ | 100% | 43% | **71%** | **+28** |
| 9 | AnalyticsReActAgent | `domains/analytics/agents/analytics_react_agent.py` | ✓ | ↑✓ | ↑✓ | — | ↑✓ | — | ✓ | 100% | 43% | **71%** | **+28** |
| 10 | CommunicationReActAgent | `domains/communication/agents/communication_react_agent.py` | ✓ | ↑✓ | ✓ | — | ↑✓ | — | ✓ | 100% | 57% | **71%** | **+14** |
| 11 | ATSIntegrationReActAgent | `domains/ats_integration/agents/ats_integration_react_agent.py` | ✓ | ↑✓ | ↑✓ | — | ↑✓ | — | ✓ | 100% | 43% | **71%** | **+28** |
| 12 | CustomAgentRuntime | `domains/agent_studio/custom_agent_runtime.py` | ✓ | ✓ | ✓ | — | — | ✓ | — | 100% | n/a (runtime) | **57%** (4 de 7 critérios verificáveis) | — |
| 13 | AutonomousReActAgent | `domains/autonomous/agents/autonomous_react_agent.py` | ✓ | ✓ | ✓ | — | ↑✓ | ✓ | ✓ | 95% | 86% | **86%** | 0 |
| 14 | KanbanActionAgent | `domains/recruiter_assistant/agents/kanban_action_agent.py` | ↑ | ↑✓ | ✓ | — | ↑✓ | — | — | 95% | 29% | **43%** | **+14** |
| 15 | KanbanSearchAgent | `domains/recruiter_assistant/agents/kanban_search_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 16 | KanbanInsightAgent | `domains/recruiter_assistant/agents/kanban_insight_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 17 | PipelineActionAgent | `domains/pipeline/agents/pipeline_action_agent.py` | ↑ | ↑✓ | ✓ | — | ↑✓ | — | — | 95% | 29% | **43%** | **+14** |
| 18 | PipelineContextAgent | `domains/pipeline/agents/pipeline_context_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 19 | PipelineDecisionAgent | `domains/pipeline/agents/pipeline_decision_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 20 | SourcingPlannerAgent | `domains/sourcing/agents/sourcing_planner_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 21 | SourcingSearchAgent | `domains/sourcing/agents/sourcing_search_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 22 | SourcingEnrichAgent | `domains/sourcing/agents/sourcing_enrich_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 23 | SourcingEngagementAgent | `domains/sourcing/agents/sourcing_engagement_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 24 | DiversitySourcingAgent | `domains/sourcing/agents/diversity_sourcing_agent.py` | ↑ | ↑✓ | ✓ | — | ↑✓ | — | — | 95% | 29% | **43%** | **+14** |
| 25 | GithubSourcingAgent | `domains/sourcing/agents/github_sourcing_agent.py` | ↑ | ↑✓ | ✓ | — | ↑✓ | — | — | 95% | 29% | **43%** | **+14** |
| 26 | NurtureSequenceAgent | `domains/sourcing/agents/nurture_sequence_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 27 | PassivePipelineAgent | `domains/sourcing/agents/passive_pipeline_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 28 | ReferralAgent | `domains/sourcing/agents/referral_agent.py` | ↑ | ↑✓ | ↑✓ | — | ↑✓ | — | — | 95% | 14% | **43%** | **+29** |
| 29 | StackOverflowSourcingAgent | `domains/sourcing/agents/stackoverflow_sourcing_agent.py` | ↑ | ↑✓ | ✓ | — | ↑✓ | — | — | 95% | 29% | **43%** | **+14** |
| 30 | PipelineReActAgent (cv_screening) | `domains/cv_screening/agents/pipeline_react_agent.py` | ✓ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 31 | CompanySettingsReActAgent | `domains/company_settings/agents/company_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (mappings + yaml) | 80% | 43% | **57%** | **+14** |
| 32 | JobWizardGraph | `domains/job_management/agents/job_wizard_graph.py` | — | ✓ | ✓ | ✓ | — | — | ✓ | 60% | 57% | **57%** | 0 |
| 33 | WSIInterviewGraph | `domains/cv_screening/agents/wsi_interview_graph.py` | — | ✓ | ✓ | ✓ | ✓ | — | — | 55% | 43% | **57%** | **+14** |
| 34 | InterviewGraph | `domains/interview_scheduling/agents/interview_graph.py` | — | ✓ | ✓ (L2 BLOCK + REGENERATE — F4) | ✓ | ✓ | — | — | 50% | 29% | **57%** | **+28** |
| 35 | PolicySetupAgent | `domains/policy/agents/agent.py` | ✓ | — (usa `audit_service.log_decision` direto) | ✓ | ✓ | ✓ | ✓ | — | 25% | 0% | **71%** | **+71** |
| 36 | JobCreationGraph | `domains/job_creation/graph.py` | — | ✓ | ✓ | ✓ | — | — | — | 5% | 0% | **57%** | **+57** |

**Notas:**
- **Top-level `*ReActAgent` (linhas 1-13) — recompute task #371.** A mesma regra de herança F5 aplica-se aos top-level: cada agente declara `class XxxReActAgent(LangGraphReActBase, EnhancedAgentMixin)` (verificado por `grep "class \w+ReActAgent\("` em `app/domains/**/agents/*react_agent.py` — 13/13 arquivos). A cadeia direta para `LangGraphReActBase` injeta os 3 gates em runtime nas mesmas linhas (`:150-152`, `:251`, `:349`). Critérios `(2) Audit` e `(5) Tenant` (e `(3) FG` quando o arquivo não importa diretamente — rows 8/9/11) migram de `—` para `↑✓`. Linhas 1-7 e 10 sobem de 57% → **71%**; linhas 8/9/11 sobem de 43% → **71%**; linha 13 (AutonomousReActAgent) ganha `↑✓` em Tenant mas score permanece 86% (já era PASS implícito). Linha 12 (CustomAgentRuntime) está fora do escopo F5/#371 — não é um `*ReActAgent`, é um runtime; mantém score 57%.
- **Sub-agents (linhas 14-29) — recompute task #369.** A herança de `LangGraphReActBase` é por composição estrutural: cada sub-agent declara `class XxxAgent(YyyReActAgent)` (Python class inheritance), e a cadeia `Yyy ReActAgent → LangGraphReActBase` injeta os 3 gates em runtime — `FairnessGuard.check()` (`libs/agents-core/lia_agents_core/langgraph_react_base.py:251`), `AuditCallback` (`:150-152`) e `tenant_llm_context.get_current_llm_tenant()` (`:349`). Verificação satisfeita para os 16 sub-agents. Critérios marcados `↑✓` (PASS por composição verificável): **(2) Audit, (3) FG, (5) Tenant**. Critérios mantidos `↑`/`—` (gap aberto, F5 exige no próprio arquivo): **(1) Base, (4) PII, (6) SPB, (7) Reg**. Score uniforme: **43%** (3/7).
- **Sub-agents — gaps remanescentes (transparência).** Todos os 16 sub-agents têm `b=↑` (extends parent, não LangGraphReActBase direto), `p=—` (PII masking ocorre no base mas F5 não permite herança nesse critério), `s=—` (SPB ocorre no base mas idem) e `Reg=—` (sub-agents não estão em `agents_registry.yaml`, expostos só via parent). Esses 4 critérios continuam abertos por design — não são compliance gaps.
- **Mais movimento**: `JobCreationGraph` passou de 5%→57% (PARCIAL conforme A1), `PolicySetupAgent` de 25%→71% (PARCIAL/RESOLVIDO conforme A2), `WSIInterviewGraph` de 55%→57% e `InterviewGraph` de 50%→**57%** (F4 / task #352 adicionou FairnessGuard L2 com política BLOCK + REGENERATE em `interview_graph.py:339-462` + audit `decision="blocked"`). Sub-agents 14-29: 14%/29% → **43% uniforme** (recompute F5 em task #369). Top-level `*ReActAgent` 1-13: 43%/57%/86% → **71% uniforme (exceto linha 13 que permanece 86%)** (recompute F5 em task #371).
- **Discrepância de contagem persiste:** doc diz "35 agents" mas tabula 36 linhas. Mantemos as 36 para fidelidade.

---

## 5. Reconciliação por Dimensão (Stage do plan)

| Stage | Findings totais | RESOLVIDO | PARCIAL | PENDENTE | INCORRETO | OBSOLETO | % progresso |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Stage 1 — Hotfixes** | 4 (R1, C8, R5/R6, sweep audit shim) | 3 (R1, C8, sweep) | 0 | 0 | 0 | 1 (R5/R6 — falso-positivo do plan) | **100%** (excluindo OBSOLETO) |
| **Stage 2 — Compliance Gates** | 9 (C1-C7, R2, R7) | 9 (C1-C7, R2, R7) | 0 | 0 | 0 | 0 | **100%** |
| **Stage 3 — Tools System** | 8 (T1-T3, W7-W10) | 4 (T2, T3, W7 -66 ocorrências, W7 resíduo de 18 documentado em F8 / task #352) | 0 | 4 (T1, W8, W9, W10) | 0 | 0 | **50%** |
| **Stage 4 — Agents Compliance** | 12 (A1-A4, W16-W17, W19, sub-agents 14-29 contados como 5 buckets) | 9 (A3 — F4 task #352, W16, W17, W19, sub-agents 14-29 — F5 recompute task #369; top-level `*ReActAgent` 1-13 também recomputado em task #371 como rebuild de scorecard) | 3 (A1, A2, A4) | 0 | 0 | 0 | **75%** |
| **Stage 5 — Cleanup** | 17 (D1-D3, W6, W11-W15, O1-O17, P14 156 shims) | 14 (D1-D3, W6, W11-W15, O1-O17) | 1 (P14 shims sem SLA) | 2 (T1/registry paralelo, W8/W10 dead) | 0 | 0 | **82%** |
| **Stage 6 — Observability** | 11 moves + 4 docs (P16-P20) = 15 | 11 (moves canônicos via Tarefa #343) | 4 (refresh de docs ARCHITECTURE.md §9.4 + CANONICAL_SOURCES_SPEC.md + CLAUDE.md + ADRs) | 0 | 0 | 0 | **73%** (código 100%; docs ~0%) |
| **Falsos-positivos do plan** | 5 (R5, R6, W21, sub-claim A1 "órfão", sub-claim W16/W19 "sem rota") | — | — | — | — | 5 | — |

---

## 6. Findings INCORRETO e OBSOLETO — discriminação explícita

> Esta seção formaliza a separação entre as duas situações que poderiam, em leitura apressada, ser confundidas.

### 6.1 Findings `INCORRETO` (código implementado mas com bug ou cobertura errada)

**Nenhum.** Auditoria não identificou nenhum caso em que a remediação foi implementada e está funcionalmente errada. Todo finding `RESOLVIDO` listado em §3 foi grep-validado contra os critérios canônicos correspondentes (FairnessGuard SSOT, `audit_service` canônico, prefixo de rota, sweep de imports, etc.). Findings que **ainda não foram remediados** estão classificados como `PENDENTE`/`PARCIAL`, não `INCORRETO`.

### 6.2 Findings `OBSOLETO` — falsos-positivos do plan original

> O plan listou estes itens como problemas. Re-verificação confirma que ou (a) o problema descrito nunca existiu no código, ou (b) ele desapareceu por refactor antes de qualquer ação dirigida ao finding. Em ambos os casos a remediação proposta **não se aplica mais** e o finding deve ser fechado sem trabalho adicional.

| ID | Diagnóstico do plan | Por que é falso-positivo | Recomendação |
|---|---|---|---|
| **R5** | `llm_config_router` incluído 2× em `routes.py` | `grep -nE "llm_config_router" lia-agent-system/app/api/routes.py` retorna **1** import (`:260`) e **1** include (`:426`). Único registro. | Fechar. |
| **R6** | `webhooks.router` incluído 2× em `routes.py` | `routes.py:529` é o único include de `webhooks.router`. | Fechar. |
| **W21** | 3 webhooks duplicados | `routes.py:532-534` são `external_webhooks`, `merge_webhooks`, `mailgun_webhooks` — **3 provedores distintos**, não duplicação. | Fechar. |
| **A1 (sub-claim "JobCreationGraph órfão")** | Plan/CODE_AUDIT sugeriu que `JobCreationGraph` era órfão | Sempre foi consumido por `domains/job_creation/domain.py:27`. Gap real era exclusivamente compliance — registrado em §3 como `PARCIAL`. | A parte "órfão" é OBSOLETA; a parte "compliance" continua tracked como A1=PARCIAL em §3. |
| **W16/W19 (sub-claim "CompanySettingsReActAgent sem rota")** | Plan disse que faltava rota/mapping | Já estava em `orchestrator/domain_mappings.py:39-41` antes de #302; também em `orchestrator/config/domain_routing.yaml:339`. | A parte "sem rota" é OBSOLETA; o finding em §3 fica `RESOLVIDO`. |

---

## 7. Validação Cruzada Específica

### 7.1 routes.py
- `llm_config_router`: linhas **260** (import) e **426** (include). **1 include**. → R5 **OBSOLETO/INCORRETO**.
- `webhooks.router`: linha **529**. **1 include**. → R6 **OBSOLETO/INCORRETO**.
- `agent_chat_ws_router`: linhas **212** (import), **495** (include com `prefix="/api/v1"`). → W17 **RESOLVIDO**.
- `agent_chat_sse_router`: linhas **213** (import), **496** (include com `prefix="/api/v1"`).
- `external_webhooks/merge_webhooks/mailgun_webhooks`: linhas **532-534** — 3 routers distintos. → W21 **OBSOLETO**.

### 7.2 Estado de `shared/observability/` (atualizado 2026-04-17)
`app/shared/observability/__init__.py` — **512 bytes** (8 linhas) com cabeçalho documental indicando que os legacy paths foram removidos na Tarefa #343 (referência a `scripts/check_forbidden_imports.py`). Os **11 módulos canônicos** estão presentes em `app/shared/observability/`:

```
agent_health_alert_service.py    structured_logging.py
agent_monitoring_service.py      token_budget_service.py
callbacks.py                     token_tracking_service.py
drift_alert_service.py           tracing.py
__init__.py                      wsi_observability.py
langsmith.py                     model_drift_service.py
```

Os **11 paths legados** correspondentes foram **deletados sem shim** (verificados MISSING via `[ -f ... ]`):
- `app/shared/tracing.py` ❌
- `app/shared/llm/callbacks.py` ❌
- `app/shared/governance/agent_monitoring_service.py` ❌
- `app/shared/services/agent_health_alert_service.py` ❌
- `app/shared/services/drift_alert_service.py` ❌
- `app/shared/services/model_drift_service.py` ❌
- `app/shared/services/structured_logging.py` ❌
- `app/shared/services/wsi_observability.py` ❌
- `app/domains/credits/services/token_tracking_service.py` ❌
- `app/domains/credits/services/token_budget_service.py` ❌
- `app/config/langsmith.py` ❌

**41 importadores** já usam o caminho canônico `from app.shared.observability...` (`grep -rn "from app.shared.observability" app --include="*.py" | wc -l = 41`). **Stage 6 código: RESOLVIDO.** Resíduo doc-only: refresh de `ARCHITECTURE.md` §9.4, `CANONICAL_SOURCES_SPEC.md`, `CLAUDE.md`.

### 7.3 W7 — `require_company=False` (perfil das 18 ocorrências restantes)
`grep -rn "@tool_handler.*require_company=False" app --include="*.py" | wc -l` = **18**. Todas marcadas com comentário `# require_company=False kept: …` justificando isenção. Distribuição **canônica** (recontagem 2026-04-17):

| Arquivo | Decoradores |
|---|---:|
| `pipeline/agents/pipeline_tool_registry.py` | 5 |
| `recruiter_assistant/agents/kanban_tool_registry.py` | 3 |
| `hiring_policy/agents/policy_tool_registry.py` | 3 |
| `autonomous/agents/autonomous_tool_registry.py` | 3 |
| `talent_intelligence/tools/skills_ontology_tools.py` | 2 |
| `talent_intelligence/tools/market_intelligence_tools.py` | 1 |
| `sourcing/agents/sourcing_tool_registry.py` | 1 |
| **Total** | **18** |

→ Risco residual: BAIXO. Cada call site tem rationale documentado in-line, inventário canônico em `docs/policies/require_company_exemptions.md` (F8 / task #352) e CI gate em `scripts/check_require_company_exemptions.py`. **Status: RESOLVIDO** (não mais PARCIAL).

### 7.4 T1/T3/W8/W10 — Tool System (atualizado 2026-04-20 — correção da premissa de "dead code")

> **Errata 2026-04-20.** A versão anterior desta seção (e o item §1.2 #1 e §9.4) afirmava que `app/tools/registry.py` era um "registry paralelo" com apenas 30 callers em 2 arquivos, e que `tool_permissions.yaml` + `tool_permissions_loader.py` estavam "sem consumidores após a deleção do GlobalToolRegistry" e podiam ser removidos. **Ambas afirmações eram incorretas** e Task #373 foi aberta com base nessa premissa errada (e não pôde ser executada). Verificação fresca abaixo.

- ~~`app/shared/global_tool_registry.py` (259 L) — classe `GlobalToolRegistry` definida; **0 callers em produção**~~ — **DELETADO** (T3 RESOLVIDO via deleção; canary `TestF12GlobalToolRegistryDeadCanary` impede ressurreição).
- `app/tools/registry.py` (169 L) — define o `tool_registry` (instância singleton de `ToolRegistry`) que é o **registry canônico** do sistema, não um registry paralelo. É instanciado em `app/tools/__init__.py` (linha 18) e populado por `initialize_tools()` (linhas 92-127), chamado em boot por `app/main.py:35`. **Consumidores diretos:** `app/tools/executor.py:18` (executor que despacha tools), `app/orchestrator/orchestrator.py:37` (`from app.tools import ... tool_registry`), `app/orchestrator/agentic_loop.py:35`, `app/domains/ai/services/tool_executor_service.py:13`, `app/domains/job_management/agents/job_wizard_graph.py:34`. **Caller files que registram tools** (`grep -rln "from app.tools.registry" app/ → 18 arquivos`): `app/domains/sourcing/tools/{enrichment_tools,query_tools}.py`, `app/domains/job_management/tools/{job_tools,job_wizard_tools,query_tools}.py`, `app/domains/cv_screening/tools/{candidate_tools,cv_upload_tool,cv_match_tool}.py`, `app/domains/communication/tools/communication_tools.py`, `app/domains/analytics/tools/analytics_query_tools/registry.py`, `app/domains/automation/tools/automation_tools.py`, `app/domains/recruiter_assistant/tools/pipeline_tools.py`, `app/domains/talent_intelligence/tools/registry.py`, `app/domains/company_settings/tools/import_tools.py`, `app/shared/tools/export_tools.py`. **`@tool_handler` é um decorator de checagem por-função (tenant + audit) e não é um substituto de registry**: ele não mantém um catálogo enumerável consultável pelo executor/orquestrador. **STATUS: ATIVO (não-paralelo); migração para `@tool_handler` exige co-design de um substituto enumerável + reescrita de TODOS os 18 caller files + adaptação do executor/orquestrador.**
- `app/tools/tool_permissions.yaml` (245 L) e `app/tools/tool_permissions_loader.py` (288 L) — **NÃO são dead code.** Consumidores ativos verificados:
  - `app/tools/scope_config.py:17-23` importa `ToolPermissionsLoader`, `get_tools_for_scope`, `is_tool_allowed`. `scope_config` alimenta o orquestrador e o `tool_executor_service` com o mapeamento `scope → [tool_names]` (escopos UI: `TALENT_FUNNEL`, `JOB_TABLE`, `IN_JOB`) e a lista `restricted_tools` que exigem HITL.
  - `app/shared/providers/llm_factory.py:461` importa `from app.tools.tool_permissions_loader import get_permissions` dentro de `_load_from_permissions(...)` — usa o YAML como fonte de defaults globais de `llm_provider` e `llm_fallback_order` por tenant (4ª camada da cadeia DI documentada nas linhas 443-446).
  - `app/orchestrator/tenant_budget.py:282` referencia o YAML como fonte canônica de config per-tenant (`llm_provider` + `llm_fallback_order`).
  - Documentado em `docs/specs/ai/ADR-016-tool-registration-canonical.md` §3 ("`tool_permissions.yaml` continua, com escopo reduzido") e em `docs/specs/CANONICAL_SOURCES_SPEC.md:98` ("Scope/governance: `app/tools/tool_permissions.yaml`").
  - **STATUS: ATIVO.** Remoção é uma migração arquitetural (mover scope/HITL config + per-tenant LLM provider config para outra fonte e atualizar `scope_config.py` + `llm_factory._load_from_permissions` + `tenant_budget.py`), **não** um cleanup de dead code.

→ Decisão pendente para Stage 5/3 — **rescopada em 2026-04-20:**
  - (a) Tratar `app/tools/registry.py` + loader/yaml como **subsistema canônico ativo**; qualquer migração para `@tool_handler` deve seguir ADR-016 e cobrir todos os 18 caller files + executor + orchestrator + scope_config + llm_factory + tenant_budget. **Não** abrir tarefas que pressuponham "deletar" sem migração equivalente. **Não** abrir tarefas que escopem só `talent_intelligence` + `analytics_query_tools` ("30 calls em 2 arquivos") — esse escopo está incompleto.
  - (b) Se ADR-016 indicar manter, encerrar T1/W8/W10 como **CANÔNICO ATIVO** (não PENDENTE de remoção). Atualizar §1.2 e §9b.2 nesse caso.

---

## 8. Análise Crítica do Diagnóstico Original (Atualizada)

### 8.1 Onde o doc continua certo
- Mapeamento dos 5 cv_screening scoring services (C1-C5) **identificou o gap correto**: hoje todos os 5 importam `scoring_safeguards` (FairnessGuard + audit) — **gap fechado** após o doc original.
- IDOR em `finetuning_export.py` (R1) **identificou o gap real**: hoje endpoints exigem `Depends(get_current_user)` + `audit_service.log_decision` — **gap fechado**.
- Estrutura proposta para `shared/observability/`: arquitetonicamente correta; **executada na Tarefa #343** (11 moves + 11 deleções de legacy + 41 importadores canônicos).
- Tool system: `GlobalToolRegistry` confirmado morto e **deletado**. ~~`app/tools/registry.py` paralelo~~ (corrigido 2026-04-20) — `app/tools/registry.py` é o registry **canônico** wired por `initialize_tools()`, não paralelo; `tool_permissions.yaml` + loader são **ativos** (consumidos por `scope_config.py` + `llm_factory.py`). Ver §7.4 errata.

### 8.2 Onde o doc estava errado (falsos-positivos)
- R5, R6, W21 (rotas duplicadas): inexistentes (ver §6).
- JobCreationGraph "órfão": sempre conectado.
- CompanySettings "sem rota": já mapeado em `domain_mappings.py`.

### 8.3 O que envelheceu desde o plan
- T2 (5 legacy @tool): **completamente migrado**.
- Sweep audit shim (W4, W5, W20, C9, I1-I5): **100% concluído**.
- Bias detectors (D1): **3 implementações agora delegam ao FairnessGuard SSOT**.
- C8 (PII import): **resolvido**.
- Duplicatas D2/D3/W11-W15: **uma cópia em cada caso**.
- Stubs `lia_*` + `company_benefits_api` (O13-O17): **deletados**.
- 12 órfãos (O1-O12): **deletados**.
- `agent_chat_ws` prefix (W17), `bias_audit_service` location (W6): **resolvidos**.

### 8.4 Onde o doc poderia ser mais preciso
- "Score doc" 95% para sub-agents por herança implícita continua sendo escolha do plan, não verdade do código (linhas 14-29 verificadas: ≤29% no arquivo).
- Estimativas de esforço: pipeline_tool_registry tem 99 458 bytes (XL/L), não L como sugerido.
- "Ativar ou deletar GlobalToolRegistry": após 30 dias adicionais sem callers, **deletar** é a única ação racional.
- ~~Loader/yaml `tool_permissions` "sem consumidor após deleção do GlobalToolRegistry"~~ (corrigido 2026-04-20) — premissa errada do snapshot anterior; loader é consumido por `scope_config.py` + `llm_factory.py:461`, e o GlobalToolRegistry nunca foi caller do loader. Ver §7.4 errata.

---

## 9. Recomendações de Próximas Tarefas

> **Princípio.** Listamos apenas o que efetivamente falta. Tarefas já em fila ou já executadas não são repetidas.

### 9.1 Hotfix imediato (1 sprint, < 4 h)
- ~~**F1.** R1 — Adicionar `Depends(get_current_user)` + checagem `current_user.company_id == company_id` em `api/v1/finetuning_export.py:11-26`.~~ **✅ RESOLVIDO em 2026-04-17** — `finetuning_export.py` agora importa `get_current_user` + `audit_service`; ambos endpoints chamam `Depends(get_current_user)` + `audit_service.log_decision` em sucesso e falha. Único hotfix de Stage 1 fechado.

### 9.2 Compliance gates (5 dias úteis)
- ~~**F2.** C1-C5 — Adicionar `FairnessGuard.check()` pre + `audit_service.log_decision()` post nos 5 scoring services~~ **✅ RESOLVIDO em 2026-04-17** — Os 5 services (`cv_scoring_service.py`, `lia_score_service.py`, `pre_qualification_service.py`, `eligibility_verification_service.py`, `evaluation_criteria_service.py`) agora importam `from app.shared.compliance.scoring_safeguards import run_fairness_check, log_scoring_decision, FairnessBlockedError, hash_payload` e aplicam a política fail-closed (FG indisponível → `FairnessBlockedError` + audit `decision="blocked"`).

### 9.3 Agentes — completar A1-A4
- **F3.** A1 — Migrar `JobCreationGraph` para herdar `LangGraphReActBase` (atualmente b=0; FG/PII/Audit já presentes).
- **F4.** A3 — Adicionar `FairnessGuard.check()` no `InterviewGraph` (atualmente f=0). **✅ RESOLVIDO em task #352** — `interview_graph.py:339-366` agora roda `check_fairness()` fail-open sobre `response_data["message"]` ao final do `ainvoke`, com paridade ao WSI L2 e fitness `TestF4InterviewGraphFairnessGuard`.
- **F5.** Sub-agents ReAct (linhas 14-29 da matriz) — **política definida em task #352, opção (a) — composição:**
  - **Decisão.** Gates compliance (FairnessGuard, PII masking, AuditCallback, tenant context) ficam **na base** (`LangGraphReActBase` + `react_loop_factory`). Sub-agents **não** importam diretamente esses módulos; o gate é aplicado na fronteira do react_loop pai.
  - **Scoring derivado.** Para a matriz 36×7, sub-agents recebem score do gate por **composição verificável** quando há um vínculo estrutural entre sub-agent e pai — satisfeito por **qualquer** das duas evidências, ambas equivalentes para o ciclo de vida do gate: (a) o pai (`*_react_agent.py`) instancia o sub-agent dentro do grafo (AST: `cls(...)` ou registrado em `sub_agents=[...]`); **ou** (b) o sub-agent estende o pai por herança Python (`class XxxAgent(YyyReActAgent)`) — caminho mais forte, pois o gate herdado pela MRO do pai roda em toda execução do sub-agent. Em ambos os casos exige-se também que o pai (ou a base que o pai estende — `LangGraphReActBase` em `libs/agents-core/lia_agents_core/langgraph_react_base.py`) satisfaça `f≥1, a≥1, t≥1` no critério respectivo. A coluna passa de `↑` (herança simbólica) para `↑✓` (herança verificável) somente quando vínculo estrutural + satisfação na cadeia valem.
  - **Critério de auditoria.** A linha do sub-agent é tratada como **PASS** apenas em FairnessGuard (f), AuditCallback (a) e Tenant Context (t) — nunca em SystemPrompt (s) nem Base ReAct (b), que continuam exigidos no próprio arquivo do sub-agent.
  - **Não-fazer.** Não duplicar gates nos sub-agents (anti-pattern); não promover sub-agent a top-level só para satisfazer scorecard. Caso um sub-agent precise de FG/Audit *adicional* (e.g., decisão automatizada própria), promova-o a `*_react_agent.py` com base própria.
  - **Operacionalização.** ✅ **RESOLVIDO em task #369** — recompute aplicado neste snapshot. Linhas 14-29 da matriz §4 agora exibem `↑✓` em FairnessGuard, AuditCallback e Tenant Context (verificação: `class XxxAgent(YyyReActAgent)` + cadeia até `LangGraphReActBase` em `libs/agents-core/lia_agents_core/langgraph_react_base.py:150-152, 251, 349`). Score uniforme 43% (3/7). Item #8 do Top 10 (§1.2) fechado.

### 9.4 Tool system — decisão arquitetural (corrigido 2026-04-20)

> **Correção 2026-04-20.** As tarefas F6 e F7 abaixo (em sua forma original) foram emitidas com base em premissas incorretas — ver §7.4 errata. Substituídas por F6′/F7′.

- **F6.** ~~Deletar `app/shared/global_tool_registry.py`~~ **✅ RESOLVIDO via deleção (T3)**. ~~Resta deletar `app/tools/tool_permissions.yaml` + `app/tools/tool_permissions_loader.py` (W8, W10) — sem callers após remoção do `GlobalToolRegistry`.~~ **❌ Premissa incorreta — NÃO executar.** O loader é importado por `app/tools/scope_config.py` (orquestrador + `tool_executor_service`) e por `app/shared/providers/llm_factory.py:461` (per-tenant LLM provider selection); o YAML também é referenciado por `app/orchestrator/tenant_budget.py:282`. Task #373 foi aberta nessa premissa errada e não pôde ser executada.
- **F6′.** Se a remoção do loader/yaml ainda for desejada, abrir tarefa que primeiro **migre** `scope_config.py`, `llm_factory._load_from_permissions` e `tenant_budget.py` para outra fonte de verdade (ex.: tabela `tenant_llm_configs` já existente — ver `scripts/migrate_yaml_llm_to_db.py`). Só então deletar yaml + loader. **Esforço:** M (não XS).
- **F7.** ~~Migrar 30 calls `tool_registry.register(ToolDefinition(…))` em `domains/talent_intelligence/tools/registry.py` e `domains/analytics/tools/analytics_query_tools/registry.py` para `@tool_handler(domain=…)`. Depois, deletar `app/tools/registry.py` (T1).~~ **❌ Escopo incompleto — NÃO executar como descrito.** `app/tools/registry.py` é o registry **canônico** wired por `initialize_tools()` em `app/tools/__init__.py` e consumido pelo `executor`, `orchestrator`, `agentic_loop`, `tool_executor_service` e `job_wizard_graph`. Há **18 caller files** registrando tools (não 2), distribuídos por ~14 módulos de domínio (sourcing, job_management, cv_screening, communication, analytics, automation, recruiter_assistant, talent_intelligence, company_settings, shared/tools). `@tool_handler` é um decorator de checagem por-função, não um substituto de registry enumerável.
- **F7′.** Se uma migração para `@tool_handler` (ou outro registry decorator-based) ainda for desejada, ela deve seguir o caminho descrito em `docs/specs/ai/ADR-016-tool-registration-canonical.md` e cobrir: (i) co-design de um catálogo enumerável que substitua `tool_registry.list_tools()` / `get_schemas_for_agent()`; (ii) reescrita de TODOS os 18 caller files; (iii) adaptação de `app/tools/executor.py`, `app/orchestrator/orchestrator.py`, `app/orchestrator/agentic_loop.py`, `app/domains/ai/services/tool_executor_service.py`, `app/domains/job_management/agents/job_wizard_graph.py`. **Esforço:** L–XL. Alternativa: encerrar T1/W8/W10 como **CANÔNICO ATIVO** e atualizar §1.2/§9b.2.
- **F8.** Cobrir as 18 `require_company=False` restantes em uma checagem cruzada YAML × código (W7 resíduo). **✅ RESOLVIDO em task #352** — `docs/policies/require_company_exemptions.md` (inventário canônico) + `lia-agent-system/scripts/check_require_company_exemptions.py` (CI gate) + fitness `TestF8RequireCompanyExemptionsDocumented`.

### 9.5 Stage 6 — Observability (paralelo, 3-5 dias)
- **F9.** ~~Implementar Stage 6 conforme plano (P16-P20): mover 11 arquivos, criar 11 shims, atualizar 10 consumidores diretos~~ **✅ RESOLVIDO no código em Tarefa #343** — 11 módulos movidos para `app/shared/observability/`, 11 paths legados deletados sem shim (CI gate em `scripts/check_forbidden_imports.py`), 41 importadores migrados para o caminho canônico. **Resta apenas refresh doc-only**: atualizar `ARCHITECTURE.md` §5.1 e §9.4, `CANONICAL_SOURCES_SPEC.md`, `CLAUDE.md` para refletir o novo path canônico `app.shared.observability.*`.

### 9.6 Higiene
- **F10.** SLA para 156 shims backward-compat: adicionar tag `@deprecated since=YYYY-MM-DD` e regra de remoção (ex.: 0 importadores há 90 dias). **✅ RESOLVIDO em task #352** — política em `docs/policies/shim_sla.md`; cabeçalhos `@deprecated since=2026-04-17` aplicados aos 10 shims `RAILS-DEPRECATED` em `app/shared/`; fitness `TestF10ShimSlaHeaders` impede regressão. Os 146 shims restantes são re-exports puros, removidos em batch quando `integrations_hub` cobrir 100% das chamadas.
- **F11.** CI lint proibindo `from langchain_core.tools import tool` em `app/domains/*/tools/` (regressão de T2). **✅ RESOLVIDO em task #352** — `lia-agent-system/scripts/check_no_langchain_tool_decorator.py` + step `F11 — block langchain_core @tool decorator regression` em `.github/workflows/ci.yml.disabled` + fitness `TestF11NoLangchainToolDecoratorRegression`.
- **F12.** Smoke test de boot: verificar que `GlobalToolRegistry._registry` está populada — força "ativar ou deletar" no CI. **✅ RESOLVIDO via deleção em task #352** — `app/shared/global_tool_registry.py` foi confirmado deletado (0 callers). O canary `TestF12GlobalToolRegistryDeadCanary` falha se o módulo voltar a existir sem callers, mantendo a pressão "ativar ou deletar" sem precisar do registry vivo.

### 9.7 Não-fazer (decisões já implícitas)
- **NF1.** Não reabrir R5, R6, W21 — falsos-positivos confirmados em duas auditorias.
- **NF2.** Não tentar "ativar" `GlobalToolRegistry`: dead code seguro de remover.
- **NF3.** (adicionado 2026-04-20) Não abrir tarefa de "deletar `app/tools/tool_permissions.yaml` + `tool_permissions_loader.py`" como cleanup pontual — ambos têm consumidores ativos (`scope_config.py`, `llm_factory.py:461`, `tenant_budget.py:282`). Qualquer remoção requer migração arquitetural (F6′ em §9.4). Task #373 foi aberta nessa premissa errada e marcada como tal.
- **NF4.** (adicionado 2026-04-20) Não tratar `app/tools/registry.py` como "registry paralelo" com 2 callers / 30 calls. É o registry **canônico** (18 caller files + executor + orchestrator). Migração para `@tool_handler` ou outro substituto é XL e exige F7′ em §9.4.

---

## 9b. Crosswalk Findings × Project Tasks

> Mapeia cada finding (ou bloco de findings) à tarefa de remediação correspondente em `.local/tasks/` e indica o estado **inferido** dela a partir do estado do código de hoje. Estado do código é a fonte da verdade; a inferência segue a regra: se o código satisfaz os critérios canônicos do finding, a tarefa correspondente é tratada como **MERGED/concluída**; se o código segue inalterado, a tarefa é **PENDING/PROPOSED** e deve ficar em fila; se a auditoria desta semana mostra que o problema descrito não existia (OBSOLETO), a tarefa pode ser **cancelada**.

### 9b.1 Tarefas que podem ser fechadas (MERGED inferido a partir de evidência fresca)

| Finding(s) atendido | Slug da task em `.local/tasks/` | Evidência canônica | Ação sugerida |
|---|---|---|---|
| **R1** (RESOLVIDO em 2026-04-17) | (follow-up #348 desta auditoria) | `api/v1/finetuning_export.py` agora com `Depends(get_current_user)` + `audit_service.log_decision` em ambos endpoints | Fechar como MERGED |
| **C1-C5** (RESOLVIDO em 2026-04-17) | (follow-up #349 desta auditoria) | Os 5 scoring services importam `app.shared.compliance.scoring_safeguards` (FG fail-closed + log_scoring_decision) | Fechar como MERGED |
| **T3** (RESOLVIDO via deleção) | (follow-up #350 desta auditoria) | `app/shared/global_tool_registry.py` deletado; canary `TestF12GlobalToolRegistryDeadCanary` (F12 / task #352) | Fechar como MERGED |
| **A3** (RESOLVIDO em F4 / task #352) | `audit-interview-graphs-compliance.md` (sub-parte) | `interview_graph.py:341-471` aplica `check_fairness` (FG L2) com BLOCK + REGENERATE + audit `decision="blocked"` | Fechar como MERGED |
| **Stage 6 — código** (RESOLVIDO em task #343) | `audit-observability-canonical.md` (parte de código) | `app/shared/observability/__init__.py` 512 b + 11 módulos canônicos + 11 paths legados deletados + 41 importadores; CI gate em `scripts/check_forbidden_imports.py` | Fechar como MERGED para escopo "código"; manter aberto sub-item "refresh docs" |
| **W7** (RESOLVIDO em F8 / task #352) | `audit-require-company-sweep.md` | 18 decoradores documentados em `docs/policies/require_company_exemptions.md` + CI gate `scripts/check_require_company_exemptions.py` | Fechar como MERGED |
| R2 | `audit-applications-apply-compliance.md` | `api/v1/applications.py:21,67-68,225-275,345` | Fechar como MERGED |
| R3 | `audit-bulk-actions-compliance.md` | `api/v1/bulk_actions.py:16,22-30,37-94` | Fechar como MERGED |
| R4 | (parte da `audit-bulk-actions-compliance.md` ou tarefa equivalente) | `api/v1/stage_transition_automation.py:21-28,61,504-551` | Fechar como MERGED |
| R7 / W1 | `audit-chat-sse-compliance.md` | `api/v1/agent_chat_sse.py:45-46,234,403` | Fechar como MERGED |
| W17 | `audit-chat-ws-prefix.md` | `api/routes.py:495` (`prefix="/api/v1"`) | Fechar como MERGED |
| W2 / W3 | `audit-unified-chat.md` | `chat.py:222,268,608-616,898`; `agent_chat_ws.py:52,661,951` | Fechar como MERGED |
| C8, C9, W4, W5, W20, I1-I5 | `audit-hotfix-imports-canonicos.md` + `audit-shim-mapper-conflicts.md` | `grep "from app.shared.services.audit_service" → 0`; `grep "pii_filter" → 0`; `stage_automation_engine.py:444` | Fechar como MERGED |
| T2 | `audit-migrate-tool-handler.md` | `grep "from langchain_core.tools import tool" lia-agent-system/app/domains → 0`; 5 arquivos com `@tool_handler` | Fechar como MERGED |
| C6, C7 | `audit-feedback-sourcing-compliance.md` | `sourcing_pipeline_service.py:478-577,664-677`; `candidate_feedback_service.py:227,445-520` | Fechar como MERGED |
| D1 | `audit-bias-consolidation.md` | `bias_detector_service.py:26-33`; `interview_intelligence_tools.py:14-20`; `jd_enrichment.py:32-46` (todos delegam ao FairnessGuard SSOT) | Fechar como MERGED |
| W16, W19 | `audit-company-settings-routing.md` | `orchestrator/domain_mappings.py:39-41` + `orchestrator/config/domain_routing.yaml:339` | Fechar como MERGED |
| D2, D3, W11-W15 | `audit-near-duplicates-consolidation.md` (+ `audit-pipeline-tool-registry-consolidate.md` para D3 especificamente) | Apenas uma cópia em cada caso (ver §3.3) | Fechar como MERGED |
| O1-O17 | `audit-cleanup-orphans-stubs.md` | Todos os 17 arquivos não existem mais | Fechar como MERGED |
| A2 (parcial) | `audit-policy-setup-agent.md` | `domains/policy/agents/agent.py:35,44-47,74,107,143,251-286,304` (Base+FG+PII+Tenant+SPB+audit) | Fechar como MERGED (PARCIAL no scorecard mas com 6/7 critérios verificáveis) |
| A1 (parcial) | `audit-jobcreation-graph-compliance.md` | `domains/job_creation/graph.py:36,127,189,272,309,512,1188-1197` (FG+PII+AuditCallback) | Fechar como MERGED para o escopo "compliance gates"; permanece PARCIAL no scorecard pela ausência de Base ReAct (não-aplicável: é StateGraph) |
| A4 (parcial) | (parte da `audit-interview-graphs-compliance.md`) | `wsi_interview_graph.py:42-56,571,577-594,652-755` | Fechar como MERGED |

### 9b.2 Tarefas que devem permanecer em fila (PENDING/PROPOSED — código não mudou)

| Finding(s) | Slug da task | Por quê não fechar |
|---|---|---|
| T1, W8, W10 | `audit-pipeline-tool-registry-consolidate.md` (parcial) | **Corrigido 2026-04-20:** `app/tools/registry.py` é o registry **canônico** (não paralelo) wired por `initialize_tools()`, com **18 caller files** + consumo direto pelo executor/orchestrator/agentic_loop/tool_executor_service. `tool_permissions.yaml` + `tool_permissions_loader.py` **NÃO são dead code** — consumidos por `app/tools/scope_config.py` (mapeamento `scope → tools` + HITL) e por `app/shared/providers/llm_factory.py:461` (per-tenant LLM provider/fallback). Tarefa só pode ser executada se rescopada conforme F6′/F7′ em §9.4. Task #373 (premissa errada) — não executar. |
| Sub-agents (linhas 14-29 da matriz) | (sem slug — política de scoring) | Decisão de critério: política F5 (#352) define `↑✓` mas recompute pendente para snapshot 2026-05 |
| Stage 6 — refresh de docs (ARCHITECTURE.md §9.4, CANONICAL_SOURCES_SPEC.md, CLAUDE.md) | (sub-item de `audit-observability-canonical.md`) | Código foi migrado em Tarefa #343 (11 moves + 11 deleções + 41 importadores), mas a documentação de arquitetura ainda referencia paths legados |
| P14 — 146 shims sem SLA | `audit-ci-guards-shim-sla.md` | Política de remoção batch ainda pendente; 10 shims `RAILS-DEPRECATED` já marcados (F10) |

### 9b.3 Tarefas que podem ser **canceladas** (findings classificados OBSOLETO)

| Finding | Slug (se houver) | Motivo de cancelamento |
|---|---|---|
| R5 / R6 / W21 | (sem slug dedicado; itens dentro do escopo geral de "rotas") | Falsos-positivos. O plan estava errado nos números de linha. |
| Sub-claim "JobCreationGraph órfão" | (sub-item dentro de `audit-jobcreation-graph-compliance.md`) | Nunca foi órfão. A parte `compliance` da tarefa segue válida (e já MERGED conforme 9b.1). |
| Sub-claim "CompanySettings sem rota" | (sub-item dentro de `audit-company-settings-routing.md`) | Mapeamento já existia desde antes. Tarefa principal segue MERGED. |

### 9b.4 Resumo do crosswalk (atualizado 2026-04-17)

- **23 tarefas inferidas como MERGED** (poderiam ser fechadas hoje sem trabalho adicional) — +6 vs. snapshot anterior (R1, C1-C5 bloco, T3, A3, Stage 6 código, W7).
- **4 blocos de tarefas inferidas como PENDING/PROPOSED** (precisam continuar em fila): T1/W8/W10, sub-agents (política), refresh docs Stage 6, 146 shims SLA.
- **3 sub-itens canceláveis** (OBSOLETO).
- **3 follow-ups novos propostos por esta auditoria** (#348 R1, #349 C1-C5, #350 T1/T3/W8-W10) — **#348, #349, parcial de #350 (T3) já MERGED**; resta apenas escopo W8/W10/T1.

> **Nota sobre estado real das tarefas.** Esta auditoria não tem acesso direto ao status PROPOSED/PENDING/MERGED do sistema de gestão de tarefas. As atribuições acima são **inferidas a partir do estado do código** e devem ser cruzadas pelo time de planejamento com o status canônico antes de qualquer fechamento.

---

## 10. Apêndice — Reproduzibilidade

Comandos exatos usados para gerar a evidência fresca (executar a partir de `/home/runner/workspace`):

```bash
# Routes (R5, R6, W17, W21)
grep -nE "llm_config_router|webhooks\.router|agent_chat_(ws|sse)_router" \
  lia-agent-system/app/api/routes.py

# Migração @tool (T2)
grep -rn "from langchain_core.tools import tool" lia-agent-system/app/domains/

# Sweep audit shim (W4, W5, W20, C9, I1-I5)
grep -rn "from app.shared.services.audit_service" lia-agent-system/app/

# C1-C5 scoring services
for f in cv_scoring lia_score pre_qualification eligibility_verification evaluation_criteria; do
  printf '%s: ' "$f"
  grep -c "FairnessGuard\|fairness_guard\|audit_service" \
    lia-agent-system/app/domains/cv_screening/services/${f}_service.py
done

# C6, C7
grep -nE "FairnessGuard|audit_service" \
  lia-agent-system/app/domains/sourcing/services/sourcing_pipeline_service.py
grep -nE "FairnessGuard|audit_service" \
  lia-agent-system/app/domains/candidates/services/candidate_feedback_service.py

# C8
grep -n "pii_filter" lia-agent-system/app/domains/job_creation/domain.py

# R1, R2, R3, R4
grep -nE "FairnessGuard|fairness_guard|audit_service|get_current_user" \
  lia-agent-system/app/api/v1/finetuning_export.py
grep -nE "FairnessGuard|audit_service|get_current_user" \
  lia-agent-system/app/api/v1/applications.py
grep -nE "FairnessGuard|audit_service|get_current_user" \
  lia-agent-system/app/api/v1/bulk_actions.py
grep -nE "FairnessGuard|audit_service" \
  lia-agent-system/app/api/v1/stage_transition_automation.py

# R7 (chat SSE C3B)
grep -nE "pre_compliance|post_compliance" lia-agent-system/app/api/v1/agent_chat_sse.py

# T3 GlobalToolRegistry callers
grep -rn "GlobalToolRegistry.get_instance\|get_registry().register" lia-agent-system/app

# W7 — distribuição require_company=False
grep -rn "require_company\s*=\s*False" lia-agent-system/app

# Stage 6 — observability vazia
ls -la lia-agent-system/app/shared/observability/

# A1-A4
for f in domains/job_creation/graph.py \
         domains/policy/agents/agent.py \
         domains/interview_scheduling/agents/interview_graph.py \
         domains/cv_screening/agents/wsi_interview_graph.py; do
  printf '%s\n' "$f"
  grep -cE "FairnessGuard|AuditCallback|audit_service|tenant_llm_context|LangGraphReActBase|pii_masking|mask_pii|strip_pii|SystemPromptBuilder" \
    lia-agent-system/app/$f
done

# Inventário shared/
find lia-agent-system/app/shared -name '*.py' | wc -l
find lia-agent-system/app/shared -mindepth 1 -maxdepth 1 -type d | wc -l
find lia-agent-system/app/shared -maxdepth 1 -name '*.py' | wc -l

# Matriz 36 agents × 7 critérios (loop)
for a in $(find lia-agent-system/app/domains -name '*react_agent*.py' \
                                              -o -name '*_graph.py' \
                                              -o -name 'custom_agent_runtime.py' \
                                              -o -name 'agent.py' | sort); do
  base=$(grep -c "LangGraphReActBase" $a)
  aud=$(grep -c "AuditCallback\|audit_callback" $a)
  fg=$(grep -c "FairnessGuard\|fairness_guard" $a)
  pii=$(grep -c "pii_masking\|mask_pii\|strip_pii" $a)
  ten=$(grep -c "tenant_llm_context\|get_provider_for_tenant" $a)
  spb=$(grep -c "SystemPromptBuilder" $a)
  printf '%s | b=%d a=%d f=%d p=%d t=%d s=%d\n' "$a" "$base" "$aud" "$fg" "$pii" "$ten" "$spb"
done
```

---

*Auditoria original gerada em 2026-04-17 — Tarefa #347. Nenhum arquivo de código foi modificado. Verificação 1:1 com `attached_assets/CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN_1776388079132.md` (1 469 linhas). Reconciliação contra `docs/audits/AUDIT_STATUS_REPORT_2026-04.md` (Tarefa #302, 2026-04-16). 96 marcadores de status (78 findings nominais + sub-itens).*

*__Reconciliação 2026-04-17 — Tarefa #370.__ Re-verificação contra estado fresco do código no commit `dcb90de764270124f7345387e47b8d57123e65b9`. Reclassificações: R1 PENDENTE → RESOLVIDO; C1-C5 PENDENTE → RESOLVIDO (via `scoring_safeguards`); T3 PENDENTE → RESOLVIDO via deleção; A3 PARCIAL → RESOLVIDO (FG L2 BLOCK + REGENERATE); Stage 6 0% → 73% (código RESOLVIDO em Tarefa #343, resta refresh de 3 documentos). W7 unificado para **18 decoradores** (recontagem canônica). Inventário verificado: **299** `.py` em `shared/`, **29** subpastas (nova: `observability/`), **20** top-level. Nenhum arquivo de código foi modificado nesta tarefa — apenas este relatório. Top 10 reformulado em §1.2; Errata completa em §0.*
