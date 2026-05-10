# 00 — CAPACIDADES LIVE — Plataforma LIA WeDOTalent

> **CANONICAL VIVO.** Última auditoria: **2026-05-10**. Auditor: Paulo + Claude (sessão `vibrant-montalcini-654139`).
> Branch Replit: `feat/benefits-prv-canonical` HEAD `7bea40531` (`fix(p1-compliance): DPO lookup + LiaOpinion cascade docs + EU AI Act Art.13 disclosure`)
> **Substitui (parcialmente):** `mapeamento_capacidades_prompts_lia.md` (será mantido como referência arquivada após Fase 4).
> **Próximo doc:** `00b-INVENTARIO_DOCUMENTAL.md` (higiene Fase 0.5) → `01-MATRIZ_CAPACIDADE_CODIGO.md` (Fase 1).

---

## Sumário executivo

A plataforma LIA é hoje um sistema agentic-IA multi-domínio, multi-tenant, com governança de compliance ativa em produção. Tamanho:

| Camada | Métrica |
|---|---|
| Backend | ~71k linhas Python (`lia-agent-system/app/`) |
| Frontend | ~300k linhas TS/TSX (`plataforma-lia/src/`) |
| Domains agentic registrados | **19** (não 16 como dizia auditoria de Mar/2026) |
| Sensores de governança ativos | **36** (`scripts/check_*.py`) |
| Endpoints API | 311 routers FastAPI em `/v1/` |
| Migrations Alembic | 130 |
| Tests backend | 728 (passing/total) |
| Tests frontend | 549 |
| ADR-001 violations | **0** (370 service files clean) |
| Compliance ADR (LIA-C01) | **19/19 domains** call `super().get_system_prompt()` |
| Plan & Execute wiring | ✅ wired (28 PlanPatterns, 52 task_id entries, 5+ templates) |

Status macro: **base canonical madura, governança ativa, gaps remanescentes localizados (não estruturais)**. A maioria das auditorias antigas (de Dez/2024 a Mar/2026) lista TODOs já fechados; o trabalho agora é mapear gaps reais residuais — não reconstruir o que existe.

---

## Seção 1 — Os 4 contextos de prompt LIA (atualizado)

Fonte original: `mapeamento_capacidades_prompts_lia.md` (Mar/2026).
Atualização: tools confirmadas via `grep` em `app/domains/*/agents/*tool_registry*.py` no Replit branch ativa.

### Contexto 1 — Flutuante / Global (`recruiter_assistant` domain, scope `GLOBAL`)
Tools confirmadas:
- `get_company_config`
- `generate_report`
- `schedule_report`
- `capture_wizard_feedback`

Equivalente v5: `autonomous` domain (73+ tools) — gap de cobertura conhecido, pendente análise de quais tools v5 deveriam ser portadas (Fase 1 vai mapear).

### Contexto 2 — Tabela de Vagas (`job_management`, scope `JOB_TABLE`)
13 tools confirmadas:
- Query: `search_jobs`, `get_job_details`, `get_pipeline_stats`, `search_salary_benchmark`, `get_intelligent_salary`, `get_intelligent_skills`, `get_job_suggestions`, `validate_job_fields`
- Write: `create_job`, **`update_job`** (B10 — confirmado wired em `app/api/v1/chat.py:116`, `app/domains/job_management/actions.py:10`, tool em `job_tools.py:718`), `publish_job`, `archive_job`, `clone_job`

### Contexto 3 — Dentro da Vaga / Kanban (`cv_screening` + `pipeline_transition` + `interview_scheduling` + `communication`, scope `IN_JOB`)
6 tools confirmadas:
- `search_candidates`, `move_candidate_stage`, `send_communication`, `schedule_interview`, `wsi_screening`, `get_interview_details`

