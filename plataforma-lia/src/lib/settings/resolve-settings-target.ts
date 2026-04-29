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
  'pipeline',
  'screening',
  'templates-assinatura',
  'comunicacao-alertas',
  'usuarios-departamentos',
  'integrations',
  'webhooks',
  'fairness-compliance',
] as const

export type SettingsSectionId = (typeof SETTINGS_SECTION_IDS)[number]

export const SETTINGS_SUBSECTIONS: Record<string, string[]> = {
  'fairness-compliance': ['fairness', 'lgpd-candidatos', 'studio'],
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
