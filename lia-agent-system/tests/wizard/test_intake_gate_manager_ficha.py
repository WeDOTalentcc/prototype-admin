"""
Bug #4 — _ficha_data() não inclui parsed_manager_email / parsed_manager_name.

O FE recebe ws_stage_payload.data via SSE mas nunca vê o gestor, porque _ficha_data
não o inclui. O gestor fica no state (parsed_manager_email) mas nunca é enviado
ao painel lateral.

RED: _ficha_data com manager no state → data NÃO inclui parsed_manager_email.
GREEN: _ficha_data inclui parsed_manager_email / parsed_manager_name.

Sentinelas:
  T1 — _ficha_data com email no state → data.parsed_manager_email presente
  T2 — _ficha_data com nome no state → data.parsed_manager_name presente
  T3 — _ficha_data sem manager → keys existem com None (sem KeyError no FE)
  T4 — nó inteiro: ws_stage_payload.data.parsed_manager_email após turno off_topic
"""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _import_ficha_data():
    mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
    return getattr(mod, "_ficha_data")


def _base_state(**kw):
    s = {
        "parsed_title": "Diretor de RH",
        "parsed_seniority": "Senior",
        "parsed_model": "hibrido",
        "parsed_department": None,
        "parsed_location": None,
        "parsed_employment_type": None,
        "screening_mode": None,
        "salary_min": None,
        "salary_max": None,
        "salary_range": None,
    }
    s.update(kw)
    return s


class TestManagerEmailInFichaData:
    def test_email_present_in_data(self):
        _ficha_data = _import_ficha_data()
        state = _base_state(parsed_manager_email="jose.moreira@empresa.com")
        data = _ficha_data(state, "msg de teste")
        assert "parsed_manager_email" in data, (
            "_ficha_data não inclui 'parsed_manager_email' → FE nunca vê o gestor. "
            "Fix: adicionar state.get('parsed_manager_email') ao dict retornado."
        )
        assert data["parsed_manager_email"] == "jose.moreira@empresa.com"


class TestManagerNameInFichaData:
    def test_name_present_in_data(self):
        _ficha_data = _import_ficha_data()
        state = _base_state(parsed_manager_name="Jose Moreira")
        data = _ficha_data(state, "msg de teste")
        assert "parsed_manager_name" in data, (
            "_ficha_data não inclui 'parsed_manager_name' → FE nunca vê nome do gestor. "
            "Fix: adicionar state.get('parsed_manager_name') ao dict retornado."
        )
        assert data["parsed_manager_name"] == "Jose Moreira"


class TestNoManagerKeysNone:
    def test_keys_present_with_none_when_no_manager(self):
        _ficha_data = _import_ficha_data()
        state = _base_state()  # sem manager
        data = _ficha_data(state, "msg")
        for key in ("parsed_manager_email", "parsed_manager_name"):
            assert key in data, (
                f"_ficha_data ausente key '{key}' quando gestor não fornecido. "
                "FE pode quebrar com KeyError. Fix: incluir com state.get()."
            )


class TestNodePayloadContainsManager:
    def test_manager_in_ws_stage_payload_after_off_topic(self):
        node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
        state = {
            "user_query": "me pergunte quando abrir outra vaga",
            "raw_input": "quero criar uma vaga de diretor de rh",  # original input ≠ current query
            "parsed_title": "Diretor de RH",
            "parsed_seniority": "Senior",
            "parsed_model": "hibrido",
            "parsed_manager_email": "jose.moreira@empresa.com",
            "parsed_manager_name": "Jose Moreira",
            "intake_approved": None,
            "intake_salary_suggested": True,
            "intake_gate_seen_user_query": "titulo dado",
            "current_stage": "intake",
            "workspace_id": "co",
            "company_id": "co",
        }
        out = types.SimpleNamespace(
            intent="off_topic", confidence=0.9,
            extracted_data={}, conversational_reply="ok",
        )

        async def _classify(**kwargs):
            return out

        fake_cls = mock.Mock()
        fake_cls.classify = _classify

        with mock.patch(
            "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
            return_value=False,
        ), mock.patch(
            "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
            return_value=fake_cls,
        ), mock.patch(
            "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
            return_value=None,
        ), mock.patch(
            "app.domains.job_creation.nodes.intake_gate._resolve_confirmed_competencies",
            return_value=([], [], None),
        ):
            result = node_mod.intake_gate_node(state)

        data = ((result.get("ws_stage_payload") or {}).get("data")) or {}
        assert data.get("parsed_manager_email") == "jose.moreira@empresa.com", (
            "ws_stage_payload.data não tem parsed_manager_email após turno off_topic. "
            "FE mostra painel vazio para gestor. Fix: incluir em _ficha_data()."
        )
