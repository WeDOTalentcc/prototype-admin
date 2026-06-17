"""UC-P1-28: Rail A ghost card capabilities — 7 missing capabilities added to capability_map.yaml."""
from app.shared.services.capability_map_service import CapabilityMapService


def test_capability_map_loads_with_at_least_22_entries():
    caps = CapabilityMapService.load()
    assert len(caps) >= 22, f"Expected >= 22 capabilities, got {len(caps)}"


def test_all_7_ghost_capabilities_present():
    caps = CapabilityMapService.load()
    expected = {
        "criar_vaga",
        "listar_talent_pools",
        "criar_automacao",
        "consultar_consumo",
        "configurar_policy",
        "criar_template",
        "criar_a_partir_de_template",
    }
    missing = expected - set(caps.keys())
    assert not missing, f"Missing Rail A UC-P1-28 capabilities: {missing}"


def test_all_new_capabilities_have_navigate_fallback_or_modal():
    caps = CapabilityMapService.load()
    new_ids = [
        "criar_vaga", "listar_talent_pools", "criar_automacao",
        "consultar_consumo", "configurar_policy", "criar_template",
        "criar_a_partir_de_template",
    ]
    for cap_id in new_ids:
        cap = caps[cap_id]
        assert cap.navigate_fallback or cap.modal_id, (
            f"UC-P1-28: '{cap_id}' must have navigate_fallback or modal_id to avoid dead-end."
        )


def test_criar_a_partir_de_template_requires_template_entity():
    reqs = CapabilityMapService.needs_entity("criar_a_partir_de_template")
    assert any(r.type == "template" for r in reqs), (
        "criar_a_partir_de_template must require template_id — which template to copy?"
    )


def test_criar_automacao_not_chat_executable_has_modal():
    cap = CapabilityMapService.get("criar_automacao")
    assert cap is not None
    assert cap.chat_executable is False
    assert cap.modal_id == "automation_builder"


def test_configurar_policy_not_chat_executable_has_modal():
    cap = CapabilityMapService.get("configurar_policy")
    assert cap is not None
    assert cap.chat_executable is False
    assert cap.modal_id == "hiring_policy_config"


def test_criar_template_not_chat_executable_has_modal():
    cap = CapabilityMapService.get("criar_template")
    assert cap is not None
    assert cap.chat_executable is False
    assert cap.modal_id == "template_builder"


def test_criar_vaga_is_chat_executable():
    cap = CapabilityMapService.get("criar_vaga")
    assert cap is not None
    assert cap.chat_executable is True
    assert cap.navigate_fallback == "/jobs/new"


def test_listar_talent_pools_is_chat_executable():
    cap = CapabilityMapService.get("listar_talent_pools")
    assert cap is not None
    assert cap.chat_executable is True


def test_consultar_consumo_is_chat_executable():
    cap = CapabilityMapService.get("consultar_consumo")
    assert cap is not None
    assert cap.chat_executable is True
