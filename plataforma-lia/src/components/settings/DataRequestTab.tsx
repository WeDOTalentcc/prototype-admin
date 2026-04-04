"use client"
import NextImage from "next/image"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  ClipboardList, Settings, FileText, Palette,
  Plus, Trash2, Upload, Lightbulb, Bot, Shield, Bell, Clock,
  ChevronDown, Pencil, X, Save, Database, User, File, Brain, Info,
  MessageSquare, Send, CheckCircle, AlertCircle
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useDataRequestConfig, DataField, CollectionMode, LgpdConfig } from "@/hooks/use-data-request-config"
import { Loader2 } from "lucide-react"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

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

const FieldBadges = ({ field }: { field: DataField }) => (
  <div className="flex items-center gap-1 flex-wrap">
    <Badge variant="outline" className="text-micro px-1 py-0 h-4">
      {field.type}
    </Badge>
    {field.isDefault && (
      <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro px-1 py-0 h-4">
        <Database className="w-2.5 h-2.5 mr-0.5" />
        Banco
      </Badge>
    )}
    {field.savesToProfile && (
      <Badge className="bg-status-success/10 text-status-success dark:bg-status-success/30 dark:text-status-success text-micro px-1 py-0 h-4">
        <User className="w-2.5 h-2.5 mr-0.5" />
        Cadastro
      </Badge>
    )}
    {field.type === 'file' && (
      <Badge className="bg-status-warning/10 text-status-warning dark:bg-status-warning/30 dark:text-status-warning text-micro px-1 py-0 h-4">
        <File className="w-2.5 h-2.5 mr-0.5" />
        Documento
      </Badge>
    )}
    {!field.isDefault && (
      <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro px-1 py-0 h-4">
        <Brain className="w-2.5 h-2.5 mr-0.5 text-wedo-cyan" />
        Custom
      </Badge>
    )}
  </div>
)

