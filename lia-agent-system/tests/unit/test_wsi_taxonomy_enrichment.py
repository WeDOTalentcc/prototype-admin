"""TDD red-phase — WSI Skill Taxonomy enrichment (Sprint B Phase 3).

Adiciona à taxonomia existente (199 skills, v3):
  - WsiSkill.primary_ocean: dimensão OCEAN primária da skill (O/C/E/A/N)
  - WsiSkill.bias_risk: low | medium | high — controla threshold de amostras
  - WsiSkill.decay_rate: fast | normal | slow — controla λ de decay temporal
  - THRESHOLD_BY_BIAS_RISK: dict adaptive (30 / 20 / 12)
  - DECAY_LAMBDA_BY_TYPE: dict adaptive (0.12 / 0.05 / 0.02)
  - get_skills_by_ocean() / get_skills_by_bias_risk() helpers
  - app/shared/wsi_skill_taxonomy.py canonical shim (ADR-001)
  - wsi_effectiveness_service usa threshold adaptativo por bias_risk, não flat 20
"""
from __future__ import annotations
import pytest


# ── Schema fields ────────────────────────────────────────────────────────────

def test_wsi_skill_has_primary_ocean_field():
    """WsiSkill deve ter campo primary_ocean opcional (O/C/E/A/N | None)."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill
    skill = find_skill("active_listening")
    assert hasattr(skill, "primary_ocean"), (
        "WsiSkill está faltando campo primary_ocean. Adicionar:\n"
        "  primary_ocean: str | None = None  # 'O'|'C'|'E'|'A'|'N'"
    )


def test_wsi_skill_has_bias_risk_field():
    """WsiSkill deve ter campo bias_risk com default 'medium'."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill
    skill = find_skill("active_listening")
    assert hasattr(skill, "bias_risk"), (
        "WsiSkill está faltando campo bias_risk. Adicionar:\n"
        "  bias_risk: str = 'medium'  # 'low'|'medium'|'high'"
    )


def test_wsi_skill_has_decay_rate_field():
    """WsiSkill deve ter campo decay_rate com default 'normal'."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill
    skill = find_skill("active_listening")
    assert hasattr(skill, "decay_rate"), (
        "WsiSkill está faltando campo decay_rate. Adicionar:\n"
        "  decay_rate: str = 'normal'  # 'fast'|'normal'|'slow'"
    )


# ── Constants ────────────────────────────────────────────────────────────────

def test_threshold_by_bias_risk_constant_exists():
    """THRESHOLD_BY_BIAS_RISK deve existir com 3 chaves e valores crescentes."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import THRESHOLD_BY_BIAS_RISK
    assert "low" in THRESHOLD_BY_BIAS_RISK
    assert "medium" in THRESHOLD_BY_BIAS_RISK
    assert "high" in THRESHOLD_BY_BIAS_RISK


def test_threshold_by_bias_risk_values_are_ordered():
    """high > medium > low em número de amostras exigidas."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import THRESHOLD_BY_BIAS_RISK
    assert THRESHOLD_BY_BIAS_RISK["high"] > THRESHOLD_BY_BIAS_RISK["medium"]
    assert THRESHOLD_BY_BIAS_RISK["medium"] > THRESHOLD_BY_BIAS_RISK["low"]
    # Valores concretos aprovados na discussão
    assert THRESHOLD_BY_BIAS_RISK["high"] == 30
    assert THRESHOLD_BY_BIAS_RISK["medium"] == 20
    assert THRESHOLD_BY_BIAS_RISK["low"] == 12


def test_decay_lambda_by_type_constant_exists():
    """DECAY_LAMBDA_BY_TYPE deve existir com valores fast > normal > slow (λ)."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import DECAY_LAMBDA_BY_TYPE
    assert "fast" in DECAY_LAMBDA_BY_TYPE
    assert "normal" in DECAY_LAMBDA_BY_TYPE
    assert "slow" in DECAY_LAMBDA_BY_TYPE
    assert DECAY_LAMBDA_BY_TYPE["fast"] > DECAY_LAMBDA_BY_TYPE["normal"]
    assert DECAY_LAMBDA_BY_TYPE["normal"] > DECAY_LAMBDA_BY_TYPE["slow"]
    # Valores aprovados
    assert abs(DECAY_LAMBDA_BY_TYPE["fast"] - 0.12) < 1e-9
    assert abs(DECAY_LAMBDA_BY_TYPE["normal"] - 0.05) < 1e-9
    assert abs(DECAY_LAMBDA_BY_TYPE["slow"] - 0.02) < 1e-9


