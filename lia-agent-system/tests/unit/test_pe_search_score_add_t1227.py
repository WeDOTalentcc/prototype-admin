"""
Task #1227 — Fluxo P&E "Buscar, pontuar e adicionar (item 1)".

Sentinelas do caminho REAL (não delegate/fake) dos discrete handlers do
PlanExecutor para o pattern `buscar_pontuar_e_adicionar`:

  1. sourcing.search_candidates REUSA `PearchService.search_by_job_description`
     tenant-scoped (company_id repassado). Emite `candidates` (p/ o score) E
     `candidate_ids` (compat com os patterns buscar_e_comparar/buscar_e_triar).
  2. search sem vaga E sem termo → clarification honesta (não chama Pearch).
  3. search sem resultados → vazio honesto (success, candidates=[], SEM fake).
  4. cv_screening.score_candidates chama `score_candidate_standalone` por
     candidato, ranqueia por `rubric_score` desc e marca aprovados reusando a
     classificação do serviço (`sub_status == "cv_approved"`), sem reimplementar
     threshold.
  5. score sem candidatos → erro honesto (não chama o scoring).
  6. cv_screening.add_approved_to_vacancy REUSA `add_candidate_to_vacancy` só
     para os aprovados, com `_context` tenant-scoped (company_id do actx).
  7. add reporta falhas honestamente (NUNCA finge sucesso).
  8. add sem ids → clarification honesta (não chama add_candidate_to_vacancy).
  9. Chaining search→score via PlanExecutor injeta `candidates` e produz
     `approved_candidate_ids`.
 10. plan_detector casa o pattern com 2 tasks e NÃO contém step de criação de
     vaga (INVIOLÁVEL #1211).
"""
import types

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _action_context(raw_query="busque candidatos e pontue", base_context=None):
    from app.shared.execution.discrete_actions import ActionContext
    return ActionContext(
        company_id="co-1227",
        user_id="user-1227",
        session_id="sess-1227",
        tenant_id="co-1227",
        raw_query=raw_query,
        base_context=base_context or {},
    )


def _profile(docid, name, skills=None, match_score=80.0, score=3):
    """Perfil estilo CandidateProfile (acesso por atributo)."""
    return types.SimpleNamespace(
        docid=docid,
        name=name,
        first_name=name.split()[0] if name else None,
        last_name=name.split()[-1] if name and " " in name else None,
        title="Engenheiro",
        current_title="Engenheiro",
        skills=skills or ["python"],
        experiences=[],
        education=[],
        total_experience_years=5.0,
        summary="resumo",
        emails=[f"{docid}@x.com"],
        best_personal_email=f"{docid}@x.com",
        best_business_email=None,
        location="Remoto",
        match_score=match_score,
        score=score,
        is_discovered=False,
    )


def _pearch_response(profiles):
    resp = MagicMock()
    resp.get_candidates = MagicMock(return_value=list(profiles))
    resp.search_results = []
    resp.candidates = list(profiles)
    return resp


# ---------------------------------------------------------------------------
# 1-3. sourcing.search_candidates
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_search_reuses_pearch_tenant_scoped_and_emits_ids():
    from app.shared.execution import discrete_actions as da

    search = AsyncMock(return_value=_pearch_response([
        _profile("11111111-1111-4111-8111-111111111111", "Ana Souza"),
        _profile("22222222-2222-4222-8222-222222222222", "Bruno Lima"),
    ]))
    jd = AsyncMock(return_value={
        "title": "Backend Sr", "description": "Python e FastAPI", "location": "Remoto",
    })

    with patch.object(da, "PearchService") as PS, \
         patch.object(da, "_get_vacancy_jd", jd):
        PS.return_value.search_by_job_description = search

        handler = da.get_discrete_handler("sourcing", "search_candidates")
        assert handler is not None, "handler de search_candidates não registrado"

        resp = await handler(
            {"vacancy_id": "job-1"},
            _action_context(),
        )

    assert resp.success is True
    search.assert_awaited_once()
    # tenant-scoped: company_id repassado ao serviço canônico
    s_kwargs = search.call_args.kwargs
    assert s_kwargs.get("company_id") == "co-1227"
    # emite candidatos (p/ score) E candidate_ids (compat chain comparar/triar)
    assert isinstance(resp.data, dict)
    assert len(resp.data.get("candidates") or []) == 2
    assert resp.data.get("candidate_ids") == [
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
    ]


