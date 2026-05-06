"""
Referral Tool Registry — indicações via colaboradores internos.

Expõe tools para ReferralAgent:
- referral_identify_connectors: identifica colaboradores com perfil próximo à vaga
- referral_prepare_request: prepara mensagem de solicitação de indicação
- referral_send_request: envia solicitação via CommunicationMatrix (HITL obrigatório)
- referral_track_responses: rastreia respostas de indicações

HITL OBRIGATÓRIO: referral_send_request requer aprovação humana antes do envio.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_REFERRAL_TOOL_DEFINITIONS: list[ToolDefinition] = []


@tool_handler("referral")
async def _wrap_referral_identify_connectors(**kwargs: Any) -> dict[str, Any]:
    """
    Identifica colaboradores internos com perfil relevante para indicar candidatos.
    FairnessGuard: verifica query antes de executar busca.
    """
    logger.info("[referral_tools] referral_identify_connectors called: %s", list(kwargs.keys()))
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    company_id = kwargs.get("company_id", "")
    role = kwargs.get("role", "")
    skills = kwargs.get("skills", [])
    limit = min(int(kwargs.get("limit", 15)), 50)

    # FairnessGuard: verificar query de busca
    query_str = f"{role} {' '.join(str(s) for s in skills)}"
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_result = _fg.check(query_str)
        if _fg_result.is_blocked:
            return {
                "success": False,
                "data": {},
                "message": _fg_result.educational_message or "Busca bloqueada por critério discriminatório.",
            }
    except Exception as _fg_exc:
        logger.debug("[referral_tools] FairnessGuard check skipped: %s", _fg_exc)

    conditions = [
        "c.status = 'hired'",
        "c.company_id = :company_id",
    ]
    params: dict[str, Any] = {"company_id": company_id, "lim": limit}

    if role:
        conditions.append("c.current_title ILIKE :role_pattern")
        params["role_pattern"] = f"%{role}%"

    if skills and isinstance(skills, list) and len(skills) > 0:
        conditions.append("c.technical_skills && :skills_arr")
        params["skills_arr"] = skills

    where_clause = " AND ".join(conditions)

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text(f"""
                    SELECT c.id, c.name, c.email, c.current_title,
                           c.technical_skills, c.years_of_experience,
                           c.location_city, c.location_country
                    FROM candidates c
                    WHERE {where_clause}
                    ORDER BY c.years_of_experience DESC NULLS LAST
                    LIMIT :lim
                """),
                params,
            )
            rows = result.mappings().all()
        except Exception as db_exc:
            logger.warning("[referral_tools] DB query failed: %s — retornando vazio", db_exc)
            rows = []

    connectors = []
    for row in rows:
        connectors.append({
            "id": str(row["id"]),
            "name": row["name"],
            "email": row["email"],
            "current_title": row["current_title"],
            "technical_skills": row["technical_skills"] or [],
            "years_of_experience": row["years_of_experience"],
            "location": f"{row['location_city'] or ''}, {row['location_country'] or ''}".strip(", "),
            "relevance_reason": (
                f"Trabalha como {row['current_title']} — pode indicar candidatos para '{role}'."
                if role else "Colaborador ativo da empresa."
            ),
        })

    return {
        "success": True,
        "data": {
            "connectors": connectors,
            "count": len(connectors),
            "company_id": company_id,
        },
        "message": (
            f"{len(connectors)} colaborador(es) identificado(s) como potenciais conectores "
            f"para indicações de '{role or 'qualquer vaga'}'."
        ),
    }
_REFERRAL_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="referral_identify_connectors",
        description=(
            "Identifica colaboradores ativos da empresa com perfil relevante para solicitar indicações "
            "de candidatos para uma vaga. Filtra por cargo, skills e localização."
        ),
        parameters={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Cargo buscado (para encontrar colaboradores afins)"},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills técnicas da vaga",
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de conectores (padrão: 15)",
                    "default": 15,
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_referral_identify_connectors,
    )
)


@tool_handler("referral")
async def _wrap_referral_prepare_request(**kwargs: Any) -> dict[str, Any]:
    """Prepara mensagem personalizada de solicitação de indicação."""
    logger.info("[referral_tools] referral_prepare_request called: %s", list(kwargs.keys()))
    connector_name = kwargs.get("connector_name", "")
    role = kwargs.get("role", "")
    company_name = kwargs.get("company_name", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    channel = kwargs.get("channel", "email").lower()
    custom_message = kwargs.get("custom_message", "")

    if not connector_name or not role:
        return {
            "success": False,
            "data": {},
            "message": "Parâmetros 'connector_name' e 'role' são obrigatórios.",
        }

    if channel == "whatsapp":
        message = (
            f"Olá {connector_name.split()[0]}! 👋\n\n"
            f"Estamos com uma vaga aberta de *{role}*"
            + (f" na {company_name}" if company_name else "") + ".\n\n"
            "Você conhece alguém com esse perfil que possa ter interesse? "
            "Qualquer indicação é muito bem-vinda! 🙏\n\n"
            "Se quiser, posso compartilhar mais detalhes da vaga."
        )
    else:
        message = (
            f"Olá {connector_name.split()[0]},\n\n"
            f"Espero que esteja bem! Estamos com uma vaga aberta de {role}"
            + (f" em {company_name}" if company_name else "") + ".\n\n"
            "Sabe de alguém com esse perfil que possa ter interesse? "
            "Sua indicação pode fazer toda a diferença.\n\n"
            "Qualquer nome ou contato que você queira sugerir será muito apreciado!\n\n"
            "Obrigado(a) pela ajuda."
        )

    if custom_message:
        message = custom_message

    request_id = str(uuid.uuid4())

    return {
        "success": True,
        "data": {
            "request_id": request_id,
            "connector_name": connector_name,
            "role": role,
            "channel": channel,
            "message": message,
            "vacancy_id": vacancy_id,
            "requires_hitl": True,
            "hitl_note": "HITL obrigatório — esta mensagem precisa de aprovação humana antes do envio.",
        },
        "message": (
            f"Mensagem de indicação preparada para {connector_name} via {channel}. "
            f"AGUARDANDO APROVAÇÃO HITL antes do envio."
        ),
    }
_REFERRAL_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="referral_prepare_request",
        description=(
            "Prepara mensagem personalizada de solicitação de indicação para um colaborador, "
            "via email ou WhatsApp. Retorna rascunho com HITL obrigatório antes do envio."
        ),
        parameters={
            "type": "object",
            "properties": {
                "connector_name": {"type": "string", "description": "Nome do colaborador conector"},
                "role": {"type": "string", "description": "Cargo da vaga"},
                "company_name": {"type": "string", "description": "Nome da empresa (opcional)"},
                "vacancy_id": {"type": "string", "description": "ID da vaga (opcional)"},
                "channel": {
                    "type": "string",
                    "enum": ["email", "whatsapp"],
                    "description": "Canal de comunicação (padrão: email)",
                    "default": "email",
                },
                "custom_message": {
                    "type": "string",
                    "description": "Mensagem customizada (substitui o template padrão)",
                },
            },
            "required": ["connector_name", "role"],
        },
        output_schema=ToolOutput,
        function=_wrap_referral_prepare_request,
    )
)


async def _check_referral_matrix_approval(channel: str, company_id: str) -> bool:
    """
    Verifica se o canal/empresa requer aprovação via communication_matrix para referrals.
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
        logger.warning("[referral_tools] communication_matrix query failed — assumindo requires_approval=True: %s", e)
    return True


