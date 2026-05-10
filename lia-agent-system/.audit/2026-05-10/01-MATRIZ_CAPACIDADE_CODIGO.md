# 01 — Matriz Capacidade × Código — SSH Audit

> **Fase 1 da auditoria profunda LIA WeDOTalent.** Todas as células validadas via SSH read-only ao Replit canonical.
>
> **HEAD validado:** `ff81b2aedc12ba9efa61c590b4792636aa8f6a3b` (= `ff81b2aed`)
> **Branch:** `feat/benefits-prv-canonical`
> **Data auditoria:** 2026-05-10
> **Método:** 4 Explore agents paralelos via SSH `replit-wedo-0405`. Auditoria estrutural por lote (Job, Candidate, Talent+Sourcing, Compliance).
>
> **Princípio aplicado:** código é fonte de verdade. Cada célula tem file:line + comando SSH como evidência. Achados de docs antigos sem cross-check no código foram descartados.

---

## Sumário executivo

| Métrica | Valor |
|---|---|
| Domains agentic auditados | **19/19** (100%) |
| Tools mapeadas com file:line | ~120 |
| Sensores executados via SSH | 6 (com output real) |
| Findings P0 confirmados | **3** |
| Findings P1 confirmados | **5** |
| Findings P2 confirmados | **6** |
| Falsos positivos da 1ª rodada (worktree local) descartados | **8** |

**Status macro da plataforma (Sprint B atual):**
- ✅ Estrutura agentic canonical sólida (19 domains, ~50 sub-agents, ~120 tools)
- ✅ Compliance ADRs aplicadas (LIA-C01: 19/19 domains; ADR-001: 0 violations; ADR-029: 0 leaks)
- ✅ Plan & Execute wired (28 PlanPatterns, 52 task_ids)
- ⚠ **3 P0 críticos compliance** — todos legítimos (LGPD/multi-tenancy/FairnessGuard)
- ⚠ **5 P1** — todos validados via SSH

---

## Achados consolidados — P0/P1/P2 (todos SSH-validated)

### 🔴 P0 (Blockers — bloqueiam produção segundo Inegociáveis)

#### P0-1: PII em logs — 335+ violations (LGPD inegociável #4)

**Evidência SSH (sensor):**
```
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python scripts/check_no_pii_in_logs.py 2>&1 | tail -20'
```
Retorna **335+ violations em 15+ arquivos**.

**Exemplos concretos:**
- `app/api/v1/communications.py:335` — `logger.info(f"✅ Email sent to {request.to_email} ...")`
- `app/api/v1/client_users.py:404` — f-string com `user.id`, `client.name`
- `app/api/v1/company.py` — múltiplos f-strings com PII

**Impacto:** Violação direta da Inegociável #4 (PII masking 100% logs). Risco LGPD + audit trail contamination.

**Fix:** ADR-006 — substituir f-string por `logger.info("...", extra={"email_masked": mask(email)})` ou format masking.

**Esforço estimado:** L (3-4 dias) — 335 instances, mas pattern repetitivo permite migration script.

---

#### P0-2: Multi-tenancy bypass — 20+ endpoints sem `_require_company_id()`

**Evidência SSH (sensor):**
```
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python scripts/check_company_id_in_routes.py 2>&1 | tail -20'
```

**Concentração de violações:**
- `app/api/v1/recruitment_stages/`: **9 endpoints**
  - `stages_crud.py:104` — `update_stage()`
  - `stages_crud.py:136` — `delete_stage()`
  - `stages_substatus.py:120` — `patch_sub_status()`
  - `stages_substatus.py:146` — `delete_sub_status()`
  - `stages_transition.py:266` — `execute_transition()`
  - `stages_ats_mapping.py:79` — `delete_ats_mapping()`
  - + reorder_stages, etc.
- `app/api/v1/ats.py`: **3 endpoints**
  - `ats.py:63-123` — `POST /ats/connections`
  - `ats.py:249-289` — `POST /ats/field-mappings`
  - `ats.py:411-566` — `POST /ats/connections/{id}/sync`

