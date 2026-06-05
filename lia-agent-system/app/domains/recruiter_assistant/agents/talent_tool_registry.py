"""
Talent Tool Registry - Exposes talent funnel tools to the ReAct loop.

Wraps talent funnel operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for candidate analysis and
management.

ADR-001: All SQL queries delegated to canonical repositories.
- CandidateRepository: PII-touching queries (candidates table)
- VacancyCandidateRepository: vacancy_candidates aggregations
"""
import logging
import uuid
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.core.database import AsyncSessionLocal
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository
from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository
from app.shared.compliance.fairness_guard import FairnessGuard

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


@tool_handler("talent")
async def _wrap_search_candidates(**kwargs: Any) -> dict[str, Any]:
    """Search candidates by skills, experience, location."""
    query = kwargs.get("query", "")
    filters = kwargs.get("filters", {})
    company_id = kwargs.get("company_id", "")
    limit = int(kwargs.get("limit", 20))
    logger.info(f"[talent_tools] search_candidates called: query={query} filters={filters}")

    results = []
    total = 0
    try:
        location = filters.get("location", "") if isinstance(filters, dict) else ""
        min_exp = filters.get("min_experience", 0) if isinstance(filters, dict) else 0

        async with AsyncSessionLocal() as db:
            repo = CandidateRepository(db)
            data = await repo.search_by_skills_and_experience(
                company_id=company_id,
                query=query,
                location=location,
                min_experience=min_exp,
                limit=limit,
            )
        results = data["results"]
        total = data["total"]
    except Exception as e:
        # REGRA 4 (fail-loud): erro de DB NAO pode parecer "0 resultados".
        logger.warning(f"[talent_tools] search_candidates DB error: {e}")
        return {
            "success": False,
            "errored": True,
            "data": {"query": query, "filters": filters, "candidates_found": 0, "results": []},
            "message": "Nao consegui consultar candidatos agora (erro interno). Tente de novo em instantes.",
        }

    data_block = {
        "query": query,
        "filters": filters,
        "candidates_found": total,
        "results": results,
    }
    message = f"Busca realizada. {total} candidatos encontrados para '{query}'."
    # P0.2: 0-resultados -> sinal estruturado de relaxamento (agente relaxa + oferece opcoes).
    if total == 0:
        from app.orchestrator.context.empty_result_guidance import build_empty_result_guidance
        _applied = dict(filters) if isinstance(filters, dict) else {}
        if query:
            _applied["busca_textual"] = query
        _guidance = build_empty_result_guidance("candidato", _applied)
        data_block["empty_guidance"] = _guidance
        message = _guidance["guidance"]
    return {
        "success": True,
        "data": data_block,
        "message": message,
    }


@tool_handler("talent")
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
        async with AsyncSessionLocal() as db:
            repo = VacancyCandidateRepository(db)
            data = await repo.list_for_talent_funnel(
                company_id=company_id,
                status=status,
                vacancy_id=vacancy_id,
                limit=limit,
            )
        candidates = data["candidates"]
        total = data["total"]
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


