/**
 * Task #894 — resolução de deep-link `/configuracoes?section=…&subsection=…&field=…`.
 *
 * Mantido em `lib/` (puro, sem JSX, sem `next/*`) para que o teste
 * irmão de `use-ui-action.test.ts` possa cobri-lo no projeto `unit`
 * (environment: 'node') sem importar o monolito da página
 * `SettingsPageEnhanced` (que carrega 8 hubs lazy + `next/navigation`).
 *
 * Aplica os mesmos aliases que o handler `settings-open-tab` para
 * preservar contrato com despachadores antigos (chat, proactive-actions).
 */

export const SETTINGS_SECTION_IDS = [
  'minha-empresa',
  // P1-4 (2026-05-26): hub novo "LIA & Personalização" desentrelaça config LIA
  // do hub operacional Recrutamento & LIA. Audit ref: §3.learning-loops-vs-instrucoes-lia.
  'lia-personalizacao',
  // Consolidações P1 (2026-05-25): 'pipeline', 'screening', 'templates-assinatura' absorvidos.
  // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
  'recrutamento-lia',
  'comunicacao-alertas',
  'usuarios-departamentos',
  'integrations',
  // Webhooks DEFER (2026-05-25): removido do menu cliente — audit Wave 1+. Reativação quando 1º cliente pedir.
  'fairness-compliance',
] as const

export type SettingsSectionId = (typeof SETTINGS_SECTION_IDS)[number]

export const SETTINGS_SUBSECTIONS: Record<string, string[]> = {
  // PR 2/3 (2026-05-25): 'fairness' (dashboard) e 'ai-transparency' movidos para /wedo-admin/ (staff).
  // 'consent' e 'audit-summary' adicionados — vindos de Governança dissolvida.
  'fairness-compliance': ['lgpd-candidatos', 'consent', 'audit-summary', 'studio'],
  // P1-4 (2026-05-26): hub novo agrupa toda config LIA (instrucoes-lia + learning-loops).
  'lia-personalizacao': ['instrucoes-lia', 'learning-loops'],
  // P1-4 (2026-05-26): 'instrucoes-lia' movido para hub 'lia-personalizacao' (config LIA juntada).
  // Recrutamento & LIA fica apenas com subsections operacionais (pipeline + screening + automacoes).
  'recrutamento-lia': ['pipeline', 'screening', 'automacoes'],
  // Consolidações P1 (2026-05-25): hub comunicacao-alertas absorveu templates-assinatura (5 tabs canonical).
  'comunicacao-alertas': ['templates', 'signature', 'schedule', 'alerts'],
  // P1-4 (2026-05-26): 'learning-loops' movido para hub 'lia-personalizacao' (config LIA juntada).
  // Minha Empresa fica sem subsections — bloco direto (basic + cultura + tech + etc.).
  'minha-empresa': [],
}

export const SETTINGS_SECTION_ALIASES: Record<string, SettingsSectionId> = {
  alertas: 'comunicacao-alertas',
  integracoes: 'integrations',
  'templates-e-assinatura': 'templates-assinatura',
}

export interface ResolvedSettingsTarget {
  section: SettingsSectionId | null
  subsection: string
  field: string | null
}

const EMPTY: ResolvedSettingsTarget = { section: null, subsection: '', field: null }

function isKnownSection(id: string): id is SettingsSectionId {
  return (SETTINGS_SECTION_IDS as readonly string[]).includes(id)
}

/**
 * Lê `?section=`, `?subsection=` e `?field=` de um `URLSearchParams`
 * e devolve o destino canônico que o `SettingsPageEnhanced` deve abrir.
 *
 * - Sections desconhecidas viram `null` (evita tabs fantasma).
 * - Subsections desconhecidas viram `''` (evita state poluído).
 * - O alias `alertas → comunicacao-alertas` é o mesmo de `openTabHandler`.
 * - O parâmetro `field` é preservado mesmo sem `section`, para manter
 *   compatibilidade com Task #712 (scroll-into-view a partir do chat).
 */
export function resolveSettingsTarget(
  params: URLSearchParams | null | undefined,
): ResolvedSettingsTarget {
  if (!params) return EMPTY
  const field = params.get('field')
  const rawSection = params.get('section')
  if (!rawSection) return { ...EMPTY, field }
  const sectionId = SETTINGS_SECTION_ALIASES[rawSection] ?? rawSection
  if (!isKnownSection(sectionId)) return { ...EMPTY, field }
  const rawSubsection = params.get('subsection') || ''
  const validSubs = SETTINGS_SUBSECTIONS[sectionId] ?? []
  const subsection = validSubs.includes(rawSubsection) ? rawSubsection : ''
  return { section: sectionId, subsection, field }
}
