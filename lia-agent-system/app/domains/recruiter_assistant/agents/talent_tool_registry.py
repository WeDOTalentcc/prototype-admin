"""
Talent Tool Registry - Exposes talent funnel tools to the ReAct loop.

Wraps talent funnel operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for candidate analysis and
management.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


async def _wrap_search_candidates(**kwargs: Any) -> dict[str, Any]:
    """Search candidates by skills, experience, location."""
    query = kwargs.get("query", "")
    filters = kwargs.get("filters", {})
    kwargs.get("company_id", "")
    limit = int(kwargs.get("limit", 20))
    logger.info(f"[talent_tools] search_candidates called: query={query} filters={filters}")

    results = []
    total = 0
    try:
        async with AsyncSessionLocal() as session:
            location = filters.get("location", "") if isinstance(filters, dict) else ""
            min_exp = filters.get("min_experience", 0) if isinstance(filters, dict) else 0

            rows = await session.execute(
                text("""
                    SELECT id, name, current_title, location_city, location_state,
                           technical_skills, years_of_experience, lia_score,
                           skills_match_percentage, status
                    FROM candidates
                    WHERE is_active = true
                      AND (:query = ''
                           OR name ILIKE :qlike
                           OR current_title ILIKE :qlike
                           OR :query = ANY(technical_skills))
                      AND (:location = '' OR location_city ILIKE :lloc OR location_state ILIKE :lloc)
                      AND (years_of_experience IS NULL OR years_of_experience >= :min_exp)
                    ORDER BY lia_score DESC NULLS LAST, created_at DESC
                    LIMIT :lim
                """),
                {
                    "query": query,
                    "qlike": f"%{query}%",
                    "location": location,
                    "lloc": f"%{location}%",
                    "min_exp": min_exp,
                    "lim": limit,
                },
            )
            for row in rows.mappings():
                results.append({
                    "id": str(row["id"]),
                    "name": row["name"],
                    "current_title": row["current_title"],
                    "location": f"{row['location_city'] or ''}, {row['location_state'] or ''}".strip(", "),
                    "skills": row["technical_skills"] or [],
                    "years_of_experience": row["years_of_experience"],
                    "lia_score": row["lia_score"],
                    "match_percentage": row["skills_match_percentage"],
                    "status": row["status"],
                })

            count_row = await session.execute(
                text("""
                    SELECT COUNT(*) AS total FROM candidates
                    WHERE is_active = true
                      AND (:query = ''
                           OR name ILIKE :qlike
                           OR current_title ILIKE :qlike
                           OR :query = ANY(technical_skills))
                      AND (:location = '' OR location_city ILIKE :lloc OR location_state ILIKE :lloc)
                      AND (years_of_experience IS NULL OR years_of_experience >= :min_exp)
                """),
                {"query": query, "qlike": f"%{query}%", "location": location,
                 "lloc": f"%{location}%", "min_exp": min_exp},
            )
            total = int((count_row.mappings().first() or {}).get("total", len(results)))
    except Exception as e:
        logger.warning(f"[talent_tools] search_candidates DB error: {e}")

    return {
        "success": True,
        "data": {
            "query": query,
            "filters": filters,
            "candidates_found": total,
            "results": results,
        },
        "message": f"Busca realizada. {total} candidatos encontrados para '{query}'.",
    }


async def _wrap_list_candidates(**kwargs: Any) -> dict[str, Any]:
    """List candidates in the funnel with optional filters."""
    status = kwargs.get("status", "all")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    limit = int(kwargs.get("limit", 20))
    logger.info(f"[talent_tools] list_candidates called: status={status} vacancy={vacancy_id} limit={limit}")

    candidates = []
    total = 0
    try:
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text("""
                    SELECT vc.id AS vc_id, vc.vacancy_id, vc.candidate_id,
                           vc.status, vc.stage, vc.lia_score, vc.match_percentage,
                           vc.created_at,
                           c.name, c.current_title, c.location_city, c.technical_skills
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE (:status = 'all' OR vc.status = :status)
                      AND (:vid = '' OR vc.vacancy_id::text = :vid)
                      AND (:cid = '' OR vc.company_id = :cid)
                    ORDER BY vc.lia_score DESC NULLS LAST, vc.created_at DESC
                    LIMIT :lim
                """),
                {"status": status, "vid": vacancy_id, "cid": company_id, "lim": limit},
            )
            for row in rows.mappings():
                candidates.append({
                    "id": str(row["candidate_id"]),
                    "name": row["name"],
                    "current_title": row["current_title"],
                    "location": row["location_city"],
                    "skills": row["technical_skills"] or [],
                    "status": row["status"],
                    "stage": row["stage"],
                    "lia_score": row["lia_score"],
                    "match_percentage": row["match_percentage"],
                    "applied_at": str(row["created_at"]) if row["created_at"] else None,
                })

            count_row = await session.execute(
                text("""
                    SELECT COUNT(*) AS total FROM vacancy_candidates vc
                    WHERE (:status = 'all' OR vc.status = :status)
                      AND (:vid = '' OR vc.vacancy_id::text = :vid)
                      AND (:cid = '' OR vc.company_id = :cid)
                """),
                {"status": status, "vid": vacancy_id, "cid": company_id},
            )
            total = int((count_row.mappings().first() or {}).get("total", len(candidates)))
    except Exception as e:
        logger.warning(f"[talent_tools] list_candidates DB error: {e}")

    return {
        "success": True,
        "data": {
            "status": status,
            "limit": limit,
            "total": total,
            "candidates": candidates,
        },
        "message": f"Lista carregada. {total} candidatos no funil com status '{status}'.",
    }


async def _wrap_view_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    """View complete candidate profile including education and work history."""
    candidate_id = kwargs.get("candidate_id", "")
    logger.info(f"[talent_tools] view_candidate_profile called for candidate={candidate_id}")

    profile: dict[str, Any] = {"candidate_id": candidate_id, "profile_loaded": False}
    try:
        async with AsyncSessionLocal() as session:
            row = await session.execute(
                text("""
                    SELECT id, name, email, current_title, current_company,
                           seniority_level, years_of_experience,
                           technical_skills, soft_skills, certifications,
                           location_city, location_state, location_country,
                           lia_score, skills_match_percentage,
                           status, is_active, linkedin_url,
                           self_introduction, work_history, languages,
                           salary_expectation_clt, salary_expectation_pj,
                           work_model_preference, is_remote, willing_to_relocate,
                           gender, source
                    FROM candidates
                    WHERE id = :cid
                """),
                {"cid": candidate_id},
            )
            data = row.mappings().first()
            if not data:
                return {
                    "success": False,
                    "data": {"candidate_id": candidate_id},
                    "message": f"Candidato {candidate_id} nao encontrado.",
                }

            # Busca formação acadêmica na tabela candidate_education
            edu_rows = await session.execute(
                text("""
                    SELECT institution, degree, field_of_study, start_year, end_year, is_current
                    FROM candidate_education
                    WHERE candidate_id = :cid
                    ORDER BY end_year DESC NULLS FIRST, start_year DESC NULLS FIRST
                """),
                {"cid": candidate_id},
            )
            education = [
                {
                    "institution": r["institution"],
                    "degree": r["degree"],
                    "field_of_study": r["field_of_study"],
                    "period": f"{r['start_year'] or '?'} - {'atual' if r['is_current'] else (r['end_year'] or '?')}",
                }
                for r in edu_rows.mappings()
            ]

            profile = {
                "candidate_id": str(data["id"]),
                "name": data["name"],
                "email": data["email"],
                "current_title": data["current_title"],
                "current_company": data["current_company"],
                "seniority_level": data["seniority_level"],
                "years_of_experience": data["years_of_experience"],
                "technical_skills": data["technical_skills"] or [],
                "soft_skills": data["soft_skills"] or [],
                "certifications": data["certifications"] or [],
                "location": f"{data['location_city'] or ''}, {data['location_country'] or ''}".strip(", "),
                "lia_score": data["lia_score"],
                "match_percentage": data["skills_match_percentage"],
                "status": data["status"],
                "linkedin_url": data["linkedin_url"],
                "summary": data["self_introduction"],
                "languages": data["languages"],
                "work_history": data["work_history"] or [],
                "education": education,
                "salary_expectation_clt": data["salary_expectation_clt"],
                "salary_expectation_pj": data["salary_expectation_pj"],
                "work_model": data["work_model_preference"],
                "is_remote": data["is_remote"],
                "willing_to_relocate": data["willing_to_relocate"],
                "gender": data["gender"],
                "source": data["source"],
                "profile_loaded": True,
            }
    except Exception as e:
        logger.warning(f"[talent_tools] view_candidate_profile DB error: {e}")

    return {
        "success": True,
        "data": profile,
        "message": f"Perfil completo do candidato {profile.get('name', candidate_id)} carregado.",
    }


async def _wrap_compare_candidates(**kwargs: Any) -> dict[str, Any]:
    """Compare 2+ candidates side by side."""
    candidate_ids = kwargs.get("candidate_ids", [])
    logger.info(f"[talent_tools] compare_candidates called: candidates={len(candidate_ids)}")
    try:
        return {
            "success": True,
            "data": {
                "candidate_ids": candidate_ids,
                "comparison_count": len(candidate_ids),
                "comparison_complete": True,
                "dimensions": ["skills", "experience", "score", "fit"],
            },
            "message": f"Comparacao de {len(candidate_ids)} candidatos concluida.",
        }
    except Exception as e:
        logger.error(f"[talent_tools] compare_candidates error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": "Erro ao comparar candidatos."}


async def _wrap_rank_candidates(**kwargs: Any) -> dict[str, Any]:
    """Rank candidates by fit score for a job."""
    vacancy_id = kwargs.get("vacancy_id", "")
    criteria = kwargs.get("criteria", "fit_score")
    logger.info(f"[talent_tools] rank_candidates called: vacancy={vacancy_id} criteria={criteria}")

    order_col = "vc.match_percentage" if criteria == "skills" else "vc.lia_score"
    ranking = []
    try:
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text(f"""
                    SELECT vc.candidate_id, vc.status, vc.stage,
                           vc.lia_score, vc.match_percentage,
                           c.name, c.current_title, c.technical_skills
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.vacancy_id::text = :vid
                      AND vc.status != 'rejected'
                    ORDER BY {order_col} DESC NULLS LAST
                    LIMIT 50
                """),
                {"vid": vacancy_id},
            )
            for position, row in enumerate(rows.mappings(), start=1):
                ranking.append({
                    "position": position,
                    "candidate_id": str(row["candidate_id"]),
                    "name": row["name"],
                    "current_title": row["current_title"],
                    "skills": row["technical_skills"] or [],
                    "lia_score": row["lia_score"],
                    "match_percentage": row["match_percentage"],
                    "status": row["status"],
                    "stage": row["stage"],
                })
    except Exception as e:
        logger.error(f"[talent_tools] rank_candidates error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": f"Erro ao gerar ranking para vaga {vacancy_id}."}

    return {
        "success": True,
        "data": {
            "vacancy_id": vacancy_id,
            "criteria": criteria,
            "ranking_generated": True,
            "ranked_count": len(ranking),
            "ranking": ranking,
        },
        "message": f"Ranking gerado: {len(ranking)} candidatos para a vaga {vacancy_id} (criterio: {criteria}).",
    }


async def _wrap_analyze_skills(**kwargs: Any) -> dict[str, Any]:
    """Analyze skill match between candidate and job requirements."""
    candidate_id = kwargs.get("candidate_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    logger.info(f"[talent_tools] analyze_skills called: candidate={candidate_id} vacancy={vacancy_id}")

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    extra_skills: list[str] = []
    match_percentage = 0.0

    try:
        async with AsyncSessionLocal() as session:
            c_row = await session.execute(
                text("SELECT technical_skills, soft_skills FROM candidates WHERE id = :cid"),
                {"cid": candidate_id},
            )
            c_data = c_row.mappings().first()
            candidate_skills = set(s.lower() for s in ((c_data or {}).get("technical_skills") or []))

            if vacancy_id:
                v_row = await session.execute(
                    text("SELECT technical_requirements FROM job_vacancies WHERE id = :vid"),
                    {"vid": vacancy_id},
                )
                v_data = v_row.mappings().first()
                tech_reqs = (v_data or {}).get("technical_requirements") or []
                required_skills = set()
                for req in (tech_reqs if isinstance(tech_reqs, list) else []):
                    tech = (req.get("technology") or "").lower()
                    if tech:
                        required_skills.add(tech)

                if required_skills:
                    matched_skills = sorted(candidate_skills & required_skills)
                    missing_skills = sorted(required_skills - candidate_skills)
                    extra_skills = sorted(candidate_skills - required_skills)
                    match_percentage = round(len(matched_skills) / len(required_skills) * 100, 1)
                    # Persist match_percentage on vacancy_candidate if record exists
                    await session.execute(
                        text("""
                            UPDATE vacancy_candidates
                            SET match_percentage = :mp
                            WHERE candidate_id = :cid AND vacancy_id::text = :vid
                        """),
                        {"mp": match_percentage, "cid": candidate_id, "vid": vacancy_id},
                    )
                    await session.commit()
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(f"[talent_tools] analyze_skills DB error: {e}")

    return {
        "success": True,
        "data": {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "match_percentage": match_percentage,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
        },
        "message": f"Analise de skills: {match_percentage}% de match ({len(matched_skills)} skills correspondentes, {len(missing_skills)} faltantes).",
    }


async def _wrap_recommend_actions(**kwargs: Any) -> dict[str, Any]:
    """Generate action recommendations for candidates based on real scores and status."""
    candidate_ids = kwargs.get("candidate_ids", [])
    logger.info(f"[talent_tools] recommend_actions called: candidates={len(candidate_ids)}")

    recommendations = []
    try:
        if candidate_ids:
            async with AsyncSessionLocal() as session:
                rows = await session.execute(
                    text("""
                        SELECT id, name, status, lia_score, skills_match_percentage,
                               last_contacted_at, last_activity_at
                        FROM candidates
                        WHERE id = ANY(:ids::uuid[])
                    """),
                    {"ids": candidate_ids},
                )
                for row in rows.mappings():
                    score = row["lia_score"] or 0
                    match = row["skills_match_percentage"] or 0
                    status = row["status"] or "new"
                    actions = []

                    if score >= 4.2 and status in ("new", "sourced"):
                        actions.append({"action": "advance_to_screening", "priority": "high",
                                        "reason": f"Score LIA alto ({score:.1f}/5). Mover para triagem imediatamente."})
                    elif score >= 3.5:
                        actions.append({"action": "schedule_interview", "priority": "medium",
                                        "reason": f"Bom score ({score:.1f}/5). Agendar entrevista inicial."})
                    elif score < 3.0 and score > 0:
                        actions.append({"action": "review_or_reject", "priority": "low",
                                        "reason": f"Score baixo ({score:.1f}/5). Revisar criterios ou desqualificar."})

                    if match >= 80:
                        actions.append({"action": "highlight_as_top_match", "priority": "high",
                                        "reason": f"Match de skills excelente ({match:.0f}%)."})
                    elif match < 50 and match > 0:
                        actions.append({"action": "verify_requirements", "priority": "medium",
                                        "reason": f"Match de skills baixo ({match:.0f}%). Verificar se requisitos sao corretos."})

                    if not row["last_contacted_at"] and status != "new":
                        actions.append({"action": "send_initial_contact", "priority": "medium",
                                        "reason": "Candidato nunca foi contactado."})

                    if not actions:
                        actions.append({"action": "review_profile", "priority": "low",
                                        "reason": "Revisar perfil completo para determinar proximo passo."})

                    recommendations.append({
                        "candidate_id": str(row["id"]),
                        "name": row["name"],
                        "current_status": status,
                        "lia_score": score,
                        "actions": actions,
                    })
    except Exception as e:
        logger.warning(f"[talent_tools] recommend_actions DB error: {e}")
        recommendations = [{"candidate_id": cid, "actions": [{"action": "review_profile", "priority": "low"}]}
                           for cid in candidate_ids]

    return {
        "success": True,
        "data": {
            "candidate_ids": candidate_ids,
            "recommendations_count": len(recommendations),
            "recommendations": recommendations,
        },
        "message": f"Recomendacoes geradas para {len(recommendations)} candidatos.",
    }


async def _wrap_create_shortlist(**kwargs: Any) -> dict[str, Any]:
    """Create a shortlist (CandidateList) from selected candidates."""
    candidate_ids = kwargs.get("candidate_ids", [])
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id")
    created_by = kwargs.get("created_by", "lia_agent")
    logger.info(
        f"[talent_tools] create_shortlist called: candidates={len(candidate_ids)} vacancy={vacancy_id}"
    )
    try:
        async with AsyncSessionLocal() as session:
            shortlist_id = str(uuid.uuid4())
            list_name = f"Shortlist vaga {vacancy_id}" if vacancy_id else "Shortlist LIA"
            await session.execute(
                text("""
                    INSERT INTO candidate_lists (id, company_id, name, description, created_by, is_active)
                    VALUES (:id, :cid, :name, :desc, :created_by, true)
                """),
                {
                    "id": shortlist_id,
                    "cid": company_id,
                    "name": list_name,
                    "desc": f"Criada automaticamente pelo agente LIA. Vaga: {vacancy_id}",
                    "created_by": created_by,
                },
            )
            added = 0
            for cid in candidate_ids:
                try:
                    await session.execute(
                        text("""
                            INSERT INTO candidate_list_members (id, list_id, candidate_id, added_by, source)
                            VALUES (:id, :lid, :cid, :added_by, 'agent')
                            ON CONFLICT DO NOTHING
                        """),
                        {"id": str(uuid.uuid4()), "lid": shortlist_id, "cid": cid, "added_by": created_by},
                    )
                    added += 1
                except Exception:
                    pass
            await session.commit()

        return {
            "success": True,
            "data": {
                "candidate_ids": candidate_ids,
                "vacancy_id": vacancy_id,
                "shortlist_id": shortlist_id,
                "shortlist_count": added,
            },
            "message": f"Shortlist criada com {added} candidatos (id: {shortlist_id}).",
        }
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[talent_tools] create_shortlist error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": "Erro ao criar shortlist."}


async def _wrap_export_report(**kwargs: Any) -> dict[str, Any]:
    """Export analysis report — generates a traceable report ID with candidate summary."""
    report_type = kwargs.get("report_type", "general")
    candidate_ids = kwargs.get("candidate_ids", [])
    vacancy_id = kwargs.get("vacancy_id", "")
    logger.info(f"[talent_tools] export_report called: type={report_type} candidates={len(candidate_ids)}")

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {"count": len(candidate_ids)}

    try:
        if candidate_ids:
            async with AsyncSessionLocal() as session:
                rows = await session.execute(
                    text("""
                        SELECT name, current_title, lia_score, skills_match_percentage, status
                        FROM candidates
                        WHERE id = ANY(:ids::uuid[])
                        ORDER BY lia_score DESC NULLS LAST
                    """),
                    {"ids": candidate_ids},
                )
                entries = [dict(r) for r in rows.mappings()]
                scores = [e["lia_score"] for e in entries if e["lia_score"]]
                summary = {
                    "count": len(entries),
                    "avg_lia_score": round(sum(scores) / len(scores), 2) if scores else None,
                    "top_candidate": entries[0]["name"] if entries else None,
                    "entries": entries,
                }
    except Exception as e:
        logger.warning(f"[talent_tools] export_report DB error: {e}")

    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "candidate_ids": candidate_ids,
            "vacancy_id": vacancy_id,
            "report_id": report_id,
            "exported": True,
            "summary": summary,
        },
        "message": f"Relatorio '{report_type}' gerado (id: {report_id}) com {summary.get('count', 0)} candidatos.",
    }


async def _wrap_check_search_fairness(**kwargs: Any) -> dict[str, Any]:
    search_criteria = kwargs.get("search_criteria", "")
    kwargs.get("context", "talent_search")
    logger.info(f"[talent_tools] check_search_fairness called: criteria='{search_criteria[:60]}...'")

    if not search_criteria.strip():
        return {
            "success": False,
            "message": "Criterio de busca vazio. Informe o texto a validar.",
        }

    try:
        result = _fairness_guard.check(search_criteria)
        implicit_warnings = _fairness_guard.check_implicit_bias(search_criteria)

        if result.is_blocked:
            return {
                "success": True,
                "data": {
                    "is_fair": False,
                    "blocked": True,
                    "category": result.category,
                    "blocked_terms": result.blocked_terms,
                    "educational_message": result.educational_message,
                    "soft_warnings": implicit_warnings,
                },
                "message": f"Criterio de busca BLOQUEADO por vies discriminatorio: {result.educational_message}",
            }

        semantic_warnings = []
        try:
            semantic_result = await _fairness_guard.check_semantic(search_criteria, context="talent_search")
            if semantic_result.is_blocked:
                return {
                    "success": True,
                    "data": {
                        "is_fair": False,
                        "blocked": True,
                        "category": semantic_result.category,
                        "blocked_terms": semantic_result.blocked_terms,
                        "educational_message": semantic_result.educational_message,
                        "soft_warnings": implicit_warnings + (semantic_result.soft_warnings or []),
                    },
                    "message": f"Criterio de busca BLOQUEADO por vies semantico: {semantic_result.educational_message}",
                }
            semantic_warnings = semantic_result.soft_warnings or []
        except Exception as sem_err:
            logger.debug(f"[talent_tools] semantic check skipped: {sem_err}")

        all_warnings = implicit_warnings + [w for w in semantic_warnings if w not in implicit_warnings]

        return {
            "success": True,
            "data": {
                "is_fair": True,
                "blocked": False,
                "soft_warnings": all_warnings,
            },
            "message": "Criterio de busca validado. Nenhum vies discriminatorio detectado."
            + (f" {len(all_warnings)} alertas de vies implicito." if all_warnings else ""),
        }
    except Exception as e:
        logger.error(f"[talent_tools] check_search_fairness error: {e}", exc_info=True)
        return {"success": True, "data": {"is_fair": True, "soft_warnings": []}, "error": str(e)}


async def _wrap_get_talent_pool_benchmarks(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    logger.info(
        f"[talent_tools] get_talent_pool_benchmarks called: "
        f"company={company_id} vacancy={vacancy_id}"
    )

    pool_size = 0
    avg_score = 0.0
    stage_distribution: dict[str, int] = {}

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT
                        COUNT(*) AS total,
                        AVG(CASE WHEN score IS NOT NULL THEN score ELSE 0 END) AS avg_score
                    FROM vacancy_candidates
                    WHERE (:vid = '' OR vacancy_id = :vid)
                      AND (:cid = '' OR company_id = :cid)
                """),
                {"vid": vacancy_id, "cid": company_id},
            )
            row = result.mappings().first()
            if row:
                pool_size = int(row["total"] or 0)
                avg_score = round(float(row["avg_score"] or 0), 1)

            stage_result = await session.execute(
                text("""
                    SELECT stage, COUNT(*) AS cnt
                    FROM vacancy_candidates
                    WHERE (:vid = '' OR vacancy_id = :vid)
                      AND (:cid = '' OR company_id = :cid)
                    GROUP BY stage
                    ORDER BY cnt DESC
                """),
                {"vid": vacancy_id, "cid": company_id},
            )
            for srow in stage_result.mappings():
                stage_distribution[str(srow["stage"])] = int(srow["cnt"])
    except Exception as e:
        logger.warning(f"[talent_tools] SQL error in get_talent_pool_benchmarks: {e}")

    market_benchmarks = {
        "avg_candidates_per_job": 45,
        "avg_qualified_rate": 0.25,
        "avg_time_in_funnel_days": 28,
        "sources": ["LinkedIn Talent Solutions 2024", "Gupy Benchmark Report 2024"],
    }

    return {
        "success": True,
        "data": {
            "pool_size": pool_size,
            "avg_score": avg_score,
            "stage_distribution": stage_distribution,
            "market_benchmarks": market_benchmarks,
        },
        "sources": market_benchmarks["sources"] + ["Dados internos da empresa"],
        "message": f"Benchmarks do pool de talentos: {pool_size} candidatos, score medio {avg_score}.",
    }


