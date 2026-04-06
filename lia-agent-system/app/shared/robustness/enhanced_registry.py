"""
Enhanced Agent Registry - Registry with improved routing and fallback chains.

Provides:
- Dynamic confidence-based routing
- Fallback chains with reason logging
- Telemetry for misroutes
- Intent schema integration
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agents.base_agent import AgentType, BaseAgent
from app.shared.robustness.intent_schemas import (
    ALL_INTENT_SCHEMAS,
    IntentSchema,
    get_intent_schema,
)

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Represents a routing decision with metadata."""
    agent: BaseAgent | None
    agent_type: AgentType | None
    confidence: float
    intent: str
    routing_method: str
    fallback_used: bool = False
    fallback_reason: str = ""
    alternatives: list[tuple[AgentType, float]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_type": self.agent_type.value if self.agent_type else None,
            "confidence": self.confidence,
            "intent": self.intent,
            "routing_method": self.routing_method,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "alternatives": [(at.value, conf) for at, conf in self.alternatives],
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RoutingTelemetry:
    """Telemetry data for routing decisions."""
    total_routes: int = 0
    direct_matches: int = 0
    confidence_matches: int = 0
    fallback_routes: int = 0
    failed_routes: int = 0
    misroutes_detected: int = 0
    avg_confidence: float = 0.0
    
    def record_route(self, decision: RoutingDecision) -> None:
        """Record a routing decision."""
        self.total_routes += 1
        
        if decision.routing_method == "direct_mapping":
            self.direct_matches += 1
        elif decision.routing_method == "confidence_scoring":
            self.confidence_matches += 1
        elif decision.fallback_used:
            self.fallback_routes += 1
        
        if decision.agent is None:
            self.failed_routes += 1
        
        self.avg_confidence = (
            (self.avg_confidence * (self.total_routes - 1) + decision.confidence) 
            / self.total_routes
        )
    
    def record_misroute(self) -> None:
        """Record a detected misroute."""
        self.misroutes_detected += 1
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_routes": self.total_routes,
            "direct_matches": self.direct_matches,
            "confidence_matches": self.confidence_matches,
            "fallback_routes": self.fallback_routes,
            "failed_routes": self.failed_routes,
            "misroutes_detected": self.misroutes_detected,
            "avg_confidence": round(self.avg_confidence, 3),
            "direct_match_rate": round(self.direct_matches / max(1, self.total_routes), 3),
            "fallback_rate": round(self.fallback_routes / max(1, self.total_routes), 3)
        }


FALLBACK_CHAINS: dict[AgentType, list[AgentType]] = {
    AgentType.JOB_PLANNER: [AgentType.RECRUITER_ASSISTANT],
    AgentType.SOURCING: [AgentType.CV_SCREENING, AgentType.RECRUITER_ASSISTANT],
    AgentType.CV_SCREENING: [AgentType.WSI_EVALUATOR, AgentType.RECRUITER_ASSISTANT],
    AgentType.INTERVIEWER: [AgentType.WSI_EVALUATOR, AgentType.SCHEDULING, AgentType.RECRUITER_ASSISTANT],
    AgentType.WSI_EVALUATOR: [AgentType.CV_SCREENING, AgentType.RECRUITER_ASSISTANT],
    AgentType.SCHEDULING: [AgentType.RECRUITER_ASSISTANT],
    AgentType.ANALYST_FEEDBACK: [AgentType.RECRUITER_ASSISTANT],
    AgentType.ATS_INTEGRATOR: [AgentType.RECRUITER_ASSISTANT],
    AgentType.TASK_PLANNER: [AgentType.RECRUITER_ASSISTANT],
    AgentType.RECRUITER_ASSISTANT: [],
}


