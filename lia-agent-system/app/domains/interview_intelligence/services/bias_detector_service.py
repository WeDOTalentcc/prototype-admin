"""
Bias Detector Service — Enhanced interviewer bias detection.

Analyzes ONLY interviewer utterances (not candidate self-disclosures).

Three detection layers:
1. Speaker-aware pattern matching: parses speaker turns, applies regex only to
   interviewer lines (illegal questions, bias indicators)
2. Structural analysis: talk-time ratio (interviewer vs candidate), leading
   question detection, question diversity
3. LLM-powered: deep contextual analysis with interviewer-only transcript

Detects: age, gender, appearance, family status, socioeconomic,
disability, racial, religious, sexual orientation, affinity bias,
disproportionate talk-time, and leading questions.

Enforces tenant isolation via mandatory company_id.
"""
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_intelligence.repositories.interview_repository import (
    InterviewRepository,
)

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

LEADING_QUESTION_PATTERNS: list[tuple[str, str]] = [
    (r"você não acha que\b", "Pergunta indutiva: 'você não acha que...'"),
    (r"concorda que\b", "Pergunta indutiva: 'concorda que...'"),
    (r"é verdade que\b", "Pergunta indutiva: 'é verdade que...'"),
    (r"obviamente você\b", "Pergunta presumptiva: 'obviamente você...'"),
    (r"certamente você\b", "Pergunta presumptiva: 'certamente você...'"),
    (r"todo mundo sabe que\b", "Pressão social: 'todo mundo sabe que...'"),
    (r"não seria melhor\b", "Pergunta direcionada: 'não seria melhor...'"),
    (r"você deveria\b", "Pergunta prescritiva: 'você deveria...'"),
]

INTERVIEWER_LABELS = [
    "entrevistador", "entrevistadora", "interviewer", "recruiter",
    "recrutador", "recrutadora", "avaliador", "avaliadora",
    "gestor", "gestora", "manager", "hiring manager",
]

CANDIDATE_LABELS = [
    "candidato", "candidata", "candidate", "entrevistado", "entrevistada",
]