### Contexto 4 — Funil de Talentos (`sourcing` + `analytics` + `recruiter_assistant`, scope `TALENT_FUNNEL`)
9 tools confirmadas:
- `search_talents`, `get_candidate_profile`, **`create_shortlist`** (C9 — confirmado em `app/domains/recruiter_assistant/agents/talent_tool_registry.py:914`, com `SafetyCategory.PIPELINE_MOVE`), `score_sourcing_candidate`, `bulk_action_talent`, `export_candidates`, `get_talent_analytics`, `generate_insights`, `contact_candidate`

### Domínios canonical detectados além dos 4 prompts
Não estavam mapeados no doc original mas são reais e registrados:
- `agent_studio` — criação de agents customizados
- `digital_twin` — twin de avaliação
- `recruitment_campaign` — multi-stage campaigns
- `talent_pool` — pool de candidatos passivos
- `job_creation` (separado de `job_management`)
- `company_settings` ⭐ NOVO desde Mar/2026
- `candidate_self_service` ⭐ NOVO desde Mar/2026
- `offer` ⭐ NOVO desde Mar/2026
- `automation` (tasks, reminders, notes)
- `ats_integration` (sync com ATS externos)
- `hiring_policy` (FairnessGuard advisory) — H4 mapping confirmado em `_DOMAIN_TO_AGENT` (`app/domains/workflow.py:621`) + `app/shared/messaging/dispatchers.py:37`

### UI Actions (modais via chat — A2 confirmado wired)
Modais reais expostos via `ui_action`:
- `open_communication_modal` (`orchestrated_talent_chat.py:128`)
- `open_schedule_modal` (`:129`)
- `open_screening_modal` (`:130`)
- `open_modal` genérico via `rail_a_capability_check.py:21`
- Por etapa kanban (`pipeline_service.py:287-295`): `interview_scheduling`, `feedback`, `stage_advance`, `offer`, `contact`

---

## Seção 2 — Fases já completas com evidência

Cross-check `PLANO_IMPLEMENTACAO_STATUS.md` × git log Replit. Cada linha aponta para commit hash que prova a entrega.

