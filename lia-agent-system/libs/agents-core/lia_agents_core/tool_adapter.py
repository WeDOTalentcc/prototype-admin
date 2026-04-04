"""
Tool Adapter — ToolDefinition e tool_definition_to_langchain_tool.

Extrai as definições de compatibilidade do react_loop legado para uso
direto pelos tool registries e agentes LangGraph sem depender do ReActLoop.

Uso:
    from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool

    @ToolDefinition(name="my_tool", description="...", function=my_fn)
    ...
"""
from typing import Any, Callable, Dict

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Schema for a tool compatible with LangGraph create_react_agent."""

    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="What the tool does")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema describing the tool parameters",
    )
    function: Callable = Field(
        ...,
        description="Async or sync function to execute when the tool is called",
    )

    class Config:
        arbitrary_types_allowed = True


def tool_definition_to_langchain_tool(td: ToolDefinition) -> Any:
    """
    Converte um ToolDefinition em LangChain StructuredTool
    compatível com LangGraph create_react_agent.

    Suporta funções async e sync automaticamente.

    Uso em agentes (_get_tools()):
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_my_tools()
        lc_tools = [tool_definition_to_langchain_tool(td) for td in tool_defs]
    """
    import inspect

    try:
        from langchain_core.tools import StructuredTool
    except ImportError as exc:
        raise ImportError(
            "langchain-core não instalado — necessário para LangGraph"
        ) from exc

    fn = td.function
    name = td.name
    description = td.description or f"Executa {name}"

    if inspect.iscoroutinefunction(fn):
        return StructuredTool.from_function(
            coroutine=fn,
            name=name,
            description=description,
        )
    return StructuredTool.from_function(
        func=fn,
        name=name,
        description=description,
    )
