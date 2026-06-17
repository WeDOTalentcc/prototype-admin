"""
GAP-06-008 — Email Template Variable Validation (P1)

Tests:
  - test_extract_variables_from_template
  - test_extract_returns_empty_for_no_variables
  - test_extract_deduplicates_repeated_variables
  - test_missing_variable_returns_422
  - test_all_variables_provided_passes
  - test_extra_variables_allowed
  - test_validate_returns_sorted_missing_list
  - test_empty_template_has_no_required_variables
  - test_combined_subject_and_body_extraction
  - test_send_email_endpoint_raises_422_on_missing_variables (integration-style, mocked)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests for app.shared.template_validation
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractTemplateVariables:
    """Tests for extract_template_variables utility."""

    def test_extract_variables_from_template(self):
        """Standard case: extracts {{var}} names from a template."""
        from app.shared.template_validation import extract_template_variables

        result = extract_template_variables(
            "Olá {{candidate_name}}, você foi selecionado para {{job_title}}."
        )
        assert result == {"candidate_name", "job_title"}

    def test_extract_returns_empty_for_no_variables(self):
        """Template with no {{...}} returns empty set."""
        from app.shared.template_validation import extract_template_variables

        result = extract_template_variables("Sem variáveis aqui.")
        assert result == set()

    def test_extract_empty_string(self):
        """Empty string returns empty set."""
        from app.shared.template_validation import extract_template_variables

        assert extract_template_variables("") == set()

    def test_extract_deduplicates_repeated_variables(self):
        """Same variable used multiple times is returned once."""
        from app.shared.template_validation import extract_template_variables

        result = extract_template_variables(
            "{{candidate_name}} enviou currículo. Oi {{candidate_name}}!"
        )
        assert result == {"candidate_name"}

    def test_extract_combined_subject_and_body(self):
        """Variables from concatenated subject+body are all found."""
        from app.shared.template_validation import extract_template_variables

        combined = "Vaga {{job_title}} — {{company_name}} " + \
                   "<p>Caro {{candidate_name}}, salário: {{salary}}</p>"
        result = extract_template_variables(combined)
        assert result == {"job_title", "company_name", "candidate_name", "salary"}

    def test_extract_does_not_match_single_brace(self):
        """Single {brace} syntax is NOT a template variable."""
        from app.shared.template_validation import extract_template_variables

        result = extract_template_variables("{not_a_variable} but {{this_is}}")
        assert result == {"this_is"}


class TestValidateTemplateVariables:
    """Tests for validate_template_variables utility."""

    def test_all_variables_provided_passes(self):
        """Returns empty list when all required variables are provided."""
        from app.shared.template_validation import validate_template_variables

        missing = validate_template_variables(
            "Hello {{candidate_name}}, vaga: {{job_title}}",
            {"candidate_name": "Ana Lima", "job_title": "Engenheira Senior"},
        )
        assert missing == []

    def test_missing_variable_returns_list(self):
        """Returns list of missing variable names."""
        from app.shared.template_validation import validate_template_variables

        missing = validate_template_variables(
            "Hello {{candidate_name}}, vaga: {{job_title}}",
            {"candidate_name": "Ana Lima"},  # job_title missing
        )
        assert missing == ["job_title"]

    def test_multiple_missing_variables(self):
        """Returns all missing variables as sorted list."""
        from app.shared.template_validation import validate_template_variables

        missing = validate_template_variables(
            "{{candidate_name}} — {{job_title}} — {{company_name}}",
            {},  # nothing provided
        )
        assert missing == ["candidate_name", "company_name", "job_title"]  # sorted

    def test_extra_variables_allowed(self):
        """Extra variables in provided dict that are not in template are ignored."""
        from app.shared.template_validation import validate_template_variables

        missing = validate_template_variables(
            "Hello {{candidate_name}}",
            {
                "candidate_name": "Ana",
                "extra_unused_var": "ignored",
                "another_extra": "also ignored",
            },
        )
        assert missing == []

    def test_validate_returns_sorted_missing_list(self):
        """Missing variables are always returned in sorted order."""
        from app.shared.template_validation import validate_template_variables

        missing = validate_template_variables(
            "{{zzz}} {{aaa}} {{mmm}}",
            {},
        )
        assert missing == ["aaa", "mmm", "zzz"]

    def test_empty_template_has_no_required_variables(self):
        """Empty template requires nothing."""
        from app.shared.template_validation import validate_template_variables

        missing = validate_template_variables("", {"any_var": "value"})
        assert missing == []


# ─────────────────────────────────────────────────────────────────────────────
# Integration-style test for the send_email endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestSendEmailEndpointVariableValidation:
    """Tests that the send_email endpoint returns 422 for missing variables."""

    @pytest.mark.asyncio
    async def test_send_email_raises_422_on_missing_variables(self):
        """send_email returns HTTP 422 with structured error when template variables missing."""
        from fastapi import HTTPException

        # Build a mock template with {{candidate_name}} and {{job_title}}
        mock_template = MagicMock()
        mock_template.subject = "Olá {{candidate_name}}"
        mock_template.body_html = "<p>Você foi selecionado para {{job_title}}.</p>"
        mock_template.body_text = None

        # Build a mock email log (returned when send would succeed)
        mock_log = MagicMock()
        mock_log.id = uuid4()
        mock_log.status = "sent"
        mock_log.recipient_email = "test@example.com"
        mock_log.subject = "Olá Ana"
        mock_log.error_message = None

        with (
            patch(
                "app.repositories.email_templates_repository.EmailTemplatesRepository.get_by_id_for_company",
                new_callable=AsyncMock,
                return_value=mock_template,
            ),
            patch(
                "app.api.v1.email_templates.check_email_rate_limit",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "app.api.v1.email_templates.validate_recipient_is_known_candidate",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "app.domains.communication.services.email_service.EmailService.send_email",
                new_callable=AsyncMock,
                return_value=mock_log,
            ) as mock_send,
        ):
            from app.api.v1.email_templates import send_email
            from app.schemas.email_template import EmailSendRequest
            from app.auth.models import User

            mock_user = MagicMock(spec=User)
            mock_user.id = uuid4()

            mock_repo = MagicMock()
            mock_repo.db = AsyncMock()
            mock_repo.get_by_id_for_company = AsyncMock(return_value=mock_template)

            mock_email_svc = MagicMock()
            mock_email_svc.send_email = AsyncMock(return_value=mock_log)

            request = EmailSendRequest(
                recipient_email="test@example.com",
                variables={},  # missing candidate_name and job_title
            )

            with pytest.raises(HTTPException) as exc_info:
                await send_email(
                    template_id=str(uuid4()),
                    request=request,
                    current_user=mock_user,
                    repo=mock_repo,
                    email_svc=mock_email_svc,
                    company_id=str(uuid4()),
                )

            assert exc_info.value.status_code == 422
            detail = exc_info.value.detail
            assert detail["error"] == "missing_template_variables"
            assert "candidate_name" in detail["missing"]
            assert "job_title" in detail["missing"]
            assert "candidate_name" in detail["required"]
            assert "job_title" in detail["required"]
            # email_svc.send_email must NOT have been called (fail before side effect)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_passes_when_all_variables_provided(self):
        """send_email proceeds when all required template variables are provided."""
        from fastapi import HTTPException

        mock_template = MagicMock()
        mock_template.subject = "Olá {{candidate_name}}"
        mock_template.body_html = "<p>Vaga: {{job_title}}</p>"
        mock_template.body_text = None

        mock_log = MagicMock()
        mock_log.id = uuid4()
        mock_log.status = "sent"
        mock_log.recipient_email = "test@example.com"
        mock_log.subject = "Olá Ana"
        mock_log.error_message = None

        from app.schemas.email_template import EmailSendRequest
        from app.auth.models import User

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_repo = MagicMock()
        mock_repo.db = AsyncMock()
        mock_repo.get_by_id_for_company = AsyncMock(return_value=mock_template)

        mock_email_svc = MagicMock()
        mock_email_svc.send_email = AsyncMock(return_value=mock_log)

        with (
            patch(
                "app.api.v1.email_templates.check_email_rate_limit",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "app.api.v1.email_templates.validate_recipient_is_known_candidate",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            from app.api.v1.email_templates import send_email

            request = EmailSendRequest(
                recipient_email="test@example.com",
                variables={
                    "candidate_name": "Ana Lima",
                    "job_title": "Engenheira Senior",
                },
            )

            # Should not raise
            response = await send_email(
                template_id=str(uuid4()),
                request=request,
                current_user=mock_user,
                repo=mock_repo,
                email_svc=mock_email_svc,
                company_id=str(uuid4()),
            )

            assert response.success is True
            mock_email_svc.send_email.assert_called_once()
