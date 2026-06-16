"""Tool registry for analytics query tools."""
import logging

from app.tools.registry import ToolDefinition, tool_registry

from .activity_metrics import get_activity_summary, get_pending_actions
from .financial_trends import get_cost_metrics, get_trends
from .intelligence import get_conversion_patterns, get_ml_predictions, get_smart_alerts
from .pipeline_analytics import compare_candidates, get_pipeline_stats, get_vacancy_funnel
from .quality_metrics import get_hiring_quality, get_prediction_metrics, get_stakeholder_metrics
from .recruiter_performance import (
    get_comparative_metrics,
    get_efficiency_metrics,
    get_recruiter_metrics,
    get_velocity_metrics,
)
from .workload_analysis import get_bottleneck_analysis, get_workload_distribution

logger = logging.getLogger(__name__)


def register_analytics_query_tools() -> None:
    """Register analytics-domain query tools in the tool registry."""

    tool_registry.register(ToolDefinition(
        name="get_pipeline_stats",
        description="Obter estatísticas gerais do pipeline de recrutamento: número de vagas, candidatos, taxas de conversão por período.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "recruiter_id": {"type": "string", "description": "Filtrar por recrutador"},
                "department": {"type": "string", "description": "Filtrar por departamento"}
            }
        },
        handler=get_pipeline_stats,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_vacancy_funnel",
        description="Obter métricas de funil de uma vaga específica: candidatos por etapa, taxas de conversão, candidatos parados.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga"},
                "include_stalled": {"type": "boolean", "default": True, "description": "Incluir candidatos parados"},
                "stalled_days": {"type": "integer", "default": 7, "description": "Dias para considerar como parado"}
            },
            "required": ["job_id"]
        },
        handler=get_vacancy_funnel,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="compare_candidates",
        description="Comparar múltiplos candidatos lado a lado com métricas de score, experiência, skills e disponibilidade.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de UUIDs dos candidatos (máximo 5)"},
                "job_id": {"type": "string", "description": "UUID da vaga para contexto de comparação"}
            },
            "required": ["candidate_ids"]
        },
        handler=compare_candidates,
        allowed_agents=["recruiter_assistant", "wsi_evaluator", "sourcing", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_activity_summary",
        description="Obter resumo de atividades: candidatos em entrevistas, mudanças de etapa, candidatos adicionados no período.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar atividades"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador para filtrar"},
                "period": {"type": "string", "enum": ["today", "week", "month"], "default": "week", "description": "Período de análise"},
                "activity_type": {"type": "string", "enum": ["interviews", "stage_changes", "all"], "default": "all", "description": "Tipo de atividade"}
            }
        },
        handler=get_activity_summary,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_pending_actions",
        description="Obter ações pendentes: feedbacks atrasados, candidatos aguardando avaliação, ofertas pendentes de resposta, candidatos parados em etapa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador para filtrar"},
                "include_overdue": {"type": "boolean", "default": True, "description": "Incluir itens atrasados"},
                "overdue_days": {"type": "integer", "default": 3, "description": "Dias para considerar como atrasado"}
            }
        },
        handler=get_pending_actions,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_recruiter_metrics",
        description="Obter métricas de performance do recrutador: vagas fechadas, time-to-fill, taxa de conversão, eficiência.",
        parameters_schema={
            "type": "object",
            "properties": {
                "recruiter_id": {"type": "string", "description": "ID do recrutador (usa contexto se não informado)"},
                "period": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "compare_with_team": {"type": "boolean", "default": False, "description": "Comparar com métricas da equipe"}
            }
        },
        handler=get_recruiter_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_velocity_metrics",
        description="Obter métricas de velocidade de contratação: tempo médio para fechar vaga, taxa de compliance com SLA, vagas dentro/fora do SLA.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador para filtrar"},
                "sla_days": {"type": "integer", "default": 30, "description": "Dias de SLA para considerar"}
            }
        },
        handler=get_velocity_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_efficiency_metrics",
        description="Obter métricas de eficiência do recrutamento: candidatos por contratação, entrevistas por contratação, taxa de conversão triagem para oferta.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter"], "default": "month", "description": "Período de análise"},
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar"}
            }
        },
        handler=get_efficiency_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_comparative_metrics",
        description="Obter métricas comparativas: comparar performance do recrutador com a equipe ou com período anterior.",
        parameters_schema={
            "type": "object",
            "properties": {
                "recruiter_id": {"type": "string", "description": "ID do recrutador (usa contexto se não informado)"},
                "comparison_type": {"type": "string", "enum": ["team", "previous_period"], "default": "team", "description": "Tipo de comparação"},
                "period": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=get_comparative_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_workload_distribution",
        description="Obter distribuição de carga de trabalho da equipe: vagas ativas por recrutador, recrutadores sobrecarregados e subcarregados.",
        parameters_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "ID do time/departamento para filtrar"},
                "include_details": {"type": "boolean", "default": False, "description": "Incluir lista detalhada de vagas por recrutador"}
            }
        },
        handler=get_workload_distribution,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_bottleneck_analysis",
        description="Analisar gargalos no pipeline de uma vaga: etapa com maior rejeição, tempo médio por etapa, etapa mais lenta, recomendações.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (obrigatório)"},
                "period": {"type": "string", "enum": ["week", "month"], "default": "month", "description": "Período de análise"}
            },
            "required": ["job_id"]
        },
        handler=get_bottleneck_analysis,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_stakeholder_metrics",
        description="Obter métricas de responsividade de stakeholders: aprovações pendentes, tempo médio de resposta de gestores, decisões atrasadas, gargalos de stakeholders.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar (opcional)"},
                "period": {"type": "string", "enum": ["week", "month"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=get_stakeholder_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_hiring_quality",
        description="Obter métricas de qualidade pós-contratação: retenção em 90 dias, satisfação do gestor, avaliação de performance.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["quarter", "year"], "default": "quarter", "description": "Período de análise"},
                "department_id": {"type": "string", "description": "ID do departamento para filtrar (opcional)"}
            }
        },
        handler=get_hiring_quality,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_prediction_metrics",
        description="Obter predições de sucesso de uma vaga: probabilidade de fechamento, data estimada, fatores de risco, score de confiança.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (obrigatório)"}
            },
            "required": ["job_id"]
        },
        handler=get_prediction_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_cost_metrics",
        description="Obter métricas de custo de recrutamento: custo médio por contratação, investimento em sourcing, ROI estimado, custo por fonte.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para análise específica (opcional)"},
                "period": {"type": "string", "enum": ["month", "quarter"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=get_cost_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_trends",
        description="Analisar tendências históricas de métricas de recrutamento: volume mensal de candidatos/vagas/contratações, direção da tendência, crescimento percentual, sazonalidade.",
        parameters_schema={
            "type": "object",
            "properties": {
                "metric_type": {"type": "string", "enum": ["candidates", "jobs", "hires"], "default": "candidates", "description": "Tipo de métrica a analisar"},
                "period": {"type": "string", "enum": ["month", "quarter"], "default": "month", "description": "Granularidade do período"}
            }
        },
        handler=get_trends,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_ml_predictions",
        description="Obter predições ML para candidatos: probabilidade de aceitação, risco de rotatividade, previsão de performance, recomendação de ação.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato para predição (opcional)"},
                "job_id": {"type": "string", "description": "UUID da vaga para contexto (opcional)"}
            }
        },
        handler=get_ml_predictions,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "wsi_evaluator", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_conversion_patterns",
        description="Analisar padrões de conversão por fonte e perfil: fontes mais eficientes, perfis com maior conversão, funil de conversão por etapa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar (opcional)"}
            }
        },
        handler=get_conversion_patterns,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "sourcing", "orchestrator"]
    ))

    tool_registry.register(ToolDefinition(
        name="get_smart_alerts",
        description="Obter alertas inteligentes e detecção de riscos: vagas em risco de SLA, candidatos esfriando, gargalos no pipeline, ações urgentes.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar alertas (opcional)"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "all"], "default": "all", "description": "Filtrar por severidade"}
            }
        },
        handler=get_smart_alerts,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))

    logger.info("✅ Registered 19 analytics query tools")
