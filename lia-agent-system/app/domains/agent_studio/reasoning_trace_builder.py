"""Reasoning Trace Builder — Onda 1 B2 canonical (2026-05-27).

Converte mensagens do LangGraph state (final messages list) em
`list[AgentReasoningStep]` consumido pelo DecisionTreeDrawer no Studio
Control Room (4ª aba).

LGPD Art. 9 — cada step declara `data_fields_accessed`, list de campos
do candidato/job tocados pela tool. Heurística inferencial (não tem como
saber 100% sem instrumentação fina das tools) — sensível por design:
nunca marca campos proibidos LGPD (CPF, raça, religião, gênero, estado
civil).

Refs:
- ~/.claude/plans/steady-dazzling-shamir.md Onda 1 B2
- libs/agents-core/lia_agents_core/agent_interface.py AgentReasoningStep
- CLAUDE.md ADR-LGPD-001
"""
from __future__ import annotations

from typing import Any

from lia_agents_core.agent_interface import AgentReasoningStep


# LGPD Art. 9 — campos sensíveis NUNCA podem aparecer em data_fields_accessed.
# Documentado declarativamente pra que o sensor check_lgpd_data_access_logged
# possa pinar a invariante.
FORBIDDEN_LGPD_FIELDS = frozenset({
    "cpf",
    "raca",
    "raça",
    "religiao",
    "religião",
    "genero",
    "gênero",
    "estado_civil",
    "estado civil",
    "orientacao_sexual",
    "orientação_sexual",
    "saude",
    "saúde",
    "deficiencia",
    "deficiência",
})

# Heurística canonical: nome de tool → campos do candidato/job que ela tipicamente lê.
# Mantido conservador — preferível subdeclarar (audit incompleto)
# do que sobredeclarar (LGPD violation declarativa).
_TOOL_DATA_FIELDS: dict[str, list[str]] = {
    # Read tools (Pool 1 cross-domain canonical)
    "search_candidates": ["nome", "email"],
    "get_candidate_details": ["nome", "email", "telefone", "curriculum"],
    "search_talent_pool": ["nome", "email"],
    "get_job_details": ["titulo_vaga", "descricao_vaga"],
    "list_jobs": ["titulo_vaga"],
    "get_pipeline_summary": ["status_candidato"],
    "get_evaluation_criteria": ["criterios_avaliacao"],
    "get_company_culture": ["cultura_empresa"],
    "get_analytics_summary": [],
    "summarize_context": [],
    "clarify_request": [],
    # Write tools
    "move_candidate": ["nome", "status_candidato"],
    "create_note": ["nome"],
    "send_email": ["email", "nome"],
    "update_candidate_field": ["nome"],
    "schedule_interview": ["nome", "email", "telefone"],
}


# Heurística textual: tool name contém keyword → adiciona campo.
# Cobre tools customizadas que não estão em _TOOL_DATA_FIELDS.
_KEYWORD_FIELDS: list[tuple[tuple[str, ...], list[str]]] = [
    (("resume", "cv", "curriculum"), ["curriculum"]),
    (("phone", "telefone", "contact"), ["telefone"]),
    (("email", "mail"), ["email"]),
    (("interview", "entrevista"), ["nome", "email"]),
    (("calendar", "schedule"), ["nome"]),
    (("salary", "salario", "compensation"), ["expectativa_salarial"]),
]


def _infer_data_fields_accessed(
    tool_name: str, tool_input: Any
) -> list[str]:
    """Inferir LGPD data_fields_accessed por tool name + input.

    Conservador: nunca inclui FORBIDDEN_LGPD_FIELDS (defesa em profundidade).
    """
    fields: set[str] = set()

    tn = (tool_name or "").lower().strip()

    # 1. Lookup direto na tabela canonical.
    if tn in _TOOL_DATA_FIELDS:
        fields.update(_TOOL_DATA_FIELDS[tn])

    # 2. Heurística textual via keywords no nome.
    for keywords, kw_fields in _KEYWORD_FIELDS:
        if any(kw in tn for kw in keywords):
            fields.update(kw_fields)

    # 3. Inspeção do tool_input — candidate_id presente → assume leitura
    # de identificação básica.
    if isinstance(tool_input, dict):
        if "candidate_id" in tool_input or "candidate_ids" in tool_input:
            fields.update({"nome", "email"})
        if "job_id" in tool_input:
            fields.update({"titulo_vaga"})

    # Defense-in-depth LGPD: filter FORBIDDEN antes de retornar.
    safe = sorted(f for f in fields if f.lower() not in FORBIDDEN_LGPD_FIELDS)
    return safe


