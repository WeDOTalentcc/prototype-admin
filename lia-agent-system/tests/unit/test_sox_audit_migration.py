"""UC-P0-06: SOXAuditLog client_id must not be nullable."""
from lia_models.audit_logs import SOXAuditLog
import sqlalchemy as sa


def test_sox_audit_client_id_has_server_default():
    """client_id column must have server_default='system' for safe inserts."""
    col = SOXAuditLog.__table__.c.client_id
    assert col.server_default is not None, (
        "SOXAuditLog.client_id must have server_default='system'. "
        "This prevents NULL entries when company context is unavailable."
    )
    assert col.server_default.arg == "system", (
        f"Expected server_default='system', got '{col.server_default.arg}'"
    )


def test_sox_audit_client_id_column_exists():
    """client_id column must exist in the model."""
    col_names = [c.name for c in SOXAuditLog.__table__.columns]
    assert "client_id" in col_names, "SOXAuditLog must have client_id column"
