"use client"

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
  <div className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        <span className={textStyles.subtitle}>{title}</span>
        {count !== undefined && (
          <Badge variant="outline" className="ml-1 text-[10px]">{count} itens</Badge>
        )}
      </div>
      <ChevronDown className={cn(
        "w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform duration-200",
        isExpanded && "rotate-180"
      )} />
    </button>
    {isExpanded && (
      <div className="p-3 bg-white dark:bg-gray-900">
        {children}
      </div>
    )}
  </div>
)

const FieldBadges = ({ field }: { field: DataField }) => (
  <div className="flex items-center gap-1 flex-wrap">
    <Badge variant="outline" className="text-[9px] px-1 py-0 h-4">
      {field.type}
    </Badge>
    {field.isDefault && (
      <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[9px] px-1 py-0 h-4">
        <Database className="w-2.5 h-2.5 mr-0.5" />
        Banco
      </Badge>
    )}
    {field.savesToProfile && (
      <Badge className="bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300 text-[9px] px-1 py-0 h-4">
        <User className="w-2.5 h-2.5 mr-0.5" />
        Cadastro
      </Badge>
    )}
    {field.type === 'file' && (
      <Badge className="bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 text-[9px] px-1 py-0 h-4">
        <File className="w-2.5 h-2.5 mr-0.5" />
        Documento
      </Badge>
    )}
    {!field.isDefault && (
      <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[9px] px-1 py-0 h-4">
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
      <div className="space-y-4">
        <Card className="border-0 rounded-md">
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-8 h-8 text-gray-700 dark:text-gray-300 animate-spin" />
              <p className="text-xs text-gray-500 dark:text-gray-400">Carregando configurações...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <p className="text-[11px] text-amber-700 dark:text-amber-300">
            {error} - Usando configurações padrão.
          </p>
        </div>
      )}
      <Card className="border-0 rounded-md">
        <CardHeader className="pb-3 pt-4 px-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
                <ClipboardList className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                Solicitação de Dados
              </CardTitle>
              <p className={`mt-1 ${textStyles.description}`}>
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
                    className="h-8 text-[11px] px-3"
                  >
                    <X className="w-3.5 h-3.5 mr-1" />
                    Cancelar
                  </Button>
                  <Button 
                    size="sm" 
                    onClick={handleSaveChanges} 
                    disabled={isSaving || !hasChanges}
                    className="h-8 text-[11px] px-3 bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200 text-white dark:text-gray-900"
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
                  className="h-8 text-[11px] px-3"
                >
                  <Pencil className="w-3.5 h-3.5 mr-1" />
                  Editar Configurações
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 px-4 pb-4">
          <div className="flex items-start gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
            <Lightbulb className="w-4 h-4 text-gray-700 dark:text-gray-300 mt-0.5 flex-shrink-0" />
            <div className={textStyles.description}>
              <p className={`mb-0.5 ${textStyles.subtitle}`}>
                Como Funciona
              </p>
              <p>
                Configure os campos que deseja solicitar. O sistema pode enviar solicitações <strong className="text-gray-700 dark:text-gray-300">automaticamente</strong> ou <strong>manualmente</strong>.
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
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                  <div>
                    <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">OTP Obrigatório</Label>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400">Verificação por código</p>
                  </div>
                </div>
                {isEditing ? (
                  <Switch
                    checked={config.otpRequired}
                    onCheckedChange={(checked: boolean) => updateGeneralConfig({ otpRequired: checked })}
                  />
                ) : (
                  <Badge variant={config.otpRequired ? "default" : "secondary"} className="text-[10px]">
                    {config.otpRequired ? 'Ativo' : 'Inativo'}
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <div className="flex items-center gap-2">
                  <Bell className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                  <div>
                    <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Lembretes Automáticos</Label>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400">Enviar lembretes pendentes</p>
                  </div>
                </div>
                {isEditing ? (
                  <Switch
                    checked={config.autoReminders}
                    onCheckedChange={(checked: boolean) => updateGeneralConfig({ autoReminders: checked })}
                  />
                ) : (
                  <Badge variant={config.autoReminders ? "default" : "secondary"} className="text-[10px]">
                    {config.autoReminders ? 'Ativo' : 'Inativo'}
                  </Badge>
                )}
              </div>

              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                  <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Dias para Expiração</Label>
                </div>
                {isEditing ? (
                  <Select
                    value={config.expirationDays.toString()}
                    onValueChange={(value) => updateGeneralConfig({ expirationDays: parseInt(value) })}
                  >
                    <SelectTrigger className="w-full h-8 text-[11px]">
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
                  <p className="text-xs font-medium text-gray-900 dark:text-gray-100">{config.expirationDays} dias</p>
                )}
              </div>

              {config.autoReminders && (
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center gap-2 mb-2">
                    <Bell className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                    <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Enviar Lembrete Após</Label>
                  </div>
                  {isEditing ? (
                    <Select
                      value={config.reminderDays.toString()}
                      onValueChange={(value) => updateGeneralConfig({ reminderDays: parseInt(value) })}
                    >
                      <SelectTrigger className="w-full h-8 text-[11px]">
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
                    <p className="text-xs font-medium text-gray-900 dark:text-gray-100">{config.reminderDays} dia(s)</p>
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
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300 mb-2 block">
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
                          "p-3 rounded-md border-2 text-left transition-all",
                          config.collectionMode === option.value
                            ? "border-gray-900 bg-gray-50 dark:border-gray-50 dark:bg-gray-800"
                            : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <option.icon className={cn(
                            "w-4 h-4",
                            config.collectionMode === option.value ? "text-gray-900 dark:text-gray-50" : "text-gray-400"
                          )} />
                          <span className={cn(
                            "text-[11px] font-medium",
 config.collectionMode === option.value ? "text-gray-900" : "text-gray-700 dark:text-gray-300"
                          )}>
                            {option.label}
                          </span>
                        </div>
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">{option.desc}</p>
                        {option.value === 'candidate_choice' && (
                          <Badge className="mt-1 bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 text-[9px] h-4">Recomendado</Badge>
                        )}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 text-[10px]">
                      {config.collectionMode === 'portal_only' && 'Apenas Portal'}
                      {config.collectionMode === 'chat_only' && 'Apenas Chat'}
                      {config.collectionMode === 'candidate_choice' && 'Candidato Escolhe'}
                    </Badge>
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">
                      {config.collectionMode === 'portal_only' && '- Envia link direto para formulário'}
                      {config.collectionMode === 'chat_only' && '- Coleta via conversa no WhatsApp'}
                      {config.collectionMode === 'candidate_choice' && '- LIA pergunta preferência ao candidato'}
                    </span>
                  </div>
                )}
              </div>

              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <h4 className="text-[11px] font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <Send className="w-3.5 h-3.5 text-gray-700 dark:text-gray-300" />
                  Mensagens do WhatsApp
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-[10px]">
                          Use variáveis: {'{{nome}}'}, {'{{empresa}}'}, {'{{campo}}'}, {'{{proximo_campo}}'}, {'{{campos_pendentes}}'}, {'{{dias_restantes}}'}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </h4>
                <div className="space-y-3">
                  <div>
                    <Label className="text-[10px] text-gray-600 dark:text-gray-400 mb-1 block">Solicitação Inicial</Label>
                    {isEditing ? (
                      <textarea
                        value={config.collectionMessages.initialRequest}
                        onChange={(e) => updateCollectionMessages({ initialRequest: e.target.value })}
                        rows={2}
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      />
                    ) : (
                      <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
                        {config.collectionMessages.initialRequest}
                      </p>
                    )}
                  </div>

                  {(config.collectionMode === 'candidate_choice') && (
                    <div>
                      <Label className="text-[10px] text-gray-600 dark:text-gray-400 mb-1 block">Mensagem de Escolha</Label>
                      {isEditing ? (
                        <textarea
                          value={config.collectionMessages.choicePrompt}
                          onChange={(e) => updateCollectionMessages({ choicePrompt: e.target.value })}
                          rows={3}
                          className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                        />
                      ) : (
                        <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
                          {config.collectionMessages.choicePrompt}
                        </p>
                      )}
                    </div>
                  )}

                  {(config.collectionMode === 'chat_only' || config.collectionMode === 'candidate_choice') && (
                    <>
                      <div>
                        <Label className="text-[10px] text-gray-600 dark:text-gray-400 mb-1 block">Início da Coleta via Chat</Label>
                        {isEditing ? (
                          <textarea
                            value={config.collectionMessages.chatStartMessage}
                            onChange={(e) => updateCollectionMessages({ chatStartMessage: e.target.value })}
                            rows={2}
                            className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                          />
                        ) : (
                          <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
                            {config.collectionMessages.chatStartMessage}
                          </p>
                        )}
                      </div>

                      <div>
                        <Label className="text-[10px] text-gray-600 dark:text-gray-400 mb-1 block">Confirmação de Documento</Label>
                        {isEditing ? (
                          <textarea
                            value={config.collectionMessages.documentReceived}
                            onChange={(e) => updateCollectionMessages({ documentReceived: e.target.value })}
                            rows={1}
                            className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                          />
                        ) : (
                          <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
                            {config.collectionMessages.documentReceived}
                          </p>
                        )}
                      </div>
                    </>
                  )}

                  <div>
                    <Label className="text-[10px] text-gray-600 dark:text-gray-400 mb-1 block">Lembrete de Pendência</Label>
                    {isEditing ? (
                      <textarea
                        value={config.collectionMessages.pendingReminder}
                        onChange={(e) => updateCollectionMessages({ pendingReminder: e.target.value })}
                        rows={2}
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      />
                    ) : (
                      <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
                        {config.collectionMessages.pendingReminder}
                      </p>
                    )}
                  </div>

                  <div>
                    <Label className="text-[10px] text-gray-600 dark:text-gray-400 mb-1 block">Confirmação Final</Label>
                    {isEditing ? (
                      <textarea
                        value={config.collectionMessages.allComplete}
                        onChange={(e) => updateCollectionMessages({ allComplete: e.target.value })}
                        rows={1}
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      />
                    ) : (
                      <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
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
              <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <p className="text-[10px] text-amber-700 dark:text-amber-300">
                    A Lei Geral de Proteção de Dados (Lei nº 13.709/2018) exige consentimento explícito do candidato antes da coleta de dados pessoais.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Exigir Consentimento</Label>
                    {isEditing ? (
                      <Switch
                        checked={config.lgpd.requireConsent}
                        onCheckedChange={(checked: boolean) => updateLgpdConfig({ requireConsent: checked })}
                      />
                    ) : (
                      <Badge variant={config.lgpd.requireConsent ? "default" : "secondary"} className="text-[9px]">
                        {config.lgpd.requireConsent ? 'Obrigatório' : 'Desabilitado'}
                      </Badge>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-500 dark:text-gray-400">Candidato deve autorizar antes de enviar dados</p>
                </div>

                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Permitir Exclusão</Label>
                    {isEditing ? (
                      <Switch
                        checked={config.lgpd.allowDataDeletion}
                        onCheckedChange={(checked: boolean) => updateLgpdConfig({ allowDataDeletion: checked })}
                      />
                    ) : (
                      <Badge variant={config.lgpd.allowDataDeletion ? "default" : "secondary"} className="text-[9px]">
                        {config.lgpd.allowDataDeletion ? 'Habilitado' : 'Desabilitado'}
                      </Badge>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-500 dark:text-gray-400">Candidato pode solicitar exclusão dos dados</p>
                </div>
              </div>

              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300 mb-2 block">
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
                      className="w-20 px-2 py-1 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    />
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">dias após término do processo</span>
                  </div>
                ) : (
                  <p className="text-[11px] text-gray-600 dark:text-gray-400">
                    {config.lgpd.dataRetentionDays} dias após término do processo
                  </p>
                )}
              </div>

              <div>
                <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300 mb-1 block">
                  Mensagem de Consentimento (WhatsApp)
                </Label>
                {isEditing ? (
                  <textarea
                    value={config.lgpd.consentMessage}
                    onChange={(e) => updateLgpdConfig({ consentMessage: e.target.value })}
                    rows={4}
                    className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  />
                ) : (
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
                    {config.lgpd.consentMessage}
                  </p>
                )}
              </div>

              <div>
                <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300 mb-1 block">
                  Disclaimer (Portal)
                </Label>
                {isEditing ? (
                  <textarea
                    value={config.lgpd.disclaimerText}
                    onChange={(e) => updateLgpdConfig({ disclaimerText: e.target.value })}
                    rows={3}
                    className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  />
                ) : (
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md whitespace-pre-wrap">
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
                    <div className="p-3 border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 rounded-md">
                      <h4 className="text-[11px] font-medium mb-2 text-gray-900 dark:text-gray-100">Novo Campo Customizado</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                        <div>
                          <Label className="text-[10px] text-gray-700 dark:text-gray-300">Nome do Campo</Label>
                          <input
                            type="text"
                            value={newFieldName}
                            onChange={(e) => setNewFieldName(e.target.value)}
                            placeholder="Ex: Número do Passaporte"
                            className="w-full mt-1 px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                          />
                        </div>
                        <div>
                          <Label className="text-[10px] text-gray-700 dark:text-gray-300">Tipo</Label>
                          <Select value={newFieldType} onValueChange={(v: any) => setNewFieldType(v)}>
                            <SelectTrigger className="mt-1 h-7 text-[11px]">
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
                          <Button size="sm" onClick={handleAddField} disabled={!newFieldName.trim()} className="h-7 text-[10px] px-2">
                            Adicionar
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => setShowAddField(false)} className="h-7 text-[10px] px-2">
                            Cancelar
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <Button variant="outline" size="sm" onClick={() => setShowAddField(true)} className="h-7 text-[10px]">
                      <Plus className="w-3 h-3 mr-1" />
                      Adicionar Campo
                    </Button>
                  )}
                </>
              )}

              {defaultFields.length > 0 && (
                <div>
                  <h4 className="text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Campos do Sistema</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {defaultFields.map((field) => (
                      <TooltipProvider key={field.id}>
                        <div
                          className={cn(
                            "flex items-center justify-between p-2 rounded-md border transition-colors",
                            field.enabled
                              ? "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600"
                              : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-60"
                          )}
                        >
                          <div className="flex-1 min-w-0 mr-2">
                            <div className="flex items-center gap-1">
                              <span className="text-[11px] font-medium text-gray-900 dark:text-gray-100 truncate">{field.displayName}</span>
                              {field.id === 'cv_document' && (
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Info className="w-3 h-3 text-gray-500 dark:text-gray-400" />
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs">
                                    <p className="text-[10px]">O CV enviado será parseado automaticamente pela LIA para extração de dados estruturados.</p>
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
                            <Badge variant={field.enabled ? "default" : "secondary"} className="text-[9px] h-4">
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
                  <h4 className="text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Campos Personalizados</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {customFields.map((field) => (
                      <div
                        key={field.id}
                        className={cn(
                          "flex items-center justify-between p-2 rounded-md border transition-colors",
                          field.enabled
                            ? "bg-white dark:bg-gray-900 border-purple-300/50 dark:border-purple-700/50"
                            : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-60"
                        )}
                      >
                        <div className="flex-1 min-w-0 mr-2">
                          <span className="text-[11px] font-medium text-gray-900 dark:text-gray-100 truncate block">{field.displayName}</span>
                          <FieldBadges field={field} />
                        </div>
                        <div className="flex items-center gap-1">
                          {isEditing && (
                            <button
                              onClick={() => removeCustomField(field.id)}
                              className="p-0.5 text-gray-400 dark:text-gray-500 hover:text-red-500 transition-colors"
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
                            <Badge variant={field.enabled ? "default" : "secondary"} className="text-[9px] h-4">
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
                <p className="text-[11px] text-gray-500 dark:text-gray-400 italic">
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
                <div className="p-3 border border-dashed border-gray-300 dark:border-gray-600 rounded-md">
                  <Label className="text-[11px] font-medium mb-2 block text-gray-700 dark:text-gray-300">Logo da Empresa</Label>
                  <div className="flex items-center gap-3">
                    {config.branding.logoUrl ? (
                      <div className="relative w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md overflow-hidden">
                        <img src={config.branding.logoUrl} alt="Logo" className="w-full h-full object-contain" />
                      </div>
                    ) : (
                      <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                        <Upload className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                      </div>
                    )}
                    {isEditing && (
                      <Button variant="outline" size="sm" className="h-7 text-[10px]">
                        <Upload className="w-3 h-3 mr-1" />
                        Upload
                      </Button>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <Label className="text-[11px] font-medium mb-2 block text-gray-700 dark:text-gray-300">Cor Primária</Label>
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
                          className="flex-1 px-2 py-1 text-[11px] border border-gray-300 dark:border-gray-600 rounded-full font-mono uppercase bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                        />
                      </>
                    ) : (
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-6 h-6 rounded-md border border-gray-200 dark:border-gray-700" 
                          style={{ backgroundColor: config.branding.primaryColor }}
                        />
                        <span className="text-[11px] font-mono text-gray-700 dark:text-gray-300">{config.branding.primaryColor}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Mensagem de Boas-vindas</Label>
                  {isEditing && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => generateLiaSuggestion('welcome')}
                      className="h-6 text-[10px] px-2 text-gray-600 dark:text-gray-400 hover:text-[#4da8ba] hover:bg-[#F0F9FA]"
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
                    className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    placeholder="Mensagem exibida no início do formulário..."
                  />
                ) : (
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md">
                    {config.branding.welcomeMessage}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label className="text-[11px] font-medium text-gray-700 dark:text-gray-300">Mensagem de Agradecimento</Label>
                  {isEditing && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => generateLiaSuggestion('thankYou')}
                      className="h-6 text-[10px] px-2 text-gray-600 dark:text-gray-400 hover:text-[#4da8ba] hover:bg-[#F0F9FA]"
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
                    className="w-full px-2 py-1.5 text-[11px] border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:border-gray-900 dark:focus:border-gray-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    placeholder="Mensagem exibida após o envio do formulário..."
                  />
                ) : (
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded-md">
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
