"""
Suggestion Interaction Service for processing chat commands related to suggestions.

Handles detection and processing of user interactions with LIA's suggestions
during the job creation wizard, including:
- Accepting suggestions
- Rejecting suggestions
- Replacing skills with alternatives
- Adjusting requirement levels (required vs nice-to-have)

Uses regex patterns for fast detection (no LLM calls).
"""
import logging
import re
from difflib import SequenceMatcher
from typing import Any

from app.schemas.job_description import RequirementLevel
from app.schemas.suggestion_interaction import (
    DetectedInteraction,
    SuggestionInteractionType,
)
from app.shared.services.skills_catalog_service import skills_catalog_service

logger = logging.getLogger(__name__)


ACCEPT_PATTERN = re.compile(
    r"(aceito?|pode adicionar|sim[,\s]|quero)\s+(?:a?\s*sugestão\s+de\s+)?([\w\s]+?)(?:\s*,|\s*$|\s+(?:como|é|e\s|também))",
    re.IGNORECASE
)

REJECT_PATTERN = re.compile(
    r"(não preciso|remov[ea]|tir[ae]|não quero)\s+(?:de\s+)?([\w\s]+?)(?:\s*,|\s*$|\s+(?:como|é|e\s|também))",
    re.IGNORECASE
)

REPLACE_PATTERN = re.compile(
    r"(troque?|substitua?|prefiro)\s+([\w\s]+?)\s+(?:por|ao invés de|em vez de)\s+([\w\s]+?)(?:\s*,|\s*$|\s+(?:como|é))",
    re.IGNORECASE
)

ADJUST_LEVEL_PATTERN = re.compile(
    r"([\w\s]+?)\s+(?:como|é)\s+(obrigatório|diferencial|nice.?to.?have)",
    re.IGNORECASE
)

CLARIFY_PATTERN = re.compile(
    r"(por que|porque|de onde|explica|justifica|qual o motivo)\s+(?:você\s+)?suger[ei](?:u|mos)?\s+(?:a?\s*)?([\w\s]+?)(?:\s*\?|\s*$|\s*,)",
    re.IGNORECASE
)


LEVEL_MAPPING: dict[str, RequirementLevel] = {
    "obrigatório": RequirementLevel.REQUIRED,
    "obrigatorio": RequirementLevel.REQUIRED,
    "required": RequirementLevel.REQUIRED,
    "diferencial": RequirementLevel.NICE_TO_HAVE,
    "nice-to-have": RequirementLevel.NICE_TO_HAVE,
    "nicetoehave": RequirementLevel.NICE_TO_HAVE,
    "nice_to_have": RequirementLevel.NICE_TO_HAVE,
}


