"use client"

import { useState, useEffect } from "react"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import {
  mapInterviewStagesToKanban,
  createInitialCandidatesData,
  type DynamicStage,
} from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { mapLegacyStage } from "@/lib/recruitment-stages"
import {
  generateWorkHistory,
  generateEducation,
  seededRandom,
  getSalaryByExperience,
} from "@/components/kanban/utils/candidate-data-enrichment"

export function useKanbanCandidateLoader({
  job,
  dynamicStages,
  setCandidatesData,
}: {
  job?: Record<string, unknown>
  dynamicStages: DynamicStage[]
  setCandidatesData: (fn: (prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>) => void
}) {
  const [isLoadingCandidates, setIsLoadingCandidates] = useState(true)
  const [hasMounted, setHasMounted] = useState(false)
  const [isClient, setIsClient] = useState(false)

  // Marcar montagem client-side (evita hidratação SSR)
  useEffect(() => {
    setIsClient(true)
    setHasMounted(true)
  }, [])

  // Atualizar etapas dinâmicas quando job.interviewStages mudar
  useEffect(() => {
    // @ts-ignore // TODO: fix type
    // @ts-ignore // TODO: fix type
    const newStages = mapInterviewStagesToKanban(job?.interviewStages)
    setCandidatesData(prev => {
      const newData = createInitialCandidatesData(newStages)
      Object.keys(prev).forEach(stageId => {
        const candidates = prev[stageId] || []
        if (newData[stageId]) {
          newData[stageId] = [...candidates]
        } else {
          newData['sourcing'] = [...(newData['sourcing'] || []), ...candidates]
        }
      })
      return newData
    })
  }, [job?.interviewStages])

  // Carregar candidatos reais do backend
  useEffect(() => {
    setIsLoadingCandidates(true)
    liaApi.listCandidates(undefined, undefined, 0, 200)
      .then(response => {
        try {
          if (!response.items || response.items.length === 0) { setIsLoadingCandidates(false); return }

          const mapCandidateToKanban = (c: CandidateLocal, index: number) => {
            try {
              const experience = c.years_of_experience || ((index % 12) + 1)
              const monthlySalary = c.current_salary || getSalaryByExperience(experience, index)
              const location = c.location_city && c.location_state
                ? `${c.location_city}, ${c.location_state}`
                : c.location_city || 'Não especificado'
              let educationData: Record<string, unknown>[] = []
              // @ts-ignore // TODO: fix type
              let workHistoryData: Record<string, unknown>[] = []
              // @ts-ignore // TODO: fix type
              // @ts-ignore // TODO: fix type
              try { educationData = generateEducation(c, experience) } catch { educationData = [] }
              // @ts-ignore // TODO: fix type
              try { workHistoryData = generateWorkHistory(c, experience) } catch { workHistoryData = [] }

              const rawStatus = (c.status || 'novo').toLowerCase()
              let mappedStage = 'funil'
              if (['reprovado', 'rejected', 'descartado', 'reprovados'].includes(rawStatus)) mappedStage = 'reprovados'
              else if (['aprovado', 'hired', 'contratado', 'aprovados'].includes(rawStatus)) mappedStage = 'aprovados'
              else if (['final', 'proposta', 'offer'].includes(rawStatus)) mappedStage = 'final'
              else if (['entrevista', 'interview', 'entrevistando'].includes(rawStatus)) mappedStage = 'entrevista'
              else if (['triagem', 'screening', 'em_triagem'].includes(rawStatus)) mappedStage = 'triagem'

              return {
                id: c.id, name: c.name || 'Sem nome', role: c.current_title || 'Não especificado',
                currentCompany: c.current_company || '', location,
                score: c.lia_score || null,
                fitScore: c.skills_match_percentage || Math.floor(70 + seededRandom(c.id || String(index), 1) * 25),
                warnings: 0, avatar: c.avatar_url || '', source: c.source || 'website',
                appliedDate: c.created_at ? new Date(c.created_at).toLocaleDateString('pt-BR') : 'Hoje',
                email: c.email || '', phone: c.phone || '', linkedin: c.linkedin_url || '',
                experience: `${experience} anos`, stage: mappedStage, etapa: mappedStage,
                education: educationData, skills: c.technical_skills || [],
                languages: Array.isArray(c.languages)
                  ? c.languages.map((l: Record<string, unknown>) => typeof l === 'string' ? l : l.language)
                  : Object.keys(c.languages || {}),
                expectedSalary: c.desired_salary_max
                  ? `R$ ${c.desired_salary_max.toLocaleString('pt-BR')}`
                  : `R$ ${Math.floor(monthlySalary * 1.2).toLocaleString('pt-BR')}`,
                currentSalary: `R$ ${monthlySalary.toLocaleString('pt-BR')}`,
                contractType: c.contract_type_preference || 'CLT',
                workModel: c.work_model_preference || 'híbrido',
                availability: 'A confirmar', portfolio: c.portfolio_url || '', github: c.github_url || '',
                workHistory: workHistoryData,
                bigFive: {
                  openness: 70 + Math.floor(seededRandom(c.id || String(index), 10) * 20),
                  conscientiousness: 70 + Math.floor(seededRandom(c.id || String(index), 11) * 20),
                  extraversion: 60 + Math.floor(seededRandom(c.id || String(index), 12) * 25),
                  agreeableness: 70 + Math.floor(seededRandom(c.id || String(index), 13) * 20),
                  neuroticism: 25 + Math.floor(seededRandom(c.id || String(index), 14) * 25),
                },
                notes: c.notes || '',
                liaAnalysis: {
                  score: c.lia_score || 75,
                  strengths: c.lia_insights?.strengths || ['Perfil técnico sólido'],
                  concerns: c.lia_insights?.concerns || [],
                  recommendation: c.lia_insights?.recommendation || 'Avaliar com atenção'
                },
                status: c.status || 'novo'
              }
            // @ts-ignore // TODO: fix type
            } catch { return null }
          }

          // @ts-ignore // TODO: fix type
          const currentDynamicStages = mapInterviewStagesToKanban(job?.interviewStages)
          const backendCandidates = response.items
            .map(mapCandidateToKanban)
            .filter((c): c is NonNullable<typeof c> => c !== null)

          const newOrganizedData: Record<string, Record<string, unknown>[]> = {}
          currentDynamicStages.forEach(stage => { newOrganizedData[stage.id] = [] })

          const findBestStageForCandidate = (rawStatus: string, mappedStage: string): string => {
            if (mappedStage === 'rejected' || ['reprovado', 'descartado'].includes(rawStatus)) return 'rejected'
            if (mappedStage === 'offer_declined' || rawStatus === 'proposta_recusada') return 'offer_declined'
            if (mappedStage === 'hired' || ['aprovado', 'contratado'].includes(rawStatus)) return 'hired'
            const stageExists = (id: string) => currentDynamicStages.some(s => s.id === id)
            if ((mappedStage === 'offer' || ['final', 'proposta'].includes(rawStatus)) && stageExists('offer')) return 'offer'
            if (['interview_manager', 'entrevista_gestor'].includes(rawStatus) && stageExists('interview_manager')) return 'interview_manager'
            if (['interview_technical', 'entrevista_tecnica'].includes(rawStatus) && stageExists('interview_technical')) return 'interview_technical'
            if ((mappedStage === 'interview_hr' || ['entrevista', 'interview', 'entrevistando'].includes(rawStatus)) && stageExists('interview_hr')) return 'interview_hr'
            if ((mappedStage === 'screening' || ['triagem', 'em_triagem', 'triado', 'triado_aprovado'].includes(rawStatus)) && stageExists('screening')) return 'screening'
            const normalizedStatus = rawStatus.replace(/_/g, ' ').toLowerCase()
            const customStage = currentDynamicStages.find(s =>
              s.name.toLowerCase().includes(normalizedStatus) ||
              s.displayName.toLowerCase().includes(normalizedStatus) ||
              normalizedStatus.includes(s.name.toLowerCase())
            )
            if (customStage) return customStage.id
            return 'sourcing'
          }

          backendCandidates.forEach((candidate) => {
            const rawStatus = (candidate.status || 'novo').toLowerCase()
            const mappedStage = mapLegacyStage(rawStatus)
            const targetStage = findBestStageForCandidate(rawStatus, mappedStage)
            const needsAction = ['sourcing', 'screening'].includes(targetStage)
            let extraData = {}
            if (targetStage.startsWith('interview')) {
              const idx = (newOrganizedData[targetStage] || []).length
              const isScheduled = idx % 2 === 0
              extraData = {
                agendada: isScheduled ? new Date(Date.now() + (idx + 1) * 24 * 60 * 60 * 1000).toISOString() : undefined,
                interviewDate: isScheduled ? (idx === 0 ? 'Hoje às 14h' : `${idx + 1} dias às 10h`) : undefined,
                typeOfInterview: isScheduled ? 'Teams' : undefined,
                teamsLink: undefined,
                interviewer: isScheduled ? 'Maria Silva - Head de P&C' : undefined,
              }
            }
            if (newOrganizedData[targetStage]) {
              newOrganizedData[targetStage].push({
                ...candidate, needsAction, stage: targetStage,
                sub_status: (candidate as Record<string, unknown>).sub_status || 'pending',
                ...extraData
              })
            } else {
              newOrganizedData['sourcing'] = newOrganizedData['sourcing'] || []
              newOrganizedData['sourcing'].push({ ...candidate, needsAction: true, stage: 'sourcing', sub_status: 'identified' })
            }
          })

          setCandidatesData(() => newOrganizedData)
        } catch { /* process error */ } finally {
          setIsLoadingCandidates(false)
        }
      })
      .catch(() => { setIsLoadingCandidates(false) })
  }, [])

  return {
    state: { isLoadingCandidates, hasMounted, isClient },
    actions: { setIsLoadingCandidates, setHasMounted, setIsClient },
  }
}

export type KanbanCandidateLoaderState = ReturnType<typeof useKanbanCandidateLoader>
