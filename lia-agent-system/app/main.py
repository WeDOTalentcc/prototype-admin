"""
LIA Agent System - Main FastAPI application.
"""
# === LLM Bootstrap: monkey-patch SDK constructors for PII + audit + tenant ===
# MUST be first import — before anything instantiates Anthropic/OpenAI/GenAI
from app.shared.llm_bootstrap import install_llm_guards

install_llm_guards(entrypoint="fastapi")

import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.sentry import init_sentry

init_sentry()

from app.api import orchestrator_routes
from app.config.langsmith import configure_langsmith
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.logging_middleware import StructuredLoggingMiddleware
from app.domains.automation.services.automation_handlers import register_all_handlers
from app.domains.automation.services.automation_scheduler import automation_scheduler
from app.middleware.auth_enforcement import AuthEnforcementMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.response_envelope import ResponseEnvelopeMiddleware
from app.shared.services.embedding_cache_service import embedding_cache
from app.domains.ai.services.llm import LLMService
from app.tools import initialize_tools

# Configure LangSmith tracing BEFORE logging
# W3-028 (2026-05-23): production fail-fast — LangSmith não-configurado
# em prod/staging é gap observability (sem traces LLM = audit cego).
# Em dev, continua sendo warn-only.
_LANGSMITH_OK = configure_langsmith()
if not _LANGSMITH_OK:
    import os as _os_w3028
    _env_w3028 = _os_w3028.environ.get("APP_ENV", "development")
    # W3-028 fix (2026-05-24): Datadog LLM Obs (Sprint 13.6 migration) eh
    # alternative canonical pra LLM observability. Se ativo, satisfaz W3-028
    # requirement sem precisar de LangSmith.
    _dd_llmobs = _os_w3028.environ.get("DD_LLMOBS_ENABLED") in ("1", "true", "True")
    _dd_key = bool(_os_w3028.environ.get("DD_API_KEY"))
    _alt_obs = _dd_llmobs and _dd_key
    if _env_w3028 in ("production", "prod", "staging") and not _alt_obs:
        raise RuntimeError(
            f"[W3-028] LLM Observability NAO configurado em ambiente {_env_w3028!r}. "
            "Set LANGSMITH_API_KEY OR (DD_LLMOBS_ENABLED=1 + DD_API_KEY) em Replit Secrets. "
            "Em dev, warn-only."
        )

from app.core.logging_config import configure_logging
from app.shared.pii_masking import install_global_pii_masking

configure_logging()
install_global_pii_masking()  # L7: LGPD — mascara CPF, e-mail, telefone e nomes em todos os logs
logger = logging.getLogger(__name__)



