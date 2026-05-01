"""
Stage 2 — Basic Info handler for the wizard step service.
"""
import logging

from ._shared import analyze_competency_gaps

logger = logging.getLogger(__name__)


async def handle_basic_info(
    job_draft: dict,
    company_departments: list,
    suggestions_data: dict,
) -> tuple[str, dict]:
    """
    Handle stage 2: basic job info confirmation + competency gap analysis.

    Returns:
        (lia_message, suggestions_data)
    """
    dept_list = ""
    if company_departments:
        dept_list = f"\n\n📋 **Departamentos cadastrados:** {', '.join([d['name'] for d in company_departments[:8]])}"

    job_title_for_gap = job_draft.get('cargo') or job_draft.get('job_title') or ''
    seniority_for_gap = job_draft.get('senioridade') or job_draft.get('seniority') or 'Pleno'
    detected_tech = job_draft.get('competenciasTecnicas') or job_draft.get('detected_skills') or []
    detected_behav = job_draft.get('competenciasComportamentais') or job_draft.get('behavioral_skills') or []

    if isinstance(detected_tech, str):
        detected_tech = [detected_tech]
    if isinstance(detected_behav, str):
        detected_behav = [detected_behav]

    competency_gap_message = ""
    try:
        if job_title_for_gap:
            gap_analysis = await analyze_competency_gaps(
                job_title=job_title_for_gap,
                seniority=seniority_for_gap,
                detected_technical=detected_tech,
                detected_behavioral=detected_behav,
            )

            job_draft['competency_gap_analysis'] = gap_analysis
            suggestions_data['competency_gap_analysis'] = gap_analysis

            if gap_analysis.get('missing_technical') or gap_analysis.get('missing_behavioral'):
                gap_feedback_parts = []
                gap_feedback_parts.append(
                    f"\n\n📊 **Análise de Competências** (completude: {gap_analysis['completeness_score']}%)"
                )
                gap_feedback_parts.append(gap_analysis['analysis_summary'])

                if gap_analysis.get('missing_technical'):
                    tech_names = [s.get('name', str(s)) for s in gap_analysis['missing_technical'][:5]]
                    gap_feedback_parts.append(
                        f"\n🔧 **Competências técnicas sugeridas** (baseado no cargo {job_title_for_gap}):"
                    )
                    gap_feedback_parts.extend([f"  • {name}" for name in tech_names])

                if gap_analysis.get('missing_behavioral'):
                    behav_names = [s.get('name', str(s)) for s in gap_analysis['missing_behavioral'][:3]]
                    gap_feedback_parts.append("\n🎯 **Competências comportamentais sugeridas**:")
                    gap_feedback_parts.extend([f"  • {name}" for name in behav_names])

                gap_feedback_parts.append("\n*Gostaria de adicionar alguma dessas competências à vaga?*")
                competency_gap_message = "\n".join(gap_feedback_parts)
                job_draft['competency_gap_feedback'] = competency_gap_message
    except Exception as e:
        logger.warning(f"Competency gap analysis failed: {e}")

    lia_message = f"""Ótimo progresso! Vamos às **Informações Básicas**. 📋
{dept_list}

**O que precisamos confirmar:**
• Quantas posições você precisa preencher?
• Qual o departamento responsável?
• Quem será o gestor da vaga?
• Prazo para preenchimento
• Tipo de contratação (CLT, PJ, Temporário)

💡 *Se algum campo já estiver preenchido no painel, é só confirmar ou ajustar.*
{competency_gap_message}

---

✅ **Próximo passo:** Após confirmar, vamos para as **competências** onde sugerirei skills baseadas no cargo.

*Campos com ícone 📊 foram sugeridos com base no seu histórico.*"""

    suggestions_data["departments"] = [d["name"] for d in company_departments] if company_departments else []
    suggestions_data["contract_types"] = ["CLT", "PJ", "Temporário", "Estágio", "Terceirizado"]

    if job_draft.get('competency_gap_analysis'):
        suggestions_data['competency_gap_analysis'] = job_draft['competency_gap_analysis']

    return lia_message, suggestions_data
