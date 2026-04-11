"use client"

import { useState, useEffect, useImperativeHandle } from "react"
import { getGlobalSearchSettings, updateGlobalSearchSettings } from "@/lib/api/global-search-settings"

export interface GlobalSearchSettings {
  defaultLimit: number
  searchType: 'fast' | 'pro'
  showEmails: boolean
  showPhoneNumbers: boolean
  highFreshness: boolean
  autoExpandGlobal: boolean
  confirmBeforeSearch: boolean
  globalSearchEnabled: boolean
}

export interface LimitOption {
  value: number
  label: string
  description: string
  estimatedCredits: {
    fast: number
    pro: number
  }
  recommended?: boolean
}

export const limitOptions: LimitOption[] = [
  {
    value: 50,
    label: "50 candidatos",
    description: "Ideal para buscas exploratórias e vagas específicas",
    estimatedCredits: { fast: 50, pro: 350 },
    recommended: true
  },
  {
    value: 100,
    label: "100 candidatos",
    description: "Bom para vagas com alta demanda de candidatos",
    estimatedCredits: { fast: 100, pro: 700 }
  },
  {
    value: 150,
    label: "150 candidatos",
    description: "Para processos seletivos de grande volume",
    estimatedCredits: { fast: 150, pro: 1050 }
  },
  {
    value: 200,
    label: "200 candidatos",
    description: "Máximo recomendado - projetos de sourcing massivo",
    estimatedCredits: { fast: 200, pro: 1400 }
  }
]

const defaultSettings: GlobalSearchSettings = {
  defaultLimit: 50,
  searchType: 'fast',
  showEmails: false,
  showPhoneNumbers: false,
  highFreshness: false,
  autoExpandGlobal: false,
  confirmBeforeSearch: true,
  globalSearchEnabled: true
}

export interface GlobalSearchHubRef {
  save: () => Promise<void>
  cancel: () => void
  hasChanges: boolean
}

export function useGlobalSearchHub(
  activeSubsection?: string,
  onChangesUpdate?: (hasChanges: boolean) => void,
  ref?: React.Ref<GlobalSearchHubRef>
) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'limits')
  const [settings, setSettings] = useState<GlobalSearchSettings>(defaultSettings)
  const [originalSettings, setOriginalSettings] = useState<GlobalSearchSettings>(defaultSettings)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const [isEditingLimits, setIsEditingLimits] = useState(false)
  const [isEditingOptions, setIsEditingOptions] = useState(false)

  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await getGlobalSearchSettings()
        const mapped: GlobalSearchSettings = {
          defaultLimit: data.default_limit,
          searchType: data.search_type,
          showEmails: data.show_emails,
          showPhoneNumbers: data.show_phone_numbers,
          highFreshness: data.high_freshness,
          autoExpandGlobal: data.auto_expand_global,
          confirmBeforeSearch: data.confirm_before_search,
          globalSearchEnabled: data.global_search_enabled ?? true
        }
        setSettings(mapped)
        setOriginalSettings(mapped)
      } catch (e) {
      }
      setLoading(false)
    }
    loadSettings()
  }, [])

  useEffect(() => {
    onChangesUpdate?.(hasChanges)
  }, [hasChanges, onChangesUpdate])

  const handleSettingChange = (key: keyof GlobalSearchSettings, value: unknown) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
    setSuccessMessage(null)
    setErrorMessage(null)
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleSave = async () => {
    setSaving(true)
    setErrorMessage(null)
    try {
      await updateGlobalSearchSettings({
        default_limit: settings.defaultLimit,
        search_type: settings.searchType,
        show_emails: settings.showEmails,
        show_phone_numbers: settings.showPhoneNumbers,
        high_freshness: settings.highFreshness,
        auto_expand_global: settings.autoExpandGlobal,
        confirm_before_search: settings.confirmBeforeSearch,
        global_search_enabled: settings.globalSearchEnabled
      })

      setOriginalSettings(settings)
      setSuccessMessage('Configurações salvas com sucesso!')
      setHasChanges(false)
      setIsEditingLimits(false)
      setIsEditingOptions(false)

      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (error) {
      setErrorMessage('Erro ao salvar configurações. Tente novamente.')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setSaving(false)
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleCancel = () => {
    setSettings(originalSettings)
    setHasChanges(false)
    setIsEditingLimits(false)
    setIsEditingOptions(false)
    setSuccessMessage(null)
    setErrorMessage(null)
  }

  const handleCancelLimits = () => {
    setSettings(prev => ({ ...prev, defaultLimit: originalSettings.defaultLimit }))
    setIsEditingLimits(false)
    const hasOtherChanges =
      settings.searchType !== originalSettings.searchType ||
      settings.showEmails !== originalSettings.showEmails ||
      settings.showPhoneNumbers !== originalSettings.showPhoneNumbers ||
      settings.highFreshness !== originalSettings.highFreshness ||
      settings.autoExpandGlobal !== originalSettings.autoExpandGlobal ||
      settings.confirmBeforeSearch !== originalSettings.confirmBeforeSearch ||
      settings.globalSearchEnabled !== originalSettings.globalSearchEnabled
    if (!hasOtherChanges) setHasChanges(false)
  }

  const handleCancelOptions = () => {
    setSettings(prev => ({
      ...prev,
      showEmails: originalSettings.showEmails,
      showPhoneNumbers: originalSettings.showPhoneNumbers,
      highFreshness: originalSettings.highFreshness,
      confirmBeforeSearch: originalSettings.confirmBeforeSearch,
      autoExpandGlobal: originalSettings.autoExpandGlobal
    }))
    setIsEditingOptions(false)
    const hasOtherChanges =
      settings.defaultLimit !== originalSettings.defaultLimit ||
      settings.searchType !== originalSettings.searchType ||
      settings.globalSearchEnabled !== originalSettings.globalSearchEnabled
    if (!hasOtherChanges) setHasChanges(false)
  }

  useImperativeHandle(ref, () => ({
    save: handleSave,
    cancel: handleCancel,
    hasChanges
  }), [handleSave, handleCancel, hasChanges])

  const selectedLimit = limitOptions.find(o => o.value === settings.defaultLimit) || limitOptions[0]
  const estimatedCreditsPerSearch = settings.searchType === 'fast'
    ? selectedLimit.estimatedCredits.fast
    : selectedLimit.estimatedCredits.pro

  return {
    activeTab, setActiveTab,
    settings, handleSettingChange,
    loading, saving,
    hasChanges, successMessage, errorMessage,
    isEditingLimits, setIsEditingLimits,
    isEditingOptions, setIsEditingOptions,
    handleSave, handleCancel,
    handleCancelLimits, handleCancelOptions,
    selectedLimit, estimatedCreditsPerSearch,
  }
}
