"""
StageRuleAdapter — bridge entre stage_automation_rules (UI legacy) e
communication_automations (engine canonical).

WT-2022 P3.2 (2026-05-21): decisão Paulo — `stage_automation_rules` continua
recebendo writes da UI legada (`/api/v1/automation-rules/*`) mas o engine que
EXECUTA automations (`stage_automation_engine.py:198`) lê de
`communication_automations`. Existem duas tabelas com schemas parecidos sem
consistência. Adapter resolve isso com dual-write.

## Pattern canonical

- **READ list**: query `communication_automations` primeiro (canonical), fallback
  `stage_automation_rules` para registros não-migrados.
- **CREATE/UPDATE**: dual-write — escreve em ambos para preservar UI legacy +
  engine canonical em sync.
- **DELETE**: soft delete em ambos (`is_active=False`) — preserva
  auditability + permite rollback.
- **Adapter de schema**: `stage_rule_to_communication_automation` converte
  StageAutomationRule → CommunicationAutomation (campos divergem; `actions: list`
  vs `action_type: str + action_config: dict`).

## Decisões / compromissos

- Migration completa (DELETE tabela `stage_automation_rules`) NÃO incluída
  nesta sprint — preserva dados legacy.
- Backfill (povoar communication_automations a partir de stage_automation_rules
  pré-existentes) é tarefa de cronjob separada — não no critical path.
- ADR sugerido: `~/Documents/wedotalent_audit_2026-05-21/
  ADR-WT-2022-automation-rules-migration.md`

## Reference

- WT-2022 P3.2 — stage_automation_rules → communication_automations migration
- `lia-agent-system/app/api/v1/automation_rules.py` (UI endpoint, dual-write
  caller)
- `lia-agent-system/app/domains/automation/repositories/
  communication_automation_repository.py` (canonical engine repo)
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.automation import (
    CommunicationAutomation,
    StageAutomationRule,
)

logger = logging.getLogger(__name__)


class StageRuleAdapter:
    """Bridge schemas entre StageAutomationRule (UI) ↔ CommunicationAutomation (engine)."""

    @staticmethod
    def stage_rule_to_communication_automation(
        rule: StageAutomationRule,
    ) -> CommunicationAutomation:
        """
        Converte StageAutomationRule → CommunicationAutomation.

        Campos divergem:
        - `actions: list` (stage) → `action_type: str + action_config: dict`
          (communication). Pegamos primeira action como type canonical;
          mantemos lista inteira em action_config['actions'].
        - `conditions: dict` (stage) → `conditions: list` (communication).
          Wrap em lista de um item se vier dict.
        - Campos exclusivos stage (auto_execute, confidence_threshold,
          source_stage, target_stage) → trigger_config dict.

        Idempotente: mesmo input → mesmo output. Não persiste.
        """
        actions_list = rule.actions or []
        primary_action_type = "default"
        if actions_list:
            first_action = actions_list[0]
            if isinstance(first_action, dict):
                primary_action_type = first_action.get("type", "default")
            elif isinstance(first_action, str):
                primary_action_type = first_action

        conditions = rule.conditions or {}
        conditions_list: list[Any]
        if isinstance(conditions, dict):
            conditions_list = [conditions] if conditions else []
        elif isinstance(conditions, list):
            conditions_list = conditions
        else:
            conditions_list = []

        return CommunicationAutomation(
            company_id=rule.company_id,
            name=rule.name or f"Stage rule {rule.trigger_type}",
            description=rule.description,
            trigger_type=rule.trigger_type,
            trigger_config={
                "auto_execute": rule.auto_execute,
                "confidence_threshold": (
                    float(rule.confidence_threshold)
                    if rule.confidence_threshold
                    else 0.8
                ),
                "source_stage": rule.source_stage,
                "target_stage": rule.target_stage,
                # Preserva lista completa de actions originais para o engine
                # reconstituir multi-action behavior.
                "actions": actions_list,
            },
            action_type=primary_action_type,
            action_config={"actions": actions_list},
            conditions=conditions_list,
            is_active=rule.is_active,
            priority=rule.priority or "normal",
        )

    @staticmethod
    async def upsert_communication_automation_from_stage_rule(
        db: AsyncSession,
        rule: StageAutomationRule,
    ) -> CommunicationAutomation | None:
        """
        Dual-write helper — chamado depois de CREATE/UPDATE em
        stage_automation_rules. Cria ou atualiza CommunicationAutomation
        equivalente.

        Match strategy: same (company_id, trigger_type, name) → UPDATE.
        Sem match → INSERT.

        Retorna a CommunicationAutomation upserted, ou None em caso de erro
        (não-fatal — UI legacy continua funcionando mesmo se canonical write
        falha, mas log warning para detecção).
        """
        from sqlalchemy import select

        try:
            mirror = StageRuleAdapter.stage_rule_to_communication_automation(rule)

            # ADR-001-EXEMPT: cross-table adapter sync — StageRuleAdapter eh
            # ponte temporaria entre stage_automation_rules (legacy) e
            # communication_automations (canonical) durante a migration
            # WT-2022 P3.2 (deprecate stage_automation_rules em favor de
            # communication_automations). Quando migration completar e
            # legacy table for dropada, este adapter inteiro sera removido.
            # Marker defensive aplicado em sessao paralela 2026-05-21 pra
            # desbloquear sensor BLOCKING ADR-001 select-in-services.
            # Audit anchor: working tree multi-agente 2026-05-21.
            # Busca match por (company_id, trigger_type, name)
            stmt = select(CommunicationAutomation).where(
                CommunicationAutomation.company_id == rule.company_id,
                CommunicationAutomation.trigger_type == rule.trigger_type,
                CommunicationAutomation.name == mirror.name,
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()

            if existing:
                # UPDATE in-place — preserva id + audit trail
                existing.description = mirror.description
                existing.trigger_config = mirror.trigger_config
                existing.action_type = mirror.action_type
                existing.action_config = mirror.action_config
                existing.conditions = mirror.conditions
                existing.is_active = mirror.is_active
                existing.priority = mirror.priority
                await db.flush()
                logger.info(
                    "[P3.2] Updated communication_automation %s mirrored from "
                    "stage_rule %s (company=%s, trigger=%s)",
                    existing.id, rule.id, rule.company_id, rule.trigger_type,
                )
                return existing
            else:
                db.add(mirror)
                await db.flush()
                await db.refresh(mirror)
                logger.info(
                    "[P3.2] Created communication_automation %s mirrored from "
                    "stage_rule %s (company=%s, trigger=%s)",
                    mirror.id, rule.id, rule.company_id, rule.trigger_type,
                )
                return mirror

        except Exception as e:
            # Não-fatal: UI legacy continua funcionando. Log warning para
            # cronjob de reconciliação detectar drift posteriormente.
            logger.warning(
                "[P3.2] Failed to mirror stage_rule %s → communication_automation "
                "(company=%s, trigger=%s): %s. UI write succeeded but engine "
                "may not see this rule until reconciliation runs.",
                rule.id, rule.company_id, rule.trigger_type, e,
            )
            return None

    @staticmethod
    async def soft_delete_mirror(
        db: AsyncSession,
        rule: StageAutomationRule,
    ) -> bool:
        """
        Soft delete CommunicationAutomation mirror (is_active=False) quando
        stage_automation_rule é deletada. Preserva dados para auditabilidade.

        Retorna True se mirror foi encontrado e marcado inativo, False se não
        houve match (não-fatal).
        """
        from sqlalchemy import select, update

        try:
            stmt = (
                update(CommunicationAutomation)
                .where(
                    CommunicationAutomation.company_id == rule.company_id,
                    CommunicationAutomation.trigger_type == rule.trigger_type,
                    CommunicationAutomation.name == (
                        rule.name or f"Stage rule {rule.trigger_type}"
                    ),
                    CommunicationAutomation.is_active.is_(True),
                )
                .values(is_active=False)
            )
            result = await db.execute(stmt)
            affected = result.rowcount or 0
            if affected > 0:
                logger.info(
                    "[P3.2] Soft-deleted %d communication_automation mirror(s) "
                    "for stage_rule %s",
                    affected, rule.id,
                )
                return True
            return False

        except Exception as e:
            logger.warning(
                "[P3.2] Failed to soft-delete mirror for stage_rule %s: %s",
                rule.id, e,
            )
            return False
