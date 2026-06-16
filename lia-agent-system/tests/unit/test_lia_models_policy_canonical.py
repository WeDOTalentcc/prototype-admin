"""
Anti-regressão · W1-003 (2026-05-22) — Canonical policy budget/quota constants.

Garante que constantes movidas de V1 PolicyEngine pra `lia_models/policy.py`
mantêm shape exato + invariantes-chave que callers (V2
PolicyEngineService.apply_industry_defaults + save_policy_block) dependem.

Pre-audit: sprint_logs/sprint_1.2/W1-003_AUDIT.md.
"""
from __future__ import annotations


class TestCanonicalConstantsImportable:
    """Sanity: constantes importáveis do canonical location."""

    def test_canonical_default_policies_importable(self) -> None:
        from lia_models.policy import CANONICAL_DEFAULT_POLICIES  # noqa: F401

    def test_canonical_sector_defaults_importable(self) -> None:
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS  # noqa: F401

    def test_canonical_default_usage_limits_importable(self) -> None:
        from lia_models.policy import CANONICAL_DEFAULT_USAGE_LIMITS  # noqa: F401

    def test_canonical_allowed_usage_types_importable(self) -> None:
        from lia_models.policy import CANONICAL_ALLOWED_USAGE_TYPES  # noqa: F401


class TestCanonicalDefaultPolicies:
    """CANONICAL_DEFAULT_POLICIES tem shape e valores exatos do V1."""

    def test_has_all_required_keys(self) -> None:
        from lia_models.policy import CANONICAL_DEFAULT_POLICIES

        required = {
            "max_pearch_searches_per_day",
            "max_voice_screenings_per_day",
            "max_tokens_per_request",
            "max_concurrent_requests",
            "allow_global_search",
            "require_approval_for_bulk_email",
        }
        assert set(CANONICAL_DEFAULT_POLICIES.keys()) == required

    def test_canonical_defaults_match_v1_baseline(self) -> None:
        """Valores exatos do V1 PolicyEngine.DEFAULT_POLICIES (linha 59-66)."""
        from lia_models.policy import CANONICAL_DEFAULT_POLICIES

        assert CANONICAL_DEFAULT_POLICIES["max_pearch_searches_per_day"] == 10
        assert CANONICAL_DEFAULT_POLICIES["max_voice_screenings_per_day"] == 20
        assert CANONICAL_DEFAULT_POLICIES["max_tokens_per_request"] == 50000
        assert CANONICAL_DEFAULT_POLICIES["max_concurrent_requests"] == 5
        assert CANONICAL_DEFAULT_POLICIES["allow_global_search"] is True
        assert CANONICAL_DEFAULT_POLICIES["require_approval_for_bulk_email"] is True


class TestCanonicalSectorDefaults:
    """CANONICAL_SECTOR_DEFAULTS preserva invariantes-chave regulatórias."""

    def test_has_alpha1_sectors(self) -> None:
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS

        expected = {"tech", "varejo", "logistica", "financeiro", "saude", "rpo"}
        assert set(CANONICAL_SECTOR_DEFAULTS.keys()) == expected

    def test_tech_allows_global_search(self) -> None:
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS

        assert CANONICAL_SECTOR_DEFAULTS["tech"]["allow_global_search"] is True

    def test_financeiro_blocks_global_search_BCB_498(self) -> None:
        """Invariante regulatório: setor financeiro NUNCA permite global_search."""
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS

        assert CANONICAL_SECTOR_DEFAULTS["financeiro"]["allow_global_search"] is False

    def test_saude_blocks_global_search(self) -> None:
        """Invariante regulatório: setor saúde NUNCA permite global_search."""
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS

        assert CANONICAL_SECTOR_DEFAULTS["saude"]["allow_global_search"] is False

    def test_rpo_highest_throughput(self) -> None:
        """RPO é high-volume sourcing: deve ter limites mais altos."""
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS

        assert CANONICAL_SECTOR_DEFAULTS["rpo"]["max_pearch_searches_per_day"] == 500
        assert CANONICAL_SECTOR_DEFAULTS["rpo"]["max_concurrent_requests"] == 50

    def test_all_sectors_have_required_keys(self) -> None:
        from lia_models.policy import (
            CANONICAL_DEFAULT_POLICIES,
            CANONICAL_SECTOR_DEFAULTS,
        )

        required_keys = set(CANONICAL_DEFAULT_POLICIES.keys())
        for sector, defaults in CANONICAL_SECTOR_DEFAULTS.items():
            assert set(defaults.keys()) == required_keys, (
                f"sector {sector!r} missing keys: "
                f"{required_keys - set(defaults.keys())}"
            )


