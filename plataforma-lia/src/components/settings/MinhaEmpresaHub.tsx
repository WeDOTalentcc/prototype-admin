"use client"

import React from "react"
import {
  Building, Heart, Code, Gift, Network, GitBranch, BarChart3, FileText,
  Loader2, RefreshCw, AlertCircle, CheckCircle, Upload,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { useSettingsConversational } from "@/hooks/settings/use-settings-conversational"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { textStyles } from "@/lib/design-tokens"
import { Globe } from "lucide-react"
import type { LucideIcon } from "lucide-react"

const ICON_MAP: Record<string, LucideIcon> = {
  Building,
  Heart,
  Code,
  Gift,
  Network,
  GitBranch,
  BarChart3,
  FileText,
  Upload,
}

export function MinhaEmpresaHub() {
  const t = useTranslations("settings.minhaEmpresa")
  const {
    blocks,
    benefits,
    companyId,
    loading,
    error,
    successMessage,
    overallProgress,
    expandedBlocks,
    recentlyUpdated,
    editingField,
    isSavingField,
    toggleBlock,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll,
  } = useCompanySettingsCards()

  const { triggerAction, triggerPrefillSection } = useSettingsConversational()

  const BLOCK_TO_PREFILL: Record<string, "culture" | "tech_stack" | "benefits" | "workforce" | "policy" | "compensation" | undefined> = {
    culture: "culture",
    tech: "tech_stack",
    benefits: "benefits",
    workforce: "workforce",
    policy: "policy",
    documents: "compensation",
  }

  const pendingSections = React.useMemo(
    () => blocks.filter((b) => b.progress.total > 0 && b.progress.filled < b.progress.total),
    [blocks],
  )
  const totalPendingFields = React.useMemo(
    () => pendingSections.reduce((acc, b) => acc + (b.progress.total - b.progress.filled), 0),
    [pendingSections],
  )

  const handleJumpToBlock = React.useCallback((blockKey: string) => {
    if (typeof window === "undefined") return
    if (!expandedBlocks.has(blockKey)) toggleBlock(blockKey)
    setTimeout(() => {
      const target = document.querySelector(
        `[data-block-anchor="${blockKey}"]`,
      ) as HTMLElement | null
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" })
    }, 60)
  }, [expandedBlocks, toggleBlock])

  const websiteUrl = React.useMemo(() => {
    const basicBlock = blocks.find((b) => b.key === "basic")
    return basicBlock?.fields.find((f) => f.key === "website")?.value as string | undefined
  }, [blocks])

  const handleAnalyzeWebsite = React.useCallback(() => {
    const urlTag = websiteUrl ? `\n[website_url:${websiteUrl}]` : ""
    triggerAction("analyze_website", {
      section: "minha-empresa",
      prompt:
        "[ACTION:analyze_website]" + urlTag + "\n\n" +
        t("analyzeWebsitePrompt"),
      source: "ui",
      autoSend: true,
    })
  }, [triggerAction, websiteUrl, t])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-label={t("loading")}>
        <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        <span className={`ml-2 ${textStyles.body}`}>
          {t("loadingCompanyData")}
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {(error || successMessage) && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
          error
            ? "bg-status-error/10 text-status-error border border-status-error/30"
            : "bg-status-success/10 text-status-success border border-status-success/30"
        }`}>
          {error ? <AlertCircle className="w-4 h-4 flex-shrink-0" /> : <CheckCircle className="w-4 h-4 flex-shrink-0" />}
          <span>{error || successMessage}</span>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className={textStyles.h3}>{t("title")}</h2>
            <p className={`${textStyles.description} mt-0.5`}>
              {t("description")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleAnalyzeWebsite}
              data-testid="analyze-website-cta"
              className="
                inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                bg-lia-bg-secondary dark:bg-lia-bg-elevated
                text-lia-text-primary border border-lia-border-subtle
                hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none
              "
              title={t("analyzeWebsiteTitle")}
            >
              <Globe className="w-3.5 h-3.5 text-wedo-cyan" aria-hidden />
              {t("analyzeWebsite")}
            </button>
            <button
              onClick={refreshAll}
              className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              aria-label={t("refreshData")}
            >
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
            </button>
            <span className={`${textStyles.metricSmall} flex-shrink-0`}>
              {t("configuredSuffix", { progress: overallProgress })}
            </span>
            {overallProgress >= 80 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30 flex-shrink-0">
                <CheckCircle className="w-3 h-3 mr-1" />
                {t("almostComplete")}
              </span>
            )}
          </div>
        </div>
        <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full transition-[width] duration-500 bg-lia-btn-primary-bg"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {totalPendingFields > 0 && (
        <div
          className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary/60 dark:bg-lia-bg-elevated px-3 py-2.5"
          data-testid="profile-progress-panel"
        >
          <div className="flex items-center justify-between mb-1.5">
            <p className={`${textStyles.captionBold} text-lia-text-primary`}>
              {t("profileCompletePending", { progress: overallProgress, count: totalPendingFields })}
            </p>
            <span className="text-micro text-lia-text-tertiary">
              {t("sectionsToReview", { count: pendingSections.length })}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {pendingSections.map((b) => {
              const remaining = b.progress.total - b.progress.filled
              const prefillKey = BLOCK_TO_PREFILL[b.key]
              return (
                <span key={b.key} className="inline-flex items-center gap-0.5">
                  <button
                    type="button"
                    onClick={() => handleJumpToBlock(b.key)}
                    data-testid={`pending-section-${b.key}`}
                    className="
                      inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium
                      bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle
                      text-lia-text-primary hover:border-lia-border-medium hover:bg-lia-bg-secondary
                      transition-colors motion-reduce:transition-none
                    "
                  >
                    {b.title}
                    <span className="text-lia-text-tertiary">({remaining})</span>
                  </button>
                  {prefillKey && (
                    <button
                      type="button"
                      onClick={() => triggerPrefillSection(prefillKey, b.progress.missingLabels)}
                      data-testid={`pending-prefill-${b.key}`}
                      className="
                        inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium
                        bg-lia-btn-primary-bg/10 text-lia-btn-primary-bg border border-lia-btn-primary-bg/30
                        hover:bg-lia-btn-primary-bg/20 transition-colors motion-reduce:transition-none
                      "
                      title={t("askLiaToFillTitle", { section: b.title })}
                    >
                      {t("askLiaShort")}
                    </button>
                  )}
                </span>
              )
            })}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {blocks.map((block) => (
          <MinhaEmpresaCard
            key={block.key}
            block={block}
            IconComp={ICON_MAP[block.iconName]}
            isExpanded={expandedBlocks.has(block.key)}
            recentlyUpdated={recentlyUpdated}
            editingField={editingField}
            isSavingField={isSavingField}
            benefits={benefits}
            companyId={companyId}
            onBenefitsChanged={refreshAll}
            onToggle={() => toggleBlock(block.key)}
            onStartEditing={startEditing}
            onCancelEditing={cancelEditing}
            onSaveField={saveField}
          />
        ))}
      </div>
    </div>
  )
}
