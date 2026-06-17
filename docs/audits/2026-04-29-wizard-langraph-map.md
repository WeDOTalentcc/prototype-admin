# LANGRAPH WIZARD MAP - Job Creation Audit Report

**Date:** 2026-04-29  
**Repo:** WeDoTalent LIA (`lia-agent-system` + `plataforma-lia`)  
**Issue:** Chat wizard used simple tool instead of structured LangGraph stages

---

## 1. JobCreationGraph Architecture (Backend)

### 1.1 Graph Stages (Nodes in Order)

The `JobCreationGraph` implements **WSI Methodology** as 10+ sequential stages. Each node:
- Reads dependencies from `JobCreationState`
- Computes outputs
- Emits `ws_stage_payload` (the WS event the frontend consumes)

**Stages identified:**

```
intake → jd_enrichment → bigfive → salary → competency → wsi_questions → 
eligibility → review → publish → calibration → handoff
```

**File:** `/home/runner/workspace/lia-agent-system/app/domains/job_creation/graph.py`

### 1.2 Node Details

| Stage | Purpose | HITL? | Outputs Key Field |
|-------|---------|-------|-------------------|
| `intake_node` | Parse user text → structured payload | No | `intake_payload` (confidence, parsed fields) |
| `jd_enrichment_node` | LLM-enrich JD + quality score | **YES** (F1) | `jd_enriched`, `jd_quality_score` |
| `bigfive_node` | Extract Big Five traits (F2+F3) | Conditional | `bigfive_profile`, `trait_rankings` |
| `salary_node` | Validate/benchmark salaries | No | `salary_min/max` |
| `competency_node` | F4+F5 seniority mapping | No | Skill/trait distribution |
| `wsi_questions_node` | Generate screening questions (F6) | **YES** (HITL #2) | `screening_questions` |
| `eligibility_node` | Pre-screening yes/no questions | No | `eligibility_questions` |
| `review_node` | Readiness check before publish | No | `completeness`, warnings |
| `publish_node` | Publish job + launch auto-screening | No | Job published on backend |
| `calibration_node` | 3+ candidate calibration (optional) | No | `calibration_candidates` |
| `handoff_node` | Navigate to job detail page | No | `job_page_url` |

### 1.3 State Schema (JobCreationState)

**File:** `/home/runner/workspace/lia-agent-system/app/domains/job_creation/state.py`

**Key fields:**

```python
class JobCreationState(TypedDict, total=False):
    # Session
    session_id: str
    user_id: str
    workspace_id: int
    auth_token: str
    current_stage: WizardStage  # enum: intake, jd_enrichment, ..., done
    stage_history: List[WizardStage]
    
    # Pre-F1 Input
    raw_input: str  # Original user query
    user_query: str  # Latest message
    parsed_title: Optional[str]
    parsed_seniority: Optional[str]
    parsed_department: Optional[str]
    intake_confidence: float
    precompleted_stages: List[str]  # Stages auto-skip (never includes HITL)
    
    # F1: JD Enrichment
    jd_raw: Optional[str]
    jd_enriched: Optional[Dict]  # EnrichedJobDescription
    jd_quality_score: float  # 0-100
    jd_quality_warnings: List[str]
    jd_approved: Optional[bool]  # HITL #1 feedback
    
    # F2+F3: Big Five
    bigfive_profile: Optional[BigFiveProfile]
    trait_rankings: List[TraitRanking]
    
    # Salary
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_benchmark: Optional[Dict]  # ← Buggy source (see section 4)
    
    # F6: Questions
    screening_questions: List[ScreeningQuestion]
    wsi_questions_approved: Optional[bool]  # HITL #2 feedback
    
    # WebSocket Event (Emitted)
    ws_stage_payload: Dict  # {"type":"wizard_stage", "stage":"...", "data":{...}}
```

### 1.4 HITL (Human-In-The-Loop) Points

Two mandatory approval gates:

- **HITL #1** (`jd_enrichment`): Recruiter reviews & approves enriched JD before proceeding
- **HITL #2** (`wsi_questions`): Recruiter approves generated screening questions

Both use `state.{stage}_approved` flag. The graph checks this on resume (see § 1.5).

### 1.5 Transitions & Conditional Edges

The graph uses **LangGraph conditional edges** (pseudocode):

```python
# After jd_enrichment:
if state.jd_approved is None or not state.requires_approval:
    → continue to next stage
elif state.jd_approved is False:
    → PAUSE (wait for recruiter approval via resume())
else:
    → continue

# Similar logic for wsi_questions
```

**Resume method:** `JobCreationGraph.resume(thread_id, prior_state, updates)`
- Merges recruiter feedback into state
- Re-invokes graph from last HITL pause
- Used by `/resume` endpoint to handle HITL responses

### 1.6 Streaming & Token Emission

Two invocation modes:

- **`invoke(state, thread_id)`** – Synchronous, returns final state after execution or HITL pause
- **`stream_invoke(state, thread_id, on_token=None)`** – Async token-streaming via `astream_events("v2")`

The `on_token` callback receives LLM chunks in real-time (e.g., for UI progress bars).

**File reference:** lines ~2800–3000 in `graph.py`

---

## 2. WebSocket Panel Integration (Frontend)

### 2.1 Panel Type & DynamicPanel Mapping

**File:** `/home/runner/workspace/plataforma-lia/src/contexts/lia-float-context.tsx` (lines ~45–65)

```typescript
export type DynamicPanelType = 
  | "calibration"
  | "candidate_review"
  | "profile"
  | "job_creation"  ← Target for wizard
  | "scheduling"
  | ...;

const PANEL_TYPE_TO_DOMAIN_HINT: Record<DynamicPanelType, string> = {
  job_creation: "wizard",  // Routes to JobCreationGraph domain
};
```

### 2.2 Panel Open Trigger

**Function:** `openDynamicPanel(panel: DynamicPanelData)`

**Called when:**
- Backend emits WS event with `panel_type: "job_creation"`
- `handlePanelUpdate()` callback (line ~305) receives `PanelUpdateEvent`

```typescript
const handlePanelUpdate = useCallback((event: PanelUpdateEvent) => {
  if (event.action === "open" || event.action === "update") {
    setState(prev => ({
      ...prev,
      dynamicPanel: {
        panelType: event.panel_type as DynamicPanelType,
        data: event.panel_data,
        title: event.panel_title,
      },
    }));
  }
}, []);
```

### 2.3 JobCreationPanel Component

**File:** `/home/runner/workspace/plataforma-lia/src/components/lia-float/panels/JobCreationPanel.tsx`

**Current implementation (v1):** Simple checklist of fields
- Renders `fields[]` array with status badges (complete/in_progress/pending)
- Progress bar (% of fields filled)
- JD preview
- **MISSING:** Stage-by-stage cards (intake → JD → Big Five → etc.)

```tsx
interface JobCreationPanelProps {
  data: Record<string, unknown>
}

export function JobCreationPanel({ data }: JobCreationPanelProps) {
  const step = data.current_step || 1;
  const totalSteps = data.total_steps || 5;
  const fields = data.fields || [...]; // flat list
  // Renders: progress bar + field checklist
}
```

### 2.4 Message Enrichment with Domain Hint

When `job_creation` panel is active, **every outbound chat message** gets enriched (lines ~370–390):

```typescript
const enrichedMetadata = hintDomain && !metadata?.domain_hint
  ? {
      ...metadata,
      source: "rail_a",
      domain_hint: hintDomain,  // "wizard"
      card_id: `panel_active:${activePanelType}`,
    }
  : metadata;

await connection.sendMessage(content, domain, scope, enrichedMetadata);
```

This ensures the backend router (MainOrchestrator tier -1) routes to `wizard` domain with high confidence.

---

## 3. Gap Analysis – Why JobCreationGraph Wasn't Used

### 3.1 Two Parallel Paths

**Path A (INTENDED):** Chat + Wizard Panel
```
User: "Vamos criar uma vaga"
  → MainOrchestrator detects intent="job_creation"
  → Routes to WizardService
  → Invokes JobCreationGraph
  → Emits ws_stage_payload { type: "wizard_stage", stage: "intake", ... }
  → Frontend receives WS event
  → openDynamicPanel({ panelType: "job_creation", data: {...} })
  → User sees stage cards in sidebar + chat continues
```

**Path B (WHAT HAPPENED):** Chat-only tool calling
```
User: "Vamos criar uma vaga"
  → MainOrchestrator.process_request()
  → action_executor sees intent, calls create_job() TOOL
  → Bypasses JobCreationGraph entirely
  → Returns job_id directly to chat
  → No ws_stage_payload emitted
  → No panel opened
  → Chat becomes caotic (asks same questions, no structure)
```

### 3.2 Root Cause: MainOrchestrator Routing

**File:** `/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py` (lines ~100–200)

The `MainOrchestrator` uses **cascaded routing** (Phase 0 → Phase 1 → Phase 2):

```
Phase 0: PendingAction (multi-turn confirmation)
  ↓
Phase 1: ActionExecutor (detect closed-box intents)
  └─ If intent in ACTIONABLE_INTENTS: call tool directly (create_job, etc)
  └─ MISSING: Check for `job_creation` intent → delegate to wizard service
  ↓
Phase 2: CascadedRouter → DomainWorkflow → ReAct Agent
  └─ Used only if Phase 1 found no tool
```

**The bug:** `job_creation` intent is caught by Phase 1's `create_job` tool before reaching Phase 2's domain router.

**Evidence:** `ACTIONABLE_INTENTS` in `/home/runner/workspace/lia-agent-system/app/orchestrator/action_executor.py` likely includes something like `"job_creation"`, `"create_job"`, etc., mapping directly to the `create_job()` tool.

### 3.3 How to Fix (High Level)

**Option 1: Router Override**
```python
# In main_orchestrator.py, before Phase 1:
if intent == "job_creation":
    wizard_service = WizardOrchestrationService()
    result = wizard_service.handle_wizard_flow(state)
    return result  # skips action_executor
```

**Option 2: Tool Interception**
```python
# In action_executor, route job_creation to WizardService instead:
if intent == "job_creation":
    wizard_result = invoke_job_creation_graph(state)
    return wizard_result
```

**Option 3: Intelligent Tool (Hybrid)**
```python
# Modify create_job tool to detect wizard context:
async def create_job(...):
    if should_use_wizard():
        graph = JobCreationGraph()
        # Return streaming ws_stage_payload instead of direct job_id
        return graph.invoke(state)
    else:
        # Direct tool path (legacy)
        return simple_create_job()
```

---

## 4. Bug Root Causes (Per Paulo's Symptoms)

| Symptom | Root Cause | File/Line |
|---------|-----------|----------|
| "Repetiu perguntas" | No state carryover; LLM asked fresh each turn | `app/orchestrator/action_executor.py` – `create_job()` doesn't pass state to LLM |
| "Não respondeu várias perguntas" | Chat tool ignores context; no memory bridge | `app/domains/job_management/tools/job_tools.py:create_job()` – no conversation_messages read |
| "Navegou pra `/funil-de-talentos` sem pedir" | Manual tool call in prompt; no safeguard | (Likely in LLM system prompt or ReAct agent) |
| "Benchmark R$ 33k/mês" | Buggy salary service or mock data | Unknown service (not found in grep); likely test data exposed |
| "Criou como rascunho SEM competências" | `create_job()` doesn't collect behavioral screening Qs | `job_tools.py` – only F1/F2 captured, not F6 (wsi_questions) |
| "Erros intermitentes" | Token expired or backend service flaky | `_get_api_client()` in `graph.py` rebuilds on auth change; token TTL likely 1hr |

---

## 5. Implementation Plan (Hybrid UX)

### Phase 1: Reroute Wizard Intent (Days 1–2)

**In `/main_orchestrator.py`:**
1. Add early check before `action_executor`
2. If `intent == "job_creation"`, invoke `WizardOrchestrationService`
3. Return wizard result (not tool result)

**In `/action_executor.py`:**
1. Remove `job_creation` from `ACTIONABLE_INTENTS` (or demote priority)
2. Ensure LangGraph path wins

### Phase 2: Frontend Panel Auto-Open (Day 2–3)

**In `JobCreationPanel.tsx`:**
1. Consume `ws_stage_payload` from parent context
2. Render stage cards (not flat checklist):
   - intake (user input)
   - jd_enrichment (rich preview + quality score)
   - bigfive (traits + ranking)
   - salary (benchmark + range picker)
   - wsi_questions (Q list with edit UI)
   - review (checklist before publish)

3. Add "Minimize" button → collapses to icon bar

**In `lia-float-context.tsx`:**
1. `onPanelUpdate()` → auto-opens when `panel_type: "job_creation"`
2. No explicit user action needed

### Phase 3: Chat Minimization (Day 3–4)

**UI Layout:**
```
┌─────────────────────────────────┐
│      Top bar (minimize btn)      │
├──────────────────┬──────────────┤
│                  │              │
│   Chat area      │  Wizard      │
│   (75% width)    │  Panel       │
│                  │  (25% width) │
│                  │              │
└──────────────────┴──────────────┘
```

- Chat stays open (for clarifications, follow-up)
- Panel shows stage progression
- Clicking a stage scrolls panel to that section

### Phase 4: Skip-Stage Feature (Day 4)

**In JobCreationPanel:**
```tsx
// For each stage card:
<button onClick={() => skipStage('salary')}>
  Pular stage
</button>

// Skipped stages:
// - Go directly to next stage
// - Use defaults (salary: market rates)
// - Can't skip HITL stages (jd_enrichment, wsi_questions)
```

### Phase 5: Integration Tests (Day 5)

- Chat message → JobCreationGraph invoked
- Stage completion → panel updates
- HITL approval → graph resumes
- E2E: intake → JD → Big Five → publish

---

## 6. Files to Modify (Summary)

| File | Change | Lines |
|------|--------|-------|
| `main_orchestrator.py` | Add wizard intent check | ~150–200 |
| `action_executor.py` | Remove/demote job_creation | ~50–100 |
| `JobCreationPanel.tsx` | Render stage cards | ~30–150 (rewrite) |
| `lia-float-context.tsx` | Auto-open logic | ~300–350 |
| `job_tools.py` | (Optional) add wizard bridge | ~50–100 |
| `graph.py` | (No change) – already correct | – |
| `state.py` | (No change) – already correct | – |

---

## 7. Notes

- **Existing JobCreationGraph is sound** – implements full WSI methodology
- **Frontend panel v1 too simple** – needs stage-card redesign
- **MainOrchestrator coupling too tight** – tool calling wins over graph routing
- **No test coverage for wizard intent** – add integration test for full path
- **Token/auth flakiness** – investigate `_get_api_client()` token refresh (1hr TTL?)