async def _persist_referral_approval(
    request_key: str,
    approved_by: str,
    channel: str,
    vacancy_id: str,
    company_id: str,
) -> tuple[str, bool]:
    """
    Persiste aprovação de referral na tabela referral_hitl_approvals.
    Retorna (approval_id, db_persisted).
    """
    import uuid as _uuid
    from datetime import datetime as _dt
    approval_id = str(_uuid.uuid4())
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO referral_hitl_approvals (
                        approval_id, request_key, approved_by,
                        channel, vacancy_id, company_id, approved_at, status
                    ) VALUES (
                        :appr_id, :req_key, :approver,
                        :channel, :vac_id, :co_id, :now, 'approved'
                    )
                    ON CONFLICT (request_key) DO UPDATE
                        SET approval_id = EXCLUDED.approval_id,
                            approved_by = EXCLUDED.approved_by,
                            approved_at = EXCLUDED.approved_at,
                            status = 'approved'
                """),
                {
                    "appr_id": approval_id,
                    "req_key": request_key,
                    "approver": approved_by or "recruiter",
                    "channel": channel,
                    "vac_id": vacancy_id or None,
                    "co_id": company_id or None,
                    "now": _dt.utcnow(),
                },
            )
            await session.commit()
        return approval_id, True
    except Exception as db_exc:
        logger.warning("[referral_tools] Não foi possível persistir aprovação referral: %s", db_exc)
        return approval_id, False


async def _verify_referral_approval_in_db(request_key: str) -> tuple[bool | None, str]:
    """
    Verifica aprovação de referral no DB.
    Retorna (True=aprovado, None=tabela ausente, False=não aprovado), motivo.
    """
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT status, approved_by, approved_at
                    FROM referral_hitl_approvals
                    WHERE request_key = :req_key
                    LIMIT 1
                """),
                {"req_key": request_key},
            )
            row = result.mappings().first()
            if row and row["status"] == "approved":
                return True, f"Aprovado por {row['approved_by']}"
            return False, "Nenhum registro de aprovação encontrado."
    except Exception as db_exc:
        err = str(db_exc).lower()
        if "does not exist" in err or "no such table" in err:
            return None, "tabela_ausente"
        return False, f"Erro DB: {db_exc}"


