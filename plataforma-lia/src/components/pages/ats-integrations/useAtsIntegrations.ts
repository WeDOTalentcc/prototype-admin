import { useState, useCallback, useEffect } from "react"
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
  selectedView: ViewTab
  setSelectedView: (v: ViewTab) => void
  selectedSystem: ATSSystem | null
  showSystemModal: boolean
  openSystemModal: (system: ATSSystem) => void
  closeSystemModal: () => void

  atsSystems: typeof ATS_SYSTEMS
  integrations: typeof INTEGRATIONS
  syncLogs: typeof SYNC_LOGS

  connections: ATSConnectionData[]
  loadingConnections: boolean
  refreshConnections: () => void

  getStatusColor: (status: string) => string
}

export interface ATSConnectionData {
  id: string
  provider: string
  provider_name: string
  is_active: boolean
  last_sync_at: string | null
  last_sync_status: string | null
  total_candidates_synced: number
}

export interface UseSystemModalReturn {
  selectedTab: ModalTab
  setSelectedTab: (t: ModalTab) => void
  isConnecting: boolean
  connectionStatus: ConnectionStatus
  connectionMessage: string
  credentials: ATSCredentials
  setCredentials: (c: ATSCredentials) => void
  handleTestConnection: () => void
  handleSaveConnection: () => void
  isSaving: boolean
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
  handleSaveMappings: () => void
  isSavingMappings: boolean
  getFieldTypeIcon: (type: string) => string
  getConfidenceColor: (confidence: number) => string
}

export interface ATSCredentials {
  apiKey: string
  apiSecret: string
  apiEndpoint: string
}

export function useAtsIntegrations(): UseAtsIntegrationsReturn {
  const [selectedView, setSelectedView] = useState<ViewTab>('overview')
  const [selectedSystem, setSelectedSystem] = useState<ATSSystem | null>(null)
  const [showSystemModal, setShowSystemModal] = useState(false)
  const [connections, setConnections] = useState<ATSConnectionData[]>([])
  const [loadingConnections, setLoadingConnections] = useState(false)

  const fetchConnections = useCallback(async () => {
    setLoadingConnections(true)
    try {
      const res = await fetch('/api/backend-proxy/ats/connections')
      if (res.ok) {
        const data = await res.json()
        setConnections(Array.isArray(data) ? data : [])
      }
    } catch {
      // silent — connections list is non-critical
    } finally {
      setLoadingConnections(false)
    }
  }, [])

  useEffect(() => {
    fetchConnections()
  }, [fetchConnections])

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
    connections,
    loadingConnections,
    refreshConnections: fetchConnections,
    getStatusColor
  }
}

