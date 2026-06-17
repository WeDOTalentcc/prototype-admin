"""2-table P2 sensor (2026-06-06).

As tools que emitem response_blocks (ranking/comparacao/perfil) co-locam um
render_hint no result instruindo o LLM a NAO duplicar os dados como tabela
markdown no texto (o bloco visual e a fonte unica). Os agentes de dominio NAO
usam system_prompt_builder, entao o guide vai no result da tool. Este sensor
pina (a) o texto do hint e (b) que as 3 tools wiram render_hint -- sem precisar
de DB.
"""
from __future__ import annotations

import inspect


def test_narrate_hint_text_is_explicit():
    from app.domains.recruiter_assistant.agents import talent_tool_registry as T

    assert "NAO repita" in T._RRP_NARRATE_HINT
    assert "tabela markdown" in T._RRP_NARRATE_HINT


def test_rrp_tools_colocate_render_hint():
    from app.domains.recruiter_assistant.agents import talent_tool_registry as T

    src = inspect.getsource(T)
    # rank + compare + profile -> 3 wirings da chave render_hint no result
    assert src.count('"render_hint"') >= 3, (
        "Alguma tool RRP deixou de co-locar render_hint -> volta o 2-table "
        "(LLM duplica a tabela markdown alem do bloco visual)."
    )
