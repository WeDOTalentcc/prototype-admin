"use client"

import React, { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Calendar, Loader2, Send, Brain, AlertTriangle } from "lucide-react"
import { Badge } from "@/components/ui/badge"

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
  const [isGeneratingEmail, setIsGeneratingEmail] = useState(false)
  const [isScheduling, setIsScheduling] = useState(false)
  const [emailTemplate, setEmailTemplate] = useState<{
    subject: string
    body: string
  } | null>(null)
  const [schedulingPrompt, setSchedulingPrompt] = useState("")
  const [scheduledInterview, setScheduledInterview] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open && !emailTemplate) {
      generateEmailTemplate()
    }
  }, [open])

  const generateEmailTemplate = async () => {
    setIsGeneratingEmail(true)
    try {
      const response = await fetch("/api/v1/interviews/generate-email-template", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          candidate_email: candidateEmail,
          job_title: jobTitle,
          interview_type: "técnica",
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
      console.error("Error generating email:", error)
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
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          candidate_email: candidateEmail,
          candidate_id: candidateId,
          job_title: jobTitle,
          job_vacancy_id: jobVacancyId,
          interview_type: "técnica",
          natural_language_prompt: schedulingPrompt,
          user_name: userName,
          user_email: userEmail,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Erro ao agendar entrevista" }))
        throw new Error(errorData.detail || "Erro ao agendar entrevista")
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
    } catch (error: any) {
      console.error("Error scheduling interview:", error)
      setError(error.message || "Erro ao agendar entrevista. Por favor, tente novamente.")
    } finally {
      setIsScheduling(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-white dark:bg-gray-800 rounded-md dark:border-gray-700">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <DialogTitle className="text-sm font-semibold text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              Agendar Entrevista
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-gray-600 dark:text-gray-400">
            {candidateName} • {jobTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {scheduledInterview ? (
            <div className="p-4 rounded-md border border-green-200 bg-green-50">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs font-medium text-green-700">
                  Entrevista agendada com sucesso!
                </span>
              </div>
              <p className="text-xs text-gray-600">
                {scheduledInterview.interviewer} receberá a confirmação por email.
              </p>
              {scheduledInterview.meeting_url && (
                <a
                  href={scheduledInterview.meeting_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-600 dark:text-gray-400 hover:underline inline-flex items-center gap-1 mt-2"
                >
                  Abrir Teams Meeting
                </a>
              )}
            </div>
          ) : (
            <>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Label className="text-xs font-medium text-gray-800 dark:text-gray-200">
                    Email de Convite
                  </Label>
                  <Badge className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-0">
                    <Brain className="w-3 h-3 mr-1 text-wedo-cyan" />
                    Gerado por LIA
                  </Badge>
                </div>

                {isGeneratingEmail ? (
                  <div className="flex items-center justify-center p-8">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-600 dark:text-gray-400" />
                  </div>
                ) : emailTemplate ? (
                  <div className="space-y-2">
                    <Input
                      value={emailTemplate.subject}
                      onChange={(e) =>
                        setEmailTemplate({ ...emailTemplate, subject: e.target.value })
                      }
                      className="h-9 text-xs font-medium border-gray-200 focus:ring-gray-400 focus:border-gray-400 bg-gray-50 text-gray-800"
                    />
                    <div
                      className="p-3 rounded-md border border-gray-200 text-xs overflow-y-auto max-h-[200px] bg-gray-50 text-gray-600"
                      dangerouslySetInnerHTML={{ __html: emailTemplate.body }}
                    />
                  </div>
                ) : (
                  <p className="text-xs text-red-500">Erro ao gerar template de email</p>
                )}
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-medium text-gray-800 dark:text-gray-200">
                  Quando agendar?
                </Label>
                <Input
                  placeholder="Ex: Agendar para amanhã às 14h comigo"
                  value={schedulingPrompt}
                  onChange={(e) => setSchedulingPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSchedule()
                    }
                  }}
                  disabled={isScheduling}
                  className="h-9 text-xs border-gray-200 focus:ring-gray-400 focus:border-gray-400 bg-gray-50 text-gray-800"
                />
                <p className="text-xs text-gray-500">
                  Use linguagem natural: "amanhã às 14h comigo" ou "próxima segunda 10h"
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-md border border-red-200 bg-red-50">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-red-700">
                        Erro ao agendar
                      </p>
                      <p className="text-xs text-red-600 mt-1">
                        {error}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={isScheduling}
                  className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleSchedule}
                  disabled={isScheduling || !schedulingPrompt.trim()}
                  className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  {isScheduling ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
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
