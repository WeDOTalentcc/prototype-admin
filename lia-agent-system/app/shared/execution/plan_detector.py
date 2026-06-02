import logging
import re
from dataclasses import dataclass
from typing import Any


from app.shared.execution.execution_plan import AgentTask, ExecutionPlan

logger = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    domain_id: str
    action_id: str
    context_from: str | None = None


@dataclass
class PlanPattern:
    name: str
    patterns: list[str]
    pipeline: list[PipelineStep]
    description: str = ""


PLAN_PATTERNS: list[PlanPattern] = [
    PlanPattern(
        name="buscar_e_comparar",
        patterns=[
            r"buscar?\s+.*\s+e\s+comparar?",
            r"encontrar?\s+.*\s+e\s+comparar?",
            r"pesquisar?\s+.*\s+e\s+comparar?",
        ],
        pipeline=[
            PipelineStep(domain_id="sourcing", action_id="search_candidates"),
            PipelineStep(domain_id="sourcing", action_id="compare_candidates", context_from="task_0.candidate_ids"),
        ],
        description="Buscar candidatos e comparar os resultados",
    ),
    PlanPattern(
        name="buscar_top_e_detalhar",
        patterns=[
            r"(top|melhor|melhores)\s+\d+\s+.*\s+e\s+detalh",
            r"buscar?\s+(top|melhor)\s+.*\s+e\s+(mostr|detalh|ver)",
        ],
        pipeline=[
            PipelineStep(domain_id="sourcing", action_id="search_top"),
            PipelineStep(domain_id="sourcing", action_id="show_candidate_details", context_from="task_0.top_candidate_id"),
        ],
        description="Buscar os melhores candidatos e detalhar o principal",
    ),
    PlanPattern(
        name="gerar_jd_e_avaliar",
        patterns=[
            r"gerar?\s+(?:a\s+)?(?:jd|descri[cç][aã]o)\s+e\s+(avali|tria)",
            r"cri(?:ar|e)\s+(?:a\s+)?descri[cç][aã]o\s+e\s+(avali|tria)",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="generate_jd"),
            PipelineStep(domain_id="cv_screening", action_id="evaluate_against_jd", context_from="task_0.jd_data"),
        ],
        description="Gerar JD e avaliar candidatos contra ela",
    ),
    PlanPattern(
        name="triagem_e_agendar",
        patterns=[
            r"tri(?:ar|agem)\s+.*\s+e\s+agendar?",
            r"avali(?:ar|a[cç][aã]o)\s+.*\s+e\s+agendar?\s+entrevista",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="screen_candidates"),
            PipelineStep(domain_id="interview_scheduling", action_id="schedule_interview", context_from="task_0.approved_ids"),
        ],
        description="Triar candidatos e agendar entrevistas para aprovados",
    ),
    PlanPattern(
        name="avaliar_e_notificar",
        patterns=[
            r"avali(?:ar|a[cç][aã]o)\s+.*\s+e\s+(notific|avis|comunic)",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="evaluate_candidate"),
            PipelineStep(domain_id="communication", action_id="send_notification", context_from="task_0.evaluation_result"),
        ],
        description="Avaliar candidato e notificar sobre resultado",
    ),
    PlanPattern(
        name="filtrar_e_reportar",
        patterns=[
            r"filtr(?:ar|o)\s+.*\s+e\s+(gerar?\s+relat[oó]rio|report)",
            r"buscar?\s+.*\s+e\s+gerar?\s+relat[oó]rio",
        ],
        pipeline=[
            PipelineStep(domain_id="sourcing", action_id="filter_candidates"),
            PipelineStep(domain_id="analytics", action_id="generate_report", context_from="task_0.filtered_data"),
        ],
        description="Filtrar candidatos e gerar relatório",
    ),
    PlanPattern(
        name="criar_vaga_e_publicar",
        patterns=[
            r"cri(?:ar|e)\s+(?:a\s+)?vaga\s+e\s+(public|sinc)",
            r"nova\s+vaga\s+.*\s+e\s+(public|sinc)",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="create_job"),
            PipelineStep(domain_id="ats_integration", action_id="sync_job", context_from="task_0.job_id"),
        ],
        description="Criar vaga e publicar/sincronizar com ATS",
    ),
    PlanPattern(
        name="analisar_e_planejar",
        patterns=[
            r"analis(?:ar|e)\s+.*\s+e\s+(planejar?|sugerir?|recomendar?)",
            r"diagn[oó]stico\s+.*\s+e\s+(plano|sugest)",
        ],
        pipeline=[
            PipelineStep(domain_id="analytics", action_id="analyze_funnel"),
            PipelineStep(domain_id="recruiter_assistant", action_id="create_plan", context_from="task_0.analysis_data"),
        ],
        description="Analisar funil e criar plano de ação",
    ),
    PlanPattern(
        name="agendar_e_lembrar",
        patterns=[
            r"agendar?\s+.*\s+e\s+(lembr|enviar?\s+lembrete|reminder)",
        ],
        pipeline=[
            PipelineStep(domain_id="interview_scheduling", action_id="schedule_interview"),
            PipelineStep(domain_id="communication", action_id="send_reminder", context_from="task_0.interview_data"),
        ],
        description="Agendar entrevista e enviar lembrete",
    ),
    PlanPattern(
        name="mover_e_notificar",
        patterns=[
            r"mov(?:er|a)\s+.*\s+e\s+(notific|avis|comunic|email)",
            r"atualizar?\s+(?:o\s+)?(?:status|est[aá]gio|stage)\s+.*\s+e\s+(notific|avis)",
        ],
        pipeline=[
            PipelineStep(domain_id="automation", action_id="move_candidate_stage"),
            PipelineStep(domain_id="communication", action_id="send_notification", context_from="task_0.movement_data"),
        ],
        description="Mover candidato de etapa e notificar",
    ),
    PlanPattern(
        name="buscar_e_triar",
        patterns=[
            r"buscar?\s+.*\s+e\s+tri(?:ar|agem)",
            r"encontrar?\s+.*\s+e\s+avali(?:ar|a[cç][aã]o)",
        ],
        pipeline=[
            PipelineStep(domain_id="sourcing", action_id="search_candidates"),
            PipelineStep(domain_id="cv_screening", action_id="screen_candidates", context_from="task_0.candidate_ids"),
        ],
        description="Buscar candidatos e triar automaticamente",
    ),
    PlanPattern(
        name="relatorio_e_exportar",
        patterns=[
            r"gerar?\s+relat[oó]rio\s+e\s+export",
            r"relat[oó]rio\s+.*\s+e\s+export",
        ],
        pipeline=[
            PipelineStep(domain_id="analytics", action_id="generate_report"),
            PipelineStep(domain_id="analytics", action_id="export_report", context_from="task_0.report_data"),
        ],
        description="Gerar relatório e exportar",
    ),
    PlanPattern(
        name="adicionar_analisar_wsi",
        patterns=[
            r"adiciona[rn]?\s+.*\s+(na|[àa])\s+vaga\s+e\s+(dispara[r]?|inicia[r]?|fa[cz][er]?)\s+(triagem|wsi|screening)",
            r"cadastra[rn]?\s+.*\s+(na|[àa])\s+vaga\s+e\s+(dispara[r]?|triagem|wsi)",
            r"(adiciona[r]?|cadastra[r]?)\s+candidato\s+.*\s+e\s+(triagem|wsi|screening)",
            r"coloca[r]?\s+.*\s+na\s+vaga\s+e\s+(tria[r]?|screen|wsi)",
            r"insere?\s+.*\s+na\s+vaga\s+e\s+(dispara[r]?|tria[r]?|faz[er]?\s+triagem)",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="add_candidate_to_vacancy"),
            PipelineStep(domain_id="cv_screening", action_id="run_wsi_screening", context_from="task_0.candidate_id"),
        ],
        description="Adicionar candidato à vaga e disparar triagem WSI",
    ),
    PlanPattern(
        name="upload_cadastrar_triar",
        patterns=[
            r"analise?\s+(?:este|esse|o)\s+cv\s+(?:para|na|e\s+cadastr)",
            r"cadastr[ae]\s+(?:este|esse|o)?\s*candidato\s+.*\s+e\s+tria[r]?",
            r"faz[er]?\s+(?:o\s+)?upload\s+.*\s+e\s+(cadastr|registr|tria)",
            r"cri[ae]\s+(?:o\s+)?candidato\s+.*\s+e\s+(tria[r]?|screen|wsi)",
            r"registra[r]?\s+(?:o\s+)?candidato\s+.*\s+e\s+(dispara[r]?|tria[r]?|screen|wsi)",
            r"parse[ia]?\s+(?:o\s+)?cv\s+.*\s+e\s+(cadastr|tria|adiciona)",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="parse_and_create_candidate"),
            PipelineStep(domain_id="cv_screening", action_id="add_to_vacancy", context_from="task_0.candidate_id"),
            PipelineStep(domain_id="cv_screening", action_id="run_wsi_screening", context_from="task_1.vacancy_candidate_id"),
        ],
        description="Parsear CV, cadastrar candidato e disparar triagem WSI",
    ),
    PlanPattern(
        name="launch_job_sourcing",
        patterns=[
            r"lan[cç]ar?\s+(busca|sourcing|search)",
            r"iniciar?\s+(sourcing|busca)\s+(para|da|de)\s+vaga",
            r"ativar?\s+sourcing",
            r"come[cç]ar?\s+(a\s+)?buscar?\s+candidatos?\s+(para|da)\s+vaga",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="enrich_job_description"),
            PipelineStep(domain_id="sourcing", action_id="start_sourcing", context_from="task_0.job_id"),
            PipelineStep(domain_id="communication", action_id="notify_sourcing_started", context_from="task_1.job_id"),
        ],
        description="Lançar busca de candidatos para uma vaga",
    ),
    PlanPattern(
        name="close_stale_jobs",
        patterns=[
            r"fechar?\s+vagas?\s+(paradas?|estagnadas?|antigas?)",
            r"arquivar?\s+vagas?\s+sem\s+movimenta[cç][aã]o",
            r"limpar?\s+vagas?\s+abertas?\s+h[aá]\s+muito",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="list_stale_jobs"),
            PipelineStep(domain_id="communication", action_id="notify_stale_job_owners", context_from="task_0.job_ids"),
            PipelineStep(domain_id="job_management", action_id="archive_stale_jobs", context_from="task_0.job_ids"),
        ],
        description="Fechar vagas estagnadas",
    ),
    PlanPattern(
        name="screening_campaign",
        patterns=[
            r"enviar?\s+(wsi|triagem)\s+(em\s+lote|para\s+todos|em\s+massa)",
            r"disparar?\s+campanha\s+de\s+triagem",
            r"triagem\s+em\s+lote",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="list_pending_screening"),
            PipelineStep(domain_id="cv_screening", action_id="send_wsi_batch", context_from="task_0.candidate_ids"),
        ],
        description="Campanha de triagem em lote",
    ),
    PlanPattern(
        name="onboarding_pipeline",
        patterns=[
            r"onboarding\s+(pipeline|flow|completo)",
            r"preparar?\s+onboarding",
            r"iniciar?\s+processo\s+de\s+admiss[aã]o",
            r"day.?1\s+e\s+documentos",
        ],
        pipeline=[
            PipelineStep(domain_id="communication", action_id="request_onboarding_documents"),
            PipelineStep(domain_id="interview_scheduling", action_id="schedule_day_one", context_from="task_0.candidate_id"),
            PipelineStep(domain_id="communication", action_id="notify_team_new_hire", context_from="task_0.candidate_id"),
        ],
        description="Pipeline completo de onboarding",
    ),
    PlanPattern(
        name="full_hiring_launch",
        patterns=[
            r"lan[cç]amento\s+completo\s+(de\s+)?vaga",
            r"criar?\s+publicar?\s+e\s+(lan[cç]ar?|iniciar?)\s+sourcing",
            r"setup\s+completo\s+(de\s+)?vaga",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="enrich_job_description"),
            PipelineStep(domain_id="job_management", action_id="publish_job", context_from="task_0.job_id"),
            PipelineStep(domain_id="sourcing", action_id="start_sourcing", context_from="task_1.job_id"),
        ],
        description="Lançamento completo de vaga",
    ),
    PlanPattern(
        name="weekly_report",
        patterns=[
            r"relat[oó]rio\s+semanal",
            r"gerar?\s+relat[oó]rio\s+da\s+semana",
            r"enviar?\s+resumo\s+semanal",
            r"weekly\s+report",
        ],
        pipeline=[
            PipelineStep(domain_id="analytics", action_id="collect_weekly_metrics"),
            PipelineStep(domain_id="analytics", action_id="generate_weekly_report", context_from="task_0.metrics"),
            PipelineStep(domain_id="communication", action_id="send_weekly_report", context_from="task_1.report"),
        ],
        description="Relatório semanal de recrutamento",
    ),
    PlanPattern(
        name="candidate_nurturing",
        patterns=[
            r"nutri[cç][aã]o\s+de\s+candidatos",
            r"engajar?\s+candidatos?\s+(no\s+)?pipeline",
            r"enviar?\s+atualiza[cç][oõ]es?\s+para\s+candidatos",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="list_active_pipeline"),
            PipelineStep(domain_id="communication", action_id="send_pipeline_updates", context_from="task_0.candidate_ids"),
        ],
        description="Nutrição de candidatos no pipeline",
    ),
    PlanPattern(
        name="interview_prep_pack",
        patterns=[
            r"kit\s+de\s+prepara[cç][aã]o",
            r"enviar?\s+prepara[cç][aã]o\s+para\s+entrevista",
            r"briefing\s+e\s+guia\s+de\s+entrevista",
        ],
        pipeline=[
            PipelineStep(domain_id="interview_scheduling", action_id="get_upcoming_interview"),
            PipelineStep(domain_id="communication", action_id="send_interview_prep_guide", context_from="task_0.interview_id"),
            PipelineStep(domain_id="communication", action_id="send_company_briefing", context_from="task_0.candidate_id"),
        ],
        description="Kit de preparação para entrevista",
    ),
    PlanPattern(
        name="talent_pool_build",
        patterns=[
            r"construir?\s+pool\s+de\s+talentos",
            r"adicionar?\s+reprovados?\s+(ao\s+)?pool",
            r"talent\s+pool",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="list_recently_rejected"),
            PipelineStep(domain_id="analytics", action_id="classify_by_competency", context_from="task_0.candidate_ids"),
            PipelineStep(domain_id="sourcing", action_id="add_to_talent_pool", context_from="task_1.classified"),
        ],
        description="Construção de pool de talentos",
    ),
    PlanPattern(
        name="end_of_month_closure",
        patterns=[
            r"fechamento\s+mensal",
            r"fechar?\s+o\s+m[eê]s",
            r"relat[oó]rio\s+mensal",
            r"encerrar?\s+ciclo\s+mensal",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="list_filled_jobs_month"),
            PipelineStep(domain_id="job_management", action_id="archive_filled_jobs", context_from="task_0.job_ids"),
            PipelineStep(domain_id="analytics", action_id="generate_monthly_report", context_from="task_0.metrics"),
            PipelineStep(domain_id="communication", action_id="send_monthly_report", context_from="task_2.report"),
        ],
        description="Fechamento mensal de recrutamento",
    ),
]


