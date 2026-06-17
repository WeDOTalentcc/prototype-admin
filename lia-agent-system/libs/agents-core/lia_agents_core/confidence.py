"""
Confidence Scoring — nó de confiança para LangGraph StateGraphs.

Adiciona um nó de avaliação de confiança ao grafo que:
- Analisa a qualidade da resposta gerada pelo agente
- Determina se é necessário nova iteração ou se o resultado é aceitável
- Expõe o score para o AuditCallback e para métricas externas

Compatível com LangGraph 0.2.x e com o ReActState customizado.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# DESIGN DECISION UC-P2-33 2026-05-02: Heuristic confidence scoring accepted.
# compute_confidence uses rule-based thresholds: deterministic, under 1ms, no LLM cost.
# The CascadedRouter handles quality fallback via Tier 6 autonomous agent.
# If LLM-as-judge needed: wrap BARSEvaluator in app/shared/evaluation/bars_evaluator.py.



def compute_confidence(
    response: Optional[str],
    tool_calls_made: int = 0,
    error: Optional[str] = None,
    observations_count: int = 0,
) -> float:
    """
    Heurística de confiança baseada em características da execução.

    Retorna float [0.0, 1.0]:
    - 1.0: resposta longa com tools usadas e sem erros
    - 0.9: resposta com tools e sem erros
    - 0.7: resposta sem tools
    - 0.3: resposta curta ou sem conteúdo
    - 0.0: erro
    """
    if error:
        return 0.0

    if not response or not response.strip():
        return 0.1

    resp_len = len(response.strip())

    if tool_calls_made > 0 and observations_count > 0:
        if resp_len > 200:
            return 0.92
        return 0.85

    if tool_calls_made > 0:
        return 0.80

    if resp_len > 300:
        return 0.75
    if resp_len > 100:
        return 0.70
    return 0.50


class ConfidenceNode:
    """
    Nó LangGraph que adiciona score de confiança ao state.

    Uso no grafo:
        graph.add_node("score_confidence", ConfidenceNode(domain="pipeline"))
    """

    def __init__(self, domain: str = "unknown"):
        self.domain = domain

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula confiança e adiciona ao state."""
        response = state.get("final_response") or state.get("response", "")
        tool_calls = state.get("tool_calls_made", [])
        error = state.get("error")
        observations = state.get("observations", [])

        confidence = compute_confidence(
            response=response,
            tool_calls_made=len(tool_calls) if isinstance(tool_calls, list) else 0,
            error=error,
            observations_count=len(observations) if isinstance(observations, list) else 0,
        )

        logger.debug(
            "[ConfidenceNode] domain=%s confidence=%.2f tools=%s error=%s",
            self.domain, confidence,
            len(tool_calls) if isinstance(tool_calls, list) else 0,
            bool(error),
        )

        return {**state, "confidence": confidence}
