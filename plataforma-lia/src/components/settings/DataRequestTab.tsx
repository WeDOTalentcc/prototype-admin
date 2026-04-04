"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  ClipboardList, Settings, FileText, Palette,
  Lightbulb, Shield, MessageSquare,
  ChevronDown, Pencil, X, Save
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Loader2, AlertCircle } from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import { useDataRequestTabState } from "./useDataRequestTabState"
import { GeneralSettingsContent, CollectionModelContent, LgpdSectionContent } from "./DataRequestConfigSections"
import { DataRequestFieldsSection, DataRequestBrandingSection } from "./DataRequestFieldsBrandingSection"

interface DataRequestTabProps {
  companyId?: string
}

const CollapsibleSection = ({
  id,
  title,
  icon: Icon,
  children,
  count,
  isExpanded,
  onToggle
}: {
  id: string
  title: string
  icon: React.ComponentType<{ className?: string }>
  children: React.ReactNode
  count?: number
  isExpanded: boolean
  onToggle: () => void
}) => (
  <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md overflow-hidden">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-lia-text-primary" />
        <span className={textStyles.subtitle}>{title}</span>
        {count !== undefined && (
          <Badge variant="outline" className="ml-1 text-micro">{count} itens</Badge>
        )}
      </div>
      <ChevronDown className={cn(
        "w-4 h-4 text-lia-text-secondary transition-transform duration-200",
        isExpanded && "rotate-180"
      )} />
    </button>
    {isExpanded && (
      <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-primary">
        {children}
      </div>
    )}
  </div>
)

export function DataRequestTab({ companyId = 'default' }: DataRequestTabProps) {
  const state = useDataRequestTabState(companyId)

  if (state.isLoading) {
    return (
      <div className="space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
        <Card className="border-0 rounded-md">
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-8 h-8 text-lia-text-primary animate-spin motion-reduce:animate-none" />
              <p className="text-xs text-lia-text-secondary">Carregando configurações...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {state.error && (
        <div className="flex items-center gap-2 p-3 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-md">
          <AlertCircle className="w-4 h-4 text-status-warning flex-shrink-0" />
          <p className="text-xs text-status-warning dark:text-status-warning">
            {state.error} - Usando configurações padrão.
          </p>
        </div>
      )}
      <Card className="border-0 rounded-md">
        <CardHeader className="pb-3 pt-4 px-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
                <ClipboardList className="w-4 h-4 text-lia-text-primary" />
                Solicitação de Dados
              </CardTitle>
              <p className={`mt-1 ${textStyles.description}`} aria-live="polite" aria-atomic="true">
                Configure como e quando solicitar informações adicionais dos candidatos.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {state.isEditing ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={state.handleCancelEditing}
                    disabled={state.isSaving}
                    className="h-8 text-xs px-3"
                  >
                    <X className="w-3.5 h-3.5 mr-1" />
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    onClick={state.handleSaveChanges}
                    disabled={state.isSaving || !state.hasChanges}
                    className="h-8 text-xs px-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active text-white"
                  >
                    <Save className="w-3.5 h-3.5 mr-1" />
                    {state.isSaving ? 'Salvando...' : 'Salvar Alterações'}
                  </Button>
                </>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={state.handleStartEditing}
                  className="h-8 text-xs px-3"
                >
                  <Pencil className="w-3.5 h-3.5 mr-1" />
                  Editar Configurações
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 px-4 pb-4">
          <div className="flex items-start gap-2 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
            <Lightbulb className="w-4 h-4 text-lia-text-primary mt-0.5 flex-shrink-0" />
            <div className={textStyles.description}>
              <p className={`mb-0.5 ${textStyles.subtitle}`}>
                Como Funciona
              </p>
              <p>
                Configure os campos que deseja solicitar. O sistema pode enviar solicitações <strong className="text-lia-text-primary">automaticamente</strong> ou <strong>manualmente</strong>.
              </p>
            </div>
          </div>

          <CollapsibleSection
            id="general"
            title="Configurações Gerais"
            icon={Settings}
            isExpanded={state.expandedSections.general}
            onToggle={() => state.toggleSection('general')}
          >
            <GeneralSettingsContent
              config={state.config}
              isEditing={state.isEditing}
              updateGeneralConfig={state.updateGeneralConfig}
            />
          </CollapsibleSection>

          <CollapsibleSection
            id="collection"
            title="Modelo de Coleta (WhatsApp)"
            icon={MessageSquare}
            isExpanded={state.expandedSections.collection}
            onToggle={() => state.toggleSection('collection')}
          >
            <CollectionModelContent
              config={state.config}
              isEditing={state.isEditing}
              updateGeneralConfig={state.updateGeneralConfig}
              updateCollectionMessages={state.updateCollectionMessages}
            />
          </CollapsibleSection>

          <CollapsibleSection
            id="lgpd"
            title="LGPD e Consentimento"
            icon={Shield}
            isExpanded={state.expandedSections.lgpd}
            onToggle={() => state.toggleSection('lgpd')}
          >
            <LgpdSectionContent
              config={state.config}
              isEditing={state.isEditing}
              updateLgpdConfig={state.updateLgpdConfig}
            />
          </CollapsibleSection>

          <CollapsibleSection
            id="fields"
            title="Campos Solicitados"
            icon={FileText}
            count={state.enabledFields.length}
            isExpanded={state.expandedSections.fields}
            onToggle={() => state.toggleSection('fields')}
          >
            <DataRequestFieldsSection
              isEditing={state.isEditing}
              fields={state.config.fields}
              showAddField={state.showAddField}
              setShowAddField={state.setShowAddField}
              newFieldName={state.newFieldName}
              setNewFieldName={state.setNewFieldName}
              newFieldType={state.newFieldType}
              setNewFieldType={state.setNewFieldType}
              handleAddField={state.handleAddField}
              toggleFieldEnabled={state.toggleFieldEnabled}
              removeCustomField={state.removeCustomField}
            />
          </CollapsibleSection>

          <CollapsibleSection
            id="branding"
            title="Branding do Portal"
            icon={Palette}
            isExpanded={state.expandedSections.branding}
            onToggle={() => state.toggleSection('branding')}
          >
            <DataRequestBrandingSection
              isEditing={state.isEditing}
              branding={state.config.branding}
              updateBranding={state.updateBranding}
            />
          </CollapsibleSection>
        </CardContent>
      </Card>
    </div>
  )
}

export default DataRequestTab
