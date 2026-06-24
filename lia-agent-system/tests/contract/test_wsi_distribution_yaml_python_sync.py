"""Sensor: SENIORITY_WEIGHTS e SENIORITY_DISTRIBUTIONS Python devem ser coerentes
e SENIORITY_WEIGHTS deve cobrir todas as chaves canônicas de SENIORITY_DISTRIBUTIONS.

Task 7 do plano WSI — fix split-brain entre scorer e distribuições.
"""
import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _python_seniority_keys():
    """Retorna o set de senioridades presentes em SENIORITY_DISTRIBUTIONS (modo full)."""
    from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS
    return set(SENIORITY_DISTRIBUTIONS.get("full", SENIORITY_DISTRIBUTIONS).keys())


# ---------------------------------------------------------------------------
# Testes sensor
# ---------------------------------------------------------------------------

def test_seniority_distributions_has_all_yaml_canonical():
    """SENIORITY_DISTRIBUTIONS Python deve conter todas as 8 senioridades YAML."""
    yaml_canonical = {
        "estagiario", "junior", "pleno", "senior",
        "lead", "principal", "staff", "diretor", "executive",
    }
    keys = _python_seniority_keys()
    missing = yaml_canonical - keys
    assert not missing, (
        f"YAML seniorities ausentes em SENIORITY_DISTRIBUTIONS Python: {missing}"
    )


def test_seniority_weights_covers_all_python_keys():
    """SENIORITY_WEIGHTS deve cobrir todas as chaves de SENIORITY_DISTRIBUTIONS.

    Garante que o scorer não caia em fallback para nenhuma senioridade válida.
    """
    from app.domains.cv_screening.services.wsi_deterministic_scorer import SENIORITY_WEIGHTS
    python_keys = _python_seniority_keys()
    missing = [k for k in python_keys if k not in SENIORITY_WEIGHTS]
    assert not missing, (
        f"Chaves em SENIORITY_DISTRIBUTIONS sem entrada em SENIORITY_WEIGHTS: {missing}. "
        f"O scorer cairia no fallback {{technical: 0.625, behavioral: 0.375}} para essas senioridades."
    )


@pytest.mark.parametrize("seniority,mode,exp_tech,exp_behav", [
    # YAML canonical spot-checks por senioridade
    ("senior",     "full",    7, 5),
    ("diretor",    "full",    7, 5),
    ("pleno",      "full",    8, 4),
    ("junior",     "full",    9, 3),
    ("estagiario", "full",    9, 3),
    ("lead",       "full",    7, 5),
    ("principal",  "full",    7, 5),
    ("senior",     "compact", 4, 3),
    ("pleno",      "compact", 5, 2),
    ("diretor",    "compact", 3, 4),
    ("lead",       "compact", 3, 4),
])
def test_python_distribution_values(seniority, mode, exp_tech, exp_behav):
    """SENIORITY_DISTRIBUTIONS Python bate com YAML canonical."""
    from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS
    dist = SENIORITY_DISTRIBUTIONS[mode][seniority]
    assert dist["technical"] == exp_tech, (
        f"{seniority}/{mode}: technical={dist['technical']}, esperado {exp_tech}"
    )
    assert dist["behavioral"] == exp_behav, (
        f"{seniority}/{mode}: behavioral={dist['behavioral']}, esperado {exp_behav}"
    )


@pytest.mark.parametrize("alias,expected_key", [
    ("vp",        "executive"),
    ("executive", "executive"),
    ("vp_clevel", "executive"),
    ("staff",     "senior"),
    ("diretor",   "diretor"),
    ("director",  "diretor"),
])
def test_normalize_aliases_return_valid_distribution_key(alias, expected_key):
    """_normalize_seniority_for_kernel retorna chave que existe em SENIORITY_DISTRIBUTIONS."""
    from app.domains.cv_screening.services.wsi_service.service import _normalize_seniority_for_kernel
    from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS
    normalized = _normalize_seniority_for_kernel(alias)
    assert normalized == expected_key, (
        f"alias {alias!r} normalizou para {normalized!r}, esperado {expected_key!r}"
    )
    assert normalized in SENIORITY_DISTRIBUTIONS["full"], (
        f"chave normalizada {normalized!r} não existe em SENIORITY_DISTRIBUTIONS[full]"
    )


def test_seniority_weights_executive_not_fallback():
    """SENIORITY_WEIGHTS['executive'] deve existir explicitamente.

    'vp'/'executive' normalizados → 'executive'; sem entrada explícita o scorer
    usaria o fallback {technical:0.625,behavioral:0.375} = peso de pleno, errado
    para C-level.
    """
    from app.domains.cv_screening.services.wsi_deterministic_scorer import SENIORITY_WEIGHTS
    assert "executive" in SENIORITY_WEIGHTS, (
        "SENIORITY_WEIGHTS não tem chave 'executive'. "
        "Adicione: \"executive\": {\"technical\": 0.3125, \"behavioral\": 0.6875}"
    )
    w = SENIORITY_WEIGHTS["executive"]
    assert w["technical"] <= 0.40, (
        f"executive weight técnico={w['technical']} muito alto para C-level "
        f"(esperado ≤ 0.40, como diretor=0.3125)"
    )
