"""Sensor: fingerprint estavel dos criterios de busca (Fase 2).

_generate_search_fingerprint ancora feedback/aprendizado ao CONJUNTO DE CRITERIOS
da busca (query + search_spec/filtros), nao a vaga nem recrutador. Pina:
- determinismo (mesmos criterios -> mesmo hash)
- sensibilidade (query/filtro diferente -> hash diferente)
- normalizacao (ordem de array, case, espaco nao mudam o hash)
- chaves utilitarias ignoradas (has_email etc. nao mudam o hash)

Skill: tdd-workflow + harness-engineering (sensor computacional).
"""
from app.api.v1.candidate_search._shared import _generate_search_fingerprint as fp


def test_deterministico_mesmos_criterios():
    a = fp("engenheiro python senior", {"skills": ["python", "aws"]})
    b = fp("engenheiro python senior", {"skills": ["python", "aws"]})
    assert a == b


def test_query_diferente_muda_hash():
    assert fp("dev java", {}) != fp("dev python", {})


def test_filtro_diferente_muda_hash():
    base = fp("dev", {"skills": ["python"]})
    assert base != fp("dev", {"skills": ["python", "aws"]})
    assert base != fp("dev", {"locations": ["sao paulo"]})


def test_ordem_de_array_nao_importa():
    assert fp("dev", {"skills": ["python", "aws"]}) == fp("dev", {"skills": ["aws", "python"]})


def test_case_e_espaco_normalizados():
    assert fp("  Dev Python  ", {"skills": ["Python"]}) == fp("dev python", {"skills": ["python"]})


def test_chaves_utilitarias_ignoradas():
    base = fp("dev", {"skills": ["python"]})
    # has_email/datas nao definem a identidade da referencia
    assert base == fp("dev", {"skills": ["python"], "has_email": True})
    assert base == fp("dev", {"skills": ["python"], "updated_at_from": "2026-01-01"})


def test_spec_vazio_vs_none():
    assert fp("dev", None) == fp("dev", {})


def test_hash_tem_tamanho_fixo():
    h = fp("qualquer", {"skills": ["x"]})
    assert isinstance(h, str) and len(h) == 32
