"use client"

import { textStyles, cardStyles } from '@/lib/design-tokens'
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Link2, Settings, Activity, CheckCircle, AlertTriangle, XCircle,
  Plus, Play, Eye, Edit, Trash2, Download,
  FileText, BarChart3, Database, Server, Zap,
  Minus, Filter, RefreshCw, ArrowRight,
  CheckCircle2, Info, MoreHorizontal
} from"lucide-react"
import { useAtsIntegrations } from './ats-integrations/useAtsIntegrations'
import { SystemConfigurationModal } from './ats-integrations/SystemConfigurationModal'
import type { ATSSystem, ViewTab } from './ats-integrations/ats-integrations.types'

// ── Pure status helpers ───────────────────────────────────────────────────────
function getStatusIcon(status: string) {
  switch (status) {
    case 'connected':  return <CheckCircle className="w-4 h-4 text-status-success" />
    case 'connecting': return <RefreshCw className="w-4 h-4 text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
    case 'error':      return <XCircle className="w-4 h-4 text-status-error" />
    case 'disabled':   return <Minus className="w-4 h-4 text-lia-text-secondary" />
    default:           return <AlertTriangle className="w-4 h-4 text-status-warning" />
  }
}
function getSyncStatusIcon(status: string) {
  switch (status) {
    case 'success': return <CheckCircle2 className="w-4 h-4 text-status-success" />
    case 'warning': return <AlertTriangle className="w-4 h-4 text-status-warning" />
    case 'error':   return <XCircle className="w-4 h-4 text-status-error" />
    default:        return <Info className="w-4 h-4 text-lia-text-tertiary" />
  }
}
const STATUS_LABEL: Record<string, string> = {
  connected: 'Conectado', connecting: 'Conectando', error: 'Erro', disabled: 'Desabilitado'
}

// ── Sub-view components ───────────────────────────────────────────────────────
type HookState = ReturnType<typeof useAtsIntegrations>

