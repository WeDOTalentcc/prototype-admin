# Glossário de Tools e DomainActions — LIA AI

> **Fonte da verdade visível** para o time de desenvolvimento consumir e reproduzir a camada de IA da plataforma LIA.
>
> Gerado automaticamente a partir de:
> - `app/tools/tool_registry_metadata.yaml` (fonte YAML das ferramentas)
> - `app/domains/*/actions.py` e `app/domains/*/domain.py` (DomainActions)
>
> **Regenerar:** `python scripts/generate_tool_action_glossary.py`
>
> **Última atualização:** 2026-04-21 11:14 UTC · **Status pós FIX 1-12:** 100% cobertura

## Changelog referente aos FIXes

| FIX | Commit | Mudou no glossário |
|-----|--------|---------------------|
| 1 | `82009b0c8` | n/a (injeção no LLM) |
| 2 | `4d55b7c40` | +245 examples em DomainActions |
| 3+4 | `c9ec97385` | +governance_tags, +related_tools em Tools |
| 5+6+7 | `71a2ec1d1` | wizard sync + cross-refs em 2 clusters |
| 8 | `8e8bfa3bd` | +side_effects em Tools + FairnessGuard ativa |
| 9 | `896f4ae34` | +25 examples inline (4 domínios novos) + 100% quality |
| 10 | `c0a3e3b79` | +5 wizard tools YAML (extract_job_requirements, create_job_draft, validate_job_requirements, get_salary_benchmarks, check_job_draft_health) |
| 11 | `cf12c3ec9` | cross-ref em `generate_wsi_questions` |
| 12 | `3f7245f18` | n/a (observability module) |

---
## Governance tags — glossário

Valores canônicos de `governance_tags` (campo de `ToolDefinition`) com enforcement atual.

| Tag | Significado | Enforcement | Status |
|-----|-------------|-------------|--------|
| `multi_tenant` | Tool valida `company_id` | `ToolExecutionContext` | ✅ ativo |
| `pii` | Tool trata PII | Logging/audit (parcial) | ⏳ parcial |
| `fairness_guard` | Sujeita à análise de viés | **FIX 8** — Layer 1 regex bloqueia | ✅ **ativo** |
| `requires_hitl` | Precisa confirmação humana | **FIX 3** — `pending_hitl_confirmation` | ✅ **ativo** |
| `audit_trail` | Grava audit log | Hook futuro | ⏳ parcial |
| `credits_consumed` | Custa crédito externo | Validação futura | ⏳ parcial |
| `write_destructive` | Ação destrutiva | Combinada com `requires_hitl` | ✅ via HITL |

---
## Side_effects — glossário

Valores observados no YAML (15 distintos).

| Side effect | Significado | Uso downstream |
|-------------|-------------|----------------|
| `none` | Read-only | Retry seguro, idempotent |
| `db_write` | Persiste no banco | Retry cuidadoso, idempotency key |
| `external_api_call` | Chama API externa | Circuit breaker, timeout |
| `credits_consumed` | Gasta créditos pagos | Budget check pré-execução |
| `audit_trail` | Grava audit log | Forward ao audit service |
| `email_sent` | Envio de email | Rate limiting, dedup |
| `webhook_fired` | Dispara webhook | Replay protection |
| `whatsapp_sent` | Envio via WhatsApp | Rate limiting por tenant |
| `mock_only` | Só mock | Skip em produção |
| `write_destructive` | Destrutivo | Sempre com HITL |

---
## Tools (103 entries)

### `add_candidate_to_vacancy`

**Descrição completa:**
> Adds an existing talent-pool candidate to a specific vacancy, creating a VacancyCandidate record at the specified initial stage. Use when sourcing agents find matches or when the recruiter manually nominates a candidate for a position. Writes to vacancy_candidates table; does not duplicate the candidate profile.

**USE WHEN:**
> Sourcing agent found a match; recruiter says "adicionar esse candidato à vaga X"; bulk sourcing results need to be funneled into an active job; talent pool promotion.

**DO NOT USE WHEN:**
> Candidate is not yet in the talent pool (import first); candidate is already in the vacancy (will create duplicate); moving between stages (use update_candidate_stage).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['search_candidates', 'update_candidate_stage', 'shortlist_candidate']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "vacancy_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "vacancy_id": {
      "type": "string"
    },
    "stage": {
      "type": "string"
    },
    "notes": {
      "type": "string"
    }
  }
}
```

---

### `add_to_list`

**Descrição completa:**
> Adds a candidate to a named talent pool list (e.g., "Banco Sênior Python", "Ex-clientes interessados") for future outreach and pipeline management. Lists are tenant-scoped. Does not change the candidate's stage or vacancy assignment.

**USE WHEN:**
> Tagging a candidate for future sourcing campaigns; recruiter wants to segment the talent pool by profile type; pre-campaign list building; saving silver medalists.

**DO NOT USE WHEN:**
> Adding candidate to an active vacancy (use add_candidate_to_vacancy); creating a full talent pool with automation (use create_talent_pool); shortlisting for specific vacancy (use shortlist_candidate).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['create_talent_pool', 'add_to_talent_pool', 'shortlist_candidate']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "list_name"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "list_name": {
      "type": "string"
    },
    "notes": {
      "type": "string"
    }
  }
}
```

---

### `add_to_talent_pool`

**Descrição completa:**
> Adds one or more candidates to an existing talent pool by pool_id and candidate ID list. Creates pool membership records. Candidates remain in the pool independently of any active vacancy assignment. Use this to grow a talent pool from sourcing results or talent pool migration.

**USE WHEN:**
> Sourcing agent surfaces matching profiles for a pool; recruiter manually adds candidates to a strategic pool; bulk import from external source into pool.

**DO NOT USE WHEN:**
> Adding candidate to a specific vacancy (use add_candidate_to_vacancy); creating a new pool (use create_talent_pool); moving candidates from pool to job (use move_pool_to_job).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['move_pool_to_job', 'get_pool_candidates', 'create_talent_pool']` |
| `allowed_agents` | `['talent_pool', 'sourcing', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "pool_id",
    "candidate_ids"
  ],
  "properties": {
    "pool_id": {
      "type": "string"
    },
    "candidate_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `advance_campaign_stage`

**Descrição completa:**
> Advances a recruitment campaign to its next configured stage, triggering the associated automation actions (e.g., sending WSI invites, mass shortlisting, notifying hiring manager). HITL confirmation is required for stages marked as sensitive (offer, hire).

**USE WHEN:**
> Recruiter confirms campaign is ready to move forward; current stage goals are met; time-based trigger fires; recruiter says "avançar campanha para próxima etapa".

**DO NOT USE WHEN:**
> Campaign has not met stage completion criteria; recruiter wants to review progress first (use get_campaign_progress); manually handling individual candidates (use update_candidate_stage).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'requires_hitl', 'audit_trail']` |
| `side_effects` | `['db_write', 'webhook_fired', 'email_sent', 'audit_trail']` |
| `related_tools` | `['get_campaign_progress', 'create_recruitment_campaign', 'bulk_update_candidates_stage']` |
| `allowed_agents` | `['recruitment_campaign', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "campaign_id"
  ],
  "properties": {
    "campaign_id": {
      "type": "string"
    }
  }
}
```

---

### `analyze_company_website`

**Descrição completa:**
> Scrapes the company website (with SSRF guard) and surfaces structured candidate fields (mission, values, benefits, tech_stack) for human review. Does NOT write — gravação só após confirmação humana via save_company_section.

**USE WHEN:**
> Onboarding step "website"; recruiter pastes a URL and asks LIA to "puxar o que dá daqui".

**DO NOT USE WHEN:**
> Site is private/paywalled; recruiter wants live job-board scraping (different domain).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['external_api_call']` |
| `related_tools` | `['process_uploaded_document', 'save_company_section']` |
| `allowed_agents` | `['company_settings', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "company_id",
    "website_url"
  ],
  "properties": {
    "company_id": {
      "type": "string"
    },
    "website_url": {
      "type": "string"
    },
    "user_id": {
      "type": "string"
    }
  }
}
```

---

### `analyze_interview_recording`

**Descrição completa:**
> Performs a comprehensive analysis of an interview transcript using multi-dimensional frameworks: WSI (Bloom, Dreyfus, CBI, Big Five), bias detection, comparative ranking against other candidates in the same vacancy, strategic hiring opinion, and structured candidate feedback. Requires an interview_id or raw transcript. Consumes LLM credits.

**USE WHEN:**
> WSI or video interview has been completed; recruiter asks for full interview analysis; before HITL hire/reject decision; generating post-interview candidate feedback.

**DO NOT USE WHEN:**
> Only bias check needed (use detect_interview_bias); only opinion needed (use generate_interview_opinion); interview has not been completed; no transcript available.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'fairness_guard', 'credits_consumed', 'audit_trail']` |
| `side_effects` | `['db_write', 'credits_consumed', 'audit_trail']` |
| `related_tools` | `['detect_interview_bias', 'generate_interview_opinion', 'generate_candidate_feedback', 'compare_interview_performance', 'evaluate_with_twin']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analytics']` |
| `scope` | `IN_JOB` |
| `version` | `2.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "interview_id": {
      "type": "string",
      "description": "UUID da entrevista (busca do banco)"
    },
    "transcript": {
      "type": "string",
      "description": "Transcrição inline (fallback)"
    },
    "candidate_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "interviewer_name": {
      "type": "string"
    },
    "interview_type": {
      "type": "string",
      "enum": [
        "behavioral",
        "technical",
        "cultural",
        "final"
      ]
    },
    "include_bias": {
      "type": "boolean",
      "default": true
    },
    "include_comparative": {
      "type": "boolean",
      "default": true
    },
    "include_opinion": {
      "type": "boolean",
      "default": true
    },
    "include_feedback": {
      "type": "boolean",
      "default": true
    }
  }
}
```

---

### `analyze_skill_gaps`

**Descrição completa:**
> Analyzes the gap between a candidate's skill set and a job's requirements using the skills ontology. Categorizes each job requirement as matched, missing, or transferable (adjacent via ontology) and provides development suggestions. Supports candidate_id and job_id for database-backed analysis or direct skill lists.

**USE WHEN:**
> Evaluating a specific candidate against job requirements; before making a screening decision; generating development feedback for a candidate; HITL decision support.

**DO NOT USE WHEN:**
> Searching for candidates broadly (use search_candidates with skill filters); inferring related skills for job design (use infer_related_skills); mapping skill names (use map_candidate_skills_to_ontology).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['infer_related_skills', 'map_candidate_skills_to_ontology', 'evaluate_with_twin']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'analytics', 'screening']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "candidate_skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "required_skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "candidate_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    }
  }
}
```

---

### `build_dag`

**Descrição completa:**
> Builds and validates a Directed Acyclic Graph (DAG) from a list of task dependencies, detecting cycles and computing topological execution levels. Read-only — does not persist anything. Use to validate a dependency graph before committing to an execution plan.

**USE WHEN:**
> Validating a new task decomposition for cycle-free dependencies; debugging a stuck pipeline; before calling get_execution_plan to check graph integrity first.

**DO NOT USE WHEN:**
> Generating and persisting the full plan (use get_execution_plan); getting next ready tasks (use get_next_tasks); decomposing tasks (use decompose_task).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_execution_plan', 'decompose_task', 'check_dependencies']` |
| `allowed_agents` | `['orchestrator', 'automation']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "task_ids"
  ],
  "properties": {
    "task_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `bulk_update_candidates_stage`

**Descrição completa:**
> Moves a list of candidates to the same target stage within a job vacancy in a single atomic operation. Use for post-screening batch decisions where multiple candidates are advanced or rejected simultaneously. Generates one audit entry per candidate to maintain a full audit trail.

**USE WHEN:**
> After automated screening batch completes; recruiter approves a set of candidates for next stage; mass rejection after final round; HITL bulk approval event.

**DO NOT USE WHEN:**
> Moving a single candidate (use update_candidate_stage for cleaner logging); different target stages per candidate (call update_candidate_stage in sequence); pipeline stats only (use get_pipeline_stats).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'requires_hitl', 'fairness_guard']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['update_candidate_stage', 'reject_candidate', 'get_pipeline_stats']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analyst_feedback']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_ids",
    "target_stage"
  ],
  "properties": {
    "candidate_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "target_stage": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    }
  }
}
```

---

### `calibrate_sourcing_agent`

**Descrição completa:**
> Triggers the calibration flow for an existing sourcing agent, launching the Big Card modal where the recruiter reviews a batch of candidate profiles and rates them as positive or negative examples. The agent updates its scoring model based on this HITL feedback to reduce false positives.

**USE WHEN:**
> Agent has completed initial sourcing run and has candidates to review; recruiter is getting poor quality matches; after major job requirement changes; periodic recalibration cycle.

**DO NOT USE WHEN:**
> Creating a new agent (use create_sourcing_agent); checking agent performance metrics without triggering calibration (use get_agent_status); one-time search (use run_multi_strategy_search).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'requires_hitl']` |
| `side_effects` | `['webhook_fired', 'db_write']` |
| `related_tools` | `['create_sourcing_agent', 'get_agent_status', 'run_multi_strategy_search']` |
| `allowed_agents` | `['agent_studio', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "agent_id"
  ],
  "properties": {
    "agent_id": {
      "type": "string"
    }
  }
}
```

---

### `cancel_interview`

**Descrição completa:**
> Cancels a scheduled interview, records the reason and timestamp for audit purposes, and notifies all participants. Currently simulated — real calendar cancellation and notification require integration. This is a write-destructive action; the interview slot becomes free and must be rescheduled if still needed.

**USE WHEN:**
> Candidate withdraws or is rejected before the interview; interviewer is no longer available and rescheduling is not possible; recruiter says "cancelar entrevista [id]".

**DO NOT USE WHEN:**
> Rescheduling to a different time (use reschedule_interview); candidate is rejected after interview (use reject_candidate); checking interview status (use get_interview_status).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'write_destructive']` |
| `side_effects` | `['db_write', 'email_sent', 'mock_only', 'audit_trail', 'write_destructive']` |
| `related_tools` | `['reschedule_interview', 'get_interview_status', 'reject_candidate']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'interview_scheduling']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    }
  }
}
```

---

### `cancel_vacancy`

**Descrição completa:**
> Cancels a job vacancy with a structured reason code, closes the pipeline, and updates the vacancy status to cancelled. Sends notifications to candidates in active stages if configured. This is a write-destructive action — cancelled vacancies cannot be easily reopened.

**USE WHEN:**
> Budget cut eliminates the position; role filled internally; position restructured; recruiter says "cancelar vaga", "encerrar processo seletivo".

**DO NOT USE WHEN:**
> Temporarily pausing (use pause_vacancy); job was filled (use confirm_placement); updating job requirements (use update_job).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'requires_hitl', 'audit_trail', 'write_destructive']` |
| `side_effects` | `['db_write', 'email_sent', 'audit_trail', 'write_destructive']` |
| `related_tools` | `['pause_vacancy', 'confirm_placement', 'update_job']` |
| `allowed_agents` | `['job_planner', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id",
    "reason"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "reason": {
      "type": "string",
      "enum": [
        "budget_cut",
        "position_eliminated",
        "internal_hire",
        "other"
      ]
    }
  }
}
```

---

### `capture_wizard_feedback`

**Descrição completa:**
> Records recruiter feedback and satisfaction rating about the job creation wizard experience, categorized by feedback type (e.g., suggestions, bugs, praise). Writes to the feedback table for product improvement tracking — does NOT affect job data.

**USE WHEN:**
> End of wizard session; recruiter explicitly provides feedback; post-wizard NPS prompt; recruiter complains about or praises the wizard experience mid-session.

**DO NOT USE WHEN:**
> Feedback about a candidate (different tool); feedback about interview results; recording a hiring outcome (use record_hiring_outcome).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['record_hiring_outcome', 'generate_enriched_jd']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "feedback_type",
    "rating"
  ],
  "properties": {
    "feedback_type": {
      "type": "string"
    },
    "rating": {
      "type": "integer"
    },
    "comment": {
      "type": "string"
    }
  }
}
```

---

### `check_dependencies`

**Descrição completa:**
> Checks the dependency completion status for a specific planned task, returning which prerequisite tasks are done, pending, or blocked. Use to determine if a task is ready to start before dispatching it to the appropriate specialist agent.

**USE WHEN:**
> Orchestrator is about to start a task and needs to confirm all dependencies are met; debugging why a task is not being picked up; validating execution readiness.

**DO NOT USE WHEN:**
> Getting the full dependency graph (use build_dag); retrieving multiple ready tasks at once (use get_next_tasks); generating an execution plan (use get_execution_plan).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['build_dag', 'get_next_tasks', 'get_execution_plan']` |
| `allowed_agents` | `['orchestrator', 'automation']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "task_id"
  ],
  "properties": {
    "task_id": {
      "type": "string"
    }
  }
}
```

---

### `check_interviewer_availability`

**Descrição completa:**
> Checks calendar availability for an interviewer over a specified date range, returning available and busy time slots. Currently uses a deterministic simulation stub — replace with real Google Calendar or Outlook integration in production. Use before scheduling an interview to confirm slot availability.

**USE WHEN:**
> Before scheduling an interview to find open slots; recruiter asks "quando [entrevistador] está disponível?"; automatic interview scheduling flow; candidate proposes dates and agent checks feasibility.

**DO NOT USE WHEN:**
> Scheduling the interview (use schedule_interview after confirming availability); checking candidate availability (different operation); post-scheduling status (use get_interview_status).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['external_api_call', 'mock_only']` |
| `related_tools` | `['schedule_interview', 'get_interview_status']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'interview_scheduling']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interviewer_id",
    "date_range"
  ],
  "properties": {
    "interviewer_id": {
      "type": "string"
    },
    "date_range": {
      "type": "string",
      "description": "Format: 'YYYY-MM-DD to YYYY-MM-DD'"
    }
  }
}
```

---

### `check_job_draft_health`

**Descrição completa:**
> Avalia proativamente a saúde do rascunho da vaga — identifica campos faltantes, salário abaixo do mercado, poucas skills ou responsabilidades vagas. Retorna lista de risks + suggestions. Use antes de publicar.

**USE WHEN:**
> User signals readiness to publish the draft, or wants a sanity check on an in-progress draft. Also useful periodically during wizard flow.

**DO NOT USE WHEN:**
> Draft has just been created and not yet enriched — wait for user to fill core fields first.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['validate_job_requirements', 'enrich_job_description', 'suggest_jd_improvements']` |
| `allowed_agents` | `['job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "title"
  ],
  "properties": {
    "title": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    },
    "salary_min": {
      "type": "number"
    },
    "salary_max": {
      "type": "number"
    },
    "skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "responsibilities": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `compare_interview_performance`

**Descrição completa:**
> Compares a candidate's interview performance against all other candidates who have interviewed for the same vacancy, producing a ranked comparison with benchmarks, percentile scores, and differentiating insights. Use to contextualize individual performance within the full applicant pool.

**USE WHEN:**
> Recruiter asks "como esse candidato se compara aos outros?"; before final shortlist decision; hiring manager wants relative ranking; after multiple interviews are complete.

**DO NOT USE WHEN:**
> Only one candidate has been interviewed (no comparison possible); generating individual feedback (use generate_candidate_feedback); full analysis (use analyze_interview_recording).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['analyze_interview_recording', 'generate_interview_opinion', 'get_vacancy_funnel']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analytics']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    }
  }
}
```

---

### `confirm_autonomous_action`

**Descrição completa:**
> Approves a pending autonomous action for immediate execution. Once confirmed, the action executes with the same parameters LIA prepared. Creates a HITL approval audit entry. This is the mandatory HITL gate for autonomous operations that write data or contact candidates.

**USE WHEN:**
> Recruiter reviews pending action and approves it; HITL approval workflow step; bulk confirmation of low-risk actions; recruiter says "pode executar essa ação".

**DO NOT USE WHEN:**
> Action should be rejected (use reject_autonomous_action); reviewing actions without deciding (use get_autonomous_actions); executing a tool directly without HITL.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'requires_hitl', 'audit_trail']` |
| `side_effects` | `['db_write', 'webhook_fired', 'audit_trail']` |
| `related_tools` | `['reject_autonomous_action', 'get_autonomous_actions', 'get_proactive_alerts']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "action_id"
  ],
  "properties": {
    "action_id": {
      "type": "string"
    }
  }
}
```

---

### `confirm_placement`

**Descrição completa:**
> Marks a candidate as hired, closes the vacancy (or reduces headcount target), and records the hiring outcome for learning analytics. Creates a permanent hire record. Triggers onboarding integration if configured. This is a terminal action for the vacancy.

**USE WHEN:**
> Offer has been accepted; recruiter confirms the hire; closing the recruitment cycle for a position; recruiter says "contratar [candidato]", "fechar vaga".

**DO NOT USE WHEN:**
> Offer letter hasn't been signed; candidate needs more evaluation; pausing the vacancy (use pause_vacancy); cancelling without a hire (use cancel_vacancy).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'requires_hitl', 'audit_trail']` |
| `side_effects` | `['db_write', 'webhook_fired', 'audit_trail']` |
| `related_tools` | `['create_offer_letter', 'cancel_vacancy', 'record_hiring_outcome']` |
| `allowed_agents` | `['pipeline_action', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "job_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "start_date": {
      "type": "string"
    }
  }
}
```

---

### `create_digital_twin`

**Descrição completa:**
> Creates a Digital Twin agent from a Subject Matter Expert (SME) user, capturing their evaluation reasoning, scoring criteria, and interview patterns via RAG. The twin can later evaluate candidates as if the SME were conducting the interview. Writes twin profile to the database.

**USE WHEN:**
> SME wants their judgment to scale across all candidates; senior recruiter or domain expert wants to automate their screening logic; company has a valued interviewer whose patterns should be preserved.

**DO NOT USE WHEN:**
> Evaluating a candidate with an existing twin (use evaluate_with_twin); listing available twins (use list_digital_twins); standard AI screening without personalization.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'credits_consumed']` |
| `related_tools` | `['evaluate_with_twin', 'list_digital_twins', 'calibrate_sourcing_agent']` |
| `allowed_agents` | `['digital_twin', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "twin_name"
  ],
  "properties": {
    "twin_name": {
      "type": "string"
    },
    "sme_user_id": {
      "type": "string"
    },
    "specialties": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `create_job`

**Descrição completa:**
> Creates a new job vacancy record in the database with the provided title, description, requirements, and optional fields. Returns the new job_id. Use only when all required data has been confirmed — prefer save_job_draft for work-in-progress. Increments the company's active vacancy count for quota enforcement.

**USE WHEN:**
> Recruiter confirms all required fields and explicitly wants to create the vacancy; wizard flow is complete and data is validated; job is being created programmatically from an approved template.

**DO NOT USE WHEN:**
> Data is still being collected (use save_job_draft); recruiter wants to review before committing; updating an existing vacancy (use update_job); publishing immediately without review (create first, then publish_job separately).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail', 'quota_consumed']` |
| `related_tools` | `['save_job_draft', 'validate_job_fields', 'publish_job', 'update_job']` |
| `allowed_agents` | `['orchestrator', 'job_planner', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "title",
    "description"
  ],
  "properties": {
    "title": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "department": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "salary_range": {
      "type": "object"
    },
    "requirements": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `create_job_draft`

**Descrição completa:**
> Cria um NOVO rascunho de vaga em memória com os requisitos extraídos, para revisão do recruiter. NÃO publica diretamente. Retorna draft que precisa passar por save_job_draft após confirmação.

**USE WHEN:**
> After extract_job_requirements produces structured output. The draft is in-memory only — user reviews before save_job_draft persists it.

**DO NOT USE WHEN:**
> Job already exists — use update_job_vacancy instead. Direct persistence desired — use save_job_draft with full spec.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['extract_job_requirements', 'validate_job_requirements', 'save_job_draft']` |
| `allowed_agents` | `['job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "title"
  ],
  "properties": {
    "title": {
      "type": "string"
    },
    "skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "work_model": {
      "type": "string",
      "enum": [
        "Remoto",
        "Híbrido",
        "Presencial"
      ]
    },
    "seniority": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "salary_min": {
      "type": "number"
    },
    "salary_max": {
      "type": "number"
    },
    "company_id": {
      "type": "string",
      "description": "Auto-injected from session"
    }
  }
}
```

---

### `create_nurture_sequence`

**Descrição completa:**
> Creates an automated multi-channel nurture sequence to engage passive candidates over time with configurable touchpoints (email, WhatsApp, LinkedIn). Supports four predefined templates (tech_talent, leadership, silver_medalist, general) or custom naming. Sequences run automatically in the background after creation.

**USE WHEN:**
> Recruiter wants long-term engagement with passive candidates in a pool; silver medalists should be kept warm for future openings; talent pool requires ongoing nurture between campaigns.

**DO NOT USE WHEN:**
> Immediate one-off communication (use send_email or send_whatsapp); checking engagement metrics (use get_engagement_metrics); active-candidate pipeline management.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'requires_hitl']` |
| `side_effects` | `['db_write', 'email_sent', 'whatsapp_sent', 'audit_trail']` |
| `related_tools` | `['get_engagement_metrics', 'suggest_reengagement', 'send_email']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'communication', 'recruitment_campaign']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_ids"
  ],
  "properties": {
    "candidate_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "template": {
      "type": "string",
      "enum": [
        "tech_talent",
        "leadership",
        "silver_medalist",
        "general"
      ]
    },
    "custom_name": {
      "type": "string"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `create_offer_letter`

**Descrição completa:**
> Generates a structured offer letter document for a selected candidate and job, incorporating the agreed salary, start date, and company-standard terms. The letter is generated as a PDF or structured data but NOT sent automatically — recruiter reviews before delivery. HITL required before sending.

**USE WHEN:**
> Recruiter is ready to make a formal offer; candidate has been approved by hiring manager; final stage of pipeline; recruiter says "gerar carta de oferta para [candidato]".

**DO NOT USE WHEN:**
> Verbal offer negotiation still in progress; candidate hasn't reached offer stage; confirming a hire (use confirm_placement after offer is accepted).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'requires_hitl', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['confirm_placement', 'update_candidate_stage', 'send_email']` |
| `allowed_agents` | `['pipeline_action', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "job_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "salary": {
      "type": "number"
    },
    "start_date": {
      "type": "string"
    }
  }
}
```

---

### `create_recruitment_campaign`

**Descrição completa:**
> Creates an end-to-end recruitment campaign that orchestrates sourcing, screening, nurture sequences, and pipeline actions for a job or talent pool in a single automated workflow. Supports three automation levels: fully automatic, semi-automated with HITL checkpoints, or recruiter-assisted. Writes campaign config to the database.

**USE WHEN:**
> Recruiter wants to launch a full recruitment drive for a position; proactive talent pipeline campaign for an upcoming hiring need; recruiter says "criar campanha para vaga X".

**DO NOT USE WHEN:**
> Quick one-time sourcing run (use run_multi_strategy_search); manual candidate-by-candidate management (use individual tools); checking campaign progress (use get_campaign_progress).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'requires_hitl', 'audit_trail', 'credits_consumed']` |
| `side_effects` | `['db_write', 'webhook_fired', 'credits_consumed', 'audit_trail']` |
| `related_tools` | `['get_campaign_progress', 'advance_campaign_stage', 'create_talent_pool']` |
| `allowed_agents` | `['recruitment_campaign', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "name"
  ],
  "properties": {
    "name": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "talent_pool_id": {
      "type": "string"
    },
    "automation_level": {
      "type": "string",
      "enum": [
        "auto",
        "semi",
        "assisted"
      ]
    }
  }
}
```

---

### `create_sourcing_agent`

**Descrição completa:**
> Creates a persistent AI sourcing agent linked to a job or talent pool, using an optional sector template to pre-configure search strategies and scoring criteria. The agent runs autonomously between sessions, discovering and scoring candidates. Consumes quota credits per run.

**USE WHEN:**
> Recruiter wants ongoing automated sourcing for a hard-to-fill role; talent pool needs continuous population; recruiter says "criar agente de sourcing para [vaga]".

**DO NOT USE WHEN:**
> One-time search (use search_candidates or run_multi_strategy_search); calibrating an existing agent (use calibrate_sourcing_agent); listing existing agents (use get_agent_status).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'credits_consumed', 'audit_trail']` |
| `side_effects` | `['db_write', 'credits_consumed', 'audit_trail']` |
| `related_tools` | `['calibrate_sourcing_agent', 'run_multi_strategy_search', 'get_agent_status']` |
| `allowed_agents` | `['agent_studio', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "agent_name"
  ],
  "properties": {
    "agent_name": {
      "type": "string"
    },
    "sector_template": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "talent_pool_id": {
      "type": "string"
    }
  }
}
```

