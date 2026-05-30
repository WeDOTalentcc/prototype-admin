"""intake_gate_node — Frente 2 conversacional (2026-05-29).

Gate HITL antes do jd_enrichment: coleta campos faltantes, sugere faixa
salarial e pede permissão ao recrutador antes de avançar.

Dois sub-estados via ``langgraph.types.interrupt()`` (replay model):
  1. Campos obrigatórios ausentes → interrupt(ask_fields) → re-extrai no resume
  2. Campos presentes → interrupt(salary_suggestion + permissão) → classifica no resume

Quando ``intake_salary_suggested=True`` (self-loop após clarify), o WS detection
detecta a resposta fresca e classifica diretamente sem novo interrupt.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
# Module-level import so tests can mock: app.domains.job_creation.nodes.intake_gate._in_graph_runtime
from app.domains.job_creation.internal.utils import _in_graph_runtime
from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG

logger = logging.getLogger(__name__)

# ── Permission classifier (regex, zero-latency) ─────────────────────────────
_AFFIRMATIVE_RE = re.compile(
    r"\b(sim|ok|pode(?:\s+(?:criar|seguir|ir|avançar|avançar|comecar|começar))?|"
    r"vamos(?:\s+lá)?|beleza|perfeito|ótimo|certo|correto|"
    r"confirm(?:o|ado|ada)|segue?|avança?|é\s+isso|"
    r"tudo\s+(?:bem|certo|ok|bom)|vá\s+em\s+frente|"
    r"vai\s+(?:em\s+frente|lá)|positivo|exato|prossegue?|criar)\b",
    re.IGNORECASE | re.UNICODE,
)

_SALARY_TIMEOUT_S = 8.0


def _is_permission_granted(user_msg: str) -> bool:
    """True se a mensagem contém afirmação clara de permissão em PT-BR."""
    return bool(_AFFIRMATIVE_RE.search(user_msg.strip()))


_COMPACT_RE = re.compile(
    r"\b(compacto?|compact|7\s*q|7\s*perguntas?)\b",
    re.IGNORECASE | re.UNICODE,
)
_FULL_RE = re.compile(
    r"\b(completo?|completa|full|12\s*q|12\s*perguntas?)\b",
    re.IGNORECASE | re.UNICODE,
)


def _classify_mode_and_permission(user_msg: str) -> tuple:
    """Return (screening_mode, approved). Zero-latency regex classifier.

    screening_mode: "compact" | "full" | None
    approved: True if mode selected OR explicit permission word found
    """
    text = user_msg.strip()
    mode = None
    if _COMPACT_RE.search(text):
        mode = "compact"
    elif _FULL_RE.search(text):
        mode = "full"
    # Mode selection implies permission; explicit affirmatives also count
    approved = bool(mode) or _is_permission_granted(text)
    return mode, approved


def _get_missing(title: Optional[str], seniority: Optional[str], model: Optional[str]) -> List[str]:
    missing = []
    if not title:
        missing.append("título do cargo")
    if not seniority:
        missing.append("senioridade (júnior, pleno, sênior...)")
    if not model:
        missing.append("modelo de trabalho (remoto, presencial ou híbrido)")
    return missing


def _build_fields_question(title: Optional[str], missing: List[str]) -> str:
    joined = ", ".join(missing)
    if title:
        return msg("intake_gate.ask_fields_with_title", title=title, missing=joined)
    return msg("intake_gate.ask_fields", missing=joined)


def _reextract_fields(
    answer: str,
    current_title: Optional[str],
    current_seniority: Optional[str],
    current_model: Optional[str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Re-run IntakeExtractor sobre a resposta do recrutador. Fail-open."""
    try:
        from app.domains.job_creation.graph import get_intake_extractor
        extractor = get_intake_extractor()
        extraction = extractor.extract(answer)

        def _val(fn: str) -> Optional[str]:
            f = getattr(extraction, fn, None)
            if f is None:
                return None
            v = getattr(f, "value", None)
            return v if v not in (None, "", []) else None

        title = current_title or _val("title")
        seniority = current_seniority or _val("seniority")
        model = current_model or _val("work_model")
        return title, seniority, model
    except Exception as exc:
        logger.warning("[JobCreation:intake_gate] reextract failed (fail-open): %s", exc)
        return current_title, current_seniority, current_model


