"""Sentinela — matcher de elegibilidade cobre TODAS as colunas de escopo da verba.

Fase 5a. Pinam matches_subsidiaries (filial/CNPJ). Sentinela de harness: se alguem
adicionar uma nova coluna de escopo em CompensationComponent sem liga-la no
list_matching, falha (evita ghost field como subsidiaries foi).
"""
import inspect

from app.shared.eligibility_matching import matches_subsidiaries


# ── subsidiaries (filial / CNPJ) ──────────────────────────────────────────
def test_empty_subsidiaries_applies_to_all():
    assert matches_subsidiaries([], "Filial SP", "11.111.111/0001-11") is True
    assert matches_subsidiaries(None, "Filial SP") is True


def test_vaga_without_subsidiary_not_restricted():
    subs = [{"name": "Filial SP", "cnpj": "11111111000111"}]
    assert matches_subsidiaries(subs, None, None) is True


def test_match_by_name_normalized():
    subs = [{"name": "Filial São Paulo", "cnpj": None}]
    assert matches_subsidiaries(subs, "filial sao paulo") is True


def test_match_by_cnpj_digits_only():
    subs = [{"name": "X", "cnpj": "11.111.111/0001-11"}]
    assert matches_subsidiaries(subs, None, "11111111000111") is True


def test_subsidiary_no_match():
    subs = [{"name": "Filial SP", "cnpj": "11111111000111"}]
    assert matches_subsidiaries(subs, "Filial RJ", "22222222000122") is False


# ── sentinela de cobertura ────────────────────────────────────────────────
def test_harness_sentinel_every_scope_column_has_matcher_in_list_matching():
    from app.domains.company.repositories.compensation_component_repository import (
        CompensationComponentRepository,
    )
    from app.models.compensation_component import CompensationComponent

    # Colunas de escopo conhecidas (atualize JUNTO com o matcher ao adicionar dimensao).
    scope_columns = {"seniority_levels", "contract_types", "departments", "subsidiaries"}
    model_columns = {c.name for c in CompensationComponent.__table__.columns}
    assert scope_columns <= model_columns, (
        f"Colunas de escopo ausentes no modelo: {scope_columns - model_columns}"
    )

    src = inspect.getsource(CompensationComponentRepository.list_matching)
    for col in scope_columns:
        assert f"c.{col}" in src, (
            f"list_matching NAO usa c.{col} — coluna de escopo virou ghost field. "
            f"Ligue-a num matcher de app/shared/eligibility_matching.py."
        )