---

### `create_talent_pool`

**Descrição completa:**
> Creates a new live talent pool in the tenant's account with an optional archetype (persona template) to guide automated sourcing. The pool is immediately active and can be linked to sourcing agents. Writes to the talent_pools table.

**USE WHEN:**
> Recruiter wants a dedicated pool for a recurring role type; launching a proactive sourcing initiative; organizing candidates by archetype (e.g., "Líderes de Produto").

**DO NOT USE WHEN:**
> Adding candidates to an existing pool (use add_to_talent_pool); creating a single job vacancy (use create_job); listing existing pools (use list_talent_pools).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['add_to_talent_pool', 'list_talent_pools', 'create_sourcing_agent']` |
| `allowed_agents` | `['talent_pool', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "name"
  ],
  "properties": {
    "name": {
      "type": "string"
    },
    "archetype_id": {
      "type": "string"
    },
    "description": {
      "type": "string"
    }
  }
}
```

---

### `decompose_task`

**Descrição completa:**
> Decomposes a complex recruitment or workflow task into executable subtasks using an LLM with a structured planning prompt. Automatically assigns agent types, priorities, estimated durations, and dependency chains. Optionally persists the subtasks to the database via PlannedTaskService. Use for any multi-step workflow that requires orchestration across multiple agents.

**USE WHEN:**
> Recruiter or orchestrator has a high-level goal requiring multiple specialized agents (e.g., "open and fill a senior engineer role in 30 days"); automation domain receives a complex task; goal planning step at the start of an autonomous pipeline.

**DO NOT USE WHEN:**
> Simple single-step tasks with no dependencies (use the specific tool directly); already have a decomposed task list (use get_execution_plan or prioritize_tasks); previewing only without persisting (pass persist=False).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'credits_consumed']` |
| `related_tools` | `['prioritize_tasks', 'get_execution_plan', 'build_dag']` |
| `allowed_agents` | `['orchestrator', 'automation']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "task_description"
  ],
  "properties": {
    "task_description": {
      "type": "string"
    },
    "goal_id": {
      "type": "string"
    },
    "parent_task_id": {
      "type": "string"
    },
    "deadline": {
      "type": "string"
    },
    "persist": {
      "type": "boolean",
      "default": true
    }
  }
}
```

---

### `detect_interview_bias`

**Descrição completa:**
> Detects potential bias patterns in an interview transcript using linguistic pattern analysis and LLM-based evaluation. Identifies age, gender, appearance, affinity, and illegal question bias. Returns a structured bias report with evidence citations. Always runs as part of FairnessGuard pipeline.

**USE WHEN:**
> Post-interview compliance check; FairnessGuard pipeline trigger; recruiter requests bias audit; HR policy requires bias screening before final decision.

**DO NOT USE WHEN:**
> Full interview analysis needed (use analyze_interview_recording which includes bias); no interview transcript available; candidate screening without an interview (different stage).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'fairness_guard', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['analyze_interview_recording', 'generate_interview_opinion']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analytics']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    },
    "use_llm": {
      "type": "boolean",
      "default": true
    }
  }
}
```

---

### `detect_pending_decisions`

**Descrição completa:**
> Scans the pipeline for hiring manager decisions that are overdue based on SLA configuration, identifies the bottlenecks, and optionally sends escalation notifications to the responsible parties. Use to maintain pipeline velocity and enforce decision SLAs.

**USE WHEN:**
> SLA monitoring scheduled run; recruiter asks "o que está pendente de decisão?"; end-of-week pipeline review; before escalating to hiring managers.

**DO NOT USE WHEN:**
> Viewing general pipeline stats (use get_pipeline_stats); checking autonomous actions (use get_autonomous_actions); sending a specific notification (use send_email).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['email_sent', 'audit_trail']` |
| `related_tools` | `['get_proactive_alerts', 'get_pipeline_stats', 'send_email']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "send_notifications": {
      "type": "boolean",
      "default": false
    }
  }
}
```

---

### `evaluate_with_twin`

**Descrição completa:**
> Evaluates a candidate using a Digital Twin's internalized reasoning model, producing a structured assessment that mirrors how the SME would judge the candidate. Uses RAG few-shot retrieval to apply historical evaluation patterns. Result includes score, evidence, and recommendation. Counts against credits.

**USE WHEN:**
> Candidate is at a stage where the SME's judgment should be simulated; scaling expert evaluation to many candidates; consistency check before final HITL review; recruiter says "avaliar com o twin do [nome]".

**DO NOT USE WHEN:**
> No existing digital twin (use analyze_interview_recording for standard AI analysis); final hiring decision (always requires HITL); creating a new twin (use create_digital_twin).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'requires_hitl', 'fairness_guard', 'credits_consumed', 'audit_trail']` |
| `side_effects` | `['db_write', 'credits_consumed', 'audit_trail']` |
| `related_tools` | `['create_digital_twin', 'analyze_interview_recording', 'generate_interview_opinion']` |
| `allowed_agents` | `['digital_twin', 'cv_screening', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "twin_id",
    "candidate_id"
  ],
  "properties": {
    "twin_id": {
      "type": "string"
    },
    "candidate_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    }
  }
}
```

---

### `export_candidates`

**Descrição completa:**
> Exports candidate profile data for a list of candidate IDs to CSV or Excel format, with configurable field selection. The resulting file contains PII and should only be generated when the recruiter explicitly requests an export. Logs the export event for LGPD compliance audit.

**USE WHEN:**
> Recruiter explicitly requests to export candidate data; sharing shortlist with hiring manager offline; bulk data transfer to external ATS; compliance-requested data extraction.

**DO NOT USE WHEN:**
> Recruiter wants to view data on screen (use search_candidates or get_candidate_details); syncing to external ATS automatically (use ats_sync_candidate); generating a report (use generate_report).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'requires_hitl']` |
| `side_effects` | `['audit_trail', 'external_api_call']` |
| `related_tools` | `['search_candidates', 'generate_report', 'get_candidate_details']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "candidate_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "format": {
      "type": "string",
      "enum": [
        "csv",
        "xlsx"
      ]
    },
    "fields": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `extract_job_requirements`

**Descrição completa:**
> Extrai requisitos estruturados de uma descrição de vaga em texto livre (skills, modalidade, senioridade) usando IA. Primeiro passo do fluxo wizard — converte input não estruturado em dados prontos para create_job_draft.

**USE WHEN:**
> Wizard agent receives unstructured job description or user request to create a job. Use this BEFORE create_job_draft to structure the fields.

**DO NOT USE WHEN:**
> Job is already structured in the session context; skip to create_job_draft. External JD import should use import_job_description tool instead.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['create_job_draft', 'validate_job_requirements', 'enrich_job_description']` |
| `allowed_agents` | `['job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "text"
  ],
  "properties": {
    "text": {
      "type": "string",
      "description": "Texto da descrição ou input do usuário"
    },
    "title": {
      "type": "string",
      "description": "Título do cargo se já identificado"
    }
  }
}
```

---

### `forecast_hiring_needs`

**Descrição completa:**
> Forecasts hiring needs for a given period by combining historical turnover data, current pipeline velocity, growth targets, and seasonal patterns. Returns projected headcount requirements per department, including backfill and net-new positions. Read-only planning output — does not create any jobs.

**USE WHEN:**
> Quarterly or annual headcount planning; recruiter or HR director asks "quantas contratações precisamos para Q3?"; board presentation preparation; budget justification for hiring team.

**DO NOT USE WHEN:**
> Real-time vacancy management (use search_jobs / get_pipeline_stats); generating a single report (use generate_report); current pipeline status (not planning).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_pipeline_stats', 'generate_report', 'get_candidate_stats']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "period": {
      "type": "string",
      "enum": [
        "month",
        "quarter",
        "half_year",
        "year"
      ]
    },
    "department": {
      "type": "string"
    },
    "growth_rate": {
      "type": "number"
    },
    "include_backfills": {
      "type": "boolean"
    }
  }
}
```

---

### `generate_candidate_feedback`

**Descrição completa:**
> Generates a structured, constructive, and empathetic feedback message for a candidate after their interview, referencing specific strengths, development areas, and next steps. The feedback is designed to be sent directly to the candidate and follows WeDO communication standards.

**USE WHEN:**
> Interview is complete and recruiter wants to provide feedback to the candidate; post-rejection courtesy feedback; offering development guidance to rejected candidates; recruiter says "gerar feedback para o candidato".

**DO NOT USE WHEN:**
> Interview has not been analyzed yet (run analyze_interview_recording first); internal hiring opinion (use generate_interview_opinion); sending the feedback (use send_email or send_whatsapp after generating).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'credits_consumed']` |
| `side_effects` | `['credits_consumed']` |
| `related_tools` | `['analyze_interview_recording', 'generate_interview_opinion', 'send_email']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analytics']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    }
  }
}
```

---

### `generate_enriched_jd`

**Descrição completa:**
> Generates a complete, bias-audited, market-aligned job description from collected fields and available market data. Output includes structured sections (role summary, responsibilities, requirements, benefits) following WeDO inclusivity standards. Does not persist — combine with save_job_draft or create_job to store.

**USE WHEN:**
> Recruiter has confirmed core fields and wants a polished, publishable JD; final wizard step before review; recruiter asks LIA to "escrever a descrição completa".

**DO NOT USE WHEN:**
> Recruiter wants only suggestions or improvements (use get_job_suggestions); JD is already written and recruiter only wants to save it; generating candidate content.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'fairness_guard']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_job_suggestions', 'save_job_draft', 'create_job', 'validate_job_fields']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "fields"
  ],
  "properties": {
    "fields": {
      "type": "object"
    },
    "tone": {
      "type": "string"
    }
  }
}
```

---

### `generate_interview_opinion`

**Descrição completa:**
> Generates a structured strategic hiring opinion based on an interview analysis, returning one of three verdicts: CONTRATAR / NÃO CONTRATAR / AVALIAR MAIS, each supported by evidence citations from the transcript and alignment with job requirements. Does NOT make the decision — provides decision support for HITL.

**USE WHEN:**
> After interview analysis; before HITL hire/reject decision; recruiter asks "o que você acha desse candidato?"; generating summary for hiring manager review.

**DO NOT USE WHEN:**
> No interview analysis exists (run analyze_interview_recording first); final hiring decision (must be HITL); generating candidate feedback (use generate_candidate_feedback).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'requires_hitl', 'fairness_guard', 'credits_consumed', 'audit_trail']` |
| `side_effects` | `['db_write', 'credits_consumed', 'audit_trail']` |
| `related_tools` | `['analyze_interview_recording', 'generate_candidate_feedback', 'compare_interview_performance']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analytics']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    }
  }
}
```

---

### `generate_report`

**Descrição completa:**
> Generates a recruitment analytics report covering the specified date range and scope, in PDF, CSV, or JSON format. Reports include KPIs, funnel metrics, time-to-fill, diversity stats, and hiring quality indicators. Does not store in DB by default — returns a download URL or inline data.

**USE WHEN:**
> Recruiter asks for a report; end-of-month KPI review; board presentation prep; compliance reporting; comparing performance across periods.

**DO NOT USE WHEN:**
> Real-time pipeline view (use get_pipeline_stats); scheduling recurring reports (use schedule_report); individual candidate report (use export_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['external_api_call', 'audit_trail']` |
| `related_tools` | `['schedule_report', 'get_pipeline_stats', 'get_candidate_stats', 'export_candidates']` |
| `allowed_agents` | `['orchestrator', 'analytics']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "report_type"
  ],
  "properties": {
    "report_type": {
      "type": "string"
    },
    "date_from": {
      "type": "string"
    },
    "date_to": {
      "type": "string"
    },
    "format": {
      "type": "string",
      "enum": [
        "pdf",
        "csv",
        "json"
      ]
    }
  }
}
```

---

### `get_agent_status`

**Descrição completa:**
> Returns the current status, active search strategy, performance metrics (candidates found, qualified, conversion rate), and last-run timestamp for a sourcing agent. Read-only — does not trigger any agent action.

**USE WHEN:**
> Recruiter asks "como está o agente X?"; monitoring dashboard; before deciding to calibrate or pause; checking if agent is healthy or stuck.

**DO NOT USE WHEN:**
> Triggering calibration (use calibrate_sourcing_agent); running a search now (use run_multi_strategy_search); checking analytics metrics (use analytics tools).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['calibrate_sourcing_agent', 'create_sourcing_agent', 'run_multi_strategy_search']` |
| `allowed_agents` | `['agent_studio', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "agent_id"
  ],
  "properties": {
    "agent_id": {
      "type": "string"
    }
  }
}
```

---

### `get_autonomous_actions`

**Descrição completa:**
> Lists autonomous actions that LIA has executed or is waiting for recruiter confirmation to execute. Pending actions require HITL approval before running. Use to review what LIA has done or is planning to do autonomously.

**USE WHEN:**
> Recruiter wants to review LIA's autonomous activities; HITL check at start of session; audit of automated actions for the day; before approving or rejecting a batch.

**DO NOT USE WHEN:**
> Proactive alert view (use get_proactive_alerts); approving a specific action (use confirm_autonomous_action); rejecting an action (use reject_autonomous_action).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['none']` |
| `related_tools` | `['confirm_autonomous_action', 'reject_autonomous_action', 'get_proactive_alerts']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": [
        "pending",
        "executed",
        "all"
      ]
    }
  }
}
```

---

### `get_campaign_progress`

**Descrição completa:**
> Returns the current stage, completion percentage, candidate funnel counts, and activity timeline for an active recruitment campaign. Use to monitor campaign health and decide whether to advance to the next stage.

**USE WHEN:**
> Recruiter asks "como está a campanha?"; monitoring dashboard; before advancing campaign stage; detecting if campaign is stuck or needs intervention.

**DO NOT USE WHEN:**
> Creating a campaign (use create_recruitment_campaign); advancing stage (use advance_campaign_stage); generic pipeline stats (use get_pipeline_stats).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['create_recruitment_campaign', 'advance_campaign_stage', 'get_pipeline_stats']` |
| `allowed_agents` | `['recruitment_campaign', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "campaign_id"
  ],
  "properties": {
    "campaign_id": {
      "type": "string"
    }
  }
}
```

---

### `get_candidate_details`

**Descrição completa:**
> Retrieves the complete profile for a specific candidate including personal data, skills, work history, WSI scores, pipeline history, and engagement signals. Optionally includes the full stage transition history. Use when you need the full context on a known candidate to support a decision.

**USE WHEN:**
> After finding a candidate in search results; recruiter says "ver mais sobre [nome]"; before making a stage decision; before generating interview opinion; HITL review step.

**DO NOT USE WHEN:**
> Searching for candidates (use search_candidates); aggregate stats (use get_candidate_stats); pipeline funnel overview (use get_vacancy_funnel). Contains PII — check consent before displaying.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['none']` |
| `related_tools` | `['search_candidates', 'update_candidate_stage', 'analyze_interview_recording']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analytics']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "include_history": {
      "type": "boolean"
    }
  }
}
```

---

### `get_candidate_stats`

**Descrição completa:**
> Returns aggregate statistical summaries about the tenant's candidate pool, such as skill distribution, seniority breakdown, availability percentages, and score histograms. Supports optional grouping and filtering. Use for dashboard and analytical views, not individual candidate lookup.

**USE WHEN:**
> Recruiter wants overview of talent pool composition; analytics dashboard load; before launching sourcing campaign to understand existing coverage; reporting.

**DO NOT USE WHEN:**
> Looking for individual candidates (use search_candidates); pipeline-level stats per vacancy (use get_pipeline_stats); detailed funnel analysis (use get_vacancy_funnel).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_pipeline_stats', 'search_candidates', 'generate_report']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "filters": {
      "type": "object"
    },
    "group_by": {
      "type": "string"
    }
  }
}
```

---

### `get_company_config`

**Descrição completa:**
> Retrieves company-level configuration including hiring workflow stages, approval requirements, default pipeline settings, and integration preferences for the tenant. Use this to tailor agent behavior to the company's specific recruiting process.

**USE WHEN:**
> Before building a job or pipeline to know approval requirements; checking if HITL approval is required; agent needs company-specific workflow stages or SLA config.

**DO NOT USE WHEN:**
> Fetching candidate or job data (use search_candidates / get_job_details); checking user permissions (use auth context); retrieving billing info (use billing tools).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['validate_job_fields', 'create_job', 'get_pipeline_stats']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "config_type": {
      "type": "string"
    }
  }
}
```

---

### `get_engagement_metrics`

**Descrição completa:**
> Returns engagement analytics for one or all nurture sequences, including open rates, click-through rates, reply rates, and conversion rates (passive → applicant → hired). Use to evaluate which nurture templates and touchpoints are most effective.

**USE WHEN:**
> Recruiter asks "como está performando nossa sequência de nurture?"; monthly engagement review; optimizing templates based on conversion data; campaign ROI analysis.

**DO NOT USE WHEN:**
> Creating a nurture sequence (use create_nurture_sequence); re-engaging specific inactive candidates (use suggest_reengagement); general pipeline analytics (use get_pipeline_stats).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['create_nurture_sequence', 'suggest_reengagement', 'get_pipeline_stats']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics', 'recruitment_campaign']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "sequence_id": {
      "type": "string"
    },
    "period": {
      "type": "string",
      "enum": [
        "week",
        "month",
        "quarter"
      ]
    }
  }
}
```

---

### `get_execution_plan`

**Descrição completa:**
> Generates a structured execution plan with parallel levels from a set of planned tasks, validates the dependency DAG for cycles, and persists the plan to the database. Returns the plan with its parallel execution levels and any cycle warnings. Use to prepare the final, validated execution schedule before starting an autonomous pipeline.

**USE WHEN:**
> Tasks are decomposed and prioritized, and the orchestrator is ready to start executing; recruiter asks "qual é o plano de execução?"; before dispatching tasks to specialist agents.

**DO NOT USE WHEN:**
> Tasks haven't been decomposed yet (use decompose_task first); just checking dependencies without a plan (use build_dag); retrieving next ready tasks during execution (use get_next_tasks).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['decompose_task', 'build_dag', 'get_next_tasks', 'prioritize_tasks']` |
| `allowed_agents` | `['orchestrator', 'automation']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "task_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "goal_id": {
      "type": "string"
    },
    "name": {
      "type": "string"
    }
  }
}
```

---

### `get_external_applications`

**Descrição completa:**
> Imports applications received from external job boards for a specific vacancy, creating candidate profiles and VacancyCandidate records for new applicants. Deduplicates against existing profiles. Should be run periodically or on-demand to sync inbound applications from external channels.

**USE WHEN:**
> After publishing to external job boards; syncing applications from LinkedIn/Indeed; recruiter asks "importar candidatos do [board]"; scheduled sync job.

**DO NOT USE WHEN:**
> Searching existing candidates (use search_candidates); adding a known candidate manually (use add_candidate_to_vacancy); ATS full sync (use ats_pull_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write', 'external_api_call', 'audit_trail']` |
| `related_tools` | `['publish_to_job_board', 'add_candidate_to_vacancy', 'search_candidates']` |
| `allowed_agents` | `['sourcing', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "board": {
      "type": "string"
    }
  }
}
```

---

### `get_intelligent_salary`

**Descrição completa:**
> Returns AI-calibrated salary range suggestions by combining real-time external market data with the company's internal budget history and approved compensation bands. Produces a contextual recommendation rather than raw benchmark data, reducing negotiation risk and aligning with budget constraints.

**USE WHEN:**
> Wizard salary step; recruiter is uncertain about compensation range and wants a calibrated suggestion that respects both market and internal budget; final salary confirmation before saving job.

**DO NOT USE WHEN:**
> Recruiter has already decided on salary (just use save_job_draft / create_job); pure market benchmark needed without internal context (use search_salary_benchmark).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['external_api_call']` |
| `related_tools` | `['search_salary_benchmark', 'validate_job_fields', 'save_job_draft']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_title"
  ],
  "properties": {
    "job_title": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    },
    "location": {
      "type": "string"
    }
  }
}
```

---

### `get_intelligent_skills`

**Descrição completa:**
> Generates a prioritized and deduplicated skill list for a given job title and seniority using the LIA skills ontology, past job postings, and market signals. Helps recruiters avoid overfitting to their own vocabulary and surfaces adjacent or emerging skills.

**USE WHEN:**
> Recruiter starts skills section of job creation wizard; job title is known but recruiter is unsure which skills to require; improving an existing requirement list.

**DO NOT USE WHEN:**
> Skills have already been confirmed; deep ontology traversal needed (use infer_related_skills or get_skill_adjacencies); analyzing candidate skills vs job requirements (use analyze_skill_gaps).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'fairness_guard']` |
| `side_effects` | `['none']` |
| `related_tools` | `['infer_related_skills', 'get_job_suggestions', 'validate_job_fields']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_title"
  ],
  "properties": {
    "job_title": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    },
    "industry": {
      "type": "string"
    }
  }
}
```

---

### `get_interview_status`

**Descrição completa:**
> Retrieves the current status and details of an interview by its ID. Status values are: scheduled, completed, cancelled, pending. Currently uses a deterministic simulation — real status requires integration with the interview management database. Use to check if an interview has been completed before triggering post-interview analysis.

**USE WHEN:**
> Before calling analyze_interview_recording to verify the interview is complete; recruiter asks "qual o status da entrevista [id]?"; pipeline automation checks interview completion to unlock the next stage.

**DO NOT USE WHEN:**
> Analyzing interview results (use analyze_interview_recording); scheduling a new interview (use schedule_interview); checking interviewer availability (use check_interviewer_availability).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['mock_only']` |
| `related_tools` | `['analyze_interview_recording', 'schedule_interview', 'reschedule_interview']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'interview_scheduling']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    }
  }
}
```

---

### `get_job_details`

**Descrição completa:**
> Returns the full record for a specific job vacancy including title, description, requirements, skills, salary range, pipeline stages, and optionally the list of associated candidates. Use when you need the complete job context before taking an action or generating content.

**USE WHEN:**
> Recruiter references a specific job_id; before generating a JD update; before publishing to a board; HITL approval requiring full job context; before sourcing.

**DO NOT USE WHEN:**
> Searching for jobs by name (use search_jobs); pipeline stats only (use get_pipeline_stats); candidate list without job context (use search_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['search_jobs', 'get_pipeline_stats', 'update_job', 'publish_job']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics', 'job_planner']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "include_candidates": {
      "type": "boolean"
    }
  }
}
```

---

### `get_job_suggestions`

**Descrição completa:**
> Generates AI-powered improvement suggestions for a job description or requirements list, including bias warnings, unclear language, missing sections, and competitive positioning tips. Use this when the recruiter has drafted a description and wants quality or inclusivity feedback.

**USE WHEN:**
> Recruiter provides initial job description; wizard step for description quality check; recruiter asks "está bom assim?" or "como melhorar a descrição?".

**DO NOT USE WHEN:**
> Job is already published and recruiter does not plan to edit it; recruiter wants salary data (use search_salary_benchmark); recruiter wants to generate the full JD from scratch (use generate_enriched_jd).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'fairness_guard']` |
| `side_effects` | `['none']` |
| `related_tools` | `['generate_enriched_jd', 'validate_job_fields', 'search_salary_benchmark']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_title"
  ],
  "properties": {
    "job_title": {
      "type": "string"
    },
    "current_description": {
      "type": "string"
    },
    "industry": {
      "type": "string"
    }
  }
}
```

---

### `get_learning_insights`

**Descrição completa:**
> Returns patterns and insights derived from historical hiring outcomes, including which skills, sourcing channels, and screening criteria most reliably predicted successful hires for a given role and seniority. Helps recruiters refine future screening criteria and sourcing strategies.

**USE WHEN:**
> Recruiter is opening a new role and wants to know what worked before; calibrating screening criteria; strategy planning based on past data; recruiter asks "o que funcionou para esse perfil antes?".

**DO NOT USE WHEN:**
> Recording a new hiring outcome (use record_hiring_outcome); real-time pipeline analytics (use get_pipeline_stats); forecasting future hiring needs (use forecast_hiring_needs).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['record_hiring_outcome', 'forecast_hiring_needs', 'get_pipeline_stats']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "role": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    }
  }
}
```

