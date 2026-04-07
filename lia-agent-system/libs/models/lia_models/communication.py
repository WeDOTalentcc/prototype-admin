"""
CommunicationLog — canonical SQLAlchemy model.
Migrated from app/models/communication.py as part of Phase 3 consolidation.

Note: CommunicationLog is a thin alias over CommunicationHistory, which is the
canonical table. Both names refer to the same table (communication_history).
"""
from lia_models.communication_history import (
    CommunicationHistory,
    CommunicationType,
    CommunicationChannel,
    CommunicationDirection,
    CommunicationStatus,
)

# CommunicationLog is an alias for CommunicationHistory.
# The proactive_alert_service uses CommunicationLog; this alias keeps
# backwards compatibility without creating a second table.
CommunicationLog = CommunicationHistory

__all__ = [
    "CommunicationLog",
    "CommunicationHistory",
    "CommunicationType",
    "CommunicationChannel",
    "CommunicationDirection",
    "CommunicationStatus",
]
