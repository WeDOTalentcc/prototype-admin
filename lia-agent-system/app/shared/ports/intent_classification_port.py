"""Port for intent classification (UC-P3-16).

Decouples wizard_step_service (and any other caller) from the concrete
intent_classifier and enhanced_intent_classifier implementations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IIntentClassificationPort(ABC):
    """Abstract port for classifying user-message intent.

    Implementations may delegate to IntentClassifierService,
    EnhancedIntentClassifierService, or a test double.
    """

    @abstractmethod
    async def classify(
        self,
        user_input: str,
        stage_context: str | None = None,
        use_llm: bool = True,
    ) -> Any:
        """Classify message intent.

        Returns a ClassificationResult-compatible object with at minimum:
        - .intent_type  — the classified intent
        - .confidence   — float 0-1
        - .extracted_entities — dict
        - .original_text — str
        """
        ...

    @abstractmethod
    async def get_available_intents(self) -> list[str]:
        """Return list of intent names this classifier supports."""
        ...


class IntentClassifierAdapter(IIntentClassificationPort):
    """Adapter: wraps IntentClassifierService (standard) behind the port."""

    async def classify(
        self,
        user_input: str,
        stage_context: str | None = None,
        use_llm: bool = True,
    ) -> Any:
        from app.domains.ai.services.intent_classifier import intent_classifier_service

        return await intent_classifier_service.classify(
            user_input=user_input,
            stage_context=stage_context,
            use_llm=use_llm,
        )

    async def get_available_intents(self) -> list[str]:
        from app.domains.ai.services.intent_classifier import IntentType

        return [t.value for t in IntentType]


class EnhancedIntentClassifierAdapter(IIntentClassificationPort):
    """Adapter: wraps EnhancedIntentClassifierService behind the port.

    The enhanced classifier has a richer signature (stage + filled_fields).
    This adapter exposes the common port interface; callers that need the
    full enhanced API should import the service directly.
    """

    async def classify(
        self,
        user_input: str,
        stage_context: str | None = None,
        use_llm: bool = True,
    ) -> Any:
        from app.shared.services.enhanced_intent_classifier import (
            enhanced_intent_classifier,
        )

        # enhanced_intent_classifier.classify has extra kwargs; stage_context maps
        # to the `stage` parameter with a safe fallback.
        return await enhanced_intent_classifier.classify(
            user_input=user_input,
            stage=stage_context,
        )

    async def get_available_intents(self) -> list[str]:
        from app.shared.services.enhanced_intent_classifier import EnhancedIntentType

        return [t.value for t in EnhancedIntentType]
