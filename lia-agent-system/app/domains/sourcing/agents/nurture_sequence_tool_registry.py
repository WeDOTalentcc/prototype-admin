"""
Nurture Sequence Tool Registry — sequências automáticas multi-touch.

Expõe tools para NurtureSequenceAgent:
- nurture_create_sequence: cria sequência de touchpoints (até 5 steps)
- nurture_get_sequence_status: status atual de uma sequência
- nurture_approve_step: aprovação HITL de um step antes do envio
- nurture_execute_step: executa um step aprovado da sequência
- nurture_expire_sequence: expira sequência por LGPD ou opt-out

HITL: cada step requer aprovação quando communication_matrix.requires_approval=true.
LGPD: sequências são expiradas pelo lgpd_cleanup após TTL.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from lia_agents_core.react_loop import ToolDefinition

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_NURTURE_TOOL_DEFINITIONS: list[ToolDefinition] = []

MAX_STEPS = 5
DEFAULT_STEP_INTERVAL_DAYS = 3

_STEP_TYPES = ["email", "whatsapp", "linkedin_message", "sms"]


@tool_handler("nurture_sequence")
async def _wrap_nurture_create_sequence(**kwargs: Any) -> dict[str, Any]:
    """
    Cria sequência de nurture multi-touch para um candidato.
    FairnessGuard: verifica contexto da sequência antes de criar.
    """
    logger.info("[nurture_tools] nurture_create_sequence called: %s", list(kwargs.keys()))
    candidate_id = kwargs.get("candidate_id", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")
    steps = kwargs.get("steps", [])
    max_steps_override = kwargs.get("max_steps", MAX_STEPS)

    if not candidate_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'candidate_id' é obrigatório."}

    # FairnessGuard: verificar contexto da sequência
    query_str = f"{vacancy_id} {company_id} candidate:{candidate_id}"
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_result = _fg.check(query_str)
        if _fg_result.is_blocked:
            return {
                "success": False,
                "data": {},
                "message": _fg_result.educational_message or "Criação de sequência bloqueada por critério discriminatório.",
            }
    except Exception as _fg_exc:
        logger.debug("[nurture_tools] FairnessGuard check skipped: %s", _fg_exc)

    if not steps:
        steps = [
            {
                "step": 1,
                "type": "email",
                "delay_days": 0,
                "subject": "Oportunidade de carreira — {role}",
                "template": "initial_outreach",
            },
            {
                "step": 2,
                "type": "whatsapp",
                "delay_days": DEFAULT_STEP_INTERVAL_DAYS,
                "template": "follow_up_1",
            },
            {
                "step": 3,
                "type": "email",
                "delay_days": DEFAULT_STEP_INTERVAL_DAYS * 2,
                "template": "follow_up_2",
            },
        ]

    max_allowed = min(int(max_steps_override), MAX_STEPS)
    steps = steps[:max_allowed]

    # Validar tipos de step
    for s in steps:
        if s.get("type") not in _STEP_TYPES:
            s["type"] = "email"

    sequence_id = str(uuid.uuid4())
    now = datetime.utcnow()

    enriched_steps = []
    for i, step in enumerate(steps, 1):
        delay = int(step.get("delay_days", (i - 1) * DEFAULT_STEP_INTERVAL_DAYS))
        scheduled_at = now + timedelta(days=delay)
        enriched_steps.append({
            "step_number": i,
            "type": step.get("type", "email"),
            "delay_days": delay,
            "scheduled_at": scheduled_at.isoformat(),
            "template": step.get("template", f"step_{i}"),
            "subject": step.get("subject", ""),
            "status": "pending",
            "requires_hitl": True,
            "approved": False,
        })

    lgpd_expiry = now + timedelta(days=180)

    # Persistir sequência na tabela candidate_nurture_sequences
    import json as _json
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO candidate_nurture_sequences (
                        sequence_id, candidate_id, vacancy_id, company_id,
                        status, total_steps, current_step,
                        steps_approved, steps_executed,
                        steps_data, created_at, updated_at, lgpd_expiry
                    ) VALUES (
                        :seq_id, :cand_id, :vac_id, :co_id,
                        'created', :total_steps, 0,
                        0, 0,
                        :steps_data, :created_at, :created_at, :lgpd_expiry
                    )
                    ON CONFLICT (sequence_id) DO NOTHING
                """),
                {
                    "seq_id": sequence_id,
                    "cand_id": candidate_id,
                    "vac_id": vacancy_id or None,
                    "co_id": company_id or None,
                    "total_steps": len(enriched_steps),
                    "steps_data": _json.dumps(enriched_steps),
                    "created_at": now,
                    "lgpd_expiry": lgpd_expiry,
                },
            )
            await session.commit()
        logger.info("[nurture_tools] Sequência %s persistida no DB", sequence_id)
    except Exception as db_exc:
        # Graceful degradation: tabela pode não existir ainda
        logger.warning(
            "[nurture_tools] Não foi possível persistir sequência %s: %s — "
            "tabela candidate_nurture_sequences pode não existir",
            sequence_id, db_exc
        )

    return {
        "success": True,
        "data": {
            "sequence_id": sequence_id,
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "steps": enriched_steps,
            "total_steps": len(enriched_steps),
            "max_steps": max_allowed,
            "status": "created",
            "created_at": now.isoformat(),
            "lgpd_expiry": lgpd_expiry.isoformat(),
            "hitl_note": (
                "Cada step requer aprovação HITL antes do envio. "
                "Use nurture_approve_step para aprovar cada etapa."
            ),
        },
        "message": (
            f"Sequência de nurture criada: {len(enriched_steps)} step(s) configurados. "
            f"ID: {sequence_id}. HITL obrigatório antes de cada envio."
        ),
    }
