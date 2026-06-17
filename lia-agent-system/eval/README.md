# LIA Eval Suite

Enterprise test framework for LIA — 72 cases across 12 categories.
Tests functional behavior, tool execution, context awareness, and robustness.

## Quick Start

```bash
cd /home/runner/workspace/lia-agent-system/eval

# 1. Run all tests (needs JWT token from browser DevTools > Application > Cookies)
python eval_runner.py --token <YOUR_JWT> --url http://localhost:8001

# 2. Re-score failures with Claude (needs ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-ant-... python eval_judge.py eval_results_20260417_*.json

# 3. Generate HTML report
python eval_report.py eval_results_20260417_*_judged.json
# Open eval_report_*.html in browser
```

## Run Specific Categories

```bash
# Only Job Management + Candidate Management
python eval_runner.py --token <JWT> --categories JM,CM

# Single case
python eval_runner.py --token <JWT> --id JM-001

# Critical cases only
python eval_runner.py --token <JWT> --categories CX,EX,MT
```

## Score Interpretation

| Score | Label   | Meaning |
|-------|---------|---------|
| 0     | FAIL    | Anti-pattern detected, refused, or empty response |
| 1     | PARTIAL | Attempted but missed key criteria |
| 2     | PASS    | Main criteria met, no critical issues |
| 3     | PERFECT | All criteria met, proactive, correct tool use |

**Target: ≥ 80% pass rate (score ≥ 2)**

## Categories

| ID | Name                  | Cases | Key Agents |
|----|-----------------------|-------|------------|
| JM | Job Management        | 8     | jobs_mgmt |
| CM | Candidate Management  | 8     | pipeline, sourcing |
| KB | Kanban / Pipeline     | 6     | kanban |
| SC | Screening / WSI       | 6     | pipeline, wsi |
| CO | Communication         | 5     | communication |
| AN | Analytics / Reports   | 6     | analytics |
| SO | Sourcing              | 6     | sourcing |
| WZ | Wizard / Job Creation | 5     | wizard |
| PR | Predictive / Proactive| 5     | analytics, proactive |
| MT | Multi-task Planning   | 5     | main_orchestrator |
| CX | Context Awareness     | 6     | context_adapter, agent_chat_ws |
| EX | Edge Cases            | 7     | security, fairness_guard |

## How to Get a JWT Token

1. Open the LIA platform in your browser
2. Open DevTools → Application → Cookies
3. Copy the value of the `auth_token` or `access_token` cookie
4. Or: DevTools → Network → any API call → Request Headers → `Authorization: Bearer <TOKEN>`

## Adding New Cases

Edit `eval_cases.yaml`. Follow the schema:

```yaml
- id: XX-NNN
  category: XX           # 2-letter category code
  severity: critical     # critical | high | medium | low
  title: "Short title"
  prompt: "Exact message to send to LIA"
  context:
    scope: "Vagas"       # Page tag shown in chat input
    page: "gestao-vagas" # URL path
    entity_id: "V0037"   # Optional: job/candidate ID in context
    entity_type: "job"   # Optional: job | candidate
  expected_tools:
    - tool_name
  expected_behavior: "Description of what LIA should do"
  canonical_files:
    - "app/path/to/file.py"
  success_criteria:
    - "Specific measurable criterion"
  anti_patterns:
    - "Thing LIA should NOT do"
```

## Canonical File Map (Quick Reference)

When a category fails, fix these files first:

| Category | Primary Files to Check |
|----------|------------------------|
| JM | `jobs_mgmt_tool_registry.py`, `jobs_mgmt_system_prompt.py` |
| CM | `pipeline_react_agent.py`, `sourcing_tool_registry.py` |
| KB | `kanban_tool_registry.py`, `kanban_react_agent.py` |
| SC | `wsi/`, `cv_screening_service.py`, `fairness_guard.py` |
| CO | `communication_tool_registry.py`, `email_adapter.py` |
| AN | `analytics_tool_registry.py`, `analytics_react_agent.py` |
| SO | `sourcing_tool_registry.py`, `sourcing_react_agent.py` |
| WZ | `wizard_tool_registry.py`, `wizard_react_agent.py` |
| PR | `proactive_alert_service.py`, `early_warning_service.py` |
| MT | `main_orchestrator.py`, `agentic_loop.py` |
| CX | `context_adapter.py`, `agent_chat_ws.py`, `tenant.py` |
| EX | `prompt_injection_guard.py`, `fairness_guard.py` |
