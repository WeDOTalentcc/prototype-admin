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
    db=None,
    company_id: str | None = None,
) -> tuple[str, dict, dict]:
    """
    Handle stage 1: parse job description, extract criteria, build LIA message.

    Returns:
        (lia_message, detected_criteria, suggestions_data)
    """
    # F.1 — ATS job history context (fail-open: wrapped in try/except)
    try:
        from app.domains.job_management.services.ats_job_history_service import ats_job_history_service

        # Use a rough title hint from the raw input (first 60 chars or explicit title)
        _title_hint = (
            job_draft.get('job_title')
            or job_draft.get('cargo')
            or request.user_input[:60]
        )
        if _title_hint and company_id:
            _similar_jobs = await ats_job_history_service.get_similar_jobs(
                company_id=company_id,
                role=_title_hint,
                limit=10,
            )
            if _similar_jobs:
                # Aggregate common skills
                _skill_counts: dict[str, int] = {}
                _salary_mins = []
                _salary_maxs = []
                for _j in _similar_jobs:
                    if _j.skills:
                        for _s in _j.skills:
                            _sk = _s.get('name') if isinstance(_s, dict) else str(_s)
                            _skill_counts[_sk] = _skill_counts.get(_sk, 0) + 1
                    if _j.salary_min and _j.salary_max:
                        _salary_mins.append(_j.salary_min)
                        _salary_maxs.append(_j.salary_max)

                _top_skills = [
                    sk for sk, _ in sorted(_skill_counts.items(), key=lambda x: x[1], reverse=True)[:8]
                ]
                _typical_salary: dict = {}
                if _salary_mins and _salary_maxs:
                    import statistics as _stats
                    _typical_salary = {
                        "min": round(_stats.mean(_salary_mins)),
                        "max": round(_stats.mean(_salary_maxs)),
                        "currency": "BRL",
                        "sample_size": len(_salary_mins),
                    }

                suggestions_data["historical_context"] = {
                    "similar_count": len(_similar_jobs),
                    "common_skills": _top_skills,
                    "typical_salary": _typical_salary,
                }
                job_draft["_ats_historical_count"] = len(_similar_jobs)
                job_draft["_ats_common_skills"] = _top_skills

                logger.info(
                    "[F.1] ATS history: %d similar jobs found for role=%s",
                    len(_similar_jobs), _title_hint,
                )
    except Exception as _ats_exc:
        logger.warning("[F.1] ats_job_history_service failed (non-blocking): %s", _ats_exc)

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

            # F.4 apply_learning: adjust description suggestions based on company correction history
            _role_for_al = detected_criteria.get("cargo") or ""
            if db is not None and company_id and _role_for_al:
                try:
                    from app.domains.analytics.services.feedback_learning_service import feedback_learning_service
                    _al_seniority = detected_criteria.get("senioridadeIdiomas") or "Pleno"
                    _al_skills = (
                        (detected_criteria.get("competenciasTecnicas") or [])
                        + (detected_criteria.get("competenciasComportamentais") or [])
                    )
                    _al_adjusted = await feedback_learning_service.apply_learning(
                        db=db,
                        company_id=company_id,
                        suggestion={"skills": _al_skills, "role": _role_for_al, "seniority": _al_seniority},
                        role=_role_for_al,
                        seniority=_al_seniority,
                    )
                    if _al_adjusted:
                        suggestions_data["learning_adjustments"] = _al_adjusted
                except Exception as _al_exc:
                    logger.warning("apply_learning failed in stage_description: %s", _al_exc)

            lia_message = lia_intro + "\n".join(criteria_lines)

            # F.1 — Surface historical context hint in the LIA message
            _hist = suggestions_data.get("historical_context", {})
            if _hist.get("similar_count", 0) > 0:
                _hist_count = _hist["similar_count"]
                _hist_skills = _hist.get("common_skills", [])
                lia_message += (
                    f"\n\n📂 **Histórico ATS:** Notei que vocês já criaram **{_hist_count}** vaga(s) "
                    f"similar(es). Quer começar com base no padrão que costumam usar?"
                )
                if _hist_skills:
                    lia_message += f"\n   Skills recorrentes: {', '.join(_hist_skills[:5])}"

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

            # C.3.1: Seniority confirmation — ask recruiter to confirm inferred seniority
            _seniority_val = detected_criteria.get('senioridadeIdiomas') or job_draft.get('senioridade') or job_draft.get('seniority')
            if _seniority_val:
                _seniority_conf = field_origins.get('senioridadeIdiomas', {}).get('confidence', 0.5)
                _seniority_low_conf = _seniority_conf < 0.70
                lia_message += f"\n\nIdentifiquei a senioridade como **{_seniority_val}**. Confirma ou prefere ajustar?"
                if _seniority_low_conf:
                    suggestions_data.setdefault('stage_meta', {})['requires_seniority_confirmation'] = True

            suggestions_data['skill_suggestions'] = job_draft.get('skill_suggestions', {})
            suggestions_data['skill_quality_feedback'] = job_draft.get('skill_quality_feedback', {})
            suggestions_data['responsibilities_analysis'] = job_draft.get('responsibilities_analysis', {})
            suggestions_data['detected_responsibilities'] = job_draft.get('detected_responsibilities', [])
            suggestions_data['suggested_responsibilities'] = job_draft.get('suggested_responsibilities', [])
        else:
            lia_message = "Entendi a descrição! Por favor, me informe se deseja ajustar algo ou adicione mais detalhes."
            detected_criteria = {}
    except Exception:
        lia_message = "Consegui processar a descrição. Verifique os critérios detectados no painel lateral."
        detected_criteria = {}

    return lia_message, detected_criteria, suggestions_data