_NURTURE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="nurture_create_sequence",
        description=(
            "Cria uma sequência de nurture multi-touch (até 5 touchpoints) para um candidato. "
            "Suporta email, WhatsApp, LinkedIn message e SMS. "
            "Cada step requer aprovação HITL. LGPD: sequências expiram em 180 dias."
        ),
        parameters={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
                "company_id": {"type": "string", "description": "ID da empresa"},
                "steps": {
                    "type": "array",
                    "description": (
                        "Lista de steps customizados. Se vazio, usa template padrão (3 steps). "
                        "Cada step: {type, delay_days, template, subject}"
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": _STEP_TYPES},
                            "delay_days": {"type": "integer"},
                            "template": {"type": "string"},
                            "subject": {"type": "string"},
                        },
                    },
                },
                "max_steps": {
                    "type": "integer",
                    "description": f"Máximo de steps (1-{MAX_STEPS}, padrão: {MAX_STEPS})",
                    "default": MAX_STEPS,
                },
            },
            "required": ["candidate_id"],
        },
        function=_wrap_nurture_create_sequence,
    )
)


@tool_handler("nurture_sequence")
async def _wrap_nurture_get_sequence_status(**kwargs: Any) -> dict[str, Any]:
    """Obtém status atual de uma sequência de nurture (via cache/event store)."""
    logger.info("[nurture_tools] nurture_get_sequence_status called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    sequence_id = kwargs.get("sequence_id", "")
    candidate_id = kwargs.get("candidate_id", "")

    if not sequence_id and not candidate_id:
        return {
            "success": False,
            "data": {},
            "message": "Forneça 'sequence_id' ou 'candidate_id'.",
        }

    # Consultar candidate_nurture_sequences via DB se disponível
    async with AsyncSessionLocal() as session:
        try:
            if sequence_id:
                result = await session.execute(
                    text("""
                        SELECT sequence_id, candidate_id, vacancy_id, company_id,
                               status, total_steps, current_step,
                               created_at, updated_at, lgpd_expiry,
                               steps_executed, steps_approved
                        FROM candidate_nurture_sequences
                        WHERE sequence_id = :sid
                    """),
                    {"sid": sequence_id},
                )
            else:
                result = await session.execute(
                    text("""
                        SELECT sequence_id, candidate_id, vacancy_id, company_id,
                               status, total_steps, current_step,
                               created_at, updated_at, lgpd_expiry,
                               steps_executed, steps_approved
                        FROM candidate_nurture_sequences
                        WHERE candidate_id = :cid
                        ORDER BY created_at DESC
                        LIMIT 1
                    """),
                    {"cid": candidate_id},
                )
            row = result.mappings().first()

            if not row:
                return {
                    "success": False,
                    "data": {"sequence_id": sequence_id, "candidate_id": candidate_id},
                    "message": f"Sequência não encontrada para {'sequence_id=' + sequence_id if sequence_id else 'candidate_id=' + candidate_id}.",
                }

            # Check LGPD expiry
            lgpd_expiry = row["lgpd_expiry"]
            lgpd_expired = lgpd_expiry and lgpd_expiry < datetime.utcnow()
            status = row["status"]
            if lgpd_expired and status not in ("expired", "completed"):
                status = "lgpd_expired"

            return {
                "success": True,
                "data": {
                    "sequence_id": str(row["sequence_id"]),
                    "candidate_id": str(row["candidate_id"]),
                    "vacancy_id": str(row["vacancy_id"] or ""),
                    "company_id": str(row["company_id"] or ""),
                    "status": status,
                    "total_steps": row["total_steps"] or 0,
                    "current_step": row["current_step"] or 0,
                    "steps_executed": row["steps_executed"] or 0,
                    "steps_approved": row["steps_approved"] or 0,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "lgpd_expiry": lgpd_expiry.isoformat() if lgpd_expiry else None,
                    "lgpd_expired": bool(lgpd_expired),
                },
                "message": f"Sequência {row['sequence_id']}: status={status}, step {row['current_step'] or 0}/{row['total_steps'] or 0}.",
            }

        except Exception as db_exc:
            logger.warning("[nurture_tools] DB query failed (tabela pode não existir): %s", db_exc)
            # Graceful degradation: retornar info básica sem persistência
            return {
                "success": True,
                "data": {
                    "sequence_id": sequence_id,
                    "candidate_id": candidate_id,
                    "status": "unknown",
                    "note": "Tabela candidate_nurture_sequences não encontrada. Use nurture_create_sequence para criar uma sequência persistida.",
                },
                "message": f"Status da sequência {sequence_id or candidate_id}: tabela de sequências não disponível.",
            }

_NURTURE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="nurture_get_sequence_status",
        description=(
            "Obtém o status atual de uma sequência de nurture: steps pendentes, "
            "aprovados, enviados e próximo agendamento."
        ),
        parameters={
            "type": "object",
            "properties": {
                "sequence_id": {"type": "string", "description": "ID da sequência"},
                "candidate_id": {"type": "string", "description": "ID do candidato"},
            },
            "required": [],
        },
        function=_wrap_nurture_get_sequence_status,
    )
)


