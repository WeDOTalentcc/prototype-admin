"""
Job Analytics Prompt Service - Routes natural language queries to specialized agents.

This service connects the LIA prompt to specialized agents for job-related analyses,
metrics, and insights.

Architecture:
- Routes natural language queries about jobs to appropriate specialized agents
- Supports single job, multiple jobs, or portfolio-wide analysis
- Returns structured responses suitable for chat display
"""
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.agents.agent_types import AgentType
from app.core.database import AsyncSessionLocal
from lia_models.candidate import VacancyCandidate
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


COMMAND_TEMPLATES = {
    "funnel_analysis": {
        "name": "Análise de Funil",
        "description": "Analisa o funil de recrutamento da vaga",
        "prompt_template": "Analise o funil da vaga {job_title}. Mostre: candidatos por etapa, taxa de conversão, gargalos, tempo médio por etapa.",
        "agent": "AnalistaFeedbackAgent",
        "agent_type": AgentType.ANALYST_FEEDBACK,
        "required_context": ["job_id"],
        "intent": "analyze_funnel"
    },
    "comparative_analysis": {
        "name": "Análise Comparativa",
        "description": "Compara métricas entre vagas",
        "prompt_template": "Compare as vagas selecionadas: {job_titles}. Analise: tempo médio, taxa de conversão, qualidade de candidatos.",
        "agent": "AnalistaFeedbackAgent",
        "agent_type": AgentType.ANALYST_FEEDBACK,
        "required_context": ["job_ids"],
        "intent": "comparar_vagas"
    },
    "bottleneck_detection": {
        "name": "Detecção de Gargalos",
        "description": "Identifica gargalos no processo",
        "prompt_template": "Identifique gargalos na vaga {job_title}: etapas com maior tempo de espera, candidatos parados, ações pendentes.",
        "agent": "AnalistaFeedbackAgent",
        "agent_type": AgentType.ANALYST_FEEDBACK,
        "required_context": ["job_id"],
        "intent": "detect_anomalies"
    },
    "time_to_fill_prediction": {
        "name": "Previsão de Fechamento",
        "description": "Prevê quando a vaga será preenchida",
        "prompt_template": "Preveja o tempo para preencher a vaga {job_title} com base em dados históricos e progresso atual.",
        "agent": "AnalistaFeedbackAgent",
        "agent_type": AgentType.ANALYST_FEEDBACK,
        "required_context": ["job_id"],
        "intent": "forecast_metrics"
    },
    "candidate_quality_score": {
        "name": "Score de Qualidade",
        "description": "Avalia qualidade média dos candidatos",
        "prompt_template": "Avalie a qualidade dos candidatos da vaga {job_title}: fit técnico médio, fit cultural, diversidade de fontes.",
        "agent": "AvaliadorWSIAgent",
        "agent_type": AgentType.WSI_EVALUATOR,
        "required_context": ["job_id"],
        "intent": "evaluate_candidates"
    },
    "sourcing_effectiveness": {
        "name": "Efetividade de Sourcing",
        "description": "Analisa fontes de candidatos",
        "prompt_template": "Analise a efetividade do sourcing para {job_title}: melhores canais, taxa de conversão por fonte, custo por candidato.",
        "agent": "SourcingAgent",
        "agent_type": AgentType.SOURCING,
        "required_context": ["job_id"],
        "intent": "analyze_sourcing"
    },
    "weekly_summary": {
        "name": "Resumo Semanal",
        "description": "Resumo da semana de recrutamento",
        "prompt_template": "Gere o resumo semanal de recrutamento: novos candidatos, movimentações, entrevistas realizadas, propostas enviadas.",
        "agent": "AnalistaFeedbackAgent",
        "agent_type": AgentType.ANALYST_FEEDBACK,
        "required_context": [],
        "intent": "generate_kpi_report"
    },
    "salary_benchmark": {
        "name": "Benchmark Salarial",
        "description": "Compara salário com mercado",
        "prompt_template": "Compare o salário da vaga {job_title} com o mercado: está competitivo? Sugestões de ajuste.",
        "agent": "JobIntakeAgent",
        "agent_type": AgentType.JOB_INTAKE,
        "required_context": ["job_id"],
        "intent": "salary_benchmark"
    }
}

