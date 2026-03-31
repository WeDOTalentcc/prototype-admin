'use client'

import { useState, useCallback, useRef, useMemo } from 'react'

export type FieldChangeSource = 'panel' | 'chat' | 'orchestrator'

export interface FieldChange {
  id: string
  field: string
  oldValue: unknown
  newValue: unknown
  source: FieldChangeSource
  timestamp: Date
  displayLabel?: string
}

export interface GroupedChange {
  id: string
  changes: FieldChange[]
  timestamp: Date
  summary: string
}

export interface UseChatSyncOptions {
  debounceMs?: number
  maxChanges?: number
  groupingWindowMs?: number
  onGroupedChange?: (group: GroupedChange) => void
  onFieldUpdate?: (fieldId: string, source: FieldChangeSource) => void
}

export interface UseChatSyncReturn {
  trackFieldChange: (change: Omit<FieldChange, 'id' | 'timestamp'>) => void
  getRecentChanges: () => FieldChange[]
  getGroupedChanges: () => GroupedChange[]
  generateChangeSummary: () => string
  generateLLMContext: () => string
  clearChanges: () => void
  pendingChanges: FieldChange[]
  lastGroupedChange: GroupedChange | null
}

const FIELD_LABELS: Record<string, string> = {
  'cargo': 'Cargo',
  'area': 'Área',
  'gestor': 'Gestor',
  'localidade': 'Localidade',
  'modeloTrabalho': 'Modelo de Trabalho',
  'tipoContrato': 'Tipo de Contrato',
  'minSalary': 'Salário Mínimo',
  'maxSalary': 'Salário Máximo',
  'minBonus': 'Bônus Mínimo',
  'maxBonus': 'Bônus Máximo',
  'bonusCriteria': 'Critérios de Bônus',
  'technicalSkill': 'Competência Técnica',
  'behavioralCompetency': 'Competência Comportamental',
  'wsiQuestion': 'Pergunta WSI',
  'benefit': 'Benefício',
  'experienciaMinima': 'Experiência Mínima',
  'formacao': 'Formação',
  'idiomas': 'Idiomas',
}

function getFieldLabel(field: string): string {
  return FIELD_LABELS[field] || field
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não'
  if (typeof value === 'number') return value.toLocaleString('pt-BR')
  if (Array.isArray(value)) {
    if (value.length === 0) return '—'
    return (value as unknown[]).map(String).join(', ')
  }
  if (typeof value === 'object' && value !== null) {
    if ('name' in value && typeof (value as { name: unknown }).name === 'string') return (value as { name: string }).name
    return JSON.stringify(value)
  }
  return String(value)
}

function formatSalaryValue(value: string | number): string {
  if (!value) return '—'
  const numValue = typeof value === 'string' ? parseFloat(value.replace(/\D/g, '')) : value
  if (isNaN(numValue)) return String(value)
  return `R$ ${numValue.toLocaleString('pt-BR')}`
}

