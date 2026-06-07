# LIA AI Layer — Architecture Tree

> **Fonte-da-verdade = código.** This document was produced by walking the real
> filesystem of `lia-agent-system/app/` and `lia-agent-system/libs/agents-core/`
> (not by trusting `ARCHITECTURE.md`, `ARCHITECTURE_TARGET*.md`, or the
> `LIA_REFACTORING_REPORT*.md` files, several of which describe aspirational
> target states). Every path shown below exists in the tree at the time of
> writing. Noise (`__pycache__`, `*.pyc`, test internals, migration internals)
> is collapsed or omitted.

The AI layer is a FastAPI service that turns recruiter/candidate natural-language
input into routed, tenant-scoped, compliance-wrapped agent executions. A request
flows:

```
HTTP / WebSocket / SSE
        │
   app/main.py  ──(lifespan: install_llm_guards → bootstrap → init_db → DomainRegistry → orchestrator → tools)
        │
   middleware (auth_enforcement → rate_limit → idempotency → audit_access → response_envelope)
        │
   app/api/orchestrator_routes.py
        │
   app/orchestrator/  ── routing → execution → (supervisor / guards / action_executor)
        │
   app/domains/<name>/agents/*react_agent.py   (one of the 16 ReActAgents)
        │
   domain tools  ──(via libs/agents-core react loop + tool_handler)──▶ services / repositories
        │
   app/shared/  (llm · compliance · tenant · audit · messaging) wraps every step
```

---

## 1. Entry point & cross-cutting bootstrap

```
lia-agent-system/
├── app/
│   ├── main.py                     # FastAPI app; lifespan boots LLM guards, checkpointer,
│   │                               #   DomainRegistry, orchestrator, tools, schedulers.
│   │                               #   Fail-fast prod guards (Redis enc, LLM keys, tenant-strict).
│   ├── agents_registry.yaml        # Declarative agent registry (name→class_path→model_id),
│   │                               #   hot-reloaded by app/core/agent_registry_watcher.py.
│   ├── api/
│   │   └── orchestrator_routes.py  # initialize_orchestrator() + chat entry routes
│   ├── middleware/                 # auth_enforcement (sets _current_company_id ContextVar),
│   │                               #   rate_limiter, idempotency, request_id,
│   │                               #   audit_access_middleware, response_envelope
│   └── core/                       # config, database, sentry, logging, prompt_version_loader
```

`main.py` imports `app.shared.llm_bootstrap.install_llm_guards` **first** — before
any module instantiates an LLM client — so every SDK call is monkey-patched for
PII stripping, per-tenant credit gating, and audit logging.

---

## 2. Orchestration layer — `app/orchestrator/`

The orchestrator decides *who* handles a request and *how* it executes. Routing
picks a domain/agent; execution runs the agentic loop; guards, supervisor, and
action layers wrap state-changing work.

```
app/orchestrator/
├── routing/
│   ├── cascaded_router.py            # CascadedRouter — multi-tier severity-based routing,
│   │                                 #   Tier 6 ReAct fallback wires app/domains/autonomous
│   ├── fast_router.py                # Cheap heuristic first-pass router
│   ├── llm_cascade.py                # LLM-backed cascade classification
│   ├── domain_mappings.py            # intent/keyword → domain_id maps
│   ├── confirmation_classifier.py    # PT-BR natural confirmation detection ("sim", "vamos")
│   ├── job_creation_disambiguator.py # detect_job_creation — composite-phrase guard so
│   │                                 #   Plan&Execute NEVER creates a job (wizard-only)
│   ├── post_wizard_continuation.py   # conversational continuation after wizard terminal stage
│   └── pe_add_to_vacancy_continuation.py
├── execution/
│   ├── main_orchestrator.py          # MainOrchestrator — top-level execution coordinator
│   ├── agentic_loop.py               # ReAct loop driver (defense-in-depth credit gate)
│   ├── task_planner.py               # Plan&Execute planner (LIA_V2_USE_PLAN_SERVICE)
│   ├── state_manager.py              # per-turn execution state
│   ├── pending_action.py             # deferred/HITL action representation
│   └── registry.py                   # execution-level registry
├── supervisor/
│   └── handoff_tools.py              # CrewAI-style supervisor pre-graph handoff tools
├── action_executor/
│   ├── executor.py                   # ActionExecutorService — closed-loop cross-chat action exec
│   ├── action_types.py               # action enum/types
│   ├── intents_config.py             # intent→action config
│   └── utils.py
├── action_handlers/                  # per-domain action handler implementations
│   ├── candidate_actions.py   job_actions.py        pipeline_actions.py
│   ├── communication_actions.py  interview_actions.py  sourcing_actions.py
│   ├── analytics_actions.py   handler_deps.py       _handler_hooks.py
├── guards/
│   ├── precondition_checker.py       # preconditions before state change
│   ├── rail_a_capability_check.py    # capability gating
│   ├── tenant_budget.py              # per-tenant budget guard
│   └── wizard_state.py               # wizard-state guard
├── context/
│   ├── navigation_intent.py          # useNavigationIntent backend counterpart (T-1165)
│   ├── chat_adapter.py  context_adapter.py  view_context.py
│   ├── intent_types.py  temporal_resolver.py  empty_result_guidance.py
├── heuristics/
│   ├── cv_matching_detector.py
│   └── technical_response_detector.py
├── memory/
│   ├── memory_resolver.py
│   ├── semantic_cache.py
│   └── vector_semantic_cache.py
├── observability/
│   └── _observability.py
├── services/
│   ├── plan_orchestration_service.py # PlanExecutor wiring (real DomainRegistry+DomainWorkflow)
│   ├── policy_gate_service.py        # policy gate before execution
│   ├── fallback_react_service.py     # ReAct fallback service
│   ├── rail_a_hint_override.py  context_type_override.py
├── legacy/
│   ├── orchestrator.py               # pre-refactor orchestrator (still referenced)
│   └── tasting_engine.py
└── config/
    └── domain_routing.yaml           # declarative routing config
```

