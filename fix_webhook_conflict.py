#!/usr/bin/env python3
"""Fix webhook table conflict: rename Python webhook -> studio_webhook."""
import os

BASE = "/home/runner/workspace/lia-agent-system"


def patch(rel, old, new, label):
    full = os.path.join(BASE, rel)
    with open(full) as f:
        content = f.read()
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# 1. Model: rename table name
patch(
    "libs/models/lia_models/webhook.py",
    '__tablename__ = "webhooks"',
    '__tablename__ = "studio_webhooks"',
    "rename model tablename",
)

# 2. Migration 074: rename table
patch(
    "alembic/versions/074_webhooks.py",
    '"webhooks",',
    '"studio_webhooks",',
    "rename in migration create_table",
)
patch(
    "alembic/versions/074_webhooks.py",
    'op.drop_table("webhooks")',
    'op.drop_table("studio_webhooks")',
    "rename in migration drop_table",
)


print("\nDone — webhook -> studio_webhook")
