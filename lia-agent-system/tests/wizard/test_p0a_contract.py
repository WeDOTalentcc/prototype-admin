"""P0-A — regime de contratação (employment_type) persistido ponta a ponta.

Auditoria 2026-05-29: contract_type era extraído pelo IntakeExtractor mas
descartado pelo intake_node, ausente do state e do publish.job_data — vaga
criada sem regime de contratação. A coluna employment_type já existe na tabela
(zero migration). Estes testes pinam o wire extractor->state->publish.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.domains.job_creation.nodes.intake import intake_node


def _field(v):
    return SimpleNamespace(value=v, source="llm", confidence=0.9)


def _fake_payload(contract="clt"):
    return SimpleNamespace(
        title=_field("Desenvolvedor Python"),
        seniority=_field("senior"),
        department=_field("engenharia"),
        location=_field("remoto"),
        work_model=_field("remoto"),
        contract_type=_field(contract),
        overall_confidence=0.9,
    )


def test_intake_maps_contract_type_to_parsed_employment_type():
    """intake_node deve mapear payload.contract_type -> state.parsed_employment_type."""
    fake_extractor = MagicMock()
    fake_extractor.extract.return_value = _fake_payload("clt")
    fake_extractor.extract_from_sources.return_value = _fake_payload("clt")

    state = {
        "raw_input": "vaga de desenvolvedor python senior CLT remoto",
        "user_query": "vaga de desenvolvedor python senior CLT remoto",
    }
    with patch(
        "app.domains.job_creation.graph.get_intake_extractor",
        return_value=fake_extractor,
    ):
        result = intake_node(state)

    assert result.get("parsed_employment_type") == "clt", (
        "intake_node não persistiu contract_type em parsed_employment_type. "
        f"state keys: {[k for k in result if 'employ' in k or 'parsed' in k]}"
    )


def test_intake_employment_type_in_ws_stage_payload():
    """O painel também recebe o employment_type (ws_stage_payload.data)."""
    fake_extractor = MagicMock()
    fake_extractor.extract.return_value = _fake_payload("pj")
    fake_extractor.extract_from_sources.return_value = _fake_payload("pj")
    state = {"raw_input": "vaga dev PJ", "user_query": "vaga dev PJ"}
    with patch(
        "app.domains.job_creation.graph.get_intake_extractor",
        return_value=fake_extractor,
    ):
        result = intake_node(state)
    data = (result.get("ws_stage_payload") or {}).get("data") or {}
    assert data.get("parsed_employment_type") == "pj"


def test_publish_job_data_includes_employment_type():
    """Sensor estrutural: publish.job_data inclui employment_type (do state)."""
    import inspect
    from app.domains.job_creation.nodes import publish as publish_mod

    src = inspect.getsource(publish_mod)
    assert '"employment_type": state.get("parsed_employment_type")' in src, (
        "publish.job_data não inclui employment_type — vaga criada sem regime "
        "de contratação (coluna employment_type existe na tabela)."
    )
