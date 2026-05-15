"""Sentinela offline — Task #1084 / T1.

Garante que o contrato canônico ``WizardGateService.resume_gate(...)`` é o
único entry point legítimo de resume HITL do wizard a partir de transports
(WS hoje, REST/SSE/chat-classifier no futuro). Cobre:

  S1. ``derive_gate_id`` é determinístico e usa AMBOS thread_id + pending_id
      (proteção contra colisão entre threads).
  S2. Idempotência via CAS: chamar ``resume_gate`` 2× com o mesmo gate_id
      executa o resume e o audit emit **uma** única vez.
  S3. Rejeição também é cacheada (CAS) e gera audit row de ``rejected``.
  S4. AST-level: ``app/api/v1/agent_chat_ws.py`` NÃO importa ``JobWizardGraph``
      diretamente — todo resume do wizard passa por ``wizard_gate_service``.
  S5. Timeout no engine NÃO escreve CAS (permite retry pelo usuário) e NÃO
      emite audit row.
  S6. **Idempotência sob concorrência real**: duas chamadas ``resume_gate``
      executando em paralelo (``asyncio.gather``) com o mesmo gate_id
      executam o engine **uma** única vez e emitem audit row **uma** única
      vez — invariante crítico de CAS atômico (acquire-or-wait).
  S7. **Anti-tampering de gate_id**: passar um ``gate_id`` divergente do
      derivado canônico (``derive_gate_id(thread_id, pending_id)``) DEVE
      levantar ``ValueError`` antes de tocar engine/audit/CAS — protege o
      contrato canônico contra cliente malicioso/buggy forçando colisão de
      chave de idempotência.

Estes testes rodam offline (sem Redis, sem DB, sem backend up): o
``wizard_gate_service`` faz fail-open para ``self._memory_cas`` quando o
Redis não está disponível, e o ``audit_service`` é mockado.
"""
from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.job_creation.services.wizard_gate_service import (
    WizardGateService,
    wizard_gate_service,
)


# ----------------------------------------------------------------------
# S1 — derive_gate_id determinístico
# ----------------------------------------------------------------------


def test_s1_derive_gate_id_is_deterministic_and_includes_both_inputs():
    """O gate_id deve ser estável para o mesmo (thread, pending) E mudar
    se qualquer um dos dois mudar — protege contra colisão entre threads
    que (em teoria) reusem o mesmo pending UUID."""
    g1 = WizardGateService.derive_gate_id("wiz-aaaa-sess1", "pid-XYZ")
    g2 = WizardGateService.derive_gate_id("wiz-aaaa-sess1", "pid-XYZ")
    g3 = WizardGateService.derive_gate_id("wiz-bbbb-sess2", "pid-XYZ")
    g4 = WizardGateService.derive_gate_id("wiz-aaaa-sess1", "pid-OTHER")

    assert g1 == g2, "mesmo input → mesmo gate_id (determinismo)"
    assert g1 != g3, "thread_id diferente → gate_id diferente"
    assert g1 != g4, "pending_id diferente → gate_id diferente"
    assert "wiz-aaaa-sess1" in g1 and "pid-XYZ" in g1, (
        "gate_id deve carregar evidência dos inputs (debuggability)"
    )


def test_s1_derive_gate_id_empty_pending_returns_empty():
    """Sem pending_id não há gate — string vazia sinaliza 'não cacheável'."""
    assert WizardGateService.derive_gate_id("wiz-x-y", "") == ""


# ----------------------------------------------------------------------
# S2 — idempotência (CAS): aprovar 2× = 1 audit, 1 resume
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_s2_resume_gate_idempotent_via_cas_on_approval():
    """Chamar resume_gate(approved) 2× com o mesmo gate_id deve:
      - executar o engine de resume **uma** única vez,
      - emitir audit row **uma** única vez,
      - retornar ``cached=True`` na 2ª chamada com a mesma message.
    """
    svc = WizardGateService()  # instância fresca → CAS in-memory limpo

    fake_engine = AsyncMock(return_value="Vaga aprovada e criada.")
    fake_audit = AsyncMock()

    with patch.object(svc, "_resume_engine", fake_engine), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        first = await svc.resume_gate(
            thread_id="wiz-t1-s1",
            pending_id="pid-1",
            decision="approved",
            ws_session_id="s1",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-1",
        )
        second = await svc.resume_gate(
            thread_id="wiz-t1-s1",
            pending_id="pid-1",
            decision="approved",
            ws_session_id="s1",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-1",
        )

    assert first["status"] == "ok"
    assert first["cached"] is False
    assert second["cached"] is True, "2ª chamada com mesmo gate_id deve ser cacheada"
    assert first["message"] == second["message"], "mensagem deve ser estável entre chamadas idempotentes"
    assert first["gate_id"] == second["gate_id"]

    assert fake_engine.await_count == 1, (
        "engine de resume DEVE rodar 1× — 2× quebra Inegociável de idempotência "
        "e abre race condition entre botão+chat (Task #1084)"
    )
    assert fake_audit.await_count == 1, (
        "audit row DEVE ser emitido 1× — 2× viola SOX/EU AI Act "
        "(audit duplicado para o mesmo gate)"
    )