---

## 3. Core agents — `app/agents/`

A thin layer of non-domain agent primitives. The bulk of agents live inside each
domain (§4); this folder holds shared graph nodes and the policy-setup agent.

```
app/agents/
├── nodes.py                # shared LangGraph node helpers
└── policy_setup_agent.py   # chat-driven policy setup agent (pairs with app/domains/policy)
```

### The 16 canonical ReActAgents

The inventory is sentinel-locked by
`tests/integration/agents/test_tenant_aware_rollout_t_d.py` — adding a 17th
without following the T-D pattern (TenantAwareAgentMixin) breaks the build.

| # | Agent class | Lives in |
|---|---|---|
| 1 | `AnalyticsReActAgent` | `app/domains/analytics/agents/analytics_react_agent.py` |
| 2 | `ATSIntegrationReActAgent` | `app/domains/ats_integration/agents/ats_integration_react_agent.py` |
| 3 | `AutomationReActAgent` | `app/domains/automation/agents/automation_react_agent.py` |
| 4 | `AutonomousReActAgent` | `app/domains/autonomous/agents/autonomous_react_agent.py` |
| 5 | `CommunicationReActAgent` | `app/domains/communication/agents/communication_react_agent.py` |
| 6 | `CompanySettingsReActAgent` | `app/domains/company_settings/agents/company_react_agent.py` |
| 7 | `PipelineReActAgent` | `app/domains/cv_screening/agents/pipeline_react_agent.py` |
| 8 | `PolicyReActAgent` | `app/domains/hiring_policy/agents/policy_react_agent.py` |
| 9 | `JobsManagementReActAgent` | `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` |
| 10 | `KanbanReActAgent` | `app/domains/recruiter_assistant/agents/kanban_react_agent.py` |
| 11 | `TalentFunnelReActAgent` | `app/domains/recruiter_assistant/agents/talent_funnel_react_agent.py` |
| 12 | `SourcingReActAgent` | `app/domains/sourcing/agents/sourcing_react_agent.py` |
| 13 | `TalentPoolReActAgent` | `app/domains/talent_pool/agents/talent_pool_agent.py` |
| 14 | `WizardReActAgent` | `app/domains/job_management/agents/wizard_react_agent.py` |
| 15 | `CandidateSelfServiceAgent` | `app/domains/candidate_self_service/agents/candidate_react_agent.py` |
| 16 | `PipelineTransitionAgent` | `app/domains/pipeline/agents/pipeline_transition_agent.py` |

> Each domain typically also has parent/sub-agents and a `*_tool_registry.py`,
> `*_stage_context.py`, and `*_system_prompt.py` triple (see §4). The 16 above
> are the canonical *routable* ReActAgents; sub-agents (e.g. sourcing's
> search/enrich/diversity/github/nurture agents) are reachable via tool registries.

---

## 4. Domains — `app/domains/`

59 directories (per `DOMAIN_CATALOG.md`), classified as: **13 Agentic** + **3
Micro-Action** (= 16 `@register_domain`), **11 Service**, **30 Repository-stub**,
**2 Canonical-Active-legacy**. Registration is via `@register_domain` in
`app/domains/registry.py`; base contracts in `app/domains/base.py` and
`app/domains/compliance_base.py` (all domains MUST extend `ComplianceDomainPrompt`).

Each domain shows only the canonical sub-parts that **actually exist**.
AI-heavy domains are flagged ⭐.

### Agentic domains (routable by CascadedRouter)

