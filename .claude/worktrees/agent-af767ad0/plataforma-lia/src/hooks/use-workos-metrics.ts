import useSWR from 'swr'

interface WorkOSMetrics {
  source: 'local' | 'workos_api'
  sso_users_count: number
  scim_users_count: number
  groups_count: number
  directories_count: number
  connections_count: number
}

const fetcher = (url: string) => fetch(url).then(res => res.json())

export function useWorkOSMetrics(companyId: string) {
  const { data, error, isLoading, mutate } = useSWR<WorkOSMetrics>(
    `/api/backend-proxy/workos/admin/realtime-metrics?company_id=${companyId}`,
    fetcher,
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
    }
  )

  return {
    metrics: data,
    isLoading,
    isError: error,
    isFromWorkOS: data?.source === 'workos_api',
    refresh: mutate,
  }
}
