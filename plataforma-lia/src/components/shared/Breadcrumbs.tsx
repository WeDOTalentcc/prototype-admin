"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronRight, Home } from "lucide-react"
import { cn } from "@/lib/utils"
import { PAGE_PATHS } from "@/lib/navigation/routes"

// ─────────────────────────────────────────────────────────────────
// Build a reverse lookup: path segment → human-readable PT-BR label
// Derived from PAGE_PATHS (single source of truth in routes.ts).
//
// e.g. "/recrutar" → "Recrutar"
//      "/funil-de-talentos" → "Funil de Talentos"
// ─────────────────────────────────────────────────────────────────
const SEGMENT_LABEL: Record<string, string> = Object.fromEntries(
  Object.entries(PAGE_PATHS).map(([label, path]) => [
    // strip leading "/" to get segment key
    path.replace(/^\//, ""),
    label,
  ]),
)

/** Additional static segments not in PAGE_PATHS (sub-routes). */
const EXTRA_SEGMENT_LABELS: Record<string, string> = {
  "agent-studio": "Estúdio de Agentes",
  "ai-credits": "Créditos de IA",
  "integracoes": "Integrações",
  "inteligencia": "Inteligência",
  "relatorios": "Relatórios",
  "agentes": "Agentes",
  "marketplace": "Marketplace",
  "pipeline": "Pipeline",
  "kanban": "Kanban",
  "vagas": "Vagas",
  "candidatos": "Candidatos",
  "bancos": "Bancos de Talentos",
}

const ALL_LABELS: Record<string, string> = { ...EXTRA_SEGMENT_LABELS, ...SEGMENT_LABEL }

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const LOCALE_RE = /^[a-z]{2}(-[A-Z]{2})?$/  // e.g. "pt", "en", "pt-BR"

// ─────────────────────────────────────────────────────────────────

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbsProps {
  /** Optional override. When omitted, crumbs are auto-generated from the
   *  current pathname. */
  items?: BreadcrumbItem[]
  className?: string
}

/**
 * Auto-generate breadcrumbs from a pathname like "/pt/recrutar/123".
 *
 * Rules:
 *  - Locale prefixes (2-letter ISO codes) are skipped silently.
 *  - UUID segments are skipped (detail pages — no readable label).
 *  - Unknown segments use the raw segment as label (no href skip).
 *  - Last crumb gets no href (current page indicator).
 */
export function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean)
  const items: BreadcrumbItem[] = [{ label: "Início", href: "/" }]

  let currentPath = ""
  for (const segment of segments) {
    currentPath += `/${segment}`

    // skip locale prefixes ("pt", "en", "pt-BR")
    if (LOCALE_RE.test(segment) && segment.length <= 5) continue

    // skip UUIDs
    if (UUID_RE.test(segment)) continue

    const label = ALL_LABELS[segment] ?? segment
    items.push({ label, href: currentPath })
  }

  // Last item should not be a link (current page)
  if (items.length > 1) {
    items[items.length - 1] = { label: items[items.length - 1].label }
  }

  return items
}

/**
 * Universal breadcrumb navigation component.
 *
 * Renders null on root ("/") or when only one crumb would show (no trail).
 * Place inside the dashboard layout above `{children}` for automatic
 * path-based breadcrumbs, or supply `items` for manual override.
 *
 * @example
 * // Auto mode (uses pathname)
 * <Breadcrumbs />
 *
 * @example
 * // Manual override
 * <Breadcrumbs items={[
 *   { label: "Recrutar", href: "/pt/recrutar" },
 *   { label: "Vaga: Dev Sênior" },
 * ]} />
 */
export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  const pathname = usePathname()
  const crumbs = items ?? generateBreadcrumbs(pathname)

  // Don't render if only "Início" or nothing
  if (crumbs.length <= 1) return null

  return (
    <nav aria-label="Localização atual" className={cn(
      "flex items-center gap-1 text-sm text-muted-foreground",
      className,
    )}>
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1
        return (
          <span key={`${crumb.label}-${index}`} className="flex items-center gap-1">
            {index > 0 && (
              <ChevronRight className="h-3.5 w-3.5 flex-shrink-0 text-muted-foreground/50" aria-hidden />
            )}
            {index === 0 && (
              <Home className="h-3.5 w-3.5 flex-shrink-0" aria-hidden />
            )}
            {isLast || !crumb.href ? (
              <span
                className="font-medium text-foreground"
                aria-current={isLast ? "page" : undefined}
              >
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="hover:text-foreground transition-colors"
              >
                {crumb.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
