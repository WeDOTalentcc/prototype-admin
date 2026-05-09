# pg_insert exposed for test patchability (tests patch this attr)
try:
    from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: F401
except ImportError:
    pg_insert = None  # noqa: F841
"""Shim: re-exports from app.shared.services.checkpoint_service (canonical location).

Tests patch via app.services.checkpoint_service — this shim ensures importability.
"""
from app.shared.services.checkpoint_service import *  # noqa: F401, F403
try:
    from app.shared.services.checkpoint_service import *  # noqa: F401, F403
except ImportError:
    pass
