"""
Deadline Calculator Service - Calculate job vacancy deadlines from pipeline SLAs.

Calculates:
- deadline_screening: When screening phase should be completed
- deadline_shortlist: When shortlist should be ready
- deadline_closing: Final deadline for closing the position
- deadline: Overall deadline (sum of all SLAs)

Uses SLAs defined in PipelineTemplate stages.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from lia_models.pipeline_template import PipelineTemplate

logger = logging.getLogger(__name__)


class DeadlineCalculatorService:
    """Service for calculating job vacancy deadlines based on pipeline SLAs."""
    
    DEFAULT_SCREENING_DAYS = 3
    DEFAULT_SHORTLIST_DAYS = 7
    DEFAULT_INTERVIEW_DAYS = 14
    DEFAULT_CLOSING_DAYS = 21
    
    def calculate_deadlines_from_sla(
        self,
        stages: list[dict[str, Any]],
        start_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Calculate deadlines from pipeline stage SLAs.
        
        Args:
            stages: List of stage dicts with 'name', 'order', 'sla_days'
            start_date: Start date for calculations (default: now)
            
        Returns:
            Dict with calculated deadlines:
            {
                "deadline_screening": datetime,
                "deadline_shortlist": datetime,
                "deadline_closing": datetime,
                "deadline": datetime,
                "total_sla_days": int,
                "breakdown": [{"stage": "...", "sla_days": X, "deadline": datetime}]
            }
        """
        if not start_date:
            start_date = datetime.utcnow()
        
        if not stages:
            return self._get_default_deadlines(start_date)
        
        sorted_stages = sorted(stages, key=lambda x: x.get("order", 0))
        
        cumulative_days = 0
        breakdown = []
        screening_deadline = None
        shortlist_deadline = None
        
        for stage in sorted_stages:
            stage_name = stage.get("name", "").lower()
            sla_days = stage.get("sla_days", 3)
            cumulative_days += sla_days
            
            stage_deadline = start_date + timedelta(days=cumulative_days)
            
            breakdown.append({
                "stage": stage.get("name", "Unknown"),
                "sla_days": sla_days,
                "cumulative_days": cumulative_days,
                "deadline": stage_deadline.isoformat()
            })
            
            if any(kw in stage_name for kw in ["triagem", "screening", "cv", "currículo"]):
                screening_deadline = stage_deadline
            
            if any(kw in stage_name for kw in ["shortlist", "seleção", "entrevista técnica"]):
                shortlist_deadline = stage_deadline
        
        closing_deadline = start_date + timedelta(days=cumulative_days)
        
        if not screening_deadline:
            first_stage_sla = sorted_stages[0].get("sla_days", self.DEFAULT_SCREENING_DAYS) if sorted_stages else self.DEFAULT_SCREENING_DAYS
            screening_deadline = start_date + timedelta(days=first_stage_sla)
        
        if not shortlist_deadline:
            midpoint_days = cumulative_days // 2 if cumulative_days > 0 else self.DEFAULT_SHORTLIST_DAYS
            shortlist_deadline = start_date + timedelta(days=midpoint_days)
        
        return {
            "deadline_screening": screening_deadline,
            "deadline_shortlist": shortlist_deadline,
            "deadline_closing": closing_deadline,
            "deadline": closing_deadline,
            "open_date": start_date,
            "total_sla_days": cumulative_days,
            "breakdown": breakdown
        }
    
    def _get_default_deadlines(self, start_date: datetime) -> dict[str, Any]:
        """Get default deadlines when no pipeline is specified."""
        return {
            "deadline_screening": start_date + timedelta(days=self.DEFAULT_SCREENING_DAYS),
            "deadline_shortlist": start_date + timedelta(days=self.DEFAULT_SHORTLIST_DAYS),
            "deadline_closing": start_date + timedelta(days=self.DEFAULT_CLOSING_DAYS),
            "deadline": start_date + timedelta(days=self.DEFAULT_CLOSING_DAYS),
            "open_date": start_date,
            "total_sla_days": self.DEFAULT_CLOSING_DAYS,
            "breakdown": [
                {"stage": "Triagem", "sla_days": self.DEFAULT_SCREENING_DAYS, "cumulative_days": self.DEFAULT_SCREENING_DAYS, "deadline": (start_date + timedelta(days=self.DEFAULT_SCREENING_DAYS)).isoformat()},
                {"stage": "Entrevistas", "sla_days": self.DEFAULT_SHORTLIST_DAYS - self.DEFAULT_SCREENING_DAYS, "cumulative_days": self.DEFAULT_SHORTLIST_DAYS, "deadline": (start_date + timedelta(days=self.DEFAULT_SHORTLIST_DAYS)).isoformat()},
                {"stage": "Proposta", "sla_days": self.DEFAULT_CLOSING_DAYS - self.DEFAULT_SHORTLIST_DAYS, "cumulative_days": self.DEFAULT_CLOSING_DAYS, "deadline": (start_date + timedelta(days=self.DEFAULT_CLOSING_DAYS)).isoformat()}
            ]
        }
    
    async def calculate_deadlines_from_pipeline(
        self,
        pipeline_template_id: str | None,
        company_id: str,
        start_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Calculate deadlines from a specific pipeline template.
        
        Args:
            pipeline_template_id: ID of the pipeline template (optional)
            company_id: Company ID for multi-tenancy
            start_date: Start date for calculations (default: now)
            
        Returns:
            Dict with calculated deadlines and metadata
        """
        if not start_date:
            start_date = datetime.utcnow()
        
        stages = []
        pipeline_name = "Padrão"
        
        async with AsyncSessionLocal() as db:
            if pipeline_template_id:
                # ADR-001-EXEMPT: PipelineTemplate is owned by job_management/screening pipeline
                # surface; no repo exposes it today. Sprint 6 follow-up: add PipelineTemplateRepository.
                result = await db.execute(
                    select(PipelineTemplate).where(
                        PipelineTemplate.id == pipeline_template_id
                    )
                )
                pipeline = result.scalar_one_or_none()
                
                if pipeline:
                    pipeline_stages = pipeline.stages
                    if pipeline_stages:
                        stages = list(pipeline_stages) if pipeline_stages else []
                        pipeline_name = str(pipeline.name) if pipeline.name else "Padrão"
            
            if not stages:
                result = await db.execute(
                    select(PipelineTemplate).where(
                        PipelineTemplate.company_id == company_id,
                        PipelineTemplate.is_default,
                        PipelineTemplate.is_active
                    )
                )
                default_pipeline = result.scalar_one_or_none()
                
                if default_pipeline:
                    default_stages = default_pipeline.stages
                    if default_stages:
                        stages = list(default_stages) if default_stages else []
                        pipeline_name = str(default_pipeline.name) if default_pipeline.name else "Padrão"
        
        deadlines = self.calculate_deadlines_from_sla(stages, start_date)
        deadlines["pipeline_name"] = pipeline_name
        deadlines["source"] = "pipeline_sla" if stages else "default"
        
        return deadlines
    
    def adjust_deadline(
        self,
        current_deadline: datetime,
        days_to_add: int
    ) -> datetime:
        """
        Adjust a deadline by adding days.
        
        Args:
            current_deadline: Current deadline
            days_to_add: Days to add (can be negative)
            
        Returns:
            New adjusted deadline
        """
        return current_deadline + timedelta(days=days_to_add)
    
    def calculate_sla_status(
        self,
        deadline: datetime,
        current_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Calculate SLA status for a deadline.
        
        Args:
            deadline: The deadline to check
            current_date: Current date (default: now)
            
        Returns:
            Dict with SLA status:
            {
                "within_sla": bool,
                "days_remaining": int,
                "status": "on_track" | "at_risk" | "overdue",
                "urgency_level": 1-5
            }
        """
        if not current_date:
            current_date = datetime.utcnow()
        
        days_remaining = (deadline - current_date).days
        
        if days_remaining < 0:
            status = "overdue"
            urgency_level = 5
            within_sla = False
        elif days_remaining <= 2:
            status = "at_risk"
            urgency_level = 4
            within_sla = True
        elif days_remaining <= 5:
            status = "at_risk"
            urgency_level = 3
            within_sla = True
        else:
            status = "on_track"
            urgency_level = 1 if days_remaining > 14 else 2
            within_sla = True
        
        return {
            "within_sla": within_sla,
            "days_remaining": days_remaining,
            "status": status,
            "urgency_level": urgency_level,
            "deadline": deadline.isoformat()
        }
    
    def format_deadlines_for_display(
        self,
        deadlines: dict[str, Any]
    ) -> dict[str, str]:
        """
        Format deadlines for display in UI.
        
        Args:
            deadlines: Dict with datetime deadlines
            
        Returns:
            Dict with formatted strings
        """
        def format_date(dt: Any) -> str:
            if not dt:
                return "Não definido"
            if isinstance(dt, datetime):
                return dt.strftime("%d/%m/%Y")
            return str(dt)
        
        return {
            "deadline_screening": format_date(deadlines.get("deadline_screening")),
            "deadline_shortlist": format_date(deadlines.get("deadline_shortlist")),
            "deadline_closing": format_date(deadlines.get("deadline_closing")),
            "deadline": format_date(deadlines.get("deadline")),
            "total_days": f"{deadlines.get('total_sla_days', 0)} dias",
            "pipeline": deadlines.get("pipeline_name", "Padrão")
        }


deadline_calculator_service = DeadlineCalculatorService()



def derive_deadlines_from_stages(stages):
    """Onda 2D (audit 2026-06-06): normaliza interview_stages (sla_hours|sla_days) e
    devolve os 4 prazos da vaga (deadline_screening/shortlist/closing/deadline) como
    soma cumulativa dos SLAs das etapas. Fonte = SLA do pipeline (não edição manual).

    Robust: ignora entradas não-dict; converte sla_hours->dias; default 3 dias por etapa.
    """
    norm = []
    for i, st in enumerate(stages or []):
        if not isinstance(st, dict):
            continue
        sla_days = st.get("sla_days")
        if sla_days is None and st.get("sla_hours") is not None:
            try:
                sla_days = max(1, round(float(st["sla_hours"]) / 24))
            except (TypeError, ValueError):
                sla_days = None
        norm.append({
            "name": st.get("name") or st.get("display_name") or st.get("displayName") or "",
            "order": st.get("order", i),
            "sla_days": sla_days if sla_days is not None else 3,
        })
    result = deadline_calculator_service.calculate_deadlines_from_sla(norm)
    return {
        k: result[k]
        for k in ("deadline_screening", "deadline_shortlist", "deadline_closing", "deadline")
    }
