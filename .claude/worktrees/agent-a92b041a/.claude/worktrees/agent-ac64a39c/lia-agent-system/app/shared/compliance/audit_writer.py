"""Backwards-compatibility shim — real implementation in libs/audit."""
from lia_audit.audit_writer import (  # noqa: F401
    AuditWriter,
    get_audit_writer,
)