# ----------------------------------------------------------------------
# S3 — rejeição também é cacheada e auditada
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_s3_resume_gate_rejection_is_cached_and_audited():
    svc = WizardGateService()
    fake_engine = AsyncMock()
    fake_audit = AsyncMock()

    with patch.object(svc, "_resume_engine", fake_engine), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        first = await svc.resume_gate(
            thread_id="wiz-rej-s2",
            pending_id="pid-rej",
            decision="rejected",
            ws_session_id="s2",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-2",
            comment="não está adequada",
        )
        second = await svc.resume_gate(
            thread_id="wiz-rej-s2",
            pending_id="pid-rej",
            decision="rejected",
            ws_session_id="s2",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-2",
        )

    assert first["status"] == "rejected"
    assert "Ação cancelada" in first["message"]
    assert second["cached"] is True
    assert fake_engine.await_count == 0, "rejeição NÃO retoma engine"
    assert fake_audit.await_count == 1, "rejeição emite audit row 1× (não 2×)"


# ----------------------------------------------------------------------
# S4 — AST: agent_chat_ws.py NÃO importa JobWizardGraph diretamente
# ----------------------------------------------------------------------


def _imports_in_file(path: Path) -> set[str]:
    """Coleta todos os símbolos importados (nome final usado no escopo).

    Cobre tanto ``import x.y`` (-> 'x.y') quanto ``from a.b import C`` (-> 'C').
    Inclui imports inline dentro de funções (LangGraph compile etc).
    """
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                names.add(alias.asname or alias.name)
                # fully-qualified também — pega caso de ``from x import JobWizardGraph``
                names.add(f"{mod}.{alias.name}")
    return names


def test_s4_agent_chat_ws_does_not_import_job_wizard_graph_directly():
    """Após Task #1084, todo resume do wizard via WS DEVE passar por
    ``wizard_gate_service``. Importar ``JobWizardGraph`` em ``agent_chat_ws.py``
    é regressão — quebra o contrato canônico único e abre o caminho para
    audit duplicado / race condition entre chat+botão (T2)."""
    repo_root = Path(__file__).resolve().parents[3]
    ws_file = repo_root / "app" / "api" / "v1" / "agent_chat_ws.py"
    assert ws_file.exists(), f"esperava encontrar {ws_file}"

    imports = _imports_in_file(ws_file)
    forbidden = {
        "JobWizardGraph",
        "app.domains.job_management.agents.job_wizard_graph.JobWizardGraph",
    }
    leaked = imports & forbidden
    assert not leaked, (
        f"agent_chat_ws.py importa {leaked} diretamente — proibido pela "
        "Task #1084. Use wizard_gate_service.resume_gate(...) em vez disso."
    )


def test_s4_agent_chat_ws_imports_wizard_gate_service():
    """Espelho positivo de S4: o handler WS DEVE importar wizard_gate_service
    (caso contrário o resume do wizard regrediu para o bloco inline)."""
    repo_root = Path(__file__).resolve().parents[3]
    ws_file = repo_root / "app" / "api" / "v1" / "agent_chat_ws.py"
    src = ws_file.read_text(encoding="utf-8")
    assert "wizard_gate_service" in src, (
        "agent_chat_ws.py DEVE referenciar wizard_gate_service no handler "
        "approval_response (Task #1084)."
    )
    assert "resume_gate" in src, (
        "agent_chat_ws.py DEVE chamar resume_gate(...) — entry point canônico."
    )


