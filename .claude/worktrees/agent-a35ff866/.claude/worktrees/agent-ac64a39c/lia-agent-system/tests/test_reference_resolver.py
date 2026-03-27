import pytest
from app.shared.memory.conversation_state import ConversationState
from app.shared.memory.reference_resolver import ReferenceResolver, ResolvedReference


class TestConversationState:
    def test_initial_state(self):
        state = ConversationState()
        assert state.last_candidates_shown == []
        assert state.last_candidate_detailed is None
        assert state.detailed_history == []
        assert state.shortlist == []
        assert state.mentioned_candidates == {}
        assert state.active_filters == {}
        assert state.last_search_term is None
        assert state.last_action is None
        assert state.last_job_id is None
        assert state.last_domain_id is None
        assert state.last_results_count is None

    def test_update_candidates_shown(self):
        state = ConversationState()
        state.update_candidates_shown([1, 2, 3, 4, 5])
        assert state.last_candidates_shown == [1, 2, 3, 4, 5]

    def test_update_candidates_shown_max_20(self):
        state = ConversationState()
        ids = list(range(1, 30))
        state.update_candidates_shown(ids)
        assert len(state.last_candidates_shown) == 20
        assert state.last_candidates_shown == list(range(1, 21))

    def test_update_candidate_detailed(self):
        state = ConversationState()
        state.update_candidate_detailed(42)
        assert state.last_candidate_detailed == 42
        assert state.detailed_history == [42]

    def test_detailed_history_max_10(self):
        state = ConversationState()
        for i in range(1, 15):
            state.update_candidate_detailed(i)
        assert len(state.detailed_history) == 10
        assert state.detailed_history == list(range(5, 15))
        assert state.last_candidate_detailed == 14

    def test_add_to_shortlist(self):
        state = ConversationState()
        result = state.add_to_shortlist(42)
        assert result is True
        assert 42 in state.shortlist

    def test_add_to_shortlist_duplicate(self):
        state = ConversationState()
        state.add_to_shortlist(42)
        result = state.add_to_shortlist(42)
        assert result is False
        assert state.shortlist.count(42) == 1

    def test_add_to_shortlist_max_50(self):
        state = ConversationState()
        for i in range(50):
            state.add_to_shortlist(i)
        result = state.add_to_shortlist(999)
        assert result is False
        assert len(state.shortlist) == 50

    def test_remove_from_shortlist(self):
        state = ConversationState()
        state.add_to_shortlist(42)
        result = state.remove_from_shortlist(42)
        assert result is True
        assert 42 not in state.shortlist

    def test_remove_from_shortlist_not_found(self):
        state = ConversationState()
        result = state.remove_from_shortlist(42)
        assert result is False

    def test_update_mentioned(self):
        state = ConversationState()
        state.update_mentioned("João Silva", 42)
        assert state.mentioned_candidates["João Silva"] == 42

    def test_to_dict_from_dict_roundtrip(self):
        state = ConversationState()
        state.update_candidates_shown([1, 2, 3])
        state.update_candidate_detailed(42)
        state.add_to_shortlist(10)
        state.update_mentioned("Maria", 5)
        state.active_filters = {"skill": "python"}
        state.last_search_term = "python dev"
        state.last_action = "search"
        state.last_job_id = 7
        state.last_domain_id = "sourcing"
        state.last_results_count = 3

        data = state.to_dict()
        restored = ConversationState.from_dict(data)

        assert restored.last_candidates_shown == [1, 2, 3]
        assert restored.last_candidate_detailed == 42
        assert restored.detailed_history == [42]
        assert restored.shortlist == [10]
        assert restored.mentioned_candidates == {"Maria": 5}
        assert restored.active_filters == {"skill": "python"}
        assert restored.last_search_term == "python dev"
        assert restored.last_action == "search"
        assert restored.last_job_id == 7
        assert restored.last_domain_id == "sourcing"
        assert restored.last_results_count == 3

    def test_clear(self):
        state = ConversationState()
        state.update_candidates_shown([1, 2, 3])
        state.update_candidate_detailed(42)
        state.add_to_shortlist(10)
        state.update_mentioned("Maria", 5)
        state.active_filters = {"skill": "python"}
        state.last_search_term = "test"
        state.last_action = "search"
        state.last_job_id = 7
        state.last_domain_id = "sourcing"
        state.last_results_count = 3

        state.clear()

        assert state.last_candidates_shown == []
        assert state.last_candidate_detailed is None
        assert state.detailed_history == []
        assert state.shortlist == []
        assert state.mentioned_candidates == {}
        assert state.active_filters == {}
        assert state.last_search_term is None
        assert state.last_action is None
        assert state.last_job_id is None
        assert state.last_domain_id is None
        assert state.last_results_count is None

    def test_update_after_action_with_candidates(self):
        state = ConversationState()
        response_data = {
            "candidates": [
                {"id": 1, "name": "João"},
                {"id": 2, "name": "Maria"},
                {"id": 3, "name": "Pedro"},
            ],
            "filters": {"skill": "python"},
            "search_term": "python dev",
        }
        state.update_after_action("search", "sourcing", response_data)
        assert state.last_candidates_shown == [1, 2, 3]
        assert state.last_results_count == 3
        assert state.last_action == "search"
        assert state.last_domain_id == "sourcing"
        assert state.mentioned_candidates["João"] == 1
        assert state.mentioned_candidates["Maria"] == 2
        assert state.active_filters == {"skill": "python"}
        assert state.last_search_term == "python dev"

    def test_update_after_action_with_candidate_detail(self):
        state = ConversationState()
        response_data = {
            "candidate": {"id": 42, "name": "Ana Costa"},
        }
        state.update_after_action("detail", "sourcing", response_data)
        assert state.last_candidate_detailed == 42
        assert state.mentioned_candidates["Ana Costa"] == 42

    def test_update_after_action_with_job_id(self):
        state = ConversationState()
        response_data = {"job_id": 99}
        state.update_after_action("create_job", "job_management", response_data)
        assert state.last_job_id == 99

    def test_update_after_action_non_dict(self):
        state = ConversationState()
        state.update_after_action("test", "test", "not a dict")
        assert state.last_action == "test"
        assert state.last_domain_id == "test"


