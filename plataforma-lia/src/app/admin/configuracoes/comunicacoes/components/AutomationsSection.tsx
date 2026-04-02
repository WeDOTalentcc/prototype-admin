'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
  Clock, Edit, Plus, Eye, Loader2, FileText,
  RefreshCw, Activity, AlertTriangle, Play, Zap,
  Calendar, MessageSquare, UserCheck, Users, Gift, ClipboardCheck
} from "lucide-react"
import type { AutomationRule } from './types'

const getAutomationIcon = (trigger: string) => {
  if (trigger.includes('screening')) return ClipboardCheck
  if (trigger.includes('interview')) return Calendar
  if (trigger.includes('no_show')) return AlertTriangle
  if (trigger.includes('feedback')) return MessageSquare
  if (trigger.includes('offer')) return Gift
  if (trigger.includes('application')) return UserCheck
  if (trigger.includes('welcome')) return Users
  return Zap
}

const getActionLabel = (action: string) => {
  switch (action) {
    case 'send_email': return { label: 'Email', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary' }
    case 'send_whatsapp': return { label: 'WhatsApp', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' }
    case 'notify_recruiter': return { label: 'Notificação', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' }
    default: return { label: action, color: 'bg-lia-bg-secondary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-tertiary' }
  }
}

const formatLastTriggered = (dateStr?: string) => {
  if (!dateStr) return 'Nunca disparada'
  const date = new Date(dateStr)
  return date.toLocaleDateString('pt-BR', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

interface AutomationsSectionProps {
  automations: AutomationRule[]
  automationsLoading: boolean
  selectedAutomation: AutomationRule | null
  setSelectedAutomation: (automation: AutomationRule | null) => void
  togglingAutomation: string | null
  fetchAutomations: () => void
  handleToggleAutomationActive: (id: string) => void
  handleSeedDefaultAutomations: () => void
}

export function AutomationsSection({
  automations,
  automationsLoading,
  selectedAutomation,
  setSelectedAutomation,
  togglingAutomation,
  fetchAutomations,
  handleToggleAutomationActive,
  handleSeedDefaultAutomations
}: AutomationsSectionProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >
            Catálogo de Automações ({automations.length})
          </h3>
          <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
            Configure automações para disparar comunicações automaticamente
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchAutomations}
            disabled={automationsLoading}
          >
            <RefreshCw className={`w-4 h-4 ${automationsLoading ? 'animate-spin motion-reduce:animate-none' : ''}`} />
          </Button>
          <Badge variant="outline" className="text-xs">
            <Activity className="w-3 h-3 mr-1" />
            {automations.filter(a => a.isActive).length} ativas
          </Badge>
        </div>
      </div>

      {automationsLoading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-primary dark:text-lia-text-secondary" />
          <span className="ml-3 text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
            Carregando automações...
          </span>
        </div>
      ) : automations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Zap className="w-12 h-12 text-lia-text-disabled mb-4" />
          <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
            Nenhuma automação encontrada
          </p>
          <p className="text-xs mt-1 mb-4 text-lia-text-tertiary dark:text-lia-text-secondary" >
            Crie automações padrão para começar
          </p>
          <Button
            onClick={handleSeedDefaultAutomations}
            disabled={automationsLoading}
            className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
          >
            <Plus className="w-4 h-4 mr-2" />
            Criar Automações Padrão
          </Button>
        </div>
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {automations.map(automation => {
          const IconComponent = getAutomationIcon(automation.trigger)
          const actionInfo = getActionLabel(automation.action)
          
          return (
            <Card
              key={automation.id}
              className={`cursor-pointer transition-colors motion-reduce:transition-none ${selectedAutomation?.id === automation.id ? 'ring-2 ring-lia-btn-primary-bg/20 dark:ring-lia-border-subtle/20' : 'hover:border-lia-border-default'}`}
              onClick={() => setSelectedAutomation(selectedAutomation?.id === automation.id ? null : automation)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <div 
                        className="w-8 h-8 rounded-md flex items-center justify-center"
                        style={{backgroundColor: automation.isActive ? 'var(--status-warning-bg)' : 'var(--lia-bg-secondary)'}}
                      >
                        <IconComponent
                          className={`w-4 h-4 ${automation.isActive ? 'text-status-warning' : 'lia-text-400 dark:text-lia-text-secondary'}`}
                        />
                      </div>
                      <div>
                        <h4 className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                          {automation.name}
                        </h4>
                      </div>
                    </div>
                    
                    <p className="text-xs mb-3 text-lia-text-tertiary dark:text-lia-text-secondary" >
                      {automation.description}
                    </p>
                    
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <Badge variant="outline" className="text-xs">
                        <Zap className="w-3 h-3 mr-1" />
                        {automation.trigger}
                      </Badge>
                      <Badge className={`text-xs ${actionInfo.color}`}>
                        {actionInfo.label}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                      <span className="flex items-center gap-1">
                        <Play className="w-3 h-3" />
                        {automation.triggerCount.toLocaleString('pt-BR')} disparos
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatLastTriggered(automation.lastTriggered)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation()
                        setSelectedAutomation(automation)
                      }}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Switch
                      checked={automation.isActive}
                      onCheckedChange={() => handleToggleAutomationActive(automation.id)}
                      onClick={(e: React.MouseEvent) => e.stopPropagation()}
                      disabled={togglingAutomation === automation.id}
                    />
                  </div>
                </div>

                {selectedAutomation?.id === automation.id && (
                  <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle" >
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >
                          Condições de Disparo
                        </label>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {automation.conditions?.map((condition, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {condition}
                            </Badge>
                          )) || (
                            <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                              Nenhuma condição definida
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {automation.templateId && (
                        <div>
                          <label className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary" >
                            Template Vinculado
                          </label>
                          <Badge variant="outline" className="text-xs mt-1">
                            <FileText className="w-3 h-3 mr-1" />
                            {automation.templateId}
                          </Badge>
                        </div>
                      )}

                      <div className="flex gap-2 pt-2">
                        <Button size="sm" variant="outline" className="flex-1">
                          <Eye className="w-4 h-4 mr-1" />
                          Visualizar Template
                        </Button>
                        <Button size="sm" variant="outline" className="flex-1">
                          <Activity className="w-4 h-4 mr-1" />
                          Ver Histórico
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
      )}
    </div>
  )
}
