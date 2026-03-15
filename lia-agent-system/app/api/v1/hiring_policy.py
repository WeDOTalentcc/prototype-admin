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
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import uuid

from app.core.database import get_db
from app.models.company_hiring_policy import (
    CompanyHiringPolicy,
    ALL_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
    AUTOMATION_RULES_DEFAULTS,
)
from app.schemas.company_hiring_policy import (
    CompanyHiringPolicyCreate,
    CompanyHiringPolicyUpdate,
    CompanyHiringPolicyBlockUpdate,
    CompanyHiringPolicyResponse,
    PolicyProgressResponse,
    PolicyChatMessage,
    PolicyChatResponse,
)
from app.shared.policy_helper import invalidate_policy_cache, get_company_policy
from app.shared.policy_sync_service import sync_policy_to_models
from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent

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


def _calculate_progress(policy: CompanyHiringPolicy) -> int:
    """Calculate setup progress based on explicitly answered questions."""
    answered = policy.answered_questions or []
    filled = len(answered)
    total = TOTAL_QUESTIONS
    return min(int((filled / total) * 100), 100)


def _blocks_completed(policy: CompanyHiringPolicy) -> Dict[str, bool]:
    """Check which blocks have been completed based on answered questions."""
    answered = set(policy.answered_questions or [])

    block_questions = {
        "pipeline_rules": {"min_interviews_before_offer", "manager_approval_for_offer", "max_days_in_stage", "pipeline_template"},
        "scheduling_rules": {"allowed_days", "allowed_hours", "default_duration_minutes", "self_scheduling_enabled"},
        "communication_rules": {"auto_rejection_feedback", "rejection_feedback_deadline_hours", "preferred_channel", "lia_tone"},
        "screening_rules": {"salary_expectation_filter", "experience_policy", "default_screening_questions"},
        "automation_rules": {"auto_screening", "auto_scheduling", "auto_stage_advance", "autonomy_level"},
    }

    result = {}
    for block, questions in block_questions.items():
        result[block] = questions.issubset(answered)
    result["pipeline_templates"] = "pipeline_template" in answered

    return result


