"use client"

import { useState, useEffect, useCallback } from 'react'
import { useUIPreferencesStore } from '@/stores/ui-preferences-store'

export interface ColumnConfig {
  id: string
  label: string
  category: string
  visible: boolean
  order: number
}

export interface ColumnConfigState {
  columns: ColumnConfig[]
  savedViews: SavedView[]
}

export interface SavedView {
  id: string
  name: string
  columns: string[]
  createdAt: string
}

const DEFAULT_COLUMNS: ColumnConfig[] = [
  { id: 'id', label: 'ID da Vaga', category: 'principais', visible: true, order: 0 },
  { id: 'status', label: 'Status', category: 'principais', visible: true, order: 1 },
  { id: 'screeningStatus', label: 'Triagem', category: 'principais', visible: true, order: 2 },
  { id: 'title', label: 'Título da Vaga', category: 'principais', visible: true, order: 3 },
  { id: 'candidates', label: 'Candidatos', category: 'principais', visible: true, order: 4 },
  { id: 'performance', label: 'Performance LIA', category: 'principais', visible: true, order: 5 },
  { id: 'recruiter', label: 'Recrutador(a)', category: 'responsaveis', visible: true, order: 6 },
  { id: 'manager', label: 'Gestor(a)', category: 'responsaveis', visible: true, order: 7 },
  { id: 'location', label: 'Localização', category: 'localizacao', visible: true, order: 8 },
  { id: 'stage', label: 'Estágio', category: 'informacoes', visible: false, order: 9 },
  { id: 'priority', label: 'Prioridade', category: 'informacoes', visible: false, order: 10 },
  { id: 'urgencyLevel', label: 'Nível de Urgência', category: 'informacoes', visible: false, order: 11 },
  { id: 'openDate', label: 'Data de Abertura', category: 'informacoes', visible: false, order: 12 },
  { id: 'deadline', label: 'Prazo (Deadline)', category: 'informacoes', visible: false, order: 13 },
  { id: 'level', label: 'Senioridade', category: 'informacoes', visible: false, order: 14 },
  { id: 'isAffirmative', label: 'Vaga Afirmativa', category: 'informacoes', visible: false, order: 15 },
  { id: 'approvalStatus', label: 'Status de Aprovação', category: 'informacoes', visible: false, order: 16 },
  { id: 'description', label: 'Descrição', category: 'informacoes', visible: false, order: 17 },
  { id: 'requirements', label: 'Requisitos', category: 'informacoes', visible: false, order: 18 },
  { id: 'deadlineScreening', label: 'Prazo de Triagem', category: 'prazos', visible: false, order: 19 },
  { id: 'deadlineShortlist', label: 'Data da Shortlist', category: 'prazos', visible: false, order: 20 },
  { id: 'deadlineClosing', label: 'Prazo de Fechamento', category: 'prazos', visible: false, order: 21 },
  { id: 'department', label: 'Departamento', category: 'responsaveis', visible: false, order: 22 },
  { id: 'recruiterEmail', label: 'Email Recrutador', category: 'responsaveis', visible: false, order: 23 },
  { id: 'managerEmail', label: 'Email Gestor', category: 'responsaveis', visible: false, order: 24 },
  { id: 'createdBy', label: 'Criado por', category: 'responsaveis', visible: false, order: 25 },
  { id: 'workModel', label: 'Modelo de Trabalho', category: 'localizacao', visible: false, order: 26 },
  { id: 'salary', label: 'Faixa Salarial', category: 'remuneracao', visible: false, order: 27 },
  { id: 'salaryRangeMin', label: 'Salário Mínimo', category: 'remuneracao', visible: false, order: 28 },
  { id: 'salaryRangeMax', label: 'Salário Máximo', category: 'remuneracao', visible: false, order: 29 },
  { id: 'benefits', label: 'Benefícios', category: 'remuneracao', visible: false, order: 30 },
  { id: 'budget', label: 'Budget', category: 'remuneracao', visible: false, order: 31 },
  { id: 'budgetUsed', label: 'Budget Usado', category: 'remuneracao', visible: false, order: 32 },
  { id: 'type', label: 'Tipo de Contrato', category: 'remuneracao', visible: false, order: 33 },
  { id: 'publishedLinkedIn', label: 'LinkedIn', category: 'divulgacao', visible: false, order: 34 },
  { id: 'publishedWebsite', label: 'Website', category: 'divulgacao', visible: false, order: 35 },
  { id: 'publishedIndeed', label: 'Indeed', category: 'divulgacao', visible: false, order: 36 },
  { id: 'publishedAt', label: 'Data de Publicação', category: 'divulgacao', visible: false, order: 37 },
  { id: 'technicalRequirements', label: 'Skills Técnicas', category: 'requisitos', visible: false, order: 38 },
  { id: 'languages', label: 'Idiomas', category: 'requisitos', visible: false, order: 39 },
  { id: 'behavioralCompetencies', label: 'Competências', category: 'requisitos', visible: false, order: 40 },
  { id: 'screeningQuestions', label: 'Perguntas de Triagem', category: 'requisitos', visible: false, order: 41 },
  { id: 'targetSector', label: 'Setor Alvo', category: 'targeting', visible: false, order: 42 },
  { id: 'targetSegment', label: 'Segmento Alvo', category: 'targeting', visible: false, order: 43 },
  { id: 'targetAudience', label: 'Público-Alvo', category: 'targeting', visible: false, order: 44 },
  { id: 'isConfidential', label: 'Confidencial', category: 'confidencialidade', visible: false, order: 45 },
  { id: 'visibility', label: 'Visibilidade', category: 'confidencialidade', visible: false, order: 46 },
  { id: 'accessList', label: 'Lista de Acesso', category: 'confidencialidade', visible: false, order: 47 },
  { id: 'maskedCompanyName', label: 'Nome Mascarado', category: 'confidencialidade', visible: false, order: 48 },
  { id: 'hiringProcess', label: 'Etapas do Processo', category: 'processo', visible: false, order: 49 },
  { id: 'interviewStages', label: 'Estágios de Entrevista', category: 'processo', visible: false, order: 50 },
  { id: 'timeline', label: 'Timeline', category: 'processo', visible: false, order: 51 },
  { id: 'governanceRules', label: 'Regras de Governança', category: 'processo', visible: false, order: 52 },
  { id: 'screeningConfig', label: 'Config de Triagem', category: 'processo', visible: false, order: 53 },
  { id: 'organizationalStructure', label: 'Estrutura Organizacional', category: 'processo', visible: false, order: 54 },
  { id: 'nps', label: 'NPS', category: 'metricas', visible: false, order: 55 },
  { id: 'viewCount', label: 'Visualizações', category: 'metricas', visible: false, order: 56 },
  { id: 'funnelData', label: 'Dados do Funil', category: 'metricas', visible: false, order: 57 },
  { id: 'liaMetrics', label: 'Métricas LIA', category: 'metricas', visible: false, order: 58 },
  { id: 'nextActions', label: 'Próximas Ações', category: 'metricas', visible: false, order: 59 },
  { id: 'tags', label: 'Tags', category: 'tags', visible: false, order: 60 },
  { id: 'createdAt', label: 'Data de Criação', category: 'timestamps', visible: false, order: 61 },
  { id: 'updatedAt', label: 'Última Atualização', category: 'timestamps', visible: false, order: 62 },
  { id: 'closedAt', label: 'Data de Fechamento', category: 'timestamps', visible: false, order: 63 },
  { id: 'readiness', label: 'Prontidão', category: 'principais', visible: true, order: 64 },
]

