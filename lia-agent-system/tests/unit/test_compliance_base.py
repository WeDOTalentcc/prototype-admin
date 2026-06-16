"""
Tests for LIA-C01: ComplianceDomainPrompt

Tests:
    - test_compliance_domain_prompt_is_abstract
    - test_new_domain_inheriting_compliance_gets_fairness
    - test_new_domain_inheriting_compliance_gets_pii_strip
    - test_domain_prompt_generates_warning_in_workflow
    - test_compliance_domain_prompt_subclass_accepted
    - test_pre_process_blocks_discriminatory_query
"""
import pytest
import logging
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.base import (
    DomainAction,
    DomainContext,
    DomainPrompt,
    DomainResponse,
    IntentResult,
)
from app.domains.compliance_base import ComplianceDomainPrompt


# ---------------------------------------------------------------------------
# Concrete test subclasses
# ---------------------------------------------------------------------------

class _MinimalComplianceDomain(ComplianceDomainPrompt):
    """Minimal concrete subclass for testing."""

    domain_id = "test_compliance"
    domain_name = "Test Compliance Domain"

    def get_allowed_actions(self) -> List[DomainAction]:
        return [
            DomainAction(
                action_id="noop",
                name="No-op",
                description="Does nothing",
            )
        ]

    def get_system_prompt(self) -> str:
        return "You are a test assistant."

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        return IntentResult(
            intent_id="test.noop",
            action_id="noop",
            confidence=0.9,
            reasoning="test",
        )

    async def execute_action(
        self, action_id: str, params: Dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        return DomainResponse.success_response("OK")


class _MinimalDomainPrompt(DomainPrompt):
    """Concrete DomainPrompt (NOT inheriting ComplianceDomainPrompt) for testing."""

    domain_id = "test_plain"
    domain_name = "Plain Domain"

    def get_allowed_actions(self) -> List[DomainAction]:
        return []

    def get_system_prompt(self) -> str:
        return "Plain system prompt."

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        return IntentResult(
            intent_id="plain.noop",
            action_id="noop",
            confidence=0.9,
        )

    async def execute_action(
        self, action_id: str, params: Dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        return DomainResponse.success_response("OK")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def domain_context() -> DomainContext:
    return DomainContext(
        domain_id="test",
        user_id="user-001",
        session_id="sess-001",
        tenant_id="tenant-001",
    )


@pytest.fixture
def compliance_domain() -> _MinimalComplianceDomain:
    return _MinimalComplianceDomain()


@pytest.fixture
def plain_domain() -> _MinimalDomainPrompt:
    return _MinimalDomainPrompt()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestComplianceDomainPromptAbstract:
    """LIA-C01: ComplianceDomainPrompt must be abstract."""

    def test_compliance_domain_prompt_is_abstract(self):
        """ComplianceDomainPrompt cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ComplianceDomainPrompt()  # type: ignore[abstract]

    def test_compliance_subclass_can_be_instantiated(self, compliance_domain):
        """Concrete subclass can be instantiated."""
        assert isinstance(compliance_domain, ComplianceDomainPrompt)
        assert isinstance(compliance_domain, DomainPrompt)


class TestComplianceConfig:
    """LIA-C01: compliance_config and get_required_prompt_blocks."""

    def test_default_compliance_config(self, compliance_domain):
        config = compliance_domain.get_compliance_config()
        assert config["fairness_guard_enabled"] is True
        assert config["pii_strip_enabled"] is True
        assert config["prompt_injection_guard_enabled"] is True
        assert config["fact_checker_enabled"] is True
        assert config["high_impact"] is False

    def test_custom_compliance_config_override(self):
        class _HighImpactDomain(_MinimalComplianceDomain):
            domain_id = "high_impact_domain"
            _compliance_config = {
                "high_impact": True,
                "fairness_action_type": "rejection",
            }

        d = _HighImpactDomain()
        config = d.get_compliance_config()
        assert config["high_impact"] is True
        assert config["fairness_action_type"] == "rejection"
        # Defaults still present
        assert config["fairness_guard_enabled"] is True

    def test_get_required_prompt_blocks(self, compliance_domain):
        blocks = compliance_domain.get_required_prompt_blocks()
        assert "LGPD_COMPLIANCE" in blocks
        assert "NON_DISCRIMINATION" in blocks
        assert "DATA_MINIMIZATION" in blocks


class TestFairnessGuardIntegration:
    """LIA-C01: FairnessGuard called during pre_process."""

    @pytest.mark.asyncio
    async def test_new_domain_inheriting_compliance_gets_fairness(
        self, compliance_domain, domain_context
    ):
        """pre_process calls FairnessGuard.check for non-high_impact domains."""
        mock_result = MagicMock()
        mock_result.is_blocked = False
        mock_result.soft_warnings = []

        with patch(
            "app.domains.compliance_base.ComplianceDomainPrompt._run_fairness_guard",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_fairness:
            result = await compliance_domain.pre_process("quero candidatos python", domain_context)

        mock_fairness.assert_called_once_with("quero candidatos python", domain_context, None)
        assert result is None  # Not blocked

    @pytest.mark.asyncio
    async def test_pre_process_blocks_discriminatory_query(
        self, compliance_domain, domain_context
    ):
        """pre_process returns DomainResponse when FairnessGuard blocks."""
        blocked_response = DomainResponse(
            success=False,
            message="Discriminação por gênero não permitida.",
            metadata={"blocked_by": "fairness_guard"},
        )

        with patch(
            "app.domains.compliance_base.ComplianceDomainPrompt._run_fairness_guard",
            new_callable=AsyncMock,
            return_value=blocked_response,
        ):
            result = await compliance_domain.pre_process(
                "quero apenas homens para a vaga", domain_context
            )

        assert result is not None
        assert result.success is False
        assert "blocked_by" in result.metadata
        assert result.metadata["blocked_by"] == "fairness_guard"

    @pytest.mark.asyncio
    async def test_fairness_guard_called_with_real_discriminatory_query(
        self, compliance_domain, domain_context
    ):
        """Integration: real FairnessGuard blocks gender-discriminatory query."""
        mock_fair_result = MagicMock()
        mock_fair_result.is_blocked = True
        mock_fair_result.blocked_terms = ["apenas homens"]
        mock_fair_result.category = "genero"
        mock_fair_result.educational_message = "Discriminação por gênero não é permitida."
        mock_fair_result.confidence = 0.9
        mock_fair_result.original_query = "apenas homens"
        mock_fair_result.soft_warnings = []

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check.return_value = mock_fair_result

            result = await compliance_domain.pre_process(
                "apenas homens", domain_context
            )

        assert result is not None
        assert result.success is False
        assert result.metadata.get("blocked_by") == "fairness_guard"


class TestPIIStrip:
    """LIA-C01: PII Strip called during pre_process."""

    @pytest.mark.asyncio
    async def test_new_domain_inheriting_compliance_gets_pii_strip(
        self, compliance_domain, domain_context
    ):
        """pre_process calls _strip_pii and stores stripped query in context."""
        original_query = "candidato joao@email.com com CPF 123.456.789-00"
        stripped_query = "candidato [EMAIL REMOVIDO] com CPF [CPF REMOVIDO]"

        with patch(
            "app.domains.compliance_base.ComplianceDomainPrompt._run_fairness_guard",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.domains.compliance_base.ComplianceDomainPrompt._strip_pii",
                return_value=stripped_query,
            ) as mock_strip:
                with patch(
                    "app.domains.compliance_base.ComplianceDomainPrompt._check_prompt_injection",
                    new_callable=AsyncMock,
                    return_value=None,
                ):
                    await compliance_domain.pre_process(original_query, domain_context)

        mock_strip.assert_called_once_with(original_query)

    @pytest.mark.asyncio
    async def test_pii_strip_stores_stripped_query_in_context(
        self, compliance_domain, domain_context
    ):
        """When PII is stripped, context.metadata is updated."""
        original = "email: test@test.com"
        stripped = "email: [EMAIL REMOVIDO]"

        with patch(
            "app.domains.compliance_base.ComplianceDomainPrompt._run_fairness_guard",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(compliance_domain, "_strip_pii", return_value=stripped):
                with patch(
                    "app.domains.compliance_base.ComplianceDomainPrompt._check_prompt_injection",
                    new_callable=AsyncMock,
                    return_value=None,
                ):
                    await compliance_domain.pre_process(original, domain_context)

        assert domain_context.metadata.get("pii_was_stripped") is True
        assert domain_context.metadata.get("pii_stripped_query") == stripped

    def test_strip_pii_delegates_to_pii_masking(self, compliance_domain):
        """_strip_pii calls strip_pii_for_llm_prompt."""
        text = "candidato com CPF 123.456.789-00"
        with patch("app.shared.pii_masking.strip_pii_for_llm_prompt") as mock_strip:
            mock_strip.return_value = "candidato com CPF [CPF REMOVIDO]"
            result = compliance_domain._strip_pii(text)

        mock_strip.assert_called_once_with(text)
        assert result == "candidato com CPF [CPF REMOVIDO]"

    def test_strip_pii_fail_safe(self, compliance_domain):
        """_strip_pii returns original text on import error."""
        text = "some text"
        with patch(
            "app.shared.pii_masking.strip_pii_for_llm_prompt",
            side_effect=ImportError("not available"),
        ):
            result = compliance_domain._strip_pii(text)

        assert result == text


class TestWorkflowComplianceIntegration:
    """LIA-C02: DomainWorkflow emits warning for plain DomainPrompt domains."""

    @pytest.mark.asyncio
    async def test_domain_prompt_generates_warning_in_workflow(
        self, plain_domain, domain_context, caplog
    ):
        """DomainPrompt (non-compliance) generates a warning log in DomainWorkflow."""
        from app.domains.workflow import DomainWorkflow

        workflow = DomainWorkflow(
            enable_fairness_guard=False,
            enable_fact_checker=False,
            enable_learning_loop=False,
        )

        with patch.object(
            plain_domain,
            "process_intent",
            new_callable=AsyncMock,
            return_value=IntentResult(
                intent_id="plain.noop",
                action_id="noop",
                confidence=0.9,
            ),
        ):
            with patch.object(
                plain_domain,
                "execute_action",
                new_callable=AsyncMock,
                return_value=DomainResponse.success_response("OK"),
            ):
                with caplog.at_level(logging.WARNING, logger="app.domains.workflow"):
                    response = await workflow.process(
                        plain_domain, domain_context, "test query"
                    )

        # Warning should be emitted for non-compliance domain
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("LIA-C02" in msg or "ComplianceDomainPrompt" in msg for msg in warning_messages), (
            f"Expected LIA-C02 warning not found. Got: {warning_messages}"
        )

    @pytest.mark.asyncio
    async def test_compliance_domain_prompt_subclass_accepted(
        self, compliance_domain, domain_context, caplog
    ):
        """ComplianceDomainPrompt subclass does NOT generate LIA-C02 warning."""
        from app.domains.workflow import DomainWorkflow

        workflow = DomainWorkflow(
            enable_fairness_guard=False,
            enable_fact_checker=False,
            enable_learning_loop=False,
        )

        with patch.object(
            compliance_domain,
            "process_intent",
            new_callable=AsyncMock,
            return_value=IntentResult(
                intent_id="test.noop",
                action_id="noop",
                confidence=0.9,
            ),
        ):
            with patch.object(
                compliance_domain,
                "execute_action",
                new_callable=AsyncMock,
                return_value=DomainResponse.success_response("OK"),
            ):
                with patch.object(
                    compliance_domain,
                    "pre_process",
                    new_callable=AsyncMock,
                    return_value=None,
                ):
                    with patch.object(
                        compliance_domain,
                        "post_process",
                        new_callable=AsyncMock,
                        side_effect=lambda r, c: r,
                    ):
                        with caplog.at_level(logging.WARNING, logger="app.domains.workflow"):
                            response = await workflow.process(
                                compliance_domain, domain_context, "test query"
                            )

        # No LIA-C02 warning for compliant domains
        lia_c02_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "LIA-C02" in r.message
        ]
        assert len(lia_c02_warnings) == 0, (
            f"Unexpected LIA-C02 warning for compliance domain: {[r.message for r in lia_c02_warnings]}"
        )


class TestRepr:
    """__repr__ format tests."""

    def test_repr_includes_domain_id_and_compliance(self, compliance_domain):
        r = repr(compliance_domain)
        assert "test_compliance" in r
        assert "compliance=True" in r