---

### `get_market_intelligence`

**Descrição completa:**
> Retrieves real-time market intelligence for a given job role by combining web search with LLM parsing to surface: external salary benchmarks, demand trends, in-demand skill shifts, supply/demand ratios, and competitive landscape analysis. Results are richer but slower and costlier than get_intelligent_salary.

**USE WHEN:**
> Recruiter wants a comprehensive market analysis before opening a new position; salary negotiation context; sourcing strategy planning; recruiter asks "como está o mercado para [cargo]?".

**DO NOT USE WHEN:**
> Quick salary estimate only (use search_salary_benchmark or get_intelligent_salary); candidate skills analysis (use infer_related_skills); job exists and only needs update.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'credits_consumed']` |
| `side_effects` | `['external_api_call', 'credits_consumed']` |
| `related_tools` | `['search_salary_benchmark', 'get_intelligent_salary', 'infer_related_skills']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'analyst_feedback', 'wsi_evaluator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "job_title": {
      "type": "string",
      "description": "Job title to research"
    },
    "seniority": {
      "type": "string",
      "description": "Seniority level (Junior, Pleno, Senior)"
    },
    "location": {
      "type": "string",
      "description": "Location for regional adjustment"
    },
    "industry": {
      "type": "string",
      "description": "Industry sector"
    },
    "include_trends": {
      "type": "boolean",
      "default": true
    }
  },
  "required": [
    "job_title"
  ]
}
```

---

### `get_next_tasks`

**Descrição completa:**
> Returns the list of planned tasks that are ready for execution (all dependencies completed, not yet started), filtered by goal, agent type, and company. Use to drive the autonomous execution loop — call repeatedly to pick up tasks as they become available.

**USE WHEN:**
> Orchestrator's main execution loop polling for work; agent checks if there are pending tasks before going idle; after completing a task, checking if any newly unblocked tasks are ready.

**DO NOT USE WHEN:**
> Decomposing tasks (use decompose_task); checking a specific task's dependencies (use check_dependencies); generating the execution plan (use get_execution_plan).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['check_dependencies', 'get_execution_plan', 'prioritize_tasks']` |
| `allowed_agents` | `['orchestrator', 'automation']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "goal_id": {
      "type": "string"
    },
    "parent_task_id": {
      "type": "string"
    },
    "agent_type": {
      "type": "string"
    },
    "limit": {
      "type": "integer",
      "default": 5
    }
  }
}
```

---

### `get_pipeline_stats`

**Descrição completa:**
> Returns stage-by-stage conversion statistics for one or all vacancies over an optional date range, including candidate counts per stage, conversion rates, average time-in-stage, and rejection reasons. Essential for identifying bottlenecks.

**USE WHEN:**
> Recruiter asks "como está o funil?"; analytics dashboard load; detecting SLA bottlenecks; before forecasting time-to-fill; comparing pipeline health across jobs.

**DO NOT USE WHEN:**
> Individual candidate details (use get_candidate_details); aggregate talent pool stats (use get_candidate_stats); full funnel with per-candidate list (use get_vacancy_funnel).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_vacancy_funnel', 'get_candidate_stats', 'forecast_hiring_needs']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "job_id": {
      "type": "string"
    },
    "date_range": {
      "type": "string"
    }
  }
}
```

---

### `get_pool_candidates`

**Descrição completa:**
> Returns the list of candidates in a specific talent pool, optionally filtered by their pool stage (discovered, contacted, screening, screened, ready). Includes candidate summary data and pool-specific metadata. Use to inspect pool contents before making sourcing or transfer decisions.

**USE WHEN:**
> Recruiter asks "quem está no pool X?"; before moving candidates from pool to vacancy; analytics on pool readiness; campaign targeting within a pool.

**DO NOT USE WHEN:**
> Searching all candidates (use search_candidates); getting a full candidate profile (use get_candidate_details); listing pools (use list_talent_pools).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['list_talent_pools', 'move_pool_to_job', 'get_candidate_details']` |
| `allowed_agents` | `['talent_pool', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "pool_id"
  ],
  "properties": {
    "pool_id": {
      "type": "string"
    },
    "stage": {
      "type": "string",
      "enum": [
        "discovered",
        "contacted",
        "screening",
        "screened",
        "ready"
      ]
    }
  }
}
```

---

### `get_proactive_alerts`

**Descrição completa:**
> Returns a list of proactive pipeline alerts generated by LIA's monitoring system, covering stale candidates exceeding SLA, bottleneck stages, empty pipelines, and high rejection rate anomalies. Filter by severity or category. Read-only — use confirm_autonomous_action to act on pending suggestions.

**USE WHEN:**
> Recruiter starts a session and wants to know what needs attention; monitoring dashboard load; before planning daily sourcing/review activities.

**DO NOT USE WHEN:**
> Acting on a specific alert (use confirm_autonomous_action); listing pending autonomous actions (use get_autonomous_actions); pipeline data only (use get_pipeline_stats).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_autonomous_actions', 'confirm_autonomous_action', 'get_pipeline_stats']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "severity": {
      "type": "string",
      "enum": [
        "low",
        "medium",
        "high",
        "critical"
      ]
    },
    "category": {
      "type": "string"
    }
  }
}
```

---

### `get_salary_benchmarks`

**Descrição completa:**
> Busca benchmarks salariais combinando histórico interno (SQL por empresa) com dados externos de mercado (Robert Half 2024, Gupy). Retorna internal_avg, market_range, sources citáveis e recommendation baseada nos dois.

**USE WHEN:**
> Wizard stage 'salary' — user needs concrete salary data to define the range. Also when updating an existing job's compensation.

**DO NOT USE WHEN:**
> Salary already confirmed by user in the same session; skip external call to save latency and credits.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'credits_consumed']` |
| `side_effects` | `['external_api_call', 'credits_consumed']` |
| `related_tools` | `['search_salary_benchmark', 'suggest_compensation', 'create_job_draft']` |
| `allowed_agents` | `['job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_title",
    "seniority"
  ],
  "properties": {
    "job_title": {
      "type": "string"
    },
    "seniority": {
      "type": "string",
      "enum": [
        "Estágio",
        "Júnior",
        "Pleno",
        "Sênior",
        "Especialista",
        "Gerente",
        "Diretor"
      ]
    },
    "location": {
      "type": "string"
    },
    "department": {
      "type": "string"
    }
  }
}
```

---

### `get_skill_adjacencies`

**Descrição completa:**
> Returns adjacent skills for a single given skill with their proximity weights, domain classifications, and relationship types (complementary, prerequisite, alternative) from the skills ontology graph. Use to explore the immediate skill neighborhood for a specific technology or competency.

**USE WHEN:**
> Recruiter asks what skills relate to a specific technology; expanding a single skill before sourcing; building a comprehensive competency map for a role.

**DO NOT USE WHEN:**
> Multiple input skills (use infer_related_skills); gap analysis for a candidate (use analyze_skill_gaps); mapping raw strings to canonical names (use map_candidate_skills_to_ontology).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['infer_related_skills', 'analyze_skill_gaps']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'analytics', 'job_planner', 'job_wizard']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "skill"
  ],
  "properties": {
    "skill": {
      "type": "string"
    },
    "min_weight": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  }
}
```

---

### `get_vacancy_funnel`

**Descrição completa:**
> Returns per-stage candidate counts and (optionally) the candidate list for a specific vacancy, providing a complete funnel snapshot including rejected candidates if requested. Use when the recruiter needs the full picture of who is where in a specific vacancy.

**USE WHEN:**
> Recruiter asks "quem está em cada etapa da vaga X?"; hiring manager review; before making bulk stage decisions; sourcing gap analysis for a specific vacancy.

**DO NOT USE WHEN:**
> Aggregate stats across vacancies (use get_pipeline_stats); talent pool overview (use get_candidate_stats); searching for candidates by profile (use search_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_pipeline_stats', 'bulk_update_candidates_stage', 'get_candidate_details']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "include_rejected": {
      "type": "boolean"
    }
  }
}
```

---

### `hide_candidate`

**Descrição completa:**
> Soft-removes a candidate from the active pipeline view without rejecting or deleting them. The candidate remains in the talent pool and can be unhidden later. Use when the recruiter wants to deprioritize a candidate without making a final rejection decision.

**USE WHEN:**
> Recruiter says "esconder", "tirar da vista", "não quero ver agora"; candidate is on hold pending other interviews; duplicates in the view; keeping pipeline clean without committing to rejection.

**DO NOT USE WHEN:**
> Final rejection decision (use reject_candidate); moving to a different stage (use update_candidate_stage); permanent removal.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['reject_candidate', 'update_candidate_stage', 'get_candidate_details']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analyst_feedback']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "vacancy_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    }
  }
}
```

---

### `import_workforce_plan`

**Descrição completa:**
> Imports a hiring plan (department, role, quantity, deadline) into the company_culture_profiles.additional_data.workforce_plan JSON. Replaces any prior plan in full — no partial merge.

**USE WHEN:**
> Onboarding step "workforce"; recruiter shares a planning spreadsheet or table of upcoming hires.

**DO NOT USE WHEN:**
> Editing a single line of the plan (read first, then re-import the full list); creating actual jobs (use create_job).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail', 'write_destructive']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['save_company_section', 'create_job']` |
| `allowed_agents` | `['company_settings', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "company_id",
    "plan_data"
  ],
  "properties": {
    "company_id": {
      "type": "string"
    },
    "plan_data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "department": {
            "type": "string"
          },
          "role": {
            "type": "string"
          },
          "quantity": {
            "type": "integer"
          },
          "deadline": {
            "type": "string"
          }
        }
      }
    },
    "user_id": {
      "type": "string"
    }
  }
}
```

---

### `infer_related_skills`

**Descrição completa:**
> Uses the LIA skills ontology graph to infer related and adjacent skills from a set of input skills, applying adjacency traversal and semantic proximity scoring. Returns a prioritized list of skills the LLM should consider when screening candidates or building job requirements. Depth 1–3 controls breadth of traversal.

**USE WHEN:**
> Job requirements seem too narrow; sourcing is not finding enough candidates; recruiter wants to surface non-obvious adjacent skills; before running search_candidates with an expanded skill set.

**DO NOT USE WHEN:**
> Comparing candidate skills to job requirements (use analyze_skill_gaps); mapping raw skill strings to canonical nodes (use map_candidate_skills_to_ontology); getting a single skill's neighbors (use get_skill_adjacencies).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_skill_adjacencies', 'analyze_skill_gaps', 'map_candidate_skills_to_ontology']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'analytics', 'job_planner', 'job_wizard']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "skills"
  ],
  "properties": {
    "skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "depth": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30
    }
  }
}
```

---

### `list_digital_twins`

**Descrição completa:**
> Lists all Digital Twins available to the current tenant with their names, associated SME, specialties, and creation date. Use to let the recruiter or agent select the right twin before evaluation.

**USE WHEN:**
> Before calling evaluate_with_twin; recruiter asks "quais twins temos?"; selecting a domain specialist twin for a technical role evaluation.

**DO NOT USE WHEN:**
> Evaluating a candidate (use evaluate_with_twin); creating a twin (use create_digital_twin); listing sourcing agents (use get_agent_status).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['create_digital_twin', 'evaluate_with_twin']` |
| `allowed_agents` | `['digital_twin', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {}
}
```

---

### `list_jobs`

**Descrição completa:**
> List all job vacancies in the company portfolio with status, metrics, candidate counts, and department breakdown. Returns active, paused, and closed vacancies with key KPIs such as time-to-fill, pipeline velocity, and SLA health per vacancy.

**USE WHEN:**
> When the recruiter asks to see their job portfolio, list open or active vacancies, check how many jobs are currently running, or browse all positions across departments. Triggers on: "minhas vagas", "vagas abertas", "listar vagas", "ver vagas", "vagas ativas".

**DO NOT USE WHEN:**
> Do not use to get details of a single vacancy — use view_job_details instead. Do not use to search candidates — use search_candidates instead. Do not use when the recruiter is creating a new job — use create_job instead.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['view_job_details', 'pause_job', 'search_jobs']` |
| `allowed_agents` | `['jobs_management', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "description": "Filter by status: active, paused, closed, all (default: active)"
    },
    "department": {
      "type": "string",
      "description": "Filter by department name (optional)"
    }
  }
}
```

---

### `list_talent_pools`

**Descrição completa:**
> Lists all talent pools for the current tenant, optionally filtered by status (active, paused, archived). Returns pool metadata including candidate counts, archetype, and last activity timestamp. Use to give the recruiter an overview of available pools before selecting one for action.

**USE WHEN:**
> Recruiter asks "quais pools temos?"; before adding candidates to a pool; before moving candidates from pool to vacancy; analytics on pool coverage.

**DO NOT USE WHEN:**
> Getting candidates inside a specific pool (use get_pool_candidates); creating a new pool (use create_talent_pool); searching for candidates (use search_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_pool_candidates', 'create_talent_pool', 'add_to_talent_pool']` |
| `allowed_agents` | `['talent_pool', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": [
        "active",
        "paused",
        "archived"
      ]
    }
  }
}
```

---

### `map_candidate_skills_to_ontology`

**Descrição completa:**
> Normalizes raw skill strings from a candidate's profile to canonical ontology node names with domain and specialization classifications. Resolves abbreviations, typos, and synonyms (e.g., "JS" → "JavaScript", "react.js" → "React"). Essential pre-step before skill gap analysis or ontology-based searches.

**USE WHEN:**
> Before running analyze_skill_gaps with raw profile data; normalizing imported candidate skills from external ATS or resume parser; ensuring consistent skill terminology across the tenant.

**DO NOT USE WHEN:**
> Skills are already normalized; gap analysis without normalization is acceptable for quick checks; inferring related skills (different purpose — use infer_related_skills).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['analyze_skill_gaps', 'infer_related_skills']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'analytics', 'screening']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "candidate_id": {
      "type": "string"
    }
  }
}
```

---

### `match_internal_candidates`

**Descrição completa:**
> Matches internal employees to an open position using direct skill matches, adjacent and transferable skills via the ontology graph, and development potential scoring. Returns a ranked list of internal candidates with match rationale, enabling evidence-based internal mobility decisions before external sourcing.

**USE WHEN:**
> New vacancy opens and recruiter wants to check internal talent first; recruiter says "tem alguém interno para essa vaga?"; strategic internal mobility initiative; cost reduction before external hiring.

**DO NOT USE WHEN:**
> No internal employee database available; vacancy requires external market hire by policy; already searched internally (avoid redundant calls); searching external talent pool (use search_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['search_candidates', 'analyze_skill_gaps', 'add_candidate_to_vacancy']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "job_id": {
      "type": "string"
    },
    "required_skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "job_title": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    },
    "department": {
      "type": "string"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

---

### `move_candidate`

**Descrição completa:**
> Move a candidate to a different stage in the recruitment pipeline, such as advancing from screening to interview, or from interview to offer stage. Records a reason for audit trail and triggers downstream notifications if configured for the target stage.

**USE WHEN:**
> When the recruiter asks to advance or move a specific candidate to another stage. Triggers on: "mover candidato para entrevista", "avançar candidato", "mover para próxima etapa", "candidato X para triagem", "mover X para oferta".

**DO NOT USE WHEN:**
> Do not use to reject candidates — use reject_candidate instead. Do not use to move multiple candidates at once — use bulk_update_candidates_stage. Do not use without candidate_id, target_stage, and reason — all three are required.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'write_destructive', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['reject_candidate', 'bulk_update_candidates_stage', 'update_candidate_stage']` |
| `allowed_agents` | `['cv_screening', 'pipeline_action', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "target_stage",
    "reason"
  ],
  "properties": {
    "candidate_id": {
      "type": "string",
      "description": "UUID of the candidate to move"
    },
    "target_stage": {
      "type": "string",
      "description": "Target pipeline stage name (e.g. triagem, entrevista, oferta)"
    },
    "reason": {
      "type": "string",
      "description": "Reason for the stage move (required for audit trail)"
    }
  }
}
```

---

### `move_pool_to_job`

**Descrição completa:**
> Moves selected candidates from a talent pool directly into a job vacancy at a specified pipeline stage, creating VacancyCandidate records in a single atomic operation. Use for efficient pool-to-vacancy pipeline transfers when a matching job opens up.

**USE WHEN:**
> Recruiter activates a new job matching an existing pool archetype; campaign triggered pool-to-vacancy transfer; recruiter says "mover pool X para a vaga Y".

**DO NOT USE WHEN:**
> Adding individual candidates not in a pool (use add_candidate_to_vacancy); bulk stage change within a vacancy (use bulk_update_candidates_stage); exporting pool data (use export_candidates).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['add_candidate_to_vacancy', 'bulk_update_candidates_stage', 'get_pool_candidates']` |
| `allowed_agents` | `['talent_pool', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "pool_id",
    "job_id",
    "candidate_ids",
    "target_stage"
  ],
  "properties": {
    "pool_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "candidate_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "target_stage": {
      "type": "string"
    }
  }
}
```

---

### `pause_job`

**Descrição completa:**
> Pause an active job vacancy, temporarily stopping new applications and sourcing activities. Requires a structured reason for audit trail compliance. The vacancy remains in the system and can be reactivated at any time using reopen_job.

**USE WHEN:**
> When the recruiter explicitly asks to pause, suspend, or temporarily halt a vacancy. Appropriate for: "pausar a vaga", "suspender recrutamento", "colocar vaga em espera", "pausar", "suspender vaga". Always confirm intent before executing.

**DO NOT USE WHEN:**
> Do not use if the recruiter intends to close the vacancy permanently — use close_job. Do not pause without a job_id and reason — both are required. Always ask for confirmation before pausing, as it affects candidates in the pipeline.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'write_destructive', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['close_job', 'reopen_job', 'list_jobs']` |
| `allowed_agents` | `['jobs_management', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id",
    "reason"
  ],
  "properties": {
    "job_id": {
      "type": "string",
      "description": "UUID of the job vacancy to pause"
    },
    "reason": {
      "type": "string",
      "description": "Reason for pausing the vacancy (required for audit trail)"
    }
  }
}
```

---

### `pause_vacancy`

**Descrição completa:**
> Pauses an active job vacancy, stopping new applications and sourcing while preserving all existing candidates in the pipeline. Sets an expected resume date. The vacancy can be re-activated later without data loss.

**USE WHEN:**
> Hiring temporarily blocked (budget review, org change); need to pause intake without closing; recruiter says "pausar vaga", "segurar processo por agora".

**DO NOT USE WHEN:**
> Permanent cancellation (use cancel_vacancy); vacancy is already filled (use confirm_placement); updating vacancy fields (use update_job).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['cancel_vacancy', 'update_job', 'publish_job']` |
| `allowed_agents` | `['job_planner', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id",
    "reason"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    },
    "resume_date": {
      "type": "string"
    }
  }
}
```

---

### `prioritize_tasks`

**Descrição completa:**
> Recalculates and updates priority scores for a list of planned tasks using multi-criteria scoring (urgency 30%, impact 25%, criticality 25%, efficiency 20%). Writes updated priority values back to the planned_tasks table. Run after decomposing tasks or when context changes (budget cut, new deadline, blocked dependency).

**USE WHEN:**
> After decompose_task creates a set of subtasks; context has changed and priority order needs re-evaluation; orchestrator detects a bottleneck and needs to reorder the queue.

**DO NOT USE WHEN:**
> Tasks have not been created yet (use decompose_task first); generating an execution plan (use get_execution_plan which calls prioritization internally); retrieving the next tasks to run (use get_next_tasks).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['decompose_task', 'get_execution_plan', 'get_next_tasks']` |
| `allowed_agents` | `['orchestrator', 'automation']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "task_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "goal_id": {
      "type": "string"
    }
  }
}
```

---

### `process_uploaded_document`

**Descrição completa:**
> Two-phase document ingestion. Phase 1 extracts text (PDF/DOCX/TXT), runs PII masking (CPF/email/phone) and FairnessGuard, then returns suggested_fields for human approval. Phase 2 (handler-side, when the recruiter confirms) persists per section via save_company_section and logs persist_document_extraction.

**USE WHEN:**
> Onboarding step "documento"; recruiter uploads handbook, comp policy, org chart, or tech doc.

**DO NOT USE WHEN:**
> CV/resume parsing (use cv_screening tools); already-structured JSON (use save_company_section directly).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['pii', 'fairness_guard', 'requires_hitl', 'multi_tenant', 'audit_trail']` |
| `side_effects` | `['audit_trail']` |
| `related_tools` | `['save_company_section', 'save_company_benefits', 'analyze_company_website']` |
| `allowed_agents` | `['company_settings', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "company_id",
    "document_text"
  ],
  "properties": {
    "company_id": {
      "type": "string"
    },
    "document_text": {
      "type": "string"
    },
    "document_type": {
      "type": "string",
      "enum": [
        "handbook",
        "org_chart",
        "compensation",
        "tech_doc",
        "general"
      ]
    },
    "user_id": {
      "type": "string"
    }
  }
}
```

---

### `publish_job`

**Descrição completa:**
> Publishes a job vacancy to make it visible to candidates and distributes it to configured job boards and channels. Changes status from draft to published. Optionally specifies which channels to publish to. This is an irreversible action without a complementary unpublish — use pause_vacancy to take offline temporarily.

**USE WHEN:**
> Recruiter confirms job is ready for candidates; wizard completion step; HR approval workflow completes; recruiter explicitly says "publicar vaga".

**DO NOT USE WHEN:**
> Job is still being drafted (use save_job_draft); recruiter wants to review once more; publishing to a specific external board only (use publish_to_job_board).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail', 'requires_hitl']` |
| `side_effects` | `['db_write', 'webhook_fired', 'external_api_call', 'audit_trail']` |
| `related_tools` | `['create_job', 'update_job', 'pause_vacancy', 'publish_to_job_board']` |
| `allowed_agents` | `['orchestrator', 'job_planner']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "channels": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `publish_to_job_board`

**Descrição completa:**
> Publishes a job vacancy to a specific external job board (LinkedIn, Indeed, Gupy, Glassdoor) via the configured integration. Separate from the internal publish action. Consumes integration credits if applicable. Posts the full JD with application link.

**USE WHEN:**
> Recruiter wants to expand candidate sourcing to external channels; job is published internally and ready for external distribution; recruiter says "postar no LinkedIn".

**DO NOT USE WHEN:**
> Internal publish only (use publish_job); job is still a draft; searching for external candidates (use search_candidates_pearch); checking job board performance.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'credits_consumed', 'audit_trail']` |
| `side_effects` | `['external_api_call', 'credits_consumed', 'audit_trail']` |
| `related_tools` | `['publish_job', 'get_external_applications', 'search_candidates_pearch']` |
| `allowed_agents` | `['job_planner', 'communication', 'orchestrator']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id",
    "board"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "board": {
      "type": "string",
      "enum": [
        "linkedin",
        "indeed",
        "gupy",
        "glassdoor"
      ]
    }
  }
}
```

---

### `record_hiring_outcome`

**Descrição completa:**
> Records the final outcome of a hiring cycle (filled, cancelled, expired, or turnover) along with an optional satisfaction score and retention data. This data feeds LIA's continuous learning system to improve future scoring and routing decisions. Should be called once per vacancy lifecycle close event.

**USE WHEN:**
> Hiring cycle is closed for any reason; vacancy is filled and candidate has started; tracking early attrition after 30/60/90 days; recording that a vacancy was cancelled or expired without a hire.

**DO NOT USE WHEN:**
> Confirming a hire (use confirm_placement first, then record_hiring_outcome for learning data); retrieving historical insights (use get_learning_insights); interim pipeline status recording.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['confirm_placement', 'get_learning_insights', 'forecast_hiring_needs']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `IN_JOB` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id",
    "candidate_id",
    "outcome"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "candidate_id": {
      "type": "string"
    },
    "outcome": {
      "type": "string",
      "enum": [
        "filled",
        "cancelled",
        "expired",
        "turnover"
      ]
    },
    "satisfaction_score": {
      "type": "number",
      "minimum": 1,
      "maximum": 5
    },
    "retention_days": {
      "type": "integer"
    }
  }
}
```

---

### `reject_autonomous_action`

**Descrição completa:**
> Rejects a pending autonomous action, preventing its execution and logging the rejection reason for LIA's learning system. The rejection is recorded to help calibrate future autonomous decisions and reduce similar false positives.

**USE WHEN:**
> Recruiter reviews pending action and disagrees; action parameters are wrong; context has changed and action is no longer appropriate; recruiter says "não fazer essa ação".

**DO NOT USE WHEN:**
> Approving an action (use confirm_autonomous_action); reviewing without deciding (use get_autonomous_actions); cancelling a vacancy (different concept — use cancel_vacancy).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['confirm_autonomous_action', 'get_autonomous_actions']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "action_id"
  ],
  "properties": {
    "action_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    }
  }
}
```

---

### `reject_candidate`

**Descrição completa:**
> Permanently rejects a candidate from a vacancy, records the rejection reason, optionally sends a rejection notification, and removes them from the active funnel. Creates an audit log entry. This is a definitive action — the candidate remains in the talent pool but is marked rejected for this vacancy.

**USE WHEN:**
> Recruiter confirms rejection after screening or interviews; HITL rejection approval granted; FairnessGuard audit passed; recruiter says "reprovar", "dispensar", "não aprovado".

**DO NOT USE WHEN:**
> Temporarily hiding a candidate (use hide_candidate); moving to a lower stage (use update_candidate_stage); bulk rejecting multiple candidates (use bulk_update_candidates_stage with a rejection stage).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'requires_hitl', 'fairness_guard']` |
| `side_effects` | `['db_write', 'audit_trail', 'email_sent']` |
| `related_tools` | `['hide_candidate', 'update_candidate_stage', 'bulk_update_candidates_stage']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analyst_feedback']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "vacancy_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    },
    "notify": {
      "type": "boolean"
    }
  }
}
```

---

### `reschedule_interview`

**Descrição completa:**
> Reschedules an existing interview to a new date/time, recording the reason for the change. Currently simulated — persistent state update requires full database integration. Use when the candidate or interviewer needs to change the previously agreed slot.

**USE WHEN:**
> Candidate requests a new time after confirming the original; interviewer is unavailable for the scheduled slot; recruiter says "remarcar entrevista [id] para [nova data]".

**DO NOT USE WHEN:**
> Cancelling the interview entirely (use cancel_interview); scheduling for the first time (use schedule_interview); checking interview status (use get_interview_status).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write', 'email_sent', 'mock_only', 'audit_trail']` |
| `related_tools` | `['schedule_interview', 'cancel_interview', 'send_interview_invitation']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'interview_scheduling']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "interview_id",
    "new_datetime_str"
  ],
  "properties": {
    "interview_id": {
      "type": "string"
    },
    "new_datetime_str": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    }
  }
}
```

