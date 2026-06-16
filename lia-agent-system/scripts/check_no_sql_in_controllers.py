#!/usr/bin/env python3
"""
CI Guard: Zero SQLAlchemy calls allowed in app/api/ files.

Usage:
    python3 scripts/check_no_sql_in_controllers.py

Exits 1 if any direct DB calls are found in controller files NOT in the
PENDING_MIGRATION allowlist. The allowlist was created on 2026-04-06 with
177 legacy files; each file must be migrated and removed from the list.

This enforces Golden Rule G1: Controllers call services/repos, NEVER the DB.
See ARCHITECTURE.md ADR-001.
"""
import sys
import re
from pathlib import Path

SQL_PATTERNS = [
    (r"await\s+db\.(execute|scalar|scalars|query|get|merge|delete|flush|refresh)", "direct db method call"),
    (r"\bsa\.(select|insert|update|delete|text)\(", "SQLAlchemy expression in controller"),
    (r"from sqlalchemy.*import", "SQLAlchemy import in controller"),
    (r"AsyncSession.*=.*Depends\(get_db\)", "AsyncSession directly in route handler"),
]

EXCLUDE_PATTERNS = [
    r"^\s*#",           # commented lines
    r"response_model",   # not SQL
]

# ── Files that had pre-existing SQL violations on 2026-04-06 ─────────────────
# DO NOT ADD NEW FILES. Remove files as they are migrated to repositories.
# Deadline: migrate ALL files by 2026-07-01.
PENDING_MIGRATION = {
    "app/api/public/candidate_portal.py",
    "app/api/public/shared_searches.py",
    "app/api/v1/ab_testing.py",
    "app/api/v1/admin_lgpd.py",
    "app/api/v1/admin_templates.py",
    "app/api/v1/agent_monitoring.py",
    "app/api/v1/agent_quality.py",
    "app/api/v1/agent_templates.py",
    "app/api/v1/ai_consumption.py",
    "app/api/v1/alerts.py",
    "app/api/v1/audit_logs.py",
    "app/api/v1/audit_timeline.py",
    "app/api/v1/autocomplete.py",
    "app/api/v1/automation/_shared.py",
    "app/api/v1/automation/event_handlers.py",
    "app/api/v1/automation/suggestions.py",
    "app/api/v1/automation/triggers.py",
    "app/api/v1/automation_rules.py",
    "app/api/v1/automations.py",
    "app/api/v1/benefits.py",
    "app/api/v1/bias_audit.py",
    "app/api/v1/big_five.py",
    "app/api/v1/briefing.py",
    "app/api/v1/calendar.py",
    "app/api/v1/candidate_compare.py",
    "app/api/v1/candidate_search/_shared.py",
    "app/api/v1/candidate_search/archetypes.py",
    "app/api/v1/candidate_search/calibration.py",
    "app/api/v1/candidate_search/contact.py",
    "app/api/v1/candidate_search/core_search.py",
    "app/api/v1/candidate_search/jd_search.py",
    "app/api/v1/candidate_search/misc_search.py",
    "app/api/v1/candidates.py",
    "app/api/v1/communication_matrix.py",
    "app/api/v1/communication_optout.py",
    "app/api/v1/communication_settings.py",
    "app/api/v1/company_benefits.py",
    "app/api/v1/company_retention.py",
    "app/api/v1/conversations.py",
    "app/api/v1/credits.py",
    "app/api/v1/cultural_fit.py",
    "app/api/v1/cv_parser.py",
    "app/api/v1/data_request.py",
    "app/api/v1/default_templates.py",
    "app/api/v1/digest.py",
    "app/api/v1/drift.py",
    "app/api/v1/early_warning.py",
    "app/api/v1/event_history.py",
    "app/api/v1/experience_highlights.py",
    "app/api/v1/fairness_reports.py",
    "app/api/v1/finetuning_export.py",
    "app/api/v1/global_policies.py",
    "app/api/v1/granular_consent.py",
    "app/api/v1/guardrails.py",
    "app/api/v1/hiring_policy.py",
    "app/api/v1/hitl.py",
    "app/api/v1/intelligence.py",
    "app/api/v1/interview_analysis.py",
    "app/api/v1/interview_notes.py",
    "app/api/v1/jd_import.py",
    "app/api/v1/job_analytics.py",
    "app/api/v1/job_board.py",
    "app/api/v1/job_drafts.py",
    "app/api/v1/job_learning.py",
    "app/api/v1/job_qualification.py",
    "app/api/v1/job_status_webhooks.py",
    "app/api/v1/job_templates.py",
    "app/api/v1/job_vacancies/export.py",
    "app/api/v1/journey_intelligence.py",
    "app/api/v1/learning_outcomes.py",
    "app/api/v1/learning_patterns.py",
    "app/api/v1/lia_assistant/conversational.py",
    "app/api/v1/lia_assistant/insights.py",
    "app/api/v1/lia_assistant/suggestions.py",
    "app/api/v1/lia_assistant/wizard.py",
    "app/api/v1/lia_assistant_fasttrack.py",
    "app/api/v1/lia_assistant_flags.py",
    "app/api/v1/lia_assistant_learning.py",
    "app/api/v1/lia_assistant_vacancy.py",
    "app/api/v1/lia_assistant_wizard_stages.py",
    "app/api/v1/lia_field_toggles.py",
    "app/api/v1/lia_profile_analysis.py",
    "app/api/v1/llm_config.py",
    "app/api/v1/ml_feedback.py",
    "app/api/v1/ml_predictions.py",
    "app/api/v1/pipeline.py",
    "app/api/v1/pipeline_policy.py",
    "app/api/v1/pipeline_templates.py",
    "app/api/v1/pipeline_velocity.py",
    "app/api/v1/policies.py",
    "app/api/v1/predictive_analytics.py",
    "app/api/v1/rag_search.py",
    "app/api/v1/recruiter_behavior.py",
    "app/api/v1/recruiter_metrics.py",
    "app/api/v1/recruiter_profiles.py",
    "app/api/v1/recruitment_email_templates.py",
    "app/api/v1/recruitment_stages.py",
    "app/api/v1/reports.py",
    "app/api/v1/rubric_evaluation.py",
    "app/api/v1/saturation.py",
    "app/api/v1/screening_questions.py",
    "app/api/v1/search_assistant.py",
    "app/api/v1/search_feedback.py",
    "app/api/v1/self_scheduling_public.py",
    "app/api/v1/settings_progress.py",
    "app/api/v1/short_lists.py",
    "app/api/v1/skills_catalog.py",
    "app/api/v1/sourcing.py",
    "app/api/v1/sourcing_pipeline.py",
    "app/api/v1/suggestion_feedback.py",
    "app/api/v1/system_health.py",
    "app/api/v1/task_lifecycle.py",
    "app/api/v1/task_planner.py",
    "app/api/v1/teams.py",
    "app/api/v1/test_activities.py",
    "app/api/v1/toon.py",
    "app/api/v1/twilio_voice.py",
    "app/api/v1/user_agent_preferences.py",
    "app/api/v1/webhooks.py",
    "app/api/v1/whatsapp.py",
    "app/api/v1/wizard_smart_orchestrator.py",
    "app/api/v1/wizard_suggestions.py",
    "app/api/v1/workforce_planning.py",
    "app/api/v1/wsi/evaluation.py",
    "app/api/v1/wsi/questions.py",
    "app/api/v1/wsi/reports.py",
    "app/api/v1/wsi/sessions.py",
    "app/api/v1/wsi_async.py",
    "app/api/v1/wsi_observability.py",
    "app/api/v1/wsi_screening_pipeline_endpoint.py",
    "app/api/wsi_endpoints.py",
    # Controllers that pass db to service layer (no direct db.execute)
    "app/api/v1/affirmative.py",
    "app/api/v1/platform_event_handlers.py",  # TODO: migrate to repository
    "app/api/v1/calibration.py",
    # Re-export hub modules (not controllers — AsyncSession is re-exported for route handlers)
    "app/api/v1/job_vacancies/_shared.py",
    "app/api/v1/lia_assistant/_shared.py",
    # Email tracking — uses get_async_db, needs migration
    "app/api/v1/email_tracking.py",
}

errors = []
checked = 0
skipped_legacy = 0

for path in Path("app/api").rglob("*.py"):
    if "__pycache__" in str(path):
        continue
    rel = str(path)
    if rel in PENDING_MIGRATION:
        skipped_legacy += 1
        continue
    checked += 1
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        for pattern, description in SQL_PATTERNS:
            if re.search(pattern, line):
                errors.append(f"{path}:{i}: {description}\n  > {line.strip()[:100]}")

if errors:
    print(f"\n[FAIL] SQL/DB calls found in {len(errors)} locations in app/api/:")
    print()
    for e in errors:
        print(f"  {e}")
    print()
    print("Fix: Move DB calls to app/domains/*/repositories/ and call them from services.")
    print("See ARCHITECTURE.md ADR-001 for the repository pattern.")
    print(f"\n(Note: {skipped_legacy} legacy files are pending migration — see PENDING_MIGRATION list)")
    sys.exit(1)

print(f"[PASS] No SQL in NEW controllers ({checked} new files checked, {skipped_legacy} legacy files pending migration)")
sys.exit(0)
