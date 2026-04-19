"""Goal service — chat-surface canonical for the recruiter assistant.

Provides a single entry point used by the recruiter_assistant chat tool
`assistant_track_goals`. The current implementation is a structured stub:
real targets/quotas live elsewhere (workflow, OKR), and this service
returns a deterministic shape so the chain can be exercised end-to-end
while the analytics pipeline is wired in a follow-up task.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class GoalService:
    """Aggregates user/team recruiting goals for the chat assistant."""

    async def get_user_goals(
        self,
        user_id: str = "",
        company_id: str | None = None,
        period: str = "current_month",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return the user's recruiting goals and current progress.

        Stub: returns an empty goals payload until the analytics aggregation
        pipeline is connected. The shape matches what the chat surface and
        downstream UI will consume.
        """
        logger.info(
            "GoalService.get_user_goals user=%s company=%s period=%s",
            user_id, company_id, period,
        )
        return {
            "success": True,
            "user_id": user_id,
            "company_id": company_id,
            "period": period,
            "goals": [],
            "summary": {
                "total": 0,
                "on_track": 0,
                "at_risk": 0,
                "achieved": 0,
            },
            "simulation_stub": True,
        }


goal_service = GoalService()


def get_goal_service() -> GoalService:
    return goal_service
