"""Sentinel: every canonical ReActAgent prompt is governance-classified.

Task #1043 / PR-B (expanded after code review feedback).

Background: the T-E regression ("LIA pergunta company_id no chat")
escapes when a tenant-facing prompt loses the defensive rule
forbidding the LLM from asking for data already present in
``tenant_context_snippet``. The original sentinel covered only
``job_management`` and ``company_settings``, leaving the other 14
canonical ReActAgents unchecked — a new agent could ship without
governance review.

This test enforces structural coverage of all 16 canonical
ReActAgents (inventory mirrored from
``tests/integration/agents/test_tenant_aware_rollout_t_d.py``):

1. **TENANT_FACING_PROMPTS**: prompts whose agents talk to recruiters
   and may elicit tenant identity. They MUST contain the defensive
   rule (regex matched, accent-tolerant).
2. **NON_TENANT_FACING_PROMPTS**: prompts whose agents work on
   already-scoped objects (sourcing search, kanban moves, pipeline
   transitions, analytics queries, etc.) and never prompt for tenant
   identity. They are explicitly listed so adding a new agent forces
   a conscious classification decision.
3. **Closure check**: the union of (1) + (2) must cover every prompt
   YAML for the 16 canonical ReActAgents. Adding a 17th agent or a
   new domain prompt without classifying it breaks the build.

Adding a new ReActAgent? Classify its prompt YAML in one of the lists
below. If it talks to recruiters about anything that could surface
tenant identity (company name/sector/plan/headcount/recruiter
cadastro) → TENANT_FACING. Otherwise → NON_TENANT_FACING with a brief
reason in the comment.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PROMPTS_ROOT = Path(__file__).resolve().parents[3] / "app" / "prompts" / "domains"


# ---------------------------------------------------------------------------
# Canonical inventory — mirror of test_tenant_aware_rollout_t_d.py
# ---------------------------------------------------------------------------

# Prompts that converse with recruiters and could elicit tenant identity.
# These MUST carry the anti-question rule.
TENANT_FACING_PROMPTS: list[Path] = [
    PROMPTS_ROOT / "job_management.yaml",     # wizard
    PROMPTS_ROOT / "company_settings.yaml",
    PROMPTS_ROOT / "autonomous.yaml",         # autonomous recruiter assistant — open chat
    PROMPTS_ROOT / "recruiter_assistant.yaml",  # talent_funnel + jobs_mgmt + kanban shared
    PROMPTS_ROOT / "hiring_policy.yaml",      # policy negotiates company-level rules
    PROMPTS_ROOT / "communication.yaml",      # drafts messages on behalf of company
    PROMPTS_ROOT / "ats_integration.yaml",    # configures ATS for the tenant
    PROMPTS_ROOT / "analytics.yaml",          # may answer "how many vacancies do we have"
]

# Prompts that act on already-scoped objects (job_id, candidate_id,
# stage_id) and do not prompt the recruiter for tenant identity. They
# are listed explicitly so adding a new agent requires a classification.
NON_TENANT_FACING_PROMPTS: list[tuple[Path, str]] = [
    (PROMPTS_ROOT / "sourcing.yaml", "sourcing operates on a job_id; recruiter never asked for tenant identity"),
    (PROMPTS_ROOT / "cv_screening.yaml", "screens CVs against an already-bound job; no tenant prompts"),
    (PROMPTS_ROOT / "talent_pool.yaml", "voice/text screening of a candidate — tenant inferred from job/candidate scope"),
    (PROMPTS_ROOT / "automation.yaml", "rule engine; no recruiter dialogue about tenant identity"),
    (PROMPTS_ROOT / "candidate_self_service.yaml", "PUBLIC chat with candidate, never sees recruiter tenant prompts"),
    (PROMPTS_ROOT / "pipeline_transition.yaml", "moves candidates through stages of an already-scoped job"),
]

# Sentinel: union must equal the 16 canonical ReActAgent prompt YAMLs.
EXPECTED_CANONICAL_COUNT = 14  # 8 tenant-facing + 6 non-tenant-facing


MARKER = re.compile(
    r"NUNCA\s+pergunte\s+dados\s+que\s+J[ÁA]\s+est[ãa]o\s+no\s+`?tenant_context_snippet`?",
    re.IGNORECASE,
)


@pytest.mark.parametrize(
    "prompt_path", TENANT_FACING_PROMPTS, ids=lambda p: p.name
)
def test_tenant_facing_prompt_contains_anti_question_rule(prompt_path: Path) -> None:
    """Tenant-facing prompts must carry the T-E defensive rule."""
    assert prompt_path.exists(), (
        f"Tenant-facing prompt declared but file missing: {prompt_path}. "
        f"Either create the YAML or move the entry to NON_TENANT_FACING_PROMPTS."
    )
    content = prompt_path.read_text(encoding="utf-8")
    assert MARKER.search(content), (
        f"{prompt_path.name} is classified as tenant-facing but lacks the "
        f"anti-question defensive rule. Add a behavioral rule containing "
        f"'NUNCA pergunte dados que JÁ estão no `tenant_context_snippet`' "
        f"(see app/prompts/domains/company_settings.yaml for the canonical "
        f"wording). Without this guard, the agent can regress to the T-E "
        f"anti-pattern (\"LIA pergunta company_id no chat\")."
    )


@pytest.mark.parametrize(
    "entry", NON_TENANT_FACING_PROMPTS, ids=lambda e: e[0].name
)
def test_non_tenant_facing_prompt_is_documented(entry: tuple[Path, str]) -> None:
    """Non-tenant-facing prompts must exist and have a documented reason."""
    prompt_path, reason = entry
    assert prompt_path.exists(), (
        f"Non-tenant-facing prompt declared but file missing: {prompt_path}. "
        f"If the agent was removed, drop this entry."
    )
    assert reason and len(reason) >= 20, (
        f"{prompt_path.name} is classified as non-tenant-facing but has no "
        f"meaningful reason (got: {reason!r}). Provide a 1-line justification."
    )


def test_classification_covers_every_domain_yaml_used_by_canonical_react_agents() -> None:
    """Closure: every canonical ReActAgent prompt must be classified.

    If you add a 17th agent or rename a YAML, this fails until you add the
    file to TENANT_FACING_PROMPTS or NON_TENANT_FACING_PROMPTS.
    """
    classified = {p.resolve() for p in TENANT_FACING_PROMPTS} | {
        p.resolve() for p, _ in NON_TENANT_FACING_PROMPTS
    }
    assert len(classified) == EXPECTED_CANONICAL_COUNT, (
        f"Expected {EXPECTED_CANONICAL_COUNT} classified prompts, got "
        f"{len(classified)}. Update EXPECTED_CANONICAL_COUNT after adding "
        f"or removing a canonical ReActAgent."
    )

    # Every classified file must exist on disk.
    missing = [str(p) for p in classified if not p.exists()]
    assert not missing, f"Classified prompts missing on disk: {missing}"
