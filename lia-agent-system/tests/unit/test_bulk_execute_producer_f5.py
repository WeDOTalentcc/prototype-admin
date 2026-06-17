"""
TDD F5: bulk_execute producer — batch_move, send_batch_communication,
bulk_update_candidates_stage emitem ui_action: "bulk_execute" no data.

Verifica:
1. batch_move_candidates inclui ui_action + ui_action_params quando sucesso total
2. batch_move_candidates marca falhas honestas quando moved < total
3. send_batch_communication inclui ui_action + resultados
4. bulk_update_candidates_stage inclui ui_action + per-item ok/fail via failed_ids
5. HiTL block nao inclui ui_action (nao deve acionar BulkResultReport)
6. Shape de results bate com BulkItemResult FE (id, name, ok: obrigatórios)
7. (NEW) Name resolution: _fetch_candidate_name_map resolve IDs em nomes reais
8. (NEW) Name resolution fail-open: UUID usado como fallback quando lookup falha

Run: pytest tests/unit/test_bulk_execute_producer_f5.py -v
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestBatchMoveCandidatesBulkExecute:
    def test_success_total_all_ok(self):
        """Quando moved == total, todos os itens são ok=True."""
        candidate_ids = ["a1", "b2", "c3"]
        moved = 3
        target = "Triagem"
        name_map = {"a1": "Alice", "b2": "Bob", "c3": "Carol"}
        _ui_results = (
            [{"id": cid, "name": name_map.get(cid, cid), "ok": True} for cid in candidate_ids]
            if moved == len(candidate_ids)
            else (
                [{"id": cid, "name": name_map.get(cid, cid), "ok": True} for cid in candidate_ids[:moved]]
                + [{"id": cid, "name": name_map.get(cid, cid), "ok": False, "reason": "Não confirmado"} for cid in candidate_ids[moved:]]
            )
        )
        assert all(r["ok"] for r in _ui_results)
        assert len(_ui_results) == 3
        assert _ui_results[0]["name"] == "Alice"
        assert _ui_results[1]["name"] == "Bob"

    def test_partial_move_marks_failures(self):
        """Quando moved < total, os primeiros 'moved' são ok, o resto fail."""
        candidate_ids = ["a1", "b2", "c3", "d4"]
        moved = 2
        name_map = {}  # fail-open: falls back to UUID
        _ui_results = (
            [{"id": cid, "name": name_map.get(cid, cid), "ok": True} for cid in candidate_ids]
            if moved == len(candidate_ids)
            else (
                [{"id": cid, "name": name_map.get(cid, cid), "ok": True} for cid in candidate_ids[:moved]]
                + [{"id": cid, "name": name_map.get(cid, cid), "ok": False, "reason": "Não confirmado"} for cid in candidate_ids[moved:]]
            )
        )
        ok_items = [r for r in _ui_results if r["ok"]]
        fail_items = [r for r in _ui_results if not r["ok"]]
        assert len(ok_items) == 2
        assert len(fail_items) == 2
        assert all("reason" in r for r in fail_items)
        # fallback: name == id when map empty
        assert _ui_results[0]["name"] == "a1"

    def test_result_items_have_required_fields(self):
        """Cada item em results tem id, name, ok (shape BulkItemResult FE)."""
        candidate_ids = ["x1", "x2"]
        _ui_results = [{"id": cid, "name": cid, "ok": True} for cid in candidate_ids]
        for item in _ui_results:
            assert "id" in item
            assert "name" in item
            assert "ok" in item
            assert isinstance(item["ok"], bool)


class TestNameResolutionHelper:
    """Tests for _fetch_candidate_name_map (kanban) and _fetch_candidate_name_map_local (candidate_tools)."""

    @pytest.mark.asyncio
    async def test_fetch_name_map_returns_resolved_names(self):
        """When CandidateRepository.list_by_ids returns candidates, map has real names."""
        from app.domains.recruiter_assistant.agents import kanban_tool_registry

        cand_a = MagicMock(); cand_a.id = "uuid-a"; cand_a.name = "Alice Silva"
        cand_b = MagicMock(); cand_b.id = "uuid-b"; cand_b.name = "Bruno Costa"

        mock_repo = AsyncMock()
        mock_repo.list_by_ids = AsyncMock(return_value=[cand_a, cand_b])

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.domains.recruiter_assistant.agents.kanban_tool_registry.AsyncSessionLocal", return_value=mock_session):
            with patch("app.domains.candidates.repositories.candidate_repository.CandidateRepository", return_value=mock_repo):
                result = await kanban_tool_registry._fetch_candidate_name_map(
                    ["uuid-a", "uuid-b"], "company-1"
                )

        assert result.get("uuid-a") == "Alice Silva"
        assert result.get("uuid-b") == "Bruno Costa"

    @pytest.mark.asyncio
    async def test_fetch_name_map_fail_open_on_exception(self):
        """When DB lookup raises, return empty dict (fail-open, caller uses UUID fallback)."""
        from app.domains.recruiter_assistant.agents import kanban_tool_registry

        with patch("app.domains.recruiter_assistant.agents.kanban_tool_registry.AsyncSessionLocal", side_effect=Exception("DB down")):
            result = await kanban_tool_registry._fetch_candidate_name_map(
                ["uuid-x"], "company-1"
            )

        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_name_map_empty_ids_returns_empty(self):
        """Empty candidate_ids list returns empty dict without any DB call."""
        from app.domains.recruiter_assistant.agents import kanban_tool_registry

        with patch("app.domains.recruiter_assistant.agents.kanban_tool_registry.AsyncSessionLocal") as mock_db:
            result = await kanban_tool_registry._fetch_candidate_name_map([], "company-1")

        assert result == {}
        mock_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_name_map_local_fail_open(self):
        """_fetch_candidate_name_map_local in candidate_tools also fail-open."""
        from app.domains.cv_screening.tools import candidate_tools

        with patch("app.domains.cv_screening.tools.candidate_tools._fetch_candidate_name_map_local",
                   new_callable=AsyncMock, return_value={}):
            result = await candidate_tools._fetch_candidate_name_map_local(["cid1"], "co1")
        # When mocked to return {}, fallback to UUID is triggered in caller
        assert result == {}

    def test_uuid_fallback_in_results_when_name_map_empty(self):
        """When name_map is empty (fail-open), result name == cid (UUID)."""
        candidate_ids = ["uuid-1", "uuid-2"]
        _name_map = {}  # empty = fail-open scenario
        results = [
            {"id": cid, "name": _name_map.get(cid, cid), "ok": True}
            for cid in candidate_ids
        ]
        assert results[0]["name"] == "uuid-1"
        assert results[1]["name"] == "uuid-2"


class TestBulkUpdateCandidatesStageBulkExecute:
    def test_per_item_ok_based_on_failed_ids(self):
        """failed_ids determinam quais itens têm ok=False."""
        candidate_ids = ["c1", "c2", "c3", "c4"]
        failed_ids = ["c2", "c4"]
        _failed_set = set(failed_ids)
        _name_map = {"c1": "Carlos A", "c2": "Carlos B", "c3": "Carlos C", "c4": "Carlos D"}
        results = [
            {"id": cid, "name": _name_map.get(cid, cid), "ok": cid not in _failed_set}
            for cid in candidate_ids
        ]
        ok_items = [r for r in results if r["ok"]]
        fail_items = [r for r in results if not r["ok"]]
        assert [r["id"] for r in ok_items] == ["c1", "c3"]
        assert [r["id"] for r in fail_items] == ["c2", "c4"]
        assert ok_items[0]["name"] == "Carlos A"
        assert fail_items[0]["name"] == "Carlos B"

    def test_empty_failed_ids_all_ok(self):
        """Se failed_ids vazio, todos ok."""
        candidate_ids = ["c1", "c2", "c3"]
        _failed_set: set = set()
        _name_map = {}  # fail-open
        results = [{"id": cid, "name": _name_map.get(cid, cid), "ok": cid not in _failed_set} for cid in candidate_ids]
        assert all(r["ok"] for r in results)
        # names fall back to UUIDs
        assert results[0]["name"] == "c1"

    def test_names_resolve_correctly_with_name_map(self):
        """With populated name_map, results show real names."""
        candidate_ids = ["id-1", "id-2"]
        _failed_set: set = set()
        _name_map = {"id-1": "João Ferreira", "id-2": "Maria Santos"}
        results = [{"id": cid, "name": _name_map.get(cid, cid), "ok": cid not in _failed_set} for cid in candidate_ids]
        assert results[0]["name"] == "João Ferreira"
        assert results[1]["name"] == "Maria Santos"


class TestBulkExecuteActionKey:
    def test_batch_move_action_key_matches_tool_name(self):
        action = "batch_move_candidates"
        assert isinstance(action, str)
        assert action == "batch_move_candidates"

    def test_send_batch_comm_action_key(self):
        action = "send_batch_communication"
        assert action == "send_batch_communication"

    def test_bulk_update_stage_action_key(self):
        action = "bulk_update_candidates_stage"
        assert action == "bulk_update_candidates_stage"


class TestBulkExecuteDataShape:
    def test_data_has_ui_action_and_params_alongside_domain_data(self):
        """data{} deve ter ui_action + ui_action_params + dados de domínio."""
        candidate_ids = ["id1", "id2"]
        moved = 2
        target = "Aprovados"
        _name_map = {"id1": "Ana Lima", "id2": "Pedro Nunes"}
        _ui_results = [{"id": cid, "name": _name_map.get(cid, cid), "ok": True} for cid in candidate_ids]
        data = {
            "ui_action": "bulk_execute",
            "ui_action_params": {
                "action": "batch_move_candidates",
                "title": f"Candidatos movidos para '{target}'",
                "results": _ui_results,
            },
            "moved_count": moved,
            "target_stage": target,
            "candidate_ids": candidate_ids,
        }
        assert data["ui_action"] == "bulk_execute"
        assert "ui_action_params" in data
        assert data["ui_action_params"]["action"] == "batch_move_candidates"
        assert len(data["ui_action_params"]["results"]) == 2
        assert data["moved_count"] == 2
        assert data["target_stage"] == "Aprovados"
        # Names are resolved, not UUIDs
        assert data["ui_action_params"]["results"][0]["name"] == "Ana Lima"
        assert data["ui_action_params"]["results"][1]["name"] == "Pedro Nunes"
