"use client"

import { useState, useCallback, useEffect } from "react"

export interface DataField {
  id: string
  name: string
  displayName: string
  type: 'text' | 'email' | 'phone' | 'date' | 'file' | 'select' | 'textarea'
  required: boolean
  enabled: boolean
  isDefault: boolean
  databaseField?: string
  savesToProfile: boolean
}

export interface StageConfig {
  stageId: string
  stageName: string
  stageDisplayName: string
  requiredFields: string[]
  isAutomatic: boolean
  isBlocking: boolean
}

export interface PortalBranding {
  logoUrl: string | null
  primaryColor: string
  welcomeMessage: string
  thankYouMessage: string
}

export type CollectionMode = 'portal_only' | 'chat_only' | 'candidate_choice'

export interface CollectionMessages {
  initialRequest: string
  choicePrompt: string
  chatStartMessage: string
  documentReceived: string
  pendingReminder: string
  allComplete: string
}

export interface LgpdConfig {
  enabled: boolean
  requireConsent: boolean
  consentMessage: string
  disclaimerText: string
  dataRetentionDays: number
  allowDataDeletion: boolean
}

export interface DataRequestConfig {
  otpRequired: boolean
  expirationDays: number
  autoReminders: boolean
  reminderDays: number
  collectionMode: CollectionMode
  collectionMessages: CollectionMessages
  lgpd: LgpdConfig
  fields: DataField[]
  stageConfigs: StageConfig[]
  branding: PortalBranding
}

interface ApiCollectionMessages {
  initial_request: string
  choice_prompt: string
  chat_start_message: string
  document_received: string
  pending_reminder: string
  all_complete: string
}

interface ApiLgpdConfig {
  require_consent: boolean
  consent_message: string
  disclaimer_text: string
  data_retention_days: number
  allow_data_deletion: boolean
}

interface ApiCollectionSettings {
  collection_mode: CollectionMode
  collection_messages: ApiCollectionMessages
  lgpd: ApiLgpdConfig
}

export const DEFAULT_DATA_FIELDS: DataField[] = [
  { id: 'full_name', name: 'full_name', displayName: 'Nome Completo', type: 'text', required: true, enabled: true, isDefault: true, databaseField: 'name', savesToProfile: true },
  { id: 'email', name: 'email', displayName: 'Email', type: 'email', required: true, enabled: true, isDefault: true, databaseField: 'email', savesToProfile: true },
  { id: 'phone', name: 'phone', displayName: 'Telefone', type: 'phone', required: true, enabled: true, isDefault: true, databaseField: 'phone', savesToProfile: true },
  { id: 'cpf', name: 'cpf', displayName: 'CPF', type: 'text', required: false, enabled: true, isDefault: true, databaseField: 'cpf', savesToProfile: true },
  { id: 'birth_date', name: 'birth_date', displayName: 'Data de Nascimento', type: 'date', required: false, enabled: true, isDefault: true, databaseField: 'birth_date', savesToProfile: true },
  { id: 'address', name: 'address', displayName: 'Endereço Completo', type: 'textarea', required: false, enabled: true, isDefault: true, databaseField: 'address', savesToProfile: true },
  { id: 'rg', name: 'rg', displayName: 'RG', type: 'text', required: false, enabled: false, isDefault: true, databaseField: 'rg', savesToProfile: true },
  { id: 'ctps', name: 'ctps', displayName: 'CTPS', type: 'text', required: false, enabled: false, isDefault: true, databaseField: 'ctps', savesToProfile: true },
  { id: 'pis', name: 'pis', displayName: 'PIS/PASEP', type: 'text', required: false, enabled: false, isDefault: true, databaseField: 'pis', savesToProfile: true },
  { id: 'bank_info', name: 'bank_info', displayName: 'Dados Bancários', type: 'text', required: false, enabled: false, isDefault: true, databaseField: 'bank_info', savesToProfile: true },
  { id: 'emergency_contact', name: 'emergency_contact', displayName: 'Contato de Emergência', type: 'text', required: false, enabled: false, isDefault: true, databaseField: 'emergency_contact', savesToProfile: true },
  { id: 'cv_document', name: 'cv_document', displayName: 'Currículo (Arquivo)', type: 'file', required: false, enabled: true, isDefault: true, databaseField: 'cv_url', savesToProfile: true },
  { id: 'id_document', name: 'id_document', displayName: 'Documento de Identidade', type: 'file', required: false, enabled: false, isDefault: true, savesToProfile: false },
  { id: 'proof_of_address', name: 'proof_of_address', displayName: 'Comprovante de Residência', type: 'file', required: false, enabled: false, isDefault: true, savesToProfile: false },
]

