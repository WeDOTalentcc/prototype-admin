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


# Campos que o recrutador pode fornecer no passo de permissao (provide_field_data).
# Whitelist defensiva — so estes sao ingeridos do extracted_data do LLM.
_PERMISSION_FIELD_KEYS = (
    "salary_min", "salary_max", "parsed_location", "parsed_employment_type",
    "parsed_manager_name", "parsed_manager_email", "parsed_department",
    "parsed_model",
)


def _classify_permission(state: JobCreationState, resume_msg: str):
    """Classifica a resposta de permissao via LLM gate classifier (canonical).

    Substitui o regex zero-latency (_classify_mode_and_permission) por
    entendimento de intencao — raiz do fluxo robotico (Paulo 2026-05-30):
    "acho que vamos trabalhar com salario" deixa de ser falso-approve.

    Fail-open: se o LLM falhar, cai no regex (zero-latency) preservando o
    comportamento atual para casos claros ("compacto", "pode").

    Returns (intent, extracted_mode, confirmed, field_updates, llm_reply).
    """
    try:
        from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool
        from app.domains.job_creation.services.wizard_gate_classifier import (
            get_wizard_gate_classifier,
        )

        classifier = get_wizard_gate_classifier()
        _cid = state.get("workspace_id") or state.get("company_id")
        _uid = state.get("user_id") or state.get("recruiter_id")

        # Task #1123 fix: últimas 6 msgs do histórico → últimas 3 turnos no
        # classificador (trunca a 300 chars por msg + 1200 total no classify).
        # Sem isso o LLM não sabe que título/gestor já foram fornecidos e gera
        # respostas do tipo "preciso de algumas infos básicas: qual o título?".
        _conv_msgs = state.get("conversation_messages") or []
        _last_turns: list[str] | None = [
            str(m.get("content", "")).strip()
            for m in _conv_msgs[-6:]
            if m.get("content")
        ] or None

        def _coro():
            return classifier.classify(
                user_message=resume_msg,
                stage="intake_permission",
                ws_stage_payload=state.get("ws_stage_payload"),
                tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
                hiring_policy_summary=str(state.get("hiring_policy_summary") or ""),
                company_id=str(_cid) if _cid else None,
                user_id=str(_uid) if _uid else None,
                last_turns=_last_turns,
            )

        out = run_coro_in_threadpool(_coro, timeout=30.0)
        intent = out.intent
        conf = out.confidence or 0.0
        extracted = out.extracted_data if isinstance(out.extracted_data, dict) else {}
        reply = out.conversational_reply or ""

        # Confidence floor — re-pergunta sem aprovar nem mutar (igual jd_gate).
        if conf < 0.7:
            return ("ask_question", None, False, {}, reply)

        if intent == "approve":
            return ("approve", None, True, {}, reply)
        if intent == "select_compact":
            return ("select_compact", "compact", True, {}, reply)
        if intent == "select_full":
            return ("select_full", "full", True, {}, reply)
        if intent == "provide_field_data":
            field_updates = {}
            for k in _PERMISSION_FIELD_KEYS:
                v = extracted.get(k)
                if v not in (None, "", []):
                    field_updates[k] = v
            # Salario unico: espelha min em max quando so um veio.
            if "salary_min" in field_updates and "salary_max" not in field_updates:
                field_updates["salary_max"] = field_updates["salary_min"]
            return ("provide_field_data", None, False, field_updates, reply)
        # ask_question / off_topic → re-pergunta, nao aprova.
        return (intent, None, False, {}, reply)
    except Exception as exc:  # noqa: BLE001 — fail-open para regex
        logger.warning(
            "[JobCreation:intake_gate] LLM permission classify falhou "
            "(fallback regex): %s", exc,
        )
        mode, confirmed = _classify_mode_and_permission(resume_msg)
        return (
            "approve" if confirmed else "off_topic",
            mode, confirmed, {}, "",
        )


# ---------------------------------------------------------------------------
# Sub-estado 1.5 helpers -- criacao de departamento inline (2026-06-18)
# ---------------------------------------------------------------------------

