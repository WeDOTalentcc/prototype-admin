"""
Audit trail da FairnessGuard — testes RED-GREEN-REFACTOR.

Cobre:
  Fix A — SSE pre-dispatch: log_check() chamado ao bloquear
  Fix B — EnhancedAgentMixin._fairness_pre_check: log_check() chamado ao bloquear
  Fix C1 — hiring_policy: gate de fairness antes de PolicyReActAgent
  Fix C2 — pipeline_orchestrator: gate antes de PipelineReActAgent
  Fix C3 — task_planner: gate antes de AutomationReActAgent

Estratégia: testar handlers diretamente (não via HTTP/middleware).
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── helpers ─────────────────────────────────────────────────────────────────

def _blocked(category: str = "genero"):
    from app.shared.compliance.fairness_guard import FairnessCheckResult
    return FairnessCheckResult(
        is_blocked=True,
        blocked_terms=["somente homens"],
        category=category,
        educational_message="Mensagem educacional de teste.",
        original_query="somente homens",
        confidence=0.95,
    )


def _clean():
    from app.shared.compliance.fairness_guard import FairnessCheckResult
    return FairnessCheckResult(
        is_blocked=False,
        blocked_terms=[],
        category=None,
        educational_message=None,
        original_query="dev Python senior",
        confidence=0.0,
    )


# ─── Fix A: SSE pre-dispatch persiste bloqueio ───────────────────────────────

class TestSSEFairnessAuditTrail:
    """Fix A: gate LIA-P03 em agent_chat_sse.py deve chamar log_check() ao bloquear."""

    @pytest.mark.asyncio
    async def test_sse_bloqueia_e_chama_log_check(self):
        """
        Simula execução do bloco LIA-P03:
        FairnessGuard.check() retorna blocked → HTTPException 400
        E log_check() deve ter sido chamado.
        """
        from fastapi import HTTPException

        log_check_mock = AsyncMock()
        blocked = _blocked()

        # Simula o bloco LIA-P03 da forma como está no código
        _company_id = "co-123"
        _user_id = "usr-456"

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=blocked,
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            log_check_mock,
        ):
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fr = _fg.check("somente homens")

            # Esta é a lógica que o Fix A adicionou:
            if _fr and _fr.is_blocked:
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(
                        _fg.log_check(
                            result=_fr,
                            context="chat_sse",
                            company_id=_company_id or None,
                            recruiter_id=_user_id or None,
                        )
                    )
                except Exception:
                    pass

        # deixa tasks pendentes completar
        await asyncio.sleep(0.05)
        log_check_mock.assert_called_once()
        kw = log_check_mock.call_args.kwargs
        assert kw.get("company_id") == "co-123"
        assert kw.get("recruiter_id") == "usr-456"
        assert kw.get("context") == "chat_sse"

    def test_sse_fairness_gate_chama_log_check_ao_bloquear_codigo(self):
        """Verifica que o código do SSE realmente chama log_check (inspecção estática)."""
        import ast, textwrap

        with open("app/api/v1/agent_chat_sse.py") as f:
            source = f.read()

        # Deve conter log_check na vizinhança do bloco LIA-P03
        assert "log_check" in source, (
            "Fix A ausente: agent_chat_sse.py não chama log_check(). "
            "Adicione create_task(_fg.log_check(...)) antes do raise HTTPException no bloco LIA-P03."
        )

        # Verifica que log_check aparece ANTES do raise na mesma região
        lia_p03_idx = source.find("LIA-P03")
        assert lia_p03_idx != -1, "Bloco LIA-P03 não encontrado"
        block = source[lia_p03_idx : lia_p03_idx + 800]
        log_check_in_block = "log_check" in block
        assert log_check_in_block, (
            f"log_check não encontrado no bloco LIA-P03 (primeiros 800 chars após marcador).\n"
            f"Bloco:\n{block}"
        )


# ─── Fix B: EnhancedAgentMixin._fairness_pre_check persiste bloqueio ─────────

class TestMixinFairnessAuditTrail:
    """Fix B: _fairness_pre_check deve aceitar company_id kwarg e chamar log_check()."""

    @pytest.fixture
    def mixin(self):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin

        class _TestAgent(EnhancedAgentMixin):
            _enhanced_domain = "test_domain"

        return _TestAgent()

    @pytest.mark.asyncio
    async def test_pre_check_aceita_company_id_kwarg(self, mixin):
        """_fairness_pre_check deve aceitar company_id= e recruiter_id= como kwargs."""
        import inspect
        sig = inspect.signature(mixin._fairness_pre_check)
        params = list(sig.parameters.keys())
        assert "company_id" in params, (
            "Fix B ausente: _fairness_pre_check não tem parâmetro company_id. "
            "Adicione *, company_id: Optional[str] = None na assinatura."
        )
        assert "recruiter_id" in params, (
            "Fix B ausente: _fairness_pre_check não tem parâmetro recruiter_id."
        )

    @pytest.mark.asyncio
    async def test_pre_check_chama_log_check_ao_bloquear(self, mixin):
        """Quando bloqueado, log_check() deve ser chamado com company_id."""
        log_check_mock = AsyncMock()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_blocked(),
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            log_check_mock,
        ):
            result = await mixin._fairness_pre_check(
                "somente homens",
                company_id="co-789",
                recruiter_id="usr-000",
            )
            assert result is not None  # bloqueado

        await asyncio.sleep(0.05)
        log_check_mock.assert_called_once()
        kw = log_check_mock.call_args.kwargs
        assert kw.get("company_id") == "co-789"
        assert kw.get("context") == "test_domain"

    @pytest.mark.asyncio
    async def test_pre_check_backward_compat_sem_company_id(self, mixin):
        """Chamada legacy sem company_id ainda funciona corretamente."""
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_blocked(),
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            AsyncMock(),
        ):
            result = await mixin._fairness_pre_check("somente homens")
            assert result is not None

    @pytest.mark.asyncio
    async def test_pre_check_log_check_fail_open(self, mixin):
        """Erro em log_check não impede o retorno da mensagem educacional."""
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_blocked(),
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            side_effect=RuntimeError("DB down"),
        ):
            result = await mixin._fairness_pre_check(
                "somente homens",
                company_id="co-789",
            )
            assert result is not None  # mensagem educacional retornada mesmo com erro

    @pytest.mark.asyncio
    async def test_pre_check_input_limpo_nao_chama_log_check(self, mixin):
        """Input limpo: log_check NÃO deve ser chamado."""
        log_check_mock = AsyncMock()
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_clean(),
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            log_check_mock,
        ):
            result = await mixin._fairness_pre_check(
                "dev Python senior",
                company_id="co-789",
            )
            assert result is None

        await asyncio.sleep(0.05)
        log_check_mock.assert_not_called()


# ─── Fix C1: hiring_policy handler tem gate de fairness ──────────────────────

class TestHiringPolicyFairnessGate:
    """Fix C1: policy_chat handler deve bloquear antes de chamar PolicyReActAgent."""

    @pytest.mark.asyncio
    async def test_policy_chat_bloqueia_e_nao_chama_agente(self):
        """FairnessGuard bloqueia → HTTPException 400/422, agente não é chamado."""
        from fastapi import HTTPException
        from app.api.v1.hiring_policy import policy_chat

        agent_mock = AsyncMock()
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        payload = MagicMock()
        payload.message = "somente homens para esta vaga"
        payload.session_id = "s1"
        payload.conversation_history = []

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_blocked(),
        ), patch(
            "app.api.v1.hiring_policy.PolicyReActAgent",
            return_value=MagicMock(process_legacy_format=agent_mock),
        ), patch(
            "app.api.v1.hiring_policy.get_company_policy",
            new=AsyncMock(return_value={}),
        ), patch(
            "app.api.v1.hiring_policy.HiringPolicyRepository",
            return_value=MagicMock(
                fetch_conversation_history=AsyncMock(return_value=[])
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await policy_chat(
                    company_id="co-123",
                    payload=payload,
                    db=mock_db,
                    _company_gate="co-123",
                )

        assert exc_info.value.status_code in (400, 422)
        agent_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_policy_chat_input_limpo_chama_agente(self):
        """Input limpo → PolicyReActAgent é chamado normalmente."""
        from app.api.v1.hiring_policy import policy_chat

        agent_result = {"reply": "Ok.", "updated_fields": {}}
        agent_mock = AsyncMock(return_value=agent_result)
        mock_db = AsyncMock()

        payload = MagicMock()
        payload.message = "altere o prazo para 30 dias"
        payload.session_id = "s2"
        payload.conversation_history = []

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_clean(),
        ), patch(
            "app.api.v1.hiring_policy.PolicyReActAgent",
            return_value=MagicMock(process_legacy_format=agent_mock),
        ), patch(
            "app.api.v1.hiring_policy.get_company_policy",
            new=AsyncMock(return_value={}),
        ), patch(
            "app.api.v1.hiring_policy.HiringPolicyRepository",
            return_value=MagicMock(
                fetch_conversation_history=AsyncMock(return_value=[])
            ),
        ):
            # pode levantar outros erros (schema), mas não por fairness
            try:
                await policy_chat(
                    company_id="co-123",
                    payload=payload,
                    db=mock_db,
                    _company_gate="co-123",
                )
            except Exception as e:
                # aceitamos qualquer erro exceto 400 por fairness
                from fastapi import HTTPException
                if isinstance(e, HTTPException) and e.status_code == 400:
                    detail = getattr(e, "detail", "")
                    if "fairness" in str(detail).lower() or "discrimin" in str(detail).lower():
                        pytest.fail(f"Input limpo foi bloqueado por fairness: {e.detail}")

        agent_mock.assert_called_once()


# ─── Fix C2: pipeline_orchestrator handler tem gate de fairness ──────────────

class TestPipelineOrchestratorFairnessGate:
    """Fix C2: pipeline_orchestrate handler deve bloquear inputs discriminatórios."""

    @pytest.mark.asyncio
    async def test_pipeline_orchestrate_bloqueia_input_discriminatorio(self):
        from fastapi import HTTPException, Request
        from app.api.v1.pipeline_orchestrator import pipeline_react_orchestrate as pipeline_orchestrate

        agent_mock = AsyncMock()

        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = "usr-456"
        mock_request.state.company_id = "co-123"
        mock_request.json = AsyncMock(return_value={
            "message": "mover somente homens para triagem",
            "session_id": "s1",
            "context": {},
        })

        with patch.dict("os.environ", {"USE_REACT_AGENTS": "true"}), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_blocked(),
        ), patch(
            "app.api.v1.pipeline_orchestrator.PipelineReActAgent",
            return_value=MagicMock(process=agent_mock),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await pipeline_orchestrate(
                    request=mock_request,
                    company_id="co-123",
                )

        assert exc_info.value.status_code in (400, 422)
        agent_mock.assert_not_called()


# ─── Fix C3: task_planner handler tem gate de fairness ───────────────────────

class TestTaskPlannerFairnessGate:
    """Fix C3: decompose_task handler deve bloquear task_description discriminatória."""

    @pytest.mark.asyncio
    async def test_decompose_task_bloqueia_description_discriminatoria(self):
        from fastapi import HTTPException
        from app.api.v1.task_planner import decompose_task

        agent_mock = AsyncMock()
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "usr-1"

        request_payload = MagicMock()
        request_payload.task_description = "contratar somente homens para engenharia"
        request_payload.goal_id = None
        request_payload.parent_task_id = None
        request_payload.deadline = None
        request_payload.persist = False
        request_payload.additional_context = {}

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=_blocked(),
        ), patch(
            "app.api.v1.task_planner.AutomationReActAgent",
            return_value=MagicMock(decompose_task=agent_mock),
        ), patch(
            "app.api.v1.task_planner.get_user_company_id",
            return_value="co-123",
        ):
            with pytest.raises(HTTPException) as exc_info:
                await decompose_task(
                    request=request_payload,
                    db=mock_db,
                    current_user=mock_user,
                    company_id="co-123",
                )

        assert exc_info.value.status_code in (400, 422)
        agent_mock.assert_not_called()
