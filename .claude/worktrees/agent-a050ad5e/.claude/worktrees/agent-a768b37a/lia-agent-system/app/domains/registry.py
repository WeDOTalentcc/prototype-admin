"""
Domain Registry - Auto-discovery and management of domain implementations.

Uses @register_domain decorator for zero-config domain registration.
Replaces AgentRegistry's hardcoded intent mapping with dynamic discovery.
"""
from typing import Dict, List, Type, Optional, Any
import logging

from app.domains.base import DomainPrompt, DomainAction

logger = logging.getLogger(__name__)

_DOMAIN_REGISTRY: Dict[str, Type[DomainPrompt]] = {}


def register_domain(cls: Type[DomainPrompt]) -> Type[DomainPrompt]:
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
    
    _DOMAIN_REGISTRY[cls.domain_id] = cls
    logger.info(f"Domain registered: {cls.domain_id} ({cls.__name__})")
    return cls


class DomainRegistry:
    """
    Central registry for all domain implementations.
    
    Provides singleton access, lazy instantiation, and domain discovery.
    Coexists with AgentRegistry during migration — both can be active.
    """
    _instance: Optional["DomainRegistry"] = None
    _instances: Dict[str, DomainPrompt] = {}

    def __new__(cls) -> "DomainRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._instances = {}
        return cls._instance

    def get_instance(self, domain_id: str) -> Optional[DomainPrompt]:
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

    def list_domains(self) -> List[str]:
        """List all registered domain IDs."""
        return list(_DOMAIN_REGISTRY.keys())

    def list_registered_classes(self) -> Dict[str, str]:
        """List all registered domain classes with their IDs."""
        return {did: cls.__name__ for did, cls in _DOMAIN_REGISTRY.items()}

    def get_all_actions(self) -> Dict[str, List[DomainAction]]:
        """Get all actions from all registered domains."""
        result = {}
        for domain_id in _DOMAIN_REGISTRY:
            instance = self.get_instance(domain_id)
            if instance:
                result[domain_id] = instance.get_allowed_actions()
        return result

    def get_domain_for_action(self, action_id: str) -> Optional[DomainPrompt]:
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
