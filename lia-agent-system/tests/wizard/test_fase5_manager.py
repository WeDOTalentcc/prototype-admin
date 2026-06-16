"""FASE 5 — gestor + email (manager_name/manager_email) persistidos ponta a ponta.

Gap identificado por Paulo (2026-05-30): ao criar vaga, o intake nao coletava
gestor/email do gestor. O IntakeExtractor ja conhecia os campos do schema
(manager_name/manager_email) e o right_panel_form ja os honrava, mas o
intake_node descartava-os (sem parsed_manager_*) e o publish.job_data nao os
enviava. Estes testes pinam o wire extractor->state->publish + override via
right_panel_form (edicao no painel da ficha viva).

Espelha tests/wizard/test_p0a_contract.py (mesmo padrao P0-A do employment_type).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.domains.job_creation.nodes.intake import intake_node


def _field(v):
    return SimpleNamespace(value=v, source="llm", confidence=0.9)


def _fake_payload(manager="Ana Souza", email="ana@empresa.com"):
    return SimpleNamespace(
        title=_field("Desenvolvedor Python"),
        seniority=_field("senior"),
        department=_field("engenharia"),
        location=_field("remoto"),
        work_model=_field("remoto"),
        contract_type=_field("clt"),
        manager_name=_field(manager),
        manager_email=_field(email),
        overall_confidence=0.9,
    )


def test_intake_maps_manager_to_parsed_manager_name():
    """intake_node deve mapear payload.manager_name -> state.parsed_manager_name."""
    fake = MagicMock()
    fake.extract.return_value = _fake_payload()
    fake.extract_from_sources.return_value = _fake_payload()
    state = {
        "raw_input": "vaga dev python senior, gestor Ana Souza ana@empresa.com",
        "user_query": "vaga dev python senior, gestor Ana Souza ana@empresa.com",
    }
    with patch(
        "app.domains.job_creation.graph.get_intake_extractor",
        return_value=fake,
    ):
        result = intake_node(state)

    assert result.get("parsed_manager_name") == "Ana Souza", (
        "intake_node nao persistiu manager_name em parsed_manager_name. "
        f"keys: {[k for k in result if 'manager' in k or 'parsed' in k]}"
    )
    assert result.get("parsed_manager_email") == "ana@empresa.com"


def test_intake_manager_in_ws_stage_payload():
    """O painel (ficha viva) recebe gestor + email no ws_stage_payload.data."""
    fake = MagicMock()
    fake.extract.return_value = _fake_payload("Bruno Lima", "bruno@co.com")
    fake.extract_from_sources.return_value = _fake_payload("Bruno Lima", "bruno@co.com")
    state = {"raw_input": "vaga", "user_query": "vaga"}
    with patch(
        "app.domains.job_creation.graph.get_intake_extractor",
        return_value=fake,
    ):
        result = intake_node(state)
    data = (result.get("ws_stage_payload") or {}).get("data") or {}
    assert data.get("parsed_manager_name") == "Bruno Lima"
    assert data.get("parsed_manager_email") == "bruno@co.com"


def test_right_panel_form_overrides_manager():
    """Edicao no painel (right_panel_form) tem precedencia (recognition > recall).

    Pina o caminho FASE 5b: o recrutador edita o gestor na ficha viva, o valor
    viaja como right_panel_form.manager_name e o IntakeExtractor o honra a 0.95.
    user_text vazio => sem LLM (teste puro).
    """
    from app.domains.job_creation.services.intake_extractor import IntakeExtractor

    payload = IntakeExtractor().extract_from_sources(
        user_text="",
        right_panel_form={
            "manager_name": "Carla Dias",
            "manager_email": "carla@empresa.com",
        },
    )
    assert payload.manager_name.value == "Carla Dias"
    assert payload.manager_name.source == "right_panel_form"
    assert payload.manager_email.value == "carla@empresa.com"


def test_publish_job_data_includes_manager():
    """Sensor estrutural: publish.job_data inclui manager + manager_email."""
    import inspect
    from app.domains.job_creation.nodes import publish as publish_mod

    src = inspect.getsource(publish_mod)
    assert '"manager": state.get("parsed_manager_name")' in src, (
        "publish.job_data nao inclui manager — vaga criada sem gestor."
    )
    assert '"manager_email": state.get("parsed_manager_email")' in src, (
        "publish.job_data nao inclui manager_email."
    )


def test_devlocal_insert_includes_manager_and_p0_fields():
    """Sensor estrutural: o INSERT dev-local (api_client._create_job_local) inclui
    manager/manager_email/employment_type/salary_range.

    Gap descoberto 2026-05-30: o path dev-local (ativo no Replit quando Rails
    base_url vazio) so inseria 15 colunas e descartava silenciosamente os campos
    que o publish_node monta. Sem isto, gestor/email (FASE 5), contrato (P0-A) e
    salario (P0-B) nao persistiam no path dev-local.
    """
    import inspect
    from app.domains.job_creation import api_client as ac_mod

    src = inspect.getsource(ac_mod.JobCreationAPIClient._create_job_local)
    for col in ("employment_type", "manager", "manager_email", "salary_range"):
        assert col in src, f"dev-local INSERT nao inclui coluna {col!r}"
    # As colunas precisam estar na lista canonica _columns E no SQL INSERT.
    assert '"manager", "manager_email"' in src or "'manager', 'manager_email'" in src, (
        "manager/manager_email ausentes da lista _columns do INSERT dev-local"
    )
