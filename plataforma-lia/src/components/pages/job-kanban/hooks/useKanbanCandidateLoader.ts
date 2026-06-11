"use client"

import { formatBRL } from "@/lib/pricing"

import { useState, useEffect } from "react"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import {
  mapInterviewStagesToKanban,
  createInitialCandidatesData,
  type DynamicStage,
} from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { mapLegacyStage } from "@/lib/recruitment-stages"

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
    const newStages = mapInterviewStagesToKanban((job as Record<string, unknown>)?.interviewStages as unknown as import("../utils/kanbanStageUtils").InterviewStageFromJob[])
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
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: only re-run when interviewStages changes
  }, [job?.interviewStages])

  // P0-2 (fix 2026-06-08): job.id é índice legado inteiro; usar backendId (UUID)
  // quando disponível. Computado fora do useEffect para ser dep estável (tamanho fixo).
  const vacancyUuid = ((job as Record<string, unknown>)?.backendId || (job as Record<string, unknown>)?.id) as string | undefined

  // Carregar candidatos reais do backend
  useEffect(() => {
    setIsLoadingCandidates(true)
    // P0-1 (audit 2026-06-05): escopa o board aos candidatos DA VAGA
    // (vacancy_candidates) em vez da lista global de 200.
    liaApi.listCandidates(undefined, undefined, 0, 200, vacancyUuid)
      .then(response => {
        try {
          if (!response.items || response.items.length === 0) { setIsLoadingCandidates(false); return }

          const mapCandidateToKanban = (c: CandidateLocal, _index: number) => {
            try {
              const experience = c.years_of_experience ?? null
              const location = c.location_city && c.location_state
                ? `${c.location_city}, ${c.location_state}`
                : c.location_city || null

              const rawStatus = (c.status || 'novo').toLowerCase()
              let mappedStage = 'funil'
              if (['reprovado', 'rejected', 'descartado', 'reprovados'].includes(rawStatus)) mappedStage = 'reprovados'
              else if (['aprovado', 'hired', 'contratado', 'aprovados'].includes(rawStatus)) mappedStage = 'aprovados'
              else if (['final', 'proposta', 'offer'].includes(rawStatus)) mappedStage = 'final'
              else if (['entrevista', 'interview', 'entrevistando'].includes(rawStatus)) mappedStage = 'entrevista'
              else if (['triagem', 'screening', 'em_triagem'].includes(rawStatus)) mappedStage = 'triagem'

              const jobTitle = (job as Record<string, unknown>)?.title as string || null
              const jobIdVal = (job as Record<string, unknown>)?.id as string || (job as Record<string, unknown>)?.backendId as string || null
              const recruiterName = (job as Record<string, unknown>)?.recruiter_name as string || (job as Record<string, unknown>)?.recruiterName as string || null
              const managerName = (job as Record<string, unknown>)?.hiring_manager as string || (job as Record<string, unknown>)?.hiringManager as string || null

              return {
                id: c.id, name: c.name || 'Sem nome', role: c.current_title || null,
                currentCompany: c.current_company || null, location,
                jobTitle: jobTitle,
                jobId: jobIdVal,
                recruiter: recruiterName,
                manager: managerName,
                score: c.lia_score ?? null,
                fitScore: c.skills_match_percentage ?? null,
                warnings: 0, avatar: c.avatar_url || '', source: c.source || 'website',
                appliedDate: c.created_at ? new Date(c.created_at).toLocaleDateString('pt-BR') : null,
                email: c.email || '', phone: c.phone || '', linkedin: c.linkedin_url || '',
                experience: experience ? `${experience} anos` : null, stage: mappedStage, etapa: mappedStage,
                seniority_level: c.seniority_level || null,
                years_of_experience: c.years_of_experience ?? null,
                education: null, skills: c.technical_skills || [],
                languages: Array.isArray(c.languages)
                  ? c.languages.map((l: Record<string, unknown>) => typeof l === 'string' ? l : l.language)
                  : Object.keys(c.languages || {}),
                expectedSalary: c.desired_salary_max
                  ? `${formatBRL(c.desired_salary_max)}`
                  : null,
                currentSalary: c.current_salary ? `${formatBRL(c.current_salary)}` : null,
                contractType: c.contract_type_preference || null,
                workModel: c.work_model_preference || null,
                availability: null, portfolio: c.portfolio_url || '', github: c.github_url || '',
                workHistory: null,
                bigFive: null,
                notes: c.notes || '',
                liaAnalysis: c.lia_score ? {
                  score: c.lia_score,
                  strengths: c.lia_insights?.strengths || [],
                  concerns: c.lia_insights?.concerns || [],
                  recommendation: c.lia_insights?.recommendation || null
                } : null,
                status: c.status || 'novo'
              }
            } catch { return null }
          }

          const currentDynamicStages = mapInterviewStagesToKanban((job as Record<string, unknown>)?.interviewStages as unknown as import("../utils/kanbanStageUtils").InterviewStageFromJob[])
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
  // eslint-disable-next-line react-hooks/exhaustive-deps -- re-roda quando a vaga muda (vacancyUuid = backendId ?? id)
  }, [vacancyUuid])

  return {
    state: { isLoadingCandidates, hasMounted, isClient },
    actions: { setIsLoadingCandidates, setHasMounted, setIsClient },
  }
}

export type KanbanCandidateLoaderState = ReturnType<typeof useKanbanCandidateLoader>
