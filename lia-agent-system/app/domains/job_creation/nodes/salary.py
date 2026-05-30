"""salary_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

Validate salary range vs market benchmark (Phase 2C-1).
"""

import logging
import time
from typing import Any, Dict, Optional

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.helpers.llm_exceptions import classify_llm_exception_reason
from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

logger = logging.getLogger(__name__)


def salary_node(state: JobCreationState) -> JobCreationState:
    """Validate salary range vs market benchmark.

    Phase 2C-1: now actively fetches benchmark from internal + market sources
    and combines via MarketBenchmarkService.combine_with_internal() (peso 70/30).
    """
    # Lazy import of helpers defined in graph.py (avoids circular import).
    from app.domains.job_creation.graph import (  # noqa: E402
        _emit_fallback_telemetry,
        _emit_wizard_fallback_metric,
    )

    t0 = time.time()
    logger.info("[JobCreation:salary] Starting salary validation")

    # ── Fetch benchmark if not already in state ──
    # Task #1062: timeout determinístico (D4 da auditoria #1058). Em timeout
    # o nó pula benchmark gracefully (`salary_benchmark=None`) — recrutador
    # pode preencher manualmente sem travar o wizard.
    _SALARY_TIMEOUT_S = float(__import__("os").environ.get(
        "LIA_SALARY_TIMEOUT_S", "45"
    ))
    # Task #1065 — flag de fallback (timeout do benchmark fetch ou
    # exception). Painel renderiza banner pedindo revisão manual da faixa.
    salary_used_fallback = False
    # Task #1067 — root-cause label propagado pro painel.
    salary_fallback_reason: Optional[str] = None
    if not state.get("salary_benchmark"):
        try:
            # PR-14 (2026-05-26): substituido _asyncio.run() + ThreadPoolExecutor
            # local por helper canonical run_coro_in_threadpool(). _cf_sl mantido
            # apenas para capturar TimeoutError (mesmo type lancado pelo helper).
            import concurrent.futures as _cf_sl

            async def _fetch_benchmark():
                from app.core.database import AsyncSessionLocal
                from app.domains.analytics.services.job_insights_service import JobInsightsService
                from app.domains.analytics.services.market_benchmark_service import MarketBenchmarkService

                role = state.get("parsed_title") or ""
                seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or ""
                location = state.get("parsed_location") or None
                work_model = state.get("parsed_model") or None
                company_id = str(state.get("workspace_id") or state.get("company_id") or "")

                internal = {}
                market = {}

                # Source 1: internal (requires DB)
                if company_id and role:
                    try:
                        async with AsyncSessionLocal() as _db:
                            insights = JobInsightsService()
                            internal = await insights.get_salary_benchmark(
                                db=_db, company_id=company_id, role=role,
                                seniority=seniority, location=location,
                                work_model=work_model,
                            )
                    except Exception as _int_exc:
                        logger.warning(
                            "[JobCreation:salary] internal benchmark failed: %s", _int_exc,
                        )

                # Source 2: market
                try:
                    market_svc = MarketBenchmarkService()
                    market = await market_svc.search_salary_benchmark(
                        role=role, seniority=seniority, location=location,
                    )
                except Exception as _mkt_exc:
                    logger.warning(
                        "[JobCreation:salary] market benchmark failed: %s", _mkt_exc,
                    )

                # Combine 70/30 if internal high-confidence
                combined = {}
                try:
                    market_svc = MarketBenchmarkService()
                    combined = market_svc.combine_with_internal(
                        internal_data=internal if internal.get("sample_size", 0) > 0 else None,
                        market_data=market,
                    )
                except Exception as _comb_exc:
                    logger.warning(
                        "[JobCreation:salary] combine failed (fail-open): %s", _comb_exc,
                    )
                    combined = market or internal or {}

                return combined

            # PR-14 (2026-05-26): helper canonical run_coro_in_threadpool()
            # substitui ThreadPoolExecutor inline + _run_fetch wrapper. Mesma
            # semantica de timeout (concurrent.futures.TimeoutError).
            try:
                _benchmark = run_coro_in_threadpool(
                    _fetch_benchmark, timeout=_SALARY_TIMEOUT_S
                )
            except _cf_sl.TimeoutError:
                logger.warning(
                    "[JobCreation:salary] benchmark fetch timeout after %.1fs — "
                    "skipping benchmark gracefully (Task #1062)",
                    _SALARY_TIMEOUT_S,
                )
                _benchmark = None
                salary_used_fallback = True
                salary_fallback_reason = "timeout"
                _emit_wizard_fallback_metric(
                    node="salary", state=state, reason="benchmark_timeout",
                    timeout_s=_SALARY_TIMEOUT_S,
                    elapsed_ms=(time.time() - t0) * 1000,
                )
            if _benchmark:
                state = {**state, "salary_benchmark": _benchmark}
                # P0-B (auditoria 2026-05-29): popular a faixa salarial a partir
                # do benchmark de mercado quando o recrutador ainda não definiu
                # uma. Default aceitável — sobrescrevível via painel/chat (Fase 3).
                # Sem isso a vaga era publicada com salary_min/max=None.
                if state.get("salary_min") is None and _benchmark.get("min") is not None:
                    state = {
                        **state,
                        "salary_min": _benchmark.get("min"),
                        "salary_max": _benchmark.get("max"),
                        "salary_currency": _benchmark.get("currency", "BRL"),
                    }
                logger.info(
                    "[JobCreation:salary] benchmark fetched: source=%s conf=%s",
                    _benchmark.get("source"), _benchmark.get("confidence"),
                )
        except Exception as _bench_exc:
            # Fail-open — não bloqueia o wizard se serviços falharem
            logger.warning(
                "[JobCreation:salary] benchmark fetch failed (fail-open): %s", _bench_exc,
            )
            salary_used_fallback = True
            salary_fallback_reason = classify_llm_exception_reason(_bench_exc)

    updates: Dict[str, Any] = {
        "current_stage": "salary",
        "stage_history": (state.get("stage_history") or []) + ["salary"],
        "completeness": calculate_completeness("salary"),
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="salary",
            completeness=calculate_completeness("salary"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    msg("salary.ready_fallback")
                    if salary_used_fallback
                    else msg("salary.ready")
                ),
                "salary_min": state.get("salary_min"),
                "salary_max": state.get("salary_max"),
                "salary_currency": state.get("salary_currency", "BRL"),
                "benefits": state.get("benefits", []),
                "benchmark": state.get("salary_benchmark"),
                # Task #1065 — flag de fallback (timeout do benchmark fetch).
                # Painel renderiza banner pedindo revisão manual da faixa.
                "salary_used_fallback": salary_used_fallback,
                # Task #1067 — root-cause label.
                "salary_fallback_reason": salary_fallback_reason,
                # Task #1070 — snapshot agregado de degradação (sessão/tenant).
                "ai_degraded_mode": _emit_fallback_telemetry(
                    state, "salary", salary_fallback_reason,
                ),
            },
        ),
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:salary] %0.fms", elapsed)
    return {**state, **updates}
