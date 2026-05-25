/**
 * Agent Template Catalog Adapter (Sprint 3 Parte 2).
 *
 * Mapa shape canonical backend (`AgentTemplateCatalog`, snake_case + sector_id PT-BR)
 * → shape legacy esperado pelos consumers (`AgentTemplate`, snake_case mas com
 * `category` (sem _id), `vertical` em vez de `sector_id`).
 *
 * Per decisão Paulo: este adapter é a única ponte. Consumers usam `AgentTemplate`
 * legacy shape; backend canonical é fonte de verdade. Quando todos os consumers
 * migrarem pro shape backend direto (Sprint futuro), deletar adapter.
 *
 * Refs:
 * - lia-agent-system migration _SECTOR_MAP canonical: tech↔tech, health↔saude,
 *   education↔educacao, retail↔varejo, null↔null.
 */
import type {
  AgentTemplate,
  AgentCategory as LegacyAgentCategory,
  AgentVertical as LegacyAgentVertical,
} from "@/components/pages-agent-studio/custom-agents/types"
import type { AgentTemplateCatalog } from "@/types/agent-template-catalog"

/**
 * Reverse map de sector_id canonical (backend, PT-BR) → vertical legacy (EN).
 * Espelha _SECTOR_MAP forward em lia-agent-system alembic migration.
 */
const SECTOR_TO_VERTICAL: Record<string, LegacyAgentVertical> = {
  tech: "tech",
  saude: "health",
  educacao: "education",
  varejo: "retail",
  generico: null,
}

export function mapSectorIdToVertical(
  sectorId: string | null | undefined,
): LegacyAgentVertical {
  if (sectorId === null || sectorId === undefined) return null
  return SECTOR_TO_VERTICAL[sectorId] ?? null
}

/**
 * Converte um AgentTemplateCatalog (backend canonical) pro shape
 * AgentTemplate legacy consumido pelos componentes do Agent Studio.
 *
 * Field rename canonical:
 * - `category_id` (backend) → `category` (consumer)
 * - `sector_id` (backend, PT-BR) → `vertical` (consumer, EN)
 * - `icon` (backend nullable) → `icon` (consumer required, fallback "Box")
 * - `domain` (backend não tem) → derivado de `category_id`
 */
export function mapCatalogToLegacy(item: AgentTemplateCatalog): AgentTemplate {
  return {
    id: item.id,
    name: item.name,
    description: item.description,
    category: item.category_id as LegacyAgentCategory,
    domain: item.category_id,
    icon: item.icon ?? "Box",
    system_prompt: item.system_prompt,
    allowed_tools: item.allowed_tools,
    context_level: item.context_level,
    max_steps: item.max_steps,
    temperature: item.temperature,
    enable_memory: item.enable_memory,
    excluded_tools: item.excluded_tools,
    tags: item.tags,
    vertical: mapSectorIdToVertical(item.sector_id),
    vertical_prompts: (item.vertical_prompts ?? undefined) as
      | AgentTemplate["vertical_prompts"]
      | undefined,
  }
}

/**
 * Helper: lista catalog → lista legacy.
 */
export function mapCatalogListToLegacy(
  items: AgentTemplateCatalog[] | null | undefined,
): AgentTemplate[] {
  if (!Array.isArray(items)) return []
  return items.map(mapCatalogToLegacy)
}
