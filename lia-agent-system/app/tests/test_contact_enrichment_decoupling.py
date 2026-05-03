"""UC-P3-15: contact_enrichment → candidate_enrichment via port.

TDD-first tests that verify:
1. IEnrichmentPort is importable and has the expected abstract interface.
2. CandidateEnrichmentAdapter is a concrete implementation of IEnrichmentPort.
3. ContactEnrichmentService no longer imports CandidateEnrichmentService directly.
4. A mock port can be injected and its methods called correctly.
"""
from __future__ import annotations

import asyncio
import inspect


def test_enrichment_port_is_importable():
    """IEnrichmentPort and CandidateEnrichmentAdapter must be importable from the port module."""
    from app.domains.sourcing.ports.enrichment_port import (
        CandidateEnrichmentAdapter,
        IEnrichmentPort,
    )

    assert IEnrichmentPort is not None
    assert CandidateEnrichmentAdapter is not None


def test_enrichment_port_is_abstract():
    """IEnrichmentPort must be abstract (cannot be instantiated directly)."""
    from app.domains.sourcing.ports.enrichment_port import IEnrichmentPort
    import pytest

    with pytest.raises(TypeError):
        IEnrichmentPort()  # type: ignore[abstract]


def test_enrichment_port_has_required_methods():
    """IEnrichmentPort must declare enrich_candidate and scrape_profile."""
    from app.domains.sourcing.ports.enrichment_port import IEnrichmentPort

    abstract_methods = IEnrichmentPort.__abstractmethods__
    assert "enrich_candidate" in abstract_methods
    assert "scrape_profile" in abstract_methods


def test_candidate_enrichment_adapter_implements_port():
    """CandidateEnrichmentAdapter must be a subclass of IEnrichmentPort."""
    from app.domains.sourcing.ports.enrichment_port import (
        CandidateEnrichmentAdapter,
        IEnrichmentPort,
    )

    assert issubclass(CandidateEnrichmentAdapter, IEnrichmentPort)


def test_contact_enrichment_service_does_not_import_candidate_directly():
    """contact_enrichment_service must NOT import CandidateEnrichmentService directly.

    The only allowed cross-domain reference is through the port module.
    """
    import ast
    import pathlib

    src_path = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/domains/sourcing/services/contact_enrichment_service.py"
    )
    source = src_path.read_text()

    # Direct import of the concrete service should be gone
    assert "from app.domains.candidates.services.candidate_enrichment_service import" not in source, (
        "contact_enrichment_service still directly imports candidate_enrichment_service. "
        "Use IEnrichmentPort from the port module instead."
    )

    # Port import should be present
    assert "from app.domains.sourcing.ports.enrichment_port import" in source


def test_mock_enrichment_port_works():
    """A mock IEnrichmentPort can be injected and called without hitting Apify."""
    from app.domains.sourcing.ports.enrichment_port import IEnrichmentPort

    class MockEnrichmentPort(IEnrichmentPort):
        async def enrich_candidate(self, db, candidate_id, linkedin_url=None,
                                   include_experiences=True, include_education=True,
                                   include_email_discovery=True):
            return {"name": "Test Candidate", "email": "test@example.com", "success": True}

        async def scrape_profile(self, linkedin_url, actor="dev_fusion/Linkedin-Profile-Scraper"):
            return {"name": "Test Candidate", "emailAddress": "test@example.com"}

    port = MockEnrichmentPort()
    result = asyncio.run(port.enrich_candidate(None, "uuid-123", "co_1"))
    assert result["name"] == "Test Candidate"
    assert result["email"] == "test@example.com"

    raw = asyncio.run(port.scrape_profile("https://linkedin.com/in/test"))
    assert raw["emailAddress"] == "test@example.com"


def test_contact_enrichment_service_accepts_port_injection():
    """ContactEnrichmentService constructor must accept an IEnrichmentPort argument."""
    import inspect
    from app.domains.sourcing.ports.enrichment_port import IEnrichmentPort
    from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService

    sig = inspect.signature(ContactEnrichmentService.__init__)
    assert "enrichment_svc" in sig.parameters, "Constructor must have enrichment_svc parameter"

    annotation = sig.parameters["enrichment_svc"].annotation
    # Annotation could be string or actual type — just verify it mentions IEnrichmentPort
    ann_str = str(annotation)
    assert "IEnrichmentPort" in ann_str or "enrichment_port" in ann_str.lower(), (
        f"Parameter annotation should reference IEnrichmentPort, got: {ann_str}"
    )