```
app/domains/
├── cv_screening/ ⭐               # CV analysis, WSI evaluation, candidate scoring
│   ├── agents/                    #   pipeline_react_agent, wsi_interview_graph,
│   │                              #   pipeline_{stage_context,system_prompt,tool_registry}
│   ├── tools/                     #   candidate_tools, cv_match_tool, cv_upload_tool
│   ├── services/                  #   cv_parser, cv_scoring_service, rubric_evaluation_service,
│   │                              #   lia_score_service, hitl_service, calibration_profiles,
│   │                              #   personalized_feedback_service, … (30+ services)
│   ├── prompts/  config/  constants/  models/  schemas/  repositories/
├── sourcing/ ⭐                   # Candidate sourcing across channels
│   ├── agents/                    #   sourcing_react_agent (parent) + search/enrich/diversity/
│   │                              #   github/stackoverflow/nurture/passive/referral/planner/
│   │                              #   engagement sub-agents, each w/ *_tool_registry
│   ├── tools/                     #   query_tools, enrichment_tools
│   ├── ports/  services/  config/  repositories/
├── job_management/ ⭐             # Job lifecycle + the canonical WizardReActAgent
│   ├── agents/                    #   wizard_react_agent, wizard_{system_prompt,tool_registry},
│   │                              #   stage_context
│   ├── tools/                     #   job_tools, job_wizard_tools, query_tools, job_tools_compat
│   ├── prompts/  schemas/  services/  config/  repositories/
├── job_creation/ ⭐               # Wizard graph (15 nodes: 11 functional + 4 HITL gates)
│   ├── nodes/                     #   intake, jd_enrichment, competency, wsi_questions,
│   │                              #   salary, bigfive, eligibility, pipeline_template, publish,
│   │                              #   + gate nodes: intake_gate, jd_gate, competency_gate,
│   │                              #   wsi_questions_gate, review_gate, calibration, handoff
│   ├── orchestrator/              #   wizard_orchestrator, wizard_tools, wizard_service_tools,
│   │                              #   wsi_canonical_adapter
│   ├── graph.py  domain.py  state.py  policy_gate.py  compliance.py  feature_flag.py
│   ├── actions/  helpers/  internal/  services/  repositories/
├── recruiter_assistant/ ⭐        # General recruiter copilot (fallback domain)
│   ├── agents/                    #   recruiter_copilot, jobs_mgmt, kanban (+action/insight/
│   │                              #   search sub-agents), talent / talent_funnel react agents
│   ├── tools/  prompts/  services/  config/  repositories/
├── pipeline/ ⭐                   # Pipeline visualization + candidate movement
│   ├── agents/                    #   pipeline_transition_agent + action/context/decision agents
│   ├── tools/  models/  services/  config/  repositories/
├── communication/ ⭐             # Email / WhatsApp / Teams messaging
│   ├── agents/                    #   communication_react_agent + tool_registry/system_prompt
│   ├── tools/  schemas/  models/  services/  config/  repositories/
├── analytics/                     # Recruitment analytics, reports, dashboards
│   ├── agents/  tools/  schemas/  models/  services/  config/  repositories/
├── ats_integration/               # ATS sync (Gupy, Pandapé, Merge)
│   ├── agents/  tools/  models/  services/  config/  repositories/
├── automation/                    # Tasks, reminders, notes, workflow automation
│   ├── agents/  tools/  models/  services/  config/  repositories/
├── hiring_policy/                 # Hiring policy advisory w/ FairnessGuard (PolicyReActAgent)
│   ├── agents/  actions/  tools/  services/  config/  repositories/
├── interview_scheduling/ ⭐       # Scheduling + calendar (LangGraph interview_graph)
│   ├── agents/                    #   interview_graph, interview_scheduling_nodes, system_prompt
│   ├── tools/                     #   scheduling_tools
│   ├── schemas/  models/  services/  config/  repositories/
└── agent_studio/ ⭐               # Custom agent creation/marketplace (tenant-scoped templates)
    └── config/  repositories/     #   resolved via registry.get_domain_for_company()
```

### Micro-action domains (`@register_domain`, lightweight)

```
├── digital_twin/ ⭐   config/                 # Digital twin creation/evaluation
├── recruitment_campaign/  config/            # Multi-stage recruitment campaigns
└── talent_pool/       agents/ config/ repositories/   # TalentPoolReActAgent
```

### Service domains (business logic, not orchestrator-routable)

