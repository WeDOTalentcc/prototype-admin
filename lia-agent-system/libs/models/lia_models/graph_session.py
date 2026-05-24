"""
Graph Session Model - Database-backed session state persistence.

Provides durable storage for job wizard graph sessions across restarts.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from lia_config.database import Base


class GraphSession(Base):
    """
    Persistent storage for graph session state.
    
    Stores the full state of job wizard sessions for:
    - Multi-turn conversation persistence across restarts
    - Session recovery after connection loss
    - Analytics and audit trail
    """
    __tablename__ = "graph_sessions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    current_stage = Column(String(50), default="initial")
    job_draft = Column(JSON, default=dict)
    confidence_scores = Column(JSON, default=dict)
    messages = Column(JSON, default=list)
    
    reasoning_steps = Column(JSON, default=list)
    tool_calls = Column(JSON, default=list)
    tool_results = Column(JSON, default=list)
    extracted_fields = Column(JSON, default=dict)
    
    last_response = Column(String, nullable=True)
    last_intent = Column(String(50), nullable=True)
    error = Column(String, nullable=True)
    
    is_complete = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    execution_count = Column(String, default="0")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    def to_state(self) -> dict:
        """Convert to JobWizardState dict."""
        return {
            "session_id": self.session_id,  # type: ignore
            "company_id": str(self.company_id) if self.company_id else "",  # type: ignore
            "user_id": self.user_id,  # type: ignore
            "current_stage": self.current_stage if self.current_stage else "initial",  # type: ignore
            "job_draft": dict(self.job_draft) if self.job_draft else {},  # type: ignore
            "confidence_scores": dict(self.confidence_scores) if self.confidence_scores else {},  # type: ignore
            "messages": list(self.messages) if self.messages else [],  # type: ignore
            "reasoning_steps": list(self.reasoning_steps) if self.reasoning_steps else [],  # type: ignore
            "tool_calls": list(self.tool_calls) if self.tool_calls else [],  # type: ignore
            "tool_results": list(self.tool_results) if self.tool_results else [],  # type: ignore
            "extracted_fields": dict(self.extracted_fields) if self.extracted_fields else {},  # type: ignore
            "response_text": self.last_response,  # type: ignore
            "intent": self.last_intent,  # type: ignore
            "error": self.error,  # type: ignore
            "should_continue": True,
            "needs_clarification": False
        }
    
    @classmethod
    def from_state(cls, state: dict, session_id: str | None = None) -> "GraphSession":
        """Create from JobWizardState dict."""
        import logging
        from uuid import UUID as UUID_type
        
        logger = logging.getLogger(__name__)
        
        company_id = state.get("company_id")
        original_company_id = company_id
        
        if isinstance(company_id, str):
            try:
                company_id = UUID_type(company_id)
            except (ValueError, AttributeError):
                raise ValueError(
                    f"Invalid company_id '{original_company_id}'. "
                    "A valid UUID is required for multi-tenant support."
                )
        elif company_id is None:
            raise ValueError(
                "company_id is required. "
                "A valid UUID must be provided for multi-tenant support."
            )
        
        return cls(
            session_id=session_id or state.get("session_id"),
            company_id=company_id,
            user_id=state.get("user_id", ""),
            current_stage=state.get("current_stage", "initial"),
            job_draft=state.get("job_draft", {}),
            confidence_scores=state.get("confidence_scores", {}),
            messages=state.get("messages", []),
            reasoning_steps=state.get("reasoning_steps", []),
            tool_calls=state.get("tool_calls", []),
            tool_results=state.get("tool_results", []),
            extracted_fields=state.get("extracted_fields", {}),
            last_response=state.get("response_text"),
            last_intent=state.get("intent"),
            error=state.get("error"),
            is_complete=state.get("current_stage") == "complete"
        )
    
    def update_from_state(self, state: dict) -> None:
        """Update fields from state dict."""
        self.current_stage = state.get("current_stage", self.current_stage)
        self.job_draft = state.get("job_draft", self.job_draft)
        self.confidence_scores = state.get("confidence_scores", self.confidence_scores)
        self.messages = state.get("messages", self.messages)
        self.reasoning_steps = state.get("reasoning_steps", self.reasoning_steps)
        self.tool_calls = state.get("tool_calls", self.tool_calls)
        self.tool_results = state.get("tool_results", self.tool_results)
        self.extracted_fields = state.get("extracted_fields", self.extracted_fields)
        self.last_response = state.get("response_text")
        self.last_intent = state.get("intent")
        self.error = state.get("error")
        self.is_complete = state.get("current_stage") == "complete"
        self.last_activity_at = datetime.utcnow()
