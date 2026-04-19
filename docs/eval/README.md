# LIA Eval — How to run the diagnostic battery

> For the _what_ and _why_ of each dimension see
> [`AGENTIC_EVAL_FRAMEWORK.md`](./AGENTIC_EVAL_FRAMEWORK.md).
> For stage-by-stage operational notes see
> [`AGENTIC_EVAL_PLAYBOOK.md`](./AGENTIC_EVAL_PLAYBOOK.md).

## One-command run

```bash
cd plataforma-lia
npm run diagnostic
```

The battery runs these stages in order and produces a consolidated HTML
report at `plataforma-lia/playwright-report/diagnostic/index.html`:

```
preflight → smoke → critical → agentic (D1–D10) → pass^k (D9) → persona → golden
```

## Prerequisites

| What | How to set it up |
|------|-----------------|
| Backend running | Restart the `lia-backend` workflow |
| Frontend running | Restart the `dev-server` workflow |
| Demo tenant seeded | `python lia-agent-system/app/db/seed.py --tenant demo` |
| Seed recruiter + vaga V0037 | `python lia-agent-system/app/db/seed.py --jobs` |
| `ANTHROPIC_API_KEY` | Set in Replit Secrets |
| `LIA_TEST_TOKEN` | JWT for the seed recruiter — required for PF-02–PF-04 |
| `LIA_E2E_COOKIE` | Browser cookie value (defaults to `e2e-test-token` for local dev) |

Generate `LIA_TEST_TOKEN`:
```bash
python lia-agent-system/eval/eval_runner.py --print-token
# or: python -c "from lia_agent_system.eval.eval_runner import _make_eval_token; print(_make_eval_token())"
```

If pre-flight fails it prints an **actionable error** and stops — you will
never silently get an empty result.

## Filtering by stage, dimension or tag

```bash
# Fastest check — pre-flight + smoke only (~2 min)
npm run diagnostic -- --stage smoke

# Only critical scenarios (~10 min)
npm run diagnostic -- --stage critical

# Only one dimension
npm run diagnostic -- --grep @d4

# Stop on the first failure
npm run diagnostic -- --bail

# Custom k for pass^k
npm run diagnostic -- --k 3

# Skip Python stages (golden + persona) — useful when Python env is unavailable
npm run diagnostic -- --no-python
```

## Reading the report

Open `plataforma-lia/playwright-report/diagnostic/index.html` in any browser.

- **Top stripe** — release decision: ✅ SHIP / ⚠ SHIP WITH NOTE / 🚫 BLOCK.
- **Dimension scorecard** — D1–D10 with score 0–3, pass rate, and pass^k.
- **Findings table** — all critical/high failures sorted by severity × dimension.
  Each row links to an evidence file (trace JSON, Playwright artifact, etc.).
- **Stage summary** — pass/fail for each stage of the battery.

A priorised Markdown copy lands at
`docs/eval/reports/diagnostic-{timestamp}.md` after every run.

## How `pass^k` works (D9)

D9 is not a new scenario — it replays every scenario tagged `@passk` a
total of **k** times (default: 5, configurable via `--k` or `AGENTIC_PASS_K`).

A scenario _passes_ D9 only if it scores ≥ 2 on **every** run. The D9
score is the minimum score across all k runs:

- **3** — all k runs scored 3
- **2** — all k runs scored ≥ 2
- **1** — at least one run scored 1
- **0** — at least one run scored 0

This is the τ-bench `pass^k` metric adapted for LIA.

## How to add a scenario

> **Rule: YAML is the single source of truth. Never duplicate a scenario in TypeScript.**

1. Pick the right file in `lia-agent-system/eval/agentic_cases/`:
   - `d1-memory.yaml`, `d2-self-knowledge.yaml`, … `d10-proactive.yaml`
   - `d99-mixed.yaml` for cross-cutting scenarios
2. Add a new entry to the `scenarios:` array following the schema in
   `lia-agent-system/eval/agentic_cases/README.md`.
3. Tag it with the correct dimension (`d1`…`d10`), severity, and optionally
   `smoke` and/or `passk`.
4. Bump `meta.version` at the top of the YAML file.
5. Run `npm run diagnostic -- --grep @d4` (or whichever dimension) to verify
   the new scenario is picked up.

The Playwright driver (`e2e/tests/agentic-eval/agentic-eval.spec.ts`) loads
all YAML files dynamically — no code changes needed.

## Troubleshooting pre-flight

| Error | Fix |
|-------|-----|
| `PF-01` Backend unreachable | Start `lia-backend` workflow |
| `PF-02` Demo tenant not found | Run `python lia-agent-system/app/db/seed.py --tenant demo` |
| `PF-03` Token rejected (401/403) | The server's `SECRET_KEY` may have rotated. Set `LIA_TEST_TOKEN` |
| `PF-04` V0037 not found | Run `python lia-agent-system/app/db/seed.py --jobs` |
| `PF-05` No LLM API key | Set `ANTHROPIC_API_KEY` in Replit Secrets |
| `PF-06` Frontend unreachable | Start `dev-server` workflow |

## Report directory layout

```
plataforma-lia/playwright-report/diagnostic/
├── index.html                  ← consolidated HTML report
├── smoke-results.json          ← smoke Playwright JSON output
├── proposed-tasks.json         ← auto-generated task list (critical+high)
└── artifacts/                  ← traces, screenshots, videos

docs/eval/reports/
└── diagnostic-{timestamp}.md   ← prioritised Markdown for human review

lia-agent-system/eval/agentic/runs/
├── agentic-{timestamp}.json           ← agentic raw captures
└── agentic-{timestamp}-passk.json     ← pass^k captures
```
