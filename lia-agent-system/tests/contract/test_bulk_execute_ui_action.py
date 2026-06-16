"""Contract tests for bulk_execute ui_action (F3 Gap 1).

Verifica que UIBulkExecuteParams existe no schema canonico e que
GLOBAL_UI_ACTION_TYPES esta sincronizado com o FE (src/types/ui-action.ts).
"""
import pytest

from app.shared.websocket.ws_message_schemas import (
    GLOBAL_UI_ACTION_TYPES,
    UIBulkExecuteParams,
    UIAction,
    _UI_ACTION_PARAMS_BY_TYPE,
    validate_global_ui_action_params,
)


class TestBulkExecuteInWsMessageSchemas:
    def test_bulk_execute_type_registered_in_global_types(self):
        assert "bulk_execute" in GLOBAL_UI_ACTION_TYPES

    def test_uibulkexecuteparams_class_exists(self):
        assert UIBulkExecuteParams is not None

    def test_bulk_execute_in_params_by_type(self):
        assert "bulk_execute" in _UI_ACTION_PARAMS_BY_TYPE
        assert _UI_ACTION_PARAMS_BY_TYPE["bulk_execute"] is UIBulkExecuteParams

    def test_uibulkexecuteparams_valid_payload(self):
        params = UIBulkExecuteParams(
            action="reject_candidates",
            title="3 candidatos rejeitados",
            results=[
                {"id": "c1", "name": "Ana Lima", "ok": True},
                {"id": "c2", "name": "Joao Paz", "ok": False, "reason": "Email invalido"},
            ],
        )
        assert params.action == "reject_candidates"
        assert len(params.results) == 2

    def test_uibulkexecuteparams_empty_results_allowed(self):
        params = UIBulkExecuteParams(
            action="move_stage",
            title="0 candidatos movidos",
        )
        assert params.results == []

    def test_validate_global_ui_action_params_bulk_execute(self):
        validated = validate_global_ui_action_params(
            "bulk_execute",
            {
                "action": "reject_candidates",
                "title": "2 rejeitados",
                "results": [{"id": "c1", "name": "X", "ok": True}],
            },
        )
        assert validated is not None
        assert isinstance(validated, UIBulkExecuteParams)
        assert validated.action == "reject_candidates"

    def test_uiaction_wraps_bulk_execute(self):
        action = UIAction(
            type="bulk_execute",
            params={
                "action": "move_stage",
                "title": "1 movido",
                "results": [{"id": "c1", "name": "Y", "ok": True}],
            },
        )
        assert action.type == "bulk_execute"
        assert action.params["action"] == "move_stage"
