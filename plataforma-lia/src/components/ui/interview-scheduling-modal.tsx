"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState, useEffect } from"react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from"@/components/ui/dialog"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Calendar, Loader2, Send, Brain, AlertTriangle } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { sanitizeHtml } from"@/lib/sanitize"


interface ScheduledInterviewData {
  interviewer?: string
  meeting_url?: string
  [key: string]: unknown
}

interface InterviewSchedulingModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  candidateName: string
  candidateEmail: string
  candidateId?: string
  jobTitle: string
  jobVacancyId?: string
  userName: string
  userEmail: string
}

export function InterviewSchedulingModal({
  open,
  onOpenChange,
  candidateName,
  candidateEmail,
  candidateId,
  jobTitle,
  jobVacancyId,
  userName,
  userEmail,
}: InterviewSchedulingModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('interview-scheduling', open)

  const [isGeneratingEmail, setIsGeneratingEmail] = useState(false)
  const [isScheduling, setIsScheduling] = useState(false)
  const [emailTemplate, setEmailTemplate] = useState<{
    subject: string
    body: string
  } | null>(null)
  const [schedulingPrompt, setSchedulingPrompt] = useState("")
  const [scheduledInterview, setScheduledInterview] = useState<ScheduledInterviewData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open && !emailTemplate) {
      generateEmailTemplate()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const generateEmailTemplate = async () => {
    setIsGeneratingEmail(true)
    try {
      const response = await fetch("/api/v1/interviews/generate-email-template", {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          candidate_email: candidateEmail,
          job_title: jobTitle,
          interview_type:"técnica",
          user_name: userName,
        }),
      })

      if (!response.ok) throw new Error("Failed to generate email")

      const data = await response.json()
      setEmailTemplate({
        subject: data.subject,
        body: data.body,
      })
    } catch (error) {
    } finally {
      setIsGeneratingEmail(false)
    }
  }

  const handleSchedule = async () => {
    if (!schedulingPrompt.trim()) return

    setIsScheduling(true)
    setError(null)
    
    try {
      const response = await fetch("/api/v1/interviews/schedule-from-prompt", {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          candidate_email: candidateEmail,
          candidate_id: candidateId,
          job_title: jobTitle,
          job_vacancy_id: jobVacancyId,
          interview_type:"técnica",
          natural_language_prompt: schedulingPrompt,
          user_name: userName,
          user_email: userEmail,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail:"Erro ao agendar entrevista" }))
        throw new Error(errorData.detail ||"Erro ao agendar entrevista")
      }

      const data = await response.json()
      setScheduledInterview(data)

      setTimeout(() => {
        onOpenChange(false)
        setScheduledInterview(null)
        setEmailTemplate(null)
        setSchedulingPrompt("")
        setError(null)
      }, 4000)
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message :"Erro ao agendar entrevista. Por favor, tente novamente.")
    } finally {
      setIsScheduling(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl dark:border-lia-border-subtle">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-lia-text-secondary" />
            <DialogTitle className="text-sm font-semibold text-lia-text-primary">
              Agendar Entrevista
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-lia-text-secondary">
            {candidateName} • {jobTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {scheduledInterview ? (
            <div className="p-4 rounded-xl border border-status-success/30 bg-status-success/10">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-status-success rounded-full animate-pulse motion-reduce:animate-none" />
                <span className="text-xs font-medium text-status-success">
                  Entrevista agendada com sucesso!
                </span>
              </div>
              <p className="text-xs text-lia-text-secondary">
                {scheduledInterview.interviewer} receberá a confirmação por email.
              </p>
              {scheduledInterview.meeting_url && (
                <a
                  href={scheduledInterview.meeting_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-lia-text-secondary hover:underline inline-flex items-center gap-1 mt-2"
                >
                  Abrir Teams Meeting
                </a>
              )}
            </div>
          ) : (
            <>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Label className="text-xs font-medium text-lia-text-primary">
                    Email de Convite
                  </Label>
                  <Chip variant="neutral" muted className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-0">
                    <Brain className="w-3 h-3 mr-1 text-wedo-cyan" />
                    Gerado por IA
                  </Chip>
                </div>

                {isGeneratingEmail ? (
                  <div className="flex items-center justify-center p-8" role="status" aria-live="polite" aria-label="Carregando...">
                    <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                  </div>
                ) : emailTemplate ? (
                  <div className="space-y-2">
                    <Input
                      value={emailTemplate.subject}
                      onChange={(e) =>
                        setEmailTemplate({ ...emailTemplate, subject: e.target.value })
                      }
                      className="h-9 text-xs font-medium border-lia-border-subtle focus:ring-lia-border-medium focus:border-lia-border-medium bg-lia-bg-secondary text-lia-text-primary"
                    />
                    <div
                      className="p-3 rounded-xl border border-lia-border-subtle text-xs overflow-y-auto max-h-chart-sm bg-lia-bg-secondary text-lia-text-secondary"
                      dangerouslySetInnerHTML={{ __html: sanitizeHtml(emailTemplate.body) }}
                    />
                  </div>
                ) : (
                  <p className="text-xs text-status-error">Erro ao gerar modelo de email</p>
                )}
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-medium text-lia-text-primary">
                  Quando agendar?
                </Label>
                <Input
                  placeholder="Ex: Agendar para amanhã às 14h comigo"
                  value={schedulingPrompt}
                  onChange={(e) => setSchedulingPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key ==="Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSchedule()
                    }
                  }}
                  disabled={isScheduling}
                  className="h-9 text-xs border-lia-border-subtle focus:ring-lia-border-medium focus:border-lia-border-medium bg-lia-bg-secondary text-lia-text-primary"
                />
                <p className="text-xs text-lia-text-secondary">
                  Use linguagem natural:"amanhã às 14h comigo" ou"próxima segunda 10h"
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-xl border border-status-error/30 bg-status-error/10">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-status-error mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-status-error">
                        Erro ao agendar
                      </p>
                      <p className="text-xs text-status-error mt-1">
                        {error}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-lia-border-subtle">
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={isScheduling}
                  className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleSchedule}
                  disabled={isScheduling || !schedulingPrompt.trim()}
                  className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                >
                  {isScheduling ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                      Agendando...
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5 mr-1.5" />
                      Agendar Entrevista
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
