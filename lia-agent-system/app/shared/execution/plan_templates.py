import logging
from typing import Any

from app.shared.execution.action_planner import ActionPlanner, RetryPolicy
from app.shared.execution.execution_plan import AgentTask, ExecutionPlan

logger = logging.getLogger(__name__)


class PlanTemplateRegistry:
    """Registry of pre-defined plan templates for common workflows."""

    TEMPLATES = {
        "schedule_interviews_batch": {
            "name": "Agendar Entrevistas em Lote",
            "description": "Agenda entrevistas para múltiplos candidatos finalistas",
            "retry_policy": {"max_retries": 2, "backoff_type": "exponential", "base_delay": 2.0},
            "steps": [
                {"task_id": "find_candidates", "domain_id": "cv_screening", "action_id": "list_top_candidates", "is_critical": True},
                {"task_id": "check_availability", "domain_id": "interview_scheduling", "action_id": "check_availability", "depends_on": ["find_candidates"], "is_critical": True},
                {"task_id": "create_events", "domain_id": "interview_scheduling", "action_id": "schedule_interviews", "depends_on": ["check_availability"], "is_critical": False},
                {"task_id": "send_invites", "domain_id": "communication", "action_id": "send_interview_invites", "depends_on": ["create_events"], "is_critical": False},
                {"task_id": "update_stages", "domain_id": "job_management", "action_id": "advance_to_interview", "depends_on": ["create_events"], "is_critical": False},
            ]
        },
        "batch_rejection_feedback": {
            "name": "Feedback de Reprovação em Lote",
            "description": "Envia feedback personalizado para candidatos reprovados",
            "retry_policy": {"max_retries": 3, "backoff_type": "linear", "base_delay": 1.0},
            "steps": [
                {"task_id": "get_rejected", "domain_id": "job_management", "action_id": "list_rejected_no_feedback", "is_critical": True},
                {"task_id": "generate_messages", "domain_id": "communication", "action_id": "generate_rejection_messages", "depends_on": ["get_rejected"], "is_critical": True},
                {"task_id": "send_messages", "domain_id": "communication", "action_id": "send_batch_messages", "depends_on": ["generate_messages"], "is_critical": False},
                {"task_id": "log_feedback", "domain_id": "analytics", "action_id": "log_feedback_sent", "depends_on": ["send_messages"], "is_critical": False},
            ]
        },
        "advance_top_candidates": {
            "name": "Avançar Melhores Candidatos",
            "description": "Move candidatos com score alto para próxima etapa",
            "retry_policy": {"max_retries": 1, "backoff_type": "fixed", "base_delay": 1.0},
            "steps": [
                {"task_id": "identify_top", "domain_id": "cv_screening", "action_id": "get_high_score_candidates", "is_critical": True},
                {"task_id": "validate_transition", "domain_id": "job_management", "action_id": "validate_stage_transition", "depends_on": ["identify_top"], "is_critical": True},
                {"task_id": "move_candidates", "domain_id": "job_management", "action_id": "batch_advance_stage", "depends_on": ["validate_transition"], "is_critical": True},
                {"task_id": "notify_recruiters", "domain_id": "communication", "action_id": "notify_stage_change", "depends_on": ["move_candidates"], "is_critical": False},
            ]
        },
        "sourcing_expansion": {
            "name": "Expandir Sourcing",
            "description": "Amplia busca de candidatos quando funil está fraco",
            "retry_policy": {"max_retries": 2, "backoff_type": "exponential", "base_delay": 2.0},
            "steps": [
                {"task_id": "analyze_funnel", "domain_id": "analytics", "action_id": "analyze_vacancy_funnel", "is_critical": True},
                {"task_id": "search_candidates", "domain_id": "sourcing", "action_id": "search_talent_pool", "depends_on": ["analyze_funnel"], "is_critical": True},
                {"task_id": "import_candidates", "domain_id": "sourcing", "action_id": "import_to_pipeline", "depends_on": ["search_candidates"], "is_critical": False},
                {"task_id": "notify_results", "domain_id": "communication", "action_id": "notify_sourcing_results", "depends_on": ["import_candidates"], "is_critical": False},
            ]
        },
        "launch_job_sourcing": {
            "name": "Lancar Busca de Candidatos",
            "description": "Enriquece a vaga, lanca sourcing automatizado e notifica recruiter",
            "steps": [
                {"task_id": "enrich_jd", "domain_id": "job_management", "action_id": "enrich_job_description", "is_critical": True},
                {"task_id": "source_candidates", "domain_id": "sourcing", "action_id": "start_sourcing", "depends_on": ["enrich_jd"], "is_critical": True},
                {"task_id": "notify_recruiter", "domain_id": "communication", "action_id": "notify_sourcing_started", "depends_on": ["source_candidates"], "is_critical": False},
            ]
        },
        "close_stale_jobs": {
            "name": "Fechar Vagas Estagnadas",
            "description": "Identifica vagas sem movimentacao >30 dias, notifica responsavel e arquiva",
            "steps": [
                {"task_id": "find_stale", "domain_id": "job_management", "action_id": "list_stale_jobs", "is_critical": True},
                {"task_id": "notify_owners", "domain_id": "communication", "action_id": "notify_stale_job_owners", "depends_on": ["find_stale"], "is_critical": False},
                {"task_id": "archive_jobs", "domain_id": "job_management", "action_id": "archive_stale_jobs", "depends_on": ["notify_owners"], "is_critical": False},
            ]
        },
        "screening_campaign": {
            "name": "Campanha de Triagem",
            "description": "Envio em massa de WSI para candidatos em triagem inicial",
            "steps": [
                {"task_id": "list_candidates", "domain_id": "cv_screening", "action_id": "list_pending_screening", "is_critical": True},
                {"task_id": "send_wsi", "domain_id": "cv_screening", "action_id": "send_wsi_batch", "depends_on": ["list_candidates"], "is_critical": True},
                {"task_id": "update_status", "domain_id": "job_management", "action_id": "mark_screening_sent", "depends_on": ["send_wsi"], "is_critical": False},
            ]
        },
        # NOTE (Task #1222): the "onboarding_pipeline" template was removed.
        # Onboarding é um fluxo contínuo/multi-etapa que pertence a um agente do
        # Studio, não a um template one-shot do Plan & Execute. Handoff honesto
        # via app/shared/execution/agent_handoff.py.
        "full_hiring_launch": {
            "name": "Lancamento Completo de Vaga",
            "description": "Cria, enriquece, publica e inicia sourcing de uma nova vaga",
            "steps": [
                {"task_id": "enrich", "domain_id": "job_management", "action_id": "enrich_job_description", "is_critical": True},
                {"task_id": "publish", "domain_id": "job_management", "action_id": "publish_job", "depends_on": ["enrich"], "is_critical": True},
                {"task_id": "sourcing", "domain_id": "sourcing", "action_id": "start_sourcing", "depends_on": ["publish"], "is_critical": False},
                {"task_id": "notify", "domain_id": "communication", "action_id": "notify_job_published", "depends_on": ["publish"], "is_critical": False},
            ]
        },
        "weekly_report": {
            "name": "Relatorio Semanal de Recrutamento",
            "description": "Gera e envia relatorio consolidado da semana para gestores",
            "steps": [
                {"task_id": "collect_metrics", "domain_id": "analytics", "action_id": "collect_weekly_metrics", "is_critical": True},
                {"task_id": "generate_report", "domain_id": "analytics", "action_id": "generate_weekly_report", "depends_on": ["collect_metrics"], "is_critical": True},
                {"task_id": "send_report", "domain_id": "communication", "action_id": "send_weekly_report", "depends_on": ["generate_report"], "is_critical": False},
            ]
        },
        "candidate_nurturing": {
            "name": "Nutricao de Candidatos",
            "description": "Envia atualizacoes de status e conteudo de engajamento para pipeline ativo",
            "steps": [
                {"task_id": "list_pipeline", "domain_id": "cv_screening", "action_id": "list_active_pipeline", "is_critical": True},
                {"task_id": "send_updates", "domain_id": "communication", "action_id": "send_pipeline_updates", "depends_on": ["list_pipeline"], "is_critical": False},
                {"task_id": "log_touchpoints", "domain_id": "analytics", "action_id": "log_nurturing_touchpoints", "depends_on": ["send_updates"], "is_critical": False},
            ]
        },
        "interview_prep_pack": {
            "name": "Kit de Preparacao para Entrevista",
            "description": "Envia guia de preparacao, agenda, e briefing ao candidato antes da entrevista",
            "steps": [
                {"task_id": "get_interview", "domain_id": "interview_scheduling", "action_id": "get_upcoming_interview", "is_critical": True},
                {"task_id": "send_guide", "domain_id": "communication", "action_id": "send_interview_prep_guide", "depends_on": ["get_interview"], "is_critical": False},
                {"task_id": "send_briefing", "domain_id": "communication", "action_id": "send_company_briefing", "depends_on": ["get_interview"], "is_critical": False},
            ]
        },
        "talent_pool_build": {
            "name": "Construcao de Pool de Talentos",
            "description": "Importa candidatos reprovados para pool, classifica por competencia",
            "steps": [
                {"task_id": "collect_rejected", "domain_id": "cv_screening", "action_id": "list_recently_rejected", "is_critical": True},
                {"task_id": "classify", "domain_id": "analytics", "action_id": "classify_by_competency", "depends_on": ["collect_rejected"], "is_critical": False},
                {"task_id": "add_to_pool", "domain_id": "sourcing", "action_id": "add_to_talent_pool", "depends_on": ["classify"], "is_critical": True},
            ]
        },
        "end_of_month_closure": {
            "name": "Fechamento Mensal",
            "description": "Arquiva vagas preenchidas, gera relatorio mensal, atualiza metas",
            "steps": [
                {"task_id": "find_filled", "domain_id": "job_management", "action_id": "list_filled_jobs_month", "is_critical": True},
                {"task_id": "archive", "domain_id": "job_management", "action_id": "archive_filled_jobs", "depends_on": ["find_filled"], "is_critical": False},
                {"task_id": "generate_monthly_report", "domain_id": "analytics", "action_id": "generate_monthly_report", "depends_on": ["find_filled"], "is_critical": True},
                {"task_id": "send_to_managers", "domain_id": "communication", "action_id": "send_monthly_report", "depends_on": ["generate_monthly_report"], "is_critical": False},
            ]
        },
    }

    @classmethod
    def get_template_names(cls) -> list[str]:
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template(cls, template_name: str) -> dict[str, Any] | None:
        return cls.TEMPLATES.get(template_name)

    @classmethod
    def build_plan(
        cls,
        template_name: str,
        params: dict[str, Any] | None = None,
        plan_id: str | None = None,
    ) -> ExecutionPlan | None:
        template = cls.get_template(template_name)
        if not template:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"Template '{template_name}' not found")
            return None

        tasks = []
        for step in template["steps"]:
            task = AgentTask(
                task_id=step["task_id"],
                domain_id=step["domain_id"],
                action_id=step["action_id"],
                params=dict(params or {}),
                depends_on=step.get("depends_on", []),
                is_critical=step.get("is_critical", True),
                max_retries=template["retry_policy"].get("max_retries", 1),
            )
            tasks.append(task)

        plan = ExecutionPlan(tasks=tasks, plan_id=plan_id)
        plan.detected_pattern = template_name
        plan.original_query = template["description"]

        return plan

    @classmethod
    def build_planner(
        cls,
        template_name: str,
        params: dict[str, Any] | None = None,
        domain_registry=None,
        domain_workflow=None,
    ) -> ActionPlanner | None:
        template = cls.get_template(template_name)
        if not template:
            return None

        planner = ActionPlanner(
            domain_registry=domain_registry,
            domain_workflow=domain_workflow,
        )

        retry_config = template["retry_policy"]
        planner.set_retry_policy(RetryPolicy(
            max_retries=retry_config.get("max_retries", 2),
            backoff_type=retry_config.get("backoff_type", "exponential"),
            base_delay_seconds=retry_config.get("base_delay", 1.0),
        ))

        return planner
