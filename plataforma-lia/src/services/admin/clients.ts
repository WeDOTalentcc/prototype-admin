import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export interface Client {
  id: string
  name: string
  tradeName?: string
  cnpj?: string
  status: 'active' | 'inactive' | 'trial' | 'suspended' | string
  planId?: string
  logoUrl?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  state?: string
  country?: string
  createdAt?: string
  updatedAt?: string
  usersCount?: number
  activeJobsCount?: number
}

export interface ClientUser {
  id: string
  name: string
  email: string
  role: string
  isActive: boolean
  lastLogin?: string
  createdAt?: string
}

export interface ClientsListParams {
  page?: number
  limit?: number
  search?: string
  status?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface ClientsListResponse {
  items: Client[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface CreateClientData {
  name: string
  tradeName?: string
  cnpj?: string
  email?: string
  phone?: string
  planId?: string
  status?: string
}

export interface UpdateClientData {
  name?: string
  tradeName?: string
  cnpj?: string
  email?: string
  phone?: string
  planId?: string
  status?: string
  logoUrl?: string
}

export { ApiClientError }

function mapBackendClientToClient(bc: Record<string, unknown>): Client {
  return {
    id: bc.id,
    name: bc.name,
    tradeName: bc.trade_name,
    cnpj: bc.cnpj,
    status: bc.status,
    planId: bc.plan_id,
    logoUrl: bc.logo_url,
    email: bc.primary_email,
    phone: bc.primary_phone,
    address: bc.address ? JSON.stringify(bc.address) : undefined,
    createdAt: bc.created_at,
    updatedAt: bc.updated_at,
    usersCount: bc.users_count || 0,
    activeJobsCount: bc.active_jobs_count || 0,
  }
}

class ClientsService {
  async getClients(
    params: ClientsListParams = {},
    options?: ApiClientOptions
  ): Promise<ClientsListResponse> {
    try {
      const queryParams = new URLSearchParams()
      
      const page = params.page || 1
      const limit = params.limit || 20
      const offset = (page - 1) * limit
      
      queryParams.set('limit', limit.toString())
      if (offset > 0) queryParams.set('offset', offset.toString())
      if (params.search) queryParams.set('search', params.search)
      if (params.status) queryParams.set('status', params.status)
      if (params.sortBy) queryParams.set('sort_by', params.sortBy)
      if (params.sortOrder) queryParams.set('sort_order', params.sortOrder)

      const endpoint = queryParams.toString() 
        ? `/clients?${queryParams}`
        : `/clients`

      const response = await apiClient.get<any>(endpoint, options)
      
      if (Array.isArray(response)) {
        return {
          items: response.map(mapBackendClientToClient),
          total: response.length,
          page: page,
          limit: limit,
          totalPages: 1
        }
      }
      
      const data = response.data || response
      const rawClients = data.clients || data.items || []
      const clients = rawClients.map(mapBackendClientToClient)
      const total = data.total || data.count || clients.length
      const responseLimit = data.limit || limit
      const calculatedTotalPages = Math.ceil(total / responseLimit) || 1
      
      return {
        items: clients,
        total: total,
        page: page,
        limit: responseLimit,
        totalPages: data.total_pages || data.totalPages || calculatedTotalPages
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return {
        items: [],
        total: 0,
        page: params.page || 1,
        limit: params.limit || 20,
        totalPages: 0
      }
    }
  }

  async getClient(id: string, options?: Omit<ApiClientOptions, 'clientId'>): Promise<Client | null> {
    try {
      return await apiClient.get<Client>(
        `/clients/${id}`,
        { clientId: id, ...options }
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return null
    }
  }

  async createClient(data: CreateClientData, options?: ApiClientOptions): Promise<Client> {
    return apiClient.post<Client>(`/clients`, data, options)
  }

  async updateClient(
    id: string, 
    data: UpdateClientData, 
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<Client> {
    return apiClient.patch<Client>(
      `/clients/${id}`, 
      data, 
      { clientId: id, ...options }
    )
  }

  async deleteClient(id: string, options?: Omit<ApiClientOptions, 'clientId'>): Promise<void> {
    return apiClient.delete(
      `/clients/${id}`, 
      { clientId: id, ...options }
    )
  }

  async getClientUsers(
    clientId: string, 
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientUser[]> {
    try {
      const data = await apiClient.get<ClientUser[] | { items: ClientUser[] }>(
        `/clients/${clientId}/users`,
        { clientId, ...options }
      )
      return Array.isArray(data) ? data : data.items || []
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return []
    }
  }

  async addClientUser(
    clientId: string, 
    userData: Partial<ClientUser>,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientUser> {
    return apiClient.post<ClientUser>(
      `/clients/${clientId}/users`, 
      userData, 
      { clientId, ...options }
    )
  }

  async updateClientUser(
    clientId: string, 
    userId: string, 
    userData: Partial<ClientUser>,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientUser> {
    return apiClient.patch<ClientUser>(
      `/clients/${clientId}/users/${userId}`, 
      userData, 
      { clientId, ...options }
    )
  }

  async deleteClientUser(
    clientId: string, 
    userId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<void> {
    return apiClient.delete(
      `/clients/${clientId}/users/${userId}`, 
      { clientId, ...options }
    )
  }
}

export const clientsService = new ClientsService()
