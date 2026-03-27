"""
Backwards-compatibility shim.
Real implementation moved to libs/config (lia_config.config).

All imports from `app.core.config` continue to work unchanged.
"""
from lia_config.config import (  # noqa: F401
    DatabaseSettings,
    CacheSettings,
    MessagingSettings,
    LLMSettings,
    AuditSettings,
    AuthSettings,
    AppSettings,
    IntegrationSettings,
    Settings,
    settings,
)