LLM_BIAS_PROMPT = """Você é um especialista em recrutamento justo e equitativo (DEI — Diversity, Equity & Inclusion).

Analise APENAS as falas do ENTREVISTADOR na transcrição abaixo. Identifique sinais de viés (consciente ou inconsciente) nas PERGUNTAS e COMENTÁRIOS do entrevistador — NÃO em auto-revelações do candidato.

TIPOS DE VIÉS A DETECTAR:
1. Viés de confirmação — perguntas direcionadas para confirmar impressão inicial
2. Viés de afinidade — favoritismo por similaridade (mesma escola, cidade, etc.)
3. Viés de halo/horn — deixar uma característica influenciar toda avaliação
4. Viés de gênero — perguntas diferenciadas por gênero
5. Viés de idade — suposições baseadas em idade
6. Viés socioeconômico — julgamento por origem social
7. Viés de aparência — comentários sobre aparência física
8. Perguntas ilegais — perguntas sobre família, religião, orientação sexual, saúde
9. Perguntas indutivas/direcionadas — leading questions que sugerem a resposta
10. Estereotipagem — generalizações baseadas em grupo

IMPORTANTE: Se o candidato menciona espontaneamente informações pessoais (família, religião, etc.), isso NÃO é viés do entrevistador. Foque apenas nas perguntas e comentários iniciados pelo entrevistador.

FALAS DO ENTREVISTADOR:
{interviewer_text}

Responda em JSON com a estrutura:
{{
  "bias_detected": true/false,
  "overall_fairness_score": 1-5 (5 = totalmente justo),
  "findings": [
    {{
      "type": "tipo_do_viés",
      "excerpt": "trecho citado do entrevistador",
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

        _ii_repo = InterviewRepository(db)
        interview = await _ii_repo.get_for_company(
            interview_id=interview_id, company_id=company_id
        )
        if not interview:
            return {"success": False, "error": "Interview not found"}

        transcript = interview.transcript
        if not transcript or len(transcript.strip()) < 50:
            return {"success": False, "error": "Transcript too short or missing"}

        turns = self._parse_speaker_turns(transcript)
        interviewer_text = self._extract_interviewer_text(turns)

        pattern_findings = self._detect_patterns_interviewer_only(interviewer_text)
        leading_findings = self._detect_leading_questions(interviewer_text)
        talk_time = self._compute_talk_time(turns)

        llm_findings: dict[str, Any] = {}
        if use_llm and interviewer_text:
            llm_findings = await self._detect_with_llm(interviewer_text)

        merged = self._merge_findings(
            pattern_findings, leading_findings, talk_time, llm_findings
        )

        return {
            "success": True,
            "interview_id": interview_id,
            "bias_detected": merged["bias_detected"],
            "overall_fairness_score": merged["fairness_score"],
            "talk_time_analysis": talk_time,
            "pattern_alerts": pattern_findings,
            "leading_question_alerts": leading_findings,
            "llm_analysis": llm_findings if use_llm else None,
            "findings": merged["findings"],
            "summary": merged["summary"],
            "recommendations": merged["recommendations"],
        }

    def _parse_speaker_turns(self, transcript: str) -> list[dict[str, Any]]:
        lines = transcript.strip().split("\n")
        turns: list[dict[str, Any]] = []
        current_speaker = "unknown"
        current_role = "unknown"
        current_text: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            speaker_match = re.match(r"^([^:]{1,50}):\s*(.*)$", line)
            if speaker_match:
                if current_text:
                    turns.append({
                        "speaker": current_speaker,
                        "role": current_role,
                        "text": " ".join(current_text),
                        "word_count": sum(len(t.split()) for t in current_text),
                    })
                    current_text = []

                current_speaker = speaker_match.group(1).strip()
                current_role = self._classify_speaker(current_speaker)
                remaining = speaker_match.group(2).strip()
                if remaining:
                    current_text.append(remaining)
            else:
                current_text.append(line)

        if current_text:
            turns.append({
                "speaker": current_speaker,
                "role": current_role,
                "text": " ".join(current_text),
                "word_count": sum(len(t.split()) for t in current_text),
            })

        return turns

    def _classify_speaker(self, speaker_name: str) -> str:
        name_lower = speaker_name.lower().strip()
        for label in INTERVIEWER_LABELS:
            if label in name_lower:
                return "interviewer"
        for label in CANDIDATE_LABELS:
            if label in name_lower:
                return "candidate"
        return "unknown"

    def _extract_interviewer_text(self, turns: list[dict[str, Any]]) -> str:
        interviewer_turns = [t["text"] for t in turns if t["role"] == "interviewer"]
        if not interviewer_turns:
            if len(turns) >= 2:
                interviewer_turns = [t["text"] for t in turns[::2]]
        return "\n".join(interviewer_turns)

    def _detect_patterns_interviewer_only(self, interviewer_text: str) -> list[dict[str, Any]]:
        if not interviewer_text:
            return []
        text_lower = interviewer_text.lower()
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
                    "source": "pattern_interviewer",
                })
        return alerts

    def _detect_leading_questions(self, interviewer_text: str) -> list[dict[str, Any]]:
        if not interviewer_text:
            return []
        text_lower = interviewer_text.lower()
        alerts: list[dict[str, Any]] = []
        for pattern, description in LEADING_QUESTION_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                alerts.append({
                    "type": "leading_question",
                    "description": description,
                    "occurrences": len(matches),
                    "severity": "medium",
                    "source": "leading_question_detector",
                })
        return alerts

    def _compute_talk_time(self, turns: list[dict[str, Any]]) -> dict[str, Any]:
        interviewer_words = sum(
            t["word_count"] for t in turns if t["role"] == "interviewer"
        )
        candidate_words = sum(
            t["word_count"] for t in turns if t["role"] == "candidate"
        )
        total = interviewer_words + candidate_words or 1

        interviewer_ratio = round(interviewer_words / total, 2)
        candidate_ratio = round(candidate_words / total, 2)

        disproportionate = interviewer_ratio > 0.60

        return {
            "interviewer_words": interviewer_words,
            "candidate_words": candidate_words,
            "interviewer_ratio": interviewer_ratio,
            "candidate_ratio": candidate_ratio,
            "disproportionate": disproportionate,
            "assessment": (
                "Entrevistador fala demais — candidato teve pouco espaço"
                if disproportionate
                else "Proporção de fala equilibrada"
            ),
        }

    async def _detect_with_llm(self, interviewer_text: str) -> dict[str, Any]:
        import json
        try:
            from app.domains.ai.services.llm import LLMService
            llm = LLMService()

            truncated = interviewer_text[:6000] if len(interviewer_text) > 6000 else interviewer_text
            prompt = LLM_BIAS_PROMPT.format(interviewer_text=truncated)

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
        leading_alerts: list[dict[str, Any]],
        talk_time: dict[str, Any],
        llm_result: dict[str, Any],
    ) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []

        for alert in pattern_alerts:
            findings.append({
                "type": alert["type"],
                "description": alert["description"],
                "severity": alert["severity"],
                "source": "pattern_interviewer",
                "occurrences": alert["occurrences"],
            })

        for alert in leading_alerts:
            findings.append({
                "type": alert["type"],
                "description": alert["description"],
                "severity": alert["severity"],
                "source": "leading_question_detector",
                "occurrences": alert["occurrences"],
            })

        if talk_time.get("disproportionate"):
            findings.append({
                "type": "disproportionate_talk_time",
                "description": (
                    f"Entrevistador usou {talk_time['interviewer_ratio']*100:.0f}% do tempo de fala. "
                    "Candidato teve pouco espaço para demonstrar competências."
                ),
                "severity": "medium",
                "source": "talk_time_analysis",
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
            high_count = sum(1 for f in findings if f.get("severity") in ("alta", "high"))
            med_count = sum(1 for f in findings if f.get("severity") in ("média", "medium"))
            penalty = high_count * 1.0 + med_count * 0.5
            fairness_score = max(1, round(5 - penalty))

        recommendations: list[str] = []
        if bias_detected:
            recommendations.append(
                "Revisar linguagem e perguntas do entrevistador para eliminar vieses identificados."
            )
            high_severity = [f for f in findings if f.get("severity") in ("alta", "high")]
            if high_severity:
                recommendations.append(
                    "Treinamento urgente em entrevista inclusiva recomendado para o entrevistador."
                )
            if any(f["type"] == "leading_question" for f in findings):
                recommendations.append(
                    "Substituir perguntas indutivas por perguntas abertas baseadas em competências."
                )
            if talk_time.get("disproportionate"):
                recommendations.append(
                    "Reduzir tempo de fala do entrevistador — regra 80/20 (candidato fala 80%)."
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
                    f"{len(findings)} indicador(es) de viés detectado(s) nas falas do entrevistador. "
                    f"Score de equidade: {fairness_score}/5."
                )
            else:
                summary = "Nenhum viés detectado nas falas do entrevistador. Entrevista conduzida de forma justa."

        return {
            "bias_detected": bias_detected,
            "fairness_score": fairness_score,
            "findings": findings,
            "summary": summary,
            "recommendations": recommendations,
        }


bias_detector_service = BiasDetectorService()
