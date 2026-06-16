"""
Compensation Analysis Service - Analyzes proposed compensation packages.

This service compares proposed compensation (salary, bonus, benefits) against:
- Company compensation policies
- Market benchmarks
- Historical internal data

Provides recommendations and identifies misalignments.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID as UUID_type

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.analytics.services.job_insights_service import JobInsightsService
from lia_models.compensation_policy import CompensationPolicy
from app.schemas.compensation_analysis import (
    BenefitAnalysis,
    BonusAnalysis,
    CompensationAlignmentStatus,
    CompensationAnalysisResult,
    DataSource,
    SalaryAnalysis,
    TotalCompAnalysis,
)
from app.domains.company.services.company_configuration_service import CompanyConfigurationService
from app.shared.services.market_benchmark_service import MarketBenchmarkService

logger = logging.getLogger(__name__)


def _to_uuid(value: str) -> UUID_type | None:
    """Convert string to UUID, returns None if invalid."""
    try:
        return UUID_type(value)
    except (ValueError, TypeError):
        return None


BENEFIT_ANNUAL_VALUES = {
    "vale refeição": 550 * 12,
    "vale alimentação": 600 * 12,
    "vale transporte": 300 * 12,
    "plano de saúde": 800 * 12,
    "plano odontológico": 80 * 12,
    "seguro de vida": 100 * 12,
    "gympass": 150 * 12,
    "auxílio home office": 200 * 12,
    "auxílio creche": 500 * 12,
    "previdência privada": 500 * 12,
    "participação nos lucros": 0,
    "bônus anual": 0,
    "stock options": 0,
}


class CompensationAnalysisService:
    """
    Service for analyzing compensation packages against policies and market data.
    
    Features:
    - Policy lookup by role/seniority/department
    - Market benchmark comparison
    - Benefits monetization
    - Total compensation calculation
    - Alignment assessment with recommendations
    """
    
    MONTHS_PER_YEAR = 12
    ALIGNMENT_TOLERANCE_PCT = 0.10
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.market_benchmark_service = MarketBenchmarkService()
        self.company_config_service = CompanyConfigurationService()
        self.job_insights_service = JobInsightsService()
    
    async def analyze_compensation(
        self,
        company_id: str,
        job_title: str,
        seniority: str,
        department: str | None = None,
        location: str | None = None,
        proposed_salary_min: float | None = None,
        proposed_salary_max: float | None = None,
        proposed_bonus_pct: float | None = None,
        proposed_benefits: list[str] | None = None,
        db: AsyncSession | None = None
    ) -> CompensationAnalysisResult:
        """
        Analyze proposed compensation against company policy and market data.
        
        Args:
            company_id: Company identifier
            job_title: Job title/role
            seniority: Seniority level (Júnior, Pleno, Sênior, etc.)
            department: Department name (optional)
            location: Location for market comparison (optional)
            proposed_salary_min: Proposed minimum salary (monthly)
            proposed_salary_max: Proposed maximum salary (monthly)
            proposed_bonus_pct: Proposed bonus percentage
            proposed_benefits: List of proposed benefit names
            db: Optional database session
        
        Returns:
            CompensationAnalysisResult with complete analysis
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Analyzing compensation for {job_title} ({seniority}) at company {company_id}")
        
        data_sources_used: list[DataSource] = []
        alerts: list[str] = []
        recommendations: list[str] = []
        
        if db:
            return await self._perform_analysis(
                db=db,
                company_id=company_id,
                job_title=job_title,
                seniority=seniority,
                department=department,
                location=location,
                proposed_salary_min=proposed_salary_min,
                proposed_salary_max=proposed_salary_max,
                proposed_bonus_pct=proposed_bonus_pct,
                proposed_benefits=proposed_benefits or [],
                data_sources_used=data_sources_used,
                alerts=alerts,
                recommendations=recommendations
            )
        else:
            async with AsyncSessionLocal() as session:
                return await self._perform_analysis(
                    db=session,
                    company_id=company_id,
                    job_title=job_title,
                    seniority=seniority,
                    department=department,
                    location=location,
                    proposed_salary_min=proposed_salary_min,
                    proposed_salary_max=proposed_salary_max,
                    proposed_bonus_pct=proposed_bonus_pct,
                    proposed_benefits=proposed_benefits or [],
                    data_sources_used=data_sources_used,
                    alerts=alerts,
                    recommendations=recommendations
                )
    
    async def _perform_analysis(
        self,
        db: AsyncSession,
        company_id: str,
        job_title: str,
        seniority: str,
        department: str | None,
        location: str | None,
        proposed_salary_min: float | None,
        proposed_salary_max: float | None,
        proposed_bonus_pct: float | None,
        proposed_benefits: list[str],
        data_sources_used: list[DataSource],
        alerts: list[str],
        recommendations: list[str]
    ) -> CompensationAnalysisResult:
        """Execute the complete compensation analysis."""
        
        policy = await self._get_company_policy(
            db=db,
            company_id=company_id,
            job_title=job_title,
            seniority=seniority,
            department=department
        )
        
        if policy:
            data_sources_used.append(DataSource.COMPANY_POLICY)
        
        market_data = await self._get_market_data(
            company_id=company_id,
            job_title=job_title,
            seniority=seniority,
            location=location
        )
        
        if market_data and market_data.get("min") is not None:
            data_sources_used.append(DataSource.MARKET_BENCHMARK)
        
        company_config = await self.company_config_service.get_configuration(
            company_id=company_id,
            db=db,
            allow_default_fallback=True
        )
        
        company_benefits = company_config.benefits if company_config else []
        
        salary_analysis = self._analyze_salary(
            proposed_min=proposed_salary_min,
            proposed_max=proposed_salary_max,
            policy=policy,
            market_data=market_data,
            alerts=alerts,
            recommendations=recommendations,
            data_sources=data_sources_used
        )
        
        bonus_analysis = self._analyze_bonus(
            proposed_pct=proposed_bonus_pct,
            policy=policy,
            alerts=alerts,
            recommendations=recommendations
        )
        
        benefits_analysis = self._analyze_benefits(
            proposed_benefits=proposed_benefits,
            company_benefits=company_benefits,
            seniority=seniority,
            alerts=alerts,
            recommendations=recommendations
        )
        
        total_comp = self._calculate_total_comp(
            salary_analysis=salary_analysis,
            bonus_analysis=bonus_analysis,
            benefits_analysis=benefits_analysis,
            policy=policy,
            market_data=market_data
        )
        
        result = self._build_result(
            salary_analysis=salary_analysis,
            bonus_analysis=bonus_analysis,
            benefits_analysis=benefits_analysis,
            total_comp=total_comp,
            data_sources_used=data_sources_used,
            alerts=alerts,
            recommendations=recommendations,
            job_title=job_title,
            seniority=seniority
        )
        
        return result
    
    async def _get_company_policy(
        self,
        db: AsyncSession,
        company_id: str,
        job_title: str,
        seniority: str,
        department: str | None = None
    ) -> dict[str, Any] | None:
        """
        Find matching compensation policy for role/seniority/department.
        
        Matching priority:
        1. Exact match on role_pattern + seniority + department
        2. Match on role_pattern + seniority
        3. Match on seniority + department
        4. Match on seniority only
        """
        try:
            company_uuid = _to_uuid(company_id)
            if not company_uuid:
                self.logger.warning(f"Invalid company_id: {company_id}")
                return None
            
            now = datetime.utcnow()
            
            base_conditions = [
                CompensationPolicy.company_id == company_uuid,
                CompensationPolicy.is_active,
                or_(
                    CompensationPolicy.effective_from.is_(None),
                    CompensationPolicy.effective_from <= now
                ),
            # ADR-001-EXEMPT: single-row CompensationPolicy lookup; CompensationPolicyRepository pending Sprint 6 follow-up
                or_(
                    CompensationPolicy.effective_until.is_(None),
                    CompensationPolicy.effective_until >= now
                )
            ]
            
            job_title_lower = job_title.lower()
            seniority_lower = seniority.lower()
            
            # TENANT-EXEMPT: dynamic builder — base_conditions[0] is CompensationPolicy.company_id == company_uuid (declared above); AST sensor cannot trace dynamic conditions
            query = select(CompensationPolicy).where(
                and_(*base_conditions)
            ).order_by(CompensationPolicy.created_at.desc())
            
            result = await db.execute(query)
            policies = result.scalars().all()
            
            best_match: CompensationPolicy | None = None
            best_score = 0
            
            for policy in policies:
                score = 0
                
                role_pattern = str(policy.role_pattern) if policy.role_pattern is not None else None
                sen_level = str(policy.seniority_level) if policy.seniority_level is not None else None
                dept = str(policy.department) if policy.department is not None else None
                
                if role_pattern:
                    pattern_lower = role_pattern.lower()
                    if pattern_lower in job_title_lower or job_title_lower in pattern_lower:
                        score += 40
                    elif any(word in job_title_lower for word in pattern_lower.split()):
                        score += 20
                
                if sen_level:
                    if sen_level.lower() == seniority_lower:
                        score += 30
                    elif self._seniority_match_partial(sen_level, seniority):
                        score += 15
                
                if department and dept:
                    if dept.lower() == department.lower():
                        score += 20
                
                if policy.salary_min is not None or policy.salary_max is not None:
                    score += 5
                
                if score > best_score:
                    best_score = score
                    best_match = policy
            
            if not best_match:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                self.logger.info(f"No matching policy found for {job_title} ({seniority})")
                return None
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.info(f"Found policy '{best_match.name}' with score {best_score}")
            
            return {
                "id": str(best_match.id),
                "name": best_match.name,
                "department": best_match.department,
                "role_pattern": best_match.role_pattern,
                "seniority_level": best_match.seniority_level,
                "salary_min": best_match.salary_min,
                "salary_max": best_match.salary_max,
                "salary_target": best_match.salary_target,
                "bonus_enabled": best_match.bonus_enabled,
                "bonus_type": best_match.bonus_type,
                "bonus_min_pct": best_match.bonus_min_pct,
                "bonus_target_pct": best_match.bonus_target_pct,
                "bonus_max_pct": best_match.bonus_max_pct,
                "bonus_criteria": best_match.bonus_criteria if best_match.bonus_criteria is not None else {},
                "total_comp_annual_min": best_match.total_comp_annual_min,
                "total_comp_annual_max": best_match.total_comp_annual_max,
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching compensation policy: {e}")
            return None
    
    def _seniority_match_partial(self, policy_seniority: str, target_seniority: str) -> bool:
        """Check if seniorities are adjacent levels."""
        levels = {
            "estagiário": 0, "estagiario": 0,
            "júnior": 1, "junior": 1,
            "pleno": 2,
            "sênior": 3, "senior": 3,
            "especialista": 4, "staff": 4,
            "principal": 5,
            "gerente": 5, "manager": 5,
            "diretor": 6, "director": 6,
        }
        
        policy_level = levels.get(policy_seniority.lower(), -1)
        target_level = levels.get(target_seniority.lower(), -1)
        
        if policy_level < 0 or target_level < 0:
            return False
        
        return abs(policy_level - target_level) == 1
    
    async def _get_market_data(
        self,
        company_id: str,
        job_title: str,
        seniority: str,
        location: str | None = None
    ) -> dict[str, Any] | None:
        """Fetch market benchmark data for the role."""
        try:
            result = await self.market_benchmark_service.search_salary_benchmark(
                role=job_title,
                seniority=seniority,
                location=location
            )
            
            if result and result.get("min") is not None:
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}")
            return None
    
    def _analyze_salary(
        self,
        proposed_min: float | None,
        proposed_max: float | None,
        policy: dict[str, Any] | None,
        market_data: dict[str, Any] | None,
        alerts: list[str],
        recommendations: list[str],
        data_sources: list[DataSource]
    ) -> SalaryAnalysis:
        """Analyze salary against policy and market."""
        analysis = SalaryAnalysis(
            proposed_min=proposed_min,
            proposed_max=proposed_max,
        )
        
        sources: list[DataSource] = []
        confidence = 0.0
        
        if market_data:
            analysis.market_min = market_data.get("min")
            analysis.market_max = market_data.get("max")
            analysis.market_median = market_data.get("median")
            sources.append(DataSource.MARKET_BENCHMARK)
            
            market_confidence = market_data.get("confidence", "low")
            if market_confidence == "high":
                confidence += 0.4
            elif market_confidence == "medium":
                confidence += 0.25
            else:
                confidence += 0.1
        
        if policy:
            analysis.policy_min = policy.get("salary_min")
            analysis.policy_max = policy.get("salary_max")
            sources.append(DataSource.COMPANY_POLICY)
            confidence += 0.3
        
        if proposed_min is not None or proposed_max is not None:
            sources.append(DataSource.USER_INPUT)
            confidence += 0.2
        
        if proposed_min is not None and proposed_max is not None:
            proposed_mid = (proposed_min + proposed_max) / 2
            
            if analysis.market_median is not None:
                market_mid = analysis.market_median
                deviation_pct = (proposed_mid - market_mid) / market_mid if market_mid > 0 else 0
                
                if deviation_pct > 0.2:
                    analysis.market_alignment = CompensationAlignmentStatus.ABOVE_MARKET
                    analysis.market_percentile = 90
                    alerts.append(f"Salário proposto {deviation_pct*100:.0f}% acima do mercado")
                elif deviation_pct < -0.15:
                    analysis.market_alignment = CompensationAlignmentStatus.BELOW_MARKET
                    analysis.market_percentile = 25
                    alerts.append(f"Salário proposto {abs(deviation_pct)*100:.0f}% abaixo do mercado")
                    recommendations.append("Considere aumentar a faixa salarial para atrair melhores candidatos")
                else:
                    analysis.market_alignment = CompensationAlignmentStatus.ALIGNED
                    analysis.market_percentile = 50 + int(deviation_pct * 100)
            
            if analysis.policy_min is not None and analysis.policy_max is not None:
                if proposed_min < analysis.policy_min * (1 - self.ALIGNMENT_TOLERANCE_PCT):
                    analysis.policy_alignment = CompensationAlignmentStatus.BELOW_POLICY
                    alerts.append("Salário mínimo proposto abaixo da política da empresa")
                    analysis.suggested_min = analysis.policy_min
                    analysis.suggestion_reason = "Ajustado ao mínimo da política"
                elif proposed_max > analysis.policy_max * (1 + self.ALIGNMENT_TOLERANCE_PCT):
                    analysis.policy_alignment = CompensationAlignmentStatus.ABOVE_POLICY
                    alerts.append("Salário máximo proposto acima da política da empresa")
                    recommendations.append("Verificar aprovação especial para faixa acima da política")
                    analysis.suggested_max = analysis.policy_max
                    analysis.suggestion_reason = "Ajustado ao máximo da política"
                else:
                    analysis.policy_alignment = CompensationAlignmentStatus.ALIGNED
        else:
            if policy and policy.get("salary_min") is not None:
                analysis.suggested_min = policy.get("salary_min")
                analysis.suggested_max = policy.get("salary_max")
                analysis.suggestion_reason = "Baseado na política da empresa"
            elif market_data and market_data.get("min") is not None:
                analysis.suggested_min = market_data.get("min")
                analysis.suggested_max = market_data.get("max")
                analysis.suggestion_reason = "Baseado em dados de mercado"
        
        analysis.data_sources = sources
        analysis.confidence = min(confidence, 1.0)
        
        return analysis
    
    def _analyze_bonus(
        self,
        proposed_pct: float | None,
        policy: dict[str, Any] | None,
        alerts: list[str],
        recommendations: list[str]
    ) -> BonusAnalysis:
        """Analyze bonus against company policy."""
        analysis = BonusAnalysis(
            proposed_pct=proposed_pct,
        )
        
        if policy and policy.get("bonus_enabled"):
            analysis.policy_exists = True
            analysis.policy_min_pct = policy.get("bonus_min_pct")
            analysis.policy_target_pct = policy.get("bonus_target_pct")
            analysis.policy_max_pct = policy.get("bonus_max_pct")
            analysis.policy_type = policy.get("bonus_type")
            analysis.data_source = DataSource.COMPANY_POLICY
            
            if proposed_pct is not None:
                if analysis.policy_min_pct is not None and proposed_pct < analysis.policy_min_pct:
                    analysis.policy_alignment = CompensationAlignmentStatus.BELOW_POLICY
                    alerts.append(f"Bônus proposto ({proposed_pct}%) abaixo do mínimo da política ({analysis.policy_min_pct}%)")
                    analysis.suggested_pct = analysis.policy_target_pct
                    analysis.suggestion_reason = "Ajustado à meta da política"
                elif analysis.policy_max_pct is not None and proposed_pct > analysis.policy_max_pct:
                    analysis.policy_alignment = CompensationAlignmentStatus.ABOVE_POLICY
                    alerts.append(f"Bônus proposto ({proposed_pct}%) acima do máximo da política ({analysis.policy_max_pct}%)")
                    recommendations.append("Verificar aprovação especial para bônus acima da política")
                else:
                    analysis.policy_alignment = CompensationAlignmentStatus.ALIGNED
            else:
                analysis.suggested_pct = analysis.policy_target_pct
                analysis.suggested_type = analysis.policy_type
                analysis.suggestion_reason = "Baseado na política da empresa"
        else:
            if proposed_pct is not None and proposed_pct > 0:
                alerts.append("Bônus proposto, mas não há política de bônus definida")
                recommendations.append("Definir política de bônus para o cargo")
        
        return analysis
    
    def _analyze_benefits(
        self,
        proposed_benefits: list[str],
        company_benefits: list[dict[str, Any]],
        seniority: str,
        alerts: list[str],
        recommendations: list[str]
    ) -> BenefitAnalysis:
        """Analyze benefits against company standard package."""
        
        standard_benefit_names = []
        for benefit in company_benefits:
            applicable_seniorities = benefit.get("applicable_seniorities", [])
            if not applicable_seniorities or seniority.lower() in [s.lower() for s in applicable_seniorities]:
                if benefit.get("is_mandatory") or benefit.get("is_highlighted"):
                    standard_benefit_names.append(benefit.get("name", "").lower())
        
        analysis = BenefitAnalysis(
            proposed_benefits=proposed_benefits,
            company_standard_benefits=[b.get("name", "") for b in company_benefits if b.get("is_mandatory") or b.get("is_highlighted")],
            data_source=DataSource.COMPANY_POLICY if company_benefits else None
        )
        
        proposed_lower = [b.lower() for b in proposed_benefits]
        
        missing = []
        for std_benefit in standard_benefit_names:
            if not any(std_benefit in p or p in std_benefit for p in proposed_lower):
                missing.append(std_benefit)
        
        analysis.missing_standard_benefits = missing
        
        if missing:
            alerts.append(f"Benefícios padrão não incluídos: {', '.join(missing[:3])}")
            analysis.suggested_additions = missing
        
        monetizable_value, breakdown = self._calculate_monetizable_benefits(
            proposed_benefits=proposed_benefits,
            company_benefits=company_benefits
        )
        
        analysis.monetizable_annual_value = monetizable_value
        analysis.monetizable_breakdown = breakdown
        
        return analysis
    
    def _calculate_monetizable_benefits(
        self,
        proposed_benefits: list[str],
        company_benefits: list[dict[str, Any]]
    ) -> tuple:
        """Calculate annual value of monetizable benefits."""
        total_value = 0.0
        breakdown: dict[str, float] = {}
        
        company_benefit_values = {}
        for benefit in company_benefits:
            name = benefit.get("name", "").lower()
            value = benefit.get("value", 0) or 0
            value_type = benefit.get("value_type", "monetary")
            
            if value_type == "monetary" and value > 0:
                annual_value = value * 12
                company_benefit_values[name] = annual_value
        
        for benefit_name in proposed_benefits:
            name_lower = benefit_name.lower()
            
            if name_lower in company_benefit_values:
                value = company_benefit_values[name_lower]
                breakdown[benefit_name] = value
                total_value += value
            else:
                for key, default_value in BENEFIT_ANNUAL_VALUES.items():
                    if key in name_lower or name_lower in key:
                        if default_value > 0:
                            breakdown[benefit_name] = default_value
                            total_value += default_value
                        break
        
        return total_value, breakdown
    
    def _calculate_total_comp(
        self,
        salary_analysis: SalaryAnalysis,
        bonus_analysis: BonusAnalysis,
        benefits_analysis: BenefitAnalysis,
        policy: dict[str, Any] | None,
        market_data: dict[str, Any] | None
    ) -> TotalCompAnalysis:
        """Calculate total compensation breakdown."""
        analysis = TotalCompAnalysis()
        
        if salary_analysis.proposed_min is not None:
            analysis.proposed_annual_salary_min = salary_analysis.proposed_min * self.MONTHS_PER_YEAR
        if salary_analysis.proposed_max is not None:
            analysis.proposed_annual_salary_max = salary_analysis.proposed_max * self.MONTHS_PER_YEAR
        
        if bonus_analysis.proposed_pct is not None and salary_analysis.proposed_max is not None:
            salary_mid = (salary_analysis.proposed_min or salary_analysis.proposed_max + salary_analysis.proposed_max) / 2
            annual_salary_mid = salary_mid * self.MONTHS_PER_YEAR
            analysis.proposed_bonus_annual = annual_salary_mid * (bonus_analysis.proposed_pct / 100)
        
        if benefits_analysis.monetizable_annual_value:
            analysis.proposed_benefits_annual = benefits_analysis.monetizable_annual_value
        
        salary_min_annual = analysis.proposed_annual_salary_min or 0
        salary_max_annual = analysis.proposed_annual_salary_max or 0
        bonus_annual = analysis.proposed_bonus_annual or 0
        benefits_annual = analysis.proposed_benefits_annual or 0
        
        if salary_min_annual > 0:
            analysis.proposed_total_comp_min = salary_min_annual + bonus_annual + benefits_annual
        if salary_max_annual > 0:
            analysis.proposed_total_comp_max = salary_max_annual + bonus_annual + benefits_annual
        
        if market_data:
            market_min = market_data.get("min")
            market_max = market_data.get("max")
            if market_min is not None:
                analysis.market_total_comp_min = market_min * self.MONTHS_PER_YEAR
            if market_max is not None:
                analysis.market_total_comp_max = market_max * self.MONTHS_PER_YEAR
            
            if analysis.proposed_total_comp_min and analysis.market_total_comp_min:
                proposed_mid = (analysis.proposed_total_comp_min + (analysis.proposed_total_comp_max or analysis.proposed_total_comp_min)) / 2
                market_mid = (analysis.market_total_comp_min + (analysis.market_total_comp_max or analysis.market_total_comp_min)) / 2
                
                if proposed_mid > market_mid * 1.15:
                    analysis.market_alignment = CompensationAlignmentStatus.ABOVE_MARKET
                elif proposed_mid < market_mid * 0.85:
                    analysis.market_alignment = CompensationAlignmentStatus.BELOW_MARKET
                else:
                    analysis.market_alignment = CompensationAlignmentStatus.ALIGNED
        
        if policy:
            if policy.get("total_comp_annual_min"):
                analysis.policy_total_comp_min = policy.get("total_comp_annual_min")
            if policy.get("total_comp_annual_max"):
                analysis.policy_total_comp_max = policy.get("total_comp_annual_max")
            
            if analysis.proposed_total_comp_min and analysis.policy_total_comp_min:
                if analysis.proposed_total_comp_min < analysis.policy_total_comp_min * 0.9:
                    analysis.policy_alignment = CompensationAlignmentStatus.BELOW_POLICY
                elif analysis.proposed_total_comp_max and analysis.policy_total_comp_max and analysis.proposed_total_comp_max > analysis.policy_total_comp_max * 1.1:
                    analysis.policy_alignment = CompensationAlignmentStatus.ABOVE_POLICY
                else:
                    analysis.policy_alignment = CompensationAlignmentStatus.ALIGNED
        
        analysis.breakdown_chart = {
            "salary": {
                "min": salary_min_annual,
                "max": salary_max_annual,
                "label": "Salário Base",
            },
            "bonus": {
                "value": bonus_annual,
                "label": "Bônus",
            },
            "benefits": {
                "value": benefits_annual,
                "label": "Benefícios",
            }
        }
        
        return analysis
    
    def _build_result(
        self,
        salary_analysis: SalaryAnalysis,
        bonus_analysis: BonusAnalysis,
        benefits_analysis: BenefitAnalysis,
        total_comp: TotalCompAnalysis,
        data_sources_used: list[DataSource],
        alerts: list[str],
        recommendations: list[str],
        job_title: str,
        seniority: str
    ) -> CompensationAnalysisResult:
        """Build the final analysis result."""
        
        alignments = [
            salary_analysis.market_alignment,
            salary_analysis.policy_alignment,
            bonus_analysis.policy_alignment,
            total_comp.market_alignment,
            total_comp.policy_alignment,
        ]
        
        non_no_data = [a for a in alignments if a != CompensationAlignmentStatus.NO_DATA]
        
        if not non_no_data:
            overall = CompensationAlignmentStatus.NO_DATA
        elif any(a in [CompensationAlignmentStatus.BELOW_MARKET, CompensationAlignmentStatus.BELOW_POLICY] for a in non_no_data):
            overall = CompensationAlignmentStatus.BELOW_MARKET
        elif any(a in [CompensationAlignmentStatus.ABOVE_MARKET, CompensationAlignmentStatus.ABOVE_POLICY] for a in non_no_data):
            overall = CompensationAlignmentStatus.ABOVE_MARKET
        else:
            overall = CompensationAlignmentStatus.ALIGNED
        
        if overall == CompensationAlignmentStatus.ALIGNED:
            summary = f"Compensação para {job_title} ({seniority}) está alinhada com mercado e políticas internas."
        elif overall == CompensationAlignmentStatus.BELOW_MARKET:
            summary = f"Compensação para {job_title} ({seniority}) está abaixo do mercado ou das políticas. Recomenda-se revisão."
        elif overall == CompensationAlignmentStatus.ABOVE_MARKET:
            summary = f"Compensação para {job_title} ({seniority}) está acima do mercado ou das políticas. Pode requerer aprovação especial."
        else:
            summary = f"Dados insuficientes para análise completa de compensação para {job_title} ({seniority})."
        
        suggested_values: dict[str, Any] = {}
        
        if salary_analysis.suggested_min is not None:
            suggested_values["salary_min"] = salary_analysis.suggested_min
        if salary_analysis.suggested_max is not None:
            suggested_values["salary_max"] = salary_analysis.suggested_max
        if bonus_analysis.suggested_pct is not None:
            suggested_values["bonus_pct"] = bonus_analysis.suggested_pct
        if benefits_analysis.suggested_additions:
            suggested_values["additional_benefits"] = benefits_analysis.suggested_additions
        
        confidence_factors = [salary_analysis.confidence]
        if DataSource.COMPANY_POLICY in data_sources_used:
            confidence_factors.append(0.3)
        if DataSource.MARKET_BENCHMARK in data_sources_used:
            confidence_factors.append(0.3)
        
        analysis_confidence = min(sum(confidence_factors), 1.0)
        
        return CompensationAnalysisResult(
            salary=salary_analysis,
            bonus=bonus_analysis,
            benefits=benefits_analysis,
            total_comp=total_comp,
            overall_assessment=overall,
            summary=summary,
            alerts=alerts,
            recommendations=recommendations,
            suggested_values=suggested_values,
            analyzed_at=datetime.utcnow(),
            data_sources_used=list(set(data_sources_used)),
            analysis_confidence=analysis_confidence
        )


compensation_analysis_service = CompensationAnalysisService()
