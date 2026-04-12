"""
Bias Detector Service — Enhanced interviewer bias detection.

Two layers:
1. Deterministic: regex pattern matching for known bias indicators
2. LLM-powered: deep contextual analysis for subtle/implicit bias

Detects: age, gender, appearance, family status, socioeconomic,
disability, racial, religious, sexual orientation, and affinity bias.
"""
import logging
import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import Interview

logger = logging.getLogger(__name__)

BIAS_PATTERNS: list[tuple[str, str, str, str]] = [
    (r"\b(idade|velho|jovem|novo demais|experiência demais|aposentad[oa])\b",
     "age_bias", "high", "Referência a idade do candidato"),
    (r"\b(bonit[oa]|atraente|aparência|feio|magr[oa]|gord[oa]|apresentável)\b",
     "appearance_bias", "high", "Referência à aparência física"),
    (r"\b(casad[oa]|solteir[oa]|filhos|grávida|gestante|maternidade|paternidade)\b",
     "family_status_bias", "high", "Referência a estado civil/família"),
    (r"\b(sotaque|regional|periferia|favela|bairro nobre|classe)\b",
     "socioeconomic_bias", "medium", "Referência a origem socioeconômica"),
    (r"\b(deficiente|deficiência|cadeirante|cego|surdo|mudo|pcd)\b",
     "disability_bias", "high", "Referência a deficiência (pode ser contexto legítimo)"),
    (r"\b(raça|cor|negro|branco|pardo|indígena|asiático|preto)\b",
     "racial_bias", "high", "Referência a raça/cor"),
    (r"\b(religião|religioso|igreja|deus|ateu|evangélic[oa]|católic[oa])\b",
     "religious_bias", "medium", "Referência a religião"),
    (r"\b(orientação sexual|gay|lésbica|trans|heterossexual|homossexual|lgbtq)\b",
     "sexual_orientation_bias", "high", "Referência a orientação sexual"),
    (r"\b(parece comigo|mesma faculdade|mesma cidade|conterrâneo|colega de)\b",
     "affinity_bias", "medium", "Indicador de viés de afinidade"),
    (r"\b(cultural fit|não combina|não é a cara|nosso perfil|cara da empresa)\b",
     "cultural_proxy_bias", "medium", "Proxy para viés via 'cultural fit'"),
]

INTERVIEWER_PATTERN_INDICATORS = [
    (r"entrevistador[a]?:\s*(?:[^?]*\?)", "question_pattern",
     "Padrão de perguntas do entrevistador"),
]

LLM_BIAS_PROMPT = """Você é um especialista em recrutamento justo e equitativo (DEI — Diversity, Equity & Inclusion).

Analise a transcrição de entrevista abaixo e identifique quaisquer sinais de viés (consciente ou inconsciente) por parte do(s) entrevistador(es).

TIPOS DE VIÉS A DETECTAR:
1. Viés de confirmação — perguntas direcionadas para confirmar impressão inicial
2. Viés de afinidade — favoritismo por similaridade (mesma escola, cidade, etc.)
3. Viés de halo/horn — deixar uma característica influenciar toda avaliação
4. Viés de gênero — perguntas diferenciadas por gênero
5. Viés de idade — suposições baseadas em idade
6. Viés socioeconômico — julgamento por origem social
7. Viés de aparência — comentários sobre aparência física
8. Perguntas ilegais — perguntas sobre família, religião, orientação sexual, saúde
9. Estereotipagem — generalizações baseadas em grupo

Para cada viés detectado, forneça:
- Tipo de viés
- Trecho relevante da transcrição (citação direta)
- Severidade: alta/média/baixa
- Recomendação para o entrevistador

Se NÃO detectar viés, diga explicitamente que a entrevista parece justa.

TRANSCRIÇÃO:
{transcript}

Responda em JSON com a estrutura:
{{
  "bias_detected": true/false,
  "overall_fairness_score": 1-5 (5 = totalmente justo),
  "findings": [
    {{
      "type": "tipo_do_viés",
      "excerpt": "trecho citado",
      "severity": "alta/média/baixa",
      "recommendation": "sugestão"
    }}
  ],
  "summary": "resumo em 2-3 frases"
}}"""