---

### `run_multi_strategy_search`

**Descrição completa:**
> Executes four parallel candidate discovery strategies simultaneously — direct match, adjacent skills, silver medalists (past applicants), and re-engagement — and returns a merged, deduplicated, and ranked result set. More thorough than a single search but consumes more compute. Use for high-priority or hard-to-fill roles.

**USE WHEN:**
> Recruiter opens a critical or urgent role and wants maximum coverage; initial sourcing run for a new talent pool; recruiter says "busca completa" or "encontrar todos os perfis".

**DO NOT USE WHEN:**
> Simple skills-based search is sufficient (use search_candidates); persistent ongoing sourcing is needed (use create_sourcing_agent); specific external network search (use search_candidates_pearch).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'credits_consumed']` |
| `side_effects` | `['credits_consumed', 'external_api_call']` |
| `related_tools` | `['search_candidates', 'create_sourcing_agent', 'search_candidates_pearch']` |
| `allowed_agents` | `['agent_studio', 'sourcing', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_title"
  ],
  "properties": {
    "job_title": {
      "type": "string"
    },
    "skills": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "location": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    }
  }
}
```

---

### `save_company_benefits`

**Descrição completa:**
> Persists benefits offered by the company into company_benefits. Supports append (default) and replace modes; emits an audit entry per benefit.

**USE WHEN:**
> Onboarding step "benefícios"; recruiter lists "vale-refeição, home-office, plano de saúde…"; replace mode when the recruiter says "substitui tudo".

**DO NOT USE WHEN:**
> Editing a single benefit attribute (use save_company_field with field=benefits[].x); compensation bands (use save_company_section culture).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail', 'write_destructive', 'fairness_guard']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['save_company_section', 'get_company_benefits']` |
| `allowed_agents` | `['company_settings', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "company_id",
    "benefits"
  ],
  "properties": {
    "company_id": {
      "type": "string"
    },
    "benefits": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "mode": {
      "type": "string",
      "enum": [
        "append",
        "replace"
      ]
    },
    "user_id": {
      "type": "string"
    }
  }
}
```

---

### `save_company_field`

**Descrição completa:**
> Updates a single canonical field on a company's profile (e.g. name, industry, size, mission, vision). Use when the recruiter wants to fix or set ONE specific attribute conversationally; for bulk updates prefer save_company_section.

**USE WHEN:**
> Recruiter says "muda o nome da empresa para X", "atualiza o setor", "corrige a missão"; single-field edits coming from the chat.

**DO NOT USE WHEN:**
> Updating multiple fields at once (use save_company_section); tier-1 fields (cnpj, name) without prior is_admin + confirmed=true.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail', 'write_destructive', 'fairness_guard']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['save_company_section', 'get_company_profile', 'process_uploaded_document']` |
| `allowed_agents` | `['company_settings', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "company_id",
    "field",
    "value"
  ],
  "properties": {
    "company_id": {
      "type": "string"
    },
    "field": {
      "type": "string"
    },
    "value": {},
    "user_id": {
      "type": "string"
    },
    "confirmed": {
      "type": "boolean"
    },
    "is_admin": {
      "type": "boolean"
    }
  }
}
```

---

### `save_company_section`

**Descrição completa:**
> Bulk-updates a whole section of a company record (profile, culture, tech_stack, hiring_policies, benefits). Each section maps to its canonical table and goes through FairnessGuard L1 before the write.

**USE WHEN:**
> Recruiter is going through the onboarding orchestrator step "configure cultura/perfil/benefícios"; chat needs to persist >1 field at once.

**DO NOT USE WHEN:**
> Single-field tweak (use save_company_field); document import (use process_uploaded_document — two-phase with explicit confirm).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail', 'write_destructive', 'fairness_guard']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['save_company_field', 'save_company_benefits', 'process_uploaded_document']` |
| `allowed_agents` | `['company_settings', 'orchestrator']` |
| `scope` | `GLOBAL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "company_id",
    "section",
    "data"
  ],
  "properties": {
    "company_id": {
      "type": "string"
    },
    "section": {
      "type": "string",
      "enum": [
        "profile",
        "culture",
        "tech_stack",
        "hiring_policies"
      ]
    },
    "data": {
      "type": "object"
    },
    "user_id": {
      "type": "string"
    }
  }
}
```

---

### `save_job_draft`

**Descrição completa:**
> Persists the current job vacancy as a DRAFT in the database, creating or updating the draft record without publishing it. Use this to checkpoint progress during multi-turn wizard sessions so recruiters can resume later without data loss. Writes to job_vacancies table with status=draft.

**USE WHEN:**
> Wizard session paused or recruiter needs to leave; partial job data collected; recruiter explicitly says "salvar rascunho"; intermediate auto-save checkpoint.

**DO NOT USE WHEN:**
> Recruiter wants to publish immediately (use create_job + publish_job); job data is invalid or incomplete without recruiter confirmation; updating a published job (use update_job).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['create_job', 'validate_job_fields', 'publish_job']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "fields"
  ],
  "properties": {
    "fields": {
      "type": "object"
    },
    "draft_id": {
      "type": "string"
    }
  }
}
```

---

### `schedule_interview`

**Descrição completa:**
> Creates a scheduled interview slot between a candidate and an interviewer at the specified date/time, returning an interview_id and calendar link. Currently uses a simulation stub for calendar creation — real integration pending. Sends no notifications automatically; use send_interview_invitation separately.

**USE WHEN:**
> Availability has been confirmed and recruiter or candidate chooses a specific slot; automatic scheduling after candidate accepts an interview invite; recruiter says "agendar entrevista para [data] com [entrevistador]".

**DO NOT USE WHEN:**
> Availability not checked yet (use check_interviewer_availability first); rescheduling an existing interview (use reschedule_interview); sending the invitation (use send_interview_invitation after scheduling).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['db_write', 'mock_only', 'audit_trail']` |
| `related_tools` | `['check_interviewer_availability', 'send_interview_invitation', 'reschedule_interview']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'interview_scheduling']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "interviewer_id",
    "datetime_str"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "interviewer_id": {
      "type": "string"
    },
    "datetime_str": {
      "type": "string"
    },
    "interview_type": {
      "type": "string",
      "enum": [
        "technical",
        "behavioral",
        "cultural_fit",
        "final"
      ]
    }
  }
}
```

---

### `schedule_report`

**Descrição completa:**
> Creates a recurring scheduled report job that automatically generates and sends the specified report type to designated recipients on a cron schedule. Persists the schedule configuration to the database and activates the job immediately.

**USE WHEN:**
> Recruiter wants to receive weekly/monthly reports automatically; HR director wants a recurring KPI digest; setting up ongoing pipeline health monitoring for a client.

**DO NOT USE WHEN:**
> One-time report (use generate_report); checking current pipeline stats (use get_pipeline_stats); modifying an existing schedule (use an update operation).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'webhook_fired']` |
| `related_tools` | `['generate_report', 'get_pipeline_stats']` |
| `allowed_agents` | `['orchestrator', 'analytics']` |
| `scope` | `GLOBAL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "report_type",
    "schedule",
    "recipients"
  ],
  "properties": {
    "report_type": {
      "type": "string"
    },
    "schedule": {
      "type": "string",
      "description": "Cron expression"
    },
    "recipients": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

### `search_candidates`

**Descrição completa:**
> Searches the tenant-scoped talent pool using multi-dimensional filters including skills, seniority, experience range, WSI score, availability, location, and language. Returns a ranked list of matching candidates with summary profiles. Use this as the primary discovery tool when the recruiter wants to find or surface candidates.

**USE WHEN:**
> Recruiter asks to find candidates matching a profile; sourcing agent needs matches for a job; building a shortlist; proactive talent discovery; analytics queries.

**DO NOT USE WHEN:**
> Fetching a single known candidate (use get_candidate_details); searching external networks like LinkedIn (use search_candidates_pearch); pipeline stats (use get_pipeline_stats).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_candidate_details', 'search_candidates_pearch', 'add_candidate_to_vacancy']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'analytics']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string"
    },
    "filters": {
      "type": "object"
    },
    "limit": {
      "type": "integer"
    },
    "offset": {
      "type": "integer"
    }
  }
}
```

---

### `search_candidates_pearch`

**Descrição completa:**
> Searches 800M+ external professional profiles via Pearch AI using semantic search. Returns enriched profiles that can be imported into the talent pool. Each search consumes Pearch credits — select fast (cheaper) or pro (more accurate) mode. External data; always validate before candidate contact.

**USE WHEN:**
> No matching candidates in internal pool; recruiter explicitly wants external talent discovery; hard-to-fill specialty roles; recruiter says "buscar no Pearch" or "encontrar candidatos externos".

**DO NOT USE WHEN:**
> Internal pool has sufficient candidates (use search_candidates first); recruiter wants to post a job externally (use publish_to_job_board); budget constraints prohibit credit consumption.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'credits_consumed']` |
| `side_effects` | `['external_api_call', 'credits_consumed']` |
| `related_tools` | `['search_candidates', 'run_multi_strategy_search', 'add_candidate_to_vacancy']` |
| `allowed_agents` | `['sourcing', 'sourcing_search', 'agent_studio', 'orchestrator']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string"
    },
    "search_type": {
      "type": "string",
      "enum": [
        "fast",
        "pro"
      ]
    },
    "limit": {
      "type": "integer",
      "maximum": 50
    },
    "show_emails": {
      "type": "boolean"
    }
  }
}
```

---

### `search_jobs`

**Descrição completa:**
> Searches the tenant's job vacancy table by title, status, department, or free text, returning a list of matching vacancies with summary data. Use when the recruiter references a job by name or asks to list active/open positions.

**USE WHEN:**
> Recruiter refers to a job by name or partial name; listing active vacancies for dashboard; cross-vacancy analytics; before adding a candidate to a vacancy if job_id is unknown.

**DO NOT USE WHEN:**
> Single job with known job_id (use get_job_details); analytics on pipeline stages (use get_pipeline_stats); external job board search (use publish_to_job_board).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['get_job_details', 'get_pipeline_stats', 'create_job']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'analytics', 'job_planner']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "department": {
      "type": "string"
    },
    "limit": {
      "type": "integer"
    }
  }
}
```

---

### `search_salary_benchmark`

**Descrição completa:**
> Fetches external salary benchmark data for a specific job title, seniority level, and location so the recruiter can define a competitive and realistic compensation range. Use this before drafting salary bands or when the recruiter asks "quanto pagar" for a role. Does NOT write to the database — read-only market data retrieval.

**USE WHEN:**
> Recruiter starts a new job and needs a salary reference; wizard step for salary collection; recruiter explicitly asks for market salary data or benchmark.

**DO NOT USE WHEN:**
> Salary has already been confirmed; recruiter wants to update an existing job's salary (use update_job); detailed internal budget analysis (use analytics tools).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['external_api_call']` |
| `related_tools` | `['get_intelligent_salary', 'validate_job_fields', 'save_job_draft']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_title"
  ],
  "properties": {
    "job_title": {
      "type": "string"
    },
    "seniority": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "industry": {
      "type": "string"
    }
  }
}
```

---

### `send_email`

**Descrição completa:**
> Sends a transactional or templated email to one or more candidates or recruiters. Supports free-form body or template_id lookup. This action sends a REAL email — it is not a preview or draft. Logs delivery to the communication audit trail. MOCK status: partially live; confirm template coverage before production use.

**USE WHEN:**
> Recruiter explicitly requests to notify a candidate by email; automated pipeline event triggers notification (rejection, interview invite, offer letter); communication domain action routed here.

**DO NOT USE WHEN:**
> WhatsApp is the preferred channel for this candidate (use send_whatsapp); email should only be previewed, not sent; bulk automated nurture (use create_nurture_sequence).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'requires_hitl']` |
| `side_effects` | `['email_sent', 'audit_trail']` |
| `related_tools` | `['send_whatsapp', 'create_nurture_sequence', 'reject_candidate']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'communication']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "to",
    "subject",
    "body"
  ],
  "properties": {
    "to": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "subject": {
      "type": "string"
    },
    "body": {
      "type": "string"
    },
    "template_id": {
      "type": "string"
    }
  }
}
```

---

### `send_interview_invitation`

**Descrição completa:**
> Sends an interview invitation email to a candidate for a scheduled interview. Currently simulated — real email delivery requires email provider integration. PII handling: candidate_email is not logged, only identifiers are recorded. Use after schedule_interview to notify the candidate.

**USE WHEN:**
> Interview has been scheduled and candidate needs to be notified; recruiter says "enviar convite de entrevista para [candidato]"; automated pipeline step after scheduling confirmation.

**DO NOT USE WHEN:**
> Interview not yet scheduled (use schedule_interview first); general email communication (use send_email); WhatsApp notification preferred (use send_whatsapp).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail']` |
| `side_effects` | `['email_sent', 'mock_only', 'audit_trail']` |
| `related_tools` | `['schedule_interview', 'send_email', 'get_interview_status']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'interview_scheduling']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "interview_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "interview_id": {
      "type": "string"
    },
    "candidate_email": {
      "type": "string"
    }
  }
}
```

---

### `send_whatsapp`

**Descrição completa:**
> Sends a WhatsApp message to a candidate's phone number using a registered template or free-form message. This action delivers a REAL WhatsApp message via the configured provider — not a preview. Logs delivery to the communication audit trail. MOCK status: provider integration required for production; may return mock response in dev.

**USE WHEN:**
> Candidate's preferred contact channel is WhatsApp; WSI invitation via WhatsApp; interview scheduling confirmation; recruiter explicitly requests WhatsApp outreach.

**DO NOT USE WHEN:**
> Candidate has not provided phone number or consented to WhatsApp contact; email is preferred channel (use send_email); bulk automated sequence (use create_nurture_sequence).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'audit_trail', 'requires_hitl']` |
| `side_effects` | `['whatsapp_sent', 'audit_trail']` |
| `related_tools` | `['send_email', 'wsi_screening', 'create_nurture_sequence']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'communication']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "phone",
    "message"
  ],
  "properties": {
    "phone": {
      "type": "string"
    },
    "message": {
      "type": "string"
    },
    "template_name": {
      "type": "string"
    }
  }
}
```

---

### `shortlist_candidate`

**Descrição completa:**
> Adds a candidate to the shortlist for a specific vacancy, flagging them as a priority prospect for the recruiter's review. Shortlisted candidates appear at the top of the pipeline view. This is a soft endorsement that does not change the pipeline stage.

**USE WHEN:**
> Screening agent identifies a high-score candidate worth highlighting; recruiter wants to curate a shortlist before sending to hiring manager; talent pool pipeline preview step.

**DO NOT USE WHEN:**
> Moving candidate to a formal interview stage (use update_candidate_stage); adding a new candidate to the vacancy (use add_candidate_to_vacancy); final hiring decision.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['db_write']` |
| `related_tools` | `['add_candidate_to_vacancy', 'update_candidate_stage', 'get_candidate_details']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "vacancy_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "vacancy_id": {
      "type": "string"
    },
    "notes": {
      "type": "string"
    }
  }
}
```

---

### `suggest_reengagement`

**Descrição completa:**
> Identifies inactive candidates in the talent pool who are strong re-engagement targets based on inactivity duration, past WSI scores, and engagement signal history. Returns a prioritized list of candidates to re-contact. Does not send any messages — use create_nurture_sequence or send_email to act.

**USE WHEN:**
> Recruiter wants to revive cold candidates; launching a re-engagement campaign; pipeline is thin and recruiter wants to tap existing talent before sourcing externally.

**DO NOT USE WHEN:**
> Sending messages (use send_email / send_whatsapp / create_nurture_sequence after); searching for new candidates (use search_candidates); getting engagement data (use get_engagement_metrics).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['create_nurture_sequence', 'search_candidates', 'get_engagement_metrics']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'sourcing', 'recruitment_campaign']` |
| `scope` | `TALENT_FUNNEL` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "properties": {
    "days_inactive": {
      "type": "integer",
      "minimum": 7
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

---

### `update_candidate_stage`

**Descrição completa:**
> Moves a single candidate to a specified pipeline stage within a vacancy, creating an audit log entry and optionally notifying the candidate. Enforces tenant isolation to prevent cross-company data access. Use when the recruiter explicitly advances or regresses a candidate's status in the funnel.

**USE WHEN:**
> Recruiter says "mover para entrevistas", "avançar candidato", "reprovar na triagem"; post-screening decision; scheduled stage progression; HITL approval granted.

**DO NOT USE WHEN:**
> Moving multiple candidates at once (use bulk_update_candidates_stage); permanently rejecting (use reject_candidate); hiding from view (use hide_candidate); removing from vacancy (different operation).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail', 'pii', 'requires_hitl']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['bulk_update_candidates_stage', 'reject_candidate', 'hide_candidate', 'wsi_screening']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant', 'screening', 'analyst_feedback']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "target_stage"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "target_stage": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "notes": {
      "type": "string"
    },
    "notify_candidate": {
      "type": "boolean"
    }
  }
}
```

---

### `update_job`

**Descrição completa:**
> Updates one or more fields of an existing job vacancy identified by job_id. Partial updates are supported — only provided fields are changed. Creates an audit log entry with the previous and new values. Use when the recruiter wants to edit an existing published or draft vacancy.

**USE WHEN:**
> Recruiter wants to change title, description, requirements, salary, or status of an existing job; correcting a published job; applying hiring manager feedback; updating work model or location.

**DO NOT USE WHEN:**
> Creating a new job (use create_job); publishing a draft for the first time (use publish_job); pausing or cancelling a vacancy (use pause_vacancy / cancel_vacancy).

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'audit_trail']` |
| `side_effects` | `['db_write', 'audit_trail']` |
| `related_tools` | `['create_job', 'publish_job', 'pause_vacancy', 'cancel_vacancy']` |
| `allowed_agents` | `['orchestrator', 'job_planner', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string"
    },
    "fields": {
      "type": "object"
    }
  }
}
```

---

### `validate_job_fields`

**Descrição completa:**
> Validates a set of job creation fields against business rules and returns a structured report of missing required information, format errors, and improvement suggestions. Use this after collecting job data from the recruiter to confirm completeness before persisting — prevents wasted saves with incomplete records.

**USE WHEN:**
> Before calling save_job_draft or create_job; wizard step transitions; recruiter says they are "done" entering job info; pre-publish validation check.

**DO NOT USE WHEN:**
> Job is already published or active; validating candidate data (use different schema); real-time per-field validation while recruiter is still typing.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant']` |
| `side_effects` | `['none']` |
| `related_tools` | `['save_job_draft', 'create_job', 'get_job_suggestions']` |
| `allowed_agents` | `['job_planner', 'job_intake', 'orchestrator', 'job_wizard']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "fields"
  ],
  "properties": {
    "fields": {
      "type": "object"
    }
  }
}
```

---

### `validate_job_requirements`

**Descrição completa:**
> Valida requisitos da vaga contra viés discriminatório usando FairnessGuard. Layer 1 bloqueia viés explícito; Layer 2 emite alertas educacionais para viés implícito. Use para requirements, description e screening_questions.

**USE WHEN:**
> Before saving a job draft, or when reviewing screening questions for fairness compliance. Mandatory in the draft-to-publish transition.

**DO NOT USE WHEN:**
> Content is already validated in a prior step of the same flow; skip to avoid redundant checks that waste tokens.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['fairness_guard', 'multi_tenant', 'audit_trail']` |
| `side_effects` | `['audit_trail']` |
| `related_tools` | `['extract_job_requirements', 'create_job_draft', 'check_job_draft_health']` |
| `allowed_agents` | `['job_wizard', 'orchestrator']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "text",
    "field_name"
  ],
  "properties": {
    "text": {
      "type": "string"
    },
    "field_name": {
      "type": "string",
      "enum": [
        "requirements",
        "description",
        "screening_questions"
      ]
    }
  }
}
```

---

### `view_job_details`

**Descrição completa:**
> Get comprehensive details of a specific job vacancy including full description, requirements, pipeline stages, candidate counts per stage, SLA status, priority level, and recruitment KPIs such as time-in-stage and conversion rates.

**USE WHEN:**
> When the recruiter asks about a specific vacancy's details, pipeline status, or recruitment metrics. Triggers on: "ver detalhes da vaga", "como está a vaga X", "detalhes da vaga", "ver vaga", "informações da vaga".

**DO NOT USE WHEN:**
> Do not use to list all vacancies — use list_jobs instead. Do not use to update vacancy fields — use update_job instead. Requires job_id; if not provided, ask the recruiter to specify which vacancy.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii']` |
| `side_effects` | `['none']` |
| `related_tools` | `['list_jobs', 'update_job', 'pause_job']` |
| `allowed_agents` | `['jobs_management', 'recruiter_assistant', 'orchestrator']` |
| `scope` | `JOB_TABLE` |
| `version` | `1.0` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "job_id"
  ],
  "properties": {
    "job_id": {
      "type": "string",
      "description": "UUID of the job vacancy to retrieve details for"
    }
  }
}
```

---

### `wsi_screening`

**Descrição completa:**
> Initiates a WSI (Workforce Screening Interview) for a candidate in the context of a job vacancy, launching the AI-driven voice, text, or video screening session. Triggers the full WSI pipeline including question delivery, transcript generation, BARS scoring, and Bloom/Dreyfus analysis. This action contacts the candidate.

**USE WHEN:**
> Candidate advances to screening stage; recruiter or automation decides to start the structured WSI interview; post-shortlist step to qualify candidates at scale.

**DO NOT USE WHEN:**
> Candidate has already completed a WSI for this vacancy; recruiter wants to review existing WSI results (use get_candidate_details or analyze_interview_recording); candidate has not consented to AI screening.

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `governance_tags` | `['multi_tenant', 'pii', 'requires_hitl', 'fairness_guard', 'audit_trail']` |
| `side_effects` | `['db_write', 'webhook_fired', 'whatsapp_sent', 'audit_trail']` |
| `related_tools` | `['analyze_interview_recording', 'update_candidate_stage', 'get_candidate_details']` |
| `allowed_agents` | `['orchestrator', 'recruiter_assistant']` |
| `scope` | `IN_JOB` |
| `version` | `1.1` |

**Parameters schema:**

```json
{
  "type": "object",
  "required": [
    "candidate_id",
    "job_id"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "screening_type": {
      "type": "string",
      "enum": [
        "voice",
        "text",
        "video"
      ]
    }
  }
}
```

---

## DomainActions (281 entries em 18 domínios)

### Domínio: `agent_studio` (20 actions)

### `create_sourcing_agent` — Criar Agente de Sourcing

**Descrição completa:**
> Cria um agente de sourcing especializado usando template de setor (tech, saúde, finanças, etc). O agente aprendido aplica critérios de seleção ajustados ao perfil da vaga. Aciona quando recruiter quer automatizar sourcing para uma vaga ou pool específico.

**Examples (few-shot):**
- `"cria agente"`
- `"quero um agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_name',)` |
| `optional_params` | `('sector_template', 'job_id', 'talent_pool_id')` |
| `tags` | `[]` |

---

### `calibrate_agent` — Calibrar Agente

**Descrição completa:**
> Inicia calibração do agente de sourcing avaliando perfis de candidatos com o recrutador para ajustar os critérios de seleção. Aciona quando o agente está trazendo candidatos fora do perfil ou após 20+ avaliações manuais.

**Examples (few-shot):**
- `"calibra este agente"`
- `"ajusta o comportamento do agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_agent_status` — Status do Agente

**Descrição completa:**
> Obtém status atual do agente de sourcing: estratégia ativa, candidatos processados, taxa de aprovação e métricas de performance. Aciona quando recruiter quer saber como o agente está performando.

**Examples (few-shot):**
- `"mostra agente"`
- `"quero ver agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_agents` — Listar Agentes

**Descrição completa:**
> Lista todos os agentes de sourcing ativos da empresa com seu status, estratégia e métricas resumidas. Aciona quando recruiter quer gerenciar seus agentes ou verificar quais estão rodando.

**Examples (few-shot):**
- `"lista agentes disponíveis"`
- `"quais agentes temos ativos?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('job_id', 'pool_id')` |
| `tags` | `[]` |

---

### `recalibrate_agent` — Recalibrar Agente

**Descrição completa:**
> Recalibra agente com novo feedback do recrutador para ajustar critérios de seleção após novas contratações. Aciona quando há mudança no perfil da vaga ou após feedback negativo dos últimos candidatos selecionados.

**Examples (few-shot):**
- `"recalibrar agente"`
- `"quero recalibrar agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `pause_agent` — Pausar Agente

**Descrição completa:**
> Pausa agente de sourcing interrompendo buscas automáticas (libera quota). Requer confirmação. Aciona quando recruiter quer pausar busca temporariamente ou há vagas suficientes no pipeline.

**Examples (few-shot):**
- `"pausa agente"`
- `"interrompe agente temporariamente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('agent_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_sector_templates` — Ver Templates

**Descrição completa:**
> Lista templates de setor disponíveis para criação de agentes de sourcing com critérios pré-configurados por indústria. Aciona quando recruiter escolhe criar um novo agente e quer ver opções disponíveis.

**Examples (few-shot):**
- `"lista template"`
- `"mostra template ativas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `run_multi_strategy` — Busca Multi-Estratégia

**Descrição completa:**
> Executa busca inteligente com 4 estratégias paralelas (semântica, booleana, pearch, talent pool) para maximizar cobertura de candidatos. Aciona quando busca simples não encontrou candidatos suficientes.

**Examples (few-shot):**
- `"roda estratégia"`
- `"executa estratégia"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_title', 'skills')` |
| `optional_params` | `('location', 'seniority')` |
| `tags` | `[]` |

---

### `create_custom_agent` — Criar Agente Custom

**Descrição completa:**
> Cria agente customizado com nome, role, system prompt e tools específicas para automatizar fluxos do recrutamento. Aciona quando recruiter quer um assistente especializado para tarefa recorrente específica.

