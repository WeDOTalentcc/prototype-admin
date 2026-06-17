# FairnessGuard Coverage Report

**Generated**: T007 — Validate prompts and PII masking coverage for FairnessGuard compliance.

---

## 1. Persona & Ethical Guidelines

**Location**: `app/prompts/shared/lia_persona.yaml` (not `app/config/lia_persona.yaml` — that file does not exist).

The persona YAML contains an `ethical_guidelines` section that covers:
- Permitted evaluation criteria (hard skills, soft skills, experience, cultural fit)
- Prohibited criteria / bias (name, age, photo, institution, marital status, address, ethnicity)
- Inclusive language requirements
- Transparency and documentation obligations

**Note**: The `ethical_guidelines` section does NOT explicitly mention `FairnessGuard` by name, `LGPD`, or `anti-discrimination` law references. Those references live in the FairnessGuard module itself (`app/shared/compliance/fairness_guard.py`), which cites CLT, LGPD, Lei 7.716/89, Lei 10.741/03, Lei 9.029/95, Lei 13.146/15, CF Art. 5º, and EU AI Act.

---

## 2. Where FairnessGuard Is Active

### 2.1 Core Module
| File | Role |
|------|------|
| `app/shared/compliance/fairness_guard.py` | Core FG engine: L1 regex, L2 implicit bias, L3 semantic, L4 learning batch validation |
| `app/shared/compliance/fairness_guard_middleware.py` | Reusable middleware: `check_fairness()`, `check_fairness_async()`, `check_rejection_reason()` |
| `app/shared/compliance/__init__.py` | Re-exports `FairnessGuard`, `FairnessCheckResult` |

### 2.2 API Endpoints Using FairnessGuard
| File | Usage |
|------|-------|
| `app/api/v1/candidates.py` | `check_rejection_reason` from middleware |
| `app/api/v1/wsi_questions.py` | `check_fairness` from middleware |
| `app/api/v1/jd_generation.py` | `check_fairness` from middleware |
| `app/api/v1/interview_notes.py` | Direct `FairnessGuard` import |
| `app/api/v1/fairness_reports.py` | FairnessGuard referenced |
| `app/api/v1/jd_import.py` | FairnessGuard referenced |
| `app/api/v1/rubric_evaluation.py` | FairnessGuard referenced |
| `app/api/v1/ml_predictions.py` | FairnessGuard referenced |
| `app/api/v1/rag_search.py` | FairnessGuard referenced |

### 2.3 Orchestrator & Workflow
| File | Usage |
|------|-------|
| `app/orchestrator/main_orchestrator.py` | Direct `FairnessGuard` import — query-level check |
| `app/domains/workflow.py` | Direct `FairnessGuard` import |

### 2.4 Domain Agents / Services
| File | Usage |
|------|-------|
| `app/domains/hiring_policy/agents/policy_react_agent.py` | Direct import |
| `app/domains/hiring_policy/agents/policy_tool_registry.py` | Direct import |
| `app/domains/pipeline/agents/pipeline_transition_agent.py` | Lazy import inside method |
| `app/domains/pipeline/agents/pipeline_feedback_tool.py` | Lazy import inside method |
| `app/domains/pipeline/agents/pipeline_tool_registry.py` | Direct import |
| `app/domains/recruiter_assistant/agents/talent_tool_registry.py` | Direct import |
| `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` | Direct import |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | Direct import |
| `app/domains/job_management/agents/wizard_tool_registry.py` | Direct import |
| `app/domains/cv_screening/services/personalized_feedback_service.py` | Direct import |
| `app/domains/cv_screening/services/rubric_evaluation_service.py` | Direct import |
| `app/domains/cv_screening/agents/wsi_interview_graph.py` | `check_fairness` from middleware |
| `app/domains/sourcing/services/pearch_service.py` | Lazy import |
| `app/domains/sourcing/agents/sourcing_react_agent.py` | Lazy import |
| `app/domains/interview_scheduling/agents/interview_scheduling_nodes.py` | Lazy import |
| `app/services/rag_pipeline_service.py` | Lazy import |

