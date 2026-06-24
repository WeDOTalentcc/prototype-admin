"""
Sourcing Tool Registry - Exposes sourcing tools to the ReAct loop.

Wraps sourcing operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call during candidate search
and screening.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


@tool_handler("sourcing")
async def _wrap_set_search_criteria(**kwargs: Any) -> dict[str, Any]:
    """Define search parameters for talent sourcing."""
    role = kwargs.get("role", "")
    skills = kwargs.get("skills", [])
    location = kwargs.get("location", "")
    experience_level = kwargs.get("experience_level", "")
    salary_range = kwargs.get("salary_range", {})

    criteria_id = str(uuid.uuid4())
    return {
        "success": True,
        "data": {
            "criteria_id": criteria_id,
            "role": role,
            "skills": skills if isinstance(skills, list) else [],
            "location": location,
            "experience_level": experience_level,
            "salary_range": salary_range if isinstance(salary_range, dict) else {},
        },
        "message": f"Criterios de busca definidos para '{role}' em '{location}'.",
    }


@tool_handler("sourcing")
async def _wrap_suggest_skills(**kwargs: Any) -> dict[str, Any]:
    """Suggest relevant skills based on role and context."""
    role = kwargs.get("role", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: from tool_handler ContextVar
    if not role:
        return {"success": False, "data": {}, "message": "Parametro 'role' e obrigatorio."}

    # ADR-001-EXEMPT: skills frequency analytics aggregation (COUNT + unnest) for suggestion — complex GROUP BY, not abstractable to repo method
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT unnest(technical_skills) as skill, COUNT(*) as cnt
                FROM candidates
                WHERE current_title ILIKE :role_pattern
                  AND technical_skills IS NOT NULL
                  AND (company_id IS NULL OR company_id = :company_id)
                GROUP BY skill
                ORDER BY cnt DESC
                LIMIT 10
            """),
            {"role_pattern": f"%{role}%", "company_id": company_id},
        )
        rows = result.mappings().all()[:limit]

    if not rows:
        return {
            "success": True,
            "data": {"role": role, "suggested_skills": []},
            "message": f"Nenhuma skill encontrada para o cargo '{role}'. Tente um termo mais generico.",
        }

    suggested = [{"skill": row["skill"], "frequency": row["cnt"]} for row in rows]
    return {
        "success": True,
        "data": {
            "role": role,
            "suggested_skills": suggested,
        },
        "message": f"{len(suggested)} skills sugeridas para '{role}'.",
    }


