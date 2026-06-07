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

> **Review markers (this revision).** Items flagged for follow-up per the
> architecture diagnosis (§14) carry an inline marker: 🔴 FIX (a divergence or
> risk to correct), 🟡 REVIEW (consistency / architecture debt to decide on),
> 🔵 NOTE (minor cleanup or special case to watch). Every marked item is
> consolidated, with the file(s) to touch, in §16 (Action Register).

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
| FairnessGuard (L1 regex / L2 implicit-bias / L3 HR-sensitive) | `shared/compliance/fairness_guard.py` + `fairness_recursive.py` (nested payloads) + `fairness_guard_middleware.py` (FastAPI dep) | scoring / hiring-policy / screening writes + recruiter `save_*` tools | C3b pre-step (L3) + `scoring_safeguards.py` C1-C5 gate (LGPD Art.20 / EU AI Act) + recursive guard on agent payloads | OK (selective by design; depends on the protected-attributes registry loading) |
| Protected-attributes registry | `shared/compliance/protected_attributes.py` + `config/protected_attributes.yaml` | foundation for FairnessGuard + BiasAudit (`PROTECTED_ATTRIBUTE_IDS` / `PROTECTED_DB_FIELDS` / `BIAS_AUDIT_DIMENSIONS`) | loaded at startup; `is_registry_loaded()` sanity check | 🔴 **FIX** — OK, but FAIL-OPEN if the YAML is missing/empty (ADR-031 path bug made FairnessGuard run fail-open Mar-May 2026) |
| FactChecker (+ domain validators, LIA-C06) | `shared/compliance/fact_checker.py` + `compliance/domain_validators.py` + `shared/rag/realtime_fact_checker.py` | LLM output before it reaches the user | C3b post-step + RAG path | OK |
| BiasAuditService (FAR-5 disparate-impact / four-fifths) | `shared/services/bias_audit_service.py` (canonical, cross-domain) + `domains/interview_intelligence/services/bias_detector_service.py` (interview-specific) | periodic / annual bias audits over decisions across domains | `bias_audit_service` singleton; reads `BIAS_AUDIT_DIMENSIONS` from the registry | OK |
| Prompt-injection guard | `shared/compliance/prompt_injection_guard.py` (+ `shared/prompt_injection.py`) | recruiter/candidate text + LLM output | pre-tool screen | OK |
| Hate-speech guard | `shared/compliance/hate_speech_guard.py` | generated output | C3b step | OK |
| PII strip to LLM | `shared/pii_masking.py::strip_pii_for_llm_prompt` + `shared/llm_bootstrap.py` monkey-patch | ALL SDK calls (single chokepoint) | bootstrap wraps `.create`/`.stream`; ON by default | 🔴 **FIX** — PARTIAL: recruiter chat + some recruiter-facing tools run `mask_names=False`, so candidate NAMES still reach the LLM (see §8.2) |
| PII masking in logs | `shared/pii_masking.py::install_global_pii_masking` (`PIIMaskingFilter`) | root logger + all handlers + stack traces | installed at boot | OK |
| HITL gates + tool safety governance | `shared/hitl/agent_gate.py` + `hitl_decorator.@require_hitl` + `compliance/safety_category.py` (`SafetyCategory` enum) | wizard 4 gates + tools tagged in each registry's `GUARDRAIL_TOOLS` (destructive_write / bulk_action / pii_export / outreach / pipeline_move / offer) | LangGraph `interrupt()` + decorator | OK (selective by design) |
| Audit logging | `shared/compliance/audit_service.py` (+ writer/storage/decorators) | mutative public service methods | mandatory + ratchet sentinel in `interview_scheduling`/`interview_intelligence`/`offer` + `company`; SOX 7-year on offer | PARTIAL: strictly enforced only on those domains; others are best-effort |
| Credit gating | `shared/llm_bootstrap.py::check_credit_budget` | ALL SDK message-creation primitives | bootstrap + orchestrator + agentic-loop (defense-in-depth) | OK |
| BYOK (chat / completion) | `shared/tenant_llm_context.py::get_gemini_client_for_tenant` / `get_claude_model_for_tenant` | Gemini / Claude / OpenAI chat | per-tenant `tenant_llm_configs.providers`; platform key only as fallback | OK |
| BYOK (embeddings) | `shared/providers/embedding_factory.py::_get_tenant_provider` | embedding generation | tenant-key branch exists only for `gemini` | 🔴 **FIX** — GAP: OpenAI embeddings and the semantic-routing cache always use the platform key (see §8.3) |
| Per-tenant custom guardrails | `shared/compliance/guardrail_repository.py` + `models/guardrail.py` | DB-backed per-domain / per-company agent guardrails | repository read at agent build; scoped by `is_active` / `domain` / `company_id` | OK |
| C3b layer (kill-switch) | `shared/compliance/c3b_layer.py` | realtime chat (WS/SSE) | wraps pre/post compliance; `LIA_DISABLE_C3B` kill-switch | OK |

