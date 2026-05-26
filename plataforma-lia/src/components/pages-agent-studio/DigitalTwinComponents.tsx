"use client"

import React, { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { ChevronDown, ChevronRight, FileText, HelpCircle, Info, Loader2, Plus, Star, ThumbsDown, ThumbsUp, Upload, Users2, X } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles, inputStyles, formStyles
} from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"

interface DigitalTwin {
  id: string
  twin_name: string
  specialties: string[]
  description: string | null
  decision_count: number
  accuracy_pct: number | null
  is_active: boolean
  created_at: string
}

interface TwinEvaluation {
  twin_id: string
  twin_name: string
  score: number
  decision: "approved" | "rejected" | "maybe"
  reasoning: string
  confidence: number
  supporting_examples: Array<{
    decision: string
    reasoning: string
    similarity: number
  }>
}

// P0 rewrite 2026-05-26 (Paulo): página Gêmeos Digitais agora segue layout canonical
// idêntico Marketplace/Personalizados — header + sub-header neutro + grid cards + CTA.
// REMOVIDOS: TwinCompetitiveBanner (citava concorrente Eightfold), DigitalTwinOnboarding
// (4 cards horizontais "Passo 1-4"), e marketing copy ("DIFERENCIAL", "Unico no mercado",
// "globalmente", "built-in"). Vide CLAUDE.md "Quiet Operator" + memory
// project_white_label_ai_assistant.
export function DigitalTwinHeader() {
  const t = useTranslations("agents.studio.twins")

  return (
    <TabSectionHeader
      title={t("headerTitle")}
      subtitle={t("subheader")}
    />
  )
}

interface DigitalTwinEmptyStateProps {
  onCreateTwin: () => void
}

export function DigitalTwinEmptyState({ onCreateTwin }: DigitalTwinEmptyStateProps) {
  const t = useTranslations("agents.studio.twins.emptyState")
  const { persona: aiPersona } = useAiPersona()
  const aiAssistantName = aiPersona?.name ?? "assistente"

  return (
    <div className="flex flex-col items-center py-12 px-6">
      <div className="flex items-center justify-center w-12 h-12 rounded-md bg-lia-bg-tertiary mb-4">
        <Users2 className="w-6 h-6 text-graphite" />
      </div>
      <h3 className={`${textStyles.h3} text-center mb-1`}>{t("title")}</h3>
      <p className={`${textStyles.description} text-center max-w-md mb-6`}>
        {t("description")}
      </p>
      <Button className={buttonStyles.primary} onClick={onCreateTwin}>
        <Plus className="w-4 h-4 mr-1.5" />
        {t("createFirst")}
      </Button>
      <p className={`${textStyles.caption} mt-2 text-center`}>{t("noExperience", { aiAssistant: aiAssistantName })}</p>
    </div>
  )
}

interface CreateDigitalTwinModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated?: () => void
}

