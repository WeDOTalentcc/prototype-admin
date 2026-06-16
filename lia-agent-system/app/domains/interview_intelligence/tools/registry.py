"""Interview Intelligence — Tool Registry for Agent Studio.

Exposes 5 tools from interview_intelligence services via the Agent Studio
factory (CustomAgentRuntime). Tool functions are reused from
talent_intelligence/tools/interview_intelligence_tools.py — no duplication.
"""
from lia_agents_core.tool_adapter import ToolDefinition, ToolOutput

from app.domains.talent_intelligence.tools.interview_intelligence_tools import (
    analyze_interview_recording,
    compare_interview_performance,
    detect_interview_bias,
    generate_candidate_feedback,
    generate_interview_opinion,
)


def get_interview_intelligence_tools() -> list[ToolDefinition]:
    """Return all ToolDefinitions for the Interview Intelligence domain."""
    return [
        ToolDefinition(
            name="analyze_interview_recording",
            description=(
                "Análise completa de entrevista: WSI (Bloom, Dreyfus, CBI, Big Five) + "
                "detecção de viés + análise comparativa + parecer estratégico + feedback. "
                "Parâmetros: interview_id (str, obrigatório — busca transcrição do banco), "
                "interview_type (str, padrão 'behavioral'), include_bias (bool, padrão True), "
                "include_comparative (bool, padrão True), include_opinion (bool, padrão True), "
                "include_feedback (bool, padrão True)."
            ),
            output_schema=ToolOutput,
            function=analyze_interview_recording,
        ),
        ToolDefinition(
            name="detect_interview_bias",
            description=(
                "Detectar viés em entrevista: padrões linguísticos + análise LLM. "
                "Identifica viés de idade, gênero, aparência, afinidade, confirmação "
                "e perguntas ilegais. Parâmetros: interview_id (str, obrigatório), "
                "use_llm (bool, padrão True)."
            ),
            output_schema=ToolOutput,
            function=detect_interview_bias,
        ),
        ToolDefinition(
            name="compare_interview_performance",
            description=(
                "Comparar performance de candidato em entrevista vs. outros candidatos "
                "da mesma vaga. Ranking, benchmarks e insights comparativos. "
                "Parâmetros: interview_id (str, obrigatório)."
            ),
            output_schema=ToolOutput,
            function=compare_interview_performance,
        ),
        ToolDefinition(
            name="generate_interview_opinion",
            description=(
                "Gerar parecer estratégico de contratação: CONTRATAR / NÃO CONTRATAR / "
                "AVALIAR MAIS com evidências, riscos e mitigações. Baseado em WSI, viés "
                "e comparativo. Parâmetros: interview_id (str, obrigatório)."
            ),
            output_schema=ToolOutput,
            function=generate_interview_opinion,
        ),
        ToolDefinition(
            name="generate_candidate_feedback",
            description=(
                "Gerar feedback estruturado e construtivo para devolver ao candidato "
                "após entrevista. Foca em competências demonstradas e áreas de "
                "desenvolvimento. Parâmetros: interview_id (str, obrigatório)."
            ),
            output_schema=ToolOutput,
            function=generate_candidate_feedback,
        ),
    ]
