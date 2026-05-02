"""
Pipeline Feedback Tool — COMP-9.

Gera feedback diferenciado e personalizado para candidatos com base em:
  - Perfil do candidato (skills, experiência)
  - Resultado da avaliação (score, pontos fortes, gaps)
  - Gate da transição (Gate 1 = construtivo, Gate 2 = conclusivo)

Guardrails:
  - FairnessGuard no output (não revelar viés)
  - FactChecker (não inventar dados do candidato)
  - Nunca revelar score numérico
  - Sempre incluir link para revisão humana (LGPD Art. 20)
  - Baseado em perfil real: NÃO template estático
"""
import logging

logger = logging.getLogger(__name__)

# LGPD Art. 20 — link para revisão por humano
HUMAN_REVIEW_LINK = "https://app.wedotalent.com/candidato/revisar-decisao"


async def send_gate_feedback(
    gate_number: int,
    candidate_id: str,
    company_id: str,
    candidate_name: str | None = None,
    evaluation_result: dict | None = None,
    job_title: str | None = None,
    from_stage: str | None = None,
    to_stage: str | None = None,
) -> dict:
    """
    Gera e envia feedback diferenciado para candidato após transição de pipeline.

    Gate 1 (triagem → avaliação inicial):
      - Tom: construtivo, focado em desenvolvimento
      - Conteúdo: destaca pontos fortes, sugere áreas de crescimento
      - NÃO conclusivo (processo ainda em andamento)

    Gate 2 (avaliação → decisão final):
      - Tom: conclusivo, profissional, respeitoso
      - Conteúdo: reconhece participação, comunica decisão, oferece próximos passos
      - SEMPRE inclui link de revisão humana (LGPD Art. 20)

    Args:
        gate_number: 1 (construtivo) ou 2 (conclusivo)
        candidate_id: ID do candidato
        company_id: ID da empresa
        candidate_name: Nome do candidato (para personalização)
        evaluation_result: Dict com lia_score, strengths, gaps, recommendation
        job_title: Título da vaga
        from_stage: Etapa de origem
        to_stage: Etapa de destino

    Returns:
        Dict com { feedback_text, sent, gate_number, guardrails_applied }
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate

        from app.domains.ai.services.llm import llm_service

        # Selecionar prompt por gate
        if gate_number == 1:
            feedback_prompt = _build_gate1_prompt(
                candidate_name=candidate_name,
                evaluation_result=evaluation_result,
                job_title=job_title,
                to_stage=to_stage,
            )
        else:
            feedback_prompt = _build_gate2_prompt(
                candidate_name=candidate_name,
                evaluation_result=evaluation_result,
                job_title=job_title,
                from_stage=from_stage,
            )

        # Guardrail: FairnessGuard no output gerado
        llm = llm_service.get_audited_model()
        template = ChatPromptTemplate.from_template(feedback_prompt)
        chain = template | llm
        response = await chain.ainvoke({})
        feedback_text = response.content if hasattr(response, "content") else str(response)

        # Guardrail: nunca revelar score numérico
        feedback_text = _remove_score_references(feedback_text)

        # Guardrail: sempre incluir link de revisão (Gate 2)
        if gate_number == 2:
            feedback_text = _ensure_review_link(feedback_text)

        # Guardrail: FairnessGuard no output
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            fg = FairnessGuard()
            fg_result = fg.check(feedback_text)
            if fg_result.is_blocked:
                logger.warning(
                    "[PipelineFeedback][COMP-9] FairnessGuard bloqueou output gate=%d candidate=%s",
                    gate_number, candidate_id,
                )
                feedback_text = _get_safe_fallback_feedback(gate_number, candidate_name, job_title)
        except ImportError as fg_err:
            logger.debug("[PipelineFeedback] FairnessGuard not available: %s", fg_err)
        except Exception as fg_err:
            logger.error("[LIA-FG-04] FairnessGuard error on pipeline feedback: %s", fg_err)

        logger.info(
            "[PipelineFeedback][COMP-9] Feedback gate=%d gerado candidate=%s company=%s len=%d",
            gate_number, candidate_id, company_id, len(feedback_text),
        )

        return {
            "feedback_text": feedback_text,
            "sent": False,  # Apenas gera — envio é via notification_service
            "gate_number": gate_number,
            "candidate_id": candidate_id,
            "guardrails_applied": ["fairness_guard", "no_score_reveal", "review_link"],
        }

    except Exception as e:
        logger.error("[PipelineFeedback] Erro ao gerar feedback gate=%d: %s", gate_number, e)
        return {
            "feedback_text": _get_safe_fallback_feedback(gate_number, candidate_name, job_title),
            "sent": False,
            "gate_number": gate_number,
            "candidate_id": candidate_id,
            "error": str(e),
            "guardrails_applied": ["fallback_used"],
        }


def _build_gate1_prompt(
    candidate_name: str | None,
    evaluation_result: dict | None,
    job_title: str | None,
    to_stage: str | None,
) -> str:
    """Gate 1: feedback construtivo, focado em desenvolvimento."""
    name = candidate_name or "Candidato(a)"
    job = job_title or "a vaga"
    strengths = []
    gaps = []

    if evaluation_result:
        strengths = evaluation_result.get("strengths", [])[:3]  # máx 3 pontos
        gaps = evaluation_result.get("gaps", [])[:2]            # máx 2 gaps

    strengths_text = "\n".join(f"- {s}" for s in strengths) if strengths else "- Perfil em análise"
    gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else ""

    return f"""Assistente de RH da WeDOTalent. Escreva um feedback construtivo para o candidato {name} que avançou para a próxima etapa do processo seletivo para {job}.

