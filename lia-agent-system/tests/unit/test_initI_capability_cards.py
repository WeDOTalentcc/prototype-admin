"""Initiative I.A (2026-04-21) — Grounded Capability Cards catalog.

Closes chat gap: LIA responded "o que você sabe fazer?" with free-prose bullets
including hallucinated capabilities (prevejo tempo até fechar, calculo taxas
de conversão) — no tools backed those claims.

Source of truth: `app/prompts/catalog/capability_cards.yaml`.

Invariants enforced by this test file (becomes CI guard via ci-audit-gate.yml):
  - YAML parses
  - Each capability has required fields (id, title, user_phrasing, tools,
    example_input, example_output)
  - Every tool referenced by any card MUST exist in the live tool_registry
    (no phantom/hallucinated capabilities)
  - No duplicate IDs
  - version metadata present
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


CATALOG_REL = "app/prompts/catalog/capability_cards.yaml"

REQUIRED_FIELDS = {"id", "title", "user_phrasing", "tools", "example_input", "example_output"}


def _find_catalog() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / CATALOG_REL
        if cand.exists():
            return cand
    raise RuntimeError(f"{CATALOG_REL} not found")


def _load() -> dict:
    return yaml.safe_load(_find_catalog().read_text(encoding="utf-8"))


def test_catalog_parses_and_has_version() -> None:
    """I.A: capability_cards.yaml must parse + have version metadata."""
    data = _load()
    assert isinstance(data, dict)
    assert data.get("version") == 1, "I.A: catalog must declare version: 1"
    assert "capabilities" in data and isinstance(data["capabilities"], list)
    assert len(data["capabilities"]) >= 10, (
        "I.A: catalog should have at least 10 capabilities to cover common workflows"
    )


def test_every_card_has_required_fields() -> None:
    """I.A: each card must have id/title/user_phrasing/tools/example_input/example_output."""
    data = _load()
    offences: list[str] = []
    for i, card in enumerate(data["capabilities"]):
        missing = REQUIRED_FIELDS - set(card.keys())
        if missing:
            offences.append(f"card[{i}] id={card.get('id', '?')} missing: {sorted(missing)}")
    assert not offences, "I.A required fields:\n  " + "\n  ".join(offences)


def test_no_duplicate_ids() -> None:
    """I.A: card IDs must be unique."""
    data = _load()
    ids = [c["id"] for c in data["capabilities"]]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"I.A: duplicate card IDs: {duplicates}"


def test_every_card_tool_exists_in_runtime_registry() -> None:
    """I.A CORE INVARIANT: every tool referenced by a card must be registered.

    This is the anti-hallucination guard — if a card claims LIA can do X via
    tool Y, tool Y must actually be callable in the live system.

    Triggers all tool registration imports so tool_registry is populated.
    """
    # Force-load tool modules to populate the registry
    from app.tools.registry import tool_registry

    # Use the canonical init path used by uvicorn startup
    from app.tools import initialize_tools
    initialize_tools()

    registered = set(tool_registry.list_tools())
    assert len(registered) > 0, "I.A prerequisite: tool_registry must be populated"

    data = _load()
    offences: list[str] = []
    for card in data["capabilities"]:
        tools = card.get("tools", [])
        for t in tools:
            if t not in registered:
                offences.append(
                    f"card id={card['id']!r} references tool {t!r} — NOT in tool_registry"
                )

    assert not offences, (
        "I.A hallucination guard: these cards reference tools not in live "
        "registry. Either the tool name is wrong, the tool isn't registered "
        "yet (wire it), or remove the card. Do NOT advertise capabilities "
        "without real tool backing:\n  " + "\n  ".join(offences)
    )


def test_user_phrasing_not_empty() -> None:
    """I.A UX: each card must have at least one natural-language trigger."""
    data = _load()
    for card in data["capabilities"]:
        phrasing = card.get("user_phrasing", [])
        assert isinstance(phrasing, list) and len(phrasing) >= 1, (
            f"I.A: card id={card['id']!r} must have ≥1 user_phrasing entry"
        )


def test_metadata_block_present() -> None:
    """I.A traceability: metadata block with initiative ref must be present."""
    data = _load()
    md = data.get("metadata", {})
    assert "I.A" in str(md.get("initiative", ""))
    assert "roadmap" in str(md.get("reference", "")).lower() or "LIA_MATURITY" in str(md)
