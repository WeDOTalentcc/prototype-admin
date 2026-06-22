"""
view_context — formata o ESTADO DA TELA atual num bloco de prompt para o chat
global da LIA (P0.1 consciencia de estado da tela, 2026-06-03).

Régua Apollo: o chat abre ciente do conjunto de trabalho do recrutador
("voce tem 88.778 contatos na busca atual"). Aqui transformamos o view_context
enviado pelo frontend (page_type + counts + filtros + ids visiveis) num bloco
PT-BR que o agente global (recruiter_copilot) injeta no system prompt.

Funcao PURA e deterministica (computacional) — testavel sem instanciar o agente.
REGRA 4: retorna "" quando nao ha contexto util; nunca inventa estado.

Sensor: tests/contract/test_view_context_awareness.py
"""
from __future__ import annotations

from typing import Any

_PAGE_LABELS = {
    "vagas": "Vagas",
    "jobs": "Vagas",
    "funil": "Funil de Talentos",
    "candidatos": "Funil de Talentos",
    "talent": "Funil de Talentos",
    "kanban": "Kanban",
    "pipeline": "Kanban",
    "configuracoes": "Configurações",
    "settings": "Configurações",
    "indicadores": "Indicadores",
    "analytics": "Indicadores",
    "painel": "Painel de Controle",
    "dashboard": "Painel de Controle",
}

_COUNT_LABELS = {
    "total": "no total",
    "ativas": "ativas",
    "ativos": "ativos",
    "urgentes": "urgentes",
    "em_risco": "em risco",
    "concluidas": "concluídas",
    "entrevistas": "entrevistas",
    "pausadas": "pausadas",
}


def _label_page(page_type: Any) -> str:
    if not page_type:
        return ""
    slug = str(page_type).strip().lower()
    return _PAGE_LABELS.get(slug, str(page_type))


def _format_counts(counts: dict[str, Any]) -> str:
    parts: list[str] = []
    for k, v in counts.items():
        if v is None:
            continue
        label = _COUNT_LABELS.get(str(k).strip().lower(), str(k))
        parts.append(f"{v} {label}")
    return ", ".join(parts)


def format_view_context(view_context: dict[str, Any] | None) -> str:
    """Formata o estado-da-tela atual num bloco de prompt PT-BR.

    Retorna "" se view_context for None/vazio/sem conteudo util — REGRA 4
    anti-silent-fallback: nao inventar contexto que nao existe.
    """
    if not view_context or not isinstance(view_context, dict):
        return ""

    lines: list[str] = []

    page_label = _label_page(view_context.get("page_type", ""))
    if page_label:
        lines.append(f"- Tela: {page_label}")

    job_ref = view_context.get("job_title") or view_context.get("job_id") or view_context.get("job_vacancy_id")
    if job_ref:
        lines.append(f"- Vaga atual: {job_ref}")

    counts = view_context.get("counts")
    if isinstance(counts, dict) and counts:
        counts_str = _format_counts(counts)
        if counts_str:
            lines.append(f"- Contagens nesta visão: {counts_str}")

    filters = view_context.get("active_filters")
    if isinstance(filters, (list, tuple)) and filters:
        lines.append(
            "- Filtros ativos: " + ", ".join(str(f) for f in filters)
        )

    visible_ids = view_context.get("visible_ids")
    if isinstance(visible_ids, (list, tuple)) and visible_ids:
        sample = ", ".join(str(i) for i in list(visible_ids)[:5])
        lines.append(f"- Itens visíveis: {len(visible_ids)} (ex.: {sample})")

    # Fase 5 (2026-06-10): candidato/vaga em foco (origem: entityContext do FE)
    entity_focus = view_context.get("entity_focus")
    if isinstance(entity_focus, dict) and entity_focus.get("id"):
        _etype = entity_focus.get("type", "candidate")
        _label = entity_focus.get("label") or entity_focus.get("id", "")
        _id_str = entity_focus["id"]
        _focus_mode = entity_focus.get("mode", "active")  # [Fix P1 focus-mode]
        if _etype == "candidate":
            lines.append(f"- Candidato em foco: {_label} (ID: {_id_str})")
        elif _focus_mode == "background":
            # Vaga disponível como contexto — usuário não está navegando nela agora
            lines.append(
                f"- Vaga disponível como contexto (usuário não está navegando nela agora): "
                f"{_label} (ID: {_id_str})"
            )
        else:
            # active ou qualquer outro valor — comportamento original
            lines.append(f"- Vaga em foco: {_label} (ID: {_id_str})")

    # GAP-02-001: pagination awareness — agent knows which page recruiter is on
    pagination = view_context.get("pagination_state")
    if isinstance(pagination, dict):
        cur = pagination.get("current_page")
        total_p = pagination.get("total_pages")
        page_sz = pagination.get("page_size")
        total_i = pagination.get("total_items")
        if cur is not None and total_p is not None:
            pag_parts = [f"página {cur} de {total_p}"]
            if page_sz is not None:
                pag_parts.append(f"{page_sz} itens/pág")
            if total_i is not None:
                pag_parts.append(f"{total_i} total")
            lines.append("- Paginação: " + ", ".join(pag_parts))

    # GAP-02-001: modal awareness — agent knows which modal is open
    active_modal = view_context.get("active_modal")
    if isinstance(active_modal, str) and active_modal:
        lines.append(f"- Modal aberto: {active_modal}")

    if not lines:
        return ""

    header = (
        "Estado da tela atual (o recrutador está olhando para esta visão AGORA "
        "— use como contexto; se ele disser 'resuma/refine/liste isso', refere-se "
        "a esta visão):"
    )
    return header + "\n" + "\n".join(lines)


