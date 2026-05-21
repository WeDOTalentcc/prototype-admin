"""ATS Integration ReAct Agent — Tool Registry.

Wraps ATSSyncService operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for bidirectional ATS synchronization.

Supported providers: Gupy, Pandapé, Merge.
"""
import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------


@tool_handler("ats_integration")
async def _wrap_sync_candidate_to_ats(**kwargs: Any) -> dict[str, Any]:
    """Push candidate data to an external ATS."""
    from app.domains.ats_integration.services.ats_sync_service import (
        ATSSyncService,
        ATSSyncTrigger,
    )

    candidate_id: int | None = kwargs.get("candidate_id")
    company_id: str | None = kwargs.get("company_id")
    ats_provider: str | None = kwargs.get("ats_provider")
    trigger_raw: str = kwargs.get("trigger", "CANDIDATE_UPDATED")

    if candidate_id is None:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    # Map trigger string to enum value (case-insensitive)
    trigger_map = {t.value: t for t in ATSSyncTrigger}
    # Accept both raw enum value ("status_change") and constant name ("STATUS_CHANGE")
    trigger_value = trigger_raw.lower()
    trigger = trigger_map.get(trigger_value)
    if trigger is None:
        # Try mapping constant-name style to value style
        trigger_value_alt = trigger_raw.lower().replace("_", "_")
        trigger = trigger_map.get(trigger_value_alt, ATSSyncTrigger.CANDIDATE_UPDATED)

    svc = ATSSyncService()
    result = await svc.trigger_sync(
        trigger=trigger,
        source_agent="ats_integration_react_agent",
        ats_type=ats_provider.lower(),
        candidate_id=str(candidate_id),
        data={"candidate_id": candidate_id, "company_id": company_id},
    )
    return {"success": result.get("success", False), **result}
