"""
TDD — ADR-001 digital_twin domain.py.

Verifica que domain.py NÃO contém sql_text/sa_select inline
e que as queries passam pelo DigitalTwinRepository canonical.
"""
import inspect
import pytest


def test_domain_has_no_sql_inline():
    """domain.py não deve ter sql_text nem sa_select diretos (ADR-001)."""
    from app.domains.digital_twin import domain as dt_domain
    src = inspect.getsource(dt_domain)
    assert "sql_text" not in src, "sql_text inline encontrado em digital_twin/domain.py"
    assert "sa_select" not in src, "sa_select inline encontrado em digital_twin/domain.py"
    assert "from sqlalchemy import select" not in src, (
        "select() inline encontrado — usar DigitalTwinRepository.list_by_company"
    )


def test_domain_uses_digital_twin_repository():
    """domain.py usa DigitalTwinRepository para queries de DigitalTwin."""
    from app.domains.digital_twin import domain as dt_domain
    src = inspect.getsource(dt_domain)
    assert "DigitalTwinRepository" in src, (
        "DigitalTwinRepository não encontrado — queries de DigitalTwin devem passar pelo repositório"
    )


def test_domain_uses_candidate_repository_for_candidate_lookup():
    """domain.py usa CandidateRepository para lookup de candidato (não sql_text inline)."""
    from app.domains.digital_twin import domain as dt_domain
    src = inspect.getsource(dt_domain)
    assert "CandidateRepository" in src, (
        "CandidateRepository ausente — candidate lookup deve usar o repositório canonical"
    )


def test_domain_uses_job_vacancy_repo_for_job_lookup():
    """domain.py usa JobVacancyCRUDRepository para lookup de vaga (não sql_text direto)."""
    from app.domains.digital_twin import domain as dt_domain
    src = inspect.getsource(dt_domain)
    assert "JobVacancyCRUDRepository" in src, (
        "JobVacancyCRUDRepository ausente — job lookup deve usar o repositório canonical"
    )
