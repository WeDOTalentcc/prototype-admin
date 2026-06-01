"""
CompanyHiringPolicy API endpoints.

Provides CRUD operations for company hiring policies:
- GET /company-hiring-policy/{company_id} — Get policy (or defaults)
- PUT /company-hiring-policy/{company_id} — Upsert full policy
- PATCH /company-hiring-policy/{company_id} — Update specific blocks
- PATCH /company-hiring-policy/{company_id}/block — Update a single block
- GET /company-hiring-policy/{company_id}/progress — Setup progress
- POST /company-hiring-policy/chat — Policy setup chat with LIA
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
from app.domains.hiring_policy.repositories.hiring_policy_repository import (
    HiringPolicyRepository,
)
from app.models.company_hiring_policy import (
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
)
from app.schemas.company_hiring_policy import (
    PolicyBlockValidationError,
    PolicyInstructionsUpdate,
    coerce_and_validate_block,
    validate_policy_instructions,
    CompanyHiringPolicyBlockUpdate,
    CompanyHiringPolicyResponse,
    CompanyHiringPolicyUpdate,
    PolicyChatMessage,
    PolicyChatResponse,
    PolicyProgressResponse,
)
from app.shared.policy_helper import get_company_policy, invalidate_policy_cache
from app.shared.policy_sync_service import sync_policy_to_models
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company-hiring-policy", tags=["hiring-policy"])

VALID_BLOCKS = [
    "pipeline_rules",
    "scheduling_rules",
    "communication_rules",
    "screening_rules",
    "automation_rules",
    "pipeline_templates",
]

BLOCK_QUESTION_COUNTS = {
    "pipeline_rules": 4,
    "scheduling_rules": 4,
    "communication_rules": 4,
    "screening_rules": 3,
    "automation_rules": 4,
}

TOTAL_QUESTIONS = 19


def _calculate_progress(policy) -> int:
    answered = policy.answered_questions or []
    return min(int((len(answered) / TOTAL_QUESTIONS) * 100), 100)


def _blocks_completed(policy) -> dict[str, bool]:
    answered = set(policy.answered_questions or [])
    block_questions = {
        "pipeline_rules": {"min_interviews_before_offer", "manager_approval_for_offer", "max_days_in_stage", "pipeline_template"},
        "scheduling_rules": {"allowed_days", "allowed_hours", "default_duration_minutes", "self_scheduling_enabled"},
        "communication_rules": {"auto_rejection_feedback", "rejection_feedback_deadline_hours", "preferred_channel", "lia_tone"},
        "screening_rules": {"salary_expectation_filter", "experience_policy", "default_screening_questions"},
        "automation_rules": {"auto_screening", "auto_scheduling", "auto_stage_advance", "autonomy_level"},
    }
    result = {block: questions.issubset(answered) for block, questions in block_questions.items()}
    result["pipeline_templates"] = "pipeline_template" in answered
    return result


def _validate_block_or_422(block: str, data):
    """P0.a boundary: coerce+validate a block payload, surfacing 422 on bad input.

    Free text in a typed gate slot fails loud instead of corrupting the gate
    (CLAUDE.md: falhar alto, nunca silenciosamente)."""
    try:
        return coerce_and_validate_block(block, data)
    except PolicyBlockValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{company_id}", response_model=CompanyHiringPolicyResponse)
async def get_policy(company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], db: AsyncSession = Depends(get_db), _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get hiring policy for a company. Returns defaults if none exists."""
    repo = HiringPolicyRepository(db)
    policy = await repo.get_by_company(company_id)
    if policy:
        return policy.to_dict()
    return {
        "id": "",
        "company_id": company_id,
        "pipeline_rules": PIPELINE_RULES_DEFAULTS,
        "scheduling_rules": SCHEDULING_RULES_DEFAULTS,
        "communication_rules": COMMUNICATION_RULES_DEFAULTS,
        "screening_rules": SCREENING_RULES_DEFAULTS,
        "automation_rules": AUTOMATION_RULES_DEFAULTS,
        "pipeline_templates": [],
        "learned_patterns": [],
        "setup_progress": 0,
        "setup_completed_at": None,
        "created_by": None,
        "updated_by": None,
        "created_at": None,
        "updated_at": None,
    }


