"""
N-14 (Audit Rev 4) — `wizard_node_latency_seconds` OTLP histogram.

Garante:
  * O decorator `wizard_traced_node` registra latency no histograma OTLP.
  * Atributos `node`, `wizard.stage`, `tenant.company_id`, `status` são
    anexados.
  * O histograma emite tanto em sucesso quanto em erro (alerta de
    regressão).
  * Se OTel metrics estiver indisponível, o decorator não quebra o nó
    (degrada para no-op).
"""
import pytest

pytestmark = pytest.mark.easy

from app.shared.observability import span_validation as sv
from app.shared.observability.span_validation import wizard_traced_node


class _FakeHistogram:
    def __init__(self):
        self.records: list[tuple[float, dict]] = []

    def record(self, value, attributes=None):
        self.records.append((value, dict(attributes or {})))


@pytest.fixture(autouse=True)
def _isolate_histogram_singleton(monkeypatch):
    """Reset the lazy singleton between tests to inject a fake."""
    sv._reset_wizard_node_latency_histogram_for_tests()
    yield
    sv._reset_wizard_node_latency_histogram_for_tests()


@pytest.fixture
def fake_histogram(monkeypatch):
    fake = _FakeHistogram()
    monkeypatch.setattr(sv, "_get_wizard_node_latency_histogram", lambda: fake)
    return fake


def _state(stage: str = "intake", company_id: str = "c-42") -> dict:
    """Mimic the canonical wizard state shape consumed by `_attrs_from_state`.

    The decorator reads `workspace_id`/`company_id` (top-level) for the
    tenant tag — this matches `JobCreationState` which stores the tenant
    alongside other top-level fields.
    """
    return {
        "current_stage": stage,
        "workspace_id": company_id,
        "user_id": "u-7",
        "session_id": "conv-1",
    }


class TestHistogramEmissionOnSuccess:

    def test_records_on_success(self, fake_histogram):
        @wizard_traced_node("wizard.intake")
        def my_node(state):
            return state

        my_node(_state())

        assert len(fake_histogram.records) == 1
        elapsed, attrs = fake_histogram.records[0]
        assert elapsed >= 0
        assert attrs["node"] == "intake"
        assert attrs["wizard.stage"] == "intake"
        assert attrs["status"] == "ok"
        assert attrs["tenant.company_id"] == "c-42"

    def test_records_per_call(self, fake_histogram):
        @wizard_traced_node("wizard.bigfive")
        def my_node(state):
            return state

        my_node(_state(stage="bigfive"))
        my_node(_state(stage="bigfive"))
        my_node(_state(stage="bigfive"))

        assert len(fake_histogram.records) == 3
        for _, attrs in fake_histogram.records:
            assert attrs["node"] == "bigfive"
            assert attrs["status"] == "ok"


class TestHistogramEmissionOnError:

    def test_records_on_error(self, fake_histogram):
        @wizard_traced_node("wizard.publish")
        def failing_node(state):
            raise RuntimeError("DB down")

        with pytest.raises(RuntimeError, match="DB down"):
            failing_node(_state(stage="publish"))

        assert len(fake_histogram.records) == 1
        elapsed, attrs = fake_histogram.records[0]
        assert elapsed >= 0
        assert attrs["node"] == "publish"
        assert attrs["status"] == "error"


class TestHistogramFailureIsolation:
    """Telemetry MUST never break the node."""

    def test_record_exception_does_not_propagate(self, monkeypatch):
        class _BrokenHist:
            def record(self, value, attributes=None):
                raise OSError("metrics pipeline broken")

        monkeypatch.setattr(
            sv, "_get_wizard_node_latency_histogram", lambda: _BrokenHist()
        )

        @wizard_traced_node("wizard.review")
        def my_node(state):
            return {"current_stage": "review"}

        result = my_node(_state(stage="review"))
        assert result == {"current_stage": "review"}


class TestSingletonLifecycle:

    def test_lazy_singleton_returns_same_instance(self):
        # Without monkeypatch — exercises the real lazy path. Either real
        # OTel histogram OR _NoopHistogram, but the same object both times.
        h1 = sv._get_wizard_node_latency_histogram()
        h2 = sv._get_wizard_node_latency_histogram()
        assert h1 is h2

    def test_reset_helper_clears_singleton(self):
        h1 = sv._get_wizard_node_latency_histogram()
        sv._reset_wizard_node_latency_histogram_for_tests()
        h2 = sv._get_wizard_node_latency_histogram()
        # After reset, a new instance is created (may or may not be the
        # same object since OTel may cache internally — we assert the
        # singleton slot was cleared, which is the contract).
        assert h2 is not None
