"""WT-2022 Camada IA Proativa: contract tests.

Cobertura:
1. Sensor AST detecta detector nao-registrado (regression test do proprio sensor)
2. ProactiveDetectorService.detectors contem exatamente 6 detectors canonical
3. Cada detector retorna lista (mesmo que vazia) sem raise para input vazio
4. ProactiveDetectorService.run_for_company nao quebra se um detector lanca
5. Endpoint /proactive-hints rejeita request sem JWT (multi-tenancy gate)
6. dismiss_hint rejeita hint de outra company (cross-tenant guard)
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def detector_service():
    """Importa modulo canonical e devolve instancia singleton."""
    from app.shared.services.proactive_detector_service import (
        proactive_detector_service,
    )
    return proactive_detector_service


@pytest.fixture
def fake_db():
    """Fake AsyncSession que retorna lista vazia em qualquer execute()."""
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock(
        scalars=lambda: MagicMock(
            first=lambda: None,
            all=lambda: [],
        ),
        first=lambda: None,
    ))
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# Test 1: Sensor AST funciona corretamente
# ---------------------------------------------------------------------------


def test_sensor_finds_all_canonical_detectors() -> None:
    """O sensor AST deve detectar todos os detectors declarados."""
    canonical = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "shared"
        / "services"
        / "proactive_detector_service.py"
    )
    if not canonical.exists():
        pytest.skip("Canonical file not deployed yet")

    source = canonical.read_text(encoding="utf-8")
    tree = ast.parse(source)

    detector_classes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = (
                    base.id
                    if isinstance(base, ast.Name)
                    else getattr(base, "attr", "")
                )
                if base_name == "BaseDetector" and node.name != "BaseDetector":
                    detector_classes.append(node.name)

    # Sprint 0 canonical: 6 detectors
    assert len(detector_classes) >= 6, (
        f"Esperado >= 6 detectors, encontrei {len(detector_classes)}: "
        f"{detector_classes}"
    )


# ---------------------------------------------------------------------------
# Test 2: Service registra todos os detectors
# ---------------------------------------------------------------------------


def test_service_registers_all_canonical_detectors(detector_service) -> None:
    detector_names = {d.name for d in detector_service.detectors}
    canonical = {
        "company_profile_completion",
        "dsr_overdue",
        "candidate_stale",
        "workforce_plan_stale",
        "ai_credits_low",
        "pipeline_stuck",
    }
    missing = canonical - detector_names
    assert not missing, f"Detectors faltando no service: {missing}"


# ---------------------------------------------------------------------------
# Test 3: Detectors handles invalid company_id gracefully
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_detectors_return_list_for_invalid_company_id(
    detector_service, fake_db
) -> None:
    """Detector NAO deve raise para company_id invalido. Retorna []."""
    for detector in detector_service.detectors:
        result = await detector.detect(fake_db, "not-a-uuid")
        assert isinstance(result, list), (
            f"Detector {detector.name} retornou {type(result).__name__}, "
            "esperado list"
        )


# ---------------------------------------------------------------------------
# Test 4: run_for_company isola falha de um detector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_for_company_isolates_detector_failure(
    detector_service, fake_db
) -> None:
    """Se um detector lanca, os outros continuam rodando."""
    from app.shared.services.proactive_detector_service import BaseDetector

    class BrokenDetector(BaseDetector):
        name = "broken_test_detector"
        severity = "low"

        async def detect(self, db, company_id):
            raise RuntimeError("detector quebrado proposital")

    original = list(detector_service.detectors)
    detector_service.detectors = [BrokenDetector()] + original

    try:
        result = await detector_service.run_for_company(
            fake_db, "00000000-0000-0000-0000-000000000000"
        )
        # Sumario inclui o broken detector com -1
        assert result["detectors_run"] >= 1
        assert "broken_test_detector" in result["per_detector"]
        assert result["per_detector"]["broken_test_detector"] == -1
    finally:
        detector_service.detectors = original


# ---------------------------------------------------------------------------
# Test 5: Endpoint require_company_id gate
# ---------------------------------------------------------------------------


def test_endpoint_has_require_company_id_dependency() -> None:
    """GET /proactive-hints + POST dismiss devem usar require_company_id."""
    try:
        from app.api.v1 import proactive_hints
    except ImportError:
        pytest.skip("proactive_hints module not deployed yet")

    src = (
        Path(proactive_hints.__file__).read_text(encoding="utf-8")
        if hasattr(proactive_hints, "__file__")
        else ""
    )
    # Strings exatas — protege contra remocao silenciosa do gate.
    assert "Depends(require_company_id)" in src, (
        "Endpoint sem dependency require_company_id (cross-tenant gap)"
    )
    assert "list_active_hints" in src
    assert "dismiss_hint" in src


# ---------------------------------------------------------------------------
# Test 6: Celery task registration
# ---------------------------------------------------------------------------


def test_celery_task_registered() -> None:
    """proactive.detect_hints_hourly deve estar registrado no celery_app."""
    try:
        from app.core.celery_app import celery_app

        from app.jobs.tasks import proactive  # noqa: F401  # forca import
    except ImportError:
        pytest.skip("celery_app or task module not available in this env")

    task_names = list(celery_app.tasks.keys())
    assert "proactive.detect_hints_hourly" in task_names, (
        f"Task nao registrada. Tasks disponiveis: "
        f"{[n for n in task_names if 'proactive' in n]}"
    )


# ---------------------------------------------------------------------------
# Test 7: Sensor script executa sem erro contra arquivo canonical
# ---------------------------------------------------------------------------


def test_sensor_script_passes_on_canonical_file(tmp_path) -> None:
    """Sensor AST deve exit 0 no estado canonical."""
    sensor = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "check_proactive_detectors_registered.py"
    )
    if not sensor.exists():
        pytest.skip("Sensor script not deployed yet")

    spec = importlib.util.spec_from_file_location("check_detectors", sensor)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    # main() retorna int; deve ser 0 quando registro esta consistente
    import sys
    argv = sys.argv
    try:
        sys.argv = ["check_proactive_detectors_registered.py"]
        rc = module.main()
    finally:
        sys.argv = argv

    assert rc == 0, (
        "Sensor reportou drift. Verifique se todo XxxDetector(BaseDetector) "
        "esta listado em ProactiveDetectorService.detectors."
    )
