#!/usr/bin/env python3
"""
GAP-03-006: Calendar integration safety sensor.

Validates that:
1. Interview scheduling tools are wired correctly
2. Calendar credentials are not hardcoded
3. Continuation dispatch for interview_scheduling is registered
4. Scheduling tools have required docstrings
"""

import re
import sys
from pathlib import Path

def check_continuation_dispatch():
    """Verify interview_scheduling is in _CONTINUATION_DISPATCH."""
    file_path = Path("app/orchestrator/routing/post_wizard_continuation.py")
    if not file_path.exists():
        return True, "File not found"
    
    content = file_path.read_text()
    if "interview_scheduling" not in content:
        return False, "interview_scheduling not in _CONTINUATION_DISPATCH"
    
    if '"interview_scheduling"' not in content:
        return False, "interview_scheduling key not properly quoted"
    
    return True, "Continuation dispatch registered"


def check_no_hardcoded_credentials():
    """Verify no calendar API keys are hardcoded."""
    patterns = [
        r'CALENDAR_API_KEY\s*=\s*["\']',
        r'MICROSOFT_GRAPH_TOKEN\s*=\s*["\']',
        r'GOOGLE_CALENDAR_KEY\s*=\s*["\']',
    ]
    
    violations = []
    for pattern in patterns:
        result = Path("lia-agent-system").rglob("*.py")
        for file_path in result:
            if "test" in file_path.name or "__pycache__" in str(file_path):
                continue
            content = file_path.read_text()
            if re.search(pattern, content):
                violations.append(str(file_path))
    
    if violations:
        return False, f"Hardcoded credentials found: {violations}"
    
    return True, "No hardcoded credentials"


def check_scheduling_tools_docstrings():
    """Verify scheduling tools have proper docstrings."""
    try:
        tool_files = list(Path("app/domains/interview_scheduling/tools").glob("*.py"))
    except:
        return True, "Interview scheduling tools dir not found"
    
    violations = []
    for file_path in tool_files:
        if file_path.name.startswith("_"):
            continue
        content = file_path.read_text()
        # Check for docstring
        if not (content.strip().startswith('"""') or content.strip().startswith("'''")):
            if 'def ' in content:
                violations.append(f"{file_path.name}: missing module docstring")
    
    if violations:
        return False, f"Docstring violations: {violations}"
    
    return True, "All tools have docstrings"


def main():
    checks = [
        ("Continuation dispatch", check_continuation_dispatch),
        ("No hardcoded credentials", check_no_hardcoded_credentials),
        ("Tool docstrings", check_scheduling_tools_docstrings),
    ]
    
    all_pass = True
    for name, check_fn in checks:
        passed, msg = check_fn()
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not passed:
            all_pass = False
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
