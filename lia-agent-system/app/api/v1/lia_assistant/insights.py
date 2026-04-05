"""
Insights and expanded-prompt routes:
  POST /lia/job-insights
  POST /lia/expanded-prompt
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.job_vacancy import JobVacancy
from app.services.llm import LLMService
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.dependencies.token_budget import require_token_budget

from ._shared import (
    logger,
    # models
    InsightsRequest,
    InsightsResponse,
    InsightItem,
    ExpandedPromptRequest,
    ExpandedPromptResponse,
    QuestionType,
    # helpers
    detect_question_type,
    handle_salary_question,
    handle_skills_question,
    handle_time_to_fill_question,
    handle_process_question,
)

router = APIRouter()


@router.post("/job-insights", response_model=InsightsResponse)
async def generate_job_insights(
    request: InsightsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Generate dynamic insights for selected jobs.
    Uses Analytics and JobIntake agents for intelligent analysis.
    """
    company_id = current_user.company_id
    insights: List[InsightItem] = []
    summary: Dict[str, Any] = {
        "total_jobs": len(request.job_ids),
        "total_candidates": 0,
        "avg_time_to_fill": 0,
        "health_score": 0
    }

    try:
        jobs_data = []
        total_candidates = 0

        for job_id in request.job_ids:
            try:
                job_query = select(JobVacancy).where(JobVacancy.id == UUID(job_id))
                result = await db.execute(job_query)
                job = result.scalar_one_or_none()

                if job:
                    candidate_count = getattr(job, 'current_candidates', 0) or 0
                    total_candidates += candidate_count

                    jobs_data.append({
                        "id": str(job.id),
                        "title": job.title,
                        "status": job.status,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "deadline": job.deadline.isoformat() if job.deadline else None,
                        "candidates": candidate_count,
                        "priority": getattr(job, 'priority', 'medium')
                    })

                    if job.deadline:
                        days_until_deadline = (job.deadline.date() - datetime.utcnow().date()).days
                        if days_until_deadline <= 7 and days_until_deadline >= 0:
                            insights.append(InsightItem(
                                type="warning",
                                title=f"Prazo próximo: {job.title}",
                                description=f"Vaga expira em {days_until_deadline} dias",
                                severity="high",
                                recommendation="Acelere o processo de triagem ou estenda o prazo",
                                data={"job_id": str(job.id), "days_remaining": days_until_deadline}
                            ))
                        elif days_until_deadline < 0:
                            insights.append(InsightItem(
                                type="critical",
                                title=f"Prazo expirado: {job.title}",
                                description=f"Vaga expirou há {abs(days_until_deadline)} dias",
                                severity="critical",
                                recommendation="Avalie se deve reabrir a vaga com novo prazo",
                                data={"job_id": str(job.id), "days_overdue": abs(days_until_deadline)}
                            ))

                    if candidate_count == 0:
                        insights.append(InsightItem(
                            type="info",
                            title=f"Sem candidatos: {job.title}",
                            description="Esta vaga ainda não recebeu candidaturas",
                            severity="medium",
                            recommendation="Considere ampliar os canais de divulgação ou revisar os requisitos",
                            data={"job_id": str(job.id)}
                        ))

            except Exception as e:
                logger.warning(f"Error processing job {job_id}: {e}")
                continue

        summary["total_candidates"] = total_candidates

        if jobs_data:
            health_factors = []
            for job in jobs_data:
                score = 100
                if job.get("candidates", 0) == 0:
                    score -= 30
                health_factors.append(score)

            summary["health_score"] = sum(health_factors) // len(health_factors) if health_factors else 0

            if summary["health_score"] >= 80:
                insights.append(InsightItem(
                    type="success",
                    title="Pipeline saudável",
                    description=f"Score geral: {summary['health_score']}%",
                    severity="low",
                    data={"score": summary["health_score"]}
                ))
            elif summary["health_score"] >= 50:
                insights.append(InsightItem(
                    type="warning",
                    title="Pipeline precisa de atenção",
                    description=f"Score geral: {summary['health_score']}%",
                    severity="medium",
                    recommendation="Revise as vagas com alertas críticos",
                    data={"score": summary["health_score"]}
                ))
            else:
                insights.append(InsightItem(
                    type="critical",
                    title="Pipeline crítico",
                    description=f"Score geral: {summary['health_score']}%",
                    severity="high",
                    recommendation="Ação urgente necessária nas vagas abertas",
                    data={"score": summary["health_score"]}
                ))

        return InsightsResponse(
            insights=insights,
            summary=summary,
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return InsightsResponse(
            insights=[
                InsightItem(
                    type="error",
                    title="Erro ao gerar insights",
                    description=str(e),
                    severity="high"
                )
            ],
            summary=summary,
            generated_at=datetime.utcnow().isoformat()
        )


async def _handle_jobs_management_query(
    db,
    company_id: str,
    message: str,
    context_ids: Optional[List[str]],
    llm_svc,
) -> str:
    """Handler for job management panel queries with real job data injected."""
    from sqlalchemy import select
    from datetime import datetime

    try:
        query = select(JobVacancy).where(JobVacancy.company_id == company_id)
        if context_ids:
            query = query.where(JobVacancy.id.in_(context_ids))
        else:
            query = query.order_by(JobVacancy.created_at.desc()).limit(30)

        result = await db.execute(query)
        jobs = result.scalars().all()

        now = datetime.utcnow()
        jobs_lines = []
        sla_risk_count = 0

        for job in jobs:
            days_open = (now - job.created_at).days if job.created_at else 0
            sla_flag = ""
            if job.deadline:
                days_to_deadline = (job.deadline - now).days
                if days_to_deadline < 0:
                    sla_flag = " ⚠️ SLA VENCIDO"
                    sla_risk_count += 1
                elif days_to_deadline <= 14:
                    sla_flag = f" ⚠️ SLA em {days_to_deadline}d"
                    sla_risk_count += 1

            salary_info = ""
            if job.salary_range:
                sal = job.salary_range
                salary_info = f" | R$ {sal.get('min', '?'):,}–{sal.get('max', '?'):,}"

            jobs_lines.append(
                f"• [{job.status}] {job.title}"
                f" | {job.department or 'N/A'}"
                f" | {job.seniority_level or 'N/A'}"
                f" | {job.location or 'N/A'}"
                f"{salary_info}"
                f" | Aberta há {days_open}d"
                f" | Prioridade: {job.priority or 'média'}"
                f"{sla_flag}"
            )

        total = len(jobs)
        active = sum(1 for j in jobs if j.status in ("Ativa", "Publicada", "Em andamento"))
        paused = sum(1 for j in jobs if j.status in ("Pausada",))
        draft = sum(1 for j in jobs if j.status in ("Rascunho",))

        jobs_text = "\n".join(jobs_lines) if jobs_lines else "Nenhuma vaga encontrada para esta empresa."
        scope_note = f"vagas selecionadas ({total})" if context_ids else f"últimas {total} vagas"

        prompt = f"""Você é LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Você está auxiliando um RECRUTADOR no painel de gestão de vagas.

=== IMPORTANTE ===
- O usuário é um RECRUTADOR gerenciando as vagas da empresa, NÃO um candidato buscando emprego.
- NUNCA pergunte sobre cargo desejado, localização pessoal, nível de experiência do usuário, tipo de contrato preferido.
- Responda sempre em Português Brasileiro.
- Seja direta, objetiva e profissional.

=== DADOS REAIS DAS VAGAS ({scope_note}) ===
Total: {total} | Ativas/Publicadas: {active} | Pausadas: {paused} | Rascunhos: {draft} | Risco de SLA: {sla_risk_count}

{jobs_text}

=== MENSAGEM DO RECRUTADOR ===
{message}

=== INSTRUÇÕES DE RESPOSTA ===
- Use os dados acima para responder com precisão.
- Se pedir lista, formate como tabela ou lista estruturada com as vagas reais.
- Se pedir análise, analise os dados (SLA, performance, gargalos, prioridades).
- Se pedir comparação, compare as vagas entre si usando os dados disponíveis.
- Destaque alertas de SLA quando relevante.
- Sugira ações concretas quando identificar problemas."""

        return await llm_svc.generate(prompt)

    except Exception as exc:
        logger.warning("[expanded-prompt/jobs] Erro ao buscar vagas: %s", exc)
        prompt = f"""Você é LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Você está auxiliando um RECRUTADOR no painel de gestão de vagas da empresa.
O usuário é RECRUTADOR, não candidato.

Mensagem do recrutador: {message}

Responda em Português Brasileiro de forma útil e profissional.
Não solicite informações pessoais do usuário."""
        return await llm_svc.generate(prompt)


@router.post("/expanded-prompt", response_model=ExpandedPromptResponse)
async def process_expanded_prompt(
    request: ExpandedPromptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    _budget: None = Depends(require_token_budget),
):
    """
    Route expanded commands to appropriate agents based on context.

    Strategy:
    1. For job_creation context: run specialized pre-handlers (salary/skills/time)
       then fall through to full orchestrator for anything else.
    2. For all other contexts: route directly through the full orchestrator
       (with 14-pattern multi-step plan detection enabled).
    3. Orchestrator fallback on any error.
    """
    company_id = current_user.company_id
    user_id = str(current_user.id)

    try:
        llm_svc = LLMService()

        # --- Phase 1: specialized pre-handlers for job_creation context ---
        if request.context_type == "job_creation":
            question_type = detect_question_type(request.message)
            job_context = request.context or {}

            if question_type == QuestionType.SALARY:
                response_text = await handle_salary_question(db, company_id, job_context, request.message)
                return ExpandedPromptResponse(
                    response=response_text,
                    agent_used="salary_insights",
                    actions=[],
                    follow_up_suggestions=["Quer ajustar a faixa salarial?", "Posso comparar com outras vagas similares."],
                )
            elif question_type == QuestionType.SKILLS:
                response_text = await handle_skills_question(db, company_id, job_context, request.message)
                return ExpandedPromptResponse(
                    response=response_text,
                    agent_used="skills_insights",
                    actions=[],
                    follow_up_suggestions=["Quer adicionar essas skills à vaga?", "Posso sugerir competências comportamentais também."],
                )
            elif question_type == QuestionType.TIME_TO_FILL:
                response_text = await handle_time_to_fill_question(db, company_id, job_context, request.message)
                return ExpandedPromptResponse(
                    response=response_text,
                    agent_used="time_insights",
                    actions=[],
                    follow_up_suggestions=["Quer ver as etapas que mais demoram?", "Posso sugerir ações para acelerar o processo."],
                )
            elif question_type == QuestionType.PROCESS:
                response_text = await handle_process_question(request.message, llm_svc)
                return ExpandedPromptResponse(
                    response=response_text,
                    agent_used="process_explainer",
                    actions=[],
                    follow_up_suggestions=["Posso ajudar com mais detalhes sobre o processo."],
                )

        # --- Phase 2: jobs/portfolio specialized handler ---
        if request.context_type in ("jobs", "job_management", "portfolio"):
            response_text = await _handle_jobs_management_query(
                db=db,
                company_id=company_id,
                message=request.message,
                context_ids=request.context_ids,
                llm_svc=llm_svc,
            )
            return ExpandedPromptResponse(
                response=response_text,
                agent_used="jobs_management",
                actions=[],
                follow_up_suggestions=["Quer mais detalhes sobre alguma vaga?", "Posso gerar um relatório completo."],
            )

        # --- Phase 3: Full orchestrator with 14-pattern multi-step detection ---
        try:
            from app.api.orchestrator_routes import get_orchestrator
            orchestrator = get_orchestrator()

            orch_context = {
                "company_id": company_id,
                "source": "expanded_prompt",
                "context_type": request.context_type,
                "context_ids": request.context_ids or [],
            }
            if request.context:
                orch_context.update(request.context)

            conv_id = f"expanded_{user_id}_{request.context_type}"

            result = await orchestrator.process_request(
                user_id=user_id,
                message=request.message,
                conversation_id=conv_id,
                context=orch_context,
            )

            response_text = (
                result.get("message")
                or result.get("response")
                or result.get("content")
                or "Processando sua solicitação..."
            )
            agent_used = result.get("agent", result.get("agent_used", "orchestrator"))
            follow_ups = result.get("suggested_prompts") or result.get("next_actions") or [
                "Posso ajudar com mais alguma coisa?",
                "Quer que eu analise algo mais?",
            ]

            return ExpandedPromptResponse(
                response=response_text,
                agent_used=agent_used,
                actions=result.get("actions", []),
                follow_up_suggestions=follow_ups[:3],
            )

        except Exception as orch_err:
            logger.warning(f"[expanded-prompt] Orchestrator error, falling back to LLM: {orch_err}")
            prompt = f"""Você é LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Você está auxiliando um RECRUTADOR.

Mensagem do recrutador: {request.message}
Contexto: {request.context_type}

Responda em Português Brasileiro de forma útil, clara e profissional."""
            response_text = await llm_svc.generate(prompt, provider="gemini")
            return ExpandedPromptResponse(
                response=response_text,
                agent_used="general_assistant_fallback",
                actions=[],
                follow_up_suggestions=["Posso ajudar com mais alguma informação?"],
            )

    except Exception as e:
        logger.error(f"Error processing expanded prompt: {e}")
        return ExpandedPromptResponse(
            response="Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.",
            agent_used="error_handler",
            actions=[],
            follow_up_suggestions=["Tente novamente ou reformule sua pergunta"],
        )
