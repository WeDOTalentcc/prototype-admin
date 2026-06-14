__domain_type__ = "agentic"  # ADR-031 §6.1
"""
Job Creation Domain — Conversational wizard for creating jobs with WSI methodology.

Registers the JobCreationDomain with the domain registry on import.
"""

from app.domains.job_creation.domain import JobCreationDomain

__all__ = ["JobCreationDomain"]
