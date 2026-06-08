"use client"

// useCandidatesInteractions.ts
// Owns candidate click/preview/communication handlers and quick-action builders.
// Receives dependencies via parameters; returns pure handler functions.

import React from "react"
import { useRouter } from "next/navigation"
import { ChevronsLeftRight, Target, Calendar, CheckCircle, Mail, MessageSquare } from "lucide-react"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"
import { type QuickAction } from "@/components/ui/quick-action-chips"
import { type ParsedCVResponse } from "@/components/cv"
import type { Candidate } from "@/components/pages/candidates/types"
import { PREVIEW_WIDTH_MIN, PREVIEW_WIDTH_MAX } from "./candidates-core"
import { toast } from "sonner"

interface UseCandidatesInteractionsParams {
  // Candidate data
  candidates: Candidate[]
  setCandidates: (fn: ((prev: Candidate[]) => Candidate[]) | Candidate[]) => void
  sortedCandidates: Candidate[]
  selectedCandidatesForBatch: Set<string>
  setSelectedCandidatesForBatch: (s: Set<string>) => void
  // View state setters
  setPreviewCandidate: (c: Candidate | null) => void
  setShowCandidatePreview: (v: boolean) => void
  setIsPreviewMaximized: (fn: ((prev: boolean) => boolean) | boolean) => void
  isPreviewMaximized: boolean
  setShowPreview: (v: boolean) => void
  setSelectedCandidate: (c: Candidate | null) => void
  setShowCandidatePage: (v: boolean) => void
  setShowSidePreview: (v: boolean) => void
  setSidePreviewCandidate: (c: Candidate | null) => void
  // Preview resize
  previewWidth: number
  setPreviewWidth: (v: number) => void
  // Modals
  setUnifiedModalCandidate: (c: Candidate | null) => void
  setUnifiedModalSelectedCandidates: (v: Array<{ id: string; name: string; email?: string; phone?: string; avatar?: string }>) => void
  setUnifiedModalType: (t: CommunicationType) => void
  setUnifiedModalOpen: (v: boolean) => void
  setShowScheduleModal: (v: boolean) => void
  setShowContactModal: (v: boolean) => void
  setSelectedCandidateForAction: (c: Candidate | null) => void
  setShowComparisonModal: (v: boolean) => void
  setShowQuickViewModal: (v: boolean) => void
  setShowBatchApproval: (v: boolean) => void
  // CV modal
  setParsedCVData: (d: ParsedCVResponse | null) => void
  setShowCVPreviewModal: (v: boolean) => void
  // Toast
  // Callbacks from props
  onAddRecentItem?: (item: {
    id: string; type: 'candidato' | 'vaga' | 'chat'; title: string; subtitle?: string; meta?: Record<string, string | undefined>
  }) => void
  markCandidateAsViewed: (id: string, ctx: string) => void
  handleBulkActionComplete: () => void
  // LIA chat stubs
  handleAICommand: (cmd: string) => Promise<void>
  deselectAllCandidates: () => void
}