### Sprint Pre-flight + Sprints 2-9 + Q2 ADR-001 cleanup
| Bloco | Status | Commit hash | Tag |
|---|---|---|---|
| Pre-flight P0 (governance + tenant) | ✅ | `e01105f54` | `fix(governance,tenant): Sprint Pre-flight — close pre-existing P0 debt` |
| Sprint 2 Phase 1 (PromptComposer canonical) | ✅ | `d91c68fd4` | `feat(prompts): Sprint 2 Phase 1 — PromptComposer canonical + candidate migrated` |
| Sprint 2 Phase 2 (13 agents migrated) | ✅ | `c9baec92e` | `feat(prompts): 13 agents migrated, 14/14 ADOPTED, sensor BLOCKING` |
| Sprint 2 Phase 3.1 (P0 candidate identity-leak) | ✅ | `bd69fe0e9` | `fix(prompts): P0 candidate identity-leak + golden snapshots` |
| Sprint 2 Phase 3.3 (LGPD/fairness blocks) | ✅ | `e9cfc0e25` | `fix(compliance): reactivate LGPD/fairness blocks (Audit M closure)` |
| Sprint 2 Phase 3.4 (CDP cleanup + tenant gate) | ✅ | `c432d7456` | `refactor(domains): delete 18 dead CDP overrides + annotate 8 require_company=False` |
| Sprint 2 Phase 4 (runtime placeholder) | ✅ | `86da990ba` | `fix(prompts): runtime placeholder substitution (Audit G)` |
| Sprint 3 (RuntimeContext canonical) | ✅ | `574661c2c` | `feat(governance): RuntimeContext canonical (ADR-029 §3)` |
| Sprint 4A (RLS candidates + sensor) | ✅ | `74ba4ba9d` | `feat(rls): RLS canonical for candidates + RLS coverage sensor` |
| Sprint 4B (FairnessGuard fail-fast) | ✅ | `4aeb3c819` | `feat(compliance): FairnessGuard fail-fast init + LGPD runbook` |
| Sprint 5.1 (ADR-001 sensors) | ✅ | `4c4162e04` | `feat(governance): ADR-001 sensors (no SQL/select in services)` |
| Sprint 5.2 (RLS T1 LGPD) | ✅ | `5b1c15efc` | `feat(rls): RLS for 6 T1 LGPD tables (UUID pattern)` |
| Sprint 5.3 (RLS T2 LGPD/Compliance) | ✅ | `c121c4975` | `feat(rls): RLS for 14 T2 tables` |
| Sprint 5.4 (3 zero-repo domains) | ✅ | `aa6c353fe` | `feat(repository): scaffold 3 zero-repo domains + canonical example` |
| Sprint 5.7 (RLS T3 batch 20 tables) | ✅ | `53b1d95af` | `feat(rls): RLS T3 batch (20 tables)` |
| Sprint 5.8 (InterviewRepository) | ✅ | `df1faf6c9` | `feat(repository): InterviewRepository (ADR-001 example)` |
| Sprint 5.9 (RLS T4-T8, mig 122-126) | ✅ | `efec49c62` | `feat(rls): RLS T4-T8 close 76-table multi-tenancy gap` |
| Sprint Q2 ADR-001 (vacancy_search canonical) | ✅ | `8faecb597` | `refactor(adr-001): Sprint Q2 ADR-001 cleanup` |
| Sprint 6 (raw SQL → repos) | ✅ | `271930b44` | `refactor(adr-001): Sprint 6 — extract 19 raw SQL queries` |
| Sprint 7 (top-5 select offenders) | ✅ | `228dae85f` | `refactor(adr-001): Sprint 7 — promote sensor 1 to blocking` |
| Sprint 8 (337 select() refactored) | ✅ | `75ad13afb` | `refactor(adr-001): Sprint 8 — 5 parallel agents refactor 337 select() violations` |
| Sprint 8 batch 2 (long-tail, sensor BLOCKING) | ✅ | `65b033556` | `refactor(adr-001): close 56 long-tail violations + sensor 2 BLOCKING` |
| Sprint 9 (P1 multi-tenancy) | ✅ | `324817bfe` | `fix(adr-001): Sprint 9 — P1 multi-tenancy bug + activate CI` |
| Wave 4 (R-043+R-044+R-045+R-049+R-051+R-052) | ✅ | `b1dfefdad` | `Wave 4: directory hygiene + config` |
| R-014b (react_loop → tool_adapter) | ✅ | `b7770a28e` | `[R-014b] complete react_loop → tool_adapter migration across all 14 domains` |
| R-017 (lia_models completeness sensor + 55 imports) | ✅ | `af2cf97c1` | `[R-017] wire lia_models completeness sensor to CI` |

