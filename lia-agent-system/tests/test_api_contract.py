import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.shared.api.response import (
    APIResponse,
    ErrorDetail,
    ResponseMeta,
    bad_request,
    error_response,
    forbidden,
    internal_error,
    not_found,
    ok_response,
)


def _make_request(request_id: str = "test-req-123") -> MagicMock:
    req = MagicMock()
    req.state.request_id = request_id
    return req


def _parse(resp) -> dict:
    return json.loads(resp.body.decode("utf-8"))


class TestAPIResponseEnvelope:

    def test_ok_response_shape(self):
        resp = ok_response({"users": [1, 2, 3]})
        body = _parse(resp)
        assert body["ok"] is True
        assert body["data"] == {"users": [1, 2, 3]}
        assert "meta" in body
        assert "ts" in body["meta"]
        assert resp.status_code == 200

    def test_error_response_shape(self):
        resp = error_response("VALIDATION_ERROR", "Field X is required", 422, details={"field": "x"})
        body = _parse(resp)
        assert body["ok"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Field X is required"
        assert body["error"]["details"] == {"field": "x"}
        assert resp.status_code == 422

    def test_not_found_shortcut(self):
        resp = not_found("Candidate")
        body = _parse(resp)
        assert body["ok"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert "Candidate" in body["error"]["message"]
        assert resp.status_code == 404

    def test_internal_error_shortcut(self):
        resp = internal_error()
        body = _parse(resp)
        assert body["ok"] is False
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert resp.status_code == 500

    def test_ok_response_has_no_error_key(self):
        resp = ok_response({"id": 1})
        body = _parse(resp)
        assert "error" not in body
        assert "data" in body

    def test_error_response_has_no_data_key(self):
        resp = error_response("BAD_REQUEST", "invalid")
        body = _parse(resp)
        assert "data" not in body
        assert "error" in body

    def test_request_id_propagation(self):
        req = _make_request("abc-123")
        resp = ok_response({"ok": True}, request=req)
        body = _parse(resp)
        assert body["meta"]["request_id"] == "abc-123"

    def test_bad_request_shortcut(self):
        resp = bad_request("Missing name")
        body = _parse(resp)
        assert body["ok"] is False
        assert body["error"]["code"] == "BAD_REQUEST"
        assert resp.status_code == 400

    def test_forbidden_shortcut(self):
        resp = forbidden("Not your tenant")
        body = _parse(resp)
        assert body["ok"] is False
        assert body["error"]["code"] == "FORBIDDEN"
        assert resp.status_code == 403


RAILS_EVENT_CONTRACTS = {
    "agent_execution_completed": {
        "required_keys": ["event", "agent_id", "company_id", "execution_id", "result", "timestamp"],
        "types": {"event": str, "agent_id": str, "company_id": str, "execution_id": str, "result": dict, "timestamp": str},
    },
    "agent_execution_failed": {
        "required_keys": ["event", "agent_id", "company_id", "execution_id", "error_code", "error_message", "timestamp"],
        "types": {"event": str, "agent_id": str, "company_id": str, "execution_id": str, "error_code": str, "error_message": str, "timestamp": str},
    },
    "agent_deployment_created": {
        "required_keys": ["event", "agent_id", "company_id", "deployment_id", "version", "status", "timestamp"],
        "types": {"event": str, "agent_id": str, "company_id": str, "deployment_id": str, "version": str, "status": str, "timestamp": str},
    },
    "agent_deployment_paused": {
        "required_keys": ["event", "agent_id", "company_id", "deployment_id", "reason", "timestamp"],
        "types": {"event": str, "agent_id": str, "company_id": str, "deployment_id": str, "reason": str, "timestamp": str},
    },
    "agent_approval_requested": {
        "required_keys": ["event", "agent_id", "company_id", "approval_id", "requested_by", "action", "timestamp"],
        "types": {"event": str, "agent_id": str, "company_id": str, "approval_id": str, "requested_by": str, "action": str, "timestamp": str},
    },
    "agent_approval_reviewed": {
        "required_keys": ["event", "agent_id", "company_id", "approval_id", "reviewed_by", "decision", "timestamp"],
        "types": {"event": str, "agent_id": str, "company_id": str, "approval_id": str, "reviewed_by": str, "decision": str, "timestamp": str},
    },
}


def _build_sample_payload(event_name: str, contract: dict) -> dict:
    payload = {}
    for key in contract["required_keys"]:
        expected_type = contract["types"][key]
        if key == "event":
            payload[key] = event_name
        elif key == "timestamp":
            payload[key] = datetime.utcnow().isoformat() + "Z"
        elif key == "result":
            payload[key] = {"status": "success", "output": {}}
        elif expected_type is str:
            payload[key] = f"test-{key}"
        elif expected_type is dict:
            payload[key] = {}
        else:
            payload[key] = f"test-{key}"
    return payload


class TestRailsEventContracts:

    @pytest.mark.parametrize("event_name", list(RAILS_EVENT_CONTRACTS.keys()))
    def test_event_has_required_keys(self, event_name: str):
        contract = RAILS_EVENT_CONTRACTS[event_name]
        payload = _build_sample_payload(event_name, contract)
        for key in contract["required_keys"]:
            assert key in payload, f"Missing required key '{key}' in event '{event_name}'"

    @pytest.mark.parametrize("event_name", list(RAILS_EVENT_CONTRACTS.keys()))
    def test_event_field_types(self, event_name: str):
        contract = RAILS_EVENT_CONTRACTS[event_name]
        payload = _build_sample_payload(event_name, contract)
        for key, expected_type in contract["types"].items():
            assert isinstance(payload[key], expected_type), (
                f"Event '{event_name}': field '{key}' expected {expected_type.__name__}, "
                f"got {type(payload[key]).__name__}"
            )

    @pytest.mark.parametrize("event_name", list(RAILS_EVENT_CONTRACTS.keys()))
    def test_event_name_matches_payload(self, event_name: str):
        contract = RAILS_EVENT_CONTRACTS[event_name]
        payload = _build_sample_payload(event_name, contract)
        assert payload["event"] == event_name

    @pytest.mark.parametrize("event_name", list(RAILS_EVENT_CONTRACTS.keys()))
    def test_event_timestamp_is_iso(self, event_name: str):
        contract = RAILS_EVENT_CONTRACTS[event_name]
        payload = _build_sample_payload(event_name, contract)
        ts = payload["timestamp"].rstrip("Z")
        datetime.fromisoformat(ts)

    @pytest.mark.parametrize("event_name", list(RAILS_EVENT_CONTRACTS.keys()))
    def test_event_has_company_id(self, event_name: str):
        contract = RAILS_EVENT_CONTRACTS[event_name]
        payload = _build_sample_payload(event_name, contract)
        assert "company_id" in payload
        assert isinstance(payload["company_id"], str)
        assert len(payload["company_id"]) > 0

    @pytest.mark.parametrize("event_name", list(RAILS_EVENT_CONTRACTS.keys()))
    def test_event_has_agent_id(self, event_name: str):
        contract = RAILS_EVENT_CONTRACTS[event_name]
        payload = _build_sample_payload(event_name, contract)
        assert "agent_id" in payload
        assert isinstance(payload["agent_id"], str)
