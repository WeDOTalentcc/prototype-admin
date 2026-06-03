"""
Task #1226 — Fluxo P&E "Mover e notificar (+ avisar o time)".

Sentinelas do caminho REAL (não delegate/fake) dos discrete handlers do
PlanExecutor para o pattern `mover_e_notificar`:

  1. move_candidate_stage REUSA o caminho compliant: FairnessGuard L3
     (pipeline_move) + PipelineStageService.transition_candidate + AuditService
     (decision_type=move_stage). Retorna `movement_data` para o chaining.
  2. move sem params obrigatórios → clarification honesta (NUNCA fake success;
     transition_candidate não é chamado).
  3. move com FairnessGuard bloqueado → não move (transition_candidate não é
     chamado), resposta honesta de bloqueio.
  4. send_notification cria notificações in-app para o time + audita
     (decision_type=send_message) + roda fairness LEVE no conteúdo.
  5. fairness na notificação é NÃO bloqueante no caminho feliz (soft warnings
     não impedem o envio).
  6. send_notification sem destinatários → erro honesto (não cria notificação,
     não finge sucesso).
  7. Chaining mover→notificar: `task_0.movement_data` é injetado e chega ao
     handler de notificação via PlanExecutor.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _action_context(raw_query="mover candidato e notificar o time"):
    from app.shared.execution.discrete_actions import ActionContext
    return ActionContext(
        company_id="co-1226",
        user_id="user-1226",
        session_id="sess-1226",
        tenant_id="co-1226",
        raw_query=raw_query,
        base_context={},
    )


def _fairness_ok():
    """check_with_layer3 / check retornando resultado limpo."""
    res = MagicMock()
    res.is_blocked = False
    res.category = None
    res.blocked_terms = []
    res.soft_warnings = []
    res.educational_message = None
    return res


def _fairness_blocked():
    res = MagicMock()
    res.is_blocked = True
    res.category = "age"
    res.blocked_terms = ["energia jovem"]
    res.soft_warnings = []
    res.educational_message = "Critério pode configurar discriminação etária."
    return res


# ---------------------------------------------------------------------------
# 1. move_candidate_stage — caminho compliant real
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_move_reuses_compliant_service_and_audits():
    from app.shared.execution import discrete_actions as da

    transition = AsyncMock(return_value={
        "success": True,
        "from_stage": "triagem",
        "to_stage": "entrevista",
        "candidate_id": "cand-1",
    })
    audit = AsyncMock()
    guard = MagicMock()
    guard.check_with_layer3 = AsyncMock(return_value=_fairness_ok())
    guard.log_check = AsyncMock()

    with patch.object(da, "PipelineStageService") as PSS, \
         patch.object(da, "AuditService") as AS, \
         patch.object(da, "FairnessGuard", return_value=guard):
        PSS.return_value.transition_candidate = transition
        AS.return_value.log_decision = audit

        handler = da.get_discrete_handler("automation", "move_candidate_stage")
        assert handler is not None, "handler de move_candidate_stage não registrado"

        resp = await handler(
            {"vacancy_candidate_id": "vc-1", "to_stage": "entrevista"},
            _action_context(),
        )

    assert resp.success is True
    transition.assert_awaited_once()
    _, kwargs = transition.call_args
    assert kwargs["vacancy_candidate_id"] == "vc-1"
    assert kwargs["to_stage"] == "entrevista"
    # company/tenant preservado no context da transição
    assert (kwargs.get("context") or {}).get("company_id") == "co-1226"

    # auditoria move_stage
    audit.assert_awaited()
    a_kwargs = audit.call_args.kwargs
    assert a_kwargs["decision_type"] == "move_stage"
    assert a_kwargs["company_id"] == "co-1226"

    # fairness BLOQUEANTE (L3) rodou no pedido
    guard.check_with_layer3.assert_awaited()

    # dados de chaining para a notificação
    assert isinstance(resp.data, dict)
    assert "movement_data" in resp.data


@pytest.mark.asyncio
async def test_move_missing_params_is_honest_clarification_not_fake():
    from app.shared.execution import discrete_actions as da

    transition = AsyncMock()
    with patch.object(da, "PipelineStageService") as PSS, \
         patch.object(da, "AuditService"), \
         patch.object(da, "FairnessGuard"):
        PSS.return_value.transition_candidate = transition

        handler = da.get_discrete_handler("automation", "move_candidate_stage")
        resp = await handler({}, _action_context())

    # honesto: não executou e não fingiu sucesso
    transition.assert_not_awaited()
    assert resp.needs_clarification is True or resp.success is False


@pytest.mark.asyncio
async def test_move_fairness_blocked_does_not_move():
    from app.shared.execution import discrete_actions as da

    transition = AsyncMock()
    guard = MagicMock()
    guard.check_with_layer3 = AsyncMock(return_value=_fairness_blocked())
    guard.log_check = AsyncMock()

    with patch.object(da, "PipelineStageService") as PSS, \
         patch.object(da, "AuditService"), \
         patch.object(da, "FairnessGuard", return_value=guard):
        PSS.return_value.transition_candidate = transition

        handler = da.get_discrete_handler("automation", "move_candidate_stage")
        resp = await handler(
            {"vacancy_candidate_id": "vc-1", "to_stage": "entrevista"},
            _action_context("mover quem tem energia jovem e avisar"),
        )

    transition.assert_not_awaited()
    assert resp.success is False


# ---------------------------------------------------------------------------
# 4-6. send_notification — handler real + compliance (audit + fairness leve)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_notify_creates_notifications_with_audit_and_light_fairness():
    from app.shared.execution import discrete_actions as da

    create_notif = AsyncMock(return_value={"success": True})
    audit = AsyncMock()
    guard = MagicMock()
    guard.check = MagicMock(return_value=_fairness_ok())
    guard.log_check = AsyncMock()
    resolver = AsyncMock(return_value=[("u1", "a@x.com"), ("u2", "b@x.com")])

    with patch.object(da, "notification_service") as NS, \
         patch.object(da, "AuditService") as AS, \
         patch.object(da, "FairnessGuard", return_value=guard), \
         patch.object(da, "_resolve_team_recipients", resolver):
        NS.create_notification = create_notif
        AS.return_value.log_decision = audit

        handler = da.get_discrete_handler("communication", "send_notification")
        assert handler is not None, "handler de send_notification não registrado"

        resp = await handler(
            {"movement_data": {"to_stage": "entrevista", "candidate_id": "cand-1"}},
            _action_context(),
        )

    assert resp.success is True
    assert create_notif.await_count == 2
    audit.assert_awaited()
    assert audit.call_args.kwargs["decision_type"] == "send_message"
    # fairness LEVE rodou no conteúdo da notificação
    guard.check.assert_called()


@pytest.mark.asyncio
async def test_notify_fairness_is_non_blocking_on_soft_warnings():
    from app.shared.execution import discrete_actions as da

    create_notif = AsyncMock(return_value={"success": True})
    warned = MagicMock()
    warned.is_blocked = False
    warned.category = None
    warned.blocked_terms = []
    warned.soft_warnings = ["aviso leve"]
    warned.educational_message = None
    guard = MagicMock()
    guard.check = MagicMock(return_value=warned)
    guard.log_check = AsyncMock()
    resolver = AsyncMock(return_value=[("u1", "a@x.com")])

    with patch.object(da, "notification_service") as NS, \
         patch.object(da, "AuditService"), \
         patch.object(da, "FairnessGuard", return_value=guard), \
         patch.object(da, "_resolve_team_recipients", resolver):
        NS.create_notification = create_notif

        handler = da.get_discrete_handler("communication", "send_notification")
        resp = await handler({"message": "Atualização do pipeline"}, _action_context())

    # soft warning NÃO bloqueia o envio
    assert resp.success is True
    create_notif.assert_awaited()


@pytest.mark.asyncio
async def test_notify_no_recipients_is_honest_error():
    from app.shared.execution import discrete_actions as da

    create_notif = AsyncMock()
    guard = MagicMock()
    guard.check = MagicMock(return_value=_fairness_ok())
    guard.log_check = AsyncMock()
    resolver = AsyncMock(return_value=[])

    with patch.object(da, "notification_service") as NS, \
         patch.object(da, "AuditService"), \
         patch.object(da, "FairnessGuard", return_value=guard), \
         patch.object(da, "_resolve_team_recipients", resolver):
        NS.create_notification = create_notif

        handler = da.get_discrete_handler("communication", "send_notification")
        resp = await handler({"message": "x"}, _action_context())

    create_notif.assert_not_awaited()
    assert resp.success is False


# ---------------------------------------------------------------------------
# 6b. SECURITY — recipient_user_ids são validados contra o tenant
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_notify_explicit_recipients_validated_against_tenant():
    """IDs explícitos (untrusted) NÃO podem ser usados crus — passam pelo
    resolver tenant-scoped `_resolve_recipients_by_ids`."""
    from app.shared.execution import discrete_actions as da

    create_notif = AsyncMock(return_value={"success": True})
    guard = MagicMock()
    guard.check = MagicMock(return_value=_fairness_ok())
    guard.log_check = AsyncMock()
    # resolver retorna SÓ o id que pertence ao tenant (o cross-tenant é descartado)
    by_ids = AsyncMock(return_value=[("u-do-tenant", "ok@x.com")])
    team = AsyncMock(return_value=[])

    with patch.object(da, "notification_service") as NS, \
         patch.object(da, "AuditService"), \
         patch.object(da, "FairnessGuard", return_value=guard), \
         patch.object(da, "_resolve_recipients_by_ids", by_ids), \
         patch.object(da, "_resolve_team_recipients", team):
        NS.create_notification = create_notif

        handler = da.get_discrete_handler("communication", "send_notification")
        resp = await handler(
            {
                "message": "x",
                "recipient_user_ids": ["u-do-tenant", "u-de-outro-tenant"],
            },
            _action_context(),
        )

    # caminho de IDs explícitos foi validado via resolver tenant-scoped
    by_ids.assert_awaited_once()
    assert by_ids.await_args.args[0] == "co-1226"
    assert set(by_ids.await_args.args[1]) == {"u-do-tenant", "u-de-outro-tenant"}
    # NÃO caiu no caminho do time
    team.assert_not_awaited()
    # só criou notificação para o id que o resolver liberou (tenant-scoped)
    assert create_notif.await_count == 1
    assert resp.success is True


@pytest.mark.asyncio
async def test_notify_explicit_recipients_all_cross_tenant_is_honest_error():
    """Se todos os IDs explícitos forem de fora do tenant, o resolver retorna
    vazio → erro honesto, nenhuma notificação criada."""
    from app.shared.execution import discrete_actions as da

    create_notif = AsyncMock()
    guard = MagicMock()
    guard.check = MagicMock(return_value=_fairness_ok())
    guard.log_check = AsyncMock()
    by_ids = AsyncMock(return_value=[])

    with patch.object(da, "notification_service") as NS, \
         patch.object(da, "AuditService"), \
         patch.object(da, "FairnessGuard", return_value=guard), \
         patch.object(da, "_resolve_recipients_by_ids", by_ids):
        NS.create_notification = create_notif

        handler = da.get_discrete_handler("communication", "send_notification")
        resp = await handler(
            {"message": "x", "recipient_user_ids": ["u-de-outro-tenant"]},
            _action_context(),
        )

    create_notif.assert_not_awaited()
    assert resp.success is False


# ---------------------------------------------------------------------------
# 7. Chaining ponta-a-ponta via PlanExecutor
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mover_e_notificar_chains_movement_data_via_executor():
    from app.shared.execution import discrete_actions as da
    from app.shared.execution.plan_detector import PlanDetector
    from app.shared.execution.plan_executor import PlanExecutor

    plan = PlanDetector().detect("mover o candidato cand-1 para entrevista e notificar o time")
    assert plan is not None and len(plan.tasks) == 2

    transition = AsyncMock(return_value={
        "success": True, "from_stage": "triagem", "to_stage": "entrevista",
        "candidate_id": "cand-1",
    })
    create_notif = AsyncMock(return_value={"success": True})
    guard = MagicMock()
    guard.check_with_layer3 = AsyncMock(return_value=_fairness_ok())
    guard.check = MagicMock(return_value=_fairness_ok())
    guard.log_check = AsyncMock()
    resolver = AsyncMock(return_value=[("u1", "a@x.com")])

    captured = {}

    async def _capture_resolver(company_id):
        captured["company_id"] = company_id
        return [("u1", "a@x.com")]

    with patch.object(da, "PipelineStageService") as PSS, \
         patch.object(da, "AuditService") as AS, \
         patch.object(da, "FairnessGuard", return_value=guard), \
         patch.object(da, "notification_service") as NS, \
         patch.object(da, "_resolve_team_recipients", side_effect=_capture_resolver):
        PSS.return_value.transition_candidate = transition
        AS.return_value.log_decision = AsyncMock()
        NS.create_notification = create_notif

        executor = PlanExecutor()
        result = await executor.execute(
            plan,
            user_id="user-1226",
            session_id="sess-1226",
            tenant_id="co-1226",
            base_context={
                "company_id": "co-1226",
                "vacancy_candidate_id": "vc-1",
                "to_stage": "entrevista",
            },
        )

    # ambos os passos executaram de verdade
    transition.assert_awaited_once()
    create_notif.assert_awaited()
    # movement_data foi injetado no contexto do plano após o task_0
    assert result.get_context("task_0.movement_data") is not None
    # nenhuma tarefa ficou pendente/falha
    assert all(t.status.value in ("completed",) for t in result.tasks), \
        [(t.task_id, t.status.value, t.error) for t in result.tasks]
