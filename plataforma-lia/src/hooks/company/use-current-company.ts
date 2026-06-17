import useSWR from 'swr'
import { useAuthStore } from '@/stores/auth-store'

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
  tenantId: string | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const jsonFetcher = (url: string) =>
  fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json()
  })

export function useCurrentCompany(): UseCurrentCompanyReturn {
  const user = useAuthStore(s => s.user)
  const { data, error, isLoading, mutate } = useSWR<Company>(
    '/api/backend-proxy/company/profile',
    jsonFetcher,
    { revalidateOnFocus: false }
  )

  return {
    company: data ?? null,
    companyId: data?.id ?? null,
    tenantId: user?.company_id ?? null,  // R-020 P0-C: direct access after SSOUser fix
    loading: isLoading,
    error: error?.message ?? null,
    refetch: async () => { await mutate() },
  }
}
