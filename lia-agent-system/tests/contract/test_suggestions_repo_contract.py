"""
Contract sensor — /lia/suggestions canonical repos (P1-6 Fase B).

WHY THIS SENSOR EXISTS
======================
Fase B P1-6 (2026-05-23) refatorou ``app/api/v1/lia_assistant/suggestions.py``
de 2 SQL inline (viola ADR-001) pra usar repos canonical:

  - JobVacancyCRUDRepository.list_active_for_company(company_id)
  - VacancyCandidateRepository.count_created_since(company_id, since_dt)

Esse sensor garante:
1. Methods canonical existem nos repos (anti-regression refactor)
2. suggestions.py NÃO contém os tokens de SQL inline removidos
3. suggestions.py importa os 2 repos canonical

Pattern: BLOCKING. Anti-regressão.
"""
from __future__ import annotations

import inspect
from pathlib import Path


def _suggestions_source() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "app" / "api" / "v1" / "lia_assistant" / "suggestions.py"
    return src.read_text()


def test_list_active_for_company_exists_in_repo():
    """``JobVacancyCRUDRepository.list_active_for_company`` deve existir."""
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )
    assert hasattr(JobVacancyCRUDRepository, "list_active_for_company"), (
        "list_active_for_company ausente em JobVacancyCRUDRepository. "
        "P1-6 (Fase B) introduziu esse método como canonical pra ``/lia/suggestions``. "
        "Restaurar ou suggestions.py vai cair em fallback exception."
    )
    method = JobVacancyCRUDRepository.list_active_for_company
    assert inspect.iscoroutinefunction(method), (
        "list_active_for_company deve ser async (coroutine function)."
    )


def test_count_created_since_exists_in_repo():
    """``VacancyCandidateRepository.count_created_since`` deve existir."""
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )
    assert hasattr(VacancyCandidateRepository, "count_created_since"), (
        "count_created_since ausente em VacancyCandidateRepository. "
        "P1-6 (Fase B) introduziu como canonical pra ``/lia/suggestions``. "
        "Restaurar ou suggestions.py cai em fallback exception."
    )
    method = VacancyCandidateRepository.count_created_since
    assert inspect.iscoroutinefunction(method), (
        "count_created_since deve ser async (coroutine function)."
    )


def test_suggestions_endpoint_uses_repos_not_inline_sql():
    """suggestions.py NÃO deve conter SQL inline (ADR-001)."""
    src = _suggestions_source()

    # Markers de SQL inline removido (P1-6)
    forbidden_patterns = [
        "select(JobVacancy)",
        "select(func.count(VacancyCandidate",
    ]
    found = [p for p in forbidden_patterns if p in src]
    assert not found, (
        f"suggestions.py contém SQL inline (ADR-001 violation): {found}\n"
        "Usar JobVacancyCRUDRepository.list_active_for_company / "
        "VacancyCandidateRepository.count_created_since em vez."
    )


def test_suggestions_endpoint_imports_canonical_repos():
    """suggestions.py deve importar os 2 repos canonical."""
    src = _suggestions_source()

    required_imports = [
        "JobVacancyCRUDRepository",
        "VacancyCandidateRepository",
        "require_company_id",
    ]
    missing = [imp for imp in required_imports if imp not in src]
    assert not missing, (
        f"suggestions.py NÃO importa canonical: {missing}\n"
        "P1-6 (Fase B) requer todos 3 imports."
    )


def test_suggestions_endpoint_uses_require_company_id_canonical():
    """company_id deve vir de Depends(require_company_id), NUNCA payload."""
    src = _suggestions_source()
    assert "Depends(require_company_id)" in src, (
        "suggestions.py não usa require_company_id canonical. "
        "Multi-tenancy fail-closed: company_id SEMPRE vem do JWT."
    )
    # Confirmar que NÃO há mais overwrite `company_id = current_user.company_id`
    assert "company_id = current_user.company_id" not in src, (
        "suggestions.py ainda overwrite company_id com current_user.company_id. "
        "P1-6 removeu — JWT é fonte autoritativa unica (defense-in-depth)."
    )
