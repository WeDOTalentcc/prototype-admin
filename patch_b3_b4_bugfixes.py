#!/usr/bin/env python3
"""Fix GAP B3 (context_level missing in execute) + B4 (duplicate in test)."""
import os

path = "/home/runner/workspace/lia-agent-system/app/api/v1/custom_agents.py"
with open(path) as f:
    content = f.read()

# B4: Remove duplicate context_level in test
old_b4 = """            context_level=getattr(agent, "context_level", "full"),
            context_level=getattr(agent, "context_level", "full"),"""
new_b4 = """            context_level=getattr(agent, "context_level", "full"),"""

if old_b4 in content:
    content = content.replace(old_b4, new_b4, 1)
    print("OK B4: removed duplicate context_level in test")
else:
    print("SKIP B4: duplicate not found (may already be fixed)")

# B3: Add context_level to execute endpoint
old_b3 = """            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),
        )

        start = time.time()
        # GAP 2+3: Enrich context with tenant + user info"""
new_b3 = """            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),
            context_level=getattr(agent, "context_level", "full"),
        )

        start = time.time()
        # GAP 2+3: Enrich context with tenant + user info"""

if old_b3 in content:
    content = content.replace(old_b3, new_b3, 1)
    print("OK B3: added context_level to execute endpoint")
else:
    print("SKIP B3: pattern not found")

with open(path, "w") as f:
    f.write(content)

# Verify
import ast
ast.parse(content)
print("OK: syntax valid")