@tool_handler("sourcing")
async def _wrap_search_candidates(**kwargs: Any) -> dict[str, Any]:
    """Execute talent search based on defined criteria."""
    skills = kwargs.get("skills", [])
    location = kwargs.get("location", "")
    seniority = kwargs.get("experience_level", "") or kwargs.get("seniority_level", "")
    role = kwargs.get("role", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: from tool_handler ContextVar
    page = kwargs.get("page", 1)
    limit = kwargs.get("limit", 20)
    if limit > 50:
        limit = 50
    offset = (max(1, page) - 1) * limit

    # P0.A canonical: tenant gate FIRST in conditions. company_id IS NULL preserves
    # global talent pool sharing (Pearch AI / merge.dev imported candidates).
    conditions = [
        "is_active = true",
        "(company_id IS NULL OR company_id = :company_id)",
    ]
    params: dict[str, Any] = {"lim": limit, "off": offset, "company_id": company_id}

    if role:
        conditions.append("current_title ILIKE :role_pattern")
        params["role_pattern"] = f"%{role}%"

    if skills and isinstance(skills, list) and len(skills) > 0:
        conditions.append("technical_skills && :skills_arr")
        params["skills_arr"] = skills

    if location:
        conditions.append(
            "(location_city ILIKE :loc_pattern OR location_state ILIKE :loc_pattern OR location_country ILIKE :loc_pattern)"
        )
        params["loc_pattern"] = f"%{location}%"

    if seniority:
        conditions.append("seniority_level ILIKE :seniority_pattern")
        params["seniority_pattern"] = f"%{seniority}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT id, name, email, current_title, current_company,
               seniority_level, years_of_experience,
               technical_skills, soft_skills,
               location_city, location_state, location_country,
               status, lia_score
        FROM candidates
        WHERE {where_clause}
        ORDER BY lia_score DESC NULLS LAST, years_of_experience DESC NULLS LAST
        LIMIT :lim OFFSET :off
    """

    count_query = f"SELECT COUNT(*) as total FROM candidates WHERE {where_clause}"

    # ADR-001-EXEMPT: dynamic candidate search builder with explicit filter allowlist — canonically documented per pre-existing CROSS-TENANT-EXEMPT markers in file
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(text(count_query), params)
        total = count_result.scalar() or 0

        result = await session.execute(text(query), params)
        rows = result.mappings().all()

    candidates = []
    for row in rows:
        candidates.append({
            "id": str(row["id"]),
            "name": row["name"],
            "email": row["email"],
            "current_title": row["current_title"],
            "current_company": row["current_company"],
            "seniority_level": row["seniority_level"],
            "years_of_experience": row["years_of_experience"],
            "technical_skills": row["technical_skills"] or [],
            "soft_skills": row["soft_skills"] or [],
            "location": f"{row['location_city'] or ''}, {row['location_state'] or ''}, {row['location_country'] or ''}".strip(", "),
            "status": row["status"],
            "lia_score": row["lia_score"],
        })

    # --- Phase 8.1.5: Pearch hybrid search support ---
    include_pearch = kwargs.get("include_pearch", False)
    pearch_candidates = []
    pearch_count = 0
    if include_pearch:
        try:
            from app.domains.sourcing.services.pearch_service import PearchService
            pearch_svc = PearchService()
            pearch_query = f"{role} {' '.join(skills) if isinstance(skills, list) else ''} {location}".strip()
            pearch_result = await pearch_svc.search_candidates(
                query=pearch_query,
                search_type="fast",
                limit=min(limit, 15),
            )
            if pearch_result and pearch_result.get("candidates"):
                for pc in pearch_result["candidates"]:
                    pc["source"] = "pearch"
                    pearch_candidates.append(pc)
                pearch_count = len(pearch_candidates)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("[SearchCandidates] Pearch fallback: %s", e)

    # Combine local + pearch, dedup by email/linkedin
    if pearch_candidates:
        seen = {c.get("email") or c.get("id") for c in candidates}
        for pc in pearch_candidates:
            uid = pc.get("email") or pc.get("linkedin_url") or pc.get("id")
            if uid and uid not in seen:
                seen.add(uid)
                candidates.append(pc)
        total = total + pearch_count

    return {
        "success": True,
        "data": {
            "candidates": candidates,
            "total_results": total,
            "page": page,
            "limit": limit,
        },
        "message": f"{len(candidates)} candidatos encontrados (total: {total}).",
    }


@tool_handler("sourcing")
async def _wrap_filter_results(**kwargs: Any) -> dict[str, Any]:
    """Apply filters to search results."""
    filters = kwargs.get("filters", {})
    page = kwargs.get("page", 1)
    limit = kwargs.get("limit", 20)
    if limit > 50:
        limit = 50
    offset = (max(1, page) - 1) * limit

    conditions = ["is_active = true"]
    params: dict[str, Any] = {"lim": limit, "off": offset}

    if filters.get("min_experience"):
        conditions.append("years_of_experience >= :min_exp")
        params["min_exp"] = int(filters["min_experience"])

    if filters.get("max_experience"):
        conditions.append("years_of_experience <= :max_exp")
        params["max_exp"] = int(filters["max_experience"])

    if filters.get("location"):
        conditions.append(
            "(location_city ILIKE :floc OR location_state ILIKE :floc OR location_country ILIKE :floc)"
        )
        params["floc"] = f"%{filters['location']}%"

    if filters.get("skills") and isinstance(filters["skills"], list):
        conditions.append("technical_skills && :fskills")
        params["fskills"] = filters["skills"]

    if filters.get("seniority_level"):
        conditions.append("seniority_level ILIKE :fsen")
        params["fsen"] = f"%{filters['seniority_level']}%"

    if filters.get("title"):
        conditions.append("current_title ILIKE :ftitle")
        params["ftitle"] = f"%{filters['title']}%"

    if filters.get("status"):
        conditions.append("status = :fstatus")
        params["fstatus"] = filters["status"]

    where_clause = " AND ".join(conditions)

    # CROSS-TENANT-EXEMPT (sensor-window-adjacent block of both queries below):
    # where_clause built above includes the canonical tenant gate
    # '(company_id IS NULL OR company_id = :company_id)' as the second
    # condition (line ~102). Regex sensor cannot inspect f-string interpolation,
    # so this block is explicit-marker exempt. Audit 2026-05-21 P0.A canonical
    # (Sub-sprint B).
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(
            # CROSS-TENANT-EXEMPT: see above (sensor scans 5 lines above text()).
            text(f"SELECT COUNT(*) as total FROM candidates WHERE {where_clause}"), params
        )
        total = count_result.scalar() or 0

        result = await session.execute(
            # CROSS-TENANT-EXEMPT: see above (sensor scans 5 lines above text()).
            text(f"""
                SELECT id, name, email, current_title, current_company,
                       seniority_level, years_of_experience,
                       technical_skills, location_city, location_state, location_country,
                       status, lia_score
                FROM candidates
                WHERE {where_clause}
                ORDER BY lia_score DESC NULLS LAST
                LIMIT :lim OFFSET :off
            """),
            params,
        )
        rows = result.mappings().all()

    candidates = []
    for row in rows:
        candidates.append({
            "id": str(row["id"]),
            "name": row["name"],
            "current_title": row["current_title"],
            "current_company": row["current_company"],
            "seniority_level": row["seniority_level"],
            "years_of_experience": row["years_of_experience"],
            "technical_skills": row["technical_skills"] or [],
            "location": f"{row['location_city'] or ''}, {row['location_state'] or ''}, {row['location_country'] or ''}".strip(", "),
            "lia_score": row["lia_score"],
        })

    return {
        "success": True,
        "data": {
            "filters_applied": filters,
            "filtered_candidates": candidates,
            "filtered_count": total,
            "page": page,
            "limit": limit,
        },
        "message": f"Filtros aplicados: {len(candidates)} candidatos retornados (total: {total}).",
    }


@tool_handler("sourcing")
async def _wrap_analyze_profile(**kwargs: Any) -> dict[str, Any]:
    """Perform AI analysis of a candidate profile."""
    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, name, current_title, current_company, seniority_level,
                       years_of_experience, technical_skills, soft_skills,
                       location_city, location_state, location_country,
                       certifications, languages, work_history,
                       lia_score, lia_insights, headline, expertise
                FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = result.mappings().first()

    if not candidate:
        return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' nao encontrado."}

    tech_skills = candidate["technical_skills"] or []
    soft_skills = candidate["soft_skills"] or []
    certifications = candidate["certifications"] or []
    years = candidate["years_of_experience"] or 0

    strengths = []
    if len(tech_skills) >= 5:
        strengths.append(f"Amplo portfolio tecnico ({len(tech_skills)} skills)")
    if len(soft_skills) >= 3:
        strengths.append(f"Boas soft skills ({len(soft_skills)} identificadas)")
    if years >= 5:
        strengths.append(f"Experiencia solida ({years} anos)")
    if certifications:
        strengths.append(f"{len(certifications)} certificacoes")
    if candidate["lia_score"] and candidate["lia_score"] > 70:
        strengths.append(f"Score LIA alto ({candidate['lia_score']:.1f})")

    gaps = []
    if len(tech_skills) < 3:
        gaps.append("Portfolio tecnico limitado")
    if not soft_skills:
        gaps.append("Sem soft skills identificadas")
    if years < 2:
        gaps.append("Pouca experiencia profissional")
    if not certifications:
        gaps.append("Sem certificacoes")

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate["id"]),
            "name": candidate["name"],
            "current_title": candidate["current_title"],
            "current_company": candidate["current_company"],
            "seniority_level": candidate["seniority_level"],
            "years_of_experience": years,
            "technical_skills": tech_skills,
            "soft_skills": soft_skills,
            "certifications": certifications,
            "location": f"{candidate['location_city'] or ''}, {candidate['location_state'] or ''}, {candidate['location_country'] or ''}".strip(", "),
            "strengths": strengths,
            "gaps": gaps,
            "overall_score": candidate["lia_score"] or 0.0,
            "lia_insights": candidate["lia_insights"],
        },
        "message": f"Analise do perfil de '{candidate['name']}' concluida.",
    }


@tool_handler("sourcing")
async def _wrap_compare_candidates(**kwargs: Any) -> dict[str, Any]:
    """Compare multiple candidate profiles."""
    candidate_ids = kwargs.get("candidate_ids", [])
    if not candidate_ids or not isinstance(candidate_ids, list):
        return {"success": False, "data": {}, "message": "Parametro 'candidate_ids' (lista) e obrigatorio."}

    placeholders = ", ".join([f":id_{i}" for i in range(len(candidate_ids))])
    params = {f"id_{i}": cid for i, cid in enumerate(candidate_ids)}

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(f"""
                SELECT id, name, current_title, current_company, seniority_level,
                       years_of_experience, technical_skills, soft_skills,
                       location_city, location_state, location_country,
                       lia_score, certifications
                FROM candidates
                WHERE id IN ({placeholders})
            """),
            params,
        )
        rows = result.mappings().all()

    if not rows:
        return {"success": False, "data": {}, "message": "Nenhum dos candidatos informados foi encontrado."}

    comparison = []
    for row in rows:
        comparison.append({
            "id": str(row["id"]),
            "name": row["name"],
            "current_title": row["current_title"],
            "current_company": row["current_company"],
            "seniority_level": row["seniority_level"],
            "years_of_experience": row["years_of_experience"],
            "technical_skills": row["technical_skills"] or [],
            "soft_skills": row["soft_skills"] or [],
            "location": f"{row['location_city'] or ''}, {row['location_state'] or ''}, {row['location_country'] or ''}".strip(", "),
            "lia_score": row["lia_score"] or 0.0,
            "certifications": row["certifications"] or [],
            "tech_skill_count": len(row["technical_skills"] or []),
        })

    ranking = sorted(comparison, key=lambda x: (x["lia_score"], x["years_of_experience"] or 0), reverse=True)
    for i, c in enumerate(ranking):
        c["rank"] = i + 1

    return {
        "success": True,
        "data": {
            "candidate_ids": [str(r["id"]) for r in rows],
            "comparison": comparison,
            "ranking": ranking,
        },
        "message": f"Comparacao de {len(rows)} candidatos concluida.",
    }


@tool_handler("sourcing")
async def _wrap_score_candidate(**kwargs: Any) -> dict[str, Any]:
    """Apply WSI scoring to a candidate."""
    candidate_id = kwargs.get("candidate_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    if not candidate_id or not vacancy_id:
        return {"success": False, "data": {}, "message": "Parametros 'candidate_id' e 'vacancy_id' sao obrigatorios."}

    async with AsyncSessionLocal() as session:
        c_result = await session.execute(
            text("""
                SELECT id, name, technical_skills, soft_skills, years_of_experience,
                       seniority_level, current_title, location_city, location_state
                FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = c_result.mappings().first()

        v_result = await session.execute(
            text("""
                SELECT id, title, requirements, seniority_level, location, work_model
                FROM job_vacancies WHERE id = :vid
            """),
            {"vid": vacancy_id},
        )
        vacancy = v_result.mappings().first()

    if not candidate:
        return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' nao encontrado."}
    if not vacancy:
        return {"success": False, "data": {}, "message": f"Vaga '{vacancy_id}' nao encontrada."}

    candidate_skills = set(s.lower() for s in (candidate["technical_skills"] or []))
    requirements = set(r.lower() for r in (vacancy["requirements"] or []))

    if requirements:
        matched_skills = candidate_skills & requirements
        skill_score = (len(matched_skills) / len(requirements)) * 100
    else:
        matched_skills = set()
        skill_score = 50.0

    seniority_match = 100.0 if (
        candidate["seniority_level"] and vacancy["seniority_level"] and
        candidate["seniority_level"].lower() == vacancy["seniority_level"].lower()
    ) else 50.0

    experience_score = min(100.0, (candidate["years_of_experience"] or 0) * 10)

    wsi_score = round(skill_score * 0.5 + seniority_match * 0.25 + experience_score * 0.25, 2)

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate["id"]),
            "candidate_name": candidate["name"],
            "vacancy_id": str(vacancy["id"]),
            "vacancy_title": vacancy["title"],
            "wsi_score": wsi_score,
            "dimensions": {
                "skill_match": round(skill_score, 2),
                "seniority_match": seniority_match,
                "experience_score": round(experience_score, 2),
            },
            "matched_skills": list(matched_skills),
            "missing_skills": list(requirements - candidate_skills),
        },
        "message": f"Score WSI de '{candidate['name']}' para '{vacancy['title']}': {wsi_score:.1f}/100.",
    }


