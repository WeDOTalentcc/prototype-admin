"""Sensor: serialize_panel_update inclui thread_id + completeness para o wizard.

Bug 2026-06-05 (chat full): o painel do wizard fechava ao digitar o titulo.
O frame panel_update(panel_type="wizard_stage") nao carregava thread_id nem
completeness, entao a chave de dedup do FE (thread_id:stage:completeness)
colapsava entre dois turnos do MESMO stage -> a ponte que injeta o `stage` era
suprimida no 2o turno -> painel sumia.

Estes testes pinam o contrato do produtor: quando thread_id/completeness sao
fornecidos, aparecem no frame; quando None, sao omitidos (serialize_event
descarta None) para nao poluir os demais panel_update nao-wizard.
"""
from app.shared.chat_event_serializer import serialize_panel_update


def test_wizard_panel_update_carries_thread_id_and_completeness():
    ev = serialize_panel_update(
        panel_type="wizard_stage",
        panel_data={"message": "Perfeito..."},
        panel_title="intake",
        action="open",
        thread_id="wiz-abc-sess1",
        completeness=0.42,
    )
    assert ev["type"] == "panel_update"
    assert ev["panel_type"] == "wizard_stage"
    assert ev["thread_id"] == "wiz-abc-sess1"
    assert ev["completeness"] == 0.42


def test_two_intake_turns_produce_distinct_dedup_keys():
    # FE dedup key = f"{thread_id}:{stage}:{completeness}". Dois turnos do mesmo
    # stage com completeness crescente DEVEM gerar chaves distintas.
    a = serialize_panel_update(
        "wizard_stage", {}, "intake", "open",
        thread_id="wiz-x-s", completeness=0.2,
    )
    b = serialize_panel_update(
        "wizard_stage", {}, "intake", "open",
        thread_id="wiz-x-s", completeness=0.5,
    )
    key_a = f"{a.get('thread_id')}:{a['panel_title']}:{a.get('completeness')}"
    key_b = f"{b.get('thread_id')}:{b['panel_title']}:{b.get('completeness')}"
    assert key_a != key_b


def test_non_wizard_panel_update_omits_optional_fields():
    ev = serialize_panel_update(
        panel_type="candidate_profile",
        panel_data={"id": "c1"},
        panel_title="Candidato",
        action="open",
    )
    assert "thread_id" not in ev
    assert "completeness" not in ev