### Sprint B (Sprint atual — Mai 2026)
| Bloco | Status | Commit hash | Tag |
|---|---|---|---|
| B Phase 1 (record_jd + PII redactor + repo multi-tenancy) | ✅ | `25710a1b0` | `feat(sprint-b-phase1): wire record_jd on publish + PII redactor` |
| B Phase 2 (`_classify_questions_with_taxonomy`) | ✅ | `4c4340122` | `feat(sprint-b-phase2): wire in generate_questions (W1)` |
| B Phase 3 (D2 toggle + ADR-LGPD-001 docstring) | ✅ | `91497122c` | `feat(sprint-b-phase3): default bigfive_department_history toggle ON` |
| B Phase 4 (C2 audit log + C3 bias snapshot) | ✅ | `87cb8fbcd` | `feat(sprint-b-phase4): wire AuditService.log_action + push BiasAuditSnapshot per hire` |
| B P0-1 (IDOR cross-tenant fix) | ✅ | `8c9e6c6b1` | `fix(sprint-b-p0-1): close IDOR cross-tenant in set_feature_flag` |
| B P0-2 (single bias snapshot per hire) | ✅ | `c34417f5a` | `fix(sprint-b-p0-2): single bias_audit snapshot per hire` |
| B P0-3 (ADR-LGPD-001 ANPD + Art.12 §1 + EU AI Act) | ✅ | `bb255d1b4` | `fix(sprint-b-p0-3): harden ADR-LGPD-001 with ANPD precedent` |
| B P1-1 (record_jd_if_enabled hoisted) | ✅ | `7270adca4` | `refactor(sprint-b-p1-1): hoist into JdSimilarService` |
| B P1-9 (HITL admin/DPO gate) | ✅ | `a2ab9861a` | `feat(sprint-b-p1-9): HITL gate routes sensitive flag toggles through admin/DPO` |
| B P1-2 (suppress preventive DeprecationWarning) | ✅ | `a11471f0e` | `docs(sprint-b-p1-2)` |
| B P1-batch (idempotency + ALLOWED_TRAITS + PII) | ✅ | `1bd8812f2` | `fix(p1-batch)` |
| B P1-opinion (LiaOpinion ADR-001 + clobber guard) | ✅ | `ffd89215e` | `fix(p1-opinion)` |
| B P1-concurrency (SELECT FOR UPDATE + is_current) | ✅ | `d50582dab` | `fix(p1-concurrency)` |
| B P1-compliance (DPO lookup + EU AI Act Art.13) | ✅ | `7bea40531` | **HEAD ATUAL** |
| Phase 2.5 (OCEAN traits emission + record_hire) | ✅ | `324daf5c2` + `758fe02db` | `feat(phase-2-5): persist LiaOpinion with ocean_traits` |
| Phase B close (/reject endpoint + sweep) | ✅ | `057268490` | `feat(phase-b-close): /reject + sweep_expired_approvals` |

### Cross-check com docs antigos
| Doc original | Status reportado | Realidade hoje |
|---|---|---|
| `PENDENTES_IA.md` (2024-12-21) | "Plan & Execute pendente" | ✅ Wired (sensor `check_plan_execute_wiring.py` GREEN) |
| `PENDENTES_IA.md` Ag.0 Orchestrator "estado multi-turn" | "🟡 Planejado" | ✅ Implementado (chat_session_state, ContextAdapter) |
| `PENDENTES_IA.md` Ag.1 "JD generation" | "🟡 Planejado" | ✅ Implementado (`jd-generation`, `jd-import` endpoints) |
| `PENDENTES_IA.md` Ag.3 "OCR PDF/DOCX" | "🟡 Planejado" | ⚠ A validar Fase 1 D11 |
| `ANALISE-GAPS-COMPLETA.md` (2025-12-20) | "FairnessGuard parcial" | ✅ 3 camadas ativas (`compliance_base.py:LIA-C01`) |
| `AUDITORIA-FUNCIONALIDADES.md` (2026-03-03) | "ADR-001 em progresso" | ✅ 0 violations (Sprint 8 batch 2) |
| `PLANO_SPRINTS_Y1_Y5.md` D4 "bias detection" | "TODO" | ✅ `BiasAuditSnapshot` per hire (Sprint B Phase 4) |
| `PLANO_SPRINTS_Y1_Y5.md` C2 "audit trail interview" | "TODO" | ✅ `AuditService.log_action` (Sprint B Phase 4) |
| Plano Sprint Lia anterior (sessão atual) "B10/C9/H4/A2" | "Sprint 2 fix" | ✅ Todos já implementados |
| Plano Sprint Lia anterior "Plan & Execute wiring" | "Sprint 1 fix" | ✅ Wired há ≥1 Sprint |

---

## Seção 3 — 19 Domains Agentic + status compliance

Lista canonical do `app/domains/registry.py` cross-check com `@register_domain` decorators. Sensor `check_domain_prompt_super` confirma 19/19 herdam `ComplianceDomainPrompt` (LIA-C01 enforcement).

