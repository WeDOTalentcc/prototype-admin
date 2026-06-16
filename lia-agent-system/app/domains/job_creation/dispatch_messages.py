"""Dispatch messages canonical entre frontend wizard e backend graph.

Pattern fragil identificado em audit F-4.11: frontend dispatch
sendChatMessage(literal_string) e backend parsea via regex em
pipeline_template_node. Mudanca de copy em qualquer lado quebra silenciosamente.

Esta constante e canonical para AMBOS lados. Mirror em:
  plataforma-lia/src/components/unified-chat/wizard/dispatchMessages.ts

Sensor schema-sync (futuro PR): validar que strings/regex batem TS<->Python.

NAO MUDAR sem atualizar dispatchMessages.ts simultaneamente.
"""

from __future__ import annotations

# ── Literal dispatch templates (frontend envia EXATAMENTE estas strings) ──
# Mantidos para documentacao + casos onde precisamos emitir do backend.
APPLY_TEMPLATE_TEMPLATE = "Aplicar template de pipeline {template_id}"
APPLIED_ACK_MESSAGE = "Template de pipeline aplicado, pode seguir."
USE_DEFAULT_MESSAGE = "Usar pipeline padrao da empresa."

# ── Regex canonical (mesma semantica dos literais acima, robustos a variacoes) ──
# Liberalidade pre-existente em graph.py:
#  - Patterns sao IGNORECASE
#  - Aceitam variacoes ortograficas comuns (acentos, "padrao"/"padrao")
#  - Aceitam re-arranjo de palavras (search, nao match anchorado)
#
# Strings que DEVEM matchar APPLY_TEMPLATE_PATTERN:
#  - "Aplicar template de pipeline <uuid>"
#
# Strings que DEVEM matchar APPLIED_ACK_PATTERN:
#  - "Template de pipeline aplicado, pode seguir."
#  - "Template de pipeline aplicada"  (variacao genero)
#
# Strings que DEVEM matchar USE_DEFAULT_PATTERN:
#  - "Usar pipeline padrao da empresa."
#  - "Pipeline padrao da empresa"
#  - "Pular template"
APPLY_TEMPLATE_PATTERN = (
    r"aplicar.*?template.*?pipeline.*?"
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)
APPLIED_ACK_PATTERN = r"template.*?pipeline.*?aplicad[oa]"
USE_DEFAULT_PATTERN = (
    r"(pipeline.*?padr[ãa]o.*?empresa"
    r"|usar.*?padr[ãa]o.*?empresa"
    r"|pular.*?template)"
)
