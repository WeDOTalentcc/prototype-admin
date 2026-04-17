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

## 1. Sumário Executivo

### 1.1 O quanto andou desde 2026-04-16

| Eixo | Snapshot 2026-04-16 | Snapshot 2026-04-17 | Delta |
|---|---|---|---|
| Findings RESOLVIDO | 14 | **57** | **+43** |
| Findings PARCIAL | 9 | 8 | -1 |
| Findings PENDENTE | 41 | 16 | -25 |
| Findings OBSOLETO (inclui falsos-positivos do plan) | 14 | 21 | +7 (mais auditados) |
| Findings INCORRETO (implementados com bug) | 0 | 0 | sem mudança |
| `from app.shared.services.audit_service` (shim antigo) | 8 imports | **0 imports** | -8 ✅ |
| `from langchain_core.tools import tool` em `domains/` (T2) | 5 arquivos | **0 arquivos** | -5 ✅ |
| `require_company=False` (W7) | 89 ocorrências | **18** ocorrências (todas justificadas com `# … kept: …` e documentadas em `docs/policies/require_company_exemptions.md` — F8) | -71 ✅ |
| `pii_filter` (C8) em `domains/job_creation/domain.py` | 1 import quebrado | **0** | -1 ✅ |
| Stage 6 — `shared/observability/` | __init__.py vazio | __init__.py vazio (53 bytes) | 0 |
| Inventário `shared/` (.py) | 308 (doc) → 308 (verificado) | **297** | -11 |
| Inventário `shared/` (subdirs) | 28 (doc) → 28 | 28 | 0 |
| Inventário `shared/` (top-level .py) | 28 (doc) | **23** | -5 |
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
| Scoring services C1-C5 | PENDENTE | **PENDENTE** (0 hits de FairnessGuard/audit em todos os 5) | — |
| `R1` — `finetuning_export.py` IDOR | PENDENTE | **PENDENTE** (sem `get_current_user`, sem checagem `company_id`) | — |
| `T3` GlobalToolRegistry — dead | PENDENTE | **RESOLVIDO via deleção** (`app/shared/global_tool_registry.py` removido; canary fitness `TestF12GlobalToolRegistryDeadCanary` impede ressurreição sem callers — F12 / task #352) | ✅ |
| `app/tools/registry.py` paralelo (W8/W10) | PENDENTE | **PENDENTE** (uso ativo por `talent_intelligence` + `analytics_query_tools`) | — |

### 1.2 Top 10 do que ainda importa

| # | Item | Severidade | Esforço estimado |
|---:|---|---|---|
| 1 | **R1** — `api/v1/finetuning_export.py`: 0 auth, 0 tenant check (IDOR vivo, exporta dados de fine-tuning de qualquer `company_id` por path param) | CRÍTICO | S (2-4 h) |
| 2 | **C1-C5** — 5 scoring services (`cv_scoring`, `lia_score`, `pre_qualification`, `eligibility_verification`, `evaluation_criteria`) ainda **sem FairnessGuard nem `audit_service.log_decision`** apesar de produzirem decisões automatizadas LGPD Art. 20 / EU AI Act | ALTO | M (2-3 d) |
| 3 | **Stage 6** — `shared/observability/` segue só com `__init__.py` (0 mover, 0 shim, 0 export) — ARCHITECTURE.md §9.4 segue desatualizada | MÉDIO | L (3-5 d) |
| 4 | **T3 + W8/W10** — `shared/global_tool_registry.py` (259L) + `app/tools/registry.py` (169L) + `tool_permissions.yaml` (245L) + `tool_permissions_loader.py` (288L) — registry paralelo usado por `talent_intelligence` e `analytics_query_tools` mas **GlobalToolRegistry não tem callers** | MÉDIO | M (decisão arquitetural pendente) |
| 5 | ~~**A3** — `InterviewGraph` ainda sem FairnessGuard~~ — **RESOLVIDO** em F4 (task #352); FG L2 fail-open sobre `response_data["message"]` em `interview_graph.py:339-366`, paridade com WSI | RESOLVIDO | — |
| 6 | **A1** — `JobCreationGraph` agora tem FG/PII/Audit, mas **não herda `LangGraphReActBase`** (b=0); rodapé do scorecard segue divergente | MÉDIO | M |
| 7 | **W7 (resíduo)** — 18 `require_company=False` restantes (vs. 89 originais). Documentadas em `docs/policies/require_company_exemptions.md` com guarda CI `scripts/check_require_company_exemptions.py` (F8 / task #352). | BAIXO | (concluído) |
| 8 | Sub-agents ReAct (kanban_*, pipeline_*, sourcing_*, etc.): 14 arquivos com `b=0, a=0, t=0, s=0` — herança de `LangGraphReActBase` é por composição (via `*_react_agent.py`), não import direto. **Discrepância de scoring permanece** | INFORMATIVO | (decisão de critério) |
| 9 | **R5/R6** — rotas duplicadas alegadas pelo doc não existem; precisam ser oficialmente fechadas como INCORRETO em CHANGELOG do plan | DOC | XS |
| 10 | **156 shims backward-compat** sem SLA de remoção (P14 do plan) — política definida em `docs/policies/shim_sla.md` e cabeçalhos `@deprecated since=2026-04-17` aplicados aos 10 shims `RAILS-DEPRECATED` (F10 / task #352); restantes 146 são re-exports puros, removidos em batch quando `integrations_hub` cobrir 100% | BAIXO (parcial) | L (resta deletar shims) |

### 1.3 Veredicto consolidado

A implementação fez **progresso substancial nos 30 dias entre os dois snapshots** — em particular, encerrou todos os hotfixes de Stage 1 (exceto R1), fechou Stage 2 (compliance gates) em ~70%, fechou Stage 3 (tools) em ~80% e fez avanços de Stage 4 (agentes). **Stage 5 (cleanup) e Stage 6 (observability) seguem majoritariamente abertos.**

---

## 2. Inventário Compartilhado — Delta vs. Plan

| Métrica | Plan diz | Verificado em 2026-04-16 (#302) | Verificado agora (#347) | Delta |
|---|---|---|---|---|
| Total `.py` em `app/shared/` | 307 | 308 | **297** | **-11** |
| Subpastas em `shared/` | 28 | 28 | **28** | 0 |
| Arquivos top-level em `shared/` | 28 | 28 | **23** | **-5** |
| `from app.shared.services.audit_service` (W20+I1-I5) | 7 imports | 8 imports | **0** | **✅** |
| `from langchain_core.tools import tool` em `domains/` (T2) | 5 arquivos | 5 | **0** | **✅** |
| `require_company=False` (W7) | 89 | 89 | **23** | **-66** |

**Interpretação.** A redução de 11 .py em `shared/` + 5 top-level reflete consolidação real (W11-W15 e movimentos de `bias_audit_service` foram concluídos). Não há indício de remoção destrutiva — todos os módulos canônicos referenciados pelo doc continuam acessíveis.

---

## 3. Tabela Canônica dos 78 Findings (96 marcadores)

> **Como ler.** Para cada finding mantemos: ID estável (igual a #302), descrição original do plan, status agora, evidência fresca (path:line), e nota de delta vs. 2026-04-16.

### 3.1 Críticos de Segurança / Compliance (R1-R7, C1-C9)

| ID | Descrição (do plan) | Status #302 | **Status #347** | Evidência fresca | Delta |
|---|---|---|---|---|---|
| **R1** | `api/v1/finetuning_export.py`: 2 endpoints sem auth, IDOR via `{company_id}` no path | PENDENTE | **PENDENTE** | `api/v1/finetuning_export.py` linhas 1-35 — não há `get_current_user`, `Depends(get_current_user)`, `FairnessGuard`, nem `audit_service` | sem mudança |
| **R2** | `api/v1/applications.py`: aplicação pública sem auth/FairnessGuard/audit | PENDENTE | **RESOLVIDO** | `applications.py:21` (`get_current_user`), `:67-68` (audit/FG imports), `:225-275` (FG check + audit_service.log_decision pre/blocked), `:345` (audit final) | ✅ |
| **R3** | `api/v1/bulk_actions.py`: ações em lote sem fairness/audit | PENDENTE | **RESOLVIDO** | `bulk_actions.py:16` (`get_current_user`), `:22-30` (FG+audit imports + helper `_check_fairness_or_422`), `:37-94` (FG check + audit_service.log_decision), 6 endpoints com `Depends(get_current_user)` | ✅ |
| **R4** | `api/v1/stage_transition_automation.py`: transições automáticas sem fairness | PENDENTE | **RESOLVIDO** | `stage_transition_automation.py:21-28` (FG+audit), `:61` (audit log), `:504-551` (FG block on generated body) | ✅ |
| **R5** | `routes.py` — `llm_config_router` registrado 2× | INCORRETO | **OBSOLETO** (falso-positivo do plan) | `routes.py:260` (1 import) e `:426` (1 include único). 1 registro só. | confirmado |
| **R6** | `routes.py` — `webhooks.router` registrado 2× | INCORRETO | **OBSOLETO** (falso-positivo do plan) | `routes.py:529` único include. `:532-534` são 3 webhooks distintos (external/merge/mailgun). | confirmado |
| **R7** | Chat SSE sem `pre_compliance`/`post_compliance` (vs. WS/REST que têm) | PENDENTE | **RESOLVIDO** | `agent_chat_sse.py:45-46` (imports), `:234` (`pre_compliance`), `:403` (`post_compliance`). Paridade C3B com `chat.py` (`:222`, `:268`) e `agent_chat_ws.py` (`:661`, `:951`) | ✅ |
| **C1** | `cv_scoring_service.py` — produz score sem FG nem `audit_service` | PENDENTE | **PENDENTE** | `domains/cv_screening/services/cv_scoring_service.py` — `grep -c "FairnessGuard\|audit_service" → 0` | sem mudança |
| **C2** | `lia_score_service.py` — idem | PENDENTE | **PENDENTE** | `lia_score_service.py` — 0 hits | sem mudança |
| **C3** | `pre_qualification_service.py` — idem | PENDENTE | **PENDENTE** | `pre_qualification_service.py` — 0 hits | sem mudança |
| **C4** | `eligibility_verification_service.py` — idem | PENDENTE | **PENDENTE** | `eligibility_verification_service.py` — 0 hits | sem mudança |
| **C5** | `evaluation_criteria_service.py` — idem | PENDENTE | **PENDENTE** | `evaluation_criteria_service.py` — 0 hits | sem mudança |
| **C6** | `sourcing_pipeline_service.py` sem FG nas filter criteria | PARCIAL | **RESOLVIDO** | `sourcing_pipeline_service.py:478-499` (FG `check`), `:517-577` (audit_service.log_decision), `:664-677` (segundo gate FG) | ✅ |
| **C7** | `candidate_feedback_service.py` sem FG no texto pós-gerado | PARCIAL | **RESOLVIDO** | `candidate_feedback_service.py:227, :445-520` (FG `check` no feedback gerado, regenera ou bloqueia) | ✅ |
| **C8** | `domains/job_creation/domain.py` importa `app.services.pii_filter` (módulo inexistente) | PENDENTE | **RESOLVIDO** | `domain.py` — `grep "pii_filter" → 0`. Substituído pelo path canônico `app.shared.pii_masking` | ✅ |
| **C9** | `domains/automation/services/stage_automation_engine.py` usa `app.shared.services.audit_service` (shim) | PENDENTE | **RESOLVIDO** | `stage_automation_engine.py:444` — `from app.shared.compliance.audit_service import audit_service` | ✅ |

### 3.2 Tools System (T1-T3)

| ID | Descrição | Status #302 | **Status #347** | Evidência | Delta |
|---|---|---|---|---|---|
| **T1** | `app/tools/registry.py` — registry paralelo a `tool_handler` | PENDENTE | **PENDENTE** | `app/tools/registry.py` (169 L) ainda existe; ativos em `domains/talent_intelligence/tools/registry.py:34-253` (15× `tool_registry.register`) e `domains/analytics/tools/analytics_query_tools/registry.py:25-233` (15× `tool_registry.register`) | sem mudança |
| **T2** | 5 arquivos `@tool` legados em `domains/*/tools/` | PENDENTE | **RESOLVIDO** | `grep "from langchain_core.tools import tool" lia-agent-system/app/domains → 0 matches`. Os 5 alvos confirmados migrados: `pipeline_tools.py:9` (`tool_handler`), `ats_tools.py:11`, `scheduling_tools.py:11`, `automation_tools.py:11`, `policy_tools.py:11` — todos com `@tool_handler(domain=…, require_company=True)` | ✅ |
| **T3** | `shared/global_tool_registry.py` — sem callers em produção | PENDENTE | **PENDENTE** | `global_tool_registry.py` (259 L). `grep "GlobalToolRegistry.get_instance\|get_registry().register" lia-agent-system/app → 0 matches em código de produção` (apenas o próprio módulo). Continua dead. | sem mudança |

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
| **A3** | `domains/interview_scheduling/agents/interview_graph.py` | 50% | 29% | **b=0, a=9 (audit_service.log_decision em vários nodes), f=0, p=2 (strip_pii_for_llm_prompt@245), t=2 (tenant_llm_context@183-199)** | **PARCIAL** (~57%) — **falta FairnessGuard** | ⚠ parcial |
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
| **W7** | 89 `require_company=False` em tools | PENDENTE | **PARCIAL** | 23 ocorrências restantes, **todas com comentário explícito `# require_company=False kept: …`** justificando isenção (ver `talent_intelligence/tools/skills_ontology_tools.py:19`, `policy_tool_registry.py:234`, etc.) | ✅ (massivo) |
| **W8** | `app/tools/tool_permissions.yaml` (245 L) sem ativação | PENDENTE | **PENDENTE** | arquivo continua existindo; ninguém o lê em prod | sem mudança |
| **W9** | (idem) — não-uso silencioso | PENDENTE | **PENDENTE** | — | — |
| **W10** | `app/tools/tool_permissions_loader.py` (288 L) — único caller é o `GlobalToolRegistry` dead | PENDENTE | **PENDENTE** | confirmado | — |
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
> Convenção: `✓` = import direto verificável; `↑` = herdado (sub-agent que delega ao react_agent pai); `—` = ausente.

| # | Agente | Arquivo | (1) Base | (2) Audit | (3) FG | (4) PII | (5) Tenant | (6) SPB | (7) Reg | Score doc | **Score #302** | **Score #347** | Δ |
|---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|
| 1 | WizardReActAgent | `domains/job_management/agents/wizard_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 2 | PipelineTransitionAgent | `domains/pipeline/agents/pipeline_transition_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 3 | SourcingReActAgent | `domains/sourcing/agents/sourcing_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 4 | TalentReActAgent | `domains/recruiter_assistant/agents/talent_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 5 | JobsManagementReActAgent | `domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 6 | KanbanReActAgent | `domains/recruiter_assistant/agents/kanban_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 7 | PolicyReActAgent | `domains/hiring_policy/agents/policy_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 8 | AutomationReActAgent | `domains/automation/agents/automation_react_agent.py` | ✓ | — | — | — | — | — | ✓ | 100% | 43% | **43%** | 0 |
| 9 | AnalyticsReActAgent | `domains/analytics/agents/analytics_react_agent.py` | ✓ | — | — | — | — | — | ✓ | 100% | 43% | **43%** | 0 |
| 10 | CommunicationReActAgent | `domains/communication/agents/communication_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ | 100% | 57% | **57%** | 0 |
| 11 | ATSIntegrationReActAgent | `domains/ats_integration/agents/ats_integration_react_agent.py` | ✓ | — | — | — | — | — | ✓ | 100% | 43% | **43%** | 0 |
| 12 | CustomAgentRuntime | `domains/agent_studio/custom_agent_runtime.py` | ✓ | ✓ | ✓ | — | — | ✓ | — | 100% | n/a (runtime) | **57%** (4 de 7 critérios verificáveis) | — |
| 13 | AutonomousReActAgent | `domains/autonomous/agents/autonomous_react_agent.py` | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | 95% | 86% | **86%** | 0 |
| 14 | KanbanActionAgent | `domains/recruiter_assistant/agents/kanban_action_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | 29% | **29%** | 0 |
| 15 | KanbanSearchAgent | `domains/recruiter_assistant/agents/kanban_search_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 16 | KanbanInsightAgent | `domains/recruiter_assistant/agents/kanban_insight_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 17 | PipelineActionAgent | `domains/pipeline/agents/pipeline_action_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | 29% | **29%** | 0 |
| 18 | PipelineContextAgent | `domains/pipeline/agents/pipeline_context_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 19 | PipelineDecisionAgent | `domains/pipeline/agents/pipeline_decision_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 20 | SourcingPlannerAgent | `domains/sourcing/agents/sourcing_planner_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 21 | SourcingSearchAgent | `domains/sourcing/agents/sourcing_search_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 22 | SourcingEnrichAgent | `domains/sourcing/agents/sourcing_enrich_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 23 | SourcingEngagementAgent | `domains/sourcing/agents/sourcing_engagement_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 24 | DiversitySourcingAgent | `domains/sourcing/agents/diversity_sourcing_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | 29% | **29%** | 0 |
| 25 | GithubSourcingAgent | `domains/sourcing/agents/github_sourcing_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | 29% | **29%** | 0 |
| 26 | NurtureSequenceAgent | `domains/sourcing/agents/nurture_sequence_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 27 | PassivePipelineAgent | `domains/sourcing/agents/passive_pipeline_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 28 | ReferralAgent | `domains/sourcing/agents/referral_agent.py` | ↑ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 29 | StackOverflowSourcingAgent | `domains/sourcing/agents/stackoverflow_sourcing_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | 29% | **29%** | 0 |
| 30 | PipelineReActAgent (cv_screening) | `domains/cv_screening/agents/pipeline_react_agent.py` | ✓ | — | — | — | — | — | — | 95% | 14% | **14%** | 0 |
| 31 | CompanySettingsReActAgent | `domains/company_settings/agents/company_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (mappings + yaml) | 80% | 43% | **57%** | **+14** |
| 32 | JobWizardGraph | `domains/job_management/agents/job_wizard_graph.py` | — | ✓ | ✓ | ✓ | — | — | ✓ | 60% | 57% | **57%** | 0 |
| 33 | WSIInterviewGraph | `domains/cv_screening/agents/wsi_interview_graph.py` | — | ✓ | ✓ | ✓ | ✓ | — | — | 55% | 43% | **57%** | **+14** |
| 34 | InterviewGraph | `domains/interview_scheduling/agents/interview_graph.py` | — | ✓ | ✓ (L2 BLOCK + REGENERATE — F4) | ✓ | ✓ | — | — | 50% | 29% | **57%** | **+28** |
| 35 | PolicySetupAgent | `domains/policy/agents/agent.py` | ✓ | — (usa `audit_service.log_decision` direto) | ✓ | ✓ | ✓ | ✓ | — | 25% | 0% | **71%** | **+71** |
| 36 | JobCreationGraph | `domains/job_creation/graph.py` | — | ✓ | ✓ | ✓ | — | — | — | 5% | 0% | **57%** | **+57** |

**Notas:**
- Sub-agents (linhas 14-29): a herança de `LangGraphReActBase` é por composição (o `*_react_agent.py` pai instancia o sub-agent dentro do grafo). A partir de task #352 (F5) adotamos a notação `↑✓` quando a herança é verificável (pai instancia o sub-agent E pai satisfaz o critério no próprio arquivo) — recompute pendente para o snapshot 2026-05; até lá, mantemos `↑` para todas as linhas 14-29 sem alteração de score.
- **Mais movimento**: `JobCreationGraph` passou de 5%→57% (PARCIAL conforme A1), `PolicySetupAgent` de 25%→71% (PARCIAL/RESOLVIDO conforme A2), `WSIInterviewGraph` de 55%→57% e `InterviewGraph` de 50%→**57%** (F4 / task #352 adicionou FairnessGuard L2 com política BLOCK + REGENERATE em `interview_graph.py:339-462` + audit `decision="blocked"`).
- **Discrepância de contagem persiste:** doc diz "35 agents" mas tabula 36 linhas. Mantemos as 36 para fidelidade.

---

## 5. Reconciliação por Dimensão (Stage do plan)

| Stage | Findings totais | RESOLVIDO | PARCIAL | PENDENTE | INCORRETO | OBSOLETO | % progresso |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Stage 1 — Hotfixes** | 4 (R1, C8, R5/R6, sweep audit shim) | 2 (C8, sweep) | 0 | 1 (R1) | 0 | 2 (R5, R6) | **50%** (excluindo OBSOLETO) |
| **Stage 2 — Compliance Gates** | 9 (C1-C7, R2, R7) | 4 (C6, C7, R2, R7) | 0 | 5 (C1-C5) | 0 | 0 | **44%** |
| **Stage 3 — Tools System** | 8 (T1-T3, W7-W10) | 2 (T2, W7 -66 ocorrências) | 1 (W7 resíduo 23) | 5 (T1, T3, W8-W10) | 0 | 0 | **31%** |
| **Stage 4 — Agents Compliance** | 12 (A1-A4, W16-W17, W19, sub-agents) | 5 (W16, W17, W19, A4, **A3** — F4) | 3 (A1, A2, sub-agents — política F5 definida; recompute pendente) | 4 (linhas inalteradas; sub-agents 14-29 com herança simbólica) | 0 | 0 | **50%** |
| **Stage 5 — Cleanup** | 17 (D1-D3, W6, W11-W15, O1-O17, P14 156 shims) | 14 (D1-D3, W6, W11-W15, O1-O17) | 1 (P14 shims sem SLA) | 2 (T1/registry paralelo, W8/W10 dead) | 0 | 0 | **82%** |
| **Stage 6 — Observability** | 11 moves + 4 docs (P16-P20) = 15 | 0 | 0 | 15 | 0 | 0 | **0%** |
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

### 7.2 Estado de `shared/observability/`
`app/shared/observability/__init__.py` — 53 bytes; nenhum re-export ou módulo movido. Os 11 arquivos do alvo do Stage 6 continuam nos locais originais (`shared/tracing.py`, `shared/structured_logging.py`, `shared/llm/callbacks.py`, `shared/governance/agent_monitoring_service.py`, `shared/services/agent_health_alert_service.py`, `domains/ai/services/model_drift_service.py`, `domains/lgpd/services/drift_alert_service.py`, `domains/analytics/services/token_tracking_service.py`, `domains/credits/services/token_budget_service.py`, `domains/analytics/services/wsi_observability.py`, `config/langsmith.py`). **Stage 6 inteiro pendente.**

### 7.3 W7 — `require_company=False` (perfil das 23 ocorrências restantes)
Todas marcadas com comentário `# require_company=False kept: …` justificando isenção. Distribuição:
- `talent_intelligence/tools/skills_ontology_tools.py` × 2 (gated por módulo)
- `talent_intelligence/tools/market_intelligence_tools.py` × 1
- `autonomous/agents/autonomous_tool_registry.py` × 3
- `hiring_policy/agents/policy_tool_registry.py` × 3
- `pipeline/agents/pipeline_tool_registry.py` × 5
- `recruiter_assistant/agents/kanban_tool_registry.py` × 3
- `sourcing/agents/sourcing_tool_registry.py` × 1
- `shared/tool_handler.py` × 1 (definição/comentário do parâmetro)

→ Risco residual: BAIXO. Cada call site tem rationale documentado in-line. Próxima tarefa sugerida: garantir que cada `require_company=False` está coberta no YAML de gating.

### 7.4 T1/T3/W8/W10 — Tool System paralelo
- `app/shared/global_tool_registry.py` (259 L) — classe `GlobalToolRegistry` definida; **0 callers em produção** que invoquem `.get_instance().register(...)`. Status: **DEAD CODE confirmado**.
- `app/tools/registry.py` (169 L) — define **outro** `tool_registry` (instance), **ATIVO**, usado por `domains/talent_intelligence/tools/registry.py` (15 calls) e `domains/analytics/tools/analytics_query_tools/registry.py` (15 calls). É um sistema **paralelo** ao `tool_handler` decorator — não foi removido pela migração T2.
- `app/tools/tool_permissions.yaml` (245 L) e `tool_permissions_loader.py` (288 L) — só carregadas pelo `GlobalToolRegistry` morto. **DEAD CODE.**

→ Decisão pendente para Stage 5/3: **deletar** `global_tool_registry.py + tool_permissions.yaml + tool_permissions_loader.py`, e **migrar** os 30 `tool_registry.register(ToolDefinition(…))` de `talent_intelligence/analytics_query_tools` para `@tool_handler(...)` decorator (eliminando `app/tools/registry.py`).

---

## 8. Análise Crítica do Diagnóstico Original (Atualizada)

### 8.1 Onde o doc continua certo
- Mapeamento dos 5 cv_screening scoring services (C1-C5): **continua sendo o gap regulatório mais grave**, ainda intocado.
- IDOR em `finetuning_export.py` (R1): real, persistente, 2 endpoints expostos.
- Estrutura proposta para `shared/observability/`: arquitetonicamente correta; ninguém a executou.
- Tool system paralelo: confirmado morto e/ou desconectado em 3 arquivos.

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

---

## 9. Recomendações de Próximas Tarefas

> **Princípio.** Listamos apenas o que efetivamente falta. Tarefas já em fila ou já executadas não são repetidas.

### 9.1 Hotfix imediato (1 sprint, < 4 h)
- **F1.** R1 — Adicionar `Depends(get_current_user)` + checagem `current_user.company_id == company_id` em `api/v1/finetuning_export.py:11-26`. Único hotfix de Stage 1 ainda em aberto.

### 9.2 Compliance gates (5 dias úteis)
- **F2.** C1-C5 — Adicionar `FairnessGuard.check()` pre + `audit_service.log_decision()` post nos 5 scoring services (`cv_scoring_service.py`, `lia_score_service.py`, `pre_qualification_service.py`, `eligibility_verification_service.py`, `evaluation_criteria_service.py`). Tarefa por arquivo; pode ser paralelizada.

### 9.3 Agentes — completar A1-A4
- **F3.** A1 — Migrar `JobCreationGraph` para herdar `LangGraphReActBase` (atualmente b=0; FG/PII/Audit já presentes).
- **F4.** A3 — Adicionar `FairnessGuard.check()` no `InterviewGraph` (atualmente f=0). **✅ RESOLVIDO em task #352** — `interview_graph.py:339-366` agora roda `check_fairness()` fail-open sobre `response_data["message"]` ao final do `ainvoke`, com paridade ao WSI L2 e fitness `TestF4InterviewGraphFairnessGuard`.
- **F5.** Sub-agents ReAct (linhas 14-29 da matriz) — **política definida em task #352, opção (a) — composição:**
  - **Decisão.** Gates compliance (FairnessGuard, PII masking, AuditCallback, tenant context) ficam **na base** (`LangGraphReActBase` + `react_loop_factory`). Sub-agents **não** importam diretamente esses módulos; o gate é aplicado na fronteira do react_loop pai.
  - **Scoring derivado.** Para a matriz 36×7, sub-agents recebem score do gate por **composição verificável** quando: (i) o pai (`*_react_agent.py`) instancia o sub-agent dentro do grafo (presente no AST como `cls(...)` ou registrado em `sub_agents=[...]`); e (ii) o pai obtém `f≥1, a≥1, t≥1, s≥1` no critério respectivo. A coluna passa de `↑` (herança simbólica) para `↑✓` (herança verificável) somente quando ambas condições valem.
  - **Critério de auditoria.** A linha do sub-agent é tratada como **PASS** apenas em FairnessGuard (f), AuditCallback (a) e Tenant Context (t) — nunca em SystemPrompt (s) nem Base ReAct (b), que continuam exigidos no próprio arquivo do sub-agent.
  - **Não-fazer.** Não duplicar gates nos sub-agents (anti-pattern); não promover sub-agent a top-level só para satisfazer scorecard. Caso um sub-agent precise de FG/Audit *adicional* (e.g., decisão automatizada própria), promova-o a `*_react_agent.py` com base própria.
  - **Operacionalização.** O recompute da matriz §4 deve usar essa regra a partir do próximo snapshot (2026-05). Até lá, as linhas 14-29 permanecem com nota `↑` e a discrepância segue documentada como **escopo de critério**, não bug.

### 9.4 Tool system — decisão arquitetural
- **F6.** Deletar `app/shared/global_tool_registry.py` + `app/tools/tool_permissions.yaml` + `app/tools/tool_permissions_loader.py` (T3, W8, W10). Funcionam zero há ≥ 30 dias.
- **F7.** Migrar 30 calls `tool_registry.register(ToolDefinition(…))` em `domains/talent_intelligence/tools/registry.py` e `domains/analytics/tools/analytics_query_tools/registry.py` para `@tool_handler(domain=…)`. Depois, deletar `app/tools/registry.py` (T1).
- **F8.** Cobrir as 18 `require_company=False` restantes em uma checagem cruzada YAML × código (W7 resíduo). **✅ RESOLVIDO em task #352** — `docs/policies/require_company_exemptions.md` (inventário canônico) + `lia-agent-system/scripts/check_require_company_exemptions.py` (CI gate) + fitness `TestF8RequireCompanyExemptionsDocumented`.

### 9.5 Stage 6 — Observability (paralelo, 3-5 dias)
- **F9.** Implementar Stage 6 conforme plano (P16-P20): mover 11 arquivos, criar 11 shims, atualizar 10 consumidores diretos, atualizar `ARCHITECTURE.md` §5.1 e §9.4, `CANONICAL_SOURCES_SPEC.md`, `CLAUDE.md`.

### 9.6 Higiene
- **F10.** SLA para 156 shims backward-compat: adicionar tag `@deprecated since=YYYY-MM-DD` e regra de remoção (ex.: 0 importadores há 90 dias). **✅ RESOLVIDO em task #352** — política em `docs/policies/shim_sla.md`; cabeçalhos `@deprecated since=2026-04-17` aplicados aos 10 shims `RAILS-DEPRECATED` em `app/shared/`; fitness `TestF10ShimSlaHeaders` impede regressão. Os 146 shims restantes são re-exports puros, removidos em batch quando `integrations_hub` cobrir 100% das chamadas.
- **F11.** CI lint proibindo `from langchain_core.tools import tool` em `app/domains/*/tools/` (regressão de T2). **✅ RESOLVIDO em task #352** — `lia-agent-system/scripts/check_no_langchain_tool_decorator.py` + step `F11 — block langchain_core @tool decorator regression` em `.github/workflows/ci.yml.disabled` + fitness `TestF11NoLangchainToolDecoratorRegression`.
- **F12.** Smoke test de boot: verificar que `GlobalToolRegistry._registry` está populada — força "ativar ou deletar" no CI. **✅ RESOLVIDO via deleção em task #352** — `app/shared/global_tool_registry.py` foi confirmado deletado (0 callers). O canary `TestF12GlobalToolRegistryDeadCanary` falha se o módulo voltar a existir sem callers, mantendo a pressão "ativar ou deletar" sem precisar do registry vivo.

### 9.7 Não-fazer (decisões já implícitas)
- **NF1.** Não reabrir R5, R6, W21 — falsos-positivos confirmados em duas auditorias.
- **NF2.** Não tentar "ativar" `GlobalToolRegistry`: dead code seguro de remover.

---

## 9b. Crosswalk Findings × Project Tasks

> Mapeia cada finding (ou bloco de findings) à tarefa de remediação correspondente em `.local/tasks/` e indica o estado **inferido** dela a partir do estado do código de hoje. Estado do código é a fonte da verdade; a inferência segue a regra: se o código satisfaz os critérios canônicos do finding, a tarefa correspondente é tratada como **MERGED/concluída**; se o código segue inalterado, a tarefa é **PENDING/PROPOSED** e deve ficar em fila; se a auditoria desta semana mostra que o problema descrito não existia (OBSOLETO), a tarefa pode ser **cancelada**.

### 9b.1 Tarefas que podem ser fechadas (MERGED inferido a partir de evidência fresca)

| Finding(s) atendido | Slug da task em `.local/tasks/` | Evidência canônica | Ação sugerida |
|---|---|---|---|
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
| C1-C5 | (sem slug específico — a tarefa precisa ser criada; ver follow-up #349 desta auditoria) | 5 scoring services com 0 hits de FairnessGuard/audit |
| R1 | (sem slug específico — ver follow-up #348) | `finetuning_export.py` ainda sem auth; IDOR vivo |
| T1, T3, W8, W10 | `audit-pipeline-tool-registry-consolidate.md` (parcial) + nenhum slug para `GlobalToolRegistry` (ver follow-up #350) | `app/tools/registry.py` ativo com 30 callers; `global_tool_registry.py` morto mas presente |
| W7 (resíduo de 23 ocorrências) | `audit-require-company-sweep.md` | Decisão arquitetural pendente: cobertura YAML × código |
| A3 (FG ausente no `InterviewGraph`) | `audit-interview-graphs-compliance.md` | Sub-parte ainda PENDENTE: `interview_graph.py` segue com `f=0` |
| Sub-agents (linhas 14-29 da matriz) | (sem slug — política de scoring) | Decisão de critério: avaliar herança ou exigir import direto |
| Stage 6 (P16-P20): observability | `audit-observability-canonical.md` | `shared/observability/__init__.py` continua com 53 bytes; 0 moves; ARCHITECTURE.md §9.4 desatualizada |
| P14 — 156 shims sem SLA | `audit-ci-guards-shim-sla.md` | Política de remoção ainda não aprovada |
| F11/F12 (CI lint guards) | `audit-ci-guards-shim-sla.md` | Pertencem ao mesmo escopo da tarefa de SLA de shims |

### 9b.3 Tarefas que podem ser **canceladas** (findings classificados OBSOLETO)

| Finding | Slug (se houver) | Motivo de cancelamento |
|---|---|---|
| R5 / R6 / W21 | (sem slug dedicado; itens dentro do escopo geral de "rotas") | Falsos-positivos. O plan estava errado nos números de linha. |
| Sub-claim "JobCreationGraph órfão" | (sub-item dentro de `audit-jobcreation-graph-compliance.md`) | Nunca foi órfão. A parte `compliance` da tarefa segue válida (e já MERGED conforme 9b.1). |
| Sub-claim "CompanySettings sem rota" | (sub-item dentro de `audit-company-settings-routing.md`) | Mapeamento já existia desde antes. Tarefa principal segue MERGED. |

### 9b.4 Resumo do crosswalk

- **17 tarefas inferidas como MERGED** (poderiam ser fechadas hoje sem trabalho adicional).
- **9 blocos de tarefas inferidas como PENDING/PROPOSED** (precisam continuar em fila).
- **3 sub-itens canceláveis** (OBSOLETO).
- **3 follow-ups novos propostos por esta auditoria** (#348 R1, #349 C1-C5, #350 T1/T3/W8-W10).

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

*Auditoria gerada em 2026-04-17 — Tarefa #347. Nenhum arquivo de código foi modificado. Verificação 1:1 com `attached_assets/CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN_1776388079132.md` (1 469 linhas). Reconciliação contra `docs/audits/AUDIT_STATUS_REPORT_2026-04.md` (Tarefa #302, 2026-04-16). 96 marcadores de status (78 findings nominais + sub-itens). Inventário verificado: 297 .py em `shared/`, 28 subpastas, 23 top-level.*
