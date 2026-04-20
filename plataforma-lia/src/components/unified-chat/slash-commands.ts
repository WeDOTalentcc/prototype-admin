import {
  Briefcase,
  Search,
  BarChart2,
  FileText,
  HelpCircle,
  Plus,
  MessageSquare,
  Calendar,
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
    subtitle: "Pesquisar candidatos por criterios",
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
    subtitle: "Status do funil de candidatos",
    icon: BarChart2,
    dropdownPrefill: "Mostrar o status do funil de candidatos",
    buildBareMessage: () => "Mostrar funil de vagas abertas",
    buildMentionMessage: (mention) => `Pipeline da vaga: ${mention}`,
    showInDropdown: true,
  },
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
    showInDropdown: true,
  },
  {
    id: "feedback",
    primary: "/feedback",
    aliases: [],
    label: "Enviar feedback",
    subtitle: "Enviar feedback para um candidato",
    icon: MessageSquare,
    buildMentionMessage: (mention) => `Enviar feedback para: ${mention}`,
    showInDropdown: false,
  },
  {
    id: "agendar",
    primary: "/agendar",
    aliases: [],
    label: "Agendar entrevista",
    subtitle: "Agendar entrevista com um candidato",
    icon: Calendar,
    buildMentionMessage: (mention) => `Agendar entrevista com: ${mention}`,
    showInDropdown: false,
  },
  {
    id: "ajuda",
    primary: "/ajuda",
    aliases: [],
    label: "O que posso fazer?",
    subtitle: "Ver todas as capacidades da LIA",
    icon: HelpCircle,
    dropdownPrefill: "O que voce pode fazer? Liste todas as suas capacidades.",
    buildBareMessage: () => "/ajuda",
    showInDropdown: true,
  },
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
 * Find a command by either its `primary` token or one of its `aliases`.
 * Returns `undefined` when nothing matches.
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
 */
export function findSlashCommandByVerb(verb: string): SlashCommand | undefined {
  const v = verb.trim().toLowerCase()
  if (!v) return undefined
  return SLASH_COMMANDS.find((cmd) => {
    const tokens = [cmd.primary, ...cmd.aliases]
    return tokens.some((t) => t.replace(/^\//, "").split(/\s+/)[0] === v)
  })
}