**Impacto:** Cross-company data leak. Risco compliance crítico.

**Fix:** Adicionar `_require_company_id()` ou `get_user_company_id()` em cada endpoint, ou marker `# multi-tenancy: <reason>` se intencional.

**Esforço estimado:** M (2-3 dias) — fix repetitivo + tests.

---

#### P0-3: `offer` domain `high_impact:True` SEM FairnessGuard

**Evidência SSH (grep direto):**
```
ssh replit-wedo-0405 'grep -rn "FairnessGuard\|fairness_guard\|fairness_check" /home/runner/workspace/lia-agent-system/app/domains/offer/ --include="*.py"'
```
Retorna **vazio** — nenhuma referência a FairnessGuard no domain.

**Domain config (cross-check):**
- `app/domains/offer/domain.py:27` — `OfferDomain(ComplianceDomainPrompt)`
- Compliance config: `{"high_impact": True, "fairness_action_type": "offer"}`

**6 tools no domain (todas sem gate):**
- `create_offer_draft`, `update_offer_draft`, `get_offer_draft`
- `send_offer` (marked high-impact, requires_confirmation=True) — **mas sem FairnessGuard pré-send**
- `prepare_offer_manual_send`, `cancel_offer`

**Impacto:** Violação Inegociável #3 (FairnessGuard 100% screening + decisões de alto impacto). Oferta pode ir sem checagem de bias.

**Fix:** Implementar `compliance.py` em `app/domains/offer/` espelhando padrão de `app/domains/job_creation/compliance.py` — pre-check fairness em `send_offer`.

**Esforço estimado:** M (2 dias) — usar pattern existente em job_creation.

---

### 🟡 P1 (Critical — não bloqueiam mas degradam compliance)

#### P1-1: `automation/pipeline_monitor.py:299` auto_rejection sem HITL gate

**Evidência SSH:**
- `app/domains/automation/services/pipeline_monitor.py:299-301` — flag `auto_rejection` em communication rule
- Comparação: `app/domains/automation/services/stage_automation_engine.py:458` tem `human_review_required=not result.get("executed")`
- **Pipeline_monitor não força HITL** mesmo em rejeições.

**Impacto:** Viola Inegociável #2 (no auto-rejection). Comunicação automation pode rejeitar candidato sem aprovação humana.

**Fix:** Adicionar `human_review_required=True` gate em pipeline_monitor antes de auto_rejection.

---

#### P1-2: Agent compliance gaps em 3 agents (sensor `check_agent_compliance`)

**Evidência SSH (sensor):**
- `automation_react_agent.py` — missing `@register_agent("automation")` decorator
- `autonomous_react_agent.py` — missing `@register_agent("autonomous")` decorator
- `talent_react_agent.py` — missing `LangGraphReActBase`, `EnhancedAgentMixin`, `@register_agent` (FAR-2 violation)
- 7 violations totais em 3 of 15 agents

**Impacto:** Falta `FairnessGuard().check()` automático + PII redaction (LGPD/LIA-C04).

**Fix:** Adicionar decoradores e inheritance canonical em cada agent.

---

#### P1-3: FairnessGuard Layer 3 feature-flagged (default OFF)

**Evidência SSH:**
- `app/shared/compliance/fairness_guard.py:820-824` — Layer 3 (LLM semantic) condicional em `FAIRNESS_LAYER3_ENABLED`
- Default: disabled.

**Impacto:** Inegociável #3 (FairnessGuard 3 camadas) parcialmente ativo. Layer 1 (regex) + Layer 2 (léxico implícito) sempre on, mas Layer 3 (LLM semantic) off por default.

**Fix:** Promover Layer 3 para default-on (ou explicitar como enterprise feature).

---

#### P1-4: HITL gate limitado a feature flags

