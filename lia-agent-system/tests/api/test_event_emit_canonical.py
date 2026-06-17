"""Sprint 7C Part 2 — emit canonical event tests.

Cobre:
6. talent_pools.add_candidates endpoint emite canonical event
   'candidate_added_to_pool' via publish_platform_event após DB commit.

Único emit canonical implementado em Part 2. Outros 3 eventos
(candidate_screened, agent_completed_review, weekly_summary) ficam pendentes
pra próximas sprints / outros agents.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_add_candidates_emits_canonical_event():
    """Test 6: POST /talent_pools/{pool_id}/add_candidates emite
    'candidate_added_to_pool' via publish_platform_event."""
    from app.api.v1 import talent_pools

    # Stub mínimo: payload com 2 candidate_ids
    pool_id = uuid4()
    company_id = "11111111-1111-1111-1111-111111111111"
    cid1, cid2 = 1001, 1002

    # Mock user + helpers
    fake_user = MagicMock()
    fake_db = MagicMock()
    fake_db.add = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.execute = AsyncMock()

    # Inexistente existing query result (cada candidate é novo)
    empty_result = MagicMock()
    empty_result.scalars = MagicMock(
        return_value=MagicMock(first=MagicMock(return_value=None))
    )
    fake_db.execute = AsyncMock(return_value=empty_result)

    payload = talent_pools.AddCandidatesToPoolRequest(
        candidate_ids=[cid1, cid2],
        origin="manual",
    )

    with patch.object(talent_pools, "_get_pool_or_404", new=AsyncMock(return_value=MagicMock())):
        with patch.object(talent_pools, "_refresh_counts", new=AsyncMock()):
            with patch.object(talent_pools, "get_user_company_id", return_value=company_id):
                with patch.object(
                    talent_pools, "publish_platform_event", new=AsyncMock(return_value=True)
                ) as mock_emit:
                    await talent_pools.add_candidates(
                        pool_id=pool_id,
                        payload=payload,
                        db=fake_db,
                        current_user=fake_user,
                        company_id=company_id,
                    )

                    # emit canonical called 1x após commit
                    mock_emit.assert_awaited_once()
                    event_arg = mock_emit.await_args.args[0]
                    # PlatformEvent canonical attrs
                    assert event_arg.event_type == "candidate_added_to_pool"
                    assert event_arg.company_id == company_id
                    assert "pool_id" in event_arg.payload
                    assert "candidate_ids" in event_arg.payload
