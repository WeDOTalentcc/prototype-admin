"""
Job-wizard routes:
  POST /lia/job-wizard/interpret
  POST /lia/job-wizard/orchestrate
  POST /lia/job-wizard/salary-benchmark
  POST /lia/job-wizard/evaluate
  POST /lia/job-wizard/step
"""

import json
import re
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.domains.ai.services.llm import LLMService, get_llm_service

from ._shared import (
    # constants
    STAGE_MAP,
    STAGE_NAMES,
    STAGE_ORDER,
    WIZARD_ORCHESTRATOR_PROMPT,
    WIZARD_STAGES_INFO,
    # imports needed by routes
    EnhancedIntentType,
    # models
    InterpretMessageAction,
    InterpretMessageRequest,
    InterpretMessageResponse,
    SalaryBenchmarkRequest,
    SalaryBenchmarkResponse,
    WizardEvaluateCompensation,
    WizardEvaluateRequest,
    WizardEvaluateResponse,
    WizardEvaluateSuggestion,
    WizardOrchestrationResult,
    WizardOrchestratorAction,
    WizardOrchestratorRequest,
    WizardOrchestratorResponse,
    WizardStepRequest,
    WizardStepResponse,
    enhanced_intent_classifier,
    # services
    job_insights_service,
    llm_service,
    logger,
    market_benchmark_service,
)

router = APIRouter()


@router.post("/job-wizard/interpret", response_model=InterpretMessageResponse)
async def interpret_user_message(
    request: InterpretMessageRequest
):
    """
    Interpret user message using AI to determine intent and action.

    This endpoint uses the enhanced intent classifier to understand
    what the user wants to do, providing intelligent conversation flow.
    """
    try:
        f"Stage: {STAGE_NAMES.get(request.current_stage, request.current_stage)}"
        filled_fields = request.context.get('filled_fields', []) if request.context else []

        classification = await enhanced_intent_classifier.classify(
            user_input=request.message,
            stage=STAGE_MAP.get(request.current_stage, 1),
            filled_fields=filled_fields
        )

        logger.info(f"Message interpreted: '{request.message[:50]}...' -> {classification.intent_type} (confidence: {classification.confidence})")

        action = InterpretMessageAction.OTHER
        should_advance = False
        target_stage = None
        lia_response = None

        if classification.intent_type == EnhancedIntentType.CONFIRM:
            action = InterpretMessageAction.CONFIRM
            should_advance = True
            current_idx = STAGE_ORDER.index(request.current_stage) if request.current_stage in STAGE_ORDER else 0
            if current_idx < len(STAGE_ORDER) - 1:
                target_stage = STAGE_ORDER[current_idx + 1]
            lia_response = "Entendido! Avançando para a próxima etapa..."

        elif classification.intent_type == EnhancedIntentType.NAVIGATION:
            action = InterpretMessageAction.ADVANCE_STAGE
            should_advance = True
            current_idx = STAGE_ORDER.index(request.current_stage) if request.current_stage in STAGE_ORDER else 0
            if current_idx < len(STAGE_ORDER) - 1:
                target_stage = STAGE_ORDER[current_idx + 1]
            lia_response = f"Certo! Vamos para {STAGE_NAMES.get(target_stage, 'próxima etapa')}."

        elif classification.intent_type == EnhancedIntentType.QUESTION:
            action = InterpretMessageAction.ASK_QUESTION
            lia_response = f"Boa pergunta! Na etapa de **{STAGE_NAMES.get(request.current_stage, 'atual')}**, posso esclarecer o que precisar. Qual é a sua dúvida?"

        elif classification.intent_type == EnhancedIntentType.CORRECTION:
            action = InterpretMessageAction.UPDATE_FIELD
            lia_response = "Entendido, vou atualizar as informações conforme solicitado."

        elif classification.intent_type == EnhancedIntentType.CREATE_JOB or classification.intent_type == EnhancedIntentType.UPDATE_FIELD:
            action = InterpretMessageAction.PROVIDE_DATA
            ents = classification.entities
            parts = []
            if ents:
                if getattr(ents, "cargo", None):
                    parts.append(f"cargo: **{ents.cargo}**")
                if getattr(ents, "senioridade", None):
                    parts.append(f"senioridade: **{ents.senioridade}**")
                if getattr(ents, "modelo_trabalho", None):
                    parts.append(f"modelo: **{ents.modelo_trabalho}**")
                if getattr(ents, "localizacao", None):
                    parts.append(f"local: **{ents.localizacao}**")
                if getattr(ents, "skills_tecnicas", None):
                    skills_str = ", ".join(getattr(ents, "skills_tecnicas", [])[:4])
                    parts.append(f"skills: **{skills_str}**")
            if parts:
                lia_response = f"✅ Registrado! {', '.join(parts).capitalize()}. Deseja adicionar mais detalhes ou podemos avançar?"
            else:
                lia_response = "✅ Informações registradas. Deseja adicionar mais detalhes ou podemos avançar para a próxima etapa?"

        elif classification.intent_type == EnhancedIntentType.REJECT:
            action = InterpretMessageAction.REJECT
            lia_response = "Entendido. O que você gostaria de ajustar?"

        elif classification.intent_type == EnhancedIntentType.HELP:
            action = InterpretMessageAction.HELP
            lia_response = f"Estou aqui para ajudar! Na etapa de **{STAGE_NAMES.get(request.current_stage, 'atual')}**, você pode..."

        entities_dict = classification.entities.to_dict() if classification.entities else {}

        return InterpretMessageResponse(
            action=action,
            confidence=classification.confidence,
            extracted_entities=entities_dict if entities_dict else None,
            lia_response=lia_response,
            should_advance=should_advance,
            target_stage=target_stage,
            clarification_needed=classification.needs_clarification,
            clarification_question=classification.clarification_question,
            reasoning=classification.reasoning
        )

    except Exception as e:
        logger.error(f"Error interpreting message: {e}")
        return InterpretMessageResponse(
            action=InterpretMessageAction.OTHER,
            confidence=0.5,
            lia_response="Desculpe, não consegui entender completamente. Pode reformular?",
            reasoning=str(e)
        )