### 2.5 Shared / Libs
| File | Usage |
|------|-------|
| `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` | Lazy import — applies FG to all enhanced agents |
| `app/shared/learning/learning_loop_service.py` | Lazy import — validates learned patterns (F1-02) |

### 2.6 System Prompts Referencing FairnessGuard
| File |
|------|
| `app/domains/hiring_policy/agents/policy_system_prompt.py` |
| `app/domains/recruiter_assistant/agents/talent_system_prompt.py` |
| `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` |
| `app/domains/job_management/agents/wizard_system_prompt.py` |
| `app/domains/communication/agents/communication_system_prompt.py` |
| `app/prompts/domains/cv_screening.yaml` |

### 2.7 Tests
| File |
|------|
| `tests/fairness/test_red_teaming.py` |
| `tests/security/test_red_team_fairness.py` |
| `tests/security/test_red_team_circuit_breakers.py` |
| `tests/test_sprint2_fairness_agent.py` |
| `tests/test_fairness_guard.py` |
| `tests/unit/test_far1_new_categories.py` |
| `tests/unit/test_far2_sprint2.py` |
| `tests/unit/test_far2_entry_points.py` |
| `tests/unit/test_far3_soft_warnings.py` |
| `tests/unit/test_far4_layer3.py` |
| `tests/unit/test_f1_02_fairness_learning.py` |
| `tests/unit/test_fairness_guard_mixin.py` |
| `tests/unit/test_fairness_guard_agents.py` |
| `tests/unit/test_sprint_v_product.py` |
| `tests/unit/test_sprint_i_foundations.py` |
| `tests/unit/test_coverage_boost.py` |
| `tests/unit/test_audit_trail_gates.py` |
| `tests/unit/test_p3_features.py` |
| `tests/unit/test_comp8_comp9.py` |
| `tests/unit/test_rag_pipeline.py` |
| `tests/e2e/test_alpha1_scenario.py` |
| `tests/test_domains/test_cv_screening_agents.py` |
| `tests/test_domains/test_wizard_react_agent.py` |
| `tests/test_domains/test_interview_scheduling.py` |
| `tests/test_domains/test_policy_react_agent.py` |
| `tests/test_domains/test_pipeline_transition_agent.py` |

---

## 3. PII Masking Coverage

### 3.1 Core PII Masking Module
**File**: `app/shared/pii_masking.py`

Provides:
- `mask_pii(text)` — regex-based masking of CPF, email, phone, etc.
- `PIIMaskingFilter` — logging filter that auto-masks PII in log messages and exception traces
- `install_global_pii_masking()` — installs masking on root logger and all handlers
- `strip_pii_for_llm_prompt(text)` — removes PII/quasi-identifiers before sending to LLM (controlled by `LLM_PROMPT_PII_STRIPPING_ENABLED` env var)
- Layer 4 (Presidio NER) — optional deep NER-based PII detection when `presidio_analyzer` is installed

### 3.2 PII Masking in Domain Code
| File | Usage |
|------|-------|
| `app/domains/cv_screening/services/rubric_evaluation_service.py` | Calls `strip_pii_for_llm_prompt()` on CV content before LLM call (SEG-3B, LGPD Art. 12 data minimization) |
| `app/shared/learning/finetuning_export.py` | `mask_pii()` method for fine-tuning data export |
| `app/shared/resilience/dlq_service.py` | `_mask_pii()` — masks PII keys in DLQ kwargs before persistence |

### 3.3 ATS-Specific PII Filtering
| File | Role |
|------|------|
| `app/services/ats_clients/ats_pii_filter.py` | PII filter for ATS client data |
| `app/services/ats_clients/lgpd_field_registry.py` | LGPD field classification for ATS sync |

