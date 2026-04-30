# Deep Dive: Intent Routing Logic in LIA — Action Executor vs JobCreationGraph

**Analysis Date:** 2026-04-29  
**Scope:** MainOrchestrator phases, ActionExecutor routing, JobCreationGraph integration  
**Status:** Complete—ready for fix proposals

---

## 1. MainOrchestrator Phase Sequence

**File:** `/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py` (1785 lines)

### Execution Flow (Canonical)

```
Phase 0.0: Rail A Capability Gate (PR-J)
   └─ Checks domain_hint from metadata.source="rail_a"
   └─ If valid domain_hint ∈ DomainRegistry → short-circuit to Phase 2

Phase 0: PendingAction (multi-turn confirmation/params)
   └─ Checks pending_action_store for unresolved intent
   └─ If params missing → returns "needs_params" + clarification prompt
   └─ If confirmation needed → returns summary for approval
   └─ If ready → _execute_action() via ACTIONABLE_INTENTS config
   └─ Returns to user or falls through to Phase 1

Phase 1: ActionExecutor (closed-loop tool-like intent matching)
   └─ Calls action_executor.try_execute(intent, entities, context)
   └─ ACTIONABLE_INTENTS lookup (200+ intents in intents_config.py)
   └─ If not_actionable → falls through to Phase 2
   └─ If needs_params/confirmation → stores pending action, returns to user
   └─ If executed → returns ActionResult + logs to conversation_memory
   └─ NOTE: **This is where job_creation bypass happens**

Phase 1.5: Agentic Tool Calling (LIA-A04)
   └─ If Phase 1 did not match, LLM can call tools
   └─ Not a full phase—optional interception

Phase 2: Orchestrator (full routing + domain workflow)
   └─ CascadedRouter (cascaded intent classification)
   └─ DomainRegistry lookup
   └─ DomainWorkflow.process() + domain-specific logic
   └─ Fallback to ReActAgent if needed
   └─ Returns DomainResponse with message + data
```

### Decision Points (Where phases skip)

| Point | Condition | Result |
|-------|-----------|--------|
| Phase 0 → 0.0 | `context.metadata.source == "rail_a"` | **Bypass all, go direct to Phase 2** |
| Phase 0 → 1 | No pending action OR action resolved | Continue to ActionExecutor |
| Phase 1 → 2 | `not is_actionable(intent)` | Fall through to Orchestrator |
| Phase 1 → user | `status in ["needs_params", "needs_confirmation"]` | **Return early, wait for user** |
| Phase 1 → conv_memory | `status == "executed"` | **Log result, return to user, stop** |

**Critical:** Phase 1 returns directly to user on `executed` status (line 534) — never reaches Phase 2.

---

## 2. ActionExecutor Deep Dive

**Files:**  
- `/app/orchestrator/action_executor/executor.py` (622 lines)  
- `/app/orchestrator/action_executor/intents_config.py` (1078 lines)  
- `/app/orchestrator/action_executor/utils.py` (utilities)  
- `/app/orchestrator/action_executor/` (handler subpackage)

### ACTIONABLE_INTENTS Structure

**Entry count:** ~200 intents mapped to 30+ action_ids

**Sample intents (partial list):**
- `mover_candidato` → `move_candidate` (pipeline_transition domain)
- `enviar_email` → `send_email` (communication domain)
- `agendar_entrevista` → `schedule_interview` (interview_scheduling domain)
- `disparar_triagem` → `start_screening` (cv_screening domain)
- `criar_automacao` → `create_automation` (automation domain)
- `comparar_candidatos` → `compare_candidates` (sourcing domain)
- ❌ **NOT FOUND:** `criar_vaga`, `criar_job`, `create_job`, `job_creation`

**Lookup failure mode:** If intent not in ACTIONABLE_INTENTS → `is_actionable()` returns False → Phase 1 returns `ActionResult(status="not_actionable")` → falls to Phase 2.

### Intent Detection Method

**File:** `/app/orchestrator/action_executor/utils.py`

Function: `_detect_intent_from_message(message, conversation_history=None)`

- Uses `MESSAGE_INTENT_PATTERNS` (regex-based keyword matching)
- ~60 regex patterns covering intent variants
- Returns matched intent or None
- Examples: `criar_tarefa` matches `(me\s+)?(cri|escrev|munt)a\s+(um[a]?\s+)?(tarefa|task|lembr|remind)`

### Fluxo do create_job Tool Call

**Path:** Does NOT exist in ACTIONABLE_INTENTS

1. User says "criar vaga" / "create job" / similar
2. MainOrchestrator.execute() calls action_executor.try_execute()
3. _detect_intent_from_message() looks in MESSAGE_INTENT_PATTERNS
4. No pattern matches "criar.*vaga" → detected = None
5. Fallback: try ACTIONABLE_INTENTS.get("") → None
6. is_actionable() returns False → ActionResult(status="not_actionable")
7. Phase 1 returns control to Phase 2
8. CascadedRouter classifies message (likely → "job_creation" domain)
9. DomainRegistry().get_instance("job_creation") succeeds
10. domain.execute_action() invoked (NOT the JobCreationGraph yet)

