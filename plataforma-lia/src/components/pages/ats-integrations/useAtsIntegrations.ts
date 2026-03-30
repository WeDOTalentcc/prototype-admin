import { useState, useCallback } from "react"
import type {
  ATSSystem,
  FieldMapping,
  SystemField,
  ViewTab,
  ModalTab,
  ConnectionStatus
} from './ats-integrations.types'
import {
  ATS_SYSTEMS,
  INTEGRATIONS,
  SYNC_LOGS,
  LIA_FIELDS,
  SAP_FIELDS,
  DEFAULT_FIELDS,
  MAPPING_TEMPLATES,
  FIELD_TYPE_ICONS
} from './ats-integrations.constants'

export interface UseAtsIntegrationsReturn {
  // page state
  selectedView: ViewTab
  setSelectedView: (v: ViewTab) => void
  selectedSystem: ATSSystem | null
  showSystemModal: boolean
  openSystemModal: (system: ATSSystem) => void
  closeSystemModal: () => void

  // derived data (constants re-exported for JSX)
  atsSystems: typeof ATS_SYSTEMS
  integrations: typeof INTEGRATIONS
  syncLogs: typeof SYNC_LOGS

  // helpers
  getStatusColor: (status: string) => string
}

export interface UseSystemModalReturn {
  // modal tab
  selectedTab: ModalTab
  setSelectedTab: (t: ModalTab) => void
  // connection
  isConnecting: boolean
  connectionStatus: ConnectionStatus
  handleTestConnection: () => void
  // mapping
  mappings: FieldMapping[]
  draggedField: SystemField | null
  selectedTemplate: string
  systemFields: SystemField[]
  liaFields: typeof LIA_FIELDS
  mappingTemplates: typeof MAPPING_TEMPLATES
  handleDragStart: (field: SystemField) => void
  handleDragOver: (e: React.DragEvent) => void
  handleDrop: (e: React.DragEvent, targetField: SystemField) => void
  applyTemplate: (templateId: string) => void
  removeMapping: (mappingId: string) => void
  // pure utils
  getFieldTypeIcon: (type: string) => string
  getConfidenceColor: (confidence: number) => string
}

// ── Page-level hook ────────────────────────────────────────────────────────
export function useAtsIntegrations(): UseAtsIntegrationsReturn {
  const [selectedView, setSelectedView] = useState<ViewTab>('overview')
  const [selectedSystem, setSelectedSystem] = useState<ATSSystem | null>(null)
  const [showSystemModal, setShowSystemModal] = useState(false)

  const openSystemModal = useCallback((system: ATSSystem) => {
    setSelectedSystem(system)
    setShowSystemModal(true)
  }, [])

  const closeSystemModal = useCallback(() => {
    setShowSystemModal(false)
    setSelectedSystem(null)
  }, [])

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'connected': return 'bg-status-success/10 text-status-success border-status-success/30'
      case 'connecting': return 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default'
      case 'error': return 'bg-status-error/10 text-status-error border-status-error/30'
      case 'disabled': return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
      default: return 'bg-status-warning/10 text-status-warning border-status-warning/30'
    }
  }, [])

  return {
    selectedView,
    setSelectedView,
    selectedSystem,
    showSystemModal,
    openSystemModal,
    closeSystemModal,
    atsSystems: ATS_SYSTEMS,
    integrations: INTEGRATIONS,
    syncLogs: SYNC_LOGS,
    getStatusColor
  }
}

// ── Modal-level hook ───────────────────────────────────────────────────────
export function useSystemModal(system: { type: string }): UseSystemModalReturn {
  const [selectedTab, setSelectedTab] = useState<ModalTab>('connection')
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle')
  const [mappings, setMappings] = useState<FieldMapping[]>([])
  const [draggedField, setDraggedField] = useState<SystemField | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')

  const systemFields: SystemField[] = system.type === 'sap' ? SAP_FIELDS : DEFAULT_FIELDS

  const calculateConfidence = (source: SystemField, target: SystemField): number => {
    let confidence = 0
    if (source.type === target.type) confidence += 40
    else if (
      (source.type === 'string' && target.type === 'email') ||
      (source.type === 'email' && target.type === 'string')
    ) confidence += 20
    const sourceName = source.name.toLowerCase()
    const targetName = target.name.toLowerCase()
    if (sourceName.includes('name') && targetName.includes('nome')) confidence += 30
    if (sourceName.includes('email') && targetName.includes('email')) confidence += 40
    if (sourceName.includes('phone') && targetName.includes('telefone')) confidence += 40
    if (sourceName.includes('id') && targetName.includes('id')) confidence += 50
    return Math.min(confidence, 100)
  }

  const handleTestConnection = useCallback(() => {
    setConnectionStatus('testing')
    setIsConnecting(true)
    setTimeout(() => {
      setConnectionStatus('success')
      setIsConnecting(false)
    }, 3000)
  }, [])

  const handleDragStart = useCallback((field: SystemField) => {
    setDraggedField(field)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, targetField: SystemField) => {
    e.preventDefault()
    setDraggedField(current => {
      if (current) {
        const newMapping: FieldMapping = {
          id: `${current.id}_${targetField.id}`,
          sourceField: current.id,
          targetField: targetField.id,
          sourceFieldName: current.name,
          targetFieldName: targetField.name,
          isActive: true,
          confidence: calculateConfidence(current, targetField)
        }
        setMappings(prev => [...prev.filter(m => m.targetField !== targetField.id), newMapping])
      }
      return null
    })
  }, [])

  const applyTemplate = useCallback((templateId: string) => {
    const template = MAPPING_TEMPLATES.find(t => t.id === templateId)
    if (template) {
      const newMappings: FieldMapping[] = template.mappings.map(m => ({
        id: `${m.sourceField}_${m.targetField}`,
        sourceField: m.sourceField,
        targetField: m.targetField,
        sourceFieldName: systemFields.find(f => f.id === m.sourceField)?.name ?? m.sourceField,
        targetFieldName: LIA_FIELDS.find(f => f.id === m.targetField)?.name ?? m.targetField,
        isActive: true,
        confidence: m.confidence
      }))
      setMappings(newMappings)
      setSelectedTemplate(templateId)
    }
  }, [systemFields])

  const removeMapping = useCallback((mappingId: string) => {
    setMappings(prev => prev.filter(m => m.id !== mappingId))
  }, [])

  const getFieldTypeIcon = useCallback((type: string) => {
    return FIELD_TYPE_ICONS[type] ?? '❓'
  }, [])

  const getConfidenceColor = useCallback((confidence: number) => {
    if (confidence >= 90) return 'text-status-success bg-status-success/10'
    if (confidence >= 70) return 'text-status-warning bg-status-warning/10'
    return 'text-status-error bg-status-error/10'
  }, [])

  return {
    selectedTab,
    setSelectedTab,
    isConnecting,
    connectionStatus,
    handleTestConnection,
    mappings,
    draggedField,
    selectedTemplate,
    systemFields,
    liaFields: LIA_FIELDS,
    mappingTemplates: MAPPING_TEMPLATES,
    handleDragStart,
    handleDragOver,
    handleDrop,
    applyTemplate,
    removeMapping,
    getFieldTypeIcon,
    getConfidenceColor
  }
}
