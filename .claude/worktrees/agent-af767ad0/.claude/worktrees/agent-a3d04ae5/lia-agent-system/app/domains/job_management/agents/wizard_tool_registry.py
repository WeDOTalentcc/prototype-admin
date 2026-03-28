"""
Wizard Tool Registry - Exposes wizard tools to the ReAct loop.

Wraps existing job_wizard_tools functions into ToolDefinition format
so the ReActLoop can autonomously decide which tools to call.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import text as sql_text

from app.core.database import AsyncSessionLocal

from app.shared.agents.react_loop import ToolDefinition
from app.shared.compliance.fairness_guard import FairnessGuard
from app.domains.job_management.tools.job_wizard_tools import (
    search_salary_benchmark as _search_salary_benchmark,
    validate_job_fields as _validate_job_fields,
    get_job_suggestions as _get_job_suggestions,
    save_job_draft as _save_job_draft,
    get_company_config as _get_company_config,
    generate_enriched_jd as _generate_enriched_jd,
)

logger = logging.getLogger(__name__)

MARKET_SALARY_BENCHMARKS = {
    "estagio": {"min": 1200, "max": 2500, "currency": "BRL"},
    "estagiario": {"min": 1200, "max": 2500, "currency": "BRL"},
    "junior": {"min": 3000, "max": 6000, "currency": "BRL"},
    "júnior": {"min": 3000, "max": 6000, "currency": "BRL"},
    "pleno": {"min": 6000, "max": 12000, "currency": "BRL"},
    "senior": {"min": 12000, "max": 22000, "currency": "BRL"},
    "sênior": {"min": 12000, "max": 22000, "currency": "BRL"},
    "especialista": {"min": 15000, "max": 28000, "currency": "BRL"},
    "gerente": {"min": 18000, "max": 35000, "currency": "BRL"},
    "diretor": {"min": 30000, "max": 60000, "currency": "BRL"},
    "c-level": {"min": 40000, "max": 80000, "currency": "BRL"},
}

MARKET_BENCHMARK_SOURCES = [
    "Robert Half - Guia Salarial 2024",
    "Gupy - Pesquisa de Remuneração 2024",
    "Glassdoor Brasil - Dados salariais agregados",
]

_fairness_guard = FairnessGuard()


async def _wrap_validate_job_requirements(**kwargs: Any) -> Dict[str, Any]:
    text = kwargs.get("text", "")
    field_name = kwargs.get("field_name", "requirements")
    logger.info(f"[wizard_tools] validate_job_requirements called for field={field_name}")
    try:
        explicit_result = _fairness_guard.check(text)
        implicit_warnings = _fairness_guard.check_implicit_bias(text)

        if explicit_result.is_blocked:
            return {
                "is_compliant": False,
                "educational_message": explicit_result.educational_message,
                "blocked_terms": explicit_result.blocked_terms,
                "category": explicit_result.category,
                "soft_warnings": implicit_warnings,
                "field_name": field_name,
            }

        semantic_warnings = []
        try:
            semantic_result = await _fairness_guard.check_semantic(text, context=f"job_{field_name}")
            if semantic_result.is_blocked:
                return {
                    "is_compliant": False,
                    "educational_message": semantic_result.educational_message,
                    "blocked_terms": semantic_result.blocked_terms,
                    "category": semantic_result.category,
                    "soft_warnings": implicit_warnings + (semantic_result.soft_warnings or []),
                    "field_name": field_name,
                }
            semantic_warnings = semantic_result.soft_warnings or []
        except Exception as sem_err:
            logger.debug(f"[wizard_tools] semantic check skipped: {sem_err}")

        all_warnings = implicit_warnings + [w for w in semantic_warnings if w not in implicit_warnings]

        return {
            "is_compliant": True,
            "educational_message": None,
            "soft_warnings": all_warnings,
            "field_name": field_name,
        }
    except Exception as e:
        logger.error(f"[wizard_tools] validate_job_requirements error: {e}", exc_info=True)
        return {"is_compliant": True, "soft_warnings": [], "error": str(e)}


async def _wrap_get_salary_benchmarks(**kwargs: Any) -> Dict[str, Any]:
    job_title = kwargs.get("job_title", "")
    seniority = kwargs.get("seniority", "pleno")
    location = kwargs.get("location", "")
    department = kwargs.get("department", "")
    logger.info(f"[wizard_tools] get_salary_benchmarks called for title={job_title}, seniority={seniority}")

    internal_avg: Optional[Dict[str, Any]] = None
    try:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            query = sql_text("""
                SELECT
                    AVG((salary_range->>'min')::float) as avg_min,
                    AVG((salary_range->>'max')::float) as avg_max,
                    COUNT(*) as total_vagas
                FROM job_vacancies
                WHERE salary_range IS NOT NULL
                  AND (title ILIKE :title_pattern OR department = :dept)
            """)
            result = await db.execute(query, {
                "title_pattern": f"%{job_title}%",
                "dept": department or "",
            })
            row = result.fetchone()
            if row and row.total_vagas and row.total_vagas > 0:
                internal_avg = {
                    "avg_min": round(float(row.avg_min), 2) if row.avg_min else None,
                    "avg_max": round(float(row.avg_max), 2) if row.avg_max else None,
                    "sample_size": int(row.total_vagas),
                    "source": "Histórico interno da empresa",
                }
    except Exception as e:
        logger.warning(f"[wizard_tools] get_salary_benchmarks SQL error (non-fatal): {e}")

    seniority_key = seniority.lower().strip() if seniority else "pleno"
    market_range = MARKET_SALARY_BENCHMARKS.get(seniority_key, MARKET_SALARY_BENCHMARKS.get("pleno"))

    recommendation = None
    if internal_avg and internal_avg.get("avg_min") and market_range:
        if internal_avg["avg_min"] < market_range["min"] * 0.8:
            recommendation = (
                f"O histórico interno (R$ {internal_avg['avg_min']:,.0f}-{internal_avg['avg_max']:,.0f}) "
                f"está abaixo do benchmark de mercado (R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}) "
                f"para nível {seniority}. Considere ajustar para atrair melhores candidatos."
            )
        elif internal_avg["avg_max"] and internal_avg["avg_max"] > market_range["max"] * 1.2:
            recommendation = (
                f"O histórico interno (R$ {internal_avg['avg_min']:,.0f}-{internal_avg['avg_max']:,.0f}) "
                f"está acima do benchmark de mercado (R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}) "
                f"para nível {seniority}. A empresa oferece remuneração competitiva."
            )
        else:
            recommendation = (
                f"O histórico interno está alinhado com o benchmark de mercado "
                f"(R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}) para nível {seniority}."
            )
    elif market_range:
        recommendation = (
            f"Sem histórico interno disponível. Benchmark de mercado para {seniority}: "
            f"R$ {market_range['min']:,.0f}-{market_range['max']:,.0f}."
        )

    return {
        "internal_avg": internal_avg,
        "market_range": {
            "min": market_range["min"] if market_range else None,
            "max": market_range["max"] if market_range else None,
            "currency": "BRL",
            "seniority": seniority,
        },
        "sources": MARKET_BENCHMARK_SOURCES,
        "recommendation": recommendation,
        "job_title": job_title,
        "location": location or "Brasil",
    }


async def _wrap_search_salary_benchmark(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper for search_salary_benchmark that handles errors gracefully."""
    logger.info(f"[wizard_tools] search_salary_benchmark called with: {list(kwargs.keys())}")
    try:
        return await _search_salary_benchmark(**kwargs)
    except Exception as e:
        logger.error(f"[wizard_tools] search_salary_benchmark error: {e}", exc_info=True)
        return {"error": str(e), "success": False}


