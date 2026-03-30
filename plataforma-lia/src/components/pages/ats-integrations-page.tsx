"use client"

import { textStyles, cardStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Link2, Settings, Activity, CheckCircle, AlertTriangle, XCircle,
  Plus, Play, RotateCw, Eye, Edit, Trash2, Download,
  Upload, FileText, BarChart3, Calendar, Clock, Users,
  Database, Server, Wifi, Shield, Key, Globe, Zap, Target,
  ArrowRight, ArrowUp, ArrowDown, Minus, Search, Filter,
  Bell, Mail, Smartphone, MessageSquare, RefreshCw, Copy,
  ExternalLink, Code, GitBranch, HardDrive, CloudUpload,
  AlertCircle, Info, CheckCircle2, TrendingUp, Lock, Crown,
  MoreHorizontal
} from "lucide-react"
import { useAtsIntegrations, useSystemModal } from './ats-integrations/useAtsIntegrations'
import type { ATSSystem, SystemConfigurationModalProps, ViewTab } from './ats-integrations/ats-integrations.types'

// ── Status helpers ────────────────────────────────────────────────────────────
function getStatusIcon(status: string) {
  switch (status) {
    case 'connected': return <CheckCircle className="w-4 h-4 text-status-success" />
    case 'connecting': return <RotateCw className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
    case 'error': return <XCircle className="w-4 h-4 text-status-error" />
    case 'disabled': return <Minus className="w-4 h-4 text-lia-text-secondary" />
    default: return <AlertTriangle className="w-4 h-4 text-status-warning" />
  }
}

function getSyncStatusIcon(status: string) {
  switch (status) {
    case 'success': return <CheckCircle2 className="w-4 h-4 text-status-success" />
    case 'warning': return <AlertTriangle className="w-4 h-4 text-status-warning" />
    case 'error': return <XCircle className="w-4 h-4 text-status-error" />
    default: return <Info className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'connected': return 'Conectado'
    case 'connecting': return 'Conectando'
    case 'error': return 'Erro'
    default: return 'Desabilitado'
  }
}

// ── Sub-views ─────────────────────────────────────────────────────────────────
interface OverviewProps {
  atsSystems: ATSSystem[]
  integrations: { isActive: boolean }[]
  syncLogs: { id: string; message: string; system: string; timestamp: string; records: number; duration: number; status: string }[]
  getStatusColor: (s: string) => string
  setSelectedView: (v: ViewTab) => void
  openSystemModal: (system: ATSSystem) => void
}