### Why job_creation is bypassed

**Root cause:** `intent="job_creation"` (or variants) is NOT in ACTIONABLE_INTENTS.

If Classifier returns `intent="job_creation"`:
- Phase 1 `action_executor.is_actionable("job_creation")` → False
- Phase 1 returns `not_actionable` → falls to Phase 2 ✓ (works)

BUT if there WAS a simple `create_job` entry in ACTIONABLE_INTENTS → Phase 1 would intercept and call a tool handler directly, bypassing Phase 2's DomainWorkflow entirely. This is THE CURRENT ARCHITECTURE for other actions like `move_candidate`, `send_email`.

---

## 3. JobCreationGraph Integration Status

**Files:**  
- `/app/domains/job_creation/graph.py` (11 LangGraph stages)  
- `/app/domains/job_creation/domain.py` (DomainPrompt wrapper)  
- `/app/domains/recruiter_assistant/services/wizard_action_executor.py` (separate wizard FSM)

### Graph Structure

11 Stages (defined in state nodes):
1. `intake_node` — parse recruiter free-text input
2. `jd_enrichment_node` — HITL #1 (recruiter approves JD)
3. `salary_benchmark_node` — fetch salary data
4. `wsi_questions_node` — HITL #2 (recruiter approves WSI screening questions)
5. `calibration_node` — adjust questions per job category
6. `publication_check_node` — pre-publication compliance
7. `publish_node` — create job in ATS
8. ... (4 more post-publish stages)

**HITL gates:**
- jd_enrichment: recruiter must approve AI-enriched job description
- wsi_questions: recruiter must approve AI-generated screening questions

### How DomainPrompt invokes the Graph

**File:** `/app/domains/job_creation/domain.py` (line ~43)

```python
@register_domain
class JobCreationDomain(ComplianceDomainPrompt):
    domain_id = "job_creation"
    
    async def execute_action(self, action_id: str, params: dict, context: DomainContext):
        # Forwards to job_creation_graph.stream_invoke()
        # NOT called in Phase 1 (ActionExecutor)
        # ONLY called in Phase 2 (DomainWorkflow)
```

### WebSocket Entry Point

**File:** `/app/api/v1/agent_chat_ws.py`

Routes incoming WS messages to:
- `POST /ws/agent-chat` → `wizard_first_message()` → invokes `job_creation_graph` directly
- This is the **proper entry point** for job creation (Frente D / Onda 20 context)

**Issue:** MainOrchestrator's regular HTTP endpoints do NOT know to dispatch to this WS entry; they go through phases 0-2 instead.

---

## 4. Domain Hint Routing (Tier -1)

**File:** `/app/orchestrator/services/rail_a_hint_override.py` (109 lines)

### Behavior

When FE sends WS payload with:
```json
{
  "context": {
    "metadata": {
      "source": "rail_a",
      "domain_hint": "job_creation",
      "intent_hint": "create_job"
    }
  }
}
```

**Execution:**
1. MainOrchestrator.execute() (line 483)
2. Calls `try_hint_route(ctx)` → line 508
3. `get_hint_domain()` validates `source == "rail_a"` + `domain_hint ∈ DomainRegistry`
4. Returns RouteResult with confidence=0.99, source="rail_a_hint_override"
5. **Bypasses Phase 1 entirely** → jumps to Phase 2 with guaranteed domain match
6. DomainRegistry.get_instance("job_creation") → JobCreationDomain instance
7. Invokes domain workflow correctly

**Registered domains:** `DomainRegistry.list_domains()` includes `"job_creation"` ✓

### Precedence

Rail A hint evaluated at **Phase 0.0** (before ActionExecutor Phase 1) per line 483:

```python
# Phase 0.0: Rail A hint
hint_route = try_hint_route(ctx)
if hint_route:
    # Jump to Phase 2 directly
```

---

## 5. WSI Methodology + HITL Documentation

**Documented in:** Graph code comments + state definition

**11-stage pipeline maps to WSI Bloco A (F1-F6 canonical):**
- F1: intake + enrichment (HITL gate)
- F2-F5: enrichment/salary/WSI gen
- F6: WSI question approval (HITL gate)
- Post-publish: validation + calibration

**ADR-019** (Sprint II–IV): canonical service extraction pattern; job_creation_graph is exemplar.

No separate ADR for WSI methodology—embedded in graph.py comments + task #850.

---

## 6. Minimal Fix Proposals

### Option A: Demote create_job in Phase 1, Add Rail A Hint (LEAST INVASIVE)

**Changes:**
1. **Do NOT add** `create_job` to ACTIONABLE_INTENTS
2. Ensure `domain_hint="job_creation"` sent from FE (rail_a_hint_override handles it)
3. For HTTP clients: enhance context_type_override to recognize "job_creation" intent

**Files changed:** 0–1 (context_type_override service, if needed)  
**Lines changed:** ~20  
**Risk:** Low—Phase 1 already falls through on non-actionable intents; Rail A hint already works

