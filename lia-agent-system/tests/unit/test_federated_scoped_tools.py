"""TDD Fase 2: escopo dinamico de tools no federado (contextvar + _resolve_scoped_tool_defs).
Flag off = set default; flag on + escopo ativo = subconjunto escopado de todos os dominios."""
import os

import pytest

from app.domains.recruiter_assistant.agents.recruiter_copilot_react_agent import (
    _resolve_scoped_tool_defs,
    _scoped_tools_enabled,
)
from app.tools.scope_config import PromptScope, reset_active_scope, set_active_scope


class _D:
    def __init__(self, n):
        self.name = n


@pytest.fixture(autouse=True)
def _clean():
    os.environ.pop("LIA_FEDERATED_SCOPED_TOOLS", None)
    reset_active_scope()
    yield
    os.environ.pop("LIA_FEDERATED_SCOPED_TOOLS", None)
    reset_active_scope()


def _default():
    return [_D("a"), _D("b")]


def test_flag_off_retorna_default():
    assert not _scoped_tools_enabled()
    assert [d.name for d in _resolve_scoped_tool_defs(_default)] == ["a", "b"]


def test_flag_on_sem_escopo_retorna_default():
    os.environ["LIA_FEDERATED_SCOPED_TOOLS"] = "true"
    reset_active_scope()
    assert [d.name for d in _resolve_scoped_tool_defs(_default)] == ["a", "b"]


def test_flag_on_com_escopo_retorna_scoped():
    os.environ["LIA_FEDERATED_SCOPED_TOOLS"] = "true"
    set_active_scope(PromptScope.TALENT_FUNNEL)
    scoped = _resolve_scoped_tool_defs(_default)
    names = {getattr(d, "name", None) for d in scoped}
    assert "a" not in names and "b" not in names, "deve ser scoped, nao o default"
    assert len(scoped) >= 1 and all(getattr(d, "name", None) for d in scoped)


def test_scope_guidance_injetavel_nao_vazia():
    """Fase 3: a guidance de escopo (capabilities+restrictions) que o federado injeta
    no prompt quando escopado existe e e nao-vazia p/ os escopos de dominio."""
    from app.tools.scope_config import PromptScope, get_scope_system_prompt_addition
    for sc in (PromptScope.TALENT_FUNNEL, PromptScope.JOB_TABLE, PromptScope.IN_JOB):
        add = get_scope_system_prompt_addition(sc)
        assert add and len(add) > 100, f"{sc.value} guidance vazia/curta"
        assert "PODE" in add, f"{sc.value} sem secao de capabilities/restrictions"
