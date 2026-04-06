"""Analytics & Reporting Domain - Tool definitions and executor."""
from typing import Any, Dict, List

from app.domains.base import DomainContext

ANALYTICS_TOOLS = [
    {
        "tool_id": "analytics_generate_kpi",
        "name": "Gerar KPIs",
        "description": "Gera relatórios de KPIs de recrutamento",
        "handler": "app.domains.analytics.services.report_service.generate_kpi_report",
    },
    {
        "tool_id": "analytics_analyze_funnel",
        "name": "Analisar Funil",
        "description": "Analisa métricas do funil de conversão",
        "handler": "app.domains.analytics.services.report_service.analyze_funnel",
    },
    {
        "tool_id": "analytics_job_health",
        "name": "Saúde da Vaga",
        "description": "Verifica indicadores de saúde da vaga",
        "handler": "app.domains.analytics.services.report_service.job_health_check",
    },
    {
        "tool_id": "analytics_detect_anomalies",
        "name": "Detectar Anomalias",
        "description": "Detecta anomalias nos dados de recrutamento",
        "handler": "app.domains.analytics.services.report_service.detect_anomalies",
    },
    {
        "tool_id": "analytics_get_insights",
        "name": "Insights da Vaga",
        "description": "Obtém benchmarks salariais, competências e vagas similares",
        "handler": "app.domains.analytics.services.job_insights_service.get_job_insights",
    },
    {
        "tool_id": "analytics_generate_report",
        "name": "Gerar Relatório",
        "description": "Gera relatórios em PDF/Excel para vagas e candidatos",
        "handler": "app.domains.analytics.services.job_report_service.generate_report",
    },
    {
        "tool_id": "analytics_search_analytics",
        "name": "Analytics de Busca",
        "description": "Dados de desempenho de busca de candidatos",
        "handler": "app.domains.analytics.services.search_analytics_service.get_search_analytics",
    },
    {
        "tool_id": "analytics_predict",
        "name": "Analytics Preditivo",
        "description": "Previsões de contratação, tempo de preenchimento e risco de desistência",
        "handler": "app.domains.analytics.services.predictive_analytics_service.predict",
    },
    {
        "tool_id": "analytics_dashboard",
        "name": "Dados do Dashboard",
        "description": "Obtém indicadores estratégicos e dados do dashboard",
        "handler": "app.domains.analytics.services.report_service.get_dashboard_data",
    },
    {
        "tool_id": "analytics_monitoring",
        "name": "Monitoramento de Agentes",
        "description": "Dados de monitoramento de desempenho dos agentes de IA",
        "handler": "app.domains.analytics.services.agent_monitoring_service.get_monitoring_data",
    },
]


def _get_tool_by_id(tool_id: str) -> dict | None:
    for tool in ANALYTICS_TOOLS:
        if tool["tool_id"] == tool_id:
            return tool
    return None


async def execute_analytics_tool(
    tool_id: str,
    parameters: dict[str, Any],
    context: DomainContext,
) -> dict[str, Any]:
    tool = _get_tool_by_id(tool_id)
    if not tool:
        return {"error": f"Tool {tool_id} not found", "status": "error"}

    handler_path = tool["handler"]
    parts = handler_path.rsplit(".", 1)
    if len(parts) != 2:
        return {"error": f"Invalid handler path: {handler_path}", "status": "error"}

    module_path, func_name = parts
    try:
        import importlib
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        result = await handler(**parameters) if callable(handler) else handler
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e), "status": "error", "tool_id": tool_id}
