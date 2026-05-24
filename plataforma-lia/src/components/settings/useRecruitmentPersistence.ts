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
  /** P1-W1-04: erro de fetch exposto — não mais silenciado */
  fetchError: string | null
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
  // P1-W1-04: estado de erro exposto para que callers possam mostrar feedback real
  const [fetchError, setFetchError] = useState<string | null>(null)
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

        if (!cancelled) {
          if (questionsRes.ok) {
            const questionsResult = await questionsRes.json()
            const rawList: RawScreeningQuestion[] =
              questionsResult.items ?? (Array.isArray(questionsResult) ? questionsResult : [])
            const mapped = rawList.map(mapRawScreeningQuestion)
            setQuestions(mapped)
            setOriginalQuestions(mapped)
          } else if (questionsRes.status !== 404) {
            // P1-W1-03/07: 404 = empresa ainda não configurou perguntas (legítimo, lista vazia OK)
            // Outros erros = falha real de rede/backend — surfaçar para o caller
            setFetchError("Falha ao carregar perguntas de screening")
          }
        }

        if (!cancelled) {
          if (pipelineRes.ok) {
            const pipelineData = await pipelineRes.json()
            if (pipelineData.pipeline && Array.isArray(pipelineData.pipeline)) {
              const stages = (pipelineData.pipeline as RawPipelineStage[]).map(
                mapRawPipelineStage
              )
              setRecruitmentStages(stages)
              setOriginalStages(stages)
            }
          } else if (pipelineRes.status !== 404) {
            // P1-W1-04: 404 = pipeline ainda não configurado (DEFAULT_STAGES é legítimo)
            // Outros erros = falha real — surfaçar, não manter DEFAULT_STAGES como se fosse dado real
            setFetchError("Falha ao carregar configurações de pipeline")
          }
          // 404 no pipeline = empresa nova sem pipeline configurado → DEFAULT_STAGES permanece,
          // mas isso é intencionalmente esperado, não um erro silencioso
        }
      } catch (err) {
        // P1-W1-04: falhar explicitamente — nunca esconder erro de rede/timeout
        if (!cancelled) {
          console.error("[useRecruitmentPersistence] fetchData failed:", err)
          setFetchError("Erro ao conectar com o backend. Tente recarregar a página.")
        }
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
    fetchError,
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
