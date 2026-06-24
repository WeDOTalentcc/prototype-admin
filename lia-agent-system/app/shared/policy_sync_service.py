"""
PolicySyncService — Synchronizes CompanyHiringPolicy to derived models.

Called after policy save (PUT/PATCH) to keep SLAs and feature flags in sync.
"""
from app.middleware.request_id import get_correlation_id
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

AUTOMATION_FLAG_MAP = {
    "auto_screening": {
        "flag_key_template": "ENABLE_AUTO_SCREENING_{company_id}",
        "description": "Enable automatic candidate screening",
        "category": "automation",
    },
    "auto_scheduling": {
        "flag_key_template": "ENABLE_AUTO_SCHEDULING_{company_id}",
        "description": "Enable automatic interview scheduling",
        "category": "automation",
    },
    "auto_stage_advance": {
        "flag_key_template": "ENABLE_AUTO_STAGE_ADVANCE_{company_id}",
        "description": "Enable automatic pipeline stage advancement",
        "category": "automation",
    },
}

AUTONOMY_LEVEL_PRESETS = {
    "low": {"auto_screening": False, "auto_scheduling": False, "auto_stage_advance": False},
    "medium": {"auto_screening": True, "auto_scheduling": False, "auto_stage_advance": False},
    "high": {"auto_screening": True, "auto_scheduling": True, "auto_stage_advance": True},
}


async def sync_policy_to_models(
    company_id: str,
    policy: dict[str, Any],
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Synchronize policy data to derived models after save.
    
    Returns dict with sync results for logging/debugging.
    """
    results = {
        "company_id": company_id,
        "sla_synced": False,
        "flags_synced": False,
        "errors": [],
    }
    
    try:
        sla_result = await _sync_stage_slas(company_id, policy, db)
        results["sla_synced"] = sla_result
    except Exception as e:
        logger.error(f"Error syncing SLAs for {company_id}: {e}")
        results["errors"].append(f"SLA sync: {str(e)}")
    
    try:
        flags_result = await _sync_feature_flags(company_id, policy, db)
        results["flags_synced"] = flags_result
    except Exception as e:
        logger.error(f"Error syncing feature flags for {company_id}: {e}")
        results["errors"].append(f"Flag sync: {str(e)}")
    
    logger.info(
        f"PolicySync for {company_id}: SLA={results['sla_synced']}, "
        f"Flags={results['flags_synced']}, Errors={len(results['errors'])}"
    )
    return results


async def _sync_stage_slas(
    company_id: str,
    policy: dict[str, Any],
    db: AsyncSession,
) -> bool:
    """Sync max_days_in_stage to RecruitmentStage SLA hours."""
    pipeline_rules = policy.get("pipeline_rules", {})
    max_days = pipeline_rules.get("max_days_in_stage")
    
    if not max_days:
        return False
    
    try:
        from sqlalchemy import select, update

        from app.models.recruitment_stage import RecruitmentStage
        
        if isinstance(max_days, dict):
            for stage_name, days in max_days.items():
                sla_hours = int(days) * 24
                stmt = (
                    update(RecruitmentStage)
                    .where(
                        RecruitmentStage.company_id == company_id,
                        RecruitmentStage.name.ilike(f"%{stage_name}%"),
                    )
                    .values(sla_hours=sla_hours)
                )
                await db.execute(stmt)
        elif isinstance(max_days, (int, float)):
            sla_hours = int(max_days) * 24
            stmt = (
                update(RecruitmentStage)
                .where(RecruitmentStage.company_id == company_id)
                .values(sla_hours=sla_hours)
            )
            await db.execute(stmt)
        
        await db.flush()
        logger.info(f"SLA hours synced for company {company_id}: max_days={max_days}")
        return True
    except ImportError:
        logger.warning("RecruitmentStage model not available, skipping SLA sync")
        return False
    except Exception as e:
        logger.error(f"Error syncing SLAs: {e}")
        return False


async def _sync_feature_flags(
    company_id: str,
    policy: dict[str, Any],
    db: AsyncSession,
) -> bool:
    """Sync automation_rules to per-company feature flags."""
    automation_rules = policy.get("automation_rules", {})
    if not automation_rules:
        return False
    
    try:
        from app.shared.governance.feature_flag_service import feature_flag_service
        
        autonomy_level = automation_rules.get("autonomy_level", "low")
        presets = AUTONOMY_LEVEL_PRESETS.get(autonomy_level, AUTONOMY_LEVEL_PRESETS["low"])
        
        for rule_key, flag_config in AUTOMATION_FLAG_MAP.items():
            explicit_value = automation_rules.get(rule_key)
            if explicit_value is not None:
                is_enabled = bool(explicit_value)
            else:
                is_enabled = presets.get(rule_key, False)
            
            flag_key = flag_config["flag_key_template"].format(company_id=company_id)

            await feature_flag_service.set_flag(
                db=db,
                flag_key=flag_key,
                is_enabled=is_enabled,
                company_id=company_id,
                description=flag_config["description"],
                category=flag_config["category"],
                created_by="policy-sync",
            )

            # P1-3 (post-Sprint-B audit): close the audit-log bypass.
            # The /feature-flags/set HTTP endpoint logs every toggle via
            # AuditService.log_action, but programmatic syncs through
            # this helper were skipping the trail entirely. LGPD Art. 20
            # requires the trail regardless of caller. Fail-soft so a
            # missing audit row never breaks the policy sync.
            try:
                import uuid as _uuid
                from app.shared.compliance.audit_service import AuditService

                await AuditService().log_action(
                    trace_id=get_correlation_id(),
                    company_id=str(company_id),
                    action_type="feature_flag_change",
                    actor="policy-sync",
                    target_id=flag_key,
                    target_type="feature_flag",
                    metadata={
                        "flag_key": flag_key,
                        "is_enabled": is_enabled,
                        "category": flag_config["category"],
                        "source": "policy_sync",
                        "autonomy_level": autonomy_level,
                        "rule_key": rule_key,
                    },
                )
            except Exception as audit_exc:
                logger.warning(
                    "[PolicySync] audit log_action failed (fail-soft) "
                    "flag=%s: %s",
                    flag_key, str(audit_exc)[:200],
                )

        logger.info(
            f"Feature flags synced for company {company_id}: "
            f"autonomy={autonomy_level}, rules={automation_rules}"
        )
        return True
    except Exception as e:
        logger.error(f"Error syncing feature flags: {e}")
        return False
