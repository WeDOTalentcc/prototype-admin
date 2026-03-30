"use client"

import React from "react"
import {
  useSortable,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Card } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  GripVertical, Trash2, Check, X, Lock, Clock, Shield, Settings,
  ChevronDown, ChevronRight, Star, Loader2, Gauge,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useSubStatusPanel } from "@/hooks/use-sub-status-panel"
import type { RecruitmentStage, SubStatus, StageDataField } from "./recruitment-journey.types"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function getTypeBadge(type: RecruitmentStage['type']) {
  switch (type) {
    case 'system':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-200 lia-text-600 text-micro font-medium">
          <Lock className="h-3 w-3" />
          Sistema
        </span>
      )
    case 'default':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary text-micro font-medium">
          <Shield className="h-3 w-3" />
          Padrão
        </span>
      )
    case 'custom':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary text-micro font-medium">
          <Settings className="h-3 w-3" />
          Custom
        </span>
      )
  }
}

const ACTION_BEHAVIOR_LABELS: Record<string, string> = {
  intake: "Entrada", screening: "Triagem WSI", scheduling: "Agendamento",
  evaluation: "Avaliação", verification: "Verificação", offer: "Proposta",
  passive: "Passivo", conclusion_hired: "Contratação",
  conclusion_rejected: "Reprovação", conclusion_declined: "Proposta Recusada",
}

const ACTION_BEHAVIOR_SHORT: Record<string, string> = {
  intake: "Entrada", screening: "Triagem", scheduling: "Agend.",
  evaluation: "Aval.", verification: "Verif.", offer: "Proposta",
  passive: "Passivo", conclusion_hired: "Contrat.",
  conclusion_rejected: "Reprov.", conclusion_declined: "Recusada",
}

export function getActionBehaviorLabel(behavior?: string): string | null {
  return behavior ? (ACTION_BEHAVIOR_LABELS[behavior] || null) : null
}

export function getActionBehaviorShort(behavior?: string): string | null {
  return behavior ? (ACTION_BEHAVIOR_SHORT[behavior] || null) : null
}

export function ActionBehaviorBadge({ behavior }: { behavior?: string }) {
  const label = getActionBehaviorLabel(behavior)
  if (!label) return null
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium bg-wedo-cyan/15 text-wedo-cyan">
      {label}
    </span>
  )
}

export function getStageDisplayName(stage: RecruitmentStage): string {
  return stage.display_name || stage.name
}

export function isRealId(id: string): boolean {
  return !id.startsWith('stage-') && !id.startsWith('catalog-')
}

// ---------------------------------------------------------------------------
// Data fields catalog
// ---------------------------------------------------------------------------

const ALL_DATA_FIELDS: StageDataField[] = [
  { id: 'full_name',         displayName: 'Nome Completo',            category: 'basic',       required: false, auto_collect: false },
  { id: 'email',             displayName: 'Email',                    category: 'basic',       required: false, auto_collect: false },
  { id: 'phone',             displayName: 'Telefone',                 category: 'basic',       required: false, auto_collect: false },
  { id: 'cpf',               displayName: 'CPF',                      category: 'basic',       required: false, auto_collect: false },
  { id: 'birth_date',        displayName: 'Data de Nascimento',       category: 'basic',       required: false, auto_collect: false },
  { id: 'address',           displayName: 'Endereço Completo',        category: 'basic',       required: false, auto_collect: false },
  { id: 'cv_document',       displayName: 'Currículo (Arquivo)',       category: 'document',    required: false, auto_collect: false },
  { id: 'id_document',       displayName: 'Documento de Identidade',  category: 'document',    required: false, auto_collect: false },
  { id: 'proof_of_address',  displayName: 'Comprovante de Residência',category: 'document',    required: false, auto_collect: false },
  { id: 'rg',                displayName: 'RG',                       category: 'admissional', required: false, auto_collect: false },
  { id: 'ctps',              displayName: 'CTPS',                     category: 'admissional', required: false, auto_collect: false },
  { id: 'pis',               displayName: 'PIS/PASEP',                category: 'admissional', required: false, auto_collect: false },
  { id: 'bank_info',         displayName: 'Dados Bancários',          category: 'financial',   required: false, auto_collect: false },
  { id: 'emergency_contact', displayName: 'Contato de Emergência',    category: 'admissional', required: false, auto_collect: false },
]

