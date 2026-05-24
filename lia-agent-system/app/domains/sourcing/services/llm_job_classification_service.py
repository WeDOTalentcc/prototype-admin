"""
LLM Job Classification Service (Fase 5 / G3).

Post-vector-search filter that validates candidate-job compatibility using LLM.
Removes candidates whose profiles are fundamentally incompatible with the vacancy
(e.g., a Java developer matched against a neurosurgeon vacancy via keyword overlap).

Uses Gemini Flash for low-latency classification. Falls back to heuristic matching
when LLM is unavailable.
"""
import hashlib
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_CLASSIFICATION_CACHE: dict[str, tuple[dict[str, Any], float]] = {}
_CACHE_TTL_SECONDS = 300
_CACHE_MAX_SIZE = 500

COMPATIBILITY_PROMPT = """Você é um especialista em recrutamento. Analise se o candidato é COMPATÍVEL com a vaga.

## Vaga:
Título: {job_title}
Área: {job_area}
Requisitos: {job_requirements}

## Candidato:
Nome: {candidate_name}
Cargo Atual: {candidate_title}
Experiência: {candidate_experience}
Habilidades: {candidate_skills}

## Regras:
- COMPATÍVEL: o candidato tem formação/experiência relevante para a vaga, mesmo que não atenda 100% dos requisitos
- INCOMPATÍVEL: o candidato é de área completamente diferente (ex: médico vs programador, motorista vs designer)
- Na dúvida, classifique como COMPATÍVEL (evitar falsos negativos)

Responda APENAS em JSON:
{{"compatible": true/false, "confidence": 0.0-1.0, "reason": "explicação breve"}}"""

INCOMPATIBLE_AREAS = {
    ("saude", "tecnologia"), ("saude", "logistica"), ("saude", "marketing"),
    ("tecnologia", "saude"), ("tecnologia", "agropecuaria"),
    ("juridico", "tecnologia"), ("juridico", "logistica"),
    ("engenharia_civil", "tecnologia"), ("engenharia_civil", "saude"),
    ("educacao", "tecnologia"), ("educacao", "financeiro"),
    ("agropecuaria", "tecnologia"), ("agropecuaria", "financeiro"),
}


def _detect_area(text: str) -> str | None:
    text_lower = (text or "").lower()
    area_keywords = {
        "saude": ["médico", "medico", "enfermeiro", "hospital", "clínica", "clinica", "saúde", "saude", "cirurgião", "cirurgiao", "farmacêutico", "farmaceutico", "fisioterapeuta", "nutricionista", "psicólogo", "psicologo", "dentista", "odontolog"],
        "tecnologia": ["developer", "desenvolvedor", "programador", "software", "frontend", "backend", "devops", "data engineer", "cloud", "sre", "fullstack", "react", "python", "java", "typescript", "machine learning", "dados", "data science"],
        "juridico": ["advogado", "jurídico", "juridico", "direito", "compliance", "regulatório", "regulatorio"],
        "logistica": ["motorista", "logística", "logistica", "transporte", "armazém", "armazem", "estoque", "supply chain", "cadeia de suprimentos"],
        "marketing": ["marketing", "publicidade", "propaganda", "mídia", "midia", "social media", "branding", "comunicação", "comunicacao"],
        "financeiro": ["contabilidade", "financeiro", "auditoria", "controller", "tesouraria", "fiscal", "tributário", "tributario", "banking"],
        "engenharia_civil": ["engenheiro civil", "construção", "construcao", "obra", "arquiteto", "urbanismo", "estrutural"],
        "educacao": ["professor", "pedagogo", "educação", "educacao", "docente", "ensino", "escola"],
        "agropecuaria": ["agrônomo", "agronomo", "agropecuário", "agropecuario", "veterinário", "veterinario", "zootecnia", "agricultura"],
    }
    for area, keywords in area_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return area
    return None


def _cache_key(
    job_title: str,
    job_area: str,
    job_requirements: str,
    candidate_title: str,
) -> str:
    raw = (
        f"{job_title.strip().lower()}|"
        f"{job_area.strip().lower()}|"
        f"{job_requirements.strip().lower()[:200]}|"
        f"{candidate_title.strip().lower()}"
    )
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_get(key: str) -> dict[str, Any] | None:
    entry = _CLASSIFICATION_CACHE.get(key)
    if entry is None:
        return None
    result, ts = entry
    if time.monotonic() - ts > _CACHE_TTL_SECONDS:
        _CLASSIFICATION_CACHE.pop(key, None)
        return None
    return result


