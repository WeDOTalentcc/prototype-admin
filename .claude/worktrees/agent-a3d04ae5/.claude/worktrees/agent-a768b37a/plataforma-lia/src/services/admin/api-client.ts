const BACKEND_URL = '/api/backend-proxy'

export interface ApiClientOptions {
  clientId?: string
  userId?: string
  userRole?: string
}

export interface ApiError {
  status: number
  message: string
  isAuthError: boolean
  isForbidden: boolean
  isNetworkError: boolean
}

export class ApiClientError extends Error {
  status: number
  isAuthError: boolean
  isForbidden: boolean
  isNetworkError: boolean

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'ApiClientError'
    this.status = error.status
    this.isAuthError = error.isAuthError
    this.isForbidden = error.isForbidden
    this.isNetworkError = error.isNetworkError
  }
}

function buildHeaders(options: ApiClientOptions = {}): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (options.clientId) {
    headers['X-Company-ID'] = options.clientId
  }

  if (options.userId) {
    headers['X-User-ID'] = options.userId
  }

  if (options.userRole) {
    headers['X-User-Role'] = options.userRole
  }

  return headers
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    throw new ApiClientError({
      status: 401,
      message: 'Unauthorized - Please log in again',
      isAuthError: true,
      isForbidden: false,
      isNetworkError: false,
    })
  }

  if (response.status === 403) {
    throw new ApiClientError({
      status: 403,
      message: 'Forbidden - You do not have permission to access this resource',
      isAuthError: false,
      isForbidden: true,
      isNetworkError: false,
    })
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiClientError({
      status: response.status,
      message: errorData.message || errorData.detail || `Request failed: ${response.statusText}`,
      isAuthError: false,
      isForbidden: false,
      isNetworkError: false,
    })
  }

  return response.json()
}

function handleNetworkError(error: unknown): never {
  if (error instanceof ApiClientError) {
    throw error
  }

  const message = error instanceof Error ? error.message : 'Network error occurred'
  throw new ApiClientError({
    status: 0,
    message,
    isAuthError: false,
    isForbidden: false,
    isNetworkError: true,
  })
}

export const apiClient = {
  baseUrl: BACKEND_URL,

  async get<T>(endpoint: string, options: ApiClientOptions = {}): Promise<T> {
    try {
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        method: 'GET',
        headers: buildHeaders(options),
      })
      return handleResponse<T>(response)
    } catch (error) {
      return handleNetworkError(error)
    }
  },

  async post<T>(endpoint: string, data: unknown, options: ApiClientOptions = {}): Promise<T> {
    try {
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        method: 'POST',
        headers: buildHeaders(options),
        body: JSON.stringify(data),
      })
      return handleResponse<T>(response)
    } catch (error) {
      return handleNetworkError(error)
    }
  },

  async patch<T>(endpoint: string, data: unknown, options: ApiClientOptions = {}): Promise<T> {
    try {
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        method: 'PATCH',
        headers: buildHeaders(options),
        body: JSON.stringify(data),
      })
      return handleResponse<T>(response)
    } catch (error) {
      return handleNetworkError(error)
    }
  },

  async put<T>(endpoint: string, data: unknown, options: ApiClientOptions = {}): Promise<T> {
    try {
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        method: 'PUT',
        headers: buildHeaders(options),
        body: JSON.stringify(data),
      })
      return handleResponse<T>(response)
    } catch (error) {
      return handleNetworkError(error)
    }
  },

  async delete<T = void>(endpoint: string, options: ApiClientOptions = {}): Promise<T> {
    try {
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        method: 'DELETE',
        headers: buildHeaders(options),
      })
      
      if (response.status === 204) {
        return undefined as T
      }
      
      return handleResponse<T>(response)
    } catch (error) {
      return handleNetworkError(error)
    }
  },
}

export default apiClient