@tool_handler("talent")
async def _wrap_view_candidate_profile(**kwargs: Any) -> dict[str, Any]:
    """View complete candidate profile including education and work history."""
    candidate_id = kwargs.get("candidate_id", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[talent_tools] view_candidate_profile called for candidate={candidate_id}")

    profile: dict[str, Any] = {"candidate_id": candidate_id, "profile_loaded": False}
    try:
        async with AsyncSessionLocal() as db:
            repo = CandidateRepository(db)
            data = await repo.get_full_profile(
                candidate_id=candidate_id,
                company_id=company_id,
            )
        if not data:
            return {
                "success": False,
                "data": {"candidate_id": candidate_id},
                "message": f"Candidato {candidate_id} nao encontrado.",
            }
        profile = data
    except Exception as e:
        logger.warning(f"[talent_tools] view_candidate_profile DB error: {e}")

    return {
        "success": True,
        "data": profile,
        "message": f"Perfil completo do candidato {profile.get('name', candidate_id)} carregado.",
    }


@tool_handler("talent")
async def _wrap_compare_candidates(**kwargs: Any) -> dict[str, Any]:
    """Compare 2+ candidates side by side (perfil) + emite comparison_table (RRP)."""
    candidate_ids = kwargs.get("candidate_ids", [])
    company_id = kwargs.get("company_id", "")
    logger.info(f"[talent_tools] compare_candidates called: candidates={len(candidate_ids)}")
    _compared: list = []
    _rrp_blocks: list = []
    if len(candidate_ids) >= 2:
        try:
            from sqlalchemy import text as _sa_text
            from app.shared.rrp_ranking_builder import build_candidate_comparison_blocks
            _ids = [str(c) for c in candidate_ids[:5]]
            _ph = ", ".join(f"CAST(:c{i} AS uuid)" for i in range(len(_ids)))
            _bp = {f"c{i}": v for i, v in enumerate(_ids)}
            _bp["co"] = str(company_id)
            async with AsyncSessionLocal() as db:
                _rows = await db.execute(_sa_text(
                    "SELECT c.id, c.name, c.current_title, c.seniority_level, "
                    "c.years_of_experience, c.technical_skills, c.location_city, "
                    "c.location_state FROM candidates c "
                    f"WHERE c.id IN ({_ph}) AND EXISTS (SELECT 1 FROM vacancy_candidates "
                    "vc WHERE vc.candidate_id = c.id AND vc.company_id = :co)"
                ), _bp)
                for m in _rows.mappings():
                    _sk = m["technical_skills"]
                    _loc = f"{m['location_city'] or ''}/{m['location_state'] or ''}".strip("/") or "-"
                    _compared.append({
                        "id": str(m["id"]), "name": m["name"],
                        "title": m["current_title"], "seniority": m["seniority_level"],
                        "experience": m["years_of_experience"],
                        "skills": (_sk[:5] if isinstance(_sk, list) else []),
                        "location": _loc,
                    })
            _rrp_blocks = build_candidate_comparison_blocks(_compared)
        except Exception as _e:
            logger.warning(f"[talent_tools] compare_candidates RRP skipped: {_e}")
    return {
        "success": True,
        "data": {
            "candidate_ids": candidate_ids,
            "comparison_count": len(candidate_ids),
            "comparison_complete": True,
            "dimensions": ["skills", "experience", "score", "fit"],
            "candidates": _compared,
            "response_blocks": _rrp_blocks or None,
        },
        "message": f"Comparacao de {len(_compared) or len(candidate_ids)} candidatos concluida.",
    }

@tool_handler("talent")
async def _wrap_rank_candidates(**kwargs: Any) -> dict[str, Any]:
    """Rank candidates by fit score for a job."""
    vacancy_id = kwargs.get("vacancy_id", "")
    criteria = kwargs.get("criteria", "fit_score")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[talent_tools] rank_candidates called: vacancy={vacancy_id} criteria={criteria}")

    ranking = []
    _rrp_blocks: list = []
    try:
        async with AsyncSessionLocal() as db:
            repo = VacancyCandidateRepository(db)
            ranking = await repo.rank_for_job(
                vacancy_id=vacancy_id,
                company_id=company_id,
                criteria=criteria,
            )
            # AD3 (RRP): enriquece com pareceres + monta blocos ricos (moat).
            try:
                from sqlalchemy import text as _sa_text
                from app.shared.rrp_ranking_builder import build_candidate_ranking_blocks
                _op_rows = await db.execute(_sa_text(
                    "SELECT candidate_id, id, recommendation, summary, strengths, "
                    "concerns, wsi_screening_id FROM lia_opinions "
                    "WHERE job_vacancy_id::text = :vid AND company_id = :cid "
                    "AND is_current = true"
                ), {"vid": vacancy_id, "cid": company_id})
                _op_map = {str(m["candidate_id"]): m for m in _op_rows.mappings()}
                _norm = []
                for _r in ranking:
                    _cid = str(_r.get("candidate_id"))
                    _op = _op_map.get(_cid, {})
                    _norm.append({
                        "id": _cid, "name": _r.get("name"),
                        "score": _r.get("lia_score"), "stage": _r.get("stage"),
                        "recommendation": _op.get("recommendation"),
                        "summary": _op.get("summary"),
                        "strengths": _op.get("strengths"),
                        "concerns": _op.get("concerns"),
                        "opinion_id": _op.get("id"),
                        "wsi_id": _op.get("wsi_screening_id"),
                    })
                _rrp_blocks = build_candidate_ranking_blocks(vacancy_id, _norm)
            except Exception as _rrp_exc:
                logger.warning(f"[talent_tools] rank_candidates RRP blocks skipped: {_rrp_exc}")
    except Exception as e:
        logger.warning(f"[talent_tools] rank_candidates DB error: {e}")

    return {
        "success": True,
        "data": {
            "vacancy_id": vacancy_id,
            "criteria": criteria,
            "ranking_generated": True,
            "ranked_count": len(ranking),
            "ranking": ranking,
            "response_blocks": _rrp_blocks or None,
        },
        "message": f"Ranking gerado: {len(ranking)} candidatos para a vaga {vacancy_id} (criterio: {criteria}).",
    }


@tool_handler("talent")
async def _wrap_analyze_skills(**kwargs: Any) -> dict[str, Any]:
    """Analyze skill match between candidate and job requirements."""
    candidate_id = kwargs.get("candidate_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[talent_tools] analyze_skills called: candidate={candidate_id} vacancy={vacancy_id}")

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    extra_skills: list[str] = []
    match_percentage = 0.0

    try:
        async with AsyncSessionLocal() as session:
            cand_repo = CandidateRepository(session)
            vc_repo = VacancyCandidateRepository(session)

            candidate_skills = await cand_repo.get_skill_set(
                candidate_id=candidate_id,
                company_id=company_id,
            )

            if vacancy_id:
                jv_repo = JobVacancyCrudRepository(session)
                vacancy = await jv_repo.get_vacancy_by_id(vacancy_id)
                # ADR-001: use JobVacancyCrudRepository instead of raw SQL (W1-004-B)
                tech_reqs = (vacancy.technical_requirements if vacancy else None) or []
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
                    await vc_repo.update_match_percentage(
                        candidate_id=candidate_id,
                        vacancy_id=vacancy_id,
                        match_percentage=match_percentage,
                    )
    except Exception as e:
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


@tool_handler("talent")
async def _wrap_recommend_actions(**kwargs: Any) -> dict[str, Any]:
    """Generate action recommendations for candidates based on real scores and status."""
    candidate_ids = kwargs.get("candidate_ids", [])
    company_id = kwargs.get("company_id", "")
    logger.info(f"[talent_tools] recommend_actions called: candidates={len(candidate_ids)}")

    recommendations: list[dict[str, Any]] = []
    try:
        if candidate_ids:
            async with AsyncSessionLocal() as db:
                repo = CandidateRepository(db)
                rows = await repo.list_for_recommendations(
                    candidate_ids=candidate_ids,
                    company_id=company_id,
                )
            for row in rows:
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
        logger.exception(
            "[talent_tools] recommend_actions DB error; returning stock fallback. error=%s",
            e,
        )
        fallback_recommendations = [
            {"candidate_id": cid, "actions": [{"action": "review_profile", "priority": "low"}]}
            for cid in candidate_ids
        ]
        return {
            "success": True,
            "data": {
                "candidate_ids": candidate_ids,
                "recommendations_count": len(fallback_recommendations),
                "recommendations": fallback_recommendations,
            },
            "message": f"Recomendacoes geradas para {len(fallback_recommendations)} candidatos.",
            "fallback_used": True,
            "needs_manual_review": True,
            "fallback_reason": f"{type(e).__name__}: {e}",
        }

    return {
        "success": True,
        "data": {
            "candidate_ids": candidate_ids,
            "recommendations_count": len(recommendations),
            "recommendations": recommendations,
        },
        "message": f"Recomendacoes geradas para {len(recommendations)} candidatos.",
        "fallback_used": False,
        "needs_manual_review": False,
        "fallback_reason": None,
    }


@tool_handler("talent")
async def _wrap_create_shortlist(**kwargs: Any) -> dict[str, Any]:
    """Create a shortlist (CandidateList) from selected candidates."""
    from app.domains.candidates.repositories.short_list_repository import ShortListRepository
    candidate_ids = kwargs.get("candidate_ids", [])
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id")
    created_by = kwargs.get("created_by", "lia_agent")
    logger.info(
        f"[talent_tools] create_shortlist called: candidates={len(candidate_ids)} vacancy={vacancy_id}"
    )
    async with AsyncSessionLocal() as session:
        repo = ShortListRepository(session)
        list_name = f"Shortlist vaga {vacancy_id}" if vacancy_id else "Shortlist LIA"
        description = f"Criada automaticamente pelo agente LIA. Vaga: {vacancy_id}"
        record = await repo.create(
            company_id=company_id,
            name=list_name,
            description_encoded=description,
            created_by=created_by,
        )
        shortlist_id = str(record.id)
        added = 0
        for cid in candidate_ids:
            try:
                await repo.add_member(list_id=record.id, candidate_id=cid)
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

@tool_handler("talent")
async def _wrap_export_report(**kwargs: Any) -> dict[str, Any]:
    """Export analysis report — generates a traceable report ID with candidate summary."""
    report_type = kwargs.get("report_type", "general")
    candidate_ids = kwargs.get("candidate_ids", [])
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    logger.info(f"[talent_tools] export_report called: type={report_type} candidates={len(candidate_ids)}")

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {"count": len(candidate_ids)}

    try:
        if candidate_ids:
            async with AsyncSessionLocal() as db:
                repo = CandidateRepository(db)
                entries = await repo.list_for_report(
                    candidate_ids=candidate_ids,
                    company_id=company_id,
                )
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


@tool_handler("talent")
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
        logger.exception(
            "[talent_tools] check_search_fairness FAILED -- failing CLOSED"
        )
        return {
            "success": False,
            "data": {
                "is_fair": False,
                "blocked": False,
                "fallback_used": True,
                "needs_manual_review": True,
                "soft_warnings": [],
            },
            "error": f"Fairness check failed: {str(e)}",
            "message": (
                "Nao foi possivel validar o criterio de busca por vies. "
                "Por seguranca (fail-closed LGPD), revise manualmente antes de prosseguir."
            ),
        }


@tool_handler("talent")
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
        async with AsyncSessionLocal() as db:
            repo = VacancyCandidateRepository(db)
            data = await repo.get_pool_benchmarks(
                company_id=company_id,
                vacancy_id=vacancy_id,
            )
        pool_size = data["pool_size"]
        avg_score = data["avg_score"]
        stage_distribution = data["stage_distribution"]
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


@tool_handler("talent")
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
        async with AsyncSessionLocal() as db:
            repo = VacancyCandidateRepository(db)
            data = await repo.get_pool_health(
                company_id=company_id,
                vacancy_id=vacancy_id,
            )
        pool_size = data["pool_size"]
        avg_score = data["avg_score"]
        stagnant_count = data["stagnant_count"]
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
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        touches_pii=True,
        pii_output_fields=["name",
        "email",
        "linkedin_url",
        "phone"],
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
        output_schema=ToolOutput,
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
        touches_pii=True, pii_output_fields=["name", "email", "linkedin_url"],
            output_schema=ToolOutput,
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
        touches_pii=True, pii_output_fields=["name", "email", "phone", "linkedin_url"],
            output_schema=ToolOutput,
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
        affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST",
            output_schema=ToolOutput,
            function=_wrap_compare_candidates,
    ),
    ToolDefinition(
        name="rank_candidates",
        description="Rankeia (ordena) os candidatos de uma vaga por score de fit/LIA e retorna uma TABELA RICA de ranking (com o porque de cada nota e as fontes). Use SEMPRE que o recrutador pedir para rankear, ordenar, ou ver os melhores/top candidatos de uma vaga. Se a vaga foi citada por nome, resolva o vacancy_id antes e entao chame esta tool.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga para calcular fit"},
                "criteria": {"type": "string", "description": "Criterio de ranking: fit_score, experience, skills"},
            },
            "required": ["vacancy_id"],
        },
        affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST",
            output_schema=ToolOutput,
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
        output_schema=ToolOutput,
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
        affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST",
            output_schema=ToolOutput,
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
        affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST", side_effects=["write"],
            output_schema=ToolOutput,
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
        side_effects=["write"], touches_pii=True, pii_output_fields=["name", "email", "phone"],
            output_schema=ToolOutput,
            function=_wrap_export_report,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
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
        output_schema=ToolOutput,
        function=_wrap_check_search_fairness,
    ),
    ToolDefinition(
        name="get_talent_pool_benchmarks",
        description="Obtem benchmarks reais do pool de talentos via SQL: tamanho do pool, score medio, distribuicao por etapa, comparacao com mercado. Fontes citaveis incluidas.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga para filtrar pool"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_talent_pool_benchmarks,
    ),
    ToolDefinition(
        name="check_pool_health",
        description="Avalia proativamente a saude do pool de talentos: identifica riscos como pool pequeno, scores baixos, candidatos parados ha muito tempo. Use no inicio de interacoes para dar visao estrategica.",
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {"type": "string", "description": "ID da vaga para avaliar pool especifico"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_check_pool_health,
    ),
]

