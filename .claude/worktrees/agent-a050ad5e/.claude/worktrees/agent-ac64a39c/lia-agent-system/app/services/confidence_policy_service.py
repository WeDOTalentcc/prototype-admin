"""
Confidence Policy Service for Job Wizard Enhancement.

Manages confidence calculations and decision policies for
auto-applying inferred values during job creation wizard flow.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ConfidenceAction(str, Enum):
    """Actions to take based on confidence levels."""
    APPLY_SILENT = "apply_silent"
    APPLY_NOTIFY = "apply_notify"
    ASK_USER = "ask_user"
    ALERT_CONFLICT = "alert_conflict"


@dataclass
class ConfidenceThresholds:
    """
    Thresholds for determining actions based on confidence.
    
    Attributes:
        silent_apply: Minimum confidence to auto-apply without notification
        apply_notify: Minimum confidence to auto-apply with notification
        ask_user: Minimum confidence to present as suggestion requiring confirmation
    """
    silent_apply: float = 0.85
    apply_notify: float = 0.70
    ask_user: float = 0.50


SOURCE_BASE_CONFIDENCE: Dict[str, float] = {
    "text_extraction": 0.70,
    "company_default": 0.85,
    "benchmark": 0.60,
    "similar_jobs": 0.75,
    "recruiter_history": 0.80,
    "ai_generation": 0.65,
    "fixed": 1.0,
    "session": 1.0,
    "system": 1.0,
    "calculation": 0.75,
}

MULTI_SOURCE_AGREE_BONUS = 0.10
MULTI_SOURCE_DISAGREE_PENALTY = 0.30
MAX_CONFIDENCE = 0.95


@dataclass
class ConfidenceResult:
    """Result of a confidence calculation."""
    confidence: float
    sources: List[str]
    adjustments: List[str]
    action: ConfidenceAction


class ConfidencePolicyService:
    """
    Service for calculating and applying confidence policies.
    
    Determines how confident we are in inferred values and what
    action to take based on that confidence.
    """
    
    def __init__(self, thresholds: Optional[ConfidenceThresholds] = None):
        self.thresholds = thresholds or ConfidenceThresholds()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate_field_confidence(
        self,
        field: str,
        value: Any,
        sources: List[Dict[str, Any]]
    ) -> ConfidenceResult:
        """
        Calculate confidence for a field value based on its sources.
        
        Args:
            field: Field name being evaluated
            value: The inferred value
            sources: List of sources with their values and types
                    Example: [{"type": "text_extraction", "value": "Senior"}]
        
        Returns:
            ConfidenceResult with calculated confidence and recommended action
        """
        if not sources:
            return ConfidenceResult(
                confidence=0.0,
                sources=[],
                adjustments=["no_sources"],
                action=ConfidenceAction.ASK_USER
            )
        
        source_confidences = []
        source_types = []
        adjustments = []
        
        for source in sources:
            source_type = source.get("type", "unknown")
            base_confidence = SOURCE_BASE_CONFIDENCE.get(source_type, 0.50)
            source_confidences.append(base_confidence)
            source_types.append(source_type)
        
        base_confidence = max(source_confidences) if source_confidences else 0.0
        
        if len(sources) > 1:
            values = [s.get("value") for s in sources]
            unique_values = set(str(v) for v in values if v is not None)
            
            if len(unique_values) == 1:
                base_confidence = min(base_confidence + MULTI_SOURCE_AGREE_BONUS, MAX_CONFIDENCE)
                adjustments.append(f"multi_source_agreement:+{MULTI_SOURCE_AGREE_BONUS}")
            else:
                base_confidence = max(base_confidence - MULTI_SOURCE_DISAGREE_PENALTY, 0.0)
                adjustments.append(f"multi_source_conflict:-{MULTI_SOURCE_DISAGREE_PENALTY}")
        
        final_confidence = min(base_confidence, MAX_CONFIDENCE)
        
        action = self.get_action_for_confidence(final_confidence, self.thresholds)
        
        return ConfidenceResult(
            confidence=final_confidence,
            sources=source_types,
            adjustments=adjustments,
            action=action
        )
    
    def get_action_for_confidence(
        self,
        confidence: float,
        thresholds: Optional[ConfidenceThresholds] = None
    ) -> ConfidenceAction:
        """
        Determine the action to take based on confidence level.
        
        Args:
            confidence: Calculated confidence score (0.0 to 1.0)
            thresholds: Optional custom thresholds
        
        Returns:
            ConfidenceAction indicating what to do
        """
        t = thresholds or self.thresholds
        
        if confidence >= t.silent_apply:
            return ConfidenceAction.APPLY_SILENT
        elif confidence >= t.apply_notify:
            return ConfidenceAction.APPLY_NOTIFY
        elif confidence >= t.ask_user:
            return ConfidenceAction.ASK_USER
        else:
            return ConfidenceAction.ASK_USER
    
    def should_auto_apply(
        self,
        company_id: str,
        recruiter_id: str,
        field: str,
        confidence: float,
        thresholds: Optional[ConfidenceThresholds] = None
    ) -> Tuple[bool, str]:
        """
        Determine if a value should be auto-applied for a specific context.
        
        Args:
            company_id: Company making the request
            recruiter_id: Recruiter creating the job
            field: Field being considered
            confidence: Calculated confidence
            thresholds: Optional custom thresholds
        
        Returns:
            Tuple of (should_apply: bool, reason: str)
        """
        t = thresholds or self.thresholds
        action = self.get_action_for_confidence(confidence, t)
        
        if action == ConfidenceAction.APPLY_SILENT:
            return (True, f"High confidence ({confidence:.2f}) - auto-applied silently")
        
        if action == ConfidenceAction.APPLY_NOTIFY:
            return (True, f"Good confidence ({confidence:.2f}) - auto-applied with notification")
        
        if action == ConfidenceAction.ASK_USER:
            return (False, f"Low confidence ({confidence:.2f}) - requires user confirmation")
        
        return (False, f"Conflict detected - requires user resolution")
    
    def calculate_aggregate_confidence(
        self,
        field_confidences: Dict[str, float]
    ) -> float:
        """
        Calculate overall confidence for a draft based on individual field confidences.
        
        Args:
            field_confidences: Dict mapping field names to their confidence scores
        
        Returns:
            Aggregate confidence score
        """
        if not field_confidences:
            return 0.0
        
        return sum(field_confidences.values()) / len(field_confidences)
    
    def get_fields_needing_confirmation(
        self,
        field_confidences: Dict[str, float],
        thresholds: Optional[ConfidenceThresholds] = None
    ) -> List[str]:
        """
        Get list of fields that need user confirmation.
        
        Args:
            field_confidences: Dict mapping field names to confidence scores
            thresholds: Optional custom thresholds
        
        Returns:
            List of field names requiring confirmation
        """
        t = thresholds or self.thresholds
        return [
            field for field, confidence in field_confidences.items()
            if self.get_action_for_confidence(confidence, t) in (
                ConfidenceAction.ASK_USER,
                ConfidenceAction.ALERT_CONFLICT
            )
        ]
    
    def get_fields_with_conflicts(
        self,
        sources_by_field: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """
        Identify fields where sources provide conflicting values.
        
        Args:
            sources_by_field: Dict mapping field names to their source data
        
        Returns:
            List of field names with conflicting source values
        """
        conflicting_fields = []
        
        for field, sources in sources_by_field.items():
            if len(sources) <= 1:
                continue
            
            values = [s.get("value") for s in sources if s.get("value") is not None]
            unique_values = set(str(v) for v in values)
            
            if len(unique_values) > 1:
                conflicting_fields.append(field)
        
        return conflicting_fields


confidence_policy_service = ConfidencePolicyService()
