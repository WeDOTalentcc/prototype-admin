"""Contract sentinel — Bug A2 (schema drift between IntakeExtractor and intake_node).

Origin: docs/audits/wizard-job-creation-2026-05.md §5.1, fix 2026-05-15.

Bug A2 was: ``graph.py::intake_node`` consumed ``extraction.parsed_title``,
``.parsed_seniority``, ``.parsed_department``, ``.parsed_location``,
``.parsed_model``, ``.confidence``, ``.source`` directly. But
``IntakeExtractor.extract()`` returns a ``JobIntakePayload`` whose interface
is ``.title.value``, ``.title.source``, ``.work_model.value``,
``.overall_confidence``. The mismatch was swallowed by the ``try/except``
fail-open in ``intake_node`` and ``parsed_title`` was NEVER set, cascading
into the input-thin guard always firing and the LIA replying the same canned
template 4× to varied inputs (user-reported 2026-05-15).

These tests guard against re-introduction by asserting the canonical contract:
  1. JobIntakePayload exposes the fields ``intake_node`` reads (positive).
  2. JobIntakePayload does NOT expose the legacy ``parsed_*`` attributes
     (anti-pattern — would cause silent fail-open AttributeError if read).
  3. ``intake_node`` source code does NOT reference the legacy attribute
     names (AST-level static guard).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.domains.job_creation.services.intake_extractor import (
    IntakeField,
    IntakeExtractor,
    JobIntakePayload,
)


# Field name on the consumer side (intake_node) → field name on the producer
# side (JobIntakePayload). Mirrors the ``_val(...)`` calls in
# ``app/domains/job_creation/graph.py:507-513``.
CONSUMER_TO_PRODUCER = {
    "parsed_title": "title",
    "parsed_seniority": "seniority",
    "parsed_department": "department",
    "parsed_location": "location",
    "parsed_model": "work_model",  # NB: schema field is work_model, exposed as parsed_model
}

# Legacy attribute names that intake_node USED to read directly off the
# extraction object. Re-introducing any of these in graph.py would silently
# revert Bug A2.
LEGACY_BANNED_ATTRS = {
    "parsed_title",
    "parsed_seniority",
    "parsed_department",
    "parsed_location",
    "parsed_model",
}


# ---------------------------------------------------------------------------
# S1 — Producer contract: every field intake_node reads exists on the payload
#      as an IntakeField (with .value and .source).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("producer_field", sorted(set(CONSUMER_TO_PRODUCER.values())))
def test_payload_exposes_intake_field_for_consumer(producer_field: str) -> None:
    payload = JobIntakePayload(raw_input="vaga de Desenvolvedor Python Senior")
    assert hasattr(payload, producer_field), (
        f"JobIntakePayload missing field '{producer_field}' that intake_node "
        f"reads via _val('{producer_field}'). Schema drift — see "
        f"docs/architecture/wizard-flow.md §5.1 Bug A2."
    )
    field = getattr(payload, producer_field)
    assert isinstance(field, IntakeField), (
        f"JobIntakePayload.{producer_field} must be an IntakeField "
        f"(with .value and .source), got {type(field).__name__}."
    )
    # Contract: IntakeField always exposes .value and .source (may be None/empty).
    assert hasattr(field, "value"), f"IntakeField missing .value on {producer_field}"
    assert hasattr(field, "source"), f"IntakeField missing .source on {producer_field}"


def test_payload_exposes_overall_confidence_for_intake_node() -> None:
    """intake_node reads ``extraction.overall_confidence`` (graph.py:514)."""
    payload = JobIntakePayload(raw_input="x")
    assert hasattr(payload, "overall_confidence"), (
        "JobIntakePayload must expose .overall_confidence — read by "
        "intake_node at graph.py:514. Bug A2 sentinel."
    )
    assert isinstance(payload.overall_confidence, (int, float))


# ---------------------------------------------------------------------------
# S2 — Anti-pattern: legacy raw attributes must NOT exist on the payload.
#      If they do, intake_node would still work but the schema drift would
#      be back (the attribute names are wrong vs the canonical .value path).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("legacy_attr", sorted(LEGACY_BANNED_ATTRS))
def test_payload_does_not_expose_legacy_parsed_attrs(legacy_attr: str) -> None:
    payload = JobIntakePayload(raw_input="x")
    assert not hasattr(payload, legacy_attr), (
        f"JobIntakePayload exposes legacy attribute '{legacy_attr}' — this "
        f"is the producer-side hook for Bug A2. The canonical interface is "
        f"'{CONSUMER_TO_PRODUCER.get(legacy_attr, '???')}.value'. See "
        f"docs/architecture/wizard-flow.md §5.1."
    )


# ---------------------------------------------------------------------------
# S3 — Static AST guard: intake_node source must NOT contain Attribute access
#      named after any of the legacy banned attrs on a name resembling
#      ``extraction``. Catches a regression that re-introduces
#      ``extraction.parsed_title`` or similar.
# ---------------------------------------------------------------------------
def test_intake_node_source_has_no_legacy_attribute_access() -> None:
    from app.domains.job_creation import graph as graph_mod

    source_path = Path(inspect.getsourcefile(graph_mod))  # type: ignore[arg-type]
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if node.attr not in LEGACY_BANNED_ATTRS:
            continue
        # Only flag accesses on a name that looks like the extraction var.
        if isinstance(node.value, ast.Name) and node.value.id in {"extraction", "result"}:
            offenders.append(f"L{node.lineno}: {node.value.id}.{node.attr}")

    assert not offenders, (
        "graph.py contains direct attribute access to legacy intake fields "
        "on the extraction object (Bug A2 regression). Use the canonical "
        "_val(field_name) helper instead. Offenders:\n  - "
        + "\n  - ".join(offenders)
    )


# ---------------------------------------------------------------------------
# S4 — Round-trip: feeding a clearly-job-flavored phrase through the regex
#      branch yields a payload where intake_node's _val mapping resolves
#      to a non-None title (positive proof the contract works end-to-end).
# ---------------------------------------------------------------------------
def test_regex_extraction_populates_title_consumed_by_intake_node() -> None:
    extractor = IntakeExtractor(llm_client=object())  # truthy non-None to skip _get_llm
    # Stub _llm_extract → None so we exercise the regex path deterministically.
    extractor._llm_extract = lambda masked, raw: None  # type: ignore[assignment]
    payload = extractor.extract("vaga de Desenvolvedor Python Senior")
    assert payload is not None
    # Mirror exactly what intake_node does (graph.py:498-505).
    title_field = getattr(payload, "title", None)
    assert title_field is not None
    title_value = getattr(title_field, "value", None)
    assert title_value not in (None, "", []), (
        "Regex branch failed to populate JobIntakePayload.title.value — "
        "intake_node would receive parsed_title=None and the input-thin "
        "guard would fire (Bug B regression chain)."
    )
