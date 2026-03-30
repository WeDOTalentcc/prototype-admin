'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { toast } from "sonner"
import {
  Edit, Save, X, Trash2, Plus, Loader2, FileText,
  RefreshCw, Activity, Copy, Lock, Unlock, Play, Webhook
} from "lucide-react"
import type { WebhookConfig, WebhookEvent, WebhookLog } from './types'

interface WebhooksSectionProps {
  webhooks: WebhookConfig[]
  webhooksLoading: boolean
  savingWebhook: boolean
  testingWebhook: string | null
  editingWebhook: WebhookConfig | null
  setEditingWebhook: (webhook: WebhookConfig | null) => void
  showWebhookSecret: string | null
  setShowWebhookSecret: (id: string | null) => void
  showLogsModal: boolean
  setShowLogsModal: (show: boolean) => void
  selectedWebhookForLogs: WebhookConfig | null
  setSelectedWebhookForLogs: (webhook: WebhookConfig | null) => void
  webhookLogs: WebhookLog[]
  setWebhookLogs: (logs: WebhookLog[]) => void
  webhookLogsLoading: boolean
  availableEvents: WebhookEvent[]
  webhookHeaderKey: string
  setWebhookHeaderKey: (key: string) => void
  webhookHeaderValue: string
  setWebhookHeaderValue: (value: string) => void
  fetchWebhooks: () => void
  handleCreateWebhook: () => void
  handleSaveWebhook: () => void
  handleDeleteWebhook: (id: string) => void
  handleToggleWebhookActive: (id: string) => void
  handleTestWebhook: (id: string) => void
  handleViewWebhookLogs: (webhook: WebhookConfig) => void
  handleToggleWebhookEvent: (eventName: string) => void
  handleAddWebhookHeader: () => void
  handleRemoveWebhookHeader: (key: string) => void
}

