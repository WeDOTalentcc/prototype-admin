# Copilot Instructions — Background Agent (Python) Real-time Progress

## Overview

The Python background agent communicates execution progress to the Rails API via `report_progress`. Rails persists each step in `background_agent_steps` table and broadcasts via ActionCable WebSocket to the frontend.

## Architecture

```
Python Worker → POST /v1/users/background_agents/{id}/report_progress → Rails persists + broadcasts → Frontend WebSocket
```

## API Contract: `POST /v1/users/background_agents/{id}/report_progress`

### Authentication
Bearer token with `service` or `one_time_token` role.

### Request Body (JSON)

```json
{
  "step": "search_iteration",
  "status": "running",
  "message": "Searching for candidates — iteration 2",
  "cycle_id": 42,
  "iteration_number": 2,
  "details": {
    "queries_used": ["senior developer python", "backend engineer"],
    "candidates_found": 15,
    "provider": "local",
    "strategy": "diversified"
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | string | **yes** | One of: `plan`, `load_context`, `generate_queries`, `search`, `evaluate`, `score`, `deliver` |
| `status` | string | **yes** | One of: `running`, `done`, `error` |
| `message` | string | no | Human-readable description of what's happening |
| `cycle_id` | integer | no | The `agent_cycle` ID if available |
| `iteration_number` | integer | no | Current search iteration number (1-based) |
| `details` | object | no | Free-form JSON with step-specific data (see below) |

### Response

```json
{ "success": true, "step_id": 123 }
```

The `step_id` is the persisted record ID. Rails broadcasts the full step data to the frontend WebSocket immediately after persisting.

## Step Definitions & Expected Details

### `plan` (optional but recommended)
Report the agent's search plan before executing.

```python
report_progress(state, step="plan", status="done", details={
    "plan_text": "Based on the job requirements for Senior Python Developer, I will search using 3 strategies: skills-based, title-based, and location-based queries.",
    "strategies": ["skills_match", "title_match", "location_expansion"],
    "estimated_iterations": 3
})
```

### `load_context`
Loading job context, preferences, feedback history.

```python
report_progress(state, step="load_context", status="running")
# ... load context ...
report_progress(state, step="load_context", status="done", details={
    "job_title": "Senior Python Developer",
    "has_preferences": True,
    "feedback_count": 12
})
```

### `generate_queries`
LLM generating diversified search queries.

```python
report_progress(state, step="generate_queries", status="done", details={
    "queries_count": 5,
    "queries": ["python developer senior", "backend engineer python", "...]
})
```

### `search`
Executing search queries against providers.

```python
# Call TWICE per iteration: running at start, done at end
report_progress(state, step="search", status="running", iteration_number=1, details={
    "provider": "local",
    "query": "python developer senior"
})
# After search completes:
report_progress(state, step="search", status="done", iteration_number=1, details={
    "provider": "local",
    "candidates_found": 23,
    "candidates_new": 15,
    "candidates_duplicates": 8
})
```

### `evaluate`
Evaluating search results quality, deciding next action.

```python
report_progress(state, step="evaluate", status="done", details={
    "quality_score": 0.72,
    "coverage": 0.6,
    "gaps": ["lacks senior-level candidates", "no remote candidates found"],
    "diagnosis": "Good coverage for skills but missing seniority",
    "hypotheses": ["Try adding 'lead' or 'staff' to queries", "Expand location filter"],
    "decision": "NEEDS_IMPROVEMENT",
    "candidates_so_far": 15
})
```

### `score`
LLM scoring candidates.

```python
report_progress(state, step="score", status="running", details={
    "candidates_to_score": 20
})
# After scoring:
report_progress(state, step="score", status="done", details={
    "candidates_scored": 20,
    "average_score": 78.5,
    "above_threshold": 15,
    "score_distribution": {"90-100": 3, "80-89": 7, "70-79": 5, "below_70": 5}
})
```

### `deliver`
Delivering final results.

```python
report_progress(state, step="deliver", status="done", details={
    "candidates_delivered": 10,
    "total_found": 45,
    "total_iterations": 3,
    "duration_ms": 32500,
    "top_score": 95,
    "average_score": 82.3
})
```

## Implementation Pattern

### `_with_progress()` Wrapper

Every graph node should be wrapped to report progress automatically:

```python
def _with_progress(step_name: str, func):
    def wrapper(state: dict) -> dict:
        report_progress(state, step=step_name, status="running")
        try:
            result = func(state)
            report_progress(state, step=step_name, status="done", details=extract_details(result))
            return result
        except Exception as e:
            report_progress(state, step=step_name, status="error", message=str(e))
            raise
    return wrapper
```

### `report_progress()` Function

```python
import httpx

def report_progress(
    state: dict,
    step: str,
    status: str,
    message: str | None = None,
    details: dict | None = None,
    iteration_number: int | None = None
):
    agent_id = state["agent_id"]
    cycle_id = state.get("cycle_id")
    base_url = get_settings().ats_api.base_url
    token = get_ott_service().get_token()

    payload = {
        "step": step,
        "status": status,
        "message": message,
        "cycle_id": cycle_id,
        "iteration_number": iteration_number,
        "details": details
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        httpx.post(
            f"{base_url}/v1/users/background_agents/{agent_id}/report_progress",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
    except Exception as e:
        logger.warning(f"Failed to report progress: {e}")
```

## Rules

1. **Always report `running` before the step and `done` after** — this gives the frontend a real-time "in progress" indicator
2. **Include `iteration_number`** for search steps — the frontend uses it to show iteration count
3. **Include rich `details` in `evaluate`** — gaps, diagnosis, hypotheses are shown to the user as "agent thinking"
4. **Add a `plan` step** at the beginning of each cycle — generates a human-readable search plan via LLM and reports it
5. **Never let `report_progress` failures break the graph** — always wrap in try/except, log warning, continue
6. **Use step names exactly as defined** — `plan`, `load_context`, `generate_queries`, `search`, `evaluate`, `score`, `deliver`
7. **The `details` object is free-form** — include whatever is useful for the frontend to display
8. **Keep messages concise** — they appear directly in the UI
9. **Report errors with `status="error"`** — include the error message in `message` field
10. **`cycle_id` should be included** whenever available — it links steps to a specific execution cycle
