/**
 * Single source of truth for the dashboard sidebar's label↔path mapping.
 *
 * Why this file exists:
 *   The label↔URL mapping used to live in TWO places —
 *   `PAGE_ROUTES` in `src/components/dashboard-app.tsx` and
 *   `ROUTE_TO_PAGE` in `src/app/[locale]/(dashboard)/DashboardLayoutClient.tsx`.
 *   They drifted (Task #948) and caused 404s when a sidebar click pushed a URL
 *   that no route entry recognized. Centralizing the table here means adding
 *   or renaming a route requires editing exactly one place.
 *
 * Conventions:
 *   - `PageLabel` is the canonical label shown in the Sidebar AND the value
 *     used by `dashboard-app.tsx::renderCurrentPage()` switch cases.
 *   - `PAGE_PATHS` maps every label that has a dedicated route folder
 *     (`[locale]/(dashboard)/<segment>/page.tsx`) to its first path segment.
 *   - Labels without an entry here (e.g. "Indicadores", "Templates") are
 *     SPA-only states rendered inside the dashboard shell without a URL.
 */

export const PAGE_PATHS = {
  "Conversar": "/chat",
  "Decidir": "/tasks",
  "Vagas": "/jobs",
  "Recrutar": "/recrutar",
  "Funil de Talentos": "/funil-de-talentos",
  "Agentes": "/agent-studio",
  "Marketplace": "/agents/marketplace",
  "Configurações": "/configuracoes",
  "Biblioteca LIA": "/biblioteca-lia",
  "Bancos de Talentos": "/bancos-de-talentos",
  "Central Comunicação": "/central-comunicacao",
  "Ajuda": "/ajuda",
  "Projetos": "/projetos",
} as const

export type PageLabel = keyof typeof PAGE_PATHS
export type PagePath = (typeof PAGE_PATHS)[PageLabel]

/**
 * Labels rendered by `dashboard-app.tsx::renderCurrentPage()` that DO NOT
 * have a dedicated route folder — they only exist as SPA-only states inside
 * the dashboard shell. Listed here so the `DashboardPageLabel` union below
 * remains the single typed enumeration of valid `currentPage` values.
 */
export const SPA_ONLY_PAGE_LABELS = [
  "Indicadores",
  "Templates",
  "Estúdio de Agentes",
] as const

export type SpaOnlyPageLabel = (typeof SPA_ONLY_PAGE_LABELS)[number]

/** Every label `currentPage` may legitimately hold (excluding `upgrade-*`). */
export type DashboardPageLabel = PageLabel | SpaOnlyPageLabel

const DASHBOARD_PAGE_LABEL_SET: ReadonlySet<string> = new Set<string>([
  ...Object.keys(PAGE_PATHS),
  ...SPA_ONLY_PAGE_LABELS,
])

/** Runtime guard for the `DashboardPageLabel` union. */
export function isDashboardPageLabel(value: string): value is DashboardPageLabel {
  return DASHBOARD_PAGE_LABEL_SET.has(value)
}

const PATH_TO_LABEL: Record<string, PageLabel> = Object.fromEntries(
  Object.entries(PAGE_PATHS).map(([label, path]) => [path, label as PageLabel]),
) as Record<string, PageLabel>

/** Returns the URL path (without locale prefix) for a sidebar label, or undefined. */
export function pathFromLabel(label: string): PagePath | undefined {
  return (PAGE_PATHS as Record<string, PagePath>)[label]
}

/** Returns the canonical label for a first-segment path (without locale), or undefined. */
export function labelFromPath(path: string): PageLabel | undefined {
  return PATH_TO_LABEL[path]
}

/**
 * Fase A.2 (2026-06-06): deep-link de navegação in-shell. Mapeia o param
 * `?view=<label>` para um DashboardPageLabel válido. Usado pela LIA para
 * navegar às abas SEM rota própria (Indicadores, Templates, Módulos) — o
 * DashboardApp lê este param no mount + em mudança de searchParams.
 * Retorna undefined para param ausente/desconhecido (falha-soft).
 */
export function pageLabelFromViewParam(
  raw: string | null | undefined,
): DashboardPageLabel | undefined {
  if (!raw) return undefined
  let decoded = raw
  try {
    decoded = decodeURIComponent(raw)
  } catch {
    decoded = raw
  }
  return isDashboardPageLabel(decoded) ? (decoded as DashboardPageLabel) : undefined
}
