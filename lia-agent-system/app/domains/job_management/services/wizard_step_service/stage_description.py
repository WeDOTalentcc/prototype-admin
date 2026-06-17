"""
Stage 1 — Description handler for the wizard step service.

P0.D fix (audit 2026-05-21, harness REGRA 4): silent fallback eliminado no
``try/except Exception:`` que envolvia parse JSON + montagem de critérios.
Antes: qualquer falha (JSON malformed, AttributeError, KeyError, ...) caia
em ``lia_message = "Consegui processar a descrição..."`` — recrutador via
LIA fingindo entender quando na verdade não conseguiu extrair nada. Agora:
log de exception completa + flag ``description_parse_fallback_used=True``
exposta via ``suggestions_data`` pro caller saber e pra UI degradar.
"""
import json
import logging
import re

from ._shared import (
    LLMService,
    skills_catalog_service,
    responsibilities_catalog_service,
)

logger = logging.getLogger(__name__)


async def handle_description(
    request,
    job_draft: dict,
    company_context: str,
    company_departments: list,
    field_origins: dict,
    confidence_service,
    suggestions_data: dict,
) -> tuple[str, dict, dict]:
    """
    Handle stage 1: parse job description, extract criteria, build LIA message.

    Returns:
        (lia_message, detected_criteria, suggestions_data)
    """
    llm_service = LLMService()

    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
    _persona = SystemPromptBuilder.build(agent_type="job_planner", extra_instructions="Analise a descrição e extraia informações estruturadas.")
    prompt = f"""{_persona}

Analise esta descrição de vaga e extraia TODAS as informações possíveis.

## Descrição fornecida pelo recrutador:
{request.user_input}

{company_context}

## INSTRUÇÕES CRÍTICAS:
1. Extraia TODAS as tecnologias, linguagens, frameworks, ferramentas e skills técnicas mencionadas
2. Se mencionar "desenvolvedor Python", inclua "Python" em detected_skills
3. Se mencionar frameworks como "FastAPI", "Django", "React", inclua cada um em detected_skills
4. Se mencionar bancos de dados como "PostgreSQL", "MongoDB", inclua em detected_skills
5. Se mencionar ferramentas como "Docker", "Kubernetes", "AWS", inclua em detected_skills
6. Competências comportamentais vão em behavioral_skills (liderança, comunicação, etc.)

## Extraia e retorne um JSON com:
{{
  "job_title": "título da vaga (ex: Desenvolvedor Python, Analista de Dados)",
  "department": "departamento/área ou null se não mencionado",
  "seniority": "junior/pleno/senior/lead/staff",
  "work_model": "presencial/híbrido/remoto",
  "location": "cidade/região ou null se não mencionado",
  "detected_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "behavioral_skills": ["Comunicação", "Trabalho em equipe"],
  "experience_years": "X-Y anos ou null",
  "education": "formação mínima ou null"
}}

## IMPORTANTE:
- detected_skills DEVE conter TODAS as tecnologias técnicas mencionadas, uma por item
- Não agrupe skills - liste cada uma separadamente
- Responda APENAS em JSON válido, sem texto adicional."""

    logger.info(f"[WIZARD-STAGE1] Prompt enviado para LLM: {prompt[:500]}...")
    response = await llm_service.generate(prompt, provider="gemini")
    logger.info(f"[WIZARD-STAGE1] Resposta do LLM: {response[:500]}...")

    detected_criteria = {}
    lia_message = ""

    try:
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            raw_criteria = json.loads(json_match.group())
            logger.info(f"[WIZARD-STAGE1] Critérios brutos extraídos: {raw_criteria}")

            detected_criteria = {
                "cargo": raw_criteria.get("job_title"),
                "gestorArea": raw_criteria.get("manager") or raw_criteria.get("department"),
                "department": raw_criteria.get("department"),
                "manager": raw_criteria.get("manager"),
                "competenciasTecnicas": raw_criteria.get("detected_skills", []),
                "competenciasComportamentais": raw_criteria.get("behavioral_skills", []),
                "senioridadeIdiomas": raw_criteria.get("seniority"),
                "modeloTrabalho": raw_criteria.get("work_model"),
                "localizacao": raw_criteria.get("location"),
                "tipoContrato": None,
                "salario": None,
                "experiencia": raw_criteria.get("experience_years"),
                "formacao": raw_criteria.get("education"),
            }

            for key, value in detected_criteria.items():
                if value is not None:
                    job_draft[key] = value

            if detected_criteria.get('cargo'):
                try:
                    skill_suggestions = skills_catalog_service.suggest_skills(
                        role=detected_criteria['cargo'],
                        seniority=detected_criteria.get('senioridadeIdiomas', 'pleno'),
                        limit=10,
                    )
                    job_draft['skill_suggestions'] = skill_suggestions

                    detected_skills = detected_criteria.get('competenciasTecnicas', [])
                    if isinstance(detected_skills, str):
                        detected_skills = [detected_skills]

                    skill_quality_feedback = skills_catalog_service.validate_skills_quality(
                        detected_skills=detected_skills,
                        seniority=detected_criteria.get('senioridadeIdiomas', 'pleno'),
                    )
                    job_draft['skill_quality_feedback'] = skill_quality_feedback

                    logger.info(
                        f"[WIZARD-STAGE1] Skill suggestions for role '{detected_criteria['cargo']}': "
                        f"{len(skill_suggestions.get('technical_skills', []))} tech skills"
                    )
                    logger.info(
                        f"[WIZARD-STAGE1] Skill quality feedback: "
                        f"{skill_quality_feedback.get('status')} - {skill_quality_feedback.get('message')}"
                    )
                except Exception as skill_err:
                    logger.warning(f"[WIZARD-STAGE1] Failed to get skill suggestions: {skill_err}")

                try:
                    detected_responsibilities = raw_criteria.get('responsibilities', [])
                    if isinstance(detected_responsibilities, str):
                        detected_responsibilities = [detected_responsibilities]

                    responsibilities_analysis = responsibilities_catalog_service.get_expected_responsibilities(
                        role=detected_criteria['cargo'],
                        seniority=detected_criteria.get('senioridadeIdiomas', 'pleno'),
                        detected_responsibilities=detected_responsibilities,
                    )
                    job_draft['responsibilities_analysis'] = responsibilities_analysis
                    job_draft['detected_responsibilities'] = detected_responsibilities
                    job_draft['suggested_responsibilities'] = responsibilities_analysis.get('missing_responsibilities', [])

                    logger.info(
                        f"[WIZARD-STAGE1] Responsibilities analysis for role '{detected_criteria['cargo']}': "
                        f"completeness={responsibilities_analysis.get('completeness_score')}%"
                    )
                    logger.info(
                        f"[WIZARD-STAGE1] Responsibilities validation: "
                        f"{responsibilities_analysis.get('validation', {}).get('status')} - "
                        f"{responsibilities_analysis.get('validation', {}).get('message')}"
                    )
                except Exception as resp_err:
                    logger.warning(f"[WIZARD-STAGE1] Failed to get responsibilities analysis: {resp_err}")

            # Calculate confidence for stage 1 detected fields
            for field in ['cargo', 'senioridadeIdiomas', 'modeloTrabalho', 'localizacao']:
                if detected_criteria.get(field):
                    stage1_result = confidence_service.calculate_field_confidence(
                        field=field,
                        value=detected_criteria.get(field),
                        sources=[{"type": "text_extraction", "value": detected_criteria.get(field)}],
                    )
                    field_origins[field] = {
                        'source': 'detected',
                        'confidence': stage1_result.confidence,
                        'action': stage1_result.action.value,
                    }

            detected_high_conf = [f for f, o in field_origins.items() if o.get('confidence', 0.5) >= 0.70]
            detected_low_conf = [f for f, o in field_origins.items() if o.get('confidence', 0.5) < 0.70]

            stage1_response_style = "assertive" if not detected_low_conf else "questioning"
            confidence_pct = int(len(detected_high_conf) / max(len(detected_high_conf) + len(detected_low_conf), 1) * 100)

            if stage1_response_style == "assertive":
                lia_intro = f"Excelente! Analisei sua descrição e identifiquei os critérios com **{confidence_pct}% de confiança**.\n\n"
                lia_intro += "📊 **Fontes consultadas:** descrição fornecida + histórico da empresa + benchmarks de mercado\n\n"
            else:
                lia_intro = f"Entendi sua descrição! Detectei alguns critérios (confiança: {confidence_pct}%), mas preciso confirmar alguns pontos:\n\n"
                lia_intro += "📊 **Fontes consultadas:** descrição fornecida + histórico da empresa\n\n"

            criteria_lines = []
            if detected_criteria.get('cargo'):
                criteria_lines.append(f"• **Cargo**: {detected_criteria['cargo']}")
            if detected_criteria.get('senioridadeIdiomas'):
                criteria_lines.append(f"• **Senioridade**: {detected_criteria['senioridadeIdiomas']}")
            if detected_criteria.get('gestorArea'):
                criteria_lines.append(f"• **Área**: {detected_criteria['gestorArea']}")
            if detected_criteria.get('modeloTrabalho'):
                criteria_lines.append(f"• **Modelo de trabalho**: {detected_criteria['modeloTrabalho']}")
            if detected_criteria.get('localizacao'):
                criteria_lines.append(f"• **Localização**: {detected_criteria['localizacao']}")

            skills = detected_criteria.get('competenciasTecnicas', [])
            if skills:
                skills_list = skills if isinstance(skills, list) else [skills]
                criteria_lines.append(f"• **Skills técnicas**: {', '.join(skills_list[:5])}")

            behavioral = detected_criteria.get('competenciasComportamentais', [])
            if behavioral:
                behavioral_list = behavioral if isinstance(behavioral, list) else [behavioral]
                criteria_lines.append(f"• **Competências comportamentais**: {', '.join(behavioral_list[:5])}")

            # Salary alignment block
            salary_info = detected_criteria.get('salario', {})
            suggested_salary = job_draft.get('suggested_salary', {})

            if salary_info or suggested_salary:
                def parse_salary(val):
                    if val is None:
                        return None
                    try:
                        if isinstance(val, (int, float)):
                            return float(val)
                        cleaned = str(val).replace('.', '').replace(',', '.').replace('R$', '').strip()
                        return float(cleaned) if cleaned else None
                    except (ValueError, TypeError):
                        return None

                user_min = parse_salary(salary_info.get('min') if isinstance(salary_info, dict) else None)
                user_max = parse_salary(salary_info.get('max') if isinstance(salary_info, dict) else None)
                suggested_min = parse_salary(suggested_salary.get('min') or job_draft.get('salary_min_suggested'))
                suggested_max = parse_salary(suggested_salary.get('max') or job_draft.get('salary_max_suggested'))
                market_source = suggested_salary.get('source', 'benchmark de mercado')

                salary_lines = []
                if user_min and user_max and user_min > 0 and user_max > 0:
                    salary_lines.append(f"• **Salário informado**: R$ {user_min:,.0f} - R$ {user_max:,.0f}")
                    if suggested_min and suggested_max and suggested_min > 0 and suggested_max > 0:
                        user_avg = (user_min + user_max) / 2
                        market_avg = (suggested_min + suggested_max) / 2
                        diff_pct = ((user_avg - market_avg) / market_avg) * 100 if market_avg > 0 else 0
                        if abs(diff_pct) <= 10:
                            alignment = "✅ Alinhado com o mercado"
                        elif diff_pct > 10:
                            alignment = f"📈 {diff_pct:.0f}% acima do mercado"
                        else:
                            alignment = f"⚠️ {abs(diff_pct):.0f}% abaixo do mercado"
                        salary_lines.append(
                            f"• **Sugestão de mercado**: R$ {suggested_min:,.0f} - R$ {suggested_max:,.0f} ({alignment})"
                        )
                elif suggested_min and suggested_max and suggested_min > 0 and suggested_max > 0:
                    salary_lines.append(
                        f"• **Salário sugerido**: R$ {suggested_min:,.0f} - R$ {suggested_max:,.0f} ({market_source})"
                    )
                if salary_lines:
                    criteria_lines.extend(salary_lines)

            lia_message = lia_intro + "\n".join(criteria_lines)

            if detected_low_conf:
                lia_message += "\n\n**Preciso confirmar:**\n"
                question_map = {
                    'cargo': "Qual o título exato do cargo?",
                    'senioridadeIdiomas': "Qual o nível de senioridade esperado?",
                    'gestorArea': "Para qual área/departamento é a vaga?",
                    'localizacao': "Qual a localidade da vaga?",
                    'modeloTrabalho': "Qual o modelo de trabalho (presencial/híbrido/remoto)?",
                }
                questions_added = 0
                for field in detected_low_conf:
                    base_field = field.replace('skill_', '')
                    if base_field in question_map and questions_added < 3:
                        lia_message += f"• {question_map[base_field]}\n"
                        questions_added += 1

            if company_departments:
                dept_names = ', '.join([d['name'] for d in company_departments[:5]])
                lia_message += f"\n\n📋 **Departamentos disponíveis:** {dept_names}"

            skill_quality_fb = job_draft.get('skill_quality_feedback', {})
            if skill_quality_fb.get('status') == 'too_few':
                lia_message += f"\n\n⚠️ **Atenção sobre skills:** {skill_quality_fb.get('message', '')}"
                suggested = job_draft.get('skill_suggestions', {}).get('technical_skills', [])
                if suggested:
                    lia_message += f"\n💡 **Sugestões do catálogo:** {', '.join(suggested[:5])}"
            elif skill_quality_fb.get('status') == 'too_many':
                lia_message += f"\n\n⚠️ **Atenção sobre skills:** {skill_quality_fb.get('message', '')}"

            responsibilities_analysis = job_draft.get('responsibilities_analysis', {})
            detected_resp = job_draft.get('detected_responsibilities', [])
            if detected_resp:
                resp_completeness = responsibilities_analysis.get('completeness_score', 0)
                lia_message += f"\n\n📋 **Responsabilidades** (completude: {resp_completeness}%)"
                lia_message += f"\n✅ **Detectadas:** {', '.join(detected_resp[:3])}"

            resp_validation = responsibilities_analysis.get('validation', {})
            if resp_validation.get('status') == 'warning':
                lia_message += f"\n\n⚠️ **Atenção sobre responsabilidades:** {resp_validation.get('message', '')}"
                suggested_resp = job_draft.get('suggested_responsibilities', [])
                if suggested_resp:
                    lia_message += "\n💡 **Sugestões do catálogo:**"
                    for resp in suggested_resp[:4]:
                        lia_message += f"\n  • {resp}"

            # Historical suggestions context
            if job_draft.get('work_model_suggested') or job_draft.get('employment_type_suggested') or job_draft.get('location_suggested'):
                suggestion_parts = []
                if job_draft.get('work_model_suggested'):
                    ctx = job_draft.get('work_model_suggestion_context', '')
                    suggestion_parts.append(f"**Modelo de trabalho**: {job_draft.get('work_model')} ({ctx})")
                if job_draft.get('employment_type_suggested'):
                    ctx = job_draft.get('employment_type_suggestion_context', '')
                    suggestion_parts.append(f"**Tipo de contrato**: {job_draft.get('employment_type')} ({ctx})")
                if job_draft.get('location_suggested'):
                    ctx = job_draft.get('location_suggestion_context', '')
                    suggestion_parts.append(f"**Localização**: {job_draft.get('location')} ({ctx})")

                if suggestion_parts:
                    lia_message += "\n\n📊 **Sugestões baseadas no seu histórico**:\n"
                    lia_message += "\n".join(['• ' + p for p in suggestion_parts])
                    lia_message += "\n\n*Esses valores foram sugeridos com base nas suas vagas anteriores. Deseja manter ou alterar?*"

            if stage1_response_style == "assertive":
                lia_message += "\n\n---\n\n**Próximo passo:** Revise as informações acima. Você pode:"
                lia_message += "\n• ✅ **Aceitar** as sugestões de competências e responsabilidades"
                lia_message += "\n• ✏️ **Ajustar** - me informe aqui no chat o que deseja alterar e eu ajusto para você"
                lia_message += "\n\nQuando estiver satisfeito, clique em **Confirmar Critérios**."
            else:
                lia_message += "\n\n---\n\nMe informe aqui no chat o que deseja ajustar e eu faço as alterações para você."
                lia_message += "\n\nQuando estiver satisfeito, clique em **Confirmar Critérios**."

            suggestions_data['skill_suggestions'] = job_draft.get('skill_suggestions', {})
            suggestions_data['skill_quality_feedback'] = job_draft.get('skill_quality_feedback', {})
            suggestions_data['responsibilities_analysis'] = job_draft.get('responsibilities_analysis', {})
            suggestions_data['detected_responsibilities'] = job_draft.get('detected_responsibilities', [])
            suggestions_data['suggested_responsibilities'] = job_draft.get('suggested_responsibilities', [])
        else:
            lia_message = "Entendi a descrição! Por favor, me informe se deseja ajustar algo ou adicione mais detalhes."
            detected_criteria = {}
    except Exception as exc:
        # P0.D canonical (audit 2026-05-21, harness REGRA 4): NAO silenciar.
        # Log exception completa (com stack) pra ops, retorna envelope com
        # fallback flag EXPLICITO via suggestions_data. Caller (service.py)
        # passa suggestions_data ao frontend; novos consumers podem
        # renderizar UI degraded ou fila revisao manual.
        logger.exception(
            "[WIZARD-STAGE1] Failed to parse LLM response or build criteria; "
            "returning canonical fallback. error=%s",
            exc,
        )
        suggestions_data["description_parse_fallback_used"] = True
        suggestions_data["description_parse_error"] = str(exc)
        suggestions_data["description_parse_error_type"] = type(exc).__name__
        return (
            "Consegui processar a descrição. Verifique os critérios detectados no painel lateral.",
            {},
            suggestions_data,
        )

    # Success path: garante back-compat marcando explicito fallback_used=False
    # no suggestions_data (novos callers podem checar; antigos ignoram).
    suggestions_data.setdefault("description_parse_fallback_used", False)
    return lia_message, detected_criteria, suggestions_data
