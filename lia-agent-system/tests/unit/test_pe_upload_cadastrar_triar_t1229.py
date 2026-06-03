"""
Task #1229 — Fluxo P&E "Upload, cadastrar e handoff de triagem (item 5)".

Sentinelas do caminho REAL (não delegate/fake) dos discrete handlers do
PlanExecutor para o pattern `upload_cadastrar_triar`:

  1. cv_screening.parse_and_create_candidate REUSA o primitivo canônico
     `cv_upload_tool.parse_and_create_candidate` tenant-scoped (_context com
     company_id do ActionContext) e emite candidate_id/candidate_name p/ chaining.
  2. parse_and_create_candidate sem cv_text → clarification honesta (não chama o
     primitivo).
  3. parse_and_create_candidate sem tenant → erro honesto.
  4. parse_and_create_candidate com falha do primitivo → erro honesto (nunca finge
     sucesso).
  5. cv_screening.add_to_vacancy REUSA o tool ENDURECIDO `add_candidate_to_vacancy`
     (valida e-mail + FairnessGuard C1 + cross_tenant + audit) tenant-scoped,
     stage "Triagem".
  6. add_to_vacancy sem candidato/vaga → clarification.
  7. add_to_vacancy com missing_email/invalid_email do tool → erro honesto
     (pré-condição respeitada, nunca fake success).
  8. add_to_vacancy com cross_tenant_access_denied → erro honesto.
  9. tenant vem do ActionContext (server-side), não de params (spoof ignorado).
 10. run_wsi_screening é interceptado pelo honest handoff guard (kind triagem_wsi,
     executed False) — NUNCA finge envio de triagem.
 11. plan_detector casa upload_cadastrar_triar (3 tasks) e NÃO contém step de
     criação de vaga (INVIOLÁVEL #1211); cobre frases naturais PT-BR.
 12. Chaining via PlanExecutor: candidate_id (task_0) chega ao add_to_vacancy;
     run_wsi NÃO executa → consolidated = agent_handoff (nunca fake success).
"""
import pytest
from unittest.mock import AsyncMock, patch


def _action_context(raw_query="analise este cv e cadastre na vaga", base_context=None,
                    company_id="co-1229"):
    from app.shared.execution.discrete_actions import ActionContext
    return ActionContext(
        company_id=company_id,
        user_id="user-1229",
        session_id="sess-1229",
        tenant_id=company_id,
        raw_query=raw_query,
        base_context=base_context or {},
    )


_CV_TEXT = (
    "Ana Souza\nEngenheira de Software Sênior\nana.souza@example.com\n"
    "Experiência: 8 anos em Python, FastAPI, PostgreSQL e arquitetura de microsserviços. "
    "Liderança técnica de squads ágeis. Formada em Ciência da Computação."
)


def _create_ok(cid="cand-1229", name="Ana Souza", duplicate=False):
    return {
        "success": True,
        "duplicate": duplicate,
        "candidate_id": cid,
        "candidate_name": name,
        "message": f"✅ Candidato **{name}** cadastrado com sucesso.",
        "parsed": {"name": name, "email": "ana.souza@example.com", "skills": ["Python"]},
    }


def _add_ok(cid="cand-1229", job="job-1229", stage="Triagem"):
    return {
        "success": True,
        "message": f"✅ Ana foi adicionada à vaga na etapa '{stage}'.",
        "action_taken": "add_candidate_to_vacancy",
        "affected_entities": [cid, job],
        "data": {
            "candidate_id": cid,
            "candidate_name": "Ana Souza",
            "job_id": job,
            "job_title": "Engenheira de Software",
            "stage": stage,
            "source": "cv_upload",
            "added_by": "user-1229",
        },
    }


# ---------------------------------------------------------------------------
# 1-4. cv_screening.parse_and_create_candidate
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_parse_and_create_reuses_primitive_tenant_scoped_and_emits_candidate_id():
    from app.shared.execution import discrete_actions as da

    prim = AsyncMock(return_value=_create_ok())
    with patch.object(da, "_parse_and_create_candidate_primitive", prim):
        handler = da.get_discrete_handler("cv_screening", "parse_and_create_candidate")
        assert handler is not None, "handler parse_and_create_candidate não registrado"
        resp = await handler({"cv_text": _CV_TEXT, "vacancy_id": "job-1229"}, _action_context())

    assert resp.success is True
    prim.assert_awaited_once()
    kwargs = prim.call_args.kwargs
    assert kwargs.get("cv_text") == _CV_TEXT
    # tenant injetado via _context (server-side), nunca de params do cliente
    ctx = kwargs.get("_context") or kwargs.get("context")
    assert ctx is not None and getattr(ctx, "company_id", None) == "co-1229"
    data = resp.data or {}
    assert data.get("candidate_id") == "cand-1229"
    assert data.get("candidate_name") == "Ana Souza"


