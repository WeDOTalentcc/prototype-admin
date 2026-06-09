"""
TDD — Supervisor memory parity (F5 2026-06-09).

Verifica via inspeção de código-fonte que:
1. _run_via_supervisor usa _eff_content (não content cru)
2. _run_via_supervisor usa _cid (não req.conversation_id or session_id)
3. _eff_content é definido no escopo compartilhado (antes de agent_task)
4. _ctx_prefix é construído no escopo compartilhado
5. _ehint é incluído em _eff_content (entity hint propagado)
6. Bloco duplicado de _eff_content foi removido de _run_agent
"""
import inspect
import sys
sys.path.insert(0, "/home/runner/workspace/lia-agent-system")


def _get_source():
    path = "/home/runner/workspace/lia-agent-system/app/api/v1/agent_chat_sse.py"
    with open(path) as f:
        return f.read()


def test_supervisor_uses_eff_content():
    """_run_via_supervisor deve usar _eff_content, não content cru."""
    src = _get_source()
    # Localizar bloco _build_supervisor_context
    idx = src.find("_build_supervisor_context(")
    assert idx != -1, "_build_supervisor_context não encontrado"
    block = src[idx:idx+400]
    assert "content=_eff_content," in block, (
        f"Supervisor deve usar content=_eff_content. Encontrado:\n{block}"
    )


def test_supervisor_uses_canonical_cid():
    """_run_via_supervisor deve usar _cid, não req.conversation_id or session_id."""
    src = _get_source()
    idx = src.find("_build_supervisor_context(")
    block = src[idx:idx+400]
    assert "conversation_id=_cid," in block, (
        f"Supervisor deve usar conversation_id=_cid. Encontrado:\n{block}"
    )
    assert "req.conversation_id or session_id" not in block, (
        "Supervisor NÃO deve usar req.conversation_id or session_id"
    )


def test_eff_content_hoisted_to_shared_scope():
    """_eff_content deve ser definido no escopo compartilhado, antes de agent_task."""
    src = _get_source()
    # _eff_content = content deve aparecer ANTES de agent_task = asyncio.create_task
    idx_eff = src.find("        _eff_content = content\n")
    idx_task = src.find("        agent_task = asyncio.create_task(")
    assert idx_eff != -1, "_eff_content = content não encontrado no escopo externo"
    assert idx_task != -1, "agent_task = asyncio.create_task não encontrado"
    assert idx_eff < idx_task, (
        f"_eff_content deve ser definido ANTES de agent_task. "
        f"_eff_content@{idx_eff}, agent_task@{idx_task}"
    )


def test_ctx_prefix_in_shared_scope():
    """_ctx_prefix deve ser construído no escopo compartilhado."""
    src = _get_source()
    idx_prefix = src.find("        _ctx_prefix = \"\"\n")
    idx_task = src.find("        agent_task = asyncio.create_task(")
    assert idx_prefix != -1, "_ctx_prefix = '' não encontrado no escopo externo"
    assert idx_prefix < idx_task, "_ctx_prefix deve ser definido ANTES de agent_task"


def test_ehint_included_in_eff_content():
    """Entity hint (_ehint) deve ser incluído no _eff_content hoisted."""
    src = _get_source()
    # Encontrar o bloco hoisted (antes de agent_task)
    idx_hoist_comment = src.find("_eff_content hoisted p/ escopo compartilhado")
    idx_task = src.find("        agent_task = asyncio.create_task(")
    assert idx_hoist_comment != -1, "Comentário do hoist não encontrado"
    hoist_block = src[idx_hoist_comment:idx_task]
    assert "_ehint" in hoist_block, "Entity hint deve ser aplicado no bloco hoisted"
    assert "NAO invente outro nome/titulo" in hoist_block, (
        "Instrução de entity hint deve estar no bloco hoisted"
    )


def test_no_duplicate_eff_content_in_run_agent():
    """Bloco duplicado de _ctx_prefix/_eff_content deve ter sido removido de _run_agent."""
    src = _get_source()
    # O bloco duplicado tinha um comentário característico
    assert "bloqueador-1 MEMORIA (v2): embute historico recente" not in src, (
        "Bloco duplicado de memória deve ter sido removido de _run_agent"
    )
    # Também não deve ter _ctx_prefix = '' duplicado dentro de _run_agent
    # (apenas 1 ocorrência do init, no escopo compartilhado)
    count = src.count('        _ctx_prefix = ""\n')
    assert count == 1, f"Esperado 1 _ctx_prefix init (no hoist), encontrado {count}"


if __name__ == "__main__":
    tests = [
        test_supervisor_uses_eff_content,
        test_supervisor_uses_canonical_cid,
        test_eff_content_hoisted_to_shared_scope,
        test_ctx_prefix_in_shared_scope,
        test_ehint_included_in_eff_content,
        test_no_duplicate_eff_content_in_run_agent,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"  ❌ {t.__name__} (ERROR): {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
