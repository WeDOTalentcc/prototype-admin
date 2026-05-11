"""
Domain Registry - Auto-discovery and management of domain implementations.

Uses @register_domain decorator for zero-config domain registration.
Replaces AgentRegistry's hardcoded intent mapping with dynamic discovery.
"""
import logging
from typing import Optional

from app.domains.base import DomainAction, DomainPrompt

# LIA-C01: Compliance enforcement — domains MUST extend ComplianceDomainPrompt
def _get_compliance_base():
    try:
        from app.domains.compliance_base import ComplianceDomainPrompt
        return ComplianceDomainPrompt
    except ImportError:
        return None

logger = logging.getLogger(__name__)

_DOMAIN_REGISTRY: dict[str, type[DomainPrompt]] = {}


def register_domain(cls: type[DomainPrompt]) -> type[DomainPrompt]:
    """
    Decorator for auto-registering domain implementations.
    
    Usage:
        @register_domain
        class SourcingDomain(DomainPrompt):
            domain_id = "sourcing"
            ...
    """
    if not hasattr(cls, 'domain_id') or not cls.domain_id:
        raise ValueError(f"Domain class {cls.__name__} must define 'domain_id'")
    
    if cls.domain_id in _DOMAIN_REGISTRY:
        logger.warning(
            f"Domain '{cls.domain_id}' already registered by {_DOMAIN_REGISTRY[cls.domain_id].__name__}. "
            f"Overwriting with {cls.__name__}."
        )
    
    # LIA-C01: Enforce ComplianceDomainPrompt inheritance (BLOCKING as of 2026-04-13)
    # Escape hatch: LIA_ALLOW_NON_COMPLIANT_DOMAINS=1 for emergency rollback only.
    import os as _os
    _ComplianceBase = _get_compliance_base()
    if _ComplianceBase is not None and not issubclass(cls, _ComplianceBase):
        _msg = (
            f"[LIA-C01] Domain '{cls.domain_id}' (class={cls.__name__}) does NOT extend "
            f"ComplianceDomainPrompt. All domains MUST inherit from ComplianceDomainPrompt "
            f"to guarantee FairnessGuard + PII + PromptInjection + FactCheck enforcement. "
            f"See app/domains/compliance_base.py."
        )
        if _os.environ.get("LIA_ALLOW_NON_COMPLIANT_DOMAINS") == "1":
            logger.error("%s — BYPASS via LIA_ALLOW_NON_COMPLIANT_DOMAINS=1", _msg)
        else:
            logger.error(_msg)
            raise TypeError(_msg)

    _DOMAIN_REGISTRY[cls.domain_id] = cls
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Domain registered: {cls.domain_id} ({cls.__name__})")
    return cls


class DomainRegistry:
    """
    Central registry for all domain implementations.
    
    Provides singleton access, lazy instantiation, and domain discovery.
    Coexists with AgentRegistry during migration — both can be active.
    """
    _instance: Optional["DomainRegistry"] = None
    _instances: dict[str, DomainPrompt] = {}

    def __new__(cls) -> "DomainRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._instances = {}
        return cls._instance

    def get_instance(self, domain_id: str) -> DomainPrompt | None:
        """Get or create a domain instance by ID."""
        if domain_id not in self._instances:
            domain_cls = _DOMAIN_REGISTRY.get(domain_id)
            if domain_cls is None:
                logger.warning(f"Domain '{domain_id}' not found in registry")
                return None
            try:
                self._instances[domain_id] = domain_cls()
                logger.info(f"Domain instantiated: {domain_id}")
            except Exception as e:
                logger.error(f"Failed to instantiate domain '{domain_id}': {e}")
                return None
        return self._instances[domain_id]

    def list_domains(self) -> list[str]:
        """List all registered domain IDs."""
        return list(_DOMAIN_REGISTRY.keys())

    def list_registered_classes(self) -> dict[str, str]:
        """List all registered domain classes with their IDs."""
        return {did: cls.__name__ for did, cls in _DOMAIN_REGISTRY.items()}

    def get_all_actions(self) -> dict[str, list[DomainAction]]:
        """Get all actions from all registered domains."""
        result = {}
        for domain_id in _DOMAIN_REGISTRY:
            instance = self.get_instance(domain_id)
            if instance:
                result[domain_id] = instance.get_allowed_actions()
        return result

    def get_domain_for_action(self, action_id: str) -> DomainPrompt | None:
        """Find which domain handles a given action."""
        for domain_id in _DOMAIN_REGISTRY:
            instance = self.get_instance(domain_id)
            if instance and instance.get_action_by_id(action_id):
                return instance
        return None

    def is_registered(self, domain_id: str) -> bool:
        """Check if a domain is registered."""
        return domain_id in _DOMAIN_REGISTRY

    def reset(self) -> None:
        """Reset all instances (for testing)."""
        self._instances.clear()
        logger.info("DomainRegistry instances cleared")

    @classmethod
    def reset_registry(cls) -> None:
        """Reset the entire registry including class registrations (for testing only)."""
        global _DOMAIN_REGISTRY
        _DOMAIN_REGISTRY.clear()
        if cls._instance:
            cls._instance._instances.clear()
        logger.info("DomainRegistry fully reset")

    def __repr__(self) -> str:
        registered = list(_DOMAIN_REGISTRY.keys())
        instantiated = list(self._instances.keys())
        return f"<DomainRegistry registered={registered} instantiated={instantiated}>"