def view_context_from_context(ctx: dict | None) -> dict | None:
    """Deriva um view_context a partir do context bruto do agente.

    Prefere ctx['view_context'] (rico, quando o FE enviar). Se ausente,
    SINTETIZA a partir dos sinais que o FE JA envia hoje (getPageContext em
    useChatMessages.ts): page_type, job_vacancy_id, candidate_id. Assim o
    chat global ja abre ciente da tela SEM exigir mudanca de frontend.
    Retorna None se nao houver nenhum sinal (REGRA 4: nao inventa).
    """
    if not ctx or not isinstance(ctx, dict):
        return None
    explicit = ctx.get("view_context")
    if isinstance(explicit, dict) and explicit:
        return explicit
    synth: dict = {}
    if ctx.get("page_type"):
        synth["page_type"] = ctx["page_type"]
    visible: list[str] = []
    if ctx.get("job_vacancy_id"):
        visible.append(str(ctx["job_vacancy_id"]))
    if ctx.get("candidate_id"):
        visible.append(str(ctx["candidate_id"]))
    if visible:
        synth["visible_ids"] = visible
    # Fase 5 (2026-06-10): synthesize entity_focus from context.metadata.entity_ids
    # (injected by lia-float-context.tsx when user clicks hover LIA button)
    meta_entity_ids = (ctx.get("metadata") or {}).get("entity_ids")
    if isinstance(meta_entity_ids, dict):
        _eid = meta_entity_ids.get("candidate_id") or meta_entity_ids.get("job_id") or meta_entity_ids.get("entity_id")
        if _eid and "entity_focus" not in synth:
            synth["entity_focus"] = {
                "type": meta_entity_ids.get("entity_type", "candidate"),
                "id": str(_eid),
                "label": meta_entity_ids.get("entity_label", ""),
            }
    return synth or None


def effective_domain_for_scope(context: dict | None, resolved_domain: str | None) -> str | None:
    """Prefere metadata.domain_hint (sinal explícito do FE) sobre resolved_domain
    para derivar o PromptScope do turno no caminho federado.

    domain_hint é sinal EXPLÍCITO do recrutador (card "Foco em Vaga" / "Foco em Candidato").
    resolved_domain é o resultado do router — pode ser "auto" no caminho federado
    (LIA_FEDERATED_PRIMARY) porque o CascadedRouter é pulado para domínios não-especiais.
    O sinal explícito do FE ganha.

    Regra: page_type ainda prevalece sobre domain_hint (via scope_for_context existente).
    Esta função só resolve o effective_domain; scope_for_context aplica a precedência final.
    """
    domain_hint = ((context or {}).get("metadata") or {}).get("domain_hint")
    return domain_hint if isinstance(domain_hint, str) and domain_hint else resolved_domain


# ---------------------------------------------------------------------------
# GAP-02-006 — Stale context detection
# ---------------------------------------------------------------------------

import logging as _logging

_stale_logger = _logging.getLogger(__name__)

_STALE_THRESHOLD_SECONDS_DEFAULT = 60


def detect_stale_context(
    captured_at: str | None,
    threshold_seconds: int = _STALE_THRESHOLD_SECONDS_DEFAULT,
) -> bool:
    """Return True when the view_context is older than threshold_seconds.

    Args:
        captured_at: ISO-8601 timestamp from the FE (e.g. "2026-06-16T12:00:00.000Z").
            None / empty → treated as fresh (graceful; FE may not send this field).
        threshold_seconds: age in seconds beyond which context is considered stale.
            Default 60 s. Pass 0 to treat any timestamped context as stale (useful
            in tests).

    Returns:
        True  — context is older than threshold (stale).
        False — context is fresh, missing, or timestamp is unparseable (all safe).

    Design: fails-open (returns False) on any error so that stale detection never
    breaks the chat request. Staleness is a warning signal, not a gate.
    """
    if not captured_at:
        return False
    try:
        from datetime import datetime, timezone

        # Handle trailing Z (JavaScript ISO format) — Python 3.10 doesn't accept it
        ts = captured_at.strip()
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        captured = datetime.fromisoformat(ts)
        # If tz-naive (unlikely from JS), assume UTC
        if captured.tzinfo is None:
            captured = captured.replace(tzinfo=timezone.utc)
        age_s = (datetime.now(timezone.utc) - captured).total_seconds()
        return age_s > threshold_seconds
    except (ValueError, TypeError, OverflowError):
        # Unparseable timestamp — treat as fresh (fail-open)
        return False


def check_and_log_stale_context(ctx: dict | None) -> None:
    """Convenience helper: checks captured_at in ctx and logs a warning if stale.

    Intended to be called once per chat request after the context dict is available.
    Does nothing (silently) if ctx is None, captured_at is absent, or context is fresh.
    """
    if not ctx or not isinstance(ctx, dict):
        return
    # Look in ctx directly and inside nested view_context
    captured_at = ctx.get("captured_at")
    if not captured_at:
        vc = ctx.get("view_context")
        if isinstance(vc, dict):
            captured_at = vc.get("captured_at")
    if detect_stale_context(captured_at):
        _stale_logger.warning(
            "Stale view_context received (age > %ds) — agent context may not reflect "
            "current screen state",
            _STALE_THRESHOLD_SECONDS_DEFAULT,
            extra={"captured_at": captured_at},
        )
