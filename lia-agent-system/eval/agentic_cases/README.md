# Agentic eval scenarios

Multi-turn YAML scenarios consumed by the Playwright runner under
`plataforma-lia/e2e/tests/agentic-eval/`. See
[`docs/eval/AGENTIC_EVAL_FRAMEWORK.md`](../../../docs/eval/AGENTIC_EVAL_FRAMEWORK.md)
for the rubric and
[`docs/eval/AGENTIC_EVAL_PLAYBOOK.md`](../../../docs/eval/AGENTIC_EVAL_PLAYBOOK.md)
for how to run.

## File naming

```
d{N}-{slug}.yaml      # one file per dimension; multiple scenarios per file
```

Each file contains a top-level `scenarios:` array. Scenarios are scored
independently. Tag every scenario with the dimension(s) it primarily
exercises (`d1`, `d4`, `d10`…) plus a severity (`critical`, `high`,
`medium`, `low`) and optionally `smoke` and `passk`.

## Scenario schema

```yaml
- id: AGT-D04-001
  meta: { version: "1.0.0" }
  tags: [d4, critical, smoke, passk]
  severity: critical                      # critical | high | medium | low
  goal: "Recruiter wants to add 3 candidates from sourcing and start WSI."

  # Setup the test environment must satisfy. The runner does NOT mutate
  # the platform; setup_notes documents the assumption so the operator
  # can seed it. `setup` is the structured form for future automation.
  setup_notes: "Vaga V0037 must exist with screening questions configured."
  setup:
    company_settings: filled
    integrations: { whatsapp: on }
    jobs:
      - id: V0037
        status: publicada
        screening_questions: 3

  # camelCase `pageContext` is the canonical form (matches the frontend
  # ChatContext payload). `page_context` (snake_case) is accepted as a
  # legacy alias and normalised by the runner.
  pageContext: { scope: "sourcing", page: "sourcing" }

  persona:
    role: "recruiter"
    language: "pt-BR"
    consent_policy: "always_yes"   # always_yes | always_no | ask_what_will_happen_first

  turns:
    - user: "Busca candidatos com Python para a vaga V0037."
    - user: "Adiciona os 3 melhores ao pipeline."
    - user: "Dispara triagem para eles."

  facts_you_know:
    job_id: "V0037"
    job_title: "Engenheira(o) de dados sênior"
  facts_you_do_not_know:
    - "candidate_ids — wait for LIA to surface them"

  # Tool calls the LIA backend should emit, in any order. Deterministic
  # pre-check by the judge.
  expected_tools:
    - search_candidates
    - add_candidate
    - start_wsi_screening

  # Verifiable post-conditions. Each entry is { check: <type>, ... }.
  # The judge applies these as deterministic pre-checks before LLM
  # scoring. Supported `check` values:
  #   - tool_called: tool name is present in observed_tools
  #   - tool_not_called: tool name is absent
  #   - response_contains: response text matches a substring (case-insensitive)
  #   - response_not_contains: response text must NOT match
  #   - language_pt: response detected as PT-BR
  expected_state_after:
    - { check: tool_called, name: start_wsi_screening }
    - { check: response_contains, text: "triagem" }
    - { check: language_pt }

  expected_proactive_actions: []

  # Optional per-scenario rubric override. If absent, the dimension's
  # default rubric from AGENTIC_EVAL_FRAMEWORK.md applies.
  judge_rubric: |
    Score 3 only if all three tools fired AND LIA confirmed completion
    naming the 3 candidate names from step 1.

  stop_when: "LIA confirma que a triagem foi disparada para 3 candidatos."
```

`turns` is a *script*, not a hard constraint — the user-simulator may
improvise within scenario rules if LIA pushes for clarification.

The runner normalises `page_context` → `pageContext` and treats
`setup_notes` as the human-readable form of `setup`. Older scenario
files that only use the snake_case keys keep working.

`expected_tools`, `expected_state_after` and `expected_proactive_actions`
drive deterministic checks **before** the LLM judge runs. The judge is
informed of which deterministic checks failed and weighs them in the
final score.