Reading the matrix: tenant isolation, compliance-domain-prompt, prompt-injection,
PII-in-logs, and credit gating are the truly *universal* controls (they fire for
every agent/domain). FairnessGuard, BiasAudit, HITL, and strict Audit are
*selective by design* (only the decisions that need them). The
protected-attributes registry is *foundational*: FairnessGuard and BiasAudit both
read it, so if `config/protected_attributes.yaml` fails to load they silently run
fail-open (this already happened, ADR-031), which makes registry-load monitoring
part of the compliance surface rather than an afterthought.

The realtime chat pipeline (`c3b_layer.py`) runs these guards in a fixed order:
HateSpeechGuard, then PII strip, then PromptInjectionGuard, then FairnessGuard L3
(pre-step); FactChecker plus AuditService (post-step). Each guard is wrapped in
its own try/except and logs a skip warning if it cannot validate, so a single
guard failure degrades gracefully instead of taking the turn down.

Known holes to watch: (1) the PII name-leak on recruiter-facing paths (§8.2),
(2) the embedding BYOK gap (§8.3), and (3) the fail-open behavior of the
protected-attributes registry above. Everything else marked `OK` covers its
intended surface; the `PARTIAL` rows (PII-to-LLM, strict Audit) are correct but
narrower than a maximalist reading would want.

### 8.1.1 Coverage grid - controls x the 16 canonical agents

The table above is the per-control reference (seam / enforcement / status). This
grid is the per-cell view (which control actually fires on which agent), in the
"transversal bands" style. Columns are the 16 canonical ReActAgents from §3, in
the same order; the legend maps the short codes. The point this grid makes: most
controls are `OK` on every agent not because each domain re-implements them, but
because every ReActAgent inherits them from `LangGraphReActBase` +
`TenantAwareAgentMixin` + `ComplianceDomainPrompt` + the `llm_bootstrap`
chokepoint. Individual modules implement few of these on their own; the agent
layer unifies the whole band.

Legend: `✓` enforced · `⚠` enforced but with a documented gap · `○` not
applicable / does not fire by design.
Columns: `Anlt`=Analytics, `ATS`=ATSIntegration, `Auto`=Automation,
`Anon`=Autonomous, `Comm`=Communication, `Cfg`=CompanySettings,
`CVSc`=Pipeline/cv_screening, `Pol`=Policy/hiring_policy, `JobM`=JobsManagement,
`Kanb`=Kanban, `Funl`=TalentFunnel, `Src`=Sourcing, `Pool`=TalentPool,
`Wiz`=Wizard, `CSS`=CandidateSelfService, `PTr`=PipelineTransition.

| Control | Anlt | ATS | Auto | Anon | Comm | Cfg | CVSc | Pol | JobM | Kanb | Funl | Src | Pool | Wiz | CSS | PTr |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Tenant isolation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Compliance domain prompt | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FairnessGuard (L1/L2; L3 high-impact) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Protected-attrs registry [a] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FactChecker | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Prompt-injection guard | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Hate-speech guard [b] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PII strip to LLM [c] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PII masking in logs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HITL + tool safety [d] | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ○ | ✓ |
| Audit logging [e] | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ |
| BiasAudit [f] (periodic) | ○ | ○ | ○ | ○ | ○ | ○ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | ✓ | ○ | ○ |
| Credit gating | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BYOK (chat / completion) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BYOK (embeddings) [g] | ○ | ○ | ○ | ○ | ⚠ | ○ | ⚠ | ○ | ⚠ | ⚠ | ⚠ | ⚠ | ○ | ⚠ | ○ | ○ |
| Per-tenant custom guardrails | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| C3b layer [b] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Footnotes:

- **[a]** Foundational config (`config/protected_attributes.yaml`). Shown `✓`
  everywhere because every agent inherits FairnessGuard, which reads it. If the
  YAML fails to load, FairnessGuard and BiasAudit run FAIL-OPEN (ADR-031), so the
  whole column is only as strong as registry-load monitoring.
- **[b]** Hate-speech and the C3b wrapper fire on realtime chat turns
  (`c3b_layer.py`). Background / proactive invocations that skip the chat pipeline
  (e.g. Automation or Autonomous running headless) are covered only by the
  bootstrap-level controls, not by C3b.
