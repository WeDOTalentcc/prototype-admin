"""
TDD: ADR-001 Wave C-2 Agent F — pipeline_tool_registry.py migration.

Verifica:
1. Nenhum SQL inline sem marker ADR-001-EXEMPT em pipeline_tool_registry.py
2. Os 4 repos novos existem no filesystem
3. _require_company_id falha com ValueError para company_id vazio
"""
import asyncio
import importlib
from pathlib import Path

import pytest

REGISTRY_PATH = Path("app/domains/pipeline/agents/pipeline_tool_registry.py")
REPOS_BASE = Path("app/domains/pipeline/repositories")


# ─── 1. No unmarked SQL inline ─────────────────────────────────────────────────

def test_pipeline_registry_no_unmarked_sql():
    """Verifica que todo text() sem EXEMPT marker foi migrado.

    Usa lookback de 50 linhas para cobrir blocos async with multi-query
    onde o EXEMPT marker está no início do bloco (cancel/reschedule_interview).
    """
    content = REGISTRY_PATH.read_text()
    lines = content.split("\n")
    violations = []
    for i, line in enumerate(lines):
        if 'text("""' in line or "text('''" in line:
            # Look back up to 50 lines for EXEMPT marker (covers full async-with block)
            context = "\n".join(lines[max(0, i - 50): i + 1])
            if "ADR-001-EXEMPT" not in context:
                violations.append(f"Line {i+1}: {line.strip()}")
    assert violations == [], "Unmarked SQL inline found:\n" + "\n".join(violations)


# ─── 2. New repositories exist ─────────────────────────────────────────────────

def test_candidate_pipeline_repository_exists():
    assert (REPOS_BASE / "candidate_pipeline_repository.py").exists()


def test_lia_opinion_repository_exists():
    assert (REPOS_BASE / "lia_opinion_repository.py").exists()


def test_stage_repository_exists():
    assert (REPOS_BASE / "stage_repository.py").exists()


def test_recruiter_preferences_repository_exists():
    assert (REPOS_BASE / "recruiter_preferences_repository.py").exists()


# ─── 3. _require_company_id fail-closed ────────────────────────────────────────

@pytest.mark.parametrize("module_name,class_name,method,args", [
    ("candidate_pipeline_repository", "CandidatePipelineRepository", "get_profile", ("some-cid", "")),
    ("candidate_pipeline_repository", "CandidatePipelineRepository", "get_salary_info", ("some-cid", "")),
    ("candidate_pipeline_repository", "CandidatePipelineRepository", "get_phone_by_email", ("test@x.com", "")),
    ("lia_opinion_repository", "LiaOpinionRepository", "get_by_candidate", ("some-cid", "")),
    ("stage_repository", "StageRepository", "get_sub_statuses_for_stage", ("screening", "")),
    ("stage_repository", "StageRepository", "get_default_sub_status", ("screening", "")),
    ("recruiter_preferences_repository", "RecruiterPreferencesRepository", "get_preferences", ("rid", "")),
    ("recruiter_preferences_repository", "RecruiterPreferencesRepository", "upsert_preference", ("rid", "", "pkey", "pval")),
])
def test_repos_require_company_id(module_name, class_name, method, args):
    """Todos os repos devem levantar ValueError quando company_id for vazio."""
    mod = importlib.import_module(f"app.domains.pipeline.repositories.{module_name}")
    cls = getattr(mod, class_name)
    repo = cls(db=None)
    with pytest.raises(ValueError, match="company_id is required"):
        asyncio.run(getattr(repo, method)(*args))


# ─── 4. Imports in registry ────────────────────────────────────────────────────

def test_pipeline_registry_imports_repos():
    """pipeline_tool_registry.py deve importar os 4 repos novos."""
    content = REGISTRY_PATH.read_text()
    assert "CandidatePipelineRepository" in content
    assert "LiaOpinionRepository" in content
    assert "StageRepository" in content
    assert "RecruiterPreferencesRepository" in content


def test_pipeline_registry_uses_repos_not_raw_select():
    """Os 4 blocos migrados devem usar repo.get_* em vez de text() inline."""
    content = REGISTRY_PATH.read_text()
    # Verifica que os wrappers migrados usam o repo
    assert "repo.get_profile" in content
    assert "repo.get_salary_info" in content
    assert "repo.get_by_candidate" in content
    assert "repo.get_sub_statuses_for_stage" in content
    assert "repo.get_default_sub_status" in content
    assert "repo.get_preferences" in content
    assert "repo.upsert_preference" in content
