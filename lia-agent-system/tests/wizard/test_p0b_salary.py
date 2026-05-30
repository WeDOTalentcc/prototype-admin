"""P0-B — faixa salarial persistida a partir do benchmark de mercado.

Auditoria 2026-05-29: nenhum nó gravava salary_min/max (só review_gate resetava
pra None); salary_node só buscava o benchmark sem extrair a faixa. Resultado:
vaga publicada com salary_min/max=None. Fix: salary_node popula a faixa do
benchmark (sem sobrescrever o que o recrutador já definiu) + publish mapeia
salary_range JSON (coluna canônica).
"""
from __future__ import annotations

from unittest.mock import patch

from app.domains.job_creation.nodes.salary import salary_node


def _benchmark(mn=12000, mx=18000):
    return {"min": mn, "max": mx, "median": (mn + mx) // 2,
            "source": "market", "confidence": "high"}


def test_salary_node_populates_range_from_benchmark():
    """Sem faixa definida, salary_node popula salary_min/max do benchmark."""
    state = {"parsed_title": "Dev", "parsed_seniority": "senior"}  # sem salary_min
    with patch(
        "app.domains.job_creation.nodes.salary.run_coro_in_threadpool",
        return_value=_benchmark(12000, 18000),
    ):
        result = salary_node(state)
    assert result.get("salary_min") == 12000
    assert result.get("salary_max") == 18000
    assert result.get("salary_currency") == "BRL"


def test_salary_node_does_not_override_recruiter_value():
    """Se o recrutador já definiu a faixa, o benchmark NÃO sobrescreve."""
    state = {
        "parsed_title": "Dev", "parsed_seniority": "senior",
        "salary_min": 20000, "salary_max": 28000, "salary_currency": "BRL",
    }
    with patch(
        "app.domains.job_creation.nodes.salary.run_coro_in_threadpool",
        return_value=_benchmark(12000, 18000),
    ):
        result = salary_node(state)
    assert result.get("salary_min") == 20000  # preservado
    assert result.get("salary_max") == 28000


def test_publish_job_data_maps_salary_range():
    """Sensor estrutural: publish.job_data inclui salary_range JSON (coluna canônica)."""
    import inspect
    from app.domains.job_creation.nodes import publish as publish_mod
    src = inspect.getsource(publish_mod)
    assert '"salary_range":' in src, (
        "publish.job_data não mapeia salary_range — a faixa não chega na coluna "
        "canônica salary_range JSON."
    )
