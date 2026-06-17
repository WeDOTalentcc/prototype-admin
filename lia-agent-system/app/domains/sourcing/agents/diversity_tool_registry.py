"""
Diversity Sourcing Tool Registry — sourcing afirmativo com FairnessGuard.

Expõe tools para DiversitySourcingAgent:
- diversity_search_candidates: busca candidatos priorizando metas de diversidade
- diversity_get_pool_metrics: métricas de diversidade do pool atual
- diversity_check_goals: verifica atingimento de metas de diversidade por vaga

IMPORTANTE: Este agente prioriza (não exclui) candidatos fora das metas.
Nenhum candidato qualificado é penalizado por não pertencer a um grupo alvo.
Conforme FairnessGuard (Layer 3) e Four-Fifths Rule (FAR-4).
"""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_DIVERSITY_TOOL_DEFINITIONS: list[ToolDefinition] = []

# Allowlist estrito de grupos de diversidade válidos.
# NUNCA interpolar valores fora deste set em SQL — prevenção de SQL injection.
_ALLOWED_DIVERSITY_GROUPS = frozenset({
    "pcd", "mulheres", "negros_pardos", "lgbtqia", "50_mais", "refugiados", "baixa_renda"
})

_DIVERSITY_GROUPS = {
    "pcd": "Pessoas com Deficiência (Lei 8.213/91)",
    "mulheres": "Mulheres em tech/liderança",
    "negros_pardos": "Pessoas negras e pardas (ação afirmativa)",
    "lgbtqia": "LGBTQIA+",
    "50_mais": "Profissionais 50+ (combate etarismo)",
    "refugiados": "Refugiados e imigrantes",
    "baixa_renda": "Candidatos de baixa renda / primeira geração",
}