# ----------------------------------------------------------------------
# S5 — timeout NÃO escreve CAS (permite retry) e NÃO emite audit
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_s5_resume_gate_timeout_does_not_persist_cas_or_audit():
    """Em timeout do engine, o gate NÃO deve ser cacheado — o usuário
    precisa poder tentar de novo. Audit também NÃO é emitido (não houve
    decisão concluída para auditar)."""
    svc = WizardGateService()

    async def _slow_engine(*_a, **_kw):
        raise asyncio.TimeoutError()

    fake_audit = AsyncMock()
    with patch.object(svc, "_resume_engine", side_effect=_slow_engine), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        first = await svc.resume_gate(
            thread_id="wiz-to-s3",
            pending_id="pid-to",
            decision="approved",
            ws_session_id="s3",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-3",
        )

    assert first["status"] == "timeout"
    assert first["cached"] is False
    assert fake_audit.await_count == 0, "timeout NÃO emite audit row"

    # E uma 2ª tentativa NÃO deve ver cached=True
    fake_engine_ok = AsyncMock(return_value="Vaga criada após retry.")
    with patch.object(svc, "_resume_engine", fake_engine_ok), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        second = await svc.resume_gate(
            thread_id="wiz-to-s3",
            pending_id="pid-to",
            decision="approved",
            ws_session_id="s3",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-3",
        )

    assert second["status"] == "ok", "retry após timeout deve poder rodar"
    assert second["cached"] is False, "timeout anterior NÃO deve ter cacheado o gate"
    assert fake_engine_ok.await_count == 1


# ----------------------------------------------------------------------
# Singleton sanity
# ----------------------------------------------------------------------


def test_resume_engine_uses_job_creation_graph_not_legacy_wizard():
    """Sentinela Task #1085 / T2: ``WizardGateService._resume_engine`` DEVE
    delegar para ``JobCreationGraph.aresume_with_message`` (motor canônico
    baseado em ``langgraph.types.interrupt()``) e NÃO mais para o legacy
    ``JobWizardGraph.ainvoke(None)``.

    O motor legacy perdia a resposta do recrutador entre turnos, fazendo
    o wizard repetir a mesma pergunta em loop ("preciso da sua aprovação"
    4× ignorando "manda bala"/"tá liberado"). O motor canônico pausa em
    ``interrupt()`` e retoma via ``Command(resume=<msg>)`` exatamente no
    ponto da pergunta, com a resposta como input estruturado.
    """
    import ast
    import inspect
    import textwrap

    from app.domains.job_creation.services.wizard_gate_service import (
        WizardGateService,
    )

    raw_src = textwrap.dedent(inspect.getsource(WizardGateService._resume_engine))
    # Strip the docstring before checking — historical references to legacy
    # patterns ("JobWizardGraph", "ainvoke(None)") são esperadas no docstring
    # como parte da explicação do "porquê" da migração e não constituem
    # regressão. Só importa o código executável.
    tree = ast.parse(raw_src)
    fn = tree.body[0]
    if (
        fn.body
        and isinstance(fn.body[0], ast.Expr)
        and isinstance(fn.body[0].value, ast.Constant)
        and isinstance(fn.body[0].value.value, str)
    ):
        fn.body = fn.body[1:]
    src = ast.unparse(fn)

    assert "JobCreationGraph" in src, (
        "_resume_engine DEVE referenciar JobCreationGraph (Task #1085 / T2). "
        "Encontrado source sem essa classe — provavelmente regrediu para "
        "o motor legacy JobWizardGraph."
    )
    assert "aresume_with_message" in src, (
        "_resume_engine DEVE chamar aresume_with_message (resume canônico "
        "via langgraph.types.interrupt() + Command(resume=...))."
    )
    forbidden_usages = [
        "import JobWizardGraph",
        "JobWizardGraph()",
        "JobWizardGraph(",
    ]
    leaked = [pat for pat in forbidden_usages if pat in src]
    assert not leaked, (
        f"_resume_engine NÃO pode mais importar/instanciar JobWizardGraph "
        f"(legacy DEPRECATED). Use JobCreationGraph como motor único. "
        f"Padrões proibidos encontrados: {leaked}"
    )
    assert "ainvoke(None" not in src.replace(" ", ""), (
        "_resume_engine NÃO pode mais usar ainvoke(None) — esse padrão "
        "perde a resposta do recrutador entre turnos. Use "
        "aresume_with_message para entregar a decisão ao interrupt() pausado."
    )


