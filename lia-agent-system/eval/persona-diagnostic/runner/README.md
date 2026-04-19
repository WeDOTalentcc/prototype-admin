# Persona Diagnostic — Automated Suite

Turns the manual 120-probe persona diagnostic (see `../diagnostico-persona.md`)
into a single-command, repeatable evaluation.

## What it does

1. **Probe sheet contract** — `../probes.yaml` (auto-generated from
   `plataforma-lia/e2e/tests/persona-diagnostic/probes.ts`). 120 probes
   across 10 thematic categories + 6 specialised agents, each tagged with
   id / category / agent / criticality / prompt / expected behaviour /
   suggested context.
2. **Runner** — `runner.py` authenticates as the demo recruiter (auto-issued
   JWT signed with the backend's `SECRET_KEY`), then POSTs each probe to
   `POST /api/v1/chat`, nudging routing via `context.scope` / `context.page`
   per the probe's agent target. Each probe runs in its own conversation_id.
3. **LLM-as-Judge** — `judge.py` calls Claude Haiku at `temperature=0` with
   the rubric in `../scoring-rubric.md`. Returns score 0–3 and an
   independent critical-failure flag (1 of 9 triggers).
4. **Consolidated report** — `report.py` emits a JSON contract and a Markdown
   report with: per-category pass/fail vs. thresholds, per-agent averages,
   weighted overall score, and a baseline diff against the last consolidated
   report on disk.
5. **Single command + non-zero exit** — `run_diagnostic.py` is the only
   entry point. Exits **1** if any critical failure is detected.

## Run it

```bash
# from repo root, with lia-backend running on :8001:
python lia-agent-system/eval/persona-diagnostic/runner/run_diagnostic.py
```

Useful flags:

```bash
# only one category
... --categories "A. Identidade,D. Fairness"

# only specific probes
... --ids ID-001,ID-002,FAI-003

# only one agent
... --agents WSI

# capture only (skip judge & rubric)
... --skip-judge

# point at a different baseline
... --baseline lia-agent-system/eval/persona-diagnostic/runs/report-prev.json

# never block CI even on critical failures
... --allow-critical
```

Required env vars:

| Var | Purpose | Default |
|-----|---------|---------|
| `ANTHROPIC_API_KEY` | LLM-as-judge (Claude Haiku) | required for scoring |
| `LIA_BACKEND_URL` | Where the LIA backend is | `http://localhost:8001` |
| `LIA_TEST_TOKEN` | Override the auto-issued recruiter JWT | optional |
| `PERSONA_JUDGE_MODEL` | Override judge model | `claude-haiku-4-5-20251001` |

## Outputs

For run-id `run-20260419-184500`:

- `runs/capture-run-20260419-184500.json` — raw responses (no scoring)
- `runs/report-run-20260419-184500.json` — full consolidated report
- `runs/report-run-20260419-184500.md` — human-readable Markdown report

## Workflow

The `persona-diagnostic` workflow in `.replit` runs this single command. It
is **not** part of the default `Project` parallel set — start it manually
when you need a run, so the diagnostic doesn't compete with the dev server
for resources.

## Regenerating the probe sheet

`probes.yaml` is auto-generated from the canonical TypeScript list used by
the Playwright capture. To refresh it after editing `probes.ts`:

```bash
node lia-agent-system/eval/persona-diagnostic/runner/regenerate_probes.mjs
```

## Out of scope

- Fixing the behaviours that fail (covered by separate tasks).
- UI changes.
- Mandatory CI integration (the workflow is opt-in).
- Any prompt or system-prompt edits.
