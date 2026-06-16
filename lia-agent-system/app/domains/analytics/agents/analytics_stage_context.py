"""Analytics ReAct Agent — Stage Context.

Defines execution stages for the analytics workflow and their associated tools.
Each stage maps to a specific phase of an analytics inquiry:
  query-understanding → data-retrieval → synthesis
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, Any] = {
    "query-understanding": {
        "name": "query-understanding",
        "description": "Entender qual métrica, KPI ou relatório o recrutador está solicitando",
        "tools": [
            "get_job_insights",
            "get_search_analytics",
            "get_agent_performance",
        ],
        "required_fields": ["company_id"],
        "transition_criteria": "Quando o tipo de análise estiver claro e os parâmetros básicos coletados",
        "next_stages": ["data-retrieval"],
    },
    "data-retrieval": {
        "name": "data-retrieval",
        "description": "Buscar e calcular os dados necessários para responder à solicitação",
        "tools": [
            "get_job_insights",
            "predict_hiring_metrics",
            "generate_job_report",
            "generate_candidate_report",
        ],
        "required_fields": ["company_id"],
        "transition_criteria": "Quando os dados foram coletados e estão prontos para interpretação",
        "next_stages": ["synthesis"],
    },
    "synthesis": {
        "name": "synthesis",
        "description": "Sintetizar os dados coletados em insights acionáveis e recomendações claras",
        "tools": [
            "get_job_insights",
            "predict_hiring_metrics",
            "generate_job_report",
            "generate_candidate_report",
            "get_search_analytics",
            "get_agent_performance",
            "interpret_fairness_report",
            "generate_lgpd_audit_summary",
        ],
        "required_fields": [],
        "transition_criteria": "Estágio final — resposta entregue ao recrutador",
        "next_stages": [],
    },
}


def get_stage_context(stage: str) -> dict[str, Any]:
    """Return the stage definition dict for the given stage name."""
    return STAGE_DEFINITIONS.get(stage, STAGE_DEFINITIONS["query-understanding"])


def get_stage_tools(stage: str) -> list[str]:
    """Return the list of tool names available for the given stage."""
    return get_stage_context(stage).get("tools", [])


def get_transition_prompt(from_stage: str, to_stage: str) -> str:
    """Return a human-readable message for stage transitions."""
    prompts: dict[tuple, str] = {
        ("query-understanding", "data-retrieval"): (
            "Consulta compreendida. Buscando dados analíticos no banco..."
        ),
        ("data-retrieval", "synthesis"): (
            "Dados coletados com sucesso. Sintetizando insights e recomendações..."
        ),
        ("query-understanding", "synthesis"): (
            "Consulta simples identificada. Gerando resposta direta com os dados disponíveis..."
        ),
    }
    return prompts.get(
        (from_stage, to_stage),
        f"Avançando de '{from_stage}' para '{to_stage}'.",
    )
