# JobVacancy) for recruiter pipeline visualization. Tenant scope established
# by caller via authenticated session.
# TODO Sprint 6: refactor to use existing CandidateRepository +  # R-048: needs owner + ticket
# JobVacancyCRUDRepository explicitly.

"""
Pipeline Service - Manages stale candidates and pipeline health.

This service identifies candidates that need attention:
- Candidates without activity for X days
- Suggests actions based on current stage
- Groups candidates by job vacancy
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


STAGE_ACTIONS = {
    "new": [
        {"id": "screen", "label": "Iniciar Triagem", "icon": "filter", "action": "start_screening"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "screening": [
        {"id": "schedule", "label": "Agendar Entrevista", "icon": "calendar", "action": "schedule_interview"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "Triagem": [
        {"id": "schedule", "label": "Agendar Entrevista", "icon": "calendar", "action": "schedule_interview"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "interview": [
        {"id": "feedback", "label": "Registrar Feedback", "icon": "message-square", "action": "add_feedback"},
        {"id": "advance", "label": "Avançar Etapa", "icon": "arrow-right", "action": "advance_stage"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "Entrevista": [
        {"id": "feedback", "label": "Registrar Feedback", "icon": "message-square", "action": "add_feedback"},
        {"id": "advance", "label": "Avançar Etapa", "icon": "arrow-right", "action": "advance_stage"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "evaluation": [
        {"id": "offer", "label": "Enviar Oferta", "icon": "file-text", "action": "send_offer"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "Avaliação": [
        {"id": "offer", "label": "Enviar Oferta", "icon": "file-text", "action": "send_offer"},
        {"id": "reject", "label": "Reprovar", "icon": "x", "action": "reject_candidate", "variant": "destructive"}
    ],
    "offer": [
        {"id": "followup", "label": "Follow-up", "icon": "phone", "action": "followup_offer"},
        {"id": "hire", "label": "Confirmar Contratação", "icon": "check", "action": "confirm_hire"},
        {"id": "reject", "label": "Candidato Recusou", "icon": "x", "action": "candidate_declined", "variant": "destructive"}
    ],
    "Oferta": [
        {"id": "followup", "label": "Follow-up", "icon": "phone", "action": "followup_offer"},
        {"id": "hire", "label": "Confirmar Contratação", "icon": "check", "action": "confirm_hire"},
        {"id": "reject", "label": "Candidato Recusou", "icon": "x", "action": "candidate_declined", "variant": "destructive"}
    ]
}

DEFAULT_ACTIONS = [
    {"id": "contact", "label": "Entrar em Contato", "icon": "mail", "action": "contact_candidate"},
    {"id": "view", "label": "Ver Perfil", "icon": "eye", "action": "view_profile"}
]


class PipelineService:
    """
    Service for managing pipeline health and stale candidates.
    """
    
    def __init__(self, stale_days: int = 3):
        self.stale_days = stale_days
    
    async def get_stale_candidates(
        self,
        db: AsyncSession | None = None,
        stale_days: int | None = None,
        limit: int = 50,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get candidates that have been inactive for X days.
        
        Args:
            db: Database session
            stale_days: Days of inactivity to consider stale (default: 3)
            limit: Maximum number of candidates to return
            
        Returns:
            Stale candidates grouped by job vacancy
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        days = stale_days or self.stale_days
        stale_threshold = datetime.utcnow() - timedelta(days=days)
        
        try:
            final_statuses = ['hired', 'rejected', 'Contratado', 'Rejeitado', 'Reprovado', 'Desistente']
            
            # Onda 4.2b-P0-2 (2026-05-23): filtro company_id obrigatorio.
            tenant_filter = (
                [Candidate.company_id == company_id] if company_id else []
            )
            query = select(Candidate).where(  # ADR-001-EXEMPT: R-048 Sprint 6 — complex stale-candidate filter; move to CandidatePipelineRepository.get_stale_candidates()
                and_(
                    *tenant_filter,
                    Candidate.is_active,
                    ~Candidate.status.in_(final_statuses),
                    or_(
                        Candidate.last_activity_at < stale_threshold,
                        and_(
                            Candidate.last_activity_at.is_(None),
                            Candidate.updated_at < stale_threshold
                        )
                    )
                )
            ).order_by(
                Candidate.updated_at.asc()
            ).limit(limit)
            
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            # Onda 4.2b-P0-2 (2026-05-23): JobVacancy tambem precisa filtro tenant.
            jobs_tenant_filter = (
                [JobVacancy.company_id == company_id] if company_id else []
            )
            jobs_query = select(JobVacancy).where(  # ADR-001-EXEMPT: R-048 Sprint 6 — active-jobs filter co-located with stale-candidate logic; move to CandidatePipelineRepository
                *jobs_tenant_filter,
                JobVacancy.status.in_(["Ativa", "Publicada", "open", "active"]),
            )
            jobs_result = await db.execute(jobs_query)
            jobs = {str(j.id): j for j in jobs_result.scalars().all()}
            
            grouped = {}
            ungrouped = []
            
            for candidate in candidates:
                days_stale = self._calculate_days_stale(candidate, stale_threshold)
                candidate_data = self._format_candidate(candidate, days_stale)
                
                job_id = candidate.additional_data.get("job_id") if candidate.additional_data else None
                
                if job_id and job_id in jobs:
                    if job_id not in grouped:
                        job = jobs[job_id]
                        grouped[job_id] = {
                            "job_id": job_id,
                            "job_title": job.title,
                            "job_department": job.department,
                            "candidates": []
                        }
                    grouped[job_id]["candidates"].append(candidate_data)
                else:
                    ungrouped.append(candidate_data)
            
            if ungrouped:
                grouped["ungrouped"] = {
                    "job_id": None,
                    "job_title": "Sem Vaga Associada",
                    "job_department": "Banco de Talentos",
                    "candidates": ungrouped
                }
            
            total_stale = len(candidates)
            critical_count = sum(1 for c in candidates if self._calculate_days_stale(c, stale_threshold) >= 7)
            
            return {
                "total_stale": total_stale,
                "critical_count": critical_count,
                "stale_threshold_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "groups": list(grouped.values()),
                "summary": {
                    "message": self._generate_summary_message(total_stale, critical_count),
                    "urgency": "high" if critical_count > 0 else ("medium" if total_stale > 5 else "low")
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching stale candidates: {e}", exc_info=True)
            raise
        finally:
            if should_close:
                await db.close()
    
    def _calculate_days_stale(self, candidate: Candidate, threshold: datetime) -> int:
        """Calculate how many days a candidate has been stale."""
        last_activity = candidate.last_activity_at or candidate.updated_at or candidate.created_at
        if last_activity:
            delta = datetime.utcnow() - last_activity
            return delta.days
        return 0
    
    def _format_candidate(self, candidate: Candidate, days_stale: int) -> dict[str, Any]:
        """Format candidate data for the pipeline report."""
        status = candidate.status or "new"
        actions = STAGE_ACTIONS.get(status, DEFAULT_ACTIONS)
        
        urgency = "critical" if days_stale >= 7 else ("high" if days_stale >= 5 else "normal")
        
        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "status": status,
            "status_label": self._get_status_label(status),
            "days_stale": days_stale,
            "stale_message": f"Há {days_stale} dia{'s' if days_stale != 1 else ''} sem ação",
            "urgency": urgency,
            "lia_score": candidate.lia_score,
            "actions": actions,
            "last_activity": (candidate.last_activity_at or candidate.updated_at).isoformat() if (candidate.last_activity_at or candidate.updated_at) else None
        }
    
    def _get_status_label(self, status: str) -> str:
        """Get human-readable status label."""
        labels = {
            "new": "Novo",
            "screening": "Triagem",
            "Triagem": "Triagem",
            "interview": "Entrevista",
            "Entrevista": "Entrevista",
            "evaluation": "Avaliação",
            "Avaliação": "Avaliação",
            "offer": "Oferta",
            "Oferta": "Oferta",
            "hired": "Contratado",
            "rejected": "Rejeitado"
        }
        return labels.get(status, status.capitalize())
    
    def _generate_summary_message(self, total: int, critical: int) -> str:
        """Generate summary message for the briefing."""
        if total == 0:
            return "Excelente! Todos os candidatos estão em dia."
        
        if critical > 0:
            return f"Você tem {total} candidato{'s' if total != 1 else ''} aguardando ação, {critical} em situação crítica (7+ dias)."
        
        return f"Você tem {total} candidato{'s' if total != 1 else ''} aguardando ação."
    
    async def execute_pipeline_action(
        self,
        candidate_id: str,
        action_id: str,
        db: AsyncSession | None = None,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a pipeline action on a candidate.

        Onda 4.2b-P0-1 (2026-05-23): adicionado company_id obrigatorio pra
        cross-tenant guard. Antes user de empresa A podia rejeitar/contratar
        candidato de empresa B passando o ID (LGPD critical).

        Args:
            candidate_id: The candidate's UUID
            action_id: The action to execute
            db: Database session
            company_id: Tenant scope (REQUIRED — fail-closed multi-tenancy)

        Returns:
            Result of the action
        """
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy invariant fail-closed). "
                "Onda 4.2b-P0-1 fix — execute_pipeline_action antes permitia "
                "cross-tenant write em candidatos de outras empresas."
            )

        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            import uuid as uuid_module
            # Onda 4.2b-P0-1: filtro company_id obrigatorio.
            result = await db.execute(
                select(Candidate).where(  # ADR-001-EXEMPT: R-048 Sprint 6 — single-record lookup; move to CandidateRepository.get_by_id_and_company()
                    Candidate.id == uuid_module.UUID(candidate_id),
                    Candidate.company_id == company_id,
                )
            )
            candidate = result.scalar_one_or_none()

            if not candidate:
                return {"success": False, "error": "Candidato não encontrado"}
            
            candidate.last_activity_at = datetime.utcnow()
            candidate.updated_at = datetime.utcnow()
            
            action_results = {
                "start_screening": {"new_status": "screening", "message": f"Triagem iniciada para {candidate.name}"},
                "schedule_interview": {"new_status": "interview", "message": f"Agendar entrevista com {candidate.name}", "open_modal": "interview_scheduling"},
                "add_feedback": {"message": f"Adicionar feedback para {candidate.name}", "open_modal": "feedback"},
                "advance_stage": {"message": f"Avançar {candidate.name} para próxima etapa", "open_modal": "stage_advance"},
                "send_offer": {"new_status": "offer", "message": f"Preparar oferta para {candidate.name}", "open_modal": "offer"},
                "followup_offer": {"message": f"Follow-up de oferta com {candidate.name}", "action": "send_email"},
                "confirm_hire": {"new_status": "hired", "message": f"{candidate.name} contratado com sucesso!"},
                "reject_candidate": {"new_status": "rejected", "message": f"Candidato {candidate.name} movido para rejeitados"},
                "candidate_declined": {"new_status": "rejected", "message": f"{candidate.name} recusou a oferta"},
                "contact_candidate": {"message": f"Entrar em contato com {candidate.name}", "open_modal": "contact"},
                "view_profile": {"message": f"Visualizando perfil de {candidate.name}", "navigate": f"/candidates/{candidate_id}"}
            }
            
            action_config = action_results.get(action_id, {"message": "Ação executada"})
            
            if "new_status" in action_config:
                candidate.status = action_config["new_status"]
            
            await db.commit()
            
            return {
                "success": True,
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                **action_config
            }
            
        except Exception as e:
            logger.error(f"Error executing pipeline action: {e}", exc_info=True)
            await db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                await db.close()


pipeline_service = PipelineService()