class TestCanonicalUsageLimits:
    """CANONICAL_DEFAULT_USAGE_LIMITS e CANONICAL_ALLOWED_USAGE_TYPES."""

    def test_default_usage_limits_match_v1(self) -> None:
        from lia_models.policy import CANONICAL_DEFAULT_USAGE_LIMITS

        assert CANONICAL_DEFAULT_USAGE_LIMITS == {
            "chat_requests": 1000,
            "action_executions": 500,
            "llm_calls": 5000,
        }

    def test_allowed_usage_types_is_frozenset(self) -> None:
        """frozenset previne mutação acidental (anti-injection guard)."""
        from lia_models.policy import CANONICAL_ALLOWED_USAGE_TYPES

        assert isinstance(CANONICAL_ALLOWED_USAGE_TYPES, frozenset)
        assert CANONICAL_ALLOWED_USAGE_TYPES == frozenset({
            "chat_requests",
            "action_executions",
            "llm_calls",
        })


class TestPolicyEngineServiceUsesCanonical:
    """W1-003 GREEN: V2 service NÃO instancia mais V1."""

    async def test_apply_industry_defaults_does_not_import_v1(self) -> None:
        """
        Após W1-003: PolicyEngineService.apply_industry_defaults usa lookup
        direto em CANONICAL_SECTOR_DEFAULTS, sem `from app.orchestrator.
        policy_engine import PolicyEngine`.
        """
        import inspect

        from app.domains.policy.services.policy_engine_service import (
            PolicyEngineService,
        )

        src = inspect.getsource(PolicyEngineService.apply_industry_defaults)
        # NÃO pode haver instanciação V1
        assert "PolicyEngine(" not in src, (
            "PolicyEngineService.apply_industry_defaults ainda instancia V1. "
            "W1-003 fix: usar CANONICAL_SECTOR_DEFAULTS de lia_models.policy."
        )
        assert "from app.orchestrator.policy_engine" not in src, (
            "Import V1 ainda presente em apply_industry_defaults."
        )

    async def test_save_policy_block_does_not_import_v1(self) -> None:
        import inspect

        from app.domains.policy.services.policy_engine_service import (
            PolicyEngineService,
        )

        src = inspect.getsource(PolicyEngineService.save_policy_block)
        assert "PolicyEngine(" not in src, (
            "PolicyEngineService.save_policy_block ainda instancia V1."
        )
        assert "from app.orchestrator.policy_engine" not in src, (
            "Import V1 ainda presente em save_policy_block."
        )


class TestV1ModuleGone:
    """Após W1-003: módulo V1 deletado + reexport removido."""

    def test_v1_module_deleted(self) -> None:
        """app/orchestrator/policy_engine.py deve ter sido git rm-ado."""
        import importlib.util

        spec = importlib.util.find_spec("app.orchestrator.policy_engine")
        assert spec is None, (
            "V1 PolicyEngine ainda existe em app/orchestrator/policy_engine.py. "
            "W1-003 fix: git rm app/orchestrator/policy_engine.py."
        )

    def test_v1_reexport_removed_from_orchestrator_init(self) -> None:
        """app.orchestrator.__init__.py NÃO pode reexportar PolicyEngine."""
        from app import orchestrator as orch_pkg

        assert not hasattr(orch_pkg, "PolicyEngine"), (
            "PolicyEngine ainda reexportado em app/orchestrator/__init__.py. "
            "W1-003 fix: remover linhas 'from .policy_engine import PolicyEngine' "
            "e '\"PolicyEngine\"' de __all__."
        )

    def test_v1_not_in_orchestrator_all(self) -> None:
        from app import orchestrator as orch_pkg

        if hasattr(orch_pkg, "__all__"):
            assert "PolicyEngine" not in orch_pkg.__all__, (
                "PolicyEngine ainda em __all__ de app.orchestrator. Remover."
            )
