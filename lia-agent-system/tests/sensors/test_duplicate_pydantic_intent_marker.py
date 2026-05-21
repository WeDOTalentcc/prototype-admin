"""Self-test for Sprint Q.2 # DUPLICATE_OF_INTENT marker support in
check_duplicate_pydantic_schemas.py sensor.

Pattern: tmp_path-based AST fixtures. No DB / network.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


SENSOR_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "check_duplicate_pydantic_schemas.py"
)


def _load_sensor():
    """Load the sensor module dynamically (it's a script, not in app/)."""
    spec = importlib.util.spec_from_file_location("sensor_q2", SENSOR_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sensor_q2"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sensor():
    return _load_sensor()


def _write_two_dup_files(
    tmp_path: Path,
    with_marker_on_b: bool,
) -> Path:
    """Create canonical (a.py) + duplicate (b.py) with same class A(BaseModel).
    If with_marker_on_b is True, prepend the DUPLICATE_OF_INTENT comment.
    Returns the root dir to pass to collect_schemas.
    """
    (tmp_path / "a.py").write_text(
        "from pydantic import BaseModel\n"
        "\n"
        "class A(BaseModel):\n"
        "    x: int\n",
        encoding="utf-8",
    )
    marker = "# DUPLICATE_OF_INTENT: a.py — re-export pattern\n" if with_marker_on_b else ""
    (tmp_path / "b.py").write_text(
        "from pydantic import BaseModel\n"
        "\n"
        f"{marker}"
        "class A(BaseModel):\n"
        "    x: int\n",
        encoding="utf-8",
    )
    return tmp_path


def test_marker_excludes_intentional_duplicate(tmp_path, sensor):
    """A dup carrying `# DUPLICATE_OF_INTENT` is NOT counted as a violation."""
    root = _write_two_dup_files(tmp_path, with_marker_on_b=True)
    schemas = sensor.collect_schemas(root)
    duplicates = sensor.find_duplicates(schemas)
    assert duplicates == {}, (
        f"Expected no violations when one of two dups has marker, got: {duplicates}"
    )


def test_no_marker_still_counts_as_violation(tmp_path, sensor):
    """Without marker, two dups of class A are still flagged."""
    root = _write_two_dup_files(tmp_path, with_marker_on_b=False)
    schemas = sensor.collect_schemas(root)
    duplicates = sensor.find_duplicates(schemas)
    assert "A" in duplicates, (
        f"Expected class A to be flagged as duplicate, got: {duplicates}"
    )
    assert len(duplicates["A"]) == 2


def test_marker_detected_on_line_directly_above(tmp_path, sensor):
    """Marker on the line immediately above `class X(...)` is detected."""
    (tmp_path / "f.py").write_text(
        "from pydantic import BaseModel\n"
        "# DUPLICATE_OF_INTENT: canonical.py — reason\n"
        "class A(BaseModel):\n"
        "    x: int\n",
        encoding="utf-8",
    )
    schemas = sensor.collect_schemas(tmp_path)
    assert len(schemas) == 1
    assert schemas[0].has_intent_marker is True


def test_marker_detected_up_to_5_lines_above(tmp_path, sensor):
    """Marker up to 5 lines above (with blank/comment lines between) is detected."""
    (tmp_path / "f.py").write_text(
        "from pydantic import BaseModel\n"
        "# DUPLICATE_OF_INTENT: canonical.py — reason\n"
        "\n"
        "\n"
        "\n"
        "class A(BaseModel):\n"
        "    x: int\n",
        encoding="utf-8",
    )
    schemas = sensor.collect_schemas(tmp_path)
    assert len(schemas) == 1
    assert schemas[0].has_intent_marker is True


def test_marker_too_far_above_not_detected(tmp_path, sensor):
    """Marker more than 5 lines above is NOT detected (out of lookback window)."""
    (tmp_path / "f.py").write_text(
        "from pydantic import BaseModel\n"
        "# DUPLICATE_OF_INTENT: canonical.py — reason\n"
        "\n"
        "\n"
        "\n"
        "\n"
        "\n"
        "\n"
        "class A(BaseModel):\n"
        "    x: int\n",
        encoding="utf-8",
    )
    schemas = sensor.collect_schemas(tmp_path)
    assert len(schemas) == 1
    assert schemas[0].has_intent_marker is False


def test_three_site_group_with_one_marker_still_violates(tmp_path, sensor):
    """If A is declared in 3 files and only 1 carries marker, the remaining
    2 unmarked are still a real violation."""
    (tmp_path / "a.py").write_text(
        "from pydantic import BaseModel\nclass A(BaseModel):\n    x: int\n",
        encoding="utf-8",
    )
    (tmp_path / "b.py").write_text(
        "from pydantic import BaseModel\n"
        "# DUPLICATE_OF_INTENT: a.py — re-export\n"
        "class A(BaseModel):\n    x: int\n",
        encoding="utf-8",
    )
    (tmp_path / "c.py").write_text(
        "from pydantic import BaseModel\nclass A(BaseModel):\n    x: str\n",
        encoding="utf-8",
    )
    schemas = sensor.collect_schemas(tmp_path)
    duplicates = sensor.find_duplicates(schemas)
    assert "A" in duplicates
    # All 3 sites listed for context, but only 2 unmarked
    assert len(duplicates["A"]) == 3
    unmarked = [d for d in duplicates["A"] if not d.has_intent_marker]
    assert len(unmarked) == 2
