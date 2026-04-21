#!/usr/bin/env python3
"""Fix broken V1 tool handlers on Replit — pure string replacement, no imports."""
from pathlib import Path

BASE = Path("/home/runner/workspace/lia-agent-system/app/domains")

# ── 1. ATS INTEGRATION: all 10 use .ats_sync_service.ats_sync_service.* (singleton) ──
ats_file = BASE / "ats_integration/tools/__init__.py"
ats_content = ats_file.read_text()
# Replace the list with an empty one
import re
ats_content = re.sub(
    r'ATS_INTEGRATION_TOOLS\s*=\s*\[.*?\]',
    'ATS_INTEGRATION_TOOLS = [\n    # Migrated to V2 DomainAction path (actions.py).\n    # Singleton instance pattern (.ats_sync_service.ats_sync_service.*) is not\n    # resolvable via dynamic import. Routes handled by PipelineTransitionAgent.\n]',
    ats_content,
    flags=re.DOTALL
)
ats_file.write_text(ats_content)
print("✓ ats_integration/tools/__init__.py — cleared 10 broken handlers")

# ── 2. AUTOMATION: all 10 use .task_service.task_service.* (singleton) ──
auto_file = BASE / "automation/tools/__init__.py"
auto_content = auto_file.read_text()
auto_content = re.sub(
    r'AUTOMATION_TOOLS\s*=\s*\[.*?\]',
    'AUTOMATION_TOOLS = [\n    # Migrated to V2 DomainAction path (actions.py).\n    # Singleton instance pattern (.task_service.task_service.* etc.) is not\n    # resolvable via dynamic import. Routes handled via automation_tools.py.\n]',
    auto_content,
    flags=re.DOTALL
)
auto_file.write_text(auto_content)
print("✓ automation/tools/__init__.py — cleared 10 broken handlers")

# ── 3. INTERVIEW SCHEDULING: all 10 use .scheduling_service.scheduling_service.* (singleton) ──
sched_file = BASE / "interview_scheduling/tools/__init__.py"
sched_content = sched_file.read_text()
sched_content = re.sub(
    r'INTERVIEW_SCHEDULING_TOOLS\s*=\s*\[.*?\]',
    'INTERVIEW_SCHEDULING_TOOLS = [\n    # Migrated to V2 DomainAction path (actions.py).\n    # Singleton instance pattern (.scheduling_service.scheduling_service.* etc.) is not\n    # resolvable via dynamic import. Routes handled via scheduling_tools.py.\n]',
    sched_content,
    flags=re.DOTALL
)
sched_file.write_text(sched_content)
print("✓ interview_scheduling/tools/__init__.py — cleared 10 broken handlers")

# ── 4. RECRUITER ASSISTANT: all 10 use singleton pattern ──
ra_file = BASE / "recruiter_assistant/tools/__init__.py"
ra_content = ra_file.read_text()
ra_content = re.sub(
    r'RECRUITER_ASSISTANT_TOOLS\s*=\s*\[.*?\]',
    'RECRUITER_ASSISTANT_TOOLS = [\n    # Migrated to V2 DomainAction path.\n    # Singleton instance pattern not resolvable via dynamic import.\n    # Routes handled by KanbanAgent and PolicyAgent.\n]',
    ra_content,
    flags=re.DOTALL
)
ra_file.write_text(ra_content)
print("✓ recruiter_assistant/tools/__init__.py — cleared 10 broken handlers")

# ── 5. CV SCREENING: remove 2 entries that reference missing wsi_service.py ──
cv_file = BASE / "cv_screening/tools/__init__.py"
cv_content = cv_file.read_text()

# Remove calculate_wsi entry
cv_content = re.sub(
    r'\s*\{\s*\n\s*"tool_id":\s*"calculate_wsi".*?"handler":\s*"[^"]*wsi_service\.calculate_wsi"[^}]*\},?',
    '',
    cv_content,
    flags=re.DOTALL
)

# Remove generate_wsi_questions entry that points to wsi_service (not wsi_question_adjuster)
cv_content = re.sub(
    r'\s*\{\s*\n\s*"tool_id":\s*"generate_wsi_questions".*?"handler":\s*"[^"]*wsi_service\.generate_wsi_questions_tool"[^}]*\},?',
    '',
    cv_content,
    flags=re.DOTALL
)

cv_file.write_text(cv_content)
print("✓ cv_screening/tools/__init__.py — removed 2 broken wsi_service entries")

print("\nAll done. Run audit_tool_routing.py CHECK 4 to verify.")
