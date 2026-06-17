import {
  Briefcase,
  Search,
  BarChart2,
  FileText,
  HelpCircle,
  Plus,
  MessageSquare,
  Calendar,
  BookOpen,
  TrendingUp,
  Filter,
  Clock,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"

/**
 * Single source of truth for unified-chat slash commands.
 *
 * Both `useSlashCommands` (dropdown UX) and `useWizardIntegration.handleSlashCommand`
 * (input interceptor) consume this list. The in-app `/ajuda` help and the task
 * spec MUST be kept in sync with the entries below.
 *
 * Keep changes here whenever a new shortcut is added or renamed.
 */
export interface SlashCommand {
  /** Stable identifier used by the dropdown selection handler. */
  id: string
  /** Canonical token, e.g. "/criar vaga". Always lowercase, leading slash. */
  primary: string
  /** Alternative tokens accepted by the interceptor (lowercase, with slash). */
  aliases: readonly string[]
  /** Short label shown in the dropdown. */
  label: string
  /** Secondary line shown in the dropdown. */
  subtitle: string
  /** Icon displayed in the dropdown. */
  icon: LucideIcon
  /**
   * Text inserted into the input when picked from the dropdown.
   * When omitted the dropdown emits the canonical token (so the interceptor
   * fires on the next Enter).
   *
   * Conventions:
   *   - For commands that submit immediately on the next Enter, prefill
   *     ends with the canonical token (no trailing space) — e.g.
   *     "/relatorio semanal".
   *   - For commands that need user input (e.g. /buscar, /definir, /feedback,
   *     /agendar), prefill ends with a space or `@` so the user knows to
   *     keep typing.
   */
  dropdownPrefill?: string
  /**
   * Message dispatched to the backend when the user types the bare command
   * (no @mention). Returning `null` means the command is dropdown-only and
   * has no interceptor behaviour.
   */
  buildBareMessage?: () => string | null
  /**
   * Message dispatched when the command is used as `/cmd @target`. Returning
   * `null` means the command does not accept a mention argument.
   */
  buildMentionMessage?: (mention: string) => string | null
  /** When true, the entry is shown in the `/`-trigger dropdown. */
  showInDropdown?: boolean
}

/** Convenience: lowercase + collapse whitespace, useful when matching tokens. */
export function normalizeCommand(input: string): string {
  return input.trim().toLowerCase().replace(/\s+/g, " ")
}

/**
 * IDs of commands that resolve via `onExecuteCommand` (UI side-effect only,
 * no backend message). Anything in this list is exempt from the
 * "must have buildBareMessage or non-empty dropdownPrefill" invariant.
 */
export const EXECUTE_ONLY_COMMAND_IDS: readonly string[] = ["nova-conversa"]

export const SLASH_COMMANDS: readonly SlashCommand[] = [
  {
    id: "criar-vaga",
    primary: "/criar vaga",
    aliases: ["/nova vaga", "/job"],
    label: "Criar vaga",
    subtitle: "Iniciar wizard de criacao de vaga",
    icon: Briefcase,
    dropdownPrefill: "Quero criar uma nova vaga de emprego. ",
    buildBareMessage: () => "Criar nova vaga",
    showInDropdown: true,
  },
  {
    id: "buscar",
    primary: "/buscar",
    aliases: ["/talent"],
    label: "Buscar candidatos",
    subtitle: "Pesquisar candidatos por criterios — complete a frase",
    icon: Search,
    dropdownPrefill: "Buscar candidatos que ",
    buildBareMessage: () => "Buscar candidatos",
    buildMentionMessage: (mention) => `Buscar candidato: ${mention}`,
    showInDropdown: true,
  },
  {
    id: "pipeline",
    primary: "/pipeline",
    aliases: [],
    label: "Ver pipeline",
    subtitle: "Status do funil de vagas abertas (use @vaga para filtrar)",
    icon: BarChart2,
    dropdownPrefill: "Mostrar o status do funil de candidatos",
    buildBareMessage: () => "Mostrar funil de vagas abertas",
    buildMentionMessage: (mention) => `Pipeline da vaga: ${mention}`,
    showInDropdown: true,
  },
  // ---------------------------------------------------------------------------
  // /relatorio — generic entry preserved for backcompat (token + verb match).
  // The four `relatorio-*` variants below are the discoverable surface.
  // ---------------------------------------------------------------------------
  {
    id: "relatorio",
    primary: "/relatorio",
    aliases: ["/relatório"],
    label: "Gerar relatorio",
    subtitle: "Relatorios de recrutamento",
    icon: FileText,
    dropdownPrefill: "Gerar um relatorio de recrutamento ",
    buildBareMessage: () => "Gerar relatorio semanal de recrutamento",
    buildMentionMessage: (mention) => `Relatorio da vaga: ${mention}`,
    showInDropdown: false,
  },
  {
    id: "relatorio-semanal",
    primary: "/relatorio semanal",
    aliases: [],
    label: "Relatorio semanal",
    subtitle: "Resumo da semana — vagas, candidatos, atividades",
    icon: FileText,
    dropdownPrefill: "/relatorio semanal",
    buildBareMessage: () => "Gerar relatorio semanal de recrutamento",
    showInDropdown: true,
  },
  {
    id: "relatorio-funil",
    primary: "/relatorio funil",
    aliases: ["/relatorio pipeline"],
    label: "Relatorio do funil",
    subtitle: "Conversao por etapa do pipeline",
    icon: TrendingUp,
    dropdownPrefill: "/relatorio funil",
    buildBareMessage: () =>
      "Gerar relatorio do funil de candidatos com conversao por etapa",
    showInDropdown: true,
  },
  {
    id: "relatorio-fonte",
    primary: "/relatorio fonte",
    aliases: ["/relatorio sourcing"],
    label: "Relatorio de fonte",
    subtitle: "Performance por canal de origem (LinkedIn, indicacao, etc.)",
    icon: Filter,
    dropdownPrefill: "/relatorio fonte",
    buildBareMessage: () =>
      "Gerar relatorio de performance por canal de origem dos candidatos",
    showInDropdown: true,
  },
  {
    id: "relatorio-tempo",
    primary: "/relatorio tempo",
    aliases: ["/relatorio sla"],
    label: "Relatorio de tempo",
    subtitle: "Time-to-hire e SLA por etapa",
    icon: Clock,
    dropdownPrefill: "/relatorio tempo",
    buildBareMessage: () =>
      "Gerar relatorio de time-to-hire e SLA por etapa",
    showInDropdown: true,
  },
  // ---------------------------------------------------------------------------
  // /feedback e /agendar — agora visiveis com prefill que aciona @autocomplete.
  // ---------------------------------------------------------------------------
  {
    id: "feedback",
    primary: "/feedback",
    aliases: [],
    label: "Enviar feedback",
    subtitle: "Use com @candidato — enviar feedback estruturado",
    icon: MessageSquare,
    dropdownPrefill: "/feedback @",
    // P1-2 (Fase B 2026-05-23): bare `/feedback` (sem @target) agora dispara
    // mensagem de clarificacao em vez de no-op silencioso. Pattern espelha
    // `/buscar` bare — completa o loop de discoverability do dropdown.
    buildBareMessage: () =>
      "Quero registrar feedback de um candidato. Pra qual candidato? (use @ pra mencionar)",
    buildMentionMessage: (mention) => `Enviar feedback para: ${mention}`,
    showInDropdown: true,
  },
  {
    id: "agendar",
    primary: "/agendar",
    aliases: [],
    label: "Agendar entrevista",
    subtitle: "Use com @candidato — agendar entrevista",
    icon: Calendar,
    dropdownPrefill: "/agendar @",
    // P1-2 (Fase B 2026-05-23): bare `/agendar` (sem @target) dispara
    // clarificacao em vez de no-op. LIA pede candidato e horario.
    buildBareMessage: () =>
      "Quero agendar uma entrevista. Pra qual candidato e quando? (use @ pra mencionar)",
    buildMentionMessage: (mention) => `Agendar entrevista com: ${mention}`,
    showInDropdown: true,
  },
  {
    id: "ajuda",
    primary: "/ajuda",
    aliases: [],
    label: "O que posso fazer?",
    subtitle: "Ver todas as capacidades da IA",
    icon: HelpCircle,
    dropdownPrefill: "O que voce pode fazer? Liste todas as suas capacidades.",
    buildBareMessage: () => "/ajuda",
    showInDropdown: true,
  },
  {
    id: "planejar",
    primary: "/planejar",
    aliases: ["/plan", "/decompor", "/automatizar"],
    label: "Planejar tarefa",
    subtitle: "Decomponha tarefa complexa em subtarefas com dependencias",
    icon: TrendingUp,
    dropdownPrefill: "/planejar ",
    buildBareMessage: () => "/planejar",
    buildMentionMessage: (mention) => `/planejar ${mention}`,
    showInDropdown: true,
  },  {
    id: "planejar",
    primary: "/planejar",
    aliases: ["/plan", "/decompor", "/automatizar"],
    label: "Planejar tarefa",
    subtitle: "Decomponha tarefa complexa em subtarefas com dependencias",
    icon: TrendingUp,
    dropdownPrefill: "/planejar ",
    buildBareMessage: () => "/planejar",
    buildMentionMessage: (mention) => `/planejar ${mention}`,
    showInDropdown: true,
  },
  // ---------------------------------------------------------------------------
  // /definir — generic entry (kept visible) plus 5 hardcoded shortcuts for the
  // most common terms. The shortcuts ARE intercepted locally by
  // `UnifiedChat.handleSend` via DEFINIR_REGEX (no backend round-trip), so
  // their `buildBareMessage` returns the canonical token only as a contract
  // fallback (visible-command invariant) — not as the actual dispatch path.
  // ---------------------------------------------------------------------------
  {
    id: "definir",
    primary: "/definir",
    aliases: ["/glossario", "/glossário"],
    label: "Definir termo",
    subtitle: "Definicao oficial — complete com o termo",
    icon: BookOpen,
    dropdownPrefill: "/definir ",
    showInDropdown: true,
  },
  // Onda 4-P2-2 (2026-05-24): removidos 5 shortcuts hardcoded /definir-wsi,
  // /definir-bars, /definir-bloom, /definir-bigfive, /definir-arquetipo.
  // Glossário canonical é dinâmico via lookupGlossaryTerm(term) consumido
  // pelo handler genérico de "/definir TERM" abaixo. Cada termo novo do
  // glossário NÃO requer PR no slash-commands.ts.
  {
    id: "nova-conversa",
    primary: "/nova-conversa",
    aliases: [],
    label: "Nova conversa",
    subtitle: "Iniciar conversa limpa",
    icon: Plus,
    showInDropdown: true,
  },
]

/**
 * Build the markdown card body shown when the user types `/ajuda`.
 * Lives here (single source of truth) so any chat surface can render
 * the same help text without duplicating the SLASH_COMMANDS filter.
 */
export function buildAjudaHelpMarkdown(): string {
  const lines = SLASH_COMMANDS
    .filter((c) => c.showInDropdown)
    .map((c) => `- **${c.primary}** — ${c.subtitle}`)
    .join("\n")
  return `Comandos disponíveis:\n\n${lines}\n\n_Dica: digite \`/\` para ver o menu rápido._`
}

/**
 * Match `/ajuda` (case-insensitive, no args). Exported so any surface
 * can detect the local-help command consistently.
 */
export const AJUDA_REGEX = /^\/ajuda\s*$/i

/**
 * Shape of the in-chat messages emitted when `/ajuda` resolves locally.
 * Mirrors the chat surface's `Message` contract loosely so consumers can
 * spread the result straight into their `setMessages` reducer without
 * coupling slash-commands to a chat-specific type.
 */
export interface AjudaChatMessages {
  userMsg: { id: string; sender: "user"; content: string; timestamp: string }
  helpMsg: { id: string; sender: "lia"; content: string; timestamp: string }
}

/**
 * Build the user-echo + LIA-help message pair for an in-chat `/ajuda`
 * resolution. Centralised here so every chat surface (UnifiedChat and
 * any future popovers) renders identical bubbles and we can unit-test
 * the wiring without rendering the full chat component.
 *
 * `now` is injected so tests get deterministic timestamps; production
 * callers can omit it and rely on the default `Date.now()`/`new Date()`.
 */
export function buildAjudaChatMessages(
  rawInput: string,
  responseMarkdown: string,
  now: Date = new Date(),
): AjudaChatMessages {
  const ts = now.toISOString()
  const ms = now.getTime()
  return {
    userMsg: { id: `user-${ms}`, sender: "user", content: rawInput, timestamp: ts },
    helpMsg: { id: `lia-${ms}-ajuda`, sender: "lia", content: responseMarkdown, timestamp: ts },
  }
}

/**
 * Find a command by either its `primary` token or one of its `aliases`.
 * Returns `undefined` when nothing matches.
 *
 * Important: when multiple entries share a verb (e.g. `/relatorio` and
 * `/relatorio semanal`), token lookup matches by full normalized string —
 * so both `/relatorio` and `/relatorio semanal` resolve to the right entry.
 */
export function findSlashCommandByToken(token: string): SlashCommand | undefined {
  const normalized = normalizeCommand(token)
  return SLASH_COMMANDS.find(
    (cmd) =>
      normalizeCommand(cmd.primary) === normalized ||
      cmd.aliases.some((alias) => normalizeCommand(alias) === normalized),
  )
}

/**
 * Find a command by the leading verb of a `/<verb> @target` phrase, e.g.
 * `"buscar"` or `"job"`. Compares against the verb portion of `primary` and
 * each alias, ignoring the leading slash.
 *
 * When several entries share a verb (e.g. `/relatorio` vs `/relatorio
 * semanal`), the first match wins — the catalog lists generic entries
 * before variants on purpose so cross-mention forms (`/relatorio @vaga`)
 * resolve to the variant with `buildMentionMessage`.
 */
export function findSlashCommandByVerb(verb: string): SlashCommand | undefined {
  const v = verb.trim().toLowerCase()
  if (!v) return undefined
  return SLASH_COMMANDS.find((cmd) => {
    const tokens = [cmd.primary, ...cmd.aliases]
    return tokens.some((t) => t.replace(/^\//, "").split(/\s+/)[0] === v)
  })
}

/**
 * Match bare `/buscar` (no args). Used by `UnifiedChat.handleSend` to render
 * a local clarification card with the canonical search recipes, instead of
 * shipping the generic "Buscar candidatos" payload to the backend agent.
 */
export const BUSCAR_BARE_REGEX = /^\/buscar\s*$/i

/**
 * Markdown card body shown when the user submits bare `/buscar`.
 *
 * Listing the canonical search recipes locally turns the dropdown discovery
 * into a complete loop: the user picks `/buscar`, hits Enter, and gets a
 * concrete menu of patterns to copy/paste — no agent round-trip, no LLM
 * generation drift. Same pattern as `/ajuda`.
 */
export function buildBuscarHelpMarkdown(): string {
  const recipes = [
    "`/buscar candidatos com habilidade <skill>` — ex: `/buscar candidatos com habilidade Python`",
    "`/buscar candidatos de nivel <senioridade>` — ex: `/buscar candidatos de nivel pleno`",
    "`/buscar candidatos com status <status>` — ex: `/buscar candidatos com status aprovado`",
    "`/buscar candidatos do departamento <dept>` — ex: `/buscar candidatos do departamento engenharia`",
    "`/buscar @candidato` — buscar um candidato especifico",
  ]
  return [
    "Que tipo de busca? Use um destes padroes:",
    "",
    ...recipes.map((r) => `- ${r}`),
    "",
    "_Ou descreva em linguagem natural — ex: \"candidatos seniores em SP que dominam React\"._",
  ].join("\n")
}

/**
 * Build the user-echo + LIA-help message pair for an in-chat bare `/buscar`
 * resolution. Mirrors `buildAjudaChatMessages` so any chat surface emits the
 * same bubbles.
 */
export function buildBuscarChatMessages(
  rawInput: string,
  responseMarkdown: string,
  now: Date = new Date(),
): AjudaChatMessages {
  const ts = now.toISOString()
  const ms = now.getTime()
  return {
    userMsg: { id: `user-${ms}`, sender: "user", content: rawInput, timestamp: ts },
    helpMsg: { id: `lia-${ms}-buscar`, sender: "lia", content: responseMarkdown, timestamp: ts },
  }
}
