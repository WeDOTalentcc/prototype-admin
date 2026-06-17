/**
 * Payload canonical para criar um Custom Agent a partir de um AgentTemplate.
 *
 * SINGLE SOURCE OF TRUTH (Paulo, crítica do recrutador 2026-05-30, P1):
 *   O wizard (CreateAgentWizard, approach="template") e a ação "Usar agora"
 *   do TemplateCard (criação direta, sem passar pelo wizard) precisam montar
 *   EXATAMENTE o mesmo corpo de POST /api/backend-proxy/custom-agents. Antes o
 *   corpo vivia inline só no wizard; "Usar agora" e "Ajustar antes" caíam ambos
 *   no wizard (mesma coisa). Agora "Usar agora" cria direto reusando este helper
 *   — 1 fonte de verdade, sem divergência de contrato.
 *
 * Não inclui `category` no corpo: o backend deriva categoria do domain/tools.
 * (bug histórico `body.category` já corrigido no endpoint.)
 */

import type { AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"

export interface CreateAgentPayload {
  name: string
  role: string
  description: string
  system_prompt: string
  allowed_tools: string[]
  domain: string
  context_level: AgentTemplate["context_level"]
  max_steps: number
  temperature: number
}

/**
 * Monta o corpo do POST a partir de um template. `nameOverride` permite ao
 * wizard usar o nome editado pelo recrutador; quando ausente usa o nome do
 * template (caminho "Usar agora", criação direta com os defaults).
 */
export function buildCreateAgentPayloadFromTemplate(
  template: AgentTemplate,
  nameOverride?: string,
): CreateAgentPayload {
  return {
    name: nameOverride || template.name,
    role: template.description,
    description: template.description,
    system_prompt: template.system_prompt,
    allowed_tools: template.allowed_tools,
    domain: template.domain,
    context_level: template.context_level,
    max_steps: template.max_steps,
    temperature: template.temperature,
  }
}

/** Headers canonical (Content-Type + Bearer quando há auth_token). */
export function buildAgentAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}