**Evidência SSH:**
- `app/api/v1/lia_assistant_flags.py:72-91` — `SENSITIVE_FLAGS_REQUIRING_HITL` lista
- HITL enforced **apenas** para mutations de feature flags (`lia_assistant_flags.py:183-192`)
- Domain tools (offer.send_offer, pipeline rejection, etc.) não têm gate explícito centralizado

**Impacto:** Inegociável #7 (Human override) parcial. Centralized HITL não existe pra ações de domínio (cada domain implementa por conta).

**Fix:** Generalizar HITL para tools com `SafetyCategory` high-impact via decorador ou middleware.

---

#### P1-5: `job_management` 0 testes específicos para 29 actions + WizardReActAgent

**Evidência SSH:**
```
ssh replit-wedo-0405 'find /home/runner/workspace/lia-agent-system/tests -path "*job_management*" -name "*.py" 2>/dev/null | wc -l'
```
Retorna 0.

**Domain tem:**
- 29 actions (`actions.py`)
- WizardReActAgent canonical (`@register_agent("wizard")`)
- 11 services + 5 tool files

**Impacto:** Risco de regressão em fluxos críticos (criação de vaga, wizard).

**Fix:** Mínimo 15 testes de integração agent → domain flow.

---

### 🟢 P2 (Important — qualidade/consistência)

#### P2-1: `hiring_policy` 2 tools sem FairnessGuard invoke explícito
- `tools/policy_tools.py:15-68` — `check_diversity_targets` (esperado FairnessGuard, missing invoke)
- `tools/policy_tools.py:70-114` — `validate_job_requirements` (no PII redaction)

#### P2-2: `ats_integration` webhook signature validation only
- `app/api/v1/ats.py:649-758` — `POST /ats/webhooks/{provider}` valida signature mas não tem company_id check

#### P2-3: `recruitment_campaign` skeleton (4 actions sem agents/tools)
- Domain class: `app/domains/recruitment_campaign/domain.py:28` (142 linhas)
- 4 actions: `create_campaign`, `get_campaign_progress`, `advance_campaign`, `list_campaigns`
- Sem `agents/`, sem `tools/` — handlers dispersos

#### P2-4: `company_settings` import_benefits_from_data sem consent validation
- `tools/import_tools.py:318-425` — importa benefícios de file_data, sem checar consent
- NEW Mar/2026 — tools ainda não em wrapper canonical

#### P2-5: ExpandableAIPrompt em frontend mas não em backend recruiter_assistant
- Frontend: `plataforma-lia/src/components/expandable-ai-prompt.tsx` ✓
- Backend: nada equivalente em `app/domains/recruiter_assistant/` — possível inconsistência arquitetural

#### P2-6: Auth Enforcement com synthetic dev mode
- `app/middleware/auth_enforcement.py:208-338` — `_set_company_id_from_jwt` canonical
- Linha 293-296: synthetic dev mode (`DEV_MODE`)
- Risco se acidentalmente shipped em produção

---

## Detalhamento por lote

### Lote 1 — Job Stack (4 domains)

| Domain | LOC | Agents | Tools | Tests | Status | Notas SSH |
|---|---|---|---|---|---|---|
| `job_creation` | 443 | 0 (terceirizado a job_management) | 0 | 39 | ✅ WIRED | 14 services, compliance.py com `mask_pii_for_llm()` + FairnessGuard |
| `job_management` | 104 | **1 (WizardReActAgent canonical)** | 100+ via registry | **0** ⚠ | ✅ WIRED + P1-5 | 29 actions, FairnessGuard ativo (`_fairness_guard = FairnessGuard()`), 6 agent files, 11 services |
| `recruitment_campaign` | 142 | 0 | 0 | 4 mínimos | ⚠ PARTIAL P2-3 | Apenas 4 actions, skeleton |
| `offer` | 164 | 1 placeholder | 6 | 16 | ⚠ P0-3 | high_impact=True mas SEM FairnessGuard. 7 tools files |

