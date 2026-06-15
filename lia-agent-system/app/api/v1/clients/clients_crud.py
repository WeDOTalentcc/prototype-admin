"""
Client CRUD endpoints: list, get, create, update, status, delete, and status-options.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ._shared import (
    CLIENT_STATUS_OPTIONS,
    COMPANY_SIZE_OPTIONS,
    ClientAccountRepository,
    ClientCreate,
    ClientStatus,
    ClientUpdate,
    EmailService,
    StatusUpdate,
    _get_client_checked,
    clone_templates_for_client,
    get_client_repo,
    get_email_service,
    get_user_from_headers,
    hubspot_service,
    logger,
    provision_workos_organization,
    sync_client_to_hubspot,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter()


@router.get("/status-options", summary="List available status options", response_model=None)
async def list_status_options(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all available client status options."""
    return {
        "success": True,
        "data": {
            "statuses": CLIENT_STATUS_OPTIONS,
            "company_sizes": COMPANY_SIZE_OPTIONS,
        },
    }


@router.get("", summary="List clients", response_model=None)
async def list_clients(
    status: str | None = Query(None),
    plan_id: str | None = Query(None),
    search: str | None = Query(None),
    industry: str | None = Query(None),
    company_size: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all clients with optional filters."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        company_id_filter = None if is_admin else current_user.get("company_id")
        clients = await repo.list_all(
            status=status, plan_id=plan_id, search=search,
            industry=industry, company_size=company_size,
            company_id=company_id_filter, limit=limit, offset=offset,
        )
        total = await repo.count_all(
            status=status, plan_id=plan_id, search=search,
            industry=industry, company_size=company_size, company_id=company_id_filter,
        )
        logger.info(f"Listed {len(clients)} clients (total: {total})")
        return {
            "success": True,
            "data": {"clients": [c.to_dict() for c in clients], "total": total, "limit": limit, "offset": offset},
        }
    except Exception as e:
        logger.error(f"Error listing clients: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR if not isinstance(status, str) else 500,
            detail=f"Failed to list clients: {str(e)}",
        )


@router.get("/{client_id}", summary="Get client by ID", response_model=None)
async def get_client(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific client by ID."""
    try:
        client = await _get_client_checked(client_id, current_user, repo)
        return {"success": True, "data": client.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{client_id}/stats", summary="Get client statistics", response_model=None)
async def get_client_stats(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get statistics for a specific client."""
    try:
        client = await _get_client_checked(client_id, current_user, repo)
        stats = {
            "client_id": str(client.id),
            "name": client.name,
            "status": client.status,
            "limits": {
                "user_limit": client.user_limit,
                "job_limit": client.job_limit,
                "ai_credits_monthly": client.ai_credits_monthly,
            },
            "usage": {
                "users_count": 0, "active_jobs_count": 0, "total_jobs_count": 0,
                "candidates_count": 0, "ai_credits_used": 0,
            },
            "utilization": {
                "users_percentage": 0, "jobs_percentage": 0, "ai_credits_percentage": 0,
            },
        }
        return {"success": True, "data": stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", status_code=201, summary="Create client", response_model=None)
async def create_client(
    data: ClientCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
    email_svc: EmailService = Depends(get_email_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new client. Only admin users can create new clients."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can create clients")

        valid_statuses = [s.value for s in ClientStatus]
        if data.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        if data.cnpj:
            existing = await repo.get_by_cnpj(data.cnpj)
            if existing:
                raise HTTPException(status_code=409, detail=f"Client with CNPJ {data.cnpj} already exists")

        client_data = {
            "name": data.name, "trade_name": data.trade_name, "cnpj": data.cnpj,
            "primary_email": data.primary_email, "primary_phone": data.primary_phone,
            "website": data.website,
            "address": data.address.model_dump() if data.address else None,
            "status": data.status, "plan_id": data.plan_id,
            "contract_start_date": data.contract_start_date,
            "contract_end_date": data.contract_end_date,
            "user_limit": data.user_limit, "job_limit": data.job_limit,
            "ai_credits_monthly": data.ai_credits_monthly,
            "settings": data.settings or {}, "features_enabled": data.features_enabled or [],
            "account_manager_id": data.account_manager_id,
            "implementation_manager_id": data.implementation_manager_id,
            "logo_url": data.logo_url, "industry": data.industry, "company_size": data.company_size,
        }

        try:
            client = await repo.create(client_data)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail="Internal server error")

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created client: {client.name} (ID: {client.id})")

        organization_id = await provision_workos_organization(client, repo.db)

        try:
            cloned_count = await clone_templates_for_client(repo.db, str(client.id))
            logger.info(f"Cloned {cloned_count} system templates for client {client.id}")
        except Exception as template_error:
            logger.warning(f"Failed to clone templates for client {client.id}: {template_error}")

        email_sent = False
        if client.primary_email:
            try:
                import os
                base_url = os.getenv("FRONTEND_URL", "https://app.wedotalent.com")
                email_sent = await email_svc.send_welcome_email(
                    client=client, admin_portal_url=f"{base_url}/login", db=repo.db
                )
                if email_sent:
                    # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
                    logger.info(f"Welcome email sent to {client.primary_email}")
                else:
                    # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
                    logger.warning(f"Failed to send welcome email to {client.primary_email}")
            except Exception as email_error:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.warning(f"Error sending welcome email: {email_error}")

        hubspot_result = None
        try:
            hubspot_result = await sync_client_to_hubspot(client, repo.db)
            if hubspot_result.get("success"):
                logger.info(f"Synced client {client.id} to HubSpot")
            else:
                logger.warning(f"HubSpot sync skipped or failed: {hubspot_result.get('error')}")
        except Exception as hubspot_error:
            logger.warning(f"Error syncing to HubSpot: {hubspot_error}")

        response_data = client.to_dict()
        response_data["organization_id"] = organization_id
        response_data["email_sent"] = email_sent
        response_data["hubspot_synced"] = hubspot_result.get("success") if hubspot_result else False

        return {"success": True, "message": "Client created successfully", "data": response_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{client_id}", summary="Update client", response_model=None)
async def update_client(
    client_id: str,
    data: ClientUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing client."""
    try:
        client = await _get_client_checked(client_id, current_user, repo)
        # Check write access (non-admin can only edit their own company)
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        if not is_admin and str(client.id) != user_company_id:
            raise HTTPException(status_code=403, detail="Access denied to update this client")

        update_data = data.model_dump(exclude_unset=True)
        if "address" in update_data and update_data["address"]:
            update_data["address"] = (
                update_data["address"].model_dump()
                if hasattr(update_data["address"], "model_dump")
                else update_data["address"]
            )

        from uuid import UUID as _UUID
        client = await repo.update(_UUID(client_id), update_data)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated client: {client.name} (ID: {client.id})")
        return {"success": True, "message": "Client updated successfully", "data": client.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{client_id}/status", summary="Update client status", response_model=None)
async def update_client_status(
    client_id: str,
    data: StatusUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update client status. Only admin users can update client status."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can update client status")
        valid_statuses = [s.value for s in ClientStatus]
        if data.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client ID format")
        result = await repo.update_status(client_uuid, data.status)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
        client, old_status = result
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Updated client status: {client.name} from {old_status} to {data.status}")
        return {
            "success": True,
            "message": f"Client status updated from {old_status} to {data.status}",
            "data": client.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{client_id}", summary="Delete client (soft delete)", response_model=None)
async def delete_client(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: ClientAccountRepository = Depends(get_client_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Soft delete a client. Only admin users can delete clients."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_id = current_user.get("user_id", "system")
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin users can delete clients")
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client ID format")
        client = await repo.soft_delete(client_uuid, deleted_by=user_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Soft deleted client: {client.name} (ID: {client.id})")
        return {"success": True, "message": f"Client '{client.name}' has been deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
