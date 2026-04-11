"use client"

import React, { useState, useEffect } from"react"
import {
  ChevronLeft, ChevronRight, ThumbsUp, ThumbsDown, MessageSquare,
  X, CheckCircle, Edit3
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from"@/components/ui/dialog"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from"@/lib/design-tokens"

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

const MATCH_BADGE: Record<string, { label: string; style: string }> = {
  good: { label:"Good Match", style: badgeStyles.success },
  partial: { label:"Partial Match", style: badgeStyles.warning },
  no: { label:"No Match", style: badgeStyles.error },
}

const REJECTION_REASONS = ["Stack técnica diferente do necessário","Senioridade insuficiente","Apenas experiência com CRUD/e-commerce","Localização incompatível","Experiência não relevante para a posição",
]

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
  const [candidates, setCandidates] = useState<CalibrationCandidate[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [approvedCount, setApprovedCount] = useState(0)
  const [rejectedCount, setRejectedCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
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
    try {
      const res = await fetch(`/api/backend-proxy/sourcing-agents/${agentId}/calibration-candidates?limit=15`)
      const data = await res.json()
      setCandidates(data?.candidates || [])
    } catch (err) {
      console.error("Failed to load calibration candidates:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!candidate) return
    await submitFeedback("positive","Perfil aprovado para o pipeline")
    setApprovedCount(prev => prev + 1)
    advanceOrComplete()
  }

  const handleReject = async (reason: string) => {
    if (!candidate) return
    await submitFeedback("negative", reason)
    setRejectedCount(prev => prev + 1)
    setShowRejectModal(false)
    advanceOrComplete()
  }

  const submitFeedback = async (signalType: string, reason: string) => {
    try {
      await fetch(`/api/backend-proxy/sourcing-agents/${agentId}/feedback`, {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          candidate_id: candidate.id,
          signal_type: signalType,
          reason,
        }),
      })
    } catch (err) {
      console.error("Feedback failed:", err)
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
          <DialogTitle className="sr-only">Calibração concluída</DialogTitle>
          <DialogDescription className="sr-only">Resultado da calibração do agente</DialogDescription>
          <div className="flex flex-col items-center py-8">
            <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
            <h3 className={textStyles.h3}>Calibração concluída!</h3>
            <p className={`${textStyles.body} text-center mt-2`}>
              {approvedCount} aprovados · {rejectedCount} rejeitados
            </p>
            <p className={`${textStyles.caption} text-center mt-1`}>
              O agente aprendeu seu critério e vai buscar candidatos similares aos aprovados.
            </p>
            <Button
              className={`${buttonStyles.primary} mt-6`}
              onClick={() => onCalibrationComplete(agentId)}
            >
              Fechar e aguardar candidatos
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden p-0">
        <DialogTitle className="sr-only">Calibração de candidatos</DialogTitle>
        <DialogDescription className="sr-only">Avalie candidatos para calibrar o agente de sourcing</DialogDescription>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3">
          <button onClick={onClose} className="flex items-center gap-1 text-sm text-lia-text-secondary hover:text-lia-text-primary">
            <ChevronLeft className="w-4 h-4" /> Voltar
          </button>
          <span className={textStyles.caption}>
            Perfil {currentIdx + 1}/{candidates.length}
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

        {isLoading || !candidate ? (
          <div className="flex items-center justify-center h-96">
            <p className={textStyles.caption}>Carregando perfis para calibração...</p>
          </div>
        ) : (
          <div className="flex h-[70vh]">
            {/* Left panel — Candidate Profile */}
            <div className="w-1/2 overflow-y-auto border-r border-lia-border-subtle p-6">
              {/* Candidate header */}
              <div className="flex items-center gap-3 mb-4">
                <Avatar className="w-12 h-12">
                  <AvatarImage src={candidate.avatar_url || undefined} />
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

              {/* Tags */}
              {candidate.skills?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {candidate.skills.slice(0, 8).map(skill => (
                    <Badge key={skill} className="bg-lia-bg-tertiary text-lia-text-secondary text-xs">{skill}</Badge>
                  ))}
                </div>
              )}

              {/* Experience stats */}
              <div className="flex gap-6 mb-4 py-3 border-y border-lia-border-subtle">
                <div>
                  <p className={textStyles.caption}>Total experiência</p>
                  <p className={textStyles.subtitle}>{candidate.total_experience_years}a</p>
                </div>
              </div>

              {/* Experiences */}
              <div>
                <h4 className={`${textStyles.label} mb-2`}>Experiências</h4>
                <div className="space-y-3">
                  {candidate.experiences?.slice(0, 4).map((exp, i) => (
                    <div key={i} className="border-l-2 border-lia-border-subtle pl-3">
                      <p className={textStyles.subtitle}>{exp.title}</p>
                      <p className={textStyles.caption}>
                        {exp.company} · {exp.start_date} – {exp.end_date ||"Atual"}
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
                  <h4 className={`${textStyles.label} mb-2`}>Educação</h4>
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
                  <h3 className={textStyles.h4}>Por que combinamos este perfil</h3>
                  <button className="text-sm text-lia-text-tertiary hover:text-lia-text-secondary flex items-center gap-1">
                    <Edit3 className="w-3.5 h-3.5" /> Editar Critérios
                  </button>
                </div>

                <div className="space-y-4">
                  {candidate.match_criteria?.map((mc, i) => {
                    const badge = MATCH_BADGE[mc.match]
                    return (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge className={badge.style}>{badge.label}</Badge>
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
                >
                  <ThumbsUp className="w-4 h-4 mr-2" /> Aprovar
                </Button>
                <Button
                  className={`w-full ${buttonStyles.outline} border-red-300 text-red-600 hover:bg-red-50`}
                  onClick={() => setShowRejectModal(true)}
                >
                  <ThumbsDown className="w-4 h-4 mr-2" /> Rejeitar
                </Button>
                {!showCommentInput ? (
                  <button
                    onClick={() => setShowCommentInput(true)}
                    className="w-full flex items-center justify-center gap-1 text-sm text-lia-text-tertiary hover:text-lia-text-secondary py-1"
                  >
                    <MessageSquare className="w-3.5 h-3.5" /> Adicionar comentário
                  </button>
                ) : (
                  <div>
                    <textarea
                      value={comment}
                      onChange={e => setComment(e.target.value)}
                      placeholder="Comentário para o agente aprender..."
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
              Aprovados: <strong>{approvedCount}/{MIN_APPROVALS} mín.</strong>
            </span>
            <span className={textStyles.caption}>
              Rejeitados: {rejectedCount}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="text-sm text-lia-text-tertiary hover:text-lia-text-secondary"
            >
              Pular calibração
            </button>
            {canFinish && (
              <Button
                className={buttonStyles.primary}
                onClick={() => onCalibrationComplete(agentId)}
              >
                Fechar e aguardar ✓
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
  const [customReason, setCustomReason] = useState("")

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-[60]">
      <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-5">
        <h4 className={textStyles.h4}>Por que rejeitar?</h4>
        <p className={`${textStyles.caption} mb-3`}>
          Sua resposta ajuda o agente a melhorar as próximas buscas.
        </p>
        <div className="space-y-2">
          {REJECTION_REASONS.map(reason => (
            <button
              key={reason}
              onClick={() => onSelect(reason)}
              className="w-full text-left px-3 py-2 rounded-xl text-sm hover:bg-lia-bg-tertiary border border-lia-border-subtle transition-colors"
            >
              {reason}
            </button>
          ))}
          <div className="pt-2">
            <input
              type="text"
              value={customReason}
              onChange={e => setCustomReason(e.target.value)}
              placeholder="Outro motivo..."
              className="w-full border border-lia-border-default rounded-xl px-3 py-2 text-sm"
              onKeyDown={e => e.key ==="Enter" && customReason.trim() && onSelect(customReason.trim())}
            />
          </div>
        </div>
        <div className="flex justify-end mt-3">
          <button onClick={onClose} className="text-sm text-lia-text-tertiary hover:text-lia-text-secondary">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}
