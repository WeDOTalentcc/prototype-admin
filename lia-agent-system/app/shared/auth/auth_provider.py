"""
AuthProvider — abstração leve sobre o sistema de auth híbrido.

Harness: Guide computacional — sub-apps dependem de AuthContext,
         nunca de app/auth/ diretamente.

Dois caminhos internos (transparentes para os callers):
  LOCAL: FastAPI JWT (decode_token → User por UUID)
  RAILS: Rails JWT fallback (validate_rails_token → auto-provisiona User)
  WORKOS: WorkOS SSO → vira JWT LOCAL via auth_router (mesmo caminho)

Sprint F: api-onboarding importa get_auth_context_dependency(), não app/auth/dependencies.
"""
from __future__ import annotations

import dataclasses
import enum
import logging
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.auth.models import User

logger = logging.getLogger(__name__)

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class AuthSource(str, enum.Enum):
    """Origem da autenticação resolvida."""
    LOCAL = "local"    # FastAPI JWT gerado localmente
    RAILS = "rails"    # JWT do backend Rails (legacy/bridge)
    WORKOS = "workos"  # WorkOS SSO → vira LOCAL via auth_router


@dataclasses.dataclass
class AuthContext:
    """
    Contexto de autenticação resolvido — único objeto que sub-apps precisam.

    Campos:
        user: User model (retrocompat com get_current_active_user)
        company_id: tenant UUID string
        auth_source: AuthSource enum
        roles: lista de roles do usuário (ex: ["recruiter"])
    """
    user: "User"
    company_id: str
    auth_source: AuthSource
    roles: list

    @property
    def is_wedotalent_admin(self) -> bool:
        return "wedotalent_admin" in self.roles

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles or self.is_wedotalent_admin

    def has_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)


class AuthProvider:
    """
    Resolve AuthContext a partir de um Bearer token.
    Esconde os dois caminhos de autenticação (LOCAL e RAILS).
    """

    async def resolve(
        self,
        token: str,
        db: "AsyncSession",
    ) -> "AuthContext":
        """
        Resolve AuthContext para o token fornecido.

        Returns:
            AuthContext com user, company_id, auth_source, roles.

        Raises:
            HTTPException 401 se token inválido.
            HTTPException 403 se usuário inativo.
        """
        user, source = await self._get_user_from_token(token, db)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        company_id = str(user.company_id or "")
        roles = [str(user.role)] if user.role else []

        return AuthContext(
            user=user,
            company_id=company_id,
            auth_source=source or AuthSource.LOCAL,
            roles=roles,
        )

    async def _get_user_from_token(
        self,
        token: str,
        db: "AsyncSession",
    ) -> "tuple":
        """
        Tenta os dois caminhos em ordem: LOCAL → RAILS.
        Retorna (user, source) ou (None, None) se ambos falharem.
        """
        # Path 1: tenta FastAPI JWT
        try:
            from app.auth.security import decode_token
            from jwt.exceptions import InvalidTokenError
            from sqlalchemy import select
            from app.auth.models import User
            from uuid import UUID

            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                token_type = payload.get("type")
                if user_id and token_type == "access":
                    result = await db.execute(
                        select(User).where(User.id == UUID(user_id))
                    )
                    user = result.scalar_one_or_none()
                    if user is not None:
                        return user, AuthSource.LOCAL
            except (InvalidTokenError, ValueError):
                pass
            except Exception:
                pass

            # Path 2: Rails JWT fallback
            from app.auth.dependencies import _resolve_rails_jwt_user
            user = await _resolve_rails_jwt_user(token, db)
            if user is not None:
                return user, AuthSource.RAILS

        except Exception as exc:
            logger.warning("[AuthProvider] _get_user_from_token error: %s", exc)

        return None, None


# ── Singleton e FastAPI dependency ────────────────────────────────────────────

_auth_provider: "AuthProvider | None" = None


def get_auth_provider() -> AuthProvider:
    global _auth_provider
    if _auth_provider is None:
        _auth_provider = AuthProvider()
    return _auth_provider


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: "AsyncSession" = Depends(lambda: None),
) -> "AuthContext":
    """
    FastAPI dependency que retorna AuthContext.

    Uso em endpoints:
        @router.get("/")
        async def my_endpoint(auth: AuthContext = Depends(get_auth_context)):
            current_user = auth.user
            company_id = auth.company_id

    Retrocompat: auth.user é o mesmo User model de get_current_active_user.

    Nota: use get_auth_context_dependency() para injetar db correto.
    """
    provider = get_auth_provider()
    return await provider.resolve(credentials.credentials, db)


def get_auth_context_dependency():
    """
    Retorna o dependency get_auth_context configurado com db correto.
    Para uso em sub-apps que precisam de db próprio.

    Exemplo:
        from app.shared.auth.auth_provider import get_auth_context_dependency, AuthContext

        auth_dep = get_auth_context_dependency()

        @router.get("/me")
        async def me(auth: AuthContext = Depends(auth_dep)):
            return {"user_id": auth.user.id, "company_id": auth.company_id}
    """
    from app.core.database import get_db

    async def _dep(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: "AsyncSession" = Depends(get_db),
    ) -> "AuthContext":
        provider = get_auth_provider()
        return await provider.resolve(credentials.credentials, db)

    return _dep
