"""Task #1051 — sentinelas anti-recorrência do wizard de criação de vaga.

4 contratos AST + comportamentais que travam regressão dos bugs:

    S1 — Auto-heal de demo user legado (B1)
        ``app.auth.dependencies._heal_legacy_demo_company_id`` existe E é
        chamado em AMBOS os caminhos de retorno de demo user existente
        (``ensure_demo_user`` e ``get_current_user_or_demo``). Sem isso, um
        user demo persistido com ``company_id="demo_company"`` antes do
        rollout do CANONICAL_DEMO_UUID quebra ``CompanyId.parse`` e a LIA
        volta a perguntar empresa no chat (T-E recorrência #4).

    S2 — Helper canônico de continuidade de sessão wizard (B2/B3/B4)
        ``WizardSessionService.is_session_active(session_id, company_id)``
        existe como método ``async`` e é fail-open (retorna False em
        exceção). Cobre TANTO o thread_id legado (`wiz-{session_id}`)
        QUANTO o tenant-prefixed (`wiz-{token}-{session_id}`) — paridade
        com ``derive_thread_id``.

    S3 — Pin de domínio antes do router no WS (B2/B3/B4)
        ``app/api/v1/agent_chat_ws.py`` invoca
        ``WizardSessionService.is_session_active`` ANTES do bloco
        ``if active_domain in ("auto", "recruiter_assistant", "")`` que
        roda o ``CascadedRouter``. Sem isso, o turno 2 do wizard
        ("Demo Company, 5 anos…") é reclassificado e perde checkpointer.

    S4 — Comportamental: sessão completed NÃO é pinada
        Stub do checkpointer com ``current_stage="completed"`` faz
        ``is_session_active`` devolver False — wizard finalizado libera
        o router para outras intenções.

Origem: 4 bugs simultâneos reportados pelo usuário em 2026-05-13:
    B1 = "LIA pergunta company_id"
    B2 = "esquece título da vaga entre turnos"
    B3 = "não consigo acessar histórico"
    B4 = "tool de salário re-pergunta empresa"
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Resolve repo root via this file's location — robust under pytest rootdir
# resolution and `python -m pytest` invocation styles.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEPENDENCIES = _REPO_ROOT / "app" / "auth" / "dependencies.py"
_WIZ_SVC = (
    _REPO_ROOT
    / "app"
    / "domains"
    / "job_creation"
    / "services"
    / "wizard_session_service.py"
)
_WS_HANDLER = _REPO_ROOT / "app" / "api" / "v1" / "agent_chat_ws.py"


def _parse(path: Path) -> ast.Module:
    assert path.exists(), f"Sentinela não encontrou arquivo canônico: {path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _functions(module: ast.Module) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
    return out


def _calls_named(node: ast.AST, name: str) -> bool:
    """True iff ``node`` (or any descendant) contains a call whose final
    attribute or function name matches ``name``."""
    for descendant in ast.walk(node):
        if not isinstance(descendant, ast.Call):
            continue
        func = descendant.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
        if isinstance(func, ast.Attribute) and func.attr == name:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# S1 — auto-heal de demo user legado (B1)
# ─────────────────────────────────────────────────────────────────────────────
def test_s1_heal_helper_exists_in_dependencies():
    funcs = _functions(_parse(_DEPENDENCIES))
    assert "_heal_legacy_demo_company_id" in funcs, (
        "S1 fail: ``_heal_legacy_demo_company_id`` ausente — sem auto-heal, "
        "user demo legado quebra CompanyId.parse e a LIA pergunta empresa."
    )


def test_s1_heal_called_in_ensure_demo_user_and_get_current_user_or_demo():
    funcs = _functions(_parse(_DEPENDENCIES))
    for fn_name in ("ensure_demo_user", "get_current_user_or_demo"):
        assert fn_name in funcs, f"S1 fail: função canônica {fn_name} sumiu"
        assert _calls_named(funcs[fn_name], "_heal_legacy_demo_company_id"), (
            f"S1 fail: {fn_name} retorna user demo legado SEM chamar "
            "_heal_legacy_demo_company_id — recorrência B1 (LIA pergunta company_id)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# S2 — helper canônico de continuidade
# ─────────────────────────────────────────────────────────────────────────────
def test_s2_is_session_active_exists_and_is_async():
    mod = _parse(_WIZ_SVC)
    classes = {n.name: n for n in mod.body if isinstance(n, ast.ClassDef)}
    assert "WizardSessionService" in classes, "S2 fail: classe canônica sumiu"
    methods = {
        n.name: n
        for n in classes["WizardSessionService"].body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "is_session_active" in methods, (
        "S2 fail: ``is_session_active`` ausente — sem ele, o WS não tem "
        "como pinar wizard antes do router (B2/B3/B4)."
    )
    assert isinstance(methods["is_session_active"], ast.AsyncFunctionDef), (
        "S2 fail: ``is_session_active`` precisa ser ``async`` (lê checkpointer)."
    )
    # Cobertura de fail-open — método precisa ter try/except interno.
    assert any(
        isinstance(n, ast.Try) for n in ast.walk(methods["is_session_active"])
    ), "S2 fail: ``is_session_active`` precisa ser fail-open (try/except)."


# ─────────────────────────────────────────────────────────────────────────────
# S3 — pin de domínio antes do router
# ─────────────────────────────────────────────────────────────────────────────
def test_s3_ws_pins_wizard_before_router():
    src = _WS_HANDLER.read_text(encoding="utf-8")
    pin_idx = src.find("is_session_active")
    router_idx = src.find('if active_domain in ("auto", "recruiter_assistant", ""):')
    # `find` returns the FIRST occurrence — `if active_domain in (...)` aparece
    # 2× (pin + router). Pegamos o segundo (router) explicitamente.
    second_router_idx = src.find(
        'if active_domain in ("auto", "recruiter_assistant", ""):',
        router_idx + 1,
    )
    assert pin_idx > 0, (
        "S3 fail: agent_chat_ws.py não chama ``is_session_active`` — "
        "sem pin de wizard, B2/B3/B4 voltam."
    )
    assert second_router_idx > 0, (
        "S3 fail: bloco do CascadedRouter ``if active_domain in (auto, "
        "recruiter_assistant, '')`` sumiu — pino órfão."
    )
    assert pin_idx < second_router_idx, (
        "S3 fail: pin de wizard precisa rodar ANTES do bloco do "
        "CascadedRouter — ordem invertida quebra B2/B3/B4."
    )


# ─────────────────────────────────────────────────────────────────────────────
# S4 — sessão completed não é pinada (comportamental, não AST)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_s4_completed_session_does_not_pin(monkeypatch):
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    async def fake_prior_completed(thread_id: str) -> dict:  # noqa: ARG001
        return {
            "current_stage": "completed",
            "conversation_messages": [{"role": "user", "content": "x"}],
        }

    monkeypatch.setattr(
        WizardSessionService, "_get_prior_state", staticmethod(fake_prior_completed)
    )
    active = await WizardSessionService.is_session_active(
        session_id="sess-xyz", company_id=None
    )
    assert active is False, (
        "S4 fail: wizard COMPLETED foi pinado como ativo — bloqueia "
        "outras intenções após a vaga ser publicada."
    )


@pytest.mark.asyncio
async def test_s4_open_session_does_pin(monkeypatch):
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    async def fake_prior_open(thread_id: str) -> dict:  # noqa: ARG001
        return {
            "current_stage": "intake",
            "conversation_messages": [
                {"role": "user", "content": "criar vaga de backend"},
            ],
        }

    monkeypatch.setattr(
        WizardSessionService, "_get_prior_state", staticmethod(fake_prior_open)
    )
    active = await WizardSessionService.is_session_active(
        session_id="sess-xyz", company_id=None
    )
    assert active is True, (
        "S4 fail: sessão wizard ABERTA (stage=intake, conversa não vazia) "
        "deveria ser pinada — sem isso B2/B3/B4 voltam."
    )


@pytest.mark.asyncio
async def test_s4_no_session_returns_false(monkeypatch):
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    async def fake_prior_empty(thread_id: str) -> dict:  # noqa: ARG001
        return {}

    monkeypatch.setattr(
        WizardSessionService, "_get_prior_state", staticmethod(fake_prior_empty)
    )
    active = await WizardSessionService.is_session_active(
        session_id="sess-novo", company_id=None
    )
    assert active is False, (
        "S4 fail: sem checkpoint algum, helper não pode pinar — false positive."
    )