export function useSystemModal(system: { type: string }): UseSystemModalReturn {
  const [selectedTab, setSelectedTab] = useState<ModalTab>('connection')
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle')
  const [connectionMessage, setConnectionMessage] = useState('')
  const [mappings, setMappings] = useState<FieldMapping[]>([])
  const [draggedField, setDraggedField] = useState<SystemField | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)
  const [isSavingMappings, setIsSavingMappings] = useState(false)
  const [credentials, setCredentials] = useState<ATSCredentials>({
    apiKey: '',
    apiSecret: '',
    apiEndpoint: '',
  })

  useEffect(() => {
    if (selectedTab !== 'mapping') return
    const loadMappings = async () => {
      try {
        const connRes = await fetch('/api/backend-proxy/ats/connections')
        const allConns: ATSConnectionData[] = connRes.ok ? await connRes.json() : []
        const conn = allConns.find(c => c.provider?.toLowerCase() === system.type && c.is_active)
        if (!conn) return

        const res = await fetch(`/api/backend-proxy/ats/field-mappings?connection_id=${conn.id}`)
        if (!res.ok) return
        const data = await res.json()
        if (Array.isArray(data.mappings) && data.mappings.length > 0) {
          setMappings(data.mappings.map((m: Record<string, unknown>, i: number) => ({
            id: (m.id as string) || `persisted-${i}`,
            sourceField: m.sourceField as string,
            targetField: m.targetField as string,
            sourceFieldName: m.sourceFieldName as string,
            targetFieldName: m.targetFieldName as string,
            confidence: (m.confidence as number) || 100,
            isActive: m.isActive !== false,
          })))
        }
      } catch {
        // silent — non-critical
      }
    }
    loadMappings()
  }, [selectedTab, system.type])

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

  const handleTestConnection = useCallback(async () => {
    if (!credentials.apiKey) {
      setConnectionStatus('error')
      setConnectionMessage('Informe a API Key antes de testar.')
      return
    }

    setConnectionStatus('testing')
    setIsConnecting(true)
    setConnectionMessage('')

    try {
      const res = await fetch('/api/backend-proxy/ats/connections/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: system.type,
          api_key: credentials.apiKey,
          api_endpoint: credentials.apiEndpoint || undefined,
        }),
      })

      const data = await res.json()

      if (data.success) {
        setConnectionStatus('success')
        setConnectionMessage(data.message || 'Conexão estabelecida com sucesso.')
      } else {
        setConnectionStatus('error')
        setConnectionMessage(data.message || 'Falha na conexão. Verifique as credenciais.')
      }
    } catch {
      setConnectionStatus('error')
      setConnectionMessage('Erro de rede ao testar conexão.')
    } finally {
      setIsConnecting(false)
    }
  }, [credentials.apiKey, credentials.apiEndpoint, system.type])

  const handleSaveConnection = useCallback(async () => {
    if (!credentials.apiKey) return

    setIsSaving(true)
    try {
      const res = await fetch('/api/backend-proxy/ats/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: system.type,
          provider_name: system.type === 'gupy' ? 'Gupy' : system.type === 'pandape' ? 'Pandapé' : system.type,
          api_key: credentials.apiKey,
          api_secret: credentials.apiSecret || undefined,
          api_endpoint: credentials.apiEndpoint || undefined,
        }),
      })

      const data = await res.json()
      if (data.success) {
        setConnectionStatus('success')
        setConnectionMessage('Conexão salva com sucesso.')
      } else {
        setConnectionMessage(data.message || 'Erro ao salvar conexão.')
      }
    } catch {
      setConnectionMessage('Erro de rede ao salvar conexão.')
    } finally {
      setIsSaving(false)
    }
  }, [credentials, system.type])

  const handleSaveMappings = useCallback(async () => {
    setIsSavingMappings(true)
    try {
      const connRes = await fetch('/api/backend-proxy/ats/connections')
      const allConns: ATSConnectionData[] = connRes.ok ? await connRes.json() : []
      const conn = allConns.find(c => c.provider?.toLowerCase() === system.type && c.is_active)
      if (!conn) {
        setConnectionMessage('Nenhuma conexão ativa encontrada. Salve a conexão primeiro.')
        setConnectionStatus('error')
        return
      }

      const res = await fetch('/api/backend-proxy/ats/field-mappings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          connection_id: conn.id,
          mappings: mappings.map(m => ({
            sourceField: m.sourceField,
            targetField: m.targetField,
            sourceFieldName: m.sourceFieldName,
            targetFieldName: m.targetFieldName,
            confidence: m.confidence,
            isActive: m.isActive,
          })),
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        setConnectionMessage(errData.detail || `Erro ao salvar mapeamentos (${res.status})`)
        setConnectionStatus('error')
        return
      }

      const data = await res.json()
      if (data.success === false) {
        setConnectionMessage(data.detail || 'Erro ao salvar mapeamentos.')
        setConnectionStatus('error')
        return
      }

      setConnectionMessage('Mapeamentos salvos com sucesso!')
      setConnectionStatus('success')
    } catch {
      setConnectionMessage('Erro ao salvar mapeamentos.')
      setConnectionStatus('error')
    } finally {
      setIsSavingMappings(false)
    }
  }, [mappings, system.type])

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
    return FIELD_TYPE_ICONS[type] ?? '?'
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
    connectionMessage,
    credentials,
    setCredentials,
    handleTestConnection,
    handleSaveConnection,
    isSaving,
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
    handleSaveMappings,
    isSavingMappings,
    getFieldTypeIcon,
    getConfidenceColor
  }
}