def _build_dept_creation_message(
    dept_candidate: str,
    existing_departments=None,
) -> str:
    """Monta mensagem propondo criacao do departamento nao encontrado."""
    lines = [
        "O departamento **{}** nao esta cadastrado na sua empresa.".format(dept_candidate),
        "",
        "Posso cria-lo agora. Confirme o nome e informe o que souber:",
        "* **Codigo** (ex: RH, TI, MKT) -- opcional",
        "* **Descricao** -- o que este departamento faz",
        "* **Localizacao** -- qual escritorio",
        "* **Headcount** -- quantas pessoas hoje",
        "* **Centro de custo** -- codigo financeiro",
        "* **Prioridade de contratacao** -- normal / alta / critica",
        "",
        "_O gestor informado nesta vaga sera vinculado automaticamente ao departamento._",
        "",
    ]
    if existing_departments:
        depts_str = ", ".join(list(existing_departments)[:8])
        lines.append("Ou escolha um dos departamentos cadastrados: {}".format(depts_str))
        lines.append("")
    lines.append(
        'Responda "sim" (+ campos opcionais) para criar **{}**, '
        "ou informe o nome de um departamento existente.".format(dept_candidate)
    )
    return "\n".join(lines)


def _execute_dept_creation_sync(dept_candidate, parsed, state):
    """Executa criacao de departamento via SyncSessionLocal (psycopg2 pool).

    P0 fix event-loop (2026-06-24): run_coro_in_threadpool + AsyncSessionLocal
    sempre falhava com "Future attached to a different loop". O except setava
    department_creation_done=True sem criar — dado fantasma.
    Fix (a): except NAO seta done=True (fail-loud, state reflete verdade).
    Fix (b): SyncSessionLocal com pool psycopg2 (sem conflito de event loop).
    """
    from lia_config.database import SyncSessionLocal
    from sqlalchemy import text as sa_text
    import uuid as _uuid

    company_id = str(state.get("company_id") or state.get("workspace_id") or "")
    if not company_id:
        logger.warning("[DeptCreation] company_id not in state -- skip creation")
        return {"department_creation_done": False, "dept_creation_error": "company_id ausente"}
    manager_name = state.get("parsed_manager_name")
    manager_email = state.get("parsed_manager_email")

    try:
        with SyncSessionLocal() as db:
            db.execute(
                sa_text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": company_id},
            )
            dept_id = str(_uuid.uuid4())
            dept_name = (parsed.get("name") or dept_candidate).strip()

            cols = {
                "id": dept_id,
                "company_id": company_id,
                "name": dept_name,
                "is_active": True,
            }
            if parsed.get("code"):
                cols["code"] = parsed["code"].strip().upper()
            if parsed.get("description"):
                cols["description"] = parsed["description"].strip()
            if parsed.get("location"):
                cols["location"] = parsed["location"].strip()
            if parsed.get("headcount"):
                cols["headcount"] = int(parsed["headcount"])
            if parsed.get("cost_center"):
                cols["cost_center"] = parsed["cost_center"].strip()
            hp = (parsed.get("hiring_priority") or "normal").lower().strip()
            if hp not in ("normal", "alta", "critica", "urgente"):
                hp = "normal"
            if hp != "normal":
                cols["hiring_priority"] = hp
            if manager_name:
                cols["manager_name"] = manager_name.strip()
            if manager_email:
                cols["manager_email"] = manager_email.strip()

            col_names = ", ".join(cols.keys())
            col_params = ", ".join(f":{k}" for k in cols.keys())
            db.execute(
                sa_text(f"INSERT INTO departments ({col_names}) VALUES ({col_params})"),
                cols,
            )
            db.commit()

        logger.info("[DeptCreation] created dept=%s id=%s company=%s", dept_name, dept_id, company_id)
        mgr_msg = ""
        if manager_name:
            mgr_msg = " Gestor **{}** vinculado.".format(manager_name)
        return {
            "parsed_department": dept_name,
            "department_created_id": dept_id,
            "department_creation_done": True,
            "dept_creation_confirmation_msg": (
                "Departamento **{}** criado com sucesso!{} "
                "Continuando a criacao da vaga...".format(dept_name, mgr_msg)
            ),
        }
    except Exception as exc:
        logger.error("[DeptCreation] DB write failed (fail-loud): %s", exc, exc_info=True)
        return {
            "department_creation_done": False,
            "dept_creation_error": str(exc)[:200],
        }


