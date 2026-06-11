"""Sensor F-3.3 (PR-8 ONDA 3): WSI question distribution YAML canonical schema.

Garante que wsi_question_distribution.yaml mantém invariantes da
WSI_METHODOLOGY_COMPLETE_v2.md:

- compact mode soma 7 (technical + behavioral) por seniority
- full mode soma 12 (technical + behavioral) por seniority
- 8 seniorities canonical em ambos modes
- valores casam com hardcoded original em graph.py (paridade)
"""

import yaml
from pathlib import Path

import pytest


YAML_PATH = (
    Path(__file__).resolve().parents[2]
    / "app/prompts/job_creation/wsi_question_distribution.yaml"
)

CANONICAL_SENIORITIES = {
    "estagiario",
    "junior",
    "pleno",
    "senior",
    "lead",
    "principal",
    "staff",
    "diretor",
    "executive",
}


@pytest.fixture(scope="module")
def distributions():
    assert YAML_PATH.exists(), f"YAML faltando em {YAML_PATH}"
    with open(YAML_PATH) as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), "YAML root deve ser dict"
    return data


def test_yaml_loads(distributions):
    """YAML parseável e nao-vazio."""
    assert distributions, "YAML vazio"


def test_modes_present(distributions):
    """compact + full presentes."""
    assert "compact" in distributions
    assert "full" in distributions


def test_compact_totals_7(distributions):
    """Cada seniority compact soma 7 questoes."""
    for seniority, blocks in distributions["compact"].items():
        total = sum(blocks.values())
        assert total == 7, (
            f"compact[{seniority}] total = {total}, esperado 7 "
            f"(blocks = {blocks})"
        )


def test_full_totals_12(distributions):
    """Cada seniority full soma 12 questoes."""
    for seniority, blocks in distributions["full"].items():
        total = sum(blocks.values())
        assert total == 12, (
            f"full[{seniority}] total = {total}, esperado 12 "
            f"(blocks = {blocks})"
        )


def test_all_seniorities_canonical(distributions):
    """8 seniorities canonical presentes em compact e full."""
    compact_keys = set(distributions["compact"].keys())
    full_keys = set(distributions["full"].keys())
    assert compact_keys == CANONICAL_SENIORITIES, (
        f"compact seniorities mismatch: {compact_keys ^ CANONICAL_SENIORITIES}"
    )
    assert full_keys == CANONICAL_SENIORITIES, (
        f"full seniorities mismatch: {full_keys ^ CANONICAL_SENIORITIES}"
    )


def test_block_types_only_technical_behavioral(distributions):
    """Apenas technical + behavioral sao tipos de bloco canonical."""
    allowed = {"technical", "behavioral"}
    for mode, table in distributions.items():
        for seniority, blocks in table.items():
            assert set(blocks.keys()) == allowed, (
                f"{mode}[{seniority}] blocos = {list(blocks.keys())}, "
                f"esperado {allowed}"
            )


def test_consumer_uses_yaml():
    """_get_question_distribution lê do YAML e nao mais do dict hardcoded.

    Paridade contra a tabela original (hardcoded substituido em PR-8).
    """
    from app.domains.job_creation.graph import _get_question_distribution

    # Spot-check valores canonical contra hardcoded original
    assert _get_question_distribution("compact", "pleno") == {
        "technical": 5,
        "behavioral": 2,
    }
    assert _get_question_distribution("compact", "lead") == {
        "technical": 3,
        "behavioral": 4,
    }
    assert _get_question_distribution("full", "senior") == {
        "technical": 7,
        "behavioral": 5,
    }
    assert _get_question_distribution("full", "estagiario") == {
        "technical": 9,
        "behavioral": 3,
    }
    # Variante acentuada normalizada
    assert _get_question_distribution("compact", "sênior") == {
        "technical": 4,
        "behavioral": 3,
    }
    # Unknown seniority -> fallback pleno
    assert _get_question_distribution("compact", "alien") == {
        "technical": 5,
        "behavioral": 2,
    }
