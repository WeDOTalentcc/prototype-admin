"""
Job Context Service - Enriches job context with comprehensive data for AI agents.

This service provides enriched context about a job vacancy, including:
- Job details (requirements, skills, salary, timeline)
- Candidates in pipeline with WSI scores, Big Five profiles
- Funnel metrics (conversion rates, bottlenecks, time in stage)
- Historical data (similar jobs, past performance)

Used by the Orchestrator to provide specialized agents with full context
for data-driven, accurate responses.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class FunnelHealthStatus(StrEnum):
    HEALTHY = "saudável"
    ATTENTION = "atenção"
    CRITICAL = "crítico"


@dataclass
class FunnelMetrics:
    """Metrics for recruitment funnel analysis."""
    total_candidates: int = 0
    by_stage: dict[str, int] = field(default_factory=dict)
    conversion_rates: dict[str, float] = field(default_factory=dict)
    avg_time_by_stage: dict[str, float] = field(default_factory=dict)
    bottleneck_stage: str | None = None
    health_status: FunnelHealthStatus = FunnelHealthStatus.HEALTHY
    stalled_candidates: list[dict[str, Any]] = field(default_factory=list)
    candidates_needing_feedback: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EnrichedCandidate:
    """Candidate with all relevant scores and metrics."""
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    current_company: str | None = None
    location: str | None = None
    stage: str | None = None
    sub_status: str | None = None
    days_in_stage: int = 0
    
    fit_score: float | None = None
    wsi_score: float | None = None
    wsi_technical: float | None = None
    wsi_behavioral: float | None = None
    
    big_five: dict[str, float] = field(default_factory=dict)
    
    rubric_scores: dict[str, float] = field(default_factory=dict)
    
    skills: list[str] = field(default_factory=list)
    experience_years: int | None = None
    
    has_cv: bool = False
    has_wsi_screening: bool = False
    has_interview: bool = False
    
    warnings: list[str] = field(default_factory=list)
    last_activity: datetime | None = None


@dataclass
class EnrichedJobContext:
    """Complete enriched context for a job vacancy."""
    job_id: str
    title: str
    department: str | None = None
    seniority: str | None = None
    work_model: str | None = None
    location: str | None = None
    
    salary_min: float | None = None
    salary_max: float | None = None
    
    required_skills: list[str] = field(default_factory=list)
    desired_skills: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    
    status: str = "active"
    priority: str = "normal"
    deadline: datetime | None = None
    days_open: int = 0
    
    funnel_metrics: FunnelMetrics = field(default_factory=FunnelMetrics)
    
    candidates: list[EnrichedCandidate] = field(default_factory=list)
    
    similar_jobs_avg_time_to_hire: float | None = None
    similar_jobs_avg_candidates: int | None = None


class JobContextService:
    """
    Service for building enriched job context for AI agents.
    
    This service aggregates data from multiple sources to provide
    comprehensive context that enables agents to give accurate,
    data-driven responses about job vacancies.
    """
    
    def __init__(self, db_service=None):
        """Initialize with optional database service."""
        self.db_service = db_service
    
    
    def _enrich_candidates(
        self, 
        candidates: list[dict[str, Any]]
    ) -> list[EnrichedCandidate]:
        """Enrich candidate data with computed fields."""
        enriched = []
        
        for c in candidates:
            big_five = c.get("bigFive", {}) or {}
            
            warnings = []
            if c.get("warnings", 0) > 0:
                warnings.append(f"{c['warnings']} alertas")
            
            has_wsi = bool(c.get("wsiScore") or c.get("score"))
            
            enriched_candidate = EnrichedCandidate(
                id=c.get("id", ""),
                name=c.get("name", "Desconhecido"),
                email=c.get("email"),
                phone=c.get("phone"),
                role=c.get("role"),
                current_company=c.get("currentCompany"),
                location=c.get("location"),
                stage=c.get("stage"),
                sub_status=c.get("subStatus"),
                days_in_stage=c.get("daysInStage", 0),
                fit_score=c.get("fitScore"),
                wsi_score=c.get("wsiScore") or c.get("score"),
                wsi_technical=c.get("wsiTechnical"),
                wsi_behavioral=c.get("wsiBehavioral"),
                big_five=big_five,
                skills=c.get("skills", []) or [],
                experience_years=self._parse_experience(c.get("experience")),
                has_cv=bool(c.get("cvUrl") or c.get("hasCV")),
                has_wsi_screening=has_wsi,
                has_interview=c.get("stage") in ["interview_hr", "interview_technical", "interview_manager"],
                warnings=warnings,
                last_activity=self._parse_date(c.get("lastActivity"))
            )
            
            enriched.append(enriched_candidate)
        
        return enriched
    
    def _compute_funnel_metrics(
        self, 
        candidates: list[EnrichedCandidate]
    ) -> FunnelMetrics:
        """Compute funnel metrics from candidates."""
        metrics = FunnelMetrics()
        metrics.total_candidates = len(candidates)
        
        stage_order = [
            "sourcing", "screening", "interview_hr", 
            "interview_technical", "interview_manager", 
            "offer", "hired", "rejected"
        ]
        
        for stage in stage_order:
            stage_candidates = [c for c in candidates if c.stage == stage]
            metrics.by_stage[stage] = len(stage_candidates)
        
        for i, stage in enumerate(stage_order[:-2]):
            current = metrics.by_stage.get(stage, 0)
            next_stage = stage_order[i + 1]
            next_count = sum(
                metrics.by_stage.get(s, 0) 
                for s in stage_order[i + 1:-1]
            )
            if current > 0:
                rate = (next_count / current) * 100
                metrics.conversion_rates[f"{stage}_to_{next_stage}"] = round(rate, 1)
        
        for stage in stage_order:
            stage_candidates = [c for c in candidates if c.stage == stage]
            if stage_candidates:
                avg_days = sum(c.days_in_stage for c in stage_candidates) / len(stage_candidates)
                metrics.avg_time_by_stage[stage] = round(avg_days, 1)
        
        worst_conversion = 100
        for stage, rate in metrics.conversion_rates.items():
            if rate < worst_conversion:
                worst_conversion = rate
                metrics.bottleneck_stage = stage.split("_to_")[0]
        
        metrics.stalled_candidates = [
            {"id": c.id, "name": c.name, "stage": c.stage, "days": c.days_in_stage}
            for c in candidates
            if c.days_in_stage > 7 and c.stage not in ["hired", "rejected"]
        ]
        
        metrics.candidates_needing_feedback = [
            {"id": c.id, "name": c.name, "stage": c.stage}
            for c in candidates
            if c.stage in ["rejected", "screening"] and not c.has_wsi_screening
        ]
        
        total = metrics.total_candidates
        metrics.by_stage.get("hired", 0)
        metrics.by_stage.get("rejected", 0)
        stalled = len(metrics.stalled_candidates)
        
        if total == 0:
            metrics.health_status = FunnelHealthStatus.ATTENTION
        elif stalled > total * 0.3:
            metrics.health_status = FunnelHealthStatus.CRITICAL
        elif stalled > total * 0.15:
            metrics.health_status = FunnelHealthStatus.ATTENTION
        else:
            metrics.health_status = FunnelHealthStatus.HEALTHY
        
        return metrics
    
    def _parse_salary_min(self, salary: str | None) -> float | None:
        """Extract minimum salary from salary text."""
        if not salary:
            return None
        try:
            import re
            cleaned = salary.replace("R$", "").replace(".", "").replace(",", ".")
            if "k" in cleaned.lower():
                cleaned = cleaned.lower().replace("k", "000")
            numbers = re.findall(r'\d+(?:\.\d+)?', cleaned)
            if numbers:
                return float(numbers[0])
        except Exception:
            pass
        return None
    
    def _parse_salary_max(self, salary: str | None) -> float | None:
        """Extract maximum salary from salary text."""
        if not salary:
            return None
        try:
            import re
            cleaned = salary.replace("R$", "").replace(".", "").replace(",", ".")
            if "k" in cleaned.lower():
                cleaned = cleaned.lower().replace("k", "000")
            numbers = re.findall(r'\d+(?:\.\d+)?', cleaned)
            if len(numbers) >= 2:
                return float(numbers[1])
        except Exception:
            pass
        return None
    
    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
    
    def _parse_experience(self, experience: str | None) -> int | None:
        """Parse experience string to years."""
        if not experience:
            return None
        try:
            import re
            numbers = re.findall(r'\d+', experience)
            if numbers:
                return int(numbers[0])
        except Exception:
            pass
        return None
    
    


job_context_service = JobContextService()
