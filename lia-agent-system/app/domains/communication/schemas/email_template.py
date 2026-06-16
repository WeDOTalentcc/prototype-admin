"""
Email template schemas — canonical lives in app/schemas/email_template.py.

Sprint E.2: this file used to duplicate all 21 classes verbatim. Replaced
with a shim re-export to satisfy the no-duplicate sensor (R-008/ADR-SCHEMAS-001).
"""
# Re-export from canonical module so callers using either path
# resolve to the same Pydantic class objects.
from app.schemas.email_template import *  # noqa: F401, F403
