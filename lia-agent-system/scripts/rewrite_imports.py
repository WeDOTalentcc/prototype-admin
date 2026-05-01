#!/usr/bin/env python3
"""
rewrite_imports.py
Substitui 'from app.services.SHIM' por 'from app.domains.X.services.SHIM'
em todos os arquivos .py, exceto os proprios shims em app/services/.
Executar de: /home/runner/workspace/lia-agent-system/
"""
import os

SHIM_MAP = {
    'agent_monitoring_service': 'app.domains.analytics.services.agent_monitoring_service',
    'apify_mcp_client': 'app.domains.sourcing.services.apify_mcp_client',
    'apify_service': 'app.domains.sourcing.services.apify_service',
    'ats_job_history_service': 'app.domains.job_management.services.ats_job_history_service',
    'ats_sync_service': 'app.domains.ats_integration.services.ats_sync_service',
    'automation_handlers': 'app.domains.automation.services.automation_handlers',
    'automation_scheduler': 'app.domains.automation.services.automation_scheduler',
    'automation_service': 'app.domains.automation.services.automation_service',
    'automation_trigger_service': 'app.domains.automation.services.automation_trigger_service',
    'autonomous_agent_service': 'app.domains.automation.services.autonomous_agent_service',
    'calendar_service': 'app.domains.interview_scheduling.services.calendar_service',
    'calibration_profiles': 'app.domains.cv_screening.services.calibration_profiles',
    'candidate_report_service': 'app.domains.analytics.services.candidate_report_service',
    'communication_dispatcher': 'app.domains.communication.services.communication_dispatcher',
    'communication_history_service': 'app.domains.communication.services.communication_history_service',
    'communication_service': 'app.domains.communication.services.communication_service',
    'conversation_manager': 'app.domains.recruiter_assistant.services.conversation_manager',
    'conversation_memory': 'app.domains.recruiter_assistant.services.conversation_memory',
    'cv_parser': 'app.domains.cv_screening.services.cv_parser',
    'cv_scoring_service': 'app.domains.cv_screening.services.cv_scoring_service',
    'data_request_service': 'app.domains.communication.services.data_request_service',
    'data_request_whatsapp_service': 'app.domains.communication.services.data_request_whatsapp_service',
    'eligibility_verification_service': 'app.domains.cv_screening.services.eligibility_verification_service',
    'email_providers': 'app.domains.communication.services.email_providers',
    'email_service': 'app.domains.communication.services.email_service',
    'evaluation_criteria_service': 'app.domains.cv_screening.services.evaluation_criteria_service',
    'gupy_service': 'app.domains.ats_integration.services.gupy_service',
    'interview_transcript_analysis_service': 'app.domains.interview_scheduling.services.interview_transcript_analysis_service',
    'jd_enrichment_service': 'app.domains.job_management.services.jd_enrichment_service',
    'jd_generator_service': 'app.domains.job_management.services.jd_generator_service',
    'jd_import_service': 'app.domains.job_management.services.jd_import_service',
    'jd_template_cache_service': 'app.domains.job_management.services.jd_template_cache_service',
    'jd_template_service': 'app.domains.job_management.services.jd_template_service',
    'job_alert_service': 'app.domains.job_management.services.job_alert_service',
    'job_analytics_prompt_service': 'app.domains.analytics.services.job_analytics_prompt_service',
    'job_audit_service': 'app.domains.job_management.services.job_audit_service',
    'job_board_service': 'app.domains.job_management.services.job_board_service',
    'job_clone_service': 'app.domains.job_management.services.job_clone_service',
    'job_context_service': 'app.domains.job_management.services.job_context_service',
    'job_embedding_service': 'app.domains.job_management.services.job_embedding_service',
    'job_insights_service': 'app.domains.analytics.services.job_insights_service',
    'job_pattern_service': 'app.domains.job_management.services.job_pattern_service',
    'job_qualification_service': 'app.domains.job_management.services.job_qualification_service',
    'job_report_service': 'app.domains.analytics.services.job_report_service',
    'job_status_webhook_service': 'app.domains.job_management.services.job_status_webhook_service',
    'job_template_service': 'app.domains.job_management.services.job_template_service',
    'job_vacancy_service': 'app.domains.job_management.services.job_vacancy_service',
    'kanban_assistant_service': 'app.domains.recruiter_assistant.services.kanban_assistant_service',
    'memory_service': 'app.domains.recruiter_assistant.services.memory_service',
    'merge_ats_service': 'app.domains.ats_integration.services.merge_ats_service',
    'pandape_service': 'app.domains.ats_integration.services.pandape_service',
    'pearch_service': 'app.domains.sourcing.services.pearch_service',
    'personalized_feedback_service': 'app.domains.cv_screening.services.personalized_feedback_service',
    'pipeline_service': 'app.domains.recruiter_assistant.services.pipeline_service',
    'pipeline_stage_service': 'app.domains.recruiter_assistant.services.pipeline_stage_service',
    'planned_task_service': 'app.domains.automation.services.planned_task_service',
    'pre_qualification_service': 'app.domains.cv_screening.services.pre_qualification_service',
    'predictive_analytics_service': 'app.domains.analytics.services.predictive_analytics_service',
    'proactive_alert_service': 'app.domains.automation.services.proactive_alert_service',
    'proactive_service': 'app.domains.automation.services.proactive_service',
    'recruitment_email_templates': 'app.domains.job_management.services.recruitment_email_templates',
    'report_service': 'app.domains.analytics.services.report_service',
    'rubric_evaluation_service': 'app.domains.cv_screening.services.rubric_evaluation_service',
    'scheduling_service': 'app.domains.interview_scheduling.services.scheduling_service',
    'score_normalization_service': 'app.domains.cv_screening.services.score_normalization_service',
    'screening_question_set_service': 'app.domains.cv_screening.services.screening_question_set_service',
    'search_analytics_service': 'app.domains.analytics.services.search_analytics_service',
    'seniority_context_calibrator': 'app.domains.cv_screening.services.seniority_context_calibrator',
    'seniority_jd_analyzer': 'app.domains.job_management.services.seniority_jd_analyzer',
    'seniority_resolver': 'app.domains.cv_screening.services.seniority_resolver',
    'seniority_utils': 'app.domains.cv_screening.services.seniority_utils',
    'stage_automation_engine': 'app.domains.automation.services.stage_automation_engine',
    'stage_transition_automation': 'app.domains.automation.services.stage_transition_automation',
    'task_service': 'app.domains.automation.services.task_service',
    'teams_auth': 'app.domains.communication.services.teams_auth',
    'teams_bot': 'app.domains.communication.services.teams_bot',
    'teams_recording_service': 'app.domains.communication.services.teams_recording_service',
    'teams_service': 'app.domains.communication.services.teams_service',
    'teams_simple': 'app.domains.communication.services.teams_simple',
    'template_importer_service': 'app.domains.job_management.services.template_importer_service',
    'template_learning_service': 'app.domains.job_management.services.template_learning_service',
    'template_seeder': 'app.domains.job_management.services.template_seeder',
    'vacancy_search_service': 'app.domains.job_management.services.vacancy_search_service',
    'webhook_service': 'app.domains.communication.services.webhook_service',
    'whatsapp_factory': 'app.domains.communication.services.whatsapp_factory',
    'whatsapp_meta_service': 'app.domains.communication.services.whatsapp_meta_service',
    'whatsapp_provider': 'app.domains.communication.services.whatsapp_provider',
    'whatsapp_service': 'app.domains.communication.services.whatsapp_service',
    'whatsapp_twilio_service': 'app.domains.communication.services.whatsapp_twilio_service',
    'wizard_analytics_service': 'app.domains.analytics.services.wizard_analytics_service',
    'wizard_data_priority_service': 'app.domains.job_management.services.wizard_data_priority_service',
    'wizard_orchestrator_service': 'app.domains.job_management.services.wizard_orchestrator_service',
    'wsi_deterministic_scorer': 'app.domains.cv_screening.services.wsi_deterministic_scorer',
    'wsi_question_adjuster': 'app.domains.cv_screening.services.wsi_question_adjuster',
    'wsi_screening_pipeline': 'app.domains.cv_screening.services.wsi_screening_pipeline',
    'wsi_service': 'app.domains.cv_screening.services.wsi_service',
    'wsi_voice_orchestrator': 'app.domains.cv_screening.services.wsi_voice_orchestrator',
}

# Build exact replacement pairs
REPLACEMENTS = {f'app.services.{k}': v for k, v in SHIM_MAP.items()}

SERVICES_DIR = os.path.normpath('./app/services')

def should_skip(path):
    norm = os.path.normpath(path)
    # Skip the shim files themselves
    if norm.startswith(SERVICES_DIR + os.sep) or norm == SERVICES_DIR:
        return True
    return False

def rewrite_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False

    original = content
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    os.chdir('/home/runner/workspace/lia-agent-system')
    changed = []
    total_files = 0

    for root, dirs, files in os.walk('.'):
        dirs[:] = [
            d for d in dirs
            if d not in {'__pycache__', '.git', 'node_modules', '.venv', '.pythonlibs'}
            and not should_skip(os.path.join(root, d))
        ]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            path = os.path.join(root, fname)
            if should_skip(path):
                continue
            total_files += 1
            if rewrite_file(path):
                changed.append(path)

    print(f'Scanned: {total_files} files')
    print(f'Rewritten: {len(changed)} files')
    print()
    for p in sorted(changed):
        print(f'  CHANGED: {p}')

if __name__ == '__main__':
    main()
