"""
Interview Intelligence Pro — Full interview analysis suite.

Premium tools (module: interview_intelligence):
- analyze_interview_recording: Full WSI + bias + comparative + opinion + feedback
- detect_interview_bias: Standalone bias detection
- generate_interview_opinion: Strategic hiring recommendation
- generate_candidate_feedback: Structured feedback for candidate
- compare_interview_performance: Comparative analysis across candidates
"""
import logging
import re
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

BIAS_INDICATORS = [
    (r"\b(idade|velho|jovem|novo demais)\b", "age_bias", "Referência a idade do candidato"),
    (r"\b(bonit[oa]|atraente|aparência|feio|magr[oa]|gord[oa])\b", "appearance_bias", "Referência à aparência física"),
    (r"\b(casad[oa]|solteir[oa]|filhos|grávida|gestante|maternidade)\b", "family_status_bias", "Referência a estado civil/família"),
    (r"\b(sotaque|regional|periferia|favela)\b", "socioeconomic_bias", "Referência a origem socioeconômica"),
    (r"\b(deficiente|deficiência|cadeirante|cego|surdo|mudo)\b", "disability_bias", "Referência a deficiência"),
    (r"\b(raça|cor|negro|branco|pardo|indígena|asiático)\b", "racial_bias", "Referência a raça/cor"),
    (r"\b(religião|religioso|igreja|deus|ateu)\b", "religious_bias", "Referência a religião"),
    (r"\b(orientação sexual|gay|lésbica|trans|heterossexual|homossexual)\b", "sexual_orientation_bias", "Referência a orientação sexual"),
]

COMPETENCY_KEYWORDS = {
    "liderança": ["liderar", "liderança", "equipe", "time", "gerenciar", "coordenar", "delegar", "mentoria"],
    "comunicação": ["comunicar", "comunicação", "apresentar", "explicar", "articular", "negociar"],
    "resolução de problemas": ["resolver", "solução", "problema", "desafio", "analisar", "diagnosticar"],
    "trabalho em equipe": ["equipe", "colaborar", "colaboração", "parceria", "integração", "coletivo"],
    "adaptabilidade": ["adaptar", "mudança", "flexível", "flexibilidade", "aprender", "novo"],
    "proatividade": ["proativo", "iniciativa", "antecipar", "propor", "sugerir", "melhorar"],
    "pensamento analítico": ["analisar", "dados", "métricas", "indicadores", "avaliar", "investigar"],
    "gestão de tempo": ["prazo", "deadline", "priorizar", "organizar", "produtividade", "eficiência"],
    "orientação a resultados": ["resultado", "meta", "objetivo", "entrega", "performance", "kpi"],
    "criatividade": ["criativo", "inovar", "inovação", "ideia", "inventar", "design thinking"],
}

SENTIMENT_POSITIVE = ["excelente", "ótimo", "bom", "forte", "destaque", "impressionante", "qualificado", "competente", "seguro", "claro"]
SENTIMENT_NEGATIVE = ["fraco", "ruim", "insuficiente", "falta", "não conseguiu", "dificuldade", "preocupante", "risco", "confuso", "inseguro"]