# ─── Agent Studio: tenant-scoped domain resolution (Etapa 8) ──────────────────

async def get_domain_for_company(
    domain_id: str,
    company_id: str,
    db=None,
):
    """
    Resolve a domain for a specific company, with tenant-scoped fallback.

    Resolution order:
    1. If db provided, look for a published AgentTemplate for this domain+company.
       If found, build a DomainPrompt-like proxy from its system_prompt_yaml.
    2. Fallback to the global WeDO domain (same as DomainRegistry().get_instance()).
    """
    if db is not None:
        try:
            from sqlalchemy import select

            from lia_models.agent_template import AgentTemplate, AgentTemplateStatus

            stmt = (
                select(AgentTemplate)
                .where(
                    AgentTemplate.domain == domain_id,
                    AgentTemplate.company_id == company_id,
                    AgentTemplate.status == AgentTemplateStatus.PUBLISHED,
                )
                .order_by(AgentTemplate.version.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            template = result.scalar_one_or_none()

            if template:
                logger.info(
                    "Agent Studio: using custom template %r (v%s) for company %s / domain %s",
                    template.name,
                    template.version,
                    company_id,
                    domain_id,
                )
                return _YamlDomainProxy(template.system_prompt_yaml, domain_id)
        except Exception as exc:
            logger.warning("Agent Studio template lookup failed (non-blocking): %s", exc)

    return DomainRegistry().get_instance(domain_id)


class _YamlDomainProxy:
    """
    Minimal DomainPrompt-compatible proxy built from an AgentTemplate YAML.
    Only implements what the orchestrator actually reads.
    """

    def __init__(self, system_prompt_yaml: str, domain_id: str) -> None:
        self.domain_id = domain_id
        self._system_prompt_yaml = system_prompt_yaml
        self._system_prompt = None

    def _parse_prompt(self) -> str:
        if self._system_prompt is None:
            try:
                import yaml
                data = yaml.safe_load(self._system_prompt_yaml) or {}
                self._system_prompt = data.get("prompt", self._system_prompt_yaml)
            except Exception:
                self._system_prompt = self._system_prompt_yaml
        return self._system_prompt

    def get_system_prompt(self, **kwargs):
        from app.shared.agents.tenant_aware_agent import (
            resolve_tenant_snippet_for_non_react,
        )
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
        domain_yaml_additions = self._parse_prompt()
        for key, value in kwargs.items():
            domain_yaml_additions = domain_yaml_additions.replace("{{" + key + "}}", str(value))
        # Task #978 (T-G): YAML-defined domain proxies são NON-ReAct e devem
        # passar pelo helper canônico para não regredirem o bug "LIA pergunta
        # company_id no chat" (3a recorrência endereçada em T-F).
        _tenant_snippet = resolve_tenant_snippet_for_non_react(
            {"tenant_context_snippet": kwargs.get("tenant_context_snippet", "")},
            agent_name=f"yaml_domain_proxy:{self.domain_id}",
            company_id_raw=kwargs.get("company_id"),
        )
        return SystemPromptBuilder.build(
            agent_type=self.domain_id,
            extra_instructions=domain_yaml_additions,
            tenant_context_snippet=_tenant_snippet,
            user_name=kwargs.get("user_name", ""),
            user_role=kwargs.get("user_role", ""),
        )

    def get_allowed_actions(self):
        return []

    def get_action_by_id(self, action_id: str):
        return None

    def __repr__(self) -> str:
        return f"<_YamlDomainProxy domain={self.domain_id}>"
