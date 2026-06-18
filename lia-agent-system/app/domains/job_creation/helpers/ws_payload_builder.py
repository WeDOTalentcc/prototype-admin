"""Helper canonical para construir ws_stage_payload (PR-9 / F-3.1 sub-sprint A).

Background: o pattern ``{"type": "wizard_stage", "stage": ..., "data": {...},
"completeness": ..., "requires_approval": ...}`` aparecia copy-pasted em 20
sites em ``app/domains/job_creation/graph.py`` (graph.py LOC 5514 antes do
refactor). Esta extracao formaliza o contrato de payload WS canonical, reduz
boilerplate, e centraliza validacao de campos invariantes (Task #1099 invariant:
``data.message`` obrigatorio para evitar silent_fallback no WizardSessionService).

Pattern canonical de uso:

    state["ws_stage_payload"] = build_ws_stage_payload(
        stage="bigfive",
        completeness=calculate_completeness("bigfive"),
        requires_approval=False,
        data={
            "message": "Big Five extraido. Quer ajustar ou seguir?",
            "bigfive_profile": bigfive_profile,
            "trait_rankings": trait_rankings,
        },
    )

    # Com ui_action (pipeline_template node):
    state["ws_stage_payload"] = build_ws_stage_payload(
        stage="pipeline_template",
        completeness=calculate_completeness("pipeline_template"),
        requires_approval=True,
        ui_action="suggest_pipeline_template",
        data={
            "message": "Vamos usar este pipeline?",
            "templates": templates,
            ...
        },
    )

Garantias:
- ``type`` sempre ``"wizard_stage"`` (constante, inferida);
- ``stage`` validado contra ``WIZARD_STAGE_NAMES`` canonical;
- ``data.message`` obrigatorio (Task #1099) — raise ValueError se ausente;
- ``completeness`` aceita int (0) ou float ([0.0, 1.0]) — valida range;
- ``requires_approval`` sempre booleano;
- ``ui_action`` opcional, string quando presente.

Retorna ``dict[str, Any]`` (nao TypedDict) para preservar mutabilidade
existente — alguns sites mutam ``ws_stage_payload["data"]`` apos construcao
(ex.: jd_enrichment_node:797 anexa ``templates`` e ``ui_action`` depois).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# Stage names canonical — alinhado com WizardStage enum em state.py.
# Mantido como tuple para imutabilidade + checagem O(N) barata.
WIZARD_STAGE_NAMES: tuple[str, ...] = (
    "intake",
    "jd_enrichment",
    "pipeline_template",
    "bigfive",
    "salary",
    "benefits",
    "variable_comp",
    "competency",
    "wsi_questions",
    "eligibility",
    "review",
    "publish",
    "calibration",
    "handoff",
    "done",
    "scheduling",
)


def build_ws_stage_payload(
    *,
    stage: str,
    requires_approval: bool,
    data: Dict[str, Any],
    completeness: Optional[float | int] = None,
    ui_action: Optional[str] = None,
) -> Dict[str, Any]:
    """Construtor canonical de ``ws_stage_payload``.

    Args:
        stage: nome canonical da stage. Deve estar em ``WIZARD_STAGE_NAMES``.
        requires_approval: HITL gate ativo? Boolean estrito.
        data: dict de dados especificos da stage. **Obrigatorio** conter
            chave ``"message"`` (Task #1099 invariant — sem isso o
            WizardSessionService cai em ``_emit_silent_fallback``).
        completeness: progresso geral do wizard. ``int`` (0) ou ``float``
            no range ``[0.0, 1.0]``. Quando ``None`` (default), a chave nao
            e adicionada ao payload — preserva byte-equivalence com sites
            originais de block path que omitem o campo. Sites canonical
            de sucesso devem passar ``calculate_completeness(stage)``.
        ui_action: payload de acao UI opcional (ex.: ``"suggest_pipeline_template"``).
            Quando ``None``, a chave nao e adicionada ao payload final.

    Returns:
        Dict canonical com ordem de chaves preservada para byte-equivalence:
        ``{type, stage, [ui_action,] data, [completeness,] requires_approval}``.

    Raises:
        ValueError: ``stage`` nao-canonical, ``completeness`` fora de range,
            ou ``data["message"]`` ausente/falsy.
        TypeError: ``data`` nao e ``dict`` ou ``requires_approval`` nao e ``bool``.
    """
    # Validacao defensiva — fail-loud canonical (REGRA 4 anti-silent-fallback).
    if stage not in WIZARD_STAGE_NAMES:
        raise ValueError(
            f"build_ws_stage_payload: stage={stage!r} nao e canonical. "
            f"Permitidos: {WIZARD_STAGE_NAMES}"
        )

    if not isinstance(data, dict):
        raise TypeError(
            f"build_ws_stage_payload: data deve ser dict, recebeu {type(data).__name__}"
        )

    # Task #1099 invariant — data.message obrigatorio.
    # Sem isso o WizardSessionService cai em silent_fallback ("[ATENCAO: estado
    # inconsistente]"). Falhamos cedo aqui para pegar bug em test, nao em prod.
    if not data.get("message"):
        raise ValueError(
            f"build_ws_stage_payload: data['message'] obrigatorio (Task #1099 invariant). "
            f"Stage={stage!r}, data_keys={list(data.keys())}"
        )

    if not isinstance(requires_approval, bool):
        raise TypeError(
            f"build_ws_stage_payload: requires_approval deve ser bool, "
            f"recebeu {type(requires_approval).__name__}"
        )

    if completeness is not None:
        # completeness pode ser int (0 em block paths) ou float (calculate_completeness).
        if isinstance(completeness, bool) or not isinstance(completeness, (int, float)):
            raise TypeError(
                f"build_ws_stage_payload: completeness deve ser int|float|None, "
                f"recebeu {type(completeness).__name__}"
            )
        if not (0 <= completeness <= 1):
            # Aceita 0 (int) ou floats em [0.0, 1.0]. Rejeita 100 (legado de %).
            raise ValueError(
                f"build_ws_stage_payload: completeness={completeness} fora de [0, 1]. "
                f"Use 0 (int) para bloqueio ou float [0.0, 1.0] para progresso."
            )

    # Ordem de chaves preserva pattern dos 20 sites originais para byte-equivalence:
    # {type, stage, [ui_action,] data, [completeness,] requires_approval}.
    payload: Dict[str, Any] = {
        "type": "wizard_stage",
        "stage": stage,
    }
    if ui_action is not None:
        payload["ui_action"] = ui_action
    payload["data"] = data
    if completeness is not None:
        payload["completeness"] = completeness
    payload["requires_approval"] = requires_approval
    return payload