```
├── ai/                 repositories/ services/   # LLMService, response cache, prompt mgmt
├── interview_intelligence/ ⭐  services/         # bias_detector, comparative_analysis,
│                                                 #   strategic_opinion, interview_wsi,
│                                                 #   feedback_generator, transcription
├── voice/ ⭐           services/ plugins/ protocols/ schemas/ repositories/
│                                                 #   gemini_live_audio, voice_screening_orchestrator,
│                                                 #   voice_core_orchestrator, realtime_credit_session
├── persona/ ⭐         services/                 # ai_persona_service + validators
├── talent_intelligence/ ⭐  tools/ services/     # skills ontology, internal mobility, workforce
│                                                 #   planning, market intel, candidate nurture,
│                                                 #   interview_intelligence_tools (cross-call)
├── company/   candidates/   recruitment/   compliance/   consent/
├── credits/   billing/   integrations_hub/   lgpd/   modules/
```

### Other domains

```
# Canonical-Active (legacy path, NOT deprecated):
├── autonomous/  agents/        # Tier 6 ReAct fallback for CascadedRouter
├── policy/      agents/ services/ repositories/   # PolicyEngineService, PolicySetupAgent,
│                                                  #   ALPHA1_SECTOR_RULES (sector FairnessGuard)
# AI-relevant service domains worth noting:
├── company_settings/ ⭐  agents/ tools/ config/ repositories/   # CompanySettingsReActAgent
├── candidate_self_service/ ⭐  agents/ actions/ tools/ services/ config/ repositories/
├── offer/  agents/ tools/ models/ services/ config/ repositories/   # offer mgmt (SOX audit)
├── opinions/    digital_twin/ (above)
# Repository-stub domains (pure CRUD: __init__.py + dependencies.py + repositories/):
#   admin, admin_settings, agent_memory, approvals, auth, bulk_actions, candidate_lists,
#   chat, clients, client_users, company_culture, data_subject, email_templates, goals,
#   health_check, job_vacancies_analytics, journey_mapping, lia_assistant, notifications,
#   observability, recruitment_journey, saas_metrics, shared_searches, tasks,
#   technical_tests, triagem, trust_center, workforce
```

> Files of note: `app/domains/registry.py` (DomainRegistry singleton +
> `@register_domain` + `get_domain_for_company` Agent-Studio resolution +
> `_YamlDomainProxy`), `app/domains/DOMAIN_CATALOG.md` (authoritative
> classification), `app/domains/base.py`, `app/domains/compliance_base.py`,
> `app/domains/workflow.py`.

---

## 5. Cross-cutting AI infrastructure — `app/shared/`

This is the wrapper layer every agent passes through: LLM access, prompts,
compliance, tenant isolation, audit, messaging, memory, and RAG.

```
app/shared/
├── llm_bootstrap.py            # monkey-patches Anthropic/OpenAI/genai SDK constructors:
│                               #   API-key + base_url injection, PII strip, per-call credit gate,
│                               #   audit log. Single chokepoint for ALL SDK usage.
├── tenant_llm_context.py       # _current_company_id ContextVar reader; per-tenant LLM config
│                               #   (provider/key/model/region) + tenant Gemini/Claude clients
├── domain_action_registry.py   # DomainActionRegistry — single-owner action mapping + aliases
├── tool_catalog.py             # ToolCatalog — system-wide tool inventory
├── tool_handler.py             # ToolHandler — executes tool calls w/ tenant context
├── pii_masking.py              # install_global_pii_masking + strip_pii_for_llm_prompt
├── prompt_injection.py         # prompt-injection detection helpers
├── tenant_guard.py  tenant_session.py  runtime_context.py
├── llm/
│   ├── callbacks.py            # LangChain callbacks (tracing/metrics)
│   └── safe_response.py        # safe LLM response wrapping
├── prompts/
│   ├── system_prompt_builder.py    # SystemPromptBuilder — central prompt assembly
│   ├── prompt_composer.py  loader.py  templates.py
│   ├── agent_prompts.py  job_wizard.py  voice_system_prompt.py
│   ├── persona_aware_prompt.py  training_persona.py  anti_sycophancy_block.py
│   ├── cot.py  few_shot_examples.py  intent_few_shot_examples.py
│   ├── interaction_patterns.py  glossary_loader.py
│   └── examples/
├── compliance/                 # 3-pillar compliance (LGPD + SOX + EU AI Act)
│   ├── fairness_guard.py  fairness_guard_middleware.py  fairness_recursive.py
│   ├── fact_checker.py  prompt_injection_guard.py  hate_speech_guard.py
│   ├── protected_attributes.py  scoring_safeguards.py  safety_category.py
│   ├── c3b_layer.py            # C3b layer (PII strip + Fairness L3 + FactCheck + Audit)
│   ├── audit_service.py  audit_writer.py  audit_storage.py  audit_callback.py
│   ├── audit_decorators.py  audit_models.py  domain_validators.py
│   └── guardrail_repository.py
├── agents/
│   ├── agent_registry.py       # AgentRegistry (legacy intent map, coexists w/ DomainRegistry)
│   ├── agent_bus.py            # AgentBus — inter-agent message bus
│   ├── tenant_aware_agent.py   # TenantAwareAgentMixin + is_tenant_strict_mode +
│   │                           #   resolve_tenant_snippet_for_non_react (canonical non-ReAct seam)
│   ├── crew_executor.py  crew_context.py  crew_audit.py  crew_models.py  crew_examples.py
│   └── agent_types.py
├── tools/
│   ├── export_tools.py  insight_tools.py  predictive_tools.py  proactive_tools.py
├── messaging/                  # BrokerInterface abstraction (Redis / RabbitMQ / Pub-Sub)
│   ├── broker_interface.py  rabbitmq_producer.py  rabbitmq_consumer.py
│   ├── rails_crud_consumer.py  rails_event_publisher.py  rails_event_schemas.py
│   ├── unified_event_publisher.py  platform_events.py  dispatchers.py  celery_config.py
├── memory/
│   ├── conversation_state.py  reference_resolver.py  candidate_list_store.py
├── rag/
│   ├── hybrid_search.py  reranker.py  realtime_fact_checker.py  response_watermarker.py
├── hitl/
│   ├── agent_gate.py  hitl_approval_context.py    (+ shared/hitl_decorator.py at root)
├── governance/
│   ├── agent_monitoring_service.py  feature_flag_service.py
├── intelligence/
│   ├── embedding_service.py  semantic_search_service.py  smart_extractor.py
│   ├── param_patterns.py
│   ├── chunking/              # RecursiveTextSplitter + section_aware/semantic/sliding_window
│   ├── ab_testing/           # thompson_sampler, bandit_posterior_repository
│   └── template_learning/
├── learning/                  # learning loop: correction_capture, feedback_writer,
│                              #   finetuning_export, learning_loop_service, golden curation
└── ml/
    └── ttf_predictor.py       # time-to-fill predictor
```