def _cache_put(key: str, result: dict[str, Any]) -> None:
    if len(_CLASSIFICATION_CACHE) >= _CACHE_MAX_SIZE:
        oldest_key = min(_CLASSIFICATION_CACHE, key=lambda k: _CLASSIFICATION_CACHE[k][1])
        _CLASSIFICATION_CACHE.pop(oldest_key, None)
    _CLASSIFICATION_CACHE[key] = (result, time.monotonic())


class LLMJobClassificationService:
    def _heuristic_check(
        self,
        job_info: dict[str, Any],
        candidate: dict[str, Any],
    ) -> tuple[bool, float, str]:
        job_text = f"{job_info.get('title', '')} {job_info.get('area', '')} {job_info.get('requirements', '')}"
        candidate_text = f"{candidate.get('title', '')} {candidate.get('experience', '')} {candidate.get('skills', '')}"

        job_area = _detect_area(job_text)
        cand_area = _detect_area(candidate_text)

        if job_area and cand_area and (job_area, cand_area) in INCOMPATIBLE_AREAS:
            return False, 0.75, f"Áreas incompatíveis: vaga={job_area}, candidato={cand_area}"

        return True, 0.5, "Heurística: sem incompatibilidade detectada"

    async def classify_candidate(
        self,
        job_info: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        ck = _cache_key(
            job_info.get("title", ""),
            job_info.get("area", ""),
            str(job_info.get("requirements", ""))[:200],
            candidate.get("title", ""),
        )
        cached = _cache_get(ck)
        if cached is not None:
            logger.debug("[LLMJobClassification] Cache hit: %s", ck[:8])
            return {**cached, "method": cached.get("method", "cached") + "_cached"}

        try:
            from app.shared.providers.llm_factory import get_provider_for_tenant

            prompt = COMPATIBILITY_PROMPT.format(
                job_title=job_info.get("title", "N/A"),
                job_area=job_info.get("area", "N/A"),
                job_requirements=str(job_info.get("requirements", "N/A"))[:500],
                candidate_name=candidate.get("name", "N/A"),
                candidate_title=candidate.get("title", "N/A"),
                candidate_experience=str(candidate.get("experience", "N/A"))[:400],
                candidate_skills=str(candidate.get("skills", "N/A"))[:300],
            )

            container = get_provider_for_tenant()
            text = await container.generate_with_fallback(prompt, agent_type="JobClassificationAgent")
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text)

            result = {
                "compatible": parsed.get("compatible", True),
                "confidence": parsed.get("confidence", 0.5),
                "reason": parsed.get("reason", ""),
                "method": "llm",
            }
            _cache_put(ck, result)
            return result
        except Exception as exc:
            logger.debug("[LLMJobClassification] LLM fallback to heuristic: %s", exc)
            compatible, confidence, reason = self._heuristic_check(job_info, candidate)
            return {
                "compatible": compatible,
                "confidence": confidence,
                "reason": reason,
                "method": "heuristic_fallback",
            }

    async def filter_candidates(
        self,
        job_info: dict[str, Any],
        candidates: list[dict[str, Any]],
        min_confidence: float = 0.6,
    ) -> dict[str, Any]:
        compatible = []
        filtered_out = []

        for candidate in candidates:
            result = await self.classify_candidate(job_info, candidate)
            candidate_with_classification = {
                **candidate,
                "job_compatibility": result,
            }

            if result["compatible"] or result["confidence"] < min_confidence:
                compatible.append(candidate_with_classification)
            else:
                filtered_out.append(candidate_with_classification)

        logger.info(
            "[LLMJobClassification] Filtered %d/%d candidates for '%s' (min_conf=%.2f)",
            len(filtered_out), len(candidates), job_info.get("title", "?"), min_confidence,
        )

        return {
            "compatible_candidates": compatible,
            "filtered_out": filtered_out,
            "total_input": len(candidates),
            "total_compatible": len(compatible),
            "total_filtered": len(filtered_out),
        }


llm_job_classification_service = LLMJobClassificationService()
