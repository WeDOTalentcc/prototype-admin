"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Link2, Settings, RefreshCw, Zap, Server, Database,
  CheckCircle, XCircle, Wifi, ArrowRight, Trash2, GitBranch
} from "lucide-react"
import { useSystemModal } from './useAtsIntegrations'
import type { SystemConfigurationModalProps } from './ats-integrations.types'

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
    getFieldTypeIcon, getConfidenceColor
  } = useSystemModal(system)

  const isAtsProvider = system.type === 'gupy' || system.type === 'pandape'

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-md w-full max-w-4xl max-h-[90vh] flex flex-col">
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
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors motion-reduce:transition-none ${
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
                          <input type={field.type} placeholder={field.placeholder} className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="border border-lia-border-subtle rounded-md p-4">
                    <h5 className="font-medium text-lia-text-primary mb-3">Módulos para Sincronização</h5>
                    <div className="grid grid-cols-2 gap-2">
                      {['Recruiting', 'Candidate Profile', 'Job Requisition', 'Interview', 'Offer Letter'].map(mod => (
                        <label key={mod} className="flex items-center gap-2">
                          <input type="checkbox" defaultChecked className="rounded-md border-lia-border-default" />
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
                        <input type={f.type} placeholder={f.placeholder} className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
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
                        <input type={f.type} placeholder={f.placeholder} className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {isAtsProvider && (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary mb-4">
                    Credenciais {system.type === 'gupy' ? 'Gupy' : 'Pandapé'}
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-lia-text-primary mb-2">API Key</label>
                      <input
                        type="password"
                        placeholder="Cole sua API Key aqui"
                        value={credentials.apiKey}
                        onChange={(e) => setCredentials({ ...credentials, apiKey: e.target.value })}
                        className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong bg-lia-bg-primary text-lia-text-primary"
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
                          className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-lia-border-strong/20 focus:border-lia-border-strong bg-lia-bg-primary text-lia-text-primary"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div className="flex items-center justify-between p-4 bg-lia-bg-secondary rounded-md" role="status" aria-live="polite" aria-label="Status da conexão">
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
                <h4 className="text-xs font-medium text-lia-text-primary mb-4">Templates de Mapeamento</h4>
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
                                  <p className="font-medium text-lia-text-primary text-sm">{field.name}</p>
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
                  <div>
                    <h5 className="font-medium text-lia-text-primary mb-3 flex items-center gap-2">
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
                                  <p className="font-medium text-lia-text-primary text-sm">{field.name}</p>
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
                  <h5 className="font-medium text-lia-text-primary mb-3">Resumo do Mapeamento</h5>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-lia-text-primary">{mappings.length}</p>
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
                <h5 className="font-medium text-lia-text-secondary mb-2">Como usar o mapeamento:</h5>
                <ul className="text-sm text-lia-text-secondary space-y-1">
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
              <h3 className="text-xs font-medium text-lia-text-primary mb-2">Configuração de Sincronização</h3>
              <p className="text-lia-text-secondary">Configurações de frequência e filtros em desenvolvimento</p>
            </div>
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