---

## 6. Top-level AI plumbing — `app/prompts/`, `app/tools/`

```
app/prompts/                    # YAML + Python prompt catalog (registered at startup by
│                               #   app/core/prompt_version_loader.py)
├── domains/                    # per-domain system prompts (YAML):
│   ├── cv_screening.yaml  sourcing.yaml  job_management.yaml  job_creation.yaml
│   ├── company_settings.yaml  communication.yaml  pipeline.yaml  analytics.yaml
│   ├── autonomous.yaml  hiring_policy.yaml  interview_scheduling.yaml  offer.yaml
│   ├── wsi_evaluation.yaml  wsi_interview.yaml  wsi_layer2_extraction.yaml
│   ├── intent_classification.yaml  orchestrator.yaml  agent_studio.yaml  … (31 files)
├── job_creation/              # wizard gate prompts: gate_classifier, gate_competency,
│   │                          #   gate_review, gate_wsi_questions, wizard_supervisor,
│   │                          #   intake_gate_classifier, wsi_question_distribution, messages
├── shared/                    # lia_persona, compliance_block, guardrails_block,
│   │                          #   defensive, few_shot_template, agent_prompts, policy_setup
├── experiments/              # A/B prompt variants (cascade_router, job_wizard_field_extraction)
├── tenants/                  # per-tenant prompt overrides (__test_tenant__)
├── cot.py  examples.py  templates.py  job_wizard.py
└── *_prompts.py              # jobs_management / kanban_assistant / talent_assistant

app/tools/                      # function-calling tool registry (initialize_tools() in lifespan)
├── registry.py                # central tool registry
├── executor.py                # tool executor
├── categories.py  scope_config.py  context_helpers.py
├── tool_registry_loader.py  tool_registry_metadata.yaml
└── tool_permissions_loader.py  tool_permissions.yaml
```

---

## 7. Low-level primitives — `libs/agents-core/`

The reusable agent runtime package (imported as `lia_agents_core`). Domain
ReActAgents build on these primitives; the package has no domain knowledge.

```
libs/agents-core/lia_agents_core/
├── agent_bus.py               # low-level AgentBus primitive
├── react_agent_registry.py    # ReactAgentRegistry — @register_agent decorator + lookup
├── langgraph_react_base.py    # LangGraphReActBase — base class for all ReActAgents
├── langgraph_base.py          # LangGraphBase (sync checkpointer seam)
├── react_loop.py              # the ReAct reason→act loop
├── checkpointer.py            # AsyncPostgresSaver canonical (fail-closed in prod, §main.py)
├── tool_adapter.py  timed_tool_node.py  nodes.py
├── agent_interface.py  agent_scaffold.py  contracts.py  confidence.py
├── enhanced_agent_mixin.py  autonomy_engine.py
├── state_machine.py  base_state_machine.py
├── long_term_memory.py  working_memory.py  memory_integration.py
├── streaming_callback.py  observability.py  execution_log_store.py
├── learning_extractor.py  proactive_worker.py  sourcing_engagement_nodes.py
```

