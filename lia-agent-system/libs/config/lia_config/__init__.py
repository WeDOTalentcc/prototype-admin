"""
lia-config — LIA configuration, database session and Celery setup.

Exports:
    config   : Settings classes + settings singleton
    database : engine, Base, AsyncSessionLocal, get_db, async_session_factory
    celery_app: celery_app instance
"""
from .config import settings, Settings  # noqa: F401  # use relative import for path-based access
