"""
Pipeline Stage Context — Dynamic context per action_behavior for transitions.

Maps each action_behavior to its available capabilities, expected preferences,
and contextual prompts. Used by the system prompt and tool registry to scope
what the agent can do for each transition type.
"""
from typing import Any

STAGE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "screening": {
        "label": "Triagem",
        "description": "Configurar e iniciar triagem do candidato (WSI, texto, vídeo)",
        "available_actions": [
            "configurar tipo de triagem (voz, texto, vídeo)",
            "definir prazo e urgência",
            "personalizar mensagem de convite",
            "solicitar coleta de informação adicional na triagem",
        ],
        "extractable_preferences": ["screening_type", "deadline", "urgency", "custom_message", "additional_questions"],
        "proactive_questions": [
            "Que tipo de triagem prefere para este candidato? (voz, texto ou vídeo)",
            "Quer incluir alguma pergunta específica sobre pretensão salarial ou disponibilidade?",
            "Tem urgência no prazo? (padrão: 3 dias úteis)",
        ],
        "default_action": "lia_auto",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "get_candidate_salary_info", "update_candidate_field", "request_data_collection",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "scheduling": {
        "label": "Agendamento de Entrevista",
        "description": "Agendar, cancelar ou reagendar entrevista com o candidato (data, hora, formato, entrevistador)",
        "available_actions": [
            "definir data, hora e formato (presencial/remoto/híbrido)",
            "indicar entrevistador(es)",
            "definir duração",
            "combinar ações (agendar + solicitar info)",
            "personalizar convite",
            "cancelar entrevista agendada (atualiza DB + Graph + notifica candidato)",
            "reagendar para nova data/hora (atualiza DB + Graph + notifica candidato)",
        ],
        "extractable_preferences": [
            "date", "time", "format", "interviewer", "duration", "location", "notes",
            "cancellation_reason", "new_date", "new_time", "notify_channel",
        ],
        "proactive_questions": [
            "Já tem entrevistador definido? Se sim, qual o nome?",
            "Qual formato prefere? (presencial, videochamada ou híbrido)",
            "Tem plataforma de preferência? (Google Meet, Teams, Zoom...)",
            "Quer incluir alguma solicitação adicional, como pretensão salarial?",
            "Qual o motivo do cancelamento? (opcional — ajuda a personalizar a mensagem ao candidato)",
            "Quer avisar o candidato por email ou WhatsApp?",
            "Quer mover o candidato de volta à triagem ou para outra etapa após cancelar?",
        ],
        "default_action": "lia_auto",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "get_candidate_salary_info", "update_candidate_field", "request_data_collection",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "schedule_secondary_task",
            "personalize_communication", "check_candidate_availability",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "evaluation": {
        "label": "Avaliação / Teste",
        "description": "Enviar teste ou avaliação ao candidato (técnico, case, idioma)",
        "available_actions": [
            "escolher tipo de teste (técnico, case, inglês)",
            "definir prazo",
            "personalizar instruções",
        ],
        "extractable_preferences": ["test_type", "deadline", "custom_instructions"],
        "proactive_questions": [
            "Que tipo de avaliação faz mais sentido? (técnico, case de negócio, inglês, ou misto)",
            "Quer que eu consulte o perfil do candidato para sugerir o tipo de teste mais adequado?",
            "Tem prazo definido para entrega? (padrão: 5 dias úteis)",
            "Quer adicionar instruções específicas ou contexto para o candidato?",
        ],
        "default_action": "lia_auto",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "get_candidate_salary_info", "update_candidate_field", "request_data_collection",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "verification": {
        "label": "Verificação / Documentação",
        "description": "Solicitar documentos ou referências ao candidato",
        "available_actions": [
            "definir quais documentos solicitar",
            "definir prazo",
            "verificar status de documentos pendentes",
        ],
        "extractable_preferences": ["documents", "deadline", "notes"],
        "proactive_questions": [
            "Quais documentos precisa solicitar? (CPF, comprovante de residência, diploma, CTPS...)",
            "Vai solicitar referências profissionais também?",
            "Tem prazo definido para entrega? (padrão: 5 dias úteis)",
        ],
        "default_action": "lia_auto",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "update_candidate_field", "request_data_collection",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "offer": {
        "label": "Proposta",
        "description": "Preparar e enviar proposta ao candidato",
        "available_actions": [
            "definir faixa salarial e benefícios",
            "consultar pretensão salarial do candidato",
            "solicitar análise de fit cultural",
            "personalizar proposta",
        ],
        "extractable_preferences": ["salary_range", "benefits", "start_date", "contract_type", "notes"],
        "proactive_questions": [
            "Quer verificar a pretensão salarial atual antes de montar a proposta?",
            "Qual o pacote de benefícios? (VR, VT, plano de saúde, bônus...)",
            "Vai incluir participação nos resultados (PLR) ou stock options?",
            "Qual a data de início prevista?",
            "Formato do contrato: CLT, PJ ou outro?",
        ],
        "default_action": "lia_auto",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "get_candidate_salary_info", "update_candidate_field", "request_data_collection",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "conclusion_rejected": {
        "label": "Reprovação",
        "description": "Registrar reprovação do candidato com motivo e feedback",
        "available_actions": [
            "informar motivo da reprovação",
            "pedir sugestão de motivo baseado no perfil",
            "personalizar feedback ao candidato",
            "solicitar anonimização LGPD",
        ],
        "extractable_preferences": ["rejection_reason", "feedback_message", "anonymize_lgpd"],
        "proactive_questions": [
            "Qual o motivo principal da reprovação? (seja objetivo: falta de experiência técnica, pretensão fora da faixa...)",
            "Quer que eu consulte o perfil e o WSI para sugerir um motivo objetivo?",
            "Quer personalizar o feedback enviado ao candidato ou usar o padrão?",
            "Precisa solicitar anonimização dos dados (LGPD) após a reprovação?",
        ],
        "default_action": "manual",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "update_candidate_field",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "check_rejection_fairness",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "conclusion_hired": {
        "label": "Contratação",
        "description": "Confirmar contratação do candidato",
        "available_actions": [
            "confirmar dados de contratação",
            "solicitar onboarding tasks",
            "notificar equipe",
        ],
        "extractable_preferences": ["start_date", "contract_type", "onboarding_notes"],
        "proactive_questions": [
            "Qual a data de início do candidato?",
            "Quer iniciar as tasks de onboarding automaticamente? (envio de contrato, solicitação de docs admissionais, integração com time)",
            "Tem alguma observação específica para o time de RH ou gestor?",
        ],
        "default_action": "manual",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "get_candidate_salary_info", "update_candidate_field",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "conclusion_declined": {
        "label": "Recusa de Proposta",
        "description": "Registrar que o candidato recusou a proposta",
        "available_actions": [
            "registrar motivo da recusa",
            "personalizar follow-up",
        ],
        "extractable_preferences": ["decline_reason", "follow_up_notes"],
        "proactive_questions": [
            "O candidato informou o motivo da recusa? (salário abaixo da expectativa, outra oferta, localização...)",
            "Quer registrar um follow-up para contato futuro? (ex: banco de talentos, próximas vagas)",
        ],
        "default_action": "manual",
        "tools": [
            "get_candidate_profile", "get_candidate_screening_results",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context", "personalize_communication",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
    "passive": {
        "label": "Movimentação Simples",
        "description": "Mover candidato para próxima etapa sem ação automatizada",
        "available_actions": [
            "adicionar observações",
        ],
        "extractable_preferences": ["notes"],
        "proactive_questions": [
            "Quer adicionar alguma observação sobre essa movimentação?",
        ],
        "default_action": "just_move",
        "tools": [
            "get_candidate_profile", "get_candidate_wsi_scores", "get_candidate_screening_results",
            "update_candidate_field",
            "get_stage_sub_statuses", "suggest_sub_status", "extract_preferences",
            "validate_transition", "get_job_context",
            "get_recruiter_preferences", "save_recruiter_preference",
            "get_interview_details", "cancel_interview", "reschedule_interview",
        ],
    },
}


def get_stage_capabilities(action_behavior: str) -> dict[str, Any]:
    return STAGE_CAPABILITIES.get(action_behavior, STAGE_CAPABILITIES["passive"])


def get_allowed_tools_for_behavior(action_behavior: str) -> list[str]:
    caps = get_stage_capabilities(action_behavior)
    return caps.get("tools", [])


def get_stage_context_prompt(
    action_behavior: str,
    candidate_name: str = "",
    job_title: str = "",
    from_stage: str = "",
    to_stage: str = "",
) -> str:
    caps = get_stage_capabilities(action_behavior)
    actions_list = "\n".join(f"  - {a}" for a in caps["available_actions"])
    prefs_list = ", ".join(caps["extractable_preferences"])
    proactive_qs = caps.get("proactive_questions", [])
    proactive_section = ""
    if proactive_qs:
        qs_text = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(proactive_qs))
        proactive_section = f"\n\nPERGUNTAS PROATIVAS SUGERIDAS para este behavior (use quando o recrutador não especificar detalhes):\n{qs_text}"

    return f"""CONTEXTO DA TRANSIÇÃO ATUAL:
- Tipo: {caps['label']} ({action_behavior})
- Descrição: {caps['description']}
- Candidato: {candidate_name or 'Não informado'}
- Vaga: {job_title or 'Não informada'}
- Etapa origem: {from_stage}
- Etapa destino: {to_stage}
- Ação padrão: {caps['default_action']}

AÇÕES DISPONÍVEIS para este tipo de transição:
{actions_list}

PREFERÊNCIAS EXTRAÍVEIS: {prefs_list}{proactive_section}"""
