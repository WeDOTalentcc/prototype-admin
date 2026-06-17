"use client"

import React from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  TrendingUp, Clock, Phone, Calendar, Award, Zap, CheckCircle
} from"lucide-react"
import { textStyles } from"@/lib/design-tokens"
import type { LiaMetricsData } from"@/hooks/ai/use-lia-metrics-data"

interface LiaMetricsKpiCardsProps {
  data: LiaMetricsData
}

export function LiaMetricsKpiCards({ data }: LiaMetricsKpiCardsProps) {
  const {
    contacted, totalCandidates, contactRate,
    triageCompleted, triageConversionRate,
    triageApproved, triageApprovalRate,
    interviewScheduled, interviewConversionRate,
    avgTimeContact, avgLiaScore, avgSkillsMatch,
  } = data

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3">
      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-1">
            <Phone className="w-4 h-4 text-lia-text-secondary" />
            <Chip variant="neutral" muted className={`text-xs px-1.5 py-0.5 ${contactRate >= 80 ? 'bg-status-success' : contactRate >= 60 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
              {contactRate.toFixed(0)}%
            </Chip>
          </div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {contacted}/{totalCandidates}
          </div>
          <div className={`${textStyles.bodySmall}`}>
            Taxa de Contato
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-1">
            <CheckCircle className="w-4 h-4 text-status-success" />
            <Chip variant="neutral" muted className={`text-xs px-1.5 py-0.5 ${triageConversionRate >= 70 ? 'bg-status-success' : triageConversionRate >= 50 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
              {triageConversionRate.toFixed(0)}%
            </Chip>
          </div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {triageCompleted}/{contacted}
          </div>
          <div className={`${textStyles.bodySmall}`}>
            Taxa de Triagem
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-1">
            <Award className="w-4 h-4 text-status-success" />
            <Chip variant="neutral" muted className={`text-xs px-1.5 py-0.5 ${triageApprovalRate >= 60 ? 'bg-status-success' : triageApprovalRate >= 40 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
              {triageApprovalRate.toFixed(0)}%
            </Chip>
          </div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {triageApproved}/{triageCompleted}
          </div>
          <div className={`${textStyles.bodySmall}`}>
            Taxa de Aprovação
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-1">
            <Calendar className="w-4 h-4 text-wedo-purple" />
            <Chip variant="neutral" muted className={`text-xs px-1.5 py-0.5 ${interviewConversionRate >= 50 ? 'bg-status-success' : interviewConversionRate >= 30 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
              {interviewConversionRate.toFixed(0)}%
            </Chip>
          </div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {interviewScheduled}/{triageApproved}
          </div>
          <div className={`${textStyles.bodySmall}`}>
            Agendamentos
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-1">
            <Clock className="w-4 h-4 text-wedo-orange" />
            <TrendingUp className="w-3 h-3 text-status-success" />
          </div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {avgTimeContact.toFixed(1)}h
          </div>
          <div className={`${textStyles.bodySmall}`}>
            Tempo Contato
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between mb-1">
            <Zap className="w-4 h-4 text-lia-text-secondary" />
            <Chip density="relaxed" variant="neutral" muted className="px-1.5 py-0.5">
              {avgLiaScore.toFixed(1)}
            </Chip>
          </div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {avgSkillsMatch}%
          </div>
          <div className={`${textStyles.bodySmall}`}>
            Score/Match
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
