"""
Smoke tests for Orchestrator V1 — Sprint I Tarefa C.

Valida que a infraestrutura de characterization tests está funcional ANTES de
construir os 52 fixtures completos. Se estes 5 tests passarem, podemos
prosseguir com confiança para os characterization tests detalhados.

Princípio: small steps, validate often. Cada teste aqui mapeia para uma
premissa do plano de migração que precisa ser verdade.
"""
from __future__ import annotations

import inspect

import pytest


class TestV1ImportAndStructure:
    """Sanidade — V1 existe, é importável, e tem a estrutura esperada."""

    def test_v1_module_importable(self):
        """V1 (orchestrator.py) deve ser importável apesar do DeprecationWarning."""
        from app.orchestrator.legacy import orchestrator as v1_module

        assert v1_module is not None
        assert hasattr(v1_module, "Orchestrator"), (
            "V1 module deve expor classe Orchestrator"
        )

    def test_v1_class_has_expected_public_methods(self):
        """V1 deve ter os 12 métodos públicos mapeados no plano de migração."""
        from app.orchestrator.legacy.orchestrator import Orchestrator

        expected_methods = {
            "process_request",
            "process_request_with_memory",
            "execute_plan",
            "process_analytics_request",
            "get_metrics",
            "get_cache_stats",
            "invalidate_cache_for_entity",
            "is_tool_allowed",
            "get_scope_system_prompt",
            "get_available_tools",
        }
        actual_public = {
            name
            for name, _ in inspect.getmembers(Orchestrator, predicate=inspect.isfunction)
            if not name.startswith("_")
        }

        missing = expected_methods - actual_public
        assert not missing, (
            f"V1 perdeu métodos esperados pelo plano de migração: {missing}. "
            f"Atualizar Anexo H de ORCHESTRATOR_MIGRATION_MASTER_PLAN.md."
        )

    def test_v1_class_has_expected_internal_methods(self):
        """V1 deve ter os métodos privados/heurísticos críticos para extração no Sprint II."""
        from app.orchestrator.legacy.orchestrator import Orchestrator

        expected_internal = {
            "_handle_directly",  # LIA-A04 fallback ReAct
            "_handle_cv_screening_with_rubric",  # CV matching
            "_is_technical_response",  # Heurística technical
            "_is_cv_matching_request",  # Heurística cv matching
        }
        actual = {
            name
            for name, _ in inspect.getmembers(Orchestrator, predicate=inspect.isfunction)
            if name.startswith("_") and not name.startswith("__")
        }

        missing = expected_internal - actual
        assert not missing, (
            f"V1 perdeu métodos internos esperados: {missing}. "
            f"Sprint II Tarefa de extração depende disso."
        )

    def test_v1_marked_as_deprecated(self):
        """V1 deve manter marcação LIA-D06 DEPRECATED até Sprint V."""
        import app.orchestrator.legacy.orchestrator as v1_module

        docstring = inspect.getsourcefile(v1_module)
        assert docstring, "V1 module deve ser inspecionável"

        source = inspect.getsource(v1_module)
        assert "LIA-D06" in source or "DEPRECATED" in source.upper(), (
            "V1 deve manter marcação de deprecation visível"
        )


class TestCharacterizationInfrastructure:
    """Valida que conftest.py tem fixtures funcionais."""

    def test_tenant_a_context_has_required_fields(self, tenant_a_context):
        """Multi-tenant context deve incluir company_id (P0 LGPD)."""
        assert "company_id" in tenant_a_context
        assert "user_id" in tenant_a_context
        assert "scope" in tenant_a_context

    def test_tenant_isolation_uuids_differ(self, tenant_a_context, tenant_b_context):
        """Tenant A e B devem ter company_id distintos para teste de isolation."""
        assert tenant_a_context["company_id"] != tenant_b_context["company_id"]

    def test_lgpd_protected_attributes_includes_core_set(self, lgpd_protected_attributes):
        """Lista LGPD deve incluir os 7 atributos do CLAUDE.md global rule #2."""
        required = {"race", "religion", "gender", "ethnicity", "marital_status", "health"}
        actual = set(lgpd_protected_attributes)
        missing = required - actual
        assert not missing, f"Atributos LGPD obrigatórios faltando: {missing}"
