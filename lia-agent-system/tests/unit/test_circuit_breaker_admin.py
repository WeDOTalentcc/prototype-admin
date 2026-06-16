"""
Tests — Admin Circuit Breakers endpoint (Gap 16.3)

Cobre:
- GET /admin/circuit-breakers → retorna status de todos os circuits
- POST /admin/circuit-breakers/{name}/reset → reset de circuit existente
- POST /admin/circuit-breakers/{name}/reset → 404 para circuit inexistente
- POST /admin/circuit-breakers/reset-all → reset de todos
- _get_combined_status combina class + functional instances
- total e open_count corretos
"""
import pytest
from unittest.mock import MagicMock, patch

# Pre-import para garantir que o módulo está no sys.modules antes dos patches
import app.api.v1.admin_circuit_breakers as _cb_module  # noqa: E402


# ─────────────────────────────────────────────
# _get_combined_status
# ─────────────────────────────────────────────

class TestGetCombinedStatus:
    def test_combines_class_and_functional_circuits(self):
        with (
            patch.object(_cb_module, "get_all_circuit_stats",
                         return_value={"anthropic": {"state": "closed", "total_calls": 10}}),
            patch.object(_cb_module, "get_all_circuits_status",
                         return_value={"pearch_functional": {"state": "open", "failure_count": 5}}),
        ):
            result = _cb_module._get_combined_status()

        assert "anthropic" in result
        assert "pearch_functional" in result
        assert result["anthropic"]["implementation"] == "class"
        assert result["pearch_functional"]["implementation"] == "functional"

    def test_class_circuit_takes_priority_over_functional(self):
        """Se mesmo nome existe em ambas as instâncias, class tem prioridade."""
        with (
            patch.object(_cb_module, "get_all_circuit_stats",
                         return_value={"anthropic": {"state": "closed"}}),
            patch.object(_cb_module, "get_all_circuits_status",
                         return_value={"anthropic": {"state": "open"}}),
        ):
            result = _cb_module._get_combined_status()

        assert result["anthropic"]["state"] == "closed"
        assert result["anthropic"]["implementation"] == "class"


# ─────────────────────────────────────────────
# list_circuit_breakers endpoint
# ─────────────────────────────────────────────

class TestListCircuitBreakers:
    @pytest.mark.asyncio
    async def test_returns_total_and_circuits(self):
        with patch.object(_cb_module, "_get_combined_status", return_value={
            "anthropic": {"state": "closed", "implementation": "class"},
            "openai": {"state": "open", "implementation": "class"},
        }):
            result = await _cb_module.list_circuit_breakers(_user=MagicMock())

        assert result["total"] == 2
        assert result["open_count"] == 1
        assert "anthropic" in result["circuits"]
        assert "openai" in result["circuits"]

    @pytest.mark.asyncio
    async def test_open_count_zero_when_all_closed(self):
        with patch.object(_cb_module, "_get_combined_status", return_value={
            "anthropic": {"state": "closed"},
            "gemini": {"state": "half_open"},
        }):
            result = await _cb_module.list_circuit_breakers(_user=MagicMock())

        assert result["open_count"] == 0


# ─────────────────────────────────────────────
# reset_circuit_breaker
# ─────────────────────────────────────────────

class TestResetCircuitBreaker:
    @pytest.mark.asyncio
    async def test_resets_known_class_circuit(self):
        mock_circuit = MagicMock()

        # Patch dentro da função (lazy import)
        import app.shared.resilience.circuit_breaker as _cb_res
        original_all = _cb_res.ALL_CIRCUITS.copy()
        _cb_res.ALL_CIRCUITS["__test_circuit__"] = mock_circuit
        try:
            result = await _cb_module.reset_circuit_breaker("__test_circuit__", _user=MagicMock())
        finally:
            _cb_res.ALL_CIRCUITS.pop("__test_circuit__", None)

        mock_circuit.reset.assert_called_once()
        assert result["new_state"] == "closed"
        assert result["circuit"] == "__test_circuit__"

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_circuit(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await _cb_module.reset_circuit_breaker("nonexistent_xyzabc", _user=MagicMock())

        assert exc_info.value.status_code == 404


# ─────────────────────────────────────────────
# reset_all_circuit_breakers
# ─────────────────────────────────────────────

class TestResetAllCircuitBreakers:
    @pytest.mark.asyncio
    async def test_resets_all_returns_new_state(self):
        reset_all_fn = MagicMock()
        reset_fn = MagicMock()

        with (
            patch.object(_cb_module, "reset_all_circuits", reset_all_fn),
            patch.object(_cb_module, "reset_circuit", reset_fn),
        ):
            result = await _cb_module.reset_all_circuit_breakers(_user=MagicMock())

        reset_all_fn.assert_called_once()
        assert result["new_state"] == "closed"
        assert "total_reset" in result
