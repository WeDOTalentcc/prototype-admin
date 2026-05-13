"""Task #1051 — sentinelas anti-recorrência do wizard de criação de vaga.

Sentinelas AST + comportamentais que travam regressão dos 4 bugs:

    S1 — Auto-heal de demo user legado (B1)
        ``app.auth.dependencies._heal_legacy_demo_company_id`` existe E é
        chamado em AMBOS os caminhos de retorno de demo user existente
        (``ensure_demo_user`` e ``get_current_user_or_demo``). Sem isso, um
        user demo persistido com ``company_id="demo_company"`` antes do
        rollout do CANONICAL_DEMO_UUID quebra ``CompanyId.parse`` e a LIA
        volta a perguntar empresa no chat (T-E recorrência #4).

    S2 — Helper canônico de continuidade de sessão (B2/B3/B4)
        ``WizardSessionService.is_session_active(session_id, company_id)``
        existe como classmethod ``async`` e é fail-open. Cobre TANTO os
        thread_ids heurísticos (legacy + tenant-prefixed) QUANTO o
        ``thread_id`` custom (via Redis marker ``_read_session_thread``)
        — paridade com TODAS as 3 prioridades de ``derive_thread_id``.

    S3 — Pin de domínio na CAMADA CANÔNICA (router, não no WS)
        ``CascadedRouter.route`` invoca ``is_session_active`` e — quando
        retorna True — devolve ``RouteResult(domain_id="wizard",
        source="wizard_session_pin")`` curto-circuitando os tiers
        clássicos. Reviewer feedback v1: "domain pinning was implemented
        in the wrong layer". O pin precisa estar no router para cobrir
        TODOS os transports (WS, SSE, REST orchestrator,
        autonomous_react_agent) sem duplicação.

    S4 — Comportamental: open/completed/empty
        Stub do ``_get_prior_state`` cobre 3 cenários: stage=intake +
        msgs (ativa), stage=completed (libera router), state vazio
        (false negative). Adicionalmente, ``process_message`` mantém o
        marker Redis: persistido em turno aberto, deletado no completed.

Origem: 4 bugs simultâneos reportados em 2026-05-13:
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
_ROUTER = _REPO_ROOT / "app" / "orchestrator" / "cascaded_router.py"


def _parse(path: Path) -> ast.Module:
    assert path.exists(), f"Sentinela não encontrou arquivo canônico: {path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _functions(module: ast.Module) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
    return out


def _class_methods(module: ast.Module, class_name: str) -> dict[str, ast.AST]:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                m.name: m
                for m in node.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return {}


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
    methods = _class_methods(_parse(_WIZ_SVC), "WizardSessionService")
    assert methods, "S2 fail: classe canônica WizardSessionService sumiu"
    assert "is_session_active" in methods, (
        "S2 fail: ``is_session_active`` ausente — sem ele o router não tem "
        "como pinar wizard antes de classificar (B2/B3/B4)."
    )
    assert isinstance(methods["is_session_active"], ast.AsyncFunctionDef), (
        "S2 fail: ``is_session_active`` precisa ser ``async`` (lê checkpointer + Redis)."
    )
    # Cobertura de fail-open — método precisa ter try/except.
    assert any(
        isinstance(n, ast.Try) for n in ast.walk(methods["is_session_active"])
    ), "S2 fail: ``is_session_active`` precisa ser fail-open (try/except)."


def test_s2_is_session_active_covers_all_three_thread_id_strategies():
    """Reviewer v1: ``is_session_active`` ignorava ``msg["thread_id"]``
    custom (priority 1 de ``derive_thread_id``). Agora consulta TANTO o
    Redis marker (custom) QUANTO os candidate ids (heurísticos)."""
    methods = _class_methods(_parse(_WIZ_SVC), "WizardSessionService")
    fn = methods["is_session_active"]
    assert _calls_named(fn, "_read_session_thread"), (
        "S2 fail: ``is_session_active`` não consulta Redis marker — "
        "thread_ids custom (msg.thread_id) não serão detectados."
    )
    assert _calls_named(fn, "_candidate_thread_ids"), (
        "S2 fail: ``is_session_active`` precisa cobrir os candidates "
        "heurísticos (legacy + tenant-prefixed) como fallback."
    )
    # process_message precisa popular E limpar o marker.
    assert "process_message" in methods, "S2 fail: process_message sumiu"
    pm = methods["process_message"]
    assert _calls_named(pm, "_mark_session_thread"), (
        "S2 fail: process_message não persiste marker Redis — "
        "is_session_active não detectaria sessões com thread_id custom."
    )
    assert _calls_named(pm, "_clear_session_thread"), (
        "S2 fail: process_message não limpa marker no completed — "
        "router pinaria wizard infinitamente após publish."
    )


# ─────────────────────────────────────────────────────────────────────────────
# S3 — pin canônico DENTRO do CascadedRouter
# ─────────────────────────────────────────────────────────────────────────────
def test_s3_router_pins_wizard_via_is_session_active():
    """AST: ``CascadedRouter.route`` invoca ``is_session_active`` E retorna
    um RouteResult com ``domain_id="wizard"`` quando ativa."""
    methods = _class_methods(_parse(_ROUTER), "CascadedRouter")
    assert "route" in methods, "S3 fail: CascadedRouter.route sumiu"
    route_fn = methods["route"]
    assert isinstance(route_fn, ast.AsyncFunctionDef), (
        "S3 fail: CascadedRouter.route precisa ser ``async``."
    )
    assert _calls_named(route_fn, "is_session_active"), (
        "S3 fail: CascadedRouter.route NÃO invoca is_session_active — "
        "pin de wizard ausente da camada canônica. Reviewer v1: "
        "'domain pinning was implemented in the wrong layer'."
    )
    # Garantir que existe um RouteResult(domain_id="wizard", source=...) na função.
    found_pin_return = False
    for node in ast.walk(route_fn):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "RouteResult"):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        domain_v = kw.get("domain_id")
        source_v = kw.get("source")
        if (
            isinstance(domain_v, ast.Constant) and domain_v.value == "wizard"
            and isinstance(source_v, ast.Constant)
            and source_v.value == "wizard_session_pin"
        ):
            found_pin_return = True
            break
    assert found_pin_return, (
        "S3 fail: route() não devolve RouteResult(domain_id='wizard', "
        "source='wizard_session_pin') — pin não curto-circuita o router."
    )


def test_s3_ws_handler_does_not_duplicate_pin():
    """Defesa contra drift: o pin precisa estar APENAS no router, não no
    WS handler. Duplicação leva a (a) divergência de comportamento e (b)
    overhead duplo de checkpointer reads."""
    ws_path = _REPO_ROOT / "app" / "api" / "v1" / "agent_chat_ws.py"
    src = ws_path.read_text(encoding="utf-8")
    # O bloco "if active_domain in (...)" + chamada a is_session_active
    # caracteriza o pin antigo. Garantimos que NÃO co-existem.
    has_call = "is_session_active" in src
    assert not has_call, (
        "S3 fail: agent_chat_ws.py ainda chama ``is_session_active`` — pin "
        "duplicado. A lógica precisa ficar exclusivamente em CascadedRouter "
        "(reviewer v1, Task #1051)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# S4 — comportamental (com monkeypatch de checkpointer + Redis)
# ─────────────────────────────────────────────────────────────────────────────
async def _stub_no_redis(*args, **kwargs):
    return None


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
    monkeypatch.setattr(
        WizardSessionService, "_read_session_thread", classmethod(_stub_no_redis)
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
    monkeypatch.setattr(
        WizardSessionService, "_read_session_thread", classmethod(_stub_no_redis)
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
    monkeypatch.setattr(
        WizardSessionService, "_read_session_thread", classmethod(_stub_no_redis)
    )
    active = await WizardSessionService.is_session_active(
        session_id="sess-novo", company_id=None
    )
    assert active is False, (
        "S4 fail: sem checkpoint algum, helper não pode pinar — false positive."
    )


@pytest.mark.asyncio
async def test_s4_redis_marker_finds_custom_thread_id(monkeypatch):
    """Cenário do reviewer v1: FE iniciou wizard com ``msg.thread_id``
    custom; ``_candidate_thread_ids`` heurístico não consegue reproduzir
    esse formato, então quem detecta a sessão é o Redis marker."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    async def fake_marker(cls, session_id: str) -> str:  # noqa: ARG001
        return "custom-fe-thread-deadbeef"

    async def fake_prior(thread_id: str) -> dict:
        if thread_id == "custom-fe-thread-deadbeef":
            return {
                "current_stage": "wsi_questions",
                "conversation_messages": [{"role": "user", "content": "x"}],
            }
        return {}  # heurísticos não encontram nada

    monkeypatch.setattr(
        WizardSessionService, "_read_session_thread", classmethod(fake_marker)
    )
    monkeypatch.setattr(
        WizardSessionService, "_get_prior_state", staticmethod(fake_prior)
    )
    active = await WizardSessionService.is_session_active(
        session_id="sess-fe-custom", company_id=None
    )
    assert active is True, (
        "S4 fail: Redis marker apontando para thread_id custom não foi "
        "consultado — sessões iniciadas com msg.thread_id custom seriam "
        "perdidas (reviewer v1)."
    )
