"""
WSI Weight Configuration - Universal Scoring Model

This module defines the universal weights for candidate scoring.
A single, consistent scoring model is used across all industries
to ensure fair and unbiased evaluation of candidates.

Design Decision (December 2025):
- Industry-specific weights were removed to prevent potential biases
- A universal model ensures consistent evaluation across all candidates
- If customization is needed in the future, it should be per-vacancy
  with explicit justification and audit trail
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class ScoringWeights:
    """
    Universal weight configuration for candidate scoring.
    
    Profile Weights (must sum to 1.0):
    - skills_match: How well candidate skills match requirements
    - experience_match: Relevance of work experience
    - seniority_match: Alignment with required seniority level
    - location_match: Geographic compatibility
    - title_match: Job title alignment
    
    WSI Weights (must sum to 1.0):
    - technical_competency: Technical skills demonstrated in WSI
    - behavioral_competency: Behavioral skills demonstrated in WSI
    - cultural_fit: Alignment with company culture
    - communication: Communication skills quality
    """
    skills_match: float = 0.35
    experience_match: float = 0.20
    seniority_match: float = 0.15
    location_match: float = 0.15
    title_match: float = 0.15
    
    technical_competency: float = 0.40
    behavioral_competency: float = 0.30
    cultural_fit: float = 0.15
    communication: float = 0.15
    
    def validate(self) -> bool:
        """Ensure weights sum to 1.0 for each category."""
        profile_sum = (
            self.skills_match + self.experience_match + 
            self.seniority_match + self.location_match + self.title_match
        )
        wsi_sum = (
            self.technical_competency + self.behavioral_competency +
            self.cultural_fit + self.communication
        )
        return abs(profile_sum - 1.0) < 0.01 and abs(wsi_sum - 1.0) < 0.01
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_weights": {
                "skills_match": self.skills_match,
                "experience_match": self.experience_match,
                "seniority_match": self.seniority_match,
                "location_match": self.location_match,
                "title_match": self.title_match,
            },
            "wsi_weights": {
                "technical_competency": self.technical_competency,
                "behavioral_competency": self.behavioral_competency,
                "cultural_fit": self.cultural_fit,
                "communication": self.communication,
            }
        }


UNIVERSAL_WEIGHTS = ScoringWeights()

IndustryWeights = ScoringWeights

from enum import Enum, StrEnum


class Industry(StrEnum):
    """
    Industry enum kept for backward compatibility.
    
    DEPRECATED: Industry-specific weights have been removed.
    All values now return the same universal weights.
    This enum is preserved only to prevent import errors.
    """
    DEFAULT = "default"
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    CONSULTING = "consulting"
    EDUCATION = "education"
    GOVERNMENT = "government"
    STARTUPS = "startups"

INDUSTRY_WEIGHTS = {industry: UNIVERSAL_WEIGHTS for industry in Industry}


def get_weights() -> ScoringWeights:
    """Get the universal scoring weights."""
    return UNIVERSAL_WEIGHTS


def get_weights_for_industry(industry: str | None = None) -> ScoringWeights:
    """
    Get scoring weights (legacy compatibility function).
    
    Note: Industry-specific weights have been removed.
    This function now always returns universal weights regardless
    of the industry parameter.
    
    Args:
        industry: Ignored. Kept for backward compatibility.
        
    Returns:
        Universal ScoringWeights instance.
    """
    return UNIVERSAL_WEIGHTS


def list_available_industries() -> list[str]:
    """
    List available configurations (legacy compatibility).
    
    Returns only 'default' as industry-specific weights were removed.
    """
    return ["default"]
