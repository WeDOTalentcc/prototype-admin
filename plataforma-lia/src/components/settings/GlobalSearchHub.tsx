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
      <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
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
      <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50 mb-3">
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
                <Globe className="w-4 h-4 text-lia-text-secondary" />
                <span className="font-['Open_Sans',sans-serif] text-base-ui font-semibold text-lia-text-primary">
                  Habilitar Busca Global
                </span>
                {settings.globalSearchEnabled ? (
                  <Badge className="bg-status-success/15 text-status-success text-xs">Ativo</Badge>
                ) : (
                  <Badge className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-xs">Desativado</Badge>
                )}
              </div>
              <p className="text-xs text-lia-text-secondary mb-2" aria-live="polite" aria-atomic="true">
                Controla o acesso à busca global de candidatos em toda a plataforma.
              </p>
              
              {/* Detailed explanation */}
              <div className={`p-3 rounded-md border ${settings.globalSearchEnabled ? 'bg-lia-bg-secondary border-lia-border-subtle dark:bg-lia-bg-primary/20 dark:border-lia-border-strong' : 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/20 dark:border-status-warning/30'}`}>
                <div className="flex items-start gap-1.5">
                  <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                  <div className="text-micro text-lia-text-primary space-y-1.5">
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
                        <p className="mt-2 text-status-warning dark:text-status-warning font-medium">
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
          <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
                  <Users className="w-3.5 h-3.5 text-lia-text-secondary" />
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
                          <Loader2 className={`${actionButtonStyles.icon} animate-spin motion-reduce:animate-none`} />
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
                    className={`relative flex items-start p-3 rounded-md border-2 transition-colors motion-reduce:transition-none ${
                      isEditingLimits ? 'cursor-pointer' : 'cursor-default'
                    } ${
                      settings.defaultLimit === option.value
                        ? 'border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50'
                        : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default dark:hover:border-lia-border-medium'
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
                          className={`text-xs font-medium text-lia-text-primary ${isEditingLimits ? 'cursor-pointer' : 'cursor-default'}`}
                        >
                          {option.label}
                        </Label>
                        {option.recommended && (
                          <Badge className="bg-status-success/10 text-status-success dark:bg-status-success/30 dark:text-status-success text-micro px-1.5 py-0.5">
                            Recomendado
                          </Badge>
                        )}
                      </div>
                      <p className="text-micro text-lia-text-primary mt-0.5">
                        {option.description}
                      </p>
                    </div>
                    <div className="text-right ml-3">
                      <div className="text-xs font-semibold text-lia-text-primary">
                        ~{option.estimatedCredits.fast} créditos
                      </div>
                      <div className="text-micro text-lia-text-primary">
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
          <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
                  <Settings className="w-3.5 h-3.5 text-lia-text-secondary" />
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
                          <Loader2 className={`${actionButtonStyles.icon} animate-spin motion-reduce:animate-none`} />
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
              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-lia-border-subtle dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-lia-text-primary">
                    Revelar emails automaticamente
                  </div>
                  <div className="text-micro text-lia-text-primary">
                    +2 créditos por candidato com email revelado
                  </div>
                </div>
                <Switch
                  checked={settings.showEmails}
                  onCheckedChange={(checked: boolean) => handleSettingChange('showEmails', checked)}
                  disabled={!isEditingOptions}
                />
              </div>

              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-lia-border-subtle dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-lia-text-primary">
                    Revelar telefones automaticamente
                  </div>
                  <div className="text-micro text-lia-text-primary">
                    +14 créditos por candidato com telefone revelado
                  </div>
                </div>
                <Switch
                  checked={settings.showPhoneNumbers}
                  onCheckedChange={(checked: boolean) => handleSettingChange('showPhoneNumbers', checked)}
                  disabled={!isEditingOptions}
                />
              </div>

              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-lia-border-subtle dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-lia-text-primary">
                    Priorizar perfis atualizados recentemente
                  </div>
                  <div className="text-micro text-lia-text-primary">
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

          <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
                <Shield className="w-3.5 h-3.5 text-lia-text-secondary" />
                Controle de Gastos
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3 space-y-2">
              <div className={`flex items-center justify-between gap-4 py-1.5 border-b border-lia-border-subtle dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
                <div>
                  <div className="text-xs font-medium text-lia-text-primary">
                    Confirmar antes de cada busca global
                  </div>
                  <div className="text-micro text-lia-text-primary">
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
                  <div className="text-xs font-medium text-lia-text-primary">
                    Sugerir expansão global automaticamente
                  </div>
                  <div className="text-micro text-lia-text-primary">
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
          <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
                <DollarSign className="w-3.5 h-3.5 text-lia-text-secondary" />
                Tabela de Custos da Busca Global
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3">
              <div className="overflow-hidden rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                <table className="w-full text-xs">
                  <thead className="bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                    <tr>
                      <th className="px-2 py-1.5 text-left text-xs font-medium text-lia-text-secondary">
                        Limite
                      </th>
                      <th className="px-2 py-1.5 text-center text-xs font-medium text-lia-text-secondary">
                        Créditos Estimados
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                    {limitOptions.map((option, idx) => (
                      <tr 
                        key={option.value}
                        className={`${
                          settings.defaultLimit === option.value 
                            ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50' 
 : idx % 2 === 0 ? 'bg-lia-bg-primary' : 'bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50'
                        }`}
                      >
                        <td className="px-2 py-1.5">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-medium text-lia-text-primary">
                              {option.label}
                            </span>
                            {settings.defaultLimit === option.value && (
                              <Badge className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro px-1.5">
                                Atual
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="px-2 py-1.5 text-center">
                          <span className="text-xs font-semibold text-lia-text-primary">
                            ~{option.estimatedCredits.fast} créditos
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-3 p-3 bg-status-warning/10 dark:bg-status-warning/20 rounded-md">
                <div className="flex items-start gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-status-warning dark:text-status-warning mt-0.5 flex-shrink-0" />
                  <div className="text-micro text-status-warning dark:text-status-warning">
                    <strong>Nota:</strong> Os custos são estimativas baseadas no limite configurado. 
                    O custo real pode variar dependendo dos filtros aplicados e disponibilidade de candidatos.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detalhamento de Custos por Campo */}
          <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
                <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
                Detalhamento de Custos por Opção
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3">
              {/* Custo Estimado - como mostra no modal */}
              <div className="p-4 rounded-md border bg-lia-bg-secondary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle mb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span className="font-medium text-xs">Custo Estimado</span>
                  </div>
                  <Badge variant="outline" className="text-xs px-1.5 py-0.5 border-lia-border-default text-lia-text-primary dark:border-lia-border-default">
                    Tempo Real
                  </Badge>
                </div>
                
                <div className="flex items-end justify-between mb-3">
                  <div>
                    <div className="text-base font-bold text-lia-text-primary">
                      1-3
                    </div>
                    <div className="text-xs text-lia-text-secondary">
                      créditos por candidato
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-xs">
                      {settings.defaultLimit}-{settings.defaultLimit * 3}
                    </div>
                    <div className="text-xs text-lia-text-secondary">
                      total ({settings.defaultLimit} candidatos)
                    </div>
                  </div>
                </div>

                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-lia-text-secondary">
                      Base (Busca Rápida)
                    </span>
                    <span className="font-medium">1</span>
                  </div>
                  <div className="flex justify-between text-xs pt-1.5 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <span className="flex items-center gap-1 font-medium text-lia-text-primary">
                      <TrendingUp className="w-3 h-3" />
                      Total Base por Candidato
                    </span>
                    <span className="font-bold text-lia-text-primary">
                      1
                    </span>
                  </div>
                </div>
              </div>

              {/* Tabela de custos adicionais por opção */}
              <div className="overflow-hidden rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                <table className="w-full text-xs">
                  <thead className="bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-lia-text-secondary">
                        Opção / Campo
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-lia-text-secondary">
                        Seção
                      </th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-lia-text-secondary">
                        Custo Adicional
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                    {/* Custo Base */}
                    <tr className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
                          <span className="font-medium text-lia-text-primary">Busca Global / Híbrida</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Origem da Busca</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro">
                          1 crédito/cand.
                        </Badge>
                      </td>
                    </tr>

                    {/* Dados Atualizados */}
                    <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
                          <span className="font-medium text-lia-text-primary">Dados Atualizados (High Freshness)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Opções de Qualidade</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro">
                          +2 créditos
                        </Badge>
                      </td>
                    </tr>

                    {/* Apenas com Email */}
                    <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Search className="w-3.5 h-3.5 text-lia-text-secondary" />
                          <span className="font-medium text-lia-text-primary">Apenas com Email (filtro)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-lia-bg-tertiary text-lia-text-primary text-micro">
                          +1 crédito
                        </Badge>
                      </td>
                    </tr>

                    {/* Mostrar Emails */}
                    <tr className="bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Shield className="w-3.5 h-3.5 text-status-success" />
                          <span className="font-medium text-lia-text-primary">Mostrar Emails (revelar)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-status-success/15 text-status-success text-micro">
                          +2 créditos
                        </Badge>
                      </td>
                    </tr>

                    {/* Apenas com Telefone */}
                    <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Search className="w-3.5 h-3.5 text-lia-text-secondary" />
                          <span className="font-medium text-lia-text-primary">Apenas com Telefone (filtro)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-lia-bg-tertiary text-lia-text-primary text-micro">
                          +1 crédito
                        </Badge>
                      </td>
                    </tr>

                    {/* Mostrar Telefones - CUSTO ALTO */}
                    <tr className="bg-status-warning/10/50 dark:bg-status-warning/20">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
                          <span className="font-medium text-lia-text-primary">Mostrar Telefones (revelar)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-status-warning/15 text-status-warning text-micro">
                          +14 créditos
                        </Badge>
                      </td>
                    </tr>

                    {/* Email OU Telefone */}
                    <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Search className="w-3.5 h-3.5 text-lia-text-secondary" />
                          <span className="font-medium text-lia-text-primary">Email OU Telefone (filtro)</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                      <td className="px-3 py-2 text-center">
                        <Badge className="bg-lia-bg-tertiary text-lia-text-primary text-micro">
                          +1 crédito
                        </Badge>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Resumo de custos máximos */}
              <div className="mt-4 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="w-3.5 h-3.5 text-lia-text-secondary" />
                  <span className="text-xs font-medium text-lia-text-primary">Resumo de Custos</span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="text-micro text-lia-text-secondary">Custo Mínimo</div>
                    <div className="text-sm font-bold text-status-success">1 crédito</div>
                    <div className="text-micro text-lia-text-tertiary">por candidato</div>
                  </div>
                  <div className="p-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="text-micro text-lia-text-secondary">Custo Típico</div>
                    <div className="text-sm font-bold text-lia-text-primary">3-5 créditos</div>
                    <div className="text-micro text-lia-text-tertiary">por candidato</div>
                  </div>
                  <div className="p-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-md border border-status-warning/30 dark:border-status-warning/30">
                    <div className="text-micro text-lia-text-secondary">Custo Máximo</div>
                    <div className="text-sm font-bold text-status-warning">19 créditos</div>
                    <div className="text-micro text-lia-text-tertiary">por candidato</div>
                  </div>
                </div>
                <p className="text-micro text-lia-text-secondary mt-2 text-center">
                  * O custo máximo inclui todas as opções habilitadas (Freshness + Emails + Telefones)
                </p>
              </div>

              {/* Aviso sobre busca local */}
              <div className="mt-3 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                <div className="flex items-start gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success mt-0.5 flex-shrink-0" />
                  <div className="text-micro text-status-success dark:text-status-success">
                    <strong>Busca Local é gratuita!</strong> Buscas na base local (candidatos já cadastrados) 
                    não consomem créditos. As opções acima são cobradas apenas em buscas Híbridas ou Globais.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
            <CardHeader className="pb-2">
              <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
                <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
                Resumo da Configuração Atual
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md col-span-2">
                  <div className="text-micro text-lia-text-primary mb-0.5">
                    Limite por busca
                  </div>
                  <div className="text-lg font-bold text-lia-text-primary">
                    {settings.defaultLimit}
                  </div>
                  <div className="text-micro text-lia-text-primary">candidatos (~1 crédito/cand)</div>
                </div>
                <div className="p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50 rounded-md col-span-2">
                  <div className="text-micro text-lia-text-primary mb-0.5">
                    Custo estimado por busca
                  </div>
                  <div className="text-xl font-bold text-lia-text-primary">
                    ~{estimatedCreditsPerSearch} créditos
                  </div>
                  <div className="text-micro text-lia-text-secondary mt-0.5">
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
          <div className="flex items-center gap-1.5 px-2 py-1.5 bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success text-xs rounded-full">
            <CheckCircle className="w-3.5 h-3.5" />
            {successMessage}
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-1.5 px-2 py-1.5 bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error text-xs rounded-full">
            <AlertCircle className="w-3.5 h-3.5" />
            {errorMessage}
          </div>
        </div>
      )}
    </div>
  )
})
