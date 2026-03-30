import useSWR from 'swr'

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

const jsonFetcher = (url: string) =>
  fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json()
  })

export function useCurrentCompany(): UseCurrentCompanyReturn {
  const { data, error, isLoading, mutate } = useSWR<Company>(
    '/api/backend-proxy/company/profile',
    jsonFetcher,
    { revalidateOnFocus: false }
  )

  return {
    company: data ?? null,
    companyId: data?.id ?? null,
    loading: isLoading,
    error: error?.message ?? null,
    refetch: () => mutate(),
  }
}
