"use client"

import { useState, useEffect, useCallback } from "react"
import {
  templatesService,
  DefaultTemplate,
  TemplateVariable,
  CreateTemplateData,
  UpdateTemplateData,
  TemplateListFilters,
  ApiClientError,
} from "@/services/admin/templates-service"

export interface UseDefaultTemplatesFilters {
  category?: string
  status?: string
  search?: string
}

export interface UseDefaultTemplatesResult {
  templates: DefaultTemplate[]
  variables: TemplateVariable[]
  total: number
  isLoading: boolean
  isSubmitting: boolean
  error: string | null
  filters: UseDefaultTemplatesFilters
  setFilters: (filters: UseDefaultTemplatesFilters) => void
  refetch: () => Promise<void>
  createTemplate: (data: CreateTemplateData) => Promise<DefaultTemplate | null>
  updateTemplate: (id: string, data: UpdateTemplateData) => Promise<DefaultTemplate | null>
  deleteTemplate: (id: string) => Promise<boolean>
  duplicateTemplate: (id: string) => Promise<DefaultTemplate | null>
  seedTemplates: () => Promise<{ success: boolean; count: number }>
}

export function useDefaultTemplates(initialFilters?: UseDefaultTemplatesFilters): UseDefaultTemplatesResult {
  const [templates, setTemplates] = useState<DefaultTemplate[]>([])
  const [variables, setVariables] = useState<TemplateVariable[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<UseDefaultTemplatesFilters>(initialFilters || {})

  const fetchTemplates = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const apiFilters: TemplateListFilters = {}
      if (filters.category && filters.category !== 'all') apiFilters.category = filters.category
      if (filters.status && filters.status !== 'all') apiFilters.status = filters.status
      if (filters.search) apiFilters.search = filters.search

      const response = await templatesService.getTemplates(apiFilters)
      setTemplates(response.templates)
      setTotal(response.total)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar templates")
      }
    } finally {
      setIsLoading(false)
    }
  }, [filters])

  const fetchVariables = useCallback(async () => {
    try {
      const variablesData = await templatesService.getVariables()
      setVariables(variablesData)
    } catch (err) {
    }
  }, [])

  const createTemplate = useCallback(async (data: CreateTemplateData): Promise<DefaultTemplate | null> => {
    setIsSubmitting(true)
    setError(null)

    try {
      const newTemplate = await templatesService.createTemplate(data)
      setTemplates(prev => [newTemplate, ...prev])
      setTotal(prev => prev + 1)
      return newTemplate
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao criar template")
      }
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const updateTemplate = useCallback(async (id: string, data: UpdateTemplateData): Promise<DefaultTemplate | null> => {
    setIsSubmitting(true)
    setError(null)

    const previousTemplates = [...templates]

    setTemplates(prev => prev.map(t => 
      t.id === id ? { ...t, ...data, updatedAt: new Date().toISOString() } : t
    ))

    try {
      const updatedTemplate = await templatesService.updateTemplate(id, data)
      setTemplates(prev => prev.map(t => t.id === id ? updatedTemplate : t))
      return updatedTemplate
    } catch (err) {
      setTemplates(previousTemplates)
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao atualizar template")
      }
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [templates])

  const deleteTemplate = useCallback(async (id: string): Promise<boolean> => {
    setIsSubmitting(true)
    setError(null)

    const previousTemplates = [...templates]
    const previousTotal = total

    setTemplates(prev => prev.filter(t => t.id !== id))
    setTotal(prev => prev - 1)

    try {
      await templatesService.deleteTemplate(id)
      return true
    } catch (err) {
      setTemplates(previousTemplates)
      setTotal(previousTotal)
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao excluir template")
      }
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [templates, total])

  const duplicateTemplate = useCallback(async (id: string): Promise<DefaultTemplate | null> => {
    setIsSubmitting(true)
    setError(null)

    try {
      const duplicatedTemplate = await templatesService.duplicateTemplate(id)
      setTemplates(prev => [duplicatedTemplate, ...prev])
      setTotal(prev => prev + 1)
      return duplicatedTemplate
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao duplicar template")
      }
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const seedTemplates = useCallback(async (): Promise<{ success: boolean; count: number }> => {
    setIsSubmitting(true)
    setError(null)

    try {
      const result = await templatesService.seedTemplates()
      await fetchTemplates()
      return { success: true, count: result.count }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao popular templates")
      }
      return { success: false, count: 0 }
    } finally {
      setIsSubmitting(false)
    }
  }, [fetchTemplates])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  useEffect(() => {
    fetchVariables()
  }, [fetchVariables])

  return {
    templates,
    variables,
    total,
    isLoading,
    isSubmitting,
    error,
    filters,
    setFilters,
    refetch: fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    duplicateTemplate,
    seedTemplates,
  }
}
