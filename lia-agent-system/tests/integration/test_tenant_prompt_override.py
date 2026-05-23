"""
Anti-regressão · W4-040 (2026-05-23) — tenant prompt override end-to-end.

Verifica que `PromptLoader.load(path, tenant_id=...)` retorna o YAML
do tenant quando existe, ou cai pra canonical quando não existe.

Fixture: app/prompts/tenants/__test_tenant__/shared/lia_persona.yaml
(criada por W4-040 patch).

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W4-040).
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _reset_loader_cache():
    """PromptLoader._cache é classvar — limpa entre tests."""
    from app.shared.prompts.loader import PromptLoader
    PromptLoader._cache.clear()
    yield
    PromptLoader._cache.clear()


class TestTenantPromptOverrideE2E:
    """W4-040 · validar tenant override priority (fail-soft → canonical)."""

    def test_tenant_fixture_exists(self) -> None:
        """Fixture deve estar em app/prompts/tenants/__test_tenant__/."""
        repo_root = Path(__file__).resolve().parents[2]
        fixture = (
            repo_root
            / "app/prompts/tenants/__test_tenant__/shared/lia_persona.yaml"
        )
        assert fixture.exists(), (
            f"W4-040 test fixture missing: {fixture}\n"
            "Re-run sprint X.A batch 6 patch."
        )

    def test_loader_picks_tenant_yaml_when_tenant_id_provided(self) -> None:
        """load(path, tenant_id='__test_tenant__') deve retornar override YAML."""
        from app.shared.prompts.loader import PromptLoader

        result = PromptLoader.load("shared/lia_persona", tenant_id="__test_tenant__")
        assert isinstance(result, dict)
        persona = result.get("persona", {})
        assert persona.get("name") == "LIA Test Override", (
            f"Tenant override NÃO foi aplicado. Got persona: {persona}"
        )

    def test_loader_falls_back_to_canonical_when_tenant_yaml_missing(self) -> None:
        """tenant_id='unknown_tenant' → cai pra canonical (fail-soft)."""
        from app.shared.prompts.loader import PromptLoader

        # Canonical lia_persona deve carregar para tenant inexistente
        result = PromptLoader.load("shared/lia_persona", tenant_id="unknown_tenant_xyz")
        assert isinstance(result, dict)
        # NÃO deve ser o override
        persona = result.get("persona", {})
        assert persona.get("name") != "LIA Test Override", (
            "tenant_id desconhecido deveria cair pra canonical, "
            "não retornar fixture override."
        )

    def test_loader_uses_canonical_when_tenant_id_none(self) -> None:
        """load(path) sem tenant_id → canonical."""
        from app.shared.prompts.loader import PromptLoader

        result = PromptLoader.load("shared/lia_persona")
        assert isinstance(result, dict)
        persona = result.get("persona", {})
        assert persona.get("name") != "LIA Test Override"

    def test_cache_isolates_tenants(self) -> None:
        """Cache deve distinguir (path, tenant_id) — sem cross-tenant pollution."""
        from app.shared.prompts.loader import PromptLoader

        canonical = PromptLoader.load("shared/lia_persona")
        override = PromptLoader.load("shared/lia_persona", tenant_id="__test_tenant__")
        # Mesmo path, tenant_ids diferentes → resultados diferentes
        assert canonical.get("persona", {}).get("name") != \
               override.get("persona", {}).get("name"), (
            f"Cache pollution: canonical e tenant retornaram mesmo data.\n"
            f"canonical={canonical.get('persona')}\noverride={override.get('persona')}"
        )
