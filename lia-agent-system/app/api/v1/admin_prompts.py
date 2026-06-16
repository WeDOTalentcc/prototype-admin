"""
Admin — Prompts endpoints.

Sprint B / André P3/R3 — PromptVersionRegistry endpoints (canonical):
  GET /api/v1/admin/prompts/versions          → lista todos os prompts registrados
  GET /api/v1/admin/prompts/versions/{name}   → versões de um nome específico

Wave 2 Agent B / T-13 Fase 2 — Per-tenant YAML override endpoints (ADR-028-v3):
  GET    /api/v1/admin/prompts/tenant-overrides
  GET    /api/v1/admin/prompts/tenant-overrides/{path:path}
  PUT    /api/v1/admin/prompts/tenant-overrides/{path:path}
  DELETE /api/v1/admin/prompts/tenant-overrides/{path:path}

Multi-tenancy fail-closed: company_id sempre via require_company_id (JWT).
Hot-reload: PromptLoader.invalidate_cache(path, tenant_id) após PUT/DELETE.
PII scan: PII_PATTERNS canonical (app/shared/pii_masking.py).
Validações: yaml.safe_load + metadata.version required (T-05 enforcement).
"""
import logging
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth.dependencies import require_admin, require_wedotalent_admin
from app.auth.models import User
from app.shared.compliance.audit_service import AuditService
from app.shared.pii_masking import PII_PATTERNS
from app.shared.prompts.loader import PROMPTS_DIR, TENANTS_DIR, PromptLoader
from app.shared.security.require_company_id import require_company_id
from app.shared.services.prompt_version_registry import prompt_version_registry

router = APIRouter(prefix="/admin/prompts", tags=["admin-prompts"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response schemas — Sprint B (versions)
# ---------------------------------------------------------------------------


class PromptVersionResponse(BaseModel):
    name: str
    version: str
    hash_prefix: str
    hash_sha256: str
    created_at: str


class PromptVersionListResponse(BaseModel):
    total: int
    versions: list[PromptVersionResponse]


# ---------------------------------------------------------------------------
# Request/Response schemas — Wave 2 (tenant overrides)
# ---------------------------------------------------------------------------


class TenantOverrideEntry(BaseModel):
    """Single tenant override metadata entry."""
    path: str = Field(..., description="Canonical path, e.g. domains/sourcing")
    version: str = Field(..., description="metadata.version do YAML")
    last_updated_at: str = Field(..., description="ISO timestamp do mtime")
    size_bytes: int = Field(..., description="Tamanho atual do override")


class TenantOverrideListResponse(BaseModel):
    company_id: str
    total: int
    overrides: list[TenantOverrideEntry]


class TenantOverrideContentResponse(BaseModel):
    path: str
    content: str = Field(..., description="YAML raw")
    version: str
    last_updated_at: str


class TenantOverridePutRequest(BaseModel):
    """REGRA 1 — extra=forbid canonical."""
    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., min_length=1, description="YAML raw content")
    expected_version: str | None = Field(
        None,
        description="metadata.version esperado (optimistic concurrency, opcional)",
    )


class TenantOverridePutResponse(BaseModel):
    success: bool
    path: str
    version: str
    last_updated_at: str
    validation_warnings: list[str] = Field(default_factory=list)


class TenantOverrideDeleteResponse(BaseModel):
    success: bool
    deleted_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_version_response(entry: dict) -> PromptVersionResponse:
    return PromptVersionResponse(
        name=entry["name"],
        version=entry["version"],
        hash_prefix=entry["hash_prefix"],
        hash_sha256=entry["hash_sha256"],
        created_at=entry["created_at"],
    )


# Backward-compat alias (tests/unit/test_admin_prompts_extended.py)
_to_response = _to_version_response


_ALLOWED_PATH_PREFIXES = ("domains/", "shared/")
_MAX_YAML_BYTES = 256 * 1024  # 256 KiB safety bound


def _validate_logical_path(path: str) -> None:
    """Bloqueia path traversal + restringe a prefixes canonical.

    YAML paths permitidos: domains/{name} ou shared/{name}.
    """
    if not path:
        raise HTTPException(status_code=400, detail="Path vazio")
    if ".." in path or path.startswith("/") or "\\" in path:
        raise HTTPException(status_code=400, detail="Path inválido (traversal)")
    if not path.startswith(_ALLOWED_PATH_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Path deve começar com {_ALLOWED_PATH_PREFIXES} "
                "(canonical YAML paths)"
            ),
        )
    canonical_file = PROMPTS_DIR / f"{path}.yaml"
    if not canonical_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Path canonical {path} não existe — não pode ser sobrescrito",
        )


def _resolve_tenant_override_path(company_id: str, path: str) -> Path:
    _validate_logical_path(path)
    return TENANTS_DIR / company_id / f"{path}.yaml"