# ── Field validity across fixture ────────────────────────────────────────────

VALID_OCEAN = {"O", "C", "E", "A", "N"}
VALID_BIAS_RISK = {"low", "medium", "high"}
VALID_DECAY = {"fast", "normal", "slow"}


def test_all_skills_primary_ocean_is_valid_when_set():
    """Quando primary_ocean está definido, deve ser uma das 5 dimensões OCEAN."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy
    tax = load_taxonomy()
    bad = []
    for parent_id, parent in tax.parents.items():
        for skill in parent.skills:
            if skill.primary_ocean is not None and skill.primary_ocean not in VALID_OCEAN:
                bad.append((parent_id, skill.id, skill.primary_ocean))
    assert not bad, f"primary_ocean inválido: {bad[:5]}"


def test_all_skills_bias_risk_is_valid():
    """bias_risk deve ser low|medium|high em todas as skills."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy
    tax = load_taxonomy()
    bad = []
    for parent_id, parent in tax.parents.items():
        for skill in parent.skills:
            if skill.bias_risk not in VALID_BIAS_RISK:
                bad.append((parent_id, skill.id, skill.bias_risk))
    assert not bad, (
        f"bias_risk inválido em {len(bad)} skills: {bad[:5]}. "
        f"Default deve ser 'medium'."
    )


def test_all_skills_decay_rate_is_valid():
    """decay_rate deve ser fast|normal|slow em todas as skills."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy
    tax = load_taxonomy()
    bad = []
    for parent_id, parent in tax.parents.items():
        for skill in parent.skills:
            if skill.decay_rate not in VALID_DECAY:
                bad.append((parent_id, skill.id, skill.decay_rate))
    assert not bad, (
        f"decay_rate inválido em {len(bad)} skills: {bad[:5]}. "
        f"Default deve ser 'normal'."
    )


# ── Key skill metadata spot checks ───────────────────────────────────────────

def test_ai_ml_skills_have_high_bias_risk_and_fast_decay():
    """Skills de ai_ml_specialist são high bias_risk (correlação de idade)
    e fast decay (tecnologia muda rápido)."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import skills_by_parent
    skills = skills_by_parent("ai_ml_specialist")
    assert skills, "ai_ml_specialist parent deve ter skills"
    high_risk = [s for s in skills if s.bias_risk == "high"]
    fast_decay = [s for s in skills if s.decay_rate == "fast"]
    assert len(high_risk) >= 3, (
        f"Esperado >=3 skills high bias_risk em ai_ml_specialist, "
        f"encontrado {len(high_risk)}: {[s.id for s in high_risk]}"
    )
    assert len(fast_decay) >= 3, (
        f"Esperado >=3 skills fast decay em ai_ml_specialist, "
        f"encontrado {len(fast_decay)}"
    )


def test_health_clinical_skills_have_slow_decay():
    """Skills de saúde são traços humanos estáveis — decay lento."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import skills_by_parent
    skills = skills_by_parent("health_clinical")
    slow = [s for s in skills if s.decay_rate == "slow"]
    assert len(slow) >= 4, (
        f"Esperado >=4 skills slow decay em health_clinical, "
        f"encontrado {len(slow)}: {[s.id for s in slow]}"
    )


def test_culture_ethics_skills_have_slow_decay():
    """Integridade e ética são traços estáveis — decay lento."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import skills_by_parent
    skills = skills_by_parent("culture_ethics_wellbeing")
    slow = [s for s in skills if s.decay_rate == "slow"]
    assert len(slow) >= 2, (
        f"Esperado >=2 skills slow decay em culture_ethics_wellbeing, "
        f"encontrado {len(slow)}"
    )


