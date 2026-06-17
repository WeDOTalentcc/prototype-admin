"""utils canonical — PR-17 step 2 extract (2026-05-26 ONDA 3 follow-up).

Helpers genéricos do wizard movidos de graph.py:
- _extract_last_turns: extrai últimas N turns de conversation_messages
- _min_jd_quality_threshold: env-configurable JD quality gate
- _try_meta_helper: sync wrapper para wizard_meta_question_helper
- _in_graph_runtime: detecta execução em LangGraph Pregel runtime
- _llm_gates_enabled: feature flag LIA_WIZARD_LLM_GATES
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _extract_last_turns(state: Any, n: int = 3) -> list[str]:
    """Task #1123 — extrai últimas N turns de ``state['conversation_messages']``.

    Formato canônico: ``[{"role": "user"|"assistant", "content": "..."}, ...]``.
    Devolve lista de strings ``"<role>: <content>"`` para alimentar prompts dos
    classifiers e do meta-question helper. Tail bounded (default 3 turnos);
    content truncado a 300 chars por turno. Fail-open: state malformado
    devolve lista vazia (caller trata como "sem histórico").
    """
    try:
        msgs = state.get("conversation_messages") or []
    except Exception:
        return []
    out: list[str] = []
    for m in list(msgs)[-(n * 2):]:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip().lower() or "msg"
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        out.append(f"{role}: {content[:300]}")
    return out[-n:]


def _min_jd_quality_threshold() -> float:
    """Min JD quality score (0-100) required to advance past jd_gate to bigfive.

    Configurable via ``LIA_WIZARD_MIN_JD_QUALITY`` env var. Default 30
    (production threshold — vagas with quality < 30 force the recruiter
    to rewrite). In dev environments where the LLM enrichment proxy
    fails (e.g. Replit modelfarm Gemini endpoint not supported), every
    enrichment hits the deterministic fallback (score=20.0). Set this
    env var to ``0`` in dev to allow the wizard to advance past the
    fallback enrichment for testing. See harness fix 2026-05-19
    (Bug C — wizard stuck at jd_gate after 'Recebi a descrição').
    """
    raw = os.environ.get("LIA_WIZARD_MIN_JD_QUALITY", "30").strip()
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 30.0


def _build_wizard_state_summary(state: Any) -> str:
    """Constrói resumo legível do estado atual do wizard para injetar no meta-helper.

    O bot fica "burro" pós-JD porque recebe só stage_description (1 frase estática).
    Este resumo dá ao LLM a ficha viva: o que foi preenchido, o que falta, status JD,
    competências, modo de triagem — para responder "o que falta?" ou perguntas
    contextuais com precisão.
    """
    lines: list[str] = []

    stage = state.get("current_stage") or "desconhecido"
    lines.append(f"Stage atual: {stage}")

    field_map = {
        "nome do recrutador": state.get("parsed_recruiter_name"),
        "título do cargo": state.get("parsed_title"),
        "senioridade": state.get("parsed_seniority"),
        "modelo de trabalho": state.get("parsed_model"),
        "departamento": state.get("parsed_department"),
        "localização": state.get("parsed_location"),
        "tipo de contrato": state.get("parsed_employment_type"),
        "gestor responsável": state.get("parsed_manager_name"),
    }
    filled = [k for k, v in field_map.items() if v]
    missing = [k for k, v in field_map.items() if not v]
    if filled:
        lines.append("Campos preenchidos: " + ", ".join(
            f"{k}={field_map[k]!r}" for k in filled
        ))
    # Email do gestor: NUNCA expor o valor ao LLM (LGPD — capturado
    # deterministicamente no servidor). Mostrar apenas presença/ausência.
    if state.get("parsed_manager_email"):
        lines.append("Email do gestor: registrado (capturado automaticamente)")
    else:
        missing.append("email do gestor")
    if missing:
        lines.append("Campos ainda faltantes: " + ", ".join(missing))

    jd_enriched = state.get("jd_enriched")
    jd_score = state.get("jd_quality_score")
    jd_approved = state.get("jd_approved")
    if jd_enriched:
        score_str = f", qualidade={jd_score:.0f}/100" if jd_score is not None else ""
        approved_str = " (aprovada pelo recrutador)" if jd_approved else " (aguardando aprovação do recrutador)"
        lines.append(f"JD enriquecida: Sim{score_str}{approved_str}")
    else:
        lines.append("JD enriquecida: Não (ainda não gerada)")

    tech = state.get("confirmed_technical_competencies") or []
    behav = state.get("confirmed_behavioral_competencies") or []
    def _names(items):
        out = []
        for it in items:
            if isinstance(it, dict):
                n = it.get("skill") or it.get("competencia") or it.get("name")
            else:
                n = str(it)
            if n:
                out.append(str(n))
        return out
    if tech or behav:
        # Listar NOMES (não só contagem) para o LLM conseguir ADICIONAR/REMOVER
        # competências: ao pedir adicione X, ele reconstrói a lista atual + X
        # e chama confirm_competencies com o conjunto completo (semântica replace).
        _tn = _names(tech); _bn = _names(behav)
        lines.append(
            f"Competências técnicas confirmadas ({len(_tn)}): "
            + (", ".join(_tn) if _tn else "(nenhuma)")
        )
        lines.append(
            f"Competências comportamentais confirmadas ({len(_bn)}): "
            + (", ".join(_bn) if _bn else "(nenhuma)")
        )
    else:
        lines.append("Competências confirmadas: nenhuma ainda (aguardando confirmação)")

    _resp = state.get("confirmed_responsibilities") or []
    if _resp:
        lines.append(f"Responsabilidades confirmadas ({len(_resp)}): " + "; ".join(str(r) for r in _resp))
    else:
        lines.append("Responsabilidades confirmadas: nenhuma (opcional — o JD gera se não informadas)")

    _langs = state.get("confirmed_languages") or []
    if _langs:
        _ln = []
        for _l in _langs:
            _name = _l.get("language", "") if isinstance(_l, dict) else str(_l)
            _lvl = _l.get("level", "") if isinstance(_l, dict) else ""
            if _name:
                _ln.append(_name + (" (" + _lvl + ")" if _lvl else ""))
        if _ln:
            lines.append("Idiomas exigidos: " + ", ".join(_ln))



    mode = state.get("screening_mode")
    if mode:
        label = "Compacto (7 perguntas)" if mode == "compact" else "Completo (12 perguntas)"
        lines.append(f"Modo de triagem WSI escolhido: {label}")
    else:
        lines.append("Modo de triagem WSI: não escolhido ainda")

    sal_min = state.get("salary_min")
    sal_max = state.get("salary_max")
    if sal_min or sal_max:
        lines.append(f"Faixa salarial: R$ {sal_min or '?'} – R$ {sal_max or '?'}")

    return "\n".join(lines)


def _try_meta_helper(
    *,
    state: Any,
    stage: str,
    user_message: str,
    stage_description: str,
) -> str | None:
    """Task #1123 — wrapper sync para ``wizard_meta_question_helper``.

    Captura qualquer exceção (incluindo ``ImportError`` em testes offline
    onde o módulo não está presente) e devolve ``None`` — caller cai no
    ``output.conversational_reply`` do classifier. Mantém o gate
    determinístico do ponto de vista de fluxo (helper só altera o TEXTO
    da resposta, não o roteamento).
    """
    try:
        from app.domains.job_creation.services.wizard_meta_question_helper import (
            generate_meta_response_sync,
        )
        wizard_state_summary = _build_wizard_state_summary(state)
        return generate_meta_response_sync(
            stage=stage,
            user_message=user_message,
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            last_turns=_extract_last_turns(state, n=3),
            stage_description=stage_description,
            wizard_state_summary=wizard_state_summary,
        )
    except Exception as _exc:
        logger.info("[JobCreation:meta_helper] failed (fail-open): %s", _exc)
        return None


def _in_graph_runtime() -> bool:
    """True iff currently executing inside a LangGraph node (Pregel runtime).

    Task #1094 — used by gate_nodes to guard ``langgraph.types.interrupt()``
    calls so they remain test-safe when the gate function is invoked as a
    plain Python callable (offline sentinels: T2/T4/T5/T6) rather than via
    ``graph.invoke()``. In runtime, ``get_config()`` returns the active
    Pregel config; outside runtime it raises (RuntimeError or LookupError
    depending on the langgraph version). Either way we report False and the
    gate falls back to the legacy END no-op semantics.
    """
    try:
        from langgraph.config import get_config
        get_config()
        return True
    except Exception:
        return False


def _llm_gates_enabled() -> bool:
    """Task #1085 (T2) — feature flag ``LIA_WIZARD_LLM_GATES``.

    Task #1130 (GA) — flag agora **ON por default em TODOS os ambientes**
    (dev, staging, prod). Os 3 gates restantes (competency #1086, wsi
    #1087, review #1088) foram migrados para o classifier LLM e ficaram
    estáveis. O caminho legado ``route_after_jd`` keyword-based segue
    disponível só para rollback emergencial via ``LIA_WIZARD_LLM_GATES=0``.

    Lido a cada chamada ao builder para que testes possam alternar o flag
    via ``monkeypatch.setenv`` sem reset do módulo.

    REMOVE: 2026-09-01 — após 30 dias de baseline pós-GA sem regressão,
    deletar ``route_after_jd``/``route_after_competency``/``route_after_wsi``/
    ``route_after_review`` keyword-based do ``domain.py`` e remover o
    short-circuit "OFF" desta função (a flag deixa de existir, gates LLM
    viram caminho único).
    """
    raw = os.environ.get("LIA_WIZARD_LLM_GATES", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    # Task #1130 — default ON em TODOS os ambientes. Mantemos a leitura de
    # ``LIA_ENV``/``APP_ENV``/``ENVIRONMENT`` no histórico para que
    # operadores possam reconhecer o callsite, mas a inferência por
    # ambiente foi APOSENTADA (toda ramificação caía em True após GA).
    return True