**Examples (few-shot):**
- `"cria agente"`
- `"quero um agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('name', 'role', 'system_prompt')` |
| `optional_params` | `('allowed_tools', 'domain', 'max_steps', 'temperature')` |
| `tags` | `[]` |

---

### `list_custom_agents` — Listar Agentes Custom

**Descrição completa:**
> Lista agentes customizados criados pela empresa com status (ativo/pausado), domínio e última execução. Aciona para gerenciamento de agentes customizados do tenant.

**Examples (few-shot):**
- `"lista agente"`
- `"mostra agente ativas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('status', 'domain')` |
| `tags` | `[]` |

---

### `test_custom_agent` — Testar Agente Custom

**Descrição completa:**
> Testa agente customizado com uma mensagem de exemplo antes de colocar em produção. Aciona durante criação ou após edição de agente customizado.

**Examples (few-shot):**
- `"testa agente"`
- `"valida agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_id', 'message')` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `execute_custom_agent` — Executar Agente Custom

**Descrição completa:**
> Executa agente customizado em produção com a mensagem ou contexto fornecido. Aciona quando recruiter chama o agente pelo nome no chat ou via automação.

**Examples (few-shot):**
- `"executa agente"`
- `"roda agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_id', 'message')` |
| `optional_params` | `('context',)` |
| `tags` | `[]` |

---

### `publish_to_marketplace` — Publicar no Marketplace

**Descrição completa:**
> Publica agente customizado no marketplace para ser instalado por outras empresas da plataforma. Requer confirmação. Aciona quando agente tem qualidade suficiente e empresa quer monetizá-lo.

**Examples (few-shot):**
- `"publica agente"`
- `"divulga agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('agent_id', 'title')` |
| `optional_params` | `('short_description', 'category', 'credits_per_execution')` |
| `tags` | `[]` |

---

### `browse_marketplace` — Explorar Marketplace

**Descrição completa:**
> Navega e busca agentes disponíveis no marketplace por categoria ou nome. Aciona quando recruiter quer expandir capacidades com agentes prontos de outros tenants.

**Examples (few-shot):**
- `"navega marketplace de agentes"`
- `"mostra agentes disponíveis no marketplace"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('category', 'search')` |
| `tags` | `[]` |

---

### `install_from_marketplace` — Instalar do Marketplace

**Descrição completa:**
> Instala agente do marketplace na empresa, adicionando-o à lista de agentes disponíveis. Requer confirmação e consome quota. Aciona ao selecionar agente no marketplace.

**Examples (few-shot):**
- `"instala agente"`
- `"ativa agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('listing_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `assign_to_crew` — Atribuir a Crew

**Descrição completa:**
> Atribui agente customizado como role especializado em uma crew de agentes para fluxos complexos. Aciona na configuração de crews de automação avançada.

**Examples (few-shot):**
- `"atribui agente"`
- `"designa agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('agent_id', 'crew_id', 'role_name')` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_studio_consumption` — Consumo do Studio

**Descrição completa:**
> Obtém consumo de tokens e créditos dos agentes do Studio no período. Aciona quando recruiter quer controlar custos ou entender billing de agentes.

**Examples (few-shot):**
- `"mostra agente"`
- `"quero ver agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('days',)` |
| `tags` | `[]` |

---

### `deactivate_agent` — Desativar Agente

**Descrição completa:**
> Desativa agente de sourcing ou custom liberando quota da empresa. Requer confirmação. Aciona quando agente não é mais necessário ou quota precisa ser liberada.

**Examples (few-shot):**
- `"desativa este agente"`
- `"pausa o agente temporariamente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('agent_id',)` |
| `optional_params` | `('agent_type',)` |
| `tags` | `[]` |

---

### `uninstall_agent` — Desinstalar Agente

**Descrição completa:**
> Desinstala agente instalado do marketplace liberando quota. Requer confirmação. Aciona quando agente não é mais utilizado.

**Examples (few-shot):**
- `"desinstalar agente"`
- `"quero desinstalar agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('installation_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `explain_agent_studio` — Explicar Agent Studio

**Descrição completa:**
> Explica o que é o Agent Studio, como criar e gerenciar agentes de sourcing e customizados. Aciona quando recruiter pergunta 'o que é o Agent Studio?' ou como começar.

**Examples (few-shot):**
- `"explicar agent studio"`
- `"quero explicar agent studio"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `analytics` (18 actions)

### `generate_kpi_report` — Gerar Relatório de KPIs

**Descrição completa:**
> Gera relatório consolidado de KPIs de recrutamento (tempo de preenchimento, taxa de aprovação, volume de candidatos) para uma vaga ou período. Aciona quando o recrutador pede métricas, indicadores ou relatório gerencial. Saída: documento com gráficos e tabelas.

**Examples (few-shot):**
- `"gera relatório de KPIs do mês"`
- `"cria dashboard de métricas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('period', 'format')` |
| `tags` | `[]` |

---

### `analyze_funnel` — Analisar Funil de Conversão

**Descrição completa:**
> Analisa as métricas do funil de conversão de recrutamento etapa por etapa (candidaturas → triagem → entrevista → oferta). Identifica gargalos e etapas com maior perda. Aciona ao detectar queda de candidatos ou pedir análise de funil.

**Examples (few-shot):**
- `"analisa o funil desta vaga"`
- `"onde estamos perdendo candidatos no funil?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('period', 'stages')` |
| `tags` | `[]` |

---

### `job_health_check` — Verificar Saúde da Vaga

**Descrição completa:**
> Verifica indicadores de saúde da vaga em tempo real: volume de candidatos, taxa de triagem, SLAs, saturação do pipeline e alertas de risco. Aciona ao abrir a vaga no dashboard ou quando recruiter pede 'como está a vaga?'.

**Examples (few-shot):**
- `"checa vaga"`
- `"verifica vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `detect_anomalies` — Detectar Anomalias

**Descrição completa:**
> Detecta anomalias estatísticas nos dados de recrutamento — picos, quedas abruptas, métricas fora do padrão histórico. Aciona automaticamente ou quando recruiter suspeita de problema de qualidade de dados.

**Examples (few-shot):**
- `"detecta anomalias no funil"`
- `"algo está fora do padrão?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('job_id', 'metric', 'threshold')` |
| `tags` | `[]` |

---

### `compare_periods` — Comparar Períodos

**Descrição completa:**
> Compara métricas de recrutamento entre dois períodos de tempo distintos (semana, mês, trimestre). Identifica tendências positivas e negativas. Aciona quando recruiter pergunta 'este mês vs o anterior' ou análises sazonais.

**Examples (few-shot):**
- `"compara este mês com o passado"`
- `"evolução do pipeline mês a mês"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('period_a', 'period_b')` |
| `optional_params` | `('job_id', 'metrics')` |
| `tags` | `[]` |

---

### `forecast` — Previsão de Métricas

**Descrição completa:**
> Prevê métricas e tendências de recrutamento para os próximos dias/semanas usando modelos de IA. Aciona quando recruiter planeja capacidade, quer estimar time-to-fill ou simular cenários futuros.

**Examples (few-shot):**
- `"previsão de métricas"`
- `"quero previsão de métricas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('job_id', 'metric', 'horizon_days')` |
| `tags` | `[]` |

---

### `suggest_strategy` — Sugerir Estratégia

**Descrição completa:**
> Sugere mudanças de estratégia de recrutamento baseadas em dados históricos e benchmarks do mercado via IA. Aciona quando recruiter pede recomendações, plano de ação ou está com a vaga parada.

**Examples (few-shot):**
- `"minha vaga tá parada, o que faço?"`
- `"sugere mudança de estratégia de sourcing"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('context', 'goals')` |
| `tags` | `[]` |

---

### `answer_data_question` — Responder Pergunta sobre Dados

**Descrição completa:**
> Responde perguntas abertas sobre dados e analytics de recrutamento usando linguagem natural. Aciona para qualquer pergunta analítica: 'quantos candidatos passaram?', 'qual a taxa de aprovação?', 'quando a vaga vai fechar?'.

**Examples (few-shot):**
- `"responder pergunta sobre dados"`
- `"quero responder pergunta sobre dados"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('question',)` |
| `optional_params` | `('job_id', 'context')` |
| `tags` | `[]` |

---

### `get_job_insights` — Obter Insights da Vaga

**Descrição completa:**
> Obtém insights combinados da vaga: benchmarks salariais do mercado, competências mais demandadas e vagas similares publicadas. Aciona quando recruiter quer contextualizar a vaga ou negociar salário.

**Examples (few-shot):**
- `"mostra vaga"`
- `"quero ver vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('include_salary', 'include_skills', 'include_similar')` |
| `tags` | `[]` |

---

### `generate_job_report` — Gerar Relatório da Vaga

**Descrição completa:**
> Gera relatório completo da vaga em formato PDF ou Excel com histórico de candidatos, métricas e análise de pipeline. Aciona quando recruiter precisa apresentar resultados ao cliente ou ao hiring manager.

**Examples (few-shot):**
- `"gera vaga"`
- `"crie vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('format', 'sections')` |
| `tags` | `[]` |

---

### `generate_candidate_report` — Gerar Relatório de Candidato

**Descrição completa:**
> Gera relatório comparativo de candidatos selecionados com scores WSI, competências e recomendação final. Aciona antes de apresentar shortlist ao hiring manager ou para decisão de oferta.

**Examples (few-shot):**
- `"gera candidato"`
- `"crie candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_ids',)` |
| `optional_params` | `('job_id', 'format', 'criteria')` |
| `tags` | `[]` |

---

### `get_search_analytics` — Analytics de Busca

**Descrição completa:**
> Obtém analytics de desempenho das buscas de candidatos: taxa de match, qualidade dos resultados, estratégias mais eficazes. Aciona quando recruiter avalia efetividade do sourcing.

**Examples (few-shot):**
- `"mostra métricas"`
- `"quero ver métricas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('period', 'search_type')` |
| `tags` | `[]` |

---

### `get_wizard_analytics` — Analytics do Wizard

**Descrição completa:**
> Obtém métricas de uso do wizard de criação de vagas: tempo médio, etapas com mais abandono, campos mais editados. Aciona para análise de UX e melhoria de processo.

**Examples (few-shot):**
- `"mostra métricas"`
- `"quero ver métricas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('period',)` |
| `tags` | `[]` |

---

### `predict_hiring_probability` — Prever Probabilidade de Contratação

**Descrição completa:**
> Prevê via IA a probabilidade de sucesso na contratação para uma vaga ou candidato específico, baseado em dados históricos de vagas similares. Aciona quando recruiter quer priorizar vagas ou candidatos.

**Examples (few-shot):**
- `"prever probabilidade de contratação"`
- `"quero prever probabilidade de contratação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('candidate_id',)` |
| `tags` | `[]` |

---

### `predict_time_to_fill` — Prever Tempo de Preenchimento

**Descrição completa:**
> Estima o tempo necessário para preencher uma posição com base em histórico de vagas similares, mercado e pipeline atual. Aciona quando recruiter planeja prazo de entrega para o cliente.

**Examples (few-shot):**
- `"prever tempo de preenchimento"`
- `"quero prever tempo de preenchimento"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `predict_dropout_risk` — Prever Risco de Desistência

**Descrição completa:**
> Prevê o risco de desistência do candidato em cada etapa do pipeline usando IA. Aciona para intervir proativamente com candidatos de alto risco antes da perda.

**Examples (few-shot):**
- `"prever risco de desistência"`
- `"quero prever risco de desistência"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id',)` |
| `optional_params` | `('job_id',)` |
| `tags` | `[]` |

---

### `get_dashboard_data` — Dados do Dashboard

**Descrição completa:**
> Obtém indicadores estratégicos do dashboard principal: vagas ativas, pipeline geral, alertas e KPIs do período. Aciona ao abrir o dashboard ou pedir visão geral do recrutamento.

**Examples (few-shot):**
- `"mostra KPIs"`
- `"quero ver KPIs"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('period', 'metrics')` |
| `tags` | `[]` |

---

### `get_agent_monitoring` — Monitoramento de Agentes

**Descrição completa:**
> Monitora o desempenho dos agentes de IA: chamadas, latência, taxa de sucesso, uso de tokens e erros recentes. Aciona para diagnóstico de problemas com agentes ou análise de custos.

**Examples (few-shot):**
- `"mostra agente"`
- `"quero ver agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('agent_type', 'period')` |
| `tags` | `[]` |

---

### Domínio: `ats_integration` (18 actions)

### `sync_candidate` — Sincronizar Candidato

**Descrição completa:**
> Sincroniza dados de um candidato com o ATS externo (Greenhouse, Lever, etc.), propagando atualizações de status, score WSI e dados de perfil. Aciona após mudança de etapa ou avaliação de candidato quando há integração ativa.

**Examples (few-shot):**
- `"sincroniza candidato"`
- `"atualiza candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id',)` |
| `optional_params` | `('ats_provider', 'connection_id')` |
| `tags` | `[]` |

---

### `sync_job` — Sincronizar Vaga

**Descrição completa:**
> Sincroniza dados de uma vaga com o ATS externo, incluindo requisitos, status e configurações de pipeline. Aciona após criação ou atualização de vaga quando há integração ATS configurada.

**Examples (few-shot):**
- `"sincroniza vaga"`
- `"atualiza vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('job_id',)` |
| `optional_params` | `('ats_provider', 'connection_id')` |
| `tags` | `[]` |

---

### `bulk_sync` — Sincronização em Massa

**Descrição completa:**
> Executa sincronização em massa de múltiplos candidatos ou vagas com o ATS externo. Requer confirmação. Aciona para sincronização inicial ou reconciliação periódica entre sistemas.

**Examples (few-shot):**
- `"sincroniza tudo do ATS agora"`
- `"faz sync completo"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('sync_type',)` |
| `optional_params` | `('ats_provider', 'connection_id', 'filters')` |
| `tags` | `[]` |

---

### `pull_candidates` — Importar Candidatos

**Descrição completa:**
> Importa candidatos do ATS externo para o WedoTalent, criando ou atualizando perfis existentes. Aciona quando recruiter quer trazer dados do ATS para usar nas ferramentas de triagem da LIA.

**Examples (few-shot):**
- `"importar candidatos"`
- `"quero importar candidatos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('ats_provider', 'connection_id', 'job_id', 'limit')` |
| `tags` | `[]` |

---

### `pull_jobs` — Importar Vagas

**Descrição completa:**
> Importa vagas do ATS externo para o WedoTalent, sincronizando requisitos e status. Aciona para iniciar gestão de vagas existentes no ATS usando a plataforma LIA.

**Examples (few-shot):**
- `"importar vagas"`
- `"quero importar vagas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('ats_provider', 'connection_id', 'status', 'limit')` |
| `tags` | `[]` |

---

### `check_sync_status` — Verificar Status da Sincronização

**Descrição completa:**
> Verifica o status atual de sincronização com o ATS: pendentes, erros, última execução e taxa de sucesso. Aciona para diagnóstico de problemas de integração ou verificação pós-sincronização.

**Examples (few-shot):**
- `"qual status da sincronização?"`
- `"o sync já terminou?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('connection_id', 'sync_job_id')` |
| `tags` | `[]` |

---

### `configure_ats` — Configurar ATS

**Descrição completa:**
> Configura conexão e credenciais do ATS externo (API key, endpoint, mapeamentos). Requer confirmação. Aciona durante setup inicial de integração ou quando credenciais mudam.

**Examples (few-shot):**
- `"configura integração com ATS"`
- `"conecta com Workday"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('ats_provider',)` |
| `optional_params` | `('api_key', 'api_endpoint', 'company_id')` |
| `tags` | `[]` |

---

### `list_connections` — Listar Conexões ATS

**Descrição completa:**
> Lista todas as conexões ATS configuradas pela empresa com status de saúde e última sincronização. Aciona para gerenciamento de integrações ou escolha de conexão ativa.

**Examples (few-shot):**
- `"lista integrações ativas"`
- `"quais ATS estão conectados?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('ats_provider', 'is_active')` |
| `tags` | `[]` |

---

### `test_connection` — Testar Conexão

**Descrição completa:**
> Testa a saúde da conexão com o ATS verificando autenticação e disponibilidade do endpoint. Aciona antes de sincronizações críticas ou para diagnóstico de falhas de conexão.

**Examples (few-shot):**
- `"testa a conexão com o ATS"`
- `"o ATS está respondendo?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('connection_id', 'ats_provider')` |
| `tags` | `[]` |

---

### `map_fields` — Mapear Campos

**Descrição completa:**
> Configura o mapeamento de campos entre o WedoTalent e o ATS externo para garantir que dados fluam corretamente. Requer confirmação. Aciona durante configuração ou quando campos mudam no ATS.

**Examples (few-shot):**
- `"mapear campos"`
- `"quero mapear campos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('connection_id',)` |
| `optional_params` | `('field_mappings',)` |
| `tags` | `[]` |

---

### `view_sync_log` — Ver Log de Sincronização

**Descrição completa:**
> Visualiza o log de auditoria de sincronização com registros de operações, erros e dados trocados. Aciona para auditoria, compliance ou debug de sincronizações que falharam.

**Examples (few-shot):**
- `"mostra mapeamento de campos"`
- `"como os campos estão mapeados?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('connection_id', 'sync_job_id', 'limit')` |
| `tags` | `[]` |

---

### `resolve_conflict` — Resolver Conflito de Dados

**Descrição completa:**
> Resolve conflitos de dados detectados entre WedoTalent e ATS externo, escolhendo qual sistema prevalece. Requer confirmação. Aciona quando sync report indica dados divergentes.

**Examples (few-shot):**
- `"resolver conflito de dados"`
- `"quero resolver conflito de dados"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('conflict_id',)` |
| `optional_params` | `('resolution_strategy',)` |
| `tags` | `[]` |

---

### `update_status_ats` — Atualizar Status no ATS

**Descrição completa:**
> Envia atualização de status do candidato (aprovado, rejeitado, em processo) para o ATS externo em tempo real. Aciona automaticamente após mudança de etapa quando integração está ativa.

**Examples (few-shot):**
- `"atualiza status no ATS externo"`
- `"sincroniza status do candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id', 'new_status')` |
| `optional_params` | `('connection_id', 'reason')` |
| `tags` | `[]` |

---

### `send_score_ats` — Enviar Score para ATS

**Descrição completa:**
> Envia score e parecer WSI do candidato para o campo correspondente no ATS externo. Aciona após avaliação WSI quando há integração ativa configurada.

**Examples (few-shot):**
- `"envia score"`
- `"manda score"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id',)` |
| `optional_params` | `('connection_id', 'score', 'parecer')` |
| `tags` | `[]` |

---

### `sync_interview_result` — Sincronizar Resultado de Entrevista

**Descrição completa:**
> Sincroniza resultados de entrevista (scorecard, notas, recomendação) com o ATS externo. Aciona após conclusão de entrevista estruturada quando integração está ativa.

**Examples (few-shot):**
- `"sincroniza entrevista"`
- `"atualiza entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id',)` |
| `optional_params` | `('connection_id', 'candidate_id')` |
| `tags` | `[]` |

---

### `enable_webhook` — Ativar Webhook

**Descrição completa:**
> Ativa webhook para sincronização em tempo real entre o ATS e a plataforma LIA para eventos específicos. Aciona durante configuração de integração para automação de sincronização bidirecional.

**Examples (few-shot):**
- `"ativar webhook"`
- `"quero ativar webhook"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('connection_id',)` |
| `optional_params` | `('events',)` |
| `tags` | `[]` |

---

### `disable_webhook` — Desativar Webhook

**Descrição completa:**
> Desativa webhook de sincronização com o ATS parando eventos em tempo real. Aciona quando integração precisa ser suspensa temporariamente ou webhook está causando erros.

**Examples (few-shot):**
- `"desativar webhook"`
- `"quero desativar webhook"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('connection_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `view_field_mapping` — Ver Mapeamento de Campos

**Descrição completa:**
> Visualiza o mapeamento atual de campos entre WedoTalent e o ATS externo. Aciona para auditoria, verificação de configuração ou antes de alterar mapeamentos.

**Examples (few-shot):**
- `"mostra mapeamento de campos"`
- `"como os campos estão mapeados?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('connection_id', 'ats_provider')` |
| `tags` | `[]` |

---

### Domínio: `automation` (20 actions)

### `create_task` — Criar Tarefa

**Descrição completa:**
> Cria nova tarefa planejada no sistema de automação com título, descrição, agente responsável e prazo. Aciona quando recruiter ou orquestrador precisa registrar uma atividade para execução futura ou delegação.

**Examples (few-shot):**
- `"cria tarefa para o time"`
- `"adiciona lembrete de follow-up"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_tasks` — Listar Tarefas

**Descrição completa:**
> Lista tarefas ativas e seus status (pendente, em execução, concluída, bloqueada) para o objetivo atual. Aciona quando recruiter quer ver o progresso do pipeline de automação ou tarefas pendentes.

**Examples (few-shot):**
- `"lista minhas tarefas pendentes"`
- `"mostra tasks do dia"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `complete_task` — Concluir Tarefa

**Descrição completa:**
> Marca tarefa como concluída registrando o resultado e liberando tarefas dependentes bloqueadas. Requer confirmação. Aciona ao finalizar execução de uma subtarefa no fluxo de automação.

**Examples (few-shot):**
- `"concluir tarefa"`
- `"quero concluir tarefa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `cancel_task` — Cancelar Tarefa

**Descrição completa:**
> Cancela tarefa pendente com motivo, liberando recursos alocados e notificando tarefas dependentes. Requer confirmação. Aciona quando tarefa não é mais necessária ou contexto mudou.

**Examples (few-shot):**
- `"cancela tarefa"`
- `"desiste de tarefa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `decompose_task` — Decompor Tarefa

**Descrição completa:**
> Decompõe tarefa complexa em subtarefas menores via IA, atribuindo agente responsável, prioridade e dependências para cada uma. Aciona ao receber objetivo de alto nível que requer orquestração multi-agente.

**Examples (few-shot):**
- `"decompor tarefa"`
- `"quero decompor tarefa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `plan_execution` — Planejar Execução

**Descrição completa:**
> Cria plano de execução validado com níveis paralelos e mapa de dependências para um conjunto de tarefas. Aciona após decomposição para preparar pipeline de execução autônoma.

**Examples (few-shot):**
- `"planejar execução"`
- `"quero planejar execução"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_next_tasks` — Próximas Tarefas

**Descrição completa:**
> Obtém próximas tarefas prontas para execução (todas as dependências concluídas) filtradas por agente e objetivo. Aciona no loop de execução autônoma para buscar trabalho disponível.

**Examples (few-shot):**
- `"mostra tarefa"`
- `"quero ver tarefa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `create_automation` — Criar Automação

**Descrição completa:**
> Cria nova regra de automação que dispara ações automaticamente baseado em eventos do pipeline (mudança de etapa, SLA vencido, etc.). Requer confirmação. Aciona quando recruiter quer automatizar tarefa recorrente.

**Examples (few-shot):**
- `"cria automação"`
- `"quero um automação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_automations` — Listar Automações

**Descrição completa:**
> Lista regras de automação configuradas pela empresa com status ativo/inativo e métricas de execução. Aciona para gestão das automações existentes ou verificar o que está rodando.

**Examples (few-shot):**
- `"lista automação"`
- `"mostra automação ativas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `enable_automation` — Ativar Automação

**Descrição completa:**
> Ativa regra de automação previamente criada para que comece a disparar ações automaticamente. Requer confirmação. Aciona quando automação está pronta para produção.

**Examples (few-shot):**
- `"ativar automação"`
- `"quero ativar automação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `disable_automation` — Desativar Automação

**Descrição completa:**
> Desativa regra de automação parando execuções automáticas sem excluí-la. Requer confirmação. Aciona para pausar automação temporariamente ou quando está causando comportamento indesejado.

**Examples (few-shot):**
- `"desativar automação"`
- `"quero desativar automação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `trigger_automation` — Disparar Automação

**Descrição completa:**
> Dispara manualmente uma automação configurada para execução imediata fora do gatilho automático. Requer confirmação. Aciona para teste de automação ou execução manual pontual.

**Examples (few-shot):**
- `"dispara automação"`
- `"ativa automação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `view_automation_log` — Ver Log de Automação

**Descrição completa:**
> Visualiza histórico de execuções de automações com timestamps, resultados e erros. Aciona para auditoria, debug de automações falhas ou compliance.

**Examples (few-shot):**
- `"ver automação"`
- `"mostra automação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `configure_stage_automation` — Configurar Automação de Etapa

**Descrição completa:**
> Configura automação de transição de etapa do pipeline (ex: ao aprovado em triagem → enviar convite de entrevista). Requer confirmação. Aciona na configuração de fluxos automáticos de pipeline.

**Examples (few-shot):**
- `"configura automação"`
- `"define automação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `predict_substatus` — Prever Sub-status

**Descrição completa:**
> Prevê via IA o próximo sub-status mais provável para um candidato baseado no histórico e comportamento. Aciona para sugestões proativas de próxima ação ou alertas de risco de perda.

**Examples (few-shot):**
- `"prever sub-status"`
- `"quero prever sub-status"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `check_proactive_alerts` — Verificar Alertas Proativos

**Descrição completa:**
> Verifica alertas proativos ativos para o recrutador: SLAs vencidos, candidatos parados, vagas sem movimento. Aciona no briefing diário ou quando recruiter pede 'o que precisa de atenção?'.

**Examples (few-shot):**
- `"vê alertas proativos"`
- `"tem novos alertas?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `configure_alert` — Configurar Alerta

**Descrição completa:**
> Configura regras de alertas proativos com threshold, canal de notificação e frequência. Requer confirmação. Aciona quando recruiter quer personalizar quais alertas receber.

**Examples (few-shot):**
- `"configura novo alerta"`
- `"cria alerta pra vaga parada"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `schedule_recurring` — Agendar Tarefa Recorrente

**Descrição completa:**
> Agenda tarefa recorrente de automação com frequência (diária, semanal, mensal). Requer confirmação. Aciona para criar relatórios automáticos ou verificações periódicas.

**Examples (few-shot):**
- `"agenda task recorrente"`
- `"marca lembrete semanal"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `view_task_dependencies` — Ver Dependências