# ── Helper functions ──────────────────────────────────────────────────────────

def test_get_skills_by_ocean_returns_skills_for_openness():
    """get_skills_by_ocean('O') deve retornar skills mapeadas em Openness."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import get_skills_by_ocean
    skills = get_skills_by_ocean("O")
    assert len(skills) >= 5, (
        f"Esperado >=5 skills mapeadas em O (Openness), encontrado {len(skills)}. "
        "Verificar primary_ocean no JSON para skills de inovação/criatividade/aprendizado."
    )
    ids = {s.id for s in skills}
    # innovation_entrepreneurship skills devem estar em O
    assert any("innov" in sid or "creativ" in sid or "zero" in sid or "experiment" in sid
               for sid in ids), (
        f"Nenhuma skill de inovação encontrada em Openness. IDs: {sorted(ids)[:10]}"
    )


def test_get_skills_by_ocean_returns_empty_for_invalid():
    """get_skills_by_ocean com dimensão inválida deve retornar lista vazia."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import get_skills_by_ocean
    assert get_skills_by_ocean("X") == []
    assert get_skills_by_ocean("") == []


def test_get_skills_by_bias_risk_returns_high_risk_skills():
    """get_skills_by_bias_risk('high') deve retornar skills de alto risco."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import get_skills_by_bias_risk
    skills = get_skills_by_bias_risk("high")
    assert len(skills) >= 3, (
        f"Esperado >=3 skills high bias_risk, encontrado {len(skills)}. "
        "ai_ml_specialist e technical_leadership devem ter skills high."
    )


def test_get_skills_by_bias_risk_low_returns_skills():
    """get_skills_by_bias_risk('low') deve retornar o maior grupo."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import get_skills_by_bias_risk
    low = get_skills_by_bias_risk("low")
    medium = get_skills_by_bias_risk("medium")
    assert len(low) > len(medium), (
        "Maioria das skills deve ser low bias_risk (padrão para soft skills "
        "bem estabelecidas)."
    )


# ── Shared canonical shim (ADR-001) ──────────────────────────────────────────

def test_shared_wsi_skill_taxonomy_shim_importable():
    """app/shared/wsi_skill_taxonomy.py deve existir e re-exportar os símbolos
    canônicos para que services não dependam de import do domain layer."""
    from app.shared.wsi_skill_taxonomy import (
        WsiSkill,
        WsiTaxonomy,
        load_taxonomy,
        find_skill,
        get_skills_by_ocean,
        get_skills_by_bias_risk,
        THRESHOLD_BY_BIAS_RISK,
        DECAY_LAMBDA_BY_TYPE,
    )
    assert callable(load_taxonomy)
    assert callable(find_skill)
    assert THRESHOLD_BY_BIAS_RISK["medium"] == 20


# ── Effectiveness service uses adaptive threshold ────────────────────────────

def test_effectiveness_service_uses_threshold_by_bias_risk():
    """wsi_effectiveness_service deve usar THRESHOLD_BY_BIAS_RISK ao invés
    de comparar hardcoded >=20. Adaptive threshold por bias_risk da skill."""
    import inspect
    from app.domains.job_creation.services import wsi_effectiveness_service as svc
    src = inspect.getsource(svc)
    assert "THRESHOLD_BY_BIAS_RISK" in src or "threshold_by_bias_risk" in src.lower(), (
        "wsi_effectiveness_service ainda usa flat threshold. "
        "Substituir: times_used >= MIN_SAMPLES_FOR_DISCRIMINATION\n"
        "Por: times_used >= THRESHOLD_BY_BIAS_RISK[skill.bias_risk or 'medium']"
    )
