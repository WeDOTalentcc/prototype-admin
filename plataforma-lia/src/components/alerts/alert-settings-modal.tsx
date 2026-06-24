"use client"

import { useState, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  X, Plus, Save, Settings, Bell, BellOff, Edit2, Trash2,
  Clock, Target, Users, DollarSign, Star, AlertTriangle,
  CheckCircle, Info, Mail, Smartphone, Monitor,
  Calendar, RefreshCw, Loader2, MessageSquare
} from"lucide-react"
import { toast } from"sonner"

interface AlertPreference {
  id?: string
  user_id: string
  alert_type: string
  name?: string
  description?: string
  is_enabled: boolean
  threshold?: number
  channels: {
    email: boolean
    bell: boolean
    teams: boolean
    whatsapp: boolean
  }
  cooldown_hours: number
}

interface AlertRule {
  id: string
  name: string
  metric: string
  operator: '>' | '<' | '=' | '>=' | '<='
  threshold: number
  enabled: boolean
  severity: 'critical' | 'warning' | 'info'
  frequency: 'realtime' | 'daily' | 'weekly'
  departments: string[]
  notifications: {
    email: boolean
    push: boolean
    inApp: boolean
  }
  conditions?: {
    consecutiveDays?: number
    minimumVariance?: number
    excludeNewHires?: boolean
  }
}

interface AlertSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  alertRules: AlertRule[]
  onUpdateRules: (rules: AlertRule[]) => void
}

