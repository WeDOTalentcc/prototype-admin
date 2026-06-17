"""Sensor (audit C10/#10 2026-06-05): WSI question-gen tem denominador + bias-block.

Antes: so existia o NUMERADOR (inc_wsi_fallback). Sem total gerado nem first-shot,
o fallback/retry rate ficava sem base — impossivel dizer se 10 fallbacks/dia e 1%
ou 50%. Adiciona:
  - wsi_questions_generated_total{framework, outcome=first_shot|retried|manual_review}
  - wsi_bias_block_total{framework}  (bias_marker_detected em _validate_deterministic)

Inclui um sensor de WIRING (source-level): helper que existe mas nao e chamado e
helper morto — denominador continua sem base (cf. regra "wiring end-to-end").
"""
import importlib.util
from pathlib import Path

import pytest

from app.shared.observability import fallback_metrics as fm

_HAS_PROM = importlib.util.find_spec("prometheus_client") is not None

ROOT = Path(__file__).resolve().parents[2]  # .../lia-agent-system
GEN_SRC = (
    ROOT / "app" / "domains" / "cv_screening" / "services" / "wsi_service"
    / "question_generator.py"
).read_text(encoding="utf-8")


def _v(name, **labels):
    from prometheus_client import REGISTRY
    return REGISTRY.get_sample_value(name, labels) or 0.0


@pytest.mark.skipif(not _HAS_PROM, reason="prometheus_client ausente")
def test_inc_wsi_generated_increments():
    before = _v("wsi_questions_generated_total", framework="CBI", outcome="first_shot")
    fm.inc_wsi_generated("CBI", "first_shot")
    after = _v("wsi_questions_generated_total", framework="CBI", outcome="first_shot")
    assert after == before + 1


@pytest.mark.skipif(not _HAS_PROM, reason="prometheus_client ausente")
def test_inc_wsi_generated_bad_outcome_is_skipped():
    # label fora da allow-list -> skip silencioso (fail-open), nunca levanta
    fm.inc_wsi_generated("CBI", "bogus_outcome")


@pytest.mark.skipif(not _HAS_PROM, reason="prometheus_client ausente")
def test_inc_wsi_bias_block_increments():
    before = _v("wsi_bias_block_total", framework="Dreyfus")
    fm.inc_wsi_bias_block("Dreyfus")
    after = _v("wsi_bias_block_total", framework="Dreyfus")
    assert after == before + 1


def test_generator_wires_denominator_and_bias():
    assert "inc_wsi_generated(" in GEN_SRC, (
        "question_generator.py NAO chama inc_wsi_generated — denominador do "
        "fallback/retry rate fica sem base (helper morto). "
        "-> Fix: chamar inc_wsi_generated(_framework_label, outcome) em cada return "
        "de _generate_validated_question."
    )
    assert "inc_wsi_bias_block(" in GEN_SRC, (
        "question_generator.py NAO chama inc_wsi_bias_block — bias_marker_detected "
        "do _validate_deterministic nao e instrumentado. "
        "-> Fix: inc_wsi_bias_block(_framework_label) quando 'bias_marker_detected' em det_flags."
    )