export function CreateDigitalTwinModal({ isOpen, onClose, onCreated }: CreateDigitalTwinModalProps) {
  const t = useTranslations("agents.studio.twins.createModal")
  const [twinName, setTwinName] = useState("")
  const [specialty, setSpecialty] = useState("")
  const [description, setDescription] = useState("")
  const [decisionsFile, setDecisionsFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  // Wave 3 #17 audit 2026-05-22: LGPD disclosure step antes do form de criação.
  const [hasAcceptedDisclosure, setHasAcceptedDisclosure] = useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const handleClose = () => {
    setTwinName("")
    setSpecialty("")
    setDescription("")
    setDecisionsFile(null)
    setHasAcceptedDisclosure(false)
    onClose()
  }

  const MAX_FILE_SIZE = 5 * 1024 * 1024

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    if (file && file.size > MAX_FILE_SIZE) {
      toast.error(t("fileTooLargeTitle"), t("fileTooLargeDesc"))
      if (fileInputRef.current) fileInputRef.current.value = ""
      return
    }
    setDecisionsFile(file)
  }

  const handleRemoveFile = () => {
    setDecisionsFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsText(file)
    })
  }

  const handleSubmit = async () => {
    if (!twinName.trim()) return
    setIsSubmitting(true)
    try {
      let decisionsData: string | null = null
      if (decisionsFile) {
        decisionsData = await readFileAsText(decisionsFile)
      }

      const res = await fetch("/api/backend-proxy/digital-twins", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          twin_name: twinName.trim(),
          specialties: specialty
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          description: description.trim() || null,
          decisions_data: decisionsData,
        }),
      })
      if (res.ok) {
        toast.success(t("successTitle"), t("successDesc"))
        handleClose()
        onCreated?.()
      } else {
        toast.error(t("errorTitle"), t("errorDesc"))
      }
    } catch {
      toast.error(t("errorTitle"), t("errorDesc"))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            <Users2 className="w-5 h-5 inline mr-2 text-graphite" />
            {t("title")}
          </DialogTitle>
          <DialogDescription className="text-sm text-lia-text-secondary">
            {t("subtitle")}
          </DialogDescription>
        </DialogHeader>

        {!hasAcceptedDisclosure ? (
          // P0 rewrite 2026-05-26 (Paulo): LGPD agora é Collapsible neutro DS.
          // Summary 1 linha visível default + click expande pro texto completo.
          // Compliance preservada (todo conteúdo Art. 6 + 11 + 18 acessível ao expandir).
          // Visual amber/yellow alarmista substituído por tokens canonical mist/graphite.
          <div className="space-y-4 py-2">
            <Collapsible defaultOpen={false} className="group">
              <CollapsibleTrigger className="w-full text-left p-3 rounded-md bg-lia-bg-tertiary border border-lia-border-medium hover:bg-lia-bg-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 text-lia-text-secondary flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <span className="text-sm text-lia-text-primary">
                      {t("lgpd.summary")}
                    </span>
                  </div>
                  <ChevronDown className="w-4 h-4 text-lia-text-secondary flex-shrink-0 mt-0.5 transition-transform group-data-[state=open]:rotate-180" aria-hidden="true" />
                </div>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle text-sm text-lia-text-secondary space-y-2">
                <p className="leading-relaxed">{t("lgpd.detail.indexing")}</p>
                <p className="leading-relaxed">{t("lgpd.detail.storage")}</p>
                <p className="leading-relaxed">{t("lgpd.detail.confirmation")}</p>
              </CollapsibleContent>
            </Collapsible>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                className={buttonStyles.secondary}
                onClick={handleClose}
                aria-label={t("lgpd.cancelAria")}
              >
                {t("cancel")}
              </Button>
              <Button
                onClick={() => setHasAcceptedDisclosure(true)}
                className={buttonStyles.primary}
                aria-label={t("lgpd.confirmAria")}
              >
                {t("lgpd.confirmButton")}
              </Button>
            </div>
          </div>
        ) : (
        <div className="space-y-4 py-2">
          <div className={formStyles.fieldGroup}>
            <label className={formStyles.labelRequired}>{t("nameLabel")}</label>
            <input
              className={inputStyles.default + " w-full"}
              placeholder={t("namePlaceholder")}
              value={twinName}
              onChange={(e) => setTwinName(e.target.value)}
            />
            <p className={formStyles.helperText}>
              <Info className="w-3 h-3 inline mr-1" />
              {t("nameHelp")}
            </p>
          </div>

          <div className={formStyles.fieldGroup}>
            <label className={formStyles.label}>{t("specialtyLabel")}</label>
            <input
              className={inputStyles.default + " w-full"}
              placeholder={t("specialtyPlaceholder")}
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
            />
            <p className={formStyles.helperText}>
              <Info className="w-3 h-3 inline mr-1" />
              {t("specialtyHelp")}
            </p>
          </div>

          <div className={formStyles.fieldGroup}>
            <label className={formStyles.label}>{t("descLabel")}</label>
            <textarea
              className={inputStyles.default + " w-full min-h-[80px] resize-none"}
              placeholder={t("descPlaceholder")}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
            <p className={formStyles.helperText}>
              <Info className="w-3 h-3 inline mr-1" />
              {t("descHelp")}
            </p>
          </div>

          <div className={formStyles.fieldGroup}>
            <label className={formStyles.label}>{t("decisionsLabel")}</label>
            <div
              className="relative rounded-lg border-2 border-dashed border-lia-border-default hover:border-pebble transition-colors p-4 cursor-pointer bg-lia-bg-secondary"
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              {decisionsFile ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-4 h-4 text-graphite shrink-0" />
                    <span className={`${textStyles.bodySmall} truncate`}>{decisionsFile.name}</span>
                    <span className={textStyles.caption}>
                      ({(decisionsFile.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleRemoveFile() }}
                    className="p-1 rounded hover:bg-lia-bg-tertiary"
                  >
                    <X className="w-3.5 h-3.5 text-lia-text-secondary" />
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-1.5 py-1">
                  <Upload className="w-5 h-5 text-slate" />
                  <p className={textStyles.bodySmall}>{t("decisionsUploadCta")}</p>
                  <p className={textStyles.caption}>{t("decisionsFormats")}</p>
                </div>
              )}
            </div>
            <p className={formStyles.helperText}>
              <Info className="w-3 h-3 inline mr-1" />
              {t("decisionsHelp")}
            </p>
          </div>
        </div>
        )}

        {hasAcceptedDisclosure && <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={handleClose}>
            {t("cancel")}
          </Button>
          <Button
            className={buttonStyles.primary}
            onClick={handleSubmit}
            disabled={!twinName.trim() || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                {t("creating")}
              </>
            ) : (
              <>
                <Plus className="w-4 h-4 mr-1.5" />
                {t("create")}
              </>
            )}
          </Button>
        </DialogFooter>}
      </DialogContent>
    </Dialog>
  )
}

