"""
Testes unitários para MemoryResolver (Phase 2).
Cobre: resolução posicional, should_keep_filters, is_pagination_request,
pronomes via WorkingMemory, ConversationState novos campos.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.memory.memory_resolver import (
    MemoryResolver,
    memory_resolver,
    is_pagination_request,
    should_keep_filters,
    _resolve_positional,
    _should_resolve,
)
from app.shared.memory.conversation_state import ConversationState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_state(**kwargs) -> ConversationState:
    state = ConversationState()
    for k, v in kwargs.items():
        setattr(state, k, v)
    return state


# ---------------------------------------------------------------------------
# is_pagination_request
# ---------------------------------------------------------------------------

class TestIsPaginationRequest:
    def test_mostra_mais(self):
        assert is_pagination_request("mostra mais") is True

    def test_ver_mais(self):
        assert is_pagination_request("ver mais candidatos") is True

    def test_proximos(self):
        assert is_pagination_request("próximos 10") is True

    def test_mais_candidatos(self):
        assert is_pagination_request("quero ver mais candidatos") is True

    def test_normal_message(self):
        assert is_pagination_request("quem são os top 5?") is False

    def test_proxima_fase(self):
        # "próxima fase" não é paginação
        assert is_pagination_request("mover para próxima fase") is False


# ---------------------------------------------------------------------------
# should_keep_filters
# ---------------------------------------------------------------------------

class TestShouldKeepFilters:
    def test_pronoun_e_ele(self):
        assert should_keep_filters("e ele?") is True

    def test_pronoun_e_ela(self):
        assert should_keep_filters("e ela também?") is True

    def test_continuity_e_o_segundo(self):
        assert should_keep_filters("e o segundo candidato?") is True

    def test_new_search_busca(self):
        assert should_keep_filters("busca candidatos Python em São Paulo") is False

    def test_new_search_filtra(self):
        assert should_keep_filters("filtra por senioridade: senior") is False

    def test_new_search_procura(self):
        assert should_keep_filters("procura por React developers") is False

    def test_neutral_question(self):
        # Sem pronomes e sem keywords de busca → não mantém filtros
        assert should_keep_filters("quais são os requisitos?") is False

    def test_pronoun_without_new_search(self):
        assert should_keep_filters("aprova esse candidato") is True


# ---------------------------------------------------------------------------
# _resolve_positional
# ---------------------------------------------------------------------------

class TestResolvePositional:
    def test_terceiro(self):
        ids = [10, 20, 30, 40]
        result = _resolve_positional("e o terceiro?", ids)
        assert result == (2, 30)

    def test_primeiro(self):
        ids = [100, 200]
        result = _resolve_positional("o primeiro candidato", ids)
        assert result == (0, 100)

    def test_segundo(self):
        ids = [11, 22, 33]
        result = _resolve_positional("analisa o segundo", ids)
        assert result == (1, 22)

    def test_out_of_range(self):
        ids = [10, 20]
        result = _resolve_positional("o quinto candidato", ids)
        assert result is None

    def test_empty_list(self):
        result = _resolve_positional("o primeiro", [])
        assert result is None

    def test_no_positional(self):
        ids = [10, 20, 30]
        result = _resolve_positional("mover candidato para entrevista", ids)
        assert result is None

    def test_ordinal_symbol(self):
        ids = [5, 10, 15, 20]
        result = _resolve_positional("analisa o 3º", ids)
        assert result == (2, 15)


# ---------------------------------------------------------------------------
# ConversationState — Phase 2 new fields
# ---------------------------------------------------------------------------

class TestConversationStatePhase2:
    def test_default_last_entity_is_none(self):
        state = ConversationState()
        assert state.last_entity is None

    def test_default_pagination_cursor_is_zero(self):
        state = ConversationState()
        assert state.pagination_cursor == 0

    def test_update_last_entity(self):
        state = ConversationState()
        state.update_last_entity("candidate", 42, "João Silva")
        assert state.last_entity == {"type": "candidate", "id": 42, "name": "João Silva"}

    def test_advance_pagination(self):
        state = ConversationState()
        new_cursor = state.advance_pagination(page_size=10)
        assert new_cursor == 10
        assert state.pagination_cursor == 10

    def test_advance_pagination_twice(self):
        state = ConversationState()
        state.advance_pagination(10)
        new_cursor = state.advance_pagination(10)
        assert new_cursor == 20

    def test_reset_pagination(self):
        state = ConversationState()
        state.advance_pagination(10)
        state.reset_pagination()
        assert state.pagination_cursor == 0

    def test_to_dict_includes_new_fields(self):
        state = ConversationState()
        state.update_last_entity("job", "j-1", "Dev Python")
        state.advance_pagination(5)
        d = state.to_dict()
        assert d["last_entity"] == {"type": "job", "id": "j-1", "name": "Dev Python"}
        assert d["pagination_cursor"] == 5

    def test_from_dict_restores_new_fields(self):
        data = {
            "last_entity": {"type": "sourcing", "id": 99, "name": "Busca Python"},
            "pagination_cursor": 20,
        }
        state = ConversationState.from_dict(data)
        assert state.last_entity == {"type": "sourcing", "id": 99, "name": "Busca Python"}
        assert state.pagination_cursor == 20

    def test_clear_resets_new_fields(self):
        state = ConversationState()
        state.update_last_entity("candidate", 1, "Ana")
        state.advance_pagination(10)
        state.clear()
        assert state.last_entity is None
        assert state.pagination_cursor == 0

    def test_update_after_action_sets_last_entity(self):
        state = ConversationState()
        response_data = {
            "candidate": {"id": 55, "name": "Carlos Melo"},
        }
        state.update_after_action("get_candidate", "talent", response_data)
        assert state.last_entity == {"type": "candidate", "id": 55, "name": "Carlos Melo"}


# ---------------------------------------------------------------------------
# MemoryResolver.resolve() — posicional via ConversationState
# ---------------------------------------------------------------------------

class TestMemoryResolverPositional:
    @pytest.mark.asyncio
    async def test_positional_resolved_from_state(self):
        state = make_state(
            last_candidates_shown=[10, 20, 30],
            mentioned_candidates={"João": 10, "Maria": 20, "Pedro": 30},
        )
        resolver = MemoryResolver()
        enriched, was_resolved = await resolver.resolve(
            message="e o terceiro?",
            session_id="sess-1",
            conversation_state=state,
        )
        assert was_resolved is True
        assert "30" in enriched or "Pedro" in enriched
        assert "posição 3" in enriched

    @pytest.mark.asyncio
    async def test_positional_with_name(self):
        state = make_state(
            last_candidates_shown=[100, 200],
            mentioned_candidates={"Ana": 100},
        )
        resolver = MemoryResolver()
        enriched, was_resolved = await resolver.resolve(
            message="o primeiro candidato",
            session_id="sess-1",
            conversation_state=state,
        )
        assert was_resolved is True
        assert "Ana" in enriched
        assert "100" in enriched

    @pytest.mark.asyncio
    async def test_positional_out_of_range_falls_to_working_memory(self):
        state = make_state(last_candidates_shown=[10])

        with patch("lia_agents_core.working_memory.WorkingMemoryService") as MockWMS:
            mock_service = AsyncMock()
            mock_service.get_context_summary = AsyncMock(return_value=None)
            MockWMS.return_value = mock_service

            resolver = MemoryResolver()
            enriched, was_resolved = await resolver.resolve(
                message="o quinto candidato",
                session_id="sess-1",
                conversation_state=state,
            )
        # Out of range → falls through → WorkingMemory returns None → no resolution
        assert was_resolved is False
        assert enriched == "o quinto candidato"


# ---------------------------------------------------------------------------
# MemoryResolver.resolve() — pronomes via WorkingMemory
# ---------------------------------------------------------------------------

class TestMemoryResolverPronouns:
    @pytest.mark.asyncio
    async def test_pronoun_resolved_via_working_memory(self):
        with patch("lia_agents_core.working_memory.WorkingMemoryService") as MockWMS:
            mock_service = AsyncMock()
            mock_service.get_context_summary = AsyncMock(return_value={
                "last_candidate": {"id": 42, "name": "Beatriz Santos"},
            })
            MockWMS.return_value = mock_service

            resolver = MemoryResolver()
            enriched, was_resolved = await resolver.resolve(
                message="move ela para entrevista",
                session_id="sess-2",
            )

        assert was_resolved is True
        assert "Beatriz Santos" in enriched

    @pytest.mark.asyncio
    async def test_no_pronoun_skips_resolution(self):
        resolver = MemoryResolver()
        enriched, was_resolved = await resolver.resolve(
            message="quem são os top 5 candidatos?",
            session_id="sess-3",
        )
        assert was_resolved is False
        assert enriched == "quem são os top 5 candidatos?"

    @pytest.mark.asyncio
    async def test_working_memory_unavailable_returns_original(self):
        with patch("lia_agents_core.working_memory.WorkingMemoryService") as MockWMS:
            MockWMS.side_effect = Exception("DB unavailable")
            resolver = MemoryResolver()
            enriched, was_resolved = await resolver.resolve(
                message="mover ele para triagem",
                session_id="sess-err",
            )
        assert was_resolved is False
        assert enriched == "mover ele para triagem"

    @pytest.mark.asyncio
    async def test_last_entity_from_state_prepended(self):
        state = make_state()
        state.update_last_entity("job", "j-10", "Engenheiro de Dados")

        with patch("lia_agents_core.working_memory.WorkingMemoryService") as MockWMS:
            mock_service = AsyncMock()
            mock_service.get_context_summary = AsyncMock(return_value={
                "last_candidate": {"id": 1, "name": "X"},
            })
            MockWMS.return_value = mock_service

            resolver = MemoryResolver()
            enriched, was_resolved = await resolver.resolve(
                message="atualizar a vaga",
                session_id="sess-4",
                conversation_state=state,
            )

        assert was_resolved is True
        assert "Engenheiro de Dados" in enriched
        assert "j-10" in enriched
