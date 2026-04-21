#!/usr/bin/env python3
"""Apply JWT blacklist changes to Replit — security.py, dependencies.py, auth.py."""
from pathlib import Path

BASE = Path("/home/runner/workspace/lia-agent-system/app")

# ── 1. security.py — append blacklist functions after decode_token ──
sec_path = BASE / "auth/security.py"
sec_text = sec_path.read_text()

if "blacklist_token" not in sec_text:
    blacklist_code = '''

# ── JWT Blacklist (logout / token revocation) ─────────────────────────────────

import hashlib
from datetime import timezone

_BLACKLIST_PREFIX = "jwt_blacklist:"


def _token_key(token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()
    return f"{_BLACKLIST_PREFIX}{digest}"


async def blacklist_token(token: str) -> None:
    """Add token to Redis blacklist until its natural expiry."""
    try:
        from app.core.redis_client import get_redis
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp is None:
            return
        ttl = int(exp - datetime.now(timezone.utc).timestamp())
        if ttl <= 0:
            return
        redis = await get_redis()
        if redis is None:
            return
        await redis.setex(_token_key(token), ttl, "1")
    except Exception:
        pass  # non-blocking — logout proceeds even if Redis is down


async def is_token_blacklisted(token: str) -> bool:
    """Return True if the token has been explicitly revoked."""
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        if redis is None:
            return False
        return bool(await redis.exists(_token_key(token)))
    except Exception:
        return False
'''
    sec_path.write_text(sec_text + blacklist_code)
    print("✓ auth/security.py — added blacklist_token + is_token_blacklisted")
else:
    print("○ auth/security.py — already has blacklist (skipped)")

# ── 2. dependencies.py — add is_token_blacklisted import + check ──
dep_path = BASE / "auth/dependencies.py"
dep_text = dep_path.read_text()

if "is_token_blacklisted" not in dep_text:
    # Fix import line
    dep_text = dep_text.replace(
        "from app.auth.security import decode_token",
        "from app.auth.security import decode_token, is_token_blacklisted"
    )

    # Add blacklist check inside get_current_user, after `token = credentials.credentials`
    dep_text = dep_text.replace(
        "    token = credentials.credentials\n\n    try:\n        payload = decode_token(token)",
        "    token = credentials.credentials\n\n    if await is_token_blacklisted(token):\n        raise HTTPException(\n            status_code=status.HTTP_401_UNAUTHORIZED,\n            detail=\"Token revogado. Faça login novamente.\",\n            headers={\"WWW-Authenticate\": \"Bearer\"},\n        )\n\n    try:\n        payload = decode_token(token)"
    )
    dep_path.write_text(dep_text)
    print("✓ auth/dependencies.py — added blacklist check in get_current_user")
else:
    print("○ auth/dependencies.py — already has blacklist check (skipped)")

# ── 3. auth.py — add blacklist_token import + /logout endpoint ──
auth_path = BASE / "api/v1/auth.py"
auth_text = auth_path.read_text()

if "blacklist_token" not in auth_text:
    # Add to security imports
    auth_text = auth_text.replace(
        "    verify_password,\n)",
        "    verify_password,\n    blacklist_token,\n)"
    )

    # Append logout endpoint at end of file
    logout_endpoint = '''

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    audit_svc: AuditService = Depends(get_audit_service),
):
    """Revoke the current access token (JWT blacklist via Redis)."""
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.removeprefix("Bearer ").strip()
        if auth_header.startswith("Bearer ")
        else ""
    )
    if token:
        await blacklist_token(token)

    await audit_svc.log_event(
        action="user.logout",
        actor_id=str(current_user.id),
        company_id=current_user.company_id or "unknown",
        resource_type="auth",
        resource_id=str(current_user.id),
        details={"email": str(current_user.id)},
    )
    return None
'''
    auth_text += logout_endpoint
    auth_path.write_text(auth_text)
    print("✓ api/v1/auth.py — added blacklist_token import + /logout endpoint")
else:
    print("○ api/v1/auth.py — already has logout endpoint (skipped)")

print("\nJWT blacklist patch complete.")