- **[c]** Enforced for every agent at the `llm_bootstrap` chokepoint, BUT recruiter
  chat strips with `mask_names=False`, so candidate NAMES still reach the LLM on
  recruiter-facing turns (§8.2). The cell stays `✓` because identifiers
  (CPF/email/phone) are always stripped; the name gap is the row-level caveat.
- **[d]** `✓` where the agent's tool registry declares `GUARDRAIL_TOOLS` /
  `@require_hitl`, plus the Wizard's 4 `interrupt()` gates. `○` = the agent has no
  state-changing tool that needs a human gate.
- **[e]** Best-effort `log_decision` across these agents. The mandatory,
  sentinel-enforced ratchet (SOX 7-year) lives in the `interview_scheduling` /
  `interview_intelligence` / `offer` services, which are not routable ReActAgents,
  so they do not appear as columns. `Cfg` is `○` because `company_settings`
  persists through `save_company_*` without a direct `log_decision` call.
- **[f]** BiasAudit runs periodically / annually over stored decisions (FAR-5
  disparate impact / four-fifths). `✓` marks the agents whose scoring or ranking
  decisions feed those audits, not a per-turn check.
- **[g]** `⚠` = the agent generates embeddings, which use the platform key, not
  the tenant key (§8.3). `○` = the agent does not embed.

Coverage read: 13 of the 17 rows are universal (`✓` on all 16 agents, purely by
inheritance). The 4 scoped rows are HITL/tool-safety and Audit (fire where an
action warrants), BiasAudit (periodic, over decision-producing agents), and BYOK
embeddings (the one true gap: platform key on every agent that embeds).

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

🔴 **FIX — Residual name-leak gap (the one to flag):** `c3b_layer.pre_compliance` calls
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

🔴 **FIX — Where embeddings are NOT covered by BYOK (and why it is mandatory):**

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

---

## 10. Domain & agent glossary

§3 lists *where* each agent lives and §4 lists the domain tree. This section adds
the *what it does / when it fires* dimension. Source of truth for the domain
classification is `app/domains/DOMAIN_CATALOG.md`; the inventory of the 16
canonical ReActAgents is `tests/integration/agents/test_tenant_aware_rollout_t_d.py`.

### 10.1 The 16 canonical ReActAgents (what each does)

| Agent | Domain | What it does / when it fires |
|---|---|---|
| `AnalyticsReActAgent` | analytics | Recruitment analytics, reports, dashboards, KPIs. Narrates metrics and trends in chat. |
| `ATSIntegrationReActAgent` | ats_integration | Connects and syncs jobs/candidates with external ATS (Gupy, Pandape, Merge). |
| `AutomationReActAgent` | automation | Tasks, reminders, notes, lightweight workflow automation. |
| `AutonomousReActAgent` | autonomous (legacy) | Cross-domain ReAct fallback. Historically the router "Tier 6" fallback; see §12 for its disputed current status. |
| `CommunicationReActAgent` | communication | Composes and sends email / WhatsApp / Teams, progress reports, daily briefings. |
| `CompanySettingsReActAgent` | company_settings | Conversational company configuration (profile, benefits, workforce plan, culture) with prefill tags and FairnessGuard on every save. |
| `PipelineReActAgent` | cv_screening | CV analysis, WSI scoring, candidate screening and ranking. |
| `PolicyReActAgent` | hiring_policy | Hiring-policy advisory with FairnessGuard and diversity rules. |
| `JobsManagementReActAgent` | recruiter_assistant | Job CRUD, pipeline configuration, job queries. |
| `KanbanReActAgent` | recruiter_assistant | Kanban / pipeline board operations and candidate-movement insights. |
| `TalentFunnelReActAgent` | recruiter_assistant | The canonical Talent Funnel: multi-mode candidate search across 3 sources. |
| `SourcingReActAgent` | sourcing | Candidate sourcing across channels; parent of the search / enrich / diversity / github / nurture / passive / referral sub-agents. |
| `TalentPoolReActAgent` | talent_pool | Talent-pool management (list, add candidate, move pool to job). |
| `WizardReActAgent` | job_management | Drives the HITL job-creation wizard (15 nodes, 4 `interrupt()` gates). |
| `CandidateSelfServiceAgent` | candidate_self_service | Candidate-facing self-service (public screening chat, application status). |
| `PipelineTransitionAgent` | pipeline | Validates and executes candidate stage transitions. |