@tool_handler("ats_integration")
async def _wrap_fetch_candidate_from_ats(**kwargs: Any) -> dict[str, Any]:
    """Pull candidate data from an external ATS."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncService

    ats_candidate_id: str | None = kwargs.get("ats_candidate_id")
    kwargs.get("company_id")
    ats_provider: str | None = kwargs.get("ats_provider")

    if not ats_candidate_id:
        return {"success": False, "message": "ats_candidate_id é obrigatório"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    svc = ATSSyncService()
    result = await svc.pull_candidate(
        ats_type=ats_provider.lower(),
        ats_candidate_id=ats_candidate_id,
        source_agent="ats_integration_react_agent",
    )
    return {"success": result.get("success", False), **result}
@tool_handler("ats_integration")
async def _wrap_validate_ats_fields(**kwargs: Any) -> dict[str, Any]:
    """Validate field mappings before a sync operation."""
    from app.domains.ats_integration.services.ats_sync_service import ATSFieldMapping

    candidate_data: dict[str, Any] | None = kwargs.get("candidate_data")
    company_id: str | None = kwargs.get("company_id")
    ats_provider: str | None = kwargs.get("ats_provider")

    if not candidate_data:
        return {"success": False, "message": "candidate_data é obrigatório"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    provider = ats_provider.lower()
    mapping = ATSFieldMapping.get_mapping(provider)
    if not mapping:
        return {
            "success": False,
            "message": f"ATS provider '{ats_provider}' não tem mapeamento configurado",
            "supported_providers": ["gupy", "pandape", "merge"],
        }

    syncable: list[dict[str, Any]] = []
    unsyncable: list[dict[str, str]] = []

    for field, value in candidate_data.items():
        can_sync = ATSFieldMapping.can_sync_field(provider, field)
        ats_field = ATSFieldMapping.get_ats_field_name(provider, field)
        if can_sync and ats_field:
            syncable.append({"wedotalent_field": field, "ats_field": ats_field})
        else:
            field_cfg = mapping.get(field, {})
            reason = field_cfg.get("note", "Campo não mapeado no ATS")
            unsyncable.append({"field": field, "reason": reason})

    return {
        "success": True,
        "ats_provider": ats_provider,
        "company_id": company_id,
        "syncable_fields": syncable,
        "unsyncable_fields": unsyncable,
        "syncable_count": len(syncable),
        "unsyncable_count": len(unsyncable),
        "validation_passed": len(syncable) > 0,
    }
@tool_handler("ats_integration")
async def _wrap_bulk_sync_candidates(**kwargs: Any) -> dict[str, Any]:
    """Sync multiple candidates to an external ATS in bulk."""
    from app.domains.ats_integration.services.ats_sync_service import (
        ATSSyncService,
        ATSSyncTrigger,
    )

    candidate_ids: list[int] | None = kwargs.get("candidate_ids")
    company_id: str | None = kwargs.get("company_id")
    ats_provider: str | None = kwargs.get("ats_provider")
    trigger_raw: str = kwargs.get("trigger", "BULK_SYNC")

    if not candidate_ids:
        return {"success": False, "message": "candidate_ids é obrigatório (lista de inteiros)"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    trigger_map = {t.value: t for t in ATSSyncTrigger}
    trigger = trigger_map.get(trigger_raw.lower(), ATSSyncTrigger.BULK_SYNC)

    svc = ATSSyncService()
    results = []
    errors = []

    for cid in candidate_ids:
        try:
            res = await svc.trigger_sync(
                trigger=trigger,
                source_agent="ats_integration_react_agent",
                ats_type=ats_provider.lower(),
                candidate_id=str(cid),
                data={"candidate_id": cid, "company_id": company_id},
            )
            results.append({"candidate_id": cid, "success": res.get("success"), "sync_id": res.get("sync_id")})
        except Exception as inner_e:
            errors.append({"candidate_id": cid, "error": str(inner_e)})

    success_count = sum(1 for r in results if r.get("success"))
    return {
        "success": len(errors) == 0,
        "ats_provider": ats_provider,
        "total": len(candidate_ids),
        "synced": success_count,
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "message": (
            f"Sincronizados {success_count}/{len(candidate_ids)} candidatos para {ats_provider}"
        ),
    }
@tool_handler("ats_integration")
async def _wrap_get_sync_status(**kwargs: Any) -> dict[str, Any]:
    """Get synchronization status for a candidate."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncService

    candidate_id: int | None = kwargs.get("candidate_id")
    company_id: str | None = kwargs.get("company_id")
    ats_provider: str | None = kwargs.get("ats_provider")

    if candidate_id is None:
        return {"success": False, "message": "candidate_id é obrigatório"}

    svc = ATSSyncService()
    stats = svc.get_sync_stats()
    audit = svc.get_audit_log(
        candidate_id=str(candidate_id),
        limit=20,
    )

    # Filter by provider if specified
    if ats_provider:
        audit = [entry for entry in audit if entry.get("ats_type", "").lower() == ats_provider.lower()]

    last_sync = audit[0] if audit else None
    return {
        "success": True,
        "candidate_id": candidate_id,
        "company_id": company_id,
        "ats_provider": ats_provider,
        "last_sync": last_sync,
        "total_syncs_for_candidate": len(audit),
        "platform_stats": stats,
        "configured_providers": stats.get("configured_clients", []),
    }
# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

