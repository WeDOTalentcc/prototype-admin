"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { ChevronDown, ChevronUp, Database, Key, ShieldCheck } from "lucide-react"
import { useTranslations } from "next-intl"
import { Chip } from "@/components/ui/chip"

interface LlmConfigData {
  company_id: string
  primary_provider: string
  fallback_order: string[]
  providers: Record<string, { api_key?: string; model?: string; is_active?: boolean }>
  routing: Record<string, string>
  is_active: boolean
}

interface EmbeddingTransparencyCardProps {
  llmConfig: LlmConfigData | null | undefined
  isLoading?: boolean
}

const EMBEDDING_SURFACES = [
  "chatMemory",
  "candidateSearch",
  "similarJobs",
  "jdSimilar",
  "domainContent",
] as const

type SurfaceKey = (typeof EMBEDDING_SURFACES)[number]

export function EmbeddingTransparencyCard({ llmConfig, isLoading }: EmbeddingTransparencyCardProps) {
  const t = useTranslations("settings")
  const [expanded, setExpanded] = useState(false)

  const embeddingProvider = llmConfig?.routing?.embedding ?? null
  const providerLabel = embeddingProvider
    ? embeddingProvider.charAt(0).toUpperCase() + embeddingProvider.slice(1)
    : t("integrations.embedding.providerDefault")

  const byokConfigured = embeddingProvider
    ? !!(llmConfig?.providers?.[embeddingProvider]?.api_key)
    : false

  const byokStatus = byokConfigured
    ? t("integrations.embedding.byokConfigured")
    : t("integrations.embedding.byokManaged")

  if (isLoading) {
    return (
      <div
        className={cn(cardStyles.default, "p-4 mb-4 animate-pulse")}
        aria-busy="true"
        aria-label={t("integrations.embedding.title")}
      >
        <div className="h-4 w-48 bg-lia-border-subtle rounded mb-2" />
        <div className="h-3 w-72 bg-lia-border-subtle rounded" />
      </div>
    )
  }

  return (
    <div
      className={cn(cardStyles.default, "p-4 mb-4")}
      data-testid="embedding-transparency-card"
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="w-9 h-9 rounded-md flex items-center justify-center flex-shrink-0 bg-lia-bg-tertiary text-lia-text-secondary">
            <Database className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h3 className={cn(textStyles.h3)}>
              {t("integrations.embedding.title")}
            </h3>
            <p className={cn(textStyles.description, "mt-0.5")}>
              {t("integrations.embedding.description")}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <Chip variant="neutral" muted className="text-[10px] px-2 py-0.5 gap-1">
                <span className="font-medium">{t("integrations.embedding.providerLabel")}:</span>
                {" "}{providerLabel}
              </Chip>
              {byokConfigured ? (
                <Chip variant="success" className="text-[10px] px-2 py-0.5 gap-1">
                  <Key className="w-3 h-3" />
                  {byokStatus}
                </Chip>
              ) : (
                <Chip variant="neutral" className="text-[10px] px-2 py-0.5 gap-1 text-lia-text-secondary">
                  <ShieldCheck className="w-3 h-3" />
                  {byokStatus}
                </Chip>
              )}
            </div>
          </div>
        </div>
        <button
          type="button"
          className="flex-shrink-0 flex items-center gap-1 text-[11px] text-lia-text-tertiary hover:text-lia-text-secondary transition-colors mt-1"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          aria-controls="embedding-surfaces-table"
          data-testid="embedding-transparency-toggle"
        >
          {expanded ? (
            <>
              {t("integrations.embedding.hideSurfaces")}
              <ChevronUp className="w-3.5 h-3.5" />
            </>
          ) : (
            <>
              {t("integrations.embedding.showSurfaces")}
              <ChevronDown className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </div>

      {/* Collapsible surfaces table */}
      {expanded && (
        <div id="embedding-surfaces-table" className="mt-4">
          <table
            className="w-full text-[11px]"
            role="table"
            aria-label={t("integrations.embedding.surfacesTableLabel")}
          >
            <thead>
              <tr className="border-b border-lia-border-subtle">
                <th className={cn(textStyles.label, "text-left pb-2 font-semibold pr-3 w-[30%]")}>
                  {t("integrations.embedding.colSurface")}
                </th>
                <th className={cn(textStyles.label, "text-left pb-2 font-semibold pr-3 w-[40%]")}>
                  {t("integrations.embedding.colContent")}
                </th>
                <th className={cn(textStyles.label, "text-left pb-2 font-semibold w-[30%]")}>
                  {t("integrations.embedding.colPiiPolicy")}
                </th>
              </tr>
            </thead>
            <tbody>
              {EMBEDDING_SURFACES.map((key: SurfaceKey, idx: number) => (
                <tr
                  key={key}
                  className={cn(
                    "border-b border-lia-border-subtle last:border-0",
                    idx % 2 !== 0 ? "bg-lia-bg-secondary/40" : ""
                  )}
                >
                  <td className={cn(textStyles.description, "py-2 pr-3 font-medium align-top")}>
                    {t(`integrations.embedding.surface.${key}.name`)}
                  </td>
                  <td className={cn(textStyles.description, "py-2 pr-3 align-top")}>
                    {t(`integrations.embedding.surface.${key}.content`)}
                  </td>
                  <td className="py-2 align-top">
                    <Chip variant="neutral" muted className="text-[10px] px-1.5 py-0.5">
                      {t(`integrations.embedding.surface.${key}.piiPolicy`)}
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className={cn(textStyles.caption, "mt-3 text-lia-text-tertiary")}>
            {t("integrations.embedding.presidioNote")}
          </p>
        </div>
      )}
    </div>
  )
}
