"""Track 3 G2 (2026-04-21) — Observability markers catalog + CI guard.

Closes Phase 0 observation: 95 [LIA-*] markers in code, zero catalog.
Canonical-fix: producer = the markers themselves (logger lines); catalog
is the consumer spec. CI guard validates:
  1. Catalog YAML parses + metadata present
  2. Every marker in catalog has category + purpose + origin + severity
  3. NO marker in code missing from catalog (drift guard)
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


CATALOG_REL = "app/shared/observability/marker_catalog.yaml"
MARKER_PATTERN = re.compile(r"\[LIA-([A-Z0-9]+)\]")
REQUIRED_FIELDS = {"category", "purpose", "origin", "severity"}


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / CATALOG_REL).exists():
            return parent
    raise RuntimeError(f"{CATALOG_REL} not found")


def _load_catalog() -> dict:
    return yaml.safe_load((_root() / CATALOG_REL).read_text(encoding="utf-8"))


def test_marker_catalog_parses_with_metadata() -> None:
    """G2: catalog YAML parses + has metadata + markers dict."""
    data = _load_catalog()
    assert isinstance(data, dict)
    assert "metadata" in data
    assert "markers" in data
    assert isinstance(data["markers"], dict)
    assert len(data["markers"]) >= 20, (
        f"G2: catalog must document at least 20 markers (found {len(data['markers'])})"
    )
    assert data["metadata"].get("initiative") == "G2"


def test_every_catalog_entry_has_required_fields() -> None:
    """G2: each marker must declare category/purpose/origin/severity."""
    data = _load_catalog()
    offences = []
    for name, entry in data["markers"].items():
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            offences.append(f"{name}: missing {sorted(missing)}")
    assert not offences, "G2 schema:\n  " + "\n  ".join(offences)


def test_no_code_marker_missing_from_catalog() -> None:
    """G2 drift guard: every [LIA-*] marker found in app/ must be in catalog.

    This prevents marker drift: if devs add new log markers without updating
    the catalog, CI fails. Keeps catalog as living documentation, not stale.
    """
    root = _root()
    app_dir = root / "app"
    found_markers: set[str] = set()
    for py in app_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        for m in MARKER_PATTERN.findall(text):
            # Strip LIA- prefix in catalog; format stored as "LIA-X"
            found_markers.add(f"LIA-{m}")

    catalog_markers = set(_load_catalog()["markers"].keys())
    drift = found_markers - catalog_markers

    assert not drift, (
        f"G2 drift: {len(drift)} marker(s) used in code but missing from catalog. "
        f"Add entries to app/shared/observability/marker_catalog.yaml:\n  "
        + "\n  ".join(sorted(drift))
    )


def test_catalog_origin_paths_exist() -> None:
    """G2 invariant: every catalog entry's `origin` path must exist in repo."""
    root = _root()
    data = _load_catalog()
    missing = []
    for name, entry in data["markers"].items():
        origin = entry.get("origin", "")
        if not origin:
            continue
        if not (root / origin).exists():
            missing.append(f"{name}: origin {origin} not found")
    assert not missing, "G2 origin paths:\n  " + "\n  ".join(missing)


def test_g2_doc_exists() -> None:
    """G2 human-readable doc for on-call + dashboards."""
    root = _root()
    doc = root / "docs" / "OBSERVABILITY_MARKERS.md"
    assert doc.exists(), (
        "G2: docs/OBSERVABILITY_MARKERS.md must exist as human-readable summary "
        "of marker catalog (for on-call, dashboard authors, new devs)."
    )
    text = doc.read_text(encoding="utf-8")
    assert "LIA-" in text and len(text) > 500
