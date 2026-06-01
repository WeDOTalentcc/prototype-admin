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
  fairness_flagged?: boolean
  fairness_category?: string | null
  needs_manual_review?: boolean
  evaluation_failed?: boolean
  failure_reason?: string | null
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

type ScanSample = { decision: string; role: string | null; skills: string[]; summary: string }
type ScanPreview = {
  evaluator_name?: string
  decisions_found: number
  approved_count: number
  rejected_count: number
  sample_decisions: ScanSample[]
  has_enough: boolean
  bias_audit?: { passed: boolean; flags: string[] }
}

export function CreateDigitalTwinModal({ isOpen, onClose, onCreated }: CreateDigitalTwinModalProps) {
  const t = useTranslations("agents.studio.twins.createModal")
  const [step, setStep] = useState<"select" | "scanning" | "preview">("select")
  const [specialists, setSpecialists] = useState<Array<{ id: string; name: string; email: string; role: string }>>([])
  const [selectedId, setSelectedId] = useState("")
  const [twinName, setTwinName] = useState("")
  const [specialty, setSpecialty] = useState("")
  const [description, setDescription] = useState("")
  const [monthsBack, setMonthsBack] = useState(12)
  const [preview, setPreview] = useState<ScanPreview | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const authHeaders = (): Record<string, string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
    const h: Record<string, string> = { "Content-Type": "application/json" }
    if (token) h.Authorization = `Bearer ${token}`
    return h
  }

  useEffect(() => {
    if (!isOpen) return
    fetch("/api/backend-proxy/company/users/list", { headers: authHeaders(), credentials: "include" })
      .then((r) => (r.ok ? r.json() : { users: [] }))
      .then((d) => {
        const us = Array.isArray(d?.users) ? d.users : []
        setSpecialists(
          us
            .filter((u: { email?: string }) => (u.email || "").includes("@"))
            .map((u: { id: string; name: string; email: string; role: string }) => ({
              id: String(u.id), name: u.name, email: u.email, role: u.role,
            })),
        )
      })
      .catch(() => {})
  }, [isOpen])

  const reset = () => {
    setStep("select"); setSelectedId(""); setTwinName(""); setSpecialty("")
    setDescription(""); setMonthsBack(12); setPreview(null); setError(null); setIsCreating(false)
  }
  const handleClose = () => { reset(); onClose() }

  const handleScan = async () => {
    if (!selectedId) return
    setError(null); setStep("scanning")
    try {
      const res = await fetch("/api/backend-proxy/digital-twins/scan-preview", {
        method: "POST", headers: authHeaders(), credentials: "include",
        body: JSON.stringify({ sme_user_id: selectedId, months_back: monthsBack }),
      })
      if (!res.ok) throw new Error(String(res.status))
      const data: ScanPreview = await res.json()
      setPreview(data)
      if (!twinName.trim() && data.evaluator_name) setTwinName(t("namePrefill", { name: data.evaluator_name }))
      setStep("preview")
    } catch {
      setError(t("scan.error")); setStep("select")
    }
  }

  const handleCreate = async () => {
    if (!selectedId || !twinName.trim()) return
    setIsCreating(true)
    try {
      const res = await fetch("/api/backend-proxy/digital-twins", {
        method: "POST", headers: authHeaders(), credentials: "include",
        body: JSON.stringify({
          twin_name: twinName.trim(),
          sme_user_id: selectedId,
          specialties: specialty.split(",").map((x) => x.trim()).filter(Boolean),
          description: description.trim() || null,
          months_back: monthsBack,
        }),
      })
      if (res.ok) { toast.success(t("successTitle"), t("successDesc")); handleClose(); onCreated?.() }
      else { toast.error(t("errorTitle"), t("errorDesc")) }
    } catch { toast.error(t("errorTitle"), t("errorDesc")) }
    finally { setIsCreating(false) }
  }

  const lgpdFootnote = (
    <details className="text-[11px] text-lia-text-disabled mt-1">
      <summary className="cursor-pointer flex items-center gap-1 list-none select-none">
        <Info className="w-3 h-3 shrink-0" aria-hidden="true" />
        <span>{t("lgpd.footnote")} <span className="underline">{t("lgpd.learnMore")}</span></span>
      </summary>
      <div className="mt-1 pl-4 space-y-1 text-lia-text-secondary">
        <p>{t("lgpd.detail.indexing")}</p>
        <p>{t("lgpd.detail.storage")}</p>
        <p>{t("lgpd.detail.confirmation")}</p>
      </div>
    </details>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg bg-lia-bg-primary border-lia-border-subtle max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            <Users2 className="w-5 h-5 inline mr-2 text-graphite" />
            {t("title")}
          </DialogTitle>
          <DialogDescription className="text-sm text-lia-text-secondary">
            {t("subtitle")}
          </DialogDescription>
        </DialogHeader>

        {step === "select" && (
          <div className="space-y-4 py-2">
            <div className={formStyles.fieldGroup}>
              <label className={formStyles.labelRequired}>{t("specialist.label")}</label>
              <select
                className={inputStyles.default + " w-full"}
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
              >
                <option value="">{t("specialist.placeholder")}</option>
                {specialists.map((sp) => (
                  <option key={sp.id} value={sp.id}>{sp.name} {sp.role ? "— " + sp.role : ""}</option>
                ))}
              </select>
              <p className={formStyles.helperText}>
                <Info className="w-3 h-3 inline mr-1" />
                {specialists.length === 0 ? t("specialist.empty") : t("specialist.help")}
              </p>
            </div>

            <div className={formStyles.fieldGroup}>
              <label className={formStyles.label}>{t("period.label")}</label>
              <select
                className={inputStyles.default + " w-full"}
                value={monthsBack}
                onChange={(e) => setMonthsBack(Number(e.target.value))}
              >
                <option value={6}>{t("period.months", { n: 6 })}</option>
                <option value={12}>{t("period.months", { n: 12 })}</option>
                <option value={24}>{t("period.months", { n: 24 })}</option>
              </select>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}
            {lgpdFootnote}
          </div>
        )}

        {step === "scanning" && (
          <div className="flex flex-col items-center justify-center gap-3 py-12">
            <Users2 className="w-8 h-8 text-graphite animate-pulse" />
            <p className={textStyles.bodySmall}>{t("scan.title")}</p>
          </div>
        )}

        {step === "preview" && preview && (
          <div className="space-y-4 py-2">
            <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4 space-y-2">
              <p className={textStyles.bodySmall}>
                {t("preview.foundCount", { count: preview.decisions_found, name: preview.evaluator_name || "" })}
              </p>
              <div className="flex items-center gap-4">
                <span className="inline-flex items-center gap-1 text-sm text-lia-text-secondary">
                  <ThumbsUp className="w-3.5 h-3.5 text-emerald-600" /> {preview.approved_count} {t("preview.approved")}
                </span>
                <span className="inline-flex items-center gap-1 text-sm text-lia-text-secondary">
                  <ThumbsDown className="w-3.5 h-3.5 text-rose-500" /> {preview.rejected_count} {t("preview.rejected")}
                </span>
              </div>
              {preview.bias_audit && (
                preview.bias_audit.passed
                  ? <Chip className="bg-emerald-50 text-emerald-700">{t("preview.biasAuditedBadge")}</Chip>
                  : <Chip className="bg-amber-50 text-amber-700">{t("preview.biasFlagged")}</Chip>
              )}
            </div>

            {preview.decisions_found === 0 ? (
              <div className="rounded-md bg-[#FEF9F0] border border-[#D19960]/30 p-3">
                <p className="text-sm text-[#D19960] font-medium">{t("preview.noDataTitle")}</p>
                <p className="text-xs text-[#D19960]">{t("preview.noDataDesc")}</p>
              </div>
            ) : (
              <>
                {!preview.has_enough && (
                  <p className="text-xs text-[#D19960]">{t("preview.lowDataWarning", { count: preview.decisions_found })}</p>
                )}
                <div>
                  <p className={textStyles.bodySmall + " font-semibold mb-1.5"}>{t("preview.examplesTitle")}</p>
                  <div className="space-y-1.5">
                    {preview.sample_decisions.map((sp, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-lia-text-secondary rounded-md border border-lia-border-subtle p-2">
                        {sp.decision === "approved"
                          ? <ThumbsUp className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                          : <ThumbsDown className="w-3.5 h-3.5 text-rose-500 mt-0.5 shrink-0" />}
                        <span>{sp.summary}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] italic text-lia-text-disabled">
                  <Info className="w-3 h-3 inline mr-1" />
                  {t("preview.reasoningInferred")}
                </p>
              </>
            )}

            {lgpdFootnote}
          </div>
        )}

        <DialogFooter>
          {step === "select" && (
            <>
              <Button className={buttonStyles.secondary} onClick={handleClose}>{t("cancel")}</Button>
              <Button className={buttonStyles.primary} onClick={handleScan} disabled={!selectedId}>
                {t("scan.cta")}
              </Button>
            </>
          )}
          {step === "preview" && (
            <>
              <Button className={buttonStyles.secondary} onClick={() => setStep("select")}>{t("preview.back")}</Button>
              <Button
                className={buttonStyles.primary}
                onClick={handleCreate}
                disabled={!twinName.trim() || isCreating || (preview?.decisions_found ?? 0) === 0}
              >
                {isCreating ? (<><Loader2 className="w-4 h-4 mr-1.5 animate-spin" />{t("creating")}</>) : (<><Plus className="w-4 h-4 mr-1.5" />{t("preview.confirmButton")}</>)}
              </Button>
            </>
          )}
        </DialogFooter>
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


interface EvaluateCandidateWithTwinModalProps {
  isOpen: boolean
  onClose: () => void
  candidateName: string
  candidateProfile: Record<string, unknown>
  jobContext: Record<string, unknown>
}

// "Second opinion" entry point used from the candidate card in the pipeline.
// Lists the company twins, lets the recruiter pick one, and shows how that
// specialist's twin would evaluate this candidate (with fairness flag).
export function EvaluateCandidateWithTwinModal({
  isOpen, onClose, candidateName, candidateProfile, jobContext,
}: EvaluateCandidateWithTwinModalProps) {
  const t = useTranslations("agents.studio.twins.evaluateCandidate")
  const [twins, setTwins] = useState<Array<{ id: string; twin_name: string }>>([])
  const [twinId, setTwinId] = useState("")
  const [evaluation, setEvaluation] = useState<TwinEvaluation | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const authHeaders = (): Record<string, string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
    const h: Record<string, string> = { "Content-Type": "application/json" }
    if (token) h.Authorization = `Bearer ${token}`
    return h
  }

  useEffect(() => {
    if (!isOpen) return
    setEvaluation(null); setTwinId("")
    fetch("/api/backend-proxy/digital-twins", { headers: authHeaders(), credentials: "include" })
      .then((r) => (r.ok ? r.json() : { twins: [] }))
      .then((d) => {
        const arr = Array.isArray(d?.twins) ? d.twins : Array.isArray(d) ? d : []
        setTwins(arr.map((x: { id?: string; twin_id?: string; twin_name?: string; name?: string }) => ({
          id: String(x.id ?? x.twin_id), twin_name: x.twin_name ?? x.name ?? "",
        })))
      })
      .catch(() => {})
  }, [isOpen])

  const runEval = async (id: string) => {
    setIsLoading(true); setEvaluation(null)
    try {
      const res = await fetch(`/api/backend-proxy/digital-twins/${id}/evaluate`, {
        method: "POST", headers: authHeaders(), credentials: "include",
        body: JSON.stringify({ candidate_profile: candidateProfile, job_context: jobContext, k: 5 }),
      })
      setEvaluation(await res.json())
    } catch {
      /* surfaced via empty state */
    } finally {
      setIsLoading(false)
    }
  }

  const decisionLabel = (d?: string) =>
    d === "approved" ? t("decisionApproved") : d === "rejected" ? t("decisionRejected") : t("decisionMaybe")

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg bg-lia-bg-primary border-lia-border-subtle max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            <Users2 className="w-5 h-5 inline mr-2 text-graphite" />
            {t("title", { name: candidateName })}
          </DialogTitle>
          <DialogDescription className="text-sm text-lia-text-secondary">{t("subtitle")}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className={formStyles.fieldGroup}>
            <label className={formStyles.label}>{t("pickTwin")}</label>
            <select
              className={inputStyles.default + " w-full"}
              value={twinId}
              onChange={(e) => { setTwinId(e.target.value); if (e.target.value) runEval(e.target.value) }}
            >
              <option value="">{t("pickTwinPlaceholder")}</option>
              {twins.map((tw) => (
                <option key={tw.id} value={tw.id}>{tw.twin_name}</option>
              ))}
            </select>
            {twins.length === 0 && <p className={formStyles.helperText}>{t("noTwins")}</p>}
          </div>

          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
              <Loader2 className="w-4 h-4 animate-spin" /> {t("evaluating")}
            </div>
          )}

          {evaluation && !isLoading && (
            <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary p-4 space-y-2">
              <div className="flex items-center gap-2">
                {evaluation.decision === "approved"
                  ? <ThumbsUp className="w-4 h-4 text-emerald-600" />
                  : evaluation.decision === "rejected"
                    ? <ThumbsDown className="w-4 h-4 text-rose-500" />
                    : <Info className="w-4 h-4 text-lia-text-secondary" />}
                <span className="font-semibold text-lia-text-primary">{decisionLabel(evaluation.decision)}</span>
                <span className="text-sm text-lia-text-secondary">
                  · {evaluation.score}/100 · {Math.round((evaluation.confidence || 0) * 100)}%
                </span>
              </div>
              {evaluation.reasoning && <p className="text-sm text-lia-text-secondary">{evaluation.reasoning}</p>}
              {evaluation.fairness_flagged && (
                <Chip className="bg-amber-50 text-amber-700">{t("fairnessFlagged")}</Chip>
              )}
              {evaluation.needs_manual_review && (
                <p className="text-xs text-[#D19960]">{t("needsReview")}</p>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button className={buttonStyles.secondary} onClick={onClose}>{t("close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
