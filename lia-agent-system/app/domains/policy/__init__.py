"""Deprecated — superseded by hiring_policy. See DOMAIN_CATALOG.md.

Este domínio implementa PolicySetupAgent como um questionário linear de 19 perguntas.
O domínio hiring_policy implementa um ReAct Agent consultivo com FairnessGuard,
anti-sycophancy e raciocínio estratégico — arquitetura superior.
Cronograma de remoção: Sprint VI (pós-Alpha 1 go-live).
Ver: docs/TODO_POLICY_CONSOLIDATION.md para detalhes do plano de merge.

UC-P1-21: Backward-compat shim re-exports HiringPolicyDomain so existing
callers that import from app.domains.policy continue to work during migration.
"""
import warnings

__domain_type__ = "deprecated"

# Re-export canonical class for backward compatibility.
# Import triggers a DeprecationWarning so callers can migrate.
try:
    from app.domains.hiring_policy.domain import HiringPolicyDomain  # noqa: F401

    warnings.warn(
        "app.domains.policy is deprecated. Use app.domains.hiring_policy instead. "
        "Scheduled for removal in Sprint VI.",
        DeprecationWarning,
        stacklevel=2,
    )
except ImportError:
    # If hiring_policy is not yet installed (e.g., early bootstrap), do nothing.
    pass