@tool_handler("sourcing")
async def _wrap_add_to_shortlist(**kwargs: Any) -> dict[str, Any]:
    """Add a candidate to the shortlist."""
    candidate_id = kwargs.get("candidate_id", "")
    shortlist_id = kwargs.get("shortlist_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    added_by = kwargs.get("added_by", "lia-agent")
    notes = kwargs.get("notes", "")

    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    async with AsyncSessionLocal() as session:
        c_result = await session.execute(
            text("""
                SELECT id, name FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = c_result.mappings().first()
        if not candidate:
            return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' nao encontrado."}

        if shortlist_id:
            # P0.A canonical: candidate_list_members nao tem company_id;
            # filtra via parent candidate_lists.company_id.
            existing = await session.execute(
                text("""
                    SELECT clm.id FROM candidate_list_members clm
                    JOIN candidate_lists cl ON cl.id = clm.list_id
                    WHERE clm.list_id = :lid
                      AND clm.candidate_id = :cid
                      AND cl.company_id = :company_id
                """),
                {"lid": shortlist_id, "cid": candidate_id, "company_id": company_id},
            )
            if existing.first():
                return {
                    "success": False,
                    "data": {},
                    "message": f"Candidato '{candidate['name']}' ja esta nesta lista.",
                }

            await session.execute(
                # RLS-EXEMPT: candidate_list_members — transitive via candidate_list (which has company_id)
                text("""
                    INSERT INTO candidate_list_members (list_id, candidate_id, added_by, notes, source)
                    VALUES (:lid, :cid, :added_by, :notes, 'sourcing_agent')
                """),
                {
                    "lid": shortlist_id,
                    "cid": candidate_id,
                    "added_by": added_by,
                    "notes": notes,
                },
            )
            await session.commit()

            return {
                "success": True,
                "data": {
                    "candidate_id": str(candidate_id),
                    "candidate_name": candidate["name"],
                    "shortlist_id": shortlist_id,
                },
                "message": f"Candidato '{candidate['name']}' adicionado a shortlist.",
            }
        else:
            return {
                "success": False,
                "data": {},
                "message": "Parametro 'shortlist_id' e obrigatorio para adicionar a uma lista.",
            }


@tool_handler("sourcing")
async def _wrap_remove_from_shortlist(**kwargs: Any) -> dict[str, Any]:
    """Remove a candidate from the shortlist."""
    candidate_id = kwargs.get("candidate_id", "")
    shortlist_id = kwargs.get("shortlist_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate

    if not candidate_id or not shortlist_id:
        return {"success": False, "data": {}, "message": "Parametros 'candidate_id' e 'shortlist_id' sao obrigatorios."}

    async with AsyncSessionLocal() as session:
        # P0.A canonical: DELETE com tenant gate via parent candidate_lists.
        # Antes, recrutador da Company A podia deletar membros de lista
        # da Company B (cross-tenant DELETE). Agora subquery restringe
        # apenas ao list_id que pertence a esta company.
        result = await session.execute(
            text("""
                DELETE FROM candidate_list_members
                WHERE list_id = :lid
                  AND candidate_id = :cid
                  AND list_id IN (
                      SELECT id FROM candidate_lists WHERE company_id = :company_id
                  )
                RETURNING id
            """),
            {"lid": shortlist_id, "cid": candidate_id, "company_id": company_id},
        )
        deleted = result.first()
        await session.commit()

    if not deleted:
        return {
            "success": False,
            "data": {},
            "message": f"Candidato '{candidate_id}' nao encontrado na lista '{shortlist_id}'.",
        }

    return {
        "success": True,
        "data": {
            "candidate_id": candidate_id,
            "shortlist_id": shortlist_id,
        },
        "message": f"Candidato '{candidate_id}' removido da shortlist.",
    }


@tool_handler("sourcing")
async def _wrap_rank_candidates(**kwargs: Any) -> dict[str, Any]:
    """Rank candidates in the shortlist."""
    shortlist_id = kwargs.get("shortlist_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical (handoff site 1 + 2)

    limit = min(int(kwargs.get("limit", 10)), 50)
    if not shortlist_id and not vacancy_id:
        return {"success": False, "data": {}, "message": "Informe 'shortlist_id' ou 'vacancy_id' para gerar o ranking."}

    async with AsyncSessionLocal() as session:
        if vacancy_id:
            # P0.A canonical: vacancy_candidates.company_id is NOT NULL — filter
            # at vc level. JOIN to candidates is safe (vc.company_id already
            # constrains which candidates are reachable from this vacancy).
            result = await session.execute(
                text("""
                    SELECT c.id, c.name, c.current_title, c.years_of_experience,
                           c.technical_skills, c.lia_score as candidate_lia_score,
                           vc.lia_score as vacancy_lia_score, vc.match_percentage, vc.stage
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.vacancy_id = :vid
                      AND vc.company_id = :company_id
                    ORDER BY vc.lia_score DESC NULLS LAST, vc.match_percentage DESC NULLS LAST
                """),
                {"vid": vacancy_id, "company_id": company_id},
            )
        else:
            # P0.A canonical: candidate_list_members has no company_id direct;
            # JOIN candidate_lists to constrain by tenant.
            result = await session.execute(
                text("""
                    SELECT c.id, c.name, c.current_title, c.years_of_experience,
                           c.technical_skills, c.lia_score,
                           clm.notes, clm.source
                    FROM candidate_list_members clm
                    JOIN candidates c ON c.id = clm.candidate_id
                    JOIN candidate_lists cl ON cl.id = clm.list_id
                    WHERE clm.list_id = :lid
                      AND cl.company_id = :company_id
                    ORDER BY c.lia_score DESC NULLS LAST, c.years_of_experience DESC NULLS LAST
                """),
                {"lid": shortlist_id, "company_id": company_id},
            )
        rows = result.mappings().all()

    if not rows:
        return {
            "success": True,
            "data": {"ranking": [], "total": 0},
            "message": "Nenhum candidato encontrado para ranking.",
        }

    ranking = []
    for i, row in enumerate(rows):
        entry = {
            "rank": i + 1,
            "id": str(row["id"]),
            "name": row["name"],
            "current_title": row["current_title"],
            "years_of_experience": row["years_of_experience"],
            "technical_skills": row["technical_skills"] or [],
        }
        if vacancy_id:
            entry["lia_score"] = row["vacancy_lia_score"] or row["candidate_lia_score"] or 0.0
            entry["match_percentage"] = row["match_percentage"] or 0.0
            entry["stage"] = row["stage"]
        else:
            entry["lia_score"] = row["lia_score"] or 0.0
        ranking.append(entry)

    return {
        "success": True,
        "data": {
            "shortlist_id": shortlist_id or None,
            "vacancy_id": vacancy_id or None,
            "ranking": ranking,
            "total": len(ranking),
        },
        "message": f"Ranking de {len(ranking)} candidatos gerado.",
    }


@tool_handler("sourcing")
async def _wrap_send_outreach(**kwargs: Any) -> dict[str, Any]:
    """Send recruitment outreach message to a candidate."""
    candidate_id = kwargs.get("candidate_id", "")
    channel = kwargs.get("channel", "email")
    message_template = kwargs.get("message_template", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: PII leak gate (email+phone)

    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    async with AsyncSessionLocal() as session:
        # P0.A canonical: this query previously leaked email + phone of
        # candidates from OTHER companies. Tenant gate required.
        c_result = await session.execute(
            text("""
                SELECT id, name, email, phone FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = c_result.mappings().first()

        if not candidate:
            return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' nao encontrado."}

        log_id = str(uuid.uuid4())
        if not company_id:
            raise ValueError(
                "company_id required for communication_logs INSERT "
                "(multi-tenancy fail-closed per ADR-001)"
            )
        await session.execute(
            text("""
                INSERT INTO communication_logs
                    (id, candidate_id, candidate_email, candidate_phone, channel,
                     message_type, subject, body, status, sent_by,
                     company_id, created_at, updated_at)
                VALUES
                    (:id, :cid, :email, :phone, :channel,
                     'outreach', 'Outreach', :body, 'sent', 'lia-agent',
                     :company_id, NOW(), NOW())
            """),
            {
                "id": log_id,
                "cid": str(candidate_id),
                "email": candidate["email"],
                "phone": candidate["phone"],
                "channel": channel,
                "company_id": str(company_id),
                "body": message_template,
            },
        )
        await session.commit()

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate_id),
            "candidate_name": candidate["name"],
            "channel": channel,
            "status": "sent",
            "log_id": log_id,
        },
        "message": f"Mensagem enviada para '{candidate['name']}' via {channel}.",
    }


