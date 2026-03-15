// ARCHIVED: Tab Métricas LIA - Removida em 15/01/2026 para simplificação do MVP

"use client"

import React from "react"
import { Brain, Clock, TrendingUp, Zap, CheckCircle, BarChart3, Star, AlertCircle, Lightbulb } from "lucide-react"
import { textStyles } from '@/lib/design-tokens'

interface JobFunnel {
  total: number
  screening: number
  interview: number
  final: number
  hired: number
}

interface PreviewJob {
  funnel: JobFunnel
  level: string
  urgencyLevel: number
  [key: string]: any
}

interface LiaMetricsTabProps {
  previewJob: PreviewJob
}

export function LiaMetricsTab({ previewJob }: LiaMetricsTabProps) {
  return (
    <div className="space-y-4">
      {/* Header com Resumo */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
        <div className="flex items-start gap-2">
          <Brain className="w-4 h-4 text-gray-600 dark:text-gray-600 mt-0.5" />
          <div className="flex-1">
            <h4 className={`${textStyles.title} dark:text-gray-100 mb-1`}>
              Performance LIA - Triagens Automatizadas
            </h4>
            <p className={`${textStyles.bodySmall} dark:text-gray-600`}>
              Análise detalhada do impacto da inteligência artificial no processo de triagem desta vaga
            </p>
          </div>
        </div>
      </div>

      {/* Métricas Principais - Grid 2x2 */}
      <div className="grid grid-cols-2 gap-3">
        {/* Horas Economizadas */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Horas Economizadas</span>
            <Clock className="w-3 h-3 text-gray-600 dark:text-gray-600" />
          </div>
          <div className="text-2xl font-bold text-gray-950 dark:text-gray-100">
            {(() => {
              const triagens = Math.round(previewJob.funnel.total * 0.85)
              const horasEconomizadas = Math.round((triagens * 15) / 60)
              return horasEconomizadas
            })()}h
          </div>
          <div className="mt-1 text-[11px] text-gray-600 dark:text-gray-600">
            ≈ {Math.round((Math.round(previewJob.funnel.total * 0.85) * 15) / 60 / 8)} dias de trabalho
          </div>
        </div>

        {/* ROI da LIA */}
        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-gray-300 dark:border-gray-600">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-medium text-gray-800 dark:text-gray-200">ROI da LIA</span>
            <TrendingUp className="w-3 h-3 text-gray-600 dark:text-gray-600" />
          </div>
          <div className="text-2xl font-bold text-gray-950 dark:text-gray-100">
            {(() => {
              const triagens = Math.round(previewJob.funnel.total * 0.85)
              const horasEconomizadas = Math.round((triagens * 15) / 60)
              const custoHora = 80
              const economia = horasEconomizadas * custoHora
              const roi = Math.round((economia / 1000) * 10) / 10
              return roi
            })()}x
          </div>
          <div className="mt-1 text-[11px] text-gray-600 dark:text-gray-600">
            R$ {(() => {
              const triagens = Math.round(previewJob.funnel.total * 0.85)
              const horasEconomizadas = Math.round((triagens * 15) / 60)
              return (horasEconomizadas * 80).toLocaleString('pt-BR')
            })()} economizados
          </div>
        </div>

        {/* Tempo Médio de Triagem */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Tempo Médio/Triagem</span>
            <Zap className="w-3 h-3 text-gray-600 dark:text-gray-600" />
          </div>
          <div className="text-2xl font-bold text-gray-950 dark:text-gray-100">
            2.3min
          </div>
          <div className="mt-1 text-[11px] text-gray-600 dark:text-gray-600">
            vs 15min manual
          </div>
        </div>

        {/* Taxa de Conclusão */}
        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-gray-300 dark:border-gray-600">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Taxa de Conclusão</span>
            <CheckCircle className="w-3 h-3 text-gray-600 dark:text-gray-600" />
          </div>
          <div className="text-2xl font-bold text-gray-950 dark:text-gray-100">
            {(() => {
              const realizadas = Math.round(previewJob.funnel.screening * 0.6)
              const agendadas = Math.round(previewJob.funnel.screening * 0.7)
              return agendadas > 0 ? Math.round((realizadas / agendadas) * 100) : 0
            })()}%
          </div>
          <div className="mt-1 text-[11px] text-gray-600 dark:text-gray-600">
            {Math.round(previewJob.funnel.screening * 0.6)} de {Math.round(previewJob.funnel.screening * 0.7)} agendadas
          </div>
        </div>
      </div>

      {/* Funil LIA Detalhado */}
      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
        <h4 className={`${textStyles.title} dark:text-gray-100 mb-3 flex items-center gap-1`}>
          <BarChart3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-600" />
          Funil de Triagem LIA
        </h4>

        <div className="space-y-2">
          {/* Pipeline */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600 dark:text-gray-600 w-24">Contatados</span>
            <div className="flex-1 mx-2">
              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1" style={{ width: '100%' }}>
                  <span className="text-[11px] text-white font-medium">{Math.round(previewJob.funnel.total * 0.85)}</span>
                </div>
              </div>
            </div>
            <span className="text-[11px] text-gray-600 w-10 text-right">100%</span>
          </div>

          {/* Agendadas */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600 dark:text-gray-600 w-24">Agendadas</span>
            <div className="flex-1 mx-2">
              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                <div className="bg-gray-500 dark:bg-gray-400 h-3 rounded-full flex items-center justify-end pr-1"
                     style={{ width: `${(Math.round(previewJob.funnel.screening * 0.7) / Math.round(previewJob.funnel.total * 0.85)) * 100}%` }}>
                  <span className="text-[11px] text-white font-medium">{Math.round(previewJob.funnel.screening * 0.7)}</span>
                </div>
              </div>
            </div>
            <span className="text-[11px] text-gray-600 w-10 text-right">
              {Math.round((Math.round(previewJob.funnel.screening * 0.7) / Math.round(previewJob.funnel.total * 0.85)) * 100)}%
            </span>
          </div>

          {/* Realizadas */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600 dark:text-gray-600 w-24">Realizadas</span>
            <div className="flex-1 mx-2">
              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                <div className="bg-gray-600 dark:bg-gray-300 h-3 rounded-full flex items-center justify-end pr-1"
                     style={{ width: `${(Math.round(previewJob.funnel.screening * 0.6) / Math.round(previewJob.funnel.total * 0.85)) * 100}%` }}>
                  <span className="text-[11px] text-white dark:text-gray-900 font-medium">{Math.round(previewJob.funnel.screening * 0.6)}</span>
                </div>
              </div>
            </div>
            <span className="text-[11px] text-gray-600 w-10 text-right">
              {Math.round((Math.round(previewJob.funnel.screening * 0.6) / Math.round(previewJob.funnel.total * 0.85)) * 100)}%
            </span>
          </div>

          {/* Aprovados */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600 dark:text-gray-600 w-24">Aprovados</span>
            <div className="flex-1 mx-2">
              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                <div className="bg-gray-900 dark:bg-gray-100 h-3 rounded-full flex items-center justify-end pr-1"
                     style={{ width: `${(Math.round(previewJob.funnel.interview * 0.8) / Math.round(previewJob.funnel.total * 0.85)) * 100}%` }}>
                  <span className="text-[11px] text-white dark:text-gray-900 font-bold">{Math.round(previewJob.funnel.interview * 0.8)}</span>
                </div>
              </div>
            </div>
            <span className="text-[11px] text-gray-600 w-10 text-right">
              {Math.round((Math.round(previewJob.funnel.interview * 0.8) / Math.round(previewJob.funnel.total * 0.85)) * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Média de Notas por Pergunta */}
      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
        <h4 className={`${textStyles.title} dark:text-gray-100 mb-3 flex items-center gap-1`}>
          <Star className="w-3.5 h-3.5 text-gray-600 dark:text-gray-600" />
          Média de Notas por Critério
        </h4>

        <div className="space-y-2">
          {[
            { criterio: 'Experiência Técnica', nota: 8.2, cor: 'bg-gray-600 dark:bg-gray-400' },
            { criterio: 'Fit Cultural', nota: 7.8, cor: 'bg-gray-500 dark:bg-gray-500' },
            { criterio: 'Comunicação', nota: 8.5, cor: 'bg-gray-800 dark:bg-gray-200' },
            { criterio: 'Disponibilidade', nota: 9.1, cor: 'bg-gray-950 dark:bg-gray-50' },
            { criterio: 'Expectativa Salarial', nota: 6.9, cor: 'bg-gray-400 dark:bg-gray-600' }
          ].map((item, idx) => (
            <div key={idx} className="flex items-center justify-between">
              <span className="text-xs text-gray-600 dark:text-gray-600 w-32">{item.criterio}</span>
              <div className="flex-1 mx-2">
                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div className={`${item.cor} h-2 rounded-full`} style={{ width: `${(item.nota / 10) * 100}%` }}></div>
                </div>
              </div>
              <span className="text-xs font-bold text-gray-950 dark:text-gray-50 w-8 text-right">{item.nota}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Comparação com Outras Vagas */}
      <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-md p-3 border border-indigo-200 dark:border-indigo-800">
        <h4 className={`${textStyles.title} dark:text-gray-100 mb-3 flex items-center gap-1`}>
          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
          Comparação com Outras Vagas
        </h4>

        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
            <p className="text-[11px] text-gray-600 dark:text-gray-600 mb-1">Média de Notas</p>
            <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">8.1</p>
            <div className="flex items-center justify-center gap-1 mt-1">
              <TrendingUp className="w-2.5 h-2.5 text-gray-600 dark:text-gray-600" />
              <span className="text-[11px] text-gray-800 dark:text-gray-200">+12% vs média</span>
            </div>
          </div>

          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
            <p className="text-[11px] text-gray-600 dark:text-gray-600 mb-1">Taxa Aprovação</p>
            <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">
              {Math.round((Math.round(previewJob.funnel.interview * 0.8) / Math.round(previewJob.funnel.screening * 0.6)) * 100)}%
            </p>
            <div className="flex items-center justify-center gap-1 mt-1">
              <TrendingUp className="w-2.5 h-2.5 text-gray-600 dark:text-gray-600" />
              <span className="text-[11px] text-gray-800 dark:text-gray-200">+8% vs média</span>
            </div>
          </div>

          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
            <p className="text-[11px] text-gray-600 dark:text-gray-600 mb-1">Qualidade</p>
            <p className="text-lg font-bold text-gray-950 dark:text-gray-50 font-semibold">A+</p>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Star className="w-2.5 h-2.5 text-gray-600 dark:text-gray-600" />
              <span className={textStyles.bodySmall}>Top 10%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Taxa de Desistência */}
      <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-3 border border-red-200 dark:border-red-800">
        <h4 className={`${textStyles.title} dark:text-gray-100 mb-2 flex items-center gap-1`}>
          <AlertCircle className="w-3.5 h-3.5 text-red-600" />
          Taxa de Desistência
        </h4>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className={`${textStyles.bodySmall} dark:text-gray-600`}>Não Responderam</span>
              <span className="text-xs font-bold text-red-700 dark:text-red-300">
                {Math.round(previewJob.funnel.total * 0.15)}
              </span>
            </div>
            <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
              <div className="bg-red-500 h-1.5 rounded-full" style={{ width: '15%' }}></div>
            </div>
            <p className="text-[11px] text-gray-600 mt-1">15% do total</p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Cancelaram</span>
              <span className="text-xs font-bold text-orange-700 dark:text-orange-300">
                {Math.round(previewJob.funnel.screening * 0.1)}
              </span>
            </div>
            <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
              <div className="bg-orange-500 h-1.5 rounded-full" style={{ width: '10%' }}></div>
            </div>
            <p className="text-[11px] text-gray-600 mt-1">10% agendados</p>
          </div>
        </div>
      </div>

      {/* Insights e Recomendações */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 border border-yellow-200 dark:border-yellow-800">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-medium text-gray-800 dark:text-gray-200 font-semibold mb-1">
              Insights da LIA
            </p>
            <ul className="space-y-1 text-[11px] text-gray-800 dark:text-gray-200">
              <li>• Triagens 6.5x mais rápidas que processo manual</li>
              <li>• Economia de R$ {(() => {
                const triagens = Math.round(previewJob.funnel.total * 0.85)
                const horasEconomizadas = Math.round((triagens * 15) / 60)
                return (horasEconomizadas * 80).toLocaleString('pt-BR')
              })()} em custos de recrutamento</li>
              <li>• Taxa de aprovação 8% acima da média geral</li>
              <li>• Candidatos com fit cultural 12% superior</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
