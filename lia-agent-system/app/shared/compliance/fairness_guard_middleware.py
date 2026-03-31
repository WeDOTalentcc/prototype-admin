"""
FairnessGuard Middleware — Reusable decorator for FastAPI endpoints (G1).

Applies FairnessGuard L1 (regex) + L2 (implicit bias) checks on text fields
in request bodies or response payloads. Can be used as:
  1. A FastAPI dependency (for request-side checks)
  2. A utility function (for response-side checks after generation)

Gap addressed: G1 — FairnessGuard as reusable middleware across all endpoints.
"""
import logging
from typing import List, Optional

from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


class FairnessViolation(Exception):
    """Raised when FairnessGuard L1 detects explicit bias."""

    def __init__(
        self,
        result: FairnessCheckResult,
        field_name: str = "text",
    ):
        self.result = result
        self.field_name = field_name
        super().__init__(result.educational_message or "Viés detectado pelo FairnessGuard.")


class FairnessCheckOutput:
    """Result of a FairnessGuard middleware check on one or more text fields."""

    def __init__(self):
        self.is_blocked: bool = False
        self.blocked_field: Optional[str] = None
        self.blocked_result: Optional[FairnessCheckResult] = None
        self.warnings: List[str] = []
        self.checked_fields: List[str] = []

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def to_dict(self):
        d = {
            "fairness_checked": True,
            "fairness_fields_checked": self.checked_fields,
        }
        if self.warnings:
            d["fairness_warnings"] = self.warnings
        if self.is_blocked:
            d["fairness_blocked"] = True
            d["fairness_blocked_field"] = self.blocked_field
            d["fairness_category"] = self.blocked_result.category if self.blocked_result else None
            d["fairness_educational_message"] = (
                self.blocked_result.educational_message if self.blocked_result else None
            )
        return d


def check_fairness(
    texts: dict[str, str],
    context: str = "endpoint",
    company_id: str = "",
    raise_on_block: bool = False,
) -> FairnessCheckOutput:
    """Check multiple text fields against FairnessGuard L1 + L2.

    Args:
        texts: mapping of field_name -> text_content to check.
        context: logging context (e.g. "jd_generation", "wsi_questions").
        company_id: for audit logging.
        raise_on_block: if True, raises FairnessViolation on L1 block.

    Returns:
        FairnessCheckOutput with aggregated results.
    """
    output = FairnessCheckOutput()

    for field_name, text in texts.items():
        if not text or not text.strip():
            continue

        output.checked_fields.append(field_name)

        result = _fairness_guard.check(text)

        if result.is_blocked:
            logger.warning(
                "[FairnessGuardMiddleware][%s] L1 BLOCKED field=%s category=%s terms=%s",
                context, field_name, result.category, result.blocked_terms,
            )
            output.is_blocked = True
            output.blocked_field = field_name
            output.blocked_result = result

            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_fairness_guard.log_check(
                        result=result,
                        context=context,
                        company_id=company_id,
                    ))
            except Exception:
                pass

            if raise_on_block:
                raise FairnessViolation(result=result, field_name=field_name)
            return output

        if result.soft_warnings:
            for w in result.soft_warnings:
                if w not in output.warnings:
                    output.warnings.append(w)
            logger.info(
                "[FairnessGuardMiddleware][%s] L2 warnings field=%s count=%d",
                context, field_name, len(result.soft_warnings),
            )

    return output


async def check_fairness_async(
    texts: dict[str, str],
    context: str = "endpoint",
    company_id: str = "",
    include_semantic: bool = False,
) -> FairnessCheckOutput:
    """Async version with optional L3 (semantic) check.

    Args:
        texts: mapping of field_name -> text_content to check.
        context: logging context.
        company_id: for audit logging.
        include_semantic: if True, runs L3 semantic check on non-blocked fields.

    Returns:
        FairnessCheckOutput with aggregated results.
    """
    output = check_fairness(texts, context=context, company_id=company_id)

    if output.is_blocked:
        return output

    if include_semantic:
        for field_name, text in texts.items():
            if not text or not text.strip():
                continue
            try:
                sem_result = await _fairness_guard.check_semantic(text, context=context)
                if sem_result.is_blocked:
                    logger.warning(
                        "[FairnessGuardMiddleware][%s] L3 semantic BLOCKED field=%s",
                        context, field_name,
                    )
                    output.is_blocked = True
                    output.blocked_field = field_name
                    output.blocked_result = sem_result
                    return output
                if sem_result.soft_warnings:
                    for w in sem_result.soft_warnings:
                        if w not in output.warnings:
                            output.warnings.append(w)
            except Exception as e:
                logger.debug(
                    "[FairnessGuardMiddleware][%s] L3 semantic skipped for %s: %s",
                    context, field_name, e,
                )

    return output


def check_rejection_reason(
    reason: str,
    candidate_name: str = "",
    company_id: str = "",
) -> FairnessCheckOutput:
    """Specialized check for candidate rejection reasons (G2).

    Runs L1 + L2 on the rejection reason text.
    """
    if not reason or not reason.strip():
        return FairnessCheckOutput()

    return check_fairness(
        texts={"rejection_reason": reason},
        context="candidate_rejection",
        company_id=company_id,
    )