Note: the 16 ReActAgents are NOT the same set as the 16 `@register_domain`
domains. Some agents live in domains that are classified as service or legacy
(e.g. `company_settings`, `candidate_self_service`, `autonomous`), and some
`@register_domain` domains (e.g. `digital_twin`, `recruitment_campaign`) have no
routable ReActAgent. See §14 for why this matters.

### 10.2 Domains by class (one-line purpose)

**Agentic (13, `@register_domain`, router-routable):** `analytics` (reports,
dashboards) · `ats_integration` (external ATS sync) · `automation` (tasks /
reminders / notes) · `communication` (email / WhatsApp / Teams) · `cv_screening`
(CV analysis + WSI scoring) · `hiring_policy` (policy advisory + FairnessGuard) ·
`interview_scheduling` (scheduling + calendar) · `job_creation` (the wizard graph)
· `job_management` (job lifecycle + WizardReActAgent) · `pipeline` (stage
transitions) · `recruiter_assistant` (general copilot + fallback) · `sourcing`
(candidate sourcing) · `agent_studio` (custom-agent creation, see §13).

**Micro-action (3, lightweight `@register_domain`):** `digital_twin` (candidate
digital-twin creation/eval) · `recruitment_campaign` (multi-stage campaigns) ·
`talent_pool` (pool management).

**Service (11, business logic, not router-routable):** `ai` (LLM services,
response cache, prompt mgmt) · `billing` · `candidates` (candidate CRUD) ·
`company` (company config) · `credits` (token consumption) · `integrations_hub`
(third-party integration mgmt) · `interview_intelligence` (bias detection,
comparative analysis; promotion candidate) · `lgpd` (data-protection compliance) ·
`modules` (feature gating) · `recruitment` (process data) · `voice` (voice
screening; promotion candidate). Also AI-relevant: `persona` (AI persona
personalization), `talent_intelligence` (skills ontology, internal mobility,
workforce planning), `offer` (offer mgmt with SOX audit), `candidate_self_service`,
`company_settings`.

🟡 **Repository-stub (30):** pure CRUD (`__init__.py` + `dependencies.py` +
`repositories/` only). Consumed by agentic domains and routes; not agents. Full
list in `DOMAIN_CATALOG.md`.

🟡 **Canonical-active legacy (2):** `autonomous` (ReAct fallback) and `policy` (the
real `PolicyEngineService` + `PolicySetupAgent` + sector FairnessGuard rules).
Production code in the pre-refactor location; `hiring_policy` does NOT replace
`policy`.

---

## 11. Capability catalog

What the platform can actually *do*, grounded in the implementing code. Business
actions are reached either through the deterministic `action_handlers` (Phase 1 of
the orchestrator) or through a domain agent's tools (Phase 2); state-changing ones
pass an HITL confirmation.

### 11.1 Business / recruiting actions

| Capability | Implemented in | HITL |
|---|---|---|
| Generate report / daily briefing | `orchestrator/action_handlers/analytics_actions.py`, `communication_actions.py` (`_send_progress_report`, `_generate_daily_briefing`) + analytics domain tools | no |
| Compare candidates | `orchestrator/action_handlers/sourcing_actions.py` (`_compare_candidates`) | no |
| Move candidate across stages | `orchestrator/action_handlers/candidate_actions.py` (`_move_candidate`, `_batch_move_candidates`) + `PipelineTransitionAgent` | yes |
| Schedule / reschedule interview | `orchestrator/action_handlers/interview_actions.py`, `communication_actions.py` | yes |
| Send communication (email / WhatsApp) | `orchestrator/action_handlers/communication_actions.py` (`_send_email`, `_send_whatsapp`) | yes |
| Source / search candidates | `orchestrator/action_handlers/sourcing_actions.py` (`_search_candidates`), `domains/sourcing/tools/query_tools.py` | no |
| Screen CV / WSI score | `orchestrator/action_handlers/candidate_actions.py` (`_start_screening`), `domains/cv_screening/services/wsi_service/` | no |
| Create job (wizard) | `domains/job_management/tools/job_wizard_tools.py`, `domains/job_creation/graph.py` | yes (4 gates) |
| Publish job / sync to ATS | `domains/ats_integration/services/`, `domains/job_creation/nodes/publish.py` | yes |
| Manage offers | `domains/offer/tools/`, `domains/offer/services/` (SOX audit) | yes |
| Talent-pool operations | `domains/talent_pool/agents/talent_pool_tool_registry.py` (list / add / move pool to job) | move = yes |

> Creation of a job is ALWAYS and ONLY the canonical wizard; Plan & Execute never
> creates a job (see `replit.md` Plan & Execute section).

### 11.2 AI / platform capabilities

