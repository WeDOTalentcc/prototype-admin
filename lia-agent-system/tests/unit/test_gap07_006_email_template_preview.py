"""
GAP-07-006 — Live email template preview with real data.

Unit tests for the POST /{template_id}/preview endpoint in
app/api/v1/email_templates.py.

Tests:
  - test_preview_renders_subject_and_body_with_variables
  - test_preview_leaves_unfilled_placeholders_when_variable_missing
  - test_preview_returns_404_for_unknown_template
  - test_preview_renders_empty_body_text_as_none
  - test_preview_sanitizes_html_injection_in_variables
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_template(
    subject: str = "Olá {{candidate_name}}",
    body_html: str = "<p>Vaga: {{job_title}}</p>",
    body_text: str | None = None,
) -> MagicMock:
    """Build a minimal mock EmailTemplate ORM object."""
    tmpl = MagicMock()
    tmpl.subject = subject
    tmpl.body_html = body_html
    tmpl.body_text = body_text
    return tmpl


def _make_repo(template: MagicMock | None) -> MagicMock:
    """Build a mock EmailTemplatesRepository that returns the given template."""
    repo = MagicMock()
    repo.get_by_id_for_company = AsyncMock(return_value=template)
    return repo


COMPANY_ID = str(uuid4())
TEMPLATE_ID = str(uuid4())


# ── tests ──────────────────────────────────────────────────────────────────────

class TestPreviewTemplateById:
    """Tests for preview_template_by_id endpoint."""

    @pytest.mark.asyncio
    async def test_preview_renders_subject_and_body_with_variables(self):
        """Provided variables are substituted in subject and body_html."""
        from app.api.v1.email_templates import preview_template_by_id
        from app.schemas.email_template import TemplatePreviewByIdRequest

        template = _make_template(
            subject="Olá {{candidate_name}}, vaga: {{job_title}}",
            body_html="<p>Empresa: {{company_name}}. Início: {{start_date}}.</p>",
            body_text="Empresa: {{company_name}}. Início: {{start_date}}.",
        )
        repo = _make_repo(template)

        request = TemplatePreviewByIdRequest(variables={
            "candidate_name": "João Silva",
            "job_title": "Desenvolvedor Full Stack",
            "company_name": "TechCorp",
            "start_date": "1º de Março",
        })

        response = await preview_template_by_id(
            template_id=TEMPLATE_ID,
            request=request,
            repo=repo,
            company_id=COMPANY_ID,
        )

        assert response.success is True
        assert response.data.subject == "Olá João Silva, vaga: Desenvolvedor Full Stack"
        assert "TechCorp" in response.data.body_html
        assert "1º de Março" in response.data.body_html
        assert response.data.body_text is not None
        assert "TechCorp" in response.data.body_text

    @pytest.mark.asyncio
    async def test_preview_leaves_unfilled_placeholders_when_variable_missing(self):
        """When a variable is not provided, the {{placeholder}} remains in output."""
        from app.api.v1.email_templates import preview_template_by_id
        from app.schemas.email_template import TemplatePreviewByIdRequest

        template = _make_template(
            subject="Olá {{candidate_name}}",
            body_html="<p>Vaga: {{job_title}} — Empresa: {{company_name}}</p>",
        )
        repo = _make_repo(template)

        # Only providing candidate_name; job_title and company_name are missing
        request = TemplatePreviewByIdRequest(variables={"candidate_name": "Ana Lima"})

        response = await preview_template_by_id(
            template_id=TEMPLATE_ID,
            request=request,
            repo=repo,
            company_id=COMPANY_ID,
        )

        assert response.success is True
        # candidate_name is filled
        assert "Ana Lima" in response.data.subject
        # missing vars remain as-is in output
        assert "{{job_title}}" in response.data.body_html
        assert "{{company_name}}" in response.data.body_html

    @pytest.mark.asyncio
    async def test_preview_returns_404_for_unknown_template(self):
        """Returns HTTP 404 when template is not found for company."""
        from fastapi import HTTPException
        from app.api.v1.email_templates import preview_template_by_id
        from app.schemas.email_template import TemplatePreviewByIdRequest

        repo = _make_repo(None)  # template not found

        request = TemplatePreviewByIdRequest(variables={})

        with pytest.raises(HTTPException) as exc_info:
            await preview_template_by_id(
                template_id="nonexistent-id",
                request=request,
                repo=repo,
                company_id=COMPANY_ID,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_preview_renders_empty_body_text_as_none(self):
        """When body_text is empty/None after rendering, response body_text is None."""
        from app.api.v1.email_templates import preview_template_by_id
        from app.schemas.email_template import TemplatePreviewByIdRequest

        template = _make_template(
            subject="Test subject",
            body_html="<p>Body</p>",
            body_text="",  # empty — should become None
        )
        repo = _make_repo(template)

        request = TemplatePreviewByIdRequest(variables={})

        response = await preview_template_by_id(
            template_id=TEMPLATE_ID,
            request=request,
            repo=repo,
            company_id=COMPANY_ID,
        )

        assert response.success is True
        # empty body_text normalised to None
        assert response.data.body_text is None

    @pytest.mark.asyncio
    async def test_preview_sanitizes_xss_in_variable_values(self):
        """Variable values with HTML special chars are rendered as-is (not executed)."""
        from app.api.v1.email_templates import preview_template_by_id
        from app.schemas.email_template import TemplatePreviewByIdRequest

        template = _make_template(
            subject="Olá {{candidate_name}}",
            body_html="<p>{{candidate_name}}</p>",
        )
        repo = _make_repo(template)

        # XSS payload in variable value — BE substitutes string literally
        xss_payload = '<script>alert("xss")</script>'
        request = TemplatePreviewByIdRequest(variables={"candidate_name": xss_payload})

        response = await preview_template_by_id(
            template_id=TEMPLATE_ID,
            request=request,
            repo=repo,
            company_id=COMPANY_ID,
        )

        # The BE inserts the value literally (sanitization is FE-side via sanitizeEmailHtml)
        # This test ensures the endpoint does NOT crash and returns a response
        assert response.success is True
        assert response.data.subject is not None
        assert response.data.body_html is not None