export function WebhooksSection({
  webhooks,
  webhooksLoading,
  savingWebhook,
  testingWebhook,
  editingWebhook,
  setEditingWebhook,
  showWebhookSecret,
  setShowWebhookSecret,
  showLogsModal,
  setShowLogsModal,
  selectedWebhookForLogs,
  setSelectedWebhookForLogs,
  webhookLogs,
  setWebhookLogs,
  webhookLogsLoading,
  availableEvents,
  webhookHeaderKey,
  setWebhookHeaderKey,
  webhookHeaderValue,
  setWebhookHeaderValue,
  fetchWebhooks,
  handleCreateWebhook,
  handleSaveWebhook,
  handleDeleteWebhook,
  handleToggleWebhookActive,
  handleTestWebhook,
  handleViewWebhookLogs,
  handleToggleWebhookEvent,
  handleAddWebhookHeader,
  handleRemoveWebhookHeader
}: WebhooksSectionProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400" >
            Webhooks Configurados ({webhooks.length})
          </h3>
          <Button
            size="sm"
            variant="ghost"
            onClick={fetchWebhooks}
            disabled={webhooksLoading}
          >
            <RefreshCw className={`w-4 h-4 ${webhooksLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <Button
          size="sm"
          className="bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200"
          onClick={handleCreateWebhook}
          disabled={webhooksLoading}
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Webhook
        </Button>
      </div>

      {webhooksLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-700 dark:text-gray-300" />
          <span className="ml-3 text-sm text-gray-500 dark:text-gray-400" >
            Carregando webhooks...
          </span>
        </div>
      ) : (
        <>
          {editingWebhook && (
            <Card className="mb-4">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    {editingWebhook.id.startsWith('new-') ? 'Novo Webhook' : 'Editar Webhook'}
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setEditingWebhook(null)} disabled={savingWebhook}>
                      <X className="w-4 h-4 mr-1" /> Cancelar
                    </Button>
                    <Button 
                      size="sm" 
                      className="bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200" 
                      onClick={handleSaveWebhook}
                      disabled={savingWebhook || !editingWebhook.name || !editingWebhook.url}
                    >
                      {savingWebhook ? (
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400" >Nome *</label>
                    <Input
                      value={editingWebhook.name}
                      onChange={(e) => setEditingWebhook({ ...editingWebhook, name: e.target.value })}
                      placeholder="Ex: Slack Notifications"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400" >URL do Endpoint *</label>
                    <Input
                      value={editingWebhook.url}
                      onChange={(e) => setEditingWebhook({ ...editingWebhook, url: e.target.value })}
                      placeholder="https://example.com/webhook"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 dark:text-gray-400" >Descrição</label>
                  <Textarea
                    value={editingWebhook.description || ''}
                    onChange={(e) => setEditingWebhook({ ...editingWebhook, description: e.target.value })}
                    placeholder="Descrição opcional do webhook"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium mb-2 block text-gray-500 dark:text-gray-400" >
                    Eventos ({editingWebhook.events.length} selecionados)
                  </label>
                  {availableEvents.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 border rounded-md border-gray-200 dark:border-gray-700" >
                      {availableEvents.map(event => (
                        <label
                          key={event.name}
                          className="flex items-center gap-2 text-xs cursor-pointer p-1 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          <input
                            type="checkbox"
                            checked={editingWebhook.events.includes(event.name)}
                            onChange={() => handleToggleWebhookEvent(event.name)}
                            className="rounded-md"
                          />
                          <span className="text-gray-800 dark:text-gray-100" >{event.name}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <Input
                      value={editingWebhook.events.join(', ')}
                      onChange={(e) => setEditingWebhook({
                        ...editingWebhook,
                        events: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
                      })}
                      placeholder="candidate.created, candidate.updated (separados por vírgula)"
                    />
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400" >Retry Count</label>
                    <Input
                      type="number"
                      min={0}
                      max={10}
                      value={editingWebhook.retryCount}
                      onChange={(e) => setEditingWebhook({ ...editingWebhook, retryCount: parseInt(e.target.value) || 3 })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 dark:text-gray-400" >Timeout (segundos)</label>
                    <Input
                      type="number"
                      min={5}
                      max={120}
                      value={editingWebhook.timeoutSeconds}
                      onChange={(e) => setEditingWebhook({ ...editingWebhook, timeoutSeconds: parseInt(e.target.value) || 30 })}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium mb-2 block text-gray-500 dark:text-gray-400" >
                    Headers Customizados
                  </label>
                  {editingWebhook.headers && Object.keys(editingWebhook.headers).length > 0 && (
                    <div className="space-y-1 mb-2">
                      {Object.entries(editingWebhook.headers).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-2 text-xs p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                          <code className="flex-1">{key}: {value}</code>
                          <Button size="sm" variant="ghost" onClick={() => handleRemoveWebhookHeader(key)}>
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Input
                      value={webhookHeaderKey}
                      onChange={(e) => setWebhookHeaderKey(e.target.value)}
                      placeholder="Header Key"
                      className="flex-1"
                    />
                    <Input
                      value={webhookHeaderValue}
                      onChange={(e) => setWebhookHeaderValue(e.target.value)}
                      placeholder="Header Value"
                      className="flex-1"
                    />
                    <Button size="sm" variant="outline" onClick={handleAddWebhookHeader} disabled={!webhookHeaderKey.trim()}>
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={editingWebhook.isActive}
                    onCheckedChange={(checked: boolean) => setEditingWebhook({ ...editingWebhook, isActive: checked })}
                  />
                  <span className="text-sm text-gray-500 dark:text-gray-400" >Ativo</span>
                </div>
              </CardContent>
            </Card>
          )}

          {webhooks.length === 0 && !editingWebhook ? (
            <Card className="flex flex-col items-center justify-center py-12">
              <Webhook className="w-12 h-12 mb-3 text-gray-400 dark:text-gray-500"  />
              <p className="text-sm font-medium mb-1 text-gray-500 dark:text-gray-400" >
                Nenhum webhook configurado
              </p>
              <p className="text-xs mb-4 text-gray-400 dark:text-gray-500" >
                Configure webhooks para receber notificações de eventos em tempo real
              </p>
              <Button
                size="sm"
                className="bg-gray-900 dark:bg-gray-50 hover:bg-gray-800 dark:hover:bg-gray-200"
                onClick={handleCreateWebhook}
              >
                <Plus className="w-4 h-4 mr-2" />
                Criar Webhook
              </Button>
            </Card>
          ) : (
            <div className="space-y-3">
              {webhooks.map(webhook => (
                <Card key={webhook.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Webhook className={`w-4 h-4 ${webhook.isActive ? 'text-gray-950' : 'text-gray-400 dark:text-gray-500'}`} />
                          <h4 className="font-medium text-sm text-gray-800 dark:text-gray-100" >
                            {webhook.name}
                          </h4>
                          <Badge variant={webhook.isActive ? 'default' : 'secondary'} className="text-xs">
                            {webhook.isActive ? 'Ativo' : 'Inativo'}
                          </Badge>
                        </div>
                        {webhook.description && (
                          <p className="text-xs mb-1 text-gray-500 dark:text-gray-400" >
                            {webhook.description}
                          </p>
                        )}
                        <p className="text-xs mb-2 font-mono text-gray-400 dark:text-gray-500" >
                          {webhook.url}
                        </p>
                        <div className="flex flex-wrap gap-1 mb-2">
                          {webhook.events.slice(0, 5).map(event => (
                            <Badge key={event} variant="outline" className="text-xs">
                              {event}
                            </Badge>
                          ))}
                          {webhook.events.length > 5 && (
                            <Badge variant="outline" className="text-xs">
                              +{webhook.events.length - 5} mais
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500" >
                          <span className="flex items-center gap-1">
                            <Activity className="w-3 h-3" />
                            {webhook.successRate}% sucesso
                          </span>
                          {webhook.totalDeliveries !== undefined && (
                            <span>{webhook.totalDeliveries} entregas</span>
                          )}
                          {webhook.lastTriggered && (
                            <span>Último: {new Date(webhook.lastTriggered).toLocaleString('pt-BR')}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleTestWebhook(webhook.id)}
                          disabled={testingWebhook === webhook.id || !webhook.isActive}
                          title={!webhook.isActive ? 'Ative o webhook para testar' : 'Enviar teste'}
                        >
                          {testingWebhook === webhook.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleViewWebhookLogs(webhook)}
                          title="Ver logs de entrega"
                        >
                          <FileText className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowWebhookSecret(showWebhookSecret === webhook.id ? null : webhook.id)}
                          title="Ver/ocultar secret"
                        >
                          {showWebhookSecret === webhook.id ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditingWebhook(webhook)} title="Editar">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-status-error hover:text-status-error"
                          onClick={() => handleDeleteWebhook(webhook.id)}
                          title="Excluir"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                        <Switch
                          checked={webhook.isActive}
                          onCheckedChange={() => handleToggleWebhookActive(webhook.id)}
                        />
                      </div>
                    </div>
                    {showWebhookSecret === webhook.id && webhook.secret && (
                      <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-800 rounded-md flex items-center justify-between">
                        <code className="text-xs">{webhook.secret}</code>
                        <Button size="sm" variant="ghost" onClick={() => { navigator.clipboard.writeText(webhook.secret); toast.success('Secret copiado!') }}>
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {showLogsModal && selectedWebhookForLogs && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <Card className="w-full max-w-3xl max-h-[80vh] overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      Logs de Entrega - {selectedWebhookForLogs.name}
                    </CardTitle>
                    <Button size="sm" variant="ghost" onClick={() => { setShowLogsModal(false); setSelectedWebhookForLogs(null); setWebhookLogs([]) }}>
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="overflow-y-auto max-h-[60vh]">
                  {webhookLogsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-gray-700 dark:text-gray-300" />
                      <span className="ml-2 text-sm text-gray-500 dark:text-gray-400" >
                        Carregando logs...
                      </span>
                    </div>
                  ) : webhookLogs.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="w-10 h-10 mx-auto mb-2 text-gray-400 dark:text-gray-500"  />
                      <p className="text-sm text-gray-500 dark:text-gray-400" >
                        Nenhum log de entrega encontrado
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {webhookLogs.map((log: WebhookLog) => (
                        <div
                          key={log.id}
                          className="p-3 rounded-md border text-sm border-gray-200 dark:border-gray-700"
                          
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge 
                                className={`text-xs ${
                                  log.status === 'success' 
                                    ? 'bg-status-success/15 text-status-success' 
                                    : log.status === 'failed' 
                                    ? 'bg-status-error/15 text-status-error' 
                                    : 'bg-status-warning/15 text-status-warning'
                                }`}
                              >
                                {log.status === 'success' ? 'Sucesso' : log.status === 'failed' ? 'Falha' : 'Pendente'}
                              </Badge>
                              <span className="text-gray-800 dark:text-gray-100" >{log.event_type}</span>
                            </div>
                            <span className="text-xs text-gray-400 dark:text-gray-500" >
                              {new Date(log.created_at).toLocaleString('pt-BR')}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {log.response_status && (
                              <div>
                                <span className="text-gray-500 dark:text-gray-400" >Status HTTP: </span>
                                <span className="text-gray-800 dark:text-gray-100" >{log.response_status}</span>
                              </div>
                            )}
                            <div>
                              <span className="text-gray-500 dark:text-gray-400" >Tentativas: </span>
                              <span className="text-gray-800 dark:text-gray-100" >{log.attempts}</span>
                            </div>
                          </div>
                          {log.response_body && (
                            <details className="mt-2">
                              <summary className="text-xs cursor-pointer text-gray-500 dark:text-gray-400" >
                                Ver resposta
                              </summary>
                              <pre className="mt-1 p-2 bg-gray-50 dark:bg-gray-800 rounded-md text-xs overflow-x-auto">
                                {log.response_body}
                              </pre>
                            </details>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  )
}