@pytest.mark.asyncio
async def test_search_without_vacancy_or_query_is_honest_clarification():
    from app.shared.execution import discrete_actions as da

    search = AsyncMock()
    with patch.object(da, "PearchService") as PS:
        PS.return_value.search_by_job_description = search

        handler = da.get_discrete_handler("sourcing", "search_candidates")
        resp = await handler({}, _action_context(raw_query=""))

    search.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
async def test_search_no_results_is_honest_empty_not_fake():
    from app.shared.execution import discrete_actions as da

    search = AsyncMock(return_value=_pearch_response([]))
    jd = AsyncMock(return_value={"title": "X", "description": "Y", "location": None})

    with patch.object(da, "PearchService") as PS, \
         patch.object(da, "_get_vacancy_jd", jd):
        PS.return_value.search_by_job_description = search

        handler = da.get_discrete_handler("sourcing", "search_candidates")
        resp = await handler({"vacancy_id": "job-1"}, _action_context())

    search.assert_awaited_once()
    assert resp.success is True
    assert (resp.data or {}).get("candidates") == []
    assert (resp.data or {}).get("candidate_ids") == []


# ---------------------------------------------------------------------------
# 4-5. cv_screening.score_candidates
# ---------------------------------------------------------------------------
def _score_result(cid, name, rubric, sub_status):
    return {
        "success": True,
        "candidate_id": cid,
        "candidate_name": name,
        "rubric_score": rubric,
        "cv_fit": "Alto" if rubric >= 70 else "Médio",
        "recommendation": "Recomendado" if sub_status == "cv_approved" else "Não recomendado",
        "sub_status": sub_status,
        "strengths": [],
        "concerns": [],
    }


@pytest.mark.asyncio
async def test_score_calls_standalone_per_candidate_ranks_and_marks_approved():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock(side_effect=[
        _score_result("c1", "Ana", 60, "cv_rejected"),
        _score_result("c2", "Bruno", 90, "cv_approved"),
        _score_result("c3", "Carla", 75, "cv_approved"),
    ])

    with patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score

        handler = da.get_discrete_handler("cv_screening", "score_candidates")
        assert handler is not None, "handler de score_candidates não registrado"

        resp = await handler(
            {
                "vacancy_id": "job-1",
                "candidates": [
                    {"id": "c1", "name": "Ana"},
                    {"id": "c2", "name": "Bruno"},
                    {"id": "c3", "name": "Carla"},
                ],
            },
            _action_context(),
        )

    assert resp.success is True
    # uma chamada por candidato, tenant-scoped
    assert score.await_count == 3
    assert score.await_args.kwargs.get("company_id") == "co-1227"
    assert score.await_args.kwargs.get("vacancy_id") == "job-1"
    # ranqueado por rubric_score desc
    ranking = resp.data["ranking"]
    scores = [r["rubric_score"] for r in ranking if r.get("success")]
    assert scores == sorted(scores, reverse=True)
    # aprovados = sub_status cv_approved (reuso da classificação do serviço)
    assert set(resp.data["approved_candidate_ids"]) == {"c2", "c3"}


@pytest.mark.asyncio
async def test_score_without_candidates_is_honest_error():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock()
    with patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score

        handler = da.get_discrete_handler("cv_screening", "score_candidates")
        resp = await handler({"vacancy_id": "job-1", "candidates": []}, _action_context())

    score.assert_not_awaited()
    assert resp.success is False


# ---------------------------------------------------------------------------
# 6-8. cv_screening.add_approved_to_vacancy (gated dispatch)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_add_approved_reuses_tool_tenant_scoped_for_each_id():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock(return_value={"success": True, "message": "ok"})
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_approved_to_vacancy")
        assert handler is not None, "handler de add_approved_to_vacancy não registrado"

        resp = await handler(
            {"job_id": "job-1", "approved_candidate_ids": ["c2", "c3"]},
            _action_context(),
        )

    assert resp.success is True
    assert add.await_count == 2
    # _context tenant-scoped (company_id do actx, nunca client-provided)
    ctx_obj = add.await_args.kwargs.get("_context")
    assert getattr(ctx_obj, "company_id", None) == "co-1227"
    assert add.await_args.kwargs.get("job_id") == "job-1"