**Tools `job_management` com FairnessGuard ativo (auditadas via SSH):**
- `create_job`, `update_job`, `pause_job`, `close_job`, `publish_job` — todos `tool_handler` decorados em `wizard_tool_registry.py`
- Pre-check fairness via `_fairness_pre_check()` em `wizard_react_agent.py:151-156`

---

### Lote 2 — Candidate Stack (6 domains)

| Domain | LOC | Agents | Tools | Highlights SSH |
|---|---|---|---|---|
| `cv_screening` | 747 | 1 (PipelineReActAgent) | **15** | WSI service 8 arquivos, FairnessGuard em 5 services, PII via `strip_pii_for_llm_prompt()`, `@_traceable` LangSmith em `layer2_extractor.py:184` |
| `pipeline` (`pipeline_transition`) | 418 | **4** (base+3 specialized) | **20** | HITL gates múltiplos: `pipeline_transition_agent.py:145-255`, `pipeline_tool_registry.py:1349` (`requires_human_review=True`) |
| `interview_scheduling` | 651 | LangGraph `interview_graph` | LG nodes | 8 services/repos (Calendar, transcript) |
| `communication` | 596 | 1 (CommunicationReActAgent) | 5+ | **`consent_gate.py:49-138`** canonical fail-closed + audit trail. Multi-canal: Mailgun/Resend/MetaWhatsApp/Twilio/Teams |
| `automation` | 134 | 1 (AutomationReActAgent) | varios | ⚠ P1-1: `pipeline_monitor.py:299` auto_rejection sem HITL |
| `candidate_self_service` (NEW) | 354 | 1 | 4 | Read-only portal + **LGPD Art.20** via `explain_candidate_decision` tool |

**Inegociáveis Lote 2 (validados via SSH):**
| # | Status | Evidência |
|---|---|---|
| #1 WSI Explicável | ✅ | `cv_screening/services/wsi_service/layer2_extractor.py:184 @_traceable` |
| #2 No Auto-Rejection | ⚠ P1-1 | pipeline OK; automation pipeline_monitor falha |
| #3 FairnessGuard 100% | ✅ | 5 services (cv_scoring, eligibility, evaluation, lia_score, personalized_feedback) |
| #4 PII Masking | ✅ (lote) / ❌ (global) | strip_pii_for_llm_prompt + masked_logger; mas P0-1 global 335 violations |
| #5 Consent | ✅ | `consent_gate.py:49-138` fail-closed |
| #6 DSR + LGPD Art.20 | ✅ | `candidate_self_service/tools/explain_candidate_decision.py` |
| #7 Human Override | ⚠ P1-1 | pipeline OK; automation parcial |

---

### Lote 3 — Talent + Sourcing Stack (6 domains)

| Domain | LOC | Agents | Tools | Highlights SSH |
|---|---|---|---|---|
| `sourcing` | 901 | **11 sub-agents** | 30 actions, registry 1464 LOC | Diversity ✅, **Pearch AI ATIVO** (`candidate_search/credits.py:29-30`), Apify GitHub/StackOverflow |
| `recruiter_assistant` | 905 | **7 sub-agents** | registry 62.3 KB (kanban) + 1088 LOC (talent) | JobsManagement, Kanban (4 sub: Action/Insight/Search/base), TalentFunnel, Talent. Prompt 1 + 4 |
| `talent_pool` | 592 | 1 (TalentPoolReActAgent) | tool registry | LangGraphReActBase + EnhancedAgentMixin |
| `analytics` | 154 | 1 (AnalyticsReActAgent) | tool registry | KPI/reports, integrado no funil |
| `agent_studio` | 982 | runtime centralizado | `custom_agent_runtime.py` 22.5 KB | Custom agents por tenant, frontend `agent-studio/` |
| `digital_twin` | 511 | 0 (avaliação pura) | — | Pattern correto: domain de avaliação sem ReAct |

