# LIA-T01 | PR-G: canonical-fix sensor for hitl_service
"""
PR-G sensors: hitl_service canonical path enforcement.

Harness taxonomy:
  - SENSOR (computacional): assert shim is gone — no dead code
  - SENSOR (computacional): assert all consumers use canonical path
  - SENSOR (computacional): canonical module is importable and has required symbols

canonical-fix rule: corrigir na fonte, nunca no consumidor.
Canonical path: app.domains.cv_screening.services.hitl_service
Dead path: app.shared.services.hitl_service (deleted)
"""
import ast
import pathlib

import pytest

_ROOT = pathlib.Path(__file__).parent.parent.parent.parent  # lia-agent-system/
_APP = _ROOT / "app"
_CANONICAL = _APP / "domains" / "cv_screening" / "services" / "hitl_service.py"
_DEAD_SHIM = _APP / "shared" / "services" / "hitl_service.py"


# ---------------------------------------------------------------------------
# Sensor: shim is gone
# ---------------------------------------------------------------------------

class TestHITLShimDeleted:
    """Sensor: dead shim must not exist — only one source of truth."""

    def test_shared_hitl_shim_does_not_exist(self) -> None:
        assert not _DEAD_SHIM.exists(), (
            f"Dead shim found at {_DEAD_SHIM}. "
            "The canonical HITL implementation lives in "
            "app.domains.cv_screening.services.hitl_service. "
            "Delete the shim and update any remaining imports."
        )

    def test_canonical_hitl_service_exists(self) -> None:
        assert _CANONICAL.exists(), (
            f"Canonical hitl_service not found at {_CANONICAL}. "
            "Something deleted the wrong file."
        )

    def test_canonical_is_substantial(self) -> None:
        """Canonical must be a real implementation (>100 lines), not another shim."""
        lines = _CANONICAL.read_text().splitlines()
        assert len(lines) > 100, (
            f"canonical hitl_service has only {len(lines)} lines — looks like a shim. "
            "The canonical implementation should have the full HITLService class."
        )


# ---------------------------------------------------------------------------
# Sensor: consumers use canonical import path
# ---------------------------------------------------------------------------

class TestHITLImportPaths:
    """Sensor: no file may import from app.shared.services.hitl_service."""

    def _python_files(self) -> list[pathlib.Path]:
        return [
            p for p in _APP.rglob("*.py")
            if "__pycache__" not in str(p)
        ]

    def test_no_consumer_imports_dead_shim(self) -> None:
        """Assert zero files import from the deleted shim path."""
        violations: list[str] = []
        for pyfile in self._python_files():
            src = pyfile.read_text(errors="ignore")
            if "shared.services.hitl_service" in src or "shared/services/hitl_service" in src:
                violations.append(str(pyfile.relative_to(_ROOT)))

        assert not violations, (
            f"Files still importing from deleted shim:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\nUpdate these imports to: "
            "app.domains.cv_screening.services.hitl_service"
        )

    def test_canonical_path_used_by_consumers(self) -> None:
        """At least 3 files must import from canonical path (confirms it's in use)."""
        consumers = []
        for pyfile in self._python_files():
            src = pyfile.read_text(errors="ignore")
            if (
                "cv_screening.services.hitl_service" in src
                and str(pyfile) != str(_CANONICAL)
            ):
                consumers.append(str(pyfile.relative_to(_ROOT)))

        assert len(consumers) >= 3, (
            f"Expected at least 3 consumers of canonical hitl_service, found {len(consumers)}. "
            "Check that imports weren't accidentally removed."
        )


# ---------------------------------------------------------------------------
# Sensor: canonical module has required public symbols
# ---------------------------------------------------------------------------

class TestHITLCanonicalSymbols:
    """Sensor: canonical module must expose HITLService and hitl_service singleton."""

    def test_hitlservice_class_defined(self) -> None:
        src = _CANONICAL.read_text()
        tree = ast.parse(src)
        class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        assert "HITLService" in class_names, (
            "HITLService class not found in canonical hitl_service.py. "
            "The canonical implementation must define HITLService."
        )

    def test_hitl_service_singleton_defined(self) -> None:
        src = _CANONICAL.read_text()
        assert "hitl_service" in src, (
            "hitl_service singleton not found in canonical hitl_service.py. "
            "Consumers expect a module-level singleton: hitl_service = HITLService()"
        )

    def test_request_approval_method_exists(self) -> None:
        src = _CANONICAL.read_text()
        assert "request_approval" in src, (
            "request_approval method missing from canonical hitl_service. "
            "All agents call hitl_service.request_approval() — cannot be removed."
        )
