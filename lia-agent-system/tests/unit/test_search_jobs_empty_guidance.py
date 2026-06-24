"""Fase B P0.2 (autocorrecao 0-resultados): search_jobs emite relaxation guidance.

Hoje search_jobs retorna {total:0} seco em 0-resultados -> beco sem saida. Com P0.2,
0 resultados -> sinal estruturado (empty + relaxation_suggestions + applied_filters +
guidance) via build_empty_result_guidance (helper PURO ja existente). _format_search_jobs_result
e o seam puro (testavel sem DB). Extensao da REGRA 4 (anti-fallback-silencioso).
"""
from app.domains.job_management.tools.query_tools import _format_search_jobs_result


def test_empty_returns_relaxation_guidance():
    r = _format_search_jobs_result([], {"seniority": "senior", "department": "Eng", "status": None})
    assert r["success"] is True
    d = r["data"]
    assert d["total"] == 0
    assert d.get("empty") is True
    assert d.get("relaxation_suggestions"), "deve sugerir relaxar filtros"
    # so filtros ATIVOS entram em applied_filters (status=None nao)
    assert "seniority" in d.get("applied_filters", {})
    assert "status" not in d.get("applied_filters", {})


def test_empty_without_filters_still_structured():
    r = _format_search_jobs_result([], {})
    assert r["data"]["total"] == 0
    assert r["data"].get("empty") is True


def test_nonempty_returns_normal_no_guidance():
    jobs = [{"id": "1", "title": "Dev"}]
    r = _format_search_jobs_result(jobs, {"status": "open"})
    assert r["data"]["total"] == 1
    assert r["data"]["jobs"] == jobs
    assert "relaxation_suggestions" not in r["data"]
