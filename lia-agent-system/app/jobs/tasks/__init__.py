"""Celery tasks package (Fase 7)."""

from app.jobs.tasks.agents import (  # noqa: F401
    wizard_process_async_task,
    pipeline_transition_async_task,
    execute_wizard_task,
    execute_pipeline_task,
    execute_sourcing_task,
    execute_screening_task,
    execute_kanban_task,
    execute_policy_task,
    execute_automation_task,
)
from app.jobs.tasks.async_agent_tasks import (  # noqa: F401
    run_drift_batch_task,
    start_wsi_interview_task,
    run_triagem_task,
    run_sourcing_task,
)
from app.jobs.tasks.communication import (  # noqa: F401
    send_bulk_email_task,
    send_daily_briefing_task,
    send_weekly_digest_task,
    process_queued_messages_task,
)
from app.jobs.tasks.briefing_dispatch import (  # noqa: F401
    dispatch_daily_briefings,
    dispatch_weekly_briefings,
    dispatch_monthly_briefings,
)
from app.jobs.tasks.compliance import (  # noqa: F401
    apply_audit_lifecycle_policy,
    run_lgpd_cleanup_task,
    conversation_ttl_cleanup_task,
    pii_backfill_encrypt_existing_task,
    pii_backfill_encrypt_interview_offer_existing_task,
    run_retention_cleanup,
    cleanup_expired_working_memory,
)
from app.jobs.tasks.feedback import (  # noqa: F401
    feedback_generate_and_send_task,
    feedback_auto_send_task,
    feedback_process_pending_sends_task,
)
from app.jobs.tasks.followup import (  # noqa: F401
    followup_process_pending_task,
    wsi_check_abandoned_task,
)
from app.jobs.tasks.memory import (  # noqa: F401
    compress_old_episodes_task,
)
from app.jobs.tasks.ml import (  # noqa: F401
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
)
from app.jobs.tasks.proactive import (  # noqa: F401  # WT-2022
    proactive_detect_hints_hourly,
)

from app.jobs.tasks.voice import (  # noqa: F401
    run_openmic_wsi_pipeline_task,
)
from app.jobs.tasks.voice_retention import (  # noqa: F401  # F-05 P0 LGPD Art. 16
    voice_retention_purge_daily_task,
)

from app.jobs.tasks.health import (  # noqa: F401
    check_dlq_health_task,
)

# Sprint 7C Part 1 v2: pool_agents cron infra canonical (dispatch stub + scan REAL)
from app.jobs.tasks.pool_agents import (  # noqa: F401
    dispatch_pool_agent_assignment_task,
    scan_pool_agent_cron_schedules,
)

# Fase 2.5 Onda C1-core: motor de execução unificado (agent_deployments)
from app.jobs.tasks.agent_deployments import (  # noqa: F401
    dispatch_agent_deployment_task,
    scan_agent_deployment_cron_schedules,
)

__all__ = [
    # agents
    "wizard_process_async_task",
    "pipeline_transition_async_task",
    "execute_wizard_task",
    "execute_pipeline_task",
    "execute_sourcing_task",
    "execute_screening_task",
    "execute_kanban_task",
    "execute_policy_task",
    "execute_automation_task",
    # async_agent_tasks
    "run_drift_batch_task",
    "start_wsi_interview_task",
    "run_triagem_task",
    "run_sourcing_task",
    # communication
    "send_bulk_email_task",
    "send_daily_briefing_task",
    "send_weekly_digest_task",
    "process_queued_messages_task",
    # briefing dispatch (frequency-respecting — Wave 3 Camada 3 Item 2)
    "dispatch_daily_briefings",
    "dispatch_weekly_briefings",
    "dispatch_monthly_briefings",
    # compliance
    "apply_audit_lifecycle_policy",
    "run_lgpd_cleanup_task",
    "conversation_ttl_cleanup_task",
    "pii_backfill_encrypt_existing_task",
    "pii_backfill_encrypt_interview_offer_existing_task",
    "run_retention_cleanup",
    "cleanup_expired_working_memory",
    # feedback
    "feedback_generate_and_send_task",
    "feedback_auto_send_task",
    "feedback_process_pending_sends_task",
    # followup
    "followup_process_pending_task",
    "wsi_check_abandoned_task",
    # proactive (WT-2022)
    "proactive_detect_hints_hourly",
    # memory
    "compress_old_episodes_task",
    # ml
    "run_ragas_evaluate_batch",
    "rebuild_domain_index_task",
    "recompute_routing_adjustments",
    "process_ml_feedback_weights_task",
    "run_golden_drift_check",
    "aggregate_global_insights",
    "evolve_few_shots",
    "check_agent_registry_reload",
    "rebuild_all_domains_task",
    "recompute_active_ml_jobs_task",
    # voice
    "run_openmic_wsi_pipeline_task",
    # health (R-024)
    "check_dlq_health_task",
    # pool_agents (Sprint 7C Part 1 v2)
    "dispatch_pool_agent_assignment_task",
    "scan_pool_agent_cron_schedules",
    # agent_deployments (Fase 2.5 Onda C1-core — motor unificado)
    "dispatch_agent_deployment_task",
    "scan_agent_deployment_cron_schedules",
]

from app.jobs.tasks.expurgo_gravacoes import (  # noqa: F401  # Phase 3b LGPD Art. 16
    expurgo_gravacoes_audio,
)