def _safe_fetch_salary(
    state: JobCreationState,
    title: Optional[str],
    seniority: Optional[str],
    model: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Fetch salary benchmark. Returns None on timeout/error (fail-open)."""
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    try:
        async def _fetch() -> Optional[Dict[str, Any]]:
            from app.domains.analytics.services.market_benchmark_service import MarketBenchmarkService
            svc = MarketBenchmarkService()
            return await svc.search_salary_benchmark(
                role=title or "",
                seniority=seniority or "",
                work_model=model or None,
                company_id=str(state.get("workspace_id") or state.get("company_id") or ""),
            )

        return run_coro_in_threadpool(_fetch, timeout=_SALARY_TIMEOUT_S)
    except Exception as exc:
        logger.warning("[JobCreation:intake_gate] salary fetch failed (fail-open): %s", exc)
        return None


def _build_permission_message(
    benchmark,
    title: Optional[str],
    seniority: Optional[str],
    model: Optional[str],
) -> str:
    """Build salary suggestion + mode selection + permission message."""
    title_str = title or "a vaga"
    seniority_str = seniority or ""
    model_str = model or ""
    compact_q = SCREENING_MODE_CONFIG["compact"]["total_questions"]
    compact_min = SCREENING_MODE_CONFIG["compact"]["estimated_minutes"]
    full_q = SCREENING_MODE_CONFIG["full"]["total_questions"]
    full_min = SCREENING_MODE_CONFIG["full"]["estimated_minutes"]

    if benchmark and benchmark.get("min") and benchmark.get("max"):
        sal_min = benchmark["min"]
        sal_max = benchmark["max"]

        def _fmt(v: float) -> str:
            return f"R$ {v:,.0f}".replace(",", ".")

        salary_part = msg(
            "intake_gate.salary_with_mode",
            title=title_str,
            seniority=seniority_str,
            model=model_str,
            min=_fmt(sal_min),
            max=_fmt(sal_max),
            compact_q=compact_q,
            compact_min=compact_min,
            full_q=full_q,
            full_min=full_min,
        )
    else:
        salary_part = msg(
            "intake_gate.salary_fallback_with_mode",
            title=title_str,
            seniority=seniority_str,
            compact_q=compact_q,
            compact_min=compact_min,
            full_q=full_q,
            full_min=full_min,
        )
    return salary_part


def _make_ws_response(
    state: JobCreationState,
    message: str,
    extra_updates: Optional[Dict[str, Any]] = None,
) -> JobCreationState:
    """Helper: return state with ws_stage_payload, requires_approval=True."""
    updates: Dict[str, Any] = {
        "current_stage": "intake",
        "requires_approval": True,
        "ws_stage_payload": build_ws_stage_payload(
            stage="intake",
            completeness=calculate_completeness("intake"),
            requires_approval=True,
            data={"message": message},
        ),
    }
    if extra_updates:
        updates.update(extra_updates)
    return {**state, **updates}


# ── Routing ──────────────────────────────────────────────────────────────────

def route_after_intake_gate(state: JobCreationState) -> str:
    """Roteia: intake_approved=True → jd_enrichment; caso contrário → END."""
    if state.get("intake_approved") is True:
        logger.info("[JobCreation:route] intake_gate -> jd_enrichment (approved)")
        return "jd_enrichment"
    logger.info("[JobCreation:route] intake_gate -> END (waiting for user)")
    return "end"


# ── Main node ────────────────────────────────────────────────────────────────

def intake_gate_node(state: JobCreationState) -> JobCreationState:
    """HITL #0 — gate conversacional antes do jd_enrichment.

    Sub-estado 1 (campos faltantes):
        interrupt(ask_fields) → re-extrai do resume → se ainda faltam → interrupt de novo.

    Sub-estado 2 (salário + permissão):
        _safe_fetch_salary → interrupt(permission) → classifica no resume.

    WS detection (defense layer para path graph.invoke sem Command(resume)):
        Quando intake_salary_suggested=True + fresh user_query, detecta resume
        sem interrupt(), classifica permissão diretamente (self-loop scenario).

    Mecanismo de replay do LangGraph:
        interrupt() em sub-estado 1 é replayed corretamente no 3º resume
        (retorna o campo anterior antes de processar a permissão final).
    """
    t0 = time.time()

    parsed_title = state.get("parsed_title")
    parsed_seniority = state.get("parsed_seniority")
    parsed_model = state.get("parsed_model")
    intake_salary_suggested = state.get("intake_salary_suggested")

    # ── WS detection (defense layer) ────────────────────────────────────────
    # Detecta resume para o sub-estado 2 (permissão) quando o path é
    # graph.invoke (não Command(resume)). Só ativa quando salary_suggested=True
    # (significa que voltamos via self-loop após clarify, não via interrupt replay).
    resume_msg = ""
    _uq = (state.get("user_query") or "").strip()
    _seen = (state.get("intake_gate_seen_user_query") or "").strip()
    _raw = (state.get("raw_input") or "").strip()
    _is_fresh = bool(_uq) and _uq != _seen
    _is_initial = bool(_raw) and _uq == _raw

    if (
        _is_fresh
        and not _is_initial
        and intake_salary_suggested
        and state.get("intake_approved") is not True
        and bool(parsed_title and parsed_seniority and parsed_model)
    ):
        resume_msg = _uq
        logger.info(
            "[JobCreation:intake_gate] WS resume detected (salary_suggested, fresh user_query=%s)",
            _uq[:40],
        )

    # ═══ Sub-estado 1: Campos obrigatórios ══════════════════════════════════
    if not (parsed_title and parsed_seniority and parsed_model):
        missing = _get_missing(parsed_title, parsed_seniority, parsed_model)
        ask_msg = _build_fields_question(parsed_title, missing)

        if _in_graph_runtime():
            from langgraph.types import interrupt  # type: ignore[import]

            _resume = interrupt({
                "type": "intake_fields",
                "stage": "intake",
                "data": {"message": ask_msg, "missing_fields": missing},
            })
            fields_answer = (str(_resume) if _resume is not None else "").strip()

            if fields_answer:
                parsed_title, parsed_seniority, parsed_model = _reextract_fields(
                    fields_answer, parsed_title, parsed_seniority, parsed_model,
                )
                logger.info(
                    "[JobCreation:intake_gate] post-fields-interrupt: title=%s seniority=%s model=%s",
                    parsed_title, parsed_seniority, parsed_model,
                )

            # Se ainda faltam campos após primeira extração, interrupt de novo
            if not (parsed_title and parsed_seniority and parsed_model):
                missing2 = _get_missing(parsed_title, parsed_seniority, parsed_model)
                ask_msg2 = _build_fields_question(parsed_title, missing2)
                interrupt({
                    "type": "intake_fields",
                    "stage": "intake",
                    "data": {"message": ask_msg2, "missing_fields": missing2},
                })
                # (replay: se interrupt de novo retornar, continua extração)
        else:
            # Non-runtime path (testes / action-based)
            return _make_ws_response(state, ask_msg, {
                "parsed_title": parsed_title,
                "parsed_seniority": parsed_seniority,
                "parsed_model": parsed_model,
                "intake_gate_seen_user_query": _uq,
            })

    # ═══ Sub-estado 2: Sugestão de salário + permissão ══════════════════════
    if not intake_salary_suggested:
        benchmark = _safe_fetch_salary(state, parsed_title, parsed_seniority, parsed_model)
        permission_msg = _build_permission_message(benchmark, parsed_title, parsed_seniority, parsed_model)

        if not resume_msg:
            if _in_graph_runtime():
                from langgraph.types import interrupt  # type: ignore[import]

                _resume = interrupt({
                    "type": "intake_permission",
                    "stage": "intake",
                    "data": {"message": permission_msg},
                })
                resume_msg = (str(_resume) if _resume is not None else "").strip()
            else:
                # Non-runtime: retorna com mensagem de permissão
                return _make_ws_response(state, permission_msg, {
                    "parsed_title": parsed_title,
                    "parsed_seniority": parsed_seniority,
                    "parsed_model": parsed_model,
                    "intake_salary_suggested": True,
                    "intake_gate_seen_user_query": _uq,
                })

    # ═══ Sub-estado 3: Classificar resposta de permissão ════════════════════
    if not resume_msg:
        # Sem mensagem para classificar (não deveria acontecer em runtime)
        logger.info("[JobCreation:intake_gate] no resume_msg — END (awaiting user)")
        return {
            **state,
            "parsed_title": parsed_title,
            "parsed_seniority": parsed_seniority,
            "parsed_model": parsed_model,
            "intake_salary_suggested": intake_salary_suggested,
            "intake_gate_seen_user_query": _uq,
            "current_stage": "intake",
            "requires_approval": True,
        }

    extracted_mode, confirmed = _classify_mode_and_permission(resume_msg)

    elapsed = (time.time() - t0) * 1000
    logger.info(
        "[JobCreation:intake_gate] permission=%s mode=%s msg=%s (%.0fms)",
        confirmed, extracted_mode, resume_msg[:40], elapsed,
    )

    base = {
        "parsed_title": parsed_title,
        "parsed_seniority": parsed_seniority,
        "parsed_model": parsed_model,
        "intake_salary_suggested": True,
        "intake_gate_seen_user_query": resume_msg,
        "current_stage": "intake",
    }
    if extracted_mode:
        base["screening_mode"] = extracted_mode

    if confirmed:
        if extracted_mode:
            mode_label = "Compacto" if extracted_mode == "compact" else "Completo"
            reply = msg("intake_gate.proceeding_with_mode", title=parsed_title or "a vaga", mode_label=mode_label)
        else:
            reply = msg("intake_gate.proceeding", title=parsed_title or "a vaga")
        return {
            **state,
            **base,
            "intake_approved": True,
            "requires_approval": False,
            "ws_stage_payload": build_ws_stage_payload(
                stage="intake",
                completeness=calculate_completeness("intake"),
                requires_approval=False,
                data={"message": reply},
            ),
        }

    # Não confirmado → clarifica e aguarda (self-loop via graph re-invoke)
    clarify = msg("intake_gate.off_topic_redirect")
    return {
        **state,
        **base,
        "intake_approved": None,
        "requires_approval": True,
        "ws_stage_payload": build_ws_stage_payload(
            stage="intake",
            completeness=calculate_completeness("intake"),
            requires_approval=True,
            data={"message": clarify},
        ),
    }
