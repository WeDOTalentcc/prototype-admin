"""
Enhanced Base Agent - Base agent with built-in robustness features.

Provides:
- Automatic error handling wrapper
- Input validation
- Context management
- Cancellation detection
- Telemetry/logging
"""
from typing import Dict, Any, Optional, List
from abc import abstractmethod
import logging
import time

from app.agents.base_agent import BaseAgent, AgentType, AgentResponse
from app.shared.robustness.error_handling import (
    handle_agent_errors,
    AgentError,
    AgentErrorCode,
    create_user_friendly_error
)
from app.shared.robustness.intent_schemas import (
    IntentSchema,
    get_agent_intents,
    EntityRequirement
)
from app.shared.robustness.input_validation import (
    sanitize_text,
    detect_language,
    SupportedLanguage
)
from app.shared.robustness.context_management import (
    CancellationHandler,
    ContextManager
)
from app.shared.robustness.defensive_prompts import (
    get_clarification_message,
    get_out_of_scope_response,
    get_defensive_prompt_section
)

logger = logging.getLogger(__name__)


class EnhancedBaseAgent(BaseAgent):
    """
    Enhanced base agent with built-in robustness features.
    
    Features:
    - Dynamic can_handle() based on intent schemas
    - Automatic error handling
    - Input validation and sanitization
    - Cancellation detection
    - Telemetry/metrics
    """
    
    def __init__(self):
        super().__init__()
        self._intent_schemas: List[IntentSchema] = []
        self._load_intent_schemas()
        self._metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time_ms": 0,
            "cancellations": 0
        }
    
    def _load_intent_schemas(self) -> None:
        """Load intent schemas for this agent type."""
        self._intent_schemas = get_agent_intents(self.agent_type)
    
    def get_intent_schemas(self) -> List[IntentSchema]:
        """Get all intent schemas for this agent."""
        return self._intent_schemas
    
    def can_handle(self, intent: str, entities: Dict[str, Any]) -> float:
        """
        Dynamic confidence scoring based on intent schemas.
        
        Analyzes:
        - Intent match
        - Entity presence and quality
        - Context requirements
        """
        for schema in self._intent_schemas:
            if schema.intent == intent:
                confidence = schema.calculate_confidence(
                    entities=entities,
                    context={},
                    message=""
                )
                logger.debug(f"{self.name}: Intent '{intent}' confidence = {confidence:.2f}")
                return confidence
        
        for schema in self._intent_schemas:
            keyword_matches = sum(
                1 for kw in schema.keywords 
                if kw.lower() in intent.lower()
            )
            if keyword_matches > 0:
                base_confidence = min(0.6, 0.3 + keyword_matches * 0.1)
                logger.debug(f"{self.name}: Keyword match for '{intent}' confidence = {base_confidence:.2f}")
                return base_confidence
        
        return 0.0
    
    def get_missing_entities(self, intent: str, entities: Dict[str, Any]) -> List[EntityRequirement]:
        """Get missing required/recommended entities for an intent."""
        for schema in self._intent_schemas:
            if schema.intent == intent:
                return schema.get_missing_entities(entities)
        return []
    
    def validate_intent(self, intent: str, entities: Dict[str, Any]) -> bool:
        """Check if all required entities are present for an intent."""
        for schema in self._intent_schemas:
            if schema.intent == intent:
                return schema.is_valid(entities)
        return True
    
    async def process_with_robustness(
        self,
        intent: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """
        Process with full robustness features.
        
        Includes:
        - Input sanitization
        - Cancellation detection
        - Validation
        - Error handling
        - Metrics
        """
        start_time = time.time()
        self._metrics["total_requests"] += 1
        
        try:
            entities = self._sanitize_entities(entities)
            
            last_message = context.get("last_message", "")
            if last_message and CancellationHandler.is_cancellation_request(last_message):
                self._metrics["cancellations"] += 1
                return AgentResponse(
                    success=True,
                    message=CancellationHandler.get_cancellation_response(),
                    data={"cancelled": True}
                )
            
            missing = self.get_missing_entities(intent, entities)
            required_missing = [m for m in missing if m.importance.value == "required"]
            
            if required_missing:
                missing_names = [m.description or m.entity_type.value for m in required_missing]
                clarification = get_clarification_message(
                    [m.entity_type.value for m in required_missing]
                )
                return AgentResponse(
                    success=False,
                    message=clarification,
                    data={"missing_entities": missing_names},
                    requires_user_input=True
                )
            
            response = await self.process(intent, entities, context)
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._update_metrics(success=response.success, elapsed_ms=elapsed_ms)
            
            return response
            
        except AgentError as e:
            self._metrics["failed_requests"] += 1
            logger.warning(f"{self.name}: AgentError - {e.code.value}: {e.user_message}")
            return AgentResponse(
                success=False,
                message=e.user_message,
                data=e.to_response().to_dict()
            )
        except Exception as e:
            self._metrics["failed_requests"] += 1
            logger.error(f"{self.name}: Unexpected error - {str(e)}")
            error = create_user_friendly_error(
                AgentErrorCode.INTERNAL_ERROR,
                technical_message=str(e)
            )
            return AgentResponse(
                success=False,
                message=error.user_message,
                data=error.to_dict()
            )
    
    def _sanitize_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all string entities."""
        sanitized = {}
        for key, value in entities.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_text(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_text(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    def _update_metrics(self, success: bool, elapsed_ms: float) -> None:
        """Update agent metrics."""
        if success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1
        
        total = self._metrics["total_requests"]
        current_avg = self._metrics["avg_response_time_ms"]
        self._metrics["avg_response_time_ms"] = (
            (current_avg * (total - 1) + elapsed_ms) / total
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return self._metrics.copy()
    
    def get_defensive_prompt(self) -> str:
        """Get defensive prompt section for this agent."""
        return get_defensive_prompt_section(self.agent_type.value)
    
    def create_clarification_response(
        self,
        missing_items: List[str],
        context_message: str = ""
    ) -> AgentResponse:
        """Create a response asking for clarification."""
        message = get_clarification_message(missing_items)
        if context_message:
            message = f"{context_message}\n\n{message}"
        
        return AgentResponse(
            success=False,
            message=message,
            requires_user_input=True,
            data={"needs_clarification": True, "missing": missing_items}
        )
    
    def create_out_of_scope_response(self, category: str = "general") -> AgentResponse:
        """Create an out-of-scope response."""
        return AgentResponse(
            success=False,
            message=get_out_of_scope_response(category),
            data={"out_of_scope": True, "category": category}
        )


class RobustAgentMixin:
    """
    Mixin to add robustness features to existing agents.
    
    Usage:
        class MyAgent(RobustAgentMixin, BaseAgent):
            ...
    """
    
    _intent_schemas: List[IntentSchema] = []
    
    def init_robustness(self):
        """Initialize robustness features. Call in __init__."""
        from app.shared.robustness.intent_schemas import get_agent_intents
        self._intent_schemas = get_agent_intents(self.agent_type)
    
    def can_handle_robust(self, intent: str, entities: Dict[str, Any]) -> float:
        """Enhanced can_handle with schema-based scoring."""
        for schema in self._intent_schemas:
            if schema.intent == intent:
                return schema.calculate_confidence(entities, {}, "")
        return 0.0
    
    def check_cancellation(self, message: str) -> Optional[AgentResponse]:
        """Check for and handle cancellation requests."""
        if CancellationHandler.is_cancellation_request(message):
            return AgentResponse(
                success=True,
                message=CancellationHandler.get_cancellation_response(),
                data={"cancelled": True}
            )
        return None
    
    def sanitize_input(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input entities."""
        sanitized = {}
        for key, value in entities.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_text(value)
            else:
                sanitized[key] = value
        return sanitized