@pytest.mark.asyncio
async def test_resume_engine_forwards_comment_as_resume_message():
    """Quando o aprovador deixa um comentário livre na decisão, o
    ``_resume_engine`` DEVE entregá-lo como ``resume_message`` para o
    ``interrupt()`` pausado — sem isso, o nó do wizard recebe sempre
    o mesmo placeholder ``"approved"`` e perde o conteúdo da decisão
    (regressão do bug original)."""
    svc = WizardGateService()
    fake_engine = AsyncMock(return_value="ok")
    fake_audit = AsyncMock()

    with patch.object(svc, "_resume_engine", fake_engine), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        await svc.resume_gate(
            thread_id="wiz-fwd-comment",
            pending_id="pid-fwd",
            decision="approved",
            ws_session_id="sf",
            company_id="00000000-0000-4000-a000-000000000001",
            user_id="user-fwd",
            comment="aprovo, mas troca o título para Engenheiro Backend Pleno",
        )

    assert fake_engine.await_count == 1
    kwargs = fake_engine.await_args.kwargs
    assert kwargs.get("resume_message") == (
        "aprovo, mas troca o título para Engenheiro Backend Pleno"
    ), (
        "comentário do aprovador DEVE ser propagado como resume_message — "
        "default 'approved' só vale quando comment está vazio."
    )


def test_wizard_gate_service_singleton_exposed():
    """O módulo deve expor ``wizard_gate_service`` como singleton — é o
    contrato pelo qual handlers de transport devem importar a service."""
    from app.domains.job_creation.services import wizard_gate_service as mod
    assert hasattr(mod, "wizard_gate_service")
    assert isinstance(mod.wizard_gate_service, WizardGateService)


# ----------------------------------------------------------------------
# S6 — concorrência real: asyncio.gather com mesmo gate_id
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_s6_concurrent_resume_gate_calls_run_engine_and_audit_once():
    """Duas chamadas paralelas com o mesmo gate_id (= duplo-clique no botão,
    ou botão + chat aprovando ao mesmo tempo) devem:
      - executar o engine **uma** única vez (CAS atômico),
      - emitir audit row **uma** única vez,
      - retornar o MESMO message para ambas as chamadas (uma `cached=False`,
        a outra `cached=True`).
    Sem isso, recrutadores que clicam 2× no botão geram 2 vagas e 2 audit
    rows duplicados — viola SOX/EU AI Act e a Inegociável de idempotência.
    """
    svc = WizardGateService()

    engine_calls = 0
    engine_started = asyncio.Event()
    engine_release = asyncio.Event()

    async def _slow_engine(*_a, **_kw):
        nonlocal engine_calls
        engine_calls += 1
        engine_started.set()
        # Mantém o engine "ocupado" para garantir que a 2ª chamada
        # entre em CAS enquanto a 1ª ainda está executando.
        await engine_release.wait()
        return "Vaga aprovada (concurrent)."

    fake_audit = AsyncMock()

    with patch.object(svc, "_resume_engine", side_effect=_slow_engine), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        # Dispara a 1ª task; aguarda ela ENTRAR no engine para garantir
        # que ela já adquiriu o lease (won) antes da 2ª iniciar.
        task1 = asyncio.create_task(svc.resume_gate(
            thread_id="wiz-conc-s6", pending_id="pid-conc",
            decision="approved", ws_session_id="s6",
            company_id="00000000-0000-4000-a000-000000000001", user_id="user-6",
        ))
        await engine_started.wait()
        # 2ª chamada — deve ver o lease in_progress e aguardar via polling.
        task2 = asyncio.create_task(svc.resume_gate(
            thread_id="wiz-conc-s6", pending_id="pid-conc",
            decision="approved", ws_session_id="s6",
            company_id="00000000-0000-4000-a000-000000000001", user_id="user-6",
        ))
        # Pequena pausa para a 2ª task entrar no estado de "wait".
        await asyncio.sleep(0.1)
        # Libera o engine; a 1ª finaliza, a 2ª lê o final via peek.
        engine_release.set()
        results = await asyncio.gather(task1, task2)

    assert engine_calls == 1, (
        f"engine rodou {engine_calls}× sob concorrência — esperado 1× "
        f"(invariante CAS atômico, Task #1084 review fix)"
    )
    assert fake_audit.await_count == 1, (
        f"audit emitido {fake_audit.await_count}× — esperado 1× "
        "(SOX/EU AI Act exige 1 audit row por gate resolvido)"
    )
    # Exatamente uma das duas chamadas retorna cached=True (a perdedora
    # da corrida); ambas retornam a mesma message final.
    cached_flags = sorted(r["cached"] for r in results)
    assert cached_flags == [False, True], (
        f"esperado [False, True] (1 vencedora, 1 perdedora), recebido {cached_flags}"
    )
    assert results[0]["message"] == results[1]["message"]
    assert results[0]["gate_id"] == results[1]["gate_id"]


