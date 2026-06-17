"""
Working Memory - Persistent agent state across messages.

Unlike conversation history (what was said), working memory tracks
what the agent KNOWS and what it PLANS to do. Think of it as the
agent's notepad that persists between messages.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text, select
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import AsyncSessionLocal, Base

logger = logging.getLogger(__name__)


class AgentWorkingMemory(Base):
    """SQLAlchemy model for persisting agent reasoning state."""

    __tablename__ = "agent_working_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)
    domain = Column(String(100), nullable=False)
    current_stage = Column(String(100), nullable=True)
    collected_fields = Column(JSON, default=dict)
    current_plan = Column(JSON, default=list)
    pending_actions = Column(JSON, default=list)
    adjustment_history = Column(JSON, default=list)
    parecer_data = Column(JSON, default=dict)
    accepted_suggestions = Column(JSON, default=list)
    rejected_suggestions = Column(JSON, default=list)
    agent_notes = Column(Text, nullable=True)
    iteration_count = Column(Integer, default=0)
    last_intent = Column(String(100), nullable=True)
    last_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    company_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)


class WorkingMemorySchema(BaseModel):
    """Pydantic schema for serializing working memory state."""

    id: Optional[str] = None
    session_id: str
    domain: str
    current_stage: Optional[str] = None
    collected_fields: Dict[str, Any] = Field(default_factory=dict)
    current_plan: List[Any] = Field(default_factory=list)
    pending_actions: List[Any] = Field(default_factory=list)
    adjustment_history: List[Any] = Field(default_factory=list)
    parecer_data: Dict[str, Any] = Field(default_factory=dict)
    accepted_suggestions: List[Any] = Field(default_factory=list)
    rejected_suggestions: List[Any] = Field(default_factory=list)
    agent_notes: Optional[str] = None
    iteration_count: int = 0
    last_intent: Optional[str] = None
    last_confidence: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    company_id: str = ""
    user_id: str = ""

    class Config:
        from_attributes = True


class WorkingMemoryService:
    """Service for managing agent working memory across sessions.

    Provides CRUD operations and domain-specific helpers for reading
    and updating the persistent reasoning state that agents maintain
    between user messages.
    """

    async def get_or_create(
        self,
        session_id: str,
        domain: str,
        company_id: str,
        user_id: str,
    ) -> AgentWorkingMemory:
        """Retrieve existing working memory or create a new one.

        Args:
            session_id: The session identifier.
            domain: The agent domain (e.g. 'wizard', 'pipeline').
            company_id: Company ID for multi-tenancy.
            user_id: The user interacting with the agent.

        Returns:
            The existing or newly created AgentWorkingMemory instance.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()

            if memory is None:
                memory = AgentWorkingMemory(
                    session_id=session_id,
                    domain=domain,
                    company_id=company_id,
                    user_id=user_id,
                    collected_fields={},
                    current_plan=[],
                    pending_actions=[],
                    adjustment_history=[],
                    parecer_data={},
                    accepted_suggestions=[],
                    rejected_suggestions=[],
                    iteration_count=0,
                )
                session.add(memory)
                await session.commit()
                await session.refresh(memory)
                logger.info(
                    f"Created new working memory for session={session_id} domain={domain}"
                )
            else:
                logger.debug(
                    f"Found existing working memory for session={session_id} domain={domain}"
                )

            return memory

    async def update_memory(
        self,
        session_id: str,
        domain: str,
        updates: Dict[str, Any],
        company_id: str = "",
    ) -> AgentWorkingMemory:
        """Update specific fields on the working memory record.

        Args:
            session_id: The session identifier.
            domain: The agent domain.
            updates: Dictionary of field names to new values.

        Returns:
            The updated AgentWorkingMemory instance.

        Raises:
            ValueError: If no working memory exists for the given session/domain.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()

            if memory is None:
                raise ValueError(
                    f"No working memory found for session={session_id} domain={domain}"
                )

            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)

            memory.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()
            await session.refresh(memory)
            logger.debug(
                f"Updated working memory for session={session_id} domain={domain}: "
                f"fields={list(updates.keys())}"
            )
            return memory

    async def add_collected_field(
        self,
        session_id: str,
        domain: str,
        field_name: str,
        value: Any,
        confidence: float,
        source: str,
        company_id: str = "",
    ) -> None:
        """Add or update a collected field in the working memory.

        Args:
            session_id: The session identifier.
            domain: The agent domain.
            field_name: Name of the field being collected.
            value: The field value.
            confidence: Confidence score for the extraction (0.0-1.0).
            source: Where the value came from (e.g. 'user_message', 'tool_result').
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()
            if memory is None:
                logger.warning(
                    f"Cannot add field: no working memory for session={session_id} domain={domain}"
                )
                return

            fields: Dict[str, Any] = dict(memory.collected_fields or {})  # type: ignore
            fields[field_name] = {
                "value": value,
                "confidence": confidence,
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
            }
            memory.collected_fields = fields  # type: ignore
            memory.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()
            logger.debug(
                f"Added collected field '{field_name}' for session={session_id} domain={domain}"
            )

    async def add_adjustment(
        self,
        session_id: str,
        domain: str,
        field: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        company_id: str = "",
    ) -> None:
        """Record a field value adjustment in the history.

        Args:
            session_id: The session identifier.
            domain: The agent domain.
            field: Name of the field being adjusted.
            old_value: Previous value of the field.
            new_value: New value of the field.
            reason: Why the adjustment was made.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()
            if memory is None:
                logger.warning(
                    f"Cannot add adjustment: no working memory for session={session_id} domain={domain}"
                )
                return

            history = list(memory.adjustment_history or [])  # type: ignore
            history.append(
                {
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            memory.adjustment_history = history  # type: ignore
            memory.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()
            logger.debug(
                f"Added adjustment for field '{field}' in session={session_id} domain={domain}"
            )

    async def set_plan(
        self,
        session_id: str,
        domain: str,
        plan: List[Any],
        company_id: str = "",
    ) -> None:
        """Set the current plan (list of next steps) for the agent.

        Args:
            session_id: The session identifier.
            domain: The agent domain.
            plan: List of planned next steps.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()
            if memory is None:
                logger.warning(
                    f"Cannot set plan: no working memory for session={session_id} domain={domain}"
                )
                return

            memory.current_plan = plan  # type: ignore
            memory.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()
            logger.debug(
                f"Set plan with {len(plan)} steps for session={session_id} domain={domain}"
            )

    async def get_context_summary(
        self,
        session_id: str,
        domain: str,
        company_id: str = "",
    ) -> str:
        """Generate a human-readable summary of the working memory state.

        This summary is intended for injection into LLM prompts so the agent
        can recall what it knows and what it planned to do.

        Args:
            session_id: The session identifier.
            domain: The agent domain.

        Returns:
            A formatted string summarizing the current working memory state.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()

            if memory is None:
                return "No working memory found for this session."

            parts: List[str] = []

            parts.append(f"Domain: {memory.domain}")
            if memory.current_stage:  # type: ignore
                parts.append(f"Current Stage: {memory.current_stage}")
            parts.append(f"Iteration: {memory.iteration_count}")

            if memory.last_intent:  # type: ignore
                parts.append(
                    f"Last Intent: {memory.last_intent} "
                    f"(confidence: {memory.last_confidence or 0:.2f})"  # type: ignore
                )

            collected: dict = memory.collected_fields or {}  # type: ignore
            if collected:
                parts.append("Collected Fields:")
                for field_name, field_data in collected.items():
                    if isinstance(field_data, dict):
                        val = field_data.get("value", "?")
                        conf = field_data.get("confidence", 0)
                        parts.append(f"  - {field_name}: {val} (confidence: {conf:.2f})")
                    else:
                        parts.append(f"  - {field_name}: {field_data}")

            plan: list = memory.current_plan or []  # type: ignore
            if plan:
                parts.append("Current Plan:")
                for i, step in enumerate(plan, 1):
                    parts.append(f"  {i}. {step}")

            pending: list = memory.pending_actions or []  # type: ignore
            if pending:
                parts.append(f"Pending Actions: {len(pending)} action(s) awaiting confirmation")

            if memory.agent_notes:  # type: ignore
                parts.append(f"Agent Notes: {memory.agent_notes}")

            return "\n".join(parts)

    async def increment_iteration(
        self,
        session_id: str,
        domain: str,
        company_id: str = "",
    ) -> None:
        """Increment the iteration counter for the working memory.

        Args:
            session_id: The session identifier.
            domain: The agent domain.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentWorkingMemory).where(
                    AgentWorkingMemory.session_id == session_id,  # type: ignore
                    AgentWorkingMemory.domain == domain,  # type: ignore
                    AgentWorkingMemory.company_id == company_id,  # type: ignore  # Multi-tenancy
                )
            )
            memory = result.scalar_one_or_none()
            if memory is None:
                logger.warning(
                    f"Cannot increment iteration: no working memory for "
                    f"session={session_id} domain={domain}"
                )
                return

            memory.iteration_count = (memory.iteration_count or 0) + 1  # type: ignore
            memory.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()
            logger.debug(
                f"Incremented iteration to {memory.iteration_count} "
                f"for session={session_id} domain={domain}"
            )
