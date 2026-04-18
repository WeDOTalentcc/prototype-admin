"use client"

import NextImage from"next/image"
import React from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Switch } from"@/components/ui/switch"
import { Label } from"@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from"@/components/ui/tooltip"
import {
  Plus, Trash2, Upload, Bot, Info, Database, User, File, Brain
} from"lucide-react"
import { cn } from"@/lib/utils"
import type { DataField } from"@/hooks/company/use-data-request-config"

const FieldBadges = ({ field }: { field: DataField }) => (
  <div className="flex items-center gap-1 flex-wrap">
    <Chip variant="neutral" className="text-micro px-1 py-0 h-4">
      {field.type}
    </Chip>
    {field.isDefault && (
      <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro px-1 py-0 h-4">
        <Database className="w-2.5 h-2.5 mr-0.5" />
        Banco
      </Chip>
    )}
    {field.savesToProfile && (
      <Chip variant="neutral" muted className="dark:bg-status-success/30 dark:text-status-success text-micro px-1 py-0 h-4">
        <User className="w-2.5 h-2.5 mr-0.5" />
        Cadastro
      </Chip>
    )}
    {field.type === 'file' && (
      <Chip variant="neutral" muted className="dark:bg-status-warning/30 dark:text-status-warning text-micro px-1 py-0 h-4">
        <File className="w-2.5 h-2.5 mr-0.5" />
        Documento
      </Chip>
    )}
    {!field.isDefault && (
      <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro px-1 py-0 h-4">
        <Brain className="w-2.5 h-2.5 mr-0.5 text-wedo-cyan" />
        Custom
      </Chip>
    )}
  </div>
)

interface DataRequestFieldsSectionProps {
  isEditing: boolean
  fields: DataField[]
  showAddField: boolean
  setShowAddField: (show: boolean) => void
  newFieldName: string
  setNewFieldName: (name: string) => void
  newFieldType: 'text' | 'email' | 'phone' | 'date' | 'file' | 'textarea'
  setNewFieldType: (type: 'text' | 'email' | 'phone' | 'date' | 'file' | 'textarea') => void
  handleAddField: () => void
  toggleFieldEnabled: (id: string) => void
  removeCustomField: (id: string) => void
}

export function DataRequestFieldsSection({
  isEditing,
  fields,
  showAddField,
  setShowAddField,
  newFieldName,
  setNewFieldName,
  newFieldType,
  setNewFieldType,
  handleAddField,
  toggleFieldEnabled,
  removeCustomField,
}: DataRequestFieldsSectionProps) {
  const defaultFields = fields.filter(f => f.isDefault)
  const customFields = fields.filter(f => !f.isDefault)

  return (
    <div className="space-y-3">
      {isEditing && (
        <>
          {showAddField ? (
            <div className="p-3 border border-lia-border-default dark:border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <h4 className="text-xs font-medium mb-2 text-lia-text-primary">Novo Campo Customizado</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                <div>
                  <Label className="text-micro text-lia-text-primary">Nome do Campo</Label>
                  <input
                    type="text"
                    value={newFieldName}
                    onChange={(e) => setNewFieldName(e.target.value)}
                    placeholder="Ex: Número do Passaporte"
                    className="w-full mt-1 px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-xl focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                  />
                </div>
                <div>
                  <Label className="text-micro text-lia-text-primary">Tipo</Label>
                  <Select value={newFieldType} onValueChange={(v) => setNewFieldType(v as"textarea" |"text" |"email" |"phone" |"file" |"date")}>
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
                  className={cn("flex items-center justify-between p-2 rounded-md border transition-colors",
                    field.enabled
                      ?"bg-lia-bg-primary dark:bg-lia-bg-primary border-lia-border-default dark:border-lia-border-default"
                      :"bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle opacity-60"
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
                    <Chip variant="neutral" muted className="text-micro h-4">
                      {field.enabled ? 'Ativo' : 'Inativo'}
                    </Chip>
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
                className={cn("flex items-center justify-between p-2 rounded-md border transition-colors",
                  field.enabled
                    ?"bg-lia-bg-primary dark:bg-lia-bg-primary border-wedo-purple/30/50 dark:border-wedo-purple/30/50"
                    :"bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle opacity-60"
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
                    <Chip variant="neutral" muted className="text-micro h-4">
                      {field.enabled ? 'Ativo' : 'Inativo'}
                    </Chip>
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
  )
}

interface DataRequestBrandingSectionProps {
  isEditing: boolean
  branding: {
    logoUrl: string | null
    primaryColor: string
    welcomeMessage: string
    thankYouMessage: string
  }
  updateBranding: (updates: Partial<DataRequestBrandingSectionProps['branding']>) => void
}

export function DataRequestBrandingSection({
  isEditing,
  branding,
  updateBranding,
}: DataRequestBrandingSectionProps) {
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

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="p-3 border border-dashed border-lia-border-default dark:border-lia-border-default rounded-xl">
          <Label className="text-xs font-medium mb-2 block text-lia-text-primary">Logo da Empresa</Label>
          <div className="flex items-center gap-3">
            {branding.logoUrl ? (
              <div className="relative w-12 h-12 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl overflow-hidden">
                <NextImage src={branding.logoUrl} alt="Logo" fill className="object-contain" />
              </div>
            ) : (
              <div className="w-12 h-12 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
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

        <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
          <Label className="text-xs font-medium mb-2 block text-lia-text-primary">Cor Primária</Label>
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <input
                  type="color"
                  value={branding.primaryColor}
                  onChange={(e) => updateBranding({ primaryColor: e.target.value })}
                  className="w-8 h-8 rounded-md border-0 cursor-pointer"
                />
                <input
                  type="text"
                  value={branding.primaryColor}
                  onChange={(e) => updateBranding({ primaryColor: e.target.value })}
                  className="flex-1 px-2 py-1 text-xs border border-lia-border-default dark:border-lia-border-default rounded-full font-mono uppercase bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-primary"
                />
              </>
            ) : (
              <div className="flex items-center gap-2">
                <div 
                  className="w-6 h-6 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle" 
                  style={{backgroundColor: branding.primaryColor}}
                />
                <span className="text-xs font-mono text-lia-text-primary">{branding.primaryColor}</span>
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
            value={branding.welcomeMessage}
            onChange={(e) => updateBranding({ welcomeMessage: e.target.value })}
            rows={2}
            className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-xl focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
            placeholder="Mensagem exibida no início do formulário..."
          />
        ) : (
          <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-xl">
            {branding.welcomeMessage}
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
            value={branding.thankYouMessage}
            onChange={(e) => updateBranding({ thankYouMessage: e.target.value })}
            rows={2}
            className="w-full px-2 py-1.5 text-xs border border-lia-border-default dark:border-lia-border-default rounded-xl focus:outline-none focus:border-lia-btn-primary-bg dark:focus:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
            placeholder="Mensagem exibida após envio do formulário..."
          />
        ) : (
          <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-xl">
            {branding.thankYouMessage}
          </p>
        )}
      </div>
    </div>
  )
}
