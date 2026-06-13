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
        _label_pt = "Candidato em foco" if _etype == "candidate" else "Vaga em foco"
        _id_str = entity_focus["id"]
        lines.append(f"- {_label_pt}: {_label} (ID: {_id_str})")

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
