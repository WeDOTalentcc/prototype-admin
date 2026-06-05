"""
Sourcing Actions — candidate discovery, tagging, ranking, and management.

Handles: tag_candidates, rank_candidates, compare_candidates, search_candidates,
         suggest_candidates, add_candidate, export_candidates, favorite_candidate
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def execute_sourcing_action(
    action_id: str,
    params: dict[str, Any],
    context: dict[str, Any],
):
    if action_id == "tag_candidates":
        return await _tag_candidates(params, context)
    elif action_id == "rank_candidates":
        return await _rank_candidates(params, context)
    elif action_id == "compare_candidates":
        return await _compare_candidates(params, context)
    elif action_id == "search_candidates":
        return await _search_candidates(params, context)
    elif action_id == "suggest_candidates":
        return await _suggest_candidates(params, context)
    elif action_id == "add_candidate":
        return await _add_candidate(params, context)
    elif action_id == "export_candidates":
        return await _export_candidates(params, context)
    elif action_id == "favorite_candidate":
        return await _favorite_candidate(params, context)
    return None


async def _tag_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        candidate_ids = params.get("candidate_ids", [])
        tag = params.get("tag", "")
        company_id = context.get("company_id") if context else None

        if not candidate_ids or not tag:
            return ActionResult(
                status="error",
                message="Informe os candidatos e a tag a ser aplicada.",
                error_detail="Missing candidate_ids or tag",
                action_type="tag_candidates",
            )

        async with AsyncSessionLocal() as db:
            tagged_count = 0
            for cid in candidate_ids:
                if company_id:
                    authz = await db.execute(text(
                        "SELECT 1 FROM vacancy_candidates WHERE candidate_id = CAST(:cid AS uuid) AND company_id = :co LIMIT 1"
                    ), {"cid": str(cid), "co": str(company_id)})
                    if authz.fetchone() is None:
                        continue
                result = await db.execute(text("""
                    UPDATE candidates
                    SET tags = CASE
                        WHEN tags IS NULL THEN ARRAY[:tag]::text[]
                        WHEN :tag = ANY(tags) THEN tags
                        ELSE array_append(tags, :tag)
                    END, updated_at = NOW()
                    WHERE id = CAST(:cid AS uuid)
                """), {"tag": tag, "cid": str(cid)})
                tagged_count += result.rowcount
            await db.commit()

        from app.orchestrator.action_handlers._handler_hooks import log_action_audit, sync_to_rails
        for cid in candidate_ids:
            await log_action_audit("tag_candidates", company_id, candidate_id=str(cid))
            await sync_to_rails("candidate_tagged", "candidate", str(cid), {"tag": tag})

        return ActionResult(
            status="executed",
            message=f"Tag **\"{tag}\"** aplicada a **{tagged_count}** candidato(s).",
            data={
                "candidate_ids": candidate_ids,
                "tag": tag,
                "tagged_count": tagged_count,
                "tagged_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="tag_candidates",
        )
    except Exception as e:
        logger.warning(f"tag_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao aplicar tags nos candidatos.",
            error_detail=str(e),
            action_type="tag_candidates",
        )


async def _rank_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        company_id = context.get("company_id") if context else None
        limit = int(params.get("limit", 10))

        if not job_id:
            return ActionResult(
                status="error",
                message="Informe a vaga para rankear os candidatos.",
                error_detail="Missing job_id",
                action_type="rank_candidates",
            )

        async with AsyncSessionLocal() as db:
            sql = """
                SELECT c.id, c.name, c.current_title, c.seniority_level,
                       vc.stage, vc.score, vc.lia_score
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.vacancy_id = CAST(:job_id AS uuid)
            """
            bind: dict[str, Any] = {"job_id": str(job_id), "lim": limit}
            if company_id:
                sql += " AND vc.company_id = :co"
                bind["co"] = str(company_id)
            sql += " ORDER BY COALESCE(vc.lia_score, vc.score, 0) DESC LIMIT :lim"
            result = await db.execute(text(sql), bind)
            rows = result.fetchall()

        if not rows:
            return ActionResult(
                status="executed",
                message="Nenhum candidato encontrado nesta vaga para rankear.",
                data={"candidates": [], "job_id": job_id},
                action_type="rank_candidates",
            )

        lines = []
        ranked = []
        for i, row in enumerate(rows, 1):
            score = row.lia_score or row.score or 0
            lines.append(f"{i}. **{row.name}** — {row.current_title or 'N/A'} | Score: {score}% | Etapa: {row.stage or 'N/A'}")
            ranked.append({
                "rank": i, "id": str(row.id), "name": row.name,
                "score": score, "stage": row.stage,
            })

        return ActionResult(
            status="executed",
            message=f"**Ranking dos candidatos (Top {len(rows)}):**\n\n" + "\n".join(lines),
            data={"candidates": ranked, "job_id": job_id},
            action_type="rank_candidates",
        )
    except Exception as e:
        logger.warning(f"rank_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao rankear candidatos.",
            error_detail=str(e),
            action_type="rank_candidates",
        )


async def _compare_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        candidate_ids = params.get("candidate_ids", [])
        company_id = context.get("company_id") if context else None
        if len(candidate_ids) < 2:
            return ActionResult(
                status="error",
                message="Selecione pelo menos 2 candidatos para comparar.",
                error_detail="Less than 2 candidate_ids",
                action_type="compare_candidates",
            )

        async with AsyncSessionLocal() as db:
            placeholders = ", ".join(f"CAST(:id{i} AS uuid)" for i in range(len(candidate_ids)))
            bind_params: dict[str, Any] = {f"id{i}": str(cid) for i, cid in enumerate(candidate_ids)}
            sql = f"""
                SELECT c.id, c.name, c.current_title, c.current_company,
                       c.seniority_level, c.years_of_experience,
                       c.technical_skills, c.location_city, c.location_state
                FROM candidates c
                WHERE c.id IN ({placeholders})
            """
            if company_id:
                sql += " AND EXISTS (SELECT 1 FROM vacancy_candidates vc WHERE vc.candidate_id = c.id AND vc.company_id = :co)"
                bind_params["co"] = str(company_id)
            result = await db.execute(text(sql), bind_params)
            rows = result.fetchall()

        if len(rows) < 2:
            return ActionResult(
                status="error",
                message="Candidatos não encontrados para comparação.",
                error_detail="Less than 2 candidates found",
                action_type="compare_candidates",
            )

        lines = ["**Comparação de Candidatos:**\n"]
        compared = []
        for row in rows:
            skills = row.technical_skills[:5] if row.technical_skills else []
            skills_str = ", ".join(skills) if skills else "N/A"
            loc = f"{row.location_city or ''}/{row.location_state or ''}".strip("/") or "N/A"
            lines.append(
                f"- **{row.name}**: {row.current_title or 'N/A'} @ {row.current_company or 'N/A'} | "
                f"{row.seniority_level or 'N/A'} | {row.years_of_experience or '?'} anos | "
                f"Skills: {skills_str} | Local: {loc}"
            )
            compared.append({
                "id": str(row.id), "name": row.name,
                "title": row.current_title, "company": row.current_company,
                "seniority": row.seniority_level, "experience": row.years_of_experience,
                "skills": skills, "location": loc,
            })

        _rrp_blocks = []
        if compared:
            from app.shared.rrp_blocks import (
                ComparisonTableBlock, ComparisonColumn, ComparisonRow,
            )
            _table = ComparisonTableBlock(
                block_id="comparison_table:compare_candidates:"
                + "-".join(str(c.get("id")) for c in compared),
                role="support", layout="wide",
                title="Comparacao de candidatos", entity_type="candidate",
                columns=[
                    ComparisonColumn(key="name", label="Candidato", type="text"),
                    ComparisonColumn(key="title", label="Cargo", type="text"),
                    ComparisonColumn(key="seniority", label="Senioridade", type="text"),
                    ComparisonColumn(key="experience", label="Experiencia", type="text"),
                    ComparisonColumn(key="skills", label="Skills", type="text"),
                    ComparisonColumn(key="location", label="Local", type="text"),
                ],
                rows=[
                    ComparisonRow(
                        entity_id=str(c.get("id")),
                        cells={
                            "name": c.get("name") or ("ID " + str(c.get("id"))),
                            "title": c.get("title") or "-",
                            "seniority": c.get("seniority") or "-",
                            "experience": (str(c.get("experience")) + " anos")
                            if c.get("experience") else "-",
                            "skills": c.get("skills") or [],
                            "location": c.get("location") or "-",
                        },
                    )
                    for c in compared
                ],
                total_count=len(compared), shown_count=len(compared),
            )
            _rrp_blocks = [_table.model_dump(mode="json")]

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"candidates": compared, "response_blocks": _rrp_blocks},
            action_type="compare_candidates",
        )
    except Exception as e:
        logger.warning(f"compare_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao comparar candidatos.",
            error_detail=str(e),
            action_type="compare_candidates",
        )


async def _search_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        query = params.get("query", "")
        company_id = context.get("company_id") if context else None
        limit = int(params.get("limit", 10))

        if not query:
            return ActionResult(
                status="error",
                message="Informe o critério de busca.",
                error_detail="Missing query",
                action_type="search_candidates",
            )

        search_term = f"%{query}%"
        async with AsyncSessionLocal() as db:
            sql = """
                SELECT DISTINCT c.id, c.name, c.current_title, c.current_company,
                       c.location_city, c.seniority_level
                FROM candidates c
                LEFT JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                WHERE (
                    c.name ILIKE :q OR c.current_title ILIKE :q
                    OR c.current_company ILIKE :q
                    OR :raw_q = ANY(c.technical_skills)
                    OR c.location_city ILIKE :q
                )
            """
            bind = {"q": search_term, "raw_q": query}
            if company_id:
                sql += " AND vc.company_id = :co"
                bind["co"] = str(company_id)
            sql += " ORDER BY c.name LIMIT :lim"
            bind["lim"] = limit

            result = await db.execute(text(sql), bind)
            rows = result.fetchall()

        if not rows:
            return ActionResult(
                status="executed",
                message=f"Nenhum candidato encontrado para \"{query}\".",
                data={"candidates": [], "query": query},
                action_type="search_candidates",
            )

        lines = [f"**Resultados para \"{query}\" ({len(rows)} encontrados):**\n"]
        found = []
        for row in rows:
            lines.append(f"- **{row.name}** — {row.current_title or 'N/A'} @ {row.current_company or 'N/A'} | {row.location_city or 'N/A'}")
            found.append({
                "id": str(row.id), "name": row.name,
                "title": row.current_title, "company": row.current_company,
            })

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"candidates": found, "query": query},
            action_type="search_candidates",
        )
    except Exception as e:
        logger.warning(f"search_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao buscar candidatos.",
            error_detail=str(e),
            action_type="search_candidates",
        )


async def _suggest_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        company_id = context.get("company_id") if context else None
        limit = int(params.get("limit", 5))

        if not job_id:
            return ActionResult(
                status="error",
                message="Informe a vaga para sugerir candidatos.",
                error_detail="Missing job_id",
                action_type="suggest_candidates",
            )

        async with AsyncSessionLocal() as db:
            job_sql = "SELECT title, requirements, seniority_level, tags FROM job_vacancies WHERE id = CAST(:jid AS uuid)"
            job_bind: dict[str, Any] = {"jid": str(job_id)}
            if company_id:
                job_sql += " AND company_id = :co"
                job_bind["co"] = str(company_id)
            job_row = await db.execute(text(job_sql), job_bind)
            job = job_row.fetchone()

            if not job:
                return ActionResult(
                    status="error",
                    message="Vaga não encontrada.",
                    error_detail="Job not found",
                    action_type="suggest_candidates",
                )

            result = await db.execute(text("""
                SELECT c.id, c.name, c.current_title, c.seniority_level,
                       c.years_of_experience, c.location_city
                FROM candidates c
                WHERE c.id NOT IN (
                    SELECT vc.candidate_id FROM vacancy_candidates vc
                    WHERE vc.vacancy_id = CAST(:jid AS uuid)
                )
                AND (c.seniority_level = :sen OR :sen IS NULL)
                ORDER BY c.years_of_experience DESC NULLS LAST
                LIMIT :lim
            """), {"jid": str(job_id), "sen": job.seniority_level, "lim": limit})
            rows = result.fetchall()

        if not rows:
            return ActionResult(
                status="executed",
                message="Nenhum candidato sugerido encontrado para esta vaga.",
                data={"candidates": [], "job_id": job_id},
                action_type="suggest_candidates",
            )

        lines = [f"**Candidatos sugeridos para \"{job.title}\":**\n"]
        suggested = []
        for row in rows:
            lines.append(f"- **{row.name}** — {row.current_title or 'N/A'} | {row.seniority_level or 'N/A'} | {row.years_of_experience or '?'} anos")
            suggested.append({"id": str(row.id), "name": row.name, "title": row.current_title})

        return ActionResult(
            status="executed",
            message="\n".join(lines),
            data={"candidates": suggested, "job_id": job_id, "job_title": job.title},
            action_type="suggest_candidates",
        )
    except Exception as e:
        logger.warning(f"suggest_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao sugerir candidatos.",
            error_detail=str(e),
            action_type="suggest_candidates",
        )


async def _add_candidate(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        import uuid as uuid_mod

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        name = params.get("name", "")
        email = params.get("email", "")
        phone = params.get("phone")
        current_title = params.get("current_title")
        current_company = params.get("current_company")
        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        company_id = context.get("company_id") if context else None

        if not name or not email:
            return ActionResult(
                status="error",
                message="Nome e email são obrigatórios para cadastrar um candidato.",
                error_detail="Missing name or email",
                action_type="add_candidate",
            )

        candidate_id = str(uuid_mod.uuid4())
        async with AsyncSessionLocal() as db:
            existing = await db.execute(text(
                "SELECT id FROM candidates WHERE email = :email LIMIT 1"
            ), {"email": email})
            if existing.fetchone():
                return ActionResult(
                    status="error",
                    message=f"Já existe um candidato cadastrado com o email **{email}**.",
                    error_detail="Duplicate email",
                    action_type="add_candidate",
                )

            if not company_id:
                raise ValueError(
                    "company_id required for candidates INSERT "
                    "(multi-tenancy fail-closed per ADR-001)"
                )
            await db.execute(text("""
                INSERT INTO candidates (id, name, email, phone, current_title, current_company,
                    company_id, created_at, updated_at)
                VALUES (CAST(:id AS uuid), :name, :email, :phone, :title, :company,
                    CAST(:company_id AS uuid), NOW(), NOW())
            """), {
                "id": candidate_id, "name": name, "email": email,
                "phone": phone, "title": current_title, "company": current_company,
                "company_id": str(company_id),
            })

            if job_id and company_id:
                vc_id = str(uuid_mod.uuid4())
                await db.execute(text("""
                    INSERT INTO vacancy_candidates (id, vacancy_id, candidate_id, company_id, stage, status, created_at, updated_at)
                    VALUES (CAST(:id AS uuid), CAST(:vid AS uuid), CAST(:cid AS uuid), :co, 'Novos', 'active', NOW(), NOW())
                """), {"id": vc_id, "vid": str(job_id), "cid": candidate_id, "co": str(company_id)})

            await db.commit()

        from app.orchestrator.action_handlers._handler_hooks import log_action_audit, sync_to_rails
        await log_action_audit("add_candidate", company_id, candidate_id=candidate_id)
        await sync_to_rails("candidate_created", "candidate", candidate_id, {"name": name, "email": email})

        job_info = " e vinculado à vaga" if job_id else ""
        return ActionResult(
            status="executed",
            message=f"Candidato **{name}** cadastrado com sucesso{job_info}.",
            data={
                "candidate_id": candidate_id, "name": name, "email": email,
                "job_id": job_id, "created_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="add_candidate",
        )
    except Exception as e:
        logger.warning(f"add_candidate failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao cadastrar candidato.",
            error_detail=str(e),
            action_type="add_candidate",
        )


async def _export_candidates(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        job_id = params.get("job_id") or (context or {}).get("job_vacancy_id")
        company_id = context.get("company_id") if context else None

        async with AsyncSessionLocal() as db:
            if job_id:
                export_sql = """
                    SELECT c.name, c.email, c.phone, c.current_title, c.current_company,
                           vc.stage, vc.score, vc.lia_score
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.vacancy_id = CAST(:jid AS uuid)
                """
                export_bind: dict[str, Any] = {"jid": str(job_id)}
                if company_id:
                    export_sql += " AND vc.company_id = :co"
                    export_bind["co"] = str(company_id)
                export_sql += " ORDER BY c.name"
                result = await db.execute(text(export_sql), export_bind)
            elif company_id:
                result = await db.execute(text("""
                    SELECT DISTINCT c.name, c.email, c.phone, c.current_title, c.current_company,
                           vc.stage, vc.score, vc.lia_score
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.company_id = :co
                    ORDER BY c.name
                    LIMIT 100
                """), {"co": str(company_id)})
            else:
                return ActionResult(
                    status="error",
                    message="Não foi possível determinar o escopo da exportação.",
                    error_detail="No job_id or company_id",
                    action_type="export_candidates",
                )
            rows = result.fetchall()

        if not rows:
            return ActionResult(
                status="executed",
                message="Nenhum candidato encontrado para exportar.",
                data={"candidates": [], "count": 0},
                action_type="export_candidates",
            )

        exported = []
        for row in rows:
            exported.append({
                "name": row.name, "email": row.email, "phone": row.phone,
                "title": row.current_title, "company": row.current_company,
                "stage": row.stage, "score": row.lia_score or row.score,
            })

        return ActionResult(
            status="executed",
            message=f"**{len(exported)} candidatos** prontos para exportação. Os dados foram preparados no formato estruturado.",
            data={"candidates": exported, "count": len(exported), "format": "json", "job_id": job_id},
            action_type="export_candidates",
        )
    except Exception as e:
        logger.warning(f"export_candidates failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao exportar candidatos.",
            error_detail=str(e),
            action_type="export_candidates",
        )


async def _favorite_candidate(params: dict[str, Any], context: dict[str, Any]):
    from app.orchestrator.action_executor import ActionResult
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        from app.orchestrator.action_handlers._handler_hooks import log_action_audit, resolve_candidate_by_name, sync_to_rails

        candidate_id = params.get("candidate_id", "")
        candidate_name = params.get("candidate_name", "o candidato")
        user_id = context.get("user_id") if context else None
        company_id = context.get("company_id") if context else None

        if not candidate_id and candidate_name:
            resolved = await resolve_candidate_by_name(candidate_name, company_id)
            if resolved:
                candidate_id = resolved["id"]
                candidate_name = resolved["name"]

        if not candidate_id:
            return ActionResult(
                status="error",
                message="Informe o candidato a ser favoritado.",
                error_detail="Missing candidate_id",
                action_type="favorite_candidate",
            )

        async with AsyncSessionLocal() as db:
            if company_id:
                authz = await db.execute(text(
                    "SELECT 1 FROM vacancy_candidates WHERE candidate_id = CAST(:cid AS uuid) AND company_id = :co LIMIT 1"
                ), {"cid": candidate_id, "co": str(company_id)})
                if authz.fetchone() is None:
                    return ActionResult(
                        status="error",
                        message="Sem permissão para favoritar este candidato.",
                        error_detail="Candidate does not belong to caller's company",
                        action_type="favorite_candidate",
                    )

            await db.execute(text("""
                UPDATE candidates
                SET lia_insights = COALESCE(lia_insights, '{}'::jsonb) || '{"favorited": true}'::jsonb,
                    updated_at = NOW()
                WHERE id = CAST(:cid AS uuid)
            """), {"cid": candidate_id})
            await db.commit()

        await log_action_audit("favorite_candidate", company_id, candidate_id=str(candidate_id))
        await sync_to_rails("candidate_favorited", "candidate", str(candidate_id))

        return ActionResult(
            status="executed",
            message=f"**{candidate_name}** adicionado(a) aos favoritos.",
            data={
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "favorited": True,
                "favorited_at": datetime.utcnow().isoformat(),
                "simulated": False,
            },
            action_type="favorite_candidate",
        )
    except Exception as e:
        logger.warning(f"favorite_candidate failed: {e}")
        from app.orchestrator.action_executor import ActionResult
        return ActionResult(
            status="error",
            message="Erro ao favoritar candidato.",
            error_detail=str(e),
            action_type="favorite_candidate",
        )
