"""Task #765 — neutral, layer-free helpers for the structured
``JobVacancy.benefits`` JSONB column.

Both the canonical write-time normalizer (``normalize_benefits_payload``)
and the flat-display-name extractor (``benefit_display_names``) live
here so any layer (API handlers, domain services, embedding,
notifications, recruitment chat) can import them without depending on
the API layer (``app.api.v1.job_vacancies._shared``).

Contract:
    * The persisted shape is a list of dicts with at minimum a
      ``name`` field.
    * Optional structured fields preserved on save/load:
      ``id, description, category, value_type, value, percentage_value,
      value_details, provider, seniority_levels, waiting_period_days,
      is_mandatory, is_active, is_highlighted, is_discount``.
    * ``value_type`` is clamped to one of
      ``{"monetary", "percentage", "informative"}``.
"""
from __future__ import annotations

from typing import Any, Iterable

_BENEFIT_VALID_VALUE_TYPES: frozenset[str] = frozenset(
    {"monetary", "percentage", "informative"}
)


def normalize_benefits_payload(raw: Iterable[Any] | None) -> list[dict]:
    """Coerce a mixed list of strings/dicts into the canonical JSONB
    benefit shape stored on ``job_vacancies.benefits``.

    * Strings → ``{"name": <str>, "category": None, "value_type": "informative"}``
    * Dicts → kept as-is, but with ``name`` required (entries without
      a usable name are dropped to avoid persisting garbage), and
      ``value_type`` clamped to one of the three known values.
    * ``None`` / falsy → ``[]``.
    """
    if not raw:
        return []
    out: list[dict] = []
    for item in raw:
        if item is None:
            continue
        if isinstance(item, str):
            name = item.strip()
            if not name:
                continue
            out.append({
                "name": name,
                "category": None,
                "value_type": "informative",
            })
            continue
        if isinstance(item, dict):
            name_val = item.get("name")
            if not isinstance(name_val, str) or not name_val.strip():
                continue
            entry: dict = dict(item)
            entry["name"] = name_val.strip()
            vt = entry.get("value_type")
            if vt not in _BENEFIT_VALID_VALUE_TYPES:
                entry["value_type"] = "informative"
            out.append(entry)
    return out


def benefit_display_names(benefits: Iterable[Any] | None) -> list[str]:
    """Extract human-readable names from a structured benefits list for
    downstream consumers (notifications, embedding, LLM prompts,
    candidate-facing chat, public vacancy view) that still expect a
    flat list of strings. Tolerates legacy strings and missing fields.
    """
    if not benefits:
        return []
    out: list[str] = []
    for item in benefits:
        if isinstance(item, str):
            text = item.strip()
            if text:
                out.append(text)
        elif isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
    return out
