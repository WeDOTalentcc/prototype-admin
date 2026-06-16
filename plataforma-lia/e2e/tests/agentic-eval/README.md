# Agentic Eval — Playwright runner

Driver for the agentic eval roteiro defined in
`docs/eval/AGENTIC_EVAL_FRAMEWORK.md`.

## What this does

For each YAML scenario in `lia-agent-system/eval/agentic_cases/`:

1. Logs in via the shared `authenticatedPage` fixture from
   `plataforma-lia/e2e/fixtures/auth.fixture.ts` — same auth path used
   by the rest of the e2e suite. The runner does not inject cookies
   itself.
2. Calls `openChatOnPage(page, scope, pagePath)` to navigate to the
   `pageContext` declared in the scenario and surface the LIA chat.
3. Boots a Python user-simulator subprocess
   (`lia-agent-system/eval/agentic/user_simulator.py`) and feeds it
   LIA's replies.
4. Intercepts every `POST /api/v1/chat` and every backend tool call to
   build the `observed_tools` list.
5. Persists a `runs/agentic-<TS>.json` capture file with the full
   transcript per scenario.

The judge (`judge_agentic.py`) and report (`eval_report_agentic.py`)
consume that capture downstream — they are not invoked here so this
runner stays free of API keys.

## Running

See [`docs/eval/AGENTIC_EVAL_PLAYBOOK.md`](../../../../docs/eval/AGENTIC_EVAL_PLAYBOOK.md).

## Files

- `agentic.config.ts` — Playwright config, single worker, longer timeouts.
- `agentic-eval.spec.ts` — the runner.
- `agentic-helpers.ts` — chat helpers + capture helpers.

## Tags

Each scenario gets tagged via `test.describe`:

- `@d1`–`@d10` — dimension (lowercase, matches the YAML `tags:` field)
- `@critical`, `@high`, `@medium`, `@low` — severity
- `@smoke` — subset that runs in CI fast lane
- `@passk` — replay candidates for D9