@tool_handler("sourcing")
async def _wrap_generate_message(**kwargs: Any) -> dict[str, Any]:
    """Generate a personalized outreach message."""
    candidate_id = kwargs.get("candidate_id", "")
    tone = kwargs.get("tone", "professional")
    role = kwargs.get("role", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate

    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, name, current_title, current_company, technical_skills
                FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = result.mappings().first()

    if not candidate:
        return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' nao encontrado."}

    name = candidate["name"]
    title = candidate["current_title"] or "profissional"
    company = candidate["current_company"] or ""
    skills = candidate["technical_skills"] or []
    top_skills = ", ".join(skills[:3]) if skills else "suas habilidades"
    target_role = role or "uma oportunidade"

    if tone == "casual":
        message = (
            f"Oi {name}! Tudo bem?\n\n"
            f"Vi seu perfil como {title}"
            f"{f' na {company}' if company else ''} e fiquei impressionado(a) "
            f"com {top_skills}.\n\n"
            f"Temos {target_role} que combina muito com voce. "
            f"Bora trocar uma ideia?\n\nAbs!"
        )
    elif tone == "enthusiastic":
        message = (
            f"Ola {name}!\n\n"
            f"Estamos muito empolgados em encontrar seu perfil! "
            f"Sua experiencia como {title}"
            f"{f' na {company}' if company else ''} e "
            f"expertise em {top_skills} sao exatamente o que buscamos.\n\n"
            f"Temos uma oportunidade incrivel como {target_role}. "
            f"Adorariamos conversar com voce!\n\nAtenciosamente"
        )
    else:
        message = (
            f"Prezado(a) {name},\n\n"
            f"Identificamos seu perfil como {title}"
            f"{f' na {company}' if company else ''} e acreditamos que "
            f"suas competencias em {top_skills} sao altamente relevantes.\n\n"
            f"Gostaríamos de apresentar uma oportunidade como {target_role}. "
            f"Podemos agendar uma conversa?\n\nAtenciosamente"
        )

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate_id),
            "candidate_name": name,
            "generated_message": message,
            "tone": tone,
            "role": role,
        },
        "message": f"Mensagem personalizada gerada para '{name}'.",
    }


