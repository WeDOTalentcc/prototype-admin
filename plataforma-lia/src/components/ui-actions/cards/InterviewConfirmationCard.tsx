"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Calendar,
  Clock,
  MapPin,
  Video,
  Phone,
  Users,
  CheckCircle2,
  ExternalLink,
  Copy,
  Mail
} from "lucide-react"

interface InterviewConfirmationData {
  candidate_id: string
  candidate_name: string
  candidate_avatar?: string
  job_title: string
  date: string
  time: string
  duration: string
  type: "presencial" | "teams" | "meet" | "telefone"
  location?: string
  meeting_link?: string
  interviewers: Array<{
    name: string
    role?: string
    avatar?: string
  }>
  notes?: string
}

interface InterviewConfirmationCardProps {
  data: InterviewConfirmationData
  onAddToCalendar?: () => void
  onCopyLink?: () => void
  onSendReminder?: () => void
}

export function InterviewConfirmationCard({
  data,
  onAddToCalendar,
  onCopyLink,
  onSendReminder
}: InterviewConfirmationCardProps) {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case "teams":
      case "meet":
        return <Video className="h-4 w-4" />
      case "telefone":
        return <Phone className="h-4 w-4" />
      default:
        return <MapPin className="h-4 w-4" />
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "teams":
        return "Microsoft Teams"
      case "meet":
        return "Google Meet"
      case "telefone":
        return "Ligação Telefônica"
      default:
        return "Presencial"
    }
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <Card
      className="w-full max-w-md border-l-4 overflow-hidden bg-lia-bg-secondary"
     
    >
      <div
        className="px-4 py-2 flex items-center gap-2 bg-lia-text-primary"
      >
        <CheckCircle2 className="h-5 w-5 text-wedo-green" />
        <span className="font-medium text-lia-text-inverse">
          Entrevista Agendada!
        </span>
      </div>

      <CardContent className="p-4">
        <div className="flex items-center gap-3 mb-4">
          <Avatar className="h-10 w-10 border-2 border-lia-bg-primary">
            <AvatarImage src={data.candidate_avatar} alt={data.candidate_name} />
            <AvatarFallback
              className="text-sm bg-lia-bg-tertiary text-lia-text-primary"
            >
              {getInitials(data.candidate_name)}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="font-semibold text-lia-text-primary">
              {data.candidate_name}
            </div>
            <div className="text-sm text-lia-text-secondary">
              {data.job_title}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div
            className="p-3 rounded-xl border bg-lia-bg-primary border-lia-border-subtle"
          >
            <div className="flex items-center gap-2 mb-1 text-lia-text-tertiary">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">Data</span>
            </div>
            <div className="font-semibold text-lia-text-primary">
              {data.date}
            </div>
          </div>

          <div
            className="p-3 rounded-xl border bg-lia-bg-primary border-lia-border-subtle"
          >
            <div className="flex items-center gap-2 mb-1 text-lia-text-tertiary">
              <Clock className="h-4 w-4 text-lia-text-secondary" />
              <span className="text-xs">Horário</span>
            </div>
            <div className="font-semibold text-lia-text-primary">
              {data.time}
            </div>
            <div className="text-xs text-lia-text-tertiary">
              {data.duration}
            </div>
          </div>
        </div>

        <div
          className="p-3 rounded-xl border mb-4 bg-lia-bg-primary border-lia-border-subtle"
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lia-text-secondary">{getTypeIcon(data.type)}</span>
            <span className="text-sm font-medium text-lia-text-primary">
              {getTypeLabel(data.type)}
            </span>
          </div>
          {data.location && (
            <div className="text-sm text-lia-text-secondary">
              {data.location}
            </div>
          )}
          {data.meeting_link && (
            <div className="flex items-center gap-2 mt-2">
              <a
                href={data.meeting_link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-lia-text-secondary hover:underline flex items-center gap-1"
              >
                Acessar reunião
                <ExternalLink className="h-3 w-3" />
              </a>
              {onCopyLink && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 px-2 text-lia-text-secondary"
                  onClick={onCopyLink}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              )}
            </div>
          )}
        </div>

        {data.interviewers && data.interviewers.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 text-sm mb-2 text-lia-text-tertiary">
              <Users className="h-4 w-4" />
              Entrevistadores
            </div>
            <div className="flex flex-wrap gap-2">
              {data.interviewers.map((interviewer, index) => (
                <div
                  key={interviewer.name}
                  className="flex items-center gap-2 px-2 py-1 rounded-full bg-lia-bg-tertiary"
                >
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={interviewer.avatar} alt={interviewer.name} />
                    <AvatarFallback
                      className="text-xs bg-lia-bg-primary text-lia-text-secondary"
                    >
                      {getInitials(interviewer.name)}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm text-lia-text-secondary">
                    {interviewer.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.notes && (
          <div
            className="p-3 rounded-xl border mb-4 bg-lia-bg-tertiary border-lia-border-subtle"
          >
            <div className="text-xs mb-1 text-lia-text-secondary">Notas para o candidato</div>
            <p className="text-sm text-lia-text-secondary">{data.notes}</p>
          </div>
        )}

        <div
          className="flex items-center gap-2 pt-2 border-t border-lia-border-subtle"
        >
          {onAddToCalendar && (
            <Button
              size="sm"
              variant="outline"
              className="border-lia-border-default text-lia-text-primary"
              onClick={onAddToCalendar}
            >
              <Calendar className="h-3.5 w-3.5 mr-1.5" />
              Add ao Calendário
            </Button>
          )}
          {onSendReminder && (
            <Button
              size="sm"
              variant="ghost"
              className="text-lia-text-secondary"
              onClick={onSendReminder}
            >
              <Mail className="h-3.5 w-3.5 mr-1.5" />
              Enviar Lembrete
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
