"""
Tests for policy/ domain registration — T11.

Verifica:
1. PolicyDomain registra domain_id="policy" no DomainRegistry.
2. PolicyDomain herda de ComplianceDomainPrompt (LIA-C01).
3. get_allowed_actions() retorna lista (shim delega para hiring_policy).
4. Módulo importa sem erros fatais.
5. DomainRegistry.get_instance("policy") resolve para PolicyDomain.
"""
import importlib
import warnings

import pytest


class TestPolicyDomainRegistration:
    """Testa que PolicyDomain é registrado corretamente no DomainRegistry."""

    def test_module_imports_without_error(self):
        """app.domains.policy.domain deve importar sem exceção."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mod = importlib.import_module("app.domains.policy.domain")
        assert mod is not None

    def test_policy_domain_class_exists(self):
        """PolicyDomain deve ser exportado pelo módulo."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from app.domains.policy.domain import PolicyDomain  # noqa: F401
        assert PolicyDomain is not None

    def test_domain_id_is_policy(self):
        """domain_id deve ser 'policy'."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from app.domains.policy.domain import PolicyDomain
        assert PolicyDomain.domain_id == "policy"

    def test_inherits_compliance_base(self):
        """PolicyDomain deve herdar de ComplianceDomainPrompt (LIA-C01)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from app.domains.policy.domain import PolicyDomain
            from app.domains.compliance_base import ComplianceDomainPrompt
        assert issubclass(PolicyDomain, ComplianceDomainPrompt), (
            "PolicyDomain deve herdar de ComplianceDomainPrompt (exigido pelo register_domain)"
        )

    def test_registered_in_domain_registry(self):
        """Após importar o módulo, 'policy' deve estar no _DOMAIN_REGISTRY."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import app.domains.policy.domain  # noqa: F401 — side-effect: registers
            from app.domains.registry import _DOMAIN_REGISTRY
        assert "policy" in _DOMAIN_REGISTRY, (
            f"'policy' não encontrado em _DOMAIN_REGISTRY. Chaves: {list(_DOMAIN_REGISTRY.keys())}"
        )

    def test_registry_resolves_to_policy_domain(self):
        """DomainRegistry.get_instance('policy') deve retornar instância de PolicyDomain."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import app.domains.policy.domain  # noqa: F401 — ensure registered
            from app.domains.policy.domain import PolicyDomain
            from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            instance = registry.get_instance("policy")
        assert isinstance(instance, PolicyDomain), (
            f"Esperado PolicyDomain, got {type(instance)}"
        )

    def test_get_allowed_actions_returns_list(self):
        """get_allowed_actions() deve retornar lista (delegada ao hiring_policy)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from app.domains.policy.domain import PolicyDomain
            instance = PolicyDomain.__new__(PolicyDomain)
            # Bypass __init__ DeprecationWarning for unit isolation
            object.__setattr__(instance, '_compliance_config', PolicyDomain._compliance_config)
        actions = instance.get_allowed_actions()
        assert isinstance(actions, list), "get_allowed_actions() deve retornar list"

    def test_domain_is_marked_deprecated(self):
        """Instanciar PolicyDomain deve emitir DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from app.domains.policy.domain import PolicyDomain
            PolicyDomain()
        dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert dep_warnings, "Esperado pelo menos 1 DeprecationWarning ao instanciar PolicyDomain"