QUERY_PATTERNS = {
    "funnel_analysis": [
        r"(analise|analisar|análise|mostrar?)\s*(o\s+)?funil",
        r"funil\s+de\s+(recrutamento|candidatos|conversão)",
        r"candidatos\s+por\s+etapa",
        r"taxa\s+de\s+conversão",
    ],
    "comparative_analysis": [
        r"compar(ar|e|ação)",
        r"diferença\s+entre\s+(as\s+)?vagas",
        r"qual\s+vaga\s+(está|tem)\s+(melhor|pior)",
    ],
    "bottleneck_detection": [
        r"gargalo(s)?",
        r"(candidatos?|pessoas?)\s+(parado|parada|travado|travada)(s|os|as)?",
        r"onde\s+(está|estão)\s+(o\s+)?problema",
        r"(etapa|fase)\s+com\s+(mais\s+)?demora",
    ],
    "time_to_fill_prediction": [
        r"preve(r|ja|são)",
        r"quando\s+(vai|será)\s+(fechar|preencher|concluir)",
        r"tempo\s+(para|de)\s+(fechar|preencher)",
        r"estimativa\s+de\s+(fechamento|preenchimento)",
    ],
    "candidate_quality_score": [
        r"qualidade\s+(dos?\s+)?candidatos?",
        r"(score|pontuação|nota)\s+(média|geral)",
        r"fit\s+(técnico|cultural)",
        r"avaliaç(ão|ões)\s+(dos?\s+)?candidatos?",
    ],
    "sourcing_effectiveness": [
        r"(fonte|canal|origem)\s+(de|dos?\s+)?candidatos?",
        r"efetividade\s+do\s+sourcing",
        r"de\s+onde\s+vêm\s+os\s+candidatos",
        r"melhor(es)?\s+(fonte|canal)",
    ],
    "weekly_summary": [
        r"resumo\s+(semanal|da\s+semana)",
        r"(como\s+foi|o\s+que\s+aconteceu)\s+(essa|a)\s+semana",
        r"relatório\s+(semanal|da\s+semana)",
    ],
    "salary_benchmark": [
        r"(salário|remuneração)\s+(está\s+)?(competitivo|adequado)",
        r"benchmark\s+salarial",
        r"comparar?\s+(com\s+o\s+)?mercado",
        r"faixa\s+salarial",
    ],
}


@dataclass
class AnalyticsResponse:
    """Structured response from analytics service."""
    command: str
    agent_used: str
    response: str
    data: dict[str, Any] = field(default_factory=dict)
    charts: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "agent_used": self.agent_used,
            "response": self.response,
            "data": self.data,
            "charts": self.charts,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error,
        }