# ----------------------------------------------------------------------
# S7 — anti-tampering: gate_id divergente é rejeitado fail-loud
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_s7_resume_gate_rejects_mismatched_gate_id_from_caller():
    """Passar ``gate_id`` divergente do canônico ``derive_gate_id(thread,
    pending)`` DEVE levantar ``ValueError`` ANTES de tocar engine/audit/CAS.

    Sem essa validação, um cliente WS malicioso poderia:
      - injetar um gate_id já 'usado' para forçar resposta cached fake;
      - injetar um gate_id único por chamada para suprimir idempotência
        (re-executar engine + audit row múltiplas vezes para a mesma
        decisão de gate).
    """
    svc = WizardGateService()
    fake_engine = AsyncMock()
    fake_audit = AsyncMock()

    with patch.object(svc, "_resume_engine", fake_engine), \
         patch.object(svc, "_emit_gate_audit", fake_audit):
        with pytest.raises(ValueError, match="gate_id mismatch"):
            await svc.resume_gate(
                thread_id="wiz-tamp-s7",
                pending_id="pid-real",
                decision="approved",
                ws_session_id="s7",
                company_id="00000000-0000-4000-a000-000000000001",
                user_id="user-7",
                gate_id="gate:wiz-OTHER:pid-FORGED",  # divergente
            )

    assert fake_engine.await_count == 0, "tampering NÃO deve executar engine"
    assert fake_audit.await_count == 0, "tampering NÃO deve emitir audit row"


def test_s7_ws_handler_does_not_pass_gate_id_from_client():
    """AST guard: o handler WS NÃO DEVE repassar ``gate_id`` vindo do
    cliente para ``resume_gate(...)``. A derivação canônica via
    (thread_id, pending_id) é a única fonte de verdade.

    Procura especificamente pelo padrão ``msg.get("gate_id")`` ou
    ``msg["gate_id"]`` no arquivo do handler — qualquer um deles é
    sinal de regressão para o anti-pattern de aceitar gate_id do cliente.
    """
    repo_root = Path(__file__).resolve().parents[3]
    ws_file = repo_root / "app" / "api" / "v1" / "agent_chat_ws.py"
    src = ws_file.read_text(encoding="utf-8")

    # Guard sobre o trecho substring; a checagem precisa ser robusta
    # a refactor de variáveis (ex.: `_ws_gate_id = msg.get("gate_id")`).
    forbidden_patterns = [
        'msg.get("gate_id")',
        "msg.get('gate_id')",
        'msg["gate_id"]',
        "msg['gate_id']",
    ]
    leaked = [p for p in forbidden_patterns if p in src]
    assert not leaked, (
        f"agent_chat_ws.py lê gate_id do cliente via {leaked} — proibido "
        "pela Task #1084 (review fix anti-tampering). A derivação canônica "
        "via (thread_id, pending_id) é a única fonte de verdade."
    )


# ----------------------------------------------------------------------
# S8 — WS handler roteia REJEIÇÃO do wizard pelo service (não pelo
#      branch genérico legacy `elif not ws_approved`)
# ----------------------------------------------------------------------


