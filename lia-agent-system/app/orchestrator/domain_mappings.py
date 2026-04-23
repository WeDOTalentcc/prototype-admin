"""
Centralized domain mappings — single source of truth for agent-type → domain resolution.

Used by CascadedRouter (Tier 5 LLM output mapping) and available for any module
that needs to resolve an agent type string to its canonical domain_id.

The ``AGENT_TYPE_TO_DOMAIN`` mapping is **auto-discovered** from the
``DomainRegistry``: each domain declares its own aliases via the
``agent_aliases`` attribute (or the ``get_agent_aliases()`` classmethod) on
``DomainPrompt``. This eliminates the drift that previously occurred when an
agent-type string in this dict pointed to a domain id that was never
registered (see task #580 — 10 orphans resolved manually).

Adding a new agent-type alias is therefore a one-file change in the owning
domain. There is no list to keep in sync here.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN = "recruiter_assistant"


def _build_agent_type_to_domain() -> dict[str, str]:
    """Build the alias → domain_id mapping from the DomainRegistry.

    Importing ``app.domains`` triggers the ``@register_domain`` decorators for
    every domain module. We then ask each registered class for its aliases.

    If two domains claim the same alias the first registration wins and a
    warning is logged (a registry collision is a real bug — fail loudly via
    the log; the test ``test_no_orphan_agent_types`` will catch it in CI).
    """
    # Local import to avoid an import cycle: app.orchestrator.__init__ imports
    # this module, and some app.domains.* sub-modules lazily import from
    # app.orchestrator inside functions. Top-level domain modules do NOT
    # import the orchestrator, so this import is safe at runtime.
    import app.domains  # noqa: F401  — side-effect: triggers @register_domain
    from app.domains.registry import _DOMAIN_REGISTRY

    mapping: dict[str, str] = {}
    for registry_key, cls in _DOMAIN_REGISTRY.items():
        # A few domains expose ``domain_id`` as a @property instead of a class
        # attribute; in that case ``cls.domain_id`` is the property object and
        # ``registry_key`` is also that object. Resolve via instantiation.
        domain_id = cls.domain_id if isinstance(cls.domain_id, str) else None
        aliases: list[str] = []
        if domain_id:
            try:
                aliases = list(cls.get_agent_aliases())
            except Exception as exc:  # pragma: no cover — defensive
                logger.error(
                    "Domain %s.get_agent_aliases() raised %s — skipping",
                    domain_id,
                    exc,
                )
                continue
        else:
            try:
                instance = cls()
                domain_id = instance.domain_id
                if not isinstance(domain_id, str) or not domain_id:
                    raise ValueError(f"empty domain_id on {cls.__name__}")
                # Method may be defined on instance; fall back to class default.
                get_aliases = getattr(instance, "get_agent_aliases", None)
                aliases = list(get_aliases()) if get_aliases else [domain_id]
                if domain_id not in aliases:
                    aliases = [domain_id, *aliases]
            except Exception as exc:  # pragma: no cover — defensive
                logger.error(
                    "Could not resolve domain_id for %s (registry_key=%r): %s",
                    cls.__name__, registry_key, exc,
                )
                continue
        for alias in aliases:
            existing = mapping.get(alias)
            if existing and existing != domain_id:
                logger.warning(
                    "Agent-type alias collision: %r already mapped to %r, "
                    "ignoring claim from %r (class=%s)",
                    alias,
                    existing,
                    domain_id,
                    cls.__name__,
                )
                continue
            mapping[alias] = domain_id
    return mapping


# Cache the built mapping once domains are registered. We expose it via PEP
# 562 ``__getattr__`` so the (relatively expensive) registry walk happens
# lazily on first access — this matters because importing this module from
# ``app.orchestrator.__init__`` happens before ``app.domains`` is imported in
# many tests, and we must not eagerly trigger that import here.
_CACHED_MAPPING: dict[str, str] | None = None


def _get_mapping() -> dict[str, str]:
    global _CACHED_MAPPING
    if _CACHED_MAPPING is None:
        _CACHED_MAPPING = _build_agent_type_to_domain()
    return _CACHED_MAPPING


def reset_mapping_cache() -> None:
    """Clear the cached mapping (testing helper)."""
    global _CACHED_MAPPING
    _CACHED_MAPPING = None


def __getattr__(name: str):  # PEP 562
    if name == "AGENT_TYPE_TO_DOMAIN":
        return _get_mapping()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def resolve_domain(intent: str) -> str:
    """Resolve an intent/agent-type string to its canonical domain_id."""
    intent_lower = str(intent).lower().strip()
    mapping = _get_mapping()

    if intent_lower in mapping:
        return mapping[intent_lower]

    for agent_key, domain_id in mapping.items():
        if agent_key in intent_lower or intent_lower in agent_key:
            return domain_id

    return DEFAULT_DOMAIN
