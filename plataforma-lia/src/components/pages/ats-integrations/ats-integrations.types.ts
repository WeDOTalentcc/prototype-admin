export interface ATSSystem {
  id: string
  name: string
  type: 'sap' | 'workday' | 'bamboohr' | 'greenhouse' | 'custom' | 'gupy' | 'pandape' | 'merge'
  status: 'connected' | 'connecting' | 'error' | 'disabled'
  description: string
  logo?: string
  lastSync?: string
  totalRecords: number
  syncedRecords: number
  errorCount: number
  features: string[]
  webhookUrl?: string
  apiEndpoint?: string
  version?: string
}

export interface SyncLog {
  id: string
  timestamp: string
  system: string
  type: 'sync' | 'webhook' | 'manual'
  status: 'success' | 'warning' | 'error'
  records: number
  duration: number
  message: string
  details?: string
}

export interface Integration {
  id: string
  name: string
  system: ATSSystem
  isActive: boolean
  lastRun: string
  nextRun: string
  frequency: 'realtime' | 'hourly' | 'daily' | 'weekly'
  direction: 'import' | 'export' | 'bidirectional'
  mappedFields: number
  totalFields: number
}

export interface SystemField {
  id: string
  name: string
  type: 'string' | 'email' | 'phone' | 'number' | 'date' | 'url' | 'select'
  required: boolean
  description: string
}

export interface FieldMapping {
  id: string
  sourceField: string
  targetField: string
  sourceFieldName: string
  targetFieldName: string
  isActive: boolean
  confidence: number
}

export interface MappingTemplate {
  id: string
  name: string
  description: string
  mappings: {
    sourceField: string
    targetField: string
    confidence: number
  }[]
}

export type ViewTab = 'overview' | 'systems' | 'integrations' | 'logs'
export type ModalTab = 'connection' | 'mapping' | 'sync' | 'webhooks'
export type ConnectionStatus = 'idle' | 'testing' | 'success' | 'error'

export interface SystemConfigurationModalProps {
  system: ATSSystem
  onClose: () => void
}