@router.put("/{company_id}", response_model=CompanyHiringPolicyResponse)
async def upsert_policy(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: CompanyHiringPolicyUpdate,
    user_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create or update full hiring policy for a company."""
    repo = HiringPolicyRepository(db)
    update_data = payload.model_dump(exclude_none=True)
    for _block in VALID_BLOCKS:
        if _block in update_data:
            update_data[_block] = _validate_block_or_422(_block, update_data[_block])
    effective_user = user_id or payload.updated_by

    policy = await repo.upsert(company_id, update_data, VALID_BLOCKS, user_id=effective_user)
    policy.setup_progress = _calculate_progress(policy)
    if policy.setup_progress >= 100 and not policy.setup_completed_at:
        policy.setup_completed_at = datetime.utcnow()
    await repo.flush()
    invalidate_policy_cache(company_id)

    # T-1169: capturar dict ANTES do sync_policy_to_models — esse helper executa
    # db.execute(update())+flush() que expira attributes do `policy`. Acessar
    # `policy.<attr>` depois disso dispara lazy-load num contexto async perdido
    # → sqlalchemy.exc.MissingGreenlet 500. Capturar uma vez e reusar.
    response_dict = policy.to_dict()

    try:
        await sync_policy_to_models(company_id, response_dict, db)
    except Exception as e:
        logger.warning(f"Policy sync failed for {company_id}: {e}")

    logger.info(f"Policy upserted for company {company_id}, progress={policy.setup_progress}%")
    return response_dict


@router.patch("/{company_id}", response_model=CompanyHiringPolicyResponse)
async def update_policy_partial(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: CompanyHiringPolicyUpdate,
    user_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Partially update hiring policy — merges provided blocks."""
    repo = HiringPolicyRepository(db)
    policy = await repo.create_if_missing(company_id, user_id)

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        if key in VALID_BLOCKS:
            value = _validate_block_or_422(key, value)
            existing = getattr(policy, key) or {}
            if isinstance(existing, dict) and isinstance(value, dict):
                # T-1169: NOVO dict — Column(JSON) puro não rastreia mutação in-place.
                setattr(policy, key, {**existing, **value})
            else:
                setattr(policy, key, value)

    policy.updated_by = user_id or payload.updated_by
    policy.updated_at = datetime.utcnow()
    policy.setup_progress = _calculate_progress(policy)
    if policy.setup_progress >= 100 and not policy.setup_completed_at:
        policy.setup_completed_at = datetime.utcnow()
    await repo.flush()
    invalidate_policy_cache(company_id)

    # T-1169: ver comentário em upsert_policy.
    response_dict = policy.to_dict()

    try:
        await sync_policy_to_models(company_id, response_dict, db)
    except Exception as e:
        logger.warning(f"Policy sync failed for {company_id}: {e}")

    return response_dict


@router.patch("/{company_id}/block", response_model=CompanyHiringPolicyResponse)
async def update_policy_block(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: CompanyHiringPolicyBlockUpdate,
    user_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a single block of the hiring policy."""
    if payload.block not in VALID_BLOCKS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid block: {payload.block}. Valid: {VALID_BLOCKS}",
        )

    repo = HiringPolicyRepository(db)
    policy = await repo.create_if_missing(company_id, user_id)

    clean_data = _validate_block_or_422(payload.block, payload.data)
    existing = getattr(policy, payload.block) or {}
    if isinstance(existing, dict) and isinstance(clean_data, dict):
        # T-1169: NOVO dict — Column(JSON) puro não rastreia mutação in-place.
        setattr(policy, payload.block, {**existing, **clean_data})
    else:
        setattr(policy, payload.block, clean_data)

    policy.updated_by = user_id or payload.updated_by
    policy.updated_at = datetime.utcnow()
    policy.setup_progress = _calculate_progress(policy)
    if policy.setup_progress >= 100 and not policy.setup_completed_at:
        policy.setup_completed_at = datetime.utcnow()
    await repo.flush()
    invalidate_policy_cache(company_id)

    # T-1169: ver comentário em upsert_policy.
    response_dict = policy.to_dict()

    try:
        await sync_policy_to_models(company_id, response_dict, db)
    except Exception as e:
        logger.warning(f"Policy sync failed for {company_id}: {e}")

    return response_dict


@router.patch("/{company_id}/instructions", response_model=CompanyHiringPolicyResponse)
async def update_policy_instructions(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: PolicyInstructionsUpdate,
    user_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """P3b: merge free-text policy instructions (prompt hints). SEPARADO dos 5
    blocos de gate — texto livre nunca toca um slot tipado (invariante de segurança)."""
    try:
        clean = validate_policy_instructions(payload.instructions)
    except PolicyBlockValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repo = HiringPolicyRepository(db)
    policy = await repo.create_if_missing(company_id, user_id)
    existing = policy.policy_instructions or {}
    # T-1169: NOVO dict — Column(JSON) puro não rastreia mutação in-place.
    policy.policy_instructions = {**existing, **clean}
    policy.updated_by = user_id or payload.updated_by
    policy.updated_at = datetime.utcnow()
    await repo.flush()
    invalidate_policy_cache(company_id)
    return policy.to_dict()


@router.get("/{company_id}/progress", response_model=PolicyProgressResponse)
async def get_policy_progress(company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], db: AsyncSession = Depends(get_db), _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get setup progress for a company's hiring policy."""
    repo = HiringPolicyRepository(db)
    policy = await repo.get_by_company(company_id)
    if not policy:
        return {
            "company_id": company_id,
            "setup_progress": 0,
            "setup_completed_at": None,
            "blocks_completed": {b: False for b in list(BLOCK_QUESTION_COUNTS) + ["pipeline_templates"]},
        }
    return {
        "company_id": company_id,
        "setup_progress": policy.setup_progress or 0,
        "setup_completed_at": policy.setup_completed_at.isoformat() if policy.setup_completed_at else None,
        "blocks_completed": _blocks_completed(policy),
    }


@router.post("/{company_id}/chat", response_model=PolicyChatResponse)
async def policy_chat(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: PolicyChatMessage,
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Conversational endpoint for hiring policy configuration."""
    current_policy = await get_company_policy(company_id, db)

    session_id = payload.session_id or str(uuid.uuid4())
    repo = HiringPolicyRepository(db)

    conversation_history = payload.conversation_history or []
    if not conversation_history:
        conversation_history = await repo.fetch_conversation_history(company_id, session_id)

    try:
        react_agent = PolicyReActAgent()
        result = await react_agent.process_legacy_format(
            message=payload.message,
            company_id=company_id,
            session_id=session_id,
            current_policy=current_policy,
            conversation_history=conversation_history,
        )
        logger.info(
            f"[policy_chat] ReAct agent processed message for company={company_id} "
            f"compliance_blocked={result.get('compliance_blocked', False)}"
        )
    except Exception as react_err:
        logger.warning(f"[policy_chat] ReAct agent failed: {react_err}")
        result = {
            "reply": "Estou com dificuldade em processar sua mensagem agora. Por favor, tente novamente em instantes.",
            "updated_fields": {},
            "block_completed": False,
            "all_completed": False,
            "setup_progress": current_policy.setup_progress if current_policy else 0,
        }

    try:
        await repo.persist_chat_messages(
            company_id, session_id,
            user_message=payload.message,
            assistant_reply=result.get("reply", ""),
            user_id=payload.user_id,
        )
    except Exception as e:
        logger.warning(f"[policy_chat] Failed to persist messages: {e}")

    if result.get("updated_fields"):
        try:
            update_payload = CompanyHiringPolicyUpdate(**result["updated_fields"])
            await upsert_policy(company_id, update_payload, user_id="lia-agent", db=db)
        except Exception as e:
            logger.warning(f"[policy_chat] Failed to persist updated_fields: {e}")

    answered_field = result.get("answered_field")
    if answered_field:
        policy = await repo.get_by_company(company_id)
        if policy:
            policy = await repo.update_answered_questions(policy, answered_field)
            policy.setup_progress = _calculate_progress(policy)
            if policy.setup_progress >= 100 and not policy.setup_completed_at:
                policy.setup_completed_at = datetime.utcnow()
            await repo.flush()

    return PolicyChatResponse(
        reply=result["reply"],
        current_block=result.get("current_block"),
        current_question=result.get("current_question", 0),
        total_questions=result.get("total_questions", 19),
        setup_progress=result.get("setup_progress", 0),
        updated_fields=result.get("updated_fields", {}),
        block_completed=result.get("block_completed", False),
        all_completed=result.get("all_completed", False),
        session_id=session_id,
    )

reorder_collection_before_item(router)
