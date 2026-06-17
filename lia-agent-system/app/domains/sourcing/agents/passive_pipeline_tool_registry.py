"""
Passive Pipeline Tool Registry — reativação de candidatos frios.

Expõe tools para PassivePipelineAgent:
- passive_search_archived: busca candidatos arquivados/inativos com fit recalculado
- passive_calculate_fit_score: recalcula score de fit para nova vaga
- passive_check_lgpd_ttl: verifica se candidato ainda está dentro do TTL LGPD

Respeita TTL LGPD: candidatos cujo consentimento expirou NÃO são reativados.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler
from app.domains.sourcing.repositories.passive_candidate_repository import PassiveCandidateRepository

logger = logging.getLogger(__name__)

_PASSIVE_TOOL_DEFINITIONS: list[ToolDefinition] = []

# TTL LGPD padrão para candidatos arquivados: 2 anos
LGPD_TTL_DAYS = 730


@tool_handler("passive_pipeline")
async def _wrap_passive_search_archived(**kwargs: Any) -> dict[str, Any]:
    """
    Busca candidatos arquivados ou rejeitados pelo candidato (pipeline passivo).
    Recalcula score de fit e respeita TTL LGPD.
    FairnessGuard: verifica query antes de executar busca.
    """
    logger.info("[passive_tools] passive_search_archived called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    role = kwargs.get("role", "")

    # FairnessGuard: verificar query de busca
    query_str = f"{role} {' '.join(str(s) for s in kwargs.get('skills', []))}"
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_result = _fg.check(query_str)
        if _fg_result.is_blocked:
            return {
                "success": False,
                "data": {},
                "message": _fg_result.educational_message or "Busca bloqueada por critério discriminatório.",
            }
    except Exception as _fg_exc:
        logger.debug("[passive_tools] FairnessGuard check skipped: %s", _fg_exc)
    skills = kwargs.get("skills", [])
    min_fit_score = float(kwargs.get("min_fit_score", 50.0))
    limit = min(int(kwargs.get("limit", 20)), 50)
    page = max(1, int(kwargs.get("page", 1)))
    offset = (page - 1) * limit
    ttl_days = int(kwargs.get("ttl_days", LGPD_TTL_DAYS))

    # LGPD: calcular data limite para reativação
    lgpd_cutoff = datetime.utcnow() - timedelta(days=ttl_days)

    conditions = [
        "status IN ('archived', 'rejected_by_candidate', 'passive')",
        "is_active = false",
        "(updated_at IS NULL OR updated_at >= :lgpd_cutoff)",
    ]
    params: dict[str, Any] = {
        "lim": limit,
        "off": offset,
        "lgpd_cutoff": lgpd_cutoff,
    }

    if role:
        conditions.append("current_title ILIKE :role_pattern")
        params["role_pattern"] = f"%{role}%"

    if skills and isinstance(skills, list) and len(skills) > 0:
        conditions.append("technical_skills && :skills_arr")
        params["skills_arr"] = skills

    if min_fit_score > 0:
        conditions.append("(lia_score IS NULL OR lia_score >= :min_fit)")
        params["min_fit"] = min_fit_score

    where_clause = " AND ".join(conditions)
    query = f"""
        SELECT id, name, email, current_title, current_company,
               seniority_level, years_of_experience,
               technical_skills, soft_skills,
               location_city, location_state, location_country,
               status, lia_score, updated_at, created_at
        FROM candidates
        WHERE {where_clause}
        ORDER BY lia_score DESC NULLS LAST, updated_at DESC NULLS LAST
        LIMIT :lim OFFSET :off
    """
    count_query = f"SELECT COUNT(*) FROM candidates WHERE {where_clause}"

    # ADR-001-EXEMPT: LGPD TTL mandatory filter + dynamic skills array match (&&) + role ILIKE
    # — dynamic conditions array prevents migration to typed repo method without losing LGPD gate;
    # refactor pending compliance review (ADR-001 Wave C-2 Agent D)
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(text(count_query), params)
        total = count_result.scalar() or 0
        result = await session.execute(text(query), params)
        rows = result.mappings().all()

    candidates = []
    for row in rows:
        last_contact = row["updated_at"]
        days_since_contact = (
            (datetime.utcnow() - last_contact).days
            if last_contact else None
        )
        lgpd_ok = (
            last_contact is None or last_contact >= lgpd_cutoff
        )

        if not lgpd_ok:
            continue

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
            "days_since_last_contact": days_since_contact,
            "lgpd_compliant": True,
            "lgpd_expiry_date": (
                (last_contact + timedelta(days=ttl_days)).isoformat()
                if last_contact else None
            ),
        })

    return {
        "success": True,
        "data": {
            "candidates": candidates,
            "total_results": total,
            "page": page,
            "limit": limit,
            "lgpd_info": {
                "ttl_days": ttl_days,
                "cutoff_date": lgpd_cutoff.isoformat(),
                "note": "Apenas candidatos dentro do TTL LGPD são retornados.",
            },
        },
        "message": (
            f"{len(candidates)} candidato(s) no pipeline passivo dentro do TTL LGPD ({ttl_days} dias). "
            f"Total encontrado: {total}."
        ),
    }
_PASSIVE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="passive_search_archived",
        description=(
            "Busca candidatos arquivados (status archived/rejected_by_candidate/passive) "
            "para reengajamento. Filtra por role e skills. "
            "Respeita TTL LGPD — não retorna candidatos com consentimento expirado (padrão: 2 anos). "
            "Ideal para reanimar candidatos de processos anteriores para novas vagas."
        ),
        parameters={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Cargo/função buscado"},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills técnicas",
                },
                "min_fit_score": {
                    "type": "number",
                    "description": "Score mínimo de fit LIA (0-100, padrão: 50)",
                    "default": 50.0,
                },
                "limit": {"type": "integer", "description": "Máximo de resultados (padrão: 20)", "default": 20},
                "page": {"type": "integer", "description": "Página (padrão: 1)", "default": 1},
                "ttl_days": {
                    "type": "integer",
                    "description": "TTL LGPD em dias (padrão: 730 = 2 anos)",
                    "default": 730,
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_passive_search_archived,
    )
)


@tool_handler("passive_pipeline")
async def _wrap_passive_calculate_fit_score(**kwargs: Any) -> dict[str, Any]:
    """Recalcula score de fit de candidato passivo para uma nova vaga."""
    logger.info("[passive_tools] passive_calculate_fit_score called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    candidate_id = kwargs.get("candidate_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate

    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'candidate_id' é obrigatório."}
    if not vacancy_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'vacancy_id' é obrigatório."}

    # ADR-001-EXEMPT: cross-domain read (candidates + job_vacancies) for fit score computation
    # — ContextAggregatorService pattern; complex cross-repo join pending LGPD-aware refactor sprint
    # (ADR-001 Wave C-2 Agent D)
    async with AsyncSessionLocal() as session:
        c_res = await session.execute(
            text("""
                SELECT id, name, technical_skills, soft_skills, years_of_experience,
                       seniority_level, current_title, status, updated_at
                FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = c_res.mappings().first()

        # ADR-001-EXEMPT: cross-domain read (candidates + job_vacancies) for fit score computation
        # — ContextAggregatorService pattern; complex cross-repo join pending LGPD-aware refactor sprint
        v_res = await session.execute(
            text("""
                SELECT id, title, requirements, seniority_level
                FROM job_vacancies
                WHERE id = :vid AND company_id = :company_id
            """),
            {"vid": vacancy_id, "company_id": company_id},
        )
        vacancy = v_res.mappings().first()

    if not candidate:
        return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' não encontrado."}
    if not vacancy:
        return {"success": False, "data": {}, "message": f"Vaga '{vacancy_id}' não encontrada."}

    # LGPD: verificar TTL
    last_update = candidate["updated_at"]
    lgpd_cutoff = datetime.utcnow() - timedelta(days=LGPD_TTL_DAYS)
    if last_update and last_update < lgpd_cutoff:
        return {
            "success": False,
            "data": {"lgpd_expired": True},
            "message": (
                f"Candidato fora do TTL LGPD ({LGPD_TTL_DAYS} dias). "
                "Reativação bloqueada por compliance. Contate o DPO para esclarecimentos."
            ),
        }

    candidate_skills = set(s.lower() for s in (candidate["technical_skills"] or []))
    requirements = set(r.lower() for r in (vacancy["requirements"] or []))

    if requirements:
        matched = candidate_skills & requirements
        skill_score = len(matched) / len(requirements) * 100
    else:
        matched = set()
        skill_score = 50.0

    seniority_match = 100.0 if (
        candidate["seniority_level"] and vacancy["seniority_level"] and
        candidate["seniority_level"].lower() == vacancy["seniority_level"].lower()
    ) else 50.0

    exp_score = min(100.0, (candidate["years_of_experience"] or 0) * 10)

    fit_score = round(skill_score * 0.5 + seniority_match * 0.25 + exp_score * 0.25, 2)

    days_since = (datetime.utcnow() - last_update).days if last_update else None
    recency_penalty = 0
    if days_since and days_since > 365:
        recency_penalty = min(10, (days_since - 365) / 36.5)
        fit_score = max(0, fit_score - recency_penalty)

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate["id"]),
            "candidate_name": candidate["name"],
            "vacancy_id": str(vacancy["id"]),
            "vacancy_title": vacancy["title"],
            "fit_score": round(fit_score, 2),
            "dimensions": {
                "skill_match": round(skill_score, 2),
                "seniority_match": seniority_match,
                "experience_score": round(exp_score, 2),
                "recency_penalty": round(recency_penalty, 2),
            },
            "matched_skills": list(matched),
            "missing_skills": list(requirements - candidate_skills),
            "days_since_last_activity": days_since,
            "lgpd_compliant": True,
            "reengagement_recommended": fit_score >= 60.0,
        },
        "message": (
            f"Fit score de '{candidate['name']}' para '{vacancy['title']}': "
            f"{fit_score:.1f}/100. "
            + ("Recomendado para reengajamento." if fit_score >= 60.0 else "Score abaixo do limiar de reengajamento (60).")
        ),
    }