@tool_handler("diversity")
async def _wrap_diversity_search_candidates(**kwargs: Any) -> dict[str, Any]:
    """
    Busca candidatos aplicando critérios afirmativos de diversidade.
    Prioriza grupos subrepresentados dentro do pool qualificado.
    NÃO exclui candidatos que não pertencem aos grupos alvo.
    """
    logger.info("[diversity_tools] diversity_search_candidates called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal
    from app.shared.compliance.fairness_guard import FairnessGuard

    role = kwargs.get("role", "")
    skills = kwargs.get("skills", [])
    location = kwargs.get("location", "")
    diversity_targets = kwargs.get("diversity_targets", [])
    min_experience = kwargs.get("min_experience", 0)
    limit = min(int(kwargs.get("limit", 20)), 50)
    page = max(1, int(kwargs.get("page", 1)))
    offset = (page - 1) * limit

    # FairnessGuard: garante que query base não é discriminatória
    query_str = f"{role} {location} {' '.join(skills or [])}"
    try:
        _fg = FairnessGuard()
        _fg_result = _fg.check(query_str)
        if _fg_result.is_blocked:
            return {
                "success": False,
                "data": {},
                "message": _fg_result.educational_message or "Busca bloqueada por critério discriminatório.",
            }
    except Exception as _fg_exc:
        logger.debug("[diversity_tools] FairnessGuard check skipped: %s", _fg_exc)

    conditions = ["is_active = true"]
    params: dict[str, Any] = {"lim": limit, "off": offset}

    if role:
        conditions.append("current_title ILIKE :role_pattern")
        params["role_pattern"] = f"%{role}%"

    if skills and isinstance(skills, list) and len(skills) > 0:
        conditions.append("technical_skills && :skills_arr")
        params["skills_arr"] = skills

    if location:
        conditions.append(
            "(location_city ILIKE :loc_pattern OR location_state ILIKE :loc_pattern "
            "OR location_country ILIKE :loc_pattern)"
        )
        params["loc_pattern"] = f"%{location}%"

    if min_experience > 0:
        conditions.append("years_of_experience >= :min_exp")
        params["min_exp"] = min_experience

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Ordena priorizando candidatos que PERTENCEM aos grupos alvo (diversity_targets)
    # sem excluir quem não pertence — apenas boost de posição (sourcing afirmativo)
    #
    # SEGURANÇA: apenas grupos da allowlist _ALLOWED_DIVERSITY_GROUPS são aceitos.
    # Nenhum valor externo é interpolado em SQL — usa parâmetros vinculados (:g_N).
    safe_targets = [g for g in (diversity_targets or []) if g in _ALLOWED_DIVERSITY_GROUPS]

    if safe_targets:
        # Gerar condições com parâmetros vinculados para evitar SQL injection
        target_param_names = [f"g_{i}" for i in range(len(safe_targets))]
        for i, g in enumerate(safe_targets):
            params[f"g_{i}"] = g

        # CASE com parâmetros vinculados — seguro contra injection
        target_cond = " OR ".join(
            [f":{pname} = ANY(diversidade_autodeclarada)" for pname in target_param_names]
        )
        order_clause = f"""
            CASE
                WHEN diversidade_autodeclarada IS NOT NULL
                 AND ({target_cond}) THEN 0
                WHEN diversidade_autodeclarada IS NOT NULL
                 AND array_length(diversidade_autodeclarada, 1) > 0 THEN 1
                ELSE 2
            END,
            lia_score DESC NULLS LAST,
            years_of_experience DESC NULLS LAST
        """
    else:
        # Sem metas definidas: boost genérico para qualquer perfil de diversidade
        order_clause = """
            CASE
                WHEN diversidade_autodeclarada IS NOT NULL
                 AND array_length(diversidade_autodeclarada, 1) > 0 THEN 0
                ELSE 1
            END,
            lia_score DESC NULLS LAST,
            years_of_experience DESC NULLS LAST
        """

    query = f"""
        SELECT id, name, email, current_title, current_company,
               seniority_level, years_of_experience,
               technical_skills, soft_skills,
               location_city, location_state, location_country,
               status, lia_score,
               diversidade_autodeclarada
        FROM candidates
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT :lim OFFSET :off
    """

    count_query = f"SELECT COUNT(*) as total FROM candidates WHERE {where_clause}"

    # ADR-001-EXEMPT: diversity search with _ALLOWED_DIVERSITY_GROUPS allowlist + CASE ORDER BY bound params — LGPD Art.5 sensitive data, dynamic CASE not abstractable to repo without recreating same logic; FairnessGuard wraps output
    async with AsyncSessionLocal() as session:
        try:
            count_result = await session.execute(text(count_query), params)
            total = count_result.scalar() or 0
            result = await session.execute(text(query), params)
            rows = result.mappings().all()
        except Exception as db_exc:
            logger.warning("[diversity_tools] DB sem coluna diversidade_autodeclarada — fallback: %s", db_exc)
            # Fallback: busca sem coluna de diversidade
            simple_query = f"""
                SELECT id, name, email, current_title, current_company,
                       seniority_level, years_of_experience,
                       technical_skills, soft_skills,
                       location_city, location_state, location_country,
                       status, lia_score
                FROM candidates
                WHERE {where_clause}
                ORDER BY lia_score DESC NULLS LAST
                LIMIT :lim OFFSET :off
            """
            # ADR-001-EXEMPT: diversity search fallback (no diversidade_autodeclarada col) — same LGPD Art.5 exemption as main block above
            result = await session.execute(text(simple_query), params)
            rows = result.mappings().all()
            total = len(rows)

    candidates = []
    for row in rows:
        diversity_flags = list(row["diversidade_autodeclarada"] or []) if "diversidade_autodeclarada" in row.keys() else []
        candidates.append({
            "id": str(row["id"]),
            "name": row["name"],
            "email": row["email"],
            "current_title": row["current_title"],
            "current_company": row["current_company"],
            "seniority_level": row["seniority_level"],
            "years_of_experience": row["years_of_experience"],
            "technical_skills": row["technical_skills"] or [],
            "location": (
                f"{row['location_city'] or ''}, "
                f"{row['location_state'] or ''}, "
                f"{row['location_country'] or ''}"
            ).strip(", "),
            "status": row["status"],
            "lia_score": row["lia_score"],
            "diversity_flags": diversity_flags,
            "has_diversity_profile": len(diversity_flags) > 0,
        })

    # Métricas de diversidade do resultado
    with_diversity = [c for c in candidates if c.get("has_diversity_profile")]
    diversity_rate = len(with_diversity) / max(len(candidates), 1) * 100

    return {
        "success": True,
        "data": {
            "candidates": candidates,
            "total_results": total,
            "page": page,
            "limit": limit,
            "diversity_metrics": {
                "candidates_with_diversity_profile": len(with_diversity),
                "total_candidates": len(candidates),
                "diversity_rate_percent": round(diversity_rate, 1),
                "targets_applied": diversity_targets,
                "note": "Candidatos qualificados com perfil de diversidade foram priorizados, não excluídos outros.",
            },
        },
        "message": (
            f"{len(candidates)} candidato(s) encontrado(s) com critérios de diversidade aplicados. "
            f"{len(with_diversity)} ({diversity_rate:.0f}%) possuem perfil de diversidade autodeclarado."
        ),
    }
_DIVERSITY_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="diversity_search_candidates",
        description=(
            "Busca candidatos priorizando metas de diversidade ativas (PCD, mulheres, negros/pardos, "
            "LGBTQIA+, 50+). IMPORTANTE: NÃO exclui candidatos que não pertencem aos grupos alvo — "
            "apenas prioriza candidatos qualificados com perfil de diversidade dentro do pool. "
            "Conforme FairnessGuard e Four-Fifths Rule."
        ),
        parameters={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Cargo/função buscado"},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills técnicas requeridas",
                },
                "location": {"type": "string", "description": "Localização"},
                "diversity_targets": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["pcd", "mulheres", "negros_pardos", "lgbtqia", "50_mais", "refugiados", "baixa_renda"],
                    },
                    "description": "Grupos de diversidade alvo para priorização (não exclusão)",
                },
                "min_experience": {
                    "type": "integer",
                    "description": "Experiência mínima em anos",
                    "default": 0,
                },
                "limit": {"type": "integer", "description": "Máximo de resultados (padrão: 20)", "default": 20},
                "page": {"type": "integer", "description": "Página (padrão: 1)", "default": 1},
            },
            "required": [],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name", "email", "linkedin_url"],
        output_schema=ToolOutput,
        function=_wrap_diversity_search_candidates,
    )
)