export function useCandidatesInteractions({
  candidates,
  setCandidates,
  sortedCandidates,
  selectedCandidatesForBatch,
  setSelectedCandidatesForBatch,
  setPreviewCandidate,
  setShowCandidatePreview,
  setIsPreviewMaximized,
  isPreviewMaximized,
  setShowPreview,
  setSelectedCandidate,
  setShowCandidatePage,
  setShowSidePreview,
  setSidePreviewCandidate,
  previewWidth,
  setPreviewWidth,
  setUnifiedModalCandidate,
  setUnifiedModalSelectedCandidates,
  setUnifiedModalType,
  setUnifiedModalOpen,
  setShowScheduleModal,
  setShowContactModal,
  setSelectedCandidateForAction,
  setShowComparisonModal,
  setShowQuickViewModal,
  setShowBatchApproval,
  setParsedCVData,
  setShowCVPreviewModal,
  onAddRecentItem,
  markCandidateAsViewed,
  handleBulkActionComplete,
  handleAICommand,
  deselectAllCandidates,
}: UseCandidatesInteractionsParams) {
  const router = useRouter()

  // ── Unified communication modal ───────────────────────────────────────────
  const openUnifiedModal = (candidate: Candidate, type: CommunicationType) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }

  // ── Candidate click / preview ─────────────────────────────────────────────
  const handleCandidateClick = (candidate: Candidate) => {
    setPreviewCandidate(candidate)
    setShowCandidatePreview(true)
    markCandidateAsViewed(candidate.id, 'profile')
    onAddRecentItem?.({
      id: candidate.id, type: 'candidato', title: candidate.name,
      subtitle: (candidate as unknown as Record<string, unknown>).currentRole as string || candidate.location,
      meta: { candidateId: candidate.id },
    })
  }

  const handleCloseCandidatePreview = () => { setShowCandidatePreview(false); setPreviewCandidate(null) }
  const handleTogglePreviewMaximize = () => { setIsPreviewMaximized((p: boolean) => !p) }
  const handleCandidatePageOpen = (candidate: Candidate) => { router.push(`/funil-de-talentos/candidato/${candidate.id}`) }
  const handleCloseSidePreview = () => { setShowSidePreview(false); setSidePreviewCandidate(null) }
  const handleClosePreview = () => { setShowPreview(false); setSelectedCandidate(null); setIsPreviewMaximized(false) }
  const handleToggleMaximize = () => { setIsPreviewMaximized((p: boolean) => !p) }
  const handleCloseCandidatePage = () => { setShowCandidatePage(false); setSelectedCandidate(null) }

  const handleCandidateSelection = (
    candidateId: string,
    _index: number,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    event.stopPropagation()
    const newSelected = new Set(selectedCandidatesForBatch)
    if (event.target.checked) newSelected.add(candidateId)
    else newSelected.delete(candidateId)
    setSelectedCandidatesForBatch(newSelected)
  }

  const selectAllCandidates = () => {
    setSelectedCandidatesForBatch(new Set(sortedCandidates.map(c => c.id)))
  }

  const handleLIAClick = (candidate: Candidate) => {
    handleCandidateClick(candidate)
  }

  // ── Preview resize ────────────────────────────────────────────────────────
  const handlePreviewResize = (e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = previewWidth
    const onMove = (ev: MouseEvent) => {
      setPreviewWidth(Math.min(Math.max(PREVIEW_WIDTH_MIN, startWidth + (startX - ev.clientX)), PREVIEW_WIDTH_MAX))
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = 'default'
      document.body.style.userSelect = 'auto'
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  // ── Candidate action modal openers ────────────────────────────────────────
  const handleNavigateToFullProfile = (candidate: Candidate) => {
    setSelectedCandidate(candidate)
    setShowQuickViewModal(false)
    setShowComparisonModal(false)
    setShowCandidatePage(true)
  }
  const handleScheduleInterview = (candidate: Candidate) => {
    setSelectedCandidateForAction(candidate)
    setShowComparisonModal(false)
    setShowScheduleModal(true)
  }
  const handleContactCandidate = (candidate: Candidate) => {
    setSelectedCandidateForAction(candidate)
    setShowComparisonModal(false)
    setShowContactModal(true)
  }
  const handleSendMessage = (_data: Record<string, unknown>) => { setShowContactModal(false) }
  const handleScheduleComplete = (_data: Record<string, unknown>) => { setShowScheduleModal(false) }

  // ── Communication shortcuts ───────────────────────────────────────────────
  const handleSendEmail = (candidate: Candidate) => openUnifiedModal(candidate, 'email')
  const handleSendWhatsApp = (candidate: Candidate) => openUnifiedModal(candidate, 'whatsapp')
  const handleSendTriagem = (candidate: Candidate) => openUnifiedModal(candidate, 'triagem')
  const handleSendAgendamento = (candidate: Candidate) => openUnifiedModal(candidate, 'agendamento')
  const handleSendFeedback = (candidate: Candidate) => openUnifiedModal(candidate, 'feedback')

  // ── Bulk communication ────────────────────────────────────────
  const openBulkUnifiedModal = (type: CommunicationType) => {
    const selected = sortedCandidates
      .filter(c => selectedCandidatesForBatch.has(c.id))
      .map(c => ({ id: c.id, name: c.name, email: c.email, phone: c.phone, avatar: c.avatar }))
    if (selected.length === 0) return
    setUnifiedModalCandidate(null)
    setUnifiedModalSelectedCandidates(selected)
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }

  const handleBulkEmail = () => openBulkUnifiedModal('email')
  const handleBulkWSIScreening = () => openBulkUnifiedModal('triagem')
  const handleBulkScheduleInterview = () => openBulkUnifiedModal('agendamento')
  const handleBulkFeedback = () => openBulkUnifiedModal('feedback')

  // ── Unified modal close/send ──────────────────────────────────────────────
  const handleUnifiedModalClose = () => {
    setUnifiedModalOpen(false)
    setUnifiedModalCandidate(null)
    setUnifiedModalSelectedCandidates([])
  }
  const handleUnifiedModalSend = (_data: Record<string, unknown>) => {
    handleUnifiedModalClose()
  }

  const handleBatchApprovalComplete = (_data: Record<string, unknown>) => {
    setShowBatchApproval(false)
    setSelectedCandidatesForBatch(new Set())
  }

  // ── WSI handlers ──────────────────────────────────────────────────────────
  // These setters are provided externally from useCandidatesUIState
  // and referenced from LIA handlers. Exposed as-is.
  const handleWSIScreeningComplete = (_result: Record<string, unknown>) => {}

  // ── Add candidate ─────────────────────────────────────────────────────────
  const handleAddCandidate = (
    newCandidate: Record<string, unknown>,
    setShowAddCandidateModal: (v: boolean) => void
  ) => {
    const c = {
      ...newCandidate,
      candidateId: newCandidate.id,
      tags: (newCandidate.skills as string[]).slice(0, 3),
      status: 'active' as const,
      score: (newCandidate.liaAnalysis as unknown as Record<string, unknown>)?.score || 75,
      workModel: newCandidate.workModel as 'remoto' | 'híbrido' | 'presencial',
      contractType: newCandidate.contractType as 'CLT' | 'PJ' | 'Freelancer',
      linkedin: newCandidate.linkedin || '',
      skills: newCandidate.skills || [],
      experience: parseInt(newCandidate.experience as string) || 1,
      education: newCandidate.education || 'Superior Completo',
    }
    setCandidates((prev: Candidate[]) => [c as unknown as Candidate, ...prev])
    setShowAddCandidateModal(false)
  }

  // ── CV handlers ───────────────────────────────────────────────────────────
  const handleCVParsed = (data: ParsedCVResponse) => {
    setParsedCVData(data)
    setShowCVPreviewModal(true)
  }
  const handleCVConfirmed = (_candidateId: string) => {
    setShowCVPreviewModal(false)
    setParsedCVData(null)
    handleBulkActionComplete()
  }

  // ── Quick-action builders ─────────────────────────────────────────────────
  const handleQuickSchedule = () => {
    if (selectedCandidatesForBatch.size > 0) {
      const id = Array.from(selectedCandidatesForBatch)[0]
      const c = candidates.find(c => c.id === id)
      if (c) handleScheduleInterview(c)
    } else {
      handleAICommand('agendar entrevista com candidatos')
    }
  }
  const handleQuickEvaluate = () => {
    if (selectedCandidatesForBatch.size > 0)
      handleAICommand(`avaliar fit dos ${selectedCandidatesForBatch.size} candidatos selecionados`)
    else
      handleAICommand('avaliar fit técnico dos candidatos')
  }
  const handleQuickEmail = () => {
    if (selectedCandidatesForBatch.size > 0) {
      const id = Array.from(selectedCandidatesForBatch)[0]
      const c = candidates.find(c => c.id === id)
      if (c) handleContactCandidate(c)
    } else {
      handleAICommand('gerar email de follow-up para candidatos')
    }
  }
  const handleQuickWhatsApp = () => { handleAICommand('enviar mensagem whatsapp para candidatos') }
  const handleQuickCompare = () => {
    if (selectedCandidatesForBatch.size >= 2) setShowComparisonModal(true)
    else handleAICommand('comparar perfis de candidatos')
  }
  const handleQuickTimeline = () => {
    if (selectedCandidatesForBatch.size > 0) {
      const id = Array.from(selectedCandidatesForBatch)[0]
      const c = candidates.find(c => c.id === id)
      if (c) handleCandidatePageOpen(c)
    } else {
      handleAICommand('mostrar timeline de interações com candidatos')
    }
  }

  const getCandidateQuickActions = (): QuickAction[] => {
    const n = selectedCandidatesForBatch.size
    return [
      { id: 'schedule', label: n > 0 ? `Agendar (${n})` : 'Agendar', icon: Calendar, variant: 'default' as const, onClick: handleQuickSchedule },
      { id: 'evaluate', label: n > 0 ? `Avaliar Fit (${n})` : 'Avaliar Fit', icon: Target, variant: 'default' as const, onClick: handleQuickEvaluate },
      { id: 'compare', label: n >= 2 ? `Comparar (${n})` : 'Comparar', icon: ChevronsLeftRight, variant: 'default' as const, onClick: handleQuickCompare },
      { id: 'email', label: n > 0 ? `Email (${n})` : 'Email', icon: Mail, variant: 'success' as const, onClick: handleQuickEmail },
      { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, variant: 'success' as const, onClick: handleQuickWhatsApp },
      { id: 'approve', label: n > 0 ? `Aprovar (${n})` : 'Aprovar', icon: CheckCircle, variant: 'success' as const, onClick: () => setShowBatchApproval(true) },
    ]
  }

  // ── Comparison helper ─────────────────────────────────────────────────────
  const getComparisonCandidates = () => sortedCandidates.filter(c => selectedCandidatesForBatch.has(c.id))

  const convertCandidatesForBatch = (cands: Candidate[]) =>
    cands.map(c => ({
      id: c.id, name: c.name, email: c.email, phone: c.phone, position: c.position,
      location: c.location, experience: c.experience.toString(), skills: c.skills,
      education: c.education, score: c.score, status: 'pending' as const,
      workModel: c.workModel, contractType: c.contractType,
      currentSalary: c.salary?.current?.toString() || '',
      expectedSalary: c.salary?.expected?.toString() || '',
      linkedin: c.linkedin, languages: c.languages || [], benefits: c.benefits || [],
      liaScore: c.liaAnalysis?.score || c.score, skillsMatch: c.skills.length,
      currentStage: 'Triagem',
      appliedDate: c.lastUpdated?.toISOString() || new Date().toISOString(),
      lastInteraction: c.lastUpdated?.toISOString() || new Date().toISOString(),
      notes: c.notes || '', github: '', portfolio: '', certifications: [],
      availability: 'Imediata', noticePeriod: '30 dias', priority: 'média' as const,
      source: 'linkedin', tags: c.tags || [], jobTitle: c.position, department: 'Tecnologia',
    }))

  return {
    openUnifiedModal,
    handleCandidateClick,
    handleCloseCandidatePreview,
    handleTogglePreviewMaximize,
    handleCandidatePageOpen,
    handleCloseSidePreview,
    handleClosePreview,
    handleToggleMaximize,
    handleCloseCandidatePage,
    handleCandidateSelection,
    selectAllCandidates,
    handleLIAClick,
    handlePreviewResize,
    handleNavigateToFullProfile,
    handleScheduleInterview,
    handleContactCandidate,
    handleSendMessage,
    handleScheduleComplete,
    handleSendEmail,
    handleSendWhatsApp,
    handleSendTriagem,
    handleSendAgendamento,
    handleSendFeedback,
    handleBulkEmail,
    handleBulkWSIScreening,
    handleBulkScheduleInterview,
    handleBulkFeedback,
    handleUnifiedModalClose,
    handleUnifiedModalSend,
    handleBatchApprovalComplete,
    handleWSIScreeningComplete,
    handleAddCandidate,
    handleCVParsed,
    handleCVConfirmed,
    handleQuickSchedule,
    handleQuickEvaluate,
    handleQuickEmail,
    handleQuickWhatsApp,
    handleQuickCompare,
    handleQuickTimeline,
    getCandidateQuickActions,
    getComparisonCandidates,
    convertCandidatesForBatch,
  }
}