**Trade-off:** Requires FE cooperation; HTTP clients without metadata won't use graph

---

### Option B: Intercept Before Phase 1 (MINIMAL)

**Changes:**
1. In MainOrchestrator.execute() Phase 0, add Pre-Phase-1 check:
   ```python
   if intent in ("job_creation", "create_job", "criar_vaga"):
       return await self._delegate_to_domain("job_creation", ctx, ...)
       # Skip Phase 1 entirely, go direct to Phase 2
   ```
2. Hardcode 3–5 critical intents that MUST bypass ActionExecutor

**Files changed:** main_orchestrator.py  
**Lines changed:** ~15  
**Risk:** Medium—hardcoded list is brittle; future intents need same treatment

**Advantage:** No Rail A metadata required; works for all clients

---

### Option C: Create WizardOrchestrationService (MODERATE)

**Changes:**
1. New service: `/app/orchestrator/services/wizard_orchestration_service.py`
   ```python
   class WizardOrchestrationService:
       async def try_route_to_wizard(self, intent, context):
           if intent in WIZARD_INTENTS:
               return await job_creation_graph.stream_invoke(...)
           return None
   ```
2. In Phase 1 `_try_action_executor()`, add pre-check:
   ```python
   wizard_result = await wizard_orchestration_service.try_route_to_wizard(intent, ctx)
   if wizard_result:
       return wizard_result
   ```

**Files changed:** main_orchestrator.py, new service file  
**Lines changed:** ~40  
**Risk:** Low-medium—introduces new service layer but isolates wizard logic

**Advantage:** Clean separation; mirrors existing override services (rail_a, context_type)

---

### Option D: Refactor Phase 1 to delegate unknown intents (HIGHEST)

**Changes:**
1. Extend ActionExecutorService with domain-aware fallback:
   ```python
   async def try_execute(self, intent, ...):
       if not self.is_actionable(intent):
           domain = DomainRegistry().get_instance(intent)
           if domain:
               # Execute via domain instead of returning not_actionable
               return await domain.execute_action(...)
       # ... existing logic
   ```

**Files changed:** action_executor/executor.py  
**Lines changed:** ~25  
**Risk:** Medium—ActionExecutor was designed as closed-loop only; domain delegation blurs responsibility

**Advantage:** Unified Phase 1 fallback for all non-actionable intents

---

## Summary Table

| Option | Files | Lines | Risk | Requires | Effort |
|--------|-------|-------|------|----------|--------|
| A (Rail A hint) | 0–1 | ~20 | Low | FE metadata | Low |
| B (Pre-Phase-1 gate) | 1 | ~15 | Medium | Hardcode list | Low |
| C (Service) | 2 | ~40 | Low-med | Service layer | Medium |
| D (Fallback in Phase 1) | 1 | ~25 | Medium | Domain lookup | Low |

---

## Regression Risk Analysis

**Safe zones** (low regression):
- Rail A hint (Phase 0.0) — already in code, tested
- Pre-Phase-1 gate — new branch, doesn't affect existing Phase 1 logic
- WizardOrchestrationService — isolated service, no side effects

**Risky zones:**
- Modifying ActionExecutor fallback — changes Phase 1 behavior for ALL intents
- Hardcoding intent list — maintenance burden; future features will forget to add

---

## Recommended Fix: Option C

**Rationale:**
1. **Mirrors canonical patterns** (ADR-019): rail_a_hint_override, context_type_override already exist
2. **Minimal Phase 1 changes**: one `if wizard_result` block
3. **Future-proof**: service can grow to handle more wizard-like graphs (e.g., team_creation_graph)
4. **Clean separation**: wizard logic out of action_executor
5. **No FE dependency**: works without domain_hint metadata

**Implementation sketch:**
```python
# new file: app/orchestrator/services/wizard_orchestration_service.py
WIZARD_INTENTS = frozenset({"job_creation", "criar_vaga", "create_job"})

class WizardOrchestrationService:
    async def try_route_to_wizard(self, intent: str, ctx: dict) -> ActionResult | None:
        if intent not in WIZARD_INTENTS:
            return None
        from app.domains.job_creation.graph import job_creation_graph
        # Invoke graph and wrap result as ActionResult
        ...
        
# in main_orchestrator.py Phase 1 (~line 527):
action_response = await wizard_service.try_route_to_wizard(intent, ctx)
if action_response is not None:
    return action_response
action_response = await self._try_action_executor(ctx, conv_id)
```

---

## Open Questions

1. **How does `wizard_react_agent.py` (Onda 20/Frente D) relate?**
   - Is it the same as JobCreationGraph or a separate agent?
   - Should it replace the graph or sit beside it?

2. **Domain hint versioning:** Should Rail A hints be declared in a registry (RAIL_A_HINT_REGISTRY) to avoid silent mismatches?

3. **Async context propagation:** Ensure conversation_memory + state updates happen at the same layer as Phase 1 (line 529–534).