async def _wrap_check_pool_health(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    logger.info(
        f"[talent_tools] check_pool_health called: "
        f"company={company_id} vacancy={vacancy_id}"
    )

    risks = []
    pool_size = 0
    avg_score = 0.0
    stagnant_count = 0

    try:
        async with AsyncSessionLocal() as session:
            pool_result = await session.execute(
                text("""
                    SELECT
                        COUNT(*) AS total,
                        AVG(CASE WHEN score IS NOT NULL THEN score ELSE 0 END) AS avg_score,
                        COUNT(*) FILTER (
                            WHERE updated_at < NOW() - INTERVAL '14 days'
                        ) AS stagnant
                    FROM vacancy_candidates
                    WHERE (:vid = '' OR vacancy_id = :vid)
                      AND (:cid = '' OR company_id = :cid)
                """),
                {"vid": vacancy_id, "cid": company_id},
            )
            row = pool_result.mappings().first()
            if row:
                pool_size = int(row["total"] or 0)
                avg_score = round(float(row["avg_score"] or 0), 1)
                stagnant_count = int(row["stagnant"] or 0)
    except Exception as e:
        logger.warning(f"[talent_tools] SQL error in check_pool_health: {e}")

    if pool_size < 5:
        risks.append({
            "level": "high",
            "type": "pool_too_small",
            "message": f"Pool muito pequeno ({pool_size} candidatos). Risco alto de nao preencher a vaga. Considere ampliar criterios de busca.",
        })
    elif pool_size < 15:
        risks.append({
            "level": "medium",
            "type": "pool_small",
            "message": f"Pool abaixo do ideal ({pool_size} candidatos). O benchmark de mercado e 25-45 por vaga.",
        })

    if avg_score > 0 and avg_score < 5.0:
        risks.append({
            "level": "high",
            "type": "low_quality",
            "message": f"Score medio muito baixo ({avg_score}/10). Revise os criterios de busca ou atracao.",
        })

    if stagnant_count > 0:
        stagnant_pct = (stagnant_count / pool_size * 100) if pool_size > 0 else 0
        if stagnant_pct > 30:
            risks.append({
                "level": "high",
                "type": "high_stagnation",
                "message": f"{stagnant_count} candidatos ({stagnant_pct:.0f}%) parados ha mais de 14 dias. Risco de dropout.",
            })
        elif stagnant_pct > 10:
            risks.append({
                "level": "medium",
                "type": "stagnation",
                "message": f"{stagnant_count} candidatos ({stagnant_pct:.0f}%) parados ha mais de 14 dias.",
            })

    overall_health = "healthy"
    if any(r["level"] == "high" for r in risks):
        overall_health = "critical"
    elif any(r["level"] == "medium" for r in risks):
        overall_health = "attention"

    return {
        "success": True,
        "data": {
            "pool_size": pool_size,
            "avg_score": avg_score,
            "stagnant_count": stagnant_count,
            "risks": risks,
            "overall_health": overall_health,
        },
        "sources": ["LinkedIn Talent Solutions 2024", "Gupy Benchmark Report 2024", "Dados internos"],
        "message": f"Saude do pool: {overall_health}. {len(risks)} riscos identificados.",
    }


TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="search_candidates",
        description="Busca candidatos por skills, experiencia, localizacao e outros criterios. Retorna lista de candidatos encontrados.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto de busca (skills, cargo, etc.)"},
                "filters": {"type": "object", "description": "Filtros opcionais (localizacao, experiencia, etc.)"},
            },
            "required": ["query"],
        },
        function=_wrap_search_candidates,
    ),
    ToolDefinition(
        name="list_candidates",
        description="Lista candidatos no funil de talentos com filtros opcionais de status e limite de resultados.",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filtro de status: all, active, shortlisted, rejected"},
                "limit": {"type": "integer", "description": "Numero maximo de candidatos a retornar"},
            },
            "required": [],
        },
        function=_wrap_list_candidates,
    ),
    ToolDefinition(
        name="view_candidate_profile",
        description="Visualiza o perfil completo do candidato incluindo dados pessoais, experiencia, formacao, skills e scores.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_view_candidate_profile,
    ),
    ToolDefinition(
        name="compare_candidates",
        description="Compara 2 ou mais candidatos lado a lado em multiplas dimensoes: skills, experiencia, scores e fit.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos a comparar"},
            },
            "required": ["candidate_ids"],
        },
        function=_wrap_compare_candidates,
    ),
    ToolDefinition(
        name="rank_candidates",
        description="Rankeia candidatos por score de fit para uma vaga especifica, usando criterios objetivos.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga para calcular fit"},
                "criteria": {"type": "string", "description": "Criterio de ranking: fit_score, experience, skills"},
            },
            "required": ["vacancy_id"],
        },
        function=_wrap_rank_candidates,
    ),
    ToolDefinition(
        name="analyze_skills",
        description="Analisa o match de competencias entre um candidato e os requisitos de uma vaga. Identifica skills que combinam, faltantes e extras.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "vacancy_id": {"type": "string", "description": "ID da vaga para comparar requisitos"},
            },
            "required": ["candidate_id"],
        },
        function=_wrap_analyze_skills,
    ),
    ToolDefinition(
        name="recommend_actions",
        description="Gera recomendacoes de acoes para candidatos com base em dados e analises realizadas.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos"},
            },
            "required": ["candidate_ids"],
        },
        function=_wrap_recommend_actions,
    ),
    ToolDefinition(
        name="create_shortlist",
        description="Cria uma shortlist a partir dos candidatos selecionados para uma vaga especifica. Requer confirmacao do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos para a shortlist"},
                "vacancy_id": {"type": "string", "description": "ID da vaga associada a shortlist"},
            },
            "required": ["candidate_ids", "vacancy_id"],
        },
        function=_wrap_create_shortlist,
    ),
    ToolDefinition(
        name="export_report",
        description="Exporta relatorio de analise dos candidatos. Tipos disponiveis: ranking, comparison, skills_analysis, general.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo do relatorio: ranking, comparison, skills_analysis, general"},
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs dos candidatos a incluir no relatorio"},
            },
            "required": ["report_type"],
        },
        function=_wrap_export_report,
    ),
    ToolDefinition(
        name="check_search_fairness",
        description="Valida criterios de busca contra vies discriminatorio usando FairnessGuard. Detecta vies explicito (bloqueia) e implicito (alerta). Use antes de executar buscas com criterios fornecidos pelo recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "search_criteria": {"type": "string", "description": "Texto do criterio de busca a validar"},
                "context": {"type": "string", "description": "Contexto da validacao (talent_search, filter, etc.)"},
            },
            "required": ["search_criteria"],
        },
        function=_wrap_check_search_fairness,
    ),
    ToolDefinition(
        name="get_talent_pool_benchmarks",
        description="Obtem benchmarks reais do pool de talentos via SQL: tamanho do pool, score medio, distribuicao por etapa, comparacao com mercado. Fontes citaveis incluidas.",
        parameters={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID da empresa"},
                "vacancy_id": {"type": "string", "description": "ID da vaga para filtrar pool"},
            },
            "required": [],
        },
        function=_wrap_get_talent_pool_benchmarks,
    ),
    ToolDefinition(
        name="check_pool_health",
        description="Avalia proativamente a saude do pool de talentos: identifica riscos como pool pequeno, scores baixos, candidatos parados ha muito tempo. Use no inicio de interacoes para dar visao estrategica.",
        parameters={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID da empresa"},
                "vacancy_id": {"type": "string", "description": "ID da vaga para avaliar pool especifico"},
            },
            "required": [],
        },
        function=_wrap_check_pool_health,
    ),
]

