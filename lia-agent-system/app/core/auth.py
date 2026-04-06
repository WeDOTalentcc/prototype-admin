"""
Compatibility shim — re-exports auth dependencies from canonical location.
Import from app.auth.dependencies directly in new code.
"""
from app.auth.dependencies import (  # noqa: F401
    get_current_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
