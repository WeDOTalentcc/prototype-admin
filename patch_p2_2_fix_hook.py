#!/usr/bin/env python3
"""Fix PATCH hook for version snapshot."""
path = "/home/runner/workspace/lia-agent-system/app/api/v1/custom_agents.py"
with open(path) as f:
    content = f.read()

old = '''    """Update custom agent. Automatically creates a version snapshot before applying changes."""
    try:
        update_data = body.model_dump(exclude_unset=True)
        agent = await agent_marketplace_service.update_agent(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            data=update_data,
        )'''

new = '''    """Update custom agent. Automatically creates a version snapshot before applying changes."""
    # P2.2: Snapshot before update
    try:
        from app.services.agent_version_service import agent_version_service
        from sqlalchemy import select as _sel
        _existing_result = await db.execute(
            _sel(CustomAgent).where(
                CustomAgent.id == agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
        )
        _existing = _existing_result.scalar_one_or_none()
        if _existing:
            _update_data_peek = body.model_dump(exclude_unset=True)
            _changed_fields = [k for k in _update_data_peek.keys() if hasattr(_existing, k)]
            if _changed_fields:
                await agent_version_service.create_snapshot(
                    db=db,
                    agent=_existing,
                    changed_fields=_changed_fields,
                    changed_by=str(current_user.id),
                )
    except Exception as _snap_err:
        logger.warning("[AgentVersion] snapshot failed (non-blocking): %s", _snap_err)

    try:
        update_data = body.model_dump(exclude_unset=True)
        agent = await agent_marketplace_service.update_agent(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            data=update_data,
        )'''

if old in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK: PATCH hook added")
else:
    print("ERROR: pattern not found")

import ast
try:
    ast.parse(content)
    print("OK: syntax valid")
except SyntaxError as e:
    print(f"ERROR: {e}")
