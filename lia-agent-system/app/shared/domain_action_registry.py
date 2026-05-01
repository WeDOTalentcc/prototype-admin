"""
DomainActionRegistry - Central registry for action ownership across domains.

Prevents action overlap by ensuring each action has a single owner domain.
Other domains that need the same action use delegate_to_domain().

Usage:
    registry = DomainActionRegistry()
    registry.register("compare_candidates", "cv_screening")
    registry.register_alias("compare_candidates", "sourcing")
    
    owner = registry.get_owner("compare_candidates")  # "cv_screening"
    is_alias = registry.is_alias("compare_candidates", "sourcing")  # True
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ActionRegistration:
    action_id: str
    owner_domain: str
    alias_domains: set[str] = field(default_factory=set)
    description: str = ""


class DomainActionRegistry:
    _instance: Optional['DomainActionRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry: dict[str, ActionRegistration] = {}
            cls._instance._domain_actions: dict[str, set[str]] = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, action_id: str, owner_domain: str, description: str = "") -> None:
        if action_id in self._registry:
            existing = self._registry[action_id]
            if existing.owner_domain != owner_domain:
                logger.warning(
                    f"[ACTION-REGISTRY] Conflict: '{action_id}' already owned by "
                    f"'{existing.owner_domain}', attempted re-registration by '{owner_domain}'. "
                    f"Registering '{owner_domain}' as alias instead."
                )
                existing.alias_domains.add(owner_domain)
                return
            return

        self._registry[action_id] = ActionRegistration(
            action_id=action_id,
            owner_domain=owner_domain,
            description=description,
        )
        if owner_domain not in self._domain_actions:
            self._domain_actions[owner_domain] = set()
        self._domain_actions[owner_domain].add(action_id)
        
        logger.debug(f"[ACTION-REGISTRY] Registered '{action_id}' → owner='{owner_domain}'")

    def register_alias(self, action_id: str, alias_domain: str) -> None:
        if action_id not in self._registry:
            logger.warning(
                f"[ACTION-REGISTRY] Cannot alias '{action_id}' to '{alias_domain}': "
                f"action not registered. Register owner first."
            )
            return
        self._registry[action_id].alias_domains.add(alias_domain)
        logger.debug(f"[ACTION-REGISTRY] Alias '{action_id}' ← '{alias_domain}'")

    def get_owner(self, action_id: str) -> str | None:
        reg = self._registry.get(action_id)
        return reg.owner_domain if reg else None

    def is_alias(self, action_id: str, domain_id: str) -> bool:
        reg = self._registry.get(action_id)
        if not reg:
            return False
        return domain_id in reg.alias_domains

    def should_delegate(self, action_id: str, calling_domain: str) -> str | None:
        reg = self._registry.get(action_id)
        if not reg:
            return None
        if reg.owner_domain == calling_domain:
            return None
        if calling_domain in reg.alias_domains:
            return reg.owner_domain
        return None

    def get_domain_actions(self, domain_id: str) -> set[str]:
        return self._domain_actions.get(domain_id, set())

    def get_conflicts(self) -> list[dict[str, Any]]:
        conflicts = []
        for action_id, reg in self._registry.items():
            if reg.alias_domains:
                conflicts.append({
                    "action_id": action_id,
                    "owner": reg.owner_domain,
                    "aliases": list(reg.alias_domains),
                })
        return conflicts

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_actions": len(self._registry),
            "total_domains": len(self._domain_actions),
            "conflicts": len(self.get_conflicts()),
            "actions_per_domain": {
                d: len(a) for d, a in self._domain_actions.items()
            },
        }

    def initialize_default_mappings(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.register("compare_candidates", "cv_screening", "Compare candidates using WSI scores")
        self.register_alias("compare_candidates", "sourcing")
        self.register_alias("compare_candidates", "recruiter_assistant")

        self.register("move_candidate", "pipeline_transition", "Move candidate between pipeline stages")
        self.register_alias("move_candidate", "recruiter_assistant")

        self.register("send_email", "communication", "Send email to candidate")
        self.register("send_whatsapp", "communication", "Send WhatsApp to candidate")

        self.register("score_candidate_wsi", "cv_screening", "Calculate WSI score")
        self.register("parse_cv", "cv_screening", "Parse candidate CV")
        self.register("create_job_vacancy", "job_management", "Create job vacancy")
        self.register("generate_job_description", "job_management", "Generate JD")
        self.register("search_candidates", "sourcing", "Search candidates")
        self.register("schedule_interview", "interview_scheduling", "Schedule interview")

        logger.info(
            f"[ACTION-REGISTRY] Initialized with {len(self._registry)} actions "
            f"across {len(self._domain_actions)} domains, "
            f"{len(self.get_conflicts())} controlled overlaps"
        )


def get_action_registry() -> DomainActionRegistry:
    registry = DomainActionRegistry()
    registry.initialize_default_mappings()
    return registry
