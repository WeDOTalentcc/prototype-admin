"use client"

import {
  Clock,
  TrendingUp, Lightbulb, BarChart3, Brain, Zap, CheckCircle, Star, AlertCircle,
} from "lucide-react"
import { type Job } from "@/components/jobs"

interface JobPreviewLiaMetricsProps {
  previewJob: Job
}

const textStyles = {
  title: 'text-xs font-semibold text-lia-text-primary',
  bodySmall: 'text-micro text-lia-text-tertiary',
  label: 'text-xs text-lia-text-secondary',
}

export function JobPreviewLiaMetrics({ previewJob }: JobPreviewLiaMetricsProps) {
  return (
    <div data-testid="job-preview-lia-metrics" className="space-y-4">
      <div className="bg-lia-bg-secondary rounded-xl p-3">
        <div className="flex items-start gap-2">
          <Brain className="w-4 h-4 text-wedo-cyan mt-0.5" />
          <div className="flex-1">
            <h4 className={`${textStyles.title} mb-1`}>
              Performance de Triagem
            </h4>
            <p className={`${textStyles.bodySmall}`}>
              Análise detalhada do impacto da inteligência artificial no processo de triagem desta vaga
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-lia-bg-secondary rounded-xl p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Triagens Realizadas</span>
            <Clock className="w-3 h-3 text-lia-text-primary" />
          </div>
          <div className="text-2xl font-semibold text-lia-text-primary">
            {previewJob.liaMetrics?.triagens_realizadas ?? 0}
          </div>
          <div className="mt-1 text-xs text-lia-text-primary">
            de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
          </div>
        </div>

        <div className="bg-lia-bg-tertiary rounded-xl p-3 border border-lia-border-default">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Funil de Triagem</span>
            <TrendingUp className="w-3 h-3 text-lia-text-primary" />
          </div>
          <div className="text-2xl font-semibold text-lia-text-primary">
            {previewJob.liaMetrics?.pipeline_lia ?? 0}
          </div>
          <div className="mt-1 text-xs text-lia-text-primary">
            candidatos em triagem
          </div>
        </div>

        <div className="bg-lia-bg-secondary rounded-xl p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Sem Resposta</span>
            <Zap className="w-3 h-3 text-lia-text-primary" />
          </div>
          <div className="text-2xl font-semibold text-lia-text-primary">
            {previewJob.liaMetrics?.sem_resposta ?? 0}
          </div>
          <div className="mt-1 text-xs text-lia-text-primary">
            candidatos
          </div>
        </div>

        <div className="bg-lia-bg-tertiary rounded-xl p-3 border border-lia-border-default">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-primary">Taxa de Conclusão</span>
            <CheckCircle className="w-3 h-3 text-lia-text-primary" />
          </div>
          <div className="text-2xl font-semibold text-lia-text-primary">
            {(() => {
              const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
              const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
              return agendadas > 0 ? Math.round((realizadas / agendadas) * 100) : 0
            })()}%
          </div>
          <div className="mt-1 text-xs text-lia-text-primary">
            {previewJob.liaMetrics?.triagens_realizadas ?? 0} de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
          </div>
        </div>
      </div>

      <div className="bg-lia-bg-secondary rounded-xl p-3">
        <h4 className={`${textStyles.title} mb-3 flex items-center gap-1`}>
          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary" />
          Funil de Triagem
        </h4>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-lia-text-primary w-24">Funil de Triagem</span>
            <div className="flex-1 mx-2">
              <div className="bg-lia-interactive-active rounded-full h-3">
                <div className="bg-lia-border-medium h-3 rounded-full flex items-center justify-end pr-1 w-full">
                  <span className="text-xs text-white font-medium">{previewJob.liaMetrics?.pipeline_lia ?? 0}</span>
                </div>
              </div>
            </div>
            <span className="text-xs text-lia-text-primary w-10 text-right">100%</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-lia-text-primary w-24">Agendadas</span>
            <div className="flex-1 mx-2">
              <div className="bg-lia-interactive-active rounded-full h-3">
                {(() => {
                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                  const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                  const widthPercent = pipelineLia > 0 ? (triagensAgendadas / pipelineLia) * 100 : 0
                  return (
                    <div className="bg-lia-border-medium h-3 rounded-full flex items-center justify-end pr-1"
                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                      <span className="text-xs text-white font-medium">{triagensAgendadas}</span>
                    </div>
                  )
                })()}
              </div>
            </div>
            <span className="text-xs text-lia-text-primary w-10 text-right">
              {(() => {
                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                return pipelineLia > 0 ? Math.round((triagensAgendadas / pipelineLia) * 100) : 0
              })()}%
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-lia-text-primary w-24">Realizadas</span>
            <div className="flex-1 mx-2">
              <div className="bg-lia-interactive-active rounded-full h-3">
                {(() => {
                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                  const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                  const widthPercent = pipelineLia > 0 ? (triagensRealizadas / pipelineLia) * 100 : 0
                  return (
                    <div className="bg-lia-text-secondary h-3 rounded-full flex items-center justify-end pr-1"
                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                      <span className="text-xs text-white font-medium">{triagensRealizadas}</span>
                    </div>
                  )
                })()}
              </div>
            </div>
            <span className="text-xs text-lia-text-primary w-10 text-right">
              {(() => {
                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                return pipelineLia > 0 ? Math.round((triagensRealizadas / pipelineLia) * 100) : 0
              })()}%
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-lia-text-primary w-24">Entrevistas</span>
            <div className="flex-1 mx-2">
              <div className="bg-lia-interactive-active rounded-full h-3">
                {(() => {
                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                  const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                  const widthPercent = pipelineLia > 0 ? (entrevistasAgendadas / pipelineLia) * 100 : 0
                  return (
                    <div className="bg-lia-btn-primary-bg h-3 rounded-full flex items-center justify-end pr-1"
                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                      <span className="text-xs text-lia-btn-primary-text font-bold">{entrevistasAgendadas}</span>
                    </div>
                  )
                })()}
              </div>
            </div>
            <span className="text-xs text-lia-text-primary w-10 text-right">
              {(() => {
                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                return pipelineLia > 0 ? Math.round((entrevistasAgendadas / pipelineLia) * 100) : 0
              })()}%
            </span>
          </div>
        </div>
      </div>

      <div className="bg-lia-bg-secondary rounded-xl p-3">
        <h4 className={`${textStyles.title} mb-3 flex items-center gap-1`}>
          <Star className="w-3.5 h-3.5 text-lia-text-primary" />
          Média de Notas por Critério
        </h4>

        <div className="text-center py-4">
          <p className="text-xs text-lia-text-tertiary">
            Sem dados disponíveis
          </p>
          <p className="text-micro text-lia-text-muted mt-1">
            As médias serão exibidas após as triagens serem concluídas
          </p>
        </div>
      </div>

      <div className="bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-xl p-3 border border-wedo-purple/30 dark:border-wedo-purple/30">
        <h4 className={`${textStyles.title} mb-3 flex items-center gap-1`}>
          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary" />
          Resumo do Funil
        </h4>

        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-xs text-lia-text-primary mb-1">Total no Funil</p>
            <p className="text-base-ui font-semibold text-lia-text-primary">
              {previewJob.funnel.total}
            </p>
            <p className="text-micro text-lia-text-tertiary mt-1">candidatos</p>
          </div>

          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-xs text-lia-text-primary mb-1">Em Triagem</p>
            <p className="text-base-ui font-semibold text-lia-text-primary">
              {previewJob.funnel.screening}
            </p>
            <p className="text-micro text-lia-text-tertiary mt-1">candidatos</p>
          </div>

          <div className="text-center p-2 bg-lia-bg-secondary rounded-xl">
            <p className="text-xs text-lia-text-primary mb-1">Em Entrevista</p>
            <p className="text-base-ui font-semibold text-lia-text-primary">
              {previewJob.funnel.interview}
            </p>
            <p className="text-micro text-lia-text-tertiary mt-1">candidatos</p>
          </div>
        </div>
      </div>

      <div className="bg-status-warning/10 dark:bg-status-warning/20 rounded-xl p-3 border border-status-warning/30 dark:border-status-warning/30">
        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
          <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
          Candidatos Sem Resposta
        </h4>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className={`${textStyles.bodySmall}`}>Sem Resposta</span>
              <span className="text-xs font-bold text-status-warning dark:text-status-warning">
                {previewJob.liaMetrics?.sem_resposta ?? 0}
              </span>
            </div>
            <div className="bg-lia-interactive-active rounded-full h-1.5">
              {(() => {
                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                const percent = pipelineLia > 0 ? (semResposta / pipelineLia) * 100 : 0
                return <div className="bg-status-warning h-1.5 rounded-full" style={{width: `${percent}%`}}></div>
              })()}
            </div>
            <p className="text-xs text-lia-text-primary mt-1">
              {(() => {
                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                return pipelineLia > 0 ? `${Math.round((semResposta / pipelineLia) * 100)}% do funil` : 'N/A'
              })()}
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <span className={`${textStyles.bodySmall}`}>Aguardando</span>
              <span className="text-xs font-bold text-lia-text-secondary dark:text-wedo-cyan-dark">
                {(() => {
                  const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                  const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                  return Math.max(0, agendadas - realizadas)
                })()}
              </span>
            </div>
            <div className="bg-lia-interactive-active rounded-full h-1.5">
              {(() => {
                const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                const percent = agendadas > 0 ? ((agendadas - realizadas) / agendadas) * 100 : 0
                return <div className="bg-lia-btn-primary-bg h-1.5 rounded-full" style={{width: `${Math.max(0, percent)}%`}}></div>
              })()}
            </div>
            <p className="text-xs text-lia-text-primary mt-1">triagens pendentes</p>
          </div>
        </div>
      </div>

      <div className="bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 text-lia-text-primary mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-medium text-lia-text-primary font-semibold mb-1">
              Resumo da Triagem
            </p>
            <ul className="space-y-1 text-xs text-lia-text-primary">
              <li>• {previewJob.liaMetrics?.triagens_realizadas ?? 0} triagens realizadas de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas</li>
              <li>• {previewJob.liaMetrics?.entrevistas_agendadas ?? 0} entrevistas agendadas</li>
              <li>• {previewJob.liaMetrics?.sem_resposta ?? 0} candidatos sem resposta</li>
              <li>• {previewJob.liaMetrics?.pipeline_lia ?? 0} candidatos no funil LIA</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
