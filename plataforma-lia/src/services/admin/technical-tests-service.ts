import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export type TestCategory = 'coding' | 'logic' | 'domain' | 'personality'
export type TestStatus = 'active' | 'draft' | 'archived'
export type TestDifficulty = 'easy' | 'medium' | 'hard'

export interface TechnicalTest {
  id: string
  name: string
  description?: string
  category: TestCategory
  subcategory?: string
  duration: number
  difficulty: TestDifficulty
  status: TestStatus
  passingScore: number
  totalQuestions?: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface ClientTest {
  id: string
  clientId: string
  testId: string
  enabled: boolean
  customPassingScore?: number
  customDuration?: number
  testsTaken: number
  avgScore: number
  completionRate: number
  lastUsed?: string
  test: TechnicalTest
  createdAt: string
  updatedAt: string
}

export interface ClientTestStats {
  totalTests: number
  enabledTests: number
  activeTests: number
  draftTests: number
  totalTestsTaken: number
  avgCompletionRate: number
  testsTakenThisWeek: number
  byCategory: {
    coding: { total: number; enabled: number }
    logic: { total: number; enabled: number }
    domain: { total: number; enabled: number }
    personality: { total: number; enabled: number }
  }
}

export interface CreateTestData {
  name: string
  description?: string
  category: TestCategory
  subcategory?: string
  duration: number
  difficulty: TestDifficulty
  passingScore: number
  totalQuestions?: number
}

export interface UpdateTestData {
  name?: string
  description?: string
  category?: TestCategory
  subcategory?: string
  duration?: number
  difficulty?: TestDifficulty
  status?: TestStatus
  passingScore?: number
  totalQuestions?: number
  isActive?: boolean
}

export interface ClientTestConfig {
  enabled?: boolean
  customPassingScore?: number
  customDuration?: number
}

export interface TestListResponse {
  tests: TechnicalTest[]
  total: number
  limit: number
  offset: number
}

export interface ClientTestListResponse {
  tests: ClientTest[]
  total: number
  limit: number
  offset: number
}

export interface TestFilters {
  category?: string
  is_active?: boolean
  status?: TestStatus
  limit?: number
  offset?: number
}

export { ApiClientError }

function mapBackendTest(data: any): TechnicalTest {
  return {
    id: data.id,
    name: data.name,
    description: data.description,
    category: data.category,
    subcategory: data.subcategory,
    duration: data.duration,
    difficulty: data.difficulty,
    status: data.status,
    passingScore: data.passing_score ?? data.passingScore ?? 0,
    totalQuestions: data.total_questions ?? data.totalQuestions,
    isActive: data.is_active ?? data.isActive ?? true,
    createdAt: data.created_at ?? data.createdAt,
    updatedAt: data.updated_at ?? data.updatedAt,
  }
}

function mapBackendClientTest(data: any): ClientTest {
  return {
    id: data.id,
    clientId: data.client_id ?? data.clientId,
    testId: data.test_id ?? data.testId,
    enabled: data.enabled ?? false,
    customPassingScore: data.custom_passing_score ?? data.customPassingScore,
    customDuration: data.custom_duration ?? data.customDuration,
    testsTaken: data.tests_taken ?? data.testsTaken ?? 0,
    avgScore: data.avg_score ?? data.avgScore ?? 0,
    completionRate: data.completion_rate ?? data.completionRate ?? 0,
    lastUsed: data.last_used ?? data.lastUsed,
    test: data.test ? mapBackendTest(data.test) : data.test,
    createdAt: data.created_at ?? data.createdAt,
    updatedAt: data.updated_at ?? data.updatedAt,
  }
}

function mapBackendStats(data: any): ClientTestStats {
  return {
    totalTests: data.total_tests ?? data.totalTests ?? 0,
    enabledTests: data.enabled_tests ?? data.enabledTests ?? 0,
    activeTests: data.active_tests ?? data.activeTests ?? 0,
    draftTests: data.draft_tests ?? data.draftTests ?? 0,
    totalTestsTaken: data.total_tests_taken ?? data.totalTestsTaken ?? 0,
    avgCompletionRate: data.avg_completion_rate ?? data.avgCompletionRate ?? 0,
    testsTakenThisWeek: data.tests_taken_this_week ?? data.testsTakenThisWeek ?? 0,
    byCategory: {
      coding: {
        total: data.by_category?.coding?.total ?? data.byCategory?.coding?.total ?? 0,
        enabled: data.by_category?.coding?.enabled ?? data.byCategory?.coding?.enabled ?? 0,
      },
      logic: {
        total: data.by_category?.logic?.total ?? data.byCategory?.logic?.total ?? 0,
        enabled: data.by_category?.logic?.enabled ?? data.byCategory?.logic?.enabled ?? 0,
      },
      domain: {
        total: data.by_category?.domain?.total ?? data.byCategory?.domain?.total ?? 0,
        enabled: data.by_category?.domain?.enabled ?? data.byCategory?.domain?.enabled ?? 0,
      },
      personality: {
        total: data.by_category?.personality?.total ?? data.byCategory?.personality?.total ?? 0,
        enabled: data.by_category?.personality?.enabled ?? data.byCategory?.personality?.enabled ?? 0,
      },
    },
  }
}

class TechnicalTestsService {
  private baseEndpoint = '/technical-tests'
  private clientsEndpoint = '/clients'

