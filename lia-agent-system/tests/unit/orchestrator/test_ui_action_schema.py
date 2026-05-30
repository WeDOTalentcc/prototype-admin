"""
PR-D — UIAction Pydantic schemas (BE mirror)

Cobre validação strict de UIActions globais no boundary BE→FE.
Espelho dos testes FE em ``src/hooks/__tests__/use-ui-action.test.ts``.

Skill: lia-testing PARTE 1 (TDD) + harness-engineering [sensor no boundary].
"""

from app.shared.websocket.ws_message_schemas import (
    GLOBAL_UI_ACTION_TYPES,
    UIAction,
    UINavigateToParams,
    UIOpenModalParams,
    UIOpenOfferReviewParams,
    UIScrollToParams,
    UIWizardStepParams,
    validate_global_ui_action_params,
)


# ─── GLOBAL_UI_ACTION_TYPES espelha o FE ────────────────────────────────


def test_global_action_types_match_fe_canonical_list():
    """Lista de tipos globais deve estar idêntica ao FE."""
    assert set(GLOBAL_UI_ACTION_TYPES) == {
        "navigate_to",
        "open_modal",
        "open_offer_review",
        "wizard_step",
        "open_panel",
        "scroll_to",
        "settings_open_tab",  # WT-2022 Fase 4: bridge chat -> SettingsPageEnhanced
    }


# ─── Validação por tipo ──────────────────────────────────────────────────


def test_navigate_to_valid():
    p = UINavigateToParams.model_validate({"page": "/configuracoes/ai-credits"})
    assert p.page == "/configuracoes/ai-credits"
    assert p.query == {}


def test_navigate_to_with_query():
    p = UINavigateToParams.model_validate(
        {"page": "/configuracoes", "query": {"tab": "hiring-policy"}}
    )
    assert p.query == {"tab": "hiring-policy"}


def test_navigate_to_invalid_missing_page():
    """`page` é obrigatório — falha validação."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        UINavigateToParams.model_validate({"query": {"x": "y"}})


def test_open_offer_review_valid():
    p = UIOpenOfferReviewParams.model_validate(
        {"candidate_id": "cand-1", "job_id": "job-1"}
    )
    assert p.candidate_id == "cand-1"
    assert p.draft_id is None


def test_open_offer_review_with_draft():
    p = UIOpenOfferReviewParams.model_validate(
        {"candidate_id": "cand-1", "job_id": "job-1", "draft_id": "draft-xyz"}
    )
    assert p.draft_id == "draft-xyz"


def test_open_modal_drops_extra_fields():
    """`extra=ignore` deve descartar campos não declarados (sensor anti-injection)."""
    p = UIOpenModalParams.model_validate(
        {"modal_id": "confirm", "data": {"x": 1}, "evil": "<script>"}
    )
    assert p.modal_id == "confirm"
    assert not hasattr(p, "evil")


# ─── validate_global_ui_action_params (router-side helper) ───────────────


def test_validate_global_returns_model_for_known_action():
    result = validate_global_ui_action_params(
        "navigate_to", {"page": "/jobs"}
    )
    assert isinstance(result, UINavigateToParams)
    assert result.page == "/jobs"


def test_validate_global_returns_none_for_unknown_action():
    """Action page-specific não é validada aqui — caller assume default."""
    result = validate_global_ui_action_params(
        "move_candidate", {"candidate_id": "x"}
    )
    assert result is None


def test_validate_global_returns_none_for_invalid_params():
    """Action global com params inválidos é rejeitada (sensor)."""
    result = validate_global_ui_action_params("navigate_to", {})  # falta `page`
    assert result is None


def test_validate_global_open_offer_review():
    result = validate_global_ui_action_params(
        "open_offer_review",
        {"candidate_id": "c1", "job_id": "j1", "draft_id": "d1"},
    )
    assert isinstance(result, UIOpenOfferReviewParams)
    assert result.draft_id == "d1"


# ─── UIAction wire-format ────────────────────────────────────────────────


def test_ui_action_accepts_global_type():
    a = UIAction.model_validate(
        {"type": "navigate_to", "params": {"page": "/jobs"}}
    )
    assert a.type == "navigate_to"
    assert a.params == {"page": "/jobs"}


def test_ui_action_accepts_page_specific_type():
    """Tipo aberto: page-specific actions (kanban, talent) passam pelo wire."""
    a = UIAction.model_validate(
        {"type": "move_candidate", "params": {"candidate_id": "c1"}}
    )
    assert a.type == "move_candidate"


def test_ui_action_drops_extra_fields():
    a = UIAction.model_validate(
        {"type": "navigate_to", "params": {"page": "/x"}, "leak": "should-go"}
    )
    assert not hasattr(a, "leak")
