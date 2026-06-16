"""Fase B P0.2 (autocorrecao 0-resultados): search_candidates (sourcing/supervisor).

Mesmo padrao do search_jobs: 0-resultados -> sinal estruturado de relaxamento via
build_empty_result_guidance (produtor unico). _format_search_candidates_result e o seam
PURO (testavel sem DB). canonical-fix: reusa o helper, nao reinventa.
"""
from app.domains.sourcing.tools.query_tools import _format_search_candidates_result


def test_empty_returns_relaxation_guidance():
    r = _format_search_candidates_result([], {"seniority": "Senior", "skills": ["python"], "status": None})
    assert r["success"] is True
    d = r["data"]
    assert d["total"] == 0
    assert d.get("empty") is True
    assert d.get("relaxation_suggestions"), "deve sugerir relaxar filtros"
    assert "seniority" in d.get("applied_filters", {})
    assert "status" not in d.get("applied_filters", {})  # None nao entra


def test_nonempty_returns_normal_no_guidance():
    cands = [{"id": "1", "name": "Ana"}]
    r = _format_search_candidates_result(cands, {"status": "active"})
    assert r["data"]["total"] == 1
    assert r["data"]["candidates"] == cands
    assert "relaxation_suggestions" not in r["data"]