class PlanDetector:
    def __init__(self, custom_patterns: list[PlanPattern] | None = None):
        self._patterns = custom_patterns or PLAN_PATTERNS
        self._detection_count = 0
        self._match_count = 0

    def detect(self, query: str) -> ExecutionPlan | None:
        self._detection_count += 1
        normalized = query.lower().strip()

        for pattern in self._patterns:
            for regex in pattern.patterns:
                try:
                    if re.search(regex, normalized, re.IGNORECASE):
                        plan = self._build_plan(pattern, query)
                        self._match_count += 1
                        logger.info(
                            f"PlanDetector matched pattern '{pattern.name}' "
                            f"with {len(plan.tasks)} tasks"
                        )
                        return plan
                except re.error as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"Regex error in pattern '{pattern.name}': {e}")

        return None

    def _build_plan(self, pattern: PlanPattern, original_query: str) -> ExecutionPlan:
        plan = ExecutionPlan()
        plan.original_query = original_query
        plan.detected_pattern = pattern.name

        for i, step in enumerate(pattern.pipeline):
            task_id = f"task_{i}"
            depends_on = [f"task_{i-1}"] if i > 0 else []

            context_mappings: dict[str, str] = {}
            if step.context_from:
                parts = step.context_from.split(".", 1)
                if len(parts) == 2:
                    context_mappings[parts[1]] = step.context_from

            task = AgentTask(
                task_id=task_id,
                domain_id=step.domain_id,
                action_id=step.action_id,
                params={},
                depends_on=depends_on,
                context_mappings=context_mappings,
            )
            plan.add_task(task)

        return plan

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_detections": self._detection_count,
            "total_matches": self._match_count,
            "match_rate": self._match_count / max(self._detection_count, 1),
            "pattern_count": len(self._patterns),
        }

    def list_patterns(self) -> list[dict[str, str]]:
        return [{"name": p.name, "description": p.description} for p in self._patterns]
