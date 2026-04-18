"use client"

import React, { useState } from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Textarea } from"@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Loader2, Check, X, HelpCircle, MapPin, Briefcase, Star } from"lucide-react"
import { CalibrationCandidate, CalibrationFeedbackData } from"../types"

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
}

type FeedbackStatus ="approved" |"rejected" |"maybe" | null

const MOCK_CANDIDATES: CalibrationCandidate[] = [
  {
    id:"cal_1",
    name:"Ricardo Mendes",
    title:"Senior Software Engineer",
    location:"São Paulo, SP",
    experience_years: 8,
    skills: ["React","Node.js","AWS","Python"],
    match_score: 92
  },
  {
    id:"cal_2",
    name:"Juliana Costa",
    title:"Full Stack Developer",
    location:"Rio de Janeiro, RJ",
    experience_years: 5,
    skills: ["Vue.js","Django","PostgreSQL"],
    match_score: 78
  },
  {
    id:"cal_3",
    name:"Fernando Alves",
    title:"Backend Developer",
    location:"Curitiba, PR",
    experience_years: 6,
    skills: ["Java","Spring Boot","Kubernetes"],
    match_score: 85
  },
  {
    id:"cal_4",
    name:"Camila Rodrigues",
    title:"Tech Lead",
    location:"Belo Horizonte, MG",
    experience_years: 10,
    skills: ["Python","Machine Learning","Leadership"],
    match_score: 88
  },
  {
    id:"cal_5",
    name:"Lucas Ferreira",
    title:"Frontend Developer",
    location:"Porto Alegre, RS",
    experience_years: 3,
    skills: ["React","TypeScript","Tailwind"],
    match_score: 65
  }
]

export function CalibrationFeedbackPanel({
  initialData = {},
  onSubmit,
  isLoading = false
}: PanelProps) {
  const [candidates] = useState<CalibrationCandidate[]>(() => {
    const initial = initialData.samples as CalibrationCandidate[] | undefined
    return initial && initial.length > 0 ? initial : MOCK_CANDIDATES
  })

  const [feedbackMap, setFeedbackMap] = useState<Record<string, FeedbackStatus>>(() => {
    const initialFeedback = initialData.feedback as CalibrationFeedbackData["feedback"] | undefined
    if (initialFeedback) {
      const map: Record<string, FeedbackStatus> = {}
      initialFeedback.approved?.forEach((id) => (map[id] ="approved"))
      initialFeedback.rejected?.forEach((id) => (map[id] ="rejected"))
      initialFeedback.maybe?.forEach((id) => (map[id] ="maybe"))
      return map
    }
    return {}
  })

  const [generalFeedback, setGeneralFeedback] = useState<string>(
    (initialData.general_feedback as string) ||""
  )

  const handleSetFeedback = (candidateId: string, status: FeedbackStatus) => {
    setFeedbackMap((prev) => ({
      ...prev,
      [candidateId]: prev[candidateId] === status ? null : status
    }))
  }

  const handleSubmit = async () => {
    const approved: string[] = []
    const rejected: string[] = []
    const maybe: string[] = []

    Object.entries(feedbackMap).forEach(([id, status]) => {
      if (status ==="approved") approved.push(id)
      else if (status ==="rejected") rejected.push(id)
      else if (status ==="maybe") maybe.push(id)
    })

    const data: CalibrationFeedbackData = {
      samples: candidates,
      feedback: {
        approved,
        rejected,
        maybe
      },
      general_feedback: generalFeedback || undefined
    }
    await onSubmit(data)
  }

  const getScoreStyle = (score: number): { bg: string; text: string } => {
    if (score >= 85) return { bg: 'var(--lia-btn-primary-bg)', text: 'var(--lia-btn-primary-text)' }
    if (score >= 70) return { bg: 'var(--lia-bg-tertiary)', text: 'var(--lia-text-primary)' }
    return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-tertiary)' }
  }

  const getStats = () => {
    const approved = Object.values(feedbackMap).filter((s) => s ==="approved").length
    const rejected = Object.values(feedbackMap).filter((s) => s ==="rejected").length
    const maybe = Object.values(feedbackMap).filter((s) => s ==="maybe").length
    const pending = candidates.length - approved - rejected - maybe
    return { approved, rejected, maybe, pending }
  }

  const stats = getStats()

  return (
    <div className="space-y-6">
      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            🎯 Calibração de Busca
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
            Avalie os candidatos abaixo para calibrar a busca. Sua avaliação ajudará
            a IA a entender melhor o perfil ideal para a vaga.
          </p>
          <div className="flex flex-wrap gap-3 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-lia-btn-primary-bg" />
              <span className="text-xs text-lia-text-secondary">{stats.approved} aprovados</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-lia-border-default" />
              <span className="text-xs text-lia-text-secondary">{stats.maybe} talvez</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-lia-text-tertiary" />
              <span className="text-xs text-lia-text-secondary">{stats.rejected} reprovados</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-lia-border-subtle" />
              <span className="text-xs text-lia-text-secondary">{stats.pending} pendentes</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {candidates.map((candidate) => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            status={feedbackMap[candidate.id] || null}
            onSetStatus={(status) => handleSetFeedback(candidate.id, status)}
            getScoreStyle={getScoreStyle}
          />
        ))}
      </div>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm flex items-center gap-2 font-sans text-lia-text-primary">
            💬 Feedback Geral
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={generalFeedback}
            onChange={(e) => setGeneralFeedback(e.target.value)}
            placeholder="Descreva o perfil ideal, o que você busca nos candidatos, ajustes na busca..."
            rows={4}
            className="dark:bg-lia-bg-primary dark:border-lia-border-subtle"
          />
        </CardContent>
      </Card>

      <Button
        onClick={handleSubmit}
        disabled={isLoading}
        className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none mr-2" />
            Salvando...
          </>
        ) : ("Concluir Calibração"
        )}
      </Button>
    </div>
  )
}

