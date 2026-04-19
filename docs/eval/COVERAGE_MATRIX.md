# Coverage Matrix — existing tests vs. D1–D10

> Generated as Step 1 of task #563. Maps every existing test file to the
> dimension(s) it already covers, what to reuse, what to extend, and what
> to build from scratch under `lia-agent-system/eval/agentic_cases/`.

Legend:
- ✅ already covers the dimension well → reuse as-is.
- 🟡 partial coverage → extend with the new multi-turn shape, but keep
  the existing assertions.
- ❌ no coverage → must be built fresh in `agentic_cases/`.

## Per-dimension audit

### D1 — Conversational memory

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/tests/test_reference_resolver.py` | ✅ unit-level pronoun resolution | Reuse — runs at unit level, complementary to e2e |
| `lia-agent-system/tests/test_context_compression.py` | ✅ window compression | Reuse |
| `plataforma-lia/e2e/tests/chat/conversation-memory.spec.ts` | 🟡 single-page memory | Extend with cross-page memory in `agentic_cases/d1-*.yaml` |
| `plataforma-lia/e2e/tests/lia-capability-eval/multi-turn-context.spec.ts` | 🟡 hard-coded turns | Extend with simulator-driven follow-ups |

**To build:** 7 scenarios `d1-memory-*.yaml` covering ID reuse, pronoun
chains, decision recall, and cross-turn entity resolution.

### D2 — Self-knowledge

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/tests/test_prompt_tool_parity.py` | ✅ system prompt vs. tool registry parity | Reuse |
| `plataforma-lia/e2e/tests/persona-diagnostic/probes.ts` (CAP-*) | 🟡 8 single-shot capability probes | Extend with negative probes ("você consegue X?" where X is fake) |

**To build:** 6 scenarios `d2-self-*.yaml` covering scope-correct vs.
scope-leaky descriptions across LIA/JOB/SRC/CVS/INT/WSI.

### D3 — Platform grounding

| File | Coverage | Action |
|------|----------|--------|
| (none) | ❌ no test asserts LIA names the right screen/menu/field | Build from scratch |

**To build:** 7 scenarios `d3-grounding-*.yaml` driven from
`agentic/platform_ground_truth.yaml`.

### D4 — Multi-step planning

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/tests/test_react_loop.py` | 🟡 ReAct loop unit tests | Reuse for unit; extend e2e |
| `lia-agent-system/tests/test_agent_comprehensive.py` | 🟡 cross-domain XD scenarios | Reuse |
| `lia-agent-system/tests/golden_dataset.py` (XD001-005) | 🟡 5 cross-domain prompts | Reuse, but they are one-shot — extend to multi-turn |

**To build:** 7 scenarios `d4-planning-*.yaml` with ≥3 tool calls each
and intermediate state validation.

### D5 — Smart clarification

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/eval/eval_cases.yaml` (anti-patterns) | 🟡 catches "asks for `company_id`" but only after the fact | Extend |

**To build:** 6 scenarios `d5-clarify-*.yaml` with ambiguous prompts and
context that already carries the missing field.

### D6 — Tool-use robustness

| File | Coverage | Action |
|------|----------|--------|
| `plataforma-lia/e2e/tests/lia-capability-eval/resilience-edge-cases.spec.ts` | ✅ failure-injection | Reuse |
| `lia-agent-system/tests/test_agent_regression.py` | 🟡 some empty-result regressions | Reuse |

**To build:** 6 scenarios `d6-robust-*.yaml` with fixtures that force
empty/error/timeout/invalid-filter responses.

### D7 — Disambiguation & sensitive data

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/tests/fairness/test_red_teaming.py` | ✅ PII masking probes | Reuse |
| `lia-agent-system/tests/ragas/` | 🟡 faithfulness; not specifically PII | Extend |

**To build:** 6 scenarios `d7-sensitive-*.yaml` with seeded duplicate
candidates and masked-PII echo probes.

### D8 — Refusal & scope

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/eval/persona-diagnostic/` | ✅ 120 probes across A–J | **Reuse verbatim** — D8 inherits the persona rubric |
| `plataforma-lia/e2e/tests/lia-capability-eval/prompt-injection-security.spec.ts` | ✅ jailbreak probes | Reuse |

**To build:** 0. D8 = persona-diagnostic. The agentic runner just calls
the persona-diagnostic judge for any scenario tagged `@d8`.

### D9 — Consistency (`pass^k`)

| File | Coverage | Action |
|------|----------|--------|
| (none) | ❌ no existing test re-runs the same scenario k times | Build framework hook |

**To build:** No new scenarios. The runner replays a curated subset
(critical scenarios across D1, D4, D6, D8, D10) k=5 times. Failure of
any single run drops the D9 score.

### D10 — Contextual proactive assistance *(new)*

| File | Coverage | Action |
|------|----------|--------|
| `lia-agent-system/tests/test_phase3_proactivity.py` | 🟡 proactive *suggestions* (alerts) but not gap-detection + nav | Reuse |

**To build:** 8 scenarios `d10-proactive-*.yaml` with `setup` blocks
that null `company.settings`, remove screening questions, leave a vaga
without policy, etc.

## Summary

| Action | Count |
|--------|-------|
| Reuse as-is | 7 files |
| Extend       | 8 files |
| Build fresh  | ~70 scenarios across 9 dimensions (D8 reuses persona) |

Total new YAML scenarios in `agentic_cases/`: **66** (D1: 7, D2: 6,
D3: 7, D4: 7, D5: 6, D6: 6, D7: 6, D8: 6 short-form scenarios that
delegate to the persona-diagnostic judge, D10: 8, plus the catch-all
`d99-mixed.yaml` with 7 cross-cutting scenarios). D9 is computed by
re-running every scenario tagged `@passk` k times — no separate YAML.
Tag casing follows the YAML `tags:` field exactly (lowercase: `@d1`,
`@d2`, …, `@d10`, `@passk`, `@critical`, `@high`, `@smoke`).
