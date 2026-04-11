"""
Interview Intelligence — Analyze interview transcriptions for sentiment,
competency mapping, and bias detection.

Complements the existing voice screening with deeper interview analysis.
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


@tool_handler("talent_intelligence")
async def analyze_interview_recording(
    transcript: str = "",
    candidate_id: str | None = None,
    job_id: str | None = None,
    interviewer_name: str | None = None,
    interview_type: str = "behavioral",
    **kwargs,
) -> dict[str, Any]:
    """
    Analyze an interview transcript for sentiment, competency mapping,
    and potential bias indicators.

    Args:
        transcript: Full text transcript of the interview
        candidate_id: UUID of the candidate being interviewed
        job_id: UUID of the job position
        interviewer_name: Name of the interviewer
        interview_type: Type of interview (behavioral, technical, cultural, final)
    """
    if not transcript or len(transcript.strip()) < 50:
        return {
            "success": False,
            "data": {},
            "message": "Transcrição da entrevista é obrigatória (mínimo 50 caracteres).",
        }

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
