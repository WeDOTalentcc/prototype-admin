# Agentic Eval Playbook — How to run the suite

> This is the operational guide. For the *what* and the *why* see
> [`AGENTIC_EVAL_FRAMEWORK.md`](./AGENTIC_EVAL_FRAMEWORK.md).
> For a complete guide to the **unified diagnostic battery** (the recommended
> way to run everything at once) see [`README.md`](./README.md).

## TL;DR — Unified battery (recommended)

```bash
# Full battery: preflight → smoke → critical → agentic D1-D10 → pass^k → persona → golden
cd plataforma-lia && npm run diagnostic

# Quick smoke only (~2 min)
cd plataforma-lia && npm run diagnostic:smoke

# One dimension
cd plataforma-lia && npm run diagnostic -- --grep @d4

# Custom k
cd plataforma-lia && npm run diagnostic -- --k 3
```

Report lands at `plataforma-lia/playwright-report/diagnostic/index.html`.

## TL;DR — Agentic-only run (manual)

```bash
# 1. start backend + frontend in dev (workflows already configured)
# 2. smoke run (~10 minutes, only critical scenarios)
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  npx playwright test \
  --config plataforma-lia/e2e/tests/agentic-eval/agentic.config.ts \
  --grep @smoke

# 3. full run (~60 minutes, all 66 scenarios; pass^k=5 on @passk by default)
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  npx playwright test \
  --config plataforma-lia/e2e/tests/agentic-eval/agentic.config.ts

# 4. judge + report
python lia-agent-system/eval/agentic/judge_agentic.py \
  lia-agent-system/eval/agentic/runs/agentic-<TS>.json
python lia-agent-system/eval/agentic/eval_report_agentic.py \
  lia-agent-system/eval/agentic/runs/agentic-<TS>_judged.json
open lia-agent-system/eval/agentic/runs/agentic_report_<TS>.html
```

## Pre-requisites

| Item | Source | Notes |
|------|--------|-------|
| Backend running | `lia-backend` workflow | Auto-generated demo JWT requires the backend `SECRET_KEY` |
| Frontend running | `dev-server` workflow | Playwright targets `PLAYWRIGHT_BASE_URL` (default `http://localhost:5000`) |
| `ANTHROPIC_API_KEY` env | Replit Secret | Used by the user-simulator and the judge |
| Demo tenant seeded | `00000000-0000-4000-a000-000000000001` | The roteiro assumes this tenant exists with V0037 vaga |
| Playwright browser | `apt-get install chromium` *or* `npx playwright install chromium` | The config auto-detects system chromium |

## Filters

| Goal | Command |
|------|---------|
| One dimension | `--grep @d4` (lowercase tags `@d1`–`@d10`, matching the YAML `tags:` field) |
| One severity | `--grep @critical` |
| One scenario | `--grep AGT-D04-001` |
| Skip D9 (`pass^k`) | `--grep-invert @passk` (the pass^k replay loop is the slowest part of the run) |
| Custom k for D9 | `AGENTIC_PASS_K=3 npx playwright test ...` |

## Reading the report

The HTML lands at `lia-agent-system/eval/agentic/runs/agentic_report_<TS>.html`.
Open in a browser. Three areas matter:

1. **Top stripe — release decision.** Green = ship; orange = ship-with-note;
   red = block. Mirrors the matrix in `AGENTIC_EVAL_FRAMEWORK.md` § *Score
   → release decision*.
2. **Per-dimension scorecard.** D1–D10 with average score, pass rate, and
   delta vs. previous run. Click a dimension to filter the scenario table.
3. **Tool-call diff.** For each scenario, expected tool list vs. observed
   tool list, intersected with the network capture from `/api/v1/chat`.

Click any failed scenario to expand:

- The full conversation transcript (user-simulator + LIA + tool calls).
- The judge's per-dimension JSON (score, reasoning, anti-patterns hit).
- The deterministic checks that ran *before* the judge (regex-based).
- Links to the canonical files most likely to need a fix.

## Failure triage flow

When a scenario fails, the playbook is:

1. **Reproduce manually.** Open `/pt/chat`, log in as the demo recruiter,
   replay the conversation by hand. If it now passes, it's a flake — bump
   the `pass^k` (D9) for that scenario in the next run before opening an
   issue.
2. **Categorise.** Use the dimension that scored 0/1 to pick the
   right canonical file:
   - D1, D4 → `app/orchestrator/orchestrator.py`,
     `app/shared/state/conversation_state.py`
   - D2 → `app/shared/prompts/system_prompt_builder.py`,
     `app/shared/prompts/agent_prompts.py`,
     `app/tools/tool_registry_metadata.yaml`
   - D3, D10 → `app/shared/prompts/system_prompt_builder.py`,
     `agentic/platform_ground_truth.yaml`
   - D5 → `app/shared/prompts/system_prompt_builder.py`
   - D6 → individual tool implementation under `app/domains/.../tools/`
   - D7 → `app/shared/security/pii_masker.py`,
     `app/shared/fairness/fairness_guard.py`
   - D8 → `app/shared/prompts/system_prompt_builder.py`,
     `app/shared/safety/refusal_policies.py`
   - D9 → usually a temperature / sampling drift; root cause sits in
     whichever component was scored on the underlying dimension
3. **Open one issue per dimension.** Title format:
   `[Agentic Eval][Dn] <scenario id> — <one-line failure>`. Body includes
   the run ID, the scenario YAML path, the judge JSON, and the canonical
   files. Link the issue back to the run report.
4. **Re-run only that scenario** with `--grep <id>` after the fix to keep
   the loop fast.

## When to update the golden

The golden lives in `lia-agent-system/eval/agentic_cases/`. Update it
when:

- A new feature ships → add a scenario in the relevant dimension.
- A failure mode is observed in production that no scenario catches → add
  the scenario *first*, then fix.
- The platform changes a screen name, status, or pipeline stage → update
  `agentic/platform_ground_truth.yaml` first; the D3/D10 scenarios will
  pick up the new ground truth automatically.

When you change a YAML, bump the `meta.version` in the file. The judge
uses the version to invalidate cached results from prior runs.

## Costs and timing

| Mode  | Scenarios | Wall time | Anthropic cost |
|-------|-----------|-----------|----------------|
| Smoke | ~12       | 10 min    | ~$0.40         |
| Full  | 66        | 60 min    | ~$2.50         |
| Full + D9 (k=5) | 66 + 13 × 4 | 90 min | ~$4.50 |

These are estimates with `claude-haiku-4-5` as both user-simulator and
judge. Switching the simulator to `claude-sonnet-4-6` increases realism
but ~3× the cost.

## Limitations

- The user-simulator does not click on the UI — it only types into the
  chat. UI click flows are still covered by `e2e/tests/lia-capabilities/`.
- D10 *consent* sub-criterion is judged by the LLM, not deterministically
  enforced. If this becomes a release blocker we can layer a regex check
  for explicit "posso prosseguir?" / "tudo bem se eu fizer X?".
- The runner re-uses one Playwright browser context per scenario for
  isolation; this means it does not catch cross-conversation leaks. Those
  are covered by `e2e/tests/chat/conversation-memory.spec.ts`.