> Sibling `libs/` packages (`audit`, `config`, `messaging`, `models`, `schemas`,
> `services`, `utils`) provide shared infra (e.g. `lia_config.database`,
> `lia_models`) consumed across the AI layer.

---

## 8. Cross-cutting concerns

These wrap **every** agent execution regardless of domain:

- **Tenant isolation** — `TenantAwareAgentMixin`
  (`app/shared/agents/tenant_aware_agent.py`) + the `CompanyId` value object +
  the `_current_company_id` ContextVar (set by `AuthEnforcementMiddleware`, read
  by `tenant_llm_context.py` and `llm_bootstrap.py`). Fail-closed in prod via
  `LIA_AGENT_TENANT_STRICT`. Non-ReAct callsites MUST use
  `resolve_tenant_snippet_for_non_react(...)` — the only canonical seam — never
  read `ctx["tenant_context_snippet"]` directly. This is the blast door against
  the recurring *"LIA pergunta company_id no chat"* bug.

- **Compliance 3-pillar (LGPD + SOX + EU AI Act)** — `FairnessGuard`
  (`fairness_guard.py` + recursive + middleware), `FactChecker`
  (`fact_checker.py`), and `BiasAuditService`
  (`app/domains/interview_intelligence/services/bias_detector_service.py`). All
  domains MUST extend `ComplianceDomainPrompt` (`app/domains/compliance_base.py`)
  — enforced at `@register_domain` time, escape hatch
  `LIA_ALLOW_NON_COMPLIANT_DOMAINS=1` (emergency only).

- **Prompt-injection guard** — `app/shared/compliance/prompt_injection_guard.py`
  (+ `app/shared/prompt_injection.py`) screens recruiter/candidate text and LLM
  output before tool execution.

- **PII protection** — `install_global_pii_masking()` masks CPF/email/phone/name
  in all logs; `llm_bootstrap` strips PII from prompts before SDK calls. Both the
  regex layers (CPF/email/phone/RG/CNPJ + quasi-identifiers) and the Presidio NER
  layer for names (PERSON/NRP) are ON by default
  (`LLM_PROMPT_PII_STRIPPING_ENABLED=true`, `LLM_PROMPT_PRESIDIO_ENABLED=true`).
  The full data-flow map and the residual name-leak gap (recruiter chat runs
  `mask_names=False`) are in §8.2.

- **HITL gates** — `app/shared/hitl/agent_gate.py` +
  `app/shared/hitl_decorator.py`; the job-creation wizard uses LangGraph
  `interrupt()` at 4 gate nodes for human approval.

- **Audit logging** — `app/shared/compliance/audit_service.py` (+ writer/storage/
  decorators). `AuditService.log_decision[_in_session]` is mandatory on mutative
  public service methods in interview/offer domains (SOX 7-year). `main.py`
  registers the main event loop so sync LangGraph nodes can redispatch audit
  writes without poisoning the asyncpg pool.

- **AgentBus / CrewAI-style delegation** — `app/shared/agents/agent_bus.py` (+
  `libs/agents-core/lia_agents_core/agent_bus.py`) carries inter-agent messages;
  `crew_executor.py` / `crew_context.py` formalize multi-agent delegation. The
  orchestrator supervisor (`app/orchestrator/supervisor/handoff_tools.py`) issues
  handoffs across domains.

- **Per-tenant credit gating** — `llm_bootstrap` wraps every SDK message-creation
  primitive with `check_credit_budget`, reading `company_id` from the same
  ContextVar; defense-in-depth gates also live in the orchestrator and agentic
  loop.

---

## 8.1 Cross-cutting control coverage matrix

The §8 bullets describe each control in prose. This matrix answers the practical
question: *which controls touch ALL domains/agents vs. only some, how are they
enforced, and where are the gaps?* "Scope" = how broadly the control fires.
Status uses `OK` (covers its intended surface), `PARTIAL` (covered only on a
subset that should arguably be wider), `GAP` (a known hole, by design or debt).

