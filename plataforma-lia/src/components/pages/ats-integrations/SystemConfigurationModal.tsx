"use client"

import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Link2, Settings, RefreshCw, Zap, Server, Database,
  CheckCircle, XCircle, Wifi, ArrowRight, Trash2, GitBranch, Save
} from "lucide-react"
import { useSystemModal, type ATSConnectionData } from './useAtsIntegrations'
import type { SystemConfigurationModalProps } from './ats-integrations.types'

function SyncTab({ systemType }: { systemType: string }) {
  const [connections, setConnections] = useState<ATSConnectionData[]>([])
  const [syncing, setSyncing] = useState<string | null>(null)
  const [syncResult, setSyncResult] = useState<{ id: string; message: string; success: boolean } | null>(null)

  useEffect(() => {
    fetch('/api/backend-proxy/ats/connections')
      .then(r => r.ok ? r.json() : [])
      .then(data => setConnections(
        (Array.isArray(data) ? data : []).filter(
          (c: ATSConnectionData) => c.provider?.toLowerCase() === systemType
        )
      ))
      .catch((err) => { console.error('[SystemConfigurationModal] ATS connections fetch failed', err) })
  }, [systemType])

  const triggerSync = useCallback(async (connectionId: string, syncType: string) => {
    setSyncing(connectionId)
    setSyncResult(null)
    try {
      const res = await fetch('/api/backend-proxy/ats/connections/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, sync_type: syncType }),
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: `Erro HTTP ${res.status}` }))
        setSyncResult({ id: connectionId, message: errData.detail || `Erro (${res.status})`, success: false })
        return
      }
      const data = await res.json()
      setSyncResult({ id: connectionId, message: data.message || 'Concluído', success: data.success !== false })
    } catch {
      setSyncResult({ id: connectionId, message: 'Erro de rede', success: false })
    } finally {
      setSyncing(null)
    }
  }, [])

  if (connections.length === 0) {
    return (
      <div className="text-center py-12">
        <RefreshCw className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
        <h3 className="text-xs font-medium text-lia-text-primary mb-2">Nenhuma Conexão Ativa</h3>
        <p className="text-lia-text-secondary">Configure uma conexão na aba Conexão para habilitar a sincronização.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-xs font-medium text-lia-text-primary mb-4">Sincronizar Dados</h4>
        {connections.map((conn) => (
          <div key={conn.id} className="border border-lia-border-subtle rounded-xl p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-medium text-lia-text-primary">{conn.provider_name}</p>
                <p className="text-xs text-lia-text-secondary">
                  {conn.last_sync_at
                    ? `Última sync: ${new Date(conn.last_sync_at).toLocaleString('pt-BR')}`
                    : 'Nunca sincronizado'}
                </p>
              </div>
              <p className="text-sm text-lia-text-secondary">{conn.total_candidates_synced || 0} candidatos</p>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="gap-2"
                disabled={syncing === conn.id}
                onClick={() => triggerSync(conn.id, 'candidates')}
              >
                {syncing === conn.id
                  ? <><RefreshCw className="w-3 h-3 animate-spin" />Sincronizando...</>
                  : 'Sincronizar Candidatos'}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="gap-2"
                disabled={syncing === conn.id}
                onClick={() => triggerSync(conn.id, 'jobs')}
              >
                Sincronizar Vagas
              </Button>
              <Button
                size="sm"
                className="gap-2"
                disabled={syncing === conn.id}
                onClick={() => triggerSync(conn.id, 'full')}
              >
                Sincronização Completa
              </Button>
            </div>
            {syncResult && syncResult.id === conn.id && (
              <div className={`mt-3 p-2 rounded-md text-sm ${
                syncResult.success
                  ? 'bg-status-success/10 text-status-success'
                  : 'bg-status-error/10 text-status-error'
              }`}>
                {syncResult.message}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export function SystemConfigurationModal({ system, onClose }: SystemConfigurationModalProps) {
  const {
    selectedTab, setSelectedTab,
    isConnecting, connectionStatus, connectionMessage,
    credentials, setCredentials,
    handleTestConnection, handleSaveConnection, isSaving,
    mappings, selectedTemplate,
    systemFields, liaFields, mappingTemplates,
    handleDragStart, handleDragOver, handleDrop,
    applyTemplate, removeMapping,
    handleSaveMappings, isSavingMappings,
    getFieldTypeIcon, getConfidenceColor
  } = useSystemModal(system)

  const isAtsProvider = system.type === 'gupy' || system.type === 'pandape' || system.type === 'merge'

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-lia-text-primary">{system.name}</h2>
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
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium rounded-lg transition-colors motion-reduce:transition-none ${
                selectedTab === tab.id
                  ? 'border-lia-border-strong text-lia-text-primary bg-lia-bg-primary'
                  : 'border-transparent text-lia-text-secondary hover:text-lia-text-primary'
              }`}
            >
              <tab.Icon className="w-4 h-4" />{tab.label}
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
                    <h4 className="text-xs font-medium text-lia-text-primary mb-4">Configuração SAP SuccessFactors</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        { label: 'URL do Servidor', type: 'url', placeholder: 'https://api.successfactors.com/v2' },
                        { label: 'Company ID', type: 'text', placeholder: 'SODEXO_BRASIL' },
                        { label: 'Client ID', type: 'text', placeholder: 'sua-client-id' },
                        { label: 'Client Secret', type: 'password', placeholder: '••••••••••••••••' }
                      ].map(field => (
                        <div key={field.label}>
                          <label className="block text-sm font-medium text-lia-text-primary mb-2">{field.label}</label>
                          <input type={field.type} placeholder={field.placeholder} className="w-full p-3 border border-lia-border-default rounded-xl focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="border border-lia-border-subtle rounded-xl p-4">
                    <h5 className="font-medium text-lia-text-primary mb-3">Módulos para Sincronização</h5>
                    <div className="grid grid-cols-2 gap-2">
                      {['Recruiting', 'Candidate Profile', 'Job Requisition', 'Interview', 'Offer Letter'].map(mod => (
                        <label key={mod} className="flex items-center gap-2">
                          <input type="checkbox" defaultChecked className="rounded-xl border-lia-border-default" />
                          <span className="text-sm text-lia-text-primary">{mod}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
              {system.type === 'workday' && (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary mb-4">Configuração Workday HCM</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: 'Tenant URL', type: 'url', placeholder: 'https://wd2-impl-services1.workday.com', span: false },
                      { label: 'Username', type: 'text', placeholder: 'integration.user@tenant', span: false },
                      { label: 'Password', type: 'password', placeholder: '••••••••••••••••', span: true }
                    ].map(f => (
                      <div key={f.label} className={f.span ? 'md:col-span-2' : ''}>
                        <label className="block text-sm font-medium text-lia-text-primary mb-2">{f.label}</label>
                        <input type={f.type} placeholder={f.placeholder} className="w-full p-3 border border-lia-border-default rounded-xl focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {system.type === 'bamboohr' && (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary mb-4">Configuração BambooHR</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: 'Subdomain', type: 'text', placeholder: 'sua-empresa' },
                      { label: 'API Key', type: 'password', placeholder: '••••••••••••••••' }
                    ].map(f => (
                      <div key={f.label}>
                        <label className="block text-sm font-medium text-lia-text-primary mb-2">{f.label}</label>
                        <input type={f.type} placeholder={f.placeholder} className="w-full p-3 border border-lia-border-default rounded-xl focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {isAtsProvider && (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary mb-4">
                    Credenciais {system.type === 'gupy' ? 'Gupy' : system.type === 'pandape' ? 'Pandapé' : 'Merge.dev'}
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-lia-text-primary mb-2">API Key</label>
                      <input
                        type="password"
                        placeholder="Cole sua API Key aqui"
                        value={credentials.apiKey}
                        onChange={(e) => setCredentials({ ...credentials, apiKey: e.target.value })}
                        className="w-full p-3 border border-lia-border-default rounded-xl focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong bg-lia-bg-primary text-lia-text-primary"
                      />
                    </div>
                    {system.type === 'pandape' && (
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-lia-text-primary mb-2">API Endpoint (opcional)</label>
                        <input
                          type="url"
                          placeholder="https://api-ats.pandape.com"
                          value={credentials.apiEndpoint}
                          onChange={(e) => setCredentials({ ...credentials, apiEndpoint: e.target.value })}
                          className="w-full p-3 border border-lia-border-default rounded-xl focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong bg-lia-bg-primary text-lia-text-primary"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div className="flex items-center justify-between p-4 bg-lia-bg-secondary rounded-xl" role="status" aria-live="polite" aria-label="Status da conexão">
                <div className="flex items-center gap-3">
                  {connectionStatus === 'idle' && <Wifi className="w-5 h-5 text-lia-text-secondary" />}
                  {connectionStatus === 'testing' && <RefreshCw className="w-5 h-5 text-lia-text-tertiary animate-spin motion-reduce:animate-none" />}
                  {connectionStatus === 'success' && <CheckCircle className="w-5 h-5 text-status-success" />}
                  {connectionStatus === 'error' && <XCircle className="w-5 h-5 text-status-error" />}
                  <div>
                    <p className="font-medium text-lia-text-primary">
                      {connectionStatus === 'idle' && 'Pronto para testar conexão'}
                      {connectionStatus === 'testing' && 'Testando conexão...'}
                      {connectionStatus === 'success' && (connectionMessage || 'Conexão estabelecida com sucesso!')}
                      {connectionStatus === 'error' && (connectionMessage || 'Erro na conexão - verifique as credenciais')}
                    </p>
                    <p className="text-sm text-lia-text-secondary">
                      {connectionStatus === 'idle' && 'Clique em "Testar Conexão" para validar as configurações'}
                      {connectionStatus === 'testing' && 'Verificando credenciais e conectividade...'}
                      {connectionStatus === 'success' && 'Sistema pronto para sincronização'}
                      {connectionStatus === 'error' && 'Verifique as credenciais e tente novamente'}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleTestConnection} disabled={isConnecting} variant="outline" className="gap-2">
                    {isConnecting
                      ? <><RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />Testando...</>
                      : <><Zap className="w-4 h-4" />Testar Conexão</>}
                  </Button>
                  {isAtsProvider && connectionStatus === 'success' && (
                    <Button onClick={handleSaveConnection} disabled={isSaving} className="gap-2">
                      {isSaving
                        ? <><RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />Salvando...</>
                        : <><CheckCircle className="w-4 h-4" />Salvar Conexão</>}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}

          {selectedTab === 'mapping' && (
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-medium text-lia-text-primary mb-4">Modelos de Mapeamento</h4>
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
                      <h5 className="font-medium text-lia-text-primary">{template.name}</h5>
                      <p className="text-sm text-lia-text-secondary mt-1">{template.description}</p>
                      <p className="text-xs text-lia-text-secondary mt-2">{template.mappings.length} campos mapeados</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-medium text-lia-text-primary mb-4">Mapeamento de Campos</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h5 className="font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                      <Server className="w-4 h-4" />{system.name} (Origem)
                    </h5>
                    <div className="space-y-2 max-h-96 overflow-y-auto border border-lia-border-subtle rounded-xl p-3">
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
                                  <p className="font-medium text-lia-text-primary text-sm">{field.name}</p>
                                  <p className="text-xs text-lia-text-secondary">{field.description}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                {field.required && <span className="text-micro bg-status-error/15 text-status-error px-1.5 py-0.5 rounded-md" aria-live="polite">Obrigatório</span>}
                                {isMapped && <CheckCircle className="w-4 h-4 text-status-success" />}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                  <div>
                    <h5 className="font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                      <Database className="w-4 h-4" />Plataforma LIA (Destino)
                    </h5>
                    <div className="space-y-2 max-h-96 overflow-y-auto border border-lia-border-subtle rounded-xl p-3">
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
                                  <p className="font-medium text-lia-text-primary text-sm">{field.name}</p>
                                  <p className="text-xs text-lia-text-secondary">{field.description}</p>
                                  {mapping && <p className="text-xs text-lia-text-tertiary mt-1">← Mapeado de: {mapping.sourceFieldName}</p>}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {field.required && <span className="text-micro bg-status-error/15 text-status-error px-1.5 py-0.5 rounded-md" aria-live="polite">Obrigatório</span>}
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
                <div className="border border-lia-border-subtle rounded-xl p-4">
                  <h5 className="font-medium text-lia-text-primary mb-3">Resumo do Mapeamento</h5>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-2xl font-semibold text-lia-text-primary">{mappings.length}</p>
                      <p className="text-sm text-lia-text-secondary">Campos Mapeados</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-semibold text-status-success">{mappings.filter(m => m.confidence >= 90).length}</p>
                      <p className="text-sm text-lia-text-secondary">Alta Confiança (≥90%)</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-semibold text-wedo-orange">{liaFields.filter(f => f.required && !mappings.some(m => m.targetField === f.id)).length}</p>
                      <p className="text-sm text-lia-text-secondary">Obrigatórios Pendentes</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {mappings.map(mapping => (
                      <div key={mapping.id} className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl">
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

              <div className="bg-lia-bg-secondary border border-lia-border-default rounded-xl p-4">
                <h5 className="font-medium text-lia-text-secondary mb-2">Como usar o mapeamento:</h5>
                <ul className="text-sm text-lia-text-secondary space-y-1">
                  <li>• Arraste campos da origem para os campos de destino correspondentes</li>
                  <li>• Use templates pré-configurados para mapeamentos comuns</li>
                  <li>• Verifique a porcentagem de confiança de cada mapeamento</li>
                  <li>• Certifique-se de mapear todos os campos obrigatórios (marcados em vermelho)</li>
                  <li>• Clique no X para remover mapeamentos incorretos</li>
                </ul>
              </div>

              {mappings.length > 0 && (
                <div className="flex justify-end">
                  <Button
                    className="gap-2"
                    disabled={isSavingMappings}
                    onClick={handleSaveMappings}
                  >
                    {isSavingMappings
                      ? <><RefreshCw className="w-4 h-4 animate-spin" />Salvando...</>
                      : <><Save className="w-4 h-4" />Salvar Mapeamentos</>}
                  </Button>
                </div>
              )}
            </div>
          )}

          {selectedTab === 'sync' && (
            <SyncTab systemType={system.type} />
          )}

          {selectedTab === 'webhooks' && (
            <div className="text-center py-12">
              <Zap className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
              <h3 className="text-xs font-medium text-lia-text-primary mb-2">Configuração de Webhooks</h3>
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
