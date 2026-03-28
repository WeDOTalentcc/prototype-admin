import { useState, useCallback } from 'react'

interface OverrideApproveState {
  isLoading: boolean
  error: string | null
}

interface OverrideApproveResult {
  success: boolean
  message: string
  candidateId: string
  candidateName: string
  newStage: string
  newStatus: string
  override: boolean
}

interface UseOverrideApproveReturn {
  isLoading: boolean
  error: string | null
  approveOverride: (candidateId: string, vacancyId: string) => Promise<OverrideApproveResult | null>
  clearError: () => void
}

export function useOverrideApprove(): UseOverrideApproveReturn {
  const [state, setState] = useState<OverrideApproveState>({
    isLoading: false,
    error: null,
  })

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  const approveOverride = useCallback(async (
    candidateId: string,
    vacancyId: string,
  ): Promise<OverrideApproveResult | null> => {
    setState({ isLoading: true, error: null })

    try {
      const response = await fetch(
        `/api/backend-proxy/candidates/${candidateId}/screening-decision`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            decision: 'approved',
            job_id: vacancyId,
            reviewer_id: 'recruiter',
          }),
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData?.details?.detail || errorData?.error || 'Erro ao aprovar candidato'
        setState({ isLoading: false, error: errorMsg })
        return null
      }

      const data = await response.json()
      setState({ isLoading: false, error: null })
      return data as OverrideApproveResult
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Erro de conexão'
      setState({ isLoading: false, error: errorMsg })
      return null
    }
  }, [])

  return {
    isLoading: state.isLoading,
    error: state.error,
    approveOverride,
    clearError,
  }
}
