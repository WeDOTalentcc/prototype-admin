"""
Benefits Service - Provides benefit data for AI agents.

This service manages company benefits for:
- JobPlanner agent
- RecruiterAssistant agent
- Sourcer agent
- Entrevistador agent

Features:
- In-memory cache with 5-minute TTL
- Formatting benefits for AI prompts
- Filtering by category, seniority, and highlighting
"""
import logging
import time
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.company.repositories.benefit_repository import BenefitRepository
from lia_models.company import Benefit

logger = logging.getLogger(__name__)


# ============================================================================
# TAXONOMIA CANONICAL v2 (2026-05-24)
# ============================================================================
# Single source of truth para categorias / tipos de valor / carencias.
# Consumidores: endpoint /v1/company_benefits/categories/list,
#               frontend useBenefitTaxonomy hook,
#               LIA wizard prompt formatter,
#               JD publication grouping.
#
# REGRA canonical-fix: NUNCA hardcodar uma segunda lista em outro lugar.
# Adicione/modifique APENAS aqui — endpoint e frontend herdam via API.
# ----------------------------------------------------------------------------

BENEFIT_CATEGORIES: dict[str, str] = {
    "health":      "Saúde",
    "wellness":    "Bem-estar",
    "food":        "Alimentação",
    "transport":   "Transporte",
    "education":   "Educação & Desenvolvimento",
    "financial":   "Financeiro",
    "retirement":  "Previdência",
    "family":      "Família",
    "parental":    "Parental estendido",
    "flexibility": "Flexibilidade & Tempo",
    "equipment":   "Equipamento & Home Office",
    "culture":     "Cultura & Lazer",
    "recognition": "Reconhecimento",
    "other":       "Outros",
}

BENEFIT_CATEGORY_ICONS: dict[str, str] = {
    "health":      "🏥",  # hospital
    "wellness":    "💪",  # flex bicep
    "food":        "🍽️",  # plate with utensils
    "transport":   "🚌",  # bus
    "education":   "📚",  # books
    "financial":   "💰",  # money bag
    "retirement":  "🏛️",  # classical building
    "family":      "👪",  # family
    "parental":    "🤱",  # breast-feeding
    "flexibility": "⏰",      # alarm clock
    "equipment":   "💻",  # laptop
    "culture":     "🎭",  # performing arts
    "recognition": "🏆",  # trophy
    "other":       "📦",  # package
}

# Legacy aliases — categorias v1 absorvidas pela v2.
# Mantidos para backward-compat com dados antigos no banco.
# Sensor: nenhuma nova insercao deve usar essas chaves; o helper
# resolve_benefit_category() normaliza no read path.
BENEFIT_CATEGORY_LEGACY_ALIASES: dict[str, str] = {
    "quality_life": "flexibility",  # absorvido por flexibility + wellness
    "security":     "financial",    # seguro de vida, assist. funeral cabem em financial
}

BENEFIT_VALUE_TYPES: dict[str, str] = {
    "monetary":      "Valor fixo (R$)",
    "percentage":    "Percentual do salário",
    "match":         "Contrapartida da empresa",
    "reimbursement": "Reembolso até limite",
    "coverage":      "Cobertura/franquia",
    "informative":   "Apenas descrição",
}

BENEFIT_VALUE_TYPE_ICONS: dict[str, str] = {
    "monetary":      "DollarSign",
    "percentage":    "Percent",
    "match":         "Repeat",
    "reimbursement": "Receipt",
    "coverage":      "Shield",
    "informative":   "Info",
}

BENEFIT_WAITING_PERIODS: list[dict] = [
    {"id": 0,   "label": "Imediato"},
    {"id": -1,  "label": "Após período de experiência (90 dias)"},
    {"id": 30,  "label": "30 dias"},
    {"id": 60,  "label": "60 dias"},
    {"id": 90,  "label": "90 dias"},
    {"id": 180, "label": "180 dias (6 meses)"},
    {"id": 365, "label": "365 dias (1 ano)"},
    {"id": 540, "label": "540 dias (18 meses)"},
    {"id": 730, "label": "730 dias (2 anos)"},
]


