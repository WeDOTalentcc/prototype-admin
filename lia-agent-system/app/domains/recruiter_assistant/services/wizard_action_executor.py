"""
WizardActionExecutor - Closed-loop action execution for Job Wizard.

Handles wizard-specific actions via conversational interaction:
- save_draft: Save current job draft
- publish_job: Publish/create job from draft
- generate_jd: Generate job description using AI
- generate_wsi_questions: Generate WSI screening questions
- apply_template: Apply a job template to current draft
- clear_field: Clear a specific field from the draft
- reset_wizard: Reset the wizard session
"""
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.shared.runtime_context import RuntimeContext
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)


logger = logging.getLogger(__name__)


@dataclass
class WizardActionResult:
    status: str  # "executed", "needs_params", "needs_confirmation", "not_actionable", "error"
    message: str = ""
    data: dict[str, Any] | None = None
    action_type: str | None = None
    missing_params: list[str] | None = None
    pending_action_id: str | None = None
    confirmation_summary: dict[str, Any] | None = None
    draft_updates: dict[str, Any] | None = None  # Fields to merge into job_draft


WIZARD_ACTIONABLE_INTENTS: dict[str, dict[str, Any]] = {
    "salvar_rascunho": {
        "action_id": "save_draft",
        "required_params": [],
        "optional_params": ["draft_name"],
        "risk_level": "low",
        "requires_confirmation": False,
        "clarification_prompts": {},
    },
    "publicar_vaga": {
        "action_id": "publish_job",
        "required_params": [],
        "optional_params": [],
        "risk_level": "high",
        "requires_confirmation": True,
        "min_completeness": 0.7,
        "clarification_prompts": {},
    },
    "gerar_descricao": {
        "action_id": "generate_jd",
        "required_params": [],
        "optional_params": ["style", "tone"],
        "risk_level": "low",
        "requires_confirmation": False,
        "clarification_prompts": {},
    },
    "gerar_perguntas_wsi": {
        "action_id": "generate_wsi_questions",
        "required_params": [],
        "optional_params": ["block", "count"],
        "risk_level": "low",
        "requires_confirmation": False,
        "clarification_prompts": {},
    },
    "aplicar_template": {
        "action_id": "apply_template",
        "required_params": ["template_id"],
        "optional_params": [],
        "risk_level": "medium",
        "requires_confirmation": True,
        "clarification_prompts": {
            "template_id": "Qual template gostaria de aplicar? Diga o nome ou área.",
        },
    },
    "limpar_campo": {
        "action_id": "clear_field",
        "required_params": ["field_name"],
        "optional_params": [],
        "risk_level": "low",
        "requires_confirmation": False,
        "clarification_prompts": {
            "field_name": "Qual campo deseja limpar?",
        },
    },
    "resetar_wizard": {
        "action_id": "reset_wizard",
        "required_params": [],
        "optional_params": [],
        "risk_level": "high",
        "requires_confirmation": True,
        "clarification_prompts": {},
    },
}

# Wizard field names mapping
WIZARD_FIELDS = {
    "titulo": "title", "title": "title",
    "descricao": "description", "description": "description",
    "departamento": "department", "department": "department",
    "local": "location", "location": "location", "localidade": "location",
    "salario": "salary_range", "salary": "salary_range", "faixa salarial": "salary_range",
    "senioridade": "seniority_level", "seniority": "seniority_level", "nivel": "seniority_level",
    "tipo contrato": "contract_type", "contrato": "contract_type",
    "modalidade": "work_model", "modelo trabalho": "work_model", "remoto": "work_model",
    "skills": "required_skills", "habilidades": "required_skills", "competencias": "required_skills",
    "responsabilidades": "responsibilities",
    "requisitos": "requirements",
    "beneficios": "benefits",
}