**Descrição completa:**
> Visualiza o grafo de dependências das tarefas planejadas mostrando ordem de execução e bloqueios. Aciona para debug de pipeline travado ou para entender sequência de automação.

**Examples (few-shot):**
- `"ver tarefa"`
- `"mostra tarefa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `run_autonomous_check` — Executar Verificação Autônoma

**Descrição completa:**
> Executa verificação autônoma de background check de candidato via agente de IA. Requer confirmação. Aciona para validação de informações de candidatos finalistas.

**Examples (few-shot):**
- `"roda agente"`
- `"executa agente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `candidate_self_service` (4 actions)

### `get_status` — Consultar Status da Candidatura

**Descrição completa:**
> Retorna etapa atual, data de entrada e próximos passos

**Examples (few-shot):**
- `"qual meu status no processo?"`
- `"em que etapa estou?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id', 'vacancy_id')` |
| `optional_params` | `[]` |
| `tags` | `('status', 'pipeline')` |

---

### `get_interview_info` — Consultar Entrevista Agendada

**Descrição completa:**
> Retorna data, horário e formato da entrevista agendada (se houver)

**Examples (few-shot):**
- `"quando é minha entrevista?"`
- `"mostra detalhes da minha entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id', 'vacancy_id')` |
| `optional_params` | `[]` |
| `tags` | `('interview', 'scheduling')` |

---

### `get_feedback` — Consultar Feedback da Triagem

**Descrição completa:**
> Retorna feedback estruturado WSI se disponibilizado pela empresa

**Examples (few-shot):**
- `"qual o feedback sobre mim?"`
- `"teve retorno da entrevista?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id', 'vacancy_id')` |
| `optional_params` | `[]` |
| `tags` | `('feedback', 'wsi')` |

---

### `get_lgpd_info` — Solicitar Explicação LGPD

**Descrição completa:**
> Informa sobre direito de explicação (LGPD Art. 20) e canal de contato

**Examples (few-shot):**
- `"quais dados vocês têm de mim?"`
- `"mostra meus direitos LGPD"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id',)` |
| `optional_params` | `[]` |
| `tags` | `('lgpd', 'compliance')` |

---

### Domínio: `communication` (20 actions)

### `send_email` — Enviar Email

**Descrição completa:**
> Envia email individual personalizado para candidato ou stakeholder usando templates ou texto livre. Requer confirmação. Aciona quando recruiter pede para enviar email, comunicar resultado ou fazer follow-up.

**Examples (few-shot):**
- `"envia email pra Maria confirmando entrevista"`
- `"manda um feedback pro candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_bulk_email` — Enviar Email em Massa

**Descrição completa:**
> Envia email em massa para múltiplos destinatários simultaneamente usando template selecionado com personalização por candidato. Requer confirmação. Aciona para comunicações em lote como rejeições ou avanços de processo.

**Examples (few-shot):**
- `"envia email pra todos os reprovados"`
- `"manda comunicação em massa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_candidate_report` — Enviar Parecer ao Gestor

**Descrição completa:**
> Envia relatório ou parecer completo do candidato para o gestor contratante com score WSI, pontos fortes e recomendação. Requer confirmação. Aciona ao avançar candidato para entrevista com hiring manager.

**Examples (few-shot):**
- `"envia parecer do candidato pro gestor"`
- `"manda relatório do Fernando pra Ana"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_progress_report` — Relatório de Progresso

**Descrição completa:**
> Envia relatório de andamento da vaga para stakeholders com métricas atuais, pipeline e próximos passos. Aciona para comunicação proativa com clientes ou quando gestor pede atualização de status.

**Examples (few-shot):**
- `"envia relatório de progresso"`
- `"atualiza o cliente sobre a vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_kpi_report` — Relatório de KPIs

**Descrição completa:**
> Envia relatório consolidado de KPIs de recrutamento para liderança ou cliente. Requer confirmação. Aciona em ciclos semanais/mensais de reporting ou quando solicitado por stakeholder.

**Examples (few-shot):**
- `"envia relatório de KPIs"`
- `"manda dashboard pro time"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_feedback` — Enviar Feedback

**Descrição completa:**
> Envia feedback personalizado ao candidato sobre o resultado do processo seletivo, respeitando LGPD. Requer confirmação. Aciona quando candidato é rejeitado e recruiter quer dar devolutiva de qualidade.

**Examples (few-shot):**
- `"envia feedback pro candidato"`
- `"manda retorno da entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `create_template` — Criar Template

**Descrição completa:**
> Cria novo template de email reutilizável para comunicações padronizadas (convite, rejeição, oferta, etc.). Aciona quando recruiter precisa de novo template para situação não coberta pelos existentes.

**Examples (few-shot):**
- `"cria template"`
- `"quero um template"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `edit_template` — Editar Template

**Descrição completa:**
> Edita template de email existente com novo conteúdo, assunto ou personalização. Aciona para atualizar comunicações desatualizadas ou personalizar templates padrão da empresa.

**Examples (few-shot):**
- `"edita template"`
- `"altera template"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_templates` — Listar Templates

**Descrição completa:**
> Lista templates de email disponíveis filtrados por tipo (candidato, gestor, sistema) e status. Aciona quando recruiter quer escolher template para comunicação ou gerenciar biblioteca.

**Examples (few-shot):**
- `"lista template"`
- `"mostra template ativas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `preview_template` — Visualizar Template

**Descrição completa:**
> Pré-visualiza template de email com dados reais do candidato antes de enviar. Aciona antes de envio para verificar personalização e conteúdo estão corretos.

**Examples (few-shot):**
- `"visualizar template"`
- `"quero visualizar template"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `notify_stakeholders` — Notificar Stakeholders

**Descrição completa:**
> Envia notificação para stakeholders (hiring manager, HRBP, cliente) sobre eventos críticos do processo seletivo. Requer confirmação. Aciona em marcos importantes: candidato aprovado, vaga fechada, oferta aceita.

**Examples (few-shot):**
- `"notifica stakeholders da vaga"`
- `"avisa os interessados"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_whatsapp` — Enviar WhatsApp

**Descrição completa:**
> Envia mensagem via WhatsApp para candidato usando template aprovado ou mensagem personalizada. Requer confirmação. Aciona quando candidato prefere WhatsApp ou resposta rápida é necessária.

**Examples (few-shot):**
- `"manda whatsapp pro candidato confirmar horário"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_teams_message` — Enviar Mensagem Teams

**Descrição completa:**
> Envia mensagem via Microsoft Teams para recruiter ou stakeholder interno. Requer confirmação. Aciona para notificações urgentes de equipe interna ou comunicações com hiring manager via Teams.

**Examples (few-shot):**
- `"envia mensagem"`
- `"manda mensagem"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_sms` — Enviar SMS

**Descrição completa:**
> Envia SMS para candidato para lembretes ou confirmações urgentes. Requer confirmação. Aciona quando tempo de resposta é crítico ou candidato não respondeu ao email.

**Examples (few-shot):**
- `"envia SMS pro candidato"`
- `"manda mensagem curta"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_communication_history` — Histórico de Comunicação

**Descrição completa:**
> Obtém histórico completo de comunicações com um candidato (emails, WhatsApp, SMS) com timestamps e status de entrega. Aciona para contexto antes de nova comunicação ou auditoria de interações.

**Examples (few-shot):**
- `"mostra email"`
- `"quero ver email"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_screening_invite` — Convite de Triagem

**Descrição completa:**
> Envia convite para triagem WSI ao candidato com link e instruções. Requer confirmação. Aciona após aprovação de candidato na primeira etapa de análise de currículo.

**Examples (few-shot):**
- `"envia WSI"`
- `"manda WSI"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_interview_invite` — Convite de Entrevista

**Descrição completa:**
> Envia convite de entrevista ao candidato com data, horário, formato e informações do entrevistador. Requer confirmação. Aciona após scheduling confirmar horário disponível.

**Examples (few-shot):**
- `"envia entrevista"`
- `"manda entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `update_preferences` — Preferências de Comunicação

**Descrição completa:**
> Atualiza preferências de comunicação do candidato: canal preferido (email/WhatsApp/SMS) e horários. Aciona quando candidato solicita mudança de canal ou previamente à primeira comunicação.

**Examples (few-shot):**
- `"atualiza email"`
- `"muda email"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `manage_webhook` — Gerenciar Webhook

**Descrição completa:**
> Configura e gerencia webhooks de comunicação para integração com ferramentas externas (Zapier, n8n, ATS). Aciona na configuração de integrações de comunicação automática.

**Examples (few-shot):**
- `"gerenciar webhook"`
- `"quero gerenciar webhook"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `handle_data_request` — Solicitação de Dados

**Descrição completa:**
> Processa solicitação de dados pessoais ou exclusão (LGPD/GDPR) do candidato, registrando no audit trail. Requer confirmação. Aciona quando candidato exerce direito de acesso ou exclusão de dados.

**Examples (few-shot):**
- `"solicitação de dados"`
- `"quero solicitação de dados"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `company_settings` (7 actions)

### `configure_profile` — Configurar Perfil da Empresa

**Descrição completa:**
> Configura dados institucionais da empresa (nome, CNPJ, website, etc.)

**Examples (few-shot):**
- `"configura perfil da empresa"`
- `"edita dados institucionais"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'profile')` |

---

### `configure_culture` — Configurar Cultura & EVP

**Descrição completa:**
> Configura missao, visao, valores, cultura e proposta de valor

**Examples (few-shot):**
- `"configura cultura e valores"`
- `"define missão e visão"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'culture')` |

---

### `configure_tech_stack` — Configurar Tech Stack

**Descrição completa:**
> Configura stack tecnologico e cultura de engenharia

**Examples (few-shot):**
- `"configura tech stack"`
- `"define as tecnologias usadas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'tech')` |

---

### `configure_benefits` — Configurar Beneficios

**Descrição completa:**
> Configura pacote de beneficios da empresa

**Examples (few-shot):**
- `"configura benefícios"`
- `"define pacote de benefícios"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'benefits')` |

---

### `configure_workforce` — Configurar Planejamento de Contratacoes

**Descrição completa:**
> Configura planejamento de contratacoes (workforce planning)

**Examples (few-shot):**
- `"configura planejamento de contratações"`
- `"define workforce planning"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'workforce')` |

---

### `analyze_website` — Analisar Website

**Descrição completa:**
> Analisa website da empresa para extrair dados automaticamente

**Examples (few-shot):**
- `"analisa nosso site pra extrair dados"`
- `"olha no website e extrai info"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'analysis')` |

---

### `process_document` — Processar Documento

**Descrição completa:**
> Processa documento enviado para extrair dados da empresa

**Examples (few-shot):**
- `"processa este documento da empresa"`
- `"extrai dados deste arquivo"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('company', 'document')` |

---

### Domínio: `cv_screening` (24 actions)

### `parse_cv` — Analisar CV

**Descrição completa:**
> Analisa e extrai dados estruturados do currículo: experiências, competências, formação, idiomas e contatos. Aciona como primeira etapa ao receber candidatura ou ao adicionar candidato manualmente ao pipeline.

**Examples (few-shot):**
- `"analisa esse currículo que anexei"`
- `"extrai os dados deste CV"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `auto_screen` — Triagem automática

**Descrição completa:**
> Executa triagem automática do candidato contra os requisitos da vaga usando score WSI e rubricas configuradas. Aciona após parse_cv para aprovação/rejeição automática com base em critérios objetivos.

**Examples (few-shot):**
- `"triagem automática"`
- `"quero triagem automática"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `batch_screen` — Triagem em lote

**Descrição completa:**
> Executa triagem em lote de múltiplos candidatos simultaneamente para ranqueamento eficiente. Aciona quando há acúmulo de candidaturas ou para triagem semanal de novos candidatos.

**Examples (few-shot):**
- `"triagem em lote"`
- `"quero triagem em lote"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `calculate_wsi_score` — Calcular WSI

**Descrição completa:**
> Calcula o score WSI (Work Style Interview) do candidato baseado no CV e competências mapeadas para a vaga. Aciona após parse_cv ou quando recruiter quer pontuação para comparação.

**Examples (few-shot):**
- `"calcula WSI"`
- `"computa WSI"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `rank_candidates` — Rankear candidatos

**Descrição completa:**
> Ordena candidatos por score WSI e compatibilidade com a vaga para priorização do pipeline. Aciona quando recruiter pede ranqueamento ou antes de apresentar shortlist.

**Examples (few-shot):**
- `"ranqueia os candidatos por fit"`
- `"ordena por score WSI"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `dynamic_cutoff` — Corte dinâmico

**Descrição completa:**
> Aplica corte dinâmico ao pipeline retendo apenas o top 25% dos candidatos com base nos scores. Aciona quando pipeline está saturado e recruiter precisa focar nos melhores candidatos.

**Examples (few-shot):**
- `"corte dinâmico"`
- `"quero corte dinâmico"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `detect_red_flags` — Detectar red flags

**Descrição completa:**
> Detecta red flags no currículo: gaps não explicados, inconsistências de datas, histórico de rotatividade elevada. Aciona durante triagem para alertar recruiter sobre riscos antes de avançar candidato.

**Examples (few-shot):**
- `"detecta red flags neste CV"`
- `"tem algum risco neste perfil?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `check_saturation` — Verificar saturação

**Descrição completa:**
> Verifica se o pipeline de candidatos está saturado com volume suficiente para preenchimento da vaga. Aciona para decidir se sourcing deve continuar ou pausar.

**Examples (few-shot):**
- `"checa pipeline"`
- `"verifica pipeline"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `classify_bloom` — Classificar Bloom

**Descrição completa:**
> Classifica respostas do candidato pela Taxonomia de Bloom para avaliar profundidade de raciocínio (do básico ao criativo). Aciona durante avaliação de respostas de entrevistas estruturadas.

**Examples (few-shot):**
- `"classificar bloom"`
- `"quero classificar bloom"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `classify_dreyfus` — Classificar Dreyfus

**Descrição completa:**
> Classifica o nível de proficiência do candidato no modelo Dreyfus (novice → expert) para competências técnicas. Aciona na avaliação de seniority para vagas técnicas.

**Examples (few-shot):**
- `"classificar dreyfus"`
- `"quero classificar dreyfus"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `map_big_five` — Mapear Big Five

**Descrição completa:**
> Mapeia traços comportamentais do candidato no modelo Big Five (abertura, consciência, extroversão, amabilidade, neuroticismo). Aciona na avaliação comportamental de candidatos finalistas.

**Examples (few-shot):**
- `"mapear big five"`
- `"quero mapear big five"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `validate_cbi` — Validar CBI

**Descrição completa:**
> Valida respostas do candidato contra o framework CBI (Competency-Based Interview) verificando evidências comportamentais. Aciona durante entrevista estruturada para garantir qualidade das evidências coletadas.

**Examples (few-shot):**
- `"valida entrevista"`
- `"verifica entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `generate_report` — Gerar parecer

**Descrição completa:**
> Gera parecer completo do candidato com score WSI, análise de competências, red flags e recomendação final. Aciona antes de apresentar candidato ao hiring manager.

**Examples (few-shot):**
- `"gera relatório"`
- `"crie relatório"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `compare_candidates` — Comparar candidatos

**Descrição completa:**
> Compara candidatos selecionados lado a lado em dimensões de competência, score e fit cultural. Aciona quando recruiter tem múltiplos finalistas e precisa decidir quem avançar.

**Examples (few-shot):**
- `"compara estes dois candidatos"`
- `"qual é melhor entre esses perfis?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `calibrate_model` — Calibrar modelo

**Descrição completa:**
> Calibra o modelo de triagem com feedback explícito do recrutador sobre candidatos aprovados e rejeitados. Aciona periodicamente para melhorar precisão da triagem automática.

**Examples (few-shot):**
- `"calibra modelo de triagem"`
- `"ajusta pontuação de fit"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `explain_score` — Explicar score

**Descrição completa:**
> Explica detalhadamente como o score WSI do candidato foi calculado, indicando quais competências contribuíram e quais faltam. Aciona quando recruiter ou candidato questiona o resultado.

**Examples (few-shot):**
- `"pontua score"`
- `"calcula score de score"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `evaluate_rubric` — Avaliar rubrica

**Descrição completa:**
> Avalia candidato por rubrica estruturada com critérios e pesos específicos da vaga. Aciona para avaliação padronizada e comparável entre candidatos.

**Examples (few-shot):**
- `"avalia rubrica"`
- `"analisa rubrica"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `generate_questions` — Gerar perguntas

**Descrição completa:**
> Gera perguntas de triagem WSI personalizadas para a vaga com base nos requisitos e competências mapeadas. Aciona na configuração de nova vaga ou antes de entrevista estruturada.

**Examples (few-shot):**
- `"gera pergunta"`
- `"crie pergunta"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `adjust_questions` — Ajustar perguntas

**Descrição completa:**
> Ajusta e refina perguntas de triagem com IA baseado em feedback do recruiter ou resultados anteriores. Aciona quando perguntas estão muito fáceis/difíceis ou não discriminam candidatos.

**Examples (few-shot):**
- `"ajustar perguntas"`
- `"quero ajustar perguntas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `voice_screening` — Triagem por voz

**Descrição completa:**
> Executa triagem por voz com candidato usando metodologia WSI via interface de áudio. Aciona quando candidato prefere formato oral ou para agilizar triagem inicial.

**Examples (few-shot):**
- `"triagem por voz"`
- `"quero triagem por voz"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `normalize_scores` — Normalizar scores

**Descrição completa:**
> Normaliza scores entre candidatos de diferentes buscas para comparação justa em base comum. Aciona ao combinar resultados de múltiplos processos de triagem.

**Examples (few-shot):**
- `"normalizar scores"`
- `"quero normalizar scores"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `assess_seniority` — Avaliar senioridade

**Descrição completa:**
> Avalia e classifica o nível de senioridade do candidato (júnior, pleno, sênior, especialista) com base no CV e respostas. Aciona para alocação correta em vagas de nível específico.

**Examples (few-shot):**
- `"avaliar senioridade"`
- `"quero avaliar senioridade"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `send_feedback` — Enviar feedback

**Descrição completa:**
> Envia feedback personalizado ao candidato sobre o resultado da triagem com pontos positivos e áreas de desenvolvimento. Aciona após rejeição quando empresa quer oferecer experiência de qualidade.

**Examples (few-shot):**
- `"envia feedback pro candidato"`
- `"manda retorno da entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `pre_qualify` — Pré-qualificar

**Descrição completa:**
> Pré-qualifica candidato com perguntas rápidas antes da triagem formal para filtrar desqualificadores objetivos (localização, salário, disponibilidade). Aciona como etapa zero antes do processo completo.

**Examples (few-shot):**
- `"pré-qualifica este candidato"`
- `"faz primeira triagem"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `digital_twin` (5 actions)

### `create_twin` — Criar Digital Twin

**Descrição completa:**
> Cria Digital Twin de um especialista da empresa para replicar seu raciocínio de avaliação de candidatos. Aciona quando empresa quer escalar conhecimento de especialista para avaliações consistentes.

**Examples (few-shot):**
- `"cria digital twin"`
- `"quero um digital twin"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('twin_name',)` |
| `optional_params` | `('sme_user_id', 'specialties')` |
| `tags` | `[]` |

---

### `evaluate_with_twin` — Avaliar com Twin

**Descrição completa:**
> Avalia candidato usando o raciocínio replicado do Digital Twin do especialista para decisão de fit. Aciona como etapa avançada de avaliação de candidatos finalistas quando Twin está disponível.

**Examples (few-shot):**
- `"avalia digital twin"`
- `"analisa digital twin"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('twin_id', 'candidate_id')` |
| `optional_params` | `('job_id',)` |
| `tags` | `[]` |

---

### `list_twins` — Listar Twins

**Descrição completa:**
> Lista Digital Twins disponíveis na empresa com especialidade e status de treinamento. Aciona quando recruiter quer escolher qual Twin usar ou verificar quais estão prontos.

**Examples (few-shot):**
- `"lista digital twin"`
- `"mostra digital twin ativas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `index_twin_audio` — Treinar Twin com Áudio

**Descrição completa:**
> Treina o Digital Twin indexando gravação de entrevista realizada pelo especialista para aprender seu padrão de avaliação. Aciona durante calibração do Twin com novas entrevistas do especialista.

**Examples (few-shot):**
- `"treinar twin com áudio"`
- `"quero treinar twin com áudio"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('twin_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `deactivate_twin` — Desativar Twin

**Descrição completa:**
> Desativa Digital Twin liberando quota da empresa. Requer confirmação. Aciona quando especialista saiu da empresa ou Twin não é mais utilizado.

**Examples (few-shot):**
- `"desativa digital twin"`
- `"desliga digital twin"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('twin_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `hiring_policy` (9 actions)

### `configure_policy` — Configurar Política de Contratação

**Descrição completa:**
> Configura regras gerais da política de contratação da empresa

**Examples (few-shot):**
- `"configura política de contratação"`
- `"define regras gerais do processo"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'setup')` |

---

### `configure_pipeline` — Configurar Pipeline

**Descrição completa:**
> Define regras de pipeline e etapas do processo seletivo

**Examples (few-shot):**
- `"configura o pipeline"`
- `"define etapas do processo seletivo"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'pipeline')` |

---

### `configure_scheduling` — Configurar Agendamento

**Descrição completa:**
> Define regras de agendamento de entrevistas

**Examples (few-shot):**
- `"configura regras de agendamento"`
- `"define políticas de entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'scheduling')` |

---

### `configure_communication` — Configurar Comunicação

**Descrição completa:**
> Define regras de comunicação com candidatos

**Examples (few-shot):**
- `"configura comunicação com candidatos"`
- `"define templates de resposta"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'communication')` |

---

### `configure_screening` — Configurar Triagem

**Descrição completa:**
> Define regras de triagem e avaliação de candidatos

**Examples (few-shot):**
- `"configura triagem"`
- `"define critérios de avaliação"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'screening')` |

---

### `configure_automation` — Configurar Automação

**Descrição completa:**
> Define nível de autonomia da LIA e regras de automação

**Examples (few-shot):**
- `"configura nível de automação"`
- `"define autonomia da LIA"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'automation')` |

---

### `validate_compliance` — Validar Compliance

**Descrição completa:**
> Valida se a política atual está em conformidade com regras de fairness e LGPD

**Examples (few-shot):**
- `"valida compliance da política"`
- `"checa se está dentro da LGPD"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'compliance')` |

---

### `get_progress` — Ver Progresso

**Descrição completa:**
> Retorna o progresso atual da configuração da política

**Examples (few-shot):**
- `"mostra progresso da configuração"`
- `"quanto já configuramos?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'progress')` |

---

### `configure_candidate_portal` — Configurar Portal do Candidato

**Descrição completa:**
> Ativa e configura o Portal do Candidato (WhatsApp + link web) para candidatos consultarem seu status no processo seletivo

**Examples (few-shot):**
- `"configura portal do candidato"`
- `"ativa link pra candidato consultar status"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('policy', 'candidate_portal', 'communication')` |

---

### Domínio: `interview_scheduling` (20 actions)

### `schedule_interview` — Agendar Entrevista

**Descrição completa:**
> Agenda entrevista entre candidato e entrevistador via calendário com criação de evento, envio de convites e confirmações. Requer confirmação. Aciona quando recruiter ou candidato confirma horário de entrevista.

**Examples (few-shot):**
- `"agenda entrevista com o João na quinta"`
- `"marca entrevista técnica"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('candidate_name', 'candidate_email', 'interviewer_email', 'start_time')` |
| `optional_params` | `('job_title', 'interview_type', 'duration_minutes', 'location', 'notes')` |
| `tags` | `[]` |

---

### `reschedule_interview` — Reagendar Entrevista

**Descrição completa:**
> Reagenda entrevista existente para novo horário atualizando eventos no calendário e notificando participantes. Requer confirmação. Aciona quando candidato ou entrevistador solicita novo horário.

**Examples (few-shot):**
- `"remarca a entrevista para amanhã"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('interview_id', 'new_start_time')` |
| `optional_params` | `('reason', 'notify_participants')` |
| `tags` | `[]` |

---

### `cancel_interview` — Cancelar Entrevista

**Descrição completa:**
> Cancela entrevista agendada e notifica participantes com motivo da cancelamento. Requer confirmação. Aciona quando entrevista não será realizada por desistência ou indisponibilidade.

**Examples (few-shot):**
- `"cancela a entrevista de hoje"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('interview_id',)` |
| `optional_params` | `('cancellation_reason', 'notify_participants')` |
| `tags` | `[]` |

---

### `check_availability` — Verificar Disponibilidade

**Descrição completa:**
> Verifica disponibilidade do entrevistador no calendário para data e duração específicas. Aciona antes de propor horário ao candidato para garantir slot disponível.

**Examples (few-shot):**
- `"checa disponibilidade do candidato"`
- `"quando o Lucas está livre?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interviewer_email', 'date')` |
| `optional_params` | `('duration_minutes', 'timezone')` |
| `tags` | `[]` |

---

### `generate_self_scheduling_link` — Gerar Link de Auto-agendamento

**Descrição completa:**
> Gera link para candidato escolher horário disponível do entrevistador de forma autônoma sem intervenção do recruiter. Aciona para otimizar agendamento e melhorar experiência do candidato.

**Examples (few-shot):**
- `"gera email de follow-up"`
- `"cria mensagem pós-entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_name', 'candidate_email', 'interviewer_emails')` |
| `optional_params` | `('job_title', 'interview_type', 'duration_minutes', 'expires_in_days')` |
| `tags` | `[]` |

---

### `find_common_slots` — Encontrar Horários Comuns

**Descrição completa:**
> Encontra horários comuns disponíveis para múltiplos participantes (painéis com vários entrevistadores). Aciona para agendamento de entrevistas em painel com 2+ entrevistadores.

**Examples (few-shot):**
- `"encontra horário comum entre entrevistadores"`
- `"quando todos estão livres?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('participant_emails',)` |
| `optional_params` | `('duration_minutes', 'preferred_days', 'date_range')` |
| `tags` | `[]` |

---

### `send_reminder` — Enviar Lembrete

**Descrição completa:**
> Envia lembrete de entrevista para candidato e entrevistador com detalhes e instruções de acesso. Requer confirmação. Aciona automaticamente 24h antes ou quando recruiter solicita lembrete manual.

**Examples (few-shot):**
- `"envia lembrete da entrevista"`
- `"lembra participantes da reunião"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('interview_id',)` |
| `optional_params` | `('channels', 'custom_message')` |
| `tags` | `[]` |

