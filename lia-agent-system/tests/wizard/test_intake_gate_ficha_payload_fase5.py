"""TDD ajuste 5 — payload cumulativo do intake_gate.

Todas as respostas do intake_gate carregam parsed_* + screening_mode + salary
no ws_stage_payload.data, para a ficha viva (5a) mostrar zonas e competências
no MESMO payload (useWizardFlow substitui stageData, não faz merge).

Run:
    cd lia-agent-system && python -m pytest tests/wizard/test_intake_gate_ficha_payload_fase5.py -v --no-cov
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _state(**ov):
    base = {
        "parsed_title": "Engenheiro de Software",
        "parsed_seniority": "senior",
        "parsed_model": "remoto",
        "parsed_department": "Tecnologia",
        "parsed_location": "São Paulo",
        "parsed_employment_type": "CLT",
        "intake_salary_suggested": None,
        "intake_approved": None,
        "screening_mode": None,
        "user_query": "quero criar vaga engenheiro senior remoto",
        "raw_input": "quero criar vaga engenheiro senior remoto",
        "intake_gate_seen_user_query": None,
        "current_stage": "intake",
        "workspace_id": "cid-1",
        "company_id": "cid-1",
    }
    base.update(ov)
    return base


def _data_of(result):
    return ((result.get("ws_stage_payload") or {}).get("data")) or {}


def _run(state, suggestion=None):
    node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
    svc = mock.MagicMock()
    svc.suggest_competencies = mock.AsyncMock(return_value=suggestion or {
        "technical": [{"skill": "Python", "contexto": "c"}],
        "behavioral": [{"competencia": "Comunicação", "contexto": "c", "trait_big_five": "extraversion"}],
    })
    with mock.patch("app.domains.job_creation.nodes.intake_gate._in_graph_runtime", return_value=False), \
         mock.patch("app.domains.job_creation.nodes.intake_gate._safe_fetch_salary", return_value={"min": 10000, "max": 15000}), \
         mock.patch("app.domains.analytics.services.competency_benchmark_service.get_competency_benchmark_service", return_value=svc):
        return node_mod.intake_gate_node(state)


class TestPermissionPayloadCumulative:
    def test_permission_data_has_parsed_fields(self):
        # campos presentes, salário não sugerido → sub-estado permissão (_make_ws_response)
        result = _run(_state(intake_salary_suggested=None))
        data = _data_of(result)
        assert data.get("parsed_title") == "Engenheiro de Software"
        assert data.get("parsed_seniority") == "senior"
        assert data.get("parsed_model") == "remoto"

    def test_permission_data_has_enriching_fields(self):
        result = _run(_state(intake_salary_suggested=None))
        data = _data_of(result)
        assert data.get("parsed_department") == "Tecnologia"
        assert data.get("parsed_location") == "São Paulo"
        assert data.get("parsed_employment_type") == "CLT"


class TestApprovalPayloadCumulative:
    def _approve(self):
        return _run(_state(
            intake_salary_suggested=True,
            user_query="compacto, pode criar",
            intake_gate_seen_user_query="quero criar vaga engenheiro senior remoto",
        ))

    def test_approval_data_has_parsed_and_mode(self):
        data = _data_of(self._approve())
        assert data.get("parsed_title") == "Engenheiro de Software"
        assert data.get("screening_mode") == "compact"

    def test_approval_data_still_has_competencies(self):
        data = _data_of(self._approve())
        comp = (data.get("suggestions_data") or {}).get("competencies")
        assert comp is not None
        assert len(comp.get("technical") or []) >= 1

    def test_approval_data_has_confirmed(self):
        data = _data_of(self._approve())
        assert "confirmed_technical_competencies" in data
        assert "confirmed_behavioral_competencies" in data


class TestClarifyPayloadCumulative:
    def test_clarify_data_has_parsed(self):
        result = _run(_state(
            intake_salary_suggested=True,
            user_query="não sei ainda",
            intake_gate_seen_user_query="quero criar vaga engenheiro senior remoto",
        ))
        data = _data_of(result)
        assert data.get("parsed_title") == "Engenheiro de Software"
