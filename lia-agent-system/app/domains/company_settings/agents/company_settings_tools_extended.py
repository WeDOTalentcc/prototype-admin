"""
WT-2022 Fase 4: Tools dedicadas para company_settings (extensão de company_tool_registry).

Decisão Paulo 2026-05-21: 8 tools existentes em company_tool_registry cobrem
genericamente via save_company_field/save_hiring_policy. Mas LIA precisa
raciocinar pra montar patch nested correto — slow + error-prone.

Status:
    ✅ 3 tools dedicadas criadas (este arquivo)
    ❌ TOOL_DEFINITIONS de company_tool_registry deve referenciar essas tools
    ❌ Bridge UnifiedChat lateral (events lia:settings-action) — wire frontend

## Tools criadas

1. **toggle_learning_loop(loop_name, value)** — liga/desliga loop específico
2. **toggle_lia_field(field_name, value, instruction?)** — controla LIA field toggle/instruction
3. **record_dsr_action(request_id, action, response?)** — workflow DSR

## Pattern de uso (LIA agent decide via prompt)

    Recrutador: "Desliga o learning loop de Big5 cultura"
    LIA chama: toggle_learning_loop(loop_name="bigfive_company_culture", value=False)

    Recrutador: "Marca DSR ABC123 como concluído com resposta XYZ"
    LIA chama: record_dsr_action(request_id="ABC123", action="complete", response="XYZ")

## Wire em company_tool_registry.py

```python
# Adicionar imports
from app.domains.company_settings.agents.company_settings_tools_extended import (
    _wrap_toggle_learning_loop,
    _wrap_toggle_lia_field,
    _wrap_record_dsr_action,
)

# Adicionar a TOOL_DEFINITIONS list:
ToolDefinition(
    name="toggle_learning_loop",
    description="Liga/desliga um learning loop especifico (Big5, JD similar, WSI effectiveness)",
    parameters={...},
    handler=_wrap_toggle_learning_loop,
),
# ... idem para outros 2
```
"""
from __future__ import annotations

import logging
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


VALID_LEARNING_LOOPS = {
    "enabled",
    "bigfive_company_culture",
    "bigfive_department_history",
    "wsi_question_effectiveness",
    "jd_similar_suggestion",
}