def _handle_department_creation_subflow(state, dept_candidate, _uq, _is_fresh, _is_initial):
    """Sub-estado 1.5: propoe criar dept nao encontrado, aguarda confirmacao.

    Returns dict of state updates, or None (interrupt emitted in runtime -- next
    invocation will have _is_fresh_dept=True with the recruiter response).
    """
    from app.domains.job_creation.services.department_wizard_service import (
        parse_dept_creation_response,
    )

    existing_depts = list(state.get("existing_departments") or [])
    _dept_seen = state.get("intake_gate_seen_user_query") or ""
    _is_fresh_dept = bool(_uq) and _uq != _dept_seen and not _is_initial

    if _is_fresh_dept and not (state.get("intake_salary_suggested") or state.get("intake_approved")):
        parsed = parse_dept_creation_response(_uq, dept_candidate)

        if parsed["confirmed"]:
            return _execute_dept_creation_sync(dept_candidate, parsed, state)

        elif parsed.get("chosen_existing"):
            chosen = parsed["chosen_existing"]
            return {
                "parsed_department": chosen,
                "department_creation_done": True,
                "dept_creation_confirmation_msg": "Departamento **{}** selecionado. Continuando...".format(chosen),
            }

    # Primeira vez (ou resposta ambigua): emite prompt
    dept_msg = _build_dept_creation_message(dept_candidate, existing_depts)

    if _in_graph_runtime():
        from langgraph.types import interrupt  # type: ignore[import]
        interrupt({
            "type": "department_creation",
            "stage": "intake",
            "data": {
                "message": dept_msg,
                "dept_candidate": dept_candidate,
                "existing_departments": existing_depts,
            },
        })
        return None
    else:
        return {"dept_creation_prompt_sent": True, "dept_creation_message": dept_msg}


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
) -> Optional[Dict[str, Any]]:
    """Fetch salary benchmark. Returns None on timeout/error (fail-open).

    Usa a assinatura canônica de MarketBenchmarkService.search_salary_benchmark
    (role, seniority, location) — mesma usada por salary.py, jd_enrichment_service,
    compensation_analysis e os demais consumidores. location vem de parsed_location
    (mercado nacional quando ausente). Salário de mercado é dado PÚBLICO, não
    tenant-scoped, então company_id não participa (o produtor não o usa).
    """
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    location = state.get("parsed_location") or None

    try:
        async def _fetch() -> Optional[Dict[str, Any]]:
            from app.domains.analytics.services.market_benchmark_service import MarketBenchmarkService
            svc = MarketBenchmarkService()
            return await svc.search_salary_benchmark(
                role=title or "",
                seniority=seniority or "",
                location=location,
            )

        return run_coro_in_threadpool(_fetch, timeout=_SALARY_TIMEOUT_S)
    except Exception as exc:
        logger.warning("[JobCreation:intake_gate] salary fetch failed (fail-open): %s", exc)
        return None


_COMPETENCY_TIMEOUT_S = 12.0


