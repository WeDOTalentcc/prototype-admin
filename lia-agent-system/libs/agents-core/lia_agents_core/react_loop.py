"""
react_loop.py — Shim de compatibilidade pós-migração LangGraph.

O ReActLoop customizado foi removido em favor do create_react_agent nativo do LangGraph.
Este módulo re-exporta interfaces ainda referenciadas por código existente
(tool registries, enhanced_agent_mixin, learning_extractor, testes).

Para novos agentes, use:
    from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool
    from lia_agents_core.langgraph_react_base import LangGraphReActBase
"""
from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool  # noqa: F401

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReActState(BaseModel):
    """Stub de compatibilidade pós-migração LangGraph.

    Usado por learning_extractor, enhanced_agent_mixin e langgraph_react_base
    para sintetizar estado após execução LangGraph.
    Em produção, o estado real é gerenciado pelo LangGraph MessagesState.
    """

    messages: List[Dict[str, Any]] = Field(default_factory=list)
    current_reasoning: str = Field(default="")
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    should_respond: bool = Field(default=False)
    final_response: Optional[str] = Field(default=None)
    iteration: int = Field(default=0)
    tool_calls_made: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
    failed_tool_calls: List[str] = Field(default_factory=list)
    consecutive_duplicate_count: int = Field(default=0)
    last_tool_call_key: Optional[str] = Field(default=None)
    tokens_used_estimate: int = Field(default=0)
    session_id: Optional[str] = Field(default=None)
    confidence_score: float = Field(default=0.5)
    streaming_callback: Optional[Any] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True


class ReActConfig(BaseModel):
    """Stub de compatibilidade — parâmetros do antigo ReActLoop.

    Mantido para enhanced_agent_mixin, conftest e testes que referenciam
    ReActConfig como tipo. Novos agentes devem usar LangGraphReActBase
    diretamente (configuração via create_react_agent).
    """

    system_prompt: str = ""
    available_tools: List[Any] = Field(default_factory=list)
    domain: str = ""
    max_iterations: int = 5
    model_provider: str = "claude"
    temperature: float = 0.3
    guardrails: List[Any] = Field(default_factory=list)
    active_scope: Optional[str] = None


class ReActLoop:
    """Stub de compatibilidade — o ReActLoop real foi removido.

    Instanciar este stub levanta NotImplementedError com instrução de migração.
    Mantido apenas para que imports não quebrem em testes de contrato.
    """

    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError(
            "ReActLoop foi removido. Use LangGraphReActBase com create_react_agent. "
            "Veja libs/agents-core/lia_agents_core/langgraph_react_base.py"
        )


__all__ = [
    "ToolDefinition",
    "tool_definition_to_langchain_tool",
    "ReActState",
    "ReActConfig",
    "ReActLoop",
]