---

## 4. LGPD Compliance Points

### 4.1 Consent Management
| File | Role |
|------|------|
| `app/services/granular_consent_service.py` | Granular consent management service |
| `app/services/consent_checker_service.py` | Consent verification before data processing |
| `app/api/v1/consent_management.py` | Consent management API endpoint |
| `app/api/v1/granular_consent.py` | Granular consent API endpoint |
| `app/schemas/consent_management.py` | Consent data schemas |

### 4.2 Data Subject Requests (Opt-out / Deletion / Access)
| File | Role |
|------|------|
| `app/api/v1/data_subject_requests.py` | DSR API endpoint (access, deletion, portability) |
| `app/api/v1/data_request.py` | Data request handling |
| `app/services/dsr_export_service.py` | DSR data export service |
| `app/schemas/data_subject_requests.py` | DSR data schemas |
| `app/domains/communication/models/data_request.py` | Data request model |

### 4.3 LGPD Administration
| File | Role |
|------|------|
| `app/api/v1/admin_lgpd.py` | Admin LGPD management endpoint |
| `app/api/v1/lgpd_compliance.py` | LGPD compliance endpoint |
| `app/schemas/lgpd_compliance.py` | LGPD compliance schemas |
| `app/services/lgpd_cleanup_service.py` | Data retention / cleanup service |

### 4.4 Data Minimization
| File | Mechanism |
|------|-----------|
| `app/shared/pii_masking.py` | `strip_pii_for_llm_prompt()` — removes PII before LLM calls |
| `app/domains/cv_screening/services/rubric_evaluation_service.py` | Applies PII stripping (LGPD Art. 12) |
| `app/shared/resilience/dlq_service.py` | Masks PII in dead-letter queue persistence |
| `app/services/ats_clients/lgpd_field_registry.py` | Controls which fields are synced to ATS |
| `app/prompts/shared/lia_persona.yaml` | Data persistence guidelines: sensitive data requires explicit consent |

---

## 5. Identified Gaps

### 5.1 Persona Config Location
- The task referenced `app/config/lia_persona.yaml` — this file does **not** exist. The actual persona config lives at `app/prompts/shared/lia_persona.yaml`.

### 5.2 Ethical Guidelines Missing Explicit FairnessGuard References
- The `ethical_guidelines` section in `lia_persona.yaml` does not mention FairnessGuard by name, LGPD, or specific anti-discrimination laws. These references exist only in the FairnessGuard module code. Consider adding a cross-reference to inform LLM prompts that FairnessGuard enforcement is active.

### 5.3 PII Masking Not Applied in All LLM Calls
- `strip_pii_for_llm_prompt()` is confirmed in `rubric_evaluation_service.py` but not explicitly called in other services that send text to LLMs (e.g., JD generation, WSI questions, sourcing search prompts). The global `LLM_PROMPT_PII_STRIPPING_ENABLED` env var controls the feature, but individual call sites may not invoke it.

### 5.4 FairnessGuard Middleware Adoption
- Only 4 files use `fairness_guard_middleware` (`candidates.py`, `wsi_questions.py`, `jd_generation.py`, `wsi_interview_graph.py`). Other endpoints reference FairnessGuard directly rather than through the standardized middleware. Consider migrating to the middleware pattern for consistency.

### 5.5 Domains Without Explicit FairnessGuard Integration
- `app/domains/analytics/` — no FairnessGuard import found (analytics queries could carry bias)
- `app/domains/automation/` — no FairnessGuard import found (automated actions could propagate bias)
- `app/domains/ats_integration/` — no FairnessGuard import found (ATS-synced data not checked)
- `app/domains/communication/` — FairnessGuard referenced in system prompts but not in service code

### 5.6 No FairnessGuard on Public-Facing Endpoints
- `app/api/public/` — public vacancy application endpoints do not appear to have FairnessGuard checks on incoming candidate data.