@pytest.mark.asyncio
async def test_add_reports_failures_without_fake_success():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock(side_effect=[
        {"success": True},
        {"success": False, "error": "candidate_not_found"},
    ])
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_approved_to_vacancy")
        resp = await handler(
            {"job_id": "job-1", "approved_candidate_ids": ["c2", "c-ext"]},
            _action_context(),
        )

    # 1 adicionado, 1 falha — reportado honestamente
    assert resp.success is True
    assert resp.data["added"] == ["c2"]
    assert len(resp.data["failures"]) == 1
    assert resp.data["failures"][0]["candidate_id"] == "c-ext"


@pytest.mark.asyncio
async def test_add_without_ids_is_honest_clarification():
    from app.shared.execution import discrete_actions as da

    add = AsyncMock()
    with patch.object(da, "add_candidate_to_vacancy", add):
        handler = da.get_discrete_handler("cv_screening", "add_approved_to_vacancy")
        resp = await handler({"job_id": "job-1", "approved_candidate_ids": []}, _action_context())

    add.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


# ---------------------------------------------------------------------------
# 9-10. plan_detector pattern + chaining via PlanExecutor
# ---------------------------------------------------------------------------
def test_plan_detector_matches_pattern_without_creation_step():
    from app.shared.execution.plan_detector import PlanDetector

    plan = PlanDetector().detect("busque candidatos para a vaga e pontue")
    assert plan is not None
    assert plan.detected_pattern == "buscar_pontuar_e_adicionar"
    assert len(plan.tasks) == 2
    # INVIOLÁVEL #1211 — nenhum step de criação de vaga
    action_ids = {t.action_id for t in plan.tasks}
    assert action_ids == {"search_candidates", "score_candidates"}
    assert not any("creat" in a or "criar" in a for a in action_ids)


@pytest.mark.asyncio
async def test_search_score_chains_candidates_via_executor():
    from app.shared.execution import discrete_actions as da
    from app.shared.execution.plan_detector import PlanDetector
    from app.shared.execution.plan_executor import PlanExecutor

    plan = PlanDetector().detect("busque candidatos para a vaga e pontue")
    assert plan is not None and len(plan.tasks) == 2

    search = AsyncMock(return_value=_pearch_response([
        _profile("c1", "Ana", match_score=60),
        _profile("c2", "Bruno", match_score=90),
    ]))
    jd = AsyncMock(return_value={"title": "X", "description": "Python", "location": None})
    score = AsyncMock(side_effect=[
        _score_result("c1", "Ana", 60, "cv_rejected"),
        _score_result("c2", "Bruno", 90, "cv_approved"),
    ])

    with patch.object(da, "PearchService") as PS, \
         patch.object(da, "_get_vacancy_jd", jd), \
         patch.object(da, "CVScoringService") as CS:
        PS.return_value.search_by_job_description = search
        CS.return_value.score_candidate_standalone = score

        executor = PlanExecutor()
        result = await executor.execute(
            plan,
            user_id="user-1227",
            session_id="sess-1227",
            tenant_id="co-1227",
            base_context={"company_id": "co-1227", "vacancy_id": "job-1"},
        )

    search.assert_awaited_once()
    # candidatos da busca chegaram ao score (chaining task_0.candidates)
    assert score.await_count == 2
    # aprovados derivados do scoring real
    approved = result.get_context("task_1.approved_candidate_ids")
    assert approved == ["c2"]
    assert all(t.status.value == "completed" for t in result.tasks), \
        [(t.task_id, t.status.value, t.error) for t in result.tasks]


# ---------------------------------------------------------------------------
# 11. Gate de confirmação (módulo puro espelhando post_wizard_continuation)
# ---------------------------------------------------------------------------
def test_add_offer_gate_store_and_classify_roundtrip():
    from app.orchestrator.execution.pending_action import PendingActionStore
    from app.orchestrator.routing import pe_add_to_vacancy_continuation as cont

    store = PendingActionStore()
    state = cont.store_add_offer(
        "conv-1227", "co-1227", "job-1", ["c2", "c3"], store=store,
    )
    assert state is not None
    assert state.intent == cont.ADD_CONTINUATION_INTENT
    assert state.awaiting_confirmation is True
    assert state.collected_params["job_id"] == "job-1"
    assert state.collected_params["approved_candidate_ids"] == ["c2", "c3"]

    got = cont.get_add_continuation("conv-1227", store=store)
    assert got is not None and cont.is_add_continuation(got)

    # sem ids/job → nada a parkear (honesto)
    assert cont.store_add_offer("c", "co", None, [], store=store) is None

    cont.clear_add_continuation("conv-1227", store=store)
    assert cont.get_add_continuation("conv-1227", store=store) is None
