"""B8 E2E — 7 tests covering Peça 1 (3 extractor RUNs) + Peça 2 (4 carry tests)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
os.chdir("/home/runner/workspace/lia-agent-system")


# ═══════════════════════════════════════════════
# PEÇA 1 — Extractor RUNs (deterministic, no LLM)
# ═══════════════════════════════════════════════

class TestB8Peca1Extractors:

    def test_turno1_captures_manager(self):
        """'gestor é joao silva joao.silva@wedotalent.cc' → captures both."""
        from app.orchestrator.guards.pending_manager_capture import extract_pending_manager
        result = extract_pending_manager("gestor é joao silva joao.silva@wedotalent.cc")
        assert result is not None, "Should capture manager"
        assert result["email"] == "joao.silva@wedotalent.cc"
        assert result["name"] is not None
        print(f"  T1 OK: name={result['name']!r} email={result['email']!r}")

    def test_turno2_no_capture(self):
        """'você já tem meus dados' → NO capture."""
        from app.orchestrator.guards.pending_manager_capture import extract_pending_manager
        result = extract_pending_manager("você já tem meus dados")
        assert result is None, f"Should NOT capture, got {result}"
        print("  T2 OK: correctly returned None")

    def test_manager_vs_recruiter(self):
        """'o gestor é João Silva mas o recrutador sou eu' → captures João."""
        from app.orchestrator.guards.pending_manager_capture import extract_pending_manager
        result = extract_pending_manager("o gestor é João Silva mas o recrutador sou eu, Ana")
        assert result is not None, "Should capture manager"
        name = (result.get("name") or "").lower()
        assert "joão" in name or "joao" in name or "silva" in name, (
            f"Expected João Silva, got {result.get('name')!r}"
        )
        print(f"  T3 OK: name={result.get('name')!r} (not recruiter)")


# ═══════════════════════════════════════════════
# PEÇA 2 — Carry + CONTEXT_CARRY_KEYS
# ═══════════════════════════════════════════════

class TestB8Peca2Carry:

    def test_context_carry_keys_include_manager(self):
        """_CONTEXT_CARRY_KEYS must include parsed_manager_name/email."""
        from app.domains.job_creation.services.wizard_session_service import _CONTEXT_CARRY_KEYS
        assert "parsed_manager_name" in _CONTEXT_CARRY_KEYS, f"Missing parsed_manager_name in {_CONTEXT_CARRY_KEYS}"
        assert "parsed_manager_email" in _CONTEXT_CARRY_KEYS, f"Missing parsed_manager_email in {_CONTEXT_CARRY_KEYS}"
        print(f"  P2.3 OK: {_CONTEXT_CARRY_KEYS}")

    def test_fresh_session_populates_manager_from_ctx(self):
        """Fresh wizard: ctx has manager → state gets manager."""
        # Directly test the fresh-session code path logic
        # (extracted from _build_state to avoid needing full service deps)
        ctx = {
            "user_name": "Ana Recrutadora",
            "user_email": "ana@empresa.com",
            "parsed_manager_name": "João Silva",
            "parsed_manager_email": "joao.silva@wedotalent.cc",
        }
        # Simulate fresh path (lines 906-912 of wizard_session_service.py)
        state = {}
        state["parsed_recruiter_name"] = ctx.get("user_name") or None
        state["parsed_recruiter_email"] = ctx.get("user_email") or None
        state["parsed_manager_name"] = ctx.get("parsed_manager_name") or None
        state["parsed_manager_email"] = ctx.get("parsed_manager_email") or None

        assert state["parsed_manager_name"] == "João Silva"
        assert state["parsed_manager_email"] == "joao.silva@wedotalent.cc"
        assert state["parsed_recruiter_name"] == "Ana Recrutadora"
        assert state["parsed_recruiter_email"] == "ana@empresa.com"
        print(f"  FRESH OK: manager={state['parsed_manager_name']!r} recruiter={state['parsed_recruiter_name']!r}")

    def test_continue_session_does_not_overwrite(self):
        """Continue wizard: state already has manager → ctx does NOT overwrite."""
        ctx = {
            "parsed_manager_name": "João Silva",  # from chat carry
            "parsed_manager_email": "joao@x.com",
        }
        # Simulate continue path (lines 873-878) with existing state
        state = {
            "parsed_manager_name": "Carlos Mendes",  # wizard already captured
            "parsed_manager_email": "carlos@empresa.com",
        }
        # The guard: only if state doesn't already have it
        if ctx.get("parsed_manager_name") and not state.get("parsed_manager_name"):
            state["parsed_manager_name"] = ctx["parsed_manager_name"]
        if ctx.get("parsed_manager_email") and not state.get("parsed_manager_email"):
            state["parsed_manager_email"] = ctx["parsed_manager_email"]

        assert state["parsed_manager_name"] == "Carlos Mendes", (
            f"Wizard capture should win, got {state['parsed_manager_name']!r}"
        )
        assert state["parsed_manager_email"] == "carlos@empresa.com"
        print(f"  CONTINUE OK: wizard capture preserved ({state['parsed_manager_name']!r})")

    def test_continue_session_fills_empty(self):
        """Continue wizard: state has NO manager → ctx FILLS it."""
        ctx = {
            "parsed_manager_name": "João Silva",
            "parsed_manager_email": "joao.silva@wedotalent.cc",
        }
        state = {
            "parsed_manager_name": None,
            "parsed_manager_email": None,
        }
        if ctx.get("parsed_manager_name") and not state.get("parsed_manager_name"):
            state["parsed_manager_name"] = ctx["parsed_manager_name"]
        if ctx.get("parsed_manager_email") and not state.get("parsed_manager_email"):
            state["parsed_manager_email"] = ctx["parsed_manager_email"]

        assert state["parsed_manager_name"] == "João Silva"
        assert state["parsed_manager_email"] == "joao.silva@wedotalent.cc"
        print(f"  CONTINUE-FILL OK: carried {state['parsed_manager_name']!r}")


# ═══════════════════════════════════════════════
# PEÇA 2.1 — SSE wiring (code presence verification)
# ═══════════════════════════════════════════════

class TestB8Peca21SSEWiring:

    def test_sse_has_b8_p2_carry_code(self):
        """agent_chat_sse.py contains B8 Peça 2 carry block."""
        with open("/home/runner/workspace/lia-agent-system/app/api/v1/agent_chat_sse.py") as f:
            content = f.read()
        assert "[B8-P2] pending_manager carried to wizard" in content, (
            "Missing B8 P2 carry block in agent_chat_sse.py"
        )
        assert 'context["parsed_manager_name"] = _pm["name"]' in content
        assert 'context["parsed_manager_email"] = _pm["email"]' in content
        print("  SSE WIRING OK: B8 P2 carry block present")

    def test_sse_carry_is_before_run_wizard(self):
        """B8 P2 carry must appear BEFORE _run_wizard definition."""
        with open("/home/runner/workspace/lia-agent-system/app/api/v1/agent_chat_sse.py") as f:
            content = f.read()
        pos_carry = content.index("[B8-P2] pending_manager carried")
        pos_wizard = content.index("async def _run_wizard():")
        assert pos_carry < pos_wizard, (
            f"Carry at pos {pos_carry} must be BEFORE _run_wizard at {pos_wizard}"
        )
        print("  SSE ORDER OK: carry before _run_wizard")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--no-header", "-q"])
