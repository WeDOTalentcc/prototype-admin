"""
Agent Interface - Standard contract for all domain agents.

Every domain agent (Wizard, Pipeline, Sourcing, etc.) must implement
this interface. This ensures:
1. Consistent input/output across domains
2. Any agent can be used as a tool by a future central orchestrator
3. Easy testing and mocking
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentAction(BaseModel):
    """Represents a single action the agent wants to perform."""

    action_type: str = Field(
        ...,
        description="Type of action to perform: update_field, call_tool, navigate, confirm, save_draft",
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action",
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Whether this action requires user confirmation before execution",
    )


class NavigationCommand(BaseModel):
    """Command to navigate between stages in a wizard or workflow."""

    target_stage: str = Field(
        ...,
        description="The stage to navigate to",
    )
    reason: str = Field(
        ...,
        description="Why the navigation is happening",
    )
    auto_navigate: bool = Field(
        default=False,
        description="Whether to navigate automatically without user confirmation",
    )


class AgentInput(BaseModel):
    """Standardized input for all domain agents."""

    message: str = Field(
        ...,
        description="The user message to process",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific context (job draft, pipeline state, etc.)",
    )
    session_id: str = Field(
        ...,
        description="Unique session identifier",
    )
    company_id: str = Field(
        ...,
        description="Company ID for multi-tenancy",
    )
    user_id: str = Field(
        ...,
        description="ID of the user interacting with the agent",
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Previous messages in the conversation",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source, channel, locale, etc.)",
    )


class AgentReasoningStep(BaseModel):
    """Structured single step in an agent decision tree.

    Wave 0 Fix 4 (2026-05-27) — preparatório Onda 1 Studio Control Room.

    Diferente da `ReasoningStep` em libs/agents-core/lia_agents_core/state_machine.py
    (que captura graph execution log: node_name, durations), esta classe captura
    **a lógica de decisão do agente** — critérios avaliados, scores, dados
    acessados (LGPD Art. 9). Usada pelo DecisionTreeDrawer (Onda 1) pra render
    "por que o agente recomendou esta ação".

    Campo `data_fields_accessed` é o backbone do audit LGPD — toda execução
    de agente declara quais campos do candidato leu, e o sensor
    `check_lgpd_data_access_logged.py` (Onda 1) valida.
    """

    step_type: Literal["criterion", "thought", "action", "observation"] = Field(
        ...,
        description="Tipo do passo no decision tree.",
    )
    label: str = Field(
        ...,
        description="Rótulo curto exibido na UI (ex: Experiência 3 anos).",
    )
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Score normalizado [0.0, 1.0]. Opcional pra passos sem peso.",
    )
    matched: Optional[bool] = Field(
        default=None,
        description="True/False/None — checkmark visual no DecisionTreeDrawer.",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detalhe textual livre exibido em expand.",
    )
    data_fields_accessed: List[str] = Field(
        default_factory=list,
        description="Campos do candidato/job lidos neste passo (LGPD Art. 9 trail).",
    )


class AgentReasoningStep(BaseModel):
    """Structured single step in an agent decision tree.

    Wave 0 Fix 4 (2026-05-27) — preparatório Onda 1 Studio Control Room.

    Diferente da `ReasoningStep` em libs/agents-core/lia_agents_core/state_machine.py
    (que captura graph execution log: node_name, durations), esta classe captura
    **a lógica de decisão do agente** — critérios avaliados, scores, dados
    acessados (LGPD Art. 9). Usada pelo DecisionTreeDrawer (Onda 1) pra render
    "por que o agente recomendou esta ação".

    Campo `data_fields_accessed` é o backbone do audit LGPD — toda execução
    de agente declara quais campos do candidato leu, e o sensor
    `check_lgpd_data_access_logged.py` (Onda 1) valida.
    """

    step_type: Literal["criterion", "thought", "action", "observation"] = Field(
        ...,
        description="Tipo do passo no decision tree.",
    )
    label: str = Field(
        ...,
        description="Rótulo curto exibido na UI (ex: Experiência 3 anos).",
    )
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Score normalizado [0.0, 1.0]. Opcional pra passos sem peso.",
    )
    matched: Optional[bool] = Field(
        default=None,
        description="True/False/None — checkmark visual no DecisionTreeDrawer.",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detalhe textual livre exibido em expand.",
    )
    data_fields_accessed: List[str] = Field(
        default_factory=list,
        description="Campos do candidato/job lidos neste passo (LGPD Art. 9 trail).",
    )


class AgentOutput(BaseModel):
    """Standardized output from all domain agents."""

    message: str = Field(
        ...,
        description="The agent response message to display to the user",
    )
    actions: List[AgentAction] = Field(
        default_factory=list,
        description="Actions the agent performed or wants to perform",
    )
    state_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Updates to apply to the domain state (fields, flags, etc.)",
    )
    navigation: Optional[NavigationCommand] = Field(
        default=None,
        description="Navigation command if the agent wants to change stages",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the response (0.0 to 1.0)",
    )
    reasoning_steps: List[str] = Field(
        default_factory=list,
        description="Chain of reasoning steps the agent took (legacy flat list).",
    )
    reasoning_trace: Optional[List[AgentReasoningStep]] = Field(
        default=None,
        description=(
            "Structured decision tree — Wave 0 Fix 4 (2026-05-27). Populated by "
            "agents that expose audit-grade reasoning (Onda 1 DecisionTreeDrawer). "
            "None = legacy path; [] = agent ran but produced no structured trace."
        ),
    )
    tool_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from any tools that were called",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional output metadata (timing, tokens used, etc.)",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if something went wrong",
    )


class ClarificationOutput(BaseModel):
    """
    Retornado pelo orquestrador quando não consegue determinar o domínio com confiança.

    O frontend deve exibir isso como uma pergunta ao usuário, não como resposta de agente.
    O WebSocket envia type="clarification" com question + options antes de invocar qualquer agente.
    """

    type: Literal["clarification"] = "clarification"
    question: str = Field(
        ...,
        description="Pergunta de clarificação a exibir ao usuário",
    )
    options: List[str] = Field(
        default_factory=list,
        description="Opções sugeridas para o usuário escolher",
    )
    session_id: str = Field(
        ...,
        description="ID da sessão de chat",
    )
    company_id: str = Field(
        default="",
        description="ID da empresa (multi-tenant)",
    )


class BaseAgent(ABC):
    """Abstract base class that all domain agents must implement.

    This ensures a consistent interface across all agents (Wizard, Pipeline,
    Sourcing, etc.) and allows any agent to be used as a tool by a central
    orchestrator in the future.
    """

    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process user input and return agent output.

        This is the main entry point for the agent. It should:
        1. Analyze the input message and context
        2. Reason about what to do (using ReAct loop or other logic)
        3. Execute any necessary tools
        4. Return a structured response

        Args:
            input: Standardized agent input with message, context, and metadata.

        Returns:
            Standardized agent output with response, actions, and state updates.
        """
        ...

    async def get_status(self) -> dict:
        """Return the current status of the agent.

        Useful for monitoring and debugging. Returns information about
        the agent's health, configuration, and recent activity.

        Returns:
            Dictionary with status information including domain, health,
            and any relevant metrics.
        """
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
        }

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """The domain this agent operates in (e.g., 'wizard', 'pipeline', 'sourcing').

        Returns:
            String identifier for the agent's domain.
        """
        ...

    @property
    @abstractmethod
    def available_tools(self) -> List[str]:
        """List of tool names this agent can use.

        Returns:
            List of string tool identifiers available to this agent.
        """
        ...
