/**
 * Agent category accent — Fase 3 Sprint 5 (2026-05-30, decisão Paulo).
 *
 * O 10% de cor com propósito (DESIGN.md "90/10 Rule") aplicado ao Agent Studio:
 * cada categoria de RH ganha um acento CONTIDO ao avatar do agente — nunca ao
 * card inteiro. Dá "cara de agente" (identidade) sem reintroduzir o multicolor
 * saturado que a Sprint 1 removeu ("ATS infantil 4 cores").
 *
 * Guardas canônicas (todas respeitadas aqui):
 *  - Paleta DESSATURADA / editorial (tons "muted", nunca cores primárias 500).
 *  - CYAN EXCLUÍDO. wedo-cyan é reservado à assistente da plataforma quando
 *    ela age (white-label, memory project_white_label_ai_assistant). Nenhum
 *    acento de categoria puxa cyan, mesmo onde seria "natural" (analytics =>
 *    plum em vez de azul-ciano).
 *  - Tokens CANÔNICOS registrados em tailwind.config.ts (agent-cat-*) +
 *    DESIGN.md frontmatter colors. Sem Tailwind cru (amber-500) nem hex.
 *  - Acento aplicado só ao avatar (bg tonal /12 + ícone no tom). Texto, borda,
 *    botões do card permanecem em tokens neutros lia-*.
 *
 * Cada categoria => token de cor (sem prefixo utility). Consumidores compõem
 * bg-${token}/12 (fundo tonal sutil) + text-${token} (ícone/inicial).
 * general não tem acento (neutro graphite sobre powder) — o default calmo.
 *
 * Ref: AGENT_STUDIO_FASE3_STUDIO_EXPERIENCE.md Sprint 5; DESIGN.md
 * "Agent category accent"; types.ts AgentCategory (single source of categories).
 */
import type { AgentCategory } from "@/components/pages-agent-studio/custom-agents/types"

/**
 * Token de acento por categoria. Valor é o NOME do token Tailwind canonical
 * (sem bg-/text-), pra o consumidor compor a utility class.
 * null = sem acento (neutro). general é deliberadamente neutro.
 */
export const CATEGORY_ACCENT_TOKEN: Record<AgentCategory, string | null> = {
  // Triagem — slate-blue dessaturado (sério, analítico, calmo).
  screening: "agent-cat-screening",
  // Captação — sage/verde-acinzentado (crescimento, busca; distinto do
  // forest-green de status pra não confundir "ativo" com "categoria").
  sourcing: "agent-cat-sourcing",
  // Comunicação — terracota suave (calor humano, conversa).
  communication: "agent-cat-communication",
  // Análise — plum dessaturado (insight; NÃO cyan/azul, que puxaria a cor IA).
  analytics: "agent-cat-analytics",
  // Vagas — ocre/âmbar-acinzentado (estrutura, organização).
  job_management: "agent-cat-jobs",
  // Automação — ardósia/steel (mecânico, sistêmico, neutro-frio).
  automation: "agent-cat-automation",
  // Geral — sem acento; neutro graphite sobre powder (o repouso calmo do DS).
  general: null,
}

/**
 * Classes Tailwind do avatar pra uma categoria. Contido: só bg tonal + cor do
 * ícone/inicial. Quando general (sem acento), volta ao neutro canonical
 * (bg-powder + text-graphite) — o mesmo do StudioCardShell default.
 */
export interface CategoryAvatarClasses {
  /** Background tonal sutil do wrapper do avatar. */
  bg: string
  /** Cor do ícone/inicial dentro do avatar. */
  text: string
}

export function categoryAvatarClasses(category: AgentCategory): CategoryAvatarClasses {
  const token = CATEGORY_ACCENT_TOKEN[category]
  if (!token) {
    // Neutro canonical (general / fallback) — igual ao default do shell.
    return { bg: "bg-powder dark:bg-lia-bg-tertiary", text: "text-graphite dark:text-lia-text-primary" }
  }
  // Acento contido: fundo a 12% de opacidade (sutil, legível), ícone no tom
  // cheio (contraste WCAG AA sobre o fundo /12 claro).
  return { bg: `bg-${token}/12`, text: `text-${token}` }
}
