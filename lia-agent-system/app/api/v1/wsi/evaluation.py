
"""WSI evaluation API.

Routes:
  POST /jd-evaluate
  POST /analyze-response
  POST /complete-screening
"""
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.voice.repositories.wsi_repository import WsiRepository
from app.domains.opinions.repositories.opinions_repository import OpinionsRepository

from ._shared import (
    _BIAS_TERMS,
    _JD_SENIORITY_KEYWORDS,
    BLOOM_LEVELS,
    DREYFUS_LEVELS,
    WSI_CLASSIFICATION_MAP,
    AnalyzeResponseOutput,
    AnalyzeResponseRequest,
    ArchetypeIndicator,
    BigFiveIndicators,
    CompleteScreeningRequest,
    CompleteScreeningResponse,
    JDEvaluateRequest,
    JDEvaluateResponse,
    _jd_get_band,
    _run_anthropic_sync,
    classify_wsi_score,
    get_anthropic_client,
    parse_json_response,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/jd-evaluate", response_model=None)
# Phase 2 complete (2026-05-21): WSI scoring stays here; persistence
# moves to OpinionsRepository.create_wsi_opinion_with_atomic_version
# + WsiRepository.insert_result / complete_session.
async def evaluate_jd(request: JDEvaluateRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Evaluate job description quality using 9 dimensions (spec F1.B).
    Hard block if score < 30 (band=Crítico). 5 quality bands."""
    from app.domains.cv_screening.services.wsi_service.jd_quality import (
        evaluate_jd_quality,
    )
    # Consolidação WSI Fase 3: delega ao canônico único (mesma função que o
    # wizard conversacional usa). Single source of truth do score 9-dim.
    _r = evaluate_jd_quality(
        description=request.description,
        job_title=request.job_title,
        department=request.department,
        seniority=request.seniority,
        responsibilities=request.responsibilities,
        technical_skills=request.technical_skills,
        behavioral_competencies=request.behavioral_competencies,
    )
    score = _r["score"]
    band_key = _r["band"]
    band_label = _r["band_label"]
    indicators = _r["indicators"]
    suggestion = _r["suggestion"]
    _details = _r["details"]

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
                "indicators": indicators,
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
        details=_details
    )


@router.post("/analyze-response", response_model=AnalyzeResponseOutput)
async def analyze_response(
    request: AnalyzeResponseRequest,
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Analyze a single candidate response using Claude AI.

    Onda 4.2c-P0-6 (2026-05-23): cross-tenant guard via pre-check do
    session.job_vacancy_id pertencer ao company_id. Antes user empresa A
    podia inserir response_analysis em session da empresa B.

    Evaluates:
    - Bloom's Taxonomy level demonstrated (cognitive level)
    - Dreyfus Model proficiency level
    - Big Five personality indicators
    """
    from sqlalchemy import text as _text

    # Onda 4.2c-P0-6: tenant pre-check via session → job_vacancy → company_id.
    tenant_check = await db.execute(
        _text(
            "SELECT 1 FROM wsi_sessions s "
            "INNER JOIN job_vacancies jv ON jv.id = s.job_vacancy_id "
            "WHERE s.id = :sid AND jv.company_id = :company_id"
        ),
        {"sid": request.session_id, "company_id": company_id},
    )
    if not tenant_check.scalar():
        raise HTTPException(status_code=404, detail="Session not found")

    client = await get_anthropic_client()

    question_text = ""
    try:
        _repo = WsiRepository(db)
        row = await _repo.get_question_text_and_competency(request.question_id)
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
        _repo = WsiRepository(db)
        await _repo.insert_response_analysis_simple(
            analysis_id=analysis_id,
            session_id=request.session_id,
            question_id=request.question_id,
            candidate_id=request.candidate_id,
            job_vacancy_id="",
            competency="General",
            response_text=request.response_text,
            bloom_level=bloom_score,
            dreyfus_level=dreyfus_level,
            evidences=data.get("evidences", []),
            red_flags=data.get("red_flags", []),
            final_score=data.get("score", 3.0),
            justification=data.get("feedback", ""),
        )
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
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Complete WSI screening by analyzing all responses and generating final report.

    Onda 4.2c-P0-7 (2026-05-23): cross-tenant guard via pre-check no
    session_id. Antes user empresa A podia gravar overall_wsi + classification
    fictícios em session/result de outra empresa.

    Returns comprehensive assessment including:
    - Overall score (0-5)
    - Cognitive level (Bloom average)
    - Proficiency level (Dreyfus average)
    - Big Five personality profile
    - Archetype indicators
    - Summary and recommendations
    """
    from sqlalchemy import text as _text

    # Onda 4.2c-P0-7: tenant pre-check.
    tenant_check = await db.execute(
        _text(
            "SELECT 1 FROM wsi_sessions s "
            "INNER JOIN job_vacancies jv ON jv.id = s.job_vacancy_id "
            "WHERE s.id = :sid AND jv.company_id = :company_id"
        ),
        {"sid": request.session_id, "company_id": company_id},
    )
    if not tenant_check.scalar():
        raise HTTPException(status_code=404, detail="Session not found")

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
    # Phase 2.5 boy-scout (A5): use canonical .stability accessor instead
    # of inverting neuroticism inline. stability = 100 - neuroticism.
    o, c, e, a, s = (
        avg_big_five.openness, avg_big_five.conscientiousness,
        avg_big_five.extraversion, avg_big_five.agreeableness, avg_big_five.stability,
    )
    _n = s  # legacy alias kept for any downstream reference

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

    # Persistence — moved out of the endpoint per ADR-001 (2026-05-21).
    # WsiRepository owns wsi_results / wsi_sessions; OpinionsRepository owns
    # the atomic LiaOpinion version write so two concurrent screening
    # completions cannot produce duplicate (candidate, vacancy, version) rows.
    wsi_repo = WsiRepository(db)
    opinions_repo = OpinionsRepository(db)

    result_id = str(uuid.uuid4())
    try:
        await wsi_repo.insert_result(
            result_id=result_id,
            session_id=request.session_id,
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id or "",
            technical_wsi=avg_score,
            behavioral_wsi=avg_score,
            overall_wsi=avg_score,
            classification=classification,
            percentile=None,
        )
        await wsi_repo.complete_session(request.session_id)
    except Exception as e:
        logger.warning(f"Failed to save result: {e}")

    # Resolve company_id for the LiaOpinion write.
    # Vacancy-linked screenings derive the tenant from the vacancy row
    # (repo-side lookup, never from request payload). Non-vacancy
    # screenings fall back to the JWT-derived company_id from the
    # endpoint signature.
    try:
        resolved_company_id: str | None = None
        if request.job_vacancy_id:
            resolved_company_id = await opinions_repo.get_company_id_for_vacancy(
                request.job_vacancy_id
            )
        if not resolved_company_id:
            resolved_company_id = company_id

        # Determine recommendation per canonical WSI_CUTOFFS (Spec §10.3)
        # approved_auto >= 3.75/5 (= 7.5/10), review_min >= 3.0/5 (= 6.0/10)
        if avg_score >= 3.75:
            recommendation = "approved"
        elif avg_score >= 3.0:
            recommendation = "pending_review"
        else:
            recommendation = "not_approved"

        # Categorize recommendations into strengths, concerns, and gaps.
        # (Same heuristic as before — back-compat preserved.)
        strengths = [r for r in recommendations if "sólido" in r.lower() or "demonstra" in r.lower()]
        concerns = [r for r in recommendations if "desenvolver" in r.lower() or "trabalhar" in r.lower()]
        gaps = [r for r in recommendations if "ganhar" in r.lower() or "experiência" in r.lower()]

        opinion_id = await opinions_repo.create_wsi_opinion_with_atomic_version(
            candidate_id=request.candidate_id,
            job_vacancy_id=request.job_vacancy_id,
            company_id=resolved_company_id,
            score=round(avg_score, 2),
            wsi_score=round(avg_score, 2),
            archetype=archetypes[0].archetype if archetypes else "Perfil Equilibrado",
            recommendation=recommendation,
            summary=summary,
            score_breakdown={
                "bloom_level": round(avg_bloom),
                "dreyfus_level": round(avg_dreyfus),
                "cognitive_score": round(avg_bloom / 6 * 100),
                "proficiency_score": round(avg_dreyfus / 5 * 100),
            },
            strengths=strengths,
            concerns=concerns,
            gaps=gaps,
            matched_skills=[],
            missing_skills=[],
            next_steps=recommendations,
        )

        logger.info(
            f"Created WSI opinion {opinion_id} for candidate {request.candidate_id}, vacancy {request.job_vacancy_id}"
        )

    except Exception as e:
        logger.warning(f"Failed to create WSI opinion: {e}")
        # Don't fail the whole request — the WSI result is still saved.

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