| Capability | Lives in | Status |
|---|---|---|
| Learning Loop / feedback | `app/shared/learning/` (`learning_loop_service`, `feedback_writer`, `implicit_feedback_service`, `correction_capture`, `ab_testing_service`, `learning_golden_curation_service`, `learning_snapshot_service`, `template_learning_service`, `finetuning_export`) | active |
| Personalization / persona | `app/domains/persona/services/` (AI persona) | active |
| Plan & Execute | `app/shared/execution/` (`plan_detector`, `plan_executor`), `app/orchestrator/execution/task_planner.py`, `app/orchestrator/services/plan_orchestration_service.py` | built, OFF in prod (`LIA_V2_USE_PLAN_SERVICE`, canary) |
| ML / predictive | `app/services/ml/` (`outcome_predictor`, `model_registry`, `feature_engineering`) | active |
| RAG / retrieval | `app/shared/rag/` (`hybrid_search`, `reranker`, `realtime_fact_checker`, `response_watermarker`), `app/shared/intelligence/semantic_search_service.py` + `chunking/recursive` (RecursiveTextSplitter), `app/domains/ai/services/hybrid_search_service.py` | active |
| Semantic routing cache | `app/orchestrator/routing/` (`cascaded_router` tiers 0-5: LRU, Redis, pgvector, FastRouter, LLM cascade) | active |
| Voice analysis | `app/domains/voice/services/voice_screening_orchestrator.py` (Gemini Live + Twilio PSTN fallback) | active, per-agent flag |
| Anti-sycophancy | `app/shared/prompts/` anti-sycophancy block (`ANTI_SYCOPHANCY_ORCHESTRATOR` / `ANTI_SYCOPHANCY_OPERATIONAL`) injected into prompts | active |
| Calibration | `domains/cv_screening/services/calibration_profiles`, `domains/job_creation` calibration node | active |

---

## 12. Federated vs Supervisor orchestration (what is ON / OFF)

The `MainOrchestrator` (`app/orchestrator/execution/main_orchestrator.py`) runs a
multi-phase pipeline. Two macro-strategies coexist: the **federated** path (live)
and the **supervisor / plan** path (built but mostly OFF in production). This is
the "agente federado ligado, supervisor desligado" state.

```
request
  │
  ├─ Phase 0  PendingAction        (resume a previous action / collect params)
  ├─ Phase 1  ActionExecutor       (deterministic intent -> action_handlers; LLM narrates result)
  ├─ Phase 1.3 Plan & Execute      (multi-step plan)         [SUPERVISOR — OFF in prod]
  └─ Phase 2  Federated routing    (CascadedRouter -> domain specialist ReAct agent)  [LIVE]
```

### 12.1 Federated path (ENABLED, primary)

A request is mapped to ONE domain specialist by the `CascadedRouter`
(`app/orchestrator/routing/cascaded_router.py`), an 8-tier funnel from cheap to
expensive:

```
Tier 0  MemoryResolver        pronoun / context-reference resolution
Tier 1  LRU in-process        MD5 hash, O(1), per company_id
Tier 2  Redis hash cache      distributed exact match across workers
Tier 3  VectorSemanticCache   pgvector cosine >= 0.85   (ROUTER_VECTOR_CACHE_ENABLED)
Tier 4  FastRouter            regex / keyword patterns
Tier 5  LLM Cascade           Haiku -> Sonnet -> Opus   (expensive, last resort)
Tier 6  REMOVED (Sprint 12.3-B)  was the AutonomousReActAgent cross-domain fallback
```

The matched domain loads its specialist agent (one of the 16 ReActAgents) and runs
the ReAct loop. This is the default conversational path for single-domain
requests and it is what is live today.

### 12.2 Supervisor / Plan path (mostly OFF)

Two distinct "supervisor" implementations exist:

- **Plan & Execute (Phase 1.3)** decomposes multi-step requests (e.g. "publish the
  job and find 5 candidates") into a plan executed across domains. Components:
  `plan_detector` + `plan_executor` (`app/shared/execution/`), `task_planner`,
  `plan_orchestration_service`. **Default OFF in prod** (`LIA_V2_USE_PLAN_SERVICE`,
  canary rollout, ON only where explicitly enabled). It NEVER creates a job.
- **Wizard supervisor classifier** is a pre-graph 6-intent classifier specific to
  the job-creation wizard (`LIA_WIZARD_SUPERVISOR_CLASSIFIER`). **ON in dev/test,
  OFF in prod.**

> 🔴 **FIX** — Open inconsistency to reconcile: the router header marks Tier 6 (the autonomous
> cross-domain fallback) as REMOVED in Sprint 12.3-B "env never set in prod", while
> `DOMAIN_CATALOG.md` still documents `autonomous` as the live Tier 6 fallback. The
> two disagree; the catalog entry is likely stale and should be updated to match
> the router.

---

## 13. Agent Studio (custom agents)

`agent_studio` lets a tenant create its own agents without code. It is one of the
more mature domains: model, runtime, API, marketplace, and safety controls are all
present.

- **Model** (`libs/models/lia_models/custom_agent.py`): `CustomAgent` with
  `name`, `role`, `description`, `system_prompt`, `allowed_tools[]`,
  `excluded_tools[]`, `domain` / `category`, `status` (draft / active / paused /
  archived), `version`, `max_steps` (default 8), `temperature`, `model_override`,
  `enable_memory`, `context_level`, channel flags (`voice_enabled`, `voip_enabled`,
  `whatsapp_enabled`, `triagem_invite_enabled`), sourcing-only payloads
  (`search_strategy` / `preferences` / `outreach_config`), and runtime metrics
  (`total_executions`, `avg_confidence`). Tenant-scoped (`company_id`, FK ON DELETE
  CASCADE for LGPD erasure).
- **Creatable categories** (`category`, source of truth): `screening`, `sourcing`,
  `communication`, `analytics`, `automation`, `job_management` (plus `general`
  default). Sourcing agents have their own quota bucket.
- **Runtime** (`app/domains/agent_studio/custom_agent_runtime.py`):
  `CustomAgentRuntime` extends `LangGraphReActBase`, so a custom agent inherits the
  same compliance / tenant band as a built-in agent (§8.1). `context_level` chooses
  how much context is composed into the prompt: `full` (persona + domain + tenant +
  user + history + few-shot + intelligence_floor + custom), `standard` (no history,
  no few-shot), `minimal` (intelligence_floor + custom instructions only).
- **Safety controls**: a `_RESTRICTED_TOOLS` denylist removes dangerous tools;
  write tools require `confirm=True` and pass the canonical HITL gate (AUD-4 audit);
  a `dry_run` sandbox runs the real reasoning but intercepts side effects and
  returns "would do" actions; `FairnessGuard` validates the prompt on create /
  update; `intelligence_floor.yaml` is injected into every custom prompt as a
  quality / safety floor; `_CURRENT_COMPANY_ID` ContextVar enforces tenant
  isolation on every tool call; `studio_audit` logs creation / update / test /
  execution.
- **Marketplace** (`app/services/agent_marketplace_service.py`,
  `app/api/v1/custom_agents.py`): `AgentMarketplaceListing` (pending_review ->
  approved / rejected / unpublished) with a review workflow, `AgentInstallation`
  tracks cross-tenant installs, and `PoolAgentAssignment` binds an agent to a
  talent pool.

Verdict: well-structured and safe to represent as a first-class part of the AI
layer. 🔵 **NOTE** — the main remaining work is shifting some advanced filter logic from the
service layer down into `CustomAgentRepository`; the core lifecycle, runtime, and
guardrails are solid.

---

## 14. Enterprise-architecture diagnosis

Honest assessment against an enterprise checklist, grounded in the code audited
above. Verdict: the *agent layer* is enterprise-grade; the *domain layer* is
enterprise-grade at its core but still in transition at the edges.

### 14.1 Where it is enterprise-grade

- **Multi-tenancy**: `TenantAwareAgentMixin` on all 16 ReActAgents (sentinel-
  enforced), `CompanyId` value object, PostgreSQL RLS, tenant-scoped repositories.
- **Compliance**: 3-pillar (LGPD + SOX + EU AI Act), FairnessGuard (3 forms +
  L1/L2/L3), FactChecker, BiasAudit, protected-attributes registry, mandatory
  audit ratchet on interview / offer with SOX 7-year retention (§8.1).
- **Safety by inheritance**: 13 of 17 cross-cutting controls fire on every agent
  purely through the shared base classes and the `llm_bootstrap` chokepoint
  (§8.1.1) - including custom Studio agents.
- **Cost / observability**: per-tenant credit gating on every SDK call, external
  cost ledger, structured logging with PII masking, Sentry, health endpoints,
  canary monitoring of bypass flags.
- **Routing efficiency**: 6-tier cache-first router (memory / LRU / Redis / pgvector
  / regex / LLM cascade) keeps the expensive LLM tier as a last resort.
- **Testing discipline**: offline sentinels, AST validators, eval gates, and
  baselines guard the critical contracts (the `replit.md` contracts section is
  itself evidence of a mature regression-prevention culture).

### 14.2 Where the domain layer is NOT yet uniform

What "consistency" means here: every domain of the same class should share the same
anatomy, the same registration, the same naming, and the same layering, so a
newcomer can tell at a glance what is an agent, what is data access, and where each
rule lives. Concretely that means: every agentic domain registers the same way
(`domain.py` + `@register_domain` + inherits `ComplianceDomainPrompt`); all agentic
logic lives in an agentic domain (not in a "service domain"); the data-access (CRUD)
layer is separated from the agent layer; no two packages do the same job; and the
docs match the code. The items below are where that is not yet true. The gap is
consistency (form), not capability (function): everything works.

- 🟡 **Two architectures coexist.** Modern domains register via `@register_domain` +
  `ComplianceDomainPrompt`; legacy `autonomous` and `policy` (about 2.3k LOC each)
  still use the pre-refactor `agents/` + `@register_agent` shape.
- 🟡 **Namespace bloat.** 30 of 59 `app/domains/` entries are pure repository stubs
  (CRUD only). Putting data-access packages in the same namespace as autonomous
  agent domains makes the system look larger and less consistent than it is.
- 🟡 **Duplication / overlap.** `hiring_policy` (a ~40-LOC registered stub) overlaps
  conceptually with `policy` (the real engine, ~2,343 LOC, legacy: `PolicyEngineService`
  + `PolicySetupAgent` + sector FairnessGuard rules) - a reader cannot tell from
  the namespace where hiring rules are actually enforced. `hiring_policy` does NOT
  replace `policy`.
- 🟡 **Migration debt.** `interview_intelligence` and `voice` carry agentic-grade
  logic (2026 / 1725 LOC) but are still classified as service domains (promotion
  candidates). `talent_intelligence` similarly has tools/services without a
  `domain.py`.
- 🟡 **Two overlapping "16"s.** The 16 routable ReActAgents and the 16
  `@register_domain` domains are different sets (§10.1), which is a recurring source
  of confusion.
- 🔴 **Doc drift.** At least one authoritative doc (`DOMAIN_CATALOG.md`) is stale vs
  the code (the Tier 6 / autonomous status in §12).

### 14.3 Recommendation

The platform clears the enterprise bar on the dimensions that are hardest to
retrofit: tenant isolation, compliance, auditability, and cost control. The gap is
consistency, not capability. The highest-leverage cleanups are: (1) move the 30
repository stubs out of `app/domains/` (or mark them clearly as data-access), (2)
finish promoting `interview_intelligence` / `voice` / `talent_intelligence` to the
canonical agentic shape, (3) resolve the `policy` vs `hiring_policy` ownership, and
(4) reconcile `DOMAIN_CATALOG.md` with the router. None of these are blockers; they
are the difference between "enterprise-grade core" and "uniformly enterprise".

---

## 15. Effort estimate: relocating the 30 repository stubs

Recurring question: can the 30 repository-stub "domains" be removed, and what does
it take to clean them up? They CANNOT be deleted (each is imported by live routes
and services), but they CAN be relocated out of `app/domains/` (e.g. to
`app/data/` or `app/repositories/`) so the namespace stops conflating data-access
packages with autonomous agent domains. This section sizes that refactor. Numbers
below were measured by grep at the time of writing; re-measure before executing.

### 15.1 The de-risking fact: no models, no migrations

None of the 30 stubs contain a SQLAlchemy model (`__tablename__` / `Base`
subclass) - all models live under `libs/models/`. Therefore relocating these
directories carries **zero Alembic / migration risk**. It is a pure import-path
refactor, not a schema change. This is the single biggest reason the work is
low-risk.

### 15.2 Coupling surface (what actually has to change)

| Coupling point | Count | Notes |
|---|---|---|
| External import sites (`from app.domains.<stub> ...`) | ~96 files | Caught at import time / by the test suite if any are missed. |
| Structural sensors that hardcode the layout | 4 scripts | `scripts/check_stub_invariants.py`, `scripts/validate_stubs.py`, `scripts/check_canonical_domain_structure.py`, `scripts/check_no_imports_from_deprecated.py`. Must be updated in lockstep or CI fails. |
| Dynamic / string-based module paths | 1 known | `app/shared/tool_catalog.py` references `app.domains.workforce.agents.workforce_tool_registry` as a string via `importlib`. A blind import find-replace will NOT catch this; it would fail only at runtime. |

Import-site distribution (uneven - a few stubs carry most of the churn):

- Trivial (1-3 import sites): ~22 stubs (e.g. `triagem`, `auth`, `chat`, `consent`,
  `goals`, `health_check`, `saas_metrics`). Bulk find-replace.
- Moderate (4-7): `admin` (5), `notifications` (7), `tasks` (6), `workforce` (7),
  `compliance` (4), `data_subject` (4), `opinions`* .
- Careful (10-14): `approvals` (14), `opinions` (10). Review case by case.

### 15.3 What does NOT break

- Data / tables (no models in the stubs, so no migrations).
- The 16 core ReActAgents (they do not depend on these CRUD stubs).
- API routes - as long as each stub's `dependencies.py` is moved together with its
  `repositories/`.

### 15.4 Verdict and recommended execution

Effort: **low to medium, mostly mechanical.** Risk: **low**, because there are no
migrations and the imports are static (so the test suite + sensors catch anything
left behind). The only non-static catch point is the `workforce` string reference.

- Fits in a single focused change, but is best done in batches (trivial ->
  moderate -> careful) with the test + sensor suite run between batches.
- 🔵 Treat `workforce` separately: it has `agents/` plus the dynamic string path, so it
  is not a pure stub. It belongs with the "promote to agentic" group
  (`voice`, `interview_intelligence`, `talent_intelligence`), not the
  "relocate data-access" group.
- Minimum-risk variant: move the directories and leave a thin re-export
  `__init__.py` at the old path. This recreates the kind of shim `DOMAIN_CATALOG.md`
  records as being deleted, so use it only as an intermediate migration step, not as
  the destination.

> *`opinions` is listed under "Other domains" in §4 but classified as a repository
> stub in `DOMAIN_CATALOG.md`; treat it as a stub for this refactor.

---

## 16. Action Register (follow-up backlog)

Single index of every item flagged inline above, with the file(s) to touch.
Markers: 🔴 FIX (a divergence or risk to correct), 🟡 REVIEW (consistency /
architecture debt to decide on), 🔵 NOTE (minor cleanup or special case). The
section column points back to the rationale. None of these are production
blockers; they are the cleanup backlog behind the §14 diagnosis.

| # | Mark | Item | Section | Target file(s) |
|---|:--:|---|---|---|
| 1 | 🔴 | `DOMAIN_CATALOG.md` still lists Tier 6 / `autonomous` as the live fallback; the router marks it REMOVED (Sprint 12.3-B) | §12.2, §14.2 | `app/domains/DOMAIN_CATALOG.md` |
| 2 | 🔴 | Candidate NAMES reach the LLM on recruiter-facing chat (`mask_names=False`) | §8.1, §8.2 | `app/shared/compliance/c3b_layer.py`, `app/shared/pii_masking.py` (opt-in flag `LIA_RECRUITER_CHAT_MASK_PII`) |
| 3 | 🔴 | Protected-attributes registry runs FAIL-OPEN if the YAML fails to load (ADR-031) | §8.1 [a], §8.1.1 | `config/protected_attributes.yaml`, `app/shared/compliance/protected_attributes.py` (+ registry-load monitoring) |
| 4 | 🔴 | BYOK gap: OpenAI embeddings and the semantic-routing cache always use the platform key | §8.1, §8.3 | `app/shared/providers/embedding_factory.py`, `app/orchestrator/memory/vector_semantic_cache.py` |
| 5 | 🟡 | 30 repository stubs pollute `app/domains/`; relocate to a data-access namespace | §4, §14.2, §15 | the 30 stub dirs + sensors `scripts/check_stub_invariants.py`, `validate_stubs.py`, `check_canonical_domain_structure.py`, `check_no_imports_from_deprecated.py` + `app/shared/tool_catalog.py` |
| 6 | 🟡 | `hiring_policy` vs `policy` ownership overlap (where are hiring rules actually enforced?) | §4, §10.2, §14.2 | `app/domains/hiring_policy/`, `app/domains/policy/` |
| 7 | 🟡 | Promote `interview_intelligence` / `voice` / `talent_intelligence` to the canonical agentic shape | §4, §10.2, §14.2 | those domain dirs (add `domain.py` + `@register_domain`) |
| 8 | 🟡 | Two different "16"s (routable agents vs `@register_domain` domains) confuse readers | §10.1, §14.2 | doc-level + `app/domains/DOMAIN_CATALOG.md` |
| 9 | 🔵 | Agent Studio: move advanced filter logic from the service layer into `CustomAgentRepository` | §13 | `app/domains/agent_studio/` |
| 10 | 🔵 | `workforce` is a stub with `agents/` + a dynamic string path; handle separately from the pure stubs | §15.4 | `app/domains/workforce/`, `app/shared/tool_catalog.py` |
