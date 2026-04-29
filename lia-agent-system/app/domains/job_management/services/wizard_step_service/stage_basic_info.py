"""
Stage 2 — Basic Info handler for the wizard step service.
"""
import logging

from ._shared import analyze_competency_gaps

logger = logging.getLogger(__name__)

# C.5 — Template type keyword mapping (deterministic, no LLM)
_TEMPLATE_TYPE_KEYWORDS: dict[str, list[str]] = {
    "technical": [
        "desenvolvedor", "developer", "dev", "engenheiro", "engineer",
        "backend", "frontend", "fullstack", "full-stack", "full stack",
        "software", "dados", "data", "analytics", "bi", "machine learning",
        "ml", "ia", "ai", "devops", "sre", "platform", "infrastructure",
        "infra", "cloud", "qa", "quality", "tester", "product manager",
        "product owner", "pm", "po", "tech", "tecnologia", "sistemas",
        "arquiteto", "architect", "security", "segurança", "cybersecurity",
    ],
    "executive": [
        "diretor", "director", "cto", "ceo", "coo", "cfo", "cmo",
        "vp ", " vp", "vice-presidente", "vice presidente", "head of",
        "head de", "c-level", "clevel", "presidente", "president",
        "gerente geral", "general manager",
    ],
    "mass_hiring": [
        "volume", "massa", "mass", "operador", "operator", "atendente",
        "attendant", "motorista", "driver", "entregador", "delivery",
        "caixa", "cashier", "repositor", "promotor", "promotora",
        "vendedor", "sales rep", "agente", "agent",
    ],
    "intern": [
        "estágio", "estagio", "estagiário", "estagiaria", "intern",
        "trainee", "aprendiz", "apprentice", "jovem aprendiz",
    ],
    "operational": [
        "analista", "analyst", "coordenador", "coordinator", "supervisor",
        "assistente", "assistant", "auxiliar", "auxiliary", "técnico", "tecnico",
        "technician", "especialista", "specialist", "consultor", "consultant",
        "gerente", "manager",
    ],
}

# Human-readable labels and example pipelines per type
_TEMPLATE_DISPLAY: dict[str, dict] = {
    "technical": {
        "display_name": "Processo Técnico",
        "description": "Triagem → Entrevista Técnica → Entrevista Cultural → Proposta",
    },
    "executive": {
        "display_name": "Processo Executivo",
        "description": "Triagem → RH → Gestor → Diretoria → Proposta",
    },
    "operational": {
        "display_name": "Processo Operacional",
        "description": "Triagem → Entrevista RH → Proposta",
    },
    "mass_hiring": {
        "display_name": "Recrutamento em Massa",
        "description": "Triagem Automática → Proposta",
    },
    "intern": {
        "display_name": "Programa de Estágio",
        "description": "Triagem → Dinâmica de Grupo → Entrevista RH → Proposta",
    },
}


def _suggest_template_type(job_title: str, department: str) -> str:
    """
    Deterministically map job title + department → template type.
    Returns one of: technical, executive, operational, mass_hiring, intern.
    Fail-safe default: 'technical'.
    """
    combined = f"{job_title} {department}".lower()

    # Priority order: intern > executive > mass_hiring > technical > operational
    for ttype in ["intern", "executive", "mass_hiring", "technical", "operational"]:
        keywords = _TEMPLATE_TYPE_KEYWORDS.get(ttype, [])
        if any(kw in combined for kw in keywords):
            return ttype

    return "technical"


async def handle_basic_info(
    job_draft: dict,
    company_departments: list,
    suggestions_data: dict,
    db=None,
    company_id: str | None = None,
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

    # F.2 apply_learning: adjust skill suggestions based on company correction history
    if db is not None and company_id and job_title_for_gap:
        try:
            from app.domains.analytics.services.feedback_learning_service import feedback_learning_service
            _al_adjusted = await feedback_learning_service.apply_learning(
                db=db,
                company_id=company_id,
                suggestion={"role": job_title_for_gap, "seniority": seniority_for_gap,
                            "skills": detected_tech + detected_behav},
                role=job_title_for_gap,
                seniority=seniority_for_gap,
            )
            if _al_adjusted and _al_adjusted.get("skills"):
                suggestions_data["learning_adjustments"] = _al_adjusted
        except Exception as _al_exc:
            logger.warning("apply_learning failed in stage_basic_info: %s", _al_exc)

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

    # C.5 — Pipeline template suggestion (fail-open)
    template_message = ""
    try:
        department_hint = (
            job_draft.get('department')
            or job_draft.get('gestorArea')
            or job_draft.get('area')
            or ''
        )
        template_type = _suggest_template_type(job_title_for_gap, department_hint)
        tmpl_info = _TEMPLATE_DISPLAY.get(template_type, _TEMPLATE_DISPLAY["technical"])

        suggestions_data["pipeline_template"] = {
            "type": template_type,
            "display_name": tmpl_info["display_name"],
            "description": tmpl_info["description"],
        }
        job_draft["suggested_template_type"] = template_type

        template_message = (
            f"\n\n🔄 **Pipeline sugerido:** Para vagas de *{job_title_for_gap or 'este tipo'}*, "
            f"costumo usar o pipeline **{tmpl_info['display_name']}** "
            f"(ex: {tmpl_info['description']}). "
            f"Quer usar esse fluxo?"
        )
        logger.info(
            "[C.5] Template suggestion: type=%s for title=%s dept=%s",
            template_type, job_title_for_gap, department_hint,
        )
    except Exception as _tmpl_exc:
        logger.warning("C.5 template suggestion failed in stage_basic_info: %s", _tmpl_exc)

    lia_message = f"""Ótimo progresso! Vamos às **Informações Básicas**. 📋
{dept_list}

**O que precisamos confirmar:**
• Quantas posições você precisa preencher?
• Qual o departamento responsável?
• Quem será o gestor da vaga?
• Prazo para preenchimento
• Tipo de contratação (CLT, PJ, Temporário)

💡 *Se algum campo já estiver preenchido no painel, é só confirmar ou ajustar.*
{competency_gap_message}{template_message}

---

✅ **Próximo passo:** Após confirmar, vamos para as **competências** onde sugerirei skills baseadas no cargo.

*Campos com ícone 📊 foram sugeridos com base no seu histórico.*"""

    suggestions_data["departments"] = [d["name"] for d in company_departments] if company_departments else []
    suggestions_data["contract_types"] = ["CLT", "PJ", "Temporário", "Estágio", "Terceirizado"]

    if job_draft.get('competency_gap_analysis'):
        suggestions_data['competency_gap_analysis'] = job_draft['competency_gap_analysis']

    return lia_message, suggestions_data