class EnhancedAgentRegistry:
    """
    Enhanced registry with improved routing capabilities.
    
    Features:
    - Intent schema-based routing
    - Confidence scoring with entity analysis
    - Fallback chains with reason logging
    - Telemetry for monitoring
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: dict[AgentType, BaseAgent] = {}
            cls._instance._intent_mapping: dict[str, AgentType] = {}
            cls._instance._telemetry = RoutingTelemetry()
            cls._instance._initialize_intent_mapping()
        return cls._instance
    
    def _initialize_intent_mapping(self) -> None:
        """Initialize intent mapping from schemas."""
        for agent_type, schemas in ALL_INTENT_SCHEMAS.items():
            for schema in schemas:
                self._intent_mapping[schema.intent] = agent_type
    
    def register(self, agent: BaseAgent) -> None:
        """Register an agent."""
        self._agents[agent.agent_type] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_type.value})")
    
    def unregister(self, agent_type: AgentType) -> bool:
        """Unregister an agent."""
        if agent_type in self._agents:
            del self._agents[agent_type]
            return True
        return False
    
    def get_agent(self, agent_type: AgentType) -> BaseAgent | None:
        """Get an agent by type."""
        return self._agents.get(agent_type)
    
    def get_all_agents(self) -> list[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def route(
        self,
        intent: str,
        entities: dict[str, Any],
        context: dict[str, Any],
        message: str = ""
    ) -> RoutingDecision:
        """
        Route a request to the best agent.
        
        Routing priority:
        1. Direct intent mapping (highest confidence)
        2. Schema-based confidence scoring
        3. Keyword matching
        4. Fallback chain
        """
        if intent in self._intent_mapping:
            agent_type = self._intent_mapping[intent]
            agent = self._agents.get(agent_type)
            
            if agent:
                decision = RoutingDecision(
                    agent=agent,
                    agent_type=agent_type,
                    confidence=0.95,
                    intent=intent,
                    routing_method="direct_mapping"
                )
                self._telemetry.record_route(decision)
                return decision
        
        best_agent = None
        best_confidence = 0.0
        alternatives: list[tuple[AgentType, float]] = []
        
        for agent_type, agent in self._agents.items():
            confidence = agent.can_handle(intent, entities)
            
            if confidence > 0.3:
                alternatives.append((agent_type, confidence))
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent
        
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        if best_agent and best_confidence >= 0.5:
            decision = RoutingDecision(
                agent=best_agent,
                agent_type=best_agent.agent_type,
                confidence=best_confidence,
                intent=intent,
                routing_method="confidence_scoring",
                alternatives=alternatives[:3]
            )
            self._telemetry.record_route(decision)
            return decision
        
        return self._try_fallback_chain(intent, entities, context, alternatives)
    
    def _try_fallback_chain(
        self,
        intent: str,
        entities: dict[str, Any],
        context: dict[str, Any],
        alternatives: list[tuple[AgentType, float]]
    ) -> RoutingDecision:
        """Try fallback chain when primary routing fails."""
        if alternatives:
            primary_type = alternatives[0][0]
            fallback_chain = FALLBACK_CHAINS.get(primary_type, [])
            
            for fallback_type in fallback_chain:
                fallback_agent = self._agents.get(fallback_type)
                if fallback_agent:
                    decision = RoutingDecision(
                        agent=fallback_agent,
                        agent_type=fallback_type,
                        confidence=0.4,
                        intent=intent,
                        routing_method="fallback_chain",
                        fallback_used=True,
                        fallback_reason=f"Primary agent {primary_type.value} had low confidence",
                        alternatives=alternatives[:3]
                    )
                    self._telemetry.record_route(decision)
                    return decision
        
        assistant = self._agents.get(AgentType.RECRUITER_ASSISTANT)
        if assistant:
            decision = RoutingDecision(
                agent=assistant,
                agent_type=AgentType.RECRUITER_ASSISTANT,
                confidence=0.3,
                intent=intent,
                routing_method="default_fallback",
                fallback_used=True,
                fallback_reason="No suitable agent found, using assistant",
                alternatives=alternatives[:3]
            )
            self._telemetry.record_route(decision)
            return decision
        
        decision = RoutingDecision(
            agent=None,
            agent_type=None,
            confidence=0.0,
            intent=intent,
            routing_method="failed",
            fallback_used=True,
            fallback_reason="No agents available"
        )
        self._telemetry.record_route(decision)
        return decision
    
    def find_best_agent(
        self,
        intent: str,
        entities: dict[str, Any],
        context: dict[str, Any]
    ) -> tuple[BaseAgent | None, float]:
        """
        Legacy interface for find_best_agent.
        Returns tuple of (agent, confidence).
        """
        decision = self.route(intent, entities, context)
        return (decision.agent, decision.confidence)
    
    def report_misroute(
        self,
        intent: str,
        assigned_agent: AgentType,
        correct_agent: AgentType
    ) -> None:
        """Report a misroute for telemetry."""
        self._telemetry.record_misroute()
        logger.warning(
            f"Misroute detected: intent='{intent}' "
            f"assigned={assigned_agent.value} correct={correct_agent.value}"
        )
    
    def get_telemetry(self) -> dict[str, Any]:
        """Get routing telemetry data."""
        return self._telemetry.to_dict()
    
    def get_agent_for_intent(self, intent: str) -> BaseAgent | None:
        """Get agent directly from intent mapping."""
        agent_type = self._intent_mapping.get(intent)
        if agent_type:
            return self._agents.get(agent_type)
        return None
    
    def get_intent_schema(self, intent: str) -> IntentSchema | None:
        """Get the schema for an intent."""
        return get_intent_schema(intent)


enhanced_registry = EnhancedAgentRegistry()
