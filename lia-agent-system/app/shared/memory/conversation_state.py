import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

MAX_CANDIDATES_SHOWN = 20
MAX_DETAILED_HISTORY = 10
MAX_SHORTLIST = 50

_DEFAULT_TTL_SECONDS = 1800  # 30 minutes
_DEFAULT_MAX_SIZE = 1000


@dataclass
class ConversationState:
    company_id: str | None = None  # Multi-tenancy: tenant isolation
    last_candidates_shown: list[int] = field(default_factory=list)
    last_candidate_detailed: int | None = None
    detailed_history: list[int] = field(default_factory=list)
    shortlist: list[int] = field(default_factory=list)
    mentioned_candidates: dict[str, int] = field(default_factory=dict)
    active_filters: dict[str, Any] = field(default_factory=dict)
    last_search_term: str | None = None
    last_action: str | None = None
    last_job_id: int | None = None
    last_domain_id: str | None = None
    last_results_count: int | None = None
    # Phase 2 — MemoryResolver expansion
    last_entity: dict[str, Any] | None = None  # {type, id, name} último mencionado
    pagination_cursor: int = 0                     # offset para "mostra mais"

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "last_candidates_shown": self.last_candidates_shown,
            "last_candidate_detailed": self.last_candidate_detailed,
            "detailed_history": self.detailed_history,
            "shortlist": self.shortlist,
            "mentioned_candidates": self.mentioned_candidates,
            "active_filters": self.active_filters,
            "last_search_term": self.last_search_term,
            "last_action": self.last_action,
            "last_job_id": self.last_job_id,
            "last_domain_id": self.last_domain_id,
            "last_results_count": self.last_results_count,
            "last_entity": self.last_entity,
            "pagination_cursor": self.pagination_cursor,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationState":
        return cls(
            company_id=data.get("company_id"),
            last_candidates_shown=data.get("last_candidates_shown", []),
            last_candidate_detailed=data.get("last_candidate_detailed"),
            detailed_history=data.get("detailed_history", []),
            shortlist=data.get("shortlist", []),
            mentioned_candidates=data.get("mentioned_candidates", {}),
            active_filters=data.get("active_filters", {}),
            last_search_term=data.get("last_search_term"),
            last_action=data.get("last_action"),
            last_job_id=data.get("last_job_id"),
            last_domain_id=data.get("last_domain_id"),
            last_results_count=data.get("last_results_count"),
            last_entity=data.get("last_entity"),
            pagination_cursor=data.get("pagination_cursor", 0),
        )

    def clear(self) -> None:
        _company_id = self.company_id  # Preserve tenant context
        self.last_candidates_shown = []
        self.last_candidate_detailed = None
        self.detailed_history = []
        self.shortlist = []
        self.mentioned_candidates = {}
        self.active_filters = {}
        self.last_search_term = None
        self.last_action = None
        self.last_job_id = None
        self.last_domain_id = None
        self.last_results_count = None
        self.last_entity = None
        self.pagination_cursor = 0
        self.company_id = _company_id  # Restore tenant context
        logger.debug("ConversationState cleared")

    def update_after_action(self, action_id: str, domain_id: str, response_data: Any) -> None:
        self.last_action = action_id
        self.last_domain_id = domain_id

        if not isinstance(response_data, dict):
            return

        candidates = response_data.get("candidates") or response_data.get("candidate_ids")
        if isinstance(candidates, list):
            candidate_ids = []
            for c in candidates:
                if isinstance(c, dict) and "id" in c:
                    candidate_ids.append(c["id"])
                    name = c.get("name") or c.get("nome")
                    if name:
                        self.update_mentioned(name, c["id"])
                elif isinstance(c, int):
                    candidate_ids.append(c)
            if candidate_ids:
                self.update_candidates_shown(candidate_ids)
                self.last_results_count = len(candidate_ids)

        candidate = response_data.get("candidate") or response_data.get("candidate_detail")
        if isinstance(candidate, dict) and "id" in candidate:
            self.update_candidate_detailed(candidate["id"])
            name = candidate.get("name") or candidate.get("nome") or ""
            if name:
                self.update_mentioned(name, candidate["id"])
            self.update_last_entity("candidate", candidate["id"], name)

        job_id = response_data.get("job_id")
        if isinstance(job_id, int):
            self.last_job_id = job_id

        filters = response_data.get("filters") or response_data.get("active_filters")
        if isinstance(filters, dict):
            self.active_filters = filters

        search_term = response_data.get("search_term") or response_data.get("query")
        if isinstance(search_term, str):
            self.last_search_term = search_term

        logger.debug(f"ConversationState updated after action={action_id} domain={domain_id}")

    def add_to_shortlist(self, candidate_id: int) -> bool:
        if candidate_id in self.shortlist:
            return False
        if len(self.shortlist) >= MAX_SHORTLIST:
            logger.warning(f"Shortlist at max capacity ({MAX_SHORTLIST})")
            return False
        self.shortlist.append(candidate_id)
        logger.debug(f"Added candidate {candidate_id} to shortlist")
        return True

    def remove_from_shortlist(self, candidate_id: int) -> bool:
        if candidate_id not in self.shortlist:
            return False
        self.shortlist.remove(candidate_id)
        logger.debug(f"Removed candidate {candidate_id} from shortlist")
        return True

    def update_candidates_shown(self, candidate_ids: list[int]) -> None:
        self.last_candidates_shown = candidate_ids[:MAX_CANDIDATES_SHOWN]
        logger.debug(f"Updated candidates shown: {len(self.last_candidates_shown)} candidates")

    def update_candidate_detailed(self, candidate_id: int) -> None:
        self.last_candidate_detailed = candidate_id
        if candidate_id in self.detailed_history:
            self.detailed_history.remove(candidate_id)
        self.detailed_history.append(candidate_id)
        if len(self.detailed_history) > MAX_DETAILED_HISTORY:
            self.detailed_history = self.detailed_history[-MAX_DETAILED_HISTORY:]
        logger.debug(f"Updated candidate detailed: {candidate_id}")

    def update_mentioned(self, name: str, candidate_id: int) -> None:
        self.mentioned_candidates[name] = candidate_id
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"Updated mentioned candidate: {name} -> {candidate_id}")

    def update_last_entity(self, entity_type: str, entity_id: Any, name: str = "") -> None:
        """Registra a última entidade mencionada para resolução de pronomes."""
        self.last_entity = {"type": entity_type, "id": entity_id, "name": name}
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"Updated last_entity: {entity_type}:{entity_id} name={name!r}")

    def advance_pagination(self, page_size: int = 10) -> int:
        """Avança o cursor de paginação. Retorna o novo offset."""
        self.pagination_cursor += page_size
        return self.pagination_cursor

    def reset_pagination(self) -> None:
        """Reseta o cursor de paginação (nova busca)."""
        self.pagination_cursor = 0