@tool_handler("referral")
async def _wrap_referral_send_request(**kwargs: Any) -> dict[str, Any]:
    """
    Envia solicitação de indicação via CommunicationMatrix.

    HITL server-side: quando communication_matrix.requires_approval=True,
    verifica aprovação na tabela referral_hitl_approvals (DB autoritativo).
    O parâmetro hitl_approved é aceito apenas como fallback quando a tabela
    não existe (graceful degradation).
    """
    logger.info("[referral_tools] referral_send_request called: %s", list(kwargs.keys()))
    hitl_approved_flag = kwargs.get("hitl_approved", False)  # Sinal do caller — não autoritativo
    channel = kwargs.get("channel", "email").lower()
    company_id = kwargs.get("company_id", "")
    connector_email = kwargs.get("connector_email", "")
    vacancy_id = kwargs.get("vacancy_id", "")

    # Verificar communication_matrix.requires_approval
    matrix_requires_approval = await _check_referral_matrix_approval(channel, company_id)

    if matrix_requires_approval:
        # Chave de deduplicação para este pedido de referral
        request_key = f"{connector_email}:{vacancy_id}:{channel}"
        db_approved, db_reason = await _verify_referral_approval_in_db(request_key)

        if db_approved is None:
            # Tabela ausente: degradar para o boolean do caller
            if not hitl_approved_flag:
                return {
                    "success": False,
                    "data": {"hitl_required": True, "channel": channel},
                    "message": (
                        f"HITL obrigatório: canal '{channel}' requer aprovação humana. "
                        "Por favor, confirme explicitamente antes de enviar o pedido."
                    ),
                }
        elif not db_approved:
            return {
                "success": False,
                "data": {"hitl_required": True, "channel": channel, "db_reason": db_reason},
                "message": (
                    f"HITL obrigatório: {db_reason} "
                    "Use referral_prepare_request e aguarde aprovação do recrutador."
                ),
            }

    connector_email = kwargs.get("connector_email", "")
    connector_name = kwargs.get("connector_name", "")
    message = kwargs.get("message", "")
    vacancy_id = kwargs.get("vacancy_id", "")

    if not connector_email or not message:
        return {
            "success": False,
            "data": {},
            "message": "Parâmetros 'connector_email' e 'message' são obrigatórios.",
        }

    referral_id = str(uuid.uuid4())

    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.publish_chat_message(
            message_data={
                "event": "referral_request_sent",
                "referral_id": referral_id,
                "connector_email": connector_email,
                "connector_name": connector_name,
                "channel": channel,
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "message_preview": message[:200],
                "hitl_approved": True,
            },
            routing_key="agent.referral",
        )
    except Exception as mq_exc:
        logger.warning("[referral_tools] RabbitMQ publish failed (non-blocking): %s", mq_exc)

    return {
        "success": True,
        "data": {
            "referral_id": referral_id,
            "connector_email": connector_email,
            "connector_name": connector_name,
            "channel": channel,
            "vacancy_id": vacancy_id,
            "status": "sent",
            "hitl_approved": True,
        },
        "message": (
            f"Solicitação de indicação enviada para {connector_name or connector_email} "
            f"via {channel}. ID: {referral_id}."
        ),
    }
