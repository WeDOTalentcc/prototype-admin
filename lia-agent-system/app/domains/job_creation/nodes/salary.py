"""salary_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

Validate salary range vs market benchmark (Phase 2C-1).

Audit 2026-06-06 — faixa da EMPRESA tem precedência sobre o benchmark de
mercado. A faixa cadastrada em Configurações → Faixas Salariais por Nível é
política da empresa (fonte verificada), não estimativa. Resolve por nível +
departamento + contrato ANTES de buscar mercado; mercado vira fallback.
Precedência: right_panel_form (recrutador) > banda da empresa > benchmark.
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


def _resolve_company_salary_band(state: JobCreationState) -> Optional[Dict[str, Any]]:
    """Resolve a faixa salarial CADASTRADA da empresa pro escopo da vaga.

    Fonte: Configurações → Faixas Salariais por Nível (SalaryBand). Casa por
    nível + departamento + contrato via SalaryBandRepository.match_band (mesmo
    matcher do endpoint /company/salary-bands/resolve). Política da empresa =
    fonte verificada, tem precedência sobre o benchmark de mercado.

    Retorna {"min", "max", "currency"} ou None (sem banda / sem contexto /
    falha — fail-open: o caller cai no benchmark).
    """
    seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or ""
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id or company_id in ("default", "unknown") or not seniority:
        return None

    department = state.get("parsed_department") or None
    contract_type = state.get("parsed_employment_type") or None

    _BAND_TIMEOUT_S = float(__import__("os").environ.get("LIA_SALARY_BAND_TIMEOUT_S", "10"))

    async def _resolve():
        from app.core.database import AsyncSessionLocal
        from app.domains.company.repositories.salary_band_repository import (
            SalaryBandRepository,
        )

        async with AsyncSessionLocal() as _db:
            repo = SalaryBandRepository(_db)
            band = await repo.match_band(
                company_id,
                seniority_level=seniority,
                department=department,
                contract_type=contract_type,
            )
            if band is None or band.min is None:
                return None
            return {
                "min": band.min,
                "max": band.max,
                "currency": band.currency or "BRL",
            }

    return run_coro_in_threadpool(_resolve, timeout=_BAND_TIMEOUT_S)


def salary_node(state: JobCreationState) -> JobCreationState:
    """Validate salary range vs company band, then market benchmark.

    Phase 2C-1: now actively fetches benchmark from internal + market sources
    and combines via MarketBenchmarkService.combine_with_internal() (peso 70/30).
    Audit 2026-06-06: a faixa cadastrada da empresa (SalaryBand) tem precedência
    sobre o benchmark de mercado — mercado só é consultado quando não há banda.
    """
    # Lazy import of helpers defined in graph.py (avoids circular import).
    from app.domains.job_creation.graph import (  # noqa: E402
        _emit_fallback_telemetry,
        _emit_wizard_fallback_metric,
    )

    t0 = time.time()
    logger.info("[JobCreation:salary] Starting salary validation")

    # ── Fase 5: right_panel_form tem precedência (recrutador editou no painel) ──
    # Mesmo padrão canônico de intake_gate.py:215.
    _panel = state.get("right_panel_form") or {}
    _panel_salary_min = _panel.get("salary_min") or None
    _panel_salary_max = _panel.get("salary_max") or None
    # Suporta tanto salary_min/max avulsos quanto salary_range {min, max, currency}
    _panel_range = _panel.get("salary_range") or {}
    if isinstance(_panel_range, dict):
        _panel_salary_min = _panel_salary_min or (_panel_range.get("min") or None)
        _panel_salary_max = _panel_salary_max or (_panel_range.get("max") or None)
        if _panel_range.get("currency"):
            state = {**state, "salary_currency": _panel_range["currency"]}

    _salary_confirmed = False
    if _panel_salary_min:
        state = {
            **state,
            "salary_min": _panel_salary_min,
            "salary_max": _panel_salary_max,
            "salary_confirmed": True,
            "salary_provenance": "manual",
        }
        _salary_confirmed = True
        logger.info(
            "[JobCreation:salary] right_panel_form override: min=%s max=%s",
            _panel_salary_min, _panel_salary_max,
        )

    # ── Banda salarial da empresa tem precedência sobre o benchmark de mercado ──
    # Audit 2026-06-06: a faixa cadastrada em Configurações é POLÍTICA da empresa
    # (fonte verificada), não estimativa. Só resolve quando o recrutador ainda
    # não confirmou (right_panel_form vence) e não há faixa no state.
    salary_from_band = False
    if not _salary_confirmed and state.get("salary_min") is None:
        try:
            _band = _resolve_company_salary_band(state)
        except Exception as _band_exc:  # fail-open — cai no benchmark
            logger.warning(
                "[JobCreation:salary] company band resolve failed (fail-open): %s",
                _band_exc,
            )
            _band = None
        if _band and _band.get("min") is not None:
            state = {
                **state,
                "salary_min": _band.get("min"),
                "salary_max": _band.get("max"),
                "salary_currency": _band.get("currency") or "BRL",
                "salary_provenance": "company_salary_band",
            }
            salary_from_band = True
            logger.info(
                "[JobCreation:salary] filled from company salary band: min=%s max=%s",
                _band.get("min"), _band.get("max"),
            )

    # ── Fetch benchmark if not already in state ──
    # Task #1062: timeout determinístico (D4 da auditoria #1058). Em timeout
    # o nó pula benchmark gracefully (`salary_benchmark=None`) — recrutador
    # pode preencher manualmente sem travar o wizard.
    # Audit 2026-06-06: não busca mercado quando a banda da empresa já preencheu.
    _SALARY_TIMEOUT_S = float(__import__("os").environ.get(
        "LIA_SALARY_TIMEOUT_S", "45"
    ))
    # Task #1065 — flag de fallback (timeout do benchmark fetch ou
    # exception). Painel renderiza banner pedindo revisão manual da faixa.
    salary_used_fallback = False
    # Task #1067 — root-cause label propagado pro painel.
    salary_fallback_reason: Optional[str] = None
    if not state.get("salary_benchmark") and not salary_from_band:
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
                # Audit 2026-06-03 (P0): so ancora a faixa quando o benchmark e
                # VERIFICADO (busca real + confianca alta/media). Estimativa sem
                # fonte (is_estimate / confidence low/none) NAO vira faixa "de
                # fato" -- a LIA pede a faixa ao recrutador. Antes, qualquer
                # estimativa (incl. R$6-12k para diretoria) era anchorada.
                _bench_conf = (_benchmark.get("confidence") or "").lower()
                _bench_verified = (
                    not _benchmark.get("is_estimate", False)
                    and _bench_conf in ("high", "medium")
                )
                if (
                    state.get("salary_min") is None
                    and _benchmark.get("min") is not None
                    and _bench_verified
                ):
                    state = {
                        **state,
                        "salary_min": _benchmark.get("min"),
                        "salary_max": _benchmark.get("max"),
                        "salary_currency": _benchmark.get("currency", "BRL"),
                        "salary_provenance": "market_benchmark",
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
        "salary_confirmed": _salary_confirmed,
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
                # Audit 2026-06-06 — origem da faixa (company_salary_band |
                # market_benchmark | manual) p/ o painel rotular a proveniência.
                "salary_provenance": state.get("salary_provenance"),
                "benefits": state.get("benefits", []),
                "benchmark": state.get("salary_benchmark"),
                # Task #1065 — flag de fallback (timeout do benchmark fetch).
                # Painel renderiza banner pedindo revisão manual da faixa.
                "salary_confirmed": _salary_confirmed,
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
