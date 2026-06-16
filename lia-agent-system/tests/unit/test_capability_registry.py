"""Sprint 3 — capability registry canonical contract tests.

Covers:
  1. ToolDefinition has category field with default OTHER
  2. ToolRegistry.register populates category from TOOL_TO_CATEGORY
  3. ToolRegistry.get_tools_by_category groups deterministically
  4. SystemPromptBuilder G6 section is derived (no hardcoded category strings
     in the source that aren't either in CATEGORY_TAGLINES or in the
     literal NL examples block)
  5. SystemPromptBuilder G3 section enumerates ALL CanonicalPage entries
     except GENERAL
"""
from __future__ import annotations

import pytest

from app.shared.canonical_pages import CanonicalPage, PAGE_SHORT_LABELS_PT_BR
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
from app.tools.categories import (
    CATEGORY_TAGLINES,
    DISPLAY_ORDER,
    TOOL_TO_CATEGORY,
    ToolCategory,
    category_for_tool,
)
from app.tools.registry import ToolDefinition, tool_registry


@pytest.fixture(autouse=True, scope="module")
def _init_tools():
    """Ensure tools are registered before the suite runs."""
    from app.tools import initialize_tools
    initialize_tools()


# ---------- Sprint 3.1: ToolDefinition has category --------------------------

def test_tool_definition_has_category_default():
    td = ToolDefinition(
        name="x", description="d", parameters_schema={},
        handler=lambda **kw: None,
    )
    assert td.category == "OTHER"


def test_tool_definition_accepts_category_kwarg():
    td = ToolDefinition(
        name="x", description="d", parameters_schema={},
        handler=lambda **kw: None,
        category=ToolCategory.VAGAS,
    )
    assert td.category == "VAGAS"


# ---------- Sprint 3.2: registry auto-populates category ---------------------

def test_category_for_tool_returns_other_for_unknown():
    assert category_for_tool("nonexistent_tool_xyz") == "OTHER"


def test_category_for_tool_returns_canonical_for_mapped():
    assert category_for_tool("search_jobs") == ToolCategory.VAGAS
    assert category_for_tool("send_email") == ToolCategory.COMUNICACAO
    assert category_for_tool("get_pipeline_stats") == ToolCategory.ANALYTICS


def test_registered_tools_have_canonical_category():
    """No registered tool may be in OTHER — Sprint 3 invariant."""
    other = sorted(
        t.name for t in tool_registry._tools.values() if t.category == "OTHER"
    )
    assert other == [], (
        f"{len(other)} tools without canonical category — add them to "
        f"TOOL_TO_CATEGORY: {other}"
    )


# ---------- Sprint 3.2: registry groups deterministically --------------------

def test_get_tools_by_category_returns_sorted_within_category():
    grouped = tool_registry.get_tools_by_category()
    for cat, tools in grouped.items():
        names = [t.name for t in tools]
        assert names == sorted(names), (
            f"category {cat} not sorted: {names}"
        )


def test_get_tools_by_category_covers_all_registered():
    grouped = tool_registry.get_tools_by_category()
    flat = [t.name for tools in grouped.values() for t in tools]
    registered = set(tool_registry._tools.keys())
    assert set(flat) == registered, "tools dropped between registry and grouping"


# ---------- Sprint 3.3: builder derives G6 from registry ---------------------

def _build_prompt(context_page: str = "vagas") -> str:
    return SystemPromptBuilder.build(
        agent_type="orchestrator",
        tenant_context_snippet="",
        user_name="Paulo",
        user_role="recruiter",
        conversation_summary="",
        conversation_history=None,
        context_page=context_page,
    )


def test_g6_prompt_contains_every_used_category_header():
    """Each category with > 0 tools must appear as **<NAME>** in the prompt."""
    prompt = _build_prompt()
    grouped = tool_registry.get_tools_by_category()
    for cat in DISPLAY_ORDER:
        if grouped.get(cat):
            assert f"**{cat}**:" in prompt, f"missing category header: {cat}"


def test_g6_prompt_contains_every_registered_tool_name():
    """Every registered tool name must appear in the rendered prompt."""
    prompt = _build_prompt()
    for tool_name in tool_registry._tools.keys():
        assert tool_name in prompt, f"tool name missing from G6 prompt: {tool_name}"


def test_g6_does_not_hardcode_tool_lists_in_builder_source():
    """Sentinel: builder source must not contain a hardcoded
    `(create_job, publish_job, ...)` parenthesised list — that pattern is
    the pre-Sprint-3 antipattern. Categories must be derived.
    """
    import inspect

    src = inspect.getsource(SystemPromptBuilder.build)
    # The OLD hardcoded marker was strings like
    #   "create_job, publish_job, pause_job, close_job, update_job, search_jobs"
    forbidden = [
        "create_job, publish_job, pause_job, close_job, update_job, search_jobs",
        "search_candidates, compare_candidates, analyze_cv_match",
        "send_email, send_bulk_email, send_whatsapp",
    ]
    for snippet in forbidden:
        assert snippet not in src, (
            f"pre-Sprint-3 hardcoded tool list still present in builder: {snippet}"
        )


# ---------- Sprint 3.3: builder derives G3 from CanonicalPage ----------------

def test_g3_prompt_contains_every_canonical_page_except_general():
    prompt = _build_prompt()
    for page in CanonicalPage:
        if page.value == "general":
            continue
        # Format expected: "- `<value>` → <label>"
        marker = f"- `{page.value}`"
        assert marker in prompt, f"canonical page missing from G3: {page.value}"


def test_g3_uses_short_labels_not_long_descriptions():
    """G3 nav list should be compact — use PAGE_SHORT_LABELS_PT_BR, not
    PAGE_DESCRIPTIONS_PT_BR which is contextual sentence form."""
    prompt = _build_prompt()
    # Long contextual phrases must NOT appear in the G3 nav list — they'd
    # bloat the prompt and confuse the LLM.
    forbidden_phrases = [
        "O usuário está na página inicial",
        "O usuário está na página de Vagas",
    ]
    # Find the nav block boundaries
    start = prompt.find("Páginas canonical disponíveis:")
    end = prompt.find("Exemplo:", start)
    nav_block = prompt[start:end] if start >= 0 and end > start else ""
    for phrase in forbidden_phrases:
        assert phrase not in nav_block, (
            f"long contextual description leaked into G3 nav block: {phrase}"
        )


# ---------- Sprint 3.4 invariant: NO tool in OTHER --------------------------

def test_sprint3_no_tool_in_other():
    """Hard contract — the sensor enforces this in CI; the test pins it locally."""
    other = [
        t.name for t in tool_registry._tools.values() if t.category == "OTHER"
    ]
    assert other == [], (
        f"Sprint 3 invariant broken — {len(other)} tools in OTHER. "
        f"Add them to TOOL_TO_CATEGORY in app/tools/categories.py: {other}"
    )
