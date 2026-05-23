"""
Testes unitários para CandidateListStore (Phase 2 gap).
Cobre: set/get/delete, get_by_position, TTL, fallback in-memory,
       Redis indisponível, integração com MemoryResolver.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.memory.candidate_list_store import (
    CandidateListStore,
    LIST_TTL_SECONDS,
    KEY_PREFIX,
)
from app.orchestrator.memory.memory_resolver import MemoryResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CANDIDATES = [
    {"id": 10, "name": "Ana Lima", "score": 0.92},
    {"id": 20, "name": "Bruno Sá", "score": 0.87},
    {"id": 30, "name": "Carla Matos", "score": 0.81},
    {"id": 40, "name": "Diego Costa", "score": 0.75},
]


def make_store() -> CandidateListStore:
    from unittest.mock import AsyncMock
    store = CandidateListStore()
    # Force in-memory fallback to isolate tests from Redis state
    store._get_redis = AsyncMock(return_value=None)
    store._redis_available = False
    return store


# ---------------------------------------------------------------------------
# TTL constant
# ---------------------------------------------------------------------------

class TestConstants:
    def test_ttl_is_30_minutes(self):
        assert LIST_TTL_SECONDS == 1800

    def test_key_prefix(self):
        assert KEY_PREFIX == "candidate_list:"


# ---------------------------------------------------------------------------
# In-memory fallback (Redis indisponível)
# ---------------------------------------------------------------------------

class TestCandidateListStoreMemoryFallback:
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES)
        result = await store.get("conv-1")
        assert result == CANDIDATES

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self):
        store = make_store()
        result = await store.get("conv-missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_empty_list_is_noop(self):
        store = make_store()
        await store.set("conv-1", [])
        result = await store.get("conv-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_entry(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES)
        await store.delete("conv-1")
        result = await store.get("conv-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_missing_is_noop(self):
        store = make_store()
        # Não lança exceção
        await store.delete("conv-missing")

    @pytest.mark.asyncio
    async def test_get_by_position_first(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES)
        candidate = await store.get_by_position("conv-1", 0)
        assert candidate == CANDIDATES[0]
        assert candidate["name"] == "Ana Lima"

    @pytest.mark.asyncio
    async def test_get_by_position_third(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES)
        candidate = await store.get_by_position("conv-1", 2)
        assert candidate["name"] == "Carla Matos"

    @pytest.mark.asyncio
    async def test_get_by_position_out_of_range(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES)
        result = await store.get_by_position("conv-1", 10)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_position_negative(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES)
        result = await store.get_by_position("conv-1", -1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_position_missing_conv(self):
        store = make_store()
        result = await store.get_by_position("conv-missing", 0)
        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_conversations_isolated(self):
        store = make_store()
        await store.set("conv-A", CANDIDATES[:2])
        await store.set("conv-B", CANDIDATES[2:])
        a = await store.get("conv-A")
        b = await store.get("conv-B")
        assert len(a) == 2
        assert len(b) == 2
        assert a[0]["name"] == "Ana Lima"
        assert b[0]["name"] == "Carla Matos"

    @pytest.mark.asyncio
    async def test_overwrite_replaces_list(self):
        store = make_store()
        await store.set("conv-1", CANDIDATES[:2])
        new_list = [{"id": 99, "name": "Novo Candidato"}]
        await store.set("conv-1", new_list)
        result = await store.get("conv-1")
        assert len(result) == 1
        assert result[0]["name"] == "Novo Candidato"


# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------

class TestCandidateListStoreRedis:
    def _make_redis_store(self, redis_mock) -> CandidateListStore:
        store = CandidateListStore()
        store._redis = redis_mock
        store._redis_available = True
        return store

    @pytest.mark.asyncio
    async def test_set_calls_redis_setex(self):
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock()
        store = self._make_redis_store(redis_mock)

        await store.set("conv-1", CANDIDATES)

        redis_mock.setex.assert_called_once()
        call_args = redis_mock.setex.call_args
        assert call_args[0][0] == f"{KEY_PREFIX}conv-1"
        assert call_args[0][1] == LIST_TTL_SECONDS
        # Payload deve ser JSON string com os candidatos
        import json
        payload = json.loads(call_args[0][2])
        assert payload == CANDIDATES

    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self):
        import json
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=json.dumps(CANDIDATES))
        store = self._make_redis_store(redis_mock)

        result = await store.get("conv-1")
        assert result == CANDIDATES
        redis_mock.get.assert_called_once_with(f"{KEY_PREFIX}conv-1")

    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        store = self._make_redis_store(redis_mock)

        result = await store.get("conv-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_calls_redis_delete(self):
        redis_mock = AsyncMock()
        redis_mock.delete = AsyncMock()
        store = self._make_redis_store(redis_mock)

        await store.delete("conv-1")
        redis_mock.delete.assert_called_once_with(f"{KEY_PREFIX}conv-1")

    @pytest.mark.asyncio
    async def test_redis_set_failure_falls_back_to_memory(self):
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock(side_effect=Exception("Redis down"))
        store = self._make_redis_store(redis_mock)

        await store.set("conv-1", CANDIDATES)
        # Deve ter caído no fallback in-memory
        assert store._memory.get("conv-1") == CANDIDATES

    @pytest.mark.asyncio
    async def test_redis_get_failure_falls_back_to_memory(self):
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(side_effect=Exception("Redis down"))
        store = self._make_redis_store(redis_mock)
        store._memory["conv-1"] = CANDIDATES

        result = await store.get("conv-1")
        assert result == CANDIDATES

    @pytest.mark.asyncio
    async def test_get_ttl_calls_redis(self):
        redis_mock = AsyncMock()
        redis_mock.ttl = AsyncMock(return_value=900)
        store = self._make_redis_store(redis_mock)

        ttl = await store.get_ttl("conv-1")
        assert ttl == 900


# ---------------------------------------------------------------------------
# MemoryResolver integrado com CandidateListStore
# ---------------------------------------------------------------------------

class TestMemoryResolverWithCandidateListStore:
    @pytest.mark.asyncio
    async def test_positional_resolved_via_redis_store(self):
        """Resolução posicional usa dados completos do Redis (nome + score)."""
        store = make_store()
        await store.set("conv-1", CANDIDATES)

        resolver = MemoryResolver()
        enriched, was_resolved = await resolver.resolve(
            message="e o segundo?",
            session_id="conv-1",
            candidate_list_store=store,
        )

        assert was_resolved is True
        assert "Bruno Sá" in enriched
        assert "20" in enriched  # ID
        assert "posição 2" in enriched

    @pytest.mark.asyncio
    async def test_score_included_in_label(self):
        """Score do candidato deve aparecer no label quando presente."""
        store = make_store()
        await store.set("conv-x", [{"id": 5, "name": "Fernanda", "score": 0.95}])

        resolver = MemoryResolver()
        enriched, _ = await resolver.resolve(
            message="o primeiro",
            session_id="conv-x",
            candidate_list_store=store,
        )

        assert "95%" in enriched or "0.95" in enriched or "95" in enriched

    @pytest.mark.asyncio
    async def test_falls_back_to_conversation_state_when_store_empty(self):
        """Quando store não tem lista, usa IDs do ConversationState."""
        from app.shared.memory.conversation_state import ConversationState
        state = ConversationState()
        state.last_candidates_shown = [100, 200, 300]
        state.mentioned_candidates = {"Gustavo": 100}

        empty_store = make_store()  # sem dados
        resolver = MemoryResolver()

        enriched, was_resolved = await resolver.resolve(
            message="o primeiro candidato",
            session_id="conv-empty",
            conversation_state=state,
            candidate_list_store=empty_store,
        )

        assert was_resolved is True
        assert "Gustavo" in enriched
        assert "100" in enriched

    @pytest.mark.asyncio
    async def test_store_takes_priority_over_conversation_state(self):
        """Redis store tem prioridade sobre ConversationState (dados mais ricos)."""
        from app.shared.memory.conversation_state import ConversationState
        state = ConversationState()
        # Estado tem IDs diferentes dos do store (simulando desatualização)
        state.last_candidates_shown = [999]

        store = make_store()
        await store.set("conv-priority", [{"id": 42, "name": "Correto", "score": 0.90}])

        resolver = MemoryResolver()
        enriched, was_resolved = await resolver.resolve(
            message="o primeiro",
            session_id="conv-priority",
            conversation_state=state,
            candidate_list_store=store,
        )

        assert was_resolved is True
        assert "Correto" in enriched
        assert "42" in enriched
        assert "999" not in enriched  # ConversationState não foi usado

    @pytest.mark.asyncio
    async def test_store_error_falls_back_gracefully(self):
        """Erro no store não deve quebrar o fluxo."""
        from app.shared.memory.conversation_state import ConversationState
        state = ConversationState()
        state.last_candidates_shown = [55]

        broken_store = MagicMock()
        broken_store.get_by_position = AsyncMock(side_effect=Exception("store error"))

        resolver = MemoryResolver()
        # Deve cair no ConversationState sem raise
        enriched, was_resolved = await resolver.resolve(
            message="o primeiro",
            session_id="conv-err",
            conversation_state=state,
            candidate_list_store=broken_store,
        )

        assert was_resolved is True
        assert "55" in enriched