@router.get("/{company_id}", response_model=CompanyHiringPolicyResponse)
async def get_policy(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get hiring policy for a company. Returns defaults if none exists."""
    result = await db.execute(
        select(CompanyHiringPolicy).where(
            CompanyHiringPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()

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
    company_id: str,
    payload: CompanyHiringPolicyUpdate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create or update full hiring policy for a company."""
    result = await db.execute(
        select(CompanyHiringPolicy).where(
            CompanyHiringPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()

    update_data = payload.model_dump(exclude_none=True)

    if policy:
        for key, value in update_data.items():
            if key in VALID_BLOCKS:
                existing = getattr(policy, key) or {}
                if isinstance(existing, dict) and isinstance(value, dict):
                    existing.update(value)
                    setattr(policy, key, existing)
                else:
                    setattr(policy, key, value)
        policy.updated_by = user_id or payload.updated_by
        policy.updated_at = datetime.utcnow()
    else:
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id=company_id,
            pipeline_rules=update_data.get("pipeline_rules", PIPELINE_RULES_DEFAULTS.copy()),
            scheduling_rules=update_data.get("scheduling_rules", SCHEDULING_RULES_DEFAULTS.copy()),
            communication_rules=update_data.get("communication_rules", COMMUNICATION_RULES_DEFAULTS.copy()),
            screening_rules=update_data.get("screening_rules", SCREENING_RULES_DEFAULTS.copy()),
            automation_rules=update_data.get("automation_rules", AUTOMATION_RULES_DEFAULTS.copy()),
            pipeline_templates=update_data.get("pipeline_templates", []),
            created_by=user_id or payload.updated_by,
            updated_by=user_id or payload.updated_by,
        )
        db.add(policy)

    policy.setup_progress = _calculate_progress(policy)
    if policy.setup_progress >= 100 and not policy.setup_completed_at:
        policy.setup_completed_at = datetime.utcnow()

    await db.flush()
    invalidate_policy_cache(company_id)

    try:
        await sync_policy_to_models(company_id, policy.to_dict(), db)
    except Exception as e:
        logger.warning(f"Policy sync failed for {company_id}: {e}")

    logger.info(f"Policy upserted for company {company_id}, progress={policy.setup_progress}%")
    return policy.to_dict()


@router.patch("/{company_id}", response_model=CompanyHiringPolicyResponse)
async def update_policy_partial(
    company_id: str,
    payload: CompanyHiringPolicyUpdate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Partially update hiring policy — merges provided blocks."""
    result = await db.execute(
        select(CompanyHiringPolicy).where(
            CompanyHiringPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()

    if not policy:
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id=company_id,
            created_by=user_id,
        )
        db.add(policy)

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        if key in VALID_BLOCKS:
            existing = getattr(policy, key) or {}
            if isinstance(existing, dict) and isinstance(value, dict):
                existing.update(value)
                setattr(policy, key, existing)
            else:
                setattr(policy, key, value)

    policy.updated_by = user_id or payload.updated_by
    policy.updated_at = datetime.utcnow()
    policy.setup_progress = _calculate_progress(policy)
    if policy.setup_progress >= 100 and not policy.setup_completed_at:
        policy.setup_completed_at = datetime.utcnow()

    await db.flush()
    invalidate_policy_cache(company_id)

    try:
        await sync_policy_to_models(company_id, policy.to_dict(), db)
    except Exception as e:
        logger.warning(f"Policy sync failed for {company_id}: {e}")

    return policy.to_dict()


@router.patch("/{company_id}/block", response_model=CompanyHiringPolicyResponse)
async def update_policy_block(
    company_id: str,
    payload: CompanyHiringPolicyBlockUpdate,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update a single block of the hiring policy."""
    if payload.block not in VALID_BLOCKS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid block: {payload.block}. Valid: {VALID_BLOCKS}"
        )

    result = await db.execute(
        select(CompanyHiringPolicy).where(
            CompanyHiringPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()

    if not policy:
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id=company_id,
            created_by=user_id,
        )
        db.add(policy)

    existing = getattr(policy, payload.block) or {}
    if isinstance(existing, dict) and isinstance(payload.data, dict):
        existing.update(payload.data)
        setattr(policy, payload.block, existing)
    else:
        setattr(policy, payload.block, payload.data)

    policy.updated_by = user_id or payload.updated_by
    policy.updated_at = datetime.utcnow()
    policy.setup_progress = _calculate_progress(policy)
    if policy.setup_progress >= 100 and not policy.setup_completed_at:
        policy.setup_completed_at = datetime.utcnow()

    await db.flush()
    invalidate_policy_cache(company_id)

    try:
        await sync_policy_to_models(company_id, policy.to_dict(), db)
    except Exception as e:
        logger.warning(f"Policy sync failed for {company_id}: {e}")

    return policy.to_dict()


@router.get("/{company_id}/progress", response_model=PolicyProgressResponse)
async def get_policy_progress(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get setup progress for a company's hiring policy."""
    result = await db.execute(
        select(CompanyHiringPolicy).where(
            CompanyHiringPolicy.company_id == company_id
        )
    )
    policy = result.scalar_one_or_none()

    if not policy:
        return {
            "company_id": company_id,
            "setup_progress": 0,
            "setup_completed_at": None,
            "blocks_completed": {
                "pipeline_rules": False,
                "scheduling_rules": False,
                "communication_rules": False,
                "screening_rules": False,
                "automation_rules": False,
                "pipeline_templates": False,
            }
        }

    return {
        "company_id": company_id,
        "setup_progress": policy.setup_progress or 0,
        "setup_completed_at": policy.setup_completed_at.isoformat() if policy.setup_completed_at else None,
        "blocks_completed": _blocks_completed(policy),
    }


async def _fetch_conversation_history(
    db: AsyncSession, company_id: str, session_id: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """Fetch recent conversation history from the DB for policy chat."""
    try:
        query = text("""
            SELECT m.role, m.content
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.context_type = 'policy'
              AND c.context_id = :company_id
              AND c.session_id = :session_id
            ORDER BY m.created_at DESC
            LIMIT :limit
        """)
        result = await db.execute(query, {
            "company_id": company_id,
            "session_id": session_id,
            "limit": limit,
        })
        rows = result.fetchall()
        history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
        return history
    except Exception as e:
        logger.warning(f"[policy_chat] Failed to fetch conversation history: {e}")
        return []


async def _persist_chat_messages(
    db: AsyncSession, company_id: str, session_id: str,
    user_message: str, assistant_reply: str, user_id: Optional[str] = None,
) -> None:
    """Persist user and assistant messages to the DB."""
    try:
        find_conv = text("""
            SELECT id FROM conversations
            WHERE context_type = 'policy'
              AND context_id = :company_id
              AND session_id = :session_id
            LIMIT 1
        """)
        result = await db.execute(find_conv, {
            "company_id": company_id,
            "session_id": session_id,
        })
        row = result.fetchone()

        if row:
            conv_id = row[0]
        else:
            conv_id = str(uuid.uuid4())
            insert_conv = text("""
                INSERT INTO conversations (id, user_id, context_type, context_id, session_id, status, is_active, created_at, updated_at)
                VALUES (:id, :user_id, 'policy', :company_id, :session_id, 'active', true, NOW(), NOW())
            """)
            await db.execute(insert_conv, {
                "id": conv_id,
                "user_id": user_id or "default_user",
                "company_id": company_id,
                "session_id": session_id,
            })

        insert_msg = text("""
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (:id, :conv_id, :role, :content, NOW())
        """)
        await db.execute(insert_msg, {
            "id": str(uuid.uuid4()),
            "conv_id": conv_id,
            "role": "user",
            "content": user_message,
        })
        await db.execute(insert_msg, {
            "id": str(uuid.uuid4()),
            "conv_id": conv_id,
            "role": "assistant",
            "content": assistant_reply,
        })

        await db.flush()
    except Exception as e:
        logger.warning(f"[policy_chat] Failed to persist chat messages: {e}")


@router.post("/{company_id}/chat", response_model=PolicyChatResponse)
async def policy_chat(
    company_id: str,
    payload: PolicyChatMessage,
    db: AsyncSession = Depends(get_db)
):
    """Conversational endpoint for hiring policy configuration.

    Uses the PolicyReActAgent (ReAct-based) for intelligent, consultive
    policy configuration with compliance validation. Falls back to the
    legacy PolicySetupAgent if the ReAct agent fails.
    """
    current_policy = await get_company_policy(company_id, db)

    session_id = payload.session_id or str(uuid.uuid4())
    conversation_history = payload.conversation_history or []
    if not conversation_history:
        conversation_history = await _fetch_conversation_history(
            db, company_id, session_id
        )

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
        await _persist_chat_messages(
            db, company_id, session_id,
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
        policy_result = await db.execute(
            select(CompanyHiringPolicy).where(
                CompanyHiringPolicy.company_id == company_id
            )
        )
        policy = policy_result.scalar_one_or_none()
        if policy:
            existing_answered = list(policy.answered_questions or [])
            if answered_field not in existing_answered:
                existing_answered.append(answered_field)
                policy.answered_questions = existing_answered
                policy.setup_progress = _calculate_progress(policy)
                if policy.setup_progress >= 100 and not policy.setup_completed_at:
                    policy.setup_completed_at = datetime.utcnow()
            await db.flush()

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
