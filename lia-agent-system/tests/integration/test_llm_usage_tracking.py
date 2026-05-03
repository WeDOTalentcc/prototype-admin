"""R-002 — track_llm_usage_start helper + wiring no caller exemplar wsi/_shared.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-205 / R-002 (helper canonical + 1 caller exemplar).

Os outros 8+ callers de get_provider_for_tenant() ficam como debito Sprint 2:
  - app/api/v1/wsi/reports.py
  - app/api/v1/candidate_search/archetypes.py (2 callers)
  - app/api/v1/internal_llm.py
  - app/api/v1/email_templates.py (2 callers)
  - app/api/v1/experience_highlights.py
  - app/api/v1/interviews.py (2 callers)
  - app/api/v1/lia_profile_analysis.py
  - ... (ver grep "get_provider_for_tenant" no codebase)
"""

from __future__ import annotations

import inspect
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WSI_SHARED = REPO_ROOT / "app" / "api" / "v1" / "wsi" / "_shared.py"
TOKEN_BUDGET = REPO_ROOT / "app" / "domains" / "credits" / "services" / "token_budget_service.py"


def test_track_llm_usage_start_helper_exists() -> None:
    """R-002: helper canonical track_llm_usage_start deve existir em token_budget_service."""
    src = TOKEN_BUDGET.read_text(encoding="utf-8")
    assert "def track_llm_usage_start(" in src, (
        "R-002: token_budget_service.py precisa expor track_llm_usage_start(...). "
        "Ver criterio de aceite F-205 — helper canonical para todos callers de "
        "get_provider_for_tenant antes do .complete() / .invoke()."
    )


def test_track_llm_usage_start_signature_has_required_kwargs() -> None:
    """R-002: assinatura precisa aceitar company_id + model + domain + operation."""
    from app.domains.credits.services.token_budget_service import track_llm_usage_start

    sig = inspect.signature(track_llm_usage_start)
    params = sig.parameters
    assert "company_id" in params, "R-002: track_llm_usage_start precisa receber company_id"
    assert "model" in params, "R-002: track_llm_usage_start precisa receber model (kwarg)"
    assert "domain" in params, "R-002: track_llm_usage_start precisa receber domain (kwarg)"
    assert "operation" in params, "R-002: track_llm_usage_start precisa receber operation (kwarg)"


def test_track_llm_usage_start_returns_metadata_dict() -> None:
    """R-002: helper retorna dict de correlacao com tenant_id/model/domain/operation/started_at."""
    from app.domains.credits.services.token_budget_service import track_llm_usage_start

    payload = track_llm_usage_start(
        "company-123",
        model="claude-3-5-sonnet",
        domain="wsi.report",
        operation="cbi_questions",
    )
    assert isinstance(payload, dict)
    for key in ("tenant_id", "model", "domain", "operation", "started_at"):
        assert key in payload, f"R-002: payload precisa conter '{key}'"
    assert payload["tenant_id"] == "company-123"
    assert payload["domain"] == "wsi.report"


def test_track_llm_usage_start_tolerates_none_company_id() -> None:
    """R-002: paths sinteticos (skills_ontology singleton, etc.) podem ter company_id None."""
    from app.domains.credits.services.token_budget_service import track_llm_usage_start

    payload = track_llm_usage_start(None, model="text-embedding-004", domain="ontology")
    assert payload["tenant_id"] == "unknown"


def test_wsi_shared_get_anthropic_client_calls_tracker() -> None:
    """R-002: caller exemplar wsi/_shared.get_anthropic_client invoca track_llm_usage_start."""
    src = WSI_SHARED.read_text(encoding="utf-8")
    assert "track_llm_usage_start" in src, (
        "R-002: wsi/_shared.py precisa importar e chamar track_llm_usage_start "
        "antes de get_provider_for_tenant() — pattern canonical."
    )


def test_wsi_shared_imports_helper_from_canonical_path() -> None:
    """R-002: import deve vir de token_budget_service (path canonical, nao copia local)."""
    src = WSI_SHARED.read_text(encoding="utf-8")
    assert "from app.domains.credits.services.token_budget_service import track_llm_usage_start" in src, (
        "R-002: import canonical 'from app.domains.credits.services.token_budget_service "
        "import track_llm_usage_start' nao encontrado em wsi/_shared.py."
    )
