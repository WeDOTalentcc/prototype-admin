"""
Celery Application — configuração centralizada.

Worker: celery -A app.core.celery_app worker --loglevel=info
Beat:   celery -A app.core.celery_app beat --loglevel=info

Filas com prioridade (escada de custo André):
  sourcing_high     (priority=8) — busca de candidatos, triagem (SLA curto)
  evaluation_normal (priority=5) — avaliações WSI, scoring
  vagas_normal      (priority=5) — operações de vaga (criação, atualização)
  onboarding_low    (priority=3) — comunicações, reports, onboarding

Broker abstraction via BROKER_BACKEND:
  Trocar de Redis para outro broker é mudança de UMA variável de config:

    BROKER_BACKEND=redis     → Celery usa Redis (REDIS_URL) — padrão/produção on-prem
    BROKER_BACKEND=rabbitmq  → Celery usa RabbitMQ (RABBITMQ_URL) — on-prem alternativo
    BROKER_BACKEND=pubsub    → Celery usa GCP (CELERY_BROKER_URL must be set) — migração GCP

  Override manual (sobrepõe BROKER_BACKEND):
    CELERY_BROKER_URL    — URL explícita para o broker do Celery (qualquer transporte)
    CELERY_RESULT_BACKEND — URL explícita para o result backend

  Mapeamento BROKER_BACKEND → Celery URL:
    redis    → settings.REDIS_URL  (redis://)
    rabbitmq → settings.RABBITMQ_URL  (amqp://)
    pubsub   → CELERY_BROKER_URL obrigatório (gcpubsub:// ou similar)

  Migração GCP step-by-step: docs/infra/gcp-migration-guide.md
"""
import asyncio
import logging
import os
import traceback as _traceback

from celery import Celery, Task, signals
from celery.schedules import crontab
from kombu import Queue, Exchange
from lia_config.config import settings

_celery_log = logging.getLogger(__name__)


def _get_celery_broker_url() -> str:
    """Retorna broker URL para o Celery a partir de BROKER_BACKEND.

    BROKER_BACKEND é a variável única de controle — trocar o broker é
    mudar apenas ela. O mapping para URL compatível com Celery é feito aqui:

      redis    → REDIS_URL (redis://)
      rabbitmq → RABBITMQ_URL (amqp://)
      pubsub   → CELERY_BROKER_URL (gcpubsub:// ou similar — obrigatório)

    Override explícito sempre tem precedência:
      CELERY_BROKER_URL → qualquer URL válida para Celery (sobrepõe BROKER_BACKEND)
    """
    # Override explícito — qualquer URL direta (máxima precedência)
    explicit = os.getenv("CELERY_BROKER_URL") or getattr(settings, "CELERY_BROKER_URL", None)
    if explicit:
        return explicit

    # Derivar URL a partir de BROKER_BACKEND (variável única de controle).
    # Lê diretamente do env var para que mudanças de runtime sejam refletidas.
    # settings.BROKER_BACKEND é usado como fallback (lido em startup).
    backend = os.getenv("BROKER_BACKEND") or getattr(settings, "BROKER_BACKEND", "redis")
    backend = backend.lower().strip()

    if backend == "redis":
        return settings.REDIS_URL
    elif backend == "rabbitmq":
        return settings.RABBITMQ_URL
    elif backend == "pubsub":
        # GCP Pub/Sub: requer CELERY_BROKER_URL explícito com transport adequado
        # (ex: gcpubsub://projects/meu-projeto/topics/celery via celery-gcp-backend)
        _celery_log.error(
            "[celery_app] BROKER_BACKEND=pubsub requer CELERY_BROKER_URL explícito "
            "(ex: gcpubsub://projects/<project>/topics/celery). "
            "Usando REDIS_URL como fallback temporário. "
            "Ver: docs/infra/gcp-migration-guide.md"
        )
        return settings.REDIS_URL  # Fallback seguro — não quebra o worker
    else:
        _celery_log.warning(
            "[celery_app] BROKER_BACKEND='%s' desconhecido. Usando redis (REDIS_URL).", backend
        )
        return settings.REDIS_URL


