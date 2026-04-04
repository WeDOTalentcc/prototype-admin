"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, Save, Loader2, Pencil } from "lucide-react"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { actionButtonStyles } from '@/lib/design-tokens'
import { limitOptions, type GlobalSearchSettings } from "./useGlobalSearchSettings"

interface GlobalSearchLimitsTabProps {
  settings: GlobalSearchSettings
  isEditingLimits: boolean
  saving: boolean
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
  onSettingChange: (key: keyof GlobalSearchSettings, value: unknown) => void
}

export function GlobalSearchLimitsTab({
  settings,
  isEditingLimits,
  saving,
  onEdit,
  onCancel,
  onSave,
  onSettingChange,
}: GlobalSearchLimitsTabProps) {
  return (
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
        </CardHeader>
        <CardContent className="pt-3">
          <RadioGroup
            value={settings.defaultLimit.toString()}
            onValueChange={(value) => onSettingChange('defaultLimit', parseInt(value))}
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
                onClick={() => isEditingLimits && onSettingChange('defaultLimit', option.value)}
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
  )
}
