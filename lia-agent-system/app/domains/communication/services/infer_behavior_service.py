"""
Infer Behavior Service - Suggests action_behavior for custom pipeline stages.
Phase 6.5: Smart behavior inference for custom columns.
"""
import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.shared.providers.llm_client import is_llm_available, llm_complete

logger = logging.getLogger(__name__)

BEHAVIOR_KEYWORDS: dict[str, list[tuple[str, float]]] = {
    "screening": [
        ("triagem", 0.95), ("screening", 0.95), ("pré-seleção", 0.90),
        ("pre-selecao", 0.90), ("filtro", 0.80), ("qualificação", 0.75),
    ],
    "scheduling": [
        ("entrevista", 0.95), ("interview", 0.95), ("reunião", 0.85),
        ("meeting", 0.85), ("agendamento", 0.90), ("dinâmica", 0.85),
        ("banca", 0.80), ("painel", 0.75), ("conversa", 0.70),
    ],
    "evaluation": [
        ("teste", 0.95), ("test", 0.95), ("avaliação", 0.90),
        ("assessment", 0.90), ("case", 0.85), ("estudo de caso", 0.90),
        ("prova", 0.90), ("desafio", 0.85), ("exercício", 0.80),
        ("técnico", 0.70), ("inglês", 0.75), ("redação", 0.80),
    ],
    "verification": [
        ("referência", 0.95), ("reference", 0.95), ("verificação", 0.90),
        ("documento", 0.90), ("background", 0.90), ("check", 0.80),
        ("compliance", 0.80), ("validação", 0.80), ("antecedente", 0.85),
    ],
    "offer": [
        ("proposta", 0.95), ("offer", 0.95), ("negociação", 0.85),
        ("salário", 0.80), ("contrato", 0.80), ("remuneração", 0.80),
    ],
    "intake": [
        ("funil", 0.90), ("sourcing", 0.95), ("captação", 0.85),
        ("prospecção", 0.90), ("entrada", 0.75), ("candidatura", 0.80),
    ],
    "conclusion_hired": [
        ("contratado", 0.95), ("hired", 0.95), ("admissão", 0.90),
        ("onboarding", 0.85), ("integração", 0.70),
    ],
    "conclusion_rejected": [
        ("reprovado", 0.95), ("rejected", 0.95), ("recusado", 0.85),
        ("eliminado", 0.80), ("descartado", 0.75),
    ],
    "conclusion_declined": [
        ("desistiu", 0.90), ("declined", 0.90), ("recusa", 0.85),
        ("declinou", 0.90),
    ],
}

def infer_behavior(stage_name: str) -> dict[str, Any]:
    """
    Infer the most likely action_behavior for a given stage name.

    Returns:
        {
            "suggested_behavior": str,
            "confidence": float (0-1),
            "alternatives": [{"behavior": str, "confidence": float}],
            "method": "keyword" | "llm",
        }
    """
    if not stage_name or not stage_name.strip():
        return {
            "suggested_behavior": "passive",
            "confidence": 0.5,
            "alternatives": [],
            "method": "keyword",
        }

    name_lower = stage_name.lower().strip()
    matches: list[dict[str, Any]] = []

    for behavior, keywords in BEHAVIOR_KEYWORDS.items():
        best_score = 0.0
        for keyword, base_score in keywords:
            if keyword in name_lower:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, name_lower):
                    score = base_score
                else:
                    score = base_score * 0.9
                best_score = max(best_score, score)

        if best_score > 0:
            matches.append({"behavior": behavior, "confidence": round(best_score, 2)})

    matches.sort(key=lambda x: x["confidence"], reverse=True)

    if not matches:
        return {
            "suggested_behavior": "passive",
            "confidence": 0.5,
            "alternatives": [],
            "method": "keyword",
        }

    best = matches[0]
    alternatives = matches[1:4]

    return {
        "suggested_behavior": best["behavior"],
        "confidence": best["confidence"],
        "alternatives": alternatives,
        "method": "keyword",
    }


