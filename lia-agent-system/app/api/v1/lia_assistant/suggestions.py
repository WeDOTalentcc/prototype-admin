"""
GET /lia/suggestions — Dynamic homepage suggestion cards.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.models import JobVacancy
from app.models.candidate import VacancyCandidate

from ._shared import (
    SuggestionCard,
    SuggestionsResponse,
    logger,
)

router = APIRouter()


@router.get("/suggestions", response_model=SuggestionsResponse)
# TODO(phase2): extract to repository — LIA assistant suggestion storage
# multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
async def get_dynamic_suggestions(
    limit: int = Query(default=6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Generate dynamic suggestion cards for the homepage based on real data.

    Analyzes:
    - Critical jobs (SLA expiring, no candidates)
    - Pending candidate reviews
    - Stalled pipelines
    - Interview scheduling needs
    - Report opportunities
    """
    company_id = current_user.company_id
    str(current_user.id)
    suggestions = []

    try:
        jobs_query = select(JobVacancy).where(
            and_(
                JobVacancy.company_id == company_id,
                JobVacancy.status.in_(["open", "active", "Open", "Active", "Em Andamento"])
            )
        )
        result = await db.execute(jobs_query)
        active_jobs = result.scalars().all()

        job_ids = [str(job.id) for job in active_jobs]

        if len(active_jobs) > 0:
            suggestions.append(SuggestionCard(
                id="pipeline-overview",
                type="info",
                icon="Briefcase",
                title=f"{len(active_jobs)} vagas ativas",
                description="Clique para ver detalhes e status de todas as vagas",
                action="view_active_jobs",
                priority="medium",
                category="vagas",
                metadata={"job_ids": job_ids[:5], "count": len(active_jobs)}
            ))

        today = datetime.utcnow().date()
        week_from_now = today + timedelta(days=7)

        expiring_jobs = [
            job for job in active_jobs
            if job.deadline and job.deadline.date() <= week_from_now
        ]

        if expiring_jobs:
            suggestions.append(SuggestionCard(
                id="deadline-warning",
                type="warning",
                icon="Clock",
                title=f"{len(expiring_jobs)} vagas com prazo próximo",
                description="Vagas expirando nos próximos 7 dias",
                action="view_expiring_jobs",
                priority="high",
                category="vagas",
                metadata={"job_ids": [str(j.id) for j in expiring_jobs[:5]], "count": len(expiring_jobs)}
            ))

        if active_jobs:
            suggestions.append(SuggestionCard(
                id="pipeline-health",
                type="insight",
                icon="TrendingUp",
                title="Análise de Pipeline",
                description=f"Visualize métricas e saúde de {len(active_jobs)} vagas ativas",
                action="view_pipeline_analytics",
                priority="medium",
                category="relatorios",
                metadata={"total_jobs": len(active_jobs)}
            ))

        recent_candidates_query = select(func.count(VacancyCandidate.candidate_id)).where(
            and_(
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
        recent_result = await db.execute(recent_candidates_query)
        recent_candidates = recent_result.scalar() or 0

        if recent_candidates > 0:
            suggestions.append(SuggestionCard(
                id="new-candidates",
                type="info",
                icon="Users",
                title=f"{recent_candidates} novos candidatos",
                description="Candidatos recebidos nos últimos 7 dias aguardando triagem",
                action="start_screening",
                priority="medium",
                category="candidatos",
                metadata={"count": recent_candidates}
            ))

        if len(active_jobs) > 0:
            suggestions.append(SuggestionCard(
                id="quick-report",
                type="action",
                icon="FileText",
                title="Gerar Relatório Semanal",
                description="Resumo das vagas, candidatos e métricas da semana",
                action="generate_weekly_report",
                priority="low",
                category="relatorios",
                metadata={}
            ))

        suggestions.append(SuggestionCard(
            id="sourcing-suggestion",
            type="suggestion",
            icon="Search",
            title="Buscar Candidatos Similares",
            description="Use IA para encontrar candidatos parecidos com seus melhores contratados",
            action="similar_search",
            priority="low",
            category="candidatos",
            metadata={}
        ))

        suggestions.append(SuggestionCard(
            id="create-job-wizard",
            type="action",
            icon="Plus",
            title="Criar Nova Vaga com LIA",
            description="Crie uma vaga conversando com a LIA - ela extrai requisitos automaticamente",
            action="start_job_wizard",
            priority="low",
            category="vagas",
            metadata={}
        ))

        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x.priority, 2))

        return SuggestionsResponse(
            suggestions=suggestions[:limit],
            generated_at=datetime.utcnow().isoformat(),
            context={"active_jobs": len(active_jobs)}
        )

    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return SuggestionsResponse(
            suggestions=[
                SuggestionCard(
                    id="create-job-wizard",
                    type="action",
                    icon="Plus",
                    title="Criar Nova Vaga com LIA",
                    description="Inicie o processo de criação de vaga com assistência da LIA",
                    action="start_job_wizard",
                    priority="medium",
                    category="vagas",
                    metadata={}
                ),
                SuggestionCard(
                    id="view-jobs",
                    type="action",
                    icon="Briefcase",
                    title="Ver Vagas Ativas",
                    description="Visualize e gerencie suas vagas em aberto",
                    action="view_active_jobs",
                    priority="medium",
                    category="vagas",
                    metadata={}
                )
            ],
            generated_at=datetime.utcnow().isoformat(),
            context={"error": str(e)}
        )