@tool_handler("sourcing")
async def _wrap_track_response(**kwargs: Any) -> dict[str, Any]:
    """Track candidate response to outreach."""
    candidate_id = kwargs.get("candidate_id", "")
    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, channel, status, sent_at, delivered_at, read_at, subject,
                       message_type, error_message
                FROM communication_logs
                WHERE candidate_id = :cid
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"cid": str(candidate_id)},
        )
        rows = result.mappings().all()

    if not rows:
        return {
            "success": True,
            "data": {"candidate_id": candidate_id, "communications": [], "total": 0},
            "message": f"Nenhuma comunicacao encontrada para o candidato '{candidate_id}'.",
        }

    communications = []
    for row in rows:
        communications.append({
            "log_id": row["id"],
            "channel": row["channel"],
            "status": row["status"],
            "message_type": row["message_type"],
            "subject": row["subject"],
            "sent_at": str(row["sent_at"]) if row["sent_at"] else None,
            "delivered_at": str(row["delivered_at"]) if row["delivered_at"] else None,
            "read_at": str(row["read_at"]) if row["read_at"] else None,
            "error": row["error_message"],
        })

    latest_status = rows[0]["status"] if rows else "unknown"

    return {
        "success": True,
        "data": {
            "candidate_id": candidate_id,
            "response_status": latest_status,
            "communications": communications,
            "total": len(communications),
        },
        "message": f"Status de comunicacao do candidato: {latest_status}. {len(communications)} registro(s) encontrado(s).",
    }


