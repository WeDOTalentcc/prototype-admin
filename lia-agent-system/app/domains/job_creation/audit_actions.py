"""Audit action names canonical para job_creation domain.

Substitui strings literais soltas em graph.py por StrEnum tipado.

Sites cobertos por esta enum (Sprint Pipeline Templates 2026-05-26):
- pipeline_template_node:1504 -> APPLIED_IN_WIZARD
- pipeline_template_node:1523 -> APPLIED_ACK
- pipeline_template_node:1539 -> SKIPPED
- pipeline_template_node:1647 -> SUGGESTED

Pattern: usar PipelineTemplateAuditAction.APPLIED_IN_WIZARD.value em chamadas
a audit.log_decision(action=...) para garantir consistencia entre o emit
(graph.py) e qualquer sensor/consumer downstream que filtre por action name.

Sensor recomendado (futuro PR): validar via AST que toda chamada
audit.log_decision em app/domains/job_creation/ usa action que existe em
algum dos enums deste modulo.
"""

from enum import Enum


class PipelineTemplateAuditAction(str, Enum):
    """Audit actions canonical para pipeline_template stage.

    Quatro estados:
    - SUGGESTED: backend sugeriu template (com top-3 ranking) ao recrutador
    - APPLIED_IN_WIZARD: recrutador escolheu um template via wizard
      (request frontend re-entrada com "Aplicar template de pipeline <uuid>")
    - APPLIED_ACK: recrutador ja aplicou template via fetch separado, frontend
      avisa backend pra registrar e seguir ("Template de pipeline aplicado, pode seguir.")
    - SKIPPED: recrutador optou por usar pipeline padrao da empresa
      ("Usar pipeline padrao da empresa.")
    """

    SUGGESTED = "pipeline_template_suggested"
    APPLIED_IN_WIZARD = "pipeline_template_applied_in_wizard"
    APPLIED_ACK = "pipeline_template_applied_ack"
    SKIPPED = "pipeline_template_skipped"
