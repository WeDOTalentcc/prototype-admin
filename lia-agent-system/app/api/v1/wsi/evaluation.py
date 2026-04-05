"""
WSI package — evaluation routes.

Routes:
  POST /jd-evaluate
  POST /analyze-response
  POST /complete-screening
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
import json
import logging

from app.core.database import get_db

from ._shared import (
    JDEvaluateRequest, JDEvaluateResponse,
    AnalyzeResponseRequest, AnalyzeResponseOutput,
    CompleteScreeningRequest, CompleteScreeningResponse,
    BigFiveIndicators, ArchetypeIndicator,
    BLOOM_LEVELS, DREYFUS_LEVELS, WSI_CLASSIFICATION_MAP,
    classify_wsi_score,
    _JD_SENIORITY_KEYWORDS, _BIAS_TERMS, _JD_BANDS, _jd_get_band,
    get_anthropic_client, _run_anthropic_sync, parse_json_response,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/jd-evaluate")
async def evaluate_jd(request: JDEvaluateRequest):
    """Evaluate job description quality using 9 dimensions (spec F1.B).
    Hard block if score < 30 (band=Crítico). 5 quality bands."""
    resp_count   = len(request.responsibilities or [])
    tech_count   = len(request.technical_skills or [])
    behav_count  = len(request.behavioral_competencies or [])
    has_seniority = bool(request.seniority)
    desc = (request.description or "").lower()
    title = (request.job_title or "").lower()
    dept = (request.department or "")

    score = 0
    indicators = []

    title_has_seniority = any(
        kw in title
        for keywords in _JD_SENIORITY_KEYWORDS.values()
        for kw in keywords
    )
    pts_1 = 10 if (title_has_seniority or has_seniority) else 0
    score += pts_1
    indicators.append({
        "dimension": "D1",
        "label": "Clareza do título",
        "weight": 10,
        "earned": pts_1,
        "status": "sufficient" if pts_1 == 10 else "insufficient",
        "detail": f"{'Indicador de senioridade detectado' if pts_1 else 'Título sem indicador de senioridade'}",
    })

    if resp_count >= 5:
        pts_2 = 15
        st_2 = "sufficient"
    elif resp_count >= 2:
        pts_2 = 7
        st_2 = "partial"
    else:
        pts_2 = 0
        st_2 = "insufficient"
    score += pts_2
    indicators.append({
        "dimension": "D2",
        "label": "Responsabilidades",
        "weight": 15,
        "earned": pts_2,
        "count": resp_count,
        "minimum": 5,
        "status": st_2,
        "detail": f"{resp_count} responsabilidade(s) — mínimo ideal: 5",
    })

    # D3 — Spec Task #43: mínimo ideal = 9 skills técnicas para cobertura Full WSI
    _D3_MIN_IDEAL = 9
    if tech_count >= _D3_MIN_IDEAL:
        pts_3 = 15
        st_3 = "sufficient"
    elif tech_count >= 3:
        pts_3 = 7
        st_3 = "partial"
    else:
        pts_3 = 0
        st_3 = "insufficient"
    score += pts_3
    indicators.append({
        "dimension": "D3",
        "label": "Skills técnicas",
        "weight": 15,
        "earned": pts_3,
        "count": tech_count,
        "minimum": _D3_MIN_IDEAL,
        "status": st_3,
        "detail": f"{tech_count} skill(s) técnica(s) — mínimo ideal: {_D3_MIN_IDEAL}",
    })

    # D4 — Spec Task #43: mínimo ideal = 5 competências comportamentais (1 por trait Big Five)
    _D4_MIN_IDEAL = 5
    if behav_count >= _D4_MIN_IDEAL:
        pts_4 = 10
        st_4 = "sufficient"
    elif behav_count >= 2:
        pts_4 = 5
        st_4 = "partial"
    else:
        pts_4 = 0
        st_4 = "insufficient"
    score += pts_4
    indicators.append({
        "dimension": "D4",
        "label": "Comp. comportamentais",
        "weight": 10,
        "earned": pts_4,
        "count": behav_count,
        "minimum": _D4_MIN_IDEAL,
        "status": st_4,
        "detail": f"{behav_count} comportamental(is) — mínimo ideal: {_D4_MIN_IDEAL}",
    })

    if has_seniority and resp_count >= 3:
        pts_5 = 15
        st_5 = "sufficient"
    elif has_seniority or resp_count >= 2:
        pts_5 = 7
        st_5 = "partial"
    else:
        pts_5 = 0
        st_5 = "insufficient"
    score += pts_5
    indicators.append({
        "dimension": "D5",
        "label": "Consistência senioridade",
        "weight": 15,
        "earned": pts_5,
        "status": st_5,
        "detail": "Senioridade declarada com responsabilidades compatíveis" if pts_5 == 15 else "Senioridade ou responsabilidades insuficientes para calibração",
    })

    desc_words = len(desc.split()) if desc else 0
    has_contradiction = (
        ("autonomia" in desc and "aprovação" in desc) or
        ("independente" in desc and "acompanhamento diário" in desc)
    )
    pts_6 = 0 if has_contradiction else (10 if desc_words > 80 else 5)
    score += pts_6
    indicators.append({
        "dimension": "D6",
        "label": "Ausência de inconsistências",
        "weight": 10,
        "earned": pts_6,
        "status": "insufficient" if has_contradiction else ("sufficient" if pts_6 == 10 else "partial"),
        "detail": "Contradição detectada (autonomia vs. aprovação)" if has_contradiction else "Sem inconsistências detectadas",
    })

    has_context = bool(dept) or any(kw in desc for kw in ["empresa", "equipe", "time", "setor", "segmento", "startup", "corporati"])
    pts_7 = 10 if has_context else 0
    score += pts_7
    indicators.append({
        "dimension": "D7",
        "label": "Contexto organizacional",
        "weight": 10,
        "earned": pts_7,
        "status": "sufficient" if pts_7 == 10 else "insufficient",
        "detail": "Contexto de empresa/time/setor presente" if pts_7 else "Sem contexto organizacional (empresa, time, setor)",
    })

    found_bias = [t for t in _BIAS_TERMS if t in desc or t in title]
    pts_8 = 0 if found_bias else 10
    score += pts_8
    indicators.append({
        "dimension": "D8",
        "label": "Linguagem inclusiva",
        "weight": 10,
        "earned": pts_8,
        "status": "insufficient" if found_bias else "sufficient",
        "detail": f"Termo(s) de viés encontrado(s): {', '.join(found_bias[:3])}" if found_bias else "Linguagem neutra e inclusiva",
    })

    all_text = " ".join(filter(None, [
        request.description,
        " ".join(request.responsibilities or []),
        " ".join(request.technical_skills or []),
        " ".join(request.behavioral_competencies or []),
    ]))
    total_words = len(all_text.split())
    pts_9 = 5 if total_words >= 150 else 0
    score += pts_9
    indicators.append({
        "dimension": "D9",
        "label": "Densidade total",
        "weight": 5,
        "earned": pts_9,
        "word_count": total_words,
        "minimum": 150,
        "status": "sufficient" if pts_9 == 5 else "insufficient",
        "detail": f"{total_words} palavras — mínimo ideal: 150",
    })

    band_key, band_label = _jd_get_band(score)

    if score >= 85:
        suggestion = f"JD excelente para {request.job_title}. Perguntas WSI serão altamente calibradas com {tech_count} competências técnicas e {behav_count} comportamentais."
    elif score >= 70:
        suggestion = f"JD bem estruturado. Perguntas WSI geradas com boa qualidade. Recomenda-se enriquecer contexto organizacional para maximizar precisão."
    elif score >= 50:
        missing = []
        if resp_count < 5: missing.append(f"responsabilidades (tem {resp_count}, ideal ≥5)")
        if tech_count < 3: missing.append(f"skills técnicas (tem {tech_count}, ideal ≥3)")
        if behav_count < 2: missing.append(f"comportamentais (tem {behav_count}, ideal ≥2)")
        suggestion = f"JD adequado mas com lacunas. Melhore: {'; '.join(missing) or 'contexto e densidade'}."
    elif score >= 30:
        suggestion = "JD insuficiente para gerar perguntas de alta qualidade. Adicione responsabilidades detalhadas, skills técnicas específicas e senioridade."
    else:
        suggestion = "JD crítico — perguntas WSI bloqueadas. Adicione no mínimo: título com senioridade, 2+ responsabilidades, 1+ skill técnica e senioridade definida."

    if score < 30:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "qualidade_insuficiente",
                "message": suggestion,
                "score": score,
                "max_score": 100,
                "band": band_key,
                "band_label": band_label,
                "indicators": [i.dict() if hasattr(i, 'dict') else i for i in indicators],
                "can_generate": False,
            }
        )

    return JDEvaluateResponse(
        success=True,
        score=score,
        max_score=100,
        band=band_key,
        band_label=band_label,
        indicators=indicators,
        lia_suggestion=suggestion,
        can_generate=True,
        details={
            "responsibilities_count": resp_count,
            "technical_skills_count": tech_count,
            "behavioral_competencies_count": behav_count,
            "seniority_defined": has_seniority,
            "total_word_count": total_words,
            "has_context": has_context,
            "bias_terms_found": found_bias,
            "has_inconsistency": has_contradiction,
        }
    )


@router.post("/analyze-response", response_model=AnalyzeResponseOutput)
async def analyze_response(
    request: AnalyzeResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a single candidate response using Claude AI.

    Evaluates:
    - Bloom's Taxonomy level demonstrated (cognitive level)
    - Dreyfus Model proficiency level
    - Big Five personality indicators
    """
    client = await get_anthropic_client()

    question_text = ""
    try:
        result = await db.execute(text("""
            SELECT question_text, competency FROM wsi_questions WHERE id = :question_id
        """), {"question_id": request.question_id})
        row = result.fetchone()
        if row:
            question_text = row[0]
    except Exception:
        pass

    if client:
        prompt = f"""Analyze this candidate response using WSI methodology (Bloom + Dreyfus + Big Five).

QUESTION: {question_text or "Not available"}

CANDIDATE RESPONSE:
{request.response_text}

Analyze and provide:
1. **Bloom Level (1-6)**: What cognitive level does the response demonstrate?
   1=Remember (recalls facts), 2=Understand (explains), 3=Apply (uses in practice),
   4=Analyze (connects ideas), 5=Evaluate (justifies decisions), 6=Create (produces new ideas)

2. **Dreyfus Level (1-5)**: What proficiency level?
   1=Novice, 2=Advanced Beginner, 3=Competent, 4=Proficient, 5=Expert

3. **Big Five Indicators (0-100 each)**:
   - Openness: Creativity, curiosity for new ideas
   - Conscientiousness: Organization, discipline, goal focus
   - Extraversion: Sociability, assertiveness, energy
   - Agreeableness: Cooperation, empathy, teamwork
   - Neuroticism: Emotional sensitivity (low = stable/calm)

4. **Score (0-5)**: Overall quality of response
5. **Feedback**: Brief constructive feedback in Portuguese
6. **Evidences**: Key points that support the evaluation
7. **Red Flags**: Any concerns or inconsistencies

Return ONLY valid JSON:
{{
  "bloom_score": 4,
  "dreyfus_level": 3,
  "big_five": {{
    "openness": 65,
    "conscientiousness": 70,
    "extraversion": 55,
    "agreeableness": 60,
    "neuroticism": 35
  }},
  "score": 3.5,
  "feedback": "Resposta demonstra boa capacidade analítica...",
  "evidences": ["Exemplo concreto citado", "Métricas mencionadas"],
  "red_flags": []
}}"""

        response = await _run_anthropic_sync(
            client,
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0
        )
        try:
            if response is None:
                raise ValueError("Anthropic call timed out or failed")
            data = parse_json_response(response.content[0].text, {})
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            data = {}
    else:
        data = {}

    bloom_score = data.get("bloom_score", 3)
    dreyfus_level = data.get("dreyfus_level", 3)
    big_five = data.get("big_five", {
        "openness": 50, "conscientiousness": 50, "extraversion": 50,
        "agreeableness": 50, "neuroticism": 50
    })

    analysis_id = str(uuid.uuid4())
    try:
        await db.execute(text("""
            INSERT INTO wsi_response_analyses (
                id, session_id, question_id, candidate_id, job_vacancy_id,
                competency, response_text, bloom_level, dreyfus_level,
                evidences, red_flags, final_score, justification
            )
            VALUES (:id, :session_id, :question_id, :candidate_id, :job_vacancy_id,
                    :competency, :response_text, :bloom_level, :dreyfus_level,
                    :evidences::jsonb, :red_flags::jsonb, :final_score, :justification)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": analysis_id,
            "session_id": request.session_id,
            "question_id": request.question_id,
            "candidate_id": request.candidate_id,
            "job_vacancy_id": "",
            "competency": "General",
            "response_text": request.response_text,
            "bloom_level": bloom_score,
            "dreyfus_level": dreyfus_level,
            "evidences": json.dumps(data.get("evidences", [])),
            "red_flags": json.dumps(data.get("red_flags", [])),
            "final_score": data.get("score", 3.0),
            "justification": data.get("feedback", "")
        })
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save analysis: {e}")

    # Compute star_completeness: proportion of STAR elements present in response
    _star_keywords = [
        ["situação", "situacao", "situation", "contexto", "context"],
        ["tarefa", "task", "objetivo", "objetivo", "responsabilidade"],
        ["ação", "acao", "action", "fiz", "implementei", "desenvolvi", "criei"],
        ["resultado", "result", "outcome", "conquista", "entregamos", "consegui"],
    ]
    _resp_lower = request.response_text.lower()
    _found = sum(1 for group in _star_keywords if any(kw in _resp_lower for kw in group))
    star_completeness = round(_found / 4.0, 2)

    _score = data.get("score", 3.0)

    return AnalyzeResponseOutput(
        question_id=request.question_id,
        bloom_score=bloom_score,
        bloom_level_name=BLOOM_LEVELS.get(bloom_score, BLOOM_LEVELS[3])["name"],
        dreyfus_level=dreyfus_level,
        dreyfus_level_name=DREYFUS_LEVELS.get(dreyfus_level, DREYFUS_LEVELS[3])["name"],
        big_five_indicators=BigFiveIndicators(
            openness=big_five.get("openness", 50),
            conscientiousness=big_five.get("conscientiousness", 50),
            extraversion=big_five.get("extraversion", 50),
            agreeableness=big_five.get("agreeableness", 50),
            neuroticism=big_five.get("neuroticism", 50)
        ),
        score=_score,
        score_max=5.0,
        score_normalized=round(_score / 5.0 * 10.0, 1),
        star_completeness=star_completeness,
        feedback=data.get("feedback", "Análise em processamento"),
        evidences=data.get("evidences", []),
        red_flags=data.get("red_flags", [])
    )


@router.post("/complete-screening", response_model=CompleteScreeningResponse)
async def complete_screening(
    request: CompleteScreeningRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete WSI screening by analyzing all responses and generating final report.

    Returns comprehensive assessment including:
    - Overall score (0-5)
    - Cognitive level (Bloom average)
    - Proficiency level (Dreyfus average)
    - Big Five personality profile
    - Archetype indicators
    - Summary and recommendations
    """
    response_analyses = []

    for resp in request.responses:
        analysis = await analyze_response(
            AnalyzeResponseRequest(
                session_id=request.session_id,
                question_id=resp.question_id,
                response_text=resp.response_text,
                candidate_id=request.candidate_id
            ),
            db
        )
        response_analyses.append(analysis)

    avg_bloom = sum(a.bloom_score for a in response_analyses) / len(response_analyses) if response_analyses else 3
    avg_dreyfus = sum(a.dreyfus_level for a in response_analyses) / len(response_analyses) if response_analyses else 3
    avg_score = sum(a.score for a in response_analyses) / len(response_analyses) if response_analyses else 3.0

    avg_big_five = BigFiveIndicators(
        openness=int(sum(a.big_five_indicators.openness for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        conscientiousness=int(sum(a.big_five_indicators.conscientiousness for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        extraversion=int(sum(a.big_five_indicators.extraversion for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        agreeableness=int(sum(a.big_five_indicators.agreeableness for a in response_analyses) / len(response_analyses)) if response_analyses else 50,
        neuroticism=int(sum(a.big_five_indicators.neuroticism for a in response_analyses) / len(response_analyses)) if response_analyses else 50
    )

    classification = classify_wsi_score(avg_score)

    archetypes = []
    o, c, e, a, n = (
        avg_big_five.openness, avg_big_five.conscientiousness,
        avg_big_five.extraversion, avg_big_five.agreeableness, 100 - avg_big_five.neuroticism
    )

    if o >= 70 and e >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Catalisador Visionário",
            match_score=min(100, (o + e) // 2),
            description="Inovador, inspirador, busca mudanças"
        ))
    if c >= 70 and a >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Executor Confiável",
            match_score=min(100, (c + a) // 2),
            description="Metódico, colaborativo, entrega consistente"
        ))
    if a >= 70 and e >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Guardião de Clientes",
            match_score=min(100, (a + e) // 2),
            description="Empático, comunicativo, orientado ao cliente"
        ))
    if o >= 70 and c >= 60:
        archetypes.append(ArchetypeIndicator(
            archetype="Estrategista Analítico",
            match_score=min(100, (o + c) // 2),
            description="Pensador profundo, orientado a dados"
        ))
    if not archetypes:
        archetypes.append(ArchetypeIndicator(
            archetype="Perfil Equilibrado",
            match_score=60,
            description="Perfil versátil com características balanceadas"
        ))

    bloom_level_name = BLOOM_LEVELS.get(round(avg_bloom), BLOOM_LEVELS[3])
    dreyfus_level_name = DREYFUS_LEVELS.get(round(avg_dreyfus), DREYFUS_LEVELS[3])

    recommendations = []
    if avg_bloom < 4:
        recommendations.append("Desenvolver habilidades de análise crítica e avaliação")
    if avg_dreyfus < 3:
        recommendations.append("Ganhar mais experiência prática em projetos reais")
    if avg_big_five.conscientiousness < 50:
        recommendations.append("Trabalhar organização e planejamento")
    if avg_big_five.extraversion < 40:
        recommendations.append("Desenvolver habilidades de comunicação interpessoal")
    if not recommendations:
        recommendations.append("Candidato demonstra perfil sólido para a posição")

    class_label = WSI_CLASSIFICATION_MAP.get(classification, {}).get("label", classification)
    summary = (
        f"Candidato avaliado como {class_label} (Score: {avg_score:.1f}/5.0). "
        f"Demonstra nível cognitivo {bloom_level_name['name_pt']} (Bloom {round(avg_bloom)}) "
        f"e proficiência {dreyfus_level_name['name_pt']} (Dreyfus {round(avg_dreyfus)}). "
        f"Arquétipo predominante: {archetypes[0].archetype}."
    )

    result_id = str(uuid.uuid4())
    try:
        await db.execute(text("""
            INSERT INTO wsi_results (
                id, session_id, candidate_id, job_vacancy_id,
                technical_wsi, behavioral_wsi, overall_wsi, classification
            )
            VALUES (:id, :session_id, :candidate_id, :job_vacancy_id,
                    :technical_wsi, :behavioral_wsi, :overall_wsi, :classification)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": result_id,
            "session_id": request.session_id,
            "candidate_id": request.candidate_id,
            "job_vacancy_id": request.job_vacancy_id or "",
            "technical_wsi": avg_score,
            "behavioral_wsi": avg_score,
            "overall_wsi": avg_score,
            "classification": classification
        })

        await db.execute(text("""
            UPDATE wsi_sessions SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = :session_id
        """), {"session_id": request.session_id})

        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to save result: {e}")

    # Create WSI Opinion after successful screening completion
    try:
        company_id = None
        if request.job_vacancy_id:
            vac_result = await db.execute(text(
                "SELECT company_id FROM job_vacancies WHERE id = :vid LIMIT 1"
            ), {"vid": request.job_vacancy_id})
            vac_row = vac_result.fetchone()
            if vac_row and vac_row.company_id:
                company_id = str(vac_row.company_id)

        # Archive previous WSI opinions for same candidate/vacancy
        if request.job_vacancy_id:
            await db.execute(text("""
                UPDATE lia_opinions
                SET is_current = false
                WHERE candidate_id = :candidate_id
                AND job_vacancy_id = :job_vacancy_id
                AND opinion_type = 'wsi'
                AND company_id = :company_id
                AND is_current = true
            """), {
                "candidate_id": request.candidate_id,
                "job_vacancy_id": request.job_vacancy_id,
                "company_id": company_id
            })

        # Get next version number
        version_result = await db.execute(text("""
            SELECT COALESCE(MAX(version), 0) + 1 as next_version
            FROM lia_opinions
            WHERE candidate_id = :candidate_id
            AND (job_vacancy_id = :job_vacancy_id OR (:job_vacancy_id IS NULL AND job_vacancy_id IS NULL))
            AND opinion_type = 'wsi'
            AND company_id = :company_id
        """), {
            "candidate_id": request.candidate_id,
            "job_vacancy_id": request.job_vacancy_id,
            "company_id": company_id
        })
        new_version = version_result.scalar() or 1

        # Determine recommendation per canonical WSI_CUTOFFS (Spec §10.3)
        # approved_auto ≥ 3.75/5 (= 7.5/10), review_min ≥ 3.0/5 (= 6.0/10)
        if avg_score >= 3.75:
            recommendation = "approved"
        elif avg_score >= 3.0:
            recommendation = "pending_review"
        else:
            recommendation = "not_approved"

        # Categorize recommendations into strengths, concerns, and gaps
        strengths = [r for r in recommendations if "sólido" in r.lower() or "demonstra" in r.lower()]
        concerns = [r for r in recommendations if "desenvolver" in r.lower() or "trabalhar" in r.lower()]
        gaps = [r for r in recommendations if "ganhar" in r.lower() or "experiência" in r.lower()]

        # Insert new WSI opinion
        opinion_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO lia_opinions (
                id, candidate_id, job_vacancy_id, company_id, opinion_type, source,
                score, wsi_score, archetype, recommendation, summary, score_breakdown,
                strengths, concerns, gaps, matched_skills, missing_skills,
                next_steps, is_current, version, created_at, updated_at
            ) VALUES (
                :id, :candidate_id, :job_vacancy_id, :company_id, 'wsi', 'wsi_screening',
                :score, :wsi_score, :archetype, :recommendation, :summary, :score_breakdown::jsonb,
                :strengths::jsonb, :concerns::jsonb, :gaps::jsonb, :skills_match::jsonb, :skills_missing::jsonb,
                :next_steps::jsonb, true, :version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """), {
            "id": opinion_id,
            "candidate_id": request.candidate_id,
            "job_vacancy_id": request.job_vacancy_id,
            "company_id": company_id,
            "score": round(avg_score, 2),
            "wsi_score": round(avg_score, 2),
            "archetype": archetypes[0].archetype if archetypes else "Perfil Equilibrado",
            "recommendation": recommendation,
            "summary": summary,
            "score_breakdown": json.dumps({
                "bloom_level": round(avg_bloom),
                "dreyfus_level": round(avg_dreyfus),
                "cognitive_score": round(avg_bloom / 6 * 100),
                "proficiency_score": round(avg_dreyfus / 5 * 100)
            }),
            "strengths": json.dumps(strengths),
            "concerns": json.dumps(concerns),
            "gaps": json.dumps(gaps),
            "skills_match": json.dumps([]),
            "skills_missing": json.dumps([]),
            "next_steps": json.dumps(recommendations),
            "version": new_version
        })

        await db.commit()
        logger.info(f"Created WSI opinion {opinion_id} for candidate {request.candidate_id}, vacancy {request.job_vacancy_id}")

    except Exception as e:
        logger.warning(f"Failed to create WSI opinion: {e}")
        # Don't fail the whole request - WSI result is still saved

    return CompleteScreeningResponse(
        result_id=result_id,
        candidate_id=request.candidate_id,
        job_vacancy_id=request.job_vacancy_id,
        overall_score=round(avg_score, 2),
        classification=classification,
        cognitive_level={
            "level": round(avg_bloom),
            "name": bloom_level_name["name"],
            "name_pt": bloom_level_name["name_pt"],
            "description": bloom_level_name["description"]
        },
        proficiency_level={
            "level": round(avg_dreyfus),
            "name": dreyfus_level_name["name"],
            "name_pt": dreyfus_level_name["name_pt"],
            "description": dreyfus_level_name["description"]
        },
        big_five_profile=avg_big_five,
        archetype_indicators=archetypes,
        summary=summary,
        recommendations=recommendations,
        response_analyses=response_analyses
    )
