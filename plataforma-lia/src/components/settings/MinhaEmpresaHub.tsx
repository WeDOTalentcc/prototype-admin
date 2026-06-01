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
import { LearningLoopsPanel } from "@/components/settings/LearningLoopsPanel"
import { LiaFieldsConfigPanel } from "@/components/settings/LiaFieldsConfigPanel"
import { AnalyzeWebsiteModal } from "@/components/settings/AnalyzeWebsiteModal"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import type { ProposedSaves } from "@/lib/website-proposal-mapper"
import { buildWebsiteProposalMessage } from "@/components/unified-chat/website-proposal-injector"
import { textStyles } from "@/lib/design-tokens"
import { Globe } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { HubHeader, HubLoadingState, HubErrorState } from "./_shared"
import { SettingsEditModeToggle } from "@/components/settings/SettingsEditModeToggle"
import { useSettingsEditMode } from "@/hooks/settings/useSettingsEditMode"

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

interface MinhaEmpresaHubProps {
  activeSubsection?: string
}

export function MinhaEmpresaHub({ activeSubsection }: MinhaEmpresaHubProps = {}) {
  // ─── TODOS OS HOOKS PRIMEIRO (rules-of-hooks, CLAUDE.md Sprint 1 Hardening 2026-05-26) ───
  // Early returns de subsection foram movidos para APÓS o último hook.
  // Antes estavam nas linhas 47-55 causando 14 violations detectadas pelo ESLint.
  // Padrão: BulkImportModal fix 2026-05-04 (CLAUDE.md "Frontend / React rules-of-hooks discipline").
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
    watchdogError,
  } = useCompanySettingsCards()

  const { triggerAction: _triggerAction, triggerPrefillSection } = useSettingsConversational()

  // Sprint B.7 (2026-05-26): wire edit-mode toggle aos campos do Card.
  // isEditing=true → comportamento atual. isEditing=false → read-only (esconde edit buttons, mostra hint).
  const { isEditing: isEditModeOn } = useSettingsEditMode("minha-empresa")

  const BLOCK_TO_PREFILL: Record<string, "basic" | "culture" | "tech_stack" | "benefits" | "workforce" | "policy" | "compensation" | undefined> = {
    basic: "basic",
    culture: "culture",
    tech: "tech_stack",
    benefits: "benefits",
    workforce: "workforce",
    policy: "policy",
    documents: "compensation",
  }

  const pendingSections = React.useMemo(
    // P1 dedup (2026-06-01): bloco "policy" migrou para o hub standalone
    // "Políticas de Recrutamento". Excluído daqui para não duplicar.
    () => blocks.filter((b) => b.key !== "policy" && b.progress.total > 0 && b.progress.filled < b.progress.total),
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

  const basicBlock = React.useMemo(
    () => blocks.find((b) => b.key === "basic"),
    [blocks],
  )
  const getBasicField = React.useCallback(
    (key: string) =>
      basicBlock?.fields.find((f) => f.key === key)?.value as string | undefined,
    [basicBlock],
  )
  const websiteUrl = getBasicField("website")

  // Task #1180 — botão "Analisar nosso site" agora abre o modal pré-análise
  const [analyzeModalOpen, setAnalyzeModalOpen] = React.useState(false)
  const handleAnalyzeWebsite = React.useCallback(() => {
    setAnalyzeModalOpen(true)
  }, [])

  const { setChatMessages } = useLiaChatContext()
  const handleProposed = React.useCallback(
    ({ proposed, companyId: cid }: { proposed: ProposedSaves; companyId: string }) => {
      setChatMessages((prev) => [...prev, buildWebsiteProposalMessage(proposed, cid)])
    },
    [setChatMessages],
  )

  // Card no chat dispara `lia:settings-updated` ao salvar — re-fetch.
  React.useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => refreshAll()
    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [refreshAll])

  const existingBasic = React.useMemo(
    () => ({
      industry: getBasicField("industry"),
      employee_count: getBasicField("employee_count"),
      company_size: getBasicField("company_size"),
      headquarters_city: getBasicField("headquarters_city"),
      headquarters_state: getBasicField("headquarters_state"),
      founded_year: getBasicField("founded_year"),
      work_model: getBasicField("work_model"),
      linkedin_url: getBasicField("linkedin_url"),
      logo_url: getBasicField("logo_url"),
    }),
    [getBasicField],
  )
  const companyName = getBasicField("name") ?? ""

  // ─── SUBSECTION ROUTING — APÓS TODOS OS HOOKS ────────────────────────────
  // Audit Sprint B Phase 2 (2026-05-05): Learning Loops panel.
  if (activeSubsection === "learning-loops") {
    return <LearningLoopsPanel />
  }

  // Audit 2026-05-20 Tema D / P1.8: 34 canonical LIA field definitions.
  if (activeSubsection === "instrucoes-lia") {
    return <LiaFieldsConfigPanel />
  }

  // ─── LOADING STATE ────────────────────────────────────────────
  if (watchdogError) {
    return <HubErrorState message={watchdogError} onRetry={refreshAll} />
  }
  if (loading) {
    return <HubLoadingState message={t("loadingCompanyData")} />
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
        <HubHeader title={t("title")} description={t("description")}>
          <div className="flex items-center gap-3">
            <SettingsEditModeToggle hubId="minha-empresa" />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAnalyzeWebsite}
              data-testid="analyze-website-cta"
              title={t("analyzeWebsiteTitle")}
              className="[&_svg]:size-3.5"
            >
              <Globe className="text-wedo-cyan" aria-hidden />
              {t("analyzeWebsite")}
            </Button>
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
        </HubHeader>
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
        {blocks.filter((b) => b.key !== "policy").map((block) => (
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
            isReadOnly={!isEditModeOn}
            onBenefitsChanged={refreshAll}
            onLogoUploaded={refreshAll}
            onToggle={() => toggleBlock(block.key)}
            onStartEditing={startEditing}
            onCancelEditing={cancelEditing}
            onSaveField={saveField}
          />
        ))}
      </div>

      <AnalyzeWebsiteModal
        open={analyzeModalOpen}
        onClose={() => setAnalyzeModalOpen(false)}
        initial={{
          companyName,
          websiteUrl,
          linkedinUrl: existingBasic.linkedin_url,
          companyId: companyId ?? undefined,
          existingBasic,
        }}
        onProposed={handleProposed}
      />
    </div>
  )
}
