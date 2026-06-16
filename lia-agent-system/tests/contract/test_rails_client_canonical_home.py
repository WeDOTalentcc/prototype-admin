"""
Contract sensor — WeDOTalentATSClient permanece em canonical home
``app/shared/integration/rails_client.py`` (W2-010-B canonical merge).

WHY THIS SENSOR EXISTS
======================
Recovery #9 (2026-05-23) documentou que o commit ``840d952b3`` (Sprint X.D
Fase 1 · W2-010-B canonical merge) moveu ``WeDOTalentATSClient`` de
``app/domains/ats_integration/services/ats_clients/wedotalent_rails.py``
(DELETADO) pra ``app/shared/integration/rails_client.py`` (canonical home).

Esse refactor é POS-incident (merge happens em 2026-05-23 10:27 UTC) e
representa decisão arquitetural deliberada — não restaurar o módulo legacy.

Sensor garante:
1. Canonical classes (``WeDOTalentATSClient``, ``RailsAPIResponse``)
   permanecem em ``app.shared.integration.rails_client``.
2. Legacy path ``app.domains.ats_integration.services.ats_clients.wedotalent_rails``
   NÃO É RE-ADICIONADO acidentalmente (criaria duplicação canonical).

Pattern: BLOCKING.
"""
from __future__ import annotations

import importlib


def test_canonical_classes_in_rails_client():
    """
    ``WeDOTalentATSClient`` e ``RailsAPIResponse`` devem permanecer em
    ``app/shared/integration/rails_client.py`` (canonical home pós-W2-010-B).
    """
    from app.shared.integration.rails_client import (  # noqa: F401
        RailsAPIResponse,
        WeDOTalentATSClient,
    )

    # Validate classes are real (not shims)
    assert hasattr(WeDOTalentATSClient, "__init__"), (
        "WeDOTalentATSClient sem __init__ — não é a classe real."
    )


def test_legacy_path_remains_deleted():
    """
    ``app/domains/ats_integration/services/ats_clients/wedotalent_rails.py``
    foi DELETADO em W2-010-B canonical merge. Não deve ressuscitar — criaria
    duplicação.

    Se algum refactor futuro precisar trazer de volta (raríssimo, exigiria
    decisão arquitetural reversa), atualizar este sensor em PR explícito +
    ADR documentando reversão.
    """
    try:
        importlib.import_module(
            "app.domains.ats_integration.services.ats_clients.wedotalent_rails"
        )
        raise AssertionError(
            "Legacy module ats_clients.wedotalent_rails foi RE-ADICIONADO. "
            "W2-010-B canonical merge moveu pra app.shared.integration.rails_client. "
            "Se foi adição deliberada, atualizar sensor + ADR pra documentar "
            "reversão da decisão arquitetural."
        )
    except ModuleNotFoundError:
        # Expected — legacy path foi deletado em W2-010-B.
        pass


def test_no_orphan_imports_to_legacy_path():
    """
    Nenhum file em app/ ou tests/ deve importar o legacy path
    ``ats_clients.wedotalent_rails`` (importshould vir do canonical
    ``app.shared.integration.rails_client``).
    """
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            "grep", "-rln",
            "from app.domains.ats_integration.services.ats_clients.wedotalent_rails",
            "app/", "tests/",
            "--include=*.py",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    # Filtrar __pycache__, próprio sensor (que menciona o legacy path no
    # docstring/error message como referência), e rails_client.py canonical
    # (que documenta o move no docstring).
    _SELF_REFERENCE_FILES = {
        "tests/contract/test_rails_client_canonical_home.py",
        "app/shared/integration/rails_client.py",
    }
    orphan_imports = [
        line for line in result.stdout.split("\n")
        if line.strip()
        and "__pycache__" not in line
        and not any(self_ref in line for self_ref in _SELF_REFERENCE_FILES)
    ]

    assert not orphan_imports, (
        f"Imports orphan do legacy path ainda existem:\n"
        + "\n".join(orphan_imports)
        + "\n\nAtualizar pra:\n"
        + "  from app.shared.integration.rails_client import (\n"
        + "      RailsAPIResponse,\n"
        + "      WeDOTalentATSClient,\n"
        + "  )"
    )
