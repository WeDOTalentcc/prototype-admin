"""
Cobertura de fluxo intent-routed do job_creation (task #674).

O dominio job_creation NAO usa o padrao handler_map / _ACTION_TOOL_MAP — em
vez disso, faz roteamento por estagio do wizard via process_intent +
_route_by_stage e delega ao LangGraph (JobCreationGraph). Esses testes
cobrem 4 cenarios de transicao com a graph mockada para nao depender de
LLM ou banco.

Cenarios:
  1. Caminho feliz: start_wizard -> approve_jd -> set_salary ->
     set_screening_mode -> approve_questions -> set_eligibility ->
     configure_publish -> publish_job.
  2. Transicao invalida: tentar publicar antes de aprovar JD.
  3. Idempotencia: aprovar JD duas vezes seguidas.
  4. Recuperacao: wizard_status retorna o estagio correto apos retomada.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("LIA_ALLOW_NON_COMPLIANT_DOMAINS", "1")
os.environ.setdefault("LIA_SKIP_DB", "1")


def _force_import_all_domains() -> None:
    base = Path(__file__).resolve().parents[1] / "domains"
    for d in sorted(base.iterdir()):
        if not d.is_dir() or not (d / "domain.py").exists():
            continue
        try:
            importlib.import_module(f"app.domains.{d.name}.domain")
        except Exception:
            pass


_force_import_all_domains()


def _make_context(metadata: dict | None = None):
    from app.domains.base import DomainContext

    ctx = DomainContext(
        domain_id="job_creation",
        user_id="recruiter-1",
        session_id="thread-job-1",
        tenant_id="company-A",
        metadata=metadata or {},
    )
    setattr(ctx, "auth_token", "tok-test")
    setattr(ctx, "workspace_id", 1)
    setattr(ctx, "company_id", "company-A")
    return ctx


def _domain():
    from app.domains.registry import DomainRegistry

    return DomainRegistry().get_instance("job_creation")


def _stage_payload(stage: str, **extra):
    """Helper to build a fake graph result for a given stage."""
    base = {
        "current_stage": stage,
        "session_id": "thread-job-1",
        "completeness": 0.5,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": stage,
            "data": {},
            "completeness": 0.5,
            "requires_approval": stage in ("jd_enrichment", "wsi_questions"),
        },
    }
    base.update(extra)
    return base


@pytest.fixture
def mocked_graph():
    """Patch the JobCreationGraph singleton with a controllable MagicMock."""
    fake_graph = MagicMock()
    fake_graph.invoke = MagicMock(return_value=_stage_payload("jd_enrichment"))
    fake_graph.resume = MagicMock(return_value=_stage_payload("salary"))

    domain = _domain()
    assert domain is not None, "job_creation domain not registered"
    # Reset internal cached graph and inject the fake.
    domain._graph = fake_graph
    yield fake_graph
    domain._graph = None


# ---------------------------------------------------------------------------
# 1. Caminho feliz
# ---------------------------------------------------------------------------

@pytest.mark.medium
async def test_happy_path_full_wizard_flow(mocked_graph):
    """Sequencia completa start_wizard -> publish_job percorre cada estagio."""
    domain = _domain()
    ctx = _make_context()

    # Mapeamento (action -> proximo estagio que a graph mockada devolve)
    flow = [
        ("start_wizard", {"user_query": "Criar vaga de PM senior"}, "jd_enrichment"),
        ("approve_jd", {"approved": True}, "bigfive"),
        ("set_salary", {"salary_min": 15000, "salary_max": 20000}, "competency"),
        ("set_screening_mode", {"mode": "compact"}, "wsi_questions"),
        ("approve_questions", {"approved": True}, "eligibility"),
        ("set_eligibility", {"questions": [{"q": "Tem CNH?"}]}, "review"),
        ("configure_publish", {"platforms": ["linkedin"]}, "publish"),
        ("publish_job", {}, "calibration"),
    ]

    for action_id, params, next_stage in flow:
        if action_id == "start_wizard":
            mocked_graph.invoke.return_value = _stage_payload(next_stage)
        else:
            mocked_graph.resume.return_value = _stage_payload(next_stage)

        result = await _maybe_await(
            domain.execute_action(action_id, params, ctx)
        )
        assert result.success is True, f"{action_id} falhou: {result.error}"
        # Atualiza o contexto com o estado retornado para a proxima rodada
        ctx.metadata["wizard_state"] = result.data["wizard_state"]
        assert ctx.metadata["wizard_state"]["current_stage"] == next_stage


# ---------------------------------------------------------------------------
# 2. Transicao invalida — publicar antes de aprovar JD
# ---------------------------------------------------------------------------

@pytest.mark.medium
async def test_invalid_transition_publish_before_jd_approval(mocked_graph):
    """A graph mockada simula recusa explicita; a action deve sinalizar erro."""
    domain = _domain()
    ctx = _make_context(metadata={"wizard_state": _stage_payload("jd_enrichment")})

    # A graph nao avanca: retorna o mesmo estagio com erro embutido.
    mocked_graph.resume.return_value = {
        **_stage_payload("jd_enrichment"),
        "job_id": None,
        "error": "JD nao aprovado — nao e possivel publicar",
    }

    result = await _maybe_await(
        domain.execute_action("publish_job", {}, ctx)
    )

    # Contrato esperado para transicao invalida: o fluxo NAO pode terminar
    # com "publicacao bem sucedida". Aceitamos dois formatos (qualquer um
    # prova que a transicao foi bloqueada):
    #   (a) result.success is False — rejeicao explicita; ou
    #   (b) success=True mas (job_id is None) E uma mensagem de bloqueio
    #       (pendente / nao aprovad / nao e possivel / erro) e visivel.
    assert result.data is not None, "publish_job deve retornar algo em data"
    state = result.data.get("wizard_state", {}) or {}

    if result.success is False:
        # rejeicao explicita — ok
        return

    # success=True — entao exigimos que NADA tenha sido publicado e que a
    # mensagem sinalize o bloqueio claramente (nao sucesso silencioso).
    assert state.get("job_id") is None, (
        "Transicao invalida deveria bloquear publicacao, mas job_id foi gerado"
    )
    blocked_markers = ("pendente", "aprovad", "nao e possivel", "n\u00e3o e possivel", "erro", "bloque")
    blob = (
        (result.message or "")
        + " "
        + (result.error or "")
        + " "
        + str(state.get("error") or "")
    ).lower()
    assert any(m in blob for m in blocked_markers), (
        f"Transicao invalida sem sinal claro de bloqueio. "
        f"message={result.message!r} error={result.error!r} state_error={state.get('error')!r}"
    )


# ---------------------------------------------------------------------------
# 3. Idempotencia — aprovar JD duas vezes
# ---------------------------------------------------------------------------

@pytest.mark.medium
async def test_idempotent_jd_approval(mocked_graph):
    """Aprovar JD repetidamente nao deve quebrar nem mudar o resultado final."""
    domain = _domain()
    ctx = _make_context(metadata={"wizard_state": _stage_payload("jd_enrichment")})

    mocked_graph.resume.return_value = _stage_payload("bigfive")

    r1 = await _maybe_await(
        domain.execute_action("approve_jd", {"approved": True}, ctx)
    )
    ctx.metadata["wizard_state"] = r1.data["wizard_state"]

    r2 = await _maybe_await(
        domain.execute_action("approve_jd", {"approved": True}, ctx)
    )

    assert r1.success and r2.success
    assert (
        r1.data["wizard_state"]["current_stage"]
        == r2.data["wizard_state"]["current_stage"]
        == "bigfive"
    )
    # Cada chamada a approve_jd dispara um resume, mas o resultado e estavel.
    assert mocked_graph.resume.call_count == 2


# ---------------------------------------------------------------------------
# 4. Recuperacao de wizard interrompido — wizard_status reporta estagio certo
# ---------------------------------------------------------------------------

@pytest.mark.medium
async def test_wizard_status_recovers_interrupted_stage(mocked_graph):
    """Apos retomada, wizard_status reflete o estagio salvo no contexto."""
    domain = _domain()
    saved_state = _stage_payload("competency", completeness=0.55)
    ctx = _make_context(metadata={"wizard_state": saved_state})

    result = await _maybe_await(
        domain.execute_action("wizard_status", {}, ctx)
    )

    assert result.success is True
    assert result.data["current_stage"] == "competency"
    # wizard_status e puramente leitura — nao deve invocar a graph.
    mocked_graph.invoke.assert_not_called()
    mocked_graph.resume.assert_not_called()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _maybe_await(value):
    """JobCreationDomain.execute_action e definida como `def` (nao async),
    porem alguns handlers retornam corotinas. Aceitamos os dois formatos."""
    import inspect

    if inspect.isawaitable(value):
        return await value
    return value
