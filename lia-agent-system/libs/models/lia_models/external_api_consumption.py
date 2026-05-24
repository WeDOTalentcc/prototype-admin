import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from lia_config.database import Base


class ExternalApiProvider(str, enum.Enum):
    APIFY = "apify"
    PEARCH = "pearch"
    LLM = "llm"


class ExternalApiOperation(str, enum.Enum):
    ENRICH = "enrich"
    SEARCH = "search"
    REVEAL_EMAIL = "reveal_email"
    REVEAL_PHONE = "reveal_phone"
    APIFY_SEARCH = "apify_search"
    PROFILE_SCRAPE = "profile_scrape"
    EMAIL_FINDER = "email_finder"
    LLM_INFERENCE = "llm_inference"


class ExternalApiConsumption(Base):
    __tablename__ = "external_api_consumption"
    __table_args__ = (
        Index("ix_extapi_company_created", "company_id", "created_at"),
        Index("ix_extapi_company_provider", "company_id", "provider"),
        Index("ix_extapi_pipeline", "pipeline_id"),
    {"extend_existing": True}, )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    linkedin_url = Column(String(500), nullable=True)

    provider = Column(String(30), nullable=False, index=True)
    operation = Column(String(50), nullable=False, index=True)

    pipeline_id = Column(UUID(as_uuid=True), nullable=True)
    search_session_id = Column(String(100), nullable=True)
    actor_id = Column(String(200), nullable=True)

    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    model_name = Column(String(100), nullable=True)

    credits_consumed = Column(Integer, default=0, nullable=False)

    cost_usd = Column(Float, default=0.0, nullable=False)
    cost_brl = Column(Float, default=0.0, nullable=False)
    exchange_rate = Column(Float, default=5.50, nullable=False)

    success = Column(Boolean, default=False, nullable=False)
    result_status = Column(String(30), nullable=True)
    error_message = Column(String(500), nullable=True)
    response_time_ms = Column(Integer, default=0, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<ExternalApiConsumption {self.id} {self.provider}/{self.operation}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "user_id": self.user_id,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "linkedin_url": self.linkedin_url,
            "provider": self.provider,
            "operation": self.operation,
            "pipeline_id": str(self.pipeline_id) if self.pipeline_id else None,
            "search_session_id": self.search_session_id,
            "actor_id": self.actor_id,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "model_name": self.model_name,
            "credits_consumed": self.credits_consumed,
            "cost_usd": self.cost_usd,
            "cost_brl": self.cost_brl,
            "exchange_rate": self.exchange_rate,
            "success": self.success,
            "result_status": self.result_status,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
