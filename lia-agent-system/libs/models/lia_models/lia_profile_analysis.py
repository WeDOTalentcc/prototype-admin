"""
LIA Profile Analysis models for storing AI-generated candidate summaries.

Supports three analysis types:
1. Bullet Points - Concise bullet-point summary
2. Short Paragraph - Flowing paragraph summary  
3. Detailed Bullets - Comprehensive sectioned summary
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


class AnalysisType(enum.Enum):
    """Type of profile analysis."""
    BULLET_POINTS = "bullet_points"
    SHORT_PARAGRAPH = "short_paragraph"
    DETAILED_BULLETS = "detailed_bullets"


class LiaProfileAnalysis(Base):
    """
    LIA's AI-generated profile analysis for a candidate.
    
    Stores generated summaries that can be displayed in the 
    "Pareceres e Análises" tab alongside opinions.
    """
    __tablename__ = "lia_profile_analyses"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(String(255), nullable=False, index=True)
    
    analysis_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    candidate_name = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    company_id = Column(String(100), nullable=False, index=True)
    
    def __repr__(self):
        return f"<LiaProfileAnalysis {self.id} - {self.analysis_type}>"
    
    def to_dict(self) -> dict:
        """Return dictionary representation."""
        return {
            "id": str(self.id),
            "candidate_id": self.candidate_id,
            "analysis_type": self.analysis_type,
            "content": self.content,
            "candidate_name": self.candidate_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "company_id": self.company_id,
        }
