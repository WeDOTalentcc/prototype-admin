"""
Intelligent Data Orchestrator - Multi-source data consolidation with intelligent prioritization.

Orchestrates data from multiple sources with priority-based confidence scoring:
1. Learning Patterns (VERY_HIGH confidence) - From user feedback
2. Company Configuration (HIGH confidence) - Explicit company settings
3. Job Insights Service (HIGH confidence) - Internal LIA data
4. ATS Job History (MEDIUM confidence) - Historical ATS data
5. Market Benchmark (LOW-MEDIUM confidence) - External market data

Features:
- 3-layer caching (Session → Redis → PostgreSQL)
- Silent learning loop integration
- Intelligent field inference
- Source attribution for transparency
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DataSource(StrEnum):
    """Data sources in priority order."""
    LEARNING_PATTERNS = "learning_patterns"
    COMPANY_SKILLS_CATALOG = "company_skills_catalog"
    COMPANY_CONFIG = "company_config"
    JOB_INSIGHTS = "job_insights"
    ATS_HISTORY = "ats_history"
    MARKET_BENCHMARK = "market_benchmark"
    LLM_INFERENCE = "llm_inference"


class ConfidenceLevel(StrEnum):
    """Confidence levels for data sources."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW_MEDIUM = "low_medium"
    LOW = "low"


SOURCE_CONFIDENCE_MAP = {
    DataSource.LEARNING_PATTERNS: ConfidenceLevel.VERY_HIGH,
    DataSource.COMPANY_SKILLS_CATALOG: ConfidenceLevel.HIGH,
    DataSource.COMPANY_CONFIG: ConfidenceLevel.HIGH,
    DataSource.JOB_INSIGHTS: ConfidenceLevel.HIGH,
    DataSource.ATS_HISTORY: ConfidenceLevel.MEDIUM,
    DataSource.MARKET_BENCHMARK: ConfidenceLevel.LOW_MEDIUM,
    DataSource.LLM_INFERENCE: ConfidenceLevel.LOW,
}

CONFIDENCE_SCORES = {
    ConfidenceLevel.VERY_HIGH: 0.95,
    ConfidenceLevel.HIGH: 0.85,
    ConfidenceLevel.MEDIUM: 0.70,
    ConfidenceLevel.LOW_MEDIUM: 0.55,
    ConfidenceLevel.LOW: 0.40,
}


@dataclass
class DataResult:
    """Result from a single data source."""
    source: DataSource
    value: Any
    confidence: float
    confidence_level: ConfidenceLevel
    metadata: dict[str, Any] = field(default_factory=dict)
    cached: bool = False
    error: str | None = None


@dataclass
class OrchestratedResult:
    """Final orchestrated result from multiple sources."""
    primary_value: Any
    primary_source: DataSource
    primary_confidence: float
    all_sources: list[DataResult]
    consensus: bool
    consensus_value: Any | None = None
    suggested_value: Any | None = None
    explanation: str | None = None


@dataclass
class SalaryResult(OrchestratedResult):
    """Salary-specific result with range breakdown."""
    min_salary: float | None = None
    max_salary: float | None = None
    median_salary: float | None = None
    currency: str = "BRL"
    percentile_p25: float | None = None
    percentile_p75: float | None = None


@dataclass
class SkillsResult(OrchestratedResult):
    """Skills-specific result with categorization."""
    technical_skills: list[dict[str, Any]] = field(default_factory=list)
    behavioral_skills: list[dict[str, Any]] = field(default_factory=list)
    recommended_count: int = 0


@dataclass
class JobContext:
    """Context for job-related queries."""
    company_id: str
    session_id: str | None = None
    role: str | None = None
    title: str | None = None
    seniority: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: str | None = None


