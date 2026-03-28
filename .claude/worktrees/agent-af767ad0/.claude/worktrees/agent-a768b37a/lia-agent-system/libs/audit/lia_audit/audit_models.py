"""
Audit Models — dataclasses para registros de execução de agentes.

Separam o que vai para PostgreSQL (metadados leves, consulta rápida)
do que vai para storage de objeto (payload completo, investigação profunda).
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMCallRecord:
    """Registro de uma chamada LLM dentro de uma execução de agente."""
    type: str = "llm_call"
    timestamp: str = ""
    model: Optional[str] = None
    prompt_preview: str = ""        # primeiros 500 chars — PII já mascarado
    response_preview: str = ""      # primeiros 500 chars
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_total: Optional[int] = None
    latency_ms: float = 0.0


@dataclass
class ToolCallRecord:
    """Registro de uma chamada de tool dentro de uma execução de agente."""
    type: str = "tool_call"
    timestamp: str = ""
    tool: str = ""
    input_preview: str = ""         # primeiros 500 chars
    output_preview: str = ""        # primeiros 500 chars
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class NodeTransitionRecord:
    """Registro de transição entre nós num StateGraph."""
    type: str = "node_transition"
    timestamp: str = ""
    from_node: Optional[str] = None
    to_node: str = ""
    condition: Optional[str] = None


@dataclass
class ExecutionAuditRecord:
    """
    Registro completo de uma execução de agente.

    Campos leves (execution_metadata) → PostgreSQL: consulta rápida, dashboards.
    Campos pesados (entries) → storage de objeto: investigação, compliance, replay.
    """
    execution_id: str = ""
    session_id: str = ""
    user_id: str = ""
    company_id: str = ""
    domain: str = ""
    agent_type: str = "react"       # "react" | "graph"
    start_time: str = ""
    end_time: Optional[str] = None
    total_duration_ms: float = 0.0
    success: bool = True
    confidence: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    nodes_visited: List[str] = field(default_factory=list)
    error: Optional[str] = None
    storage_path: Optional[str] = None  # referência para o payload completo no storage
    # payload completo — enviado para storage de objeto, não para PG
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Campos leves para PostgreSQL — sem entries (payload pesado)."""
        return {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "domain": self.domain,
            "agent_type": self.agent_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "success": self.success,
            "confidence": self.confidence,
            "tools_used": self.tools_used,
            "nodes_visited": self.nodes_visited,
            "error": self.error,
            "storage_path": self.storage_path,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Payload completo para storage de objeto."""
        base = self.to_metadata_dict()
        base["entries"] = self.entries
        return base