export function AlertSettingsModal({
  isOpen,
  onClose,
  alertRules,
  onUpdateRules
}: AlertSettingsModalProps) {
  const [rules, setRules] = useState<AlertRule[]>(alertRules)
  const [preferences, setPreferences] = useState<AlertPreference[]>([])
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (isOpen) {
      fetchPreferences()
    }
  }, [isOpen])

  useEffect(() => {
    setRules(alertRules)
  }, [alertRules])

  const fetchPreferences = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/alerts/preferences?user_id=default')
      if (response.ok) {
        const data = await response.json()
        setPreferences(data.preferences || [])
      }
    } catch (error) {
    } finally {
      setIsLoading(false)
    }
  }

  const savePreferencesToBackend = async (updatedPrefs: AlertPreference[]) => {
    try {
      const response = await fetch('/api/backend-proxy/alerts/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences: updatedPrefs })
      })
      if (!response.ok) throw new Error('Failed to save preferences')
      return true
    } catch (error) {
      return false
    }
  }

  if (!isOpen) return null

  const metrics = [
    { value: 'avgTimeToFill', label: 'Tempo de Preenchimento (dias)', icon: Clock },
    { value: 'conversionRate', label: 'Taxa de Conversão (%)', icon: Target },
    { value: 'npsScore', label: 'NPS', icon: Star },
    { value: 'totalHires', label: 'Total de Contratações', icon: Users },
    { value: 'qualityOfHireScore', label: 'Score de Qualidade', icon: CheckCircle },
    { value: 'candidateResponseRate', label: 'Taxa de Resposta (%)', icon: Mail },
    { value: 'offerAcceptanceRate', label: 'Taxa de Aceite (%)', icon: CheckCircle },
    { value: 'interviewsPerWeek', label: 'Entrevistas por Semana', icon: Calendar }
  ]

  const departments = ['all', 'Tech', 'Sales', 'Design', 'Marketing', 'Product', 'Leadership']

  const convertRuleToPreference = (rule: AlertRule): AlertPreference => ({
    user_id: 'default',
    alert_type: rule.id.replace(/-/g, '_'),
    name: rule.name,
    is_enabled: rule.enabled,
    threshold: rule.threshold,
    channels: {
      email: rule.notifications.email,
      bell: rule.notifications.inApp,
      teams: false,
      whatsapp: false
    },
    cooldown_hours: rule.frequency === 'realtime' ? 1 : rule.frequency === 'daily' ? 24 : 168
  })

  const handleSaveRules = async () => {
    setIsSaving(true)
    try {
      const prefsToSave = rules.map(convertRuleToPreference)
      const success = await savePreferencesToBackend(prefsToSave)
      if (success) {
        toast.success('Configurações salvas com sucesso')
        onUpdateRules(rules)
        onClose()
      } else {
        toast.error('Erro ao salvar configurações', { description: "O servidor rejeitou as configurações. Verifique os valores e tente novamente." })
      }
    } catch (error) {
      toast.error('Erro ao salvar configurações', { description: "Verifique sua conexão e tente novamente." })
    } finally {
      setIsSaving(false)
    }
  }

  const handleToggleRule = (ruleId: string) => {
    setRules(prev => prev.map(rule =>
      rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
    ))
  }

  const handleDeleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId))
  }

  const handleEditRule = (rule: AlertRule) => {
    setEditingRule({ ...rule })
  }

  const handleSaveEditedRule = () => {
    if (!editingRule) return

    setRules(prev => prev.map(rule =>
      rule.id === editingRule.id ? editingRule : rule
    ))
    setEditingRule(null)
  }

  const handleAddNewRule = () => {
    const newRule: AlertRule = {
      id: `rule-${Date.now()}`,
      name: 'Nova Regra',
      metric: 'avgTimeToFill',
      operator: '>',
      threshold: 30,
      enabled: true,
      severity: 'warning',
      frequency: 'daily',
      departments: ['all'],
      notifications: {
        email: true,
        push: false,
        inApp: true
      },
      conditions: {
        consecutiveDays: 1,
        minimumVariance: 10,
        excludeNewHires: false
      }
    }

    setRules(prev => [...prev, newRule])
    setEditingRule(newRule)
    setShowAddForm(false)
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="w-4 h-4 text-status-error" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-status-warning" />
      case 'info': return <Info className="w-4 h-4 text-lia-text-secondary" />
      default: return <Info className="w-4 h-4 text-lia-text-secondary" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return ' border-status-error/30'
      case 'warning': return ' border-status-warning/30'
      case 'info': return 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default'
      default: return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" data-testid="alert-settings-modal">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl w-full max-w-6xl h-[90vh] flex flex-col dark:border-lia-border-subtle">
        {/* Header */}
        <div className="flex items-center justify-between p-6 dark:border-lia-border-subtle">
          <div>
            <h2 className="text-lg font-semibold text-lia-text-primary">
              Configurações de Alertas KPI
            </h2>
            <p className="text-xs text-lia-text-secondary">
              Gerencie regras de monitoramento e notificações automáticas
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onClose} className="text-xs">
              Cancelar
            </Button>
            <Button 
              onClick={handleSaveRules} 
              disabled={isSaving}
              className="gap-2 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isSaving ? 'Salvando...' : 'Salvar Configurações'}
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 h-full">

            {/* Lista de Regras */}
            <div className="p-6 border-r border-lia-border-subtle dark:border-lia-border-subtle overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-lia-text-primary">Regras de Alerta ({rules.length})</h3>
                <Button
                  size="sm"
                  onClick={handleAddNewRule}
                  className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                >
                  <Plus className="w-4 h-4" />
                  Adicionar Regra
                </Button>
              </div>

              <div className="space-y-3">
                {rules.map((rule) => (
                  <Card
                    key={rule.id}
                    className={`transition-colors motion-reduce:transition-none cursor-pointer hover:${
 editingRule?.id === rule.id ? 'ring-2 ring-lia-btn-primary-bg/20 dark:ring-lia-border-subtle/20' : ''
                    }`}
                    onClick={() => handleEditRule(rule)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-lia-text-primary">{rule.name}</h4>
                          {getSeverityIcon(rule.severity)}
                          <Chip variant="neutral" muted className={`text-xs ${getSeverityColor(rule.severity)}`}>
                            {rule.severity}
                          </Chip>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleToggleRule(rule.id)
                            }}
                            className={`w-8 h-4 rounded-full transition-colors motion-reduce:transition-none ${
 rule.enabled ? 'bg-status-success' : 'bg-lia-border-default'
                            }`}
                          >
                            <div className={`w-3 h-3 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${
 rule.enabled ? 'translate-x-4' : 'translate-x-0.5'
                            }`} />
                          </button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteRule(rule.id)
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>

                      <div className="text-sm text-lia-text-secondary mb-2">
                        {metrics.find(m => m.value === rule.metric)?.label} {rule.operator} {rule.threshold}
                      </div>

                      <div className="flex items-center gap-4 text-xs text-lia-text-secondary">
                        <span className="flex items-center gap-1">
                          <RefreshCw className="w-3 h-3" />
                          {rule.frequency}
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {rule.departments.includes('all') ? 'Todos' : rule.departments.join(', ')}
                        </span>
                        <div className="flex items-center gap-1">
                          {rule.notifications.email && <Mail className="w-3 h-3 text-lia-text-secondary" />}
                          {rule.notifications.push && <Smartphone className="w-3 h-3 text-status-success" />}
                          {rule.notifications.inApp && <Monitor className="w-3 h-3 text-wedo-purple-text" />}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {rules.length === 0 && (
                  <div className="text-center py-8 text-lia-text-secondary">
                    <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-lia-text-secondary" />
                    <p>Nenhuma regra configurada</p>
                    <p className="text-sm">Adicione regras para monitorar KPIs automaticamente</p>
                  </div>
                )}
              </div>
            </div>

            {/* Editor de Regra */}
            <div className="p-6 overflow-y-auto">
              {editingRule ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-lia-text-primary">Editar Regra</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setEditingRule(null)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>

                  {/* Configurações Básicas */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Configurações Básicas</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-lia-text-primary block mb-2">
                          Nome da Regra
                        </label>
                        <input
                          type="text"
                          value={editingRule.name}
                          onChange={(e) => setEditingRule(prev => prev ? { ...prev, name: e.target.value } : null)}
                          className="w-full p-2 border border-lia-border-default rounded-xl"
                          placeholder="Ex: Tempo de Preenchimento Crítico"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium text-lia-text-primary block mb-2">
                          Métrica
                        </label>
                        <select
                          value={editingRule.metric}
                          onChange={(e) => setEditingRule(prev => prev ? { ...prev, metric: e.target.value } : null)}
                          className="w-full p-2 border border-lia-border-default rounded-xl"
                        >
                          {metrics.map(metric => (
                            <option key={metric.value} value={metric.value}>
                              {metric.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-lia-text-primary block mb-2">
                            Operador
                          </label>
                          <select
                            value={editingRule.operator}
                            onChange={(e) => setEditingRule(prev => prev ? { ...prev, operator: e.target.value as AlertRule['operator'] } : null)}
                            className="w-full p-2 border border-lia-border-default rounded-xl"
                          >
                            <option value=">">Maior que (&gt;)</option>
                            <option value="<">Menor que (&lt;)</option>
                            <option value=">=">Maior ou igual (&gt;=)</option>
                            <option value="<=">Menor ou igual (&lt;=)</option>
                            <option value="=">Igual (=)</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-sm font-medium text-lia-text-primary block mb-2">
                            Valor Limite
                          </label>
                          <input
                            type="number"
                            value={editingRule.threshold}
                            onChange={(e) => setEditingRule(prev => prev ? { ...prev, threshold: Number(e.target.value) } : null)}
                            className="w-full p-2 border border-lia-border-default rounded-xl"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-lia-text-primary block mb-2">
                            Severidade
                          </label>
                          <select
                            value={editingRule.severity}
                            onChange={(e) => setEditingRule(prev => prev ? { ...prev, severity: e.target.value as AlertRule['severity'] } : null)}
                            className="w-full p-2 border border-lia-border-default rounded-xl"
                          >
                            <option value="critical">Crítico</option>
                            <option value="warning">Aviso</option>
                            <option value="info">Informação</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-sm font-medium text-lia-text-primary block mb-2">
                            Frequência
                          </label>
                          <select
                            value={editingRule.frequency}
                            onChange={(e) => setEditingRule(prev => prev ? { ...prev, frequency: e.target.value as AlertRule['frequency'] } : null)}
                            className="w-full p-2 border border-lia-border-default rounded-xl"
                          >
                            <option value="realtime">Tempo Real</option>
                            <option value="daily">Diário</option>
                            <option value="weekly">Semanal</option>
                          </select>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Departamentos */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Departamentos</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {departments.map(dept => (
                          <label key={dept} className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={editingRule.departments.includes(dept)}
                              onChange={(e) => {
                                const newDepts = e.target.checked
                                  ? [...editingRule.departments, dept]
                                  : editingRule.departments.filter(d => d !== dept)
                                setEditingRule(prev => prev ? { ...prev, departments: newDepts } : null)
                              }}
                              className="rounded-md"
                            />
                            <span className="text-sm">
                              {dept === 'all' ? 'Todos os Departamentos' : dept}
                            </span>
                          </label>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Notificações */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Notificações</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <label className="flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <Mail className="w-4 h-4 text-lia-text-secondary" />
                            Email
                          </span>
                          <button
                            onClick={() => setEditingRule(prev => prev ? {
                              ...prev,
                              notifications: { ...prev.notifications, email: !prev.notifications.email }
                            } : null)}
                            className={`w-8 h-4 rounded-full transition-colors motion-reduce:transition-none ${
 editingRule.notifications.email ? 'bg-status-success' : 'bg-lia-border-default'
                            }`}
                          >
                            <div className={`w-3 h-3 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${
 editingRule.notifications.email ? 'translate-x-4' : 'translate-x-0.5'
                            }`} />
                          </button>
                        </label>

                        <label className="flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <Smartphone className="w-4 h-4 text-status-success" />
                            Push Notification
                          </span>
                          <button
                            onClick={() => setEditingRule(prev => prev ? {
                              ...prev,
                              notifications: { ...prev.notifications, push: !prev.notifications.push }
                            } : null)}
                            className={`w-8 h-4 rounded-full transition-colors motion-reduce:transition-none ${
 editingRule.notifications.push ? 'bg-status-success' : 'bg-lia-border-default'
                            }`}
                          >
                            <div className={`w-3 h-3 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${
 editingRule.notifications.push ? 'translate-x-4' : 'translate-x-0.5'
                            }`} />
                          </button>
                        </label>

                        <label className="flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <Monitor className="w-4 h-4 text-wedo-purple" />
                            No Sistema
                          </span>
                          <button
                            onClick={() => setEditingRule(prev => prev ? {
                              ...prev,
                              notifications: { ...prev.notifications, inApp: !prev.notifications.inApp }
                            } : null)}
                            className={`w-8 h-4 rounded-full transition-colors motion-reduce:transition-none ${
 editingRule.notifications.inApp ? 'bg-status-success' : 'bg-lia-border-default'
                            }`}
                          >
                            <div className={`w-3 h-3 bg-lia-bg-secondary rounded-full transition-transform motion-reduce:transition-none ${
 editingRule.notifications.inApp ? 'translate-x-4' : 'translate-x-0.5'
                            }`} />
                          </button>
                        </label>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Ações */}
                  <div className="flex gap-2">
                    <Button
                      onClick={handleSaveEditedRule}
                      className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                    >
                      <Save className="w-4 h-4" />
                      Salvar Regra
                    </Button>

                    <Button
                      variant="outline"
                      onClick={() => setEditingRule(null)}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-lia-text-secondary">
                  <Settings className="w-12 h-12 mx-auto mb-4 text-lia-text-secondary" />
                  <p className="dark:text-lia-text-secondary">Selecione uma regra para editar</p>
                  <p className="text-sm">ou adicione uma nova regra para começar</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
