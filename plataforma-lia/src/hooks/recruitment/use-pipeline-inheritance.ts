import { useState, useCallback } from 'react'

interface PipelineInheritanceState {
  isCustomized: boolean
  isLoading: boolean
  error: string | null
}

export function usePipelineInheritance(jobId?: string) {
  const [state, setState] = useState<PipelineInheritanceState>({
    isCustomized: false,
    isLoading: false,
    error: null,
  })

  const checkStatus = useCallback(async () => {
    if (!jobId) return
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    try {
      const response = await fetch(`/api/backend-proxy/recruitment-stages/pipeline/job/${jobId}/inheritance-status`)
      if (response.ok) {
        const data = await response.json()
        setState({ isCustomized: data.is_customized, isLoading: false, error: null })
      }
    } catch {
      setState(prev => ({ ...prev, isLoading: false }))
    }
  }, [jobId])

  const resetToCompanyDefault = useCallback(async (): Promise<boolean> => {
    if (!jobId) return false
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    try {
      const response = await fetch(`/api/backend-proxy/recruitment-stages/pipeline/job/${jobId}/copy-from-company`, {
        method: 'POST',
      })
      if (response.ok) {
        setState({ isCustomized: false, isLoading: false, error: null })
        return true
      }
      return false
    } catch {
      setState(prev => ({ ...prev, isLoading: false, error: 'Erro ao resetar pipeline' }))
      return false
    }
  }, [jobId])

  const markAsCustomized = useCallback(async (): Promise<boolean> => {
    if (!jobId) return false
    try {
      const response = await fetch(`/api/backend-proxy/recruitment-stages/pipeline/job/${jobId}/mark-customized`, {
        method: 'POST',
      })
      if (response.ok) {
        setState(prev => ({ ...prev, isCustomized: true }))
        return true
      }
      return false
    } catch {
      return false
    }
  }, [jobId])

  return {
    ...state,
    checkStatus,
    resetToCompanyDefault,
    markAsCustomized,
  }
}
