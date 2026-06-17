# LIA-T05 — hiring_policy PolicyService
# LGPD Art. 20: Right to explanation for automated decisions
# EU AI Act Annex III item 4: High-risk AI in recruitment

import logging
import uuid
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class PolicyService:
    """Manages hiring policy compliance checks."""

    async def check_disparate_impact(self, group_rates: dict[str, float]) -> float:
        """Compute disparate impact ratio (IEEE 7003). Threshold: >= 0.8."""
        if not group_rates:
            return 1.0
        rates = list(group_rates.values())
        return min(rates) / max(rates) if max(rates) > 0 else 1.0

    async def generate_explanation(
        self, candidate_id: str, decision: str, factors: list[str]
    ) -> dict:
        """LGPD Art. 20 — generate human-readable explanation for automated decision."""
        explanation = (
            f"A decisão '{decision}' foi baseada nos seguintes fatores: "
            + ", ".join(factors[:5])
            + "."
        )
        return {
            "report_id": f"EXP-{str(uuid.uuid4())[:8]}",
            "candidate_id": candidate_id,
            "decision": decision,
            "explanation": explanation,
            "factors": factors,
            "model_version": "lia-v1",
            "timestamp": datetime.now(UTC).isoformat(),
        }