| Control | Seam (file) | Scope | Enforcement | Status / gap |
|---|---|---|---|---|
| Tenant isolation | `shared/agents/tenant_aware_agent.py` + `_current_company_id` ContextVar | ALL 16 ReActAgents + every non-ReAct callsite | `TenantAwareAgentMixin`; `resolve_tenant_snippet_for_non_react` is the only non-ReAct seam; `LIA_AGENT_TENANT_STRICT` fail-closed in prod | OK |
| Compliance domain prompt | `domains/compliance_base.py` (`ComplianceDomainPrompt`) | ALL `@register_domain` domains | enforced at registration; escape `LIA_ALLOW_NON_COMPLIANT_DOMAINS` (emergency) | OK |
| FairnessGuard | `shared/compliance/fairness_guard.py` (+ recursive + middleware) | scoring / hiring-policy / screening writes | invoked in scoring + `save_*` tools | OK (selective by design: only fairness-relevant decisions) |
| FactChecker | `shared/compliance/fact_checker.py` + `shared/rag/realtime_fact_checker.py` | LLM output before it reaches the user | C3b post-step + RAG path | OK |
| BiasAuditService | `domains/interview_intelligence/services/bias_detector_service.py` | interview / offer decisions | service-level call | OK (domain-scoped) |
| Prompt-injection guard | `shared/compliance/prompt_injection_guard.py` (+ `shared/prompt_injection.py`) | recruiter/candidate text + LLM output | pre-tool screen | OK |
| Hate-speech guard | `shared/compliance/hate_speech_guard.py` | generated output | C3b step | OK |
| PII strip to LLM | `shared/pii_masking.py::strip_pii_for_llm_prompt` + `shared/llm_bootstrap.py` monkey-patch | ALL SDK calls (single chokepoint) | bootstrap wraps `.create`/`.stream`; ON by default | PARTIAL: recruiter chat + some recruiter-facing tools run `mask_names=False`, so candidate NAMES still reach the LLM (see §8.2) |
| PII masking in logs | `shared/pii_masking.py::install_global_pii_masking` (`PIIMaskingFilter`) | root logger + all handlers + stack traces | installed at boot | OK |
| HITL gates | `shared/hitl/agent_gate.py` + wizard `interrupt()` | wizard 4 gates + explicitly gated tools | LangGraph interrupt | OK (selective by design) |
| Audit logging | `shared/compliance/audit_service.py` (+ writer/storage/decorators) | mutative public service methods | mandatory + ratchet sentinel in `interview_scheduling`/`interview_intelligence`/`offer` + `company`; SOX 7-year on offer | PARTIAL: strictly enforced only on those domains; others are best-effort |
| Credit gating | `shared/llm_bootstrap.py::check_credit_budget` | ALL SDK message-creation primitives | bootstrap + orchestrator + agentic-loop (defense-in-depth) | OK |
| BYOK (chat / completion) | `shared/tenant_llm_context.py::get_gemini_client_for_tenant` / `get_claude_model_for_tenant` | Gemini / Claude / OpenAI chat | per-tenant `tenant_llm_configs.providers`; platform key only as fallback | OK |
| BYOK (embeddings) | `shared/providers/embedding_factory.py::_get_tenant_provider` | embedding generation | tenant-key branch exists only for `gemini` | GAP: OpenAI embeddings and the semantic-routing cache always use the platform key (see §8.3) |
| C3b layer (kill-switch) | `shared/compliance/c3b_layer.py` | realtime chat (WS/SSE) | wraps pre/post compliance; `LIA_DISABLE_C3B` kill-switch | OK |

Reading the matrix: tenant isolation, compliance-domain-prompt, prompt-injection,
PII-in-logs, and credit gating are the truly *universal* controls (they fire for
every agent/domain). FairnessGuard, BiasAudit, HITL, and strict Audit are
*selective by design* (only the decisions that need them). The two real holes to
watch are the PII name-leak on recruiter-facing paths (§8.2) and the embedding
BYOK gap (§8.3).

---

## 8.2 PII data-flow map

PII enters from candidate and recruiter input, is minimized at well-defined seams
before any external boundary, and exits only as masked text. The canonical engine
is `app/shared/pii_masking.py`:

- `mask_pii(text)` -> log redaction (`***CPF***`, `***EMAIL***`, ...), with a
  UUID-v4 guard so tenant/job IDs are not eaten by the phone regex.
- `strip_pii_for_llm_prompt(text, mask_names=True)` -> data-minimization before
  LLM/embedding calls (LGPD Art. 12). Layers: (0) UUID guard, (1) direct
  identifiers CPF/email/phone/RG/CNPJ via regex, (3) quasi-identifiers
  (graduation year, explicit age, address) via regex, (4) Presidio NER for
  names (PERSON) and NRP (nationality/religion/politics).

Defaults (all verified in code): `LLM_PROMPT_PII_STRIPPING_ENABLED=true`,
`LLM_PROMPT_PRESIDIO_ENABLED=true`, `LLM_PROMPT_PRESIDIO_LANG=pt`
(spaCy `pt_core_news_sm`), `LLM_PROMPT_PRESIDIO_ENTITIES=PERSON,EMAIL_ADDRESS,PHONE_NUMBER,NRP`.
If Presidio fails to load, `strip_pii_for_llm_prompt` logs a CRITICAL because
names would then leak unmasked.

