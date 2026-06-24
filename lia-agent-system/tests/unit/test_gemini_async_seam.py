"""Pina o P1 (Funil de Talentos audit 2026-06-06): generate_with_gemini async
chamava o SDK SINCRONO client.models.generate_content -> dentro do event loop
o credit-gate sync (_enforce_credit_gate_sync, llm_bootstrap.py:220) levanta
RuntimeError "called from running event loop". Sintoma no log: repetidos
"Prompt enhancement failed: _enforce_credit_gate_sync ... provider=gemini"
durante a busca de candidatos (misc_search.py:367).

Fix canonico: usar o seam ASYNC client.aio.models.generate_content, espelhando
generate_native_gemini (llm.py:326), que ja roteia pelo gate async.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.ai.services.llm import llm_service


@pytest.mark.asyncio
async def test_generate_with_gemini_uses_async_seam(monkeypatch):
    fake_resp = MagicMock()
    fake_resp.text = "ok-async"

    aio_gen = AsyncMock(return_value=fake_resp)
    sync_gen = MagicMock(
        side_effect=AssertionError(
            "SDK Gemini SINCRONO chamado de dentro de metodo async — "
            "usar client.aio.models.generate_content"
        )
    )

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = aio_gen
    fake_client.models.generate_content = sync_gen

    # gemini_native property retorna self._gemini_client quando truthy
    monkeypatch.setattr(llm_service, "_gemini_client", fake_client)

    result = await llm_service.generate_with_gemini("oi")

    assert result == "ok-async"
    aio_gen.assert_awaited_once()
    sync_gen.assert_not_called()