@tool_handler("talent_intelligence", module="interview_intelligence")
async def analyze_interview_recording(
    interview_id: str | None = None,
    transcript: str = "",
    candidate_id: str | None = None,
    job_id: str | None = None,
    interviewer_name: str | None = None,
    interview_type: str = "behavioral",
    include_bias: bool = True,
    include_comparative: bool = True,
    include_opinion: bool = True,
    include_feedback: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """
    Full interview analysis: WSI + bias detection + comparative + opinion + feedback.

    If interview_id is provided, fetches transcript from DB.
    Otherwise falls back to inline transcript analysis.
    """
    db = kwargs.get("db")
    company_id = kwargs.get("company_id", "")

    if interview_id and db:
        if not company_id:
            return {
                "success": False,
                "data": {},
                "message": "company_id é obrigatório para isolamento de tenant.",
            }
        return await _analyze_from_db(
            interview_id=interview_id,
            db=db,
            company_id=company_id,
            include_bias=include_bias,
            include_comparative=include_comparative,
            include_opinion=include_opinion,
            include_feedback=include_feedback,
        )

    if not transcript or len(transcript.strip()) < 50:
        return {
            "success": False,
            "data": {},
            "message": "Transcrição da entrevista é obrigatória (mínimo 50 caracteres).",
        }

    return _analyze_inline(
        transcript=transcript,
        candidate_id=candidate_id,
        job_id=job_id,
        interviewer_name=interviewer_name,
        interview_type=interview_type,
    )


async def _analyze_from_db(
    interview_id: str,
    db: Any,
    company_id: str,
    include_bias: bool,
    include_comparative: bool,
    include_opinion: bool,
    include_feedback: bool,
) -> dict[str, Any]:
    from app.domains.interview_intelligence.services.interview_wsi_service import interview_wsi_service

    wsi_result = await interview_wsi_service.analyze(interview_id, db, company_id=company_id)
    if not wsi_result.get("success"):
        return {
            "success": False,
            "data": {},
            "message": wsi_result.get("error", "WSI analysis failed"),
        }

    result: dict[str, Any] = {
        "wsi_analysis": wsi_result,
    }

    if include_bias:
        from app.domains.interview_intelligence.services.bias_detector_service import bias_detector_service
        bias_result = await bias_detector_service.detect(interview_id, db, use_llm=True, company_id=company_id)
        result["bias_detection"] = bias_result
    else:
        bias_result = None

    if include_comparative:
        from app.domains.interview_intelligence.services.comparative_analysis_service import comparative_analysis_service
        comparative_result = await comparative_analysis_service.compare(
            interview_id, db, company_id
        )
        result["comparative_analysis"] = comparative_result
    else:
        comparative_result = None

    if include_opinion:
        from app.domains.interview_intelligence.services.strategic_opinion_service import strategic_opinion_service
        opinion_result = await strategic_opinion_service.generate(
            interview_id, db,
            wsi_data=wsi_result,
            bias_data=bias_result,
            comparative_data=comparative_result,
            company_id=company_id,
        )
        result["strategic_opinion"] = opinion_result
    else:
        opinion_result = None

    if include_feedback:
        from app.domains.interview_intelligence.services.feedback_generator_service import feedback_generator_service
        feedback_result = await feedback_generator_service.generate(
            interview_id, db, wsi_data=wsi_result, company_id=company_id
        )
        result["candidate_feedback"] = feedback_result

    recommendation = "AVALIAR MAIS"
    if opinion_result and opinion_result.get("success"):
        recommendation = opinion_result.get("recommendation", "AVALIAR MAIS")
    elif wsi_result.get("recommendation"):
        rec_map = {"approve": "CONTRATAR", "reject": "NÃO CONTRATAR", "pending_review": "AVALIAR MAIS"}
        recommendation = rec_map.get(wsi_result["recommendation"], "AVALIAR MAIS")

    return {
        "success": True,
        "data": result,
        "message": (
            f"Análise completa da entrevista concluída. "
            f"WSI: {wsi_result.get('wsi_score', 'N/A')}/5.0. "
            f"Recomendação: {recommendation}."
        ),
    }


@tool_handler("talent_intelligence", module="interview_intelligence")
async def detect_interview_bias(
    interview_id: str = "",
    use_llm: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """
    Detect bias in an interview transcript (pattern + LLM analysis).
    Requires interview_id of a transcribed interview.
    """
    db = kwargs.get("db")
    company_id = kwargs.get("company_id", "")
    if not interview_id or not db:
        return {
            "success": False,
            "data": {},
            "message": "interview_id e conexão com banco são obrigatórios.",
        }
    if not company_id:
        return {
            "success": False,
            "data": {},
            "message": "company_id é obrigatório para isolamento de tenant.",
        }

    from app.domains.interview_intelligence.services.bias_detector_service import bias_detector_service
    result = await bias_detector_service.detect(interview_id, db, use_llm=use_llm, company_id=company_id)

    if not result.get("success"):
        return {
            "success": False,
            "data": {},
            "message": result.get("error", "Bias detection failed"),
        }

    return {
        "success": True,
        "data": result,
        "message": (
            f"Detecção de viés concluída. "
            f"Viés detectado: {'Sim' if result.get('bias_detected') else 'Não'}. "
            f"Score de equidade: {result.get('overall_fairness_score', 'N/A')}/5."
        ),
    }


@tool_handler("talent_intelligence", module="interview_intelligence")
async def generate_interview_opinion(
    interview_id: str = "",
    **kwargs,
) -> dict[str, Any]:
    """
    Generate strategic hiring opinion (parecer) for an interview.
    Runs WSI + bias first, then generates LLM opinion.
    """
    db = kwargs.get("db")
    company_id = kwargs.get("company_id", "")
    if not interview_id or not db:
        return {
            "success": False,
            "data": {},
            "message": "interview_id e conexão com banco são obrigatórios.",
        }
    if not company_id:
        return {
            "success": False,
            "data": {},
            "message": "company_id é obrigatório para isolamento de tenant.",
        }

    from app.domains.interview_intelligence.services.interview_wsi_service import interview_wsi_service
    from app.domains.interview_intelligence.services.bias_detector_service import bias_detector_service
    from app.domains.interview_intelligence.services.comparative_analysis_service import comparative_analysis_service
    from app.domains.interview_intelligence.services.strategic_opinion_service import strategic_opinion_service

    wsi_data = await interview_wsi_service.analyze(interview_id, db, company_id=company_id)
    bias_data = await bias_detector_service.detect(interview_id, db, use_llm=True, company_id=company_id)
    comp_data = await comparative_analysis_service.compare(
        interview_id, db, company_id
    )

    result = await strategic_opinion_service.generate(
        interview_id, db,
        wsi_data=wsi_data,
        bias_data=bias_data,
        comparative_data=comp_data,
        company_id=company_id,
    )

    if not result.get("success"):
        return {
            "success": False,
            "data": {},
            "message": result.get("error", "Opinion generation failed"),
        }

    return {
        "success": True,
        "data": result,
        "message": (
            f"Parecer estratégico gerado. "
            f"Recomendação: {result.get('recommendation', 'N/A')} "
            f"(confiança: {result.get('confidence', 'N/A')})."
        ),
    }


@tool_handler("talent_intelligence", module="interview_intelligence")
async def generate_candidate_feedback(
    interview_id: str = "",
    **kwargs,
) -> dict[str, Any]:
    """
    Generate structured candidate feedback from an interview analysis.
    Suitable for sharing with candidates.
    """
    db = kwargs.get("db")
    company_id = kwargs.get("company_id", "")
    if not interview_id or not db:
        return {
            "success": False,
            "data": {},
            "message": "interview_id e conexão com banco são obrigatórios.",
        }
    if not company_id:
        return {
            "success": False,
            "data": {},
            "message": "company_id é obrigatório para isolamento de tenant.",
        }

    from app.domains.interview_intelligence.services.interview_wsi_service import interview_wsi_service
    from app.domains.interview_intelligence.services.feedback_generator_service import feedback_generator_service

    wsi_data = await interview_wsi_service.analyze(interview_id, db, company_id=company_id)
    result = await feedback_generator_service.generate(
        interview_id, db, wsi_data=wsi_data, company_id=company_id
    )

    if not result.get("success"):
        return {
            "success": False,
            "data": {},
            "message": result.get("error", "Feedback generation failed"),
        }

    return {
        "success": True,
        "data": result,
        "message": (
            f"Feedback estruturado gerado para {result.get('candidate_name', 'candidato')}."
        ),
    }


@tool_handler("talent_intelligence", module="interview_intelligence")
async def compare_interview_performance(
    interview_id: str = "",
    **kwargs,
) -> dict[str, Any]:
    """
    Compare interview performance against other candidates for the same vacancy.
    Provides ranking, benchmarks, and insights.
    """
    db = kwargs.get("db")
    company_id = kwargs.get("company_id")
    if not interview_id or not db or not company_id:
        return {
            "success": False,
            "data": {},
            "message": "interview_id, company_id e conexão com banco são obrigatórios.",
        }

    from app.domains.interview_intelligence.services.comparative_analysis_service import comparative_analysis_service
    result = await comparative_analysis_service.compare(
        interview_id, db, company_id
    )

    if not result.get("success"):
        return {
            "success": False,
            "data": {},
            "message": result.get("error", "Comparative analysis failed"),
        }

    ranking = result.get("ranking", {})
    return {
        "success": True,
        "data": result,
        "message": (
            f"Análise comparativa concluída. "
            f"Posição: {ranking.get('position', '?')}/{ranking.get('total_candidates', '?')} "
            f"(percentil {ranking.get('percentile', '?')})."
        ),
    }


def _analyze_inline(
    transcript: str,
    candidate_id: str | None,
    job_id: str | None,
    interviewer_name: str | None,
    interview_type: str,
) -> dict[str, Any]:
    transcript_lower = transcript.lower()
    word_count = len(transcript.split())

    bias_alerts = _detect_bias(transcript_lower)
    competencies = _map_competencies(transcript_lower)
    sentiment = _analyze_sentiment(transcript_lower)
    structure_analysis = _analyze_structure(transcript)

    overall_score = _calculate_overall_score(competencies, sentiment, bias_alerts, structure_analysis)

    recommendations = []
    if bias_alerts:
        recommendations.append(
            f"⚠️ {len(bias_alerts)} indicador(es) de viés detectado(s). "
            "Revisar linguagem para garantir avaliação justa."
        )
    strong_competencies = [c for c in competencies if c["evidence_count"] >= 3]
    if strong_competencies:
        recommendations.append(
            f"Competências mais evidenciadas: {', '.join(c['competency'] for c in strong_competencies[:3])}."
        )
    weak_competencies = [c for c in competencies if c["evidence_count"] == 0]
    if weak_competencies:
        recommendations.append(
            f"Competências não avaliadas: {', '.join(c['competency'] for c in weak_competencies[:3])}. "
            "Considere explorar em próxima entrevista."
        )
    if sentiment["overall"] == "negative":
        recommendations.append(
            "Tom geral da entrevista negativo. Verificar se reflete performance real ou viés do avaliador."
        )

    return {
        "success": True,
        "data": {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "interviewer": interviewer_name,
            "interview_type": interview_type,
            "transcript_stats": {
                "word_count": word_count,
                "estimated_duration_minutes": round(word_count / 150, 1),
            },
            "overall_score": overall_score,
            "sentiment_analysis": sentiment,
            "competency_mapping": competencies,
            "bias_detection": {
                "alerts_count": len(bias_alerts),
                "alerts": bias_alerts,
                "bias_free": len(bias_alerts) == 0,
            },
            "structure_analysis": structure_analysis,
            "recommendations": recommendations,
        },
        "message": (
            f"Análise de entrevista concluída. Score geral: {overall_score}/5. "
            f"{len(competencies)} competências mapeadas, "
            f"{len(bias_alerts)} alerta(s) de viés."
        ),
    }


def _detect_bias(text: str) -> list[dict[str, Any]]:
    alerts = []
    for pattern, bias_type, description in BIAS_INDICATORS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            alerts.append({
                "type": bias_type,
                "description": description,
                "occurrences": len(matches),
                "severity": "high" if len(matches) >= 3 else "medium" if len(matches) >= 2 else "low",
            })
    return alerts


def _map_competencies(text: str) -> list[dict[str, Any]]:
    results = []
    for competency, keywords in COMPETENCY_KEYWORDS.items():
        evidence_count = sum(1 for kw in keywords if kw in text)
        strength = (
            "strong" if evidence_count >= 4
            else "moderate" if evidence_count >= 2
            else "weak" if evidence_count >= 1
            else "not_assessed"
        )
        results.append({
            "competency": competency,
            "evidence_count": evidence_count,
            "strength": strength,
        })
    results.sort(key=lambda x: x["evidence_count"], reverse=True)
    return results


def _analyze_sentiment(text: str) -> dict[str, Any]:
    pos_count = sum(1 for word in SENTIMENT_POSITIVE if word in text)
    neg_count = sum(1 for word in SENTIMENT_NEGATIVE if word in text)
    total = pos_count + neg_count or 1

    if pos_count > neg_count * 1.5:
        overall = "positive"
    elif neg_count > pos_count * 1.5:
        overall = "negative"
    else:
        overall = "neutral"

    return {
        "overall": overall,
        "positive_indicators": pos_count,
        "negative_indicators": neg_count,
        "positivity_ratio": round(pos_count / total, 2),
    }


def _analyze_structure(transcript: str) -> dict[str, Any]:
    lines = transcript.strip().split("\n")
    question_count = sum(1 for line in lines if "?" in line)
    speaker_changes = 0
    prev_speaker = None
    for line in lines:
        if ":" in line[:50]:
            speaker = line.split(":")[0].strip()
            if speaker != prev_speaker:
                speaker_changes += 1
                prev_speaker = speaker

    return {
        "total_lines": len(lines),
        "questions_asked": question_count,
        "speaker_changes": speaker_changes,
        "has_structured_format": speaker_changes > 3,
    }


def _calculate_overall_score(
    competencies: list[dict[str, Any]],
    sentiment: dict[str, Any],
    bias_alerts: list[dict[str, Any]],
    structure: dict[str, Any],
) -> float:
    assessed = [c for c in competencies if c["strength"] != "not_assessed"]
    if not assessed:
        return 3.0

    strength_scores = {"strong": 5, "moderate": 3.5, "weak": 2}
    comp_avg = sum(strength_scores.get(c["strength"], 3) for c in assessed) / len(assessed)

    sentiment_mod = 0
    if sentiment["overall"] == "positive":
        sentiment_mod = 0.3
    elif sentiment["overall"] == "negative":
        sentiment_mod = -0.3

    bias_penalty = min(len(bias_alerts) * 0.2, 1.0)

    score = comp_avg + sentiment_mod - bias_penalty
    return round(max(1.0, min(5.0, score)), 1)
