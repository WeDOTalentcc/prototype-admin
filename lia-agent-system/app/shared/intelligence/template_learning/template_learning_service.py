"""
Template Learning Service — G9 stub.

Tracks email template performance (open/click rates) per company and
recommends the best-performing template variant for a given context.

Phase 1 (Alpha 1): Stub that records events and returns the most-used
template. Phase 2 will add Bayesian bandit selection and A/B cohort support.

Data model: in-memory dict (Phase 1) → Postgres table (Phase 2).
"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TemplatePerformance:
    """Tracks performance metrics for a single template variant."""

    __slots__ = ("template_id", "sends", "opens", "clicks", "last_used")

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        self.sends: int = 0
        self.opens: int = 0
        self.clicks: int = 0
        self.last_used: Optional[datetime] = None

    @property
    def open_rate(self) -> float:
        return self.opens / self.sends if self.sends > 0 else 0.0

    @property
    def click_rate(self) -> float:
        return self.clicks / self.sends if self.sends > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "sends": self.sends,
            "opens": self.opens,
            "clicks": self.clicks,
            "open_rate": round(self.open_rate, 4),
            "click_rate": round(self.click_rate, 4),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


class TemplateLearningService:
    """
    Phase 1 stub — records template usage and recommends best performer.

    Thread-safe for single-process usage. For multi-worker Celery,
    Phase 2 will persist to Postgres + Redis cache.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, TemplatePerformance]] = defaultdict(dict)

    def record_send(
        self,
        company_id: str,
        template_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        perf = self._get_or_create(company_id, template_id)
        perf.sends += 1
        perf.last_used = datetime.utcnow()
        logger.debug(
            "[TemplateLearning] send recorded company=%s template=%s total=%d",
            company_id, template_id, perf.sends,
        )

    def record_open(self, company_id: str, template_id: str) -> None:
        perf = self._get_or_create(company_id, template_id)
        perf.opens += 1

    def record_click(self, company_id: str, template_id: str) -> None:
        perf = self._get_or_create(company_id, template_id)
        perf.clicks += 1

    def recommend_template(
        self,
        company_id: str,
        context: Optional[Dict[str, Any]] = None,
        fallback_template_id: str = "default",
    ) -> str:
        """Return best-performing template_id for a company.

        Phase 1: picks highest open_rate with >= 5 sends.
        Phase 2: Bayesian Thompson Sampling with context features.
        """
        templates = self._data.get(company_id)
        if not templates:
            return fallback_template_id

        eligible = [t for t in templates.values() if t.sends >= 5]
        if not eligible:
            return fallback_template_id

        best = max(eligible, key=lambda t: t.open_rate)
        logger.debug(
            "[TemplateLearning] recommend company=%s best=%s open_rate=%.2f",
            company_id, best.template_id, best.open_rate,
        )
        return best.template_id

    def get_performance(
        self,
        company_id: str,
        template_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get performance metrics for one or all templates."""
        templates = self._data.get(company_id, {})
        if template_id:
            perf = templates.get(template_id)
            return [perf.to_dict()] if perf else []
        return [t.to_dict() for t in templates.values()]

    def _get_or_create(self, company_id: str, template_id: str) -> TemplatePerformance:
        if template_id not in self._data[company_id]:
            self._data[company_id][template_id] = TemplatePerformance(template_id)
        return self._data[company_id][template_id]


template_learning_service = TemplateLearningService()