function OverviewView({ atsSystems, integrations, syncLogs, getStatusColor, setSelectedView, openSystemModal }: HookState) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card><CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={textStyles.label}>Sistemas Conectados</p>
              <p className={`${textStyles.titleXl} text-2xl`}>{atsSystems.filter(s => s.status === 'connected').length}</p>
              <p className={textStyles.caption}>de {atsSystems.length} configurados</p>
            </div>
            <div className="w-12 h-12 bg-status-success/15 rounded-xl flex items-center justify-center" aria-live="polite" aria-atomic="true">
              <Link2 className="w-6 h-6 text-status-success" />
            </div>
          </div>
        </CardContent></Card>

        <Card><CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={textStyles.label}>Registros Sincronizados</p>
              <p className={`${textStyles.titleXl} text-2xl text-lia-text-secondary`}>{atsSystems.reduce((a, s) => a + s.syncedRecords, 0).toLocaleString()}</p>
              <p className={`${textStyles.caption} text-status-success`}>+47 hoje</p>
            </div>
            <div className="w-12 h-12 bg-lia-bg-secondary rounded-xl flex items-center justify-center">
              <Database className="w-6 h-6 text-lia-text-tertiary" />
            </div>
          </div>
        </CardContent></Card>

        <Card><CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={textStyles.label}>Integrações Ativas</p>
              <p className={`${textStyles.titleXl} text-2xl text-wedo-purple`}>{integrations.filter(i => i.isActive).length}</p>
              <p className={textStyles.caption}>de {integrations.length} total</p>
            </div>
            <div className="w-12 h-12 bg-wedo-purple/15 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-wedo-purple" />
            </div>
          </div>
        </CardContent></Card>

        <Card><CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={textStyles.label}>Uptime Médio</p>
              <p className={`${textStyles.titleXl} text-2xl text-wedo-orange`}>99.7%</p>
              <p className={`${textStyles.caption} text-wedo-orange`}>últimos 30 dias</p>
            </div>
            <div className="w-12 h-12 bg-wedo-orange/15 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6 text-wedo-orange" />
            </div>
          </div>
        </CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-xs font-sans">Ações Rápidas</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Adicionar Sistema', sub: 'Conectar novo ATS', view: 'systems' as const, Icon: Plus, cls: 'text-lia-text-tertiary' },
              { label: 'Configurar Sync', sub: 'Gerenciar integrações', view: 'integrations' as const, Icon: Settings, cls: 'text-wedo-purple' },
              { label: 'Ver Logs', sub: 'Histórico de operações', view: 'logs' as const, Icon: FileText, cls: 'text-wedo-orange' }
            ].map(({ label, sub, view, Icon, cls }) => (
              <Button key={view} variant="outline" className="h-auto p-4 justify-start gap-3" onClick={() => setSelectedView(view)}>
                <Icon className={`w-5 h-5 ${cls}`} />
                <div className="text-left">
                  <div className="font-medium">{label}</div>
                  <div className="text-sm text-lia-text-secondary">{sub}</div>
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-xs font-sans">Status dos Sistemas</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {atsSystems.map(system => (
              <div key={system.id} className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-lg hover:bg-lia-bg-secondary/50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-lia-bg-secondary rounded-xl flex items-center justify-center">
                    <Server className="w-6 h-6 text-lia-text-secondary" />
                  </div>
                  <div>
                    <h4 className={textStyles.subtitle}>{system.name}</h4>
                    <p className={textStyles.bodySmall}>{system.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(system.status)}
                      <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(system.status)}`}>{STATUS_LABEL[system.status] ?? system.status}</span>
                      {system.lastSync && <span className="text-xs text-lia-text-secondary">Última sync: {new Date(system.lastSync).toLocaleString('pt-BR')}</span>}
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
                        <p className="font-medium text-status-success">{Math.round((system.syncedRecords / system.totalRecords) * 100)}%</p>
                        <p className="text-lia-text-secondary">Sincronizado</p>
                      </div>
                    </>
                  )}
                  <Button variant="outline" size="sm" onClick={() => openSystemModal(system)}>Configurar</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-xs font-sans">Logs Recentes</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {syncLogs.slice(0, 5).map(log => (
              <div key={log.id} className="flex items-center justify-between p-3 bg-lia-bg-secondary rounded-lg">
                <div className="flex items-center gap-3">
                  {getSyncStatusIcon(log.status)}
                  <div>
                    <p className={textStyles.subtitle}>{log.message}</p>
                    <p className={textStyles.caption}>{log.system} • {new Date(log.timestamp).toLocaleString('pt-BR')}</p>
                  </div>
                </div>
                <div className="text-right text-xs text-lia-text-secondary">
                  <p>{log.records} registros</p><p>{log.duration}ms</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3">
            <Button variant="outline" size="sm" onClick={() => setSelectedView('logs')} className="w-full">Ver Todos os Logs</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function SystemsView({ atsSystems, getStatusColor, openSystemModal }: Pick<HookState, 'atsSystems' | 'getStatusColor' | 'openSystemModal'>) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>Sistemas ATS Disponíveis</h3>
          <p className={textStyles.body}>Configure e gerencie conexões com sistemas externos</p>
        </div>
        <Button className="gap-2"><Plus className="w-4 h-4" />Adicionar Sistema Personalizado</Button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {atsSystems.map(system => (
          <Card key={system.id} className={cardStyles.interactive}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-lia-bg-secondary rounded-xl flex items-center justify-center">
                    <Server className="w-6 h-6 text-lia-text-secondary" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{system.name}</CardTitle>
                    <p className="text-sm text-lia-text-secondary">{system.type.toUpperCase()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(system.status)}
                  <Chip variant={system.status === 'connected' ? 'success' : system.status === 'error' ? 'danger' : 'neutral'} muted={system.status === 'connecting'} className="text-xs" aria-live="polite">
                    {STATUS_LABEL[system.status] ?? system.status}
                  </Chip>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className={textStyles.body}>{system.description}</p>
                <div>
                  <p className="text-sm font-medium text-lia-text-primary mb-2">Funcionalidades:</p>
                  <div className="flex flex-wrap gap-1">
                    {system.features.map(f => <Chip key={f} variant="neutral" className="text-xs">{f}</Chip>)}
                  </div>
                </div>
                {system.status === 'connected' && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><p className="text-lia-text-secondary">Registros sincronizados:</p><p className="font-medium">{system.syncedRecords.toLocaleString()}</p></div>
                    <div><p className="text-lia-text-secondary">Última sincronização:</p><p className="font-medium">{system.lastSync ? new Date(system.lastSync).toLocaleString('pt-BR') : 'N/A'}</p></div>
                    {system.version && <div><p className="text-lia-text-secondary">Versão da API:</p><p className="font-medium">{system.version}</p></div>}
                    {system.errorCount > 0 && <div><p className="text-lia-text-secondary">Erros:</p><p className="font-medium text-status-error">{system.errorCount}</p></div>}
                  </div>
                )}
                {system.status === 'error' && (
                  <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-lg" aria-live="polite" aria-atomic="true">
                    <p className="text-sm text-status-error"><AlertTriangle className="w-4 h-4 inline mr-1" />Token de acesso expirado - requer renovação manual</p>
                  </div>
                )}
                <div className="flex gap-2">
                  {system.status === 'disabled' ? (
                    <Button size="sm" onClick={() => openSystemModal(system)} className="flex-1">Configurar Conexão</Button>
                  ) : (
                    <>
                      <Button size="sm" variant="outline" onClick={() => openSystemModal(system)} className="flex-1"><Settings className="w-4 h-4 mr-2" />Configurar</Button>
                      {system.status === 'connected' && <Button size="sm" variant="outline" className="flex-1"><RefreshCw className="w-4 h-4 mr-2" />Sincronizar</Button>}
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

function IntegrationsView({ integrations }: Pick<HookState, 'integrations'>) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h3 className={textStyles.title}>Integrações Ativas</h3><p className={textStyles.body}>Gerencie sincronizações e mapeamentos de dados</p></div>
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
                      <Chip variant="neutral" muted className="text-xs">{integration.isActive ? 'Ativa' : 'Inativa'}</Chip>
                      <Chip variant="neutral" className="text-xs">{integration.direction === 'bidirectional' ? '↔️ Bidirecional' : integration.direction === 'import' ? '⬇️ Import' : '⬆️ Export'}</Chip>
                      <Chip variant="neutral" className="text-xs">{integration.frequency === 'realtime' ? '⚡ Tempo Real' : integration.frequency === 'hourly' ? '🕐 A cada hora' : integration.frequency === 'daily' ? '📅 Diário' : '📆 Semanal'}</Chip>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-center"><p className="font-medium text-lia-text-primary">{integration.mappedFields}/{integration.totalFields}</p><p className="text-lia-text-secondary">Campos</p></div>
                  <div className="text-center"><p className="font-medium text-lia-text-primary">{new Date(integration.lastRun).toLocaleDateString('pt-BR')}</p><p className="text-lia-text-secondary">Última exec.</p></div>
                  <div className="text-center"><p className="font-medium text-lia-text-primary">{new Date(integration.nextRun).toLocaleDateString('pt-BR')}</p><p className="text-lia-text-secondary">Próxima</p></div>
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

function LogsView({ syncLogs }: Pick<HookState, 'syncLogs'>) {
  const statusCls = (s: string) =>
    s === 'success' ? '' :
    s === 'warning' ? '' :
    s === 'error'   ? '' :
    'bg-lia-bg-secondary text-lia-text-secondary'
  const statusLabel = (s: string) =>
    s === 'success' ? 'Sucesso' : s === 'warning' ? 'Aviso' : s === 'error' ? 'Erro' : 'Info'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h3 className={textStyles.title}>Logs de Sincronização</h3><p className={textStyles.body}>Histórico detalhado de todas as operações</p></div>
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
                <tr>{['Status','Sistema','Operação','Registros','Duração','Data/Hora','Ações'].map(h => (
                  <th key={h} className="text-left py-3 px-4 font-medium text-lia-text-primary">{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {syncLogs.map(log => (
                  <tr key={log.id} className="border-t border-lia-border-subtle">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {getSyncStatusIcon(log.status)}
                        <span className={`text-xs px-2 py-1 rounded-full ${statusCls(log.status)}`} aria-live="polite">{statusLabel(log.status)}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4"><span className="font-medium text-lia-text-primary">{log.system}</span></td>
                    <td className="py-3 px-4">
                      <p className="text-sm font-medium text-lia-text-primary">{log.message}</p>
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

// ── Main Page ─────────────────────────────────────────────────────────────────
export function ATSIntegrationsPage() {
  const hook = useAtsIntegrations()
  const { selectedView, setSelectedView, selectedSystem, showSystemModal, closeSystemModal } = hook

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-semibold text-lia-text-primary flex items-center gap-1.5">
                <Link2 className="w-6 h-6 text-lia-text-tertiary" />Integrações ATS Enterprise
              </h1>
              <p className="text-sm text-lia-text-secondary">Conecte e sincronize dados com sistemas HR externos</p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2"><Download className="w-4 h-4" />Exportar Logs</Button>
              <Button variant="outline" className="gap-2"><RefreshCw className="w-4 h-4" />Sincronizar Tudo</Button>
              <Button className="gap-2"><Plus className="w-4 h-4" />Nova Integração</Button>
            </div>
          </div>

          <div className="flex space-x-1 bg-lia-bg-secondary p-1 rounded-lg w-fit">
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
                  selectedView === tab.id ? 'bg-lia-bg-primary text-lia-text-primary shadow-sm' : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <tab.Icon className="w-4 h-4" />{tab.label}
              </button>
            ))}
          </div>
        </div>

        {selectedView === 'overview'     && <OverviewView {...hook} />}
        {selectedView === 'systems'      && <SystemsView atsSystems={hook.atsSystems} getStatusColor={hook.getStatusColor} openSystemModal={hook.openSystemModal} />}
        {selectedView === 'integrations' && <IntegrationsView integrations={hook.integrations} />}
        {selectedView === 'logs'         && <LogsView syncLogs={hook.syncLogs} />}

        {showSystemModal && selectedSystem && (
          <SystemConfigurationModal system={selectedSystem} onClose={closeSystemModal} />
        )}
      </div>
    </div>
  )
}
