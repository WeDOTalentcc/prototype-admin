"""Sensor TDD — salary_node resolve a faixa da EMPRESA antes do benchmark.

Audit 2026-06-06: a faixa cadastrada em Configuracoes -> Faixas Salariais por
Nivel e POLITICA da empresa (fonte verificada), nao estimativa. salary_node
deve preencher salary_min/max a partir dela (por nivel + departamento +
contrato) ANTES de buscar mercado. Mercado e fallback so quando nao ha banda.

Precedencia canonica: right_panel_form (recrutador) > banda da empresa >
benchmark de mercado.
"""
from unittest.mock import patch


def _base_state(**kwargs):
    return {
        "parsed_title": "Diretor Juridico",
        "parsed_seniority": "director",
        "parsed_department": "Juridico",
        "parsed_employment_type": "clt",
        "workspace_id": "cid-test",
        **kwargs,
    }


def _call_node(state, *, band=None, benchmark=None, toggle_active=True):
    from app.domains.job_creation.nodes.salary import salary_node
    with patch(
        "app.domains.job_creation.nodes.salary._salary_ranges_toggle_active",
        return_value=toggle_active,
    ) as m_toggle, patch(
        "app.domains.job_creation.nodes.salary._resolve_company_salary_band",
        return_value=band,
    ) as m_band, patch(
        "app.domains.job_creation.nodes.salary.run_coro_in_threadpool",
        return_value=benchmark,
    ) as m_bench, patch(
        "app.domains.job_creation.graph._emit_fallback_telemetry",
        return_value=None,
    ), patch(
        "app.domains.job_creation.graph._emit_wizard_fallback_metric"
    ):
        result = salary_node(state)
        return result, m_band, m_bench


class TestSalaryNodeCompanyBand:
    """salary_node preenche a faixa da empresa antes do benchmark de mercado."""

    def test_band_fills_salary_with_provenance(self):
        """Banda cadastrada -> preenche salary_min/max + provenance verificada."""
        state = _base_state(salary_min=None, salary_max=None)
        result, _m_band, _m_bench = _call_node(
            state, band={"min": 35000, "max": 40000, "currency": "BRL"},
        )
        assert result["salary_min"] == 35000
        assert result["salary_max"] == 40000
        assert result["salary_currency"] == "BRL"
        assert result.get("salary_provenance") == "company_salary_band"

    def test_band_skips_market_benchmark_fetch(self):
        """Banda casou -> nao gasta o fetch de mercado (45s)."""
        state = _base_state(salary_min=None, salary_max=None)
        _result, m_band, m_bench = _call_node(
            state, band={"min": 4000, "max": 8000, "currency": "BRL"},
        )
        m_band.assert_called_once()
        m_bench.assert_not_called()

    def test_no_band_falls_back_to_market_benchmark(self):
        """Sem banda pro escopo -> cai no benchmark de mercado (verificado)."""
        state = _base_state(salary_min=None, salary_max=None)
        result, _m_band, m_bench = _call_node(
            state,
            band=None,
            benchmark={
                "min": 12000, "max": 18000, "currency": "BRL",
                "confidence": "high", "is_estimate": False, "source": "market",
            },
        )
        m_bench.assert_called_once()
        assert result["salary_min"] == 12000
        assert result["salary_max"] == 18000
        assert result.get("salary_provenance") != "company_salary_band"

    def test_toggle_off_skips_band_uses_benchmark(self):
        """Toggle 'salary_ranges' OFF nas Instrucoes da LIA -> nao usa a banda da
        empresa; cai no benchmark de mercado (fallback canonico)."""
        state = _base_state(salary_min=None, salary_max=None)
        result, m_band, m_bench = _call_node(
            state,
            toggle_active=False,
            band={"min": 35000, "max": 40000, "currency": "BRL"},
            benchmark={
                "min": 12000, "max": 18000, "currency": "BRL",
                "confidence": "high", "is_estimate": False, "source": "market",
            },
        )
        m_band.assert_not_called()  # toggle OFF -> nem resolve a banda
        m_bench.assert_called_once()  # cai no benchmark
        assert result["salary_min"] == 12000
        assert result.get("salary_provenance") != "company_salary_band"

    def test_right_panel_form_wins_over_band(self):
        """Edicao do recrutador no painel vence a banda da empresa."""
        state = _base_state(
            salary_min=None, salary_max=None,
            right_panel_form={"salary_min": 50000, "salary_max": 60000},
        )
        result, m_band, _m_bench = _call_node(
            state, band={"min": 35000, "max": 40000, "currency": "BRL"},
        )
        assert result["salary_min"] == 50000
        assert result["salary_max"] == 60000
        m_band.assert_not_called()