def _truncate_detail(content: Any, max_chars: int = 280) -> str:
    """Truncate textual detail pra UI display."""
    if content is None:
        return ""
    s = str(content)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."


def build_reasoning_trace(
    messages: list[Any],
    max_steps: int = 20,
) -> list[AgentReasoningStep]:
    """Construir decision tree do agente a partir do LangGraph messages list.

    Onda 1 B2 — heurística canonical pra Studio Control Room.

    Args:
        messages: state["messages"] do LangGraph (lista de AIMessage/ToolMessage).
        max_steps: hard cap em 20 pra não inchar payload JSONB (~10KB por step
            no pior caso). Excedendo, último step vira summary.

    Returns:
        list[AgentReasoningStep] — pode estar vazia (agente respondeu sem tools).

    Shape canonical:
        - step_type='thought' → AIMessage com content (raciocínio do LLM)
        - step_type='action' → AIMessage com tool_calls (chamada de tool)
        - step_type='observation' → ToolMessage (resposta da tool)
    """
    trace: list[AgentReasoningStep] = []

    for m in messages:
        if len(trace) >= max_steps - 1:
            # Reserve último slot pro summary step
            remaining = sum(
                1
                for x in messages[messages.index(m):]
                if _is_step_relevant(x)
            )
            if remaining > 0:
                trace.append(
                    AgentReasoningStep(
                        step_type="thought",
                        label=f"... e mais {remaining} passos",
                        detail=(
                            f"Trace truncado em {max_steps} steps. "
                            f"Total real: {len(trace) + remaining} steps."
                        ),
                        data_fields_accessed=[],
                    )
                )
            break

        # ToolMessage — observation
        tool_call_id = getattr(m, "tool_call_id", None) or (
            m.get("tool_call_id") if isinstance(m, dict) else None
        )
        if tool_call_id:
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            tool_name = getattr(m, "name", None) or (
                m.get("name", "") if isinstance(m, dict) else ""
            )
            trace.append(
                AgentReasoningStep(
                    step_type="observation",
                    label=f"Resultado: {tool_name or 'tool'}",
                    detail=_truncate_detail(content),
                    data_fields_accessed=[],
                )
            )
            continue

        # AIMessage com tool_calls — action
        tool_calls = getattr(m, "tool_calls", None) or (
            m.get("tool_calls") if isinstance(m, dict) else None
        ) or []

        for tc in tool_calls:
            if isinstance(tc, dict):
                tc_name = tc.get("name", "")
                tc_args = tc.get("args") or tc.get("arguments") or {}
            else:
                tc_name = getattr(tc, "name", "")
                tc_args = getattr(tc, "args", None) or getattr(tc, "arguments", None) or {}
            trace.append(
                AgentReasoningStep(
                    step_type="action",
                    label=f"Chamada: {tc_name}",
                    detail=_truncate_detail(tc_args),
                    data_fields_accessed=_infer_data_fields_accessed(tc_name, tc_args),
                )
            )

        # AIMessage com content sem tool_calls — thought
        content = getattr(m, "content", None) or (
            m.get("content", "") if isinstance(m, dict) else ""
        )
        if content and not tool_calls and not tool_call_id:
            text = _extract_text(content)
            if text and text.strip():
                trace.append(
                    AgentReasoningStep(
                        step_type="thought",
                        label="Raciocínio",
                        detail=_truncate_detail(text),
                        data_fields_accessed=[],
                    )
                )

    return trace


def _is_step_relevant(m: Any) -> bool:
    """Helper: True se a mensagem virará um step (thought/action/observation)."""
    if getattr(m, "tool_call_id", None) or (
        isinstance(m, dict) and m.get("tool_call_id")
    ):
        return True
    tool_calls = getattr(m, "tool_calls", None) or (
        m.get("tool_calls") if isinstance(m, dict) else None
    )
    if tool_calls:
        return True
    content = getattr(m, "content", None) or (
        m.get("content", "") if isinstance(m, dict) else ""
    )
    return bool(content)


def _extract_text(content: Any) -> str:
    """Extrair texto de content que pode ser str ou list[dict] (Anthropic)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(content)