---

### `schedule_reminders` — Agendar Lembretes

**Descrição completa:**
> Configura lembretes automáticos recorrentes para entrevistas futuras com canais e timing definidos. Aciona na criação do agendamento para garantir lembretes sem intervenção manual.

**Examples (few-shot):**
- `"agenda lembretes da entrevista"`
- `"cria lembretes automáticos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id',)` |
| `optional_params` | `('hours_before', 'channels', 'recipient_types')` |
| `tags` | `[]` |

---

### `list_today_interviews` — Listar Entrevistas de Hoje

**Descrição completa:**
> Lista todas as entrevistas agendadas para hoje com horários, participantes e status de confirmação. Aciona no briefing diário do recruiter ou quando pede 'qual minha agenda de hoje?'.

**Examples (few-shot):**
- `"lista entrevista"`
- `"mostra entrevista ativas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('interviewer_email', 'status_filter')` |
| `tags` | `[]` |

---

### `resolve_conflict` — Resolver Conflito de Agenda

**Descrição completa:**
> Resolve conflitos de agendamento entre entrevistas sobrepostas usando estratégia de priorização configurável. Aciona quando sistema detecta conflito de agenda ou recruiter relata problema de scheduling.

**Examples (few-shot):**
- `"resolver conflito de agenda"`
- `"quero resolver conflito de agenda"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_ids',)` |
| `optional_params` | `('resolution_strategy', 'priority_rules')` |
| `tags` | `[]` |

---

### `start_wsi_interview` — Iniciar Entrevista WSI

**Descrição completa:**
> Inicia entrevista WSI completa e estruturada com candidato via chat (40-60 minutos) com perguntas baseadas em competências. Aciona quando chegou a hora da entrevista WSI no fluxo de triagem.

**Examples (few-shot):**
- `"iniciar WSI"`
- `"começar WSI"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id', 'job_vacancy_id')` |
| `optional_params` | `('competencies', 'interview_mode', 'language')` |
| `tags` | `[]` |

---

### `send_question` — Enviar Pergunta

**Descrição completa:**
> Envia pergunta de entrevista WSI para candidato durante sessão ativa, com tipo e competência alvo. Aciona durante entrevista WSI em andamento para avançar para próxima pergunta.

**Examples (few-shot):**
- `"envia pergunta"`
- `"manda pergunta"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id', 'question_text')` |
| `optional_params` | `('question_type', 'competency_target', 'time_limit')` |
| `tags` | `[]` |

---

### `analyze_response` — Analisar Resposta

**Descrição completa:**
> Analisa resposta do candidato usando metodologia WSI com IA para extrair evidências de competências e calcular score parcial. Aciona após cada resposta do candidato durante entrevista estruturada.

**Examples (few-shot):**
- `"analisa score"`
- `"avalia score"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id', 'response_text')` |
| `optional_params` | `('question_context', 'competency_target', 'expected_level')` |
| `tags` | `[]` |

---

### `transcribe_audio` — Transcrever Áudio

**Descrição completa:**
> Transcreve áudio de entrevista por voz para texto para análise e registro. Aciona em entrevistas por voz ou quando recruiter envia gravação de entrevista presencial.

**Examples (few-shot):**
- `"transcrever áudio"`
- `"quero transcrever áudio"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('audio_url',)` |
| `optional_params` | `('language', 'model', 'interview_id')` |
| `tags` | `[]` |

---

### `analyze_voice` — Analisar Voz

**Descrição completa:**
> Analisa tom de voz, confiança e consistência emocional do candidato durante entrevista oral. Aciona em entrevistas por voz para adicionar dimensão não-verbal à avaliação.

**Examples (few-shot):**
- `"analisa voz da entrevista gravada"`
- `"avalia tom de voz do candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('audio_url',)` |
| `optional_params` | `('interview_id', 'candidate_id', 'analysis_type')` |
| `tags` | `[]` |

---

### `detect_evasive` — Detectar Resposta Evasiva

**Descrição completa:**
> Detecta padrões de respostas evasivas ou inconsistentes durante entrevista para alertar o recruiter. Aciona automaticamente durante análise de respostas ou quando recruiter suspeita de inconsistência.

**Examples (few-shot):**
- `"detecta respostas evasivas"`
- `"o candidato está sendo direto?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id', 'response_text')` |
| `optional_params` | `('question_context', 'threshold')` |
| `tags` | `[]` |

---

### `generate_followup` — Gerar Pergunta de Follow-up

**Descrição completa:**
> Gera pergunta de follow-up contextualizada baseada na resposta anterior do candidato para aprofundar evidências. Aciona quando resposta foi superficial ou vaga e recruiter precisa de mais evidências.

**Examples (few-shot):**
- `"gera email de follow-up"`
- `"cria mensagem pós-entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id', 'previous_response')` |
| `optional_params` | `('competency_target', 'depth_level', 'question_type')` |
| `tags` | `[]` |

---

### `complete_interview` — Finalizar Entrevista

**Descrição completa:**
> Finaliza entrevista WSI gerando resumo completo com scores por competência, análise e recomendação final. Aciona quando todas as perguntas foram feitas e recruiter encerra a sessão.

**Examples (few-shot):**
- `"finalizar entrevista"`
- `"quero finalizar entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('interview_id',)` |
| `optional_params` | `('final_notes', 'recommendation', 'generate_report')` |
| `tags` | `[]` |

---

### `interview_qa` — Q&A sobre Entrevista

**Descrição completa:**
> Responde dúvidas do recruiter sobre processo de entrevista, metodologia WSI ou candidato específico. Aciona quando recruiter tem perguntas contextuais durante ou após entrevista.

**Examples (few-shot):**
- `"q&a sobre entrevista"`
- `"quero q&a sobre entrevista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('question',)` |
| `optional_params` | `('interview_id', 'candidate_id', 'context')` |
| `tags` | `[]` |

---

### `start_quick_screening` — Iniciar Triagem Rápida

**Descrição completa:**
> Inicia triagem rápida estruturada com candidato (10-15 minutos) para qualificação inicial antes de entrevista completa. Aciona como alternativa à entrevista WSI completa para pré-seleção eficiente.

**Examples (few-shot):**
- `"inicia triagem rápida"`
- `"começa pré-triagem automática"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id',)` |
| `optional_params` | `('job_vacancy_id', 'screening_type', 'questions')` |
| `tags` | `[]` |

---

### Domínio: `job_creation` (11 actions)

### `start_wizard` — Iniciar criacao de vaga

**Descrição completa:**
> Inicia o wizard de criacao de vaga. Recebe descricao inicial (titulo, senioridade, departamento) e guia o recrutador pelo fluxo WSI completo

**Examples (few-shot):**
- `"Criar vaga de PM senior"`
- `"Quero abrir uma vaga"`
- `"Nova vaga de desenvolvedor backend"`
- `"Preciso contratar um designer"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `approve_jd` — Aprovar JD enriquecido

**Descrição completa:**
> Aprova ou rejeita o JD enriquecido pela IA (HITL ponto 1 - F1). Recrutador pode editar antes de aprovar

**Examples (few-shot):**
- `"Aprovar JD"`
- `"Fica bom"`
- `"Aceito"`
- `"Preciso editar o JD"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `set_salary` — Definir salario e beneficios

**Descrição completa:**
> Define faixa salarial e beneficios da vaga

**Examples (few-shot):**
- `"Salario entre 15k e 20k"`
- `"Beneficios: VR, VT, plano de saude"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `set_screening_mode` — Escolher modo de triagem

**Descrição completa:**
> Escolhe entre modo compacto (7 perguntas) ou completo (12 perguntas) para a triagem WSI

**Examples (few-shot):**
- `"Modo compacto"`
- `"Quero triagem completa"`
- `"7 perguntas"`
- `"12 perguntas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `approve_questions` — Aprovar perguntas de triagem

**Descrição completa:**
> Aprova, edita ou regenera as perguntas de triagem WSI (HITL ponto 2 - F6). Recrutador revisa cada pergunta

**Examples (few-shot):**
- `"Aprovar perguntas"`
- `"Regenerar pergunta 3"`
- `"Editar pergunta 1"`
- `"Remover pergunta sobre..."`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `set_eligibility` — Configurar elegibilidade

**Descrição completa:**
> Adiciona ou remove perguntas de elegibilidade sim/nao (ex: tem CNH? aceita viagem?). Requisitos eliminatorios antes da triagem WSI

**Examples (few-shot):**
- `"Adicionar pergunta: tem CNH?"`
- `"Disponibilidade imediata e obrigatoria"`
- `"Aceita viagem?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `configure_publish` — Configurar publicacao

**Descrição completa:**
> Define plataformas (LinkedIn/Indeed/Website), modo de sourcing (local/global/hibrido), canais de contato e opcao de auto-screening

**Examples (few-shot):**
- `"Publicar no LinkedIn e Indeed"`
- `"Sourcing global"`
- `"Contato por WhatsApp e email"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `publish_job` — Publicar vaga

**Descrição completa:**
> Publica a vaga nas plataformas configuradas e inicia screening automatico. Requer que todas as etapas anteriores estejam completas

**Examples (few-shot):**
- `"Publicar"`
- `"Manda ver"`
- `"Publica essa vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `calibrate` — Calibrar perfis

**Descrição completa:**
> Apresenta candidatos para calibracao (aprovar/rejeitar com razoes). Minimo 3 perfis calibrados antes do handoff

**Examples (few-shot):**
- `"Aprovar candidato"`
- `"Rejeitar: falta experiencia em..."`
- `"Proximo candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `wizard_status` — Status do wizard

**Descrição completa:**
> Mostra o progresso atual do wizard de criacao de vaga

**Examples (few-shot):**
- `"Em que etapa estamos?"`
- `"Status do wizard"`
- `"O que falta?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `help` — Ajuda

**Descrição completa:**
> Explica o fluxo de criacao de vaga e a metodologia WSI

**Examples (few-shot):**
- `"Como funciona?"`
- `"O que e o WSI?"`
- `"Ajuda"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `job_management` (30 actions)

### `create_job` — Criar vaga

**Descrição completa:**
> Cria nova vaga de emprego via conversa natural extraindo requisitos, competências e configurações da descrição do cargo. Aciona quando recruiter inicia processo de nova posição ou cliente solicita abertura de vaga.

**Examples (few-shot):**
- `"quero abrir uma vaga de engenheiro de software"`
- `"preciso contratar um analista de dados sênior"`
- `"cria uma posição de gerente de projetos para São Paulo"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `guided_wizard` — Wizard guiado

**Descrição completa:**
> Inicia fluxo conversacional guiado passo a passo para criação de vaga com validação em cada etapa. Aciona quando recruiter prefere processo estruturado ou é iniciante na plataforma.

**Examples (few-shot):**
- `"quero criar vaga passo a passo"`
- `"me guia na criação de vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `extract_requirements` — Extrair requisitos

**Descrição completa:**
> Extrai requisitos obrigatórios e desejáveis de uma job description usando IA para estruturar critérios de triagem. Aciona ao importar JD de documento externo ou ao colar descrição de cargo no chat.

**Examples (few-shot):**
- `"extrai os requisitos deste JD"`
- `"tira os skills obrigatórios dessa descrição"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `generate_rubrics` — Gerar rubricas

**Descrição completa:**
> Gera requisitos estruturados para o sistema de Rubricas WSI baseado no cargo e competências identificadas. Aciona após criação da vaga para configurar critérios de avaliação objetivos.

**Examples (few-shot):**
- `"gera as rubricas WSI desta vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `update_job` — Atualizar vaga

**Descrição completa:**
> Atualiza campos da vaga existente: requisitos, salário, localização, status ou qualquer configuração. Aciona quando recruiter pede para modificar informações da vaga ativa.

**Examples (few-shot):**
- `"atualiza o salário da vaga 123"`
- `"muda o local da vaga para remoto"`
- `"edita os requisitos desta vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `health_check` — Health check

**Descrição completa:**
> Verifica indicadores de saúde da vaga: volume, velocidade do pipeline, SLA, taxa de triagem e alertas. Aciona na abertura do dashboard da vaga ou quando recruiter pede status geral.

**Examples (few-shot):**
- `"como está a saúde da vaga?"`
- `"tem algum alerta nessa posição?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `suggest_strategy` — Sugerir estratégia

**Descrição completa:**
> Sugere mudanças de estratégia de recrutamento baseadas nos dados da vaga: sourcing, critérios, canais. Aciona quando vaga está parada, sem candidatos qualificados ou com SLA em risco.

**Examples (few-shot):**
- `"minha vaga tá parada, o que faço?"`
- `"sugere mudança de estratégia de sourcing"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `duplicate_job` — Duplicar vaga

**Descrição completa:**
> Duplica vaga existente com todos os dados (requisitos, rubricas, configurações) para reaproveitamento. Aciona quando nova posição é similar a vaga já criada.

**Examples (few-shot):**
- `"duplica esta vaga pra eu abrir outra parecida"`
- `"cria uma cópia da vaga 55"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `create_from_template` — Criar de template

**Descrição completa:**
> Cria nova vaga usando outra vaga como template, herdando critérios e configurações. Aciona para vagas recorrentes da empresa com requisitos padronizados.

**Examples (few-shot):**
- `"cria vaga usando o template X"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `clone_job` — Clonar vaga

**Descrição completa:**
> Clona vaga existente criando cópia idêntica com novo ID. Aciona para abrir posição duplicada mantendo todos os parâmetros originais.

**Examples (few-shot):**
- `"clona a vaga 12"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `close_job` — Fechar vaga

**Descrição completa:**
> Fecha e arquiva vaga com motivo (preenchida, cancelada, orçamento) e notifica candidatos ativos. Requer atenção — ação significativa. Aciona ao preencher posição ou encerrar processo.

**Examples (few-shot):**
- `"fecha a vaga, já preenchemos"`
- `"pode encerrar o processo desta posição"`
- `"arquiva a vaga 42 como cancelada"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `pause_job` — Pausar vaga

**Descrição completa:**
> Pausa vaga temporariamente interrompendo triagem automática e sourcing sem fechar o processo. Aciona quando há mudança de contexto temporária mas vaga será retomada.

**Examples (few-shot):**
- `"pausa a vaga temporariamente"`
- `"interrompe sourcing desta posição por enquanto"`
- `"suspende a vaga por 2 semanas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_benefits` — Obter benefícios

**Descrição completa:**
> Obtém lista de benefícios da empresa para incluir na vaga automaticamente. Aciona ao criar vaga quando recruiter não quer digitar benefícios manualmente.

**Examples (few-shot):**
- `"mostra benefícios da empresa pra incluir na vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `suggest_jd_improvements` — Melhorar JD

**Descrição completa:**
> Sugere melhorias para job description usando IA: linguagem inclusiva, clareza, SEO para candidatos. Aciona quando recruiter quer otimizar a JD antes de publicar. Distinto de enrich_jd (que aplica melhorias automaticamente) e de generate_jd (que cria do zero).

**Examples (few-shot):**
- `"como posso melhorar esta JD?"`
- `"sugere mudanças pra tornar a JD mais inclusiva"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `detect_criteria` — Detectar critérios

**Descrição completa:**
> Detecta critérios de triagem automaticamente a partir da job description usando NLP. Aciona ao importar JD externa para configurar triagem sem inserção manual.

**Examples (few-shot):**
- `"identifica os critérios de triagem nesta JD"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `generate_wsi_questions` — Gerar perguntas WSI

**Descrição completa:**
> Gera conjunto de perguntas WSI customizadas para a vaga baseadas nos requisitos e competências. Aciona na configuração de nova vaga antes do início das triagens. Distinto do fluxo em cv_screening (que gera perguntas dinamicamente durante a triagem).

**Examples (few-shot):**
- `"gera as perguntas WSI pra essa vaga"`
- `"cria os questionários de triagem"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `advance_wizard_step` — Avançar etapa

**Descrição completa:**
> Avança para próxima etapa do wizard de criação de vaga após validação da etapa atual. Aciona durante fluxo guiado quando recruiter confirma dados da etapa presente.

**Examples (few-shot):**
- `"próxima etapa do wizard"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_wizard_step_data` — Dados da etapa

**Descrição completa:**
> Obtém dados e contexto da etapa atual do wizard para exibição e validação. Aciona durante wizard para carregar formulário e validações da etapa presente.

**Examples (few-shot):**
- `"mostra os dados da etapa atual"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `enrich_jd` — Enriquecer JD

**Descrição completa:**
> Enriquece job description com informações do mercado, competências complementares e linguagem otimizada. Aciona para melhorar JDs simples ou importadas antes de publicar. Distinto de generate_jd (que cria do zero) e de suggest_jd_improvements (que só sugere mudanças, sem aplicar).

**Examples (few-shot):**
- `"melhora esta JD aqui"`
- `"enriquece a descrição com informações de mercado"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `import_jd` — Importar JD

**Descrição completa:**
> Importa job description de documento (PDF, Word) ou URL para a plataforma estruturando automaticamente. Aciona quando recruiter tem JD em arquivo externo.

**Examples (few-shot):**
- `"importa essa JD em PDF"`
- `"carrega este arquivo de descrição de vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `generate_jd` — Gerar JD

**Descrição completa:**
> Gera job description completa e otimizada com IA a partir do título e requisitos básicos fornecidos. Aciona quando recruiter não tem JD pronto e quer criar do zero via IA. Distinto de enrich_jd (que melhora JD já existente) e de suggest_jd_improvements (que apenas sugere edições, sem sobrescrever).

**Examples (few-shot):**
- `"cria uma job description pra vaga de dev Python"`
- `"gera descrição da vaga do zero"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `job_analytics` — Analytics de vagas

**Descrição completa:**
> Obtém métricas e analytics da vaga: candidatos, conversão por etapa, tempo médio e benchmark de mercado. Aciona no dashboard da vaga ou quando recruiter pede análise de desempenho.

**Examples (few-shot):**
- `"quantos candidatos tem a vaga 10?"`
- `"mostra métricas desta vaga"`
- `"como está o desempenho do processo?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `qualify_job` — Qualificar vaga

**Descrição completa:**
> Qualifica a vaga verificando completude dos dados obrigatórios antes de publicação. Aciona antes de publicar vaga para garantir que todos os campos necessários estão preenchidos.

**Examples (few-shot):**
- `"checa se a vaga está pronta para publicar"`
- `"valida os campos obrigatórios"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_jobs` — Listar vagas

**Descrição completa:**
> Lista vagas abertas e ativas do tenant com status, contagem de candidatos e dias abertos. Aciona quando recruiter quer visão geral das vagas ou precisa selecionar vaga para ação.

**Examples (few-shot):**
- `"quais vagas eu tenho abertas?"`
- `"lista minhas vagas ativas"`
- `"mostra as vagas em aberto"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `publish_job` — Publicar vaga

**Descrição completa:**
> Publica vaga em job boards (LinkedIn, Indeed, site da empresa) ativando sourcing automático. Aciona após qualificação quando vaga está pronta para receber candidaturas.

**Examples (few-shot):**
- `"publica essa vaga no LinkedIn"`
- `"divulga a posição nos job boards"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `job_status_webhook` — Webhook de status

**Descrição completa:**
> Gerencia webhooks de status da vaga para integrações externas receberem atualizações em tempo real. Aciona na configuração de integrações que precisam ser notificadas de mudanças de status.

**Examples (few-shot):**
- `"configura webhook de status da vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `search_templates` — Buscar templates

**Descrição completa:**
> Busca templates de vaga por cargo, setor ou palavras-chave para reutilização. Aciona quando recruiter quer criar vaga baseada em template existente na biblioteca.

**Examples (few-shot):**
- `"busca templates de vaga de analista"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `apply_template` — Aplicar template

**Descrição completa:**
> Aplica template de vaga selecionado a nova posição, preenchendo requisitos e configurações automaticamente. Aciona após escolha de template para acelerar criação de vaga.

**Examples (few-shot):**
- `"usa este template pra criar a vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `analyze_jd` — Analisar JD

**Descrição completa:**
> Avalia qualidade da job description: clareza, inclusividade, completude e SEO para candidatos. Aciona antes de publicar para garantir JD de alta qualidade.

**Examples (few-shot):**
- `"avalia a qualidade desta JD"`
- `"analisa a descrição antes de publicar"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `suggest_compensation` — Sugerir compensação

**Descrição completa:**
> Sugere faixa de compensação competitiva baseada em benchmarks de mercado para o cargo e localização. Aciona quando recruiter precisa definir salário ou está negociando com candidato.

**Examples (few-shot):**
- `"qual salário eu devo pagar pra esse cargo?"`
- `"sugere faixa salarial competitiva"`
- `"quanto está o mercado pagando pra analista sênior em SP?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `pipeline` (5 actions)

### `move_candidate` — Mover Candidato

**Descrição completa:**
> Move um candidato para uma nova etapa do pipeline

**Examples (few-shot):**
- `"move o candidato João pra entrevista"`
- `"avança este candidato pra próxima etapa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('vacancy_candidate_id', 'to_stage')` |
| `optional_params` | `('from_stage', 'sub_status', 'prompt', 'channel')` |
| `tags` | `('pipeline', 'transition')` |

---

### `interpret_context` — Interpretar Contexto

**Descrição completa:**
> Interpreta o contexto de uma transição usando IA

**Examples (few-shot):**
- `"interpreta o contexto desta transição"`
- `"por que o candidato foi rejeitado?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('candidate_id', 'from_stage', 'to_stage', 'action_behavior')` |
| `optional_params` | `('candidate_name', 'job_title', 'prompt')` |
| `tags` | `('pipeline', 'ai', 'context')` |

---

### `predict_sub_status` — Predizer Sub-Status

**Descrição completa:**
> Prediz o sub-status mais adequado para um candidato

**Examples (few-shot):**
- `"prediz o melhor sub-status"`
- `"qual sub-status faz mais sentido aqui?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('vacancy_candidate_id', 'from_stage', 'to_stage')` |
| `optional_params` | `[]` |
| `tags` | `('pipeline', 'prediction')` |

---

### `suggest_next_action` — Sugerir Próxima Ação

**Descrição completa:**
> Sugere a próxima ação para um candidato no pipeline

**Examples (few-shot):**
- `"sugere próxima ação pra este candidato"`
- `"o que devo fazer agora?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('vacancy_candidate_id', 'current_stage')` |
| `optional_params` | `[]` |
| `tags` | `('pipeline', 'suggestion')` |

---

### `list_pipeline_stages` — Listar Etapas

**Descrição completa:**
> Lista todas as etapas do pipeline de recrutamento

**Examples (few-shot):**
- `"lista etapas do pipeline"`
- `"quais são as etapas do processo?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('company_id',)` |
| `optional_params` | `[]` |
| `tags` | `('pipeline', 'stages')` |

---

### Domínio: `recruiter_assistant` (24 actions)

### `daily_briefing` — Briefing Diário

**Descrição completa:**
> Gera briefing diário personalizado para o recrutador com prioridades do dia, candidatos aguardando ação, SLAs em risco e agenda de entrevistas. Aciona automaticamente pela manhã ou quando recruiter pede 'o que tenho para hoje?'.

**Examples (few-shot):**
- `"briefing diário"`
- `"quero briefing diário"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('briefing', 'daily', 'delegate_to_agent')` |

---

### `end_of_day_summary` — Resumo do Dia

**Descrição completa:**
> Gera resumo de encerramento do dia com ações realizadas, pendências e destaques. Aciona no fim do expediente para registro e planejamento do dia seguinte.

**Examples (few-shot):**
- `"resumo do dia"`
- `"quero resumo do dia"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('summary', 'daily', 'delegate_to_agent')` |

---

### `quick_question` — Pergunta Rápida

**Descrição completa:**
> Responde pergunta rápida do recrutador sobre candidato, vaga ou processo sem roteamento para domínio especializado. Aciona para perguntas simples de contexto ou verificações rápidas.

**Examples (few-shot):**
- `"pergunta rápida"`
- `"quero pergunta rápida"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('question', 'quick', 'delegate_to_agent')` |

---

### `plan_day` — Planejar Dia

**Descrição completa:**
> Ajuda o recrutador a planejar e priorizar as atividades do dia baseado em pipeline, SLAs e metas. Aciona quando recruiter pede ajuda para organizar agenda ou não sabe por onde começar.

**Examples (few-shot):**
- `"planejar dia"`
- `"quero planejar dia"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('planning', 'productivity', 'delegate_to_agent')` |

---

### `pipeline_health` — Saúde do Pipeline

**Descrição completa:**
> Analisa a saúde geral do pipeline de recrutamento: vagas com risco, candidatos parados, SLAs vencidos e volume total. Aciona quando recruiter quer visão consolidada de todos os processos.

**Examples (few-shot):**
- `"saúde do pipeline"`
- `"quero saúde do pipeline"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('pipeline', 'health', 'analysis')` |

---

### `stale_candidates` — Candidatos Parados

**Descrição completa:**
> Identifica e lista candidatos que estão parados em etapas sem movimento há mais de N dias. Aciona para limpeza proativa de pipeline ou quando recruiter quer reativar candidatos esquecidos.

**Examples (few-shot):**
- `"candidatos parados"`
- `"quero candidatos parados"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('candidates', 'stale', 'pipeline')` |

---

### `move_candidate` — Mover Candidato

**Descrição completa:**
> Move candidato para etapa específica do pipeline com confirmação e registro. Requer confirmação. Aciona quando recruiter quer mover candidato sem abrir tela de candidatura.

**Examples (few-shot):**
- `"move o candidato João para entrevista"`
- `"avança este candidato pra próxima etapa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('candidate', 'move', 'stage')` |

---

### `suggest_action` — Sugerir Ação

**Descrição completa:**
> Sugere a próxima melhor ação para um candidato ou vaga usando IA baseada no contexto atual. Aciona quando recruiter está indeciso ou quer recomendação do assistente.

**Examples (few-shot):**
- `"sugere próxima ação"`
- `"o que devo fazer agora?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('suggestion', 'action', 'ai', 'delegate_to_agent')` |

---

### `search_context` — Buscar Contexto

**Descrição completa:**
> Busca no histórico de conversas e memória persistente por contexto relevante sobre candidato, vaga ou situação. Aciona quando recruiter referencia algo discutido anteriormente.

**Examples (few-shot):**
- `"busca contexto sobre esta vaga"`
- `"traz histórico relacionado"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('search', 'context', 'history')` |