def _suggest_competencies_safe(
    title: Optional[str],
    seniority: Optional[str],
    department: Optional[str],
    screening_mode: str,
    company_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Sugere competencias via CompetencyBenchmarkService (Fase 2). Fail-open.

    Dimensionado pelo modo. company_id do contexto (multi-tenancy). Retorna None
    em timeout/erro -- a aprovacao NUNCA e bloqueada por falha na sugestao.
    """
    from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

    try:
        async def _fetch() -> Optional[Dict[str, Any]]:
            from app.domains.analytics.services.competency_benchmark_service import (
                get_competency_benchmark_service,
            )
            svc = get_competency_benchmark_service()
            return await svc.suggest_competencies(
                title=title or "",
                seniority=seniority,
                department=department,
                screening_mode=screening_mode,
                company_id=company_id,
            )

        return run_coro_in_threadpool(_fetch, timeout=_COMPETENCY_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 -- fail-open (nao bloqueia aprovacao)
        logger.warning(
            "[JobCreation:intake_gate] competency suggestion failed (fail-open): %s", exc,
        )
        return None


def _resolve_confirmed_competencies(
    state: JobCreationState,
    title: Optional[str],
    seniority: Optional[str],
    screening_mode: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Resolve competencias confirmadas para o estado de aprovacao.

    Precedencia:
      1. Edicoes do recruiter via right_panel_form (recognition > recall) -- vencem.
      2. Sugestao do CompetencyBenchmarkService (accept-all default).
      3. Fail-open: listas vazias se servico indisponivel (jd_enrichment Fase 4
         cai no comportamento legado de gerar competencias).

    Retorna (confirmed_technical, confirmed_behavioral, suggestion_payload).
    suggestion_payload vai ao ws_stage_payload.data.suggestions_data.competencies
    para o painel renderizar como chips editaveis (Fase 5).
    """
    panel = state.get("right_panel_form") or {}
    panel_tech = panel.get("confirmed_technical_competencies")
    panel_behav = panel.get("confirmed_behavioral_competencies")

    # 1) Painel tem precedencia quando o recruiter editou.
    if panel_tech is not None or panel_behav is not None:
        return (
            list(panel_tech or []),
            list(panel_behav or []),
            None,
        )

    # 2) Sugestao dimensionada pelo modo.
    suggestion = _suggest_competencies_safe(
        title=title,
        seniority=seniority,
        department=state.get("parsed_department"),
        screening_mode=screening_mode,
        company_id=str(state.get("workspace_id") or state.get("company_id") or "") or None,
    )
    if not suggestion:
        return [], [], None

    technical = list(suggestion.get("technical") or [])
    behavioral = list(suggestion.get("behavioral") or [])
    return technical, behavioral, {"technical": technical, "behavioral": behavioral}


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

        # Audit 2026-06-03: proveniência honesta na frase do salário. Quando o
        # benchmark é estimativa não-verificada (sem busca real → is_estimate),
        # NÃO afirmar "o mercado pratica" — rotular como estimativa de referência.
        _sal_msg_key = (
            "intake_gate.salary_estimate_with_mode"
            if benchmark.get("is_estimate")
            else "intake_gate.salary_with_mode"
        )
        salary_part = msg(
            _sal_msg_key,
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


def _ficha_data(
    state: JobCreationState,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Delegate to canonical helper (Fase 8 A1)."""
    from app.domains.job_creation.helpers.ficha_builder import build_ficha_data
    return build_ficha_data(state, message, extra)


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
            data=_ficha_data(state, message),
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

    # ═══ Sub-estado 1.5: Departamento não encontrado — criar inline ═══════════
    dept_candidate = state.get("department_candidate_from_title")
    dept_creation_done = state.get("department_creation_done", False)
    if (
        state.get("parsed_department") is None
        and dept_candidate
        and not dept_creation_done
    ):
        _dept_result = _handle_department_creation_subflow(
            state, dept_candidate, _uq, _is_fresh, _is_initial,
        )
        if _dept_result is not None:
            # Sub-fluxo retornou: pode ser interrupt (runtime) ou dict de updates.
            # Se dict, merge e continua; se None, sub-fluxo emitiu interrupt (runtime).
            state = {**state, **_dept_result}
            parsed_department = state.get("parsed_department")

    # ═══ Sub-estado 2: Sugestão de salário + permissão ══════════════════════
    if not intake_salary_suggested:
        benchmark = _safe_fetch_salary(state, parsed_title, parsed_seniority)
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

    intent, extracted_mode, confirmed, field_updates, llm_reply = _classify_permission(
        state, resume_msg,
    )

    elapsed = (time.time() - t0) * 1000
    logger.info(
        "[JobCreation:intake_gate] intent=%s mode=%s confirmed=%s fields=%s "
        "msg=%s (%.0fms)",
        intent, extracted_mode, confirmed, sorted(field_updates.keys()),
        resume_msg[:40], elapsed,
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
    # provide_field_data — ingere o dado fornecido (salario, localizacao,
    # gestor, contrato...) no state. NUNCA aprova so porque a frase tinha
    # "vamos". Re-pergunta o modo/permissao com o dado confirmado.
    if field_updates:
        base.update(field_updates)

    if confirmed:
        if extracted_mode:
            mode_label = "Compacto" if extracted_mode == "compact" else "Completo"
            reply = msg("intake_gate.proceeding_with_mode", title=parsed_title or "a vaga", mode_label=mode_label)
        else:
            reply = msg("intake_gate.proceeding", title=parsed_title or "a vaga")

        # -- Fase 3: confirmacao assistida de competencias (nao-bloqueante) --
        # Dimensiona pelo modo escolhido; default compact quando ausente
        # (competency_gate decide o modo final no path sem escolha no intake).
        eff_mode = base.get("screening_mode") or state.get("screening_mode") or "compact"
        conf_tech, conf_behav, comp_payload = _resolve_confirmed_competencies(
            state, parsed_title, parsed_seniority, eff_mode,
        )

        # Problema #2 fix: mostrar competencias que serao usadas na JD
        # para que o recrutador possa reagir (nao e um gate bloqueante —
        # o recrutador pode pedir ajuste no jd_gate ou no competency_gate).
        if conf_tech or conf_behav:
            _tech_names = [
                (c.get("skill") or c.get("name") or str(c))
                for c in (conf_tech or [])[:5]
            ]
            _behav_names = [
                (c.get("competencia") or c.get("name") or str(c))
                for c in (conf_behav or [])[:4]
            ]
            _comp_lines: list[str] = []
            if _tech_names:
                _comp_lines.append("🔧 **Técnicas:** " + ", ".join(_tech_names) + ("..." if len(conf_tech) > 5 else ""))
            if _behav_names:
                _comp_lines.append("💡 **Comportamentais:** " + ", ".join(_behav_names) + ("..." if len(conf_behav) > 4 else ""))
            if _comp_lines:
                reply = reply.rstrip() + (
                    "\n\nUsarei estas competências para a vaga — você pode ajustar no painel lateral ou me dizer se quer mudar algo após ver a descrição:\n"
                    + "\n".join(_comp_lines)
                )

        _appr_extra: Dict[str, Any] = {
            "screening_mode": base.get("screening_mode") or eff_mode,
            "confirmed_technical_competencies": conf_tech,
            "confirmed_behavioral_competencies": conf_behav,
        }
        if comp_payload:
            _appr_extra["suggestions_data"] = {"competencies": comp_payload}
        data = _ficha_data({**state, **base}, reply, _appr_extra)

        return {
            **state,
            **base,
            "intake_approved": True,
            "requires_approval": False,
            "intake_competencies_suggested": True,
            "confirmed_technical_competencies": conf_tech,
            "confirmed_behavioral_competencies": conf_behav,
            "ws_stage_payload": build_ws_stage_payload(
                stage="intake",
                completeness=calculate_completeness("intake"),
                requires_approval=False,
                data=data,
            ),
        }

    # Nao confirmado (provide_field_data / ask_question / off_topic) →
    # usa a resposta do LLM (confirma o dado + re-pergunta o modo) e aguarda.
    # field_updates ja foram mergeados em base → o painel reflete o novo dado.
    clarify = llm_reply or msg("intake_gate.off_topic_redirect")
    return {
        **state,
        **base,
        "intake_approved": None,
        "requires_approval": True,
        "ws_stage_payload": build_ws_stage_payload(
            stage="intake",
            completeness=calculate_completeness("intake"),
            requires_approval=True,
            data=_ficha_data({**state, **base}, clarify),
        ),
    }