def resolve_benefit_category(category: str | None) -> str:
    """Normaliza categoria: resolve aliases legados, retorna 'other' pra desconhecidos.

    Use no read path para garantir que LIA/UI/JD nunca veem string crua de drift.
    """
    if not category:
        return "other"
    if category in BENEFIT_CATEGORIES:
        return category
    if category in BENEFIT_CATEGORY_LEGACY_ALIASES:
        return BENEFIT_CATEGORY_LEGACY_ALIASES[category]
    return "other"


def build_categories_response() -> list[dict]:
    """Resposta canonical do endpoint /categories/list. Single source of truth."""
    return [
        {"id": k, "name": v, "icon": BENEFIT_CATEGORY_ICONS[k]}
        for k, v in BENEFIT_CATEGORIES.items()
    ]


def build_value_types_response() -> list[dict]:
    """Resposta canonical do endpoint /value-types/list."""
    return [
        {"id": k, "name": v, "icon": BENEFIT_VALUE_TYPE_ICONS[k]}
        for k, v in BENEFIT_VALUE_TYPES.items()
    ]


def build_waiting_periods_response() -> list[dict]:
    """Resposta canonical do endpoint /waiting-periods/list."""
    return list(BENEFIT_WAITING_PERIODS)




class CacheEntry:
    """Cache entry with TTL tracking."""
    
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.created_at) > self.ttl_seconds


class BenefitsCache:
    """In-memory cache for benefits with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any | None:
        """Get cached data if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, data: Any, ttl: int | None = None) -> None:
        """Set cache entry with TTL."""
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(data, ttl)
    
    def invalidate(self, company_id: str) -> None:
        """Invalidate all cache entries for a company."""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{company_id}:")]
        for key in keys_to_delete:
            del self._cache[key]
        logger.info(f"🗑️ Cache invalidated for company {company_id}")
    
    def invalidate_all(self) -> None:
        """Invalidate all cache entries."""
        self._cache.clear()
        logger.info("🗑️ All benefits cache invalidated")


_cache = BenefitsCache(default_ttl=300)


