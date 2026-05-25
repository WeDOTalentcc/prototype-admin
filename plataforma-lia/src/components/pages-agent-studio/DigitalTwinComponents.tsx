"use client"

import React, { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { AlertCircle, ArrowRight, BookOpen, ChevronRight, FileText, HelpCircle, Info, Lightbulb, Loader2, Plus, Star, ThumbsDown, ThumbsUp, Upload, UserCheck, Users, Users2, X, Zap } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
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

const HOW_IT_WORKS_ICONS = [UserCheck, BookOpen, Users2, Lightbulb] as const

export function DigitalTwinHeader() {
  const t = useTranslations("agents.studio.twins")

  return (
    <TabSectionHeader
      title={t("headerTitle")}
      subtitle={t("headerDesc")}
    />
  )
}

// Wave 4 W4-5 audit 2026-05-22: banner dismissivel explicando diferencial competitivo
// (Twin de decisor humano-avaliador eh unico no mercado HR-tech;
// Eightfold Andromeda eh employee twin = caso de uso diferente).
export function TwinCompetitiveBanner() {
  const [dismissed, setDismissed] = React.useState(false)

  React.useEffect(() => {
    const seen = localStorage.getItem("wedo_twin_competitive_banner_dismissed")
    if (seen === "1") setDismissed(true)
  }, [])

  if (dismissed) return null

  const handleDismiss = () => {
    localStorage.setItem("wedo_twin_competitive_banner_dismissed", "1")
    setDismissed(true)
  }

  return (
    <div
      className="relative rounded-xl border border-lia-border-default bg-lia-bg-secondary p-4"
      role="region"
      aria-label="Diferencial competitivo Gemeos Digitais"
    >
      <button
        type="button"
        onClick={handleDismiss}
        className="absolute top-3 right-3 p-1 rounded-md text-lia-text-disabled hover:text-lia-text-primary hover:bg-lia-bg-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
        aria-label="Dispensar banner"
      >
        <X className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
      <div className="flex items-start gap-3 pr-8">
        <div className="rounded-lg bg-powder p-2 flex-shrink-0">
          <Zap className="w-5 h-5 text-graphite" aria-hidden="true" />
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-graphite uppercase tracking-wide">
              Diferencial WeDOTalent
            </span>
            <span className={cn(badgeStyles.default, "text-[10px] font-semibold")}>
              Unico no mercado HR-tech
            </span>
          </div>
          <h4 className="text-sm font-semibold text-lia-text-primary">
            Clone o raciocinio do seu melhor entrevistador
          </h4>
          <p className="text-xs text-lia-text-secondary leading-relaxed">
            Diferente do <strong>Eightfold Andromeda</strong> (que clona funcionarios para
            career planning) ou de assistentes generalistas, o Digital Twin da WeDOTalent
            cria uma <strong>copia comportamental do seu decisor humano de hiring</strong> —
            o entrevistador top que voce confia mais. A IA aprende o padrao especifico de
            avaliacao dele e oferece <strong>segunda opiniao automatica</strong> em novos
            candidatos, no estilo dele.
          </p>
          <p className="text-xs text-lia-text-secondary leading-relaxed">
            Combinado com PT-BR nativo + LGPD compliance built-in (Art. 18 erasure via
            FK SET NULL), eh um pacote diferenciador unico globalmente.
          </p>
        </div>
      </div>
    </div>
  )
}


export function DigitalTwinOnboarding() {
  const t = useTranslations("agents.studio.twins")
  const tOnboarding = useTranslations("agents.studio.twins.onboarding")
  const { persona: aiPersona } = useAiPersona()
  const aiAssistantName = aiPersona?.name ?? "assistente"

  const steps = [
    { icon: HOW_IT_WORKS_ICONS[0], title: tOnboarding("step1Title"), desc: tOnboarding("step1Desc") },
    { icon: HOW_IT_WORKS_ICONS[1], title: tOnboarding("step2Title"), desc: tOnboarding("step2Desc") },
    { icon: HOW_IT_WORKS_ICONS[2], title: tOnboarding("step3Title", { aiAssistant: aiAssistantName }), desc: tOnboarding("step3Desc") },
    { icon: HOW_IT_WORKS_ICONS[3], title: tOnboarding("step4Title"), desc: tOnboarding("step4Desc") },
  ]

  return (
    <section className="relative overflow-hidden rounded-xl border border-lia-border-subtle bg-gradient-to-br from-lia-bg-secondary to-lia-bg-primary p-6">
      <div className="relative">
        <div className="flex items-center gap-2 mb-1">
          <Users className="w-4 h-4 text-graphite" />
          <span className="text-xs font-semibold uppercase tracking-wider text-graphite">
            {t("label")}
          </span>
        </div>
        <p className="text-base font-semibold text-lia-text-primary mb-2" role="heading" aria-level={2}>
          {t("headerTitle")}
        </p>
        <p className="text-sm text-lia-text-secondary mb-6 max-w-2xl">
          {t("headerDesc")}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {steps.map((step, i) => {
            const Icon = step.icon
            return (
              <div key={i} className="flex items-start gap-3 min-w-0">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 bg-cyan-50 dark:bg-cyan-950/30">
                  <Icon className="w-5 h-5 text-graphite" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[10px] font-bold text-lia-text-disabled uppercase whitespace-nowrap">
                      {tOnboarding("stepLabel", { number: i + 1 })}
                    </span>
                    {i < steps.length - 1 && <ArrowRight className="w-3 h-3 text-lia-text-disabled hidden xl:block" />}
                  </div>
                  <p className="text-xs font-semibold text-lia-text-primary break-words">{step.title}</p>
                  <p className="text-[11px] text-lia-text-secondary leading-relaxed break-words">{step.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
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
      <div className="flex items-center justify-center w-12 h-12 rounded-md bg-cyan-50 dark:bg-cyan-950/30 mb-4">
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
          // Wave 3 #17 audit 2026-05-22: LGPD disclosure step canonical
          <div className="space-y-4 py-2">
            <div className="rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-300">
                    Aviso LGPD — Indexação de Decisões Históricas
                  </h4>
                  <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                    Esta funcionalidade indexa decisões históricas (aprovações,
                    rejeições, raciocínios) do avaliador escolhido para que a IA
                    aprenda o padrão e ofereça segunda opinião automática.
                  </p>
                  <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                    Armazena referências ao candidato (candidate_id) e snapshots
                    sem PII direta (sem nome), conforme LGPD Art. 6 + Art. 11.
                    Embeddings derivam do raciocínio do avaliador, não dos dados
                    pessoais do candidato.
                  </p>
                  <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                    Ao confirmar você atesta que (1) candidatos foram informados
                    sobre análise comportamental no processo (LGPD Art. 11);
                    (2) o avaliador autorizou uso das decisões como treinamento;
                    (3) o sistema preserva direito de eliminação (LGPD Art. 18) —
                    referência no twin é anonimizada via FK SET NULL quando
                    candidato solicita exclusão.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                className={buttonStyles.secondary}
                onClick={handleClose}
                aria-label="Cancelar criação do Digital Twin"
              >
                Cancelar
              </Button>
              <Button
                onClick={() => setHasAcceptedDisclosure(true)}
                className={buttonStyles.primary}
                aria-label="Confirmo ciência LGPD e continuo para criação"
              >
                Confirmo — Continuar
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
          <Avatar className="w-10 h-10 bg-cyan-50 dark:bg-cyan-950/30">
            <AvatarFallback className="bg-cyan-50 dark:bg-cyan-950/30 text-graphite text-sm font-medium">
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
                  <Chip density="relaxed" variant="neutral" muted key={s} className="bg-cyan-50 dark:bg-cyan-950/30 text-graphite">
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
            <span className={cn(badgeStyles.default, "text-[10px] font-semibold ml-1")}>
              <Zap className="w-3 h-3 inline mr-0.5" aria-hidden="true" />
              Diferencial unico
            </span>
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
              <Avatar className="w-8 h-8 bg-cyan-50 dark:bg-cyan-950/30">
                <AvatarFallback className="bg-cyan-50 dark:bg-cyan-950/30 text-graphite text-xs">
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
              <blockquote className="mt-1 border-l-2 border-cyan-300 pl-3 italic text-lia-text-secondary">
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

  if (isLoading) return <p className={textStyles.caption}>{t("loadingTwins")}</p>
  if (twins.length === 0) {
    return (
      <div className="space-y-6">
        <TwinCompetitiveBanner />
        <DigitalTwinOnboarding />
        <DigitalTwinEmptyState onCreateTwin={onCreateTwin} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className={textStyles.caption}>
          {t("twinCount", { count: twins.length })}
        </p>
        <Button className={buttonStyles.primary} onClick={onCreateTwin}>
          <Plus className="w-4 h-4 mr-1.5" />
          {t("createNew")}
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {twins.map((tw) => (
          <TwinCard key={tw.id} twin={tw} onEvaluate={onEvaluate} />
        ))}
      </div>
    </div>
  )
}