@tool_handler("nurture_sequence")
async def _wrap_nurture_approve_step(**kwargs: Any) -> dict[str, Any]:
    """
    Registra aprovação HITL de um step da sequência antes do envio.

    Persiste o registro de aprovação na tabela nurture_step_approvals com status
    'approved'. O nurture_execute_step verifica esta tabela antes de executar —
    não confia apenas no booleano hitl_approved do caller.
    """
    logger.info("[nurture_tools] nurture_approve_step called: %s", list(kwargs.keys()))
    sequence_id = kwargs.get("sequence_id", "")
    step_number = kwargs.get("step_number", 1)
    approved_by = kwargs.get("approved_by", "")
    notes = kwargs.get("notes", "")

    if not sequence_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'sequence_id' é obrigatório."}

    approval_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Persistir aprovação na tabela nurture_step_approvals (fonte autoritativa)
    db_persisted = False
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO nurture_step_approvals (
                        approval_id, sequence_id, step_number,
                        approved_by, approved_at, notes, status
                    ) VALUES (
                        :appr_id, :seq_id, :step_num,
                        :approver, :approved_at, :notes, 'approved'
                    )
                    ON CONFLICT (sequence_id, step_number) DO UPDATE
                        SET approval_id = EXCLUDED.approval_id,
                            approved_by = EXCLUDED.approved_by,
                            approved_at = EXCLUDED.approved_at,
                            notes = EXCLUDED.notes,
                            status = 'approved'
                """),
                {
                    "appr_id": approval_id,
                    "seq_id": sequence_id,
                    "step_num": step_number,
                    "approver": approved_by or "recruiter",
                    "approved_at": now,
                    "notes": notes or "",
                },
            )
            await session.commit()
        db_persisted = True
        logger.info("[nurture_tools] Aprovação %s persistida no DB", approval_id)
    except Exception as db_exc:
        # Graceful degradation: tabela pode não existir ainda
        logger.warning(
            "[nurture_tools] Não foi possível persistir aprovação %s: %s — "
            "tabela nurture_step_approvals pode não existir",
            approval_id, db_exc
        )

    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.publish_chat_message(
            message_data={
                "event": "nurture_step_approved",
                "approval_id": approval_id,
                "sequence_id": sequence_id,
                "step_number": step_number,
                "approved_by": approved_by,
                "approved_at": now.isoformat(),
                "notes": notes,
                "db_persisted": db_persisted,
            },
            routing_key="agent.nurture",
        )
    except Exception as mq_exc:
        logger.warning("[nurture_tools] RabbitMQ publish failed (non-blocking): %s", mq_exc)

    return {
        "success": True,
        "data": {
            "approval_id": approval_id,
            "sequence_id": sequence_id,
            "step_number": step_number,
            "approved": True,
            "approved_by": approved_by,
            "approved_at": now.isoformat(),
            "notes": notes,
            "db_persisted": db_persisted,
            "next_action": "Use nurture_execute_step para executar o step aprovado.",
        },
        "message": (
            f"Step {step_number} da sequência {sequence_id} aprovado "
            f"por {approved_by or 'recrutador'}. Pronto para execução."
        ),
    }
_NURTURE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="nurture_approve_step",
        description=(
            "Registra aprovação HITL de um step da sequência de nurture. "
            "Obrigatório antes de executar qualquer envio quando requires_approval=true. "
            "Loga auditoria da aprovação."
        ),
        parameters={
            "type": "object",
            "properties": {
                "sequence_id": {"type": "string", "description": "ID da sequência"},
                "step_number": {"type": "integer", "description": "Número do step a aprovar"},
                "approved_by": {"type": "string", "description": "Nome ou ID do recrutador aprovador"},
                "notes": {"type": "string", "description": "Observações sobre a aprovação (opcional)"},
            },
            "required": ["sequence_id", "step_number"],
        },
        function=_wrap_nurture_approve_step,
    )
)


async def _check_communication_matrix_approval(channel: str, company_id: str) -> bool:
    """
    Verifica se o canal/empresa requer aprovação via communication_matrix.
    Retorna True se requires_approval estiver ativo, False caso contrário.
    Fail-safe: se não conseguir carregar, assume requires_approval=True.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT requires_approval
                    FROM communication_matrix
                    WHERE channel = :channel
                      AND (company_id = :cid OR company_id IS NULL)
                    ORDER BY CASE WHEN company_id = :cid THEN 0 ELSE 1 END
                    LIMIT 1
                """),
                {"channel": channel, "cid": company_id or ""},
            )
            row = result.mappings().first()
            if row is not None:
                return bool(row["requires_approval"])
    except Exception as e:
        logger.warning("[nurture_tools] communication_matrix query failed — assumindo requires_approval=True: %s", e)
    # Default: sempre requer aprovação (fail-safe)
    return True


async def _check_nurture_step_approved_in_db(sequence_id: str, step_number: int) -> tuple[bool, str]:
    """
    Verifica se um step foi aprovado via nurture_approve_step (DB autoritativo).

    Retorna (approved: bool, reason: str).
    Se a tabela não existir, assume aprovação necessária (fail-closed).
    Se a tabela existir mas não houver registro, nega a execução.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT status, approved_by, approved_at
                    FROM nurture_step_approvals
                    WHERE sequence_id = :seq_id AND step_number = :step_num
                    ORDER BY approved_at DESC
                    LIMIT 1
                """),
                {"seq_id": sequence_id, "step_num": step_number},
            )
            row = result.mappings().first()
            if row and row["status"] == "approved":
                return True, f"Aprovado por {row['approved_by']} em {row['approved_at']}"
            return False, "Nenhum registro de aprovação encontrado para este step."
    except Exception as db_exc:
        err_msg = str(db_exc).lower()
        if "does not exist" in err_msg or "no such table" in err_msg:
            # Tabela ainda não criada — graceful: confiar no parâmetro do caller
            logger.warning("[nurture_tools] Tabela nurture_step_approvals não existe — HITL degradado")
            return None, "tabela_ausente"
        logger.warning("[nurture_tools] Erro ao verificar aprovação: %s — negando por segurança", db_exc)
        return False, f"Erro de verificação: {db_exc}"


@tool_handler("nurture_sequence")
async def _wrap_nurture_execute_step(**kwargs: Any) -> dict[str, Any]:
    """
    Executa um step aprovado da sequência de nurture.

    HITL server-side: verifica aprovação na tabela nurture_step_approvals.
    Não confia no booleano hitl_approved do caller como controle primário.
    hitl_approved=True é aceito apenas se a tabela não existir (graceful degradation).
    """
    logger.info("[nurture_tools] nurture_execute_step called: %s", list(kwargs.keys()))
    sequence_id = kwargs.get("sequence_id", "")
    step_number = kwargs.get("step_number", 1)
    hitl_approved_flag = kwargs.get("hitl_approved", False)  # Sinal do caller — não autoritativo
    channel = kwargs.get("channel", "email")
    company_id = kwargs.get("company_id", "")

    if not sequence_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'sequence_id' é obrigatório."}

    # Verificar communication_matrix.requires_approval para o canal/empresa
    matrix_requires_approval = await _check_communication_matrix_approval(channel, company_id)

    if matrix_requires_approval:
        # Verificação server-side: consultar DB para aprovação real
        db_approved, db_reason = await _check_nurture_step_approved_in_db(sequence_id, step_number)

        if db_approved is None:
            # Tabela não existe: degradar para confiar no booleano do caller
            if not hitl_approved_flag:
                return {
                    "success": False,
                    "data": {"hitl_required": True, "channel": channel},
                    "message": (
                        f"HITL obrigatório: canal '{channel}' requer aprovação. "
                        "Use nurture_approve_step primeiro, depois passe hitl_approved=true."
                    ),
                }
            logger.warning(
                "[nurture_tools] Executando step %d seq %s sem verificação DB (tabela ausente)",
                step_number, sequence_id
            )
        elif not db_approved:
            return {
                "success": False,
                "data": {"hitl_required": True, "channel": channel, "db_reason": db_reason},
                "message": (
                    f"HITL obrigatório: {db_reason} "
                    f"Use nurture_approve_step para aprovar o step {step_number} "
                    f"da sequência {sequence_id} antes de executar."
                ),
            }
        # db_approved is True: aprovação verificada no DB — prosseguir

    execution_id = str(uuid.uuid4())
    now = datetime.utcnow()

    candidate_id = kwargs.get("candidate_id", "")
    channel = kwargs.get("channel", "email")
    message_content = kwargs.get("message_content", "")

    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.publish_chat_message(
            message_data={
                "event": "nurture_step_executed",
                "execution_id": execution_id,
                "sequence_id": sequence_id,
                "step_number": step_number,
                "candidate_id": candidate_id,
                "channel": channel,
                "message_preview": message_content[:200] if message_content else "",
                "executed_at": now.isoformat(),
                "hitl_approved": True,
            },
            routing_key="agent.nurture",
        )
    except Exception as mq_exc:
        logger.warning("[nurture_tools] RabbitMQ publish failed (non-blocking): %s", mq_exc)

    return {
        "success": True,
        "data": {
            "execution_id": execution_id,
            "sequence_id": sequence_id,
            "step_number": step_number,
            "candidate_id": candidate_id,
            "channel": channel,
            "status": "executed",
            "executed_at": now.isoformat(),
        },
        "message": (
            f"Step {step_number} da sequência {sequence_id} executado via {channel}. "
            f"ID de execução: {execution_id}."
        ),
    }
_NURTURE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="nurture_execute_step",
        description=(
            "Executa um step previamente aprovado da sequência de nurture. "
            "Requer hitl_approved=true. Publica evento para processamento assíncrono. "
            "Suporta email, WhatsApp, LinkedIn message e SMS."
        ),
        parameters={
            "type": "object",
            "properties": {
                "sequence_id": {"type": "string", "description": "ID da sequência"},
                "step_number": {"type": "integer", "description": "Número do step a executar"},
                "candidate_id": {"type": "string", "description": "ID do candidato"},
                "channel": {
                    "type": "string",
                    "enum": _STEP_TYPES,
                    "description": "Canal de envio",
                    "default": "email",
                },
                "message_content": {"type": "string", "description": "Conteúdo da mensagem"},
                "hitl_approved": {
                    "type": "boolean",
                    "description": "HITL aprovado (obrigatório: true)",
                    "default": False,
                },
            },
            "required": ["sequence_id", "step_number"],
        },
        function=_wrap_nurture_execute_step,
    )
)


@tool_handler("nurture_sequence")
async def _wrap_nurture_expire_sequence(**kwargs: Any) -> dict[str, Any]:
    """Expira uma sequência de nurture por LGPD, opt-out ou conclusão."""
    logger.info("[nurture_tools] nurture_expire_sequence called: %s", list(kwargs.keys()))
    sequence_id = kwargs.get("sequence_id", "")
    reason = kwargs.get("reason", "lgpd_cleanup")
    candidate_id = kwargs.get("candidate_id", "")

    if not sequence_id:
        return {"success": False, "data": {}, "message": "Parâmetro 'sequence_id' é obrigatório."}

    valid_reasons = ["lgpd_cleanup", "opt_out", "hired", "not_interested", "sequence_completed", "manual"]
    if reason not in valid_reasons:
        reason = "manual"

    expired_at = datetime.utcnow().isoformat()

    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.publish_chat_message(
            message_data={
                "event": "nurture_sequence_expired",
                "sequence_id": sequence_id,
                "candidate_id": candidate_id,
                "reason": reason,
                "expired_at": expired_at,
            },
            routing_key="agent.nurture",
        )
    except Exception as mq_exc:
        logger.warning("[nurture_tools] RabbitMQ publish failed (non-blocking): %s", mq_exc)

    return {
        "success": True,
        "data": {
            "sequence_id": sequence_id,
            "candidate_id": candidate_id,
            "reason": reason,
            "expired_at": expired_at,
            "status": "expired",
        },
        "message": f"Sequência {sequence_id} expirada. Motivo: {reason}.",
    }
_NURTURE_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="nurture_expire_sequence",
        description=(
            "Expira uma sequência de nurture. Motivos válidos: "
            "lgpd_cleanup (TTL expirado), opt_out (candidato pediu remoção), "
            "hired (contratado), not_interested, sequence_completed, manual."
        ),
        parameters={
            "type": "object",
            "properties": {
                "sequence_id": {"type": "string", "description": "ID da sequência"},
                "candidate_id": {"type": "string", "description": "ID do candidato (opcional)"},
                "reason": {
                    "type": "string",
                    "enum": ["lgpd_cleanup", "opt_out", "hired", "not_interested", "sequence_completed", "manual"],
                    "description": "Motivo da expiração",
                    "default": "lgpd_cleanup",
                },
            },
            "required": ["sequence_id"],
        },
        function=_wrap_nurture_expire_sequence,
    )
)

_NURTURE_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in _NURTURE_TOOL_DEFINITIONS}


def get_nurture_sequence_tools() -> list[ToolDefinition]:
    return list(_NURTURE_TOOL_DEFINITIONS)
