"""ATS Integration ReAct Agent — Tool Registry.

Wraps ATSSyncService operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for bidirectional ATS synchronization.

Supported providers: Gupy, Pandapé, Merge.
"""
import logging
from typing import Any, Dict, List, Optional

from lia_agents_core.react_loop import ToolDefinition

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------


async def _wrap_sync_candidate_to_ats(**kwargs: Any) -> Dict[str, Any]:
    """Push candidate data to an external ATS."""
    from app.domains.ats_integration.services.ats_sync_service import (
        ATSSyncService,
        ATSSyncTrigger,
    )

    candidate_id: Optional[int] = kwargs.get("candidate_id")
    company_id: Optional[str] = kwargs.get("company_id")
    ats_provider: Optional[str] = kwargs.get("ats_provider")
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

    try:
        svc = ATSSyncService()
        result = await svc.trigger_sync(
            trigger=trigger,
            source_agent="ats_integration_react_agent",
            ats_type=ats_provider.lower(),
            candidate_id=str(candidate_id),
            data={"candidate_id": candidate_id, "company_id": company_id},
        )
        return {"success": result.get("success", False), **result}
    except Exception as e:
        logger.error(f"[ats_integration_tools] sync_candidate_to_ats error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_fetch_candidate_from_ats(**kwargs: Any) -> Dict[str, Any]:
    """Pull candidate data from an external ATS."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncService

    ats_candidate_id: Optional[str] = kwargs.get("ats_candidate_id")
    company_id: Optional[str] = kwargs.get("company_id")
    ats_provider: Optional[str] = kwargs.get("ats_provider")

    if not ats_candidate_id:
        return {"success": False, "message": "ats_candidate_id é obrigatório"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    try:
        svc = ATSSyncService()
        result = await svc.pull_candidate(
            ats_type=ats_provider.lower(),
            ats_candidate_id=ats_candidate_id,
            source_agent="ats_integration_react_agent",
        )
        return {"success": result.get("success", False), **result}
    except Exception as e:
        logger.error(f"[ats_integration_tools] fetch_candidate_from_ats error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_validate_ats_fields(**kwargs: Any) -> Dict[str, Any]:
    """Validate field mappings before a sync operation."""
    from app.domains.ats_integration.services.ats_sync_service import ATSFieldMapping

    candidate_data: Optional[Dict[str, Any]] = kwargs.get("candidate_data")
    company_id: Optional[str] = kwargs.get("company_id")
    ats_provider: Optional[str] = kwargs.get("ats_provider")

    if not candidate_data:
        return {"success": False, "message": "candidate_data é obrigatório"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    try:
        provider = ats_provider.lower()
        mapping = ATSFieldMapping.get_mapping(provider)
        if not mapping:
            return {
                "success": False,
                "message": f"ATS provider '{ats_provider}' não tem mapeamento configurado",
                "supported_providers": ["gupy", "pandape", "merge"],
            }

        syncable: List[Dict[str, Any]] = []
        unsyncable: List[Dict[str, str]] = []

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
    except Exception as e:
        logger.error(f"[ats_integration_tools] validate_ats_fields error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_bulk_sync_candidates(**kwargs: Any) -> Dict[str, Any]:
    """Sync multiple candidates to an external ATS in bulk."""
    from app.domains.ats_integration.services.ats_sync_service import (
        ATSSyncService,
        ATSSyncTrigger,
    )

    candidate_ids: Optional[List[int]] = kwargs.get("candidate_ids")
    company_id: Optional[str] = kwargs.get("company_id")
    ats_provider: Optional[str] = kwargs.get("ats_provider")
    trigger_raw: str = kwargs.get("trigger", "BULK_SYNC")

    if not candidate_ids:
        return {"success": False, "message": "candidate_ids é obrigatório (lista de inteiros)"}
    if not ats_provider:
        return {"success": False, "message": "ats_provider é obrigatório (gupy/pandape/merge)"}

    trigger_map = {t.value: t for t in ATSSyncTrigger}
    trigger = trigger_map.get(trigger_raw.lower(), ATSSyncTrigger.BULK_SYNC)

    try:
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
    except Exception as e:
        logger.error(f"[ats_integration_tools] bulk_sync_candidates error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_get_sync_status(**kwargs: Any) -> Dict[str, Any]:
    """Get synchronization status for a candidate."""
    from app.domains.ats_integration.services.ats_sync_service import ATSSyncService

    candidate_id: Optional[int] = kwargs.get("candidate_id")
    company_id: Optional[str] = kwargs.get("company_id")
    ats_provider: Optional[str] = kwargs.get("ats_provider")

    if candidate_id is None:
        return {"success": False, "message": "candidate_id é obrigatório"}

    try:
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
    except Exception as e:
        logger.error(f"[ats_integration_tools] get_sync_status error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

def get_ats_integration_tools() -> List[ToolDefinition]:
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
            function=_wrap_sync_candidate_to_ats,
        ),
        ToolDefinition(
            name="fetch_candidate_from_ats",
            description=(
                "Buscar dados de um candidato a partir de um ATS externo (pull). "
                "Parâmetros: ats_candidate_id (str, obrigatório), company_id (str), "
                "ats_provider (str: gupy/pandape/merge)."
            ),
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
            function=_wrap_get_sync_status,
        ),
    ]


def get_stage_tools(stage: str) -> List[ToolDefinition]:
    """Return tools available for a given ATS integration stage."""
    from app.domains.ats_integration.agents.ats_integration_stage_context import (
        get_stage_tools as _stage_tools,
    )
    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_ats_integration_tools() if t.name in stage_tool_names]
