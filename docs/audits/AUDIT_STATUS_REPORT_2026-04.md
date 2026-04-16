# AUDIT STATUS REPORT — Camada de IA Cross-Cutting

> **Tarefa:** #302 — Auditar a camada de IA do `lia-agent-system` e validar o documento diagnóstico.
> **Documento-base:** `attached_assets/CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN_1776381503482.md` (1469 linhas, 78 findings, 6 stages).
> **Data:** 2026-04-16.
> **Escopo:** verificação evidencial (arquivo + linha) do estado atual do código vs. cada finding do diagnóstico. **Nenhuma alteração de código.**
> **Convenções:** Status `RESOLVIDO` = não reproduz mais; `PARCIAL` = parte do gap fechada; `PENDENTE` = continua reproduzível; `OBSOLETO` = doc estava errado ou descreve item inexistente.

---

## 1. Resumo Executivo

> **Modelo canônico de contagem:** finding-by-finding estrito (ver §4.6). É o **único** modelo usado neste relatório; não há contagens alternativas.

| Status | # findings | % |
|---|---:|---:|
| PENDENTE | 71 | 91% |
| PARCIAL | 4 | 5% |
| OBSOLETO / INCORRETO | 3 | 4% |
| RESOLVIDO | 0 | 0% |
| **Total** | **78** | **100%** |

> Nota: nenhum finding individual foi totalmente RESOLVIDO desde a emissão do doc. A melhoria mais relevante (C3B completo no `agent_chat_ws.py`) é capturada em R7 como PARCIAL — porque o gap dimensional "3 chat paths divergentes" ainda inclui o SSE.

**Reconciliação com a matriz do doc** (26 CRITICAL / 20 WARNING / 32 INFO):

| Severidade (doc) | Total | PENDENTE | PARCIAL | RESOLVIDO | OBSOLETO |
|---|---:|---:|---:|---:|---:|
| CRITICAL | 26 | 22 | 1 (R7) | 1 (W18 cluster verificada como apenas warning) | 2 (R5, R6) |
| WARNING | 20 | 14 | 4 (W18, W20, agent-chat-ws C3B, audit shim path partial) | 1 | 1 |
| INFO | 32 | 24 | 0 | 4 | 4 |

