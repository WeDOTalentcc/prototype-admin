"use client"

import { ExperienceHighlightCard } from "@/components/experience-highlight-card"
import { useCurrentCompany } from '@/hooks/company/use-current-company'
import { ProfileLiaOpinionCard } from './ProfileLiaOpinionCard'
import { QualificationMatrixCard, type QualificationMatrixData } from './QualificationMatrixCard'
import { ProfileSkillsMapCard } from './ProfileSkillsMapCard'
import { ProfileExperienceCards } from './ProfileExperienceCards'
import { ProfileInfoCards } from './ProfileInfoCards'
import type { LanguageEntry, OpinionsData } from './ProfileTabTypes'

export type { LanguageEntry, OpinionsData }
export type { OpinionEntry } from './ProfileTabTypes'

export interface CandidatePreviewProfileTabProps {
  candidate: Record<string, unknown>
  jobId?: string
  opinionsData: OpinionsData | null
  isLoadingOpinions: boolean
  isAnalyzingWithLia: boolean
  lastAnalysisDate: Date | null
  formatAnalysisDate: (date: Date | null) => string
  handleAnalyzeWithLia: () => void
  formatCurrency: (value: number | string | null | undefined, currency?: string) => string
  languagesData: LanguageEntry[]
  hasSalaryData: () => boolean
  hasAddressData: () => boolean
  getAddressString: () => string
  /** Critérios da busca ativa — quando presente (e sem jobId), mostra a matriz flat. */
  searchCriteria?: Record<string, unknown> | null
}

export function CandidatePreviewProfileTab({
  candidate,
  jobId,
  opinionsData,
  isLoadingOpinions,
  isAnalyzingWithLia,
  lastAnalysisDate,
  formatAnalysisDate,
  handleAnalyzeWithLia,
  formatCurrency,
  languagesData,
  hasSalaryData,
  hasAddressData,
  getAddressString,
  searchCriteria,
}: CandidatePreviewProfileTabProps) {
  const { companyId } = useCurrentCompany()
  const candidateId = String((candidate as { id?: unknown }).id ?? '')

  // Matriz da VAGA (grouped) vem do parecer salvo (score_breakdown.qualification_matrix).
  const currentOpinion =
    opinionsData?.current_general_opinion || opinionsData?.vacancy_opinions?.[0]
  const groupedMatrix =
    jobId && currentOpinion
      ? (((currentOpinion as { score_breakdown?: Record<string, unknown> })
          .score_breakdown?.qualification_matrix as QualificationMatrixData | undefined) ?? null)
      : null

  return (
    <div className="p-3 space-y-3">
      <ExperienceHighlightCard candidate={candidate as { id: string; name: string }} companyId={companyId || ''} />

      {/* Matriz de qualificação: vaga (grouped, do parecer) ou busca (flat, on-the-fly). */}
      <QualificationMatrixCard
        candidateId={candidateId}
        companyId={companyId || ''}
        matrix={groupedMatrix}
        searchCriteria={!jobId ? searchCriteria : null}
      />

      <ProfileLiaOpinionCard
        jobId={jobId}
        opinionsData={opinionsData}
        isLoadingOpinions={isLoadingOpinions}
        isAnalyzingWithLia={isAnalyzingWithLia}
        lastAnalysisDate={lastAnalysisDate}
        formatAnalysisDate={formatAnalysisDate}
        handleAnalyzeWithLia={handleAnalyzeWithLia}
      />

      <ProfileSkillsMapCard candidate={candidate} />

      <ProfileExperienceCards candidate={candidate} />

      <ProfileInfoCards
        candidate={candidate}
        formatCurrency={formatCurrency}
        languagesData={languagesData}
        hasSalaryData={hasSalaryData}
        hasAddressData={hasAddressData}
        getAddressString={getAddressString}
      />
    </div>
  )
}