| # | Domain ID | Domain class file | LIA-C01 (super().get_system_prompt) | ReAct Agent canonical |
|---|---|---|---|---|
| 1 | `sourcing` | `sourcing/domain.py:36` | ✅ | `sourcing_react_agent.py` (+ 9 specialist agents) |
| 2 | `job_management` | `job_management/domain.py:27` | ✅ | `wizard_react_agent.py` |
| 3 | `cv_screening` | `cv_screening/domain.py:27` | ✅ | `pipeline_react_agent.py` |
| 4 | `communication` | `communication/domain.py:26` | ✅ | `communication_react_agent.py` |
| 5 | `analytics` | `analytics/domain.py:26` | ✅ | `analytics_react_agent.py` |
| 6 | `interview_scheduling` | `interview_scheduling/domain.py:36` | ✅ | (scheduling tools, lightweight) |
| 7 | `ats_integration` | `ats_integration/domain.py:27` | ✅ | `ats_integration_react_agent.py` |
| 8 | `automation` | `automation/domain.py:27` | ✅ | `automation_react_agent.py` |
| 9 | `recruiter_assistant` | `recruiter_assistant/domain.py:28` | ✅ | 7 specialist agents |
| 10 | `pipeline` (`pipeline_transition`) | `pipeline/domain.py:94` | ✅ | 4 sub-agents (action/context/decision/transition) |
| 11 | `hiring_policy` | `hiring_policy/domain.py:103` | ✅ | `policy_react_agent.py` |
| 12 | `agent_studio` | `agent_studio/domain.py:21` | ✅ | (lightweight) |
| 13 | `digital_twin` | `digital_twin/domain.py:26` | ✅ | `autonomous_react_agent.py` (micro) |
| 14 | `recruitment_campaign` | `recruitment_campaign/domain.py:27` | ✅ | (micro) |
| 15 | `talent_pool` | `talent_pool/domain.py:27` | ✅ | `talent_pool_agent.py` |
| 16 | `job_creation` | `job_creation/domain.py:43` | ✅ | (compartilha wizard com job_management) |
| 17 | **`company_settings`** ⭐ | `company_settings/domain.py:78` | ✅ | (NEW — não estava nas auditorias antigas) |
| 18 | **`candidate_self_service`** ⭐ | `candidate_self_service/domain.py:60` | ✅ | (NEW) |
| 19 | **`offer`** ⭐ | `offer/domain.py:26` | ✅ | (NEW — relacionado a Phase 2.5/Sprint B) |

> **Insight:** as 3 domains marcadas ⭐ não aparecem em **nenhum** dos 27 docs de análise antigos. Confirma que docs estão >2 meses desatualizados.

### Serviços não-agentic (suporte)
| Domain | Files | Responsabilidade |
|---|---|---|
| `ai` | 29 | LLM service, response cache, prompt management |
| `company` | 31 | Company settings, BigFive profiles repo |
| `candidates` | 14 | Candidate CRUD, comparison |
| `recruitment` | 24 | Recruitment data, workflow state |
| `billing` | 6 | Billing engine, invoicing |
| `credits` | 7 | Credit/token tracking |
| `integrations_hub` | 10 | Slack/Microsoft management |
| `lgpd` | 11 | DSR, erasure workflows |
| `voice` | 9 | Voice screening, Twilio |

---

## Seção 4 — 36 Sensores ativos — STATUS REAL hoje

Run completo via `python scripts/check_*.py` em `2026-05-10`. Cada linha = sensor × estado.

