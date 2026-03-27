"use client"

import React, { use, useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  MessageSquare,
  Mail,
  Bell,
  Webhook,
  Shield,
  Activity,
  Settings,
  ExternalLink,
  ArrowRight,
  Grid3X3,
  Bot,
  BarChart3,
  Loader2,
  FileText,
  Link as LinkIcon,
  Sun,
  ClipboardCheck
} from "lucide-react"
import Link from "next/link"

interface Template {
  id: string
  name: string
  category: string | null
  subject: string | null
  body_html: string
  body_text: string | null
  channel: string
  situation: string | null
  variables: string[]
  is_active: boolean
  is_system_template: boolean
  origin_template_id: string | null
  version: number
  created_at: string
  updated_at: string
}

const communicationModules = [
  {
    id: 'templates',
    title: 'Templates de Email',
    description: 'Gerenciar templates de comunicação da empresa',
    icon: Mail,
    status: 'active',
    count: 12
  },
  {
    id: 'webhooks',
    title: 'Webhooks',
    description: 'Configurar integrações via webhook',
    icon: Webhook,
    status: 'active',
    count: 3
  },
  {
    id: 'policies',
    title: 'Políticas',
    description: 'Regras e limites de comunicação',
    icon: Shield,
    status: 'active',
    count: 5
  },
  {
    id: 'automations',
    title: 'Automações',
    description: 'Gatilhos automáticos de comunicação',
    icon: Activity,
    status: 'active',
    count: 8
  },
  {
    id: 'matrix',
    title: 'Matriz de Comunicação',
    description: 'Mapeamento de gatilhos e canais',
    icon: Settings,
    status: 'active',
    count: 24
  }
]

const channelFilters = [
  { id: 'email', label: 'Email', icon: Mail, color: 'bg-wedo-orange', hoverColor: 'hover:bg-wedo-orange/10' },
  { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, color: 'bg-status-success', hoverColor: 'hover:bg-status-success' },
  { id: 'bell', label: 'Bell', icon: Bell, color: 'bg-status-warning', hoverColor: 'hover:bg-status-warning' },
  { id: 'teams', label: 'Teams', icon: Grid3X3, color: 'bg-indigo-600', hoverColor: 'hover:bg-indigo-700' },
  { id: 'chat_lia', label: 'Chat LIA', icon: Bot, color: 'bg-gray-900 dark:bg-gray-50', hoverColor: 'hover:bg-gray-800 dark:hover:bg-gray-200' },
  { id: 'report', label: 'Relatórios', icon: BarChart3, color: 'bg-slate-600', hoverColor: 'hover:bg-slate-700' },
  { id: 'briefing', label: 'Briefings', icon: Sun, color: 'bg-status-warning', hoverColor: 'hover:bg-status-warning/10' },
  { id: 'parecer', label: 'Pareceres', icon: ClipboardCheck, color: 'bg-wedo-purple', hoverColor: 'hover:bg-wedo-purple' }
]