```
PII ENTRY                       MINIMIZATION SEAM                              PII SINK / BOUNDARY
---------                       -----------------                              -------------------
CV / resume (pdf, docx) --+
voice transcript ---------+
candidate chat -----------+--> c3b_layer.pre_compliance --> strip_pii_for_llm_prompt --+
recruiter chat / notes ---+        (recruiter: mask_names=False  <-- NAME LEAK)         |
ATS inbound notes --------+                                                             v
                                                       defense-in-depth (independent):  LLM SDK
                                            llm_bootstrap monkey-patch on every  -------> (Anthropic /
                                            .create / .stream call (chokepoint)          OpenAI / genai)

embedding text -----------> embedding_service.generate_* --> strip_pii_for_llm_prompt --> vector DB +
                                            (mask_names forwarded)                        embedding cache

any log / exception ------> install_global_pii_masking (PIIMaskingFilter) --------------> logs / Sentry /
                                                                                          stack traces

ATS outbound fields ------> ats_pii_filter.filter_outbound (consent gate: ats_sharing) -> external ATS
```

**Residual name-leak gap (the one to flag):** `c3b_layer.pre_compliance` calls
`strip_pii_for_llm_prompt(message, mask_names=False)` for recruiter chat (both
the chat-page and `agent_chat_ws` callers), on the rationale that recruiters are
authorized to see candidate names and NER was producing false positives on job
titles. Net effect: structured identifiers (CPF/email/phone) are still stripped,
but candidate NAMES on recruiter-facing prompts reach the LLM. `mask_names=True`
remains the default everywhere else (embeddings, candidate-facing paths). The
opt-in `LIA_RECRUITER_CHAT_MASK_PII` re-enables name masking for the recruiter UI.

---

## 8.3 BYOK coverage map (and where embeddings are NOT covered)

Per-tenant LLM config (BYOK) lives in the `tenant_llm_configs` table, resolved by
`app/shared/tenant_llm_context.py` (`get_tenant_llm_config`, in-memory
`_tenant_configs` cache, keyed off the `_current_company_id` ContextVar). The
config carries `primary_provider`, `fallback_order`, and per-provider
`{api_key, model, region}` for gemini / claude / openai.

```
SURFACE                       RESOLVER                                  BYOK?   KEY USED
-------                       --------                                  -----   --------
chat / completion
  Gemini    get_gemini_client_for_tenant (tenant_llm_context.py)       YES     tenant key, else AI_INTEGRATIONS_GEMINI_API_KEY
  Claude    get_claude_model_for_tenant (tenant_llm_context.py)        YES     tenant key, else platform
  OpenAI    tenant_llm_configs.providers.openai                        YES     tenant key, else platform

embeddings
  Gemini    embedding_factory._get_tenant_provider                     YES     tenant key (ONLY provider with a tenant branch)
  OpenAI    embedding_factory (no tenant branch)                       NO      platform OPENAI key (mandatory)
  routing   vector_semantic_cache.embed_with_fallback(text)            NO      called WITHOUT company_id; primary = platform
            (semantic router / routing_cache_vectors)                          OpenAI text-embedding-3-small (1536 dims)
```

**Where embeddings are NOT covered by BYOK (and why it is mandatory):**

1. **OpenAI embeddings.** `EmbeddingProviderFactory._get_tenant_provider` only
   has a tenant-key branch for `provider_name == "gemini"`. Any OpenAI embedding
   (primary for RAG/routing) falls through to the platform `OPENAI_API_KEY`.
2. **Semantic routing cache.** `app/orchestrator/memory/vector_semantic_cache.py`
   calls `EmbeddingProviderFactory.embed_with_fallback(text)` with no
   `company_id`, so even the Gemini path cannot resolve a tenant key there. Its
   primary model is the platform OpenAI `text-embedding-3-small`.
3. **RAG / semantic-search default fallback.** `EMBEDDING_DEFAULT_PROVIDER`
   defaults to `gemini` with `EMBEDDING_FALLBACK_ORDER = ["gemini", "openai"]`;
   when it falls back to OpenAI it uses the platform key.

**Why mandatory:** the routing/semantic vectors are stored in a *shared* table
with fixed dimensions (1536 for OpenAI `text-embedding-3-small`, 768 for Gemini
`text-embedding-004`). Letting each tenant swap embedding provider/model would
mix vector dimensions in the same cache and corrupt similarity lookups, so a
single platform embedding key is enforced for the routing layer regardless of
BYOK. Chat/completion calls (Gemini/Claude/OpenAI) strictly honor BYOK; only the
embedding/routing layer is platform-pinned.

---

## 9. FastAPI ↔ Rails boundary (one-line note)

`lia-agent-system` (this AI layer, the production backend) accepts both locally
signed JWTs and Rails JWTs from `ats_api` (the legacy Ruby-on-Rails
system-of-record); the cross-service trust contract is documented in
`docs/architecture/RAILS_BOUNDARY.md`. The Rails service is out of scope for this
AI-layer tree.