**Falsos positivos da 1ª rodada (worktree local) corrigidos via SSH:**
| Doc/1ª rodada disse | SSH 2ª rodada confirmou |
|---|---|
| Pearch AI "DEAD" / "não encontrado" | ✅ ATIVO em `credits.py:29-30` + `_shared.py:22` |
| `check_deprecated_rail_a_tools.py` "missing" | ✅ Presente em `scripts/` |
| `analytics/agents/` vazio | ✅ AnalyticsReActAgent canonical existe |
| Sourcing tinha 4 agents | ✅ 11 sub-agents |
| Recruiter_assistant tinha 6 agents | ✅ 7 sub-agents |

---

### Lote 4 — Compliance + Integrations (3 domains agentic + serviços compartilhados)

#### Domains agentic

| Domain | LOC | Agents | Tools | P0/P1 |
|---|---|---|---|---|
| `hiring_policy` | — | 1 (PolicyReActAgent canonical) | 5 | P2-1 (2 tools sem FairnessGuard invoke), API endpoints OK |
| `ats_integration` | — | 1 (AtsIntegrationReActAgent canonical) | 5 | **P0-2 contribuição** (3 endpoints sem company_id), P2-2 |
| `company_settings` (NEW) | — | 1 (CompanyReActAgent canonical) | 3 | P2-4 (no consent em import_benefits) |

#### Serviços compartilhados (mapa de governança)

| Serviço | File:Line | Cobertura | Status |
|---|---|---|---|
| **FairnessGuard 3-camadas** | `app/shared/compliance/fairness_guard.py:573-1122` | 5 domains direct + herança | ⚠ P1-3 Layer 3 feature-flagged |
| **Guardrails** | `app/shared/compliance/guardrail_repository.py:1-224` | 15 domains | ✅ Active |
| **PII Masking** | `app/shared/pii_masking.py` | All | 🔴 P0-1 (335+ violations em logs) |
| **Feature Flag Service** | `app/shared/governance/feature_flag_service.py:23-339` | All | ✅ HITL gate active (line 183) |
| **Agent Monitoring** | `app/shared/governance/agent_monitoring_service.py` | All agents | ✅ LangSmith |
| **Circuit Breaker** | `app/shared/resilience/circuit_breaker.py:87-327` | ATS (Gupy/Pandape/Merge/Rails) | ✅ 4 named circuits |
| **Token Budget** | `app/shared/observability/token_budget_service.py` | LLM | ✅ |
| **Model Drift** | `app/shared/observability/model_drift_service.py` | LLM responses | ✅ Active (347 LOC) |
| **LGPD/DSR** | `app/domains/lgpd/*` (99 files) | LGPD domain (não-agentic) | ✅ Erasure ativo |
| **Auth Enforcement** | `app/middleware/auth_enforcement.py:208-338` | All routes | ⚠ P2-6 (synthetic dev mode line 293-296) |

**Total compliance LOC:** ~3.367 linhas em `app/shared/compliance/`

#### Sensores executados via SSH (output real, não inferido)

```
✅ check_agent_compliance: 7 violations / 3 agents (P1-2)
✅ check_no_pii_in_logs: 335+ violations / 15+ files (P0-1)
✅ check_company_id_in_routes: 20+ endpoints / multi-tenancy gap (P0-2)
✅ check_no_select_in_services: 0 violations (370 service files clean)
✅ check_no_sql_inline_in_services: 0 violations (370 service files clean)
✅ check_plan_execute_wiring: wired, 28 patterns, 52 task_ids
```

---

## Inegociáveis — quadro consolidado pós Fase 1