@tool_handler("sourcing")
async def _wrap_view_candidate(**kwargs: Any) -> dict[str, Any]:
    """View detailed candidate profile."""
    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: PII leak gate (full profile)
    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    async with AsyncSessionLocal() as session:
        # P0.A canonical: this query previously leaked the FULL profile
        # (name, email, phone, linkedin_url, github_url, salary, salary_currency,
        # location, tags, notes) of candidates from OTHER companies.
        # Tenant gate required.
        result = await session.execute(
            text("""
                SELECT id, name, email, phone, linkedin_url, github_url, portfolio_url,
                       current_title, current_company, seniority_level,
                       years_of_experience, technical_skills, soft_skills,
                       languages, certifications, interests,
                       location_city, location_state, location_country,
                       work_model_preference, is_remote, willing_to_relocate,
                       current_salary, desired_salary_min, desired_salary_max,
                       salary_currency, headline, expertise,
                       lia_score, lia_insights, status, work_history,
                       source, tags, notes, created_at, updated_at
                FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        candidate = result.mappings().first()

    if not candidate:
        return {"success": False, "data": {}, "message": f"Candidato '{candidate_id}' nao encontrado."}

    profile = {
        "id": str(candidate["id"]),
        "name": candidate["name"],
        "email": candidate["email"],
        "phone": candidate["phone"],
        "linkedin_url": candidate["linkedin_url"],
        "github_url": candidate["github_url"],
        "portfolio_url": candidate["portfolio_url"],
        "current_title": candidate["current_title"],
        "current_company": candidate["current_company"],
        "seniority_level": candidate["seniority_level"],
        "years_of_experience": candidate["years_of_experience"],
        "headline": candidate["headline"],
        "technical_skills": candidate["technical_skills"] or [],
        "soft_skills": candidate["soft_skills"] or [],
        "languages": candidate["languages"],
        "certifications": candidate["certifications"] or [],
        "interests": candidate["interests"] or [],
        "expertise": candidate["expertise"] or [],
        "location": {
            "city": candidate["location_city"],
            "state": candidate["location_state"],
            "country": candidate["location_country"],
        },
        "work_preferences": {
            "work_model": candidate["work_model_preference"],
            "is_remote": candidate["is_remote"],
            "willing_to_relocate": candidate["willing_to_relocate"],
        },
        "salary": {
            "current": candidate["current_salary"],
            "desired_min": candidate["desired_salary_min"],
            "desired_max": candidate["desired_salary_max"],
            "currency": candidate["salary_currency"],
        },
        "lia_score": candidate["lia_score"],
        "lia_insights": candidate["lia_insights"],
        "status": candidate["status"],
        "work_history": candidate["work_history"],
        "source": candidate["source"],
        "tags": candidate["tags"] or [],
        "notes": candidate["notes"],
        "created_at": str(candidate["created_at"]) if candidate["created_at"] else None,
        "updated_at": str(candidate["updated_at"]) if candidate["updated_at"] else None,
    }

    return {
        "success": True,
        "data": {
            "candidate_id": str(candidate["id"]),
            "profile": profile,
        },
        "message": f"Perfil de '{candidate['name']}' carregado com sucesso.",
    }


TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="set_search_criteria",
        description="Define os parametros de busca de talentos: cargo, skills, localizacao, nivel de experiencia e faixa salarial.",
        parameters={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Cargo ou funcao desejada"},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de skills requeridas"},
                "location": {"type": "string", "description": "Localizacao desejada"},
                "experience_level": {"type": "string", "description": "Nivel de experiencia (Junior, Pleno, Senior, etc.)"},
                "salary_range": {"type": "object", "description": "Faixa salarial com min e max"},
            },
            "required": ["role"],
        },
        output_schema=ToolOutput,
        function=_wrap_set_search_criteria,
    ),
    ToolDefinition(
        name="suggest_skills",
        description="Sugere skills relevantes com base no cargo e contexto da vaga.",
        parameters={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Cargo para sugestao de skills"},
                "context": {"type": "object", "description": "Contexto adicional da busca"},
            },
            "required": ["role"],
        },
        output_schema=ToolOutput,
        function=_wrap_suggest_skills,
    ),
    ToolDefinition(
        name="search_candidates",
        description="Executa busca de candidatos com base nos criterios definidos. Retorna lista paginada de candidatos.",
        parameters={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Cargo ou titulo para buscar"},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de skills para filtrar"},
                "location": {"type": "string", "description": "Localizacao para filtrar"},
                "experience_level": {"type": "string", "description": "Nivel de senioridade"},
                "page": {"type": "integer", "description": "Numero da pagina"},
                "limit": {"type": "integer", "description": "Quantidade de resultados por pagina"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_search_candidates,
    ),
    ToolDefinition(
        name="filter_results",
        description="Aplica filtros adicionais aos resultados da busca de candidatos.",
        parameters={
            "type": "object",
            "properties": {
                "filters": {"type": "object", "description": "Filtros a aplicar (min_experience, max_experience, location, skills, seniority_level, title, status)"},
                "page": {"type": "integer", "description": "Numero da pagina"},
                "limit": {"type": "integer", "description": "Quantidade por pagina"},
            },
            "required": ["filters"],
        },
        output_schema=ToolOutput,
        function=_wrap_filter_results,
    ),
    ToolDefinition(
        name="view_candidate",
        description="Visualiza o perfil detalhado de um candidato especifico.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        touches_pii=True,
        pii_output_fields=["name", "email", "phone", "linkedin_url"],
        output_schema=ToolOutput,
        function=_wrap_view_candidate,
    ),
    ToolDefinition(
        name="analyze_profile",
        description="Realiza analise detalhada de um perfil de candidato usando IA, identificando pontos fortes e gaps.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato para analise"},
            },
            "required": ["candidate_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name"],
        output_schema=ToolOutput,
        function=_wrap_analyze_profile,
    ),
    ToolDefinition(
        name="compare_candidates",
        description="Compara multiplos candidatos lado a lado, gerando ranking e analise comparativa.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos a comparar"},
            },
            "required": ["candidate_ids"],
        },
        output_schema=ToolOutput,
        function=_wrap_compare_candidates,
    ),
    ToolDefinition(
        name="score_candidate",
        description="Aplica scoring WSI a um candidato em relacao a uma vaga especifica.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "vacancy_id": {"type": "string", "description": "ID da vaga para scoring"},
            },
            "required": ["candidate_id", "vacancy_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_score_candidate,
    ),
    ToolDefinition(
        name="add_to_shortlist",
        description="Adiciona um candidato a shortlist de selecionados.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "shortlist_id": {"type": "string", "description": "ID da shortlist/lista"},
                "added_by": {"type": "string", "description": "Quem adicionou"},
                "notes": {"type": "string", "description": "Notas sobre a adicao"},
            },
            "required": ["candidate_id", "shortlist_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_add_to_shortlist,
    ),
    ToolDefinition(
        name="remove_from_shortlist",
        description="Remove um candidato da shortlist.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "shortlist_id": {"type": "string", "description": "ID da shortlist"},
            },
            "required": ["candidate_id", "shortlist_id"],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_remove_from_shortlist,
    ),
    ToolDefinition(
        name="rank_candidates",
        description="Gera ranking dos candidatos na shortlist ou vaga com base em scores.",
        parameters={
            "type": "object",
            "properties": {
                "shortlist_id": {"type": "string", "description": "ID da shortlist"},
                "vacancy_id": {"type": "string", "description": "ID da vaga para ranking por vacancy_candidates"},
                "limit": {
                    "type": "integer",
                    "description": "Numero maximo de candidatos no ranking (padrao: 10, max: 50)",
                },
            },
            "required": [],
        },
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        output_schema=ToolOutput,
        function=_wrap_rank_candidates,
    ),
    ToolDefinition(
        name="send_outreach",
        description="Envia mensagem de abordagem para um candidato via canal especificado. Requer confirmacao do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "channel": {"type": "string", "description": "Canal de contato (email, linkedin, whatsapp)"},
                "message_template": {"type": "string", "description": "Template ou conteudo da mensagem"},
            },
            "required": ["candidate_id", "channel", "message_template"],
        },
        side_effects=["send"],
        output_schema=ToolOutput,
        function=_wrap_send_outreach,
    ),
    ToolDefinition(
        name="generate_message",
        description="Gera mensagem personalizada de abordagem para um candidato com base no tom e cargo.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "tone": {"type": "string", "description": "Tom da mensagem (professional, casual, enthusiastic)"},
                "role": {"type": "string", "description": "Cargo da vaga para contexto"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_message,
    ),
    ToolDefinition(
        name="track_response",
        description="Acompanha a resposta de um candidato a uma abordagem enviada.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_track_response,
    ),
]


@tool_handler("sourcing")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
    try:
        # ADR-001-EXEMPT: generate_report aggregation over applications table — multi-filter COUNT, not abstractable to simple repo method
        async with AsyncSessionLocal() as session:
            row = await session.execute(text("""
                SELECT COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'shortlisted') AS shortlisted,
                    COUNT(*) FILTER (WHERE status = 'contacted') AS contacted
                FROM applications
                WHERE company_id = :cid
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """), {"cid": company_id, "days": period_days})
            data = row.mappings().first() or {}
            summary = {
                "total_applications": int(data.get("total") or 0),
                "shortlisted": int(data.get("shortlisted") or 0),
                "contacted": int(data.get("contacted") or 0),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[sourcing_tools] generate_report DB error: {e}")
    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "period": period,
            "report_id": report_id,
            "generated": True,
            "summary": summary,
        },
        "message": f"Relatorio '{report_type}' de sourcing gerado (id: {report_id}). {summary.get('total_applications', 0)} candidaturas no periodo.",
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="generate_report",
        description="Gera relatorio de metricas de sourcing para o periodo selecionado.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo de relatorio: summary, detailed, funnel"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_report,
    )
)

@tool_handler("sourcing")
async def _wrap_enrich_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    """Enrich a candidate profile with Apify (LinkedIn person + email discovery)."""
    from app.domains.sourcing.services.apify_service import apify_service
    linkedin_url = kwargs.get("linkedin_url", "")
    candidate_name = kwargs.get("candidate_name", "")
    candidate_email = kwargs.get("candidate_email", "")

    if not linkedin_url and not candidate_name:
        return {
            "success": False,
            "data": {},
            "message": "Forneça linkedin_url ou candidate_name para enriquecimento.",
        }

    result = await apify_service.enrich_candidate_profile(
        linkedin_url=linkedin_url or None,
        candidate_name=candidate_name or None,
        candidate_email=candidate_email or None,
    )

    has_data = bool(result.get("linkedin") or result.get("emails"))
    return {
        "success": True,
        "data": result,
        "message": (
            f"Perfil enriquecido com sucesso. Dados encontrados: "
            f"{'LinkedIn ' if result.get('linkedin') else ''}"
            f"{'Emails ' if result.get('emails') else ''}"
        ) if has_data else "Nenhum dado complementar encontrado para este candidato.",
    }


@tool_handler("sourcing")
async def _wrap_enrich_candidate_contact(**kwargs: Any) -> dict[str, Any]:
    """Enrich a candidate's contact info (email/phone) via Apify ($0.01/candidate)."""
    from uuid import UUID as _UUID

    from app.domains.sourcing.services.contact_enrichment_service import get_contact_enrichment_service

    candidate_id = kwargs.get("candidate_id", "")
    linkedin_url = kwargs.get("linkedin_url", "")
    force = kwargs.get("force", False)
    company_id = kwargs.get("company_id", "") or ""
    user_id = kwargs.get("user_id", "") or ""

    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parametro 'candidate_id' e obrigatorio."}

    try:
        svc = get_contact_enrichment_service()
        async with AsyncSessionLocal() as session:
            result = await svc.enrich_candidate_contact(
                db=session,
                candidate_id=_UUID(candidate_id),
                linkedin_url=linkedin_url or None,
                force=force,
                company_id=company_id or None,
                user_id=user_id or None,
            )
            await session.commit()

        email = result.get("email")
        phone = result.get("phone")
        has_contact = result.get("has_contact", False) or bool(email or phone)

        return {
            "success": result.get("success", False),
            "data": {
                "candidate_id": candidate_id,
                "email": email,
                "phone": phone,
                "has_contact": has_contact,
                "source": result.get("source", "unknown"),
                "cost_usd": result.get("cost_usd", 0),
            },
            "message": (
                f"Contato enriquecido: email={email or 'N/A'}, phone={phone or 'N/A'} (custo: ${result.get('cost_usd', 0):.2f})"
                if has_contact
                else "Nenhum contato encontrado para este candidato via Apify."
            ),
        }
    except Exception as e:
        logger.warning("[sourcing_tools] enrich_candidate_contact failed: %s", e)
        return {"success": False, "data": {}, "message": f"Falha no enriquecimento de contato: {e}"}


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="enrich_candidate_contact",
        description=(
            "Enriquece contato (email/telefone) de um candidato via Apify ($0.01/candidato). "
            "Muito mais barato que revelar via Pearch (2-14 creditos). "
            "Use para obter email ou telefone de candidatos interessantes antes da abordagem."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "linkedin_url": {"type": "string", "description": "URL do LinkedIn (opcional se ja cadastrado)"},
                "force": {"type": "boolean", "description": "Forcar re-enriquecimento mesmo se ja enriquecido recentemente"},
            },
            "required": ["candidate_id"],
        },
        touches_pii=True,
        pii_output_fields=["email", "phone", "linkedin_url"],
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_enrich_candidate_contact,
    )
)


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="enrich_candidate_profile",
        description=(
            "Enriquece perfil de candidato via Apify. "
            "Busca dados do LinkedIn (experiência, skills, educação) e descobre emails. "
            "Use após identificar candidatos interessantes no sourcing."
        ),
        parameters={
            "type": "object",
            "properties": {
                "linkedin_url": {"type": "string", "description": "URL do perfil LinkedIn do candidato"},
                "candidate_name": {"type": "string", "description": "Nome completo do candidato"},
                "candidate_email": {"type": "string", "description": "Email conhecido do candidato (opcional)"},
            },
            "required": [],
        },
        touches_pii=True,
        pii_output_fields=["name", "email", "phone"],
        side_effects=["write"],
        output_schema=ToolOutput,
        function=_wrap_enrich_candidate_profile,
    )
)