export const DEFAULT_STAGE_CONFIGS: StageConfig[] = [
  { stageId: 'sourcing', stageName: 'sourcing', stageDisplayName: 'Funil', requiredFields: ['full_name', 'email', 'phone'], isAutomatic: false, isBlocking: false },
  { stageId: 'screening', stageName: 'screening', stageDisplayName: 'Triagem', requiredFields: ['full_name', 'email', 'phone', 'cv_document'], isAutomatic: true, isBlocking: false },
  { stageId: 'long_list', stageName: 'long_list', stageDisplayName: 'Long List', requiredFields: [], isAutomatic: false, isBlocking: false },
  { stageId: 'short_list', stageName: 'short_list', stageDisplayName: 'Short List', requiredFields: [], isAutomatic: false, isBlocking: false },
  { stageId: 'interview_hr', stageName: 'interview_hr', stageDisplayName: 'Entrevista RH', requiredFields: ['cpf', 'birth_date'], isAutomatic: true, isBlocking: false },
  { stageId: 'interview_technical', stageName: 'interview_technical', stageDisplayName: 'Entrevista Técnica', requiredFields: [], isAutomatic: false, isBlocking: false },
  { stageId: 'interview_manager', stageName: 'interview_manager', stageDisplayName: 'Entrevista Gestor', requiredFields: [], isAutomatic: false, isBlocking: false },
  { stageId: 'offer', stageName: 'offer', stageDisplayName: 'Proposta', requiredFields: ['address', 'rg', 'ctps', 'pis', 'bank_info', 'id_document', 'proof_of_address'], isAutomatic: true, isBlocking: true },
]

const DEFAULT_BRANDING: PortalBranding = {
  logoUrl: null,
  primaryColor: 'var(--wedo-cyan)',
  welcomeMessage: 'Olá! Precisamos de algumas informações adicionais para dar continuidade ao seu processo seletivo.',
  thankYouMessage: 'Obrigado! Suas informações foram recebidas com sucesso. Entraremos em contato em breve.',
}

const DEFAULT_COLLECTION_MESSAGES: CollectionMessages = {
  initialRequest: 'Olá {{nome}}! 👋 Para dar continuidade ao seu processo seletivo na {{empresa}}, precisamos de algumas informações e documentos.',
  choicePrompt: 'Como você prefere enviar?\n\n1️⃣ Pelo link (formulário completo)\n2️⃣ Aqui pelo chat (envio uma pergunta por vez)\n\nResponda 1 ou 2',
  chatStartMessage: 'Perfeito! Vou pedir os documentos um por um. Pode enviar foto ou arquivo PDF.\n\nPrimeiro, preciso do seu {{campo}}:',
  documentReceived: '✅ {{campo}} recebido! Agora preciso do {{proximo_campo}}:',
  pendingReminder: 'Olá {{nome}}! 📋 Lembrete: ainda faltam alguns documentos para completar seu cadastro:\n\n{{campos_pendentes}}\n\nPrazo: {{dias_restantes}} dias',
  allComplete: '🎉 Perfeito, {{nome}}! Recebemos todos os documentos. Nossa equipe vai analisar e entraremos em contato em breve!',
}