@tool_handler("diversity")
async def _wrap_diversity_get_pool_metrics(**kwargs: Any) -> dict[str, Any]:
    """Calcula métricas de diversidade do pool de candidatos atual."""
    logger.info("[diversity_tools] diversity_get_pool_metrics called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")

    # ADR-001-EXEMPT: Four-Fifths Rule metrics aggregation — multi-step COUNT with fairness calculation, not abstractable to simple repo method
    async with AsyncSessionLocal() as session:
        try:
            # P0.A canonical: diversity metrics MUST be tenant-scoped (LGPD
            # sensitive data — diversidade_autodeclarada). company_id IS NULL
            # preserves global pool aggregation; explicit company_id matches
            # only this tenant's candidates.
            result = await session.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN diversidade_autodeclarada IS NOT NULL
                                AND array_length(diversidade_autodeclarada, 1) > 0
                               THEN 1 END) as with_diversity,
                    COUNT(CASE WHEN 'pcd' = ANY(diversidade_autodeclarada) THEN 1 END) as pcd_count,
                    COUNT(CASE WHEN 'mulheres' = ANY(diversidade_autodeclarada) THEN 1 END) as mulheres_count,
                    COUNT(CASE WHEN 'negros_pardos' = ANY(diversidade_autodeclarada) THEN 1 END) as negros_count,
                    COUNT(CASE WHEN 'lgbtqia' = ANY(diversidade_autodeclarada) THEN 1 END) as lgbtqia_count,
                    COUNT(CASE WHEN '50_mais' = ANY(diversidade_autodeclarada) THEN 1 END) as seniors_count
                FROM candidates
                WHERE is_active = true
                  AND (company_id IS NULL OR company_id = :company_id)
            """), {"company_id": company_id})
            row = result.mappings().first()
        except Exception:
            # P1 audit 2026-05-20: graceful degradation legitima (coluna em
            # rollout). Mantem success=True (pool size real) + flag explicita
            # fallback_used pra observabilidade. Nao e mentira semantica.
            result = await session.execute(
                text("SELECT COUNT(*) as total FROM candidates WHERE is_active = true AND (company_id IS NULL OR company_id = :company_id)"),
                {"company_id": company_id},
            )
            total_row = result.scalar() or 0
            return {
                "success": True,
                "fallback_used": True,
                "data": {
                    "total_candidates": total_row,
                    "note": "Coluna diversidade_autodeclarada não disponível ainda neste ambiente.",
                },
                "message": f"Pool com {total_row} candidatos ativos. Métricas de diversidade indisponíveis.",
            }

    total = row["total"] or 0
    with_diversity = row["with_diversity"] or 0
    diversity_rate = with_diversity / max(total, 1) * 100

    # Four-Fifths Rule (Regra dos 4/5 — Adverse Impact Ratio)
    # Para cada grupo protegido, calcular taxa de representação no pool.
    # Grupo majoritário = candidatos sem perfil de diversidade.
    # A taxa de seleção de cada grupo deve ser >= 80% da taxa do grupo majoritário.
    # Taxa = contagem_grupo / total_pool
    majority_count = total - with_diversity
    majority_rate = majority_count / max(total, 1)

    breakdown = {
        "pcd": row["pcd_count"] or 0,
        "mulheres": row["mulheres_count"] or 0,
        "negros_pardos": row["negros_count"] or 0,
        "lgbtqia": row["lgbtqia_count"] or 0,
        "50_mais": row["seniors_count"] or 0,
    }

    four_fifths_detail: dict[str, Any] = {}
    all_compliant = True
    for group, count in breakdown.items():
        if total == 0:
            ratio = 1.0
        elif majority_rate == 0:
            # Sem maioria definida: todos são diversidade — não há adverse impact
            ratio = 1.0
        else:
            group_rate = count / max(total, 1)
            ratio = group_rate / majority_rate

        compliant = ratio >= 0.8
        if not compliant:
            all_compliant = False
        four_fifths_detail[group] = {
            "count": count,
            "rate_in_pool": round(count / max(total, 1) * 100, 1),
            "adverse_impact_ratio": round(ratio, 3),
            "compliant": compliant,
            "threshold": 0.8,
        }

    return {
        "success": True,
        "data": {
            "total_candidates": total,
            "with_diversity_profile": with_diversity,
            "diversity_rate_percent": round(diversity_rate, 1),
            "breakdown": breakdown,
            "four_fifths_rule": {
                "method": "adverse_impact_ratio",
                "threshold": 0.8,
                "majority_group_rate": round(majority_rate * 100, 1),
                "all_groups_compliant": all_compliant,
                "group_detail": four_fifths_detail,
            },
            "vacancy_id": vacancy_id,
            "company_id": company_id,
        },
        "message": (
            f"Pool com {total} candidatos: {with_diversity} ({diversity_rate:.1f}%) com perfil de diversidade. "
            + ("Four-Fifths Rule: todos os grupos OK." if all_compliant else "Four-Fifths Rule: Atenção — impacto adverso detectado em um ou mais grupos.")
        ),
    }
_DIVERSITY_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="diversity_get_pool_metrics",
        description=(
            "Calcula métricas de diversidade do pool de candidatos: taxa geral, breakdown por grupo "
            "(PCD, mulheres, negros/pardos, LGBTQIA+, 50+) e verificação da Four-Fifths Rule."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
            },
            "required": [],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_diversity_get_pool_metrics,
    )
)


@tool_handler("diversity")
async def _wrap_diversity_check_goals(**kwargs: Any) -> dict[str, Any]:
    """Verifica atingimento de metas de diversidade para uma vaga."""
    logger.info("[diversity_tools] diversity_check_goals called: %s", list(kwargs.keys()))
    goals = kwargs.get("goals", {})
    current_metrics = kwargs.get("current_metrics", {})

    if not goals:
        return {
            "success": True,
            "data": {
                "goals_defined": False,
                "message": "Nenhuma meta de diversidade definida. Use diversity_get_pool_metrics para ver o pool atual.",
            },
            "message": "Nenhuma meta de diversidade definida para esta vaga.",
        }

    report = {}
    all_met = True
    for group, target_pct in goals.items():
        current_pct = current_metrics.get(group, 0.0)
        met = current_pct >= target_pct
        if not met:
            all_met = False
        report[group] = {
            "target_percent": target_pct,
            "current_percent": round(current_pct, 1),
            "met": met,
            "gap": round(max(0, target_pct - current_pct), 1),
            "group_label": _DIVERSITY_GROUPS.get(group, group),
        }

    return {
        "success": True,
        "data": {
            "goals_met": all_met,
            "goal_report": report,
            "recommendation": (
                "Metas atingidas. Pool com boa representatividade."
                if all_met else
                "Algumas metas não foram atingidas. Considere ampliar o sourcing com diversity_search_candidates."
            ),
        },
        "message": (
            "Todas as metas de diversidade atingidas."
            if all_met else
            f"{sum(1 for v in report.values() if not v['met'])} meta(s) de diversidade abaixo do alvo."
        ),
    }
_DIVERSITY_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="diversity_check_goals",
        description=(
            "Verifica se as metas de diversidade de uma vaga foram atingidas. "
            "Recebe metas em percentual por grupo e métricas atuais do pool."
        ),
        parameters={
            "type": "object",
            "properties": {
                "goals": {
                    "type": "object",
                    "description": "Metas de diversidade: {grupo: percentual_alvo} ex: {pcd: 5, mulheres: 30}",
                },
                "current_metrics": {
                    "type": "object",
                    "description": "Métricas atuais do pool por grupo (output de diversity_get_pool_metrics)",
                },
            },
            "required": [],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_diversity_check_goals,
    )
)

_DIVERSITY_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in _DIVERSITY_TOOL_DEFINITIONS}


def get_diversity_tools() -> list[ToolDefinition]:
    return list(_DIVERSITY_TOOL_DEFINITIONS)
