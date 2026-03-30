"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
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
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [filters, setFilters] = useState<UseDefaultTemplatesFilters>(initialFilters || {})

  const buildApiFilters = (f: UseDefaultTemplatesFilters): TemplateListFilters => {
    const apiFilters: TemplateListFilters = {}
    if (f.category && f.category !== "all") apiFilters.category = f.category
    if (f.status && f.status !== "all") apiFilters.status = f.status
    if (f.search) apiFilters.search = f.search
    return apiFilters
  }

  const { data: templatesData, error: templatesError, isLoading, mutate: mutateTemplates } = useSWR(
    ["adminDefaultTemplates", filters.category ?? "", filters.status ?? "", filters.search ?? ""],
    ([, , ,]) => templatesService.getTemplates(buildApiFilters(filters))
  )

  const { data: variablesData, mutate: mutateVariables } = useSWR(
    "adminTemplateVariables",
    () => templatesService.getVariables()
  )

  const fetchError = templatesError instanceof ApiClientError ? templatesError.message
    : templatesError instanceof Error ? templatesError.message
    : templatesError ? String(templatesError) : null

  const error = submitError ?? fetchError

  const createTemplate = useCallback(async (data: CreateTemplateData): Promise<DefaultTemplate | null> => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const newTemplate = await templatesService.createTemplate(data)
      await mutateTemplates()
      return newTemplate
    } catch (err) {
      setSubmitError(err instanceof ApiClientError ? err.message : "Erro ao criar template")
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [mutateTemplates])

  const updateTemplate = useCallback(async (id: string, data: UpdateTemplateData): Promise<DefaultTemplate | null> => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const updatedTemplate = await templatesService.updateTemplate(id, data)
      await mutateTemplates()
      return updatedTemplate
    } catch (err) {
      setSubmitError(err instanceof ApiClientError ? err.message : "Erro ao atualizar template")
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [mutateTemplates])

  const deleteTemplate = useCallback(async (id: string): Promise<boolean> => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      await templatesService.deleteTemplate(id)
      await mutateTemplates()
      return true
    } catch (err) {
      setSubmitError(err instanceof ApiClientError ? err.message : "Erro ao excluir template")
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [mutateTemplates])

  const duplicateTemplate = useCallback(async (id: string): Promise<DefaultTemplate | null> => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const duplicatedTemplate = await templatesService.duplicateTemplate(id)
      await mutateTemplates()
      return duplicatedTemplate
    } catch (err) {
      setSubmitError(err instanceof ApiClientError ? err.message : "Erro ao duplicar template")
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [mutateTemplates])

  const seedTemplates = useCallback(async (): Promise<{ success: boolean; count: number }> => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const result = await templatesService.seedTemplates()
      await mutateTemplates()
      return { success: true, count: result.count }
    } catch (err) {
      setSubmitError(err instanceof ApiClientError ? err.message : "Erro ao popular templates")
      return { success: false, count: 0 }
    } finally {
      setIsSubmitting(false)
    }
  }, [mutateTemplates])

  return {
    templates: templatesData?.templates ?? [],
    variables: variablesData ?? [],
    total: templatesData?.total ?? 0,
    isLoading,
    isSubmitting,
    error,
    filters,
    setFilters,
    refetch: async () => { await mutateTemplates() },
    createTemplate,
    updateTemplate,
    deleteTemplate,
    duplicateTemplate,
    seedTemplates,
  }
}