def _read_override_metadata(file_path: Path, logical_path: str) -> TenantOverrideEntry:
    raw = file_path.read_text(encoding='utf-8')
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        data = None
    version = "?"
    if isinstance(data, dict):
        metadata = data.get("metadata", {})
        if isinstance(metadata, dict):
            version = str(metadata.get("version", "?"))
    stat = file_path.stat()
    return TenantOverrideEntry(
        path=logical_path,
        version=version,
        last_updated_at=datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        size_bytes=stat.st_size,
    )


def _scan_pii(content: str) -> list[str]:
    """REGRA canonical — reusa PII_PATTERNS (app/shared/pii_masking.py).

    Returns: lista de warnings (não bloqueia — informa admin).
    """
    warnings: list[str] = []
    for pattern, _replacement in PII_PATTERNS:
        if pattern.search(content):
            warnings.append(
                f"YAML contém padrão PII (pattern={pattern.pattern[:40]}...) — "
                "revisar antes de salvar"
            )
    return warnings


def _validate_yaml_payload(content: str) -> tuple[dict, str]:
    """Valida sintaxe + metadata.version required (T-05).

    Returns: (parsed_dict, version_string).
    Raises HTTPException 422 em qualquer falha.
    """
    if len(content.encode("utf-8")) > _MAX_YAML_BYTES:
        raise HTTPException(
            status_code=422,
            detail=f"YAML excede {_MAX_YAML_BYTES} bytes (limite canonical)",
        )
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(
            status_code=422, detail=f"YAML inválido: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=422,
            detail="YAML root deve ser mapping (dict)",
        )

    metadata = parsed.get("metadata")
    if not isinstance(metadata, dict):
        raise HTTPException(
            status_code=422,
            detail="metadata block obrigatório (T-05 enforcement)",
        )
    version = metadata.get("version")
    if not version or not isinstance(version, str):
        raise HTTPException(
            status_code=422,
            detail="metadata.version obrigatório (string não vazia) — T-05",
        )
    return parsed, version


# ---------------------------------------------------------------------------
# Endpoints — Sprint B versions
# ---------------------------------------------------------------------------