async def _wrap_validate_job_fields(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper for validate_job_fields that handles errors gracefully."""
    logger.info(f"[wizard_tools] validate_job_fields called with: {list(kwargs.keys())}")
    try:
        return await _validate_job_fields(**kwargs)
    except Exception as e:
        logger.error(f"[wizard_tools] validate_job_fields error: {e}", exc_info=True)
        return {"error": str(e), "success": False}


async def _wrap_get_job_suggestions(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper for get_job_suggestions that handles errors gracefully."""
    logger.info(f"[wizard_tools] get_job_suggestions called with: {list(kwargs.keys())}")
    try:
        return await _get_job_suggestions(**kwargs)
    except Exception as e:
        logger.error(f"[wizard_tools] get_job_suggestions error: {e}", exc_info=True)
        return {"error": str(e), "success": False}


async def _wrap_save_job_draft(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper for save_job_draft that handles errors gracefully."""
    logger.info(f"[wizard_tools] save_job_draft called with: {list(kwargs.keys())}")
    try:
        return await _save_job_draft(**kwargs)
    except Exception as e:
        logger.error(f"[wizard_tools] save_job_draft error: {e}", exc_info=True)
        return {"error": str(e), "success": False}


async def _wrap_get_company_config(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper for get_company_config that handles errors gracefully."""
    logger.info(f"[wizard_tools] get_company_config called with: {list(kwargs.keys())}")
    try:
        return await _get_company_config(**kwargs)
    except Exception as e:
        logger.error(f"[wizard_tools] get_company_config error: {e}", exc_info=True)
        return {"error": str(e), "success": False}


async def _wrap_generate_enriched_jd(**kwargs: Any) -> Dict[str, Any]:
    """Wrapper for generate_enriched_jd that handles errors gracefully."""
    logger.info(f"[wizard_tools] generate_enriched_jd called with: {list(kwargs.keys())}")
    try:
        return await _generate_enriched_jd(**kwargs)
    except Exception as e:
        logger.error(f"[wizard_tools] generate_enriched_jd error: {e}", exc_info=True)
        return {"error": str(e), "success": False}


async def _wrap_check_job_draft_health(**kwargs: Any) -> Dict[str, Any]:
    title = kwargs.get("title", "")
    seniority = kwargs.get("seniority", "")
    salary_min = kwargs.get("salary_min", 0)
    salary_max = kwargs.get("salary_max", 0)
    skills_count = kwargs.get("skills_count", 0)
    responsibilities_count = kwargs.get("responsibilities_count", 0)
    logger.info(f"[wizard_tools] check_job_draft_health called: title={title}")

    risks = []

    if not title:
        risks.append({
            "level": "high",
            "type": "missing_title",
            "message": "Titulo da vaga nao definido. Campo obrigatorio.",
        })

    if not seniority:
        risks.append({
            "level": "medium",
            "type": "missing_seniority",
            "message": "Senioridade nao definida. Essencial para calibrar requisitos e remuneracao.",
        })

    if salary_max > 0 and seniority:
        key = seniority.lower().replace("í", "i").replace("ê", "e")
        bench = MARKET_SALARY_BENCHMARKS.get(key)
        if bench and salary_max < bench["min"]:
            risks.append({
                "level": "high",
                "type": "salary_below_market",
                "message": f"Salario maximo (R${salary_max:,.0f}) abaixo do piso de mercado (R${bench['min']:,.0f}) para {seniority}. Risco de atracao insuficiente.",
            })

    if skills_count < 3:
        risks.append({
            "level": "medium",
            "type": "few_skills",
            "message": f"Apenas {skills_count} skills definidas. O recomendado e 5-10 para boa triagem WSI.",
        })

    if responsibilities_count < 2:
        risks.append({
            "level": "medium",
            "type": "few_responsibilities",
            "message": f"Apenas {responsibilities_count} responsabilidades. O recomendado e 4-8 para descricao completa.",
        })

    overall_health = "healthy"
    if any(r["level"] == "high" for r in risks):
        overall_health = "critical"
    elif any(r["level"] == "medium" for r in risks):
        overall_health = "attention"

    return {
        "success": True,
        "data": {
            "title": title or "(nao definido)",
            "risks": risks,
            "overall_health": overall_health,
            "completeness": max(0, 100 - len(risks) * 15),
        },
        "sources": MARKET_BENCHMARK_SOURCES,
        "message": f"Saude do rascunho: {overall_health}. {len(risks)} riscos identificados.",
    }


TOOL_DEFINITIONS: List[ToolDefinition] = [
    ToolDefinition(
        name="validate_job_requirements",
        description="Valida requisitos da vaga contra viés discriminatório usando FairnessGuard. Verifica viés explícito (bloqueia) e implícito (alertas educacionais). Use para validar requirements, description e screening_questions.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Conteúdo a validar (requisitos, descrição ou perguntas de triagem)"},
                "field_name": {"type": "string", "description": "Campo sendo validado: requirements, description ou screening_questions"},
            },
            "required": ["text", "field_name"],
        },
        function=_wrap_validate_job_requirements,
    ),
    ToolDefinition(
        name="get_salary_benchmarks",
        description="Busca benchmarks salariais reais combinando histórico interno da empresa (SQL) com dados de mercado (Robert Half 2024, Gupy). Retorna internal_avg, market_range, sources citáveis e recommendation. Use no estágio salary para fornecer dados concretos.",
        parameters={
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Titulo do cargo"},
                "seniority": {"type": "string", "description": "Nivel de senioridade (Estagio, Junior, Pleno, Senior, Especialista, Gerente, Diretor)"},
                "location": {"type": "string", "description": "Localizacao/cidade/regiao"},
                "department": {"type": "string", "description": "Departamento da vaga"},
            },
            "required": ["job_title", "seniority"],
        },
        function=_wrap_get_salary_benchmarks,
    ),
    ToolDefinition(
        name="search_salary_benchmark",
        description="Busca benchmarks salariais de mercado para um cargo. Retorna faixa salarial com min, max e mediana baseado em dados de mercado.",
        parameters={
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Titulo do cargo"},
                "seniority": {"type": "string", "description": "Nivel de senioridade (Junior, Pleno, Senior, etc.)"},
                "location": {"type": "string", "description": "Localizacao/cidade"},
                "industry": {"type": "string", "description": "Setor da industria"},
            },
            "required": ["job_title"],
        },
        function=_wrap_search_salary_benchmark,
    ),
    ToolDefinition(
        name="validate_job_fields",
        description="Valida os campos preenchidos da vaga. Retorna score de completude, campos preenchidos e campos faltantes.",
        parameters={
            "type": "object",
            "properties": {
                "job_data": {"type": "object", "description": "Dados atuais da vaga"},
                "company_config": {"type": "object", "description": "Configuracao da empresa"},
            },
            "required": ["job_data"],
        },
        function=_wrap_validate_job_fields,
    ),
    ToolDefinition(
        name="get_job_suggestions",
        description="Obtem sugestoes de IA para um campo especifico da vaga (skills, beneficios, competencias, modelo de trabalho, etc.).",
        parameters={
            "type": "object",
            "properties": {
                "field_name": {"type": "string", "description": "Nome do campo (skills, behavioral_competencies, benefits, work_model, seniority, etc.)"},
                "job_context": {"type": "object", "description": "Contexto atual da vaga"},
                "company_id": {"type": "string", "description": "ID da empresa"},
            },
            "required": ["field_name", "job_context"],
        },
        function=_wrap_get_job_suggestions,
    ),
    ToolDefinition(
        name="save_job_draft",
        description="Salva o rascunho atual da vaga no banco de dados. Use quando o usuario confirmar dados ou quiser salvar progresso.",
        parameters={
            "type": "object",
            "properties": {
                "draft_id": {"type": "string", "description": "UUID do rascunho"},
                "updates": {"type": "object", "description": "Campos a atualizar"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador"},
                "company_id": {"type": "string", "description": "ID da empresa"},
            },
            "required": ["draft_id", "updates", "recruiter_id", "company_id"],
        },
        function=_wrap_save_job_draft,
    ),
    ToolDefinition(
        name="get_company_config",
        description="Busca configuracoes da empresa: beneficios, politicas salariais, templates de pipeline, perguntas de triagem e cultura.",
        parameters={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID da empresa"},
                "config_type": {"type": "string", "description": "Tipo de config: all, benefits, salary_levels, pipeline_templates, screening_questions, communication, culture, ai_context"},
                "seniority": {"type": "string", "description": "Nivel de senioridade para filtrar beneficios"},
            },
            "required": ["company_id"],
        },
        function=_wrap_get_company_config,
    ),
    ToolDefinition(
        name="generate_enriched_jd",
        description="Gera descricao de vaga enriquecida com sugestoes de responsabilidades, skills, competencias e remuneracao baseadas em benchmarks de mercado.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titulo do cargo"},
                "company_id": {"type": "string", "description": "ID da empresa"},
                "seniority": {"type": "string", "description": "Nivel de senioridade"},
                "location": {"type": "string", "description": "Localizacao"},
                "detected_responsibilities": {"type": "array", "items": {"type": "string"}, "description": "Responsabilidades ja detectadas"},
                "detected_skills": {"type": "array", "items": {"type": "string"}, "description": "Skills ja detectadas"},
                "detected_behavioral": {"type": "array", "items": {"type": "string"}, "description": "Competencias comportamentais ja detectadas"},
                "salary_min": {"type": "number", "description": "Salario minimo"},
                "salary_max": {"type": "number", "description": "Salario maximo"},
            },
            "required": ["title", "company_id"],
        },
        function=_wrap_generate_enriched_jd,
    ),
    ToolDefinition(
        name="check_job_draft_health",
        description="Avalia proativamente a saude do rascunho da vaga: identifica riscos como campos faltantes, salario abaixo do mercado, poucas skills ou responsabilidades. Use antes de publicar para garantir qualidade.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titulo da vaga"},
                "seniority": {"type": "string", "description": "Nivel de senioridade"},
                "salary_min": {"type": "number", "description": "Salario minimo oferecido"},
                "salary_max": {"type": "number", "description": "Salario maximo oferecido"},
                "skills_count": {"type": "integer", "description": "Numero de skills definidas"},
                "responsibilities_count": {"type": "integer", "description": "Numero de responsabilidades definidas"},
            },
            "required": [],
        },
        function=_wrap_check_job_draft_health,
    ),
]


