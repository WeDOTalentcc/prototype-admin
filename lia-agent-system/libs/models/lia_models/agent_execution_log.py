"""
AgentExecutionLog — Persists every individual Studio agent execution.

Enables: execution history, temporal metrics, debugging, billing audit.

CANONICAL vs pool_agent_runs (decisao A4 / AUDIT 6 P1-8, 2026-05-29)
---------------------------------------------------------------------
agent_execution_logs e pool_agent_runs NAO sao duplicados -- cobrem
modos de execucao DISTINTOS e ambos sao canonical:

- agent_execution_logs (ESTA tabela): execucao INTERATIVA sincrona.
  Escrita por POST /custom-agents/{id}/execute (custom_agents.py:480) a
  cada mensagem que o usuario manda pro agente in-request. Carrega o par
  input_message/output_message + compliance_status -- trilha de auditoria
  de chat interativo (debugging, billing por execucao, FairnessGuard
  blocked vs pass). Lida por endpoints Studio de KPI/compliance/usage em
  custom_agents.py.

- pool_agent_runs (libs/models/lia_models/pool_agent_run.py): execucao
  AUTONOMA de assignment/deployment (cron / on_demand / event_driven).
  Escrita pelo orchestrator via PoolAgentRunRepository. Carrega
  assignment_id/deployment_id + runtime_metrics + results[] -- telemetria
  de run em lote (Sala de Controle / DecisionTreeDrawer). Lida pelos
  endpoints de agent_monitoring (active-executions, recent-executions).

Se a tabela aparecer "vazia" num tenant (observacao do AUDIT 6) e
artefato do dev tenant nao ter executado custom agents interativos
recentemente -- NAO e sinal de tabela vestigial.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    deployment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(128), nullable=False)

    input_message = Column(Text, nullable=False)
    output_message = Column(Text, nullable=False, default="")
    confidence = Column(Float, default=0.0)

    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    model_used = Column(String(128), default="")
    latency_ms = Column(Integer, default=0)
    credits_consumed = Column(Integer, default=0)

    tool_calls = Column(ARRAY(String), default=[])
    compliance_status = Column(String(32), default="pass")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "deployment_id": str(self.deployment_id) if self.deployment_id else None,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "input_message": self.input_message[:200] if self.input_message else "",
            "output_message": self.output_message[:500] if self.output_message else "",
            "confidence": self.confidence,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "credits_consumed": self.credits_consumed,
            "tool_calls": self.tool_calls or [],
            "compliance_status": self.compliance_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
