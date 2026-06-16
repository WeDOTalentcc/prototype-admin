"""
ThresholdResolver — cascata canônica para thresholds de aprovação de screening.

Hierarquia (mais restrito vence):
  1. Mínimo da plataforma (fairness_policy_rules, platform_general, decision_threshold)
  2. Padrão do setor (fairness_policy_rules, platform_domain/screening, decision_threshold)
  3. Configuração do tenant (company_hiring_policies.screening_rules)
  4. Fallback hardcoded (emergência — DB indisponível)

Compliance: EU AI Act Art.14 + LGPD Art.6 VII
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Fallback de emergência — usado APENAS se DB e fairness_policy_service falharem
_HARDCODED_FALLBACK = {
    "auto_approve": 0.75,   # 75% normalizado
    "review": 0.55,         # 55% normalizado
}

# Mapeamento score 0-100 → threshold 0.0-1.0
# score 75 = confidence 0.75


async def resolve_screening_thresholds(
    company_id: str | None,
    sector: str | None,
    db: "AsyncSession",
) -> dict:
    """
    Resolve thresholds de screening para um tenant/setor específico.

    Returns:
        {
            "auto_approve": float,  # 0.0-1.0 — aprovar automaticamente se confidence >= este valor
            "review": float,        # 0.0-1.0 — enviar para revisão se confidence >= este valor
            "source": str,          # "tenant" | "sector" | "platform" | "fallback"
        }
    """
    platform_floor = await _get_platform_floor(sector, db)
    tenant_config = await _get_tenant_config(company_id, db) if company_id else {}

    # Regra de merge: mais restrito vence (tenant pode só endurecer, nunca afrouxar)
    auto_approve = platform_floor["auto_approve"]
    review = platform_floor["review"]
    source = platform_floor.get("source", "platform")

    tenant_auto = tenant_config.get("auto_approve_threshold")
    tenant_review = tenant_config.get("review_threshold")

    if tenant_auto is not None:
        try:
            tenant_auto_f = float(tenant_auto)
            if tenant_auto_f >= auto_approve:
                # Tenant endurece o threshold (mais restrito) — permitido
                auto_approve = tenant_auto_f
                source = "tenant"
            else:
                # Tenant tenta afrouxar — recusa silenciosamente, usa plataforma
                logger.warning(
                    "[ThresholdResolver] Tenant %s tentou afrouxar auto_approve_threshold "
                    "para %.2f (plataforma mínimo: %.2f). Usando plataforma.",
                    company_id, tenant_auto_f, auto_approve,
                )
        except (ValueError, TypeError):
            pass

    if tenant_review is not None:
        try:
            tenant_review_f = float(tenant_review)
            # review deve ser < auto_approve e >= 0
            if 0.0 <= tenant_review_f < auto_approve:
                review = tenant_review_f
        except (ValueError, TypeError):
            pass

    return {
        "auto_approve": auto_approve,
        "review": review,
        "source": source,
    }


async def _get_platform_floor(sector: str | None, db: "AsyncSession") -> dict:
    """
    Carrega o threshold mínimo da plataforma da fairness_policy_rules.
    Layer 1 (platform_general) + Layer 2 (platform_domain/screening, por setor se informado).
    """
    try:
        from app.shared.compliance.fairness_policy_service import _get_fairness_service
        svc = _get_fairness_service()

        # Layer 1: platform_general
        platform_policy = await svc.load_effective_policy(
            tenant_id=None, domain="screening", db=db
        )

        # Encontra a regra de decision_threshold platform_general
        platform_min = 0.75  # fallback se não encontrar
        sector_auto = None
        sector_review = None

        for rule in platform_policy.get("decision_threshold", []):
            body = rule.get("body_json", {})
            scope = rule.get("scope", "")

            if scope == "platform_general":
                platform_min = body.get("min_confidence", 0.75)

            elif scope == "platform_domain" and body.get("sectors"):
                # Regra 9 do seed: thresholds por setor
                sectors = body.get("sectors", {})
                sector_key = (sector or "default").lower().strip()
                sector_cfg = sectors.get(sector_key, sectors.get("default", {}))
                if sector_cfg:
                    sector_auto = sector_cfg.get("auto_approve_threshold")
                    hitl = sector_cfg.get("hitl_threshold")
                    if hitl:
                        sector_review = hitl

        # Monta o floor: sector > platform_general
        auto_approve = sector_auto if sector_auto is not None else platform_min
        review = sector_review if sector_review is not None else (platform_min * 0.73)

        # Garante que auto_approve >= platform_min (floor absoluto)
        auto_approve = max(auto_approve, platform_min)
        review = min(review, auto_approve - 0.01)  # review sempre < auto_approve

        source = "sector" if sector_auto is not None else "platform"
        return {"auto_approve": auto_approve, "review": review, "source": source}

    except Exception as exc:
        logger.warning(
            "[ThresholdResolver] Não foi possível carregar platform floor "
            "(usando fallback hardcoded): %s", exc
        )
        return {**_HARDCODED_FALLBACK, "source": "fallback"}


async def _get_tenant_config(company_id: str, db: "AsyncSession") -> dict:
    """
    Carrega configuração de threshold do tenant via CompanyHiringPolicy.screening_rules.
    Retorna dict vazio se tenant não configurou.
    """
    try:
        from sqlalchemy import select
        from lia_models.company_hiring_policy import CompanyHiringPolicy

        result = await db.execute(
            select(CompanyHiringPolicy).where(
                CompanyHiringPolicy.company_id == str(company_id)
            )
        )
        policy = result.scalar_one_or_none()
        if policy is None:
            return {}

        screening_rules = policy.screening_rules or {}
        return {
            "auto_approve_threshold": screening_rules.get("auto_approve_threshold"),
            "review_threshold": screening_rules.get("review_threshold"),
            "sector": screening_rules.get("sector"),
        }

    except Exception as exc:
        logger.debug("[ThresholdResolver] tenant config unavailable: %s", exc)
        return {}