class BiasDetectorService:

    async def detect(
        self,
        interview_id: str,
        db: AsyncSession,
        use_llm: bool = True,
        company_id: str = "",
    ) -> dict[str, Any]:
        if not company_id:
            return {"success": False, "error": "company_id is required for tenant isolation"}
        from sqlalchemy import and_
        result = await db.execute(
            select(Interview).where(
                and_(Interview.id == interview_id, Interview.company_id == company_id)
            )
        )
        interview = result.scalar_one_or_none()
        if not interview:
            return {"success": False, "error": "Interview not found"}

        transcript = interview.transcript
        if not transcript or len(transcript.strip()) < 50:
            return {"success": False, "error": "Transcript too short or missing"}

        pattern_findings = self._detect_patterns(transcript)

        llm_findings: dict[str, Any] = {}
        if use_llm:
            llm_findings = await self._detect_with_llm(transcript)

        merged = self._merge_findings(pattern_findings, llm_findings)

        return {
            "success": True,
            "interview_id": interview_id,
            "bias_detected": merged["bias_detected"],
            "overall_fairness_score": merged["fairness_score"],
            "pattern_alerts": pattern_findings,
            "llm_analysis": llm_findings if use_llm else None,
            "findings": merged["findings"],
            "summary": merged["summary"],
            "recommendations": merged["recommendations"],
        }

    def _detect_patterns(self, transcript: str) -> list[dict[str, Any]]:
        text_lower = transcript.lower()
        alerts: list[dict[str, Any]] = []
        for pattern, bias_type, severity, description in BIAS_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                alerts.append({
                    "type": bias_type,
                    "description": description,
                    "occurrences": len(matches),
                    "severity": severity,
                    "matched_terms": list(set(matches))[:5],
                    "source": "pattern",
                })
        return alerts

    async def _detect_with_llm(self, transcript: str) -> dict[str, Any]:
        import json
        try:
            from app.domains.ai.services.llm import LLMService
            llm = LLMService()

            truncated = transcript[:8000] if len(transcript) > 8000 else transcript
            prompt = LLM_BIAS_PROMPT.format(transcript=truncated)

            raw = await llm.generate(prompt, provider="gemini")

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

            return json.loads(cleaned)
        except Exception as exc:
            logger.warning("LLM bias detection failed: %s", exc)
            return {"error": str(exc), "findings": []}

    def _merge_findings(
        self,
        pattern_alerts: list[dict[str, Any]],
        llm_result: dict[str, Any],
    ) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []

        for alert in pattern_alerts:
            findings.append({
                "type": alert["type"],
                "description": alert["description"],
                "severity": alert["severity"],
                "source": "pattern",
                "occurrences": alert["occurrences"],
            })

        llm_findings = llm_result.get("findings", [])
        for f in llm_findings:
            findings.append({
                "type": f.get("type", "unknown"),
                "description": f.get("recommendation", ""),
                "severity": f.get("severity", "medium"),
                "source": "llm",
                "excerpt": f.get("excerpt", ""),
            })

        bias_detected = len(findings) > 0
        fairness_from_llm = llm_result.get("overall_fairness_score", None)

        if fairness_from_llm is not None:
            fairness_score = fairness_from_llm
        else:
            high_count = sum(1 for f in findings if f.get("severity") == "alta" or f.get("severity") == "high")
            med_count = sum(1 for f in findings if f.get("severity") in ("média", "medium"))
            penalty = high_count * 1.0 + med_count * 0.5
            fairness_score = max(1, round(5 - penalty))

        recommendations: list[str] = []
        if bias_detected:
            recommendations.append(
                "Revisar linguagem e perguntas da entrevista para eliminar vieses identificados."
            )
            high_severity = [f for f in findings if f.get("severity") in ("alta", "high")]
            if high_severity:
                recommendations.append(
                    "Treinamento urgente em entrevista inclusiva recomendado para o entrevistador."
                )
            recommendations.append(
                "Considerar uso de roteiro padronizado para garantir equidade entre candidatos."
            )
        else:
            recommendations.append(
                "Entrevista conduzida de forma justa. Manter boas práticas."
            )

        summary = llm_result.get("summary", "")
        if not summary:
            if bias_detected:
                summary = (
                    f"{len(findings)} indicador(es) de viés detectado(s). "
                    f"Score de equidade: {fairness_score}/5."
                )
            else:
                summary = "Nenhum viés detectado. Entrevista conduzida de forma justa e equitativa."

        return {
            "bias_detected": bias_detected,
            "fairness_score": fairness_score,
            "findings": findings,
            "summary": summary,
            "recommendations": recommendations,
        }


bias_detector_service = BiasDetectorService()