const DEFAULT_LGPD_CONFIG: LgpdConfig = {
  enabled: true,
  requireConsent: true,
  consentMessage: 'Para continuar, preciso da sua autorização para coletar e processar seus dados pessoais conforme a LGPD (Lei Geral de Proteção de Dados).\n\nSeus dados serão usados exclusivamente para o processo seletivo na {{empresa}} e serão tratados com segurança.\n\nVocê autoriza? Responda SIM para continuar.',
  disclaimerText: 'Ao enviar seus dados, você concorda com nossa Política de Privacidade e autoriza o tratamento dos seus dados pessoais para fins de processo seletivo, conforme a Lei nº 13.709/2018 (LGPD). Você pode solicitar a exclusão dos seus dados a qualquer momento.',
  dataRetentionDays: 365,
  allowDataDeletion: true,
}

function mapApiToFrontend(apiData: ApiCollectionSettings): Partial<DataRequestConfig> {
  return {
    collectionMode: apiData.collection_mode,
    collectionMessages: {
      initialRequest: apiData.collection_messages.initial_request,
      choicePrompt: apiData.collection_messages.choice_prompt,
      chatStartMessage: apiData.collection_messages.chat_start_message,
      documentReceived: apiData.collection_messages.document_received,
      pendingReminder: apiData.collection_messages.pending_reminder,
      allComplete: apiData.collection_messages.all_complete,
    },
    lgpd: {
      enabled: true,
      requireConsent: apiData.lgpd.require_consent,
      consentMessage: apiData.lgpd.consent_message,
      disclaimerText: apiData.lgpd.disclaimer_text,
      dataRetentionDays: apiData.lgpd.data_retention_days,
      allowDataDeletion: apiData.lgpd.allow_data_deletion,
    },
  }
}

function mapFrontendToApi(config: DataRequestConfig): ApiCollectionSettings {
  return {
    collection_mode: config.collectionMode,
    collection_messages: {
      initial_request: config.collectionMessages.initialRequest,
      choice_prompt: config.collectionMessages.choicePrompt,
      chat_start_message: config.collectionMessages.chatStartMessage,
      document_received: config.collectionMessages.documentReceived,
      pending_reminder: config.collectionMessages.pendingReminder,
      all_complete: config.collectionMessages.allComplete,
    },
    lgpd: {
      require_consent: config.lgpd.requireConsent,
      consent_message: config.lgpd.consentMessage,
      disclaimer_text: config.lgpd.disclaimerText,
      data_retention_days: config.lgpd.dataRetentionDays,
      allow_data_deletion: config.lgpd.allowDataDeletion,
    },
  }
}

const getDefaultConfig = (): DataRequestConfig => ({
  otpRequired: true,
  expirationDays: 7,
  autoReminders: true,
  reminderDays: 2,
  collectionMode: 'candidate_choice',
  collectionMessages: DEFAULT_COLLECTION_MESSAGES,
  lgpd: DEFAULT_LGPD_CONFIG,
  fields: DEFAULT_DATA_FIELDS,
  stageConfigs: DEFAULT_STAGE_CONFIGS,
  branding: DEFAULT_BRANDING,
})

