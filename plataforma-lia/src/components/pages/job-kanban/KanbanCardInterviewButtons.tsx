"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"
import {
  ThumbsUp,
  XCircle,
  Video,
  Calendar,
  AlertCircle,
  FileText,
} from "lucide-react"

interface KanbanCardInterviewButtonsProps {
  candidate: {
    id: string
    name: string
    agendada?: string | boolean
    interviewDate?: string
    teamsLink?: string
    [key: string]: unknown
  }
  stageId: string
  setTransitionInitialPrompt: (prompt: string | undefined) => void
  setTransitionInterviewAlert: (value: { name: string; date: string } | null) => void
  setTransitionAllowStageSelection: (value: boolean) => void
  setDecisionFlowCandidate: (candidate: unknown) => void
  setDecisionFlowType: (type: "approve_to_triage" | "approve_to_interview" | "reject_pre_triage" | "reject_post_triage" | "request_urgency" | "reschedule_interview" | "confirm_hire") => void
  setShowDecisionFlowModal: (value: boolean) => void
  onOpenDecisionFlowModal: (candidate: unknown, action: "approve" | "reject") => void
  onApproveFromScreening: (candidate: unknown) => void
  onRejectFromScreening: (candidate: unknown) => void
  openTransition: (candidates: unknown[], fromStage: string, toStage: string) => void
  onManageProposal?: (candidate: unknown) => void
}

export function KanbanCardInterviewButtons({
  candidate,
  stageId,
  setTransitionInitialPrompt,
  setTransitionInterviewAlert,
  setTransitionAllowStageSelection,
  setDecisionFlowCandidate,
  setDecisionFlowType,
  setShowDecisionFlowModal,
  onOpenDecisionFlowModal,
  onApproveFromScreening,
  onRejectFromScreening,
  openTransition,
  onManageProposal,
}: KanbanCardInterviewButtonsProps) {
  const t = useTranslations('kanban')
  const locale = useLocale()
  return (
    <>
  {/* Container de Ações */}
  {(stageId === "sourcing" ||
    stageId === "screening" ||
    stageId.startsWith("interview_") ||
    stageId === "offer") && (
    <div className="border-t border-lia-border-subtle p-2 max-h-0 overflow-hidden opacity-0 group-hover:max-h-20 group-hover:opacity-100 transition-opacity motion-reduce:transition-none duration-200 ease-out relative z-20 bg-lia-bg-secondary">
      {/* Botões para FUNIL */}
      {stageId === "sourcing" && (
        <div className="flex gap-1">
          <button
            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
            onClick={(e) => {
              e.stopPropagation()
              onOpenDecisionFlowModal(candidate, "approve")
            }}
          >
            <ThumbsUp className="w-3 h-3" aria-hidden="true" />
            <span>{t('approve')}</span>
          </button>
          <button
            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-error hover:bg-status-error text-white rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
            onClick={(e) => {
              e.stopPropagation()
              onOpenDecisionFlowModal(candidate, "reject")
            }}
          >
            <XCircle className="w-3 h-3" aria-hidden="true" />
            <span>{t('reject')}</span>
          </button>
        </div>
      )}

      {/* Botões para TRIAGEM */}
      {stageId === "screening" && (
        <div className="flex gap-1">
          <button
            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
            onClick={(e) => {
              e.stopPropagation()
              onApproveFromScreening(candidate)
            }}
          >
            <ThumbsUp className="w-3 h-3" aria-hidden="true" />
            <span>{t('approve')}</span>
          </button>
          <button
            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-error hover:bg-status-error text-white rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
            onClick={(e) => {
              e.stopPropagation()
              onRejectFromScreening(candidate)
            }}
          >
            <XCircle className="w-3 h-3" aria-hidden="true" />
            <span>{t('reject')}</span>
          </button>
        </div>
      )}

      {/* Botões para ENTREVISTA */}
      {(stageId === "interview_hr" ||
        stageId === "interview_technical" ||
        stageId === "interview_manager") && (
        <div className="flex gap-1">
          {candidate.agendada ? (
            <>
              <button
                className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
                onClick={(e) => {
                  e.stopPropagation()
                  const teamsUrl = candidate.teamsLink
                  if (!teamsUrl) {
                    console.warn('Teams link not configured for this interview')
                    return
                  }
                  window.open(teamsUrl, "_blank")
                }}
                title={t('joinMeeting', { date: candidate.interviewDate ||
                  new Date(String(candidate.agendada)).toLocaleDateString(locale) })}
              >
                <Video className="w-3 h-3 text-lia-text-secondary" />
                <span>
                  {candidate.interviewDate ||
                    new Date(String(candidate.agendada)).toLocaleDateString(locale, {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                </span>
              </button>
              <button
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-warning hover:bg-status-warning text-white rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
                onClick={(e) => {
                  e.stopPropagation()
                  const dateStr =
                    candidate.interviewDate ||
                    new Date(String(candidate.agendada)).toLocaleDateString(locale, {
                      day: "numeric",
                      month: "long",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  setTransitionInitialPrompt(
                    t('reschedulePrompt', { name: candidate.name, date: dateStr })
                  )
                  setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                  openTransition([candidate], stageId, stageId)
                }}
                title={t('rescheduleInterview')}
              >
                <Calendar className="w-3 h-3" />
                <span>{t('reschedule')}</span>
              </button>
              <button
                className="flex-shrink-0 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-error/10 hover:bg-status-error/15 text-status-error border border-status-error/30 rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
                onClick={(e) => {
                  e.stopPropagation()
                  const dateStr =
                    candidate.interviewDate ||
                    new Date(String(candidate.agendada)).toLocaleDateString(locale, {
                      day: "numeric",
                      month: "long",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  setTransitionInitialPrompt(
                    t('cancelPrompt', { name: candidate.name, date: dateStr })
                  )
                  setTransitionAllowStageSelection(true)
                  setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                  openTransition([candidate], stageId, stageId)
                }}
                title={t('cancelInterview')}
              >
                <XCircle className="w-3 h-3" />
                <span>{t('cancelAction')}</span>
              </button>
            </>
          ) : (
            <>
              <button
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-status-warning hover:bg-status-warning text-white rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
                onClick={(e) => {
                  e.stopPropagation()
                  setDecisionFlowCandidate(candidate)
                  setDecisionFlowType("request_urgency")
                  setShowDecisionFlowModal(true)
                }}
              >
                <AlertCircle className="w-3 h-3" />
                <span>{t('urgency')}</span>
              </button>
              <button
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-full text-micro font-medium transition-colors motion-reduce:transition-none"
                onClick={(e) => {
                  e.stopPropagation()
                  setDecisionFlowCandidate(candidate)
                  setDecisionFlowType("reschedule_interview")
                  setShowDecisionFlowModal(true)
                }}
              >
                <Calendar className="w-3 h-3" />
                <span>{t('rescheduleTime')}</span>
              </button>
            </>
          )}
        </div>
      )}

      {stageId === "offer" && (
        <button
          className="w-full flex items-center justify-center gap-1 px-2 py-1.5 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-full text-micro transition-colors motion-reduce:transition-none"
          onClick={(e) => {
            e.stopPropagation()
            if (onManageProposal) onManageProposal(candidate)
          }}
        >
          <FileText className="w-3 h-3" />
          <span>{t('manageProposal')}</span>
        </button>
      )}
    </div>
  )}
    </>
  )
}
