#!/usr/bin/env python3
"""Sensor: _is_plan_service_enabled() must be called in main_orchestrator."""
import re
import sys

TARGET = "app/orchestrator/main_orchestrator.py"

with open(TARGET) as f:
    content = f.read()

defined = bool(re.search(r"^def _is_plan_service_enabled\(\)", content, re.MULTILINE))
called = bool(re.search(r"if _is_plan_service_enabled\(\):", content))

errors = []
if not defined:
    errors.append(f"_is_plan_service_enabled() not defined in {TARGET}")
if not called:
    errors.append(f"_is_plan_service_enabled() defined but NEVER CALLED in {TARGET}")

with open("app/shared/execution/plan_detector.py") as f:
    detector_src = f.read()
pattern_count = len(re.findall("PlanPattern.", detector_src))
if pattern_count < 14:
    errors.append(f"Expected >= 14 PlanPatterns, found {pattern_count}")

with open("app/shared/execution/plan_templates.py") as f:
    tmpl_src = f.read()
tmpl_count = tmpl_src.count("task_id")
if tmpl_count < 40:
    errors.append(f"Expected >= 40 task_id entries (proxy for 14 templates), found {tmpl_count}")

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)

print(f"OK: _is_plan_service_enabled() wired in {TARGET}")
print(f"OK: {pattern_count} PlanPatterns")
print(f"OK: templates verified ({tmpl_count} task_id entries)")