@router.post("/job-wizard/orchestrate", response_model=WizardOrchestratorResponse)
async def orchestrate_wizard_message(
    request: WizardOrchestratorRequest,
    current_user: User = Depends(get_current_user_or_demo),
    llm_svc: LLMService = Depends(get_llm_service),
):
    """
    Intelligent orchestrator for job wizard conversations.

    This endpoint receives full context and uses LLM to make intelligent
    decisions about how to handle user messages in each stage.

    When use_structured_outputs=True, uses the structured output feature
    for more reliable JSON parsing directly via LLM provider capabilities.
    """
    try:
        stage_info = WIZARD_STAGES_INFO.get(request.current_stage, {
            "name": request.current_stage,
            "purpose": "Etapa do wizard",
            "required_fields": [],
            "optional_fields": [],
            "next_stage": None
        })

        collected = request.collected_data or {}
        required = stage_info.get("required_fields", [])
        missing = [f for f in required if not collected.get(f)]

        collected_summary = "\n".join([
            f"- {k}: {v}" for k, v in collected.items() if v
        ]) or "Nenhum dado coletado ainda"

        missing_summary = ", ".join(missing) if missing else "Todos os campos obrigatórios preenchidos"

        history_text = ""
        if request.conversation_history:
            history_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in request.conversation_history[-5:]
            ])
        else:
            history_text = "Início da conversa"

        if request.use_structured_outputs:
            system_prompt = f"""Você é LIA, uma assistente inteligente ajudando recrutadores a criar vagas.

## ETAPA ATUAL: {stage_info.get("name", request.current_stage)}
**Propósito:** {stage_info.get("purpose", "")}
**Campos obrigatórios:** {", ".join(stage_info.get("required_fields", [])) or "Nenhum"}
**Campos opcionais:** {", ".join(stage_info.get("optional_fields", [])) or "Nenhum"}
**Próxima etapa:** {stage_info.get("next_stage") or "Finalização"}

## DADOS COLETADOS
{collected_summary}

## CAMPOS FALTANTES
{missing_summary}

Analise a mensagem do usuário e decida qual ação tomar.
Ações disponíveis:
- respond: Responder ao usuário com informações úteis
- advance_stage: Avançar para a próxima etapa
- update_fields: Atualizar campos da vaga com base no input
- request_clarification: Pedir mais detalhes se algo não estiver claro
- provide_suggestion: Sugerir valores para campos
- validate_data: Validar dados fornecidos"""

            messages = [
                {"role": "user", "content": f"Histórico:\n{history_text}\n\nMensagem atual: {request.message}"}
            ]

            try:
                provider = request.llm_provider or "gemini"
                result = await llm_service.generate_structured(
                    messages=messages,
                    output_model=WizardOrchestrationResult,
                    provider=provider,
                    system_prompt=system_prompt,
                    max_tokens=1000
                )

                try:
                    action = WizardOrchestratorAction(result.action)
                except ValueError:
                    action = WizardOrchestratorAction.RESPOND

                logger.info(f"Structured orchestration: action={action.value}, confidence={result.confidence}")

                return WizardOrchestratorResponse(
                    action=action,
                    response=result.response,
                    updated_fields=result.updated_fields,
                    target_stage=result.target_stage,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    suggestions=result.suggestions,
                    validation_errors=result.validation_errors
                )

            except ValueError as e:
                logger.warning(f"Structured output failed, falling back to legacy: {e}")

        prompt = WIZARD_ORCHESTRATOR_PROMPT.format(
            stage_name=stage_info.get("name", request.current_stage),
            stage_purpose=stage_info.get("purpose", ""),
            required_fields=", ".join(stage_info.get("required_fields", [])) or "Nenhum",
            optional_fields=", ".join(stage_info.get("optional_fields", [])) or "Nenhum",
            next_stage=stage_info.get("next_stage") or "Finalização",
            collected_data_summary=collected_summary,
            missing_fields=missing_summary,
            conversation_history=history_text,
            user_message=request.message
        )

        response_text = await llm_svc.generate(
            prompt=prompt,
            provider="gemini"
        )

        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response_text)

            action_str = parsed.get("action", "respond")
            try:
                action = WizardOrchestratorAction(action_str)
            except ValueError:
                action = WizardOrchestratorAction.RESPOND

            return WizardOrchestratorResponse(
                action=action,
                response=parsed.get("response", "Entendi sua mensagem."),
                updated_fields=parsed.get("updated_fields"),
                target_stage=parsed.get("target_stage"),
                confidence=parsed.get("confidence", 0.8),
                reasoning=parsed.get("reasoning"),
                suggestions=parsed.get("suggestions"),
                validation_errors=parsed.get("validation_errors")
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse orchestrator response as JSON: {e}")
            return WizardOrchestratorResponse(
                action=WizardOrchestratorAction.RESPOND,
                response=response_text,
                confidence=0.6,
                reasoning="Resposta não estruturada do LLM"
            )

    except Exception as e:
        logger.error(f"Error in wizard orchestrator: {e}")
        return WizardOrchestratorResponse(
            action=WizardOrchestratorAction.RESPOND,
            response="Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?",
            confidence=0.3,
            reasoning=str(e)
        )


@router.post("/job-wizard/salary-benchmark", response_model=SalaryBenchmarkResponse)
async def get_salary_benchmark(
    request: SalaryBenchmarkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get salary benchmark data for a job role.

    Combines internal company data with external market data.
    """
    job_insights_svc = job_insights_service
    try:

        internal_benchmark = {}
        market_benchmark = {}
        combined = {}

        try:
            internal_benchmark = await job_insights_svc.get_salary_benchmark(
                db=db,
                company_id=current_user.company_id,
                role=request.job_title,
                seniority=request.seniority,
                location=request.location
            )
        except Exception as e:
            logger.warning(f"Failed to get internal salary benchmark: {e}")
            internal_benchmark = {"sample_size": 0}

        try:
            market_benchmark = await market_benchmark_service.search_salary_benchmark(
                role=request.job_title,
                seniority=request.seniority,
                location=request.location
            )
        except Exception as e:
            logger.warning(f"Failed to get market salary benchmark: {e}")
            market_benchmark = {}

        try:
            combined = market_benchmark_service.combine_with_internal(
                internal_data=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
                market_data=market_benchmark
            )
        except Exception as e:
            logger.warning(f"Failed to combine salary benchmarks: {e}")
            combined = {}

        return SalaryBenchmarkResponse(
            internal=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
            market=market_benchmark if market_benchmark.get("min") else None,
            combined=combined if combined.get("min") else None
        )

    except Exception as e:
        logger.error(f"Error fetching salary benchmark: {e}")
        return SalaryBenchmarkResponse()


@router.post("/job-wizard/evaluate", response_model=WizardEvaluateResponse)
async def evaluate_wizard_input(
    request: WizardEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    llm_svc: LLMService = Depends(get_llm_service),
):
    """
    Evaluate user input for job wizard and extract structured data using AI.

    This endpoint:
    - Extracts job criteria (title, salary, skills, etc.) from natural language input
    - Provides salary analysis comparing to market benchmarks
    - Suggests additional competencies based on the role
    - Returns confidence scores and field origins
    """

    conversation_id = request.conversation_id or str(uuid4())
    user_input = request.user_input
    context = request.context or {}

    detected_fields: dict[str, Any] = {}
    suggestions: list[WizardEvaluateSuggestion] = []
    compensation_analysis = None
    lia_message = ""
    overall_confidence = 0.7

    try:
        extraction_prompt = f"""Analise o texto abaixo e extraia informações sobre uma vaga de emprego.

Texto do usuário:
"{user_input}"

Contexto adicional: {json.dumps(context, ensure_ascii=False) if context else "Nenhum"}

Extraia as seguintes informações em formato JSON:
{{
    "title": "título da vaga (string ou null)",
    "seniority": "nível (Júnior, Pleno, Sênior, Especialista ou null)",
    "department": "departamento (string ou null)",
    "manager": "nome do gestor SOMENTE se explicitamente mencionado (string ou null)",
    "manager_email": "email do gestor SOMENTE se explicitamente mencionado (string ou null)",
    "responsibilities": ["lista de responsabilidades"],
    "technical_skills": ["lista de competências técnicas"],
    "behavioral_skills": ["lista de competências comportamentais"],
    "salary_min": número mínimo de salário ou null,
    "salary_max": número máximo de salário ou null,
    "work_model": "modelo (Remoto, Presencial, Híbrido ou null)",
    "location": "localização (string ou null)",
    "employment_type": "tipo (CLT, PJ, Estágio ou null)",
    "is_confidential": boolean ou null,
    "is_affirmative": boolean indicando se é vaga afirmativa/inclusiva (true/false/null),
    "affirmative_criteria_primary": "critério afirmativo principal - PcD, Mulheres, LGBTQIA+, Pessoas Negras, etc (string ou null)",
    "affirmative_criteria_secondary": "critério afirmativo secundário se houver (string ou null)",
    "affirmative_description": "descrição ou contexto da ação afirmativa mencionada (string ou null)",
    "analysis": {{
        "salary_feedback": "feedback sobre o salário informado comparado ao mercado",
        "skills_suggestions": ["sugestões de competências adicionais para este cargo"],
        "completeness_score": número de 0 a 1 indicando completude dos dados
    }}
}}

IMPORTANTE:
- Se o usuário informou um valor de salário, converta para número (ex: "15k" = 15000, "R$ 10.000" = 10000)
- Para competências, sugira adições relevantes baseadas no cargo
- Forneça feedback construtivo sobre o salário
- Para vaga afirmativa: detecte expressões como "vaga afirmativa", "ação afirmativa", "exclusiva para PcD", "exclusiva para mulheres", "vaga inclusiva", "diversidade", etc. Se disser "não é afirmativa" ou "não é vaga afirmativa", is_affirmative deve ser false. Se não mencionar, deixe null
- Para o gestor/manager: Extraia se o usuário mencionar explicitamente um nome ou área (ex: "gestor: Carlos Silva", "equipe do João", "reportando para Maria", "área de TI", "departamento de infraestrutura"). Também reconheça formatos como "gestor: nome", "gestor/área: valor", "departamento: nome". NÃO invente nomes se não forem mencionados

Retorne APENAS o JSON, sem texto adicional."""

        response = await llm_svc.generate_native_gemini(
            contents=extraction_prompt,
            model="gemini-2.5-flash",
        )

        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        extracted = json.loads(response_text)

        detected_fields = {
            "title": extracted.get("title"),
            "job_title": extracted.get("title"),
            "seniority": extracted.get("seniority"),
            "department": extracted.get("department"),
            "manager": extracted.get("manager"),
            "manager_email": extracted.get("manager_email"),
            "responsibilities": extracted.get("responsibilities", []),
            "technical_skills": extracted.get("technical_skills", []),
            "behavioral_skills": extracted.get("behavioral_skills", []),
            "salary_min": extracted.get("salary_min"),
            "salary_max": extracted.get("salary_max"),
            "work_model": extracted.get("work_model"),
            "location": extracted.get("location"),
            "employment_type": extracted.get("employment_type"),
            "is_confidential": extracted.get("is_confidential"),
            "is_affirmative": extracted.get("is_affirmative"),
            "affirmative_criteria_primary": extracted.get("affirmative_criteria_primary"),
            "affirmative_criteria_secondary": extracted.get("affirmative_criteria_secondary"),
            "affirmative_description": extracted.get("affirmative_description")
        }

        is_aff = extracted.get("is_affirmative")
        aff_primary = extracted.get("affirmative_criteria_primary")
        logger.info(f"[WizardEvaluate] Affirmative action detection: is_affirmative={is_aff}, primary={aff_primary}")

        affirmative_keys = {"is_affirmative", "affirmative_criteria_primary", "affirmative_criteria_secondary", "affirmative_description"}
        detected_fields = {k: v for k, v in detected_fields.items() if v is not None or k in affirmative_keys}

        analysis = extracted.get("analysis", {})
        completeness = analysis.get("completeness_score", 0.5)
        overall_confidence = min(0.95, completeness + 0.2)

        if detected_fields.get("salary_min") or detected_fields.get("salary_max"):
            salary_min = detected_fields.get("salary_min", 0)
            salary_max = detected_fields.get("salary_max", salary_min * 1.3 if salary_min else 0)

            compensation_analysis = WizardEvaluateCompensation(
                salary={
                    "proposed_min": salary_min,
                    "proposed_max": salary_max,
                    "market_min": salary_min * 0.9,
                    "market_max": salary_max * 1.1,
                    "market_percentile": 50,
                    "data_sources": ["market_benchmark", "internal_history"]
                },
                overall_assessment=analysis.get("salary_feedback", "Faixa salarial dentro da média do mercado."),
                summary=f"Salário proposto: R$ {salary_min:,.0f} - R$ {salary_max:,.0f}"
            )

            suggestions.append(WizardEvaluateSuggestion(
                field="salary_range",
                value={"min": salary_min, "max": salary_max},
                source="user_input",
                confidence=0.9,
                reason=analysis.get("salary_feedback")
            ))

        skills_suggestions = analysis.get("skills_suggestions", [])
        for skill in skills_suggestions:
            suggestions.append(WizardEvaluateSuggestion(
                field="technical_skills",
                value=skill,
                source="market_benchmark",
                confidence=0.75,
                reason=f"Competência comum para {detected_fields.get('title', 'este cargo')}"
            ))

        message_parts = []
        if detected_fields.get("title"):
            message_parts.append(f"Entendi! Vaga para **{detected_fields.get('title')}**")
            if detected_fields.get("seniority"):
                message_parts[-1] += f" ({detected_fields.get('seniority')})"
            message_parts[-1] += "."

        if detected_fields.get("salary_min"):
            salary_feedback = analysis.get("salary_feedback", "")
            if salary_feedback:
                message_parts.append(f"💰 {salary_feedback}")

        if skills_suggestions:
            message_parts.append(f"💡 Sugestões de competências: {', '.join(skills_suggestions[:3])}")

        if detected_fields.get("is_affirmative") is True:
            affirmative_primary = detected_fields.get("affirmative_criteria_primary", "")
            if affirmative_primary:
                message_parts.append(f"✅ Vaga afirmativa detectada: **{affirmative_primary}**")
            else:
                message_parts.append("✅ Vaga afirmativa detectada")

        if not message_parts:
            message_parts.append("Recebi suas informações. Por favor, continue descrevendo a vaga para que eu possa ajudar melhor.")

        lia_message = "\n\n".join(message_parts)

        logger.info(f"[WizardEvaluate] Extracted fields: {list(detected_fields.keys())}, confidence: {overall_confidence:.2f}")

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        lia_message = "Recebi suas informações. Por favor, continue descrevendo a vaga com mais detalhes."
        overall_confidence = 0.5
    except Exception as e:
        logger.error(f"Error in wizard evaluation: {e}")
        lia_message = "Entendi suas informações. Por favor, continue descrevendo a vaga."
        overall_confidence = 0.5

    return WizardEvaluateResponse(
        conversation_id=conversation_id,
        detected_fields=detected_fields,
        compensation_analysis=compensation_analysis,
        suggestions=suggestions,
        lia_message=lia_message,
        overall_confidence=overall_confidence
    )


@router.post("/job-wizard/step", response_model=WizardStepResponse)
async def process_wizard_step(
    request: WizardStepRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Process a step in the conversational job creation wizard."""
    company_id = current_user.company_id
    recruiter_id = str(current_user.id)
    from app.domains.job_management.services.wizard_step_service import wizard_step_service
    return await wizard_step_service.process(request, db, company_id, recruiter_id)
