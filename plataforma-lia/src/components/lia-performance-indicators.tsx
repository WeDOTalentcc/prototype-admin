"use client"

import React from"react"
import { CheckCircle, Clock, XCircle, Calendar, Phone, MessageCircle, Target, TrendingUp } from"lucide-react"
import { Chip } from "@/components/ui/chip"

interface LiaPerformanceIndicatorsProps {
  candidate: Record<string, any>
}

export function LiaPerformanceIndicators({ candidate }: LiaPerformanceIndicatorsProps) {
  // Determinar status da triagem LIA
  const getTriageStatus = () => {
    if (candidate.triageComplete && candidate.triageData) {
      // Verificar se foi aprovado na triagem
      const triageData = candidate.triageData as Record<string, unknown>
      const isApproved =
        triageData.mobility === 'OK' &&
        triageData.salary !== 'Acima do budget' &&
        triageData.interest !== 'Baixo'

      return {
        status: isApproved ? 'approved' : 'completed-issues',
        label: isApproved ? 'Triagem OK' : 'Triagem c/ Ressalvas',
        icon: isApproved ? <CheckCircle className="w-3.5 h-3.5" /> : <Target className="w-3.5 h-3.5" />,
        color: isApproved
          ? ' border-status-success/30 dark:bg-status-success/30 dark:text-status-success'
          : ' border-status-warning/30 dark:text-status-warning'
      }
    }

    if (candidate.liaStatus === 'triagem_completa') {
      return {
        status: 'approved',
        label: 'Triagem OK',
        icon: <CheckCircle className="w-3.5 h-3.5" />,
        color: ' border-status-success/30 dark:bg-status-success/30 dark:text-status-success'
      }
    }

    if (candidate.liaStatus === 'em_contato' || candidate.contactStatus === 'tentando contato') {
      return {
        status: 'in-progress',
        label: 'Em Contato',
        icon: <Clock className="w-3.5 h-3.5" />,
 color: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default'
      }
    }

    if (candidate.liaStatus === 'aguardando_aprovacao_contato' || candidate.approvalPending) {
      return {
        status: 'pending',
        label: 'Aguardando Aprovação',
        icon: <Clock className="w-3.5 h-3.5" />,
        color: ' border-wedo-orange/30 dark:bg-wedo-orange/10/30 dark:text-wedo-orange'
      }
    }

    if (candidate.contactStatus === 'não contatado') {
      return {
        status: 'not-started',
        label: 'Não Contatado',
        icon: <Phone className="w-3.5 h-3.5" />,
        color: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default dark:bg-lia-bg-secondary'
      }
    }

    return {
      status: 'unknown',
      label: 'Status Indefinido',
      icon: <MessageCircle className="w-3.5 h-3.5" />,
      color: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default dark:bg-lia-bg-secondary'
    }
  }

  const triageStatus = getTriageStatus()

  // Verificar se tem entrevista agendada
  const hasScheduledInterview =
    candidate.status === 'Entrevista marcada' ||
    candidate.status === 'Entrevista agendada' ||
    candidate.stage === 'Entrevista'

  return (
    <div className="flex flex-col gap-2">
      {/* Status da Triagem */}
      <div className="flex items-center gap-2">
        <Chip
          variant="neutral"
          className={`text-xs px-2 py-1 ${triageStatus.color}`}
        >
          {triageStatus.icon}
          <span className="ml-1">{triageStatus.label}</span>
        </Chip>
      </div>

      {/* Indicadores de Conversão */}
      <div className="flex items-center gap-1">
        {/* Contato Realizado */}
        {candidate.contactStatus !== 'não contatado' && (
          <div
 className="w-6 h-6 rounded-xl bg-lia-bg-tertiary flex items-center justify-center"
            title="Contato realizado pela IA"
          >
 <Phone className="w-3 h-3 text-lia-text-secondary" />
          </div>
        )}

        {/* Triagem em Andamento ou Completa */}
        {(candidate.liaStatus === 'em_contato' || candidate.triageComplete || candidate.liaStatus === 'triagem_completa') && (
          <>
            <div className="w-3 h-px bg-lia-border-default"></div>
            <div
              className={`w-6 h-6 rounded-md flex items-center justify-center ${
 candidate.triageComplete || candidate.liaStatus === 'triagem_completa'
                  ? 'bg-status-success/15 dark:bg-status-success/30'
                  : 'bg-status-warning/15'
              }`}
              title={
                candidate.triageComplete || candidate.liaStatus === 'triagem_completa'
                  ? 'Triagem completa'
                  : 'Triagem em andamento'
              }
            >
              {candidate.triageComplete || candidate.liaStatus === 'triagem_completa' ? (
                <CheckCircle className="w-3 h-3 text-status-success dark:text-status-success" />
              ) : (
                <Clock className="w-3 h-3 text-status-warning dark:text-status-warning" />
              )}
            </div>
          </>
        )}

        {/* Entrevista Agendada */}
        {hasScheduledInterview && (
          <>
            <div className="w-3 h-px bg-lia-border-default"></div>
            <div
              className="w-6 h-6 rounded-md bg-wedo-purple/15 dark:bg-wedo-purple/30 flex items-center justify-center"
              title="Entrevista agendada"
            >
              <Calendar className="w-3 h-3 text-wedo-purple dark:text-wedo-purple" />
            </div>
          </>
        )}
      </div>

      {/* Métricas Adicionais */}
      {candidate.triageData && (
        <div className="flex gap-1 flex-wrap">
          {(candidate.triageData as Record<string, unknown>).mobility === 'OK' && (
            <div
              className="text-micro px-1.5 py-0.5 rounded-full  dark:bg-status-success/20 dark:text-status-success"
              title="Mobilidade OK"
            >
              Mob ✓
            </div>
          )}
          {(candidate.triageData as Record<string, unknown>).salary === 'Compatível' && (
            <div
              className="text-micro px-1.5 py-0.5 rounded-full  dark:bg-status-success/20 dark:text-status-success"
              title="Salário compatível"
            >
              Sal ✓
            </div>
          )}
          {(candidate.triageData as Record<string, unknown>).interest === 'Alto' && (
            <div
              className="text-micro px-1.5 py-0.5 rounded-full  dark:bg-status-success/20 dark:text-status-success"
              title="Interesse alto"
            >
              Int ✓
            </div>
          )}
        </div>
      )}
    </div>
  )
}
