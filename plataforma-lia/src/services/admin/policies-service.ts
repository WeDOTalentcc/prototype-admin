import { apiClient, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

export type PolicyCategory = 'data_retention' | 'ai_usage' | 'security' | 'compliance'
export type PolicyValueType = 'number' | 'boolean' | 'string' | 'select'

export interface Policy {
  id: string
  name: string
  description: string
  category: PolicyCategory
  valueType: PolicyValueType
  value: string | number | boolean
  options?: string[]
  unit?: string
  minValue?: number
  maxValue?: number
  updatedAt: string
  updatedBy: string
  isActive: boolean
}

export interface PolicyHistoryEntry {
  id: string
  policyId: string
  policyName: string
  previousValue: string
  newValue: string
  changedBy: string
  changedAt: string
  changeType: 'update' | 'enable' | 'disable'
  reason?: string
}

export interface PoliciesResponse {
  policies: Policy[]
  total: number
}

export interface PolicyHistoryResponse {
  history: PolicyHistoryEntry[]
  total: number
}

export interface CategoriesResponse {
  categories: PolicyCategory[]
}

export interface UpdatePolicyRequest {
  current_value: string | number | boolean
  change_reason?: string
}

function mapBackendPolicy(data: Record<string, unknown>): Policy {
  const d = safeData(data)
  return {
    id: d.str('id'),
    name: d.str('name'),
    description: d.str('description'),
    category: (d.str('category') || d.str('category')) as PolicyCategory,
    valueType: (d.str('value_type') || d.str('valueType')) as PolicyValueType,
    value: (d.raw('current_value') ?? d.raw('value') ?? '') as string | number | boolean,
    options: d.arr<string>('options').length > 0 ? d.arr<string>('options') : undefined,
    unit: d.str('unit') || undefined,
    minValue: d.num('min_value') || d.num('minValue') || undefined,
    maxValue: d.num('max_value') || d.num('maxValue') || undefined,
    updatedAt: d.str('updated_at') || d.str('updatedAt'),
    updatedBy: d.str('updated_by') || d.str('updatedBy'),
    isActive: data.is_active != null ? d.bool('is_active') : data.isActive != null ? d.bool('isActive') : true,
  }
}

function mapBackendHistoryEntry(data: Record<string, unknown>): PolicyHistoryEntry {
  const d = safeData(data)
  return {
    id: d.str('id'),
    policyId: d.str('policy_id') || d.str('policyId'),
    policyName: d.str('policy_name') || d.str('policyName'),
    previousValue: d.str('previous_value') || d.str('previousValue'),
    newValue: d.str('new_value') || d.str('newValue'),
    changedBy: d.str('changed_by') || d.str('changedBy'),
    changedAt: d.str('changed_at') || d.str('changedAt'),
    changeType: (d.str('change_type') || d.str('changeType')) as PolicyHistoryEntry['changeType'],
    reason: d.str('reason') || undefined,
  }
}

export { ApiClientError }

class PoliciesService {
  private baseEndpoint = '/global-policies'

  async getPolicies(category?: string): Promise<PoliciesResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (category && category !== 'all') {
        queryParams.set('category', category)
      }

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}?${queryParams}`
        : this.baseEndpoint

      const data = await apiClient.get<Record<string, unknown>>(endpoint)
      return {
        policies: (Array.isArray(data.policies) ? data.policies as Record<string, unknown>[] : []).map(mapBackendPolicy),
        total: Number(data.total ?? (Array.isArray(data.policies) ? (data.policies as unknown[]).length : 0)),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { policies: [], total: 0 }
    }
  }

  async getPolicyById(id: string): Promise<Policy | null> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/${id}`)
      return mapBackendPolicy(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async updatePolicy(
    id: string,
    value: string | number | boolean,
    reason?: string
  ): Promise<Policy> {
    const payload: UpdatePolicyRequest = { current_value: value }
    if (reason) {
      payload.change_reason = reason
    }

    const data = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}`, payload)
    return mapBackendPolicy(data)
  }

  async togglePolicy(id: string, isActive: boolean): Promise<Policy> {
    const data = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}`, {
      is_active: isActive,
    })
    return mapBackendPolicy(data)
  }

  async getPolicyHistory(id: string): Promise<PolicyHistoryResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/${id}/history`)
      return {
        history: (Array.isArray(data.history) ? data.history as Record<string, unknown>[] : []).map(mapBackendHistoryEntry),
        total: Number(data.total ?? (Array.isArray(data.history) ? (data.history as unknown[]).length : 0)),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { history: [], total: 0 }
    }
  }

  async getAllHistory(): Promise<PolicyHistoryResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/history`)
      return {
        history: (Array.isArray(data.history) ? data.history as Record<string, unknown>[] : []).map(mapBackendHistoryEntry),
        total: Number(data.total ?? (Array.isArray(data.history) ? (data.history as unknown[]).length : 0)),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { history: [], total: 0 }
    }
  }

  async getCategories(): Promise<CategoriesResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/categories`)
      return {
        categories: (Array.isArray(data.categories) ? data.categories : []) as PolicyCategory[],
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { categories: [] }
    }
  }

  async seedPolicies(): Promise<{ success: boolean; message: string; count?: number }> {
    try {
      const data = await apiClient.post<Record<string, unknown>>(`${this.baseEndpoint}/seed`, {})
      return {
        success: true,
        message: String(data.message ?? 'Policies seeded successfully'),
        count: data.count != null ? Number(data.count) : undefined,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error
      }
      throw error
    }
  }
}

export const policiesService = new PoliciesService()
