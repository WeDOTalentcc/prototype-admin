"""Fix do gate de crédito no streaming async (2026-06-04).

O cliente async hit o gate SYNC em _patched_stream → RuntimeError no event loop
→ LLM falha → 0 tools. Fix: gate enforçado ASYNC no __aenter__ do reconciler
quando gate_kwargs é passado (caminho async). Sync inalterado. Budget preservado.
"""
import asyncio
import app.shared.llm_bootstrap as bootstrap
from app.shared.llm_bootstrap import _AnthropicStreamReconciler


class _FakeInner:
    async def get_final_message(self):
        return None  # actual=0 → sem reconcile


class _FakeCM:
    async def __aenter__(self):
        return _FakeInner()

    async def __aexit__(self, *a):
        return False


def test_async_reconciler_enforces_gate_on_aenter(monkeypatch):
    called = {"gate": False}

    async def fake_gate(provider, kwargs, *, estimator):
        called["gate"] = True

    monkeypatch.setattr(bootstrap, "_enforce_credit_gate_async", fake_gate)
    rec = _AnthropicStreamReconciler(
        _FakeCM(), "co-1", 10, "anthropic",
        gate_kwargs={"model": "x", "messages": []},
    )

    async def run():
        async with rec as inner:
            assert inner is not None

    asyncio.run(run())
    assert called["gate"], "gate async deve rodar no __aenter__ quando gate_kwargs presente"


def test_sync_path_no_async_gate(monkeypatch):
    called = {"gate": False}

    async def fake_gate(*a, **k):
        called["gate"] = True

    monkeypatch.setattr(bootstrap, "_enforce_credit_gate_async", fake_gate)
    rec = _AnthropicStreamReconciler(_FakeCM(), "co", 0, "anthropic")  # sem gate_kwargs

    async def run():
        async with rec:
            pass

    asyncio.run(run())
    assert not called["gate"], "sem gate_kwargs (caminho sync) não enforça gate async"