const FIELD_CATEGORY_LABELS: Record<string, string> = {
  basic: 'Dados Básicos',
  document: 'Documentos',
  financial: 'Financeiro',
  admissional: 'Admissional',
}

// ---------------------------------------------------------------------------
// Data fields panel
// ---------------------------------------------------------------------------

interface DataFieldsPanelProps {
  stage: RecruitmentStage
  isEditMode: boolean
  onUpdate: (id: string, updates: Partial<RecruitmentStage>) => void
}

function DataFieldsPanel({ stage, isEditMode, onUpdate }: DataFieldsPanelProps) {
  const [expanded, setExpanded] = React.useState(false)

  const dataFields = stage.data_fields || []
  const enabledCount = dataFields.length

  function isEnabled(fieldId: string) {
    return dataFields.some(f => f.id === fieldId)
  }

  function getField(fieldId: string): StageDataField | undefined {
    return dataFields.find(f => f.id === fieldId)
  }

  function toggleField(catalog: StageDataField) {
    if (isEnabled(catalog.id)) {
      onUpdate(stage.id, { data_fields: dataFields.filter(f => f.id !== catalog.id) })
    } else {
      onUpdate(stage.id, { data_fields: [...dataFields, { ...catalog }] })
    }
  }

  function toggleRequired(fieldId: string) {
    onUpdate(stage.id, {
      data_fields: dataFields.map(f => f.id === fieldId ? { ...f, required: !f.required } : f),
    })
  }

  function toggleAutoCollect(fieldId: string) {
    onUpdate(stage.id, {
      data_fields: dataFields.map(f => f.id === fieldId ? { ...f, auto_collect: !f.auto_collect } : f),
    })
  }

  const byCategory = ALL_DATA_FIELDS.reduce<Record<string, StageDataField[]>>((acc, f) => {
    acc[f.category] = acc[f.category] || []
    acc[f.category].push(f)
    return acc
  }, {})

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle mt-3 pt-2">
      <button
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-1.5 text-xs lia-text-500 hover:lia-text-700 dark:hover:lia-text-300 transition-colors w-full"
        aria-expanded={expanded}
        type="button"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <span className="font-medium">Dados a coletar</span>
        <span className="lia-text-400">({enabledCount} campo{enabledCount !== 1 ? 's' : ''})</span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-3">
          {Object.entries(byCategory).map(([category, fields]) => (
            <div key={category}>
              <p className="text-micro font-semibold lia-text-400 uppercase tracking-wide mb-1.5 px-1">
                {FIELD_CATEGORY_LABELS[category] || category}
              </p>
              <div className="space-y-1">
                {fields.map(catalog => {
                  const active = isEnabled(catalog.id)
                  const field = getField(catalog.id)
                  return (
                    <div
                      key={catalog.id}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-md border transition-colors ${
                        active
                          ? 'bg-white dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default'
                          : 'bg-gray-50 dark:bg-lia-bg-primary/50 border-lia-border-subtle dark:border-lia-border-subtle'
                      }`}
                    >
                      {isEditMode ? (
                        <input
                          type="checkbox"
                          checked={active}
                          onChange={() => toggleField(catalog)}
                          className="h-3.5 w-3.5 rounded-md border-lia-border-default lia-text-900 cursor-pointer"
                          aria-label={`Ativar campo ${catalog.displayName}`}
                        />
                      ) : (
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${active ? 'bg-gray-900' : 'bg-gray-200'}`} />
                      )}

                      <span className={`flex-1 text-xs font-medium ${active ? 'lia-text-700 dark:text-lia-text-secondary' : 'lia-text-400'}`}>
                        {catalog.displayName}
                      </span>

                      {active && isEditMode && (
                        <div className="flex items-center gap-3">
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={field?.required ?? false}
                              onChange={() => toggleRequired(catalog.id)}
                              className="h-3 w-3 rounded-md border-lia-border-default lia-text-900 cursor-pointer"
                            />
                            <span className="text-micro lia-text-500">Obrigatório</span>
                          </label>
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={field?.auto_collect ?? false}
                              onChange={() => toggleAutoCollect(catalog.id)}
                              className="h-3 w-3 rounded-md border-lia-border-default lia-text-900 cursor-pointer"
                            />
                            <span className="text-micro lia-text-500">LIA coleta</span>
                          </label>
                        </div>
                      )}

                      {active && !isEditMode && (
                        <div className="flex items-center gap-1.5">
                          {field?.required && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-status-error/10 text-status-error text-micro">
                              Obrigatório
                            </span>
                          )}
                          {field?.auto_collect && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan text-micro">
                              LIA coleta
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
          <p className="text-micro lia-text-400 px-1 pt-1">
            Marque "LIA coleta" para que a assistente solicite o dado durante a conversa nesta etapa.
          </p>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-status panel
// ---------------------------------------------------------------------------

interface SubStatusPanelProps {
  stage: RecruitmentStage
  isEditMode: boolean
  onToggleSubStatus?: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
}

function SubStatusPanel({ stage, isEditMode, onToggleSubStatus }: SubStatusPanelProps) {
  const {
    expanded, displayList, loading, togglingId, activeCount, canFetch,
    handleExpand, handleToggleActive, handleToggleDefault,
  } = useSubStatusPanel({
    stageId: stage.id,
    initialSubStatuses: stage.sub_statuses || [],
    onToggleSubStatus,
  })

  const canManage = isEditMode && canFetch && !!onToggleSubStatus

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle mt-3 pt-2">
      <button
        onClick={handleExpand}
        className="flex items-center gap-1.5 text-xs lia-text-500 hover:lia-text-700 dark:hover:lia-text-300 transition-colors w-full"
        aria-expanded={expanded}
        aria-label={`${expanded ? 'Recolher' : 'Expandir'} subetapas de ${stage.display_name || stage.name}`}
        data-testid={`sub-status-panel-${stage.id}`}
        type="button"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <span className="font-medium">Subetapas</span>
        <span className="lia-text-400">({activeCount} ativas)</span>
        {!isRealId(stage.id) && isEditMode && (
          <span className="ml-auto text-micro text-status-warning">Salve a etapa primeiro</span>
        )}
      </button>

      {expanded && (
        <div className="mt-2 space-y-1.5">
          {loading && (
            <div className="flex items-center gap-2 px-1 py-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin lia-text-400" />
              <span className="text-xs lia-text-400">Carregando subetapas...</span>
            </div>
          )}

          {!loading && displayList.length === 0 && (
            <p className="text-xs lia-text-400 px-1 py-1 italic">
              Nenhuma subetapa disponível para esta etapa.
            </p>
          )}

          {!loading && displayList.map(ss => (
            <div
              key={ss.id}
              className={`flex items-center gap-2 px-2 py-1.5 rounded-md border transition-colors ${
                ss.is_active
                  ? 'bg-white dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default'
                  : 'bg-gray-50 dark:bg-lia-bg-primary/50 border-lia-border-subtle dark:border-lia-border-subtle opacity-60'
              }`}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{backgroundColor: ss.color || 'var(--gray-400)'}}
              />
              <span className={`flex-1 text-xs font-medium ${ss.is_active ? 'lia-text-700 dark:text-lia-text-secondary' : 'lia-text-400'}`}>
                {ss.display_name}
              </span>

              {ss.is_waiting && ss.is_active && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan-dark text-micro font-medium">
                  Aguarda
                </span>
              )}

              {canManage && ss.is_active && (
                <button
                  onClick={() => handleToggleDefault(ss)}
                  disabled={togglingId === `default-${ss.id}`}
                  aria-label={ss.is_default ? `Remover ${ss.display_name} como padrão` : `Definir ${ss.display_name} como padrão`}
                  title={ss.is_default ? 'Remover como padrão' : 'Definir como padrão'}
                  className="p-0.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                  data-testid={`sub-status-default-toggle-${ss.id}`}
                  type="button"
                >
                  {togglingId === `default-${ss.id}` ? (
                    <Loader2 className="h-3 w-3 animate-spin lia-text-400" />
                  ) : ss.is_default ? (
                    <Star className="h-3 w-3 text-status-warning fill-amber-400" />
                  ) : (
                    <Star className="h-3 w-3 lia-text-300 hover:text-status-warning" />
                  )}
                </button>
              )}

              {canManage && (
                <Switch
                  checked={ss.is_active ?? true}
                  onCheckedChange={() => handleToggleActive(ss)}
                  disabled={togglingId === ss.id}
                  aria-label={`${ss.is_active ? 'Desativar' : 'Ativar'} subetapa ${ss.display_name}`}
                />
              )}

              {!canManage && ss.is_default && (
                <Star className="h-3 w-3 text-status-warning fill-amber-400 flex-shrink-0" />
              )}
            </div>
          ))}

          {canManage && displayList.length > 0 && (
            <p className="text-micro lia-text-400 px-1 pt-1">
              Ative/desative subetapas do catálogo. Subetapas inativas não aparecem no processo seletivo.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Saturation control panel (screening stage only)
// ---------------------------------------------------------------------------

interface SaturationSettings {
  threshold_web: number
  threshold_sourcing: number
  unlock_increment: number
  unlock_hours: number
}

const DEFAULT_SATURATION: SaturationSettings = {
  threshold_web: 20,
  threshold_sourcing: 20,
  unlock_increment: 10,
  unlock_hours: 24,
}

function SaturationControlPanel({ stage, isEditMode }: { stage: RecruitmentStage; isEditMode: boolean }) {
  const [expanded, setExpanded] = React.useState(false)
  const [settings, setSettings] = React.useState<SaturationSettings>(DEFAULT_SATURATION)
  const [loading, setLoading] = React.useState(false)
  const [saving, setSaving] = React.useState(false)
  const [loaded, setLoaded] = React.useState(false)
  const [dirty, setDirty] = React.useState(false)

  const isScreening = stage.name === 'screening' || stage.action_behavior === 'screening'
  if (!isScreening) return null

  const handleExpand = () => {
    if (!expanded && !loaded) {
      setLoading(true)
      fetch('/api/backend-proxy/settings/saturation')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            setSettings({
              threshold_web: data.threshold_web ?? DEFAULT_SATURATION.threshold_web,
              threshold_sourcing: data.threshold_sourcing ?? DEFAULT_SATURATION.threshold_sourcing,
              unlock_increment: data.unlock_increment ?? DEFAULT_SATURATION.unlock_increment,
              unlock_hours: data.unlock_hours ?? DEFAULT_SATURATION.unlock_hours,
            })
          }
          setLoaded(true)
        })
        .catch(() => { setLoaded(true) })
        .finally(() => setLoading(false))
    }
    setExpanded(v => !v)
  }

  const handleChange = (field: keyof SaturationSettings, value: number) => {
    setSettings(prev => ({ ...prev, [field]: value }))
    setDirty(true)
  }

  const handleSave = () => {
    setSaving(true)
    fetch('/api/backend-proxy/settings/saturation', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
      .then(r => {
        if (r.ok) setDirty(false)
      })
      .catch(() => {})
      .finally(() => setSaving(false))
  }

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle mt-3 pt-2">
      <button
        onClick={handleExpand}
        className="flex items-center gap-1.5 text-xs lia-text-500 hover:lia-text-700 dark:hover:lia-text-300 transition-colors w-full"
        aria-expanded={expanded}
        type="button"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <Gauge className="h-3.5 w-3.5" />
        <span className="font-medium">Controle de Saturação</span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-3">
          {loading && (
            <div className="flex items-center gap-2 px-1 py-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin lia-text-400" />
              <span className="text-xs lia-text-400">Carregando configurações...</span>
            </div>
          )}

          {!loading && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <Label className="text-xs lia-text-600 dark:text-lia-text-tertiary">
                    Limite inscrições orgânicas (web/whatsapp)
                  </Label>
                  <input
                    type="number"
                    value={settings.threshold_web}
                    onChange={(e) => handleChange('threshold_web', parseInt(e.target.value) || 0)}
                    disabled={!isEditMode}
                    min={1}
                    max={999}
                    className="w-full px-2 py-1.5 text-xs lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-opacity disabled:opacity-50"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <Label className="text-xs lia-text-600 dark:text-lia-text-tertiary">
                    Limite busca ativa (sourcing)
                  </Label>
                  <input
                    type="number"
                    value={settings.threshold_sourcing}
                    onChange={(e) => handleChange('threshold_sourcing', parseInt(e.target.value) || 0)}
                    disabled={!isEditMode}
                    min={1}
                    max={999}
                    className="w-full px-2 py-1.5 text-xs lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-opacity disabled:opacity-50"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <Label className="text-xs lia-text-600 dark:text-lia-text-tertiary">
                    Incremento de desbloqueio
                  </Label>
                  <div className="flex items-center gap-1">
                    <span className="text-xs lia-text-400">+</span>
                    <input
                      type="number"
                      value={settings.unlock_increment}
                      onChange={(e) => handleChange('unlock_increment', parseInt(e.target.value) || 0)}
                      disabled={!isEditMode}
                      min={1}
                      max={100}
                      className="w-full px-2 py-1.5 text-xs lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-opacity disabled:opacity-50"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-1">
                  <Label className="text-xs lia-text-600 dark:text-lia-text-tertiary">
                    Horas de desbloqueio temporário
                  </Label>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      value={settings.unlock_hours}
                      onChange={(e) => handleChange('unlock_hours', parseInt(e.target.value) || 0)}
                      disabled={!isEditMode}
                      min={1}
                      max={168}
                      className="w-full px-2 py-1.5 text-xs lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-opacity disabled:opacity-50"
                    />
                    <span className="text-xs lia-text-400 whitespace-nowrap">horas</span>
                  </div>
                </div>
              </div>

              {isEditMode && dirty && (
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    onClick={handleSave}
                    disabled={saving}
                    className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 rounded-md px-3 py-1 text-xs font-medium"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                        Salvando...
                      </>
                    ) : (
                      'Salvar Saturação'
                    )}
                  </Button>
                </div>
              )}

              <p className="text-micro lia-text-400 px-1">
                Define os limites de candidatos simultâneos em triagem por canal. Quando o limite é atingido, novos candidatos entram em fila de espera.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// ReadOnlyStageCard
// ---------------------------------------------------------------------------

export function ReadOnlyStageCard({ stage }: { stage: RecruitmentStage }) {
  const isSystemStage = stage.type === 'system'

  return (
    <Card
      className={`border rounded-md p-4 mb-3 bg-white dark:bg-lia-bg-primary ${!stage.isActive ? "opacity-60" : ""} ${isSystemStage ? "border-lia-border-default bg-gray-50/50" : "border-lia-border-subtle"}`}
      style={{borderLeft: stage.color ? `4px solid ${stage.color}` : undefined}}
    >
      <div className="flex items-start gap-3">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-medium ${isSystemStage ? "bg-gray-200 lia-text-500" : "bg-gray-100 lia-text-500"}`}>
          {isSystemStage ? <Lock className="h-4 w-4" /> : stage.order}
        </div>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`flex-1 ${textStyles.bodyLarge} font-medium`}>
              {getStageDisplayName(stage)}
            </span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {getTypeBadge(stage.type)}
              <ActionBehaviorBadge behavior={stage.action_behavior} />
              {stage.isActive ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-status-success/10 text-status-success text-micro font-medium">
                  <Check className="h-3 w-3" />Ativo
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 lia-text-500 text-micro font-medium">
                  <X className="h-3 w-3" />Inativo
                </span>
              )}
            </div>
          </div>

          {stage.notes && <p className={`${textStyles.description} italic`}>{stage.notes}</p>}

          {stage.sla > 0 && (
            <div className="flex items-center gap-1.5 pt-1">
              <Clock className="h-3.5 w-3.5 lia-text-500" />
              <span className={textStyles.caption}>SLA: {stage.sla} {stage.sla === 1 ? 'dia' : 'dias'}</span>
            </div>
          )}

          {stage.default_channel && stage.default_channel !== 'email' && (
            <div className="flex items-center gap-1.5 pt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium bg-gray-100 lia-text-600">
                Canal: {stage.default_channel === 'whatsapp' ? 'WhatsApp' : 'E-mail + WhatsApp'}
              </span>
            </div>
          )}

          {(stage.sub_statuses?.length ?? 0) > 0 && (
            <div className="flex items-center gap-1 flex-wrap mt-1">
              {stage.sub_statuses?.map(ss => (
                <span key={ss.id} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-micro bg-gray-100 lia-text-600 dark:bg-lia-bg-elevated dark:text-lia-text-tertiary">
                  {ss.display_name}
                  {ss.is_default && <Star className="h-2.5 w-2.5 text-status-warning" />}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// SortableStageCard props
// ---------------------------------------------------------------------------

export interface SortableStageCardProps {
  stage: RecruitmentStage
  onUpdate: (id: string, updates: Partial<RecruitmentStage>) => void
  onRemove: (id: string) => void
  onToggleSubStatus?: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
  isEditMode: boolean
  registerRef?: (id: string, element: HTMLDivElement | null) => void
}

// ---------------------------------------------------------------------------
// SortableStageCard
// ---------------------------------------------------------------------------

export function SortableStageCard({
  stage, onUpdate, onRemove,
  onToggleSubStatus,
  isEditMode, registerRef,
}: SortableStageCardProps) {
  const isSystemStage = stage.type === 'system'
  const canEditName = !isSystemStage
  const canRemove = stage.type === 'custom'
  const canDrag = !isSystemStage

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: stage.id, disabled: !isEditMode || !canDrag })

  const style = { transform: CSS.Transform.toString(transform), transition }

  const combinedRef = (element: HTMLDivElement | null) => {
    setNodeRef(element)
    if (registerRef) registerRef(stage.id, element)
  }

  if (!isEditMode) return <ReadOnlyStageCard stage={stage} />

  return (
    <div ref={combinedRef} style={style}>
      <Card
        className={`border rounded-md p-4 mb-3 transition-colors duration-200 ${
          isDragging ? "opacity-90 bg-gray-50" : "bg-white hover:border-gray-400 dark:bg-lia-bg-secondary dark:hover:border-gray-500"
        } ${!stage.isActive ? "opacity-60" : ""} ${
          isSystemStage ? "border-lia-border-default bg-gray-50/50 dark:bg-lia-bg-primary/50" : "border-lia-border-subtle dark:border-lia-border-subtle"
        }`}
        style={{borderLeft: stage.color ? `4px solid ${stage.color}` : undefined}}
      >
        <div className="flex items-start gap-3">
          {canDrag ? (
            <button
              {...attributes} {...listeners}
              className="mt-1 cursor-grab active:cursor-grabbing p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Arrastar para reordenar"
            >
              <GripVertical className="h-5 w-5 lia-text-400" />
            </button>
          ) : (
            <div className="mt-1 p-1"><Lock className="h-5 w-5 lia-text-300" /></div>
          )}

          <div className="flex-1 space-y-3">
            {/* Name row */}
            <div className="flex items-center gap-3 flex-wrap">
              {canEditName ? (
                <input
                  type="text"
                  value={getStageDisplayName(stage)}
                  onChange={(e) => onUpdate(stage.id, { display_name: e.target.value, name: stage.name })}
                  className="flex-1 px-3 py-2 text-base-ui font-medium lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-colors"
                  placeholder="Nome da etapa"
                />
              ) : (
                <span className={`flex-1 ${textStyles.bodyLarge} font-medium px-3 py-2`}>
                  {getStageDisplayName(stage)}
                </span>
              )}
              <div className="flex items-center gap-2 flex-wrap">
                {getTypeBadge(stage.type)}
                <ActionBehaviorBadge behavior={stage.action_behavior} />
                {canEditName && (
                  <div className="flex items-center gap-2">
                    <Label htmlFor={`active-${stage.id}`} className={textStyles.description}>Ativo</Label>
                    <Switch
                      id={`active-${stage.id}`}
                      checked={stage.isActive}
                      onCheckedChange={(checked: boolean) => onUpdate(stage.id, { isActive: checked })}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Notes */}
            {canEditName && (
              <textarea
                value={stage.notes}
                onChange={(e) => onUpdate(stage.id, { notes: e.target.value })}
                placeholder="Notas e comentários para a equipe..."
                className="w-full px-3 py-2 text-xs lia-text-600 dark:text-lia-text-tertiary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-colors resize-none"
                rows={2}
              />
            )}

            {/* Config row: SLA / Ação / Canal */}
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-4 flex-wrap">
                {/* SLA */}
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 lia-text-500" />
                  <Label htmlFor={`sla-${stage.id}`} className={textStyles.description}>SLA</Label>
                  <div className="flex items-center gap-1">
                    <input
                      id={`sla-${stage.id}`}
                      type="number"
                      value={stage.sla}
                      onChange={(e) => onUpdate(stage.id, { sla: parseInt(e.target.value) || 0 })}
                      className="w-14 px-2 py-1 text-xs text-center lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-colors"
                      min={0} max={30}
                    />
                    <span className={textStyles.caption}>dias</span>
                  </div>
                </div>

                {/* Ação */}
                <div className="flex items-center gap-2">
                  <Label className={textStyles.description}>Ação</Label>
                  <select
                    value={stage.action_behavior || 'passive'}
                    onChange={(e) => onUpdate(stage.id, { action_behavior: e.target.value })}
                    className="px-2 py-1 text-xs lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-colors"
                  >
                    <option value="passive">Passivo</option>
                    <option value="screening">Triagem WSI</option>
                    <option value="scheduling">Agendamento</option>
                    <option value="evaluation">Avaliação</option>
                    <option value="verification">Verificação</option>
                    <option value="offer">Proposta</option>
                    <option value="intake">Entrada</option>
                    <option value="conclusion_hired">Contratação</option>
                    <option value="conclusion_rejected">Reprovação</option>
                    <option value="conclusion_declined">Proposta Recusada</option>
                  </select>
                </div>

                {/* Canal */}
                <div className="flex items-center gap-2">
                  <Label className={textStyles.description}>Canal</Label>
                  <select
                    value={stage.default_channel || 'email'}
                    onChange={(e) => onUpdate(stage.id, { default_channel: e.target.value })}
                    className="px-2 py-1 text-xs lia-text-800 dark:text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent transition-colors"
                  >
                    <option value="email">E-mail</option>
                    <option value="whatsapp">WhatsApp</option>
                    <option value="email_whatsapp">E-mail + WhatsApp</option>
                  </select>
                </div>
              </div>

              {canRemove && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemove(stage.id)}
                  className="lia-text-400 hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20 transition-colors"
                  aria-label={`Remover etapa ${getStageDisplayName(stage)}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Sub-status panel */}
            <SubStatusPanel
              stage={stage}
              isEditMode={isEditMode}
              onToggleSubStatus={onToggleSubStatus}
            />

            {/* Data fields panel */}
            <DataFieldsPanel
              stage={stage}
              isEditMode={isEditMode}
              onUpdate={onUpdate}
            />

            {/* Saturation control panel (screening stage only) */}
            <SaturationControlPanel
              stage={stage}
              isEditMode={isEditMode}
            />
          </div>
        </div>
      </Card>
    </div>
  )
}
