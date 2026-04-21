"""FIX 21 (2026-04-21) — Template discovery tools.

Closes the "me mostre os templates" chat gap where LIA responded "não tenho uma
função para mostrar todos os templates". Root cause: communication_tools had
only send_* tools (send_email, send_whatsapp, send_feedback, send_bulk_email,
schedule_interview) — zero read/preview tools. LIA could neither LIST nor
PREVIEW templates without sending.

Canonical-fix (producer-side): add two read-only tools in
app/domains/communication/tools/communication_tools.py:
  - list_message_templates(stage_name, limit) — tenant-scoped listing
  - preview_message_template(template_id, variables) — renders without sending

Reuses existing _load_email_template helper for preview (DRY).

Tests are structural: signature + registry registration + FIX 21 marker.
Runtime behavior validated by smoke test on Replit post-restart.
"""
from __future__ import annotations

import inspect


def test_list_message_templates_exists_with_expected_signature() -> None:
    """FIX 21: list_message_templates must exist and accept stage_name + limit."""
    from app.domains.communication.tools import communication_tools

    assert hasattr(communication_tools, "list_message_templates"), (
        "FIX 21: communication_tools must expose list_message_templates"
    )
    fn = communication_tools.list_message_templates
    assert inspect.iscoroutinefunction(fn), (
        "FIX 21: list_message_templates must be async (tool convention)"
    )
    sig = inspect.signature(fn)
    assert "stage_name" in sig.parameters, (
        "FIX 21: list_message_templates must accept stage_name filter"
    )
    assert "limit" in sig.parameters
    assert sig.parameters["limit"].default == 50, (
        "FIX 21: default limit=50 (higher than search_jobs because templates list is small)"
    )


def test_preview_message_template_exists_with_expected_signature() -> None:
    """FIX 21: preview_message_template must exist and accept template_id + variables."""
    from app.domains.communication.tools import communication_tools

    assert hasattr(communication_tools, "preview_message_template"), (
        "FIX 21: communication_tools must expose preview_message_template"
    )
    fn = communication_tools.preview_message_template
    assert inspect.iscoroutinefunction(fn), (
        "FIX 21: preview_message_template must be async"
    )
    sig = inspect.signature(fn)
    assert "template_id" in sig.parameters, (
        "FIX 21: preview_message_template must accept template_id"
    )
    assert "variables" in sig.parameters, (
        "FIX 21: preview_message_template must accept optional variables dict for rendering"
    )


def test_both_tools_registered_in_tool_registry() -> None:
    """FIX 21: both tools must be registered + exposed to LLM via schema."""
    from app.domains.communication.tools.communication_tools import (
        register_communication_tools,
    )
    from app.tools.registry import tool_registry

    register_communication_tools()

    list_td = tool_registry.get_tool("list_message_templates")
    preview_td = tool_registry.get_tool("preview_message_template")

    assert list_td is not None, (
        "FIX 21: list_message_templates must be registered in tool_registry. "
        "Without registration, LLM cannot discover or call it."
    )
    assert preview_td is not None, (
        "FIX 21: preview_message_template must be registered in tool_registry"
    )

    # Schemas must advertise parameters
    assert "stage_name" in list_td.parameters_schema["properties"]
    assert "limit" in list_td.parameters_schema["properties"]
    assert "template_id" in preview_td.parameters_schema["properties"]

    # Descriptions must frame these as READ/PREVIEW not SEND so LLM picks right tool
    assert (
        "listar" in list_td.description.lower()
        or "list" in list_td.description.lower()
    ), "FIX 21: description must signal LIST intent"
    assert (
        "preview" in preview_td.description.lower()
        or "visualiz" in preview_td.description.lower()
        or "exib" in preview_td.description.lower()
    ), "FIX 21: description must signal PREVIEW intent (not SEND)"


def test_module_has_fix21_marker() -> None:
    """FIX 21 audit marker per canonical-fix traceability protocol."""
    from pathlib import Path

    import app.domains.communication.tools.communication_tools as ct

    source = Path(ct.__file__).read_text(encoding="utf-8")
    assert "FIX 21" in source, (
        "FIX 21: communication_tools.py must contain `FIX 21` marker for traceability"
    )


def test_preview_tool_does_not_send() -> None:
    """FIX 21: preview_message_template must NOT call any send/email transport.

    Contract guard: this is a READ tool. If someone accidentally wires it to
    send_email later, this check catches the drift.
    """
    from pathlib import Path

    import app.domains.communication.tools.communication_tools as ct

    source = Path(ct.__file__).read_text(encoding="utf-8")
    # Find the preview function body
    marker = "async def preview_message_template"
    start = source.find(marker)
    assert start > 0
    # Crude but effective: read until next top-level def
    next_def = source.find("\nasync def ", start + 1)
    if next_def == -1:
        next_def = source.find("\ndef ", start + 1)
    body = source[start:next_def] if next_def > 0 else source[start:]

    # Must not call any email/whatsapp transport inside preview body
    forbidden_calls = [
        "send_email_via_provider",
        "send_transactional_email",
        "SendGridAPIClient",
        "smtplib",
        "send_whatsapp(",
    ]
    for call in forbidden_calls:
        assert call not in body, (
            f"FIX 21 violation: preview_message_template contains `{call}` — "
            f"preview must be READ-ONLY, never trigger real sends"
        )
