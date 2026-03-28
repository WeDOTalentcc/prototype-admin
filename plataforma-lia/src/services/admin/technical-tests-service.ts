import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

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

function mapBackendTest(data: Record<string, unknown>): TechnicalTest {
  const d = safeData(data)
  return {
    id: d.str('id'),
    name: d.str('name'),
    description: d.str('description') || undefined,
    category: (d.str('category') || 'coding') as TestCategory,
    subcategory: d.str('subcategory') || undefined,
    duration: d.num('duration'),
    difficulty: (d.str('difficulty') || 'medium') as TestDifficulty,
    status: (d.str('status') || 'active') as TestStatus,
    passingScore: d.num('passing_score') || d.num('passingScore'),
    totalQuestions: d.num('total_questions') || d.num('totalQuestions') || undefined,
    isActive: d.raw('is_active') != null ? d.bool('is_active') : d.raw('isActive') != null ? d.bool('isActive') : true,
    createdAt: d.str('created_at') || d.str('createdAt'),
    updatedAt: d.str('updated_at') || d.str('updatedAt'),
  }
}

function mapBackendClientTest(data: Record<string, unknown>): ClientTest {
  const d = safeData(data)
  return {
    id: d.str('id'),
    clientId: d.str('client_id') || d.str('clientId'),
    testId: d.str('test_id') || d.str('testId'),
    enabled: d.raw('enabled') != null ? d.bool('enabled') : false,
    customPassingScore: d.num('custom_passing_score') || d.num('customPassingScore') || undefined,
    customDuration: d.num('custom_duration') || d.num('customDuration') || undefined,
    testsTaken: d.num('tests_taken') || d.num('testsTaken'),
    avgScore: d.num('avg_score') || d.num('avgScore'),
    completionRate: d.num('completion_rate') || d.num('completionRate'),
    lastUsed: d.str('last_used') || d.str('lastUsed') || undefined,
    test: mapBackendTest(d.raw('test') ? d.rec('test') : {}),
    createdAt: d.str('created_at') || d.str('createdAt'),
    updatedAt: d.str('updated_at') || d.str('updatedAt'),
  }
}

function mapBackendStats(data: Record<string, unknown>): ClientTestStats {
  const d = safeData(data)
  const bc = (d.raw('by_category') || d.raw('byCategory') || {}) as Record<string, Record<string, number>>
  return {
    totalTests: d.num('total_tests') || d.num('totalTests'),
    enabledTests: d.num('enabled_tests') || d.num('enabledTests'),
    activeTests: d.num('active_tests') || d.num('activeTests'),
    draftTests: d.num('draft_tests') || d.num('draftTests'),
    totalTestsTaken: d.num('total_tests_taken') || d.num('totalTestsTaken'),
    avgCompletionRate: d.num('avg_completion_rate') || d.num('avgCompletionRate'),
    testsTakenThisWeek: d.num('tests_taken_this_week') || d.num('testsTakenThisWeek'),
    byCategory: {
      coding: {
        total: bc.coding?.total ?? 0,
        enabled: bc.coding?.enabled ?? 0,
      },
      logic: {
        total: bc.logic?.total ?? 0,
        enabled: bc.logic?.enabled ?? 0,
      },
      domain: {
        total: bc.domain?.total ?? 0,
        enabled: bc.domain?.enabled ?? 0,
      },
      personality: {
        total: bc.personality?.total ?? 0,
        enabled: bc.personality?.enabled ?? 0,
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

      const data = await apiClient.get<Record<string, unknown>>(endpoint)
      return {
        tests: (Array.isArray(data.tests) ? data.tests as Record<string, unknown>[] : Array.isArray(data) ? data : []).map(mapBackendTest),
        total: Number(data.total ?? (Array.isArray(data.tests) ? (data.tests as unknown[]).length : 0)),
        limit: Number(data.limit ?? 100),
        offset: Number(data.offset ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { tests: [], total: 0, limit: 100, offset: 0 }
    }
  }

  async getTestById(id: string): Promise<TechnicalTest | null> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/${id}`)
      return mapBackendTest(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
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
      const response = await apiClient.post<Record<string, unknown>>(this.baseEndpoint, payload)
      return mapBackendTest(response)
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error
      }
      return null
    }
  }

  async updateTest(id: string, data: UpdateTestData): Promise<TechnicalTest | null> {
    try {
      const payload: Record<string, unknown> = {}
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

      const response = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}`, payload)
      return mapBackendTest(response)
    } catch (error) {
      if (error instanceof ApiClientError) {
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
        throw error
      }
      return false
    }
  }

  async getClientTests(clientId: string): Promise<ClientTestListResponse> {
    try {
      const endpoint = `${this.clientsEndpoint}/${clientId}/tests`
      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        tests: (Array.isArray(data.tests) ? data.tests as Record<string, unknown>[] : Array.isArray(data) ? data : []).map(mapBackendClientTest),
        total: Number(data.total ?? (Array.isArray(data.tests) ? (data.tests as unknown[]).length : 0)),
        limit: Number(data.limit ?? 100),
        offset: Number(data.offset ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
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
      const payload: Record<string, unknown> = {}
      if (config.enabled !== undefined) payload.enabled = config.enabled
      if (config.customPassingScore !== undefined) payload.custom_passing_score = config.customPassingScore
      if (config.customDuration !== undefined) payload.custom_duration = config.customDuration

      const endpoint = `${this.clientsEndpoint}/${clientId}/tests/${testId}`
      const response = await apiClient.put<Record<string, unknown>>(endpoint, payload, { clientId })
      return mapBackendClientTest(response)
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error
      }
      return null
    }
  }

  async getClientTestStats(clientId: string): Promise<ClientTestStats | null> {
    try {
      const endpoint = `${this.clientsEndpoint}/${clientId}/tests/stats`
      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return mapBackendStats(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async seedTests(): Promise<{ message: string; count: number } | null> {
    try {
      const response = await apiClient.post<Record<string, unknown>>(`${this.baseEndpoint}/seed`, {})
      return { message: String(response.message ?? ''), count: Number(response.count ?? 0) }
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error
      }
      return null
    }
  }
}

export const technicalTestsService = new TechnicalTestsService()
