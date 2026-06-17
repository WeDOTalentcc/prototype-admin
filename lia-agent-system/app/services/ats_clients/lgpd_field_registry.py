"""Shim: re-exports from canonical lgpd_field_registry location."""
from app.domains.ats_integration.services.ats_clients.lgpd_field_registry import *  # noqa: F401, F403
try:
    from app.domains.ats_integration.services.ats_clients.lgpd_field_registry import (  # noqa: F401
        OUTBOUND_SENSITIVE_FIELDS,
        filter_outbound,
        filter_inbound_text,
        get_inbound_text_fields,
    )
except ImportError:
    pass
