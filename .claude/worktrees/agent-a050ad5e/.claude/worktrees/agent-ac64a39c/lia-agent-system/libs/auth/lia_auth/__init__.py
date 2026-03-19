"""
lia-auth — authentication interface and secrets provider.

Re-exports SecretsProvider, WorkOS dependencies, and auth utilities.
Usage:
    from lia_auth import SecretsProvider, get_secrets_provider, EnvProvider
    from lia_auth.dependencies import get_current_user, get_current_user_or_demo
"""
from lia_auth.secrets import SecretsProvider, EnvProvider, get_secrets_provider

__all__ = [
    "SecretsProvider",
    "EnvProvider",
    "get_secrets_provider",
]
