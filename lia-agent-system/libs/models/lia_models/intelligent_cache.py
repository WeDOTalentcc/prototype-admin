"""
Intelligent Cache models for 3-layer caching system.

Provides token economy through intelligent caching:
- Session-level cache (in-memory, conversation duration)
- Redis L1 cache (short TTL for volatile data)
- PostgreSQL L2 cache (long TTL for stable patterns)

Also includes embeddings storage for semantic similarity matching.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, Index, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from lia_config.database import Base


class CacheEntry(Base):
    """
    PostgreSQL L2 cache for stable, expensive-to-compute data.
    
    Stores results of expensive operations like:
    - Market benchmark queries
    - LLM-generated content (JD summaries, skill suggestions)
    - Computed patterns and analytics
    
    Cache key format: {namespace}:{tenant_id}:{specific_key}
    Example: "salary_benchmark:company_abc:dev_senior_sp"
    """
    __tablename__ = "cache_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    cache_key = Column(String(512), nullable=False, unique=True, index=True)
    namespace = Column(String(100), nullable=False, index=True)
    # TENANT-EXEMPT: CacheEntry com company_id NULL = cache global compartilhado (namespace scope)
    company_id = Column(String(255), nullable=True, index=True)
    
    value = Column(JSON, nullable=False)
    value_type = Column(String(50), default="json")
    
    ttl_seconds = Column(Integer, nullable=False, default=86400)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime, nullable=True)
    
    source = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    
    tags = Column(ARRAY(String), default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_cache_entries_namespace_company', 'namespace', 'company_id'),
        Index('ix_cache_entries_expires', 'expires_at'),
        Index('ix_cache_entries_tags', 'tags', postgresql_using='gin'),
    {"extend_existing": True}, )


class QueryEmbedding(Base):
    """
    Stores embeddings for semantic similarity matching.
    
    Used to find similar queries and reuse cached results:
    - "Dev Python Senior SP" matches "Python Developer Sênior São Paulo"
    - Avoid redundant LLM calls for similar queries
    
    Embeddings are generated once and stored for fast similarity search.
    """
    __tablename__ = "query_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)
    
    namespace = Column(String(100), nullable=False, index=True)
    # TENANT-EXEMPT: QueryEmbedding com company_id NULL = embedding compartilhado entre tenants
    company_id = Column(String(255), nullable=True, index=True)
    
    embedding = Column(ARRAY(Float), nullable=False)
    embedding_model = Column(String(100), default="text-embedding-3-small")
    embedding_dimensions = Column(Integer, default=1536)
    
    cache_key = Column(String(512), nullable=True, index=True)
    
    hit_count = Column(Integer, default=0)
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_query_embeddings_namespace_company', 'namespace', 'company_id'),
    {"extend_existing": True}, )


class LearningPattern(Base):
    """
    Stores learned patterns for intelligent suggestions.
    
    Patterns are extracted from feedback and applied to future suggestions:
    - Salary patterns: "Senior Python in SP avg R$18k"
    - Skill patterns: "90% of Data roles use SQL"
    - Preference patterns: "This company always adds 'Day Off Aniversário'"
    
    Patterns have confidence scores based on sample size and recency.
    """
    __tablename__ = "learning_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    
    pattern_type = Column(String(100), nullable=False, index=True)
    pattern_key = Column(String(512), nullable=False, index=True)
    
    pattern_value = Column(JSON, nullable=False)
    
    sample_size = Column(Integer, default=1)
    acceptance_rate = Column(Float, default=1.0)
    
    confidence = Column(String(20), default="low")
    confidence_score = Column(Float, default=0.5)
    
    role_filter = Column(String(255), nullable=True, index=True)
    seniority_filter = Column(String(100), nullable=True)
    department_filter = Column(String(100), nullable=True)
    location_filter = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    expires_at = Column(DateTime, nullable=True)
    last_applied_at = Column(DateTime, nullable=True)
    last_confirmed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_learning_patterns_company_type', 'company_id', 'pattern_type'),
        Index('ix_learning_patterns_key', 'company_id', 'pattern_key'),
        Index('ix_learning_patterns_active', 'company_id', 'is_active'),
        Index('ix_learning_patterns_role', 'company_id', 'role_filter'),
        {"extend_existing": True},
    )


class FeedbackEvent(Base):
    """
    Unified feedback capture for all suggestion types.
    
    Silently captures every suggestion and its outcome:
    - accepted: User accepted without modification
    - modified: User accepted but changed the value
    - rejected: User explicitly rejected or ignored
    
    This is the raw data that feeds LearningPattern generation.
    """
    __tablename__ = "feedback_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    
    field_name = Column(String(100), nullable=False, index=True)
    stage = Column(String(100), nullable=True)
    
    suggested_value = Column(JSON, nullable=True)
    final_value = Column(JSON, nullable=True)
    
    outcome = Column(String(20), nullable=False, index=True)
    modification_delta = Column(JSON, nullable=True)
    
    role = Column(String(255), nullable=True, index=True)
    seniority = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    
    source = Column(String(100), nullable=True)
    source_confidence = Column(Float, nullable=True)
    
    response_time_ms = Column(Integer, nullable=True)
    
    processed_for_learning = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('ix_feedback_events_company_field', 'company_id', 'field_name'),
        Index('ix_feedback_events_outcome', 'company_id', 'outcome'),
        Index('ix_feedback_events_unprocessed', 'company_id', 'processed_for_learning'),
        Index('ix_feedback_events_role', 'company_id', 'role'),
    {"extend_existing": True}, )


class TokenUsageLog(Base):
    """
    Tracks token usage for cost monitoring and optimization.
    
    Logs every LLM call with token counts, enabling:
    - Cost tracking per company/feature
    - Identifying expensive operations for caching
    - Optimizing prompts for token efficiency
    """
    __tablename__ = "token_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=True)
    
    operation = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    
    estimated_cost_usd = Column(Float, nullable=True)
    
    cache_hit = Column(Boolean, default=False)
    cache_key = Column(String(512), nullable=True)
    
    latency_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_token_usage_company_op', 'company_id', 'operation'),
        Index('ix_token_usage_date', 'created_at'),
    {"extend_existing": True}, )