  async getTests(filters: TestFilters = {}): Promise<TestListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (filters.category) queryParams.set('category', filters.category)
      if (filters.is_active !== undefined) queryParams.set('is_active', String(filters.is_active))
      if (filters.status) queryParams.set('status', filters.status)
      if (filters.limit) queryParams.set('limit', String(filters.limit))
      if (filters.offset) queryParams.set('offset', String(filters.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}?${queryParams}`
        : this.baseEndpoint

      const data = await apiClient.get<any>(endpoint)
      return {
        tests: (data.tests || data || []).map(mapBackendTest),
        total: data.total || (Array.isArray(data) ? data.length : 0),
        limit: data.limit || 100,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching technical tests:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { tests: [], total: 0, limit: 100, offset: 0 }
    }
  }

  async getTestById(id: string): Promise<TechnicalTest | null> {
    try {
      const data = await apiClient.get<any>(`${this.baseEndpoint}/${id}`)
      return mapBackendTest(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching test by id:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async createTest(data: CreateTestData): Promise<TechnicalTest | null> {
    try {
      const payload = {
        name: data.name,
        description: data.description,
        category: data.category,
        subcategory: data.subcategory,
        duration: data.duration,
        difficulty: data.difficulty,
        passing_score: data.passingScore,
        total_questions: data.totalQuestions,
      }
      const response = await apiClient.post<any>(this.baseEndpoint, payload)
      return mapBackendTest(response)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error creating test:', error.message)
        throw error
      }
      return null
    }
  }

  async updateTest(id: string, data: UpdateTestData): Promise<TechnicalTest | null> {
    try {
      const payload: Record<string, any> = {}
      if (data.name !== undefined) payload.name = data.name
      if (data.description !== undefined) payload.description = data.description
      if (data.category !== undefined) payload.category = data.category
      if (data.subcategory !== undefined) payload.subcategory = data.subcategory
      if (data.duration !== undefined) payload.duration = data.duration
      if (data.difficulty !== undefined) payload.difficulty = data.difficulty
      if (data.status !== undefined) payload.status = data.status
      if (data.passingScore !== undefined) payload.passing_score = data.passingScore
      if (data.totalQuestions !== undefined) payload.total_questions = data.totalQuestions
      if (data.isActive !== undefined) payload.is_active = data.isActive

      const response = await apiClient.put<any>(`${this.baseEndpoint}/${id}`, payload)
      return mapBackendTest(response)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error updating test:', error.message)
        throw error
      }
      return null
    }
  }

  async deleteTest(id: string): Promise<boolean> {
    try {
      await apiClient.delete(`${this.baseEndpoint}/${id}`)
      return true
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error deleting test:', error.message)
        throw error
      }
      return false
    }
  }

  async getClientTests(clientId: string): Promise<ClientTestListResponse> {
    try {
      const endpoint = `${this.clientsEndpoint}/${clientId}/tests`
      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        tests: (data.tests || data || []).map(mapBackendClientTest),
        total: data.total || (Array.isArray(data) ? data.length : 0),
        limit: data.limit || 100,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching client tests:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { tests: [], total: 0, limit: 100, offset: 0 }
    }
  }

  async configureClientTest(
    clientId: string,
    testId: string,
    config: ClientTestConfig
  ): Promise<ClientTest | null> {
    try {
      const payload: Record<string, any> = {}
      if (config.enabled !== undefined) payload.enabled = config.enabled
      if (config.customPassingScore !== undefined) payload.custom_passing_score = config.customPassingScore
      if (config.customDuration !== undefined) payload.custom_duration = config.customDuration

      const endpoint = `${this.clientsEndpoint}/${clientId}/tests/${testId}`
      const response = await apiClient.put<any>(endpoint, payload, { clientId })
      return mapBackendClientTest(response)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error configuring client test:', error.message)
        throw error
      }
      return null
    }
  }

  async getClientTestStats(clientId: string): Promise<ClientTestStats | null> {
    try {
      const endpoint = `${this.clientsEndpoint}/${clientId}/tests/stats`
      const data = await apiClient.get<any>(endpoint, { clientId })
      return mapBackendStats(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching client test stats:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async seedTests(): Promise<{ message: string; count: number } | null> {
    try {
      const response = await apiClient.post<any>(`${this.baseEndpoint}/seed`, {})
      return response
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error seeding tests:', error.message)
        throw error
      }
      return null
    }
  }
}

export const technicalTestsService = new TechnicalTestsService()