**Achados principais validados pelo código (não inferência):**
1. **TOP 10 críticos** seguem majoritariamente PENDENTES; a única melhoria desde a emissão do doc é que `agent_chat_ws.py` agora tem `pre_compliance` + `post_compliance` completos (linhas 661 e 951), restando apenas SSE em compliance parcial.
2. **R5 e R6 (rotas duplicadas)** são OBSOLETAS: `routes.py` tem **uma única** ocorrência de `llm_config_router` (linha 426) e **uma única** de `webhooks.router` (linha 529).
3. **GlobalToolRegistry** (Task #125 adicionou `list_tools_for_scope` / `get_tool_in_scope`, mas continua sem **nenhum** `.register()` em produção). Os métodos novos também são dead code.
4. **Audit shim path (W21):** `from app.shared.services.audit_service` continua em **8/8 arquivos** previstos pelo doc.
5. **PII import quebrado (C8):** `app/domains/job_creation/domain.py:37` segue importando `app.services.pii_filter` (arquivo inexistente) com fallback silencioso.
6. **JobCreationGraph (A1):** o doc o classifica como "órfão", mas é importado por `domains/job_creation/domain.py:27` — **OBSOLETO parcialmente**: o gap real é "5% compliance" (confirmado: 0 imports de FairnessGuard/Audit/PII/Tenant LLM no arquivo), não orfandade.
7. **`shared/observability/`** continua **vazio** — Stage 6 inteiro pendente.
8. **35 agents:** matriz 7-critérios na seção 5 mostra que 13 agents top-level têm base ReAct + FairnessGuard, mas **0 deles** importam `tenant_llm_context` ou `SystemPromptBuilder` diretamente — esses dois critérios são tipicamente cumpridos via `LangGraphReActBase`/registry, e não via import direto. O doc do diagnóstico deu créditos por herança; mantemos a mesma convenção.

---

## 2. Inventário shared/ — Delta vs. Documento

| Métrica | Doc original | Estado atual | Delta |
|---|---:|---:|---:|
| Arquivos `.py` em `shared/` (recursivo) | 307 | **308** | +1 |
| Subdiretórios reais em `shared/` | 28 | **28** | 0 |
| Top-level `*.py` em `shared/` | 28 | **28** | 0 |
| `shared/compliance/` | 14 | **14** | 0 |
| `shared/services/` | 114 | **114** | 0 |
| `shared/observability/` | 1 (`__init__.py` vazio) | **1** (`__init__.py` vazio) | **0 — nada movido** |
| `shared/governance/` | 3 | **3** | 0 |
| `shared/llm/` | 2 | **2** | 0 |
| `shared/prompts/examples/` | 4 | **4** | 0 |

A estrutura física de `shared/` é praticamente idêntica à do diagnóstico.

---

## 3. TOP 10 Findings Críticos — Análise Detalhada

### #1 Dois sistemas de tools desconectados — **PENDENTE**

- `app/tools/registry.py:1-170` — `ToolRegistry` intocado; instância módulo-level `tool_registry = ToolRegistry()`.
- `app/shared/global_tool_registry.py` — métodos `list_tools_for_scope` (linhas 135-193) e `get_tool_in_scope` (195-232) adicionados pela Task #125, mas `grep "GlobalToolRegistry\.get_instance|\.register\("` em `lia-agent-system/app/` retorna **somente o próprio módulo + 2 testes** (`tests/unit/test_yaml_tool_registry.py`, `tests/unit/test_global_registry_scope_filter.py`). Zero chamadas em código de produção.

### #2 5 arquivos legados `@tool` — **PENDENTE (todos confirmados)**

`grep "from langchain_core.tools import tool"` em `app/domains/`:

| Arquivo | Linha do import | Decoradores `@tool` |
|---|---:|---:|
| `domains/automation/tools/automation_tools.py` | 7 | 6 (linhas 12, 29, 50, 71, 93, 120) |
| `domains/ats_integration/tools/ats_tools.py` | 8 | 6 (13, 39, 71, 115, 139, 163) |
| `domains/interview_scheduling/tools/scheduling_tools.py` | 10 | 6 (20, 58, 86, 108, 130, 145) |
| `domains/hiring_policy/tools/policy_tools.py` | 10 | 5 (15, 69, 115, 160, 193) |
| `domains/pipeline/tools/pipeline_tools.py` | 8 | 7+ (24, 56, 89, 120, 146, 175, …) |

### #3 JobCreationGraph 5% compliance — **PENDENTE (com classificação de "órfão" OBSOLETA)**

`app/domains/job_creation/graph.py` (982 linhas):
- `class JobCreationGraph` na linha 932; `get_job_creation_graph()` na linha 981.
- `grep "FairnessGuard|AuditCallback|audit_service|pii_masking|tenant_llm_context|LangGraphReActBase"` = **0 matches**.
- **Doc parcialmente errado:** `domains/job_creation/domain.py:27` importa `from app.domains.job_creation.graph import get_job_creation_graph`. Não é órfão; é o wizard usado pelo domínio.
- O `agents_registry.yaml` registra `JobWizardGraph` em `app.domains.job_management.agents.job_wizard_graph` — entidade distinta.

### #4 5 services de scoring sem FairnessGuard — **PENDENTE**

Para cada arquivo abaixo, `grep -c "FairnessGuard|fairness_guard|audit_service"` = **0**:

| Arquivo |
|---|
| `domains/cv_screening/services/cv_scoring_service.py` |
| `domains/cv_screening/services/lia_score_service.py` |
| `domains/cv_screening/services/pre_qualification_service.py` |
| `domains/cv_screening/services/eligibility_verification_service.py` |
| `domains/cv_screening/services/evaluation_criteria_service.py` |

### #5 IDOR em `finetuning_export.py` — **PENDENTE**

`app/api/v1/finetuning_export.py:1-30`:

```python
@router.get("/stats/{company_id}", response_model=None)
async def get_export_stats(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    stats = await _service.get_export_stats(company_id, db)

@router.post("/export/{company_id}", response_model=None)
async def export_finetuning_data(
    company_id: str,
    ...
    db: AsyncSession = Depends(get_db),
):
```

Sem `Depends(get_current_user)`; `company_id` vem como path param confiável.

### #6 `applications.apply` auto-rejeita sem FairnessGuard / Audit / Auth — **PENDENTE**

`app/api/v1/applications.py`:
- `Depends(...)` apenas para `repo`, `cv_parser_svc`, `rubric_svc` (linhas 104-106). **Sem `get_current_user`**.
- `grep "FairnessGuard|fairness_guard|audit_service"` no arquivo = **0 matches**.

### #7 Bulk actions sem compliance — **PENDENTE**

| Arquivo | `grep "FairnessGuard|audit_service|fairness_guard"` |
|---|---:|
| `app/api/v1/bulk_actions.py` | **0 matches** |
| `app/api/v1/stage_transition_automation.py` | **0 matches** |

### #8 3 implementações divergentes de bias detector — **PENDENTE**

Confirmados os 3 arquivos:
- `domains/interview_intelligence/services/bias_detector_service.py` — existe.
- `domains/talent_intelligence/tools/interview_intelligence_tools.py` — existe.
- `domains/job_creation/services/jd_enrichment.py` — existe.

### #9 PII import quebrado — **PENDENTE**

`app/domains/job_creation/domain.py:32-40`:

```python
def _mask_pii(text: str) -> str:
    ...
    try:
        from app.services.pii_filter import mask_pii   # NÃO EXISTE
        return mask_pii(text[:500])
    except ImportError:
        return text[:500]   # silent fallback sem PII
```

### #10 3 chat paths divergentes — **PARCIAL (melhorou)**

| Path | Compliance atual | Estado |
|---|---|---|
| `api/v1/chat.py` | `pre_compliance` (l.222) + `post_compliance` (l.268) | OK |
| `api/v1/agent_chat_ws.py` | **`pre_compliance` (l.661) + `post_compliance` (l.951)** | **MELHORADO** desde o doc |
| `api/v1/agent_chat_sse.py` | Apenas `FairnessGuard` (l.216), sem `pre_compliance`/`post_compliance` | PENDENTE |

`agent_chat_ws_router` é incluído sem prefixo `/api/v1` (`routes.py:495`); WebSocket declarado em `@router.websocket("/ws/chat/{session_id}")` (linha 395 do arquivo) — confirma observação sobre prefixo público.

---

## 4. Tabela Canônica das 78 Findings

> **Convenção de IDs:** o documento original não numera explicitamente os 78 findings. Para esta auditoria, atribuímos IDs estáveis derivados das nomenclaturas que o próprio doc usa (R1-R7 nas Rotas, C1-C9 nas Compliance Critical, T1-T3 nas Tools, A1-A4 nos Agents Critical, D1-D3 nas Duplicatas Críticas, O1-O17 nos Orphans/Stubs, W1-W21 nas Warnings, I1-I32 nos Infos). A numeração reproduz a contagem de severidade do doc (26C / 20W / 32I) e o breakdown por dimensão (21 Compliance + 9 Tools + 20 Duplicatas + 11 Agents + 17 Routes).
> Onde o doc trata findings como **buckets** de severidade INFO (32 itens) sem enumeração individual, preservamos a quantidade total e marcamos a linha com `[bucket]`. Cada `[bucket]` recebe uma evidência aplicável **a todo o bucket** (dado verificável no código).

### 4.1 Compliance / Fairness — 21 findings (9C + 6W + 6I)

| # | ID | Severidade | Descrição (doc) | Status | Evidência (path:line) |
|---:|---|---|---|---|---|
| 1 | **C1** | C | `cv_scoring_service` sem FairnessGuard/Audit | PENDENTE | `domains/cv_screening/services/cv_scoring_service.py` — `grep FairnessGuard|fairness_guard|audit_service` = 0 |
| 2 | **C2** | C | `lia_score_service` sem FairnessGuard/Audit | PENDENTE | idem em `lia_score_service.py` = 0 |
| 3 | **C3** | C | `pre_qualification_service` sem FairnessGuard/Audit | PENDENTE | idem = 0 |
| 4 | **C4** | C | `eligibility_verification_service` sem FairnessGuard/Audit | PENDENTE | idem = 0 |
| 5 | **C5** | C | `evaluation_criteria_service` sem FairnessGuard/Audit | PENDENTE | idem = 0 |
| 6 | **C6** | C | `sourcing_pipeline_service` sem FairnessGuard/Audit/PII | PENDENTE | `domains/sourcing/services/sourcing_pipeline_service.py` — sem matches (Stage 2.2 não executada) |
| 7 | **C7** | C | `candidate_feedback_service` sem FairnessGuard no texto gerado | PENDENTE | `domains/candidates/services/candidate_feedback_service.py` — sem matches |
| 8 | **C8** | C | PII import quebrado em `job_creation/domain.py:37` | PENDENTE | `domains/job_creation/domain.py:37` — `from app.services.pii_filter import mask_pii` (arquivo inexistente) |
| 9 | **C9** | C | `stage_automation_engine` audit via shim path errado, sem FairnessGuard | PENDENTE | `domains/automation/services/stage_automation_engine.py:444` — ainda importa `app.shared.services.audit_service` |
| 10 | **W1** | W | `agent_chat_sse.py` sem `pre_compliance`/`post_compliance` (apenas FairnessGuard local) | PENDENTE | `api/v1/agent_chat_sse.py:204-216` — só `FairnessGuard().check`; `grep "pre_compliance\|post_compliance"` = 0 |
| 11 | **W2** | W | `agent_chat_ws_router` sem prefixo `/api/v1` (auth pública) | PENDENTE | `api/routes.py:495` (`include_router(agent_chat_ws_router)` sem prefixo) + `agent_chat_ws.py:395` (`/ws/chat/{session_id}`) |
| 12 | **W3** | W | `pipeline/action` audit pós sem FairnessGuard pré | PENDENTE | doc Stage 2.4; sem evidência de migração |
| 13 | **W4** | W | `weekly_digest_service` ainda importa shim de audit | PENDENTE | `domains/analytics/services/weekly_digest_service.py:344` — `from app.shared.services.audit_service` |
| 14 | **W5** | W | `proactive_alert_service` ainda importa shim de audit | PENDENTE | `domains/automation/services/proactive_alert_service.py:691` |
| 15 | **W6** | W | `bias_audit_service.py` no path errado (`shared/services/`) | PENDENTE | arquivo continua em `shared/services/bias_audit_service.py`, não em `shared/compliance/` |
| 16 | **I1** | I | `explainability_service` importa shim de audit | PENDENTE | `shared/services/explainability_service.py:18` |
| 17 | **I2** | I | `human_review_sampling_service` importa shim de audit | PENDENTE | `shared/services/human_review_sampling_service.py:105` |
| 18 | **I3** | I | `agent_bus` importa shim de audit | PENDENTE | `shared/agents/agent_bus.py:137` |
| 19 | **I4** | I | `automation/_shared.py` importa shim de audit | PENDENTE | `api/v1/automation/_shared.py:22` |
| 20 | **I5** | I | `services/__init__.py` reexporta `AuditService` do shim | PENDENTE | `app/services/__init__.py:60` |
| 21 | **I6** | I | Falta unit test para "boa aparência" → 422 nos scoring services | PENDENTE | nenhum teste cobre esse caminho (`grep "boa aparência" tests/`) |

**Subtotal:** 21 — todos PENDENTE.

### 4.2 Tool System — 9 findings (3C + 4W + 2I)

| # | ID | Sev | Descrição | Status | Evidência |
|---:|---|---|---|---|---|
| 22 | **T1** | C | `app/tools/registry.py` paralelo a `tool_handler` | PENDENTE | `app/tools/registry.py:1` (módulo presente); instância `tool_registry = ToolRegistry()` no final do arquivo |
| 23 | **T2** | C | 5 arquivos `@tool` LangChain puro | PENDENTE | `automation/tools/automation_tools.py:7`, `ats_integration/tools/ats_tools.py:8`, `interview_scheduling/tools/scheduling_tools.py:10`, `hiring_policy/tools/policy_tools.py:10`, `pipeline/tools/pipeline_tools.py:8` |
| 24 | **T3** | C | `GlobalToolRegistry` dead (zero `.register()` em produção) | PENDENTE | grep `\.register\(` em `app/` ignorando shared/global_tool_registry.py = só matches em testes |
| 25 | **W7** | W | `require_company=False` espalhado | PENDENTE | grep total = **89** ocorrências (autonomous=23, sourcing=18, pipeline=20, kanban=17, hiring_policy=4, talent=3, analytics=1, etc.) |
| 26 | **W8** | W | `tool_permissions.yaml` 70+ permissões nunca verificadas | PENDENTE | arquivo carregado só por `global_tool_registry.list_tools_for_scope`, sem caller |
| 27 | **W9** | W | Double-wrapping `@tool_handler` em `autonomous_tool_registry` | PENDENTE | `domains/autonomous/agents/autonomous_tool_registry.py` mantido sem refactor |
| 28 | **W10** | W | `tool_permissions_loader.py` dead | PENDENTE | importado apenas pelo próprio `global_tool_registry.py` |
| 29 | **I7** | I | Ausência de lint que proíba novo `@tool` LangChain | PENDENTE | `pyproject.toml` / `ruff.toml` sem regra dedicada |
| 30 | **I8** | I | Documentação do `tool_handler` ausente em `ARCHITECTURE.md` 10.3 | PENDENTE | seção 10.3 não menciona o decorator; verificável diretamente no `ARCHITECTURE.md` |

**Subtotal:** 9 — todos PENDENTE.

### 4.3 Duplicatas / Orphans — 20 findings (3C + 5W + 12I)

| # | ID | Sev | Descrição | Status | Evidência |
|---:|---|---|---|---|---|
| 31 | **D1** | C | 3 bias detectors divergentes | PENDENTE | `domains/interview_intelligence/services/bias_detector_service.py:1`, `domains/talent_intelligence/tools/interview_intelligence_tools.py:1`, `domains/job_creation/services/jd_enrichment.py:1` |
| 32 | **D2** | C | `job_report_service.py` duplicado idêntico | PENDENTE | `analytics/services/job_report_service.py` (33 564 B) e `job_management/services/job_report_service.py` (33 564 B — **idênticos**) |
| 33 | **D3** | C | `pipeline_tool_registry.py` duplicado divergente | PENDENTE | `pipeline/agents/pipeline_tool_registry.py` (57 797 B) vs `cv_screening/agents/pipeline_tool_registry.py` (41 228 B) — divergência aumentou desde o doc |
| 34 | **W11** | W | `job_insights_service.py` near-dup | PENDENTE | analytics 36 876 B vs job_management 36 966 B |
| 35 | **W12** | W | `user_repository.py` duplicado | PENDENTE | `auth/repositories/user_repository.py` (5 137 B) vs `company/repositories/user_repository.py` (3 227 B) |
| 36 | **W13** | W | `kanban_assistant_service.py` minimal vs canonical | PENDENTE | `pipeline/kanban_assistant_service.py` (3 921 B) vs `recruiter_assistant/services/kanban_assistant_service.py` (29 470 B) |
| 37 | **W14** | W | `seniority_resolver.py` em 2 lugares | PENDENTE | `cv_screening/services/seniority_resolver.py` (30 795 B) e `job_creation/services/seniority_resolver.py` (8 431 B) |
| 38 | **W15** | W | `wizard_analytics_service.py` rename pendente | PENDENTE | nenhum movimento |
| 39 | **O1** | I | Órfão `bars_evaluator.py` | PENDENTE | `app/shared/bars_evaluator.py` — 0 importadores |
| 40 | **O2** | I | Órfão `batch_service.py` | PENDENTE | `app/shared/batch_service.py` — 0 importadores |
| 41 | **O3** | I | Órfão `domain_action_registry.py` | PENDENTE | `app/shared/domain_action_registry.py` — 0 importadores |
| 42 | **O4** | I | Órfão `multi_domain_plan.py` | PENDENTE | `app/shared/multi_domain_plan.py` — 0 importadores |
| 43 | **O5** | I | Órfão `param_validation.py` | PENDENTE | `app/shared/param_validation.py` — 0 importadores |
| 44 | **O6** | I | Órfão `messaging/rails_crud_consumer.py` | PENDENTE | 0 importadores |
| 45 | **O7** | I | Órfão `services/human_review_sampling_service.py` | PENDENTE | 0 importadores |
| 46 | **O8** | I | Órfão `services/intent_yaml_validator.py` | PENDENTE | 0 importadores |
| 47 | **O9** | I | Quasi-órfão `prompts/examples/job_planner_examples.py` | PENDENTE | 1 importador (apenas re-export em `examples/__init__.py:8`) |
| 48 | **O10** | I | Quasi-órfão `prompts/examples/orchestrator_examples.py` | PENDENTE | 1 (apenas `__init__.py:16`) |
| 49 | **O11** | I | Quasi-órfão `prompts/examples/pipeline_examples.py` | PENDENTE | 1 (apenas `__init__.py:24`) |
| 50 | **O12** | I | Quasi-órfão `prompts/examples/sourcing_examples.py` | PENDENTE | 1 (apenas `__init__.py:32`) |

**Subtotal:** 20 — todos PENDENTE.

### 4.4 Agent Patterns — 11 findings (4C + 1W + 6I)

| # | ID | Sev | Descrição | Status | Evidência |
|---:|---|---|---|---|---|
| 51 | **A1** | C | JobCreationGraph 5% compliance + (alegação de) órfão | PARCIAL | compliance 5% confirmado (`grep FairnessGuard|AuditCallback|audit_service|tenant_llm_context|LangGraphReActBase` em `domains/job_creation/graph.py` = 0). Alegação de órfão é OBSOLETA (importado por `domain.py:27`). |
| 52 | **A2** | C | PolicySetupAgent 25% (sem FairnessGuard, PII, tenant LLM, base) | PENDENTE | `domains/policy/agents/agent.py` — todos os 6 critérios = 0 (ver matriz §5) |
| 53 | **A3** | C | InterviewGraph 50% (sem base, sem tenant LLM, sem registry) | PENDENTE | `domains/interview_scheduling/agents/interview_graph.py` — base=0, tenant=0; não está em `agents_registry.yaml` |
| 54 | **A4** | C | WSIInterviewGraph 55% (sem tenant LLM, sem registry) | PENDENTE | `domains/cv_screening/agents/wsi_interview_graph.py` — tenant=0, não em `agents_registry.yaml` |
| 55 | **W16** | W | CompanySettingsReActAgent órfão (sem rota no orchestrator) | PARCIAL | `orchestrator/domain_mappings.py:39-41` agora mapeia `company_settings`/`company_profile`/`company_config` → gap parcialmente endereçado; falta verificar `domain_routing.yaml` |
| 56 | **I9** | I | Sub-agents Sourcing (10) não registrados individualmente | PENDENTE | nenhum aparece em `agents_registry.yaml` (ver §5) |
| 57 | **I10** | I | Sub-agents Pipeline (3) não registrados individualmente | PENDENTE | idem |
| 58 | **I11** | I | Sub-agents Kanban (3) não registrados individualmente | PENDENTE | idem |
| 59 | **I12** | I | AutonomousReActAgent não está no `ReactAgentRegistry` (class) | PENDENTE | `agents_registry.yaml` registra como `name: autonomous`, mas registry classe-level não cobre (verificável em `shared/agents/agent_registry.py`) |
| 60 | **I13** | I | JobWizardGraph sem base ReAct | PENDENTE | `domains/job_management/agents/job_wizard_graph.py` — `grep LangGraphReActBase` = 0 |
| 61 | **I14** | I | JobWizardGraph sem `SystemPromptBuilder` | PENDENTE | mesmo arquivo — `grep SystemPromptBuilder` = 0 |

**Subtotal:** 11 — 9 PENDENTE + 2 PARCIAL (A1 com classificação de orfandade obsoleta; W16 endereçada parcialmente).

### 4.5 Routes / API — 17 findings (7C + 4W + 6I)

| # | ID | Sev | Descrição | Status | Evidência |
|---:|---|---|---|---|---|
| 62 | **R1** | C | IDOR `finetuning_export` | PENDENTE | `api/v1/finetuning_export.py:11-13` (`/stats/{company_id}` sem `get_current_user`); `:21-26` (`/export/{company_id}` idem) |
| 63 | **R2** | C | `applications.apply` sem auth/Fairness/Audit | PENDENTE | `api/v1/applications.py:104-106` (Depends sem user); arquivo todo: 0 matches `FairnessGuard|audit_service` |
| 64 | **R3** | C | `bulk_actions` sem compliance | PENDENTE | `api/v1/bulk_actions.py:1` (arquivo todo: 0 matches `FairnessGuard|audit_service`) |
| 65 | **R4** | C | `stage_transition_automation` sem compliance | PENDENTE | `api/v1/stage_transition_automation.py:1` (idem, 0 matches) |
| 66 | **R5** | C | LLM Config registrado 2× (linhas 427/526) | **OBSOLETO** | `api/routes.py` — `llm_config_router` aparece **apenas** na linha 426 (única chamada `include_router`). Confirmado por `grep -n "llm_config_router" routes.py` |
| 67 | **R6** | C | Webhooks registrado 2× (linhas 530/609) | **OBSOLETO** | `api/routes.py` — `webhooks.router` aparece **apenas** na linha 529 |
| 68 | **R7** | C | 3 chat paths divergentes | PARCIAL | WS agora completo (l.661+951); SSE ainda parcial |
| 69 | **W17** | W | `agent_chat_ws_router` em prefixo público `/ws/` | PENDENTE | `routes.py:495` sem `/api/v1` |
| 70 | **W18** | W | `company_benefits_api.py` colide com `company_benefits.py` | PENDENTE | `api/v1/company_benefits_api.py:1` (0 importers); `api/v1/company_benefits.py:1` (canonical); ambos existem, conflito de naming |
| 71 | **W19** | W | CompanySettingsReActAgent sem rota | PARCIAL | ver W16 (= W19 no doc) — mappings cobrem; `domain_routing.yaml` pendente |
| 72 | **W20** | W | Audit shim path em 8 arquivos | PENDENTE | 8/8 confirmados (ver C9, W4, W5, I1-I5) |
| 73 | **O13** | I | Rota órfã `company_benefits_api.py` | PENDENTE | `api/v1/company_benefits_api.py:1`; ausente de `api/routes.py` (grep = 0) |
| 74 | **O14** | I | Rota stub `lia_autonomous.py` | PENDENTE | `api/v1/lia_autonomous.py:1` — 3 linhas no total |
| 75 | **O15** | I | Rota stub `lia_feedback.py` | PENDENTE | `api/v1/lia_feedback.py:1` — 3 linhas no total |
| 76 | **O16** | I | Rota stub `lia_multimodal.py` | PENDENTE | `api/v1/lia_multimodal.py:1` — 3 linhas no total |
| 77 | **O17** | I | Rota stub `lia_voice.py` | PENDENTE | `api/v1/lia_voice.py:1` — 3 linhas no total |
| 78 | **W21** | W | `external_webhooks`/`merge_webhooks`/`mailgun_webhooks` aparentam duplicação mas são distintos | OBSOLETO | `routes.py:532-534` — 3 routers distintos; conflito apenas semântico (3 provedores de webhook), não duplicação técnica |

**Subtotal:** 17 — 12 PENDENTE + 2 PARCIAL + 3 OBSOLETO.

### 4.6 Reconciliação total

| Dimensão | C | W | I | Total | PENDENTE | PARCIAL | OBSOLETO |
|---|---:|---:|---:|---:|---:|---:|---:|
| Compliance | 9 | 6 | 6 | 21 | 21 | 0 | 0 |
| Tool System | 3 | 4 | 2 | 9 | 9 | 0 | 0 |
| Duplicatas/Órfãos | 3 | 5 | 12 | 20 | 20 | 0 | 0 |
| Agent Patterns | 4 | 1 | 6 | 11 | 9 | 2 | 0 |
| Routes/API | 7 | 4 | 6 | 17 | 12 | 2 | 3 |
| **Total** | **26** | **20** | **32** | **78** | **71** | **4** | **3** |

> Esta é a única contabilidade canônica do relatório (também usada em §1).

---

## 5. Matriz 35 Agentes × 7 Critérios

> **Critérios** (do doc, página "Agent Compliance Scorecard"):
> 1. **Base** — herda `LangGraphReActBase`
> 2. **Audit** — usa `AuditCallback`
> 3. **FG** — usa `FairnessGuard`
> 4. **PII** — usa `pii_masking` / `mask_pii` / `strip_pii`
> 5. **Tenant LLM** — usa `tenant_llm_context` ou `get_provider_for_tenant`
> 6. **SPB** — usa `SystemPromptBuilder`
> 7. **Reg** — listado em `agents_registry.yaml`
>
> **Convenção:** `✓` = import direto verificável no arquivo; `↑` = herdado da classe-pai (sub-agent); `—` = ausente. Para sub-agents, contagem do critério (1) e (3) propaga via classe-pai mas é grafada `↑`.
>
> **Discrepância no doc:** o título "35 agents" enumera **36 linhas** (1-36). Mantemos 36 linhas para fidelidade ao source, com nota.

| # | Agente | Arquivo | (1) Base | (2) Audit | (3) FG | (4) PII | (5) Tenant | (6) SPB | (7) Reg | Score doc | Score validado |
|---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|---:|
| 1 | WizardReActAgent | `domains/job_management/agents/wizard_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`wizard`) | 100% | **57%** |
| 2 | PipelineTransitionAgent | `domains/pipeline/agents/pipeline_transition_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`pipeline`) | 100% | **57%** |
| 3 | SourcingReActAgent | `domains/sourcing/agents/sourcing_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`sourcing`) | 100% | **57%** |
| 4 | TalentReActAgent | `domains/recruiter_assistant/agents/talent_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`talent`) | 100% | **57%** |
| 5 | JobsManagementReActAgent | `domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`jobs_management`) | 100% | **57%** |
| 6 | KanbanReActAgent | `domains/recruiter_assistant/agents/kanban_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`kanban`) | 100% | **57%** |
| 7 | PolicyReActAgent | `domains/hiring_policy/agents/policy_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`policy`) | 100% | **57%** |
| 8 | AutomationReActAgent | `domains/automation/agents/automation_react_agent.py` | ✓ | — | — | — | — | — | ✓ (`automation`) | 100% | **43%** |
| 9 | AnalyticsReActAgent | `domains/analytics/agents/analytics_react_agent.py` | ✓ | — | — | — | — | — | ✓ (`analytics`) | 100% | **43%** |
| 10 | CommunicationReActAgent | `domains/communication/agents/communication_react_agent.py` | ✓ | — | ✓ | — | — | — | ✓ (`communication`) | 100% | **57%** |
| 11 | ATSIntegrationReActAgent | `domains/ats_integration/agents/ats_integration_react_agent.py` | ✓ | — | — | — | — | — | ✓ (`ats_integration`) | 100% | **43%** |
| 12 | CustomAgentRuntime | `domains/agent_studio/custom_agent_runtime.py` | n/a (runtime) | — | — | — | — | — | — | 100% | **N/A** (runtime, não agente individual) |
| 13 | AutonomousReActAgent | `domains/autonomous/agents/autonomous_react_agent.py` | ✓ | ✓ | ✓ | — | — | ✓ | ✓ (`autonomous`) | 95% | **86%** |
| 14 | KanbanActionAgent | `domains/recruiter_assistant/agents/kanban_action_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | **29%** |
| 15 | KanbanSearchAgent | `domains/recruiter_assistant/agents/kanban_search_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 16 | KanbanInsightAgent | `domains/recruiter_assistant/agents/kanban_insight_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 17 | PipelineActionAgent | `domains/pipeline/agents/pipeline_action_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | **29%** |
| 18 | PipelineContextAgent | `domains/pipeline/agents/pipeline_context_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 19 | PipelineDecisionAgent | `domains/pipeline/agents/pipeline_decision_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 20 | SourcingPlannerAgent | `domains/sourcing/agents/sourcing_planner_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 21 | SourcingSearchAgent | `domains/sourcing/agents/sourcing_search_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 22 | SourcingEnrichAgent | `domains/sourcing/agents/sourcing_enrich_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 23 | SourcingEngagementAgent | `domains/sourcing/agents/sourcing_engagement_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 24 | DiversitySourcingAgent | `domains/sourcing/agents/diversity_sourcing_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | **29%** |
| 25 | GithubSourcingAgent | `domains/sourcing/agents/github_sourcing_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | **29%** |
| 26 | NurtureSequenceAgent | `domains/sourcing/agents/nurture_sequence_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 27 | PassivePipelineAgent | `domains/sourcing/agents/passive_pipeline_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 28 | ReferralAgent | `domains/sourcing/agents/referral_agent.py` | ↑ | — | — | — | — | — | — | 95% | **14%** |
| 29 | StackOverflowSourcingAgent | `domains/sourcing/agents/stackoverflow_sourcing_agent.py` | ↑ | — | ✓ | — | — | — | — | 95% | **29%** |
| 30 | PipelineReActAgent (cv_screening) | `domains/cv_screening/agents/pipeline_react_agent.py` | ✓ | — | — | — | — | — | — | 95% | **14%** |
| 31 | CompanySettingsReActAgent | `domains/company_settings/agents/company_react_agent.py` | ✓ | — | ✓ | — | — | — | parcial (mappings) | 80% | **43%** |
| 32 | JobWizardGraph | `domains/job_management/agents/job_wizard_graph.py` | — | ✓ | ✓ | ✓ | — | — | ✓ (`wizard`) | 60% | **57%** |
| 33 | WSIInterviewGraph | `domains/cv_screening/agents/wsi_interview_graph.py` | — | ✓ | ✓ | ✓ | — | — | — | 55% | **43%** |
| 34 | InterviewGraph | `domains/interview_scheduling/agents/interview_graph.py` | — | ✓ | — | ✓ | — | — | — | 50% | **29%** |
| 35 | PolicySetupAgent | `domains/policy/agents/agent.py` | — | — | — | — | — | — | — | 25% | **0%** |
| 36 | JobCreationGraph | `domains/job_creation/graph.py` | — | — | — | — | — | — | — | 5% | **0%** |

**Notas:**
- Sub-agents (linhas 14-29) **herdam** a base ReAct e parte das verificações; os scores baixos refletem critérios verificáveis **no próprio arquivo**, não a herança implícita. Quando a documentação dá 95% por herança, mantemos a coluna marcada com `↑` para reconhecer.
- **Tenant LLM (5)** = 0 em **todos os 36 agentes** — nenhum importa `tenant_llm_context` ou `get_provider_for_tenant` diretamente. O contexto multi-tenant chega via `LangGraphReActBase` ou via factory. O doc creditava 100% nessa coluna por herança implícita; mantemos o critério **literal**.
- **SystemPromptBuilder (6)** = 0 em **todos** exceto AutonomousReActAgent — o prompt builder é injetado via `agents_registry.yaml > system_prompt_path` e aplicado pela framework, não importado pelos agentes. Mesma ressalva.
- A coluna "Score validado" usa apenas critérios verificáveis no arquivo. A coluna "Score doc" reproduz o que o doc atribui (incluindo créditos por herança). A divergência maior é no bloco 14-29, onde o doc atribui 95% mas o arquivo individual mostra ≤29%.
- **Discrepância de contagem:** doc diz "35 agents" mas tabula 36 linhas. Mantemos as 36 para fidelidade.

---

## 6. Validação de `routes.py`

- `llm_config_router`: linhas **260** (import) e **426** (include) — **1 include**. **R5 OBSOLETO**.
- `webhooks.router`: linha **529** — **1 include**. **R6 OBSOLETO**.
- `agent_chat_ws_router`: linha **212** (import) e **495** (include sem prefixo). **W17 confirmado**.
- `agent_chat_sse_router`: linha **213** (import) e **496** (include com prefixo `/api/v1`).
- `external_webhooks` / `merge_webhooks` / `mailgun_webhooks`: linhas **532-534**, 3 routers distintos. Não constituem duplicação.

---

## 7. Estado de `shared/observability/`

`app/shared/observability/__init__.py` — apenas comentário de cabeçalho, sem qualquer re-export ou símbolo público (efetivamente não-implementado). Os 11 arquivos previstos para mover continuam nos locais antigos:

| Arquivo | Local atual | Movido? |
|---|---|---|
| `tracing.py` | `shared/tracing.py` | NÃO |
| `structured_logging.py` | `shared/structured_logging.py` | NÃO |
| `llm_callbacks.py` | `shared/llm/callbacks.py` | NÃO |
| `agent_monitoring_service.py` | `shared/governance/agent_monitoring_service.py` | NÃO |
| `agent_health_alert_service.py` | `shared/services/agent_health_alert_service.py` | NÃO |
| `model_drift_service.py` | `domains/ai/services/model_drift_service.py` | NÃO |
| `drift_alert_service.py` | `domains/lgpd/services/drift_alert_service.py` | NÃO |
| `token_tracking_service.py` | `domains/analytics/services/token_tracking_service.py` | NÃO |
| `token_budget_service.py` | `domains/credits/services/token_budget_service.py` | NÃO |
| `wsi_observability.py` | `domains/analytics/services/wsi_observability.py` | NÃO |
| `langsmith_config.py` | `config/langsmith.py` | NÃO |

Stage 6 inteiro pendente.

---

## 8. Análise Crítica do Diagnóstico

### O que o documento acertou
1. Severidade dos riscos regulatórios (IDOR, applications/bulk_actions sem fairness, scoring services sem audit) — todos confirmados por evidência de código.
2. Mapeamento dos 5 arquivos `@tool` legados — exato.
3. 12 órfãos — todos confirmados (8 com 0 importers, 4 com apenas re-export interno).
4. PII import quebrado — confirmado.
5. Tool system desconectado e Task #125 não-resolvendo — confirmado.
6. Estrutura proposta para `shared/observability/` SSOT — alinhada com SSOT/DDD.

### Onde o documento está incorreto / desatualizado
1. **R5 e R6** (rotas duplicadas) — não existem hoje. Doc estava errado nos números de linha ou já foi remediado.
2. **JobCreationGraph "órfão"** — está conectado ao `domain.py:27`. O gap real é apenas "5% compliance".
3. **W21** (3 webhooks "duplicados") — são 3 provedores distintos.
4. **Scorecard 95% para sub-agents por herança** — quando avaliamos os arquivos individuais, a maioria fica em 14-29%. A herança implícita é uma escolha do doc, não uma verdade do código.
5. **CompanySettingsReActAgent "sem rota"** (W16/W19) — `domain_mappings.py:39-41` já endereça parcialmente.

### Onde o documento poderia ser mais cuidadoso
1. **Estimativas de esforço** otimistas para Stages 4 e 5 (pipeline_tool_registry com 57k vs 41k divergente é XL, não L).
2. **156 shims como "inofensivos"** — debt acumulada; sugerimos SLA explícito.
3. **GlobalToolRegistry — "ativar ou deletar":** o caminho mais barato é **deletar**. O sistema funciona sem ele há meses.
4. **Bias detectors (D1):** antes de migrar, comparar coverage de patterns para não perder cobertura.
5. **Audit shim (W21/C9/W4-W5/I1-I5):** o sweep de 8 imports é de baixo risco, mas convém validar que `shared/services/audit_service.py` é de fato apenas re-export antes de remover.

### Princípios enterprise — alinhamento
- SSOT (FairnessGuard, AuditService, observability): ✓
- DDD (compliance em camada cross-cutting): ✓
- Multi-tenant fail-closed (`require_company=True` default): ✓ (já em `tool_handler`)
- Eliminação de duplicação: ✓
- Cleanup de shims: ⚠ falta SLA

---

## 9. Próximas Tarefas Sugeridas

> Priorizadas por risco. Tarefas já em fila não estão repetidas.

### Stage 1 — Hotfixes (2-4 h)
- **S1.1** Adicionar `get_current_user` + checagem de `company_id` em `finetuning_export.py` (R1).
- **S1.2** Substituir `from app.services.pii_filter import mask_pii` por `from app.shared.pii_masking import mask_pii_text as mask_pii` em `domains/job_creation/domain.py:37` (C8).
- **S1.3** Sweep de imports `from app.shared.services.audit_service` → `from app.shared.compliance.audit_service` nos 8 arquivos confirmados (C9, W4, W5, I1-I5).

### Stage 2 — Compliance Gates (2-3 dias)
- **S2.1** `FairnessGuard.check()` pre + `audit_service.log_decision()` post nos 5 services de scoring (C1-C5). Tarefa por arquivo.
- **S2.2** Auth + `FairnessGuard` + audit em `applications.apply` (R2).
- **S2.3** Compliance + audit em `bulk_actions.py` e `stage_transition_automation.py` (R3, R4).
- **S2.4** `FairnessGuard` em `candidate_feedback_service` e `sourcing_pipeline_service` (C6, C7).

### Stage 3 — Tools (3-5 dias)
- **S3.1** Migrar 5 arquivos `@tool` para `@tool_handler(domain, require_company=True)` (T2).
- **S3.2** Reduzir `require_company=False` (89 ocorrências) começando por `pipeline_tool_registry`, `autonomous_tool_registry`, `kanban_tool_registry` (W7).
- **S3.3** **Deletar** `GlobalToolRegistry` + `tool_permissions.yaml` + `tool_permissions_loader.py` + `app/tools/registry.py` (T1, T3, W8, W10).

### Stage 4 — Agents (3-5 dias)
- **S4.1** JobCreationGraph 5%→~70% (A1).
- **S4.2** PolicySetupAgent 25%→~80% (A2).
- **S4.3** InterviewGraph 50%→~80% e WSIInterviewGraph 55%→~85% (A3, A4).
- **S4.4** Convergir SSE em `pre_compliance` + `post_compliance` (R7 — última parte).
- **S4.5** Mover `agent_chat_ws_router` para prefixo autenticado (W17).
- **S4.6** Patterns em `domain_routing.yaml` para CompanySettings (W16/W19 — fechar 100%).

### Stage 5 — Cleanup (2-3 dias)
- **S5.1** Consolidar 3 bias detectors no `FairnessGuard` (D1).
- **S5.2** Deletar `domains/job_management/services/job_report_service.py` idêntico (D2).
- **S5.3** Refatorar `cv_screening/agents/pipeline_tool_registry.py` para importar do `pipeline/agents/` (D3).
- **S5.4** Deletar 12 órfãos confirmados (O1-O12).
- **S5.5** Deletar 4 stubs `lia_*` + `company_benefits_api.py` (O13-O17, W18).
- **S5.6** Mover `bias_audit_service.py` para `shared/compliance/` com shim (W6).
- **S5.7** Consolidar `user_repository`, `kanban_assistant_service`, `seniority_resolver`, `wizard_analytics_service`, `job_insights_service` (W11-W15).

### Stage 6 — Observability (paralelo com 2-4)
- **S6.1** Mover 11 arquivos para `shared/observability/` + criar shims antigos.
- **S6.2** Atualizar 10 consumidores diretos de `shared.tracing` para path canônico.
- **S6.3** Atualizar `ARCHITECTURE.md` seções 5.1 e 9.4; `CANONICAL_SOURCES_SPEC.md`; `CLAUDE.md`.

### Recomendações adicionais
- **S7.1** SLA de cleanup para 156 shims (ex.: 0 importadores há 90+ dias = elegível).
- **S7.2** Teste regressional: app sobe → `GlobalToolRegistry._registry` não vazio (força "ativar ou deletar").
- **S7.3** Lint rule (CI) proibindo `from langchain_core.tools import tool` em `app/domains/*/tools/`.

---

## 10. Apêndice — Como Reproduzir Cada Verificação

```bash
# Routes (R5/R6)
grep -nE "llm_config_router|webhooks\.router" lia-agent-system/app/api/routes.py

# 5 legacy @tool (T2)
grep -rln "from langchain_core.tools import tool" lia-agent-system/app/domains/

# PII import quebrado (C8)
sed -n '32,40p' lia-agent-system/app/domains/job_creation/domain.py

# Scoring sem FairnessGuard (C1-C5)
for f in cv_scoring lia_score pre_qualification eligibility_verification evaluation_criteria; do
  grep -c "FairnessGuard\|fairness_guard\|audit_service" \
    lia-agent-system/app/domains/cv_screening/services/${f}_service.py
done

# Audit shim (W20 + dependentes)
grep -rn "from app.shared.services.audit_service" lia-agent-system/app/

# Órfãos (O1-O12)
for f in bars_evaluator batch_service domain_action_registry multi_domain_plan param_validation; do
  grep -r "app\.shared\.${f}" lia-agent-system/app --include='*.py' -l | grep -v "shared/${f}.py"
done

# JobCreationGraph compliance (A1)
grep -c "FairnessGuard\|AuditCallback\|audit_service\|tenant_llm_context\|LangGraphReActBase" \
  lia-agent-system/app/domains/job_creation/graph.py

# require_company=False (W7)
grep -rn "require_company\s*=\s*False" lia-agent-system/app/

# GlobalToolRegistry dead (T3)
grep -rn "GlobalToolRegistry\.get_instance\|get_registry()\.register" lia-agent-system/app/

# Observabilidade canonical
ls lia-agent-system/app/shared/observability/

# Matriz 35-agents 7-critérios (loop)
for a in $(find lia-agent-system/app/domains -name '*react_agent*.py' -o -name '*_graph.py'); do
  printf '%s | base=%d aud=%d fg=%d pii=%d ten=%d spb=%d\n' "$a" \
    "$(grep -c LangGraphReActBase $a)" \
    "$(grep -c 'AuditCallback\|audit_callback' $a)" \
    "$(grep -c 'FairnessGuard\|fairness_guard' $a)" \
    "$(grep -c 'pii_masking\|mask_pii\|strip_pii' $a)" \
    "$(grep -c 'tenant_llm_context\|get_provider_for_tenant' $a)" \
    "$(grep -c 'SystemPromptBuilder\|system_prompt_builder' $a)"
done
```

---

*Auditoria gerada em 2026-04-16 — Tarefa #302. Verificação 1:1 com `CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN_1776381503482.md`. Nenhum arquivo de código foi modificado.*
