"use client"

/**
 * useCvScreening — Hook para fluxo de upload de CV no chat da LIA.
 *
 * Uso:
 *   const { screenCv, isScreening, lastResult } = useCvScreening()
 *   await screenCv({ file, vacancyTitle, onProgress })
 *
 * Conecta o arquivo anexado no chat ao endpoint /api/backend-proxy/cv/upload-and-screen
 * e retorna o resultado estruturado (candidate_id, match_score, recommendation, message).
 */

import { useState, useCallback } from "react"

export interface CvScreeningResult {
  success: boolean
  candidate_id?: string
  candidate_name?: string
  job_id?: string
  job_title?: string
  match_score?: number
  recommendation?: string
  message: string
  parsed?: {
    name?: string
    email?: string
    phone?: string
    current_title?: string
    seniority_level?: string
    skills?: string[]
    confidence_score?: number
  }
  error?: string
}

interface ScreenCvOptions {
  file?: File
  cvText?: string
  vacancyTitle?: string
  vacancyId?: string
  runBars?: boolean
  onProgress?: (step: string) => void
}

interface UseCvScreeningResult {
  screenCv: (options: ScreenCvOptions) => Promise<CvScreeningResult>
  isScreening: boolean
  lastResult: CvScreeningResult | null
  reset: () => void
}

export function useCvScreening(): UseCvScreeningResult {
  const [isScreening, setIsScreening] = useState(false)
  const [lastResult, setLastResult] = useState<CvScreeningResult | null>(null)

  const screenCv = useCallback(async (options: ScreenCvOptions): Promise<CvScreeningResult> => {
    const { file, cvText, vacancyTitle, vacancyId, runBars = true, onProgress } = options

    if (!file && !cvText) {
      const err: CvScreeningResult = { success: false, message: "Nenhum arquivo ou texto de CV fornecido.", error: "missing_input" }
      setLastResult(err)
      return err
    }

    setIsScreening(true)
    onProgress?.("Enviando CV para análise...")

    try {
      let body: BodyInit

      if (file) {
        const formData = new FormData()
        formData.append("file", file)
        if (vacancyTitle) formData.append("vacancy_title", vacancyTitle)
        if (vacancyId) formData.append("vacancy_id", vacancyId)
        formData.append("run_bars", String(runBars))
        body = formData
      } else {
        body = JSON.stringify({ cv_text: cvText, vacancy_title: vacancyTitle, vacancy_id: vacancyId, run_bars: runBars })
      }

      onProgress?.("Processando com IA...")

      const response = await fetch("/api/backend-proxy/cv/upload-and-screen", {
        method: "POST",
        body,
        // Don't set Content-Type for FormData — browser sets it with boundary
        ...(!(file) ? { headers: { "Content-Type": "application/json" } } : {}),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const err: CvScreeningResult = {
          success: false,
          message: `Erro ao processar CV: ${errorData.error || response.statusText}`,
          error: "backend_error",
        }
        setLastResult(err)
        return err
      }

      const data = await response.json() as CvScreeningResult
      onProgress?.("Análise concluída!")
      setLastResult(data)
      return data

    } catch (error) {
      const err: CvScreeningResult = {
        success: false,
        message: "Erro de conexão ao processar CV. Tente novamente.",
        error: error instanceof Error ? error.message : "connection_error",
      }
      setLastResult(err)
      return err
    } finally {
      setIsScreening(false)
    }
  }, [])

  const reset = useCallback(() => {
    setLastResult(null)
  }, [])

  return { screenCv, isScreening, lastResult, reset }
}