class SuggestionInteractionService:
    """
    Service for detecting and processing suggestion interactions from chat messages.
    
    Uses regex patterns for fast detection of user intent regarding
    accepting, rejecting, replacing, or adjusting suggestions.
    """
    
    FUZZY_MATCH_THRESHOLD = 0.7
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.skills_catalog = skills_catalog_service
    
    def detect_interactions(
        self,
        message: str,
        current_suggestions: list[str]
    ) -> list[DetectedInteraction]:
        """
        Detect all suggestion interactions in a user message.
        
        Args:
            message: The user's message text
            current_suggestions: List of currently active suggestion names
            
        Returns:
            List of detected interactions with their details
        """
        if not message or not message.strip():
            return []
        
        interactions = self._detect_via_regex(message)
        
        validated_interactions = self._validate_targets(
            interactions, 
            current_suggestions
        )
        
        return validated_interactions
    
    def _detect_via_regex(self, message: str) -> list[DetectedInteraction]:
        """
        Fast path detection using regex patterns.
        
        Args:
            message: The user's message text
            
        Returns:
            List of detected interactions (may need validation)
        """
        interactions: list[DetectedInteraction] = []
        message.lower()
        
        for match in ACCEPT_PATTERN.finditer(message):
            match.group(1)
            target_skill = match.group(2).strip()
            
            interactions.append(DetectedInteraction(
                interaction_type=SuggestionInteractionType.ACCEPT,
                target_skill=target_skill,
                replacement_skill=None,
                new_level=None,
                confidence=0.85,
                original_text=match.group(0)
            ))
            self.logger.debug(f"Detected ACCEPT: {target_skill}")
        
        for match in REJECT_PATTERN.finditer(message):
            match.group(1)
            target_skill = match.group(2).strip()
            
            interactions.append(DetectedInteraction(
                interaction_type=SuggestionInteractionType.REJECT,
                target_skill=target_skill,
                replacement_skill=None,
                new_level=None,
                confidence=0.85,
                original_text=match.group(0)
            ))
            self.logger.debug(f"Detected REJECT: {target_skill}")
        
        for match in REPLACE_PATTERN.finditer(message):
            match.group(1)
            target_skill = match.group(2).strip()
            replacement_skill = match.group(3).strip()
            
            interactions.append(DetectedInteraction(
                interaction_type=SuggestionInteractionType.REPLACE,
                target_skill=target_skill,
                replacement_skill=replacement_skill,
                new_level=None,
                confidence=0.80,
                original_text=match.group(0)
            ))
            self.logger.debug(f"Detected REPLACE: {target_skill} -> {replacement_skill}")
        
        for match in ADJUST_LEVEL_PATTERN.finditer(message):
            target_skill = match.group(1).strip()
            level_text = match.group(2).lower().replace("-", "").replace("_", "")
            
            new_level = self._parse_level(level_text)
            
            if new_level:
                interactions.append(DetectedInteraction(
                    interaction_type=SuggestionInteractionType.ADJUST_LEVEL,
                    target_skill=target_skill,
                    replacement_skill=None,
                    new_level=new_level,
                    confidence=0.90,
                    original_text=match.group(0)
                ))
                self.logger.debug(f"Detected ADJUST_LEVEL: {target_skill} -> {new_level}")
        
        for match in CLARIFY_PATTERN.finditer(message):
            target_skill = match.group(2).strip()
            
            interactions.append(DetectedInteraction(
                interaction_type=SuggestionInteractionType.CLARIFY,
                target_skill=target_skill,
                replacement_skill=None,
                new_level=None,
                confidence=0.85,
                original_text=match.group(0)
            ))
            self.logger.debug(f"Detected CLARIFY: {target_skill}")
        
        return interactions
    
    def _parse_level(self, level_text: str) -> RequirementLevel | None:
        """
        Parse a level text string into a RequirementLevel enum.
        
        Args:
            level_text: The level text (e.g., "obrigatório", "diferencial")
            
        Returns:
            RequirementLevel or None if not recognized
        """
        normalized = level_text.lower().strip().replace("-", "").replace("_", "").replace(" ", "")
        
        if normalized in ("obrigatorio", "obrigatório", "required"):
            return RequirementLevel.REQUIRED
        elif normalized in ("diferencial", "nicetoehave", "nicetohaev"):
            return RequirementLevel.NICE_TO_HAVE
        
        return LEVEL_MAPPING.get(normalized)
    
    def _validate_targets(
        self,
        interactions: list[DetectedInteraction],
        current_suggestions: list[str]
    ) -> list[DetectedInteraction]:
        """
        Validate that interaction targets match current suggestions.
        
        Applies fuzzy matching to find the best match for each target.
        
        Args:
            interactions: List of detected interactions
            current_suggestions: List of current suggestion names
            
        Returns:
            Validated interactions with corrected target names
        """
        if not current_suggestions:
            return interactions
        
        validated: list[DetectedInteraction] = []
        suggestions_lower = [s.lower() for s in current_suggestions]
        
        for interaction in interactions:
            target = interaction.target_skill.lower()
            
            best_match, score = self._find_best_match(target, current_suggestions)
            
            if score >= self.FUZZY_MATCH_THRESHOLD:
                validated_interaction = DetectedInteraction(
                    interaction_type=interaction.interaction_type,
                    target_skill=best_match,
                    replacement_skill=interaction.replacement_skill,
                    new_level=interaction.new_level,
                    confidence=interaction.confidence * score,
                    original_text=interaction.original_text
                )
                validated.append(validated_interaction)
            else:
                if target in suggestions_lower:
                    idx = suggestions_lower.index(target)
                    validated_interaction = DetectedInteraction(
                        interaction_type=interaction.interaction_type,
                        target_skill=current_suggestions[idx],
                        replacement_skill=interaction.replacement_skill,
                        new_level=interaction.new_level,
                        confidence=interaction.confidence,
                        original_text=interaction.original_text
                    )
                    validated.append(validated_interaction)
                else:
                    validated.append(interaction)
                    self.logger.warning(
                        f"Could not find match for '{interaction.target_skill}' "
                        f"in suggestions: {current_suggestions}"
                    )
        
        return validated
    
    def _find_best_match(
        self,
        target: str,
        suggestions: list[str]
    ) -> tuple[str, float]:
        """
        Find the best matching suggestion for a target skill name.
        
        Args:
            target: The target skill name to match
            suggestions: List of available suggestions
            
        Returns:
            Tuple of (best_match, score)
        """
        best_match = target
        best_score = 0.0
        
        target_lower = target.lower()
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            if target_lower == suggestion_lower:
                return suggestion, 1.0
            
            if target_lower in suggestion_lower or suggestion_lower in target_lower:
                score = 0.9
                if score > best_score:
                    best_score = score
                    best_match = suggestion
                continue
            
            score = SequenceMatcher(None, target_lower, suggestion_lower).ratio()
            if score > best_score:
                best_score = score
                best_match = suggestion
        
        return best_match, best_score
    
    def apply_interactions(
        self,
        interactions: list[DetectedInteraction],
        current_suggestions: list[str] | list[Any]
    ) -> list[str]:
        """
        Apply detected interactions to the current list of suggestions.
        
        Accepts both List[str] and List[SuggestedItem] (or any object with 'value' attribute).
        
        Args:
            interactions: List of interactions to apply
            current_suggestions: Current suggestion items (strings or objects with 'value')
            
        Returns:
            Updated list of suggestions as strings after applying interactions
        """
        suggestions: list[str] = []
        for s in current_suggestions:
            if isinstance(s, str):
                suggestions.append(s)
            elif hasattr(s, 'value'):
                suggestions.append(s.value)
            else:
                suggestions.append(str(s))
        
        result = list(suggestions)
        
        for interaction in interactions:
            target_lower = interaction.target_skill.lower()
            
            if interaction.interaction_type == SuggestionInteractionType.REJECT:
                result = [
                    s for s in result 
                    if s.lower() != target_lower
                ]
                self.logger.info(f"Removed suggestion: {interaction.target_skill}")
            
            elif interaction.interaction_type == SuggestionInteractionType.REPLACE:
                if interaction.replacement_skill:
                    replacement_valid, alternatives = self._validate_replacement_skill(
                        interaction.replacement_skill
                    )
                    
                    for i, s in enumerate(result):
                        if s.lower() == target_lower:
                            if replacement_valid:
                                result[i] = interaction.replacement_skill
                                self.logger.info(
                                    f"Replaced {interaction.target_skill} with "
                                    f"{interaction.replacement_skill}"
                                )
                            else:
                                self.logger.warning(
                                    f"Replacement skill '{interaction.replacement_skill}' "
                                    f"not found in catalog. Alternatives: {alternatives}"
                                )
                            break
        
        return result
    
    def _validate_replacement_skill(
        self,
        skill_name: str
    ) -> tuple[bool, list[str]]:
        """
        Validate if a replacement skill exists in the catalog.
        
        Args:
            skill_name: Name of the skill to validate
            
        Returns:
            Tuple of (is_valid, alternative_suggestions)
        """
        search_results = self.skills_catalog.search_skills(skill_name, limit=5)
        
        for result in search_results:
            if result["skill"].lower() == skill_name.lower():
                return True, []
            if result["score"] >= 0.95:
                return True, []
        
        alternatives = [r["skill"] for r in search_results[:3]]
        return False, alternatives
    
    def generate_confirmation_message(
        self,
        interactions: list[DetectedInteraction]
    ) -> str:
        """
        Generate a confirmation message in Portuguese for the applied interactions.
        
        Args:
            interactions: List of interactions that were applied
            
        Returns:
            Confirmation message string from LIA
        """
        if not interactions:
            return "Entendi! Não detectei alterações específicas nas sugestões. Como posso ajudar?"
        
        messages: list[str] = []
        
        accepts = [i for i in interactions if i.interaction_type == SuggestionInteractionType.ACCEPT]
        rejects = [i for i in interactions if i.interaction_type == SuggestionInteractionType.REJECT]
        replaces = [i for i in interactions if i.interaction_type == SuggestionInteractionType.REPLACE]
        adjusts = [i for i in interactions if i.interaction_type == SuggestionInteractionType.ADJUST_LEVEL]
        clarifies = [i for i in interactions if i.interaction_type == SuggestionInteractionType.CLARIFY]
        
        if accepts:
            skills = [i.target_skill for i in accepts]
            if len(skills) == 1:
                messages.append(f"✅ Adicionei **{skills[0]}** às competências da vaga.")
            else:
                skills_text = ", ".join(skills[:-1]) + f" e {skills[-1]}"
                messages.append(f"✅ Adicionei **{skills_text}** às competências da vaga.")
        
        if rejects:
            skills = [i.target_skill for i in rejects]
            if len(skills) == 1:
                messages.append(f"❌ Removi **{skills[0]}** das sugestões.")
            else:
                skills_text = ", ".join(skills[:-1]) + f" e {skills[-1]}"
                messages.append(f"❌ Removi **{skills_text}** das sugestões.")
        
        if replaces:
            for r in replaces:
                messages.append(
                    f"🔄 Substituí **{r.target_skill}** por **{r.replacement_skill}**."
                )
        
        if adjusts:
            for a in adjusts:
                level_text = "obrigatório" if a.new_level == RequirementLevel.REQUIRED else "diferencial"
                messages.append(
                    f"📊 Ajustei **{a.target_skill}** como **{level_text}**."
                )
        
        if clarifies:
            for c in clarifies:
                messages.append(
                    f"ℹ️ **{c.target_skill}**: Sugerido pelo catálogo de skills com base no cargo e senioridade."
                )
        
        response = "\n".join(messages)
        
        if len(interactions) > 1:
            response += "\n\nDeseja fazer mais alguma alteração?"
        else:
            response += " Posso ajudar com mais alguma coisa?"
        
        return response
    
    def get_suggestion_alternatives(
        self,
        skill_name: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get alternative skill suggestions from the catalog.
        
        Args:
            skill_name: The skill to find alternatives for
            limit: Maximum number of alternatives to return
            
        Returns:
            List of alternative skill suggestions with metadata
        """
        return self.skills_catalog.search_skills(skill_name, limit=limit)
    
    def suggest_skills_for_replacement(
        self,
        current_skill: str,
        role: str | None = None,
        area: str | None = None
    ) -> list[str]:
        """
        Suggest replacement skills based on context.
        
        Args:
            current_skill: The skill being replaced
            role: Optional job role context
            area: Optional skill area filter
            
        Returns:
            List of suggested replacement skill names
        """
        search_results = self.skills_catalog.search_skills(
            current_skill,
            area=area,
            limit=10
        )
        
        suggestions = [
            r["skill"] for r in search_results 
            if r["skill"].lower() != current_skill.lower()
        ]
        
        return suggestions[:5]


suggestion_interaction_service = SuggestionInteractionService()