_REFERRAL_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="referral_send_request",
        description=(
            "Envia solicitação de indicação para colaborador via email ou WhatsApp. "
            "HITL OBRIGATÓRIO: requer parâmetro 'hitl_approved=true'. "
            "Nunca enviar sem aprovação explícita do recrutador responsável."
        ),
        parameters={
            "type": "object",
            "properties": {
                "connector_email": {"type": "string", "description": "Email do colaborador conector"},
                "connector_name": {"type": "string", "description": "Nome do colaborador"},
                "message": {"type": "string", "description": "Mensagem a enviar (output de referral_prepare_request)"},
                "channel": {
                    "type": "string",
                    "enum": ["email", "whatsapp"],
                    "description": "Canal de comunicação",
                    "default": "email",
                },
                "vacancy_id": {"type": "string", "description": "ID da vaga"},
                "hitl_approved": {
                    "type": "boolean",
                    "description": "HITL aprovado (true obrigatório para envio)",
                    "default": False,
                },
            },
            "required": ["connector_email", "message"],
        },
        output_schema=ToolOutput,
        function=_wrap_referral_send_request,
    )
)

@tool_handler("referral")
async def _wrap_referral_approve_request(**kwargs: Any) -> dict[str, Any]:
    """
    Registra aprovação HITL para um pedido de referral antes do envio.

    Persiste o registro na tabela referral_hitl_approvals com status 'approved'.
    O referral_send_request verificará este registro no DB — não confia apenas
    no booleano hitl_approved do caller.
    """
    logger.info("[referral_tools] referral_approve_request called: %s", list(kwargs.keys()))
    connector_email = kwargs.get("connector_email", "")
    vacancy_id = kwargs.get("vacancy_id", "")
    channel = kwargs.get("channel", "email").lower()
    company_id = kwargs.get("company_id", "")
    approved_by = kwargs.get("approved_by", "")
    notes = kwargs.get("notes", "")

    if not connector_email:
        return {"success": False, "data": {}, "message": "Parâmetro 'connector_email' é obrigatório."}

    # Chave de deduplicação — mesma usada no referral_send_request
    request_key = f"{connector_email}:{vacancy_id}:{channel}"

    approval_id, db_persisted = await _persist_referral_approval(
        request_key=request_key,
        approved_by=approved_by or "recruiter",
        channel=channel,
        vacancy_id=vacancy_id,
        company_id=company_id,
    )

    return {
        "success": True,
        "data": {
            "approval_id": approval_id,
            "request_key": request_key,
            "connector_email": connector_email,
            "vacancy_id": vacancy_id,
            "channel": channel,
            "approved_by": approved_by,
            "db_persisted": db_persisted,
            "notes": notes,
            "next_action": (
                "Aprovação registrada. Use referral_send_request para enviar o pedido."
            ),
        },
        "message": (
            f"Aprovação HITL registrada para referral a {connector_email} via {channel}. "
            f"ID: {approval_id}."
            + (" (DB persistido)" if db_persisted else " (sem DB — graceful degradation)")
        ),
    }
_REFERRAL_TOOL_DEFINITIONS.append(
    ToolDefinition(
        name="referral_approve_request",
        description=(
            "Registra aprovação HITL para um pedido de indicação antes do envio. "
            "Obrigatório quando communication_matrix.requires_approval=true para o canal. "
            "Use ANTES de referral_send_request para registrar a decisão do recrutador no DB. "
            "O referral_send_request verificará este registro — não aceita apenas booleano."
        ),
        parameters={
            "type": "object",
            "properties": {
                "connector_email": {
                    "type": "string",
                    "description": "Email do colaborador que será solicitado a indicar",
                },
                "vacancy_id": {
                    "type": "string",
                    "description": "ID da vaga para a qual se pede indicação",
                },
                "channel": {
                    "type": "string",
                    "description": "Canal de envio (email, whatsapp, linkedin)",
                    "enum": ["email", "whatsapp", "linkedin"],
                    "default": "email",
                },
                "approved_by": {
                    "type": "string",
                    "description": "Nome ou ID do recrutador aprovador",
                },
                "notes": {
                    "type": "string",
                    "description": "Observações sobre a aprovação (opcional)",
                },
            },
            "required": ["connector_email"],
        },
        output_schema=ToolOutput,
        function=_wrap_referral_approve_request,
    )
)

_REFERRAL_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in _REFERRAL_TOOL_DEFINITIONS}


def get_referral_tools() -> list[ToolDefinition]:
    return list(_REFERRAL_TOOL_DEFINITIONS)