function generateChangeMessage(change: FieldChange): string {
  const label = change.displayLabel || getFieldLabel(change.field)
  const isSalaryField = ['minSalary', 'maxSalary', 'minBonus', 'maxBonus'].includes(change.field)
  
  if (change.field === 'technicalSkill') {
    if (change.oldValue === null) {
      return `Adicionada competência: ${change.newValue?.name || change.newValue}`
    }
    if (change.newValue === null) {
      return `Removida competência: ${change.oldValue?.name || change.oldValue}`
    }
    return `Atualizada competência: ${change.newValue?.name || change.newValue}`
  }
  
  if (change.field === 'behavioralCompetency') {
    if (change.oldValue === null) {
      return `Adicionada competência comportamental: ${change.newValue?.name || change.newValue}`
    }
    if (change.newValue === null) {
      return `Removida competência comportamental: ${change.oldValue?.name || change.oldValue}`
    }
    return `Atualizada competência comportamental: ${change.newValue?.name || change.newValue}`
  }
  
  if (change.field === 'wsiQuestion') {
    if (change.oldValue === null) {
      return `Adicionada pergunta de triagem`
    }
    if (change.newValue === null) {
      return `Removida pergunta de triagem`
    }
    return `Atualizada pergunta de triagem`
  }
  
  if (change.field === 'benefit') {
    const name = change.newValue?.name || change.oldValue?.name || 'benefício'
    if (change.newValue?.enabled === false) {
      return `Desativado benefício: ${name}`
    }
    if (change.newValue?.enabled === true && change.oldValue?.enabled === false) {
      return `Ativado benefício: ${name}`
    }
    return `Atualizado benefício: ${name}`
  }
  
  if (change.field === 'benefits') {
    const oldBenefits = Array.isArray(change.oldValue) ? change.oldValue : []
    const newBenefits = Array.isArray(change.newValue) ? change.newValue : []
    
    const changedBenefit = newBenefits.find((newB: { id: string; name: string; enabled: boolean }) => {
      const oldB = oldBenefits.find((ob: { id: string; enabled: boolean }) => ob.id === newB.id)
      return oldB && oldB.enabled !== newB.enabled
    })
    
    if (changedBenefit) {
      if (changedBenefit.enabled) {
        return `${changedBenefit.name} adicionado aos benefícios`
      } else {
        return `${changedBenefit.name} removido dos benefícios`
      }
    }
    
    const enabledCount = newBenefits.filter((b: { enabled: boolean }) => b.enabled).length
    return `Benefícios atualizados (${enabledCount} selecionados)`
  }
  
  if (isSalaryField) {
    const formattedValue = formatSalaryValue(change.newValue)
    return `${label} atualizado para ${formattedValue}`
  }
  
  if (change.field === 'minSalary' || change.field === 'maxSalary') {
    return `Salário atualizado`
  }
  
  const newFormatted = formatValue(change.newValue)
  return `${label} atualizado para ${newFormatted}`
}

function generateGroupSummary(changes: FieldChange[]): string {
  if (changes.length === 1) {
    return generateChangeMessage(changes[0])
  }
  
  const salaryChanges = changes.filter(c => 
    ['minSalary', 'maxSalary'].includes(c.field)
  )
  if (salaryChanges.length >= 2) {
    const minChange = salaryChanges.find(c => c.field === 'minSalary')
    const maxChange = salaryChanges.find(c => c.field === 'maxSalary')
    if (minChange && maxChange) {
      const min = formatSalaryValue(minChange.newValue)
      const max = formatSalaryValue(maxChange.newValue)
      const otherChanges = changes.filter(c => !['minSalary', 'maxSalary'].includes(c.field))
      if (otherChanges.length === 0) {
        return `Salário atualizado para ${min} - ${max}`
      }
    }
  }
  
  const skillChanges = changes.filter(c => c.field === 'technicalSkill')
  if (skillChanges.length > 0) {
    const added = skillChanges.filter(c => c.oldValue === null)
    const removed = skillChanges.filter(c => c.newValue === null)
    const parts: string[] = []
    if (added.length > 0) {
      const names = added.map(c => c.newValue?.name || c.newValue).join(', ')
      parts.push(`Adicionadas competências: ${names}`)
    }
    if (removed.length > 0) {
      const names = removed.map(c => c.oldValue?.name || c.oldValue).join(', ')
      parts.push(`Removidas competências: ${names}`)
    }
    if (parts.length > 0) {
      const otherCount = changes.length - skillChanges.length
      if (otherCount > 0) {
        parts.push(`e ${otherCount} outra(s) alteração(ões)`)
      }
      return parts.join('; ')
    }
  }
  
  return `${changes.length} campos atualizados`
}

