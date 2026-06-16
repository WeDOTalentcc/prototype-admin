"""Backwards-compatibility shim — real implementation in libs/audit."""
from lia_audit.audit_models import (  # noqa: F401
    ExecutionAuditRecord,
    LLMCallRecord,
    NodeTransitionRecord,
    ToolCallRecord,
)