class JobAnalyticsPromptService:
    """
    Service for routing natural language analytics queries to specialized agents.
    
    Features:
    - Command templates for common analytics tasks
    - Natural language query routing
    - Single job and multi-job analysis
    - Quick insights generation
    - Next action suggestions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.command_templates = COMMAND_TEMPLATES
        self.query_patterns = QUERY_PATTERNS
    
    def get_available_commands(self) -> list[dict[str, Any]]:
        """
        Returns list of available command templates.
        
        Returns:
            List of command metadata dictionaries
        """
        commands = []
        for cmd_id, template in self.command_templates.items():
            commands.append({
                "id": cmd_id,
                "name": template["name"],
                "description": template["description"],
                "required_context": template["required_context"],
                "agent": template["agent"],
            })
        return commands
    
    async def execute_command(
        self,
        command_id: str,
        context: dict[str, Any],
        db: AsyncSession | None = None
    ) -> AnalyticsResponse:
        """
        Executes a command template with the provided context.
        
        Args:
            command_id: ID of the command template to execute
            context: Context with required variables (job_id, job_ids, etc.)
            db: Optional database session
            
        Returns:
            AnalyticsResponse with results
        """
        start_time = time.time()
        
        if command_id not in self.command_templates:
            return AnalyticsResponse(
                command=command_id,
                agent_used="",
                response=f"Comando '{command_id}' não encontrado.",
                success=False,
                error=f"Unknown command: {command_id}",
                metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
            )
        
        template = self.command_templates[command_id]
        
        missing_context = []
        for required in template["required_context"]:
            if required not in context or not context[required]:
                missing_context.append(required)
        
        if missing_context:
            return AnalyticsResponse(
                command=command_id,
                agent_used=template["agent"],
                response=f"Contexto incompleto. Campos faltando: {', '.join(missing_context)}",
                success=False,
                error=f"Missing required context: {missing_context}",
                metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
            )
        
        try:
            job_data = await self._get_job_data(context, db)
            
            prompt = template["prompt_template"].format(**job_data)
            
            agent = None
            
            if agent is None:
                self.logger.warning(f"Agent {template['agent']} not found, using fallback")
                result = await self._execute_fallback(command_id, prompt, context, db)
            else:
                entities = {
                    **context,
                    "prompt": prompt,
                    "message": prompt,
                }
                
                agent_context = {
                    "command_id": command_id,
                    "original_context": context,
                    **job_data,
                }
                
                response = await agent.process(
                    intent=template["intent"],
                    entities=entities,
                    context=agent_context
                )
                
                result = {
                    "response": response.message,
                    "data": response.data,
                    "suggestions": response.suggested_prompts or [],
                    "success": response.success,
                }
            
            charts = await self._generate_charts_data(command_id, result.get("data", {}), context)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalyticsResponse(
                command=command_id,
                agent_used=template["agent"],
                response=result.get("response", "Análise concluída."),
                data=result.get("data", {}),
                charts=charts,
                suggestions=result.get("suggestions", []),
                success=result.get("success", True),
                metadata={
                    "execution_time_ms": execution_time_ms,
                    "job_count": len(context.get("job_ids", [context.get("job_id")])) if context.get("job_id") or context.get("job_ids") else 0,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error executing command {command_id}: {e}", exc_info=True)
            return AnalyticsResponse(
                command=command_id,
                agent_used=template["agent"],
                response=f"Erro ao executar análise: {str(e)}",
                success=False,
                error=str(e),
                metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
            )
    
    async def analyze_natural_query(
        self,
        query: str,
        context: dict[str, Any],
        db: AsyncSession | None = None
    ) -> AnalyticsResponse:
        """
        Routes a natural language query to the best matching command/agent.
        
        Args:
            query: Natural language query from user
            context: Context with job information
            db: Optional database session
            
        Returns:
            AnalyticsResponse with results
        """
        start_time = time.time()
        
        command_id = self._detect_command_from_query(query)
        
        if command_id:
            self.logger.info(f"Detected command '{command_id}' from query: {query[:50]}...")
            return await self.execute_command(command_id, context, db)
        
        self.logger.info(f"No specific command detected, using general analysis for: {query[:50]}...")
        
        try:
            agent = None
            
            if agent is None:
                return AnalyticsResponse(
                    command="natural_query",
                    agent_used="AnalistaFeedbackAgent",
                    response="Agente de análise não disponível no momento.",
                    success=False,
                    error="Agent not available",
                    metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
                )
            
            job_data = await self._get_job_data(context, db)
            
            entities = {
                **context,
                "query": query,
                "message": query,
                "user_query": query,
                **job_data,
            }
            
            response = await agent.process(
                intent="general_query",
                entities=entities,
                context={"original_query": query, **job_data}
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalyticsResponse(
                command="natural_query",
                agent_used="AnalistaFeedbackAgent",
                response=response.message,
                data=response.data,
                suggestions=response.suggested_prompts or [],
                success=response.success,
                metadata={"execution_time_ms": execution_time_ms}
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing natural query: {e}", exc_info=True)
            return AnalyticsResponse(
                command="natural_query",
                agent_used="AnalistaFeedbackAgent",
                response=f"Erro ao processar consulta: {str(e)}",
                success=False,
                error=str(e),
                metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
            )
    
    async def get_job_quick_insights(
        self,
        job_id: str,
        db: AsyncSession | None = None
    ) -> AnalyticsResponse:
        """
        Returns quick metrics for a single job.
        
        Args:
            job_id: Job vacancy ID
            db: Optional database session
            
        Returns:
            AnalyticsResponse with quick insights
        """
        start_time = time.time()
        
        try:
            should_close_session = False
            if db is None:
                db = AsyncSessionLocal()
                should_close_session = True
            
            try:
                # ADR-001-EXEMPT: cross-domain JobVacancy lookup without company scope.
                # Caller path validates context separately; promote to JobVacancyCrudRepository
                # method get_vacancy_by_id_only in a follow-up sprint.
                job_query = select(JobVacancy).where(JobVacancy.id == job_id)
                result = await db.execute(job_query)
                job = result.scalar_one_or_none()
                
                if not job:
                    return AnalyticsResponse(
                        command="quick_insights",
                        agent_used="JobAnalyticsPromptService",
                        response=f"Vaga com ID {job_id} não encontrada.",
                        success=False,
                        error="Job not found",
                        metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
                    )
                
                candidates_query = select(
                    func.count(VacancyCandidate.id).label("total"),
                    VacancyCandidate.stage.label("stage")
                ).where(
                    VacancyCandidate.vacancy_id == job_id
                ).group_by(VacancyCandidate.stage)
                
                candidates_result = await db.execute(candidates_query)
                stage_counts = {row.stage: row.total for row in candidates_result.fetchall()}
                
                total_candidates = sum(stage_counts.values())
                
                days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
                
                new_this_week = 0
                try:
                    from datetime import timedelta
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    new_query = select(func.count(VacancyCandidate.id)).where(
                        and_(
                            VacancyCandidate.vacancy_id == job_id,
                            VacancyCandidate.created_at >= week_ago
                        )
                    )
                    new_result = await db.execute(new_query)
                    new_this_week = new_result.scalar() or 0
                except Exception:
                    pass
                
                insights_data = {
                    "job_id": str(job_id),
                    "job_title": job.title,
                    "status": job.status,
                    "total_candidates": total_candidates,
                    "candidates_by_stage": stage_counts,
                    "days_open": days_open,
                    "new_candidates_this_week": new_this_week,
                    "priority": job.priority if hasattr(job, 'priority') else "normal",
                }
                
                funnel_stages = ["sourced", "screening", "interview", "offer", "hired"]
                total_in_funnel = sum(stage_counts.get(s, 0) for s in funnel_stages[:3])
                hired = stage_counts.get("hired", 0)
                
                if total_in_funnel > 0:
                    conversion_rate = (hired / total_candidates * 100) if total_candidates > 0 else 0
                    insights_data["overall_conversion_rate"] = round(conversion_rate, 1)
                
                charts = [
                    {
                        "type": "funnel",
                        "title": "Funil de Candidatos",
                        "data": [
                            {"stage": stage, "count": stage_counts.get(stage, 0)}
                            for stage in funnel_stages
                        ]
                    },
                    {
                        "type": "metric",
                        "title": "Métricas Rápidas",
                        "data": {
                            "total": total_candidates,
                            "days_open": days_open,
                            "new_this_week": new_this_week,
                        }
                    }
                ]
                
                suggestions = []
                if total_candidates == 0:
                    suggestions.append("Iniciar sourcing de candidatos para esta vaga")
                elif days_open > 30 and hired == 0:
                    suggestions.append("Considere revisar o perfil da vaga ou expandir canais de sourcing")
                if stage_counts.get("screening", 0) > 10:
                    suggestions.append("Há muitos candidatos aguardando triagem - priorize as avaliações")
                
                response_text = (
                    f"📊 **{job.title}**\n\n"
                    f"• Total de candidatos: {total_candidates}\n"
                    f"• Dias em aberto: {days_open}\n"
                    f"• Novos esta semana: {new_this_week}\n"
                    f"• Status: {job.status}"
                )
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                return AnalyticsResponse(
                    command="quick_insights",
                    agent_used="JobAnalyticsPromptService",
                    response=response_text,
                    data=insights_data,
                    charts=charts,
                    suggestions=suggestions,
                    success=True,
                    metadata={"execution_time_ms": execution_time_ms}
                )
                
            finally:
                if should_close_session:
                    await db.close()
                    
        except Exception as e:
            self.logger.error(f"Error getting quick insights for job {job_id}: {e}", exc_info=True)
            return AnalyticsResponse(
                command="quick_insights",
                agent_used="JobAnalyticsPromptService",
                response=f"Erro ao obter insights: {str(e)}",
                success=False,
                error=str(e),
                metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
            )
    
    async def get_multi_job_comparison(
        self,
        job_ids: list[str],
        db: AsyncSession | None = None
    ) -> AnalyticsResponse:
        """
        Compares multiple jobs.
        
        Args:
            job_ids: List of job vacancy IDs to compare
            db: Optional database session
            
        Returns:
            AnalyticsResponse with comparison data
        """
        if not job_ids or len(job_ids) < 2:
            return AnalyticsResponse(
                command="multi_job_comparison",
                agent_used="JobAnalyticsPromptService",
                response="São necessárias pelo menos 2 vagas para comparação.",
                success=False,
                error="Insufficient jobs for comparison"
            )
        
        return await self.execute_command(
            "comparative_analysis",
            {"job_ids": job_ids},
            db
        )
    
    async def suggest_next_actions(
        self,
        job_id: str,
        db: AsyncSession | None = None
    ) -> AnalyticsResponse:
        """
        Suggests next actions based on job analysis.
        
        Args:
            job_id: Job vacancy ID
            db: Optional database session
            
        Returns:
            AnalyticsResponse with suggested actions
        """
        start_time = time.time()
        
        try:
            insights = await self.get_job_quick_insights(job_id, db)
            
            if not insights.success:
                return insights
            
            data = insights.data
            suggestions = []
            priority_actions = []
            
            total_candidates = data.get("total_candidates", 0)
            stage_counts = data.get("candidates_by_stage", {})
            days_open = data.get("days_open", 0)
            
            if total_candidates == 0:
                priority_actions.append({
                    "action": "start_sourcing",
                    "title": "Iniciar Sourcing",
                    "description": "Esta vaga não tem candidatos. Inicie a busca ativa.",
                    "priority": "high",
                    "command": "sourcing_effectiveness"
                })
            
            screening_count = stage_counts.get("screening", 0) + stage_counts.get("applied", 0)
            if screening_count > 5:
                priority_actions.append({
                    "action": "process_screening",
                    "title": "Processar Triagem",
                    "description": f"{screening_count} candidatos aguardando triagem.",
                    "priority": "high",
                    "command": "candidate_quality_score"
                })
            
            interview_count = stage_counts.get("interview", 0)
            if interview_count > 0:
                priority_actions.append({
                    "action": "schedule_interviews",
                    "title": "Agendar Entrevistas",
                    "description": f"{interview_count} candidatos prontos para entrevista.",
                    "priority": "medium",
                    "command": None
                })
            
            if days_open > 45:
                priority_actions.append({
                    "action": "review_strategy",
                    "title": "Revisar Estratégia",
                    "description": f"Vaga aberta há {days_open} dias. Considere ajustes.",
                    "priority": "medium",
                    "command": "bottleneck_detection"
                })
            
            if days_open > 14 and total_candidates > 5:
                suggestions.append("Executar análise de funil para identificar gargalos")
            
            if total_candidates > 10:
                suggestions.append("Avaliar qualidade geral dos candidatos")
            
            suggestions.append("Verificar benchmark salarial da vaga")
            
            response_text = f"## Próximas Ações para {data.get('job_title', 'esta vaga')}\n\n"
            
            if priority_actions:
                response_text += "### Ações Prioritárias\n"
                for action in priority_actions:
                    emoji = "🔴" if action["priority"] == "high" else "🟡"
                    response_text += f"{emoji} **{action['title']}**: {action['description']}\n"
            
            if suggestions:
                response_text += "\n### Sugestões Adicionais\n"
                for suggestion in suggestions:
                    response_text += f"• {suggestion}\n"
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalyticsResponse(
                command="suggest_next_actions",
                agent_used="JobAnalyticsPromptService",
                response=response_text,
                data={
                    "job_id": job_id,
                    "job_title": data.get("job_title"),
                    "priority_actions": priority_actions,
                    "additional_suggestions": suggestions,
                    "insights": data,
                },
                charts=[],
                suggestions=suggestions,
                success=True,
                metadata={"execution_time_ms": execution_time_ms}
            )
            
        except Exception as e:
            self.logger.error(f"Error suggesting next actions: {e}", exc_info=True)
            return AnalyticsResponse(
                command="suggest_next_actions",
                agent_used="JobAnalyticsPromptService",
                response=f"Erro ao gerar sugestões: {str(e)}",
                success=False,
                error=str(e),
                metadata={"execution_time_ms": int((time.time() - start_time) * 1000)}
            )
    
    def _detect_command_from_query(self, query: str) -> str | None:
        """
        Detect the most appropriate command from a natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Command ID or None if no match
        """
        query_lower = query.lower()
        
        best_match = None
        best_score = 0
        
        for cmd_id, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score = len(pattern)
                    if score > best_score:
                        best_score = score
                        best_match = cmd_id
        
        return best_match
    
    async def _get_job_data(
        self,
        context: dict[str, Any],
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Fetch job data for template rendering.
        
        Args:
            context: Context with job_id or job_ids
            db: Optional database session
            
        Returns:
            Dict with job_title, job_titles, etc.
        """
        job_data = {
            "job_title": context.get("job_title", "Vaga"),
            "job_titles": context.get("job_titles", "Vagas selecionadas"),
        }
        
        if not db:
            return job_data
        
        try:
            if "job_id" in context and context["job_id"]:
                job_query = select(JobVacancy.title).where(JobVacancy.id == context["job_id"])
                result = await db.execute(job_query)
                job = result.scalar_one_or_none()
                if job:
                    job_data["job_title"] = job
            
            if "job_ids" in context and context["job_ids"]:
                jobs_query = select(JobVacancy.title).where(JobVacancy.id.in_(context["job_ids"]))
                result = await db.execute(jobs_query)
                titles = [row[0] for row in result.fetchall()]
                if titles:
                    job_data["job_titles"] = ", ".join(titles)
                    
        except Exception as e:
            self.logger.warning(f"Could not fetch job data: {e}")
        
        return job_data
    
    async def _execute_fallback(
        self,
        command_id: str,
        prompt: str,
        context: dict[str, Any],
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Execute fallback when agent is not available.
        
        Args:
            command_id: Command being executed
            prompt: Rendered prompt
            context: Execution context
            db: Optional database session
            
        Returns:
            Dict with fallback response
        """
        return {
            "response": f"Análise solicitada: {prompt}\n\nNo momento, o agente especializado não está disponível. Por favor, tente novamente mais tarde.",
            "data": {"command": command_id, "fallback": True},
            "suggestions": [],
            "success": False,
        }
    
    async def _generate_charts_data(
        self,
        command_id: str,
        data: dict[str, Any],
        context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate chart data for frontend visualization.
        
        Args:
            command_id: Command that was executed
            data: Response data from agent
            context: Execution context
            
        Returns:
            List of chart configurations
        """
        charts = []
        
        if command_id == "funnel_analysis":
            if "stages" in data:
                charts.append({
                    "type": "funnel",
                    "title": "Funil de Recrutamento",
                    "data": data["stages"]
                })
            if "conversion_rates" in data:
                charts.append({
                    "type": "bar",
                    "title": "Taxa de Conversão por Etapa",
                    "data": data["conversion_rates"]
                })
        
        elif command_id == "comparative_analysis":
            if "comparison" in data:
                charts.append({
                    "type": "grouped_bar",
                    "title": "Comparação entre Vagas",
                    "data": data["comparison"]
                })
        
        elif command_id == "sourcing_effectiveness":
            if "sources" in data:
                charts.append({
                    "type": "pie",
                    "title": "Candidatos por Fonte",
                    "data": data["sources"]
                })
        
        elif command_id == "time_to_fill_prediction":
            if "timeline" in data:
                charts.append({
                    "type": "line",
                    "title": "Projeção de Fechamento",
                    "data": data["timeline"]
                })
        
        return charts


job_analytics_prompt_service = JobAnalyticsPromptService()