def _validate_redis_encryption_key() -> None:
    """
    R-001 — Fail-fast guard for REDIS_ENCRYPTION_KEY.

    Without REDIS_ENCRYPTION_KEY, ``app.shared.security.redis_crypto.RedisCrypto``
    silently falls back to plaintext storage (FAIL-OPEN by design for gradual
    rollout in dev). In production this is unacceptable — candidate PII,
    session data, and voting/fairness caches would land in Redis as plaintext.

    Pattern mirrors the LLM-key and OPENMIC_ALLOW_UNSIGNED_WEBHOOK guards in
    this same lifespan: warn in dev, raise ``RuntimeError`` in prod/staging.

    Raises:
        RuntimeError: if APP_ENV is production/prod/staging and the key is
            empty or whitespace-only.
    """
    _redis_key = os.getenv("REDIS_ENCRYPTION_KEY", "").strip()
    _is_production_env = os.getenv("APP_ENV", "development").lower() in (
        "production",
        "prod",
        "staging",
    )
    if _redis_key:
        logger.info("✅ Redis encryption configured (REDIS_ENCRYPTION_KEY present)")
        return
    if _is_production_env:
        logger.critical(
            "🚨 SECURITY: REDIS_ENCRYPTION_KEY is empty in production environment! "
            "PII (candidate data, sessions, voting cache) would be stored in plaintext. "
            "Generate key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
        raise RuntimeError(
            "REDIS_ENCRYPTION_KEY is required in production/staging environments. "
            "Refusing to start with PII at risk of plaintext storage."
        )
    logger.warning(
        "⚠️  REDIS_ENCRYPTION_KEY not set — PII stored in plaintext (dev mode only)"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info("🚀 Starting LIA Agent System...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # ─── ADR-AUTH-001: Required env vars fail-fast (canonical harness) ────
    # Validates DATABASE_URL, SECRET_KEY, FIELD_ENCRYPTION_KEY, REDIS_URL, etc.
    # Strict in production (raises). Warn-only in dev/IS_DEVELOPMENT=true.
    try:
        import sys as _sys
        _here = os.path.dirname(os.path.abspath(__file__))
        _root = os.path.dirname(_here)
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from scripts.check_required_env import validate_required_env
        _is_prod = os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging")
        _env_errors = validate_required_env(strict=True)
        if _env_errors:
            if _is_prod:
                _msg = (
                    f"{len(_env_errors)} required env var(s) missing or malformed "
                    f"(ADR-AUTH-001 startup check, APP_ENV={os.getenv('APP_ENV')}):\n\n"
                    + "\n──\n".join(_env_errors)
                )
                raise RuntimeError(_msg)
            logger.warning(
                "ADR-AUTH-001: %d env var(s) failing canonical check (dev mode — warn only):",
                len(_env_errors),
            )
            for _err in _env_errors:
                logger.warning("  %s", _err.replace("\n", " | "))
        else:
            logger.info("✅ ADR-AUTH-001: all required env vars valid.")
    except RuntimeError:
        raise  # re-raise the env validation error in prod
    except Exception as _env_check_exc:
        logger.warning("ADR-AUTH-001 env check skipped (import failed): %s", _env_check_exc)


    # ─── Audit-loop-leak fix (2026-05-20) ────────────────────────────────
    # Capture the running event loop so AuditService can redispatch
    # `_asyncio.run(audit.log_decision(...))` calls from LangGraph sync
    # nodes back onto this loop (prevents asyncpg pool poisoning).
    try:
        from app.shared.compliance.audit_service import register_main_loop
        register_main_loop()
    except Exception as _loop_reg_exc:
        logger.warning(
            "[AuditService] register_main_loop failed at startup: %s",
            _loop_reg_exc,
        )

    # ─── Sprint R.2 (2026-05-21) — aio_pika cross-loop close leak fix ────
    # Capture the running event loop so `publish_to_exchange()` can
    # redispatch publishes from LangGraph/Celery worker threads back onto
    # this loop, reusing the singleton aio_pika connection bound here.
    try:
        from app.shared.messaging.rabbitmq_producer import (
            register_main_loop as _register_mq_loop,
        )
        _register_mq_loop()
    except Exception as _mq_loop_reg_exc:
        logger.warning(
            "[RabbitMQProducer] register_main_loop failed at startup: %s",
            _mq_loop_reg_exc,
        )

    
    # Validate Microsoft Teams configuration
    if settings.MICROSOFT_APP_ID and settings.MICROSOFT_APP_PASSWORD:
        logger.info("✅ Microsoft Teams Bot configured")
    else:
        logger.warning("⚠️  Microsoft Teams Bot NOT configured (MICROSOFT_APP_ID/PASSWORD missing)")
        logger.warning("   Teams integration will not work until credentials are added")
    
    # Validate Microsoft Graph configuration
    if settings.AZURE_CLIENT_ID and settings.AZURE_CLIENT_SECRET and settings.AZURE_TENANT_ID:
        logger.info("✅ Microsoft Graph API configured (Outlook Calendar access enabled)")
    else:
        logger.warning("⚠️  Microsoft Graph API NOT configured (AZURE_CLIENT_ID/SECRET/TENANT_ID missing)")
        logger.warning("   Calendar/scheduling features will not work until credentials are added")
    
    # Validate Pearch AI configuration
    pearch_api_key = os.getenv("PEARCH_API_KEY")
    if pearch_api_key:
        logger.info("✅ Pearch AI configured (candidate search in 190M+ profiles enabled)")
    else:
        logger.warning("⚠️  Pearch AI NOT configured (PEARCH_API_KEY missing)")
        logger.warning("   Candidate search features will not work until API key is added")

    # ─── Validate global LLM provider keys ────────────────────────────────────
    # The platform uses a hybrid LLM provisioning strategy:
    #   1. Per-tenant config in `tenant_llm_configs` table (encrypted, set via
    #      menu Configurações > Integrações > LLM)
    #   2. Global env vars as fallback for tenants without their own config
    # Without at least ONE provider key, agents will fail at runtime when the
    # first chat message arrives — silent outage. Warn loudly here.
    has_anthropic = bool(
        getattr(settings, "AI_INTEGRATIONS_ANTHROPIC_API_KEY", None)
        or getattr(settings, "ANTHROPIC_API_KEY", None)
    )
    has_gemini = bool(getattr(settings, "AI_INTEGRATIONS_GEMINI_API_KEY", None))
    has_openai = bool(
        getattr(settings, "AI_INTEGRATIONS_OPENAI_API_KEY", None)
        or getattr(settings, "OPENAI_API_KEY", None)
    )
    if has_anthropic or has_gemini or has_openai:
        providers = [
            name
            for name, ok in (("anthropic", has_anthropic), ("gemini", has_gemini), ("openai", has_openai))
            if ok
        ]
        logger.info(f"✅ LLM provider(s) configured globally: {', '.join(providers)}")
        logger.info(
            "   Tenants without entries in `tenant_llm_configs` will use these as fallback."
        )
    else:
        logger.warning(
            "⚠️  NO LLM provider configured globally (AI_INTEGRATIONS_ANTHROPIC_API_KEY, "
            "ANTHROPIC_API_KEY, AI_INTEGRATIONS_GEMINI_API_KEY, OPENAI_API_KEY all empty)."
        )
        logger.warning(
            "   Agents will fail at runtime unless every tenant has its own entry "
            "in `tenant_llm_configs`. In production this is almost certainly a misconfiguration."
        )
        # In production environments, refuse to start with no LLM key at all.
        if os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging"):
            raise RuntimeError(
                "No LLM provider key configured globally and APP_ENV is production. "
                "Set AI_INTEGRATIONS_ANTHROPIC_API_KEY (or another provider) before deploying."
            )

    # Production safety guard: OPENMIC_ALLOW_UNSIGNED_WEBHOOK must never be true in prod
    _allow_unsigned = os.getenv("OPENMIC_ALLOW_UNSIGNED_WEBHOOK", "false").lower()
    _is_production = os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging")
    if _allow_unsigned == "true" and _is_production:
        logger.critical(
            "🚨 SECURITY: OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true is set in a production environment! "
            "This disables webhook signature verification. Remove this env var immediately."
        )
        raise RuntimeError(
            "OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true is not permitted in production. "
            "This bypasses webhook HMAC validation and must only be used in local development."
        )
    elif _allow_unsigned == "true":
        logger.warning(
            "⚠️  OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true — webhook signature check bypassed "
            "(dev mode only). Remove before deploying to production."
        )
    elif not os.getenv("OPENMIC_WEBHOOK_SECRET"):
        logger.warning(
            "⚠️  OPENMIC_WEBHOOK_SECRET not set — OpenMic webhook endpoint will return 503 "
            "for all incoming requests. Set OPENMIC_WEBHOOK_SECRET to enable the endpoint."
        )
    else:
        logger.info("✅ OpenMic webhook configured (HMAC-SHA256 signature validation enabled)")

    # Validate Redis encryption key (R-001 — fail-fast in prod/staging)
    _validate_redis_encryption_key()

    # ─── R-007: alerta agregado de flags de bypass de compliance ──────────────
    # Estas flags desligam camadas de compliance (FairnessGuard, PII strip,
    # AuditService, etc.). Em produção, NUNCA devem estar ON exceto rollback
    # emergencial — log CRITICAL + Sentry breadcrumb pra detecção.
    _BYPASS_FLAGS = {
        "LIA_ALLOW_NON_COMPLIANT_DOMAINS": "Bypass de ComplianceDomainPrompt (FairnessGuard, PII, PromptInjection, FactCheck)",
        "LIA_ALLOW_NON_COMPLIANT_AGENTS": "Bypass de LangGraphReActBase compliance em agents",
        "LIA_DISABLE_C3B": "KILL SWITCH da camada C3b inteira (PII strip + Fairness L3 + FactCheck + Audit) — passthrough total",
        "LIA_ALLOW_REGISTRY_DRIFT": "Permite class_path inválido em agents_registry (R-004 emergency rollback only)",
        # PR4 (Task #1004) — desliga audit log canônico em todas as save tools
        # de company_settings. Default OFF; quando ON, viola Inegociável #6
        # (auditabilidade SOX/EU AI Act). Use APENAS para rollback emergencial
        # se o storage de audit_logs estiver indisponível e o serviço estiver
        # bloqueando saves de configuração corporativa.
        "LIA_DISABLE_COMPANY_AUDIT": "Desliga audit log canônico em company_settings save tools (PR4 / Task #1004) — viola Inegociável #6",
    }
    _active_bypasses = [
        f"{flag}: {desc}"
        for flag, desc in _BYPASS_FLAGS.items()
        if os.getenv(flag, "0") == "1"
    ]

    # T-A canonical: LIA_AGENT_TENANT_STRICT é fail-CLOSED por default em
    # prod/staging. Quando explicitamente OFF em prod, agentes voltam a
    # degradar silenciosamente em "sua empresa"/"geral" (origem do bug
    # "LIA pergunta company_id no chat"). Logar como bypass agregado.
    from app.shared.agents.tenant_aware_agent import is_tenant_strict_mode
    _tenant_strict = is_tenant_strict_mode()
    _is_prod_like = os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging")
    if _is_prod_like and not _tenant_strict:
        _active_bypasses.append(
            "LIA_AGENT_TENANT_STRICT=false: TenantAwareAgentMixin em fail-OPEN — "
            "agentes vão degradar para 'sua empresa'/'geral' quando tenant ausente"
        )
    if _tenant_strict:
        logger.info("✅ TenantAwareAgentMixin fail-CLOSED ativo (LIA_AGENT_TENANT_STRICT=true)")
    else:
        logger.info("ℹ️  TenantAwareAgentMixin fail-OPEN (dev mode — agentes não bloqueiam por tenant ausente)")
    if _active_bypasses:
        logger.critical(
            "🚨 COMPLIANCE BYPASS ATIVA — %d flag(s):\n%s\n"
            "Em produção isso desabilita garantias LGPD/Fairness/Audit. "
            "Remover IMEDIATAMENTE se não for emergência rollback.",
            len(_active_bypasses),
            "\n".join(f"  • {b}" for b in _active_bypasses),
        )
        # PR4 follow-up: incluir staging conforme R-001 / R-007 — staging
        # também faz parte da postura prod-like (canary alerting depende).
        if os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging"):
            try:
                sentry_sdk.capture_message(
                    f"COMPLIANCE BYPASS ATIVA em {os.getenv('APP_ENV')}: "
                    f"{[f.split(':')[0] for f in _active_bypasses]}",
                    level="error",
                )
            except Exception:
                pass

    # T-E canary: Sentry alert dedicado pra LIA_AGENT_TENANT_STRICT=false
    # em prod (alerta isolado pra on-call diferenciar do agregado R-007).
    # Usa fingerprint estável `LIA_AGENT_TENANT_STRICT_BYPASS` pra Sentry
    # agrupar em UM issue persistente (alerting rules referenciam essa chave).
    if _is_prod_like and not _tenant_strict and os.getenv("APP_ENV", "development").lower() in ("production", "prod"):
        try:
            with sentry_sdk.push_scope() as _scope:
                _scope.fingerprint = ["LIA_AGENT_TENANT_STRICT_BYPASS"]
                _scope.set_tag("event_key", "LIA_AGENT_TENANT_STRICT_BYPASS")
                _scope.set_tag("compliance_flag", "LIA_AGENT_TENANT_STRICT")
                _scope.set_extra(
                    "runbook",
                    "docs/runbooks/missing_tenant_context.md",
                )
                _scope.set_extra(
                    "impact",
                    "TenantAwareAgentMixin fail-OPEN — agentes podem voltar a "
                    "perguntar 'qual empresa' no chat (bug histórico).",
                )
                sentry_sdk.capture_message(
                    "LIA_AGENT_TENANT_STRICT_BYPASS",
                    level="error",
                )
        except Exception:
            pass

    # ─── R-051: LangSmith availability warning ──────────────────────────────────
    from app.config.langsmith import is_langsmith_enabled  # R-051
    if not is_langsmith_enabled():
        _startup_logger = logging.getLogger("lia.startup")
        _startup_logger.warning(
            "LangSmith tracing not configured (LANGSMITH_API_KEY / LANGCHAIN_API_KEY not set). "
            "LLM traces will not be captured. Set LANGSMITH_API_KEY to enable."
        )  # R-051
    else:
        logging.getLogger("lia.startup").info("LangSmith tracing enabled (lia.startup)")  # R-051

    # ─── Onda 1.F + Sprint R.1 (2026-05-21): AsyncPostgresSaver canonical ───────
    # Startup fail-closed: em production/staging, abortar boot se
    # checkpointer for MemorySaver. Defense-in-depth contra regressao do
    # bug V1.d e Task #1161 Bug B (PostgresSaver sync → aget_tuple
    # NotImplementedError silenciado → MemorySaver → state loss em restart).
    # Sprint R.1: initialize_checkpointer_async PRECISA rodar antes de
    # qualquer agente instanciar (LangGraphBase.__init__ chama
    # get_checkpointer no caminho sync).
    try:
        from lia_agents_core.checkpointer import (
            get_checkpointer,
            initialize_checkpointer_async,
        )
        _cp = await initialize_checkpointer_async()
        _cp_type = type(_cp).__name__ if _cp is not None else "None"
        _app_env = getattr(settings, "APP_ENV", "development")
        _is_prod_like = _app_env in {"production", "staging"}
        _memory_names = {"MemorySaver", "MemorySaver(default)", "InMemorySaver"}
        if _is_prod_like and _cp_type in _memory_names:
            _msg = (
                f"[Onda1.F] FAIL-CLOSED boot: checkpointer={_cp_type!r} em "
                f"APP_ENV={_app_env!r}. MemorySaver wipa em restart — "
                f"checkpoints LangGraph nao persistiriam. Investigar "
                f"PostgresSaver+DATABASE_URL antes de retomar."
            )
            logging.getLogger("lia.startup").critical(_msg)
            raise SystemExit(2)
        logging.getLogger("lia.startup").info(
            "[Onda1.F] Checkpointer canonical OK: type=%s env=%s",
            _cp_type, _app_env,
        )
    except SystemExit:
        raise
    except Exception as _cp_exc:
        # Em dev, falha em construir o checkpointer NAO derruba boot —
        # _memory_saver() de _fallback_ ainda permite o sistema subir.
        logging.getLogger("lia.startup").warning(
            "[Onda1.F] Checkpointer health-check soft-failed: %s", _cp_exc,
        )

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Domain auto-discovery
    from app.domains.registry import DomainRegistry
    domain_registry = DomainRegistry()
    registered = domain_registry.list_domains()
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"✅ Domain registry: {len(registered)} domains registered: {registered}")
    
    # Warm-up embedding cache
    try:
        async with AsyncSessionLocal() as db:
            await embedding_cache.warm_up(db)
    except Exception as e:
        logger.warning(f"⚠️ Embedding cache warm-up failed: {e}")
    
    try:
        from app.core.prompt_version_loader import register_all_prompts_at_startup
        _prompt_count = register_all_prompts_at_startup()
        logger.info(f"✅ PromptVersionRegistry: {_prompt_count} YAML prompts registered")
    except Exception as e:
        logger.warning(f"⚠️ Prompt version registration failed: {e}")

    try:
        from app.core.prompt_version_loader import bootstrap_experiments_from_yaml
        _exp_count = bootstrap_experiments_from_yaml()
        if _exp_count:
            logger.info(f"✅ A/B experiments: {_exp_count} loaded from YAML")
    except Exception as e:
        logger.warning(f"⚠️ A/B experiment bootstrap failed: {e}")

    # Initialize Orchestrator
    try:
        llm_service = LLMService()
        orchestrator_routes.initialize_orchestrator(llm_service)
        logger.info("✅ Multi-Agent Orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Orchestrator initialization failed: {e}", exc_info=True)
        logger.warning("   Orchestrator endpoints will not work until initialization succeeds")
    
    # Start Automation Scheduler
    try:
        automation_scheduler.start()
        logger.info("✅ Automation Scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Automation Scheduler não iniciou: {e} — jobs periódicos inativos")
    
    # Initialize Stage Automation Engine and register handlers
    try:
        register_all_handlers()
        logger.info("✅ Stage Automation Engine initialized with handlers")
    except Exception as e:
        logger.error(f"❌ Stage Automation Engine initialization failed: {e}")
        logger.warning("   Automation triggers will not work until handlers are registered")
    
    # Initialize Tool Registry for function calling
    try:
        initialize_tools()
        logger.info("✅ Tool Registry initialized")
    except Exception as e:
        logger.error(f"❌ Tool Registry initialization failed: {e}")
        logger.warning("   Function calling tools will not work until registry is initialized")

    # Validate LLM circuit breaker configuration (timeouts, thresholds, fallbacks)
    try:
        from app.shared.resilience.circuit_breaker import validate_llm_circuit_configs
        _cb_validation = validate_llm_circuit_configs()
        if _cb_validation.get("_all_ok"):
            logger.info(
                "✅ LLM circuit breakers validated: anthropic=%.0fs/threshold=%d, "
                "openai=%.0fs/threshold=%d, gemini=%.0fs/threshold=%d",
                _cb_validation["anthropic"]["timeout_s"], _cb_validation["anthropic"]["failure_threshold"],
                _cb_validation["openai"]["timeout_s"], _cb_validation["openai"]["failure_threshold"],
                _cb_validation["gemini"]["timeout_s"], _cb_validation["gemini"]["failure_threshold"],
            )
        else:
            _issues = {k: v["issues"] for k, v in _cb_validation.items() if isinstance(v, dict) and not v.get("ok")}
            logger.error("❌ LLM circuit breaker validation failed: %s", _issues)
    except Exception as e:
        logger.warning("⚠️  LLM circuit breaker validation error (non-blocking): %s", e)

    try:
        from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop
        await monitoring_loop.start()
        # Task #1060: start() is a no-op quando MONITORING_LOOP_INTERVAL_SECONDS=0;
        # logamos o estado real (running × disabled) pra deixar evidente em dev.
        if monitoring_loop.is_running:
            logger.info(
                "✅ MonitoringLoop started (proactive pipeline checks every %ds)",
                monitoring_loop._check_interval,
            )
        else:
            logger.info(
                "ℹ️  MonitoringLoop não iniciado (MONITORING_LOOP_INTERVAL_SECONDS=0) — "
                "alertas proativos desligados nesta instância (Task #1060 — dev/Playwright)."
            )
    except Exception as e:
        logger.warning("⚠️  MonitoringLoop não iniciou: %s — alertas proativos inativos", e)

    # Seed PolicyEngine default rules (idempotente — skip-if-exists)
    try:
        # Canonical path (Sprint 11 T-09 B+A combo: shim app.shared.services.policy_engine_service deletado)
        from app.domains.policy.services.policy_engine_service import PolicyEngineService
        _pe_stats = await PolicyEngineService().load_default_rules()
        logger.info(
            f"✅ PolicyEngine rules seeded: "
            f"{_pe_stats.get('business_rules_created', 0)} business, "
            f"{_pe_stats.get('rate_limit_rules_created', 0)} rate-limit, "
            f"{_pe_stats.get('escalation_rules_created', 0)} escalation criadas; "
            f"{_pe_stats.get('business_rules_skipped', 0) + _pe_stats.get('rate_limit_rules_skipped', 0) + _pe_stats.get('escalation_rules_skipped', 0)} já existiam"
        )
    except Exception as e:
        logger.warning(f"⚠️  PolicyEngine seed failed (non-blocking): {e}")

    # W1-001-B (2026-05-23): ReAct agent registry agora é AgentRegistry canonical
    # (singleton via @register_agent decorator). Registro lazy via
    # _ensure_agents_loaded() no agent_chat_ws.py e workflow.py — sem boot call.
    # Legacy register_react_agents() removido pra evitar double-register e
    # ambiguidade de naming.

    # W3-030 (2026-05-23): wire AiConsumptionOutbox drainer worker.
    # Background loop drena `ai_consumption_outbox` table → AiConsumption
    # via TokenTrackingService. Sem worker, callbacks de usage_tracking
    # gravam no outbox mas NUNCA são entregues (silent data loss).
    try:
        from app.shared.observability.ai_consumption_outbox_worker import (
            get_outbox_worker,
        )
        await get_outbox_worker().start()
        logger.info("✅ AiConsumptionOutbox drainer worker started")
    except Exception as e:
        logger.error(f"❌ AiConsumptionOutbox worker start failed (non-blocking): {e}")

    # Initialize RabbitMQ Consumer (Phase 4 — WS async response forwarding)
    try:
        from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
        await rabbitmq_consumer.start()
        if rabbitmq_consumer._running:
            logger.info("✅ RabbitMQ Consumer iniciado")
        else:
            logger.info("ℹ️  RabbitMQ Consumer inativo (RABBITMQ_URL não configurado)")
    except Exception as e:
        logger.warning(f"⚠️  RabbitMQ Consumer não iniciado: {e}")

    # Register Platform Event Handlers (inter-API async communication via RabbitMQ)
    try:
        from app.api.v1.platform_event_handlers import register_all_handlers as register_platform_handlers
        register_platform_handlers()
        logger.info("✅ Platform Event Handlers registrados")
    except Exception as e:
        logger.warning(f"⚠️  Platform Event Handlers não registrados: {e}")

    # Seed A/B Testing email template variants (Fase 5 / A5 — idempotent)
    try:
        from app.shared.intelligence.ab_testing import seed_email_ab_tests
        async with AsyncSessionLocal() as _ab_db:
            _ab_result = await seed_email_ab_tests(_ab_db)
            logger.info(
                "✅ A/B Testing seeded: created=%d, skipped=%d",
                len(_ab_result.get("created", [])),
                len(_ab_result.get("skipped", [])),
            )
    except Exception as e:
        logger.warning(f"⚠️  A/B Testing seed failed (non-blocking): {e}")

    # Validate OpenAPI schema generation (pre-flight check — catch Pydantic schema errors at startup)
    try:
        schema = app.openapi()
        path_count = len(schema.get("paths", {}))
        schema_count = len(schema.get("components", {}).get("schemas", {}))
        logger.info(
            "✅ OpenAPI schema generated successfully: %d endpoints, %d schemas",
            path_count, schema_count,
        )
    except Exception as e:
        logger.error(
            "❌ OpenAPI schema generation failed — /openapi.json will return 500: %s", e,
            exc_info=True,
        )

    logger.info("🎯 LIA Agent System ready!")

    yield

    # Shutdown
    # Parar RabbitMQ Consumer
    try:
        from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
        await rabbitmq_consumer.stop()
    except Exception:
        pass
    # Sprint R.2: close singleton aio_pika producer connection on main loop
    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.close()
    except Exception:
        pass
    # W3-030 (2026-05-23): graceful shutdown do outbox drainer worker.
    # `stop()` drena último lote pendente antes de cancelar a task.
    try:
        from app.shared.observability.ai_consumption_outbox_worker import (
            get_outbox_worker,
        )
        await get_outbox_worker().stop()
    except Exception:
        pass
    logger.info("🛑 Shutting down LIA Agent System...")

    # Sprint R.1: close AsyncPostgresSaver pool
    try:
        from lia_agents_core.checkpointer import shutdown_checkpointer_async
        await shutdown_checkpointer_async()
    except Exception as _cp_exc:
        logger.warning("[Sprint R.1] erro fechando checkpointer pool: %s", _cp_exc)

    try:
        from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop
        await monitoring_loop.stop()
    except Exception:
        pass

    # Stop WebSocket manager (Redis pub/sub cleanup)
    try:
        from app.shared.websocket.ws_manager import ws_manager
        await ws_manager.shutdown()
    except Exception:
        pass

    # Stop Automation Scheduler
    try:
        automation_scheduler.stop()
    except Exception as e:
        logger.error(f"Error stopping Automation Scheduler: {e}")


# ---------------------------------------------------------------------------
# OpenAPI tags — categorias de endpoints para documentação automática
# ---------------------------------------------------------------------------
_OPENAPI_TAGS = [
    {"name": "agents", "description": "Agentes ReAct de recrutamento (chat WebSocket, HITL, orquestrador)"},
    {"name": "candidates", "description": "Gestão de candidatos, busca RAG híbrida, TOON cards"},
    {"name": "jobs", "description": "Vagas, descrições de cargo, wizard, importação JD"},
    {"name": "rag-search", "description": "Busca semântica híbrida BM25 + pgvector (Sprint G6)"},
    {"name": "hitl", "description": "Human-in-the-Loop: aprovar/rejeitar ações de agentes"},
    {"name": "guardrails", "description": "Guardrails de agentes: CRUD + seed-defaults + toggle"},
    {"name": "pipeline", "description": "Pipeline de candidatos, stages, transições, kanban"},
    {"name": "sourcing", "description": "Busca ativa, boolean strings, abordagem WhatsApp"},
    {"name": "cv-screening", "description": "Triagem curricular, rubrica WSI, scores, red flags"},
    {"name": "compliance", "description": "LGPD, bias audit, fairness guard, DSR, consentimento"},
    {"name": "analytics", "description": "KPIs, funil, previsões ML, relatórios, model drift"},
    {"name": "communication", "description": "Email, WhatsApp, Teams, notificações, templates"},
    {"name": "scheduling", "description": "Agendamento de entrevistas, calendário, convites"},
    {"name": "auth", "description": "Autenticação, WorkOS SSO, permissões"},
    {"name": "admin", "description": "Administração, monitoramento, circuit breakers, tokens"},
    {"name": "health", "description": "Health check, observabilidade, métricas"},
    {"name": "toon", "description": "TOON cards — perfil visual de candidato por vaga (Sprint G7)"},
    {"name": "drift", "description": "Model drift detection e alertas automáticos"},
    {"name": "bias-audit", "description": "Auditoria de bias Four-Fifths Rule por vaga"},
    {"name": "wsi", "description": "WSI — entrevista estruturada por WhatsApp/voz"},
    {"name": "policy-engine", "description": "Motor de políticas de recrutamento por setor"},
    {"name": "short-lists", "description": "Short lists de candidatos por vaga (Sprint F4)"},
]

# Create FastAPI app
app = FastAPI(
    title="LIA Agent System — WeDOTalent",
    summary="Plataforma B2B SaaS de recrutamento inteligente com IA (LangGraph + Claude Sonnet 4.5)",
    description="""
## LIA — Learning Intelligence Assistant

API REST + WebSocket da plataforma de recrutamento inteligente **WeDOTalent**.

### Arquitetura
- **7 agentes ReAct** (LangGraph): Wizard, Pipeline, Sourcing, Talent, JobsManagement, Kanban, Policy
- **362 endpoints REST** + WebSocket chat
- **Multi-tenant**: `company_id` obrigatório em todos os recursos
- **Compliance**: LGPD, BCB 498, SOX, ISO 27001, EU AI Act

### Autenticação
Bearer token via WorkOS SSO:
```
Authorization: Bearer <token>
```

### Convenções
- Datas em ISO 8601 UTC (`2026-03-15T10:00:00Z`)
- UUIDs para todos os IDs
- Paginação: `?page=1&page_size=20`
- Multi-tenant: `?company_id=<uuid>` ou header `X-Company-ID`

### Links úteis
- [Documentação de referência](/docs/redoc)
- [OpenAPI JSON](/openapi.json)
    """,
    version="3.0.0",
    lifespan=lifespan,
    debug=False,  # T-canonical-2026-05-20 (audit F2.B2): hardcoded, NÃO usa
                  # settings.DEBUG. settings.DEBUG=True em dev pode vazar
                  # stack trace pro client via Starlette ServerErrorMiddleware
                  # quando pre-handler errors escapam (e.g. Pydantic constraint
                  # inválida em path param). Stack vai apenas pra logs server-side.
    openapi_tags=_OPENAPI_TAGS,
    contact={
        "name": "WeDOTalent Engineering",
        "url": "https://wedotalent.com",
        "email": "tech@wedotalent.com",
    },
    license_info={
        "name": "Proprietary — WeDOTalent",
        "url": "https://wedotalent.com/terms",
    },
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/docs/redoc",
    redirect_slashes=False,
)

# Auth enforcement — validates JWT and injects company_id (multi-tenancy)
app.add_middleware(AuthEnforcementMiddleware)

# Response envelope — auto-wraps 2xx JSON into {"ok": true, "data": ...}
app.add_middleware(ResponseEnvelopeMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# W2-009-B (2026-05-23): Idempotency-Key Stripe-style cache para mutations
# (POST/PUT/PATCH/DELETE). Header opcional; passthrough quando ausente.
# Wired DEPOIS de RateLimit (mais externo) e ANTES de Auth (mais interno)
# pra que cache só seja consultado após company_id estar resolvido.
app.add_middleware(IdempotencyMiddleware)

# CORS must be added AFTER RateLimitMiddleware so it executes BEFORE it
# (FastAPI processes add_middleware in reverse order).
# This ensures 429 responses include CORS headers for browser clients.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Company-ID",
        "X-Tenant-ID",
        "Accept",
        "Origin",
        "Cache-Control",
    ],
)

# Request ID middleware
app.add_middleware(RequestIdMiddleware)

# Structured logging — outermost so it captures final status code
app.add_middleware(StructuredLoggingMiddleware)

from fastapi import Request as FastAPIRequest
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# LIAError handler — unified error hierarchy (P35-060)
# ---------------------------------------------------------------------------
from app.shared.errors import LIAError, LIAComplianceError


@app.exception_handler(LIAComplianceError)
async def lia_compliance_error_handler(request: FastAPIRequest, exc: LIAComplianceError):
    """Compliance errors return 451 (Unavailable For Legal Reasons). Never silenced."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "LIAComplianceError: code=%s message=%s [request_id=%s]",
        exc.code, exc.message, request_id,
    )
    return JSONResponse(
        status_code=451,
        content={**exc.to_dict(), "request_id": request_id},
    )


@app.exception_handler(LIAError)
async def lia_error_handler(request: FastAPIRequest, exc: LIAError):
    """LIA platform errors return structured JSON with appropriate status code."""
    request_id = getattr(request.state, "request_id", "unknown")
    status = 400 if exc.recoverable else 500
    logger.warning(
        "LIAError: code=%s recoverable=%s [request_id=%s]",
        exc.code, exc.recoverable, request_id,
    )
    return JSONResponse(
        status_code=status,
        content={**exc.to_dict(), "request_id": request_id},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: FastAPIRequest, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    # 5xx: log real detail internally, never expose to client (OWASP A05)
    if exc.status_code >= 500:
        logger.error(
            "HTTP %d raised explicitly: %s [request_id=%s]",
            exc.status_code, exc.detail, request_id,
        )
    safe_message = exc.detail if exc.status_code < 500 else "Internal server error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": safe_message,
            "request_id": request_id,
        }
    )


from app.domains.credits.services.token_budget_service import RequestBudgetExceededError


@app.exception_handler(RequestBudgetExceededError)
async def request_budget_exceeded_handler(request: FastAPIRequest, exc: RequestBudgetExceededError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "[RequestBudget] Request bloqueado por ceiling: "
        "company_id=%s agent_type=%s estimated=%d ceiling=%d plan=%s request_id=%s",
        exc.company_id, exc.agent_type, exc.estimated_tokens,
        exc.ceiling, exc.plan_code, request_id,
    )
    return JSONResponse(
        status_code=413,
        content={
            "error": "request_too_large",
            "message": (
                f"Request excede o limite de tokens por chamada "
                f"({exc.estimated_tokens:,} estimados / {exc.ceiling:,} permitidos). "
                "Reduza o tamanho do prompt ou contexto."
            ),
            "estimated_tokens": exc.estimated_tokens,
            "ceiling": exc.ceiling,
            "agent_type": exc.agent_type,
            "plan_code": exc.plan_code,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: FastAPIRequest, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "request_id": request_id,
        }
    )



@app.exception_handler(TypeError)
async def type_error_handler(request: FastAPIRequest, exc: TypeError) -> JSONResponse:
    """
    Captura TypeError que escapa de dependency resolution (audit F2.B2).

    Pydantic 2.10 lança TypeError ao tentar aplicar constraint inválida (e.g.,
    `pattern=` em type UUID — vide F2.B1). Sem este handler dedicado, o erro
    vaza pelo ServerErrorMiddleware da Starlette com stack trace completo.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"TypeError em dependency/handler resolution: {exc}",
        exc_info=True,
        extra={"request_id": request_id, "path": str(request.url.path)},
    )
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "code": "TYPE_RESOLUTION_ERROR",
            "message": "Erro interno na resolução do tipo do parâmetro",
            "request_id": request_id,
        },
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_error_handler(request: FastAPIRequest, exc: PydanticValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "Pydantic validation error: %d errors on %s %s",
        len(exc.errors()), request.method, request.url.path,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "code": "VALIDATION_ERROR",
            "message": "Validation error",
            "errors": exc.errors(include_url=False),
            "request_id": request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: FastAPIRequest, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    # T-1168 — incluir o `errors()` no log é essencial para diagnose: antes só
    # logávamos a contagem ("1 errors on POST /api/v1/wsi/screening-pipeline"),
    # o que escondeu por horas o campo culpado (`seniority` com Literal violation).
    # `errors()` é determinístico e não vaza segredos (Pydantic redige valores).
    _err_summary = [
        {"loc": e.get("loc"), "type": e.get("type"), "msg": e.get("msg")}
        for e in exc.errors()
    ]
    logger.warning(
        "Request validation error: %d errors on %s %s — details=%s",
        len(exc.errors()), request.method, request.url.path, _err_summary,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "code": "REQUEST_VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )


# Register all API routers
from app.api.routes import register_all_routes

register_all_routes(app)  # includes: admin_dlq_router, health, sourcing, etc.

# Serve Teams icons from the Next.js public folder (or a local fallback).
# Required so Teams can fetch color/outline icons when validating the app manifest.
try:
    import os as _os
    from fastapi.staticfiles import StaticFiles
    _teams_icons_candidates = [
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "plataforma-lia", "public", "teams-icons"),
        _os.path.join(_os.path.dirname(__file__), "static", "teams-icons"),
    ]
    for _icons_dir in _teams_icons_candidates:
        _icons_dir = _os.path.normpath(_icons_dir)
        if _os.path.isdir(_icons_dir):
            app.mount("/teams-icons", StaticFiles(directory=_icons_dir), name="teams-icons")
            logger.info(f"✅ Teams icons served at /teams-icons from {_icons_dir}")
            break
    else:
        logger.warning("⚠️  Teams icons directory not found — /teams-icons/ will return 404")
except Exception as _e:
    logger.warning(f"⚠️  Could not mount Teams icons static files: {_e}")


# Root-level health check redirects to comprehensive system health
from fastapi.responses import RedirectResponse


@app.get("/health")
async def app_health_check():
    """Root health check - redirects to comprehensive system health endpoint."""
    return RedirectResponse(url="/api/v1/health", status_code=307)


# ---------------------------------------------------------------------------
# Prometheus /metrics endpoint (Hardening C, registrado 2026-05-21)
# Expose canary metrics (canary_metrics.py + fallback_metrics.py + tenant-aware
# counters) para scraping por Prometheus / Grafana.
# Endpoint eh PUBLIC por convencao Prometheus (deploy time deve restringir
# acesso via firewall ou reverse-proxy basic-auth se exposto publicamente).
# ---------------------------------------------------------------------------
@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    """Prometheus scrape endpoint.

    Returns text/plain exposition do default REGISTRY. Fail-open: se
    prometheus_client nao estiver instalado, retorna HTTP 503 com body
    explicativo (preferivel a 500 silencioso pro scraper).
    """
    try:
        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            REGISTRY,
            generate_latest,
        )
        from fastapi.responses import Response

        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:  # pragma: no cover -- prometheus_client opcional em dev
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(
            content="prometheus_client not installed",
            status_code=503,
        )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "LIA Agent System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
