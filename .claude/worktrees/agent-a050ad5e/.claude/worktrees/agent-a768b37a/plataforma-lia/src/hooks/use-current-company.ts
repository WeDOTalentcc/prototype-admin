import { useState, useEffect, useCallback } from 'react'

interface Company {
  id: string
  name: string
  trade_name?: string
  logo_url?: string
  plan_id?: string
  status?: string
}

interface UseCurrentCompanyReturn {
  company: Company | null
  companyId: string | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useCurrentCompany(): UseCurrentCompanyReturn {
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCompany = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/backend-proxy/company/profile')
      if (response.ok) {
        const data = await response.json()
        setCompany(data)
      } else {
        setError('Não foi possível carregar dados da empresa')
      }
    } catch (err) {
      setError('Erro ao carregar empresa')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCompany()
  }, [fetchCompany])

  return {
    company,
    companyId: company?.id || null,
    loading,
    error,
    refetch: fetchCompany
  }
}
