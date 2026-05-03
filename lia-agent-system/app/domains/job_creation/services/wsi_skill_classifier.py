"""WsiSkillClassifier - Sprint B Phase 3.

Classifica pergunta gerada (texto livre) em uma skill da taxonomia.

Strategy: zero-shot LLM classification com fallback heuristic.
- Primary: prompt LLM com lista de skill_ids + descricao + retorna 1 skill_id
- Fallback: keyword matching simples se LLM falha

Multi-tenancy: nao aplica (taxonomia eh global).
LGPD: pergunta pode conter contexto da vaga - logs com hash, nao texto direto.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.domains.job_creation.services.wsi_skill_taxonomy import (
    all_skill_ids,
    find_skill,
    load_taxonomy,
)

logger = logging.getLogger(__name__)


# Skill default quando classificacao falha (parent communication, generico)
DEFAULT_FALLBACK_SKILL = "ambiguity_tolerance"  # comum em qualquer cargo


class WsiSkillClassifier:
    """Classifica pergunta WSI em skill da taxonomia."""

    def __init__(self, llm: Any = None):
        """llm: LangChain BaseChatModel ou compativel. Pode ser None pra fallback heuristic only."""
        self._llm = llm

    def _build_classification_prompt(self, question_text: str) -> str:
        tax = load_taxonomy()
        skill_lines: list[str] = []
        for parent_id, parent in tax.parents.items():
            for skill in parent.skills:
                skill_lines.append(
                    f"- {skill.id}: {skill.description}",
                )
        skills_block = "\n".join(skill_lines)
        return (
            "Voce eh um classificador de perguntas comportamentais. "
            "Dado uma pergunta de entrevista, escolha a UNICA skill que ela "
            "melhor testa, dentre a lista abaixo. "
            "Retorne APENAS o id da skill (snake_case), sem explicacao.\n\n"
            f"PERGUNTA:\n{question_text}\n\n"
            f"SKILLS DISPONIVEIS:\n{skills_block}\n\n"
            "RESPOSTA (so o id):"
        )

    def _heuristic_fallback(self, question_text: str) -> str:
        """Keyword-based fallback quando LLM nao disponivel ou falha.

        Looks for keyword stems in question text. Returns DEFAULT_FALLBACK_SKILL
        se nada bate.
        """
        text = question_text.lower()
        # Heuristics simples - cobre os casos mais comuns
        keyword_map = [
            (r"\bprazo|deadline|urgente\b", "delivery_under_deadline_pressure"),
            (r"\bprioriz|escolher entre\b", "prioritization_with_competing_demands"),
            (r"\bfeedback|critica\b", "feedback_acceptance"),
            (r"\bconflito|desacordo\b", "conflict_resolution"),
            (r"\bdado|metrica|numero\b", "data_driven_decision_making"),
            (r"\baprend|nova tecnologia|stack\b", "technical_self_learning"),
            (r"\bcliente|stakeholder\b", "stakeholder_management"),
            (r"\bambig|sem requisito|incerteza\b", "ambiguity_tolerance"),
            (r"\bcausa raiz|investigar\b", "root_cause_analysis"),
            (r"\bequipe|time|colega\b", "cross_team_alignment"),
            (r"\bmedico|paciente|diagnostico clinico\b", "clinical_diagnostic_reasoning"),
            (r"\bcurriculo|curso|aluno|aula\b", "instructional_design"),
        ]
        for pattern, skill_id in keyword_map:
            if re.search(pattern, text):
                if find_skill(skill_id) is not None:
                    return skill_id
        return DEFAULT_FALLBACK_SKILL

    def _normalize_llm_response(self, response_text: str) -> str | None:
        """Extracts skill_id from LLM response. Returns None se nao bate."""
        # Strip whitespace, quotes, common surroundings
        text = response_text.strip().strip('"').strip("'").strip("`")
        # Try direct match
        if find_skill(text) is not None:
            return text
        # Try to find a skill_id pattern in text
        valid_ids = set(all_skill_ids())
        for match in re.findall(r"[a-z_]+", text):
            if match in valid_ids:
                return match
        return None

    def classify(self, question_text: str) -> dict[str, Any]:
        """Classifica pergunta em skill_id. ALWAYS returns a valid skill_id.

        Returns: {skill_id, source} onde source in {llm, heuristic, default}.
        """
        if not question_text or not question_text.strip():
            return {"skill_id": DEFAULT_FALLBACK_SKILL, "source": "default"}

        # Try LLM first if available
        if self._llm is not None:
            try:
                prompt = self._build_classification_prompt(question_text)
                response = self._llm.invoke(prompt)
                response_text = (
                    response.content
                    if hasattr(response, "content")
                    else str(response)
                )
                skill_id = self._normalize_llm_response(response_text)
                if skill_id is not None:
                    return {"skill_id": skill_id, "source": "llm"}
                logger.debug(
                    "[Classifier] LLM response not a valid skill_id: %s",
                    response_text[:50],
                )
            except Exception as exc:
                logger.warning(
                    "[Classifier] LLM call failed (fallback heuristic): %s",
                    str(exc)[:100],
                )

        # Heuristic fallback
        skill_id = self._heuristic_fallback(question_text)
        return {"skill_id": skill_id, "source": "heuristic"}