VALID_BEHAVIORS = [
    "screening", "scheduling", "evaluation", "verification",
    "offer", "intake", "conclusion_hired", "conclusion_rejected",
    "conclusion_declined", "passive"
]

async def infer_behavior_llm(stage_name: str, description: str | None = None) -> dict[str, Any]:
    """
    Infer action_behavior using LLM for stage names that keywords can't classify well.
    Returns same structure as infer_behavior but with method='llm'.
    """
    if not settings.ENABLE_LLM_INFER_BEHAVIOR:
        return {"suggested_behavior": "passive", "confidence": 0.5, "alternatives": [], "method": "keyword_fallback"}
    
    if not is_llm_available():
        return {"suggested_behavior": "passive", "confidence": 0.5, "alternatives": [], "method": "keyword_fallback"}
    
    try:
        prompt = f"""Classifique a etapa de recrutamento abaixo em uma das categorias.

NOME DA ETAPA: "{stage_name}"
{f'DESCRIÇÃO: "{description}"' if description else ''}

CATEGORIAS POSSÍVEIS:
- screening: Triagem inicial, pré-seleção, filtro de candidatos
- scheduling: Entrevistas, reuniões, dinâmicas, agendamentos
- evaluation: Testes técnicos, avaliações, cases, provas, desafios
- verification: Verificação de referências, documentos, background check
- offer: Proposta salarial, negociação, contrato
- intake: Entrada no funil, sourcing, captação, candidatura
- conclusion_hired: Contratação, admissão, onboarding
- conclusion_rejected: Reprovação, rejeição, eliminação
- conclusion_declined: Desistência do candidato, recusa de proposta
- passive: Etapa passiva sem ação automática (espera, standby, banco de talentos)

Responda APENAS com JSON:
{{
  "suggested_behavior": "categoria_escolhida",
  "confidence": 0.0 a 1.0,
  "reasoning": "explicação breve em português",
  "alternatives": [{{"behavior": "outra_categoria", "confidence": 0.0 a 1.0}}]
}}"""
        
        response_text = await llm_complete(
            prompt=prompt,
            max_tokens=300,
            temperature=0.1,
        )
        
        if not response_text:
            logger.warning("[INFER-LLM] Empty response")
            return _keyword_fallback(stage_name)
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            logger.warning("[INFER-LLM] No JSON in response")
            return _keyword_fallback(stage_name)
        
        result = json.loads(json_match.group())
        
        if result.get("suggested_behavior") not in VALID_BEHAVIORS:
            logger.warning(f"[INFER-LLM] Invalid behavior: {result.get('suggested_behavior')}")
            return _keyword_fallback(stage_name)
        
        result["method"] = "llm"
        
        alts = result.get("alternatives", [])
        result["alternatives"] = [
            a for a in alts 
            if isinstance(a, dict) and a.get("behavior") in VALID_BEHAVIORS
        ][:3]
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[INFER-LLM] Classified '{stage_name}' as {result['suggested_behavior']} (confidence: {result['confidence']})")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"[INFER-LLM] JSON parse error: {e}")
        return _keyword_fallback(stage_name)
    except Exception as e:
        logger.error(f"[INFER-LLM] Error: {e}", exc_info=True)
        return _keyword_fallback(stage_name)


def _keyword_fallback(stage_name: str) -> dict[str, Any]:
    """Fall back to keyword-based inference."""
    result = infer_behavior(stage_name)
    result["method"] = "keyword_fallback"
    return result


async def infer_behavior_auto(stage_name: str, description: str | None = None) -> dict[str, Any]:
    """
    Auto mode: try keywords first, escalate to LLM if confidence is low.
    """
    keyword_result = infer_behavior(stage_name)
    
    if keyword_result["confidence"] >= 0.7:
        return keyword_result
    
    logger.info(f"[INFER-AUTO] Keyword confidence {keyword_result['confidence']} < 0.7, escalating to LLM")
    llm_result = await infer_behavior_llm(stage_name, description)
    
    if llm_result.get("method") == "llm" and llm_result.get("confidence", 0) > keyword_result["confidence"]:
        return llm_result
    
    return keyword_result
