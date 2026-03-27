'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Mail, Clock, Loader2, Send, RefreshCw, MessageSquare,
  Search, Check, X, AlertCircle
} from "lucide-react"
import type { CommunicationLogEntry, HistoryChannelFilter, HistoryStatusFilter, HistoryPeriodFilter } from './types'

const getStatusBadge = (status: CommunicationLogEntry['status']) => {
  const styles: Record<string, string> = {
    sent: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    delivered: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    read: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    bounced: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    pending: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200'
  }
  const labels: Record<string, string> = {
    sent: 'Enviado',
    delivered: 'Entregue',
    read: 'Lido',
    failed: 'Falhou',
    bounced: 'Bounce',
    pending: 'Pendente'
  }
  return (
    <Badge className={`text-xs ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </Badge>
  )
}

const getChannelIcon = (channel: CommunicationLogEntry['channel']) => {
  switch (channel) {
    case 'email':
      return <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
    case 'whatsapp':
      return (
        <svg className="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
      )
    case 'sms':
      return <MessageSquare className="w-4 h-4 text-purple-500" />
    default:
      return <Mail className="w-4 h-4" />
  }
}

interface HistorySectionProps {
  communicationLogs: CommunicationLogEntry[]
  historyLoading: boolean
  historySearch: string
  setHistorySearch: (search: string) => void
  historyChannel: HistoryChannelFilter
  setHistoryChannel: (channel: HistoryChannelFilter) => void
  historyStatus: HistoryStatusFilter
  setHistoryStatus: (status: HistoryStatusFilter) => void
  historyPeriod: HistoryPeriodFilter
  setHistoryPeriod: (period: HistoryPeriodFilter) => void
  historyPage: number
  setHistoryPage: (page: number | ((p: number) => number)) => void
  historyTotal: number
  historyPerPage: number
  fetchCommunicationHistory: () => void
}

export function HistorySection({
  communicationLogs,
  historyLoading,
  historySearch,
  setHistorySearch,
  historyChannel,
  setHistoryChannel,
  historyStatus,
  setHistoryStatus,
  historyPeriod,
  setHistoryPeriod,
  historyPage,
  setHistoryPage,
  historyTotal,
  historyPerPage,
  fetchCommunicationHistory
}: HistorySectionProps) {
  const filteredLogs = communicationLogs.filter(log => {
    if (historySearch) {
      const searchLower = historySearch.toLowerCase()
      const matchesRecipient = log.recipientName.toLowerCase().includes(searchLower) || log.recipient.toLowerCase().includes(searchLower)
      const matchesSubject = log.subject?.toLowerCase().includes(searchLower) || log.templateName?.toLowerCase().includes(searchLower)
      if (!matchesRecipient && !matchesSubject) return false
    }
    return true
  })

  const totalPages = Math.ceil(historyTotal / historyPerPage)

  const historyStats = {
    total: historyTotal,
    delivered: communicationLogs.filter(l => l.status === 'delivered' || l.status === 'read').length,
    failed: communicationLogs.filter(l => l.status === 'failed' || l.status === 'bounced').length,
    pending: communicationLogs.filter(l => l.status === 'sent' || l.status === 'pending').length
  }

  const successRate = historyTotal > 0 
    ? Math.round((historyStats.delivered / historyTotal) * 100) 
    : 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
            Histórico de Comunicações
          </h3>
          <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Visualize todas as comunicações enviadas pela plataforma
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => fetchCommunicationHistory()}
          disabled={historyLoading}
        >
          <RefreshCw className={`w-4 h-4 ${historyLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {historyLoading && communicationLogs.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-700 dark:text-gray-300" />
          <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
            Carregando histórico...
          </span>
        </div>
      ) : (
      <>
      <div className="grid grid-cols-4 gap-4 mb-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>Total</p>
                <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                  {historyStats.total.toLocaleString('pt-BR')}
                </p>
              </div>
              <Send className="w-8 h-8" style={{ color: 'var(--eleven-text-tertiary)' }} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>Entregues</p>
                <p className="text-2xl font-semibold text-emerald-600">
                  {historyStats.delivered.toLocaleString('pt-BR')}
                </p>
              </div>
              <Check className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>Falhas</p>
                <p className="text-2xl font-semibold text-red-600">
                  {historyStats.failed.toLocaleString('pt-BR')}
                </p>
              </div>
              <X className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>Taxa Sucesso</p>
                <p className="text-2xl font-semibold" style={{ color: successRate >= 90 ? 'var(--status-success)' : successRate >= 70 ? 'var(--status-warning)' : 'var(--status-error)' }}>
                  {successRate}%
                </p>
              </div>
              <AlertCircle className="w-8 h-8" style={{ color: successRate >= 90 ? 'var(--status-success)' : successRate >= 70 ? 'var(--status-warning)' : 'var(--status-error)' }} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Comunicações Recentes</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2" style={{ color: 'var(--eleven-text-tertiary)' }} />
                <Input
                  placeholder="Buscar por destinatário ou assunto..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="pl-8 h-8 w-64"
                />
              </div>
              <select
                className="h-8 px-2 text-xs border rounded-md"
                value={historyChannel}
                onChange={(e) => setHistoryChannel(e.target.value as HistoryChannelFilter)}
              >
                <option value="all">Todos Canais</option>
                <option value="email">Email</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="sms">SMS</option>
              </select>
              <select
                className="h-8 px-2 text-xs border rounded-md"
                value={historyStatus}
                onChange={(e) => setHistoryStatus(e.target.value as HistoryStatusFilter)}
              >
                <option value="all">Todos Status</option>
                <option value="sent">Enviado</option>
                <option value="delivered">Entregue</option>
                <option value="read">Lido</option>
                <option value="failed">Falhou</option>
                <option value="bounced">Bounce</option>
              </select>
              <select
                className="h-8 px-2 text-xs border rounded-md"
                value={historyPeriod}
                onChange={(e) => setHistoryPeriod(e.target.value as HistoryPeriodFilter)}
              >
                <option value="today">Hoje</option>
                <option value="7days">Últimos 7 dias</option>
                <option value="30days">Últimos 30 dias</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Send className="w-12 h-12 text-gray-300 mb-4" />
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Nenhuma comunicação encontrada
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Ajuste os filtros ou aguarde novas comunicações
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredLogs.map(log => (
                <div
                  key={log.id}
                  className="flex items-center justify-between p-3 rounded-md border hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                  style={{ borderColor: 'var(--eleven-border-subtle)' }}
                >
                  <div className="flex items-center gap-3">
                    {getChannelIcon(log.channel)}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                          {log.recipientName}
                        </span>
                        {getStatusBadge(log.status)}
                        {log.type === 'inbound' && (
                          <Badge variant="outline" className="text-xs">Inbound</Badge>
                        )}
                      </div>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        {log.subject || log.templateName || log.communicationType || 'Sem assunto'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {log.jobTitle && (
                      <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {log.jobTitle}
                      </span>
                    )}
                    <span className="text-xs flex items-center gap-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      <Clock className="w-3 h-3" />
                      {new Date(log.timestamp).toLocaleString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setHistoryPage(p => Math.max(1, p - 1))}
                disabled={historyPage === 1 || historyLoading}
              >
                Anterior
              </Button>
              <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                Página {historyPage} de {totalPages}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setHistoryPage(p => Math.min(totalPages, p + 1))}
                disabled={historyPage === totalPages || historyLoading}
              >
                Próximo
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      </>
      )}
    </div>
  )
}