const categoryLabels: Record<string, { label: string; color: string }> = {
  approval: { label: 'Aprovação', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  rejection: { label: 'Rejeição', color: 'bg-status-error/10 text-status-error dark:bg-status-error/20 dark:text-status-error' },
  scheduling: { label: 'Agendamento', color: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400' },
  followup: { label: 'Follow-up', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
 feedback: { label: 'Feedback', color: 'bg-gray-50 text-gray-900 dark:bg-gray-800 dark:text-gray-300' },
  system: { label: 'Sistema', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' }
}

export default function ClientComunicacoesPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [channelFilter, setChannelFilter] = useState('email')

  useEffect(() => {
    const fetchTemplates = async () => {
      setLoading(true)
      try {
        const response = await fetch(`/api/backend-proxy/email-templates/?company_id=${clientId}&skip=0&limit=50`)
        if (response.ok) {
          const data = await response.json()
          setTemplates(data.items || [])
        }
      } catch (error) {
        console.error('Error fetching templates:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchTemplates()
  }, [clientId])

  const filteredTemplates = templates.filter(t => t.channel === channelFilter)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <MessageSquare className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 
              className="text-lg font-semibold"
              style={{ color: 'var(--eleven-text-primary)' }}
            >
              Comunicações
            </h2>
          </div>
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Configurações de comunicação do cliente
          </p>
        </div>
        <Link href="/admin/configuracoes/comunicacoes" target="_blank">
          <Button variant="outline" size="sm">
            <ExternalLink className="w-4 h-4 mr-2" />
            Abrir Configurações Globais
          </Button>
        </Link>
      </div>

      <Card className="border-status-warning/30 bg-status-warning/10/50 dark:border-status-warning/30 dark:bg-status-warning/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 text-status-warning mt-0.5" />
            <div>
              <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                Contexto do Cliente: {clientId}
              </p>
              <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                As configurações abaixo são específicas para este cliente. 
                Todas as chamadas de API utilizarão o header X-Company-ID: {clientId}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
                Templates de Comunicação
              </CardTitle>
            </div>
            <Badge variant="outline" className="text-xs">
              {templates.length} templates
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {channelFilters.map((filter) => {
              const Icon = filter.icon
              const isActive = channelFilter === filter.id
              return (
                <Button
                  key={filter.id}
                  variant={isActive ? "default" : "outline"}
                  size="sm"
                  onClick={() => setChannelFilter(filter.id)}
                  className={isActive ? `${filter.color} ${filter.hoverColor} text-white border-0` : ''}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {filter.label}
                </Button>
              )
            })}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-600 dark:text-gray-400" />
              <span className="ml-2 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Carregando templates...
              </span>
            </div>
          ) : filteredTemplates.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Nenhum template encontrado para este canal
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTemplates.map((template) => (
                <div
                  key={template.id}
                  className="p-4 border rounded-md hover:border-gray-900 dark:hover:border-gray-50 transition-colors"
                  style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 
                          className="font-medium"
                          style={{ color: 'var(--eleven-text-primary)' }}
                        >
                          {template.name}
                        </h4>
                        {template.origin_template_id && (
                          <Badge 
                            variant="outline" 
                            className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-900 dark:border-gray-50"
                          >
                            <LinkIcon className="w-3 h-3 mr-1" />
                            🔗 Herdado do Sistema
                          </Badge>
                        )}
                        {template.is_system_template && !template.origin_template_id && (
                          <Badge 
                            variant="outline" 
                            className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30 dark:bg-wedo-purple/20 dark:text-wedo-purple dark:border-wedo-purple/30"
                          >
                            Sistema
                          </Badge>
                        )}
                      </div>
                      {template.subject && (
                        <p className="text-sm mb-2" style={{ color: 'var(--eleven-text-secondary)' }}>
                          {template.subject}
                        </p>
                      )}
                      <div className="flex items-center gap-2">
                        {template.category && categoryLabels[template.category] && (
                          <Badge 
                            variant="secondary" 
                            className={`text-xs ${categoryLabels[template.category].color}`}
                          >
                            {categoryLabels[template.category].label}
                          </Badge>
                        )}
                        <Badge 
                          variant={template.is_active ? "default" : "secondary"}
                          className={`text-xs ${template.is_active ? 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' : 'bg-gray-100 text-gray-500'}`}
                        >
                          {template.is_active ? 'Ativo' : 'Inativo'}
                        </Badge>
                        <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          v{template.version}
                        </span>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {communicationModules.map((module) => {
          const Icon = module.icon
          return (
            <Card 
              key={module.id}
              className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer group"
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {module.count} itens
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <h3 
                  className="font-medium mb-1"
                  style={{ color: 'var(--eleven-text-primary)' }}
                >
                  {module.title}
                </h3>
                <p 
                  className="text-sm mb-3"
                  style={{ color: 'var(--eleven-text-tertiary)' }}
                >
                  {module.description}
                </p>
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400 group-hover:translate-x-1 transition-transform">
                  Configurar
                  <ArrowRight className="w-4 h-4 ml-1" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
            Histórico de Comunicações
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Activity className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              O histórico de comunicações será exibido aqui
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Filtrado por Company ID: {clientId}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
