"""Sprint D — ModelTierResolver — contrato TDD."""
import pytest


# ─── GRUPO 1: Tiers canônicos ────────────────────────────────────────────────

def test_tier_constants_importable():
    """Constantes de tier devem ser importáveis."""
    from app.shared.llm.model_tier_resolver import (
        TIER_FAST, TIER_STANDARD, TIER_HEAVY,
        MODEL_TIERS,
    )
    assert TIER_FAST == "fast"
    assert TIER_STANDARD == "standard"
    assert TIER_HEAVY == "heavy"
    assert TIER_FAST in MODEL_TIERS
    assert TIER_STANDARD in MODEL_TIERS
    assert TIER_HEAVY in MODEL_TIERS


def test_model_tiers_map_to_canonical_models():
    """MODEL_TIERS deve mapear para modelos canônicos definidos em llm_models.py."""
    from app.shared.llm.model_tier_resolver import MODEL_TIERS
    from app.shared.llm_models import CANONICAL_HAIKU_MODEL, CANONICAL_SONNET_MODEL
    # fast = haiku (barato)
    assert MODEL_TIERS["fast"] == CANONICAL_HAIKU_MODEL
    # standard = sonnet (mid-tier)
    assert MODEL_TIERS["standard"] == CANONICAL_SONNET_MODEL
    # heavy = sonnet ou opus (mais pesado disponível)
    assert MODEL_TIERS["heavy"] in (CANONICAL_SONNET_MODEL, "claude-opus-4-5", "claude-opus-4")


def test_domain_defaults_importable():
    """DOMAIN_TIER_DEFAULTS deve ter domínios principais."""
    from app.shared.llm.model_tier_resolver import DOMAIN_TIER_DEFAULTS
    required_domains = {"screening", "sourcing", "communication", "classification", "default"}
    missing = required_domains - set(DOMAIN_TIER_DEFAULTS.keys())
    assert not missing, f"Domínios faltando em DOMAIN_TIER_DEFAULTS: {missing}"


def test_domain_defaults_have_tier_and_threshold():
    """Cada entrada em DOMAIN_TIER_DEFAULTS deve ter tier e threshold."""
    from app.shared.llm.model_tier_resolver import DOMAIN_TIER_DEFAULTS, TIER_FAST, TIER_STANDARD, TIER_HEAVY
    valid_tiers = {TIER_FAST, TIER_STANDARD, TIER_HEAVY}
    for domain, cfg in DOMAIN_TIER_DEFAULTS.items():
        assert "tier" in cfg, f"Domínio {domain} sem tier"
        assert "threshold" in cfg, f"Domínio {domain} sem threshold"
        assert cfg["tier"] in valid_tiers, f"Tier inválido em {domain}: {cfg[tier]}"
        assert 0.0 <= cfg["threshold"] <= 1.0, f"Threshold inválido em {domain}: {cfg[threshold]}"


# ─── GRUPO 2: resolve_model_tier() — lógica de resolução ────────────────────

def test_resolver_importable():
    """ModelTierResolver deve ser importável."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver
    resolver = ModelTierResolver()
    assert hasattr(resolver, "resolve")


def test_resolver_returns_fast_model_for_fast_domain():
    """Domínio classification (fast) com confidence alta → haiku."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, MODEL_TIERS
    resolver = ModelTierResolver()
    model = resolver.resolve(domain="classification", confidence=0.95)
    assert model == MODEL_TIERS["fast"]


def test_resolver_returns_standard_for_screening():
    """Domínio screening (standard) com confidence ok → sonnet."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, MODEL_TIERS
    resolver = ModelTierResolver()
    model = resolver.resolve(domain="screening", confidence=0.85)
    assert model == MODEL_TIERS["standard"]


def test_resolver_escalates_when_confidence_below_threshold():
    """confidence < threshold → escala para tier superior."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, MODEL_TIERS
    resolver = ModelTierResolver()
    # screening padrão: tier=standard, threshold=0.75
    # confidence=0.50 < 0.75 → escala para heavy
    model = resolver.resolve(domain="screening", confidence=0.50)
    assert model == MODEL_TIERS["heavy"]


def test_resolver_no_escalation_when_confidence_at_threshold():
    """confidence == threshold → não escala (boundary)."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, MODEL_TIERS, DOMAIN_TIER_DEFAULTS
    resolver = ModelTierResolver()
    screening_threshold = DOMAIN_TIER_DEFAULTS["screening"]["threshold"]
    model = resolver.resolve(domain="screening", confidence=screening_threshold)
    assert model == MODEL_TIERS["standard"]  # não escalou


def test_resolver_uses_default_for_unknown_domain():
    """Domínio desconhecido → usa DOMAIN_TIER_DEFAULTS[default]."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, DOMAIN_TIER_DEFAULTS, MODEL_TIERS
    resolver = ModelTierResolver()
    default_tier = DOMAIN_TIER_DEFAULTS["default"]["tier"]
    model = resolver.resolve(domain="unknown_domain_xyz", confidence=0.90)
    assert model == MODEL_TIERS[default_tier]


def test_resolver_accepts_tenant_override():
    """Tenant pode sobrescrever o tier para um domínio."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, MODEL_TIERS
    resolver = ModelTierResolver()
    # Tenant quer usar "heavy" para communication (padrão é "fast")
    tenant_policy = {"communication": {"tier": "heavy", "threshold": 0.70}}
    model = resolver.resolve(domain="communication", confidence=0.95, tenant_tier_policy=tenant_policy)
    assert model == MODEL_TIERS["heavy"]


def test_resolver_fail_safe_on_invalid_input():
    """domain=None e confidence=None -> usa default domain (standard tier)."""
    from app.shared.llm.model_tier_resolver import ModelTierResolver, MODEL_TIERS, DOMAIN_TIER_DEFAULTS
    resolver = ModelTierResolver()
    model = resolver.resolve(domain=None, confidence=None)
    # None -> "default" domain -> tier padrao (standard)
    default_tier = DOMAIN_TIER_DEFAULTS["default"]["tier"]
    assert model == MODEL_TIERS[default_tier]


# ─── GRUPO 3: Sensor ─────────────────────────────────────────────────────────

def test_llm_tier_sensor_exists():
    """Sensor check_llm_hardcoded_models.py deve existir."""
    from pathlib import Path
    sensor = Path("scripts/check_llm_hardcoded_models.py")
    assert sensor.exists(), (
        "scripts/check_llm_hardcoded_models.py deve existir. "
        "CORREÇÃO: criar sensor AST que detecta model= hardcoded em chamadas LLM."
    )