export function useJobColumnConfig() {
  const uiPrefs = useUIPreferencesStore()
  const [columns, setColumns] = useState<ColumnConfig[]>(DEFAULT_COLUMNS)
  const [savedViews, setSavedViews] = useState<SavedView[]>([])
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    
    try {
      const stored = uiPrefs.jobColumnConfig
      if (stored) {
        if (stored.columns && Array.isArray(stored.columns)) {
          const mergedColumns = DEFAULT_COLUMNS.map(defaultCol => {
            const savedCol = stored.columns.find(c => c.id === defaultCol.id)
            return savedCol ? { ...defaultCol, visible: savedCol.visible, order: savedCol.order } : defaultCol
          })
          setColumns(mergedColumns.sort((a, b) => a.order - b.order))
        }
        if (stored.savedViews) {
          setSavedViews(stored.savedViews)
        }
      }
    } catch (error) {
      console.error("[useJobColumnConfig] Error:", error)
    }
    setIsLoaded(true)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const saveToStore = useCallback((cols: ColumnConfig[], views: SavedView[]) => {
    if (typeof window === 'undefined') return
    uiPrefs.setJobColumnConfig({ columns: cols, savedViews: views })
  }, [uiPrefs])

  const toggleColumn = useCallback((columnId: string) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible: !col.visible } : col
      )
      saveToStore(updated, savedViews)
      return updated
    })
  }, [savedViews, saveToStore])

  const setColumnVisibility = useCallback((columnId: string, visible: boolean) => {
    setColumns(prev => {
      const updated = prev.map(col => 
        col.id === columnId ? { ...col, visible } : col
      )
      saveToStore(updated, savedViews)
      return updated
    })
  }, [savedViews, saveToStore])

  const reorderColumns = useCallback((fromIndex: number, toIndex: number) => {
    setColumns(prev => {
      const updated = [...prev]
      const [moved] = updated.splice(fromIndex, 1)
      updated.splice(toIndex, 0, moved)
      const reordered = updated.map((col, idx) => ({ ...col, order: idx }))
      saveToStore(reordered, savedViews)
      return reordered
    })
  }, [savedViews, saveToStore])

  const resetToDefault = useCallback(() => {
    setColumns(DEFAULT_COLUMNS)
    saveToStore(DEFAULT_COLUMNS, savedViews)
  }, [savedViews, saveToStore])

  const saveView = useCallback((name: string) => {
    const visibleColumnIds = columns.filter(c => c.visible).map(c => c.id)
    const newView: SavedView = {
      id: `view-${Date.now()}`,
      name,
      columns: visibleColumnIds,
      createdAt: new Date().toISOString()
    }
    setSavedViews(prev => {
      const updated = [...prev, newView]
      saveToStore(columns, updated)
      return updated
    })
  }, [columns, saveToStore])

  const applyView = useCallback((viewId: string) => {
    const view = savedViews.find(v => v.id === viewId)
    if (!view) return
    
    setColumns(prev => {
      const updated = prev.map(col => ({
        ...col,
        visible: view.columns.includes(col.id)
      }))
      saveToStore(updated, savedViews)
      return updated
    })
  }, [savedViews, saveToStore])

  const deleteView = useCallback((viewId: string) => {
    setSavedViews(prev => {
      const updated = prev.filter(v => v.id !== viewId)
      saveToStore(columns, updated)
      return updated
    })
  }, [columns, saveToStore])

  const visibleColumns = columns.filter(c => c.visible)
  const visibleColumnIds = visibleColumns.map(c => c.id)

  const getColumnsByCategory = useCallback(() => {
    const categories: Record<string, ColumnConfig[]> = {}
    columns.forEach(col => {
      if (!categories[col.category]) {
        categories[col.category] = []
      }
      categories[col.category].push(col)
    })
    return categories
  }, [columns])

  return {
    columns,
    visibleColumns,
    visibleColumnIds,
    savedViews,
    isLoaded,
    toggleColumn,
    setColumnVisibility,
    reorderColumns,
    resetToDefault,
    saveView,
    applyView,
    deleteView,
    getColumnsByCategory
  }
}
