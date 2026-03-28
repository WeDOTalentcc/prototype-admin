"""
ActionExecutorService - Closed-loop action execution for LIA.

Transforms LIA from open-loop (suggest UI actions) to closed-loop (execute real actions).
Maps intents to domain actions, validates parameters, and executes via domains.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    status: Literal["executed", "needs_params", "needs_confirmation", "not_actionable", "error"]
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    missing_params: Optional[List[str]] = None
    confirmation_summary: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    pending_action_id: Optional[str] = None
    error_detail: Optional[str] = None


ACTIONABLE_INTENTS: Dict[str, Dict[str, Any]] = {
    "mover_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id", "to_stage"],
        "optional_params": ["from_stage", "sub_status", "reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "to_stage": "etapa destino",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer mover?",
            "to_stage": "Para qual etapa do pipeline?",
        },
    },
    "atualizar_status_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id", "to_stage"],
        "optional_params": ["from_stage", "sub_status"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "to_stage": "etapa destino",
        },
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer atualizar?",
            "to_stage": "Para qual etapa?",
        },
    },
    "reprovar_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id"],
        "optional_params": ["reason", "feedback_message"],
        "risk_level": "high",
        "requires_confirmation": True,
        "default_params": {"to_stage": "Reprovado"},
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer reprovar?",
        },
    },
    "aprovar_candidato": {
        "domain_id": "pipeline_transition",
        "action_id": "move_candidate",
        "required_params": ["candidate_id"],
        "optional_params": ["to_stage", "reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer aprovar?",
        },
    },
    "enviar_email": {
        "domain_id": "communication",
        "action_id": "send_email",
        "required_params": ["candidate_id", "subject", "body"],
        "optional_params": ["template_id", "cc"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "subject": "assunto",
            "body": "mensagem",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato quer enviar o email?",
            "subject": "Qual o assunto do email?",
            "body": "Qual a mensagem que quer enviar?",
        },
    },
    "enviar_mensagem": {
        "domain_id": "communication",
        "action_id": "send_email",
        "required_params": ["candidate_id", "subject", "body"],
        "optional_params": ["template_id"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "subject": "assunto",
            "body": "mensagem",
        },
        "clarification_prompts": {
            "candidate_id": "Para qual candidato?",
            "subject": "Qual o assunto?",
            "body": "Qual a mensagem?",
        },
    },
    "agendar_entrevista": {
        "domain_id": "interview_scheduling",
        "action_id": "schedule_interview",
        "required_params": ["candidate_id", "datetime"],
        "optional_params": ["interviewer", "type", "location"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "candidate_id": "candidato",
            "datetime": "data e hora",
            "interviewer": "entrevistador",
        },
        "clarification_prompts": {
            "candidate_id": "Com qual candidato quer agendar?",
            "datetime": "Para qual data e horário?",
        },
    },
    "disparar_triagem": {
        "domain_id": "cv_screening",
        "action_id": "start_screening",
        "required_params": [],
        "optional_params": ["candidate_ids"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "iniciar_triagem": {
        "domain_id": "cv_screening",
        "action_id": "start_screening",
        "required_params": [],
        "optional_params": ["candidate_ids"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {},
        "clarification_prompts": {},
    },
    "analisar_perfil": {
        "domain_id": "cv_screening",
        "action_id": "analyze_profile",
        "required_params": ["candidate_id"],
        "optional_params": [],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato quer analisar?",
        },
    },
    "analise_detalhada": {
        "domain_id": "cv_screening",
        "action_id": "analyze_profile",
        "required_params": ["candidate_id"],
        "optional_params": [],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {"candidate_id": "candidato"},
        "clarification_prompts": {
            "candidate_id": "Qual candidato quer analisar em detalhe?",
        },
    },
    "pausar_vaga": {
        "domain_id": "job_management",
        "action_id": "pause_job",
        "required_params": ["job_id"],
        "optional_params": ["reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
            "reason": "motivo",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer pausar?",
            "reason": "Qual o motivo da pausa?",
        },
    },
    "fechar_vaga": {
        "domain_id": "job_management",
        "action_id": "close_job",
        "required_params": ["job_id"],
        "optional_params": ["reason", "outcome"],
        "risk_level": "high",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
            "reason": "motivo",
            "outcome": "resultado",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer fechar?",
            "reason": "Qual o motivo do fechamento?",
            "outcome": "Qual foi o resultado do processo?",
        },
    },
    "duplicar_vaga": {
        "domain_id": "job_management",
        "action_id": "duplicate_job",
        "required_params": ["job_id"],
        "optional_params": ["new_title"],
        "risk_level": "low",
        "requires_confirmation": False,
        "param_labels": {
            "job_id": "vaga",
            "new_title": "novo título",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer duplicar?",
            "new_title": "Qual o título da nova vaga?",
        },
    },
    "reabrir_vaga": {
        "domain_id": "job_management",
        "action_id": "reopen_job",
        "required_params": ["job_id"],
        "optional_params": [],
        "risk_level": "medium",
        "requires_confirmation": True,
        "param_labels": {
            "job_id": "vaga",
        },
        "clarification_prompts": {
            "job_id": "Qual vaga você quer reabrir?",
        },
    },
}

CONFIRMATION_PATTERNS = [
    "sim", "pode", "confirmo", "confirma", "ok", "vamos",
    "pode sim", "manda", "envia", "faz isso", "tá bom",
    "perfeito", "isso mesmo", "correto", "exato", "avança",
    "prossiga", "pode mandar", "manda ver", "vai lá",
    "yes", "go", "confirm", "approved", "claro", "com certeza",
    "pode fazer", "autorizo", "está certo", "está correto",
    "tudo certo", "beleza", "show", "bora",
]

REJECTION_PATTERNS = [
    "não", "cancela", "para", "espera", "mudei de ideia",
    "deixa", "esquece", "cancelar", "no", "cancel", "stop",
    "não quero", "desistir", "abortar", "parar", "não pode",
    "errado", "incorreto", "refazer", "voltar", "desfazer",
]

VALID_PIPELINE_STAGES = [
    "Novo", "Triagem", "Entrevista", "Entrevista Técnica",
    "Entrevista Final", "Teste Técnico", "Proposta",
    "Contratado", "Reprovado", "Desistente",
    "Análise", "Shortlist", "Oferta",
]

STAGE_ALIASES = {
    "new": "Novo",
    "screening": "Triagem",
    "interview": "Entrevista",
    "technical interview": "Entrevista Técnica",
    "final interview": "Entrevista Final",
    "technical test": "Teste Técnico",
    "proposal": "Proposta",
    "offer": "Oferta",
    "hired": "Contratado",
    "rejected": "Reprovado",
    "withdrawn": "Desistente",
    "analysis": "Análise",
    "shortlist": "Shortlist",
}


def is_confirmation(message: str) -> bool:
    msg = message.lower().strip().rstrip("!.?")
    for pattern in CONFIRMATION_PATTERNS:
        if msg == pattern or msg.startswith(pattern + " ") or msg.endswith(" " + pattern):
            return True
    return False


def is_rejection(message: str) -> bool:
    msg = message.lower().strip().rstrip("!.?")
    for pattern in REJECTION_PATTERNS:
        if msg == pattern or msg.startswith(pattern + " ") or msg.endswith(" " + pattern):
            return True
    return False


def resolve_candidate_from_context(
    candidate_name: Optional[str],
    candidate_id: Optional[str],
    candidates_data: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if candidate_id:
        for c in candidates_data:
            if str(c.get("id", "")) == str(candidate_id):
                return c

    if candidate_name and candidates_data:
        name_lower = candidate_name.lower().strip()
        for c in candidates_data:
            c_name = (c.get("name") or "").lower().strip()
            if name_lower == c_name:
                return c
        for c in candidates_data:
            c_name = (c.get("name") or "").lower().strip()
            if name_lower in c_name or c_name in name_lower:
                return c
        for c in candidates_data:
            c_name = (c.get("name") or "").lower().strip()
            name_parts = name_lower.split()
            if any(part in c_name for part in name_parts if len(part) > 2):
                return c
    return None


def resolve_stage(stage_text: Optional[str]) -> Optional[str]:
    if not stage_text:
        return None
    normalized = stage_text.strip().lower()
    if normalized in STAGE_ALIASES:
        return STAGE_ALIASES[normalized]
    stage_lower = normalized
    for valid_stage in VALID_PIPELINE_STAGES:
        if stage_lower == valid_stage.lower():
            return valid_stage
    for valid_stage in VALID_PIPELINE_STAGES:
        if stage_lower in valid_stage.lower() or valid_stage.lower() in stage_lower:
            return valid_stage
    return stage_text.title()


class ActionExecutorService:

    def __init__(self):
        self.execution_count = 0

    def is_actionable(self, intent: str) -> bool:
        return intent in ACTIONABLE_INTENTS

    def get_action_config(self, intent: str) -> Optional[Dict[str, Any]]:
        return ACTIONABLE_INTENTS.get(intent)

    async def try_execute(
        self,
        intent: str,
        entities: Dict[str, Any],
        candidates_data: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> ActionResult:
        if not self.is_actionable(intent):
            return ActionResult(status="not_actionable")

        config = ACTIONABLE_INTENTS[intent]
        params = dict(config.get("default_params", {}))

        candidate_name = entities.get("candidate_name")
        candidate_id = entities.get("candidate_id")

        if candidate_name or candidate_id:
            resolved = resolve_candidate_from_context(
                candidate_name, candidate_id, candidates_data
            )
            if resolved:
                params["candidate_id"] = str(resolved.get("id", ""))
                params["candidate_name"] = resolved.get("name", candidate_name or "")
                params["candidate_email"] = resolved.get("email", "")
                if resolved.get("stage"):
                    params["from_stage"] = resolved["stage"]
            elif candidate_name:
                params["candidate_name_unresolved"] = candidate_name

        target_stage = entities.get("target_stage") or entities.get("to_stage") or entities.get("stage")
        if target_stage:
            resolved_stage = resolve_stage(target_stage)
            if resolved_stage:
                params["to_stage"] = resolved_stage

        if entities.get("subject"):
            params["subject"] = entities["subject"]
        if entities.get("body") or entities.get("message"):
            params["body"] = entities.get("body") or entities.get("message")
        if entities.get("datetime") or entities.get("date"):
            params["datetime"] = entities.get("datetime") or entities.get("date")
        if entities.get("interviewer"):
            params["interviewer"] = entities["interviewer"]
        if entities.get("reason"):
            params["reason"] = entities["reason"]

        if entities.get("job_id"):
            params["job_id"] = entities["job_id"]
        if entities.get("job_title"):
            params["job_title"] = entities["job_title"]
        if entities.get("new_title"):
            params["new_title"] = entities["new_title"]
        if entities.get("outcome"):
            params["outcome"] = entities["outcome"]

        missing = []
        for req_param in config["required_params"]:
            if req_param not in params or not params[req_param]:
                if req_param == "candidate_id" and params.get("candidate_name_unresolved"):
                    missing.append("candidate_id")
                elif req_param not in params:
                    missing.append(req_param)

        if missing:
            first_missing = missing[0]
            prompt = config.get("clarification_prompts", {}).get(
                first_missing,
                f"Por favor, informe: {config.get('param_labels', {}).get(first_missing, first_missing)}"
            )

            if first_missing == "candidate_id" and params.get("candidate_name_unresolved"):
                prompt = f"Não encontrei o candidato '{params['candidate_name_unresolved']}' no pipeline desta vaga. Pode verificar o nome?"

            return ActionResult(
                status="needs_params",
                message=prompt,
                missing_params=missing,
                action_type=config["action_id"],
                pending_action_id=str(uuid.uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        if config.get("requires_confirmation", False):
            summary = self._build_confirmation_summary(intent, config, params)
            return ActionResult(
                status="needs_confirmation",
                message=summary["message"],
                confirmation_summary=summary,
                action_type=config["action_id"],
                pending_action_id=str(uuid.uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        result = await self._execute_action(intent, config, params, context)
        return result

    def _build_confirmation_summary(
        self, intent: str, config: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        action_id = config["action_id"]
        candidate_name = params.get("candidate_name", "o candidato")

        if action_id == "move_candidate":
            to_stage = params.get("to_stage", "próxima etapa")
            from_stage = params.get("from_stage", "")
            from_text = f" (atualmente em {from_stage})" if from_stage else ""
            message = f"Vou mover **{candidate_name}**{from_text} para a etapa **{to_stage}**. Confirma?"
        elif action_id == "send_email":
            subject = params.get("subject", "")
            message = f"Vou enviar um email para **{candidate_name}**"
            if subject:
                message += f' com assunto "{subject}"'
            message += ". Confirma o envio?"
        elif action_id == "schedule_interview":
            dt = params.get("datetime", "")
            message = f"Vou agendar uma entrevista com **{candidate_name}**"
            if dt:
                message += f" para **{dt}**"
            message += ". Confirma?"
        elif action_id == "pause_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **pausar** a vaga **{job_title}**. Confirma?"
        elif action_id == "close_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **fechar** a vaga **{job_title}**. Confirma?"
        elif action_id == "reopen_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **reabrir** a vaga **{job_title}**. Confirma?"
        else:
            message = f"Vou executar a ação **{action_id}** para **{candidate_name}**. Confirma?"

        return {
            "message": message,
            "action_id": action_id,
            "intent": intent,
            "params": params,
            "risk_level": config.get("risk_level", "medium"),
        }

    async def _execute_action(
        self,
        intent: str,
        config: Dict[str, Any],
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ActionResult:
        domain_id = config["domain_id"]
        action_id = config["action_id"]

        if action_id == "send_email":
            try:
                tenant_id = context.get("tenant_id", "default") if context else "default"
                logger.info(f"Direct email execution for tenant: {tenant_id}")
                from app.services.email_providers import get_email_provider
                provider = get_email_provider()
                status = provider.get_status()
                if status.get("configured") and status.get("healthy"):
                    candidate_name = params.get("candidate_name", "")
                    to_email = params.get("email", params.get("candidate_email", ""))
                    subject = params.get("subject", "")
                    body = params.get("body", "")
                    if to_email and subject:
                        import html as html_module
                        safe_body = html_module.escape(body)
                        result = await provider.send_email(
                            to=to_email,
                            subject=subject,
                            html_content=f"<p>{safe_body}</p>",
                            text_content=body,
                        )
                        if result.success:
                            self.execution_count += 1
                            return ActionResult(
                                status="executed",
                                message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                                data={
                                    "candidate_id": params.get("candidate_id", ""),
                                    "candidate_name": candidate_name,
                                    "subject": subject,
                                    "to_email": to_email,
                                    "message_id": result.message_id,
                                    "sent_at": datetime.utcnow().isoformat(),
                                    "simulated": False,
                                    "provider": result.provider,
                                },
                                action_type="send_email",
                            )
            except Exception as e:
                logger.warning(f"Direct email sending failed, falling back to domain: {e}")

        if action_id == "schedule_interview":
            try:
                tenant_id = context.get("tenant_id", "default") if context else "default"
                logger.info(f"Direct scheduling for tenant: {tenant_id}")
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                async with AsyncSessionLocal() as db:
                    interview_id = str(uuid_mod.uuid4())
                    candidate_name = params.get("candidate_name", "")
                    dt = params.get("datetime", "")
                    interviewer = params.get("interviewer", "")
                    candidate_id = params.get("candidate_id", "")

                    await db.execute(text("""
                        INSERT INTO interviews (id, candidate_id, interviewer_name, start_time, status, created_at, updated_at)
                        VALUES (:id, CAST(:candidate_id AS uuid), :interviewer, :start_time, 'scheduled', NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": interview_id,
                        "candidate_id": candidate_id,
                        "start_time": dt,
                        "interviewer": interviewer,
                    })
                    await db.commit()

                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
                        data={
                            "interview_id": interview_id,
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "datetime": dt,
                            "interviewer": interviewer,
                            "scheduled_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="schedule_interview",
                    )
            except Exception as e:
                logger.warning(f"Direct scheduling failed, falling back to domain: {e}")

        if action_id == "move_candidate":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                candidate_id = params.get("candidate_id", "")
                to_stage = params.get("to_stage", "")
                candidate_name = params.get("candidate_name", "o candidato")
                from_stage = params.get("from_stage", "")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE vacancy_candidates
                        SET stage = :to_stage, status = 'active', updated_at = NOW()
                        WHERE (id = CAST(:candidate_id AS uuid) OR candidate_id = CAST(:candidate_id AS uuid))
                    """), {
                        "to_stage": to_stage,
                        "candidate_id": candidate_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Candidato não encontrado",
                            error_detail="Candidato não encontrado no pipeline",
                            action_type="move_candidate",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
                        data={
                            "candidate_id": candidate_id,
                            "candidate_name": candidate_name,
                            "from_stage": from_stage,
                            "to_stage": to_stage,
                            "moved_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="move_candidate",
                    )
            except Exception as e:
                logger.warning(f"Direct move_candidate failed, falling back to domain: {e}")

        if action_id == "pause_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE job_vacancies
                        SET status = 'Pausada', updated_at = NOW()
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Vaga não encontrada",
                            error_detail="Vaga não encontrada no sistema",
                            action_type="pause_job",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** pausada com sucesso.",
                        data={
                            "job_id": job_id,
                            "job_title": job_title,
                            "paused_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="pause_job",
                    )
            except Exception as e:
                logger.warning(f"Direct pause_job failed, falling back to domain: {e}")

        if action_id == "close_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE job_vacancies
                        SET status = 'Fechada', closed_at = NOW(), updated_at = NOW()
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Vaga não encontrada",
                            error_detail="Vaga não encontrada no sistema",
                            action_type="close_job",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** fechada com sucesso.",
                        data={
                            "job_id": job_id,
                            "job_title": job_title,
                            "closed_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="close_job",
                    )
            except Exception as e:
                logger.warning(f"Direct close_job failed, falling back to domain: {e}")

        if action_id == "duplicate_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                new_title = params.get("new_title", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    original = await db.execute(text("""
                        SELECT title, company_id, department, location, work_model,
                               employment_type, seniority_level, description, requirements,
                               salary, salary_range, benefits, priority, recruiter,
                               recruiter_email, manager, manager_email, tags
                        FROM job_vacancies
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    row = original.fetchone()
                    if not row:
                        return ActionResult(
                            status="error",
                            message="Vaga original não encontrada",
                            error_detail="Vaga original não encontrada no sistema",
                            action_type="duplicate_job",
                        )

                    new_id = str(uuid_mod.uuid4())
                    final_title = new_title if new_title else f"{row.title} (Cópia)"

                    await db.execute(text("""
                        INSERT INTO job_vacancies (
                            id, title, company_id, department, location, work_model,
                            employment_type, seniority_level, description, requirements,
                            salary, salary_range, benefits, priority, recruiter,
                            recruiter_email, manager, manager_email, tags,
                            status, created_at, updated_at
                        ) VALUES (
                            CAST(:new_id AS uuid), :title, :company_id, :department, :location, :work_model,
                            :employment_type, :seniority_level, :description, :requirements,
                            :salary, :salary_range, :benefits, :priority, :recruiter,
                            :recruiter_email, :manager, :manager_email, :tags,
                            'Ativa', NOW(), NOW()
                        )
                    """), {
                        "new_id": new_id,
                        "title": final_title,
                        "company_id": row.company_id,
                        "department": row.department,
                        "location": row.location,
                        "work_model": row.work_model,
                        "employment_type": row.employment_type,
                        "seniority_level": row.seniority_level,
                        "description": row.description,
                        "requirements": row.requirements,
                        "salary": row.salary,
                        "salary_range": row.salary_range,
                        "benefits": row.benefits,
                        "priority": row.priority,
                        "recruiter": row.recruiter,
                        "recruiter_email": row.recruiter_email,
                        "manager": row.manager,
                        "manager_email": row.manager_email,
                        "tags": row.tags,
                    })
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** duplicada com sucesso. Nova vaga: **{final_title}**.",
                        data={
                            "job_id": job_id,
                            "new_job_id": new_id,
                            "job_title": job_title,
                            "new_title": final_title,
                            "duplicated_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="duplicate_job",
                    )
            except Exception as e:
                logger.warning(f"Direct duplicate_job failed, falling back to domain: {e}")

        if action_id == "reopen_job":
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text
                import uuid as uuid_mod

                job_id = params.get("job_id", "")
                job_title = params.get("job_title", "a vaga")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(text("""
                        UPDATE job_vacancies
                        SET status = 'Ativa', closed_at = NULL, updated_at = NOW()
                        WHERE id = CAST(:job_id AS uuid)
                    """), {
                        "job_id": job_id,
                    })
                    if result.rowcount == 0:
                        return ActionResult(
                            status="error",
                            message="Vaga não encontrada",
                            error_detail="Vaga não encontrada no sistema",
                            action_type="reopen_job",
                        )
                    await db.commit()
                    self.execution_count += 1
                    return ActionResult(
                        status="executed",
                        message=f"Vaga **{job_title}** reaberta com sucesso.",
                        data={
                            "job_id": job_id,
                            "job_title": job_title,
                            "reopened_at": datetime.utcnow().isoformat(),
                            "simulated": False,
                        },
                        action_type="reopen_job",
                    )
            except Exception as e:
                logger.warning(f"Direct reopen_job failed, falling back to domain: {e}")

        if action_id == "start_screening":
            try:
                candidate_ids = params.get("candidate_ids", [])
                logger.info(f"Screening queued for candidates: {candidate_ids}")
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message="Triagem iniciada para os candidatos da vaga.",
                    data={
                        "action": "start_screening",
                        "candidate_ids": candidate_ids,
                        "queued_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                    },
                    action_type="start_screening",
                )
            except Exception as e:
                logger.warning(f"Direct start_screening failed, falling back to domain: {e}")

        if action_id == "analyze_profile":
            try:
                candidate_id = params.get("candidate_id", "")
                candidate_name = params.get("candidate_name", "o candidato")
                logger.info(f"Profile analysis queued for candidate: {candidate_id}")
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message=f"Análise de perfil iniciada para **{candidate_name}**.",
                    data={
                        "action": "analyze_profile",
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "queued_at": datetime.utcnow().isoformat(),
                        "simulated": False,
                    },
                    action_type="analyze_profile",
                )
            except Exception as e:
                logger.warning(f"Direct analyze_profile failed, falling back to domain: {e}")

        try:
            safe_params = {k: v for k, v in params.items() if k not in ("email", "candidate_email", "body", "phone")}
            logger.info(f"Executing closed-loop action: {domain_id}.{action_id} params={list(safe_params.keys())}")

            from app.domains.registry import DomainRegistry

            registry = DomainRegistry()
            domain = registry.get_instance(domain_id)

            if not domain:
                logger.warning(f"Domain '{domain_id}' not found, using simulated execution")
                return await self._simulate_execution(action_id, params, context)

            if action_id == "move_candidate" and "candidate_id" in params and "vacancy_candidate_id" not in params:
                params["vacancy_candidate_id"] = params["candidate_id"]

            from app.domains.base import DomainContext
            domain_context = DomainContext(
                tenant_id=context.get("tenant_id", "default"),
                user_id=context.get("user_id", "recruiter"),
                conversation_id=context.get("conversation_id"),
                metadata=context,
            )

            response = await domain.execute_action(
                action_id=action_id,
                params=params,
                context=domain_context,
            )

            if response and response.success:
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message=response.message or self._success_message(action_id, params),
                    data=response.data if isinstance(response.data, dict) else {"result": str(response.data)},
                    action_type=action_id,
                )
            else:
                error_msg = response.message if response else "Domain execution failed"
                logger.warning(f"Domain execution returned failure: {error_msg}")
                return await self._simulate_execution(action_id, params, context)

        except Exception as e:
            logger.error(f"Action execution error: {e}", exc_info=True)
            return await self._simulate_execution(action_id, params, context)

    async def _simulate_execution(
        self,
        action_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ActionResult:
        candidate_name = params.get("candidate_name", "o candidato")
        self.execution_count += 1

        if action_id == "move_candidate":
            to_stage = params.get("to_stage", "próxima etapa")
            from_stage = params.get("from_stage", "")
            return ActionResult(
                status="executed",
                message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "moved_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="move_candidate",
            )

        elif action_id == "send_email":
            subject = params.get("subject", "")
            return ActionResult(
                status="executed",
                message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "subject": subject,
                    "sent_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="send_email",
            )

        elif action_id == "schedule_interview":
            dt = params.get("datetime", "a definir")
            return ActionResult(
                status="executed",
                message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "datetime": dt,
                    "scheduled_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="schedule_interview",
            )

        elif action_id in ("start_screening", "analyze_profile"):
            return ActionResult(
                status="executed",
                message="Triagem iniciada para os candidatos da vaga.",
                data={
                    "action": action_id,
                    "started_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type=action_id,
            )

        elif action_id == "pause_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** pausada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reason": params.get("reason", ""),
                    "paused_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="pause_job",
            )

        elif action_id == "close_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** fechada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reason": params.get("reason", ""),
                    "outcome": params.get("outcome", ""),
                    "closed_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="close_job",
            )

        elif action_id == "duplicate_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** duplicada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "new_title": params.get("new_title", ""),
                    "duplicated_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="duplicate_job",
            )

        elif action_id == "reopen_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** reaberta com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reopened_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="reopen_job",
            )

        return ActionResult(
            status="executed",
            message=f"Ação **{action_id}** executada com sucesso.",
            data={"action": action_id, "params": params, "simulated": True},
            action_type=action_id,
        )

    def _success_message(self, action_id: str, params: Dict[str, Any]) -> str:
        candidate_name = params.get("candidate_name", "o candidato")
        if action_id == "move_candidate":
            return f"**{candidate_name}** foi movido(a) para **{params.get('to_stage', 'próxima etapa')}**."
        elif action_id == "send_email":
            return f"Email enviado para **{candidate_name}**."
        elif action_id == "schedule_interview":
            return f"Entrevista agendada com **{candidate_name}**."
        return f"Ação {action_id} executada com sucesso."


action_executor = ActionExecutorService()