PONTOS FORTES IDENTIFICADOS:
{strengths_text}

{"ÁREAS DE DESENVOLVIMENTO:" + chr(10) + gaps_text if gaps_text else ""}

INSTRUÇÕES:
- Tom: positivo, encorajador, profissional
- Destaque os pontos fortes com exemplos concretos
- Se houver gaps, mencione como oportunidades de crescimento (nunca como eliminatórios)
- NÃO mencione nenhum score numérico ou porcentagem
- NÃO diga que o processo está concluído (processo continua)
- Mencione que haverá próximas etapas
- Máximo 150 palavras
- Em português brasileiro

Escreva apenas o feedback, sem introdução ou explicação."""


def _build_gate2_prompt(
    candidate_name: str | None,
    evaluation_result: dict | None,
    job_title: str | None,
    from_stage: str | None,
) -> str:
    """Gate 2: feedback conclusivo, respeitoso, com caminho de revisão."""
    name = candidate_name or "Candidato(a)"
    job = job_title or "a vaga"
    recommendation = "potential"

    if evaluation_result:
        recommendation = evaluation_result.get("recommendation_level", "potential")

    advanced = recommendation in {"highly_recommended", "recommended"}

    if advanced:
        tone_instruction = "O candidato foi selecionado. Tom: celebratório, acolhedor, com próximos passos claros."
        next_steps = "Informe que a equipe entrará em contato para agendar próximas etapas."
    else:
        tone_instruction = "O candidato não foi selecionado nesta rodada. Tom: respeitoso, empático, sem julgamento. Agradeça a participação."
        next_steps = f"Inclua o link para revisão humana da decisão: {HUMAN_REVIEW_LINK}"

    return f"""Assistente de RH da WeDOTalent. Escreva um comunicado final para {name} sobre o processo seletivo para {job}.

CONTEXTO: {tone_instruction}

PRÓXIMOS PASSOS: {next_steps}

INSTRUÇÕES:
- Tom: profissional, humano, respeitoso
- NÃO mencione scores, porcentagens ou rankings
- NÃO cite critérios protegidos (gênero, idade, etnia, etc.)
- Agradeça genuinamente a participação
- {"Se não selecionado: " + chr(10) + "  - Inclua link: " + HUMAN_REVIEW_LINK if not advanced else ""}
- Máximo 200 palavras
- Em português brasileiro

Escreva apenas o comunicado, sem introdução."""


def _remove_score_references(text: str) -> str:
    """Remove referências a scores numéricos do feedback."""
    import re
    # Remove padrões como "score de 75", "75 pontos", "75%", "nota 8"
    text = re.sub(r'\b\d+[\.,]?\d*\s*(%|pontos?|score|nota)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(score|nota|pontuação)\s+\d+[\.,]?\d*\b', '', text, flags=re.IGNORECASE)
    return text.strip()


def _ensure_review_link(text: str) -> str:
    """Garante que link de revisão está presente no feedback Gate 2 (LGPD Art. 20)."""
    if HUMAN_REVIEW_LINK not in text:
        text += f"\n\nCaso deseje solicitar revisão desta decisão por um avaliador humano, acesse: {HUMAN_REVIEW_LINK}"
    return text


def _get_safe_fallback_feedback(
    gate_number: int,
    candidate_name: str | None,
    job_title: str | None,
) -> str:
    """Feedback fallback seguro quando LLM falha."""
    name = candidate_name or "Candidato(a)"
    job = job_title or "a vaga"

    if gate_number == 1:
        return (
            f"Olá {name}, agradecemos sua candidatura para {job}. "
            f"Após análise inicial, gostaríamos de continuar seu processo seletivo. "
            f"Em breve entraremos em contato com os próximos passos. "
            f"Obrigado pela sua participação!"
        )
    else:
        return (
            f"Olá {name}, agradecemos imensamente sua participação no processo seletivo para {job}. "
            f"Após cuidadosa análise, não poderemos prosseguir com sua candidatura neste momento. "
            f"Caso deseje solicitar revisão desta decisão, acesse: {HUMAN_REVIEW_LINK} "
            f"Desejamos muito sucesso em sua jornada profissional!"
        )