def _get_celery_result_backend() -> str:
    """Retorna result backend URL para o Celery.

    Prioridade:
    1. CELERY_RESULT_BACKEND env var (override explícito)
    2. settings.CELERY_RESULT_BACKEND (via config)
    3. Derivado de BROKER_BACKEND (redis → REDIS_URL, rabbitmq → REDIS_URL)
    4. settings.REDIS_URL (fallback final)

    Nota: RabbitMQ não é adequado como result backend — Redis é usado mesmo
    quando BROKER_BACKEND=rabbitmq, pois o result backend precisa de storage.
    """
    explicit = os.getenv("CELERY_RESULT_BACKEND") or getattr(settings, "CELERY_RESULT_BACKEND", None)
    if explicit:
        return explicit
    return settings.REDIS_URL


class LIATask(Task):
    """
    Base class para todas as tasks Celery da LIA.

    Comportamento adicional vs Task padrão:
    - on_failure(): persiste na DLQ Redis quando retries se esgotam
    - Notificação Bell para tasks críticas (fail-safe)

    Uso: @celery_app.task(base=LIATask, ...)
    """

    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Chamado pelo Celery quando a task falha definitivamente (retries esgotados)."""
        queue = (self.request.delivery_info or {}).get("routing_key", "celery")

        tb_str = ""
        if einfo is not None:
            try:
                tb_str = str(einfo.traceback) if hasattr(einfo, "traceback") else ""
            except Exception:
                tb_str = _traceback.format_exc()

        try:
            from app.shared.resilience.dlq_service import dlq_service

            async def _push():
                await dlq_service.push_failure(
                    task_name=self.name,
                    queue=queue,
                    args=list(args),
                    kwargs=dict(kwargs),
                    exc=exc,
                    tb=tb_str,
                    retries=self.request.retries,
                    company_id=kwargs.get("company_id") if isinstance(kwargs, dict) else None,
                )

            # Roda em um novo event loop sem bloquear o worker
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_push())
                else:
                    loop.run_until_complete(_push())
            except RuntimeError:
                asyncio.run(_push())

        except Exception as dlq_exc:
            import logging
            logging.getLogger(__name__).debug(
                "[LIATask.on_failure] DLQ push falhou (fail-safe): %s", dlq_exc
            )


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


@signals.worker_process_init.connect
def _install_llm_guards_on_worker(**kwargs):
    """Wave 4 Gap 1 (2026-05-22): install LLM SDK monkey-patches in each
    Celery worker process so background jobs (Sidekiq-equivalent, drift,
    insights, ML recompute, WSI etc) ALSO route LLM calls through the
    ai_credit_gate. FastAPI startup wires this in main.py for the API
    process; Celery workers are a separate process tree with their own
    import graph -- if we skipped this, every LLM call from a worker
    would bypass the universal credit gate.

    install_llm_guards() is idempotent (module-level flag) and safe to
    call multiple times (re-emits llm_guards_installed gauge to refresh
    Prometheus timeseries on forked workers).
    """
    try:
        from app.shared.llm_bootstrap import install_llm_guards
        install_llm_guards(entrypoint='celery')
    except Exception as exc:  # noqa: BLE001
        # Nunca bloquear inicialização do worker. Mas LOG ALTO porque
        # se isso falhar, o worker roda SEM o gate de créditos (bypass).
        _celery_log.error(
            "[celery_app] install_llm_guards FAILED on worker init: %s -- LLM gate bypassed in this worker process",
            exc,
            exc_info=True,
        )

_default_exchange = Exchange("lia_tasks", type="direct")

celery_app = Celery(
    "lia_tasks",
    broker=_get_celery_broker_url(),
    backend=_get_celery_result_backend(),
    include=["app.jobs.celery_tasks"],
    task_cls=LIATask,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,  # resultados expiram em 1 hora

    # R-049: Prefetch tuning
    # sourcing_high (long LLM tasks): prefetch=1 to prevent queue starvation
    # evaluation_normal (RAGAS batch): prefetch=1
    # vagas_normal (job updates): prefetch=1
    # onboarding_low (background tasks): prefetch=10 (fast, short)
    # worker_prefetch_multiplier=1 is safe default for LLM workloads
    # Note: Celery does not support per-queue prefetch; the global value is
    # intentionally set to 1 (conservative) to avoid long LLM tasks blocking
    # short ones on the same worker. For onboarding_low tasks a dedicated
    # worker process with --prefetch-multiplier=10 can be launched separately.
    worker_prefetch_multiplier=1,

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
        "followup.*":                    {"queue": "onboarding_low",    "priority": 3},
        "wsi.*":                         {"queue": "evaluation_normal", "priority": 4},
        "feedback.*":                    {"queue": "onboarding_low",    "priority": 3},
        "drift.run_batch":               {"queue": "onboarding_low",    "priority": 2},
        "digest.*":                      {"queue": "onboarding_low",    "priority": 3},
    },

    beat_schedule={
        # Drift check diário às 06h (Brasília = UTC-3 → 09h UTC)
        "drift-run-batch-daily": {
            "task": "drift.run_batch",
            "schedule": crontab(hour=9, minute=0),  # 06h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # P37-073: Golden scenario qualitative drift (after quantitative drift)
        "golden-drift-check-daily": {
            "task": "golden_drift.run_check",
            "schedule": crontab(hour=10, minute=0),  # 07h Brasília — runs after drift.run_batch
            "options": {"expires": 7200, "queue": "evaluation_normal"},
        },
        # PX08-12.7: GlobalInsights aggregation — daily at 05h Brasília (before drift at 07h)
        "global-insights-aggregate-daily": {
            "task": "insights.aggregate_all",
            "schedule": crontab(hour=8, minute=0),  # 05h Brasília / UTC-3
            "options": {"expires": 7200, "queue": "evaluation_normal"},
        },
        # PX08-12.7: Few-shot evolution — daily at 06h Brasília (between insights and drift)
        "fewshot-evolve-daily": {
            "task": "fewshot.evolve",
            "schedule": crontab(hour=9, minute=0),  # 06h Brasília / UTC-3
            "options": {"expires": 7200, "queue": "evaluation_normal"},
        },
        # Lifecycle policy de auditoria: 1º de cada mês às 03h (Brasília = UTC-3 → 06h UTC)
        "audit-lifecycle-monthly": {
            "task": "audit.apply_lifecycle_policy",
            "schedule": crontab(day_of_month=1, hour=6, minute=0),  # 03h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # F-05 P0 LGPD Art. 16: voice data retention daily at 03:15 UTC (00:15 Brasília)
        # Paulo approved 2026-05-22: 60d audio / 180d transcript / 365d wsi_score
        "voice-retention-daily": {
            "task": "voice.retention_purge_daily",
            "schedule": crontab(hour=3, minute=15),  # 00:15 Brasília / UTC-3
            "options": {"expires": 7200, "queue": "onboarding_low"},
        },
        # LGPD cleanup diário às 02h Brasília (UTC-3 → 05h UTC)
        "lgpd-cleanup-daily": {
            "task": "lgpd.run_cleanup_daily",
            "schedule": crontab(hour=5, minute=0),  # 02h Brasília / UTC-3
            "options": {"expires": 7200},
        },
        # UC-P3-17: LGPD deletion alert -- 90 days before scheduled deletion
        # Runs daily at 01h UTC (22h Brasilia previous day) -- before cleanup at 05h UTC
        "lgpd-deletion-alert-daily": {
            "task": "lgpd.deletion_alert",
            "schedule": crontab(hour=1, minute=0),  # 22h Brasilia / UTC-3
            "options": {"expires": 7200},
        },
        # TTL de conversa diário às 03h Brasília (UTC-3 → 06h UTC) — LGPD Art. 18
        "conversation-ttl-cleanup-daily": {
            "task": "conversation.ttl_cleanup",
            "schedule": crontab(hour=6, minute=0),  # 03h Brasília / UTC-3
            "options": {"expires": 7200},
        },
        # Briefing diário às 06h Brasília (UTC-3 → 09h UTC) — P3-1
        # LEGACY: despacha pra TODOS os users ativos (sem filtro briefing_frequency).
        # Migration plan: substituir por briefing-dispatch-daily abaixo apos
        # validacao + comunicacao a tenants.
        "briefing-daily": {
            "task": "briefing.send_daily",
            "schedule": crontab(hour=9, minute=0),  # 06h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # CANONICAL — Wave 3 Camada 3 Item 2: respeita briefing_frequency do
        # AlertConfig. Daily + twice_daily juntos no mesmo task (twice_daily
        # eh tratado pelo job em si — dispatcha 2x se preciso baseado em
        # briefing_hour_local, TBD field).
        "briefing-dispatch-daily": {
            "task": "briefing.dispatch_daily",
            "schedule": crontab(hour=9, minute=0),  # 06h Brasília / UTC-3
            "options": {"expires": 3600},
        },
        # Weekly: segundas-feiras 08h Brasilia (11h UTC). Coincide com
        # digest.send_weekly legacy, mas dispatcha so para tenants com
        # briefing_frequency='weekly' (digest sai pra todos).
        "briefing-dispatch-weekly": {
            "task": "briefing.dispatch_weekly",
            "schedule": crontab(hour=11, minute=0, day_of_week=1),  # Mon 08h Brasilia
            "options": {"expires": 7200},
        },
        # Monthly: dia 1 do mes, 08h Brasilia (11h UTC).
        "briefing-dispatch-monthly": {
            "task": "briefing.dispatch_monthly",
            "schedule": crontab(hour=11, minute=0, day_of_month=1),  # 1st @ 08h Brasilia
            "options": {"expires": 7200},
        },
        # Follow-up de convites WSI não abertos — a cada hora (Gap A)
                # WT-2022 Camada IA Proativa: scheduler-driven hints (1x/hora)
        "proactive-detect-hints-hourly": {
            "task": "proactive.detect_hints_hourly",
            "schedule": crontab(minute=5),  # :05 past every hour (offset de followup :00)
            "options": {"expires": 3500, "queue": "onboarding_low"},
        },
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
        # I6 — Feedback auto-send: processa feedback aprovado não enviado a cada 2h
        "feedback-process-pending-sends": {
            "task": "feedback.process_pending_sends",
            "schedule": crontab(minute=30, hour="*/2"),  # a cada 2h no minuto 30
            "options": {"expires": 7000},
        },
        # ACH-027 — Avaliação RAGAS diária às 03h UTC (00h Brasília)
        # Condicionada a ENABLE_RAG_EVAL (default: true). Desabilitar em ambientes sem RAGAS.
        **({
            "ragas-evaluate-daily": {
                "task": "ragas.evaluate_batch",
                "schedule": crontab(hour=3, minute=0),  # 00h Brasília / UTC-3
                "options": {"expires": 7200},
            },
        } if os.getenv("ENABLE_RAG_EVAL", "true").lower() == "true" else {}),
        # E9 — Adaptive Routing: recompute ajustes de confiança diariamente às 07h UTC (04h Brasília)
        "routing-recompute-daily": {
            "task": "routing.recompute_adjustments",
            "schedule": crontab(hour=7, minute=0),
            "args": ["global"],
            "options": {"expires": 3600},
        },
        # Etapa 4 — Retenção de dados LGPD: 1º de cada mês às 02h UTC
        "data-retention-monthly": {
            "task": "data.retention.run",
            "schedule": crontab(day_of_month=1, hour=2, minute=0),
            "options": {"expires": 7200},
        },
        # Phase 3b — Expurgo mensal de gravações de áudio (LGPD Art. 16)
        # 1º de cada mês 05:00 UTC = 02:00 BRT. Após data-retention-monthly (02h UTC).
        "expurgo-gravacoes-mensal": {
            "task": "expurgo_gravacoes_audio",
            "schedule": crontab(0, 5, day_of_month=1),  # 05:00 UTC = 02:00 BRT
            "options": {"expires": 7200, "queue": "onboarding_low"},
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
        # Weekly Digest: segundas-feiras 08h Brasília (UTC-3 → 11h UTC)
        "digest-weekly": {
            "task": "digest.send_weekly",
            "schedule": crontab(hour=11, minute=0, day_of_week=1),  # segunda 08h Brasília / UTC-3
            "options": {"expires": 3600},
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
        # UC-P2-02 -- AgentWorkingMemory TTL cleanup: daily at 03h15 UTC
        "agent-working-memory-cleanup-daily": {
            "task": "agent_working_memory.cleanup",
            "schedule": crontab(hour=3, minute=15),
            "options": {"expires": 7200},
        },
        # R-024: DLQ health check -- runs hourly, alerts if queue backlog exceeds thresholds
        "dlq-health-check-hourly": {
            "task": "health.check_dlq_health",
            "schedule": crontab(minute=10),  # :10 past every hour
            "options": {"expires": 3600, "queue": "celery"},
        },
        # R-002 -- Sensor diario de RLS Postgres em tabelas criticas (04h UTC)
        "rls-health-check-daily": {
            "task": "rls.health_check",
            "schedule": crontab(hour=4, minute=0),  # 01h Brasília / UTC-3
            "options": {"expires": 7200, "queue": "evaluation_normal"},
        },
    },
)