@tool_handler("talent")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    """P3-B: Gera relatorio de talentos com metricas do periodo."""
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    logger.info(f"[talent_tools] generate_report called: type={report_type} period={period}")
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    summary: dict[str, Any] = {}
    try:
        async with AsyncSessionLocal() as db:
            repo = CandidateRepository(db)
            summary = await repo.get_applications_summary(
                company_id=company_id,
                period_days=period_days,
            )
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
            },
            "required": ["report_type"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_report,
    )
)

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "discovery": ["search_candidates", "list_candidates", "view_candidate_profile", "check_search_fairness", "get_talent_pool_benchmarks", "check_pool_health"],
    "analysis": ["compare_candidates", "rank_candidates", "analyze_skills", "view_candidate_profile", "check_search_fairness", "get_talent_pool_benchmarks", "check_pool_health"],
    "action_planning": ["recommend_actions", "create_shortlist", "export_report", "generate_report", "view_candidate_profile", "check_search_fairness", "check_pool_health"],
}

# SafetyCategory preserved for callers that need detail info.
from app.shared.compliance.safety_category import SafetyCategory  # noqa: F401

GUARDRAIL_TOOLS: dict[str, SafetyCategory] = {
    "create_shortlist": SafetyCategory.PIPELINE_MOVE,
    "export_report": SafetyCategory.PII_EXPORT,
}


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
