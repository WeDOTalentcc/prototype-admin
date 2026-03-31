// @ts-nocheck
"use client"

import React, { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChevronDown, ChevronUp, Brain, Pencil, Check,
  GitBranch, Calendar, MessageSquare, Filter, Zap, Loader2, X, Maximize2
} from "lucide-react"
import { useHiringPolicies } from "@/hooks/use-hiring-policies"
import { FIELD_LABELS, POLICY_BLOCKS, FIELD_CONFIGS, formatFieldValue } from "@/lib/hiring-policy-utils"
import { LiaChatMessage, LiaChatInput, LiaLoadingIndicator } from "@/components/ui/lia-expanded-panel"
import { textStyles } from "@/lib/design-tokens"
import type { LucideIcon } from "lucide-react"

const ICON_MAP: Record<string, LucideIcon> = {
  GitBranch,
  Calendar,
  MessageSquare,
  Filter,
  Zap,
}

function InlineFieldEditor({
  field,
  currentValue,
  onSave,
  onCancel,
  isSaving,
}: {
  field: string
  currentValue: unknown
  onSave: (value: unknown) => void
  onCancel: () => void
  isSaving: boolean
}) {
  const config = FIELD_CONFIGS[field]
  const [localValue, setLocalValue] = useState(() => {
    if (currentValue === null || currentValue === undefined) return ''
    if (config?.type === 'boolean') return currentValue
    if (Array.isArray(currentValue)) return currentValue.join(', ')
    return String(currentValue)
  })

  const handleSave = () => {
    let parsed: unknown = localValue
    if (config?.type === 'number') {
      parsed = localValue === '' ? null : Number(localValue)
    } else if (config?.type === 'boolean') {
      parsed = localValue
    } else if (field === 'default_screening_questions') {
      parsed = typeof localValue === 'string'
        ? localValue.split(',').map((s: string) => s.trim()).filter(Boolean)
        : localValue
    }
    onSave(parsed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      onCancel()
    }
  }

  if (config?.type === 'boolean') {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={() => { onSave(!currentValue) }}
          disabled={isSaving}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none ${
            currentValue ? 'bg-gray-900 dark:lia-bg-100' : 'bg-gray-300 dark:lia-bg-600'
          }`}
        >
          <span
            className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white dark:bg-lia-bg-primary transition-transform motion-reduce:transition-none ${
              currentValue ? 'translate-x-4' : 'translate-x-0.5'
            }`}
          />
        </button>
        <button
          onClick={onCancel}
          className="p-0.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <X className="w-3 h-3 lia-text-400" />
        </button>
      </div>
    )
  }

  if (config?.type === 'select' && config.options) {
    return (
      <div className="flex items-center gap-1">
        <select
          value={localValue}
          onChange={(e) => setLocalValue(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
          disabled={isSaving}
          className="text-xs font-medium lia-text-800 dark:text-lia-text-primary bg-white dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-md px-1.5 py-0.5 focus:outline-none focus:ring-1 focus:ring-gray-400"
          style={{fontFamily: '"Inter", sans-serif'}}
        >
          <option value="">Selecionar...</option>
          {config.options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="p-0.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <Check className="w-3 h-3 text-status-success" />
        </button>
        <button
          onClick={onCancel}
          className="p-0.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <X className="w-3 h-3 lia-text-400" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      <input
        type={config?.type === 'number' ? 'number' : 'text'}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
        disabled={isSaving}
        min={config?.min}
        max={config?.max}
        placeholder={config?.placeholder || ''}
        className="w-24 text-xs font-medium lia-text-800 dark:text-lia-text-primary bg-white dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-md px-1.5 py-0.5 text-right focus:outline-none focus:ring-1 focus:ring-gray-400"
        style={{fontFamily: '"Inter", sans-serif'}}
      />
      {config?.suffix && (
        <span className="text-micro lia-text-500">{config.suffix}</span>
      )}
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="p-0.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        {isSaving ? (
          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none lia-text-400" />
        ) : (
          <Check className="w-3 h-3 text-status-success" />
        )}
      </button>
      <button
        onClick={onCancel}
        className="p-0.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <X className="w-3 h-3 lia-text-400" />
      </button>
    </div>
  )
}

export function HiringPoliciesHub() {
  const {
    policy,
    progress,
    messages,
    inputValue,
    setInputValue,
    isSending,
    isLoading,
    expandedBlocks,
    chatEndRef,
    setupProgress,
    handleSendMessage,
    toggleBlock,
    editingField,
    startEditing,
    cancelEditing,
    saveFieldValue,
    isSavingBlock,
    recentlyUpdated,
  } = useHiringPolicies()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none lia-text-400 dark:lia-text-500" />
        <span className={`ml-2 ${textStyles.body}`}>
          Carregando politicas...
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className={textStyles.h3}>Políticas de Contratação</h2>
          <div className="flex items-center gap-2">
            <span className={`${textStyles.metricSmall} flex-shrink-0`}>
              {setupProgress}% configurado
            </span>
            {setupProgress >= 100 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30 dark:bg-status-success/20 dark:text-status-success dark:border-status-success/30 flex-shrink-0">
                Completo
              </span>
            )}
          </div>
        </div>
        <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full transition-[width,height] duration-500 bg-gray-900 dark:lia-bg-100"
            style={{width: `${setupProgress}%`}}
          />
        </div>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        <div
          className="w-[60%] flex flex-col bg-white dark:bg-lia-bg-primary rounded-md overflow-hidden"
          style={{border: '1px solid var(--gray-200)'}}
        >
          <div
            className="flex-shrink-0 px-4 py-3"
            style={{backgroundColor: 'var(--gray-50)'}}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div
                  className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/[.12]"
                >
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3
                    className="text-sm font-semibold leading-tight truncate lia-text-950 dark:lia-text-50"
                   
                  >
                    Olá! Sou a Lia.
                  </h3>
                  <p
                    className="text-xs leading-tight truncate mt-0.5 lia-text-500"
                   
                   aria-live="polite" aria-atomic="true">
                    Posso criar vagas, buscar candidatos, analisar ...
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none flex items-center justify-center"
                  aria-label="Expandir chat"
                >
                  <Maximize2 className="w-3.5 h-3.5 lia-text-500" />
                </button>
                <button
                  className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none flex items-center justify-center"
                  aria-label="Fechar chat"
                >
                  <X className="w-4 h-4 lia-text-500" />
                </button>
              </div>
            </div>
          </div>

          <div
            className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
            style={{backgroundColor: 'var(--gray-50)'}}
          >
            {messages.map((msg, idx) => (
              <LiaChatMessage
                key={idx}
                type={msg.role === 'user' ? 'user' : 'lia'}
                content={msg.content}
                timestamp={msg.timestamp}
              />
            ))}
            {isSending && <LiaLoadingIndicator />}
            <div ref={chatEndRef} />
          </div>

          <div
            className="flex-shrink-0 p-4"
            style={{backgroundColor: 'var(--gray-50)'}}
          >
            <LiaChatInput
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleSendMessage}
              placeholder="Envie mensagem para a LIA..."
              isLoading={isSending}
              showFileUpload={false}
              showAudioRecord={false}
            />
          </div>
        </div>

        <div className="w-[40%] overflow-y-auto space-y-3">
          {POLICY_BLOCKS.map((block) => {
            const IconComp = ICON_MAP[block.iconName]
            const isExpanded = expandedBlocks.has(block.key)
            const blockData = policy ? (policy as Record<string, unknown>)[block.key] : null
            const isCompleted = progress?.blocks_completed?.[block.key] ?? false

            return (
              <Card
                key={block.key}
                className="bg-white dark:bg-lia-bg-secondary overflow-hidden rounded-md"
                style={{border: '1px solid var(--gray-200)'}}
              >
                <button
                  onClick={() => toggleBlock(block.key)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none duration-150"
                  aria-expanded={isExpanded}
                  aria-label={`${block.title} - ${isCompleted ? 'Configurado' : 'Pendente'}`}
                >
                  <div className="flex items-center gap-2">
                    {IconComp && <IconComp className="w-4 h-4 lia-text-500 dark:text-lia-text-tertiary" />}
                    <span className={textStyles.h3}>
                      {block.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium border ${
                        isCompleted
                          ? 'bg-status-success/10 text-status-success border-status-success/30 dark:bg-status-success/20 dark:text-status-success dark:border-status-success/30'
                          : 'bg-gray-100 lia-text-700 border-lia-border-subtle dark:bg-lia-bg-elevated dark:text-lia-text-secondary dark:border-lia-border-default'
                      }`}
                    >
                      {isCompleted ? 'Configurado' : 'Pendente'}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 lia-text-400 dark:lia-text-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 lia-text-400 dark:lia-text-500" />
                    )}
                  </div>
                </button>

                {isExpanded && blockData && (
                  <CardContent className="px-4 py-3" style={{borderTop: '1px solid var(--gray-200)'}}>
                    <div className="space-y-1">
                      {block.fields.map((field) => {
                        const value = blockData[field]
                        const isEditing = editingField?.block === block.key && editingField?.field === field
                        const isUpdated = recentlyUpdated.has(field)

                        return (
                          <div
                            key={field}
                            className={`group flex items-center justify-between gap-2 py-1.5 px-1.5 rounded-md transition-colors motion-reduce:transition-none duration-300 ${
                              isUpdated ? 'bg-status-success/10 dark:bg-status-success/10' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                            }`}
                          >
                            <span className={`${textStyles.description} flex-shrink-0`}>
                              {FIELD_LABELS[field] || field}
                            </span>
                            {isEditing ? (
                              <InlineFieldEditor
                                field={field}
                                currentValue={value}
                                onSave={(newValue) => saveFieldValue(block.key, field, newValue)}
                                onCancel={cancelEditing}
                                isSaving={isSavingBlock}
                              />
                            ) : (
                              <div className="flex items-center gap-1">
                                <span className={`${textStyles.metricSmall} text-right transition-colors motion-reduce:transition-none duration-300 ${
                                  isUpdated ? 'text-status-success dark:text-status-success' : ''
                                }`}>
                                  {formatFieldValue(value)}
                                </span>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    startEditing(block.key, field)
                                  }}
                                  className="opacity-0 group-hover:opacity-100 p-0.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-opacity motion-reduce:transition-none"
                                  aria-label={`Editar ${FIELD_LABELS[field] || field}`}
                                >
                                  <Pencil className="w-3 h-3 lia-text-400" />
                                </button>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                )}

                {isExpanded && !blockData && (
                  <CardContent className="px-4 py-3" style={{borderTop: '1px solid var(--gray-200)'}}>
                    <p className={textStyles.description}>Nenhum dado configurado ainda.</p>
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