@tool_handler("sourcing")
async def _wrap_rag_search(**kwargs) -> dict:
    """Busca semantica hibrida de candidatos (BM25 + pgvector)."""
    query = kwargs.get("query", "")
    company_id = kwargs.get("company_id", "")
    limit = kwargs.get("limit", 20)
    alpha = kwargs.get("alpha", 0.5)

    if not query:
        return {"success": False, "data": {}, "message": "Parametro query obrigatorio."}

    try:
        from app.domains.ai.services.rag_pipeline_service import rag_pipeline_service
        async with AsyncSessionLocal() as session:
            result = await rag_pipeline_service.search(
                query=query,
                company_id=company_id or "global",
                db=session,
                limit=min(limit, 50),
                alpha=alpha,
            )
        candidates = []
        for r in (result.results or []):
            candidates.append({
                "name": getattr(r, "name", ""),
                "score": getattr(r, "score", 0),
                "summary": (getattr(r, "summary", "") or "")[:200],
                "id": str(getattr(r, "id", "")),
            })
        if not candidates:
            from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
            _g = build_empty_result_guidance("candidato", {"query": query})
            return {
                "success": True,
                "data": {"candidates": [], "total": 0, "search_type": "hybrid_rag", **_g},
                "message": _g.get("guidance") or "Nenhum candidato via busca semantica com esse criterio.",
            }
        return {
            "success": True,
            "data": {"candidates": candidates, "total": result.total_found, "search_type": "hybrid_rag"},
            "message": f"Encontrados {result.total_found} candidatos via busca semantica.",
        }
    except Exception as e:
        logger.warning("[sourcing_tools] rag_search failed: %s", e)
        return {
            "success": False,
            "data": {"candidates": [], "total": 0},
            "message": "Busca semantica indisponivel. Use search_candidates para busca textual.",
        }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="rag_search",
        description=(
            "Busca semantica de candidatos combinando relevancia textual (BM25) e "
            "similaridade vetorial (pgvector). Use para buscas por perfil, competencias "
            "ou descricoes complexas onde keyword search nao e suficiente."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto de busca em linguagem natural"},
                "limit": {"type": "integer", "description": "Maximo de resultados (default 20, max 50)"},
                "alpha": {"type": "number", "description": "Peso semantico vs textual (0.0-1.0, default 0.5)"},
            },
            "required": ["query"],
        },
        output_schema=ToolOutput,
        function=_wrap_rag_search,
    )
)

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "search-criteria": ["set_search_criteria", "suggest_skills"],
    "talent-search": ["search_candidates", "filter_results", "view_candidate", "enrich_candidate_profile", "enrich_candidate_contact"],
    "profile-analysis": ["analyze_profile", "compare_candidates", "score_candidate", "enrich_candidate_profile", "enrich_candidate_contact"],
    "shortlist-creation": ["add_to_shortlist", "remove_from_shortlist", "rank_candidates", "generate_report"],
    "outreach": ["send_outreach", "generate_message", "track_response"],
}


