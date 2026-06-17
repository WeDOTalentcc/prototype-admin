"""sticky_vacancy (fix #1 live audit, 2026-06-07).

Escopo de vaga sticky por conversa: persiste a ultima vaga resolvida e
reaproveita quando o turno nao resolve nenhuma (em vez de zerar). Isso impede
list_candidates/rank de perderem o escopo num follow-up.
"""
from __future__ import annotations

from app.shared.entity_resolver import sticky_vacancy, _ACTIVE_VACANCY_BY_CONV


def setup_function():
    _ACTIVE_VACANCY_BY_CONV.clear()


def test_persists_resolved():
    assert sticky_vacancy("c1", "v1") == "v1"


def test_reuses_last_when_none_this_turn():
    sticky_vacancy("c1", "v1")
    # follow-up sem vaga -> mantem v1 (NAO zera)
    assert sticky_vacancy("c1", "") == "v1"


def test_new_resolved_overrides():
    sticky_vacancy("c1", "v1")
    assert sticky_vacancy("c1", "v2") == "v2"
    assert sticky_vacancy("c1", "") == "v2"


def test_scoped_per_conversation():
    sticky_vacancy("c1", "v1")
    # outra conversa sem vaga -> nao herda v1
    assert sticky_vacancy("c2", "") == ""


def test_empty_conv_id_safe():
    assert sticky_vacancy("", "") == ""
    assert sticky_vacancy("", "v9") == "v9"  # retorna mas nao persiste (sem cid)
    assert sticky_vacancy("", "") == ""
