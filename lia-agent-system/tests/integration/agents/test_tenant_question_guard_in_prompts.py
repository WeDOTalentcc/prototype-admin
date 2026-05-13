"""Sentinel: prompts at risk of asking tenant data must carry the
defensive rule that prevents the T-E regression
("LIA pergunta company_id no chat").

Task #1043 / PR-B.

Scope: prompt YAMLs whose agents talk directly to recruiters and may
elicit tenant identity (company name, sector, plan, headcount, company
id, recruiter identity). Today: ``wizard`` (job_management) and
``company_settings``. Other ReActAgents (sourcing, kanban, pipeline,
analytics, etc.) operate on already-scoped objects and do not prompt
the recruiter for tenant identity, so they are not in scope here.

Adding a new tenant-facing ReActAgent? Append its YAML path to
``TENANT_FACING_PROMPTS`` so the build refuses prompts missing the rule.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PROMPTS_ROOT = Path(__file__).resolve().parents[3] / "app" / "prompts" / "domains"

TENANT_FACING_PROMPTS = [
    PROMPTS_ROOT / "job_management.yaml",
    PROMPTS_ROOT / "company_settings.yaml",
]

# Normalised marker — case-insensitive, accent-tolerant.
MARKER = re.compile(
    r"NUNCA\s+pergunte\s+dados\s+que\s+J[ÁA]\s+est[ãa]o\s+no\s+`?tenant_context_snippet`?",
    re.IGNORECASE,
)


@pytest.mark.parametrize("prompt_path", TENANT_FACING_PROMPTS, ids=lambda p: p.name)
def test_tenant_facing_prompt_contains_anti_question_rule(prompt_path: Path) -> None:
    assert prompt_path.exists(), f"Prompt file missing: {prompt_path}"
    content = prompt_path.read_text(encoding="utf-8")
    assert MARKER.search(content), (
        f"{prompt_path.name} is tenant-facing but lacks the anti-question "
        f"defensive rule. Add a behavioral rule containing "
        f"'NUNCA pergunte dados que JÁ estão no `tenant_context_snippet`' "
        f"to prevent regression of T-E ('LIA pergunta company_id no chat'). "
        f"See app/prompts/domains/company_settings.yaml for the canonical wording."
    )
