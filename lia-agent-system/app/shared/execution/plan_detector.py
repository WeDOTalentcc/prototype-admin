import logging
import re
from dataclasses import dataclass
from typing import Any


from app.shared.execution.execution_plan import AgentTask, ExecutionPlan

logger = logging.getLogger(__name__)


# ── INVIOLABLE (Task #1211) ──────────────────────────────────────────────────
# Action ids that PERSIST a new job/vacancy. Plan & Execute must NEVER run any
# of these — job creation is exclusively the canonical wizard. The import-time
# guard _assert_no_creation_steps() raises if any PlanPattern references one.
JOB_CREATION_ACTION_IDS: frozenset[str] = frozenset(
    {
        "create_job",
        "create_jobs",
        "create_vacancy",
        "create_job_vacancy",
        "create_requisition",
        "new_job",
    }
)


class JobCreationInPlanError(RuntimeError):
    """Raised at import time if a PlanPattern would create a job (forbidden)."""


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
    # ── Sourcing + Comparison ──
    PlanPattern(
        name="buscar_e_comparar",
        patterns=[
            r"buscar?\s+.*\s+e\s+comparar?",
            r"encontrar?\s+.*\s+e\s+comparar?",
            r"pesquisar?\s+.*\s+e\s+comparar?",
        ],
        pipeline=[
            PipelineStep(domain_id="sourcing", action_id="search_candidates"),
            PipelineStep(domain_id="cv_screening", action_id="compare_candidates", context_from="task_0.candidate_ids"),
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
            PipelineStep(domain_id="sourcing", action_id="search_candidates"),
            PipelineStep(domain_id="cv_screening", action_id="rank_candidates", context_from="task_0.candidate_ids"),
        ],
        description="Buscar os melhores candidatos e ranquear",
    ),

    # ── JD + Screening ──
    PlanPattern(
        name="gerar_jd_e_avaliar",
        patterns=[
            r"ger(?:ar|e)\s+(?:a\s+)?(?:jd|descri[cç][aã]o)\b.*?\s+e\s+(avali|tria)",
            r"cri(?:ar|e)\s+(?:a\s+)?descri[cç][aã]o\b.*?\s+e\s+(avali|tria)",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="generate_jd"),
            PipelineStep(domain_id="cv_screening", action_id="score_cv", context_from="task_0.jd_data"),
        ],
        description="Gerar JD e avaliar candidatos contra ela",
    ),

    # ── Evaluate + Notify ──
    PlanPattern(
        name="avaliar_e_notificar",
        patterns=[
            r"avali(?:ar|a[cç][aã]o)\s+.*\s+e\s+(notific|avis|comunic)",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="score_cv"),
            PipelineStep(domain_id="communication", action_id="notify_stakeholders", context_from="task_0.evaluation_result"),
        ],
        description="Avaliar candidato e notificar sobre resultado",
    ),

    # ── Interview + Remind ──
    PlanPattern(
        name="agendar_e_lembrar",
        patterns=[
            r"agend(?:ar|e)\s+.*\s+e\s+(lembr|avisa|notific)",
            r"marc(?:ar|e)\s+entrevista\s+e\s+(lembr|avisa|envi)",
        ],
        pipeline=[
            PipelineStep(domain_id="interview_scheduling", action_id="scheduling_schedule_interview"),
            PipelineStep(domain_id="communication", action_id="communication_send_email", context_from="task_0.interview_data"),
        ],
        description="Agendar entrevista e enviar lembrete",
    ),

    # ── Move Stage + Notify ──
    PlanPattern(
        name="mover_e_notificar",
        patterns=[
            r"mov(?:er|a)\s+.*\s+e\s+(notific|avis|comunic)",
            r"avan[cç](?:ar|e)\s+.*\s+e\s+(notific|avis|comunic)",
        ],
        pipeline=[
            PipelineStep(domain_id="pipeline_transition", action_id="move_candidate"),
            PipelineStep(domain_id="communication", action_id="notify_stakeholders", context_from="task_0.movement_data"),
        ],
        description="Mover candidato no pipeline e notificar",
    ),

    # ── Search + Screen ──
    PlanPattern(
        name="buscar_e_triar",
        patterns=[
            r"buscar?\s+.*\s+e\s+tri(?:ar|agem)",
            r"encontrar?\s+.*\s+e\s+tri(?:ar|agem)",
        ],
        pipeline=[
            PipelineStep(domain_id="sourcing", action_id="search_candidates"),
            PipelineStep(domain_id="cv_screening", action_id="batch_screen", context_from="task_0.candidate_ids"),
        ],
        description="Buscar candidatos e iniciar triagem",
    ),

    # ── Score + Rank ──
    PlanPattern(
        name="pontuar_e_rankear",
        patterns=[
            r"pontua(?:r|e)\s+.*\s+e\s+rank",
            r"avalia(?:r|e)\s+.*\s+e\s+classific",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="score_cv"),
            PipelineStep(domain_id="cv_screening", action_id="rank_candidates", context_from="task_0.scores"),
        ],
        description="Pontuar CVs e ranquear candidatos",
    ),

    # ── Parse CV + Screen ──
    PlanPattern(
        name="importar_cv_e_triar",
        patterns=[
            r"import(?:ar|e)\s+(?:o\s+)?cv\s+.*e\s+tri",
            r"cadastr(?:ar|e)\s+candidato\s+e\s+tri",
        ],
        pipeline=[
            PipelineStep(domain_id="cv_screening", action_id="parse_cv"),
            PipelineStep(domain_id="cv_screening", action_id="generate_wsi_questions", context_from="task_0.candidate_id"),
        ],
        description="Importar CV e iniciar triagem WSI",
    ),

    # ── Enrich JD + Start Sourcing ──
    PlanPattern(
        name="enriquecer_e_buscar",
        patterns=[
            r"enrique[cç](?:er|a)\s+.*\s+e\s+(busc|sourc|procur)",
        ],
        pipeline=[
            PipelineStep(domain_id="job_management", action_id="enrich_job_description"),
            PipelineStep(domain_id="sourcing", action_id="auto_source", context_from="task_0.job_id"),
        ],
        description="Enriquecer descrição da vaga e iniciar sourcing",
    ),

    # ── Analytics + Report ──
    PlanPattern(
        name="analisar_e_reportar",
        patterns=[
            r"analis(?:ar|e)\s+.*\s+e\s+(report|relat[oó]rio|envi)",
            r"gerar?\s+(?:relat[oó]rio|an[aá]lise)\s+.*\s+e\s+envi",
        ],
        pipeline=[
            PipelineStep(domain_id="analytics", action_id="analytics_analyze_funnel"),
            PipelineStep(domain_id="communication", action_id="send_kpi_report", context_from="task_0.analysis_data"),
        ],
        description="Analisar funil e enviar relatório",
    ),

    # ── Briefing diário ──
    PlanPattern(
        name="briefing_e_planejar",
        patterns=[
            r"briefing\s+.*\s+e\s+plan",
            r"resumo\s+do\s+dia\s+e\s+plan",
        ],
        pipeline=[
            PipelineStep(domain_id="recruiter_assistant", action_id="daily_briefing"),
            PipelineStep(domain_id="recruiter_assistant", action_id="plan_day", context_from="task_0.briefing_data"),
        ],
        description="Gerar briefing e planejar o dia",
    ),

    # NOTE (Task #1222): triagem is a CONTINUOUS agent, not a one-shot action.
    # NOTE (Task #1211 — INVIOLABLE): NO pattern creates a job. Job creation
    # is ALWAYS the canonical wizard. See wizard bootstrap in MainOrchestrator.

]


def _assert_no_creation_steps(patterns: list[PlanPattern]) -> None:
    """Fail loud (Task #1211) if any PlanPattern would create a job.

    Plan & Execute is forbidden from persisting a vacancy — that is exclusively
    the canonical wizard. Runs at import time so a forbidden step can never ship.
    """
    offenders: list[str] = []
    for pattern in patterns:
        for step in pattern.pipeline:
            if step.action_id in JOB_CREATION_ACTION_IDS:
                offenders.append(f"{pattern.name} -> {step.domain_id}.{step.action_id}")
    if offenders:
        raise JobCreationInPlanError(
            "Plan & Execute must NEVER create a job (Task #1211 inviolable rule). "
            "Job creation is exclusively the canonical wizard. Forbidden steps: "
            + "; ".join(offenders)
        )


_assert_no_creation_steps(PLAN_PATTERNS)


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
