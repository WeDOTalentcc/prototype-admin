# Agentic Eval Frameworks — Market Reference

> Companion to [`AGENTIC_EVAL_FRAMEWORK.md`](./AGENTIC_EVAL_FRAMEWORK.md).
> Summarises the public agentic-eval frameworks we drew from and maps each
> one to our 10 dimensions (D1–D10) so reviewers can audit what we borrowed
> and what we invented.

## Why these references

The 10 dimensions in `AGENTIC_EVAL_FRAMEWORK.md` are not invented from
scratch. They are an opinionated synthesis of the public state of the art
plus the failure modes we observed in real LIA traces. This document keeps
the receipts.

## τ-bench (Sierra/Anthropic, 2024)

- **What it is.** Multi-turn benchmark with an LLM user-simulator and
  domain tools (retail, airline). Introduces `pass^k` as the metric: a
  task only counts as solved if it solves on every one of k independent
  runs (k=5 by default).
- **What we borrow.** The user-simulator pattern (D1, D4, D10), the
  multi-turn YAML scenario shape, and `pass^k` as our D9.
- **What we don't borrow.** Their domain tools — we use the LIA tool
  registry directly via the production `/api/v1/chat` endpoint.
- **Maps to.** D1, D4, D9.
- **Reference.** Yao et al., 2024 — `arxiv.org/abs/2406.12045`.

## AgentBench (Tsinghua, 2023)

- **What it is.** 8-environment benchmark for agent reasoning across OS,
  DB, KG, web shopping, web browsing, etc. Strong on tool-use failure
  injection (broken APIs, wrong schemas).
- **What we borrow.** The failure-injection methodology that powers D6
  (tool-use robustness). Some D2 self-knowledge probes are inspired by
  AgentBench's "what tools do you have?" sub-tasks.
- **Maps to.** D2, D4, D6.
- **Reference.** Liu et al., 2023 — `arxiv.org/abs/2308.03688`.

## HELM Agentic (Stanford CRFM, 2024)

- **What it is.** Holistic Evaluation of Language Models extended with
  agentic tasks. Strong on the *clarification* sub-task and on
  rubric-based scoring with multiple dimensions.
- **What we borrow.** The 0–3 rubric shape (we use the same scale across
  all dimensions for consistency), and the "ask the minimum" framing for
  D5.
- **Maps to.** D3, D5, D8.
- **Reference.** `crfm.stanford.edu/helm/`.

## RAGAS (2024)

- **What it is.** Reference-free / reference-based metrics for
  retrieval-augmented generation: faithfulness, answer relevancy, context
  precision/recall.
- **What we borrow.** The faithfulness check for D3 (platform grounding):
  a response that names a screen/field is faithful only if that
  screen/field is in `agentic/platform_ground_truth.yaml`.
- **Maps to.** D3, D7.
- **Reference.** `github.com/explodinggradients/ragas`.

## OpenAI Evals (2023+)

- **What it is.** Open framework for prompt-level evals with
  contributed templates ("model-graded", "fact", "matching").
- **What we borrow.** The judge-with-prompt pattern (`eval_judge.py` and
  `persona-diagnostic/runner/judge.py` already use it) and the
  "ask_clarifying_question" eval shape for D5.
- **Maps to.** D2, D5, D8.
- **Reference.** `github.com/openai/evals`.

## NIST AI RMF (Risk Management Framework)

- **What it is.** Government-backed framework for AI risk management.
  Includes "Measure" sub-functions for accuracy, robustness, privacy,
  security and governability.
- **What we borrow.** Three risk axes that map directly to dimensions:
  `Privacy / Sensitive Information Handling` (D7), `Robustness` (D6),
  and `Goal-Conducive Behaviour` (D10 proactive assistance).
- **Maps to.** D6, D7, D10.
- **Reference.** NIST AI 100-1.

## Anthropic Responsible Scaling Policy

- **What it is.** Threshold-based release-blocking evaluations: a model
  cannot ship if any critical capability evaluation fails.
- **What we borrow.** The hard-block matrix at the end of
  `AGENTIC_EVAL_FRAMEWORK.md`. A single critical failure overrides the
  numeric score. This mirrors Anthropic's "no critical eval failures
  before release" stance.
- **Maps to.** Decision matrix; D6, D8, D10.
- **Reference.** `anthropic.com/news/responsible-scaling-policy`.

## SWE-bench (Princeton, 2023)

- **What it is.** GitHub-issue benchmark with multi-seed evaluation.
- **What we borrow.** Multi-seed insistence — a fix that works on one
  seed and breaks on another doesn't ship. This reinforces D9.
- **Maps to.** D9.
- **Reference.** `swebench.com`.

## AppWorld (CMU/Allen AI, 2024)

- **What it is.** Multi-app agentic benchmark with cross-app state
  tracking.
- **What we borrow.** Cross-domain probes for D4 multi-step planning
  ("busca candidato → cria entrevista → manda WhatsApp").
- **Maps to.** D4, D1.
- **Reference.** `appworld.dev`.

## Cross-reference matrix

| Dimension                | τ-bench | AgentBench | HELM | RAGAS | OpenAI Evals | NIST | Anthropic | SWE-bench | AppWorld |
|--------------------------|---------|------------|------|-------|--------------|------|-----------|-----------|----------|
| D1 Memory                | ✓       |            |      |       |              |      |           |           | ✓        |
| D2 Self-knowledge        |         | ✓          |      |       | ✓            |      |           |           |          |
| D3 Grounding             |         |            | ✓    | ✓     |              |      |           |           |          |
| D4 Multi-step planning   | ✓       | ✓          |      |       |              |      |           |           | ✓        |
| D5 Clarification         |         |            | ✓    |       | ✓            |      |           |           |          |
| D6 Tool robustness       |         | ✓          |      |       |              | ✓    | ✓         |           |          |
| D7 Sensitive data        |         |            |      | ✓     |              | ✓    |           |           |          |
| D8 Refusal & scope       |         |            | ✓    |       | ✓            |      | ✓         |           |          |
| D9 Consistency `pass^k`  | ✓       |            |      |       |              |      |           | ✓         |          |
| D10 Proactive assistance |         |            |      |       |              | ✓    | ✓         |           |          |

## Anti-mapping (what we deliberately did **not** borrow)

- **AgentBench LLM-as-environment.** AgentBench wraps an LLM as a fake
  environment for some sub-tasks. We do not — every probe runs through
  the production stack to keep the test honest.
- **τ-bench tool definitions.** We use the LIA registry directly so the
  test surface tracks the product surface.
- **HELM closed datasets.** Our golden lives in `agentic_cases/` and is
  versioned in this repo. No external dependencies.