| # | Inegociável | Status agregado | Evidências (SSH-validated) |
|---|---|---|---|
| 1 | **WSI explicável** | ✅ PASS | `wsi_observability.py` 446 LOC + `layer2_extractor.py:184 @_traceable` LangSmith |
| 2 | **No auto-rejection** | ⚠ P1-1 | pipeline OK (5 HITL gates); automation pipeline_monitor falha |
| 3 | **FairnessGuard 100%** | ⚠ P1-3 + P0-3 | 5 services cv_screening + hiring_policy OK; Layer 3 feature-flagged; offer SEM FG |
| 4 | **PII masking 100%** | 🔴 P0-1 | 335+ violations sensor; `pii_masking.py` canonical existe mas não 100% aplicado |
| 5 | **Consent management** | ✅ PASS | `consent_gate.py:49-138` fail-closed, granular per-channel |
| 6 | **DSR 15d + LGPD Art.20** | ✅ PASS | `app/domains/lgpd/` 99 files + `candidate_self_service.explain_candidate_decision` |
| 7 | **Human override** | ⚠ P1-4 | HITL exists para feature flags, parcial em domain tools (offer/automation) |
| 8 | **WCAG 2.1 AA** | 🚫 N/A Fase 1 | Frontend audit deferido (Fase 2 smoke test) |

---

## Comparação 1ª rodada (worktree local) vs 2ª rodada (Replit SSH)

A 1ª rodada de agents leu o worktree local (branch `claude/vibrant-montalcini-654139`, sem os 50+ commits Sprint B). Várias premissas foram corrigidas:

| Achado 1ª rodada (descartado) | Realidade SSH 2ª rodada |
|---|---|
| ❌ "offer domain não existe" | ✅ Existe — 7 tools + 16 testes (mas P0-3 sem FairnessGuard) |
| ❌ "Plan & Execute dead function" | ✅ Wired (sensor confirma 28 patterns + 52 task_ids) |
| ❌ "B10/C9/H4/A2 não implementados" | ✅ Todos wired (validado em Fase 0) |
| ❌ "PII import quebrado em job_creation" | ✅ Não detectado em SSH atual; provavelmente fixado |
| ❌ "pipeline sem HITL para moves críticos" | ✅ pipeline tem 5 HITL gates explícitos |
| ❌ "Pearch AI dead" | ✅ ATIVO em `credits.py:29-30` |
| ❌ "Sensor check_deprecated_rail_a_tools missing" | ✅ Presente |
| ❌ "Analytics agents vazio" | ✅ AnalyticsReActAgent canonical |

---

## Cobertura da auditoria

- ✅ **19 domains agentic** auditados (100%)
- ✅ **~50 sub-agents** mapeados com file:line
- ✅ **~120 tools** identificadas em registries
- ✅ **6 sensores** executados com output real
- ✅ **8 falsos positivos** descartados via cross-check SSH
- ✅ **3 P0 + 5 P1 + 6 P2** com evidência SSH

**Cobertura de dimensões (14 do playbook):**
- D1-D7 (estruturais): coverage 100% para todos 19 domains
- D8-D11 (qualidade): cobertos parcialmente — D8/D11 deferidos para Fase 2 (comportamental)
- D12-D14 (governança/segurança/perf): cobertos via sensores compliance
- WCAG (D3 acessibilidade) deferido para Fase 2 (Preview MCP frontend)

---

## Próximos passos

**Fase 2 — Auditoria comportamental (smoke tests híbridos):**
- Backend: cURL/Python via SSH para cada contexto de prompt × happy path
- Frontend: Claude Preview MCP — kanban, candidate-page, agent-studio, funil-de-talentos
- Validação SLA P95 < 5s
- Output: `02-SMOKE_TESTS_RESULTS.md`

**Fase 3 — Auditoria de governança:**
- 13 Crenças + 8 Inegociáveis + 18 Production Readiness × evidência
- FairnessGuard 3 camadas — auditar especificamente o Layer 3 feature-flagged
- LGPD/EU AI Act risk consolidado
- Output: `03-GOVERNANCE_REPORT.md`

**Fase 4 — Roadmap consolidado:**
- Cruzar achados Fases 1-3 + priorização
- Substituir `PLANO_SPRINTS_Y1_Y5.md` por roadmap baseado em evidência SSH
- Output: `04-ROADMAP_PRIORIZADO.md`

---

**Fim do 01-MATRIZ_CAPACIDADE_CODIGO.md.**
