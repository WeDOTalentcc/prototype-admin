"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.domains.communication.services.email_tracking_service import *  # noqa: F401, F403
from app.domains.communication.services.email_tracking_service import _sha256, _hash_ip, _hash_email  # noqa: F401
