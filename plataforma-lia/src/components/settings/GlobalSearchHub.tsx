"use client"

import React, { forwardRef, useImperativeHandle, useState } from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Globe, Info, Loader2, CheckCircle, AlertCircle } from"lucide-react"
import { Switch } from"@/components/ui/switch"
import { Users, Settings, DollarSign } from"lucide-react"
import { tabStyles } from '@/lib/design-tokens'
import { useGlobalSearchSettings } from"./useGlobalSearchSettings"
import { GlobalSearchLimitsTab } from"./GlobalSearchLimitsTab"
import { GlobalSearchOptionsTab } from"./GlobalSearchOptionsTab"
import { GlobalSearchCostsTab } from"./GlobalSearchCostsTab"

export interface GlobalSearchHubRef {
  save: () => Promise<void>
  cancel: () => void
  hasChanges: boolean
}

interface GlobalSearchHubProps {
  activeSubsection?: string
  onChangesUpdate?: (hasChanges: boolean) => void
}

export const GlobalSearchHub = forwardRef<GlobalSearchHubRef, GlobalSearchHubProps>(
  function GlobalSearchHub({ activeSubsection, onChangesUpdate }, ref) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'limits')

  const {
    settings,
    loading,
    saving,
    hasChanges,
    successMessage,
    errorMessage,
    isEditingLimits,
    setIsEditingLimits,
    isEditingOptions,
    setIsEditingOptions,
    estimatedCreditsPerSearch,
    handleSettingChange,
    handleSave,
    handleCancel,
    handleCancelLimits,
    handleCancelOptions,
  } = useGlobalSearchSettings(onChangesUpdate)

  useImperativeHandle(ref, () => ({
    save: handleSave,
    cancel: handleCancel,
    hasChanges
  }), [handleSave, handleCancel, hasChanges])

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
                <span className="text-base-ui font-semibold text-lia-text-primary">
                  Habilitar Busca Global
                </span>
                {settings.globalSearchEnabled ? (
                  <Chip variant="neutral" muted className="text-xs">Ativo</Chip>
                ) : (
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-xs">Desativado</Chip>
                )}
              </div>
              <p className="text-xs text-lia-text-secondary mb-2" aria-live="polite" aria-atomic="true">
                Controla o acesso à busca global de candidatos em toda a plataforma.
              </p>

              <div className={`p-3 rounded-md border ${settings.globalSearchEnabled ? 'bg-lia-bg-secondary border-lia-border-subtle dark:bg-lia-bg-primary/20 dark:border-lia-border-strong' : 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/20 dark:border-status-warning/30'}`}>
                <div className="flex items-start gap-1.5">
                  <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                  <div className="text-micro text-lia-text-primary space-y-1.5">
                    {settings.globalSearchEnabled ? (
                      <>
                        <p className="font-medium">Quando habilitado, você tem acesso a:</p>
                        <ul className="list-disc list-inside space-y-1 ml-1">
                          <li><strong>Funil de Talentos:</strong> Opções de busca"Híbrida" e"Global" no prompt de busca</li>
                          <li><strong>Resultados de Busca:</strong> Ícones de expansão global e híbrida no prompt expandido</li>
                          <li><strong>Criação de Vaga:</strong> LIA pode buscar candidatos externos para calibração e sourcing</li>
                          <li><strong>Sourcing Automático:</strong> Expansão para base global quando banco local é insuficiente</li>
                          <li><strong>Revelação de Contatos:</strong> Opção de revelar emails e telefones (1 crédito + $0.01 Apify/candidato)</li>
                        </ul>
                      </>
                    ) : (
                      <>
                        <p className="font-medium">Quando desabilitado:</p>
                        <ul className="list-disc list-inside space-y-1 ml-1">
                          <li><strong>Funil de Talentos:</strong> Apenas busca"Local" disponível (base própria)</li>
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
        <GlobalSearchLimitsTab
          settings={settings}
          isEditingLimits={isEditingLimits}
          saving={saving}
          onEdit={() => setIsEditingLimits(true)}
          onCancel={handleCancelLimits}
          onSave={handleSave}
          onSettingChange={handleSettingChange}
        />
      )}

      {activeTab === 'options' && (
        <GlobalSearchOptionsTab
          settings={settings}
          isEditingOptions={isEditingOptions}
          saving={saving}
          onEdit={() => setIsEditingOptions(true)}
          onCancel={handleCancelOptions}
          onSave={handleSave}
          onSettingChange={handleSettingChange}
        />
      )}

      {activeTab === 'costs' && (
        <GlobalSearchCostsTab
          settings={settings}
          estimatedCreditsPerSearch={estimatedCreditsPerSearch}
        />
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