class BenefitsService:
    """
    Service for managing and providing company benefits to AI agents.
    """
    
    def __init__(self):
        self.cache = _cache
    
    async def get_active_benefits(
        self,
        company_id: str,
        db: AsyncSession | None = None
    ) -> list[Benefit]:
        """
        Get all active benefits for a company.
        
        Args:
            company_id: Company ID (UUID string)
            db: Database session (optional)
            
        Returns:
            List of active Benefit objects
        """
        cache_key = f"{company_id}:active"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit for active benefits: {company_id}")
            return cached
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            benefits = await BenefitRepository(db).list_active_ordered(company_id)

            self.cache.set(cache_key, benefits)
            logger.info(f"✅ Loaded {len(benefits)} active benefits for company {company_id}")
            
            return benefits
            
        except Exception as e:
            logger.error(f"❌ Error fetching active benefits: {e}")
            return []
            
        finally:
            if should_close:
                await db.close()
    
    async def get_highlighted_benefits(
        self,
        company_id: str,
        db: AsyncSession | None = None
    ) -> list[Benefit]:
        """
        Get highlighted/featured benefits for a company.
        
        Args:
            company_id: Company ID (UUID string)
            db: Database session (optional)
            
        Returns:
            List of highlighted Benefit objects
        """
        cache_key = f"{company_id}:highlighted"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit for highlighted benefits: {company_id}")
            return cached
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            benefits = await BenefitRepository(db).list_highlighted(company_id)

            self.cache.set(cache_key, benefits)
            logger.info(f"⭐ Loaded {len(benefits)} highlighted benefits for company {company_id}")
            
            return benefits
            
        except Exception as e:
            logger.error(f"❌ Error fetching highlighted benefits: {e}")
            return []
            
        finally:
            if should_close:
                await db.close()
    
    async def get_benefits_by_category(
        self,
        company_id: str,
        category: str,
        db: AsyncSession | None = None
    ) -> list[Benefit]:
        """
        Get benefits filtered by category.
        
        Args:
            company_id: Company ID (UUID string)
            category: Category key (e.g., 'health', 'food', 'transport')
            db: Database session (optional)
            
        Returns:
            List of Benefit objects in the specified category
        """
        cache_key = f"{company_id}:category:{category}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit for category benefits: {company_id}:{category}")
            return cached
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            benefits = await BenefitRepository(db).list_by_category(company_id, category)

            self.cache.set(cache_key, benefits)
            category_name = BENEFIT_CATEGORIES.get(category, category)
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"📂 Loaded {len(benefits)} benefits in category '{category_name}' for company {company_id}")
            
            return benefits
            
        except Exception as e:
            logger.error(f"❌ Error fetching benefits by category: {e}")
            return []
            
        finally:
            if should_close:
                await db.close()
    
    async def get_benefits_by_seniority(
        self,
        company_id: str,
        seniority_level: str,
        db: AsyncSession | None = None
    ) -> list[Benefit]:
        """
        Get benefits filtered by seniority level.
        
        Args:
            company_id: Company ID (UUID string)
            seniority_level: Seniority level (e.g., 'junior', 'pleno', 'senior')
            db: Database session (optional)
            
        Returns:
            List of Benefit objects applicable to the seniority level
        """
        cache_key = f"{company_id}:seniority:{seniority_level}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit for seniority benefits: {company_id}:{seniority_level}")
            return cached
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            all_benefits = await BenefitRepository(db).list_active_ordered(company_id)
            
            benefits = []
            for benefit in all_benefits:
                seniority_levels = benefit.seniority_levels or []
                if not seniority_levels or seniority_level.lower() in [s.lower() for s in seniority_levels]:
                    benefits.append(benefit)
            
            self.cache.set(cache_key, benefits)
            logger.info(f"🎯 Loaded {len(benefits)} benefits for seniority '{seniority_level}' at company {company_id}")
            
            return benefits
            
        except Exception as e:
            logger.error(f"❌ Error fetching benefits by seniority: {e}")
            return []
            
        finally:
            if should_close:
                await db.close()
    
    def format_for_ai_prompt(self, benefits: list[Benefit]) -> str:
        """
        Format benefits list for use in AI prompts.
        
        Args:
            benefits: List of Benefit objects
            
        Returns:
            Formatted string for AI prompt consumption
            
        Example output:
            **Benefícios da Empresa:**
            - Saúde & Bem-estar: Plano de Saúde (R$ 800,00/mês), Vale Farmácia (50% desconto)
            - Alimentação: Vale Refeição (R$ 35,00/dia), Vale Alimentação (R$ 600,00/mês)
        """
        if not benefits:
            return "**Benefícios da Empresa:**\n- Nenhum benefício cadastrado."
        
        benefits_by_category: dict[str, list[str]] = {}
        
        for benefit in benefits:
            category_key = benefit.category or "other"
            category_name = BENEFIT_CATEGORIES.get(category_key, category_key.title())
            
            if category_name not in benefits_by_category:
                benefits_by_category[category_name] = []
            
            formatted_benefit = self._format_single_benefit(benefit)
            benefits_by_category[category_name].append(formatted_benefit)
        
        lines = ["**Benefícios da Empresa:**"]
        
        category_order = list(BENEFIT_CATEGORIES.values())
        sorted_categories = sorted(
            benefits_by_category.keys(),
            key=lambda x: category_order.index(x) if x in category_order else 999
        )
        
        for category in sorted_categories:
            benefits_list = benefits_by_category[category]
            line = f"- {category}: {', '.join(benefits_list)}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _format_single_benefit(self, benefit: Benefit) -> str:
        """
        Format a single benefit for display.
        
        Args:
            benefit: Benefit object
            
        Returns:
            Formatted string (e.g., "Plano de Saúde (R$ 800,00/mês)")
        """
        name = benefit.name
        value_type = benefit.value_type or "informative"
        
        if value_type == "monetary" and benefit.value:
            value_str = f"R$ {benefit.value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            details = benefit.value_details or ""
            if details:
                return f"{name} ({value_str}/{details})"
            else:
                return f"{name} ({value_str})"
        
        elif value_type == "percentage" and benefit.percentage_value:
            percentage = benefit.percentage_value
            if benefit.is_discount:
                return f"{name} ({percentage:.0f}% desconto)"
            else:
                return f"{name} ({percentage:.0f}%)"
        
        elif benefit.value_details:
            return f"{name} ({benefit.value_details})"
        
        else:
            return name
    
    async def get_benefits_summary(
        self,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get a summary of benefits with counts by category.
        
        Args:
            company_id: Company ID (UUID string)
            db: Database session (optional)
            
        Returns:
            Dictionary with summary statistics:
            {
                "total": 15,
                "highlighted": 5,
                "by_category": {
                    "health": {"count": 3, "name": "Saúde & Bem-estar"},
                    "food": {"count": 2, "name": "Alimentação"},
                    ...
                },
                "mandatory_count": 4,
                "discount_count": 2
            }
        """
        cache_key = f"{company_id}:summary"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"📦 Cache hit for benefits summary: {company_id}")
            return cached
        
        benefits = await self.get_active_benefits(company_id, db)
        
        by_category: dict[str, dict[str, Any]] = {}
        for category_key, category_name in BENEFIT_CATEGORIES.items():
            by_category[category_key] = {
                "count": 0,
                "name": category_name
            }
        
        highlighted_count = 0
        mandatory_count = 0
        discount_count = 0
        
        for benefit in benefits:
            category_key = benefit.category or "other"
            if category_key in by_category:
                by_category[category_key]["count"] += 1
            else:
                by_category[category_key] = {
                    "count": 1,
                    "name": category_key.title()
                }
            
            if benefit.is_highlighted:
                highlighted_count += 1
            if benefit.is_mandatory:
                mandatory_count += 1
            if benefit.is_discount:
                discount_count += 1
        
        summary = {
            "total": len(benefits),
            "highlighted": highlighted_count,
            "by_category": by_category,
            "mandatory_count": mandatory_count,
            "discount_count": discount_count,
            "company_id": company_id,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        self.cache.set(cache_key, summary)
        logger.info(f"📊 Generated benefits summary for company {company_id}: {len(benefits)} total benefits")
        
        return summary
    
    def invalidate_cache(self, company_id: str) -> None:
        """
        Invalidate cache for a specific company.
        Call this when benefits are modified.
        
        Args:
            company_id: Company ID (UUID string)
        """
        self.cache.invalidate(company_id)
    
    def invalidate_all_cache(self) -> None:
        """
        Invalidate all cached benefits.
        """
        self.cache.invalidate_all()
    
    async def get_benefits_for_job_posting(
        self,
        company_id: str,
        seniority_level: str | None = None,
        department: str | None = None,
        db: AsyncSession | None = None
    ) -> str:
        """
        Get formatted benefits for a job posting.
        Convenience method for agents creating job vacancies.
        
        Args:
            company_id: Company ID
            seniority_level: Optional seniority filter
            department: Optional department filter
            db: Database session
            
        Returns:
            Formatted string suitable for job descriptions
        """
        if seniority_level:
            benefits = await self.get_benefits_by_seniority(company_id, seniority_level, db)
        else:
            benefits = await self.get_active_benefits(company_id, db)
        
        if department:
            benefits = [
                b for b in benefits
                if not b.departments or department in (b.departments or [])
            ]
        
        return self.format_for_ai_prompt(benefits)
    
    async def get_highlighted_benefits_text(
        self,
        company_id: str,
        db: AsyncSession | None = None
    ) -> str:
        """
        Get formatted highlighted benefits for quick display.
        Useful for chat responses and sourcing messages.
        
        Args:
            company_id: Company ID
            db: Database session
            
        Returns:
            Formatted string with highlighted benefits
        """
        benefits = await self.get_highlighted_benefits(company_id, db)
        
        if not benefits:
            return "Destaques: Benefícios competitivos disponíveis."
        
        benefit_names = [self._format_single_benefit(b) for b in benefits[:5]]
        
        return f"🌟 Destaques: {', '.join(benefit_names)}"


benefits_service = BenefitsService()