function CandidateCard({
  candidate,
  status,
  onSetStatus,
  getScoreStyle
}: {
  candidate: CalibrationCandidate
  status: FeedbackStatus
  onSetStatus: (status: FeedbackStatus) => void
  getScoreStyle: (score: number) => { bg: string; text: string }
}) {
  const getBorderStyle = () => {
    switch (status) {
      case"approved":
        return {
          borderColor: 'var(--lia-btn-primary-bg)',
          backgroundColor: 'var(--lia-bg-secondary)'
        }
      case"rejected":
        return {
          borderColor: 'var(--lia-text-tertiary)',
          backgroundColor: 'var(--lia-bg-tertiary)'
        }
      case"maybe":
        return {
          borderColor: 'var(--lia-border-default)',
          backgroundColor: 'var(--lia-bg-secondary)'
        }
      default:
        return {
          borderColor: 'var(--lia-border-subtle)',
          backgroundColor: 'transparent'
        }
    }
  }

  const borderStyle = getBorderStyle()
  const scoreStyle = getScoreStyle(candidate.match_score)

  return (
    <Card
      className="transition-colors motion-reduce:transition-none rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle"
      style={{borderColor: borderStyle.borderColor,
        backgroundColor: borderStyle.backgroundColor,
        borderWidth: '1px'}}
    >
      <CardContent className="pt-4">
        <div className="flex items-start gap-4">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center font-semibold text-lg shrink-0 bg-lia-bg-tertiary text-lia-text-primary"
          >
            {candidate.name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-lia-text-primary">
                  {candidate.name}
                </h3>
                <p className="text-xs text-lia-text-tertiary">
                  {candidate.title}
                </p>
              </div>
              <Chip variant="neutral" muted
                className="text-xs shrink-0 border-0"
                style={{backgroundColor: scoreStyle.bg, color: scoreStyle.text}}
              >
                <Star className="h-3 w-3 mr-1" />
                {candidate.match_score}%
              </Chip>
            </div>

            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-lia-text-tertiary">
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {candidate.location}
              </span>
              <span className="flex items-center gap-1">
                <Briefcase className="h-3 w-3" />
                {candidate.experience_years} anos
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5 mt-3">
              {candidate.skills.slice(0, 5).map((skill) => (
                <Chip
                  key={skill}
                  variant="neutral"
                  className="text-xs dark:border-lia-border-default border-lia-border-subtle text-lia-text-secondary"
                >
                  {skill}
                </Chip>
              ))}
              {candidate.skills.length > 5 && (
                <Chip
                  variant="neutral"
                  className="text-xs dark:border-lia-border-default border-lia-border-subtle text-lia-text-tertiary"
                >
                  +{candidate.skills.length - 5}
                </Chip>
              )}
            </div>

            <div className="flex gap-2 mt-4">
              <Button
                variant={status ==="approved" ?"primary" :"outline"}
                size="sm"
                className={status ==="approved"
 ?"flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  :"flex-1 dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"}
                style={status ==="approved" ? {} : {
                  backgroundColor: 'transparent',
                  color: 'var(--lia-text-secondary)',
                  borderColor: 'var(--lia-border-subtle)'
                }}
                onClick={() => onSetStatus("approved")}
              >
                <Check className="h-4 w-4 mr-1" />
                Aprovar
              </Button>
              <Button
                variant={status ==="maybe" ?"primary" :"outline"}
                size="sm"
                className={status ==="maybe"
 ?"flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  :"flex-1 dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"}
                style={status ==="maybe" ? {} : {
                  backgroundColor: 'transparent',
                  color: 'var(--lia-text-secondary)',
                  borderColor: 'var(--lia-border-subtle)'
                }}
                onClick={() => onSetStatus("maybe")}
              >
                <HelpCircle className="h-4 w-4 mr-1" />
                Talvez
              </Button>
              <Button
                variant={status ==="rejected" ?"primary" :"outline"}
                size="sm"
                className={status ==="rejected"
 ?"flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  :"flex-1 dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"}
                style={status ==="rejected" ? {} : {
                  backgroundColor: 'transparent',
                  color: 'var(--lia-text-secondary)',
                  borderColor: 'var(--lia-border-subtle)'
                }}
                onClick={() => onSetStatus("rejected")}
              >
                <X className="h-4 w-4 mr-1" />
                Reprovar
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
