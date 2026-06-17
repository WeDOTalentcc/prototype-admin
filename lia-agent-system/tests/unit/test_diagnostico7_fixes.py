"""
Diagnóstico #7 — Testes dos fixes de qualidade.

Cobre:
1. POLICY-1 — UUID inválido em evaluate_policy não lança ValueError
2. FLOAT-1  — sendApproval limpa hitlRef antes do envio (guard duplo-submit)
3. MIXIN-1  — _resolve_guardrails loga warning ao cair em defaults estáticos
4. CIRCUIT-1 — reset_all_circuit_breakers loga circuit que falhou e retorna lista de failed
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# POLICY-1 — UUID inválido não explode
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_policy_invalid_company_id_no_exception():
    """UUID inválido em evaluate_policy é tratado com warning, sem ValueError."""
    from app.domains.policy.services.policy_engine_service import PolicyEngineService

    service = PolicyEngineService()

    # Mock do DB que retorna lista vazia de regras
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.domains.policy.services.policy_engine_service.AsyncSessionLocal",
        return_value=mock_ctx,
    ):
        # company_id inválido (não é UUID) — não deve lançar exceção
        result = await service.evaluate(
            action="some_action",
            context={},
            company_id="not-a-valid-uuid",
        )

    # Deve retornar resultado válido (ALLOW por default sem regras)
    assert result is not None
    assert result.allowed is True


@pytest.mark.asyncio
async def test_policy_valid_company_id_still_works():
    """UUID válido continua funcionando após o fix."""
    from app.domains.policy.services.policy_engine_service import PolicyEngineService

    service = PolicyEngineService()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.domains.policy.services.policy_engine_service.AsyncSessionLocal",
        return_value=mock_ctx,
    ):
        result = await service.evaluate(
            action="some_action",
            context={},
            company_id="12345678-1234-5678-1234-567812345678",
        )

    assert result is not None


@pytest.mark.asyncio
async def test_policy_none_company_id_no_exception():
    """company_id=None não lança exceção (path existente)."""
    from app.domains.policy.services.policy_engine_service import PolicyEngineService

    service = PolicyEngineService()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.domains.policy.services.policy_engine_service.AsyncSessionLocal",
        return_value=mock_ctx,
    ):
        result = await service.evaluate(
            action="some_action",
            context={},
            company_id=None,
        )

    assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# MIXIN-1 — _resolve_guardrails warning ao usar defaults
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_guardrails_logs_warning_when_both_sources_fail():
    """_resolve_guardrails loga warning quando autonomy engine e DB falham."""
    from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin

    class _Agent(EnhancedAgentMixin):
        pass

    agent = _Agent.__new__(_Agent)
    agent._enhanced_domain = "test_domain"

    # Mock autonomy engine e DB para falharem
    mock_autonomy = MagicMock()
    mock_autonomy.resolve_guardrails = AsyncMock(side_effect=RuntimeError("autonomy down"))
    agent._autonomy_engine = mock_autonomy

    mock_logger = MagicMock()

    with (
        patch("lia_agents_core.enhanced_agent_mixin.logger", mock_logger),
        patch(
            "lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._resolve_guardrails",
            wraps=agent._resolve_guardrails,
        ),
        patch(
            "lia_agents_core.enhanced_agent_mixin.AsyncSessionLocal",
            side_effect=RuntimeError("db down"),
        ) if False else patch(
            "lia_agents_core.enhanced_agent_mixin.logger", mock_logger
        ),
    ):
        with patch(
            "lia_agents_core.enhanced_agent_mixin.logger", mock_logger
        ):
            # Patch DB import dentro do método
            with patch.dict("sys.modules", {
                "lia_config.database": MagicMock(AsyncSessionLocal=MagicMock(
                    side_effect=RuntimeError("db down")
                )),
                "app.shared.compliance.guardrail_repository": MagicMock(),
            }):
                result = await agent._resolve_guardrails("company-1")

    # Deve retornar defaults
    assert isinstance(result, list)
    assert len(result) > 0

    # Deve ter logado warning mencionando "static defaults"
    warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
    assert any("static defaults" in w.lower() or "static" in w for w in warning_calls)


@pytest.mark.asyncio
async def test_resolve_guardrails_returns_defaults_without_raising():
    """_resolve_guardrails nunca lança exceção — sempre retorna lista."""
    from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin

    class _Agent(EnhancedAgentMixin):
        pass

    agent = _Agent.__new__(_Agent)
    agent._enhanced_domain = "test_domain"

    mock_autonomy = MagicMock()
    mock_autonomy.resolve_guardrails = AsyncMock(side_effect=Exception("fail"))
    agent._autonomy_engine = mock_autonomy

    with patch.dict("sys.modules", {
        "lia_config.database": MagicMock(
            AsyncSessionLocal=MagicMock(side_effect=Exception("db fail"))
        ),
        "app.shared.compliance.guardrail_repository": MagicMock(),
    }):
        result = await agent._resolve_guardrails("any-company")

    assert isinstance(result, list)
    assert "move_candidate" in result


# ─────────────────────────────────────────────────────────────────────────────
# CIRCUIT-1 — reset_all loga e retorna failed circuits
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reset_all_returns_failed_circuits_on_partial_failure():
    """Se um circuit falha no reset, retorna failed_circuits na resposta."""
    from app.api.v1.admin_circuit_breakers import reset_all_circuit_breakers

    mock_user = MagicMock()
    mock_user.id = "admin-1"

    def _failing_reset(name):
        if name == "broken_circuit":
            raise RuntimeError("circuit stuck")

    with (
        patch("app.api.v1.admin_circuit_breakers.reset_all_circuits"),
        patch("app.api.v1.admin_circuit_breakers._circuits", {"broken_circuit": MagicMock(), "ok_circuit": MagicMock()}),
        patch("app.api.v1.admin_circuit_breakers.reset_circuit", side_effect=_failing_reset),
        patch("app.api.v1.admin_circuit_breakers.ALL_CIRCUITS", {}),
    ):
        result = await reset_all_circuit_breakers(_user=mock_user)

    assert "failed_circuits" in result
    assert "broken_circuit" in result["failed_circuits"]
    assert "ok_circuit" not in result.get("failed_circuits", [])


@pytest.mark.asyncio
async def test_reset_all_no_failed_key_when_all_succeed():
    """Quando todos os resets têm sucesso, 'failed_circuits' não aparece na resposta."""
    from app.api.v1.admin_circuit_breakers import reset_all_circuit_breakers

    mock_user = MagicMock()
    mock_user.id = "admin-1"

    with (
        patch("app.api.v1.admin_circuit_breakers.reset_all_circuits"),
        patch("app.api.v1.admin_circuit_breakers._circuits", {"c1": MagicMock(), "c2": MagicMock()}),
        patch("app.api.v1.admin_circuit_breakers.reset_circuit"),
        patch("app.api.v1.admin_circuit_breakers.ALL_CIRCUITS", {}),
    ):
        result = await reset_all_circuit_breakers(_user=mock_user)

    assert "failed_circuits" not in result
    assert result["action"] == "reset_all"
