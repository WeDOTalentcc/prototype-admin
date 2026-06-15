import asyncio
"""
Celery Task Definitions — facade (Fase 7 split)

All tasks moved to app/jobs/tasks/*.py
Import paths unchanged: from app.jobs.celery_tasks import <task_name>
"""
# Re-export celery_app so tests can import from app.jobs.celery_tasks
from lia_config.celery_app import celery_app  # noqa: F401
# Re-export private async runner for unit testing of retention logic
from app.jobs.tasks.compliance import _run_retention_cleanup_async  # noqa: F401

from app.jobs.tasks import (  # noqa: F401
    wizard_process_async_task,
    pipeline_transition_async_task,
    execute_wizard_task,
    execute_pipeline_task,
    execute_sourcing_task,
    execute_screening_task,
    execute_kanban_task,
    execute_policy_task,
    execute_automation_task,
    run_drift_batch_task,
    start_wsi_interview_task,
    run_triagem_task,
    run_sourcing_task,
    send_bulk_email_task,
    send_daily_briefing_task,
    send_weekly_digest_task,
    process_queued_messages_task,
    apply_audit_lifecycle_policy,
    run_lgpd_cleanup_task,
    conversation_ttl_cleanup_task,
    pii_backfill_encrypt_existing_task,
    run_retention_cleanup,
    cleanup_expired_working_memory,
    feedback_generate_and_send_task,
    feedback_auto_send_task,
    feedback_process_pending_sends_task,
    followup_process_pending_task,
    proactive_detect_hints_hourly,  # WT-2022
    wsi_check_abandoned_task,
    compress_old_episodes_task,  # celery task name: memory.compress_old_episodes
    run_ragas_evaluate_batch,
    rebuild_domain_index_task,
    recompute_routing_adjustments,
    process_ml_feedback_weights_task,
    run_golden_drift_check,
    aggregate_global_insights,
    evolve_few_shots,
    check_agent_registry_reload,
    rebuild_all_domains_task,
    recompute_active_ml_jobs_task,
    run_openmic_wsi_pipeline_task,
    check_dlq_health_task,
    expurgo_gravacoes_audio,
)
