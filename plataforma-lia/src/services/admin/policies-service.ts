import { apiClient, ApiClientError } from './api-client'

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
  return {
    id: data.id,
    name: data.name,
    description: data.description,
    category: data.category,
    valueType: data.value_type || data.valueType,
    value: data.current_value ?? data.value,
    options: data.options,
    unit: data.unit,
    minValue: data.min_value ?? data.minValue,
    maxValue: data.max_value ?? data.maxValue,
    updatedAt: data.updated_at || data.updatedAt,
    updatedBy: data.updated_by || data.updatedBy,
    isActive: data.is_active ?? data.isActive ?? true,
  }
}

function mapBackendHistoryEntry(data: Record<string, unknown>): PolicyHistoryEntry {
  return {
    id: data.id,
    policyId: data.policy_id || data.policyId,
    policyName: data.policy_name || data.policyName,
    previousValue: data.previous_value || data.previousValue,
    newValue: data.new_value || data.newValue,
    changedBy: data.changed_by || data.changedBy,
    changedAt: data.changed_at || data.changedAt,
    changeType: data.change_type || data.changeType,
    reason: data.reason,
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

      const data = await apiClient.get<any>(endpoint)
      return {
        policies: (data.policies || data || []).map(mapBackendPolicy),
        total: data.total || (data.policies || data || []).length,
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
      const data = await apiClient.get<any>(`${this.baseEndpoint}/${id}`)
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

    const data = await apiClient.put<any>(`${this.baseEndpoint}/${id}`, payload)
    return mapBackendPolicy(data)
  }

  async togglePolicy(id: string, isActive: boolean): Promise<Policy> {
    const data = await apiClient.put<any>(`${this.baseEndpoint}/${id}`, {
      is_active: isActive,
    })
    return mapBackendPolicy(data)
  }

  async getPolicyHistory(id: string): Promise<PolicyHistoryResponse> {
    try {
      const data = await apiClient.get<any>(`${this.baseEndpoint}/${id}/history`)
      return {
        history: (data.history || data || []).map(mapBackendHistoryEntry),
        total: data.total || (data.history || data || []).length,
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
      const data = await apiClient.get<any>(`${this.baseEndpoint}/history`)
      return {
        history: (data.history || data || []).map(mapBackendHistoryEntry),
        total: data.total || (data.history || data || []).length,
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
      const data = await apiClient.get<any>(`${this.baseEndpoint}/categories`)
      return {
        categories: data.categories || data || [],
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
      const data = await apiClient.post<any>(`${this.baseEndpoint}/seed`, {})
      return {
        success: true,
        message: data.message || 'Policies seeded successfully',
        count: data.count,
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
