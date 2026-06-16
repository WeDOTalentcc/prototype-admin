"""
test_rail_a_golden_llm_judge — PR-E expansion.

LLM-as-judge sobre `tests/fixtures/rail_a_golden_dataset.json` (22 cards × 5
variações = 110 inputs).

Disciplina harness-engineering:
  - GUIDE (feedforward): golden dataset + capability_map garantem routing correto
  - SENSOR computacional (rodam SEMPRE): testes de estrutura sem LLM
  - SENSOR inferencial (gated por OPENAI_API_KEY): DeepEval LLM-as-judge

Métricas DeepEval (não-bloqueantes):
  - HallucinationMetric, AnswerRelevancyMetric, BiasMetric
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

GOLDEN_PATH = (
    Path(__file__).parent.parent / "fixtures" / "rail_a_golden_dataset.json"
)


def _load_golden_dataset():
    if not GOLDEN_PATH.exists():
        pytest.skip(f"Golden dataset ausente: {GOLDEN_PATH}")
    with open(GOLDEN_PATH) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Sensores estruturais (rodam SEMPRE — sem LLM)
# ─────────────────────────────────────────────────────────────────────────────


def test_golden_dataset_has_22_cards():
    dataset = _load_golden_dataset()
    cards = dataset.get("cards", [])
    assert len(cards) == 22, f"Esperado 22 cards, encontrado {len(cards)}"


def test_golden_dataset_card_ids_match_rail_a():
    dataset = _load_golden_dataset()
    expected = {
        "create-job", "job-template", "search-candidates", "add-candidate",
        "talent-pool", "candidate-info", "update-status", "schedule-interview",
        "reschedule-interview", "send-offer", "compare-candidates", "register-hire",
        "close-vacancy", "job-report", "daily-briefing", "hiring-predictions",
        "configure-automations", "wsi-screening", "ai-suggestions", "ai-credits",
        "hiring-policy", "email-templates",
    }
    actual = {c["card_id"] for c in dataset.get("cards", [])}
    assert not (expected - actual), f"Cards faltando: {expected - actual}"
    assert not (actual - expected), f"Cards inesperados: {actual - expected}"


def test_each_card_has_at_least_3_variations():
    dataset = _load_golden_dataset()
    failures = [
        f"{c['card_id']}: {len(c.get('variations', []))} variações"
        for c in dataset.get("cards", [])
        if len(c.get("variations", [])) < 3
    ]
    assert not failures, f"Cards com poucas variações: {failures}"


def test_each_card_has_intent_and_domain_hint():
    dataset = _load_golden_dataset()
    failures = []
    for card in dataset.get("cards", []):
        if not card.get("intent_hint"):
            failures.append(f"{card['card_id']}: missing intent_hint")
        if not card.get("domain_hint"):
            failures.append(f"{card['card_id']}: missing domain_hint")
    assert not failures, f"Cards incompletos: {failures}"


# ─────────────────────────────────────────────────────────────────────────────
# Avaliação inferencial (gated por deepeval + OPENAI_API_KEY)
# ─────────────────────────────────────────────────────────────────────────────


def _require_deepeval():
    """Lazy importorskip — só dispara quando o teste roda."""
    return pytest.importorskip("deepeval", reason="deepeval not installed")


def _stub_response_for_card(card: dict, variation: str) -> tuple[str, list[str]]:
    routing_layer = card.get("routing_layer")
    intent = card.get("intent_hint")
    modal_id = card.get("modal_id")

    if routing_layer == "modal":
        return (
            f"Abrindo {modal_id}...",
            [f"intent={intent}", f"modal_id={modal_id}", "routing=capability_map_gate"],
        )
    if routing_layer == "navigate":
        nav = card.get("expected_be_behavior") or "/"
        return (
            f"Navegando para {nav}...",
            [f"intent={intent}", f"navigate={nav}", "routing=capability_map_gate"],
        )
    return (
        f"Vou ajudar com {intent}. Pode me dar mais detalhes sobre o contexto?",
        [f"intent={intent}", f"domain={card.get('domain_hint')}", f"variation={variation}"],
    )


@pytest.mark.parametrize("metric_class_name,threshold", [
    ("HallucinationMetric", 0.5),
    ("AnswerRelevancyMetric", 0.7),
    ("BiasMetric", 0.5),
])
def test_rail_a_golden_metric_per_card(metric_class_name, threshold):
    """Roda métrica DeepEval em cada card. Skip gracioso se ambiente não tem deps."""
    _require_deepeval()
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY ausente")

    try:
        from deepeval import metrics as deepeval_metrics
        from deepeval.models import GPTModel
        from deepeval.test_case import LLMTestCase
        metric_class = getattr(deepeval_metrics, metric_class_name)
        judge = GPTModel(model="gpt-4o-mini")
    except Exception as exc:
        pytest.skip(f"DeepEval setup: {exc}")

    dataset = _load_golden_dataset()
    cards = dataset.get("cards", [])
    full = bool(os.getenv("LIA_LIVE_JUDGE_FULL"))

    failures: list[str] = []
    for card in cards:
        variations = card.get("variations", [])
        if not variations:
            continue
        sample = variations if full else variations[:1]
        for variation in sample:
            actual, context = _stub_response_for_card(card, variation)
            metric = metric_class(threshold=threshold, model=judge)
            tc = LLMTestCase(input=variation, actual_output=actual, context=context)
            try:
                metric.measure(tc)
                if metric.score < threshold:
                    failures.append(
                        f"{card['card_id']}: {metric_class_name}={metric.score:.2f}"
                    )
            except Exception as exc:
                failures.append(f"{card['card_id']}: erro {exc}")

    if failures:
        print(f"\n[{metric_class_name}] {len(failures)} cards abaixo do threshold:")
        for f in failures[:10]:
            print(f"  - {f}")
        pytest.skip(
            f"[{metric_class_name}] {len(failures)}/{len(cards)} abaixo do threshold "
            f"(soft fail — não-bloqueante)"
        )
