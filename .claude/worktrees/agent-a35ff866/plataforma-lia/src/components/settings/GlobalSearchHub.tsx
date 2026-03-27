"use client"

import React, { useState, useEffect, forwardRef, useImperativeHandle } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Globe, Zap, Save, CheckCircle, AlertCircle, Info,
  Brain, Loader2, DollarSign, Users, Search,
  TrendingUp, Shield, Clock, Settings, HelpCircle, Pencil
} from "lucide-react"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { getGlobalSearchSettings, updateGlobalSearchSettings } from "@/lib/api/global-search-settings"
import { textStyles, cardStyles, badgeStyles, tabStyles, actionButtonStyles } from '@/lib/design-tokens'

interface GlobalSearchSettings {
  defaultLimit: number
  searchType: 'fast' | 'pro'
  showEmails: boolean
  showPhoneNumbers: boolean
  highFreshness: boolean
  autoExpandGlobal: boolean
  confirmBeforeSearch: boolean
  globalSearchEnabled: boolean
}

interface LimitOption {
  value: number
  label: string
  description: string
  estimatedCredits: {
    fast: number
    pro: number
  }
  recommended?: boolean
}

const limitOptions: LimitOption[] = [
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

export interface GlobalSearchHubRef {
  save: () => Promise<void>
  cancel: () => void
  hasChanges: boolean
}

interface GlobalSearchHubProps {
  activeSubsection?: string
  onChangesUpdate?: (hasChanges: boolean) => void
}

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

export const GlobalSearchHub = forwardRef<GlobalSearchHubRef, GlobalSearchHubProps>(
  function GlobalSearchHub({ activeSubsection, onChangesUpdate }, ref) {
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
        console.error('Error loading settings from API:', e)
      }
      setLoading(false)
    }
    loadSettings()
  }, [])

  useEffect(() => {
    onChangesUpdate?.(hasChanges)
  }, [hasChanges, onChangesUpdate])

  const handleSettingChange = (key: keyof GlobalSearchSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
    setSuccessMessage(null)
    setErrorMessage(null)
  }

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
      console.error('Error saving settings:', error)
      setErrorMessage('Erro ao salvar configurações. Tente novamente.')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setSaving(false)
    }
  }

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-4 h-4 animate-spin text-gray-600 dark:text-gray-400" />
      </div>
    )
  }

  const tabs = [
    { id: 'limits', label: 'Limites', icon: Users },
    { id: 'options', label: 'Opções', icon: Settings },
    { id: 'costs', label: 'Custos', icon: DollarSign }
  ]

  return (
    <div className="space-y-3">
      {/* Master Toggle - Habilitar/Desabilitar Busca Global */}
      <Card className="border-gray-200/50 dark:border-gray-700/50 mb-3">
        <CardContent className="pt-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-0.5">
              <Switch
                checked={settings.globalSearchEnabled}
                onCheckedChange={(checked: boolean) => handleSettingChange('globalSearchEnabled', checked)}
              />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1.5">
                <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="font-['Open_Sans',sans-serif] text-[13px] font-semibold text-gray-900 dark:text-gray-50">
                  Habilitar Busca Global
                </span>
                {settings.globalSearchEnabled ? (
                  <Badge className="bg-green-100 text-green-700 text-[11px]">Ativo</Badge>
                ) : (
                  <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 text-[11px]">Desativado</Badge>
                )}
              </div>
              <p className="text-[11px] text-gray-600 dark:text-gray-400 mb-2">
                Controla o acesso à busca global de candidatos em toda a plataforma.
              </p>
              
              {/* Detailed explanation */}
              <div className={`p-3 rounded-md border ${settings.globalSearchEnabled ? 'bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800' : 'bg-amber-50 border-amber-100 dark:bg-amber-900/20 dark:border-amber-800'}`}>
                <div className="flex items-start gap-1.5">
                  <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600 dark:text-gray-400" />
                  <div className="text-[10px] text-gray-800 dark:text-gray-200 space-y-1.5">
                    {settings.globalSearchEnabled ? (
                      <>
                        <p className="font-medium">Quando habilitado, você tem acesso a:</p>
                        <ul className="list-disc list-inside space-y-1 ml-1">
                          <li><strong>Funil de Talentos:</strong> Opções de busca "Híbrida" e "Global" no prompt de busca</li>
                          <li><strong>Resultados de Busca:</strong> Ícones de expansão global e híbrida no prompt expandido</li>
                          <li><strong>Criação de Vaga:</strong> LIA pode buscar candidatos externos para calibração e sourcing</li>
                          <li><strong>Sourcing Automático:</strong> Expansão para base global quando banco local é insuficiente</li>
                          <li><strong>Revelação de Contatos:</strong> Opção de revelar emails e telefones (consome créditos)</li>
                        </ul>
                      </>
                    ) : (
                      <>
                        <p className="font-medium">Quando desabilitado:</p>
                        <ul className="list-disc list-inside space-y-1 ml-1">
                          <li><strong>Funil de Talentos:</strong> Apenas busca "Local" disponível (base própria)</li>
                          <li><strong>Resultados de Busca:</strong> Ícones de busca global/híbrida serão ocultados</li>
                          <li><strong>Criação de Vaga:</strong> LIA usará apenas candidatos da sua base para calibração</li>
                          <li><strong>Sourcing Automático:</strong> Desabilitado - sem expansão para base externa</li>
                          <li><strong>Economia:</strong> Nenhum crédito de busca global será consumido</li>
                        </ul>
                        <p className="mt-2 text-amber-700 dark:text-amber-400 font-medium">
                          Você pode reativar a busca global a qualquer momento.
                        </p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className={!settings.globalSearchEnabled ? 'opacity-50 pointer-events-none' : ''}>
      <div className={tabStyles.pillContainer}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'limits' && (
        <div className="space-y-3">
          <Card className="border-gray-200/50 dark:border-gray-700/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="font-['Open_Sans',sans-serif] text-[13px] font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-50">
                  <Users className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  Limite de Candidatos por Busca Global
                </CardTitle>
                {!isEditingLimits ? (
                  <button
                    onClick={() => setIsEditingLimits(true)}
                    className={actionButtonStyles.smOutline}
                  >
                    <Pencil className={actionButtonStyles.icon} />
                    Editar
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCancelLimits}
                      disabled={saving}
                      className={actionButtonStyles.smSecondary}
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className={actionButtonStyles.smPrimary}
                    >
                      {saving ? (
                        <>
                          <Loader2 className={`${actionButtonStyles.icon} animate-spin`} />
                          Salvando...
                        </>
                      ) : (
                        <>
                          <Save className={actionButtonStyles.icon} />
                          Salvar Alterações
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-3">
              <RadioGroup
                value={settings.defaultLimit.toString()}
                onValueChange={(value) => handleSettingChange('defaultLimit', parseInt(value))}
                className="space-y-2"
                disabled={!isEditingLimits}
              >
                {limitOptions.map((option) => (
                  <div
                    key={option.value}
                    className={`relative flex items-start p-3 rounded-md border-2 transition-all ${
                      isEditingLimits ? 'cursor-pointer' : 'cursor-default'
                    } ${
                      settings.defaultLimit === option.value
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800/50'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    } ${!isEditingLimits ? 'opacity-75' : ''}`}
                    onClick={() => isEditingLimits && handleSettingChange('defaultLimit', option.value)}
                  >
                    <RadioGroupItem
                      value={option.value.toString()}
                      id={`limit-${option.value}`}
                      className="mt-0.5"
                      disabled={!isEditingLimits}
                    />
                    <div className="ml-2 flex-1">
                      <div className="flex items-center gap-2">
                        <Label
                          htmlFor={`limit-${option.value}`}
                          className={`text-xs font-medium text-gray-950 dark:text-gray-50 ${isEditingLimits ? 'cursor-pointer' : 'cursor-default'}`}
                        >
                          {option.label}
                        </Label>
                        {option.recommended && (
                          <Badge className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-[10px] px-1.5 py-0.5">
                            Recomendado
                          </Badge>
                        )}
                      </div>
                      <p className="text-[10px] text-gray-800 dark:text-gray-200 mt-0.5">
                        {option.description}
                      </p>
                    </div>
                    <div className="text-right ml-3">
                      <div className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                        ~{option.estimatedCredits.fast} créditos
                      </div>
                      <div className="text-[10px] text-gray-800 dark:text-gray-200">
                        estimativa
                      </div>
                    </div>
                  </div>
                ))}
              </RadioGroup>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'options' && (
        <div className="space-y-3">
          <Card className="border-gray-200/50 dark:border-gray-700/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="font-['Open_Sans',sans-serif] text-[13px] font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-50">
                  <Settings className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  Opções de Busca
                </CardTitle>
                {!isEditingOptions ? (
                  <button
                    onClick={() => setIsEditingOptions(true)}
                    className={actionButtonStyles.smOutline}
                  >
                    <Pencil className={actionButtonStyles.icon} />
                    Editar
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCancelOptions}
                      disabled={saving}
                      className={actionButtonStyles.smSecondary}
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className={actionButtonStyles.smPrimary}
                    >
                      {saving ? (
                        <>
                          <Loader2 className={`${actionButtonStyles.icon} animate-spin`} />
                          Salvando...
                        </>
                      ) : (
                        <>
                          <Save className={actionButtonStyles.icon} />
                          Salvar Alterações
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-3 space-y-2">
              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-gray-100 dark:border-gray-800 ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-gray-950 dark:text-gray-50">
                    Revelar emails automaticamente
                  </div>
                  <div className="text-[10px] text-gray-800 dark:text-gray-200">
                    +2 créditos por candidato com email revelado
                  </div>
                </div>
                <Switch
                  checked={settings.showEmails}
                  onCheckedChange={(checked: boolean) => handleSettingChange('showEmails', checked)}
                  disabled={!isEditingOptions}
                />
              </div>

              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-gray-100 dark:border-gray-800 ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-gray-950 dark:text-gray-50">
                    Revelar telefones automaticamente
                  </div>
                  <div className="text-[10px] text-gray-800 dark:text-gray-200">
                    +14 créditos por candidato com telefone revelado
                  </div>
                </div>
                <Switch
                  checked={settings.showPhoneNumbers}
                  onCheckedChange={(checked: boolean) => handleSettingChange('showPhoneNumbers', checked)}
                  disabled={!isEditingOptions}
                />
              </div>

              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-gray-100 dark:border-gray-800 ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-gray-950 dark:text-gray-50">
                    Priorizar perfis atualizados recentemente
                  </div>
                  <div className="text-[10px] text-gray-800 dark:text-gray-200">
                    Candidatos ativos nos últimos 90 dias
                  </div>
                </div>
                <Switch
                  checked={settings.highFreshness}
                  onCheckedChange={(checked: boolean) => handleSettingChange('highFreshness', checked)}
                  disabled={!isEditingOptions}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="border-gray-200/50 dark:border-gray-700/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-[13px] font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-50">
                <Shield className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Controle de Gastos
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3 space-y-2">
              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-gray-100 dark:border-gray-800 ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-gray-950 dark:text-gray-50">
                    Confirmar antes de cada busca global
                  </div>
                  <div className="text-[10px] text-gray-800 dark:text-gray-200">
                    Exibe estimativa de créditos antes de executar
                  </div>
                </div>
                <Switch
                  checked={settings.confirmBeforeSearch}
                  onCheckedChange={(checked: boolean) => handleSettingChange('confirmBeforeSearch', checked)}
                  disabled={!isEditingOptions}
                />
              </div>

              <div className={`flex items-center justify-between gap-4 py-1.5 ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-gray-950 dark:text-gray-50">
                    Sugerir expansão global automaticamente
                  </div>
                  <div className="text-[10px] text-gray-800 dark:text-gray-200">
                    Quando busca local retorna poucos resultados
                  </div>
                </div>
                <Switch
                  checked={settings.autoExpandGlobal}
                  onCheckedChange={(checked: boolean) => handleSettingChange('autoExpandGlobal', checked)}
                  disabled={!isEditingOptions}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'costs' && (
        <div className="space-y-3">
          <Card className="border-gray-200/50 dark:border-gray-700/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-[13px] font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-50">
                <DollarSign className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Tabela de Custos da Busca Global
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3">
              <div className="overflow-hidden rounded-md border border-gray-200 dark:border-gray-700">
                <table className="w-full text-[11px]">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-2 py-1.5 text-left text-[11px] font-medium text-gray-600 dark:text-gray-300">
                        Limite
                      </th>
                      <th className="px-2 py-1.5 text-center text-[11px] font-medium text-gray-600 dark:text-gray-300">
                        Créditos Estimados
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {limitOptions.map((option, idx) => (
                      <tr 
                        key={option.value}
                        className={`${
                          settings.defaultLimit === option.value 
                            ? 'bg-gray-100 dark:bg-gray-800/50' 
 : idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50 dark:bg-gray-800/50'
                        }`}
                      >
                        <td className="px-2 py-1.5">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[11px] font-medium text-gray-950 dark:text-gray-50">
                              {option.label}
                            </span>
                            {settings.defaultLimit === option.value && (
                              <Badge className="bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 text-[10px] px-1.5">
                                Atual
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="px-2 py-1.5 text-center">
                          <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-300">
                            ~{option.estimatedCredits.fast} créditos
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-md">
                <div className="flex items-start gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                  <div className="text-[10px] text-amber-700 dark:text-amber-300">
                    <strong>Nota:</strong> Os custos são estimativas baseadas no limite configurado. 
                    O custo real pode variar dependendo dos filtros aplicados e disponibilidade de candidatos.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detalhamento de Custos por Campo */}
          <Card className="border-gray-200/50 dark:border-gray-700/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-[13px] font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-50">
                <Zap className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Detalhamento de Custos por Opção
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3">
              {/* Custo Estimado - como mostra no modal */}
              <div className="p-4 rounded-md border bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    <span className="font-medium text-xs">Custo Estimado</span>
                  </div>
                  <Badge variant="outline" className="text-[11px] px-1.5 py-0.5 border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300">
                    Tempo Real
                  </Badge>
                </div>
                
                <div className="flex items-end justify-between mb-3">
                  <div>
                    <div className="text-base font-bold text-gray-900 dark:text-gray-50">
                      1-3
                    </div>
                    <div className="text-[11px] text-gray-600 dark:text-gray-400">
                      créditos por candidato
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-xs">
                      {settings.defaultLimit}-{settings.defaultLimit * 3}
                    </div>
                    <div className="text-[11px] text-gray-600 dark:text-gray-400">
                      total ({settings.defaultLimit} candidatos)
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-200 dark:border-gray-700 pt-3 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600 dark:text-gray-400">
                      Base (Busca Rápida)
                    </span>
                    <span className="font-medium">1</span>
                  </div>
                  <div className="flex justify-between text-xs pt-1.5 border-t border-gray-200 dark:border-gray-700">
                    <span className="flex items-center gap-1 font-medium text-gray-800 dark:text-gray-200">
                      <TrendingUp className="w-3 h-3" />
                      Total Base por Candidato
                    </span>
                    <span className="font-bold text-gray-900 dark:text-gray-50">
                      1
                    </span>
                  </div>
                </div>
              </div>

              {/* Tabela de custos adicionais por opção */}
              <div className="overflow-hidden rounded-md border border-gray-200 dark:border-gray-700">
                <table className="w-full text-[11px]">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-3 py-2 text-left text-[11px] font-medium text-gray-600 dark:text-gray-300">
                        Opção / Campo
                      </th>
                      <th className="px-3 py-2 text-left text-[11px] font-medium text-gray-600 dark:text-gray-300">
                        Seção
                      </th>
                      <th className="px-3 py-2 text-center text-[11px] font-medium text-gray-600 dark:text-gray-300">
                        Custo Adicional
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {/* Custo Base */}
                    <tr className="bg-gray-100 dark:bg-gray-800/50">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Busca Global / Híbrida</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Origem da Busca</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[10px]">
                          1 crédito/cand.
                        </Badge>
                      </td>
                    </tr>

                    {/* Dados Atualizados */}
                    <tr className="bg-white dark:bg-gray-900">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Dados Atualizados (High Freshness)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Opções de Qualidade</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[10px]">
                          +2 créditos
                        </Badge>
                      </td>
                    </tr>

                    {/* Apenas com Email */}
                    <tr className="bg-white dark:bg-gray-900">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Search className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Apenas com Email (filtro)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-[10px]">
                          +1 crédito
                        </Badge>
                      </td>
                    </tr>

                    {/* Mostrar Emails */}
                    <tr className="bg-gray-50/50 dark:bg-gray-800/50">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Shield className="w-3.5 h-3.5 text-green-500" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Mostrar Emails (revelar)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-green-100 text-green-700 text-[10px]">
                          +2 créditos
                        </Badge>
                      </td>
                    </tr>

                    {/* Apenas com Telefone */}
                    <tr className="bg-white dark:bg-gray-900">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Search className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Apenas com Telefone (filtro)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-[10px]">
                          +1 crédito
                        </Badge>
                      </td>
                    </tr>

                    {/* Mostrar Telefones - CUSTO ALTO */}
                    <tr className="bg-amber-50/50 dark:bg-amber-900/20">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Mostrar Telefones (revelar)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-amber-100 text-amber-700 text-[10px]">
                          +14 créditos
                        </Badge>
                      </td>
                    </tr>

                    {/* Email OU Telefone */}
                    <tr className="bg-white dark:bg-gray-900">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Search className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                          <span className="font-medium text-gray-950 dark:text-gray-50">Email OU Telefone (filtro)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-[10px]">
                          +1 crédito
                        </Badge>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Resumo de custos máximos */}
              <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                  <span className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Resumo de Custos</span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-2 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                    <div className="text-[10px] text-gray-500 dark:text-gray-400">Custo Mínimo</div>
                    <div className="text-sm font-bold text-green-600">1 crédito</div>
                    <div className="text-[9px] text-gray-400 dark:text-gray-500">por candidato</div>
                  </div>
                  <div className="p-2 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                    <div className="text-[10px] text-gray-500 dark:text-gray-400">Custo Típico</div>
                    <div className="text-sm font-bold text-gray-900 dark:text-gray-50">3-5 créditos</div>
                    <div className="text-[9px] text-gray-400 dark:text-gray-500">por candidato</div>
                  </div>
                  <div className="p-2 bg-white dark:bg-gray-900 rounded border border-amber-200 dark:border-amber-700">
                    <div className="text-[10px] text-gray-500 dark:text-gray-400">Custo Máximo</div>
                    <div className="text-sm font-bold text-amber-600">19 créditos</div>
                    <div className="text-[9px] text-gray-400 dark:text-gray-500">por candidato</div>
                  </div>
                </div>
                <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-2 text-center">
                  * O custo máximo inclui todas as opções habilitadas (Freshness + Emails + Telefones)
                </p>
              </div>

              {/* Aviso sobre busca local */}
              <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-md">
                <div className="flex items-start gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                  <div className="text-[10px] text-green-700 dark:text-green-300">
                    <strong>Busca Local é gratuita!</strong> Buscas na base local (candidatos já cadastrados) 
                    não consomem créditos. As opções acima são cobradas apenas em buscas Híbridas ou Globais.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-gray-200/50 dark:border-gray-700/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-[13px] font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-50">
                <TrendingUp className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Resumo da Configuração Atual
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md col-span-2">
                  <div className="text-[10px] text-gray-800 dark:text-gray-200 mb-0.5">
                    Limite por busca
                  </div>
                  <div className="text-[18px] font-bold text-gray-950 dark:text-gray-50">
                    {settings.defaultLimit}
                  </div>
                  <div className="text-[10px] text-gray-800 dark:text-gray-200">candidatos (~1 crédito/cand)</div>
                </div>
                <div className="p-3 bg-gray-100 dark:bg-gray-800/50 rounded-md col-span-2">
                  <div className="text-[10px] text-gray-800 dark:text-gray-200 mb-0.5">
                    Custo estimado por busca
                  </div>
                  <div className="text-[20px] font-bold text-gray-900 dark:text-gray-50">
                    ~{estimatedCreditsPerSearch} créditos
                  </div>
                  <div className="text-[10px] text-gray-600 dark:text-gray-400 mt-0.5">
                    {settings.showEmails && '+emails '}
                    {settings.showPhoneNumbers && '+telefones '}
                    {settings.highFreshness && '+freshness'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      </div>


      {successMessage && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-1.5 px-2 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-[11px] rounded-full">
            <CheckCircle className="w-3.5 h-3.5" />
            {successMessage}
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-1.5 px-2 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-[11px] rounded-full">
            <AlertCircle className="w-3.5 h-3.5" />
            {errorMessage}
          </div>
        </div>
      )}
    </div>
  )
})
