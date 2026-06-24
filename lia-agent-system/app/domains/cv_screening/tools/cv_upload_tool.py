"""
CV Upload Tool — Phase 2

Provides tools for:
  1. parse_and_create_candidate  — AI-parse raw CV text → create Candidate in DB
  2. add_to_vacancy              — add existing Candidate to a JobVacancy pipeline
  3. create_and_screen_candidate — end-to-end: parse CV text → create → add to vacancy → BARS score
"""
import logging

from app.shared.robustness.document_scanner import scan_document
import uuid
from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.shared.tool_guards import validate_uuid_params

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_context(kwargs: dict[str, Any]):
    return kwargs.get("context") or kwargs.get("_context")


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%Y", "%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except (ValueError, TypeError):
            pass
    return None


# ---------------------------------------------------------------------------
# Tool: parse_and_create_candidate
# ---------------------------------------------------------------------------

async def parse_and_create_candidate(
    cv_text: str,
    vacancy_title: str | None = None,
    vacancy_id: str | None = None,
    source: str = "cv_upload",
    **kwargs,
) -> dict[str, Any]:
    """
    Parse raw CV text with AI and create a new Candidate record in the database.

    Returns candidate_id on success so downstream tasks can use it.
    """
    context = _extract_context(kwargs)
    company_id = getattr(context, "company_id", None) if context else None
    user_id = getattr(context, "user_id", "system") if context else "system"

    if not cv_text or len(cv_text.strip()) < 30:
        return {
            "success": False,
            "message": "Texto do CV muito curto ou vazio.",
            "error": "cv_text_too_short",
        }

    logger.info(f"📄 Parsing CV for create (company={company_id}, user={user_id})")

    try:
        # Build a mock UploadFile-compatible object

        from app.domains.cv_screening.services.cv_parser import CVParserService

        class _FakeUpload:
            filename = "cv_from_chat.txt"
            content_type = "text/plain"
            _content = cv_text.encode("utf-8", errors="ignore")

            async def read(self):
                return self._content

        parser = CVParserService()
        scan_result = scan_document(cv_text)
        if scan_result.threats:
            logger.warning("CV upload tool scan threats: %s", scan_result.threats)
        cv_text = scan_result.sanitized_text
        parsed = await parser.extract_with_ai(cv_text)

        # ----------------------------------------------------------------
        # Create Candidate in DB
        # ----------------------------------------------------------------
        from sqlalchemy import func, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate

        async with AsyncSessionLocal() as db:
            # Duplicate check — skip creation if email already exists.
            # Task #1229: scope the uniqueness check by company_id when the
            # caller injected a tenant context, so the same e-mail can exist in
            # different tenants (defense-in-depth on top of Postgres RLS).
            if parsed.email:
                dup_conditions = [func.lower(Candidate.email) == parsed.email.lower()]
                if company_id:
                    dup_conditions.append(Candidate.company_id == company_id)
                dup = await db.execute(
                    select(Candidate).where(*dup_conditions)
                )
                existing = dup.scalar_one_or_none()
                if existing:
                    cand_id = str(existing.id)
                    logger.info(f"Duplicate candidate found by email: {cand_id}")
                    return {
                        "success": True,
                        "duplicate": True,
                        "candidate_id": cand_id,
                        "candidate_name": getattr(existing, "name", parsed.full_name),
                        "message": (
                            f"⚠️ Candidato já cadastrado com este e-mail: "
                            f"**{getattr(existing, 'name', parsed.full_name)}** (id: `{cand_id[:8]}...`). "
                            f"Usando cadastro existente."
                        ),
                        "parsed": {
                            "name": parsed.full_name,
                            "email": parsed.email,
                            "skills": parsed.skills[:10],
                        },
                    }

            new_candidate = Candidate(
                id=uuid.uuid4(),
                # Task #1229: persist tenant ownership so the candidate is
                # isolated per company (RLS + explicit column) — was previously
                # created with a NULL company_id (cross-tenant leak risk).
                company_id=company_id,
                name=parsed.full_name or "Candidato sem nome",
                email=parsed.email,
                phone=parsed.phone,
                linkedin_url=parsed.linkedin,
                github_url=parsed.github,
                portfolio_url=parsed.portfolio,
                current_title=parsed.current_title,
                seniority_level=parsed.seniority_level,
                technical_skills=parsed.skills or [],
                soft_skills=parsed.soft_skills or [],
                certifications=parsed.certifications or [],
                interests=parsed.interests or [],
                date_of_birth=_parse_date(parsed.date_of_birth),
                is_active=True,
                source=source,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Parse location if available
            if parsed.location:
                parts = [p.strip() for p in parsed.location.split(",")]
                if len(parts) >= 1:
                    new_candidate.city = parts[0]
                if len(parts) >= 2:
                    new_candidate.state = parts[1]
                if len(parts) >= 3:
                    new_candidate.country = parts[2]

            db.add(new_candidate)
            await db.commit()
            await db.refresh(new_candidate)

            cand_id = str(new_candidate.id)
            cand_name = getattr(new_candidate, "name", parsed.full_name)
            logger.info(f"✅ Candidate created: {cand_id} ({cand_id})")

            skills_preview = ", ".join(parsed.skills[:5]) if parsed.skills else "Não identificadas"
            vacancy_info = f" para a vaga **{vacancy_title}**" if vacancy_title else ""

            return {
                "success": True,
                "duplicate": False,
                "candidate_id": cand_id,
                "candidate_name": cand_name,
                "vacancy_id": vacancy_id,
                "vacancy_title": vacancy_title,
                "message": (
                    f"✅ Candidato **{cand_name}** cadastrado com sucesso{vacancy_info}.\n"
                    f"- **Cargo atual:** {parsed.current_title or 'Não identificado'}\n"
                    f"- **Senioridade:** {parsed.seniority_level or 'Não identificado'}\n"
                    f"- **Skills:** {skills_preview}\n"
                    f"- **Confiança da extração:** {int((parsed.confidence_score or 0.7) * 100)}%"
                ),
                "parsed": {
                    "name": parsed.full_name,
                    "email": parsed.email,
                    "phone": parsed.phone,
                    "current_title": parsed.current_title,
                    "seniority_level": parsed.seniority_level,
                    "skills": parsed.skills[:10],
                    "confidence_score": parsed.confidence_score,
                },
            }

    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ parse_and_create_candidate error: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao cadastrar candidato a partir do CV: {str(e)}",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Tool: add_to_vacancy  (thin wrapper for plan pipelines)
# ---------------------------------------------------------------------------

async def add_to_vacancy(
    candidate_id: str,
    vacancy_id: str | None = None,
    vacancy_title: str | None = None,
    initial_stage: str = "Triagem",
    source: str = "cv_upload",
    **kwargs,
) -> dict[str, Any]:
    """
    Add a candidate to a vacancy pipeline.

    Resolves the vacancy by ID or by title if ID is not provided.
    Returns vacancy_candidate_id for downstream WSI triggering.
    """
    context = _extract_context(kwargs)
    company_id = getattr(context, "company_id", None) if context else None
    user_id = getattr(context, "user_id", "system") if context else "system"

    logger.info(
        f"➕ add_to_vacancy: cand={str(candidate_id)[:8]}... "
        f"vacancy_id={vacancy_id} vacancy_title={vacancy_title}"
    )

    err = validate_uuid_params(candidate_id=candidate_id)
    if err:
        return err
    if vacancy_id:
        err = validate_uuid_params(vacancy_id=vacancy_id)
        if err:
            return err

    try:
        from sqlalchemy import and_, func, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        async with AsyncSessionLocal() as db:
            # Resolve candidate
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). TODO(harness): add
            # Candidate.company_id == company_id filter via tool_handler kwargs.
            cand_res = await db.execute(select(Candidate).where(Candidate.id == UUID(candidate_id)))
            candidate = cand_res.scalar_one_or_none()
            if not candidate:
                return {
                    "success": False,
                    "message": f"Candidato não encontrado: {candidate_id}",
                    "error": "candidate_not_found",
                }

            # Resolve vacancy
            job = None
            if vacancy_id:
                # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id ==
                # company_id is conditionally appended below.
                q = select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
                if company_id:
                    q = q.where(JobVacancy.company_id == company_id)
                res = await db.execute(q)
                job = res.scalar_one_or_none()

            if not job and vacancy_title:
                # TENANT-EXEMPT: dynamic builder — JobVacancy.company_id ==
                # company_id is conditionally appended below.
                q = (
                    select(JobVacancy)
                    .where(func.lower(JobVacancy.title).contains(vacancy_title.strip().lower()))
                )
                if company_id:
                    q = q.where(JobVacancy.company_id == company_id)
                q = q.limit(1)
                res = await db.execute(q)
                job = res.scalar_one_or_none()

            if not job:
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {vacancy_title or vacancy_id}",
                    "error": "vacancy_not_found",
                }

            job_id = str(job.id)
            job_title_str = getattr(job, "title", "Vaga")

            # Duplicate check
            # TENANT-EXEMPT: tool invoked via tool_registry; tenant boundary
            # enforced by Postgres RLS (Task #1143). job_id was resolved
            # against the tenant-scoped query above, so the (vacancy_id,
            # candidate_id) pair is implicitly bound to the current tenant.
            dup = await db.execute(
            # TENANT-EXEMPT: see above — RLS + tool_registry tenant context.
                select(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        VacancyCandidate.candidate_id == UUID(candidate_id),
                    )
                )
            )
            existing_vc = dup.scalar_one_or_none()
            if existing_vc:
                vc_id = str(existing_vc.id)
                return {
                    "success": True,
                    "duplicate": True,
                    "vacancy_candidate_id": vc_id,
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "job_title": job_title_str,
                    "message": (
                        f"⚠️ **{getattr(candidate, 'name', 'Candidato')}** já está associado "
                        f"à vaga **{job_title_str}**. Continuando com o cadastro existente."
                    ),
                }

            # Task #1306: resolve the structural stage link at creation so the
            # SLA detector can join by id instead of fragile name matching.
            from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
            initial_stage_id = await resolve_recruitment_stage_id(
                db, str(company_id), initial_stage
            )
            vc = VacancyCandidate(
                id=uuid.uuid4(),
                vacancy_id=UUID(job_id),
                candidate_id=UUID(candidate_id),
                company_id=company_id,
                source=source,
                stage=initial_stage,
                recruitment_stage_id=initial_stage_id,
                status="sourced",
                added_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(vc)
            await db.commit()
            await db.refresh(vc)

            vc_id = str(vc.id)
            cand_name = getattr(candidate, "name", "Candidato")
            logger.info(f"✅ VacancyCandidate created: {vc_id}")

            return {
                "success": True,
                "duplicate": False,
                "vacancy_candidate_id": vc_id,
                "candidate_id": candidate_id,
                "candidate_name": cand_name,
                "job_id": job_id,
                "job_title": job_title_str,
                "message": (
                    f"✅ **{cand_name}** adicionado à vaga **{job_title_str}** "
                    f"na etapa **{initial_stage}**."
                ),
            }

    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ add_to_vacancy error: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao adicionar candidato à vaga: {str(e)}",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Tool: create_and_screen_candidate  (Opção C — full flow)
# ---------------------------------------------------------------------------

async def create_and_screen_candidate(
    cv_text: str,
    vacancy_title: str | None = None,
    vacancy_id: str | None = None,
    run_bars: bool = True,
    run_wsi: bool = False,
    initial_stage: str = "Triagem",
    **kwargs,
) -> dict[str, Any]:
    """
    End-to-end CV flow:
      1. AI-parse CV text → extract structured candidate data
      2. Create Candidate in DB (or reuse if duplicate)
      3. Add to JobVacancy pipeline
      4. Run BARS rubric scoring (if run_bars=True and vacancy has requirements)
      5. Optionally trigger WSI screening (if run_wsi=True)

    This is the single-call version for simple interactions.
    The multi-step PlanDetector flow calls the individual tools above.
    """
    _extract_context(kwargs)

    # Step 1 + 2: Parse & create
    create_result = await parse_and_create_candidate(
        cv_text=cv_text,
        vacancy_title=vacancy_title,
        vacancy_id=vacancy_id,
        **kwargs,
    )

    if not create_result.get("success"):
        return create_result

    candidate_id = create_result["candidate_id"]
    candidate_name = create_result.get("candidate_name", "Candidato")
    sections = [create_result["message"]]

    # Step 3: Add to vacancy (if provided)
    vc_result = None
    job_id = vacancy_id
    job_title = vacancy_title

    if vacancy_title or vacancy_id:
        vc_result = await add_to_vacancy(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            vacancy_title=vacancy_title,
            initial_stage=initial_stage,
            **kwargs,
        )
        sections.append(vc_result["message"])
        if vc_result.get("success"):
            job_id = vc_result.get("job_id", vacancy_id)
            job_title = vc_result.get("job_title", vacancy_title)

    # Step 4: BARS scoring
    bars_result = None
    if run_bars and candidate_id and job_id:
        try:
            from app.domains.cv_screening.tools.cv_match_tool import analyze_cv_match

            bars_result = await analyze_cv_match(
                candidate_id=candidate_id,
                vacancy_id=job_id,
                **kwargs,
            )
            if bars_result.get("success"):
                sections.append(
                    f"\n📊 **Avaliação BARS:**\n{bars_result.get('message', '')}"
                )
        except Exception as e:
            logger.warning(f"BARS scoring skipped: {e}")
            sections.append(f"\n⚠️ Avaliação BARS não disponível: {e}")

    # Step 5: WSI (optional)
    wsi_result = None
    if run_wsi and candidate_id and job_id:
        try:
            from app.domains.cv_screening.tools.candidate_tools import wsi_screening

            wsi_result = await wsi_screening(
                candidate_id=candidate_id,
                job_id=job_id,
                screening_type="complete",
                **kwargs,
            )
            if wsi_result.get("success"):
                sections.append(f"\n🎯 {wsi_result.get('message', '')}")
        except Exception as e:
            logger.warning(f"WSI skipped: {e}")

    full_message = "\n\n".join(s for s in sections if s)

    return {
        "success": True,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "job_id": job_id,
        "job_title": job_title,
        "match_score": bars_result.get("match_score") if bars_result else None,
        "recommendation": bars_result.get("recommendation") if bars_result else None,
        "message": full_message,
        "steps": {
            "parse_create": create_result,
            "add_to_vacancy": vc_result,
            "bars_scoring": bars_result,
            "wsi_screening": wsi_result,
        },
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_cv_upload_tools() -> None:
    """Register CV upload tools with the global tool registry."""
    from app.tools.registry import ToolDefinition, tool_registry

    tool_registry.register(ToolDefinition(
        name="parse_and_create_candidate",
        handler=parse_and_create_candidate,
        description=(
            "Parseia texto de um CV com IA e cria um registro de Candidato no banco de dados. "
            "Retorna candidate_id para uso em fluxos subsequentes."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "cv_text": {"type": "string", "description": "Texto completo do currículo"},
                "vacancy_title": {"type": "string", "description": "Título da vaga de interesse (opcional)"},
                "vacancy_id": {"type": "string", "description": "UUID da vaga de interesse (opcional)"},
                "source": {"type": "string", "description": "Origem do candidato", "default": "cv_upload"},
            },
            "required": ["cv_text"],
        },
    ))

    tool_registry.register(ToolDefinition(
        name="add_to_vacancy",
        handler=add_to_vacancy,
        description=(
            "Adiciona um candidato existente ao pipeline de uma vaga. "
            "Resolve a vaga por ID ou por título. Retorna vacancy_candidate_id."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato"},
                "vacancy_id": {"type": "string", "description": "UUID da vaga"},
                "vacancy_title": {"type": "string", "description": "Título da vaga (busca por nome)"},
                "initial_stage": {"type": "string", "description": "Etapa inicial do candidato na vaga", "default": "Triagem"},
            },
            "required": ["candidate_id"],
        },
    ))

    tool_registry.register(ToolDefinition(
        name="create_and_screen_candidate",
        handler=create_and_screen_candidate,
        description=(
            "Fluxo completo de CV: parseia texto → cria Candidato → adiciona à vaga → "
            "avalia com BARS → (opcionalmente) dispara triagem WSI."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "cv_text": {"type": "string", "description": "Texto completo do currículo"},
                "vacancy_title": {"type": "string", "description": "Título da vaga"},
                "vacancy_id": {"type": "string", "description": "UUID da vaga"},
                "run_bars": {"type": "boolean", "description": "Se deve rodar avaliação BARS", "default": True},
                "run_wsi": {"type": "boolean", "description": "Se deve disparar triagem WSI", "default": False},
            },
            "required": ["cv_text"],
        },
    ))

    logger.info("✅ CV upload tools registered: parse_and_create_candidate, add_to_vacancy, create_and_screen_candidate")