### ✅ Sensores GREEN (22)
| Sensor | Output |
|---|---|
| `check_deprecated_rail_a_tools` | 22 intents, 0 @deprecated functions |
| `check_domain_prompt_super` | 19/19 domains call super() |
| `check_init_completeness` | 126 model files imported |
| `check_no_cid_empty_escape` | 2077 files scanned, 0 escapes |
| `check_no_dev_fallback_tokens` | OK |
| `check_no_observability_services_dup` | 15+111, sem dups |
| `check_no_react_loop_import_in_agents` | 3270 files OK |
| `check_no_select_in_services` | 370 service files, 0 hits ADR-001 |
| `check_no_sql_inline_in_services` | 370 service files, 0 raw SQL ADR-001 |
| `check_no_tenant_in_tool_schemas` | 64 tool files, 0 leaks ADR-029 |
| `check_plan_execute_wiring` | wired, 28 PlanPatterns, 52 task_id entries |
| `check_prompt_composer_uniformity` | 14/14 ADOPTED, 0 LEGACY |
| `check_pyproject_libs_consistency` | 7 libs OK |
| `check_rails_owned_writes` | OK ADR-001-EXEMPT |
| `check_shim_sla` | 139 shim files, no expired |
| `check_tool_authoring_surface` | initialize_tools allowed (ADR-016) |
| `check_tool_governance` | OK G-GOV |
| `check_tool_output_schemas` | todos ToolDefinition declaram output_schema |
| `check_no_devmode_in_prod_env` | OK |

### ⚠ Sensores WARN-ONLY (1)
| Sensor | Output |
|---|---|
| `check_table_has_rls_policy` | 2 GAPs: `workforce_entries`, `wsi_question_effectiveness` (WARN-ONLY até Sprint 5+) |

### ❌ Sensores com VIOLATIONS (13) — vão pro roadmap
| Sensor | Severity proposta | Resumo |
|---|---|---|
| `check_no_pii_in_logs` | **P0 LGPD** | PII em logs detectado — viola Inegociável #4 |
| `check_company_id_in_routes` | **P0 multi-tenancy** | 3 endpoints sem `_require_company_id`: `stages_substatus.py:120`, `:146`, `stages_transition.py:266` |
| `check_no_direct_contextvar_set` | **P0 R-008** | Direct `_current_company_id.set()` fora de canonical helpers |
| `check_agent_compliance` | **P1** | Agentes sem FairnessGuard explícito ou sem PII redaction |
| `check_no_langchain_tool_decorator` | **P1** | `policy_tools.py:9` usa `from langchain_core.tools import tool` (deveria usar `tool_handler`) |
| `check_no_legacy_tool_decorator` | **P1** | `policy_tools.py` legacy decorator |
| `check_tenant_db` | **P1** | Endpoints sem `Depends(get_tenant_db)` |
| `check_response_models` | **P2 ADR-005** | Endpoints sem `response_model=` |
| `check_no_sql_in_controllers` | **P2** | 134 legacy controllers (migration ativa, conhecido) |
| `check_llm_factory_enforcement` | **P2** | 4 violations (allowlist gestionada) |
| `check_llm_imports` | **P2** | Direct anthropic imports (e.g. `agent_quality_evaluator.py:166` — comment justifica mock) |
| `check_no_getattr_on_models` | **P2 G6** | `getattr(message, "company_id", None)` — usar acesso direto |
| `check_duplicate_indexes` | **P2** | OfferProposal `status` index colide com `__table_args__` |
| `check_forbidden_imports` | **P2 ADR-012** | `from libs.messaging.lia_messaging.X` deveria ser `from lia_messaging.X` |
| `check_require_company_exemptions` | **P3 audit** | 7 em código vs 19 doc — sync gap |
| `check_no_silent_swallow` | **P3** | 29 silent swallows — usar logger.debug exc_info |

> **Insight crítico:** 3 violations P0 (PII em logs, multi-tenancy gap em 3 endpoints, ContextVar direct set) — **violam Inegociáveis #3, #4 e R-008**. Vão para topo do roadmap (Fase 4).

---

## Seção 5 — Inventário documental WeDO/

