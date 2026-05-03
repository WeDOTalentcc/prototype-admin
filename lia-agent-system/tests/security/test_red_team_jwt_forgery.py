"""R-008 — hardening ContextVar company_id contra JWT forgery / cross-tenant.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-323 / R-008.

Red team scenarios:
1. Atacante envia POST com company_id="victim-co" no body — ContextVar deve
   permanecer com o JWT-verified company_id.
2. Atacante envia X-Company-ID="victim-co" header — middleware ja rejeita
   com 403 (cross-tenant attempt detectado, F-323 ja parcialmente coberto).
3. ContextVar nao deve ser populada antes da signature verification do JWT.
4. Helper canonical _set_company_id_synthetic_dev_only raise se chamado em prod.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "app" / "middleware" / "auth_enforcement.py"


def _read_target() -> str:
    return TARGET.read_text(encoding="utf-8")


def test_canonical_helper_set_company_id_from_jwt_exists() -> None:
    """R-008: helper canonical _set_company_id_from_jwt esta exposto."""
    from app.middleware.auth_enforcement import _set_company_id_from_jwt

    assert callable(_set_company_id_from_jwt)
    sig = inspect.signature(_set_company_id_from_jwt)
    assert (
        "verified_payload" in sig.parameters
    ), "R-008: helper precisa receber verified_payload (dict ja decodificado)."


def test_canonical_helper_synthetic_dev_only_exists() -> None:
    """R-008: helper para DEV_MODE separado do path de auth real."""
    from app.middleware.auth_enforcement import _set_company_id_synthetic_dev_only

    assert callable(_set_company_id_synthetic_dev_only)


def test_synthetic_dev_only_raises_outside_dev_mode(monkeypatch) -> None:
    """R-008: chamar synthetic helper fora de DEV_MODE raise RuntimeError (defesa em profundidade)."""
    import importlib
    import sys

    monkeypatch.setenv("LIA_DEV_MODE", "false")
    monkeypatch.setenv("ENVIRONMENT", "production")
    if "app.middleware.auth_enforcement" in sys.modules:
        del sys.modules["app.middleware.auth_enforcement"]
    mod = importlib.import_module("app.middleware.auth_enforcement")

    assert mod._DEV_MODE is False
    with pytest.raises(RuntimeError, match="R-008"):
        mod._set_company_id_synthetic_dev_only("attacker-tenant")


def test_set_company_id_from_jwt_extracts_only_company_id_claim() -> None:
    """R-008: helper extrai company_id apenas do payload, ignora outros campos."""
    from app.middleware.auth_enforcement import _current_company_id, _set_company_id_from_jwt

    # Token "verified" hipotetico
    payload = {
        "sub": "user-1",
        "company_id": "legit-co",
        "role": "admin",
        # Campos nao usados:
        "iat": 1234,
        "exp": 5678,
    }
    result = _set_company_id_from_jwt(payload)
    assert result == "legit-co"
    assert _current_company_id.get() == "legit-co"


def test_set_company_id_from_jwt_handles_missing_claim() -> None:
    """R-008: payload sem company_id → ContextVar = '' (nao raise)."""
    from app.middleware.auth_enforcement import _set_company_id_from_jwt

    payload = {"sub": "user-no-tenant"}
    result = _set_company_id_from_jwt(payload)
    assert result == ""


def test_no_direct_contextvar_set_outside_helpers() -> None:
    """R-008: source-level audit — _current_company_id.set() so via helpers canonicos.

    Permite somente ocorrencias dentro das proprias funcoes helper. Outras
    chamadas indicam regressao (alguem reintroduzindo set direto).
    """
    src = _read_target()
    # Acha todas as ocorrencias de _current_company_id.set(...)
    direct_sets = re.findall(r"_current_company_id\.set\([^)]*\)", src)

    # As 2 chamadas legitimas estao dentro dos helpers canonicos.
    # Toda chamada FORA deles e' regressao.
    # Heuristica: contar quantas estao no body dos 2 helpers.
    helper_blocks = re.findall(
        r"def _set_company_id_(?:from_jwt|synthetic_dev_only)\([^)]*\)[^:]*:.*?(?=\n(?:def |class |\Z))",
        src,
        re.DOTALL,
    )
    helper_text = "\n".join(helper_blocks)
    sets_in_helpers = re.findall(r"_current_company_id\.set\([^)]*\)", helper_text)

    sets_outside_helpers = len(direct_sets) - len(sets_in_helpers)
    assert sets_outside_helpers == 0, (
        f"R-008: {sets_outside_helpers} chamadas a _current_company_id.set() fora "
        "dos helpers canonicos detectadas. Use _set_company_id_from_jwt() ou "
        "_set_company_id_synthetic_dev_only() em vez de set direto."
    )


def test_no_company_id_set_from_request_body_or_query() -> None:
    """R-008: source-level — auth_enforcement nao le company_id de request.body/query."""
    src = _read_target()
    # Pattern: request.json()['company_id'] OR request.body... company_id
    forbidden_patterns = [
        r"request\.json\(\)\.get\(['\"]company_id['\"]",
        r"request\.body.*company_id",
        r"request\.query_params.*company_id",
    ]
    offenders = []
    for pattern in forbidden_patterns:
        if re.search(pattern, src):
            offenders.append(pattern)
    assert not offenders, (
        "R-008: auth_enforcement.py nao pode ler company_id de request.body/query/json. "
        f"Padroes detectados: {offenders}"
    )
