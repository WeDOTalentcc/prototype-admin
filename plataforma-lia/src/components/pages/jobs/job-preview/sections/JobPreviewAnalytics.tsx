"use client"

import { CURRENCY_SYMBOL } from "@/lib/pricing"
import {
  Clock, Shield,
  Target, TrendingUp, Lightbulb, BarChart3,
} from "lucide-react"
import { type Job } from "@/components/jobs"
import { type JobVacancyMetrics } from "@/services/lia-api"

interface JobPreviewAnalyticsProps {
  previewJob: Job
  jobMetrics: JobVacancyMetrics | null
  isLoadingJobMetrics: boolean
}

const textStyles = {
  title: 'text-xs font-semibold text-lia-text-primary',
  bodySmall: 'text-micro text-lia-text-tertiary',
  label: 'text-xs text-lia-text-secondary',
}

export function JobPreviewAnalytics({ previewJob, jobMetrics, isLoadingJobMetrics }: JobPreviewAnalyticsProps) {
  return (
    <div data-testid="job-preview-analytics" className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-lia-bg-secondary rounded-xl p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Sucesso de Fechamento</span>
            <Target className="w-3 h-3 text-lia-text-primary" />
          </div>
          <div className="text-xl font-semibold text-lia-text-primary font-semibold">
            {isLoadingJobMetrics ? '...' : jobMetrics?.performance?.conversion_rate != null 
              ? `${Math.round(jobMetrics.performance.conversion_rate)}%` 
              : previewJob.funnel.hired > 0 
                ? `${Math.round((previewJob.funnel.hired / Math.max(previewJob.funnel.total, 1)) * 100)}%`
                : '—'}
          </div>
          <div className="mt-1 text-xs text-lia-text-primary">
            Pipeline: {jobMetrics?.funnel.total ?? previewJob.funnel.total} candidatos
          </div>
        </div>

        <div className="bg-lia-bg-tertiary rounded-xl p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Atividade 7d</span>
            <TrendingUp className="w-3 h-3 text-lia-text-secondary" />
          </div>
          <div className="text-xl font-semibold text-lia-text-primary">
            {isLoadingJobMetrics ? '...' : jobMetrics ? jobMetrics.activity.applications_7d : 0}
          </div>
          <div className="mt-1 text-xs text-lia-text-secondary">
            {isLoadingJobMetrics ? '...' : jobMetrics ? `${jobMetrics.activity.views_7d} visualizações` : 'Sem dados'}
          </div>
        </div>

        <div className="bg-lia-bg-secondary rounded-xl p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Tempo de Preenchimento</span>
            <Clock className="w-3 h-3 text-lia-text-primary" />
          </div>
          <div className="text-xl font-semibold text-lia-text-primary font-semibold">
            {isLoadingJobMetrics ? '...' : jobMetrics?.performance.time_to_fill_days != null ? `${jobMetrics.performance.time_to_fill_days}d` : (previewJob.urgencyLevel > 3 ? '15d' : previewJob.urgencyLevel > 2 ? '25d' : '35d')}
          </div>
          <div className="mt-1 text-xs text-lia-text-primary">
            {isLoadingJobMetrics ? '...' : jobMetrics?.activity.interviews_scheduled ? `${jobMetrics.activity.interviews_scheduled} entrevistas agendadas` : 'Sem entrevistas'}
          </div>
        </div>

        <div className={`rounded-md p-3 ${jobMetrics?.sla.within_sla === false ? 'bg-status-error/10 dark:bg-status-error/20' : 'bg-lia-bg-secondary'}`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Status SLA</span>
            <Shield className={`w-3 h-3 ${jobMetrics?.sla.within_sla === false ? 'text-status-error' : 'text-lia-text-primary'}`} />
          </div>
          <div className={`text-xl font-semibold font-semibold ${jobMetrics?.sla.within_sla === false ? 'text-status-error dark:text-status-error' : 'text-lia-text-primary'}`}>
            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.within_sla ? 'OK' : 'Atrasado'}
          </div>
          <div className={`mt-1 text-xs ${jobMetrics?.sla.within_sla === false ? 'text-status-error dark:text-status-error' : 'text-lia-text-primary'}`}>
            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.days_remaining != null ? `${jobMetrics.sla.days_remaining} dias restantes` : 'Sem prazo definido'}
          </div>
        </div>
      </div>

      <div className="bg-lia-bg-secondary rounded-xl p-3">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 text-lia-text-primary mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-medium text-lia-text-primary font-semibold mb-1">
              Insights de IA
            </p>
            <ul className="space-y-1 text-xs text-lia-text-primary">
              {previewJob.funnel.total < 10 && (
                <li>• Pipeline baixo: Ampliar divulgação ou revisar requisitos</li>
              )}
              {previewJob.seniority === 'Sênior' && (
                <li>• Alto risco de recusa: Prepare margem de negociação de 15-20%</li>
              )}
              {previewJob.funnel.screening > previewJob.funnel.interview * 3 && (
                <li>• Gargalo em entrevistas: Agilize agendamentos</li>
              )}
              {previewJob.urgencyLevel > 3 && previewJob.funnel.total < 20 && (
                <li>• Urgência vs Pipeline: Ative sourcing ativo e headhunting</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-lia-bg-secondary rounded-xl p-3">
        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary" />
          Comparativo com Mercado
        </h4>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className={`${textStyles.bodySmall}`}>Salário</p>
            <p className="text-sm font-bold text-lia-text-primary">
              {previewJob.salary > `${CURRENCY_SYMBOL} 10.000` ? '+15%' : '-5%'}
            </p>
            <p className={textStyles.bodySmall}>vs. mercado</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className={`${textStyles.bodySmall}`}>Candidatos</p>
            <p className="text-sm font-bold text-lia-text-primary">
              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
            </p>
            <p className={textStyles.bodySmall}>vs. média</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className={`${textStyles.bodySmall}`}>Atratividade</p>
            <p className="text-sm font-bold text-lia-text-primary">
              #—
            </p>
            <p className={textStyles.bodySmall}>ranking</p>
          </div>
        </div>
      </div>

      <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-3">
        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
          <Shield className="w-3.5 h-3.5 text-status-error" />
          Fatores de Risco
        </h4>
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-primary">Competitividade salarial</span>
            <div className="flex items-center gap-0.5">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1.5 h-2.5 rounded-full ${
                    i < (previewJob.seniority === 'Sênior' ? 4 : 2) ? 'bg-status-error' : 'bg-lia-border-default'
                  }`}
                />
              ))}
            </div>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-primary">Escassez de talentos</span>
            <div className="flex items-center gap-0.5">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1.5 h-2.5 rounded-full ${
                    i < (previewJob.seniority === 'Sênior' ? 3 : 1) ? 'bg-wedo-orange' : 'bg-lia-border-default'
                  }`}
                />
              ))}
            </div>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-primary">Tempo de processo</span>
            <div className="flex items-center gap-0.5">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1.5 h-2.5 rounded-full ${
                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-lia-border-medium' : 'bg-lia-border-default'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