_PASSIVE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="passive_calculate_fit_score",
        description=(
            "Recalcula o score de fit de um candidato passivo (arquivado) para uma nova vaga. "
            "Aplica penalidade de recência e verifica TTL LGPD. "
            "Retorna se o candidato é recomendado para reengajamento."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "vacancy_id": {"type": "string", "description": "ID da nova vaga"},
            },
            "required": ["candidate_id", "vacancy_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_passive_calculate_fit_score,
    )
)


@tool_handler("passive_pipeline")
async def _wrap_passive_check_lgpd_ttl(**kwargs: Any) -> dict[str, Any]:
    """Verifica status LGPD de um candidato para reengajamento."""
    logger.info("[passive_tools] passive_check_lgpd_ttl called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: LGPD TTL gate
    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'candidate_id' é obrigatório."}

    _lgpd_cutoff_date = (datetime.utcnow() - timedelta(days=LGPD_TTL_DAYS)).date()
    async with AsyncSessionLocal() as session:
        repo = PassiveCandidateRepository(db=session)
        candidate = await repo.get_with_lgpd_check(candidate_id, company_id, _lgpd_cutoff_date)

    if not candidate:
        return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' não encontrado."}

    last_update = candidate["updated_at"] or candidate["created_at"]
    lgpd_cutoff = datetime.utcnow() - timedelta(days=LGPD_TTL_DAYS)
    expiry_date = (last_update + timedelta(days=LGPD_TTL_DAYS)) if last_update else None

    lgpd_ok = (last_update is None or last_update >= lgpd_cutoff)
    days_remaining = (
        (expiry_date - datetime.utcnow()).days
        if expiry_date else None
    )

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate["id"]),
            "candidate_name": candidate["name"],
            "lgpd_compliant": lgpd_ok,
            "ttl_days": LGPD_TTL_DAYS,
            "last_activity": last_update.isoformat() if last_update else None,
            "expiry_date": expiry_date.isoformat() if expiry_date else None,
            "days_remaining": days_remaining,
            "can_reengage": lgpd_ok,
            "action_if_expired": "Solicitar novo consentimento ou excluir dados via LGPD cleanup.",
        },
        "message": (
            f"LGPD OK — {candidate['name']} pode ser reengajado. "
            f"{days_remaining} dias restantes até expiração."
            if lgpd_ok else
            f"LGPD EXPIRADO — {candidate['name']} não pode ser reengajado sem novo consentimento."
        ),
    }
_PASSIVE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="passive_check_lgpd_ttl",
        description=(
            "Verifica o status LGPD de um candidato para reengajamento: "
            "se o TTL de consentimento está dentro do prazo (padrão: 2 anos) e "
            "quantos dias restam até expiração."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_passive_check_lgpd_ttl,
    )
)

_PASSIVE_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in _PASSIVE_TOOL_DEFINITIONS}


def get_passive_pipeline_tools() -> list[ToolDefinition]:
    return list(_PASSIVE_TOOL_DEFINITIONS)
