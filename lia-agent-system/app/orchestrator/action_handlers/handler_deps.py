"""UC-P1-20: Centralized handler dependency provider.

Replaces per-handler direct service instantiation with a single injectable
HandlerDeps container. The orchestrator / action executor builds one
HandlerDeps per request and passes it down so fairness, audit, and
permission concerns can be wired centrally without touching every handler.

Usage (handler side):
    async def execute_candidate_action(
        action_id: str,
        params: dict,
        context: dict,
        deps: HandlerDeps | None = None,
    ):
        deps = deps or HandlerDeps()
        svc = deps.pipeline_service
        ...

Usage (orchestrator/executor side):
    from app.orchestrator.action_handlers.handler_deps import HandlerDeps
    deps = HandlerDeps(db=db, company_id=company_id, user_id=user_id)
    result = await execute_candidate_action(action_id, params, context, deps=deps)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandlerDeps:
    """Dependencies available to all action handlers.

    Services are lazy-loaded on first access to avoid circular imports at
    module load time. Pass db and identity fields at construction time;
    service singletons will be initialised with them on demand.
    """

    db: Any = None
    company_id: str = ""
    user_id: str = ""

    # Private lazy-loaded service slots — accessed via properties below
    _pipeline_service: Any = field(default=None, repr=False)
    _fairness_guard: Any = field(default=None, repr=False)
    _audit_service: Any = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Lazy properties
    # ------------------------------------------------------------------

    @property
    def pipeline_service(self) -> Any:
        """Recruiter-assistant pipeline service (candidate stage management)."""
        if self._pipeline_service is None:
            from app.domains.recruiter_assistant.services.pipeline_service import (
                PipelineService,
            )
            self._pipeline_service = PipelineService(self.db)
        return self._pipeline_service

    @property
    def fairness_guard(self) -> Any:
        """Shared fairness guard for LGPD / bias checks on AI decisions."""
        if self._fairness_guard is None:
            from app.shared.compliance.fairness_guard import FairnessGuard

            self._fairness_guard = FairnessGuard()
        return self._fairness_guard

    @property
    def audit_service(self) -> Any:
        """Shared audit service for action event recording."""
        if self._audit_service is None:
            from app.shared.services.audit_service import AuditService

            self._audit_service = AuditService(self.db)
        return self._audit_service

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def with_identity(self, company_id: str, user_id: str) -> "HandlerDeps":
        """Return a copy of this deps object with updated identity fields."""
        return HandlerDeps(
            db=self.db,
            company_id=company_id,
            user_id=user_id,
        )