@pytest.mark.asyncio
async def test_parse_and_create_without_cv_text_is_honest_clarification():
    from app.shared.execution import discrete_actions as da

    prim = AsyncMock()
    with patch.object(da, "_parse_and_create_candidate_primitive", prim):
        handler = da.get_discrete_handler("cv_screening", "parse_and_create_candidate")
        resp = await handler({}, _action_context(raw_query="cadastre o candidato"))

    prim.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
async def test_parse_and_create_without_tenant_is_honest_error():
    from app.shared.execution import discrete_actions as da

    prim = AsyncMock()
    with patch.object(da, "_parse_and_create_candidate_primitive", prim):
        handler = da.get_discrete_handler("cv_screening", "parse_and_create_candidate")
        resp = await handler(
            {"cv_text": _CV_TEXT},
            _action_context(company_id=None),
        )

    prim.assert_not_awaited()
    assert resp.success is False


@pytest.mark.asyncio
async def test_parse_and_create_primitive_failure_is_honest_error_no_fake():
    from app.shared.execution import discrete_actions as da

    prim = AsyncMock(return_value={"success": False, "error": "cv_text_too_short",
                                   "message": "Texto do CV muito curto."})
    with patch.object(da, "_parse_and_create_candidate_primitive", prim):
        handler = da.get_discrete_handler("cv_screening", "parse_and_create_candidate")
        resp = await handler({"cv_text": _CV_TEXT}, _action_context())

    prim.assert_awaited_once()
    assert resp.success is False


# ---------------------------------------------------------------------------
# 5-9. cv_screening.add_to_vacancy
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_add_to_vacancy_reuses_hardened_tool_tenant_scoped_stage_triagem():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock(return_value=_add_ok())
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_to_vacancy")
        assert handler is not None, "handler add_to_vacancy não registrado"
        resp = await handler(
            {"candidate_id": "cand-1229", "vacancy_id": "job-1229"},
            _action_context(),
        )

    assert resp.success is True
    add.assert_awaited_once()
    kwargs = add.call_args.kwargs
    assert kwargs.get("candidate_id") == "cand-1229"
    assert kwargs.get("job_id") == "job-1229"
    assert kwargs.get("initial_stage") == "Triagem"
    ctx = kwargs.get("_context") or kwargs.get("context")
    assert ctx is not None and getattr(ctx, "company_id", None) == "co-1229"


@pytest.mark.asyncio
async def test_add_to_vacancy_without_candidate_or_vacancy_is_clarification():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock()
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_to_vacancy")
        resp = await handler({}, _action_context())

    add.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
@pytest.mark.parametrize("error_code", ["missing_email", "invalid_email"])
async def test_add_to_vacancy_email_precondition_is_honest_error_no_fake(error_code):
    from app.shared.execution import discrete_actions as da

    add = AsyncMock(return_value={"success": False, "error": error_code,
                                  "message": "Candidato sem e-mail válido."})
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_to_vacancy")
        resp = await handler(
            {"candidate_id": "cand-1229", "vacancy_id": "job-1229"},
            _action_context(),
        )

    add.assert_awaited_once()
    assert resp.success is False  # nunca finge que adicionou


@pytest.mark.asyncio
async def test_add_to_vacancy_cross_tenant_is_honest_error():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock(return_value={"success": False, "error": "cross_tenant_access_denied",
                                  "message": "Acesso negado: vaga pertence a outra empresa"})
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_to_vacancy")
        resp = await handler(
            {"candidate_id": "cand-1229", "vacancy_id": "job-of-other-tenant"},
            _action_context(),
        )

    assert resp.success is False


@pytest.mark.asyncio
async def test_tenant_comes_from_context_not_params_spoof_ignored():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock(return_value=_add_ok())
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_to_vacancy")
        await handler(
            {"candidate_id": "cand-1229", "vacancy_id": "job-1229",
             "company_id": "attacker-co", "tenant_id": "attacker-co"},
            _action_context(company_id="co-1229"),
        )

    ctx = add.call_args.kwargs.get("_context") or add.call_args.kwargs.get("context")
    assert getattr(ctx, "company_id", None) == "co-1229"  # do JWT, não do params