def test_s8_ws_handler_routes_wizard_rejection_through_service():
    """Issue #1 do 2º re-review: a branch legacy ``elif not ws_approved``
    no handler (genérica para qualquer domínio HITL) NÃO pode ser o caminho
    do wizard rejeitado — caso contrário o "entry point único" não existe
    de fato (audit row sai por outro caminho, sem CAS, sem idempotência).

    Guard estrutural: o handler DEVE ter uma branch ``resume_domain == "wizard"``
    que cobre AMBOS approved/rejected via ``wizard_gate_service.resume_gate``,
    e ela DEVE aparecer no source ANTES da branch genérica ``elif not ws_approved``.
    """
    repo_root = Path(__file__).resolve().parents[3]
    ws_file = repo_root / "app" / "api" / "v1" / "agent_chat_ws.py"
    src = ws_file.read_text(encoding="utf-8")

    wizard_branch_idx = src.find('resume_domain == "wizard"')
    legacy_reject_idx = src.find("elif not ws_approved")
    resume_gate_idx = src.find("wizard_gate_service.resume_gate(")

    assert wizard_branch_idx != -1, (
        "Esperado branch `resume_domain == \"wizard\"` no handler WS — "
        "rejeição do wizard precisa rotear pelo service canônico."
    )
    assert resume_gate_idx != -1, (
        "Esperada chamada `wizard_gate_service.resume_gate(...)` no handler WS."
    )
    assert legacy_reject_idx != -1, (
        "Branch genérica `elif not ws_approved` deve continuar existindo "
        "para outros domínios HITL (cv_screening etc) — só não pode capturar wizard."
    )
    assert wizard_branch_idx < legacy_reject_idx, (
        "Branch wizard DEVE vir ANTES de `elif not ws_approved`, senão a "
        "rejeição do wizard cai no caminho legacy e o service nunca é chamado."
    )
    # E o resume_gate precisa estar dentro da branch wizard (entre os dois marcos)
    assert wizard_branch_idx < resume_gate_idx < legacy_reject_idx, (
        "wizard_gate_service.resume_gate(...) DEVE estar dentro da branch "
        "`resume_domain == \"wizard\"` — não em outro contexto."
    )


# ----------------------------------------------------------------------
# S9 — CAS lease token-aware: worker stale NÃO sobrescreve resultado
#      do worker que adquiriu o lease atual.
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_s9_cas_finalize_with_stale_token_is_noop_against_redis():
    """Issue #2 do 2º re-review: se worker A pega lease, lease expira
    enquanto A ainda processa, e worker B adquire lease novo e finaliza,
    quando A tentar finalizar com token antigo o write DEVE ser no-op
    (caso contrário A sobrescreve o resultado de B — perda de write
    cross-worker).

    Validação contra Redis fake: setamos a key com token_B, chamamos
    `_cas_finalize(..., token=token_A)` e verificamos que a key continua
    com o valor de B (Lua só escreve se GET == ARGV[1]).
    """
    svc = WizardGateService()
    gid = "gate:wiz-stale:pid-stale"
    key = f"wizard:gate:resolved:{gid}"

    class _FakeRedis:
        def __init__(self):
            self.store: dict[str, str] = {}

        def eval(self, script, numkeys, *args):
            # Reproduz a semântica dos dois Lua scripts de produção em Python
            k = args[0]
            expected = args[1]
            current = self.store.get(k)
            if current != expected:
                return 0
            if "DEL" in script:
                self.store.pop(k, None)
                return 1
            # finalize: SET key newval EX ttl
            self.store[k] = args[2]
            return 1

        def setex(self, k, ttl, v):
            self.store[k] = v

        def set(self, *_a, **_kw):
            return True

        def get(self, k):
            return self.store.get(k)

        def delete(self, k):
            self.store.pop(k, None)

    fake = _FakeRedis()
    # Estado inicial: worker B já publicou seu resultado (sem token, simula
    # cached final por outro processo).
    fake.store[key] = json.dumps({"status": "ok", "message": "do worker B", "gate_id": gid})

    with patch("app.domains.job_creation.services.wizard_gate_service._get_redis",
               return_value=fake):
        # Worker A tenta finalizar com token velho — DEVE ser no-op
        applied = svc._cas_finalize(
            gid,
            {"status": "ok", "message": "stale write de A", "gate_id": gid},
            token="in_progress:TOKEN_A_VELHO",
        )
        assert applied is False, (
            "finalize com token stale DEVE ser no-op — Lua compare-and-set falhou"
        )
        # E o valor publicado por B continua intacto
        assert "do worker B" in fake.store[key]

        # Worker A também não pode derrubar o lease de B
        released = svc._cas_release_failed(gid, token="in_progress:TOKEN_A_VELHO")
        assert released is False
        assert key in fake.store, "release com token stale NÃO pode apagar a key"
