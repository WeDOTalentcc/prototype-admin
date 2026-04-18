"use client"

import React, { useCallback, useMemo } from "react"
import { useTranslations } from "next-intl"
import {
  Briefcase,
  Users,
  ExternalLink,
  Wand2,
  GitBranch,
  Database,
  FileText,
  Sparkles,
  ListChecks,
  ShieldCheck,
  Send,
  Radio,
  Archive,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useRouter } from "@/i18n/routing"
import {
  PipelineRail,
  type PipelineRailNode,
} from "@/components/pages/pipeline-overview/pipeline-rail"

export interface PipelineRailItemPreview {
  id: string
  label: string
  /** Optional secondary text (e.g. cargo, score, badge). */
  subtitle?: string
  /** Optional internal href (validated against allowlist). */
  href?: string
}

export interface PipelineRailStagePayload {
  key: string
  displayName: string
  color: string
  count: number
  /** Lucide icon name (lowercased, e.g. "briefcase", "users"). */
  icon?: string
  /** Up to 3 compact item previews shown beneath the rail. */
  items?: PipelineRailItemPreview[]
}

export interface PipelineRailCardData {
  mode: "vagas" | "candidatos"
  stages: PipelineRailStagePayload[]
  totalCount?: number
  jobId?: string
  jobTitle?: string
  /** Optional href para CTA "Continuar wizard" (já com locale handling pelo emissor). */
  wizardHref?: string
}

export interface PipelineRailCardProps {
  data: PipelineRailCardData
  className?: string
}

const ICON_MAP: Record<string, LucideIcon> = {
  briefcase: Briefcase,
  users: Users,
  database: Database,
  filetext: FileText,
  "file-text": FileText,
  sparkles: Sparkles,
  listchecks: ListChecks,
  "list-checks": ListChecks,
  shieldcheck: ShieldCheck,
  "shield-check": ShieldCheck,
  send: Send,
  radio: Radio,
  archive: Archive,
  gitbranch: GitBranch,
  "git-branch": GitBranch,
}

function resolveIcon(name?: string, fallback: LucideIcon = GitBranch): LucideIcon {
  if (!name) return fallback
  const key = name.toLowerCase().replace(/_/g, "-")
  return ICON_MAP[key] || ICON_MAP[key.replace(/-/g, "")] || fallback
}

/**
 * Allowlist de prefixos internos aceitos para `wizardHref`.
 * Qualquer href que não comece com um destes prefixos é rejeitado
 * (defesa contra open-redirect a partir de payload do backend).
 */
const SAFE_HREF_PREFIXES = [
  "/jobs",
  "/funil-de-talentos",
  "/visao-do-funil",
  "/criar-vaga",
  "/aprovacao",
  "/wsi",
] as const

function isSafeInternalHref(href: string | undefined): href is string {
  if (!href || typeof href !== "string") return false
  if (!href.startsWith("/")) return false
  if (href.startsWith("//")) return false
  return SAFE_HREF_PREFIXES.some((p) => href === p || href.startsWith(`${p}/`) || href.startsWith(`${p}?`))
}

