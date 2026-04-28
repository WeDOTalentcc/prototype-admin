"use client"

import { useEffect, useState } from "react"
import {
  RecruitmentStage,
  DEFAULT_STAGES,
} from "@/components/settings/RecruitmentJourneyConfig"
import {
  mapRawPipelineStage,
  mapRawScreeningQuestion,
  RawPipelineStage,
  RawScreeningQuestion,
  ScreeningQuestion,
} from "./recruitment-types"
import { apiFetch } from "@/lib/api/api-fetch"

export interface RecruitmentPersistenceState {
  loading: boolean
  questions: ScreeningQuestion[]
  setQuestions: React.Dispatch<React.SetStateAction<ScreeningQuestion[]>>
  originalQuestions: ScreeningQuestion[]
  setOriginalQuestions: React.Dispatch<React.SetStateAction<ScreeningQuestion[]>>
  recruitmentStages: RecruitmentStage[]
  setRecruitmentStages: React.Dispatch<React.SetStateAction<RecruitmentStage[]>>
  originalStages: RecruitmentStage[]
  setOriginalStages: React.Dispatch<React.SetStateAction<RecruitmentStage[]>>
}

export function useRecruitmentPersistence(): RecruitmentPersistenceState {
  const [loading, setLoading] = useState(true)
  const [questions, setQuestions] = useState<ScreeningQuestion[]>([])
  const [originalQuestions, setOriginalQuestions] = useState<ScreeningQuestion[]>([])
  const [recruitmentStages, setRecruitmentStages] =
    useState<RecruitmentStage[]>(DEFAULT_STAGES)
  const [originalStages, setOriginalStages] = useState<RecruitmentStage[]>([])

  useEffect(() => {
    let cancelled = false
    async function fetchData() {
      try {
        setLoading(true)
        const [questionsRes, pipelineRes] = await Promise.all([
          apiFetch('/api/backend-proxy/company/screening-questions'),
          apiFetch('/api/backend-proxy/company-pipeline'),
        ])

        if (!cancelled && questionsRes.ok) {
          const questionsResult = await questionsRes.json()
          const rawList: RawScreeningQuestion[] =
            questionsResult.items ?? (Array.isArray(questionsResult) ? questionsResult : [])
          const mapped = rawList.map(mapRawScreeningQuestion)
          setQuestions(mapped)
          setOriginalQuestions(mapped)
        }

        if (!cancelled && pipelineRes.ok) {
          const pipelineData = await pipelineRes.json()
          if (pipelineData.pipeline && Array.isArray(pipelineData.pipeline)) {
            const stages = (pipelineData.pipeline as RawPipelineStage[]).map(
              mapRawPipelineStage
            )
            setRecruitmentStages(stages)
            setOriginalStages(stages)
          }
        }
      } catch {
        // Silent — UI keeps default stages and empty questions
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => {
      cancelled = true
    }
  }, [])

  return {
    loading,
    questions,
    setQuestions,
    originalQuestions,
    setOriginalQuestions,
    recruitmentStages,
    setRecruitmentStages,
    originalStages,
    setOriginalStages,
  }
}
