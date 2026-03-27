"""
Backwards-compatibility shim.
Real implementation moved to libs/config (lia_config.celery_app).

All imports from `app.core.celery_app` continue to work unchanged.
Worker/Beat entry points:
  celery -A app.core.celery_app worker --loglevel=info
  celery -A app.core.celery_app beat --loglevel=info
"""
from lia_config.celery_app import celery_app  # noqa: F401
