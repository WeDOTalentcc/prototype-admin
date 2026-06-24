"""
TDD — HITL drain no caminho supervisor (F5 2026-06-09).

Cobre:
1. sink vazio → drain retorna None
2. tool HITL → sink populado → drain retorna o dict
3. primeiro HITL do turno vence (second append ignorado)
4. reset_sink limpa entre turnos
5. resultado não-HITL não polui o sink
"""
import app.shared.hitl_pending_sink as sink


def _hitl_result(tool="close_job", domain="jobs"):
    return {
        "needs_confirmation": True,
        "hitl": {"tool": tool, "domain": domain},
        "message": "Confirmar?",
        "data": {"job_id": "abc"},
    }


def test_drain_empty():
    sink.reset_sink()
    assert sink.drain_sink() is None


def test_append_and_drain():
    sink.reset_sink()
    sink.append_from_result(_hitl_result())
    d = sink.drain_sink()
    assert d is not None
    assert d["tool"] == "close_job"
    assert d["domain"] == "jobs"
    # consumo único
    assert sink.drain_sink() is None


def test_first_wins():
    sink.reset_sink()
    sink.append_from_result(_hitl_result("t1", "d1"))
    sink.append_from_result(_hitl_result("t2", "d2"))
    assert sink.drain_sink()["tool"] == "t1"


def test_reset_clears_between_turns():
    sink.reset_sink()
    sink.append_from_result(_hitl_result())
    sink.reset_sink()  # novo turno
    assert sink.drain_sink() is None


def test_non_hitl_result_ignored():
    sink.reset_sink()
    sink.append_from_result({"success": True, "data": {}})
    assert sink.drain_sink() is None


def test_agentic_loop_return_includes_hitl_pending(monkeypatch):
    """Verifica que o dict retornado pelo agentic_loop inclui hitl_pending."""
    import importlib
    import app.orchestrator.execution.agentic_loop as al_mod
    # Apenas verifica que o campo existe nas constantes de retorno dos caminhos
    # success e max_iter, inspecionando o código-fonte.
    import inspect
    src = inspect.getsource(al_mod)
    assert '"hitl_pending": _hitl_pending_sink.drain_sink()' in src, (
        "Return path 'text response' deve incluir hitl_pending"
    )
    # Conta quantas vezes aparece (deve ser ≥2: success + max_iter)
    count = src.count('"hitl_pending": _hitl_pending_sink.drain_sink()')
    assert count >= 2, f"Esperado ≥2 drain calls, encontrado {count}"


def test_main_orchestrator_threads_hitl_pending():
    """Verifica que main_orchestrator.py passa hitl_pending ao ChatResponse."""
    import inspect
    import app.orchestrator.execution.main_orchestrator as mo_mod
    src = inspect.getsource(mo_mod)
    assert 'hitl_pending=_agentic_result.get("hitl_pending")' in src, (
        "ChatResponse do agentic_result deve incluir hitl_pending"
    )