export function PipelineRailCard({ data, className }: PipelineRailCardProps) {
  const t = useTranslations("chat.pipelineRailCard")
  const router = useRouter()

  const fallbackIcon = data?.mode === "vagas" ? Briefcase : Users

  const safeStages: PipelineRailStagePayload[] = useMemo(() => {
    if (!Array.isArray(data?.stages)) return []
    return data.stages
      .filter(
        (s): s is PipelineRailStagePayload =>
          !!s && typeof s.key === "string" && typeof s.displayName === "string"
      )
      .map((s) => ({
        ...s,
        items: Array.isArray(s.items)
          ? s.items
              .filter(
                (it): it is PipelineRailItemPreview =>
                  !!it && typeof it.id === "string" && typeof it.label === "string"
              )
              .slice(0, 3)
          : undefined,
      }))
  }, [data?.stages])

  const stagesWithItems = useMemo(
    () => safeStages.filter((s) => Array.isArray(s.items) && s.items!.length > 0),
    [safeStages]
  )

  const nodes = useMemo<PipelineRailNode[]>(() => {
    return safeStages.map((stage) => ({
      key: stage.key,
      displayName: stage.displayName,
      color: stage.color || "#2D2D2D",
      count: typeof stage.count === "number" ? stage.count : 0,
      Icon: resolveIcon(stage.icon, fallbackIcon),
      isSelected: false,
      onClick: () => {
        router.push(`/visao-do-funil?view=${data.mode}`)
      },
    }))
  }, [safeStages, data?.mode, fallbackIcon, router])

  const handleOpenFunnel = useCallback(() => {
    router.push(`/visao-do-funil?view=${data.mode}`)
  }, [router, data?.mode])

  const safeWizardHref = isSafeInternalHref(data?.wizardHref) ? data.wizardHref : undefined

  const handleContinueWizard = useCallback(() => {
    if (safeWizardHref) {
      router.push(safeWizardHref)
    }
  }, [router, safeWizardHref])

  const total =
    typeof data?.totalCount === "number"
      ? data.totalCount
      : safeStages.reduce((acc, s) => acc + (typeof s.count === "number" ? s.count : 0), 0)

  if (!data || (data.mode !== "vagas" && data.mode !== "candidatos")) {
    return null
  }

  return (
    <div
      data-testid="pipeline-rail-card"
      className={cn(
        "mt-2 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-3",
        "shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          {data.mode === "vagas" ? (
            <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
          ) : (
            <Users className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
          )}
          <span className="text-xs font-medium text-lia-text-primary truncate">
            {data.jobTitle || t(data.mode === "vagas" ? "titleVacancies" : "titleCandidates")}
          </span>
        </div>
        <span className="text-micro text-lia-text-disabled flex-shrink-0">
          {t(data.mode === "vagas" ? "totalVacancies" : "totalCandidates", { count: total })}
        </span>
      </div>

      <div className="-mx-1">
        <PipelineRail
          nodes={nodes}
          emptyMessage={
            <p className="text-micro text-lia-text-disabled px-2 py-3">
              {t("empty")}
            </p>
          }
        />
      </div>

      {stagesWithItems.length > 0 && (
        <div className="mt-2 space-y-1.5">
          {stagesWithItems.map((stage) => (
            <div key={stage.key} className="flex flex-col gap-1">
              <div className="flex items-center gap-1.5 px-1">
                <span
                  className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: stage.color || "#2D2D2D" }}
                />
                <span className="text-micro font-medium text-lia-text-secondary truncate">
                  {stage.displayName}
                </span>
                <span className="text-micro text-lia-text-disabled">·</span>
                <span className="text-micro text-lia-text-disabled">{stage.count}</span>
              </div>
              <ul className="flex flex-wrap gap-1 px-1">
                {stage.items!.map((item) => {
                  const itemHref = isSafeInternalHref(item.href) ? item.href : undefined
                  const content = (
                    <div className="flex items-center gap-1 max-w-[180px]">
                      <span className="truncate">{item.label}</span>
                      {item.subtitle ? (
                        <span className="text-lia-text-disabled truncate">· {item.subtitle}</span>
                      ) : null}
                    </div>
                  )
                  return (
                    <li key={item.id}>
                      {itemHref ? (
                        <button
                          type="button"
                          onClick={() => router.push(itemHref)}
                          className="text-micro px-1.5 py-0.5 rounded border border-lia-border-subtle bg-lia-bg-tertiary hover:bg-lia-bg-hover text-lia-text-primary transition-colors"
                        >
                          {content}
                        </button>
                      ) : (
                        <span className="text-micro px-1.5 py-0.5 rounded border border-lia-border-subtle bg-lia-bg-tertiary text-lia-text-primary">
                          {content}
                        </span>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 mt-2 pt-2 border-t border-lia-border-subtle/50">
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs gap-1.5"
          onClick={handleOpenFunnel}
        >
          <ExternalLink className="w-3 h-3" />
          {t("openFunnel")}
        </Button>
        {data.wizardHref ? (
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs gap-1.5 text-wedo-cyan hover:text-wedo-cyan-dark"
            onClick={handleContinueWizard}
          >
            <Wand2 className="w-3 h-3" />
            {t("continueWizard")}
          </Button>
        ) : null}
      </div>
    </div>
  )
}

export default PipelineRailCard
