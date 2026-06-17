"""TDD — item #2: responsabilidades no fluxo (confirm_responsibilities + enrich)."""
from __future__ import annotations
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext, _handle_confirm_responsibilities, build_tool_registry,
)
from app.domains.job_creation.orchestrator.wizard_service_tools import (
    _handle_enrich_job_description,
)

CTX = ToolContext(company_id="c1")


@pytest.mark.easy
def test_confirm_responsibilities_basic():
    res = _handle_confirm_responsibilities({}, {"responsibilities": ["Gerir caixa", "Negociar bancos", ""]}, CTX)
    assert not res.error
    assert res.state_updates["confirmed_responsibilities"] == ["Gerir caixa", "Negociar bancos"]


@pytest.mark.easy
def test_confirm_responsibilities_requires_list():
    assert _handle_confirm_responsibilities({}, {}, CTX).error
    assert _handle_confirm_responsibilities({}, {"responsibilities": []}, CTX).error


@pytest.mark.easy
def test_confirm_responsibilities_rejects_tenant_keys():
    res = _handle_confirm_responsibilities({}, {"responsibilities": ["x"], "company_id": "y"}, CTX)
    assert res.error and "tenant" in res.llm_message.lower()


@pytest.mark.easy
def test_registry_has_confirm_responsibilities():
    assert "confirm_responsibilities" in build_tool_registry()


@pytest.mark.medium
def test_enrich_passes_confirmed_responsibilities():
    captured = {}

    class _Enriched:
        def model_dump(self):
            return {"titulo_padronizado": "X", "responsabilidades": ["R1", "R2"]}

    def _enrich(**kw):
        captured.update(kw)
        return (_Enriched(), 80.0, [])

    fake_service = SimpleNamespace(enrich=_enrich)
    with patch("app.domains.job_creation.internal.services._get_jd_service", return_value=fake_service):
        res = _handle_enrich_job_description(
            {
                "parsed_title": "Gerente", "raw_input": "x",
                "confirmed_responsibilities": ["R1", "R2"],
            },
            {}, CTX,
        )
    assert not res.error
    # a tool repassou as responsabilidades confirmadas ao enrich (produtor)
    assert captured["confirmed_responsibilities"] == ["R1", "R2"]