class IntelligentDataOrchestrator:
    """
    Central orchestrator for multi-source data consolidation.
    
    Responsibilities:
    1. Query multiple data sources in parallel
    2. Apply priority-based confidence scoring
    3. Detect consensus across sources
    4. Cache results for token economy
    5. Capture feedback for learning loop
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache_manager = None
        self._learning_loop = None
        self._company_config = None
        self._job_insights = None
        self._ats_history = None
        self._market_benchmark = None
        self._skills_catalog_db = None
    
    def _get_cache_manager(self):
        """Lazy load cache manager."""
        if self._cache_manager is None:
            from app.shared.services.cache_manager_service import cache_manager_service
            self._cache_manager = cache_manager_service
        return self._cache_manager
    
    def _get_learning_loop(self):
        """Lazy load learning loop service."""
        if self._learning_loop is None:
            from app.shared.learning.learning_loop_service import learning_loop_service
            self._learning_loop = learning_loop_service
        return self._learning_loop
    
    def _get_company_config(self):
        """Lazy load company configuration service."""
        if self._company_config is None:
            from app.domains.company.services.company_configuration_service import company_config_service
            self._company_config = company_config_service
        return self._company_config
    
    def _get_job_insights(self):
        """Lazy load job insights service."""
        if self._job_insights is None:
            from app.domains.analytics.services.job_insights_service import job_insights_service
            self._job_insights = job_insights_service
        return self._job_insights
    
    def _get_ats_history(self):
        """Lazy load ATS history service."""
        if self._ats_history is None:
            from app.domains.job_management.services.ats_job_history_service import ats_job_history_service
            self._ats_history = ats_job_history_service
        return self._ats_history
    
    def _get_market_benchmark(self):
        """Lazy load market benchmark service."""
        if self._market_benchmark is None:
            from app.shared.services.market_benchmark_service import market_benchmark_service
            self._market_benchmark = market_benchmark_service
        return self._market_benchmark
    
    def _get_skills_catalog_db(self, db: AsyncSession):
        """Get skills catalog DB service instance."""
        from app.shared.services.skills_catalog_service import get_skills_catalog_db_service
        return get_skills_catalog_db_service(db)
    
    async def get_salary_data(
        self,
        db: AsyncSession,
        context: JobContext
    ) -> SalaryResult:
        """
        Get salary data from all sources with intelligent prioritization.
        
        Priority order:
        1. Learning patterns (company's historical preferences)
        2. Company configuration (explicit salary policies)
        3. Internal job history (previous similar jobs)
        4. ATS history (connected ATS data)
        5. Market benchmark (external data)
        """
        cache_manager = self._get_cache_manager()
        from app.shared.services.cache_manager_service import CacheNamespace
        
        cache_result = await cache_manager.get(
            namespace=CacheNamespace.SALARY_BENCHMARK,
            company_id=context.company_id,
            identifiers={
                "role": context.role or context.title,
                "seniority": context.seniority,
                "location": context.location
            },
            session_id=context.session_id,
            db=db
        )
        
        if cache_result.hit:
            self.logger.debug("Salary data from cache")
            cached_value = cache_result.value
            if cached_value is not None:
                return self._parse_cached_salary(cached_value)
        
        all_results = []
        
        learning_data = await self._get_learning_salary(db, context)
        if learning_data:
            all_results.append(learning_data)
        
        config_data = await self._get_company_config_salary(db, context)
        if config_data:
            all_results.append(config_data)
        
        internal_data = await self._get_internal_salary(db, context)
        if internal_data:
            all_results.append(internal_data)
        
        ats_data = await self._get_ats_salary(context)
        if ats_data:
            all_results.append(ats_data)
        
        market_data = await self._get_market_salary(context)
        if market_data:
            all_results.append(market_data)
        
        result = self._consolidate_salary_results(all_results, context)
        
        await cache_manager.set(
            namespace=CacheNamespace.SALARY_BENCHMARK,
            company_id=context.company_id,
            identifiers={
                "role": context.role or context.title,
                "seniority": context.seniority,
                "location": context.location
            },
            value=self._salary_to_cache(result),
            session_id=context.session_id,
            db=db,
            confidence=result.primary_confidence,
            source=result.primary_source.value
        )
        
        return result
    
    async def _get_learning_salary(
        self,
        db: AsyncSession,
        context: JobContext
    ) -> DataResult | None:
        """Get salary from learning patterns."""
        try:
            learning_loop = self._get_learning_loop()
            adjustment = await learning_loop.get_salary_adjustment(
                db, context.company_id, context.role, context.seniority
            )
            
            if adjustment:
                return DataResult(
                    source=DataSource.LEARNING_PATTERNS,
                    value={
                        "min": adjustment["learned_min"],
                        "max": adjustment["learned_max"],
                        "median": (adjustment["learned_min"] + adjustment["learned_max"]) / 2
                    },
                    confidence=min(adjustment.get("confidence", 0.9) * CONFIDENCE_SCORES[ConfidenceLevel.VERY_HIGH], 1.0),
                    confidence_level=ConfidenceLevel.VERY_HIGH,
                    metadata={
                        "sample_size": adjustment.get("sample_size", 0),
                        "source_type": "company_learning"
                    }
                )
        except Exception as e:
            self.logger.warning(f"Error getting learning salary: {e}")
        
        return None
    
    async def _get_company_config_salary(
        self,
        db: AsyncSession,
        context: JobContext
    ) -> DataResult | None:
        """Get salary from company configuration."""
        try:
            company_config = self._get_company_config()
            config_obj = await company_config.get_configuration(context.company_id, db=db)
            
            if config_obj:
                salary_policies = getattr(config_obj, "salary_policies", {})
                role_key = (context.role or context.title or "").lower()
                
                if role_key in salary_policies:
                    policy = salary_policies[role_key]
                    return DataResult(
                        source=DataSource.COMPANY_CONFIG,
                        value={
                            "min": policy.get("min"),
                            "max": policy.get("max"),
                            "median": policy.get("median")
                        },
                        confidence=CONFIDENCE_SCORES[ConfidenceLevel.HIGH],
                        confidence_level=ConfidenceLevel.HIGH,
                        metadata={"source_type": "explicit_policy"}
                    )
                
                default_ranges = getattr(config_obj, "default_salary_ranges", {})
                seniority = (context.seniority or "pleno").lower()
                
                if seniority in default_ranges:
                    ranges = default_ranges[seniority]
                    return DataResult(
                        source=DataSource.COMPANY_CONFIG,
                        value={
                            "min": ranges.get("min"),
                            "max": ranges.get("max"),
                            "median": (ranges.get("min", 0) + ranges.get("max", 0)) / 2
                        },
                        confidence=CONFIDENCE_SCORES[ConfidenceLevel.HIGH] * 0.8,
                        confidence_level=ConfidenceLevel.HIGH,
                        metadata={"source_type": "default_range"}
                    )
        except Exception as e:
            self.logger.warning(f"Error getting company config salary: {e}")
        
        return None
    
    async def _get_internal_salary(self, db: AsyncSession, context: JobContext) -> DataResult | None:
        """Get salary from internal job insights."""
        try:
            job_insights = self._get_job_insights()
            insights = await job_insights.get_salary_benchmark(
                db=db,
                company_id=context.company_id,
                role=context.role or context.title or "",
                seniority=context.seniority,
                location=context.location
            )
            
            if insights and insights.get("salary_range"):
                salary = insights["salary_range"]
                return DataResult(
                    source=DataSource.JOB_INSIGHTS,
                    value={
                        "min": salary.get("min"),
                        "max": salary.get("max"),
                        "median": salary.get("median")
                    },
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.HIGH],
                    confidence_level=ConfidenceLevel.HIGH,
                    metadata={"sample_size": insights.get("sample_size", 0)}
                )
        except Exception as e:
            self.logger.warning(f"Error getting internal salary: {e}")
        
        return None
    
    async def _get_ats_salary(self, context: JobContext) -> DataResult | None:
        """Get salary from ATS history."""
        try:
            ats_history = self._get_ats_history()
            insight = await ats_history.get_salary_insights(
                company_id=context.company_id,
                role=context.role or context.title or "",
                seniority=context.seniority,
                location=context.location
            )
            
            if insight:
                return DataResult(
                    source=DataSource.ATS_HISTORY,
                    value={
                        "min": insight.min_salary,
                        "max": insight.max_salary,
                        "median": insight.median_salary
                    },
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.MEDIUM],
                    confidence_level=ConfidenceLevel.MEDIUM,
                    metadata={
                        "sample_size": insight.sample_size,
                        "ats_sources": insight.ats_type
                    }
                )
        except Exception as e:
            self.logger.warning(f"Error getting ATS salary: {e}")
        
        return None
    
    async def _get_market_salary(self, context: JobContext) -> DataResult | None:
        """Get salary from market benchmark."""
        try:
            market_benchmark = self._get_market_benchmark()
            benchmark = await market_benchmark.search_salary_benchmark(
                role=context.role or context.title or "",
                seniority=context.seniority,
                location=context.location
            )
            
            if benchmark:
                return DataResult(
                    source=DataSource.MARKET_BENCHMARK,
                    value={
                        "min": benchmark.get("min"),
                        "max": benchmark.get("max"),
                        "median": benchmark.get("median"),
                        "p25": benchmark.get("p25"),
                        "p75": benchmark.get("p75")
                    },
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.LOW_MEDIUM],
                    confidence_level=ConfidenceLevel.LOW_MEDIUM,
                    metadata={
                        "source": benchmark.get("source", "market"),
                        "last_updated": benchmark.get("last_updated")
                    }
                )
        except Exception as e:
            self.logger.warning(f"Error getting market salary: {e}")
        
        return None
    
    def _consolidate_salary_results(
        self,
        results: list[DataResult],
        context: JobContext
    ) -> SalaryResult:
        """Consolidate salary results from multiple sources."""
        if not results:
            return SalaryResult(
                primary_value=None,
                primary_source=DataSource.MARKET_BENCHMARK,
                primary_confidence=0.0,
                all_sources=[],
                consensus=False,
                explanation="Nenhuma fonte de dados disponível para o cargo especificado"
            )
        
        results.sort(key=lambda r: r.confidence, reverse=True)
        primary = results[0]
        
        consensus = self._check_salary_consensus(results)
        
        if consensus:
            all_mins = [r.value.get("min") for r in results if r.value and r.value.get("min")]
            all_maxs = [r.value.get("max") for r in results if r.value and r.value.get("max")]
            
            import statistics
            suggested_min = statistics.mean(all_mins) if all_mins else None
            suggested_max = statistics.mean(all_maxs) if all_maxs else None
            suggested_value = {"min": suggested_min, "max": suggested_max}
        else:
            suggested_value = primary.value
        
        explanation = self._generate_salary_explanation(results, consensus)
        
        val = primary.value or {}
        
        return SalaryResult(
            primary_value=primary.value,
            primary_source=primary.source,
            primary_confidence=primary.confidence,
            all_sources=results,
            consensus=consensus,
            consensus_value=suggested_value if consensus else None,
            suggested_value=suggested_value,
            explanation=explanation,
            min_salary=val.get("min"),
            max_salary=val.get("max"),
            median_salary=val.get("median"),
            percentile_p25=val.get("p25"),
            percentile_p75=val.get("p75")
        )
    
    def _check_salary_consensus(self, results: list[DataResult]) -> bool:
        """Check if salary results have consensus (within 20% range)."""
        if len(results) < 2:
            return True
        
        all_mins = [r.value.get("min") for r in results if r.value and r.value.get("min")]
        all_maxs = [r.value.get("max") for r in results if r.value and r.value.get("max")]
        
        if len(all_mins) < 2 or len(all_maxs) < 2:
            return True
        
        import statistics
        
        min_std = statistics.stdev(all_mins)
        max_std = statistics.stdev(all_maxs)
        
        min_mean = statistics.mean(all_mins)
        max_mean = statistics.mean(all_maxs)
        
        min_cv = (min_std / min_mean) if min_mean > 0 else 0
        max_cv = (max_std / max_mean) if max_mean > 0 else 0
        
        return min_cv < 0.20 and max_cv < 0.20
    
    def _generate_salary_explanation(
        self,
        results: list[DataResult],
        consensus: bool
    ) -> str:
        """Generate human-readable explanation for salary recommendation."""
        if not results:
            return "Não encontramos dados suficientes para sugerir uma faixa salarial."
        
        source_names = {
            DataSource.LEARNING_PATTERNS: "padrões históricos da sua empresa",
            DataSource.COMPANY_CONFIG: "política salarial configurada",
            DataSource.JOB_INSIGHTS: "análise de vagas similares",
            DataSource.ATS_HISTORY: "histórico do seu ATS",
            DataSource.MARKET_BENCHMARK: "benchmark de mercado"
        }
        
        primary = results[0]
        source_name = source_names.get(primary.source, str(primary.source))
        
        if consensus and len(results) >= 2:
            sources = ", ".join(source_names.get(r.source, str(r.source)) for r in results[:3])
            return f"Sugestão baseada em {sources}. Todas as fontes indicam valores similares."
        
        return f"Sugestão principal baseada em {source_name} (confiança: {int(primary.confidence * 100)}%)."
    
    def _salary_to_cache(self, result: SalaryResult) -> dict[str, Any]:
        """Convert salary result to cacheable format."""
        return {
            "min_salary": result.min_salary,
            "max_salary": result.max_salary,
            "median_salary": result.median_salary,
            "primary_source": result.primary_source.value,
            "primary_confidence": result.primary_confidence,
            "consensus": result.consensus,
            "explanation": result.explanation,
            "cached_at": datetime.utcnow().isoformat()
        }
    
    def _parse_cached_salary(self, cached: dict[str, Any]) -> SalaryResult:
        """Parse cached salary data back to SalaryResult."""
        return SalaryResult(
            primary_value={
                "min": cached.get("min_salary"),
                "max": cached.get("max_salary"),
                "median": cached.get("median_salary")
            },
            primary_source=DataSource(cached.get("primary_source", "market_benchmark")),
            primary_confidence=cached.get("primary_confidence", 0.5),
            all_sources=[],
            consensus=cached.get("consensus", False),
            explanation=cached.get("explanation"),
            min_salary=cached.get("min_salary"),
            max_salary=cached.get("max_salary"),
            median_salary=cached.get("median_salary")
        )
    
    async def get_skills_data(
        self,
        db: AsyncSession,
        context: JobContext,
        limit: int = 15
    ) -> SkillsResult:
        """
        Get skills data from all sources with intelligent prioritization.
        
        Priority order:
        1. Learning patterns (company's skill preferences)
        2. Company configuration (required skills catalog)
        3. Internal job history
        4. ATS history
        5. Skills catalog (default)
        """
        cache_manager = self._get_cache_manager()
        from app.shared.services.cache_manager_service import CacheNamespace
        
        cache_result = await cache_manager.get(
            namespace=CacheNamespace.SKILLS_SUGGESTIONS,
            company_id=context.company_id,
            identifiers={
                "role": context.role or context.title,
                "seniority": context.seniority
            },
            session_id=context.session_id,
            db=db
        )
        
        if cache_result.hit:
            self.logger.debug("Skills data from cache")
            cached_value = cache_result.value
            if cached_value is not None:
                return self._parse_cached_skills(cached_value)
        
        all_results = []
        
        learning_skills = await self._get_learning_skills(db, context)
        if learning_skills:
            all_results.append(learning_skills)
        
        company_catalog_skills = await self._get_skills_from_catalog(db, context)
        if company_catalog_skills:
            all_results.append(company_catalog_skills)
        
        config_skills = await self._get_company_config_skills(db, context)
        if config_skills:
            all_results.append(config_skills)
        
        ats_skills = await self._get_ats_skills(context)
        if ats_skills:
            all_results.append(ats_skills)
        
        catalog_skills = await self._get_catalog_skills(context)
        if catalog_skills:
            all_results.append(catalog_skills)
        
        result = self._consolidate_skills_results(all_results, context, limit)
        
        await cache_manager.set(
            namespace=CacheNamespace.SKILLS_SUGGESTIONS,
            company_id=context.company_id,
            identifiers={
                "role": context.role or context.title,
                "seniority": context.seniority
            },
            value=self._skills_to_cache(result),
            session_id=context.session_id,
            db=db,
            confidence=result.primary_confidence,
            source=result.primary_source.value
        )
        
        return result
    
    async def _get_learning_skills(
        self,
        db: AsyncSession,
        context: JobContext
    ) -> DataResult | None:
        """Get skills from learning patterns."""
        try:
            learning_loop = self._get_learning_loop()
            skills = await learning_loop.get_preferred_skills(
                db, context.company_id, context.role, context.seniority
            )
            
            if skills:
                return DataResult(
                    source=DataSource.LEARNING_PATTERNS,
                    value=[s["skill"] for s in skills],
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.VERY_HIGH],
                    confidence_level=ConfidenceLevel.VERY_HIGH,
                    metadata={"skills_detail": skills}
                )
        except Exception as e:
            self.logger.warning(f"Error getting learning skills: {e}")
        
        return None
    
    async def _get_company_config_skills(
        self,
        db: AsyncSession,
        context: JobContext
    ) -> DataResult | None:
        """Get skills from company configuration."""
        try:
            company_config = self._get_company_config()
            config_obj = await company_config.get_configuration(context.company_id, db=db)
            
            if config_obj:
                required_skills = getattr(config_obj, "required_skills", {})
                role_key = (context.role or context.title or "").lower()
                
                if role_key in required_skills:
                    return DataResult(
                        source=DataSource.COMPANY_CONFIG,
                        value=required_skills[role_key],
                        confidence=CONFIDENCE_SCORES[ConfidenceLevel.HIGH],
                        confidence_level=ConfidenceLevel.HIGH,
                        metadata={"source_type": "company_catalog"}
                    )
        except Exception as e:
            self.logger.warning(f"Error getting company config skills: {e}")
        
        return None
    
    async def _get_ats_skills(self, context: JobContext) -> DataResult | None:
        """Get skills from ATS history."""
        try:
            ats_history = self._get_ats_history()
            insights = await ats_history.get_skill_insights(
                company_id=context.company_id,
                role=context.role or context.title or ""
            )
            
            if insights:
                return DataResult(
                    source=DataSource.ATS_HISTORY,
                    value=[i.skill_name for i in insights],
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.MEDIUM],
                    confidence_level=ConfidenceLevel.MEDIUM,
                    metadata={
                        "insights_detail": [
                            {"skill": i.skill_name, "frequency": i.frequency, "percentage": i.percentage}
                            for i in insights
                        ]
                    }
                )
        except Exception as e:
            self.logger.warning(f"Error getting ATS skills: {e}")
        
        return None
    
    async def _get_catalog_skills(self, context: JobContext) -> DataResult | None:
        """Get skills from curated catalog."""
        try:
            from app.shared.services.skills_catalog_service import skills_catalog_service
            
            role = context.role or context.title or ""
            skills = skills_catalog_service.get_skills_for_role(
                role=role,
                seniority=context.seniority
            )
            
            if skills:
                return DataResult(
                    source=DataSource.JOB_INSIGHTS,
                    value=skills,
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.MEDIUM],
                    confidence_level=ConfidenceLevel.MEDIUM,
                    metadata={"source_type": "curated_catalog"}
                )
        except Exception as e:
            self.logger.warning(f"Error getting catalog skills: {e}")
        
        return None
    
    async def _get_skills_from_catalog(
        self,
        db: AsyncSession,
        context: JobContext
    ) -> DataResult | None:
        """Get skills from company's skills catalog database."""
        try:
            skills_catalog_db = self._get_skills_catalog_db(db)
            catalog = await skills_catalog_db.get_company_catalog(context.company_id)
            
            if catalog and catalog.get("skills"):
                company_skills = catalog.get("skills", [])
                
                role_key = (context.role or context.title or "").lower()
                role_specific_skills = [
                    s for s in company_skills 
                    if role_key in s.get("applicable_roles", [])
                ]
                
                selected_skills = role_specific_skills if role_specific_skills else company_skills[:10]
                
                return DataResult(
                    source=DataSource.COMPANY_SKILLS_CATALOG,
                    value=[s.get("name") for s in selected_skills],
                    confidence=CONFIDENCE_SCORES[ConfidenceLevel.HIGH],
                    confidence_level=ConfidenceLevel.HIGH,
                    metadata={
                        "source_type": "company_catalog",
                        "role_specific": len(role_specific_skills) > 0
                    }
                )
        except Exception as e:
            self.logger.warning(f"Error getting company catalog skills: {e}")
        
        return None
    
    def _consolidate_skills_results(
        self,
        results: list[DataResult],
        context: JobContext,
        limit: int
    ) -> SkillsResult:
        """Consolidate skills results from multiple sources."""
        if not results:
            return SkillsResult(
                primary_value=[],
                primary_source=DataSource.JOB_INSIGHTS,
                primary_confidence=0.0,
                all_sources=[],
                consensus=False,
                technical_skills=[],
                behavioral_skills=[],
                recommended_count=0
            )
        
        results.sort(key=lambda r: r.confidence, reverse=True)
        primary = results[0]
        
        skill_scores: dict[str, float] = {}
        
        for result in results:
            skills = result.value or []
            for i, skill in enumerate(skills):
                skill_name = skill if isinstance(skill, str) else skill.get("name", str(skill))
                position_weight = 1.0 - (i * 0.05)
                score = result.confidence * max(position_weight, 0.5)
                
                if skill_name in skill_scores:
                    skill_scores[skill_name] = max(skill_scores[skill_name], score)
                else:
                    skill_scores[skill_name] = score
        
        sorted_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)
        
        technical = []
        behavioral = []
        
        behavioral_keywords = ["comunicação", "liderança", "trabalho em equipe", "resolução", "adaptabilidade",
                               "proatividade", "criatividade", "empatia", "organização", "negociação",
                               "communication", "leadership", "teamwork", "problem solving", "adaptability"]
        
        for skill_name, score in sorted_skills[:limit]:
            skill_entry = {
                "name": skill_name,
                "score": round(score, 2),
                "source": "consolidated"
            }
            
            if any(kw in skill_name.lower() for kw in behavioral_keywords):
                behavioral.append(skill_entry)
            else:
                technical.append(skill_entry)
        
        consolidated_skills = [s[0] for s in sorted_skills[:limit]]
        
        return SkillsResult(
            primary_value=consolidated_skills,
            primary_source=primary.source,
            primary_confidence=primary.confidence,
            all_sources=results,
            consensus=len(results) >= 2,
            suggested_value=consolidated_skills,
            technical_skills=technical,
            behavioral_skills=behavioral,
            recommended_count=len(consolidated_skills)
        )
    
    def _skills_to_cache(self, result: SkillsResult) -> dict[str, Any]:
        """Convert skills result to cacheable format."""
        return {
            "skills": result.primary_value,
            "technical_skills": result.technical_skills,
            "behavioral_skills": result.behavioral_skills,
            "primary_source": result.primary_source.value,
            "primary_confidence": result.primary_confidence,
            "cached_at": datetime.utcnow().isoformat()
        }
    
    def _parse_cached_skills(self, cached: dict[str, Any]) -> SkillsResult:
        """Parse cached skills data back to SkillsResult."""
        return SkillsResult(
            primary_value=cached.get("skills", []),
            primary_source=DataSource(cached.get("primary_source", "job_insights")),
            primary_confidence=cached.get("primary_confidence", 0.5),
            all_sources=[],
            consensus=True,
            technical_skills=cached.get("technical_skills", []),
            behavioral_skills=cached.get("behavioral_skills", []),
            recommended_count=len(cached.get("skills", []))
        )
    
    async def capture_field_feedback(
        self,
        db: AsyncSession,
        context: JobContext,
        field_name: str,
        suggested_value: Any,
        final_value: Any,
        source: str | None = None,
        source_confidence: float | None = None,
        explicitly_rejected: bool = False
    ) -> None:
        """
        Capture feedback for learning loop.
        
        This is called silently whenever a field is finalized.
        """
        try:
            learning_loop = self._get_learning_loop()
            await learning_loop.capture_from_wizard_update(
                db=db,
                company_id=context.company_id,
                session_id=context.session_id or "",
                job_id=None,
                field_name=field_name,
                suggested_value=suggested_value,
                final_value=final_value,
                stage=None,
                context={
                    "role": context.role,
                    "title": context.title,
                    "seniority": context.seniority,
                    "department": context.department,
                    "location": context.location
                },
                source=source,
                source_confidence=source_confidence,
                explicitly_rejected=explicitly_rejected
            )
        except Exception as e:
            self.logger.warning(f"Error capturing feedback: {e}")


intelligent_data_orchestrator = IntelligentDataOrchestrator()
