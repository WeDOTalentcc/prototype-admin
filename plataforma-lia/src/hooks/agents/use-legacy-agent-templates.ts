/**
 * Convenience hook: catalog backend canonical → shape AgentTemplate legacy.
 *
 * Sprint 3 Parte 2 — bridge ergonômica para consumers existentes que esperam
 * o shape do antigo `agent-templates-data.ts` (deletado nessa sprint).
 *
 * Para consumers novos, preferir `useAgentTemplateCatalog` direto + acessar
 * shape canonical (snake_case + sector_id PT-BR).
 */
"use client"

import { useMemo } from "react"

import {
  mapCatalogListToLegacy,
} from "@/lib/agent-template-catalog-adapter"
import { useAgentTemplateCatalog } from "@/hooks/agents/use-agent-template-catalog"
import type { AgentTemplate } from "@/components/pages-agent-studio/custom-agents/types"

export interface UseLegacyAgentTemplatesReturn {
  templates: AgentTemplate[]
  isLoading: boolean
  error: string | null
}

export function useLegacyAgentTemplates(): UseLegacyAgentTemplatesReturn {
  const { data, isLoading, error } = useAgentTemplateCatalog()
  const templates = useMemo(() => mapCatalogListToLegacy(data), [data])
  return { templates, isLoading, error }
}
