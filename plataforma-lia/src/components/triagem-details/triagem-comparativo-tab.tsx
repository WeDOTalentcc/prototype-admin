"use client"

import { BarChart3, Target, Brain, Trophy } from "lucide-react"
import type { WSICandidateRanking, WSIVacancyRanking } from "@/services/lia-api"
import type { Candidate } from "@/components/pages/candidates/types"

interface TriagemComparativoTabProps {
  vacancyRanking: WSIVacancyRanking | null
  ranking: WSICandidateRanking | null
  candidate: Candidate
}

export function TriagemComparativoTab({ vacancyRanking, ranking, candidate }: TriagemComparativoTabProps) {
  if (!vacancyRanking || vacancyRanking.total_screened === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
          <BarChart3 className="w-6 h-6 text-lia-text-secondary" />
        </div>
        <div className="text-center max-w-xs">
          <p className="text-sm font-semibold text-lia-text-secondary">Ranking e Comparativo</p>
          <p className="text-xs text-lia-text-secondary mt-1" aria-live="polite" aria-atomic="true">
            O comparativo entre candidatos estará disponível quando houver 2 ou mais candidatos avaliados nesta vaga.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-4">
      {/* Pool averages */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Média Geral', value: vacancyRanking.averages.overall, icon: BarChart3 },
          { label: 'Média Técnica', value: vacancyRanking.averages.technical, icon: Target },
          { label: 'Média Comportamental', value: vacancyRanking.averages.behavioral, icon: Brain },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="border border-lia-border-subtle rounded-xl p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Icon className="w-3.5 h-3.5 text-lia-text-secondary" />
              <span className="text-micro text-lia-text-secondary uppercase tracking-wide">{label}</span>
            </div>
            <p className="text-lg font-semibold text-lia-text-primary">
              {value.toFixed(1)}<span className="text-xs text-lia-text-secondary">/10</span>
            </p>
          </div>
        ))}
      </div>

      {/* Ranking table */}
      <div className="border border-lia-border-subtle rounded-xl overflow-hidden">
        <div className="bg-lia-bg-secondary px-3 py-2 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Trophy className="w-3.5 h-3.5 text-lia-text-secondary" />
            <span className="text-xs font-semibold text-lia-text-secondary" aria-live="polite" aria-atomic="true">
              Ranking — {vacancyRanking.total_screened} candidato{vacancyRanking.total_screened !== 1 ? 's' : ''} avaliado{vacancyRanking.total_screened !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
        <div className="divide-y divide-lia-border-subtle">
          {vacancyRanking.ranking.map((entry) => {
            const isCurrent = entry.candidate_id === candidate?.id
            return (
              <div
                key={entry.result_id}
                className={`flex items-center gap-3 px-3 py-2.5 ${isCurrent ? 'bg-lia-btn-primary-bg' : 'hover:bg-lia-interactive-hover'}`}
              >
                {/* Rank badge */}
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-micro font-bold flex-shrink-0 ${
                  entry.rank === 1 ? 'bg-status-warning/10 text-status-warning' :
                  entry.rank === 2 ? 'bg-lia-bg-tertiary text-lia-text-secondary' :
                  entry.rank === 3 ? 'bg-wedo-orange/10 text-wedo-orange-text' :
                  isCurrent ? 'bg-lia-bg-primary text-lia-text-primary' : 'bg-lia-bg-tertiary text-lia-text-secondary'
                }`}>
                  {entry.rank}
                </div>
                {/* Name */}
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-medium truncate ${isCurrent ? 'text-white' : 'text-lia-text-primary'}`}>
                    {isCurrent ? `${entry.candidate_name} (você)` : entry.candidate_name}
                  </p>
                  {entry.candidate_title && (
                    <p className={`text-micro truncate ${isCurrent ? 'lia-text-muted' : 'lia-text-secondary'}`}>{entry.candidate_title}</p>
                  )}
                </div>
                {/* Scores */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="text-right">
                    <p className={`text-micro ${isCurrent ? 'lia-text-secondary' : 'lia-text-secondary'}`}>Tec</p>
                    <p className={`text-xs font-semibold ${isCurrent ? 'text-white' : 'text-lia-text-secondary'}`}>{entry.technical_wsi.toFixed(1)}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-micro ${isCurrent ? 'lia-text-secondary' : 'lia-text-secondary'}`}>Comp</p>
                    <p className={`text-xs font-semibold ${isCurrent ? 'text-white' : 'text-lia-text-secondary'}`}>{entry.behavioral_wsi.toFixed(1)}</p>
                  </div>
                  <div className="text-right min-w-[36px]">
                    <p className={`text-micro ${isCurrent ? 'lia-text-secondary' : 'lia-text-secondary'}`}>WSI</p>
                    <p className={`text-sm-ui font-bold ${isCurrent ? 'text-white' : 'text-lia-text-primary'}`}>{entry.overall_wsi.toFixed(1)}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