---

### `save_memory` — Salvar Memória

**Descrição completa:**
> Salva informação importante na memória persistente para referência futura (preferências de candidato, acordos com cliente, etc.). Aciona quando recruiter diz 'anota isso' ou quer preservar contexto.

**Examples (few-shot):**
- `"salvar memória"`
- `"quero salvar memória"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('memory', 'save', 'persistent')` |

---

### `recall_memory` — Recuperar Memória

**Descrição completa:**
> Recupera informação da memória persistente sobre candidato, vaga ou decisão anterior. Aciona quando recruiter pergunta 'o que você sabe sobre X?' ou referencia informação anterior.

**Examples (few-shot):**
- `"recuperar memória"`
- `"quero recuperar memória"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('memory', 'recall', 'search')` |

---

### `conversation_summary` — Resumo da Conversa

**Descrição completa:**
> Gera resumo estruturado da conversa atual com pontos-chave, decisões e próximas ações. Aciona quando recruiter pede resumo ou ao fim de conversa longa.

**Examples (few-shot):**
- `"resumo da conversa"`
- `"quero resumo da conversa"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('conversation', 'summary')` |

---

### `kanban_analysis` — Análise do Kanban

**Descrição completa:**
> Analisa o quadro Kanban de recrutamento com IA identificando padrões, gargalos e oportunidades de otimização. Aciona quando recruiter quer análise estratégica do fluxo de candidatos.

**Examples (few-shot):**
- `"análise do kanban"`
- `"quero análise do kanban"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('kanban', 'analysis', 'ai')` |

---

### `calibrate_profile` — Calibrar Perfil

**Descrição completa:**
> Calibra o perfil ideal de candidato para a vaga com base no feedback do recruiter sobre candidatos vistos. Aciona quando triagem está retornando candidatos fora do perfil desejado.

**Examples (few-shot):**
- `"calibra perfil do candidato"`
- `"ajusta fit com a vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('calibration', 'profile', 'delegate_to_agent')` |

---

### `send_notification` — Enviar Notificação

**Descrição completa:**
> Envia notificação proativa para o recrutador sobre evento crítico (candidato que vai desistir, SLA em risco). Aciona automaticamente pela IA ao detectar situação que requer atenção imediata.

**Examples (few-shot):**
- `"envia notificação"`
- `"avisa sobre atualização"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('notification', 'proactive')` |

---

### `track_goals` — Acompanhar Metas

**Descrição completa:**
> Acompanha o progresso das metas de recrutamento do período (vagas fechadas, tempo médio, candidatos contratados). Aciona quando recruiter quer ver performance ou relatório para liderança.

**Examples (few-shot):**
- `"acompanhar metas"`
- `"quero acompanhar metas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('goals', 'tracking', 'metrics')` |

---

### `generate_insights` — Gerar Insights

**Descrição completa:**
> Gera insights proativos sobre padrões de sourcing, efetividade de canais e oportunidades de melhoria. Aciona semanalmente ou quando recruiter pede análise de desempenho.

**Examples (few-shot):**
- `"gera insights deste processo"`
- `"o que aprendemos com este processo?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('insights', 'proactive', 'delegate_to_agent')` |

---

### `compare_candidates` — Comparar Candidatos

**Descrição completa:**
> Faz comparação rápida entre candidatos selecionados com análise de pontos fortes, gaps e recomendação. Aciona quando recruiter tem dúvida entre dois ou mais finalistas.

**Examples (few-shot):**
- `"compara estes dois candidatos"`
- `"qual é melhor entre esses perfis?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('candidates', 'comparison', 'delegate_to_agent')` |

---

### `stage_recommendation` — Recomendar Etapa

**Descrição completa:**
> Recomenda próxima etapa ideal para candidato baseado em score, perfil e histórico do processo. Aciona quando recruiter pede orientação sobre como avançar com candidato específico.

**Examples (few-shot):**
- `"recomenda próxima etapa"`
- `"qual próximo passo pra esse candidato?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('stage', 'recommendation', 'delegate_to_agent')` |

---

### `proactive_alerts` — Alertas Proativos

**Descrição completa:**
> Lista e prioriza alertas proativos do pipeline: SLA vencidos, candidatos parados, vagas sem movimento, risco de perda. Aciona no início do dia ou quando recruiter pede 'o que precisa de atenção?'.

**Examples (few-shot):**
- `"mostra alertas proativos"`
- `"tem alerta importante?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('alerts', 'proactive', 'monitoring')` |

---

### `autonomous_actions` — Ações Autônomas

**Descrição completa:**
> Lista e gerencia ações autônomas executadas pela LIA (emails enviados, candidatos movidos) para revisão e auditoria. Aciona quando recruiter quer saber o que a IA fez ou revisar ações automáticas.

**Examples (few-shot):**
- `"executa ações autônomas"`
- `"roda o agente no modo automático"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('autonomous', 'actions', 'automation')` |

---

### `stakeholder_notify` — Notificar Stakeholders

**Descrição completa:**
> Detecta decisões pendentes de hiring managers e dispara notificações com escalação automática. Aciona quando candidato está aguardando decisão do gestor há mais do prazo acordado.

**Examples (few-shot):**
- `"notifica stakeholders"`
- `"avisa o gestor contratante"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('stakeholder', 'notification', 'escalation', 'hiring_manager')` |

---

### `learning_insights` — Insights de Aprendizado

**Descrição completa:**
> Apresenta o que a LIA aprendeu com contratações anteriores: padrões de sucesso, preditores de performance e calibrações. Aciona quando recruiter quer entender o aprendizado do sistema.

**Examples (few-shot):**
- `"mostra insights de aprendizado"`
- `"o que a LIA aprendeu até agora?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('learning', 'insights', 'outcomes', 'feedback')` |

---

### `help_command` — Ajuda

**Descrição completa:**
> Mostra lista de comandos, funcionalidades disponíveis e exemplos de uso para orientar o recruiter. Aciona quando recruiter digita 'ajuda', 'help' ou está perdido na plataforma.

**Examples (few-shot):**
- `"me ajuda"`
- `"o que você sabe fazer?"`
- `"comandos disponíveis"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `('help', 'commands')` |

---

### Domínio: `recruitment_campaign` (4 actions)

### `create_campaign` — Criar Campanha

**Descrição completa:**
> Cria campanha de recrutamento estruturada para vaga ou pool de talentos com etapas, automações e nível de autonomia configurados. Aciona quando recruiter inicia processo estruturado de atração de candidatos.

**Examples (few-shot):**
- `"cria campanha de recrutamento"`
- `"monta campanha pra abrir vagas de dev"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('name',)` |
| `optional_params` | `('job_id', 'talent_pool_id', 'automation_level')` |
| `tags` | `[]` |

---

### `get_campaign_progress` — Progresso da Campanha

**Descrição completa:**
> Obtém estágio atual da campanha com métricas de progresso, próximos passos e alertas de desvio. Aciona para acompanhar andamento da campanha ou quando recruiter pede status.

**Examples (few-shot):**
- `"como está a campanha?"`
- `"mostra progresso da campanha"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('campaign_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `advance_campaign` — Avançar Campanha

**Descrição completa:**
> Avança campanha para próximo estágio após validação dos critérios de entrada. Requer confirmação. Aciona quando etapa atual está concluída e recruiter confirma avanço para fase seguinte.

**Examples (few-shot):**
- `"avança campanha para próxima fase"`
- `"passa pra próxima etapa da campanha"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('campaign_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `list_campaigns` — Listar Campanhas

**Descrição completa:**
> Lista campanhas de recrutamento ativas e recentes com status, vagas vinculadas e métricas resumidas. Aciona quando recruiter quer gerenciar campanhas em andamento.

**Examples (few-shot):**
- `"lista campanhas ativas"`
- `"quais campanhas estão rodando?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('job_id', 'status')` |
| `tags` | `[]` |

---

### Domínio: `sourcing` (36 actions)

### `search_candidates` — Buscar candidatos

**Descrição completa:**
> Busca candidatos no banco de talentos com filtros de skills, localização, seniority, disponibilidade e score. Aciona quando recruiter pede busca de candidatos para uma vaga específica.

**Examples (few-shot):**
- `"busca candidatos para a vaga de engenheiro"`
- `"quais candidatos temos para essa posição?"`
- `"encontra desenvolvedores Python disponíveis"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `global_search` — Busca global

**Descrição completa:**
> Executa busca em todas as fontes disponíveis (banco interno, Pearch AI, LinkedIn, job boards) com estratégia unificada. Aciona quando busca simples não encontrou candidatos suficientes.

**Examples (few-shot):**
- `"busca geral por candidatos"`
- `"procura em todos os canais"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `semantic_search` — Busca semântica

**Descrição completa:**
> Busca candidatos por similaridade semântica usando embeddings vetoriais, capturando candidatos com perfil similar mesmo sem palavras-chave exatas. Aciona para vagas com requisitos difíceis de expressar em palavras.

**Examples (few-shot):**
- `"busca candidatos por competências similares"`
- `"encontra perfis parecidos com esse"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `generate_boolean` — Gerar boolean

**Descrição completa:**
> Gera query booleana otimizada para busca em LinkedIn, Indeed e outros job boards baseada nos requisitos da vaga. Aciona quando recruiter quer fazer busca manual ou exportar para ferramentas externas.

**Examples (few-shot):**
- `"gera string boolean pra busca no LinkedIn"`
- `"cria query booleana pra esse perfil"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `parse_cv` — Analisar CV

**Descrição completa:**
> Extrai dados estruturados de currículo: experiências, competências, formação e contatos para enriquecer perfil no sistema. Aciona ao receber currículo em formato PDF ou Word.

**Examples (few-shot):**
- `"analisa esse currículo que anexei"`
- `"extrai os dados deste CV"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `add_candidate` — Adicionar candidato

**Descrição completa:**
> Cadastra novo candidato no banco de talentos com dados básicos de perfil e origem. Aciona quando recruiter quer adicionar candidato indicado, importado ou captado manualmente.

**Examples (few-shot):**
- `"adiciona novo candidato manualmente"`
- `"cadastra a Paula no sistema"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `suggest_candidates` — Sugerir candidatos

**Descrição completa:**
> Sugere candidatos do banco de talentos compatíveis com os requisitos da vaga baseado em matching semântico. Aciona quando recruiter abre nova vaga para ver candidatos já disponíveis internamente. Distinto de auto_source (que age automaticamente) e de talent_pool_search (que busca só no pool interno sem sourcing externo).

**Examples (few-shot):**
- `"sugere candidatos pra esta vaga"`
- `"me indica bons fits"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `match_candidates` — Match de candidatos

**Descrição completa:**
> Calcula índice de compatibilidade entre candidato e vaga analisando skills, experiência e fit cultural. Aciona para priorização de candidatos ou validação de fit antes de avançar.

**Examples (few-shot):**
- `"faz o matching dos candidatos com a vaga"`
- `"qual candidato tem melhor fit?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `enrich_profile` — Enriquecer perfil

**Descrição completa:**
> Enriquece dados do candidato buscando informações públicas (LinkedIn, GitHub) para completar perfil. Aciona quando perfil do candidato está incompleto ou recruiter quer mais contexto.

**Examples (few-shot):**
- `"enriquece o perfil deste candidato"`
- `"busca mais dados sobre o Fernando no LinkedIn"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `auto_source` — Sourcing automático

**Descrição completa:**
> Executa pipeline automatizado de sourcing para a vaga: busca, triagem preliminar e ranqueamento sem intervenção. Aciona para vagas com volume alto ou quando recruiter quer automação completa. Distinto de suggest_candidates (que apresenta para revisão manual antes de agir) e de talent_pool_search (que busca só no pool interno).

**Examples (few-shot):**
- `"faz sourcing automático pra essa vaga"`
- `"busca candidatos ativamente"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `check_volume` — Verificar volume

**Descrição completa:**
> Avalia se o volume de candidatos qualificados no pipeline é suficiente para preencher a posição. Aciona para decidir se sourcing deve continuar ou se há candidatos suficientes.

**Examples (few-shot):**
- `"quantos candidatos temos no pipeline?"`
- `"checa o volume de inscritos na vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `proactive_suggest` — Sugestão proativa

**Descrição completa:**
> Sugere ações proativas de sourcing baseadas em análise do pipeline e mercado de talentos. Aciona quando vaga está sem movimento ou pipeline abaixo do esperado.

**Examples (few-shot):**
- `"me sugere candidatos proativamente"`
- `"tem alguém que encaixa nessa vaga?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `filter_candidates` — Filtrar candidatos

**Descrição completa:**
> Aplica filtros avançados ao pipeline de candidatos: score, etapa, localização, disponibilidade, data de cadastro. Aciona quando recruiter quer segmentar lista de candidatos.

**Examples (few-shot):**
- `"filtra os candidatos por seniority"`
- `"aplica filtro de localização"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `rank_candidates` — Rankear candidatos

**Descrição completa:**
> Ordena candidatos por score de compatibilidade, score WSI e prioridade de contato. Aciona para gerar shortlist ranqueada ou priorizar próximos a contatar.

**Examples (few-shot):**
- `"ranqueia os candidatos por fit"`
- `"ordena por score WSI"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `compare_candidates` — Comparar candidatos

**Descrição completa:**
> Compara candidatos selecionados lado a lado em skills, experiência, score e pontos fortes. Aciona quando recruiter tem múltiplos finalistas e precisa decidir quem avançar.

**Examples (few-shot):**
- `"compara estes dois candidatos"`
- `"qual é melhor entre esses perfis?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `talent_pool_search` — Busca talent pool

**Descrição completa:**
> Busca candidatos no pool interno de talentos da empresa incluindo ex-candidatos e indicados. Aciona como primeira etapa de sourcing para aproveitar banco interno antes de busca externa. Distinto de auto_source (que inclui sourcing externo) e de suggest_candidates (que retorna sugestões a revisar).

**Examples (few-shot):**
- `"amplia a busca pra mais canais"`
- `"busca em mais fontes além do pool"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `pearch_search` — Busca Pearch

**Descrição completa:**
> Executa busca via Pearch AI para encontrar candidatos passivos com perfil técnico específico. Aciona para vagas técnicas de difícil preenchimento ou quando banco interno não tem candidatos suficientes.

**Examples (few-shot):**
- `"busca no Pearch por esse perfil"`
- `"pesquisa candidatos via Pearch"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `build_search_strategy` — Estratégia de busca

**Descrição completa:**
> Define estratégia de sourcing personalizada para a vaga: canais, critérios, volume e timeline. Aciona no início de vaga nova para estruturar abordagem de busca.

**Examples (few-shot):**
- `"monta uma estratégia de busca pra essa vaga"`
- `"como devo fazer o sourcing?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `analyze_search_results` — Analisar resultados

**Descrição completa:**
> Analisa efetividade dos resultados de busca: qualidade dos matches, taxa de retorno e gaps de critérios. Aciona após busca para avaliar se estratégia precisa ser ajustada.

**Examples (few-shot):**
- `"analisa os resultados da busca"`
- `"o que esses candidatos têm em comum?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `feedback_search` — Feedback de busca

**Descrição completa:**
> Registra feedback do recruiter sobre qualidade dos candidatos retornados para melhorar próximas buscas. Aciona quando recruiter avalia candidatos e quer refinar busca.

**Examples (few-shot):**
- `"dá feedback dos resultados de busca"`
- `"ajusta a busca com base nesse feedback"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `expand_search` — Expandir busca

**Descrição completa:**
> Amplia critérios de busca relaxando restrições quando não há candidatos suficientes no pool atual. Aciona quando busca retorna poucos resultados e recruiter precisa ampliar escopo.

**Examples (few-shot):**
- `"busca pool de talentos"`
- `"quero encontrar pool de talentos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `contact_candidates` — Contatar candidatos

**Descrição completa:**
> Inicia outreach para candidatos selecionados com mensagem personalizada via canal preferido. Aciona para engajar candidatos passivos ou confirmar interesse de candidatos ativos.

**Examples (few-shot):**
- `"entra em contato com esses candidatos"`
- `"aborda os candidatos selecionados"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `screen_candidates` — Triagem rápida

**Descrição completa:**
> Executa screening inicial rápido de candidatos com checklist de desqualificadores objetivos. Aciona como pré-triagem para reduzir volume antes da triagem WSI completa.

**Examples (few-shot):**
- `"faz triagem rápida destes candidatos"`
- `"elimina os que não têm os requisitos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `assess_market` — Avaliar mercado

**Descrição completa:**
> Analisa o mercado de talentos disponíveis para a posição: volume, competição, faixa salarial e disponibilidade. Aciona no início da vaga para calibrar expectativas de prazo e salário.

**Examples (few-shot):**
- `"avalia o mercado pra esse cargo"`
- `"como está a oferta de profissionais?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `export_candidates` — Exportar candidatos

**Descrição completa:**
> Exporta lista de candidatos filtrados para CSV ou Excel para análise externa ou relatório. Aciona quando recruiter precisa compartilhar lista com cliente ou fazer análise offline.

**Examples (few-shot):**
- `"exporta lista de candidatos em CSV"`
- `"baixa os candidatos desta vaga"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `import_candidates` — Importar candidatos

**Descrição completa:**
> Importa candidatos de arquivo CSV, planilha ou integração externa para o banco de talentos. Aciona ao migrar dados de outra plataforma ou receber lista de candidatos do cliente.

**Examples (few-shot):**
- `"importa candidatos de um arquivo"`
- `"carrega lista de candidatos de uma planilha"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `dedup_candidates` — Deduplicar

**Descrição completa:**
> Remove candidatos duplicados do pipeline identificando registros com mesmo email ou documento. Aciona periodicamente ou quando pipeline mostra inconsistências de contagem.

**Examples (few-shot):**
- `"remove candidatos duplicados"`
- `"consolida perfis repetidos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `tag_candidates` — Taguear candidatos

**Descrição completa:**
> Adiciona tags personalizadas aos candidatos para segmentação e busca rápida posterior. Aciona quando recruiter quer categorizar candidatos por perfil, status ou interesse.

**Examples (few-shot):**
- `"coloca tags nesses candidatos"`
- `"marca estes como prioridade"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `engagement_pipeline` — Pipeline engagement

**Descrição completa:**
> Gerencia fluxo automatizado de engajamento com candidatos passivos: sequência de contatos, follow-ups e respostas. Aciona para campanhas de nurturing de talentos no banco interno.

**Examples (few-shot):**
- `"mostra pipeline de engajamento"`
- `"como está o engajamento dos candidatos?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `schedule_outreach` — Agendar outreach

**Descrição completa:**
> Agenda contato futuro com candidato passivo para momento mais adequado (ex: após período de confidencialidade). Aciona quando recruiter quer manter candidato ativo para oportunidades futuras.

**Examples (few-shot):**
- `"agenda abordagem desses candidatos"`
- `"programa o outreach pra segunda"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `update_candidate_stage` — Mover candidato de etapa

**Descrição completa:**
> Move candidato para outra etapa do pipeline com registro de motivo e notificação automática. Aciona quando recruiter aprova candidato para próxima fase do processo seletivo.

**Examples (few-shot):**
- `"atualiza etapa deste candidato"`
- `"move o João para shortlist"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `reject_candidate` — Rejeitar candidato

**Descrição completa:**
> Rejeita candidato do processo seletivo com motivo e opção de envio de feedback. FairnessGuard ativo. Aciona quando candidato não atende requisitos mínimos ou foi preterido por outro.

**Examples (few-shot):**
- `"rejeita este candidato"`
- `"reprova o Fernando"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `shortlist_candidate` — Favoritar candidato

**Descrição completa:**
> Adiciona candidato à shortlist de favoritos para decisão final ou apresentação ao hiring manager. Aciona quando recruiter identifica candidato forte para manter em evidência.

**Examples (few-shot):**
- `"coloca o candidato na shortlist"`
- `"favorita o Lucas"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `add_candidate_to_vacancy` — Adicionar candidato à vaga

**Descrição completa:**
> Vincula candidato existente no banco de talentos a uma vaga específica para iniciar processo seletivo. Aciona quando candidato foi encontrado externamente e recruiter quer incluí-lo no pipeline.

**Examples (few-shot):**
- `"adiciona candidato"`
- `"inclui candidato"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_candidate_stats` — Estatísticas de candidatos

**Descrição completa:**
> Obtém métricas e estatísticas do candidato no pipeline: etapa atual, score, histórico de avaliações e comunicações. Aciona para contextualização antes de ação sobre candidato específico.

**Examples (few-shot):**
- `"mostra estatísticas do candidato"`
- `"qual o score médio deste perfil?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_candidate_history` — Histórico do candidato

**Descrição completa:**
> Obtém histórico completo de participação do candidato em processos seletivos anteriores na plataforma. Aciona para verificar se candidato já foi avaliado antes ou reativar candidatura anterior.

**Examples (few-shot):**
- `"mostra histórico do candidato"`
- `"o que já aconteceu com ele no processo?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### Domínio: `talent_pool` (6 actions)

### `create_talent_pool` — Criar Banco de Talentos

**Descrição completa:**
> Cria novo banco de talentos vivo com nome, arquétipo de candidato ideal e critérios de triagem. Aciona quando empresa quer manter pool de candidatos para posições recorrentes.

**Examples (few-shot):**
- `"cria pool de talentos"`
- `"monta banco de talentos de devs"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('name',)` |
| `optional_params` | `('archetype_id', 'description')` |
| `tags` | `[]` |

---

### `list_talent_pools` — Listar Bancos de Talentos

**Descrição completa:**
> Lista bancos de talentos ativos com nome, arquétipo, contagem de candidatos e última atualização. Aciona quando recruiter quer gerenciar pools ou selecionar pool para ação.

**Examples (few-shot):**
- `"lista pools de talentos"`
- `"mostra meus pools"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `[]` |
| `optional_params` | `('status',)` |
| `tags` | `[]` |

---

### `add_to_pool` — Adicionar ao Pool

**Descrição completa:**
> Adiciona candidatos ao banco de talentos com origem registrada para rastreamento. Aciona após processo seletivo para manter candidatos aprovados não contratados ou ao receber indicações.

**Examples (few-shot):**
- `"adiciona candidato ao pool"`
- `"guarda este perfil no banco de talentos"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('pool_id', 'candidate_ids')` |
| `optional_params` | `('origin',)` |
| `tags` | `[]` |

---

### `move_pool_to_job` — Mover para Vaga

**Descrição completa:**
> Migra candidatos do pool para uma vaga específica na etapa selecionada, iniciando processo seletivo. Requer confirmação. Aciona quando vaga abre e candidatos do pool são elegíveis.

**Examples (few-shot):**
- `"move pool pra uma vaga"`
- `"aproveita este pool na vaga 45"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('pool_id', 'job_id', 'candidate_ids', 'target_stage')` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

### `get_pool_candidates` — Ver Candidatos do Pool

**Descrição completa:**
> Lista candidatos de um banco de talentos com estágios, scores e disponibilidade para análise e ação. Aciona quando recruiter quer ver quem está no pool ou selecionar candidatos para vaga.

**Examples (few-shot):**
- `"mostra candidatos do pool"`
- `"quem tem neste banco de talentos?"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `False` |
| `required_params` | `('pool_id',)` |
| `optional_params` | `('stage', 'limit')` |
| `tags` | `[]` |

---

### `create_job_from_pool` — Criar Vaga do Pool

**Descrição completa:**
> Cria nova vaga a partir de um banco de talentos herdando arquétipo, critérios e configurações do pool. Requer confirmação. Aciona quando nova posição tem perfil igual ao pool existente.

**Examples (few-shot):**
- `"cria vaga usando candidatos do pool"`
- `"abre posição pra este pool"`

**Campos técnicos:**

| Campo | Valor |
|-------|-------|
| `requires_confirmation` | `True` |
| `required_params` | `('pool_id',)` |
| `optional_params` | `[]` |
| `tags` | `[]` |

---

## Clusters semânticos disambiguados (FIX 7+11)

Três grupos de ações similares foram identificadas como fonte de confusão no LLM. FIX 7 e FIX 11 adicionaram cross-references nas descriptions.

### Cluster 1 — Melhorar Job Description (job_management)

| action_id | Comportamento |
|-----------|---------------|
| `generate_jd` | Cria JD do zero com IA |
| `enrich_jd` | Enriquece JD existente, aplicando melhorias |
| `suggest_jd_improvements` | Só sugere edições, não sobrescreve |

Cada uma referencia as outras no texto de `description` via `Distinto de X (que ...)`.

### Cluster 2 — Buscar candidatos (sourcing)

| action_id | Comportamento |
|-----------|---------------|
| `auto_source` | Sourcing automático com outreach |
| `suggest_candidates` | Sugere perfis para revisão manual |
| `talent_pool_search` | Busca só no pool interno, sem sourcing externo |

### Cluster 3 — Perguntas WSI (job_management vs cv_screening)

| action_id | Domínio | Quando usar |
|-----------|---------|-------------|
| `generate_wsi_questions` | `job_management` | Na configuração da vaga, antes da triagem começar |
| _(dinamicamente)_ | `cv_screening` | Durante a triagem, adaptando por candidato |

`generate_wsi_questions` em `job_management/actions.py` tem cross-ref explícito para o fluxo em `cv_screening`.

---
## Reverse index — Tool → DomainActions que a invocam

| Tool | Invocada por |
|------|---------------|

---

## Estatísticas

- **103** ferramentas (tools) no registry
- **281** DomainActions em **18** domínios
- Geração automática via `scripts/generate_tool_action_glossary.py`

## Regenerar este documento

```bash
# Em lia-agent-system/ root:
python scripts/generate_tool_action_glossary.py

# Ou em CI:
python scripts/generate_tool_action_glossary.py --check  # exit 1 se stale
```

## Ver também

- [`docs/LIA_AI_HANDOFF.md`](./LIA_AI_HANDOFF.md) — Handoff técnico das 12 melhorias
- [`docs/specs/ai/ADR-019-governance-and-observability.md`](./specs/ai/ADR-019-governance-and-observability.md) — Decisões arquiteturais
- [`docs/specs/CANONICAL_SOURCES_SPEC.md`](./specs/CANONICAL_SOURCES_SPEC.md) — Registry canônico
- [`app/tools/tool_registry_metadata.yaml`](../app/tools/tool_registry_metadata.yaml) — fonte YAML

*Última regeneração: 2026-04-21 11:14 UTC*
