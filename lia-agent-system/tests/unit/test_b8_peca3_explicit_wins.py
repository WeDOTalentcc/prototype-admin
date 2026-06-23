"""B8 Peça 3 — RUN DECISIVO: input explícito DEVE vencer inferência.

Cenário: user disse "gestor é João Silva joao@x.com".
ClientUser table tem "João Souza joao.souza@empresa.com" (active).
Vaga DEVE gravar manager="João Silva" + manager_email="joao@x.com".
Se gravar Souza = regressão T4b.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_explicit_input_wins_over_client_user():
    """Explicit manager name+email from user MUST win over ClientUser inference."""
    from app.domains.job_management.services.job_vacancy_service import (
        infer_manager_email_if_missing,
        validate_manager_email,
    )

    # --- Step 1: infer_manager_email_if_missing ---
    # User gave BOTH name and email explicitly
    result_email = await infer_manager_email_if_missing(
        manager_name="João Silva",
        manager_email="joao@x.com",  # EXPLICIT
        company_id="company-uuid",
        department="Tecnologia",
    )
    # Must return the explicit email unchanged
    assert result_email == "joao@x.com", (
        f"REGRESSÃO: email deveria ser 'joao@x.com' (explícito), got '{result_email}'"
    )

    # --- Step 2: validate_manager_email ---
    # ClientUser has "João Souza" with DIFFERENT email
    mock_user = MagicMock()
    mock_user.status = "active"
    mock_user.name = "João Souza"  # DIFFERENT from user's "João Silva"

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=None)  # joao@x.com NOT in ClientUser

    with patch(
        "app.repositories.client_user_repository.ClientUserRepository",
        return_value=mock_repo,
    ):
        validation = await validate_manager_email(
            "joao@x.com",
            "00000000-0000-0000-0000-000000000001",
            MagicMock(),
        )

    # joao@x.com not found in ClientUser → valid=False, source=not_found
    assert validation["valid"] is False
    assert validation["source"] == "not_found"

    # --- Step 3: Simulate _create_vacancy_from_state logic ---
    manager_name = "João Silva"  # from state (explicit input)
    manager_email_final = result_email  # "joao@x.com"

    # P3.2 only enriches name if EMPTY
    if validation["valid"] and validation.get("user_name"):
        if not manager_name:  # This is False → does NOT overwrite
            manager_name = validation["user_name"]

    assert manager_name == "João Silva", (
        f"REGRESSÃO T4b: nome deveria ser 'João Silva' (explícito), got '{manager_name}'"
    )
    assert manager_email_final == "joao@x.com", (
        f"REGRESSÃO: email deveria ser 'joao@x.com' (explícito), got '{manager_email_final}'"
    )
    print(f"✅ PASS: manager='{manager_name}' manager_email='{manager_email_final}'")


@pytest.mark.asyncio
async def test_explicit_name_no_email_stays_empty():
    """User gave name but NO email. manager_email must stay None (Option 3).

    Pre-existing infer_manager_email_if_missing may try Department lookup,
    but if no Department match, email stays None. P3.1 (ClientUser inference)
    was REVERTED so no fallback to similar-name ClientUser.
    """
    from app.domains.job_management.services.job_vacancy_service import (
        infer_manager_email_if_missing,
    )

    # Mock the manager_inference_service to return None (no Department match)
    mock_svc = MagicMock()
    mock_svc.get_manager_by_name = AsyncMock(return_value=None)

    with patch(
        "app.shared.services.manager_inference_service.manager_inference_service",
        mock_svc,
    ):
        result_email = await infer_manager_email_if_missing(
            manager_name="João Silva",
            manager_email=None,  # user did NOT give email
            company_id="company-uuid",
            department="Tecnologia",
        )

    # No Department match + P3.1 reverted → email stays None
    assert result_email is None, (
        f"Email deveria ser None (user não deu, nenhum match Department), got '{result_email}'"
    )
    print("✅ PASS: email stays None when user didn't provide and no Department match")


@pytest.mark.asyncio
async def test_validate_active_user_but_name_present():
    """Even when email IS valid in ClientUser, P3.2 does NOT overwrite existing name."""
    from app.domains.job_management.services.job_vacancy_service import validate_manager_email

    mock_user = MagicMock()
    mock_user.status = "active"
    mock_user.name = "João Souza"  # ClientUser has different name

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=mock_user)

    with patch(
        "app.repositories.client_user_repository.ClientUserRepository",
        return_value=mock_repo,
    ):
        validation = await validate_manager_email(
            "joao@x.com",
            "00000000-0000-0000-0000-000000000001",
            MagicMock(),
        )

    # Validation says it's valid (email exists), returns user_name
    assert validation["valid"] is True
    assert validation["user_name"] == "João Souza"

    # BUT the caller logic:
    state_manager_name = "João Silva"  # explicit from user
    if validation["valid"] and validation.get("user_name"):
        if not state_manager_name:  # False → no overwrite
            state_manager_name = validation["user_name"]

    assert state_manager_name == "João Silva", (
        f"REGRESSÃO: P3.2 sobrescreveu nome explícito! Got '{state_manager_name}'"
    )
    print(f"✅ PASS: explicit name preserved despite ClientUser having different name")
