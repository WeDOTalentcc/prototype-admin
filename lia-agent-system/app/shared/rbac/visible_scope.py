"""Sprint 6 RBAC — canonical visible scope helper (1-level manager hierarchy).

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md.

Computes the visible scope for a user once, returns immutable dataclass
consumed by all entity filters (vagas, candidatos, interviews, tasks).

Hierarchy: 1-level direct manager (no cascade). Decision Paulo 2026-05-25.
Manager sees:
  - own department (Sprint 2 Phase 1 dept_id rule)
  - data of direct subordinates (users WHERE manager_id == self.id)
    Subordinates may live in DIFFERENT departments (cross-dept manager)

Strict enforcement: filter always applies based on (role, dept_id, manager_id).
NULL manager_id means user has no subordinates (not bypass).
NULL dept_id remains soft-launch bypass (Sprint 2 Phase 1 canonical).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from app.core.database import AsyncSessionLocal


@dataclass(frozen=True)
class VisibleScope:
    """Resolved scope for a user — what they can see across entities."""

    # Own user info
    user_id: str | None
    user_email: str | None
    own_dept_id: str | None
    is_admin: bool
    role: str | None

    # Direct subordinates (1-level): users WHERE manager_id == user.id
    subordinate_user_ids: frozenset[str] = field(default_factory=frozenset)
    subordinate_user_emails: frozenset[str] = field(default_factory=frozenset)
    subordinate_dept_ids: frozenset[str] = field(default_factory=frozenset)

    @property
    def has_subordinates(self) -> bool:
        return bool(self.subordinate_user_ids)

    @property
    def visible_dept_ids(self) -> frozenset[str]:
        """Union of own dept + subordinate depts. Used by entity-level filters."""
        out: set[str] = set()
        if self.own_dept_id:
            out.add(str(self.own_dept_id))
        out.update(self.subordinate_dept_ids)
        return frozenset(out)

    @property
    def visible_user_ids(self) -> frozenset[str]:
        """Union of self + subordinates. Used for ownership checks."""
        out: set[str] = set(self.subordinate_user_ids)
        if self.user_id:
            out.add(str(self.user_id))
        return frozenset(out)


async def compute_visible_scope(current_user) -> VisibleScope:
    """Compute visible scope for current_user. Cached per-request would be ideal
    but for soft-launch posture this is called few times per request.

    Args:
        current_user: ORM User (or any object with id/email/role/department_id attrs)

    Returns:
        VisibleScope dataclass (frozen) — safe to share across filters.
    """
    if current_user is None:
        return VisibleScope(user_id=None, user_email=None, own_dept_id=None,
                            is_admin=False, role=None)

    from app.auth.models import UserRole
    user_id = str(getattr(current_user, "id", "") or "") or None
    user_email = (getattr(current_user, "email", "") or "").lower() or None
    own_dept_id = getattr(current_user, "department_id", None)
    own_dept_str = str(own_dept_id) if own_dept_id else None

    role_attr = getattr(current_user, "role", None)
    role_str = role_attr.value if hasattr(role_attr, "value") else (str(role_attr) if role_attr else None)
    is_admin = role_str in (UserRole.admin.value, UserRole.wedotalent_admin.value)

    # Only managers + admins gain hierarchy view. Recruiters/viewers see own dept only.
    subord_ids: set[str] = set()
    subord_emails: set[str] = set()
    subord_depts: set[str] = set()
    if user_id and role_str in (UserRole.manager.value, UserRole.admin.value, UserRole.wedotalent_admin.value):
        try:
            async with AsyncSessionLocal() as db:
                rs = await db.execute(
                    text(
                        "SELECT id::text AS uid, email, department_id::text AS dept "
                        "FROM users WHERE manager_id = :mid AND is_active = true"
                    ),
                    {"mid": user_id},
                )
                for row in rs.fetchall():
                    subord_ids.add(row.uid)
                    if row.email:
                        subord_emails.add(row.email.lower())
                    if row.dept:
                        subord_depts.add(row.dept)
        except Exception:
            # Non-blocking — if lookup fails, fall back to no-subordinate view
            pass

    return VisibleScope(
        user_id=user_id,
        user_email=user_email,
        own_dept_id=own_dept_str,
        is_admin=is_admin,
        role=role_str,
        subordinate_user_ids=frozenset(subord_ids),
        subordinate_user_emails=frozenset(subord_emails),
        subordinate_dept_ids=frozenset(subord_depts),
    )
