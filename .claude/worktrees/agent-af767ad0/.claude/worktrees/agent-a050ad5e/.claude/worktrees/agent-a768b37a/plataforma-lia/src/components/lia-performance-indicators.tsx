"use client"

import React from "react"
import { CheckCircle, Clock, XCircle, Calendar, Phone, MessageCircle, Target, TrendingUp } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface LiaPerformanceIndicatorsProps {
  candidate: any
}

export function LiaPerformanceIndicators({ candidate }: LiaPerformanceIndicatorsProps) {
  // Determinar status da triagem LIA
  const getTriageStatus = () => {
    if (candidate.triageComplete && candidate.triageData) {
      // Verificar se foi aprovado na triagem
      const isApproved =
        candidate.triageData.mobility === 'OK' &&
        candidate.triageData.salary !== 'Acima do budget' &&
        candidate.triageData.interest !== 'Baixo'

      return {
        status: isApproved ? 'approved' : 'completed-issues',
        label: isApproved ? 'Triagem OK' : 'Triagem c/ Ressalvas',
        icon: isApproved ? <CheckCircle className="w-3.5 h-3.5" /> : <Target className="w-3.5 h-3.5" />,
        color: isApproved
          ? 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-yellow-100 text-yellow-700 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-400'
      }
    }

    if (candidate.liaStatus === 'triagem_completa') {
      return {
        status: 'approved',
        label: 'Triagem OK',
        icon: <CheckCircle className="w-3.5 h-3.5" />,
        color: 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400'
      }
    }

    if (candidate.liaStatus === 'em_contato' || candidate.contactStatus === 'tentando contato') {
      return {
        status: 'in-progress',
        label: 'Em Contato',
        icon: <Clock className="w-3.5 h-3.5" />,
 color: 'bg-gray-100 text-wedo-cyan-dark border-gray-300 dark:border-gray-600 dark:text-gray-300'
      }
    }

    if (candidate.liaStatus === 'aguardando_aprovacao_contato' || candidate.approvalPending) {
      return {
        status: 'pending',
        label: 'Aguardando Aprovação',
        icon: <Clock className="w-3.5 h-3.5" />,
        color: 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900/30 dark:text-orange-400'
      }
    }

    if (candidate.contactStatus === 'não contatado') {
      return {
        status: 'not-started',
        label: 'Não Contatado',
        icon: <Phone className="w-3.5 h-3.5" />,
        color: 'bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-400'
      }
    }

    return {
      status: 'unknown',
      label: 'Status Indefinido',
      icon: <MessageCircle className="w-3.5 h-3.5" />,
      color: 'bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-400'
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
        <Badge
          variant="outline"
          className={`text-[11px] px-2 py-1 ${triageStatus.color}`}
        >
          {triageStatus.icon}
          <span className="ml-1">{triageStatus.label}</span>
        </Badge>
      </div>

      {/* Indicadores de Conversão */}
      <div className="flex items-center gap-1">
        {/* Contato Realizado */}
        {candidate.contactStatus !== 'não contatado' && (
          <div
 className="w-6 h-6 rounded bg-gray-100 flex items-center justify-center"
            title="Contato realizado pela LIA"
          >
 <Phone className="w-3 h-3 text-gray-600 dark:text-gray-300" />
          </div>
        )}

        {/* Triagem em Andamento ou Completa */}
        {(candidate.liaStatus === 'em_contato' || candidate.triageComplete || candidate.liaStatus === 'triagem_completa') && (
          <>
            <div className="w-3 h-px bg-gray-300 dark:bg-gray-600"></div>
            <div
              className={`w-6 h-6 rounded flex items-center justify-center ${
                candidate.triageComplete || candidate.liaStatus === 'triagem_completa'
                  ? 'bg-green-100 dark:bg-green-900/30'
                  : 'bg-yellow-100 dark:bg-yellow-900/30'
              }`}
              title={
                candidate.triageComplete || candidate.liaStatus === 'triagem_completa'
                  ? 'Triagem completa'
                  : 'Triagem em andamento'
              }
            >
              {candidate.triageComplete || candidate.liaStatus === 'triagem_completa' ? (
                <CheckCircle className="w-3 h-3 text-green-600 dark:text-green-400" />
              ) : (
                <Clock className="w-3 h-3 text-yellow-600 dark:text-yellow-400" />
              )}
            </div>
          </>
        )}

        {/* Entrevista Agendada */}
        {hasScheduledInterview && (
          <>
            <div className="w-3 h-px bg-gray-300 dark:bg-gray-600"></div>
            <div
              className="w-6 h-6 rounded bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center"
              title="Entrevista agendada"
            >
              <Calendar className="w-3 h-3 text-purple-600 dark:text-purple-400" />
            </div>
          </>
        )}
      </div>

      {/* Métricas Adicionais */}
      {candidate.triageData && (
        <div className="flex gap-1 flex-wrap">
          {candidate.triageData.mobility === 'OK' && (
            <div
              className="text-[11px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
              title="Mobilidade OK"
            >
              Mob ✓
            </div>
          )}
          {candidate.triageData.salary === 'Compatível' && (
            <div
              className="text-[11px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
              title="Salário compatível"
            >
              Sal ✓
            </div>
          )}
          {candidate.triageData.interest === 'Alto' && (
            <div
              className="text-[11px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
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
