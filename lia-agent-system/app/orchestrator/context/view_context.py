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

    if not lines:
        return ""

    header = (
        "Estado da tela atual (o recrutador está olhando para esta visão AGORA "
        "— use como contexto; se ele disser 'resuma/refine/liste isso', refere-se "
        "a esta visão):"
    )
    return header + "\n" + "\n".join(lines)