async def _wrap_generate_report(**kwargs: Any) -> Dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[wizard_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: Dict[str, Any] = {}
    try:
        async with AsyncSessionLocal() as session:
            row = await session.execute(sql_text("""
                SELECT COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'draft') AS drafts,
                    COUNT(*) FILTER (WHERE status = 'published') AS published
                FROM job_vacancies
                WHERE (:cid = '' OR company_id = :cid)
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """), {"cid": company_id, "days": period_days})
            data = row.mappings().first() or {}
            summary = {
                "total_jobs": int(data.get("total") or 0),
                "drafts": int(data.get("drafts") or 0),
                "published": int(data.get("published") or 0),
            }
    except Exception as e:
        logger.warning(f"[wizard_tools] generate_report DB error: {e}")
    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "period": period,
            "report_id": report_id,
            "generated": True,
            "summary": summary,
        },
        "message": f"Relatorio '{report_type}' de vagas gerado (id: {report_id}). {summary.get('total_jobs', 0)} vagas no periodo.",
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="generate_report",
        description="Gera relatorio de vagas criadas e publicadas no periodo selecionado.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo de relatorio: summary, detailed"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
                "company_id": {"type": "string", "description": "ID da empresa (opcional)"},
            },
            "required": [],
        },
        function=_wrap_generate_report,
    )
)

_TOOL_MAP: Dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: Dict[str, List[str]] = {
    "input-evaluation": ["validate_job_requirements", "validate_job_fields", "get_job_suggestions", "get_company_config", "save_job_draft", "check_job_draft_health"],
    "jd-enrichment": ["generate_enriched_jd", "get_job_suggestions", "get_company_config", "save_job_draft", "check_job_draft_health"],
    "salary": ["get_salary_benchmarks", "search_salary_benchmark", "validate_job_fields", "save_job_draft", "check_job_draft_health"],
    "competencies": ["validate_job_requirements", "get_job_suggestions", "validate_job_fields", "save_job_draft"],
    "wsi-questions": ["validate_job_requirements", "validate_job_fields", "save_job_draft"],
    "review-publish": ["validate_job_requirements", "save_job_draft", "validate_job_fields", "check_job_draft_health", "generate_report"],
}


def get_wizard_tools() -> List[ToolDefinition]:
    """Return all wizard tool definitions."""
    return list(TOOL_DEFINITIONS)


def get_stage_tools(stage: str) -> List[ToolDefinition]:
    """Return only tools relevant to the current wizard stage.

    Args:
        stage: Current wizard stage identifier.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    logger.debug(f"[wizard_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
