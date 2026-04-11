"""Tool registry for talent intelligence tools."""
import logging

from app.tools.registry import ToolDefinition, tool_registry

from .candidate_nurture_tools import (
    create_nurture_sequence,
    get_engagement_metrics,
    suggest_reengagement,
)
from .internal_mobility_tools import match_internal_candidates
from .interview_intelligence_tools import analyze_interview_recording
from .market_intelligence_tools import get_market_intelligence
from .skills_ontology_tools import (
    analyze_skill_gaps,
    get_skill_adjacencies,
    infer_related_skills,
    map_candidate_skills_to_ontology,
)
from .workforce_planning_tools import forecast_hiring_needs

logger = logging.getLogger(__name__)


def register_talent_intelligence_tools() -> None:
    """Register all talent intelligence domain tools in the tool registry."""

    tool_registry.register(ToolDefinition(
        name="infer_related_skills",
        description="Inferir skills relacionadas a partir de uma lista de skills usando o grafo de ontologia (adjacência e propagação).",
        parameters_schema={
            "type": "object",
            "properties": {
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de skills para buscar relacionadas"},
                "depth": {"type": "integer", "default": 2, "description": "Profundidade máxima de travessia no grafo (1-3)"},
                "limit": {"type": "integer", "default": 15, "description": "Número máximo de skills relacionadas a retornar"},
            },
            "required": ["skills"],
        },
        handler=infer_related_skills,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "analytics", "job_planner", "job_wizard"],
    ))

    tool_registry.register(ToolDefinition(
        name="get_skill_adjacencies",
        description="Obter skills adjacentes no grafo de ontologia com pesos de proximidade.",
        parameters_schema={
            "type": "object",
            "properties": {
                "skill": {"type": "string", "description": "Nome da skill"},
                "min_weight": {"type": "number", "default": 0.0, "description": "Peso mínimo para filtrar adjacências"},
            },
            "required": ["skill"],
        },
        handler=get_skill_adjacencies,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "analytics", "job_planner", "job_wizard"],
    ))

    tool_registry.register(ToolDefinition(
        name="analyze_skill_gaps",
        description="Analisar gaps de skills entre candidato e requisitos da vaga usando adjacências da ontologia.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_skills": {"type": "array", "items": {"type": "string"}, "description": "Skills do candidato"},
                "required_skills": {"type": "array", "items": {"type": "string"}, "description": "Skills requeridas pela vaga"},
                "candidate_id": {"type": "string", "description": "UUID do candidato (carrega skills do DB se candidate_skills vazio)"},
                "job_id": {"type": "string", "description": "UUID da vaga (carrega requisitos do DB se required_skills vazio)"},
            },
        },
        handler=analyze_skill_gaps,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "analytics", "screening"],
    ))

    tool_registry.register(ToolDefinition(
        name="map_candidate_skills_to_ontology",
        description="Mapear skills brutas de um candidato para nós canônicos da ontologia de skills.",
        parameters_schema={
            "type": "object",
            "properties": {
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de skills brutas (texto livre)"},
                "candidate_id": {"type": "string", "description": "UUID do candidato (carrega skills do DB se skills vazio)"},
            },
        },
        handler=map_candidate_skills_to_ontology,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "analytics", "screening"],
    ))

    tool_registry.register(ToolDefinition(
        name="match_internal_candidates",
        description="Encontrar candidatos internos para mobilidade interna usando matching baseado na ontologia de skills.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (carrega skills/título do DB)"},
                "required_skills": {"type": "array", "items": {"type": "string"}, "description": "Skills requeridas pela posição alvo"},
                "job_title": {"type": "string", "description": "Título da posição alvo"},
                "seniority": {"type": "string", "description": "Nível de senioridade requerido"},
                "department": {"type": "string", "description": "Departamento para filtrar (opcional)"},
                "limit": {"type": "integer", "default": 20, "description": "Máximo de candidatos a retornar"},
            },
        },
        handler=match_internal_candidates,
        allowed_agents=["orchestrator", "recruiter_assistant", "analytics"],
    ))

    tool_registry.register(ToolDefinition(
        name="forecast_hiring_needs",
        description="Prever necessidades de contratação baseado em dados de turnover, pipeline e crescimento planejado.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter", "half_year", "year"], "default": "quarter", "description": "Horizonte de previsão"},
                "department": {"type": "string", "description": "Departamento para previsão (opcional)"},
                "growth_rate": {"type": "number", "description": "Taxa de crescimento planejado (ex: 0.10 = 10%)"},
                "include_backfills": {"type": "boolean", "default": True, "description": "Incluir estimativa de backfills por turnover"},
            },
        },
        handler=forecast_hiring_needs,
        allowed_agents=["orchestrator", "recruiter_assistant", "analytics"],
    ))

    tool_registry.register(ToolDefinition(
        name="analyze_interview_recording",
        description="Analisar transcrição de entrevista com sentimento, mapeamento de competências e detecção de viés.",
        parameters_schema={
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "Transcrição completa da entrevista"},
                "candidate_id": {"type": "string", "description": "UUID do candidato (opcional)"},
                "job_id": {"type": "string", "description": "UUID da vaga (opcional)"},
                "interviewer_name": {"type": "string", "description": "Nome do entrevistador (opcional)"},
                "interview_type": {"type": "string", "enum": ["behavioral", "technical", "cultural", "final"], "default": "behavioral", "description": "Tipo de entrevista"},
            },
            "required": ["transcript"],
        },
        handler=analyze_interview_recording,
        allowed_agents=["orchestrator", "recruiter_assistant", "screening", "analytics"],
    ))

    tool_registry.register(ToolDefinition(
        name="create_nurture_sequence",
        description="Criar sequência automatizada de nurture para candidatos passivos.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "UUIDs dos candidatos para incluir"},
                "template": {"type": "string", "enum": ["tech_talent", "leadership", "silver_medalist", "general"], "default": "general"},
                "custom_name": {"type": "string", "description": "Nome customizado para a sequência (opcional)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags de segmentação (opcional)"},
            },
            "required": ["candidate_ids"],
        },
        handler=create_nurture_sequence,
        allowed_agents=["orchestrator", "recruiter_assistant", "communication", "recruitment_campaign"],
    ))

    tool_registry.register(ToolDefinition(
        name="get_engagement_metrics",
        description="Obter métricas de engajamento de sequências de nurture derivadas de dados reais do banco.",
        parameters_schema={
            "type": "object",
            "properties": {
                "sequence_id": {"type": "string", "description": "ID da sequência (opcional — retorna agregado se omitido)"},
                "period": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month"},
            },
        },
        handler=get_engagement_metrics,
        allowed_agents=["orchestrator", "recruiter_assistant", "analytics", "recruitment_campaign"],
    ))

    tool_registry.register(ToolDefinition(
        name="suggest_reengagement",
        description="Sugerir candidatos inativos para reengajamento baseado em período de inatividade e sinais de engajamento.",
        parameters_schema={
            "type": "object",
            "properties": {
                "days_inactive": {"type": "integer", "default": 30, "description": "Dias mínimos de inatividade"},
                "limit": {"type": "integer", "default": 20, "description": "Máximo de candidatos a sugerir"},
            },
        },
        handler=suggest_reengagement,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "recruitment_campaign"],
    ))

    tool_registry.register(ToolDefinition(
        name="get_market_intelligence",
        description="Obter inteligência de mercado em tempo real: benchmarks salariais, tendências de demanda e skills em alta via fontes externas.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Título do cargo para pesquisar"},
                "seniority": {"type": "string", "description": "Nível de senioridade (Junior, Pleno, Senior)"},
                "location": {"type": "string", "description": "Localização para ajuste regional"},
                "industry": {"type": "string", "description": "Setor da indústria"},
                "include_trends": {"type": "boolean", "default": True, "description": "Incluir tendências de mercado"},
            },
            "required": ["job_title"],
        },
        handler=get_market_intelligence,
        allowed_agents=["orchestrator", "recruiter_assistant", "sourcing", "analyst_feedback", "wsi_evaluator"],
    ))

    logger.info("Registered 11 talent intelligence tools")
