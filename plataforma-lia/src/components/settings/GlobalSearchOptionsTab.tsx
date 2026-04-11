"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Settings, Shield, Save, Loader2, Pencil } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { actionButtonStyles } from '@/lib/design-tokens'
import type { GlobalSearchSettings } from "./useGlobalSearchSettings"

interface GlobalSearchOptionsTabProps {
  settings: GlobalSearchSettings
  isEditingOptions: boolean
  saving: boolean
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
  onSettingChange: (key: keyof GlobalSearchSettings, value: unknown) => void
}

export function GlobalSearchOptionsTab({
  settings,
  isEditingOptions,
  saving,
  onEdit,
  onCancel,
  onSave,
  onSettingChange,
}: GlobalSearchOptionsTabProps) {
  const editHeader = (
    <div className="flex items-center justify-between">
      <CardTitle className="font-['Open_Sans',sans-serif] text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
        <Settings className="w-3.5 h-3.5 text-lia-text-secondary" />
        Opções de Busca
      </CardTitle>
      {!isEditingOptions ? (
        <button
          onClick={onEdit}
          className={actionButtonStyles.smOutline}
        >
          <Pencil className={actionButtonStyles.icon} />
          Editar
        </button>
      ) : (
        <div className="flex items-center gap-2">
          <button
            onClick={onCancel}
            disabled={saving}
            className={actionButtonStyles.smSecondary}
          >
            Cancelar
          </button>
          <button
            onClick={onSave}
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
  )

  return (
    <div className="space-y-3">
      <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
        <CardHeader className="pb-2">
          {editHeader}
        </CardHeader>
        <CardContent className="pt-3 space-y-2">
          <div className={`flex items-center justify-between gap-4 py-1.5 dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
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
              onCheckedChange={(checked: boolean) => onSettingChange('showEmails', checked)}
              disabled={!isEditingOptions}
            />
          </div>

          <div className={`flex items-center justify-between gap-4 py-1.5 dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
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
              onCheckedChange={(checked: boolean) => onSettingChange('showPhoneNumbers', checked)}
              disabled={!isEditingOptions}
            />
          </div>

          <div className={`flex items-center justify-between gap-4 py-1.5 dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
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
              onCheckedChange={(checked: boolean) => onSettingChange('highFreshness', checked)}
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
          <div className={`flex items-center justify-between gap-4 py-1.5 dark:border-lia-border-strong ${!isEditingOptions ? 'opacity-75' : ''}`}>
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
              onCheckedChange={(checked: boolean) => onSettingChange('confirmBeforeSearch', checked)}
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
              onCheckedChange={(checked: boolean) => onSettingChange('autoExpandGlobal', checked)}
              disabled={!isEditingOptions}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