@tool_handler("company_settings")
async def _wrap_toggle_learning_loop(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4 Tool: liga/desliga learning loop especifico via chat.

    Wrapper canonical sobre save_hiring_policy — LIA nao precisa raciocinar
    sobre nested JSONB patch.

    Args (via kwargs after tool_handler injection):
        loop_name: enabled|bigfive_company_culture|bigfive_department_history|
                   wsi_question_effectiveness|jd_similar_suggestion
        value: True | False
        company_id: do JWT (injetado por tool_handler)
        db: AsyncSession (injetado)
    """
    loop_name = kwargs.get("loop_name", "")
    value = kwargs.get("value")
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if loop_name not in VALID_LEARNING_LOOPS:
        return {
            "success": False,
            "error": f"loop_name invalido. Valores aceitos: {sorted(VALID_LEARNING_LOOPS)}",
        }
    if not isinstance(value, bool):
        return {"success": False, "error": "value deve ser True ou False"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}

    try:
        # Use canonical helper learning_loops_toggles + update via repo
        from app.shared.services.learning_loops_toggles import (
            load_learning_loops_toggles,
        )
        from app.domains.hiring_policy.repositories.hiring_policy_repository import (
            HiringPolicyRepository,
        )

        current = await load_learning_loops_toggles(company_id, db)
        updated = {**current, loop_name: value}

        repo = HiringPolicyRepository(db)
        policy = await repo.get_by_company(company_id)
        if not policy:
            return {"success": False, "error": "CompanyHiringPolicy not found"}

        rules = dict(getattr(policy, "automation_rules", {}) or {})
        rules["learning_loops"] = updated
        policy.automation_rules = rules
        await db.commit()

        # WT-2022 Fase 4 bridge: formato canonical ChatResponse (ui_action=str,
        # ui_action_params=dict) — useUIAction.dispatch lida com 'settings_open_tab'
        # e dispatcha o CustomEvent 'lia:settings-action' que SettingsPageEnhanced escuta.
        return {
            "success": True,
            "loop_name": loop_name,
            "value": value,
            "ui_action": "settings_open_tab",
            "ui_action_params": {
                "section": "minha-empresa",
                "subsection": "learning-loops",
            },
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4: toggle_learning_loop failed: %s", exc, exc_info=True
        )
        return {"success": False, "error": str(exc)[:200]}


@tool_handler("company_settings")
async def _wrap_toggle_lia_field(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4 Tool: liga/desliga lia_field toggle + opcional instruction.

    Args:
        field_name: ex 'mission', 'vision', 'tech_stack', 'departments', etc.
        value: True | False (toggle)
        instruction: opcional, string customizada
    """
    field_name = kwargs.get("field_name", "")
    value = kwargs.get("value")
    instruction = kwargs.get("instruction")
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if not field_name:
        return {"success": False, "error": "field_name required"}
    if not isinstance(value, bool):
        return {"success": False, "error": "value deve ser True ou False"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}

    try:
        from app.domains.cv_screening.services.lia_field_config_service import (
            LiaFieldConfigService,
        )

        svc = LiaFieldConfigService(db)
        await svc.set_toggle(
            company_id=company_id,
            field_name=field_name,
            value=value,
        )
        if instruction is not None:
            await svc.set_instruction(
                company_id=company_id,
                field_name=field_name,
                instruction=instruction,
            )

        # WT-2022 Fase 4 bridge: formato canonical ChatResponse.
        return {
            "success": True,
            "field_name": field_name,
            "value": value,
            "instruction_updated": instruction is not None,
            "ui_action": "settings_open_tab",
            "ui_action_params": {
                "section": "minha-empresa",
                "subsection": "instrucoes-lia",
                "field": field_name,
            },
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4: toggle_lia_field failed: %s", exc, exc_info=True
        )
        return {"success": False, "error": str(exc)[:200]}


@tool_handler("company_settings")
async def _wrap_record_dsr_action(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4 Tool: workflow DSR via chat (assign/verify/process/complete/reject).

    Args:
        request_id: UUID do DSR
        action: assign|verify-identity|process|complete|reject
        response: required se action=complete
        rejection_reason: required se action=reject
        assignee_email: required se action=assign
    """
    request_id = kwargs.get("request_id", "")
    action = kwargs.get("action", "")
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    VALID_ACTIONS = {"assign", "verify-identity", "process", "complete", "reject"}
    if action not in VALID_ACTIONS:
        return {"success": False, "error": f"action invalida. Aceitos: {sorted(VALID_ACTIONS)}"}
    if not request_id:
        return {"success": False, "error": "request_id required"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}

    try:
        from uuid import UUID
        from app.repositories.data_subject_repository import (
            DataSubjectRepository,
            DsrExecutorFailedError,
        )

        repo = DataSubjectRepository(db)
        request_uuid = UUID(request_id)
        company_uuid = UUID(company_id)
        dsr = await repo.get_by_id_and_company(request_uuid, company_uuid)
        if not dsr:
            return {"success": False, "error": "DSR not found"}

        audit_entry = {
            "actor": "lia_chat",
            "action": action,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

        if action == "complete":
            response = kwargs.get("response", "")
            if not response:
                return {"success": False, "error": "response required for complete"}
            try:
                dsr = await repo.complete_request(
                    dsr, response=response, evidence_files=[], audit_entry=audit_entry,
                )
            except DsrExecutorFailedError as exc:
                return {
                    "success": False,
                    "error": f"DSR executor failed (compliance gate): {exc}",
                    "executor_failed": True,
                }
        elif action == "reject":
            reason = kwargs.get("rejection_reason", "")
            if not reason:
                return {"success": False, "error": "rejection_reason required for reject"}
            dsr = await repo.reject_request(dsr, reason, audit_entry)
        elif action == "process":
            dsr = await repo.start_processing(dsr, audit_entry)
        else:
            return {
                "success": False,
                "error": f"action '{action}' nao implementada nesta tool — use endpoint REST",
            }

        # WT-2022 Fase 4 bridge: formato canonical ChatResponse.
        return {
            "success": True,
            "request_id": str(dsr.id),
            "new_status": dsr.status,
            "ui_action": "settings_open_tab",
            "ui_action_params": {
                "section": "fairness-compliance",
                "subsection": "lgpd-candidatos",
                "field": str(dsr.id),
            },
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4: record_dsr_action failed: %s", exc, exc_info=True
        )
        return {"success": False, "error": str(exc)[:200]}


# ToolDefinition exports pra registrar em company_tool_registry.TOOL_DEFINITIONS
# Caller adiciona a lista existente:
#
#   from app.domains.company_settings.agents.company_settings_tools_extended import (
#       FASE_4_TOOL_DEFINITIONS,
#   )
#   TOOL_DEFINITIONS.extend(FASE_4_TOOL_DEFINITIONS)
def get_fase_4_tool_definitions():
    """Retorna list de ToolDefinition pra registrar em TOOL_DEFINITIONS.

    Importa lazy pra evitar circular deps.
    """
    try:
        from app.shared.tool_governance import ToolDefinition
    except ImportError:
        # Fallback genérico
        class ToolDefinition:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

    return [
        ToolDefinition(
            name="toggle_learning_loop",
            description="Liga/desliga um learning loop especifico (Big5, JD similar, WSI effectiveness)",
            parameters={
                "type": "object",
                "properties": {
                    "loop_name": {
                        "type": "string",
                        "enum": list(VALID_LEARNING_LOOPS),
                        "description": "Nome do loop",
                    },
                    "value": {"type": "boolean", "description": "True liga, False desliga"},
                },
                "required": ["loop_name", "value"],
            },
            handler=_wrap_toggle_learning_loop,
        ),
        ToolDefinition(
            name="toggle_lia_field",
            description="Liga/desliga toggle de campo LIA + opcional adiciona instrucao customizada",
            parameters={
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string",
                        "description": "Campo (mission, vision, tech_stack, departments, etc)",
                    },
                    "value": {"type": "boolean"},
                    "instruction": {"type": "string", "description": "Opcional"},
                },
                "required": ["field_name", "value"],
            },
            handler=_wrap_toggle_lia_field,
        ),
        ToolDefinition(
            name="record_dsr_action",
            description="Workflow DSR via chat: assign, verify-identity, process, complete ou reject",
            parameters={
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "UUID do DSR"},
                    "action": {
                        "type": "string",
                        "enum": ["assign", "verify-identity", "process", "complete", "reject"],
                    },
                    "response": {"type": "string", "description": "Required se action=complete"},
                    "rejection_reason": {"type": "string", "description": "Required se action=reject"},
                    "assignee_email": {"type": "string", "description": "Required se action=assign"},
                },
                "required": ["request_id", "action"],
            },
            handler=_wrap_record_dsr_action,
        ),
    ]


FASE_4_TOOL_DEFINITIONS = []  # populated lazily via get_fase_4_tool_definitions()


# ════════════════════════════════════════════════════════════════════════════
# WT-2022 Fase 4 Extended — 5 tools high-impact
# ════════════════════════════════════════════════════════════════════════════

VALID_ALERT_IDS = {
    "sla_warning",
    "interview_reminder",
    "feedback_pending",
    "candidate_waiting",
    "anomaly_detected",
    "monthly_goal_at_risk",
}
VALID_ALERT_CHANNELS = {"email", "in_app", "teams", "whatsapp", "both", "none"}

# Canonical mapping alert_id → numeric "id" usado em AlertConfig.alerts JSONB
# (storage usa DEFAULT_ALERTS com ids "1"-"5", ver app/api/v1/alerts.py).
ALERT_ID_TO_STORAGE = {
    "sla_warning": "1",
    "monthly_goal_at_risk": "2",
    "candidate_waiting": "3",
    "interview_reminder": "4",
    "feedback_pending": "5",
    "anomaly_detected": "6",  # criado on-demand se não existir
}

ALERT_ID_TO_LABEL = {
    "sla_warning": "SLA Próximo do Vencimento",
    "monthly_goal_at_risk": "Meta Mensal em Risco",
    "candidate_waiting": "Candidato Sem Interação",
    "interview_reminder": "Entrevista Não Confirmada",
    "feedback_pending": "Feedback Pendente",
    "anomaly_detected": "Anomalia Detectada",
}


@tool_handler("company_settings")
async def _wrap_toggle_communication_alert(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4.4: liga/desliga (ou troca canal de) um alerta de comunicacao.

    DEPRECATED 2026-05-22 (ADR-WT-2025 Sprint B+C):
    Esta tool escreve em AlertConfig.alerts (JSONB legacy, 5 alert_ids hardcoded).
    Canonical eh AlertPreference - proactive_detector_service.py le APENAS de la.
    Migration alembic 170 backfilla rows legacy -> canonical.

    Read-shadow pattern: mantem write para compat 1 release cycle. Depois
    de migration 170 confirmar backfill, substituir esta tool por uma que
    escreve em AlertPreference (via AlertRepository.upsert_preference_by_type).
    Tracking: WT-2026.
    """
    alert_id = kwargs.get("alert_id", "")
    enabled = kwargs.get("enabled")
    channel = kwargs.get("channel")
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if alert_id not in VALID_ALERT_IDS:
        return {"success": False, "error": f"alert_id invalido. Aceitos: {sorted(VALID_ALERT_IDS)}"}
    if enabled is None and channel is None:
        return {"success": False, "error": "informe ao menos um: enabled (bool) ou channel (str)"}
    if enabled is not None and not isinstance(enabled, bool):
        return {"success": False, "error": "enabled deve ser True ou False"}
    if channel is not None and channel not in VALID_ALERT_CHANNELS:
        return {"success": False, "error": f"channel invalido. Aceitos: {sorted(VALID_ALERT_CHANNELS)}"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}
    if db is None:
        return {"success": False, "error": "db session not injected"}

    try:
        from datetime import datetime
        from app.repositories.alert_repository import (
            AlertRepository,
        )

        repo = AlertRepository(db)
        config = await repo.get_active_config_for_company(company_id)
        storage_id = ALERT_ID_TO_STORAGE.get(alert_id, alert_id)

        alerts_list: list[dict[str, Any]] = (
            [dict(a) for a in (config.alerts or [])] if config and config.alerts else []
        )

        idx = next(
            (i for i, a in enumerate(alerts_list) if str(a.get("id")) == storage_id),
            None,
        )
        if idx is None:
            alerts_list.append({
                "id": storage_id,
                "name": ALERT_ID_TO_LABEL.get(alert_id, alert_id),
                "description": f"Alerta {alert_id}",
                "enabled": True if enabled is None else enabled,
                "channel": channel or "email",
            })
        else:
            if enabled is not None:
                alerts_list[idx]["enabled"] = enabled
            if channel is not None:
                alerts_list[idx]["channel"] = channel

        if config:
            await repo.update_config(config, {
                "alerts": alerts_list,
                "updated_at": datetime.utcnow(),
            })
        else:
            await repo.create_config({
                "company_id": company_id,
                "alerts": alerts_list,
                "briefing_frequency": "daily",
                "is_active": True,
            })

        return {
            "success": True,
            "alert_id": alert_id,
            "enabled": enabled,
            "channel": channel,
            "ui_action": "settings_open_tab",
            "ui_action_params": {
                "section": "comunicacao-alertas",
                "field": alert_id,
            },
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4.4: toggle_communication_alert failed: %s",
            exc, exc_info=True,
        )
        return {"success": False, "error": str(exc)[:200]}


@tool_handler("company_settings")
async def _wrap_update_email_signature(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4.5: atualiza signature text e/ou html em CommunicationSettings."""
    text = kwargs.get("text")
    html = kwargs.get("html")
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if not text and not html:
        return {"success": False, "error": "text ou html required (ao menos um)"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}
    if db is None:
        return {"success": False, "error": "db session not injected"}
    if text is not None and len(text) > 4000:
        return {"success": False, "error": "text excede 4000 chars"}
    if html is not None and len(html) > 16000:
        return {"success": False, "error": "html excede 16000 chars"}

    try:
        from app.domains.communication.repositories.communication_settings_repository import (
            CommunicationSettingsRepository,
        )

        repo = CommunicationSettingsRepository(db)
        update_data: dict[str, Any] = {}
        if text is not None:
            update_data["signature"] = text
        if html is not None:
            update_data["signature_html"] = html

        await repo.upsert(company_id, update_data)
        await db.commit()

        return {
            "success": True,
            "signature_updated": True,
            "text_updated": text is not None,
            "html_updated": html is not None,
            "ui_action": "settings_open_tab",
            "ui_action_params": {"section": "templates-assinatura"},
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4.5: update_email_signature failed: %s",
            exc, exc_info=True,
        )
        return {"success": False, "error": str(exc)[:200]}


VALID_PIPELINE_ACTIONS = {"create", "update", "delete", "toggle_active"}


@tool_handler("company_settings")
async def _wrap_configure_pipeline_stage(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4.6: CRUD de pipeline stages (RecruitmentStage canonical)."""
    from uuid import UUID

    action = kwargs.get("action", "")
    stage_data = kwargs.get("stage_data", {}) or {}
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if action not in VALID_PIPELINE_ACTIONS:
        return {"success": False, "error": f"action invalida. Aceitas: {sorted(VALID_PIPELINE_ACTIONS)}"}
    if not isinstance(stage_data, dict):
        return {"success": False, "error": "stage_data deve ser objeto"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}
    if db is None:
        return {"success": False, "error": "db session not injected"}

    try:
        from app.domains.recruitment.repositories.recruitment_stage_repository import (
            RecruitmentStageRepository,
        )

        repo = RecruitmentStageRepository(db)
        result_payload: dict[str, Any] = {}

        if action == "create":
            name = stage_data.get("name")
            display_name = stage_data.get("display_name") or name
            if not name:
                return {"success": False, "error": "stage_data.name required p/ create"}
            create_payload = {
                "company_id": company_id,
                "name": name,
                "display_name": display_name,
                "description": stage_data.get("description"),
                "stage_order": stage_data.get("stage_order", 0),
                "color": stage_data.get("color"),
                "icon": stage_data.get("icon"),
                "stage_type": stage_data.get("stage_type", "active"),
                "default_channel": stage_data.get("default_channel", "email"),
                "action_behavior": stage_data.get("action_behavior", "passive"),
                "is_active": True,
                "is_system": False,
                "stage_category": stage_data.get("stage_category", "custom"),
            }
            stage = await repo.create(create_payload)
            result_payload = {"id": str(stage.id), "name": stage.name}
        else:
            stage_id_str = stage_data.get("id")
            if not stage_id_str:
                return {"success": False, "error": "stage_data.id required"}
            try:
                stage_uuid = UUID(str(stage_id_str))
            except ValueError:
                return {"success": False, "error": "stage_data.id invalido (UUID esperado)"}

            existing = await repo.get_by_id(stage_uuid)
            if not existing:
                return {"success": False, "error": "stage nao encontrado"}
            # Multi-tenancy fail-closed
            if str(existing.company_id) != str(company_id):
                return {"success": False, "error": "stage pertence a outro tenant (cross-tenant bloqueado)"}
            if getattr(existing, "is_system", False) and action == "delete":
                return {"success": False, "error": "stage de sistema nao pode ser deletado"}

            if action == "update":
                allowed_keys = {
                    "display_name", "description", "stage_order", "color", "icon",
                    "sla_hours", "default_channel", "action_behavior",
                }
                update_payload = {k: v for k, v in stage_data.items() if k in allowed_keys}
                if not update_payload:
                    return {
                        "success": False,
                        "error": f"nenhum campo valido em stage_data. Aceitos: {sorted(allowed_keys)}",
                    }
                await repo.update(stage_uuid, update_payload)
                result_payload = {"id": str(stage_uuid), "updated": list(update_payload.keys())}
            elif action == "delete":
                await repo.soft_delete(stage_uuid)
                result_payload = {"id": str(stage_uuid), "deleted": True}
            elif action == "toggle_active":
                is_active = stage_data.get("is_active")
                if not isinstance(is_active, bool):
                    return {"success": False, "error": "stage_data.is_active deve ser bool em toggle_active"}
                await repo.update(stage_uuid, {"is_active": is_active})
                result_payload = {"id": str(stage_uuid), "is_active": is_active}

        return {
            "success": True,
            "action": action,
            "stage": result_payload,
            "ui_action": "settings_open_tab",
            "ui_action_params": {"section": "pipeline"},
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4.6: configure_pipeline_stage failed: %s",
            exc, exc_info=True,
        )
        return {"success": False, "error": str(exc)[:200]}


VALID_SCREENING_ACTIONS = {"add", "remove", "update"}
VALID_QUESTION_TYPES = {"text", "single_choice", "multiple_choice", "yes_no", "scale"}


@tool_handler("company_settings")
async def _wrap_configure_screening_questions(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4.7: CRUD de eligibility screening questions."""
    from uuid import UUID

    action = kwargs.get("action", "")
    question_data = kwargs.get("question_data", {}) or {}
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if action not in VALID_SCREENING_ACTIONS:
        return {"success": False, "error": f"action invalida. Aceitas: {sorted(VALID_SCREENING_ACTIONS)}"}
    if not isinstance(question_data, dict):
        return {"success": False, "error": "question_data deve ser objeto"}
    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}
    if db is None:
        return {"success": False, "error": "db session not injected"}

    try:
        from app.domains.recruitment.repositories.screening_question_repository import (
            ScreeningQuestionRepository,
        )

        repo = ScreeningQuestionRepository(db)
        result_payload: dict[str, Any] = {}

        if action == "add":
            question_text = question_data.get("question_text")
            if not question_text:
                return {"success": False, "error": "question_data.question_text required"}
            q_type = question_data.get("question_type", "text")
            if q_type not in VALID_QUESTION_TYPES:
                return {
                    "success": False,
                    "error": f"question_type invalido. Aceitos: {sorted(VALID_QUESTION_TYPES)}",
                }
            next_order = (await repo.get_last_order(company_id)) + 1
            create_payload = {
                "company_id": company_id,
                "question_text": question_text,
                "question_type": q_type,
                "options": question_data.get("options"),
                "is_required": bool(question_data.get("is_required", True)),
                "is_eliminatory": bool(question_data.get("is_eliminatory", False)),
                "expected_answer": question_data.get("expected_answer"),
                "category": question_data.get("category"),
                "order": question_data.get("order", next_order),
                "is_active": True,
            }
            q = await repo.create(create_payload)
            result_payload = {"id": str(q.id), "question_text": str(q.question_text)[:80]}
        else:
            q_id_str = question_data.get("id")
            if not q_id_str:
                return {"success": False, "error": "question_data.id required"}
            try:
                q_uuid = UUID(str(q_id_str))
            except ValueError:
                return {"success": False, "error": "question_data.id invalido (UUID esperado)"}
            existing = await repo.get_by_id(q_uuid)
            if not existing:
                return {"success": False, "error": "question nao encontrada"}
            if str(existing.company_id) != str(company_id):
                return {"success": False, "error": "question pertence a outro tenant (cross-tenant bloqueado)"}

            if action == "update":
                allowed_keys = {
                    "question_text", "question_type", "options", "is_required",
                    "is_eliminatory", "expected_answer", "category", "order", "is_active",
                }
                update_payload = {k: v for k, v in question_data.items() if k in allowed_keys}
                if "question_type" in update_payload and update_payload["question_type"] not in VALID_QUESTION_TYPES:
                    return {
                        "success": False,
                        "error": f"question_type invalido. Aceitos: {sorted(VALID_QUESTION_TYPES)}",
                    }
                if not update_payload:
                    return {"success": False, "error": "nenhum campo valido em question_data"}
                await repo.update(q_uuid, update_payload)
                result_payload = {"id": str(q_uuid), "updated": list(update_payload.keys())}
            elif action == "remove":
                await repo.soft_delete(q_uuid)
                result_payload = {"id": str(q_uuid), "removed": True}

        return {
            "success": True,
            "action": action,
            "question": result_payload,
            "ui_action": "settings_open_tab",
            "ui_action_params": {"section": "screening"},
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4.7: configure_screening_questions failed: %s",
            exc, exc_info=True,
        )
        return {"success": False, "error": str(exc)[:200]}


@tool_handler("company_settings")
async def _wrap_set_communication_schedule(**kwargs: Any) -> dict[str, Any]:
    """WT-2022 Fase 4.8: configura janela LGPD outbound (CommunicationSettings)."""
    sending_hours_start = kwargs.get("sending_hours_start")
    sending_hours_end = kwargs.get("sending_hours_end")
    respect_weekends = kwargs.get("respect_weekends")
    max_messages_per_day = kwargs.get("max_messages_per_day")
    company_id = kwargs.get("company_id")
    db = kwargs.get("db")

    if not company_id:
        return {"success": False, "error": "company_id required from JWT"}
    if db is None:
        return {"success": False, "error": "db session not injected"}

    if (
        sending_hours_start is None
        and sending_hours_end is None
        and respect_weekends is None
        and max_messages_per_day is None
    ):
        return {
            "success": False,
            "error": "informe ao menos um campo: sending_hours_start, sending_hours_end, respect_weekends ou max_messages_per_day",
        }

    if sending_hours_start is not None:
        if not isinstance(sending_hours_start, int) or isinstance(sending_hours_start, bool):
            return {"success": False, "error": "sending_hours_start deve ser int"}
        if not (6 <= sending_hours_start <= 12):
            return {"success": False, "error": "sending_hours_start deve estar entre 6 e 12"}
    if sending_hours_end is not None:
        if not isinstance(sending_hours_end, int) or isinstance(sending_hours_end, bool):
            return {"success": False, "error": "sending_hours_end deve ser int"}
        if not (18 <= sending_hours_end <= 22):
            return {"success": False, "error": "sending_hours_end deve estar entre 18 e 22"}
    if (
        sending_hours_start is not None
        and sending_hours_end is not None
        and sending_hours_start >= sending_hours_end
    ):
        return {"success": False, "error": "sending_hours_start deve ser < sending_hours_end"}
    if respect_weekends is not None and not isinstance(respect_weekends, bool):
        return {"success": False, "error": "respect_weekends deve ser bool"}
    if max_messages_per_day is not None:
        if not isinstance(max_messages_per_day, int) or isinstance(max_messages_per_day, bool):
            return {"success": False, "error": "max_messages_per_day deve ser int"}
        if not (1 <= max_messages_per_day <= 50):
            return {"success": False, "error": "max_messages_per_day deve estar entre 1 e 50"}

    try:
        from app.domains.communication.repositories.communication_settings_repository import (
            CommunicationSettingsRepository,
        )

        repo = CommunicationSettingsRepository(db)
        update_data: dict[str, Any] = {}
        if sending_hours_start is not None:
            update_data["sending_hours_start"] = sending_hours_start
        if sending_hours_end is not None:
            update_data["sending_hours_end"] = sending_hours_end
        if respect_weekends is not None:
            update_data["respect_weekends"] = respect_weekends
        if max_messages_per_day is not None:
            update_data["max_messages_per_day"] = max_messages_per_day

        await repo.upsert(company_id, update_data)
        await db.commit()

        return {
            "success": True,
            "schedule_updated": True,
            "updated_fields": list(update_data.keys()),
            "ui_action": "settings_open_tab",
            "ui_action_params": {"section": "comunicacao-alertas"},
        }
    except Exception as exc:
        logger.error(
            "WT-2022 Fase 4.8: set_communication_schedule failed: %s",
            exc, exc_info=True,
        )
        return {"success": False, "error": str(exc)[:200]}


def get_fase_4_extended_tool_definitions():
    """Retorna 5 ToolDefinition adicionais (Fase 4 Extended) pra registrar em TOOL_DEFINITIONS.

    Importa lazy pra evitar circular deps.
    """
    try:
        from app.shared.tool_governance import ToolDefinition
    except ImportError:
        class ToolDefinition:  # type: ignore[no-redef]
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

    return [
        ToolDefinition(
            name="toggle_communication_alert",
            description="Liga/desliga ou troca canal de um alerta de comunicacao (sla, lembrete entrevista, feedback pendente, etc)",
            parameters={
                "type": "object",
                "properties": {
                    "alert_id": {"type": "string", "enum": sorted(VALID_ALERT_IDS)},
                    "enabled": {"type": "boolean"},
                    "channel": {"type": "string", "enum": sorted(VALID_ALERT_CHANNELS)},
                },
                "required": ["alert_id"],
            },
            handler=_wrap_toggle_communication_alert,
        ),
        ToolDefinition(
            name="update_email_signature",
            description="Atualiza assinatura de email (texto e/ou HTML) usada nas comunicacoes outbound",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Assinatura em texto puro"},
                    "html": {"type": "string", "description": "Assinatura em HTML"},
                },
                "required": [],
            },
            handler=_wrap_update_email_signature,
        ),
        ToolDefinition(
            name="configure_pipeline_stage",
            description="CRUD de pipeline stages: create/update/delete/toggle_active",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": sorted(VALID_PIPELINE_ACTIONS)},
                    "stage_data": {
                        "type": "object",
                        "description": "create: name+display_name; update/delete/toggle_active: id obrigatorio",
                    },
                },
                "required": ["action", "stage_data"],
            },
            handler=_wrap_configure_pipeline_stage,
        ),
        ToolDefinition(
            name="configure_screening_questions",
            description="CRUD de perguntas de triagem (CompanyScreeningQuestion): add/update/remove",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": sorted(VALID_SCREENING_ACTIONS)},
                    "question_data": {
                        "type": "object",
                        "description": "add: question_text obrigatorio; update/remove: id obrigatorio",
                    },
                },
                "required": ["action", "question_data"],
            },
            handler=_wrap_configure_screening_questions,
        ),
        ToolDefinition(
            name="set_communication_schedule",
            description="Configura janela LGPD outbound: sending_hours_start (6-12), sending_hours_end (18-22), respect_weekends, max_messages_per_day (1-50)",
            parameters={
                "type": "object",
                "properties": {
                    "sending_hours_start": {"type": "integer", "minimum": 6, "maximum": 12},
                    "sending_hours_end": {"type": "integer", "minimum": 18, "maximum": 22},
                    "respect_weekends": {"type": "boolean"},
                    "max_messages_per_day": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": [],
            },
            handler=_wrap_set_communication_schedule,
        ),
    ]


FASE_4_EXTENDED_TOOL_DEFINITIONS = []  # populated lazily