class TestReferenceResolver:
    def setup_method(self):
        self.resolver = ReferenceResolver()
        self.state = ConversationState()

    def test_pronoun_dele(self):
        self.state.last_candidate_detailed = 42
        result = self.resolver.resolve("mostre o perfil dele", self.state)
        assert result.resolved is True
        assert result.reference_type == "pronoun"
        assert result.resolved_id == 42
        assert result.confidence > 0.8

    def test_pronoun_dela(self):
        self.state.last_candidate_detailed = 55
        result = self.resolver.resolve("qual o currículo dela", self.state)
        assert result.resolved is True
        assert result.reference_type == "pronoun"
        assert result.resolved_id == 55

    def test_pronoun_esse_candidato(self):
        self.state.last_candidate_detailed = 10
        result = self.resolver.resolve("detalhe esse candidato", self.state)
        assert result.resolved is True
        assert result.reference_type == "pronoun"
        assert result.resolved_id == 10

    def test_pronoun_no_context(self):
        result = self.resolver.resolve("mostre o perfil dele", self.state)
        assert result.resolved is False
        assert result.reference_type == "pronoun"

    def test_pronoun_fallback_to_first_candidate(self):
        self.state.last_candidates_shown = [100, 200, 300]
        result = self.resolver.resolve("conte sobre dele", self.state)
        assert result.resolved is True
        assert result.resolved_id == 100

    def test_position_primeiro(self):
        self.state.last_candidates_shown = [10, 20, 30]
        result = self.resolver.resolve("detalhe o primeiro", self.state)
        assert result.resolved is True
        assert result.reference_type == "position"
        assert result.resolved_id == 10

    def test_position_terceiro(self):
        self.state.last_candidates_shown = [10, 20, 30, 40, 50]
        result = self.resolver.resolve("mostre o terceiro", self.state)
        assert result.resolved is True
        assert result.reference_type == "position"
        assert result.resolved_id == 30

    def test_position_ultimo(self):
        self.state.last_candidates_shown = [10, 20, 30]
        result = self.resolver.resolve("mostre o último", self.state)
        assert result.resolved is True
        assert result.reference_type == "position"
        assert result.resolved_id == 30

    def test_position_numero(self):
        self.state.last_candidates_shown = [10, 20, 30, 40, 50]
        result = self.resolver.resolve("mostre o número 3", self.state)
        assert result.resolved is True
        assert result.reference_type == "position"
        assert result.resolved_id == 30

    def test_position_out_of_range(self):
        self.state.last_candidates_shown = [10, 20]
        result = self.resolver.resolve("mostre o quinto", self.state)
        assert result.resolved is False
        assert result.reference_type == "position"

    def test_position_empty_list(self):
        result = self.resolver.resolve("mostre o primeiro", self.state)
        assert result.resolved is False
        assert result.reference_type == "position"

    def test_previous_anterior(self):
        self.state.detailed_history = [10, 20, 30]
        result = self.resolver.resolve("volte ao anterior", self.state)
        assert result.resolved is True
        assert result.reference_type == "previous"
        assert result.resolved_id == 20

    def test_previous_no_history(self):
        self.state.detailed_history = [10]
        result = self.resolver.resolve("volte ao anterior", self.state)
        assert result.resolved is False
        assert result.reference_type == "previous"

    def test_shortlist_add_salve(self):
        self.state.last_candidate_detailed = 42
        result = self.resolver.resolve("salve esse candidato", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "add_shortlist"
        assert result.resolved_id == 42

    def test_shortlist_add_favorite(self):
        self.state.last_candidate_detailed = 55
        result = self.resolver.resolve("favorite esse", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "add_shortlist"

    def test_shortlist_show(self):
        self.state.shortlist = [1, 2, 3]
        result = self.resolver.resolve("mostre meus favoritos", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "show_shortlist"
        assert result.resolved_ids == [1, 2, 3]

    def test_shortlist_remove(self):
        self.state.last_candidate_detailed = 42
        result = self.resolver.resolve("remover dos favoritos", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "remove_shortlist"

    def test_continuation_desse_grupo(self):
        self.state.last_candidates_shown = [10, 20, 30]
        result = self.resolver.resolve("filtre desse grupo", self.state)
        assert result.resolved is True
        assert result.reference_type == "continuation"
        assert result.resolved_ids == [10, 20, 30]
        assert result.keep_filters is True

    def test_continuation_dentre_eles(self):
        self.state.last_candidates_shown = [5, 10, 15]
        result = self.resolver.resolve("dentre eles quem tem python", self.state)
        assert result.resolved is True
        assert result.reference_type == "continuation"
        assert result.resolved_ids == [5, 10, 15]

    def test_name_exact_match(self):
        self.state.mentioned_candidates = {"João Silva": 42}
        result = self.resolver.resolve("conte sobre João Silva", self.state)
        assert result.resolved is True
        assert result.reference_type == "name"
        assert result.resolved_id == 42

    def test_name_fuzzy_match(self):
        self.state.mentioned_candidates = {"João Silva": 42}
        result = self.resolver.resolve("mostre joao silva", self.state)
        assert result.resolved is True
        assert result.reference_type == "name"
        assert result.resolved_id == 42

    def test_name_no_match(self):
        self.state.mentioned_candidates = {"João Silva": 42}
        result = self.resolver.resolve("buscar candidatos python", self.state)
        assert result.resolved is False

    def test_cascade_shortlist_over_pronoun(self):
        self.state.last_candidate_detailed = 42
        result = self.resolver.resolve("salve dele nos favoritos", self.state)
        assert result.reference_type == "shortlist"
        assert result.action == "add_shortlist"

    def test_cascade_pronoun_over_position(self):
        self.state.last_candidate_detailed = 42
        self.state.last_candidates_shown = [10, 20, 30]
        result = self.resolver.resolve("mostre o perfil dele o primeiro", self.state)
        assert result.reference_type == "pronoun"
        assert result.resolved_id == 42

    def test_empty_query(self):
        result = self.resolver.resolve("", self.state)
        assert result.resolved is False
        assert result.reference_type == "none"

    def test_no_references(self):
        result = self.resolver.resolve("buscar candidatos python", self.state)
        assert result.resolved is False
        assert result.reference_type == "none"

    def test_normalize_query(self):
        normalized = self.resolver._normalize_query("  BUSCAR   candidatos   PYTHON  ")
        assert normalized == "buscar candidatos python"

    def test_should_keep_filters_true(self):
        assert self.resolver.should_keep_filters("com os mesmos critérios") is True
        assert self.resolver.should_keep_filters("manter filtros") is True

    def test_should_keep_filters_false(self):
        assert self.resolver.should_keep_filters("buscar candidatos python") is False

    def test_position_segunda(self):
        self.state.last_candidates_shown = [10, 20, 30]
        result = self.resolver.resolve("detalhe a segunda", self.state)
        assert result.resolved is True
        assert result.reference_type == "position"
        assert result.resolved_id == 20

    def test_shortlist_show_empty(self):
        result = self.resolver.resolve("mostre meus favoritos", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "show_shortlist"
        assert result.resolved_ids == []

    def test_detailed_history_dedup(self):
        state = ConversationState()
        state.update_candidate_detailed(10)
        state.update_candidate_detailed(20)
        state.update_candidate_detailed(10)
        assert state.detailed_history == [20, 10]
        assert state.last_candidate_detailed == 10
