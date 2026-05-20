"""
CV parser schemas — canonical lives in app/schemas/cv_parser.py.

Sprint E.2: this file used to duplicate all 9 classes verbatim. Replaced
with a shim re-export to satisfy the no-duplicate sensor.
"""
# Re-export from canonical module so callers using either path
# resolve to the same Pydantic class objects.
from app.schemas.cv_parser import *  # noqa: F401, F403