Cross-ref para `00b-INVENTARIO_DOCUMENTAL.md` (Fase 0.5). Aqui só o resumo agregado:

| Categoria | Count | Ação |
|---|---|---|
| **CANONICAL VIVO** | 9 | Manter, atualizar in-place + header cross-ref |
| **REFERÊNCIA PERMANENTE** | 7 | Manter, framework atemporal |
| **PLANO SUBSTITUÍVEL** | 10 | Arquivar APÓS Fase 4 produzir substituto |
| **STATUS HISTÓRICO** | 11 | Arquivar AGORA na Fase 0.5 |
| **DUPLICADO** | 1 | Arquivar duplicata, manter UPPERCASE |
| **TOTAL** | **38** docs em `WeDO/analises/` + `WeDO/planos/` |

Detalhe doc-a-doc, decisões de archive, justificativa: ver `00b-INVENTARIO_DOCUMENTAL.md`.

---

## Seção 6 — Glossário atualizado (deltas)

Termos do `mapeamento_capacidades_prompts_lia.md` Seção 10 que mudaram desde Mar/2026:

| Termo | Definição original | Atualização hoje |
|---|---|---|
| **Plan & Execute** | "TaskPlanner+PlanDetector+PlanExecutor planejados" | ✅ wired em `main_orchestrator.py:443/476/480`, 28 patterns, 52 task_ids, 5+ templates (`schedule_interviews_batch`, `batch_rejection_feedback`, `advance_top_candidates`, `close_stale_jobs`, `onboarding_pipeline`) |
| **CrewPlanExecutor** | (não existia) | Novo. Para delegação de tasks paralelos via crew pattern (`shared/execution/plan_executor.py:399`) |
| **PromptComposer** | (não canonical) | Canonical desde Sprint 2 Phase 1 (commit `d91c68fd4`). 14/14 react_agents adopted, sensor BLOCKING |
| **RuntimeContext** | (não existia) | Sprint 3 ADR-029 §3 (`574661c2c`). Typed dataclass com fields canonical de tenant context |
| **ADR-LGPD-001** | (não existia) | Sprint B P0-3 (`bb255d1b4`). Anonimização de agregados (BigFive dept) — citado em CLAUDE.md global |
| **OCEAN traits emission** | (não existia) | Phase 2.5 (`324daf5c2`). Pipeline OCEAN trait → record_hire → flip ADR-LGPD-001 sentinels |
| **Phase B approval workflow** | (não existia) | Sprint atual. Second-actor approval para sensitive feature flags + /reject endpoint + expiry sweep |
| **EU AI Act Art.13 disclosure** | (não existia) | HEAD atual (`7bea40531`). Disclosure em LiaOpinion docs |

### Terminologia confirmada vivendo
- **DEFs canonical:** `ComplianceDomainPrompt` (`compliance_base.py`), `EnhancedAgentMixin`, `ToolDefinition`, `LangGraphReActBase`, `tool_handler`, `with_runtime_context`
- **HITL surfaces:** approval workflow, DPO gate (Sprint B P1-9), human override em decisões high-impact
- **Compliance gates:** LIA-C01 (super().get_system_prompt obrigatório), R-008 (no direct ContextVar set), R-014b (no react_loop in agents)

---

## Seção 7 — Próximos passos / handoff para Fase 0.5+

Esta Fase 0 produziu fonte única atualizada. Fase 0.5 (próxima) faz higiene documental:

1. Arquivar 11 docs STATUS HISTÓRICO + 1 DUPLICADO (12 movs imediatos)
2. Adicionar header `> ARQUIVADO em 2026-05-10` + link cross-ref nos 12
3. Adicionar header `> CANONICAL VIVO. Última auditoria 2026-05-10` nos 9 canonical vivos
4. Criar `WeDO/_archive/2026-05-10/` (local + replicar no Replit se aplicável)
5. Criar `WeDO/README.md` se não existir, com índice atual
6. Output: `00b-INVENTARIO_DOCUMENTAL.md` com decisão linha-a-linha + antes/depois

