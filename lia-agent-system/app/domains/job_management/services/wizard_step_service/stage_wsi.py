import logging

logger = logging.getLogger(__name__)


async def handle_wsi_questions(
    job_draft: dict,
    suggestions_data: dict,
    db=None,
    company_id: str | None = None,
    screening_mode: str = "compact",
) -> tuple[str, dict]:
    """
    Handle stage 5: WSI question generation.

    C.1: Uses canonical WsiQuestionGenerator (F2+F3+F6) + SeniorityResolver.
    Fail-open: on any exception, falls back to legacy hardcoded approach.

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

    # --- C.1: Canonical WSI question generation ---
    wsi_question_suggestions = []
    canonical_used = False

    try:
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority_simple
        from app.domains.job_creation.services.wsi_question_generator import WSIQuestionGenerator
        from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
        from app.domains.job_creation.schemas import (
            EnrichedJobDescription,
            TechnicalSkill,
            BehavioralCompetency,
            ContextSignals,
        )

        # Step 1: Resolve seniority from job_draft signals
        explicit_seniority = job_draft.get("senioridade") or job_draft.get("seniority")
        job_title = job_draft.get("cargo") or job_draft.get("job_title") or ""
        job_description = job_draft.get("descricao") or job_draft.get("description") or ""

        resolved_seniority = resolve_seniority_simple(
            explicit_seniority=explicit_seniority,
            job_title=job_title,
            job_description=job_description,
        )
        logger.info("[stage_wsi:C1] Resolved seniority: %s", resolved_seniority)
        suggestions_data["resolved_seniority"] = resolved_seniority

        # Step 2: Build EnrichedJobDescription from job_draft fields.
        # Try JdEnrichmentService if we have a non-trivial JD; otherwise
        # construct a minimal EnrichedJobDescription from available signals.
        enriched = None

        if job_description and len(job_description) > 50:
            try:
                department = job_draft.get("gestorArea") or job_draft.get("department") or ""
                enrichment_svc = JdEnrichmentService()
                enriched, _qs, _warns = enrichment_svc.enrich(
                    jd_raw=job_description,
                    title=job_title,
                    seniority=resolved_seniority,
                    department=department,
                )
                logger.info("[stage_wsi:C1] JD enriched for WSI, quality=%.1f", _qs)
            except Exception as _enr_exc:
                logger.warning(
                    "[stage_wsi:C1] JdEnrichmentService failed, building minimal EnrichedJobDescription: %s",
                    _enr_exc,
                )
                enriched = None

        if enriched is None:
            # Build minimal EnrichedJobDescription from job_draft fields
            skills_obrigatorias = []
            for s in detected_tech[:15]:
                if isinstance(s, str):
                    skills_obrigatorias.append(TechnicalSkill(skill=s, contexto=""))
                elif isinstance(s, dict):
                    skills_obrigatorias.append(TechnicalSkill(
                        skill=s.get("name") or s.get("skill") or str(s),
                        contexto=s.get("context") or "",
                    ))

            competencias_comportamentais = []
            for b in detected_behav[:8]:
                if isinstance(b, str):
                    competencias_comportamentais.append(
                        BehavioralCompetency(competencia=b, contexto="", trait_big_five="conscientiousness")
                    )
                elif isinstance(b, dict):
                    competencias_comportamentais.append(
                        BehavioralCompetency(
                            competencia=b.get("name") or b.get("competency") or str(b),
                            contexto=b.get("context") or "",
                            trait_big_five=b.get("trait_big_five") or "conscientiousness",
                        )
                    )

            enriched = EnrichedJobDescription(
                titulo_padronizado=job_title or "Cargo",
                senioridade_confirmada=resolved_seniority,
                about_role=job_description[:300] if job_description else "",
                responsabilidades=[],
                skills_obrigatorias=skills_obrigatorias,
                skills_desejaveis=[],
                competencias_comportamentais=competencias_comportamentais,
                context_signals=ContextSignals(),
            )

        # Step 3: Generate WSI questions (F2+F3+F6)
        generator = WSIQuestionGenerator()

        # Determine distribution based on screening_mode
        if screening_mode == "full":
            distribution = {"technical": 5, "behavioral": 3}
        else:
            # compact (default)
            distribution = {"technical": 3, "behavioral": 2}

        # F2: Extract Big Five
        bigfive = generator.extract_bigfive(enriched)

        # Infer role archetype from job_title for F3 prior
        title_lower = job_title.lower()
        if any(t in title_lower for t in ["engineer", "developer", "dev ", "engenheiro", "desenvolvedor"]):
            role_archetype = "engineering"
        elif any(t in title_lower for t in ["product", "produto", "pm ", "gerente de produto"]):
            role_archetype = "product"
        elif any(t in title_lower for t in ["design", "ux", "ui"]):
            role_archetype = "design"
        elif any(t in title_lower for t in ["sales", "venda", "comercial"]):
            role_archetype = "sales"
        elif any(t in title_lower for t in ["ops", "operacao", "operações", "suporte"]):
            role_archetype = "operations"
        else:
            role_archetype = "default"

        # F3: Rank traits
        trait_rankings = generator.rank_traits(bigfive, resolved_seniority, role_archetype)

        # F6: Generate questions
        generated = generator.generate_questions(enriched, resolved_seniority, distribution, trait_rankings)

        # Convert to suggestions format expected by the wizard
        for q in generated:
            wsi_question_suggestions.append({
                "competency": q.skill or q.competency or "",
                "type": q.block,
                "suggested_question": q.question,
                "ideal_answer": q.ideal_answer,
                "scoring_rubric": q.scoring_rubric,
                "framework": q.framework,
                "trait_ocean": q.trait_ocean,
                "bloom_level": q.bloom_level,
                "dreyfus_level": q.dreyfus_level,
                "weight": q.weight,
            })

        # Store in job_draft
        job_draft["wsi_questions"] = wsi_question_suggestions
        suggestions_data["trait_rankings"] = trait_rankings
        canonical_used = True
        logger.info("[stage_wsi:C1] Canonical WSI generation OK: %d questions", len(wsi_question_suggestions))

    except Exception as _wsi_exc:
        logger.warning("[stage_wsi:C1] WsiQuestionGenerator failed, falling back to legacy: %s", _wsi_exc)
        canonical_used = False

    # --- Legacy fallback (kept intact) ---
    if not canonical_used:
        wsi_question_suggestions = []

        if detected_tech:
            tech_names = (
                detected_tech[:5]
                if isinstance(detected_tech[0], str)
                else [c.get('name', str(c)) for c in detected_tech[:5]]
            )
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

        job_draft["wsi_questions"] = wsi_question_suggestions

    # Build competency summary for LIA message
    wsi_competency_summary = ""
    if detected_tech or detected_behav:
        wsi_competency_summary = "\n\n📋 **Competências identificadas para triagem:**"

        if detected_tech:
            tech_names_display = (
                detected_tech[:5]
                if isinstance(detected_tech[0], str)
                else [c.get('name', str(c)) for c in detected_tech[:5]]
            )
            wsi_competency_summary += f"\n**Técnicas:** {', '.join(tech_names_display)}"

        if detected_behav:
            behav_names_display = (
                detected_behav[:3]
                if isinstance(detected_behav[0], str)
                else [c.get('name', c.get('competency', str(c))) for c in detected_behav[:3]]
            )
            wsi_competency_summary += f"\n**Comportamentais:** {', '.join(behav_names_display)}"

        wsi_competency_summary += (
            f"\n\n🎯 **{len(wsi_question_suggestions)} perguntas sugeridas** baseadas nas competências detectadas."
        )

    suggestions_data['wsi_question_suggestions'] = wsi_question_suggestions
    suggestions_data['detected_competencies'] = {
        'technical': detected_tech,
        'behavioral': detected_behav,
    }

    quality_source = "WSI F2+F3+F6" if canonical_used else "modelo legado"

    # C.3.2: Screening mode selection — ask recruiter if mode not yet chosen
    _screening_mode_in_draft = job_draft.get('screening_mode')
    if not _screening_mode_in_draft:
        suggestions_data.setdefault('stage_meta', {})['requires_screening_mode_selection'] = True

    lia_message = f"""Perfeito! Agora vou gerar as **Perguntas de Triagem WSI**. 📝
{wsi_competency_summary}

🎯 **Metodologia WSI aplicada** *(via {quality_source})*:
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

    # C.3.2: Append mode selection question only when recruiter hasn't chosen yet
    if not _screening_mode_in_draft:
        lia_message += "\n\nPrefere triagem **compacta** (5 perguntas rápidas) ou **completa** (12 perguntas detalhadas)?"

    return lia_message, suggestions_data
