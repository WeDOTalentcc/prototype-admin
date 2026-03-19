"""
Celery Application — configuração centralizada.

Worker: celery -A app.core.celery_app worker --loglevel=info
Beat:   celery -A app.core.celery_app beat --loglevel=info

Filas com prioridade (escada de custo André):
  sourcing_high     (priority=8) — busca de candidatos, triagem (SLA curto)
  evaluation_normal (priority=5) — avaliações WSI, scoring
  vagas_normal      (priority=5) — operações de vaga (criação, atualização)
  onboarding_low    (priority=3) — comunicações, reports, onboarding
"""
from celery import Celery, signals
from celery.schedules import crontab
from kombu import Queue, Exchange
from lia_config.config import settings


@signals.worker_process_init.connect
def _install_pii_masking_on_worker(**kwargs):
    """Instala PIIMaskingFilter em cada processo filho do worker Celery.

    O modelo prefork do Celery cria novos processos que NÃO herdam filtros
    de log instalados no processo pai (main.py). Esta função garante que
    o filtro seja instalado em cada worker child para conformidade LGPD.
    """
    try:
        from app.shared.pii_masking import install_global_pii_masking
        install_global_pii_masking()
    except Exception:
        pass  # Nunca bloquear inicialização do worker por causa do PII filter

_default_exchange = Exchange("lia_tasks", type="direct")

celery_app = Celery(
    "lia_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.jobs.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,  # resultados expiram em 1 hora

    # Filas com prioridade
    task_queues=(
        Queue("sourcing_high",     _default_exchange, routing_key="sourcing_high",     queue_arguments={"x-max-priority": 10}),
        Queue("evaluation_normal", _default_exchange, routing_key="evaluation_normal", queue_arguments={"x-max-priority": 10}),
        Queue("vagas_normal",      _default_exchange, routing_key="vagas_normal",      queue_arguments={"x-max-priority": 10}),
        Queue("onboarding_low",    _default_exchange, routing_key="onboarding_low",    queue_arguments={"x-max-priority": 10}),
        Queue("celery",            _default_exchange, routing_key="celery"),  # fila padrão
    ),
    task_default_queue="celery",
    task_default_exchange="lia_tasks",
    task_default_routing_key="celery",

    # Roteamento de tasks por domínio
    task_routes={
        # Sourcing — alta prioridade
        "agents.sourcing.*":             {"queue": "sourcing_high",     "priority": 8},
        # Avaliação / triagem / WSI
        "agents.wsi_interview.*":        {"queue": "evaluation_normal", "priority": 5},
        "agents.triagem.*":              {"queue": "evaluation_normal", "priority": 5},
        "agents.screening.*":            {"queue": "evaluation_normal", "priority": 5},
        "agents.pipeline.*":             {"queue": "evaluation_normal", "priority": 5},
        # Vagas / wizard
        "agents.wizard.*":               {"queue": "vagas_normal",      "priority": 5},
        "agents.kanban.*":               {"queue": "vagas_normal",      "priority": 4},
        "agents.automation.*":           {"queue": "vagas_normal",      "priority": 4},
        # Baixa prioridade
        "agents.policy.*":               {"queue": "onboarding_low",    "priority": 3},
        "communication.email.*":         {"queue": "onboarding_low",    "priority": 3},
        "drift.run_batch":               {"queue": "onboarding_low",    "priority": 2},
    },

    beat_schedule={
        # Drift check diário às 06h (Brasília = UTC-3 → 09h UTC)
        "drift-run-batch-daily": {
            "task": "drift.run_batch",
            "schedule": crontab(hour=9, minute=0),  # 06h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # Lifecycle policy de auditoria: 1º de cada mês às 03h (Brasília = UTC-3 → 06h UTC)
        "audit-lifecycle-monthly": {
            "task": "audit.apply_lifecycle_policy",
            "schedule": crontab(day_of_month=1, hour=6, minute=0),  # 03h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # LGPD cleanup diário às 02h Brasília (UTC-3 → 05h UTC)
        "lgpd-cleanup-daily": {
            "task": "lgpd.run_cleanup_daily",
            "schedule": crontab(hour=5, minute=0),  # 02h Brasília / UTC-3
            "options": {"expires": 7200},
        },
        # Briefing diário às 06h Brasília (UTC-3 → 09h UTC) — P3-1
        "briefing-daily": {
            "task": "briefing.send_daily",
            "schedule": crontab(hour=9, minute=0),  # 06h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # Follow-up de convites WSI não abertos — a cada hora (Gap A)
        "followup-check-hourly": {
            "task": "followup.process_pending",
            "schedule": crontab(minute=0),  # todo início de hora
            "options": {"expires": 3500},
        },
        # Triagem WSI abandonada — a cada 4h (Gap B)
        "wsi-abandoned-check": {
            "task": "wsi.check_abandoned",
            "schedule": crontab(minute=0, hour="*/4"),  # 00h, 04h, 08h, 12h, 16h, 20h UTC
            "options": {"expires": 14000},
        },
        # ACH-027 — Avaliação RAGAS diária às 03h UTC (00h Brasília)
        "ragas-evaluate-daily": {
            "task": "ragas.evaluate_batch",
            "schedule": crontab(hour=3, minute=0),  # 00h Brasília / UTC-3
            "options": {"expires": 7200},
        },
        # E9 — Adaptive Routing: recompute ajustes de confiança diariamente às 07h UTC (04h Brasília)
        "routing-recompute-daily": {
            "task": "routing.recompute_adjustments",
            "schedule": crontab(hour=7, minute=0),
            "args": ["global"],
            "options": {"expires": 3600},
        },
        # E4 — Hot-Reload de Agentes: verificar agents_registry.yaml a cada minuto
        "agent-registry-hot-reload": {
            "task": "agents.registry.check_reload",
            "schedule": crontab(minute="*/1"),
            "options": {"expires": 55},  # expira antes do próximo tick para evitar sobreposição
        },
        # E6 — RAG rebuild: reconstrução diária de índices de domínio às 04h UTC (01h Brasília)
        "rag-rebuild-domain-index-daily": {
            "task": "rag.rebuild_all_domains",
            "schedule": crontab(hour=4, minute=0),
            "options": {"expires": 7200},
        },
        # D6 — ML Feedback: recompute pesos adaptativos semanal (domingo 02h UTC / 23h Brasília)
        "ml-feedback-recompute-weekly": {
            "task": "ml.feedback.recompute_active_jobs",
            "schedule": crontab(hour=2, minute=0, day_of_week=0),  # domingo 02h UTC
            "options": {"expires": 3600},
        },
        # Z4-02 — LTM Compression: comprime episódios antigos diariamente às 03h UTC (00h Brasília)
        "memory-compress-daily": {
            "task": "memory.compress_old_episodes",
            "schedule": crontab(hour=3, minute=0),  # 00h Brasília / UTC-3
            "args": ["global"],
            "options": {"expires": 7200},
        },
    },
)