Após Fase 0.5 → Fase 1 audita os 19 domains × 14 dimensões via 4 Explore agents paralelos.

---

## Anexo A — Lista de docs WeDO/ por categoria (preview)

### CANONICAL VIVO (9)
1. `mapeamento_capacidades_prompts_lia.md` (será atualizado em Fase 4)
2. `PLANO_IMPLEMENTACAO_STATUS.md` (registro fases A-K, X1-X5, SEG, AUD)
3. `ANALISE_COMPARATIVA_V5_vs_LIA.md` (19/03/2026)
4. `diagnostico_arquitetura_codigo_lia_vs_v5.md` (Mar/2026)
5. `relatorio_capacidades_prompts_lia.md` (versão expandida 6.609 linhas)
6. `Paralelo_LIA_vs_V5_Arquitetura_IA.md`
7. `RELATORIO_AUDITORIA_LIA.md` (15/03/2026)
8. `mapa_inteligencia_lia_completo.md`
9. `AUDITORIA_TECNICA_EXECUCAO.md` (28/02/2026)

### REFERÊNCIA PERMANENTE (7)
1. `PLAYBOOK_AUDITORIA_PROFUNDA.md` (3171 linhas — framework 14-dim+12-dim+13-Crenças)
2. `ANALISE_COMPETITIVA_2026.md`
3. `ANALISE_ESTRATEGICA_CAMADA_INTELIGENCIA.md`
4. `AUDITORIA_GUIA_MIGRACAO.md`
5. `COMPETITIVE_ANALYSIS_AI_RECRUITING_AGENTS.md`
6. `NLP_CLUSTERING_STRATEGIC_ANALYSIS.md`
7. `analise-viabilidade-saas-stack.md`

### PLANO SUBSTITUÍVEL (10) — arquivar APÓS Fase 4
1. `PLANO_SPRINTS_Y1_Y5.md`
2. `PLANO_IMPLEMENTACAO_GAPS_IA.md`
3. `PLANO_IMPLEMENTACAO_INTELIGENCIA.md`
4. `GUIA_TESTES_ONDA1.md`
5. `MVP_DEVELOPMENT_SPEC.md`
6. `PLANO_ACAO_AGENTES_IA.md`
7. `PLANO_AJUSTE_PROTOTIPO.md`
8. `PLANO_REVISAO_JOB_WIZARD_V2.md`
9. `mvp-alpha-scenarios.md`
10. `plano_implementacao_wizard.md`

### STATUS HISTÓRICO (11) — arquivar AGORA
1. `PENDENTES_IA.md` (21/12/2024)
2. `ANALISE-GAPS-COMPLETA.md` (20/12/2025)
3. `AUDITORIA-FUNCIONALIDADES.md` (03/03/2026)
4. `QA_REPORT_SPRINT_2026-02-28.md`
5. `QA_VACANCY_SYSTEM_REVIEW.md` (20/01/2026)
6. `QA_WIZARD_REVIEW_JAN2026.md`
7. `RELATORIO_TRANSFORMACAO_IA_LIA.md`
8. `feature-impact-remove-block3-eligibility.md`
9. `feature-impact-vacancy-lifecycle.md`
10. `analise-reuniao-alinhamento-06fev2026.md`
11. (1 a confirmar — possível duplicata adicional)

### DUPLICADO (1) — arquivar AGORA
1. `analise-comparativa-v5-vs-lia.md` (kebab-case, 1944 linhas) → manter `ANALISE_COMPARATIVA_V5_vs_LIA.md` (UPPERCASE, 2172 linhas, 19/03/2026)

---

**Fim do 00-CAPACIDADES_LIVE.md.** Próximo: aprovação Paulo → Fase 0.5 → `00b-INVENTARIO_DOCUMENTAL.md`.
