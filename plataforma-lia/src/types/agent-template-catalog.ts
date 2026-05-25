/**
 * Tipos canonical do AgentTemplateCatalog (Sprint 3 Caminho B).
 * Espelham AgentTemplateCatalogResponse do backend lia-agent-system.
 */

export interface AgentTemplateCatalog {
  id: string
  slug: string
  name: string
  description: string
  category_id: string
  sector_id: string | null
  system_prompt: string
  allowed_tools: string[]
  context_level: "minimal" | "standard" | "full"
  max_steps: number
  temperature: number
  enable_memory: boolean
  excluded_tools: string[]
  tags: string[]
  vertical_prompts: Record<string, string> | null
  icon: string | null
  accent_color: string | null
  badge_variant: string | null
  sort_order: number
  is_active: boolean
  company_id: string | null
  created_at: string
  updated_at: string
}

export interface AgentCategory {
  id: string
  label_pt: string
  label_en: string
  icon: string | null
  sort_order: number
  is_active: boolean
}

export interface AgentSector {
  id: string
  label_pt: string
  label_en: string
  sort_order: number
  is_active: boolean
}

/**
 * Map de accent_color (token DS neutro) → classe Tailwind canonical.
 * Per decisão Paulo #10 (Sprint 2 white-label): templates usam tokens
 * NEUTROS (não cyan da LIA). Cyan exclusivo pra LIA chat persona.
 */
export function accentColorClass(value: string | null | undefined): string {
  switch (value) {
    case "ink":
      return "text-ink border-ink/30 bg-ink/5"
    case "graphite":
      return "text-graphite border-graphite/30 bg-graphite/5"
    case "slate":
      return "text-slate-600 border-slate-300 bg-slate-50"
    case "mist":
      return "text-slate-500 border-slate-200 bg-slate-50/60"
    default:
      return "text-slate-600 border-slate-200 bg-slate-50"
  }
}
