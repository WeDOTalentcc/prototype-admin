import { useState } from "react"
import { useDataRequestConfig } from "@/hooks/company/use-data-request-config"

export function useDataRequestTabState(companyId: string) {
  const configHook = useDataRequestConfig(companyId)

  const [isEditing, setIsEditing] = useState(false)
  const [newFieldName, setNewFieldName] = useState("")
  const [newFieldType, setNewFieldType] = useState<'text' | 'email' | 'phone' | 'date' | 'file' | 'textarea'>('text')
  const [showAddField, setShowAddField] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    general: true,
    collection: true,
    lgpd: true,
    fields: true,
    branding: false,
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const handleAddField = () => {
    if (newFieldName.trim()) {
      configHook.addCustomField({
        name: newFieldName.toLowerCase().replace(/\s+/g, '_'),
        displayName: newFieldName,
        type: newFieldType,
        required: false,
        enabled: true,
      })
      setNewFieldName("")
      setNewFieldType('text')
      setShowAddField(false)
    }
  }

  const handleStartEditing = () => setIsEditing(true)

  const handleCancelEditing = () => {
    configHook.resetConfig()
    setIsEditing(false)
    setShowAddField(false)
  }

  const handleSaveChanges = async () => {
    await configHook.saveConfig()
    setIsEditing(false)
  }

  const generateLiaSuggestion = (type: 'welcome' | 'thankYou') => {
    if (type === 'welcome') {
      configHook.updateBranding({
        welcomeMessage: 'Olá! 👋 Estamos muito felizes em ter você em nosso processo seletivo. Para dar continuidade, precisamos de algumas informações adicionais. Fique tranquilo, seus dados estão protegidos de acordo com a LGPD.'
      })
    } else {
      configHook.updateBranding({
        thankYouMessage: 'Perfeito! ✅ Recebemos todas as suas informações com sucesso. Nossa equipe irá analisar e entraremos em contato em breve com os próximos passos. Enquanto isso, fique à vontade para nos contatar se tiver alguma dúvida.'
      })
    }
  }

  const enabledFields = configHook.config.fields.filter(f => f.enabled)
  const defaultFields = configHook.config.fields.filter(f => f.isDefault)
  const customFields = configHook.config.fields.filter(f => !f.isDefault)

  return {
    ...configHook,
    isEditing,
    newFieldName,
    setNewFieldName,
    newFieldType,
    setNewFieldType,
    showAddField,
    setShowAddField,
    expandedSections,
    toggleSection,
    handleAddField,
    handleStartEditing,
    handleCancelEditing,
    handleSaveChanges,
    generateLiaSuggestion,
    enabledFields,
    defaultFields,
    customFields,
  }
}

export type DataRequestTabState = ReturnType<typeof useDataRequestTabState>
