"use client"

import React, { useState, useEffect } from"react"
import { useTranslations } from "next-intl"
import {
  ChevronLeft, ChevronRight, ThumbsUp, ThumbsDown, MessageSquare,
  X, CheckCircle, Edit3, Loader2, Users
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from"@/components/ui/dialog"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from"@/lib/design-tokens"
import { toast } from"@/lib/toast"

// ---------- Types ----------

interface MatchCriterion {
  criterion: string
  match:"good" |"partial" |"no"
  explanation: string
}

interface CalibrationCandidate {
  id: string
  name: string
  current_title: string
  current_company: string
  location: string
  avatar_url: string | null
  total_experience_years: number
  skills: string[]
  /** Tenure stats — chips de tempo de empresa/cargo. */
  tenure_stats?: {
    avg_months?: number
    current_months?: number
    total_months?: number
  }
  /** Auto-tags geradas — ex: ["Scale-up", "Fullstack", "Remoto ✓"]. */
  auto_tags?: string[]
  experiences: Array<{
    title: string
    company: string
    start_date: string
    end_date: string | null
    duration_years: number
    description: string
    is_current: boolean
  }>
  education: Array<{
    institution: string
    degree: string
    field: string
  }>
  match_criteria: MatchCriterion[]
}

// ---------- Constants ----------

const MATCH_BADGE_STYLES: Record<string, string> = {
  good: badgeStyles.success,
  partial: badgeStyles.warning,
  no: badgeStyles.error,
}
const MATCH_BADGE_KEYS: Record<string, string> = {
  good: "matchGood",
  partial: "matchPartial",
  no: "matchNo",
}

const REJECTION_REASON_KEYS = ["differentTechStack","insufficientSeniority","crudOnly","incompatibleLocation","irrelevantExperience"] as const

/** Formata meses em representação compacta: "1a 4m" ou "8m". */
function formatTenureMonths(months: number): string {
  if (months < 12) return `${months}m`
  const years = Math.floor(months / 12)
  const rem = months % 12
  return rem > 0 ? `${years}a ${rem}m` : `${years}a`
}

// ---------- Main Component ----------

interface CalibrationCardModalProps {
  agentId: string
  isOpen: boolean
  onClose: () => void
  onCalibrationComplete: (agentId: string) => void
}

export default function CalibrationCardModal({
  agentId, isOpen, onClose, onCalibrationComplete,
}: CalibrationCardModalProps) {
  const t = useTranslations('agents.calibration')
  const [candidates, setCandidates] = useState<CalibrationCandidate[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [approvedCount, setApprovedCount] = useState(0)
  const [rejectedCount, setRejectedCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showCommentInput, setShowCommentInput] = useState(false)
  const [comment, setComment] = useState("")
  const [isComplete, setIsComplete] = useState(false)

  const MIN_APPROVALS = 3
  const candidate = candidates[currentIdx]

  useEffect(() => {
    if (isOpen) loadCandidates()
  }, [isOpen, agentId])

  const loadCandidates = async () => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const res = await fetch(`/api/backend-proxy/custom-agents/${agentId}/calibration-candidates?limit=15`)
      if (!res.ok) {
        throw new Error(`Error ${res.status}: ${res.statusText}`)
      }
      const data = await res.json()
      setCandidates(data?.candidates || [])
    } catch (err) {
      console.error("Failed to load calibration candidates:", err)
      setLoadError(err instanceof Error ? err.message : t('errorLoading'))
    } finally {
      setIsLoading(false)
    }
  }

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleApprove = async () => {
    if (!candidate || isSubmitting) return
    const ok = await submitFeedback("positive", t('profileApproved'))
    if (ok) {
      setApprovedCount(prev => prev + 1)
      advanceOrComplete()
    }
  }

  const handleReject = async (reason: string) => {
    if (!candidate || isSubmitting) return
    const ok = await submitFeedback("negative", reason)
    if (ok) {
      setRejectedCount(prev => prev + 1)
      setShowRejectModal(false)
      advanceOrComplete()
    } else {
      setShowRejectModal(false)
    }
  }

  const submitFeedback = async (signalType: string, reason: string): Promise<boolean> => {
    setIsSubmitting(true)
    try {
      const res = await fetch(`/api/backend-proxy/custom-agents/${agentId}/feedback`, {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          candidate_id: candidate.id,
          signal_type: signalType,
          reason,
        }),
      })
      if (!res.ok) {
        throw new Error(`Error ${res.status}`)
      }
      return true
    } catch (err) {
      console.error("Feedback failed:", err)
      toast.error(t('errorSendingFeedback'), t('feedbackNotSaved'))
      return false
    } finally {
      setIsSubmitting(false)
    }
  }

  const advanceOrComplete = () => {
    if (currentIdx < candidates.length - 1) {
      setCurrentIdx(prev => prev + 1)
    } else {
      setIsComplete(true)
    }
  }

  const canFinish = approvedCount >= MIN_APPROVALS

  if (!isOpen) return null

  // Completion screen
  if (isComplete || (canFinish && currentIdx >= candidates.length - 1)) {
    return (
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="max-w-md">
          <DialogTitle className="sr-only">{t('calibrationCompleteTitle')}</DialogTitle>
          <DialogDescription className="sr-only">{t('calibrationResultDesc')}</DialogDescription>
          <div className="flex flex-col items-center py-8">
            <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
            <h3 className={textStyles.h3}>{t('calibrationComplete')}</h3>
            <p className={`${textStyles.body} text-center mt-2`}>
              {approvedCount} {t('approvedCount')} · {rejectedCount} {t('rejectedCount')}
            </p>
            <p className={`${textStyles.caption} text-center mt-1`}>
              {t('agentLearnedCriteria')}
            </p>
            <Button
              className={`${buttonStyles.primary} mt-6`}
              onClick={() => onCalibrationComplete(agentId)}
            >
              {t('closeAndWait')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden p-0">
        <DialogTitle className="sr-only">{t('candidateCalibration')}</DialogTitle>
        <DialogDescription className="sr-only">{t('evaluateCandidatesDesc')}</DialogDescription>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3">
          <button onClick={onClose} className="flex items-center gap-1 text-sm text-lia-text-secondary hover:text-lia-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30">
            <ChevronLeft className="w-4 h-4" /> {t('back')}
          </button>
          <span className={textStyles.caption}>
            {t('profile')} {currentIdx + 1}/{candidates.length}
          </span>
          <div className="flex items-center gap-3">
            {currentIdx > 0 && (
              <button onClick={() => setCurrentIdx(prev => prev - 1)} className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={() => currentIdx < candidates.length - 1 && setCurrentIdx(prev => prev + 1)}
              className={currentIdx < candidates.length - 1 ?"text-lia-text-tertiary hover:text-lia-text-secondary" :"text-lia-text-disabled"}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-96 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-lia-text-disabled" />
            <p className={textStyles.caption}>{t('loadingProfiles')}</p>
          </div>
        ) : loadError ? (
          <div className="flex flex-col items-center justify-center h-96 gap-3 px-8">
            <div className="w-12 h-12 rounded-full bg-red-50 dark:bg-red-950/30 flex items-center justify-center">
              <X className="w-6 h-6 text-red-500" />
            </div>
            <p className="text-sm font-medium text-lia-text-primary">{t('errorLoadingCandidates')}</p>
            <p className="text-xs text-lia-text-secondary text-center">{loadError}</p>
            <button
              onClick={loadCandidates}
              className="mt-2 px-4 py-2 rounded-lg text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary hover:bg-lia-bg-secondary border border-lia-border-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
            >
              {t('tryAgain')}
            </button>
          </div>
        ) : candidates.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-96 gap-3 px-8">
            <div className="w-12 h-12 rounded-full bg-amber-50 dark:bg-amber-950/30 flex items-center justify-center">
              <Users className="w-6 h-6 text-amber-500" />
            </div>
            <p className="text-sm font-medium text-lia-text-primary">{t('noCandidateFound')}</p>
            <p className="text-xs text-lia-text-secondary text-center">
              {t('noCandidateFoundDesc')}
            </p>
            <button
              onClick={onClose}
              className="mt-2 px-4 py-2 rounded-lg text-xs font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
            >
              {t('close')}
            </button>
          </div>
        ) : !candidate ? (
          <div className="flex items-center justify-center h-96">
            <p className={textStyles.caption}>{t('loadingProfile')}</p>
          </div>
        ) : (
          <div className="flex h-[70vh]">
            {/* Left panel — Candidate Profile */}
            <div className="w-1/2 overflow-y-auto border-r border-lia-border-subtle p-6">
              {/* Candidate header */}
              <div className="flex items-center gap-3 mb-4">
                <Avatar className="w-12 h-12">
                  <AvatarImage src={candidate.avatar_url || undefined} alt={candidate.name || "Candidato"} />
                  <AvatarFallback>{candidate.name?.charAt(0)}</AvatarFallback>
                </Avatar>
                <div>
                  <h3 className={textStyles.h3}>{candidate.name}</h3>
                  <p className={textStyles.body}>{candidate.location}</p>
                </div>
              </div>

              {/* Current role */}
              <div className="mb-4">
                <p className={textStyles.subtitle}>
                  {candidate.current_title} at {candidate.current_company}
                </p>
              </div>

              {/* Skills */}
              {candidate.skills?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {candidate.skills.slice(0, 8).map(skill => (
                    <Chip density="relaxed" variant="neutral" muted key={skill} className="bg-lia-bg-tertiary text-lia-text-secondary">{skill}</Chip>
                  ))}
                </div>
              )}

              {/* Auto-tags geradas pelo backend */}
              {candidate.auto_tags && candidate.auto_tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {candidate.auto_tags.map((tag, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan-text text-[11px] font-medium">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Experience stats */}
              <div className="flex gap-4 mb-4 py-3 border-y border-lia-border-subtle flex-wrap">
                <div>
                  <p className={textStyles.caption}>{t('totalExperience')}</p>
                  <p className={textStyles.subtitle}>{candidate.total_experience_years}a</p>
                </div>
                {candidate.tenure_stats?.current_months !== undefined && (
                  <div>
                    <p className={textStyles.caption}>Cargo atual</p>
                    <p className={textStyles.subtitle}>{formatTenureMonths(candidate.tenure_stats.current_months)}</p>
                  </div>
                )}
                {candidate.tenure_stats?.avg_months !== undefined && (
                  <div>
                    <p className={textStyles.caption}>Média por empresa</p>
                    <p className={textStyles.subtitle}>{formatTenureMonths(candidate.tenure_stats.avg_months)}</p>
                  </div>
                )}
              </div>

              {/* Experiences */}
              <div>
                <h4 className={`${textStyles.label} mb-2`}>{t('experiences')}</h4>
                <div className="space-y-3">
                  {candidate.experiences?.slice(0, 4).map((exp, i) => (
                    <div key={i} className="border-l-2 border-lia-border-subtle pl-3">
                      <p className={textStyles.subtitle}>{exp.title}</p>
                      <p className={textStyles.caption}>
                        {exp.company} · {exp.start_date} – {exp.end_date || t('current')}
                        {exp.duration_years > 0 && ` · ${exp.duration_years}a`}
                      </p>
                      {exp.description && (
                        <p className={`${textStyles.bodySmall} mt-1 text-lia-text-secondary`}>
                          {exp.description.slice(0, 150)}...
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Education */}
              {candidate.education?.length > 0 && (
                <div className="mt-4">
                  <h4 className={`${textStyles.label} mb-2`}>{t('education')}</h4>
                  {candidate.education.slice(0, 2).map((edu, i) => (
                    <div key={i} className="mb-1">
                      <p className={textStyles.body}>{edu.degree} — {edu.field}</p>
                      <p className={textStyles.caption}>{edu.institution}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right panel — Why we matched + Actions */}
            <div className="w-1/2 flex flex-col">
              <div className="flex-1 overflow-y-auto p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className={textStyles.h4}>{t('whyWeMatched')}</h3>
                  <button className="text-sm text-lia-text-tertiary hover:text-lia-text-secondary flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30">
                    <Edit3 className="w-3.5 h-3.5" /> {t('editCriteria')}
                  </button>
                </div>

                <div className="space-y-4">
                  {candidate.match_criteria?.map((mc, i) => {
                    const badgeStyle = MATCH_BADGE_STYLES[mc.match] || badgeStyles.info
                    const badgeKey = MATCH_BADGE_KEYS[mc.match] || "matchGood"
                    return (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Chip variant="neutral" muted className={badgeStyle}>{t(badgeKey)}</Chip>
                        </div>
                        <p className={textStyles.subtitle}>{mc.criterion}</p>
                        <p className={textStyles.bodySmall}>{mc.explanation}</p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex-shrink-0 p-6 border-t border-lia-border-subtle space-y-3">
                <Button
                  className={`w-full ${buttonStyles.primary} bg-green-600 hover:bg-green-700`}
                  onClick={handleApprove}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ThumbsUp className="w-4 h-4 mr-2" />}
                  {t('approve')}
                </Button>
                <Button
                  className={`w-full ${buttonStyles.outline} border-red-300 text-red-600 hover:bg-red-50`}
                  onClick={() => setShowRejectModal(true)}
                  disabled={isSubmitting}
                >
                  <ThumbsDown className="w-4 h-4 mr-2" /> {t('reject')}
                </Button>
                {!showCommentInput ? (
                  <button
                    onClick={() => setShowCommentInput(true)}
                    className="w-full flex items-center justify-center gap-1 text-sm text-lia-text-tertiary hover:text-lia-text-secondary py-1"
                  >
                    <MessageSquare className="w-3.5 h-3.5" /> {t('addComment')}
                  </button>
                ) : (
                  <div>
                    <textarea
                      value={comment}
                      onChange={e => setComment(e.target.value)}
                      placeholder={t('commentPlaceholder') as string}
                      rows={2}
                      className="w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm resize-none"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer — calibration progress */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center gap-4">
            <span className={textStyles.caption}>
              {t('approvedLabel')}: <strong>{approvedCount}/{MIN_APPROVALS} {t('minAbbr')}</strong>
            </span>
            <span className={textStyles.caption}>
              {t('rejectedLabel')}: {rejectedCount}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="text-sm text-lia-text-tertiary hover:text-lia-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
            >
              {t('skipCalibration')}
            </button>
            {canFinish && (
              <Button
                className={buttonStyles.primary}
                onClick={() => onCalibrationComplete(agentId)}
              >
                {t('closeAndWaitCheck')}
              </Button>
            )}
          </div>
        </div>

        {/* Rejection reason modal */}
        {showRejectModal && (
          <RejectReasonModal
            onSelect={handleReject}
            onClose={() => setShowRejectModal(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

// ---------- Reject Reason Modal ----------

function RejectReasonModal({
  onSelect,
  onClose,
}: {
  onSelect: (reason: string) => void
  onClose: () => void
}) {
  const t = useTranslations('agents.calibration')
  const [customReason, setCustomReason] = useState("")

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-[60]">
      <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-5">
        <h4 className={textStyles.h4}>{t('whyReject')}</h4>
        <p className={`${textStyles.caption} mb-3`}>
          {t('helpImproveSearches')}
        </p>
        <div className="space-y-2">
          {REJECTION_REASON_KEYS.map(key => (
            <button
              key={key}
              onClick={() => onSelect(t(`rejectionReasons.${key}`))}
              className="w-full text-left px-3 py-2 rounded-xl text-sm hover:bg-lia-bg-tertiary border border-lia-border-subtle transition-colors"
            >
              {t(`rejectionReasons.${key}`)}
            </button>
          ))}
          <div className="pt-2">
            <input
              type="text"
              value={customReason}
              onChange={e => setCustomReason(e.target.value)}
              placeholder={t('otherReason') as string}
              className="w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm"
              onKeyDown={e => e.key ==="Enter" && customReason.trim() && onSelect(customReason.trim())}
            />
          </div>
        </div>
        <div className="flex justify-end mt-3">
          <button onClick={onClose} className="text-sm text-lia-text-tertiary hover:text-lia-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30">
            {t('cancel')}
          </button>
        </div>
      </div>
    </div>
  )
}