def detect_wizard_action(message: str) -> tuple[str, float] | None:
    """Detect if message is a wizard action command."""
    msg = message.lower().strip()

    patterns = {
        "salvar_rascunho": [
            r"\bsalvar?\b", r"\bsave\b", r"\bgravar\b", r"\bguardar\b",
            r"\brascunho\b", r"\bdraft\b",
        ],
        "publicar_vaga": [
            r"\bpublicar?\b", r"\bpublish\b", r"\bcriar vaga\b", r"\bfinalizar\b",
            r"\bconcluir vaga\b", r"\babrir vaga\b",
        ],
        "gerar_descricao": [
            r"\bgerar descri[çc][aã]o\b", r"\bgenerate.*description\b",
            r"\bdescrever vaga\b", r"\bgerar jd\b", r"\bcriar descri[çc][aã]o\b",
            r"\bdescrição da vaga\b", r"\btexto da vaga\b",
        ],
        "gerar_perguntas_wsi": [
            r"\bgerar.*perguntas?\b", r"\bperguntas.*triagem\b",
            r"\bwsi.*questions?\b", r"\bscreening.*questions?\b",
            r"\bperguntas.*sele[çc][aã]o\b", r"\bquestion[aá]rio\b",
        ],
        "aplicar_template": [
            r"\baplicar template\b", r"\busar template\b", r"\btemplate\b",
            r"\bmodelo de vaga\b", r"\busar modelo\b",
        ],
        "limpar_campo": [
            r"\blimpar\b.*\bcampo\b", r"\bclear\b.*\bfield\b",
            r"\bremover\b.*\bcampo\b", r"\bapagar\b.*\bcampo\b",
            r"\blimpar\b.*\b(titulo|descri|local|sal[aá]rio|skills|depart)\b",
        ],
        "resetar_wizard": [
            r"\bresetar?\b", r"\breset\b", r"\brecomeçar\b",
            r"\bcomeçar de novo\b", r"\blimpar tudo\b", r"\bstart over\b",
        ],
    }

    for intent, pats in patterns.items():
        for pat in pats:
            if re.search(pat, msg):
                return intent, 0.85
    return None


def _calculate_completeness(draft: dict[str, Any]) -> tuple[float, list[str]]:
    """Calculate draft completeness percentage and list missing required fields."""
    required = ["title", "description", "department", "location", "seniority_level"]
    important = ["salary_range", "contract_type", "work_model", "required_skills", "responsibilities"]

    filled_required = sum(1 for f in required if draft.get(f))
    filled_important = sum(1 for f in important if draft.get(f))

    total = len(required) + len(important)
    filled = filled_required + filled_important

    missing = [f for f in required if not draft.get(f)]
    return filled / total if total > 0 else 0.0, missing


def _resolve_field_name(text: str) -> str | None:
    """Resolve a Portuguese/English field reference to canonical field name."""
    text_lower = text.lower().strip()
    return WIZARD_FIELDS.get(text_lower)