interface TwinCardProps {
  twin: DigitalTwin
  onEvaluate?: (twinId: string) => void
  onManageTwin?: (twinId: string) => void
}

export function TwinCard({ twin, onEvaluate, onManageTwin }: TwinCardProps) {
  const t = useTranslations("agents.digitalTwin")
  const initials = twin.twin_name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase()

  return (
    <Card className={cardStyles.default}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Avatar className="w-10 h-10 bg-lia-bg-tertiary">
            <AvatarFallback className="bg-lia-bg-tertiary text-graphite text-sm font-medium">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className={textStyles.subtitle}>{twin.twin_name}</p>
              <Chip variant="neutral" muted className={twin.is_active ? badgeStyles.success : badgeStyles.warning}>
                {twin.is_active ? t("active") : t("inactive")}
              </Chip>
            </div>
            {twin.specialties.length > 0 && (
              <div className="flex gap-1 mt-1 flex-wrap">
                {twin.specialties.slice(0, 4).map((s) => (
                  <Chip density="relaxed" variant="neutral" muted key={s} className="bg-lia-bg-tertiary text-graphite">
                    {s}
                  </Chip>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 mt-3 text-sm text-lia-text-secondary">
          <span title={t("indexedDecisions")}>
            <Users2 className="w-3.5 h-3.5 inline mr-1" />
            {twin.decision_count}
          </span>
          {twin.accuracy_pct != null && (
            <span title={t("accuracy")}>
              <Star className="w-3.5 h-3.5 inline mr-1" />
              {twin.accuracy_pct}%
            </span>
          )}
        </div>

        <div className="flex gap-2 mt-3 pt-3 border-t border-lia-border-subtle">
          {onEvaluate && (
            <Button className={buttonStyles.primary} onClick={() => onEvaluate(twin.id)}>
              {t("evaluateCandidate")}
            </Button>
          )}
          {onManageTwin && (
            <Button className={buttonStyles.outline} onClick={() => onManageTwin(twin.id)}>
              {t("manage")} <ChevronRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

interface EvaluateWithTwinModalProps {
  twinId: string
  candidateProfile: Record<string, unknown>
  jobContext: Record<string, unknown>
  isOpen: boolean
  onClose: () => void
}

export function EvaluateWithTwinModal({
  twinId,
  candidateProfile,
  jobContext,
  isOpen,
  onClose,
}: EvaluateWithTwinModalProps) {
  const t = useTranslations("agents.digitalTwin")
  const [evaluation, setEvaluation] = useState<TwinEvaluation | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (isOpen && twinId) runEvaluation()
  }, [isOpen, twinId])

  const runEvaluation = async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`/api/backend-proxy/digital-twins/${twinId}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_profile: candidateProfile,
          job_context: jobContext,
          k: 5,
        }),
      })
      const data = await res.json()
      setEvaluation(data)
    } catch (err) {
      console.error("Twin evaluation failed:", err)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  const decisionConfig = {
    approved: { icon: ThumbsUp, color: "text-green-600", bg: "bg-green-50", label: t("approved") },
    rejected: { icon: ThumbsDown, color: "text-red-600", bg: "bg-red-50", label: t("rejected") },
    maybe: { icon: HelpCircle, color: "text-yellow-600", bg: "bg-yellow-50", label: t("maybe") },
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className={cn(textStyles.h3, "flex items-center gap-2 flex-wrap")}>
            <Users2 className="w-5 h-5 text-graphite" aria-hidden="true" />
            {t("digitalTwinEvaluation")}
          </DialogTitle>
          <DialogDescription className="sr-only">{t("evaluationResultDesc")}</DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex flex-col items-center py-8">
            <Users2 className="w-10 h-10 text-slate animate-pulse motion-reduce:animate-none mb-3" />
            <p className={textStyles.body}>{t("analyzingHistory")}</p>
            <p className={textStyles.caption}>{t("searchingSimilarDecisions")}</p>
          </div>
        ) : evaluation ? (
          <div className="space-y-4 py-4">
            <div className="flex items-center gap-2">
              <Avatar className="w-8 h-8 bg-lia-bg-tertiary">
                <AvatarFallback className="bg-lia-bg-tertiary text-graphite text-xs">
                  {evaluation.twin_name
                    .split(" ")
                    .map((w) => w[0])
                    .join("")
                    .slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className={textStyles.subtitle}>{evaluation.twin_name}</p>
                <p className={textStyles.caption}>{t("digitalTwin")}</p>
              </div>
            </div>

            {(() => {
              const dc = decisionConfig[evaluation.decision] || decisionConfig.maybe
              const Icon = dc.icon
              return (
                <div className={`flex items-center justify-between p-4 rounded-lg ${dc.bg}`}>
                  <div className="flex items-center gap-3">
                    <Icon className={`w-6 h-6 ${dc.color}`} />
                    <div>
                      <p className={`${textStyles.h4} ${dc.color}`}>{dc.label}</p>
                      <p className={textStyles.caption}>{t("twinDecision")}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`${textStyles.metricLarge} ${dc.color}`}>{evaluation.score}</p>
                    <p className={textStyles.caption}>/100</p>
                  </div>
                </div>
              )
            })()}

            <div>
              <div className="flex items-center justify-between mb-1">
                <span className={textStyles.label}>{t("confidence")}</span>
                <span className={textStyles.caption}>
                  {(evaluation.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={evaluation.confidence * 100} className="h-1.5" />
            </div>

            <div>
              <p className={textStyles.label}>{t("reasoning")}</p>
              <blockquote className="mt-1 border-l-2 border-lia-border-medium pl-3 italic text-lia-text-secondary">
                &ldquo;{evaluation.reasoning}&rdquo;
              </blockquote>
            </div>

            {evaluation.supporting_examples.length > 0 && (
              <div>
                <p className={`${textStyles.label} mb-2`}>{t("supportingDecisions")}</p>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {evaluation.supporting_examples.map((ex, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <Chip variant="neutral" muted
                        className={
                          ex.decision === "approved" ? badgeStyles.success : badgeStyles.error
                        }
                      >
                        {ex.decision === "approved" ? "✅" : "❌"}
                      </Chip>
                      <div className="min-w-0">
                        <p className={textStyles.bodySmall}>{ex.reasoning}</p>
                        <p className={textStyles.caption}>
                          {t("similarity")}: {(ex.similarity * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center py-8">
            <p className={textStyles.body}>{t("errorEvaluating")}</p>
          </div>
        )}

        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose}>
            {t("close")}
          </Button>
          {evaluation && (
            <Button className={buttonStyles.outline} onClick={runEvaluation}>
              {t("reevaluate")}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface TwinsListProps {
  onEvaluate?: (twinId: string) => void
  onCreateTwin: () => void
  refreshKey?: number
}

export function TwinsList({ onEvaluate, onCreateTwin, refreshKey = 0 }: TwinsListProps) {
  const t = useTranslations("agents.digitalTwin")
  const tTwins = useTranslations("agents.studio.twins")
  const [twins, setTwins] = useState<DigitalTwin[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadTwins()
  }, [refreshKey])

  const loadTwins = async () => {
    setIsLoading(true)
    try {
      const res = await fetch("/api/backend-proxy/digital-twins")
      const data = await res.json()
      setTwins(data?.twins || [])
    } catch {
    } finally {
      setIsLoading(false)
    }
  }

  // P0 rewrite 2026-05-26 (Paulo): layout canonical idêntico Marketplace/Personalizados.
  // Header (título + sub-header neutro) + CTA topo direito + grid cards OU empty state.
  // SEM banner concorrente, SEM 4 cards "Passo 1-4" — esses blocos foram removidos.
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2 max-w-2xl">
          <h2 className={textStyles.h3}>{tTwins("headerTitle")}</h2>
          <p className={textStyles.description}>{tTwins("subheader")}</p>
        </div>
        <Button className={buttonStyles.primary} onClick={onCreateTwin}>
          <Plus className="w-4 h-4 mr-1.5" />
          {tTwins("createCta")}
        </Button>
      </div>

      {isLoading ? (
        <p className={textStyles.caption}>{t("loadingTwins")}</p>
      ) : twins.length === 0 ? (
        <DigitalTwinEmptyState onCreateTwin={onCreateTwin} />
      ) : (
        <>
          <p className={textStyles.caption}>
            {t("twinCount", { count: twins.length })}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {twins.map((tw) => (
              <TwinCard key={tw.id} twin={tw} onEvaluate={onEvaluate} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
