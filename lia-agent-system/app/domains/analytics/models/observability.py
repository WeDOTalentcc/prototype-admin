"""
Observability models — canonical source is libs/models/lia_models/observability.py.

Re-exports everything so both import paths work:
  from lia_models.observability import ...
  from app.domains.analytics.models.observability import ...

Do NOT add definitions here. Edit lia_models/observability.py instead.
"""
from lia_models.observability import *  # noqa: F401, F403
