'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Mail, Clock, Edit, Save, X, Eye, Trash2, Plus, Bell,
  Loader2, FileText, RefreshCw, Users, Send, Grid3X3,
  Bot, BarChart3, ClipboardCheck
} from "lucide-react"
import type { SystemTemplate, TemplateChannelFilter } from './types'
import { categoryLabels } from './constants'
import { stripHtmlToText } from './mappers'

interface TemplatesSectionProps {
  systemTemplates: SystemTemplate[]
  templateChannelFilter: TemplateChannelFilter
  setTemplateChannelFilter: (filter: TemplateChannelFilter) => void
  selectedTemplate: SystemTemplate | null
  setSelectedTemplate: (template: SystemTemplate | null) => void
  editingTemplate: SystemTemplate | null
  setEditingTemplate: (template: SystemTemplate | null) => void
  templatesLoading: boolean
  savingTemplate: boolean
  publishingTemplate: string | null
  showHtmlView: boolean
  setShowHtmlView: (show: boolean) => void
  fetchTemplates: () => void
  handleCreateTemplate: () => void
  handleSaveTemplate: () => void
  handleDeleteTemplate: (id: string) => void
  handleToggleTemplateActive: (id: string) => void
  handlePublishTemplate: (id: string) => void
}

export function TemplatesSection({
  systemTemplates,
  templateChannelFilter,
  setTemplateChannelFilter,
  selectedTemplate,
  setSelectedTemplate,
  editingTemplate,
  setEditingTemplate,
  templatesLoading,
  savingTemplate,
  publishingTemplate,
  showHtmlView,
  setShowHtmlView,
  fetchTemplates,
  handleCreateTemplate,
  handleSaveTemplate,
  handleDeleteTemplate,
  handleToggleTemplateActive,
  handlePublishTemplate
}: TemplatesSectionProps) {
  const filteredTemplates = systemTemplates.filter(t => t.channel === templateChannelFilter)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button
            variant={templateChannelFilter === 'email' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('email')}
            className={templateChannelFilter === 'email' ? 'bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200 text-white dark:text-gray-900' : ''}
          >
            <Mail className="w-4 h-4 mr-2" />
            Email
          </Button>
          <Button
            variant={templateChannelFilter === 'whatsapp' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('whatsapp')}
            className={templateChannelFilter === 'whatsapp' ? 'bg-status-success hover:bg-status-success' : ''}
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
            WhatsApp
          </Button>
          <Button
            variant={templateChannelFilter === 'bell' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('bell')}
            className={templateChannelFilter === 'bell' ? 'bg-status-warning hover:bg-status-warning text-white' : ''}
          >
            <Bell className="w-4 h-4 mr-2" />
            Notificações
          </Button>
          <Button
            variant={templateChannelFilter === 'teams' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('teams')}
            className={templateChannelFilter === 'teams' ? 'bg-wedo-purple hover:bg-wedo-purple text-white' : ''}
          >
            <Grid3X3 className="w-4 h-4 mr-2" />
            Teams
          </Button>
          <Button
            variant={templateChannelFilter === 'chat_lia' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('chat_lia')}
            className={templateChannelFilter === 'chat_lia' ? 'bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200' : ''}
          >
            <Bot className="w-4 h-4 mr-2" />
            Chat LIA
          </Button>
          <Button
            variant={templateChannelFilter === 'report' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('report')}
            className={templateChannelFilter === 'report' ? 'bg-slate-600 hover:bg-slate-700 text-white' : ''}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            Relatórios
          </Button>
          <Button
            variant={templateChannelFilter === 'briefing' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('briefing')}
            className={templateChannelFilter === 'briefing' ? 'bg-status-warning hover:bg-status-warning/80 text-white' : ''}
          >
            <ClipboardCheck className="w-4 h-4 mr-2" />
            Briefings
          </Button>
          <Button
            variant={templateChannelFilter === 'parecer' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTemplateChannelFilter('parecer')}
            className={templateChannelFilter === 'parecer' ? 'bg-wedo-purple hover:bg-wedo-purple text-white' : ''}
          >
            <FileText className="w-4 h-4 mr-2" />
            Pareceres
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchTemplates}
            disabled={templatesLoading}
          >
            <RefreshCw className={`w-4 h-4 ${templatesLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <Button
          size="sm"
          className="bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200"
          onClick={handleCreateTemplate}
          disabled={templatesLoading}
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Template
        </Button>
      </div>

      {templatesLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-700 dark:text-gray-300" />
          <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
            Carregando templates...
          </span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h3 className="text-sm font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
              Templates Disponíveis ({filteredTemplates.length})
            </h3>
            {filteredTemplates.length === 0 ? (
              <Card className="flex flex-col items-center justify-center py-12">
                <FileText className="w-12 h-12 mb-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Nenhum template encontrado
                </p>
                <p className="text-xs mb-4" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Crie um novo template para começar
                </p>
                <Button
                  size="sm"
                  className="bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200"
                  onClick={handleCreateTemplate}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Criar Template
                </Button>
              </Card>
            ) : (
              filteredTemplates.map(template => (
                <Card
                  key={template.id}
                  className={`cursor-pointer transition-all ${selectedTemplate?.id === template.id ? 'ring-2 ring-gray-900/20 dark:ring-gray-50/20' : 'hover:border-gray-300'}`}
                  onClick={() => {
                    setSelectedTemplate(template)
                    setEditingTemplate(null)
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                            {template.name}
                          </h4>
                          <Badge className={`text-xs ${categoryLabels[template.category]?.color || categoryLabels.system.color}`}>
                            {categoryLabels[template.category]?.label || 'Sistema'}
                          </Badge>
                        </div>
                        {template.subject && (
                          <p className="text-xs mb-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            {template.subject}
                          </p>
                        )}
                        <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {template.usedByCompanies} empresas
                          </span>
                          <span>Atualizado: {template.lastUpdated}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={template.isActive}
                          onCheckedChange={() => handleToggleTemplateActive(template.id)}
                          onClick={(e: React.MouseEvent) => e.stopPropagation()}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          <div>
            {editingTemplate ? (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      {editingTemplate.id ? 'Editando Template' : 'Novo Template'}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => setEditingTemplate(null)} disabled={savingTemplate}>
                        <X className="w-4 h-4 mr-1" /> Cancelar
                      </Button>
                      <Button 
                        size="sm" 
                        className="bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200" 
                        onClick={handleSaveTemplate}
                        disabled={savingTemplate}
                      >
                        {savingTemplate ? (
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4 mr-1" />
                        )}
                        Salvar
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Nome</label>
                    <Input
                      value={editingTemplate.name}
                      onChange={(e) => setEditingTemplate({ ...editingTemplate, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Categoria</label>
                    <select
                      className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
                      value={editingTemplate.category}
                      onChange={(e) => setEditingTemplate({ ...editingTemplate, category: e.target.value as SystemTemplate['category'] })}
                    >
                      {Object.entries(categoryLabels).map(([key, { label }]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </div>
                  {editingTemplate.channel === 'email' && (
                    <div>
                      <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Assunto</label>
                      <Input
                        value={editingTemplate.subject}
                        onChange={(e) => setEditingTemplate({ ...editingTemplate, subject: e.target.value })}
                      />
                    </div>
                  )}
                  <div>
                    <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Corpo da Mensagem</label>
                    <Textarea
                      value={editingTemplate.body}
                      onChange={(e) => setEditingTemplate({ ...editingTemplate, body: e.target.value })}
                      rows={10}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
                      Variáveis (separadas por vírgula)
                    </label>
                    <Input
                      value={editingTemplate.variables.join(', ')}
                      onChange={(e) => setEditingTemplate({
                        ...editingTemplate,
                        variables: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
                      })}
                      placeholder="candidato_nome, vaga, empresa_nome"
                    />
                  </div>
                </CardContent>
              </Card>
            ) : selectedTemplate ? (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{selectedTemplate.name}</CardTitle>
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={() => handlePublishTemplate(selectedTemplate.id)}
                        disabled={publishingTemplate === selectedTemplate.id || !selectedTemplate.isActive}
                        title={!selectedTemplate.isActive ? 'Ative o template para publicar' : 'Publicar para todas as empresas'}
                      >
                        {publishingTemplate === selectedTemplate.id ? (
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4 mr-1" />
                        )}
                        Publicar
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setEditingTemplate(selectedTemplate)}>
                        <Edit className="w-4 h-4 mr-1" /> Editar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-status-error hover:text-status-error hover:bg-status-error/10"
                        onClick={() => handleDeleteTemplate(selectedTemplate.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge className={`text-xs ${categoryLabels[selectedTemplate.category]?.color || categoryLabels.system.color}`}>
                      {categoryLabels[selectedTemplate.category]?.label || 'Sistema'}
                    </Badge>
                    <Badge variant={selectedTemplate.isActive ? 'default' : 'secondary'} className="text-xs">
                      {selectedTemplate.isActive ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </div>
                  {selectedTemplate.subject && (
                    <div>
                      <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Assunto</label>
                      <p className="text-sm mt-1 p-2 bg-gray-50 dark:bg-gray-800 rounded" style={{ color: 'var(--eleven-text-primary)' }}>
                        {selectedTemplate.subject}
                      </p>
                    </div>
                  )}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Corpo da Mensagem</label>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setShowHtmlView(!showHtmlView)}
                        className="h-6 px-2 text-xs"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        {showHtmlView ? 'Ver Texto' : 'Ver HTML'}
                      </Button>
                    </div>
                    <pre className="text-sm p-3 bg-gray-50 dark:bg-gray-800 rounded whitespace-pre-wrap max-h-96 overflow-y-auto" style={{ color: 'var(--eleven-text-primary)', fontFamily: 'inherit' }}>
                      {showHtmlView ? selectedTemplate.body : stripHtmlToText(selectedTemplate.body)}
                    </pre>
                  </div>
                  <div>
                    <label className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Variáveis Disponíveis</label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedTemplate.variables.length > 0 ? (
                        selectedTemplate.variables.map(v => (
                          <Badge key={v} variant="outline" className="text-xs">
                            {`{{${v}}}`}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          Nenhuma variável definida
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="flex items-center justify-center h-64">
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Selecione um template para visualizar
                </p>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
