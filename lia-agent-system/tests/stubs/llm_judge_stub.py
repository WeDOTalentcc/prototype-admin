"""
tests/stubs/llm_judge_stub.py

LLM-as-judge stub for Rail A routing evaluation — Wave 4 W4-1.

harness-engineering [sensor inferencial]:
  Evaluates whether each Rail A card variation actually reaches the
  correct intent in a full LLM call. Skipped in CI (requires real LLM).
  Run manually: pytest tests/stubs/llm_judge_stub.py -v -s

Usage:
  ANTHROPIC_API_KEY=... pytest tests/stubs/llm_judge_stub.py --no-skip

Judge rubric (per variation):
  - CORRECT:   LLM classifies to the expected domain + intent
  - PLAUSIBLE: LLM classifies to an adjacent domain, not exact intent
  - WRONG:     LLM classifies to a completely different domain

Acceptance threshold: >= 90% CORRECT across all 110 variations.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

GOLDEN_DATASET_PATH = (
    Path(__file__).parent.parent / "fixtures" / "rail_a_golden_dataset.json"
)

_SKIP_REASON = (
    "LLM-as-judge requires ANTHROPIC_API_KEY and --no-skip flag. "
    "Run manually: ANTHROPIC_API_KEY=... pytest tests/stubs/llm_judge_stub.py --no-skip -v"
)


def _should_skip() -> bool:
    return (
        not os.getenv("ANTHROPIC_API_KEY")
        or "--no-skip" not in os.sys.argv  # type: ignore[attr-defined]
    )


@pytest.fixture(scope="module")
def golden_dataset() -> dict:
    return json.loads(GOLDEN_DATASET_PATH.read_text())


@pytest.fixture(scope="module")
def judge_client():
    """Returns Anthropic client if available, else None."""
    if _should_skip():
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    except ImportError:
        return None


@pytest.mark.skipif(_should_skip(), reason=_SKIP_REASON)
class TestLLMJudgeRouting:
    """LLM-as-judge: verifies that each variation reaches the correct intent.

    How it works:
      1. Sends each variation as a user message to Claude claude-haiku-4-5 (cheapest).
      2. Asks the model to classify to (domain, intent) from a fixed list.
      3. Checks that the classification matches expected_be_behavior.domain + intent_hint.

    Skipped in CI. Run manually or in a scheduled nightly job.
    """

    def test_all_110_variations_correct_routing(self, golden_dataset, judge_client):
        assert judge_client is not None, "ANTHROPIC_API_KEY required"
        dataset = golden_dataset

        # Build known intents from dataset
        known_intents = {
            c["intent_hint"]: c["domain_hint"]
            for c in dataset["cards"]
            if c.get("intent_hint") and c.get("domain_hint")
        }

        system_prompt = f"""You are a routing classifier for a recruitment platform.
Given a user message, classify it to one of these (domain, intent) pairs:
{json.dumps(known_intents, indent=2)}

Respond with ONLY a JSON object: {{"domain": "...", "intent": "..."}}
If no match, respond: {{"domain": "unknown", "intent": "unknown"}}"""

        results = {"correct": 0, "plausible": 0, "wrong": 0, "total": 0}
        failures = []

        for card in dataset["cards"]:
            # Only test chat_cap_map and chat_llm_fallback cards (BE sees them)
            if card["routing_layer"] not in ("chat_cap_map", "chat_llm_fallback"):
                continue

            expected_intent = card.get("intent_hint", "")
            expected_domain = card.get("domain_hint", "")

            for variation in card.get("variations", []):
                results["total"] += 1
                try:
                    response = judge_client.messages.create(
                        model="claude-haiku-4-5",
                        max_tokens=100,
                        system=system_prompt,
                        messages=[{"role": "user", "content": variation}],
                    )
                    classified = json.loads(response.content[0].text)
                    got_intent = classified.get("intent", "unknown")
                    got_domain = classified.get("domain", "unknown")

                    if got_intent == expected_intent:
                        results["correct"] += 1
                    elif got_domain == expected_domain:
                        results["plausible"] += 1
                        failures.append(
                            f"PLAUSIBLE card={card['card_id']!r} "
                            f"expected={expected_intent!r} got={got_intent!r}: {variation!r}"
                        )
                    else:
                        results["wrong"] += 1
                        failures.append(
                            f"WRONG card={card['card_id']!r} "
                            f"expected=({expected_domain!r},{expected_intent!r}) "
                            f"got=({got_domain!r},{got_intent!r}): {variation!r}"
                        )
                except Exception as e:
                    results["wrong"] += 1
                    failures.append(f"ERROR card={card['card_id']!r}: {e}: {variation!r}")

        if results["total"] == 0:
            pytest.skip("No chat cards to evaluate")

        pct_correct = results["correct"] / results["total"] * 100
        print(f"\nLLM Judge results: {results}")
        if failures:
            print("\nFailures:")
            for f in failures[:10]:
                print(f"  {f}")

        assert pct_correct >= 90.0, (
            f"LLM routing accuracy {pct_correct:.1f}% below 90% threshold. "
            f"Results: {results}. "
            "Improve intent keywords in capability_map.yaml or orchestrator prompts."
        )