export function useDataRequestConfig(companyId?: string) {
  const [config, setConfig] = useState<DataRequestConfig>(getDefaultConfig())
  const [originalConfig, setOriginalConfig] = useState<DataRequestConfig>(getDefaultConfig())
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadConfig = useCallback(async () => {
    if (!companyId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `/api/backend-proxy/data-requests/config/collection-settings?company_id=${companyId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      if (response.status === 404) {
        const defaultConfig = getDefaultConfig()
        setConfig(defaultConfig)
        setOriginalConfig(defaultConfig)
        setIsLoading(false)
        return
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to load config: ${response.status}`)
      }

      const apiData: ApiCollectionSettings = await response.json()
      const mappedData = mapApiToFrontend(apiData)
      
      const mergedConfig: DataRequestConfig = {
        ...getDefaultConfig(),
        ...mappedData,
      }
      
      setConfig(mergedConfig)
      setOriginalConfig(mergedConfig)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar configurações')
      const defaultConfig = getDefaultConfig()
      setConfig(defaultConfig)
      setOriginalConfig(defaultConfig)
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    loadConfig()
  }, [loadConfig])

  const updateGeneralConfig = useCallback((updates: Partial<Pick<DataRequestConfig, 'otpRequired' | 'expirationDays' | 'autoReminders' | 'reminderDays' | 'collectionMode'>>) => {
    setConfig(prev => ({ ...prev, ...updates }))
    setHasChanges(true)
  }, [])

  const updateCollectionMessages = useCallback((updates: Partial<CollectionMessages>) => {
    setConfig(prev => ({
      ...prev,
      collectionMessages: { ...prev.collectionMessages, ...updates }
    }))
    setHasChanges(true)
  }, [])

  const updateLgpdConfig = useCallback((updates: Partial<LgpdConfig>) => {
    setConfig(prev => ({
      ...prev,
      lgpd: { ...prev.lgpd, ...updates }
    }))
    setHasChanges(true)
  }, [])

  const toggleFieldEnabled = useCallback((fieldId: string) => {
    setConfig(prev => ({
      ...prev,
      fields: prev.fields.map(f => 
        f.id === fieldId ? { ...f, enabled: !f.enabled } : f
      )
    }))
    setHasChanges(true)
  }, [])

  const addCustomField = useCallback((field: Omit<DataField, 'id' | 'isDefault' | 'savesToProfile'>) => {
    const newField: DataField = {
      ...field,
      id: `custom_${Date.now()}`,
      isDefault: false,
      savesToProfile: false,
    }
    setConfig(prev => ({
      ...prev,
      fields: [...prev.fields, newField]
    }))
    setHasChanges(true)
  }, [])

  const removeCustomField = useCallback((fieldId: string) => {
    setConfig(prev => ({
      ...prev,
      fields: prev.fields.filter(f => f.id !== fieldId)
    }))
    setHasChanges(true)
  }, [])

  const updateStageConfig = useCallback((stageId: string, updates: Partial<Omit<StageConfig, 'stageId' | 'stageName' | 'stageDisplayName'>>) => {
    setConfig(prev => ({
      ...prev,
      stageConfigs: prev.stageConfigs.map(s =>
        s.stageId === stageId ? { ...s, ...updates } : s
      )
    }))
    setHasChanges(true)
  }, [])

  const toggleStageField = useCallback((stageId: string, fieldId: string) => {
    setConfig(prev => ({
      ...prev,
      stageConfigs: prev.stageConfigs.map(s => {
        if (s.stageId !== stageId) return s
        const hasField = s.requiredFields.includes(fieldId)
        return {
          ...s,
          requiredFields: hasField 
            ? s.requiredFields.filter(f => f !== fieldId)
            : [...s.requiredFields, fieldId]
        }
      })
    }))
    setHasChanges(true)
  }, [])

  const updateBranding = useCallback((updates: Partial<PortalBranding>) => {
    setConfig(prev => ({
      ...prev,
      branding: { ...prev.branding, ...updates }
    }))
    setHasChanges(true)
  }, [])

  const saveConfig = useCallback(async () => {
    if (!companyId) {
      setError('Empresa não identificada')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      const apiPayload = mapFrontendToApi(config)
      
      const response = await fetch(
        `/api/backend-proxy/data-requests/config/collection-settings?company_id=${companyId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(apiPayload),
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to save config: ${response.status}`)
      }

      setOriginalConfig(config)
      setHasChanges(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar configurações')
      throw err
    } finally {
      setIsSaving(false)
    }
  }, [companyId, config])

  const resetConfig = useCallback(() => {
    setConfig(originalConfig)
    setHasChanges(false)
    setError(null)
  }, [originalConfig])

  const resetToDefaults = useCallback(() => {
    const defaultConfig = getDefaultConfig()
    setConfig(defaultConfig)
    setOriginalConfig(defaultConfig)
    setHasChanges(false)
    setError(null)
  }, [])

  const refetch = useCallback(() => {
    return loadConfig()
  }, [loadConfig])

  return {
    config,
    hasChanges,
    isSaving,
    isLoading,
    error,
    updateGeneralConfig,
    updateCollectionMessages,
    updateLgpdConfig,
    toggleFieldEnabled,
    addCustomField,
    removeCustomField,
    updateStageConfig,
    toggleStageField,
    updateBranding,
    saveConfig,
    resetConfig,
    resetToDefaults,
    refetch,
  }
}
