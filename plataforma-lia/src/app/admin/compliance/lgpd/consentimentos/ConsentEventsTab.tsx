"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { Search, AlertCircle, Loader2, Eye, Ban } from "lucide-react"
import { ConsentEvent } from "@/services/admin/consent-management-service"

const CONSENT_TYPE_LABELS: Record<string, string> = {
  personal_data: 'Dados Pessoais',
  marketing: 'Comunicações Marketing',
  sensitive_data: 'Dados Sensíveis',
  data_sharing: 'Compartilhamento com Clientes',
  cookies: 'Cookies',
  analytics: 'Analytics',
  third_party: 'Terceiros',
}

interface ConsentEventsTabProps {
  events: ConsentEvent[]
  isLoading: boolean
  searchTerm: string
  setSearchTerm: (v: string) => void
  eventTypeFilter: string
  setEventTypeFilter: (v: string) => void
  consentTypeFilter: string
  setConsentTypeFilter: (v: string) => void
  onLoadHistory: (subjectIdentifier: string) => void
  isLoadingHistory: boolean
  onRevoke: (event: ConsentEvent) => void
}

function getEventStatusBadge(eventType: string) {
  switch (eventType) {
    case 'granted':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Concedido</Badge>
    case 'revoked':
      return <Badge className="bg-wedo-purple/15 text-wedo-purple hover:bg-wedo-purple/15">Revogado</Badge>
    case 'expired':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Expirado</Badge>
    case 'renewed':
 return <Badge className="text-lia-text-primary dark:text-lia-text-primary hover:bg-lia-bg-tertiary">Renovado</Badge>
    default:
      return <Badge>{eventType}</Badge>
  }
}

export function ConsentEventsTab({
  events, isLoading, searchTerm, setSearchTerm,
  eventTypeFilter, setEventTypeFilter, consentTypeFilter, setConsentTypeFilter,
  onLoadHistory, isLoadingHistory, onRevoke,
}: ConsentEventsTabProps) {
  const filteredEvents = events.filter(e => {
    const matchesSearch = 
      (e.subjectName || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.subjectEmail || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.subjectIdentifier.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Eventos de Consentimento
            </CardTitle>
            <CardDescription>Registro de concessões, revogações e expirações</CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
              <Input
                placeholder="Buscar titular..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Evento" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos Eventos</SelectItem>
                <SelectItem value="granted">Concessão</SelectItem>
                <SelectItem value="revoked">Revogação</SelectItem>
                <SelectItem value="expired">Expirado</SelectItem>
                <SelectItem value="renewed">Renovação</SelectItem>
              </SelectContent>
            </Select>
            <Select value={consentTypeFilter} onValueChange={setConsentTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos os Tipos</SelectItem>
                {Object.entries(CONSENT_TYPE_LABELS).map(([key, label]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
            <span className="ml-2 text-lia-text-secondary dark:text-lia-text-tertiary">Carregando...</span>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-12 h-12 text-lia-text-disabled mb-4" />
            <p className="text-lia-text-secondary dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Nenhum evento de consentimento encontrado</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Titular</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Tipo de Consentimento</TableHead>
                <TableHead>Versão</TableHead>
                <TableHead>Evento</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>IP/Dispositivo</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEvents.map((event) => (
                <TableRow key={event.id} className="hover:bg-lia-bg-secondary">
                  <TableCell>
                    <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {event.subjectName || event.subjectIdentifier}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-lia-text-secondary dark:text-lia-text-tertiary">
                      {event.subjectEmail || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {CONSENT_TYPE_LABELS[event.consentType] || event.consentType}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary" className="text-xs">v{event.version}</Badge>
                  </TableCell>
                  <TableCell>{getEventStatusBadge(event.eventType)}</TableCell>
                  <TableCell>
                    <span className="text-lia-text-secondary dark:text-lia-text-tertiary">
                      {new Date(event.createdAt).toLocaleDateString('pt-BR', {
                        day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
                      })}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                      <div>{event.ipAddress || '-'}</div>
                      <div className="truncate max-w-32">{event.userAgent || '-'}</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button 
                        variant="ghost" size="sm"
                        onClick={() => onLoadHistory(event.subjectIdentifier)}
                        disabled={isLoadingHistory}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Histórico
                      </Button>
                      {event.eventType === 'granted' && (
                        <Button 
                          variant="ghost" size="sm" 
                          className="text-status-error hover:text-status-error hover:bg-status-error/10"
                          onClick={() => onRevoke(event)}
                        >
                          <Ban className="w-3 h-3 mr-1" />
                          Revogar
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