export function DataRequestTab({ companyId = 'default' }: DataRequestTabProps) {
  const {
    config,
    hasChanges,
    isSaving,
    isLoading,
    error,
    updateGeneralConfig,
    updateCollectionMessages,
    updateLgpdConfig,
    toggleFieldEnabled,
    addCustomField,
    removeCustomField,
    updateBranding,
    saveConfig,
    resetConfig,
  } = useDataRequestConfig(companyId)

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
      addCustomField({
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

  const handleStartEditing = () => {
    setIsEditing(true)
  }

  const handleCancelEditing = () => {
    resetConfig()
    setIsEditing(false)
    setShowAddField(false)
  }

  const handleSaveChanges = async () => {
    await saveConfig()
    setIsEditing(false)
  }

  const generateLiaSuggestion = (type: 'welcome' | 'thankYou') => {
    if (type === 'welcome') {
      updateBranding({
        welcomeMessage: 'Olá! 👋 Estamos muito felizes em ter você em nosso processo seletivo. Para dar continuidade, precisamos de algumas informações adicionais. Fique tranquilo, seus dados estão protegidos de acordo com a LGPD.'
      })
    } else {
      updateBranding({
        thankYouMessage: 'Perfeito! ✅ Recebemos todas as suas informações com sucesso. Nossa equipe irá analisar e entraremos em contato em breve com os próximos passos. Enquanto isso, fique à vontade para nos contatar se tiver alguma dúvida.'
      })
    }
  }

  const enabledFields = config.fields.filter(f => f.enabled)
  const defaultFields = config.fields.filter(f => f.isDefault)
  const customFields = config.fields.filter(f => !f.isDefault)

  if (isLoading) {
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
      {error && (
        <div className="flex items-center gap-2 p-3 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-md">
          <AlertCircle className="w-4 h-4 text-status-warning flex-shrink-0" />
          <p className="text-xs text-status-warning dark:text-status-warning">
            {error} - Usando configurações padrão.
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
              {isEditing ? (
                <>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleCancelEditing} 
                    disabled={isSaving}
                    className="h-8 text-xs px-3"
                  >
                    <X className="w-3.5 h-3.5 mr-1" />
                    Cancelar
                  </Button>
                  <Button 
                    size="sm" 
                    onClick={handleSaveChanges} 
                    disabled={isSaving || !hasChanges}
                    className="h-8 text-xs px-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active text-white"
                  >
                    <Save className="w-3.5 h-3.5 mr-1" />
                    {isSaving ? 'Salvando...' : 'Salvar Alterações'}
                  </Button>
                </>
              ) : (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleStartEditing}
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
            isExpanded={expandedSections.general}
            onToggle={() => toggleSection('general')}
          >
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
                  <Switch
                    checked={config.otpRequired}
                    onCheckedChange={(checked: boolean) => updateGeneralConfig({ otpRequired: checked })}
                  />
                ) : (
                  <Badge variant={config.otpRequired ? "default" : "secondary"} className="text-micro">
                    {config.otpRequired ? 'Ativo' : 'Inativo'}
                  </Badge>
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
                  <Switch
                    checked={config.autoReminders}
                    onCheckedChange={(checked: boolean) => updateGeneralConfig({ autoReminders: checked })}
                  />
                ) : (
                  <Badge variant={config.autoReminders ? "default" : "secondary"} className="text-micro">
                    {config.autoReminders ? 'Ativo' : 'Inativo'}
                  </Badge>
                )}
              </div>

              <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
                  <Label className="text-xs font-medium text-lia-text-primary">Dias para Expiração</Label>
                </div>
                {isEditing ? (
                  <Select
                    value={config.expirationDays.toString()}
                    onValueChange={(value) => updateGeneralConfig({ expirationDays: parseInt(value) })}
                  >
                    <SelectTrigger className="w-full h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
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
                    <Select
                      value={config.reminderDays.toString()}
                      onValueChange={(value) => updateGeneralConfig({ reminderDays: parseInt(value) })}
                    >
                      <SelectTrigger className="w-full h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
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
          </CollapsibleSection>

          <CollapsibleSection
            id="collection"
            title="Modelo de Coleta (WhatsApp)"
            icon={MessageSquare}
            isExpanded={expandedSections.collection}
            onToggle={() => toggleSection('collection')}
          >
            <div className="space-y-4">
              <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                <Label className="text-xs font-medium text-lia-text-primary mb-2 block">
                  Como o candidato responde?
                </Label>
                {isEditing ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    {[
                      { value: 'portal_only' as CollectionMode, label: 'Apenas Portal', desc: 'Link direto para formulário', icon: FileText },
                      { value: 'chat_only' as CollectionMode, label: 'Apenas Chat', desc: 'Conversa pergunta por pergunta', icon: MessageSquare },
                      { value: 'candidate_choice' as CollectionMode, label: 'Candidato Escolhe', desc: 'LIA pergunta preferência', icon: CheckCircle },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => updateGeneralConfig({ collectionMode: option.value })}
                        className={cn(
                          "p-3 rounded-md border-2 text-left transition-colors",
                          config.collectionMode === option.value
                            ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:border-lia-border-subtle dark:bg-lia-bg-secondary"
                            : "border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default"
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <option.icon className={cn(
                            "w-4 h-4",
                            config.collectionMode === option.value ? "text-lia-text-primary" : "text-lia-text-tertiary"
                          )} />
                          <span className={cn(
                            "text-xs font-medium",
 config.collectionMode === option.value ? "text-lia-text-primary" : "text-lia-text-primary"
                          )}>
                            {option.label}
                          </span>
                        </div>
                        <p className="text-micro text-lia-text-secondary">{option.desc}</p>
                        {option.value === 'candidate_choice' && (
                          <Badge className="mt-1 bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated text-micro h-4">Recomendado</Badge>
                        )}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated text-micro">
                      {config.collectionMode === 'portal_only' && 'Apenas Portal'}
                      {config.collectionMode === 'chat_only' && 'Apenas Chat'}
                      {config.collectionMode === 'candidate_choice' && 'Candidato Escolhe'}
                    </Badge>
                    <span className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                      {config.collectionMode === 'portal_only' && '- Envia link direto para formulário'}
                      {config.collectionMode === 'chat_only' && '- Coleta via conversa no WhatsApp'}
                      {config.collectionMode === 'candidate_choice' && '- LIA pergunta preferência ao candidato'}
                    </span>
                  </div>
                )}
              </div>

              <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-4">
                <h4 className="text-xs font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                  <Send className="w-3.5 h-3.5 text-lia-text-primary" />
                  Mensagens do WhatsApp
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="w-3 h-3 text-lia-text-tertiary" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-micro">
                          Use variáveis: {'{{nome}}'}, {'{{empresa}}'}, {'{{campo}}'}, {'{{proximo_campo}}'}, {'{{campos_pendentes}}'}, {'{{dias_restantes}}'}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </h4>
                <div className="space-y-3">
                  <div>
                    <Label className="text-micro text-lia-text-secondary mb-1 block">Solicitação Inicial</Label>
                    {isEditing ? (
                      <textarea
                        value={config.collectionMessages.initialRequest}
                        onChange={(e) => updateCollectionMessages({ initialRequest: e.target.value })}
                        rows={2}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                      />
                    ) : (
                      <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                        {config.collectionMessages.initialRequest}
                      </p>
                    )}
                  </div>

                  {(config.collectionMode === 'candidate_choice') && (
                    <div>
                      <Label className="text-micro text-lia-text-secondary mb-1 block">Mensagem de Escolha</Label>
                      {isEditing ? (
                        <textarea
                          value={config.collectionMessages.choicePrompt}
                          onChange={(e) => updateCollectionMessages({ choicePrompt: e.target.value })}
                          rows={3}
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                        />
                      ) : (
                        <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                          {config.collectionMessages.choicePrompt}
                        </p>
                      )}
                    </div>
                  )}

                  {(config.collectionMode === 'chat_only' || config.collectionMode === 'candidate_choice') && (
                    <>
                      <div>
                        <Label className="text-micro text-lia-text-secondary mb-1 block">Início da Coleta via Chat</Label>
                        {isEditing ? (
                          <textarea
                            value={config.collectionMessages.chatStartMessage}
                            onChange={(e) => updateCollectionMessages({ chatStartMessage: e.target.value })}
                            rows={2}
                            className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                          />
                        ) : (
                          <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                            {config.collectionMessages.chatStartMessage}
                          </p>
                        )}
                      </div>

                      <div>
                        <Label className="text-micro text-lia-text-secondary mb-1 block">Confirmação de Documento</Label>
                        {isEditing ? (
                          <textarea
                            value={config.collectionMessages.documentReceived}
                            onChange={(e) => updateCollectionMessages({ documentReceived: e.target.value })}
                            rows={1}
                            className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                          />
                        ) : (
                          <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                            {config.collectionMessages.documentReceived}
                          </p>
                        )}
                      </div>
                    </>
                  )}

                  <div>
                    <Label className="text-micro text-lia-text-secondary mb-1 block">Lembrete de Pendência</Label>
                    {isEditing ? (
                      <textarea
                        value={config.collectionMessages.pendingReminder}
                        onChange={(e) => updateCollectionMessages({ pendingReminder: e.target.value })}
                        rows={2}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                      />
                    ) : (
                      <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                        {config.collectionMessages.pendingReminder}
                      </p>
                    )}
                  </div>

                  <div>
                    <Label className="text-micro text-lia-text-secondary mb-1 block">Confirmação Final</Label>
                    {isEditing ? (
                      <textarea
                        value={config.collectionMessages.allComplete}
                        onChange={(e) => updateCollectionMessages({ allComplete: e.target.value })}
                        rows={1}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                      />
                    ) : (
                      <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                        {config.collectionMessages.allComplete}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection
            id="lgpd"
            title="LGPD e Consentimento"
            icon={Shield}
            isExpanded={expandedSections.lgpd}
            onToggle={() => toggleSection('lgpd')}
          >
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
                      <Switch
                        checked={config.lgpd.requireConsent}
                        onCheckedChange={(checked: boolean) => updateLgpdConfig({ requireConsent: checked })}
                      />
                    ) : (
                      <Badge variant={config.lgpd.requireConsent ? "default" : "secondary"} className="text-micro">
                        {config.lgpd.requireConsent ? 'Obrigatório' : 'Desabilitado'}
                      </Badge>
                    )}
                  </div>
                  <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Candidato deve autorizar antes de enviar dados</p>
                </div>

                <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs font-medium text-lia-text-primary">Permitir Exclusão</Label>
                    {isEditing ? (
                      <Switch
                        checked={config.lgpd.allowDataDeletion}
                        onCheckedChange={(checked: boolean) => updateLgpdConfig({ allowDataDeletion: checked })}
                      />
                    ) : (
                      <Badge variant={config.lgpd.allowDataDeletion ? "default" : "secondary"} className="text-micro">
                        {config.lgpd.allowDataDeletion ? 'Habilitado' : 'Desabilitado'}
                      </Badge>
                    )}
                  </div>
                  <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Candidato pode solicitar exclusão dos dados</p>
                </div>
              </div>

              <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                <Label className="text-xs font-medium text-lia-text-primary mb-2 block">
                  Retenção de Dados
                </Label>
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
                  <p className="text-xs text-lia-text-secondary">
                    {config.lgpd.dataRetentionDays} dias após término do processo
                  </p>
                )}
              </div>

              <div>
                <Label className="text-xs font-medium text-lia-text-primary mb-1 block">
                  Mensagem de Consentimento (WhatsApp)
                </Label>
                {isEditing ? (
                  <textarea
                    value={config.lgpd.consentMessage}
                    onChange={(e) => updateLgpdConfig({ consentMessage: e.target.value })}
                    rows={4}
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                  />
                ) : (
                  <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                    {config.lgpd.consentMessage}
                  </p>
                )}
              </div>

              <div>
                <Label className="text-xs font-medium text-lia-text-primary mb-1 block">
                  Disclaimer (Portal)
                </Label>
                {isEditing ? (
                  <textarea
                    value={config.lgpd.disclaimerText}
                    onChange={(e) => updateLgpdConfig({ disclaimerText: e.target.value })}
                    rows={3}
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                  />
                ) : (
                  <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md whitespace-pre-wrap">
                    {config.lgpd.disclaimerText}
                  </p>
                )}
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection
            id="fields"
            title="Campos Solicitados"
            icon={FileText}
            count={enabledFields.length}
            isExpanded={expandedSections.fields}
            onToggle={() => toggleSection('fields')}
          >
            <div className="space-y-3">
              {isEditing && (
                <>
                  {showAddField ? (
                    <div className="p-3 border border-lia-border-default dark:border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                      <h4 className="text-xs font-medium mb-2 text-lia-text-primary">Novo Campo Customizado</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                        <div>
                          <Label className="text-micro text-lia-text-primary">Nome do Campo</Label>
                          <input
                            type="text"
                            value={newFieldName}
                            onChange={(e) => setNewFieldName(e.target.value)}
                            placeholder="Ex: Número do Passaporte"
                            className="w-full mt-1 px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                          />
                        </div>
                        <div>
                          <Label className="text-micro text-lia-text-primary">Tipo</Label>
                          <Select value={newFieldType} onValueChange={(v) => setNewFieldType(v as "textarea" | "text" | "email" | "phone" | "file" | "date")}>
                            <SelectTrigger className="mt-1 h-7 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="text">Texto</SelectItem>
                              <SelectItem value="email">Email</SelectItem>
                              <SelectItem value="phone">Telefone</SelectItem>
                              <SelectItem value="date">Data</SelectItem>
                              <SelectItem value="file">Arquivo</SelectItem>
                              <SelectItem value="textarea">Texto Longo</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="flex items-end gap-2">
                          <Button size="sm" onClick={handleAddField} disabled={!newFieldName.trim()} className="h-7 text-micro px-2">
                            Adicionar
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => setShowAddField(false)} className="h-7 text-micro px-2">
                            Cancelar
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <Button variant="outline" size="sm" onClick={() => setShowAddField(true)} className="h-7 text-micro">
                      <Plus className="w-3 h-3 mr-1" />
                      Adicionar Campo
                    </Button>
                  )}
                </>
              )}

              {defaultFields.length > 0 && (
                <div>
                  <h4 className="text-micro font-medium text-lia-text-secondary mb-2 uppercase tracking-wide">Campos do Sistema</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {defaultFields.map((field) => (
                      <TooltipProvider key={field.id}>
                        <div
                          className={cn(
                            "flex items-center justify-between p-2 rounded-md border transition-colors",
                            field.enabled
                              ? "bg-lia-bg-primary dark:bg-lia-bg-primary border-lia-border-default dark:border-lia-border-default"
                              : "bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle opacity-60"
                          )}
                        >
                          <div className="flex-1 min-w-0 mr-2">
                            <div className="flex items-center gap-1">
                              <span className="text-xs font-medium text-lia-text-primary truncate">{field.displayName}</span>
                              {field.id === 'cv_document' && (
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Info className="w-3 h-3 text-lia-text-secondary" />
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs">
                                    <p className="text-micro">O CV enviado será parseado automaticamente pela LIA para extração de dados estruturados.</p>
                                  </TooltipContent>
                                </Tooltip>
                              )}
                            </div>
                            <FieldBadges field={field} />
                          </div>
                          {isEditing ? (
                            <Switch
                              checked={field.enabled}
                              onCheckedChange={() => toggleFieldEnabled(field.id)}
                              className="scale-75"
                            />
                          ) : (
                            <Badge variant={field.enabled ? "default" : "secondary"} className="text-micro h-4">
                              {field.enabled ? 'Ativo' : 'Inativo'}
                            </Badge>
                          )}
                        </div>
                      </TooltipProvider>
                    ))}
                  </div>
                </div>
              )}

              {customFields.length > 0 && (
                <div>
                  <h4 className="text-micro font-medium text-lia-text-secondary mb-2 uppercase tracking-wide">Campos Personalizados</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {customFields.map((field) => (
                      <div
                        key={field.id}
                        className={cn(
                          "flex items-center justify-between p-2 rounded-md border transition-colors",
                          field.enabled
                            ? "bg-lia-bg-primary dark:bg-lia-bg-primary border-wedo-purple/30/50 dark:border-wedo-purple/30/50"
                            : "bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle opacity-60"
                        )}
                      >
                        <div className="flex-1 min-w-0 mr-2">
                          <span className="text-xs font-medium text-lia-text-primary truncate block">{field.displayName}</span>
                          <FieldBadges field={field} />
                        </div>
                        <div className="flex items-center gap-1">
                          {isEditing && (
                            <button
                              onClick={() => removeCustomField(field.id)}
                              className="p-0.5 text-lia-text-tertiary hover:text-status-error transition-colors motion-reduce:transition-none"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                          {isEditing ? (
                            <Switch
                              checked={field.enabled}
                              onCheckedChange={() => toggleFieldEnabled(field.id)}
                              className="scale-75"
                            />
                          ) : (
                            <Badge variant={field.enabled ? "default" : "secondary"} className="text-micro h-4">
                              {field.enabled ? 'Ativo' : 'Inativo'}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {customFields.length === 0 && !isEditing && (
                <p className="text-xs text-lia-text-secondary italic">
                  Nenhum campo personalizado configurado. Clique em &quot;Editar Configurações&quot; para adicionar.
                </p>
              )}
            </div>
          </CollapsibleSection>

          <CollapsibleSection
            id="branding"
            title="Branding do Portal"
            icon={Palette}
            isExpanded={expandedSections.branding}
            onToggle={() => toggleSection('branding')}
          >
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 border border-dashed border-lia-border-default dark:border-lia-border-default rounded-md">
                  <Label className="text-xs font-medium mb-2 block text-lia-text-primary">Logo da Empresa</Label>
                  <div className="flex items-center gap-3">
                    {config.branding.logoUrl ? (
                      <div className="relative w-12 h-12 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md overflow-hidden">
                        <NextImage src={config.branding.logoUrl} alt="Logo" fill className="object-contain" />
                      </div>
                    ) : (
                      <div className="w-12 h-12 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md flex items-center justify-center">
                        <Upload className="w-4 h-4 text-lia-text-tertiary" />
                      </div>
                    )}
                    {isEditing && (
                      <Button variant="outline" size="sm" className="h-7 text-micro">
                        <Upload className="w-3 h-3 mr-1" />
                        Upload
                      </Button>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md">
                  <Label className="text-xs font-medium mb-2 block text-lia-text-primary">Cor Primária</Label>
                  <div className="flex items-center gap-2">
                    {isEditing ? (
                      <>
                        <input
                          type="color"
                          value={config.branding.primaryColor}
                          onChange={(e) => updateBranding({ primaryColor: e.target.value })}
                          className="w-8 h-8 rounded-md border-0 cursor-pointer"
                        />
                        <input
                          type="text"
                          value={config.branding.primaryColor}
                          onChange={(e) => updateBranding({ primaryColor: e.target.value })}
                          className="flex-1 px-2 py-1 text-xs border border-lia-border-default dark:border-lia-border-default rounded-full font-mono uppercase bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-primary"
                        />
                      </>
                    ) : (
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-6 h-6 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle" 
                          style={{backgroundColor: config.branding.primaryColor}}
                        />
                        <span className="text-xs font-mono text-lia-text-primary">{config.branding.primaryColor}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-xs font-medium text-lia-text-primary">Mensagem de Boas-vindas</Label>
                  {isEditing && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => generateLiaSuggestion('welcome')}
                      className="h-6 text-micro px-2 text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-secondary"
                    >
                      <Bot className="w-3 h-3 mr-1" />
                      Sugerir com LIA
                    </Button>
                  )}
                </div>
                {isEditing ? (
                  <textarea
                    value={config.branding.welcomeMessage}
                    onChange={(e) => updateBranding({ welcomeMessage: e.target.value })}
                    rows={2}
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                    placeholder="Mensagem exibida no início do formulário..."
                  />
                ) : (
                  <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md">
                    {config.branding.welcomeMessage}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-xs font-medium text-lia-text-primary">Mensagem de Agradecimento</Label>
                  {isEditing && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => generateLiaSuggestion('thankYou')}
                      className="h-6 text-micro px-2 text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-secondary"
                    >
                      <Bot className="w-3 h-3 mr-1" />
                      Sugerir com LIA
                    </Button>
                  )}
                </div>
                {isEditing ? (
                  <textarea
                    value={config.branding.thankYouMessage}
                    onChange={(e) => updateBranding({ thankYouMessage: e.target.value })}
                    rows={2}
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                    placeholder="Mensagem exibida após o envio do formulário..."
                  />
                ) : (
                  <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md">
                    {config.branding.thankYouMessage}
                  </p>
                )}
              </div>
            </div>
          </CollapsibleSection>
        </CardContent>
      </Card>
    </div>
  )
}

export default DataRequestTab
