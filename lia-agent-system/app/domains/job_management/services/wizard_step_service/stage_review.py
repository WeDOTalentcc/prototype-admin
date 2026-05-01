"""
Stage 6 — Review & completeness handler for the wizard step service.
"""
import logging

from app.domains.job_management.services.jd_generator_service import jd_generator_service

logger = logging.getLogger(__name__)


async def handle_review(
    job_draft: dict,
    company_profile,
    company_benefits: list,
    field_origins: dict,
    suggestions_data: dict,
    completeness_service,
) -> tuple[str, dict]:
    """
    Handle stage 6: review + completeness check + JD generation.

    Returns:
        (lia_message, suggestions_data)
    """
    job_data_for_completeness = {
        "title": job_draft.get("cargo") or job_draft.get("job_title"),
        "seniority_level": job_draft.get("senioridadeIdiomas") or job_draft.get("seniority"),
        "department": job_draft.get("gestorArea") or job_draft.get("department"),
        "salary_range": job_draft.get("salario") or job_draft.get("salary_range"),
        "benefits": job_draft.get("beneficios") or job_draft.get("benefits"),
        "technical_requirements": (
            job_draft.get("competenciasTecnicas")
            or job_draft.get("detected_skills")
            or job_draft.get("tech_stack")
        ),
        "behavioral_competencies": (
            job_draft.get("competenciasComportamentais") or job_draft.get("behavioral_skills")
        ),
        "description": job_draft.get("descricao") or job_draft.get("description"),
        "requirements": job_draft.get("requisitos") or job_draft.get("requirements"),
        "work_model": job_draft.get("modeloTrabalho") or job_draft.get("work_model"),
        "location": job_draft.get("localizacao") or job_draft.get("location"),
        "employment_type": job_draft.get("tipoContrato") or job_draft.get("employment_type"),
        "languages": job_draft.get("idiomas") or job_draft.get("languages"),
        "manager": job_draft.get("gestor") or job_draft.get("manager"),
        "deadline": job_draft.get("prazo") or job_draft.get("deadline"),
    }

    completeness_result = completeness_service.check_completeness(job_data_for_completeness)

    suggestions_data['completeness'] = {
        'score': completeness_result.completeness_score,
        'can_publish': completeness_result.can_publish,
        'missing_critical': completeness_result.missing_critical,
        'missing_important': completeness_result.missing_important,
        'filled_fields': completeness_result.filled_fields,
        'toggled_off': completeness_result.toggled_off,
        'field_details': completeness_result.field_details,
    }

    generated_description = jd_generator_service.generate_description(
        job_data=job_draft,
        company_context={
            'about': company_profile.about if company_profile and hasattr(company_profile, 'about') else None,
            'benefits': company_benefits,
        },
    )
    job_draft['generated_description'] = generated_description
    suggestions_data['generated_description'] = generated_description

    completeness_warnings = []
    if completeness_result.missing_critical:
        critical_labels = [completeness_service.get_field_label(f) for f in completeness_result.missing_critical]
        completeness_warnings.append(f"⚠️ **Campos obrigatórios faltando:** {', '.join(critical_labels)}")

    if completeness_result.missing_important:
        important_labels = [
            completeness_service.get_field_label(f) for f in completeness_result.missing_important[:3]
        ]
        completeness_warnings.append(f"💡 **Recomendamos preencher:** {', '.join(important_labels)}")

    warnings_text = "\n".join(completeness_warnings) if completeness_warnings else ""

    if completeness_result.can_publish:
        status_message = f"✅ **Completude: {completeness_result.completeness_score}%** - Vaga pronta para publicação!"
    else:
        status_message = (
            f"⚠️ **Completude: {completeness_result.completeness_score}%** "
            f"- Preencha os campos obrigatórios para publicar."
        )

    job_title = job_data_for_completeness.get("title") or "Vaga"
    seniority = job_data_for_completeness.get("seniority_level") or ""
    department = job_data_for_completeness.get("department") or "Não informado"
    work_model = job_data_for_completeness.get("work_model") or "Não informado"
    location = job_data_for_completeness.get("location") or "Não informado"
    employment_type = job_data_for_completeness.get("employment_type") or "CLT"

    salary_info = job_data_for_completeness.get("salary_range")
    if isinstance(salary_info, dict):
        salary_text = f"R$ {salary_info.get('min', 0):,.0f} - R$ {salary_info.get('max', 0):,.0f}"
    elif salary_info:
        salary_text = str(salary_info)
    else:
        salary_text = "A combinar"

    tech_skills = job_data_for_completeness.get("technical_requirements") or []
    if isinstance(tech_skills, list):
        tech_skills_text = ", ".join([str(s) for s in tech_skills[:8]]) if tech_skills else "Não definidas"
    else:
        tech_skills_text = str(tech_skills) if tech_skills else "Não definidas"

    behavioral_skills = job_data_for_completeness.get("behavioral_competencies") or []
    if isinstance(behavioral_skills, list):
        if behavioral_skills and isinstance(behavioral_skills[0], dict):
            def get_competency_name(c):
                return c.get('competency') or c.get('name') or c.get('skill') or str(c)
            behavioral_text = ", ".join([get_competency_name(c) for c in behavioral_skills[:5]])
        else:
            behavioral_text = ", ".join([str(s) for s in behavioral_skills[:5]]) if behavioral_skills else "Não definidas"
    else:
        behavioral_text = str(behavioral_skills) if behavioral_skills else "Não definidas"

    benefits_list = job_data_for_completeness.get("benefits") or []
    if isinstance(benefits_list, list):
        benefits_text = ", ".join(benefits_list[:6]) if benefits_list else "Não definidos"
    else:
        benefits_text = str(benefits_list)

    languages = job_data_for_completeness.get("languages") or []
    if isinstance(languages, list):
        languages_text = ", ".join(languages) if languages else "Português"
    else:
        languages_text = str(languages) if languages else "Português"

    one_page_summary = f"""**{job_title}** {f'- {seniority}' if seniority else ''}

**Departamento:** {department}
**Modelo:** {work_model} | **Local:** {location}
**Contratação:** {employment_type}
**Faixa Salarial:** {salary_text}

**Competências Técnicas:** {tech_skills_text}
**Competências Comportamentais:** {behavioral_text}
**Benefícios:** {benefits_text}
**Idiomas:** {languages_text}"""

    jd_text = str(generated_description) if generated_description else "Descrição será gerada automaticamente."
    jd_preview = jd_text[:500] + "..." if len(jd_text) > 500 else jd_text

    # Build field origin summary
    field_labels_map = {
        'job_title': 'Cargo',
        'seniority': 'Senioridade',
        'department': 'Departamento',
        'location': 'Localização',
        'work_model': 'Modelo de Trabalho',
        'employment_type': 'Tipo de Contratação',
        'salary_range': 'Faixa Salarial',
        'salary_historical': 'Referência Salarial',
        'detected_skills': 'Competências Técnicas',
        'behavioral_skills': 'Competências Comportamentais',
    }

    field_summary_lines = []
    auto_filled_count = 0

    for field, origin in field_origins.items():
        if field.startswith('skill_'):
            continue
        source = origin.get('source', 'manual')
        confidence = origin.get('confidence', 0)

        if source != 'manual' and source:
            auto_filled_count += 1
            if source == 'company_default':
                emoji = '🏢'
                source_label = 'Padrão da empresa'
            elif source == 'historical_pattern':
                emoji = '📊'
                source_label = 'Histórico de vagas'
            elif source == 'learning_adjusted':
                emoji = '🧠'
                source_label = 'Aprendizado de correções'
            elif source == 'detected':
                emoji = '🤖'
                source_label = 'Detecção automática'
            else:
                emoji = '✨'
                source_label = source

            field_label = field_labels_map.get(field, field.replace('_', ' ').title())
            confidence_pct = int(confidence * 100) if isinstance(confidence, float) else confidence
            field_summary_lines.append(
                f"  • {field_label}: {emoji} {source_label} ({confidence_pct}% confiança)"
            )

    field_origin_summary = ""
    if field_summary_lines:
        field_origin_summary = (
            f"\n🔍 **Origem dos campos preenchidos automaticamente** ({auto_filled_count} campos):\n"
            + "\n".join(field_summary_lines)
            + "\n\n"
        )
        job_draft['field_origin_summary'] = field_origin_summary
        suggestions_data['field_origins'] = field_origins
        suggestions_data['auto_filled_count'] = auto_filled_count

    lia_message = f"""Excelente! Chegamos à **Revisão Final**! 🎉

{status_message}
{field_origin_summary}
---

📋 **RESUMO DA VAGA**

{one_page_summary}

---

📝 **DESCRIÇÃO GERADA (Preview)**

{jd_preview}

---

{warnings_text}

**✅ Checklist de Qualidade:**
✓ Informações básicas conferidas
✓ Competências e pesos verificados
✓ Perguntas de triagem WSI definidas
✓ Descrição gerada automaticamente

---

{"🚀 **Próximo passo:** Clique em **Publicar Vaga** para escolher as plataformas e ativar o recrutamento!" if completeness_result.can_publish else "⚠️ **Complete os campos obrigatórios** listados acima antes de publicar."}

💡 *Após publicar, vou começar a buscar candidatos compatíveis automaticamente!*"""

    return lia_message, suggestions_data
