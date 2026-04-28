"""
Stage 5 — WSI Questions handler for the wizard step service.
"""
import logging

logger = logging.getLogger(__name__)


async def handle_wsi_questions(
    job_draft: dict,
    suggestions_data: dict,
    db=None,
    company_id: str | None = None,
) -> tuple[str, dict]:
    """
    Handle stage 5: WSI question generation.

    Returns:
        (lia_message, suggestions_data)
    """
    detected_tech = job_draft.get('competenciasTecnicas') or job_draft.get('detected_skills') or []
    detected_behav = job_draft.get('competenciasComportamentais') or job_draft.get('behavioral_skills') or []

    if isinstance(detected_tech, str):
        detected_tech = [detected_tech]
    if isinstance(detected_behav, str):
        detected_behav = [detected_behav]

    # F.3 apply_learning: filter out competencies company previously rejected
    if db is not None and company_id and (detected_tech or detected_behav):
        try:
            from app.domains.analytics.services.feedback_learning_service import feedback_learning_service
            _al_role = job_draft.get("cargo") or job_draft.get("job_title") or ""
            _al_seniority = job_draft.get("senioridade") or job_draft.get("seniority") or "Pleno"
            _al_adjusted = await feedback_learning_service.apply_learning(
                db=db,
                company_id=company_id,
                suggestion={"skills": detected_tech + detected_behav},
                role=_al_role,
                seniority=_al_seniority,
            )
            if _al_adjusted:
                suggestions_data["learning_adjustments"] = _al_adjusted
        except Exception as _al_exc:
            logger.warning("apply_learning failed in stage_wsi: %s", _al_exc)

    wsi_competency_summary = ""
    wsi_question_suggestions = []

    if detected_tech or detected_behav:
        wsi_competency_summary = "\n\n📋 **Competências identificadas para triagem:**"

        if detected_tech:
            tech_names = (
                detected_tech[:5]
                if isinstance(detected_tech[0], str)
                else [c.get('name', str(c)) for c in detected_tech[:5]]
            )
            wsi_competency_summary += f"\n**Técnicas:** {', '.join(tech_names)}"

            for tech in tech_names[:3]:
                wsi_question_suggestions.append({
                    "competency": tech,
                    "type": "technical",
                    "suggested_question": (
                        f"Descreva um projeto em que você utilizou {tech} para resolver um problema complexo."
                    ),
                    "framework": "CBI",
                })

        if detected_behav:
            behav_names = (
                detected_behav[:3]
                if isinstance(detected_behav[0], str)
                else [c.get('name', c.get('competency', str(c))) for c in detected_behav[:3]]
            )
            wsi_competency_summary += f"\n**Comportamentais:** {', '.join(behav_names)}"

            behavioral_questions_map = {
                "comunicação": "Conte sobre uma situação em que você precisou comunicar uma ideia complexa de forma simples.",
                "trabalho em equipe": "Descreva um momento em que você colaborou com uma equipe para atingir um objetivo desafiador.",
                "liderança": "Relate uma experiência em que você liderou uma equipe ou iniciativa.",
                "resolução de problemas": "Dê um exemplo de um problema difícil que você resolveu e como chegou à solução.",
                "proatividade": "Conte sobre uma situação em que você identificou uma oportunidade de melhoria e tomou iniciativa.",
            }

            for behav in behav_names[:2]:
                behav_lower = behav.lower()
                question = behavioral_questions_map.get(
                    behav_lower,
                    f"Descreva uma situação em que você demonstrou {behav} no ambiente de trabalho.",
                )
                wsi_question_suggestions.append({
                    "competency": behav,
                    "type": "behavioral",
                    "suggested_question": question,
                    "framework": "BigFive",
                })

        wsi_competency_summary += (
            f"\n\n🎯 **{len(wsi_question_suggestions)} perguntas sugeridas** baseadas nas competências detectadas."
        )

    suggestions_data['wsi_question_suggestions'] = wsi_question_suggestions
    suggestions_data['detected_competencies'] = {
        'technical': detected_tech,
        'behavioral': detected_behav,
    }

    lia_message = f"""Perfeito! Agora vou gerar as **Perguntas de Triagem WSI**. 📝
{wsi_competency_summary}

🎯 **Metodologia WSI aplicada:**
As perguntas seguem a metodologia WeDoTalent Skill Index com 7 blocos:
1. Autodeclaração de contexto
2. Micro-cases técnicos
3. Situacional comportamental
4. Fit cultural
5. Autodeclaração de habilidades
6. Perguntas técnicas específicas
7. Perguntas de elegibilidade

💡 *Recomendação: Selecione 4-6 perguntas para um formulário objetivo (3-5 min de resposta).*

---

🔄 Gerando perguntas personalizadas baseadas nas competências selecionadas...

✅ **Próximo passo:** Após confirmar as perguntas, vamos para a **revisão final** onde você verá tudo consolidado.

❓ *Quer saber mais sobre a metodologia WSI? Pergunte!*"""

    return lia_message, suggestions_data
