"""Sensor P1-1 tail — builder f11 (reports.py) opera em escala 0-10.

O f11 le scores armazenados (0-10 pelo produtor TriagemSessionService). Pina:
(1) as constantes de gate em 0-10 (G3=4.0 via wsi_scale, G4=3.0);
(2) o comportamento de _compute_decision_confidence em entradas 0-10
    (incl. o threshold de variancia 4.0 — antes 2.0 em /5).
Regressao p/ 0-5 quebra estes testes.
"""
from app.api.v1.wsi.reports import (
    _GATE_G3_THRESHOLD,
    _GATE_G4_THRESHOLD,
    _compute_decision_confidence,
)


def test_gate_thresholds_are_0_10_scale():
    assert _GATE_G3_THRESHOLD == 4.0, "G3 deve ser o canonico 0-10 (wsi_scale=4.0), nao 0-5 (2.0)"
    assert _GATE_G4_THRESHOLD == 3.0, "G4 deve ser 0-10 (3.0), nao 0-5 (1.5)"


def test_decision_confidence_high_only_at_excepcional():
    # >= 9.0 e sem gates -> alta confianca
    assert _compute_decision_confidence(9.5, [], 0, 1.0) == ("alta", False)
    # 8.0 (excelente, mas < 9.0) -> media/sem review
    assert _compute_decision_confidence(8.0, [], 0, 1.0) == ("media", False)


def test_decision_confidence_review_band_0_10():
    # 6.0–7.49 -> media + human review
    conf, review = _compute_decision_confidence(6.5, [], 0, 1.0)
    assert conf == "media" and review is True
    # < 7.5 sem gates -> media + review (fallback final)
    conf, review = _compute_decision_confidence(5.0, [], 0, 1.0)
    assert conf == "media" and review is True


def test_variance_threshold_is_0_10():
    # amplitude 5.0 (> 4.0) -> baixa confianca + review
    assert _compute_decision_confidence(8.0, [], 0, 5.0) == ("baixa", True)
    # amplitude 3.0 NAO dispara (em /5 antigo 3.0 > 2.0 dispararia) -> pina o x2
    conf, review = _compute_decision_confidence(8.0, [], 0, 3.0)
    assert conf == "media" and review is False


def test_clear_reject_gate_high_confidence():
    # gate de rejeicao clara (G3) -> alta confianca na decisao de reprovar
    assert _compute_decision_confidence(8.0, ["G3"], 0, 1.0) == ("alta", False)
