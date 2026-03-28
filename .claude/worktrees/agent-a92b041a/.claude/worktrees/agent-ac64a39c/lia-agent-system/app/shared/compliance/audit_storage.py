"""Backwards-compatibility shim — real implementation in libs/audit."""
from lia_audit.audit_storage import (  # noqa: F401
    AuditStorage,
    LocalFileStorage,
    S3Storage,
    build_storage_path,
    get_audit_storage,
)