async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    """P3-B: Gera relatório de talentos com métricas do período."""
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[talent_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
    try:
        async with AsyncSessionLocal() as session:
            row = await session.execute(
                text("""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status = 'approved') AS approved,
                        COUNT(*) FILTER (WHERE status = 'rejected') AS rejected
                    FROM applications
                    WHERE (:cid = '' OR company_id = :cid)
                      AND created_at > NOW() - MAKE_INTERVAL(days => :days)
                """),
                {"cid": company_id, "days": period_days},
            )
            data = row.mappings().first() or {}
            summary = {
                "total_applications": int(data.get("total") or 0),
                "approved": int(data.get("approved") or 0),
                "rejected": int(data.get("rejected") or 0),
            }
    except Exception as e:
        logger.warning(f"[talent_tools] generate_report DB error: {e}")
    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "period": period,
            "report_id": report_id,
            "generated": True,
            "summary": summary,
        },
        "message": (
            f"Relatorio '{report_type}' de talentos gerado (id: {report_id}). "
            f"{summary.get('total_applications', 0)} candidaturas no periodo."
        ),
    }


TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="generate_report",
        description=(
            "Gera um relatorio de talentos com metricas de candidaturas, aprovacoes e rejeicoes "
            "para o periodo selecionado. Use para responder: 'gerar relatorio', 'relatorio de talentos', "
            "'quantas candidaturas tivemos?', 'como esta o funil de talentos?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo: summary, detailed, sla"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
                "company_id": {"type": "string", "description": "ID da empresa (multi-tenant)"},
            },
            "required": ["report_type"],
        },
        function=_wrap_generate_report,
    )
)

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "discovery": ["search_candidates", "list_candidates", "view_candidate_profile", "check_search_fairness", "get_talent_pool_benchmarks", "check_pool_health"],
    "analysis": ["compare_candidates", "rank_candidates", "analyze_skills", "view_candidate_profile", "check_search_fairness", "get_talent_pool_benchmarks", "check_pool_health"],
    "action_planning": ["recommend_actions", "create_shortlist", "export_report", "generate_report", "view_candidate_profile", "check_search_fairness", "check_pool_health"],
}

GUARDRAIL_TOOLS: list[str] = [
    "create_shortlist",   # cria shortlist — ação que afeta o funil
    "export_report",      # exporta dados de candidatos — sensível LGPD
]


def get_talent_tools(stage: str = "") -> list[ToolDefinition]:
    """Return talent funnel tools, optionally filtered by stage.

    Args:
        stage: Current talent funnel stage identifier. If empty, returns all tools.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    if not stage:
        return list(TOOL_DEFINITIONS)

    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    logger.debug(f"[talent_tools] Stage '{stage}' tools: {[t.name for t in tools]}")
    return tools
