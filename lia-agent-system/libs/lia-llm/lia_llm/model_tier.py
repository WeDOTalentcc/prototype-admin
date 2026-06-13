"""
ModelTierResolver — resolve qual modelo LLM usar baseado em domínio + confiança.

Extraído de app/shared/llm/model_tier_resolver.py para libs/lia-llm.
O módulo original é mantido como shim de retrocompatibilidade.

Harness: Guide computacional — determina o modelo ANTES da chamada LLM.
O modelo de negócio (agente) não decide qual LLM usar; o harness decide.

Tiers:
  fast     → CANONICAL_HAIKU_MODEL (barato, classificação, chat)
  standard → CANONICAL_SONNET_MODEL (mid-tier, screening, geração)
  heavy    → modelo mais poderoso disponível (decisões críticas, fallback por baixa confiança)

Escalada automática por confiança:
  Se confidence < threshold do domínio → escala para tier superior
  Ex: screening (standard, threshold=0.75) com confidence=0.50 → heavy
"""
from __future__ import annotations

import logging
from typing import Any

from lia_llm.models import CANONICAL_HAIKU_MODEL, CANONICAL_SONNET_MODEL

logger = logging.getLogger(__name__)

# ── Constantes de tier ────────────────────────────────────────────────────────

TIER_FAST = "fast"
TIER_STANDARD = "standard"
TIER_HEAVY = "heavy"

# Mapeamento tier → modelo canônico (single source of truth)
MODEL_TIERS: dict[str, str] = {
    TIER_FAST:     CANONICAL_HAIKU_MODEL,
    TIER_STANDARD: CANONICAL_SONNET_MODEL,
    TIER_HEAVY:    CANONICAL_SONNET_MODEL,  # escalada máxima = sonnet (opus quando disponível)
}

# Escalada: fast → standard → heavy
_TIER_ESCALATION: dict[str, str] = {
    TIER_FAST:     TIER_STANDARD,
    TIER_STANDARD: TIER_HEAVY,
    TIER_HEAVY:    TIER_HEAVY,  # já no máximo
}

# ── Políticas padrão por domínio ──────────────────────────────────────────────

DOMAIN_TIER_DEFAULTS: dict[str, dict[str, Any]] = {
    # Domínios de classificação (rápidos, baixo custo, alta tolerância a erros)
    "classification": {"tier": TIER_FAST,     "threshold": 0.80},
    "navigation":     {"tier": TIER_FAST,     "threshold": 0.85},
    "intent":         {"tier": TIER_FAST,     "threshold": 0.80},

    # Domínios de sourcing e comunicação
    "sourcing":       {"tier": TIER_FAST,     "threshold": 0.85},
    "communication":  {"tier": TIER_FAST,     "threshold": 0.90},

    # Domínios de screening e avaliação (precisão importa)
    "screening":      {"tier": TIER_STANDARD, "threshold": 0.75},
    "evaluation":     {"tier": TIER_STANDARD, "threshold": 0.70},
    "scoring":        {"tier": TIER_STANDARD, "threshold": 0.75},

    # Domínios de criação e decisão (qualidade crítica)
    "job_creation":   {"tier": TIER_STANDARD, "threshold": 0.75},
    "offer":          {"tier": TIER_STANDARD, "threshold": 0.80},
    "hiring_policy":  {"tier": TIER_STANDARD, "threshold": 0.75},

    # Default para domínios não mapeados
    "default":        {"tier": TIER_STANDARD, "threshold": 0.75},
}


class ModelTierResolver:
    """
    Resolve o modelo LLM correto para um domínio + nível de confiança.

    Uso:
        resolver = ModelTierResolver()
        model = resolver.resolve(domain="screening", confidence=0.82)
        # → CANONICAL_SONNET_MODEL (standard, confidence ok)

        model = resolver.resolve(domain="screening", confidence=0.50)
        # → MODEL_TIERS["heavy"] (escalado: 0.50 < threshold 0.75)

        model = resolver.resolve(
            domain="communication",
            confidence=0.95,
            tenant_tier_policy={"communication": {"tier": "heavy", "threshold": 0.70}}
        )
        # → MODEL_TIERS["heavy"] (tenant override)
    """

    def resolve(
        self,
        domain: str | None,
        confidence: float | None,
        tenant_tier_policy: dict[str, dict] | None = None,
    ) -> str:
        """
        Resolve o nome do modelo para (domain, confidence).

        Args:
            domain: Domínio da operação (ex: "screening", "sourcing").
            confidence: Score de confiança 0.0-1.0. None = usa tier padrão sem escalada.
            tenant_tier_policy: Override por tenant {domain: {tier, threshold}}.

        Returns:
            Nome do modelo (string). Nunca lança exceção (fail-safe = CANONICAL_HAIKU_MODEL).
        """
        try:
            # Normalizar inputs
            domain_key = (domain or "").lower().strip() or "default"
            conf = float(confidence) if confidence is not None else None

            # Determinar política efetiva (tenant override > padrão)
            policy = self._effective_policy(domain_key, tenant_tier_policy)
            base_tier = policy["tier"]
            threshold = policy["threshold"]

            # Escalada por confiança
            if conf is not None and conf < threshold:
                final_tier = _TIER_ESCALATION.get(base_tier, base_tier)
                logger.debug(
                    "[ModelTierResolver] domain=%s confidence=%.2f < threshold=%.2f "
                    "→ escalate %s → %s",
                    domain_key, conf, threshold, base_tier, final_tier,
                )
            else:
                final_tier = base_tier

            model = MODEL_TIERS.get(final_tier, CANONICAL_HAIKU_MODEL)
            logger.debug(
                "[ModelTierResolver] domain=%s confidence=%s tier=%s model=%s",
                domain_key, f"{conf:.2f}" if conf is not None else "N/A", final_tier, model,
            )
            return model

        except Exception as exc:
            logger.warning(
                "[ModelTierResolver] resolve failed (fail-safe haiku): %s", exc
            )
            return CANONICAL_HAIKU_MODEL

    def _effective_policy(
        self,
        domain: str,
        tenant_override: dict[str, dict] | None,
    ) -> dict[str, Any]:
        """Retorna a política efetiva para o domínio (tenant override > padrão)."""
        if tenant_override and domain in tenant_override:
            override = tenant_override[domain]
            tier = override.get("tier", TIER_STANDARD)
            threshold = float(override.get("threshold", 0.75))
            if tier in MODEL_TIERS:
                return {"tier": tier, "threshold": threshold}

        return DOMAIN_TIER_DEFAULTS.get(domain, DOMAIN_TIER_DEFAULTS["default"])


# Singleton
_resolver: ModelTierResolver | None = None


def get_model_tier_resolver() -> ModelTierResolver:
    global _resolver
    if _resolver is None:
        _resolver = ModelTierResolver()
    return _resolver


def resolve_model_tier(
    domain: str | None = None,
    confidence: float | None = None,
    tenant_tier_policy: dict | None = None,
) -> str:
    """Convenience function — resolve sem instanciar explicitamente."""
    return get_model_tier_resolver().resolve(domain, confidence, tenant_tier_policy)
