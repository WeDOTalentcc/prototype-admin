"use client"

import React from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from"@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Building2,
  MapPin,
  Briefcase,
  DollarSign,
  Users,
  Clock,
  CheckCircle2,
  Edit,
  ExternalLink,
  Laptop,
  Calendar
} from"lucide-react"

interface JobSummaryData {
  id: string
  title: string
  department?: string
  location?: string
  work_model?:"presencial" |"hibrido" |"remoto"
  seniority?: string
  salary_range?: {
    min: number
    max: number
    currency?: string
  }
  headcount?: number
  deadline?: string
  status?:"rascunho" |"ativa" |"pausada" |"fechada"
  required_skills?: string[]
  nice_to_have_skills?: string[]
  benefits_count?: number
  wsi_questions_count?: number
  candidates_count?: number
}

interface JobSummaryCardProps {
  data: JobSummaryData
  onEdit?: () => void
  onView?: () => void
  onPublish?: () => void
  compact?: boolean
}

export function JobSummaryCard({
  data,
  onEdit,
  onView,
  onPublish,
  compact = false
}: JobSummaryCardProps) {
  const formatCurrency = (value: number, currency ="BRL") => {
    return new Intl.NumberFormat("pt-BR", {
      style:"currency",
      currency,
      maximumFractionDigits: 0
    }).format(value)
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case"ativa":
        return (
          <Chip variant="success">
            <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
            Ativa
          </Chip>
        )
      case"rascunho":
        return <Chip variant="neutral" muted>Rascunho</Chip>
      case"pausada":
        return (
          <Chip variant="warning">
            <span className="w-1.5 h-1.5 rounded-full bg-status-warning" />
            Pausada
          </Chip>
        )
      case"fechada":
        return <Chip variant="neutral" muted>Fechada</Chip>
      default:
        return null
    }
  }

  const getWorkModelIcon = (model?: string) => {
    switch (model) {
      case"remoto":
        return <Laptop className="h-3.5 w-3.5" />
      case"hibrido":
        return <Building2 className="h-3.5 w-3.5" />
      default:
        return <MapPin className="h-3.5 w-3.5" />
    }
  }

  const getWorkModelLabel = (model?: string) => {
    switch (model) {
      case"remoto":
        return"100% Remoto"
      case"hibrido":
        return"Híbrido"
      default:
        return"Presencial"
    }
  }

  return (
    <Card
      className="w-full max-w-md border-l-4 overflow-hidden bg-lia-bg-secondary"
     
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-semibold text-lia-text-primary">
                {data.title}
              </h4>
              {getStatusBadge(data.status)}
            </div>
            {data.department && (
              <p className="text-sm mt-0.5 text-lia-text-secondary">
                {data.department}
              </p>
            )}
          </div>
          {data.candidates_count !== undefined && (
            <div
              className="text-center px-3 py-1 rounded-xl bg-lia-bg-tertiary"
            >
              <div className="text-lg font-semibold text-wedo-purple-text">{data.candidates_count}</div>
              <div className="text-xs text-lia-text-tertiary">candidatos</div>
            </div>
          )}
        </div>

        {!compact && (
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-lia-text-secondary">
            {data.location && (
              <div className="flex items-center gap-2">
                <MapPin className="h-3.5 w-3.5 text-lia-text-tertiary" />
                <span>{data.location}</span>
              </div>
            )}
            {data.work_model && (
              <div className="flex items-center gap-2">
                {getWorkModelIcon(data.work_model)}
                <span>{getWorkModelLabel(data.work_model)}</span>
              </div>
            )}
            {data.seniority && (
              <div className="flex items-center gap-2">
                <Briefcase className="h-3.5 w-3.5 text-lia-text-tertiary" />
                <span>{data.seniority}</span>
              </div>
            )}
            {data.headcount && (
              <div className="flex items-center gap-2">
                <Users className="h-3.5 w-3.5 text-lia-text-tertiary" />
                <span>{data.headcount} vaga{data.headcount > 1 ?"s" :""}</span>
              </div>
            )}
            {data.salary_range && (
              <div className="flex items-center gap-2 col-span-2">
                <DollarSign className="h-3.5 w-3.5 text-lia-text-secondary" />
                <span>
                  {formatCurrency(data.salary_range.min)} - {formatCurrency(data.salary_range.max)}
                </span>
              </div>
            )}
            {data.deadline && (
              <div className="flex items-center gap-2 col-span-2">
                <Calendar className="h-3.5 w-3.5 text-lia-text-tertiary" />
                <span>Prazo: {data.deadline}</span>
              </div>
            )}
          </div>
        )}

        {data.required_skills && data.required_skills.length > 0 && (
          <div className="mt-3">
            <div className="text-xs mb-1.5 text-lia-text-tertiary">
              Requisitos principais:
            </div>
            <div className="flex flex-wrap gap-1.5">
              {data.required_skills.slice(0, compact ? 3 : 5).map((skill, index) => (
                <Chip key={skill} variant="neutral" muted density="compact">
                  {skill}
                </Chip>
              ))}
              {data.required_skills.length > (compact ? 3 : 5) && (
                <Chip variant="neutral" density="compact">
                  +{data.required_skills.length - (compact ? 3 : 5)}
                </Chip>
              )}
            </div>
          </div>
        )}

        {!compact && (
          <div
            className="mt-4 pt-3 border-t flex items-center gap-4 text-xs border-lia-border-subtle text-lia-text-tertiary"
          >
            {data.benefits_count !== undefined && (
              <div className="flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-wedo-green" />
                {data.benefits_count} benefícios
              </div>
            )}
            {data.wsi_questions_count !== undefined && (
              <div className="flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-wedo-purple" />
                {data.wsi_questions_count} perguntas WSI
              </div>
            )}
          </div>
        )}

        {(onEdit || onView || onPublish) && (
          <div
            className="mt-4 pt-3 border-t flex items-center gap-2 border-lia-border-subtle"
          >
            {onEdit && (
              <Button
                size="sm"
                variant="outline"
                className="border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={onEdit}
              >
                <Edit className="h-3.5 w-3.5 mr-1.5" />
                Editar
              </Button>
            )}
            {onPublish && data.status ==="rascunho" && (
              <Button
                size="sm"
                className="bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={onPublish}
              >
                Publicar
              </Button>
            )}
            {onView && (
              <Button
                size="sm"
                variant="ghost"
                className="ml-auto text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={onView}
              >
                Ver Detalhes
                <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