@tool_handler("ats_integration")
async def _wrap_recommend_integrations_by_industry(**kwargs):
    """
    Recomenda integrações ATS canonical baseado no setor.

    Audit 2026-05-20 Sessão I / Tema B: Settings > Integrações hoje mostra
    catálogo hardcoded (17 produtos) sem priorização. Esta tool retorna
    recomendações canonical por setor para a LIA sugerir ao admin.

    Multi-tenancy: company_id obrigatório via ContextVar JWT (@tool_handler).
    """
    company_id = kwargs.get("company_id")
    industry = (kwargs.get("industry") or "").strip().lower()

    INDUSTRY_RECOMMENDATIONS = {
        "tecnologia": [
            {"provider": "gupy", "rationale": "Lider ATS para empresas tech no Brasil; integracao nativa LinkedIn."},
            {"provider": "merge", "rationale": "Unified API: 1 integracao = N ATS conectados."},
        ],
        "saude": [
            {"provider": "gupy", "rationale": "Compliance LGPD-saude nativo + grandes redes hospitalares."},
        ],
        "varejo": [
            {"provider": "pandape", "rationale": "Volume alto + recrutadores junior (UI mais simples)."},
            {"provider": "gupy", "rationale": "Para varejistas grandes (>500 funcionarios)."},
        ],
        "industria": [
            {"provider": "pandape", "rationale": "Alto volume + processos descentralizados."},
        ],
        "servicos": [
            {"provider": "gupy", "rationale": "Padrao de mercado para servicos profissionais."},
        ],
    }
    industry_key = industry or "tecnologia"
    recs = INDUSTRY_RECOMMENDATIONS.get(industry_key, INDUSTRY_RECOMMENDATIONS["tecnologia"])

    return {
        "success": True,
        "data": {
            "recommendations": recs,
            "industry_used": industry_key,
            "industry_was_default": not industry,
        },
        "message": f"{len(recs)} integracao(oes) recomendada(s) para o setor '{industry_key}'.",
    }


@tool_handler("ats_integration")
async def _wrap_apply_integration_catalog_entry(**kwargs):
    """Aplica (= snapshot canonical B1) um entry de catalogo para uso da company.

    Audit 2026-05-20 Sprint 4 F5: substitui catalogo hardcoded por per-tenant DB.
    Se entry_id eh master -> cria copia canonical (snapshot B1 via repo.customize_master).
    Se entry_id ja eh custom desta company -> retorna config do entry direto.

    Retorna config canonical pra orquestrar OAuth/setup no frontend.

    Multi-tenancy: company_id obrigatorio via ContextVar JWT (@tool_handler).
    """
    import uuid as _uuid

    from app.core.database import AsyncSessionLocal
    from app.domains.ats_integration.repositories.integration_catalog_entry_repository import (
        IntegrationCatalogEntryRepository,
    )

    company_id = kwargs.get("company_id")
    entry_id_raw = kwargs.get("entry_id")
    target_company_integration_id = kwargs.get("target_company_integration_id")

    if not entry_id_raw:
        return {"success": False, "message": "entry_id eh obrigatorio (UUID do catalog entry)"}

    try:
        entry_id = _uuid.UUID(str(entry_id_raw))
    except (ValueError, TypeError, AttributeError):
        return {"success": False, "message": f"entry_id invalido: {entry_id_raw} (esperado UUID)"}

    async with AsyncSessionLocal() as session:
        repo = IntegrationCatalogEntryRepository(session)
        entry = await repo.get_by_id(entry_id, company_id)
        if not entry:
            return {
                "success": False,
                "message": "Entry nao encontrado ou fora do escopo da empresa",
            }

        # Snapshot canonical B1: se eh master, clona pra company; se ja eh custom, retorna direto
        applied_entry = entry
        was_cloned = False
        if entry.is_master_template:
            applied_entry = await repo.customize_master(
                master_id=entry.id,
                company_id=company_id,
                created_by=kwargs.get("user_id"),
            )
            if not applied_entry:
                await session.rollback()
                return {
                    "success": False,
                    "message": "Falha ao clonar master entry (snapshot canonical B1)",
                }
            was_cloned = True
            await session.commit()

        data = dict(applied_entry.data or {})
        metadata = data.get("metadata") or {}
        connect_action = metadata.get("connect_action") if isinstance(metadata, dict) else None
        config_fields = metadata.get("config_fields") if isinstance(metadata, dict) else None

        return {
            "success": True,
            "data": {
                "applied_entry_id": str(applied_entry.id),
                "parent_template_id": (
                    str(applied_entry.parent_template_id) if applied_entry.parent_template_id else None
                ),
                "was_cloned_from_master": was_cloned,
                "target_company_integration_id": target_company_integration_id,
                "provider": data.get("provider"),
                "label": data.get("label"),
                "category": data.get("category"),
                "status": data.get("status"),
                "connect_action": connect_action,
                "config_fields": config_fields,
                "logo_url": data.get("logo_url"),
            },
            "message": (
                f"Entry {data.get('label') or data.get('provider')} aplicado para a empresa"
                + (" (snapshot canonical do master)." if was_cloned else ".")
            ),
        }


