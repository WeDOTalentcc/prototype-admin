"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { Shield, Bell, Clock, AlertCircle } from "lucide-react"
import type { DataRequestConfig } from "@/hooks/use-data-request-config"

function MessageField({ label, value, isEditing, onChange, rows }: {
  label: string
  value: string
  isEditing: boolean
  onChange: (v: string) => void
  rows: number
}) {
  return (
    <div>
      <Label className="text-micro text-lia-text-secondary mb-1 block">{label}</Label>
      {isEditing ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
        />
      ) : (
        <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
          {value}
        </p>
      )}
    </div>
  )
}

interface GeneralSettingsProps {
  config: DataRequestConfig
  isEditing: boolean
  updateGeneralConfig: (updates: Record<string, unknown>) => void
}

export function GeneralSettingsContent({ config, isEditing, updateGeneralConfig }: GeneralSettingsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-lia-text-secondary" />
          <div>
            <Label className="text-xs font-medium text-lia-text-primary">OTP Obrigatório</Label>
            <p className="text-micro text-lia-text-secondary">Verificação por código</p>
          </div>
        </div>
        {isEditing ? (
          <Switch checked={config.otpRequired} onCheckedChange={(checked: boolean) => updateGeneralConfig({ otpRequired: checked })} />
        ) : (
          <Badge variant={config.otpRequired ? "default" : "secondary"} className="text-micro">{config.otpRequired ? 'Ativo' : 'Inativo'}</Badge>
        )}
      </div>

      <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
        <div className="flex items-center gap-2">
          <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
          <div>
            <Label className="text-xs font-medium text-lia-text-primary">Lembretes Automáticos</Label>
            <p className="text-micro text-lia-text-secondary">Enviar lembretes pendentes</p>
          </div>
        </div>
        {isEditing ? (
          <Switch checked={config.autoReminders} onCheckedChange={(checked: boolean) => updateGeneralConfig({ autoReminders: checked })} />
        ) : (
          <Badge variant={config.autoReminders ? "default" : "secondary"} className="text-micro">{config.autoReminders ? 'Ativo' : 'Inativo'}</Badge>
        )}
      </div>

      <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
          <Label className="text-xs font-medium text-lia-text-primary">Dias para Expiração</Label>
        </div>
        {isEditing ? (
          <Select value={config.expirationDays.toString()} onValueChange={(value) => updateGeneralConfig({ expirationDays: parseInt(value) })}>
            <SelectTrigger className="w-full h-8 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="3">3 dias</SelectItem>
              <SelectItem value="7">7 dias</SelectItem>
              <SelectItem value="14">14 dias</SelectItem>
              <SelectItem value="30">30 dias</SelectItem>
            </SelectContent>
          </Select>
        ) : (
          <p className="text-xs font-medium text-lia-text-primary">{config.expirationDays} dias</p>
        )}
      </div>

      {config.autoReminders && (
        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
          <div className="flex items-center gap-2 mb-2">
            <Bell className="w-3.5 h-3.5 text-lia-text-secondary" />
            <Label className="text-xs font-medium text-lia-text-primary">Enviar Lembrete Após</Label>
          </div>
          {isEditing ? (
            <Select value={config.reminderDays.toString()} onValueChange={(value) => updateGeneralConfig({ reminderDays: parseInt(value) })}>
              <SelectTrigger className="w-full h-8 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 dia</SelectItem>
                <SelectItem value="2">2 dias</SelectItem>
                <SelectItem value="3">3 dias</SelectItem>
                <SelectItem value="5">5 dias</SelectItem>
              </SelectContent>
            </Select>
          ) : (
            <p className="text-xs font-medium text-lia-text-primary">{config.reminderDays} dia(s)</p>
          )}
        </div>
      )}
    </div>
  )
}

interface LgpdSectionProps {
  config: DataRequestConfig
  isEditing: boolean
  updateLgpdConfig: (updates: Partial<DataRequestConfig['lgpd']>) => void
}

export function LgpdSectionContent({ config, isEditing, updateLgpdConfig }: LgpdSectionProps) {
  return (
    <div className="space-y-4">
      <div className="p-3 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-md">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
          <p className="text-micro text-status-warning dark:text-status-warning" aria-live="polite" aria-atomic="true">
            A Lei Geral de Proteção de Dados (Lei nº 13.709/2018) exige consentimento explícito do candidato antes da coleta de dados pessoais.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-xs font-medium text-lia-text-primary">Exigir Consentimento</Label>
            {isEditing ? (
              <Switch checked={config.lgpd.requireConsent} onCheckedChange={(checked: boolean) => updateLgpdConfig({ requireConsent: checked })} />
            ) : (
              <Badge variant={config.lgpd.requireConsent ? "default" : "secondary"} className="text-micro">{config.lgpd.requireConsent ? 'Obrigatório' : 'Desabilitado'}</Badge>
            )}
          </div>
          <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Candidato deve autorizar antes de enviar dados</p>
        </div>

        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-xs font-medium text-lia-text-primary">Permitir Exclusão</Label>
            {isEditing ? (
              <Switch checked={config.lgpd.allowDataDeletion} onCheckedChange={(checked: boolean) => updateLgpdConfig({ allowDataDeletion: checked })} />
            ) : (
              <Badge variant={config.lgpd.allowDataDeletion ? "default" : "secondary"} className="text-micro">{config.lgpd.allowDataDeletion ? 'Habilitado' : 'Desabilitado'}</Badge>
            )}
          </div>
          <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Candidato pode solicitar exclusão dos dados</p>
        </div>
      </div>

      <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
        <Label className="text-xs font-medium text-lia-text-primary mb-2 block">Retenção de Dados</Label>
        {isEditing ? (
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={config.lgpd.dataRetentionDays}
              onChange={(e) => updateLgpdConfig({ dataRetentionDays: parseInt(e.target.value) || 365 })}
              min={30}
              max={1825}
              className="w-20 px-2 py-1 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-primary"
            />
            <span className="text-micro text-lia-text-secondary">dias após término do processo</span>
          </div>
        ) : (
          <p className="text-xs text-lia-text-secondary">{config.lgpd.dataRetentionDays} dias após término do processo</p>
        )}
      </div>

      <MessageField label="Mensagem de Consentimento (WhatsApp)" value={config.lgpd.consentMessage} isEditing={isEditing} onChange={(v) => updateLgpdConfig({ consentMessage: v })} rows={4} />
      <MessageField label="Disclaimer (Portal)" value={config.lgpd.disclaimerText} isEditing={isEditing} onChange={(v) => updateLgpdConfig({ disclaimerText: v })} rows={3} />
    </div>
  )
}


// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function CollectionModelContent(_props: Record<string, any>) {
  return null
}
