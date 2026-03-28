import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

export interface DefaultTemplate {
  id: string
  name: string
  category: 'email' | 'sms' | 'whatsapp' | 'push'
  subject?: string
  body: string
  variables: string[]
  status: 'active' | 'draft' | 'archived'
  usedByClients: number
  createdAt: string
  updatedAt: string
}

export interface TemplateVariable {
  key: string
  label: string
  description: string
}

export interface CreateTemplateData {
  name: string
  category: 'email' | 'sms' | 'whatsapp' | 'push'
  subject?: string
  body: string
  status?: 'active' | 'draft' | 'archived'
}

export interface UpdateTemplateData {
  name?: string
  category?: 'email' | 'sms' | 'whatsapp' | 'push'
  subject?: string
  body?: string
  status?: 'active' | 'draft' | 'archived'
}

export interface TemplateListFilters {
  category?: string
  status?: string
  search?: string
}

export interface GeneratedTemplate {
  subject: string
  body_html: string
  variables_used: string[]
}

export interface TemplatePreviewResult {
  subject: string
  body_html: string
  body_text: string | null
}

export interface GenerateTemplateContext {
  job_title?: string
  company_name?: string
  tone?: 'formal' | 'casual'
  candidate_name?: string
  recruiter_name?: string
  [key: string]: string | undefined
}

export interface TemplatesListResponse {
  templates: DefaultTemplate[]
  total: number
}

export interface VariablesListResponse {
  variables: TemplateVariable[]
}

export { ApiClientError }

function mapBackendTemplate(data: Record<string, unknown>): DefaultTemplate {
  const d = safeData(data)
  return {
    id: d.str('id'),
    name: d.str('name'),
    category: d.str('category') as DefaultTemplate['category'],
    subject: d.str('subject') || undefined,
    body: d.str('body'),
    variables: d.arr<string>('variables'),
    status: d.str('status', 'draft') as DefaultTemplate['status'],
    usedByClients: d.num('used_by_clients') || d.num('usedByClients'),
    createdAt: d.str('created_at') || d.str('createdAt'),
    updatedAt: d.str('updated_at') || d.str('updatedAt'),
  }
}

function mapBackendVariable(data: Record<string, unknown>): TemplateVariable {
  const d = safeData(data)
  return {
    key: d.str('key'),
    label: d.str('label'),
    description: d.str('description'),
  }
}

class TemplatesService {
  private baseEndpoint = '/default-templates'

  async getTemplates(filters: TemplateListFilters = {}): Promise<TemplatesListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (filters.category && filters.category !== 'all') {
        queryParams.set('category', filters.category)
      }
      if (filters.status && filters.status !== 'all') {
        queryParams.set('status', filters.status)
      }
      if (filters.search) {
        queryParams.set('search', filters.search)
      }

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}?${queryParams}`
        : this.baseEndpoint

      const data = await apiClient.get<any>(endpoint)
      return {
        templates: (data.templates || data || []).map(mapBackendTemplate),
        total: data.total || (data.templates || data || []).length,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { templates: [], total: 0 }
    }
  }

  async getTemplateById(id: string): Promise<DefaultTemplate | null> {
    try {
      const data = await apiClient.get<any>(`${this.baseEndpoint}/${id}`)
      return mapBackendTemplate(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async createTemplate(templateData: CreateTemplateData): Promise<DefaultTemplate> {
    const payload = {
      name: templateData.name,
      category: templateData.category,
      subject: templateData.subject,
      body: templateData.body,
      status: templateData.status || 'draft',
    }

    const data = await apiClient.post<any>(this.baseEndpoint, payload)
    return mapBackendTemplate(data)
  }

  async updateTemplate(id: string, templateData: UpdateTemplateData): Promise<DefaultTemplate> {
    const payload: Record<string, unknown> = {}
    if (templateData.name !== undefined) payload.name = templateData.name
    if (templateData.category !== undefined) payload.category = templateData.category
    if (templateData.subject !== undefined) payload.subject = templateData.subject
    if (templateData.body !== undefined) payload.body = templateData.body
    if (templateData.status !== undefined) payload.status = templateData.status

    const data = await apiClient.put<any>(`${this.baseEndpoint}/${id}`, payload)
    return mapBackendTemplate(data)
  }

  async deleteTemplate(id: string): Promise<void> {
    await apiClient.delete(`${this.baseEndpoint}/${id}`)
  }

  async duplicateTemplate(id: string): Promise<DefaultTemplate> {
    const data = await apiClient.post<any>(`${this.baseEndpoint}/${id}/duplicate`, {})
    return mapBackendTemplate(data)
  }

  async getVariables(): Promise<TemplateVariable[]> {
    try {
      const data = await apiClient.get<any>(`${this.baseEndpoint}/variables`)
      return (data.variables || data || []).map(mapBackendVariable)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return []
    }
  }

  async seedTemplates(): Promise<{ message: string; count: number }> {
    const data = await apiClient.post<any>(`${this.baseEndpoint}/seed`, {})
    return {
      message: data.message || 'Templates seeded successfully',
      count: data.count || 0,
    }
  }

  async generateTemplate(type: string, context: GenerateTemplateContext): Promise<GeneratedTemplate> {
    const payload = {
      template_type: type,
      context: context,
      language: 'pt-BR',
    }

    const response = await fetch('/api/backend-proxy/email-templates/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiClientError({
        status: response.status,
        message: errorData.error || 'Erro ao gerar template com IA',
        isAuthError: response.status === 401,
        isForbidden: response.status === 403,
        isNetworkError: false,
      })
    }

    const data = await response.json()
    
    if (!data.success) {
      throw new ApiClientError({
        status: 500,
        message: 'Falha na geração do template',
        isAuthError: false,
        isForbidden: false,
        isNetworkError: false,
      })
    }

    return {
      subject: data.data.subject,
      body_html: data.data.body_html,
      variables_used: data.data.variables_used || [],
    }
  }

  async previewTemplate(templateId: string, variables: Record<string, string>): Promise<TemplatePreviewResult> {
    const payload = {
      variables: variables,
    }

    const response = await fetch(`/api/backend-proxy/email-templates/${templateId}/preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiClientError({
        status: response.status,
        message: errorData.error || 'Erro ao renderizar preview do template',
        isAuthError: response.status === 401,
        isForbidden: response.status === 403,
        isNetworkError: false,
      })
    }

    const data = await response.json()
    
    if (!data.success) {
      throw new ApiClientError({
        status: 500,
        message: 'Falha ao renderizar preview do template',
        isAuthError: false,
        isForbidden: false,
        isNetworkError: false,
      })
    }

    return {
      subject: data.data.subject,
      body_html: data.data.body_html,
      body_text: data.data.body_text || null,
    }
  }
}

export const templatesService = new TemplatesService()
