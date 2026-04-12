"""
Internal Mobility / Talent Marketplace — Match internal employees to open
positions considering skill adjacencies and development potential.

Reduces external hiring costs by 30-50% by surfacing internal candidates
who are qualified or near-qualified for open roles.
"""
import logging
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


@tool_handler("talent_intelligence", module="internal_mobility")
async def match_internal_candidates(
    job_id: str | None = None,
    required_skills: list[str] | None = None,
    job_title: str | None = None,
    seniority: str | None = None,
    department: str | None = None,
    limit: int = 20,
    **kwargs,
) -> dict[str, Any]:
    """
    Match internal employees/candidates to a job opening.

    Considers:
    - Direct skill matches
    - Adjacent/transferable skills (via ontology)
    - Development potential (skills gap is small and learnable)
    - Current seniority vs required seniority
    """
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text

    from app.domains.talent_intelligence.services.skills_ontology_engine import skills_ontology

    company_id = kwargs.get("company_id", "")

    r_skills: list[str] = list(required_skills or [])
    job_info: dict[str, Any] = {}

    if job_id:
        try:
            async with AsyncSessionLocal() as session:
                row = await session.execute(
                    text("""
                        SELECT title, seniority_level, department,
                               technical_requirements, required_skills
                        FROM job_vacancies
                        WHERE id = :jid AND company_id = :cid
                    """),
                    {"jid": job_id, "cid": company_id},
                )
                data = row.mappings().first()
                if data:
                    job_info = {
                        "title": data.get("title"),
                        "seniority": data.get("seniority_level"),
                        "department": data.get("department"),
                    }
                    if not r_skills:
                        reqs = data.get("technical_requirements") or []
                        if isinstance(reqs, list):
                            r_skills = [
                                r.get("technology", "")
                                for r in reqs
                                if isinstance(r, dict) and r.get("technology")
                            ]
                        if not r_skills:
                            r_skills = list(data.get("required_skills") or [])
                    if not job_title:
                        job_title = data.get("title")
                    if not seniority:
                        seniority = data.get("seniority_level")
                    if not department:
                        department = data.get("department")
        except Exception as e:
            logger.warning(f"Could not load job details: {e}")

    if not r_skills and not job_title:
        return {
            "success": False,
            "data": {},
            "message": "Forneça job_id ou required_skills/job_title para buscar candidatos internos.",
        }

    matches = []
    try:
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text("""
                    SELECT id, name, email, current_title, current_company,
                           seniority_level, years_of_experience,
                           technical_skills, soft_skills,
                           location_city, location_state,
                           lia_score, skills_match_percentage
                    FROM candidates
                    WHERE company_id = :cid
                      AND is_active = true
                      AND source IN ('internal', 'employee', 'colaborador')
                    ORDER BY lia_score DESC NULLS LAST
                    LIMIT :lim
                """),
                {"cid": company_id, "lim": limit * 3},
            )
            internal_candidates = rows.mappings().all()

            if not internal_candidates:
                return {
                    "success": True,
                    "data": {
                        "job_id": job_id,
                        "job_title": job_title,
                        "required_skills": r_skills,
                        "total_matches": 0,
                        "ready_now": 0,
                        "ready_with_development": 0,
                        "matches": [],
                    },
                    "message": (
                        "Nenhum colaborador interno encontrado (source: internal/employee/colaborador). "
                        "Para incluir candidatos externos, use a ferramenta 'search_candidates'."
                    ),
                }

            for candidate in internal_candidates:
                c_skills = list(candidate.get("technical_skills") or [])
                if r_skills:
                    gap_analysis = skills_ontology.analyze_skill_gaps(c_skills, r_skills)
                else:
                    gap_analysis = {
                        "match_percentage": 0,
                        "effective_match_percentage": 0,
                        "matched_skills": [],
                        "missing_skills": [],
                        "adjacency_matches": [],
                        "gap_severity": "unknown",
                    }

                readiness_score = _calculate_readiness(
                    gap_analysis,
                    candidate.get("seniority_level"),
                    seniority,
                    candidate.get("years_of_experience"),
                )

                if readiness_score >= 30:
                    matches.append({
                        "candidate_id": str(candidate["id"]),
                        "name": candidate["name"],
                        "current_title": candidate["current_title"],
                        "seniority_level": candidate["seniority_level"],
                        "years_of_experience": candidate["years_of_experience"],
                        "location": f"{candidate.get('location_city') or ''}, {candidate.get('location_state') or ''}".strip(", "),
                        "readiness_score": readiness_score,
                        "skill_match_percentage": gap_analysis["match_percentage"],
                        "effective_match_percentage": gap_analysis["effective_match_percentage"],
                        "matched_skills": gap_analysis["matched_skills"],
                        "missing_skills": gap_analysis["missing_skills"],
                        "adjacency_matches": gap_analysis["adjacency_matches"][:3],
                        "gap_severity": gap_analysis["gap_severity"],
                        "readiness_category": (
                            "ready_now" if readiness_score >= 80
                            else "ready_with_development" if readiness_score >= 60
                            else "future_potential" if readiness_score >= 40
                            else "long_term"
                        ),
                    })

    except Exception as e:
        logger.error(f"Error matching internal candidates: {e}", exc_info=True)
        return {
            "success": False,
            "data": {},
            "message": f"Erro ao buscar candidatos internos: {str(e)}",
        }

    matches.sort(key=lambda x: x["readiness_score"], reverse=True)
    matches = matches[:limit]

    ready_now = sum(1 for m in matches if m["readiness_category"] == "ready_now")
    ready_dev = sum(1 for m in matches if m["readiness_category"] == "ready_with_development")

    return {
        "success": True,
        "data": {
            "job_id": job_id,
            "job_title": job_title,
            "required_skills": r_skills,
            "total_matches": len(matches),
            "ready_now": ready_now,
            "ready_with_development": ready_dev,
            "matches": matches,
        },
        "message": (
            f"Encontrados {len(matches)} candidatos internos para '{job_title or 'vaga'}'. "
            f"{ready_now} prontos agora, {ready_dev} com desenvolvimento rápido."
        ),
    }


_SENIORITY_ORDER = {
    "estagiário": 0, "estagio": 0, "intern": 0,
    "júnior": 1, "junior": 1,
    "pleno": 2, "mid": 2, "mid-level": 2,
    "sênior": 3, "senior": 3,
    "especialista": 4, "staff": 4, "principal": 4,
    "coordenador": 5, "coordinator": 5,
    "gerente": 6, "manager": 6,
    "diretor": 7, "director": 7,
    "vp": 8, "vice-presidente": 8,
    "c-level": 9, "cto": 9, "ceo": 9, "cfo": 9,
}


def _calculate_readiness(
    gap_analysis: dict[str, Any],
    candidate_seniority: str | None,
    required_seniority: str | None,
    years_exp: int | None,
) -> float:
    base = gap_analysis.get("effective_match_percentage", 0)

    c_level = _SENIORITY_ORDER.get((candidate_seniority or "").lower(), 2)
    r_level = _SENIORITY_ORDER.get((required_seniority or "").lower(), 2)
    seniority_delta = c_level - r_level

    seniority_bonus = 0
    if seniority_delta >= 0:
        seniority_bonus = 10
    elif seniority_delta == -1:
        seniority_bonus = 0
    else:
        seniority_bonus = -15

    exp_bonus = 0
    if years_exp and years_exp >= 5:
        exp_bonus = 5
    elif years_exp and years_exp >= 3:
        exp_bonus = 2

    readiness = base + seniority_bonus + exp_bonus
    return round(max(0, min(100, readiness)), 1)