@tool_handler("ats_integration")
async def _wrap_create_custom_integration_catalog_entry(**kwargs):
    """Cria custom entry novo no catalogo de integracoes da company.

    Audit 2026-05-20 Sprint 4 F5: admin/recrutador pode adicionar provedor custom
    nao listado nos masters da WeDOTalent.

    Multi-tenancy: company_id obrigatorio via ContextVar JWT (@tool_handler).
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.ats_integration.repositories.integration_catalog_entry_repository import (
        IntegrationCatalogEntryRepository,
    )

    company_id = kwargs.get("company_id")
    user_id = kwargs.get("user_id")
    provider = (kwargs.get("provider") or "").strip()
    label = (kwargs.get("label") or "").strip()
    category = (kwargs.get("category") or "").strip()
    description = (kwargs.get("description") or "").strip()
    logo_url = kwargs.get("logo_url")
    industries_recommended = kwargs.get("industries_recommended") or []

    if not provider:
        return {"success": False, "message": "provider eh obrigatorio (slug canonical)"}
    if len(label) < 2:
        return {"success": False, "message": "label eh obrigatorio (minimo 2 caracteres)"}

    VALID_CATEGORIES = {
        "ai_models", "ats", "calendar", "communication", "crm_hris", "mcps_apis",
    }
    if category not in VALID_CATEGORIES:
        return {
            "success": False,
            "message": (
                f"category invalida: '{category}'. Valores aceitos: {sorted(VALID_CATEGORIES)}"
            ),
        }

    if not isinstance(industries_recommended, list):
        return {
            "success": False,
            "message": "industries_recommended deve ser uma lista de strings",
        }

    data: dict = {
        "provider": provider,
        "label": label,
        "category": category,
        "description": description or f"Integracao custom: {label}",
        "status": "production",
        "industries_recommended": [str(i) for i in industries_recommended],
    }
    if logo_url:
        data["logo_url"] = logo_url

    async with AsyncSessionLocal() as session:
        repo = IntegrationCatalogEntryRepository(session)
        try:
            entry = await repo.create_custom(
                company_id=company_id,
                data=data,
                created_by=str(user_id) if user_id else None,
            )
            await session.commit()
        except Exception as exc:
            await session.rollback()
            return {
                "success": False,
                "message": f"Falha ao criar entry custom: {exc}",
            }

        return {
            "success": True,
            "data": {
                "entry_id": str(entry.id),
                "provider": data["provider"],
                "label": data["label"],
                "category": data["category"],
                "status": data["status"],
            },
            "message": f"Integracao custom '{label}' criada no catalogo da empresa.",
        }



def get_ats_integration_tools() -> list[ToolDefinition]:
    """Return all ATS Integration tools."""
    return [
        ToolDefinition(
            name="sync_candidate_to_ats",
            description=(
                "Enviar dados de um candidato para um ATS externo (push). "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str), "
                "ats_provider (str: gupy/pandape/merge), "
                "trigger (str: STATUS_CHANGE/CANDIDATE_CREATED/CANDIDATE_UPDATED/etc)."
            ),
            output_schema=ToolOutput,
            function=_wrap_sync_candidate_to_ats,
        ),
        ToolDefinition(
            name="fetch_candidate_from_ats",
            description=(
                "Buscar dados de um candidato a partir de um ATS externo (pull). "
                "Parâmetros: ats_candidate_id (str, obrigatório), company_id (str), "
                "ats_provider (str: gupy/pandape/merge)."
            ),
            output_schema=ToolOutput,
            function=_wrap_fetch_candidate_from_ats,
        ),
        ToolDefinition(
            name="validate_ats_fields",
            description=(
                "Validar mapeamento de campos antes de uma sincronização com ATS. "
                "Retorna quais campos serão sincronizados e quais serão ignorados. "
                "Parâmetros: candidate_data (dict), company_id (str), "
                "ats_provider (str: gupy/pandape/merge)."
            ),
            output_schema=ToolOutput,
            function=_wrap_validate_ats_fields,
        ),
        ToolDefinition(
            name="bulk_sync_candidates",
            description=(
                "Sincronizar múltiplos candidatos com um ATS externo em lote. "
                "Parâmetros: candidate_ids (list[int], obrigatório), company_id (str), "
                "ats_provider (str: gupy/pandape/merge), "
                "trigger (str: BULK_SYNC/STATUS_CHANGE/etc)."
            ),
            output_schema=ToolOutput,
            function=_wrap_bulk_sync_candidates,
        ),
        ToolDefinition(
            name="get_sync_status",
            description=(
                "Consultar status de sincronização de um candidato com o ATS. "
                "Retorna histórico de syncs e estatísticas da plataforma. "
                "Parâmetros: candidate_id (int, obrigatório), company_id (str), "
                "ats_provider (str, opcional — filtra por provedor)."
            ),
            output_schema=ToolOutput,
            function=_wrap_get_sync_status,
        ),
        ToolDefinition(
            name="recommend_integrations_by_industry",
            description=(
                "Recomenda integracoes ATS canonical baseado no setor da empresa "
                "(tecnologia, saude, varejo, industria, servicos). Util quando o "
                "admin abre Settings > Integracoes pela 1a vez."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "Setor da empresa em minusculas. Se vazio, default = tecnologia.",
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_recommend_integrations_by_industry,
        ),
        ToolDefinition(
            name="apply_integration_catalog_entry",
            description=(
                "Aplica um entry do catalogo de integracoes para a company atual "
                "(snapshot canonical B1). Se entry_id eh master da WeDOTalent, "
                "clona para a empresa; se ja eh custom desta empresa, retorna config. "
                "Util quando admin escolhe um provedor (ex: Gupy/Pandape) para conectar."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "entry_id": {
                        "type": "string",
                        "description": "UUID do catalog entry (master ou custom da company).",
                    },
                    "target_company_integration_id": {
                        "type": "string",
                        "description": (
                            "Opcional: UUID de company_integration existente para "
                            "associar ao snapshot (uso futuro de re-config)."
                        ),
                    },
                },
                "required": ["entry_id"],
            },
            output_schema=ToolOutput,
            function=_wrap_apply_integration_catalog_entry,
        ),
        ToolDefinition(
            name="create_custom_integration_catalog_entry",
            description=(
                "Cria um custom entry novo no catalogo de integracoes da empresa. "
                "Util para admin adicionar um provedor nao listado nos masters "
                "curados pela WeDOTalent (ex: ATS interno, integracao homologada)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Slug canonical do provedor (ex: 'meu-ats-interno').",
                    },
                    "label": {
                        "type": "string",
                        "description": "Nome display (minimo 2 caracteres).",
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            "Categoria canonical: ai_models | ats | calendar | "
                            "communication | crm_hris | mcps_apis."
                        ),
                    },
                    "description": {
                        "type": "string",
                        "description": "Descricao curta (opcional).",
                    },
                    "logo_url": {
                        "type": "string",
                        "description": "URL/path do logo (opcional).",
                    },
                    "industries_recommended": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de setores recomendados (opcional).",
                    },
                },
                "required": ["provider", "label", "category"],
            },
            output_schema=ToolOutput,
            function=_wrap_create_custom_integration_catalog_entry,
        ),
    ]


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return tools available for a given ATS integration stage."""
    from app.domains.ats_integration.agents.ats_integration_stage_context import (
        get_stage_tools as _stage_tools,
    )
    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_ats_integration_tools() if t.name in stage_tool_names]
