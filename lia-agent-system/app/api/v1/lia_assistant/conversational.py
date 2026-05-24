"""
Conversational AI, job-draft management, and context-suggestions routes:
  POST /lia/conversational
  GET  /lia/job-draft/{conversation_id}
  DELETE /lia/job-draft/{conversation_id}
  GET  /lia/context-suggestions
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.dependencies.token_budget import require_token_budget
from app.domains.ai.services.llm import LLMService, get_llm_service
from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory

from ._shared import (
    # data tables
    _CONTEXT_SUGGESTIONS,
    _PAGE_BADGES,
    ContextBadge,
    ContextSuggestion,
    ContextSuggestionsResponse,
    # models
    ConversationalRequest,
    ConversationalResponse,
    JobDraft,
    logger,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter()

_conversation_memory = ConversationMemory()

async def _build_conversational_prompt(
    message: str,
    conversation_context: str,
    company_id: str,
    db,
    user_name: str = "",
    tenant_context_snippet: str = "",
) -> str:
    # Canonical helper injeta ai_persona per-tenant (ghost setting fix 2026-05-24).
    from app.shared.prompts.persona_aware_prompt import (
        build_system_prompt_with_persona,
    )
    system = await build_system_prompt_with_persona(
        company_id=company_id,
        db=db,
        agent_type="orchestrator",
        user_name=user_name,
        tenant_context_snippet=tenant_context_snippet,
        conversation_summary=conversation_context if conversation_context != "Início da conversa" else "",
        context_page="wizard",
        extra_instructions=(
            "Este chat é otimizado para criação e gestão de vagas. "
            "Se pedirem algo de outro módulo (pipeline, status, entrevistas), "
            "oriente a usar o chat principal. Nunca diga que a LIA 'não possui' funcionalidades — "
            "elas existem em outros módulos."
        ),
    )
    return f"{system}\n\nMensagem do usuário: {message}\n\nResponda de forma natural e útil:"


async def _get_active_draft_for_user(
    db: AsyncSession,
    user_id: str,
    company_id: str,
) -> JobDraft | None:
    """Fetch the most recent active (DRAFT status) JobDraft for a user.

    Multi-tenancy fail-closed: company_id required (caller passes JWT value).
    """
    try:
        from app.models.job_draft import JobDraftStatus
        result = await db.execute(
            select(JobDraft)
            .where(
                and_(
                    JobDraft.recruiter_id == user_id,
                    JobDraft.company_id == company_id,
                    JobDraft.status == JobDraftStatus.DRAFT,
                )
            )
            .order_by(JobDraft.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"Failed to fetch active draft for user {user_id}: {e}")
        return None


def _draft_to_dict(draft: JobDraft) -> dict[str, Any]:
    """Serialize a JobDraft to a dict suitable for API responses."""
    return {
        "id": str(draft.id),
        "conversation_id": str(draft.conversation_id) if draft.conversation_id else None,
        "status": draft.status.value if hasattr(draft.status, "value") else draft.status,
        "current_step": draft.current_step,
        "job_title": draft.job_title,
        "department": draft.department,
        "seniority": draft.seniority,
        "location": draft.location,
        "work_model": draft.work_model,
        "employment_type": draft.employment_type,
        "salary_min": draft.salary_min,
        "salary_max": draft.salary_max,
        "skills": draft.skills or [],
        "behavioral_competencies": draft.behavioral_competencies or [],
        "benefits": draft.benefits or [],
        "is_affirmative": draft.is_affirmative,
        "affirmative_criteria_primary": draft.affirmative_criteria_primary,
        "affirmative_criteria_secondary": draft.affirmative_criteria_secondary,
        "manager": draft.manager,
        "manager_email": draft.manager_email,
        "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
        "created_at": draft.created_at.isoformat() if draft.created_at else None,
    }


@router.post("/conversational", response_model=ConversationalResponse)
async def handle_conversational_message(
    request: ConversationalRequest,
    _budget: None = Depends(require_token_budget),
    llm_svc: LLMService = Depends(get_llm_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Handle general conversational messages using LLM for natural responses.

    This endpoint enables LIA to have real conversations, understanding
    questions about capabilities and responding intelligently.
    """
    try:
        user_id = str(current_user.id)

        # Mode: salary_benchmark — use structured salary analysis (fix C-06)
        if request.mode == "salary_benchmark":
            salary_prompt = f"""Você é especialista em remuneração do mercado brasileiro de tecnologia.
Forneça uma análise completa de faixa salarial para a seguinte solicitação.

REGRAS OBRIGATÓRIAS:
1. Sempre inclua valores em Reais no formato R$ XX.XXX (ponto como separador de milhar)
2. Estruture a resposta com:
   - Faixa mínima: R$ X.XXX
   - Mediana: R$ X.XXX
   - Faixa máxima: R$ X.XXX
   - Recomendação: R$ X.XXX - R$ X.XXX mensais (CLT)
3. Considere senioridade, localização e mercado brasileiro 2025
4. Responda em Português do Brasil

Solicitação: {request.message}"""

            response_text = await llm_svc.generate(salary_prompt, provider="gemini")
            return ConversationalResponse(
                response=response_text,
                understood_intent="salary_benchmark",
                suggested_action=None,
                can_help=True
            )

        # Fetch active draft early so its conversation_id can be used as fallback
        active_draft = await _get_active_draft_for_user(db, user_id)
        active_draft_dict: dict[str, Any] | None = None
        if active_draft:
            active_draft_dict = _draft_to_dict(active_draft)

        # Resolve conversation_id — priority order:
        # 1. Client-supplied & owned by user
        # 2. Active draft's conversation_id (resume flow continuity)
        # 3. Auto-create a new conversation so memory is always seeded
        resolved_conversation_id: str | None = None
        _conversation_is_owned: bool = False

        if request.conversation_id:
            try:
                existing_conv = await _conversation_memory.get_conversation(
                    db=db,
                    conversation_id=request.conversation_id,
                )
                if existing_conv is not None and str(existing_conv.user_id) == user_id:
                    resolved_conversation_id = request.conversation_id
                    _conversation_is_owned = True
                else:
                    logger.warning(
                        f"Conversation {request.conversation_id} not owned by user {user_id}, "
                        "ignoring — will prefer active draft conversation_id or auto-create"
                    )
            except Exception as e:
                logger.warning(f"Failed to verify conversation ownership: {e}")

        if not resolved_conversation_id and active_draft and active_draft.conversation_id:
            # Prefer the draft's existing conversation to preserve prior message history
            draft_conv_id = str(active_draft.conversation_id)
            try:
                draft_conv = await _conversation_memory.get_conversation(
                    db=db,
                    conversation_id=draft_conv_id,
                )
                if draft_conv is not None and str(draft_conv.user_id) == user_id:
                    resolved_conversation_id = draft_conv_id
                    _conversation_is_owned = True
                    logger.info(f"Using active draft conversation_id {draft_conv_id} for history continuity")
            except Exception as e:
                logger.warning(f"Failed to verify draft conversation ownership: {e}")

        if not resolved_conversation_id:
            try:
                _auto_company_id = (
                    str(current_user.company_id) if current_user.company_id else ""
                )
                auto_conv = await _conversation_memory.get_or_create_conversation(
                    db=db,
                    user_id=user_id,
                    company_id=_auto_company_id,
                    context_type="lia_chat",
                    title="Conversa com LIA",
                )
                resolved_conversation_id = str(auto_conv.id)
                _conversation_is_owned = True
            except Exception as e:
                logger.warning(f"Failed to auto-create conversation: {e}")

        # Load conversation history for owned conversations
        conversation_context_text = "Início da conversa"
        if resolved_conversation_id and _conversation_is_owned:
            try:
                context = await _conversation_memory.get_context_for_llm(
                    db=db,
                    conversation_id=resolved_conversation_id,
                    max_messages=10,
                    include_summary=True,
                )
                messages_hist = context.get("messages", [])
                summary = context.get("summary")

                if summary:
                    conversation_context_text = f"Resumo da conversa anterior: {summary}"
                    if messages_hist:
                        recent = "\n".join([
                            f"{m['role'].upper()}: {m['content'][:200]}"
                            for m in messages_hist[-5:]
                        ])
                        conversation_context_text += f"\n\nMensagens recentes:\n{recent}"
                elif messages_hist:
                    conversation_context_text = "\n".join([
                        f"{m['role'].upper()}: {m['content'][:200]}"
                        for m in messages_hist[-10:]
                    ])
            except Exception as e:
                logger.warning(f"Failed to load conversation history: {e}")

        _conv_user_name = ""
        _conv_tenant_snippet = ""
        try:
            _conv_user_name = current_user.name if hasattr(current_user, "name") else ""
        except Exception:
            pass
        # Task #978 (T-G): callsite NON-ReAct — usa helper canônico para
        # herdar telemetria Prometheus + fail-closed em strict-mode.
        from app.shared.agents.tenant_aware_agent import (
            resolve_tenant_snippet_for_non_react,
        )

        _company_id = getattr(current_user, "company_id", None)
        _resolver_ctx: dict[str, Any] = {}
        if _company_id:
            try:
                from app.shared.services.tenant_context_service import TenantContextService
                _tcs = TenantContextService()
                _tc = await _tcs.get_context(company_id=str(_company_id), db=db)
                _resolver_ctx["tenant_context"] = _tc
            except Exception as _tc_exc:
                logger.debug("Tenant context skipped in conversational: %s", _tc_exc)
        _conv_tenant_snippet = resolve_tenant_snippet_for_non_react(
            _resolver_ctx,
            agent_name="lia_assistant_conversational",
            company_id_raw=_company_id,
        )
        prompt = await _build_conversational_prompt(
            message=request.message,
            conversation_context=conversation_context_text,
            company_id=str(_company_id) if _company_id else "",
            db=db,
            user_name=_conv_user_name or "",
            tenant_context_snippet=_conv_tenant_snippet,
        )
        response_text = await llm_svc.generate(prompt, provider="gemini")

        lower_msg = request.message.lower()

        # Detect intent — check resume_draft first
        intent = "other"
        if any(word in lower_msg for word in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hello']):
            intent = "greeting"
        elif any(word in lower_msg for word in ['continuar', 'retomar', 'voltar', 'onde parei', 'em andamento', 'vaga que estava', 'rascunho', 'draft']):
            intent = "resume_draft"
        elif any(word in lower_msg for word in ['criar', 'nova vaga', 'do zero', 'começar']):
            intent = "create_job"
        elif any(word in lower_msg for word in ['reutilizar', 'anterior', 'fast track', 'aproveitar']):
            intent = "fast_track"
        elif '?' in request.message or any(word in lower_msg for word in ['como', 'o que', 'pode', 'consegue', 'faz', 'ajuda']):
            intent = "question"

        suggested_action = None
        if intent == "resume_draft" and active_draft:
            suggested_action = "resume_draft"
            # Override response to include draft context
            draft_title = active_draft.job_title or "vaga sem título"
            draft_step = active_draft.current_step or "início"
            response_text = (
                f"Encontrei sua vaga em andamento: **{draft_title}**! "
                f"Você estava na etapa de **{draft_step}**. "
                f"Deseja continuar de onde parou ou começar uma nova vaga do zero?"
            )
        elif intent in ("create_job", "fast_track") and active_draft:
            # When user wants to create/fast-track but has a draft, offer to resume first
            draft_title = active_draft.job_title or "uma vaga"
            suggested_action = "offer_resume_draft"
            response_text = (
                f"Você tem uma vaga em andamento (**{draft_title}**). "
                f"Deseja continuar de onde parou ou prefere começar do zero?"
            )
        elif intent == "create_job":
            suggested_action = "from_scratch"
        elif intent == "fast_track":
            suggested_action = "fast_track"
        elif intent == "greeting" and active_draft and not request.context:
            # Proactively mention draft on greeting if user has one
            draft_title = active_draft.job_title or "uma vaga"
            suggested_action = "offer_resume_draft"
            response_text += (
                f"\n\n💡 **Nota:** Você tem uma vaga em andamento (**{draft_title}**). "
                f"Quer continuar de onde parou?"
            )

        # Store message in conversation history only if conversation is verified owned
        if resolved_conversation_id and _conversation_is_owned:
            try:
                await _conversation_memory.add_message(
                    db=db,
                    conversation_id=resolved_conversation_id,
                    role="user",
                    content=request.message,
                    intent=intent,
                )
                await _conversation_memory.add_message(
                    db=db,
                    conversation_id=resolved_conversation_id,
                    role="assistant",
                    content=response_text,
                    intent=intent,
                )
                await db.commit()
            except Exception as e:
                logger.warning(f"Failed to store conversation messages: {e}")

        return ConversationalResponse(
            response=response_text,
            understood_intent=intent,
            suggested_action=suggested_action,
            can_help=True,
            active_draft=active_draft_dict,
            conversation_id=resolved_conversation_id,
        )

    except Exception as e:
        logger.error(f"Error in conversational response: {e}")
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
        _user_name = ""
        try:
            _user_name = current_user.name if hasattr(current_user, "name") else ""
        except Exception:
            pass
        return ConversationalResponse(
            response=SystemPromptBuilder.build_error_response(user_name=_user_name),
            understood_intent="fallback",
            can_help=True
        )


@router.get("/job-draft/{conversation_id}", response_model=None)
async def get_job_draft(
    conversation_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get the current job draft for a conversation, reading from the database."""
    try:
        try:
            conv_uuid = UUID(conversation_id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "message": "Invalid conversation_id format",
                "job_draft": None
            }

        from app.models.job_draft import JobDraftStatus
        user_id = str(current_user.id)
        # multi-tenancy fail-closed: explicit company_id filter
        result = await db.execute(
            select(JobDraft)
            .where(
                and_(
                    JobDraft.conversation_id == conv_uuid,
                    JobDraft.recruiter_id == user_id,
                    JobDraft.company_id == company_id,
                    JobDraft.status == JobDraftStatus.DRAFT,
                )
            )
            .order_by(JobDraft.updated_at.desc())
            .limit(1)
        )
        draft = result.scalar_one_or_none()

        if draft:
            return {
                "success": True,
                "job_draft": _draft_to_dict(draft),
            }
    except Exception as e:
        logger.warning(f"Error fetching job draft from DB: {e}")

    return {
        "success": False,
        "message": "Job draft not found",
        "job_draft": None
    }


@router.get("/active-draft", response_model=None)
async def get_active_draft(
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get the most recent active draft for the current user."""
    user_id = str(current_user.id)
    draft = await _get_active_draft_for_user(db, user_id, company_id)
    if draft:
        return {
            "success": True,
            "job_draft": _draft_to_dict(draft),
        }
    return {
        "success": False,
        "message": "No active draft found",
        "job_draft": None
    }


@router.delete("/job-draft/{conversation_id}", response_model=None)
async def clear_job_draft(
    conversation_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Clear (cancel) a job draft linked to a conversation."""
    try:
        try:
            conv_uuid = UUID(conversation_id)
        except (ValueError, TypeError):
            return {"success": False, "message": "Invalid conversation_id format"}

        from app.models.job_draft import JobDraftStatus
        user_id = str(current_user.id)
        # multi-tenancy fail-closed: explicit company_id filter
        result = await db.execute(
            select(JobDraft).where(
                and_(
                    JobDraft.conversation_id == conv_uuid,
                    JobDraft.recruiter_id == user_id,
                    JobDraft.company_id == company_id,
                )
            )
        )
        draft = result.scalar_one_or_none()

        if draft:
            draft.status = JobDraftStatus.CANCELLED
            draft.updated_at = datetime.utcnow()
            await db.commit()
            return {"success": True, "message": "Job draft cancelled"}

        return {"success": False, "message": "Job draft not found"}
    except Exception as e:
        logger.error(f"Error clearing job draft: {e}")
        return {"success": False, "message": f"Error: {e}"}


@router.get("/context-suggestions", response_model=ContextSuggestionsResponse)
async def get_context_suggestions(
    page: str = Query(..., description="Page context: home|vaga|candidato|pipeline|triagem|relatorios|configuracoes"),
    entity_id: str | None = Query(None, description="ID of the current entity (job or candidate)"),
    entity_name: str | None = Query(None, description="Display name of the current entity"),
    limit: int = Query(default=5, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Returns a context badge + proactive suggestion chips for the current page.
    Mirrors the Notion AI pattern: badge shows where you are, chips offer smart actions.
    """
    page_key = page.lower().strip()

    badge_config = _PAGE_BADGES.get(page_key, _PAGE_BADGES["home"])
    badge_label = badge_config["label"]
    if entity_name:
        badge_label = f"{badge_config['label']}: {entity_name}"

    context_badge = ContextBadge(
        label=badge_label,
        icon=badge_config["icon"],
        color=badge_config["color"],
        description=f"Contexto: {badge_config['label'].lower()}",
    )

    raw_suggestions = _CONTEXT_SUGGESTIONS.get(page_key, _CONTEXT_SUGGESTIONS["home"])

    personalized: list[ContextSuggestion] = []
    for s in raw_suggestions[:limit]:
        prompt = s["prompt"]
        if entity_name and page_key in ("vaga", "candidato"):
            prompt = f"{prompt} (referindo-se a: {entity_name}" + (f", ID: {entity_id}" if entity_id else "") + ")"
        personalized.append(ContextSuggestion(
            id=s["id"],
            label=s["label"],
            prompt=prompt,
            icon=s.get("icon"),
            category=s.get("category", "action"),
        ))

    return ContextSuggestionsResponse(
        context_badge=context_badge,
        suggestions=personalized,
        page=page_key,
        entity_id=entity_id,
        generated_at=datetime.utcnow().isoformat(),
    )