class ConversationStateStore:
    """In-memory LRU store for ConversationState with TTL-based expiration.

    Prevents unbounded memory growth in long-running processes by evicting
    entries that exceed the TTL or the max-size cap.

    Configuration via environment variables:
        CONVERSATION_STATE_TTL_SECONDS  — default 1800 (30 min)
        CONVERSATION_STATE_MAX_SIZE     — default 1000
    """

    def __init__(
        self,
        ttl_seconds: int | None = None,
        max_size: int | None = None,
    ) -> None:
        self.ttl_seconds: int = ttl_seconds or int(
            os.environ.get("CONVERSATION_STATE_TTL_SECONDS", _DEFAULT_TTL_SECONDS)
        )
        self.max_size: int = max_size or int(
            os.environ.get("CONVERSATION_STATE_MAX_SIZE", _DEFAULT_MAX_SIZE)
        )
        # OrderedDict for LRU: most-recently-used at the end
        self._entries: OrderedDict[str, tuple[ConversationState, float]] = OrderedDict()
        self._op_count: int = 0
        self._cleanup_interval: int = 100

    # -- public API (matches dict-like usage) --------------------------------

    def get(self, conversation_id: str) -> ConversationState | None:
        """Return the state for *conversation_id*, or None if missing/expired."""
        self._tick()
        entry = self._entries.get(conversation_id)
        if entry is None:
            return None
        state, created_at = entry
        if self._is_expired(created_at):
            del self._entries[conversation_id]
            logger.debug("ConversationStateStore: evicted expired key=%s", conversation_id)
            return None
        # Move to end (most-recently-used)
        self._entries.move_to_end(conversation_id)
        return state

    def set(self, conversation_id: str, state: ConversationState) -> None:
        """Store or replace the state for *conversation_id*."""
        self._tick()
        if conversation_id in self._entries:
            self._entries.move_to_end(conversation_id)
        self._entries[conversation_id] = (state, time.monotonic())
        self._evict_if_over_capacity()

    def delete(self, conversation_id: str) -> None:
        """Remove a single entry."""
        self._entries.pop(conversation_id, None)

    def __contains__(self, conversation_id: str) -> bool:
        return self.get(conversation_id) is not None

    def __len__(self) -> int:
        return len(self._entries)

    # -- internal helpers ----------------------------------------------------

    def _is_expired(self, created_at: float) -> bool:
        return (time.monotonic() - created_at) > self.ttl_seconds

    def _evict_if_over_capacity(self) -> None:
        """Drop oldest entries until we are at or below max_size."""
        while len(self._entries) > self.max_size:
            key, _ = self._entries.popitem(last=False)
            logger.debug("ConversationStateStore: LRU evicted key=%s", key)

    def _tick(self) -> None:
        """Periodic lazy cleanup of expired entries (every N operations)."""
        self._op_count += 1
        if self._op_count >= self._cleanup_interval:
            self._op_count = 0
            self._purge_expired()

    def _purge_expired(self) -> None:
        """Scan and remove all expired entries."""
        now = time.monotonic()
        expired = [k for k, (_, ts) in self._entries.items() if (now - ts) > self.ttl_seconds]
        for k in expired:
            del self._entries[k]
        if expired:
            logger.info("ConversationStateStore: purged %d expired entries", len(expired))


# Module-level singleton
conversation_state_store = ConversationStateStore()