function OverviewView({ atsSystems, integrations, syncLogs, getStatusColor, setSelectedView, openSystemModal }: OverviewProps) {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={textStyles.label}>Sistemas Conectados</p>
                <p className={`${textStyles.titleXl} text-2xl`}>
                  {atsSystems.filter(s => s.status === 'connected').length}
                </p>
                <p className={textStyles.caption}>de {atsSystems.length} configurados</p>
              </div>
              <div className="w-12 h-12 bg-status-success/15 rounded-md flex items-center justify-center" aria-live="polite" aria-atomic="true">
                <Link2 className="w-6 h-6 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={textStyles.label}>Registros Sincronizados</p>
                <p className={`${textStyles.titleXl} text-2xl text-lia-text-secondary dark:text-lia-text-secondary`}>
                  {atsSystems.reduce((acc, sys) => acc + sys.syncedRecords, 0).toLocaleString()}
                </p>
                <p className={`${textStyles.caption} text-status-success`}>+47 hoje</p>
              </div>
              <div className="w-12 h-12 bg-lia-bg-secondary rounded-md flex items-center justify-center">
                <Database className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={textStyles.label}>Integrações Ativas</p>
                <p className={`${textStyles.titleXl} text-2xl text-wedo-purple`}>
                  {integrations.filter(i => i.isActive).length}
                </p>
                <p className={textStyles.caption}>de {integrations.length} total</p>
              </div>
              <div className="w-12 h-12 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <Zap className="w-6 h-6 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={textStyles.label}>Uptime Médio</p>
                <p className={`${textStyles.titleXl} text-2xl text-wedo-orange`}>99.7%</p>
                <p className={`${textStyles.caption} text-wedo-orange`}>últimos 30 dias</p>
              </div>
              <div className="w-12 h-12 bg-wedo-orange/15 rounded-md flex items-center justify-center">
                <Activity className="w-6 h-6 text-wedo-orange" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xs font-sans">Ações Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4 justify-start gap-3" onClick={() => setSelectedView('systems')}>
              <Plus className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              <div className="text-left">
                <div className="font-medium">Adicionar Sistema</div>
                <div className="text-sm text-lia-text-secondary">Conectar novo ATS</div>
              </div>
            </Button>
            <Button variant="outline" className="h-auto p-4 justify-start gap-3" onClick={() => setSelectedView('integrations')}>
              <Settings className="w-5 h-5 text-wedo-purple" />
              <div className="text-left">
                <div className="font-medium">Configurar Sync</div>
                <div className="text-sm text-lia-text-secondary">Gerenciar integrações</div>
              </div>
            </Button>
            <Button variant="outline" className="h-auto p-4 justify-start gap-3" onClick={() => setSelectedView('logs')}>
              <FileText className="w-5 h-5 text-wedo-orange" />
              <div className="text-left">
                <div className="font-medium">Ver Logs</div>
                <div className="text-sm text-lia-text-secondary">Histórico de operações</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Systems Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xs font-sans">Status dos Sistemas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {atsSystems.map(system => (
              <div key={system.id} className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-lia-bg-secondary rounded-md flex items-center justify-center">
                    <Server className="w-6 h-6 text-lia-text-secondary" />
                  </div>
                  <div>
                    <h4 className={textStyles.subtitle}>{system.name}</h4>
                    <p className={textStyles.bodySmall}>{system.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(system.status)}
                      <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(system.status)}`}>
                        {getStatusLabel(system.status)}
                      </span>
                      {system.lastSync && (
                        <span className="text-xs text-lia-text-secondary">
                          Última sync: {new Date(system.lastSync).toLocaleString('pt-BR')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  {system.status === 'connected' && (
                    <>
                      <div className="text-center">
                        <p className={textStyles.subtitle}>{system.syncedRecords}</p>
                        <p className={textStyles.caption}>Registros</p>
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-status-success">
                          {Math.round((system.syncedRecords / system.totalRecords) * 100)}%
                        </p>
                        <p className="text-lia-text-secondary">Sincronizado</p>
                      </div>
                    </>
                  )}
                  <Button variant="outline" size="sm" onClick={() => openSystemModal(system)}>
                    Configurar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Sync Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xs font-sans">Logs Recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {syncLogs.slice(0, 5).map(log => (
              <div key={log.id} className="flex items-center justify-between p-3 bg-lia-bg-secondary rounded-md">
                <div className="flex items-center gap-3">
                  {getSyncStatusIcon(log.status)}
                  <div>
                    <p className={textStyles.subtitle}>{log.message}</p>
                    <p className={textStyles.caption}>
                      {log.system} • {new Date(log.timestamp).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>
                <div className="text-right text-xs text-lia-text-secondary">
                  <p>{log.records} registros</p>
                  <p>{log.duration}ms</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t">
            <Button variant="outline" size="sm" onClick={() => setSelectedView('logs')} className="w-full">
              Ver Todos os Logs
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function SystemsView({ atsSystems, getStatusColor, openSystemModal }: {
  atsSystems: ATSSystem[]
  getStatusColor: (s: string) => string
  openSystemModal: (system: ATSSystem) => void
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>Sistemas ATS Disponíveis</h3>
          <p className={textStyles.body}>Configure e gerencie conexões com sistemas externos</p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Adicionar Sistema Personalizado
        </Button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {atsSystems.map(system => (
          <Card key={system.id} className={cardStyles.interactive}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-lia-bg-secondary rounded-md flex items-center justify-center">
                    <Server className="w-6 h-6 text-lia-text-secondary" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{system.name}</CardTitle>
                    <p className="text-sm text-lia-text-secondary">{system.type.toUpperCase()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(system.status)}
                  <Badge
                    variant={system.status === 'connected' ? 'default' : system.status === 'connecting' ? 'secondary' : system.status === 'error' ? 'destructive' : 'outline'}
                    className="text-xs"
                    aria-live="polite"
                  >
                    {getStatusLabel(system.status)}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className={textStyles.body}>{system.description}</p>
                <div>
                  <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">Funcionalidades:</p>
                  <div className="flex flex-wrap gap-1">
                    {system.features.map(feature => (
                      <Badge key={feature} variant="outline" className="text-xs">{feature}</Badge>
                    ))}
                  </div>
                </div>
                {system.status === 'connected' && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-lia-text-secondary">Registros sincronizados:</p>
                      <p className="font-medium">{system.syncedRecords.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-lia-text-secondary">Última sincronização:</p>
                      <p className="font-medium">{system.lastSync ? new Date(system.lastSync).toLocaleString('pt-BR') : 'N/A'}</p>
                    </div>
                    {system.version && (
                      <div>
                        <p className="text-lia-text-secondary">Versão da API:</p>
                        <p className="font-medium">{system.version}</p>
                      </div>
                    )}
                    {system.errorCount > 0 && (
                      <div>
                        <p className="text-lia-text-secondary">Erros:</p>
                        <p className="font-medium text-status-error">{system.errorCount}</p>
                      </div>
                    )}
                  </div>
                )}
                {system.status === 'error' && (
                  <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-md" aria-live="polite" aria-atomic="true">
                    <p className="text-sm text-status-error">
                      <AlertTriangle className="w-4 h-4 inline mr-1" />
                      Token de acesso expirado - requer renovação manual
                    </p>
                  </div>
                )}
                <div className="flex gap-2">
                  {system.status === 'disabled' ? (
                    <Button size="sm" onClick={() => openSystemModal(system)} className="flex-1">Configurar Conexão</Button>
                  ) : (
                    <>
                      <Button size="sm" variant="outline" onClick={() => openSystemModal(system)} className="flex-1">
                        <Settings className="w-4 h-4 mr-2" />Configurar
                      </Button>
                      {system.status === 'connected' && (
                        <Button size="sm" variant="outline" className="flex-1">
                          <RefreshCw className="w-4 h-4 mr-2" />Sincronizar
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function IntegrationsView({ integrations }: { integrations: ReturnType<typeof useAtsIntegrations>['integrations'] }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>Integrações Ativas</h3>
          <p className={textStyles.body}>Gerencie sincronizações e mapeamentos de dados</p>
        </div>
        <Button className="gap-2"><Plus className="w-4 h-4" />Nova Integração</Button>
      </div>
      <div className="space-y-4">
        {integrations.map(integration => (
          <Card key={integration.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-md flex items-center justify-center ${integration.isActive ? 'bg-status-success/15' : 'bg-lia-bg-secondary'}`}>
                    <Database className={`w-6 h-6 ${integration.isActive ? 'text-status-success' : 'text-lia-text-secondary'}`} />
                  </div>
                  <div>
                    <h4 className={textStyles.subtitle}>{integration.name}</h4>
                    <p className={textStyles.bodySmall}>{integration.system.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={integration.isActive ? "default" : "secondary"} className="text-xs">
                        {integration.isActive ? 'Ativa' : 'Inativa'}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {integration.direction === 'bidirectional' ? '↔️ Bidirecional' : integration.direction === 'import' ? '⬇️ Import' : '⬆️ Export'}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {integration.frequency === 'realtime' ? '⚡ Tempo Real' : integration.frequency === 'hourly' ? '🕐 A cada hora' : integration.frequency === 'daily' ? '📅 Diário' : '📆 Semanal'}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-center">
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">{integration.mappedFields}/{integration.totalFields}</p>
                    <p className="text-lia-text-secondary">Campos</p>
                  </div>
                  <div className="text-center">
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">{new Date(integration.lastRun).toLocaleDateString('pt-BR')}</p>
                    <p className="text-lia-text-secondary">Última exec.</p>
                  </div>
                  <div className="text-center">
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">{new Date(integration.nextRun).toLocaleDateString('pt-BR')}</p>
                    <p className="text-lia-text-secondary">Próxima</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline"><Edit className="w-4 h-4" /></Button>
                    <Button size="sm" variant="outline"><Play className="w-4 h-4" /></Button>
                    <Button size="sm" variant="outline"><MoreHorizontal className="w-4 h-4" /></Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function LogsView({ syncLogs }: { syncLogs: ReturnType<typeof useAtsIntegrations>['syncLogs'] }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>Logs de Sincronização</h3>
          <p className={textStyles.body}>Histórico detalhado de todas as operações</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-2"><Filter className="w-4 h-4" />Filtros</Button>
          <Button variant="outline" size="sm" className="gap-2"><Download className="w-4 h-4" />Exportar</Button>
        </div>
      </div>
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-lia-bg-secondary">
                <tr>
                  {['Status', 'Sistema', 'Operação', 'Registros', 'Duração', 'Data/Hora', 'Ações'].map(h => (
                    <th key={h} className="text-left py-3 px-4 font-medium text-lia-text-primary dark:text-lia-text-primary">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {syncLogs.map(log => (
                  <tr key={log.id} className="border-t border-lia-border-subtle">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {getSyncStatusIcon(log.status)}
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          log.status === 'success' ? 'bg-status-success/15 text-status-success' :
                          log.status === 'warning' ? 'bg-status-warning/15 text-status-warning' :
                          log.status === 'error' ? 'bg-status-error/15 text-status-error' :
                          'bg-lia-bg-secondary text-lia-text-secondary'
                        }`} aria-live="polite">
                          {log.status === 'success' ? 'Sucesso' : log.status === 'warning' ? 'Aviso' : log.status === 'error' ? 'Erro' : 'Info'}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4"><span className="font-medium text-lia-text-primary dark:text-lia-text-primary">{log.system}</span></td>
                    <td className="py-3 px-4">
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{log.message}</p>
                      {log.details && <p className="text-xs text-lia-text-secondary">{log.details}</p>}
                    </td>
                    <td className="py-3 px-4"><span className="font-medium">{log.records}</span></td>
                    <td className="py-3 px-4"><span className="text-sm">{log.duration}ms</span></td>
                    <td className="py-3 px-4"><span className="text-sm">{new Date(log.timestamp).toLocaleString('pt-BR')}</span></td>
                    <td className="py-3 px-4"><Button size="sm" variant="ghost"><Eye className="w-4 h-4" /></Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ── System Configuration Modal ────────────────────────────────────────────────
function SystemConfigurationModal({ system, onClose }: SystemConfigurationModalProps) {
  const {
    selectedTab, setSelectedTab,
    isConnecting, connectionStatus, handleTestConnection,
    mappings, draggedField, selectedTemplate,
    systemFields, liaFields, mappingTemplates,
    handleDragStart, handleDragOver, handleDrop,
    applyTemplate, removeMapping,
    getFieldTypeIcon, getConfidenceColor
  } = useSystemModal(system)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-md w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{system.name}</h2>
            <p className="text-sm text-lia-text-secondary">Configuração de integração</p>
          </div>
          <Button variant="ghost" onClick={onClose}>×</Button>
        </div>

        {/* Tabs */}
        <div className="flex border-b bg-lia-bg-secondary">
          {[
            { id: 'connection' as const, label: 'Conexão', Icon: Link2 },
            { id: 'mapping' as const, label: 'Mapeamento', Icon: GitBranch },
            { id: 'sync' as const, label: 'Sincronização', Icon: RefreshCw },
            { id: 'webhooks' as const, label: 'Webhooks', Icon: Zap }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors motion-reduce:transition-none ${
                selectedTab === tab.id
                  ? 'border-lia-border-strong text-lia-text-primary bg-lia-bg-primary'
                  : 'border-transparent text-lia-text-secondary hover:text-lia-text-primary'
              }`}
            >
              <tab.Icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          {selectedTab === 'connection' && (
            <div className="space-y-6">
              {system.type === 'sap' && (
                <>
                  <div>
                    <h4 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">Configuração SAP SuccessFactors</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        { label: 'URL do Servidor', type: 'url', placeholder: 'https://api.successfactors.com/v2' },
                        { label: 'Company ID', type: 'text', placeholder: 'SODEXO_BRASIL' },
                        { label: 'Client ID', type: 'text', placeholder: 'sua-client-id' },
                        { label: 'Client Secret', type: 'password', placeholder: '••••••••••••••••' }
                      ].map(field => (
                        <div key={field.label}>
                          <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">{field.label}</label>
                          <input type={field.type} placeholder={field.placeholder} className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="border border-lia-border-subtle rounded-md p-4">
                    <h5 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-3">Módulos para Sincronização</h5>
                    <div className="grid grid-cols-2 gap-2">
                      {['Recruiting', 'Candidate Profile', 'Job Requisition', 'Interview', 'Offer Letter'].map(module => (
                        <label key={module} className="flex items-center gap-2">
                          <input type="checkbox" defaultChecked className="rounded-md border-lia-border-default" />
                          <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">{module}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
              {system.type === 'workday' && (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">Configuração Workday HCM</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: 'Tenant URL', type: 'url', placeholder: 'https://wd2-impl-services1.workday.com', span: false },
                      { label: 'Username', type: 'text', placeholder: 'integration.user@tenant', span: false },
                      { label: 'Password', type: 'password', placeholder: '••••••••••••••••', span: true }
                    ].map(field => (
                      <div key={field.label} className={field.span ? 'md:col-span-2' : ''}>
                        <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">{field.label}</label>
                        <input type={field.type} placeholder={field.placeholder} className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {system.type === 'bamboohr' && (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">Configuração BambooHR</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: 'Subdomain', type: 'text', placeholder: 'sua-empresa' },
                      { label: 'API Key', type: 'password', placeholder: '••••••••••••••••' }
                    ].map(field => (
                      <div key={field.label}>
                        <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">{field.label}</label>
                        <input type={field.type} placeholder={field.placeholder} className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between p-4 bg-lia-bg-secondary rounded-md" role="status" aria-live="polite" aria-label="Status da conexão">
                <div className="flex items-center gap-3">
                  {connectionStatus === 'idle' && <Wifi className="w-5 h-5 text-lia-text-secondary" />}
                  {connectionStatus === 'testing' && <RefreshCw className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />}
                  {connectionStatus === 'success' && <CheckCircle className="w-5 h-5 text-status-success" />}
                  {connectionStatus === 'error' && <XCircle className="w-5 h-5 text-status-error" />}
                  <div>
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {connectionStatus === 'idle' && 'Pronto para testar conexão'}
                      {connectionStatus === 'testing' && 'Testando conexão...'}
                      {connectionStatus === 'success' && 'Conexão estabelecida com sucesso!'}
                      {connectionStatus === 'error' && 'Erro na conexão - verifique as credenciais'}
                    </p>
                    <p className="text-sm text-lia-text-secondary">
                      {connectionStatus === 'idle' && 'Clique em "Testar Conexão" para validar as configurações'}
                      {connectionStatus === 'testing' && 'Verificando credenciais e conectividade...'}
                      {connectionStatus === 'success' && 'Sistema pronto para sincronização'}
                      {connectionStatus === 'error' && 'Verifique as credenciais e tente novamente'}
                    </p>
                  </div>
                </div>
                <Button onClick={handleTestConnection} disabled={isConnecting} className="gap-2">
                  {isConnecting ? (<><RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />Testando...</>) : (<><Zap className="w-4 h-4" />Testar Conexão</>)}
                </Button>
              </div>
            </div>
          )}

          {selectedTab === 'mapping' && (
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">Templates de Mapeamento</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {mappingTemplates.map(template => (
                    <div
                      key={template.id}
                      className={`p-4 border rounded-md cursor-pointer transition-colors motion-reduce:transition-none ${
                        selectedTemplate === template.id
                          ? 'border-lia-border-strong bg-lia-bg-secondary'
                          : 'border-lia-border-subtle hover:border-lia-border-default'
                      }`}
                      onClick={() => applyTemplate(template.id)}
                    >
                      <h5 className="font-medium text-lia-text-primary dark:text-lia-text-primary">{template.name}</h5>
                      <p className="text-sm text-lia-text-secondary mt-1">{template.description}</p>
                      <p className="text-xs text-lia-text-secondary mt-2">{template.mappings.length} campos mapeados</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-4">Mapeamento de Campos</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Source Fields */}
                  <div>
                    <h5 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-3 flex items-center gap-2">
                      <Server className="w-4 h-4" />{system.name} (Origem)
                    </h5>
                    <div className="space-y-2 max-h-96 overflow-y-auto border border-lia-border-subtle rounded-md p-3">
                      {systemFields.map(field => {
                        const isMapped = mappings.some(m => m.sourceField === field.id)
                        return (
                          <div
                            key={field.id}
                            draggable
                            onDragStart={() => handleDragStart(field)}
                            className={`p-3 border rounded-md cursor-move transition-colors motion-reduce:transition-none ${
                              isMapped ? 'border-status-success/30 bg-status-success/10' : 'border-lia-border-subtle bg-lia-bg-primary hover:border-lia-border-strong'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-xs">{getFieldTypeIcon(field.type)}</span>
                                <div>
                                  <p className="font-medium text-lia-text-primary dark:text-lia-text-primary text-sm">{field.name}</p>
                                  <p className="text-xs text-lia-text-secondary">{field.description}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                {field.required && <span className="text-xs bg-status-error/15 text-status-error px-1.5 py-0.5 rounded-md" aria-live="polite">Obrigatório</span>}
                                {isMapped && <CheckCircle className="w-4 h-4 text-status-success" />}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Target Fields */}
                  <div>
                    <h5 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-3 flex items-center gap-2">
                      <Database className="w-4 h-4" />Plataforma LIA (Destino)
                    </h5>
                    <div className="space-y-2 max-h-96 overflow-y-auto border border-lia-border-subtle rounded-md p-3">
                      {liaFields.map(field => {
                        const mapping = mappings.find(m => m.targetField === field.id)
                        return (
                          <div
                            key={field.id}
                            onDragOver={handleDragOver}
                            onDrop={(e) => handleDrop(e, field)}
                            className={`p-3 border rounded-md transition-colors motion-reduce:transition-none min-h-[60px] ${
                              mapping
                                ? 'border-lia-border-default bg-lia-bg-secondary'
                                : 'border-dashed border-lia-border-default bg-lia-bg-tertiary hover:border-lia-border-strong hover:bg-lia-bg-secondary'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-xs">{getFieldTypeIcon(field.type)}</span>
                                <div>
                                  <p className="font-medium text-lia-text-primary dark:text-lia-text-primary text-sm">{field.name}</p>
                                  <p className="text-xs text-lia-text-secondary">{field.description}</p>
                                  {mapping && <p className="text-xs text-lia-text-tertiary mt-1">← Mapeado de: {mapping.sourceFieldName}</p>}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {field.required && <span className="text-xs bg-status-error/15 text-status-error px-1.5 py-0.5 rounded-md" aria-live="polite">Obrigatório</span>}
                                {mapping && (
                                  <div className="flex items-center gap-1">
                                    <span className={`text-xs px-2 py-1 rounded-md ${getConfidenceColor(mapping.confidence)}`}>{mapping.confidence}%</span>
                                    <Button size="sm" variant="ghost" onClick={() => removeMapping(mapping.id)} className="h-6 w-6 p-0 hover:bg-status-error/15">
                                      <XCircle className="w-3 h-3 text-status-error" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {mappings.length > 0 && (
                <div className="border border-lia-border-subtle rounded-md p-4">
                  <h5 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-3">Resumo do Mapeamento</h5>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{mappings.length}</p>
                      <p className="text-sm text-lia-text-secondary">Campos Mapeados</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-status-success">{mappings.filter(m => m.confidence >= 90).length}</p>
                      <p className="text-sm text-lia-text-secondary">Alta Confiança (≥90%)</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-wedo-orange">{liaFields.filter(f => f.required && !mappings.some(m => m.targetField === f.id)).length}</p>
                      <p className="text-sm text-lia-text-secondary">Obrigatórios Pendentes</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {mappings.map(mapping => (
                      <div key={mapping.id} className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-md">
                        <span className="text-sm">
                          <span className="font-medium">{mapping.sourceFieldName}</span>
                          <ArrowRight className="w-4 h-4 inline mx-2" />
                          <span className="font-medium">{mapping.targetFieldName}</span>
                        </span>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded-md ${getConfidenceColor(mapping.confidence)}`}>{mapping.confidence}%</span>
                          <Button size="sm" variant="ghost" onClick={() => removeMapping(mapping.id)} className="h-6 w-6 p-0">
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-lia-bg-secondary border border-lia-border-default rounded-md p-4">
                <h5 className="font-medium text-lia-text-secondary dark:text-lia-text-secondary mb-2">Como usar o mapeamento:</h5>
                <ul className="text-sm text-lia-text-secondary dark:text-lia-text-secondary space-y-1">
                  <li>• Arraste campos da origem para os campos de destino correspondentes</li>
                  <li>• Use templates pré-configurados para mapeamentos comuns</li>
                  <li>• Verifique a porcentagem de confiança de cada mapeamento</li>
                  <li>• Certifique-se de mapear todos os campos obrigatórios (marcados em vermelho)</li>
                  <li>• Clique no X para remover mapeamentos incorretos</li>
                </ul>
              </div>
            </div>
          )}

          {selectedTab === 'sync' && (
            <div className="text-center py-12">
              <RefreshCw className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
              <h3 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">Configuração de Sincronização</h3>
              <p className="text-lia-text-secondary">Configurações de frequência e filtros em desenvolvimento</p>
            </div>
          )}

          {selectedTab === 'webhooks' && (
            <div className="text-center py-12">
              <Zap className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
              <h3 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">Configuração de Webhooks</h3>
              <p className="text-lia-text-secondary">Sistema de eventos em tempo real em desenvolvimento</p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 p-6 border-t">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button>Salvar Configuração</Button>
        </div>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function ATSIntegrationsPage() {
  const {
    selectedView, setSelectedView,
    selectedSystem, showSystemModal,
    openSystemModal, closeSystemModal,
    atsSystems, integrations, syncLogs,
    getStatusColor
  } = useAtsIntegrations()

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
                <Link2 className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Integrações ATS Enterprise
              </h1>
              <p className="text-sm text-lia-text-secondary">Conecte e sincronize dados com sistemas HR externos</p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2"><Download className="w-4 h-4" />Exportar Logs</Button>
              <Button variant="outline" className="gap-2"><RefreshCw className="w-4 h-4" />Sincronizar Tudo</Button>
              <Button className="gap-2"><Plus className="w-4 h-4" />Nova Integração</Button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-lia-bg-secondary p-1 rounded-md w-fit">
            {[
              { id: 'overview' as const, label: 'Visão Geral', Icon: BarChart3 },
              { id: 'systems' as const, label: 'Sistemas', Icon: Server },
              { id: 'integrations' as const, label: 'Integrações', Icon: Settings },
              { id: 'logs' as const, label: 'Logs', Icon: FileText }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
                  selectedView === tab.id
                    ? 'bg-lia-bg-primary text-lia-text-primary dark:text-lia-text-primary'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <tab.Icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {selectedView === 'overview' && (
          <OverviewView
            atsSystems={atsSystems}
            integrations={integrations}
            syncLogs={syncLogs}
            getStatusColor={getStatusColor}
            setSelectedView={setSelectedView}
            openSystemModal={openSystemModal}
          />
        )}
        {selectedView === 'systems' && (
          <SystemsView atsSystems={atsSystems} getStatusColor={getStatusColor} openSystemModal={openSystemModal} />
        )}
        {selectedView === 'integrations' && <IntegrationsView integrations={integrations} />}
        {selectedView === 'logs' && <LogsView syncLogs={syncLogs} />}

        {/* System Configuration Modal */}
        {showSystemModal && selectedSystem && (
          <SystemConfigurationModal system={selectedSystem} onClose={closeSystemModal} />
        )}
      </div>
    </div>
  )
}
