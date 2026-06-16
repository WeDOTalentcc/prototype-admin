"""User-simulator LLM for the agentic eval roteiro.

Plays the role of a recruiter following a YAML scenario script. Unlike a
hard-coded turn list, the simulator reacts to LIA's actual reply: if LIA
asks a clarifying question, the simulator answers from the scenario's
``persona`` block; if LIA proposes a navigation, the simulator decides
whether to consent based on ``persona.consent_policy``.

Modelled after τ-bench's user-simulator. Uses the same Anthropic model as
the judge for consistency.

Usage (from the Playwright runner via subprocess or shared HTTP):

    sim = UserSimulator(scenario)
    first = sim.opening_turn()  # the scenario's turn 1, verbatim
    while not sim.is_done():
        lia_reply = send_to_lia(first)
        next_user_msg = sim.respond_to(lia_reply)
        if next_user_msg is None:
            break
        first = next_user_msg

The simulator never invents data not present in the scenario — its
``system`` prompt forbids it. If LIA pushes for data outside the script,
the simulator says so and the scenario is judged on that.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SIMULATOR_MODEL = os.getenv("AGENTIC_SIMULATOR_MODEL", "claude-haiku-4-5-20251001")

SIMULATOR_SYSTEM = """\
You are a user-simulator for a QA suite. You ROLEPLAY a recruiter chatting
with LIA, an enterprise AI recruiting assistant. Your behaviour is
constrained by a JSON SCENARIO that contains:

  - persona: who you are pretending to be, and your consent policy
  - turns: a list of intended user messages, in order
  - facts_you_know: the only data you may share when LIA asks
  - facts_you_do_not_know: data you must refuse to invent if LIA asks
  - stop_when: condition that ends the conversation

Rules:
  1. Stay in character as the recruiter. Do not break the fourth wall.
  2. Speak Portuguese (PT-BR) unless the scenario's persona.language says
     otherwise.
  3. NEVER invent data. If LIA asks for something not in
     ``facts_you_know``, say "não sei" or "não tenho aqui" and ask LIA to
     proceed with what it has.
  4. Walk down ``turns`` in order. If LIA goes off-script (asks an
     unrelated question), answer briefly using ``persona`` then nudge
     LIA back to the next turn.
  5. If the scenario has consent prompts (D10), follow
     ``persona.consent_policy``: "always_yes", "always_no", or
     "ask_what_will_happen_first".
  6. When the conversation should end, output exactly the token
     ``[END]`` on its own line.

Output format: ONE message at a time. No JSON, no commentary. Just the
text the recruiter would type into the chat input.
"""


@dataclass
class SimulatorState:
    scenario: dict
    turn_index: int = 0
    history: list[dict] = field(default_factory=list)  # [{"role": "user"|"lia", "content": str}]
    finished: bool = False


class UserSimulator:
    """Drives one scenario from opening turn to ``[END]``."""

    def __init__(self, scenario: dict) -> None:
        self.state = SimulatorState(scenario=scenario)
        self._client = None
        if ANTHROPIC_API_KEY:
            try:
                import anthropic  # type: ignore
                self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except ImportError:
                self._client = None

    # ── public API ─────────────────────────────────────────────────────
    def opening_turn(self) -> str:
        """Return turn 1 verbatim — no LLM call needed."""
        turns = self.state.scenario.get("turns", [])
        if not turns:
            self.state.finished = True
            return ""
        text = turns[0]["user"]
        self.state.history.append({"role": "user", "content": text})
        self.state.turn_index = 1
        return text

    def respond_to(self, lia_reply: str) -> str | None:
        """Append LIA's reply to history and produce the next user message.

        Returns ``None`` when the scenario is finished (either ``[END]``
        was emitted or all scripted turns were consumed *and* LIA has
        nothing more to ask).
        """
        if self.state.finished:
            return None
        self.state.history.append({"role": "lia", "content": lia_reply})

        scripted = self._next_scripted_turn()
        if self._client is None:
            # No LLM — fall back to scripted only
            if scripted is None:
                self.state.finished = True
                return None
            self.state.history.append({"role": "user", "content": scripted})
            return scripted

        # Ask the LLM to either play the scripted turn (if LIA stayed
        # on-track) or improvise within the rules.
        text = self._call_llm(scripted_hint=scripted)
        if text.strip() == "[END]" or not text.strip():
            self.state.finished = True
            return None
        self.state.history.append({"role": "user", "content": text})
        return text

    def is_done(self) -> bool:
        return self.state.finished

    def transcript(self) -> list[dict]:
        return list(self.state.history)

    # ── internals ──────────────────────────────────────────────────────
    def _next_scripted_turn(self) -> str | None:
        turns = self.state.scenario.get("turns", [])
        if self.state.turn_index >= len(turns):
            return None
        text = turns[self.state.turn_index]["user"]
        self.state.turn_index += 1
        return text

    def _call_llm(self, scripted_hint: str | None) -> str:
        history_for_llm = [
            {"role": "assistant" if h["role"] == "user" else "user", "content": h["content"]}
            for h in self.state.history
        ]
        scenario_view = {
            "persona": self.state.scenario.get("persona", {}),
            "facts_you_know": self.state.scenario.get("facts_you_know", {}),
            "facts_you_do_not_know": self.state.scenario.get("facts_you_do_not_know", []),
            "stop_when": self.state.scenario.get("stop_when", "all turns consumed"),
            "next_scripted_turn": scripted_hint,
        }
        user_block = (
            "SCENARIO:\n" + json.dumps(scenario_view, ensure_ascii=False, indent=2)
            + "\n\nProduce the recruiter's next chat message. Output ONLY the message text."
        )
        try:
            msg = self._client.messages.create(  # type: ignore[union-attr]
                model=SIMULATOR_MODEL,
                max_tokens=400,
                temperature=0.3,
                system=SIMULATOR_SYSTEM,
                messages=history_for_llm + [{"role": "user", "content": user_block}],
            )
            return msg.content[0].text.strip()
        except Exception as exc:  # pragma: no cover
            return f"[SIMULATOR_ERROR: {exc}]"


def load_scenario(path: str) -> dict:
    """Load a YAML scenario file."""
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