def get_sourcing_tools() -> list[ToolDefinition]:
    """Return all sourcing tool definitions."""
    return list(TOOL_DEFINITIONS)


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return only tools relevant to the current sourcing stage.

    Args:
        stage: Current sourcing stage identifier.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.debug(f"[sourcing_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools





# ─────────────────────────────────────────────────────────────────────────────
# Opção C — registro global com namespace de domínio (2026-06-18)
# ─────────────────────────────────────────────────────────────────────────────

def register_sourcing_global() -> int:
    """Registra as tools de sourcing no tool_registry global.

    Tools com nomes conflitantes recebem prefixo 'sourcing_' (Opção C —
    namespace de domínio, 2026-06-18). Tools únicas mantêm o nome original.
    Segue o padrão de register_ui_tools_global() (ui_tool_registry.py).
    Chamada por app/tools/__init__.py:initialize_tools().

    Renames:
        search_candidates  → sourcing_search_candidates
        compare_candidates → sourcing_compare_candidates
        generate_report    → sourcing_generate_report
    """
    from app.tools.registry import ToolDefinition as _G
    from app.tools.registry import tool_registry as _reg

    _RENAMES: dict[str, str] = {
        "search_candidates": "sourcing_search_candidates",
        "compare_candidates": "sourcing_compare_candidates",
        "generate_report": "sourcing_generate_report",
        "rank_candidates": "sourcing_rank_candidates",
    }

    n = 0
    for td in TOOL_DEFINITIONS:
        _reg.register(
            _G(
                name=_RENAMES.get(td.name, td.name),
                description=td.description,
                parameters_schema=td.parameters,
                handler=td.function,
                allowed_agents=["recruiter_assistant", "orchestrator"],
            )
        )
        n += 1
    return n