@router.get("/versions", response_model=PromptVersionListResponse)
async def list_all_versions(
    current_user: User = Depends(require_admin),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: admin/platform-level — role-based access required
    """Lista todos os prompts registrados no PromptVersionRegistry."""
    all_entries = prompt_version_registry.list_all()
    return PromptVersionListResponse(
        total=len(all_entries),
        versions=[_to_version_response(e) for e in all_entries],
    )


@router.get("/versions/{name}", response_model=PromptVersionListResponse)
async def list_versions_by_name(
    name: str,
    current_user: User = Depends(require_admin),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: admin/platform-level — role-based access required
    """Lista todas as versões registradas para um nome de prompt específico."""
    entries = prompt_version_registry.list_versions(name)
    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhuma versão encontrada para o prompt {name}.",
        )
    return PromptVersionListResponse(
        total=len(entries),
        versions=[_to_version_response(e) for e in entries],
    )


# ---------------------------------------------------------------------------
# Endpoints — Wave 2 T-13 tenant overrides (ADR-028-v3)
# ---------------------------------------------------------------------------


@router.get("/tenant-overrides", response_model=TenantOverrideListResponse)
async def list_tenant_overrides(
    # P1-7/E4-prep (2026-05-21): tenant overrides are CROSS-TENANT staff
    # tooling. Customer-end UserRole.admin no longer has access; only
    # UserRole.wedotalent_admin can list/read/write/delete YAML overrides.
    current_user: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Lista todos os overrides YAML ativos para o tenant (company_id do JWT).

    Multi-tenancy fail-closed: company_id sempre do JWT — nunca payload.
    """
    tenant_dir = TENANTS_DIR / company_id
    overrides: list[TenantOverrideEntry] = []
    if tenant_dir.exists() and tenant_dir.is_dir():
        for yaml_file in tenant_dir.rglob("*.yaml"):
            relative = yaml_file.relative_to(tenant_dir).with_suffix("")
            logical_path = str(relative).replace("\\", "/")
            try:
                overrides.append(_read_override_metadata(yaml_file, logical_path))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[admin_prompts T-13] failed to read override file=%s err=%s",
                    yaml_file, exc,
                )
    overrides.sort(key=lambda o: o.path)
    return TenantOverrideListResponse(
        company_id=company_id, total=len(overrides), overrides=overrides
    )


@router.get(
    "/tenant-overrides/{path:path}",
    response_model=TenantOverrideContentResponse,
)
async def get_tenant_override(
    path: str,
    current_user: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Retorna o conteúdo YAML raw de um override específico."""
    file_path = _resolve_tenant_override_path(company_id, path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Override {path} não existe para company {company_id}",
        )
    content = file_path.read_text(encoding="utf-8")
    meta = _read_override_metadata(file_path, path)
    return TenantOverrideContentResponse(
        path=path,
        content=content,
        version=meta.version,
        last_updated_at=meta.last_updated_at,
    )


@router.put(
    "/tenant-overrides/{path:path}",
    response_model=TenantOverridePutResponse,
)
async def put_tenant_override(
    path: str,
    payload: TenantOverridePutRequest = Body(...),
    # P1-7/E4-prep (2026-05-21): only WeDOTalent staff can write tenant overrides.
    current_user: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Cria ou atualiza override YAML para o tenant.

    Validações canonical (via :func:`validate_tenant_persona_override`):
      - YAML syntax (yaml.safe_load)
      - metadata.version required (T-05)
      - Ethics invariants (LGPD / fairness / EU AI Act) — REJEITA 422 se removidos
      - PII scan (warnings — não bloqueia)
      - Path traversal blocked (em :func:`_resolve_tenant_override_path`)
      - Hot-reload via PromptLoader.invalidate_cache
    """
    # C3 (audit 2026-05-21): unified validator com ethics-invariants enforcement.
    # Substitui os antigos ``_validate_yaml_payload`` + ``_scan_pii`` inline.
    # Mesmo admin WeDOTalent staff não consegue persistir override que apague
    # blocos de compliance — o gate é fail-closed por design.
    from app.domains.persona.services.tenant_persona_validator import (
        validate_tenant_persona_override,
    )
    validation = validate_tenant_persona_override(payload.content, path=path)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "persona_override_rejected",
                "message": "Override rejeitado por validador canonical.",
                "errors": validation.errors,
                "warnings": validation.warnings,
            },
        )
    version = validation.version or "unknown"
    warnings = [w.get("message", "") for w in validation.warnings]

    file_path = _resolve_tenant_override_path(company_id, path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # C4 (audit 2026-05-21): capture before-state para audit diff.
    # Permite admin WeDOTalent reconstruir history per-tenant (rollback UI).
    prev_content = ""
    prev_hash = ""
    if file_path.exists():
        try:
            prev_content = file_path.read_text(encoding="utf-8")
            import hashlib as _hashlib
            prev_hash = _hashlib.sha256(prev_content.encode("utf-8")).hexdigest()[:16]
        except Exception:
            pass
    import hashlib as _hashlib
    new_hash = _hashlib.sha256(payload.content.encode("utf-8")).hexdigest()[:16]
    file_path.write_text(payload.content, encoding="utf-8")

    PromptLoader.invalidate_cache(path=path, tenant_id=company_id)

    audit_service = AuditService()
    try:
        # AUDIT-NO-DEMO: admin config change (T-13 tenant override write)
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="admin_prompts",
            decision_type="admin_config_change",
            action="tenant_override_put",
            decision="success",
            reasoning=[
                f"path={path}",
                f"version={version}",
                f"size_bytes={len(payload.content.encode('utf-8'))}",
                f"pii_warnings={len(warnings)}",
                f"prev_hash={prev_hash or 'first_version'}",
                f"new_hash={new_hash}",
            ],
            criteria_used=[
                "yaml_syntax", "metadata_version", "ethics_invariants",
                "pii_scan",
            ],
            actor_user_id=str(current_user.id),
            human_review_required=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[admin_prompts T-13] audit log failed (non-blocking) path=%s err=%s",
            path, exc,
        )

    meta = _read_override_metadata(file_path, path)
    return TenantOverridePutResponse(
        success=True,
        path=path,
        version=meta.version,
        last_updated_at=meta.last_updated_at,
        validation_warnings=warnings,
    )


@router.delete(
    "/tenant-overrides/{path:path}",
    response_model=TenantOverrideDeleteResponse,
)
async def delete_tenant_override(
    path: str,
    current_user: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Remove override (fallback canonical preserved via PromptLoader fail-soft)."""
    file_path = _resolve_tenant_override_path(company_id, path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Override {path} não existe para company {company_id}",
        )
    file_path.unlink()

    PromptLoader.invalidate_cache(path=path, tenant_id=company_id)

    audit_service = AuditService()
    try:
        # AUDIT-NO-DEMO: admin config change (T-13 tenant override delete)
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="admin_prompts",
            decision_type="admin_config_change",
            action="tenant_override_delete",
            decision="success",
            reasoning=[f"path={path}"],
            criteria_used=["override_existed"],
            actor_user_id=str(current_user.id),
            human_review_required=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[admin_prompts T-13] audit log failed (non-blocking) path=%s err=%s",
            path, exc,
        )

    return TenantOverrideDeleteResponse(success=True, deleted_path=path)
