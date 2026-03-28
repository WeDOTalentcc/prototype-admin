import { apiClient, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

export interface DashboardKPIs {
  totalClients: number
  activeClients: number
  trialClients: number
  churnedClients: number
  newClientsPeriod: number
  mrr: number
  arr: number
  churnRate: number
}

export interface ClientSummary {
  id: string
  name: string
  plan: string
  createdAt?: string
  trialEndDate?: string
  daysRemaining?: number
  churnedAt?: string
  reason?: string
}

export interface DashboardSummary {
  kpis: DashboardKPIs
  newClients: ClientSummary[]
  trialClients: ClientSummary[]
  churnedClients: ClientSummary[]
}

const MOCK_DASHBOARD_SUMMARY: DashboardSummary = {
  kpis: {
    totalClients: 16,
    activeClients: 12,
    trialClients: 3,
    churnedClients: 1,
    newClientsPeriod: 4,
    mrr: 24500,
    arr: 294000,
    churnRate: 2.1
  },
  newClients: [
    { id: '1', name: 'TechCorp Brasil', plan: 'Professional', createdAt: '2024-12-15T10:30:00Z' },
    { id: '2', name: 'Inovação RH Ltda', plan: 'Enterprise', createdAt: '2024-12-12T14:20:00Z' },
    { id: '3', name: 'Startup Talentos', plan: 'Starter', createdAt: '2024-12-10T09:15:00Z' },
    { id: '4', name: 'Global Hiring Co', plan: 'Professional', createdAt: '2024-12-08T16:45:00Z' }
  ],
  trialClients: [
    { id: '5', name: 'Empresa Teste Alpha', plan: 'Professional', trialEndDate: '2024-12-25T23:59:59Z', daysRemaining: 7 },
    { id: '6', name: 'Beta Recrutamento', plan: 'Enterprise', trialEndDate: '2024-12-28T23:59:59Z', daysRemaining: 10 },
    { id: '7', name: 'Gamma HR Solutions', plan: 'Starter', trialEndDate: '2024-12-22T23:59:59Z', daysRemaining: 4 }
  ],
  churnedClients: [
    { id: '8', name: 'ExCliente Corp', plan: 'Starter', churnedAt: '2024-12-05T11:00:00Z', reason: 'Custo elevado' }
  ]
}

export async function getDashboardSummary(startDate?: Date, endDate?: Date): Promise<DashboardSummary> {
  const params = new URLSearchParams()
  if (startDate) params.set('start_date', startDate.toISOString())
  if (endDate) params.set('end_date', endDate.toISOString())

  try {
    const queryString = params.toString()
    const endpoint = queryString ? `/clients/dashboard-summary?${queryString}` : '/clients/dashboard-summary'
    
    const response = await apiClient.get<{ success: boolean; data: Record<string, unknown> }>(endpoint, {
      clientId: 'admin',
      userRole: 'admin'
    })

    if (!response || !response.data) {
      return MOCK_DASHBOARD_SUMMARY
    }

    const data = response.data
    const dd = safeData(data)
    const kpisRec = safeData(dd.rec('kpis'))

    return {
      kpis: {
        totalClients: kpisRec.num('total_clients'),
        activeClients: kpisRec.num('active_clients'),
        trialClients: kpisRec.num('trial_clients'),
        churnedClients: kpisRec.num('churned_clients'),
        newClientsPeriod: kpisRec.num('new_clients_period'),
        mrr: kpisRec.num('mrr'),
        arr: kpisRec.num('arr'),
        churnRate: kpisRec.num('churn_rate')
      },
      newClients: dd.arr<Record<string, unknown>>('new_clients').map((c: Record<string, unknown>) => {
        const cd = safeData(c)
        return {
          id: cd.str('id'),
          name: cd.str('name'),
          plan: cd.str('plan'),
          createdAt: cd.str('created_at')
        }
      }),
      trialClients: dd.arr<Record<string, unknown>>('trial_clients').map((c: Record<string, unknown>) => {
        const cd = safeData(c)
        return {
          id: cd.str('id'),
          name: cd.str('name'),
          plan: cd.str('plan'),
          trialEndDate: cd.str('trial_end_date'),
          daysRemaining: cd.num('days_remaining')
        }
      }),
      churnedClients: dd.arr<Record<string, unknown>>('churned_clients').map((c: Record<string, unknown>) => {
        const cd = safeData(c)
        return {
          id: cd.str('id'),
          name: cd.str('name'),
          plan: cd.str('plan'),
          churnedAt: cd.str('churned_at'),
          reason: cd.str('reason')
        }
      })
    }
  } catch (error) {
    if (error instanceof ApiClientError) {
      if (error.isAuthError || error.isForbidden) {
        throw error
      }
    }
    return MOCK_DASHBOARD_SUMMARY
  }
}

export { ApiClientError }
