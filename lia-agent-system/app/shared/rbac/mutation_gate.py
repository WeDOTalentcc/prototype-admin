"""Sprint 7 RBAC — mutation gate (write protection canonical).

Plan: ~/.claude/plans/jolly-roaming-moler.md.

Complements Sprint 6 read filter (fail-open). Mutation gate is FAIL-SECURE:
when scope cannot be computed (DB down, missing fields), default is BLOCK 403.

Read filter hides UI; mutation gate protects data integrity.
Both layers needed for canonical RBAC enforcement.

Pattern:
    from app.shared.rbac.mutation_gate import assert_mutation_allowed
    # In PUT/PATCH/DELETE endpoint, AFTER fetching resource:
    await assert_mutation_allowed(resource, current_user)
    # Continue with mutation logic if no exception raised.
"""
from __future__ import annotations

from fastapi import HTTPException, status

from app.shared.rbac.visible_scope import compute_visible_scope


async def assert_mutation_allowed(
    resource,
    current_user,
    *,
    owner_email_attrs: tuple[str, ...] = ("created_by", "recruiter_email"),
    dept_attr: str = "department_id",
    assignee_id_attrs: tuple[str, ...] = ("assigned_to_user_id",),
    interviewer_email_attr: str = "interviewer_email",
    resource_label: str = "resource",
) -> None:
    """Raise HTTP 403 if current_user cannot mutate `resource`.

    Sprint 7 RBAC fail-secure mutation gate.

    Logic (in order of evaluation):
      1. Admin / wedotalent_admin → bypass
      2. Legacy user (no dept + no subordinates) → bypass (soft-launch compat)
      3. Resource owned by self (created_by/recruiter_email == user.email)
         OR resource assignee == self.id
         OR resource interviewer_email == self.email → allowed
      4. Resource in visible dept set (own + subordinate depts) → allowed
      5. Resource owned by subordinate
         (created_by/recruiter_email/interviewer_email in subordinate_emails
          OR assignee in subordinate_user_ids) → allowed (manager scope)
      6. Else → raise HTTP 403

    Fail-secure: if compute_visible_scope raises, default is BLOCK (raise 503).
    Mutation cannot proceed when scope is uncertain.

    Args:
        resource: ORM instance or dict with fields below
        current_user: ORM User
        owner_email_attrs: attrs holding owner email (varies by entity)
        dept_attr: attr holding department_id (FK)
        assignee_id_attrs: attrs holding assignee user_id (for tasks)
        interviewer_email_attr: attr for interview interviewer (for interviews)
        resource_label: human label for 403 message

    Raises:
        HTTPException(403): out of visible scope
        HTTPException(503): scope computation failed (fail-secure)
    """
    if resource is None:
        return  # nothing to gate

    try:
        scope = await compute_visible_scope(current_user)
    except Exception as exc:  # noqa: BLE001
        # Fail-secure: cannot determine scope → block mutation
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot verify permissions to mutate {resource_label}; retry shortly",
        ) from exc

    # Rule 1: admin bypass
    if scope.is_admin:
        return

    # Rule 2: legacy soft-launch bypass (compat with Sprint 2 Phase 1)
    if scope.own_dept_id is None and not scope.has_subordinates:
        return

    def _get(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    # Rule 3a: owner is self (any of the email attrs match)
    user_email = (scope.user_email or "").lower()
    if user_email:
        for attr in owner_email_attrs:
            raw = _get(resource, attr)
            if raw and str(raw).lower() == user_email:
                return

    # Rule 3b: interview interviewer is self
    iv = _get(resource, interviewer_email_attr)
    if iv and user_email and str(iv).lower() == user_email:
        return

    # Rule 3c: task assignee is self
    for attr in assignee_id_attrs:
        raw = _get(resource, attr)
        if raw and scope.user_id and str(raw) == str(scope.user_id):
            return

    # Rule 4: dept in visible scope
    res_dept = _get(resource, dept_attr)
    if res_dept and str(res_dept) in scope.visible_dept_ids:
        return

    # Rule 5a: owner email is a direct subordinate
    if scope.subordinate_user_emails:
        for attr in owner_email_attrs:
            raw = _get(resource, attr)
            if raw and str(raw).lower() in scope.subordinate_user_emails:
                return
        # Interviewer subordinate
        if iv and str(iv).lower() in scope.subordinate_user_emails:
            return

    # Rule 5b: assignee is direct subordinate (tasks)
    if scope.subordinate_user_ids:
        for attr in assignee_id_attrs:
            raw = _get(resource, attr)
            if raw and str(raw) in scope.subordinate_user_ids:
                return

    # Rule 6: none of the above → 403
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Permission denied: {resource_label} is outside your visible scope",
    )
