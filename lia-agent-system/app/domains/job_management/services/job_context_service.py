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
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class FunnelHealthStatus(str, Enum):
    HEALTHY = "saudável"
    ATTENTION = "atenção"
    CRITICAL = "crítico"


@dataclass
class FunnelMetrics:
    """Metrics for recruitment funnel analysis."""
    total_candidates: int = 0
    by_stage: Dict[str, int] = field(default_factory=dict)
    conversion_rates: Dict[str, float] = field(default_factory=dict)
    avg_time_by_stage: Dict[str, float] = field(default_factory=dict)
    bottleneck_stage: Optional[str] = None
    health_status: FunnelHealthStatus = FunnelHealthStatus.HEALTHY
    stalled_candidates: List[Dict[str, Any]] = field(default_factory=list)
    candidates_needing_feedback: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EnrichedCandidate:
    """Candidate with all relevant scores and metrics."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    stage: Optional[str] = None
    sub_status: Optional[str] = None
    days_in_stage: int = 0
    
    fit_score: Optional[float] = None
    wsi_score: Optional[float] = None
    wsi_technical: Optional[float] = None
    wsi_behavioral: Optional[float] = None
    
    big_five: Dict[str, float] = field(default_factory=dict)
    
    rubric_scores: Dict[str, float] = field(default_factory=dict)
    
    skills: List[str] = field(default_factory=list)
    experience_years: Optional[int] = None
    
    has_cv: bool = False
    has_wsi_screening: bool = False
    has_interview: bool = False
    
    warnings: List[str] = field(default_factory=list)
    last_activity: Optional[datetime] = None


@dataclass
class EnrichedJobContext:
    """Complete enriched context for a job vacancy."""
    job_id: str
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    work_model: Optional[str] = None
    location: Optional[str] = None
    
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    
    required_skills: List[str] = field(default_factory=list)
    desired_skills: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    
    status: str = "active"
    priority: str = "normal"
    deadline: Optional[datetime] = None
    days_open: int = 0
    
    funnel_metrics: FunnelMetrics = field(default_factory=FunnelMetrics)
    
    candidates: List[EnrichedCandidate] = field(default_factory=list)
    
    similar_jobs_avg_time_to_hire: Optional[float] = None
    similar_jobs_avg_candidates: Optional[int] = None


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
    
    def enrich_from_frontend_data(
        self,
        job_context: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        selected_candidate_ids: Optional[List[str]] = None
    ) -> EnrichedJobContext:
        """
        Enrich job context from frontend-provided data.
        
        This is the primary method used when the frontend sends
        job + candidate data directly (as in current KanbanAssistant).
        
        Args:
            job_context: Job data from frontend
            candidates: List of candidates from frontend
            selected_candidate_ids: Optional list of selected candidates
            
        Returns:
            EnrichedJobContext with computed metrics
        """
        enriched_candidates = self._enrich_candidates(candidates)
        
        funnel_metrics = self._compute_funnel_metrics(enriched_candidates)
        
        enriched = EnrichedJobContext(
            job_id=job_context.get("id", "unknown"),
            title=job_context.get("title", "Vaga"),
            department=job_context.get("department"),
            seniority=job_context.get("level"),
            work_model=job_context.get("workModel"),
            location=job_context.get("location"),
            salary_min=self._parse_salary_min(job_context.get("salary")),
            salary_max=self._parse_salary_max(job_context.get("salary")),
            required_skills=job_context.get("skills", []),
            requirements=job_context.get("requirements", []),
            deadline=self._parse_date(job_context.get("deadline")),
            funnel_metrics=funnel_metrics,
            candidates=enriched_candidates
        )
        
        if selected_candidate_ids:
            enriched.candidates = [
                c for c in enriched.candidates 
                if c.id in selected_candidate_ids
            ] + [
                c for c in enriched.candidates 
                if c.id not in selected_candidate_ids
            ]
            for c in enriched.candidates:
                if c.id in selected_candidate_ids:
                    c.warnings.insert(0, "SELECIONADO")
        
        return enriched
    
    def _enrich_candidates(
        self, 
        candidates: List[Dict[str, Any]]
    ) -> List[EnrichedCandidate]:
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
        candidates: List[EnrichedCandidate]
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
        hired = metrics.by_stage.get("hired", 0)
        rejected = metrics.by_stage.get("rejected", 0)
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
    
    def _parse_salary_min(self, salary: Optional[str]) -> Optional[float]:
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
    
    def _parse_salary_max(self, salary: Optional[str]) -> Optional[float]:
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
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
    
    def _parse_experience(self, experience: Optional[str]) -> Optional[int]:
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
    
    def to_context_dict(self, enriched: EnrichedJobContext) -> Dict[str, Any]:
        """
        Convert EnrichedJobContext to a dictionary for agent consumption.
        
        Returns a structured dict optimized for LLM context.
        """
        return {
            "job": {
                "id": enriched.job_id,
                "title": enriched.title,
                "department": enriched.department,
                "seniority": enriched.seniority,
                "work_model": enriched.work_model,
                "location": enriched.location,
                "salary_range": f"R$ {enriched.salary_min:,.0f} - R$ {enriched.salary_max:,.0f}" if enriched.salary_min and enriched.salary_max else None,
                "required_skills": enriched.required_skills,
                "desired_skills": enriched.desired_skills,
                "requirements": enriched.requirements,
                "status": enriched.status,
                "priority": enriched.priority,
                "deadline": enriched.deadline.isoformat() if enriched.deadline else None,
                "days_open": enriched.days_open
            },
            "funnel": {
                "total_candidates": enriched.funnel_metrics.total_candidates,
                "by_stage": enriched.funnel_metrics.by_stage,
                "conversion_rates": enriched.funnel_metrics.conversion_rates,
                "avg_time_by_stage_days": enriched.funnel_metrics.avg_time_by_stage,
                "bottleneck_stage": enriched.funnel_metrics.bottleneck_stage,
                "health_status": enriched.funnel_metrics.health_status.value,
                "stalled_candidates_count": len(enriched.funnel_metrics.stalled_candidates),
                "stalled_candidates": enriched.funnel_metrics.stalled_candidates[:5],
                "candidates_needing_feedback_count": len(enriched.funnel_metrics.candidates_needing_feedback),
                "candidates_needing_feedback": enriched.funnel_metrics.candidates_needing_feedback[:5]
            },
            "candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "stage": c.stage,
                    "sub_status": c.sub_status,
                    "days_in_stage": c.days_in_stage,
                    "fit_score": c.fit_score,
                    "wsi_score": c.wsi_score,
                    "wsi_technical": c.wsi_technical,
                    "wsi_behavioral": c.wsi_behavioral,
                    "big_five": c.big_five if c.big_five else None,
                    "skills": c.skills,
                    "experience_years": c.experience_years,
                    "has_cv": c.has_cv,
                    "has_wsi_screening": c.has_wsi_screening,
                    "has_interview": c.has_interview,
                    "warnings": c.warnings,
                    "role": c.role,
                    "current_company": c.current_company,
                    "location": c.location
                }
                for c in enriched.candidates
            ],
            "benchmarks": {
                "similar_jobs_avg_time_to_hire": enriched.similar_jobs_avg_time_to_hire,
                "similar_jobs_avg_candidates": enriched.similar_jobs_avg_candidates
            }
        }
    
    def get_summary_for_agents(self, enriched: EnrichedJobContext) -> str:
        """
        Generate a text summary for agent context injection.
        
        This is optimized for LLM consumption with key insights highlighted.
        """
        fm = enriched.funnel_metrics
        
        top_candidates = sorted(
            [c for c in enriched.candidates if c.wsi_score],
            key=lambda x: x.wsi_score or 0,
            reverse=True
        )[:5]
        
        summary_parts = [
            f"# Contexto da Vaga: {enriched.title}",
            "",
            f"**Departamento:** {enriched.department or 'N/A'}",
            f"**Senioridade:** {enriched.seniority or 'N/A'}",
            f"**Modelo:** {enriched.work_model or 'N/A'}",
            f"**Localização:** {enriched.location or 'N/A'}",
            "",
            "## Funil de Recrutamento",
            f"- Total de candidatos: {fm.total_candidates}",
            f"- Status do funil: {fm.health_status.value.upper()}",
        ]
        
        if fm.by_stage:
            summary_parts.append("- Distribuição por etapa:")
            for stage, count in fm.by_stage.items():
                if count > 0:
                    summary_parts.append(f"  - {stage}: {count}")
        
        if fm.bottleneck_stage:
            summary_parts.append(f"- **Gargalo identificado:** {fm.bottleneck_stage}")
        
        if fm.stalled_candidates:
            summary_parts.append(f"- Candidatos parados (>7 dias): {len(fm.stalled_candidates)}")
        
        if fm.candidates_needing_feedback:
            summary_parts.append(f"- Candidatos aguardando feedback: {len(fm.candidates_needing_feedback)}")
        
        if top_candidates:
            summary_parts.append("")
            summary_parts.append("## Top 5 Candidatos por WSI Score")
            for i, c in enumerate(top_candidates, 1):
                summary_parts.append(
                    f"{i}. {c.name} - WSI: {c.wsi_score:.1f} | "
                    f"Fit: {c.fit_score or 'N/A'}% | "
                    f"Etapa: {c.stage}"
                )
        
        return "\n".join(summary_parts)


job_context_service = JobContextService()
