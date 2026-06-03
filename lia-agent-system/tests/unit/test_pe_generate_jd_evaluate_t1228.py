"""
Task #1228 — Fluxo P&E "Gerar/enriquecer JD e avaliar (item 2)".

Sentinelas do caminho REAL (não delegate/fake) dos discrete handlers do
PlanExecutor para o pattern `gerar_jd_e_avaliar`:

  1. job_management.generate_jd REUSA `JdEnrichmentService.enrich_and_persist_vacancy`
     tenant-scoped e, quando persiste, emite `jd_data` (com vacancy_id) p/ chaining.
  2. generate_jd sem vaga → clarification honesta (não chama o primitivo).
  3. generate_jd com mínimos WSI NÃO atingidos → clarification honesta
     (persisted=False; NUNCA grava "no vácuo", sem fake success).
  4. generate_jd com falha do primitivo → erro honesto.
  5. o wrapper `_enrich_and_persist_jd` REUSA `enrich_and_persist_vacancy`
     (mesmo primitivo WSI), tenant-scoped (company_id + job_vacancy_id).
  6. cv_screening.evaluate_against_jd chama `score_candidate_standalone` por
     candidato (MESMO primitivo do item 1), tenant-scoped, e retorna o payload
     BARS (padrão do modal de CV) em `evaluations` + ranking.
  7. evaluate sem vaga → clarification.
  8. evaluate sem candidato → clarification.
  9. evaluate lê vacancy_id do `jd_data` encadeado (task_0.jd_data).
 10. evaluate carrega candidato por id tenant-scoped quando só há candidate_id.
 11. evaluate quando todos falham → erro honesto (não finge sucesso).
 12. plan_detector casa gerar_jd_e_avaliar (2 tasks) e NÃO contém step de criação
     de vaga (INVIOLÁVEL #1211); cobre o imperativo "gere".
 13. Chaining generate_jd→evaluate via PlanExecutor: jd_data injeta vacancy_id.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _action_context(raw_query="gere a jd da vaga e avalie o candidato", base_context=None):
    from app.shared.execution.discrete_actions import ActionContext
    return ActionContext(
        company_id="co-1228",
        user_id="user-1228",
        session_id="sess-1228",
        tenant_id="co-1228",
        raw_query=raw_query,
        base_context=base_context or {},
    )


def _persist_result(persisted=True, meets=True, message="ok", success=True):
    from app.schemas.jd_enrichment import JdEnrichmentPersistResult
    return JdEnrichmentPersistResult(
        success=success,
        persisted=persisted,
        meets_wsi_minimums=meets,
        job_vacancy_id="job-1228",
        technical_count=9 if meets else 3,
        behavioral_count=5 if meets else 1,
        responsibilities_count=6,
        wsi_quality_score=0.91 if meets else 0.4,
        wsi_quality_warnings=[] if meets else ["faltam competências"],
        message=message,
    )


def _score_result(cid, name, rubric, sub_status):
    return {
        "success": True,
        "candidate_id": cid,
        "candidate_name": name,
        "vacancy_id": "job-1228",
        "rubric_score": rubric,
        "cv_fit": {"classification": "Alto" if rubric >= 70 else "Médio"},
        "recommendation": "Recomendado" if sub_status == "cv_approved" else "Não recomendado",
        "sub_status": sub_status,
        "strengths": [],
        "concerns": [],
        "evaluations": [],
        "persisted": False,
        "standalone": True,
    }


# ---------------------------------------------------------------------------
# 1-4. job_management.generate_jd
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_jd_reuses_persist_and_emits_jd_data():
    from app.shared.execution import discrete_actions as da

    persist = AsyncMock(return_value=_persist_result(persisted=True, meets=True,
                                                      message="JD enriquecida e salva."))
    with patch.object(da, "_enrich_and_persist_jd", persist):
        handler = da.get_discrete_handler("job_management", "generate_jd")
        assert handler is not None, "handler de generate_jd não registrado"

        resp = await handler({"vacancy_id": "job-1228"}, _action_context())

    assert resp.success is True
    persist.assert_awaited_once()
    p_kwargs = persist.call_args.kwargs
    assert p_kwargs.get("company_id") == "co-1228"
    assert p_kwargs.get("vacancy_id") == "job-1228"
    jd_data = (resp.data or {}).get("jd_data")
    assert isinstance(jd_data, dict)
    assert jd_data.get("vacancy_id") == "job-1228"
    assert jd_data.get("persisted") is True


@pytest.mark.asyncio
async def test_generate_jd_without_vacancy_is_honest_clarification():
    from app.shared.execution import discrete_actions as da

    persist = AsyncMock()
    with patch.object(da, "_enrich_and_persist_jd", persist):
        handler = da.get_discrete_handler("job_management", "generate_jd")
        resp = await handler({}, _action_context(raw_query=""))

    persist.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
async def test_generate_jd_minimums_not_met_is_honest_no_fake():
    from app.shared.execution import discrete_actions as da

    persist = AsyncMock(return_value=_persist_result(
        persisted=False, meets=False,
        message="Faltam 6 competências técnicas e 4 comportamentais.",
    ))
    with patch.object(da, "_enrich_and_persist_jd", persist):
        handler = da.get_discrete_handler("job_management", "generate_jd")
        resp = await handler({"vacancy_id": "job-1228"}, _action_context())

    persist.assert_awaited_once()
    # honesto: pede mais info, NÃO finge que persistiu
    assert resp.needs_clarification is True or resp.success is False
    assert "compet" in (resp.message or "").lower()


@pytest.mark.asyncio
async def test_generate_jd_primitive_failure_is_honest_error():
    from app.shared.execution import discrete_actions as da

    persist = AsyncMock(return_value=_persist_result(
        success=False, persisted=False, meets=False, message="Vaga não encontrada",
    ))
    with patch.object(da, "_enrich_and_persist_jd", persist):
        handler = da.get_discrete_handler("job_management", "generate_jd")
        resp = await handler({"vacancy_id": "job-1228"}, _action_context())

    assert resp.success is False


@pytest.mark.asyncio
async def test_enrich_wrapper_reuses_canonical_primitive_tenant_scoped():
    from app.shared.execution import discrete_actions as da

    enrich = AsyncMock(return_value=_persist_result())
    svc_instance = MagicMock()
    svc_instance.enrich_and_persist_vacancy = enrich

    session = AsyncMock()
    acm = MagicMock()
    acm.__aenter__ = AsyncMock(return_value=session)
    acm.__aexit__ = AsyncMock(return_value=False)

    with patch.object(da, "JdEnrichmentService", return_value=svc_instance), \
         patch("lia_config.database.AsyncSessionLocal", MagicMock(return_value=acm)):
        await da._enrich_and_persist_jd(company_id="co-1228", vacancy_id="job-1228")

    enrich.assert_awaited_once()
    kwargs = enrich.call_args.kwargs
    assert kwargs.get("company_id") == "co-1228"
    assert kwargs.get("job_vacancy_id") == "job-1228"


# ---------------------------------------------------------------------------
# 6-11. cv_screening.evaluate_against_jd
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_evaluate_calls_standalone_per_candidate_and_returns_cards():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock(side_effect=[
        _score_result("c1", "Ana", 60, "cv_rejected"),
        _score_result("c2", "Bruno", 90, "cv_approved"),
    ])
    with patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score

        handler = da.get_discrete_handler("cv_screening", "evaluate_against_jd")
        assert handler is not None, "handler de evaluate_against_jd não registrado"

        resp = await handler(
            {
                "vacancy_id": "job-1228",
                "candidates": [{"id": "c1", "name": "Ana"}, {"id": "c2", "name": "Bruno"}],
            },
            _action_context(),
        )

    assert resp.success is True
    assert score.await_count == 2
    assert score.await_args.kwargs.get("company_id") == "co-1228"
    assert score.await_args.kwargs.get("vacancy_id") == "job-1228"
    # ranking por rubric_score desc
    ranking = resp.data["ranking"]
    scores = [r["rubric_score"] for r in ranking if r.get("success")]
    assert scores == sorted(scores, reverse=True)
    # payload BARS no padrão do modal de CV (cards completos)
    evaluations = resp.data.get("evaluations")
    assert isinstance(evaluations, list) and len(evaluations) == 2
    assert evaluations[0].get("standalone") is True


@pytest.mark.asyncio
async def test_evaluate_without_vacancy_is_clarification():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock()
    with patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score
        handler = da.get_discrete_handler("cv_screening", "evaluate_against_jd")
        resp = await handler({"candidates": [{"id": "c1", "name": "Ana"}]}, _action_context())

    score.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
async def test_evaluate_without_candidate_is_clarification():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock()
    with patch.object(da, "CVScoringService") as CS, \
         patch.object(da, "_get_candidate_for_scoring", AsyncMock(return_value=None)):
        CS.return_value.score_candidate_standalone = score
        handler = da.get_discrete_handler("cv_screening", "evaluate_against_jd")
        resp = await handler({"vacancy_id": "job-1228"}, _action_context())

    score.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
async def test_evaluate_reads_vacancy_from_chained_jd_data():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock(return_value=_score_result("c1", "Ana", 80, "cv_approved"))
    with patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score
        handler = da.get_discrete_handler("cv_screening", "evaluate_against_jd")
        resp = await handler(
            {
                "jd_data": {"vacancy_id": "job-from-jd", "persisted": True},
                "candidates": [{"id": "c1", "name": "Ana"}],
            },
            _action_context(),
        )

    assert resp.success is True
    assert score.await_args.kwargs.get("vacancy_id") == "job-from-jd"


@pytest.mark.asyncio
async def test_evaluate_loads_candidate_by_id_tenant_scoped():
    from app.shared.execution import discrete_actions as da

    loader = AsyncMock(return_value={"id": "c9", "name": "Carla", "resume_text": "x"})
    score = AsyncMock(return_value=_score_result("c9", "Carla", 88, "cv_approved"))
    with patch.object(da, "CVScoringService") as CS, \
         patch.object(da, "_get_candidate_for_scoring", loader):
        CS.return_value.score_candidate_standalone = score
        handler = da.get_discrete_handler("cv_screening", "evaluate_against_jd")
        resp = await handler(
            {"vacancy_id": "job-1228", "candidate_id": "c9"},
            _action_context(),
        )

    assert resp.success is True
    loader.assert_awaited_once()
    l_args = loader.call_args
    # tenant-scoped: company_id do actx repassado ao loader
    assert "co-1228" in [str(a) for a in l_args.args] + [str(v) for v in l_args.kwargs.values()]
    assert score.await_count == 1


@pytest.mark.asyncio
async def test_evaluate_all_fail_is_honest_error():
    from app.shared.execution import discrete_actions as da

    score = AsyncMock(return_value={"success": False, "error": "no_requirements"})
    with patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score
        handler = da.get_discrete_handler("cv_screening", "evaluate_against_jd")
        resp = await handler(
            {"vacancy_id": "job-1228", "candidates": [{"id": "c1", "name": "Ana"}]},
            _action_context(),
        )

    assert resp.success is False


# ---------------------------------------------------------------------------
# 12-13. plan_detector pattern + chaining via PlanExecutor
# ---------------------------------------------------------------------------
def test_plan_detector_matches_gerar_jd_e_avaliar_without_creation_step():
    from app.shared.execution.plan_detector import PlanDetector

    for phrase in (
        "gerar a jd da vaga e avaliar o candidato",
        "gere a descrição e avalie os candidatos",
    ):
        plan = PlanDetector().detect(phrase)
        assert plan is not None, f"não casou: {phrase!r}"
        assert plan.detected_pattern == "gerar_jd_e_avaliar"
        assert len(plan.tasks) == 2
        action_ids = {t.action_id for t in plan.tasks}
        assert action_ids == {"generate_jd", "evaluate_against_jd"}
        # INVIOLÁVEL #1211 — nenhum step de criação de vaga
        assert not any("creat" in a or "criar" in a for a in action_ids)


@pytest.mark.asyncio
async def test_generate_jd_evaluate_chains_via_executor():
    from app.shared.execution import discrete_actions as da
    from app.shared.execution.plan_detector import PlanDetector
    from app.shared.execution.plan_executor import PlanExecutor

    plan = PlanDetector().detect("gerar a jd da vaga e avaliar o candidato")
    assert plan is not None and len(plan.tasks) == 2

    persist = AsyncMock(return_value=_persist_result(persisted=True, meets=True))
    score = AsyncMock(return_value=_score_result("c1", "Ana", 85, "cv_approved"))

    with patch.object(da, "_enrich_and_persist_jd", persist), \
         patch.object(da, "CVScoringService") as CS:
        CS.return_value.score_candidate_standalone = score

        executor = PlanExecutor()
        result = await executor.execute(
            plan,
            user_id="user-1228",
            session_id="sess-1228",
            tenant_id="co-1228",
            base_context={
                "company_id": "co-1228",
                "vacancy_id": "job-1228",
                "candidates": [{"id": "c1", "name": "Ana"}],
            },
        )

    persist.assert_awaited_once()
    # vacancy_id do generate_jd (jd_data) chegou ao evaluate
    assert score.await_count == 1
    assert score.await_args.kwargs.get("vacancy_id") == "job-1228"
    assert all(t.status.value == "completed" for t in result.tasks), \
        [(t.task_id, t.status.value, t.error) for t in result.tasks]