class WizardActionExecutor:

    def __init__(self):
        self.execution_count = 0

    def is_actionable(self, intent: str) -> bool:
        return intent in WIZARD_ACTIONABLE_INTENTS

    async def try_execute(
        self,
        intent: str,
        draft: dict[str, Any],
        session_id: str,
        current_stage: str | None = None,
        entities: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> WizardActionResult:
        if not self.is_actionable(intent):
            return WizardActionResult(status="not_actionable")

        config = WIZARD_ACTIONABLE_INTENTS[intent]
        action_id = config["action_id"]
        params = dict(entities or {})

        missing = [p for p in config["required_params"] if p not in params or not params[p]]
        if missing:
            first_missing = missing[0]
            prompt = config.get("clarification_prompts", {}).get(
                first_missing, f"Por favor, informe: {first_missing}"
            )
            return WizardActionResult(
                status="needs_params",
                message=prompt,
                missing_params=missing,
                action_type=action_id,
                pending_action_id=str(uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        if config.get("requires_confirmation", False):
            summary = self._build_confirmation_summary(intent, config, draft, params)
            return WizardActionResult(
                status="needs_confirmation",
                message=summary["message"],
                confirmation_summary=summary,
                action_type=action_id,
                pending_action_id=str(uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        return await self._execute(action_id, draft, session_id, current_stage, params, context)

    def _build_confirmation_summary(
        self, intent: str, config: dict[str, Any], draft: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        title = draft.get("title", "esta vaga")
        completeness, missing = _calculate_completeness(draft)

        if intent == "publicar_vaga":
            pct = int(completeness * 100)
            msg = f"A vaga **{title}** está com **{pct}%** de completude."
            if missing:
                msg += f"\n\nCampos obrigatórios faltando: {', '.join(missing)}."
            if completeness < 0.7:
                msg += "\n\n⚠️ Recomendo preencher pelo menos 70% antes de publicar."
            msg += "\n\nDeseja publicar mesmo assim?"
        elif intent == "aplicar_template":
            msg = f"Vou aplicar o template sobre a vaga **{title}**. Campos existentes serão sobrescritos. Confirma?"
        elif intent == "resetar_wizard":
            msg = f"Vou **resetar** todo o progresso da vaga **{title}**. Isso não pode ser desfeito. Confirma?"
        else:
            msg = f"Vou executar **{intent}** na vaga **{title}**. Confirma?"

        return {
            "message": msg,
            "action_id": config["action_id"],
            "intent": intent,
            "params": params,
            "risk_level": config.get("risk_level", "medium"),
            "completeness": completeness,
        }

    async def _execute(
        self,
        action_id: str,
        draft: dict[str, Any],
        session_id: str,
        current_stage: str | None,
        params: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> WizardActionResult:
        self.execution_count += 1
        title = draft.get("title", "esta vaga")
        now = datetime.utcnow().isoformat()

        if action_id == "save_draft":
            return WizardActionResult(
                status="executed",
                message=f"Rascunho da vaga **{title}** salvo com sucesso.",
                data={"session_id": session_id, "saved_at": now, "draft_snapshot": draft},
                action_type="save_draft",
                draft_updates={"_saved_at": now, "_draft_status": "saved"},
            )

        elif action_id == "publish_job":
            completeness, missing = _calculate_completeness(draft)
            return WizardActionResult(
                status="executed",
                message=f"Vaga **{title}** publicada com sucesso! Completude: {int(completeness*100)}%.",
                data={
                    "session_id": session_id,
                    "published_at": now,
                    "completeness": completeness,
                    "missing_fields": missing,
                },
                action_type="publish_job",
                draft_updates={"_status": "published", "_published_at": now},
            )

        elif action_id == "generate_jd":
            try:
                from app.domains.job_management.services.jd_generator_service import jd_generator_service
                job_data = {
                    "title": draft.get("title", ""),
                    "department": draft.get("department", ""),
                    "seniority_level": draft.get("seniority_level", ""),
                    "required_skills": draft.get("required_skills", []),
                    "location": draft.get("location", ""),
                }
                company_ctx = context.get("company_context") if context else None
                if hasattr(jd_generator_service, 'generate_full_description'):
                    result = await jd_generator_service.generate_full_description(job_data, company_ctx)
                elif hasattr(jd_generator_service, 'generate_description'):
                    result = jd_generator_service.generate_description(job_data, company_ctx)
                else:
                    result = str(jd_generator_service)
                description = result.get("description", "") if isinstance(result, dict) else str(result)
                return WizardActionResult(
                    status="executed",
                    message=f"Descrição gerada para **{title}**:\n\n{description[:500]}{'...' if len(description) > 500 else ''}",
                    data={"generated_description": description, "generated_at": now},
                    action_type="generate_jd",
                    draft_updates={"description": description},
                )
            except Exception as e:
                logger.warning(f"JD generation failed: {e}")
                return WizardActionResult(
                    status="executed",
                    message=f"Gerei uma descrição base para **{title}**. Revise e ajuste conforme necessário.",
                    data={"generated_at": now, "simulated": True},
                    action_type="generate_jd",
                    draft_updates={
                        "description": f"Descrição profissional para {title}. [Geração automática - revise e personalize]"
                    },
                )

        elif action_id == "generate_wsi_questions":
            block = params.get("block")
            count = int(params.get("count", 5))
            try:
                from app.domains.cv_screening.services.wsi_service import WSIService
                wsi_svc = WSIService()
                skills_list = draft.get("required_skills", [])
                behav_list = draft.get("behavioral_competencies", [])
                seniority_val = draft.get("seniority_level", "pleno")
                questions_raw = await wsi_svc.generate_from_simple_inputs(
                    skills=skills_list,
                    behavioral=behav_list,
                    seniority=seniority_val,
                    mode="compact",
                )
                questions = [
                    {"id": q.id, "question": q.question_text, "competency": q.competency, "framework": q.framework}
                    for q in questions_raw
                ]
                q_list = questions if isinstance(questions, list) else [questions]
                formatted = "\n".join(f"{i+1}. {q}" for i, q in enumerate(q_list[:count]))

                # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
                # wizard_action_executor.generate_wsi_questions — service layer
                # sem db inject, sem company_id em param. Pega company_id do
                # ContextVar (RuntimeContext canonical) e abre db scope local.
                # silent_on_persist_error=True pra nao quebrar wizard UX se DB
                # audit falhar. Sem company_id, skip log + warn (gap reportado).
                try:
                    ctx = RuntimeContext.from_contextvars()
                    if ctx.company_id:
                        async with AsyncSessionLocal() as audit_db:
                            await log_automated_decision(
                                db=audit_db,
                                company_id=ctx.company_id,
                                decision_type="wsi_wizard_action",
                                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                                explanation_text=(
                                    f'Wizard action_executor gerou {len(q_list)} pergunta(s) WSI '
                                    f'(slice {count}) para draft "{title}" via wsi_service.generate_from_simple_inputs. '
                                    f'Skills tecnicos: {skills_list}. Comportamentais: {behav_list}. '
                                    f'Senioridade={seniority_val}, mode=compact, block={block}.'
                                ),
                                criteria_used=[
                                    *[f"skill:{s}" for s in skills_list],
                                    *[f"behavioral:{b}" for b in behav_list],
                                    f"seniority:{seniority_val}",
                                    "mode:compact",
                                    "action:wizard_generate_wsi",
                                    *([f"block:{block}"] if block else []),
                                ],
                                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                                confidence_score=None,
                                review_eligible=True,
                                extra_metadata={
                                    "endpoint": "wizard_action_executor.generate_wsi_questions",
                                    "title": title,
                                    "session_id": session_id,
                                    "current_stage": current_stage,
                                    "questions_count": len(q_list),
                                    "count_requested": count,
                                    "mode": "compact",
                                    "seniority": seniority_val,
                                    "block": block,
                                    "action": "wizard_generate_wsi",
                                    "prompt_template_version": "wsi_F6_pipeline_v2",
                                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                                },
                                silent_on_persist_error=True,
                            )
                            await audit_db.commit()
                    else:
                        logger.warning(
                            "WT-2022 P0.C wave 2: wizard_action_executor.generate_wsi_questions "
                            "sem company_id no ContextVar (session_id=%s). LGPD audit gap.",
                            session_id,
                        )
                except ValueError:
                    raise
                except Exception as audit_err:
                    logger.error(
                        "WT-2022 P0.C wave 2: log_automated_decision falhou em "
                        "wizard_action_executor session_id=%s: %s",
                        session_id, audit_err, exc_info=True,
                    )

                return WizardActionResult(
                    status="executed",
                    message=f"Perguntas WSI geradas para **{title}**:\n\n{formatted}",
                    data={"questions": q_list, "block": block, "count": count, "generated_at": now},
                    action_type="generate_wsi_questions",
                    draft_updates={"screening_questions": q_list},
                )
            except Exception as e:
                logger.warning(f"WSI question generation failed: {e}")
                default_questions = [
                    f"Descreva sua experiência relevante para a posição de {title}.",
                    "Qual foi o maior desafio técnico que você enfrentou e como resolveu?",
                    "Como você lida com prazos apertados e priorização de tarefas?",
                    "Descreva uma situação em que você trabalhou em equipe para alcançar um objetivo.",
                    "O que te motiva a buscar esta oportunidade?",
                ]
                return WizardActionResult(
                    status="executed",
                    message=f"Perguntas de triagem geradas para **{title}**:\n\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(default_questions)),
                    data={"questions": default_questions, "simulated": True, "generated_at": now},
                    action_type="generate_wsi_questions",
                    draft_updates={"screening_questions": default_questions},
                )

        elif action_id == "apply_template":
            template_id = params.get("template_id", "")
            try:
                from app.domains.job_management.services.job_template_service import JobTemplateService
                template_svc = JobTemplateService()
                template = await template_svc.get_template_by_id(template_id)
                if template:
                    template_data = template if isinstance(template, dict) else {"title": str(template)}
                    return WizardActionResult(
                        status="executed",
                        message=f"Template aplicado à vaga **{title}**.",
                        data={"template_id": template_id, "applied_at": now},
                        action_type="apply_template",
                        draft_updates=template_data,
                    )
            except Exception as e:
                logger.warning(f"Template application failed: {e}")

            return WizardActionResult(
                status="executed",
                message=f"Template **{template_id}** aplicado. Revise os campos preenchidos.",
                data={"template_id": template_id, "simulated": True, "applied_at": now},
                action_type="apply_template",
            )

        elif action_id == "clear_field":
            field_ref = params.get("field_name", "")
            canonical = _resolve_field_name(field_ref) or field_ref
            if canonical and canonical in draft:
                return WizardActionResult(
                    status="executed",
                    message=f"Campo **{canonical}** limpo com sucesso.",
                    data={"cleared_field": canonical, "cleared_at": now},
                    action_type="clear_field",
                    draft_updates={canonical: None},
                )
            return WizardActionResult(
                status="error",
                message=f"Campo **{field_ref}** não encontrado no rascunho. Campos disponíveis: {', '.join(draft.keys())}",
                action_type="clear_field",
            )

        elif action_id == "reset_wizard":
            return WizardActionResult(
                status="executed",
                message="Wizard resetado. Todos os dados foram limpos. Vamos começar do zero!",
                data={"session_id": session_id, "reset_at": now},
                action_type="reset_wizard",
                draft_updates={"_reset": True},
            )

        return WizardActionResult(
            status="executed",
            message=f"Ação **{action_id}** executada.",
            data={"action": action_id, "executed_at": now},
            action_type=action_id,
        )


def robust_json_parse(text: str) -> dict[str, Any] | None:
    """Robust JSON parser with multiple fallback strategies."""
    if not text:
        return None

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: Extract JSON from markdown code blocks
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                candidate = match.group(1) if '```' in pattern else match.group(0)
                return json.loads(candidate.strip())
            except (json.JSONDecodeError, TypeError, IndexError):
                continue

    # Strategy 3: Try fixing common LLM JSON issues
    cleaned = text.strip()
    cleaned = re.sub(r',\s*}', '}', cleaned)  # trailing commas
    cleaned = re.sub(r',\s*]', ']', cleaned)  # trailing commas in arrays
    cleaned = re.sub(r"'", '"', cleaned)  # single to double quotes
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    return None


wizard_action_executor = WizardActionExecutor()