# ---------------------------------------------------------------------------
# 10. run_wsi_screening — honest handoff (sem fake success)
# ---------------------------------------------------------------------------
def test_run_wsi_screening_is_intercepted_by_honest_handoff():
    from app.shared.execution.agent_handoff import build_handoff_response, HANDOFF_METADATA_KEY

    resp = build_handoff_response("cv_screening", "run_wsi_screening")
    assert resp is not None, "run_wsi_screening deveria ser interceptado como handoff"
    assert resp.success is False
    meta = (resp.metadata or {}).get(HANDOFF_METADATA_KEY) or {}
    assert meta.get("executed") is False
    assert meta.get("kind") == "triagem_wsi"


# ---------------------------------------------------------------------------
# 11. plan_detector pattern (sem step de criação — INVIOLÁVEL #1211)
# ---------------------------------------------------------------------------
def test_plan_detector_matches_upload_cadastrar_triar_without_creation_step():
    from app.shared.execution.plan_detector import PlanDetector

    phrases = [
        "analise este cv e cadastre na vaga",          # já casava
        "cadastre este candidato na vaga e triar",     # já casava
        "faça upload do cv e cadastre o candidato e triagem",   # novo imperativo
        "registrar o candidato e disparar triagem",             # novo imperativo
        "crie o candidato a partir do cv e faça a triagem",     # novo imperativo
        "suba o cv, cadastre o candidato e mande pra triagem",  # novo imperativo
    ]
    d = PlanDetector()
    for phrase in phrases:
        plan = d.detect(phrase)
        assert plan is not None, f"não casou: {phrase!r}"
        assert plan.detected_pattern == "upload_cadastrar_triar", phrase
        action_ids = [t.action_id for t in plan.tasks]
        assert action_ids == [
            "parse_and_create_candidate", "add_to_vacancy", "run_wsi_screening",
        ], phrase
        # INVIOLÁVEL #1211 — nenhum step de criação/publicação de VAGA
        # (criação de CANDIDATO é o objetivo do fluxo e é permitida)
        _JOB_CREATION = {"create_job", "create_vacancy", "criar_vaga",
                         "publish_job", "create_job_from_intake"}
        assert not (set(action_ids) & _JOB_CREATION), phrase
        assert not any("vaga" in a and ("cri" in a or "creat" in a) for a in action_ids), phrase


# ---------------------------------------------------------------------------
# 12. Chaining via PlanExecutor (candidate_id task_0 → add_to_vacancy;
#     run_wsi NÃO executa → consolidated = agent_handoff, nunca fake success)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_cadastrar_triar_chains_and_handoffs_via_executor():
    from app.shared.execution import discrete_actions as da
    from app.shared.execution.plan_detector import PlanDetector
    from app.shared.execution.plan_executor import PlanExecutor

    plan = PlanDetector().detect("analise este cv e cadastre na vaga")
    assert plan is not None and len(plan.tasks) == 3

    prim = AsyncMock(return_value=_create_ok())
    add = AsyncMock(return_value=_add_ok())

    with patch.object(da, "_parse_and_create_candidate_primitive", prim), \
         patch.object(da, "add_candidate_to_vacancy", add):
        executor = PlanExecutor()
        result = await executor.execute(
            plan,
            user_id="user-1229",
            session_id="sess-1229",
            tenant_id="co-1229",
            base_context={
                "company_id": "co-1229",
                "cv_text": _CV_TEXT,
                "vacancy_id": "job-1229",
            },
        )

    prim.assert_awaited_once()
    add.assert_awaited_once()
    # candidate_id emitido pelo task_0 chegou ao add_to_vacancy (chaining)
    assert add.call_args.kwargs.get("candidate_id") == "cand-1229"

    statuses = {t.action_id: t.status.value for t in result.tasks}
    assert statuses.get("parse_and_create_candidate") == "completed"
    assert statuses.get("add_to_vacancy") == "completed"
    # run_wsi NÃO executa — handoff honesto (nunca completed/fake success)
    assert statuses.get("run_wsi_screening") != "completed"

    consolidated = executor.build_consolidated_response(result)
    assert consolidated is not None
    assert getattr(consolidated, "success", True) is False
    assert (getattr(consolidated, "error", "") or "") == "agent_handoff"