function generateId(): string {
  return `change-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function useChatSync(options: UseChatSyncOptions = {}): UseChatSyncReturn {
  const {
    debounceMs = 500,
    maxChanges = 50,
    groupingWindowMs = 1000,
    onGroupedChange,
    onFieldUpdate,
  } = options

  const [changes, setChanges] = useState<FieldChange[]>([])
  const [groupedChanges, setGroupedChanges] = useState<GroupedChange[]>([])
  const [pendingChanges, setPendingChanges] = useState<FieldChange[]>([])
  const [lastGroupedChange, setLastGroupedChange] = useState<GroupedChange | null>(null)
  
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const groupingTimerRef = useRef<NodeJS.Timeout | null>(null)
  const pendingChangesRef = useRef<FieldChange[]>([])

  const flushPendingChanges = useCallback(() => {
    if (pendingChangesRef.current.length === 0) return
    
    const changesToGroup = [...pendingChangesRef.current]
    pendingChangesRef.current = []
    setPendingChanges([])
    
    const group: GroupedChange = {
      id: generateId(),
      changes: changesToGroup,
      timestamp: new Date(),
      summary: generateGroupSummary(changesToGroup),
    }
    
    setGroupedChanges(prev => {
      const newGroups = [...prev, group]
      if (newGroups.length > maxChanges) {
        return newGroups.slice(-maxChanges)
      }
      return newGroups
    })
    
    setLastGroupedChange(group)
    onGroupedChange?.(group)
  }, [maxChanges, onGroupedChange])

  const trackFieldChange = useCallback((change: Omit<FieldChange, 'id' | 'timestamp'>) => {
    const fullChange: FieldChange = {
      ...change,
      id: generateId(),
      timestamp: new Date(),
    }
    
    setChanges(prev => {
      const newChanges = [...prev, fullChange]
      if (newChanges.length > maxChanges) {
        return newChanges.slice(-maxChanges)
      }
      return newChanges
    })
    
    if (onFieldUpdate && (change.source === 'chat' || change.source === 'orchestrator')) {
      onFieldUpdate(change.field, change.source)
    }
    
    pendingChangesRef.current = [...pendingChangesRef.current, fullChange]
    setPendingChanges([...pendingChangesRef.current])
    
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    
    if (groupingTimerRef.current) {
      clearTimeout(groupingTimerRef.current)
    }
    
    debounceTimerRef.current = setTimeout(() => {
      groupingTimerRef.current = setTimeout(() => {
        flushPendingChanges()
      }, groupingWindowMs - debounceMs)
    }, debounceMs)
  }, [debounceMs, groupingWindowMs, maxChanges, flushPendingChanges, onFieldUpdate])

  const getRecentChanges = useCallback(() => {
    return changes
  }, [changes])

  const getGroupedChanges = useCallback(() => {
    return groupedChanges
  }, [groupedChanges])

  const generateChangeSummary = useCallback(() => {
    if (changes.length === 0) return ''
    
    const recentChanges = changes.slice(-10)
    const summaries = recentChanges.map(generateChangeMessage)
    return summaries.join('\n')
  }, [changes])

  const generateLLMContext = useCallback(() => {
    if (changes.length === 0) return ''
    
    const recentChanges = changes.slice(-20)
    const panelChanges = recentChanges.filter(c => c.source === 'panel')
    
    if (panelChanges.length === 0) return ''
    
    const contextParts = [
      '[Alterações recentes feitas pelo usuário no painel:]'
    ]
    
    panelChanges.slice(-10).forEach(change => {
      const label = getFieldLabel(change.field)
      const newValue = formatValue(change.newValue)
      contextParts.push(`- ${label}: ${newValue}`)
    })
    
    return contextParts.join('\n')
  }, [changes])

  const clearChanges = useCallback(() => {
    setChanges([])
    setGroupedChanges([])
    setPendingChanges([])
    setLastGroupedChange(null)
    pendingChangesRef.current = []
    
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    if (groupingTimerRef.current) {
      clearTimeout(groupingTimerRef.current)
    }
  }, [])

  return {
    trackFieldChange,
    getRecentChanges,
    getGroupedChanges,
    generateChangeSummary,
    generateLLMContext,
    clearChanges,
    pendingChanges,
    lastGroupedChange,
  }
}
